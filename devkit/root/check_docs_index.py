# -*- coding: utf-8 -*-
"""文档索引完整性门（第三百三十批建，第三百三十一批 A0-5 上提到根）。

**迁出登记**：本门第三百三十批建于 `liuyao/dev_tools/check_docs_index.py`（[36]），
A0-5 把它搬到 `devkit/root/`——因为它守的是**全仓** `DOCS.md`，不是六爻一科；
留在学科侧会把"跨科索引"挂在单科门禁里，八字侧自然就没有。
六爻 `check.py` 的 [36] 段随迁出移除，编号空出、**不回填**（A5-1 墓碑口径）。

为什么需要它：330 批新增 `DOCS.md` 当全仓文档地图——但地图自己也会烂：
新增文档忘了登记、或登记了已删的文件，读者按图去找会扑空，而**没有任何门看得见**。
本门就管这两件事：

  1. **覆盖**：每个被跟踪的 `.md`（除 `DOCS.md` 自身）都必须在 `DOCS.md` 里出现一次；
  2. **可达**：`DOCS.md` 里写下的每个仓库内路径都必须真实存在。

只读不改：`DOCS.md` 是索引不是真值源，但**它必须能导航到真值源**。

    python devkit/root/check_docs_index.py
    python devkit/root/check_docs_index.py --selftest
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "DOCS.md"

PATH_RE = re.compile(r"`([A-Za-z0-9_./\-]+\.md)`")


def tracked_md() -> list[str]:
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "*.md"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    return sorted(x.strip() for x in out.splitlines() if x.strip())


def registered_paths(txt: str) -> set[str]:
    """索引表**首列**里登记的路径。

    只认首列：正文里顺带提到的路径（如阅读路径表里的 `AGENTS.md`）不算"登记"——
    否则把表格某一行删掉，门仍然显示"已登记"，自检负例就抓不住了。
    """
    out: set[str] = set()
    for line in txt.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if cells:
            out |= set(PATH_RE.findall(cells[0]))
    return out


def check(index_text: str | None = None) -> list[str]:
    problems: list[str] = []
    txt = INDEX.read_text(encoding="utf-8") if index_text is None else index_text
    files = tracked_md()
    listed = registered_paths(txt)
    # 1. 覆盖
    for f in files:
        if f == "DOCS.md":
            continue
        if f not in listed:
            problems.append(f"未登记：`{f}` 不在 DOCS.md 里（新增文档必须同批登记）")
    # 2. 可达：只按仓库根解析。DOCS.md 是全仓索引，第一列路径一律写成仓内全路径
    #    （`liuyao/docs/CHANGELOG.md` 这种），不再有"按科兜底"——兜底会让漏写前缀的行蒙混过关。
    for p in sorted(listed):
        if (ROOT / p).exists():
            continue
        problems.append(f"指向不存在的文件：`{p}`")
    return problems


def selftest() -> int:
    base = INDEX.read_text(encoding="utf-8")
    fails = []
    # ① 少登记一行 → 必须抓到（删整行，正文里的顺带提及不算登记）
    t = "\n".join(l for l in base.splitlines() if not l.startswith("| `AGENTS.md` |"))
    if not check(t):
        fails.append("漏登记未被抓到")
    # ② 登记一个不存在的路径 → 必须抓到（须写成表格行：首列才是"登记"）
    t = base + "\n| `docs/NO-SUCH-FILE.md` | 不存在的文件 | 活文档 |\n"
    if not check(t):
        fails.append("死链未被抓到")
    # ③ 现行副本必须放行
    if check():
        fails.append("现行索引被误判")
    for f in fails:
        print(f"  × selftest：{f}")
    if fails:
        return 1
    print("  √ selftest：漏登记与死链都被抓到；现行索引放行")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="文档索引完整性门")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    problems = check()
    if problems:
        for p in problems:
            print(f"  × {p}")
        return 1
    n = len([f for f in tracked_md() if f != "DOCS.md"])
    print(f"  √ 文档索引完整：{n} 份文档全部登记且可达")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
