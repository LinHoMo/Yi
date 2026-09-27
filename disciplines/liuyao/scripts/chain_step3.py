# -*- coding: utf-8 -*-
"""六爻思维链：基元表 / 断语库 / 通用辅助 / 五步推演 / 应期 / 叙事组装。（拆分自 thinking_chain.py，纯搬移不改逻辑；聚合入口见 thinking_chain.py）。"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

from chain_step2 import _element_to_relation
from chain_support import _branch_element, _pos_to_name, element_strength_in_month, safe_get, strength_to_score
from chain_tables import _BRANCH_CLASHES
from chain_step3_strength import (  # noqa: E402  step3 各修正项（本文件只管编排与聚合）
    build_strength_modifiers,
    compute_an_dong,
    compute_day_modifier,
    compute_empty_modifier,
    compute_month_break_modifier,
    compute_three_punishment,
    compute_twelve_growth,
    resolve_fu_cang_result,
)

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
    if kw.get("is_empty") and kw.get("empty_modifier_reason"):
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

