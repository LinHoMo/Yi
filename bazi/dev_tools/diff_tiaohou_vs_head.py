# -*- coding: utf-8 -*-
"""改动前后逐格对拍（SKILL.md）：把当前表与 HEAD 版**逐格**比对，只报差异。

    python dev_tools/diff_tiaohou_vs_head.py                    # 两拍：data 层 + 引擎表
    python dev_tools/diff_tiaohou_vs_head.py --table engine     # 只拍 core 引擎表 TIAO_HOU
    python dev_tools/diff_tiaohou_vs_head.py --table data       # 只拍 data/tiaohou_quotes.json
    python dev_tools/diff_tiaohou_vs_head.py --head-ref HEAD~1  # 换比对面
    python dev_tools/diff_tiaohou_vs_head.py --engine-file <副本> --data-file <副本>
        ↑ 负例自证用（§四.8）：把「明知被改值/被清空」的副本喂进来，确认本工具真的报出来，
          而不是去动 core/ 或 data/ 的真文件。

三档必须分开报、逐条列明细（§四.5：只报「新覆盖了几格」会掩盖悄悄回归）：
    新增 N  —— 原格为空/整格缺失，今有 main（扩面）
    变空 N  —— 原格有 main，今空或整格消失（**最危险的一档**）
    改值 N  —— 两侧都有 main 但取值不同（含 assist / quote 单字段变化，逐字段点名）

只读：旧表用 `git show <ref>:<path>` 取回，不 stash、不 checkout、不写盘。
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

# 扁平化后脚本位于 <学科根>/dev_tools/；学科根=bazi（parents[1]），内核副本在 <学科根>/core。
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
# 块定位正则与两张表的唯一路径都由同步脚本给出——本工具不再抄第二份
# （SKILL.md「同一张表不得存两份」同样适用于「同一套定位逻辑」）
from sync_tiaohou_engine import BLOCK_RE, DATA as DATA_PATH_DEFAULT, ENGINE as ENGINE_PATH_DEFAULT  # noqa: E402

# data 层比对的字段：main/assist 是判据值，quote 是「照录」原文（改字即违反逐字体例）
DATA_FIELDS = ("main", "assist", "quote")
ENGINE_FIELDS = ("main", "assist")


def _git_root() -> Path:
    """git 仓库根（扁平化后学科根不再是仓库根，git show 的路径须相对仓库根）。"""
    proc = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          cwd=Path(__file__).resolve().parent, capture_output=True)
    if proc.returncode != 0:
        raise SystemExit("× 找不到 git 仓库根")
    return Path(proc.stdout.decode("utf-8").strip())


GIT_ROOT = _git_root()


def git_show(ref: str, rel_path: Path) -> str:
    """取回某 revision 下的文件内容（路径相对仓库根，cwd 也用仓库根）。"""
    rel = rel_path.resolve().relative_to(GIT_ROOT.resolve()).as_posix()
    proc = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=GIT_ROOT,
                          capture_output=True)
    if proc.returncode != 0:
        raise SystemExit(f"× git show {ref}:{rel} 失败：{proc.stderr.decode('utf-8', 'replace')[:200]}")
    return proc.stdout.decode("utf-8")


def _cell(raw: dict | None, fields: tuple[str, ...]) -> dict:
    """格值归一：`assist` 缺键与空串同义（书无明文＝空），否则 HEAD 侧 None、
    工作侧 "" 会被报成 55 处「改值」噪声——那是**写法差异不是取值差异**，
    对拍只报真正的取值变化（§四.5 要的是可解释的明细，不是数量吓人）。"""
    src = raw or {}
    return {f: ("" if src.get(f) is None else src[f]) for f in fields}


def load_data_table(text: str) -> dict:
    """data/tiaohou_quotes.json → {键: {main, assist, quote}}（键本身即「月序+日干」）。"""
    raw = json.loads(text)
    return {k: _cell(v, DATA_FIELDS) for k, v in raw.items() if isinstance(v, dict)}


def load_engine_table(text: str) -> dict:
    """ming_tables.py 源码 → 引擎表 TIAO_HOU 展平成 {"寅甲": {main, assist}, …}。

    引擎表的键是「月支×日干」，data 层的键是「月序+日干」——两侧都用
    `<支><干>` 两字作 cell key，于是同一格在两张表里可对拍（月序→月支由
    同步脚本的 BRANCH_OF_MONTH 单源换算，见 sync_tiaohou_engine）。
    """
    m = BLOCK_RE.search(text)
    if not m:
        raise SystemExit("× 未在源码里定位到 TIAO_HOU 块（正则来自 sync_tiaohou_engine）")
    table = ast.literal_eval("{" + m.group("body") + "}")
    out: dict[str, dict] = {}
    for branch, cells in table.items():
        for stem, cell in (cells or {}).items():
            out[f"{branch}{stem}"] = _cell(cell, ENGINE_FIELDS)
    # data 层键「月序+日干」→ 同一换算式，便于两表互拍时口径一致
    return out


def data_keys_to_branch(text: str) -> dict:
    """data 层表按「月支+日干」重键（与引擎表同轴），值仍取 main/assist/quote。"""
    from sync_tiaohou_engine import BRANCH_OF_MONTH
    raw = json.loads(text)
    out: dict[str, dict] = {}
    for key, cell in raw.items():
        if not isinstance(cell, dict):
            continue
        m = re.match(r"^(\d{1,2})(.+)$", key)
        if not m:
            continue
        branch = BRANCH_OF_MONTH.get(int(m.group(1)))
        if not branch:
            continue
        out[f"{branch}{m.group(2)}"] = _cell(cell, DATA_FIELDS)
    return out


def diff_cells(old: dict, new: dict, fields: tuple[str, ...]) -> tuple[list, list, list]:
    """返回 (新增, 变空, 改值)；每条是 (cell, 字段, 旧值, 新值)。"""
    added: list[tuple] = []
    emptied: list[tuple] = []
    changed: list[tuple] = []
    for cell in sorted(set(old) | set(new)):
        o, n = old.get(cell) or {}, new.get(cell) or {}
        if not o and not n:
            continue
        for f in fields:
            # 归一到空串：整格缺失与「该字段为空」在同一档里判（None 与 "" 不得算「改值」）
            ov, nv = o.get(f) or "", n.get(f) or ""
            if ov == nv:
                continue
            if not ov:
                added.append((cell, f, ov, nv))
            elif not nv:
                emptied.append((cell, f, ov, nv))
            else:
                changed.append((cell, f, ov, nv))
    return added, emptied, changed


def report(name: str, old: dict, new: dict, fields: tuple[str, ...]) -> int:
    added, emptied, changed = diff_cells(old, new, fields)
    print(f"\n=== {name} ===")
    print(f"HEAD 侧 {len(old)} 格 → 工作侧 {len(new)} 格；"
          f"新增 {len(added)}，变空 {len(emptied)}，改值 {len(changed)}"
          f"（按字段计，非按格计）")
    for label, rows in (("新增", added), ("变空", emptied), ("改值", changed)):
        for cell, field, ov, nv in rows:
            shown = f"{cell}/{field}: {str(ov)[:60] or '（空）'}  →  {str(nv)[:60] or '（空）'}"
            print(f"  [{label}] {shown}")
    if not (added or emptied or changed):
        print("  三档皆 0 —— 本轮未改这张表，读数持平属预期（§四.7：持平不构成修对了的证据）")
    return len(added) + len(emptied) + len(changed)


def main() -> int:
    ap = argparse.ArgumentParser(description="调候表逐格对拍（data 层 + core 引擎表）")
    ap.add_argument("--table", choices=["both", "data", "engine"], default="both")
    ap.add_argument("--head-ref", default="HEAD", help="比对面（默认 HEAD）")
    ap.add_argument("--data-file", type=Path, default=DATA_PATH_DEFAULT,
                    help="工作侧 data 层表（默认走真路径；负例自证时指临时副本）")
    ap.add_argument("--engine-file", type=Path, default=ENGINE_PATH_DEFAULT,
                    help="工作侧引擎表所在源码（默认 core/yishu_core/ming_tables.py；"
                         "负例自证时指临时副本）")
    args = ap.parse_args()

    total = 0
    if args.table in ("both", "data"):
        old_data = load_data_table(git_show(args.head_ref, DATA_PATH_DEFAULT))
        new_data = load_data_table(args.data_file.read_text(encoding="utf-8"))
        total += report("data 层 tiaohou_quotes.json（main/assist/quote）",
                        old_data, new_data, DATA_FIELDS)
    if args.table in ("both", "engine"):
        old_engine = load_engine_table(git_show(args.head_ref, ENGINE_PATH_DEFAULT))
        new_engine = load_engine_table(args.engine_file.read_text(encoding="utf-8"))
        total += report("引擎表 core/yishu_core/ming_tables.py::TIAO_HOU（main/assist）",
                        old_engine, new_engine, ENGINE_FIELDS)
        # 引擎表与 data 层不同源时，差异既可能来自手改引擎（违反 §四.6），
        # 也可能来自改了 data 没同步——顺手拍一次，明细交给同步脚本判红。
        if args.table == "engine":
            data_now = data_keys_to_branch(args.data_file.read_text(encoding="utf-8"))
            view = {k: _cell(v, ENGINE_FIELDS) for k, v in data_now.items()}
            total += report("引擎表 ↔ data 层同源核对（当前工作区两份表）",
                            view, new_engine, ENGINE_FIELDS)

    print(f"\n合计差异字段 {total} 处。口径：main/assist 变了要解释判据来源；"
          "quote 变了要确认是「照录原文」还是「改写」——后者一律不许（§二 逐字要求）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
