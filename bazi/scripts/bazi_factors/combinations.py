# -*- coding: utf-8 -*-
"""combinations —— 三会 / 四柱干支关系 / 天克地冲 / 十神组合 / 通关关隔。
"""
from __future__ import annotations

from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

from ._common import (
    _god_detail,
    _ke_wo,
    _REL_BASIS,
    BRANCH_ELEMENTS,
    CHONG_PAIRS,
    HARM_PAIRS,
    HE_PAIRS,
    KE_CYCLE,
    PILLAR_LABEL,
    PILLAR_ORDER,
    SAN_HUI_GROUPS,
    SHENG_CYCLE,
    STEM_ELEMENTS,
    TEN_GOD_COMBO_RULES,
    TEN_GOD_GROUP,
    sanxing_hits as _sanxing_hits,
    stems_wuhe,
    ten_god,
)


def san_hui_present(pillars: dict) -> list[dict]:
    """四支中构成完整三会方局者。"""
    branches = [(pillars.get(k) or {}).get("branch") or ""
                for k in ("year", "month", "day", "hour")]
    bs = [b for b in branches if b]
    out = []
    for elem, grp in SAN_HUI_GROUPS.items():
        if set(grp) <= set(bs):
            out.append({"element": elem, "branches": list(grp),
                        "basis": "三会方局（《三命通会》：寅卯辰木/巳午未火/申酉戌金/亥子丑水）"})
    return out


def pillar_relations(chart_json: dict) -> list[dict]:
    """四柱干支两两关系：机械结构标签，不批吉凶。"""
    pillars = chart_json.get("pillars") or {}
    he = {frozenset(p) for p in HE_PAIRS}
    chong = {frozenset(p) for p in CHONG_PAIRS}
    harm = {frozenset(p) for p in HARM_PAIRS}

    out: list[dict] = []
    wuhe_pairs: list[tuple] = []
    for i, a in enumerate(PILLAR_ORDER):
        for b in PILLAR_ORDER[i + 1:]:
            sa = (pillars.get(a) or {}).get("stem") or ""
            sb = (pillars.get(b) or {}).get("stem") or ""
            if sa and sb and stems_wuhe(sa, sb):
                la, lb = PILLAR_LABEL[a], PILLAR_LABEL[b]
                wuhe_pairs.append((a, b, sa, sb, la, lb))
                out.append({
                    "type": "天干合",
                    "positions": [la, lb],
                    "stems": [sa, sb],
                    "text": f"{la}{lb}干{sa}{sb}合",
                    "basis": _REL_BASIS["天干合"],
                })
            ba = (pillars.get(a) or {}).get("branch") or ""
            bb = (pillars.get(b) or {}).get("branch") or ""
            if not ba or not bb:
                continue
            pair = frozenset((ba, bb))
            kind = ("六合" if pair in he else "六冲" if pair in chong
                    else "六害" if pair in harm else "")
            if not kind:
                continue
            la, lb = PILLAR_LABEL[a], PILLAR_LABEL[b]
            out.append({
                "type": kind,
                "positions": [la, lb],
                "branches": [ba, bb],
                "text": f"{la}{lb}支{ba}{bb}{kind}",
                "basis": _REL_BASIS[kind],
            })

    branches = [(pillars.get(k) or {}).get("branch") or "" for k in PILLAR_ORDER]

    # 天干争合
    pair_by_stem_pos: dict = {}
    for a, b, sa, sb, la, lb in wuhe_pairs:
        pair_by_stem_pos.setdefault((a, sa), []).append((b, sb, lb))
        pair_by_stem_pos.setdefault((b, sb), []).append((a, sa, la))
    for (pos, stem), partners in sorted(pair_by_stem_pos.items()):
        if len(partners) < 2:
            continue
        partner_stem = partners[0][1]
        labels = sorted({lb for _, _, lb in partners})
        out.append({
            "type": "天干争合",
            "positions": [PILLAR_LABEL[pos]] + labels,
            "stems": [stem, partner_stem],
            "text": f"{PILLAR_LABEL[pos]}干{stem}逢{len(partners)}{partner_stem}争合",
            "basis": _REL_BASIS["天干争合"],
        })

    for name in _sanxing_hits([b for b in branches if b]):
        out.append({
            "type": "三刑",
            "positions": [],
            "branches": [],
            "text": name,
            "basis": _REL_BASIS["三刑"],
        })
    return out


def tian_ke_di_chong(chart_json: dict, *, dayun: list[dict] | None = None,
                     liunian: list[dict] | None = None) -> list[dict]:
    """天克地冲：某大运柱 / 流年柱 与 **日柱** 天干相克且地支相冲。"""
    pillars = chart_json.get("pillars") or {}
    day_gz = (pillars.get("day") or {}).get("ganzhi") or ""
    if len(day_gz) < 2:
        return []

    # Deferred imports to avoid issues
    from .dayun import dayun_table as _dayun_table, liunian_table as _liunian_table
    if dayun is None:
        dayun = _dayun_table(chart_json)
    if liunian is None:
        liunian = _liunian_table(chart_json, n=12)
    out = []
    for d in dayun or []:
        gz = d.get("ganzhi") or ""
        if _tian_ke(gz, day_gz) and _di_chong(gz, day_gz):
            out.append({"kind": "dayun", "ganzhi": gz, "vs": day_gz,
                        "start_age": d.get("start_age"),
                        "text": f"大运{gz}与日柱{day_gz}天克地冲"})
    for y in liunian or []:
        gz = y.get("ganzhi") or ""
        if _tian_ke(gz, day_gz) and _di_chong(gz, day_gz):
            out.append({"kind": "liunian", "ganzhi": gz, "vs": day_gz,
                        "year": y.get("year"),
                        "text": f"流年{gz}与日柱{day_gz}天克地冲"})
    return out


def ten_god_combos(chart_json: dict, strength: str = "") -> list[dict]:
    """十神组合结构标签（透干层面）。"""
    gods = {g["god"] for g in _god_detail(chart_json)}
    out = []
    for name, lhs, rhs, basis in TEN_GOD_COMBO_RULES:
        if gods & set(lhs) and gods & set(rhs):
            out.append({"name": name, "basis": basis})
    if ({"正财", "偏财"} & gods) and ({"偏官", "七杀"} & gods) and strength == "偏弱":
        out.append({"name": "财滋弱杀", "basis": "财与七杀并透而身弱（财滋弱杀结构）"})
    return out


def tong_guan(chart_json: dict) -> list[dict]:
    """日主两路「通关／关隔」结构标签。"""
    pillars = chart_json.get("pillars") or {}
    present: list[str] = []
    for key in ("year", "month", "day", "hour"):
        p = pillars.get(key) or {}
        for el in (STEM_ELEMENTS.get(p.get("stem") or ""),
                   BRANCH_ELEMENTS.get(p.get("branch") or "")):
            if el and el not in present:
                present.append(el)
    day_elem = STEM_ELEMENTS.get((pillars.get("day") or {}).get("stem") or "")
    if not day_elem:
        return []
    pset = set(present)
    out = []
    for name, attacker, victim, mediator_role in (
            ("官杀克身", _ke_wo(day_elem), day_elem, "印"),
            ("身财相战", day_elem, KE_CYCLE.get(day_elem, ""), "食伤")):
        if not attacker or not victim or attacker not in pset or victim not in pset:
            continue
        mediator = SHENG_CYCLE.get(attacker, "")
        if not mediator:
            continue
        through = mediator in pset
        relation = f"{attacker}克{victim}"
        out.append({
            "name": name,
            "克": attacker,
            "被克": victim,
            "中介": mediator,
            "中介角色": mediator_role,
            "通关": through,
            "label": f"{name}（{relation}）：得{mediator}（{mediator_role}）通关" if through
                     else f"{name}（{relation}）：无{mediator}（{mediator_role}）为关隔",
            "basis": "《滴天髓·通隔論》：兩意本相通，中間有關隔，此關若通也，到處歡相得"
                     f"（局中{'有' if through else '无'}{mediator}）",
        })
    return out


# ── 内部辅助 ──────────────────────────────────────────────────────────────────

def _tian_ke(ganzhi_a: str, ganzhi_b: str) -> bool:
    """两柱天干五行相克。"""
    if len(ganzhi_a) < 1 or len(ganzhi_b) < 1:
        return False
    ea, eb = STEM_ELEMENTS.get(ganzhi_a[0]), STEM_ELEMENTS.get(ganzhi_b[0])
    if not ea or not eb:
        return False
    return KE_CYCLE.get(ea) == eb or KE_CYCLE.get(eb) == ea


def _di_chong(ganzhi_a: str, ganzhi_b: str) -> bool:
    """两柱地支相冲。"""
    if len(ganzhi_a) < 2 or len(ganzhi_b) < 2:
        return False
    return frozenset((ganzhi_a[1], ganzhi_b[1])) in {frozenset(p) for p in CHONG_PAIRS}
