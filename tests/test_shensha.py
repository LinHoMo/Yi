# -*- coding: utf-8 -*-
"""神煞安星断言（2026-09-30u 补全批：飞刃/金舆/将星/天医/亡神/劫煞/孤辰寡宿/阴差阳错）。

口径：神煞安法是机械步骤；本测试只验证「落地支是否正确」，不评吉凶
（`AGENTS.md` 铁律一/三）。
2026-10-09 订正：劫煞（火/金/木三组曾被轮转错配）与金舆（癸）已按书源逐字核对改正，
出处见 `core/yishu_core/shensha.py` 表注（sanming_tonghui_dz:615、lantai_miaoxuan_dz:242、
mingli_tanyuan_dz:781/:785）。本文件同时把「三合四组全枚举」与「金舆=禄前二辰」两条结构
不变量补成断言——此前只测水/火两组，故轮转类错配可以长存。
"""
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[1] / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from yishu_core.shensha import (  # noqa: E402
    FEI_REN, JIN_YU, JIE_SHA, LU_SHEN, YANG_REN, TIAN_YI_YUE, GU_CHEN, GUA_SU,
    YIN_CHA_YANG_CUO, shensha_of_chart,
)
from yishu_core.symbols import EARTHLY_BRANCHES as Z  # noqa: E402


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
    """金舆（日干）：书源定式「金舆常居禄前二辰」逐格对拍；癸=寅（书源「癸逢虎」）。"""
    for stem, lu in LU_SHEN.items():
        assert JIN_YU[stem] == Z[(Z.index(lu) + 2) % 12], f"{stem} 的金舆违「禄前二辰」"
    assert JIN_YU["甲"] == "辰" and JIN_YU["癸"] == "寅"
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


def test_jie_sha_table_four_groups():
    """劫煞 = 三合绝位，四组全枚举锁定（sanming_tonghui_dz:615 逐字；lantai_miaoxuan_dz:242 旁证）。

    2026-10-09 前只测水/火两组，故「火→寅、金→申、木→亥」这类轮转错配可长存。
    """
    assert JIE_SHA == {"水": "巳", "火": "亥", "金": "寅", "木": "申"}


def test_jiang_wang_jie_fire_ju():
    """寅午戌火局：将星午、劫煞亥（火绝在亥；巳不在盘则不报亡神）。"""
    r = shensha_of_chart("甲", "丙", "午", "戌", ["丙", "午", "甲", "亥"])
    names = _names(r)
    assert names.get("将星(日支)") == ["午"]
    assert names.get("劫煞(日支)") == ["亥"]
    assert "亡神(日支)" not in names  # 巳不在盘


def test_jie_sha_metal_ju():
    """巳酉丑金局：将星酉、劫煞寅（金绝在寅）。"""
    r = shensha_of_chart("甲", "戊", "申", "酉", ["戊", "辛", "酉", "寅"])
    names = _names(r)
    assert names.get("将星(日支)") == ["酉"]
    assert names.get("劫煞(日支)") == ["寅"]


def test_jie_sha_wood_ju():
    """亥卯未木局：将星卯、劫煞申（木绝在申）。"""
    r = shensha_of_chart("甲", "丁", "亥", "卯", ["丁", "癸", "卯", "申"])
    names = _names(r)
    assert names.get("将星(日支)") == ["卯"]
    assert names.get("劫煞(日支)") == ["申"]


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
