#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一站式六爻解读 HTML 报告生成器
========================================
获取排盘结果 → 思维链 → 正文叙述 → 生成独立 HTML 文件。

用法:
    python scripts/build_html_report.py --question "投资财运" --out outputs/reports/sample.html
    python scripts/build_html_report.py --yao 7,7,8,9,7,7 --question "婚姻何时能成"
    python scripts/build_html_report.py --seed 42 --mode time --question "出行吉凶"
"""

from __future__ import annotations

import argparse
import os
import random
import re
import sys
from datetime import datetime

# 确保 scripts 目录在 path 中
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)


# ──────────────────────────────────────────────────────────────
# 1. 引擎调用：获取完整结果（含 thinking_chain + human_narrative）
# ──────────────────────────────────────────────────────────────

def run_pipeline(question: str, yao=None, seed=None, mode="time",
                 year=None, month=None, day=None, hour=None) -> dict:
    """
    调用六爻引擎，返回包含 thinking_chain 和 human_narrative 的完整字典。
    """
    import scripts.liuyao_engine as engine
    from scripts.thinking_chain import run_thinking_chain

    now = datetime.now()
    y = year or now.year
    m = month or now.month
    d = day or now.day
    h = hour if hour is not None else now.hour

    if seed is not None:
        random.seed(seed)

    if yao is not None:
        yao_values = list(yao)
        method = "手动装卦"
    elif mode == "coin":
        yao_values = engine.coin_toss()
        method = "铜钱摇卦"
    elif mode == "time":
        yao_values = engine.time_based_hexagram(y, m, d, h)
        method = "时间起卦"
    else:
        yao_values = [random.choice([6, 7, 8, 9]) for _ in range(6)]
        method = "随机起卦"

    result = engine.build_hexagram_result(
        yao_values, question, method, y, m, d, h
    )
    result = run_thinking_chain(result)

    # 生成 human_narrative
    try:
        from scripts.human_narrative import build_human_narrative
        result["human_narrative"] = build_human_narrative(result)
    except Exception as e:
        result["human_narrative"] = {"error": str(e)}

    return result


# ──────────────────────────────────────────────────────────────
# 2. SVG 瀑布图（内嵌，零外部依赖）
# ──────────────────────────────────────────────────────────────

def render_waterfall_svg(factor_contributions: list, width=600, height=280) -> str:
    """
    生成横向条形 SVG：绿=正贡献，红=负贡献，中间竖线标记零点。
    当数据缺失时返回空字符串（上层会降级到文字列表）。
    """
    if not factor_contributions:
        return ""

    # 过滤接近 0 的项
    fcs = [fc for fc in factor_contributions if abs(fc.get("score", 0)) > 0.001]
    if not fcs:
        return ""

    # 按绝对贡献度从大到小
    fcs_sorted = sorted(fcs, key=lambda x: abs(x.get("score", 0)), reverse=True)

    # 布局参数
    margin_left = 90
    margin_right = 60
    margin_top = 30
    margin_bottom = 30
    bar_height = 18
    gap = 8
    label_gap = 8

    n = len(fcs_sorted)
    plot_width = width - margin_left - margin_right
    plot_height = n * (bar_height + gap) - gap

    total_height = plot_height + margin_top + margin_bottom
    total_height = max(total_height, height)

    # 计算数据范围
    scores = [fc.get("score", 0) for fc in fcs_sorted]
    max_abs = max(abs(s) for s in scores) if scores else 1.0
    max_abs = max(max_abs, 0.5)  # 避免除零

    # 零点 x 坐标位置
    zero_x = margin_left + plot_width * 0.5

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {total_height}" '
        f'style="width:100%;max-width:{width}px;height:auto;display:block;">'
    ]

    # 背景
    svg_parts.append(
        f'<rect x="0" y="0" width="{width}" height="{total_height}" fill="none"/>'
    )

    # 零点竖线
    svg_parts.append(
        f'<line x1="{zero_x}" y1="{margin_top - 5}" x2="{zero_x}" '
        f'y2="{margin_top + plot_height + 5}" stroke="#7f8c8d" stroke-width="1" stroke-dasharray="4,2"/>'
    )

    # Y 轴刻度标签
    svg_parts.append(
        f'<text x="{margin_left - 10}" y="{margin_top - 12}" text-anchor="end" '
        f'font-size="11" fill="#7f8c8d">+</text>'
    )
    svg_parts.append(
        f'<text x="{margin_left - 10}" y="{margin_top + plot_height + 16}" text-anchor="end" '
        f'font-size="11" fill="#7f8c8d">&minus;</text>'
    )

    # 绘制每个因子条
    for i, fc in enumerate(fcs_sorted):
        score = fc.get("score", 0)
        name = fc.get("name", "")
        reason = fc.get("reason", "")

        y = margin_top + i * (bar_height + gap)

        # bar 长度按比例计算 (最大长度占 plot_width/48%)
        bar_max_len = plot_width * 0.48
        bar_len = abs(score) / max_abs * bar_max_len

        if score >= 0:
            x_start = zero_x
            fill = "#27ae60"
            text_anchor = "left"
            text_x = zero_x + bar_len + 4
        else:
            x_start = zero_x - bar_len
            fill = "#c0392b"
            text_anchor = "right"
            text_x = zero_x - bar_len - 4

        # 矩形条（圆角）
        svg_parts.append(
            f'<rect x="{x_start:.1f}" y="{y}" width="{bar_len:.1f}" height="{bar_height}" '
            f'rx="3" fill="{fill}" opacity="0.85"/>'
        )

        # Y 轴因子名（右侧对齐）
        svg_parts.append(
            f'<text x="{margin_left - label_gap}" y="{y + bar_height / 2 + 4}" '
            f'text-anchor="end" font-size="12" fill="#2c3e50" '
            f'style="font-family:\'PingFang SC\',\'Microsoft YaHei\',\'Noto Sans CJK SC\',sans-serif;">'
            f'{_xml_escape(name)}</text>'
        )

        # 分数标注
        sign = "+" if score >= 0 else ""
        svg_parts.append(
            f'<text x="{text_x:.1f}" y="{y + bar_height / 2 + 4}" '
            f'text-anchor="{text_anchor}" font-size="11" fill="{fill}" font-weight="bold">'
            f'{sign}{score:.2f}</text>'
        )

        # hover title
        svg_parts.append(
            f'<title>{_xml_escape(name)}: {sign}{score:.2f} ({_xml_escape(reason)})</title>'
        )

    svg_parts.append('</svg>')

    return "\n".join(svg_parts)


# ──────────────────────────────────────────────────────────────
# 3. HTML 渲染主函数
# ──────────────────────────────────────────────────────────────

def render_html(result: dict) -> str:
    """生成完整的 HTML 报告字符串。"""
    tc = result.get("thinking_chain") or {}
    s1 = tc.get("step1_situational_reading") or {}
    s2 = tc.get("step2_use_god_identification") or {}
    s3 = tc.get("step3_strength_analysis") or {}
    s4 = tc.get("step4_change_analysis") or {}
    s5 = tc.get("step5_synthesis") or {}

    hn = result.get("human_narrative") or {}

    # 基本数据
    question = hn.get("question") or result.get("question") or ""
    hex_name = (result.get("original_hexagram") or {}).get("name") or s1.get("hexagram_name") or ""
    changed_name = (result.get("changed_hexagram") or {}).get("name") or ""
    palace = (result.get("original_hexagram") or {}).get("palace") or ""
    generation = (result.get("original_hexagram") or {}).get("generation") or ""
    upper_tri = (result.get("original_hexagram") or {}).get("upper_trigram") or ""
    lower_tri = (result.get("original_hexagram") or {}).get("lower_trigram") or ""
    judgment = (result.get("original_hexagram") or {}).get("judgment") or ""
    judgment_changed = (result.get("changed_hexagram") or {}).get("judgment") or "" or ""

    dt = result.get("divination_time") or {}
    empty = result.get("empty_branches") or []

    verdict = s5.get("verdict") or "未知"
    final_score = s5.get("final_score")
    confidence = s5.get("confidence")
    timing_data = s5.get("timing") or {}

    factor_contribs = s5.get("factor_contributions") or []
    explain_summary = hn.get("explain_summary") or ""

    # 正文
    body_paragraphs = hn.get("body") or []
    headline = hn.get("headline") or (body_paragraphs[0] if body_paragraphs else "")
    timing_plain = hn.get("timing_plain") or ""
    advice_list = hn.get("advice") or []
    caveat = hn.get("caveat") or ""
    classical_quotes = hn.get("classical_quotes") or []

    # 用神信息
    use_god_info = hn.get("use_god") or {}
    use_cat = use_god_info.get("category") or s2.get("use_god_category") or ""
    use_br = use_god_info.get("branch") or ""
    use_el = use_god_info.get("element") or ""
    strength = use_god_info.get("strength") or s3.get("strength_level") or ""

    # 六亲五行映射
    branch_elem_map = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
                       "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}

    # 爻列表
    yao_lines = (result.get("original_hexagram") or {}).get("yao_lines") or []
    yao_lines_changed = (result.get("changed_hexagram") or {}).get("changed_lines") or []

    # verdict 色彩
    verdict_color = _verdict_color(verdict)
    verdict_bg = _verdict_bg(verdict)

    # 时间字符串
    time_str = _format_time(dt)

    # 因子贡献 SVG
    svg_content = render_waterfall_svg(factor_contribs, width=600, height=280)
    factor_fallback = _render_factor_fallback(factor_contribs) if not svg_content else ""

    # 动爻表
    moving_lines_table = _render_moving_lines_table(yao_lines, result, s4)

    # 六十四卦大象
    hex_upper_trigram = (result.get("original_hexagram") or {}).get("upper_trigram") or ""
    hex_lower_trigram = (result.get("original_hexagram") or {}).get("lower_trigram") or ""

    # classical_quotes 从 s5 提取
    s5_quotes = s5.get("classical_quotes") or []
    quotes_combined = classical_quotes + [
        q for q in s5_quotes
        if isinstance(q, dict) and q.get("quote")
        and q not in classical_quotes
    ]

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>六爻解读 · {_xml_escape(hex_name)} &middot; {_xml_escape(question)}</title>
<style>
{_css()}
</style>
</head>
<body>

<!-- ═══ Header ═══ -->
<header class="report-header">
    <div class="header-inner">
        <div class="header-symbol">☯</div>
        <h1>六爻解读报告</h1>
        <div class="header-meta">
            <span class="meta-item">❓ {_xml_escape(question)}</span>
            <span class="meta-item">🕐 {time_str}</span>
            <span class="meta-item">☰ {_xml_escape(hex_name)}（{_xml_escape(palace)}宫·{_xml_escape(generation)}）{(" → " + _xml_escape(changed_name)) if changed_name else ""}</span>
        </div>
        <div class="header-sub">
            上{_xml_escape(upper_tri)} 下{_xml_escape(lower_tri)} &nbsp;|&nbsp;
            旬{_xml_escape("、".join(empty)) if empty else "无空"}
        </div>
    </div>
</header>

<main class="report-body">

    <!-- ═══ 结论区 ═══ -->
    <section class="card card-verdict">
        <div class="verdict-badge" style="background:{verdict_bg};color:{verdict_color};">
            {verdict}
        </div>
        <div class="verdict-score">
            综合分：<strong>{final_score:+.2f}</strong>
            {("　置信度：<strong>" + str(confidence) + "%</strong>") if confidence is not None else ""}
        </div>
        <div class="verdict-headline">
            {_highlight_numbers(_xml_escape(headline))}
        </div>
    </section>

    <!-- ═══ 推因摘要 ═══ -->
    <section class="card">
        <h2>▌ 推因摘要</h2>
        <p class="explain-text">{_highlight_numbers(_xml_escape(explain_summary))}</p>
    </section>

    <!-- ═══ 因子贡献瀑布图 ═══ -->
    <section class="card">
        <h2>▌ 因子贡献分解</h2>
        <div class="svg-container">
            {svg_content}
        </div>
        {factor_fallback}
    </section>

    <!-- ═══ 正文解读 ═══ -->
    <section class="card">
        <h2>▌ 正文解读</h2>
        <div class="body-text">
            {"".join(f"<p>{_highlight_numbers(_xml_escape(p))}</p>" for p in body_paragraphs)}
        </div>
    </section>

    <!-- ═══ 应期 ═══ """
    html += f"""
    <section class="card card-timing">
        <h2>▌ 应期推断</h2>
        <p>{_highlight_numbers(_xml_escape(timing_plain))}</p>
    </section>
"""
    html += f"""
    <!-- ═══ 行动建议 ═══ -->
    <section class="card">
        <h2>▌ 行动建议</h2>
        <ul class="advice-list">
            {"".join(f"<li>{_xml_escape(a)}</li>" for a in advice_list)}
        </ul>
    </section>

    <!-- ═══ 动爻分析表 ═══ -->
    <section class="card">
        <h2>▌ 动爻分析</h2>
        {moving_lines_table}
    </section>
"""

    # 经典引文
    if quotes_combined:
        html += f"""
    <!-- ═══ 经典引文 ═══ -->
    <section class="card">
        <h2>▌ 经典引文</h2>
        <div class="quotes-block">
            {"".join(f'<blockquote><span class="quote-source">《{_xml_escape(q.get("source","经典"))}》</span>{_xml_escape(q.get("quote",""))}</blockquote>' for q in quotes_combined)}
        </div>
    </section>
"""

    # 本卦卦辞
    if judgment:
        html += f"""
    <!-- ═══ 本卦卦辞 ═══ -->
    <section class="card">
        <h2>▌ 本卦卦辞</h2>
        <p class="judgment-text"><strong>{_xml_escape(hex_name)}</strong>：{_xml_escape(judgment)}</p>
    </section>
"""

    # 附录：推演过程
    process = hn.get("process") or []
    if process:
        html += """
    <!-- ═══ 附录：推演过程 ═══ -->
    <section class="card card-appendix">
        <h2>▌ 推演过程（备查）</h2>
        <details>
            <summary>展开查看五步推演详情</summary>
            <div class="process-list">
"""
        for p in process:
            label = p.get("label", "")
            text = p.get("text", "")
            html += f"""
                <div class="process-item">
                    <span class="process-label">{_xml_escape(label)}</span>
                    <span class="process-text">{_xml_escape(text)}</span>
                </div>
"""
        html += """
            </div>
        </details>
    </section>
"""

    # 免责声明
    if caveat:
        html += f"""
    <!-- ═══ 免责声明 ═══ -->
    <section class="card card-disclaimer">
        <p class="disclaimer-text">{_xml_escape(caveat)}</p>
    </section>
"""

    # 页脚
    html += """
</main>

<footer class="report-footer">
    <p>由妙手六爻引擎生成 · 仅供参考</p>
</footer>

</body>
</html>"""

    return html


# ──────────────────────────────────────────────────────────────
# 4. 辅助渲染函数
# ──────────────────────────────────────────────────────────────

def _highlight_numbers(text: str) -> str:
    """用 <mark> 标出关键数字/格局词。"""
    # 标出 +X.XX 或 -X.XX 格式的数字
    text = re.sub(
        r'([+-]\d+\.\d+)',
        r'<mark>\1</mark>',
        text
    )
    # 标出关键格局词
    for word in ["六合", "六冲", "伏吟", "反吟", "游魂", "归魂", "三合", "回头生", "回头克", "月破", "旬空"]:
        if word in text and f'<mark>' not in text:
            # only mark once to avoid nesting
            idx = text.find(word)
            if idx >= 0 and '<mark>' not in text[max(0, idx-6):idx]:
                text = text[:idx] + f'<mark>{word}</mark>' + text[idx + len(word):]
    return text


def _verdict_color(verdict: str) -> str:
    if "大吉" in verdict:
        return "#fff"
    elif "吉" in verdict:
        return "#fff"
    elif "平" in verdict:
        return "#fff"
    elif "凶" in verdict or "跌" in verdict:
        return "#fff"
    return "#fff"


def _verdict_bg(verdict: str) -> str:
    if "大吉" in verdict:
        return "#27ae60"
    elif "吉" in verdict:
        return "#2ecc71"
    elif "平" in verdict:
        return "#f39c12"
    elif "凶" in verdict or "跌" in verdict:
        return "#c0392b"
    return "#7f8c8d"


def _format_time(dt: dict) -> str:
    if not dt:
        return ""
    parts = []
    y = dt.get("year_stem_branch", "")
    m = dt.get("month_stem_branch", "")
    d = dt.get("day_stem_branch", "")
    h = dt.get("hour_stem_branch", "")
    if m:
        parts.append(f"{m}月")
    if d:
        parts.append(f"{d}日")
    if y and not m:
        parts.append(f"{y}年")
    if h:
        parts.append(f"{h}时")
    return " ".join(parts) if parts else dt.get("datetime", "")


def _render_factor_fallback(factor_contributions: list) -> str:
    """SVG 失败时的降级：文字列表。"""
    if not factor_contributions:
        return ""
    lines = ['<ul class="factor-fallback">']
    for fc in factor_contributions:
        score = fc.get("score", 0)
        name = fc.get("name", "")
        reason = fc.get("reason", "")
        sign = "+" if score >= 0 else ""
        color = "pos" if score >= 0 else "neg"
        lines.append(
            f'<li class="{color}"><span class="fname">{_xml_escape(name)}</span>'
            f'<span class="fscore">{sign}{score:.2f}</span>'
            f'<span class="freason">{_xml_escape(reason)}</span></li>'
        )
    lines.append('</ul>')
    return "\n".join(lines)


def _render_moving_lines_table(yao_lines: list, result: dict, s4: dict) -> str:
    """生成动爻分析表 HTML。"""
    details = s4.get("details") or []
    branch_elem_map = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
                       "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}

    if not details:
        return '<p class="no-data">卦中无动爻，以静卦论。</p>'

    rows = []
    for d in details:
        pos = d.get("position", "")
        rel = d.get("original_relation", "")
        role = d.get("line_role", "")
        ct = d.get("change_type", "")
        chg = d.get("changed_branch", "")
        pos_name = {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}.get(pos, f"{pos}爻")

        # 作用
        effect = ""
        if role == "用神":
            effect = "用神" + ct
        elif role == "原神":
            effect = "原神" + ct
        elif role == "忌神":
            effect = "忌神" + ct
        elif role == "仇神":
            effect = "仇神" + ct
        else:
            effect = rel + ct

        # 该爻原始地支
        orig_br = ""
        for y in yao_lines:
            if y.get("position") == pos:
                orig_br = y.get("earthly_branch", "")
                break

        orig_elem = branch_elem_map.get(orig_br, "")
        chg_elem = branch_elem_map.get(chg, "")

        rows.append(f"""
        <tr>
            <td>{pos_name}</td>
            <td>{rel}</td>
            <td>{orig_br}（{orig_elem}）</td>
            <td>{chg}（{chg_elem}）</td>
            <td>{ct}</td>
            <td><span class="role-tag role-{role}">{effect}</span></td>
        </tr>""")

    return f"""
    <div class="table-wrapper">
    <table class="yao-table">
        <thead>
            <tr>
                <th>爻位</th><th>六亲</th><th>地支</th>
                <th>变支</th><th>动变</th><th>作用</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    </div>
    """


def _xml_escape(text: str) -> str:
    """XML/HTML 实体转义。"""
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#39;")
    return text


def _css() -> str:
    """样式层与排盘报告同源：见 assets/report.css（visualization._load_report_css）。"""
    from visualization import _load_report_css
    return _load_report_css()



def main():
    parser = argparse.ArgumentParser(
        description="六爻解读 HTML 报告生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/build_html_report.py --question "投资财运" --out outputs/reports/sample.html
  python scripts/build_html_report.py --yao 7,7,8,9,7,7 --question "婚姻何时能成"
  python scripts/build_html_report.py --seed 42 --mode coin --question "出行吉凶"
        """,
    )
    parser.add_argument("--question", "-q", type=str, default="所问之事",
                        help="占卜问题（必填）")
    parser.add_argument("--yao", type=str, default=None,
                        help="手动指定六爻值，逗号分隔，如 '7,7,8,9,7,7'")
    parser.add_argument("--out", "-o", type=str, default=None,
                        help="输出 HTML 文件路径")
    parser.add_argument("--seed", type=int, default=None,
                        help="随机种子（可复现模式）")
    parser.add_argument("--mode", type=str, default="time",
                        choices=["time", "coin", "number", "manual"],
                        help="起卦方式（默认 time）")
    parser.add_argument("--year", type=int, default=None, help="指定年")
    parser.add_argument("--month", type=int, default=None, help="指定月")
    parser.add_argument("--day", type=int, default=None, help="指定日")
    parser.add_argument("--hour", type=int, default=None, help="指定时")

    args = parser.parse_args()

    # 解析 yao
    yao = None
    if args.yao:
        try:
            yao = [int(x.strip()) for x in args.yao.split(",")]
            if len(yao) != 6:
                print(f"错误：--yao 需要恰好 6 个值，收到 {len(yao)} 个", file=sys.stderr)
                sys.exit(1)
        except ValueError:
            print("错误：--yao 格式不正确，应为 '7,7,8,9,7,7'", file=sys.stderr)
            sys.exit(1)

    # 默认输出路径
    out_path = args.out
    if not out_path:
        os.makedirs(os.path.join(PROJECT_DIR, "outputs", "reports"), exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_q = re.sub(r'[^\w\u4e00-\u9fff]+', '_', args.question)[:20]
        out_path = os.path.join(PROJECT_DIR, "outputs", "reports", f"liuyao_{safe_q}_{ts}.html")

    print(f"[build_html_report] 正在生成解读报告...")
    print(f"  问题: {args.question}")
    print(f"  模式: {args.mode}" + (f"  种子: {args.seed}" if args.seed else ""))

    # 调用引擎
    result = run_pipeline(
        question=args.question,
        yao=yao,
        seed=args.seed,
        mode=args.mode,
        year=args.year,
        month=args.month,
        day=args.day,
        hour=args.hour,
    )

    # 渲染 HTML
    html = render_html(result)

    # 写入文件
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    file_size = os.path.getsize(out_path)
    print(f"\n[✓] 报告已生成: {out_path}")
    print(f"    大小: {file_size} 字节")
    print(f"    卦象: {(result.get('original_hexagram') or {}).get('name', '?')} → "
          f"{(result.get('changed_hexagram') or {}).get('name', '无变卦')}")
    print(f"    结论: {result.get('thinking_chain', {}).get('step5_synthesis', {}).get('verdict', '?')}")


if __name__ == "__main__":
    main()
