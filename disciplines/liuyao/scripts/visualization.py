#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
六爻 SVG 卦盘组件（render 段唯一图形依赖）。

历史：本模块曾是完整可视化引擎（雷达/动变/应期时间线/八宫图/批量对比/历史统计
与 HTML 报告组装）。M3.1 之后报告只从 `scripts/render.py` 出，上述生成器已无
调用方，2026-09-26 收敛为只保留本卦+变卦 SVG 卦盘。
"""
from __future__ import annotations

import html

LINE_WIDTH = 60
LINE_GAP = 12
LINE_HEIGHT = 10
YIN_GAP = 8  # 阴爻中间缺口宽度


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
                    f'<rect x="{start_x_r-2}" y="{y_pos-8}" width="{LINE_WIDTH+4}" height="20" fill="none" stroke="#d32f2f" stroke-width="1.5"/>'
                )
                # 本卦原爻（虚线示意）
                old_yang2 = yao.get("nature") == "yang"
                col = "#aaa"
                if old_yang2:
                    svg_parts.append(f'<line x1="{start_x_r}" y1="{y_pos-2}" x2="{start_x_r+LINE_WIDTH}" y2="{y_pos-2}" stroke="{col}" stroke-width="2" stroke-dasharray="4 2"/>')
                else:
                    mid = start_x_r + LINE_WIDTH / 2
                    svg_parts.append(f'<line x1="{start_x_r}" y1="{y_pos-2}" x2="{mid-YIN_GAP}" y2="{y_pos-2}" stroke="{col}" stroke-width="2" stroke-dasharray="4 2"/>')
                    svg_parts.append(f'<line x1="{mid+YIN_GAP}" y1="{y_pos-2}" x2="{start_x_r+LINE_WIDTH}" y2="{y_pos-2}" stroke="{col}" stroke-width="2" stroke-dasharray="4 2"/>')

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)
