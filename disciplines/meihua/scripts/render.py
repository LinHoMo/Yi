# -*- coding: utf-8 -*-
"""梅花易数·报告渲染（render 段）—— 薄层，不自带 HTML 模板。

CONTRACT §一：render 调内核报告模板，学科只提供盘数据与要点。
内核暂未上收通用 report 模板（见 docs/YI-PLAN.md M4），此处先输出
单文件 Markdown：盘面数据 + narrate 正文 + 因子明细附录，段间只传结构化数据。

    python scripts/render.py [analyze.json] [-o report.md]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from narrate import narrate


def render(analyze_out: dict, out_path: Path | None = None) -> str:
    """analyze 输出 → Markdown 报告全文。"""
    s = analyze_out.get("chart_summary") or {}
    lines = [narrate(analyze_out), ""]

    # 盘面数据附录（机器可复核）
    lines += ["## 盘面数据", ""]
    lines += ["| 项 | 值 |", "|---|---|"]
    for k, v in s.items():
        lines.append(f"| {k} | {v if v is not None else '—'} |")
    bu = analyze_out.get("body_use") or {}
    for k, v in bu.items():
        lines.append(f"| 体用·{k} | {v if v is not None else '—'} |")
    iv = analyze_out.get("interaction") or {}
    lines.append(f"| 生体之卦 | {json.dumps(iv.get('生体之卦'), ensure_ascii=False)} |")
    lines.append(f"| 克体之卦 | {json.dumps(iv.get('克体之卦'), ensure_ascii=False)} |")
    t = analyze_out.get("timing") or {}
    lines.append(f"| 卦气应期 | {json.dumps(t.get('卦气应期'), ensure_ascii=False)} |")
    lines.append("")

    # 因子明细（对齐分可复核）
    lines += ["## 判读因子", ""]
    lines += ["| 因子 | 权重 | 判据 | 所本 |", "|---|---|---|---|"]
    for f in analyze_out.get("factors") or []:
        lines.append(f"| {f.get('因子')} | {f.get('权重')} | {f.get('判据')} | {f.get('所本')} |")
    lines.append("")

    md = "\n".join(lines).strip() + "\n"
    if out_path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8")
    return md


if __name__ == "__main__":
    import argparse as _ap

    CORE = Path(__file__).resolve().parents[3] / "core"
    for _p in (str(Path(__file__).resolve().parent), str(CORE)):
        if _p not in sys.path:
            sys.path.insert(0, _p)
    from yishu_core.runtime import force_utf8_stdio  # noqa: E402
    force_utf8_stdio()

    ap = _ap.ArgumentParser(description="梅花易数报告渲染（render 段）")
    ap.add_argument("analyze_json", nargs="?",
                    help="analyze 输出 JSON 文件（缺省跑观梅占演示）")
    ap.add_argument("-o", "--out", type=Path, help="写出 Markdown 报告")
    args = ap.parse_args()

    if args.analyze_json:
        data = json.loads(Path(args.analyze_json).read_text(encoding="utf-8"))
    else:
        from chart import chart
        from analyze import analyze
        params = {"way": "numbers", "year_num": 5, "month": 12, "day": 17,
                  "hour_num": 9, "question": "明晚会有女子来折花吗？"}
        data = analyze(chart(params))
    if args.out:
        render(data, args.out)
        print("报告 →", args.out)
    else:
        print(render(data))
