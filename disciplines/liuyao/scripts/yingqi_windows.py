# -*- coding: utf-8 -*-
"""相对应期 → 绝对日窗（有锚日才换算；无锚日保持语义对齐）。

次日/当日/年内/月余 等在 strict 下：
1) 有 case 年月日 → 换算日期窗，比对引擎 yingqi_dates[].date
2) 无锚日 → RHYTHM_PAIRS 语义对齐（已在 evaluate）
"""
from __future__ import annotations

from datetime import datetime, timedelta
import re

REL_RULES = [
    # (关键词, 天数窗下限, 上限, 标签)
    (("当日", "当天"), 0, 0, "当日"),
    (("次日",), 1, 1, "次日"),
    (("月余", "旺相之月"), 20, 50, "月余窗"),
    (("年内", "经年"), 1, 365, "年内窗"),
]


def resolve_case_anchor(exp_input: dict, case: dict) -> datetime | None:
    """从案例 input.date / 顶层 year-month-day 解析锚日。"""
    y = case.get("year")
    m = case.get("month")
    d = case.get("day")
    if y and m and d:
        try:
            return datetime(int(y), int(m), int(d))
        except ValueError:
            return None
    text = str((exp_input or {}).get("date") or "")
    # 尽力抽公历 YYYY-M-D
    m2 = re.search(r"(20\d{2})-(\d{1,2})-(\d{1,2})", text)
    if m2:
        try:
            return datetime(int(m2.group(1)), int(m2.group(2)), int(m2.group(3)))
        except ValueError:
            return None
    return None


def relative_window(x_yq: str) -> tuple[int, int, str] | None:
    for keys, lo, hi, label in REL_RULES:
        if any(k in x_yq for k in keys):
            return lo, hi, label
    return None


def date_in_window(anchor: datetime, date_str: str, lo: int, hi: int) -> bool:
    try:
        dt = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
    except ValueError:
        return False
    delta = (dt - anchor).days
    return lo <= delta <= hi
