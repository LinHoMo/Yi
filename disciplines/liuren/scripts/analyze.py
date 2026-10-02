# -*- coding: utf-8 -*-
"""大六壬·规则推演（analyze 段）—— 纯机械标签，无吉凶断语。

第一版判据（NEW-DISCIPLINES §2.1，本轮落地 ①②③）：
  ① 九宗门取三传（chart 段已完成，此处带出课体与门类）；
  ② 三传与日干支关系：鬼/德/合/墓/破/害/刑/冲（卷一「神煞」篇与 core 关系表）；
  ③ 十二天将乘临（chart 段布好，此处逐传带出）。
④ 课目识别（判据见 `scripts/kemu.py` 的 `IMPLEMENTED`，条数由该元组实算）、
⑤应期未落地——登记于 docs/TECH-DEBT.md（不写占位实现）。
本段**不出吉凶方向**：大六壬判吉凶须课目全表与《毕法赋》支撑，那两块落地前
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
    SHENG_CYCLE,
    STEM_ELEMENTS,
    THREE_PUNISHMENTS_CYCLIC,
    THREE_PUNISHMENTS_MUTUAL,
    TOMB_MAP,
)
from jiuzongmen import four_courses  # noqa: E402
from kemu import IMPLEMENTED as KEMU_IMPLEMENTED  # noqa: E402
from kemu import recognize as kemu_recognize  # noqa: E402


def _load_verdicts() -> dict:
    return json.loads((DISC / "data" / "verdicts.json").read_text(encoding="utf-8"))


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
# 墓库唯一真值源在 core（AGENTS.md §二），此处仅别名
_TOMB_OF_ELEM = dict(TOMB_MAP)


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


def _richen(chart_out: dict, verdicts: dict) -> list[dict]:
    """日辰关系（《六壬大全》卷三「日辰」歌赋）：干/支与其上神的生克结构标签。

    只判**日干、日支**各自与其上神（四课之上神）之间的生克，共 10 条判据；
    标签名、释义与诀文一律取 `data/verdicts.json#richen`（代码零断语字面量）。
    只出结构标签与书源引文，不作吉凶方向（AGENTS.md 铁律一/三）。
    """
    moment = chart_out.get("moment") or {}
    day_gz = moment.get("day_ganzhi") or ""
    tianpan = chart_out.get("tianpan") or {}
    if len(day_gz) < 2 or not tianpan:
        return []
    day_stem, day_branch = day_gz[0], day_gz[1]
    courses = four_courses(day_stem, day_branch, tianpan)
    sg, sz = courses[0]["shang"], courses[2]["shang"]          # 干上神 / 支上神
    g, z = STEM_ELEMENTS[day_stem], BRANCH_ELEMENTS[day_branch]
    sge, sze = BRANCH_ELEMENTS[sg], BRANCH_ELEMENTS[sz]
    spec = verdicts.get("richen") or {}
    src = spec.get("出处") or ""
    cond = (
        ("日上生干", SHENG_CYCLE.get(sge) == g),
        ("日上克干", KE_CYCLE.get(sge) == g),
        ("干生上神", SHENG_CYCLE.get(g) == sge),
        ("干克上神", KE_CYCLE.get(g) == sge),
        ("日上生辰", SHENG_CYCLE.get(sge) == z),
        ("辰上生干", SHENG_CYCLE.get(sze) == g),
        ("日上克辰", KE_CYCLE.get(sge) == z),
        ("辰上克干", KE_CYCLE.get(sze) == g),
        ("日辰俱受生", SHENG_CYCLE.get(sge) == g and SHENG_CYCLE.get(sze) == z),
        ("日辰俱受克", KE_CYCLE.get(sge) == g and KE_CYCLE.get(sze) == z),
    )
    out: list[dict] = []
    for name, ok in cond:
        if not ok:
            continue
        entry = spec.get(name) or {}
        out.append({"name": name, "desc": entry.get("desc") or "",
                    "basis": (f"干上神{sg}({sge})、支上神{sz}({sze})与日"
                              f"{day_stem}({g})、支{day_branch}({z})论生克"),
                    "句": entry.get("句") or "", "出处": src})
    return out


def analyze(chart_out: dict) -> dict:
    day_gz = chart_out["moment"]["day_ganzhi"]
    day_stem, day_branch = day_gz[0], day_gz[1]
    verdicts = _load_verdicts()
    men_desc = (verdicts.get("men") or {}).get(chart_out["men"], {})

    chuan_rows = []
    for i, b in enumerate(chart_out["san_chuan"], start=1):
        chuan_rows.append({
            "pos": ("初", "中", "末")[i - 1],
            "branch": b,
            "dun_gan": chart_out["dun_gan"][i - 1],
            "tianjiang": (chart_out.get("chuan_tianjiang") or [{}])[i - 1].get("jiang", ""),
            "relations": _relations_of(b, day_stem, day_branch),
        })

    kemu_hits = kemu_recognize(chart_out)
    richen = _richen(chart_out, verdicts)
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
        {"code": "richen", "label": "日辰关系（卷三「日辰」歌）",
         "basis": "；".join(r["name"] for r in richen) if richen
                  else "无已落判据的日辰关系命中"},  # 诀文见 data/verdicts.json#richen
        {"code": "kemu", "label": f"课目识别（已落机械判据 {len(KEMU_IMPLEMENTED)} 条）",
         "basis": "；".join(h["name"] for h in kemu_hits) if kemu_hits
                  else "无已落判据的课目命中"},  # 诀文/释义见 data/kemu.json
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
        "richen": richen,
        "san_chuan": chuan_rows,
        "kemu": kemu_hits,
        "factors": factors,
        "conclusion": {
            "strength": None,
            "pattern": chart_out["ke_name"],
            "direction": None,
            "note": f"不含吉凶方向：课目识别已落 {len(KEMU_IMPLEMENTED)} 条**纯结构**判据"
                    "（旺相/神煞/年命依赖者仍未落地），"
                    "《毕法赋》判据未接入，不写占位实现（TECH-DEBT 登记）",
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
