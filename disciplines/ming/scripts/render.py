# -*- coding: utf-8 -*-
"""命·报告（render 段）—— 薄层：因子表 + narrate 正文。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from yishu_core.runtime import force_utf8_stdio  # noqa: E402

from narrate import narrate


def render(analyze_out: dict) -> str:
    s = analyze_out.get("chart_summary") or {}
    lines = [narrate(analyze_out), "", "## 机械因子", "", "| 项 | 值 |", "|---|---|"]
    for k, v in s.items():
        lines.append(f"| {k} | {v if v is not None else '—'} |")
    pillars = analyze_out.get("pillars") or {}
    lines += ["", "## 四柱", "", "| 柱 | 干支 | 纳音 |", "|---|---|---|"]
    for k in ("year", "month", "day", "hour"):
        p = pillars.get(k) or {}
        lines.append(f"| {k} | {p.get('ganzhi') or '—'} | {p.get('nayin') or '—'} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="命·报告（render 段）")
    ap.add_argument("analyze_json", nargs="?")
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args()

    if args.analyze_json:
        a = json.loads(Path(args.analyze_json).read_text(encoding="utf-8"))
    else:
        from analyze import analyze as _analyze
        from chart import chart as _chart

        a = _analyze(_chart(datetime_str="1990-05-20 10:30"))

    text = render(a)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
