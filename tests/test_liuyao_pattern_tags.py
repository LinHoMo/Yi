# -*- coding: utf-8 -*-
"""六爻格局标签：由「格局词子串匹配」改为「读 advanced_analysis 结构」的回归断言。

背景（`docs/DEEP-DIVE-PLAN.md` §1.2）：反吟/伏吟、进退神、暗动、月破、三合/三刑此前被
降级为**文本子串匹配**——把 `step5` 全部标量拼成字符串再取词，古籍引文里出现「三合」
就会给任何一卦贴上「三合」标签（假阳）。判据唯一真值源是 `advanced_analysis`
（`hidden_movement` / `monthly_break` / `triple_combo` / `three_punishments` / `repetition`），
narrate 只做结构读取，见 `liuyao_narrate._collect_pattern_tags`。

本测试用真实案例锁定三条结构口径，防止子串扫描被重新引入。
"""
from __future__ import annotations

import pytest

import case_runner

# 案例来自多个文件（classical / wikisource / 火珠林…），合并入口唯一：load_cases()
_BY_ID = {c["id"]: c for c in case_runner.load_cases()}


def _tags(cid: str) -> set[str]:
    """取该例推理链里的 `[格局要点]` 裸标签集合（唯一注入点见 narrate）。"""
    r = case_runner.run_case(_BY_ID[cid])
    for ln in r.get("pattern_tags") or []:
        if ln.startswith("[格局要点] "):
            return set(ln[len("[格局要点] "):].split("、"))
    return set()


@pytest.mark.parametrize("cid", ["SG002", "WS017", "WSD024", "WSD033"])
def test_quoted_text_no_longer_fabricates_sanhe(cid):
    """旧实现扫 step5 文本，引文里的「三合」会让这些卦凭空多出三合标签；现须无。"""
    assert "三合" not in _tags(cid)


def test_sanxing_only_when_punishment_complete():
    """三刑只认成刑；「待刑」（缺月日补齐）不计——HO001 寅申待刑不得记三刑。"""
    assert "三刑" not in _tags("HO001")
    assert "三刑" in _tags("HO003")


def test_sanhe_from_structural_triple_combo():
    """三合局须来自结构（卦中三支成局），而非文本巧合：HO003 成局 → 有标签。"""
    assert "三合" in _tags("HO003")
