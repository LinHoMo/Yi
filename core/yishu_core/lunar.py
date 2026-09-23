# -*- coding: utf-8 -*-
"""农历内核（Lunar Kernel）—— 公历 ↔ 农历（朔望月）换算。

干支历（节气定月）与农历（朔望定月）是两套月制，都要有：
  - 四柱、月建、旺衰 走 ganzhi_calendar（节气）；
  - 梅花「年月日时起卦」、小六壬「月日时起例」用的是**农历月日**（朔望月），
    观梅占「辰年十二月十七日申时」即农历十二月十七。
故本模块提供 1900-01-31 起 150 年的农历数据表（1900…2049）与双向换算。

真值源纪律：农历数据只此一份，学科不得另存；农历**干支**不在此算——
年干支/月干支（五虎遁）/日干支/时干支一律走 ganzhi_calendar。

数据与算法：天文台历年朔望月数据经压缩为 20-bit 整数（每项 1900 起一年）：
  低 4 位 = 闰月月份（0 = 无闰）；
  第 17 位 = 闰月大月(30)/小月(29)；
  其余 12 位自高至低 = 正月…腊月 大月(30)/小月(29)。
此表为中文农历推算的通行公开数据（多份实现一致），仅覆盖 1900–2049；
2049 之后超出表范围，调用方必须显式拒绝而非近似。
"""
from __future__ import annotations

from datetime import date, timedelta

# 1900…2049 逐年农历数据（每项一年，与上文档位约定一致）
LUNAR_INFO = [
    0x04bd8, 0x04ae0, 0x0a570, 0x054d5, 0x0d260, 0x0d950, 0x16554, 0x056a0, 0x09ad0, 0x055d2,
    0x04ae0, 0x0a5b6, 0x0a4d0, 0x0d250, 0x1d255, 0x0b540, 0x0d6a0, 0x0ada2, 0x095b0, 0x14977,
    0x04970, 0x0a4b0, 0x0b4b5, 0x06a50, 0x06d40, 0x1ab54, 0x02b60, 0x09570, 0x052f2, 0x04970,
    0x06566, 0x0d4a0, 0x0ea50, 0x06e95, 0x05ad0, 0x02b60, 0x186e3, 0x092e0, 0x1c8d7, 0x0c950,
    0x0d4a0, 0x1d8a6, 0x0b550, 0x056a0, 0x1a5b4, 0x025d0, 0x092d0, 0x0d2b2, 0x0a950, 0x0b557,
    0x06ca0, 0x0b550, 0x15355, 0x04da0, 0x0a5d0, 0x14573, 0x052d0, 0x0a9a8, 0x0e950, 0x06aa0,
    0x0aea6, 0x0ab50, 0x04b60, 0x0aae4, 0x0a570, 0x05260, 0x0f263, 0x0d950, 0x05b57, 0x056a0,
    0x096d0, 0x04dd5, 0x04ad0, 0x0a4d0, 0x0d4d4, 0x0d250, 0x0d558, 0x0b540, 0x0b5a0, 0x195a6,
    0x095b0, 0x049b0, 0x0a974, 0x0a4b0, 0x0b27a, 0x06a50, 0x06d40, 0x0af46, 0x0ab60, 0x09570,
    0x04af5, 0x04970, 0x064b0, 0x074a3, 0x0ea50, 0x06b58, 0x055c0, 0x0ab60, 0x096d5, 0x092e0,
    0x0c960, 0x0d954, 0x0d4a0, 0x0da50, 0x07552, 0x056a0, 0x0abb7, 0x025d0, 0x092d0, 0x0cab5,
    0x0a950, 0x0b4a0, 0x0baa4, 0x0ad50, 0x055d9, 0x04ba0, 0x0a5b0, 0x15176, 0x052b0, 0x0a930,
    0x07954, 0x06aa0, 0x0ad50, 0x05b52, 0x04b60, 0x0a6e6, 0x0a4e0, 0x0d260, 0x0ea65, 0x0d530,
    0x05aa0, 0x076a3, 0x096d0, 0x04bd7, 0x04ad0, 0x0a4d0, 0x1d0b6, 0x0d250, 0x0d520, 0x0dd45,
    0x0b5a0, 0x056d0, 0x055b2, 0x049b0, 0x0a577, 0x0a4b0, 0x0aa50, 0x1b255, 0x06d20, 0x0ada0,
]

LUNAR_MIN_YEAR = 1900
LUNAR_MAX_YEAR = 2049
LUNAR_EPOCH = date(1900, 1, 31)  # = 农历 1900 年正月初一


def _in_range(year: int) -> bool:
    return LUNAR_MIN_YEAR <= year <= LUNAR_MAX_YEAR


def leap_month_of(year: int) -> int:
    """该农历年闰月月份（0 = 无闰）。"""
    return LUNAR_INFO[year - LUNAR_MIN_YEAR] & 0xF


def month_days(year: int, month: int) -> int:
    """农历某月天数（month 1..12，不含闰月）。"""
    return 30 if (LUNAR_INFO[year - LUNAR_MIN_YEAR] & (0x10000 >> month)) else 29


def leap_month_days(year: int) -> int:
    """该农历年闰月天数（无闰时无意义，返回 0）。"""
    return 30 if (LUNAR_INFO[year - LUNAR_MIN_YEAR] & 0x10000) else 29


def year_days(year: int) -> int:
    """该农历年总天数（含闰月）。"""
    info = LUNAR_INFO[year - LUNAR_MIN_YEAR]
    days = sum(30 if (info & (0x10000 >> m)) else 29 for m in range(1, 13))
    lm = info & 0xF
    if lm:
        days += 30 if (info & 0x10000) else 29
    return days


def solar_to_lunar(d: date) -> dict | None:
    """公历日期 → 农历 {year, month, leap, day}；超出表范围返回 None。

    `month` 为 1..12 的农历月序；`leap` 表示该月是闰月。
    """
    if d < LUNAR_EPOCH or d.year > LUNAR_MAX_YEAR + 1:
        return None
    offset = (d - LUNAR_EPOCH).days
    year = LUNAR_MIN_YEAR
    while year <= LUNAR_MAX_YEAR and offset >= year_days(year):
        offset -= year_days(year)
        year += 1
    if year > LUNAR_MAX_YEAR:
        return None

    leap = leap_month_of(year)
    month = 1
    while month <= 12:
        if leap and month == leap:
            # 闰月：先小月，越过闰月才算正月后的下一个月
            for is_leap in (True, False):
                dim = leap_month_days(year) if is_leap else month_days(year, month)
                if offset < dim:
                    return {"year": year, "month": month, "leap": is_leap, "day": offset + 1}
                offset -= dim
        else:
            dim = month_days(year, month)
            if offset < dim:
                return {"year": year, "month": month, "leap": False, "day": offset + 1}
            offset -= dim
        month += 1
    return None


def lunar_to_solar(year: int, month: int, day: int, leap: bool = False) -> date | None:
    """农历 → 公历日期（闰月取该闰月；无该闰月时若 leap 置真返回 None）。"""
    if not _in_range(year) or not (1 <= month <= 12) or not (1 <= day <= 30):
        return None
    info = LUNAR_INFO[year - LUNAR_MIN_YEAR]
    days = 0
    for y in range(LUNAR_MIN_YEAR, year):
        days += year_days(y)
    leap_of = info & 0xF
    for m in range(1, month):
        if leap_of == m:
            days += 30 if (info & 0x10000) else 29
        days += 30 if (info & (0x10000 >> m)) else 29
    if leap:
        if leap_of != month:
            return None
        days += 30 if (info & 0x10000) else 29
    days += day - 1
    return LUNAR_EPOCH + timedelta(days=days)


def lunar_month_name(month: int, leap: bool = False) -> str:
    """农历月名（正月…腊月；闰月带「闰」前缀）。"""
    names = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"]
    return ("闰" if leap else "") + names[month - 1] + "月"
