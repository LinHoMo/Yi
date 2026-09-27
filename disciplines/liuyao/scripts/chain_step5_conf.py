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
        return CONF_TXT["high"]["text"]
    elif confidence >= 60:
        return CONF_TXT["medium"]["text"]
    elif confidence >= 40:
        return CONF_TXT["medium_low"]["text"]
    else:
        return CONF_TXT["low"]["text"]


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
        parts.append(f"（量化参考 {float(score):.2f}，把握约 {kw.get('confidence','—')}%）")
    note_bits = [x for x in (
        kw.get("officer_tomb_verdict_note"), kw.get("nayin_desc"),
    ) if x]
    if note_bits:
        parts.append(" ".join(str(x) for x in note_bits))
    qt = kw.get("classical_quotes_text") or ""
    if qt:
        parts.append(str(qt).replace("【经典引文】", FREASON["quote_prefix"]["text"]))
    return "".join(parts)


