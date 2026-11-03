# -*- coding: utf-8 -*-
"""根级文档活引用门（A0-2·第三百三十一批）：仓库根 `*.md` 里的路径必须指向真实文件。

为什么需要它（A2 诊断·实测）：两科 `check_doc_refs.py` 都只扫**学科根**
（`DISC.rglob("*")`），根级八份治理文档不在任何门的扫描域里；而最权威的四份
（`AGENTS.md`／`CONTRACT.md`／`README.md`／`GOVERNANCE.md`）恰恰是最没人校对路径的四份。
实测 `AGENTS.md` 三处、`CONTRACT.md` 一处写着 `docs/CHANGELOG.md`，而根**没有** `docs/`。

本门与两科门的**根本差异**（不许为"减少误报"改回去）：

  1. 扫描域是 `ROOT.glob("*.md")`，只扫仓库根，不走 `DISC.rglob`；
  2. **禁用 basename 兜底**：`docs/CHANGELOG.md` 必须解析到真实路径，同名文件不认——
     旧门的 `any(p.name == name ...)` 兜底会让它靠 `liuyao/docs/CHANGELOG.md` 蒙混过关，
     分不清"根级"与"学科级"，等于没有判定力。

豁免口径照抄 `dev_tools/check_doc_refs.py`（不自创）：
  · 负例文件名 `__` 双下划线前缀；`...`／`<`／`…`／URL；
  · 历史散文（`HISTORY`：曾/已删除/不存在/负例/selftest/…）；
  · 运行时产物目录（`outputs/` `scratch/` `logs/` `devkit/handoff/` `devkit/pending/`）；
  · 散文速记（路径段含纯数字，如 `step3/4/5.py`）；
  · 本门自身文件。

    python devkit/root/check_root_docs.py
    python devkit/root/check_root_docs.py --selftest
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REF = re.compile(r"`([A-Za-z0-9_\-./\u4e00-\u9fff]+\.(?:md|py|json|txt|css|html|yml|yaml))(?![A-Za-z])`")
# 裸路径：只认以真实顶层目录开头的串（与两科门同口径，另加根级目录）
TOP = ("docs|scripts|data|references|dev_tools|core|tests|kernel|plugins|devkit"
       "|liuyao|bazi|dsh-plugin"
       "|.github|.worktrees")
BARE = re.compile(r"(?<![\w/.-])((?:%s)/[A-Za-z0-9_\-./\u4e00-\u9fff]*"
                  r"\.(?:md|py|json|txt|css|html|yml|yaml)(?![A-Za-z]))" % TOP)
SKIP_MARK = ("<", "…", "...", "http://", "https://", "{{")
# 运行时产物与暂存区：本就不入库，存在性不检查
RUNTIME_DIRS = ("outputs/", "scratch/", "logs/", "assets/", "devkit/handoff/", "devkit/pending/",
                ".worktrees/", "plugins/dist/", "plugins/engine/", "plugins/skills/")
HISTORY = re.compile(r"曾[并未已在经]|勘误|不采此说|已失效|原有|原挂|已删除|已随|随仓库|不存在|改指|作废|"
                     r"无此文件|负例|造的|自测|selftest|未建|待建|拟建|模板|禁止|尚未|未就位|先记欠账")
NEGATIVE = ("__does_not_exist__", "definitely_missing", "nope.py", "_selftest_", "__",
            "路径/文件名", "_patch_xxx")
SHORTHAND = re.compile(r"(^|/)\d+(?=/|\.|$)")
SUFFIXES = (".md", ".py", ".json", ".txt", ".css", ".html", ".yml", ".yaml")
# 规划/派发件：正文写的是**未来态路径**（卡还没做，文件当然不在盘上）与模板占位。
# 它们的价值是排期而不是导航，故不纳入活引用判定；完成后由 A6-INT 在卡上标注实态。
PLAN_DOCS = ("ARCHITECTURE-PLAN.md", "DISPATCH.md")
# 学科内部相对路径：根级治理文档常用 `scripts/chart.py` 这种写法指"各科的 scripts/"。
# 只按这两科解析，不做同名文件兜底；`docs/` 另按"同行是否点名学科"判（见 resolves）。
DISC_SCOPED = ("scripts/", "data/", "references/", "dev_tools/", "core/", "tests/", "assets/")
DISC_WORD = re.compile(r"liuyao|bazi|六爻|八字")
DIR_ON_LINE = re.compile(r"(?:^|`|\s)([A-Za-z0-9_.\-]+/)")


def root_docs(root: Path) -> list[Path]:
    return sorted(p for p in root.glob("*.md") if p.is_file())


def resolves(root: Path, rel: str, line: str, doc: str) -> bool:
    """仓库根严格解析；学科内部相对路径按两科解析；**没有 basename 兜底**。

    `docs/` 是 A2 实测的悬空重灾区：根级文档写 `docs/CHANGELOG.md` 时，只有同一行
    点名了学科（或本文件就是全仓索引 DOCS.md）才认学科路径；否则必须根级真实存在。
    """
    clean = rel[2:] if rel.startswith("./") else rel
    if (root / clean).exists():
        return True
    if clean.startswith(DISC_SCOPED):
        return any((root / d / clean).exists() for d in ("liuyao", "bazi"))
    if clean.startswith("docs/"):
        if doc == "DOCS.md" or DISC_WORD.search(line):
            return any((root / d / clean).exists() for d in ("liuyao", "bazi"))
        return False
    # DSH 宿主清单的特殊路径写法：`dsh-plugin/package.json` 等在 `dsh-plugin/` 下。
    if clean.startswith(".") and "/" in clean:
        host = clean.split("/")[0].lstrip(".")
        if (root / host / clean).exists():
            return True
    # 行内点名了某个目录（如 `.mcp.json` 与 `dsh-plugin/` 同现于一行）：按该目录解析。
    # 这是**上下文**解析，不是全仓 basename 兜底。
    for m in DIR_ON_LINE.finditer(line):
        if (root / m.group(1) / clean).exists():
            return True
    return False


def check(root: Path = ROOT) -> tuple[list[str], int]:
    problems: list[str] = []
    examined = 0
    files = root_docs(root)
    if not files:
        return ["仓库根扫到 0 份 .md——先查路径解析，不能当通过"], 0
    for p in files:
        if p.name in PLAN_DOCS:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        lines = text.splitlines()
        for n, line in enumerate(lines, 1):
            found: list[str] = []
            for m in REF.finditer(line):
                found.append(m.group(1).strip())
            for m in BARE.finditer(line):
                s = m.group(1)
                if s not in found:
                    found.append(s)
            for ref in found:
                if HISTORY.search(line) or HISTORY.search(lines[n - 2] if n >= 2 else ""):
                    continue
                if any(k in ref for k in NEGATIVE):
                    continue
                if any(k in ref for k in SKIP_MARK):
                    continue
                if not ref.endswith(SUFFIXES):
                    continue
                if "/" not in ref and not ref.startswith("."):
                    continue
                if ref.startswith(RUNTIME_DIRS):
                    continue
                if SHORTHAND.search(ref):
                    continue
                examined += 1
                if not resolves(root, ref, line, p.name):
                    problems.append(f"{p.name}:{n} 指向不存在的文件 → {ref}")
    return problems, examined


def selftest() -> int:
    """负例走临时目录（AGENTS.md §四.8）：死链必抓、基线兜底不得放行、真路径不误伤。"""
    fails: list[str] = []
    with tempfile.TemporaryDirectory(prefix="rootdocs_") as td:
        root = Path(td)
        (root / "README.md").write_text("见 `docs/_probe_root_dead.md`。\n", encoding="utf-8")
        (root / "GUIDE.md").write_text(
            "真路径：`kernel/sync_kernel.py`；裸路径 docs/_probe_root_dead_b.md。\n",
            encoding="utf-8")
        (root / "kernel").mkdir()
        (root / "kernel" / "sync_kernel.py").write_text("# probe\n", encoding="utf-8")
        # 只该抓 README 的 1 条 + GUIDE 的 1 条裸路径；GUIDE 的真路径不得误伤
        problems, examined = check(root)
        if len(problems) < 2:
            fails.append(f"根级死链没抓全（只抓到 {len(problems)} 条）")
        if any("kernel/sync_kernel.py" in p for p in problems):
            fails.append("真实存在的根级路径被误判")
        if examined < 2:
            fails.append(f"检视数为 {examined}——本器等于没扫")
        # 关键判据：学科级同名文件不得给根级 `docs/CHANGELOG.md` 兜底
        (root / "liuyao" / "docs").mkdir(parents=True)
        (root / "liuyao" / "docs" / "CHANGELOG.md").write_text("# probe\n", encoding="utf-8")
        (root / "CONTRACT.md").write_text("见 `docs/CHANGELOG.md`。\n", encoding="utf-8")
        problems2, _ = check(root)
        if not any("CONTRACT.md:1" in p for p in problems2):
            fails.append("basename 兜底复活：`docs/CHANGELOG.md` 被学科同名文件放行")
        # 学科内部相对路径必须能解析（`scripts/chart.py` 指各科 scripts/，不是根级）
        (root / "liuyao" / "scripts").mkdir(parents=True)
        (root / "liuyao" / "scripts" / "chart.py").write_text("# probe\n", encoding="utf-8")
        (root / "GUIDE.md").write_text("入口 `scripts/chart.py`。\n", encoding="utf-8")
        problems3, _ = check(root)
        if any("scripts/chart.py" in p for p in problems3):
            fails.append("学科内部相对路径（scripts/chart.py）被误判")
        # 0 结果防线：没有根级 md 时必须判红，不能"扫了 0 份 = 没问题"
        empty = root / "empty"
        empty.mkdir()
        problems4, examined4 = check(empty)
        if examined4 != 0 or not problems4:
            fails.append("根级 0 份文档时未判红（路径解析错了会被当成全绿）")
    if fails:
        for f in fails:
            print(f"  × selftest：{f}")
        return 1
    print("  √ selftest：根级死链必抓／学科同名文件不兜底／真路径不误伤／0 份文档判红")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="根级文档活引用门")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    files = root_docs(ROOT)
    if not files:
        print("  × 仓库根扫到 0 份 .md——先查路径解析，不能当通过")
        return 1
    problems, examined = check()
    print(f"根级文档 {len(files)} 份：检视 {examined} 条路径引用，{len(problems)} 条指向不存在的文件")
    if examined == 0:
        print("  × 0 条被检视——本器等于没跑，不判通过")
        return 1
    for p in problems:
        print(f"  × {p}")
    if problems:
        return 1
    print("  √ 根级活引用全部可达")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
