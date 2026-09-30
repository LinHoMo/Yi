# -*- coding: utf-8 -*-
"""大六壬·九宗门取三传（纯机械判据树，无解读成分）。

判据源：data/sources/liu-ren-da-quan.wikitext.txt 卷一「入手法」九法逐条
（贼克/比用/涉害/遥克/昴星/别责/八专/伏吟/返吟），诀文逐字留在学科层
data/verdicts.json，本模块只留算法。全部推断的入口，按 NEW-DISCIPLINES §2.1
要求**必须首先 100% 正确**——歧义读数以 `verified=False` 显式登记，不得静默
（清单见 dev_tools/check.py 的断言与 docs/NEW-DISCIPLINES.md §2.1）。

接口：san_chuan_full(day_stem, day_branch, tianpan) -> dict
  tianpan = {地盘位: 天盘神}（月将加时所得，12 位全）。
  返回 {men, ke_name, san_chuan, trigger, verified, day_kind}。
"""
from __future__ import annotations

from yishu_core.ganzhi_calendar import EARTHLY_BRANCHES as _BR
from yishu_core.symbols import (
    BRANCH_ELEMENTS,
    CHONG_PAIRS,
    KE_CYCLE,
    SELF_PUNISHMENTS,
    STEM_ELEMENTS,
    THREE_PUNISHMENTS_CYCLIC,
    THREE_PUNISHMENTS_MUTUAL,
)
from yishu_core.liuren_tables import JI_GONG, STEM_HE

YANG_STEMS = set("甲丙戊庚壬")
_MENG = {"寅", "申", "巳", "亥"}
_ZHONG = {"子", "午", "卯", "酉"}

PUNISH_OF: dict[str, str] = {}
for _cycle in THREE_PUNISHMENTS_CYCLIC.values():
    for _i, _b in enumerate(_cycle):
        PUNISH_OF[_b] = _cycle[(_i + 1) % 3]          # 寅→巳→申→寅 递刑
for _a, _b in THREE_PUNISHMENTS_MUTUAL.values():
    PUNISH_OF[_a] = _b
    PUNISH_OF[_b] = _a
for _s in SELF_PUNISHMENTS:
    PUNISH_OF[_s] = _s
CHONG_OF: dict[str, str] = {}
for _a, _b in CHONG_PAIRS:
    CHONG_OF[_a] = _b
    CHONG_OF[_b] = _a


def _elem(x: str) -> str:
    return STEM_ELEMENTS.get(x) or BRANCH_ELEMENTS.get(x) or ""


def _ke(a: str, b: str) -> bool:
    """a 克 b（五行单推，KE_CYCLE 唯一真值源）。"""
    ea, eb = _elem(a), _elem(b)
    return bool(ea and eb) and KE_CYCLE[ea] == eb


def four_courses(day_stem: str, day_branch: str, tianpan: dict[str, str]) -> list[dict]:
    """四课：一二课自日干（寄宫）起，三四课自日支起。下=所临地盘，上=天盘神。"""
    jigong = JI_GONG[day_stem]
    c1 = {"pos": 1, "xia": jigong, "shang": tianpan[jigong], "xia_label": "日干寄宫"}
    c2 = {"pos": 2, "xia": c1["shang"], "shang": tianpan[c1["shang"]], "xia_label": "课上神"}
    c3 = {"pos": 3, "xia": day_branch, "shang": tianpan[day_branch], "xia_label": "日支"}
    c4 = {"pos": 4, "xia": c3["shang"], "shang": tianpan[c3["shang"]], "xia_label": "支上神"}
    return [c1, c2, c3, c4]


def _ze_ke_courses(courses: list[dict]) -> tuple[list[dict], list[dict]]:
    """(下贼上诸课, 上克下诸课)。诀：取课先从下贼呼，如无下贼上克初。"""
    ze = [c for c in courses if _ke(c["xia"], c["shang"])]
    ke = [c for c in courses if _ke(c["shang"], c["xia"])]
    return ze, ke


def _bi_filter(candidates: list[dict], day_stem: str) -> list[dict]:
    """常将天日比神用，阳日用阳阴用阴（按候选上神的支阴阳）。"""
    want_yang = day_stem in YANG_STEMS
    return [c for c in candidates
            if (c["shang"] in ("子", "寅", "辰", "午", "申", "戌")) == want_yang]


def _she_hai_deep(c: dict) -> int:
    """涉害数：上神自所临地盘位涉归本家（含起讫），沿途上克下/下贼上各计一害。

    「旅行者」口径：以该课上神逐位与地盘论克。路径端点取舍诸书不一，
    故整个涉害门 verified=False（守门断言只验门类触发与结构不变量）。
    """
    start = c["xia"]
    shang = c["shang"]
    i0 = _BR.index(start)
    i1 = _BR.index(shang)                    # 本家 = 上神自身的地盘位
    steps = (i1 - i0) % 12
    harm = 0
    for k in range(steps + 1):
        pos = _BR[(i0 + k) % 12]
        if _ke(shang, pos) or _ke(pos, shang):
            harm += 1
    return harm


def _meng_zhong_ji(branch: str) -> int:
    """孟深仲浅季当休：孟 0 / 仲 1 / 季 2。"""
    return 0 if branch in _MENG else (1 if branch in _ZHONG else 2)


def _ke_tree(day_stem: str, day_branch: str, tianpan: dict[str, str],
             outer: str | None = None) -> dict | None:
    """贼克→比用→涉害 判据树；无克返回 None。

    宗门名随最终分支：独一克=贼克、取比=比用、涉害=涉害；
    `outer`（"伏吟"/"返吟"）覆写宗门名、方法名降为课体前缀。
    返回统一带 day_kind（chart 层直接透出）。
    """
    day_yang = day_stem in YANG_STEMS

    def label(method: str) -> tuple[str, str]:
        if outer:
            return outer, f"{outer}·{method}"
        return {"重审": ("贼克", "重审"), "元首": ("贼克", "元首"),
                "知一": ("比用", "知一"), "察微": ("涉害", "察微")}[method]

    courses = four_courses(day_stem, day_branch, tianpan)
    ze, ke = _ze_ke_courses(courses)
    pool = ze or ke
    if not pool:
        return None
    kind = "下贼" if ze else "上克"
    if len(pool) == 1:
        c = pool[0]
        men, ke_name = label("重审" if ze else "元首")
        return {"men": men, "ke_name": ke_name, "day_kind": "刚" if day_yang else "柔",
                "san_chuan": [c["shang"], tianpan[c["shang"]],
                              tianpan[tianpan[c["shang"]]]],
                "trigger": f"{kind}独一（{c['pos']}课 {c['xia']}→{c['shang']}）",
                "verified": True}
    bi = _bi_filter(pool, day_stem)
    if len(bi) == 1:
        c = bi[0]
        men, ke_name = label("知一")
        return {"men": men, "ke_name": ke_name, "day_kind": "刚" if day_yang else "柔",
                "san_chuan": [c["shang"], tianpan[c["shang"]],
                              tianpan[tianpan[c["shang"]]]],
                "trigger": f"{kind}多课取比（{c['pos']}课）", "verified": True}
    # 俱比/俱不比，或比后仍多 → 涉害（比者非空且未滤尽时只在比者中涉）
    cands = bi if 0 < len(bi) < len(pool) else pool
    deeps = [(_she_hai_deep(c), _meng_zhong_ji(c["shang"]), c) for c in cands]
    max_deep = max(d for d, _, _ in deeps)
    tied = [c for d, _, c in deeps if d == max_deep]
    if len(tied) > 1:
        best = min(_meng_zhong_ji(c["shang"]) for c in tied)
        tied = [c for c in tied if _meng_zhong_ji(c["shang"]) == best]
    if len(tied) > 1:
        pick = tianpan[JI_GONG[day_stem]] if day_yang else tianpan[day_branch]
        final = [c for c in tied if c["shang"] == pick]
        c = (final or tied)[0]
        men, ke_name = label("察微")
        return {"men": men, "ke_name": ke_name, "day_kind": "刚" if day_yang else "柔",
                "san_chuan": [c["shang"], tianpan[c["shang"]],
                              tianpan[tianpan[c["shang"]]]],
                "trigger": "涉害复等，柔辰刚日宜", "verified": False}
    c = tied[0]
    men, ke_name = label("察微")
    return {"men": men, "ke_name": ke_name, "day_kind": "刚" if day_yang else "柔",
            "san_chuan": [c["shang"], tianpan[c["shang"]],
                          tianpan[tianpan[c["shang"]]]],
            "trigger": f"涉害深浅定（{c['pos']}课 {c['xia']}→{c['shang']}）",
            "verified": False}


def _yao_ke(day_stem: str, courses: list[dict], tianpan: dict[str, str]) -> dict | None:
    """遥克：先神遥克日（蒿矢），后日遥克神（弹射）；多者取比。"""
    for direction, label in (("shen_ke_ri", "蒿矢"), ("ri_ke_shen", "弹射")):
        if direction == "shen_ke_ri":
            cands = [c for c in courses if _ke(c["shang"], day_stem)]
        else:
            cands = [c for c in courses if _ke(day_stem, c["shang"])]
        if not cands:
            continue
        if len(cands) > 1:
            bi = _bi_filter(cands, day_stem)
            if bi:
                cands = bi
        c = cands[0]
        return {"men": "遥克", "ke_name": label,
                "san_chuan": [c["shang"], tianpan[c["shang"]],
                              tianpan[tianpan[c["shang"]]]],
                "trigger": f"{label}（{c['pos']}课 {c['shang']}）", "verified": False}
    return None


# 柔日别责「支前三合」：三合局顺行前一（亥卯未→未前是卯；巳酉丑→丑前是酉…）
_SANHE_PREV = {"亥": "卯", "卯": "未", "未": "亥",
               "寅": "午", "午": "戌", "戌": "寅",
               "巳": "酉", "酉": "丑", "丑": "巳",
               "申": "子", "子": "辰", "辰": "申"}


def san_chuan_of(day_stem: str, day_branch: str, tianpan: dict[str, str]) -> dict:
    """九宗门（不含伏吟/返吟特法——天盘重合/皆冲走 san_chuan_full）。"""
    courses = four_courses(day_stem, day_branch, tianpan)
    jigong = JI_GONG[day_stem]
    gan_shang = tianpan[jigong]
    zhi_shang = tianpan[day_branch]
    day_yang = day_stem in YANG_STEMS

    def out(men, ke_name, chuan, trigger, verified=True):
        return {"men": men, "ke_name": ke_name, "san_chuan": chuan,
                "trigger": trigger, "verified": verified,
                "day_kind": "刚" if day_yang else "柔"}

    res = _ke_tree(day_stem, day_branch, tianpan)
    if res:
        return {**out(res["men"], res["ke_name"], res["san_chuan"], res["trigger"],
                      res["verified"])}

    # 两课结构 ⟺ 干支同位（寄宫==日支：甲寅/丁未/己未/庚申/癸丑五日恒如此）
    two_course = jigong == day_branch
    seen = {(c["xia"], c["shang"]) for c in courses}
    three_course = len(seen) == 3

    # 两课无克号八专（论克不论遥，故先于遥克）
    if two_course:
        if day_yang:
            first = tianpan[_BR[(_BR.index(jigong) + 2) % 12]]
            trigger = "阳日日阳顺行三连本位数"
        else:
            first = tianpan[_BR[(_BR.index(day_branch) - 2) % 12]]
            trigger = "阴日辰阴逆三位"
        return out("八专", "八专", [first, gan_shang, gan_shang],
                   trigger + "；中末总向日上眠", verified=False)

    yaoke = _yao_ke(day_stem, courses, tianpan)

    # 四课不全三课备，无遥无克别责例
    if three_course and yaoke is None:
        if day_yang:
            he_gan = STEM_HE[day_stem]
            first = tianpan[JI_GONG[he_gan]]
            trigger = f"刚日干合上头神（{day_stem}合{he_gan}，寄{JI_GONG[he_gan]}）"
        else:
            first = tianpan[_SANHE_PREV[day_branch]]
            trigger = f"柔日支前三合取（{day_branch}前{_SANHE_PREV[day_branch]}）"
        return out("别责", "别责", [first, gan_shang, gan_shang],
                   trigger + "；中末皆干上", verified=False)
    if yaoke:
        return {**out(yaoke["men"], yaoke["ke_name"], yaoke["san_chuan"],
                      yaoke["trigger"], yaoke["verified"])}

    # 无遥无克昴星穷
    if day_yang:
        chuan = [tianpan["酉"], zhi_shang, gan_shang]     # 阳仰：酉上神；先辰后日
        trigger = "阳仰（酉上神）先辰后日"
        name = "虎视"
    else:
        down_pos = next(p for p, sky in tianpan.items() if sky == "酉")
        chuan = [down_pos, gan_shang, zhi_shang]          # 阴俯：天盘酉所临位；先日后辰
        trigger = "阴俯（天盘酉所临位）先日后辰"
        name = "冬蛇掩目"
    return out("昴星", name, chuan, trigger, verified=False)


def classify_tianpan(day_stem: str, day_branch: str, tianpan: dict[str, str]) -> str | None:
    """天盘重合（伏吟）/天地皆冲（返吟）判据；不重合返回 None。"""
    identity = all(sky == ground for ground, sky in tianpan.items())
    chong = all(CHONG_OF.get(sky) == ground for ground, sky in tianpan.items())
    if identity:
        return "伏吟"
    if chong:
        return "返吟"
    return None


def san_chuan_full(day_stem: str, day_branch: str, tianpan: dict[str, str]) -> dict:
    """chart.py 的入口：先判伏吟/返吟特法，再落九宗门通用树。"""
    kind = classify_tianpan(day_stem, day_branch, tianpan)
    courses = four_courses(day_stem, day_branch, tianpan)
    ze, ke = _ze_ke_courses(courses)
    has_ke = bool(ze or ke)
    jigong = JI_GONG[day_stem]
    gan_shang, zhi_shang = tianpan[jigong], tianpan[day_branch]

    if kind == "伏吟" and has_ke:
        res = _ke_tree(day_stem, day_branch, tianpan, outer="伏吟")
        res["trigger"] = "伏吟有克还为用——" + res["trigger"]
        return res

    if kind == "返吟" and has_ke:
        res = _ke_tree(day_stem, day_branch, tianpan, outer="返吟")
        res["trigger"] = "返吟有克亦为用——" + res["trigger"]
        return res

    if kind == "伏吟":
        day_yang = day_stem in YANG_STEMS
        first = gan_shang if day_yang else zhi_shang      # 无克刚干柔取辰
        zhong = PUNISH_OF[first]
        if first in SELF_PUNISHMENTS:
            zhong = zhi_shang if day_yang else gan_shang  # 自刑：次传颠倒日辰并
        mo = CHONG_OF[zhong] if zhong in SELF_PUNISHMENTS else PUNISH_OF[zhong]
        return {"men": "伏吟", "ke_name": "伏吟(无克)", "san_chuan": [first, zhong, mo],
                "trigger": "无克刚干柔取辰，迤逦刑之作中末", "verified": True,
                "day_kind": "刚" if day_yang else "柔"}

    if kind == "返吟":
        day_gz = day_stem + day_branch
        yaoke = _yao_ke(day_stem, courses, tianpan)
        if yaoke:
            # 无克但有遥（如乙丑日木克土上神）→ 退遥克门；诀「六日该无克」
            # 反证其余无克返吟日皆有遥可取
            yaoke["trigger"] = "返吟无克有遥——" + yaoke["trigger"]
            return yaoke
        if day_gz in {"丁丑", "己丑", "辛丑", "丁未", "己未", "辛未"}:
            first = "亥" if day_branch == "丑" else "巳"  # 丑日登明未太乙
            return {"men": "返吟", "ke_name": "井栏射",
                    "san_chuan": [first, zhi_shang, gan_shang],
                    "trigger": "无克别有井栏名：辰上作中，日上作末",
                    "verified": False, "day_kind": "柔"}
        raise ValueError(f"返吟无克无遥不应发生于 {day_gz}（守门断言，见 dev_tools/check.py）")

    return san_chuan_of(day_stem, day_branch, tianpan)
