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
from kernel_path import kernel_dir  # noqa: E402

import json
import re
import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "scripts"), str(kernel_dir(__file__))):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core import ganzhi_calendar as gc  # noqa: E402

from liuyao_engine import build_hexagram_result  # noqa: E402
from thinking_chain import run_thinking_chain  # noqa: E402
from human_narrative import build_human_narrative, render_human_markdown  # noqa: E402

CASES = ROOT / "data" / "cases" / "classical_cases.json"
SPLITS = ROOT / "data" / "cases" / "case_splits.json"

# 爻序与卦表全部来自内核（不再有本地副本）：
#   BAGUA_LINES 自下而上，HEXAGRAM_TRIGRAMS 给出上下卦 —— 于是"某卦化出某卦"
#   的动爻位次由两者爻线逐位比较得出，不再靠一张镜像表凑。
from yishu_core.symbols import BAGUA_LINES, HEXAGRAM_TRIGRAMS  # noqa: E402

_STEMS = "甲乙丙丁戊己庚辛壬癸"
_MONTH_RE = re.compile(r"([%s])月" % "子丑寅卯辰巳午未申酉戌亥")
_DAY_RE = re.compile(r"([%s])([%s])日" % (_STEMS, "子丑寅卯辰巳午未申酉戌亥"))


def hex_lines(name: str) -> list[int] | None:
    """别卦的六爻线（自下而上，1 阳 0 阴）。"""
    tri = HEXAGRAM_TRIGRAMS.get(name)
    if not tri:
        return None
    upper, lower = tri
    return BAGUA_LINES[lower] + BAGUA_LINES[upper]


def hex2yao(hx_name: str, changed_hx: str | None = None) -> list[int] | None:
    """本卦（可选变卦）→ 六爻值序列，自下而上。7 少阳 8 少阴 9 老阳 6 老阴。

    动爻位次 = 本卦与变卦逐位比较的差异位。P0 爻序修正前这里用一张上爻在前的
    镜像表，恒之鼎的上六动会被算成第四爻动。
    """
    base = hex_lines(hx_name)
    if base is None:
        return None
    moving: tuple[int, ...] = ()
    if changed_hx and changed_hx != hx_name:
        chg = hex_lines(changed_hx)
        if chg is None:
            return [7 if b else 8 for b in base]
        moving = tuple(i + 1 for i, (a, b) in enumerate(zip(base, chg)) if a != b)
        if not moving:
            return None          # 两卦名相同却声明有变，或卦表有误
    return [(9 if b else 6) if (i + 1) in moving else (7 if b else 8)
            for i, b in enumerate(base)]


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
    """主案例库 + 外部验证集（yingqi_cases.json 等）。

    外部集与 tune/holdout 分开登记在 case_splits.json，永不参与调参；
    评分时按 split 取子集，两集合分别出分（AGENTS.md §四.1）。
    """
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    seen = {c["id"] for c in cases}
    for extra in sorted((ROOT / "data" / "cases").glob("*_cases.json")):
        if extra.name == CASES.name:
            continue
        try:
            data = json.loads(extra.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for c in data.get("cases", []):
            if c.get("id") and c["id"] not in seen:
                seen.add(c["id"])
                cases.append(c)
    return cases


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
    if split == "yingqi_holdout":
        if SPLITS.exists():
            return [i for i in json.loads(SPLITS.read_text(encoding="utf-8")).get("yingqi_holdout", [])
                    if i in all_ids]
        return [i for i in all_ids if i.startswith("YQ")]
    if split == "wikisource_holdout":
        if SPLITS.exists():
            return [i for i in json.loads(SPLITS.read_text(encoding="utf-8")).get("wikisource_holdout", [])
                    if i in all_ids]
        return [i for i in all_ids if i.startswith("WS")]
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
