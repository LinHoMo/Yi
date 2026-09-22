# -*- coding: utf-8 -*-
"""案例运行器：把古籍案例还原成真实干支时刻，喂给引擎与思维链。

只作数据装配，不打分——打分唯一入口是 `scripts/evaluate.py`。

为什么不再用"2024-06-01 + 甲X月"占位：
  案例通常只记"巳月戊戌日占求财"。旧管线把缺日期一律塞进 2024-06-01 10 时，
  并用 `"甲" + 月支` / `"甲" + 日支` 造干支串。旬空由日柱所在旬决定，
  而"甲X"几乎总不是真实日柱 → 旬空直接算错（例：丙辰日被写成甲辰日，
  旬空由子丑变成寅卯），应期日历日期也全落在假日期上。
  现在用内核反查满足该月令与该日柱的真实公历日期，四柱全部由历法算出。
"""
from __future__ import annotations

import json
import re
import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "scripts"), str(ROOT / "core")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core import ganzhi_calendar as gc  # noqa: E402

from liuyao_engine import build_hexagram_result  # noqa: E402
from thinking_chain import run_thinking_chain  # noqa: E402
from human_narrative import build_human_narrative, render_human_markdown  # noqa: E402

CASES = ROOT / "data" / "cases" / "classical_cases.json"
SPLITS = ROOT / "data" / "cases" / "case_splits.json"

_TRIGRAM_YAO = {
    "乾": [7, 7, 7], "坤": [8, 8, 8], "坎": [8, 7, 8], "离": [7, 8, 7],
    "震": [8, 8, 7], "巽": [7, 7, 8], "艮": [7, 8, 8], "兑": [8, 7, 7],
}

_HEX2TRIGRAM = {
    "乾": ("乾", "乾"), "坤": ("坤", "坤"), "屯": ("坎", "震"), "蒙": ("艮", "坎"),
    "需": ("坎", "乾"), "讼": ("乾", "坎"), "师": ("坤", "坎"), "比": ("坎", "坤"),
    "小畜": ("巽", "乾"), "履": ("乾", "兑"), "泰": ("坤", "乾"), "否": ("乾", "坤"),
    "同人": ("乾", "离"), "大有": ("离", "乾"), "谦": ("坤", "艮"), "豫": ("震", "坤"),
    "随": ("兑", "震"), "蛊": ("艮", "巽"), "临": ("坤", "兑"), "观": ("巽", "坤"),
    "噬嗑": ("离", "震"), "贲": ("艮", "离"), "剥": ("艮", "坤"), "复": ("坤", "震"),
    "无妄": ("乾", "震"), "大畜": ("艮", "乾"), "颐": ("艮", "震"), "大过": ("兑", "巽"),
    "坎": ("坎", "坎"), "离": ("离", "离"), "咸": ("兑", "艮"), "恒": ("震", "巽"),
    "遁": ("乾", "艮"), "大壮": ("震", "乾"), "晋": ("离", "坤"), "明夷": ("坤", "离"),
    "家人": ("巽", "离"), "睽": ("离", "兑"), "蹇": ("坎", "艮"), "解": ("震", "坎"),
    "损": ("艮", "兑"), "益": ("巽", "震"), "夬": ("兑", "乾"), "姤": ("乾", "巽"),
    "萃": ("兑", "坤"), "升": ("坤", "巽"), "困": ("兑", "坎"), "井": ("坎", "巽"),
    "革": ("兑", "离"), "鼎": ("离", "巽"), "震": ("震", "震"), "艮": ("艮", "艮"),
    "渐": ("巽", "艮"), "归妹": ("震", "兑"), "丰": ("震", "离"), "旅": ("离", "艮"),
    "巽": ("巽", "巽"), "兑": ("兑", "兑"), "涣": ("巽", "坎"), "节": ("坎", "兑"),
    "中孚": ("巽", "兑"), "小过": ("震", "艮"), "既济": ("坎", "离"), "未济": ("离", "坎"),
}

_STEMS, _BRANCHES = gc.HEAVENLY_STEMS, gc.EARTHLY_BRANCHES
_MONTH_RE = re.compile(r"([%s])月" % _BRANCHES)
_DAY_RE = re.compile(r"([%s])([%s])日" % (_STEMS, _BRANCHES))


def hex2yao(hx_name: str, changed_hx: str | None = None) -> list[int] | None:
    """本卦（可选变卦）→ 六爻值序列，自下而上。7 少阳 8 少阴 9 老阳 6 老阴。"""
    if hx_name not in _HEX2TRIGRAM:
        return None
    u, l = _HEX2TRIGRAM[hx_name]
    base = _TRIGRAM_YAO[l] + _TRIGRAM_YAO[u]
    if not changed_hx or changed_hx == hx_name:
        return base
    if changed_hx not in _HEX2TRIGRAM:
        return base
    cu, cl = _HEX2TRIGRAM[changed_hx]
    changed = _TRIGRAM_YAO[cl] + _TRIGRAM_YAO[cu]
    return [orig if orig == chg else (9 if orig == 7 else 6)
            for orig, chg in zip(base, changed)]


def parse_ganzhi_hint(text: str) -> tuple[str | None, str | None]:
    """从"巳月戊戌日" / "庚辰日" 提取 (月支, 日柱)。"""
    text = text or ""
    month_branch = None
    m = _MONTH_RE.search(text)
    if m:
        month_branch = m.group(1)
    day_ganzhi = None
    d = _DAY_RE.search(text)
    if d:
        day_ganzhi = d.group(1) + d.group(2)
    return month_branch, day_ganzhi


def resolve_case_time(case: dict) -> dict:
    """把案例的干支提示还原成真实公历时刻。

    返回 {dt, source, notes, hour_assumed}；source ∈ {ganzhi_resolved, stated_date_verified,
    stated_date_conflicts_ganzhi, unresolved}。
    """
    inp = case.get("input") or {}
    notes: list[str] = []
    month_branch, day_ganzhi = parse_ganzhi_hint(inp.get("date", "") or case.get("question", ""))

    stated = None
    if all(case.get(k) for k in ("year", "month", "day")):
        stated = datetime(case["year"], case["month"], case["day"], case.get("hour") or 12, 0)

    if day_ganzhi:
        around = stated or datetime(2024, 6, 1, 12, 0)
        hits = gc.find_solar_date(day_ganzhi, month_branch, around=around)
        if not hits and month_branch:
            notes.append(f"月令{month_branch}+日柱{day_ganzhi}无解，放宽月令约束")
            hits = gc.find_solar_date(day_ganzhi, None, around=around)
        if hits:
            dt = hits[0]["dt"]
            if stated:
                g_stated = gc.ganzhi_of(stated)
                if g_stated.day_ganzhi != day_ganzhi:
                    notes.append(f"案例自带公历 {stated.date()} 之日柱为 {g_stated.day_ganzhi}，"
                                 f"与原载 {day_ganzhi} 不合，以原载干支为准")
            hour = (stated.hour if stated and case.get("hour") else 12)
            return {"dt": dt.replace(hour=hour), "source": "ganzhi_resolved",
                    "notes": notes, "hour_assumed": not bool(case.get("hour")),
                    "alternatives": [h["date"] for h in hits[1:4]]}
        notes.append(f"无法由 {month_branch or '?'}月 {day_ganzhi} 还原日期")
        if stated:
            return {"dt": stated, "source": "unresolved_use_stated", "notes": notes,
                    "hour_assumed": not bool(case.get("hour")), "alternatives": []}
        raise ValueError(f"案例 {case.get('id')} 干支无法还原且无自带公历日期")

    if stated:  # 只有公历日期，没有干支提示
        return {"dt": stated, "source": "stated_date_verified", "notes": notes,
                "hour_assumed": not bool(case.get("hour")), "alternatives": []}
    raise ValueError(f"案例 {case.get('id')} 既无干支也无公历日期")


def load_cases() -> list[dict]:
    return json.loads(CASES.read_text(encoding="utf-8"))["cases"]


def load_ids(split: str | None = None, only: list[str] | None = None) -> list[str]:
    all_ids = [c["id"] for c in load_cases()]
    if only:
        return [i for i in only if i in all_ids]
    if split == "tune":
        if SPLITS.exists():
            ids = json.loads(SPLITS.read_text(encoding="utf-8")).get("tune") or []
            if ids:
                return [i for i in ids if i in all_ids]
        return [i for i in all_ids if i.startswith("ZS") and int(i[2:]) <= 20]
    if split == "holdout":
        if SPLITS.exists():
            return [i for i in json.loads(SPLITS.read_text(encoding="utf-8")).get("holdout", [])
                    if i in all_ids]
        return [i for i in all_ids if i.startswith("HO")]
    return all_ids


def run_case(case: dict) -> dict:
    """单例：还原时刻 → 排盘 → 五步思维链 → 抽取评分所需字段。"""
    cid = case["id"]
    q = case.get("question") or (case.get("input") or {}).get("question", "")
    inp = case.get("input") or {}
    hx = case.get("hexagram") or {}
    ho, hc = hx.get("original"), hx.get("changed")
    if not ho:
        raise ValueError("缺少卦名")
    yao = hex2yao(ho, hc)
    if yao is None:
        raise ValueError(f"无法解析卦象 {ho}->{hc}")

    resolved = resolve_case_time(case)
    dt = resolved["dt"]

    h = build_hexagram_result(yao, q, "manual", dt.year, dt.month, dt.day, dt.hour)
    tc = run_thinking_chain(h)
    thinking = tc.get("thinking_chain", tc)
    human = build_human_narrative(tc)
    tc["human_narrative"] = human

    s2 = thinking.get("step2_use_god_identification") or {}
    s3 = thinking.get("step3_strength_analysis") or {}
    s5 = thinking.get("step5_synthesis") or {}
    rc_lines = thinking.get("reasoning_chain", []) or []
    timing = s5.get("timing") or {}
    sel = s2.get("selected_use_god") or {}

    return {
        "id": cid,
        "question": q,
        "assembled_time": dt.strftime("%Y-%m-%d %H:%M"),
        "time_source": resolved["source"],
        "time_notes": resolved["notes"],
        "hour_assumed": resolved["hour_assumed"],
        "four_pillars": h["divination_time"],
        "hexagram": tc["original_hexagram"]["name"],
        "changed_hexagram": (tc.get("changed_hexagram") or {}).get("name", "?"),
        "use_god_category": s2.get("use_god_category", "?"),
        "use_god_branch": sel.get("earthly_branch", "?"),
        "use_god_element": s2.get("use_god_element", "?"),
        "use_god_position": sel.get("position", "?"),
        "strength_level": s3.get("strength_level", "?"),
        "final_score": s5.get("final_score", "?"),
        "verdict": s5.get("verdict", "?"),
        "special_pattern": (s5.get("special_pattern") or {}).get("pattern"),
        "yingqi": timing.get("summary_text", "?"),
        "yingqi_branches": timing.get("key_branches") or [],
        "yingqi_dates": timing.get("yingqi_dates") or timing.get("dates") or [],
        "reasoning_chain": rc_lines,
        "pattern_tags": [ln for ln in rc_lines
                         if isinstance(ln, str) and ("[格局]" in ln or "[格局要点]" in ln)],
        "empty_branches": h.get("empty_branches", []),
        "classical_quotes": h.get("classical_quotes", []),
        "human_narrative": human,
        "human_markdown": render_human_markdown(human),
    }


def run_ids(ids: list[str], verbose: bool = True) -> dict:
    """跑一批案例，返回可直接交给 evaluate.py 打分的结果结构。"""
    by_id = {c["id"]: c for c in load_cases()}
    results, errors = [], []
    for cid in ids:
        try:
            r = run_case(by_id[cid])
            results.append(r)
            if verbose:
                print(f"{cid}: {r['hexagram']}({r['assembled_time']}) "
                      f"use={r['use_god_category']}@{r['use_god_branch']} "
                      f"verdict={r['verdict']} 旬空={r['empty_branches']}")
        except Exception as exc:
            if verbose:
                print(f"{cid}: ERROR {exc}")
                print("\n".join(traceback.format_exc().strip().splitlines()[-5:]))
            errors.append({"id": cid, "error": str(exc)[:300]})
            results.append({"id": cid, "error": str(exc)[:200]})
    return {"split": "custom", "ids": ids, "total": len(ids),
            "cases": results, "errors": errors}
