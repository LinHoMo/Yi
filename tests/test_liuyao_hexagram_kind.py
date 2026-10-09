# -*- coding: utf-8 -*-
"""六爻卦体六合/六冲：结构判据唯一真值源 + 报告层不得自相矛盾。

背景（2026-10-01u）：`liuyao_step4._detect_hexagram_harmony_clash_pattern` 曾并列一份
手写卦名白名单，与同一次 analyze 的 `advanced_analysis.clash_harmony.hexagram_type`
（由 core `hexagram_he_chong_kind` 按对应位 (1,4)(2,5)(3,6) 三对地支算出）直接冲突：
白名单把 `晋`/`遁`/`夬`/`姤`/`解`/`归妹`/`旅`/`涣`/`小过`/`萃` 误收为六冲、把
`离`(八纯六冲) 误收为六合，且 `涣`/`离`/`萃` 同时出现在两张名单里。用户可见后果是
报告写「六冲卦主散，晋卦世应相冲」而同一份分析的结构层写「无明确合冲」——
`tools/report_faithfulness.py --corpus` 把它判为 contradicted。

本测试锁两件事：
  ① core 的结构判据本身符合通行口径（八纯 + 无妄 + 大壮 = 六冲；否/泰/贲/困/旅/豫/复/节 = 六合）；
  ② 报告层格局判定的「六冲/六合」类命中，只可能发生在 core 认作六冲/六合的卦上。
"""
from __future__ import annotations

import pytest

from yishu_core.symbols import (
    HEXAGRAM_KIND_LIUCHONG,
    HEXAGRAM_KIND_LIUHE,
    HEXAGRAM_TRIGRAMS,
    hexagram_he_chong_kind,
)

from liuyao_step4 import _detect_hexagram_harmony_clash_pattern

EXPECT_CHONG = {"乾", "兑", "坎", "坤", "巽", "离", "艮", "震", "无妄", "大壮"}
EXPECT_HE = {"否", "泰", "贲", "困", "旅", "豫", "复", "节"}

CHONG_PATTERNS = {"六冲主散", "冲中逢合可解"}
HE_PATTERNS = {"合处逢冲则散", "合处逢生"}


def test_core_he_chong_kind_matches_tonghang():
    got_chong = {n for n in HEXAGRAM_TRIGRAMS if hexagram_he_chong_kind(n) == HEXAGRAM_KIND_LIUCHONG}
    got_he = {n for n in HEXAGRAM_TRIGRAMS if hexagram_he_chong_kind(n) == HEXAGRAM_KIND_LIUHE}
    assert got_chong == EXPECT_CHONG, f"六冲卦集合漂移：{sorted(got_chong)}"
    assert got_he == EXPECT_HE, f"六合卦集合漂移：{sorted(got_he)}"


@pytest.mark.parametrize("name", sorted(HEXAGRAM_TRIGRAMS))
def test_harmony_clash_pattern_never_contradicts_structure(name):
    kind = hexagram_he_chong_kind(name)
    hex_result = {
        "original_hexagram": {"name": name},
        "advanced_analysis": {"hexagram_type": kind},
        "empty_branches": [],
    }
    res = _detect_hexagram_harmony_clash_pattern("占求财", hex_result, {})
    pattern = res.get("pattern")
    if kind != HEXAGRAM_KIND_LIUCHONG:
        assert pattern not in CHONG_PATTERNS, \
            f"{name}（结构层判 {kind}）不得出六冲类格局 {pattern}"
    if kind != HEXAGRAM_KIND_LIUHE:
        assert pattern not in HE_PATTERNS, \
            f"{name}（结构层判 {kind}）不得出六合类格局 {pattern}"
