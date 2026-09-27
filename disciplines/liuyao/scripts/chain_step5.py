# -*- coding: utf-8 -*-
"""六爻思维链：基元表 / 断语库 / 通用辅助 / 五步推演 / 应期 / 叙事组装。（拆分自 thinking_chain.py，纯搬移不改逻辑；聚合入口见 thinking_chain.py）。"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

from datetime import datetime

from chain_narrate import _build_reasoning_chain, _get_hexagram_body_summary_note, find_classical_quotes
from chain_step4 import _detect_special_pattern
from chain_support import safe_get
from chain_tables import HEXAGRAM_LIUCHONG, HEXAGRAM_LIUHE
from chain_verdicts import (
    STEP5_FACTOR_REASONS as FREASON,
    vdesc,
)

def step5_synthesize(r: dict) -> dict:
    """
    Step 5: 综合判断 — 综合所有前序分析给出最终结论。

    这是最终判断步骤。此前四步的输出都汇聚于此。

    评分规则（加权）：
    1. 用神旺衰分（来自 step3）作为基础分
    2. 加上动变效应分（来自 step4）
    3. 应用卦体调候：六合卦+0.5，六冲卦-0.5
    4. 辅助神煞调整
    5. 得最终分数 → 定性判断

    最终判断区间：
    - 分数 > 4.0：大吉
    - 3.0-4.0：吉（小吉-吉）
    - 2.0-3.0：平吉/小吉
    - 1.0-2.0：平/小凶
    - 分数 < 1.0：凶

    预测置信度：
    - 信号清晰（旺+原神动）→ 高（>80%）
    - 信号混合 → 中（50-80%）
    - 信号矛盾 → 低（<50%），建议谨慎

    应期判断：
    - 逢值：用神临值日
    - 逢冲：用神逢冲日
    - 出空：旬空出旬
    - 旺则速应（当月/当日），衰则待时

    各加减分项与断语覆写规则按职责外置到 chain_step5_adjust（纯搬移，逻辑未改）。
    """
    # 获取前序步骤数据
    step3_data = safe_get(r, "_step3_data", default={})
    step4_data = safe_get(r, "_step4_data", default={})
    step2_data = safe_get(r, "_step2_data", default={})
    step1_data = safe_get(r, "_step1_data", default={})

    hex_info = safe_get(r, "original_hexagram", default={})
    div_time = safe_get(r, "divination_time", default={})
    day_stem_branch = safe_get(div_time, "day_stem_branch", default="")
    day_branch = day_stem_branch[1:] if len(day_stem_branch) >= 2 else ""

    # ---------- 5.1: 基础分（用神旺衰） ----------
    base_score = safe_get(step3_data, "effective_score", default=2.5)
    strength_level = safe_get(step3_data, "strength_level", default="中和")

    # ---------- 5.2: 动变效应加成 ----------
    change_net_effect = safe_get(step4_data, "net_effect", default=0.0)

    # ---------- 5.3: 卦体调候 ----------
    hex_name = safe_get(step1_data, "hexagram_name", default="")
    palace = safe_get(step1_data, "palace", default="")

    hex_adjustment = 0.0
    hex_adjustment_reason = ""

    # 六合卦检查（上下卦各爻对应六合）
    if hex_name in HEXAGRAM_LIUHE:
        hex_adjustment += 0.5
        hex_adjustment_reason = FREASON["hex_liuhe_reason"]["text"]

    # 六冲卦检查
    if hex_name in HEXAGRAM_LIUCHONG:
        hex_adjustment -= 0.5
        hex_adjustment_reason = FREASON["hex_liuchong_reason"]["text"]

    # ---------- 5.4: 六神辅助调整（协纪辨方书—六兽分阴阳日）----------
    spirit_adjustment, spirit_adjustment_reasons = compute_spirit_adjustment(
        step3_data, hex_info, day_stem_branch,
    )

    # ---------- 5.5: 暗动加分/贪合忘生克修正 ----------
    # Hidden movement modifier from step3 (already applied to effective_score,
    # but we track it explicitly here for transparency)
    hm_modifier = safe_get(step3_data, "hidden_movement_modifier", default=0.0)
    hm_reason = safe_get(step3_data, "hidden_movement_reason", default="")
    hm_count = len(safe_get(step3_data, "hidden_movement", default=[]))

    # Greedy harmony score from step4 (already included in net_effect)
    greedy_score = safe_get(step4_data, "greedy_harmony_score", default=0.0)
    greedy_issues = safe_get(step4_data, "greedy_harmony_issues", default=[]) or []
    greedy_reason_parts = [
        i["effect"] for i in greedy_issues
        if i.get("score_effect", 0) != 0
    ]
    greedy_reason = ("、".join(greedy_reason_parts)) if greedy_reason_parts else ""

    # ---------- 5.5c: 三刑减分（来自 step3 已计入 effective_score，此处仅记录展示） ----------
    tp_score = safe_get(step3_data, "three_punishment_modifier", default=0.0)
    tp_reason = safe_get(step3_data, "three_punishment_reason", default="")

    # ---------- 5.5d–5.5c2: 高级象（日月合 / 六破 / 随官入墓 / 三合破局 / 原神贪合忘生） ----------
    adv = compute_advanced_adjustments(r, step2_data, step3_data, div_time)
    dmb_adjustment = adv["dmb_adjustment"]
    dmb_reason = adv["dmb_reason"]
    sb_adjustment = adv["sb_adjustment"]
    sb_reason = adv["sb_reason"]
    officer_tomb_adjustment = adv["officer_tomb_adjustment"]
    officer_tomb_reason = adv["officer_tomb_reason"]
    officer_tomb_severity = adv["officer_tomb_severity"]
    officer_tomb_verdict_override = adv["officer_tomb_verdict_override"]
    officer_tomb_description = adv["officer_tomb_description"]
    combo_break_adjustment = adv["combo_break_adjustment"]
    combo_break_reason = adv["combo_break_reason"]
    yuan_shen_bond_adjustment = adv["yuan_shen_bond_adjustment"]
    yuan_shen_bond_reason = adv["yuan_shen_bond_reason"]

    # 纳音（5.11）仍要从 advanced_analysis 取，故此处保留原取值
    advanced = r.get("advanced_analysis", {})

    # ---------- 5.5b: 特殊格局识别 ----------
    special_pattern = _detect_special_pattern(step3_data, step2_data, step4_data, r)
    pattern_adjustment = special_pattern.get("score_adjustment", 0.0)
    # For 从格: reverse the verdict direction by capping the negative and boosting
    if special_pattern.get("pattern") == "从格":
        # 从格 reverses the verdict: a weak use-god is actually good
        pattern_verdict_note = f"【从格特殊断法】{special_pattern['description']}——{special_pattern['impact_on_verdict']}"
    elif special_pattern.get("pattern"):
        pattern_verdict_note = f"格局【{special_pattern['pattern']}】：{special_pattern['description']}——{special_pattern['impact_on_verdict']}"
    else:
        pattern_verdict_note = ""

    # ---------- 伏神格局调整 ----------
    fu_shen_adjustment, fu_shen_note = compute_fu_shen_adjustment(step3_data, r)

    # ---------- 5.5h: 古籍通用格局加减（holdout 暴露的系统性缺口） ----------
    cl = compute_classical_adjustment(
        r, step1_data, step2_data, step3_data, special_pattern, pattern_verdict_note,
    )
    classical_adj = cl["classical_adj"]
    classical_notes = cl["classical_notes"]
    pattern_verdict_note = cl["pattern_verdict_note"]
    ctx = cl["ctx"]

    # ---------- 5.5i: 三刑+六合吉凶相战覆写 ----------
    # 当2+成刑/催刑 present 且 六合卦时，吉凶相战 — verdict 上限不超过平凶
    xing_he_conflict_override = detect_xing_he_conflict(step3_data, r, hex_name)

    # ---------- 5.6: 综合评分 ----------
    # 病药（《增删卜易》有病取药）：结构化 illness/medicine 只做有界加减，
    # 吉凶主判仍在旺衰/动变/格局；星煞不进主分（仅 narrate 旁参）。
    bing_yao_adjustment, bing_yao_reasons = compute_bing_yao_adjustment(step2_data, step3_data)
    if bing_yao_adjustment:
        classical_notes.append(f"病药：{'；'.join(bing_yao_reasons)}")

    final_score = (base_score + change_net_effect + hex_adjustment
                   + spirit_adjustment + pattern_adjustment
                   + dmb_adjustment + sb_adjustment
                   + combo_break_adjustment
                   + yuan_shen_bond_adjustment
                   + officer_tomb_adjustment
                   + fu_shen_adjustment
                   + bing_yao_adjustment
                   + classical_adj)
    final_score = round(final_score, 2)

    # ---------- 5.7: 定性判断 ----------
    # 阈值说明：古籍六爻 verdict 应明确(吉/凶)为主，避免过度收歛于中性(平吉/平凶)
    # 校准标准：final_score > 1.0 → 吉; > 4.0 → 大吉; -0.8 ~ 1.0 → 平吉; -2.0 ~ -0.8 → 凶; < -2.0 → 大凶
    if final_score > 4.0:
        verdict = "大吉"
        verdict_desc = vdesc("score_daji")
    elif final_score >= 1.0:
        verdict = "吉"
        verdict_desc = vdesc("score_ji")
    elif final_score >= -0.5:
        verdict = "平吉"
        verdict_desc = vdesc("score_ping_ji")
    elif final_score >= -2.0:
        verdict = "凶"
        verdict_desc = vdesc("score_xiong")
    else:
        verdict = "大凶"
        verdict_desc = vdesc("score_da_xiong")

    # ---------- 5.7 覆写链：强凶格局 / 从吉格局 / 随官入墓 ----------
    ov = apply_verdict_overrides(
        verdict, verdict_desc, final_score,
        r=r,
        step3_data=step3_data,
        step4_data=step4_data,
        special_pattern=special_pattern,
        classical_notes=classical_notes,
        ctx=ctx,
        xing_he_conflict_override=xing_he_conflict_override,
        officer_tomb={
            "verdict_override": officer_tomb_verdict_override,
            "severity": officer_tomb_severity,
            "description": officer_tomb_description,
            "reason": officer_tomb_reason,
            "adjustment": officer_tomb_adjustment,
        },
    )
    verdict = ov["verdict"]
    verdict_desc = ov["verdict_desc"]
    final_score = ov["final_score"]
    # 最终锁定：若强凶格局已触发，不再允许 verdict 被后续逻辑回退到 吉/平吉
    _verdict_locked = ov["fired"]
    officer_tomb_verdict_note = ov["officer_tomb_verdict_note"]

    # ---------- 5.8: 置信度评估 ----------
    confidence = _assess_confidence(step3_data, step4_data, final_score, strength_level)

    # ---------- 5.9: 应期判断 ----------
    timing = _predict_timing(r, step3_data, step1_data, day_branch, special_pattern=special_pattern)

    # ---------- 5.9b: 应期精确日期计算 ----------
    # Use divination date as base for scanning forward
    div_dt = safe_get(r, "divination_time", "datetime", default="")
    base_date = None
    if div_dt:
        try:
            base_date = datetime.strptime(div_dt, "%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            pass
    yingqi_dates = calculate_yingqi(
        step1_data, step2_data, step3_data, step4_data,
        {"verdict": verdict, "final_score": final_score},
        base_date=base_date,
    )

    # ---------- 5.10: 推理链 ----------
    reasoning_chain = _build_reasoning_chain(step1_data, step2_data, step3_data, step4_data, step5_data={
        "verdict": verdict,
        "final_score": final_score,
    }, context=r)

    # ---------- 5.11: 纳音信息（六十甲子纳音取象）----------
    nayin_info = {}
    nayin_desc = ""
    if isinstance(advanced, dict):
        nayin_info = advanced.get("nayin", {})
    if isinstance(nayin_info, dict) and nayin_info.get("description"):
        nayin_desc = nayin_info["description"]

    # ---------- 5.12: 经典引文自动检索 ----------
    classical_quotes = find_classical_quotes(r)
    classical_quotes_text = ""
    if classical_quotes:
        classical_quotes_text = "【经典引文】" + "".join(
            f"• {q['source']}：{q['quote']}" for q in classical_quotes
        )

    # ---------- 5.13: 可解释性因子贡献（SHAP 风格）----------
    factor_contributions = build_factor_contributions({
        "base_score": base_score,
        "change_net_effect": change_net_effect,
        "hex_adjustment": hex_adjustment,
        "hex_adjustment_reason": hex_adjustment_reason,
        "spirit_adjustment": spirit_adjustment,
        "spirit_adjustment_reasons": spirit_adjustment_reasons,
        "dmb_adjustment": dmb_adjustment,
        "dmb_reason": dmb_reason,
        "sb_adjustment": sb_adjustment,
        "sb_reason": sb_reason,
        "combo_break_adjustment": combo_break_adjustment,
        "combo_break_reason": combo_break_reason,
        "yuan_shen_bond_adjustment": yuan_shen_bond_adjustment,
        "yuan_shen_bond_reason": yuan_shen_bond_reason,
        "officer_tomb_adjustment": officer_tomb_adjustment,
        "officer_tomb_reason": officer_tomb_reason,
        "fu_shen_adjustment": fu_shen_adjustment,
        "fu_shen_note": fu_shen_note,
        "pattern_adjustment": pattern_adjustment,
        "pattern_verdict_note": pattern_verdict_note,
        "classical_adj": classical_adj,
        "classical_notes": classical_notes,
        "bing_yao_adjustment": bing_yao_adjustment,
        "bing_yao_reasons": bing_yao_reasons,
    }, r)

    return {
        "base_score": base_score,
        "strength_level": strength_level,
        "change_net_effect": change_net_effect,
        "hex_adjustment": hex_adjustment,
        "hex_adjustment_reason": hex_adjustment_reason,
        "spirit_adjustment": spirit_adjustment,
        "spirit_adjustment_reasons": spirit_adjustment_reasons,
        "special_pattern": special_pattern,
        "pattern_adjustment": pattern_adjustment,
        "pattern_verdict_note": pattern_verdict_note,
        "final_score": final_score,
        # 最终锁定：若强凶格局已触发，不再允许 verdict 被后续逻辑回退到 吉/平吉
        "verdict": verdict if not (_verdict_locked and "凶" not in verdict) else "凶",
        "verdict_description": verdict_desc,
        "confidence": confidence,
        "confidence_description": _confidence_to_text(confidence),
        "timing": timing,
        "yingqi_dates": yingqi_dates,
        "reasoning_chain": reasoning_chain,
        "hidden_movement_count": hm_count,
        "hidden_movement_modifier": hm_modifier,
        "hidden_movement_reason": hm_reason,
        "greedy_harmony_score": greedy_score,
        "greedy_harmony_reason": greedy_reason,
        "dmb_adjustment": dmb_adjustment,
        "dmb_reason": dmb_reason,
        "sb_adjustment": sb_adjustment,
        "sb_reason": sb_reason,
        "combo_break_adjustment": round(combo_break_adjustment, 2),
        "combo_break_reason": combo_break_reason,
        "officer_tomb_adjustment": round(officer_tomb_adjustment, 2),
        "officer_tomb_reason": officer_tomb_reason,
        "officer_tomb_severity": officer_tomb_severity,
        "officer_tomb_verdict_note": officer_tomb_verdict_note,
        "summary_text": _compose_synthesis_summary(
            strength_level=strength_level,
            base_score=base_score,
            change_net_effect=change_net_effect,
            hex_adjustment=hex_adjustment,
            hex_adjustment_reason=hex_adjustment_reason,
            spirit_adjustment=spirit_adjustment,
            spirit_adjustment_reasons=spirit_adjustment_reasons,
            hm_modifier=hm_modifier,
            hm_reason=hm_reason,
            greedy_score=greedy_score,
            greedy_reason=greedy_reason,
            tp_score=tp_score,
            tp_reason=tp_reason,
            dmb_adjustment=dmb_adjustment,
            dmb_reason=dmb_reason,
            sb_adjustment=sb_adjustment,
            sb_reason=sb_reason,
            combo_break_adjustment=combo_break_adjustment,
            combo_break_reason=combo_break_reason,
            fu_shen_adjustment=fu_shen_adjustment,
            fu_shen_note=fu_shen_note,
            officer_tomb_adjustment=officer_tomb_adjustment,
            officer_tomb_reason=officer_tomb_reason,
            special_pattern=special_pattern,
            pattern_adjustment=pattern_adjustment,
            final_score=final_score,
            verdict=verdict,
            verdict_desc=verdict_desc,
            pattern_verdict_note=pattern_verdict_note,
            officer_tomb_verdict_note=officer_tomb_verdict_note,
            nayin_desc=nayin_desc,
            confidence=confidence,
            classical_quotes_text=classical_quotes_text,
        ),
        # 卦身摘要（供整体摘要引用）
        "hexagram_body_note": _get_hexagram_body_summary_note(r),
        # 经典引文自动检索结果
        "classical_quotes": classical_quotes,
        # 可解释性：因子贡献（SHAP 风格，供 frontend / human_narrative 使用）
        "factor_contributions": factor_contributions,
        "factor_contribution_verification": round(sum(c["score"] for c in factor_contributions), 2),
    }



from chain_step5_dates import (  # noqa: E402
    _day_branch_for_date,
    _next_date_with_day_branch,
    _next_month_with_branch,
    _add_months,
    _dates_overlap,
)
from chain_step5_timing import calculate_yingqi  # noqa: E402
from chain_step5_conf import (  # noqa: E402
    _assess_confidence,
    _confidence_to_text,
    _compose_synthesis_summary,
)
from chain_step5_yp import _predict_timing  # noqa: E402
from chain_step5_adjust import (  # noqa: E402
    apply_verdict_overrides,
    build_factor_contributions,
    compute_advanced_adjustments,
    compute_bing_yao_adjustment,
    compute_classical_adjustment,
    compute_fu_shen_adjustment,
    compute_spirit_adjustment,
    detect_xing_he_conflict,
)
