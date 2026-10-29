# -*- coding: utf-8 -*-
"""叙述装配（第三百五十五批）：从 analyze JSON 的 step fact 重建叙述链。

为什么需要它：CONTRACT §六-7 要求 `analyze` 不再产 `reasoning_chain` 9 条成句与
`summary_text` 354 字——这两段是**叙述**，不是结构事实。355 批把生成时机移到
narrate／呈现层：本模块只接收 analyze JSON（chart + `thinking_chain` 的 step1–5 事实），
用 `chain_assembly` 的事实装配器重建同一串文本；**不 import `analyze.py`、不写
analyze 的输出键**。`narrate_core` / `output.py` / `case_runner` / portal / refactor_guard
在需要旧字段时调用本模块，保持产品文本不变。

边界说明：`chain_assembly` 是事实装配库（step1–5 的摘要与格局标签），不是 analyze
阶段入口；本模块消费它，但 narrative 层不回调 analyze 的输出。该方向在 CONTRACT §三
以「narrate → narrative_assembly（fact builder）」登记。
"""
from __future__ import annotations

from chain_assembly import _build_overall_summary, _build_reasoning_chain


def context_from_result(result: dict) -> dict:
    """analyze JSON → `_build_*` 需要的 context（chart 字段 + `_step*` + advanced）。"""
    tc = (result or {}).get("thinking_chain") or {}
    ctx = dict(result or {})
    ctx["_step1_data"] = tc.get("step1_situational_reading") or {}
    ctx["_step2_data"] = tc.get("step2_use_god_identification") or {}
    ctx["_step3_data"] = tc.get("step3_strength_analysis") or {}
    ctx["_step4_data"] = tc.get("step4_change_analysis") or {}
    ctx["_step5_data"] = tc.get("step5_synthesis") or {}
    return ctx


def build_reasoning_chain(result: dict) -> list[str]:
    """按 analyze JSON 的 step 事实重建 9 条叙述链（与 355 批前同源同序）。"""
    ctx = context_from_result(result)
    return _build_reasoning_chain(
        ctx["_step1_data"],
        ctx["_step2_data"],
        ctx["_step3_data"],
        ctx["_step4_data"],
        ctx["_step5_data"],
        context=ctx,
    )


def build_summary(result: dict) -> str:
    """按 analyze JSON 的 step 事实重建整体摘要（与 355 批前同源）。"""
    return _build_overall_summary(context_from_result(result))


def attach_narrative(result: dict) -> dict:
    """返回带 `thinking_chain.reasoning_chain/summary_text` 的副本（供呈现层格式化）。"""
    if not isinstance(result, dict):
        return result
    tc = result.get("thinking_chain")
    if not isinstance(tc, dict):
        return result
    tc = dict(tc)
    if "reasoning_chain" not in tc:
        tc["reasoning_chain"] = build_reasoning_chain(result)
    if "summary_text" not in tc:
        tc["summary_text"] = build_summary(result)
    out = dict(result)
    out["thinking_chain"] = tc
    return out
