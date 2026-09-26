# -*- coding: utf-8 -*-
"""古典断法增强：门面。实现按域拆在 classical_rules_{hidden,patterns,effects}.py。


纯搬移拆分，不改逻辑；对外 API 仍从本模块 import（classical_analysis 等）。
"""
from __future__ import annotations

from classical_rules_hidden import (  # noqa: F401
    ctext,
    ctpl,
    _evaluate_hidden_spirit_emergence,
    analyze_hidden_spirits,
    analyze_hidden_spirit_emergence,
    analyze_hidden_movement,
)
from classical_rules_patterns import (  # noqa: F401
    analyze_wandering_returning_soul,
    analyze_monthly_break,
    _check_broken_combo,
    analyze_triple_combo,
    analyze_advance_retreat,
    analyze_twelve_growth,
    analyze_desperate_relief,
)
from classical_rules_effects import (  # noqa: F401
    analyze_clash_harmony,
    analyze_repetition,
    analyze_repetition_deep,
    analyze_hexagram_body,
    analyze_element_strength,
    analyze_three_punishments,
    analyze_day_month_bonding,
    analyze_six_breaks,
    analyze_officer_tomb,
    analyze_transformation_pattern,
    analyze_flying_hidden_interaction,
)

__all__ = [
    "ctext",
    "ctpl",
    "_evaluate_hidden_spirit_emergence",
    "analyze_hidden_spirits",
    "analyze_hidden_spirit_emergence",
    "analyze_hidden_movement",
    "analyze_wandering_returning_soul",
    "analyze_monthly_break",
    "_check_broken_combo",
    "analyze_triple_combo",
    "analyze_advance_retreat",
    "analyze_twelve_growth",
    "analyze_desperate_relief",
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
