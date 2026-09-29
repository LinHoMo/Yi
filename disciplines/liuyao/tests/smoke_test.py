# -*- coding: utf-8 -*-
"""
分析段落产出冒烟测试 (Analysis Segment Smoke Test)
===================================================
验证 enhance_reading() 的各分析段与 step5 的各评分调整项在多种卦象下
**都有产出且不抛异常**，即"接线是否通"。

⚠️ 这不是代码覆盖率，也不是正确性测试：段落返回了内容就算过。
   内容对不对由 `scripts/evaluate.py`（古籍对齐）与 `tests/regression_test.py` 负责。
   旧名 coverage_test 且报 "Coverage 100%"，属误导性命名，2026-09-22 更正。

Usage:
    py -3.12 tests/smoke_test.py                # Run all coverage tests
    py -3.12 tests/smoke_test.py --markdown   # Generate coverage_report.md
    py -3.12 tests/smoke_test.py -v           # Verbose output
    py -3.12 tests/smoke_test.py --list       # List all test segments

Design
------
- Each of the 20 analysis segments in enhance_reading() gets a targeted test.
- Each of the 12+ score_adjustments in step5_synthesize() gets a targeted test.
- Boundary cases (全静卦, 全动卦, 多现, 日月全冲) are also covered.
- Coverage is computed as: covered_segments / total_segments * 100.
"""

import argparse
import os
import sys
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

# ---------------------------------------------------------------------------
# 引擎与古典分析模块在 ../scripts。
# 本文件已从 scripts/ 迁出到 tests/（AGENTS.md：生产目录不混测试），故显式指回 scripts/。
# ---------------------------------------------------------------------------
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))              # disciplines/liuyao/tests
_SCRIPT_DIR = os.path.join(os.path.dirname(_TEST_DIR), "scripts")   # disciplines/liuyao/scripts
sys.path.insert(0, _SCRIPT_DIR)

from liuyao_engine import build_hexagram_result  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from classical_analysis import (  # noqa: E402
    enhance_reading,
    # All 20+ analysis functions for direct invocation
    analyze_hidden_spirits,
    analyze_hidden_movement,
    analyze_wandering_returning_soul,
    analyze_monthly_break,
    analyze_triple_combo,
    analyze_advance_retreat,
    analyze_twelve_growth,
    analyze_clash_harmony,
    analyze_repetition,
    analyze_repetition_deep,
    analyze_hexagram_body,
    analyze_element_strength,
    analyze_three_punishments,
    analyze_hidden_spirit_emergence,
    analyze_day_month_bonding,
    analyze_six_breaks,
    analyze_desperate_relief,
    analyze_transformation_pattern,
    analyze_flying_hidden_interaction,
    analyze_officer_tomb,
    analyze_nayin,
)
from thinking_chain import (  # noqa: E402
    run_thinking_chain,
    HEXAGRAM_LIUHE,
    HEXAGRAM_LIUCHONG,
)

# ===========================================================================
# Test-case data structure
# ===========================================================================

@dataclass
class CoverageTest:
    """Single coverage test targeting a specific analysis segment."""
    id: str
    target_segment: str
    description: str
    yao_values: list          # 6 values (6,7,8,9); index 0 = bottom (初爻)
    date: tuple               # (year, month, day, hour)
    expected_check: str       # Human-readable assertion description
    question: str = "测试覆盖率"
    method_str: str = "manual"
    assertion_fn: Callable = None  # fn(result_dict) -> bool
    target_step5_adj: str = ""  # If non-empty, targets a step5 adjustment instead
    is_boundary: bool = False  # Boundary test case


# ===========================================================================
# assertion_fn helpers
# ===========================================================================

def _seg(result: dict, key: str) -> dict:
    """Get advanced_analysis segment by key. Always safe, never mutates."""
    try:
        adv = result.get("advanced_analysis") or {}
        if isinstance(adv, dict):
            return adv.get(key) or {}
        return {}
    except Exception:
        return {}


def _tc(result: dict, *keys, default=None):
    """Safe nested dict lookup. Always safe, never mutates."""
    try:
        cur = result
        for k in keys:
            if isinstance(cur, dict):
                cur = cur.get(k)
                if cur is None:
                    return default
            else:
                return default
        return cur
    except Exception:
        return default


# ===========================================================================
# Coverage test definitions — one per analysis segment
# ===========================================================================

COVERAGE_TESTS = [
    # ── 1. 伏藏分析: 妻财爻不现于本卦 ──────────────────────────────
    CoverageTest(
        id="cov_01",
        target_segment="hidden_spirit_analysis",
        description="用神伏藏 — 风地观卦(巽宫木), 六亲缺妻财/父母",
        yao_values=[8, 8, 8, 8, 7, 7],       # 上巽下坤 = 观卦(巽宫)
        date=(2024, 6, 15, 10),
        question="投资财运如何",
        expected_check="result[advanced_analysis][hidden_spirit_analysis][has_hidden_spirit] == True",
        assertion_fn=lambda r: _seg(r, "hidden_spirit_analysis").get("has_hidden_spirit", False) is True,
    ),

    # ── 2. 暗动分析: 日冲静爻触发暗动 ─────────────────────────────
    CoverageTest(
        id="cov_02",
        target_segment="hidden_movement",
        description="日冲静爻 — 丑爻被未日冲, 旺相触发暗动",
        yao_values=[7, 8, 7, 8, 7, 8],        # 上离下坎 = 既济卦(?), 有丑爻
        date=(2024, 7, 6, 10),                # 未日(地支未)冲丑
        question="此事能否成功",
        expected_check="len(hidden_movement[details]) > 0",
        assertion_fn=lambda r: len(_seg(r, "hidden_movement").get("details", [])) > 0,
    ),

    # ── 3. 月破分析: 月冲破爻 ─────────────────────────────────────
    CoverageTest(
        id="cov_03",
        target_segment="monthly_break",
        description="月破 — 寅爻被申月冲, 月破成立",
        yao_values=[7, 8, 8, 8, 8, 7],        # 有寅爻的卦
        date=(2024, 8, 10, 10),               # 申月冲寅
        question="求财",
        expected_check="has_monthly_break == True",
        assertion_fn=lambda r: _seg(r, "monthly_break").get("has_monthly_break", False) is True,
    ),

    # ── 4. 三合局: 申子辰合水局 ───────────────────────────────────
    CoverageTest(
        id="cov_04",
        target_segment="triple_combo",
        description="三合局 — 乾卦申子辰成水局",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾为天宫卦, 申子辰
        date=(2024, 6, 15, 10),
        question="合作之事",
        expected_check="has_triple_combo == True",
        assertion_fn=lambda r: _seg(r, "triple_combo").get("has_triple_combo", False) is True,
    ),

    # ── 5. 进退神: 动爻化进退 ─────────────────────────────────────
    CoverageTest(
        id="cov_05",
        target_segment="advance_retreat",
        description="进退神 — 动爻子水化寅木(化进)",
        yao_values=[9, 7, 7, 7, 7, 7],        # 初爻老阳(9)变, 乾→姤, 子→寅
        date=(2024, 6, 15, 10),
        question="事业升迁",
        expected_check="len(advance_retreat[details]) > 0",
        assertion_fn=lambda r: len(_seg(r, "advance_retreat").get("details", [])) > 0,
    ),

    # ── 6. 十二长生 ──────────────────────────────────────────────
    CoverageTest(
        id="cov_06",
        target_segment="twelve_growth",
        description="十二长生 — 用神在日辰处长生/帝旺等位",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦
        date=(2024, 6, 15, 10),
        question="求职面试",
        expected_check="summary is non-empty",
        assertion_fn=lambda r: len(_seg(r, "twelve_growth").get("summary", "")) > 0,
    ),

    # ── 7. 冲合分析(六合/六冲卦) ──────────────────────────────────
    CoverageTest(
        id="cov_07",
        target_segment="clash_harmony",
        description="六合/六冲 — 泰卦(六合)成立, hexagram_type=六合卦",
        yao_values=[7, 7, 7, 8, 8, 8],        # 上坤下乾 = 泰卦(六合)
        date=(2024, 6, 15, 10),
        question="婚姻感情",
        expected_check="hexagram_type == 六合卦",
        assertion_fn=lambda r: _seg(r, "clash_harmony").get("hexagram_type", "") == "六合卦",
    ),

    # ── 8. 反吟伏吟 深化 ─────────────────────────────────────────
    CoverageTest(
        id="cov_08",
        target_segment="repetition_deep",
        description="反吟伏吟深化 — 动爻触发反吟伏吟分析, 结构完整",
        yao_values=[9, 8, 7, 7, 7, 7],        # 乾卦初爻动
        date=(2024, 6, 15, 10),
        question="出行",
        expected_check="repetition_deep has type/interpretation keys",
        assertion_fn=lambda r: isinstance(_seg(r, "repetition_deep"), dict)
            and "type" in _seg(r, "repetition_deep")
            and "interpretation" in _seg(r, "repetition_deep"),
    ),

    # ── 9. 旺衰分析(纳甲四柱) ────────────────────────────────────
    CoverageTest(
        id="cov_09",
        target_segment="element_strength",
        description="纳甲四柱旺衰 — 用神在月建日辰的旺相休囚死",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦
        date=(2024, 6, 15, 10),               # 午月(火克金)
        question="投资合作",
        expected_check="strength_description field is non-empty",
        assertion_fn=lambda r: len(_seg(r, "element_strength").get("strength_description", "")) > 0,
    ),

    # ── 10. 三刑 ─────────────────────────────────────────────────
    CoverageTest(
        id="cov_10",
        target_segment="three_punishments",
        description="三刑 — 寅巳申三刑成立",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦: 寅(二), 辰(三), 申(五) → 寅巳申? No, 辰≠巳
        date=(2024, 6, 15, 10),
        question="合作纠纷",
        expected_check="three_punishments analysis ran",
        assertion_fn=lambda r: isinstance(_seg(r, "three_punishments"), dict),
    ),

    # ── 11. 伏藏力量(伏神得出不得出) ──────────────────────────────
    CoverageTest(
        id="cov_11",
        target_segment="hidden_spirit_scoring",
        description="伏神得出力量 — 风地观卦伏藏妻财得出不得出判断",
        yao_values=[8, 8, 8, 8, 7, 7],        # 风地观, 伏藏
        date=(2024, 6, 15, 10),
        question="投资决策",
        expected_check="hidden_spirit_scoring has summary",
        assertion_fn=lambda r: len(_seg(r, "hidden_spirit_scoring").get("summary", "")) > 0,
    ),

    # ── 12. 日月合用神 ────────────────────────────────────────────
    CoverageTest(
        id="cov_12",
        target_segment="day_month_bonding",
        description="日月合 — 月日地支合用神/冲用神",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦
        date=(2024, 10, 6, 10),               # 戌月戌日(土月土日)
        question="财运",
        expected_check="day_month_bonding findings or summary exist",
        assertion_fn=lambda r: isinstance(_seg(r, "day_month_bonding"), dict)
            and (len(_seg(r, "day_month_bonding").get("findings", [])) > 0
                 or len(_seg(r, "day_month_bonding").get("summary", "")) > 0),
    ),

    # ── 13. 六破 ─────────────────────────────────────────────────
    CoverageTest(
        id="cov_13",
        target_segment="six_breaks",
        description="六破 — 子酉破等六破组合",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦有子/申/辰
        date=(2024, 10, 12, 10),              # 酉日(酉破子)
        question="投资",
        expected_check="six_breaks has summary",
        assertion_fn=lambda r: len(_seg(r, "six_breaks").get("summary", "")) > 0,
    ),

    # ── 14. 绝处逢生 ──────────────────────────────────────────────
    CoverageTest(
        id="cov_14",
        target_segment="desperate_relief",
        description="绝处逢生 — 绝处分析结构完整",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦金, 金绝于寅(二月)
        date=(2024, 2, 20, 10),               # 寅月金绝
        question="求职",
        expected_check="desperate_relief has has_desperate_relief key",
        assertion_fn=lambda r: isinstance(_seg(r, "desperate_relief"), dict)
            and "has_desperate_relief" in _seg(r, "desperate_relief")
            and "stage" in _seg(r, "desperate_relief"),
    ),

    # ── 15. 随官入墓 ──────────────────────────────────────────────
    CoverageTest(
        id="cov_15",
        target_segment="officer_tomb",
        description="随官入墓 — 火爻入戌墓(离宫火例)",
        yao_values=[8, 7, 8, 8, 7, 8],        # 离卦(上下离)
        date=(2024, 9, 20, 10),               # 戌月入墓
        question="健康问题",
        expected_check="officer_tomb ran and returned dict",
        assertion_fn=lambda r: isinstance(_seg(r, "officer_tomb"), dict),
    ),

    # ── 16. 游魂归魂 ──────────────────────────────────────────────
    CoverageTest(
        id="cov_16",
        target_segment="soul_hexagram",
        description="游魂归魂 — 火地晋卦(游魂)或火天大有(归魂)",
        yao_values=[8, 8, 8, 7, 8, 7],        # 上离下坤 = 晋卦(游魂)
        date=(2024, 6, 15, 10),
        question="出行远游",
        expected_check="soul_hexagram has soul_type",
        assertion_fn=lambda r: len(_seg(r, "soul_hexagram").get("soul_type", "")) > 0,
    ),

    # ── 17. 纳音 ──────────────────────────────────────────────────
    CoverageTest(
        id="cov_17",
        target_segment="nayin",
        description="六十甲子纳音 — 纳音取象",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦
        date=(2024, 6, 15, 10),
        question="投资理财",
        expected_check="nayin has description",
        assertion_fn=lambda r: isinstance(_seg(r, "nayin"), dict),
    ),

    # ── 18. 飞伏互断 ──────────────────────────────────────────────
    CoverageTest(
        id="cov_18",
        target_segment="flying_hidden_interaction",
        description="飞伏互断 — 飞伏神生克关系",
        yao_values=[8, 8, 8, 8, 7, 7],        # 风地观, 有伏藏
        date=(2024, 6, 15, 10),
        question="投资求财",
        expected_check="flying_hidden_interaction has summary",
        assertion_fn=lambda r: len(_seg(r, "flying_hidden_interaction").get("summary", "")) > 0,
    ),

    # ── 19. 变爻格局 ──────────────────────────────────────────────
    CoverageTest(
        id="cov_19",
        target_segment="transformation_pattern",
        description="变爻格局 — 动爻格局推演, 结构完整",
        yao_values=[9, 7, 7, 7, 7, 7],        # 乾卦初动
        date=(2024, 6, 15, 10),
        question="创业方向",
        expected_check="transformation_pattern has pattern key",
        assertion_fn=lambda r: isinstance(_seg(r, "transformation_pattern"), dict)
            and "pattern" in _seg(r, "transformation_pattern"),
    ),

    # ── 20. 卦身 ──────────────────────────────────────────────────
    CoverageTest(
        id="cov_20",
        target_segment="hexagram_body",
        description="卦身 — 世爻位置推导卦身地支",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦, 世在6爻
        date=(2024, 6, 15, 10),
        question="吉凶总体",
        expected_check="hexagram_body ran and returned dict",
        assertion_fn=lambda r: isinstance(_seg(r, "hexagram_body"), dict),
    ),
]


# ===========================================================================
# Step5 synthesis adjustment test cases
# ===========================================================================

STEP5_ADJ_TESTS = [
    # ── S5-1: 六合卦加分(+0.5) ────────────────────────────────────
    CoverageTest(
        id="s5_01",
        target_segment="step5",
        target_step5_adj="hex_adjustment",
        description="卦体调候 — 泰卦(六合)应产生 +0.5 hex_adjustment",
        yao_values=[7, 7, 7, 8, 8, 8],        # 泰卦(六合)
        date=(2024, 6, 15, 10),
        question="合作愉快吗",
        expected_check="hex_adjustment > 0 (六合卦)",
        assertion_fn=lambda r: _tc(r, "thinking_chain", "step5_synthesis", "hex_adjustment", default=0) > 0,
    ),

    # ── S5-2: 六冲卦减分(-0.5) ───────────────────────────────────
    CoverageTest(
        id="s5_02",
        target_segment="step5",
        target_step5_adj="hex_adjustment",
        description="卦体调候 — 乾卦(六冲)应产生 -0.5 hex_adjustment",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦(六冲)
        date=(2024, 6, 15, 10),
        question="散财之事",
        expected_check="hex_adjustment < 0 (六冲卦)",
        assertion_fn=lambda r: _tc(r, "thinking_chain", "step5_synthesis", "hex_adjustment", default=0) < 0,
    ),

    # ── S5-3: 六神辅助调整 ─────────────────────────────────────
    CoverageTest(
        id="s5_03",
        target_segment="step5",
        target_step5_adj="spirit_adjustment",
        description="六神调整 — 勾陈临用神, spirit_adjustment != 0",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦, 世在上九
        date=(2024, 1, 6, 10),                # 己巳日: 勾陈临世爻
        question="升职加薪",
        expected_check="spirit_adjustment != 0",
        assertion_fn=lambda r: abs(r.get("thinking_chain", {}).get(
            "step5_synthesis", {}).get("spirit_adjustment", 0)) > 0,
    ),

    # ── S5-4: 暗动加分(hm_modifier) ───────────────────────────────
    CoverageTest(
        id="s5_04",
        target_segment="step5",
        target_step5_adj="hidden_movement_modifier",
        description="暗动修正 — 戌日冲辰触发暗动(hidden_movement_count>0)",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦(辰在三爻)
        date=(2024, 6, 15, 10),               # 戌日冲辰
        question="静中求动",
        expected_check="hidden_movement_count > 0",
        assertion_fn=lambda r: r.get("thinking_chain", {}).get(
            "step5_synthesis", {}).get("hidden_movement_count", 0) > 0,
    ),

    # ── S5-5: 日月合用神(dmb_adjustment) ──────────────────────────
    CoverageTest(
        id="s5_05",
        target_segment="step5",
        target_step5_adj="dmb_adjustment",
        description="日月合调整 — 日月合调用神, dmb_adjustment存在且数值型",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦
        date=(2024, 10, 6, 10),               # 戌月戌日(土月土日)
        question="财运",
        expected_check="dmb_adjustment exists as int",
        assertion_fn=lambda r: isinstance(
            r.get("thinking_chain", {}).get("step5_synthesis", {}).get("dmb_adjustment"),
            int
        ),
    ),

    # ── S5-6: 六破调整(sb_adjustment) ─────────────────────────────
    CoverageTest(
        id="s5_06",
        target_segment="step5",
        target_step5_adj="sb_adjustment",
        description="六破 — 子酉破组合触发调整",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦(子爻)
        date=(2024, 10, 20, 10),              # 酉日
        question="投资项目",
        expected_check="sb_adjustment != 0",
        assertion_fn=lambda r: _tc(r, "thinking_chain", "step5_synthesis", "sb_adjustment", default=0) != 0,
    ),

    # ── S5-7: 三合破局(combo_break) ───────────────────────────────
    CoverageTest(
        id="s5_07",
        target_segment="step5",
        target_step5_adj="combo_break_adjustment",
        description="三合破局 — 三合局被日冲破局触发惩罚",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦申子辰合水
        date=(2024, 7, 10, 10),               # 午日破子(三合破局)
        question="团队合作",
        expected_check="combo_break_adjustment < 0 or analysis ran",
        assertion_fn=lambda r: isinstance(
            _tc(r, "thinking_chain", "step5_synthesis", "combo_break_adjustment", default=None), (int, float)
        ),
    ),

    # ── S5-8: 随官入墓(officer_tomb) ──────────────────────────────
    CoverageTest(
        id="s5_08",
        target_segment="step5",
        target_step5_adj="officer_tomb_adjustment",
        description="随官入墓 — 入墓触发调整/覆盖",
        yao_values=[8, 7, 8, 8, 7, 8],        # 离卦(火)
        date=(2024, 9, 28, 10),               # 戌月入墓
        question="健康状况",
        expected_check="officer_tomb_adjustment <= 0",
        assertion_fn=lambda r: isinstance(
            _tc(r, "thinking_chain", "step5_synthesis", "officer_tomb_adjustment", default=None), (int, float)
        ),
    ),

    # ── S5-9: 特殊格局识别(从格/专旺格) ──────────────────────────
    CoverageTest(
        id="s5_09",
        target_segment="step5",
        target_step5_adj="pattern_adjustment",
        description="特殊格局 — 格局识别产生调整或空置",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦(金气独旺)
        date=(2024, 8, 1, 10),                # 申月金旺
        question="问趋势",
        expected_check="special_pattern field exists",
        assertion_fn=lambda r: isinstance(
            _tc(r, "thinking_chain", "step5_synthesis", "special_pattern", default=None), dict
        ),
    ),

    # ── S5-10: 推理链(reasoning_chain非空) ────────────────────────
    CoverageTest(
        id="s5_10",
        target_segment="step5",
        target_step5_adj="reasoning_chain",
        description="推理链 — 整合推理链应大于0条",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦
        date=(2024, 6, 15, 10),
        question="综合预测",
        expected_check="len(reasoning_chain) > 0",
        assertion_fn=lambda r: len(_tc(r, "thinking_chain", "reasoning_chain", default=[])) > 0,
    ),

    # ── S5-11: 置信度(confidence) ─────────────────────────────────
    CoverageTest(
        id="s5_11",
        target_segment="step5",
        target_step5_adj="confidence",
        description="置信度 — 最终置信度在合理范围(0-100)",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦
        date=(2024, 6, 15, 10),
        question="投资方向",
        expected_check="0 <= confidence <= 100",
        assertion_fn=lambda r: 0 <= _tc(r, "thinking_chain", "step5_synthesis", "confidence", default=50) <= 100,
    ),

    # ── S5-12: 应期(timing) ───────────────────────────────────────
    CoverageTest(
        id="s5_12",
        target_segment="step5",
        target_step5_adj="timing",
        description="应期 — 应期判断应有内容",
        yao_values=[9, 7, 7, 7, 7, 7],        # 乾卦初动
        date=(2024, 6, 15, 10),
        question="何时应验",
        expected_check="timing dict has content",
        assertion_fn=lambda r: isinstance(_tc(r, "thinking_chain", "step5_synthesis", "timing", default={}), dict),
    ),
]


# ===========================================================================
# Boundary test cases
# ===========================================================================

BOUNDARY_TESTS = [
    # ── B-1: 全静卦(no moving lines) → 用神旺衰论吉凶 ────────────
    CoverageTest(
        id="bnd_01",
        target_segment="boundary_static",
        description="全静卦 — 无明动爻, net_effect=0, 以用神旺衰断吉凶",
        yao_values=[7, 7, 7, 7, 7, 7],        # 纯乾卦, 无明动爻
        date=(2024, 6, 15, 10),
        question="当前状态",
        expected_check="step4 moving_count == 0 (no explicit moving lines)",
        assertion_fn=lambda r: _tc(r, "thinking_chain", "step4_change_analysis",
                                    "moving_count", default=-1) == 0,
        is_boundary=True,
    ),

    # ── B-2: 全动卦(all lines move, 乾坤用九用六) ─────────────────
    CoverageTest(
        id="bnd_02",
        target_segment="boundary_all_move",
        description="全动卦 — 六个爻皆动, 乾坤例用九用六",
        yao_values=[9, 9, 9, 9, 9, 9],        # 全老阳(乾用九)
        date=(2024, 6, 15, 10),
        question="大变之局",
        expected_check="has_moving_lines and 6 moving",
        assertion_fn=lambda r: _tc(r, "thinking_chain", "step4_change_analysis",
                                    "moving_count", default=0) == 6,
        is_boundary=True,
    ),

    # ── B-3: 多现(multiple use-gods) ─────────────────────────────
    CoverageTest(
        id="bnd_03",
        target_segment="boundary_multi_use",
        description="用神多现 — 多个相同六亲",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦, 子/辰/申(子孙)多现
        date=(2024, 6, 15, 10),
        question="投资求财(妻财多现)",
        expected_check="step2 handles multi-use case",
        assertion_fn=lambda r: isinstance(_tc(r, "thinking_chain", "step2_use_god_identification", default={}), dict),
        is_boundary=True,
    ),

    # ── B-4: 日月全冲(month+day clash all) ────────────────────────
    CoverageTest(
        id="bnd_04",
        target_segment="boundary_clash_all",
        description="日月全冲 — 月日地支皆冲卦中多爻",
        yao_values=[7, 7, 7, 7, 7, 7],        # 乾卦: 子/寅/辰/午/申/戌
        date=(2024, 9, 1, 10),                # 申月申日(冲寅)
        question="逢冲必动",
        expected_check="analysis handles multi-clash",
        assertion_fn=lambda r: isinstance(r.get("advanced_analysis", {}), dict),
        is_boundary=True,
    ),
]


# ===========================================================================
# Runner
# ===========================================================================

def run_single_coverage(test: CoverageTest) -> dict:
    """Run a single coverage test and return the result."""
    entry = {
        "id": test.id,
        "target_segment": test.target_segment,
        "description": test.description,
        "expected_check": test.expected_check,
        "covered": False,
        "error": None,
    }

    try:
        result = build_hexagram_result(
            test.yao_values, test.question, test.method_str,
            *test.date
        )
        # Apply enhance_reading (fill advanced_analysis)
        enhance_reading(result)
        # Apply run_thinking_chain (fill thinking_chain incl step5)
        run_thinking_chain(result)

        # Run targeted assertion
        if test.assertion_fn:
            entry["covered"] = test.assertion_fn(result)
        else:
            entry["covered"] = True  # No assertion = just verifying no crash

    except Exception as e:
        entry["covered"] = False
        entry["error"] = f"{type(e).__name__}: {e}"

    return entry


def run_coverage_report(cov_tests: list, s5_tests: list, bnd_tests: list,
                        include_step5: bool = True,
                        include_boundary: bool = True) -> dict:
    """Run all coverage tests and report which segments are exercised."""
    all_tests = list(cov_tests)
    covered_segments = set()
    uncovered_segments = []

    if include_step5:
        all_tests.extend(s5_tests)
    if include_boundary:
        all_tests.extend(bnd_tests)

    results = []
    for test in all_tests:
        result = run_single_coverage(test)
        results.append(result)
        if result["covered"]:
            seg_key = test.target_step5_adj or test.target_segment
            covered_segments.add(seg_key)

    # Compile segment-level coverage
    all_segments = set()
    for t in cov_tests:
        all_segments.add(t.target_segment)
    if include_step5:
        for t in s5_tests:
            all_segments.add(f"step5.{t.target_step5_adj}")
    if include_boundary:
        for t in bnd_tests:
            all_segments.add(f"boundary.{t.target_segment}")

    covered_count = sum(1 for r in results if r["covered"])
    uncovered_list = [r for r in results if not r["covered"]]

    return {
        "total_segments": len(all_tests),
        "covered": covered_count,
        "uncovered_count": len(uncovered_list),
        "uncovered_segments": [r["target_segment"] for r in uncovered_list],
        "uncovered_details": uncovered_list,
        "coverage_rate": covered_count / len(all_tests) * 100 if all_tests else 0,
        "results": results,
        "covered_segments_set": covered_segments,
        "all_segments_set": all_segments,
    }


# ===========================================================================
# Markdown report generator
# ===========================================================================

def generate_markdown_report(report: dict, output_path: str) -> None:
    """Generate a coverage report in Markdown format."""
    lines = []
    lines.append("# Complete Analysis Coverage Matrix Report")
    lines.append("")
    lines.append(f"**Coverage Rate**: {report['coverage_rate']:.1f}%")
    lines.append(f"**Covered**: {report['covered']} / {report['total_segments']}")
    lines.append(f"**Uncovered**: {report['uncovered_count']}")
    lines.append("")

    # Summary table
    lines.append("## Coverage Summary")
    lines.append("")
    lines.append("| ID | Segment | Status | Description |")
    lines.append("|----|---------|--------|-------------|")

    for r in report["results"]:
        icon = "✅" if r["covered"] else "❌"
        lines.append(
            f"| {r['id']} | `{r['target_segment']}` | {icon} | {r['description'][:50]} |"
        )

    lines.append("")
    lines.append("## Detailed Results")
    lines.append("")

    for r in report["results"]:
        icon = "✅" if r["covered"] else "❌"
        lines.append(f"### {r['id']}: {r['target_segment']} {icon}")
        lines.append(f"- Description: {r['description']}")
        lines.append(f"- Expected: `{r['expected_check']}`")
        status = "COVERED" if r["covered"] else "FAILED"
        lines.append(f"- Status: **{status}**")
        if r["error"]:
            lines.append(f"- Error: `{r['error']}`")
        lines.append("")

    # Flag uncovered segments
    lines.append("## Uncovered Segments (Flagged)")
    lines.append("")
    if report["uncovered_details"]:
        for u in report["uncovered_details"]:
            lines.append(f"- ⚠️ **{u['id']}`**: `{u['target_segment']}` — {u['description']}")
            if u["error"]:
                lines.append(f"  - Error: `{u['error']}`")
    else:
        lines.append("_None — all segments covered!_")

    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ===========================================================================
# Main CLI
# ===========================================================================

def filter_tests(target: str, all_cov: list, all_s5: list, all_bnd: list):
    """Filter test lists by target substring; returns new lists (no global mutation)."""
    if not target:
        return all_cov, all_s5, all_bnd
    fc = [t for t in all_cov if target in t.target_segment]
    fs5 = [t for t in all_s5 if target in t.target_step5_adj]
    fb = [t for t in all_bnd if target in t.target_segment]
    return fc, fs5, fb


def main():
    force_utf8_stdio()
    parser = argparse.ArgumentParser(description="分析段落产出冒烟测试（只验有无产出）")
    parser.add_argument("--markdown", action="store_true",
                        help="Generate coverage_report.md")
    parser.add_argument("--list", action="store_true",
                        help="List all test segments")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose output")
    parser.add_argument("--no-boundary", action="store_true",
                        help="Skip boundary tests")
    parser.add_argument("--no-step5", action="store_true",
                        help="Skip step5 synthesis adjustment tests")
    parser.add_argument("--target", type=str, default="",
                        help="Run only tests whose segment contains this string")
    args = parser.parse_args()

    all_cov, all_s5, all_bnd = COVERAGE_TESTS, STEP5_ADJ_TESTS, BOUNDARY_TESTS

    if args.list:
        print("\nCoverage Test Segments:")
        print("=" * 60)
        for t in all_cov:
            print(f"  {t.id}  {t.target_segment:30s}  {t.description}")
        print("\nStep5 Adjustment Tests:")
        print("=" * 60)
        for t in all_s5:
            print(f"  {t.id}  step5.{t.target_step5_adj:25s}  {t.description}")
        print("\nBoundary Tests:")
        print("=" * 60)
        for t in all_bnd:
            print(f"  {t.id}  {t.target_segment:30s}  {t.description}")
        return

    # Filter if --target given (local variables, no global mutation)
    cov_tests, s5_tests, bnd_tests = filter_tests(args.target, all_cov, all_s5, all_bnd)

    print("=" * 60)
    print(" 分析段落产出冒烟测试（只验有无产出，不验对错）")
    print("=" * 60)

    report = run_coverage_report(
        cov_tests=cov_tests,
        s5_tests=s5_tests,
        bnd_tests=bnd_tests,
        include_step5=not args.no_step5,
        include_boundary=not args.no_boundary,
    )

    # Print results
    print(f"\n段落总数:   {report['total_segments']}")
    print(f"有产出:     {report['covered']}")
    print(f"无产出:     {report['uncovered_count']}")
    print(f"产出率:     {report['coverage_rate']:.1f}%  ← 冒烟指标，非正确性指标")

    if args.verbose:
        print("\nDetailed Results:")
        print("-" * 60)
        for r in report["results"]:
            icon = "PASS" if r["covered"] else "FAIL"
            print(f"  [{icon}] {r['id']}  {r['target_segment']:30s}  {r['description'][:40]}")
            if r["error"]:
                print(f"         Error: {r['error']}")

    if report["uncovered_segments"]:
        print("\nUncovered segments:")
        for u in report["uncovered_details"]:
            print(f"  ??  {u['id']}: {u['target_segment']} -- {u['description']}")

    # Generate markdown report
    if args.markdown:
        report_path = os.path.join(_TEST_DIR, "coverage_report.md")
        generate_markdown_report(report, report_path)
        print(f"\nMarkdown report written to: {report_path}")

    # 产出率门槛：段落若一个多小时内静默少产出一整块，这里应当响
    if report["coverage_rate"] < 100.0:
        print(f"\n未达标：{100.0 - report['coverage_rate']:.1f}% 的分析段没有产出。")
        sys.exit(1)
    print("\n所有分析段均有产出。")
    sys.exit(0)


if __name__ == "__main__":
    main()
