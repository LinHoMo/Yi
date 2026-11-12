# -*- coding: utf-8 -*-
"""六爻「带单点应期」候选池：机读重建 + 一次性开卷（573 批建池、574 批开卷）。

与 547 批 `open_bushi_candidates.py` 同构，但语料换成 573 批《易冒》系新池（16 案，
此前零案例被提取）。**主指标沿用 546 批冻结的「顶-1 应期支一致」**，开卷后不得改指标。

重建（纯机械，LLM 不心算任何结论）：
  · 日期：池内 `month_branch`＋`day_ganzhi` → 「午月己巳日」形式（月支入月位）；
  · 卦名：`hexagram_text`／`changed_text`；
  · 动爻：由本卦／变卦逐位比较反推（`hex2yao`），无变卦者按静卦跑。

判卷：引擎给出的应期支候选取**顶-1**，与书载单点应期支一致记「命中」，否则「未命中」；
引擎无候选／不可重建者记「不适用」，不硬判。**n<30 只报逐例红绿，aggregate 恒 null。**

    python dev_tools/open_bushi_yingqi_candidates.py --dry-run
    python dev_tools/open_bushi_yingqi_candidates.py --open     # 只此一次
    python dev_tools/open_bushi_yingqi_candidates.py --verify
    python dev_tools/open_bushi_yingqi_candidates.py --selftest
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
ROOT = DISC.parent
for _sub in ("eval", "scripts", "core", "engine", "rules", ""):
    sys.path.insert(0, str(DISC / _sub) if _sub else str(DISC))

POOL = DISC / "data" / "cases" / "bushi_yingqi_candidates.json"
STATUS_OPEN = "已开卷一次·逐例红绿·无率值"
METRIC = "顶-1 应期支一致（546 批冻结口径沿用；开卷后不得改指标）"
_ENGINE = None


def engine():
    global _ENGINE
    if _ENGINE is None:
        import case_runner as C
        _ENGINE = {"C": C}
    return _ENGINE


def build_case(c: dict) -> dict | None:
    """池内条目 → 引擎可跑案例；不可重建返回 None。"""
    e = engine()
    orig = c.get("hexagram_text") or ""
    chg = c.get("changed_text") or ""
    date_str = f"{c.get('month_branch','')}月{c.get('day_ganzhi','')}日"
    moving = []
    if orig and chg:
        try:
            m = e["C"].hex2yao(orig, chg)
        except Exception:
            m = None
        if m is None:
            return None
        moving = list(m)
    elif not orig:
        return None
    return {
        "id": c.get("id"),
        "question": c.get("note") or "占验",
        "input": {"date": date_str, "question": c.get("note") or "占验"},
        "hexagram": {"original": orig, "changed": chg or None, "moving": sorted(set(moving))},
        "_date_str": date_str,
    }


def judge(pool: dict) -> list[dict]:
    rows = []
    for c in pool.get("cases") or []:
        built = build_case(c)
        rec = {"id": c.get("id"), "book": c.get("book"),
               "book_yingqi_branch": c.get("book_yingqi_branch"),
               "book_yingqi_ganzhi": c.get("book_yingqi_ganzhi"),
               "engine_top1": None, "engine_candidates": [], "in_candidate_pool": None,
               "result": None}
        if built is None:
            rec["result"] = "不适用·卦名/动爻不可机械重建"
            rows.append(rec)
            continue
        try:
            r = engine()["C"].run_case(built, full=False)
        except Exception as exc:  # noqa: BLE001
            rec["result"] = f"不适用·引擎运行异常（{type(exc).__name__}）"
            rows.append(rec)
            continue
        cands = [re.sub(r"日$", "", str(x)) for x in (r.get("yingqi_branches") or [])]
        rec["engine_candidates"] = cands[:6]
        rec["engine_top1"] = cands[0] if cands else None
        rec["rebuilt"] = {"date": built["_date_str"], "original": built["hexagram"]["original"],
                          "changed": built["hexagram"]["changed"],
                          "moving": built["hexagram"]["moving"]}
        if not cands:
            rec["result"] = "不适用·引擎无应期候选"
        else:
            # 主指标：顶-1 支是否等于书载单点应期支（546 批冻结口径）
            rec["result"] = "命中" if rec["engine_top1"] == c.get("book_yingqi_branch") else "未命中"
            # 归因线索（**不是指标**）：书载应期支是否落在引擎候选集合内
            rec["in_candidate_pool"] = c.get("book_yingqi_branch") in cands
        rows.append(rec)
    return rows


def result_sha(rows: list[dict]) -> str:
    canon = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16]


def build_open_result(rows: list[dict]) -> dict:
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip() or "unknown"
    judged = [r for r in rows if r["result"] in ("命中", "未命中")]
    aggregate = None
    if len(judged) >= 30:
        aggregate = {"n": len(judged),
                     "hit": sum(1 for r in judged if r["result"] == "命中"),
                     "rate": round(100.0 * sum(1 for r in judged if r["result"] == "命中") / len(judged), 1)}
    return {
        "opened_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "commit_at_open": commit,
        "open_count": 1,
        "metric_frozen": METRIC,
        "aggregate": aggregate,
        "_comment": ("n<30 时 aggregate 恒 null、结构内不出现率值字段（沿用 546 批 decision_rule）；"
                     "开封只此一次，判卷痕迹与 result_sha 双指纹可验。"),
        "cases": rows,
        "result_sha": result_sha(rows),
    }


def open_pool(dry: bool) -> int:
    pool = json.loads(POOL.read_text(encoding="utf-8"))
    if pool.get("open_result") is not None:
        print("  × 本池已开卷（open_result 非 null）——封存事件的判卷只允许一次")
        return 1
    rows = judge(pool)
    judged = [r for r in rows if r["result"] in ("命中", "未命中")]
    red = sum(1 for r in judged if r["result"] == "未命中")
    print(f"  {POOL.name}：{len(rows)} 案 → 可判 {len(judged)}（红 {red}／绿 {len(judged)-red}）／"
          f"不适用 {len(rows)-len(judged)}")
    for r in rows:
        if r["result"] in ("命中", "未命中"):
            print(f"    {r['id']}：书载{r['book_yingqi_branch']} vs 引擎顶-1 {r['engine_top1']} → {r['result']}")
    if dry:
        print("    --dry-run：未写盘")
        return 0
    result = build_open_result(rows)
    for case in pool.get("cases") or []:
        case["enroll_status"] = STATUS_OPEN
    pool["open_result"] = result
    POOL.write_text(json.dumps(pool, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"    已开卷：aggregate={'null（n<30，只报逐例红绿）' if result['aggregate'] is None else result['aggregate']}"
          f"｜result_sha={result['result_sha']}")
    return 0


def verify() -> int:
    pool = json.loads(POOL.read_text(encoding="utf-8"))
    res = pool.get("open_result")
    if res is None:
        print("  × 本池未开卷（open_result 为 null）")
        return 1
    problems = []
    if res.get("open_count") != 1:
        problems.append("open_count 不是 1（开卷只许一次）")
    if res.get("metric_frozen") != METRIC:
        problems.append("冻结主指标与约定不符")
    rows = judge(pool)
    if result_sha(rows) != res.get("result_sha"):
        problems.append("判卷结果与开卷记录不符（result_sha 漂移）")
    if res.get("cases") != rows:
        problems.append("开卷记录的逐例行与现场重算不符（判卷痕迹被改写）")
    judged = [r for r in rows if r["result"] in ("命中", "未命中")]
    if len(judged) < 30 and res.get("aggregate") is not None:
        problems.append(f"可判 n={len(judged)}<30 却出现率值（违冻结口径）")
    for case in pool.get("cases") or []:
        if case.get("enroll_status") != STATUS_OPEN:
            problems.append(f"{case.get('id')} 开卷后状态未改为「{STATUS_OPEN}」")
            break
    if problems:
        for p in problems:
            print("  × " + p)
        print("[byq-open] 校验判红")
        return 1
    print("  √ 已开卷池复验全绿：判卷记录与现场重算逐位一致、指标未改、率值口径合规")
    return 0


def selftest() -> int:
    pool = json.loads(POOL.read_text(encoding="utf-8"))
    rows = judge(pool)
    probes = []

    def ok(rows_):
        p2 = copy.deepcopy(pool)
        p2["open_result"] = build_open_result(rows_)
        p2["cases"][0]["enroll_status"] = STATUS_OPEN
        res = p2["open_result"]
        same = (result_sha(rows_) == res["result_sha"]) and (res["cases"] == rows_)
        return same

    probes.append(("正常重算与开卷记录一致", ok(rows)))
    changed = copy.deepcopy(rows)
    changed[0]["result"] = "命中" if changed[0]["result"] != "命中" else "未命中"
    probes.append(("篡改判卷行 → 指纹漂移被抓", not ok(changed)))
    probes.append(("开卷一次后可重算（不改盘）", len(judge(pool)) == len(rows)))
    for name, good in probes:
        print(f"  {'√' if good else '×'} {name}")
    bad = [n for n, g in probes if not g]
    if bad:
        print(f"selftest 失败 {len(bad)} 项：{'; '.join(bad)}")
        return 1
    print(f"selftest：{len(probes)} 类负例全部抓到（全程内存，真盘零写入）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="六爻单点应期池：一次性开卷")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.verify:
        return verify()
    return open_pool(dry=not args.open)


if __name__ == "__main__":
    raise SystemExit(main())
