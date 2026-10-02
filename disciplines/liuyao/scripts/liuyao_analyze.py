"""六爻分析：五步推演 facade。

此文件为纯转发层——所有推演函数实际位于 liuyao_step1-5.py。
保持向后兼容：from liuyao_analyze import step1_read_situation 等依旧可用。
"""
from __future__ import annotations

# 一次性初始化内核路径（子模块导入时 kernel_path.py 已被加入 sys.path）
import os as _ks_os, sys as _ks_sys

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))
if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ks_ensure
_ks_ensure(__file__)

from liuyao_step1 import *  # noqa: F401,F403
from liuyao_step2 import *  # noqa: F401,F403
from liuyao_step3 import *  # noqa: F401,F403
from liuyao_step4 import *  # noqa: F401,F403
from liuyao_step5 import *  # noqa: F401,F403

# 内部别名 / 全局变量，外部模块仍引用
from liuyao_timing import predict_timing_core as _predict_timing

from liuyao_step2 import _USE_GOD_RULES

__all__ = [
    "_analyze_effect_on_use_god",
    "_assess_signal_strength",
    "_assess_confidence",
    "_branch_to_relation",
    "_check_fu_cang",
    "_check_greedy_harmony",
    "_check_tan_he_wan_sheng_ke",
    "_check_tan_sheng_wan_ke",
    "_classify_line_role",
    "_combined_strength_for_hm",
    "_compose_change_summary",
    "_compose_strength_summary",
    "_compose_synthesis_summary",
    "_strength_to_text",
    "_confidence_to_text",
    "_dates_overlap",
    "_day_branch_for_date",
    "_decide_use_god",
    "_detect_classical_illness_pattern",
    "_detect_hexagram_harmony_clash_pattern",
    "_detect_hidden_movement",
    "_detect_special_pattern",
    "_determine_change_type",
    "_determine_use_god_category",
    "_element_to_relation",
    "_find_relation_positions",
    "_find_use_god_positions",
    "_forms_hexagram_harmony",
    "_match_use_god_rule",
    "_next_date_with_day_branch",
    "_strip_chart_tail",
    "_strip_hex_names",
    "_use_god_basis",
    "_use_god_rules",
    "_user_reason",
    "apply_verdict_overrides",
    "build_factor_contributions",
    "build_strength_modifiers",
    "calculate_yingqi",
    "compute_advanced_adjustments",
    "compute_an_dong",
    "compute_bing_yao_adjustment",
    "compute_classical_adjustment",
    "compute_day_modifier",
    "compute_empty_modifier",
    "compute_fu_shen_adjustment",
    "compute_month_break_modifier",
    "compute_spirit_adjustment",
    "compute_three_punishment",
    "compute_twelve_growth",
    "detect_xing_he_conflict",
    "resolve_fu_cang_result",
    "step1_read_situation",
    "step2_identify_use_god",
    "step3_analyze_strength",
    "step4_analyze_changes",
    "step5_synthesize",
]
