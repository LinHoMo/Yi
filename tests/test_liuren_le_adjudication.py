# -*- coding: utf-8 -*-
"""LE036/LE041 source adjudication（2026-10-04 轮）观察锁定。

只锁三件事，全部只读、零引擎改动：
1. 裁决记录文件的结构与 status 词表（observation-only 声明不被抹掉）；
2. 记录与 course_examples.json 的血缘：source_quote 逐字一致、expected 三传未被改动；
3. 机械证据仍成立：
   a) 引擎现行输出与记录的 engine_result 逐字段一致（引擎若变，观察必须重审）；
   b) 「换门复现」——无视一课之克的前提下，引擎自身昴星/遥克分支逐字复现书面三传
      （本轮裁决的核心依据）；
   c) 五签名例（LE022/032/036/039/041）一课皆有克，且一课不计克时全部转为书面三传；
   d) shared_evidence 通则引文仍是书源语料的逐字子串（引文逐字纪律）。
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from yishu_core.ganzhi_calendar import EARTHLY_BRANCHES

ROOT = Path(__file__).resolve().parents[1]
ADJ_PATH = ROOT / "disciplines/liuren/data/cases/le_adjudication.json"
CASES_PATH = ROOT / "disciplines/liuren/data/cases/course_examples.json"
ALLOWED_STATUS = {
    "source_error_suspected", "source_variant", "engine_rule_gap_suspected",
    "unresolved", "insufficient_information",
}


def _load_module():
    """按文件路径加载大六壬取传模块，避免与 ming/liuyao 的同名 scripts 模块互相遮蔽。"""
    spec = importlib.util.spec_from_file_location(
        "liuren_jiuzongmen_for_adjudication",
        ROOT / "disciplines/liuren/scripts/jiuzongmen.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _tianpan(delta: int) -> dict[str, str]:
    return {g: EARTHLY_BRANCHES[(EARTHLY_BRANCHES.index(g) + delta) % 12]
            for g in EARTHLY_BRANCHES}


def _norm(text: str) -> str:
    return "".join(text.split())


def _setup():
    adj = json.loads(ADJ_PATH.read_text(encoding="utf-8"))
    cases = {c["id"]: c for c in json.loads(
        CASES_PATH.read_text(encoding="utf-8"))["cases"]}
    return adj, cases


def test_structure_and_status_vocabulary():
    adj, _ = _setup()
    assert adj["schema"] == "yi-liuren-course-adjudication/1"
    assert any("OBSERVATION-ONLY" in line for line in adj["_comment"])
    ids = [r["case_id"] for r in adj["records"]]
    assert ids == ["LE036", "LE041"]
    for rec in adj["records"]:
        for field in ("case_id", "source", "source_location", "source_quote",
                      "chart_input", "source_stated_result", "engine_result",
                      "discrepancy", "possible_explanation", "evidence",
                      "adjudication_status", "source_adjudication",
                      "source_variant", "note"):
            assert field in rec, (rec["case_id"], field)
        assert rec["adjudication_status"] in ALLOWED_STATUS


def test_provenance_quote_and_expected_untouched():
    adj, cases = _setup()
    for rec in adj["records"]:
        src = cases[rec["case_id"]]
        assert rec["source_quote"] == src["source_quote"], rec["case_id"]
        assert rec["source_stated_result"]["san_chuan"] == src["expected"]["san_chuan"], \
            (rec["case_id"], "expected 三传不得改动")
        assert rec["chart_input"]["day_ganzhi"] == src["day_ganzhi"]
        assert rec["chart_input"]["delta"] == src["delta"]


def test_engine_replay_matches_record():
    adj, _ = _setup()
    J = _load_module()
    for rec in adj["records"]:
        ci = rec["chart_input"]
        res = J.san_chuan_full(ci["day_ganzhi"][0], ci["day_ganzhi"][1],
                               _tianpan(ci["delta"]))
        er = rec["engine_result"]
        assert (res["men"], res["ke_name"]) == (er["men"], er["ke_name"]), rec["case_id"]
        assert res["san_chuan"] == er["san_chuan"], rec["case_id"]
        assert res["trigger"] == er["trigger"], rec["case_id"]
        assert res["verified"] == er["verified"], rec["case_id"]


def test_alternative_gate_reproduces_book_triple():
    """换门复现：无视一课之克 → 引擎昴星/遥克分支逐字复现书面三传。"""
    adj, _ = _setup()
    J = _load_module()

    # LE036：屏蔽一课之克后，柔日昴星分支给出书面三传申寅申
    rec36 = next(r for r in adj["records"] if r["case_id"] == "LE036")
    tp = _tianpan(rec36["chart_input"]["delta"])
    saved = J._ze_ke_courses

    def _no_course1_ze_ke(courses):
        ze = [c for c in courses[1:] if J._ke(c["xia"], c["shang"])]
        ke = [c for c in courses[1:] if J._ke(c["shang"], c["xia"])]
        return ze, ke

    J._ze_ke_courses = _no_course1_ze_ke
    try:
        res = J.san_chuan_full("癸", "未", tp)
        assert res["men"] == "昴星" and res["san_chuan"] == ["申", "寅", "申"]
    finally:
        J._ze_ke_courses = saved

    # LE041：屏蔽一课之克后，遥克（蒿矢）分支给出书面三传酉巳丑
    rec41 = next(r for r in adj["records"] if r["case_id"] == "LE041")
    tp = _tianpan(rec41["chart_input"]["delta"])
    J._ze_ke_courses = _no_course1_ze_ke
    try:
        res = J.san_chuan_full("乙", "巳", tp)
        assert res["men"] == "遥克" and res["ke_name"] == "蒿矢"
        assert res["san_chuan"] == ["酉", "巳", "丑"]
    finally:
        J._ze_ke_courses = saved


def test_course1_signature_cases():
    """五签名例（LE022/032/036/039/041）：一课皆有克，一课不计克时全部转为书面三传。"""
    J = _load_module()
    _, cases = _setup()
    for cid in ("LE022", "LE032", "LE036", "LE039", "LE041"):
        src = cases[cid]
        stem, branch = src["day_ganzhi"][0], src["day_ganzhi"][1]
        tp = _tianpan(src["delta"])
        courses = J.four_courses(stem, branch, tp)
        ze, ke = J._ze_ke_courses(courses)
        assert (ze or ke) and any(c["pos"] == 1 for c in ze + ke), \
            (cid, "一课应存在克")

        saved = J._ze_ke_courses

        def _no_course1(cs, _ze=J._ke):
            return ([c for c in cs[1:] if _ze(c["xia"], c["shang"])],
                    [c for c in cs[1:] if _ze(c["shang"], c["xia"])])

        J._ze_ke_courses = _no_course1
        try:
            res = J.san_chuan_full(stem, branch, tp)
            assert res["san_chuan"] == src["expected"]["san_chuan"], cid
        finally:
            J._ze_ke_courses = saved


def test_tongze_quotes_are_verbatim_substrings():
    adj, _ = _setup()
    for q in adj["shared_evidence"]["tongze_quotes"]:
        corpus = (ROOT / "data/sources" / q["corpus_file"]).read_text(encoding="utf-8")
        assert _norm(q["quote"]) in _norm(corpus), q["loc"]
        if "quote2" in q:
            assert _norm(q["quote2"]) in _norm(corpus), q["loc"]
