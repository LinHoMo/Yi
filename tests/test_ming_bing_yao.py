# -*- coding: utf-8 -*-
"""命科病药结构断言（《神峰通考·病药说类》）。

口径：本测试只验**判据步骤**（从重者论 → 定病 → 定药 → 药在否）是否正确，
不评吉凶——「有病方为贵」是原文命题，落到具体命造须人工复核（`AGENTS.md` 铁律三）。
书源：`data/sources/shen-feng-tong-kao.wikitext.txt`（维基文库《神峰通考》公版）。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "core", ROOT / "disciplines" / "ming" / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from pattern import bing_yao  # noqa: E402


def _pillars(*, ten_gods: dict | None = None, **kw) -> dict:
    """构造 chart 片段（bing_yao 吃的是 chart_json['pillars']）。

    `ten_gods` 给定时按柱名写入 ten_god 字段——十神层病药读透干十神，
    与引擎真实 chart 产物一致（chart.py 负责填，本测试不重算十神）。
    """
    tg = ten_gods or {}
    return {"pillars": {k: {"ganzhi": v, "stem": v[0], "branch": v[1],
                            "ten_god": tg.get(k, "")}
                        for k, v in kw.items()}}


def test_thesis_quote_is_verbatim():
    """病药总纲必须是书源逐字句，不得改写。"""
    assert bing_yao(_pillars(year="甲子", month="丙寅", day="戊辰", hour="庚午"))[
        "thesis"] == "有病方为贵，无伤不是奇；格中如去病，财禄两相随"


def test_dominant_element_as_bing_by_weight():
    """「从重者论」：最重之五行为病；药为其所克之神（原文「以去其病也」）。

    原文举例：「如金日干，则为土厚埋金…是则土为诸格之病，俱喜木为医药」——
    土病药木，故造四柱土重而寅卯木见者应判土病、有药。
    """
    # 戊戌 戊申 己未 甲寅 —— 土五见最重，寅卯木见 → 土病、有木药
    got = bing_yao(_pillars(year="戊戌", month="戊申", day="己未", hour="甲寅"))
    b = got["bing"]
    assert got["dominant_element"] == "土"
    assert b["病"] == "土厚埋金/土重埋身"
    assert b["药"] == "木"
    assert b["药在局中"] is True
    assert got["has_medicine"] is True


def test_bing_without_medicine_reports_absent():
    """病在而无药：如实报「局中未见」，不得改口径掩盖（原文明言无药即病重）。

    亦锁「从重者论」口径：地支藏干（未/丑/申/戌 皆藏土或金）不计入
    ——原文明写「地支虽又藏有别物，且不必看…若再看别物，由混杂不明」。
    """
    got = bing_yao(_pillars(year="戊戌", month="己未", day="戊申", hour="己丑"))
    b = got["bing"]
    assert got["dominant_element"] == "土"
    assert b["药"] == "木"
    assert b["药在局中"] is False
    assert got["has_medicine"] is False


def test_ten_god_layer_pairs():
    """十神层病药对：原文「如用财见比肩为病，喜见官杀为药也」。

    以财为用神：日主甲，年干乙＝劫财、同类夺财之比肩为病；时干辛＝正官为药。
    """
    got = bing_yao(_pillars(ten_gods={"year": "劫财", "month": "偏财", "hour": "正官"},
                            year="乙丑", month="戊寅", day="甲戌", hour="辛未"))
    names = [c["病"] for c in got["consumed_by_bing"]]
    assert "比肩夺财" in names
    pair = next(c for c in got["consumed_by_bing"] if c["病"] == "比肩夺财")
    assert pair["药在局中"] is True
    assert "正官" in pair["所见之药"]


def test_empty_pillars_returns_empty():
    """无有效干支时不臆造病药（宁缺毋滥）。"""
    assert bing_yao({}) == {}
    assert bing_yao({"pillars": {}}) == {}