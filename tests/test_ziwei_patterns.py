# -*- coding: utf-8 -*-
"""紫微斗数古法格局判定断言（2026-10-01q 扩充批：富局 1 + 贵局 8）。

口径：判据原文逐字在 `disciplines/ziwei/data/geju_rules.json`（书源《紫微斗數全書》卷一），
本测试只验「判定式是否按原文条件成立」——用合成命盘（不依赖真实安星，故可覆盖稀有局），
不评吉凶（`AGENTS.md` 铁律一/三）。**只测富局/贵局**：贫贱局/杂局按命科口径不判。
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core"
ZIWEI_SCRIPTS = ROOT / "disciplines" / "ziwei" / "scripts"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))


def _load_ziwei_analyze():
    """按**唯一模块名**从路径加载紫微 analyze，避免各科同名 `analyze` 互相遮蔽。

    八科 `scripts/` 同名（每科都有 analyze.py），本科脚本 import 期还会把自身
    `scripts/` 插进 `sys.path`（各科脚本都假设独占解释器）。故此处：① 用
    `spec_from_file_location` 给唯一名（不进 `sys.modules['analyze']`）；
    ② 加载后**还原 `sys.path`**，不污染根 pytest 对同名模块的解析。
    """
    spec = importlib.util.spec_from_file_location("ziwei_analyze_under_test",
                                                  ZIWEI_SCRIPTS / "analyze.py")
    mod = importlib.util.module_from_spec(spec)
    before = list(sys.path)
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path[:] = before
    return mod


judge_classical_patterns = _load_ziwei_analyze().judge_classical_patterns


def _chart(mg_branch, mg_main=(), mg_aux=(), extra=None, mg_idx=0):
    """最小合成命盘：命宫 + 若干具名/具支宫。extra: {名: (支, 主星, 辅星)}。"""
    palaces = {"命宫": {"branch": mg_branch,
                        "main_stars": list(mg_main), "aux_stars": list(mg_aux)}}
    for name, (br, m, a) in (extra or {}).items():
        palaces[name] = {"branch": br, "main_stars": list(m), "aux_stars": list(a)}
    return {"palaces": palaces,
            "ming_gong": {"palace_idx": mg_idx}, "shen_gong": {"palace_idx": mg_idx}}


def _hit(chart, name) -> bool:
    for c in judge_classical_patterns(chart):
        if c["名"] == name:
            return c["成立"]
    raise AssertionError(f"判据表里没有 {name}")


def test_jincan_guanghui_sun_alone_in_wu():
    """金灿光辉：太阳单守、命在午宫（单守=命宫主星恰为太阳一颗）。"""
    assert _hit(_chart("午", ["太阳"]), "金灿光辉")
    assert not _hit(_chart("午", ["太阳", "天梁"]), "金灿光辉")   # 双星同宫非「单守」
    assert not _hit(_chart("巳", ["太阳"]), "金灿光辉")           # 不在午宫


def test_richu_fusang_sun_in_mao():
    """日出扶桑：日在卯守命，或守官禄宫。"""
    assert _hit(_chart("卯", ["太阳"]), "日出扶桑")
    assert _hit(_chart("子", [], extra={"官禄": ("卯", ["太阳"], [])}), "日出扶桑")
    assert not _hit(_chart("寅", ["太阳"]), "日出扶桑")


def test_yueluo_haigong_moon_in_hai():
    """月落亥宫：太阴守命在亥。"""
    assert _hit(_chart("亥", ["太阴"]), "月落亥宫")
    assert not _hit(_chart("子", ["太阴"]), "月落亥宫")


def test_yuesheng_canghai_moon_in_zi_tianzhai():
    """月生沧海：太阴守田宅、田宅在子。"""
    assert _hit(_chart("午", [], extra={"田宅": ("子", ["太阴"], [])}), "月生沧海")
    assert not _hit(_chart("午", [], extra={"田宅": ("丑", ["太阴"], [])}), "月生沧海")


# ── 辅煞星书源说解（star_nature 扩容 + narrate 接线）────────────────────────

def _load_ziwei_narrate():
    spec = importlib.util.spec_from_file_location("ziwei_narrate_under_test",
                                                  ZIWEI_SCRIPTS / "narrate.py")
    mod = importlib.util.module_from_spec(spec)
    before = list(sys.path)
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path[:] = before
    return mod


def test_star_nature_covers_aux_but_not_verse_only():
    """star_nature 收卷一问答论有独立标题的辅煞星；火星/铃星只说「…歌曰」无实质正文，不收。"""
    stars = json.loads((ROOT / "disciplines" / "ziwei" / "data"
                        / "star_nature.json").read_text(encoding="utf-8"))["stars"]
    assert {"文曲", "左辅", "右弼", "禄存", "擎羊", "陀罗", "文昌"} <= set(stars)
    assert "火星" not in stars and "铃星" not in stars
    assert stars["文曲"]["quote"].endswith("贱。")          # 段界止于下一标题，不吞「问流年昌曲若何」


def test_narrate_renders_aux_star_source():
    """命宫辅煞星段：辅星须出书源引文（卷一性质 + 卷二本宫释义）。"""
    out = _load_ziwei_narrate().narrate({
        "chart_summary": {"命宫主星": "七杀", "格局": "—", "命宫地支": "酉",
                          "五行局": "金四局", "紫微所在": "午", "天府所在": "戌"},
        "lunar": {"year": 1984, "month": 1, "day": 9, "leap": False},
        "pillars": {"year": "甲子", "month": "丙寅", "day": "甲戌", "hour": "己巳"},
        "palaces": {"命宫": {"branch": "酉", "main_stars": ["七杀"],
                             "aux_stars": ["文曲", "天刑"]}},
        "shen_gong": {"branch": "丑"},
        "conclusion": {},
    })
    assert "命宫辅煞星" in out
    assert "問文曲所主若何" in out          # 卷一性质（star_nature）
    aux_seg = out.split("## 十二宫星义")[0].split("命宫辅煞星")[1]
    assert "天刑" not in aux_seg            # 无书源者不出


def test_wuqu_shouyuan_in_mao():
    """武曲守垣：武曲守命在卯宫，余不是。"""
    assert _hit(_chart("卯", ["武曲"]), "武曲守垣")
    assert not _hit(_chart("辰", ["武曲"]), "武曲守垣")


def test_junchen_qinghui_ziwei_zuoyou():
    """君臣庆会：紫微与左辅右弼同守命。"""
    assert _hit(_chart("子", ["紫微"], ["左辅", "右弼"]), "君臣庆会")
    assert not _hit(_chart("子", ["紫微"], ["左辅"]), "君臣庆会")


def test_fubi_gongzhu_ziwei_flanked_or_sanfang():
    """辅弼拱主：紫微守命，左辅右弼来拱（三方四正）或夹（前后邻宫）。"""
    # 拱：左辅在财帛、右弼在官禄
    assert _hit(_chart("子", ["紫微"], extra={"财帛": ("申", ["左辅"], []),
                                             "官禄": ("辰", ["右弼"], [])}), "辅弼拱主")
    # 夹：左辅右弼分居命宫前后邻宫（子之邻为丑、亥）
    assert _hit(_chart("子", ["紫微"], extra={"A": ("丑", ["左辅"], []),
                                             "B": ("亥", ["右弼"], [])}), "辅弼拱主")
    # 不成立：非紫微守命
    assert not _hit(_chart("子", ["天机"], extra={"A": ("丑", ["左辅"], []),
                                                 "B": ("亥", ["右弼"], [])}), "辅弼拱主")


def test_caiyin_jialu_lucun_flanked_by_liangxiang():
    """财印夹禄：禄存守命，天梁天相来夹（「入财亦然」一面未并入）。"""
    assert _hit(_chart("子", [], ["禄存"], extra={"A": ("丑", ["天梁"], []),
                                                  "B": ("亥", ["天相"], [])}), "财印夹禄")
    assert not _hit(_chart("子", [], [], extra={"A": ("丑", ["天梁"], []),
                                               "B": ("亥", ["天相"], [])}), "财印夹禄")


def test_jinyu_fujia_ziwei_sun_moon_flank():
    """金舆扶驾：紫微守命，前后有日月来夹。"""
    assert _hit(_chart("子", ["紫微"], extra={"A": ("丑", ["太阳"], []),
                                             "B": ("亥", ["太阴"], [])}), "金舆扶驾")
    assert not _hit(_chart("子", ["天机"], extra={"A": ("丑", ["太阳"], []),
                                                 "B": ("亥", ["太阴"], [])}), "金舆扶驾")


def test_no_pinjian_or_za_ju_judged():
    """口径：贫贱局/杂局不得进判定表（命科不作命运断语）。"""
    names = {c["名"] for c in judge_classical_patterns(_chart("子", ["紫微"]))}
    for bad in ("生不逢时", "禄逢两杀", "马落空亡", "财与囚仇", "一生孤贫",
                "风云际会", "锦上添花", "枯木逢春"):
        assert bad not in names, f"{bad} 属贫贱/杂局，不应判"
