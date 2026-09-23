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
            hints.append("财运类：取妻财爻为用神")
            break
    
    for kw in career_keywords:
        if kw in question:
            hints.append("事业类：取官鬼爻为用神")
            break
    
    for kw in love_keywords:
        if kw in question:
            hints.append("感情类：男测取妻财爻，女测取官鬼爻为用神")
            break
    
    for kw in health_keywords:
        if kw in question:
            hints.append("健康类：取官鬼爻（病症）+ 世爻（自身）为用神")
            break
    
    for kw in study_keywords:
        if kw in question:
            hints.append("学业类：取父母爻为用神")
            break
    
    for kw in travel_keywords:
        if kw in question:
            hints.append("出行类：以世爻为主，兼看子孙爻")
            break
    
    for kw in lawsuit_keywords:
        if kw in question:
            hints.append("诉讼类：取官鬼爻为用神")
            break
    
    for kw in family_keywords:
        if kw in question:
            hints.append("家宅类：取父母爻（建筑）+ 相应爻位看风水")
            break
    
    if not hints:
        hints.append("通用：以世爻为主，兼看卦象整体生克")
    
    return hints


def format_text_output(result):
    """将JSON结果格式化为可读的文本输出"""
    lines = []
    lines.append("=" * 50)
    lines.append("六爻纳甲排盘结果")
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
    lines.append("排盘详表（从上爻到下爻）：")
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
        lines.append("经典断法分析：")
        
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

    lines = []
    W = 52  # 报告宽度

    # ── 标题头 ──
    lines.append("=" * W)
    lines.append("六 爻 纳 甲 占 卜 报 告".center(W))
    lines.append("=" * W)
    lines.append("")

    # ── 求测信息 ──
    lines.append("【求测信息】")
    lines.append(f"  问  题：{result.get('question', '未指明')}")
    lines.append(f"  方  式：{result.get('method', '铜钱摇卦')}")
    lines.append(f"  时  间：{dt.get('datetime', '未知')}")
    lines.append("")

    # ── 干支历法 ──
    lines.append("【干支历法】")
    lines.append(f"  年柱：{dt.get('year_stem_branch', '?')}　"
                 f"月柱：{dt.get('month_stem_branch', '?')}")
    lines.append(f"  日柱：{dt.get('day_stem_branch', '?')}　"
                 f"时柱：{dt.get('hour_stem_branch', '?')}")
    if empty:
        lines.append(f"  旬  空：{', '.join(empty)}")
    lines.append("")

    # ── 卦象 ──
    lines.append("─" * W)
    lines.append("【卦象一览】")
    lines.append(f"  本 卦：{oh.get('name', '?')}　"
                 f"{oh.get('upper_trigram', '?')}上{oh.get('lower_trigram', '?')}下　"
                 f"第{oh.get('sequence', '?')}卦")
    lines.append(f"  归 属：{oh.get('palace', '?')}宫（{oh.get('palace_element', '?')}行）"
                 f"　{oh.get('generation', '?')}卦")
    if oh.get('judgment'):
        lines.append(f"卦　辞：{oh['judgment']}")
    lines.append("")

    # 排盘表（上爻→下爻）
    yao_lines = oh.get("yao_lines", [])
    if yao_lines:
        lines.append("  排盘详表：")
        lines.append(f"  {'爻位':<4}{'六神':<5}{'六亲':<5}{'地支':<5}{'干支':<7}{'动静':<5}{'标记':<6}")
        lines.append("  " + "-" * (W - 4))
        for yao in reversed(yao_lines):
            pos_s = yao.get("name", "?")
            spirit_s = yao.get("six_spirit", "?")
            rel_s = yao.get("six_relation", "?")
            branch_s = yao.get("earthly_branch", "?")
            stem_s = f"{yao.get('heavenly_stem', '')}{branch_s}"
            moving_s = "动" if yao.get("is_moving") else "静"
            markers = []
            if yao.get("is_world"):
                markers.append("世")
            if yao.get("is_response"):
                markers.append("应")
            if yao.get("is_empty"):
                markers.append("空")
            mark_s = "/".join(markers) if markers else "－"
            lines.append(
                f"  {pos_s:<4}{spirit_s:<5}{rel_s:<5}{branch_s:<5}{stem_s:<7}{moving_s:<5}{mark_s:<6}"
            )
        lines.append("")

    # 变卦
    if ch:
        lines.append(f"  变 卦：{ch.get('name', '?')}")
        if ch.get('judgment'):
            lines.append(f"  变卦辞：{ch['judgment']}")
        changed_pos = ch.get("changed_lines", [])
        if changed_pos:
            pos_txt = "、".join(f"第{n}爻" for n in changed_pos)
            lines.append(f"  动 爻：{pos_txt}")
        lines.append("")

    # ── 用神建议 ──
    if hints:
        lines.append("─" * W)
        lines.append("【用神建议】")
        for h in hints[:5]:
            lines.append(f"  · {h}")
        lines.append("")

    # ── 五步思维链分析 ──
    lines.append("=" * W)
    lines.append("【五步思维链分析】")
    lines.append("=" * W)

    # ── Step 1: 观局 ──
    lines.append("")
    lines.append("  ┌── Step 1 ─ 观局 ──────────────────────────┐")
    if step1:
        lines.append(f"  │ 本卦：{step1.get('hexagram_name', '?')}　"
                     f"{step1.get('palace', '?')}宫　{step1.get('palace_element', '?')}行")
        desc1 = step1.get("description", "")
        if desc1:
            # 分行显示长描述
            for para in desc1.split("。"):
                para = para.strip()
                if para:
                    lines.append(f"  │ {para}")
    lines.append("  └──────────────────────────────────────────┘")

    # ── Step 2: 定用 ──
    lines.append("")
    lines.append("  ┌── Step 2 ─ 定用神 ────────────────────────┐")
    if step2:
        lines.append(f"  │ 用神：{step2.get('use_god_category', '?')}　"
                     f"五行：{step2.get('use_god_element', '?')}")
        pos2 = step2.get("selected_position")
        if pos2:
            lines.append(f"  │ 位置：第{pos2}爻　"
                     f"六亲：{step2.get('selected_relation', '?')}")
        desc2 = step2.get("description", "")
        if desc2:
            for para in desc2.split("。"):
                para = para.strip()
                if para:
                    lines.append(f"  │ {para}")
        # 原神/忌神
        ys_text = step2.get("yuan_shen_text", "")
        js_text = step2.get("ji_shen_text", "")
        if ys_text:
            lines.append(f"  │ 原神：{ys_text}")
        if js_text:
            lines.append(f"  │ 忌神：{js_text}")
    lines.append("  └──────────────────────────────────────────┘")

    # ── Step 3: 断旺 ──
    lines.append("")
    lines.append("  ┌── Step 3 ─ 断旺衰 ────────────────────────┐")
    if step3:
        strength = step3.get("strength_level", "?")
        eff_score = step3.get("effective_score", 0)
        lines.append(f"  │ 旺衰等级：{strength}（评分 {eff_score:.2f}）")
        desc3 = step3.get("description", "")
        if desc3:
            for para in desc3.split("。"):
                para = para.strip()
                if para:
                    lines.append(f"  │ {para}")
        # 关键因素
        factors = step3.get("key_factors", step3.get("factors", []))
        if isinstance(factors, list) and factors:
            lines.append(f"  │ 关键因素：")
            for f in factors[:6]:
                lines.append(f"  │   · {f}")
    lines.append("  └──────────────────────────────────────────┘")

    # ── Step 4: 察变 ──
    lines.append("")
    lines.append("  ┌── Step 4 ─ 察动变 ────────────────────────┐")
    if step4:
        net_eff = step4.get("net_effect", 0)
        net_desc = step4.get("net_effect_description", "无动爻")
        lines.append(f"  │ 动变净效应：{net_eff:+.2f}（{net_desc}）")
        desc4 = step4.get("description", "")
        if desc4:
            for para in desc4.split("。"):
                para = para.strip()
                if para:
                    lines.append(f"  │ {para}")
        # 逐爻分析
        yaos_detail = step4.get("yao_analysis", step4.get("moving_details", []))
        if isinstance(yaos_detail, list) and yaos_detail:
            lines.append(f"  │ 逐爻分析：")
            for yd in yaos_detail[:6]:
                if isinstance(yd, dict):
                    yd_pos = yd.get("position", "?")
                    yd_desc = yd.get("description", yd.get("analysis", ""))
                    if not yd_desc and yd.get("change_type"):
                        yd_desc = yd["change_type"]
                    if yd_desc:
                        lines.append(f"  │   第{yd_pos}爻：{yd_desc}")
                elif isinstance(yd, str) and yd:
                    lines.append(f"  │   {yd}")
    lines.append("  └──────────────────────────────────────────┘")

    # ── Step 5: 综合 ──
    lines.append("")
    lines.append("  ┌── Step 5 ─ 综合判断 ──────────────────────┐")
    if step5:
        verdict = step5.get("verdict", "?")
        final_score = step5.get("final_score", 0)
        verdict_desc = step5.get("verdict_description", "")
        confidence = step5.get("confidence", "?")
        conf_desc = step5.get("confidence_description", "")

        lines.append(f"  │ 判　语：{verdict}（{final_score:.2f}分）")
        if verdict_desc:
            lines.append(f"  │ 说　明：{verdict_desc}")
        lines.append(f"  │ 置信度：{confidence}%（{conf_desc}）")

        # 格局识别
        sp = step5.get("special_pattern", {})
        if isinstance(sp, dict) and sp.get("pattern"):
            lines.append(f"  │ 格　局：{sp['pattern']} — {sp.get('description', '')}")

        # 各项调整明细
        adj_items = []
        bc = step5.get("base_score", 0)
        adj_items.append(f"基础旺衰 {bc:.2f}")
        ce = step5.get("change_net_effect", 0)
        if ce != 0:
            adj_items.append(f"动变 {ce:+.2f}")
        ha = step5.get("hex_adjustment", 0)
        if ha != 0:
            hr = step5.get("hex_adjustment_reason", "")
            adj_items.append(f"卦体 {ha:+.1f}（{hr}）")
        sa = step5.get("spirit_adjustment", 0)
        if sa != 0:
            sr = step5.get("spirit_adjustment_reasons", "")
            if isinstance(sr, list) and sr:
                sr = "、".join(sr)
            adj_items.append(f"六神 {sa:+.1f}（{sr}）")
        tp_s = step5.get("tp_score", 0)
        if tp_s != 0:
            tp_r = step5.get("tp_reason", "")
            adj_items.append(f"三刑 {tp_s:+.1f}（{tp_r}）")
        dmb = step5.get("dmb_adjustment", 0)
        if dmb != 0:
            adj_items.append(f"日月合 {dmb:+.2f}")
        sb_a = step5.get("sb_adjustment", 0)
        if sb_a != 0:
            adj_items.append(f"六破 {sb_a:+.2f}")
        hm_c = step5.get("hidden_movement_count", 0)
        if hm_c and hm_c > 0:
            hm_r = step5.get("hidden_movement_reason", "")
            hm_m = step5.get("hidden_movement_modifier", 0)
            adj_items.append(f"暗动 {hm_m:+.1f}（{hm_r}）")
        ghr = step5.get("greedy_harmony_reason", "")
        if ghr:
            ghs = step5.get("greedy_harmony_score", 0)
            adj_items.append(f"贪合 {ghs:+.2f}（{ghr}）")
        pa = step5.get("pattern_adjustment", 0)
        if pa != 0:
            adj_items.append(f"格局 {pa:+.1f}")

        if adj_items:
            lines.append(f"  │ 评分明细：{' + '.join(adj_items)} = {final_score:.2f}")
    lines.append("  └──────────────────────────────────────────┘")

    # ── 格局识别摘要 ──
    lines.append("")
    lines.append("─" * W)
    lines.append("【格局识别】")
    patterns_found = []
    if isinstance(aa, dict):
        # 伏藏
        hs = aa.get("hidden_spirit_analysis", {})
        if isinstance(hs, dict) and hs.get("has_hidden_spirit"):
            patterns_found.append(f"伏藏：{hs.get('summary', '')}")
        # 暗动
        hm = aa.get("hidden_movement", {})
        if isinstance(hm, dict) and hm.get("has_hidden_movement"):
            patterns_found.append(f"暗动：{hm.get('summary', '')}")
        # 月破
        mb = aa.get("monthly_break", {})
        if isinstance(mb, dict) and mb.get("has_monthly_break"):
            patterns_found.append(f"月破：{mb.get('summary', '')}")
        # 三合局
        tc = aa.get("triple_combo", {})
        if isinstance(tc, dict) and tc.get("has_triple_combo"):
            patterns_found.append(f"三合局：{tc.get('summary', '')}")
        # 进退神
        ar = aa.get("advance_retreat", {})
        if isinstance(ar, dict) and ar.get("has_advance_retreat"):
            patterns_found.append(f"进退神：{ar.get('summary', '')}")
        # 六合六冲
        ch_aa = aa.get("clash_harmony", {})
        if isinstance(ch_aa, dict) and ch_aa.get("summary"):
            patterns_found.append(f"卦格：{ch_aa['summary']}")
        # 反吟伏吟
        rp = aa.get("repetition", {})
        if isinstance(rp, dict) and rp.get("summary"):
            patterns_found.append(f"吟反：{rp['summary']}")
        # 三刑
        tp = aa.get("three_punishments", {})
        if isinstance(tp, dict) and tp.get("has_punishment"):
            patterns_found.append(f"三刑：{tp.get('summary', '')}")
        # 六亲持世
        sy = aa.get("shi_yao_relation", {})
        if isinstance(sy, dict) and sy.get("description"):
            patterns_found.append(f"六亲持世：{sy['description']}")
        # 纳音
        ny = aa.get("nayin", {})
        if isinstance(ny, dict) and ny.get("description"):
            patterns_found.append(f"纳音：{ny['description']}")

    if step5 and isinstance(sp, dict) and sp.get("pattern"):
        patterns_found.append(f"特殊格局：{sp['pattern']}（{sp.get('description', '')}）")

    if patterns_found:
        for p in patterns_found:
            lines.append(f"  · {p}")
    else:
        lines.append("  （无特殊格局）")
    lines.append("")

    # ── 卜象解析 ──
    ti_r = result.get("trigram_interpretation") if isinstance(result, dict) else None
    if ti_r and isinstance(ti_r, dict) and not ti_r.get("error"):
        try:
            from trigram_symbolism import format_trigram_interpretation_text as _fmt_trigram_r
            tri_lines = _fmt_trigram_r(ti_r).split("\n")
        except Exception:
            tri_lines = []
        if tri_lines:
            lines.append("─" * W)
            lines.append("【卜象解析】")
            for tl in tri_lines:
                lines.append(tl)
            lines.append("")

    # ── 应期推断 ──
    lines.append("─" * W)
    lines.append("【应期推断】")
    timing = step5.get("timing", {}) if step5 else {}
    ying_dates = step5.get("yingqi_dates", {}) if step5 else {}

    if timing:
        speed = timing.get("speed", "待断")
        summary_t = timing.get("summary_text", "")
        lines.append(f"  整体节奏：{speed}")
        if summary_t:
            lines.append(f"  方法综述：{summary_t}")

    if ying_dates and ying_dates.get("dates"):
        use_branch = ying_dates.get("use_god_branch", "")
        use_elem = ying_dates.get("use_god_element", "")
        if use_branch:
            lines.append(f"  用　　神：{use_branch}（{use_elem}）")
        strength_l = ying_dates.get("strength_level", "")
        if strength_l:
            lines.append(f"  旺　　衰：{strength_l}")
        lines.append(f"  应期日期：")
        for d in ying_dates.get("dates", []):
            dt_s = d.get("date", "?")
            rule = d.get("rule", "")
            branch = d.get("branch", "")
            desc = d.get("description", "")
            br_info = f" [{branch}]" if branch else ""
            lines.append(f"    {dt_s}{br_info} — {rule}（{desc}）")
        yq_summary = ying_dates.get("summary_text", "")
        if yq_summary:
            lines.append(f"  小　　结：{yq_summary}")
    elif step5 and step5.get("verdict"):
        # fallback: use step5 verdict to estimate timing
        verdict_now = step5.get("verdict", "")
        if verdict_now in ("大吉", "吉"):
            lines.append("  应期推断：事顺势而为，逢值逢合应速。")
        elif verdict_now in ("凶", "平凶"):
            lines.append("  应期推断：守静安时，待用神旺相之月可转。")
        else:
            lines.append("  应期推断：吉凶参半，逢值逢冲应之。")
    else:
        lines.append("  应期推断：待定")
    lines.append("")

    # ── 最终判语 ──
    lines.append("=" * W)
    lines.append("【最 终 判 语】".center(W))
    lines.append("=" * W)
    lines.append("")

    if step5:
        verdict = step5.get("verdict", "待定")
        final_score = step5.get("final_score", 0)
        verdict_desc = step5.get("verdict_description", "")
        confidence = step5.get("confidence", "?")

        # 判语大字
        lines.append(f"　　　　　　◖ {verdict} ◗")
        lines.append("")
        if verdict_desc:
            lines.append(f"　　{verdict_desc}")
        lines.append("")
        lines.append(f"　　综合评分：{final_score:.2f} / 5.00")
        lines.append(f"　　置信　度：{confidence}%（{step5.get('confidence_description', '')}）")

        # pattern override notes
        pvn = step5.get("pattern_verdict_note", "")
        if pvn:
            lines.append("")
            lines.append(f"　　※ {pvn}")
        otn = step5.get("officer_tomb_verdict_note", "")
        if otn:
            lines.append("")
            lines.append(f"　　※ {otn}")

        # 经典引文
        cqs = step5.get("classical_quotes", [])
        if isinstance(cqs, list) and cqs:
            lines.append("")
            lines.append("　　【经典引文】")
            for cq in cqs:
                if isinstance(cq, dict):
                    src = cq.get("source", "")
                    quote = cq.get("quote", "")
                    lines.append(f"　　· {src}：「{quote}」")

        # 卦身摘要
        body_note = step5.get("hexagram_body_note", "")
        if body_note:
            lines.append("")
            lines.append(f"　　【卦身】{body_note}")

    lines.append("")
    lines.append("=" * W)
    lines.append("报告中　·　仅供参考".center(W))
    lines.append("=" * W)

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

