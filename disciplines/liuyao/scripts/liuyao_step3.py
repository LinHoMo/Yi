from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ks_ensure, kernel_dir

_ks_ensure(__file__)

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

from chain_tables import (_BRANCH_CLASHES, _BRANCH_CLASH_MAP, _CHART_TAIL,
    _ELEMENT_PEAK_MONTHS, _HE_MAP, _HEXAGRAM_HARMONY_SET, _HEX_NAMES,
    _QUESTION_USE_GOD_BASIS, _QUESTION_USE_GOD_MAP, _USE_GOD_LAYER_CITATIONS,
    HEXAGRAM_LIUCHONG, HEXAGRAM_LIUHE, JUE_MAP, SAN_HE, TRIGRAM_ELEMENT,
    USE_GOD_RELATIONSHIPS, _60_CYCLE_BASE)

from liuyao_narrate import (_build_reasoning_chain,
    _get_hexagram_body_summary_note, find_classical_quotes)

from liuyao_timing import predict_timing_core as _predict_timing

from narrative_rules import strength_reason, strength_polarity

from narrative_utils import (  # noqa: E402
    _branch_element,
    _evaluate_fu_cang_strength,
    _is_chong,
    _is_he,
    _pos_to_name,
    _twelve_growth_at_day,
    CLASSICAL_INTERPRETATIONS as CINTERP,
    element_strength_in_month,
    get_changed_hexagram_branch,
    get_elements_for_relation,
    get_empty_branches,
    get_palace_first_hexagram,
    get_relation_from_element,
    get_twelve_growth_stage,
    note_text,
    safe_get,
    strength_to_score,
    STEP5_CONFIDENCE as CONF_TXT,
    STEP5_FACTOR_REASONS as FREASON,
    STEP5_SPIRIT_REASONS as SPIRIT_TXT,
    STEP5_VERDICT_DESCS as VDESC,
    STEP5_YINGQI as YINGQI_TXT,
    VOID_KIND_LABELS,
    vdesc,
)

# ─── 全局变量 ───
_USE_GOD_RULES: list[dict] | None = None

from liuyao_step2 import _element_to_relation  # 跨文件引用

# ═══ chain_step3.py ═══


def step3_analyze_strength(r: dict) -> dict:
    """
    Step 3: 断旺 — 分析用神旺衰（最关键步骤）。

    使用「旺相休囚死」框架，结合月建、日辰综合判断。

    规则：
    ┌────────┬──────────────────────────────────┐
    │ 状态   │ 条件                              │
    ├────────┼──────────────────────────────────┤
    │ 旺(5)  │ 用神五行 同于 月建五行             │
    │ 相(4)  │ 月建五行 生 用神五行               │
    │ 休(3)  │ 用神五行 生 月建五行               │
    │ 囚(2)  │ 用神五行 克 月建五行               │
    │ 死(1)  │ 月建五行 克 用神五行               │
    └────────┴──────────────────────────────────┘

    日辰修正：
    - 日辰生用神: +1
    - 日辰克用神: -1
    - 日辰同五行: +0.5

    特殊状态：
    - 旬空：有气论70%（旺相+旬空）、休囚论30%（休囚+旬空）
    - 月破：直接降为1（死）
    - 暗动：旺相×0.7, 休囚×0.3
    """
    # 获取分析上下文
    step1_data = safe_get(r, "_step1_data", default={})
    step2_data = safe_get(r, "_step2_data", default={})
    hex_info = safe_get(r, "original_hexagram", default={})
    yao_lines = safe_get(hex_info, "yao_lines", default=[])
    palace_element = safe_get(hex_info, "palace_element", default="")

    # 获取日月建
    div_time = safe_get(r, "divination_time", default={})
    month_stem_branch = safe_get(div_time, "month_stem_branch", default="")
    day_stem_branch = safe_get(div_time, "day_stem_branch", default="")
    month_branch = month_stem_branch[1:] if len(month_stem_branch) >= 2 else ""
    day_branch = day_stem_branch[1:] if len(day_stem_branch) >= 2 else ""
    month_element = _branch_element(month_branch)
    day_element = _branch_element(day_branch)

    # 获取旬空
    empty = safe_get(r, "empty_branches", default=[])

    # 获取用神信息
    # 从 step2 获取，如果没有则临时计算（self-contained）
    selected_use_god = safe_get(step2_data, "selected_use_god", default=None)
    use_god_category = safe_get(step2_data, "use_god_category", default="世爻")
    use_god_element = safe_get(step2_data, "use_god_element", default="")

    # 如果没有step2数据，临时获取用神
    if not selected_use_god:
        if use_god_category == "世爻":
            for yao in yao_lines:
                if yao.get("is_world"):
                    selected_use_god = {
                        "position": yao.get("position"),
                        "name": _pos_to_name(yao.get("position", 0)),
                        "earthly_branch": yao.get("earthly_branch", ""),
                        "element": _branch_element(yao.get("earthly_branch", "")),
                        "is_moving": yao.get("is_moving", False),
                        "is_empty": yao.get("earthly_branch", "") in empty,
                        "is_month_break": yao.get("is_month_break", False),
                    }
                    use_god_element = _branch_element(yao.get("earthly_branch", ""))
                    break

    # 伏藏用神走独立评估分支（旺衰以伏神飞伏关系为主）
    handled, fu_result = resolve_fu_cang_result(
        selected_use_god, step2_data, use_god_category,
        month_branch, day_branch, empty, month_element, day_element,
    )
    if handled:
        return fu_result

    # ---------- 3.1: 用神月建旺衰 ----------
    god_month_strength = element_strength_in_month(use_god_element, month_element)
    god_month_score = strength_to_score(god_month_strength)

    # ---------- 3.2: 用神日辰旺衰 ----------
    god_day_strength = element_strength_in_month(use_god_element, day_element)
    god_day_score = strength_to_score(god_day_strength)

    # ---------- 3.3: 日辰修正 ----------
    day_modifier, day_modifier_reason = compute_day_modifier(day_element, use_god_element)

    # ---------- 3.4: 旬空修正 ----------
    em = compute_empty_modifier(
        selected_use_god, use_god_element, month_element, day_element,
        day_branch, yao_lines, god_month_score,
    )
    is_empty = em["is_empty"]
    empty_modifier = em["empty_modifier"]
    empty_modifier_reason = em["empty_modifier_reason"]
    chu_xun_bonus = em["chu_xun_bonus"]
    chu_xun_reason = em["chu_xun_reason"]
    is_true_void = em["is_true_void"]
    is_false_void = em["is_false_void"]
    void_kind = em["void_kind"]

    # ---------- 3.5: 月破修正 ----------
    mb = compute_month_break_modifier(selected_use_god, day_branch)
    is_month_break = mb["is_month_break"]
    month_break_modifier = mb["month_break_modifier"]
    month_break_modifier_reason = mb["month_break_modifier_reason"]

    # ---------- 3.6: 暗动修正 ----------
    ad = compute_an_dong(selected_use_god, day_branch, god_month_score)
    is_an_dong = ad["is_an_dong"]
    an_dong_modifier = ad["an_dong_modifier"]
    an_dong_modifier_reason = ad["an_dong_modifier_reason"]

    # ---------- 3.7: 十二长生修正 + 3.7b: 绝处逢生 / 绝地无援 ----------
    use_god_branch = selected_use_god.get("earthly_branch", "")
    tg = compute_twelve_growth(use_god_element, day_branch, step2_data)
    twelve_growth = tg["twelve_growth"]
    twelve_growth_modifier = tg["twelve_growth_modifier"]
    twelve_growth_reason = tg["twelve_growth_reason"]
    desperate_relief_from_stage_modifier = tg["desperate_relief_from_stage_modifier"]
    desperate_relief_from_stage_reason = tg["desperate_relief_from_stage_reason"]

    # ---------- 3.8: 综合评分 ----------
    # 基础分：月建为主（权重0.6），日辰为辅（权重0.4）
    base_score = god_month_score * 0.6 + god_day_score * 0.4
    # 加上日辰修正
    adjusted_score = base_score + day_modifier
    # 应用旬空/月破/暗动修正
    effective_score = adjusted_score * empty_modifier * month_break_modifier
    if chu_xun_bonus != 0.0:
        effective_score += chu_xun_bonus
    if is_an_dong:
        effective_score *= an_dong_modifier
    # 加上十二长生修正
    effective_score += twelve_growth_modifier

    # ---------- 3.8b: 绝处逢生修正（来自 advanced_analysis 和步骤 3.7b 绝地检测）----------
    desperate_relief_modifier = 0.0
    desperate_relief_info = None
    # 3.7b: 绝处逢生 / 绝地无援（由 step3 自身识别）
    if desperate_relief_from_stage_modifier != 0.0:
        desperate_relief_modifier += desperate_relief_from_stage_modifier
        effective_score += desperate_relief_from_stage_modifier
    # advanced_analysis: 绝处逢生（由 enhance_reading 预计算）
    advanced = r.get("advanced_analysis") if isinstance(r, dict) else None
    if isinstance(advanced, dict):
        dr = advanced.get("desperate_relief")
        if isinstance(dr, dict) and dr.get("has_desperate_relief"):
            desperate_relief_modifier = dr.get("score_modifier", 0.0)
            desperate_relief_info = dr
            effective_score += desperate_relief_modifier

    # ---------- 3.8c: 随官入墓标记（随官入墓信息，主修正已在 step5 应用）----------
    officer_tomb_ref = None
    if isinstance(advanced, dict):
        ot = advanced.get("officer_tomb")
        if isinstance(ot, dict) and ot.get("has_officer_tomb"):
            officer_tomb_ref = {
                "severity": ot.get("severity", "none"),
                "scenarios": ot.get("scenarios", []),
                "description": ot.get("description", ""),
            }

    # 分数上下限
    effective_score = max(0.5, min(5.0, effective_score))

    # ---------- 3.9: 旺衰定性 ----------
    # 古典规则：用神五行在月建处于"相"位(生月令者)时，即使合分因暗动/刑等被压低，旺衰定性仍应不低于"旺"
    _month_str_for_level = element_strength_in_month(use_god_element, month_element) if use_god_element and month_element else ""
    _xiang_bump = (_month_str_for_level == "相" and effective_score >= 2.5)
    if effective_score >= 4.5:
        strength_level = "极旺"
    elif effective_score >= 3.5:
        strength_level = "旺"
    elif effective_score >= 2.5:
        # "相"位之爻合分在[2.5, 3.5)区间时，定性上调为"旺"而非"中和"
        strength_level = "旺" if _xiang_bump else "中和"
    elif effective_score >= 1.5:
        strength_level = "偏弱"
    elif effective_score >= 0.8:
        strength_level = "弱"
    else:
        strength_level = "极弱"

    # ---------- 3.10b: 暗动检测（全卦静爻） ----------
    # Extract yuan_shen/ji_shen elements from step2_data for hidden movement role check
    yuan_shen_elem = safe_get(step2_data, "yuan_shen", "element", default="")
    ji_shen_elem = safe_get(step2_data, "ji_shen", "element", default="")
    yuan_shen_relation = _element_to_relation(yuan_shen_elem, palace_element) if yuan_shen_elem else ""
    ji_shen_relation = _element_to_relation(ji_shen_elem, palace_element) if ji_shen_elem else ""

    hidden_movement = _detect_hidden_movement(
        day_branch, yao_lines, month_element, day_element
    )
    hidden_movement_modifier = 0.0
    hidden_movement_reason = ""
    if hidden_movement:
        for hm in hidden_movement:
            hm_relation = hm.get("relation", "")
            hm_pos = hm.get("position")
            hm_name = hm.get("name", "")
            hm_branch = hm.get("branch", "")
            hm_weight = hm.get("weight", 0.5)
            # Check if this hidden-moved yao is the use god
            if hm_pos == selected_use_god.get("position"):
                hidden_movement_modifier += 0.3 * hm_weight / 0.7
                hidden_movement_reason += f"用神{hm_name}暗动（{hm_branch}受{day_branch}冲），有动意；"
            elif yuan_shen_relation and hm_relation == yuan_shen_relation:
                hidden_movement_modifier += 0.4 * hm_weight / 0.7
                hidden_movement_reason += f"原神{hm_name}暗动（{hm_branch}受{day_branch}冲），暗中生助用神；"
            elif ji_shen_relation and hm_relation == ji_shen_relation:
                hidden_movement_modifier -= 0.8 * hm_weight / 0.7
                hidden_movement_reason += f"忌神{hm_name}暗动（{hm_branch}受{day_branch}冲），暗中克害；"
            else:
                hidden_movement_reason += f"{hm_name}暗动（{hm_branch}，{hm.get('effect_strength', '中')}），"

        effective_score += hidden_movement_modifier

    # ---------- 3.10c: 三刑修正（来自 advanced_analysis）----------
    # P0-4 修正：三刑只计入"用神自身参与"的刑（branches_present 含用神支）。
    # 卦内其他爻的刑（如无关自刑）属于整体格局，不应扣在用神旺衰分上。
    tp = compute_three_punishment(r, use_god_branch)
    tp_modifier = tp["tp_modifier"]
    tp_modifier_reason = tp["tp_modifier_reason"]
    if tp_modifier != 0.0:
        effective_score += tp_modifier

    # ---------- 3.11: 收集所有修正项 ----------
    modifiers, desperate_relief_description = build_strength_modifiers({
        "day_modifier": day_modifier,
        "day_modifier_reason": day_modifier_reason,
        "chu_xun_bonus": chu_xun_bonus,
        "chu_xun_reason": chu_xun_reason,
        "is_empty": is_empty,
        "empty_modifier": empty_modifier,
        "empty_modifier_reason": empty_modifier_reason,
        "is_month_break": is_month_break,
        "month_break_modifier": month_break_modifier,
        "month_break_modifier_reason": month_break_modifier_reason,
        "is_an_dong": is_an_dong,
        "an_dong_modifier": an_dong_modifier,
        "an_dong_modifier_reason": an_dong_modifier_reason,
        "selected_use_god": selected_use_god,
        "twelve_growth_modifier": twelve_growth_modifier,
        "twelve_growth_reason": twelve_growth_reason,
        "hidden_movement": hidden_movement,
        "hidden_movement_modifier": hidden_movement_modifier,
        "hidden_movement_reason": hidden_movement_reason,
        "tp_modifier": tp_modifier,
        "tp_modifier_reason": tp_modifier_reason,
        "desperate_relief_modifier": desperate_relief_modifier,
        "desperate_relief_info": desperate_relief_info,
        "desperate_relief_from_stage_reason": desperate_relief_from_stage_reason,
    })

    return {
        "use_god_position": selected_use_god.get("position"),
        "use_god_name": selected_use_god.get("name"),
        "use_god_branch": use_god_branch,
        "use_god_element": use_god_element,
        "parent_strength_god": use_god_category,
        "month_element": month_element,
        "day_element": day_element,
        "god_month_strength": god_month_strength,
        "god_month_score": god_month_score,
        "god_day_strength": god_day_strength,
        "god_day_score": god_day_score,
        "day_modifier": day_modifier,
        "day_modifier_reason": day_modifier_reason,
        "is_empty": is_empty,
        "empty_modifier": empty_modifier,
        "empty_modifier_reason": empty_modifier_reason,
        "is_true_void": is_true_void,
        "is_false_void": is_false_void,
        "void_kind": void_kind,
        "is_month_break": is_month_break,
        "month_break_modifier": month_break_modifier,
        "month_break_modifier_reason": month_break_modifier_reason,
        "is_an_dong": is_an_dong,
        "an_dong_modifier": an_dong_modifier if is_an_dong else 1.0,
        "an_dong_modifier_reason": an_dong_modifier_reason,
        "twelve_growth_stage": twelve_growth[0] if twelve_growth else None,
        "twelve_growth_modifier": twelve_growth_modifier,
        "twelve_growth_reason": twelve_growth_reason,
        "base_score": round(base_score, 2),
        "adjusted_score": round(adjusted_score, 2),
        "effective_score": round(effective_score, 2),
        "strength_level": strength_level,
        "modifiers": modifiers,
        "summary_text": _compose_strength_summary(
            use_god_category=use_god_category,
            selected_use_god=selected_use_god,
            use_god_element=use_god_element,
            month_branch=month_branch,
            month_element=month_element,
            god_month_strength=god_month_strength,
            god_month_score=god_month_score,
            day_branch=day_branch,
            day_element=day_element,
            god_day_strength=god_day_strength,
            god_day_score=god_day_score,
            is_empty=is_empty,
            empty_modifier_reason=empty_modifier_reason,
            void_kind=void_kind,
            is_month_break=is_month_break,
            month_break_modifier_reason=month_break_modifier_reason,
            is_an_dong=is_an_dong,
            an_dong_modifier_reason=an_dong_modifier_reason,
            twelve_growth_reason=twelve_growth_reason,
            twelve_growth_modifier=twelve_growth_modifier,
            hidden_movement=hidden_movement,
            hidden_movement_reason=hidden_movement_reason,
            tp_modifier_reason=tp_modifier_reason,
            tp_modifier=tp_modifier,
            desperate_relief_description=desperate_relief_description,
            desperate_relief_modifier=desperate_relief_modifier,
            effective_score=effective_score,
            strength_level=strength_level,
        ),
        "hidden_movement": hidden_movement,
        "hidden_movement_modifier": round(hidden_movement_modifier, 2),
        "hidden_movement_reason": hidden_movement_reason,
        "three_punishment_modifier": round(tp_modifier, 2),
        "three_punishment_reason": tp_modifier_reason,
        "desperate_relief_modifier": round(desperate_relief_modifier, 2),
        "desperate_relief_info": desperate_relief_info,
        "officer_tomb": officer_tomb_ref,
    }


def _combined_strength_for_hm(element: str, month_element: str, day_element: str) -> str:
    """
    综合月建日辰判断旺衰（暗动专用轻量版）。
    返回: "旺", "相", "中和", "偏弱", "衰"
    """
    m = element_strength_in_month(element, month_element)
    d = element_strength_in_month(element, day_element)
    strength_val = {"旺": 5, "相": 4, "休": 3, "囚": 2, "死": 1, "未知": 0}
    total = strength_val.get(m, 0) + strength_val.get(d, 0)

    if total >= 9:
        return "旺"
    elif total >= 7:
        return "相"
    elif total >= 5:
        return "中和"
    elif total >= 3:
        return "偏弱"
    else:
        return "衰"


def _detect_hidden_movement(
    day_branch: str,
    yao_lines: list[dict],
    month_element: str = "",
    day_element: str = "",
) -> list[dict]:
    """
    Detect 暗动 (hidden movement) — static yao that are genuinely clashed by 日辰.

    Rule from 《卜筮正宗》《增删卜易》:
    - 旺相之爻遇日冲 → 暗动（强，~70%明动）
    - 中和之爻遇日冲 → 暗动（中，~40%）
    - 休囚之爻遇日冲 → 暗动（弱，~30%——力微短暂）
    - 月休囚+日冲+衰 → 日破（此爻彻底无用，零效力）

    Only applies to 静爻 (static yao, not marked as moving by 6 or 9).
    日破 yao are excluded from the result (weight=0 = no effect).

    Parameters
    ----------
    day_branch : str
        The day branch (e.g. "子", "午")
    yao_lines : list[dict]
        All 6 yao with their attributes including 'is_moving', 'earthly_branch',
        'six_relation', 'position', 'nature' etc.
    month_element : str
        Five-element value of the month branch (for strength calculation)
    day_element : str
        Five-element value of the day branch (for strength calculation)

    Returns
    -------
    list[dict]
        Each hidden movement record with position, branch, type, source, role, weight.
        日破 yao are excluded (zero effect).
        Empty list if none detected.
    """
    if not day_branch or not yao_lines:
        return []

    # 力量等级 → (label, weight) 映射
    STRENGTH_MAP = {
        "旺": ("暗动(旺相，七分布动)", 0.7, "强"),
        "相": ("暗动(旺相，七分布动)", 0.7, "强"),
        "中和": ("暗动(中和，中力)", 0.4, "中"),
        "偏弱": ("暗动(休囚，三分力)", 0.2, "弱"),
        "衰": ("日破(月休逢冲，此爻无用)", 0.0, "无"),
    }

    hidden_moved = []
    for yao in yao_lines:
        # Skip explicit moving yao (already 明动)
        if yao.get("is_moving") or yao.get("moving"):
            continue
        yao_branch = yao.get("earthly_branch", "") or yao.get("branch", "")
        if not yao_branch:
            continue
        # Check 六冲 relationship: day_branch clashes with yao_branch
        if _BRANCH_CLASHES.get(yao_branch) == day_branch:
            elem = _branch_element(yao_branch)

            # 计算旺衰等级
            if month_element and day_element:
                overall = _combined_strength_for_hm(elem, month_element, day_element)
            else:
                overall = "中和"  # fallback if no month/day info

            label, weight, effect_strength = STRENGTH_MAP.get(
                overall, ("暗动", 0.5, "中")
            )

            # 日破（weight=0）之爻 → 无任何作用 → 完全跳过
            if weight == 0.0:
                continue

            # Determine the role for reporting
            relation = yao.get("six_relation", "")
            role = relation if relation else "静爻"
            hidden_moved.append({
                "position": yao.get("position"),
                "name": _pos_to_name(yao.get("position", 0)),
                "branch": yao_branch,
                "element": elem,
                "relation": role,
                "type": label,
                "effect_strength": effect_strength,
                "source": "日冲",
                "weight": weight,
            })

    return hidden_moved


def _compose_strength_summary(**kw) -> str:
    """旺衰步骤：叙述体，分数只作括号备查。"""
    ug = kw.get("use_god_category") or "用神"
    name = (kw.get("selected_use_god") or {}).get("name") or ""
    elem = kw.get("use_god_element") or ""
    mb, me = kw.get("month_branch") or "", kw.get("month_element") or ""
    ms, msc = kw.get("god_month_strength") or "", kw.get("god_month_score")
    db, de = kw.get("day_branch") or "", kw.get("day_element") or ""
    ds, dsc = kw.get("god_day_strength") or "", kw.get("god_day_score")
    level = kw.get("strength_level") or ""
    score = kw.get("effective_score")
    parts = [f"{ug}在{name}，五行{elem}。"]
    parts.append(f"月建{mb}（{me}）对它{ms}，日辰{db}（{de}）对它{ds}。")
    extras = []
    if kw.get("is_empty"):
        _vk = str(kw.get("void_kind") or "")
        _vlabel = VOID_KIND_LABELS.get(_vk) or {}
        if _vlabel.get("strength_text"):
            extras.append(_vlabel["strength_text"].format(
                month=kw.get("month_branch", ""), day=kw.get("day_branch", "")))
        elif kw.get("empty_modifier_reason"):
            extras.append(str(kw["empty_modifier_reason"]).rstrip("，。"))
    if kw.get("is_month_break") and kw.get("month_break_modifier_reason"):
        extras.append(str(kw["month_break_modifier_reason"]).rstrip("，。"))
    if kw.get("is_an_dong") and kw.get("an_dong_modifier_reason"):
        extras.append(str(kw["an_dong_modifier_reason"]).rstrip("，。"))
    if kw.get("twelve_growth_modifier") and kw.get("twelve_growth_reason"):
        extras.append(str(kw["twelve_growth_reason"]).rstrip("，。"))
    if kw.get("hidden_movement") and kw.get("hidden_movement_reason"):
        extras.append(str(kw["hidden_movement_reason"]).rstrip("，。"))
    if kw.get("tp_modifier") and kw.get("tp_modifier_reason"):
        extras.append(str(kw["tp_modifier_reason"]).rstrip("，。"))
    if kw.get("desperate_relief_modifier") and kw.get("desperate_relief_description"):
        extras.append(str(kw["desperate_relief_description"]).rstrip("，。"))
    if extras:
        parts.append("另外要留意：" + "；".join(extras) + "。")
    # 口语结论
    lv = str(level)
    say = {
        "极旺": "总起来说，用神很有底气。",
        "旺": "总起来说，用神得力。",
        "相": "总起来说，用神有根，能用。",
        "中和": "总起来说，用神不强不弱，看后手怎么走。",
        "中和偏旺": "总起来说，用神略占上风。",
        "中和偏弱": "总起来说，用神稍显吃力。",
        "偏弱": "总起来说，用神偏软，宜借力。",
        "弱": "总起来说，用神力量薄，不宜硬催结果。",
        "极弱": "总起来说，用神几乎使不上劲。",
        "休囚": "总起来说，用神处在低潮。",
    }.get(lv, f"总起来说，用神状态为{lv}。")
    parts.append(say)
    if score is not None:
        parts.append(f"（量化参考 {float(score):.2f} · {lv}）")
    return "".join(parts)


# ═══ chain_step3_strength.py ═══


def resolve_fu_cang_result(
    selected_use_god,
    step2_data: dict,
    use_god_category: str,
    month_branch: str,
    day_branch: str,
    empty: list,
    month_element: str,
    day_element: str,
) -> tuple:
    """伏藏用神的早退分支。返回 (handled, result)；handled=False 时 result 为 None。"""
    if not (not selected_use_god or selected_use_god.get("is_fu_cang")):
        return False, None

    # 伏藏用神特殊评估（用神伏藏时，旺衰以伏神飞伏关系为主）
    if step2_data.get("has_fu_cang"):
        fu_detail = step2_data.get("fu_cang_detail", {})
        fu_score = _evaluate_fu_cang_strength(fu_detail, month_branch, day_branch, empty)

        # 构建伏神对应的基本信息
        fu_results = fu_detail.get("results", [])
        fu_entry = fu_results[0] if fu_results else {}
        fu_shen_info = fu_entry.get("fu_shen", {})
        fei_shen_info = fu_entry.get("fei_shen") or {}
        can_emerge_val = fu_entry.get("can_emerge", True)

        return True, {
            "use_god_position": fu_shen_info.get("position"),
            "use_god_name": fu_shen_info.get("name", ""),
            "use_god_branch": fu_shen_info.get("branch", ""),
            "use_god_element": fu_shen_info.get("element", ""),
            "parent_strength_god": use_god_category,
            "month_element": month_element,
            "day_element": day_element,
            "god_month_strength": element_strength_in_month(
                fu_shen_info.get("element", ""), month_element
            ) if fu_shen_info.get("element") else "未知",
            "god_month_score": strength_to_score(
                element_strength_in_month(fu_shen_info.get("element", ""), month_element)
            ) if fu_shen_info.get("element") else 0,
            "god_day_strength": element_strength_in_month(
                fu_shen_info.get("element", ""), day_element
            ) if fu_shen_info.get("element") else "未知",
            "god_day_score": strength_to_score(
                element_strength_in_month(fu_shen_info.get("element", ""), day_element)
            ) if fu_shen_info.get("element") else 0,
            "is_empty": fu_shen_info.get("branch", "") in empty,
            "is_month_break": False,
            "is_an_dong": False,
            "twelve_growth_stage": _twelve_growth_at_day(
                fu_shen_info.get("element", ""), day_branch
            ),
            "base_score": fu_score["score"],
            "adjusted_score": fu_score["score"],
            "effective_score": fu_score["score"],
            "strength_level": fu_score["level"],
            "modifiers": [{
                "type": "伏藏飞伏关系",
                "value": fu_score["score"],
                "reason": fu_score["analysis"],
            }],
            "summary_text": fu_score["analysis"],
            "has_fu_cang": True,
            "fu_cang_detail": fu_detail,
            "can_emerge": can_emerge_val,
            "fu_cang_analysis": fu_score["analysis"],
            "hidden_movement": [],
            "hidden_movement_modifier": 0.0,
            "hidden_movement_reason": "",
        }
    return True, {"error": "无法定位用神"}


def compute_day_modifier(day_element: str, use_god_element: str) -> tuple:
    """3.3 日辰修正：同气/生/泄/克/制。"""
    day_modifier = 0.0
    day_modifier_reason = ""
    if day_element == use_god_element:
        day_modifier = 0.5
        day_modifier_reason = "日辰与用神同气（同性相助）"
    elif SHENG_CYCLE.get(day_element) == use_god_element:
        day_modifier = 1.0
        day_modifier_reason = "日辰生用神"
    elif SHENG_CYCLE.get(use_god_element) == day_element:
        day_modifier = -1.0
        day_modifier_reason = "用神生日辰（泄气）"
    elif KE_CYCLE.get(day_element) == use_god_element:
        day_modifier = -1.0
        day_modifier_reason = "日辰克用神（克伤）"
    elif KE_CYCLE.get(use_god_element) == day_element:
        day_modifier = 0.5
        day_modifier_reason = "用神克日辰（制日）"
    return day_modifier, day_modifier_reason


def _births(branch_or_element: str, use_god_element: str) -> bool:
    """该支（或五行）是否生用神五行。空/未知一律 False。"""
    if not branch_or_element or not use_god_element:
        return False
    elem = BRANCH_ELEMENTS.get(branch_or_element, branch_or_element)
    return SHENG_CYCLE.get(elem) == use_god_element


def _branch_ke(branch_or_element: str, use_god_element: str) -> bool:
    """该支（或五行）是否克用神五行（日克用神）。"""
    if not branch_or_element or not use_god_element:
        return False
    elem = BRANCH_ELEMENTS.get(branch_or_element, branch_or_element)
    return KE_CYCLE.get(elem) == use_god_element


def compute_empty_modifier(
    selected_use_god: dict,
    use_god_element: str,
    month_element: str,
    day_element: str,
    day_branch: str,
    yao_lines: list,
    god_month_score: float,
) -> dict:
    """3.4 旬空修正：有气论 70% / 休囚论 30%，并判出旬有验加成。

    旺衰权重之外另出「真空 / 假空」标签，口径见 data/rules/verdict_texts.json
    #pattern_verdict_labels（逐字原文见 references/pattern_reference.md 格局十三）：
      假空＝旬空 + 旺相（月建或日辰临旺相）+ 有生扶（月生／日生／动爻生），或日辰冲实；
      真空＝旬空 + 月建休囚 + 日辰克用 + 无任何生扶（既无生扶又受日克，终难起）。
    两者互斥；既非假空又不构成真空者，只标旬空、不给真空/假空断语（宁缺勿滥）。
    """
    is_empty = selected_use_god.get("is_empty", False)
    empty_modifier = 1.0
    empty_modifier_reason = ""
    chu_xun_bonus = 0.0
    chu_xun_reason = ""
    is_false_void = False
    is_true_void = False
    void_kind = ""
    if is_empty:
        # 有生源检测（月建/日辰/动爻生用神 → 空亡有气，出旬有验）
        month_births_use = _births(month_element, use_god_element)
        day_births_use = _births(day_element, use_god_element)
        # 动爻生用神 → "动则生而不为空"（《增删易》动空出旬）
        moving_births_use = False
        for yao in yao_lines:
            if yao.get("is_moving"):
                y_elem = _branch_element(yao.get("earthly_branch", ""))
                if SHENG_CYCLE.get(y_elem) == use_god_element:
                    moving_births_use = True
                    break
        # 月建/日辰的旺相（"相"亦为旺，见旺相休囚死：生月令者为相）
        month_prosperous = element_strength_in_month(use_god_element, month_element) in ("旺", "相")
        day_prosperous = element_strength_in_month(use_god_element, day_element) in ("旺", "相")
        month_weak = element_strength_in_month(use_god_element, month_element) in ("休", "囚", "死")
        _ugb = (selected_use_god or {}).get("earthly_branch", "")
        # 日辰冲用神 → 旬空逢冲为填实（《卜筮正宗》冲空则实）：空而逢冲不作空论
        day_clashes_use = bool(day_branch) and bool(_ugb) and _is_chong(_ugb, day_branch)
        births = month_births_use or day_births_use or moving_births_use

        # 假空：旺相待出——旺相或有生扶，皆非真亡
        if month_prosperous or day_prosperous or births or day_clashes_use:
            is_false_void = True
            void_kind = "false"
        # 真空：休囚难起——月建休囚、日辰克用、又无一生扶
        elif month_weak and _branch_ke(day_element, use_god_element) and not births:
            is_true_void = True
            void_kind = "true"
        # 旺衰权重（口径未变，保持既有读数可比）
        void_label = VOID_KIND_LABELS.get(void_kind, {})
        if god_month_score >= 4 or moving_births_use:
            empty_modifier = 0.7  # 有气论
            if moving_births_use:
                empty_modifier_reason = "用神旬空但得动爻生之（动空），出旬即应，论70%"
            else:
                empty_modifier_reason = "用神旺相旬空，论70%（有气空亡，出空可应）"
            if day_clashes_use:
                empty_modifier_reason = "用神旺相旬空，逢日辰冲为填实（冲空则实，出空即应），论70%"
            if births:
                chu_xun_bonus = 1.0
                chu_xun_reason = "用神旬空有气且得生扶（月/日/动爻），出旬有验，断吉倾向"
            if is_false_void and void_label.get("reason"):
                empty_modifier_reason = void_label["reason"]
        else:
            empty_modifier = 0.3  # 休囚论
            empty_modifier_reason = void_label.get("reason") or "用神休囚旬空，论30%（真空亡，难应）"
    return {
        "is_empty": is_empty,
        "empty_modifier": empty_modifier,
        "empty_modifier_reason": empty_modifier_reason,
        "chu_xun_bonus": chu_xun_bonus,
        "chu_xun_reason": chu_xun_reason,
        # 真空/假空标签（《增删卜易》"旺空待出，真空难起"）
        "is_true_void": is_true_void,
        "is_false_void": is_false_void,
        "void_kind": void_kind,
    }


def compute_month_break_modifier(selected_use_god: dict, day_branch: str) -> dict:
    """3.5 月破修正：月破逢日合可救（0.5），无救近失效（0.3）。"""
    is_month_break = selected_use_god.get("is_month_break", False)
    month_break_modifier = 1.0
    month_break_modifier_reason = ""
    if is_month_break:
        # 月破日合可救
        if _is_he(selected_use_god.get("earthly_branch", ""), day_branch):
            month_break_modifier = 0.5  # 有救
            month_break_modifier_reason = "月破逢日合，可救"
        else:
            month_break_modifier = 0.3  # 几乎失效
            month_break_modifier_reason = "月破且无救，力量近乎消亡"
    return {
        "is_month_break": is_month_break,
        "month_break_modifier": month_break_modifier,
        "month_break_modifier_reason": month_break_modifier_reason,
    }


def compute_an_dong(selected_use_god: dict, day_branch: str, god_month_score: float) -> dict:
    """3.6 暗动修正：旺相受日冲为暗动（0.7），休囚受日冲为日破（0.3）。"""
    is_an_dong = False
    an_dong_modifier = 1.0
    an_dong_modifier_reason = ""
    # 暗定义：旺相之爻受日冲
    if not selected_use_god.get("is_moving", False):  # 不是动爻才是暗动
        if _is_chong(selected_use_god.get("earthly_branch", ""), day_branch):
            if god_month_score >= 4:  # 旺相受日冲为暗动
                is_an_dong = True
                an_dong_modifier = 0.7
                an_dong_modifier_reason = "旺爻受日冲为暗动，有动意而力稍逊"
            else:  # 休囚受日冲为日破
                is_an_dong = False
                an_dong_modifier = 0.3
                an_dong_modifier_reason = "休囚之爻受日冲为日破，无力"
    return {
        "is_an_dong": is_an_dong,
        "an_dong_modifier": an_dong_modifier,
        "an_dong_modifier_reason": an_dong_modifier_reason,
    }


def compute_twelve_growth(use_god_element: str, day_branch: str, step2_data: dict) -> dict:
    """3.7 十二长生修正 + 3.7b 绝处逢生 / 绝地无援。

    注意：原实现中 3.7b 依赖 3.7 块内解包出的 stage_name（twelve_growth 为真时才有），
    两节必须同进同出，切分后由本函数一并返回。
    """
    twelve_growth = get_twelve_growth_stage(use_god_element, day_branch)
    twelve_growth_modifier = 0.0
    twelve_growth_reason = ""
    desperate_relief_from_stage_modifier = 0.0
    desperate_relief_from_stage_reason = ""
    if twelve_growth:
        stage_name, stage_idx = twelve_growth
        if stage_name == "帝旺":
            twelve_growth_modifier = 0.5
            twelve_growth_reason = "用神临帝旺，极盛之象"
        elif stage_name in ("临官", "长生"):
            twelve_growth_modifier = 0.3
            twelve_growth_reason = f"用神临{stage_name}，得气之象"
        elif stage_name in ("墓", "绝", "死"):
            twelve_growth_modifier = -1.0
            twelve_growth_reason = f"用神临{stage_name}，入{stage_name}之地，力微"
        elif stage_name in ("沐浴",):
            twelve_growth_modifier = -0.3
            twelve_growth_reason = f"用神临{stage_name}，初生而气弱"

        # ---------- 3.7b: 绝处逢生 / 绝地无援 ----------
        # 用神临绝地（十二长生"绝"位）：原神发动来生 → 绝处逢生（凶中反吉）；无原神救援 → 绝地无援（额外减分）
        if stage_name == "绝":
            yuan_shen_positions_for_desperate = safe_get(step2_data, "yuan_shen", "positions", default=[])
            has_yuan_rescue = any(p.get("is_moving", False) for p in (yuan_shen_positions_for_desperate or []))
            if has_yuan_rescue:
                desperate_relief_from_stage_modifier = 1.0
                desperate_relief_from_stage_reason = "绝处逢生：用神虽临绝地，原神发动来生，凶中反吉"
            else:
                desperate_relief_from_stage_modifier = -1.0
                desperate_relief_from_stage_reason = "绝地无援：用神临绝地，原神不动/无救援，险上加险"

    return {
        "twelve_growth": twelve_growth,
        "twelve_growth_modifier": twelve_growth_modifier,
        "twelve_growth_reason": twelve_growth_reason,
        "desperate_relief_from_stage_modifier": desperate_relief_from_stage_modifier,
        "desperate_relief_from_stage_reason": desperate_relief_from_stage_reason,
    }


def compute_three_punishment(r: dict, use_god_branch: str) -> dict:
    """3.10c 三刑修正。

    P0-4 修正：三刑只计入"用神自身参与"的刑（branches_present 含用神支）。
    卦内其他爻的刑（如无关自刑）属于整体格局，不应扣在用神旺衰分上。
    """
    tp_modifier = 0.0
    tp_issues = []
    advanced_for_tp = r.get("advanced_analysis", {})
    if advanced_for_tp and isinstance(advanced_for_tp, dict):
        tp_data = advanced_for_tp.get("three_punishments", {})
        if isinstance(tp_data, dict) and tp_data.get("has_punishment"):
            # 优先使用已乘倍数后的 total_score（classical_analysis 内部对多刑叠加用了1.5x/2.0x）
            total_tp = tp_data.get("total_score", None)
            if total_tp is not None and total_tp < 0:
                tp_modifier = total_tp
            else:
                for p in tp_data.get("punishments", []):
                    bp = p.get("branches_present", [])
                    if use_god_branch and use_god_branch not in bp:
                        continue
                    tp_modifier += p.get("score", 0.0)
            # 描述仍加所有已成立的刑
            for p in tp_data.get("punishments", []):
                comp = p.get("completeness", "")
                ptype = p.get("type", "")
                if comp == "待刑":
                    missing = p.get("missing", [])
                    tp_issues.append(f"{ptype}待刑(缺{','.join(missing)})")
                elif comp == "完整":
                    tp_issues.append(f"{ptype}(完整三刑)")
                elif comp == "成刑":
                    tp_issues.append(f"{ptype}(成刑)")
                elif comp == "催刑":
                    tp_issues.append(f"{ptype}(催刑)")
                else:
                    tp_issues.append(ptype)
    tp_modifier_reason = "、".join(tp_issues) if tp_issues else ""
    return {"tp_modifier": tp_modifier, "tp_modifier_reason": tp_modifier_reason}


def build_strength_modifiers(m: dict) -> tuple:
    """3.11 收集所有修正项。返回 (modifiers, desperate_relief_description)。"""
    day_modifier = m.get("day_modifier", 0.0)
    day_modifier_reason = m.get("day_modifier_reason", "")
    chu_xun_bonus = m.get("chu_xun_bonus", 0.0)
    chu_xun_reason = m.get("chu_xun_reason", "")
    is_empty = m.get("is_empty", False)
    empty_modifier = m.get("empty_modifier", 1.0)
    empty_modifier_reason = m.get("empty_modifier_reason", "")
    is_month_break = m.get("is_month_break", False)
    month_break_modifier = m.get("month_break_modifier", 1.0)
    month_break_modifier_reason = m.get("month_break_modifier_reason", "")
    is_an_dong = m.get("is_an_dong", False)
    an_dong_modifier = m.get("an_dong_modifier", 1.0)
    an_dong_modifier_reason = m.get("an_dong_modifier_reason", "")
    selected_use_god = m.get("selected_use_god") or {}
    twelve_growth_modifier = m.get("twelve_growth_modifier", 0.0)
    twelve_growth_reason = m.get("twelve_growth_reason", "")
    hidden_movement = m.get("hidden_movement")
    hidden_movement_modifier = m.get("hidden_movement_modifier", 0.0)
    hidden_movement_reason = m.get("hidden_movement_reason", "")
    tp_modifier = m.get("tp_modifier", 0.0)
    tp_modifier_reason = m.get("tp_modifier_reason", "")
    desperate_relief_modifier = m.get("desperate_relief_modifier", 0.0)
    desperate_relief_info = m.get("desperate_relief_info")
    desperate_relief_from_stage_reason = m.get("desperate_relief_from_stage_reason", "")

    modifiers = []
    desperate_relief_description = ""
    if day_modifier != 0:
        modifiers.append({"type": "日辰", "value": day_modifier, "reason": day_modifier_reason})
    if chu_xun_bonus != 0.0:
        modifiers.append({"type": "出旬有验", "value": chu_xun_bonus, "reason": chu_xun_reason})
    if is_empty:
        modifiers.append({"type": "旬空", "value": empty_modifier, "reason": empty_modifier_reason})
    if is_month_break:
        modifiers.append({"type": "月破", "value": month_break_modifier, "reason": month_break_modifier_reason})
    if is_an_dong:
        modifiers.append({"type": "暗动", "value": an_dong_modifier, "reason": an_dong_modifier_reason})
    elif an_dong_modifier_reason and not selected_use_god.get("is_moving", False):
        modifiers.append({"type": "日破", "value": an_dong_modifier, "reason": an_dong_modifier_reason})
    if twelve_growth_modifier != 0:
        modifiers.append({
            "type": "十二长生",
            "value": twelve_growth_modifier,
            "reason": twelve_growth_reason,
        })
    if hidden_movement:
        modifiers.append({
            "type": "暗动",
            "value": hidden_movement_modifier,
            "reason": hidden_movement_reason,
            "details": hidden_movement,
        })
    if tp_modifier != 0.0:
        modifiers.append({
            "type": "三刑",
            "value": tp_modifier,
            "reason": tp_modifier_reason,
        })

    # ---------- 绝处逢生修正项 ----------
    if desperate_relief_modifier != 0.0 and (desperate_relief_info or desperate_relief_from_stage_reason):
        dr_reason = ""
        # 优先使用 step3 自身识别的绝地状态描述
        if desperate_relief_from_stage_reason:
            dr_reason = desperate_relief_from_stage_reason
        else:
            dr_reason = desperate_relief_info.get("description", "") if desperate_relief_info else ""
            if not dr_reason and desperate_relief_info:
                dr_reason = desperate_relief_info.get("verdict", "")
        modifiers.append({
            "type": "绝处逢生" if desperate_relief_modifier > 0 else "绝地无援",
            "value": desperate_relief_modifier,
            "reason": dr_reason,
        })
        desperate_relief_description = dr_reason

    return modifiers, desperate_relief_description



__all__ = [
    "step3_analyze_strength",
    "_combined_strength_for_hm",
    "_detect_hidden_movement",
    "_compose_strength_summary",
    "resolve_fu_cang_result",
    "compute_day_modifier",
    "compute_empty_modifier",
    "compute_month_break_modifier",
    "compute_an_dong",
    "compute_twelve_growth",
    "compute_three_punishment",
    "build_strength_modifiers",
]
