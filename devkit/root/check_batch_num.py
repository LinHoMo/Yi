# -*- coding: utf-8 -*-
"""批次×提交门（第三百四十六批）：CHANGELOG 标题批号必须在提交信息里出现。

    python devkit/root/check_batch_num.py
    python devkit/root/check_batch_num.py --selftest

为什么需要它：`readout_ledger.py` 的「登记×提交在册」项已守这条，但它属于六爻
dev_tools 的账台，不在根级 CI；A6-INT 把 `check_batch_num.py` 登记进
`devkit/MANIFEST.json` 的 root 列表后一直未实现（ARCHITECTURE-PLAN §五.5 欠账）。
本门是那条欠账的根级独立入口：读 HEAD 版本的两科 CHANGELOG（主文件＋历史索引），
抽 `## 日期 第N批` 标题；读 `git log` 全信息体的「第N批」；标题批号必须在提交信息
里出现，否则就是「写了条目没提交」的半个虚构面。

口径：
  · 批号阈值 >175（现代史；176 之前的旧编号不参与）；
  · `SETTLED_ORPHANS` **从 `liuyao/dev_tools/readout_ledger.py` 的 AST 读取**，
    不另抄一份允许名单（单源）；读取失败即判红，不静默放行；
  · 提交信息提到、CHANGELOG 标题没有的批号只报 NOTE（历史合并入库/范围简写
    的已知形态），不作判红——本门守的是「登记了却没提交」，不是反向考古；
  · `heads` 为空即判红（路径解析失败不许伪装成「没有孤儿」——AGENTS §四.8）。
"""
from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "liuyao" / "dev_tools" / "readout_ledger.py"
CHANGELOGS = (
    "liuyao/docs/CHANGELOG.md",
    "liuyao/docs/CHANGELOG-HISTORY-INDEX.md",
    "bazi/docs/CHANGELOG.md",
    "bazi/docs/CHANGELOG-HISTORY-INDEX.md",
)
HEAD_RE = re.compile(r"^## \d{4}-\d{2}-\d{2} 第([零〇一二两三四五六七八九十百千]+)批", re.M)
CN = {"〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
      "六": 6, "七": 7, "八": 8, "九": 9}


def parse_cn(text: str) -> int:
    tot = num = 0
    for ch in text:
        if ch in CN:
            num = num * 10 + CN[ch]
        elif ch == "十":
            tot += (num or 1) * 10
            num = 0
        elif ch == "百":
            tot += (num or 1) * 100
            num = 0
        elif ch == "千":
            tot += (num or 1) * 1000
            num = 0
    return tot + num


def read_head(path: str) -> str:
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{path}"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"HEAD 读不到 {path}：{r.stderr.strip()[:80]}")
    return r.stdout


def headed_batches() -> set[int]:
    heads: set[int] = set()
    for path in CHANGELOGS:
        heads |= {parse_cn(x) for x in HEAD_RE.findall(read_head(path))}
    return {h for h in heads if h}


def mentioned_batches() -> tuple[set[int], str]:
    body = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%B\x01"],
                          capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    cn = {parse_cn(x) for x in re.findall(r"第([零〇一二两三四五六七八九十百千]+)批", body)}
    ar = {int(x) for x in re.findall(r"第(\d{1,4})批", body)}
    return (cn | ar), body


def load_settled() -> set[int]:
    tree = ast.parse(LEDGER.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "SETTLED_ORPHANS":
                    value = ast.literal_eval(node.value)
                    return {int(k) for k in value}
    raise SystemExit("readout_ledger.py 里找不到 SETTLED_ORPHANS——单源允许名单读取失败")


def audit(heads: set[int], men: set[int], settled: set[int]) -> tuple[list[int], list[int]]:
    if not heads:
        return ([-1], [])  # -1 是哨兵：heads 空＝解析失败，不是「没有孤儿」
    orphans = sorted(h for h in heads if h > 175 and h not in men)
    unsettled = [h for h in orphans if h not in settled]
    reverse = sorted(h for h in men if h > 175 and h not in heads)
    return unsettled, reverse


def selftest() -> list[str]:
    fails: list[str] = []
    if parse_cn("三百四十四") != 344:
        fails.append("中文批号解析错：三百四十四 ≠ 344")
    if audit({344}, {344}, set()) != ([], []):
        fails.append("登记与提交一致时误判红")
    if audit({344}, set(), set()) != ([344], []):
        fails.append("登记了没提交应判红")
    if audit({344}, set(), {344}) != ([], []):
        fails.append("已结案孤儿仍判红")
    if audit(set(), set(), set())[0] != [-1]:
        fails.append("heads 空未显形（0 结果必须判红）")
    settled = load_settled()
    if 221 not in settled:
        fails.append("SETTLED_ORPHANS 单源读取失败（缺 221）")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser(description="批次×提交门（根级）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    heads = headed_batches()
    men, _ = mentioned_batches()
    settled = load_settled()
    unsettled, reverse = audit(heads, men, settled)
    print("批次×提交门（HEAD 口径）：")
    print(f"  · CHANGELOG 标题批号（>175） {len([h for h in heads if h > 175])} 个")
    print(f"  · 提交信息提及批号           {len([h for h in men if h > 175])} 个")
    print(f"  · 未结案孤儿                 {len(unsettled)} 个（已结案 {len(settled)} 条）")
    if reverse:
        print(f"  · NOTE 提交提及但标题无（历史范围简写） {reverse[:12]}"
              + (" …" if len(reverse) > 12 else ""))
    for h in unsettled:
        if h == -1:
            print("  × CHANGELOG 标题解析为 0——路径/正则失配，不许当「没有孤儿」")
        else:
            print(f"  × 第{h}批 已登记但没有任何提交信息提及（SETTLED_ORPHANS 之外）")
    if not unsettled:
        print("  √ 所有已登记批号都在提交信息里，未结案孤儿为 0")

    st_fail: list[str] = []
    if args.selftest:
        st_fail = selftest()
        print(f"  [selftest] 负例{'全部抓到' if not st_fail else '失效'}"
              "（五类：解析错／一致误伤／登记未提交／已结案误伤／0 结果）")
        for p in st_fail:
            print("  ×", p)

    if unsettled or st_fail:
        return 1
    print("批次×提交门通过。解锁＝在提交信息里写「第N批」或按 SETTLED_ORPHANS 登记结案。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
