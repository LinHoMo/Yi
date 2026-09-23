# -*- coding: utf-8 -*-
"""择吉·报告渲染（render 段）—— 薄层，不自带 HTML 模板。

    python scripts/render.py [analyze.json] [-o report.md]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(CORE), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from narrate import narrate  # noqa: E402


def render(analyze_out: dict, out_path: Path | None = None) -> str:
    """analyze 输出 → Markdown 报告全文。"""
    lines = [narrate(analyze_out), ""]

    # 盘面数据附录（机器可复核）
    lines += ["## 盘面数据", ""]
    lines += ["| 项 | 值 |", "|---|---|"]
    s = analyze_out.get("chart_summary") or {}
    for k, v in s.items():
        if isinstance(v, dict):
            v = json.dumps(v, ensure_ascii=False)
        lines.append(f"| {k} | {v if v is not None else '—'} |")
    f = analyze_out.get("factors_detail") or {}
    for k, v in f.items():
        if isinstance(v, dict):
            v = json.dumps(v, ensure_ascii=False)
        lines.append(f"| 因子·{k} | {v} |")
    hour = analyze_out.get("hour")
    if hour:
        lines.append(f"| 时辰值神 | {json.dumps(hour, ensure_ascii=False)} |")
    lines.append("")

    # 因子明细（对齐分可复核）
    lines += ["## 判读因子", ""]
    lines += ["| 因子 | 权重 | 判据 | 所本 |", "|---|---|---|---|"]
    for x in analyze_out.get("factors") or []:
        lines.append(f"| {x.get('因子')} | {x.get('权重')} | {x.get('判据')} | {x.get('所本')} |")
    lines.append("")

    text = "\n".join(lines)
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description="择吉报告渲染")
    ap.add_argument("analyze_json", nargs="?", help="analyze 输出 JSON 文件")
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args()

    if args.analyze_json:
        a = json.loads(Path(args.analyze_json).read_text(encoding="utf-8"))
    else:
        from datetime import date
        from chart import chart_from_date
        from analyze import analyze
        a = analyze(chart_from_date(date(2026, 9, 25)))
        a["question"] = "结婚嫁娶吉否"
        a["activity"] = "嫁娶"
    text = render(a, args.out)
    if args.out:
        print("报告 →", args.out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
