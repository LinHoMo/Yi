# -*- coding: utf-8 -*-
"""纳甲地支、世应相隔、爻值序列（六十四卦优先）。"""
from __future__ import annotations

from yishu_core.najia import najia_branch, response_position
from yishu_core.symbols import yao_values


class TestNajiaBranch:
    def test_qian_pure_six_lines(self):
        # 乾为天：内卦子寅辰，外卦午申戌
        assert [najia_branch("乾", i) for i in range(1, 7)] == [
            "子", "寅", "辰", "午", "申", "戌",
        ]

    def test_kun_pure_six_lines(self):
        # 坤为地：阴卦逆排
        assert [najia_branch("坤", i) for i in range(1, 7)] == [
            "未", "巳", "卯", "丑", "亥", "酉",
        ]

    def test_gou_upper_qian_lower_xun(self):
        # 姤 = 上乾下巽
        assert najia_branch("姤", 1) == "丑"
        assert najia_branch("姤", 3) == "酉"
        assert najia_branch("姤", 4) == "午"
        assert najia_branch("姤", 6) == "戌"

    def test_invalid_position_or_name(self):
        assert najia_branch("乾", 0) is None
        assert najia_branch("乾", 7) is None
        assert najia_branch("", 1) is None
        assert najia_branch("不存在", 1) is None


class TestResponsePosition:
    def test_world1_to_response4(self):
        assert response_position(1) == 4

    def test_world4_to_response1(self):
        assert response_position(4) == 1

    def test_all_positions_involution(self):
        expected = {1: 4, 2: 5, 3: 6, 4: 1, 5: 2, 6: 3}
        for world, resp in expected.items():
            assert response_position(world) == resp
            assert response_position(resp) == world

    def test_invalid_returns_none(self):
        assert response_position(0) is None
        assert response_position(7) is None


class TestYaoValues:
    def test_qian_hexagram_six_lines(self):
        # 八纯卦同名优先按六十四卦：6 爻皆少阳
        assert yao_values("乾") == [7, 7, 7, 7, 7, 7]

    def test_gou_moving_line_1(self):
        # 姤（上乾下巽）初爻阴动 → 老阴 6，余静爻
        yq = yao_values("姤", moving=(1,))
        assert yq == [6, 7, 7, 7, 7, 7]

    def test_gou_static_lines(self):
        # 下巽 [0,1,1] 上乾 [1,1,1] → 少阴少阳少阳 ×2
        assert yao_values("姤") == [8, 7, 7, 7, 7, 7]

    def test_qian_moving_yang(self):
        yq = yao_values("乾", moving=(6,))
        assert yq == [7, 7, 7, 7, 7, 9]

    def test_unknown_name_raises(self):
        try:
            yao_values("不存在")
        except KeyError:
            pass
        else:
            raise AssertionError("未知卦名应抛 KeyError")
