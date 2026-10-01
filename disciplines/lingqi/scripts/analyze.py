# -*- coding: utf-8 -*-
"""灵棋经·规则推演（analyze 段）—— 查表直录，无衍生解读。

灵棋经属「查表即断」门类：analyze 的职责是**忠实透出课表内容**
（课名/象/卦注/象曰/詩曰，全部逐字来自书源 ketables.json）并标注结构
（三部布数与阴阳定性——按《灵棋经》通行注：多寡分阳阴，奇偶见书注），
不做任何书外发挥（AGENTS.md 铁律一/三）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
for _p in (str(DISC / "scripts"),):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def analyze(chart_out: dict) -> dict:
    key = chart_out.get("key") or ""
    up, mid, down = (int(x) for x in key.split("-"))
    factors = [
        {"code": "sanbu", "label": f"上{up} 中{mid} 下{down}",
         "basis": "十二棋分三部（各四枚），面数即布数；全零不成课"},
        {"code": "ke_name", "label": chart_out.get("ke_name", ""),
         "basis": chart_out.get("xiang", "")},
        {"code": "zhu", "label": chart_out.get("zhu", ""),
         "basis": "书源卦注（逐字）"},
    ]
    return {
        "discipline": "lingqi",
        "id": chart_out.get("id", ""),
        "question": chart_out.get("question", ""),
        "chart_summary": {
            "三部布数": f"上{up} 中{mid} 下{down}",
            "课号": key,
            "课名": chart_out.get("ke_name", ""),
            "象": chart_out.get("xiang", ""),
        },
        "ke_name": chart_out.get("ke_name", ""),
        "xiangyue": chart_out.get("xiangyue") or [],
        "shiyue": chart_out.get("shiyue") or [],
        "zhu": chart_out.get("zhu", ""),
        "factors": factors,
        "conclusion": {
            "direction": None,
            "note": "查表直录古籍断语（象曰/詩曰），吉凶判断属原文文本，"
                    "非本仓推断；解读请结合原文与求测语境（铁律三）",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="灵棋经规则推演（查表直录）")
    ap.add_argument("chart_file", help="chart 段输出的 JSON 路径")
    ap.add_argument("--out", "-o", help="输出 JSON 路径（缺省打印 stdout）")
    args = ap.parse_args()
    chart_out = json.loads(Path(args.chart_file).read_text(encoding="utf-8"))
    out = analyze(chart_out)
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"analyze 已写出 → {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
