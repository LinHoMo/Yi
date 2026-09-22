# -*- coding: utf-8 -*-
"""纳甲查表：由卦名与爻位取该爻地支。

放内核的理由：变卦某爻化出什么支，是"装卦"这一步的事实，不是某一层的私有知识。
此前只有 `classical_analysis.get_changed_hexagram_branch()` 有这份逻辑，
而引擎输出的爻数据里没有 `changed_branch` 字段——于是思维链里读
`yao.get("changed_earthly_branch")` 的应期法则（动而化回头生、化出之支值日）
永远取到空，规则写了却从不触发。现在三处共用这一个实现。

position：1=初爻（最下），6=上爻（最上）。
"""
from __future__ import annotations

from .symbols import HEXAGRAM_TRIGRAMS, NAJIA_BRANCHES


def najia_branch(hex_name: str, position: int) -> str | None:
    """卦 `hex_name` 第 `position` 爻的纳甲地支；卦名或爻位不合法时返回 None。"""
    if not hex_name or not position or not (1 <= position <= 6):
        return None
    trigrams = HEXAGRAM_TRIGRAMS.get(hex_name)
    if not trigrams:
        return None
    upper_name, lower_name = trigrams
    if position <= 3:
        return NAJIA_BRANCHES[lower_name]["inner"][position - 1]
    return NAJIA_BRANCHES[upper_name]["outer"][position - 4]
