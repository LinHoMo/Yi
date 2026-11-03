# -*- coding: utf-8 -*-
"""step5 应期日期工具（T31 瘦身第一步：从 step5.py 提取纯日期函数）。

三个纯函数，不依赖 step5 内部状态，只依赖内核象数基元与链表常量。
calculate_yingqi 等调用方从本模块 import（函数名保持原下划线前缀）。
"""
from __future__ import annotations

from datetime import datetime, timedelta

try:
    from yishu_core.symbols import EARTHLY_BRANCHES as BRANCHES
except ImportError:  # pragma: no cover
    BRANCHES = []

try:
    from chain_tables import _60_CYCLE_BASE
except ImportError:  # pragma: no cover
    from datetime import datetime as _dt
    _60_CYCLE_BASE = _dt(2024, 1, 1)


def _day_branch_for_date(d: datetime) -> str:
    """Gregory 日期 → 日地支（2024-01-01 = 甲子日）。"""
    delta = (d - _60_CYCLE_BASE).days
    branch_idx = delta % 12
    if branch_idx < 0:
        branch_idx += 12
    return BRANCHES[branch_idx]


def _next_date_with_day_branch(start_date: datetime, target_branch: str, max_days: int = 366) -> datetime | None:
    """下一日-branch = target_branch 的日期（前向扫描 max_days）。"""
    if not target_branch or target_branch not in set(BRANCHES):
        return None
    d = start_date + timedelta(days=1)  # start FROM tomorrow
    for _ in range(max_days):
        if _day_branch_for_date(d) == target_branch:
            return d
        d += timedelta(days=1)
    return None


def _dates_overlap(dt1: datetime | None, dt2: datetime | None, tol_days: int = 2) -> bool:
    """Check if two dates are within tol_days of each other (same event)."""
    if dt1 is None or dt2 is None:
        return False
    return abs((dt1 - dt2).days) <= tol_days
