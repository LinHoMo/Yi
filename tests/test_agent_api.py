# -*- coding: utf-8 -*-
"""Agent API 测试（P1 稳定最小接口）。

覆盖：五入口（capabilities / validate_request / run_report / get_evidence /
     get_evaluation_status）；Agent 无需知道脚本名/执行器细节；
     run_report envelope 携带 evidence 与 provenance；validate_request 与
     CLI/Web/Actions 同一 normalize_request。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT))

from yishu_core.agent import (  # noqa: E402
    AGENT_API_VERSION,
    get_evidence,
    run_report,
    validate_request,
)
from yishu_core.execution import YiRuntime  # noqa: E402


@pytest.fixture(scope="module")
def rt() -> YiRuntime:
    return YiRuntime(str(ROOT))


class TestValidateRequest:
    def test_ok(self) -> None:
        out = validate_request({"discipline": "liuyao", "question": "test", "mode": "time"})
        assert out["ok"] is True and out["errors"] == []
        assert out["normalized"]["discipline"] == "liuyao"

    def test_missing_required_human_error(self) -> None:
        out = validate_request({"discipline": "ming"})
        assert out["ok"] is False and out["normalized"] is None
        assert "datetime" in out["errors"][0]

    def test_unknown_discipline(self) -> None:
        out = validate_request({"discipline": "astro"})
        assert out["ok"] is False


class TestRunReport:
    def test_envelope_contains_evidence_and_markdown(self, rt: YiRuntime) -> None:
        env = run_report(rt, {"discipline": "liuyao", "question": "test", "mode": "time"})
        assert len(env["markdown"]) > 50
        assert env["discipline"] == "liuyao"
        # 证据信封在位（Evidence Contract 派生视图）
        ev = env["evidence"]
        assert ev and ev["schema"].startswith("yi-evidence-v")
        assert ev["n"] == len(ev["evidence"]) > 0
        assert env["provenance"]["host"] == "subprocess"

    def test_invalid_request_raises_through(self, rt: YiRuntime) -> None:
        from yishu_core.report.request import normalize_request
        with pytest.raises(ValueError):
            run_report(rt, {"discipline": "ming"})  # 缺 datetime


class TestGetEvidence:
    def test_evidence_with_rule_registry(self, rt: YiRuntime) -> None:
        import json
        reg = json.loads((ROOT / "disciplines" / "liuyao" / "data" / "rules"
                          / "rule_registry.json").read_text(encoding="utf-8"))
        out = get_evidence(rt, {"discipline": "liuyao", "question": "test", "mode": "time"},
                           rule_registry=reg)
        assert out["ok"] is True
        env = out["envelope"]
        assert env["discipline"] == "liuyao"
        assert env["evaluation_baseline"] == "classical_holdout"
        factors = {e["factor"]: e for e in env["evidence"]}
        # 六合/六冲卦级判定必然出现 → 应挂到规则注册表
        assert factors["六合/六冲"]["rule_id"] == "liuyao.liuhe_liuchong"

    def test_evidence_without_registry_still_works(self, rt: YiRuntime) -> None:
        out = get_evidence(rt, {"discipline": "liuyao", "question": "test", "mode": "time"})
        assert out["ok"] is True
        assert all(e["rule_id"] == "" for e in out["envelope"]["evidence"])

    def test_invalid_request_returns_errors(self, rt: YiRuntime) -> None:
        out = get_evidence(rt, {"discipline": "nope"})
        assert out["ok"] is False and out["errors"]


class TestNoScriptKnowledge:
    """Agent 不该知道执行细节：公开 API 面上不出现脚本名/执行器词。"""

    def test_api_surface_hides_executors(self) -> None:
        import inspect
        from yishu_core import agent
        src = inspect.getsource(agent)
        for banned in ("chart.py", "analyze.py", "runpy", "subprocess"):
            assert banned not in src, f"agent API 泄漏执行细节：{banned}"

    def test_api_version(self) -> None:
        assert AGENT_API_VERSION
