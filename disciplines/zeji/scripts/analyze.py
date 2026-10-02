# -*- coding: utf-8 -*-
"""择吉·规则推演（analyze 段）—— 纯机械，断语只取 data/verdicts.json。

输入 chart 段输出的择日盘，输出结构化的因子与判据：
  1. 建除宜忌（该活动在建除十二神宜/忌表中的落点）
  2. 黄黑道吉凶（日值神属黄道 +1 / 黑道 -1，日辰第一权）
  3. 二十八宿吉凶（吉宿/凶宿 ±0.5）
  4. 综合裁决（verdict_rule：≥1 吉 / ≤-1 凶 / 其间平）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
DISC = Path(__file__).resolve().parents[1]
for _p in (str(CORE), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.symbols import CHONG_PAIRS  # noqa: E402

_WEIGHTS = {"建除": 20, "黄黑道": 20, "星宿": 20, "吉凶": 40}


def _load_verdicts() -> dict:
    p = DISC / "data" / "verdicts.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _load_citations() -> dict:
    p = DISC / "data" / "citations.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


VERDICTS = _load_verdicts()
CITATIONS = _load_citations()

# 日支冲肖（通书：冲即对冲地支之生肖）
_BRANCH_ZODIAC = {
    "子": "鼠", "丑": "牛", "寅": "虎", "卯": "兔", "辰": "龙", "巳": "蛇",
    "午": "马", "未": "羊", "申": "猴", "酉": "鸡", "戌": "狗", "亥": "猪",
}
# 地支六冲：**由 core 唯一真值源 CHONG_PAIRS 派生**（不在此另抄一份冲表）
_BRANCH_CLASH: dict[str, str] = {}
for _a, _b in CHONG_PAIRS:
    _BRANCH_CLASH[_a] = _b
    _BRANCH_CLASH[_b] = _a
# 煞方（申子辰日煞南，寅午戌日煞北，巳酉丑日煞东，亥卯未日煞西）
_SHA_FANG = {
    "申": "南", "子": "南", "辰": "南",
    "寅": "北", "午": "北", "戌": "北",
    "巳": "东", "酉": "东", "丑": "东",
    "亥": "西", "卯": "西", "未": "西",
}


def _shensha_chong_pengzu(chart_out: dict) -> tuple[dict, dict, dict]:
    """机械算天德/月德、冲煞、彭祖百忌。纯结构化，断语模板在 verdicts。"""
    gz = chart_out.get("ganzhi") or {}
    month_branch = gz.get("月建") or ""
    day_branch = gz.get("日支") or (gz.get("日柱") or "  ")[1:2]
    day_stem = (gz.get("日柱") or " ")[0]
    stars: list[str] = []
    try:
        from yishu_core.shensha import tian_de, yue_de
        if month_branch:
            stars.extend(tian_de(month_branch))
            yd = yue_de(month_branch)
            if yd:
                stars.append("月德")
    except Exception:
        pass

    chong_zhi = _BRANCH_CLASH.get(day_branch, "")
    chong_xiao = _BRANCH_ZODIAC.get(chong_zhi, "")
    sha_fang = _SHA_FANG.get(day_branch, "")
    chong = {
        "日支": day_branch,
        "冲支": chong_zhi,
        "冲肖": chong_xiao,
        "煞方": sha_fang,
        "phrase_chong": VERDICTS["chong_sha"]["chong_phrase"].format(zhi=chong_xiao) if chong_xiao else "",
        "phrase_sha": VERDICTS["chong_sha"]["sha_phrase"].format(fang=sha_fang) if sha_fang else "",
    }

    pz = VERDICTS.get("pengzu") or {}
    hits = []
    hits.extend((pz.get("by_stem") or {}).get(day_stem, []))
    hits.extend((pz.get("by_branch") or {}).get(day_branch, []))
    pengzu = {"日干": day_stem, "日支": day_branch, "hit": bool(hits), "items": hits}
    shensha = {"month_branch": month_branch, "stars": stars}
    return shensha, chong, pengzu


def _activity_label(activity: str) -> str:
    return VERDICTS["activity_names"].get(activity, "通用")


def _citations(activity: str, xiu_name: str = "") -> dict:
    """本例事类的参考书证（《玉匣記》逐字引文）+ 当日值宿歌诀——只透出，不参与评分。

    引文与判据**物理分栏**：`data/citations.json` 是书证，`data/verdicts.json`
    是判据唯一真值源；两者不互相覆盖（见 citations.json#_comment）。
    """
    acts = CITATIONS.get("activities") or {}
    return {
        "活动": activity,
        "通则": CITATIONS.get("common") or [],
        "本例": acts.get(activity) or [],
        "值宿歌诀": (CITATIONS.get("xiu_verses") or {}).get(xiu_name) or None,
        "缺口": CITATIONS.get("gap") or {},
        "来源": CITATIONS.get("source") or {},
    }


def _factors(chart_out: dict, activity: str) -> dict:
    """三个机械因子的计分与宜忌落点。返回 {jian_chu, huang, xiu} 明细。"""
    jc = chart_out.get("jian_chu")
    god = chart_out.get("day_god")
    xiu = chart_out.get("xiu") or {}

    jc_info = (VERDICTS["jian_chu"].get(jc) or {}) if jc else {}
    god_info = (VERDICTS["huang_hei_dao"].get(god) or {}) if god else {}

    jc_yi = activity in (jc_info.get("宜") or [])
    jc_ji = activity in (jc_info.get("忌") or [])
    god_yi = activity in (god_info.get("宜") or [])

    xiu_ji = xiu.get("name") in VERDICTS["xiu"]["吉宿"]
    xiu_xiong = xiu.get("name") in VERDICTS["xiu"]["凶宿"]

    shensha, chong, pengzu = _shensha_chong_pengzu(chart_out)

    return {
        "jian_chu": {
            "神": jc, "宜": jc_yi, "忌": jc_ji,
            "含义": jc_info.get("含义", ""),
        },
        "huang_dao": {
            "神": god, "黄道": chart_out.get("huang_dao"),
            "宜": god_yi, "含义": god_info.get("含义", ""),
        },
        "xiu": {
            "宿": xiu.get("name"), "全名": xiu.get("full"),
            "吉": xiu_ji, "凶": xiu_xiong,
        },
        "shensha": shensha,
        "chong_sha": chong,
        "pengzu": pengzu,
    }


def _verdict(f: dict) -> dict:
    """综合裁决（verdicts.json::verdict_rule）。神煞/彭祖作辅助，不压过黄黑道。"""
    score = 0.0
    score += 1.0 if f["huang_dao"]["黄道"] else -1.0
    score += 1.0 if f["jian_chu"]["宜"] else (-1.0 if f["jian_chu"]["忌"] else 0.0)
    score += 0.5 if f["xiu"]["吉"] else (-0.5 if f["xiu"]["凶"] else 0.0)
    # 天德/月德等神煞加分
    ss = f.get("shensha") or {}
    for star, w in (VERDICTS.get("shensha") or {}).get("tian_de_yue_de", {}).items():
        if star in (ss.get("stars") or []):
            score += float(w)
    # 彭祖百忌硬忌
    if (f.get("pengzu") or {}).get("hit"):
        score -= 0.5

    # 三档结论措辞唯一真值源在 verdicts.json#narrate_phrases（sum_good/sum_bad/sum_mixed）
    _tone = VERDICTS["narrate_phrases"]
    if score >= VERDICTS["verdict_rule"]["thresholds"]["吉"]:
        direction, tone = "吉", _tone["sum_good"]
    elif score <= VERDICTS["verdict_rule"]["thresholds"]["凶"]:
        direction, tone = "凶", _tone["sum_bad"]
    else:
        direction, tone = "平", _tone["sum_mixed"]
    return {"方向": direction, "说明": tone, "得分": round(score, 1),
            "所本": VERDICTS["verdict_rule"]["note"]}


def analyze(chart_out: dict) -> dict:
    """chart 段输出 → 因子与判据（结构化，无成段断语）。"""
    activity = _activity_label(chart_out.get("activity") or "通用")
    f = _factors(chart_out, activity)
    v = _verdict(f)

    hour = chart_out.get("hour")
    hour_note = None
    if hour:
        hg = hour.get("god")
        h_info = (VERDICTS["huang_hei_dao"].get(hg) or {}) if hg else {}
        hour_note = {
            "时支": hour.get("branch"), "值神": hg,
            "黄道": bool(h_info.get("huang")),
            "含义": h_info.get("含义", ""),
        }

    yi, ji = _yi_ji(f, activity)
    # 布尔命中（评分维度）：活动在建除宜表或值神宜表 → 宜命中；
    # 在建除忌表 → 忌命中（黑道凶由 huang_dao 维度单独计）
    yi_hit = bool(f["jian_chu"]["宜"] or f["huang_dao"]["宜"])
    ji_hit = bool(f["jian_chu"]["忌"])
    return {
        "schema": "zeji-analyze-v2",
        "activity": activity,
        "question": chart_out.get("question", ""),
        "yi_hit": yi_hit,
        "ji_hit": ji_hit,
        "chart_summary": {
            "日期": chart_out.get("date"),
            "星期": chart_out.get("weekday"),
            "农历": (chart_out.get("lunar") or {}).get("month_name"),
            "干支": chart_out.get("ganzhi"),
            "建除": chart_out.get("jian_chu"),
            "日值神": chart_out.get("day_god"),
            "黄道": chart_out.get("huang_dao"),
            "值宿": (chart_out.get("xiu") or {}).get("full"),
        },
        "factors_detail": f,
        "hour": hour_note,
        "yi": yi,
        "ji": ji,
        "citations": _citations(activity, (chart_out.get("xiu") or {}).get("name") or ""),
        "conclusion": v,
        "factors": [
            {"因子": "建除", "权重": _WEIGHTS["建除"], "判据": f"{f['jian_chu']['神']}"
             f"（{_yi_ji_phrase(f['jian_chu']['宜'], f['jian_chu']['忌'])}）",
             "所本": VERDICTS["narrate_phrases"]["basis_jianchu"]},
            {"因子": "黄黑道", "权重": _WEIGHTS["黄黑道"], "判据": f"{f['huang_dao']['神']}"
             f"（{'黄道' if f['huang_dao']['黄道'] else '黑道'}）",
             "所本": VERDICTS["narrate_phrases"]["basis_huanghei"]},
            {"因子": "星宿", "权重": _WEIGHTS["星宿"], "判据": f"{f['xiu']['全名']}"
             f"（{'吉宿' if f['xiu']['吉'] else ('凶宿' if f['xiu']['凶'] else '—')}）",
             "所本": VERDICTS["narrate_phrases"]["basis_xiu"]},
            {"因子": "天月德神煞", "权重": "辅助", "判据": "、".join((f.get("shensha") or {}).get("stars") or []) or "无",
             "所本": VERDICTS["shensha"]["note"]},
            {"因子": "冲煞", "权重": "趋避", "判据": (f.get("chong_sha") or {}).get("phrase_chong", "")
             + " " + (f.get("chong_sha") or {}).get("phrase_sha", ""),
             "所本": VERDICTS["chong_sha"]["note"]},
            {"因子": "彭祖百忌", "权重": "辅助", "判据": "；".join((f.get("pengzu") or {}).get("items") or []) or "不犯",
             "所本": VERDICTS["pengzu"]["note"]},
            {"因子": "吉凶", "权重": _WEIGHTS["吉凶"], "判据": f"{v['方向']}（{v['得分']}）",
             "所本": VERDICTS["verdict_rule"]["note"]},
        ],
    }


def _yi_ji(f: dict, activity: str) -> tuple[list[str], list[str]]:
    """活动在该日各因子的宜/忌要点（只有宜/忌命中的因子才列）。"""
    yi, ji = [], []
    if f["jian_chu"]["宜"]:
        yi.append(f"建除{f['jian_chu']['神']}日宜{activity}")
    if f["jian_chu"]["忌"]:
        ji.append(f"建除{f['jian_chu']['神']}日忌{activity}")
    if f["huang_dao"]["黄道"] and f["huang_dao"]["宜"]:
        yi.append(f"{f['huang_dao']['神']}（黄道）宜{activity}")
    if f["huang_dao"]["黄道"] and not f["huang_dao"]["宜"]:
        yi.append(f"{f['huang_dao']['神']}（黄道）为吉")
    if not f["huang_dao"]["黄道"]:
        ji.append(f"{f['huang_dao']['神']}（黑道）凶，忌{activity}")
    if f["xiu"]["吉"]:
        yi.append(f"{f['xiu']['全名']}值日（吉宿）")
    if f["xiu"]["凶"]:
        ji.append(f"{f['xiu']['全名']}值日（凶宿）")
    ss = f.get("shensha") or {}
    for star in (ss.get("stars") or []):
        yi.append(f"天月德：{star}照临")
    ch = f.get("chong_sha") or {}
    if ch.get("phrase_chong"):
        ji.append(ch["phrase_chong"])
    if ch.get("phrase_sha"):
        ji.append(ch["phrase_sha"])
    pz = f.get("pengzu") or {}
    for item in (pz.get("items") or []):
        ji.append(f"彭祖百忌：{item}")
    return yi, ji


def _yi_ji_phrase(yi: bool, ji: bool) -> str:
    if yi:
        return "宜"
    if ji:
        return "忌"
    return "无关"


if __name__ == "__main__":
    import argparse
    import json as _json
    from datetime import date as _date

    ap = argparse.ArgumentParser(description="择吉分析（analyze 段）")
    ap.add_argument("chart_json", nargs="?", help="chart 段输出 JSON 文件（缺省跑金标准自检）")
    ap.add_argument("-o", "--out", type=Path, help="写出 analyze JSON")
    args = ap.parse_args()

    if not args.chart_json:
        # 金标准自检：2026-09-25（执/青龙黄道/牛）嫁娶 → 执忌+青龙宜+凶宿 → 平
        from chart import chart_from_date
        a = analyze(chart_from_date(_date(2026, 9, 25)))
        assert a["chart_summary"]["建除"] == "执", a["chart_summary"]
        assert a["chart_summary"]["日值神"] == "青龙", a["chart_summary"]
        assert a["conclusion"]["方向"] == "平", a["conclusion"]
        # 2026-09-24（定/勾陈黑道）嫁娶 → 定宜+黑道 → 平偏凶
        a2 = analyze(chart_from_date(_date(2026, 9, 24)))
        assert a2["chart_summary"]["日值神"] == "勾陈" and not a2["chart_summary"]["黄道"], a2
        print("择吉 analyze 校验通过（执/青龙/牛·嫁娶 → 平）")
        raise SystemExit(0)

    chart_out = _json.loads(Path(args.chart_json).read_text(encoding="utf-8"))
    a = analyze(chart_out)
    text = _json.dumps(a, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        print("分析 →", args.out)
    else:
        print(text)
