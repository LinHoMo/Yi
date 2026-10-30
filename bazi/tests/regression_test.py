# -*- coding: utf-8 -*-
"""八字黑箱回归（A2-A·第三百三十五批）：固定样本 → 固定四柱与 conclusion 指纹。

为什么保留这层（而不是只靠 `dev_tools/golden.py`）：golden 是**看门狗**（漂移就红），
本器是**可读的定点断言**——它直接告诉后来者"哪一格的期望是什么值"，一眼能看出
是日历层、十神层还是格局层变了。两者样例刻意不同：本器只用 3 例手写日期，
golden 用 40 例语料分层（改语料不应挪动本器的覆盖面）。

期望值的来源：**定义式机械层**（年界立春、月界节气、日柱儒略日、十神表）。
它们不是"由引擎反推基准"（AGENTS.md §三.4 禁止的是把判读回填 expected）：
四柱由干支历换算**唯一确定**，conclusion 指纹只作回归哨兵，不代表正确率。

    python bazi/tests/regression_test.py
    python bazi/tests/regression_test.py -v
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
for _p in (str(DISC / "scripts"), str(DISC / "core")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from chart import chart  # noqa: E402
from analyze import analyze  # noqa: E402

# (公历时刻, 性别, 期望四柱, conclusion 规范化哈希前 16 位)
# 第三条的哈希于 368 批更新：从格真/假新增「天干层有气印比」判据后，本命（甲子 丙子 丙子 壬辰，
# 甲偏印相于子月、坐子得水生）由「从官杀·真从」改判「从官杀·假从」。A/B 逐字段实测（临时回退
# 判据后对拍 conclusion 全字段）：**只有 verdicts[2] 的 label 与 basis 两处变化**，
# pattern／strength／strength_score／useful_gods／dayun 全同——不是别的层动了。
# 373 批：`conclusion.dayun_liunian` 新增《滴天髓·歲運論》五式结构名
# （運伐歲／歲伐運／和〔干五合〕／好〔干同类〕），并修掉「运支=岁支仍标三合木局」的误标。
# 374 批：五式定义例门抓出「合先于克」的次序错（乙庚既合又克），改为合判定优先——
# 三条定点的 conclusion 因此再变一次。四柱与 pattern/strength 一律未变。
CASES = [
    ("1984-02-10 10:00", "男", "甲子 丙寅 甲戌 己巳", "12e616eb7d3a7532"),
    ("1996-11-11 22:00", "男", "丙子 己亥 壬子 辛亥", "3eaa687af9b7e7a1"),
    ("1984-12-08 08:00", "女", "甲子 丙子 丙子 壬辰", "be9ca9d98313fe20"),
]


def _sha(con: dict) -> str:
    return hashlib.sha256(json.dumps(con, ensure_ascii=False, sort_keys=True,
                                     default=str).encode("utf-8")).hexdigest()[:16]


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="八字固定样本回归（四柱 + conclusion 指纹）")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    errs: list[str] = []
    for dt, gender, want_pillars, want_sha in CASES:
        a = analyze(chart("回归", datetime_str=dt, gender=gender))
        got = " ".join((a.get("pillars") or {})[k]["ganzhi"] for k in ("year", "month", "day", "hour"))
        con = a.get("conclusion") or {}
        sha = _sha(con)
        if got != want_pillars:
            errs.append(f"{dt}：四柱 {got} ≠ 期望 {want_pillars}")
        if sha != want_sha:
            errs.append(f"{dt}：conclusion 指纹 {sha} ≠ 期望 {want_sha}")
        if args.verbose:
            print(f"  · {dt} {gender}：{got}｜{con.get('strength')}／{con.get('pattern')}｜{sha}")
    if errs:
        for e in errs:
            print(f"  × {e}")
        print("  → 先判责任方：四柱错查历法/时区；指纹错查哪一格行为变了（golden.py 可给逐字段 diff）")
        return 1
    print(f"  √ 回归：{len(CASES)} 例四柱与 conclusion 指纹全部与登记一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
