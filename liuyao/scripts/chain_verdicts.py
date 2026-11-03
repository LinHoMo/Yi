# -*- coding: utf-8 -*-
"""断语/引文库装载器（chain_verdicts）——data/verdicts.json 与 data/rules/verdict_texts.json 的唯一取用面。

第一百六十七批起 narrative_rules 的 docstring 就写着「依赖单向：narrative_rules →
chain_verdicts」、narrative_utils 也留有「chain_verdicts 部分」节名——但实现一直落在
narrative_utils，名实分离。第三百一十一批分层大清账把名实对齐：断语装载与格式化取用
归本模块；通用机械工具归 util.py；narrative_utils / narrative_rules 两模块撤编
（CONTRACT §六-6 还账）。

铁律一：本模块只装载数据与格式化取用，不含机械推演、不产结构结论；analyze（规则层
取断语表）与 narrate（正文装配）都从这里取——它是数据面，不是叙述面。
"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

import json

from pathlib import Path


# ── chain_verdicts 部分 ──
# ══════════════════════════════════════════════════════════════════════════════

# ── 断语/引文库：外置 data/verdicts.json 与 data/rules/verdict_texts.json（SKILL.md），代码只留算法与加载 ──
_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_VERDICTS_PATH = _DATA_DIR / "verdicts.json"
_VERDICT_TEXTS_PATH = _DATA_DIR / "rules" / "domain" / "verdict_texts.json"


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
# step3 旺衰口语结论（level → 断语）；结构见 data/rules/verdict_texts.json#strength_summary_say
STRENGTH_SUMMARY_SAY = _VERDICT_TEXTS.get("strength_summary_say", {})
SHENSHA_POLICY = _VERDICT_TEXTS.get("shensha_policy", {})
# 格局标签句（真空/假空…）：键 = 格局组名 → 标签名 → {label, strength_text, reason, verdict, basis}
PATTERN_VERDICT_LABELS = _VERDICT_TEXTS.get("pattern_verdict_labels", {})
VOID_KIND_LABELS = {
    "true": PATTERN_VERDICT_LABELS.get("真空/假空", {}).get("真空", {}),
    "false": PATTERN_VERDICT_LABELS.get("真空/假空", {}).get("假空", {}),
}
DUFA_QUOTE = PATTERN_VERDICT_LABELS.get("独发/独静", {}).get("古典引文", "")
DUFA_NOTES = {
    "du_fa": PATTERN_VERDICT_LABELS.get("独发/独静", {}).get("du_fa", ""),
    "du_jing": PATTERN_VERDICT_LABELS.get("独发/独静", {}).get("du_jing", ""),
}
SANCHUAN_LABELS = PATTERN_VERDICT_LABELS.get("三传克制", {})
# 【第一百六十七批】乱动卦（《火珠林》源L33）：只标结构象，取用口径第一百七十批裁定不另立。
LUANDONG_LABELS = PATTERN_VERDICT_LABELS.get("乱动", {})


def pattern_label(group: str, name: str) -> dict:
    """取格局标签句；缺库时返回空 dict（调用方按"无断语"处理，不硬编一份）。"""
    return (PATTERN_VERDICT_LABELS.get(group) or {}).get(name) or {}


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


# ── 叙述判定组装（原 narrative_rules 整体并入，见 CONTRACT §六-6）──


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
    return STEP5_FACTOR_REASONS.get(key or "base_neutral", STEP5_FACTOR_REASONS["base_neutral"])["text"]


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
