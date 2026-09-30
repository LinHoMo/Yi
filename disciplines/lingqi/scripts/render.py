# -*- coding: utf-8 -*-
"""灵棋经·报告渲染（render 段）—— 薄层，Markdown 报告。

    python scripts/render.py [analyze.json] [-o report.md]
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

from narrate import narrate  # noqa: E402


def render(analyze_out: dict, out_path: Path | None = None) -> str:
    lines = [narrate(analyze_out), ""]
    lines += ["## 课表附录（机器可复核）", ""]
    lines.append(f"- 课号：{analyze_out.get('chart_summary', {}).get('课号', '—')}")
    lines.append(f"- 课名：{analyze_out.get('ke_name', '—')}")
    lines.append(f"- 因子：{'; '.join(f.get('label', '') for f in analyze_out.get('factors') or [])}")
    lines += ["", f"生成：discipline={analyze_out.get('discipline')}，"
              "四段契约 chart→analyze→narrate→render。"]
    text = "\n".join(lines) + "\n"
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description="灵棋经报告渲染（Markdown）")
    ap.add_argument("analyze_file", nargs="?", default="", help="analyze 段 JSON 路径")
    ap.add_argument("--out", "-o", help="输出 MD 路径（缺省打印 stdout）")
    args = ap.parse_args()
    a = json.loads(Path(args.analyze_file).read_text(encoding="utf-8")) \
        if args.analyze_file else {}
    text = render(a, Path(args.out) if args.out else None)
    if not args.out:
        print(text)
    else:
        print(f"render 已写出 → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
