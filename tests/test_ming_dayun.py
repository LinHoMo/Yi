# -*- coding: utf-8 -*-
"""大运顺逆、起运岁（节距折算）、流年十神。"""
from __future__ import annotations

from datetime import datetime

from yishu_core.ganzhi_calendar import next_jie_after, prev_jie_before
from yishu_core.ming_tables import DAYS_PER_LUCK_YEAR, dayun_direction
from yishu_core.relations import ten_god

import pattern

BIRTH_DT = datetime(1984, 2, 10, 10, 0)


def _chart(gender: str = "male") -> dict:
    """甲子年 丙寅月 甲午日 己巳时。"""
    return {
        "birth": {"gender": gender, "datetime": "1984-02-10 10:00"},
        "pillars": {
            "year": {"stem": "甲", "branch": "子", "ganzhi": "甲子"},
            "month": {"stem": "丙", "branch": "寅", "ganzhi": "丙寅"},
            "day": {"stem": "甲", "branch": "午", "ganzhi": "甲午"},
            "hour": {"stem": "己", "branch": "巳", "ganzhi": "己巳"},
        },
    }


def _start_age_from_jie(jie: dict) -> float:
    days = abs((jie["instant"] - BIRTH_DT).total_seconds()) / 86400.0
    return round(days / float(DAYS_PER_LUCK_YEAR), 1)


class TestDayunDirection:
    def test_jia_male_forward(self):
        assert dayun_direction("甲", "male") == "forward"
        assert dayun_direction("甲", "男") == "forward"

    def test_jia_female_backward(self):
        assert dayun_direction("甲", "female") == "backward"
        assert dayun_direction("甲", "女") == "backward"

    def test_yin_year_reversed(self):
        assert dayun_direction("乙", "male") == "backward"
        assert dayun_direction("乙", "female") == "forward"

    def test_invalid_input(self):
        assert dayun_direction("甲", "x") is None
        assert dayun_direction("X", "male") is None
        assert dayun_direction("", "male") is None

    def test_days_per_luck_year_constant(self):
        assert DAYS_PER_LUCK_YEAR == 3


class TestDayunTable:
    def test_eight_steps_forward_order(self):
        rows = pattern.dayun_table(_chart("male"))
        assert len(rows) == 8
        assert rows[0]["index"] == 1
        # 丙寅月顺排：丁卯、戊辰、己巳…
        assert [r["ganzhi"] for r in rows[:3]] == ["丁卯", "戊辰", "己巳"]
        assert rows[0]["start_age"] < rows[1]["start_age"]

    def test_backward_order_for_female(self):
        rows = pattern.dayun_table(_chart("female"))
        assert [r["ganzhi"] for r in rows[:3]] == ["乙丑", "甲子", "癸亥"]

    def test_start_age_forward_uses_next_jie(self):
        rows = pattern.dayun_table(_chart("male"))
        expected = _start_age_from_jie(next_jie_after(BIRTH_DT))
        assert rows[0]["start_age"] == expected
        # 不是按上一节折算
        assert rows[0]["start_age"] != _start_age_from_jie(prev_jie_before(BIRTH_DT))

    def test_start_age_backward_uses_prev_jie(self):
        rows = pattern.dayun_table(_chart("female"))
        expected = _start_age_from_jie(prev_jie_before(BIRTH_DT))
        assert rows[0]["start_age"] == expected
        assert rows[0]["start_age"] != _start_age_from_jie(next_jie_after(BIRTH_DT))

    def test_ten_god_from_luck_stem(self):
        day_stem = "甲"
        for row in pattern.dayun_table(_chart("male")):
            luck_stem = row["ganzhi"][0]
            assert row["ten_god"] == ten_god(day_stem, luck_stem)

    def test_empty_without_gender(self):
        chart = _chart()
        chart["birth"] = {"gender": "", "datetime": "1984-02-10 10:00"}
        assert pattern.dayun_table(chart) == []


class TestLiunianTable:
    def test_years_and_ganzhi_from_birth(self):
        rows = pattern.liunian_table(_chart(), n=5)
        assert len(rows) == 5
        assert rows[0]["year"] == 1984
        assert rows[0]["ganzhi"] == "甲子"
        assert rows[1]["ganzhi"] == "乙丑"
        assert rows[0]["age"] == 0

    def test_ten_god_from_year_stem(self):
        day_stem = "甲"
        rows = pattern.liunian_table(_chart(), n=8)
        for row in rows:
            year_stem = row["ganzhi"][0]
            assert row["ten_god"] == ten_god(day_stem, year_stem)
        assert rows[0]["ten_god"] == "比肩"  # 甲年对甲日主
        assert rows[1]["ten_god"] == "劫财"  # 乙年

    def test_empty_without_year_pillar(self):
        chart = _chart()
        chart["pillars"]["year"] = {}
        assert pattern.liunian_table(chart) == []


def test_dayun_liunian_interactions_six_samples():
    """6 样例机械交互：有输出、无吉凶字段、关系带 basis。"""
    import sys
    from pathlib import Path as _P
    root = _P(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "disciplines" / "ming" / "scripts"))
    from chart import chart
    from analyze import analyze

    samples = [
        ("1984-02-10 10:00", "男"),
        ("1996-11-11 22:00", "男"),
        ("1990-05-20 10:30", "男"),
        ("1984-12-08 08:00", "女"),
        ("2000-08-15 14:00", "男"),
        ("1955-04-20 04:00", "女"),
    ]
    for dt, g in samples:
        c = chart("t", datetime_str=dt, gender=g)
        a = analyze(c)
        xs = (a.get("conclusion") or {}).get("dayun_liunian") or []
        assert xs, dt
        assert all(x.get("basis") for x in xs)
        for x in xs:
            assert "verdict" not in x


def test_sui_yun_bing_lin_marker():
    """岁运并临：大运干支 == 流年干支 → 只标记结构、不批吉凶（2026-09-30u）。"""
    from yishu_core.relations import ten_god as _tg
    chart = _chart("male")
    dayun = [{"index": 1, "ganzhi": "庚午", "start_age": 1, "end_age": 10},
             {"index": 2, "ganzhi": "戊辰", "start_age": 11, "end_age": 20}]
    liunian = [{"year": 1990, "ganzhi": "庚午", "age": 6},
               {"year": 1991, "ganzhi": "辛未", "age": 7}]
    xs = pattern.dayun_liunian_interactions(chart, dayun=dayun, liunian=liunian)
    hit = [x for x in xs if any(r["kind"] == "sui_yun_bing_lin" for r in x["relations"])]
    assert len(hit) == 1 and hit[0]["liunian"] == "庚午" and hit[0]["dayun"] == "庚午"
    for x in xs:
        for r in x["relations"]:
            assert "verdict" not in r
            assert r["kind"] != "sui_yun_bing_lin" or "标记" in r["text"]
