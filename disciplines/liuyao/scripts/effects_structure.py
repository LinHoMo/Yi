# -*- coding: utf-8 -*-
"""古典断法增强·effects_structure.py（拆分自 classical_rules_effects，纯搬移不改逻辑；门面见 classical_rules_effects）。"""

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel, kernel_dir

_ensure_kernel(__file__)

from yishu_core.najia import najia_branch

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
)

from classical_support import _branch_element, _combined_strength, _element_to_relation, _find_stage_at, _find_use_god_positions, _get_use_god_strength_level, _infer_use_god_category, _pos_to_name, _relation_element, _score_fanyin, _score_fuyin, _strength_score, determine_six_relation, element_strength_in_month, find_hexagram_body, g_day_cn, get_changed_hexagram_branch, get_month_strength_description, get_stages_of_interest, get_twelve_growth_stage, is_ba_zu_chong, is_ba_zu_he
from classical_tables import KE_WO, SAN_HE, SELF_PUNISHMENTS, SHENG_WO, SIX_RELATIONS, THREE_PUNISHMENTS_CYCLIC, THREE_PUNISHMENTS_MUTUAL, TRANSFORMATION_PATTERNS, TWELVE_GROWTH
from chain_verdicts import EFFECT_LABELS, EFFECT_PHRASES, CLASSICAL_INTERPRETATIONS as CINTERP, ctext, ctpl


def analyze_hexagram_body(result):
    """
    卦身法分析：卦身为一卦之身体，代表事物的本体与根基。

    Returns
    -------
    dict with keys: body_position, body_element, body_relation,
        meaning, classical_rule, implications
    """
    hex_info = result.get("original_hexagram", {})
    generation = hex_info.get("generation", "")

    # 解析 generation 为数字
    gen_map = {
        "六世": 6, "五世": 5, "四世": 4, "三世": 3,
        "二世": 2, "一世": 1,
        "游魂": 7, "归魂": 8,
    }
    gen_num = gen_map.get(generation, 0)

    if gen_num == 0:
        return {
            "body_position": None,
            "body_element": "",
            "body_relation": "",
            "meaning": ctext("cr_030"),
            "classical_rule": "阳世子起顺推，阴世应起逆推",
            "implications": [],
        }

    # 获取日干
    dt = result.get("divination_time", {})
    day_sb = dt.get("day_stem_branch", "甲")
    day_stem = day_sb[0] if day_sb else "甲"

    body_pos = find_hexagram_body(gen_num, day_stem)

    # 获取对应爻信息
    yao_lines = hex_info.get("yao_lines", [])
    body_yao = {}
    for yao in yao_lines:
        if yao.get("position") == body_pos:
            body_yao = yao
            break

    body_element = _branch_element(body_yao.get("earthly_branch", ""))
    body_relation = body_yao.get("six_relation", "")
    is_empty = body_yao.get("earthly_branch", "") in result.get("empty_branches", [])

    # 判断卦身与世爻/用神的关系
    response_texts = []

    # 卦身持世检查
    gen_map_reverse = {"六世": 6, "五世": 5, "四世": 4, "三世": 3,
                       "二世": 2, "一世": 1, "游魂": 4, "归魂": 3}
    world_pos = gen_map_reverse.get(generation, 1)

    if body_pos == world_pos:
        response_texts.append(CINTERP["hex_body_world"]["text"])

    # 卦身临用神检查
    use_positions = _find_use_god_positions(result)
    if body_pos in use_positions:
        response_texts.append(CINTERP["hex_body_use"]["text"])

    # 卦身空破
    if is_empty:
        response_texts.append(CINTERP["hex_body_empty"]["text"])

    # 卦身临官鬼
    if body_relation == "官鬼":
        response_texts.append(CINTERP["hex_body_officer"]["text"])
    elif body_relation == "妻财":
        response_texts.append(CINTERP["hex_body_wealth"]["text"])
    elif body_relation == "子孙":
        response_texts.append(CINTERP["hex_body_child"]["text"])

    if not response_texts:
        response_texts.append(ctpl("crt_025", _pos_to_name(body_pos), body_relation))

    return {
        "body_position": body_pos,
        "body_element": body_element,
        "body_relation": body_relation,
        "meaning": ctpl("crt_004", _pos_to_name(body_pos)),
        "classical_rule": "阳世子起顺推，阴世应起逆推",
        "implications": [
            CINTERP["hex_body_use_arrow"]["text"],
            CINTERP["hex_body_ji_arrow"]["text"],
            CINTERP["hex_body_world_arrow"]["text"],
            CINTERP["hex_body_empty_arrow"]["text"],
        ],
        "body_is_world": body_pos == world_pos,
        "body_is_empty": is_empty,
        "body_is_use_god": body_pos in use_positions,
        "specific_notes": response_texts,
    }


def analyze_element_strength(result):
    """
    纳甲四柱旺衰总结：基于月建日辰的五行旺衰体系。
    
    返回：
        {
            "month_branch": str,
            "month_element": str,
            "day_branch": str,
            "day_element": str,
            "strength_description": str,  # 如"木旺火相水休金囚土死"
            "use_god_advice": str,        # 通用旺衰判断建议
            "details": [
                {
                    "position": int,
                    "name": str,
                    "branch": str,
                    "element": str,
                    "six_relation": str,
                    "month_strength": str,  # 在月建的状态
                    "day_strength": str,    # 在日辰的状态
                    "overall": str,         # 综合状态
                },
                ...
            ],
            "summary": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    palace_element = hex_info.get("palace_element", "")

    if not yao_lines:
        return {"month_branch": "", "month_element": "", "day_branch": "",
                "day_element": "", "strength_description": "",
                "details": [], "summary": ctext("cr_018")}

    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""

    month_element = _branch_element(month_branch)
    day_element = _branch_element(day_branch)
    empty_branches = result.get("empty_branches", [])

    strength_desc = get_month_strength_description(month_element)

    details = []
    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        elem = _branch_element(branch)
        m_str = element_strength_in_month(elem, month_element)
        d_str = element_strength_in_month(elem, day_element)
        overall = _combined_strength(elem, month_element, day_element)

        # 特殊标记
        special = []
        if branch in empty_branches:
            special.append(ctext("cr_031"))
        if is_ba_zu_chong(branch, month_branch):
            special.append(ctext("cr_032"))
        if is_ba_zu_chong(branch, day_branch):
            special.append(ctext("cr_033"))
        stage = get_twelve_growth_stage(elem, day_branch)
        if stage in ("墓", "绝", "死"):
            special.append(f"{stage}")

        details.append({
            "position": yao["position"],
            "name": yao.get("name", ""),
            "branch": branch,
            "element": elem,
            "six_relation": yao.get("six_relation", ""),
            "month_strength": m_str,
            "day_strength": d_str,
            "overall": overall,
            "growth_stage": stage,
            "special_markers": special,
        })

    # 通用建议
    advice_parts = [
        ctpl("crt_005", month_branch, month_element, day_branch, day_element),
        ctpl("crt_006", strength_desc),
    ]

    # 综合总结
    summary_lines = advice_parts.copy()
    strong_yaos = [d for d in details if d["overall"] in ("旺", "相")]
    weak_yaos = [d for d in details if d["overall"] in ("偏弱", "衰")]

    if strong_yaos:
        s_desc = "、".join(
            f"{d['six_relation']}({d['branch']},{d['month_strength']}/{d['day_strength']})"
            for d in strong_yaos
        )
        summary_lines.append(ctpl("crt_026", s_desc))
    if weak_yaos:
        w_desc = "、".join(
            f"{d['six_relation']}({d['branch']},{d['month_strength']}/{d['day_strength']})"
            for d in weak_yaos
        )
        summary_lines.append(ctpl("crt_027", w_desc))

    return {
        "month_branch": month_branch,
        "month_element": month_element,
        "day_branch": day_branch,
        "day_element": day_element,
        "strength_description": strength_desc,
        "palace_element": palace_element,
        "details": details,
        "summary": "。".join(summary_lines),
    }


def analyze_three_punishments(result):
    """
    三刑分析（卜筮正宗定量版）：区分完整三刑、待刑、自刑。

    规则：
      - 循环刑（无恩寅巳申、恃势丑戌未）：三字全见 → 完整三刑（极凶）；
        仅见两字 → 待刑（待月日补齐方成刑）。
      - 互刑（无礼子卯）：两字相见即成刑。
      - 自刑（辰午酉亥）：同一地支两见以上。

    返回：
        {
            "has_punishment": bool,
            "punishments": [
                {
                    "type": str,              # 刑的类型
                    "completeness": str,      # "完整" | "待刑" | "成刑"
                    "branches_present": [str], # 卦中及月日出现的地支
                    "missing": [str],          # 缺失的地支（待刑时）
                    "formed_by": str,          # "卦内" | "待月日补齐"
                    "positions": [str],        # 涉及的位置
                    "description": str,
                },
                ...
            ],
            "total_score": float,  # 完整三刑 -1.0, 待刑 -0.3, 无礼成刑 -0.5, 自刑 -0.3/次
            "summary": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    if not yao_lines:
        return {"has_punishment": False, "punishments": [], "total_score": 0.0, "summary": ctext("cr_018")}

    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""

    # ── 收集所有地支及其来源 ──
    # 三刑口径（P0-1 修正）：
    #   1) 以本卦六爻为主（hex_branches）；
    #   2) 月建/日辰仅作"催刑"（external_branches），参与补足但不按完整三刑计；
    #   3) 变卦地支不参与本卦三刑（化出之爻不构成原局刑伤）。
    hex_branches = []
    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        if branch:
            hex_branches.append((branch, ctpl("crt_070", _pos_to_name(yao['position']))))

    external_branches = []
    if month_branch:
        external_branches.append((month_branch, ctpl("crt_053", month_branch)))
    if day_branch:
        external_branches.append((day_branch, ctpl("crt_054", day_branch)))

    branches_with_source = hex_branches + external_branches

    # ── 建立全量地支集合（用于完整性判断）──
    all_branches_set = set(b for b, _ in branches_with_source)
    hex_set = set(b for b, _ in hex_branches)

    # ── 辅助：从 branches_with_source 中找出指定地支的所有来源位置 ──
    def _find_sources(branchesNeeded):
        return [(b, s) for b, s in branches_with_source if b in branchesNeeded]

    punishments = []
    total_score = 0.0

    # ── 1. 循环刑（无恩、恃势）：三字全见 vs 仅见两字 ──
    for ptype, required in THREE_PUNISHMENTS_CYCLIC.items():
        required_set = set(required)
        present_set = all_branches_set & required_set
        present = sorted(present_set, key=required.index)
        missing = sorted(required_set - present_set, key=required.index)

        present_hex_cnt = len(hex_set & required_set)
        if present_hex_cnt == 3:
            # 卦内三字齐备 — 完整三刑，极凶
            sources = _find_sources(set(required))
            pos_list = list(dict.fromkeys(s for _, s in sources))  # deduplicated, keep order
            punishments.append({
                "type": ptype,
                "completeness": "完整",
                "branches_present": present,
                "missing": [],
                "formed_by": "卦内",
                "positions": pos_list,
                "description": (
                    ctpl("crt_071", ptype, present[0], present[1], present[2], '、'.join(pos_list))
                ),
                "score": -1.0,
            })
            total_score -= 1.0
        elif len(present_set) == 3:
            # 卦内二字 + 月日补足一字 — 催刑（月日催成，力减半）
            sources = _find_sources(set(required))
            pos_list = list(dict.fromkeys(s for _, s in sources))
            punishments.append({
                "type": ptype,
                "completeness": "催刑",
                "branches_present": present,
                "missing": [],
                "formed_by": "卦内为主，月日催刑",
                "positions": pos_list,
                "description": (
                    ctpl("crt_084", ptype, '、'.join((p for p in present if p in hex_set)) or '无', '、'.join((p for p in present if p not in hex_set)))
                ),
                "score": -0.5,
            })
            total_score -= 0.5
        elif len(present_set) == 2:
            # 待刑 — 需月日补齐
            sources = _find_sources(present_set)
            pos_list = list(dict.fromkeys(s for _, s in sources))
            punishments.append({
                "type": ptype,
                "completeness": "待刑",
                "branches_present": present,
                "missing": missing,
                "formed_by": "待月日补齐",
                "positions": pos_list,
                "description": (
                    ctpl("crt_092", ptype, present[0], present[1], missing[0], missing[0])
                ),
                "score": -0.3,
            })
            total_score -= 0.3
        # 卦内及月日合计不足两字: 不构成任何刑

    # ── 2. 互刑（无礼之刑子卯）：卦内两字成刑；卦内一+月日一为待刑 ──
    b1_key, b2_key = THREE_PUNISHMENTS_MUTUAL["无礼之刑"]
    in_hex = (b1_key in hex_set and b2_key in hex_set)
    in_all = (b1_key in all_branches_set and b2_key in all_branches_set)
    if in_all:
        sources = _find_sources({b1_key, b2_key})
        pos_list = list(dict.fromkeys(s for _, s in sources))
        if in_hex:
            punishments.append({
                "type": "无礼之刑",
                "completeness": "成刑",
                "branches_present": [b1_key, b2_key],
                "missing": [],
                "formed_by": "卦内",
                "positions": pos_list,
                "description": (
                    ctpl("crt_072", b1_key, b2_key, '、'.join(pos_list))
                ),
                "score": -0.5,
            })
            total_score -= 0.5
        else:
            punishments.append({
                "type": "无礼之刑",
                "completeness": "待刑",
                "branches_present": [b1_key, b2_key],
                "missing": [],
                "formed_by": "卦内为主，月日催刑",
                "positions": pos_list,
                "description": (
                    ctpl("crt_073", b1_key, b2_key)
                ),
                "score": -0.3,
            })
            total_score -= 0.3

    # ── 3. 自刑（辰午酉亥）：仅卦内同一地支两次以上 ──
    from collections import Counter
    hex_branch_counts = Counter(b for b, _ in hex_branches)
    for sp_branch in SELF_PUNISHMENTS:
        count = hex_branch_counts.get(sp_branch, 0)
        if count >= 2:
            sources = _find_sources({sp_branch})
            pos_list = list(dict.fromkeys(s for _, s in sources))
            punishments.append({
                "type": "自刑",
                "completeness": "完整",
                "branches_present": [sp_branch],
                "missing": [],
                "formed_by": "卦内",
                "positions": pos_list,
                "description": (
                    ctpl("crt_074", sp_branch, count, '、'.join(pos_list))
                ),
                "score": -0.3 * (count - 1),
            })
            total_score -= 0.3 * (count - 1)  # 每多一次减0.3

    # ── 三刑齐全加重（多个成刑/完整/催刑叠加时凶性倍增）──
    # 经典规则："三刑齐全，凶不可解"——两处以上成刑时按1.5x折算，三处以上2.0x
    complete_cnt = sum(1 for p in punishments if p.get("completeness") in ("完整", "成刑", "催刑"))
    if complete_cnt >= 3:
        total_score *= 2.0  # 三处以上成刑 → 极凶
        # 三刑杂见（循环刑+无礼刑+自刑以上至少两类并列）额外加罚
        ptype_set = set(p.get("type", "") for p in punishments)
        if len(ptype_set) >= 3:
            total_score -= 0.8  # 三类以上刑并见 → 更凶
        elif len(ptype_set) >= 2:
            total_score -= 0.5  # 多种刑类杂见，凶性更甚
    elif complete_cnt >= 2:
        total_score *= 1.5  # 两处成刑 → 凶性加重
        ptype_set = set(p.get("type", "") for p in punishments)
        if len(ptype_set) >= 2:
            total_score *= 1.25  # 多种刑类杂见，再乘1.25
        # 两处以上成刑额外定罚(不乘倍数直接加)
        total_score -= 0.5  # 2+ 成刑叠加的固定附加减分
    # 1处成刑维持原分数（线性加减已足够）

    if not punishments:
        return {"has_punishment": False, "punishments": [], "total_score": 0.0, "summary": ctext("cr_034")}

    summary_parts = [p["description"] for p in punishments]

    return {
        "has_punishment": True,
        "punishments": punishments,
        "total_score": round(total_score, 2),
        "summary": "；".join(summary_parts),
    }


