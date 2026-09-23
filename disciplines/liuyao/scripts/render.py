# -*- coding: utf-8 -*-
"""六爻纳甲·报告渲染（render 段）—— analyze JSON → Markdown 报告。

薄适配：复用 narrate 正文 + conclusion 摘要，组织成与三科 render 同构的
单文件 Markdown 报告。不引入新结论。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from narrate import narrate  # noqa: E402


def _summary_block(a: dict) -> list[str]:
    con = a.get("conclusion") or {}
    s = a.get("divination_time") or {}
    oh = a.get("original_hexagram") or {}
    lines = []
    if a.get("question"):
        lines.append(f"- **问**：{a['question']}")
    if s.get("datetime"):
        lines.append(f"- **起卦时刻**：{s['datetime']}")
    if oh.get("name"):
        lines.append(f"- **本卦**：{oh['name']}"
                     + (f"（{oh.get('palace') or ''}宫）" if oh.get("palace") else ""))
    ch = a.get("changed_hexagram") or {}
    if ch.get("name"):
        lines.append(f"- **变卦**：{ch['name']}")
    if con.get("方向"):
        lines.append(f"- **结论**：{con['方向']}"
                     + (f"（置信度 {con.get('置信度')}）" if con.get("置信度") else ""))
    if con.get("应期"):
        lines.append("- **应期**：" + "、".join(map(str, con["应期"])))
    return lines


def render(a: dict) -> str:
    """analyze JSON → Markdown 报告。"""
    con = a.get("conclusion") or {}
    lines = ["# 六爻纳甲占报告", ""]
    lines += ["## 一、结要", ""]
    summary = _summary_block(a)
    if summary:
        lines += summary
    else:
        lines.append("（结论见正文）")
    lines += ["", "## 二、正文", ""]
    lines.append(narrate(a))
    if con.get("所本"):
        lines += ["", "## 三、判据所本", "", f"{con['所本']}。", ""]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="六爻纳甲报告渲染（render 段）")
    ap.add_argument("analyze_json", nargs="?", help="analyze 输出的 JSON 文件（缺省跑演示）")
    ap.add_argument("-o", "--out", type=Path, help="写出 Markdown 报告")
    args = ap.parse_args()

    if args.analyze_json:
        a = json.loads(Path(args.analyze_json).read_text(encoding="utf-8"))
    else:
        from analyze import analyze as _analyze
        from chart import chart as _chart
        a = _analyze(_chart("coin", "占当前所问之事", seed=42))

    text = render(a)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
