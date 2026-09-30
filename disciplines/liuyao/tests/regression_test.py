# -*- coding: utf-8 -*-
"""
六爻思维链黑箱回归测试
========================
验证思维链对所有历史案例的方向一致性。
从 case_library.md 提取至少15个古典案例，通过思维链运行并比对用神取法、
吉凶方向与古典结论是否一致。

Usage:
    py -3.12 tests/regression_test.py                     # Run all, console only
    py -3.12 tests/regression_test.py --report html       # Generate HTML report
    py -3.12 tests/regression_test.py --report json       # Generate JSON results
    py -3.12 tests/regression_test.py --report all        # Generate all reports
    py -3.12 tests/regression_test.py -v                  # Verbose output
    py -3.12 tests/regression_test.py --case reg_03       # Run single case
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# 推演模块（engine / thinking_chain）在 ../scripts。
# 本文件是测试 CLI，已从 scripts/ 迁出到 tests/（AGENTS.md：生产目录不混测试），
# 故这里显式把 scripts/ 指回 sys.path——原来靠「与本脚本同目录」是不够的。
# ---------------------------------------------------------------------------
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))              # disciplines/liuyao/tests
_SCRIPT_DIR = os.path.join(os.path.dirname(_TEST_DIR), "scripts")   # disciplines/liuyao/scripts
sys.path.insert(0, _SCRIPT_DIR)

from liuyao_engine import build_hexagram_result  # noqa: E402
from thinking_chain import run_thinking_chain  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402  (liuyao_engine 已把 core/ 加入 sys.path)


# ===========================================================================
# Historical cases extracted from case_library.md
# ===========================================================================

@dataclass
class RegressionCase:
    """Single regression test case from classical sources."""
    id: str
    name: str
    source: str
    date: tuple          # (year, month, day, hour)
    yao: list            # 6 values (6,7,8,9); index 0 = 初爻 (bottom)
    question: str
    classical_verdict: str       # "吉" | "平" | "凶"
    expected_direction: str      # "auspicious" | "mixed-fav" | "mixed-unfav" | "inauspicious"
    expected_use_god: str        # "父母" | "妻财" | "官鬼" | "子孙" | "兄弟" | "世爻"
    key_reasoning: list = field(default_factory=list)
    acceptable_bands: list = field(default_factory=list)
    expected_net_effect_sign: Optional[str] = None  # 'positive'|'negative'|'neutral'|None
    expected_strength_pattern: Optional[str] = None  # 'strong'|'medium'|'weak'|None
    classical_notes: str = ""


# ---------------------------------------------------------------------------
# 18 cases covering diverse scenarios
# ---------------------------------------------------------------------------

REGRESSION_CASES = [
    # ------------------------------------------------------------------
    # Case 01 — 占父病·用神多现·原神贪合忘克 (《黄金策》)
    # 古典: 辰月戊申日, 用神父母土临月建旺, 原神贪合忘生+忌神暗动克用 → 病重(凶)
    # 引擎: 静卦乾为天全7, 用神父母土临辰月极旺, 无暗动/贪合建模 → 大吉
    # 注意: 引擎因未建模暗动/贪合, 可能判吉而非凶; acceptable_bands 包容此差异
    # ------------------------------------------------------------------
    RegressionCase(
        id="reg_01",
        name="占父病·用神多现·原神贪合忘克",
        source="《黄金策·疾病章》",
        date=(2024, 5, 10, 10),
        yao=[7, 7, 7, 7, 7, 7],
        question="父亲近病吉凶如何",
        classical_verdict="凶",
        expected_direction="inauspicious",
        expected_use_god="父母",
        key_reasoning=["原神贪合忘克", "寅木暗动克用神辰土"],
        acceptable_bands=["inauspicious", "mixed-unfav"],
        expected_net_effect_sign="neutral",
        expected_strength_pattern="strong",
        classical_notes="引擎未建模暗动/贪合忘生, 吉凶方向可能不一致(引擎限制)",
    ),

    # ------------------------------------------------------------------
    # Case 02 — 占升官·原神缺位致凶 (《黄金策·功名章》)
    # 古典: 午月甲午日, 官鬼极旺于日月但原神妻财不动, 升官无望
    # 引擎: 火风鼎, 官鬼水在午月极弱 → 方向吻合(凶)
    # ------------------------------------------------------------------
    RegressionCase(
        id="reg_02",
        name="占升官·用神衰弱·原神缺位",
        source="《黄金策·功名章》",
        date=(2024, 6, 19, 10),
        yao=[8, 9, 7, 7, 6, 7],
        question="求升迁能否成功",
        classical_verdict="凶",
        expected_direction="inauspicious",
        expected_use_god="官鬼",
        key_reasoning=["官鬼水在午月休囚无力", "原神妻财不动用神无源"],
        acceptable_bands=["inauspicious", "mixed-unfav"],
        expected_net_effect_sign="neutral",
        expected_strength_pattern="weak",
    ),

    # ------------------------------------------------------------------
    # Case 03 — 占近病·逢冲即愈 (《黄金策·疾病章》)
    # 古典: 丑月丁卯日, 子孙用神月帮日克+化回头生, 近病逢冲即愈(吉)
    # 引擎: 地天泰(六合), 子孙金临酉日极旺 → 大吉(5.00)
    # ------------------------------------------------------------------
    RegressionCase(
        id="reg_03",
        name="占近病·六合卦·用神极旺·原神发动生用",
        source="《黄金策·疾病章》",
        # 丑月乙酉日，地天泰（坤宫三世六合卦）三爻甲辰兄弟土动 → 之卦地泽临。
        # 兄弟土为子孙金之原神，原神动而生用 ⇒ 动变净效应为正；
        # 辰化丑属化退、日月合绊稍减其力，不改总体有助。用神临日帝旺、得月建
        # 丑土之生 ⇒ 极旺；六合主缠绵，旺则合为聚不为滞 ⇒ 吉。
        # 旧夹具此处记 neutral，是爻序镜像位次下的产物；P0 修正后按古籍理重推。
        date=(2024, 1, 22, 10),
        yao=[7, 7, 9, 8, 8, 8],
        question="孩子医药什么时候好",
        classical_verdict="吉",
        expected_direction="auspicious",
        expected_use_god="子孙",
        key_reasoning=["六合卦判定正确", "子孙用神极旺", "原神发动生用为吉"],
        acceptable_bands=["auspicious", "mixed-fav"],
        expected_net_effect_sign="positive",
        expected_strength_pattern="strong",
    ),

    # ------------------------------------------------------------------
    # Case 04 — 占久病·逢冲即死 (《卜筮正宗》)
    # 古典: 未月癸亥日, 世爻子水回头克+六合变六冲 → 殆(凶)
    # 引擎: 风天小畜, 世爻极弱(0.50), 双卦调整0 → 凶(0.40) 吻合
    # ------------------------------------------------------------------
    RegressionCase(
        id="reg_04",
        name="占久病·回头克·六合冲双卦",
        source="《卜筮正宗》",
        date=(2024, 7, 14, 10),
        yao=[9, 7, 7, 8, 7, 7],
        question="久病吉凶如何",
        classical_verdict="凶",
        expected_direction="inauspicious",
        expected_use_god="世爻",
        key_reasoning=["回头克为大凶", "六合变六冲为魂魄将散"],
        acceptable_bands=["inauspicious", "mixed-unfav"],
        expected_net_effect_sign="neutral",
        expected_strength_pattern="weak",
    ),

    # ------------------------------------------------------------------
    # Case 05 — 占投资求财·妻财伏藏 (《增删卜易》)
    # 古典: 寅月丙子日, 妻财不现伏藏, 日冲出伏, 财可得但不多
    # 引擎: 水雷屯, 伏藏detection正确, default 2.5分平吉
    # ------------------------------------------------------------------
    RegressionCase(
        id="reg_05",
        name="占求财·妻财伏藏·飞神被冲出伏",
        source="《增删卜易·求财章》",
        date=(2024, 2, 16, 10),
        yao=[7, 6, 8, 8, 9, 8],
        question="投资求财得失如何",
        classical_verdict="平",
        expected_direction="mixed-fav",
        expected_use_god="妻财",
        key_reasoning=["妻财不现正确识别", "伏藏检测正确(step2 has_fu_cang=True)"],
        acceptable_bands=["mixed-fav", "inauspicious"],
        expected_net_effect_sign="neutral",
        expected_strength_pattern="medium",
    ),

    # ------------------------------------------------------------------
    # Case 06 — 占婚姻·六合卦·用神中和 (仿古《黄金策》)
    # 古典: 寅月戊寅日, 六合卦+用神中和, 婚姻可成但宜缓(平吉)
    # 引擎: 雷地豫(六合), 妻财持世 → 平吉(2.90)
    # ------------------------------------------------------------------
    RegressionCase(
        id="reg_06",
        name="占婚姻·六合卦·用神中和",
        source="《黄金策·婚姻章》",
        date=(2024, 2, 10, 10),
        yao=[8, 8, 8, 7, 8, 8],
        question="婚姻能否成功",
        classical_verdict="平",
        expected_direction="mixed-fav",
        expected_use_god="妻财",
        key_reasoning=["六合卦判定正确+0.5", "用神妻财正确识别"],
        acceptable_bands=["mixed-fav", "auspicious"],
        expected_net_effect_sign="neutral",
        expected_strength_pattern="medium",
    ),

    # ------------------------------------------------------------------
    # Case 07 — 占行人·用神伏藏·合绊化退 (仿古《黄金策》)
    # 古典: 子月丙寅日, 父母不现伏藏, 子孙化退绊住原神, 行人凶
    # 引擎: 雷水解, 伏藏检测正确, 动变负 → 凶
    # ------------------------------------------------------------------
    RegressionCase(
        id="reg_07",
        name="占行人·用神伏藏·合绊化退",
        source="《黄金策·出行章》",
        date=(2024, 12, 12, 10),
        yao=[8, 9, 8, 7, 6, 8],
        question="父亲出行何日回来",
        classical_verdict="凶",
        expected_direction="inauspicious",
        expected_use_god="父母",
        key_reasoning=["父母不现正确识别", "伏藏检测正确(step2 has_fu_cang=True)"],
        acceptable_bands=["inauspicious", "mixed-unfav"],
        expected_net_effect_sign="negative",
        expected_strength_pattern="medium",
    ),

    # ------------------------------------------------------------------
    # Case 08 — 占子久病·子孙极弱·动变双凶 (仿古《卜筮正宗》)
    # 古典: 午月庚子日, 子孙极弱(0.50)+动变重负(-2.0) → 大凶(0.00)
    # 引擎: 地山谦, 方向完美吻合
    # ------------------------------------------------------------------
    RegressionCase(
        id="reg_08",
        name="占子久病·子孙极弱·动变双凶",
        source="《卜筮正宗》",
        date=(2024, 6, 8, 10),
        yao=[8, 8, 7, 8, 6, 8],
        question="儿子久病能好否",
        classical_verdict="凶",
        expected_direction="inauspicious",
        expected_use_god="子孙",
        key_reasoning=["子孙极弱无力", "动变双凶回头克+化退"],
        acceptable_bands=["inauspicious"],
        expected_net_effect_sign="negative",
        expected_strength_pattern="weak",
    ),

    # ------------------------------------------------------------------
    # Case 09 — 从格检测·用神极弱 (仿古从格案例)
    # 古典: 极弱用神顺势从强, 弃命从强旺之神
    # 引擎: step5格局识别功能, 官鬼极弱判凶(常规)或从格(特殊)
    # ------------------------------------------------------------------
    RegressionCase(
        id="reg_09",
        name="从格检测·用神极弱·原神无援",
        source="《黄金策·功名章》",
        date=(2024, 6, 15, 10),
        yao=[8, 8, 7, 7, 8, 8],
        question="测事业",
        classical_verdict="凶",
        expected_direction="inauspicious",
        expected_use_god="官鬼",
        key_reasoning=["从格检测为思维链推理的一部分", "special_pattern字段应存在"],
        acceptable_bands=["inauspicious", "mixed-unfav"],
        expected_net_effect_sign="neutral",
        expected_strength_pattern="weak",
    ),

    # ------------------------------------------------------------------
    # Case 10 — 占行人久出·伏吟极弱·静卦停滞 (仿古《增删卜易》)
    # 古典: 坤为地静卦伏吟, 用神极弱, 静极思动, 待时而动(凶)
    # ------------------------------------------------------------------
    RegressionCase(
        id="reg_10",
        name="占行人·伏吟极弱·静卦停滞",
        source="《增删卜易》",
        date=(2024, 6, 1, 10),
        yao=[8, 8, 8, 8, 8, 8],
        question="测事业",
        classical_verdict="凶",
        expected_direction="inauspicious",
        expected_use_god="官鬼",
        key_reasoning=["静卦伏吟之象主停滞", "官鬼水极弱"],
        acceptable_bands=["inauspicious", "mixed-unfav"],
        expected_net_effect_sign="neutral",
        expected_strength_pattern="weak",
    ),

    # ------------------------------------------------------------------
    # Case 11 — 占投资·反吟变卦·先成后败 (仿古《卜筮正宗》)
    # 古典: 反吟卦地支相冲, 主反复先聚后散, 投资凶
    # 引擎: 升→小畜变卦反吟, 用神丑土回头克 → 凶
    # ------------------------------------------------------------------
    RegressionCase(
        id="reg_11",
        name="占投资·反吟变卦·先成后败",
        source="《卜筮正宗》",
        date=(2024, 6, 15, 10),
        yao=[8, 7, 9, 6, 6, 8],
        question="投资如何",
        classical_verdict="凶",
        expected_direction="inauspicious",
        expected_use_god="妻财",
        key_reasoning=["反吟卦检测正确", "动变净效应负"],
        acceptable_bands=["inauspicious", "mixed-unfav"],
        expected_net_effect_sign="negative",
        expected_strength_pattern="strong",
    ),

    # ------------------------------------------------------------------
    # Case 12 — 占生意·三刑齐全·六合中和·吉凶相战 (仿古《黄金策》)
    # 古典: 三刑齐全(极凶)+六合(和合) → 吉凶相战, 平凶
    # 引擎: 风天小畜六合+三刑, 综合平凶
    # ------------------------------------------------------------------
    RegressionCase(
        id="reg_12",
        name="占生意·三刑齐全·六合中和·吉凶相战",
        source="《黄金策》",
        date=(2024, 5, 20, 10),
        yao=[7, 7, 7, 8, 7, 7],
        question="生意如何",
        classical_verdict="凶",
        expected_direction="mixed-unfav",
        expected_use_god="妻财",
        key_reasoning=["三刑检测正确", "六合卦判定正确+0.5"],
        acceptable_bands=["mixed-unfav", "inauspicious"],
        expected_net_effect_sign="neutral",
        expected_strength_pattern="medium",
    ),

    # ------------------------------------------------------------------
    # Case 13 — 占子病·伏神得出·伏克飞 (仿古《卜筮正宗》)
    # 古典: 申月乙巳日, 子孙伏藏, 伏克飞为得出有医, 虽重可愈(吉)
    # 引擎: 风地观, 伏藏检测 → 平吉
    # ------------------------------------------------------------------
    RegressionCase(
        id="reg_13",
        name="占子病·伏神得出·伏克飞为出",
        source="《卜筮正宗·飞神伏神论》",
        date=(2024, 8, 10, 10),
        yao=[8, 7, 8, 9, 7, 7],
        question="儿子病吉凶如何",
        classical_verdict="吉",
        expected_direction="mixed-fav",
        expected_use_god="子孙",
        key_reasoning=["伏神得出四法", "伏克飞为伏得出"],
        acceptable_bands=["mixed-fav", "auspicious"],
        expected_net_effect_sign="neutral",
        expected_strength_pattern="medium",
    ),

    # ------------------------------------------------------------------
    # Case 14 — 占官司·官鬼暗动·世抗官 (仿古《增删卜易》)
    # 古典: 辰月甲寅日, 官鬼旺相暗动+世子孙克官化退 → 官司不利(凶)
    # 引擎: 天水讼, 官鬼被日冲暗动, 方向凶
    # ------------------------------------------------------------------
    RegressionCase(
        id="reg_14",
        name="占官司·官鬼暗动·世抗官化退",
        source="《增删卜易·官非章》",
        date=(2024, 5, 5, 10),
        yao=[7, 7, 8, 9, 7, 7],
        question="官司吉凶如何",
        classical_verdict="凶",
        expected_direction="inauspicious",
        expected_use_god="官鬼",
        key_reasoning=["官鬼为官方法官", "世子孙克官抗官"],
        acceptable_bands=["inauspicious", "mixed-unfav"],
        expected_net_effect_sign="negative",
        expected_strength_pattern="medium",
    ),

    # ------------------------------------------------------------------
    # Case 15 — 占合伙经营·六冲卦·世应相冲 (仿古《卜筮正宗》)
    # 古典: 六冲卦占合伙, 世应相冲, 合伙不终(凶)
    # 引擎: 震为雷六冲, 方向散
    # ------------------------------------------------------------------
    RegressionCase(
        id="reg_15",
        name="占合伙·六冲卦·世应相冲",
        source="《卜筮正宗·六冲论》",
        date=(2024, 3, 15, 10),
        yao=[7, 7, 8, 7, 7, 7],
        question="合伙经营吉凶如何",
        classical_verdict="凶",
        expected_direction="inauspicious",
        expected_use_god="妻财",
        key_reasoning=["六冲卦事散不宜成事", "世应相冲为合伙大忌"],
        acceptable_bands=["inauspicious", "mixed-unfav"],
        expected_net_effect_sign="neutral",
        expected_strength_pattern="medium",
    ),

    # ------------------------------------------------------------------
    # Case 16 — 占六合出行·事聚不宜散 (仿古《卜筮正宗》)
    # 古典: 六合卦出行有阻, 须待冲开(平/凶)
    # 引擎: 水泽节六合卦, 世持官鬼 → 凶
    # ------------------------------------------------------------------
    RegressionCase(
        id="reg_16",
        name="占出行·六合卦·事阻延迟",
        source="《卜筮正宗·六合论》",
        date=(2024, 6, 25, 10),
        yao=[7, 7, 7, 6, 7, 7],
        question="出行远游吉凶如何",
        classical_verdict="凶",
        expected_direction="inauspicious",
        expected_use_god="世爻",
        key_reasoning=["六合卦事聚不宜散", "官鬼持世途中恐有灾祸"],
        acceptable_bands=["inauspicious", "mixed-unfav"],
        expected_net_effect_sign="neutral",
        expected_strength_pattern="medium",
    ),

    # ------------------------------------------------------------------
    # Case 17 — 占考试功名·父母官鬼双用神 (仿古《黄金策》)
    # 古典: 戌月癸卯日, 父母旺相+原神有力 → 功名可中但非前茅(平吉)
    # 引擎: 火地晋, 双用神分析 → 吉
    # ------------------------------------------------------------------
    RegressionCase(
        id="reg_17",
        name="占考试功名·父母旺相·官鬼得生",
        source="《黄金策·功名章》",
        date=(2024, 10, 20, 10),
        yao=[7, 7, 7, 7, 7, 9],
        question="科举考试功名如何",
        classical_verdict="平",
        expected_direction="mixed-fav",
        expected_use_god="官鬼",
        key_reasoning=["功名占须取父母与官鬼双用神", "原神有力生官鬼"],
        acceptable_bands=["mixed-fav", "auspicious"],
        expected_net_effect_sign="positive",
        expected_strength_pattern="medium",
    ),

    # ------------------------------------------------------------------
    # Case 18 — 占求财·兄弟持世·子孙通关化退 (仿古《增删卜易》)
    # 古典: 亥月甲寅日, 财旺但世持兄弟, 子孙通关化退 → 求财不利(凶)
    # 引擎: 风雷益六合, 世持兄弟 → 方向凶/平凶
    # ------------------------------------------------------------------
    RegressionCase(
        id="reg_18",
        name="占求财·兄弟持世·子孙通关不力",
        source="《增删卜易·求财章》",
        date=(2024, 11, 15, 10),
        yao=[7, 7, 7, 9, 7, 7],
        question="投资经营求财得失",
        classical_verdict="凶",
        expected_direction="inauspicious",
        expected_use_god="妻财",
        key_reasoning=["兄弟持世求财为忌", "子孙通关之力不持久"],
        acceptable_bands=["inauspicious", "mixed-unfav"],
        expected_net_effect_sign="negative",
        expected_strength_pattern="medium",
    ),
]


# ===========================================================================
# Test execution engine
# ===========================================================================

def run_single_case(case: RegressionCase, verbose: bool = False) -> dict:
    """
    运行单个回归测试案例。

    Returns a dict with:
        case_id, case_name, hexagram, verdict, final_score,
        use_god_correct, direction_correct, band_acceptable,
        checks, reasoning_diff
    """
    year, month, day, hour = case.date
    result = build_hexagram_result(case.yao, case.question, "test", year, month, day, hour)
    chain_result = run_thinking_chain(result)
    chain = chain_result.get("thinking_chain", chain_result)

    s2 = chain.get("step2_use_god_identification", {})
    s3 = chain.get("step3_strength_analysis", {})
    s4 = chain.get("step4_change_analysis", {})
    s5 = chain.get("step5_synthesis", {})

    hex_name = result["original_hexagram"]["name"]
    verdict = s5.get("verdict", "")
    final_score = s5.get("final_score", 2.5)
    final_score = final_score if isinstance(final_score, (int, float)) else 2.5

    checks = []
    reasoning_diff = []

    # ── Check 1: 用神取用 ──
    actual_use_god = s2.get("use_god_category", "")
    use_god_ok = actual_use_god == case.expected_use_god
    checks.append({
        "name": "用神取用",
        "expected": case.expected_use_god,
        "actual": actual_use_god,
        "passed": use_god_ok,
    })
    if not use_god_ok:
        reasoning_diff.append(f"用神: 期望{case.expected_use_god}, 实际{actual_use_god}")

    # ── Check 2: 旺衰方向 ──
    level = s3.get("strength_level", "")
    score_val = s3.get("effective_score", 2.5)
    score_val = score_val if isinstance(score_val, (int, float)) else 2.5

    if case.expected_strength_pattern == "strong":
        strength_ok = ("旺" in level or "相" in level) and score_val >= 2.5
    elif case.expected_strength_pattern == "medium":
        strength_ok = ("和" in level or "中" in level) or (0.5 <= score_val < 3.5)
    elif case.expected_strength_pattern == "weak":
        strength_ok = ("弱" in level or "囚" in level or "死" in level or "衰" in level) or score_val < 1.5
    else:
        strength_ok = True  # not specified

    checks.append({
        "name": "旺衰方向",
        "expected": case.expected_strength_pattern,
        "actual": f"{level}({score_val:.2f})",
        "passed": strength_ok,
    })
    if not strength_ok:
        reasoning_diff.append(
            f"旺衰: 期望{case.expected_strength_pattern}, 实际{level}({score_val:.2f})"
        )

    # ── Check 3: 动变净效应方向 ──
    net = s4.get("net_effect", 0.0)
    net_val = net if isinstance(net, (int, float)) else 0.0

    if case.expected_net_effect_sign == "positive":
        net_ok = net_val > 0.3
    elif case.expected_net_effect_sign == "negative":
        net_ok = net_val < -0.3
    elif case.expected_net_effect_sign == "neutral":
        net_ok = abs(net_val) <= 0.5
    else:
        net_ok = True  # not specified

    checks.append({
        "name": "动变净效应",
        "expected": case.expected_net_effect_sign,
        "actual": f"{net_val:+.2f}",
        "passed": net_ok,
    })
    if not net_ok:
        reasoning_diff.append(f"动变净效应: 期望{case.expected_net_effect_sign}, 实际{net_val:+.2f}")

    # ── Check 4: 吉凶方向 ──
    actual_band = _verdict_to_band(verdict, final_score)
    direction_ok = (actual_band == case.expected_direction)

    checks.append({
        "name": "吉凶方向",
        "expected": case.expected_direction,
        "actual": actual_band,
        "passed": direction_ok,
    })
    if not direction_ok:
        reasoning_diff.append(f"吉凶方向: 期望{case.expected_direction}, 实际{actual_band}")

    # ── Check 5: Band acceptable ──
    band_acceptable = actual_band in case.acceptable_bands
    checks.append({
        "name": "可接受区间",
        "expected": case.acceptable_bands,
        "actual": actual_band,
        "passed": band_acceptable,
    })
    if not band_acceptable:
        reasoning_diff.append(f"可接受区间: 期望{case.acceptable_bands}, 实际{actual_band}")

    all_passed = all(c["passed"] for c in checks)

    return {
        "case_id": case.id,
        "case_name": case.name,
        "source": case.source,
        "hexagram": hex_name,
        "use_god_correct": use_god_ok,
        "direction_correct": direction_ok,
        "band_acceptable": band_acceptable,
        "all_passed": all_passed,
        "verdict": verdict,
        "final_score": final_score,
        "classical_verdict": case.classical_verdict,
        "expected_direction": case.expected_direction,
        "actual_direction": actual_band,
        "expected_use_god": case.expected_use_god,
        "actual_use_god": actual_use_god,
        "strength_level": level,
        "effective_score": score_val,
        "net_effect": net_val,
        "checks": checks,
        "reasoning_diff": reasoning_diff,
        "classical_notes": case.classical_notes,
        "raw_chain": chain if verbose else None,
    }


def _verdict_to_band(verdict: str, score: float) -> str:
    """将引擎 verdict 映射到期望 band."""
    if "吉" in verdict and "凶" not in verdict and "平" not in verdict:
        if "大" in verdict:
            return "auspicious"
        return "auspicious" if score >= 3.0 else "mixed-fav"
    elif "平吉" in verdict:
        return "mixed-fav"
    elif "平凶" in verdict:
        return "mixed-unfav"
    elif "凶" in verdict:
        return "inauspicious"
    else:
        # Fallback by score
        if score >= 3.0:
            return "auspicious"
        elif score >= 2.0:
            return "mixed-fav"
        elif score >= 1.0:
            return "mixed-unfav"
        else:
            return "inauspicious"


# ===========================================================================
# Regression suite runner
# ===========================================================================

def run_regression_suite(cases: list = None, verbose: bool = False) -> dict:
    """Run all regression cases and produce a report."""
    if cases is None:
        cases = REGRESSION_CASES

    results = []
    for case in cases:
        try:
            result = run_single_case(case, verbose=verbose)
        except Exception as e:
            result = {
                "case_id": case.id,
                "case_name": case.name,
                "source": case.source,
                "hexagram": "?",
                "use_god_correct": False,
                "direction_correct": False,
                "band_acceptable": False,
                "all_passed": False,
                "verdict": "ERROR",
                "final_score": 0,
                "classical_verdict": case.classical_verdict,
                "expected_direction": case.expected_direction,
                "actual_direction": "error",
                "expected_use_god": case.expected_use_god,
                "actual_use_god": "ERROR",
                "strength_level": "?",
                "effective_score": 0,
                "net_effect": 0,
                "checks": [{"name": "EXCEPTION", "expected": "", "actual": str(e), "passed": False}],
                "reasoning_diff": [f"EXCEPTION: {e}"],
                "classical_notes": str(e),
            }
        results.append(result)

    total = len(results)
    use_god_match = sum(1 for r in results if r["use_god_correct"])
    direction_match = sum(1 for r in results if r["direction_correct"])
    band_acceptable = sum(1 for r in results if r["band_acceptable"])
    all_passed_count = sum(1 for r in results if r["all_passed"])

    failed_cases = [r for r in results if not r["all_passed"]]
    band_failed = [r for r in results if not r["band_acceptable"]]

    return {
        "total": total,
        "all_passed": all_passed_count,
        "use_god_accuracy": use_god_match / total if total else 0,
        "direction_accuracy": direction_match / total if total else 0,
        "band_acceptability": band_acceptable / total if total else 0,
        "cases": results,
        "failed_cases": failed_cases,
        "band_failed_cases": band_failed,
        "summary": (
            f"方向准确率{direction_match}/{total}({direction_match/total*100:.0f}%) "
            f"| 用神准确率{use_god_match}/{total}({use_god_match/total*100:.0f}%) "
            f"| 区间可接受率{band_acceptable}/{total}({band_acceptable/total*100:.0f}%)"
        ),
    }


# ===========================================================================
# Report generators
# ===========================================================================

def generate_html_report(result: dict) -> str:
    """Generate an HTML report with tables for visual inspection."""
    html_parts = []
    html_parts.append("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>六爻思维链回归测试报告</title>
<style>
  body { font-family: "Microsoft YaHei", "SimHei", sans-serif; margin: 20px; background: #f5f5f5; }
  h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
  h2 { color: #34495e; margin-top: 30px; }
  .summary-box { background: #ecf0f1; padding: 15px; border-radius: 8px; margin: 15px 0; }
  .metric { display: inline-block; margin: 5px 15px; padding: 8px 15px; border-radius: 5px; }
  .metric.good { background: #2ecc71; color: white; }
  .metric.warn { background: #f39c12; color: white; }
  .metric.bad { background: #e74c3c; color: white; }
  table { border-collapse: collapse; width: 100%; margin: 10px 0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  th { background: #3498db; color: white; padding: 10px 8px; text-align: center; font-size: 13px; }
  td { padding: 8px; text-align: center; border-bottom: 1px solid #ddd; font-size: 13px; }
  tr:hover { background: #f0f8ff; }
  .pass { color: #27ae60; font-weight: bold; }
  .fail { color: #e74c3c; font-weight: bold; }
  .band-pass { color: #2ecc71; }
  .band-fail { color: #e67e22; }
  .diff-text { color: #7f8c8d; font-size: 12px; text-align: left; }
  .source-text { color: #95a5a6; font-size: 11px; }
  .section { margin: 20px 0; }
</style>
</head>
<body>
""")

    html_parts.append("<h1>六爻思维链回归测试报告</h1>")

    # Summary
    total = result["total"]
    dir_acc = result["direction_accuracy"] * 100
    use_acc = result["use_god_accuracy"] * 100
    band_acc = result["band_acceptability"] * 100
    all_pct = result["all_passed"] / total * 100 if total else 0

    def metric_class(val):
        if val >= 80:
            return "good"
        elif val >= 60:
            return "warn"
        else:
            return "bad"

    html_parts.append(f"""
<div class="summary-box">
  <h2 style="margin-top:0">概要</h2>
  <div class="metric {metric_class(all_pct)}">总通过率: {result['all_passed']}/{total} ({all_pct:.0f}%)</div>
  <div class="metric {metric_class(dir_acc)}">吉凶方向: {dir_acc:.0f}%</div>
  <div class="metric {metric_class(use_acc)}">用神准确率: {use_acc:.0f}%</div>
  <div class="metric {metric_class(band_acc)}">区间可接受率: {band_acc:.0f}%</div>
  <p><b>{result['summary']}</b></p>
</div>
""")

    # Main results table
    html_parts.append("""
<h2>案例明细</h2>
<table>
<tr>
  <th>ID</th><th>卦名</th><th>案例名称</th><th>出处</th>
  <th>用神(期/实)</th><th>吉凶(期/实)</th><th>古典</th><th>评分</th>
  <th>区间</th><th>状态</th><th>差异</th>
</tr>
""")

    for r in result["cases"]:
        status_class = "pass" if r["all_passed"] else "fail"
        status_text = "PASS" if r["all_passed"] else "FAIL"

        ug = f"{r['expected_use_god']}/{r['actual_use_god']}"
        ug_class = "pass" if r["use_god_correct"] else "fail"

        dir_text = f"{r['expected_direction']}/{r['actual_direction']}"
        dir_class = "pass" if r["direction_correct"] else "fail"

        band_class = "band-pass" if r["band_acceptable"] else "band-fail"

        diff = "; ".join(r.get("reasoning_diff", []))
        classical = r.get("classical_verdict", "")

        html_parts.append(f"""<tr>
  <td>{r['case_id']}</td>
  <td>{r['hexagram']}</td>
  <td style="text-align:left">{r['case_name']}</td>
  <td class="source-text">{r.get('source','')}</td>
  <td class="{ug_class}">{ug}</td>
  <td class="{dir_class}">{dir_text}</td>
  <td>{classical}</td>
  <td>{r['final_score']:.2f}</td>
  <td class="{band_class}">{r['actual_direction']}</td>
  <td class="{status_class}">{status_text}</td>
  <td class="diff-text">{diff}</td>
</tr>""")

    html_parts.append("</table>")

    # Failures detail
    if result.get("band_failed_cases"):
        html_parts.append("""
<h2>方向不一致案例详情</h2>
<table>
<tr><th>ID</th><th>案例</th><th>引擎Verdict</th><th>古典结论</th><th>差异说明</th><th>备注</th></tr>
""")
        for r in result["band_failed_cases"]:
            diff = "; ".join(r.get("reasoning_diff", []))
            notes = r.get("classical_notes", "")
            html_parts.append(f"""<tr>
  <td>{r['case_id']}</td>
  <td style="text-align:left">{r['case_name']}</td>
  <td>{r['verdict']}({r['final_score']:.2f})</td>
  <td>{r['classical_verdict']}</td>
  <td class="diff-text">{diff}</td>
  <td class="source-text">{notes}</td>
</tr>""")

        html_parts.append("</table>")

    html_parts.append("</body></html>")
    return "\n".join(html_parts)


def generate_json_report(result: dict) -> str:
    """Generate machine-readable JSON report."""
    # Strip raw_chain to keep it compact
    clean = {
        "total": result["total"],
        "all_passed": result["all_passed"],
        "use_god_accuracy": result["use_god_accuracy"],
        "direction_accuracy": result["direction_accuracy"],
        "band_acceptability": result["band_acceptability"],
        "summary": result["summary"],
        "cases": [
            {
                "case_id": r["case_id"],
                "case_name": r["case_name"],
                "source": r.get("source", ""),
                "hexagram": r["hexagram"],
                "use_god_correct": r["use_god_correct"],
                "direction_correct": r["direction_correct"],
                "band_acceptable": r["band_acceptable"],
                "all_passed": r["all_passed"],
                "verdict": r["verdict"],
                "final_score": r["final_score"],
                "classical_verdict": r["classical_verdict"],
                "expected_direction": r["expected_direction"],
                "actual_direction": r["actual_direction"],
                "expected_use_god": r["expected_use_god"],
                "actual_use_god": r["actual_use_god"],
                "strength_level": r.get("strength_level", ""),
                "effective_score": r.get("effective_score", 0),
                "net_effect": r.get("net_effect", 0),
                "reasoning_diff": r.get("reasoning_diff", []),
                "classical_notes": r.get("classical_notes", ""),
            }
            for r in result["cases"]
        ],
        "failed_case_ids": [r["case_id"] for r in result["failed_cases"]],
        "band_failed_case_ids": [r["case_id"] for r in result["band_failed_cases"]],
    }
    return json.dumps(clean, ensure_ascii=False, indent=2)


def print_console_summary(result: dict) -> None:
    """Print a compact console summary."""
    print()
    print(f"{'ID':<10} {'状态':<6} {'卦名':<8} {'用神':<6} {'吉凶方向':<20} {'古典':<4} {'评分':<6} {'CASE NAME'}")
    print("-" * 100)
    for r in result["cases"]:
        status = "PASS" if r["all_passed"] else "FAIL"
        ug_mark = "OK" if r["use_god_correct"] else "XX"
        dir_mark = "OK" if r["direction_correct"] else "XX"
        band_mark = "OK" if r["band_acceptable"] else "XX"
        print(
            f"{r['case_id']:<10} {status:<6} {r['hexagram']:<8} "
            f"ug={ug_mark} dir={dir_mark} band={band_mark} "
            f"{r['classical_verdict']:<4} {r['final_score']:<6.2f} {r['case_name']}"
        )
    print("-" * 100)
    print(f"\n{result['summary']}")
    print(f"总通过: {result['all_passed']}/{result['total']}")

    if result["band_failed_cases"]:
        print(f"\n方向不一致(不可接受): {[r['case_id'] for r in result['band_failed_cases']]}")
    if result["failed_cases"]:
        total_failed = [r["case_id"] for r in result["failed_cases"]]
        print(f"部分通过(单项失败): {[cid for cid in total_failed if cid not in [r['case_id'] for r in result['band_failed_cases']]]}")


# ===========================================================================
# CLI
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="六爻思维链黑箱回归测试 ——— 验证古典案例推理一致性",
    )
    parser.add_argument(
        "--report",
        choices=["html", "json", "all"],
        help="Generate report files (html, json, or all)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for reports (default: script directory)",
    )
    parser.add_argument(
        "--case",
        type=str,
        help="Run a single case by id (e.g. reg_03)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed reasoning",
    )
    args = parser.parse_args()
    force_utf8_stdio()

    output_dir = args.output_dir or os.path.join(os.path.dirname(_SCRIPT_DIR), "outputs")
    os.makedirs(output_dir, exist_ok=True)

    if args.case:
        case = [c for c in REGRESSION_CASES if c.id == args.case]
        if not case:
            print(f"Unknown case id: {args.case}")
            print(f"Available: {', '.join(c.id for c in REGRESSION_CASES)}")
            sys.exit(1)
        result = run_regression_suite(cases=case, verbose=args.verbose)
        # Print single case details
        c = case[0]
        r = result["cases"][0]
        print(f"\n{'='*70}")
        print(f"[{'PASS' if r['all_passed'] else 'FAIL'}] {c.id}: {c.name}")
        print(f"  出处: {c.source}")
        print(f"  卦={r['hexagram']}  verdict={r['verdict']}  score={r['final_score']:.2f}")
        print(f"  古典结论: {c.classical_verdict}")
        print(f"  用神: expected={c.expected_use_god}, actual={r['actual_use_god']} {'OK' if r['use_god_correct'] else 'FAIL'}")
        print(f"  方向: expected={c.expected_direction}, actual={r['actual_direction']} {'OK' if r['direction_correct'] else 'FAIL'}")
        print(f"  区间: acceptable={c.acceptable_bands}, actual={r['actual_direction']} {'OK' if r['band_acceptable'] else 'FAIL'}")
        if r.get("reasoning_diff"):
            print(f"  差异: {'; '.join(r['reasoning_diff'])}")
        if c.classical_notes:
            print(f"  备注: {c.classical_notes}")
        if r.get("raw_chain"):
            s5 = r["raw_chain"].get("step5_synthesis", {})
            summary = s5.get("summary_text", "")
            if summary:
                print(f"\n  推理链摘要: {summary[:200]}...")
    else:
        result = run_regression_suite(verbose=args.verbose)
        print_console_summary(result)

        # Generate reports if requested
        if args.report in ("html", "all"):
            html_path = os.path.join(output_dir, "regression_report.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(generate_html_report(result))
            print(f"\nHTML report: {html_path}")

        if args.report in ("json", "all"):
            json_path = os.path.join(output_dir, "regression_results.json")
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(generate_json_report(result))
            print(f"JSON results: {json_path}")

    # 失败必须以非零退出码报出去，否则 CI / dev_tools/check.py 看不到任何信号
    sys.exit(0 if result["all_passed"] == result["total"] else 1)


if __name__ == "__main__":
    main()
