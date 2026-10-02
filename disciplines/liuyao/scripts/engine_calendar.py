# -*- coding: utf-8 -*-
"""六爻引擎历法：干支历推算（年/月/日/时干支）与真太阳时校正、时辰与子时换算。聚合入口见 liuyao_engine.py。"""

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel, kernel_dir

_ensure_kernel(__file__)

import math
import os
import sys
from datetime import datetime


def _load_ganzhi_kernel():
    """定位并导入历法内核。找不到时明确报错，绝不退回近似算法。"""
    try:
        from yishu_core import ganzhi_calendar as _gc  # 已安装为包
        return _gc
    except ImportError:
        pass
    core_dir = kernel_dir(__file__)
    if not (core_dir / "yishu_core").is_dir():
        raise RuntimeError(f"缺少历法内核目录：{core_dir / 'yishu_core'}")
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))
    from yishu_core import ganzhi_calendar as _gc
    return _gc


_GANZHI = _load_ganzhi_kernel()


GANZHI_BOUNDARY = os.environ.get("YI_GANZHI_BOUNDARY", "day")


def _noon(year, month, day):
    return datetime(year, month, day, 12, 0)


def get_year_stem_branch(year, month=0, day=0):
    """年干支。以立春为年界：未过立春仍作前一年。"""
    if month > 0 and day > 0:
        dt = _noon(year, month, day)
    else:
        dt = _noon(year, 6, 15)  # 未给月日 → 取年中，必在立春之后
    return _GANZHI.ganzhi_of(dt, boundary=GANZHI_BOUNDARY).year_ganzhi


def get_month_stem_branch(year, month, day):
    """月干支。以十二节定月支，五虎遁定月干。"""
    return _GANZHI.ganzhi_of(_noon(year, month, day), boundary=GANZHI_BOUNDARY).month_ganzhi


def get_day_stem_branch(year, month, day):
    """日干支。由儒略日数直接取模，不查表、无累积误差。"""
    return _GANZHI.day_ganzhi_of(year, month, day)


def get_hour_stem_branch(day_stem, hour):
    """时干支。五鼠遁，日干 + 时辰地支。"""
    return _GANZHI.hour_ganzhi_of(day_stem, hour)


def apply_true_solar_time(year, month, day, hour, longitude, standard_longitude=120.0):
    """
    真太阳时校正
    返回校正后的 hour 和 minute。
    - longitude: 经度, 东经为正
    - standard_longitude: 标准子午线经度 (中国CST = 120)

    时差 = (经度 - 标准子午线) * 4 分钟
    均时差(Equation of Time) 采用简化公式: ~±16分钟
    """
    # 经度差修正 (每度4分钟)
    longitude_offset_minutes = (longitude - standard_longitude) * 4.0

    # 均时差简化公式 (单位: 分钟)
    # 基于日数n (1-365), B = (n-81)*360/365
    day_of_year = (datetime(year, month, day) - datetime(year, 1, 1)).days + 1
    B = math.radians((day_of_year - 81) * 360 / 365.0)
    eot_minutes = 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)

    total_offset = longitude_offset_minutes + eot_minutes

    # 应用到输入时间
    total_minutes = hour * 60 + int(total_offset)

    while total_minutes < 0:
        total_minutes += 1440
    while total_minutes >= 1440:
        total_minutes -= 1440

    corrected_hour = total_minutes // 60
    corrected_minute = total_minutes % 60

    # 转为时辰 (23-1点子时, 1-3点丑时, etc.)
    shichen = _hour_to_shichen(corrected_hour, corrected_minute)

    return {
        "corrected_hour": corrected_hour,
        "corrected_minute": corrected_minute,
        "shichen": shichen,
        "offset_minutes": int(total_offset),
    }


def _hour_to_shichen(hour, minute=0):
    """将小时和分钟转换为十二时辰名称"""
    total = hour * 60 + minute
    if total >= 23 * 60 or total < 1 * 60:
        return "子"
    if total < 3 * 60:
        return "丑"
    if total < 5 * 60:
        return "寅"
    if total < 7 * 60:
        return "卯"
    if total < 9 * 60:
        return "辰"
    if total < 11 * 60:
        return "巳"
    if total < 13 * 60:
        return "午"
    if total < 15 * 60:
        return "未"
    if total < 17 * 60:
        return "申"
    if total < 19 * 60:
        return "酉"
    if total < 21 * 60:
        return "戌"
    return "亥"


def handle_zi_hour(hour, minute, year, month, day):
    """子时（夜子／晨子）判定。

    默认口径：日辰以当日历日为准，夜子时不作次日。
      - 夜子时（旧码误标"早子时"）23:00–23:59 → 日柱用当日
      - 晨子时（旧码误标"晚子时"）00:00–00:59 → 日柱用当日

    历史缺陷（2026-09-22 修）：旧实现在 hour == 0 时返回**翌日**日柱，
    等于把 00:00–01:00 起的所有卦的日辰推后一天——任何流派都不持此说。
    欲采"23 点换日"一派，用 `--zi-hour-type late` 显式指定，不默认生效。

    Returns:
        dict（含 type/shichen/day_* 与说明），非子时返回 None
    """
    base_date = datetime(year, month, day)

    if hour == 23:
        zi_type, label = "night_zi", "夜子时(23:00-00:00)"
    elif hour == 0:
        zi_type, label = "morning_zi", "晨子时(00:00-01:00)"
    else:
        return None

    return {
        "type": zi_type,
        "shichen": "子",
        "day_date": base_date,
        "day_year": base_date.year,
        "day_month": base_date.month,
        "day_day": base_date.day,
        "description": f"{label}，{base_date.strftime('%Y-%m-%d')}日子时，日柱用当日",
    }

