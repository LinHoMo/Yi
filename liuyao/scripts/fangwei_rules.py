# -*- coding: utf-8 -*-
"""方位层（#23）：避乱／迁移取方与延医取方——纯规则，只出方位候选与依据，不作吉凶判词。

书据（逐字在库，行号见 `data/sources/`）：
  A 避乱／迁移取方 ——《增刪卜易》源L2532 逐字「所以生方为吉，子孙之方亦吉，又当以旺衰分别」；
    同段又逐字云「午火得令而生世，往南避之为吉」与「火乃鬼方，生我何碍」，
    并先举众论「众以子孙属水，金动生之，北方为吉」而后以旺衰否之。
    ⇒ 吉方候选＝**生世之方** ∪ **子孙之方**；取舍按**旺衰**（月令）；
      「鬼方若生我亦不妨」⇒ 不以六亲名否决，只以旺衰分别。
  B 延医取方 ——《增刪卜易》源L3412 逐字「卦中子孙爻旺者，延医于子孙之方」；
    同条又逐字云「且如午火子孙或旺或动，请南方之医」「且如应爻临申金，延医必在西南」
    「如卦中有一爻独发而生用神者又以此方而延医」，三档俱备。
    ⇒ 三档：子孙旺／动 → 子孙之方；子孙休囚空破 → 应爻之方；一爻独发生用神 → 该爻之方。

地支方位取十二支 conventional 八方（书自用「申金…西南」「午火…南方」「子水…北方」皆与之合）；
旺衰用传统「旺相休囚死」以月令为主（同我旺、我生相、生我休、克我囚、我克死）。
本模块不接 engine／报告面（门禁 `dev_tools/check_fangwei.py` 守规则本身），接线须按 §四 门槛逐步量。
"""
from __future__ import annotations

BRANCH_DIR = {"子": "北", "丑": "东北", "寅": "东北", "卯": "东", "辰": "东南", "巳": "东南",
              "午": "南", "未": "西南", "申": "西南", "酉": "西", "戌": "西北", "亥": "西北"}
BRANCH_ELEM = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
               "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
LEVEL_ORDER = ["旺", "相", "休", "囚", "死"]      # 越前越旺


def strength(month_branch: str, branch: str) -> str:
    """月令定旺衰：同我旺、我生相、生我休、克我囚、我克死。"""
    me = BRANCH_ELEM.get(month_branch or "", "")
    el = BRANCH_ELEM.get(branch or "", "")
    if not me or not el:
        return ""
    if el == me:
        return "旺"
    if SHENG.get(me) == el:
        return "相"
    if SHENG.get(el) == me:
        return "休"
    if KE.get(el) == me:
        return "囚"
    if KE.get(me) == el:
        return "死"
    return ""


def direction_of(branch: str) -> str:
    return BRANCH_DIR.get(branch or "", "")


def _row(why: str, y: dict, month_branch: str) -> dict:
    b = y.get("branch") or ""
    return {"why": why, "branch": b, "direction": direction_of(b),
            "strength": strength(month_branch, b), "six_relation": y.get("six_relation") or ""}


def bi_luan_fang(shi_branch: str, yao: list[dict], month_branch: str) -> dict:
    """A 避乱／迁移：候选＝生世之方 ∪ 子孙之方，按旺衰分别；同档并列，不代书择一。"""
    shi_e = BRANCH_ELEM.get(shi_branch or "", "")
    rows = []
    for y in yao:
        b = y.get("branch") or ""
        e = BRANCH_ELEM.get(b, "")
        if e and SHENG.get(e) == shi_e:
            rows.append(_row("生世之方", y, month_branch))
        if y.get("six_relation") == "子孙":
            rows.append(_row("子孙之方", y, month_branch))
    got = [r for r in rows if r["strength"]]
    best_lv = min((r["strength"] for r in got), key=LEVEL_ORDER.index) if got else ""
    best = [r for r in got if r["strength"] == best_lv]
    seen, uniq = set(), []
    for r in best:
        if r["direction"] not in seen:
            seen.add(r["direction"])
            uniq.append(r)
    return {"candidates": rows, "ji_fang": [r["direction"] for r in uniq],
            "tie": len(uniq) > 1, "level": best_lv,
            "basis": "《增刪卜易》源L2532 逐字「生方为吉，子孙之方亦吉，又当以旺衰分别」"}


def du_fa_sheng_yong(du_fa_branch: str, use_god_branch: str) -> bool:
    """延医第三档前件。《增刪卜易》源L3412 逐字「如卦中有一爻独发而生用神者又以此方而延医」。
    用神支由调用方取自 step2 的 `selected_use_god`（单一真值源），本函数只判五行生关系。"""
    de = BRANCH_ELEM.get(du_fa_branch or "", "")
    ue = BRANCH_ELEM.get(use_god_branch or "", "")
    return bool(de and ue) and SHENG.get(de) == ue


def yan_yi_fang(yao: list[dict], ying_branch: str, month_branch: str,
                du_fa_sheng_yong: list[dict] | None = None) -> dict:
    """B 延医三档：子孙旺／动 → 子孙方；子孙皆休囚空破 → 应爻方；独发生用神 → 该爻方。"""
    out = []
    for y in yao:
        if y.get("six_relation") != "子孙":
            continue
        lv = strength(month_branch, y.get("branch") or "")
        if lv in ("旺", "相") or y.get("moving"):
            out.append(dict(_row("子孙之方", y, month_branch), 档="子孙之方"))
    if not out and ying_branch:
        y = {"branch": ying_branch}
        out.append(dict(_row("应爻之方", y, month_branch), 档="应爻之方"))
    for y in du_fa_sheng_yong or []:
        out.append(dict(_row("独发之方", y, month_branch), 档="独发之方"))
    return {"fang": out,
            "basis": "《增刪卜易》源L3412 逐字「子孙爻旺者，延医于子孙之方…休囚空破者又看应爻旺否…一爻独发而生用神者又以此方而延医」"}
