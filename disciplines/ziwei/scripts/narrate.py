# -*- coding: utf-8 -*-
"""紫微斗数·正文（narrate 段）—— 叙述机械因子；禁止命运断言。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from yishu_core.runtime import force_utf8_stdio  # noqa: E402


def narrate(a: dict) -> str:
    s = a.get("chart_summary") or {}
    con = a.get("conclusion") or {}
    mg_stars = s.get("命宫主星") or "—"
    pattern = s.get("格局") or "—"
    ju = s.get("五行局") or "—"
    mg_branch = s.get("命宫地支") or "—"
    ziwei_loc = s.get("紫微所在") or "—"
    tianfu_loc = s.get("天府所在") or "—"
    si_impact = con.get("四化影响") or []
    dy_info = s.get("大限位序") or ""
    dayun = con.get("dayun") or []

    lines = [
        "# 紫微斗数命盘因子说明",
        "",
        f"**五行局**：{ju}。**命宫**：在{mg_branch}宫。**命宫主星**：{mg_stars}。",
        f"**格局**：{pattern}。**紫微**在{ziwei_loc}，**天府**在{tianfu_loc}。",
        "",
    ]

    if si_impact:
        lines.append("**四化影响**：")
        for si in si_impact:
            lines.append(f"- {si}")
        lines.append("")

    if dy_info:
        lines.append(f"**大限走向**：{dy_info}。")
        lines.append("")
    if dayun:
        lines.append("**大限简表**（每十年一宫，不批吉凶）：")
        for d in dayun[:8]:
            lines.append(
                f"- {d.get('start_age')}–{d.get('end_age')} 岁　第{d.get('step')}步"
                f"（{d.get('direction')}）"
            )
        lines.append("")

    lines += [
        "以上为机械排盘与格局口径推演，**不是命运断言**。",
        "格局从格仅作 tentative 标注；重大决策以专业意见为准。",
        "本模块不宣称现实预测命中率（`AGENTS.md` 铁律三）。",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="紫微斗数·正文（narrate 段）")
    ap.add_argument("analyze_json", nargs="?")
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args()

    if args.analyze_json:
        a = json.loads(Path(args.analyze_json).read_text(encoding="utf-8"))
    else:
        from analyze import ziwei_analyze as _analyze
        from chart import ziwei_chart as _chart

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
