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
    discipline: str
    question: str
    datetime: str
    gender: str
    mode: str
    way: str
    numbers: str
    yao: str
    date: str
    activity: str
    hour_branch: str
    direction: str
    longitude: float
    name: str
    up: int
    mid: int
    down: int
    seed: int


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
