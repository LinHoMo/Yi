# -*- coding: utf-8 -*-
# 本文件为聚合入口：子模块见 engine_*/chain_*/classical_*。
from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)






from chain_tables import HEXAGRAM_LIUHE, HEXAGRAM_LIUCHONG
from liuyao_analyze import (
    step1_read_situation,
    step2_identify_use_god,
    step3_analyze_strength,
    step4_analyze_changes,
    step5_synthesize,
)
from liuyao_narrate import (
    analyze_shi_yao_relation,
    find_classical_quotes,
    _build_reasoning_chain,
    _build_overall_summary,
    _clean_internal_keys,
)

def run_thinking_chain(hex_result: dict) -> dict:
    """
    执行完整的五步六爻思维链分析。

    Parameters
    ----------
    hex_result : dict
        build_hexagram_result() 返回的JSON字典结构，
        包含 original_hexagram, divination_time, empty_branches,
        changed_hexagram, question_category 等字段。

    Returns
    -------
    dict
        包含五步结构的完整思维链结果：
        - step1_situational_reading
        - step2_use_god_identification
        - step3_strength_analysis
        - step4_change_analysis
        - step5_synthesis
        以及 summary_text（总摘要）和 reasoning_chain（推理链）。
    """
    # 创建内部引用字典，使各步骤可以互相引用
    context = dict(hex_result)  # 浅拷贝

    # 确保 advanced_analysis 存在（build_hexagram_result 不调用 enhance_reading）
    if "advanced_analysis" not in context or not context.get("advanced_analysis"):
        try:
            from classical_analysis import enhance_reading
            # enhance_reading 原位修改 context 并返回它
            # 调用后 context["advanced_analysis"] 已被填充
            enhance_reading(context)
            # 确保 advanced_analysis 存在（enhance_reading 可能因为异常跳过）
            if "advanced_analysis" not in context:
                context["advanced_analysis"] = {}
        except Exception:
            context["advanced_analysis"] = {}

    # 同步 advanced_analysis 到 hex_result（step1 使用 hex_result 而非 context）
    if "advanced_analysis" in context and "advanced_analysis" not in hex_result:
        hex_result["advanced_analysis"] = context["advanced_analysis"]

    # 执行五步（前一步结果存入 context 供后续步骤使用）
    context["_step1_data"] = step1_read_situation(hex_result)
    context["_step2_data"] = step2_identify_use_god(context)  # 使用含step1的context

    # 六亲持世深化分析：需 用神类别（性别视角）方能量身解读婚姻持世，
    # 故置于 step2 之后；结果存入 advanced_analysis.shi_yao_relation。
    adv = hex_result.get("advanced_analysis", {})
    if isinstance(adv, dict):
        adv["shi_yao_relation"] = analyze_shi_yao_relation(
            hex_result, context["_step2_data"].get("use_god_category")
        )
    context["_step3_data"] = step3_analyze_strength(context)
    context["_step4_data"] = step4_analyze_changes(context)
    context["_step5_data"] = step5_synthesize(context)

    # 构建最终输出
    chain = {
        "step1_situational_reading": context["_step1_data"],
        "step2_use_god_identification": context["_step2_data"],
        "step3_strength_analysis": context["_step3_data"],
        "step4_change_analysis": context["_step4_data"],
        "step5_synthesis": context["_step5_data"],
    }

    # 构建总摘要（使用完整五步数据重新生成推理链，包含卦身等辅助分析）
    full_reasoning_chain = _build_reasoning_chain(
        context["_step1_data"],
        context["_step2_data"],
        context["_step3_data"],
        context["_step4_data"],
        context["_step5_data"],
        context=context,
    )
    chain["reasoning_chain"] = full_reasoning_chain
    chain["summary_text"] = _build_overall_summary(context)

    # 清理内部引用键（不对外暴露）
    chain = _clean_internal_keys(chain)
    
    # 将思维链结果写入原字典
    hex_result["thinking_chain"] = chain

    # ★ 关键修复：重新检测经典引文（此时 chain 已构建，step4/step5 已就位）
    # 原来在 step5_synthesize 内部调用 find_classical_quotes 时 chain 还未就绪，
    # 导致「回头生/三合成局/伏藏/暗动」等需要 step4/5 数据的 pattern 全部匹配失败。
    fresh_quotes = find_classical_quotes(hex_result)
    if fresh_quotes and "step5_synthesis" in chain:
        # 替换原来的 classical_quotes（原来的往往是空或不完整的）
        chain["step5_synthesis"]["classical_quotes"] = fresh_quotes
        chain["step5_synthesis"]["classical_quotes_text"] = "【经典引文】" + "".join(
            f"• {q['source']}：{q['quote']}" for q in fresh_quotes
        )
    
    return hex_result


if __name__ == "__main__":
    # 示例用法（需要配合 build_hexagram_result 使用）
    print("六爻思维链模块")
    print("===============")
    print("使用方式：")
    print('  from thinking_chain import run_thinking_chain')
    print('  chain = run_thinking_chain(hex_result)')
    print('  print(chain["step5_synthesis"]["verdict"])')
    print()
    print("各步骤也可独立调用：")
    print("  step1_read_situation(hex_result)")
    print("  step2_identify_use_god(hex_result)")
    print("  step3_analyze_strength(hex_result)")
    print("  step4_analyze_changes(hex_result)")
    print("  step5_synthesize(hex_result)")
