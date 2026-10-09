# -*- coding: utf-8 -*-
"""命科四柱结构补充因子断言：三会方局 / 胎元 / 流月 / 小运 / 天克地冲 / 十神组合。

口径：这些均为**机械结构标签**——本测试只验「起法与判定步骤」是否正确，
不评吉凶（`AGENTS.md` 铁律一/三）。小运起法为通行口径、流派有别，模块已标 verified=False。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "core", ROOT / "disciplines" / "ming" / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from pattern import (  # noqa: E402
    tai_yuan, liuyue_table, xiao_yun_table,
    tian_ke_di_chong, ten_god_combos, san_hui_present,
    pillar_relations,
)


def _pillars(**kw) -> dict:
    return {k: {"ganzhi": v, "stem": v[0], "branch": v[1]} for k, v in kw.items()}


def test_tai_yuan_month_stem_plus1_branch_plus3():
    """胎元：月干进一位、月支进三位（《三命通会》）。辛巳→壬申、丙子→丁卯、甲申→乙亥。"""
    assert tai_yuan("辛巳")["ganzhi"] == "壬申"
    assert tai_yuan("丙子")["ganzhi"] == "丁卯"
    assert tai_yuan("甲申")["ganzhi"] == "乙亥"
    assert tai_yuan("") is None


def test_san_hui_needs_all_three():
    """三会方局须三支全：寅卯辰→木局；缺一不报。"""
    got = san_hui_present(_pillars(year="壬寅", month="丁卯", day="戊辰", hour="甲子"))
    assert [x["element"] for x in got] == ["木"]
    assert san_hui_present(_pillars(year="壬寅", month="丁卯", day="戊戌", hour="甲子")) == []


def test_liuyue_tiger_rule_forward_from_yin():
    """流月：正月（寅）起五虎遁。庚年正月戊寅，顺行十二位。"""
    rows = liuyue_table("庚", "乙", 12)
    assert rows[0]["ganzhi"] == "戊寅" and rows[0]["ten_god"] == "正财"
    assert [r["ganzhi"] for r in rows] == [
        "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
        "甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑"]


def test_xiao_yun_direction_and_start_from_hour():
    """小运：自生时起，阳男顺行（庚年男、时柱辛巳→1岁壬午、2岁癸未）。"""
    chart = {
        "pillars": _pillars(year="庚午", month="辛巳", day="乙酉", hour="辛巳"),
        "birth": {"gender": "男"},
    }
    rows = xiao_yun_table(chart, 3)
    assert [r["ganzhi"] for r in rows] == ["壬午", "癸未", "甲申"]
    assert all(r["verified"] is False for r in rows)


def test_tian_ke_di_chong_stem_ke_and_branch_chong():
    """天克地冲：干相克且支相冲。己卯 vs 乙酉（木克土、卯酉冲）成立；己卯 vs 乙卯（不冲）不成立。"""
    chart = {"pillars": _pillars(year="庚午", month="辛巳", day="乙酉", hour="辛巳")}
    got = tian_ke_di_chong(chart, dayun=[], liunian=[
        {"year": 1999, "ganzhi": "己卯"}, {"year": 2000, "ganzhi": "己卯"}])
    assert [t["ganzhi"] for t in got] == ["己卯", "己卯"]
    none = tian_ke_di_chong(chart, dayun=[], liunian=[{"year": 2003, "ganzhi": "甲申"}])
    assert none == []


def test_ten_god_combos_by_transparent_stems():
    """十神组合按透干共现判结构：伤官+正官→伤官见官；财+杀+身弱→财滋弱杀。"""
    chart = {"pillars": _pillars(year="甲子", month="戊辰", day="辛酉", hour="丙申")}
    chart["pillars"]["year"]["ten_god"] = "伤官"
    chart["pillars"]["month"]["ten_god"] = "正官"
    names = {c["name"] for c in ten_god_combos(chart)}
    assert "伤官见官" in names

    cai_sha = {"pillars": _pillars(year="甲子", month="戊辰", day="辛酉", hour="丙申")}
    cai_sha["pillars"]["year"]["ten_god"] = "偏财"
    cai_sha["pillars"]["month"]["ten_god"] = "七杀"
    assert "财滋弱杀" in {c["name"] for c in ten_god_combos(cai_sha, strength="偏弱")}
    assert "财滋弱杀" not in {c["name"] for c in ten_god_combos(cai_sha, strength="偏旺")}


def _rel_texts(chart: dict) -> list[str]:
    return [r["text"] for r in pillar_relations(chart)]


def test_pillar_relations_stem_wuhe():
    """四柱天干五合（甲己/乙庚/丙辛/丁壬/戊癸，表取 core.relations.STEM_WUHE）。"""
    assert _rel_texts({"pillars": _pillars(year="丁亥", month="壬寅",
                                           day="甲辰", hour="丙午")}) == [
        "年月干丁壬合", "年月支亥寅六合"]
    assert _rel_texts({"pillars": _pillars(year="庚午", month="辛巳",
                                           day="乙酉", hour="辛巳")}) == ["年日干庚乙合"]


def test_pillar_relations_he_chong_hai():
    """四柱地支两两关系：亥寅六合、子午六冲、寅巳六害（表取 core.symbols）。"""
    assert _rel_texts({"pillars": _pillars(year="丁亥", month="壬寅",
                                           day="甲辰", hour="丙午")}) == [
        "年月干丁壬合", "年月支亥寅六合"]
    assert _rel_texts({"pillars": _pillars(year="甲子", month="庚午",
                                           day="戊辰", hour="丁巳")}) == ["年月支子午六冲"]
    assert _rel_texts({"pillars": _pillars(year="甲寅", month="己巳",
                                           day="癸未", hour="丙戌")}) == [
        "年月干甲己合", "年月支寅巳六害"]


def test_pillar_relations_sanxing_and_self():
    """三刑：寅巳申三现→无恩之刑（同卦另成寅申冲/巳申合/寅巳害，结构并存非互斥）；亥两现→自刑。"""
    assert _rel_texts({"pillars": _pillars(year="甲寅", month="己巳",
                                           day="戊申", hour="乙卯")}) == [
        "年月干甲己合", "年月支寅巳六害", "年日支寅申六冲",
        "月日支巳申六合", "无恩之刑"]
    assert _rel_texts({"pillars": _pillars(year="乙亥", month="己卯",
                                           day="辛亥", hour="乙卯")}) == ["自刑"]


def test_pillar_relations_none_when_no_pair():
    """无干合与支合/冲/害/刑之对 → 空（防误报；同支不成对）。"""
    assert _rel_texts({"pillars": _pillars(year="甲子", month="丙子",
                                           day="戊子", hour="庚子")}) == []
    assert _rel_texts({"pillars": _pillars(year="甲子", month="庚午",
                                           day="戊辰", hour="丁巳")}) == ["年月支子午六冲"]
