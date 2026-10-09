# -*- coding: utf-8 -*-
"""十神 / 六亲 / 五行生克一致性（同一张关系表的两侧）。"""
from __future__ import annotations

from yishu_core.relations import (
    element_of,
    liuqin_to_shishen,
    shishen_to_liuqin,
    six_relation,
    ten_god,
    wuxing_relation,
)

STEMS = "甲乙丙丁戊己庚辛壬癸"
LIUQIN = ("父母", "兄弟", "子孙", "妻财", "官鬼")
SHISHEN = (
    "比肩", "劫财", "食神", "伤官", "偏财",
    "正财", "七杀", "正官", "偏印", "正印",
)


class TestWuxingRelation:
    def test_five_relations_from_wood(self):
        assert wuxing_relation("木", "木") == "同我"
        assert wuxing_relation("木", "水") == "生我"
        assert wuxing_relation("木", "火") == "我生"
        assert wuxing_relation("木", "金") == "克我"
        assert wuxing_relation("木", "土") == "我克"

    def test_cycle_consistency(self):
        # 生克闭环：木生火、火生土…
        assert wuxing_relation("火", "土") == "我生"
        assert wuxing_relation("土", "金") == "我生"
        assert wuxing_relation("金", "水") == "我生"
        assert wuxing_relation("水", "木") == "我生"

    def test_invalid_returns_none(self):
        assert wuxing_relation("木", "X") is None
        assert wuxing_relation("", "木") is None
        assert wuxing_relation("木", "") is None


class TestTenGod:
    def test_jia_day_all_ten_gods(self):
        expected = {
            "甲": "比肩", "乙": "劫财",
            "丙": "食神", "丁": "伤官",
            "戊": "偏财", "己": "正财",
            "庚": "七杀", "辛": "正官",
            "壬": "偏印", "癸": "正印",
        }
        for other, god in expected.items():
            assert ten_god("甲", other) == god, f"甲见{other}"

    def test_bing_day_officer_and_seven_kill(self):
        assert ten_god("丙", "壬") == "七杀"
        assert ten_god("丙", "癸") == "正官"

    def test_same_stem_is_bi_jian(self):
        for s in STEMS:
            assert ten_god(s, s) == "比肩"

    def test_invalid_returns_none(self):
        assert ten_god("甲", "子") is None
        assert ten_god("X", "甲") is None


class TestSixRelation:
    def test_five_liuqin(self):
        assert six_relation("木", "水") == "父母"
        assert six_relation("木", "木") == "兄弟"
        assert six_relation("木", "火") == "子孙"
        assert six_relation("木", "土") == "妻财"
        assert six_relation("木", "金") == "官鬼"

    def test_invalid_returns_none(self):
        assert six_relation("木", "X") is None
        assert six_relation("", "木") is None


class TestConsistency:
    def test_ten_god_collapses_to_six_relation(self):
        """十神去阴阳后必须等于同五行的六亲（合参对齐前提）。"""
        for day in STEMS:
            for other in STEMS:
                god = ten_god(day, other)
                liuqin = six_relation(element_of(day), element_of(other))
                assert god is not None and liuqin is not None
                assert shishen_to_liuqin(god) == liuqin, f"{day}见{other}"

    def test_shishen_to_liuqin_covers_all(self):
        for god in SHISHEN:
            assert shishen_to_liuqin(god) in LIUQIN
        assert shishen_to_liuqin("不存在") is None

    def test_liuqin_to_shishen_roundtrip(self):
        for liuqin in LIUQIN:
            pair = liuqin_to_shishen(liuqin)
            assert pair is not None
            same, diff = pair
            assert shishen_to_liuqin(same) == liuqin
            assert shishen_to_liuqin(diff) == liuqin
        assert liuqin_to_shishen("不存在") is None

    def test_each_liuqin_has_two_shishen(self):
        for liuqin in LIUQIN:
            same, diff = liuqin_to_shishen(liuqin)
            assert same != diff
            assert same in SHISHEN and diff in SHISHEN
