# -*- coding: utf-8 -*-
"""旬空 / 三刑 / 十二长生 / 六合六冲 双向性。"""
from __future__ import annotations

from yishu_core.symbols import (
    CHONG_PAIRS,
    HE_PAIRS,
    sanxing_hits,
    twelve_growth,
    twelve_growth_index,
    xunkong_of,
)


class TestXunkong:
    def test_jiazi_is_xuhai(self):
        assert xunkong_of("甲子") == ["戌", "亥"]

    def test_same_xun_shares_kong(self):
        # 甲子旬内：乙丑…癸酉 皆空戌亥
        for gz in ("乙丑", "丙寅", "丁卯", "戊辰", "己巳",
                   "庚午", "辛未", "壬申", "癸酉"):
            assert xunkong_of(gz) == ["戌", "亥"], gz

    def test_jiaxu_is_shenyou(self):
        assert xunkong_of("甲戌") == ["申", "酉"]

    def test_other_xun_heads(self):
        assert xunkong_of("甲申") == ["午", "未"]
        assert xunkong_of("甲午") == ["辰", "巳"]
        assert xunkong_of("甲辰") == ["寅", "卯"]
        assert xunkong_of("甲寅") == ["子", "丑"]

    def test_invalid_returns_empty(self):
        assert xunkong_of("") == []
        assert xunkong_of("甲") == []
        assert xunkong_of("甲子辰") == []
        assert xunkong_of("XY") == []


class TestSanxing:
    def test_wuli_zimao(self):
        assert "无礼之刑" in sanxing_hits(["子", "卯"])
        assert "无礼之刑" in sanxing_hits(["卯", "子", "午"])

    def test_wuen_yin_sishen(self):
        assert "无恩之刑" in sanxing_hits(["寅", "巳", "申"])
        assert "无恩之刑" in sanxing_hits(["申", "寅", "巳"])

    def test_shishi_chouxuwei(self):
        assert "恃势之刑" in sanxing_hits(["丑", "戌", "未"])

    def test_zixing(self):
        assert "自刑" in sanxing_hits(["辰", "辰"])
        assert "自刑" in sanxing_hits(["午", "午"])
        assert "自刑" in sanxing_hits(["酉", "酉", "子"])

    def test_no_false_positive(self):
        assert sanxing_hits(["子", "午"]) == []  # 六冲不是刑
        assert sanxing_hits(["子", "丑"]) == []
        assert sanxing_hits([]) == []
        assert sanxing_hits(["子", "X"]) == []


class TestTwelveGrowth:
    def test_mu_changsheng_at_hai(self):
        assert twelve_growth("木", "亥") == "长生"
        assert twelve_growth_index("木", "亥") == 0

    def test_huo_diwang_at_wu(self):
        assert twelve_growth("火", "午") == "帝旺"
        assert twelve_growth_index("火", "午") == 4

    def test_huo_tu_same_palace(self):
        # 火土同宫：土长生亦在寅
        assert twelve_growth("土", "寅") == "长生"
        assert twelve_growth("土", "午") == "帝旺"

    def test_shui_mu_at_chen(self):
        assert twelve_growth("水", "辰") == "墓"
        assert twelve_growth_index("水", "辰") == 8

    def test_invalid_returns_none(self):
        assert twelve_growth("木", "X") is None
        assert twelve_growth("X", "亥") is None
        assert twelve_growth_index("木", "X") is None


def _undirected_partner(pairs, branch: str):
    """把双向表当无向图查伙伴；无则 None。"""
    for a, b in pairs:
        if a == branch:
            return b
        if b == branch:
            return a
    return None


class TestHeChongBidirectional:
    def test_he_is_symmetric(self):
        for a, b in HE_PAIRS:
            assert _undirected_partner(HE_PAIRS, a) == b
            assert _undirected_partner(HE_PAIRS, b) == a

    def test_chong_is_symmetric(self):
        for a, b in CHONG_PAIRS:
            assert _undirected_partner(CHONG_PAIRS, a) == b
            assert _undirected_partner(CHONG_PAIRS, b) == a

    def test_he_known_pairs(self):
        he = {frozenset(p) for p in HE_PAIRS}
        assert frozenset(("子", "丑")) in he
        assert frozenset(("寅", "亥")) in he
        assert frozenset(("午", "未")) in he
        assert len(he) == 6

    def test_chong_known_pairs(self):
        chong = {frozenset(p) for p in CHONG_PAIRS}
        assert frozenset(("子", "午")) in chong
        assert frozenset(("卯", "酉")) in chong
        assert frozenset(("巳", "亥")) in chong
        assert len(chong) == 6

    def test_he_and_chong_partition_branches(self):
        # 六合、六冲各自都是十二支的完美匹配
        he_branches = [b for p in HE_PAIRS for b in p]
        chong_branches = [b for p in CHONG_PAIRS for b in p]
        assert sorted(he_branches) == sorted(chong_branches)
        assert len(set(he_branches)) == 12
        assert len(set(chong_branches)) == 12
