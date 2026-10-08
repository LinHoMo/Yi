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
        _tj = row.get("tianjiang") or "—"
        _tj_pos = row.get("tianjiang_pos") or ""
        _cheng = f"{_tj}×{_tj_pos}" if _tj_pos else _tj
        lines.append(
            f"- {row['pos']}传 {row['branch']}（乘{_cheng}"
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
    alias = a.get("richen_alias") or {}
    alias_map = alias.get("别名") or {}
    if alias_map:
        lines += ["", "**日辰四气别名**（《六壬鬼谷》L65-L68；别名只为显示层，"
                       "判定键仍用上列卷三直陈式）："]
        for name, hits in alias_map.items():
            lines.append(f"- **{name}**：{'、'.join(hits)}")
    st = a.get("structure_tags") or {}
    if st:
        lines += ["", "**结构标签**（与课目正交；只报机械位置，不判吉凶）："]
        for dim, rows in st.items():
            lines.append(f"- **{dim}**：")
            for r in rows:
                lines.append(f"  - {r['name']}——{r['basis']}")
                if r.get("note"):
                    lines.append(f"    > 判据边界：{r['note']}")
    cg = a.get("class_god") or {}
    if cg:
        jiang = cg.get("类将回退") or {}
        lines += ["", "**类神类将**（取象派专有层，与九宗门三传并存；只报定位）："]
        lines.append(f"- 类将取 **{jiang.get('类将') or '—'}**"
                     f"（位次：{jiang.get('位次') or '—'}；回退链："
                     f"{' → '.join(jiang.get('回退链') or [])}）——{jiang.get('依据') or ''}")
        for r in cg.get("类神之三传") or []:
            lines.append(f"  - {r['name']}——{r['basis']}")
            if r.get("note"):
                lines.append(f"    > {r['note']}")
    wx = a.get("wangxiangxiuqiusi") or {}
    if wx:
        lines += ["", "**旺相休囚死**（月令旺衰，core wangxiangxiuqiusi 表；纯结构标签，不判吉凶）："]
        for label, info in wx.items():
            lines.append(f"- **{label}**：{info.get('branch') or '—'}（{info.get('element') or '—'}）"
                         f" → **{info.get('state') or '—'}**（{info.get('basis') or ''}）")
    rg = a.get("rengui") or {}
    if rg.get("内外事"):
        yq = rg.get("应期映射表") or {}
        lines += ["", "**用神内外事 + 应期层级**（《壬归》L109/L112；纯几何标签，不判吉凶）："]
        lines.append(f"- 内外事定位：**{rg['内外事']}**（初传落{'日上' if rg['内外事'] == '外事' else '辰上'}两课）")
        if yq:
            lines.append(f"- 应期层级映射表（{len(yq)}级）：")
            for ref, meta in yq.items():
                lines.append(f"  - {ref} → **{meta.get('granularity')}**（{meta.get('basis')}）")
        hits = rg.get("动态应期命中") or []
        if hits:
            lines.append(f"- 本轮应期命中（{len(hits)}条）：")
            for h in hits:
                lines.append(f"  - {h['reference']} → **{h['granularity']}**（{h['basis']}）")
        else:
            lines.append("- 本轮应期命中：无（月建/旬首/气首等参考项与初传无直接匹配）")
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
