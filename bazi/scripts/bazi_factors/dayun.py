# -*- coding: utf-8 -*-
"""dayun —— 大运 / 流年 / 大运×流年交互 / 胎元 / 流月 / 小运。
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

from ._common import (
    BRANCH_ELEMENTS,
    DAYS_PER_LUCK_YEAR,
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
    MONTHS_PER_DAY,
    PILLAR_LABEL,
    PILLAR_ORDER,
    _REL_BASIS,
    SAN_HE_GROUPS,
    SHENG_CYCLE,
    KE_CYCLE,
    CHONG_PAIRS,
    HE_PAIRS,
    TIGER_MONTH_STEM,
    dayun_direction,
    sanxing_hits,
    ten_god,
    STEM_ELEMENTS,
    CHONG_PAIRS as _CHONG_PAIRS,
)
from yishu_core.ganzhi_calendar import next_jie_after, prev_jie_before


def dayun_table(chart_json: dict) -> list[dict]:
    """大运 8 步（顺逆按年干阴阳×性别；起运岁按距节气日数折算）。"""
    pillars = chart_json.get("pillars") or {}
    year_stem = (pillars.get("year") or {}).get("stem") or ""
    month_gz = (pillars.get("month") or {}).get("ganzhi") or ""
    gender = (chart_json.get("birth") or {}).get("gender") or ""
    day_stem = (pillars.get("day") or {}).get("stem") or ""
    birth_dt_s = (chart_json.get("birth") or {}).get("datetime") or ""

    direction = dayun_direction(year_stem, gender) if year_stem and gender else None
    if not direction or len(month_gz) < 2:
        return []

    start_age = 3.0
    start_age_months = 0
    approximate = True
    jie_name = ""
    if birth_dt_s:
        try:
            bdt = datetime.strptime(str(birth_dt_s)[:16], "%Y-%m-%d %H:%M")
            jie = next_jie_after(bdt) if direction == "forward" else prev_jie_before(bdt)
            jie_dt = jie.get("instant") if isinstance(jie, dict) else None
            jie_name = (jie.get("name") or "") if isinstance(jie, dict) else ""
            if isinstance(jie_dt, datetime):
                days = abs((jie_dt - bdt).total_seconds()) / 86400.0
                years = days / float(DAYS_PER_LUCK_YEAR)
                start_age = round(years, 1)
                rem_days = days - int(days / DAYS_PER_LUCK_YEAR) * DAYS_PER_LUCK_YEAR
                start_age_months = int(round(rem_days * MONTHS_PER_DAY))
                approximate = True
        except Exception:
            start_age = 3.0

    stems, branches = HEAVENLY_STEMS, EARTHLY_BRANCHES
    ms, mb = month_gz[0], month_gz[1]
    try:
        si = stems.index(ms)
        bi = branches.index(mb)
    except ValueError:
        return []

    step = 1 if direction == "forward" else -1
    out = []
    for i in range(8):
        s = stems[(si + step * (i + 1)) % 10]
        b = branches[(bi + step * (i + 1)) % 12]
        gz = s + b
        main_god = ten_god(day_stem, s) if day_stem else None
        a0 = round(start_age + i * 10, 1)
        out.append({
            "index": i + 1,
            "ganzhi": gz,
            "start_age": a0,
            "end_age": round(a0 + 9.9, 1),
            "ten_god": main_god or "",
            "approximate": approximate,
        })
    return out


def liunian_table(chart_json: dict, n: int = 12) -> list[dict]:
    """流年干支×十神对照表（只机械对照，不批吉凶）。"""
    pillars = chart_json.get("pillars") or {}
    year_gz = (pillars.get("year") or {}).get("ganzhi") or ""
    day_stem = (pillars.get("day") or {}).get("stem") or ""
    birth_dt_s = (chart_json.get("birth") or {}).get("datetime") or ""
    if len(year_gz) < 2:
        return []

    stems, branches = HEAVENLY_STEMS, EARTHLY_BRANCHES
    try:
        yi, yb = stems.index(year_gz[0]), branches.index(year_gz[1])
    except ValueError:
        return []

    try:
        birth_year = datetime.strptime(str(birth_dt_s)[:10], "%Y-%m-%d").year
    except Exception:
        birth_year = datetime.now().year

    out = []
    for i in range(int(n)):
        s = stems[(yi + i) % 10]
        b = branches[(yb + i) % 12]
        gz = s + b
        out.append({
            "year": birth_year + i,
            "age": i,
            "ganzhi": gz,
            "ten_god": (ten_god(day_stem, s) if day_stem else "") or "",
        })
    return out


def dayun_liunian_interactions(chart_json: dict, dayun: list[dict] | None = None,
                               liunian: list[dict] | None = None) -> list[dict]:
    """大运×流年机械交互因子。"""
    pillars = chart_json.get("pillars") or {}
    day_stem = (pillars.get("day") or {}).get("stem") or ""
    if dayun is None:
        dayun = dayun_table(chart_json)
    if liunian is None:
        liunian = liunian_table(chart_json, n=12)

    he_set = {frozenset(p) for p in HE_PAIRS}
    chong_set = {frozenset(p) for p in CHONG_PAIRS}
    sanhe = {k: set(v) for k, v in SAN_HE_GROUPS.items()}

    out = []
    for d in dayun or []:
        d_gz = d.get("ganzhi") or ""
        if len(d_gz) < 2:
            continue
        d_stem, d_branch = d_gz[0], d_gz[1]
        for y in liunian or []:
            y_gz = y.get("ganzhi") or ""
            if len(y_gz) < 2:
                continue
            y_stem, y_branch = y_gz[0], y_gz[1]
            rels = []
            if d_gz == y_gz:
                rels.append({"kind": "sui_yun_bing_lin",
                             "text": f"岁运并临（大运{d_gz}=流年{y_gz}，干支相同；"
                                     "《渊海子平》有此结构之名——只标记，不批吉凶）"})
            tg = ten_god(d_stem, y_stem) if day_stem else None
            if tg:
                rels.append({"kind": "ten_god_stem",
                             "text": f"流年干{y_stem}对运干{d_stem}={tg}", "value": tg})
            pair = frozenset((d_branch, y_branch))
            if pair in he_set:
                rels.append({"kind": "liuhe",
                             "text": f"流年支{y_branch}与运支{d_branch}六合"})
            elif pair in chong_set:
                rels.append({"kind": "liuchong",
                             "text": f"流年支{y_branch}与运支{d_branch}六冲"})
            else:
                hits = sanxing_hits([d_branch, y_branch])
                if hits:
                    rels.append({"kind": "sanxing",
                                 "text": f"流年支{y_branch}与运支{d_branch}见{'/'.join(hits)}",
                                 "value": hits})
                for elem, bs in sanhe.items():
                    if d_branch in bs and y_branch in bs:
                        rels.append({"kind": "sanhe",
                                     "text": f"流年支{y_branch}与运支{d_branch}三合{elem}局",
                                     "value": elem})
                de, ye = BRANCH_ELEMENTS.get(d_branch), BRANCH_ELEMENTS.get(y_branch)
                if de and ye:
                    if de == ye:
                        rels.append({"kind": "bihe",
                                     "text": f"流年支{y_branch}与运支{d_branch}比和（{de}）"})
                    elif SHENG_CYCLE.get(ye) == de or SHENG_CYCLE.get(de) == ye:
                        rels.append({"kind": "sheng",
                                     "text": f"流年支{y_branch}与运支{d_branch}有相生"})
                    elif KE_CYCLE.get(ye) == de or KE_CYCLE.get(de) == ye:
                        rels.append({"kind": "ke",
                                     "text": f"流年支{y_branch}与运支{d_branch}有相克"})
            out.append({
                "year": y.get("year"),
                "liunian": y_gz,
                "dayun": d_gz,
                "dayun_index": d.get("index"),
                "start_age": d.get("start_age"),
                "relations": rels,
                "basis": "干支对照（core.relations / symbols）；只记关系，不批吉凶",
            })
    return out


def tai_yuan(month_ganzhi: str) -> dict | None:
    """胎元：月柱天干进一位、地支进三位（《三命通会》胎元起法）。"""
    if len(month_ganzhi) < 2:
        return None
    s, b = month_ganzhi[0], month_ganzhi[1]
    if s not in HEAVENLY_STEMS or b not in EARTHLY_BRANCHES:
        return None
    si = (HEAVENLY_STEMS.index(s) + 1) % 10
    bi = (EARTHLY_BRANCHES.index(b) + 3) % 12
    return {"ganzhi": HEAVENLY_STEMS[si] + EARTHLY_BRANCHES[bi],
            "basis": "月干进一位、月支进三位（《三命通会》胎元起法）"}


def liuyue_table(year_stem: str, day_stem: str = "", n: int = 12) -> list[dict]:
    """流月：正月（寅）起，五虎遁配干，顺行 n 月；十神取流月干对日主。"""
    if year_stem not in TIGER_MONTH_STEM:
        return []
    start = TIGER_MONTH_STEM[year_stem]
    out = []
    for i in range(int(n)):
        b = EARTHLY_BRANCHES[(2 + i) % 12]
        s = HEAVENLY_STEMS[(start + i) % 10]
        out.append({
            "month_index": i + 1,
            "branch": b,
            "ganzhi": s + b,
            "ten_god": (ten_god(day_stem, s) if day_stem else "") or "",
        })
    return out


def xiao_yun_table(chart_json: dict, n: int = 12) -> list[dict]:
    """小运：自生时干支起，顺逆同大运，一岁一位。"""
    pillars = chart_json.get("pillars") or {}
    year_stem = (pillars.get("year") or {}).get("stem") or ""
    day_stem = (pillars.get("day") or {}).get("stem") or ""
    hour_gz = (pillars.get("hour") or {}).get("ganzhi") or ""
    gender = (chart_json.get("birth") or {}).get("gender") or ""
    if len(hour_gz) < 2 or not year_stem:
        return []
    direction = dayun_direction(year_stem, gender) if gender else None
    if not direction:
        return []
    try:
        si = HEAVENLY_STEMS.index(hour_gz[0])
        bi = EARTHLY_BRANCHES.index(hour_gz[1])
    except ValueError:
        return []
    step = 1 if direction == "forward" else -1
    out = []
    for k in range(1, int(n) + 1):
        s = HEAVENLY_STEMS[(si + step * k) % 10]
        b = EARTHLY_BRANCHES[(bi + step * k) % 12]
        out.append({
            "age": k,
            "ganzhi": s + b,
            "ten_god": (ten_god(day_stem, s) if day_stem else "") or "",
            "verified": False,
        })
    return out
