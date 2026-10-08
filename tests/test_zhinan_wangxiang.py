# -*- coding: utf-8 -*-
"""OPT-liuren_zhinan_dz-02 单测：旺相休囚死 12 月 × 5 行逐月对拍。

验证 core wangxiangxiuqiusi 表读数（《六壬指南》L246-L248「旺相休囚死」）：
  - 12 月支 ×（用神/日干/日支）三对象全部输出非空 state
  - 源 L246「当令者旺、旺所生者相、生旺者休、克旺者囚、旺所克者死」与表取值逐格比对
  - analyze 输出 narrate 含「旺相休囚死」段落
  - **不判吉凶**: 旺/相/休/囚/死 仅作状态标签，不含「求就官职」等断语
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

import importlib.util as _ilu

_spec = _ilu.spec_from_file_location(
    "yi_pathguard", Path(__file__).with_name("pathguard.py"))
_pg = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_pg)

# 六壬四段脚本与别科同名（chart/analyze/…），用完必须还原路径（见 tests/pathguard.py）
with _pg.discipline_scripts("disciplines/liuren/scripts", "core"):
    from chart import chart
    from analyze import analyze
    from narrate import narrate
    from yishu_core.symbols import (EARTHLY_BRANCHES, WANG_XIANG_XIU_QIU_SI,
                                    wangxiangxiuqiusi)


# ── 1. 12 月 × 5 行表自身完整性对拍（与 core 表逐格一致） ──

@pytest.mark.parametrize("month_branch", list(WANG_XIANG_XIU_QIU_SI.keys()))
def test_core_table_12month_complete(month_branch):
    """每月 5 元素全覆盖（12×5=60 格），不遗漏取值。"""
    row = WANG_XIANG_XIU_QIU_SI[month_branch]
    assert set(row.keys()) == {"木", "火", "土", "金", "水"}, (
        f"{month_branch}: 元素不全")
    assert set(row.values()) == {"旺", "相", "休", "囚", "死"}, (
        f"{month_branch}: 状态值非法")


@pytest.mark.parametrize("month_branch,expected", [
    ("寅", {"木": "旺", "火": "相", "水": "休", "金": "囚", "土": "死"}),
    ("卯", {"木": "旺", "火": "相", "水": "休", "金": "囚", "土": "死"}),
    ("辰", {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"}),
    ("巳", {"火": "旺", "土": "相", "木": "休", "水": "囚", "金": "死"}),
    ("午", {"火": "旺", "土": "相", "木": "休", "水": "囚", "金": "死"}),
    ("未", {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"}),
    ("申", {"金": "旺", "水": "相", "土": "休", "火": "囚", "木": "死"}),
    ("酉", {"金": "旺", "水": "相", "土": "休", "火": "囚", "木": "死"}),
    ("戌", {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"}),
    ("亥", {"水": "旺", "木": "相", "金": "休", "土": "囚", "火": "死"}),
    ("子", {"水": "旺", "木": "相", "金": "休", "土": "囚", "火": "死"}),
    ("丑", {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"}),
])
def test_core_table_values_match_source(month_branch, expected):
    """逐月对拍 core 表取值与源 L248 逐字：当令者旺／旺所生者相／生旺者休／克旺者囚／旺所克者死。"""
    assert WANG_XIANG_XIU_QIU_SI[month_branch] == expected, (
        f"{month_branch}月取值与源不符")


# ── 2. analyze 输出：wangxiangxiuqiusi 三段标签均存在且非空 ──

@pytest.mark.parametrize("month_idx,seed", [
    (0, "2024-01-15 10:00"),   # 丑月
    (1, "2024-02-15 10:00"),   # 寅月
    (2, "2024-03-15 10:00"),   # 卯月
    (3, "2024-04-15 10:00"),   # 辰月
    (4, "2024-05-15 10:00"),   # 巳月
    (5, "2024-06-15 10:00"),   # 午月
    (6, "2024-07-15 10:00"),   # 未月
    (7, "2024-08-15 10:00"),   # 申月
    (8, "2024-09-15 10:00"),   # 酉月
    (9, "2024-10-15 10:00"),   # 戌月
    (10, "2024-11-15 10:00"),  # 亥月
    (11, "2024-12-15 10:00"),  # 子月
])
def test_analyze_wangxiang_all_12months(month_idx, seed):
    """12 个月的 chart，analyze 输出 wangxiangxiuqiusi 三段标签均非空 state。"""
    c = chart(seed)
    a = analyze(c)
    wx = a.get("wangxiangxiuqiusi") or {}
    assert "用神(初传)" in wx, f"{seed}: 缺用神标签"
    assert "日干" in wx, f"{seed}: 缺日干标签"
    assert "日支" in wx, f"{seed}: 缺日支标签"
    for label in ("用神(初传)", "日干", "日支"):
        entry = wx[label]
        assert entry.get("state"), f"{seed}/{label}: state 为空"
        assert entry["state"] in {"旺", "相", "休", "囚", "死"}, (
            f"{seed}/{label}: 非法状态 {entry['state']}")
        assert entry.get("basis"), f"{seed}/{label}: basis 为空"


def test_narrate_contains_wangxiang_section():
    """narrate 输出应含「旺相休囚死」段落。"""
    c = chart("2024-06-15 10:00")
    a = analyze(c)
    md = narrate(a)
    assert "旺相休囚死" in md, "narrate 缺旺相休囚死段"
    # 不判吉凶：不得含断语字面量
    for tabu in ("求就官职", "经营利禄", "囚系呻吟", "死亡悲哭", "病疾淹延"):
        assert tabu not in md, f"narrate 含吉凶断语「{tabu}」（违规）"


def test_wangxiang_uses_month_branch():
    """旺相判断应基于月支（moment.month_branch），非时支。"""
    # 选一个月支明确的日期：2024-06-15 月支=午
    c = chart("2024-06-15 10:00")
    a = analyze(c)
    wx = a.get("wangxiangxiuqiusi", {})
    _mb = c["moment"]["month_branch"]
    assert wx["用神(初传)"]["basis"].startswith(f"{_mb}月"), (
        f"basis 应以月支{_mb}开头，实得: {wx['用神(初传)']['basis']}")
