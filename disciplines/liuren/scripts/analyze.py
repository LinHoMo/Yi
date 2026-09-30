# -*- coding: utf-8 -*-
"""大六壬·规则推演（analyze 段）—— 纯机械标签，无吉凶断语。

第一版判据（NEW-DISCIPLINES §2.1，本轮落地 ①②③）：
  ① 九宗门取三传（chart 段已完成，此处带出课体与门类）；
  ② 三传与日干支关系：鬼/德/合/墓/破/害/刑/冲（卷一「神煞」篇与 core 关系表）；
  ③ 十二天将乘临（chart 段布好，此处逐传带出）。
④65 课目识别、⑤应期未落地——登记于 docs/TECH-DEBT.md（不写占位实现）。
本段**不出吉凶方向**：大六壬判吉凶须 65 课目与《毕法赋》支撑，那两块落地前
任何「方向」输出都是臆测（AGENTS.md 铁律一/三）。
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

from yishu_core.liuren_tables import DAY_DE, JI_GONG  # noqa: E402
from yishu_core.symbols import (  # noqa: E402
    BREAK_PAIRS,
    BRANCH_ELEMENTS,
    CHONG_PAIRS,
    HARM_PAIRS,
    HE_PAIRS,
    KE_CYCLE,
    SELF_PUNISHMENTS,
    STEM_ELEMENTS,
    THREE_PUNISHMENTS_CYCLIC,
    THREE_PUNISHMENTS_MUTUAL,
)
from chart import dun_gan_of  # noqa: E402


def _load_verdicts() -> dict:
    return json.loads((DISC / "data" / "verdicts.json").read_text(encoding="utf-8"))


_CHONG = {x for pair in CHONG_PAIRS for x in pair}
_HE = {x for pair in HE_PAIRS for x in pair}
_HARM = {x for pair in HARM_PAIRS for x in pair}
_BREAK = {x for pair in BREAK_PAIRS for x in pair}
_XING: dict[str, set[str]] = {}
for _cyc in THREE_PUNISHMENTS_CYCLIC.values():
    for _i, _b in enumerate(_cyc):
        _XING.setdefault(_b, set()).add(_cyc[(_i + 1) % 3])
for _a, _b in THREE_PUNISHMENTS_MUTUAL.values():
    _XING.setdefault(_a, set()).add(_b)
    _XING.setdefault(_b, set()).add(_a)
for _s in SELF_PUNISHMENTS:
    _XING.setdefault(_s, set()).add(_s)
_KE_OF = dict(KE_CYCLE)
_HE_SET = {frozenset(p) for p in HE_PAIRS}
_CHONG_SET = {frozenset(p) for p in CHONG_PAIRS}
_HARM_SET = {frozenset(p) for p in HARM_PAIRS}
_BREAK_SET = {frozenset(p) for p in BREAK_PAIRS}
_TOMB_OF_ELEM = {"木": "未", "火": "戌", "金": "丑", "水": "辰", "土": "辰"}


def _relations_of(chuan: str, day_stem: str, day_branch: str) -> list[dict]:
    """一传与日干（寄宫）/日支的结构关系（鬼德合墓破害刑冲）。"""
    rels: list[dict] = []
    jigong = JI_GONG[day_stem]
    day_elem = STEM_ELEMENTS[day_stem]
    chuan_elem = BRANCH_ELEMENTS[chuan]
    if _KE_OF.get(chuan_elem) == day_elem:
        rels.append({"kind": "鬼", "target": "日干",
                     "note": f"{chuan_elem}克{day_elem}"})
    if chuan == DAY_DE[day_stem]:
        rels.append({"kind": "德", "target": "日干",
                     "note": f"日德在{DAY_DE[day_stem]}"})
    if chuan == _TOMB_OF_ELEM[day_elem]:
        rels.append({"kind": "墓", "target": "日干",
                     "note": f"{day_elem}墓在{chuan}"})
    for name, base in (("日干寄宫", jigong), ("日支", day_branch)):
        if chuan != base:
            pair = frozenset({chuan, base})
            if pair in _HE_SET:
                rels.append({"kind": "合", "target": name})
            if pair in _CHONG_SET:
                rels.append({"kind": "冲", "target": name})
            if pair in _HARM_SET:
                rels.append({"kind": "害", "target": name})
            if pair in _BREAK_SET:
                rels.append({"kind": "破", "target": name})
        if chuan in _XING.get(base, set()) or base in _XING.get(chuan, set()):
            kind = "自刑" if chuan == base else "刑"
            rels.append({"kind": kind, "target": name})
    return rels


def analyze(chart_out: dict) -> dict:
    day_gz = chart_out["moment"]["day_ganzhi"]
    day_stem, day_branch = day_gz[0], day_gz[1]
    verdicts = _load_verdicts()
    men_desc = (verdicts.get("men") or {}).get(chart_out["men"], {})
    tianjiang = chart_out.get("tianjiang_layout") or {}

    chuan_rows = []
    for i, b in enumerate(chart_out["san_chuan"], start=1):
        chuan_rows.append({
            "pos": ("初", "中", "末")[i - 1],
            "branch": b,
            "dun_gan": chart_out["dun_gan"][i - 1],
            "tianjiang": (chart_out.get("chuan_tianjiang") or [{}])[i - 1].get("jiang", ""),
            "relations": _relations_of(b, day_stem, day_branch),
        })

    factors = [
        {"code": "men", "label": chart_out["men"],
         "basis": chart_out.get("men_trigger", "")},
        {"code": "ke_name", "label": chart_out["ke_name"],
         "basis": men_desc.get("basis", "")},
        {"code": "san_chuan", "label": "、".join(chart_out["san_chuan"]),
         "basis": "三传遁干：" + "、".join(chart_out["dun_gan"])},
        {"code": "relations", "label": "三传与日干支关系",
         "basis": "；".join(f"{r['pos']}{r['branch']}"
                            + ("（" + "/".join(x["kind"] for x in r["relations"]) + "）"
                               if r["relations"] else "（无关系标签）")
                            for r in chuan_rows)},
    ]
    return {
        "discipline": "liuren",
        "id": chart_out.get("id", ""),
        "question": chart_out.get("question", ""),
        "chart_summary": {
            "日干支": day_gz,
            "时支": chart_out["moment"]["hour_branch"],
            "月将": chart_out["yuejiang"]["name"] + "（" + chart_out["yuejiang"]["branch"] + "）",
            "空亡": chart_out["moment"]["xunkong"],
            "天地盘": chart_out["tianpan"],
        },
        "men": chart_out["men"],
        "ke_name": chart_out["ke_name"],
        "san_chuan": chuan_rows,
        "factors": factors,
        "conclusion": {
            "strength": None,
            "pattern": chart_out["ke_name"],
            "direction": None,
            "note": "第一版不含吉凶方向：65 课目识别与《毕法赋》未落地，"
                    "不写占位实现（TECH-DEBT 登记）",
        },
        "verdicts_note": verdicts.get("preamble", []),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="大六壬规则推演（机械标签，无吉凶断语）")
    ap.add_argument("chart_file", help="chart 段输出的 JSON 路径")
    ap.add_argument("--out", "-o", help="输出 JSON 路径（缺省打印 stdout）")
    args = ap.parse_args()
    chart_out = json.loads(Path(args.chart_file).read_text(encoding="utf-8"))
    out = analyze(chart_out)
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"analyze 已写出 → {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
