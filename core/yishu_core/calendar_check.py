# -*- coding: utf-8 -*-
"""干支历自检：`python core/yishu_core/calendar_check.py [--verbose]`

不依赖任何记忆中的"某年某日交节时刻"，而是断言天文学性质与结构不变量——
这类断言写错会立刻暴露，比抄一串日期更可靠。

检查分四组：
  A 天文自洽：节气回代黄经误差、节气日期窗口、节气间隔、全年 24 节气有序
  B 干支结构：立春定年界（含立春前后一分钟）、五虎遁、五鼠遁、时辰边界
  C 日序连续：逐日 +1 不跳号、两个独立锚点互证
  D 影响面：与旧固定近似表(SOLAR_TERM_DATES)逐月比对，统计有多少天月建会改变
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from ganzhi_calendar import (  # noqa: E402
    EARTHLY_BRANCHES, HEAVENLY_STEMS, TWELVE_JIE, TWELVE_QI,
    day_ganzhi_index, ganzhi_of, ganzhi_pair, hour_branch_index,
    solar_apparent_longitude, solar_term_instant, solar_terms_of_year, julius_day,
)
from runtime import force_utf8_stdio  # noqa: E402

FAILS: list[str] = []
PASSES = 0


def check(name: str, ok: bool, detail: str = ""):
    global PASSES
    if ok:
        PASSES += 1
    else:
        FAILS.append(f"{name}: {detail}")
    return ok


# ---------------------------------------------------------------- A 天文自洽

def check_astronomy(years: range):
    max_err = 0.0
    for y in years:
        for name, deg in [(n, d) for n, d, _ in TWELVE_JIE] + TWELVE_QI:
            inst = solar_term_instant(y, name)
            jd = julius_day(inst - timedelta(hours=8))  # 北京→UTC
            actual = solar_apparent_longitude(jd)
            err = abs((deg - actual + 180.0) % 360.0 - 180.0)
            max_err = max(max_err, err)
    check("A1 节气回代黄经误差 < 0.02°", max_err < 0.02, f"最大 {max_err:.4f}°")

    windows = {"立春": (2, (3, 6)), "惊蛰": (3, (5, 8)), "清明": (4, (4, 7)),
               "立夏": (5, (5, 8)), "芒种": (6, (5, 8)), "小暑": (7, (6, 9)),
               "立秋": (8, (7, 9)), "白露": (9, (7, 10)), "寒露": (10, (7, 10)),
               "立冬": (11, (6, 9)), "大雪": (12, (6, 9)), "小寒": (1, (5, 8)),
               "冬至": (12, (20, 24)), "夏至": (6, (20, 23)),
               "春分": (3, (19, 23)), "秋分": (9, (21, 25))}
    bad = []
    for y in years:
        for name, (mon, (d_lo, d_hi)) in windows.items():
            dd = solar_term_instant(y, name)
            if dd.month != mon or not (d_lo <= dd.day <= d_hi):
                bad.append(f"{y}-{name}={dd.date()} 期望 {mon}/{d_lo}-{d_hi}")
    check("A2 节气落在公认日期窗口", not bad, f"{len(bad)} 项越界，如 {bad[:3]}")

    gaps_bad = []
    for y in years:
        terms = solar_terms_of_year(y)
        for a, b in zip(terms, terms[1:]):
            gap = (b["instant"] - a["instant"]).total_seconds() / 86400.0
            if not (13.0 <= gap <= 18.0):
                gaps_bad.append(f"{y} {a['name']}→{b['name']} {gap:.2f}天")
    check("A3 相邻节气 13–18 天", not gaps_bad, f"{gaps_bad[:3]}")

    order_bad = []
    for y in years:
        terms = solar_terms_of_year(y)
        if [t["instant"] for t in terms] != sorted(t["instant"] for t in terms):
            order_bad.append(str(y))
    check("A4 全年 24 节气时序单调", not order_bad, f"{order_bad[:3]}")


# ---------------------------------------------------------------- B 干支结构

def check_ganzhi_structure():
    ok, detail = True, ""
    for y in range(1990, 2031):
        li = solar_term_instant(y, "立春")
        before = ganzhi_pair((y - 1 - 1984) % 60)
        after = ganzhi_pair((y - 1984) % 60)
        m1 = ganzhi_of(li - timedelta(minutes=1), boundary="instant").year_ganzhi
        m2 = ganzhi_of(li + timedelta(minutes=1), boundary="instant").year_ganzhi
        # 日模式：交节当日 00:01 即算新年
        m3 = ganzhi_of(li.replace(hour=0, minute=1), boundary="day").year_ganzhi
        if m1 != before or m2 != after or m3 != after:
            ok, detail = False, f"{y}: instant前{m1}(应{before}) instant后{m2}(应{after}) day当日{m3}"
            break
    check("B1 立春定年界：instant 精确到分钟、day 当日即换", ok, detail)

    check("B2 1984 立春后为甲子年",
          ganzhi_of(solar_term_instant(1984, "立春") + timedelta(hours=2)).year_ganzhi == "甲子",
          ganzhi_of(solar_term_instant(1984, "立春") + timedelta(hours=2)).year_ganzhi)

    # 已知边界：2024-02-04 立春（龙年始于当日），故 02-03 仍癸卯、02-05 已甲辰
    y_prev = ganzhi_of(datetime(2024, 2, 3, 12)).year_ganzhi
    y_next = ganzhi_of(datetime(2024, 2, 5, 12)).year_ganzhi
    check("B3 2024-02-03→癸卯 / 02-05→甲辰",
          y_prev == "癸卯" and y_next == "甲辰", f"{y_prev} / {y_next}")

    # 五虎遁口诀
    expected = {"甲": "丙寅", "己": "丙寅", "乙": "戊寅", "庚": "戊寅", "丙": "庚寅",
                "辛": "庚寅", "丁": "壬寅", "壬": "壬寅", "戊": "甲寅", "癸": "甲寅"}
    bad = []
    for y in range(1984, 2044):
        li = solar_term_instant(y, "立春") + timedelta(hours=1)
        g = ganzhi_of(li)
        if expected[g.year_ganzhi[0]] != g.month_ganzhi:
            bad.append(f"{y} 年干{g.year_ganzhi[0]} → 月柱{g.month_ganzhi} 应{expected[g.year_ganzhi[0]]}")
    check("B4 五虎遁：立春当月必为该年干所起之寅月", not bad, f"{bad[:3]}")

    # 一年十二节 → 月支依次 寅卯辰巳午未申酉戌亥子丑
    for y in (2000, 2024, 2026):
        terms = sorted(
            [(solar_term_instant(y, n), n) for n, _, _ in TWELVE_JIE if n != "小寒"]
            + [(solar_term_instant(y + 1, "小寒"), "小寒")],
            key=lambda t: t[0])
        got = [ganzhi_of(inst + timedelta(minutes=1)).month_branch for inst, _ in terms]
        want = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
        check(f"B5 {y} 年十二节月支顺序", got == want, f"{got}")

    # 时辰边界
    hb = hour_branch_index
    check("B6 时辰边界 22:59亥/23:00子/00:59子/01:00丑",
          (hb(22, 59), hb(23, 0), hb(0, 59), hb(1, 0)) == (11, 0, 0, 1),
          f"{(hb(22,59), hb(23,0), hb(0,59), hb(1,0))}")

    # 五鼠遁：甲日子时起甲子
    g = ganzhi_of(datetime(2024, 1, 1, 0, 30))  # 2024-01-01 甲子日
    check("B7 甲子日子时 = 甲子时",
          g.day_ganzhi == "甲子" and g.hour_ganzhi == "甲子", f"{g.day_ganzhi} {g.hour_ganzhi}")


# ---------------------------------------------------------------- C 日序连续

def check_day_sequence():
    d = date(2020, 1, 1)
    prev = day_ganzhi_index(d)
    bad = []
    for _ in range(1500):
        d += timedelta(days=1)
        cur = day_ganzhi_index(d)
        if (prev + 1) % 60 != cur:
            bad.append(str(d))
            break
        prev = cur
    check("C1 连续 1500 日日序 +1 不跳号", not bad, f"{bad[:3]}")

    a = ganzhi_pair(day_ganzhi_index(date(2024, 1, 1)))
    b = ganzhi_pair(day_ganzhi_index(date(1949, 10, 1)))
    check("C2 双锚点互证：2024-01-01 与 1949-10-01 同为甲子日",
          a == "甲子" and b == "甲子", f"{a} / {b}")

    # 夜子时（23:00–23:59）不作次日：日柱仍是当日历日
    d = date(2026, 9, 22)
    late = ganzhi_of(datetime(2026, 9, 22, 23, 30)).day_ganzhi
    early = ganzhi_of(datetime(2026, 9, 23, 0, 30)).day_ganzhi
    check("C3 夜子时不偏移日柱（23:30 作当日、次日 00:30 作次日）",
          late == ganzhi_pair(day_ganzhi_index(d))
          and early == ganzhi_pair(day_ganzhi_index(d + timedelta(days=1))),
          f"{late}/{early} 应 {ganzhi_pair(day_ganzhi_index(d))}/{ganzhi_pair(day_ganzhi_index(d + timedelta(days=1)))}")


# ---------------------------------------------------------------- D 影响面

LEGACY_TERM_DAYS = {1: (6, 1), 2: (4, 2), 3: (6, 3), 4: (5, 4), 5: (6, 5), 6: (6, 6),
                    7: (7, 7), 8: (8, 8), 9: (8, 9), 10: (8, 10), 11: (7, 11), 12: (7, 0)}


def check_vs_legacy(start: date, end: date) -> dict:
    """逐日比较新内核与旧固定近似表的月支/年支，统计受影响天数。"""
    month_diff = year_diff = total = 0
    examples = []
    d = start
    while d <= end:
        dt = datetime(d.year, d.month, d.day, 12, 0)
        g = ganzhi_of(dt)
        total += 1
        # 旧算法月支
        if d.day >= LEGACY_TERM_DAYS[d.month][0]:
            legacy_branch = LEGACY_TERM_DAYS[d.month][1]
            lm = d.month
        else:
            lm = d.month - 1 if d.month > 1 else 12
            legacy_branch = LEGACY_TERM_DAYS[lm][1]
        if EARTHLY_BRANCHES.index(g.month_branch) != legacy_branch:
            month_diff += 1
            if len(examples) < 6:
                examples.append(f"{d} 月支 {g.month_branch}←旧{EARTHLY_BRANCHES[legacy_branch]}")
        # 旧算法在 1–3 月从不判立春年界，直接与"当年干支"比较
        if d.month in (1, 2, 3):
            if g.year_ganzhi != ganzhi_pair((d.year - 1984) % 60):
                year_diff += 1
        d += timedelta(days=1)
    return {"total": total, "month_diff": month_diff, "year_diff": year_diff,
            "examples": examples}


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="干支历内核自检")
    ap.add_argument("--span", type=int, default=40, help="天文检查覆盖年数")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    years = range(1996, 1996 + args.span)
    check_astronomy(years)
    check_ganzhi_structure()
    check_day_sequence()

    print(f"自检：{PASSES} 项通过，{len(FAILS)} 项失败")
    for f in FAILS:
        print(f"  × {f}")

    span = check_vs_legacy(date(2020, 1, 1), date(2026, 12, 31))
    pct = span["month_diff"] * 100.0 / span["total"] if span["total"] else 0.0
    print(f"\n与旧固定近似表对比 2020-01-01…2026-12-31（{span['total']} 天）")
    print(f"  月建不同：{span['month_diff']} 天（{pct:.1f}%）")
    print(f"  年柱不同（立春前一月内旧法不判年界）：{span['year_diff']} 天")
    if args.verbose:
        for e in span["examples"]:
            print(f"    · {e}")

    if FAILS:
        print("\n结论：内核有错，先修内核。")
        return 1
    print("\n结论：干支历内核自洽。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
