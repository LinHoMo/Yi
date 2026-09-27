from __future__ import annotations
import json
from pathlib import Path as _P
# -*- coding: utf-8 -*-
"""六爻纳甲引擎：数据表 / 干支历与真太阳时 / 排盘核心 / 文本输出 / 历史遗留梅花与批量接口。（拆分自 liuyao_engine.py，纯搬移不改逻辑；聚合入口见 liuyao_engine.py）。"""

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel, kernel_dir

_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    ADVANCE_PAIRS,
    BRANCH_ELEMENTS,
    BREAK_PAIRS,
    CHONG_PAIRS,
    EARTHLY_BRANCHES,
    EIGHT_PALACES,
    BAGUA_LINES,
    HEAVENLY_STEMS,
    HEXAGRAM_TRIGRAMS,
    HE_PAIRS,
    KE_CYCLE,
    NAJIA_BRANCHES,
    RETREAT_PAIRS,
    SHENG_CYCLE,
    STEM_ELEMENTS,
    TOMB_MAP,
)

from yishu_core.najia import najia_branch  # noqa: E402

import argparse

import json

import math

import os

import random

import sys

from datetime import datetime, timedelta

from pathlib import Path

from yishu_core.runtime import force_utf8_stdio as _force_utf8_stdio  # noqa: E402
from engine_format_report import (  # noqa: E402  报告各段落排版（本文件只管顺序编排）
    REPORT_WIDTH,
    build_head,
    build_hexagram,
    build_patterns,
    build_steps,
    build_timing,
    build_trigram,
    build_verdict,
)


_FL = json.loads((_P(__file__).resolve().parents[1] / 'data' / 'narrative_templates.json').read_text(encoding='utf-8')).get('engine_format_labels', {})


def generate_analysis_hints(question):
    """
    根据问题关键词生成用神建议
    """
    hints = []
    
    # 定义关键词映射
    finance_keywords = ["财", "钱", "投资", "生意", "收入", "利", "赚", "经济", "金", "上市", "公司", "项目", "产品", "融资", "创业", "合伙", "股份", "分红", "上市", "经营", "市场"]
    career_keywords = ["事业", "工作", "升职", "官", "职", "考", "升", "提拔", "调动", "辞职", "面试", "招聘", "编制", "公务员"]
    love_keywords = ["感情", "婚", "恋", "爱", "桃花", "对象", "另一半", "伴侣"]
    health_keywords = ["健康", "病", "疾", "身", "医", "药"]
    study_keywords = ["学", "考试", "文", "书", "成绩", "毕业", "学位"]
    travel_keywords = ["出行", "旅游", "旅行", "出远门"]
    lawsuit_keywords = ["官", "诉讼", "官司", "纠纷", "法律"]
    family_keywords = ["家", "宅", "房", "居", "搬家"]
    
    for kw in finance_keywords:
        if kw in question:
            hints.append(_FL.get("use_god_caiyun"))
            break
    
    for kw in career_keywords:
        if kw in question:
            hints.append(_FL.get("use_god_career"))
            break
    
    for kw in love_keywords:
        if kw in question:
            hints.append(_FL.get("use_god_love"))
            break
    
    for kw in health_keywords:
        if kw in question:
            hints.append("健康类：取官鬼爻（病症）+ 世爻（自身）为用神")
            break
    
    for kw in study_keywords:
        if kw in question:
            hints.append(_FL.get("use_god_exam"))
            break
    
    for kw in travel_keywords:
        if kw in question:
            hints.append("出行类：以世爻为主，兼看子孙爻")
            break
    
    for kw in lawsuit_keywords:
        if kw in question:
            hints.append(_FL.get("use_god_lawsuit"))
            break
    
    for kw in family_keywords:
        if kw in question:
            hints.append(_FL.get("use_god_home"))
            break
    
    if not hints:
        hints.append(_FL.get("use_god_default"))
    
    return hints


def format_text_output(result):
    """将JSON结果格式化为可读的文本输出"""
    lines = []
    lines.append("=" * 50)
    lines.append(_FL.get("title"))
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"求测问题：{result['question']}")
    lines.append(f"起卦方式：{result['method']}")
    
    dt = result['divination_time']
    lines.append(f"起卦时间：{dt['datetime']}")
    lines.append(f"年柱：{dt['year_stem_branch']}  月柱：{dt['month_stem_branch']}")
    lines.append(f"日柱：{dt['day_stem_branch']}  时柱：{dt['hour_stem_branch']}")
    lines.append(f"旬空：{', '.join(result['empty_branches'])}")
    lines.append("")
    
    oh = result['original_hexagram']
    lines.append("-" * 50)
    lines.append(f"本卦：{oh['name']}  (第{oh['sequence']}卦)")
    lines.append(f"卦象：{oh['upper_trigram']}上{oh['lower_trigram']}下")
    lines.append(f"归属：{oh['palace']}宫 ({oh['palace_element']}行)")
    lines.append(f"世代：{oh['generation']}卦")
    lines.append(f"卦辞：{oh['judgment']}")
    lines.append("")

    # 排盘表
    lines.append(_FL.get("yao_table"))
    lines.append(f"{'爻位':<6}{'六神':<6}{'六亲':<6}{'地支':<6}{'干支':<8}{'动静':<8}{'标记':<8}")
    lines.append("-" * 50)
    
    for yao in reversed(oh['yao_lines']):  # 从上爻开始显示
        pos_str = yao['name']
        moving_str = "动" if yao['is_moving'] else "静"
        stem_branch = f"{yao['heavenly_stem']}{yao['earthly_branch']}"
        
        markers = []
        if yao['is_world']:
            markers.append("世")
        if yao['is_response']:
            markers.append("应")
        if yao['is_empty']:
            markers.append("空")
        marker_str = "/".join(markers)
        
        lines.append(f"{pos_str:<6}{yao['six_spirit']:<6}{yao['six_relation']:<6}{yao['earthly_branch']:<6}{stem_branch:<8}{moving_str:<8}{marker_str:<8}")
    
    lines.append("")
    
    # 变卦
    if result['changed_hexagram']:
        ch = result['changed_hexagram']
        lines.append("-" * 50)
        lines.append(f"变卦：{ch['name']}")
        lines.append(f"变卦卦辞：{ch['judgment']}")
        lines.append(f"动爻位置：{', '.join(f'第{n}爻' for n in ch['changed_lines'])}")
        lines.append("")
    
    # 用神建议
    lines.append("-" * 50)
    lines.append("用神建议：")
    for hint in result['analysis_hints']['possible_use_gods']:
        lines.append(f"  - {hint}")

    # 卜象解析（八卦类象）
    ti = result.get("trigram_interpretation") if isinstance(result, dict) else None
    if ti and isinstance(ti, dict) and not ti.get("error"):
        try:
            from trigram_symbolism import format_trigram_interpretation_text as _fmt_trigram
            formatted_trigram = _fmt_trigram(ti)
        except Exception:
            formatted_trigram = None
        if formatted_trigram:
            lines.append("")
            lines.append("-" * 50)
            lines.append("【卜象解析】")
            for tline in formatted_trigram.split("\n"):
                lines.append(f"  {tline}")

    # 经典分析摘要
    if 'advanced_analysis' in result:
        aa = result['advanced_analysis']
        lines.append("")
        lines.append("-" * 50)
        lines.append(_FL.get("classical"))
        
        # 伏藏
        if aa.get('hidden_spirit_analysis'):
            hs = aa['hidden_spirit_analysis']
            if isinstance(hs, dict) and hs.get('has_hidden_spirit'):
                lines.append(f"  [伏藏] {hs.get('summary', '')}")
                for detail in hs.get('details', []):
                    if isinstance(detail, dict):
                        status = "得出" if detail.get('can_emerge') else "不得出"
                        hr = detail.get('reason', '')
                        lines.append(
                            f"    - {detail.get('missing_relation', '?')}伏("
                            f"{detail.get('hidden_spirit', {}).get('branch', '?')})"
                            f"飞{detail.get('covering_spirit', {}).get('six_relation', '?')}"
                            f"({detail.get('covering_spirit', {}).get('branch', '?')})"
                            f" → {status}（{hr}）"
                        )
                    else:
                        lines.append(f"    - {detail}")
        
        # 暗动
        if aa.get('hidden_movement'):
            hm = aa['hidden_movement']
            if isinstance(hm, dict) and hm.get('has_hidden_movement'):
                lines.append(f"  [暗动] {hm.get('summary', '')}")
        
        # 月破
        if aa.get('monthly_break'):
            mb = aa['monthly_break']
            if isinstance(mb, dict) and mb.get('has_monthly_break'):
                lines.append(f"  [月破] {mb.get('summary', '')}")
        
        # 三合局
        if aa.get('triple_combo'):
            tc = aa['triple_combo']
            if isinstance(tc, dict) and tc.get('has_triple_combo'):
                lines.append(f"  [三合] {tc.get('summary', '')}")
                for cd in tc.get('details', []):
                    if isinstance(cd, dict) and cd.get('description'):
                        lines.append(f"    - {cd['description']}")
        
        # 进退神
        if aa.get('advance_retreat'):
            ar = aa['advance_retreat']
            if isinstance(ar, dict) and ar.get('has_advance_retreat'):
                lines.append(f"  [进退] {ar.get('summary', '')}")
        
        # 六合六冲
        if aa.get('clash_harmony'):
            ch = aa['clash_harmony']
            if isinstance(ch, dict) and ch.get('summary'):
                lines.append(f"  [卦格] {ch['summary']}")
        
        # 反吟伏吟
        if aa.get('repetition'):
            rp = aa['repetition']
            if isinstance(rp, dict) and rp.get('summary'):
                lines.append(f"  [吟反] {rp['summary']}")
        
        # 旺衰总结
        if aa.get('element_strength'):
            es = aa['element_strength']
            if es.get('summary'):
                lines.append(f"  [旺衰] {es['summary']}")
    
    # 应期精确日期（来自思维链 step5.9b）
    tc = result.get("thinking_chain", {})
    step5 = tc.get("step5_synthesis", {}) or result.get("step5_synthesis", {})
    yq = step5.get("yingqi_dates") if step5 else None

    if yq and yq.get("dates"):
        lines.append("")
        lines.append("-" * 50)
        lines.append(f"应期（{yq.get('speed', '待定')}）：")
        if yq.get("use_god_branch"):
            lines.append(f"  用神：{yq['use_god_branch']}（{yq.get('use_god_element', '?')}）"
                         f"  旺衰：{yq.get('strength_level', '?')}")
        for d in yq.get("dates", []):
            dt_str = d.get("date", "?")
            rule = d.get("rule", "")
            branch = d.get("branch", "")
            desc = d.get("description", "")
            branch_info = f" [{branch}]" if branch else ""
            lines.append(f"  {dt_str}{branch_info} — {rule}（{desc}）")
        if yq.get("summary_text"):
            lines.append(f"  → {yq['summary_text']}")

    lines.append("")
    lines.append("=" * 50)

    return "\n".join(lines)


def format_reading_output(result, chain=None):
    """将思维链结果格式化为清晰的中文占卜报告。

    参数
    ----
    result : dict
        build_hexagram_result() 返回的完整排盘结果。
    chain : dict, optional
        run_thinking_chain() 返回的五步思维链字典。
        若为 None，则尝试从 result["thinking_chain"] 读取。

    返回
    ----
    str
        格式化的中文报告文本。
    """
    if chain is None:
        chain = result.get("thinking_chain", {})

    step1 = chain.get("step1_situational_reading", {})
    step2 = chain.get("step2_use_god_identification", {})
    step3 = chain.get("step3_strength_analysis", {})
    step4 = chain.get("step4_change_analysis", {})
    step5 = chain.get("step5_synthesis", {})

    dt = result.get("divination_time", {})
    oh = result.get("original_hexagram", {})
    ch = result.get("changed_hexagram", {})
    aa = result.get("advanced_analysis", {})
    empty = result.get("empty_branches", [])
    hints = result.get("analysis_hints", {}).get("possible_use_gods", [])
    # 特殊格局：Step5 与「格局识别」两段共用（原实现里由 Step5 段赋值）
    sp = step5.get("special_pattern", {}) if step5 else {}

    W = REPORT_WIDTH  # 报告宽度

    # 各段落的排版规则外置到 engine_format_report，此处只管顺序编排
    lines = []
    lines.extend(build_head(result, dt, empty, W))
    lines.extend(build_hexagram(oh, ch, hints, W))
    lines.extend(build_steps(step1, step2, step3, step4, step5, W))
    lines.extend(build_patterns(aa, step5, sp, W))
    lines.extend(build_trigram(result, W))
    lines.extend(build_timing(step5, W))
    lines.extend(build_verdict(step5, W))

    return "\n".join(lines)


def apply_depth_limit(text: str, depth: str) -> str:
    """解读深度限制器

    参数
    ----
    text : str
        原始文本输出。
    depth : str
        brief / standard / full

    返回
    ----
    str
        按深度截断后的文本。
    """
    limits = {
        "brief": 300,     # ~150汉字
        "standard": 800,  # ~400汉字
        "full": 99999,    # 无限制
    }
    limit = limits.get(depth, 99999)
    if len(text) <= limit:
        return text

    # Smart truncation at sentence boundary
    truncated = text[:limit]
    last_period = truncated.rfind("。")
    last_newline = truncated.rfind("\n")
    cut_at = max(last_period, last_newline)
    if cut_at > limit * 0.5:
        return truncated[:cut_at + 1] + "\n...(输出已达深度上限，使用 --depth full 获取全文)"
    return truncated + "...[截断]"


def _apply_depth_to_result(result: dict, depth: str) -> dict:
    """对 JSON 结果中的描述字段按深度截断。

    brief 模式下保留关键判语和标准字段，截断长描述。
    """
    if depth == "full":
        return result

    # Fields in result that contain long descriptive text
    long_fields_top = ["summary_text"]
    thinking_keys = ["thinking_chain", "step5_synthesis"]

    # Truncate top-level long fields
    for field in long_fields_top:
        val = result.get(field, "")
        if isinstance(val, str) and len(val) > 200:
            result[field] = apply_depth_limit(val, "brief")

    # Walk into thinking_chain → step5_synthesis
    tc = result.get("thinking_chain", {})
    if isinstance(tc, dict):
        for key in tc:
            step = tc[key]
            if isinstance(step, dict):
                for desc_key in ("description", "verdict_description",
                                 "reasoning_chain"):
                    val = step.get(desc_key, "")
                    if isinstance(val, str) and len(val) > 150:
                        step[desc_key] = apply_depth_limit(
                            val, "brief" if depth == "brief" else "standard"
                        )
                # step5 summary_text
                if key == "step5_synthesis":
                    summary = step.get("summary_text", "")
                    if isinstance(summary, str) and len(summary) > 200:
                        step["summary_text"] = apply_depth_limit(summary, depth)

    return result

