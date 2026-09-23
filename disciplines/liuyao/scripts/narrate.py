# -*- coding: utf-8 -*-
"""六爻纳甲·正文叙述（narrate 段）—— 唯一交付正文，师傅口吻（CONTRACT §一）。

薄适配：把 analyze JSON 里的排盘（result）与思维链（thinking_chain）交给
既有 `liuyao_engine.format_reading_output` 生成正文。正文每个象数判断
都出自 analyze 输出，不新增结论。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from liuyao_engine import format_reading_output  # noqa: E402


def narrate(a: dict) -> str:
    """analyze JSON → 完整正文（markdown 化文本）。"""
    chain = a.get("thinking_chain") or {}
    result = {k: v for k, v in a.items() if k not in ("thinking_chain", "conclusion")}
    body = format_reading_output(result, chain)
    advice = result.get("section_advice") or []
    if advice:
        body += "\n" + "=" * 52 + "\n"
        body += "【趋避建议】\n"
        for i, adv in enumerate(advice, 1):
            body += f"  {i}. {adv}\n"
    return body


def main() -> int:
    ap = argparse.ArgumentParser(description="六爻纳甲解读（narrate 段）")
    ap.add_argument("analyze_json", nargs="?", help="analyze 输出的 JSON 文件（缺省跑演示）")
    ap.add_argument("-o", "--out", type=Path, help="写出解读文本")
    args = ap.parse_args()

    if args.analyze_json:
        a = json.loads(Path(args.analyze_json).read_text(encoding="utf-8"))
    else:
        from analyze import analyze as _analyze
        from chart import chart as _chart
        a = _analyze(_chart("coin", "占当前所问之事", seed=42))

    text = narrate(a)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
