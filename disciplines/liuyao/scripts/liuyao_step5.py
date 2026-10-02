from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ks_ensure

_ks_ensure(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    BRANCH_ELEMENTS,
    KE_CYCLE,
    SHENG_CYCLE,
    EARTHLY_BRANCHES as BRANCHES,
)

from datetime import datetime, timedelta


import re


from chain_tables import (
    _BRANCH_CLASH_MAP,
    _ELEMENT_PEAK_MONTHS,
    _HE_MAP,
    HEXAGRAM_LIUCHONG,
    HEXAGRAM_LIUHE,
    SAN_HE,
    _60_CYCLE_BASE,
)

from liuyao_narrate import (_build_reasoning_chain,
    _get_hexagram_body_summary_note, find_classical_quotes)

from liuyao_timing import predict_timing_core as _predict_timing

from narrative_rules import strength_reason, strength_polarity

from narrative_utils import (  # noqa: E402
    _branch_element,
    note_text,
    safe_get,
    SANCHUAN_LABELS,
    STEP5_CONFIDENCE as CONF_TXT,
    STEP5_FACTOR_REASONS as FREASON,
    STEP5_SPIRIT_REASONS as SPIRIT_TXT,
    STEP5_VERDICT_DESCS as VDESC,
    STEP5_YINGQI as YINGQI_TXT,
    vdesc,
)

# ─── 全局变量 ───
_USE_GOD_RULES: list[dict] | None = None

from liuyao_step4 import _detect_special_pattern, _user_reason  # 跨文件引用

# ═══ chain_step5.py ═══


def step5_synthesize(r: dict) -> dict:
    """Step 5 综合判断：step3 旺衰 + step4 动变 + 卦体调候 + 神煞 → 定性 + 置信度 + 应期。"""
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
    # 5.5g: 三传克制（太岁+月建+日辰俱克）——只标记、不计分（未验证项，见 detect_three_passages_clash）
    sanchuan = adv.get("sanchuan") or {}
    sanchuan_fired = bool(sanchuan.get("fired"))
    sanchuan_reason = str(sanchuan.get("reason") or "")

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
    fu_shen_adjustment, fu_shen_note = compute_fu_shen_adjustment(step2_data, step3_data, r)

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

    # ---------- 5.8: 信号强度评估 ----------
    signal = _assess_signal_strength(step3_data, step4_data, final_score, strength_level)
    # 保留 confidence 作为向后兼容别名
    confidence = signal

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
        "strength_level": strength_level,
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
        "signal_strength": signal,
        "confidence": signal,
        "signal_strength_description": _strength_to_text(signal),
        "confidence_description": _strength_to_text(signal),
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
        # 三传克制标记（未验证项：只报象、score 恒 0，不进 final_score）
        "sanchuan": sanchuan,
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
            signal_strength=signal,
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


# ═══ chain_step5_adjust.py ═══


# ---------------------------------------------------------------- 5.4 六神
def compute_spirit_adjustment(step3_data: dict, hex_info: dict, day_stem_branch: str) -> tuple:
    """5.4 六神辅助调整（协纪辨方书—六兽分阴阳日）。返回 (adjustment, reasons)。"""
    spirit_adjustment = 0.0
    spirit_adjustment_reasons = []
    use_god_position = safe_get(step3_data, "use_god_position", default=None)
    yao_lines = safe_get(hex_info, "yao_lines", default=[])

    # 六兽分阴阳日力重 — 取出日干
    day_stem = day_stem_branch[0] if len(day_stem_branch) >= 1 else ""
    spirit_yy_factors = {}
    if day_stem:
        try:
            from classical_analysis import spirit_yin_yang_factor
            spirit_yy_factors = spirit_yin_yang_factor(day_stem)
        except ImportError:
            pass

    if use_god_position:
        for yao in yao_lines:
            if yao.get("position") == use_god_position:
                spirit = yao.get("six_spirit", "")
                yy_factor = spirit_yy_factors.get(spirit, 1.0) if spirit_yy_factors else 1.0
                if spirit == "青龙":
                    spirit_adjustment += 0.3 * yy_factor
                    if yy_factor > 1.0:
                        spirit_adjustment_reasons.append(f"{SPIRIT_TXT['qinglong_yang']['text']}(x{yy_factor})")
                    elif yy_factor < 1.0:
                        spirit_adjustment_reasons.append(f"{SPIRIT_TXT['qinglong_yin']['text']}(x{yy_factor})")
                    else:
                        spirit_adjustment_reasons.append(SPIRIT_TXT["qinglong_neutral"]["text"])
                elif spirit == "白虎":
                    spirit_adjustment -= 0.5 * yy_factor
                    if yy_factor > 1.0:
                        spirit_adjustment_reasons.append(f"{SPIRIT_TXT['baihu_yang']['text']}(x{yy_factor})")
                    elif yy_factor < 1.0:
                        spirit_adjustment_reasons.append(f"{SPIRIT_TXT['baihu_yin']['text']}(x{yy_factor})")
                    else:
                        spirit_adjustment_reasons.append(SPIRIT_TXT["baihu_neutral"]["text"])
                elif spirit == "玄武":
                    spirit_adjustment -= 0.3 * yy_factor
                    if yy_factor > 1.0:
                        spirit_adjustment_reasons.append(f"{SPIRIT_TXT['xuanwu_yin']['text']}(x{yy_factor})")
                    elif yy_factor < 1.0:
                        spirit_adjustment_reasons.append(f"{SPIRIT_TXT['xuanwu_yang']['text']}(x{yy_factor})")
                    else:
                        spirit_adjustment_reasons.append(SPIRIT_TXT["xuanwu_neutral"]["text"])
                elif spirit == "朱雀":
                    spirit_adjustment += 0.1 * yy_factor
                    if yy_factor > 1.0:
                        spirit_adjustment_reasons.append(f"{SPIRIT_TXT['zhuque_yang']['text']}(x{yy_factor})")
                    elif yy_factor < 1.0:
                        spirit_adjustment_reasons.append(f"{SPIRIT_TXT['zhuque_yin']['text']}(x{yy_factor})")
                    else:
                        spirit_adjustment_reasons.append(SPIRIT_TXT["zhuque_neutral"]["text"])
                elif spirit == "勾陈":
                    spirit_adjustment -= 0.2 * yy_factor
                    if yy_factor > 1.0:
                        spirit_adjustment_reasons.append(f"{SPIRIT_TXT['gouchen_yang']['text']}(x{yy_factor})")
                    elif yy_factor < 1.0:
                        spirit_adjustment_reasons.append(f"{SPIRIT_TXT['gouchen_yin']['text']}(x{yy_factor})")
                    else:
                        spirit_adjustment_reasons.append(SPIRIT_TXT["gouchen_neutral"]["text"])
                elif spirit == "螣蛇":
                    spirit_adjustment -= 0.1 * yy_factor
                    if yy_factor > 1.0:
                        spirit_adjustment_reasons.append(f"{SPIRIT_TXT['tengshe_yin']['text']}(x{yy_factor})")
                    elif yy_factor < 1.0:
                        spirit_adjustment_reasons.append(f"{SPIRIT_TXT['tengshe_yang']['text']}(x{yy_factor})")
                    else:
                        spirit_adjustment_reasons.append(SPIRIT_TXT["tengshe_neutral"]["text"])
                break

    return spirit_adjustment, spirit_adjustment_reasons


# ------------------------------------------- 5.5d–5.5c2 高级象（日月合/六破/入墓/破局/贪合）
def compute_advanced_adjustments(r: dict, step2_data: dict, step3_data: dict, div_time: dict) -> dict:
    """5.5d 日月合用神、5.5e 六破、5.5f 随官入墓、5.5c 三合破局、5.5c2 原神贪合忘生。"""
    advanced = r.get("advanced_analysis", {})

    # ---------- 5.5d: 日月合用神调整 (Gap 5) ----------
    # Re-run analysis here where thinking_chain data is available
    dmb_adjustment = 0.0
    dmb_reason = ""
    dmb_findings = []
    # ---------- 5.5e: 六破调整 (Gap 6) ----------
    sb_adjustment = 0.0
    sb_reason = ""
    sb_description = ""

    try:
        from classical_analysis import analyze_day_month_bonding, analyze_six_breaks
        # Build a synthetic result dict with thinking_chain data for the analysis functions
        analysis_input = dict(r)
        # Ensure thinking_chain structure exists for the helpers to find step2/step3 data
        if "thinking_chain" not in analysis_input:
            analysis_input["thinking_chain"] = {
                "step2_use_god_identification": step2_data,
                "step3_strength_analysis": step3_data,
            }
        dmb_data = analyze_day_month_bonding(analysis_input)
        dmb_adjustment = dmb_data.get("total_score_modifier", 0.0)
        dmb_findings = dmb_data.get("findings", [])
        if dmb_findings:
            dmb_reason = "、".join(
                f"{f['bond']}（{f['effect']}）" for f in dmb_findings
            )

        sb_data = analyze_six_breaks(analysis_input)
        sb_adjustment = sb_data.get("total_modifier", 0.0)
        sb_description = sb_data.get("description", "")
        if sb_data.get("has_break"):
            sb_reason = sb_data.get("description", "")
    except ImportError:
        # Fallback: use pre-computed values from enhance_reading if available
        if advanced:
            dmb_data = advanced.get("day_month_bonding", {})
            if isinstance(dmb_data, dict):
                dmb_adjustment = dmb_data.get("total_score_modifier", 0.0)
            sb_data = advanced.get("six_breaks", {})
            if isinstance(sb_data, dict):
                sb_adjustment = sb_data.get("total_modifier", 0.0)

    # ---------- 5.5f: 随官入墓凶象 (Gap 3) ----------
    # "随官入墓最凶凶，世用临之祸不轻" — 极凶之象，需从 advanced_analysis 读取
    officer_tomb_adjustment = 0.0
    officer_tomb_reason = ""
    officer_tomb_severity = "none"
    officer_tomb_verdict_override = None
    officer_tomb_description = ""

    if advanced:
        ot_data = advanced.get("officer_tomb", {})
        if isinstance(ot_data, dict) and ot_data.get("has_officer_tomb"):
            officer_tomb_adjustment = ot_data.get("score_modifier", 0.0)
            officer_tomb_severity = ot_data.get("severity", "none")
            officer_tomb_description = ot_data.get("description", "")
            scenarios = ot_data.get("scenarios", [])
            if scenarios:
                officer_tomb_reason = "随官入墓（" + "、".join(scenarios[:3]) + "）"
            else:
                officer_tomb_reason = "随官入墓"

            # catastrophic severity: force verdict to at most 平凶 regardless of score
            if officer_tomb_severity == "catastrophic":
                officer_tomb_verdict_override = "凶"
            # severe: cap at 平凶 if current score would indicate better
            elif officer_tomb_severity == "severe":
                officer_tomb_verdict_override = None  # let score adjust naturally but log

            # 疾病占修正（P0-4）：官鬼=病气，入墓为收藏之象，凶力大减
            q_txt = r.get("question", "") or ""
            if any(kw in q_txt for kw in ["病", "疾", "痛", "恙", "染"]):
                officer_tomb_adjustment = round(officer_tomb_adjustment * 0.3, 2)
                officer_tomb_severity = "mild"
                officer_tomb_description += note_text("illness_officer_tomb_mild")

    # ---------- 5.5c: 三合破局惩罚 (Gap 9) ----------
    combo_break_adjustment = 0.0
    combo_break_reason = ""
    _advanced_for_combo = r.get("advanced_analysis", {})
    if _advanced_for_combo and isinstance(_advanced_for_combo, dict):
        _tc_adv = _advanced_for_combo.get("triple_combo", {})
        if isinstance(_tc_adv, dict) and _tc_adv.get("has_triple_combo"):
            for _combo in _tc_adv.get("details", []):
                if not isinstance(_combo, dict):
                    continue
                if _combo.get("combo_status") == "破局":
                    _csm = _combo.get("combo_score_mod", -0.5)
                    if isinstance(_csm, (int, float)):
                        combo_break_adjustment += _csm
                    _cissues = _combo.get("combo_issues", [])
                    if _cissues:
                        combo_break_reason = "、".join(_cissues)
                        break  # only show first broken combo issue for brevity

    # ---------- 5.5c2: 原神贪合忘生检测 (三合火局/水局 etc 中吸收原神) ----------
    # 条件：原神所在五行参与了三合局(由日月引动) + 原神无动爻(完全被合住不生日)
    yuan_shen_bond_adjustment = 0.0
    yuan_shen_bond_reason = ""
    if _advanced_for_combo and isinstance(_advanced_for_combo, dict):
        _tc_adv2 = _advanced_for_combo.get("triple_combo", {})
        if isinstance(_tc_adv2, dict) and _tc_adv2.get("has_triple_combo"):
            _yuan_elem = safe_get(step2_data, "yuan_shen", "element", default="")
            _yuan_positions = safe_get(step2_data, "yuan_shen", "positions", default=[]) or []
            _day_br = safe_get(div_time, "day_stem_branch", default="")
            _month_br = safe_get(div_time, "month_stem_branch", default="")
            _day_b = _day_br[1:] if len(_day_br) >= 2 else ""
            _month_b = _month_br[1:] if len(_month_br) >= 2 else ""
            # 原神是否有动爻(明动)— 有动爻则原神仍有力，不构成贪合忘生
            _yuan_has_moving = any(
                isinstance(p, dict) and p.get("is_moving") for p in _yuan_positions
            )
            if _yuan_elem and not _yuan_has_moving:
                for _combo2 in _tc_adv2.get("details", []):
                    if not isinstance(_combo2, dict):
                        continue
                    if _combo2.get("element") != _yuan_elem:
                        continue
                    _combo_branches = _combo2.get("branches", [])
                    _combo_positions = _combo2.get("positions", [])
                    # 检查日辰/月建是否参与了此三合(位置列表中标记或分支匹配)
                    _has_day_or_month = any(
                        (isinstance(p, str) and ("日" in p or "月" in p))
                        for p in _combo_positions
                    ) or (_day_b in _combo_branches) or (_month_b in _combo_branches)
                    _completeness = _combo2.get("completeness", "")
                    # 日月引动待用之局
                    _active = _has_day_or_month
                    # 额外约束：原神之支必须全部在合局内，方构成完整贪合忘生
                    # (若原神有支在局外，仍可生用神，不构成贪合)
                    if _active and _yuan_positions:
                        _yuan_branches_in = [
                            p.get("earthly_branch", "")
                            for p in _yuan_positions
                            if isinstance(p, dict) and p.get("earthly_branch")
                        ]
                        _all_yuan_in_combo = bool(_yuan_branches_in) and all(
                            b in _combo_branches for b in _yuan_branches_in
                        )
                        _active = _all_yuan_in_combo
                    if _active:
                        # 原神贪合忘生 — 用神失源 (-2.0推至凶)
                        if yuan_shen_bond_adjustment == 0.0:
                            yuan_shen_bond_adjustment = -2.0
                        _combo_branches_str = "".join(_combo_branches)
                        _day_info = ""
                        if _day_b in _combo_branches:
                            _day_info = f"(日{_day_b}引动)"
                        elif _month_b in _combo_branches:
                            _day_info = f"(月{_month_b}引动)"
                        yuan_shen_bond_reason = (
                            f"原神{_yuan_elem}参与{_combo_branches_str}"
                            f"三合{_yuan_elem}局{_day_info}，贪合忘生，用神失源"
                        )
                        break

    return {
        "dmb_adjustment": dmb_adjustment,
        "dmb_reason": dmb_reason,
        "dmb_findings": dmb_findings,
        "sb_adjustment": sb_adjustment,
        "sb_reason": sb_reason,
        "sb_description": sb_description,
        "officer_tomb_adjustment": officer_tomb_adjustment,
        "officer_tomb_reason": officer_tomb_reason,
        "officer_tomb_severity": officer_tomb_severity,
        "officer_tomb_verdict_override": officer_tomb_verdict_override,
        "officer_tomb_description": officer_tomb_description,
        "combo_break_adjustment": combo_break_adjustment,
        "combo_break_reason": combo_break_reason,
        "yuan_shen_bond_adjustment": yuan_shen_bond_adjustment,
        "yuan_shen_bond_reason": yuan_shen_bond_reason,
        "sanchuan": detect_three_passages_clash(r, step2_data, step3_data, div_time),
    }


def detect_three_passages_clash(r: dict, step2_data: dict, step3_data: dict, div_time: dict) -> dict:
    """三传克制（太岁+月建+日辰俱克用神）。⚠️ 基准集无太岁对照案例，仅标记、score 恒为 0。"""
    out = {
        "fired": False,
        "score_adjustment": 0.0,
        "counted": False,          # 明确声明：本条未计分
        "year_branch": "",
        "month_branch": "",
        "day_branch": "",
        "use_god_branch": "",
        "use_god_element": "",
        "reason": "",
        "verdict": "",
        "verified": False,
    }
    labels = SANCHUAN_LABELS or {}
    out["verdict"] = labels.get("verdict", "")
    out["verified"] = bool(labels.get("verified", False))

    year_gz = str((r.get("divination_time") or {}).get("year_stem_branch") or "")
    month_gz = str(div_time.get("month_stem_branch") or "")
    day_gz = str(div_time.get("day_stem_branch") or "")
    year_branch = year_gz[1:] if len(year_gz) >= 2 else ""
    month_branch = month_gz[1:] if len(month_gz) >= 2 else ""
    day_branch = day_gz[1:] if len(day_gz) >= 2 else ""

    sel = step2_data.get("selected_use_god") or {}
    use_god_branch = sel.get("earthly_branch", "") if isinstance(sel, dict) else ""
    use_god_element = step2_data.get("use_god_element", "")

    out.update({
        "year_branch": year_branch,
        "month_branch": month_branch,
        "day_branch": day_branch,
        "use_god_branch": use_god_branch,
        "use_god_element": use_god_element,
    })

    if not (year_branch and month_branch and day_branch and use_god_element):
        return out

    def _ke(branch: str) -> bool:
        elem = BRANCH_ELEMENTS.get(branch, "")
        return bool(elem) and KE_CYCLE.get(elem) == use_god_element

    def _sheng(branch: str) -> bool:
        elem = BRANCH_ELEMENTS.get(branch, "")
        return bool(elem) and SHENG_CYCLE.get(elem) == use_god_element

    branches = (year_branch, month_branch, day_branch)
    if not all(_ke(b) for b in branches):
        return out
    if any(_sheng(b) for b in branches):
        return out
    # 卦中有动爻来生用神者不构成"俱克"（原书以"得众多动爻齐来生扶"为解）
    for yao in (safe_get(r, "original_hexagram", "yao_lines", default=[]) or []):
        if isinstance(yao, dict) and yao.get("is_moving"):
            if SHENG_CYCLE.get(_branch_element(yao.get("earthly_branch", ""))) == use_god_element:
                return out

    out["fired"] = True
    out["reason"] = str(labels.get("reason", "")).format(
        year=year_branch, month=month_branch, day=day_branch,
        use_god=use_god_element or "用神",
    ) or "三传俱克（太岁/月建/日辰俱克用神且无生扶），虽旺亦危"
    return out


# ---------------------------------------------------------------- 伏神格局
def compute_fu_shen_adjustment(step2_data: dict, step3_data: dict, r: dict) -> tuple:
    """伏神格局调整（飞空得出 / 飞来生伏 / 绝于飞 / 飞克伏 / 伏泄气 / 伏而不得出）。

    2026-10-02（TECH-DEBT 2.3「伏藏+合绊未进方向聚合」）：
      ① 新增**伏而不得出**方向权重 -1.0——旧实现只覆盖「得出/泄气/克伏」各象，
        伏神无提挈（日月生扶、飞神空破、伏克飞皆无）时方向分零反馈，只有应期
        效果；判据读 step2 `fu_cang_detail.results[].can_emerge` 结构，不嗅探文本。
        所本：《黄金策·千金赋》"伏无提挈终徒尔，飞不推开亦枉然"。
      ② step2_data 为新增入参（结构判据取用）；旧文本路径保留为兜底，先后语义不变。
    """
    step3_reasoning_text = step3_data.get("summary_text", "") if step3_data else ""
    fu_shen_adjustment = 0.0
    fu_shen_note = ""
    if "飞空得出" in step3_reasoning_text or ("飞神" in step3_reasoning_text and "旬空" in step3_reasoning_text and "得出" in step3_reasoning_text):
        # 飞神旬空 → 伏神得出有力（优先于泄气/克伏等次级关系）
        fu_shen_adjustment = 1.5
        fu_shen_note = note_text("fu_fei_kong_out")
    elif "飞来生伏" in step3_reasoning_text or "飞生伏" in step3_reasoning_text:
        # 飞神生伏神，伏得出为吉
        fu_shen_adjustment = 1.0
        fu_shen_note = note_text("fu_fei_sheng_fu")
    elif "绝于飞" in step3_reasoning_text:
        # 伏神绝于飞神 → 气绝难出（P0-5）
        fu_shen_adjustment = -2.0
        fu_shen_note = note_text("fu_die_at_fei")
    elif "飞克伏" in step3_reasoning_text:
        # 飞克伏: 需检查飞神是否旬空/月破 → 伏得出为吉
        import re
        m_fei = re.search(r'飞神(\w)', step3_reasoning_text)
        fei_branch = m_fei.group(1) if m_fei else ""
        empty_branches_list = r.get("empty_branches", []) or []
        if fei_branch and fei_branch in empty_branches_list:
            # 飞神旬空，伏神得出为吉
            fu_shen_adjustment = 1.5
            fu_shen_note = note_text("fu_out_fei_empty", fei_branch=fei_branch)
        elif "月破" in step3_reasoning_text:
            # 飞神月破，伏神得出
            fu_shen_adjustment = 1.0
            fu_shen_note = note_text("fu_out_fei_month_break")
        else:
            fu_shen_adjustment = -1.0
            fu_shen_note = note_text("fu_fei_ke_hard_out")
    elif "伏泄气于飞" in step3_reasoning_text:
        # 伏泄气: 伏神被动泄力，轻微负面
        fu_shen_adjustment = -0.5
        fu_shen_note = note_text("fu_drain_by_fei")
    else:
        # 伏而不得出（结构化判据，旧文本路径覆盖不到的盲区）：用神伏藏且所有
        # 伏/飞对均 can_emerge=False——无提挈则终不得出头，方向减分。
        _fu_results = ((step2_data or {}).get("fu_cang_detail") or {}).get("results") or []
        _fu_entries = [e for e in _fu_results if isinstance(e, dict)]
        if _fu_entries and all(not e.get("can_emerge", True) for e in _fu_entries):
            fu_shen_adjustment = -1.0
            fu_shen_note = note_text("fu_no_emerge")

    return fu_shen_adjustment, fu_shen_note


# ---------------------------------------------------------------- 5.5h 古籍通用格局加减
def compute_classical_adjustment(
    r: dict,
    step1_data: dict,
    step2_data: dict,
    step3_data: dict,
    special_pattern: dict,
    pattern_verdict_note: str,
) -> dict:
    """5.5h 古籍通用格局加减 + 产出覆用上下文 ctx。"""
    classical_adj = 0.0
    classical_notes = []
    _q_l = str((r.get("question") or r.get("question_category") or ""))
    # 行人归期 ≠ 逃亡追回：逃仆/追回不套「用神有气主终归」
    _is_catch = any(k in _q_l for k in ("逃", "追回", "可追", "逃仆", "走失", "盗"))
    _is_travel_return = (
        any(k in _q_l for k in ("归", "回", "行人", "何日", "出外", "出行"))
        and not _is_catch
    )
    _is_wealth = any(k in _q_l for k in ("财", "投资", "生意", "价", "贸易", "求财", "经营", "银", "失物", "失"))

    # 世爻六亲
    world_relation = ""
    world_branch = ""
    use_el_s = (step2_data or {}).get("use_god_element") or ""
    ug_cat = (step2_data or {}).get("use_god_category") or ""
    ug_sel = (step2_data or {}).get("selected_use_god") or {}
    ug_branch_s = ug_sel.get("earthly_branch") or (step3_data or {}).get("use_god_branch") or ""
    ug_el_s = ug_sel.get("element") or use_el_s
    for _y in ((r.get("original_hexagram") or {}).get("yao_lines") or []):
        if isinstance(_y, dict) and _y.get("is_world"):
            world_relation = _y.get("six_relation") or ""
            world_branch = _y.get("earthly_branch") or ""
            break
    palace_el = (r.get("original_hexagram") or {}).get("palace_element") or ""

    def _el_of_branch(b):
        return BRANCH_ELEMENTS.get(b or "", "")

    # 1) 行人/归期：用神生世/克世 — 迟归或速至，皆主能归（《黄金策》出行章）
    if _is_travel_return and ug_el_s and world_branch:
        w_el = _el_of_branch(world_branch) or ""
        if w_el and SHENG_CYCLE.get(ug_el_s) == w_el:
            classical_adj += 1.5
            classical_notes.append(note_text("travel_use_sheng_world"))
        elif w_el and KE_CYCLE.get(ug_el_s) == w_el:
            classical_adj += 0.8
            classical_notes.append(note_text("travel_use_ke_world"))
        elif w_el and KE_CYCLE.get(w_el) == ug_el_s:
            # 世克用：行人受制，未必即归，但用神有气仍主终归
            classical_adj += 0.3
            classical_notes.append(note_text("travel_world_ke_use"))
    if _is_travel_return:
        _fu_txt = str((step3_data or {}).get("summary_text") or "")
        _lv = str((step3_data or {}).get("strength_level") or "")
        _dead = any(k in _fu_txt for k in ("绝于", "真空", "月破", "飞克伏难出", "克伏不出"))
        if (not _dead) and (
            "得出" in _fu_txt
            or _lv in ("旺", "相", "极旺", "中和", "中和偏旺")
            or "伏神" in _fu_txt
        ):
            classical_adj += 0.6
            classical_notes.append(note_text("travel_use_alive"))

    # 2) 兄弟持世 + 求财 — 古籍大忌（《增删》兄弟持世莫求财）
    _sp_pat_txt = ""
    try:
        if isinstance(special_pattern, dict):
            _sp_pat_txt = str(special_pattern.get("pattern") or "") + str(special_pattern.get("description") or "")
    except Exception:
        _sp_pat_txt = ""
    if world_relation == "兄弟" and _is_wealth and ug_cat == "妻财":
        if any(k in _q_l for k in ("失", "找回", "失物")) or "冲中逢合" in _sp_pat_txt:
            classical_adj -= 0.2
            classical_notes.append(note_text("brother_hold_wealth_lost_soft"))
        else:
            classical_adj -= 1.2
            classical_notes.append(note_text("brother_hold_wealth"))

    # 3) 妻财持世 + 失物 — 世持财主自失可寻（增删失物章）
    if world_relation == "妻财" and any(k in _q_l for k in ("失", "找回", "失物", "银")):
        classical_adj += 0.8
        classical_notes.append(note_text("wealth_hold_lost"))

    # 5) 原神失位：用神旺相而原神（完全）不在卦中或不动 — 黄金策「用神虽旺亦凶」
    _lv_ug = str((step3_data or {}).get("strength_level") or "")
    _yuan = (step2_data or {}).get("yuan_shen") or {}
    _yuan_pos = _yuan.get("positions") or []
    _yuan_moving = any(isinstance(p, dict) and p.get("is_moving") for p in _yuan_pos)
    # 静卦判定：六爻全静时，原神不动是天然状态, 不应扣"失位"
    # 用 step1 返回的 moving_lines 列表判定是否为静卦
    _static_moving_lines = (step1_data or {}).get("moving_lines") or []
    _is_static_hexagram = (not _static_moving_lines) or len(_static_moving_lines) == 0
    if _lv_ug in ("旺", "极旺") and ug_cat and ug_cat != "世爻":
        _skip_yuanshen = (
            "冲中逢合" in _sp_pat_txt
            or any(k in _q_l for k in ("失", "找回", "失物"))
            or "世持财" in _sp_pat_txt
        )
        # 静卦(_is_static_hexagram=True)下，只要原神出现在卦中(position有值), 不算"失位";
        # 仅当原神完全不在卦中 (not _yuan_pos) 时, 才扣-1.0
        # 动卦下原神位置存在但未发动时, 仍扣-1.0
        _yuan_missing = (not _yuan_pos) or (not _is_static_hexagram and not _yuan_moving)
        if _yuan_missing and not _skip_yuanshen:
            classical_adj -= 1.0
            classical_notes.append(note_text("static_yuanshen_missing"))

    # 6) 久病逢冲为凶（对「近病逢冲即愈」）
    if any(k in _q_l for k in ("久病", "半年", "病久", "多月")):
        classical_adj -= 0.8
        classical_notes.append(note_text("chronic_illness"))

    # 7) 兄弟持世 + 功名/考试 — 竞争费力（可中而难前茅）
    if world_relation == "兄弟" and any(k in _q_l for k in ("考试", "功名", "学业", "科举", "中第")):
        classical_adj -= 0.4
        classical_notes.append(note_text("brother_hold_exam"))

    # 8) 官司：官鬼克世 / 父母月破 → 不利（增删官非章）
    if any(k in _q_l for k in ("官司", "官非", "诬告", "诉讼", "官事")) and "师尊" not in _q_l:
        ug_br_s = ug_branch_s
        w_br = world_branch
        ug_e = ug_el_s or ""
        w_e = _el_of_branch(w_br) or ""
        if ug_e and w_e and KE_CYCLE.get(ug_e) == w_e:
            classical_adj -= 1.2
            classical_notes.append(note_text("officer_ke_world_lawsuit"))
        # 文书月破：从摘要文本识别
        _txt3 = str((step3_data or {}).get("summary_text") or "") + str((step2_data or {}).get("summary_text") or "")
        if "月破" in _txt3 and any(k in _q_l for k in ("官司", "官非", "诬告")):
            classical_adj -= 0.5
            classical_notes.append(note_text("document_month_break"))

    # 9) 原神失位加强：旺极无生 → 大幅降分（黄金策）
    # 仅当用神为"极旺"时才额外加权；"旺"级已有规则5的-1.0，不再叠加
    if any("原神失位" in n for n in classical_notes) and _lv_ug == "极旺":
        classical_adj -= 1.0
        classical_notes.append(note_text("extreme_prosper_no_source"))

    # 4) 用神临月建（通用旺格标记分已在旺衰，此处仅补注记）

    # 古籍通用格局注记（供标签与人话）— 必须在 classical_notes 生成之后
    if classical_notes:
        extra = "；".join(classical_notes)
        if pattern_verdict_note:
            pattern_verdict_note = pattern_verdict_note + "；" + extra
        else:
            pattern_verdict_note = extra

    return {
        "classical_adj": classical_adj,
        "classical_notes": classical_notes,
        "pattern_verdict_note": pattern_verdict_note,
        # 后续「断语覆写」与「因子贡献」仍需用到这批上下文，一并带出
        "ctx": {
            "_q_l": _q_l,
            "_sp_pat_txt": _sp_pat_txt,
            "world_relation": world_relation,
            "ug_cat": ug_cat,
            "_is_travel_return": _is_travel_return,
            "_is_wealth": _is_wealth,
        },
    }


# ---------------------------------------------------------------- 5.5i 三刑+六合相战
def detect_xing_he_conflict(step3_data: dict, r: dict, hex_name: str) -> bool:
    """三刑+六合吉凶相战：成刑且六合卦 → 不覆过平凶；以「入六合表」为准（小畜例外处理）。"""
    tp_data_for_conflict = safe_get(step3_data, "three_punishments_raw", default=None)
    if tp_data_for_conflict is None:
        _adv_for_xh = r.get("advanced_analysis", {})
        if isinstance(_adv_for_xh, dict):
            tp_data_for_conflict = _adv_for_xh.get("three_punishments", {})
    _is_liuhe_hexagram = (hex_name in HEXAGRAM_LIUHE)
    if (isinstance(tp_data_for_conflict, dict) and tp_data_for_conflict.get("has_punishment")
            and _is_liuhe_hexagram):
        _tp_complete_cnt = sum(
            1 for _p in tp_data_for_conflict.get("punishments", [])
            if isinstance(_p, dict) and _p.get("completeness") in ("完整", "成刑", "催刑")
        )
        if _tp_complete_cnt >= 2:
            return True
    return False


# ---------------------------------------------------------------- 5.6 病药
def compute_bing_yao_adjustment(step2_data: dict, step3_data: dict) -> tuple:
    """病药（《增删卜易》）：有界加减，不进主分（仅 narrate 旁参）。"""
    bing_yao_adjustment = 0.0
    bing_yao_reasons: list[str] = []
    bing_yao_panel: dict = {}
    try:
        from bing_yao_shensha import evaluate_bing_yao
        bing_yao_panel = evaluate_bing_yao(step2_data, step3_data, None) or {}
    except Exception:
        bing_yao_panel = {}
    _ill = set(bing_yao_panel.get("illness_codes") or [])
    _med = set(bing_yao_panel.get("medicine_codes") or [])
    # 重病（空+破+衰）无药：有界扣减
    if {"void", "month_break", "weak"} <= _ill and not _med:
        bing_yao_adjustment -= 0.4
        bing_yao_reasons.append("病重无药")
    elif _ill and not _med:
        bing_yao_adjustment -= 0.2
        bing_yao_reasons.append("有病无药")
    elif _med and not _ill:
        bing_yao_adjustment += 0.15
        bing_yao_reasons.append("有药无病")
    # 有药能解病：不再另加（避免双重计）
    return bing_yao_adjustment, bing_yao_reasons


# ---------------------------------------------------------------- 5.7 断语覆写
def apply_verdict_overrides(
    verdict: str,
    verdict_desc: str,
    final_score: float,
    r: dict,
    step3_data: dict,
    step4_data: dict,
    special_pattern: dict,
    classical_notes: list,
    ctx: dict,
    xing_he_conflict_override: bool,
    officer_tomb: dict,
) -> dict:
    """5.7 古籍强凶/从吉覆写链 → 定性三件套（verdict/desc/score）。"""
    _q_l = ctx.get("_q_l", "")
    _sp_pat_txt = ctx.get("_sp_pat_txt", "")
    world_relation = ctx.get("world_relation", "")
    ug_cat = ctx.get("ug_cat", "")
    _is_travel_return = ctx.get("_is_travel_return", False)
    _is_wealth = ctx.get("_is_wealth", False)

    # v8 口径微调：更贴近古籍断语习惯
    _qtext = str((r.get("question") or r.get("question_category") or ""))
    _sp = special_pattern if isinstance(special_pattern, dict) else {}
    _sp_pat = str(_sp.get("pattern") or "") + str(_sp.get("description") or "")

    # ── 古籍强凶格局强制覆写（pattern-based overrides）──
    _fired = False
    # 行人/出行占+六冲主散/合处逢冲：行人被冲散 → 凶
    if any(k in _qtext for k in ("行人", "出行", "回来", "归")) and ("六冲" in _sp_pat or "合处逢冲" in _sp_pat):
        if verdict in ("吉", "大吉", "平吉"):
            verdict = "凶"
            verdict_desc = vdesc("travel_scattered")
            _fired = True
    # 合伙+六冲主散/合处逢冲：合伙看世应，应冲世则散 → 凶
    if "合伙" in _qtext and ("六冲" in _sp_pat or "合处逢冲" in _sp_pat):
        if verdict in ("吉", "大吉", "平吉"):
            verdict = "凶"
            verdict_desc = vdesc("partner_scattered")
            _fired = True
    # 用神衰弱+净动变负 → 凶
    if verdict == "平吉" and final_score < 0.0:
        _net_eff = 0.0
        if step4_data and isinstance(step4_data, dict):
            _net_eff = step4_data.get("net_effect") or 0.0
        if _net_eff < -0.2:
            verdict = "凶"
            verdict_desc = vdesc("weak_use_net_negative")
            _fired = True
    # 三刑+六合吉凶相战覆写：2+成刑/催刑 + 六合卦 → 上限不超过平凶
    # 偏向中带凶：六合主合而三刑主损，合中带损，吉凶相战，凶多吉少。
    # 依古籍合中带损之旨，伏下仍有六合之余气，故 score 保底在 0.5 (偏向下界)。
    if xing_he_conflict_override and verdict in ("吉", "大吉", "平吉"):
        verdict = "平凶"
        verdict_desc = vdesc("xing_he_conflict")
        if final_score < 0.5:
            final_score = 0.5
            final_score = round(final_score, 2)
        _fired = True

    if "合处逢冲" in _sp_pat and verdict in ("凶", "大凶", "平吉"):
        if any(k in _qtext for k in ("婚", "合", "成否", "聚")):
            verdict = "平/不利"
            verdict_desc = vdesc("he_then_chong")
        elif verdict == "大凶":
            verdict = "凶"
    if any(k in _qtext for k in ("价", "贵贱", "桑叶", "涨跌")) and verdict in ("凶", "大凶"):
        verdict = "下跌"
        verdict_desc = vdesc("price_down")

    # 古籍通用口径：行人「用神生世/克世」主能归；兄弟持世求财主耗
    if classical_notes:
        if any("原神失位" in n for n in classical_notes) and "冲中逢合" not in _sp_pat_txt:
            if verdict in ("大吉",):
                verdict = "吉"
                verdict_desc = vdesc("yuanshen_missing_daji_cap")
            if any("旺极无源" in n for n in classical_notes) and verdict in ("吉", "大吉", "平吉"):
                if final_score < 1.0:
                    verdict = "凶"
                    verdict_desc = vdesc("extreme_no_source_xiong")
                else:
                    verdict = "平吉"
                    verdict_desc = vdesc("yuanshen_missing_ping_ji")
            elif verdict == "吉" and final_score < 2.0:
                verdict = "平吉"
                verdict_desc = vdesc("yuanshen_missing_discount")
        if any("官鬼克世" in n for n in classical_notes):
            if verdict in ("大吉", "吉"):
                verdict = "凶"
                verdict_desc = vdesc("officer_ke_world_xiong")
            elif verdict == "平吉":
                verdict = "凶"
                verdict_desc = vdesc("officer_ke_world_tight")
        if any("兄弟持世求名" in n for n in classical_notes) and verdict in ("吉", "大凶", "凶"):
            if verdict in ("凶", "大凶"):
                verdict = "平吉"
                verdict_desc = vdesc("brother_exam_not_desperate")
            else:
                verdict = "平吉"
                verdict_desc = vdesc("brother_exam_hard")
        if any("久病" in n for n in classical_notes):
            if verdict in ("大吉", "吉"):
                verdict = "平吉" if verdict == "吉" else "凶"
                if verdict == "平吉":
                    verdict_desc = vdesc("chronic_illness_care")
            if verdict == "平吉" and any(k in _q_l for k in ("久病", "半年")):
                verdict = "凶"
                verdict_desc = vdesc("chronic_illness_tight")
        if any("兄弟持世求名" in n for n in classical_notes) and verdict in ("吉", "大吉"):
            verdict = "平吉"
            verdict_desc = vdesc("brother_exam_hard")
        if _is_travel_return and any(
            ("用神生世" in n) or ("用神克世" in n) or ("行人用神有气" in n) or ("世克用" in n)
            for n in classical_notes
        ):
            if verdict in ("凶", "大凶"):
                verdict = "平吉"
                verdict_desc = vdesc("travel_eventually_back")
            if any("用神生世" in n for n in classical_notes) and verdict in ("平吉", "凶", "大凶"):
                verdict = "吉"
                verdict_desc = vdesc("travel_use_sheng_back")
            elif verdict == "平吉" and any("用神克世" in n for n in classical_notes):
                verdict = "吉"
                verdict_desc = vdesc("travel_use_ke_fast")
        if world_relation == "兄弟" and _is_wealth and ug_cat == "妻财":
            _soft_bro = any(k in _q_l for k in ("失", "找回", "失物")) or "冲中逢合" in _sp_pat_txt
            if _soft_bro:
                if verdict in ("凶", "大凶") and final_score >= 0:
                    verdict = "吉"
                    verdict_desc = vdesc("brother_lost_he_chong")
                elif verdict == "平吉" and final_score >= 0:
                    verdict = "吉"
                    verdict_desc = vdesc("lost_recoverable")
            else:
                if verdict in ("大吉",):
                    verdict = "吉"
                    verdict_desc = vdesc("wealth_but_brother")
                elif verdict == "吉" and final_score < 2.5:
                    verdict = "平吉"
                    verdict_desc = vdesc("wealth_watch_waste")
                elif verdict in ("平吉",) and final_score <= 0.2:
                    verdict = "平/不利"
                    verdict_desc = vdesc("brother_wealth_not_worth")
    elif _is_travel_return and verdict in ("凶", "大凶"):
        # 无 classical_notes 时仍按行人占谨慎：用神非死绝不断大凶
        _fu_txt2 = str((step3_data or {}).get("summary_text") or "")
        if not any(k in _fu_txt2 for k in ("绝于", "真空", "月破")):
            if (step3_data or {}).get("effective_score", 0) >= 2.0:
                verdict = "平吉"
                verdict_desc = vdesc("travel_use_alive_slow")

    # ---------- 5.7b: 随官入墓凶象覆盖 (Gap 3) ----------
    # 随官入墓极凶，catastrophic级别强行覆盖定性判断
    officer_tomb_verdict_note = ""
    officer_tomb_verdict_override = officer_tomb.get("verdict_override")
    if officer_tomb_verdict_override:
        old_verdict = verdict
        verdict = officer_tomb_verdict_override
        if officer_tomb.get("severity") == "catastrophic":
            verdict_desc = VDESC["officer_tomb_catastrophic_prefix"]["text"] + str(officer_tomb.get("description") or "")[:50]
            officer_tomb_verdict_note = (
                f"【随官入墓强行覆盖】原为{old_verdict}，"
                f"因{officer_tomb.get('reason')}降级为凶"
            )
    elif officer_tomb.get("severity") == "severe" and officer_tomb.get("adjustment", 0.0) <= -1.0:
        officer_tomb_verdict_note = (
            f"【随官入墓凶象】{officer_tomb.get('reason')}——"
            f"评分调整{officer_tomb.get('adjustment'):+.1f}"
        )

    return {
        "verdict": verdict,
        "verdict_desc": verdict_desc,
        "final_score": final_score,
        "fired": _fired,
        "officer_tomb_verdict_note": officer_tomb_verdict_note,
    }


# 用神旺衰因子理由/极性已统一由 narrative_rules.strength_reason / strength_polarity 提供
# （数据驱动：verdict_texts.json 的 strength_reason_map / strength_polarity_map）。


# ---------------------------------------------------------------- 5.13 因子贡献
def build_factor_contributions(adj: dict, r: dict) -> list:
    """5.13 可解释性因子贡献（SHAP 风格）。adj 为各调整项的名→(分值, 理由)映射。"""
    base_score = adj.get("base_score", 0.0)
    change_net_effect = adj.get("change_net_effect", 0.0)
    hex_adjustment = adj.get("hex_adjustment", 0.0)
    hex_adjustment_reason = adj.get("hex_adjustment_reason", "")
    spirit_adjustment = adj.get("spirit_adjustment", 0.0)
    spirit_adjustment_reasons = adj.get("spirit_adjustment_reasons", []) or []
    dmb_adjustment = adj.get("dmb_adjustment", 0.0)
    dmb_reason = adj.get("dmb_reason", "")
    sb_adjustment = adj.get("sb_adjustment", 0.0)
    sb_reason = adj.get("sb_reason", "")
    combo_break_adjustment = adj.get("combo_break_adjustment", 0.0)
    combo_break_reason = adj.get("combo_break_reason", "")
    yuan_shen_bond_adjustment = adj.get("yuan_shen_bond_adjustment", 0.0)
    yuan_shen_bond_reason = adj.get("yuan_shen_bond_reason", "")
    officer_tomb_adjustment = adj.get("officer_tomb_adjustment", 0.0)
    officer_tomb_reason = adj.get("officer_tomb_reason", "")
    fu_shen_adjustment = adj.get("fu_shen_adjustment", 0.0)
    fu_shen_note = adj.get("fu_shen_note", "")
    pattern_adjustment = adj.get("pattern_adjustment", 0.0)
    pattern_verdict_note = adj.get("pattern_verdict_note", "")
    classical_adj = adj.get("classical_adj", 0.0)
    classical_notes = adj.get("classical_notes", []) or []
    bing_yao_adjustment = adj.get("bing_yao_adjustment", 0.0)
    bing_yao_reasons = adj.get("bing_yao_reasons", []) or []

    factor_contributions = []
    # 1. 用神旺衰基础分（理由/极性均以权威 strength_level 为准，避免与正文旺衰口径矛盾；
    #    极性供 有利面/拖累面 分类使用，与 floored score 解耦——极弱不再误入有利面）
    strength_level = str(adj.get("strength_level") or "")
    factor_contributions.append({
        "name": "用神旺衰",
        "factor": "base",
        "score": round(base_score, 2),
        "reason": strength_reason(strength_level),
        "polarity": strength_polarity(strength_level),
    })
    # 2. 动变效应
    factor_contributions.append({
        "name": "动变效应",
        "factor": "change",
        "score": round(change_net_effect, 2),
        "reason": (
            FREASON["change_sheng"]["text"] if change_net_effect > 0.3 else
            FREASON["change_ke"]["text"] if change_net_effect < -0.3 else
            FREASON["change_balance"]["text"]
        )
    })
    # 3. 合冲卦性
    if hex_adjustment != 0:
        factor_contributions.append({
            "name": "合冲卦性",
            "factor": "hexagram",
            "score": round(hex_adjustment, 2),
            "reason": _user_reason(hex_adjustment_reason, FREASON["hex_liuhe"]["text"] if hex_adjustment > 0 else FREASON["hex_liuchong"]["text"])
        })
    # 4. 六神辅助
    if spirit_adjustment != 0:
        # 清理 reason 中含 (xN.N) 系数备注，避免用 generator 导致 re 闭包作用域异常
        _cleaned_reasons = []
        for _r in spirit_adjustment_reasons:
            _cleaned_reasons.append(_r.split("(x")[0].strip() if "(x" in _r else _r)
        _reason_text = "；".join(_cleaned_reasons) or FREASON["spirit_fallback"]["text"]
        factor_contributions.append({
            "name": "六神辅助",
            "factor": "spirit",
            "score": round(spirit_adjustment, 2),
            "reason": _reason_text,
        })
    # 5. 暗动（已并入 base_score/effective_score，不单独计入以避免重复计算）
    # 6. 日月合
    if dmb_adjustment != 0:
        factor_contributions.append({
            "name": "日月合用神",
            "factor": "day_month_bond",
            "score": round(dmb_adjustment, 2),
            "reason": _user_reason(dmb_reason, FREASON["day_month_bond"]["text"])
        })
    # 7. 六破
    if sb_adjustment != 0:
        factor_contributions.append({
            "name": "六破损伤",
            "factor": "six_breaks",
            "score": round(sb_adjustment, 2),
            "reason": _user_reason(sb_reason, FREASON["six_break"]["text"])
        })
    # 8. 三合破
    if combo_break_adjustment != 0:
        factor_contributions.append({
            "name": "三合局破",
            "factor": "combo",
            "score": round(combo_break_adjustment, 2),
            "reason": _user_reason(combo_break_reason, FREASON["combo_break"]["text"])
        })
    # 8b. 原神贪合忘生
    if yuan_shen_bond_adjustment != 0:
        factor_contributions.append({
            "name": "原神贪合忘生",
            "factor": "yuan_shen_bond",
            "score": round(yuan_shen_bond_adjustment, 2),
            "reason": _user_reason(yuan_shen_bond_reason, FREASON["yuanshen_bond"]["text"])
        })
    # 9. 随官入墓
    if officer_tomb_adjustment != 0:
        factor_contributions.append({
            "name": "随官入墓",
            "factor": "tomb",
            "score": round(officer_tomb_adjustment, 2),
            "reason": _user_reason(officer_tomb_reason, FREASON["officer_tomb"]["text"])
        })
    # 10. 伏神得出 / 伏神不得出（TECH-DEBT 2.3：伏而不得出 −1.0 已入方向聚合）
    if fu_shen_adjustment != 0:
        factor_contributions.append({
            "name": "伏神不得出" if fu_shen_adjustment < 0 else "伏神得出",
            "factor": "fu_shen",
            "score": round(fu_shen_adjustment, 2),
            "reason": _user_reason(
                fu_shen_note,
                FREASON["fu_no_emerge"]["text"] if fu_shen_adjustment < 0
                else FREASON["fu_shen_out"]["text"],
            )
        })
    # 11. 格局调整
    if pattern_adjustment != 0:
        factor_contributions.append({
            "name": "特殊格局",
            "factor": "pattern",
            "score": round(pattern_adjustment, 2),
            "reason": _user_reason(pattern_verdict_note, FREASON["special_pattern"]["text"])
        })
    # 12. 古籍通用格局加减（classical_adj：六亲持世+事项+伏出等）
    if classical_adj != 0:
        factor_contributions.append({
            "name": "古籍格局加减",
            "factor": "classical",
            "score": round(classical_adj, 2),
            "reason": "；".join(_user_reason(n) for n in classical_notes[:2]) if classical_notes else FREASON["classical_fallback"]["text"]
        })
    # 12b. 六亲持世深化（含占问情境化解读）
    adv_shi = r.get("advanced_analysis", {}).get("shi_yao_relation") if isinstance(r, dict) else None
    if isinstance(adv_shi, dict) and adv_shi.get("classical_rule"):
        _sh_reason = adv_shi["classical_rule"]
        if adv_shi.get("scenario_interpretation"):
            _sh_reason = adv_shi["scenario_interpretation"]
        factor_contributions.append({
            "name": "六亲持世",
            "factor": "shi_yao",
            "score": 0.0,
            "reason": _sh_reason,
            "classical_rule": adv_shi.get("classical_rule", ""),
            "scenario": adv_shi.get("scenario", ""),
            "scenario_interpretation": adv_shi.get("scenario_interpretation", ""),
        })
    # 13. 病药（有界加减，见 5.6）
    if bing_yao_adjustment != 0:
        factor_contributions.append({
            "name": "病药",
            "factor": "bing_yao",
            "score": round(bing_yao_adjustment, 2),
            "reason": "；".join(bing_yao_reasons) if bing_yao_reasons else "病药平衡",
        })
    # 按绝对贡献度排序（影响最大的排前面）
    factor_contributions.sort(key=lambda x: abs(x["score"]), reverse=True)
    return factor_contributions


# ═══ chain_step5_conf.py ═══


def _assess_signal_strength(
    step3_data: dict,
    step4_data: dict,
    final_score: float,
    strength_level: str,
) -> int:
    """评估信号强度 0-100：旺+原神+清晰信号 → 高；休囚/旬空月破+忌神克 → 低。

    该值为信号一致性得分（非概率），反映旺衰/旬空/动变等维度的一致性。
    """
    strength = 70  # 基础信号强度

    # 旺衰修正
    if strength_level in ("极旺", "旺"):
        strength += 10
    elif strength_level in ("极弱", "弱"):
        strength -= 15

    # 旬空修正
    if step3_data.get("is_empty"):
        strength -= 10

    # 月破修正
    if step3_data.get("is_month_break"):
        strength -= 10

    # 动变一致性
    net_effect = step4_data.get("net_effect", 0)
    if abs(net_effect) > 1.5:
        strength += 5  # 动变方向明确
    elif abs(net_effect) < 0.3:
        strength -= 5  # 动变方向不明，降低信号强度

    # 最终分极端值提升信号强度
    if final_score > 4.0 or final_score < 1.0:
        strength += 5

    return max(30, min(95, strength))


def _assess_confidence(*args, **kwargs) -> int:
    """向后兼容别名：已重命名为 _assess_signal_strength。"""
    return _assess_signal_strength(*args, **kwargs)


def _strength_to_text(strength: int) -> str:
    """信号强度一致性描述。"""
    if strength >= 80:
        return CONF_TXT["high"]["text"]
    elif strength >= 60:
        return CONF_TXT["medium"]["text"]
    elif strength >= 40:
        return CONF_TXT["medium_low"]["text"]
    else:
        return CONF_TXT["low"]["text"]


def _confidence_to_text(*args, **kwargs) -> str:
    """向后兼容别名：已重命名为 _strength_to_text。"""
    return _strength_to_text(*args, **kwargs)


def _compose_synthesis_summary(**kw) -> str:
    """综合步骤：先说结论，再说依据，分数只作备查。"""
    verdict = kw.get("verdict") or ""
    vdesc = kw.get("verdict_desc") or ""
    score = kw.get("final_score")
    level = kw.get("strength_level") or ""
    parts = [f"综合来看，断为{verdict}。"]
    if vdesc:
        parts.append(vdesc.rstrip("。") + "。")
    supports = []
    concerns = []
    # 旺衰
    lv_say = {
        "极旺": FREASON["lv_ji_wang"]["text"], "旺": FREASON["lv_wang"]["text"], "相": FREASON["lv_xiang"]["text"],
        "中和": FREASON["lv_zhonghe"]["text"], "中和偏旺": FREASON["lv_zhonghe_wang"]["text"], "中和偏弱": FREASON["lv_zhonghe_ru"]["text"],
        "偏弱": FREASON["lv_pianruo"]["text"], "弱": FREASON["lv_ruo"]["text"], "极弱": FREASON["lv_jiruo"]["text"], "休囚": FREASON["lv_xiqiu"]["text"],
    }.get(str(level), f"用神{level}")
    supports.append(lv_say) if any(x in str(level) for x in ("旺", "相", "中和偏旺")) else concerns.append(lv_say)
    # 动变
    net = float(kw.get("change_net_effect") or 0)
    if net > 0.3:
        supports.append(FREASON["change_help"]["text"])
    elif net < -0.3:
        concerns.append(FREASON["change_drag"]["text"])
    # 格局
    sp = kw.get("special_pattern") if isinstance(kw.get("special_pattern"), dict) else {}
    pat = str(sp.get("pattern") or "") if sp else ""
    if pat:
        if any(k in pat for k in ("逢合可解", "冲中逢合", "逢空即愈", "绝处逢生")):
            supports.append(f"格局「{pat}」在化解阻力")
        elif any(k in pat for k in ("逢冲", "逢合为凶", "随官", "反吟")):
            concerns.append(f"格局「{pat}」添变数")
        else:
            supports.append(f"见「{pat}」之象")
    if kw.get("pattern_verdict_note"):
        concerns.append(str(kw["pattern_verdict_note"]).rstrip("。"))
    if supports:
        parts.append(FREASON["support_prefix"]["text"] + "，".join(supports) + "。")
    if concerns:
        parts.append(FREASON["concern_prefix"]["text"] + "，".join(str(c) for c in concerns if c) + "。")
    if score is not None:
        parts.append(f"（量化参考 {float(score):.2f}，信号强度 {kw.get('signal_strength', kw.get('confidence','—'))}）")
    note_bits = [x for x in (
        kw.get("officer_tomb_verdict_note"), kw.get("nayin_desc"),
    ) if x]
    if note_bits:
        parts.append(" ".join(str(x) for x in note_bits))
    qt = kw.get("classical_quotes_text") or ""
    if qt:
        parts.append(str(qt).replace("【经典引文】", FREASON["quote_prefix"]["text"]))
    return "".join(parts)


# ═══ chain_step5_dates.py ═══


def _day_branch_for_date(d: datetime) -> str:
    """Gregory 日期 → 日地支（2024-01-01 = 甲子日）。"""
    delta = (d - _60_CYCLE_BASE).days
    branch_idx = delta % 12
    if branch_idx < 0:
        branch_idx += 12
    return BRANCHES[branch_idx]


def _next_date_with_day_branch(start_date: datetime, target_branch: str, max_days: int = 366) -> datetime | None:
    """下一日-branch = target_branch 的日期（前向扫描 max_days）。"""
    if not target_branch or target_branch not in set(BRANCHES):
        return None
    d = start_date + timedelta(days=1)  # start FROM tomorrow
    for _ in range(max_days):
        if _day_branch_for_date(d) == target_branch:
            return d
        d += timedelta(days=1)
    return None


def _dates_overlap(dt1: datetime | None, dt2: datetime | None, tol_days: int = 2) -> bool:
    """Check if two dates are within tol_days of each other (same event)."""
    if dt1 is None or dt2 is None:
        return False
    return abs((dt1 - dt2).days) <= tol_days


# ═══ chain_step5_timing.py ═══


def calculate_yingqi(
    step1: dict,
    step2: dict,
    step3: dict,
    step4: dict,
    step5: dict,
    base_date: datetime | None = None,
) -> dict:
    """应期精确计算（《增删卜易》《黄金策》）：{日期+规则列表, speed, summary_text}。"""
    use_god_branch = safe_get(step3, "use_god_branch", default="")
    use_god_element = safe_get(step3, "use_god_element", default="")
    strength_level = safe_get(step3, "strength_level", default="中和")
    is_empty = safe_get(step3, "is_empty", default=False)
    is_month_break = safe_get(step3, "is_month_break", default=False)
    is_an_dong = safe_get(step3, "is_an_dong", default=False)

    vacant = safe_get(step1, "vacant_branches", default=[])
    if isinstance(vacant, str):
        vacant = [vacant]
    fu_cang_detail = safe_get(step2, "fu_cang_detail", default=None)
    has_fu_cang = safe_get(step2, "has_fu_cang", default=False)

    # 原神 info
    yuan_shen_element = safe_get(step2, "yuan_shen", "element", default="")
    yuan_shen_positions = safe_get(step2, "yuan_shen", "positions", default=[])
    yuan_shen_fu_cang = safe_get(step2, "yuan_shen", "fu_cang", default=None)

    # base_date defaults to today
    base = base_date if base_date else datetime.now()

    # Collect all 应期: list of (rule_str, date_or_None, branch, description_parts)
    candidates: list[tuple[str, datetime | None, str, str]] = []

    clash = _BRANCH_CLASH_MAP.get(use_god_branch, "")

    # ===== Rule 1: 逢值逢冲 =====
    if use_god_branch:
        val_date = _next_date_with_day_branch(base, use_god_branch)
        if val_date:
            candidates.append(("逢值", val_date, use_god_branch,
                               f"用神{use_god_branch}临值"))
        if clash:
            clash_date = _next_date_with_day_branch(base, clash)
            if clash_date:
                candidates.append(("逢冲", clash_date, clash,
                                   f"用神{use_god_branch}逢冲({clash})"))

    # ===== Rule 2: 原神受克时 → 原神旺时 / 忌神受制时 =====
    if yuan_shen_positions or yuan_shen_fu_cang:
        yuan_branches: list[str] = []
        for yp in (yuan_shen_positions or []):
            yb = yp.get("earthly_branch", "")
            if yb:
                yuan_branches.append(yb)
        if yuan_shen_fu_cang:
            yfb = yuan_shen_fu_cang.get("branch", "")
            if yfb:
                yuan_branches.append(yfb)

        for yb in yuan_branches:
            ys_val = _next_date_with_day_branch(base, yb)
            if ys_val:
                candidates.append(("原神值日", ys_val, yb,
                                   f"原神{yb}当值"))

    # ===== Rule 3: 旬空 → 填实 / 冲空 =====
    if is_empty and use_god_branch:
        fill_date = _next_date_with_day_branch(base, use_god_branch)
        if fill_date:
            candidates.append(("填实(实空)", fill_date, use_god_branch,
                               f"用神{use_god_branch}出空填实"))
        if clash:
            chong_date = _next_date_with_day_branch(base, clash)
            if chong_date:
                candidates.append(("冲空", chong_date, clash,
                                   f"用神{use_god_branch}冲空({clash})"))

    # ===== Rule 4: 伏藏 → 飞神值日 / 冲开 =====
    if has_fu_cang and fu_cang_detail:
        results = fu_cang_detail.get("results", [])
        for r in results:
            fei = r.get("fei_shen", {})
            fei_branch = fei.get("branch", "")
            if fei_branch:
                fei_val = _next_date_with_day_branch(base, fei_branch)
                if fei_val:
                    candidates.append(("飞神值日(伏得出)", fei_val, fei_branch,
                                       f"飞神{fei_branch}值日"))
                fei_clash = _BRANCH_CLASH_MAP.get(fei_branch, "")
                if fei_clash:
                    fei_chong = _next_date_with_day_branch(base, fei_clash)
                    if fei_chong:
                        candidates.append(("飞神冲开", fei_chong, fei_clash,
                                           f"冲飞神{fei_branch}→{fei_clash}"))

    # ===== Rule 5: 三合局 → 待合局成 =====
    if use_god_element and use_god_element in SAN_HE:
        san_he_branches = SAN_HE[use_god_element]
        for shb in san_he_branches:
            sh_date = _next_date_with_day_branch(base, shb)
            if sh_date:
                candidates.append(("三合成局", sh_date, shb,
                                   f"{'/'.join(san_he_branches)}合{use_god_element}局"))

    # ===== Rule 6: 月破 → 逢合/逢值/填实 =====
    if is_month_break and use_god_branch:
        # 逢值填实
        val_date = _next_date_with_day_branch(base, use_god_branch)
        if val_date:
            candidates.append(("月破填实", val_date, use_god_branch,
                               f"月破用神{use_god_branch}填实"))
        # 逢合（月破逢合为解）
        he_branches = _HE_MAP.get(use_god_branch, [])
        for heb in he_branches:
            he_date = _next_date_with_day_branch(base, heb)
            if he_date:
                candidates.append(("月破逢合", he_date, heb,
                                   f"月破用神{use_god_branch}逢合{heb}"))

    # ===== Rule 7: 节奏 timing =====
    # FAST: 用神旺 + 不动/暗动 → 当日或次日
    if strength_level in ("极旺", "旺") and not is_empty and not is_month_break:
        candidates.append(("速应(旺)", base + timedelta(days=0), _day_branch_for_date(base),
                           f"用神旺相，当日可能应"))
        candidates.append(("速应(次日)", base + timedelta(days=1), _day_branch_for_date(base + timedelta(days=1)),
                           YINGQI_TXT["use_alive_next_day"]["text"]))

    # MEDIUM: 用神动化进 → 逢值日（已由逢值规则覆盖）
    # SLOW: 用神休囚 + 静 → 原神旺月/旺日
    if strength_level in ("偏弱", "弱", "极弱"):
        if yuan_shen_element:
            for yb in [yp.get("earthly_branch", "") for yp in (yuan_shen_positions or [])]:
                if yb:
                    ys_date = _next_date_with_day_branch(base, yb)
                    if ys_date and not any(_dates_overlap(ys_date, c[1]) for c in candidates):
                        candidates.append(("原神旺日(迟应)", ys_date, yb,
                                           f"用神休囚，待原神{yb}旺日"))
        # 原神旺月 fallback
        if yuan_shen_element:
            peak_months = _ELEMENT_PEAK_MONTHS.get(yuan_shen_element, [])
            for pm in peak_months:
                d = datetime(base.year, pm, 15)
                if d <= base:
                    d = datetime(base.year + 1, pm, 15)
                candidates.append(("原神旺月", d, "",
                                   f"原神{yuan_shen_element}旺月（{pm}月）"))

    # ===== Deduplicate: if 逢值 == 填实 or 逢冲 == 冲空, keep more specific rule =====
    seen_dates: dict[str, tuple[str, datetime | None, str, str]] = {}
    for rule, dt, br, desc in candidates:
        if dt is None:
            continue
        key = dt.strftime("%Y-%m-%d")
        # Prefer more specific rules over generic ones
        priority = {"飞神冲开": 6, "飞神值日(伏得出)": 5, "三合成局": 4,
                     "月破逢合": 4, "填实(实空)": 3, "冲空": 4, "逢值": 2,
                     "逢冲": 2, "原神值日": 2, "月破填实": 3,
                     "速应(旺)": 1, "速应(次日)": 1, "原神旺日(迟应)": 1,
                     "原神旺月": 0}
        existing = seen_dates.get(key)
        if existing is None or priority.get(rule, 0) > priority.get(existing[0], 0):
            seen_dates[key] = (rule, dt, br, desc)

    unique_sorted = sorted(seen_dates.values(), key=lambda x: x[1] or datetime.max if x[1] else datetime.max)
    top5 = unique_sorted[:5]

    # ===== Build result =====
    dates_list = []
    for rule, dt, br, desc in top5:
        dates_list.append({
            "rule": rule,
            "date": dt.strftime("%Y-%m-%d") if dt else None,
            "branch": br,
            "description": desc,
        })

    if not dates_list:
        speed = YINGQI_TXT["no_yingqi"]["text"]
    elif any(d["rule"].startswith("速应") for d in dates_list):
        speed = YINGQI_TXT["speed_fast_desc"]["text"]
    elif any(d["rule"] in ("逢值", "逢冲", "三合成局") for d in dates_list):
        speed = YINGQI_TXT["speed_medium_desc"]["text"]
    else:
        speed = YINGQI_TXT["speed_slow_desc"]["text"]

    if dates_list:
        date_strs = "、".join(f"{d['date']}({d['rule']})" for d in dates_list if d["date"])
        summary = f"应期（{speed}）：{date_strs}"
    else:
        summary = f"应期（{speed}）：难以确定具体日期，以用神旺衰断迟速"

    return {
        "dates": dates_list,
        "speed": speed,
        "summary_text": summary,
        "use_god_branch": use_god_branch,
        "use_god_element": use_god_element,
        "strength_level": strength_level,
        "method": "增删易/黄金策规则→日历日期",
    }


__all__ = [
    "step5_synthesize",
    "compute_spirit_adjustment",
    "compute_advanced_adjustments",
    "compute_fu_shen_adjustment",
    "compute_classical_adjustment",
    "detect_xing_he_conflict",
    "compute_bing_yao_adjustment",
    "apply_verdict_overrides",
    "build_factor_contributions",
    "_assess_signal_strength",
    "_assess_confidence",
    "_strength_to_text",
    "_confidence_to_text",
    "_compose_synthesis_summary",
    "_day_branch_for_date",
    "_next_date_with_day_branch",
    "_dates_overlap",
    "calculate_yingqi",
]
