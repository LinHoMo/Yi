# -*- coding: utf-8 -*-
"""六神旺衰标签（逢恩/归垣）试点单测 — OPT-yiin_dz-05。

覆盖：四季（月支）× 六神 × 宫（爻位地支）。
书源：《易隐》曹九锡 L879。
口径：仅测试结构标签的正确性，不涉及 verdict/weight/final_score。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "core"))

from classical_enhancements_shen_yao import (  # noqa: E402
    analyze_six_god_wang_shuai,
    _SIX_GOD_FENG_EN,
    _SIX_GOD_GUI_YUAN_SEASONAL,
    _SIX_GOD_GUI_YUAN_ELEMENTAL,
)


def _make_result(month_sb: str, lines: list[dict]) -> dict:
    return {
        "original_hexagram": {"yao_lines": lines},
        "divination_time": {"month_stem_branch": month_sb},
    }


def test_feng_en_all_six_gods():
    """六种六神的逢恩条件均正确识别。"""
    # 月支选申（秋），让当权归垣不干扰（冬武才归垣）
    lines = [
        {"position": 1, "name": "初九", "six_spirit": "青龙", "earthly_branch": "子"},  # 龙入水
        {"position": 2, "name": "六二", "six_spirit": "朱雀", "earthly_branch": "寅"},  # 雀入木
        {"position": 3, "name": "九三", "six_spirit": "勾陈", "earthly_branch": "午"},  # 勾入火
        {"position": 4, "name": "九四", "six_spirit": "螣蛇", "earthly_branch": "卯"},  # 蛇入木
        {"position": 5, "name": "九五", "six_spirit": "白虎", "earthly_branch": "辰"},  # 虎入土
        {"position": 6, "name": "上六", "six_spirit": "玄武", "earthly_branch": "酉"},  # 武入金
    ]
    result = _make_result("甲申", lines)
    out = analyze_six_god_wang_shuai(result)

    for entry in out["lines"]:
        assert entry["feng_en"], f"{entry['name']}({entry['six_spirit']}/{entry['branch']}) 逢恩应为 True"

    assert len(out["summary"]["逢恩"]) == 6, f"逢恩数应为 6, got {len(out['summary']['逢恩'])}"


def test_gui_yuan_seasonal_four_seasons():
    """四季当权归垣：春龙、夏雀、秋虎、冬武。"""
    cases = [
        ("寅", "青龙", True),   # 春龙
        ("卯", "青龙", True),
        ("寅", "玄武", False),  # 冬武, 春不应归垣
        ("巳", "朱雀", True),   # 夏雀
        ("午", "朱雀", True),
        ("申", "白虎", True),   # 秋虎
        ("酉", "白虎", True),
        ("亥", "玄武", True),   # 冬武
        ("子", "玄武", True),
        ("辰", "勾陈", True),   # 三九月勾
        ("戌", "勾陈", True),
        ("丑", "螣蛇", True),   # 六十二月蛇
        ("未", "螣蛇", True),
    ]
    for month, god, expected in cases:
        lines = [{"position": 1, "name": "测试", "six_spirit": god, "earthly_branch": "丑"}]
        result = _make_result(f"甲{month}", lines)
        out = analyze_six_god_wang_shuai(result)
        actual = out["lines"][0]["gui_yuan_seasonal"]
        assert actual == expected, (
            f"月支={month} {god}: 当权归垣应为 {expected}, got {actual}"
        )


def test_gui_yuan_elemental():
    """本象归垣：六神地支与本宫地支同五行。"""
    cases = [
        ("青龙", "寅", True),    # 龙入木
        ("青龙", "卯", True),
        ("青龙", "子", False),   # 水是逢恩, 非归垣
        ("朱雀", "巳", True),    # 雀入火
        ("朱雀", "午", True),
        ("勾陈", "辰", True),    # 勾入辰戌
        ("勾陈", "戌", True),
        ("螣蛇", "丑", True),    # 蛇入丑未
        ("螣蛇", "未", True),
        ("白虎", "申", True),    # 虎入金
        ("白虎", "酉", True),
        ("玄武", "亥", True),    # 武入水
        ("玄武", "子", True),
    ]
    for god, branch, expected in cases:
        lines = [{"position": 1, "name": "测试", "six_spirit": god, "earthly_branch": branch}]
        result = _make_result("甲申", lines)
        out = analyze_six_god_wang_shuai(result)
        actual = out["lines"][0]["gui_yuan_elemental"]
        assert actual == expected, (
            f"{god}/{branch}: 本象归垣应为 {expected}, got {actual}"
        )


def test_multiple_tags_coexist():
    """同一爻同时满足逢恩 + 当权归垣时，标签应合并。"""
    # 寅月，青龙落子 → 逢恩(龙入水) + 当权归垣(春青龙)
    lines = [{"position": 1, "name": "初九", "six_spirit": "青龙", "earthly_branch": "子"}]
    result = _make_result("甲寅", lines)
    out = analyze_six_god_wang_shuai(result)

    entry = out["lines"][0]
    assert entry["feng_en"] is True
    assert entry["gui_yuan_seasonal"] is True
    assert "逢恩" in entry["tag"]
    assert "当权归垣" in entry["tag"]


def test_empty_lines_graceful():
    """空卦不崩溃。"""
    result = {"original_hexagram": {"yao_lines": []}, "divination_time": {}}
    out = analyze_six_god_wang_shuai(result)
    assert out["lines"] == []
    assert "无逢恩归垣" in out["comment"]


def test_month_branch_parsing():
    """月支解析正确。"""
    lines = [{"position": 1, "name": "初九", "six_spirit": "青龙", "earthly_branch": "子"}]
    for month_sb, expected_branch, expected_elem in [
        ("丙寅", "寅", "木"),
        ("戊辰", "辰", "土"),
        ("庚午", "午", "火"),
        ("壬申", "申", "金"),
        ("甲子", "子", "水"),
    ]:
        result = _make_result(month_sb, lines)
        out = analyze_six_god_wang_shuai(result)
        assert out["month_branch"] == expected_branch, f"{month_sb} 月支解析错"
        assert out["month_element"] == expected_elem, f"{month_sb} 月支五行解析错"


def _run_all():
    test_feng_en_all_six_gods()
    print("✅ test_feng_en_all_six_gods passed")
    test_gui_yuan_seasonal_four_seasons()
    print("✅ test_gui_yuan_seasonal_four_seasons passed")
    test_gui_yuan_elemental()
    print("✅ test_gui_yuan_elemental passed")
    test_multiple_tags_coexist()
    print("✅ test_multiple_tags_coexist passed")
    test_empty_lines_graceful()
    print("✅ test_empty_lines_graceful passed")
    test_month_branch_parsing()
    print("✅ test_month_branch_parsing passed")
    print("\n🎉 全部 6 项单测通过")


if __name__ == "__main__":
    _run_all()
