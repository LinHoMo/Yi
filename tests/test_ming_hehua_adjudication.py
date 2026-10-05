# -*- coding: utf-8 -*-
"""命科天干五合/化气 source adjudication 观察集测试。

锁 **provenance 与观察集纪律**（2026-10-05b），不锁引擎现状：
- 引文逐字存在于在库语料（防凭印象补引文）；
- observation-only：不得携带评分/expected 字段（防悄悄升级为评测集）；
- 升级路径必须写明反事实测量先行（防拿外集读数当落地依据）；
- engine 现状不写断言（未来按 promotion_path 合法落地时只更新 JSON 快照）。
照 test_ming_fangju_adjudication.py 范式。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ADJ_PATH = ROOT / "disciplines" / "ming" / "data" / "cases" / "ming_hehua_adjudication.json"
CORPUS = ROOT / "data" / "sources" / "di-tian-sui-chan-wei.wikitext.txt"


def _load() -> dict:
    return json.loads(ADJ_PATH.read_text(encoding="utf-8"))


class TestSchema:
    def test_schema_and_status(self) -> None:
        d = _load()
        assert d["schema"] == "yi-ming-hehua-adjudication/1"
        assert d["discipline"] == "ming"
        assert d["status"] == "observation_only"
        assert d["question"] and d["verdict"]

    def test_observation_only_no_scoring_fields(self) -> None:
        raw = ADJ_PATH.read_text(encoding="utf-8")
        for banned in ('"expected"', '"weight"', '"score"', '"hit"'):
            assert banned not in raw, f"观察集不得含评测字段 {banned}"

    def test_promotion_path_requires_counterfactual(self) -> None:
        d = _load()
        blob = json.dumps(d["promotion_path"], ensure_ascii=False)
        assert "反事实" in blob and "tune/holdout" in blob


class TestProvenance:
    def test_quotes_verbatim_in_corpus(self) -> None:
        d = _load()
        corpus = CORPUS.read_text(encoding="utf-8")
        assert d["source_evidence"], "证据清单不得为空"
        for ev in d["source_evidence"]:
            assert ev["quote"] in corpus, f"{ev['chapter']} 引文不逐字：{ev['quote'][:30]}…"
            assert isinstance(ev["corpus_line"], int) and ev["corpus_line"] > 0

    def test_engine_state_is_dated_snapshot(self) -> None:
        d = _load()
        st = d["engine_state_at_adjudication"]
        assert st["date"] == "2026-10-05b"
        assert "快照" in st["description"] or "信息性" in st["description"]
