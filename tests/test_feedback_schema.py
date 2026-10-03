# -*- coding: utf-8 -*-
"""Canonical FeedbackRecord 测试（P1 反馈模型统一）。

覆盖：feedback schema（字段校验/词汇锁定）、synthesis 与 liuyao 双 adapter
     往返、真实/合成物理语义分离（混集判败）、yingqi 仍为判定真值源、
     canonical 直入评估（eval_feedback_records）、六爻 store canonical 出口。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT / "synthesis"))
sys.path.insert(0, str(ROOT / "disciplines" / "liuyao" / "dev_tools"))

from yishu_core import feedback as FB  # noqa: E402
from yishu_core.feedback import (  # noqa: E402
    JUDGED,
    KIND_REAL,
    KIND_SYNTHETIC,
    POLICY_RANK,
    POLICY_WINDOW,
    from_liuyao_feedback,
    from_synthesis_divination,
    judge_record,
    synthetic_record,
    validate_feedback_record,
    validate_record_set,
)
from yishu_core import yingqi  # noqa: E402


def _good_record() -> dict:
    return {
        "event_id": "EVT001",
        "discipline": "liuyao",
        "question": "占事",
        "prediction": "吉",
        "predicted_timing": [{"date": "2026-10-05", "rule": "冲空填实"}],
        "observed_outcome": "10-05 收到消息",
        "occurred_at": "2026-10-05",
        "judged": "应验",
        "evaluation_policy": POLICY_RANK,
        "provenance": {"kind": KIND_REAL, "source_system": "synthesis.person"},
    }


class TestSchema:
    def test_good_record_passes(self) -> None:
        assert validate_feedback_record(_good_record()) == []

    def test_judged_vocabulary_locked(self) -> None:
        rec = _good_record()
        rec["judged"] = "很准"  # 口径外词——禁造
        errs = validate_feedback_record(rec)
        assert any("judged" in e for e in errs)

    def test_judged_matches_person_vocabulary(self) -> None:
        """person 档案的 JUDGED 与 canonical 同源（同一对象，非副本）。"""
        from person import JUDGED as PERSON_JUDGED
        assert PERSON_JUDGED is JUDGED

    def test_provenance_kind_required(self) -> None:
        rec = _good_record()
        rec["provenance"] = {"source_system": "synthesis.person"}
        assert any("kind" in e for e in validate_feedback_record(rec))

    def test_policy_vocabulary(self) -> None:
        rec = _good_record()
        rec["evaluation_policy"] = "fuzzy"
        assert any("evaluation_policy" in e for e in validate_feedback_record(rec))

    def test_policy_calibers_come_from_yingqi(self) -> None:
        """口径语句唯一真值源仍是 yishu_core.yingqi（[1i] 纪律的延伸）。"""
        assert FB.POLICY_CALIBERS["rank"] is yingqi.RANK_CALIBER
        assert FB.POLICY_CALIBERS["window"] is yingqi.WINDOW_CALIBER


class TestSynthesisAdapter:
    def test_round_trip(self) -> None:
        div = {
            "event_id": "EVT001", "discipline": "liuyao", "asked": "占事",
            "verdict": "吉",
            "yingqi_offered": [{"date": "2026-10-05", "rule": "冲空填实"},
                               {"date": "2026-10-17", "rule": "出旬"}],
            "outcome": {"recorded": "10-05 收到", "occurred_at": "2026-10-05",
                        "judged": "应验"},
        }
        rec = from_synthesis_divination(div)
        assert validate_feedback_record(rec) == []
        assert rec["event_id"] == "EVT001"
        assert rec["evaluation_policy"] == POLICY_RANK
        assert len(rec["predicted_timing"]) == 2
        assert rec["provenance"]["kind"] == KIND_REAL
        assert rec["provenance"]["source_system"] == "synthesis.person"

    def test_unbackfilled_folds_to_empty_judgement(self) -> None:
        div = {"event_id": "EVT002", "discipline": "liuyao",
               "outcome": {"recorded": None}}
        rec = from_synthesis_divination(div)
        assert rec["judged"] == "" and rec["occurred_at"] == ""
        assert validate_feedback_record(rec) == []

    def test_no_offered_no_policy(self) -> None:
        div = {"event_id": "EVT003", "discipline": "ming",
               "outcome": {"recorded": "无应期概念", "judged": "应验"}}
        rec = from_synthesis_divination(div)
        assert rec["evaluation_policy"] == ""


class TestLiuyaoAdapter:
    def test_store_record_folds(self) -> None:
        rec = from_liuyao_feedback({
            "id": "fb_20261003_ab", "discipline": "liuyao",
            "predicted_dates": ["2026-10-05", "2026-10-17"],
            "predicted_main_yingqi": "2026-10-05",
            "actual_date": "2026-10-05",
            "hit_strict": True, "hit_loose": True,
            "timestamp": "2026-10-03T10:00:00", "chart_id": "abcd1234",
        })
        assert validate_feedback_record(rec) == []
        assert rec["evaluation_policy"] == POLICY_WINDOW
        assert rec["occurred_at"] == "2026-10-05"
        assert rec["provenance"]["source_system"] == "liuyao.feedback_store"
        # 六爻 store 只判应期不断事——不得冒充断事判定
        assert rec["judged"] == ""

    def test_store_round_trip(self, tmp_path) -> None:
        """store 落盘 → canonical 出口往返（存储不变，形态统一）。"""
        from feedback_store import FeedbackStore
        store = FeedbackStore()
        store.dir = tmp_path  # 重定向存储，测试不污染真实反馈目录
        rid = store.save({"predicted_dates": ["2026-10-05"],
                          "actual_date": "2026-10-05"})
        recs = store.load_all_canonical()
        assert len(recs) == 1 and recs[0]["event_id"] == rid
        assert validate_feedback_record(recs[0]) == []


class TestRealVsSyntheticSeparation:
    def test_synthetic_record_marked(self) -> None:
        rec = synthetic_record(event_id="S1", discipline="liuyao",
                               occurred_at="2026-10-05", judged="应验")
        assert rec["provenance"]["kind"] == KIND_SYNTHETIC
        assert validate_feedback_record(rec) == []

    def test_mixed_kinds_rejected(self) -> None:
        errs = validate_record_set([_good_record(),
                                    synthetic_record(event_id="S1", discipline="liuyao")])
        assert any("混入多种" in e for e in errs)

    def test_real_set_passes(self) -> None:
        assert validate_record_set([_good_record()]) == []


class TestJudging:
    def test_rank_policy_routes_to_yingqi_rank(self) -> None:
        rec = _good_record()
        j = judge_record(rec)
        assert j["policy"] == POLICY_RANK
        assert j["judgement"] == yingqi.judge_rank(rec["predicted_timing"], "2026-10-05")
        assert j["judgement"]["名次"] == 1

    def test_window_policy_routes_to_yingqi_window(self) -> None:
        rec = _good_record()
        rec["evaluation_policy"] = POLICY_WINDOW
        j = judge_record(rec)
        assert j["policy"] == POLICY_WINDOW
        assert j["judgement"]["命中"] is True

    def test_no_policy_no_judgement(self) -> None:
        rec = _good_record()
        rec["evaluation_policy"] = ""
        assert judge_record(rec)["judgement"] is None


class TestCanonicalEval:
    def test_eval_feedback_records_summary(self) -> None:
        rec = _good_record()
        res = FB.judge_record(rec)  # smoke: judge path
        assert res["judgement"]["可评"]
        from outcome_eval import eval_feedback_records
        out = eval_feedback_records([rec])
        assert out["n_回填"] == 1 and out["n_应期可评"] == 1 and out["应期命中"] == 1

    def test_mixed_set_raises(self) -> None:
        from outcome_eval import eval_feedback_records
        with pytest.raises(ValueError, match="混入多种|不合规"):
            eval_feedback_records([_good_record(),
                                   synthetic_record(event_id="S1", discipline="liuyao")])

    def test_empty_set(self) -> None:
        from outcome_eval import eval_feedback_records
        assert eval_feedback_records([]) == {"n_回填": 0, "cases": []}

    def test_synthetic_regression_set_evaluates_alone(self) -> None:
        """合成回归数据可以单独成集评估（永不与真实数据混算）。"""
        from outcome_eval import eval_feedback_records
        rec = synthetic_record(event_id="SYN1", discipline="liuyao",
                               predicted_timing=[{"date": "2026-10-05", "rule": "r"}],
                               occurred_at="2026-10-05",
                               evaluation_policy=POLICY_RANK)
        out = eval_feedback_records([rec])
        assert out["n_应期可评"] == 1 and out["应期命中"] == 1


class TestOutcomeEvalCompat:
    """旧入口行为不变（[1i] 门与既有自检依赖的形状）。"""

    def test_eval_outcomes_unchanged_shape(self) -> None:
        from outcome_eval import eval_outcomes
        div = {"event_id": "FBCHK", "discipline": "liuyao", "direction": "吉",
               "asked": "口径门假例",
               "yingqi_offered": [{"date": "2026-10-01", "rule": "r0"},
                                  {"date": "2026-10-30", "rule": "r1"}],
               "outcome": {"recorded": "假例", "occurred_at": "2026-10-01",
                           "judged": "应验"}}
        res = eval_outcomes([div])
        assert res["n_回填"] == 1 and res["n_应期可评"] == 1
        yq = res["cases"][0]["应期"]
        assert yq["命中"] and yq["名次"] == 1
        assert yq["得分"] == yingqi.RANK_SCORE[1]

    def test_unbackfilled_skipped(self) -> None:
        from outcome_eval import eval_outcomes
        div = {"event_id": "E1", "discipline": "liuyao",
               "outcome": {"recorded": None}}
        assert eval_outcomes([div]) == {"n_回填": 0, "cases": []}
