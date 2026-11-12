# -*- coding: utf-8 -*-
"""应期**排序口径**离线试验（575 批，只读；不改引擎、不动读数、不改冻结指标）。

起因（574 批实测）：《易冒》系 16 案带单点应期书证的占例上，引擎 `yingqi_branches` 顶-1
只命中 **1／16**，而书载应期支落在**候选集合内 9／16**——即引擎**推得出**、**排不准**。
本器离线试若干排序口径，看哪一种与原书一致度最高，**只出试验结论，不接引擎**：
    A 引擎现状（首支）｜B 引擎序末支｜C 候选中日期最晚｜D 候选中日期最早
    E1 值日族优先｜E2 逢冲族优先｜E3 出空／填实族优先｜F 规则族优先级 × 日期远近的组合

口径纪律：n=16<30，**只报逐例计数，不出率值**；`in_candidate_pool`（候选集是否含书载支）
只是**归因线索**，不是指标。接线与否须另获授权并按 §六.3 声明新旧不可比。

    python dev_tools/yingqi_order_probe.py
    python dev_tools/yingqi_order_probe.py --selftest
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
for _sub in ("scripts", "core", ""):
    sys.path.insert(0, str(DISC / _sub) if _sub else str(DISC))

import open_bushi_yingqi_candidates as O_  # noqa: E402

POOL = O_.POOL

# 规则族（按引擎给出的 rule 字段归类）
VALUE_DAY = ("逢值", "用神值日", "发动值日", "化出之支值日", "原神值日", "日辰值事",
             "独发之爻值日", "飞神值日", "出旬之日", "填实(实空)")
CHONG = ("逢冲", "用神安静，逢冲之日", "冲空", "用神入墓，冲墓之日", "用神被辰合住，冲开之日",
         "用神被未合住，冲开之日", "用神被寅克，制杀之日（冲去寅）", "飞神冲开")
KONG = ("空亡之支出空填实", "空亡之支与用神同五行，出空填实", "化出之支逢空，出空值日", "出旬之日（本旬十日已尽，次日起用神不为空）")


def _family(rule: str) -> str:
    if any(k in rule for k in VALUE_DAY):
        return "值日"
    if any(k in rule for k in CHONG):
        return "逢冲"
    if any(k in rule for k in KONG):
        return "出空"
    if "三合成局" in rule:
        return "三合"
    if "速应" in rule:
        return "速应"
    return "其他"


def _dates_of(r: dict) -> list[dict]:
    ds = r.get("yingqi_dates") or {}
    lst = ds.get("dates") if isinstance(ds, dict) else ds
    return list(lst or [])


def _as_date(text: str) -> date | None:
    try:
        return date.fromisoformat(str(text)[:10])
    except Exception:
        return None


def strategies(r: dict) -> dict[str, str | None]:
    """各排序口径下的 top-1 应期支（None＝该口径给不出）。"""
    branches = [str(x).replace("日", "") for x in (r.get("yingqi_branches") or [])]
    dates = _dates_of(r)
    out: dict[str, str | None] = {}
    out["A 引擎现状"] = branches[0] if branches else None
    out["B 引擎序末"] = branches[-1] if branches else None
    dated = [(d, _as_date(d.get("date", ""))) for d in dates]
    dated = [(d, dt) for d, dt in dated if dt]
    out["C 日期最晚"] = max(dated, key=lambda x: x[1])[0].get("branch") if dated else None
    out["D 日期最早"] = min(dated, key=lambda x: x[1])[0].get("branch") if dated else None
    for fam, label in (("值日", "E1 值日族优先"), ("逢冲", "E2 逢冲族优先"), ("出空", "E3 出空族优先")):
        same = [x for x in dated if _family(x[0].get("rule", "")) == fam]
        out[label] = (max(same, key=lambda x: x[1])[0].get("branch") if same else None)
    # F 组合：族优先级（值日 > 逢冲 > 出空 > 三合 > 其他），同族取最晚
    rank = {"值日": 0, "逢冲": 1, "出空": 2, "三合": 3, "速应": 4, "其他": 5}
    if dated:
        best = sorted(dated, key=lambda x: (rank.get(_family(x[0].get("rule", "")), 9), -x[1].toordinal()))[0]
        out["F 族优先+最晚"] = best[0].get("branch")
    else:
        out["F 族优先+最晚"] = None
    return out


def run() -> dict:
    pool = json.loads(POOL.read_text(encoding="utf-8"))
    rows = []
    for c in pool.get("cases") or []:
        built = O_.build_case(c)
        if built is None:
            continue
        r = O_.engine()["C"].run_case(built, full=False)
        st = strategies(r)
        book = c.get("book_yingqi_branch")
        branches = [str(x).replace("日", "") for x in (r.get("yingqi_branches") or [])]
        months = [str(x).replace("月", "") for x in (r.get("yingqi_months") or [])]
        years = [str(x).replace("年", "") for x in (r.get("yingqi_years") or [])]
        rows.append({
            "id": c.get("id"), "book": book,
            "in_pool": book in branches,
            "in_month": book in months,
            "in_year": book in years,
            "hits": {k: (v == book) for k, v in st.items()},
            "picks": st,
        })
    return {"rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser(description="应期排序口径离线试验（只读）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        checks = [
            ("族判定：逢值→值日", _family("逢值") == "值日"),
            ("族判定：三合成局→三合", _family("三合成局") == "三合"),
            ("族判定：用神安静，逢冲之日→逢冲", _family("用神安静，逢冲之日") == "逢冲"),
            ("日期解析容错", _as_date("坏值") is None and _as_date("2024-02-21") is not None),
        ]
        for name, ok in checks:
            print(f"  {'√' if ok else '×'} {name}")
        bad = [n for n, ok in checks if not ok]
        if bad:
            print(f"selftest 失败 {len(bad)} 项：{'; '.join(bad)}")
            return 1
        print(f"selftest：{len(checks)} 类检查全过（真盘零写入）")
        return 0

    out = run()
    rows = out["rows"]
    names = list(rows[0]["hits"]) if rows else []
    print(f"样本 {len(rows)} 案（外部集逐例计数，n<30 不出率值）")
    print(f"  日应期候选含书载应期支（归因线索，非指标）：{sum(1 for r in rows if r['in_pool'])}／{len(rows)}")
    print(f"  仅月应期层覆盖：{sum(1 for r in rows if (not r['in_pool']) and r['in_month'])}｜"
          f"仅年应期层覆盖：{sum(1 for r in rows if (not r['in_pool']) and (not r['in_month']) and r['in_year'])}｜"
          f"三层皆无：{sum(1 for r in rows if not (r['in_pool'] or r['in_month'] or r['in_year']))}")
    for name in names:
        hit = sum(1 for r in rows if r["hits"][name])
        print(f"  {name:<14} 命中 {hit}／{len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
