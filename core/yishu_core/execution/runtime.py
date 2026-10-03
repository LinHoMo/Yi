# -*- coding: utf-8 -*-
"""YiRuntime: 统一执行入口。

核心抽象:
  rt = YiRuntime(host="subprocess")   # 本机 / CI
  result = rt.execute(request)         # 返回 RuntimeResult

目标 / 非目标:
  * 目标: 让 CLI / CI / Web / Actions 都进来走同一条流水线, 不再各自拼接 argv。
  * 非目标: 不替代学科内 scripts/。Runtime 只管 discipline routing、request
    normalization、执行宿主适配、provenance 与结果封装。科内算法仍由 scripts/ 决定。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

from yishu_core.report import (
    DISC_TITLE,
    MD_FEEDBACK_NOTE,
    REPORT_FOOTER,
    analyze_argv,
    chart_argv,
    normalize_request,
    render_argv,
    report_meta,
    report_title,
)
from yishu_core.report.html import report_page_from_markdown

from yishu_core import __version__ as _ENGINE_VERSION
from yishu_core.evidence import evidence_envelope, evidence_from_analyze
from yishu_core.execution.registry import evaluation_baseline_of
from yishu_core.execution.schemas import (
    SCHEMA_VERSION,
    AnalysisEnvelope,
    ChartEnvelope,
    RequestEnvelope,
)

CST = timezone(timedelta(hours=8))

Host = Literal["subprocess", "runpy"]


@dataclass
class RuntimeResult:
    """Runtime 执行结果 (exit envelope 的 Python 侧)。"""
    schema_version: str = SCHEMA_VERSION
    engine_version: str = _ENGINE_VERSION
    discipline: str = ""
    title: str = ""
    meta: str = ""
    markdown: str = ""
    html: str = ""
    chart: dict[str, Any] = field(default_factory=dict)
    analysis: dict[str, Any] = field(default_factory=dict)
    evidence: Any = None
    footer: str = REPORT_FOOTER
    feedback_note: str = MD_FEEDBACK_NOTE
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_envelope(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_version": self.engine_version,
            "discipline": self.discipline,
            "title": self.title,
            "meta": self.meta,
            "markdown": self.markdown,
            "html": self.html,
            "chart": self.chart,
            "analysis": self.analysis,
            "evidence": self.evidence,
            "footer": self.footer,
            "feedback_note": self.feedback_note,
            "provenance": self.provenance,
        }


class YiRuntime:
    """Yi 引擎统一执行入口。

    使用方法:
        rt = YiRuntime("/path/to/Yi/root")
        result = rt.execute({"discipline": "liuyao", "question": "..."})
        print(result.markdown)
    """

    def __init__(self, root: str | Path, *, host: Host = "subprocess",
                 runtime_label: str = "") -> None:
        self.root = Path(root).resolve()
        self.core = self.root / "core"
        self.disciplines = self.root / "disciplines"
        self.host: Host = host
        self.runtime_label = runtime_label or (
            "本机/CI 子进程" if host == "subprocess" else "浏览器内 Pyodide"
        )

        # 确保内核 import 路径
        core_str = str(self.core)
        if core_str not in sys.path:
            sys.path.insert(0, core_str)

    # ── 公开 API ───────────────────────────────────────────────────────────

    def execute(self, request: dict[str, Any]) -> RuntimeResult:
        """端到端执行: chart → analyze → render → provenance。"""
        req = normalize_request(request)
        d = req["discipline"]

        title = report_title(req)
        meta = report_meta(req, runtime=self.runtime_label)

        with tempfile.TemporaryDirectory(prefix="yi_runtime_") as tmp:
            tmp_p = Path(tmp)
            stem = req.get("name") or f"{d}-{datetime.now(CST).strftime('%Y%m%d%H%M%S')}"
            chart_p = tmp_p / f"{stem}.chart.json"
            analyze_p = tmp_p / f"{stem}.analyze.json"
            md_p = tmp_p / f"{stem}.md"

            scripts = self.disciplines / d / "scripts"

            # chart 段
            self._run([sys.executable, *chart_argv(req, str(scripts / "chart.py"), str(chart_p))])
            chart_data = json.loads(chart_p.read_text(encoding="utf-8"))

            # analyze 段
            self._run([sys.executable, *analyze_argv(req, str(scripts / "analyze.py"), str(chart_p), str(analyze_p))])
            analysis_data = json.loads(analyze_p.read_text(encoding="utf-8"))

            # render 段 (markdown)
            self._run([sys.executable, *render_argv(req, str(scripts / "render.py"), str(analyze_p), str(md_p))])
            markdown = md_p.read_text(encoding="utf-8") + MD_FEEDBACK_NOTE

        # 统一 HTML (在 tmp 之外, 不依赖文件系统)
        html = report_page_from_markdown(markdown=markdown, title=title, meta=meta, footer=REPORT_FOOTER)

        # 结构化证据（Evidence Contract 派生视图，不改动 analyze 输出本身）
        baseline = evaluation_baseline_of(d)
        evidence = evidence_envelope(
            d, evidence_from_analyze(d, analysis_data, evaluation_baseline=baseline),
            evaluation_baseline=baseline)

        return RuntimeResult(
            schema_version=SCHEMA_VERSION,
            engine_version=_ENGINE_VERSION,
            discipline=d,
            title=title,
            meta=meta,
            markdown=markdown,
            html=html,
            chart=chart_data,
            analysis=analysis_data,
            evidence=evidence,
            footer=REPORT_FOOTER,
            feedback_note=MD_FEEDBACK_NOTE,
            provenance={
                "host": self.host,
                "runtime_label": self.runtime_label,
                "executed_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M"),
            },
        )

    # ── 分步执行 (便于单步调试 / 复用) ───────────────────────────────────────

    def chart(self, request: dict[str, Any]) -> dict[str, Any]:
        req = normalize_request(request)
        with tempfile.TemporaryDirectory(prefix="yi_runtime_chart_") as tmp:
            chart_p = Path(tmp) / "chart.json"
            scripts = self.disciplines / req["discipline"] / "scripts"
            self._run([sys.executable, *chart_argv(req, str(scripts / "chart.py"), str(chart_p))])
            return json.loads(chart_p.read_text(encoding="utf-8"))

    def analyze(self, request: dict[str, Any]) -> dict[str, Any]:
        req = normalize_request(request)
        with tempfile.TemporaryDirectory(prefix="yi_runtime_analyze_") as tmp:
            tmp_p = Path(tmp)
            chart_p = tmp_p / "chart.json"
            analyze_p = tmp_p / "analyze.json"
            scripts = self.disciplines / req["discipline"] / "scripts"
            self._run([sys.executable, *chart_argv(req, str(scripts / "chart.py"), str(chart_p))])
            self._run([sys.executable, *analyze_argv(req, str(scripts / "analyze.py"), str(chart_p), str(analyze_p))])
            return json.loads(analyze_p.read_text(encoding="utf-8"))

    # ── 宿主适配 ──────────────────────────────────────────────────────────────

    def _run(self, argv: list[str]) -> None:
        """跑子进程, 失败即抛错。"""
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=self._env(),
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"命令失败 (exit {proc.returncode}): {' '.join(argv)}\n"
                f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
            )

    def _env(self) -> dict:
        import os
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        return env
