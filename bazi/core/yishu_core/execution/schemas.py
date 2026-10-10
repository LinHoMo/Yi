# -*- coding: utf-8 -*-
"""Runtime 数据契约：以 TypedDict 约束接口形状,替代裸 Dict[str, Any]。

纪律:
  * schema_version 随字段加减而递增;旧版字段保留为 deprecated,不删。
  * 这是**最小稳定** schema——只约束 Runtime 入口 / 出口,
    不规定学科内部结构科内 JSON 不在本文件约束范围内。
  * 字段描述中文:面向人读;键名英文:面向 machine 对齐与序列化。

新增 / 修改字段时同步更新 `SCHEMA_VERSION`,并在 CHANGELOG 注明。
"""
from __future__ import annotations

from typing import Any, TypedDict

# Schema 版本
SCHEMA_VERSION = "1.0.0"


class _SchemaVersion(TypedDict):
    schema_version: str
    engine_version: str


# RequestEnvelope -----------------------------------------------------------

class RequestEnvelope(TypedDict, total=False):
    """请求的 TypedDict 视图。

    ⚠️ 字段宇宙的**唯一真值源是 `yishu_core.report.request.FIELD_USAGE`**（每键声明
    `argv`/`display` 消费方式）。本类只是给执行层的静态视图，**不得自立字段**：
    2026-10-09 两科收缩后这里还留着 `way`/`date`/`activity`/`hour_branch`/`direction`/
    `up`/`mid`/`down` 八个已删科字段，而 `tests/test_execution/test_result_envelope.py`
    有一条键集恒等断言把八科旧集合写死——类型声明与协议同时存在两份就会再次漂移
    （参见 `request.py` 模块头对「静默忽略」的禁令）。
    """

    discipline: str
    question: str
    datetime: str
    gender: str
    mode: str
    numbers: str
    yao: str
    longitude: float
    name: str
    seed: int
    hour: int
    distinguish_zi_hour: bool
    zi_hour_type: str


# ChartEnvelope -------------------------------------------------------------

class ChartEnvelope(TypedDict, total=False):
    discipline: str
    hexagram: Any
    solar_terms: Any
    pillars: Any
    palace: Any


# AnalysisEnvelope ----------------------------------------------------------

class AnalysisEnvelope(TypedDict, total=False):
    discipline: str
    verdict: str
    signal_strength: int
    factors: list[Any]
    thinking_chain: Any
    advanced_analysis: Any


# EvidenceEnvelope ---------------------------------------------------------

class EvidenceEnvelope(TypedDict, total=False):
    discipline: str
    signals: list[Any]
    basis: list[Any]


# ResultEnvelope ------------------------------------------------------------

class ResultEnvelope(TypedDict, total=False):
    schema_version: str
    engine_version: str
    discipline: str
    title: str
    meta: str
    markdown: str
    html: str
    chart: ChartEnvelope
    analysis: AnalysisEnvelope
    evidence: Any
    footer: str
    feedback_note: str
    provenance: dict[str, Any]
