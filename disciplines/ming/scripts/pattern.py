# -*- coding: utf-8 -*-
"""命·格局与强弱（纯机械表驱动，无命运断语）。

规则口径（通行子平，可回溯）：
- 藏干十神本/中/余气权重 1.0 / 0.5 / 0.25
- 生扶 = 印 + 比劫；克泄耗 = 官杀 + 食伤 + 财
- 身旺喜克泄耗，身弱喜生扶（《渊海子平》扶抑用神通行口径）
- 格局取月支本气十神正格名；从格条件仅作 tentative 标注
大运顺逆走 core.ming_tables.dayun_direction；起运岁数按三日=一年近似。
"""
from __future__ import annotations

from yishu_core.ming_tables import (
    canggan_ten_gods,
    dayun_direction,
    DAYS_PER_LUCK_YEAR,
)
from yishu_core.symbols import BRANCH_ELEMENTS, STEM_ELEMENTS, SHENG_CYCLE, KE_CYCLE

# 十神 → 作用类
TEN_GOD_GROUP = {
    "比肩": "比劫",
    "劫财": "比劫",
    "正印": "印",
    "偏印": "印",
    "食神": "食伤",
    "伤官": "食伤",
    "正财": "财",
    "偏财": "财",
    "正官": "官杀",
    "偏官": "官杀",
    "七杀": "官杀",
}

# 月令本气十神 → 正格名
PATTERN_BY_MONTH_GOD = {
    "正官": "正官格",
    "偏官": "偏官格",
    "七杀": "偏官格",
    "正印": "正印格",
    "偏印": "偏印格",
    "食神": "食神格",
    "伤官": "伤官格",
    "正财": "正财格",
    "偏财": "偏财格",
    "比肩": "建禄格",
    "劫财": "月刃格",
}

LAYER_WEIGHT = {"本气": 1.0, "中气": 0.5, "余气": 0.25}

# 身旺/身弱临界（strength_score：生扶 − 克泄耗，含得令加权）
WEAK_THRESHOLD = -1.5
STRONG_THRESHOLD = 1.5


def _role(ten_god: str) -> str:
    return TEN_GOD_GROUP.get(ten_god, "")


def _element_of_stem(stem: str) -> str:
    return STEM_ELEMENTS.get(stem, "")


def strength_and_pattern(chart_json: dict) -> dict:
    """四柱 → {strength, strength_score, pattern, pattern_basis, useful_gods, taboo_gods}。"""
    pillars = chart_json.get("pillars") or {}
    day_stem = (pillars.get("day") or {}).get("stem") or ""
    day_elem = _element_of_stem(day_stem)
    if not day_stem:
        return {
            "strength": "未知",
            "strength_score": 0.0,
            "pattern": "未知",
            "pattern_basis": "缺日主",
            "useful_gods": [],
            "taboo_gods": [],
        }

    # 藏干十神打分
    sheng_fu = 0.0  # 印 + 比劫
    ke_xie_hao = 0.0  # 官杀 + 食伤 + 财
    month_main_god = ""
    details = []

    factors = chart_json.get("factors") or {}
    for pname in ("year", "month", "day", "hour"):
        block = factors.get(pname) or {}
        gods = block.get("ten_gods") or []
        for item in gods:
            if not isinstance(item, dict):
                continue
            god = item.get("ten_god") or ""
            layer = item.get("layer") or "本气"
            w = LAYER_WEIGHT.get(layer, 0.25)
            role = _role(god)
            # 日支比劫/印也算，但日干本身不重复计
            if role in ("印", "比劫"):
                sheng_fu += w
            elif role in ("官杀", "食伤", "财"):
                ke_xie_hao += w
            if pname == "month" and layer == "本气":
                month_main_god = god
            details.append({"pillar": pname, "god": god, "layer": layer, "role": role, "w": w})

    # 得令：月支本气五行生扶日主则 +1.2，克泄耗则 −1.2
    month_branch = (pillars.get("month") or {}).get("branch") or ""
    month_elem = BRANCH_ELEMENTS.get(month_branch, "")
    decree = 0.0
    if month_elem and day_elem:
        if month_elem == day_elem or SHENG_CYCLE.get(month_elem) == day_elem:
            decree = 1.2
            sheng_fu += decree
        elif SHENG_CYCLE.get(day_elem) == month_elem or KE_CYCLE.get(day_elem) == month_elem or KE_CYCLE.get(month_elem) == day_elem:
            decree = -1.2
            ke_xie_hao += 1.2

    score = round(sheng_fu - ke_xie_hao, 2)
    if score >= STRONG_THRESHOLD:
        strength = "偏旺"
    elif score <= WEAK_THRESHOLD:
        strength = "偏弱"
    else:
        strength = "中和"

    pattern = PATTERN_BY_MONTH_GOD.get(month_main_god, "")
    pattern_basis = ""
    if month_main_god:
        pattern = pattern or "杂气/未分类"
        pattern_basis = f"月令本气十神={month_main_god}"
    else:
        pattern = "未知"
        pattern_basis = "缺月令十神"

    # 从格 tentative：克泄耗压倒性且无生扶根
    tentative_from = None
    if sheng_fu < 0.5 and ke_xie_hao >= 4.0:
        tentative_from = "从弱（tentative）"
    elif ke_xie_hao < 0.5 and sheng_fu >= 4.0:
        tentative_from = "从强/专旺（tentative）"

    if strength == "偏旺":
        useful = ["官杀", "食伤", "财"]
        taboo = ["印", "比劫"]
    elif strength == "偏弱":
        useful = ["印", "比劫"]
        taboo = ["官杀", "食伤", "财"]
    else:
        useful = ["印", "财", "官杀"]  # 中和取流通
        taboo = ["比劫"]  # 防过旺

    return {
        "strength": strength,
        "strength_score": score,
        "decree_bonus": decree,
        "sheng_fu": round(sheng_fu, 2),
        "ke_xie_hao": round(ke_xie_hao, 2),
        "pattern": pattern,
        "pattern_basis": pattern_basis,
        "tentative_special": tentative_from,
        "useful_gods": useful,
        "taboo_gods": taboo,
        "useful_basis": (
            "身旺喜克泄耗（官杀/食伤/财），身弱喜生扶（印/比劫）——扶抑用神通行口径"
            if strength != "中和"
            else "中和取五行流通（印/财/官杀）"
        ),
        "details": details,
    }


def dayun_table(chart_json: dict) -> list[dict]:
    """大运 8 步（顺逆按年干阴阳×性别；起运岁≈距节气日数/3，见 DAYS_PER_LUCK_YEAR）。"""
    from datetime import datetime
    from yishu_core.ganzhi_calendar import next_jie_after

    pillars = chart_json.get("pillars") or {}
    year_stem = (pillars.get("year") or {}).get("stem") or ""
    month_gz = (pillars.get("month") or {}).get("ganzhi") or ""
    gender = (chart_json.get("birth") or {}).get("gender") or ""
    day_stem = (pillars.get("day") or {}).get("stem") or ""
    birth_dt_s = (chart_json.get("birth") or {}).get("datetime") or ""

    direction = dayun_direction(year_stem, gender) if year_stem and gender else None
    if not direction or len(month_gz) < 2:
        return []

    # 起运：出生到下一节的日数 / DAYS_PER_LUCK_YEAR（三日=一年，通行近似）
    start_age = 3
    approximate = True
    if birth_dt_s:
        try:
            bdt = datetime.strptime(str(birth_dt_s)[:16], "%Y-%m-%d %H:%M")
            jie = next_jie_after(bdt)
            jie_dt = jie.get("instant") if isinstance(jie, dict) else None
            if isinstance(jie_dt, datetime):
                days = max((jie_dt - bdt).total_seconds() / 86400.0, 0.0)
                start_age = round(days / float(DAYS_PER_LUCK_YEAR), 1)
                approximate = True  # 未计三日=一年的余数折算规则
        except Exception:
            start_age = 3

    stems = "甲乙丙丁戊己庚辛壬癸"
    branches = "子丑寅卯辰巳午未申酉戌亥"
    ms, mb = month_gz[0], month_gz[1]
    try:
        si = stems.index(ms)
        bi = branches.index(mb)
    except ValueError:
        return []

    step = 1 if direction == "forward" else -1
    out = []
    for i in range(8):
        s = stems[(si + step * (i + 1)) % 10]
        b = branches[(bi + step * (i + 1)) % 12]
        gz = s + b
        gods = canggan_ten_gods(day_stem, b) if day_stem else []
        main_god = next((g.get("ten_god") for g in gods if g.get("layer") == "本气"), "")
        a0 = round(start_age + i * 10, 1)
        out.append({
            "index": i + 1,
            "ganzhi": gz,
            "start_age": a0,
            "end_age": round(a0 + 9.9, 1),
            "ten_god": main_god,
            "approximate": approximate,
        })
    return out
