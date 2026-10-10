# -*- coding: utf-8 -*-
"""strength —— 日主强弱判据 / 扶抑用神 / 格局成败救应入口。

从 ``pattern.py`` 拆出的强弱主干：``strength_and_pattern``、
``_god_detail`` / ``_has_yang_ren`` / ``_role_of_elem`` / ``_element_of_stem`` /
``_role`` / ``_ke_wo`` 均在 ``_common``；子判 ``_from_judge`` / ``judge_pattern_cheng_bai``
走 ``congrge``。
"""
from __future__ import annotations

from ._common import (
    _CB,
    _CONG,
    _god_detail,
    _has_yang_ren,
    _role,
    _role_of_elem,
    _element_of_stem,
    JU_BONUS_W,
    LAYER_WEIGHT,
    PATTERN_BY_MONTH_GOD,
    ROOT_HEAVY_STAGES,
    ROOT_HEAVY_W,
    ROOT_LIGHT_W,
    ROOT_STAGE_ELEMENTS,
    SHENG_CYCLE,
    KE_CYCLE,
    STRONG_THRESHOLD,
    WEAK_THRESHOLD,
    BRANCH_ELEMENTS,
    SAN_HE_GROUPS,
    SAN_HUI_GROUPS,
    CHONG_PAIRS,
    twelve_growth,
    STEM_ELEMENTS,
    tiaohou_of,
)
from .congrge import _from_judge, judge_pattern_cheng_bai


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
    sheng_fu = 0.0
    ke_xie_hao = 0.0
    month_main_god = ""
    details = []

    factors = chart_json.get("factors") or {}
    for pname in ("year", "month", "day", "hour"):
        block = factors.get(pname) or {}
        gods = block.get("ten_gods") or []
        branch = (pillars.get(pname) or {}).get("branch") or ""
        for item in gods:
            if not isinstance(item, dict):
                continue
            god = item.get("ten_god") or ""
            layer = item.get("layer") or "本气"
            w = LAYER_WEIGHT.get(layer, 0.25)
            role = _role(god)
            root_stage = ""
            if role == "比劫" and day_elem in ROOT_STAGE_ELEMENTS and branch:
                root_stage = twelve_growth(day_elem, branch) or ""
                if root_stage:
                    w = ROOT_HEAVY_W if root_stage in ROOT_HEAVY_STAGES else ROOT_LIGHT_W
            if role in ("印", "比劫"):
                sheng_fu += w
            elif role in ("官杀", "食伤", "财"):
                ke_xie_hao += w
            if pname == "month" and layer == "本气":
                month_main_god = god
            entry = {"pillar": pname, "god": god, "layer": layer, "role": role, "w": w}
            if root_stage:
                entry["root_stage"] = root_stage
            details.append(entry)

    # 得令
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

    # 三支全会聚合势
    sheng_fu_for_from = sheng_fu
    ju_items = []
    ju_bonus = 0.0
    branch_list = [(pillars.get(p) or {}).get("branch") or ""
                   for p in ("year", "month", "day", "hour")]
    branch_list = [b for b in branch_list if b]
    ju_chong: dict = {}
    for b in branch_list:
        for o in branch_list:
            if o != b and ((b, o) in CHONG_PAIRS or (o, b) in CHONG_PAIRS):
                ju_chong.setdefault(b, set()).add(o)
    for table, kind in ((SAN_HE_GROUPS, "三合局"), (SAN_HUI_GROUPS, "三会方")):
        for elem, grp in table.items():
            members = sorted({b for b in branch_list if b in grp})
            if len(members) != 3:
                continue
            if any(BRANCH_ELEMENTS.get(o) != BRANCH_ELEMENTS.get(m)
                   for m in members for o in ju_chong.get(m, ())):
                continue
            if elem == day_elem or SHENG_CYCLE.get(elem) == day_elem:
                ju_items.append({"kind": kind, "element": elem,
                                 "branches": members, "w": JU_BONUS_W,
                                 "provenance": "engineering_mapping"})
                ju_bonus += JU_BONUS_W
    if ju_bonus:
        sheng_fu += ju_bonus
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

    from_kind, from_type, from_basis, tentative_from = _from_judge(
        chart_json, details, day_stem, decree=decree, sheng_fu=sheng_fu_for_from)

    if strength == "偏旺":
        useful = ["官杀", "食伤", "财"]
        taboo = ["印", "比劫"]
    elif strength == "偏弱":
        useful = ["印", "比劫"]
        taboo = ["官杀", "食伤", "财"]
    else:
        useful = ["印", "财", "官杀"]
        taboo = ["比劫"]

    cb = judge_pattern_cheng_bai(pattern, chart_json,
                                 tentative_from=bool(tentative_from),
                                 strength=strength)

    return {
        "strength": strength,
        "strength_score": score,
        "decree_bonus": decree,
        "sheng_fu": round(sheng_fu_for_from, 2),
        "ke_xie_hao": round(ke_xie_hao, 2),
        "ju_bonus": {"total": round(ju_bonus, 2), "items": ju_items},
        "pattern": pattern,
        "pattern_basis": pattern_basis,
        "pattern_cheng_bai": cb["pattern_cheng_bai"],
        "pattern_cheng_bai_basis": cb["basis"],
        "tentative_special": tentative_from,
        "from_kind": from_kind,
        "from_type": from_type,
        "from_basis": from_basis,
        "tiaohou": tiaohou_of(month_branch, day_stem),
        "useful_gods": useful,
        "taboo_gods": taboo,
        "useful_basis": (
            "身旺喜克泄耗（官杀/食伤/财），身弱喜生扶（印/比劫）——扶抑用神通行口径"
            if strength != "中和"
            else "中和取五行流通（印/财/官杀）"
        ),
        "details": details,
    }
