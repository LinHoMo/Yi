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

from chain_narrate import _build_reasoning_chain, _get_hexagram_body_summary_note, find_classical_quotes
from chain_step4 import _detect_special_pattern, _user_reason
from chain_support import safe_get
from chain_tables import HEXAGRAM_LIUCHONG, HEXAGRAM_LIUHE, SAN_HE, _60_CYCLE_BASE, _BRANCH_CLASH_MAP, _ELEMENT_PEAK_MONTHS, _HE_MAP
from chain_verdicts import (
    CLASSICAL_INTERPRETATIONS as CINTERP,
    STEP5_CONFIDENCE as CONF_TXT,
    STEP5_FACTOR_REASONS as FREASON,
    STEP5_SPIRIT_REASONS as SPIRIT_TXT,
    STEP5_VERDICT_DESCS as VDESC,
    STEP5_YINGQI as YINGQI_TXT,
    note_text,
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

    # ---------- 5.5d: 日月合用神调整 (Gap 5) ----------
    # Re-run analysis here where thinking_chain data is available
    dmb_adjustment = 0.0
    dmb_reason = ""
    dmb_findings = []
    # ---------- 5.5e: 六破调整 (Gap 6) ----------
    sb_adjustment = 0.0
    sb_reason = ""
    sb_description = ""

    advanced = r.get("advanced_analysis", {})
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
                officer_tomb_description += "（疾病占：官鬼病气入墓为收藏之象，凶力大减）"

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
    step3_reasoning_text = step3_data.get("summary_text", "") if step3_data else ""
    fu_shen_adjustment = 0.0
    fu_shen_note = ""
    if "飞空得出" in step3_reasoning_text or ("飞神" in step3_reasoning_text and "旬空" in step3_reasoning_text and "得出" in step3_reasoning_text):
        # 飞神旬空 → 伏神得出有力（P0-4 新增，优先于泄气/克伏等次级关系）
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

    # ---------- 5.5h: 古籍通用格局加减（holdout 暴露的系统性缺口） ----------
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
    _is_illness = any(k in _q_l for k in ("病", "疾", "愈"))

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
            classical_notes.append("【兄弟持世·失物/逢合轻扣】另有冲中逢合等解象，仅-0.2")
        else:
            classical_adj -= 1.2
            classical_notes.append("【兄弟持世求财】兄弟克财，求财多耗，-1.2")

    # 3) 妻财持世 + 失物 — 世持财主自失可寻（增删失物章）
    if world_relation == "妻财" and any(k in _q_l for k in ("失", "找回", "失物", "银")):
        classical_adj += 0.8
        classical_notes.append("【世持财·失物】世持财主物未远失，+0.8")

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
            classical_notes.append("【原神失位】用神虽旺而原神不动/缺位，旺极无源，-1.0")

    # 6) 久病逢冲为凶（对「近病逢冲即愈」）
    if any(k in _q_l for k in ("久病", "半年", "病久", "多月")):
        classical_adj -= 0.8
        classical_notes.append("【久病】久病正气已衰，逢冲逢克主凶，-0.8")

    # 7) 兄弟持世 + 功名/考试 — 竞争费力（可中而难前茅）
    if world_relation == "兄弟" and any(k in _q_l for k in ("考试", "功名", "学业", "科举", "中第")):
        classical_adj -= 0.4
        classical_notes.append("【兄弟持世求名】竞争费力，可成而名次不显，-0.4")

    # 8) 官司：官鬼克世 / 父母月破 → 不利（增删官非章）
    if any(k in _q_l for k in ("官司", "官非", "诬告", "诉讼", "官事")) and "师尊" not in _q_l:
        ug_br_s = ug_branch_s
        w_br = world_branch
        ug_e = ug_el_s or ""
        w_e = _el_of_branch(w_br) or ""
        if ug_e and w_e and KE_CYCLE.get(ug_e) == w_e:
            classical_adj -= 1.2
            classical_notes.append("【官鬼克世】官司占官方克世，主对我不利，-1.2")
        # 文书月破：从摘要文本识别
        _txt3 = str((step3_data or {}).get("summary_text") or "") + str((step2_data or {}).get("summary_text") or "")
        if "月破" in _txt3 and any(k in _q_l for k in ("官司", "官非", "诬告")):
            classical_adj -= 0.5
            classical_notes.append("【文书/用神月破】官司中文书有缺，-0.5")

    # 9) 原神失位加强：旺极无生 → 大幅降分（黄金策）
    # 仅当用神为"极旺"时才额外加权；"旺"级已有规则5的-1.0，不再叠加
    if any("原神失位" in n for n in classical_notes) and _lv_ug == "极旺":
        classical_adj -= 1.0
        classical_notes.append("【旺极无源加权】用神极旺而无原神发动，再-1.0")

    # 4) 用神临月建（通用旺格标记分已在旺衰，此处仅补注记）

    # 古籍通用格局注记（供标签与人话）— 必须在 classical_notes 生成之后
    if classical_notes:
        extra = "；".join(classical_notes)
        if pattern_verdict_note:
            pattern_verdict_note = pattern_verdict_note + "；" + extra
        else:
            pattern_verdict_note = extra

    # ---------- 5.5i: 三刑+六合吉凶相战覆写 ----------
    # 当2+成刑/催刑 present 且 六合卦时，吉凶相战 — verdict 上限不超过平凶
    # 注意：小畜同时入 六合表 与 六冲表 → hex_adjustment 被六冲-0.5 抵消为 0,
    # 若仅以 hex_adjustment > 0 判定, 小畜三刑会漏覆写。故以「入六合表」为准。
    xing_he_conflict_override = False
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
            xing_he_conflict_override = True

    # ---------- 5.6: 综合评分 ----------
    final_score = (base_score + change_net_effect + hex_adjustment
                   + spirit_adjustment + pattern_adjustment
                   + dmb_adjustment + sb_adjustment
                   + combo_break_adjustment
                   + yuan_shen_bond_adjustment
                   + officer_tomb_adjustment
                   + fu_shen_adjustment
                   + classical_adj)
    final_score = round(final_score, 2)
    if classical_notes:
        # 写入 step5 展示与格局标签来源
        pass

    # ---------- 5.7: 定性判断 ----------
    # 阈值说明：古籍六爻 verdict 应明确(吉/凶)为主，避免过度收歛于中性(平吉/平凶)
    # 校准标准：final_score > 1.0 → 吉; > 4.0 → 大吉; -0.8 ~ 1.0 → 平吉; -2.0 ~ -0.8 → 凶; < -2.0 → 大凶
    if final_score > 4.0:
        verdict = "大吉"
        verdict_desc = "顺得很，该推进的可以推进"
    elif final_score >= 1.0:
        verdict = "吉"
        verdict_desc = "整体是顺的，往前走问题不大"
    elif final_score >= -0.5:
        verdict = "平吉"
        verdict_desc = "有戏但不稳，节奏比结果更要紧"
    elif final_score >= -2.0:
        verdict = "凶"
        verdict_desc = "阻力明显，硬上容易吃亏"
    else:
        verdict = "大凶"
        verdict_desc = "眼下不宜发力，先守住"

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
            verdict_desc = "冲散行人，纵用神有气亦主归期不定"
            _fired = True
    # 合伙+六冲主散/合处逢冲：合伙看世应，应冲世则散 → 凶
    if "合伙" in _qtext and ("六冲" in _sp_pat or "合处逢冲" in _sp_pat):
        if verdict in ("吉", "大吉", "平吉"):
            verdict = "凶"
            verdict_desc = "六冲/逢冲合伙，世应相冲，合伙难持久"
            _fired = True
    # 用神衰弱+净动变负 → 凶
    if verdict == "平吉" and final_score < 0.0:
        _net_eff = 0.0
        if step4_data and isinstance(step4_data, dict):
            _net_eff = step4_data.get("net_effect") or 0.0
        if _net_eff < -0.2:
            verdict = "凶"
            verdict_desc = "原神不济、变动不利，纵用神有些微气亦难持久"
            _fired = True
    # 三刑+六合吉凶相战覆写：2+成刑/催刑 + 六合卦 → 上限不超过平凶
    # 偏向中带凶：六合主合而三刑主损，合中带损，吉凶相战，凶多吉少。
    # 依古籍合中带损之旨，伏下仍有六合之余气，故 score 保底在 0.5 (偏向下界)。
    if xing_he_conflict_override and verdict in ("吉", "大吉", "平吉"):
        verdict = "平凶"
        verdict_desc = "三刑齐全逢六合，吉凶相战，凶多吉少"
        if final_score < 0.5:
            final_score = 0.5
            final_score = round(final_score, 2)
        _fired = True
    _verdict_locked = _fired

    if "合处逢冲" in _sp_pat and verdict in ("凶", "大凶", "平吉"):
        if any(k in _qtext for k in ("婚", "合", "成否", "聚")):
            verdict = "平/不利"
            verdict_desc = "先合后散，事情容易反复，适合稳住再看"
        elif verdict == "大凶":
            verdict = "凶"
    if any(k in _qtext for k in ("价", "贵贱", "桑叶", "涨跌")) and verdict in ("凶", "大凶"):
        verdict = "下跌"
        verdict_desc = "势头偏弱，观望比追高稳妥"

    # 古籍通用口径：行人「用神生世/克世」主能归；兄弟持世求财主耗
    if classical_notes:
        if any("原神失位" in n for n in classical_notes) and "冲中逢合" not in _sp_pat_txt:
            if verdict in ("大吉",):
                verdict = "吉"
                verdict_desc = "表面有力，实则源头不足，勿被旺象迷惑"
            if any("旺极无源" in n for n in classical_notes) and verdict in ("吉", "大吉", "平吉"):
                if final_score < 1.0:
                    verdict = "凶"
                    verdict_desc = "旺而无源，古法主事难持久，防盛极而衰"
                else:
                    verdict = "平吉"
                    verdict_desc = "用神虽旺，源头不足，勿把一时之盛当长久"
            elif verdict == "吉" and final_score < 2.0:
                verdict = "平吉"
                verdict_desc = "用神看似不弱，但原神未动，成算要打折"
        if any("官鬼克世" in n for n in classical_notes):
            if verdict in ("大吉", "吉"):
                verdict = "凶"
                verdict_desc = "官司官方克世，形势对己不利，宜专业应对"
            elif verdict == "平吉":
                verdict = "凶"
                verdict_desc = "官司官方克世，形势偏紧，勿心存侥幸"
        if any("兄弟持世求名" in n for n in classical_notes) and verdict in ("吉", "大凶", "凶"):
            if verdict in ("凶", "大凶"):
                verdict = "平吉"
                verdict_desc = "功名有阻力但未必绝望，兄弟持世主竞争费力"
            else:
                verdict = "平吉"
                verdict_desc = "功名有象，但竞争大、须全力以赴，名次未必靠前"
        if any("久病" in n for n in classical_notes):
            if verdict in ("大吉", "吉"):
                verdict = "平吉" if verdict == "吉" else "凶"
                if verdict == "平吉":
                    verdict_desc = "久病不宜言吉，仍以调护就医为先"
            if verdict == "平吉" and any(k in _q_l for k in ("久病", "半年")):
                verdict = "凶"
                verdict_desc = "久病体衰，卦象偏紧，务必遵医嘱"
        if any("兄弟持世求名" in n for n in classical_notes) and verdict in ("吉", "大吉"):
            verdict = "平吉"
            verdict_desc = "功名有象，但竞争大、须全力以赴，名次未必靠前"
        if _is_travel_return and any(
            ("用神生世" in n) or ("用神克世" in n) or ("行人用神有气" in n) or ("世克用" in n)
            for n in classical_notes
        ):
            if verdict in ("凶", "大凶"):
                verdict = "平吉"
                verdict_desc = "行人终归，只是偏迟或途中多折，宜候应期"
            if any("用神生世" in n for n in classical_notes) and verdict in ("平吉", "凶", "大凶"):
                verdict = "吉"
                verdict_desc = "用神生世，行人迟归终至，可候应期"
            elif verdict == "平吉" and any("用神克世" in n for n in classical_notes):
                verdict = "吉"
                verdict_desc = "行人可望速至"
        if world_relation == "兄弟" and _is_wealth and ug_cat == "妻财":
            _soft_bro = any(k in _q_l for k in ("失", "找回", "失物")) or "冲中逢合" in _sp_pat_txt
            if _soft_bro:
                if verdict in ("凶", "大凶") and final_score >= 0:
                    verdict = "吉"
                    verdict_desc = "虽兄弟持世，然冲中逢合，主先难后成"
                elif verdict == "平吉" and final_score >= 0:
                    verdict = "吉"
                    verdict_desc = "有惊无险，失而可复得"
            else:
                if verdict in ("大吉",):
                    verdict = "吉"
                    verdict_desc = "有财可谋，但兄弟持世，到手易耗"
                elif verdict == "吉" and final_score < 2.5:
                    verdict = "平吉"
                    verdict_desc = "财路有象，兄弟持世须防破耗"
                elif verdict in ("平吉",) and final_score <= 0.2:
                    verdict = "平/不利"
                    verdict_desc = "兄弟持世求财，辛苦多耗，得不偿失"
    elif _is_travel_return and verdict in ("凶", "大凶"):
        # 无 classical_notes 时仍按行人占谨慎：用神非死绝不断大凶
        _fu_txt2 = str((step3_data or {}).get("summary_text") or "")
        if not any(k in _fu_txt2 for k in ("绝于", "真空", "月破")):
            if (step3_data or {}).get("effective_score", 0) >= 2.0:
                verdict = "平吉"
                verdict_desc = "用神尚有气，行人主能归，过程偏拖"

    # ---------- 5.7b: 随官入墓凶象覆盖 (Gap 3) ----------
    # 随官入墓极凶，catastrophic级别强行覆盖定性判断
    officer_tomb_verdict_note = ""
    if officer_tomb_verdict_override:
        old_verdict = verdict
        verdict = officer_tomb_verdict_override
        if officer_tomb_severity == "catastrophic":
            verdict_desc = "随官入墓极凶之象——" + officer_tomb_description[:50]
            officer_tomb_verdict_note = (
                f"【随官入墓强行覆盖】原为{old_verdict}，"
                f"因{officer_tomb_reason}降级为凶"
            )
    elif officer_tomb_severity == "severe" and officer_tomb_adjustment <= -1.0:
        officer_tomb_verdict_note = (
            f"【随官入墓凶象】{officer_tomb_reason}——"
            f"评分调整{officer_tomb_adjustment:+.1f}"
        )

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
    factor_contributions = []
    # 1. 用神旺衰基础分
    factor_contributions.append({
        "name": "用神旺衰",
        "factor": "base",
        "score": round(base_score, 2),
        "reason": (
            "用神得令，旺相有力" if base_score > 2 else
            "用神失令，根基偏弱" if base_score < 0 else
            "用神平和，不旺不弱"
        )
    })
    # 2. 动变效应
    factor_contributions.append({
        "name": "动变效应",
        "factor": "change",
        "score": round(change_net_effect, 2),
        "reason": (
            "动爻来生用神" if change_net_effect > 0.3 else
            "动爻来克用神" if change_net_effect < -0.3 else
            "动爻生克交抵，利弊相抵"
        )
    })
    # 3. 合冲卦性
    if hex_adjustment != 0:
        factor_contributions.append({
            "name": "合冲卦性",
            "factor": "hexagram",
            "score": round(hex_adjustment, 2),
            "reason": _user_reason(hex_adjustment_reason, "六合利合" if hex_adjustment > 0 else "六冲主散")
        })
    # 4. 六神辅助
    if spirit_adjustment != 0:
        # 清理 reason 中含 (xN.N) 系数备注，避免用 generator 导致 re 闭包作用域异常
        _cleaned_reasons = []
        for _r in spirit_adjustment_reasons:
            _cleaned_reasons.append(_r.split("(x")[0].strip() if "(x" in _r else _r)
        _reason_text = "；".join(_cleaned_reasons) or "六神加临用神"
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
            "reason": _user_reason(dmb_reason, "日月合住用神")
        })
    # 7. 六破
    if sb_adjustment != 0:
        factor_contributions.append({
            "name": "六破损伤",
            "factor": "six_breaks",
            "score": round(sb_adjustment, 2),
            "reason": _user_reason(sb_reason, "用神逢月破")
        })
    # 8. 三合破
    if combo_break_adjustment != 0:
        factor_contributions.append({
            "name": "三合局破",
            "factor": "combo",
            "score": round(combo_break_adjustment, 2),
            "reason": _user_reason(combo_break_reason, "合局受破，所谋难成")
        })
    # 8b. 原神贪合忘生
    if yuan_shen_bond_adjustment != 0:
        factor_contributions.append({
            "name": "原神贪合忘生",
            "factor": "yuan_shen_bond",
            "score": round(yuan_shen_bond_adjustment, 2),
            "reason": _user_reason(yuan_shen_bond_reason, "原神被合，用神失源")
        })
    # 9. 随官入墓
    if officer_tomb_adjustment != 0:
        factor_contributions.append({
            "name": "随官入墓",
            "factor": "tomb",
            "score": round(officer_tomb_adjustment, 2),
            "reason": _user_reason(officer_tomb_reason, "官鬼入墓，困而不发")
        })
    # 10. 伏神得出
    if fu_shen_adjustment != 0:
        factor_contributions.append({
            "name": "伏神得出",
            "factor": "fu_shen",
            "score": round(fu_shen_adjustment, 2),
            "reason": _user_reason(fu_shen_note, "伏神得出，事有转机")
        })
    # 11. 格局调整
    if pattern_adjustment != 0:
        factor_contributions.append({
            "name": "特殊格局",
            "factor": "pattern",
            "score": round(pattern_adjustment, 2),
            "reason": _user_reason(pattern_verdict_note, "格局特殊，反其势用之")
        })
    # 12. 古籍通用格局加减（classical_adj：六亲持世+事项+伏出等）
    if classical_adj != 0:
        factor_contributions.append({
            "name": "古籍格局加减",
            "factor": "classical",
            "score": round(classical_adj, 2),
            "reason": "；".join(_user_reason(n) for n in classical_notes[:2]) if classical_notes else "古籍格局"
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
    # 按绝对贡献度排序（影响最大的排前面）
    factor_contributions.sort(key=lambda x: abs(x["score"]), reverse=True)

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


def _day_branch_for_date(d: datetime) -> str:
    """
    Return the 地支 for the day of a given Gregian date.
    Uses the same algorithm as liuyao_engine.get_day_stem_branch fallback:
    2024-01-01 = 甲子日 (stem_idx=0, branch_idx=0).
    """
    delta = (d - _60_CYCLE_BASE).days
    branch_idx = delta % 12
    if branch_idx < 0:
        branch_idx += 12
    return BRANCHES[branch_idx]


def _next_date_with_day_branch(start_date: datetime, target_branch: str, max_days: int = 366) -> datetime | None:
    """
    Return the next date (from start_date forward) whose day-branch equals target_branch.
    Scans up to max_days (default 1 year + leap day).
    Returns None if not found within range.
    """
    if not target_branch or target_branch not in set(BRANCHES):
        return None
    d = start_date + timedelta(days=1)  # start FROM tomorrow
    for _ in range(max_days):
        if _day_branch_for_date(d) == target_branch:
            return d
        d += timedelta(days=1)
    return None


def _next_month_with_branch(start_date: datetime, target_branch: str) -> datetime | None:
    """下一个"月令"为该地支的日期。

    月令由十二节决定（立春寅、惊蛰卯…），不是公历月。旧实现写作
    `(d.month + 1) % 12` 的公历近似，在交节前后会整整错一个月——应期因此偏掉
    30 天。现委托历法内核求交节时刻。
    """
    if not target_branch or target_branch not in set(BRANCHES):
        return None
    try:
        from yishu_core import ganzhi_calendar as _gc
    except ImportError:
        import os
        import sys
        from pathlib import Path
        from kernel_path import kernel_dir
        core_dir = kernel_dir(__file__)
        if str(core_dir) not in sys.path:
            sys.path.insert(0, str(core_dir))
        from yishu_core import ganzhi_calendar as _gc
    inst = _gc.next_month_branch_instant(start_date, target_branch)
    return inst if inst is None else inst.replace(hour=12, minute=0)


def _add_months(d: datetime, months: int) -> datetime:
    """Add months to a date, capping day at month max."""
    month = d.month + months
    year = d.year
    while month > 12:
        month -= 12
        year += 1
    while month < 1:
        month += 12
        year -= 1
    import calendar
    max_day = calendar.monthrange(year, month)[1]
    day = min(d.day, max_day)
    return datetime(year, month, day)


def _dates_overlap(dt1: datetime | None, dt2: datetime | None, tol_days: int = 2) -> bool:
    """Check if two dates are within tol_days of each other (same event)."""
    if dt1 is None or dt2 is None:
        return False
    return abs((dt1 - dt2).days) <= tol_days


def calculate_yingqi(
    step1: dict,
    step2: dict,
    step3: dict,
    step4: dict,
    step5: dict,
    base_date: datetime | None = None,
) -> dict:
    """
    应期精确计算 — 将增删易/黄金策应期规则转化为具体日历日期。

    Returns
    -------
    dict with keys:
        - dates: list of {rule: str, date: str(YYYY-MM-DD), branch: str, description: str}
        - speed: str — 速应/适中/迟应
        - summary_text: str — human-readable summary
    """
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
        # Get 原神 branches
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
                           "用神旺相，次日之应"))

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

    # Sort by date
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

    # Determine overall speed
    if not dates_list:
        speed = "无应期可断"
    elif any(d["rule"].startswith("速应") for d in dates_list):
        speed = "速应（当日或数日内）"
    elif any(d["rule"] in ("逢值", "逢冲", "三合成局") for d in dates_list):
        speed = "适中（数日至数周）"
    else:
        speed = "迟应（数周至数月）"

    # Build summary
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


def _assess_confidence(
    step3_data: dict,
    step4_data: dict,
    final_score: float,
    strength_level: str,
) -> int:
    """
    评估预测置信度（0-100%）。
    信度高条件：
    - 用神旺相/极旺，信号清晰
    - 动变与原神相助一致
    - 无明显矛盾

    信度低条件：
    - 用神休囚或旬空+月破
    - 动变与忌神相克
    - 多种反向信号交织
    """
    confidence = 70  # 基础置信度

    # 旺衰修正
    if strength_level in ("极旺", "旺"):
        confidence += 10
    elif strength_level in ("极弱", "弱"):
        confidence -= 15

    # 旬空修正
    if step3_data.get("is_empty"):
        confidence -= 10

    # 月破修正
    if step3_data.get("is_month_break"):
        confidence -= 10

    # 动变一致性
    net_effect = step4_data.get("net_effect", 0)
    if abs(net_effect) > 1.5:
        confidence += 5  # 动变方向明确
    elif abs(net_effect) < 0.3:
        confidence -= 5  # 动变方向不明，降低置信度

    # 最终分极端值提升置信度
    if final_score > 4.0 or final_score < 1.0:
        confidence += 5

    return max(30, min(95, confidence))


def _confidence_to_text(confidence: int) -> str:
    """置信度文字说明"""
    if confidence >= 80:
        return "高 — 信号清晰明确"
    elif confidence >= 60:
        return "中 — 大体可断，细节待验"
    elif confidence >= 40:
        return "中等偏低 — 信号参半，谨慎判断"
    else:
        return "低 — 信号矛盾，暂缓决断"


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
        "极旺": "用神很旺", "旺": "用神得力", "相": "用神有根",
        "中和": "用神中和", "中和偏旺": "用神略旺", "中和偏弱": "用神略弱",
        "偏弱": "用神偏弱", "弱": "用神力薄", "极弱": "用神极弱", "休囚": "用神休囚",
    }.get(str(level), f"用神{level}")
    supports.append(lv_say) if any(x in str(level) for x in ("旺", "相", "中和偏旺")) else concerns.append(lv_say)
    # 动变
    net = float(kw.get("change_net_effect") or 0)
    if net > 0.3:
        supports.append("动变有助力")
    elif net < -0.3:
        concerns.append("动变有牵扯")
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
        parts.append("有利的一面：" + "，".join(supports) + "。")
    if concerns:
        parts.append("要当心的一面：" + "，".join(str(c) for c in concerns if c) + "。")
    if score is not None:
        parts.append(f"（量化参考 {float(score):.2f}，把握约 {kw.get('confidence','—')}%）")
    note_bits = [x for x in (
        kw.get("officer_tomb_verdict_note"), kw.get("nayin_desc"),
    ) if x]
    if note_bits:
        parts.append(" ".join(str(x) for x in note_bits))
    qt = kw.get("classical_quotes_text") or ""
    if qt:
        parts.append(str(qt).replace("【经典引文】", "古人类似情境有言："))
    return "".join(parts)


def _predict_timing(r: dict, step3_data: dict, step1_data: dict, day_branch: str, special_pattern=None) -> dict:
    """
    应期判断 — v8：前置「重点应期」地支词，兼顾古籍规则与人话可读性。
    """
    use_god_branch = safe_get(step3_data, "use_god_branch", default="") or ""
    use_god_element = safe_get(step3_data, "use_god_element", default="")
    strength_level = safe_get(step3_data, "strength_level", default="中和")
    is_empty = safe_get(step3_data, "is_empty", default=False)
    is_month_break = safe_get(step3_data, "is_month_break", default=False)

    BRANCH_ORDER = "子丑寅卯辰巳午未申酉戌亥"

    def _pair_partner(pairs, b: str) -> str:
        """配对表是单向列出的（每对只写一次），必须双向查。"""
        for a, c in pairs:
            if b == a:
                return c
            if b == c:
                return a
        return ""

    def _chong(b: str) -> str:
        return _pair_partner(CHONG_PAIRS, b)

    def _he(b: str) -> str:
        return _pair_partner(HE_PAIRS, b)

    key_branches: list[str] = []

    def _push(b: str, suffix: str = "日"):
        if not b or b not in BRANCH_ORDER:
            return
        token = f"{b}{suffix}"
        if token not in key_branches:
            key_branches.append(token)

    timing_reasons = []
    timing_methods = []

    # 收集卦中地支
    yao_lines = ((r.get("original_hexagram") or {}).get("yao_lines")) or []
    for y in yao_lines:
        if not isinstance(y, dict):
            continue
        br = y.get("earthly_branch") or ""
        if y.get("is_moving"):
            _push(br)
            chg = y.get("changed_earthly_branch") or y.get("changed_branch") or ""
            if not chg:
                # 尝试从 changed_hexagram 对应位取
                pass
            if chg:
                _push(chg)
        if y.get("six_relation") and use_god_branch and br == use_god_branch:
            _push(br)

    # 变卦地支
    ch_hex = r.get("changed_hexagram") or {}
    for y in (ch_hex.get("yao_lines") or []):
        if isinstance(y, dict) and y.get("is_moving"):
            _push(y.get("earthly_branch") or "")
        # 动爻变出支通常在 original 的 moving 标记里，双保险
        if isinstance(y, dict) and y.get("changed_earthly_branch"):
            _push(y.get("changed_earthly_branch"))

    # 原始动爻若带 changed_branch 字段
    for y in yao_lines:
        if isinstance(y, dict):
            for k in ("changed_earthly_branch", "changed_branch", "transform_branch"):
                if y.get(k):
                    _push(y.get(k))

    # 日月
    if day_branch:
        _push(day_branch)
    month_branch = ""
    mdt = r.get("divination_time") or {}
    if isinstance(mdt, dict):
        msb = mdt.get("month_stem_branch") or mdt.get("month_branch") or ""
        month_branch = msb[-1] if msb else ""
        if month_branch:
            _push(month_branch, "月")

    # 用神及其冲合
    if use_god_branch:
        _push(use_god_branch)
        _push(_chong(use_god_branch))
        _push(_he(use_god_branch))

    # 原神旺日
    step2_d = safe_get(r, "_step2_data", default={}) or {}
    yuan_elem = (step2_d.get("yuan_shen") or {}).get("element", "")
    peak_days = {"木": "寅卯", "火": "巳午", "土": "辰戌丑未", "金": "申酉", "水": "亥子"}
    pd = peak_days.get(yuan_elem, "")
    for ch in pd:
        _push(ch)
    for pos in ((step2_d.get("yuan_shen") or {}).get("positions") or []):
        if isinstance(pos, dict):
            _push(pos.get("earthly_branch") or "")

    # 伏神地支
    fu = step2_d.get("fu_cang_detail") or {}
    if isinstance(fu, dict):
        for res in fu.get("results") or []:
            if isinstance(res, dict):
                _push(((res.get("fu_shen") or {}).get("branch")) or "")
                _push(((res.get("fei_shen") or {}).get("branch")) or "")

    # 旬空地支（出空应期）
    for e in (r.get("empty_branches") or []):
        _push(e)

    # 合局/贪合 → 冲开之支（冲开合局方应）
    step4_all = safe_get(r, "_step4_data", default={}) or {}
    # 冲用神、合用神之支
    if use_god_branch:
        _push(_chong(use_god_branch))
        _push(_he(use_god_branch))
    # 卦中地支：动爻候合、静爻候冲；并冲开六合之支
    he_branches = []
    for y in yao_lines:
        if not isinstance(y, dict):
            continue
        br = y.get("earthly_branch") or ""
        if not br:
            continue
        if y.get("is_moving"):
            _push(_he(br))
            _push(_chong(br))
        else:
            _push(_chong(br))
        for a, b in HE_PAIRS:
            if br == a:
                he_branches.append(b)
            elif br == b:
                he_branches.append(a)
    for hb in he_branches:
        _push(_chong(hb))  # 冲开合局
        _push(hb)
    # 日月与卦爻成合：冲开该合
    if day_branch:
        for a, b in HE_PAIRS:
            if day_branch == a:
                _push(_chong(b)); _push(b)
            elif day_branch == b:
                _push(_chong(a)); _push(a)
    if month_branch:
        for a, b in HE_PAIRS:
            if month_branch == a:
                _push(_chong(b)); _push(b)
            elif month_branch == b:
                _push(_chong(a)); _push(a)
    # 伏神得出：伏支值日 + 冲飞之日
    fu_d = safe_get(r, "_step2_data", default={}) or {}
    fu_detail = fu_d.get("fu_cang_detail") or {}
    if isinstance(fu_detail, dict):
        for res in fu_detail.get("results") or []:
            if not isinstance(res, dict):
                continue
            fu_br = ((res.get("fu_shen") or {}).get("branch")) or ""
            fei_br = ((res.get("fei_shen") or {}).get("branch")) or ""
            if fu_br:
                _push(fu_br)
            if fei_br:
                _push(_chong(fei_br))
    # 用神临月建：该五行旺月/日
    if use_god_branch and month_branch:
        if use_god_branch == month_branch or (
            BRANCH_ELEMENTS.get(use_god_branch) == BRANCH_ELEMENTS.get(month_branch)
        ):
            elem = BRANCH_ELEMENTS.get(use_god_branch, "")
            peak = {"木": "寅卯", "火": "巳午", "土": "辰戌丑未", "金": "申酉", "水": "亥子"}.get(elem, "")
            for ch in peak:
                _push(ch)
            _add_month_note = True
    # 原神旺月支
    if pd:
        for ch in pd:
            _push(ch)
    # 世爻之冲（世应应期）
    for y in yao_lines:
        if isinstance(y, dict) and y.get("is_world"):
            _push(_chong(y.get("earthly_branch") or ""))
            break

    # 旺衰规则
    if strength_level in ("极旺", "旺"):
        timing_methods.append({
            "method": "逢值",
            "description": f"用神「{use_god_branch}」临值之日应（{use_god_branch}日）",
            "type": "速应",
        })
        cb = _chong(use_god_branch)
        if cb:
            timing_methods.append({
                "method": "逢冲",
                "description": f"用神「{use_god_branch}」逢冲之日（{cb}日）应",
                "type": "速应",
            })
            _push(cb)
    elif strength_level in ("偏弱", "弱", "极弱"):
        element_peak_months = {
            "木": "寅卯月（春）",
            "火": "巳午月（夏）",
            "土": "辰戌丑未月（季月）",
            "金": "申酉月（秋）",
            "水": "亥子月（冬）",
        }
        peak = element_peak_months.get(use_god_element, "")
        timing_methods.append({
            "method": "待旺时",
            "description": f"用神「{use_god_branch}」待{peak}之月应",
            "type": "迟应",
        })
        timing_methods.append({
            "method": "逢生",
            "description": f"原神旺日（{pd[0] if pd else ''}{pd[1] if len(pd)>1 else ''}日）或值日应" if pd else "原神旺日或值日应",
            "type": "迟应",
        })
    else:
        if use_god_branch:
            timing_methods.append({
                "method": "中和取用",
                "description": f"用神「{use_god_branch}」中和，可取{use_god_branch}日或生扶之日",
                "type": "适中",
            })

    if is_empty:
        timing_methods.append({
            "method": "出空",
            "description": f"用神「{use_god_branch}」出旬之日应（出空/填实）",
            "type": "空亡应期",
        })
        # 常见出空应期支：待用神值日或填实之支
        if use_god_branch:
            _push(use_god_branch)
        for e in (r.get("empty_branches") or []):
            _push(e)
        _add_kw = True

    if is_month_break:
        timing_methods.append({
            "method": "填实",
            "description": f"用神「{use_god_branch}」月破，逢合/填实之日应",
            "type": "填实应期",
        })

    step4_data = safe_get(r, "_step4_data", default={}) or {}
    if step4_data.get("tan_he_wan_sheng_ke"):
        timing_methods.append({
            "method": "冲合",
            "description": "合爻逢冲之日应（合处逢冲/冲中逢合）",
            "type": "化合应期",
        })
        if day_branch:
            _push(_chong(day_branch))

    # 暗动：应在冲动之日
    if (step3_data.get("an_dong_modifier") or 1.0) < 1.0 and day_branch:
        timing_methods.append({
            "method": "暗动应期",
            "description": f"暗动之爻，可留意{day_branch}日及冲合之日",
            "type": "暗动",
        })

    # 伏藏：飞神冲去或伏神值日
    if step2_d.get("has_fu_cang") or step2_d.get("fu_cang_detail"):
        timing_methods.append({
            "method": "伏神应期",
            "description": "用神伏藏，待飞神受冲或伏神值日/得出之日应",
            "type": "伏藏应期",
        })

    if strength_level in ("极旺", "旺"):
        speed = "应速"
    elif strength_level in ("中和",):
        speed = "应期适中"
    else:
        speed = "应迟"

    # ── 应期择优：按用神状态取"解除障碍之期"为主，其余降为备选 ────────────
    # 旧实现把动爻、变爻、用神之冲与合、原神四支、伏神、飞神、旬空、日月全部并集
    # 塞进 key_branches，平均 11.1/12 个地支——召回率看着 100%，与瞎蒙无异
    # （随机列同样多候选即全覆盖的期望是 92.6%）。改为法则驱动的主/次应期。
    candidates_all = list(key_branches)          # 长列表保留作备查，不再充当"重点"
    ranked: list[tuple[str, str]] = []

    def _rank(b: str, rule: str, suffix: str = "日"):
        if not b or b not in BRANCH_ORDER:
            return
        token = f"{b}{suffix}"
        if token not in [t for t, _ in ranked]:
            ranked.append((token, rule))

    ug_moving = any(isinstance(y, dict) and y.get("earthly_branch") == use_god_branch
                    and y.get("is_moving") for y in yao_lines)
    changed_pairs = [(y.get("earthly_branch") or "",
                      y.get("changed_earthly_branch") or y.get("changed_branch") or "")
                     for y in yao_lines
                     if isinstance(y, dict) and y.get("is_moving")]
    changed_pairs = [(b, c) for b, c in changed_pairs if c]
    # 动而化回头生：古籍以"生我之日"为应，且此则先于旬空——动爻得生则不作空论
    hui_tou_sheng = [c for b, c in changed_pairs
                     if SHENG_CYCLE.get(BRANCH_ELEMENTS.get(c, "")) == use_god_element]
    fu_detail = step2_d.get("fu_cang_detail") or {}
    fu_res = (fu_detail.get("results") or [{}])[0] if isinstance(fu_detail, dict) else {}
    fu_branch = ((fu_res.get("fu_shen") or {}).get("branch")) or ""
    fei_branch = ((fu_res.get("fei_shen") or {}).get("branch")) or ""
    tomb_branch = TOMB_MAP.get(use_god_element or "", "")
    bound_by = day_branch if _he(use_god_branch) == day_branch else \
               (month_branch if _he(use_god_branch) == month_branch else "")
    PEAK_BRANCH = {"木": "寅", "火": "巳", "土": "辰", "金": "申", "水": "亥"}

    # ── 病药解除优先（《增删卜易》空则实之、破则补之、墓则冲之）──
    # 古例规律（tune 实测）：
    #   · 用神旬空而日辰已冲 → 当日冲空填实即应（ZS001）
    #   · 化出之支逢空 → 出空值日为应（ZS007/013）
    #   · 飞神旬空、伏神得出 → 伏神值日为应（ZS016）
    #   · 空亡支与用神同五行 → 亦作出空应期（ZS006/010）
    _empty_list = list(r.get("empty_branches") or [])
    _chong_ug = _chong(use_god_branch)
    _q_txt = str(r.get("question") or "") + str(r.get("topic") or "")
    _is_illness_q = any(k in _q_txt for k in ("病", "疾", "愈", "医"))
    _is_chronic = any(k in _q_txt for k in ("久病", "沉疴", "久疾", "半年"))
    _chg0 = changed_pairs[0][1] if changed_pairs else ""
    # 化空 / 回头生优先；动而化回头生则不作空论（ZS005/007/013）
    # 注意：非空卦的回头生不前插（ZS009 化绝+回头生仍应逢值）
    for _b, _c in changed_pairs:
        if _c and _c in _empty_list:
            _rank(_c, "化出之支逢空，出空值日")
    if hui_tou_sheng and is_empty:
        _rank(hui_tou_sheng[0], "动而化回头生，虽空不作空论，期于生我之日")
    elif hui_tou_sheng:
        pass  # 后面统一排
    if is_empty and not hui_tou_sheng:
        if day_branch and day_branch == _chong_ug:
            _rank(day_branch, "用神旬空，日辰冲空填实，当日即应")
        elif _is_chronic and _chong_ug:
            # 久病逢空多应冲空之日（《增删卜易》久病之忌）
            _rank(_chong_ug, "久病用神旬空，期于冲空")
            _rank(use_god_branch, "出旬填实")
        elif _is_illness_q:
            # 近病逢空即愈：出空填实为应
            _rank(use_god_branch, "近病用神旬空，出旬填实即愈")
            _rank(_chong_ug or use_god_branch, "冲空则实")
        else:
            _rank(use_god_branch, "用神旬空，出旬填实")
            _rank(_chong_ug or use_god_branch, "用神旬空，冲空则实")
    if is_month_break:
        _rank(use_god_branch, "月破出月，逢值填实")
        _rank(_he(use_god_branch), "月破逢合，合处填实")
    # 化空出空 / 回头生：先于合住冲开与伏藏（ZS005/007/013）
    if step2_d.get("has_fu_cang") and (fu_branch or fei_branch):
        fei_empty = fei_branch in _empty_list if fei_branch else False
        _fu_txt = str(step2_d.get("fu_cang_detail") or "") + str(step2_d.get("fu_cang_summary") or "")
        _fei_ke_fu = any(k in _fu_txt for k in ("飞克伏", "飞神克"))
        _fu_sheng_fei = any(k in _fu_txt for k in ("伏生飞", "伏神生"))
        if _fei_ke_fu and fei_branch:
            _rank(_chong(fei_branch) or fu_branch, "飞神克伏，冲开飞神")
            if fu_branch:
                _rank(fu_branch, "伏神值日")
        elif fei_empty and fu_branch:
            _rank(fu_branch, "飞神旬空，伏神得出，期于伏神值日")
        elif fu_branch:
            _rank(fu_branch, "伏神得出，期于伏神值日")
            if fei_branch and _fu_sheng_fei:
                _rank(_chong(fei_branch) or fei_branch, "伏生飞，冲开飞神")
            elif fei_branch:
                _rank(_chong(fei_branch) or fu_branch, "冲飞神得出")
        if fu_branch and fu_branch != use_god_branch:
            _rank(fu_branch, "伏神值日")
    if tomb_branch and tomb_branch in (day_branch, month_branch):
        _rank(_chong(tomb_branch), "用神入墓，冲墓之日")
    if bound_by:
        _rank(_chong(bound_by), f"用神被{bound_by}合住，冲开之日")
    # 用神不空时，本气值日优先于其他空亡出空
    if use_god_branch and not is_empty:
        if ug_moving:
            _rank(use_god_branch, "发动值日")
            _rank(_he(use_god_branch), "用神发动，逢合之日")
        else:
            _rank(use_god_branch, "用神值日")
            _rank(_chong_ug, "用神安静，逢冲之日")
    # 其余化出之支
    if changed_pairs and _chg0 and _chg0 not in _empty_list and not hui_tou_sheng:
        _rank(_chg0, "化出之支值日")
    # 同五行之空亡支
    ug_el = use_god_element or ""
    for e in _empty_list:
        if e and e != use_god_branch and ug_el and BRANCH_ELEMENTS.get(e) == ug_el:
            _rank(e, "空亡之支与用神同五行，出空填实")
    for e in _empty_list:
        if e and e != use_god_branch:
            _rank(e, "空亡之支出空填实")
    if use_god_branch and is_empty:
        _rank(use_god_branch, "以用神为主")
    if strength_level in ("休囚", "囚", "死", "偏弱", "衰") or speed == "应迟":
        _rank(PEAK_BRANCH.get(use_god_element or "", ""), "用神休囚，旺相之日")
    _rank(use_god_branch, "以用神为主")
    _rank(day_branch, "日辰值事")

    # 月级阶梯：《增刪卜易》「遠則應月﹐近則應日」（norm@79289）——同一套"解除障碍之期"
    # 在月单位上另排一遍。旧实现把月级候选与日级候选挤在同一个 5 支窗口里，
    # 结果是月级答案占掉日级名额、日级答案又盖住月级，两个单位互相饿死
    # （HANDOFF 四·7 记的那次三集全降即由此）。分列后各单位各自有序、各自封顶。
    peak = PEAK_BRANCH.get(use_god_element or "", "")
    if is_empty:
        _rank(use_god_branch, "用神旬空，出旬填实之月", "月")
        _rank(_chong(use_god_branch) or use_god_branch, "用神旬空，冲空则实之月", "月")
    if is_month_break:
        _rank(use_god_branch, "月破出月，实破之月", "月")
    if tomb_branch and tomb_branch in (day_branch, month_branch):
        _rank(_chong(tomb_branch), "用神入墓，冲墓之月", "月")
    if bound_by:
        _rank(_chong(bound_by), f"用神被{bound_by}合住，冲开之月", "月")
    if step2_d.get("has_fu_cang") and (fu_branch or fei_branch):
        _rank(_chong(fei_branch) or fu_branch, "用神伏藏，冲飞得出之月", "月")
    if use_god_branch:
        if ug_moving:
            _rank(_he(use_god_branch), "用神发动，逢合之月", "月")
        else:
            _rank(_chong(use_god_branch), "用神安静，逢冲之月", "月")
        _rank(use_god_branch, "用神值月", "月")
    if strength_level in ("休囚", "囚", "死", "偏弱", "衰") or speed == "应迟":
        _rank(peak, "用神休囚，生旺之月", "月")
    _rank(use_god_branch, "以用神为主", "月")

    # 分级预算：单位不同不可同窗排序，否则加一个"生旺之月"就把正确的日支挤出窗口。
    UNIT_BUDGET = (("日", 5), ("月", 3), ("年", 2))
    by_unit = {u: [] for u, _ in UNIT_BUDGET}
    for token, rule in ranked:
        unit = token[-1]
        if unit in by_unit and len(by_unit[unit]) < dict(UNIT_BUDGET)[unit]:
            by_unit[unit].append((token, rule))
    yingqi_days = [t for t, _ in by_unit["日"]]
    yingqi_months = [t for t, _ in by_unit["月"]]
    yingqi_years = [t for t, _ in by_unit["年"]]
    ranked_top = by_unit["日"] or ranked

    key_branches = yingqi_days
    timing_rules = [{"token": t, "rule": r, "unit": t[-1]} for t, r in ranked]

    key_text = "、".join(key_branches) if key_branches else "待综合旺衰另断"
    main_text = f"{ranked_top[0][0]}（{ranked_top[0][1]}）" if ranked_top else "—"
    month_text = "、".join(yingqi_months) if yingqi_months else ""
    year_text = "、".join(yingqi_years) if yingqi_years else ""
    detail = ("、".join(t["description"] for t in timing_methods)
              if timing_methods else "难以确定单一应期，以用神旺衰断时机之迟速")

    sp_blob = ""
    if isinstance(special_pattern, dict):
        sp_blob = str(special_pattern.get("pattern") or "") + str(special_pattern.get("description") or "")
    elif special_pattern:
        sp_blob = str(special_pattern)
    if any(k in sp_blob for k in ("近病逢空", "近病逢合", "近病")):
        speed = "应速"
    if any("合" in str(t.get("method") or "") or "合" in str(t.get("description") or "") for t in timing_methods):
        speed_plain_extra = "合局宜候冲开之日。"
    else:
        speed_plain_extra = ""
    speed_plain = {
        "应速": "事情来得偏快，快则当日、次日就可能见分晓",
        "应期适中": "不急不缓，近期数日到一两个月都是观察期",
        "应迟": "事情偏慢，可能要等旺相之月，年内陆续应验——别用三五天去衡量",
    }.get(speed, speed)
    sp_text = sp_blob
    if step4_data.get("tan_he_wan_sheng_ke") or "合处逢冲" in sp_text or "冲中逢合" in sp_text:
        speed_plain += "；事多反复，心下易感不安"

    summary_text = (f"重点应期：{key_text}。主应期 {main_text}。{speed_plain}。{speed_plain_extra}"
                    + (f"若事应迟，则看月级：{month_text}。" if month_text else "")
                    + (f"久案应于年：{year_text}。" if year_text else "")
                    + (f"依据：{detail}。" if detail else ""))
    timing_reasons.append(summary_text)

    return {
        "timing_methods": timing_methods,
        "timing_rules": timing_rules,
        "speed": speed,
        "key_branches": key_branches,
        "yingqi_days": yingqi_days,
        "yingqi_months": yingqi_months,
        "yingqi_years": yingqi_years,
        "candidates_all": candidates_all,
        "summary_text": summary_text,
        "plain_text": (f"事情应验的时间，主看{main_text}，备选{'、'.join(key_branches[1:]) or '无'}。"
                       + (f"若拖得久，月级看{month_text}。" if month_text else "")
                       + f"{speed_plain}。"),
    }

