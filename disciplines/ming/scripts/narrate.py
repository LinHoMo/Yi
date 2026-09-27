# -*- coding: utf-8 -*-
"""命·正文（narrate 段）—— 叙述机械因子；禁止命运断言。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def narrate(a: dict) -> str:
    s = a.get("chart_summary") or {}
    con = a.get("conclusion") or {}
    pillars = s.get("四柱") or {}
    gz = " ".join(str(pillars.get(k) or "—") for k in ("year", "month", "day", "hour"))
    dayun = a.get("dayun") or con.get("dayun") or []

    lines = [
        "# 命局因子说明",
        "",
        f"四柱：{gz}（年月日时）。日主：{s.get('日主') or '—'}。",
        f"命宫：{s.get('命宫') or '—'}；身宫：{s.get('身宫') or '—'}。",
        "",
        f"**强弱**：{con.get('strength') or s.get('强弱') or '—'}（得分 {con.get('strength_score')}）。",
        f"**格局**：{con.get('pattern') or s.get('格局') or '—'}。",
        f"**喜用**：{'、'.join(con.get('useful_gods') or []) or '—'}；"
        f"忌：{'、'.join(con.get('taboo_gods') or []) or '—'}。",
        "",
    ]
    xunkong = s.get("空亡") or a.get("xunkong") or []
    if xunkong:
        lines.append(f"**空亡**：{'、'.join(xunkong)}（日柱旬空）。")
        lines.append("")
    if dayun:
        lines.append("**大运**（起运岁为近似）：")
        for d in dayun:
            lines.append(
                f"- {d.get('start_age')}–{d.get('end_age')} 岁　{d.get('ganzhi')}"
                f"（{d.get('ten_god') or '—'}）"
            )
        lines.append("")
    xs = con.get("dayun_liunian") or []
    if xs:
        lines.append("**大运×流年对照**（机械关系，不批吉凶）：")
        for x in xs[:4]:
            rel = "；".join(r.get("text", "") for r in (x.get("relations") or [])[:2])
            lines.append(f"- {x.get('year')}（{x.get('liunian')}）× 运{x.get('dayun')}：{rel or '—'}")
        lines.append("")
    liunian = con.get("liunian") or []
    if liunian:
        head = "、".join(f"{x.get('year')}{x.get('ganzhi')}({x.get('ten_god') or '—'})" for x in liunian[:6])
        lines.append(f"**流年前六年**（干支×十神对照，不批吉凶）：{head}…")
        lines.append("")
    lines += [
        "以上为机械排盘与扶抑口径推演，**不是命运断言**。",
        "格局从格仅作 tentative 标注；重大决策以专业意见为准。",
        "本模块不宣称现实预测命中率（`AGENTS.md` 铁律三）。",
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

        a = _analyze(_chart(datetime_str="1990-05-20 10:30", gender="男"))

    text = narrate(a)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
