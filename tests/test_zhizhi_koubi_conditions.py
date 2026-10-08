# -*- coding: utf-8 -*-
"""OPT-liuren_zhizhi_yuding_dz-02 单测：闭口课四条件并存取并集。

验证 disciplines/liuren/data/kemu.json#entries["闭口"].conditions：
- 含 1 条 main（《大全》主条件）+ 3 条 variant（《直指御定》L76/L709/L2380）
- 每条 citation 为书源逐字子串
- 《大全》主条件未被替换
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/sources/liuren_zhizhi_yuding_dz.dz.txt"


def _load() -> list[dict]:
    kemu = json.loads(
        (ROOT / "disciplines/liuren/data/kemu.json").read_text(encoding="utf-8"))
    return [e for e in kemu["entries"] if e["name"] == "闭口"][0]["conditions"]


def _source_text() -> str:
    return SRC.read_text(encoding="utf-8")


def test_four_conditions_coexist():
    """四条件并存取并集：1 main + 3 variant。"""
    conds = _load()
    assert len(conds) == 4, f"应为 4 条，实得 {len(conds)}: {[c['basis'] for c in conds]}"
    assert conds[0]["type"] == "main"
    variants = [c for c in conds if c["type"] == "variant"]
    assert len(variants) == 3, f"variant 应为 3 条，实得 {len(variants)}"


def test_main_condition_untouched():
    """《大全》主条件未被替换。"""
    conds = _load()
    main = conds[0]
    assert main["type"] == "main"
    assert "旬尾" in main["basis"] and "旬首" in main["basis"]
    assert "大全" in main["citation"]


def test_variant_L76_citation_verbatim():
    """《直指御定》L76 元武乘神临于旬首：citation 为书源逐字子串。"""
    src = _source_text()
    conds = _load()
    hit = next(c for c in conds if "L76" in c["citation"])
    # 从 citation 中抽书源逐字段（冒号后）
    quote = hit["citation"].split("：", 1)[1]
    assert quote.strip("。") in src or quote in src, (
        f"L76 citation 不是书源子串: {quote!r}")


def test_variant_L709_citation_verbatim():
    """《直指御定》L709 地盘旬首上神乘元武：citation 为书源逐字子串。"""
    src = _source_text()
    conds = _load()
    hit = next(c for c in conds if "L709" in c["citation"])
    quote = hit["citation"].split("：", 1)[1]
    assert quote.strip("。") in src or quote in src, (
        f"L709 citation 不是书源子串: {quote!r}")


def test_variant_L2380_citation_verbatim():
    """《直指御定》L2380 巳乃旬尾，遁癸为闭口：citation 为书源逐字子串。"""
    src = _source_text()
    conds = _load()
    hit = next(c for c in conds if "L2380" in c["citation"])
    quote = hit["citation"].split("：", 1)[1]
    assert quote in src, f"L2380 citation 不是书源子串: {quote!r}"


def test_each_condition_has_required_fields():
    """每条条件必含 type/basis/citation/note 四字段。"""
    conds = _load()
    for i, c in enumerate(conds):
        for field in ("type", "basis", "citation", "note"):
            assert field in c and c[field], (
                f"conditions[{i}] 缺字段 {field} 或为空")
