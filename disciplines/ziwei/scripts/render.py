# -*- coding: utf-8 -*-
"""紫微斗数·报告（render 段）—— 薄层：因子表 + narrate 正文。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.ziwei_tables import PALACES  # noqa: E402

from narrate import narrate  # noqa: E402


def render(analyze_out: dict) -> str:
    s = analyze_out.get("chart_summary") or {}
    lines = [narrate(analyze_out), "", "## 机械因子", "", "| 项 | 值 |", "|---|---|"]
    for k, v in s.items():
        lines.append(f"| {k} | {v if v is not None else '—'} |")
    palaces = analyze_out.get("palaces") or {}
    if palaces:
        lines += ["", "## 十二宫星曜", "", "| 宫 | 主星 | 辅星 | 四化 |", "|---|---|---|---|"]
        for pname in PALACES:   # 宫序唯一真值源在 core.ziwei_tables.PALACES
            p = palaces.get(pname, {})
            mh = "、".join(p.get("main_stars") or []) or "—"
            ah = "、".join(p.get("aux_stars") or []) or "—"
            sh = "、".join(p.get("sihua") or []) or "—"
            lines.append(f"| {pname}({p.get('branch', '')}) | {mh} | {ah} | {sh} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="紫微斗数·报告（render 段）")
    ap.add_argument("analyze_json", nargs="?")
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args()

    if args.analyze_json:
        a = json.loads(Path(args.analyze_json).read_text(encoding="utf-8"))
    else:
        from analyze import ziwei_analyze as _analyze
        from chart import ziwei_chart as _chart

        a = _analyze(_chart(datetime_str="1990-05-20 10:30", gender="男"))

    text = render(a)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
