# -*- coding: utf-8 -*-
"""六爻叙述层规则解析（数据驱动，代码只组装）。

把原先散落在 chain_step5_adjust / chain_narrate / human_narrative_segments 里的
三处叙述判定集中到此模块，统一口径：

1. 用神旺衰因子理由：strength_level → 理由文本（取代原先按 raw base_score 分桶的写法，
   修复「平和」与「极弱」自相矛盾）。
2. 婚姻持世解读：按用神类别（＝问测者性别视角）分流男/女模板
   （男问女→妻财为用→子孙为原神持世有利；女问男→官鬼为用→子孙克官不利）。
3. 应期基础句：已有日级日历日期时，不输出「按月计…别拿天来量」矛盾口径。

所有文本/阈值外置 data/rules/verdict_texts.json（AGENTS.md §三）；本模块仅做查找与组装，
不内嵌任何断语原文。依赖单向：narrative_rules → chain_verdicts。
"""
from __future__ import annotations

from chain_verdicts import (
    STEP5_FACTOR_REASONS as FREASON,
    NARRATIVE_HINTS,
    STRENGTH_POLARITY_MAP,
    STRENGTH_REASON_MAP,
)

# 男问女 → 用神妻财；女问男 → 用神官鬼。婚姻持世解读据此分流。
_MALE_USE_GODS = ("妻财",)
_FEMALE_USE_GODS = ("官鬼",)


def strength_reason(strength_level: str) -> str:
    """用神旺衰因子理由：以权威的 strength_level 为准，避免与正文旺衰口径矛盾。"""
    sl = str(strength_level)
    key = STRENGTH_REASON_MAP.get(sl)
    if not key:
        for lvl, k in STRENGTH_REASON_MAP.items():
            if lvl in sl:
                key = k
                break
    return FREASON.get(key or "base_neutral", FREASON["base_neutral"])["text"]


def strength_polarity(strength_level: str) -> int:
    """旺衰等级 → 极性（+1 有利 / 0 中性 / -1 拖累），用于 有利面/拖累面 分类。

    与 floored score（effective_score 下限 0.5，恒为正）解耦，使「极弱」不再误入有利面。
    """
    sl = str(strength_level)
    if sl in STRENGTH_POLARITY_MAP:
        return STRENGTH_POLARITY_MAP[sl]
    for lvl, pol in STRENGTH_POLARITY_MAP.items():
        if lvl in sl:
            return pol
    return 0


def resolve_marriage_interpretation(interp: dict, use_god_category: str = "") -> str:
    """婚姻情境的持世解读：按用神类别（性别视角）选男/女模板，缺省回退通用婚姻条。"""
    ug = use_god_category or ""
    if ug in _MALE_USE_GODS:
        return interp.get("marriage_male", interp.get("marriage", ""))
    if ug in _FEMALE_USE_GODS:
        return interp.get("marriage_female", interp.get("marriage", ""))
    return interp.get("marriage", "")


def select_timing_base(
    special_text: str, speed: str, summary_text: str, calendar_str: str
) -> str:
    """应期基础句。

    当 speed==应迟 且 已有日级日历日期时，改用不矛盾的口径
    （timing_with_dates），避免「按月计…别拿天来量」与具体日辰对冲。
    """
    if "近病逢空" in special_text or "近病" in special_text:
        return NARRATIVE_HINTS["timing_near_illness_void"]
    if speed == "应速" or "应速" in summary_text or "次日" in summary_text:
        return NARRATIVE_HINTS["timing_fast"]
    if speed == "应迟" or "应迟" in summary_text or "年内" in summary_text:
        return NARRATIVE_HINTS["timing_with_dates"] if calendar_str else NARRATIVE_HINTS["timing_slow"]
    return NARRATIVE_HINTS["timing_mid"]
