#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
六爻可视化引擎 (Liu Yao Visualization Engine)
================================================
将排盘 JSON 数据转化为可交互 HTML 报告，含：
- 卦盘图（SVG 六爻线画 — 本卦 + 变卦并列）
- 五行力量雷达图（SVG）
- 动变对比图（SVG 柱状）
- 应期时间线（SVG 横轴）
- 五行生克流转图（SVG 五角循环）
- 八宫归属图（SVG 8×8 矩阵）
- 批量对比可视化（JSON 数组 → 多列卦象）
- 历史日志统计图（胜率柱状/时间分布）

仅使用 Python 标准库。输出独立 HTML（CDN SVG，无 JS 依赖即可渲染，
可选 Chart.js CDN 增强交互）。
"""

import argparse
import html
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path

import os as _ks_os  # noqa: E402  内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in sys.path:
    sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel  # noqa: E402

_ensure_kernel(__file__)

from yishu_core.report import render_page  # noqa: E402  统一呈现 kit

# =============================================================================
# 常量定义
# =============================================================================

LINE_WIDTH = 60
LINE_GAP = 12
LINE_HEIGHT = 10
YIN_GAP = 8  # 阴爻中间缺口宽度

SVG_HEADER = '''<svg xmlns="http://www.w3.org/2000/svg" {attrs}>
<style>
  .hex-title {{ font: bold 14px "Microsoft YaHei", sans-serif; fill: #333; }}
  .hex-sub {{ font: 11px "Microsoft YaHei", sans-serif; fill: #666; }}
  .yang-line {{ stroke: #1a1a1a; stroke-width: 6; stroke-linecap: round; }}
  .yin-line-l {{ stroke: #1a1a1a; stroke-width: 6; stroke-linecap: round; }}
  .yin-line-r {{ stroke: #1a1a1a; stroke-width: 6; stroke-linecap: round; }}
  .moving-marker {{ fill: #d32f2f; }}
  .world-mark {{ fill: #1565c0; font: bold 12px sans-serif; }}
  .response-mark {{ fill: #2e7d32; font: bold 12px sans-serif; }}
  .changed-line {{ stroke: #d32f2f; stroke-width: 2; stroke-dasharray: 4,3; }}
  .ghost {{ fill: none; stroke: #999; stroke-width: 1; }}
</style>
'''

# 分析项中文名映射
ANALYSIS_CN_NAMES = {
    "hidden_spirit_analysis": "伏藏分析",
    "hidden_movement": "暗动分析",
    "soul_hexagram": "游魂归魂",
    "monthly_break": "月破分析",
    "triple_combo": "三合局",
    "advance_retreat": "进退神",
    "twelve_growth": "十二长生",
    "clash_harmony": "六合六冲",
    "repetition": "反吟伏吟",
    "repetition_deep": "伏吟反吟精析",
    "hexagram_body": "卦身分析",
    "element_strength": "五行旺衰",
    "three_punishments": "三刑分析",
    "hidden_spirit_scoring": "伏神得出",
    "day_month_bonding": "日月合用",
    "six_breaks": "六破分析",
    "desperate_relief": "绝处逢生",
    "officer_tomb": "随官入墓",
    "transformation_pattern": "动变格局",
    "flying_hidden_interaction": "飞伏互动",
    "nayin": "纳音分析",
    "classical_quotes": "经典引述",
    "hexagram_body_note": "卦身备注",
    "section_advice": "趋避建议",
}

# 分析项中文描述（当无法从数据中提取摘要时使用）
ANALYSIS_CN_DESC = {
    "hidden_spirit_analysis": "分析卦中是否有伏藏之爻（即本卦缺失的六亲需从本宫首卦借取）",
    "hidden_movement": "分析是否有旺相之爻被日辰冲动（暗动），虽无动爻之象而有动爻之实",
    "soul_hexagram": "判断本卦是否为游魂卦或归魂卦，游魂主漂泊不定，归魂主回归安定",
    "monthly_break": "检查是否有爻的地支与月建相冲（月破），月破之爻力量大损",
    "triple_combo": "检查是否形成三合局（寅午戌合火、巳酉丑合金、申子辰合水、亥卯未合木）",
    "advance_retreat": "分析动爻是否为进退神（化进则力量增长，化退则力量衰减）",
    "twelve_growth": "以日辰为基准，看各爻处于十二长生（长生→沐浴→冠带→临官→帝旺→衰→病→死→墓→绝→胎→养）何位",
    "clash_harmony": "判断卦象属于六合卦（稳定绵长）还是六冲卦（动荡分散），并列出爻位间的冲合关系",
    "repetition": "判断是否有反吟（卦变冲）或伏吟（卦变相同），主动荡不安或反复纠结",
    "repetition_deep": "深入分析反吟伏吟的具体表现和影响程度",
    "hexagram_body": "确定卦身位置（卦占事的本体），以阴阳世应起卦身",
    "element_strength": "基于月建、日辰综合评定五行旺相休囚死，给出各爻力量评分",
    "three_punishments": "检查三刑（寅巳申无恩刑、丑戌未恃势刑、子卯无礼刑、辰午酉亥自刑）",
    "hidden_spirit_scoring": "详细评估伏神是否得出（飞伏神的生克关系），得出为吉凶有应",
    "day_month_bonding": "分析用神/忌神是否与月建或日辰形成六合，合则有力、牵绊",
    "six_breaks": "检查六破（子酉破、午卯破、巳申破、寅亥破、辰丑破、戌未破），破则力损",
    "desperate_relief": "绝地逢生——用神绝地时若得原神来生，凶中反吉",
    "officer_tomb": "随官入墓——世用同临官鬼之墓，病讼最凶",
    "transformation_pattern": "分析动爻是否构成特殊格局（归妹、无妄、夷旅、蹇艮等动变组合规律）",
    "flying_hidden_interaction": "分析伏神与飞神之间的五行生克关系",
    "nayin": "六十甲子纳音五行与卦爻的关系",
}

# severity → 中文
SEVERITY_CN = {
    "high": "重", "medium": "中", "low": "轻",
    "severe": "极重", "mild": "轻微",
    "active": "显著", "inactive": "静",
    "complete": "完整", "partial": "半成",
    "strong": "强", "weak": "弱",
}

COLORS = {
    "金": "#FFD700",
    "木": "#228B22",
    "水": "#1E90FF",
    "火": "#FF4500",
    "土": "#8B4513",
    "yang": "#1a1a1a",
    "yin": "#444",
}

PALACE_ORDER = ["乾", "坎", "艮", "震", "巽", "离", "坤", "兑"]


# =============================================================================
# 1. 卦盘图 (Hexagram Diagram)
# =============================================================================

def draw_yao_line(x, y, yang=True, moving=False):
    """生成单爻 SVG 元素"""
    elems = []
    if yang:
        elems.append(
            f'<line x1="{x}" y1="{y}" x2="{x+LINE_WIDTH}" y2="{y}" class="yang-line"/>'
        )
    else:
        mid = x + LINE_WIDTH / 2
        elems.append(
            f'<line x1="{x}" y1="{y}" x2="{mid-YIN_GAP}" y2="{y}" class="yin-line-l"/>'
        )
        elems.append(
            f'<line x1="{mid+YIN_GAP}" y1="{y}" x2="{x+LINE_WIDTH}" y2="{y}" class="yin-line-r"/>'
        )
    if moving:
        # 动爻标记：阳动标○，阴动标×
        symbol = "○" if yang else "×"
        cx = x + LINE_WIDTH + 14
        elems.append(
            f'<text x="{cx}" y="{y+4}" class="moving-marker" font-size="16" font-weight="bold">{symbol}</text>'
        )
    return "\n".join(elems)


def draw_single_hexagram(hex_data, cx, cy, title=None, show_labels=True):
    """绘制单个卦象 SVG 组"""
    lines = hex_data.get("yao_lines", [])
    if not lines:
        return ""

    # 从下往上画（初爻在下 → 上爻在上）
    drawn_lines = list(reversed(lines))

    total_h = 6 * LINE_HEIGHT + 5 * LINE_GAP
    start_x = cx - LINE_WIDTH / 2
    start_y = cy + total_h / 2 - LINE_HEIGHT / 2

    svg_parts = [f'<g class="hexagram" transform="translate({start_x:.0f},{start_y:.0f})">']

    # 标题
    if title:
        svg_parts.append(
            f'<text x="{LINE_WIDTH/2}" y="-20" text-anchor="middle" class="hex-title">{html.escape(title)}</text>'
        )

    # 绘制六爻
    for i, yao in enumerate(drawn_lines):
        y_pos = i * (LINE_HEIGHT + LINE_GAP)
        yang = yao.get("nature") == "yang"
        moving = yao.get("is_moving", False)
        svg_parts.append(draw_yao_line(80, y_pos, yang, moving))

        if show_labels:
            # 右侧标注：六亲/地支/世应/空亡
            markers = []
            if yao.get("is_world"):
                markers.append(("世", "world-mark"))
            if yao.get("is_response"):
                markers.append(("应", "response-mark"))
            branch = yao.get("earthly_branch", "")
            relation = yao.get("six_relation", "")
            spirit = yao.get("six_spirit", "")
            if branch or relation:
                label = f"{spirit}{relation}{branch}"
                if yao.get("is_empty"):
                    label += "(空)"
                svg_parts.append(
                    f'<text x="{LINE_WIDTH+96}" y="{y_pos+4}" class="hex-sub">{html.escape(label)}</text>'
                )
            for j, (mk, cls) in enumerate(markers):
                svg_parts.append(
                    f'<text x="{LINE_WIDTH+96+len(label)*11 if branch or relation else 80 + j*16}" y="{y_pos+4}" class="{cls}">{mk}</text>'
                )

    svg_parts.append("</g>")
    return "\n".join(svg_parts)


def generate_hexagram_diagram(result_data, width=700, height=500):
    """生成本卦 + 变卦并列的卦象图"""
    orig = result_data.get("original_hexagram", {})
    changed = result_data.get("changed_hexagram")

    svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%">']
    svg_parts.append(
        '<style>'
        '.hex-title{font:bold 14px "Microsoft YaHei",sans-serif;fill:#333}'
        '.hex-sub{font:11px "Microsoft YaHei",sans-serif;fill:#666}'
        '.yang-line{stroke:#1a1a1a;stroke-width:6;stroke-linecap:round}'
        '.yin-line-l,.yin-line-r{stroke:#1a1a1a;stroke-width:6;stroke-linecap:round}'
        '.moving-marker{fill:#d32f2f;font:bold 16px sans-serif}'
        '.world-mark{fill:#1565c0;font:bold 12px sans-serif}'
        '.response-mark{fill:#2e7d32;font:bold 12px sans-serif}'
        '</style>'
    )

    # 本卦（左）
    orig_name = orig.get("name", "?")
    orig_palace = orig.get("palace", "?")
    orig_gen = orig.get("generation", "?")
    title_l = f"本卦：{orig_name}（{orig_palace}宫 {orig_gen}）"

    # 画本卦 — 从下往上
    lines_l = list(reversed(orig.get("yao_lines", [])))
    start_x_l = 60
    start_y_l = 60

    svg_parts.append(f'<text x="180" y="30" text-anchor="middle" class="hex-title">{html.escape(title_l)}</text>')
    for i, yao in enumerate(lines_l):
        y_pos = start_y_l + i * (LINE_HEIGHT + LINE_GAP)
        yang = yao.get("nature") == "yang"
        moving = yao.get("is_moving", False)
        # 画爻
        if yang:
            svg_parts.append(f'<line x1="{start_x_l}" y1="{y_pos}" x2="{start_x_l+LINE_WIDTH}" y2="{y_pos}" class="yang-line"/>')
        else:
            mid = start_x_l + LINE_WIDTH / 2
            svg_parts.append(f'<line x1="{start_x_l}" y1="{y_pos}" x2="{mid-YIN_GAP}" y2="{y_pos}" class="yin-line-l"/>')
            svg_parts.append(f'<line x1="{mid+YIN_GAP}" y1="{y_pos}" x2="{start_x_l+LINE_WIDTH}" y2="{y_pos}" class="yin-line-r"/>')
        # 动爻符号
        if moving:
            symbol = "○" if yang else "×"
            svg_parts.append(f'<text x="{start_x_l+LINE_WIDTH+14}" y="{y_pos+4}" class="moving-marker">{symbol}</text>')
        # 标注
        label_parts = []
        if yao.get("is_world"):
            label_parts.append('<tspan class="world-mark">世</tspan>')
        if yao.get("is_response"):
            label_parts.append('<tspan class="response-mark">应</tspan>')
        spirit = html.escape(yao.get("six_spirit", ""))
        relation = html.escape(yao.get("six_relation", ""))
        branch = html.escape(yao.get("earthly_branch", ""))
        empty_mark = "(空)" if yao.get("is_empty") else ""
        text_label = f"{spirit}{relation}{branch}{empty_mark}"
        svg_parts.append(
            f'<text x="{start_x_l+LINE_WIDTH+44}" y="{y_pos+4}" class="hex-sub">{"".join(label_parts)} {text_label}</text>'
        )

    # 变卦（右）
    if changed:
        changed_name = changed.get("name", "?")
        svg_parts.append(f'<text x="520" y="30" text-anchor="middle" class="hex-title">变卦：{html.escape(changed_name)}</text>')
        changed_positions = set(changed.get("changed_lines", []))
        start_x_r = 420
        for i, yao in enumerate(lines_l):
            pos = 6 - i  # position 1-6 from bottom
            y_pos = start_y_l + i * (LINE_HEIGHT + LINE_GAP)
            if pos in changed_positions:
                # 变后的阴阳
                old_yang = yao.get("nature") == "yang"
                yang = not old_yang  # 阴阳互变
            else:
                yang = yao.get("nature") == "yang"
            if yang:
                svg_parts.append(f'<line x1="{start_x_r}" y1="{y_pos}" x2="{start_x_r+LINE_WIDTH}" y2="{y_pos}" class="yang-line"/>')
            else:
                mid = start_x_r + LINE_WIDTH / 2
                svg_parts.append(f'<line x1="{start_x_r}" y1="{y_pos}" x2="{mid-YIN_GAP}" y2="{y_pos}" class="yin-line-l"/>')
                svg_parts.append(f'<line x1="{mid+YIN_GAP}" y1="{y_pos}" x2="{start_x_r+LINE_WIDTH}" y2="{y_pos}" class="yin-line-r"/>')
            if pos in changed_positions:
                svg_parts.append(
                    f'<rect x="{start_x_r-2}" y="{y_pos-8}" width="{LINE_WIDTH+4}" height="20" fill="none" stroke="#d32f2f" stroke-width="1.5" stroke-dasharray="3,2" rx="2"/>'
                )
                # 本卦原爻（虚线示意）
                old_yang2 = yao.get("nature") == "yang"
                col = "#aaa"
                if old_yang2:
                    svg_parts.append(f'<line x1="{start_x_r}" y1="{y_pos-2}" x2="{start_x_r+LINE_WIDTH}" y2="{y_pos-2}" stroke="{col}" stroke-width="2" stroke-dasharray="3,3" opacity="0.6"/>')
                else:
                    mid = start_x_r + LINE_WIDTH / 2
                    svg_parts.append(f'<line x1="{start_x_r}" y1="{y_pos-2}" x2="{mid-YIN_GAP}" y2="{y_pos-2}" stroke="{col}" stroke-width="2" stroke-dasharray="3,3" opacity="0.6"/>')
                    svg_parts.append(f'<line x1="{mid+YIN_GAP}" y1="{y_pos-2}" x2="{start_x_r+LINE_WIDTH}" y2="{y_pos-2}" stroke="{col}" stroke-width="2" stroke-dasharray="3,3" opacity="0.6"/>')

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


# =============================================================================
# 2. 五行力量雷达图
# =============================================================================

def generate_element_radar(result_data, size=400):
    """根据 advanced_analysis.element_strength 生成五行雷达图"""
    aa = result_data.get("advanced_analysis", {})
    es = aa.get("element_strength", {})
    details = es.get("details", [])

    # 收集五行强度
    elem_scores = {"金": 0.5, "木": 0.5, "水": 0.5, "火": 0.5, "土": 0.5}
    for d in details:
        el = d.get("five_element", "")
        score = d.get("effective_score", d.get("score", 0.5))
        if el in elem_scores:
            # 取该五行中最高分者为主体
            if score > elem_scores[el]:
                elem_scores[el] = min(score, 6.0) / 6.0  # normalize to 0-1

    # 也使用 summary
    summary = es.get("summary", "")
    # fallback: equal

    cx, cy = size // 2, size // 2
    radius = size // 2 - 50
    n = 5  # 五角

    svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="100%">']
    svg_parts.append(
        '<style>'
        '.radar-label{font:13px "Microsoft YaHei",sans-serif;fill:#333;text-anchor:middle}'
        '.radar-grid{stroke:#ccc;stroke-width:1;fill:none}'
        '.radar-area{fill:rgba(30,144,255,0.2);stroke:#1E90FF;stroke-width:2}'
        '.radar-dot{fill:#1E90FF}'
        '</style>'
    )

    # 顶点位置（金→木→水→火→土，五行正序）
    # 常规五角排列从顶部顺时针
    order = ["金", "水", "木", "火", "土"]
    angles = []
    for i in range(n):
        angle = -90 + i * (360 / n)  # 从顶部开始
        rad = math.radians(angle)
        angles.append((cx + radius * math.cos(rad), cy + radius * math.sin(rad)))

    # 网格线
    for level in [0.25, 0.5, 0.75, 1.0]:
        pts = []
        for i in range(n):
            angle = -90 + i * (360 / n)
            rad = math.radians(angle)
            r = radius * level
            pts.append(f"{cx + r * math.cos(rad):.1f},{cy + r * math.sin(rad):.1f}")
        svg_parts.append(f'<polygon points="{" ".join(pts)}" class="radar-grid"/>')

    # 轴
    for i in range(n):
        svg_parts.append(f'<line x1="{cx}" y1="{cy}" x2="{angles[i][0]:.1f}" y2="{angles[i][1]:.1f}" class="radar-grid"/>')

    # 数据多边形
    data_pts = []
    for i, el in enumerate(order):
        val = elem_scores.get(el, 0.5)
        r = radius * val
        angle = -90 + i * (360 / n)
        rad = math.radians(angle)
        px = cx + r * math.cos(rad)
        py = cy + r * math.sin(rad)
        data_pts.append(f"{px:.1f},{py:.1f}")
        # 颜色标注
        dot_col = COLORS.get(el, "#1E90FF")
        svg_parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="{dot_col}"/>')

    svg_parts.append(f'<polygon points="{" ".join(data_pts)}" class="radar-area"/>')

    # 文字标签
    for i, el in enumerate(order):
        tx, ty = angles[i]
        ofs = 18
        if ty < cy: ty -= ofs
        elif ty > cy: ty += ofs + 4
        else: ty += 4
        if tx < cx: tx -= ofs
        elif tx > cx: tx += ofs
        col = COLORS.get(el, "#333")
        val = elem_scores.get(el, 0.5)
        svg_parts.append(
            f'<text x="{tx:.0f}" y="{ty:.0f}" class="radar-label" fill="{col}">{el}({val:.0%})</text>'
        )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


# =============================================================================
# 3. 动变对比柱状图
# =============================================================================

def generate_change_comparison(result_data, width=650, height=300):
    """动变净效应柱状图"""
    chain = result_data.get("thinking_chain", {})
    step4 = chain.get("step4_change_analysis", {})
    raw_changes = step4.get("details", [])
    changes = []
    for d in raw_changes:
        changes.append({
            "position": d.get("position", 0),
            "effect_score": d.get("effect_score", d.get("net_effect", 0)),
            "description": d.get("name", "") + " " + d.get("change_type", d.get("advance_type", "")),
        })

    svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%">']
    svg_parts.append(
        '<style>'
        '.bar-label{font:12px "Microsoft YaHei",sans-serif;fill:#333;}'
        '.bar-value{font:11px "Microsoft YaHei",sans-serif;fill:#555;text-anchor:middle}'
        '.axis{stroke:#999;stroke-width:1}'
        '</style>'
    )

    bar_h = 22
    gap = 8
    left_m = 120
    right_m = 60
    bar_max_w = width - left_m - right_m
    baseline_y = height - 40
    zero_x = left_m + bar_max_w / 2
    scale = bar_max_w / 4.0  # ±2 分映射到半宽

    # 基线
    svg_parts.append(f'<line x1="{left_m}" y1="{baseline_y}" x2="{width-right_m}" y2="{baseline_y}" class="axis"/>')
    svg_parts.append(f'<line x1="{zero_x}" y1="15" x2="{zero_x}" y2="{height-10}" stroke="#bbb" stroke-width="0.5" stroke-dasharray="3,3"/>')

    if not changes:
        svg_parts.append(
            f'<text x="{width/2}" y="{height/2}" text-anchor="middle" class="bar-label" fill="#999">无动爻</text>'
        )
    else:
        for i, ch in enumerate(changes[:6]):
            pos = ch.get("position", i+1)
            effect = ch.get("effect_score", 0)
            desc = ch.get("description", f"第{pos}爻动")

            y = 20 + i * (bar_h + gap)
            bar_x = zero_x + effect * scale
            bar_w = abs(effect) * scale
            col = "#2e7d32" if effect >= 0 else "#d32f2f"

            svg_parts.append(f'<text x="{left_m-8}" y="{y+bar_h/2+4}" text-anchor="end" class="bar-label">{html.escape(desc[:10])}</text>')
            svg_parts.append(f'<rect x="{min(zero_x, bar_x):.1f}" y="{y}" width="{bar_w:.1f}" height="{bar_h}" fill="{col}" rx="3" opacity="0.8"/>')
            svg_parts.append(f'<text x="{bar_x:.1f}" y="{y+bar_h/2+4}" class="bar-value" fill="white" font-weight="bold">{effect:+.2f}</text>')

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


# =============================================================================
# 4. 应期时间线
# =============================================================================

def render_yingqi_table(result_data):
    """主/次应期表：应支 + 所本法则 + 最近的日历日。

    应期是当事人唯一能据以行动的输出，所以每条都必须说清"凭什么推出这一天"，
    并且给日历日期而非"近期"。法则缺失时宁可留白，也不编一个听起来顺的理由。
    """
    chain = result_data.get("thinking_chain", {}) or {}
    step5 = chain.get("step5_synthesis", {}) or {}
    timing = step5.get("timing", {}) or {}
    rules = timing.get("timing_rules") or []
    raw_dates = step5.get("yingqi_dates") or {}
    dates = raw_dates.get("dates", []) if isinstance(raw_dates, dict) else raw_dates
    by_branch = {}
    for d in dates or []:
        if isinstance(d, dict) and d.get("branch") and d["branch"] not in by_branch:
            by_branch[d["branch"]] = d

    if not rules and not by_branch:
        return '<p style="font-size:13px;color:#8a8175;">此卦难以定单一应期，以用神旺衰断迟速。</p>'

    labels = ["主应期", "次应期", "备选", "备选"]
    head = ("<tr><th style='text-align:left;padding:6px 10px;border-bottom:1px solid #e0d8c8;'>层次</th>"
            "<th style='text-align:left;padding:6px 10px;border-bottom:1px solid #e0d8c8;'>应支</th>"
            "<th style='text-align:left;padding:6px 10px;border-bottom:1px solid #e0d8c8;'>所本法则</th>"
            "<th style='text-align:left;padding:6px 10px;border-bottom:1px solid #e0d8c8;'>最近之日</th></tr>")
    rows = []
    seen = set()
    for i, item in enumerate((rules or [])[:4]):
        token, rule = (item if isinstance(item, (list, tuple)) and len(item) == 2
                       else (item.get("token", ""), item.get("rule", "")))
        branch = str(token)[:1]
        if not token or token in seen:
            continue
        seen.add(token)
        rec = by_branch.get(branch) or {}
        date = rec.get("date") or "候值日"
        rows.append(
            f"<tr><td style='padding:6px 10px;color:#8a6d3b;'>{labels[min(i, 3)]}</td>"
            f"<td style='padding:6px 10px;font-weight:600;'>{html.escape(str(token))}</td>"
            f"<td style='padding:6px 10px;font-size:13px;'>{html.escape(str(rule))}</td>"
            f"<td style='padding:6px 10px;font-size:13px;'>{html.escape(str(date))}</td></tr>")
    return (f"<table style='border-collapse:collapse;width:100%;margin-bottom:12px;'>{head}{''.join(rows)}</table>"
            "<p style='font-size:12px;color:#8a8175;margin:0 0 10px;'>"
            "应期是给方向的观察窗口，不是定时炸弹的倒计时；过了窗口不等于不验。</p>")


def generate_yingqi_timeline(result_data, width=650, height=200):
    """应期日期时间线"""
    chain = result_data.get("thinking_chain", {})
    step5 = chain.get("step5_synthesis", {})
    yingqi_raw = step5.get("yingqi_dates", {})
    if isinstance(yingqi_raw, dict):
        yingqi = yingqi_raw.get("dates", [])
    elif isinstance(yingqi_raw, list):
        yingqi = yingqi_raw
    else:
        yingqi = []

    svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%">']
    svg_parts.append(
        '<style>'
        '.timeline-axis{stroke:#999;stroke-width:2}'
        '.timeline-dot{fill:#1565c0}'
        '.timeline-label{font:12px "Microsoft YaHei",sans-serif;fill:#333;text-anchor:middle}'
        '.timeline-note{font:10px "Microsoft YaHei",sans-serif;fill:#666;text-anchor:middle}'
        '</style>'
    )

    axis_y = height // 2
    svg_parts.append(f'<line x1="40" y1="{axis_y}" x2="{width-40}" y2="{axis_y}" class="timeline-axis"/>')

    # 起卦日标记
    dt = result_data.get("divination_time", {})
    dt_str = dt.get("datetime", "")
    svg_parts.append(f'<circle cx="40" cy="{axis_y}" r="6" fill="#333"/>')
    svg_parts.append(f'<text x="40" y="{axis_y+20}" class="timeline-note">{html.escape(dt_str[:10])}</text>')
    svg_parts.append(f'<text x="40" y="{axis_y-14}" class="timeline-label">起卦</text>')

    if yingqi:
        usable_w = width - 120
        count = len(yingqi)
        for i, yq in enumerate(yingqi[:8]):
            date_str = yq.get("date", yq.get("branch", ""))
            desc = yq.get("description", yq.get("meaning", ""))
            confidence = yq.get("confidence", 0.5 + 0.5 * (1 - i / max(count, 1)))

            ratio = (i + 1) / max(count, 1)
            x = 40 + usable_w * ratio
            dot_r = 6 * confidence + 3
            col = "#2e7d32" if confidence > 0.7 else ( "#f57f17" if confidence > 0.4 else "#d32f2f")

            svg_parts.append(f'<circle cx="{x:.0f}" cy="{axis_y}" r="{dot_r:.1f}" fill="{col}"/>')
            svg_parts.append(f'<text x="{x:.0f}" y="{axis_y-14}" class="timeline-label">{html.escape(str(date_str))}</text>')
            if desc:
                svg_parts.append(f'<text x="{x:.0f}" y="{axis_y+20}" class="timeline-note">{html.escape(str(desc)[:15])}</text>')
    else:
        svg_parts.append(f'<text x="{width/2}" y="{axis_y-14}" class="timeline-label" fill="#999">暂无明确应期推断</text>')

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


# =============================================================================
# 5. 五行生克流转图
# =============================================================================

def generate_five_elements_flow(width=360, height=360):
    """五行相生(外圈)相克(内五角星)流转图"""
    cx, cy = width // 2, height // 2
    R = 130  # 外圈半径
    r_inner = 50  # 内星半径

    order = ["木", "火", "土", "金", "水"]  # 相生序
    angles = []
    for i in range(5):
        angle = -90 + i * 72  # 从顶部顺时针
        rad = math.radians(angle)
        angles.append((cx + R * math.cos(rad), cy + R * math.sin(rad), rad))

    svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%">']
    svg_parts.append(
        '<style>'
        '.elem-label{font:bold 16px "Microsoft YaHei",sans-serif;text-anchor:middle;fill:#333}'
        '.elem-hz{font:10px "Microsoft YaHei",sans-serif;text-anchor:middle;fill:#888}'
        '.gen-line{stroke:#2e7d2e;stroke-width:2;fill:none;marker-end:url(#arrow-gen)}'
        '.ke-line{stroke:#d32f2f;stroke-width:2;fill:none;marker-end:url(#arrow-ke)}'
        '</style>'
        '<defs>'
        '<marker id="arrow-gen" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
        '<path d="M0,0 L10,5 L0,10 z" fill="#2e7d2e"/></marker>'
        '<marker id="arrow-ke" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
        '<path d="M0,0 L10,5 L0,10 z" fill="#d32f2f"/></marker>'
        '</defs>'
    )

    # 相生圈（五边形连线）
    for i in range(5):
        j = (i + 1) % 5
        x1, y1 = angles[i][0], angles[i][1]
        x2, y2 = angles[j][0], angles[j][1]
        svg_parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="gen-line"/>')
        # 相生标签
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        svg_parts.append(f'<text x="{mid_x:.0f}" y="{mid_y:.0f}" class="elem-hz" fill="#2e7d2e">生</text>')

    # 相克线（五角星）
    ke_pairs = [(0,2), (2,4), (4,1), (1,3), (3,0)]  # 木→土→水→火→金→木
    for a, b in ke_pairs:
        x1, y1 = angles[a][0], angles[a][1]
        x2, y2 = angles[b][0], angles[b][1]
        svg_parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="ke-line"/>')
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        svg_parts.append(f'<text x="{mid_x:.0f}" y="{mid_y:.0f}" class="elem-hz" fill="#d32f2f">克</text>')

    # 五行圆点和标签
    gen_hz = {"木": "东/春", "火": "南/夏", "土": "中", "金": "西/秋", "水": "北/冬"}
    for i, el in enumerate(order):
        x, y = angles[i][0], angles[i][1]
        col = COLORS.get(el, "#333")
        svg_parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="26" fill="white" stroke="{col}" stroke-width="2.5"/>')
        svg_parts.append(f'<text x="{x:.0f}" y="{y+5}" class="elem-label" fill="{col}">{el}</text>')
        svg_parts.append(f'<text x="{x:.0f}" y="{y+18}" class="elem-hz">{gen_hz.get(el, "")}</text>')

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


# =============================================================================
# 6. 八宫归属图
# =============================================================================

def generate_palace_map(highlight_palace=None, width=560, height=560):
    """八宫 8×8 归属矩阵，高亮当前卦所在宫"""
    # 八卦五行对应
    bagua_elem = {
        "乾": "金", "坤": "土", "震": "木", "巽": "木",
        "坎": "水", "离": "火", "艮": "土", "兑": "金",
    }
    cell_w = 60
    cell_h = 56
    pad_x = 70
    pad_y = 30

    svg_w = pad_x + 8 * cell_w + 10
    svg_h = pad_y + 8 * cell_h + 20

    svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%">']
    svg_parts.append(
        '<style>'
        '.palace-label{font:bold 13px "Microsoft YaHei",sans-serif;fill:#333;text-anchor:middle}'
        '.hex-cell{font:10px "Microsoft YaHei",sans-serif;fill:#444;text-anchor:middle}'
        '.cell-bg{fill:#fafafa;stroke:#ddd;stroke-width:0.8}'
        '.cell-highlight{fill:#fff3e0;stroke:#ff9800;stroke-width:2}'
        '.gen-tag{font:9px "Microsoft YaHei",sans-serif;fill:#999;text-anchor:middle}'
        '</style>'
    )

    # 简化：每宫6-8卦的标记（用世序数字）
    generations = ["六世", "一世", "二世", "三世", "四世", "五世", "游魂", "归魂"]

    for row_i, palace in enumerate(PALACE_ORDER):
        y = pad_y + row_i * cell_h
        is_highlight = (palace == highlight_palace)
        col = COLORS.get(bagua_elem.get(palace, ""), "#333")

        # 宫名列
        svg_parts.append(f'<text x="{pad_x-8}" y="{y+cell_h/2+4}" text-anchor="end" class="palace-label" fill="{col}">{palace}</text>')

        for gen_i in range(8):
            x = pad_x + gen_i * cell_w
            cell_cls = "cell-highlight" if is_highlight else "cell-bg"
            svg_parts.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" class="{cell_cls}" rx="3"/>')
            svg_parts.append(f'<text x="{x+cell_w/2}" y="{y+cell_h/2+3}" class="gen-tag">{generations[gen_i]}</text>')

    title = "八宫归属图"
    if highlight_palace:
        title += f"（{highlight_palace}宫高亮）"
    svg_parts.append(f'<text x="{svg_w/2}" y="{svg_h-5}" text-anchor="middle" class="palace-label">{html.escape(title)}</text>')

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


# =============================================================================
# 7. 批量对比可视化
# =============================================================================

def generate_batch_comparison(results_json, width=900, height=500):
    """多个排盘结果对比"""
    if not isinstance(results_json, list):
        results_json = [results_json]

    svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%">']
    svg_parts.append(
        '<style>'
        '.batch-label{font:12px "Microsoft YaHei",sans-serif;fill:#333}'
        '.batch-score{font:bold 14px "Microsoft YaHei",sans-serif;text-anchor:middle}'
        '.batch-bar-bg{stroke:#eee;stroke-width:14}'
        '</style>'
    )

    n = len(results_json)
    bar_h = min(30, (height - 60) / max(n, 1) - 6)
    left_m = 200
    right_m = 80
    bar_max = width - left_m - right_m
    zero_x = left_m + bar_max / 2
    scale = bar_max / 4.0

    for i, res in enumerate(results_json[:15]):
        y = 30 + i * (bar_h + 12)
        chain = res.get("thinking_chain", {})
        step5 = chain.get("step5_synthesis", {})
        verdict = step5.get("verdict", "?")
        score = step5.get("final_score", 0)

        orig = res.get("original_hexagram", {})
        hex_name = orig.get("name", "?")
        q = res.get("question", "")
        label = f"{hex_name}（{q[:12]}）"

        col = "#2e7d32" if score > 2 else ("#d32f2f" if score < 0 else "#f57f17")

        svg_parts.append(f'<text x="{left_m-8}" y="{y+bar_h/2+4}" text-anchor="end" class="batch-label">{html.escape(label)}</text>')
        svg_parts.append(f'<rect x="{left_m}" y="{y}" width="{bar_max}" height="{bar_h}" rx="4" fill="#f5f5f5"/>')

        bar_x = zero_x + score * scale
        bar_w = abs(score) * scale
        svg_parts.append(f'<rect x="{min(zero_x,bar_x):.1f}" y="{y}" width="{bar_w:.1f}" height="{bar_h}" rx="4" fill="{col}" opacity="0.8"/>')
        svg_parts.append(f'<text x="{bar_x:.1f}" y="{y+bar_h/2+4}" class="batch-score" fill="white">{score:.2f}</text>')
        svg_parts.append(f'<text x="{width-right_m+5}" y="{y+bar_h/2+4}" class="batch-label">{html.escape(verdict)}</text>')

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


# =============================================================================
# 8. 历史日志统计图
# =============================================================================

def generate_history_stats(events_json, width=700, height=400):
    """历史占卜日志统计"""
    if not isinstance(events_json, list):
        events_json = [events_json]

    verdicts = {}
    hours = {}
    palaces = {}
    total = len(events_json)

    for ev in events_json:
        v = ev.get("verdict", "未知")
        verdicts[v] = verdicts.get(v, 0) + 1
        h = ev.get("hour", 12)
        hours[h] = hours.get(h, 0) + 1
        p = ev.get("palace", "?")
        palaces[p] = palaces.get(p, 0) + 1

    svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%">']
    svg_parts.append(
        '<style>'
        '.stat-label{font:11px "Microsoft YaHei",sans-serif;fill:#333;text-anchor:middle}'
        '.stat-value{font:bold 12px "Microsoft YaHei",sans-serif;fill:white;text-anchor:middle}'
        '.stat-title{font:bold 14px "Microsoft YaHei",sans-serif;fill:#222;text-anchor:middle}'
        '</style>'
    )

    # 左侧：结论分布
    left_x = 30
    left_w = 200
    left_y = 60
    bar_h = 20
    svg_parts.append(f'<text x="{left_x+left_w/2}" y="40" class="stat-title">结论分布（共{total}次）</text>')
    v_colors = {"吉": "#2e7d32", "大吉": "#1b5e20", "中平": "#f57f17", "平凶": "#e65100", "凶": "#d32f2f", "大凶": "#b71c1c"}
    for i, (v, cnt) in enumerate(sorted(verdicts.items(), key=lambda x: -x[1])[:8]):
        y = left_y + i * (bar_h + 5)
        pct = cnt / total
        w = left_w * pct
        col = v_colors.get(v, "#757575")
        svg_parts.append(f'<rect x="{left_x}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="3" fill="{col}"/>')
        svg_parts.append(f'<text x="{left_x+w+5}" y="{y+bar_h/2+4}" class="stat-label" fill="#333" text-anchor="start">{v}: {cnt}({pct:.0%})</text>')

    # 右侧：时辰分布
    right_x = 300
    right_w = 200
    svg_parts.append(f'<text x="{right_x+right_w/2}" y="40" class="stat-title">时辰分布</text>')
    max_h = max(hours.values()) if hours else 1
    for h in range(24):
        cnt = hours.get(h, 0)
        if cnt == 0:
            continue
        col_idx = h % 12
        bins = 12
        bin_w = right_w / bins
        bin_h = cnt / max_h * 180
        bx = right_x + (col_idx * bin_w)
        by = 60 + 180 - bin_h
        svg_parts.append(f'<rect x="{bx+2}" y="{by:.1f}" width="{bin_w-4}" height="{bin_h:.1f}" rx="2" fill="#1E90FF" opacity="0.7"/>')
        svg_parts.append(f'<text x="{bx+bin_w/2}" y="250" class="stat-label">{col_idx}</text>')

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


# =============================================================================
# 卦辞/爻辞数据加载
# =============================================================================

_hex_data_cache = None

def _load_hexagram_data():
    """加载并缓存 hexagrams.json（卦辞/象传/爻辞数据）"""
    global _hex_data_cache
    if _hex_data_cache is not None:
        return _hex_data_cache
    _hex_data_cache = {}
    candidates = [
        Path(__file__).parent.parent / "data" / "hexagrams.json",
        Path(__file__).parent.parent.parent / "skills" / "liu-yao" / "data" / "hexagrams.json",
    ]
    for path in candidates:
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    raw = json.load(f)
                hexs = raw.get("hexagrams", raw) if isinstance(raw, dict) else raw
                for h in hexs:
                    name = h.get("name", "")
                    if name:
                        _hex_data_cache[name] = h
                break
            except (json.JSONDecodeError, OSError):
                pass
    return _hex_data_cache


def _get_hex_text(result_data):
    """获取本卦和变卦的卦辞/爻辞数据"""
    data = _load_hexagram_data()
    orig_name = result_data.get("original_hexagram", {}).get("name", "")
    changed = result_data.get("changed_hexagram", {})
    changed_name = changed.get("name", "") if changed else {}
    moving_positions = set()
    for y in result_data.get("original_hexagram", {}).get("yao_lines", []):
        if y.get("is_moving"):
            moving_positions.add(y.get("position", 0))
    return {
        "original": data.get(orig_name, {}),
        "changed": data.get(changed_name, {}) if changed_name else {},
        "moving_positions": moving_positions,
    }


# =============================================================================
# HTML 报告组装
# =============================================================================

def _extract_analysis_text(val):
    """从分析数据中提取人类可读的中文摘要"""
    if isinstance(val, dict):
        # 优先使用 summary/interpretation/description/summary_text/meaning
        for field in ("summary", "interpretation", "description", "summary_text", "meaning"):
            text = val.get(field)
            if isinstance(text, str) and text.strip():
                return text[:200]
        # 处理 boolean flag + 专有字段的组合
        if val.get("is_soul_hexagram") is True:
            return val.get("summary") or f"游魂归魂卦——{val.get('meaning', '')}"
        if val.get("has_desperate_relief") is True:
            return f"绝处逢生——用神在{val.get('stage','')}处，原神{'发动' if val.get('yuan_shen_moving') else '不动'}，{val.get('verdict','')}"
        if val.get("has_desperate_relief") is False:
            return "用神未绝地，不涉及绝处逢生"
        if val.get("has_interaction") is False:
            return "飞伏之间无生克互动"
        if val.get("type") is None and val.get("interpretation") == "" and "score_modifier" in val:
            return None  # 无相关特征时不显示
        # 尝试拼接关键信息
        parts = []
        if val.get("has_punishment"):
            names = [f"{p.get('type','')}({p.get('completeness','')})" for p in val.get("punishments", [])]
            if names: parts.append("：".join(names))
        if val.get("is_soul_hexagram"):
            parts.append(f"类型：{val.get('soul_type','')}")
        if val.get("has_monthly_break"):
            details = val.get("details", [])
            if details:
                parts.append("月破爻位：" + ",".join(str(d.get("position","?")) for d in details[:3]))
        if val.get("hexagram_type"):
            parts.append(val["hexagram_type"])
        if parts:
            return "，".join(parts)[:200]
        return None
    elif isinstance(val, list):
        if not val:
            return None
        texts = []
        for v in val[:5]:
            if isinstance(v, str):
                texts.append(v[:80])
            elif isinstance(v, dict):
                for field in ("description", "summary", "meaning", "interpretation"):
                    if v.get(field):
                        texts.append(str(v[field])[:80])
                        break
                else:
                    texts.append(str(v)[:80])
        return "；".join(texts)[:200] if texts else None
    elif isinstance(val, str) and val.strip():
        return val[:200]
    return None


def _extract_severity(val):
    """从分析数据中提取严重程度中文"""
    if not isinstance(val, dict):
        return ""
    for field in ("severity", "level", "completeness"):
        sv = val.get(field, "")
        if sv:
            return SEVERITY_CN.get(str(sv).lower(), str(sv))
    if val.get("has_punishment"): return "有刑"
    if val.get("is_soul_hexagram"): return val.get("soul_type", "")
    if val.get("has_monthly_break"): return "有破"
    if val.get("has_triple_combo"): return "合局"
    if val.get("hexagram_type"): return val.get("hexagram_type", "")
    if val.get("has_advance_retreat"): return "有进退"
    if val.get("has_moving_lines"): return "动"
    return ""


def main():
    parser = argparse.ArgumentParser(
        description="六爻可视化组件库 — 排盘JSON → SVG 组件（卦盘/五行/宫位等）。"
                    "HTML 报告请走 render 段（单一出口）。"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # 子命令: 仅生成SVG组件（嵌入式使用）
    p4 = sub.add_parser("svg", help="生成单一SVG组件")
    p4.add_argument("--input", "-i", required=True, help="排盘JSON文件路径")
    p4.add_argument("--type", "-t", default="hexagram",
                     choices=["hexagram", "radar", "changes", "yingqi", "flow", "palace"],
                     help="SVG类型")
    p4.add_argument("--output", "-o", required=True, help="输出SVG文件路径")

    args = parser.parse_args()

    if args.command == "svg":
        with open(args.input, encoding="utf-8") as f:
            data = json.load(f)
        orig = data.get("original_hexagram", {})
        palace_name = orig.get("palace", "")

        type_map = {
            "hexagram": lambda: generate_hexagram_diagram(data),
            "radar": lambda: generate_element_radar(data),
            "changes": lambda: generate_change_comparison(data),
            "yingqi": lambda: generate_yingqi_timeline(data),
            "flow": lambda: generate_five_elements_flow(),
            "palace": lambda: generate_palace_map(highlight_palace=palace_name),
        }
        svg_out = type_map[args.type]()
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(svg_out)
        print(f"[OK] SVG ({args.type}) -> {args.output}")


if __name__ == "__main__":
    main()
