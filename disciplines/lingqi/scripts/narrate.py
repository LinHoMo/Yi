# -*- coding: utf-8 -*-
"""灵棋经·人话叙述（narrate 段）—— 直录书源断语，不做书外发挥。

文案全部来自 data/ketables.json（书源逐字）；本文件只做编排与口径声明。
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


def narrate(a: dict) -> str:
    s = a.get("chart_summary") or {}
    lines = [
        "# 灵棋课式说明",
        "",
        f"课号：{s.get('课号') or '—'}（{s.get('三部布数') or '—'}）。",
        f"课名：**{s.get('课名') or '—'}**；象：{s.get('象') or '—'}。",
        "",
        f"**卦注**：{a.get('zhu') or '—'}",
    ]
    xy = a.get("xiangyue") or []
    if xy:
        lines += ["", "**象曰**（书源原文）："]
        lines += [f"> {x}" for x in xy]
    sy = a.get("shiyue") or []
    if sy:
        lines += ["", "**詩曰**（书源原文）："]
        lines += [f"> {x}" for x in sy]
    lines += [
        "",
        "以上断语**逐字直录《靈棋經》原文**（查表即断，本仓不做书外发挥），",
        "不是现实预测；解读请结合求测语境与原文意象（AGENTS.md 铁律一/三）。",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="灵棋经人话叙述（直录书源断语）")
    ap.add_argument("analyze_file", help="analyze 段输出的 JSON 路径")
    ap.add_argument("--out", "-o", help="输出 MD 路径（缺省打印 stdout）")
    args = ap.parse_args()
    a = json.loads(Path(args.analyze_file).read_text(encoding="utf-8"))
    text = narrate(a)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"narrate 已写出 → {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
