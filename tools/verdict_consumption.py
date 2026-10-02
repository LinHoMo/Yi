# -*- coding: utf-8 -*-
"""语料**消费**审计门：语料池 ⊆ 被消费（verdict_audit 的反向）。

  python tools/verdict_consumption.py            # 报告零消费键（始终退出 0）
  python tools/verdict_consumption.py --strict   # 白名单外零消费键判失败

verdict_audit 保证「报告里的句子 ⊆ 语料池」，不保证「语料池 ⊆ 被消费」——
ziwei 命宫格局整块文案零消费却全绿过门（2026-10-01k 手工排查才发现）。
本工具把「发现死语料」机械化：跑同一批真实报告（与 verdict_audit 同源 10 例），
对本科 data/**/*.json 的每个叶子中文串（≥8 汉字）做消费检查。

匹配用**子序列**（按顺序出现即可，不要求连续）：模板串的 `{focus}`/占位符在
渲染后被真实值替换、或被剥离，连续子串必漏判；子序列容忍这些缝隙。
动态拼装键（如 step5_factor_reasons 的 `base_{强弱}`）只要文本被拼进报告，
子序列就能命中——这正是静态 grep 键名会误判、文本比对不会误判的原因。

零消费 ≠ 必死：样本集只有 10 例，主题性键（如 失物/官讼 切句）可能在样本里
 legitimately 未触发。所以默认只报告；--strict 下允许 ALLOWLIST 登记理由。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "core"))

from yishu_core.runtime import force_utf8_stdio, utf8_subprocess_env  # noqa: E402
from verdict_audit import CASES, _argv, _corpus  # noqa: E402  同一批用例与语料池口径

# 消费审计的补充样本：覆盖更多主题/月份/星象，提高语料覆盖率。
# 样本再大也做不到逐键全覆盖（主题性键合法地不触发），所以本工具只报告；
# --strict 仅供人工把关，配合 ALLOWLIST 使用。
EXTRA_CASES = (
    {"discipline": "ming", "datetime": "1984-02-10 10:00", "gender": "男"},
    {"discipline": "ming", "datetime": "1996-11-11 22:00", "gender": "男"},
    {"discipline": "ming", "datetime": "2000-08-15 14:00", "gender": "女"},
    {"discipline": "ziwei", "datetime": "1968-03-15 01:00", "gender": "男"},
    {"discipline": "ziwei", "datetime": "1984-02-04 08:00", "gender": "女"},
    {"discipline": "ziwei", "datetime": "2000-08-15 14:00", "gender": "男"},
    {"discipline": "meihua", "question": "占天气", "datetime": "2026-07-15 12:00"},
    {"discipline": "meihua", "question": "占婚姻", "way": "numbers", "numbers": "2,4,6"},
    {"discipline": "xiaoliuren", "question": "占求财", "datetime": "2026-09-30 10:30"},
    {"discipline": "xiaoliuren", "question": "占婚姻", "way": "numbers", "numbers": "4,8,3"},
    {"discipline": "zeji", "date": "2026-10-15", "activity": "安葬"},
    {"discipline": "liuyao", "question": "占天气何时有雨", "mode": "time",
     "datetime": "2026-07-15 10:30"},
    {"discipline": "liuyao", "question": "占官司输赢", "mode": "manual",
     "datetime": "2026-09-22 23:40", "yao": "7,7,8,8,9,7"},
    # 通道 A 已挂八科（2026-10-01），消费审计同步覆盖两个骨架科：
    #   liuren 起课=月将加时，必须给起课时刻
    #   lingqi 起课=十二棋三部掷数，up/mid/down 各 0..4（0 是合法面数，缺一即无课）
    {"discipline": "liuren", "question": "占出行", "datetime": "2026-09-30 10:30"},
    {"discipline": "liuren", "question": "占求财", "datetime": "2026-10-01 09:00"},
    {"discipline": "lingqi", "question": "占求财", "up": 2, "mid": 1, "down": 3},
    {"discipline": "lingqi", "question": "占疾病", "up": 4, "mid": 4, "down": 4},
)
CASES = tuple(CASES) + tuple(EXTRA_CASES)

MIN_HANZI = 8
CN = re.compile(r"[\u4e00-\u9fff]")
EXCLUDE_DIRS = {"cases", "feedback", "golden", "scratch"}   # 产物/评测库不作语料池

# 已知零消费但有意保留的键（--strict 下的白名单）：理由必须写明
ALLOWLIST: dict[str, str] = {
    "zeji/expansion_path_ref": "元数据：扩样路径声明，非报告文案",
    "zeji/validity_gap": "元数据：效度缺口声明，非报告文案",
}


def _hanzi(s: str) -> str:
    return "".join(CN.findall(s))


def _is_subseq(needle: str, haystack: str) -> bool:
    it = iter(haystack)
    return all(ch in it for ch in needle)


def _walk_strings(node, out: list) -> None:
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, list):
        for x in node:
            _walk_strings(x, out)
    elif isinstance(node, dict):
        for v in node.values():
            _walk_strings(v, out)


def corpus_entries(disc: str) -> list[tuple[str, str]]:
    """学科 data/**/*.json 的叶子中文串 → [(键路径, 汉字串)]。"""
    base = ROOT / "disciplines" / disc / "data"
    entries: list[tuple[str, str]] = []
    if not base.is_dir():
        return entries
    for f in sorted(base.rglob("*.json")):
        if EXCLUDE_DIRS & set(f.relative_to(base).parts):
            continue
        try:
            tree = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        flat: list[str] = []
        _walk_strings(tree, flat)
        for s in flat:
            h = _hanzi(s)
            if len(h) >= MIN_HANZI:
                rel = f.relative_to(ROOT / "disciplines" / disc).as_posix()
                entries.append((f"{disc}/{rel}", h))
    return entries


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="语料消费审计（零消费键检测）")
    ap.add_argument("--strict", action="store_true",
                    help="白名单外零消费键判失败（退出码 1）")
    args = ap.parse_args()

    discs = sorted({c["discipline"] for c in CASES})
    with tempfile.TemporaryDirectory() as td:
        texts: dict[str, str] = {}
        for i, case in enumerate(CASES):
            outdir = Path(td) / f"case{i}"     # 每例独立目录，md 不会互相混取
            proc = subprocess.run(_argv(case, outdir), capture_output=True,
                                  text=True, encoding="utf-8", errors="replace",
                                  cwd=str(ROOT), env=utf8_subprocess_env())
            md = next(outdir.rglob("*.md"), None)
            disc = case["discipline"]
            if md is not None:
                texts[disc] = texts.get(disc, "") + _hanzi(md.read_text(encoding="utf-8"))
            elif proc.returncode != 0:
                print(f"! {disc} 报告未生成（verdict_consumption 跳过该例）")

        failures: list[str] = []
        total_keys = 0
        for disc in discs:
            report_h = texts.get(disc, "")
            if not report_h:
                continue
            zero: list[tuple[str, str]] = []
            checked = 0
            seen: set[str] = set()
            for path, h in corpus_entries(disc):
                if h in seen:
                    continue
                seen.add(h)
                checked += 1
                if not _is_subseq(h, report_h):
                    zero.append((path, h))
            total_keys += checked
            tag = f"{disc}: {checked} 条语料 / 零消费 {len(zero)}"
            print(f"  {tag}")
            for path, h in zero[:12]:
                mark = " [白名单]" if any(path.startswith(a.split("/")[0]) and a.split("/", 1)[1] in path
                                          for a in ALLOWLIST) else ""
                print(f"    - {path}: {h[:44]}…{mark}")
                if args.strict and not mark:
                    failures.append(path)
        print(f"语料消费审计：共 {total_keys} 条（样本 {len(CASES)} 例报告）"
              + ("；零消费明细如上，接线或 --strict 白名单登记" if total_keys else ""))
        if args.strict and failures:
            print(f"× {len(failures)} 条零消费键不在白名单")
            return 1
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
