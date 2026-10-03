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


def test_axis_is_month_branch_not_global_max():
    """主轴取月令本气（原文「看了日干，次看了月令」），非全盘最重五行。

    原文：「且如月令中支中所属是火，先看月令中此一火字起，又看年上或火，又看月时上
    或有火，宜将以上各火做一处看，或为病，或非病…故曰：从重者论」——先定主轴五行，
    再聚合该五行，非全盘取最重者为病。
    """
    # 月令申（金），全局最重为土——主轴须取月令金，不取全盘土
    got = bing_yao(_pillars(year="戊戌", month="庚申", day="戊午", hour="己未"))
    assert got["element_counts"]["土"] > got["element_counts"]["金"]
    assert got["axis_element"] == "金"
    assert got["bing"]["主轴"] == "金"
    assert got["bing"]["病"] == "金重伐身"
    assert got["bing"]["药"] == "火"


def test_bing_without_medicine_reports_absent():
    """病在而无药：如实报「局中未见」，不得改口径掩盖（原文明言无药即病重）。

    亦锁「从重者论」口径：地支藏干（未/丑/申/戌 皆藏土或金）不计入
    ——原文明写「地支虽又藏有别物，且不必看…若再看别物，由混杂不明」。
    """
    # 月令酉（金）为主轴，药为火；四柱无火
    got = bing_yao(_pillars(year="乙酉", month="己酉", day="乙丑", hour="乙卯"))
    b = got["bing"]
    assert got["axis_element"] == "金"
    assert b["药"] == "火"
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

# ── provenance 与案例集纪律（评审 2026-10-03 要求）──────────────────────

def test_provenance_distinguishes_exact_vs_generalization():
    """规则性质须逐条可辨：原文逐字 vs 据通例推得，不得混同评。"""
    got = bing_yao(_pillars(year="辛酉", month="丁酉", day="癸卯", hour="壬戌"))
    prov = got["provenance"]
    assert prov["五行层"] in ("source_backed_exact", "source_informed_generalization")
    assert "generalization 项只作通则回归" in prov["口径"]

    # 土厚埋金是原文明写的逐字例，其余四行属通例推得
    from pattern import BING_RULES_BY_KE
    assert BING_RULES_BY_KE["土"][2] == "source_backed_exact"
    for elem in ("木", "金", "火", "水"):
        assert BING_RULES_BY_KE[elem][2] == "source_informed_generalization"


def test_classical_cases_are_provenance_honest():
    """古籍案例集：逐字取自书源、只收书源明写者、split 恒为 external_holdout。"""
    import json
    p = (ROOT / "disciplines" / "ming" / "data" / "cases" / "ming_bing_yao_cases.json")
    d = json.loads(p.read_text(encoding="utf-8"))
    assert d["schema"] == "yi-ming-bingyao-cases/1"
    for cid in d["splits"]["external_holdout"]:
        case = next(c for c in d["cases"] if c["id"] == cid)
        assert case["split"] == "external_holdout", f"{cid}：须恒为 external_holdout"
        assert case["source_quote"], f"{cid}：缺书源逐字引文"
        assert "《神峰通考》" in d["_provenance"]["book"]
        # expected 只收书源明写；书中未载者必须是显式 null（禁止本仓推断填值）
        by = case["expected"]["bing_yao"]
        assert by["病神"] and by["机理"], f"{cid}：病神/机理须为书源明写"
        assert "去病之神" in by


def test_classical_cases_expose_known_layer_divergence():
    """锁定已知口径分歧：书源命例取病在藏干，引擎判病在月令主轴。

    该分歧是**已登记的实现理解偏差**（TECH-DEBT §2.7），不是待修 bug——
    本测试的作用是让分歧可见并可回归，防止有人悄悄改判据去凑案例。
    """
    import json
    p = (ROOT / "disciplines" / "ming" / "data" / "cases" / "ming_bing_yao_cases.json")
    d = json.loads(p.read_text(encoding="utf-8"))
    for case in d["cases"]:
        pillars = {k: {"ganzhi": v, "stem": v[0], "branch": v[1]}
                   for k, v in case["pillars"].items()}
        got = bing_yao({"pillars": pillars})
        book_bing = case["expected"]["bing_yao"]["病神"]
        engine_bing = got["bing"]["病之五行"]
        # 已知分歧：书源病神为藏干字（如「卯中乙木」），引擎为五行（如「木/金」）
        assert "中" in book_bing, f"{case['id']}：书源病神应为藏干表述"
        assert engine_bing in "木火土金水", f"{case['id']}：引擎病神应为五行"


def test_observation_set_is_not_benchmark():
    """观察集纪律：不得被当成评测集（不计分、不入 holdout、不调参）。

    2026-10-03e source adjudication 产出。schema 刻意与评测集 cases 区分。
    """
    import json
    obs = json.loads((ROOT / "disciplines" / "ming" / "data" / "cases"
                      / "ming_bing_yao_observations.json").read_text(encoding="utf-8"))
    assert obs["schema"] == "yi-ming-bingyao-observations/1"
    note = obs["_discipline_note"]
    assert note["engine_frozen"] is True
    assert note["score_policy"].startswith("禁止计算 alignment score")
    assert note["holdout_policy"].startswith("禁止入 holdout")
    n = 0
    for o in obs["observations"]:
        assert o["source_quote"], f"{o['id']}：缺书源逐字引文"
        assert "engine_output" in o and "difference" in o, f"{o['id']}：缺差异记录"
        assert o["source_layer"], f"{o['id']}：缺病药层级判定"
        n += 1
    assert n >= 5, f"观察集仅 {n} 例，不足以支撑任何层级结论"


def test_observation_census_matches_the_ruling():
    """§2.7 裁决的机械锁定：观察集统计必须与裁决结论一致。

    若哪天engine 真的与书源同向（或书源出现「月令五行本身为病」的例），本测试会失败
    并提醒同步更新裁决文本——防裁决与代码脱节。
    """
    import json
    obs = json.loads((ROOT / "disciplines" / "ming" / "data" / "cases"
                      / "ming_bing_yao_observations.json").read_text(encoding="utf-8"))
    c = obs["layer_census"]
    # 书源病神层级全部为字层，无一例是「月令五行本身为病」
    assert c["source_layer_word_level"] == len(obs["observations"]), \
        "书源病药层级统计与观察集条目数不符"
    # engine 与书源同向者应为 0
    assert c["divergence_direction"]["engine病与书源病同五行"] == 0, \
        "若 engine 已与书源同向，TECH-DEBT §2.7 的裁决需同步更新"
    # 方向相反（engine 把书源之药当病）至少 1 例——这是最强的反例证据
    assert c["divergence_direction"]["engine病与书源药同五行"] >= 1, \
        "方向相反的强反例消失，须复核观察集与裁决"
