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

**523 批扩面**（按用户令对 176 批「守台账类新增」冻结作一次限定解冻，采用 514 批
写下的候选形态——扩本门而不新建门）：除上面两条，再守两科主 CHANGELOG 的
「最近 15 批」窗口、单批 ≤12 行、以及滑窗口时与 HEAD 对拍不丢批号。批号＋日期
仍是 342 批的底线，退出窗口的只准搬进历史索引，不准删。
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


# ── 523 批扩面：CHANGELOG 窗口／单批长度／滑窗口不丢批号 ──────────────────
# 510 批把两科主 CHANGELOG 收紧为「最近 15 批」并写明「再往后让窗口滑动时，同批
# 把退出窗口的标题补进索引即可」——但**没有任何门看着它**：522 批实盘六爻 28 批／
# 八字 26 批，超窗口 24 条，全仓门禁一直全绿。这里把 510 批的政策变成机器判据。
# 与 HEAD 那一条守的是「滑窗口只允许搬，不许丢批号」（批号＋日期是 342 批的底线）。
CHANGELOG_PAIRS = (
    ("liuyao/docs/CHANGELOG.md", "liuyao/docs/CHANGELOG-HISTORY-INDEX.md"),
    ("bazi/docs/CHANGELOG.md", "bazi/docs/CHANGELOG-HISTORY-INDEX.md"),
)
CHANGELOG_WINDOW = 15
CHANGELOG_MAX_LINES = 12
BATCH_HEAD_RE = re.compile(
    r"^## (\d{4}-\d{2}-\d{2}) 第([零〇一二两三四五六七八九十百千]+)批")


def _batch_keys(txt: str) -> set[str]:
    return {f"{m.group(1)}#{m.group(2)}" for line in txt.splitlines()
            if (m := BATCH_HEAD_RE.match(line))}


def _head_batch_keys(rel: str) -> set[str] | None:
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return _batch_keys(r.stdout) if r.returncode == 0 else None


def _probe_read(rel: str, probe: dict[str, str] | None) -> str:
    if probe is not None and rel in probe:
        return probe[rel]
    p = ROOT / rel
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def changelog_problems(probe: dict[str, str] | None = None) -> list[str]:
    """probe 只覆盖盘上四份 CHANGELOG 文本；HEAD 始终取真仓，负例才抓得到丢批号。"""
    problems: list[str] = []
    for main, idx in CHANGELOG_PAIRS:
        txt = _probe_read(main, probe)
        lines = txt.splitlines()
        marks = [(i, m.group(2)) for i, line in enumerate(lines)
                 if (m := BATCH_HEAD_RE.match(line))]
        if not marks:
            problems.append(f"{main} 扫到 0 个批次标题（路径解析失败不许报绿）")
            continue
        if len(marks) > CHANGELOG_WINDOW:
            problems.append(f"{main} 有 {len(marks)} 批，超出 {CHANGELOG_WINDOW} 批窗口 "
                            f"（超 {len(marks) - CHANGELOG_WINDOW} 条须按 510 批移入 {idx}）")
        for k, (i, b) in enumerate(marks):
            end = marks[k + 1][0] if k + 1 < len(marks) else len(lines)
            n = end - i
            if n > CHANGELOG_MAX_LINES:
                problems.append(f"{main} 第{b}批 占 {n} 行 > {CHANGELOG_MAX_LINES} 行上限"
                                f"（过程叙述压成一行摘要＋结论要点）")
        head = _head_batch_keys(main)
        if head:
            cur = _batch_keys(txt) | _batch_keys(_probe_read(idx, probe))
            missing = sorted(head - cur)
            if missing:
                problems.append(f"{main} 滑窗口丢了 {len(missing)} 个批号：{missing[:4]}"
                                f"（退出窗口的批号必须按 510 批补进 {idx}）")
    return problems


def check(index_text: str | None = None, *, probe: dict[str, str] | None = None) -> list[str]:
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
    problems += changelog_problems(probe)
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
    # ③ 现行副本必须放行（扩面后同时覆盖 CHANGELOG 窗口）
    if check():
        fails.append("现行文档面被误判")
    # ── 523 批扩面负例：只注入 CHANGELOG 文本，DOCS 面保持真盘，判红须来自目标分支 ──
    real = {rel: (ROOT / rel).read_text(encoding="utf-8")
            for pair in CHANGELOG_PAIRS for rel in pair}
    ly = real["liuyao/docs/CHANGELOG.md"]
    ls = ly.splitlines()
    # ④ 超窗口：末尾再挂一条现有批标题
    first_head = next(l for l in ls if BATCH_HEAD_RE.match(l))
    p4 = {**real, "liuyao/docs/CHANGELOG.md": ly + "\n" + first_head + "\n"}
    if not any("批窗口" in x for x in check(probe=p4)):
        fails.append("超窗口未被抓到")
    # ⑤ 单批超长：在**第一条与第二标题之间**塞 13 行过程叙述
    #    （插到第一条标题之前只会落在文件头里，不属于任何批次，抓不到东西）
    head_pos = [i for i, l in enumerate(ls) if BATCH_HEAD_RE.match(l)]
    nxt = head_pos[1]
    p5 = {**real, "liuyao/docs/CHANGELOG.md":
          "\n".join(ls[:nxt] + ["- 过程叙述"] * 13 + ls[nxt:]) + "\n"}
    if not any("行上限" in x for x in check(probe=p5)):
        fails.append("单批超长未被抓到")
    # ⑥ 滑窗口丢批号：主文件删掉最后一批，且索引里对应批号也一并抹掉
    #    （只删主文件不够——那正是「已经补进索引」的合法形态，不该判红）
    last = max(i for i, l in enumerate(ls) if BATCH_HEAD_RE.match(l))
    dropped = BATCH_HEAD_RE.match(ls[last]).group(1, 2)
    idx_rel = "liuyao/docs/CHANGELOG-HISTORY-INDEX.md"
    idx_wo = [l for l in real[idx_rel].splitlines()
              if not (BATCH_HEAD_RE.match(l) and BATCH_HEAD_RE.match(l).group(1, 2) == dropped)]
    p6 = {**real, "liuyao/docs/CHANGELOG.md": "\n".join(ls[:last]) + "\n",
          idx_rel: "\n".join(idx_wo) + "\n"}
    if not any("滑窗口丢了" in x for x in check(probe=p6)):
        fails.append("滑窗口丢批号未被抓到")
    # ⑦ 0 批次标题（路径解析失败不许报绿）
    if not any("0 个批次标题" in x for x in check(
            probe={**real, "liuyao/docs/CHANGELOG.md": "# 空\n"})):
        fails.append("0 批次未判红")
    for f in fails:
        print(f"  × selftest：{f}")
    if fails:
        return 1
    print("  √ selftest：漏登记／死链／超窗口／单批超长／丢批号／0 批次都抓到；现行文档面放行")
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
    for main, _ in CHANGELOG_PAIRS:
        txt = (ROOT / main).read_text(encoding="utf-8")
        k = len([l for l in txt.splitlines() if BATCH_HEAD_RE.match(l)])
        print(f"  √ CHANGELOG 窗口：{main} {k}/{CHANGELOG_WINDOW} 批，单批 ≤{CHANGELOG_MAX_LINES} 行")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
