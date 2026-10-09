# -*- coding: utf-8 -*-
"""命科三会/拱局轴 source adjudication 观察集测试。

锁的是 **provenance 与观察集纪律**（2026-10-04k），不锁引擎现状：
- 引文逐字存在于在库语料（防凭印象补引文）；
- observation-only：不得携带任何评分/expected/权重字段（防悄悄升级为评测集）；
- divergence_cases 引用的外集案例 id 必须真实存在于外集文件且书源类别一致
  （防张冠李戴）；
- engine 现状未变（不写断言锁「必须仍然失配」——未来按 promotion_path
  合法落地时，本测试不需改，改的是 JSON 的 engine_state 快照）。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ADJ_PATH = ROOT / "disciplines" / "ming" / "data" / "cases" / "ming_fangju_adjudication.json"
EXT_PATH = ROOT / "disciplines" / "ming" / "data" / "cases" / "ming_external_cases.json"

CORPORA = {
    "《滴天髓阐微》": ROOT / "data" / "sources" / "di-tian-sui-chan-wei.wikitext.txt",
    "《神峰通考》": ROOT / "data" / "sources" / "shen-feng-tong-kao.wikitext.txt",
}


def _load() -> dict:
    return json.loads(ADJ_PATH.read_text(encoding="utf-8"))


class TestSchema:
    def test_schema_and_status(self) -> None:
        d = _load()
        assert d["schema"] == "yi-ming-fangju-adjudication/1"
        assert d["discipline"] == "ming"
        assert d["status"] == "observation_only"
        assert d["question"] and d["verdict"]

    def test_observation_only_no_scoring_fields(self) -> None:
        """观察集纪律：不得携带评测字段（expected/权重/分数）——防悄悄升级为评测集。"""
        raw = ADJ_PATH.read_text(encoding="utf-8")
        for banned in ('"expected"', '"weight"', '"score"', '"hit"'):
            assert banned not in raw, f"观察集不得含评测字段 {banned}"

    def test_promotion_path_requires_counterfactual(self) -> None:
        d = _load()
        blob = json.dumps(d["promotion_path"], ensure_ascii=False)
        assert "反事实" in blob and "tune/holdout" in blob, \
            "升级路径必须写明反事实测量先行（防拿外集读数当落地依据）"


class TestProvenance:
    def test_quotes_verbatim_in_corpus(self) -> None:
        """每条书源引文逐字存在于其声称的语料（防凭印象补引文）。"""
        d = _load()
        corpora = {k: v.read_text(encoding="utf-8") for k, v in CORPORA.items()}
        assert d["source_evidence"], "证据清单不得为空"
        for ev in d["source_evidence"]:
            text = corpora[ev["book"]]
            assert ev["quote"] in text, f"{ev['chapter']} 引文不逐字：{ev['quote'][:30]}…"
            assert isinstance(ev["corpus_line"], int) and ev["corpus_line"] > 0

    def test_divergence_cases_exist_in_external_set(self) -> None:
        """divergence_cases 引用的 ZE id 必须真实在外集且类别一致（防张冠李戴）。"""
        d = _load()
        ext = json.loads(EXT_PATH.read_text(encoding="utf-8"))
        by_id = {c["id"]: c for c in ext["cases"]}
        assert d["divergence_cases"], "分歧案例清单不得为空"
        for dc in d["divergence_cases"]:
            cid = dc["id"]
            assert cid in by_id, f"{cid} 不在外集"
            assert by_id[cid]["expected"]["strength_book_category"] == dc["book_category"], \
                f"{cid} 书源类别与外集登记不一致"

    def test_divergence_cases_are_report_only_references(self) -> None:
        """外集案例只作分歧登记引用，不得在本文件被赋予任何期望输出。"""
        d = _load()
        for dc in d["divergence_cases"]:
            assert set(dc) == {"id", "book_category", "source_axis", "engine_judged"}, \
                f"{dc['id']}：只允许登记字段（id/book_category/source_axis/engine_judged）"

    def test_engine_state_is_dated_snapshot(self) -> None:
        """engine_state 是带日期的时点快照（信息性），不是永久断言。"""
        d = _load()
        st = d["engine_state_at_adjudication"]
        assert re.match(r"\d{4}-\d{2}-\d{2}", st["date"])
        assert "快照" in st["description"] or "信息性" in st["description"]
