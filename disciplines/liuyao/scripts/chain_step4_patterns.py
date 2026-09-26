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

from chain_step2 import _element_to_relation
from chain_support import _branch_element, _is_chong, _is_he, _pos_to_name, get_changed_hexagram_branch, get_relation_from_element, safe_get
from chain_tables import JUE_MAP, _HEXAGRAM_HARMONY_SET


def _detect_classical_illness_pattern(question: str, step2_data: dict, step3_data: dict,
                                       empty_branches: list, step4_data: dict = None,
                                       hex_result: dict = None) -> dict:
    """
    古籍经典疾厄格局识别 —《增删卜易》《卜筮正宗》之核心断法。

    特殊疾厄格局优先于一般旺衰规则：
    - 近病逢空即愈：用神旬空，速愈之象
    - 近病逢合为凶：用神被日/月/动爻合住，病难退
    - 近病逢冲即愈：用神被冲，病气散
    - 近病六冲卦速愈
    - 久病逢空/冲/合为凶
    """
    result = {"pattern": None, "description": "", "impact_on_verdict": "", "score_adjustment": 0.0}

    q = question or ""
    is_near_illness = any(kw in q for kw in ["近病", "即愈", "何日愈"])
    is_chronic_illness = any(kw in q for kw in ["久病", "沉疴", "久疾"])
    is_illness_div = any(kw in q for kw in ["病", "疾", "症"]) and ("愈" in q or "吉凶" in q or "死" in q)

    if not (is_near_illness or is_chronic_illness or is_illness_div):
        return result

    # 获取用神信息
    use_god = step2_data.get("selected_use_god") or {}
    use_god_branch = use_god.get("earthly_branch", "")
    if not use_god_branch:
        # fallback: check use_god_yao_lines
        ug_lines = step2_data.get("use_god_yao_lines") or step2_data.get("use_god_positions") or []
        if ug_lines and isinstance(ug_lines, list):
            first = ug_lines[0]
            if isinstance(first, dict):
                use_god_branch = first.get("earthly_branch", "")

    # 化空检测：从 step3 或 step4 的动爻信息中获取
    transform_to_void = False
    void_branch_hit = ""

    # 优先从 step4_data.details 获取动爻化空（标准数据源）
    if not transform_to_void and step4_data:
        s4_details = step4_data.get("details") or step4_data.get("moving_details") or []
        for m in (s4_details if isinstance(s4_details, list) else []):
            if isinstance(m, dict):
                target = (m.get("changed_branch", "") or m.get("target_earthly_branch", "")
                         or m.get("to_branch", "") or m.get("transformed_branch", ""))
                if target and target in empty_branches:
                    transform_to_void = True
                    void_branch_hit = target
                    break

    # fallback: 检查 step3_data 中的 moving_analysis / dong_analysis / moving_details
    if not transform_to_void and step3_data:
        dong_analysis = (step3_data.get("dong_analysis") or step3_data.get("moving_analysis")
                         or step3_data.get("moving_details") or [])
        for m in (dong_analysis if isinstance(dong_analysis, list) else []):
            if isinstance(m, dict):
                target = (m.get("target_earthly_branch", "") or m.get("to_branch", "")
                          or m.get("changed_branch", "") or m.get("transformed_branch", ""))
                if target and target in empty_branches:
                    transform_to_void = True
                    void_branch_hit = target
                    break

    # --- 近病逢合为凶（优先于逢空：合则病气难退，《卜筮正宗》"近病逢合为凶"）---
    # 仅限用神为静爻时——动爻逢合为"合起"（合而发动），不构成合绊；
    # 静爻逢合方为"合绊"（病气难退）。
    use_god_moving = use_god.get("is_moving", False) or any(
        yl.get("is_moving") for yl in
        (step2_data.get("use_god_yao_lines") or step2_data.get("use_god_positions") or [])
        if isinstance(yl, dict) and yl.get("earthly_branch") == use_god_branch
    )
    if (is_near_illness or is_illness_div) and use_god_branch and not use_god_moving:
        dt6 = hex_result.get("divination_time", {}) or {}
        m_b = (dt6.get("month_stem_branch", "") or "")[1:]
        d_b = (dt6.get("day_stem_branch", "") or "")[1:]
        HE6 = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
               "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
        he_bys = []
        if HE6.get(use_god_branch, "") == m_b:
            he_bys.append(f"月建{m_b}")
        if HE6.get(use_god_branch, "") == d_b:
            he_bys.append(f"日辰{d_b}")
        if he_bys:
            result["pattern"] = "近病逢合为凶"
            result["description"] = f"用神{use_god_branch}为{'、'.join(he_bys)}所合——近病逢合，病气难退（《卜筮正宗》定法）"
            result["impact_on_verdict"] = "用神被合，病气难退，凶"
            result["score_adjustment"] = -5.5
            return result

    # --- 近病逢空即愈 ---
    if (is_near_illness or is_illness_div):
        use_void = use_god_branch and use_god_branch in empty_branches
        if use_void or transform_to_void:
            void_desc = f"用神{use_god_branch}旬空" if use_void else f"用神化空（动爻化{void_branch_hit}旬空）"
            result["pattern"] = "近病逢空即愈"
            result["description"] = f"{void_desc}——近病逢空为病气将退，速愈之象（《增删易》定法）"
            result["impact_on_verdict"] = "近病逢空即愈，强调为吉"
            result["score_adjustment"] = 5.0
            return result

        # 近病运交any void branch → also 逢空象
        yao_lines = step2_data.get("use_god_yao_lines") or step2_data.get("use_god_positions") or []
        if yao_lines:
            for yl in yao_lines:
                if isinstance(yl, dict) and yl.get("earthly_branch", "") in empty_branches:
                    result["pattern"] = "近病逢空即愈"
                    result["description"] = f"用神{yl['earthly_branch']}临旬空——近病逢空即愈"
                    result["impact_on_verdict"] = "近病逢空为速愈象"
                    result["score_adjustment"] = 5.0
                    return result

    # --- 近病逢合为凶 ---
    if (is_near_illness or is_illness_div) and step3_data:
        combine_info = step3_data.get("combine_info") or {}
        if combine_info.get("is_combined"):
            combined_by = combine_info.get("combined_by", [])
            if combined_by:
                result["pattern"] = "近病逢合为凶"
                result["description"] = f"用神逢合（{'、'.join(str(x) for x in combined_by)}），近病逢合，病气难退（《增删易》定法）"
                result["impact_on_verdict"] = "近病逢合为凶之经典格局"
                result["score_adjustment"] = -3.5
                return result

        # Also check: 用神被日月生合为凶
        div_time = step3_data.get("divination_info", {})
        if not div_time:
            # Try hex_result (passed separately)
            pass
        # Check if use god is combined by day or month
        day_combine = step3_data.get("day_combine", "")
        month_combine = step3_data.get("month_combine", "")
        if day_combine or month_combine:
            combine_source = "]".join(filter(None, [f"日辰{day_combine}" if day_combine else "", f"月建{month_combine}" if month_combine else ""]))
            result["pattern"] = "近病逢合为凶"
            result["description"] = f"用神为{combine_source}所合——近病逢合为凶（《卜筮正宗》定法）"
            result["impact_on_verdict"] = "用神被合，病气难退，凶"
            result["score_adjustment"] = -3.5
            return result

    # --- 久病逢空/冲为凶 ---
    if is_chronic_illness:
        if use_god_branch and use_god_branch in empty_branches:
            result["pattern"] = "久病逢空为凶"
            result["description"] = f"久病用神{use_god_branch}逢空，久病逢空为危"
            result["impact_on_verdict"] = "久病逢空为脱象，凶"
            result["score_adjustment"] = -4.5
            return result

    return result



def _detect_hexagram_harmony_clash_pattern(question: str, hex_result: dict, step4_data: dict) -> dict:
    """
    六合/六冲交互格局识别 — 冲中逢合可解，合处逢冲则散。

    - 冲中逢合可解：六冲卦中却有日辰/动爻合世爻或应爻，冲散可解为吉
    - 合处逢冲则散：六合卦中却有日辰/月建冲世爻或应爻，合处逢冲为凶
    """
    result = {"pattern": None, "description": "", "impact_on_verdict": "", "score_adjustment": 0.0}

    q = question or ""
    hex_name = hex_result.get("original_hexagram", {}).get("name", "")
    if not hex_name:
        return result

    # 六合卦列表
    HEX_HEXAGRAMS = {"否", "屯", "豫", "贲", "鼎", "萃", "丰", "恒", "损", "同人", "节", "履",
                     "临", "家人", "中孚", "涣", "离", "咸", "泰", "大畜", "需", "大有", "夬",
                     "姤", "小过", "既济", "益", "蛊", "困", "旅", "噬嗑", "归妹"}
    # 六冲卦列表
    HEX_CLASH_HEXAGRAMS = {"乾", "坤", "坎", "离", "震", "巽", "艮", "兑",
                           "无妄", "同人", "遁", "大壮", "豫", "观", "晋", "萃",
                           "大有", "夬", "姤", "解", "归妹", "旅", "涣", "节", "中孚", "小过"}

    # Check for 六合/六冲 in hexagram name using advanced analysis
    hex_advanced = hex_result.get("advanced_analysis", {}) or {}
    hex_type = hex_advanced.get("hexagram_type", "")

    is_he = "六合" in hex_type or hex_name in ("否", "泰", "恒", "益", "萃", "咸", "损", "同人", "贲", "鼎", "随", "节", "中孚", "既济", "家人", "蛊", "困", "豫", "临", "小畜", "履", "涣", "离", "丰")
    is_chong = "六冲" in hex_type or hex_name in ("乾", "坤", "坎", "离", "震", "巽", "艮", "兑", "无妄", "大壮", "遁", "晋", "萃", "夬", "姤", "解", "归妹", "旅", "涣", "小过")

    # Empty branches (for checking if world/response is void)
    empty = hex_result.get("empty_branches", [])

    # --- 冲中逢合可解 ---
    if is_chong:
        div_time = hex_result.get("divination_time", {}) or {}
        month_branch = (div_time.get("month_stem_branch", "") or "")[1:]
        day_branch = (div_time.get("day_stem_branch", "") or "")[1:]
        # 世应爻地支（从爻标志取，original_hexagram 无 world_position 字段）
        yao_lines = hex_result.get("original_hexagram", {}).get("yao_lines", [])
        world_branch = ""
        response_branch = ""
        for y in yao_lines:
            if y.get("is_world"):
                world_branch = y.get("earthly_branch", "")
            if y.get("is_response"):
                response_branch = y.get("earthly_branch", "")
        # 六合：子丑 寅亥 卯戌 辰酉 巳申 午未
        HE_MAP = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
                  "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
        world_he = world_branch and (HE_MAP.get(world_branch, "") in [month_branch, day_branch])
        response_he = response_branch and (HE_MAP.get(response_branch, "") in [month_branch, day_branch])
        # 动爻化合（化出之爻与月日成合，或化出之爻生合用神）方可解冲
        details = step4_data.get("details", []) if step4_data else []
        def _is_helpful_he(d):
            if "化合" not in d.get("change_type", "") and "六合" not in d.get("change_type", ""):
                return False
            chg_branch = d.get("changed_branch", "")
            # 化出之支与日月成合 → 解冲
            if chg_branch and HE_MAP.get(chg_branch, "") in [month_branch, day_branch]:
                return True
            return False
        moving_he = any(_is_helpful_he(d) for d in details)

        if world_he or response_he or moving_he:
            he_target = "世爻" if world_he else ("应爻" if response_he else "动爻")
            result["pattern"] = "冲中逢合可解"
            result["description"] = f"六冲本主散，然月日/动爻合{he_target}（{'世' if world_he else ''}{'应' if response_he else ''}），冲中逢合可解"
            result["impact_on_verdict"] = "冲处逢合可解冲散，转危为安"
            result["score_adjustment"] = 2.5
            return result

        # 六冲无合解 → 事散之象（合伙/婚姻/出行/交易/官讼/谋事类；近病六冲速愈除外）
        SCATTER_KEYWORDS = ["合伙", "合作", "婚姻", "婚", "出行", "外出", "交易", "买卖",
                            "生意", "官讼", "官司", "求财", "谋事", "开店", "签约", "合同"]
        if any(k in q for k in SCATTER_KEYWORDS):
            result["pattern"] = "六冲主散"
            result["description"] = f"六冲卦主散，{hex_name}卦世应相冲，事难成合"
            result["impact_on_verdict"] = "六冲事散，合伙/婚恋/出行/交易类不利"
            result["score_adjustment"] = -2.0
            return result

    # --- 合处逢冲则散 ---
    if is_he:
        div_time = hex_result.get("divination_time", {}) or {}
        month_branch = (div_time.get("month_stem_branch", "") or "")[1:]
        day_branch = (div_time.get("day_stem_branch", "") or "")[1:]
        world_branch = ""
        response_branch = ""

        yao_lines = hex_result.get("original_hexagram", {}).get("yao_lines", [])
        for y in yao_lines:
            if y.get("is_world"):
                world_branch = y.get("earthly_branch", "")
            if y.get("is_response"):
                response_branch = y.get("earthly_branch", "")

        # Check if world/response is being clashed by month or day
        CLASH_MAP = {"子": "午", "午": "子", "卯": "酉", "酉": "卯",
                     "寅": "申", "申": "寅", "巳": "亥", "亥": "巳",
                     "辰": "戌", "戌": "辰", "丑": "未", "未": "丑"}
        world_clashed = world_branch and CLASH_MAP.get(world_branch, "") in [month_branch, day_branch]
        response_clashed = response_branch and CLASH_MAP.get(response_branch, "") in [month_branch, day_branch]

        if (world_clashed or response_clashed):
            SCATTER2 = ["婚姻", "婚", "占婚", "合伙", "合作", "出行", "外出", "交易", "买卖",
                        "生意", "官讼", "官司", "求财", "谋事", "开店", "签约", "合同"]
            if any(k in q for k in SCATTER2):
                result["pattern"] = "合处逢冲则散"
                result["description"] = f"六合本利事成，然{'世爻' if world_clashed else '应爻'}逢冲，合处逢冲则散"
                result["impact_on_verdict"] = "婚姻六合不可解冲，先成后散；散事类同"
                result["score_adjustment"] = -2.0
                return result

    return result



def _detect_special_pattern(step3_data: dict, step2_data: dict, step4_data: dict, hex_result: dict) -> dict:
    """
    特殊格局识别 — 当标准旺相休囚死规则被逆转时触发。

    检测四种高级格局：
    1. 从格 (Following Pattern) — 用神极弱，顺势从强
    2. 专旺格 (Dominant Element) — 一气独旺
    3. 两神成象格 — 两元素各据一方
    4. 化格 (Transformation) — 三合化气

    Parameters
    ----------
    step3_data : dict
        Step3 断旺结果（含 effective_score 等）
    step2_data : dict
        Step2 定用结果（含 用神五行、原神/忌神 等）
    step4_data : dict
        Step4 察变结果（含 moving_analysis 等）
    hex_result : dict
        完整卦象结果（含 original_hexagram, advanced_analysis 等）

    Returns
    -------
    dict
        {
            "pattern": None | "从格" | "专旺格" | "两神成象" | "化格",
            "description": str,
            "impact_on_verdict": str,
            "rule_applied": str,
            "score_adjustment": float,  # 对 final_score 的调整量
        }
    """
    # --- 优先检查古籍经典格局（这些格局优先于从格等高级格局） ---
    question = hex_result.get("question", "")
    empty_branches = hex_result.get("empty_branches", [])

    # 疾厄格局（近病逢空/逢合/逢冲）— 传入 step4_data 以增强动爻化空检测
    illness_pattern = _detect_classical_illness_pattern(question, step2_data, step3_data, empty_branches, step4_data=step4_data, hex_result=hex_result)
    if illness_pattern["pattern"]:
        return illness_pattern

    # 六合/六冲交互格局（冲中逢合/合处逢冲）
    harmony_clash_pattern = _detect_hexagram_harmony_clash_pattern(question, hex_result, step4_data)
    if harmony_clash_pattern["pattern"]:
        # 六冲主散 + 合伙类问题 + 用神旺 → 追加减分（用神虽旺但合伙难持久）
        if (harmony_clash_pattern.get("pattern") == "六冲主散"
                and ("合伙" in question)):
            try:
                ug_score_s5 = float(step3_data.get("effective_score", 2.5))
            except (TypeError, ValueError):
                ug_score_s5 = 2.5
            if ug_score_s5 >= 3.5:
                harmony_clash_pattern["score_adjustment"] -= 0.5
                harmony_clash_pattern["description"] += "（用神虽旺，合伙六冲终难持久）"
                harmony_clash_pattern["impact_on_verdict"] = (
                    (harmony_clash_pattern.get("impact_on_verdict") or "")
                    + "——用神虽旺而合伙难持久，额外减分"
                )
        return harmony_clash_pattern

    use_god_score = step3_data.get("effective_score", 2.5)
    hex_info = hex_result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    # Normalize score to float
    try:
        use_god_score = float(use_god_score)
    except (TypeError, ValueError):
        use_god_score = 2.5

    # ── Count elements in hexagram ──
    elem_counts: dict[str, int] = {}
    for yao in yao_lines:
        elem = yao.get("element", "")
        if not elem:
            branch = yao.get("earthly_branch", "")
            elem = _branch_element(branch)
        if elem:
            elem_counts[elem] = elem_counts.get(elem, 0) + 1

    # ── Check 1: 从格 (Following Pattern) ──
    # Condition: 用神极弱(<-1.0), 原神无援(<1.5), 忌神极旺(>3.5) or absent,
    #            all moving lines trend toward 忌神, NO 冲中逢合救应
    # ⚠️ 从格为极端罕见格局，必须严格判定，避免误判正常弱卦
    if use_god_score < -1.0:
        yuan_shen = step2_data.get("yuan_shen", {}) or {}
        ji_shen = step2_data.get("ji_shen", {}) or {}
        yuan_positions = yuan_shen.get("positions", []) or []
        ji_positions = ji_shen.get("positions", []) or []

        # 原神评估：无位置或位置少则视为无援
        yuan_shen_weak = len(yuan_positions) == 0
        if not yuan_shen_weak and yuan_positions:
            # Check if yuan_shen has any moving line support
            yuan_moving = [p for p in yuan_positions if p.get("is_moving")]
            yuan_shen_weak = len(yuan_moving) == 0 and len(yuan_positions) <= 1

        # 忌神评估：有多个位置视为极旺
        ji_shen_strong = len(ji_positions) >= 2

        # 若有"冲中逢合"、"化合"等明显救应模式，不从格
        step4_details = step4_data.get("details", []) if step4_data else []
        has_rescue = False
        for m in step4_details:
            ct = m.get("change_type", "")
            if ct in ("化合", "六合", "三合", "化进神"):
                has_rescue = True
                break
        if has_rescue:
            pass  # skip 从格
        elif ji_shen_strong and yuan_shen_weak:
            return {
                "pattern": "从格",
                "description": f"用神极弱（{use_god_score:.2f}）原神无援，忌神独旺（{len(ji_positions)}位），顺势从之",
                "impact_on_verdict": "反转标准判断——本应判凶反为吉，用神弃命从强",
                "rule_applied": "《增删易》'弱极反旺，从格为用'",
                "score_adjustment": 3.0,
            }

    # ── Check 1b: 原神绝位·用神失源 (绝处逢生反断为凶) ──
    # 条件：用神偏弱(score<2.0) + 原神不现或极弱(无实际爻位) + 无动变救援 → 大凶
    # 区别于从格：不反转方向(不加分)，而是强化凶断(减分)
    # 《增删易》"绝处逢生反断为凶"：原神无援→用神气绝→断凶不疑
    if use_god_score < 2.0:
        yuan_shen2 = step2_data.get("yuan_shen", {}) or {}
        yuan_positions2 = yuan_shen2.get("positions", []) or []
        yuan_fucang2 = yuan_shen2.get("fu_cang", None)
        # 原神不现：完全无位置，或仅有伏藏(飞神下的隐藏原神)
        _yuan_absent = len(yuan_positions2) == 0
        # 无动变内生救援(step4无正面力量)
        step4_details2 = step4_data.get("details", []) if step4_data else []
        _has_positive_change = any(
            isinstance(m, dict) and m.get("effect_score", 0) > 0.3
            for m in step4_details2
        )
        net_effect2 = step4_data.get("net_effect", 0) if step4_data else 0
        # 触发条件：原神完全不现 + 用神偏弱 + 无动变正面效应 + net_effect不显著正
        if _yuan_absent and not _has_positive_change and (isinstance(net_effect2, (int, float)) and net_effect2 <= 0.1):
            return {
                "pattern": "原神绝位·用神失源",
                "description": f"用神弱（{use_god_score:.2f}）原神不现（仅伏藏或无援），绝处逢生反断为凶",
                "impact_on_verdict": "原神气绝不能生用，用神孤立无援→大凶",
                "rule_applied": "《增删易》'原神无援，用神气绝，断凶不疑'",
                "score_adjustment": -2.0,
            }

    # ── Check 2: 专旺格 (Dominant Element Pattern) ──
    # Condition: one element >= 4 of 6 yao, score >= 4.0
    if elem_counts:
        max_elem = max(elem_counts, key=elem_counts.get)
        max_count = elem_counts[max_elem]
        if max_count >= 4:
            return {
                "pattern": "专旺格",
                "description": f"{max_elem}气独旺（{max_count}/6爻）",
                "impact_on_verdict": "喜顺泄不宜克逆——用神属此元素大吉，他元素不振无碍",
                "rule_applied": "《卜筮正宗》'专旺喜泄不喜克'",
                "score_adjustment": 0.0,  # 不直接加分，而是降低忌神惩罚
            }

    # ── Check 3: 两神成象格 (Two Element Coexistence) ──
    # Condition: exactly 2 elements, each ~3 yao, no major 相克 in moving lines
    if len(elem_counts) == 2:
        elems = list(elem_counts.keys())
        if abs(elem_counts[elems[0]] - elem_counts[elems[1]]) <= 1:
            # Check no major attacking in moving lines
            has_major_attack = False
            for m in moving_analysis:
                ct = m.get("change_type", "")
                if ct in ("回头克", "化墓", "化绝"):
                    has_major_attack = True
                    break
            if not has_major_attack:
                return {
                    "pattern": "两神成象",
                    "description": f"{elems[0]}（{elem_counts[elems[0]]}）与{elems[1]}（{elem_counts[elems[1]]}）各据一方，势均力敌",
                    "impact_on_verdict": "视用神所在方之旺衰定吉凶——用神方旺则吉",
                    "rule_applied": "《增删易》'两象平衡以用神方取'",
                    "score_adjustment": 0.0,
                }

    # ── Check 4: 化格 (Transformation Pattern) ──
    # Condition: 用神本身的动爻参与三合化才算真正化格
    # ⚠️ 化格是极端罕见格局，普通三合但不涉及用神动爻时不触发
    advanced = hex_result.get("advanced_analysis", {})
    if advanced and isinstance(advanced, dict):
        tc_data = advanced.get("triple_combo", {})
        if isinstance(tc_data, dict) and tc_data.get("has_triple_combo"):
            use_god_elem = step2_data.get("use_god_element", "土")
            # 获取用神动爻位置列表（用神发动才算化）
            use_god_moving_positions = set()
            for d in (step4_data.get("details") or step4_data.get("moving_details") or []):
                if isinstance(d, dict):
                    d_pos = d.get("position") or d.get("from_position") or 0
                    d_rel = d.get("change_type", "")
                    if d_pos and d_rel and "化合" not in d_rel and "六合" not in d_rel:
                        # 检查这条动爻是否是用神
                        d_orig_branch = d.get("original_branch", d.get("from_branch", ""))
                        if d_orig_branch:
                            d_orig_elem = _branch_element(d_orig_branch)
                            if d_orig_elem == use_god_elem:
                                use_god_moving_positions.add(d_pos)
            details = tc_data.get("details", []) or []
            for combo in details:
                target_elem = combo.get("element", "")
                positions = combo.get("positions", []) or []
                if target_elem and target_elem != use_god_elem:
                    # 严格条件: 用神动爻本身在三合中，且化出非用神元素
                    involved = use_god_moving_positions & set(positions or [])
                    if involved:
                        return {
                            "pattern": "化格",
                            "description": f"三合化{target_elem}，用神动爻{involved}随局而化",
                            "impact_on_verdict": f"用神随三合化{target_elem}，+0.5",
                            "rule_applied": "三合化气，用神发动随局而变",
                            "score_adjustment": +0.5,
                        }

    # ── No special pattern ──
    return {
        "pattern": None,
        "description": "无特殊格局，按常规断法",
        "impact_on_verdict": "无调整",
        "rule_applied": "常规旺衰断法",
        "score_adjustment": 0.0,
    }



def _forms_hexagram_harmony(branch1: str, branch2: str) -> bool:
    """Check if two branches form 六合."""
    if not branch1 or not branch2:
        return False
    key = f"{branch1}{branch2}"
    return key in _HEXAGRAM_HARMONY_SET



def _check_greedy_harmony(
    yao_lines: list[dict],
    moving_lines: list[dict],
    day_branch: str,
    month_branch: str,
    use_god_category: str,
    yuan_shen_element: str,
    ji_shen_element: str,
    palace_element: str,
) -> tuple[float, list[dict]]:
    """
    贪合忘生克检测 — rule from 《增删易》.

    When a yao forms 六合 with another yao or with 日辰/月建, it becomes "贪合" —
    obsessed with the conjunction. This causes:
    - 原神贪合忘生 → the 原神 fails to generate its 用神
    - 忌神贪合忘克 → the 忌神 fails to attack its 用神 (beneficial)

    Parameters
    ----------
    yao_lines : list[dict]
        All 6 yao lines.
    moving_lines : list[dict]
        Subset of yao_lines that are moving (动爻 or 暗动).
    day_branch : str
        Day branch.
    month_branch : str
        Month branch.
    use_god_category : str
        The use god relation (e.g. "妻财", "官鬼").
    yuan_shen_element : str
        Element of the 原神.
    ji_shen_element : str
        Element of the 忌神.
    palace_element : str
        Element of the palace.

    Returns
    -------
    tuple[float, list[dict]]
        (score_adjustment, issues_list). Positive = beneficial, negative = harmful.
        Empty list if no issues found.
    """
    if not moving_lines:
        return 0.0, []

    issues = []
    score_adjustment = 0.0
    yuan_shen_relation_name = _element_to_relation(yuan_shen_element, palace_element) if yuan_shen_element else ""
    ji_shen_relation_name = _element_to_relation(ji_shen_element, palace_element) if ji_shen_element else ""

    for yao in moving_lines:
        pos = yao.get("position", 0)
        orig_branch = yao.get("earthly_branch", "") or yao.get("branch", "")
        orig_relation = yao.get("six_relation", "")
        orig_element = _branch_element(orig_branch) if orig_branch else ""
        changed_branch = yao.get("changed_branch", "")

        # Determine the branch to check for harmony:
        # Use the original branch if static/hidden-moved, or changed branch if moving
        branches_to_check = [orig_branch]
        if changed_branch:
            branches_to_check.append(changed_branch)

        for target_branch in branches_to_check:
            if not target_branch:
                continue

            # Check 合 with 日辰
            if _forms_hexagram_harmony(target_branch, day_branch):
                # Classify by role
                if orig_relation == yuan_shen_relation_name or orig_element == yuan_shen_element:
                    # 原神贪合忘生 → harmful:原神 can't generate use god
                    effect_score = -0.3
                    reason = f"原神{orig_relation}（{_pos_to_name(pos)}爻·{orig_branch}）与{day_branch}日六合，贪合忘生用神"
                    issues.append({
                        "type": "原神贪合忘生",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"日辰{day_branch}",
                        "effect": "原神贪合，暂不能生用神（减力）",
                        "benefit_or_loss": "unfavorable",
                        "score_effect": effect_score,
                    })
                    score_adjustment += effect_score

                elif orig_relation == ji_shen_relation_name or orig_element == ji_shen_element:
                    # 忌神贪合忘克 → beneficial:忌神 can't attack use god
                    effect_score = 0.2
                    reason = f"忌神{orig_relation}（{_pos_to_name(pos)}爻·{orig_branch}）与{day_branch}日六合，贪合忘克用神"
                    issues.append({
                        "type": "忌神贪合忘克",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"日辰{day_branch}",
                        "effect": "忌神贪合，暂不克用神（减凶）",
                        "benefit_or_loss": "favorable",
                        "score_effect": effect_score,
                    })
                    score_adjustment += effect_score

                elif orig_relation == use_god_category:
                    # 用神本身被合 → 合绊，暂受阻滞
                    effect_score = -0.2
                    reason = f"用神（{_pos_to_name(pos)}爻·{orig_branch}）与{day_branch}日六合，合绊暂滞"
                    issues.append({
                        "type": "用神被合",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"日辰{day_branch}",
                        "effect": "用神被合绊，暂受阻滞",
                        "benefit_or_loss": "neutral",
                        "score_effect": effect_score,
                    })
                    score_adjustment += effect_score
                else:
                    # Other lines harmonized with day
                    issues.append({
                        "type": "合绊",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"日辰{day_branch}",
                        "effect": f"{orig_relation}{_pos_to_name(pos)}爻与日合绊",
                        "benefit_or_loss": "neutral",
                        "score_effect": 0.0,
                    })

            # Check 合 with 月建
            if month_branch and _forms_hexagram_harmony(target_branch, month_branch):
                if orig_relation == yuan_shen_relation_name or orig_element == yuan_shen_element:
                    effect_score = -0.2
                    reason = f"原神{orig_relation}（{_pos_to_name(pos)}爻·{orig_branch}）与{month_branch}月六合，贪合忘生"
                    issues.append({
                        "type": "原神贪合忘生",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"月建{month_branch}",
                        "effect": "原神与月合绊，暂不能生用神",
                        "benefit_or_loss": "unfavorable",
                        "score_effect": effect_score,
                    })
                    score_adjustment += effect_score

                elif orig_relation == ji_shen_relation_name or orig_element == ji_shen_element:
                    effect_score = 0.15
                    reason = f"忌神{orig_relation}（{_pos_to_name(pos)}爻·{orig_branch}）与{month_branch}月六合，贪合忘克"
                    issues.append({
                        "type": "忌神贪合忘克",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"月建{month_branch}",
                        "effect": "忌神与月合绊，暂不克用神（减凶）",
                        "benefit_or_loss": "favorable",
                        "score_effect": effect_score,
                    })
                    score_adjustment += effect_score
                else:
                    issues.append({
                        "type": "合绊",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"月建{month_branch}",
                        "effect": f"{orig_relation}{_pos_to_name(pos)}爻与月合绊",
                        "benefit_or_loss": "neutral",
                        "score_effect": 0.0,
                    })

    return round(score_adjustment, 2), issues

