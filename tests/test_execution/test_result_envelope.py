# -*- coding: utf-8 -*-
"""Schema 与 ResultEnvelope 的最小测试。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT))

from yishu_core.execution import (  # noqa: E402
    RuntimeResult,
    SCHEMA_VERSION,
    RequestEnvelope,
    ChartEnvelope,
    AnalysisEnvelope,
    ResultEnvelope,
    list_disciplines,
    discipline_capability,
    capability_matrix,
    supports,
)


class TestSchemaVersion:
    def test_schema_version_present(self) -> None:
        assert SCHEMA_VERSION == "1.0.0"

    def test_request_envelope_is_typeddict(self) -> None:
        # TypedDict 在运行时就是 dict，但能静态类型检查
        req: RequestEnvelope = {"discipline": "liuyao", "question": "t"}
        assert req["discipline"] == "liuyao"

    def test_chart_envelope_is_typeddict(self) -> None:
        env: ChartEnvelope = {"discipline": "liuyao", "hexagram": {}}
        assert env["discipline"] == "liuyao"

    def test_analysis_envelope_is_typeddict(self) -> None:
        env: AnalysisEnvelope = {"discipline": "liuyao", "signal_strength": 75}
        assert env["signal_strength"] == 75


class TestRuntimeResult:
    def test_defaults(self) -> None:
        r = RuntimeResult()
        assert r.schema_version == SCHEMA_VERSION
        assert r.engine_version == "0.0.1"
        assert r.discipline == ""

    def test_to_envelope_contains_required_keys(self) -> None:
        r = RuntimeResult(discipline="liuyao", markdown="# hi")
        env = r.to_envelope()
        assert "schema_version" in env
        assert "engine_version" in env
        assert env["discipline"] == "liuyao"
        assert env["markdown"] == "# hi"


class TestDisciplineRegistry:
    def test_list_disciplines_2(self) -> None:
        ds = list_disciplines()
        assert len(ds) == 2
        assert "liuyao" in ds
        assert "ming" in ds

    def test_capability_stable_for_liuyao(self) -> None:
        dc = discipline_capability("liuyao")
        assert dc.chart == "stable"
        assert dc.external_evaluation == "stable"
        assert dc.mcp == "unavailable"

    def test_capability_mcp_unavailable(self) -> None:
        for d in list_disciplines():
            dc = discipline_capability(d)
            assert dc.mcp == "unavailable"

    def test_all_capabilities_2(self) -> None:
        cm = capability_matrix()
        assert len(cm) == 2
        assert all(isinstance(row, dict) for row in cm)

    def test_supports_true(self) -> None:
        assert supports("liuyao", "chart") is True
        assert supports("liuyao", "render") is True

    def test_supports_false_for_unknown_disc(self) -> None:
        assert supports("foobar", "chart") is False

    def test_unknown_discipline_raises(self) -> None:
        with pytest.raises(ValueError):
            discipline_capability("foobar")
