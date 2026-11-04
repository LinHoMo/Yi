# -*- coding: utf-8 -*-
"""第五步·综合（analyze 段内最后一步）：把 step1–step4 的现状／用神／旺衰／动变
事实合成为 verdict、分数、应期与格局标签，供 `chain_assembly` 装配。

边界（CONTRACT.md §一.2）：本模块是推演实现，不是叙述层；不产出成段正文。
历史：329 批结构分层体检登记「step5 连 docstring 都没有」；346 批补本节。
模块体量（约 2,000 行）是既定技术债，拆分/瘦身须另批走 §四 验收，不在本批夹带。
"""
from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))
# D3 收编：本文件已迁入 scripts/engine/pipeline/，同目录兄弟 step* 由 _ks_d 覆盖，
# 但 direction/chain_tables/util/chain_verdicts/labels_loader 等仍在 scripts/，需把 scripts/ 也加入。
_ks_parent = _ks_os.path.dirname(_ks_os.path.dirname(_ks_d))
_ks_grandparent = _ks_os.path.dirname(_ks_parent)
if _ks_parent not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_parent)
if _ks_grandparent not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_grandparent)
# L2 规则层（direction/rule_engine/predicates）在 liuyao/rules/：从本文件所在目录向上搜第一个名为 rules 的目录，
# 避免 dirname 层数算式在搬目录后静默失效（D3 收编后 step5 下移两级，原式 dirname(_ks_d)/"rules" 会错指 scripts/engine/rules）。
_rules_d = _ks_d
while True:
    _rules_cand = _ks_os.path.join(_rules_d, "rules")
    if _ks_os.path.isdir(_rules_cand):
        if _rules_cand not in _ks_sys.path:
            _ks_sys.path.insert(0, _rules_cand)
        break
    _rules_up = _ks_os.path.dirname(_rules_d)
    if _rules_up == _rules_d:  # 到盘根仍未找到，静默放弃
        break
    _rules_d = _rules_up

for _p in (_ks_d, _ks_parent, _ks_grandparent):
    if _p not in _ks_sys.path:
        _ks_sys.path.insert(0, _p)

from kernel_path import ensure_kernel_on_path as _ks_ensure

_ks_ensure(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    BRANCH_ELEMENTS,
    KE_CYCLE,
    SHENG_CYCLE,
    EARTHLY_BRANCHES as BRANCHES,
)

from datetime import datetime, timedelta


import logging


import re


_log = logging.getLogger(__name__)


from chain_tables import (
    _BRANCH_CLASH_MAP,
    _ELEMENT_PEAK_MONTHS,
    _HE_MAP,
    HEXAGRAM_LIUCHONG,
    HEXAGRAM_LIUHE,
    SAN_HE,
    _60_CYCLE_BASE,
)

from chain_assembly import (_get_hexagram_body_summary_note, find_classical_quotes)

from timing import predict_timing_core as _predict_timing

from _step5_dates import (  # T31：纯日期函数提取到独立模块
    _day_branch_for_date,
    _next_date_with_day_branch,
    _dates_overlap,
)
from _step5_timing import calculate_yingqi  # T31：应期计算提取到独立模块
from _step5_weather import _weather_verdict_score  # T31：天气占主判提取到独立模块
from _step5_factors import build_factor_contributions  # T31：因子贡献构建提取到独立模块

from chain_verdicts import strength_reason, strength_polarity

from util import (  # noqa: E402  311批拆分：纯工具归 util（CONTRACT §六-6）
    _branch_element,
    _is_chong,
    _twelve_growth_at_day,
    element_strength_in_month,
    safe_get,
)
from chain_verdicts import (  # noqa: E402  断语表装载（原 narrative_utils/narrative_rules）
    note_text,
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

from step4 import _detect_special_pattern, _user_reason  # 跨文件引用
from step3 import _real_hidden_can_emerge  # 伏神真实 can_emerge 判据（缺陷 C）
from direction import (  # 古籍方向凶格上限（rules/direction.py，已瘦成 detect_caps 调度壳 + apply_caps）
    apply_caps as apply_direction_caps,
    detect_direction_caps,
)

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

    # ---------- 5.2b: 克神待解（第二零九批）----------
    # 《增删卜易》dz L965 逐字：「大象吉而受克，须待克神受克：如用神临辰土，
    # 得日月动爻生扶，乃为大象吉也。倘被寅卯克害，后逢申酉日冲克克神则吉，余仿此。」
    # 用神得月令生扶（旺/相）而动爻克伤＝克而待解（冲克克神之期应吉），减凶半档；
    # 书证只明「生扶」总条件，本批仅取月令半边（日辰/动爻生扶半边不入，防扩权）。
    _gms_ke = str(safe_get(step3_data, "god_month_strength", default="") or "")
    _ke_resolved = 0.0
    if change_net_effect < -0.3 and _gms_ke in ("旺", "相"):
        _ke_resolved = 0.5
        change_net_effect = round(change_net_effect + _ke_resolved, 2)

    # ---------- 5.3: 卦体调候 ----------
    hex_name = safe_get(step1_data, "hexagram_name", default="")
    palace = safe_get(step1_data, "palace", default="")

    # dir_caps 提前至此：卦体调候 score_delta（六合+0.5/六冲-0.5）由 rule_engine 求值。
    # cap 压档仍在 5.7b 复用同一份 dir_caps。
    _mt_sb = safe_get(div_time, "month_stem_branch", default="")
    _qclass_w = str((step2_data or {}).get("question_class") or "")
    _weather_override = _qclass_w in ("天气·占雨", "天气·占晴")
    dir_caps = [] if _weather_override else detect_direction_caps(
        safe_get(r, "original_hexagram", "yao_lines", default=[]),
        step2_data, step4_data,
        _mt_sb[1:] if len(_mt_sb) >= 2 else "",
        day_branch,
        list(r.get("empty_branches") or []),
        safe_get(r, "original_hexagram", "name", default=""),
        safe_get(r, "changed_hexagram", "name", default=""),
        str(safe_get(r, "question", default="") or ""),
    )
    hex_adjustment = round(sum(c.get("score_delta", 0.0) for c in dir_caps), 2)
    hex_adjustment_reason = ""
    if hex_name in HEXAGRAM_LIUHE:
        hex_adjustment_reason = FREASON["hex_liuhe_reason"]["text"]
    _ug_ms5 = str(safe_get(step3_data, "god_month_strength", default="") or "")
    if hex_name in HEXAGRAM_LIUCHONG:
        if _ug_ms5 in ("旺", "相"):
            hex_adjustment_reason = FREASON["hex_liuchong_wang_reason"]["text"]
        else:
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
    pattern_flags = cl["pattern_flags"]
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

    # ---------- 5.6a: 天气占主判短路（#23 第2步）----------
    # 通用旺衰／生克对天气无效，《黄金策》《卜筮全书》《增删卜易》皆以"父动主雨、
    # 财动主晴"为唯一主判。故天气门类直接以 _weather_verdict_score 的古籍档位为 final_score，
    # 短路通用评分，并屏蔽下游覆写链（强凶／主象换位／方向 cap），保证 verdict 由书定。
    # 天气案例均落在外部集 [6]，不进 [4] 回归集与金标准看门狗，本短路不改变金标准指纹。
    if _weather_override:
        _yl_w = safe_get(r, "original_hexagram", "yao_lines", default=[]) or []
        _ug_cat_w = (step2_data or {}).get("use_god_category") or ""
        _wf, _wn = _weather_verdict_score(_qclass_w, _yl_w, _ug_cat_w)
        final_score = round(_wf, 2)
        classical_notes.append(f"天气占主判：{_wn}")

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
    # 天气占已短路（_weather_override），不进通用覆写链，verdict 由书定。
    if _weather_override:
        ov = {"verdict": verdict, "verdict_desc": verdict_desc,
              "final_score": final_score, "fired": False,
              "officer_tomb_verdict_note": ""}
    else:
        ov = apply_verdict_overrides(
        verdict, verdict_desc, final_score,
        r=r,
        step3_data=step3_data,
        step4_data=step4_data,
        special_pattern=special_pattern,
        classical_notes=classical_notes,
        pattern_flags=pattern_flags,
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

    # ---------- 5.7b: 古籍方向凶格「上限」----------
    # 这四格在主分加和里要么无条目、要么被正项冲掉，于是出现「書源本案结局明写凶、
    # 引擎判吉」（原 TECH-DEBT §2.11 D1，该台账已删；现行登记＝docs/CHANGELOG.md 第二十一批）。
    # 做法是**只压档、不加和**：命中即把 verdict
    # 压到该书规定的档位，避免任何"再叠一个正项"把它平均回去。
    # 判据与逐字出处见 rules/direction.py 模块头注与 data/rules/rule_registry.json；
    # 展示句全部取自 verdict_texts.json，代码内无断语字面量（SKILL.md）。
    _mt_sb = safe_get(div_time, "month_stem_branch", default="")
    # 天气占已短路，方向 / 主象 cap 对天气无效，跳过。
    # 主象随自占/代占换位 cap（第九十二批）已迁 rules/registry.json
    # (liuyao.zhu_xiang_shou_shang)，由 rule_engine 统一求值。
    # dir_caps 已在 5.3 提前算出，此处直接复用。
    _pre_cap_verdict = verdict
    _capped, _cap_fired = apply_direction_caps(verdict, dir_caps)
    if dir_caps and not _weather_override:
        for _c in dir_caps:
            if "cap" not in _c:
                continue  # score_delta 规则不进 cap note 链
            _cap_note = f"{note_text(_c['reason_key'])}（{_c.get('src', '')}；{_c.get('detail', '')}）"
            classical_notes.append(_cap_note)
            # 第九十二批：cap 注此前只进 classical_notes，而该表在 5.5h 之后不再并回产出
            # ——实测 thinking_chain 的 step5_synthesis 根本没有 classical_notes 键，
            # 于是所有凶格上限都是**压了档却不说明**。这里把它并进真正外露的 pattern_verdict_note。
            if _cap_note not in str(pattern_verdict_note or ""):
                pattern_verdict_note = (f"{pattern_verdict_note}；{_cap_note}"
                                        if pattern_verdict_note else _cap_note)
        if _cap_fired:
            verdict = _capped
            _dk = {"大凶": "score_da_xiong", "凶": "score_xiong",
                   "平凶": "score_ping_xiong"}.get(verdict)
            if _dk:
                verdict_desc = vdesc(_dk)
            # 抬档带分（[1.8] 同档收口补洞）：若 5.7b 的 cap 把 verdict 从较低档抬到较高档
            # （救应抬吉，如六冲变合「竟以吉断」），final_score 须至少抬到新档下界；
            # 压档（凶格压严）分数本就在下方，不动。只上抬不下压——
            # 与 apply_verdict_overrides 末尾 `_floor` 及 check_verdict_coherence.band_of 同源。
            # 局部取 RANK（pure 函数库，step5 顶部未直接 import）。
            from predicates import RANK as _RANK
            if _RANK.get(_capped, -1) > _RANK.get(_pre_cap_verdict, -1):
                _lift_floor = {"大吉": 4.0, "吉": 1.0, "平吉": -0.5, "凶": -2.0}.get(_capped)
                if _lift_floor is not None and final_score < _lift_floor:
                    final_score = round(_lift_floor, 2)

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
        ladder=[(_tr.get("token") or "", _tr.get("rule") or "")
                for _tr in (timing.get("timing_rules") or [])
                if isinstance(_tr, dict) and _tr.get("unit") == "日"],
    )

    # ---------- 5.10: 推理链 ----------
    # 355 批：叙述链不再由 step5 生成（CONTRACT §六-7）；narrate 用
    # narrative_assembly 从 step1–5 事实重建。step5 只留结构与分数。

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
        # 468 批：词条按 quote_kind 分标——verbatim 保持「经典引文」，今译加「（今译）」，
        # 标题同步改为「经典引文与今译」，不再把 48 条今译统称「引文」。
        classical_quotes_text = "【经典引文与今译】" + "".join(
            f"• {q['source']}{'（今译）' if q.get('quote_kind') == 'paraphrase' else ''}"
            f"：{q['quote']}" for q in classical_quotes
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
        "god_month_strength": str(safe_get(step3_data, "god_month_strength", default="") or ""),
        "ke_resolved": _ke_resolved,
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
        # T29 第一批：三段 verdict 新字段（旧 verdict 不变，新字段为附加；见 REFACTOR-PLAN §五.1）
        "present_verdict": verdict if not (_verdict_locked and "凶" not in verdict) else "凶",
        "rescue_verdict": verdict if not (_verdict_locked and "凶" not in verdict) else "凶",
        "timing_speed": yingqi_dates.get("speed", "") if isinstance(yingqi_dates, dict) else "",
        "verdict_description": verdict_desc,
        # 古籍方向凶格上限的结构事实（供 narrate 与回归断言读取；判定见该模块）
        "direction_caps": dir_caps,
        "signal_strength": signal,
        "confidence": signal,
        "signal_strength_description": _strength_to_text(signal),
        "confidence_description": _strength_to_text(signal),
        "timing": timing,
        "yingqi_dates": yingqi_dates,
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
            # 显式告警（缺陷 F，2026-10-09）：classical_analysis 是 scripts/ 同目录
            # 兄弟文件而非 pip 包；导入失败只可能是 sys.path 缺 scripts/ 或文件缺失。
            # 力重系数退 1.0（阳/阴日不加权）——评分口径会变，必须留痕。
            _log.warning("classical_analysis 导入失败：六兽阴阳日力重退回 1.0（六神调整不变向）。"
                         "排查 sys.path 是否含 scripts/ 目录。",
                         exc_info=True)

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

            # 随官入墓旺衰条件（第两百八十二批）：随鬼入墓章覺子总论（zengshan_buyi
            # wikitext L685）结论句逐字「便是世爻用爻隨鬼入日墓入動墓或動而化墓，
            # 亦是休囚無气始見危，若旺而有扶亦有求解」——入墓凶断以休囚无气为
            # 条件；旺相有扶者「有求解」，重档减免。旺衰取入墓者（用神支，
            # 退而世爻支）的月令状态；减免幅度沿用 P0-4 病占 ×0.3 通道。
            _tomb_target = (
                ot_data.get("use_god_branch")
                or ot_data.get("world_branch")
                or ot_data.get("tomb_branch")
                or ""
            )
            _tomb_elem = BRANCH_ELEMENTS.get(_tomb_target, "")
            _tomb_month_elem = (step3_data or {}).get("month_element") or ""
            _tomb_state = (
                element_strength_in_month(_tomb_elem, _tomb_month_elem)
                if _tomb_elem and _tomb_month_elem else ""
            )
            if _tomb_state in ("旺", "相"):
                officer_tomb_adjustment = round(officer_tomb_adjustment * 0.3, 2)
                officer_tomb_severity = "mild"
                officer_tomb_description += note_text("officer_tomb_wang_you_jiu")
            # 休囚无气：保持原价（书断「始見危」），不再按占题域减半。

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
                        # 第502批精修：原神同类成局触发「贪合忘生-2.0」。但若用神本身临
                        # 月令旺相（god_month_score>=4，得月建生扶），原神成局非但不绊，
                        # 反成「原神得局生用」的吉象——《增删卜易》ZD196原文「喜水局生官」
                        # 即此（用神官鬼木在寅月，god_month_score=5）。用神月处死地
                        # （god_month_score<=2，如reg_19妻财午火在亥月，god_month_score=1）
                        # 则保持-2.0。此判别使ZD196升吉而不破reg_19。
                        _gms = 0.0
                        if isinstance(step3_data, dict):
                            try:
                                _gms = float(step3_data.get("god_month_score", 0) or 0)
                            except (TypeError, ValueError):
                                _gms = 0.0
                        if yuan_shen_bond_adjustment == 0.0:
                            if _gms >= 4.0:
                                yuan_shen_bond_adjustment = 1.5
                            else:
                                yuan_shen_bond_adjustment = -2.0
                        _combo_branches_str = "".join(_combo_branches)
                        _day_info = ""
                        if _day_b in _combo_branches:
                            _day_info = f"(日{_day_b}引动)"
                        elif _month_b in _combo_branches:
                            _day_info = f"(月{_month_b}引动)"
                        if _gms >= 4.0:
                            yuan_shen_bond_reason = (
                                f"原神{_yuan_elem}参与{_combo_branches_str}"
                                f"三合{_yuan_elem}局{_day_info}，用神临月建（旺），"
                                f"原神得局生用，吉"
                            )
                        else:
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
def _fu_structural_state(step2_data: dict, r: dict) -> dict | None:
    """用神伏藏的飞/伏结构判据（无文本嗅探）。

    数据源全部为机械结构值：
      · 飞/伏五行与地支：step2 fu_cang_detail.results[]（本宫首卦纳甲寻伏，铁律一）
      · 飞神旬空：chart empty_branches；飞神月破：内核六冲表 × 月建支
      · 绝于飞：十二长生表 伏行@飞支 ==「绝」，日辰冲伏神者豁免
        （与 narrative_utils._evaluate_fu_cang_strength 同一谓词——旧 step5 读它
        产出的文本，现在直接读它所依据的结构，判据逐字等价）
      · 真实 can_emerge：advanced_analysis.hidden_spirit_analysis（见 step3
        _real_hidden_can_emerge 注记）
    """
    if not step2_data or not step2_data.get("has_fu_cang"):
        return None
    results = (step2_data.get("fu_cang_detail") or {}).get("results") or []
    entry = next((e for e in results if isinstance(e, dict)), None)
    if entry is None:
        return None
    fu_shen = entry.get("fu_shen") or {}
    fei_shen = entry.get("fei_shen") or {}
    fu_elem = fu_shen.get("element") or ""
    fu_branch = fu_shen.get("branch") or ""
    fei_elem = fei_shen.get("element") or ""
    fei_branch = fei_shen.get("branch") or ""
    if not fu_elem:
        return None

    empty_branches = list(r.get("empty_branches") or [])
    div_time = r.get("divination_time") or {}
    month_sb = str(div_time.get("month_stem_branch") or "")
    day_sb = str(div_time.get("day_stem_branch") or "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""

    fei_ke_fu = bool(fei_elem) and KE_CYCLE.get(fei_elem) == fu_elem
    fei_sheng_fu = bool(fei_elem) and SHENG_CYCLE.get(fei_elem) == fu_elem
    fu_sheng_fei = bool(fei_elem) and SHENG_CYCLE.get(fu_elem) == fei_elem
    # 绝于飞（含日冲豁免，谓词与 narrative_utils 一致）
    growth_at_fei = _twelve_growth_at_day(fu_elem, fei_branch) if fei_branch else ""
    fu_severed_at_fei = bool(growth_at_fei == "绝") and not _is_chong(fu_branch, day_branch)

    return {
        "fu_elem": fu_elem,
        "fei_elem": fei_elem,
        "fu_branch": fu_branch,
        "fei_branch": fei_branch,
        "fei_empty": bool(fei_branch) and fei_branch in empty_branches,
        "fei_month_break": bool(fei_branch) and bool(month_branch)
                           and _BRANCH_CLASH_MAP.get(month_branch) == fei_branch,
        "fei_sheng_fu": fei_sheng_fu,
        "fei_ke_fu": fei_ke_fu,
        "fu_sheng_fei": fu_sheng_fei,
        "fu_severed_at_fei": fu_severed_at_fei,
    }


def compute_fu_shen_adjustment(step2_data: dict, step3_data: dict, r: dict) -> tuple:
    r"""伏神格局调整（飞空得出 / 飞来生伏 / 绝于飞 / 飞克伏 / 伏泄气 / 伏而不得出）。

    判据 100% 读结构值（2026-10-09 缺陷 C 重写，docstring 与实现一致）：
      旧实现把 ±分方向门控建在 step3 summary 文本的子串嗅探上（"飞克伏" in text），
      :762 甚至用 re.search(r'飞神(\w)') 从散文里抠地支；而它自称的"结构化兜底"
      读的是 step2 恒真占位 can_emerge——「伏而不得出」永不可达。
      现全部改读 _fu_structural_state() 的五行/地支/旬空/月破/十二长生结构值，
      兜底读 classical_enhancements 的真实 can_emerge（step3._real_hidden_can_emerge）。
      分支优先级与旧文本路径逐项一致：飞空 > 飞生伏 > 绝于飞 > 飞克伏（内查月破）
      > 伏泄气 > 伏而不得出。
    所本（判据动作的古籍出处；判类阈值本身见各 note basis）：
      · 飞空得出／飞破得出：《增删卜易·飞伏神章》源L1055-1056「伏神得遇飞神空破
        休囚墓绝者六也」「空下伏神，易于引拨」；《黄金策》同句。
      · 飞来生伏：《卜筮正宗》源L414「水生木谓之飞来生伏得长生」。
      · 飞克伏：《卜筮正宗》源L433「土克水谓之飞来克伏」；《易隐》源L224
        「飞克伏则伤身」。
      · 绝于飞：《卜筮正宗》源L507/L525「火绝在亥谓之伏神绝于飞爻」。
      · 伏生飞（泄气）：《卜筮正宗》源L432「木生火谓之伏去生飞，名为泄气」；
        《易隐》源L224「伏生飞曰泄气」。
      · 伏而不得出：《增删卜易》源L1058「伏神终不得出者有五」；
        《黄金策·千金赋》源L136「伏无提挈终徒尔，飞不摧开亦枉然」
        （《增删卜易》源L1535 作「伏无提携终徒耳，飞不冲开亦枉然」；
        《卜筮正宗》源L1235 作「伏无提拔终徒尔」——三书异文，逐字须按所署底本取）。
    2026-10-02 保留：新增**伏而不得出**方向权重 -1.0（现行登记处＝
    data/rules/rule_registry.json liuyao.fucang 条 applicability 末句；
    原挂 docs/TECH-DEBT.md §2.3——该台账已随扁平化删除，2026-10-13 按实改注），
      旧实现只覆盖「得出/泄气/克伏」各象，伏神无提挈时方向分零反馈。
    """
    fu_shen_adjustment = 0.0
    fu_shen_note = ""
    st = _fu_structural_state(step2_data, r)
    if not st:
        return 0.0, ""

    if st["fei_empty"]:
        # 飞神旬空 → 伏神得出有力（优先于生克等次级关系）
        fu_shen_adjustment = 1.5
        fu_shen_note = note_text("fu_fei_kong_out")
    elif st["fei_sheng_fu"]:
        # 飞神生伏神，伏得出为吉
        fu_shen_adjustment = 1.0
        fu_shen_note = note_text("fu_fei_sheng_fu")
    elif st["fu_severed_at_fei"]:
        # 伏神绝于飞神 → 气绝难出（P0-5；日辰冲伏神者已在结构谓词中豁免）
        fu_shen_adjustment = -2.0
        fu_shen_note = note_text("fu_die_at_fei")
    elif st["fei_ke_fu"]:
        # 飞克伏：飞神空/破则伏得出为吉（空已由首支覆盖），否则难出
        if st["fei_month_break"]:
            # 飞神月破，伏神得出
            fu_shen_adjustment = 1.0
            fu_shen_note = note_text("fu_out_fei_month_break")
        else:
            fu_shen_adjustment = -1.0
            fu_shen_note = note_text("fu_fei_ke_hard_out")
    elif st["fu_sheng_fei"]:
        # 伏泄气: 伏神被动泄力，轻微负面
        fu_shen_adjustment = -0.5
        fu_shen_note = note_text("fu_drain_by_fei")
    else:
        # 伏而不得出（真实结构判据）：用神伏藏且 classical_enhancements 判
        # can_emerge=False——无提挈则终不得出头，方向减分。
        can_emerge = _real_hidden_can_emerge(r, step2_data.get("use_god_category") or "")
        if can_emerge is False:
            fu_shen_adjustment = -1.0
            fu_shen_note = note_text("fu_no_emerge")

    return fu_shen_adjustment, fu_shen_note


# ---------------------------------------------------------------- 5.5h 古籍通用格局加减
# _divination_role 与 _ROLE_WORDS 原在 step5 本地重复定义，现复用 rules/predicates.py
# 的 canonical 实现（step5 已通过 rules/ 加入 sys.path，见 L14）。
from predicates import divination_role as _divination_role  # noqa: E402


# _weather_verdict_score 已提取到 scripts/_step5_weather.py
# 本模块顶部 from _step5_weather import _weather_verdict_score 回收


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
    pattern_flags: list[str] = []
    # 问事归类门控（缺陷 D 修复，2026-10-09）：读 step2 单点产出的结构枚举
    # question_class（映射表 data/rules/question_classes.json，判类前经
    # normalize_question_text 简繁归一）。旧实现对问题自由文本做关键词子串嗅探
    # （含单字"失"），上游改写措辞/换简繁/换近义问法即静默变向。
    # 关键词族逐字继承旧 :805-810 三门；判类属现代问法启发式，非古籍定式——
    # 古籍只为其下的判定动作所本（各 note 的 basis 字段）。
    _qclass = str((step2_data or {}).get("question_class") or "")
    _is_catch = _qclass == "逃亡捕捉"
    _is_travel_return = _qclass == "行人" and not _is_catch
    _is_wealth = _qclass in ("失物", "求财")
    _q_l = str((r.get("question") or r.get("question_category") or ""))

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

    # 1a) 行人归占·化退归志（《卜筮正宗》行人章总诀「动化进神不返，用神化退而归」，
    #     dz L3298）：化退在成败占主衰象（dz L551 通用轨），在归期占主归志——
    #     实案双证 dz L1246（兄动化退，已有归志，应实破之月归）、dz L1158（父化退神，
    #     父已归矣）。故归期占用神（或动爻）化退时抵回 step4 用神化退 −1.0 的衰价。
    if _is_travel_return:
        _s4d = safe_get(r, "_step4_data", default={}) or {}
        _s4_txt = str(_s4d.get("summary_text") or "")
        for _det in (_s4d.get("details") or []):
            _ct = str(_det.get("change_type") or "")
            if _ct:
                _s4_txt += " " + _ct + " " + str(_det.get("change_detail") or _det.get("detail") or "")
        if "化退" in _s4_txt:
            classical_adj += 1.0
            classical_notes.append(note_text("travel_huatui_guizhi"))
            pattern_flags.append("travel_huatui_guizhi")

    # 1) 行人/归期：用神生世/克世 — 迟归或速至，皆主能归（《黄金策》出行章）
    if _is_travel_return and ug_el_s and world_branch:
        w_el = _el_of_branch(world_branch) or ""
        if w_el and SHENG_CYCLE.get(ug_el_s) == w_el:
            classical_adj += 1.5
            classical_notes.append(note_text("travel_use_sheng_world"))
            pattern_flags.append("travel_use_sheng_world")
        elif w_el and KE_CYCLE.get(ug_el_s) == w_el:
            classical_adj += 0.8
            classical_notes.append(note_text("travel_use_ke_world"))
            pattern_flags.append("travel_use_ke_world")
        elif w_el and KE_CYCLE.get(w_el) == ug_el_s:
            # 世克用：行人受制，未必即归，但用神有气仍主终归
            classical_adj += 0.3
            classical_notes.append(note_text("travel_world_ke_use"))
            pattern_flags.append("travel_world_ke_use")
    if _is_travel_return:
        _fu_txt = str((step3_data or {}).get("summary_text") or "")
        _lv = str((step3_data or {}).get("strength_level") or "")
        _dead = any(k in _fu_txt for k in ("绝于", "真空", "月破", "飞克伏难出", "克伏不出"))
        if (not _dead) and (
            "得出" in _fu_txt
            or _lv in ("旺", "相", "极旺", "中和", "中和偏旺")
            or "伏神" in _fu_txt        ):
            classical_adj += 0.6
            classical_notes.append(note_text("travel_use_alive"))
            pattern_flags.append("travel_use_alive")

    # 2) 兄弟持世 + 求财 — 古籍之忌，但本书自带例外
    #    《卜筮正宗》源L327「兄弟持世莫求财」（《增删卜易》源L419 作「兄弟持世者难求」）；
    #    例外见《增删卜易》源L3035「虽则兄爻持世无财，但喜卯日即是财星」
    #    与《增删卜易》源L2342「得日月作财而合世，富而骄」——日辰或月建即本宫之财时不扣。
    _sp_pat_txt = ""
    try:
        if isinstance(special_pattern, dict):
            _sp_pat_txt = str(special_pattern.get("pattern") or "") + str(special_pattern.get("description") or "")
    except Exception:
        _sp_pat_txt = ""
    if world_relation == "兄弟" and _is_wealth and ug_cat == "妻财":
        _pal_e = _el_of_branch(world_branch) or ""
        _me2 = str((step3_data or {}).get("month_element") or "")
        _de2 = str((step3_data or {}).get("day_element") or "")
        _ri_yue_zuo_cai = bool(_pal_e) and KE_CYCLE.get(_pal_e) in (_me2, _de2)
        if _qclass == "失物" or "冲中逢合" in _sp_pat_txt:
            # 失物/逢合的轻扣另有书据（《增删卜易》失物章），而"日月作财"的例外只属于求财文脉，
            # 不外推到失物——故本支照常轻扣，例外只拦下面的 -1.2 重扣。
            classical_adj -= 0.2
            classical_notes.append(note_text("brother_hold_wealth_lost_soft"))
        elif _ri_yue_zuo_cai:
            pass  # 《增删卜易》源L3035 逐字「虽则兄爻持世无财，但喜卯日即是财星」，故日月作财时不扣
        else:
            classical_adj -= 1.2
            classical_notes.append(note_text("brother_hold_wealth"))

    # 3) 妻财持世 + 失物 — 世持财主自失可寻（增删失物章）
    if world_relation == "妻财" and _qclass == "失物":
        classical_adj += 0.8
        classical_notes.append(note_text("wealth_hold_lost"))

    # 5) 原神失位：用神旺相而原神（完全）不在卦中或不动 — 现行触发（**书据不符，见 #15**）
    #    按书收窄已落地（第六十批）：《增删卜易》源L1725 逐字「用神虽旺，原神若被伤克者，即如水无泉源，木无根蒂」、
    #    同书源L551 逐字「元神虽现又有不能生用神者有六：元神休囚，不动或动而休囚又被伤克者一也……以上元神无力
    #    生用神，无用之元神也，虽有如无」——条件是元神**无力或被伤克**，旧实现用"静而不动"当条件属书据不符。
    #    两次实测对比（同一条改动，不同底座）：
    #      旧底座（第五十二批前）：wikisource_direction 74.4→77.0，但 [4] 15→13（reg_01 贪合、reg_13 伏神得出翻转），
    #        当时**未采纳**，登记为 #15。
    #      新底座（#16 结构化 flag、#17 判据路补款五之后——#17 已于第六十二批并一闭）：[3] 11、[4] 17、tune 97.3/64.7、holdout 90.2/50 **全不动**，
    #        外部 wikisource_direction 74.4→75.0（外部集不参与调参，此数只作描述）；
    #        即那两支豁免不再需要——先前的翻转是"措辞替量作答"的连带效应，#16 拆开后自行消失。
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
            or _qclass == "失物"
            or "世持财" in _sp_pat_txt
        )
        # 静卦(_is_static_hexagram=True)下，只要原神出现在卦中(position有值), 不算"失位";
        # 仅当原神完全不在卦中 (not _yuan_pos) 时, 才扣-1.0
        # 动卦下原神位置存在但未发动时, 仍扣-1.0
        _me3 = str((step3_data or {}).get("month_element") or "")
        _de3 = str((step3_data or {}).get("day_element") or "")
        _yel = str(_yuan.get("element") or "")
        _yuan_powered = bool(_yel) and (_yel in (_me3, _de3) or SHENG_CYCLE.get(_me3) == _yel
                                        or SHENG_CYCLE.get(_de3) == _yel)
        _yuan_hurt = bool(_yel) and (KE_CYCLE.get(_me3) == _yel or KE_CYCLE.get(_de3) == _yel)
        _yuan_missing = (not _yuan_pos) or _yuan_hurt or (not _yuan_powered)
        if _yuan_missing and not _skip_yuanshen:
            classical_adj -= 1.0
            classical_notes.append(note_text("static_yuanshen_missing"))
            pattern_flags.append("yuanshen_missing")
            pattern_flags.append("no_source_wording")

    # 5b) 天气占主判已移至 5.6a 短路（#23 第2步）：_weather_verdict_score 以
    #     《黄金策》"父动主雨、财动主晴"为唯一主判并直接覆盖 final_score，通用旺衰/
    #     生克路径对天气无效，故此处旧 +0.8 抬升一支已失效（被短路覆盖），删除以免重复计分。
    #     下行方向 cap（rules/direction.py 第 6 条）亦随短路失效，详见 5.6a。

    # 6) 久病逢冲为凶（对「近病逢冲即愈」）
    if _qclass == "疾病·久病":
        classical_adj -= 0.8
        classical_notes.append(note_text("chronic_illness"))
        pattern_flags.append("chronic_illness")

    # 7) 兄弟持世 + 功名/考试 — 竞争费力（可中而难前茅）
    if world_relation == "兄弟" and _qclass == "功名科举":
        classical_adj -= 0.4
        classical_notes.append(note_text("brother_hold_exam"))
        pattern_flags.append("brother_hold_exam")

    # 8) 官司：官鬼克世 / 父母月破 → 不利（增删官非章）
    if _qclass == "官非词讼" and "师尊" not in _q_l:
        ug_br_s = ug_branch_s
        w_br = world_branch
        ug_e = ug_el_s or ""
        w_e = _el_of_branch(w_br) or ""
        if ug_e and w_e and KE_CYCLE.get(ug_e) == w_e:
            classical_adj -= 1.2
            classical_notes.append(note_text("officer_ke_world_lawsuit"))
            pattern_flags.append("officer_ke_world_lawsuit")
        # 文书月破：从摘要文本识别
        _txt3 = str((step3_data or {}).get("summary_text") or "") + str((step2_data or {}).get("summary_text") or "")
        if "月破" in _txt3 and _qclass == "官非词讼":
            classical_adj -= 0.5
            classical_notes.append(note_text("document_month_break"))

    # 9) 原神失位加强：旺极无生 → 大幅降分（现行；其 basis 已标"引擎引申，登记待校"，见 #15）
    # 仅当用神为"极旺"时才额外加权；"旺"级已有规则5的-1.0，不再叠加
    if "yuanshen_missing" in pattern_flags and _lv_ug == "极旺":
        classical_adj -= 1.0
        classical_notes.append(note_text("extreme_prosper_no_source"))
        pattern_flags.append("extreme_no_source")
        pattern_flags.append("no_source_wording")

    # 4) 用神临月建（通用旺格标记分已在旺衰，此处仅补注记）

    # ── 代占／自占的名分三态（第八十九批：只标结构事实，不进加和）──
    # 《卜筮全书》源L7034 逐字「又自占，以世为主；代占，以应为主」；
    # 《卜筮全书》源L5437 逐字「应受伤，不利代占，盖代占以应为主也；世受伤，不利自占，盖自占以世为主也」；
    # 《易林补遗》源L965 逐字「倘若他人代卜，反将应象为尊」。
    # 书上主象随自占／代占换位，引擎至今只看世爻。本批先把三态标出来（可指回原文），
    # 主象改判留 #27 第②步——一次只动一层，否则读数涨跌无法归因。
    _role_q = str(safe_get(r, "question", default="")
                  or (step2_data or {}).get("question_text") or "")
    _role = _divination_role(_role_q)
    if _role == "代占":
        pattern_flags.append("divination_by_proxy")
        classical_notes.append(note_text("proxy_use_response"))
    elif _role == "自占":
        pattern_flags.append("divination_by_self")
        classical_notes.append(note_text("self_use_world"))
    else:
        # 名分说不清时按书就是"无从定主象"，只标不猜——《卜筮正宗》源L1095 逐字「虽吉无益，不验也」
        # （同条上文即「必先明说是何名分，方可就其亲疏、上下分别用神以为占验」的告诫）
        pattern_flags.append("divination_role_unclear")

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
        "pattern_flags": pattern_flags,
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
    pattern_flags: list,
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

    # ── 古籍强凶格局强制覆写（数据化：rules/registry.json#verdict_overrides）──
    # 旧硬编码 if 链已整体迁为规则数据，由 rule_engine.evaluate_verdict_overrides
    # 按数组顺序求值（复刻「自上而下、后读前写」语义）。本处只组装覆写期上下文 cv
    # 并回收 verdict/desc/score；reason_key 非空才换判词文案，空串（he_then_chong_daxiong）
    # 只改 verdict 不动 desc。_fired 仅对旧代码里显式置 True 的四档生效。
    from rule_engine import evaluate_verdict_overrides as _eval_ovr
    _net_eff = (step4_data.get("net_effect") if isinstance(step4_data, dict) else 0.0) or 0.0
    _cv = {
        "verdict": verdict,
        "final_score": final_score,
        "qtext": _qtext,
        "q_l": _q_l,
        "sp_pat": _sp_pat,
        "net_effect": _net_eff,
        "pattern_flags": pattern_flags,
        "world_relation": world_relation,
        "is_wealth": _is_wealth,
        "is_travel_return": _is_travel_return,
        "xhe": xing_he_conflict_override,
    }
    _ovr_actions = _eval_ovr(_cv)
    verdict = _cv["verdict"]
    final_score = _cv["final_score"]
    for _a in _ovr_actions:
        if _a.get("reason_key"):
            verdict_desc = vdesc(_a["reason_key"])
    _fired_reasons = {"travel_scattered", "partner_scattered",
                      "weak_use_net_negative", "xing_he_conflict"}
    _fired = any(_a.get("reason_key") in _fired_reasons for _a in _ovr_actions)

    # 古籍通用口径：行人「用神生世/克世」主能归；兄弟持世求财主耗
    if classical_notes:
        if "yuanshen_missing" in pattern_flags and "冲中逢合" not in _sp_pat_txt:
            if verdict in ("大吉",):
                verdict = "吉"
                verdict_desc = vdesc("yuanshen_missing_daji_cap")
            # 「旺极无源」在旧代码里是**注记文案子串**，而 static_yuanshen_missing 的文案本身
            # 就带这四个字（verdict_texts.json 同名 key），故本条件在外层「原神失位」块内恒真——
            # 措辞替量作答：-1.0 加权（extreme_no_source）没触发也照样走平吉/凶覆写。
            # 本条按字面保留旧行为（no_source_wording 由两处生产者同时置位），
            # "是否应收紧为只认加权已触发"属语义变更，登记为 #15 单独量，不在重构里夹带。
            # 实测（2026-10-11 第五十二批）：改成只认 extreme_no_source 后 288 例两层指纹与全门逐项读数
            # 均不变——此差异在现有案例集内不可观测，故既不采纳也不宣布修好，见 CHANGELOG 同批。
            if "no_source_wording" in pattern_flags and verdict in ("吉", "大吉", "平吉"):
                if final_score < 1.0:
                    verdict = "凶"
                    verdict_desc = vdesc("extreme_no_source_xiong")
                else:
                    verdict = "平吉"
                    verdict_desc = vdesc("yuanshen_missing_ping_ji")
            elif verdict == "吉" and final_score < 2.0:
                verdict = "平吉"
                verdict_desc = vdesc("yuanshen_missing_discount")
        if "officer_ke_world_lawsuit" in pattern_flags:
            if verdict in ("大吉", "吉"):
                verdict = "凶"
                verdict_desc = vdesc("officer_ke_world_xiong")
            elif verdict == "平吉":
                verdict = "凶"
                verdict_desc = vdesc("officer_ke_world_tight")
        if "brother_hold_exam" in pattern_flags and verdict in ("吉", "大凶", "凶"):
            if verdict in ("凶", "大凶"):
                verdict = "平吉"
                verdict_desc = vdesc("brother_exam_not_desperate")
            else:
                verdict = "平吉"
                verdict_desc = vdesc("brother_exam_hard")
        if "chronic_illness" in pattern_flags:
            if verdict in ("大吉", "吉"):
                verdict = "平吉" if verdict == "吉" else "凶"
                if verdict == "平吉":
                    verdict_desc = vdesc("chronic_illness_care")
            if verdict == "平吉" and any(k in _q_l for k in ("久病", "半年")):
                verdict = "凶"
                verdict_desc = vdesc("chronic_illness_tight")
        if "brother_hold_exam" in pattern_flags and verdict in ("吉", "大吉"):
            verdict = "平吉"
            verdict_desc = vdesc("brother_exam_hard")
        if _is_travel_return and any(
            f in pattern_flags
            for f in ("travel_use_sheng_world", "travel_use_ke_world",
                      "travel_use_alive", "travel_world_ke_use")
        ):
            if verdict in ("凶", "大凶"):
                verdict = "平吉"
                verdict_desc = vdesc("travel_eventually_back")
            if "travel_use_sheng_world" in pattern_flags and verdict in ("平吉", "凶", "大凶"):
                verdict = "吉"
                verdict_desc = vdesc("travel_use_sheng_back")
            elif verdict == "平吉" and "travel_use_ke_world" in pattern_flags:
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

    # ── 判词 ↔ 分数 同档收口 ──
    # 覆写链多处把 verdict 从「凶」抬到「平吉/吉」（行人用神生世必归、兄弟持世求名
    # 未绝望、久病尚可调……皆书上有据），却**从不带动 final_score**，于是产出
    # 「判词平吉 · 得分 −5.33」这种自己跟自己打架的读数（金标准 288 例实测 15 例）。
    # 同函数内三刑合战分支早就用「保底 0.5」处理过同类问题
    # （`if final_score < 0.5: final_score = 0.5`），此处把那一步一般化：
    # 判词进哪一档，分数至少到该档下界。只上抬不下压——压档类覆写（判词比分数更悲观）
    # 是故意的，一律保留。
    _floor = {"大吉": 4.0, "吉": 1.0, "平吉": -0.5, "凶": -2.0}.get(verdict)
    if _floor is not None and final_score < _floor:
        final_score = round(_floor, 2)

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


# build_factor_contributions 已提取到 scripts/_step5_factors.py
# 本模块顶部 from _step5_factors import build_factor_contributions 回收


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
        parts.append(str(qt).replace("【经典引文与今译】", FREASON["quote_prefix"]["text"]))
    return "".join(parts)


# ═══ chain_step5_dates.py ═══
# （_day_branch_for_date / _next_date_with_day_branch / _dates_overlap
#   已提取到 scripts/_step5_dates.py，本模块顶部 import 回收）


# ═══ chain_step5_timing.py ═══


# ═══ chain_step5_timing.py ═══

# calculate_yingqi 已提取到 scripts/_step5_timing.py
# 本模块顶部 from _step5_timing import calculate_yingqi 回收



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
