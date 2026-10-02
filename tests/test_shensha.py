# -*- coding: utf-8 -*-
"""神煞安星断言（2026-09-30u 补全批：飞刃/金舆/将星/天医/亡神/劫煞/孤辰寡宿/阴差阳错）。

口径：神煞安法是机械步骤；本测试只验证「落地支是否正确」，不评吉凶
（`AGENTS.md` 铁律一/三；shensha 模块头声明通行起例、无法逐字核对原文）。
"""
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[1] / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from yishu_core.shensha import (  # noqa: E402
    FEI_REN, JIN_YU, YANG_REN, TIAN_YI_YUE, GU_CHEN, GUA_SU,
    YIN_CHA_YANG_CUO, shensha_of_chart,
)


def _names(result) -> dict:
    return {x["name"]: x["at"] for x in result}


def test_fei_ren_offsets_yang_ren():
    """飞刃 = 羊刃之冲：甲刃卯→飞刃酉、丙刃午→子、庚刃酉→卯、壬刃子→午。"""
    assert YANG_REN["甲"] == "卯" and FEI_REN["甲"] == "酉"
    assert YANG_REN["丙"] == "午" and FEI_REN["丙"] == "子"
    assert YANG_REN["庚"] == "酉" and FEI_REN["庚"] == "卯"
    assert YANG_REN["壬"] == "子" and FEI_REN["壬"] == "午"


def test_fei_ren_in_chart():
    """甲日主盘中见酉 → 飞刃安于酉。"""
    r = shensha_of_chart("甲", "庚", "申", "辰", ["庚", "酉", "甲", "辰"])
    names = _names(r)
    assert names.get("飞刃") == ["酉"]


def test_jin_yu_by_day_stem():
    """金舆（日干）：甲辰、乙巳、丙未、丁申、庚戌、辛亥、壬丑、癸卯。"""
    assert JIN_YU["甲"] == "辰" and JIN_YU["丁"] == "申"
    assert JIN_YU["庚"] == "戌" and JIN_YU["癸"] == "卯"
    r = shensha_of_chart("丁", "庚", "申", "未", ["庚", "申", "丁", "未"])
    names = _names(r)
    assert names.get("金舆") == ["申"]  # 丁→申，盘中申在


def test_jiang_wang_jie_water_ju():
    """申子辰水局：将星子、亡神亥、劫煞巳。"""
    assert shensha_of_chart("甲", "庚", "申", "辰", ["庚", "子", "甲", "巳"])
    r = shensha_of_chart("甲", "庚", "申", "辰", ["庚", "子", "甲", "巳"])
    names = _names(r)
    assert names.get("将星(日支)") == ["子"]
    assert names.get("劫煞(日支)") == ["巳"]  # 巳在盘
    assert "亡神(日支)" not in names  # 亥不在盘


def test_jiang_wang_jie_fire_ju():
    """寅午戌火局：将星午、亡神巳、劫煞寅（巳不在盘则不报亡神）。"""
    r = shensha_of_chart("甲", "丙", "午", "戌", ["丙", "午", "甲", "寅"])
    names = _names(r)
    assert names.get("将星(日支)") == ["午"]
    assert names.get("劫煞(日支)") == ["寅"]
    assert "亡神(日支)" not in names  # 巳不在盘


def test_tian_yi_month_branch():
    """天医 = 月支前一位：寅月见丑、午月见巳、亥月见戌。"""
    assert TIAN_YI_YUE["寅"] == "丑" and TIAN_YI_YUE["午"] == "巳" and TIAN_YI_YUE["亥"] == "戌"
    # 甲日主，寅月（盘内月支寅），丑在盘中 → 天医=丑
    r = shensha_of_chart("甲", "庚", "寅", "辰", ["庚", "寅", "甲", "丑"])
    names = _names(r)
    assert names.get("天医") == ["丑"]


def test_gu_chen_gua_su():
    """孤辰寡宿（方局）：亥子丑见寅孤/戌寡；寅卯辰见巳孤/丑寡。"""
    assert GU_CHEN["子"] == "寅" and GUA_SU["子"] == "戌"
    assert GU_CHEN["卯"] == "巳" and GUA_SU["卯"] == "丑"
    # 子年（年支子）：孤辰寅、寡宿戌；盘中寅在 → 孤辰报
    r = shensha_of_chart("甲", "庚", "子", "辰", ["庚", "寅", "甲", "子"])
    names = _names(r)
    assert names.get("孤辰(年支)") == ["寅"]
    assert "寡宿(年支)" not in names  # 戌不在盘


def test_yin_cha_yang_cuo_days():
    """阴差阳错日 12 组照录；盘中命中即报。"""
    assert len(YIN_CHA_YANG_CUO) == 12
    assert "丙子" in YIN_CHA_YANG_CUO and "壬戌" in YIN_CHA_YANG_CUO
    # 丙子日主：阴差阳错 → 安于日支子
    r = shensha_of_chart("丙", "庚", "申", "子", ["庚", "申", "丙", "子"])
    names = _names(r)
    assert names.get("阴差阳错") == ["子"]
    # 甲子日不入（不在 12 组）
    r2 = shensha_of_chart("甲", "庚", "申", "子", ["庚", "申", "甲", "子"])
    assert "阴差阳错" not in _names(r2)


def test_tongzi_shasha_autumn_yin_zi():
    """童子煞：秋生（申月）日支寅或时支子 → 触发；标注非子平经典原文（verified=false）。"""
    r = shensha_of_chart("甲", "甲", "子", "寅", ["甲", "申", "甲", "子"])
    tz = [x for x in r if x["name"] == "童子煞"]
    assert tz and set(tz[0]["at"]) == {"寅", "子"}
    assert "非《渊海子平》" in tz[0]["basis"]


def test_tongzi_shasha_spring_yin_zi():
    """童子煞：春生（寅月）日/时支见子 → 触发。"""
    r = shensha_of_chart("甲", "甲", "寅", "子", ["甲", "寅", "甲", "子"])
    tz = [x for x in r if x["name"] == "童子煞"]
    assert tz and "子" in tz[0]["at"]


def test_tongzi_shasha_summer_no_hit():
    """童子煞：夏生（午月）日时支无卯/未/辰、纳音无关 → 不触发。"""
    r = shensha_of_chart("甲", "甲", "午", "申", ["甲", "午", "甲", "申"])
    assert not [x for x in r if x["name"] == "童子煞"]


def test_tongzi_shasha_nayin_tu():
    """童子煞：土纳音（庚午路旁土）日/时支见辰 → 触发（纳音分支）。"""
    r = shensha_of_chart("甲", "庚", "午", "辰", ["庚", "午", "甲", "辰"])
    tz = [x for x in r if x["name"] == "童子煞"]
    assert tz and "辰" in tz[0]["at"]
