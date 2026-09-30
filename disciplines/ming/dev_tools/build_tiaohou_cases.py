# -*- coding: utf-8 -*-
"""调候评测案例集构建器（一次性数据构建，产物入库、脚本留档可复跑）。

读 data/tiaohou_quotes.json（build_tiaohou.py 的产物，逐格带原文引文），
为每个"原文有明文"的格生成一例：

  - input 的公历 datetime 由内核历法**反查**出真实时刻（月支=目标月令、日干=目标日主，
    其余柱任其自然）——与六爻 case_runner 同一"反查真实日期"范式，不造假干支；
  - expected 只填 tiaohou（书上明写的主/佐神）；四柱等其他维度**不填**（= N/A），
    严守「只评书上明写的量」；
  - source_quote 逐字保留，铁律三口径：expected 必须能指回原文。

切分：tune = 三春+三夏（寅卯辰巳午未），holdout = 三秋+三冬（申酉戌亥子丑）。
两半都出自同一部书的不同章节，无引擎输出参与切分，不存在"考卷调参"。
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.ganzhi_calendar import ganzhi_of  # noqa: E402

QUOTES = DISC / "data" / "tiaohou_quotes.json"
CASES = DISC / "data" / "cases" / "ming_classical_cases.json"

MB = {1: "寅", 2: "卯", 3: "辰", 4: "巳", 5: "午", 6: "未",
      7: "申", 8: "酉", 9: "戌", 10: "亥", 11: "子", 12: "丑"}
HOLDOUT_MONTHS = {"申", "酉", "戌", "亥", "子", "丑"}


def find_datetimes() -> dict[tuple[str, str], str]:
    """扫 1984–2003 年逐日，反查 (月支, 日干) → 首个真实公历时刻。"""
    found: dict[tuple[str, str], str] = {}
    day = datetime(1984, 1, 1, 10, 0)
    end = datetime(2003, 12, 31, 10, 0)
    while day <= end:
        m = ganzhi_of(day)
        key = (m.month_branch, m.day_ganzhi[0])
        if key not in found:
            found[key] = day.strftime("%Y-%m-%d %H:%M")
        day += timedelta(days=1)
    return found


def main() -> int:
    quotes = json.loads(QUOTES.read_text(encoding="utf-8"))
    dt_map = find_datetimes()

    store = json.loads(CASES.read_text(encoding="utf-8"))
    existing_ids = {c["id"] for c in store.get("cases", [])}

    cells = sorted(
        (v for v in quotes.values() if v["main"]),
        key=lambda v: (v["month"], "甲乙丙丁戊己庚辛壬癸".index(v["stem"])),
    )
    cases = list(store.get("cases", []))
    next_seq = len(cases) + 1
    added = 0
    for v in cells:
        cid = f"MT{next_seq:03d}"
        if cid in existing_ids:
            next_seq += 1
            continue
        dt = dt_map.get((MB[v["month"]], v["stem"]))
        if not dt:
            raise SystemExit(f"历法反查失败：{v['month']}月{v['stem']}（不应发生，12×10 全可查）")
        expected = {"tiaohou": {"main": v["main"]}}
        if v["assist"]:
            expected["tiaohou"]["assist"] = v["assist"]
        cases.append({
            "id": cid,
            "split": "holdout" if MB[v["month"]] in HOLDOUT_MONTHS else "tune",
            "book": "穷通宝鉴",
            "location": f"{v['section']}",
            "source_quote": v["quote"],
            "pillars": {"datetime": dt},
            "gender": "男",
            "note": f"{v['month']}月{v['stem']}日主调候（原文明写：主{v['main']}"
                    f"{'/佐' + v['assist'] if v['assist'] else '，佐神原文未单列'}）",
            "expected": expected,
        })
        next_seq += 1
        added += 1

    store["cases"] = cases
    store["splits"] = {
        "tune": [c["id"] for c in cases if c.get("split") == "tune"],
        "holdout": [c["id"] for c in cases if c.get("split") == "holdout"],
    }
    store["_comment"] = [
        "命科古籍案例集。规范见 disciplines/ming/docs/EVAL-PLAN.md：",
        "1) expected 只填书上明写的量，未写的一律不出现（= N/A，从分母剔除）；",
        "2) 每例必须能指回 book + location 的原文（source_quote 逐字抄录）；",
        "3) 禁止用引擎输出反推 expected。",
        "",
        "2026-09-30f 调候批（《穷通宝鉴》）：每个「原文有明文」的月支×日主格一例，",
        "expected 只有 tiaohou；公历时刻由内核历法反查（月支/日干为定值，其余任其自然）。",
        "引擎查同一张内核表（ming_tables.TIAO_HOU，提取自同一原文）→ 本集是**表对表",
        "回归 + 历法链路验证**，不是泛化证据；口径披露与随机基线见 scripts/evaluate.py。",
        "构建器：dev_tools/build_tiaohou.py（提取）+ dev_tools/build_tiaohou_cases.py（建例）。",
    ]
    CASES.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")

    n_tune = len(store["splits"]["tune"])
    n_hold = len(store["splits"]["holdout"])
    print(f"新增 {added} 例（tune {n_tune} / holdout {n_hold}）→ {CASES.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
