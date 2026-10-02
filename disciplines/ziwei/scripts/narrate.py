# -*- coding: utf-8 -*-
"""紫微斗数·正文（narrate 段）—— 逐条引用《紫微斗數全書》原文，不写命运断言。

引文与释义一律来自 data/*.json（`dev_tools/build_corpus.py` 从书源字符级提取，
逐条带书名 + 卷/篇 + 原文）：
  star_nature.json            主星性情说解（卷一·諸星問答論）
  star_palace.json            十二宫诸星释义（卷二各宫段）
  star_brightness.json        星 × 宫支 庙陷（卷二「一 命宫」本宫诗明文）
  sihua_quotes.json           四化释义（卷一·問化祿/權/科/忌星所主若何）
  geju_rules.json             定富/贵/贫贱/杂局判据（卷一）
  anshi_quotes.json           卷二各「安××诀」原文（安星所本）
  ziwei_position_table.json   五局 × 农历日 → 紫微宫支（卷二安紫微图 + 安身命例例题）
本文件只写结构与措辞，不写断语。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from yishu_core.runtime import force_utf8_stdio  # noqa: E402

_DATA = Path(__file__).resolve().parent.parent / "data"
AUX_STAR_NAMES = ("文昌", "文曲", "左辅", "右弼", "天魁", "天钺", "禄存", "擎羊",
                  "陀罗", "火星", "铃星", "天马", "地空", "地劫", "天刑", "天姚",
                  "天哭", "天虚", "龙池", "凤阁", "三台", "八座", "台辅", "封诰")


def _load(name: str) -> dict:
    path = _DATA / name
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


_VERDICTS = _load("verdicts.json")
_NATURE = _load("star_nature.json").get("stars") or {}
_PALACE_Q = _load("star_palace.json").get("palaces") or {}
_BRIGHT = _load("star_brightness.json").get("table") or {}
_SIHUA_Q = _load("sihua_quotes.json").get("hua") or {}
_GEJU = _load("geju_rules.json").get("rules") or {}
_ANSHI = _load("anshi_quotes.json").get("rules") or {}
_POS = _load("ziwei_position_table.json")


def _cite(quote: str, location: str) -> str:
    """逐字引文 + 出处（书源括注）。"""
    return f"> {quote}（{location}）"


def _star_branch(a: dict) -> dict[str, str]:
    """星名 → 所在宫支（主星 + 辅星）。"""
    out: dict[str, str] = {}
    for p in (a.get("palaces") or {}).values():
        for star in (p.get("main_stars") or []) + (p.get("aux_stars") or []):
            out[star] = p.get("branch", "")
    return out


def narrate(a: dict) -> str:
    s = a.get("chart_summary") or {}
    con = a.get("conclusion") or {}
    lu = a.get("lunar") or {}
    palaces = a.get("palaces") or {}
    mg_stars = s.get("命宫主星") or "—"
    pattern = s.get("格局") or "—"
    mg_branch = s.get("命宫地支") or "—"
    bright_of = {star: _BRIGHT.get(star, {}) for star in (mg_stars.split("、") if mg_stars else [])}
    at = _star_branch(a)
    leap = "闰" if lu.get("leap") else ""

    lines = [
        "# 紫微斗数命盘因子说明",
        "",
        f"**农历**：{lu.get('year', '')} 年{leap}{lu.get('month', '')} 月{lu.get('day', '')} 日"
        f"（安星依据）。**四柱**：{'、'.join((a.get('pillars') or {}).values())}。",
        f"**五行局**：{s.get('五行局') or '—'}。**命宫**：在{mg_branch}宫。"
        f"**身宫**：在{(a.get('shen_gong') or {}).get('branch', '—')}宫。",
        f"**命宫主星**：{mg_stars}。**格局**：{pattern}（{s.get('格局依据') or ''}）。",
        f"**紫微**在{s.get('紫微所在') or '—'}，**天府**在{s.get('天府所在') or '—'}。",
        "",
    ]

    # ── 命宫主星：庙陷 + 卷一性情说解 + 卷二本宫释义 ──────────────────────
    lines.append("## 命宫主星")
    for star in (mg_stars.split("、") if mg_stars else []):
        br = at.get(star, mg_branch)
        lv = (bright_of.get(star, {}).get(br) or {}).get("levels") or []
        if lv:
            src = (bright_of[star][br] or {}).get("quote", "")
            lines.append(f"**{star}**（在{br}宫，{lv[0]}）：")
            lines.append(_cite(src, f"《紫微斗數全書》卷二·一 命宫·{star}本宫诗"))
        nat = _NATURE.get(star) or {}
        if nat.get("quote"):
            lines.append(f"**{star}·性情说解**：")
            lines.append(_cite(nat["quote"], nat.get("location", "")))
        pq = ((_PALACE_Q.get("命宫") or {}).get(star) or {})
        if pq.get("quote"):
            lines.append(_cite(pq["quote"], pq.get("location", "")))
        lines.append("")

    # ── 命宫辅煞星：卷一性情说解 + 卷二本宫释义（书源有者才出，不可得则不出）──
    aux_block: list[str] = []
    for star in ((palaces.get("命宫") or {}).get("aux_stars") or []):
        nat = _NATURE.get(star) or {}
        pq = ((_PALACE_Q.get("命宫") or {}).get(star) or {})
        if not (nat.get("quote") or pq.get("quote")):
            continue
        aux_block.append(f"**{star}**（在{at.get(star, mg_branch)}宫）：")
        if nat.get("quote"):
            aux_block.append(_cite(nat["quote"], nat.get("location", "")))
        if pq.get("quote"):
            aux_block.append(_cite(pq["quote"], pq.get("location", "")))
        aux_block.append("")
    if aux_block:
        lines.append("### 命宫辅煞星")
        lines += aux_block

    # ── 十二宫：本宫主星的书源释义 + 该宫庙陷 ──────────────────────────────
    lines.append("## 十二宫星义")
    for palace, pdata in palaces.items():
        stars = pdata.get("main_stars") or []
        if not stars:
            continue
        br = pdata.get("branch", "")
        entry = _PALACE_Q.get(palace) or {}
        for star in stars:
            lv = (_BRIGHT.get(star, {}).get(br) or {}).get("levels") or []
            q = entry.get(star) or {}
            tail = f"（{br}宫{lv[0]}）" if lv else ""
            if q.get("quote"):
                lines.append(f"- **{palace}**（{br}宫）{star}{tail}："
                             f"「{q['quote']}」（{q.get('location', '')}）")
    lines.append("")

    # ── 四化 ─────────────────────────────────────────────────────────────
    si_impact = con.get("四化影响") or []
    if si_impact:
        lines.append("## 四化影响")
        for si in si_impact:
            lines.append(f"- {si}")
        for token in ("禄", "权", "科", "忌"):
            hq = _SIHUA_Q.get(token) or {}
            if hq.get("quote"):
                lines.append(_cite(hq["quote"], hq.get("location", "")))
        lines.append("")

    # ── 古法格局（卷二判据；机械可判者逐条列明，成立与否都写）────────────
    classical = con.get("古法格局") or []
    lines.append("## 古法格局")
    if classical:
        for c in classical:
            mark = "成立" if c.get("成立") else "未成立"
            lines.append(f"- **{c['名']}**（{c.get('类别', '')}·{mark}）"
                         f"{c.get('判据', '')}　出处：{c.get('所本', '')}")
        lines.append("- " + str((_VERDICTS.get("口径") or {}).get("格局判据", "")))
    else:
        lines.append("- 本盘未取得可判局（判据语料缺失）。")
    lines.append("")

    # ── 安星所本：本盘用到的安星诀原文 ────────────────────────────────────
    used = [st for st in AUX_STAR_NAMES if st in at]
    picked = []
    for key, val in _ANSHI.items():
        if key.startswith(("安南北斗诸星诀", "安禄权科忌")):
            picked.append((key, val))
        elif any(st in key for st in used):
            picked.append((key, val))
    if picked:
        lines.append("## 安星所本")
        for key, val in picked:
            lines.append(_cite(val.get("quote", ""), val.get("location", key)))
        lines.append("")

    # ── 紫微定位所本（五局 × 农历日）─────────────────────────────────────
    example = _POS.get("body_example") or {}
    if example.get("quote"):
        lines.append("## 定位所本")
        lines.append(f"本盘：五行局 {(s.get('五行局') or '')}；农历 "
                     f"{lu.get('month', '')} 月 {lu.get('day', '')} 日；"
                     f"紫微在 {s.get('紫微所在') or '—'} 宫。")
        lines.append(_cite(example["quote"], example.get("location", "")))
        lines.append("")

    # ── 大限 ─────────────────────────────────────────────────────────────
    dayun = con.get("dayun") or []
    if dayun:
        lines.append(f"## 大限走向")
        lines.append(f"- 起宫 {dayun[0].get('palace', '')}"
                     f"（{dayun[0].get('direction', '')}），"
                     f"起运 {dayun[0].get('start_age')} 岁，每十年一宫。")
        for d in dayun[:8]:
            lines.append(f"- {d.get('start_age')}–{d.get('end_age')} 岁　"
                         f"第{d.get('step')}步　{d.get('palace', '')}（{d.get('direction')}）")
        lines.append("")

    lines.append("## 口径声明")
    lines += [
        "以上为机械排盘与格局口径推演，**不是命运断言**。",
        str((_VERDICTS.get("口径") or {}).get("凶象表述", "")),
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
