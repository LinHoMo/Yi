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
from chain_verdicts import CLASSICAL_INTERPRETATIONS as CINTERP

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
        reasons.append(f"日辰{'生' if SHENG_CYCLE.get(day_elem) == hid_elem else '同'}伏神")
    if SHENG_CYCLE.get(month_elem) == hid_elem or month_elem == hid_elem:
        emerge_score += 1
        reasons.append(f"月建{'生' if SHENG_CYCLE.get(month_elem) == hid_elem else '同'}伏神")

    # 2. 飞神生伏神
    if SHENG_CYCLE.get(cov_elem) == hid_elem:
        emerge_score += 2
        reasons.append("飞神生伏神")

    # 3. 飞神旬空
    if cov_branch in empty_branches:
        emerge_score += 1
        reasons.append("飞神旬空")

    # 4. 飞神月破
    if is_ba_zu_chong(cov_branch, month_branch):
        emerge_score += 1
        reasons.append("飞神月破")

    # 5. 飞神休囚
    cov_strength = element_strength_in_month(cov_elem, month_elem)
    if cov_strength in ("休", "囚", "死"):
        emerge_score += 1
        reasons.append(f"飞神{cov_strength}")

    # 6. 伏克飞为出暴（伏神有力反克飞神，出暴为吉）
    if KE_CYCLE.get(hid_elem) == cov_elem:
        emerge_score += 3
        reasons.append("伏克飞为出暴")

    # --- 不得出条件 ---
    # 1. 伏神休囚被日月克
    hid_strength = element_strength_in_month(hid_elem, month_elem)
    if hid_strength in ("死", "囚"):
        emerge_score -= 2
        reasons.append(f"伏神{hid_strength}")

    day_hid_strength = element_strength_in_month(hid_elem, day_elem)
    if day_hid_strength == "死":
        emerge_score -= 2
        reasons.append("日辰克伏神")

    # 2. 飞神旺相克伏神
    if KE_CYCLE.get(cov_elem) == hid_elem:
        cov_strength = element_strength_in_month(cov_elem, month_elem)
        if cov_strength in ("旺", "相"):
            emerge_score -= 3
            reasons.append("飞神旺相克伏神")

    # 3. 伏神入墓
    tomb = TOMB_MAP.get(hid_elem, "")
    if tomb and day_branch == tomb:
        emerge_score -= 2
        reasons.append(f"伏神入墓({tomb})")

    # 4. 伏神逢绝
    stage = get_twelve_growth_stage(hid_elem, day_branch)
    if stage == "绝":
        emerge_score -= 2
        reasons.append("伏神逢绝")

    # 5. 伏神旬空
    if hid_branch in empty_branches:
        emerge_score -= 1
        reasons.append("伏神旬空")

    # 6. 伏神月破
    if is_ba_zu_chong(hid_branch, month_branch):
        emerge_score -= 2
        reasons.append("伏神月破")

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
        return {"has_hidden_spirit": False, "details": [], "summary": "无足够数据进行伏藏分析"}

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
            "summary": "本卦六亲齐备，无伏藏",
        }

    # 本宫首卦（纯卦）的地支
    # 宫殿名即为八卦名，其五行为 palace_element
    # 本宫卦上下皆为该八卦
    if palace not in NAJIA_BRANCHES:
        return {"has_hidden_spirit": True, "details": [], "summary": "宫名异常，无法分析"}

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
            f"{d['missing_relation']}伏藏（{d['hidden_spirit']['branch']}）"
            f"飞神{d['covering_spirit']['six_relation']}({d['covering_spirit']['branch']})"
            f"→ {status}"
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
        return {"has_hidden_spirit": False, "spirits": [], "summary": "无足够数据"}

    # 收集本卦已有的六亲
    existing_relations = set()
    for yao in yao_lines:
        rel = yao.get("six_relation", "")
        if rel and rel != "未知":
            existing_relations.add(rel)

    missing_relations = [r for r in SIX_RELATIONS if r not in existing_relations]

    if not missing_relations:
        return {"has_hidden_spirit": False, "spirits": [], "summary": "六亲齐备，无伏藏"}

    # 本宫首卦地支
    if palace not in NAJIA_BRANCHES:
        return {"has_hidden_spirit": True, "spirits": [], "summary": "宫名异常"}

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
            emerge_reasons.append(f"日辰{day_branch}({day_element})生伏神{hidden_branch}({hidden_element})")
        elif day_element == hidden_element:
            emerge_score += 2
            emerge_reasons.append(f"日辰{day_branch}与伏神同五行")

        # 2. 月建生扶伏神
        if SHENG_CYCLE.get(month_element) == hidden_element:
            emerge_score += 2
            emerge_reasons.append(f"月建{month_branch}({month_element})生伏神{hidden_branch}")
        elif month_element == hidden_element:
            emerge_score += 1
            emerge_reasons.append(f"月建{month_branch}与伏神同五行")

        # 3. 日冲飞神（冲开飞神）
        if is_ba_zu_chong(covering_branch, day_branch):
            emerge_score += 2
            emerge_reasons.append(f"日冲飞神{covering_branch}（{day_branch}冲{covering_branch}，冲开）")

        # 4. 月冲飞神
        if is_ba_zu_chong(covering_branch, month_branch):
            emerge_score += 1
            emerge_reasons.append(f"月冲飞神{covering_branch}（{month_branch}冲{covering_branch}）")

        # 5. 飞神旬空（空则不挡）
        if covering_branch in empty_branches:
            emerge_score += 2
            emerge_reasons.append(f"飞神{covering_branch}旬空")

        # 6. 飞神月破（破则不挡）
        if is_ba_zu_chong(covering_branch, month_branch):
            emerge_score += 2
            emerge_reasons.append(f"飞神{covering_branch}月破")

        # 7. 飞神休囚无气
        cov_strength = element_strength_in_month(covering_element, month_element)
        if cov_strength in ("休", "囚", "死"):
            emerge_score += 1
            emerge_reasons.append(f"飞神{covering_branch}休囚({cov_strength})")

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
            emerge_reasons.append(f"日辰{g_day_cn(day_element)}克飞神{g_day_cn(covering_element)}")
        if month_attacks_cov:
            emerge_score += 1
            emerge_reasons.append(f"月建{g_day_cn(month_element)}克飞神{g_day_cn(covering_element)}")
        if moving_attacks_cov:
            emerge_score += 1
            emerge_reasons.append("动爻克飞神")

        # 9. 伏神旺相有气
        hid_strength = element_strength_in_month(hidden_element, month_element)
        if hid_strength == "旺":
            emerge_score += 2
            emerge_reasons.append(f"伏神{hidden_branch}旺相")
        elif hid_strength == "相":
            emerge_score += 1
            emerge_reasons.append(f"伏神{hidden_branch}有气")

        # --- 不得出条件 ---
        # 1. 伏神被月日双克
        hid_day_strength = element_strength_in_month(hidden_element, day_element)
        if hid_strength == "死" and hid_day_strength == "死":
            emerge_score -= 4
            block_reasons.append(f"伏神{hidden_branch}被月日双克")

        # 2. 飞神旺相克伏神（飞克伏）
        if KE_CYCLE.get(covering_element) == hidden_element:
            if cov_strength in ("旺", "相"):
                emerge_score -= 3
                block_reasons.append(f"飞神{covering_branch}({covering_element})旺相克伏神{hidden_branch}({hidden_element})")

        # 3. 伏神入墓
        tomb = TOMB_MAP.get(hidden_element, "")
        if tomb and (day_branch == tomb or month_branch == tomb):
            emerge_score -= 2
            block_reasons.append(f"伏神{hidden_branch}入墓于{tomb}")

        # 4. 伏神逢绝
        stage = get_twelve_growth_stage(hidden_element, day_branch)
        if stage == "绝":
            emerge_score -= 2
            block_reasons.append(f"伏神{hidden_branch}逢绝地(日辰{day_branch})")

        # 5. 伏神旬空
        if hidden_branch in empty_branches:
            emerge_score -= 2
            block_reasons.append(f"伏神{hidden_branch}旬空")

        # 6. 伏神月破
        if is_ba_zu_chong(hidden_branch, month_branch):
            emerge_score -= 2
            block_reasons.append(f"伏神{hidden_branch}月破")

        # 7. 伏神休囚无气
        if hid_strength in ("休", "囚", "死"):
            emerge_score -= 1
            block_reasons.append(f"伏神{hidden_branch}休囚无气({hid_strength})")

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
                f"{missing_rel}伏{hidden_branch}于{covering_branch}之下，"
                f"飞神{cov_strength}，伏神{hid_strength}，"
                f"得出评分={emerge_score}({emerge_level})"
            ),
        })

    if not spirits:
        return {"has_hidden_spirit": False, "spirits": [], "summary": "无需分析"}

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
        return {"has_hidden_movement": False, "details": [], "summary": "无数据"}

    dt = result.get("divination_time", {})
    day_sb = dt.get("day_stem_branch", "")
    month_sb = dt.get("month_stem_branch", "")
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    if not day_branch:
        return {"has_hidden_movement": False, "details": [], "summary": "无日辰数据"}

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
                desc = f"{_pos_to_name(yao['position'])}({branch}旬空)被日辰{day_branch}冲，冲空则实，此爻由虚转实"
            elif overall in ("旺", "相"):
                line_type = "暗动(旺相，七分布动)"
                effect_strength = "强"
                line_score = 0.7
                desc = (
                    f"{_pos_to_name(yao['position'])}({branch})静爻被日辰{day_branch}冲，"
                    f"旺相暗动，其力约当明动七成"
                )
            elif overall == "中和":
                line_type = "暗动(中和，中力)"
                effect_strength = "中"
                line_score = 0.4
                desc = (
                    f"{_pos_to_name(yao['position'])}({branch})静爻被日辰{day_branch}冲，"
                    f"中和暗动，力量中等"
                )
            elif overall == "偏弱":
                line_type = "暗动(休囚，三分力)"
                effect_strength = "弱"
                line_score = 0.2
                desc = (
                    f"{_pos_to_name(yao['position'])}({branch})静爻被日辰{day_branch}冲，"
                    f"休囚暗动，力微短暂"
                )
            else:  # "衰"
                line_type = "日破(月休逢冲，此爻无用)"
                effect_strength = "无"
                line_score = 0.0
                desc = (
                    f"{_pos_to_name(yao['position'])}({branch})静爻被日辰{day_branch}冲，"
                    f"月休囚逢冲为日破，此爻彻底无用"
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
        return {"has_hidden_movement": False, "details": [], "summary": "本卦无暗动之爻"}

    summary = "；".join(d["description"] for d in details)
    return {"has_hidden_movement": True, "details": details, "summary": summary}


def analyze_wandering_returning_soul(result):
    """
    游魂归魂卦特殊断法。

    游魂卦/归魂卦是各宫第7、8卦，具有特殊的卦类特质：
    - 游魂：行无定、忧疑不安、心无归宿
    - 归魂：回故乡、有归属、终有所归

    参考《卜筮正宗》：
    > "游魂行无定，归魂回故乡。"
    > "游魂卦主在外、不安、忧疑、反复。"
    > "归魂卦主在内、有归、安定、终有所归。"

    此分析不改变评分（score_adjustment=0），仅提供断卦方向指引。

    返回:
        {
            "is_soul_hexagram": bool,
            "soul_type": str or None,       # "游魂" / "归魂" / None
            "meaning": str,                  # 卦类整体含义
            "travel": str,                   # 出行断法
            "residence": str,                # 居家断法
            "mind": str,                     # 心境断法
            "score_adjustment": 0,           # 不改变评分
        }
    """
    hex_info = result.get("original_hexagram", {})
    hex_name = hex_info.get("name", "")
    generation = hex_info.get("generation", "")

    # 游魂/归魂的卦类特质
    SOUL_GEN = {
        "游魂": {
            "meaning": CINTERP["youhun"]["text"],
            "travel": CINTERP["youhun_traits"]["text"],
            "residence": CINTERP["youhun_trait_home"]["text"],
            "mind": CINTERP["youhun_trait_mind"]["text"],
        },
        "归魂": {
            "meaning": CINTERP["guihun"]["text"],
            "travel": CINTERP["guihun_traits"]["text"],
            "residence": CINTERP["guihun_trait_home"]["text"],
            "mind": CINTERP["guihun_trait_mind"]["text"],
        },
    }

    soul_data = SOUL_GEN.get(generation)

    if soul_data:
        return {
            "is_soul_hexagram": True,
            "soul_type": generation,
            "meaning": soul_data["meaning"],
            "travel": soul_data["travel"],
            "residence": soul_data["residence"],
            "mind": soul_data["mind"],
            "summary": f"{generation}卦——{soul_data['meaning']}。事多{CINTERP['youhun_dynamic']['text'] if generation == '游魂' else CINTERP['guihun_dynamic']['text']}",
            "score_adjustment": 0,  # 不改变评分——仅为断卦方向指引
        }

    return {
        "is_soul_hexagram": False,
        "soul_type": None,
        "meaning": CINTERP["not_youhun_guihun"]["text"],
        "travel": "无游魂归魂特征",
        "residence": "无游魂归魂特征",
        "mind": "无游魂归魂特征",
        "summary": CINTERP["not_youhun_guihun_summary"]["text"],
        "score_adjustment": 0,
    }


def analyze_monthly_break(result):
    """
    月破分析：某爻地支被月建冲则为月破。
    
    返回：
        {
            "has_monthly_break": bool,
            "details": [
                {
                    "position": int,
                    "name": str,
                    "branch": str,
                    "element": str,
                    "six_relation": str,
                    "is_moving": bool,
                    "is_empty": bool,
                    "day_branch": str,
                    "both_broken": bool,    # 同时被日冲+月冲
                    "salvageable": bool,    # 是否可救（日辰生扶或旺相）
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
        return {"has_monthly_break": False, "details": [], "summary": "无数据"}

    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    if not month_branch:
        return {"has_monthly_break": False, "details": [], "summary": "无月建数据"}

    day_element = _branch_element(day_branch)
    month_element = _branch_element(month_branch)
    empty_branches = result.get("empty_branches", [])

    details = []
    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        if not branch:
            continue

        if is_ba_zu_chong(branch, month_branch):
            elem = _branch_element(branch)
            is_moving = yao.get("is_moving", False)
            is_empty = branch in empty_branches
            both_broken = is_ba_zu_chong(branch, day_branch)

            # 判断是否有救
            salvageable = False
            month_str = element_strength_in_month(elem, month_element)
            day_str = element_strength_in_month(elem, day_element)

            # 日辰生扶或旺相可救
            if day_str in ("旺", "相"):
                salvageable = True
            if SHENG_WO.get(day_element) == elem or SHENG_CYCLE.get(day_element) == elem:
                # 日辰生之
                salvageable = True

            desc_parts = []
            if both_broken:
                desc_parts.append(
                    f"{_pos_to_name(yao['position'])}({branch})既破于月建又冲于日辰，力量极弱"
                )
            else:
                desc_parts.append(
                    f"{_pos_to_name(yao['position'])}({branch})为月破之爻"
                )

            if salvageable:
                desc_parts.append(f"但得日辰{day_branch}生扶，尚可补救")
            else:
                desc_parts.append("无解救之力")

            if is_moving:
                desc_parts.append("动爻月破，力量减半")
            if is_empty:
                desc_parts.append("又逢旬空，更为无力")

            relation_str = yao.get("six_relation", "")
            details.append({
                "position": yao["position"],
                "name": yao.get("name", ""),
                "branch": branch,
                "element": elem,
                "six_relation": relation_str,
                "six_spirit": yao.get("six_spirit", ""),
                "is_moving": is_moving,
                "is_empty": is_empty,
                "month_branch": month_branch,
                "day_branch": day_branch,
                "both_broken": both_broken,
                "month_strength": month_str,
                "day_strength": day_str,
                "salvageable": salvageable,
                "description": "，".join(desc_parts),
            })

    if not details:
        return {"has_monthly_break": False, "details": [], "summary": "本卦无月破之爻"}

    summary = "；".join(d["description"] for d in details)
    return {"has_monthly_break": True, "details": details, "summary": summary}


def _check_broken_combo(combo_dict, day_branch, month_branch):
    """
    检查一个已完成的三合局是否被破坏。

    破局条件（《卜筮正宗》）：
      - 合局中一字被日/月冲 → 局破
      - 合局中一字入墓/逢绝 → 局力大减

    参数:
        combo_dict: {"element": str, "branches": [str,str,str], ...}
        day_branch: 日辰地支
        month_branch: 月建地支

    返回:
        {"status": "破局"/"完整", "issues": [...], "score_mod": float}
    """
    branches = combo_dict.get("branches", [])

    # 六冲映射
    CHONG_MAP = {
        "子": "午", "午": "子", "丑": "未", "未": "丑",
        "寅": "申", "申": "寅", "卯": "酉", "酉": "卯",
        "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
    }

    # 各五行入墓地支
    TOMB_MAP = {"金": "丑", "木": "未", "火": "戌", "水": "辰", "土": "辰"}

    issues = []

    for b in branches:
        # 检查日冲
        if CHONG_MAP.get(b) == day_branch:
            issues.append(f"{b}被日冲，合局不稳")
        elif CHONG_MAP.get(b) == month_branch:
            issues.append(f"{b}被月冲，合局有隙")

    # 检查合局五行是否整体入墓于日辰
    target_element = combo_dict.get("element", "")
    if target_element and day_branch == TOMB_MAP.get(target_element, ""):
        issues.append(f"合局入墓于{day_branch}，局力不显")

    if issues:
        return {"status": "破局", "severity": "减力", "issues": issues, "score_mod": -0.5}
    return {"status": "完整", "issues": [], "score_mod": 0}


def analyze_triple_combo(result):
    """
    三合局分析：检查是否存在申子辰(水)、寅午戌(火)、巳酉丑(金)、亥卯未(木)。
    增加破局检测：合局中一字被日/月冲或入墓时判定为破局。
    
    返回：
        {
            "has_triple_combo": bool,
            "details": [
                {
                    "element": str,         # 合局五行
                    "branches": [str, str, str],  # 合局三地支
                    "positions": [int, int, int], # 出现在哪些位置
                    "completeness": str,    # "完整"/"待日"/"待月"
                    "formation_type": str,  # "三爻齐发"/"二爻动+一静"/"二爻动+日/月补"
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
        return {"has_triple_combo": False, "details": [], "summary": "无数据"}

    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""

    # 收集每个位置的地支和是否明动/暗动
    pos_branch = {}
    pos_moving = {}
    pos_hidden_move = {}  # 是否是暗动

    moving_positions = set()
    for yao in yao_lines:
        pos = yao.get("position", 0)
        branch = yao.get("earthly_branch", "")
        pos_branch[pos] = branch
        is_moving = yao.get("is_moving", False)
        pos_moving[pos] = is_moving
        if is_moving:
            moving_positions.add(pos)

    # 检查暗动
    hidden_move = set()
    for yao in yao_lines:
        pos = yao.get("position", 0)
        if pos_moving.get(pos, False):
            continue
        branch = yao.get("earthly_branch", "")
        if branch and is_ba_zu_chong(branch, day_branch):
            hidden_move.add(pos)

    # 所有有力爻的位置（明动 + 暗动）
    active_positions = moving_positions | hidden_move
    # 也包括静爻（三合可以以静爻参与），但我们只需要确认静爻有对应地支即可

    details = []

    for combo_element, combo_branches in SAN_HE.items():
        b1, b2, b3 = combo_branches

        # 找到每个地支在本卦中出现的位置
        pos_map = {b: [] for b in combo_branches}
        for pos, branch in pos_branch.items():
            if branch in pos_map:
                pos_map[branch].append(pos)

        # 检查是否能形成三合
        # 需要 b1, b2, b3 各至少在一个位置出现
        if any(len(pos_map[b]) == 0 for b in combo_branches):
            # 检查是否能由日/月补齐
            locations = {b: pos_map[b] for b in combo_branches if pos_map[b]}
            if len(locations) == 2:
                # 缺一个，看日/月是否有
                missing = [b for b in combo_branches if not pos_map[b]][0]
                if missing in (day_branch, month_branch):
                    # 由日/月补齐
                    valid_positions = []
                    for b in combo_branches:
                        if pos_map[b]:
                            valid_positions.append(pos_map[b][0])
                        elif b == day_branch:
                            valid_positions.append(f"日({day_branch})")
                        elif b == month_branch:
                            valid_positions.append(f"月({month_branch})")

                    # 需要至少两个明动的爻才成局
                    actual_pos = [p for p in valid_positions if isinstance(p, int)]
                    if len(actual_pos) >= 2:
                        formation = "二爻动+日/月补"
                        _combo_d = {
                            "element": combo_element,
                            "branches": combo_branches,
                        }
                        _broken = _check_broken_combo(_combo_d, day_branch, month_branch)
                        _desc = (
                            f"{''.join(combo_branches)}合{combo_element}局，"
                            f"由日辰{day_branch}或月建{month_branch}补齐，"
                            f"力量稍逊但仍有合力"
                        )
                        if _broken["status"] == "破局":
                            _desc += f"。⚠破局：{'；'.join(_broken['issues'])}"
                        details.append({
                            "element": combo_element,
                            "branches": combo_branches,
                            "positions": valid_positions,
                            "completeness": "待日/月",
                            "formation_type": formation,
                            "combo_status": _broken["status"],
                            "combo_issues": _broken["issues"],
                            "combo_score_mod": _broken["score_mod"],
                            "description": _desc,
                        })
            continue

        # 三个地支都在本卦中
        # 取第一个出现的位置
        p1 = pos_map[b1][0]
        p2 = pos_map[b2][0]
        p3 = pos_map[b3][0]
        positions = [p1, p2, p3]

        # 判断参与方式：几个明动？几个暗动？几个静？
        moving_count = sum(1 for p in positions if p in moving_positions)
        hidden_count = sum(1 for p in positions if p in hidden_move)
        static_count = sum(1 for p in positions
                          if p not in moving_positions and p not in hidden_move)

        if moving_count >= 2 and hidden_count + static_count == 1:
            ftype = "二爻动+一静"
            completeness = "完整" if hidden_count == 0 and static_count == 1 else "完整"
        elif moving_count == 3:
            ftype = "三爻齐发"
            completeness = "完整"
        elif moving_count >= 1 or hidden_count >= 1:
            ftype = f"{moving_count}爻动+{hidden_count}暗动+{static_count}静"
            completeness = "完整"
        else:
            ftype = "三爻皆静"
            # 三个静爻三合，名为"合局待用"，需日/月引动
            completeness = "待用（需冲引发）"

        # 如果有静爻但被暗动减轻
        _combo_d = {
            "element": combo_element,
            "branches": combo_branches,
        }
        _broken = _check_broken_combo(_combo_d, day_branch, month_branch)

        desc = (
            f"{''.join(combo_branches)}成{combo_element}局，"
            f"位置{_pos_to_name(p1)}/{_pos_to_name(p2)}/{_pos_to_name(p3)}，"
            f"构成方式：{ftype}"
        )

        if completeness == "完整":
            desc += f"。{combo_element}力大增"
        elif completeness == "待用（需冲引发）":
            desc += "。静爻合局，待时日引发方成"

        if _broken["status"] == "破局":
            desc += f"。⚠破局：{'；'.join(_broken['issues'])}"

        details.append({
            "element": combo_element,
            "branches": combo_branches,
            "positions": sorted(positions),
            "completeness": completeness,
            "formation_type": ftype,
            "moving_count": moving_count,
            "hidden_count": hidden_count,
            "static_count": static_count,
            "combo_status": _broken["status"],
            "combo_issues": _broken["issues"],
            "combo_score_mod": _broken["score_mod"],
            "description": desc,
        })

    if not details:
        return {"has_triple_combo": False, "details": [], "summary": "本卦无三合局"}

    summary = "；".join(d["description"] for d in details)
    return {"has_triple_combo": True, "details": details, "summary": summary}


def analyze_advance_retreat(result):
    """
    进出神分析：动爻化进则势盛，化退则势衰。
    
    返回：
        {
            "has_advance_retreat": bool,
            "details": [
                {
                    "position": int,
                    "name": str,
                    "original_branch": str,
                    "changed_branch": str,
                    "type": "化进" or "化退" or "回头合" or "回头克" or "回头生" or "化泄" or "无进退",
                    "six_relation": str,
                    "six_spirit": str,
                    "description": str,
                },
                ...
            ],
            "summary": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    changed = result.get("changed_hexagram") or {}
    changed_name = changed.get("name")

    if not yao_lines or not changed_name:
        return {"has_advance_retreat": False, "details": [], "summary": "无动爻或无变卦"}

    # 获取月建日辰五行用于旺衰评分
    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    month_elem = BRANCH_ELEMENTS.get(month_branch, "")
    day_elem = BRANCH_ELEMENTS.get(day_branch, "")

    details = []
    for yao in yao_lines:
        if not yao.get("is_moving", False):
            continue

        pos = yao.get("position", 0)
        orig_branch = yao.get("earthly_branch", "")

        # 变卦中该位置的地支
        chg_branch = get_changed_hexagram_branch(changed_name, pos)
        if not chg_branch:
            continue

        # 判断进退
        advance_score = 0.0
        if ADVANCE_PAIRS.get(orig_branch) == chg_branch:
            advance_type = "化进"
            desc = (
                f"{_pos_to_name(pos)}({orig_branch}→{chg_branch})"
                f"化进神，力量递增，事态向前发展顺利"
            )
        elif RETREAT_PAIRS.get(orig_branch) == chg_branch:
            advance_type = "化退"
            desc = (
                f"{_pos_to_name(pos)}({orig_branch}→{chg_branch})"
                f"化退神，力量递减，事态逐渐后退/消退"
            )
        else:
            # 检查 回头合/回头克/回头生/化泄
            orig_elem = BRANCH_ELEMENTS.get(orig_branch, "")
            chg_elem = BRANCH_ELEMENTS.get(chg_branch, "")
            he_pair_match = ((orig_branch, chg_branch) in HE_PAIRS or
                             (chg_branch, orig_branch) in HE_PAIRS)
            if he_pair_match:
                advance_type = "回头合"
                desc = (
                    f"{_pos_to_name(pos)}({orig_branch}→{chg_branch})"
                    f"回头合（合住事态胶着）"
                )
            elif KE_CYCLE.get(chg_elem) == orig_elem:
                advance_type = "回头克"
                desc = (
                    f"{_pos_to_name(pos)}({orig_branch}→{chg_branch})"
                    f"回头克（大凶）"
                )
            elif SHENG_CYCLE.get(chg_elem) == orig_elem:
                advance_type = "回头生"
                desc = (
                    f"{_pos_to_name(pos)}({orig_branch}→{chg_branch})"
                    f"回头生（有救济）"
                )
            elif SHENG_CYCLE.get(orig_elem) == chg_elem:
                advance_type = "化泄"
                desc = (
                    f"{_pos_to_name(pos)}({orig_branch}→{chg_branch})"
                    f"化泄（力量消散）"
                )
            else:
                advance_type = "无进退"
                desc = (
                    f"{_pos_to_name(pos)}({orig_branch}→{chg_branch})"
                    f"不涉及进退神，需结合其他因素分析"
                )

        # ── 进退神五行力量量化（《增删卜易》） ──
        orig_elem = BRANCH_ELEMENTS.get(orig_branch, "")
        chg_elem = BRANCH_ELEMENTS.get(chg_branch, "")

        advance_orig_strength = _combined_strength(orig_elem, month_elem, day_elem)
        advance_orig_val = _strength_score(advance_orig_strength)
        advance_chg_strength = _combined_strength(chg_elem, month_elem, day_elem)
        advance_chg_val = _strength_score(advance_chg_strength)

        if advance_type == "化进":
            base_score = 2.0
            if advance_orig_val >= 4:
                base_score += 1.0  # 旺进有力
            elif advance_orig_val <= 2:
                base_score -= 0.5  # 休囚进而力微
            if advance_chg_val >= 4:
                base_score += 0.5  # 变爻旺，力量传导强
            # 逢冲减半
            if is_ba_zu_chong(orig_branch, day_branch) or is_ba_zu_chong(orig_branch, month_branch):
                base_score *= 0.5
                desc += "，逢冲减半"
            advance_score = base_score

        elif advance_type == "化退":
            base_score = -2.0
            if advance_orig_val >= 4:
                base_score += 0.5  # 旺退力弱（减衰减缓）
            elif advance_orig_val <= 2:
                base_score -= 0.5  # 休囚退而更凶
            if advance_chg_val <= 1:
                base_score -= 0.5  # 退入绝地，更凶
            # 逢冲加速退
            if is_ba_zu_chong(chg_branch, day_branch):
                base_score *= 0.7
                desc += "，逢冲加速退"
            advance_score = base_score

        details.append({
            "position": pos,
            "name": yao.get("name", ""),
            "original_branch": orig_branch,
            "changed_branch": chg_branch,
            "type": advance_type,
            "six_relation": yao.get("six_relation", ""),
            "six_spirit": yao.get("six_spirit", ""),
            "advance_score": advance_score,
            "advance_orig_strength": advance_orig_strength,
            "advance_chg_strength": advance_chg_strength,
            "description": desc,
        })

    if not details:
        return {"has_advance_retreat": False, "details": [], "summary": "无有效进退神分析"}

    summary = "；".join(d["description"] for d in details)
    return {"has_advance_retreat": True, "details": details, "summary": summary}


def analyze_twelve_growth(result):
    """
    十二长生分析：各爻在十二长生中的位置。
    
    返回：
        {
            "day_branch": str,
            "day_element": str,
            "lines": [
                {
                    "position": int,
                    "name": str,
                    "branch": str,
                    "element": str,
                    "six_relation": str,
                    "growth_stage": str,
                    "is_key_stage": bool,
                    "stage_meaning": str,
                },
                ...
            ],
            "summary": str,
            "key_lines": [int],  # 处于帝旺/长生/临官的关键爻位
            "weak_lines": [int], # 处于死/墓/绝的弱爻位
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    if not yao_lines:
        return {"day_branch": "", "day_element": "", "lines": [],
                "summary": "无数据", "key_lines": [], "weak_lines": []}

    dt = result.get("divination_time", {})
    day_sb = dt.get("day_stem_branch", "")
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    if not day_branch:
        return {"day_branch": "", "day_element": "", "lines": [],
                "summary": "无日辰数据", "key_lines": [], "weak_lines": []}

    day_element = _branch_element(day_branch)
    empty_branches = result.get("empty_branches", [])

    # 关键阶段含义
    stage_meaning = {
        "长生": CINTERP["twelve_changsheng"]["长生"]["text"],
        "沐浴": CINTERP["twelve_changsheng"]["沐浴"]["text"],
        "冠带": CINTERP["twelve_changsheng"]["冠带"]["text"],
        "临官": CINTERP["twelve_changsheng"]["临官"]["text"],
        "帝旺": CINTERP["twelve_changsheng"]["帝旺"]["text"],
        "衰": CINTERP["twelve_changsheng"]["衰"]["text"],
        "病": CINTERP["twelve_changsheng"]["病"]["text"],
        "死": CINTERP["twelve_changsheng"]["死"]["text"],
        "墓": CINTERP["twelve_changsheng"]["墓"]["text"],
        "绝": CINTERP["twelve_changsheng"]["绝"]["text"],
        "胎": CINTERP["twelve_changsheng"]["胎"]["text"],
        "养": CINTERP["twelve_changsheng"]["养"]["text"],
    }

    lines_out = []
    key_lines = []
    weak_lines = []

    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        elem = _branch_element(branch)
        stage = get_twelve_growth_stage(elem, day_branch)
        is_key = get_stages_of_interest(stage)

        is_weak_stage = stage in ("死", "墓", "绝")
        is_strong_stage = stage in ("帝旺", "临官", "长生")

        if is_weak_stage:
            weak_lines.append(yao["position"])
        if is_strong_stage:
            key_lines.append(yao["position"])

        lines_out.append({
            "position": yao["position"],
            "name": yao.get("name", ""),
            "branch": branch,
            "element": elem,
            "six_relation": yao.get("six_relation", ""),
            "growth_stage": stage,
            "is_key_stage": is_key,
            "stage_meaning": stage_meaning.get(stage, ""),
        })

    # 汇总
    parts = []
    if key_lines:
        key_desc = "、".join(f"{_pos_to_name(p)}{_find_stage_at(lines_out, p)}"
                            for p in key_lines)
        parts.append(f"得力之爻：{key_desc}")
    if weak_lines:
        weak_desc = "、".join(f"{_pos_to_name(p)}{_find_stage_at(lines_out, p)}"
                             for p in weak_lines)
        parts.append(f"无力之爻：{weak_desc}")

    summary = "；".join(parts) if parts else "各爻状态平和"

    return {
        "day_branch": day_branch,
        "day_element": day_element,
        "lines": lines_out,
        "summary": summary,
        "key_lines": key_lines,
        "weak_lines": weak_lines,
    }


def analyze_desperate_relief(result):
    """
    绝处逢生分析：当用神在日辰处逢"绝"或"死"地时，检查原神是否发动来生。

    若原神发动且有力 → "绝处逢生"（凶中反吉，+2.0）
    若原神发动但无力 → "绝处逢生但原神无力"（+0.5）
    若原神未发动但现于卦中 → "绝地待原神"（+0.2）
    若原神不现或旬空/月破 → "绝地无救"（-0.8）

    返回：
        {
            "has_desperate_relief": bool,
            "stage": str,               # "绝" / "死" / ""
            "yuan_shen_moving": bool,   # 原神是否发动
            "yuan_shen_strength": str,  # 原神综合旺衰
            "verdict": str,             # 断语标签
            "score_modifier": float,    # 分数修正
            "description": str,
        }
    """
    out = {
        "has_desperate_relief": False,
        "stage": "",
        "yuan_shen_moving": False,
        "yuan_shen_strength": "",
        "verdict": "",
        "score_modifier": 0.0,
        "description": "",
    }

    # Guard: requires original_hexagram and divination_time
    hex_info = result.get("original_hexagram")
    if not hex_info or not isinstance(hex_info, dict):
        return out

    yao_lines = hex_info.get("yao_lines", [])
    if not yao_lines:
        return out

    div_time = result.get("divination_time", {})
    day_sb = div_time.get("day_stem_branch", "")
    month_sb = div_time.get("month_stem_branch", "")
    day_branch = day_sb[1:] if isinstance(day_sb, str) and len(day_sb) >= 2 else ""
    month_branch = month_sb[1:] if isinstance(month_sb, str) and len(month_sb) >= 2 else ""
    if not day_branch:
        return out

    # ── Determine 用神 element ──
    use_god_element = ""
    # Prefer _step2_data (thinking chain) if present (put there by analyze)
    step2_data = result.get("_step2_data")
    if isinstance(step2_data, dict):
        use_god_element = step2_data.get("use_god_element", "")
        use_god_position = step2_data.get("use_god_position")
    else:
        use_god_position = None

    # Fallback: use 世爻 element
    if not use_god_element:
        for yao in yao_lines:
            if yao.get("is_world"):
                use_god_element = _branch_element(yao.get("earthly_branch", ""))
                break

    if not use_god_element:
        return out

    # ── Determine use-god position's branch for exact stage lookup ──
    use_god_branch = ""
    if use_god_position:
        for yao in yao_lines:
            if yao.get("position") == use_god_position:
                use_god_branch = yao.get("earthly_branch", "")
                break
    if not use_god_branch:
        # Fallback when position is unknown: use the 世爻 branch directly
        for yao in yao_lines:
            if yao.get("is_world"):
                use_god_branch = yao.get("earthly_branch", "")
                break
    if not use_god_branch:
        return out

    # ── Lookup 十二长生 stage ──
    tg = TWELVE_GROWTH.get(use_god_element)
    if not tg:
        return out

    stage = tg.get(day_branch, "")

    if stage not in ("绝", "死"):
        return out

    out["has_desperate_relief"] = True
    out["stage"] = stage

    # ── Determine 原神 element (the element that generates 用神) ──
    yuan_shen_element = SHENG_WO.get(use_god_element, "")
    if not yuan_shen_element:
        return out

    # ── Check 原神 status in the hexagram ──
    empty_branches = result.get("empty_branches", [])
    month_element = _branch_element(month_branch) if month_branch else _branch_element(day_branch)
    day_element = _branch_element(day_branch)

    yuan_shen_present = False
    yuan_shen_moving = False
    yuan_shen_empty = False
    yuan_shen_month_break = False
    yuan_shen_combined = "休"

    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        elem = _branch_element(branch)
        if elem != yuan_shen_element:
            continue
        yuan_shen_present = True
        if yao.get("is_moving", False):
            yuan_shen_moving = True
        if branch in empty_branches:
            yuan_shen_empty = True
        if month_branch and is_ba_zu_chong(branch, month_branch):
            yuan_shen_month_break = True

        # Compute combined strength (first match is enough — they share element)
        yuan_shen_combined = _combined_strength(yuan_shen_element, month_element, day_element)

    # If 原神 not found in main hexagram, check 伏藏 (hidden spirit analysis)
    if not yuan_shen_present:
        adv = result.get("advanced_analysis")
        if isinstance(adv, dict):
            hs_analysis = adv.get("hidden_spirit_analysis", {})
            if isinstance(hs_analysis, dict):
                details = hs_analysis.get("details", [])
                for detail in details:
                    hs = detail.get("hidden_spirit", {}) or {}
                    hs_elem = hs.get("element", "") or _branch_element(hs.get("branch", ""))
                    if hs_elem == yuan_shen_element:
                        yuan_shen_present = True
                        # 伏藏之原神 is dormant; not actively moving
                        yuan_shen_combined = element_strength_in_month(
                            yuan_shen_element, month_element
                        )
                        break

    out["yuan_shen_moving"] = yuan_shen_moving
    out["yuan_shen_strength"] = yuan_shen_combined

    # ── Apply judgment logic ──
    if yuan_shen_moving and yuan_shen_combined in ("旺", "相", "中和") and \
       not yuan_shen_empty and not yuan_shen_month_break:
        out["verdict"] = "绝处逢生"
        out["score_modifier"] = 2.0
        out["description"] = (
            f"用神{use_god_element}（{use_god_branch}）处{stage}地，"
            f"原神{yuan_shen_element}发动来生，原神{yuan_shen_combined}有力，"
            f"绝处逢生，凶中反吉"
        )
    elif yuan_shen_moving and not yuan_shen_empty and not yuan_shen_month_break:
        out["verdict"] = "绝处逢生但原神无力"
        out["score_modifier"] = 0.5
        out["description"] = (
            f"用神{use_god_element}（{use_god_branch}）处{stage}地，"
            f"原神{yuan_shen_element}发动来生，但原神{yuan_shen_combined}无力，"
            f"虽生而力微"
        )
    elif yuan_shen_present and not yuan_shen_empty and not yuan_shen_month_break:
        out["verdict"] = "绝地待原神"
        out["score_modifier"] = 0.2
        out["description"] = (
            f"用神{use_god_element}（{use_god_branch}）处{stage}地，"
            f"原神{yuan_shen_element}虽现于卦中但未发动，待时而动"
        )
    elif not yuan_shen_present:
        out["verdict"] = "绝地无救"
        out["score_modifier"] = -0.8
        out["description"] = (
            f"用神{use_god_element}（{use_god_branch}）处{stage}地，"
            f"原神{yuan_shen_element}不现于卦中，绝地无救"
        )
    else:
        # 原神 present but empty or month-broken
        out["verdict"] = "绝地无救"
        out["score_modifier"] = -0.8
        out["description"] = (
            f"用神{use_god_element}（{use_god_branch}）处{stage}地，"
            f"原神{yuan_shen_element}虽现但{'旬空' if yuan_shen_empty else '月破'}，"
            f"无力救援，绝地无救"
        )

    return out


def analyze_clash_harmony(result):
    """
    六合/六冲卦判断：
    - 检查各对应位置爻对(1-4, 2-5, 3-6)的地支关系
    - 全部合 → 六合卦
    - 全部冲 → 六冲卦
    - 部分合、部分冲 → 描述各异
    
    返回：
        {
            "hexagram_type": str,    # "六合卦"/"六冲卦"/"半合半冲"/"无明确合冲"
            "pairs": [
                {
                    "positions": (int, int),
                    "branches": (str, str),
                    "relation": str,    # "合"/"冲"/"无特殊"
                    "description": str,
                },
                ...
            ],
            "summary": str,
            "meaning": str,  # 六合/六冲的含义解释
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    if not yao_lines:
        return {"hexagram_type": "未知", "pairs": [], "summary": "无数据", "meaning": ""}

    yao_by_pos = {y["position"]: y for y in yao_lines}

    # 三对对应位置
    pair_positions = [(1, 4), (2, 5), (3, 6)]
    pairs = []
    he_count = 0
    chong_count = 0

    for p1, p2 in pair_positions:
        y1 = yao_by_pos.get(p1, {})
        y2 = yao_by_pos.get(p2, {})
        b1 = y1.get("earthly_branch", "")
        b2 = y2.get("earthly_branch", "")

        if is_ba_zu_he(b1, b2):
            relation = "合"
            he_count += 1
            desc = (f"位置{_pos_to_name(p1)}与{_pos_to_name(p2)}"
                    f"（{b1}与{b2}）六合")
        elif is_ba_zu_chong(b1, b2):
            relation = "冲"
            chong_count += 1
            desc = (f"位置{_pos_to_name(p1)}与{_pos_to_name(p2)}"
                    f"（{b1}与{b2}）六冲")
        else:
            relation = "无特殊"
            desc = (f"位置{_pos_to_name(p1)}与{_pos_to_name(p2)}"
                    f"（{b1}与{b2}）无合冲")

        pairs.append({
            "positions": (p1, p2),
            "branches": (b1, b2),
            "relation": relation,
            "description": desc,
        })

    if he_count == 3:
        hexagram_type = "六合卦"
        meaning = (
            CINTERP["liuhe_hex"]["text"]
            + CINTERP["liuhe_hex_2"]["text"]
            + CINTERP["liuhe_hex_3"]["text"]
            + CINTERP["liuhe_hex_4"]["text"]
        )
    elif chong_count == 3:
        hexagram_type = "六冲卦"
        meaning = (
            CINTERP["liuchong_hex"]["text"]
            + CINTERP["liuchong_hex_2"]["text"]
            + CINTERP["liuchong_hex_3"]["text"]
            + CINTERP["liuchong_hex_4"]["text"]
        )
    elif he_count > 0 and chong_count > 0:
        hexagram_type = "半合半冲"
        meaning = (
            f"本卦有六合又有六冲（合{he_count}对、冲{chong_count}对），"
            + CINTERP["half_he_half_chong"]["text"]
        )
    elif he_count > 0:
        hexagram_type = "有合"
        meaning = (
            f"本卦有{he_count}对合{'' if chong_count == 0 else f'，{chong_count}对冲'}，"
            + CINTERP["has_he"]["text"]
        )
    elif chong_count > 0:
        hexagram_type = "有冲"
        meaning = (
            f"本卦有{chong_count}对冲，"
            + CINTERP["has_chong"]["text"]
        )
    else:
        hexagram_type = "无明确合冲"
        meaning = CINTERP["no_he_chong"]["text"]

    pair_summaries = "；".join(p["description"] for p in pairs)
    summary = f"{hexagram_type}：{pair_summaries}"

    return {
        "hexagram_type": hexagram_type,
        "pairs": pairs,
        "summary": summary,
        "meaning": meaning,
    }


def analyze_repetition(result):
    """
    反吟伏吟分析：
    - 反吟：变卦之爻地支与本卦对应爻地支相冲（反复之意）
    - 伏吟：变卦与本卦相同（或内/外卦不变），爻位地支不变（呻吟不止）
    
    返回：
        {
            "repetition_type": str,  # "反吟"/"伏吟"/"反吟兼伏吟"/"无"
            "chong_pairs": [
                {
                    "position": int,
                    "original_branch": str,
                    "changed_branch": str,
                    "description": str,
                },
                ...
            ],
            "summary": str,
            "meaning": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    changed = result.get("changed_hexagram") or {}
    changed_name = changed.get("name")
    changed_lines = changed.get("changed_lines", [])

    if not yao_lines or not changed_name or not changed_lines:
        return {
            "repetition_type": "无",
            "chong_pairs": [],
            "summary": "本卦无动爻，不存在反吟伏吟",
            "meaning": "",
        }

    # 判断伏吟：如果所有爻都没变（理论上在变卦时有changed_lines，说明有变爻）
    # 伏吟的判定：变卦=本卦（不可能，因为有changed_lines）
    # 或者：内卦或外卦的三爻全部变化但变后相同（如乾→乾，但动爻变了又变回）
    # 这里准确判定：变卦各爻的地支与本卦对比
    yao_by_pos = {y["position"]: y for y in yao_lines}

    chong_pairs = []
    same_count = 0
    diff_count = 0

    for pos in range(1, 7):
        orig_branch = yao_by_pos.get(pos, {}).get("earthly_branch", "")
        chg_branch = get_changed_hexagram_branch(changed_name, pos)

        if orig_branch and chg_branch:
            if is_ba_zu_chong(orig_branch, chg_branch):
                chong_pairs.append({
                    "position": pos,
                    "original_branch": orig_branch,
                    "changed_branch": chg_branch,
                    "description": (
                        f"{_pos_to_name(pos)}：{orig_branch}→{chg_branch}，"
                        f"本支被冲，反复变动之象"
                    ),
                })
                diff_count += 1
            elif orig_branch == chg_branch:
                same_count += 1
            else:
                diff_count += 1

    # 反吟判定：有地支相冲的变爻对
    has_fanyin = len(chong_pairs) > 0

    # 伏吟判定：内卦或外卦三爻变化后地支不变
    # 内卦(1-3)全部变化且变后分支不变
    inner_same = True
    inner_all_changed = True
    for pos in range(1, 4):
        in_changed = pos in changed_lines
        if not in_changed:
            inner_all_changed = False
            break
        orig_branch = yao_by_pos.get(pos, {}).get("earthly_branch", "")
        chg_branch = get_changed_hexagram_branch(changed_name, pos)
        if orig_branch != chg_branch:
            inner_same = False

    outer_same = True
    outer_all_changed = True
    for pos in range(4, 7):
        in_changed = pos in changed_lines
        if not in_changed:
            outer_all_changed = False
            break
        orig_branch = yao_by_pos.get(pos, {}).get("earthly_branch", "")
        chg_branch = get_changed_hexagram_branch(changed_name, pos)
        if orig_branch != chg_branch:
            outer_same = False

    has_fuyin = (inner_all_changed and inner_same) or (outer_all_changed and outer_same)

    if has_fanyin and has_fuyin:
        repetition_type = "反吟兼伏吟"
        meaning = (
            CINTERP["fanyin_and_fuyin"]["text"]
            + CINTERP["fanyin_and_fuyin_2"]["text"]
        )
    elif has_fanyin:
        repetition_type = "反吟"
        meaning = (
            CINTERP["fanyin"]["text"]
            + CINTERP["fanyin_2"]["text"]
            + CINTERP["fanyin_3"]["text"]
        )
    elif has_fuyin:
        repetition_type = "伏吟"
        meaning = (
            CINTERP["fuyin"]["text"]
            + CINTERP["fuyin_2"]["text"]
            + CINTERP["fuyin_3"]["text"]
        )
    else:
        repetition_type = "无"
        meaning = CINTERP["no_fanyin_fuyin"]["text"]

    summary_parts = []
    if has_fanyin:
        summary_parts.append(
            f"反吟：{len(chong_pairs)}处地支相冲 "
            f"({'、'.join(d['description'] for d in chong_pairs)})"
        )
    if has_fuyin:
        trigram = "内卦" if inner_all_changed and inner_same else "外卦"
        summary_parts.append(f"伏吟：{trigram}伏吟")

    summary = "；".join(summary_parts) if summary_parts else "无反吟伏吟"

    return {
        "repetition_type": repetition_type,
        "chong_pairs": chong_pairs,
        "fuyin_trigram": ("内卦" if inner_all_changed and inner_same else
                         "外卦" if outer_all_changed and outer_same else None),
        "summary": summary,
        "meaning": meaning,
    }


def analyze_repetition_deep(result):
    """
    反吟伏吟深层析义：基于《卜筮正宗》的五行旺衰综合规则，
    对反吟伏吟进行精细化评分，而非统一扣减。

    返回：
        {
            "type": "反吟" | "伏吟" | None,
            "level": "卦" | "爻",
            "scope": "内卦" | "外卦" | "用神" | "世爻" | None,
            "interpretation": str,
            "score_modifier": float,
            "classical_quote": str,
        }
    """
    # 先调用基础分析获取类型信息
    basic = analyze_repetition(result)
    rep_type = basic.get("repetition_type", "无")

    if rep_type == "无":
        return {
            "type": None,
            "level": None,
            "scope": None,
            "interpretation": "",
            "score_modifier": 0.0,
            "classical_quote": "",
        }

    # 判断是反吟还是伏吟为主（"反吟兼伏吟"拆为反吟优先）
    if "反吟" in rep_type:
        main_type = "反吟"
    elif "伏吟" in rep_type:
        main_type = "伏吟"
    else:
        main_type = None

    # 判断 level：卦级别 vs 爻级别
    hex_info = result.get("original_hexagram", {})
    changed = result.get("changed_hexagram") or {}
    changed_name = changed.get("name")
    original_name = hex_info.get("name", "")

    level = "爻"
    if original_name and changed_name and original_name != changed_name:
        # 检查是否是整个卦变了（如六冲变六冲）
        yao_lines = hex_info.get("yao_lines", [])
        changed_lines = changed.get("changed_lines", [])
        if len(changed_lines) >= 3:
            # 检查是否内外卦地支全冲
            chong_count = basic.get("chong_pairs", [])
            if len(chong_count) >= 4:
                level = "卦"

    # 判断 scope
    scope = None
    chong_pairs = basic.get("chong_pairs", [])
    fuyin_trigram = basic.get("fuyin_trigram")

    # 检查是否涉及世爻
    generation_str = hex_info.get("generation", "")
    gen_map_reverse = {"六世": 6, "五世": 5, "四世": 4, "三世": 3,
                       "二世": 2, "一世": 1, "游魂": 4, "归魂": 3}
    world_pos = gen_map_reverse.get(generation_str, 1)

    # 获取用神位置(s)
    use_god_positions = _find_use_god_positions(result)

    # 检查反吟/伏吟是否涉及用神或世爻
    involved_positions = set()
    for cp in chong_pairs:
        if isinstance(cp, dict):
            involved_positions.add(cp.get("position", 0))

    if main_type == "伏吟":
        # 伏吟涉及变化的爻位
        changed_lines = changed.get("changed_lines", [])
        involved_positions = set(changed_lines) if changed_lines else set()

    if world_pos in involved_positions:
        scope = "世爻"
    elif any(p in involved_positions for p in use_god_positions):
        scope = "用神"
    elif fuyin_trigram:
        scope = "内卦" if fuyin_trigram == "内卦" else "外卦"
    elif chong_pairs:
        # 根据相冲爻位判断内外
        first_pos = chong_pairs[0].get("position", 1) if isinstance(chong_pairs[0], dict) else 1
        scope = "内卦" if first_pos <= 3 else "外卦"
    else:
        scope = None

    # 获取用神旺衰状态以确定评分
    use_god_strength = _get_use_god_strength_level(result)

    # 根据规则评分
    if main_type == "反吟":
        score_modifier, interpretation, classical_quote = _score_fanyin(
            scope, use_god_strength, level, chong_pairs, basic
        )
    else:  # 伏吟
        score_modifier, interpretation, classical_quote = _score_fuyin(
            scope, use_god_strength, result, basic
        )

    return {
        "type": main_type,
        "level": level,
        "scope": scope,
        "interpretation": interpretation,
        "score_modifier": round(score_modifier, 2),
        "classical_quote": classical_quote,
    }


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
            "meaning": "无法确定卦身（卦代未知）",
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
        response_texts.append(f"卦身在{_pos_to_name(body_pos)}，{body_relation}坐镇，本位安定")

    return {
        "body_position": body_pos,
        "body_element": body_element,
        "body_relation": body_relation,
        "meaning": f"卦身在{_pos_to_name(body_pos)}，代表事体核心与根基",
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
                "details": [], "summary": "无数据"}

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
            special.append("旬空")
        if is_ba_zu_chong(branch, month_branch):
            special.append("月破")
        if is_ba_zu_chong(branch, day_branch):
            special.append("日冲")
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
        f"月建{month_branch}({month_element})，日辰{day_branch}({day_element})",
        f"当月旺衰：{strength_desc}",
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
        summary_lines.append(f"旺相之爻：{s_desc}")
    if weak_yaos:
        w_desc = "、".join(
            f"{d['six_relation']}({d['branch']},{d['month_strength']}/{d['day_strength']})"
            for d in weak_yaos
        )
        summary_lines.append(f"休囚之爻：{w_desc}")

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
        return {"has_punishment": False, "punishments": [], "total_score": 0.0, "summary": "无数据"}

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
            hex_branches.append((branch, f"爻{_pos_to_name(yao['position'])}"))

    external_branches = []
    if month_branch:
        external_branches.append((month_branch, f"月建({month_branch})"))
    if day_branch:
        external_branches.append((day_branch, f"日辰({day_branch})"))

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
                    f"{ptype}（完整三刑）：{present[0]}刑{present[1]}刑{present[2]}，"
                    f"三字全见于{ '、'.join(pos_list) }，极凶之象"
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
                    f"{ptype}（催刑）：卦内{ '、'.join(p for p in present if p in hex_set) or '无'}，"
                    f"月日{ '、'.join(p for p in present if p not in hex_set) }补足成刑，"
                    f"刑伤力减半"
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
                    f"{ptype}（待刑）：{present[0]}、{present[1]}相见，"
                    f"缺{missing[0]}，待月日逢{missing[0]}方成刑，"
                    f"目前刑伤未全，但有刑伤之象"
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
                    f"无礼之刑（成刑）：{b1_key}刑{b2_key}，"
                    f"见于{ '、'.join(pos_list) }，主无礼刑伤、恩中之怨"
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
                    f"无礼之刑（待刑）：{b1_key}、{b2_key}月日相见，"
                    f"刑伤未全，主微咎"
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
                    f"自刑：{sp_branch}出现{count}次"
                    f"（{ '、'.join(pos_list) }），"
                    f"自刑主自我纠结、自作自受、内心矛盾"
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
        return {"has_punishment": False, "punishments": [], "total_score": 0.0, "summary": "本卦无三刑"}

    summary_parts = [p["description"] for p in punishments]

    return {
        "has_punishment": True,
        "punishments": punishments,
        "total_score": round(total_score, 2),
        "summary": "；".join(summary_parts),
    }


def analyze_day_month_bonding(result):
    """
    检测用神/忌神与日辰/月建的六合关系。

    经典规则：
    - 用神合日："切近有力" — immediate power, near-term response
    - 用神合月："事必成就" — success within the month
    - 月日同合：大吉之极
    - 忌神合月日：忌神有力为祸

    返回:
        {
            "findings": [{"bond": str, "effect": str, "score": float}, ...],
            "total_score_modifier": float,
            "summary": str,
        }
    """
    # Build bidirectional 六合 lookup
    HE_SET_BI = set()
    for a, b in HE_PAIRS:
        HE_SET_BI.add((a, b))
        HE_SET_BI.add((b, a))

    # Extract 用神 branch from thinking chain step2
    use_god_branch = ""
    use_god_data = result.get("thinking_chain", {}).get("step2_use_god_identification", {})
    selected = use_god_data.get("selected_use_god", {})
    if isinstance(selected, dict):
        use_god_branch = selected.get("earthly_branch", "")

    # Also check step3 which has use_god_branch explicitly
    if not use_god_branch:
        step3 = result.get("thinking_chain", {}).get("step3_strength_analysis", {})
        use_god_branch = step3.get("use_god_branch", "")

    # Fallback: find use_god from yao_lines via six_relation matching use_god_category
    if not use_god_branch:
        yao_lines = result.get("original_hexagram", {}).get("yao_lines", [])
        use_god_cat = use_god_data.get("use_god_category", "")
        for yao in yao_lines:
            if yao.get("six_relation") == use_god_cat:
                use_god_branch = yao.get("earthly_branch", "")
                break

    # Extract 忌神 positions/branches from step2
    ji_shen_branches = []
    ji_shen_data = use_god_data.get("ji_shen", {})
    if isinstance(ji_shen_data, dict):
        ji_positions = ji_shen_data.get("positions", [])
        if isinstance(ji_positions, list):
            for jp in ji_positions:
                if isinstance(jp, dict):
                    jb = jp.get("earthly_branch", "")
                    if jb:
                        ji_shen_branches.append(jb)
        # Also check fu_cang
        ji_fu = ji_shen_data.get("fu_cang")
        if isinstance(ji_fu, dict):
            jb = ji_fu.get("branch", "")
            if jb:
                ji_shen_branches.append(jb)

    div_time = result.get("divination_time", {})
    # day_branch/month_branch may be stored directly or derived from stem_branch
    day_branch = div_time.get("day_branch", "")
    month_branch = div_time.get("month_branch", "")
    if not day_branch:
        day_sb = div_time.get("day_stem_branch", "")
        if len(day_sb) >= 2:
            day_branch = day_sb[1]
    if not month_branch:
        month_sb = div_time.get("month_stem_branch", "")
        if len(month_sb) >= 2:
            month_branch = month_sb[1]

    findings = []

    # 用神合日
    if use_god_branch and day_branch and (use_god_branch, day_branch) in HE_SET_BI:
        findings.append({"bond": "日合用神", "effect": "切近有力", "score": 0.5})

    # 用神合月
    if use_god_branch and month_branch and (use_god_branch, month_branch) in HE_SET_BI:
        findings.append({"bond": "月合用神", "effect": "事必成就", "score": 0.4})

    # 月日同合 check
    if (use_god_branch and day_branch and month_branch
            and (use_god_branch, day_branch) in HE_SET_BI
            and (use_god_branch, month_branch) in HE_SET_BI):
        findings.append({"bond": "月日同合用神", "effect": "大吉之极", "score": 0.3})

    # 忌神合日/月 (negative effect)
    for ji_b in ji_shen_branches:
        if ji_b and day_branch and (ji_b, day_branch) in HE_SET_BI:
            findings.append({"bond": "日合忌神", "effect": "忌神有力为祸", "score": -0.3})
        if ji_b and month_branch and (ji_b, month_branch) in HE_SET_BI:
            findings.append({"bond": "月合忌神", "effect": "忌神缠月不解", "score": -0.25})

    total_modifier = sum(f["score"] for f in findings)

    # Build summary
    if findings:
        summary_parts = [f"{f['bond']}（{f['effect']}）" for f in findings]
        summary = "；".join(summary_parts)
    else:
        summary = "无用神/忌神与日辰月建之合"

    return {
        "findings": findings,
        "use_god_branch": use_god_branch,
        "ji_shen_branches": ji_shen_branches,
        "day_branch": day_branch,
        "month_branch": month_branch,
        "total_score_modifier": total_modifier,
        "summary": summary,
    }


def analyze_six_breaks(result):
    """
    六破系统：次级冲克关系，弱于六冲但仍有害。

    六破对：子酉破、午卯破、巳申破、寅亥破、辰丑破、戌未破
    注意：巳申、寅亥既是六合又是六破 → "合中带破"

    检查：
    - 各爻与月建之间的六破
    - 各爻与日辰之间的六破
    - 世爻/用爻被破 → 加重

    返回:
        {
            "breaks": [break_dict, ...],
            "has_break": bool,
            "total_modifier": float,
            "description": str,
            "summary": str,
        }
    """
    HE_SET_BI = set()
    for a, b in HE_PAIRS:
        HE_SET_BI.add((a, b))
        HE_SET_BI.add((b, a))

    BREAK_SET_BI = set()
    for a, b in BREAK_PAIRS:
        BREAK_SET_BI.add((a, b))
        BREAK_SET_BI.add((b, a))

    yao_lines = result.get("original_hexagram", {}).get("yao_lines", [])
    div_time = result.get("divination_time", {})
    # day_branch/month_branch may be stored directly or derived from stem_branch
    day_b = div_time.get("day_branch", "")
    month_b = div_time.get("month_branch", "")
    if not day_b:
        day_sb = div_time.get("day_stem_branch", "")
        if len(day_sb) >= 2:
            day_b = day_sb[1]
    if not month_b:
        month_sb = div_time.get("month_stem_branch", "")
        if len(month_sb) >= 2:
            month_b = month_sb[1]

    # Identify use-god branch and is_world flags
    use_god_branch = ""
    step3 = result.get("thinking_chain", {}).get("step3_strength_analysis", {})
    use_god_branch = step3.get("use_god_branch", "")

    use_god_cat = result.get("thinking_chain", {}).get("step2_use_god_identification", {}).get("use_god_category", "")

    world_positions = set()
    use_god_positions = set()
    for yao in yao_lines:
        if yao.get("is_world"):
            world_positions.add(yao.get("position"))
        if yao.get("six_relation") == use_god_cat and use_god_cat:
            use_god_positions.add(yao.get("position"))
        # Also match by branch if step3 has it
        if use_god_branch and yao.get("earthly_branch") == use_god_branch:
            use_god_positions.add(yao.get("position"))

    breaks = []
    for yao in yao_lines:
        b = yao.get("earthly_branch", "")
        if not b:
            continue
        pos = yao.get("position")
        is_critical = pos in world_positions or pos in use_god_positions

        # Check vs 日辰
        for ref_branch, ref_label in [(day_b, "日"), (month_b, "月")]:
            if not ref_branch:
                continue
            if (b, ref_branch) in BREAK_SET_BI:
                is_both_he = (b, ref_branch) in HE_SET_BI
                break_type = "合中带破" if is_both_he else "纯破"
                severity = "重" if is_critical else "轻"
                score = -0.3 if is_critical else -0.15
                breaks.append({
                    "branch": b,
                    "vs": ref_label,
                    "vs_branch": ref_branch,
                    "position": pos,
                    "type": break_type,
                    "severity": severity,
                    "is_critical": is_critical,
                    "score": score,
                    "description": (
                        f"{'世/用爻' if is_critical else ''}{_pos_to_name(pos)}爻{b}"
                        f"与{ref_label}{ref_label == '日' and '辰' or '建'}{ref_branch}"
                        f"成{break_type}，{'破损不遂' if is_critical else '微有损伤'}"
                    ),
                })

    total_modifier = sum(br.get("score", 0) for br in breaks)

    if breaks:
        po_count = len(breaks)
        he_po_count = sum(1 for br in breaks if br["type"] == "合中带破")
        desc = f"六破{po_count}处，皆主破损不遂"
        if he_po_count > 0:
            desc += f"（其中{he_po_count}处合中带破，恩中有怨）"
        summary_parts = [br["description"] for br in breaks]
        summary = "；".join(summary_parts)
    else:
        desc = ""
        summary = "无六破"

    return {
        "breaks": breaks,
        "has_break": len(breaks) > 0,
        "total_modifier": total_modifier,
        "description": desc,
        "summary": summary,
    }


def analyze_officer_tomb(result):
    """
    随官入墓分析：世爻/用神与官鬼同临墓库地支的凶象。

    《卜筮正宗》"随官入墓"歌诀：
    > "随官入墓最凶凶，世用临之祸不轻。官鬼入墓身难保，病人入墓必归冥。"

    检测五种情形：
    1. 官鬼入墓：官鬼五行对应的墓库地支出现在卦中
    2. 世随官入墓：世爻地支 = 官鬼的墓库地支
    3. 用随官入墓：用神地支 = 官鬼的墓库地支（极凶）
    4. 鬼用同墓：官鬼自身地支 = 墓支 且 世/用也临此墓
    5. 官鬼动化墓：官鬼动爻的变爻为墓库地支

    墓库对应：金墓丑、木墓未、火墓戌、水墓辰、土墓辰

    返回：
        {
            "has_officer_tomb": bool,
            "severity": "mild" | "severe" | "catastrophic" | "none",
            "scenarios": [str],
            "officer_branches": [str],
            "tomb_branch": str,
            "description": str,
            "score_modifier": float,
            "classical_quote": str,
            "details": [dict],
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    palace_element = hex_info.get("palace_element", "")
    question = result.get("question", "")

    if not yao_lines or not palace_element:
        return {
            "has_officer_tomb": False,
            "severity": "none",
            "scenarios": [],
            "officer_branches": [],
            "tomb_branch": "",
            "description": "数据不足，无法分析随官入墓",
            "score_modifier": 0.0,
            "classical_quote": CINTERP["guan_tomb_poem"]["text"],
            "details": [],
        }

    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""

    # 1. 找世爻地支
    world_branch = None
    world_pos = None
    for yao in yao_lines:
        if yao.get("is_world"):
            world_branch = yao.get("earthly_branch", "")
            world_pos = yao.get("position")
            break

    # 2. 推断用神类别并找用神地支
    use_god_category = _infer_use_god_category(question)
    use_god_branch = None
    use_god_pos = None
    if use_god_category == "世爻":
        use_god_branch = world_branch
        use_god_pos = world_pos
    else:
        for yao in yao_lines:
            if yao.get("six_relation") == use_god_category:
                use_god_branch = yao.get("earthly_branch", "")
                use_god_pos = yao.get("position")
                break
        # 用神不现则fallback到世爻
        if use_god_branch is None:
            use_god_branch = world_branch
            use_god_pos = world_pos

    # 3. 收集卦中所有地支（本卦 + 变卦 + 日月）
    present_branches = set()
    for yao in yao_lines:
        b = yao.get("earthly_branch", "")
        if b:
            present_branches.add(b)
    changed = result.get("changed_hexagram") or {}
    changed_name = changed.get("name")
    if changed_name:
        for pos_idx in range(1, 7):
            chg_branch = get_changed_hexagram_branch(changed_name, pos_idx)
            if chg_branch:
                present_branches.add(chg_branch)
    if month_branch:
        present_branches.add(month_branch)
    if day_branch:
        present_branches.add(day_branch)

    # 4. 找所有官鬼爻
    officer_lines = []
    for yao in yao_lines:
        if yao.get("six_relation") == "官鬼":
            officer_lines.append(yao)

    # 如果本卦无显式官鬼，检查伏藏官鬼
    if not officer_lines:
        hidden_analysis = result.get("advanced_analysis", {}).get("hidden_spirit_analysis", {})
        if isinstance(hidden_analysis, dict) and hidden_analysis.get("has_hidden_spirit"):
            for d in hidden_analysis.get("details", []):
                if d.get("missing_relation") == "官鬼":
                    hs = d.get("hidden_spirit", {})
                    officer_lines.append({
                        "position": hs.get("position", 0),
                        "name": hs.get("name", ""),
                        "earthly_branch": hs.get("branch", ""),
                        "six_relation": "官鬼",
                        "is_moving": False,
                        "is_hidden": True,
                    })

    if not officer_lines:
        return {
            "has_officer_tomb": False,
            "severity": "none",
            "scenarios": [],
            "officer_branches": [],
            "tomb_branch": "",
            "description": "本卦无官鬼爻，不论随官入墓",
            "score_modifier": 0.0,
            "classical_quote": CINTERP["guan_tomb_poem"]["text"],
            "details": [],
        }

    # 5. 逐官鬼分析入墓
    scenarios = []
    details = []
    officer_branches_collected = []
    worst_severity = "none"
    total_score_modifier = 0.0
    primary_tomb_branch = ""

    for officer in officer_lines:
        off_branch = officer.get("earthly_branch", "")
        if not off_branch:
            continue
        off_pos = officer.get("position", 0)
        off_name = officer.get("name") or _pos_to_name(off_pos)
        off_element = _branch_element(off_branch)
        is_moving = officer.get("is_moving", False)

        officer_branches_collected.append(off_branch)

        # 官鬼五行对应的墓库地支
        tomb = TOMB_MAP.get(off_element, "")
        if not tomb:
            continue

        if not primary_tomb_branch:
            primary_tomb_branch = tomb

        # 场景a: 官鬼入墓 -- 墓库地支出现在本卦/变卦/日月中
        officer_in_tomb = tomb in present_branches
        self_tomb = (off_branch == tomb)

        if officer_in_tomb or self_tomb:
            if "官鬼入墓" not in scenarios:
                scenarios.append("官鬼入墓")
            source = "本卦/变卦/日月中" if officer_in_tomb else "本支即墓"
            details.append({
                "type": "官鬼入墓",
                "officer_branch": off_branch,
                "officer_element": off_element,
                "tomb_branch": tomb,
                "description": f"官鬼{off_element}({off_name}·{off_branch})入墓于{tomb}（{source}）",
            })
            if worst_severity == "none":
                worst_severity = "mild"
            total_score_modifier += (-0.2 if self_tomb else -0.3)

        # 场景b: 世随官入墓 -- 世爻地支 = 官鬼墓库
        if world_branch and world_branch == tomb:
            if "世随官入墓" not in scenarios:
                scenarios.append("世随官入墓")
            details.append({
                "type": "世随官入墓",
                "officer_branch": off_branch,
                "world_branch": world_branch,
                "tomb_branch": tomb,
                "description": f"世爻{world_branch}临官鬼{off_element}之墓{tomb}，自身随鬼入墓，凶象显著",
            })
            worst_severity = "severe"
            total_score_modifier += -1.0

        # 场景c: 用随官入墓 -- 用神地支 = 官鬼墓库
        if use_god_branch and use_god_branch == tomb:
            if "用随官入墓" not in scenarios:
                scenarios.append("用随官入墓")
            details.append({
                "type": "用随官入墓",
                "officer_branch": off_branch,
                "use_god_branch": use_god_branch,
                "use_god_category": use_god_category,
                "tomb_branch": tomb,
                "description": (
                    f"用神{use_god_category}({use_god_branch})临官鬼{off_element}之墓{tomb}，"
                    f"用神被鬼所困，极凶"
                ),
            })
            worst_severity = "severe"
            total_score_modifier += -1.5

        # 场景d: 鬼用同墓 -- 官鬼自身地支即墓 且 世/用也临此墓
        if off_branch == tomb and (world_branch == tomb or use_god_branch == tomb):
            if "鬼用同墓" not in scenarios:
                scenarios.append("鬼用同墓")
            details.append({
                "type": "鬼用同墓",
                "officer_branch": off_branch,
                "world_branch": world_branch,
                "use_god_branch": use_god_branch,
                "tomb_branch": tomb,
                "description": f"官鬼({off_branch})与世/用神同墓于{tomb}，鬼用同墓，灾难性凶象",
            })
            worst_severity = "catastrophic"
            total_score_modifier += -2.0

        # 场景e: 官鬼动化墓 -- 官鬼发动且变爻为墓库地支
        if is_moving and changed_name:
            chg_branch = get_changed_hexagram_branch(changed_name, off_pos)
            if chg_branch == tomb:
                if "官鬼动化墓" not in scenarios:
                    scenarios.append("官鬼动化墓")
                details.append({
                    "type": "官鬼动化墓",
                    "officer_branch": off_branch,
                    "changed_branch": chg_branch,
                    "tomb_branch": tomb,
                    "description": (
                        f"官鬼{off_name}({off_branch})动而化墓({chg_branch})，"
                        f"鬼动入墓，凶象加剧"
                    ),
                })
                if worst_severity in ("none", "mild"):
                    worst_severity = "severe"
                else:
                    worst_severity = "severe"
                total_score_modifier += -1.0

    # 6. 综合输出
    if not scenarios:
        return {
            "has_officer_tomb": False,
            "severity": "none",
            "scenarios": [],
            "officer_branches": officer_branches_collected,
            "tomb_branch": primary_tomb_branch,
            "description": (
                f"官鬼({','.join(officer_branches_collected)})未入墓"
                f"或世/用未随鬼入墓，无随官入墓凶象"
            ),
            "score_modifier": 0.0,
            "classical_quote": CINTERP["guan_tomb_poem"]["text"],
            "details": [],
        }

    severity_text = {
        "mild": "轻微",
        "severe": "严重",
        "catastrophic": "极凶/灾难性",
    }

    scenario_descriptions = {
        "官鬼入墓": CINTERP["officer_tomb_officer"]["text"],
        "世随官入墓": CINTERP["officer_tomb_world"]["text"],
        "用随官入墓": CINTERP["officer_tomb_use"]["text"],
        "鬼用同墓": CINTERP["officer_tomb_both"]["text"],
        "官鬼动化墓": CINTERP["officer_tomb_moving"]["text"],
    }

    desc_parts = [scenario_descriptions.get(s, s) for s in scenarios]
    description = (
        f"检测到随官入墓格局（{severity_text.get(worst_severity, '')}）："
        f"{'、'.join(desc_parts)}。"
    )
    if worst_severity == "catastrophic":
        description += CINTERP["officer_tomb_catastrophic"]["text"]
    elif worst_severity == "severe":
        description += CINTERP["officer_tomb_severe"]["text"]
    else:
        description += CINTERP["officer_tomb_mild"]["text"]

    return {
        "has_officer_tomb": True,
        "severity": worst_severity,
        "scenarios": scenarios,
        "officer_branches": officer_branches_collected,
        "tomb_branch": primary_tomb_branch,
        "description": description,
        "score_modifier": round(total_score_modifier, 2),
        "classical_quote": CINTERP["guan_tomb_poem"]["text"],
        "details": details,
    }


def analyze_transformation_pattern(result):
    """
    八卦变爻深度推演：分析动爻排列规律及其附加意义。

    检查以下格局：
    - 连续三爻动：三个相邻动爻
    - 间隔动爻：1,3,5 或 2,4,6 交替
    - 上卦全动：四、五、上皆动
    - 下卦全动：初、二、三皆动
    - 对爻齐动：世爻与应爻同动
    - 用神原神齐动/用神忌神齐动

    返回：
        {
            "moving_positions": [int],
            "moving_count": int,
            "patterns": [str],
            "total_weight": float,
            "interpretation": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    # 世爻和应爻位置从爻中提取
    world_pos = 0
    response_pos = 0
    for yao in yao_lines:
        if yao.get("is_world"):
            world_pos = yao.get("position", 0)
        if yao.get("is_response"):
            response_pos = yao.get("position", 0)

    moving = []
    for yao in yao_lines:
        if yao.get("is_moving", False):
            moving.append(yao.get("position", 0))

    if len(moving) < 2:
        return {"pattern": None}

    patterns = []

    # 检查连续三爻动
    for i in range(1, 5):  # position 1~4 as starting point
        if all(p in moving for p in [i, i + 1, i + 2]):
            patterns.append("连续三爻动")
            break

    # 检查间隔动爻
    if moving == [1, 3, 5] or moving == [2, 4, 6]:
        patterns.append("间隔动爻")

    # 检查上卦全动 (positions 4,5,6)
    if all(p in moving for p in [4, 5, 6]):
        patterns.append("上卦全动")

    # 检查下卦全动 (positions 1,2,3)
    if all(p in moving for p in [1, 2, 3]):
        patterns.append("下卦全动")

    # 检查对爻齐动（世爻与应爻同动）
    if world_pos and response_pos and world_pos in moving and response_pos in moving:
        patterns.append("对爻齐动")

    # 检查用神原神齐动/用神忌神齐动
    # 需要从 thinking-chain 的用神信息获取
    question = result.get("question", "")
    use_god_cat = _infer_use_god_category(question)
    if use_god_cat and use_god_cat != "世爻":
        # 原神 = 生用神之五行对应的六亲
        use_god_elem = _relation_element(use_god_cat, hex_info.get("palace_element", ""))
        if use_god_elem:
            yuan_shen_elem = SHENG_WO.get(use_god_elem)  # 生我者为原神
            ji_shen_elem = KE_WO.get(use_god_elem)  # 克我者为忌神

            yuan_shen_rel = _element_to_relation(yuan_shen_elem, hex_info.get("palace_element", "")) if yuan_shen_elem else None
            ji_shen_rel = _element_to_relation(ji_shen_elem, hex_info.get("palace_element", "")) if ji_shen_elem else None

            use_god_moving = any(
                yao.get("is_moving") and yao.get("six_relation") == use_god_cat
                for yao in yao_lines
            )
            yuan_shen_moving = any(
                yao.get("is_moving") and yao.get("six_relation") == yuan_shen_rel
                for yao in yao_lines
            ) if yuan_shen_rel else False
            ji_shen_moving = any(
                yao.get("is_moving") and yao.get("six_relation") == ji_shen_rel
                for yao in yao_lines
            ) if ji_shen_rel else False

            if use_god_moving and yuan_shen_moving:
                patterns.append("用神原神齐动")
            if use_god_moving and ji_shen_moving:
                patterns.append("用神忌神齐动")

    total_weight = sum(
        TRANSFORMATION_PATTERNS.get(p, {}).get("weight", 1.0) for p in patterns
    )

    if patterns:
        interpretation = "；".join(
            TRANSFORMATION_PATTERNS.get(p, {}).get("advice", "") for p in patterns
        )
    else:
        interpretation = "无特殊格局"

    return {
        "moving_positions": moving,
        "moving_count": len(moving),
        "patterns": patterns,
        "total_weight": total_weight,
        "interpretation": interpretation,
    }


def analyze_flying_hidden_interaction(result):
    """
    飞伏深度互断：飞神与伏神的生克制化关系分析。
    基于《火珠林》《卜筮正宗》伏神得出/不得出规则，
    细化飞神与伏神的五行生克关系及得出难易。

    返回：
        {
            "has_interaction": bool,
            "interactions": [
                {
                    "position": int,
                    "fei_shen": str,       # 飞神六亲
                    "fu_shen": str,        # 伏神名称
                    "relation": str,       # 关系定性
                    "can_emerge": bool,
                    "description": str,
                },
                ...
            ],
            "overall_emerge": bool,
        }
    """
    fu_analysis = result.get("advanced_analysis", {}).get("hidden_spirit_analysis", {})
    if not fu_analysis or not fu_analysis.get("has_hidden_spirit"):
        return {"has_interaction": False}

    details = fu_analysis.get("details", [])
    if not details:
        return {"has_interaction": False}

    interactions = []
    for fu in details:
        covering = fu.get("covering_spirit", {})  # 飞神
        hidden = fu.get("hidden_spirit", {})      # 伏神
        fei_elem = covering.get("element", "")
        fu_elem = hidden.get("element", "")
        can_emerge = fu.get("can_emerge", True)

        if not fei_elem or not fu_elem:
            continue

        # 飞伏关系定性
        if fei_elem == fu_elem:
            relation = "比和"  # 飞伏同类 → 伏得出易
        elif SHENG_CYCLE.get(fei_elem) == fu_elem:
            relation = "飞生伏"  # 飞神生伏神 → 伏神易出，受荫
        elif KE_CYCLE.get(fei_elem) == fu_elem:
            relation = "飞克伏"  # 飞神克伏神 → 伏神难出，受压
        elif SHENG_CYCLE.get(fu_elem) == fei_elem:
            relation = "伏生飞"  # 伏神泄气 → 伏得出但力弱
        else:
            relation = "伏克飞"  # 伏神克飞神 → 伏得出但多阻

        fu_name = hidden.get("six_relation", "伏神")
        fei_name = covering.get("six_relation", "")

        interactions.append({
            "position": hidden.get("position"),
            "fei_shen": fei_name,
            "fu_shen": fu_name,
            "fei_branch": covering.get("branch", ""),
            "fu_branch": hidden.get("branch", ""),
            "relation": relation,
            "can_emerge": can_emerge,
            "description": (
                f"{_pos_to_name(hidden.get('position', 0))}："
                f"飞{fei_name}({fei_elem})与伏{fu_name}({fu_elem})：{relation}，"
                f"{'伏得出' if can_emerge else '伏难出'}"
            ),
        })

    overall_emerge = all(i["can_emerge"] for i in interactions) if interactions else True

    return {
        "has_interaction": True,
        "interactions": interactions,
        "overall_emerge": overall_emerge,
        "summary": "；".join(i["description"] for i in interactions) if interactions else "无伏神",
    }

