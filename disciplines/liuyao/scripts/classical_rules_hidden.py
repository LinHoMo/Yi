# -*- coding: utf-8 -*-
"""古典断法增强：表 / 通用辅助 / 18 项断法 / 聚合入口 enhance_reading。（拆分自 classical_analysis.py，纯搬移不改逻辑；聚合入口见 classical_analysis.py）。"""

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
from chain_verdicts import CLASSICAL_INTERPRETATIONS as CINTERP, ctext, ctpl


def _evaluate_hidden_spirit_emergence(hid_elem, hid_branch, cov_rel, cov_branch,
                                       cov_elem, month_branch, day_branch,
                                       month_elem, day_elem, empty_branches,
                                       covering_yao):
    """
    评估伏神得出/不得出。
    
    得出（吉）：
      - 日/月生伏神
      - 日/月与伏神同五行（持之）
      - 飞神生伏神
      - 日/月/动爻冲克飞神
      - 飞神旬空、月破、休囚
    
    不得出（凶）：
      - 伏神休囚被日月克
      - 飞神旺相克伏神
      - 伏神入墓、逢绝
      - 伏神旬空、月破
    """
    emerge_score = 0
    reasons = []

    # --- 得出条件 ---
    # 1. 日/月生伏神
    if SHENG_CYCLE.get(day_elem) == hid_elem or day_elem == hid_elem:
        emerge_score += 2
        reasons.append(ctpl("crt_008", '生' if SHENG_CYCLE.get(day_elem) == hid_elem else '同'))
    if SHENG_CYCLE.get(month_elem) == hid_elem or month_elem == hid_elem:
        emerge_score += 1
        reasons.append(ctpl("crt_009", '生' if SHENG_CYCLE.get(month_elem) == hid_elem else '同'))

    # 2. 飞神生伏神
    if SHENG_CYCLE.get(cov_elem) == hid_elem:
        emerge_score += 2
        reasons.append(ctext("cr_001"))

    # 3. 飞神旬空
    if cov_branch in empty_branches:
        emerge_score += 1
        reasons.append(ctext("cr_002"))

    # 4. 飞神月破
    if is_ba_zu_chong(cov_branch, month_branch):
        emerge_score += 1
        reasons.append(ctext("cr_003"))

    # 5. 飞神休囚
    cov_strength = element_strength_in_month(cov_elem, month_elem)
    if cov_strength in ("休", "囚", "死"):
        emerge_score += 1
        reasons.append(ctpl("crt_010", cov_strength))

    # 6. 伏克飞为出暴（伏神有力反克飞神，出暴为吉）
    if KE_CYCLE.get(hid_elem) == cov_elem:
        emerge_score += 3
        reasons.append(ctext("cr_004"))

    # --- 不得出条件 ---
    # 1. 伏神休囚被日月克
    hid_strength = element_strength_in_month(hid_elem, month_elem)
    if hid_strength in ("死", "囚"):
        emerge_score -= 2
        reasons.append(ctpl("crt_011", hid_strength))

    day_hid_strength = element_strength_in_month(hid_elem, day_elem)
    if day_hid_strength == "死":
        emerge_score -= 2
        reasons.append(ctext("cr_005"))

    # 2. 飞神旺相克伏神
    if KE_CYCLE.get(cov_elem) == hid_elem:
        cov_strength = element_strength_in_month(cov_elem, month_elem)
        if cov_strength in ("旺", "相"):
            emerge_score -= 3
            reasons.append(ctext("cr_006"))

    # 3. 伏神入墓
    tomb = TOMB_MAP.get(hid_elem, "")
    if tomb and day_branch == tomb:
        emerge_score -= 2
        reasons.append(ctpl("crt_012", tomb))

    # 4. 伏神逢绝
    stage = get_twelve_growth_stage(hid_elem, day_branch)
    if stage == "绝":
        emerge_score -= 2
        reasons.append(ctext("cr_007"))

    # 5. 伏神旬空
    if hid_branch in empty_branches:
        emerge_score -= 1
        reasons.append(ctext("cr_008"))

    # 6. 伏神月破
    if is_ba_zu_chong(hid_branch, month_branch):
        emerge_score -= 2
        reasons.append(ctext("cr_009"))

    can_emerge = emerge_score > 0
    reason_text = "；".join(reasons) if reasons else "条件平淡"
    return can_emerge, reason_text


def analyze_hidden_spirits(result):
    """
    伏藏分析：检查六亲是否有缺失，找出伏神、飞神及其得出/不得出。
    
    返回：
        {
            "has_hidden_spirit": bool,
            "details": [
                {
                    "missing_relation": str,        # 缺失的六亲
                    "hidden_spirit": {              # 伏神（来自本宫首卦）
                        "position": int,
                        "branch": str,
                        "six_relation": str,
                        "element": str,
                    },
                    "covering_spirit": {            # 飞神（当前卦中的该位置）
                        "position": int,
                        "branch": str,
                        "six_relation": str,
                        "element": str,
                    },
                    "can_emerge": bool,             # 伏神得出/不得出
                    "reason": str,                  # 得出/不得出判断理由
                },
                ...
            ],
            "summary": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    palace = hex_info.get("palace", "")
    palace_element = hex_info.get("palace_element", "")
    yao_lines = hex_info.get("yao_lines", [])

    if not palace or not yao_lines:
        return {"has_hidden_spirit": False, "details": [], "summary": ctext("cr_010")}

    # 收集本卦已有的六亲
    existing_relations = set()
    for yao in yao_lines:
        rel = yao.get("six_relation", "")
        if rel and rel != "未知":
            existing_relations.add(rel)

    # 找出缺失的六亲
    missing_relations = [r for r in SIX_RELATIONS if r not in existing_relations]

    if not missing_relations:
        return {
            "has_hidden_spirit": False,
            "details": [],
            "summary": ctext("cr_011"),
        }

    # 本宫首卦（纯卦）的地支
    # 宫殿名即为八卦名，其五行为 palace_element
    # 本宫卦上下皆为该八卦
    if palace not in NAJIA_BRANCHES:
        return {"has_hidden_spirit": True, "details": [], "summary": ctext("cr_012")}

    base_inner = NAJIA_BRANCHES[palace]["inner"]
    base_outer = NAJIA_BRANCHES[palace]["outer"]
    base_branches = base_inner + base_outer  # pos 1-6

    # 获取月建日辰信息
    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    month_element = _branch_element(month_branch)
    day_element = _branch_element(day_branch)
    empty_branches = result.get("empty_branches", [])

    details = []
    yao_by_position = {yao["position"]: yao for yao in yao_lines}

    for missing_rel in missing_relations:
        # 在本宫首卦中找该六亲的位置
        hidden_pos = None
        hidden_branch = None
        hidden_element = None
        for pos_idx, branch in enumerate(base_branches):
            rel = determine_six_relation(branch, palace_element)
            if rel == missing_rel:
                hidden_pos = pos_idx + 1
                hidden_branch = branch
                hidden_element = _branch_element(branch)
                break

        if hidden_pos is None:
            # 不应该发生，但保险
            continue

        # 飞神：本卦中该位置的六亲
        covering_yao = yao_by_position.get(hidden_pos, {})
        covering_relation = covering_yao.get("six_relation", "未知")
        covering_branch = covering_yao.get("earthly_branch", "")
        covering_element = _branch_element(covering_branch)

        # 判断伏神得出/不得出
        can_emerge, reason = _evaluate_hidden_spirit_emergence(
            hidden_element, hidden_branch, covering_relation, covering_branch,
            covering_element, month_branch, day_branch, month_element, day_element,
            empty_branches, yao_by_position.get(hidden_pos, {})
        )

        details.append({
            "missing_relation": missing_rel,
            "hidden_spirit": {
                "position": hidden_pos,
                "name": _pos_to_name(hidden_pos),
                "branch": hidden_branch,
                "six_relation": missing_rel,
                "element": hidden_element,
            },
            "covering_spirit": {
                "position": hidden_pos,
                "name": _pos_to_name(hidden_pos),
                "branch": covering_branch,
                "six_relation": covering_relation,
                "element": covering_element,
            },
            "can_emerge": can_emerge,
            "reason": reason,
        })

    summary_parts = []
    for d in details:
        status = "得出" if d["can_emerge"] else "不得出"
        summary_parts.append(
            ctpl("crt_013", d['missing_relation'], d['hidden_spirit']['branch'], d['covering_spirit']['six_relation'], d['covering_spirit']['branch'], status)
        )

    return {
        "has_hidden_spirit": True,
        "details": details,
        "summary": "；".join(summary_parts),
    }


def analyze_hidden_spirit_emergence(result):
    """
    伏神得出不得出优化版评分。
    基于卜筮正宗四大伏神规则完整实现：

    伏神得出（可出）的条件:
      1. 日辰生扶伏神
      2. 月建生扶伏神
      3. 日冲飞神（冲开飞神）
      4. 月冲飞神
      5. 飞神旬空（空则不挡）
      6. 飞神月破（破则不挡）
      7. 飞神休囚无气
      8. 飞神被日/月/动爻克
      9. 伏神旺相有气

    伏神不得出（难出）的条件:
      1. 伏神被月日双克
      2. 飞神旺相克伏神（飞克伏）
      3. 伏神入墓于日/月
      4. 伏神逢绝地
      5. 伏神旬空
      6. 伏神月破
      7. 伏神休囚无气

    返回：
        {
            "has_hidden_spirit": bool,
            "spirits": [
                {
                    "missing_relation": str,
                    "hidden_branch": str,
                    "covering_branch": str,
                    "can_emerge": bool,
                    "emerge_score": int,
                    "emerge_level": str,    # "极易出"/"可以出"/"难出"/"不得出"
                    "emerge_reasons": [str],
                    "block_reasons": [str],
                    "summary": str,
                },
                ...
            ],
            "summary": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    palace = hex_info.get("palace", "")
    palace_element = hex_info.get("palace_element", "")
    yao_lines = hex_info.get("yao_lines", [])

    if not palace or not yao_lines:
        return {"has_hidden_spirit": False, "spirits": [], "summary": ctext("cr_013")}

    # 收集本卦已有的六亲
    existing_relations = set()
    for yao in yao_lines:
        rel = yao.get("six_relation", "")
        if rel and rel != "未知":
            existing_relations.add(rel)

    missing_relations = [r for r in SIX_RELATIONS if r not in existing_relations]

    if not missing_relations:
        return {"has_hidden_spirit": False, "spirits": [], "summary": ctext("cr_014")}

    # 本宫首卦地支
    if palace not in NAJIA_BRANCHES:
        return {"has_hidden_spirit": True, "spirits": [], "summary": ctext("cr_015")}

    base_branches = NAJIA_BRANCHES[palace]["inner"] + NAJIA_BRANCHES[palace]["outer"]

    # 月建日辰信息
    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    month_element = _branch_element(month_branch)
    day_element = _branch_element(day_branch)
    empty_branches = result.get("empty_branches", [])

    # 收集动爻地支
    moving_branches = set()
    for yao in yao_lines:
        if yao.get("is_moving", False):
            moving_branches.add(yao.get("earthly_branch", ""))

    yao_by_position = {yao["position"]: yao for yao in yao_lines}

    spirits = []
    for missing_rel in missing_relations:
        hidden_pos = None
        hidden_branch = None
        hidden_element = None
        for pos_idx, branch in enumerate(base_branches):
            rel = determine_six_relation(branch, palace_element)
            if rel == missing_rel:
                hidden_pos = pos_idx + 1
                hidden_branch = branch
                hidden_element = _branch_element(branch)
                break

        if hidden_pos is None:
            continue

        covering_yao = yao_by_position.get(hidden_pos, {})
        covering_branch = covering_yao.get("earthly_branch", "")
        covering_element = _branch_element(covering_branch)

        # === 优化版评分 ===
        emerge_score = 0
        emerge_reasons = []
        block_reasons = []

        # --- 得出条件 ---
        # 1. 日辰生扶伏神
        if SHENG_CYCLE.get(day_element) == hidden_element:
            emerge_score += 3
            emerge_reasons.append(ctpl("crt_030", day_branch, day_element, hidden_branch, hidden_element))
        elif day_element == hidden_element:
            emerge_score += 2
            emerge_reasons.append(ctpl("crt_056", day_branch))

        # 2. 月建生扶伏神
        if SHENG_CYCLE.get(month_element) == hidden_element:
            emerge_score += 2
            emerge_reasons.append(ctpl("crt_031", month_branch, month_element, hidden_branch))
        elif month_element == hidden_element:
            emerge_score += 1
            emerge_reasons.append(ctpl("crt_057", month_branch))

        # 3. 日冲飞神（冲开飞神）
        if is_ba_zu_chong(covering_branch, day_branch):
            emerge_score += 2
            emerge_reasons.append(ctpl("crt_032", covering_branch, day_branch, covering_branch))

        # 4. 月冲飞神
        if is_ba_zu_chong(covering_branch, month_branch):
            emerge_score += 1
            emerge_reasons.append(ctpl("crt_033", covering_branch, month_branch, covering_branch))

        # 5. 飞神旬空（空则不挡）
        if covering_branch in empty_branches:
            emerge_score += 2
            emerge_reasons.append(ctpl("crt_034", covering_branch))

        # 6. 飞神月破（破则不挡）
        if is_ba_zu_chong(covering_branch, month_branch):
            emerge_score += 2
            emerge_reasons.append(ctpl("crt_035", covering_branch))

        # 7. 飞神休囚无气
        cov_strength = element_strength_in_month(covering_element, month_element)
        if cov_strength in ("休", "囚", "死"):
            emerge_score += 1
            emerge_reasons.append(ctpl("crt_036", covering_branch, cov_strength))

        # 8. 飞神被日/月/动爻克
        day_attacks_cov = KE_CYCLE.get(day_element) == covering_element
        month_attacks_cov = KE_CYCLE.get(month_element) == covering_element
        moving_attacks_cov = False
        for mb in moving_branches:
            if KE_CYCLE.get(_branch_element(mb)) == covering_element:
                moving_attacks_cov = True
                break
        if day_attacks_cov:
            emerge_score += 1
            emerge_reasons.append(ctpl("crt_037", g_day_cn(day_element), g_day_cn(covering_element)))
        if month_attacks_cov:
            emerge_score += 1
            emerge_reasons.append(ctpl("crt_038", g_day_cn(month_element), g_day_cn(covering_element)))
        if moving_attacks_cov:
            emerge_score += 1
            emerge_reasons.append(ctext("cr_016"))

        # 9. 伏神旺相有气
        hid_strength = element_strength_in_month(hidden_element, month_element)
        if hid_strength == "旺":
            emerge_score += 2
            emerge_reasons.append(ctpl("crt_039", hidden_branch))
        elif hid_strength == "相":
            emerge_score += 1
            emerge_reasons.append(ctpl("crt_058", hidden_branch))

        # --- 不得出条件 ---
        # 1. 伏神被月日双克
        hid_day_strength = element_strength_in_month(hidden_element, day_element)
        if hid_strength == "死" and hid_day_strength == "死":
            emerge_score -= 4
            block_reasons.append(ctpl("crt_040", hidden_branch))

        # 2. 飞神旺相克伏神（飞克伏）
        if KE_CYCLE.get(covering_element) == hidden_element:
            if cov_strength in ("旺", "相"):
                emerge_score -= 3
                block_reasons.append(ctpl("crt_059", covering_branch, covering_element, hidden_branch, hidden_element))

        # 3. 伏神入墓
        tomb = TOMB_MAP.get(hidden_element, "")
        if tomb and (day_branch == tomb or month_branch == tomb):
            emerge_score -= 2
            block_reasons.append(ctpl("crt_041", hidden_branch, tomb))

        # 4. 伏神逢绝
        stage = get_twelve_growth_stage(hidden_element, day_branch)
        if stage == "绝":
            emerge_score -= 2
            block_reasons.append(ctpl("crt_042", hidden_branch, day_branch))

        # 5. 伏神旬空
        if hidden_branch in empty_branches:
            emerge_score -= 2
            block_reasons.append(ctpl("crt_043", hidden_branch))

        # 6. 伏神月破
        if is_ba_zu_chong(hidden_branch, month_branch):
            emerge_score -= 2
            block_reasons.append(ctpl("crt_044", hidden_branch))

        # 7. 伏神休囚无气
        if hid_strength in ("休", "囚", "死"):
            emerge_score -= 1
            block_reasons.append(ctpl("crt_045", hidden_branch, hid_strength))

        # 判断得出/不得出
        can_emerge = emerge_score > 0
        if emerge_score >= 4:
            emerge_level = "极易出"
        elif emerge_score >= 2:
            emerge_level = "可以出"
        elif emerge_score >= 0:
            emerge_level = "勉强得出"
        elif emerge_score >= -2:
            emerge_level = "难出"
        else:
            emerge_level = "不得出"

        all_reasons = emerge_reasons + block_reasons
        reason_text = "；".join(all_reasons) if all_reasons else "条件平淡"

        spirit_pos_name = _pos_to_name(hidden_pos)
        spirits.append({
            "missing_relation": missing_rel,
            "hidden_branch": hidden_branch,
            "covering_branch": covering_branch,
            "can_emerge": can_emerge,
            "emerge_score": emerge_score,
            "emerge_level": emerge_level,
            "emerge_reasons": emerge_reasons,
            "block_reasons": block_reasons,
            "summary": (
                ctpl("crt_046", missing_rel, hidden_branch, covering_branch, cov_strength, hid_strength, emerge_score, emerge_level)
            ),
        })

    if not spirits:
        return {"has_hidden_spirit": False, "spirits": [], "summary": ctext("cr_017")}

    summary_parts = [s["summary"] for s in spirits]
    return {
        "has_hidden_spirit": True,
        "spirits": spirits,
        "summary": "；".join(summary_parts),
    }


def analyze_hidden_movement(result):
    """
    暗动分析：静爻逢日冲且旺相=暗动；静爻旬空逢日冲=冲空则实。
    
    返回：
        {
            "has_hidden_movement": bool,
            "details": [
                {
                    "position": int,
                    "name": str,
                    "branch": str,
                    "element": str,
                    "six_relation": str,
                    "type": str,          # "暗动" or "冲空则实"
                    "strength": str,       # 旺相休囚死 based on month+day
                    "description": str,
                },
                ...
            ],
            "summary": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    if not yao_lines:
        return {"has_hidden_movement": False, "details": [], "summary": ctext("cr_018")}

    dt = result.get("divination_time", {})
    day_sb = dt.get("day_stem_branch", "")
    month_sb = dt.get("month_stem_branch", "")
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    if not day_branch:
        return {"has_hidden_movement": False, "details": [], "summary": ctext("cr_019")}

    day_element = _branch_element(day_branch)
    month_element = _branch_element(month_branch)
    empty_branches = result.get("empty_branches", [])

    details = []
    for yao in yao_lines:
        if yao.get("is_moving", False):
            continue  # 只分析静爻

        branch = yao.get("earthly_branch", "")
        if not branch:
            continue

        # 判断是否被日冲
        if is_ba_zu_chong(branch, day_branch):
            is_empty = branch in empty_branches
            elem = _branch_element(branch)

            # 计算旺衰：综合月建+日辰
            m_strength = element_strength_in_month(elem, month_element)
            d_strength = element_strength_in_month(elem, day_element)

            # 综合判断：月建日辰综合
            overall = _combined_strength(elem, month_element, day_element)

            if is_empty and day_branch:
                line_type = "冲空则实"
                effect_strength = "实"
                line_score = 1.0
                desc = ctpl("crt_047", _pos_to_name(yao['position']), branch, day_branch)
            elif overall in ("旺", "相"):
                line_type = "暗动(旺相，七分布动)"
                effect_strength = "强"
                line_score = 0.7
                desc = (
                    ctpl("crt_060", _pos_to_name(yao['position']), branch, day_branch)
                )
            elif overall == "中和":
                line_type = "暗动(中和，中力)"
                effect_strength = "中"
                line_score = 0.4
                desc = (
                    ctpl("crt_079", _pos_to_name(yao['position']), branch, day_branch)
                )
            elif overall == "偏弱":
                line_type = "暗动(休囚，三分力)"
                effect_strength = "弱"
                line_score = 0.2
                desc = (
                    ctpl("crt_087", _pos_to_name(yao['position']), branch, day_branch)
                )
            else:  # "衰"
                line_type = "日破(月休逢冲，此爻无用)"
                effect_strength = "无"
                line_score = 0.0
                desc = (
                    ctpl("crt_088", _pos_to_name(yao['position']), branch, day_branch)
                )

            details.append({
                "position": yao["position"],
                "name": yao.get("name", ""),
                "branch": branch,
                "element": elem,
                "six_relation": yao.get("six_relation", ""),
                "six_spirit": yao.get("six_spirit", ""),
                "type": line_type,
                "effect_strength": effect_strength,
                "line_score": line_score,
                "month_strength": m_strength,
                "day_strength": d_strength,
                "overall_strength": overall,
                "is_day_break": (line_score == 0.0),
                "description": desc,
            })

    if not details:
        return {"has_hidden_movement": False, "details": [], "summary": ctext("cr_020")}

    summary = "；".join(d["description"] for d in details)
    return {"has_hidden_movement": True, "details": details, "summary": summary}


