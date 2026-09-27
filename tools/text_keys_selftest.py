# -*- coding: utf-8 -*-
"""断语库键一致性：代码引用的 JSON 键必须存在（防外置漏键）。"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

LIUYAO = ROOT / "disciplines" / "liuyao"
VT = LIUYAO / "data" / "rules" / "verdict_texts.json"
NT = LIUYAO / "data" / "narrative_templates.json"
AR = LIUYAO / "data" / "rules" / "advice_rules.json"


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def check_text_keys() -> list[str]:
    fails: list[str] = []
    vt, nt, ar = _load(VT), _load(NT), _load(AR)

    # collected top-level sections that code indexes
    sections = {
        "verdict_texts": set(vt.keys()),
        "narrative_templates": set(nt.keys()),
        "advice_rules": set(ar.keys()),
    }

    # scan liuyao scripts for _VERDICT_TEXTS["x"] / _NARRATIVE_TPL["x"] / _DATA["x"]
    patterns = [
        (re.compile(r'_VERDICT_TEXTS(?:\.get)?\[[\'"]([^\'"]+)[\'"]\]'), "verdict_texts"),
        (re.compile(r'_NARRATIVE_TPL(?:\.get)?\[[\'"]([^\'"]+)[\'"]\]'), "narrative_templates"),
        (re.compile(r'_DATA(?:\.get)?\[[\'"]([^\'"]+)[\'"]\]'), "advice_rules"),
    ]
    # also chain_verdicts named exports used as PATTERN_VERDICTS["k"]
    named = {
        "PATTERN_VERDICTS": ("verdict_texts", "pattern_verdicts"),
        "EFFECT_LABELS": ("verdict_texts", "effect_labels"),
        "EFFECT_PHRASES": ("verdict_texts", "effect_phrases"),
        "BING_YAO_LABELS": ("verdict_texts", "bing_yao_labels"),
        "NARRATIVE_HINTS": ("verdict_texts", "narrative_hints"),
        "PATTERN_RELATED": ("verdict_texts", "pattern_related"),
        "PATTERN_NOTES_EXTRA": ("verdict_texts", "pattern_notes_extra"),
        "SHENSHA_POLICY": ("verdict_texts", "shensha_policy"),
        "ZEJI_VALIDITY_GAP": ("verdict_texts", "zeji_validity_gap"),
    }

    for py in (LIUYAO / "scripts").glob("*.py"):
        text = py.read_text(encoding="utf-8")
        for pat, src in patterns:
            for key in pat.findall(text):
                if key not in sections[src]:
                    fails.append(f"{py.name}: {src}[{key}] 缺失")
        for name, (src, section) in named.items():
            if name not in text:
                continue
            for m in re.finditer(re.escape(name) + r'(?:\.get)?\[[\'"]([^\'"]+)[\'"]\]', text):
                key = m.group(1)
                blob = vt.get(section) if src == "verdict_texts" else {}
                if isinstance(blob, dict) and key not in blob:
                    fails.append(f"{py.name}: {name}[{key}] 缺失于 {section}")

    # advice categories referenced as fallback keys
    if "事业" not in (ar.get("advice_rules") or {}):
        fails.append("advice_rules 缺兜底类目「事业」")

    # narrative nested key spot-check
    for section, key in [
        ("strength_phrases", "month_break"),
        ("change_sentences", "no_moving"),
        ("special_sentences", "void_but_rooted"),
        ("verdict_openings", "pos_table"),
        ("pattern_hints", "六冲卦"),
        ("yingqi_descriptions", "value_day"),
    ]:
        blob = nt.get(section)
        if not isinstance(blob, dict) or key not in blob:
            fails.append(f"narrative_templates.{section}.{key} 缺失")

    return fails


if __name__ == "__main__":
    fails = check_text_keys()
    if fails:
        print("断语库键一致性失败：")
        for f in fails:
            print("  ·", f)
        raise SystemExit(1)
    print("断语库键一致性通过（verdict_texts / narrative_templates / advice_rules）")
