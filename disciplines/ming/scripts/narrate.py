# -*- coding: utf-8 -*-
"""命·正文（narrate 段）—— 占位：明示推演未实现，不编命运结论。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def narrate(a: dict) -> str:
    s = a.get("chart_summary") or {}
    pillars = s.get("四柱") or {}
    gz = " ".join(str(pillars.get(k) or "—") for k in ("year", "month", "day", "hour"))
    lines = [
        "# 命局因子说明",
        "",
        f"四柱：{gz}（年月日时）。",
        f"日主：{s.get('日主') or '—'}。命宫：{s.get('命宫') or '—'}；身宫：{s.get('身宫') or '—'}。",
        "",
        "本版本**未实现命理推演**（格局、大运、流年吉凶均未建）。",
        "以上仅为机械排盘因子，供合参与人工研判对照，**不构成命运断言**。",
        "",
        "按 `AGENTS.md`：机械运算归代码；缺推演时明示未参评，不用其他科补位猜测。",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="命·正文（narrate 段）")
    ap.add_argument("analyze_json", nargs="?")
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args()

    if args.analyze_json:
        a = json.loads(Path(args.analyze_json).read_text(encoding="utf-8"))
    else:
        from analyze import analyze as _analyze
        from chart import chart as _chart

        a = _analyze(_chart(datetime_str="1990-05-20 10:30"))

    text = narrate(a)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
