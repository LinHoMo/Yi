# -*- coding: utf-8 -*-
"""Agent API —— 面向任务 Agent 的**稳定最小接口**（P1 Agent-Native 收敛）。

设计边界（与 AGENTS.md 铁律一致）：
  * 只做**稳定最小**五入口，不造巨型框架；MCP / HTTP / CLI 都可以成为它的 adapter。
  * Agent 不应该知道：某科具体用了哪个脚本文件、四段契约在哪块拼装、
    宿主用什么机制执行子步骤——这些全部由 YiRuntime 与注册表承载。
  * 机械推演归引擎：本模块**不做任何术数推断**，只做能力查询、请求校验、
    执行编排、证据读取与评测状态读取的转发。

五入口：
  capabilities()             八字·六爻两科 × 能力 × 评测状态（机器可读，注册表唯一真值源）
  validate_request(request)  请求预检：合法 → normalized request；非法 → 人话错误
  run_report(rt, request)    端到端报告（四段契约），envelope 含 markdown/html/evidence
  get_evidence(rt, request)  一次占问的结构化证据（Evidence Contract 派生视图）
  get_evaluation_status(d)   单科评测覆盖状态（哪类评测存在；分数读数指向 HANDOFF）

用法（Agent 侧唯一需要的两行）：
    from yishu_core.agent import capabilities, validate_request, run_report, ...
    rt = YiRuntime(root)   # 宿主自备，宿主差异本模块不感知
"""
from __future__ import annotations

from typing import Any

from yishu_core.evidence import (
    evidence_envelope,
    evidence_from_analyze,
)
from yishu_core.execution.registry import (
    capability_matrix,
    discipline_capability,
    evaluation_baseline_of,
)
from yishu_core.report.request import normalize_request

AGENT_API_VERSION = "1.0.0"

# 分数读数唯一权威源（本模块不持有任何会漂移的数字）
SCORES_AUTHORITY = "docs/HANDOFF.md §一"
# 口径变更史唯一权威源
CALIBER_AUTHORITY = "docs/CHANGELOG.md"


def capabilities() -> list[dict[str, Any]]:
    """八字·六爻两科能力矩阵（含评测基线与评测分列）。adapter（MCP/API/CLI）直接转发的形状。"""
    return capability_matrix()


def validate_request(request: dict) -> dict[str, Any]:
    """请求预检：合法返回 {"ok": True, "normalized": …}；非法返回人话错误清单。

    与 CLI / Web / Actions 走同一 `normalize_request`——一个输入在所有入口
    产生完全相同的 normalized request（同源要求）。
    """
    try:
        normalized = normalize_request(request)
        return {"ok": True, "errors": [], "normalized": normalized}
    except ValueError as exc:
        return {"ok": False, "errors": [str(exc)], "normalized": None}


def run_report(rt: Any, request: dict) -> dict[str, Any]:
    """端到端执行：chart → analyze → render → envelope（含 evidence 与 provenance）。

    rt : yishu_core.execution.YiRuntime（宿主适配器由它决定，本模块不关心）。
    返回 envelope dict（RuntimeResult.to_envelope()）。
    """
    result = rt.execute(request)
    return result.to_envelope()


def get_evidence(rt: Any, request: dict, *,
                 rule_registry: dict | None = None) -> dict[str, Any]:
    """一次占问的结构化证据（Evidence Contract 派生视图）。

    rule_registry : 可选的规则注册表（如六爻 data/rules/rule_registry.json 的
                    解析结果），用于把 evidence.rule_id 挂到规则域并升级
                    evaluation_status。由 adapter 决定是否提供——core 不读学科文件。
    """
    from yishu_core.evidence import attach_rule_registry

    normalized = validate_request(request)
    if not normalized["ok"]:
        return {"ok": False, "errors": normalized["errors"]}
    req = normalized["normalized"]
    d = req["discipline"]
    analysis = rt.analyze(req)
    baseline = evaluation_baseline_of(d)
    evidence = evidence_from_analyze(d, analysis, evaluation_baseline=baseline)
    if rule_registry:
        evidence = attach_rule_registry(evidence, rule_registry)
    return {"ok": True, "envelope": evidence_envelope(d, evidence,
                                                      evaluation_baseline=baseline)}


def get_evaluation_status(discipline: str) -> dict[str, Any]:
    """单科评测覆盖状态：能力是什么性质、评测到哪一层、有哪些分列。

    刻意**不含分数**：分数会漂移，唯一权威源是 SCORES_AUTHORITY（HANDOFF §一）；
    本入口回答的是「哪类评测存在、该科结论可以说到什么程度」。
    """
    dc = discipline_capability(discipline)  # 未知学科在此抛 ValueError
    return {
        "discipline": dc.discipline,
        "capability": {k: getattr(dc, k) for k in
                       ("chart", "analyze", "narrate", "render", "evidence",
                        "synthesis", "external_evaluation", "holdout",
                        "source_provenance", "outcome_feedback")},
        "evaluation_baseline": dc.evaluation_baseline,
        "evaluation_splits": list(dc.evaluation_splits),
        "maturity_note": dc.maturity_note,
        "scores_authority": SCORES_AUTHORITY,
        "caliber_authority": CALIBER_AUTHORITY,
        "agent_note": _agent_note(dc),
    }


def _agent_note(dc) -> str:
    """该科结论允许说到什么程度（口径诚实约束的机器可读版，铁律三）。"""
    if dc.analyze == "mechanical_only":
        return ("本科为机械骨架：只输出结构标签，无吉凶断语——"
                "Agent 不得把它当成完整吉凶能力对外陈述")
    if dc.analyze == "source_only" or dc.evaluation_baseline == "source_only":
        return ("本科为古籍原文直录：输出即书源文本，"
                "Agent 不得把原文自动解释成独立预测结论")
    if dc.evaluation_baseline == "mechanical_regression":
        return ("本科只有规则自洽回归/golden 指纹，无古籍对齐分——"
                "Agent 不得陈述任何对齐百分比或效度")
    if dc.evaluation_baseline == "classical_holdout":
        return ("分数为古籍案例对齐分（须带集合名+样本量+是否调参，读 HANDOFF），"
                "不是现实命中率；现实效度以回填反馈为准（当前开环）")
    return "按铁律三口径诚实约束陈述"
