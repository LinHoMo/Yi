# -*- coding: utf-8 -*-
"""日主之根宫位分层（2026-10-04d source adjudication → 通用规则落地）锁定。

锁三件事：
1. provenance——衰旺章关键引文仍是语料的逐字子串（防凭印象改根权重口径）；
2. 机械映射——长生/临官/帝旺＝重根 1.0、墓/余气库支＝轻根 0.25，只作用于
   木火金水日主之比劫根；戊己（土寄四隅流派不一）维持藏干层位权重；
3. 外集隔离——根权重宫位分层与外部独立集无反馈回路：ZE005 改后仍为「中和」。
   （原断言含 ZE017；2026-10-04l 三支全会聚轴落地后 ZE017 依书源口径翻为
   「偏旺」，口径变更已登记 CHANGELOG 2026-10-04l，tripwire 相应改锁新读数
   与 ju_bonus 血缘，防静默回退。）

 ming 的 chart/pattern 与他科 scripts/ 同名（conftest sys.path 顺序有约定），
 故按文件路径 importlib 加载，不向 sys.path 插入学科目录（照
 test_liuren_le_adjudication.py 范式）。
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ming_chart = _load("ming_chart_root_stage", "disciplines/ming/scripts/chart.py")
ming_pattern = _load("ming_pattern_root_stage", "disciplines/ming/scripts/pattern.py")

CORPUS = ROOT / "data" / "sources" / "di-tian-sui-chan-wei.wikitext.txt"
# 外集隔离锁例：ZE005（无三支全会聚，机制未建模须仍中和）；ZE017 的读数锁定
# 移入 test_external_set_isolation_tripwire（2026-10-04l 会聚轴落地后翻偏旺）
EXT_ZE = ("ZE005",)


def _norm(text: str) -> str:
    return "".join(text.split())


def _strength(pillars: dict) -> tuple:
    cj = ming_chart.chart_from_pillars(pillars, gender="男")
    r = ming_pattern.strength_and_pattern(cj)
    roots = [(d["pillar"], d["god"], d.get("root_stage", ""), d["w"])
             for d in r["details"] if d["role"] == "比劫"]
    return r["strength"], r["strength_score"], roots


def test_provenance_quotes_verbatim_in_corpus():
    corpus = _norm(CORPUS.read_text(encoding="utf-8"))
    for quote in (
        "长生禄旺，根之重者也",
        "天干得一比肩，不如地支得一余气墓库",
        "得二比肩，不如支中得一长生禄旺",
        # wikisource 转写讹字原样：奶＝根之形讹（通行本作「根之轻者也」；
        # 同段「任癸逢辰」「干多不如根挭」为同类讹字）。语料字符级转存不改，
        # 引文按语料原样锁定，讹字在此登记。
        "墓库余气，奶之轻者也",
    ):
        assert _norm(quote) in corpus, quote


def test_heavy_and_light_root_weights():
    # 甲日：亥＝长生（重根 1.0）；辰中乙＝衰宫库支（轻根 0.25）
    strength, score, roots = _strength(
        {"year": "乙亥", "month": "丁亥", "day": "甲辰", "hour": "庚午"})
    by_branch = {"year": "亥", "month": "亥", "day": "辰", "hour": "午"}
    for pillar, god, stage, w in roots:
        if by_branch[pillar] == "亥":
            assert stage == "长生" and w == ming_pattern.ROOT_HEAVY_W, (pillar, stage, w)
        elif by_branch[pillar] == "辰":
            assert stage == "衰" and w == ming_pattern.ROOT_LIGHT_W, (pillar, stage, w)
    assert strength == "偏旺"

    # 丙日：寅＝长生（重根）；戌＝火墓（轻根）
    _, _, roots = _strength(
        {"year": "甲寅", "month": "丙寅", "day": "丙戌", "hour": "戊子"})
    stages = {stage for _, _, stage, _ in roots}
    assert "长生" in stages and "墓" in stages
    for _, _, stage, w in roots:
        assert (w == ming_pattern.ROOT_HEAVY_W) == (stage in ming_pattern.ROOT_HEAVY_STAGES)


def test_earth_day_master_keeps_layer_weights():
    # 戊日：丑/辰/戌中己戊皆库支，但土不在 ROOT_STAGE_ELEMENTS——
    # 维持藏干层位权重（本气 1.0），无 root_stage 标记
    _, _, roots = _strength(
        {"year": "戊子", "month": "乙丑", "day": "戊辰", "hour": "壬戌"})
    assert roots, "戊日应有比劫根"
    for _, _, stage, w in roots:
        assert stage == "" and w == 1.0, (stage, w)


def test_external_set_isolation_tripwire():
    """外集隔离 tripwire（2026-10-04l 口径变更后更新）。

    ZE017 已随三支全会聚轴（JU_BONUS_W，方局章/神峰书源驱动）翻为「偏旺」——
    该翻转系书源明文驱动的口径变更（CHANGELOG 2026-10-04l），非拿外集调参；
    此处改为锁定其新读数与 ju_bonus 血缘，防未来静默回退。
    ZE005（午月午时两刃，无三支全会聚）不受该轴影响，须仍为「中和」——
    其失配机制（禄刃/天干比劫权重）仍未建模，若翻转须另行登记口径变更。
    """
    cases_path = ROOT / "disciplines" / "ming" / "data" / "cases" / "ming_external_cases.json"
    cases = {c["id"]: c for c in json.loads(
        cases_path.read_text(encoding="utf-8"))["cases"]}
    strength, score, _ = _strength(cases["ZE005"]["pillars"])
    assert strength == "中和", ("ZE005", strength)
    strength, score, _ = _strength(cases["ZE017"]["pillars"])
    assert strength == "偏旺", ("ZE017", strength)
    cj = ming_chart.chart_from_pillars(cases["ZE017"]["pillars"], gender="男")
    r = ming_pattern.strength_and_pattern(cj)
    ju = r["ju_bonus"]
    assert ju["total"] == 2.0 and ju["items"][0]["kind"] == "三会方", ju
    assert ju["items"][0]["provenance"] == "engineering_mapping", ju


def test_golden_request_chart_strength_stable():
    """golden 最小请求盘（1990-05-20 10:30 男，乙木无根）不因本规则漂移——
    render_digest [6b] 的前提保持。"""
    cj = ming_chart.chart(datetime_str="1990-05-20 10:30", gender="男")
    r = ming_pattern.strength_and_pattern(cj)
    assert r["strength"] == "偏弱" and r["strength_score"] == -7.2
