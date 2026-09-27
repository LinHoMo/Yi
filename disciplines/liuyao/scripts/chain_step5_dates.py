# -*- coding: utf-8 -*-
"""六爻思维链：基元表 / 断语库 / 通用辅助 / 五步推演 / 应期 / 叙事组装。（拆分自 thinking_chain.py，纯搬移不改逻辑；聚合入口见 thinking_chain.py）。"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel, kernel_dir

_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    ADVANCE_PAIRS,
    BRANCH_ELEMENTS,
    BREAK_PAIRS,
    CHONG_PAIRS,
    EARTHLY_BRANCHES,
    EIGHT_PALACES,
    HEAVENLY_STEMS,
    HEXAGRAM_TRIGRAMS,
    HE_PAIRS,
    KE_CYCLE,
    NAJIA_BRANCHES,
    RETREAT_PAIRS,
    SHENG_CYCLE,
    STEM_ELEMENTS,
    TOMB_MAP,
    palace_of_key,
    EARTHLY_BRANCHES as BRANCHES,
)

from datetime import datetime, timedelta

import json

import re

from pathlib import Path

from chain_narrate import _build_reasoning_chain, _get_hexagram_body_summary_note, find_classical_quotes
from chain_step4 import _detect_special_pattern, _user_reason
from chain_support import safe_get
from chain_tables import HEXAGRAM_LIUCHONG, HEXAGRAM_LIUHE, SAN_HE, _60_CYCLE_BASE, _BRANCH_CLASH_MAP, _ELEMENT_PEAK_MONTHS, _HE_MAP
from chain_verdicts import (
    CLASSICAL_INTERPRETATIONS as CINTERP,
    STEP5_CONFIDENCE as CONF_TXT,
    STEP5_FACTOR_REASONS as FREASON,
    STEP5_SPIRIT_REASONS as SPIRIT_TXT,
    STEP5_VERDICT_DESCS as VDESC,
    STEP5_YINGQI as YINGQI_TXT,
    note_text,
    vdesc,
)

def _day_branch_for_date(d: datetime) -> str:
    """
    Return the 地支 for the day of a given Gregian date.
    Uses the same algorithm as liuyao_engine.get_day_stem_branch fallback:
    2024-01-01 = 甲子日 (stem_idx=0, branch_idx=0).
    """
    delta = (d - _60_CYCLE_BASE).days
    branch_idx = delta % 12
    if branch_idx < 0:
        branch_idx += 12
    return BRANCHES[branch_idx]


def _next_date_with_day_branch(start_date: datetime, target_branch: str, max_days: int = 366) -> datetime | None:
    """
    Return the next date (from start_date forward) whose day-branch equals target_branch.
    Scans up to max_days (default 1 year + leap day).
    Returns None if not found within range.
    """
    if not target_branch or target_branch not in set(BRANCHES):
        return None
    d = start_date + timedelta(days=1)  # start FROM tomorrow
    for _ in range(max_days):
        if _day_branch_for_date(d) == target_branch:
            return d
        d += timedelta(days=1)
    return None


def _next_month_with_branch(start_date: datetime, target_branch: str) -> datetime | None:
    """下一个"月令"为该地支的日期。

    月令由十二节决定（立春寅、惊蛰卯…），不是公历月。旧实现写作
    `(d.month + 1) % 12` 的公历近似，在交节前后会整整错一个月——应期因此偏掉
    30 天。现委托历法内核求交节时刻。
    """
    if not target_branch or target_branch not in set(BRANCHES):
        return None
    try:
        from yishu_core import ganzhi_calendar as _gc
    except ImportError:
        import os
        import sys
        from pathlib import Path
        from kernel_path import kernel_dir
        core_dir = kernel_dir(__file__)
        if str(core_dir) not in sys.path:
            sys.path.insert(0, str(core_dir))
        from yishu_core import ganzhi_calendar as _gc
    inst = _gc.next_month_branch_instant(start_date, target_branch)
    return inst if inst is None else inst.replace(hour=12, minute=0)


def _add_months(d: datetime, months: int) -> datetime:
    """Add months to a date, capping day at month max."""
    month = d.month + months
    year = d.year
    while month > 12:
        month -= 12
        year += 1
    while month < 1:
        month += 12
        year -= 1
    import calendar
    max_day = calendar.monthrange(year, month)[1]
    day = min(d.day, max_day)
    return datetime(year, month, day)


def _dates_overlap(dt1: datetime | None, dt2: datetime | None, tol_days: int = 2) -> bool:
    """Check if two dates are within tol_days of each other (same event)."""
    if dt1 is None or dt2 is None:
        return False
    return abs((dt1 - dt2).days) <= tol_days


