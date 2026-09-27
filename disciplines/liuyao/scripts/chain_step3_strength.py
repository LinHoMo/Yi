# -*- coding: utf-8 -*-
"""六爻 step3 旺衰：各修正项的计算与修正项清单组装（自 chain_step3.step3_analyze_strength 切出）。

纯搬移不改写逻辑：每个函数对应原函数中的一节（3.4 旬空 / 3.5 月破 / 3.6 暗动 /
3.7 十二长生 / 3.7b 绝处逢生 / 3.10c 三刑 / 3.11 修正项清单 / 伏藏早退分支）。

本模块**不 import chain_step3**，依赖单向：chain_step3 → chain_step3_strength。
（_detect_hidden_movement 与 _compose_strength_summary 仍在 chain_step3 原地，
因为 thinking_chain.py 从 chain_step3 再导出这两个名字。）

验收口径：拆分前后 step3 输出与下游叙述必须逐例一致（零指纹漂移）。
"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    KE_CYCLE,
    SHENG_CYCLE,
)

from chain_support import (  # noqa: E402
    _branch_element,
    _evaluate_fu_cang_strength,
    _is_chong,
    _is_he,
    _twelve_growth_at_day,
    element_strength_in_month,
    get_twelve_growth_stage,
    safe_get,
    strength_to_score,
)


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


def compute_empty_modifier(
    selected_use_god: dict,
    use_god_element: str,
    month_element: str,
    day_element: str,
    day_branch: str,
    yao_lines: list,
    god_month_score: float,
) -> dict:
    """3.4 旬空修正：有气论 70% / 休囚论 30%，并判出旬有验加成。"""
    is_empty = selected_use_god.get("is_empty", False)
    empty_modifier = 1.0
    empty_modifier_reason = ""
    chu_xun_bonus = 0.0
    chu_xun_reason = ""
    if is_empty:
        # 有生源检测（月建/日辰/动爻生用神 → 空亡有气，出旬有验）
        month_births_use = SHENG_CYCLE.get(month_element) == use_god_element
        day_births_use = SHENG_CYCLE.get(day_element) == use_god_element
        # 动爻生用神 → "动则生而不为空"（《增删易》动空出旬）
        moving_births_use = False
        for yao in yao_lines:
            if yao.get("is_moving"):
                y_elem = _branch_element(yao.get("earthly_branch", ""))
                if SHENG_CYCLE.get(y_elem) == use_god_element:
                    moving_births_use = True
                    break
        if god_month_score >= 4 or moving_births_use:
            empty_modifier = 0.7  # 有气论
            if moving_births_use:
                empty_modifier_reason = "用神旬空但得动爻生之（动空），出旬即应，论70%"
            else:
                empty_modifier_reason = "用神旺相旬空，论70%（有气空亡，出空可应）"
            # 日辰冲用神 → 旬空逢冲为填实（《卜筮正宗》冲空则实）
            _ugb = (selected_use_god or {}).get("earthly_branch", "")
            day_clashes_use = bool(day_branch) and bool(_ugb) and _is_chong(_ugb, day_branch)
            if day_clashes_use:
                empty_modifier_reason = "用神旺相旬空，逢日辰冲为填实（冲空则实，出空即应），论70%"
            if month_births_use or day_births_use or moving_births_use:
                chu_xun_bonus = 1.0
                chu_xun_reason = "用神旬空有气且得生扶（月/日/动爻），出旬有验，断吉倾向"
        else:
            empty_modifier = 0.3  # 休囚论
            empty_modifier_reason = "用神休囚旬空，论30%（真空亡，难应）"
    return {
        "is_empty": is_empty,
        "empty_modifier": empty_modifier,
        "empty_modifier_reason": empty_modifier_reason,
        "chu_xun_bonus": chu_xun_bonus,
        "chu_xun_reason": chu_xun_reason,
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
