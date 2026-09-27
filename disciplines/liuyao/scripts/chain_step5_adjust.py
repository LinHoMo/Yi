# -*- coding: utf-8 -*-
"""六爻思维链 step5 的加减分项与断语覆写（自 chain_step5.step5_synthesize 按职责切出）。

纯搬移不改写逻辑：每个函数对应原巨石函数中的一段编号注释（5.4 / 5.5d…5.13）。
本模块**不 import chain_step5**，依赖单向：chain_step5 → chain_step5_adjust。

验收口径：拆分前后 step5 输出与下游叙述必须逐例一致（零指纹漂移）。
"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    BRANCH_ELEMENTS,
    KE_CYCLE,
    SHENG_CYCLE,
)

from chain_step4 import _user_reason
from chain_support import safe_get
from chain_tables import HEXAGRAM_LIUHE
from chain_verdicts import (
    STEP5_FACTOR_REASONS as FREASON,
    STEP5_SPIRIT_REASONS as SPIRIT_TXT,
    STEP5_VERDICT_DESCS as VDESC,
    note_text,
    vdesc,
)


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
    }


# ---------------------------------------------------------------- 伏神格局
def compute_fu_shen_adjustment(step3_data: dict, r: dict) -> tuple:
    """伏神格局调整（飞空得出 / 飞来生伏 / 绝于飞 / 飞克伏 / 伏泄气）。"""
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
    """5.5h 古籍通用格局加减。同时产出供后续覆写复用的上下文 ctx。"""
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
    """三刑+六合吉凶相战：2+ 成刑/催刑 且 六合卦 → 覆写上限不超过平凶。

    注意：小畜同时入 六合表 与 六冲表 → hex_adjustment 被六冲-0.5 抵消为 0,
    若仅以 hex_adjustment > 0 判定, 小畜三刑会漏覆写。故以「入六合表」为准。
    """
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
    """病药（《增删卜易》有病取药）：结构化 illness/medicine 只做有界加减。

    吉凶主判仍在旺衰/动变/格局；星煞不进主分（仅 narrate 旁参）。
    """
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
    """5.7 定性判断之后的古籍强凶/从吉覆写链。返回覆写后的定性三件套。"""
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
    # 1. 用神旺衰基础分
    factor_contributions.append({
        "name": "用神旺衰",
        "factor": "base",
        "score": round(base_score, 2),
        "reason": (
            FREASON["base_strong"]["text"] if base_score > 2 else
            FREASON["base_weak"]["text"] if base_score < 0 else
            FREASON["base_neutral"]["text"]
        )
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
    # 10. 伏神得出
    if fu_shen_adjustment != 0:
        factor_contributions.append({
            "name": "伏神得出",
            "factor": "fu_shen",
            "score": round(fu_shen_adjustment, 2),
            "reason": _user_reason(fu_shen_note, FREASON["fu_shen_out"]["text"])
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
