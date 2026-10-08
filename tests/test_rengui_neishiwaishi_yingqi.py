# -*- coding: utf-8 -*-
"""OPT-rengui_dz-03: 用神内外事定位 + 六级应期刻度

单测覆盖:
  - 内外事两向（各一例）
  - 六级刻度各一例（年/月/旬/半月/日/日）
  - 动态应期命中（月建+旬首）
  - narrate 输出含 rengui section

书源:
  - 《壬归》L109: 日用=外事, 辰用=内事
  - 《壬归》L112: 六级应期刻度

铁律: 纯结构标签，不判吉凶高低，不输出 verdict/weight/final_score。
"""
import importlib.util as _ilu
import sys
from pathlib import Path

_spec = _ilu.spec_from_file_location(
    "yi_pathguard", Path(__file__).with_name("pathguard.py"))
_pg = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_pg)

# 六壬四段脚本与别科同名（chart/analyze/…），用完必须还原路径（见 tests/pathguard.py）
with _pg.discipline_scripts("disciplines/liuren/scripts", "core"):
    from chart import chart
    from analyze import analyze
    from narrate import narrate


def test_waishi_direction():
    """外事例：初传落于日上两课（日干寄宫所在的四课上神）。
    书源《壬归》L109：「凡用在日上两课，为外事，主远，主去」"""
    c = chart('2024-06-15 10:00')
    a = analyze(c)
    rg = a.get("rengui") or {}
    assert rg.get("内外事") == "外事", f"应外事, 实得 {rg.get('内外事')}"
    md = narrate(a)
    assert '用神内外事 + 应期层级' in md
    assert '外事' in md


def test_neishi_direction():
    """内事例：初传落于辰上两课（日支所在的四课上神）。
    书源《壬归》L109：「用在辰上两课，为内事，主近，主来」"""
    # 2024-06-01 子时伏吟，初传落日支上
    c = chart('2024-06-01 02:00')
    a = analyze(c)
    rg = a.get("rengui") or {}
    assert rg.get("内外事") == "内事", f"应内事, 实得 {rg.get('内外事')}"
    md = narrate(a)
    assert '内事' in md


def test_yingqi_map_6_levels():
    """应期映射表固定含 6 个参考项（年/月/旬/半月/日/五日）。
    书源《壬归》L112 逐字给出 6 级。"""
    c = chart('2024-06-15 10:00')
    a = analyze(c)
    rg = a.get("rengui") or {}
    yq = rg.get("应期映射表") or {}
    assert len(yq) == 6, f"应期映射表应为 6 级, 实得 {len(yq)}"
    # 6 个参考基项与粒度
    expected = {
        "太岁":   "年",
        "月建":   "月",
        "旬首":   "旬",
        "节气首": "半月",
        "本日干": "日",
        "气首":   "五日",
    }
    for ref, gran in expected.items():
        assert ref in yq, f"应期映射表缺 {ref}"
        assert yq[ref]["granularity"] == gran, f"{ref} 粒度应为 {gran}, 实得 {yq[ref]['granularity']}"


def test_yingqi_map_basis_fields():
    """每项 basis 字段须含书源原文关键字串。书源《壬归》L112。"""
    c = chart('2024-06-15 10:00')
    a = analyze(c)
    yq = (a.get("rengui") or {}).get("应期映射表") or {}
    assert "事在年中" in yq["太岁"]["basis"]
    assert "事在本月" in yq["月建"]["basis"]
    assert "事在本旬" in yq["旬首"]["basis"]
    assert "半月之内" in yq["节气首"]["basis"]
    assert "本日之内" in yq["本日干"]["basis"]
    assert "五日之内" in yq["气首"]["basis"]


def test_yingqi_dynamic_hit_yuejian():
    """动态应期命中：初传 == 月支（月建）时，自动命中 月建 项。
    验证 2024-06-05 10:00（初传午 = 月支午）。"""
    c = chart('2024-06-05 10:00')
    a = analyze(c)
    rg = a.get("rengui") or {}
    hits = rg.get("动态应期命中") or []
    assert len(hits) >= 1, "月建应命中"
    yuejian_hits = [h for h in hits if h["reference"] == "月建"]
    assert len(yuejian_hits) == 1
    assert yuejian_hits[0]["granularity"] == "月"
    assert c["san_chuan"][0] == c["moment"]["month_branch"], \
        "月建命中验证: 初传应等于月支"


def test_yingqi_dynamic_hit_xunshou():
    """动态应期命中：初传 == 旬首时，自动命中 旬首 项。
    验证 2024-06-05 10:00（同时命中 月建 与 旬首）。"""
    c = chart('2024-06-05 10:00')
    a = analyze(c)
    rg = a.get("rengui") or {}
    hits = rg.get("动态应期命中") or []
    xunshou_hits = [h for h in hits if h["reference"] == "旬首"]
    assert len(xunshou_hits) == 1
    assert xunshou_hits[0]["granularity"] == "旬"


def test_no_yingqi_hit_no_dynamic():
    """动态命中为空时（初传与任何已接入参考基项不匹配），不应报错。
    验证 2024-06-15 10:00（初传寅，月支午，不相等）。"""
    c = chart('2024-06-15 10:00')
    a = analyze(c)
    rg = a.get("rengui") or {}
    hits = rg.get("动态应期命中") or []
    assert hits == [], f"初传寅 != 月支午，月建不应命中; 实得 {hits}"


def test_narrate_rengui_section_full():
    """narrate 输出须含完整 rengui section：标题、内外事定位、应期映射表头、动态命中。"""
    c = chart('2024-06-15 10:00')
    a = analyze(c)
    md = narrate(a)
    assert '用神内外事 + 应期层级' in md
    assert '内外事定位' in md
    assert '应期层级映射表' in md
    # 6 级全称
    for level in ['太岁', '月建', '旬首', '节气首', '本日干', '气首']:
        assert level in md, f"narrate 缺 {level}"
