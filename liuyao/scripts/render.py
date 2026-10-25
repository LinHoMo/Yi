# -*- coding: utf-8 -*-
"""六爻纳甲·报告渲染（render 段）—— analyze JSON → 报告。

单一出口（M3.1）：同一份 analyze JSON 出 Markdown 或单文件 HTML。
HTML = 排盘（SVG 真卦盘：爻线/六亲/六神/世应/空破/动变标记）＋ 结要卡
＋ narrate 正文（复用正文生成，不另行断卦）＋ 判据所本，骨架走 core/report。
两套并行生成器（visualization.build_html_report / build_html_report.py）
已删除，报告产物只此一个出口（grep "<!DOCTYPE" 仅剩内核 kit）。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:  # 实测本 CLI 在 GBK 控制台输出的是 GBK 字节（首字节 `# \xc1\xf9\xd8\xb3`＝「六爻」），UTF-8 消费方必乱码
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 内核定位规则只在 kernel_path.py 一份实现（本文件此前只挂了 scripts/，没挂 core/）
_ks_d = os.path.dirname(os.path.abspath(__file__))
if _ks_d not in sys.path:
    sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ks_ensure  # noqa: E402

# `python scripts/render.py xxx.json -f html` 原先直接 ModuleNotFoundError: yishu_core，
# 而本文件 docstring 自称「报告产物只此一个出口」且含 HTML——md 分支能跑，
# html 分支只在被别处 import 时才侥幸可用。按仓库同一约定补挂内核。
_ks_ensure(__file__)

from narrate import narrate  # noqa: E402

_CSS_PATH = Path(__file__).resolve().parents[1] / "assets" / "report.css"
_TPL_PATH = Path(__file__).resolve().parents[1] / "data" / "narrative_templates.json"
# 章节序号汉字（报告按实际出现的可选节顺延编号）
_CN = "一二三四五六七八九十"


def _grade_note() -> str:
    """结要里「结论」行的档位注记——措辞归数据层，代码不组句（[1c] 断语外置取证）。"""
    try:
        shell = json.loads(_TPL_PATH.read_text(encoding="utf-8")).get("narrate_shell") or {}
    except (OSError, ValueError):
        return ""
    return shell.get("conclusion_grade_note") or ""


def _summary_block(a: dict) -> list[str]:
    con = a.get("conclusion") or {}
    s = a.get("divination_time") or {}
    oh = a.get("original_hexagram") or {}
    lines = []
    if a.get("question"):
        lines.append(f"- **问**：{a['question']}")
    if s.get("datetime"):
        lines.append(f"- **起卦时刻**：{s['datetime']}")
    if oh.get("name"):
        lines.append(f"- **本卦**：{oh['name']}"
                     + (f"（{oh.get('palace') or ''}宫）" if oh.get("palace") else ""))
    ch = a.get("changed_hexagram") or {}
    if ch.get("name"):
        lines.append(f"- **变卦**：{ch['name']}")
    if con.get("方向"):
        # 档位名（大吉/偏吉/平吉/凶/大凶…）是引擎的结构输出，不带注定含义；
        # 同页口径句要求凶象只用「偏向／有…信号／结构上」讲，故此处显式标注档位性质。
        lines.append(f"- **结论**：{con['方向']}{_grade_note()}")
    if con.get("应期"):
        lines.append("- **应期**：" + "、".join(map(str, con["应期"])))
    return lines


def render(a: dict, fmt: str = "md") -> str:
    """analyze JSON → 报告（fmt=md 纯文本 / fmt=html 单文件 HTML）。"""
    if fmt == "html":
        return render_html(a)
    con = a.get("conclusion") or {}
    lines = ["# 六爻纳甲占报告", ""]
    lines += ["## 一、结要", ""]
    summary = _summary_block(a)
    if summary:
        lines += summary
    else:
        lines.append("（结论见正文）")
    lines += ["", "## 二、正文", ""]
    lines.append(narrate(a))
    if con.get("所本"):
        lines += ["", "## 三、判据所本", "", f"{con['所本']}。", ""]
    return "\n".join(lines) + "\n"


def render_html(a: dict) -> str:
    """analyze JSON → 单文件 HTML 报告（render 段唯一 HTML 出口）。"""
    from yishu_core.report.html import render_page, escape, md_to_html
    from visualization import generate_hexagram_diagram

    con = a.get("conclusion") or {}
    s = a.get("divination_time") or {}
    oh = a.get("original_hexagram") or {}
    ch = a.get("changed_hexagram") or {}
    question = str(a.get("question") or "占当前所问之事")

    meta = []
    if s.get("datetime"):
        meta.append(f'<span class="meta-item">{escape(s["datetime"])}</span>')
    meta.append(
        f'<span class="meta-item">{escape(oh.get("name") or "?")}'
        + (f'（{escape(oh.get("palace") or "")}宫·{escape(oh.get("generation") or "")}）' if oh.get("palace") else "")
        + (f' → {escape(ch.get("name") or "")}' if ch.get("name") else "")
        + "</span>"
    )
    empty = a.get("empty_branches") or []
    sub = (f'上{escape(oh.get("upper_trigram") or "")} 下{escape(oh.get("lower_trigram") or "")}'
           + f" ｜ 旬{escape('、'.join(empty)) if empty else '无空'}"
           + (f" ｜ 动爻：{'、'.join(str(y.get('position')) for y in (oh.get('yao_lines') or []) if y.get('is_moving'))}"
              if any(y.get("is_moving") for y in (oh.get("yao_lines") or [])) else ""))

    # 结要卡
    verdict = str(con.get("方向") or "待定")
    verdict_cls = {"吉": "verdict-auspicious", "平": "verdict-neutral"}.get(verdict, "verdict-inauspicious") \
        if verdict in ("吉", "平") else ("verdict-auspicious" if "吉" in verdict or "有利" in verdict
                                         else ("verdict-inauspicious" if "凶" in verdict else "verdict-neutral"))
    info_rows = []
    for label, key in (("用神", "用神"), ("用神爻", "用神爻"), ("旺衰", "旺衰")):
        v = (a.get("chart_summary") or {}).get(key) or con.get(key)
        if v:
            info_rows.append(f'<div class="info-row"><span class="info-label">{label}</span>'
                             f'<span class="info-value">{escape(v)}</span></div>')
    yingqi = con.get("应期") or []
    timing_html = ""
    if yingqi:
        items = "".join(f"<li>{escape(str(t))}</li>" for t in yingqi)
        timing_html = (f'<div class="card card-timing"><h3>应期</h3><ul>{items}</ul></div>')

    body = (
        f"""
<header class="report-header">
    <div class="header-inner">
        <div class="seal">易</div>
        <h1>六爻纳甲占报告</h1>
        <div class="header-meta">
            <span class="meta-item">问：{escape(question)}</span>
            {''.join(meta)}
        </div>
        <div class="header-sub">{sub}</div>
        <div class="header-rule"></div>
    </div>
</header>

<main class="report-body">

    <section class="card card-verdict">
        <h2>一、结要</h2>
        <div class="verdict-badge {verdict_cls}">{escape(verdict)}</div>
        <div class="verdict-headline">{escape(str(con.get("说明") or ""))}</div>
        <div class="info-grid">{''.join(info_rows)}</div>
        {timing_html}
    </section>

    <section class="card hexagram-section">
        <h2>二、卦盘</h2>
        <div class="svg-container">{generate_hexagram_diagram(a)}</div>
    </section>

    <section class="card">
        <h2>三、正文</h2>
        <div class="body-text">{md_to_html(narrate(a))}</div>
    </section>
"""
    )
    # 趋避建议：analyze 层算出的 section_advice 此前只在文本报告与 narrate 里出现，
    # HTML 完全没这一节（`assets/report.css` 的 `.advice-list` 自定义起无人引用即是旁证）——
    # 属「算出来了但看不到」。节号按实际出现的可选节顺延，不硬编。
    sec_no = 3  # 一、结要 / 二、卦盘 / 三、正文 已在上面模板里
    adv = [str(x).strip() for x in (a.get("section_advice") or []) if str(x).strip()]
    if adv:
        sec_no += 1
        items = "".join(f"<li>{escape(t)}</li>" for t in adv)
        body += (f'    <section class="card"><h2>{_CN[sec_no - 1]}、趋避建议</h2>'
                 f'<ul class="advice-list">{items}</ul></section>\n')
    # 方位层（#23）：advanced_analysis.fangwei 的候选方位必须可见。parity 门此前只盯
    # 趋避／应期／所本三节，advanced_analysis 的子节掉出 HTML 都查不到——属「算出来了但看不到」。
    fw = ((a.get("advanced_analysis") or {}).get("fangwei") or {})
    if fw.get("applicable"):
        sec_no += 1
        rows = [f"{c.get('why') or ''}：{c.get('direction') or ''}"
                f"（{c.get('branch') or ''}，{c.get('strength') or ''}）"
                for c in (fw.get("candidates") or [])]
        if fw.get("ji_fang"):
            rows.append("吉方候选：" + "、".join(fw["ji_fang"])
                        + ("（同档并列，不代书择一）" if fw.get("tie") else ""))
        for y in fw.get("yan_yi") or []:
            rows.append(f"延医{y.get('档') or ''}：{y.get('direction') or ''}（{y.get('branch') or ''}）")
        if fw.get("yan_yi_note"):
            rows.append(str(fw["yan_yi_note"]))
        lis = "".join(f"<li>{escape(r)}</li>" for r in rows)
        body += (f'    <section class="card"><h2>{_CN[sec_no - 1]}、方位参考</h2>'
                 f'<ul class="advice-list">{lis}</ul>'
                 f'<div class="judgment-text">{escape(str(fw.get("basis") or ""))}</div></section>\n')
    if con.get("所本"):
        sec_no += 1
        body += (f'    <section class="card card-appendix"><h2>{_CN[sec_no - 1]}、判据所本</h2>'
                 f'<div class="judgment-text">{escape(con["所本"])}。</div></section>\n')
    body += """</main>

<footer class="report-footer">
    本报告为象征推演与方向参考，非现实预测；医疗、法律、投资等重大决策请以专业意见为准。
</footer>
"""
    css = _CSS_PATH.read_text(encoding="utf-8") if _CSS_PATH.exists() else ""
    return render_page(
        title=f"六爻纳甲占报告 · {question}",
        body=body,
        css=css,
        footer="",
        container=False,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="六爻纳甲报告渲染（render 段单一出口）")
    ap.add_argument("analyze_json", nargs="?", help="analyze 输出的 JSON 文件（缺省跑演示）")
    ap.add_argument("-f", "--fmt", choices=["md", "html"], default="md",
                    help="输出格式（缺省 md）")
    ap.add_argument("-o", "--out", type=Path, help="写出报告文件")
    args = ap.parse_args()

    if args.analyze_json:
        a = json.loads(Path(args.analyze_json).read_text(encoding="utf-8"))
    else:
        from analyze import analyze as _analyze
        from chart import chart as _chart
        a = _analyze(_chart("coin", "占当前所问之事", seed=42))

    text = render(a, fmt=args.fmt)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
