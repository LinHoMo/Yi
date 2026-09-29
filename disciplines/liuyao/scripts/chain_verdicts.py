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

