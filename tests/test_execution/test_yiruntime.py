# -*- coding: utf-8 -*-
"""YiRuntime 端到端冒烟测试（跑真实引擎, 验证 Runtime 封装不破坏结果）。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT))

from yishu_core.execution import YiRuntime, SCHEMA_VERSION  # noqa: E402


@pytest.fixture
def rt() -> YiRuntime:
    return YiRuntime(str(ROOT))


class TestRuntimeChart:
    def test_liuyao_has_hexagram(self, rt: YiRuntime) -> None:
        chart = rt.chart({"discipline": "liuyao", "question": "test", "mode": "time"})
        assert "hexagram" in chart or "original_hexagram" in chart

    def test_ming_has_pillars(self, rt: YiRuntime) -> None:
        chart = rt.chart({"discipline": "ming", "question": "test",
                          "datetime": "1990-01-01 12:00", "gender": "男"})
        assert "pillars" in chart or "four_pillars" in chart


class TestRuntimeAnalyze:
    def test_liuyao_analyze_produces_verdict(self, rt: YiRuntime) -> None:
        analysis = rt.analyze({"discipline": "liuyao", "question": "test", "mode": "time"})
        # analyze 输出应包含原始 chart 字段
        assert "original_hexagram" in analysis or "hexagram" in analysis


class TestRuntimeExecute:
    def test_full_execute_returns_markdown(self, rt: YiRuntime) -> None:
        result = rt.execute({"discipline": "liuyao", "question": "test", "mode": "time"})
        assert len(result.markdown) > 50
        assert result.schema_version == SCHEMA_VERSION
        assert result.discipline == "liuyao"
        assert "##" in result.markdown  # 有标题

    def test_full_execute_returns_html(self, rt: YiRuntime) -> None:
        result = rt.execute({"discipline": "liuyao", "question": "test", "mode": "time"})
        assert "<!DOCTYPE html>" in result.html or "<html" in result.html

    def test_provenance_populated(self, rt: YiRuntime) -> None:
        result = rt.execute({"discipline": "liuyao", "question": "test", "mode": "time"})
        assert result.provenance["host"] == "subprocess"
        assert "executed_at" in result.provenance


class TestRuntimeMultiDiscipline:
    """验证 Runtime 能路由到不同学科。"""

    @pytest.mark.parametrize("disc,extra", [
        ("liuyao", {"mode": "time"}),
        ("ming", {"datetime": "1990-01-01 12:00", "gender": "男"}),
        ("meihua", {"way": "numbers", "numbers": "1,2,3"}),
    ])
    def test_execute_min_smoke(self, rt: YiRuntime, disc: str, extra: dict) -> None:
        req = {"discipline": disc, "question": "test", **extra}
        result = rt.execute(req)
        assert result.discipline == disc
        assert len(result.markdown) > 20
