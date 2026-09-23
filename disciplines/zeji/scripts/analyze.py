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

_WEIGHTS = {"建除": 20, "黄黑道": 20, "星宿": 20, "吉凶": 40}


def _load_verdicts() -> dict:
    p = DISC / "data" / "verdicts.json"
    return json.loads(p.read_text(encoding="utf-8"))


VERDICTS = _load_verdicts()


def _activity_label(activity: str) -> str:
    return VERDICTS["activity_names"].get(activity, "通用")


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
    }


def _verdict(f: dict) -> dict:
    """综合裁决（verdicts.json::verdict_rule）。"""
    score = 0.0
    score += 1.0 if f["huang_dao"]["黄道"] else -1.0
    score += 1.0 if f["jian_chu"]["宜"] else (-1.0 if f["jian_chu"]["忌"] else 0.0)
    score += 0.5 if f["xiu"]["吉"] else (-0.5 if f["xiu"]["凶"] else 0.0)

    if score >= VERDICTS["verdict_rule"]["thresholds"]["吉"]:
        direction, tone = "吉", "黄道相合、建除无碍，事类与日辰相宜"
    elif score <= VERDICTS["verdict_rule"]["thresholds"]["凶"]:
        direction, tone = "凶", "黑道当值或建除有忌，结构上偏不利"
    else:
        direction, tone = "平", "有宜有忌，可行但需保留（宜择黄道吉时）"
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
        "schema": "zeji-analyze-v1",
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
        "conclusion": v,
        "factors": [
            {"因子": "建除", "权重": _WEIGHTS["建除"], "判据": f"{f['jian_chu']['神']}"
             f"（{_yi_ji_phrase(f['jian_chu']['宜'], f['jian_chu']['忌'])}）",
             "所本": "《协纪辨方书》建除篇通行口径"},
            {"因子": "黄黑道", "权重": _WEIGHTS["黄黑道"], "判据": f"{f['huang_dao']['神']}"
             f"（{'黄道' if f['huang_dao']['黄道'] else '黑道'}）",
             "所本": "《协纪辨方书·卷五·黄黑道》"},
            {"因子": "星宿", "权重": _WEIGHTS["星宿"], "判据": f"{f['xiu']['全名']}"
             f"（{'吉宿' if f['xiu']['吉'] else ('凶宿' if f['xiu']['凶'] else '—')}）",
             "所本": "《二十八宿吉凶歌》通行通书口径"},
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
