# -*- coding: utf-8 -*-
"""命·因子推演（analyze 段）—— 只整理机械因子，不写命理断语。

输出契约与合参层对齐：
  {question, pillars, factors, shensha, ming_shen_gong,
   conclusion: {方向: "", verdicts: [], 说明, 所本},
   chart_summary}
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


def analyze(chart_json: dict) -> dict:
    """chart JSON → analyze JSON。本轮不产出吉凶断语。"""
    result = dict(chart_json)
    pillars = result.get("pillars") or {}
    summary = {
        "四柱": {k: (v or {}).get("ganzhi") for k, v in pillars.items()},
        "日主": (pillars.get("day") or {}).get("stem"),
        "命宫": (result.get("ming_shen_gong") or {}).get("ming_gong"),
        "身宫": (result.get("ming_shen_gong") or {}).get("shen_gong"),
    }
    return {
        **result,
        "chart_summary": summary,
        "conclusion": {
            "方向": "",
            "verdicts": [],
            "说明": "命科推演未实现；本输出仅含机械因子（四柱/藏干十神/纳音/神煞/命身宫）。",
            "所本": "core.yishu_core.ming_tables + ganzhi_calendar（机械表，无断语）",
            "应期": [],
            "timing": [],
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="命·因子推演（analyze 段，无断语）")
    ap.add_argument("chart_json", nargs="?", help="chart 段输出")
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args()

    if args.chart_json:
        data = json.loads(Path(args.chart_json).read_text(encoding="utf-8"))
    else:
        from chart import chart as _chart

        data = _chart(datetime_str="1990-05-20 10:30")

    out = analyze(data)
    text = json.dumps(out, ensure_ascii=False, indent=2, default=str)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
