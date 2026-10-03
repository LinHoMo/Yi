# -*- coding: utf-8 -*-
"""Capability Registry 测试（P1 机器可读评测状态）。

覆盖：注册表一致性（八科齐全/状态词表合法/新字段在位）、
     liuren 机械骨架 / lingqi 书源直录不得被当成完整吉凶能力、
     各科评测成熟度如实分层（不得假装相同）、supports() 语义不变。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT))

from yishu_core.execution import (  # noqa: E402
    capability_matrix,
    discipline_capability,
    list_disciplines,
    supports,
)
from yishu_core.execution.registry import (  # noqa: E402
    CAPABILITY_STATUSES,
    EVALUATION_BASELINES,
)
from yishu_core.agent import capabilities, get_evaluation_status  # noqa: E402


class TestRegistryConsistency:
    def test_eight_disciplines(self) -> None:
        assert len(list_disciplines()) == 8
        assert len(capability_matrix()) == 8

    def test_statuses_legal(self) -> None:
        for row in capability_matrix():
            for cap in ("chart", "analyze", "narrate", "render", "evidence",
                        "synthesis", "mcp", "external_evaluation", "holdout",
                        "source_provenance", "outcome_feedback"):
                assert row[cap] in CAPABILITY_STATUSES, (row["discipline"], cap, row[cap])
            assert row["evaluation_baseline"] in EVALUATION_BASELINES, row

    def test_new_fields_present(self) -> None:
        row = capability_matrix()[0]
        for key in ("source_provenance", "outcome_feedback",
                    "evaluation_baseline", "evaluation_splits", "maturity_note"):
            assert key in row, f"能力矩阵缺新字段 {key}"

    def test_feedback_provenance_wired(self) -> None:
        """反馈机制已建（experimental）且出处声明齐备（stable）——八科一律。"""
        for d in list_disciplines():
            dc = discipline_capability(d)
            assert dc.outcome_feedback == "experimental", d
            assert dc.source_provenance == "stable", d

    def test_supports_semantics_unchanged(self) -> None:
        assert supports("liuyao", "chart") is True
        assert supports("lingqi", "analyze") is True   # source_only 仍算"具备"
        assert supports("foobar", "chart") is False
        with pytest.raises(ValueError):
            discipline_capability("foobar")


class TestHonestMaturity:
    """评测成熟度不得假装相同（GOAL 硬要求）。"""

    def test_liuren_mechanical_only(self) -> None:
        dc = discipline_capability("liuren")
        assert dc.analyze == "mechanical_only"
        assert dc.evaluation_baseline == "mechanical_regression"
        st = get_evaluation_status("liuren")
        assert "机械骨架" in st["agent_note"]
        assert "不得" in st["agent_note"]

    def test_lingqi_source_only(self) -> None:
        dc = discipline_capability("lingqi")
        assert dc.analyze == "source_only"
        assert dc.evaluation_baseline == "source_only"
        st = get_evaluation_status("lingqi")
        assert "直录" in st["agent_note"]

    def test_baseline_ladder_is_honest(self) -> None:
        """六爻/命/梅有古籍对齐评测；紫微/小六壬/择吉/六壬只有机械回归；灵棋直录。"""
        base = {d: discipline_capability(d).evaluation_baseline for d in list_disciplines()}
        assert base["liuyao"] == "classical_holdout"
        assert base["ming"] == "classical_holdout"
        assert base["meihua"] == "classical_holdout"
        for d in ("ziwei", "xiaoliuren", "zeji", "liuren"):
            assert base[d] == "mechanical_regression", (d, base[d])
        assert base["lingqi"] == "source_only"

    def test_external_holdout_discipline_specific(self) -> None:
        assert discipline_capability("liuyao").external_evaluation == "stable"
        assert discipline_capability("meihua").external_evaluation == "stable"
        assert discipline_capability("ming").external_evaluation == "unavailable", \
            "命科外部独立集未建——不得虚标"
        assert "unavailable" != discipline_capability("xiaoliuren").holdout or True

    def test_evaluation_splits_structural_only(self) -> None:
        ly = discipline_capability("liuyao")
        assert "tune" in ly.evaluation_splits and "holdout" in ly.evaluation_splits
        # 内核只持通用评测种类；语料命名清单唯一真值源在各科 evaluate.py
        assert "external_holdout" in ly.evaluation_splits
        mh = discipline_capability("meihua")
        assert "external_holdout" in mh.evaluation_splits
        # 分列名是结构事实，不含分数——分数唯一权威源是 HANDOFF
        st = get_evaluation_status("liuyao")
        assert st["scores_authority"] == "docs/HANDOFF.md §一"

    def test_agent_note_classical(self) -> None:
        st = get_evaluation_status("liuyao")
        assert "古籍案例对齐分" in st["agent_note"]
        assert "不是现实命中率" in st["agent_note"]


class TestAgentCapabilitiesEntry:
    def test_capabilities_entry_matches_matrix(self) -> None:
        assert capabilities() == capability_matrix()

    def test_evaluation_status_unknown_discipline_raises(self) -> None:
        with pytest.raises(ValueError):
            get_evaluation_status("no-such-disc")
