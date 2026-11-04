# -*- coding: utf-8 -*-
"""可解释性因子贡献构建（T31 第四步提取）。"""
from __future__ import annotations

# 第五百零八批升格：本文件在 <学科根>/engine/ 下，已不在 scripts/。
# 定位只走 _bootstrap 一份实现（向上搜 scripts/kernel_path.py，不按层数硬算），
# 依次配好 本目录／scripts／学科根 三处 sys.path，再交给 kernel_path 定位内核。
import os as _ks_os, sys as _ks_sys

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))
if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

# _bootstrap 在 engine/ 根（本文件的上层）：先入该目录，本文件才不依赖调用方替它配路径。
_ks_engine = _ks_os.path.dirname(_ks_d)
if _ks_engine not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_engine)

from _bootstrap import setup as _ks_setup  # noqa: E402

_ks_setup(__file__)


from chain_verdicts import strength_reason, strength_polarity, STEP5_FACTOR_REASONS as FREASON
from step4 import _user_reason


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
    strength_level = str(adj.get("strength_level") or "")
    factor_contributions.append({
        "name": "用神旺衰",
        "factor": "base",
        "score": round(base_score, 2),
        "reason": strength_reason(strength_level),
        "polarity": strength_polarity(strength_level),
    })
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
    if adj.get("ke_resolved", 0.0) > 0:
        factor_contributions.append({
            "name": "克神待解",
            "factor": "change_resolved",
            "score": round(adj["ke_resolved"], 2),
            "reason": _user_reason("", FREASON["change_ke_resolved"]["text"]),
        })
    if hex_adjustment != 0:
        factor_contributions.append({
            "name": "合冲卦性",
            "factor": "hexagram",
            "score": round(hex_adjustment, 2),
            "reason": _user_reason(hex_adjustment_reason, FREASON["hex_liuhe"]["text"] if hex_adjustment > 0 else FREASON["hex_liuchong"]["text"])
        })
    if spirit_adjustment != 0:
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
    if dmb_adjustment != 0:
        factor_contributions.append({
            "name": "日月合用神",
            "factor": "day_month_bond",
            "score": round(dmb_adjustment, 2),
            "reason": _user_reason(dmb_reason, FREASON["day_month_bond"]["text"])
        })
    if sb_adjustment != 0:
        factor_contributions.append({
            "name": "六破损伤",
            "factor": "six_breaks",
            "score": round(sb_adjustment, 2),
            "reason": _user_reason(sb_reason, FREASON["six_break"]["text"])
        })
    if combo_break_adjustment != 0:
        factor_contributions.append({
            "name": "三合局破",
            "factor": "combo",
            "score": round(combo_break_adjustment, 2),
            "reason": _user_reason(combo_break_reason, FREASON["combo_break"]["text"])
        })
    if yuan_shen_bond_adjustment != 0:
        factor_contributions.append({
            "name": "原神贪合忘生",
            "factor": "yuan_shen_bond",
            "score": round(yuan_shen_bond_adjustment, 2),
            "reason": _user_reason(yuan_shen_bond_reason, FREASON["yuanshen_bond"]["text"])
        })
    if officer_tomb_adjustment != 0:
        factor_contributions.append({
            "name": "随官入墓",
            "factor": "tomb",
            "score": round(officer_tomb_adjustment, 2),
            "reason": _user_reason(officer_tomb_reason, FREASON["officer_tomb"]["text"])
        })
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
    if pattern_adjustment != 0:
        factor_contributions.append({
            "name": "特殊格局",
            "factor": "pattern",
            "score": round(pattern_adjustment, 2),
            "reason": _user_reason(pattern_verdict_note, FREASON["special_pattern"]["text"])
        })
    if classical_adj != 0:
        factor_contributions.append({
            "name": "古籍格局加减",
            "factor": "classical",
            "score": round(classical_adj, 2),
            "reason": "；".join(_user_reason(n) for n in classical_notes[:2]) if classical_notes else FREASON["classical_fallback"]["text"]
        })
    adv_shi = r.get("advanced_analysis", {}).get("shi_yao_relation") if isinstance(r, dict) else None
    if isinstance(adv_shi, dict) and adv_shi.get("classical_rule"):
        _sh_reason = adv_shi["classical_rule"]
        if adv_shi.get("scenario_interpretation"):
            _sh_reason = adv_shi["scenario_interpretation"]
        _sh_relation = adv_shi.get("relation", "")
        _sh_scenario = adv_shi.get("scenario", "")
        _SHI_SCORE = {
            ("官鬼", "career"): 1.0,
            ("父母", "exam"): 1.0,
            ("子孙", "career"): -0.8,
            ("兄弟", "wealth"): -0.8,
        }
        _sh_score = _SHI_SCORE.get((_sh_relation, _sh_scenario), 0.0)
        factor_contributions.append({
            "name": "六亲持世",
            "factor": "shi_yao",
            "score": _sh_score,
            "reason": _sh_reason,
            "classical_rule": adv_shi.get("classical_rule", ""),
            "scenario": adv_shi.get("scenario", ""),
            "scenario_interpretation": adv_shi.get("scenario_interpretation", ""),
        })
    if bing_yao_adjustment != 0:
        factor_contributions.append({
            "name": "病药",
            "factor": "bing_yao",
            "score": round(bing_yao_adjustment, 2),
            "reason": "；".join(bing_yao_reasons) if bing_yao_reasons else "病药平衡",
        })
    factor_contributions.sort(key=lambda x: abs(x["score"]), reverse=True)
    return factor_contributions
