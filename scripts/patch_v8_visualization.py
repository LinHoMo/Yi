# -*- coding: utf-8 -*-
"""
v8 HTML 导出增强：
- visualization.build_html_report 注入「人话解读」卡片
- 生成 sample_report_v8.html 与 index.html 门户数据
"""
from pathlib import Path
import json
import sys

ROOT = Path(r"C:\Users\Lin\Desktop\skills\liu-yao")
sys.path.insert(0, str(ROOT / "scripts"))

VIS = ROOT / "scripts" / "visualization.py"
text = VIS.read_text(encoding="utf-8")

old = '''    # 综合判断卡片（置于概览页最显眼位置）
    step5_desc = step5.get("description", step5.get("verdict_description", ""))
    conf_text = f"（确信度：{confidence}%）" if confidence else ""
    tabs["概览"].append(f\'\'\'
    <div class="card" style="border-left:4px solid {"#2e7d32" if "auspicious" in v_class else "#d32f2f" if "inauspicious" in v_class else "#f57f17"};">
        <h2>综合判断 <span class="verdict-badge {v_class}">{html.escape(verdict)} {composite:.2f}分</span></h2>
        <p>{html.escape(step5_desc)}{html.escape(conf_text)}</p>
    </div>\'\'\')
'''

new = '''    # 综合判断卡片（置于概览页最显眼位置）
    step5_desc = step5.get("description", step5.get("verdict_description", ""))
    conf_text = f"（确信度：{confidence}%）" if confidence else ""
    tabs["概览"].append(f\'\'\'
    <div class="card" style="border-left:4px solid {"#2e7d32" if "auspicious" in v_class else "#d32f2f" if "inauspicious" in v_class else "#f57f17"};">
        <h2>综合判断 <span class="verdict-badge {v_class}">{html.escape(verdict)} {composite:.2f}分</span></h2>
        <p>{html.escape(step5_desc)}{html.escape(conf_text)}</p>
    </div>\'\'\')

    # 人话解读卡片
    human = result_data.get("human_narrative") or {}
    if not human:
        try:
            from human_narrative import build_human_narrative
            human = build_human_narrative(result_data) or {}
        except Exception:
            human = {}
    if human and not human.get("error"):
        advice_items = "".join(f"<li>{html.escape(str(a))}</li>" for a in (human.get("advice") or []))
        quotes_html = ""
        for q in (human.get("classical_quotes") or []):
            quotes_html += f"<p style=\\"color:#8a8175;font-size:13px;margin:4px 0;\\">（{html.escape(str(q.get('source','')))}）{html.escape(str(q.get('quote','')))}</p>"
        timing_plain = html.escape(str(human.get("timing_plain") or ""))
        tabs["概览"].append(f\'\'\'
    <div class="card" style="border-left:4px solid #b8963e;">
        <h2>人话解读</h2>
        <p style="font-size:16px;font-weight:600;color:#1c1917;margin-bottom:10px;">{html.escape(str(human.get("headline") or ""))}</p>
        <p style="margin-bottom:10px;">{html.escape(str(human.get("plain_summary") or ""))}</p>
        <h3>这意味着什么</h3>
        <p style="margin-bottom:10px;">{html.escape(str(human.get("what_it_means") or ""))}</p>
        <h3>时间节奏</h3>
        <p style="margin-bottom:10px;">{timing_plain}</p>
        <h3>可以怎么做</h3>
        <ul style="padding-left:20px;margin-bottom:8px;">{advice_items}</ul>
        {quotes_html}
        <p style="color:#8a8175;font-size:12px;margin-top:12px;">{html.escape(str(human.get("caveat") or ""))}</p>
    </div>\'\'\')
'''

if old not in text:
    raise SystemExit("visualization patch target not found")
text = text.replace(old, new, 1)
VIS.write_text(text, encoding="utf-8")
print("visualization.py patched")
