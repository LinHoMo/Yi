# -*- coding: utf-8 -*-
"""六爻思维链：基元表 / 断语库 / 通用辅助 / 五步推演 / 应期 / 叙事组装 / 断语/模板取用器。（合并自 chain_support.py 与 chain_verdicts.py，去重 import 后保留全部公共定义；聚合入口见 thinking_chain.py）。"""

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

from chain_tables import KE_WO, SHENG_WO, STEMS, TWELVE_GROWTH, TWELVE_GROWTH_STAGES, TWELVE_GROWTH_TABLES, XUN_KONG, _TWELVE_GROWTH_SCORE


# ══════════════════════════════════════════════════════════════════════════════
# ── chain_verdicts 部分 ──
# ══════════════════════════════════════════════════════════════════════════════

# ── 断语/引文库：外置 data/verdicts.json 与 data/rules/verdict_texts.json（AGENTS.md §三），代码只留算法与加载 ──
_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_VERDICTS_PATH = _DATA_DIR / "verdicts.json"
_VERDICT_TEXTS_PATH = _DATA_DIR / "rules" / "verdict_texts.json"


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"缺断语库 {path}（应随仓库一起检出）：{exc}")


_VERDICTS = _load_json(_VERDICTS_PATH)
SHI_YAO_INTERPRETATION = _VERDICTS["shi_yao_interpretation"]
SHI_YAO_POEMS = _VERDICTS["shi_yao_poems"]
QUOTE_DATABASE = _VERDICTS["quote_database"]

_VERDICT_TEXTS = _load_json(_VERDICT_TEXTS_PATH)
STEP5_CLASSICAL_NOTES = _VERDICT_TEXTS["step5_classical_notes"]
STEP5_VERDICT_DESCS = _VERDICT_TEXTS["step5_verdict_descs"]
STEP5_SPIRIT_REASONS = _VERDICT_TEXTS["step5_spirit_reasons"]
STEP5_FACTOR_REASONS = _VERDICT_TEXTS["step5_factor_reasons"]
STEP5_CONFIDENCE = _VERDICT_TEXTS["step5_confidence"]
STEP5_YINGQI = _VERDICT_TEXTS["step5_yingqi_texts"]
CLASSICAL_INTERPRETATIONS = _VERDICT_TEXTS["classical_interpretations"]
CHAIN_SUPPORT_NOTES = _VERDICT_TEXTS.get("chain_support_notes", {})
CLASSICAL_RULES_NOTES = _VERDICT_TEXTS.get("classical_rules_notes", {})
CLASSICAL_RULES_TEMPLATES = _VERDICT_TEXTS.get("classical_rules_templates", {})
PATTERN_VERDICTS = _VERDICT_TEXTS.get("pattern_verdicts", {})
EFFECT_LABELS = _VERDICT_TEXTS.get("effect_labels", {})
EFFECT_PHRASES = _VERDICT_TEXTS.get("effect_phrases", {})
BING_YAO_LABELS = _VERDICT_TEXTS.get("bing_yao_labels", {})
NARRATIVE_HINTS = _VERDICT_TEXTS.get("narrative_hints", {})
STRENGTH_REASON_MAP = _VERDICT_TEXTS.get("strength_reason_map", {})
STRENGTH_POLARITY_MAP = _VERDICT_TEXTS.get("strength_polarity_map", {})
PATTERN_RELATED = _VERDICT_TEXTS.get("pattern_related", {})
PATTERN_NOTES_EXTRA = _VERDICT_TEXTS.get("pattern_notes_extra", {})
SHENSHA_POLICY = _VERDICT_TEXTS.get("shensha_policy", {})
ZEJI_VALIDITY_GAP = _VERDICT_TEXTS.get("zeji_validity_gap", {})


def note_text(key: str, **fmt) -> str:
    """取 step5 注记展示句；key 为结构化 id。"""
    entry = STEP5_CLASSICAL_NOTES[key]
    text = entry["text"]
    return text.format(**fmt) if entry.get("template") or fmt else text


def vdesc(key: str) -> str:
    """取 step5 综合定性说明展示句。"""
    return STEP5_VERDICT_DESCS[key]["text"]


def ctext(key: str, **fmt) -> str:
    """取 classical_rules 可交付断语；key 见 data/rules/verdict_texts.json#classical_rules_notes。

    **断语/模板取用的唯一实现**：此前 `classical_rules_{hidden,patterns}` 与
    `effects_{change,harmony,structure}` 五处各写一份完全相同的副本（五份逐字节同 sha256），
    改口径要改五处、漏改一处就出现两种说法——同类缺陷即审计 F2/F3 的副本问题。
    现五处一律 `from chain_verdicts import ctext, ctpl`。
    """
    entry = CLASSICAL_RULES_NOTES[key]
    text = entry["text"]
    return text.format(**fmt) if fmt else text


def ctpl(key: str, *args) -> str:
    """取 classical_rules 拼装句模板；{0}{1}… 为位置参数。"""
    text = CLASSICAL_RULES_TEMPLATES[key]["text"]
    return text.format(*args) if args else text


_QUESTION_SCENARIO_KEYWORDS = {
    "marriage": ["婚", "恋", "感情", "喜欢", "女朋友", "男朋友", "对象", "正缘", "伴侣", "相亲", "姻缘", "爱"],
    "wealth": ["财", "投资", "求财", "赚钱", "收入", "利", "生意", "经营", "破财"],
    "illness": ["病", "健康", "疾", "医", "症", "身体", "患", "康复", "瘤", "炎"],
    "career": ["官", "升", "职", "事业", "工作", "仕", "考功", "升职", "提拔", "领导", "加薪"],
    "exam": ["考", "试", "学业", "成绩", "中", "秀才", "举人", "文", "读书", "高考", "笔试", "面试"],
    "lawsuit": ["讼", "官非", "法律", "诉讼", "被告", "原告", "起诉", "纠纷", "合同", "赔偿", "牢狱"],
    "travel": ["行", "出远门", "出行", "去某地", "旅行", "出差", "搬家", "移", "归", "返程"],
    "parents_illness": ["父病", "母病", "爸", "妈", "父亲", "母亲", "公公", "婆婆", "岳父", "岳母"],
}


# ══════════════════════════════════════════════════════════════════════════════
# ── chain_support 部分 ──
# ══════════════════════════════════════════════════════════════════════════════

# CS_NOTES 已为本文件内 CHAIN_SUPPORT_NOTES，无需跨模块导入。

def get_relation_from_element(element: str, palace_element: str) -> str:
    """根据地支五行确定六亲"""
    if element == palace_element:
        return "兄弟"
    if SHENG_WO.get(palace_element) == element:
        return "父母"
    if SHENG_CYCLE.get(palace_element) == element:
        return "子孙"
    if KE_WO.get(palace_element) == element:
        return "官鬼"
    if KE_CYCLE.get(palace_element) == element:
        return "妻财"
    return "未知"


def get_elements_for_relation(relation: str, palace_element: str) -> list[str]:
    """
    给定六亲类型和宫五行，返回该六亲对应的五行列表。
    注意：一个六亲对应一个五行（除"兄弟"即宫五行本身外）。
    "世爻"不预设五行——调用方须从世爻实际地支推算。
    """
    if relation == "世爻":
        return []  # 世爻五行须从爻支反推，此处留空
    if relation == "兄弟":
        return [palace_element]
    elif relation == "父母":
        return [SHENG_WO.get(palace_element, "")]
    elif relation == "子孙":
        return [SHENG_CYCLE.get(palace_element, "")]
    elif relation == "官鬼":
        return [KE_WO.get(palace_element, "")]
    elif relation == "妻财":
        return [KE_CYCLE.get(palace_element, "")]
    return []


def _branch_element(branch: str) -> str:
    """获取地支五行"""
    return BRANCH_ELEMENTS.get(branch, "未知")


def _stem_element(stem: str) -> str:
    """获取天干五行"""
    return STEM_ELEMENTS.get(stem, "未知")


def _pos_to_name(pos: int) -> str:
    """爻位数字到中文名称"""
    names = {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}
    return names.get(pos, f"第{pos}爻")


def _is_he(b1: str, b2: str) -> bool:
    """判断两地支是否六合"""
    for a, b in HE_PAIRS:
        if (b1 == a and b2 == b) or (b1 == b and b2 == a):
            return True
    return False


def _is_chong(b1: str, b2: str) -> bool:
    """判断两地支是否六冲"""
    for a, b in CHONG_PAIRS:
        if (b1 == a and b2 == b) or (b1 == b and b2 == a):
            return True
    return False


def get_empty_branches(day_stem: str) -> list[str]:
    """获取当日旬空的地支"""
    if day_stem in XUN_KONG:
        return XUN_KONG[day_stem]
    # 如果没有精确匹配，从甲己等推算
    stem_idx = STEMS.index(day_stem) if day_stem in STEMS else 0
    # 根据天干推算旬首
    xun_stems = ["甲子", "甲戌", "甲申", "甲午", "甲辰", "甲寅"]
    xun_idx = stem_idx % 6
    return XUN_KONG.get(xun_stems[xun_idx], [])


def element_strength_in_month(element: str, month_element: str) -> str:
    """
    五行在月建中的旺衰（旺相休囚死）。
    《黄金策》：旺者—临月建也，相者—月建生之也，
    休者—生月建也，囚者—克月建也，死者—月建克之也。
    """
    if element == month_element:
        return "旺"
    if SHENG_CYCLE.get(month_element) == element:
        return "相"
    if SHENG_CYCLE.get(element) == month_element:
        return "休"
    if KE_CYCLE.get(month_element) == element:
        return "死"
    if KE_CYCLE.get(element) == month_element:
        return "囚"
    return "未知"


def _twelve_growth_at_day(element: str, day_branch: str) -> str:
    """
    查询五行元素在日辰的十二长生阶段。

    Args:
        element: 五行（木/火/土/金/水）
        day_branch: 地支（子/丑/.../亥）

    Returns:
        十二长生阶段名称，如 "帝旺"、"临官" 等；未找到返回空字符串。
    """
    elem_table = TWELVE_GROWTH.get(element)
    if not elem_table:
        return ""
    return elem_table.get(day_branch, "")


def _evaluate_fu_cang_strength(fu_detail: dict, month_branch: str, day_branch: str, empty_branches: list = None) -> dict:
    """
    评估伏藏用神的旺衰。

    综合判断伏神的五行旺衰（月建+日辰）、飞伏关系、十二长生，
    得出 0-5 分的强度评分。

    Args:
        fu_detail: step2 中 _check_fu_cang 返回的字典，包含 results 列表
        month_branch: 月建地支
        day_branch: 日辰地支

    Returns:
        {"score": float, "level": str, "analysis": str}
    """
    month_element = _branch_element(month_branch)
    day_element = _branch_element(day_branch)

    results = fu_detail.get("results", [])
    if not results:
        return {"score": 2.5, "level": "中和", "analysis": "伏藏信息不足，默认中和。"}

    # 取第一个伏神结果（通常只有一个）
    entry = results[0]
    fu_shen = entry.get("fu_shen", {})
    fei_shen = entry.get("fei_shen") or {}

    fu_element = fu_shen.get("element", "")
    fu_branch = fu_shen.get("branch", "")
    fu_relation = fu_shen.get("six_relation", "")
    fei_element = fei_shen.get("element", "")
    fei_branch = fei_shen.get("branch", "")
    can_emerge = entry.get("can_emerge", True)

    if not fu_element:
        return {"score": 2.5, "level": "中和", "analysis": "伏神五行不明，默认中和。"}

    analysis_parts = []

    # ── 1. 月建旺衰 ──
    fu_month_strength = element_strength_in_month(fu_element, month_element)
    fu_month_score = strength_to_score(fu_month_strength)

    # ── 2. 日辰旺衰 ──
    fu_day_strength = element_strength_in_month(fu_element, day_element)
    fu_day_score = strength_to_score(fu_day_strength)

    # 基础分（月建为主 0.6，日辰为辅 0.4）
    base_score = fu_month_score * 0.6 + fu_day_score * 0.4

    analysis_parts.append(
        f"伏神五行{fu_element}，月建{month_branch}（{month_element}）→ {fu_month_strength}（{fu_month_score}分），"
        f"日辰{day_branch}（{day_element}）→ {fu_day_strength}（{fu_day_score}分），基础分{base_score:.2f}"
    )

    # ── 3. 十二长生修正 ──
    growth_stage = _twelve_growth_at_day(fu_element, day_branch)
    growth_modifier = _TWELVE_GROWTH_SCORE.get(growth_stage, 0.0)
    if growth_stage:
        if growth_modifier > 0:
            analysis_parts.append(f"伏神临{growth_stage}（日辰十二长生），,+{growth_modifier}")
        elif growth_modifier < 0:
            analysis_parts.append(f"伏神临{growth_stage}（日辰十二长生），{growth_modifier}")
        else:
            analysis_parts.append(f"伏神临{growth_stage}（日辰十二长生），无修正")
    effective_score = base_score + growth_modifier

    # ── 4. 飞伏关系修正 ──
    fu_fei_modifier = 0.0
    fu_fei_reason = ""

    if fei_element:
        # 伏神绝于飞神地支 → 伏神气绝难出（《卜筮正宗》十二长生绝地）；
        # 但日辰冲伏神者为"冲空则实/拔伏"，豁免（ZS003 子冲午得拔）。
        fei_growth = _twelve_growth_at_day(fu_element, fei_branch)
        day_chongs_fu = _is_chong(fu_branch, day_branch)
        if fei_growth == "绝" and not day_chongs_fu:
            fu_fei_modifier = -1.0
            fu_fei_reason = f"伏神{fu_element}绝于飞神{fei_branch}（{fei_growth}），伏神气绝难出，-1.0"
        elif SHENG_CYCLE.get(fei_element) == fu_element:  # 飞生伏
            fu_fei_modifier = 0.5
            fu_fei_reason = f"飞神{fei_element}生伏神{fu_element}（飞生伏），伏得出，+0.5"
        elif KE_CYCLE.get(fei_element) == fu_element:  # 飞克伏
            fu_fei_modifier = -0.8
            fu_fei_reason = f"飞神{fei_element}克伏神{fu_element}（飞克伏），伏难出，-0.8"
        elif fei_element == fu_element:  # 比和
            fu_fei_modifier = 0.3
            fu_fei_reason = f"飞{fu_element}伏{fu_element}比和，+0.3"
        elif SHENG_CYCLE.get(fu_element) == fei_element:  # 伏生飞（泄气）
            fu_fei_modifier = -0.3
            fu_fei_reason = f"伏神{fu_element}生飞神{fei_element}（伏泄气于飞），-0.3"
        elif KE_CYCLE.get(fu_element) == fei_element:
            # 伏克飞为出暴（伏神有力反克飞神，出暴主吉）
            fu_fei_modifier = 0.8
            fu_fei_reason = f"伏神{fu_element}克飞神{fei_element}（伏克飞为出暴），伏有力得出，+0.8"
        else:
            fu_fei_reason = f"伏神{fu_element}与飞神{fei_element}关系无显著生克，无修正"
    else:
        fu_fei_reason = "飞神缺失，无法判断飞伏关系"

    effective_score += fu_fei_modifier

    # ── 4b. 飞神旬空（飞空得出）── 伏神得出有力，且免于泄气之扣
    fei_branch_tmp = fei_branch or ""
    if empty_branches and fei_branch_tmp in empty_branches:
        effective_score += 1.0
        analysis_parts.append(f"飞神{fei_branch_tmp}旬空（飞空得出），伏神得出有力，+1.0")
    if fu_fei_reason:
        analysis_parts.append(fu_fei_reason)

    # ── 5. 能否得出 ──
    if not can_emerge:
        effective_score -= 0.5
        analysis_parts.append("伏神受压制难以得出，-0.5")

    # ── 伏藏压制修正 ──────────────────────────────────────────────────
    # 古籍:《增删卜易·用神伏藏章》"用神伏藏，纵月建日辰旺相，只论七成，
    #         盖为飞神所压，隐而不显，其力不能全伸"；
    #       《卜筮正宗·飞神伏神论》"伏神者，谓卦中之六亲不全，须借伏神，
    #         伏者，隐而不出，纵旺相必减二等"；
    #       《黄金策·千金赋》"伏神得日辰生旺，亦需乘时而出"——得出得时
    #         仅论得出与否，旺相仍需压制。
    # 语义: 伏藏用神不论飞伏生克关系，月日旺衰俱以「中和」为上限；
    #       「伏克飞为出暴」(fu_fei_modifier=+0.8) 仍属伏藏，不得直断旺相；
    #       压制上限 3.4 恰落于「中和」上界(2.5–3.5), 合古籍「减二等」之义。
    effective_score = min(effective_score, 3.4)
    analysis_parts.append("伏藏隐而不显，力不能全伸，压制至多为中和(≤3.4)")

    # 上下限
    effective_score = max(0.5, min(5.0, effective_score))

    # ── 旺衰定性 ──
    if effective_score >= 4.5:
        strength_level = "极旺"
    elif effective_score >= 3.5:
        strength_level = "旺"
    elif effective_score >= 2.5:
        strength_level = "中和"
    elif effective_score >= 1.5:
        strength_level = "偏弱"
    elif effective_score >= 0.8:
        strength_level = "弱"
    else:
        strength_level = "极弱"

    # 构建分析文本
    fei_desc = f"飞神{fei_branch}（{fei_element}）" if fei_branch else "飞神不明"
    fu_desc = f"{fu_relation}伏于{fu_branch}（{fu_element}）"
    analysis = f"用神伏藏（{fu_desc}），{fei_desc}。{'；'.join(analysis_parts)}。综合评分：{effective_score:.2f}（{strength_level}）。"

    return {
        "score": round(effective_score, 2),
        "level": strength_level,
        "analysis": analysis,
    }


def strength_to_score(strength: str) -> int:
    """旺相休囚死到数字分值"""
    return {"旺": 5, "相": 4, "休": 3, "囚": 2, "死": 1, "未知": 0}.get(strength, 0)


def get_twelve_growth_stage(element: str, day_branch: str) -> tuple:
    """
    获取某五行元素在指定日支的十二长生阶段。
    返回 (stage_name, index) 或 None
    """
    table = TWELVE_GROWTH_TABLES.get(element)
    if table is None:
        return None
    try:
        idx = table.index(day_branch)
        return TWELVE_GROWTH_STAGES[idx], idx
    except ValueError:
        return None


def get_changed_hexagram_branch(changed_hex_name: str, position: int) -> str | None:
    """
    获取变卦中指定位置(1-6)的地支。
    position: 1=初爻(bottom), ..., 6=上爻(top)
    """
    if changed_hex_name is None:
        return None
    trigrams = HEXAGRAM_TRIGRAMS.get(changed_hex_name)
    if trigrams is None:
        return None
    upper_name, lower_name = trigrams
    if position <= 3:
        return NAJIA_BRANCHES[lower_name]["inner"][position - 1]
    else:
        return NAJIA_BRANCHES[upper_name]["outer"][position - 4]


def get_palace_first_hexagram(palace_name: str) -> str:
    """获取八宫首卦名称。兼容 "艮" 与 "艮宫" 两种写法（内核表以裸宫名为键）。"""
    palace_data = EIGHT_PALACES.get(palace_of_key(palace_name))
    if palace_data:
        return palace_data["order"][0][0]
    return ""


def safe_get(result: dict, *keys, default=None):
    """安全地从嵌套字典中获取值"""
    current = result
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current
