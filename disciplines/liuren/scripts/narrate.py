# -*- coding: utf-8 -*-
"""大六壬·人话叙述（narrate 段）—— 机械标签翻译成人话，不出吉凶断语。

文案一律取 data/verdicts.json（引文与出处），本文件只做编排。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
DISC = Path(__file__).resolve().parents[1]
for _p in (str(CORE), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _verdicts() -> dict:
    return json.loads((DISC / "data" / "verdicts.json").read_text(encoding="utf-8"))


def narrate(a: dict) -> str:
    v = _verdicts()
    s = a.get("chart_summary") or {}
    men = a.get("men") or ""
    men_desc = (v.get("men") or {}).get(men, {})
    lines = [
        "# 六壬课式说明",
        "",
        f"日干支：{s.get('日干支') or '—'}；时支：{s.get('时支') or '—'}；"
        f"月将：{s.get('月将') or '—'}；空亡：{'、'.join(s.get('空亡') or []) or '—'}。",
        "",
        f"**门类**：{men}——{men_desc.get('desc', '')}",
        f"**课体**：{a.get('ke_name') or '—'}",
        f"**取传依据**（原文）：{men_desc.get('basis', '')}",
        "",
        "**三传**（乘将·遁干·与日干支关系）：",
    ]
    for row in a.get("san_chuan") or []:
        rels = row.get("relations") or []
        rel_txt = "、".join(x["kind"] for x in rels) if rels else "无关系标签"
        lines.append(
            f"- {row['pos']}传 {row['branch']}（乘{row.get('tianjiang') or '—'}"
            f"，遁{row.get('dun_gan') or '—'}）：{rel_txt}"
        )
    tj = v.get("tianjiang") or {}
    tj_verses = {row.get("tianjiang") for row in a.get("san_chuan") or []
                 if row.get("tianjiang") and tj.get(row["tianjiang"])}
    if tj_verses:
        lines += ["", "**天将乘临歌诀**（书源引文，逐字照录；引擎不作判读）："]
        for name in sorted(tj_verses, key=lambda n: list(tj).index(n)):
            block = tj[name]
            lines.append(f"> {name}（{block.get('head')}）：{block.get('verse')}")
    richen = a.get("richen") or []
    if richen:
        lines += ["", "**日辰关系**（《六壬大全》卷三「日辰」歌赋；只报结构命中，不判吉凶）："]
        for r in richen:
            lines.append(f"- **{r['name']}**（{r.get('desc') or ''}）：{r.get('basis') or ''}")
            if r.get("句"):
                lines.append(f"  > {r['句']}（{r.get('出处') or ''}）")
    kemu_hits = a.get("kemu") or []
    kemu_rows = [h for h in kemu_hits if h.get("verse") or h.get("note")]
    if kemu_rows:
        lines += ["", "**课目**（诀文＝卷一「课目」歌诀逐字，释义＝卷七~卷十「课经集」"
                      "定义句逐字；只报结构命中，不判吉凶）："]
        for h in kemu_rows:
            lines.append(f"- **{h['name']}**：{h.get('verse') or ''}")
            if h.get("note"):
                lines.append(f"  > {h['note']}（{h.get('note_src') or ''}）")
            if h.get("partial"):
                lines.append(f"  > 判据边界：{h['partial']}")
    lines += ["", "以上为机械排盘与结构标签，**不是吉凶断语**。"]
    lines += list(a.get("verdicts_note") or v.get("preamble") or [])
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="大六壬人话叙述（机械标签，无吉凶断语）")
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
