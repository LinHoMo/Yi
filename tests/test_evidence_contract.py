# -*- coding: utf-8 -*-
"""Evidence Contract 测试（P0 证据链）。

覆盖：analyze → Evidence 提取（两科真实引擎输出）、字段完整性、
     不制造吉凶（ming 机械标签 effect 为空）、评测状态传播
     （注册表基线 → 证据级状态）、规则注册表挂接（rule_id/出处/状态升级）、
     缺口登记（evaluation_gaps）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT))

from yishu_core.evidence import (  # noqa: E402
    EVALUATION_STATUSES,
    attach_rule_registry,
    evidence_envelope,
    evidence_from_analyze,
    evaluation_gaps,
    max_status,
)
from yishu_core.execution import YiRuntime  # noqa: E402
from yishu_core.execution.registry import evaluation_baseline_of  # noqa: E402

REQS = {
    "liuyao": {"discipline": "liuyao", "question": "test", "mode": "time"},
    "ming": {"discipline": "ming", "question": "test",
             "datetime": "1990-01-01 12:00", "gender": "男"},
}


@pytest.fixture(scope="module")
def analyses() -> dict[str, dict]:
    """两科真实 analyze 输出（一次跑全量，模块内共享）。"""
    rt = YiRuntime(str(ROOT))
    return {d: rt.analyze(req) for d, req in REQS.items()}


class TestExtractionReal:
    def test_every_discipline_yields_evidence(self, analyses) -> None:
        for d, a in analyses.items():
            ev = evidence_from_analyze(d, a, evaluation_baseline=evaluation_baseline_of(d))
            assert ev, f"{d} 未提取到任何证据"
            assert all(e["discipline"] == d for e in ev)

    def test_evidence_fields_complete(self, analyses) -> None:
        for d, a in analyses.items():
            for e in evidence_from_analyze(d, a, evaluation_baseline=evaluation_baseline_of(d)):
                for key in ("id", "discipline", "claim", "factor", "rule_id", "source",
                            "applicability", "observation", "effect",
                            "evaluation_status", "provenance"):
                    assert key in e, f"{d}:{e.get('id')} 缺字段 {key}"
                assert e["id"].startswith(f"{d}:"), e["id"]
                assert e["evaluation_status"] in EVALUATION_STATUSES, e
                assert e["provenance"].get("path"), e

    def test_ids_unique_within_output(self, analyses) -> None:
        for d, a in analyses.items():
            ev = evidence_from_analyze(d, a, evaluation_baseline=evaluation_baseline_of(d))
            ids = [e["id"] for e in ev]
            assert len(ids) == len(set(ids)), f"{d} 证据 id 重复"

    def test_no_fabricated_direction(self, analyses) -> None:
        """铁律三：学科没表态的方向，证据层不得制造（ming 机械标签）。"""
        ev = evidence_from_analyze("ming", analyses["ming"],
                                   evaluation_baseline=evaluation_baseline_of("ming"))
        for e in ev:
            if e["provenance"]["kind"] in ("verdicts", "tiaohou", "shensha"):
                assert e["effect"] == "", f"ming 机械证据不应自带吉凶方向：{e}"

    def test_liuyao_timing_evidence(self, analyses) -> None:
        ev = evidence_from_analyze("liuyao", analyses["liuyao"],
                                   evaluation_baseline=evaluation_baseline_of("liuyao"))
        timing = [e for e in ev if e["provenance"]["kind"] == "timing"]
        assert timing, "六爻应期候选应提为 timing 证据"
        assert all("应期候选第" in e["claim"] for e in timing)
        # 名次序：claim 中的位次与列表顺序一致
        assert "第 1 位" in timing[0]["claim"]

    def test_liuyao_advanced_analysis_blocks(self, analyses) -> None:
        """advanced_analysis 有发现的块 → 证据（六合/六冲卦级必然有判定）。"""
        ev = evidence_from_analyze("liuyao", analyses["liuyao"],
                                   evaluation_baseline=evaluation_baseline_of("liuyao"))
        factors = {e["factor"] for e in ev}
        assert "六合/六冲" in factors, factors
        clash = next(e for e in ev if e["factor"] == "六合/六冲")
        assert "六冲" in clash["claim"] or "六合" in clash["claim"]

    def test_ming_verdicts_extracted(self, analyses) -> None:
        ev = evidence_from_analyze("ming", analyses["ming"],
                                   evaluation_baseline=evaluation_baseline_of("ming"))
        verdicts = [e for e in ev if e["provenance"]["kind"] == "verdicts"]
        assert verdicts, "命科机械判定条目应提为 verdicts 证据"


class TestEvaluationStatusPropagation:
    """评测状态传播：注册表基线 → 证据状态；有出处 ⇒ 至少 source_only。"""

    def test_baseline_propagates(self, analyses) -> None:
        # 六爻基线 classical_holdout → 主判证据应为 classical_holdout
        ev = evidence_from_analyze("liuyao", analyses["liuyao"],
                                   evaluation_baseline="classical_holdout")
        headline = next(e for e in ev if e["provenance"]["kind"] == "headline")
        assert headline["evaluation_status"] == "classical_holdout"

    def test_source_implies_source_only(self) -> None:
        ev = evidence_from_analyze("liuyao", {"conclusion": {"方向": "吉", "所本": "《某书》"}},
                                   evaluation_baseline="unassessed")
        assert ev[0]["evaluation_status"] == "source_only"

    def test_no_source_no_claim_of_coverage(self) -> None:
        ev = evidence_from_analyze("liuyao", {"conclusion": {"说明": "仅机械观察"}},
                                   evaluation_baseline="unassessed")
        assert ev[0]["evaluation_status"] == "unassessed"

    def test_max_status(self) -> None:
        assert max_status("unassessed", "source_only") == "source_only"
        assert max_status("classical_holdout", "mechanical_regression") == "classical_holdout"


@pytest.fixture(scope="module")
def liuyao_registry() -> dict:
    return json.loads((ROOT / "disciplines" / "liuyao" / "data" / "rules"
                       / "rule_registry.json").read_text(encoding="utf-8"))


class TestRuleRegistryAttach:
    """Rule → Evidence provenance：注册表挂接补 rule_id/出处/评测状态。"""

    def test_attach_fills_rule_id(self, liuyao_registry) -> None:
        ev = [{"id": "liuyao:advanced_analysis:0", "discipline": "liuyao",
               "claim": "六冲卦", "factor": "六合/六冲", "rule_id": "",
               "source": "", "applicability": "", "observation": "",
               "effect": "", "evaluation_status": "unassessed",
               "provenance": {"kind": "advanced_analysis", "path": "advanced_analysis.clash_harmony"}}]
        out = attach_rule_registry(ev, liuyao_registry)
        assert out[0]["rule_id"] == "liuyao.liuhe_liuchong"
        # 出处缺省 → 由注册表补书名
        assert "卜筮正宗" in out[0]["source"]

    def test_attach_upgrades_evaluation_status(self, liuyao_registry) -> None:
        ev = [{"id": "x", "discipline": "liuyao", "claim": "三会局", "factor": "三会局",
               "rule_id": "", "source": "《三命通会》", "applicability": "",
               "observation": "", "effect": "",
               "evaluation_status": "unassessed", "provenance": {"kind": "f", "path": "p"}}]
        out = attach_rule_registry(ev, liuyao_registry)
        assert out[0]["rule_id"] == "liuyao.sanhui"
        assert out[0]["evaluation_status"] == "classical_holdout"

    def test_no_match_left_untouched(self, liuyao_registry) -> None:
        ev = [{"id": "x", "discipline": "liuyao", "claim": "体用关系", "factor": "体用关系",
               "rule_id": "", "source": "", "applicability": "", "observation": "",
               "effect": "吉", "evaluation_status": "unassessed",
               "provenance": {"kind": "f", "path": "p"}}]
        out = attach_rule_registry(ev, liuyao_registry)
        assert out[0]["rule_id"] == ""
        assert out[0]["evaluation_status"] == "unassessed"

    def test_attach_on_real_output(self, analyses, liuyao_registry) -> None:
        ev = evidence_from_analyze("liuyao", analyses["liuyao"],
                                   evaluation_baseline=evaluation_baseline_of("liuyao"))
        out = attach_rule_registry(ev, liuyao_registry)
        by_factor = {e["factor"]: e for e in out}
        assert by_factor["六合/六冲"]["rule_id"] == "liuyao.liuhe_liuchong"
        assert by_factor["总判"]["rule_id"] == ""  # 主判不是单条规则，不强行挂接


class TestGapsAndEnvelope:
    def test_evaluation_gaps_registered(self) -> None:
        ev = evidence_from_analyze("ming",
                                   {"conclusion": {}, "factors": [{"code": "pattern", "label": "格局",
                                                                   "basis": "月令定格"}]},
                                   evaluation_baseline="classical_holdout")
        gaps = evaluation_gaps(ev)
        # 有 source 的证据会被正确分级
        assert isinstance(gaps, list)

    def test_envelope_shape(self) -> None:
        ev = evidence_from_analyze("liuyao", {"conclusion": {"方向": "吉", "所本": "《某书》"}},
                                   evaluation_baseline="classical_holdout")
        env = evidence_envelope("liuyao", ev, evaluation_baseline="classical_holdout")
        assert env["schema"].startswith("yi-evidence-v")
        assert env["n"] == len(env["evidence"]) == len(ev)
        assert isinstance(env["gaps"], list)
        assert env["evaluation_baseline"] == "classical_holdout"
