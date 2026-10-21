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
from yishu_core.symbols import xunkong_of

# 缺生日样本的流年窗锚定纪元（260 批，口径常量；改动须按 §四.4 登记新旧不可比）
LIUNIAN_REF_YEAR = 2026


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
        # 260 批：缺生日的窗锚从「now().year」改钉登记常量 LIUNIAN_REF_YEAR——
        # 旧回退让 pillars 形样本的流年窗随公历年滑动（移动时钟实验：golden 9/40
        # 样本随钟漂移）。常量纪元使审计确定；改该值＝口径变更须登记（§四.4）。
        # 今天恰为 2026，故本改动在活钟下 digest 一字不变（golden 实跑验证）。
        birth_year = LIUNIAN_REF_YEAR

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


GONG_POS = {"year": "年", "month": "月", "day": "日", "hour": "时"}

# 《神峰通考》源L917 逐字清单：「拱禄有五日…此五日五时而拱禄格…此五日五时为拱贵格」
# 日柱→时柱：拱禄 癸亥/癸丑·癸丑/癸亥·丁巳/丁未·己未/己巳·戊辰/戊午；
# 拱贵 甲申/甲戌·甲寅/甲子·戊申/戊午·乙未/乙酉·辛丑/辛卯。
# 同书源L1848 却在清单之外用「庚戌 戊子 壬辰 壬寅…行辛卯运填实卒」——书内两处不一致，
# 故本仓不擅自扩清单，只给标签加 in_roster 分档（通则外推者一律标 false，不称已验）。
GONG_ROSTER = {("癸亥", "癸丑"), ("癸丑", "癸亥"), ("丁巳", "丁未"), ("己未", "己巳"),
               ("戊辰", "戊午"), ("甲申", "甲戌"), ("甲寅", "甲子"), ("戊申", "戊午"),
               ("乙未", "乙酉"), ("辛丑", "辛卯")}


def _gong_zhi(day_branch: str, hour_branch: str) -> str:
    """日时两支隔一位 ⇒ 虚拱中间那支（《神峰通考》拱贵拱禄 源L1848）。"""
    if not day_branch or not hour_branch:
        return ""
    i, j = EARTHLY_BRANCHES.index(day_branch), EARTHLY_BRANCHES.index(hour_branch)
    for lo, hi in ((i, j), (j, i)):
        if (hi - lo) % 12 == 2:
            return EARTHLY_BRANCHES[(lo + 1) % 12]
    return ""


def dayun_ming_yindong(chart_json: dict, dayun: list[dict] | None = None) -> list[dict]:
    """大运对**本命四柱**的引动结构标签（只标结构名与书据，不批吉凶，不覆写本命结论）。

    五条判据逐条取自《渊海子平》《神峰通考》的逐字书例（行运书例见证集，由八字科门禁 [18]
    回验；该集只作见证，解读路径不读取它），不是自造机制：
      ①补第三支——命局已具某三合局两支、运支补第三支 ⇒ 会局（源L1856「行丁丑，是巳酉丑会金局」）
      ②半合——命局只具一支、运支补成该局两支 ⇒ 半合（源L2531「直运至辛亥，亥卯合局印授扶身」）
      ③引出已具之局——命局三合本自齐全，运干五行即该局五行 ⇒ 引动（源L387「纔交乙巳运，为己之七杀，
        引出亥卯未木局」：乙＝木＝局神）
      ④冲——运支六冲命局某支，逐位指名（源L1848「入庚子运…又是午月，冲破甲子」）
      ⑤填实——日时同干、支隔一位而虚拱中间支，命柱不占该支，运支到 ⇒ 填实（源L1848「行辛卯运填实卒」）
      ⑥入墓——三合生旺墓序之墓支再临岁运，且命局确有该五行之神 ⇒ 其神入墓（《千里命稿》源L1955
        「正官格，行墓运，即是官星入墓」；土无墓库位、诸家异说，一律不标）
    判据本体在 `yindong_relations`（六条机制唯一实现），大运与流年共用。
    """
    if dayun is None:
        dayun = dayun_table(chart_json)

    ctx = _yindong_ctx(chart_json)
    if not ctx["ming"]:
        return []
    out = []
    for d in dayun or []:
        rels = yindong_relations(ctx, d.get("ganzhi") or "", "大运")
        if rels:
            out.append({"dayun": d.get("ganzhi"), "dayun_index": d.get("index"),
                        "start_age": d.get("start_age"), "relations": rels,
                        "basis": "运支运干与本命四柱的结构对照；只记结构，不批吉凶（SKILL.md 铁律三）"})
    return out


def liunian_ming_yindong(chart_json: dict, liunian: list[dict] | None = None) -> list[dict]:
    """流年对**本命四柱**的引动——与 `dayun_ming_yindong` 共用 `yindong_relations`（判据单一真值源）。

    书据（岁支会局的两条逐字例，此前「岁支引动未接」即指此）：
      《神峰通考》源L2528「再行卯运，及岁支财神会局，受职州判，大发财利」
      《渊海子平》源L388「行己巳运金生之地，见庚子年；庚金为七杀，又见子水，死于非命」
    """
    if liunian is None:
        liunian = liunian_table(chart_json, n=12)
    ctx = _yindong_ctx(chart_json)
    if not ctx["ming"]:
        return []
    out = []
    for y in liunian or []:
        rels = yindong_relations(ctx, y.get("ganzhi") or "", "流年")
        if rels:
            out.append({"liunian": y.get("ganzhi"), "year": y.get("year"), "age": y.get("age"),
                        "relations": rels,
                        "basis": "流年干支与本命四柱的结构对照；只记结构，不批吉凶（SKILL.md 铁律三）"})
    return out


def _yindong_ctx(chart_json: dict) -> dict:
    """命局侧预计算（三合局/中神/六冲/虚拱所依），供运、岁两个枚举器共用同一套前件。"""
    pillars = chart_json.get("pillars") or {}
    ming: list[tuple[str, str]] = []      # (位置名, 支)
    for key in ("year", "month", "day", "hour"):
        b = (pillars.get(key) or {}).get("branch") or ""
        if b in EARTHLY_BRANCHES:
            ming.append((GONG_POS[key], b))
    mset = {b for _, b in ming}
    d_stem = (pillars.get("day") or {}).get("stem") or ""
    h_stem = (pillars.get("hour") or {}).get("stem") or ""
    d_branch = (pillars.get("day") or {}).get("branch") or ""
    h_branch = (pillars.get("hour") or {}).get("branch") or ""
    gong = _gong_zhi(d_branch, h_branch) if (d_stem and d_stem == h_stem) else ""
    if gong and gong in mset:
        gong = ""                          # 书：四柱不可占了贵禄之宫，则填实不容物
    day_gz = (pillars.get("day") or {}).get("ganzhi") or ""
    hour_gz = (pillars.get("hour") or {}).get("ganzhi") or ""
    kong = xunkong_of(day_gz) if len(day_gz) == 2 else []
    # 书内两处不一致，如实并存而不代书择一：
    #   源L922 逐字「既为拱亡，则拱不信贵人，所以不取此日时为拱贵也」（落空 ⇒ 格废）
    #   源L1848 却仍用王郎中（甲寅日甲子时，甲寅旬空子丑 ⇒ 所拱之丑正落空）断「辛丑除通判、
    #   庚子运…乃天中杀，即空亡，夹贵不住」（落空 ⇒ 格仍起用，至岁运方败）
    # ⇒ 本仓不清空 gong、不擅自取一侧，改为另发 `gong_ge_luo_kong` 标签，把分歧摆到读数面上。
    gong_luo_kong = bool(gong) and gong in kong
    return {"ming": ming, "mset": mset,
            "sanhe": {k: set(v) for k, v in SAN_HE_GROUPS.items()},
            "wang": {k: v[1] for k, v in SAN_HE_GROUPS.items()},   # 中神＝生旺墓序第二位
            "chong_set": {frozenset(p) for p in CHONG_PAIRS},
            "mu": {k: v[2] for k, v in SAN_HE_GROUPS.items()},   # 生旺墓序第三位＝该五行之墓支
            "elems": [STEM_ELEMENTS.get((chart_json.get("pillars") or {}).get(k or {}).get("stem") or "")
                      for k in ("year", "month", "day", "hour")]
                     + [BRANCH_ELEMENTS.get((chart_json.get("pillars") or {}).get(k or {}).get("branch") or "")
                        for k in ("year", "month", "day", "hour")],
            "gong": gong, "gong_luo_kong": gong_luo_kong,
            "gong_in_roster": (day_gz, hour_gz) in GONG_ROSTER,
            "d_branch": d_branch, "h_branch": h_branch,
            "day_stem": d_stem, "day_gz": day_gz, "hour_gz": hour_gz, "kong": kong}


def _elem_rel(day_stem: str, elem: str) -> str:
    """局五行对日主的五类关系（书的命名法：「岁支**财**神会局」「乃**杀**重」）。"""
    de = STEM_ELEMENTS.get(day_stem) or ""
    if not de or not elem:
        return ""
    if de == elem:
        return "比劫"
    if KE_CYCLE.get(de) == elem:
        return "财"
    if KE_CYCLE.get(elem) == de:
        return "官杀"
    if SHENG_CYCLE.get(de) == elem:
        return "食伤"
    if SHENG_CYCLE.get(elem) == de:
        return "印"
    return ""


def yindong_relations(ctx: dict, gz: str, prefix: str = "大运") -> list[dict]:
    """一条外来干支（大运或流年）对命局的引动判据——**六条机制的唯一实现处**。"""
    if len(gz) < 2:
        return []
    ys, yb = gz[0], gz[1]
    mset, ming, day_stem = ctx["mset"], ctx["ming"], ctx["day_stem"]
    rels = []
    for elem, trio in ctx["sanhe"].items():
        have = mset & trio
        if yb == ctx["mu"][elem] and elem in ctx["elems"]:
            rel = _elem_rel(day_stem, elem)
            rels.append({"kind": "xing_ru_mu", "value": elem, "shishen_rel": rel,
                         "text": f"{prefix}{gz}支{yb}为{elem}之墓，命局之{elem}"
                                 + (f"（{rel}星）随以入墓" if rel else "入墓"),
                         "basis": "三合生旺墓序之墓支再临于岁运 ⇒ 其神入墓（《千里命稿》源L1955 逐字"
                                  "「正官格，行墓运，即是官星入墓」；《三命通会》源L253 逐字"
                                  "「然火命逢之则为入墓」定火墓在戌；"
                                  "《神峰通考》源L1868 逐字「后大运行己丑，流年丙寅四月破家…庚入墓也」）"})
        if yb in have:
            continue                     # 外来支已具于命局 ⇒ 非「运/岁来引动」（墓支例外，见上）
        rel = _elem_rel(day_stem, elem)
        tag = f"（{elem}对日主为{rel}）" if rel else ""
        if yb in trio:
            if len(have) == 2:
                rels.append({"kind": "bu_san_he_di_san_zhi", "value": elem, "shishen_rel": rel,
                             "text": f"{prefix}{gz}支{yb}补命局{''.join(sorted(have))}成{elem}三合局{tag}",
                             "basis": f"命局已具{elem}局两支＋外来支补第三支（《神峰通考》源L1856 逐字"
                                      f"「行丁丑，是巳酉丑会金局，乃杀重」同型）"})
            elif len(have) == 1 and ctx["wang"][elem] in (have | {yb}):
                rels.append({"kind": "san_he_ban_he", "value": elem, "shishen_rel": rel,
                             "text": f"{prefix}{gz}支{yb}与命局{next(iter(have))}成{elem}局半合{tag}",
                             "basis": f"命局仅具{elem}局一支、外来支补一支且须含中神{ctx['wang'][elem]}"
                                      f"（《神峰通考》源L2531 逐字「直运至辛亥，亥卯合局印授扶身」"
                                      f"／源L2528 逐字「及岁支财神会局」同型；三支未齐，故只标半合）"})
        elif have == trio and STEM_ELEMENTS.get(ys) == elem:
            rels.append({"kind": "gan_yin_chu_yi_ju", "value": elem,
                         "shishen_rel": ten_god(day_stem, ys) or "",
                         "text": f"{prefix}{gz}干{ys}（{elem}，对日主为{ten_god(day_stem, ys) or '未取'}）"
                                 f"引出命局本具之{elem}三合局",
                         "basis": "命局三合已具，外来干即局神 ⇒ 引出（《渊海子平》源L387 逐字"
                                  "「纔交乙巳运，为己之七杀，引出亥卯未木局」）"})
    for pos, b in ming:
        if frozenset((yb, b)) in ctx["chong_set"]:
            rels.append({"kind": "zhi_chong_ming", "value": f"{pos}支{b}",
                         "text": f"{prefix}{gz}支{yb}冲命局{pos}支{b}"
                                 + ("（冲提纲）" if pos == "月" else ""),
                         "basis": "外来支六冲命局之支（《神峰通考》源L1848 逐字"
                                  "「入庚子运，庚金克甲木，又是午月，冲破甲子」同型）"})
    if ctx["gong"] and yb == ctx["gong"]:
        in_roster = ctx["gong_in_roster"]
        rels.append({"kind": "zhi_tian_shi", "value": ctx["gong"], "in_roster": in_roster,
                     "text": f"{prefix}{gz}支{yb}填实命局日时{ctx['d_branch']}{ctx['h_branch']}虚拱之{ctx['gong']}"
                             + ("（在源L917 十日清单内）" if in_roster else "（不在十日清单，按通则外推）"),
                     "basis": "日时同干、支隔一位而虚拱中间支，命柱不占其宫、不落空亡；外来支到即填实"
                              "（《神峰通考》源L1848 逐字「行辛卯运填实卒」；"
                              "「四柱不可占了贵禄之宫，则填实不容物」；"
                              "「亦忌禄贵落空」＋源L922 逐字「既为拱亡，则拱不信贵人」）"})
    # 拱格受伤：书给的是两条明文判据——
    #   源L917 逐字「忌刑冲了日时拱位，又怕四柱中有伤日干七杀，皆拱不信禄贵」
    #   源L836 逐字「不要填实虚位，怕冲月时，或冲日干七杀」
    # ⇒ ①外来支冲**日支或时支**（拱位所在）；②外来干**克日干**（＝日干之七杀）。仅在虚拱成立时判。
    if ctx["gong"]:
        hurt = []
        for pos, b in (("日", ctx["d_branch"]), ("时", ctx["h_branch"])):
            if b and frozenset((yb, b)) in ctx["chong_set"]:
                hurt.append(f"支{yb}刑冲{pos}支{b}（拱位）")
        if day_stem and ys and KE_CYCLE.get(STEM_ELEMENTS.get(ys)) == STEM_ELEMENTS.get(day_stem):
            hurt.append(f"干{ys}克日干{day_stem}（＝日干之七杀，书「伤日干七杀」）")
        if ctx["gong_luo_kong"] and (hurt or yb == ctx["gong"]):
            rels.append({"kind": "gong_ge_luo_kong", "value": ctx["gong"],
                         "text": f"命局日时{ctx['day_gz']}{ctx['hour_gz']}(旬){'、'.join(ctx['kong'])}"
                                 f"所拱之{ctx['gong']}落空亡，拱格破（无格可伤）",
                         "basis": "日柱旬空含所拱之支 ⇒ 禄贵落空、拱格破。《三命通会》源L1816 逐字「伤了日时拱不住贵气大忌塡实空亡」；"
                                  "同段又逐字「完则能盛破则无用所以怕见空亡歳运同」；《三命通会》源L3331 逐字「得拱大贵忌空亡填实」；"
                                  "《神峰通考》源L922 逐字「既为拱亡，则拱不信贵人」。"
                                  "异说如实保留（不抹平）：同书源L1848 王郎中一造（甲寅旬空子丑、所拱之丑正落空）"
                                  "仍按拱格断命 ⇒ 书内两说并存，本仓从**三处同证明文**裁为破拱；"
                                  "落空时不发「伤拱格」（无格可伤），填实仍作结构标签保留（书以填实、空亡并列大忌）"})
        if hurt and not ctx["gong_luo_kong"]:
            rels.append({"kind": "gong_ge_shou_shang", "value": "、".join(hurt),
                         "text": f"{prefix}{gz}伤拱格：" + "；".join(hurt),
                         "basis": "拱格本成而言，外来支冲日/时拱位或外来干克日干（＝日干之七杀）⇒ 伤拱。《神峰通考》源L917 逐字「忌刑冲了日时拱位，又怕四柱中有伤日干七杀，"
                                  "皆拱不信禄贵」；源L836 逐字「不要填实虚位，怕冲月时，或冲日干七杀」；"
                                  "《三命通会》源L1902 逐字「大忌塡实库位及刑冲破害空亡」"})
    return rels


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
