# -*- coding: utf-8 -*-
"""《穷通宝鉴》四柱命例评测集构建器（一次性数据构建，产物入库、脚本留档可复跑）。

源：data/sources/qiong-tong-bao-jian.wikitext.txt 的 70 个 wikitable 命例表，
每行形制：|时日月年（表头）/ |四干 / |四支 / |断语（可有可无）。

expected 只含**书上明写的四柱**（客观标的）；「状元/词林/按察」等富贵断语
**不入 expected**（TECH-DEBT 规则：富贵层次不计分），逐字保留在 note 供回指。
公历时刻由内核历法**反查**：穷举 1900–2100 逐日，找四柱与书面全同的真实时刻
（确定性重建，不是猜；命例四柱在该窗口无解者如实跳过并计数）。
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
CORE = DISC.parents[1] / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.ganzhi_calendar import EARTHLY_BRANCHES, HEAVENLY_STEMS, ganzhi_of  # noqa: E402

SRC = DISC.parents[1] / "data" / "sources" / "qiong-tong-bao-jian.wikitext.txt"
CASES = DISC / "data" / "cases" / "ming_classical_cases.json"

STEMS = set(HEAVENLY_STEMS)
BRANCHES = set(EARTHLY_BRANCHES)
REPR_HOUR = {"子": 0, "丑": 1, "寅": 3, "卯": 5, "辰": 7, "巳": 9,
             "午": 11, "未": 13, "申": 15, "酉": 17, "戌": 19, "亥": 21}


def parse_tables() -> list[dict]:
    text = SRC.read_text(encoding="utf-8")
    rows: list[dict] = []
    section = ""
    in_table = False
    cells: list[str] = []
    tab_line = 0
    for i, raw in enumerate(text.splitlines()):
        s = raw.strip()
        if s.startswith("'''") and s.endswith("'''"):
            section = s.strip("'")
            continue
        if s.startswith("{|"):
            in_table = True
            cells = []
            tab_line = i + 1
            continue
        if in_table and s.startswith("|}"):
            in_table = False
            rows.append({"section": section, "line_no": tab_line, "cells": cells})
            continue
        if in_table and s:
            cells.append(s[1:] if s.startswith("|") else s)

    parsed = []
    for tab in rows:
        cells = [c[1:] if c.startswith("|") else c for c in tab["cells"]]
        r = 0
        while r < len(cells):
            if cells[r] == "时日月年":
                stems_line = cells[r + 1] if r + 1 < len(cells) else ""
                branch_line = cells[r + 2] if r + 2 < len(cells) else ""
                duan = cells[r + 3] if r + 3 < len(cells) and \
                    cells[r + 3] != "时日月年" else ""
                if len(stems_line) == 4 and len(branch_line) == 4 and \
                    all(ch in STEMS for ch in stems_line) and \
                        all(ch in BRANCHES for ch in branch_line):
                    pillars = {
                        "hour": stems_line[0] + branch_line[0],
                        "day": stems_line[1] + branch_line[1],
                        "month": stems_line[2] + branch_line[2],
                        "year": stems_line[3] + branch_line[3],
                    }
                    parsed.append({"section": tab["section"],
                                   "line_no": tab["line_no"],
                                   "pillars": pillars, "duan": duan,
                                   "quote": f"时日月年 {stems_line} {branch_line}"
                                            + (f" {duan}" if duan else "")})
                    r += 3 + (1 if duan else 0)
                    continue
            r += 1
    return parsed


def build_datetime_index(pillars_set: set[tuple]) -> dict[tuple, str]:
    """穷举 1900–2100 逐日（午时），按 年/月/日 三柱过滤；命中日再定时辰。"""
    found: dict[tuple, str] = {}
    day = datetime(1900, 2, 20, 12, 0)
    end = datetime(2100, 12, 31, 12, 0)
    while day <= end:
        m = ganzhi_of(day, boundary="day")
        triple = (m.year_ganzhi, m.month_ganzhi, m.day_ganzhi)
        matched = [t for t in pillars_set if t[:3] == triple]
        for t in matched:
            hb = t[3][1]
            dt_hit = day.replace(hour=REPR_HOUR[hb], minute=30)
            m2 = ganzhi_of(dt_hit, boundary="day")
            if (m2.year_ganzhi, m2.month_ganzhi, m2.day_ganzhi, m2.hour_ganzhi) == t:
                found[t] = dt_hit.strftime("%Y-%m-%d %H:%M")
        day += timedelta(days=1)
    return found


def main() -> int:
    rows = parse_tables()
    print(f"表内命例行: {len(rows)}")

    pending = []
    for r in rows:
        p4 = r["pillars"]
        pending.append(((p4, r["duan"], r["section"], r["quote"], r["line_no"]),
                        (p4["year"], p4["month"], p4["day"], p4["hour"])))
    dt_map = build_datetime_index({tuple(t[1]) for t in pending})

    store = json.loads(CASES.read_text(encoding="utf-8"))
    cases = store.get("cases", [])
    existing = {c["id"] for c in cases}
    added = skipped = 0
    for (p4, duan, section, quote, line_no), _key in pending:
        cid = f"MP{len(cases) + 1 + added:03d}"
        if cid in existing:
            continue
        dt = dt_map.get((p4["year"], p4["month"], p4["day"], p4["hour"]))
        if not dt:
            skipped += 1
            continue
        cases.append({
            "id": cid,
            "split": "holdout",
            "book": "穷通宝鉴",
            "location": f"{section}（表 L{line_no}）",
            "source_quote": quote,
            "pillars": {"datetime": dt},
            "gender": "男",
            "note": f"书源命例四柱 {p4['year']}/{p4['month']}/{p4['day']}/{p4['hour']}"
                    + (f"；书断语「{duan}」（富贵层次，按规则不计分）" if duan else ""),
            "expected": {"pillars": dict(p4)},
        })
        added += 1

    store["cases"] = cases
    store["splits"] = {
        "tune": [c["id"] for c in cases if c.get("split") == "tune"],
        "holdout": [c["id"] for c in cases if c.get("split") == "holdout"],
    }
    store["_comment"] = [c for c in store["_comment"] if "调候批" not in c] + [
        "",
        "2026-09-30n 命例批（《穷通宝鉴》四柱命例表 70 表）：expected 只有书上明写的",
        "四柱（客观标的）；「状元/词林/按察」等富贵断语逐字保留于 note 但**不计分**。",
        "公历时刻由内核历法反查（四柱全同的真实时刻，确定性重建）。",
        "本批度量 = 四柱对表（历法链路与明清古籍记录的吻合度），表对表回归性质，",
        "不是对齐分泛化证据。构建器：dev_tools/build_mingli_cases.py。",
    ]
    CASES.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"新增 {added} 例（反查无解跳过 {skipped}）→ holdout 合计 "
          f"{len(store['splits']['holdout'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
