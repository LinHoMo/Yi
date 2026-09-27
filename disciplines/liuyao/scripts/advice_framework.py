# -*- coding: utf-8 -*-
"""
趋避建议 — 从一开始就说人话，分类按问题关键词，不靠默认「事业」。

断语文案在 data/rules/advice_rules.json，此处只加载与组装（AGENTS.md §三）。
"""
from __future__ import annotations

import json
from pathlib import Path

_RULES_PATH = Path(__file__).resolve().parents[1] / "data" / "rules" / "advice_rules.json"


def _load() -> dict:
    try:
        return json.loads(_RULES_PATH.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"缺建议库 {_RULES_PATH}：{exc}") from exc


_DATA = _load()
ADVICE_RULES = _DATA["advice_rules"]
_CATEGORY_KEYWORDS = _DATA["category_keywords"]
_TIMING_EXTRA = _DATA.get("timing_extra") or {}


def match_advice_category(question: str, fallback: str = "事业") -> str:
    q = str(question or "")
    if not q.strip():
        return fallback
    best_key = None
    best_len = 0
    for key, kws in _CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in q and len(kw) > best_len:
                best_key = key
                best_len = len(kw)
    if best_key:
        return best_key
    for key in ADVICE_RULES:
        if key in q:
            return key
    if "财" in q:
        return "投资"
    if "婚" in q:
        return "婚姻"
    return fallback


def _bucket_of(verdict: str) -> str:
    v = str(verdict or "")
    if "凶" in v or "跌" in v:
        return "inauspicious"
    if "吉" in v and "凶" not in v:
        return "auspicious"
    return "neutral"


def generate_advice(verdict: str, category: str, result: dict) -> list:
    """按问题类型与断语，返回 3–4 条已经说人话的建议。"""
    bucket = _bucket_of(verdict)
    matched = match_advice_category(category)
    advice_list = list(ADVICE_RULES.get(matched, {}).get(bucket) or ADVICE_RULES["事业"][bucket])

    tc = result.get("thinking_chain", {}) if isinstance(result, dict) else {}
    s5 = tc.get("step5_synthesis", {}) if isinstance(tc, dict) else {}
    timing = s5.get("timing") or {}
    keys = []
    if isinstance(timing, dict):
        keys = timing.get("key_branches") or []
        plain = timing.get("plain_text") or timing.get("summary_text") or ""
    else:
        plain = ""
    if keys:
        tpl = _TIMING_EXTRA.get("keys") or "时机上可多留意 {keys} 这几日"
        advice_list = advice_list + [tpl.format(keys="、".join(keys[:4]))]
    elif plain:
        short = str(plain)
        if len(short) > 40:
            short = short[:40] + "…"
        advice_list = advice_list + [short]

    return advice_list[:4]
