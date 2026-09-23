# -*- coding: utf-8 -*-
"""小六壬·报告渲染（render 段）—— 薄层，不自带 HTML 模板。

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
        lines.append(f"| {k} | {v if v is not None else '—'} |")
    for st in analyze_out.get("steps") or []:
        lines.append(f"| 步序·{st.get('步')} | {st.get('落宫')} |")
    p = analyze_out.get("palace") or {}
    for k, v in p.items():
        if isinstance(v, (list, dict)):
            v = json.dumps(v, ensure_ascii=False)
        lines.append(f"| 宫·{k} | {v if v is not None else '—'} |")
    lines.append("")

    # 因子明细（对齐分可复核）
    lines += ["## 判读因子", ""]
    lines += ["| 因子 | 权重 | 判据 | 所本 |", "|---|---|---|---|"]
    for f in analyze_out.get("factors") or []:
        lines.append(f"| {f.get('因子')} | {f.get('权重')} | {f.get('判据')} | {f.get('所本')} |")
    lines.append("")

    text = "\n".join(lines)
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description="小六壬报告渲染")
    ap.add_argument("analyze_json", nargs="?", help="analyze 输出 JSON 文件")
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args()

    if args.analyze_json:
        a = json.loads(Path(args.analyze_json).read_text(encoding="utf-8"))
    else:
        from chart import chart_from_month_day_hour
        from analyze import analyze
        a = analyze(chart_from_month_day_hour(8, 15, 9))
        a["question"] = "去朋友家，测有人否"
        a["topic"] = "行人"
    text = render(a, args.out)
    if args.out:
        print("报告 →", args.out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
