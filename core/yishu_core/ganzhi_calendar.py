# -*- coding: utf-8 -*-
"""干支历内核（Ganzhi Calendar Kernel）

六爻、八字、择吉共用同一套时空基准，故独立成模块，单一真值源。

三条历法法则（皆为本模块的责任边界）：
  1. 年界在立春，不在元旦、不在农历正月初一 —— 未过立春仍作前一年干支。
  2. 月界在十二"节"（非"气"）—— 立春起寅月，惊蛰起卯月，余推。
  3. 日界以夜子时为界（23:00 之后仍作当日；00:00–01:00 属当日之子时）。

节气交节时刻由太阳视黄经数值求解得到，不查近似表。
精度：太阳黄经用 Meeus 低阶截断级数（约 0.01°），折算到时刻约 ±15 分钟。
交节若落在当日 23:45–00:15 之间，日界可能因该误差翻转，`near_midnight` 会置真并给出警告。
ΔT（力学时与世界时之差，当代约 69 秒）小于上述误差，故未单独修正。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta

# ---------------------------------------------------------------- 基础表（唯一真值源）

HEAVENLY_STEMS = "甲乙丙丁戊己庚辛壬癸"
EARTHLY_BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

BRANCH_ELEMENT = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}
STEM_ELEMENT = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}

# 十二节：名称、太阳视黄经（度）、交节之后的月支索引（子0 丑1 寅2 …亥11）
TWELVE_JIE = [
    ("小寒", 285.0, 1),
    ("立春", 315.0, 2),
    ("惊蛰", 345.0, 3),
    ("清明", 15.0, 4),
    ("立夏", 45.0, 5),
    ("芒种", 75.0, 6),
    ("小暑", 105.0, 7),
    ("立秋", 135.0, 8),
    ("白露", 165.0, 9),
    ("寒露", 195.0, 10),
    ("立冬", 225.0, 11),
    ("大雪", 255.0, 0),
]

# 十二中气（只用于展示与应期参照，不参与定月）
TWELVE_QI = [
    ("冬至", 270.0), ("大寒", 300.0), ("雨水", 330.0), ("春分", 0.0),
    ("谷雨", 30.0), ("小满", 60.0), ("夏至", 90.0), ("大暑", 120.0),
    ("处暑", 150.0), ("秋分", 180.0), ("霜降", 210.0), ("小雪", 240.0),
]

# 五虎遁：年干 → 寅月起始月干索引
TIGER_MONTH_STEM = {"甲": 2, "己": 2, "乙": 4, "庚": 4, "丙": 6,
                    "辛": 6, "丁": 8, "壬": 8, "戊": 0, "癸": 0}
# 五鼠遁：日干 → 子时起始时干索引
RAT_HOUR_STEM = {"甲": 0, "己": 0, "乙": 2, "庚": 2, "丙": 4,
                 "辛": 4, "丁": 6, "壬": 6, "戊": 8, "癸": 8}

BEIJING_OFFSET = timedelta(hours=8)  # 中国标准时间 UTC+8
_JDN_EPOCH_DELTA = 1721425           # JDN = date.toordinal() + 1721425
_DAY_GANZHI_ANCHOR = 49              # (JDN + 49) % 60 == 0 → 甲子


# ---------------------------------------------------------------- 太阳黄经

def julius_day(dt_utc: datetime) -> float:
    """UTC 日期时间 → 儒略日（含小数）。"""
    return (dt_utc - datetime(2000, 1, 1, 12, 0, 0)).total_seconds() / 86400.0 + 2451545.0


def jd_to_beijing(jd: float) -> datetime:
    """儒略日 → 北京时间（naive datetime，年月日时分秒）。"""
    utc = datetime(2000, 1, 1, 12, 0, 0) + timedelta(days=jd - 2451545.0)
    beijing = utc + BEIJING_OFFSET
    return beijing.replace(microsecond=0)


def solar_apparent_longitude(jd_tt: float) -> float:
    """太阳视黄经（度，0–360）。Meeus《天文算法》第 25 章低阶截断式。"""
    t = (jd_tt - 2451545.0) / 36525.0
    mean_lon = 280.46645 + 36000.76983 * t + 0.0003032 * t * t
    mean_anom = math.radians(357.52910 + 35999.05029 * t - 0.0001536 * t * t)
    eq_center = (
        (1.914600 - 0.004817 * t - 0.000014 * t * t) * math.sin(mean_anom)
        + (0.019993 - 0.000101 * t) * math.sin(2 * mean_anom)
        + 0.000289 * math.sin(3 * mean_anom)
    )
    true_lon = mean_lon + eq_center
    omega = math.radians(125.04 - 1934.136 * t)
    apparent = true_lon - 0.00569 - 0.00478 * math.sin(omega)
    return apparent % 360.0


def _lon_diff(target: float, actual: float) -> float:
    """带绕行的角差，落在 (-180, 180]。"""
    return (target - actual + 180.0) % 360.0 - 180.0


_TERM_CACHE: dict[tuple[int, str], datetime] = {}


def solar_term_instant(year: int, name: str) -> datetime:
    """求 named 节气在 `year` 年的交节时刻（北京时间）。

    在该节气的可能日期窗口内对黄经做二分求根。太阳黄经年内单调递增，
    以 ±15 天为括号即可保证同号端点。
    """
    key = (year, name)
    if key in _TERM_CACHE:
        return _TERM_CACHE[key]

    table = {n: deg for n, deg, _ in TWELVE_JIE} | {n: deg for n, deg in TWELVE_QI}
    if name not in table:
        raise KeyError(f"未知节气：{name}")
    target = table[name]

    # 粗估：以该节气黄经相对春分(0°，约 3 月 20 日)的位置推一个初始日期
    approx_offset = ((target - 0.0) % 360.0) / 360.0 * 365.2422
    guess = datetime(year, 3, 20) + timedelta(days=approx_offset)
    if guess.year > year:
        guess -= timedelta(days=365)
    if guess.year < year:
        guess += timedelta(days=365)

    lo = julius_day(guess - timedelta(days=20))
    hi = julius_day(guess + timedelta(days=20))
    f_lo = _lon_diff(target, solar_apparent_longitude(lo))
    f_hi = _lon_diff(target, solar_apparent_longitude(hi))
    if f_lo * f_hi > 0:  # 极端情况（岁差累积/初值偏差）→ 扩窗重试
        lo = julius_day(guess - timedelta(days=90))
        hi = julius_day(guess + timedelta(days=90))
        f_lo = _lon_diff(target, solar_apparent_longitude(lo))
        f_hi = _lon_diff(target, solar_apparent_longitude(hi))
        if f_lo * f_hi > 0:
            raise RuntimeError(f"{year} 年 {name} 求解失败：括号内无根")

    for _ in range(64):
        mid = (lo + hi) / 2.0
        f_mid = _lon_diff(target, solar_apparent_longitude(mid))
        if abs(f_mid) < 1e-7 or (hi - lo) < 1e-9:
            break
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid

    instant = jd_to_beijing(mid)
    _TERM_CACHE[key] = instant
    return instant


def solar_terms_of_year(year: int) -> list[dict]:
    """该历年内 24 节气交节时刻（按时间排序）。"""
    items = []
    for name, deg in TWELVE_QI:
        items.append({"name": name, "degree": deg, "instant": solar_term_instant(year, name)})
    for name, deg, _ in TWELVE_JIE:
        items.append({"name": name, "degree": deg, "instant": solar_term_instant(year, name)})
    items.sort(key=lambda x: x["instant"])
    return items


# ---------------------------------------------------------------- 四柱
#
# 交节当天算旧月还是新月，是流派问题：
#   boundary="day"    交节当日整日按新节／新年（多数排盘软件与老版 SOLAR_TERM_DATES 的做法）
#   boundary="instant" 精确到交节时刻，未交节仍作旧月（天文严格）
# 默认 "day"，以保持既有断卦行为不漂移；需要严格天文口径时显式传 "instant"。

def year_ganzhi_index(dt: datetime, boundary: str = "day") -> int:
    """60 甲子索引，年界取立春。"""
    li_chun = solar_term_instant(dt.year, "立春")
    if boundary == "instant":
        passed = dt >= li_chun
    else:
        passed = dt.date() >= li_chun.date()
    gz_year = dt.year if passed else dt.year - 1
    return (gz_year - 1984) % 60


def month_branch_index(dt: datetime, boundary: str = "day") -> tuple[int, str, datetime]:
    """当前所处的月支索引、所据之节、该节交节时刻。"""
    candidates = []
    for y in (dt.year - 1, dt.year, dt.year + 1):
        for name, _, branch in TWELVE_JIE:
            inst = solar_term_instant(y, name)
            if (inst.date() <= dt.date()) if boundary == "day" else (inst <= dt):
                candidates.append((inst, name, branch))
    if not candidates:
        raise RuntimeError(f"{dt} 超出可计算范围")
    inst, name, branch = max(candidates, key=lambda c: c[0])
    return branch, name, inst


def day_ganzhi_index(d: date) -> int:
    """60 甲子日序，由儒略日数直接取模，不查表、不累积误差。"""
    jdn = d.toordinal() + _JDN_EPOCH_DELTA
    return (jdn + _DAY_GANZHI_ANCHOR) % 60


def hour_branch_index(hour: int, minute: int = 0) -> int:
    """时辰地支索引（23:00–00:59 为子）。"""
    total = hour * 60 + minute
    if total >= 23 * 60 or total < 60:
        return 0
    return (total + 60) // 120 % 12


def ganzhi_pair(index60: int) -> str:
    return HEAVENLY_STEMS[index60 % 10] + EARTHLY_BRANCHES[index60 % 12]


def hour_ganzhi_of(day_stem: str, hour: int, minute: int = 0) -> str:
    """五鼠遁：由日干与时辰定时柱。"""
    branch = hour_branch_index(hour, minute)
    stem = (RAT_HOUR_STEM[day_stem] + branch) % 10
    return HEAVENLY_STEMS[stem] + EARTHLY_BRANCHES[branch]


def day_ganzhi_of(year: int, month: int, day: int) -> str:
    return ganzhi_pair(day_ganzhi_index(date(year, month, day)))


@dataclass
class GanzhiMoment:
    """一个时刻的完整干支历表达。"""
    dt_beijing: str
    year_ganzhi: str
    month_ganzhi: str
    day_ganzhi: str
    hour_ganzhi: str
    month_branch: str
    month_of_jie: str          # 定月所据之节
    month_jie_instant: str     # 该节交节时刻
    li_chun_instant: str       # 本年立春时刻
    day_of_jie: bool           # 当日是否恰为交节日
    near_midnight: bool        # 交节落在日界附近 → 精确到时刻时结果会翻转
    boundary: str              # day / instant
    solar_terms_ahead: list    # 未来若干节气（供应期推算）

    def to_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        return (f"{self.year_ganzhi}年 {self.month_ganzhi}月 "
                f"{self.day_ganzhi}日 {self.hour_ganzhi}时")


def ganzhi_of(dt: datetime, boundary: str = "day") -> GanzhiMoment:
    """北京时间 datetime → 四柱干支。"""
    if dt.tzinfo is not None:
        dt = dt.astimezone(tz=None).replace(tzinfo=None)

    y_idx = year_ganzhi_index(dt, boundary)
    m_branch, m_jie, m_jie_inst = month_branch_index(dt, boundary)

    # 月干：五虎遁。立春所在寅月为偏移 0，月支决定顺行位
    y_stem = HEAVENLY_STEMS[y_idx % 10]
    m_stem_idx = (TIGER_MONTH_STEM[y_stem] + (m_branch - 2) % 12) % 10
    month_gz = HEAVENLY_STEMS[m_stem_idx] + EARTHLY_BRANCHES[m_branch]

    # 日柱：夜子时（23:00 后）仍作当日
    d_idx = day_ganzhi_index(dt.date())
    day_gz = ganzhi_pair(d_idx)

    # 时柱：五鼠遁，用当日日干
    day_stem = HEAVENLY_STEMS[d_idx % 10]
    h_branch = hour_branch_index(dt.hour, dt.minute)
    h_stem_idx = (RAT_HOUR_STEM[day_stem] + h_branch) % 10
    hour_gz = HEAVENLY_STEMS[h_stem_idx] + EARTHLY_BRANCHES[h_branch]

    terms = solar_terms_of_year(dt.year)
    day_of_jie = any(t["instant"].date() == dt.date() for t in terms)
    # 交节落在日界 ±15 分钟内 → 本模块精度（约 15 分钟）不足以判定整日归属
    near_midnight = _minutes_from_midnight(m_jie_inst) <= 15

    ahead = [
        {"name": t["name"], "instant": t["instant"].strftime("%Y-%m-%d %H:%M")}
        for t in (terms + solar_terms_of_year(dt.year + 1))
        if t["instant"] > dt
    ][:8]

    return GanzhiMoment(
        dt_beijing=dt.strftime("%Y-%m-%d %H:%M"),
        year_ganzhi=ganzhi_pair(y_idx),
        month_ganzhi=month_gz,
        day_ganzhi=day_gz,
        hour_ganzhi=hour_gz,
        month_branch=EARTHLY_BRANCHES[m_branch],
        month_of_jie=m_jie,
        month_jie_instant=m_jie_inst.strftime("%Y-%m-%d %H:%M"),
        li_chun_instant=solar_term_instant(dt.year, "立春").strftime("%Y-%m-%d %H:%M"),
        day_of_jie=day_of_jie,
        near_midnight=near_midnight,
        boundary=boundary,
        solar_terms_ahead=ahead,
    )


def _minutes_from_midnight(inst: datetime) -> int:
    """交节时刻距最近一次日界（00:00）的分钟数。"""
    return min(inst.hour * 60 + inst.minute, 1440 - (inst.hour * 60 + inst.minute))


# ---------------------------------------------------------------- 应期推算用

def next_jie_after(dt: datetime) -> dict:
    """dt 之后最近的"节"（定月令者），供"出月/逢节"类应期。"""
    best = None
    for y in (dt.year, dt.year + 1):
        for name, _, _ in TWELVE_JIE:
            inst = solar_term_instant(y, name)
            if inst.date() > dt.date() and (best is None or inst < best[0]):
                best = (inst, name)
    if best is None:
        raise RuntimeError(f"{dt} 之后未找到节气（超出可计算范围）")
    return {"name": best[1], "instant": best[0],
            "date": best[0].strftime("%Y-%m-%d"), "ganzhi_day": day_ganzhi_of(
                best[0].year, best[0].month, best[0].day)}


def prev_jie_before(dt: datetime) -> dict:
    """dt 之前最近的"节"（定月令者）。

    逆行大运起运岁取「出生到上一节」的天数（与 next_jie_after 相对）。
    """
    best = None
    for y in (dt.year - 1, dt.year):
        for name, _, _ in TWELVE_JIE:
            inst = solar_term_instant(y, name)
            if inst.date() < dt.date() and (best is None or inst > best[0]):
                best = (inst, name)
    if best is None:
        raise RuntimeError(f"{dt} 之前未找到节气（超出可计算范围）")
    return {"name": best[1], "instant": best[0],
            "date": best[0].strftime("%Y-%m-%d"), "ganzhi_day": day_ganzhi_of(
                best[0].year, best[0].month, best[0].day)}


def next_month_branch_instant(dt: datetime, target_branch: str) -> datetime | None:
    """dt 之后第一个使月支成为 `target_branch` 的交节时刻。

    应期里"应于某月"指的是月令（由节决定），不是公历月——用 (month+1)%12 这类
    公历近似会在交节前后错整整一个月。
    """
    if target_branch not in EARTHLY_BRANCHES:
        return None
    want = EARTHLY_BRANCHES.index(target_branch)
    best = None
    for y in (dt.year, dt.year + 1, dt.year + 2):
        for name, _, branch in TWELVE_JIE:
            inst = solar_term_instant(y, name)
            if branch == want and inst > dt and (best is None or inst < best):
                best = inst
    return best


def months_ahead(dt: datetime, n: int = 12) -> list[dict]:
    """自 dt 起 n 个月的月令表（月支、起于何节何日），供应期展示。"""
    out = []
    cursor = dt
    for _ in range(n):
        branch, jie, inst = month_branch_index(cursor)
        out.append({
            "month_branch": EARTHLY_BRANCHES[branch],
            "jie": jie,
            "since": inst.strftime("%Y-%m-%d"),
        })
        nxt = next_jie_after(inst)
        cursor = nxt["instant"]
    return out


def find_solar_date(day_ganzhi: str, month_branch: str | None = None,
                    around: datetime | None = None, horizon_days: int = 365 * 6,
                    limit: int = 8) -> list[dict]:
    """反查满足「日柱 = day_ganzhi（且月令 = month_branch）」的真实公历日期。

    古籍案例通常只记"巳月戊戌日占求财"，没有公历日期。旧评测管线于是把这类案例
    一律塞进 2024-06-01 10 时，再由月支反推——于是应期日历日期全部建立在假日期上。
    本函数把干支信息还原成真实日期，旬空、应期、真太阳时才有着落。

    日柱 60 天一循环，叠加月令（约 30 天窗口）后在一个候选里唯一，故按距 `around`
    的远近返回前 `limit` 个候选，由调用者择一。
    """
    if not day_ganzhi or len(day_ganzhi) != 2:
        return []
    if day_ganzhi[0] not in HEAVENLY_STEMS or day_ganzhi[1] not in EARTHLY_BRANCHES:
        return []
    if month_branch is not None and month_branch not in EARTHLY_BRANCHES:
        return []

    center = around or datetime(2024, 6, 1, 12, 0)
    want_day = HEAVENLY_STEMS.index(day_ganzhi[0])
    want_branch = EARTHLY_BRANCHES.index(day_ganzhi[1])
    want_mb = EARTHLY_BRANCHES.index(month_branch) if month_branch else None

    lo = (center - timedelta(days=horizon_days)).date()
    hi = (center + timedelta(days=horizon_days)).date()
    hits = []
    d = lo
    while d <= hi:
        if day_ganzhi_index(d) % 10 == want_day and day_ganzhi_index(d) % 12 == want_branch:
            inst = datetime(d.year, d.month, d.day, 12, 0)
            mb, jie, _ = month_branch_index(inst)
            if want_mb is None or mb == want_mb:
                hits.append({"date": d.isoformat(), "dt": inst, "jie": jie,
                             "distance": abs((d - center.date()).days)})
        d += timedelta(days=1)

    hits.sort(key=lambda h: h["distance"])
    return hits[:limit]
