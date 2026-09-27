# -*- coding: utf-8 -*-
"""应期相对窗 → 绝对日窗；节奏对 RHYTHM_PAIRS 的公开行为。"""
from __future__ import annotations

from datetime import datetime

import yingqi_windows as yw
from evaluate import RHYTHM_PAIRS


class TestRelativeWindow:
    def test_same_day(self):
        assert yw.relative_window("当日") == (0, 0, "当日")
        assert yw.relative_window("当天") == (0, 0, "当日")
        assert yw.relative_window("应在当天了结") == (0, 0, "当日")

    def test_next_day(self):
        assert yw.relative_window("次日") == (1, 1, "次日")
        assert yw.relative_window("应验于次日") == (1, 1, "次日")

    def test_slow_windows(self):
        assert yw.relative_window("月余") == (20, 50, "月余窗")
        assert yw.relative_window("旺相之月") == (20, 50, "月余窗")
        assert yw.relative_window("年内") == (1, 365, "年内窗")
        assert yw.relative_window("经年") == (1, 365, "年内窗")

    def test_no_match(self):
        assert yw.relative_window("很快") is None
        assert yw.relative_window("") is None
        assert yw.relative_window("出空") is None


class TestResolveCaseAnchor:
    def test_from_case_year_month_day(self):
        dt = yw.resolve_case_anchor({}, {"year": 2020, "month": 5, "day": 1})
        assert dt == datetime(2020, 5, 1)

    def test_from_exp_input_date_text(self):
        dt = yw.resolve_case_anchor({"date": "公历 2024-03-05 占"}, {})
        assert dt == datetime(2024, 3, 5)

    def test_case_fields_precedence(self):
        dt = yw.resolve_case_anchor(
            {"date": "2024-03-05"}, {"year": 2020, "month": 5, "day": 1}
        )
        assert dt == datetime(2020, 5, 1)

    def test_invalid_returns_none(self):
        assert yw.resolve_case_anchor({}, {}) is None
        assert yw.resolve_case_anchor({}, {"year": 2020, "month": 13, "day": 1}) is None
        assert yw.resolve_case_anchor({"date": "无日期"}, {}) is None


class TestDateInWindow:
    def test_inclusive_bounds(self):
        anchor = datetime(2024, 3, 5)
        assert yw.date_in_window(anchor, "2024-03-05", 0, 0) is True
        assert yw.date_in_window(anchor, "2024-03-06", 1, 1) is True
        assert yw.date_in_window(anchor, "2024-03-04", -1, -1) is True

    def test_out_of_window(self):
        anchor = datetime(2024, 3, 5)
        assert yw.date_in_window(anchor, "2024-03-07", 1, 1) is False
        assert yw.date_in_window(anchor, "2024-03-04", 0, 0) is False

    def test_accepts_datetime_suffix(self):
        anchor = datetime(2024, 3, 5)
        assert yw.date_in_window(anchor, "2024-03-06 12:30", 1, 1) is True

    def test_invalid_date_returns_false(self):
        anchor = datetime(2024, 3, 5)
        assert yw.date_in_window(anchor, "not-a-date", 0, 0) is False
        assert yw.date_in_window(anchor, "", 0, 0) is False


class TestRhythmPairs:
    def test_shape_and_known_entries(self):
        pairs = list(RHYTHM_PAIRS)
        assert pairs
        for keys, tokens in pairs:
            assert isinstance(keys, tuple) and keys
            assert isinstance(tokens, tuple) and tokens
        flat_keys = [k for keys, _ in pairs for k in keys]
        assert "次日" in flat_keys
        assert "出空" in flat_keys

    def test_fast_window_agrees_with_rhythm(self):
        # 「次日」在相对窗里解析出的标签，必须落在快节奏对的基准词中
        lo, hi, label = yw.relative_window("次日")
        assert (lo, hi) == (1, 1)
        fast_keys = next(keys for keys, _ in RHYTHM_PAIRS if "次日" in keys)
        assert label in fast_keys

    def test_window_keywords_covered_by_relative_window(self):
        # 有日窗语义的基准词都能被 relative_window 解析（出空等节奏词除外）
        window_like = {"次日", "当天", "当日", "年内", "月余", "经年"}
        for keys, _ in RHYTHM_PAIRS:
            for k in keys:
                if k in window_like:
                    assert yw.relative_window(k) is not None, k
