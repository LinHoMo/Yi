# -*- coding: utf-8 -*-
"""古典断法增强·门面：按域拆分后的聚合入口（API 与拆分前一致）。

分域实现：
  effects_harmony   — 六合六冲 / 反吟伏吟
  effects_structure — 卦身 / 五行旺衰 / 三刑
  effects_change    — 合绊 / 六破 / 入墓 / 化格 / 飞伏
"""
from __future__ import annotations

from effects_harmony import (  # noqa: F401
    analyze_clash_harmony,
    analyze_repetition,
    analyze_repetition_deep,
)
from effects_structure import (  # noqa: F401
    analyze_hexagram_body,
    analyze_element_strength,
    analyze_three_punishments,
)
from effects_change import (  # noqa: F401
    analyze_day_month_bonding,
    analyze_six_breaks,
    analyze_officer_tomb,
    analyze_transformation_pattern,
    analyze_flying_hidden_interaction,
)

__all__ = [
    "analyze_clash_harmony",
    "analyze_repetition",
    "analyze_repetition_deep",
    "analyze_hexagram_body",
    "analyze_element_strength",
    "analyze_three_punishments",
    "analyze_day_month_bonding",
    "analyze_six_breaks",
    "analyze_officer_tomb",
    "analyze_transformation_pattern",
    "analyze_flying_hidden_interaction",
]
