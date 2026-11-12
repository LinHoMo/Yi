# -*- coding: utf-8 -*-
"""八字候选池一次性开卷（568 批，用户授权「开卷吧」后落地）。

开卷对象：`dts_candidates.json`（565 批《滴天髓闡微》机器认定 15 案）与
`shenfeng_candidates.json`（566 批《神峰通考》命例 157 案）。两池此前均**未开卷**
（`open_result: null`），预注册见各池 `preregistration`。

**冻结主指标（开卷前定，开卷后不得改）**：引擎 `strength.strength`（偏弱／偏旺／中和）
与**书载强度档**是否一致——书载档的取法是**机械映射**：
  · 滴天髓池：取池内 `category`（565 批建池时由判语关键词机械映射，未手改）；
  · 神峰池：取池内 `labels` 中的强弱词（身弱／身衰／衰弱／衰极／从弱／日主本衰／此衰极从弱之理
    →偏弱；身旺／旺极矣／强旺极矣／太旺 →偏旺；中和／中和纯粹／中和之象／中和之气 →中和）。
**判准缺失**（书载无强弱词、或四柱不可还原为真实时刻）一律记「不适用」，不硬判。

**只报逐例红绿**：可判 n < 30 时 `aggregate` 恒 null、结构里不出现率值字段、不作任何能力声称
（沿用 546 批冻结的 decision_rule 口径）。开封只此一次：已开卷的池再开即拒绝。

    python dev_tools/open_candidate_pools.py --dry-run   # 只打印逐例，不写盘
    python dev_tools/open_candidate_pools.py --open      # 开卷一次，追加 open_result
    python dev_tools/open_candidate_pools.py --verify    # 只读校验（CI 挂这个）
    python dev_tools/open_candidate_pools.py --selftest  # 内存负例自证
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
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
for _p in (str(DISC / "scripts"), str(DISC / "core")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

POOLS = (
    (DISC / "data" / "cases" / "dts_candidates.json", "滴天髓闡微·机器认定池"),
    (DISC / "data" / "cases" / "shenfeng_candidates.json", "神峰通考·命例池"),
    (DISC / "data" / "cases" / "dts_manual_candidates.json", "滴天髓闡微·人工认定池"),
)
STATUS_OPEN = "已开卷一次·逐例红绿·无率值"
STRENGTH_WORDS = {
    "偏弱": ("身弱", "身衰", "衰弱", "衰极", "从弱", "日主本衰", "此衰极从弱之理"),
    "偏旺": ("身旺", "旺极矣", "强旺极矣", "太旺"),
    "中和": ("中和纯粹", "中和之象", "中和之气", "中和"),
}
METRIC_FROZEN = "引擎 strength.strength（偏弱／偏旺／中和）↔ 书载强度档一致（书载档＝池内机械映射）"


def book_strength(pool_path: Path, case: dict) -> str | None:
    """书载强度档：只从**机械映射**取，取不到即无判准（记不适用）。"""
    manual = case.get("manual_strength")
    if manual in ("偏弱", "偏旺", "中和"):
        return manual
    if pool_path.name.startswith("dts_"):
        cat = case.get("category")
        return cat if cat in ("偏弱", "偏旺", "中和") else None
    labels = case.get("labels") or []
    for cat, words in STRENGTH_WORDS.items():
        if any(w in labels for w in words):
            return cat
    return None


def engine_strength(datetime_str: str) -> str | None:
    """引擎强弱档：跑一次 chart→analyze，取 strength.strength。"""
    from chart import chart  # noqa: E402
    from analyze import analyze  # noqa: E402
    try:
        c = chart("命局", datetime_str=datetime_str, gender="")
        st = (analyze(c).get("strength") or {})
    except Exception:
        return None
    val = st.get("strength")
    return val if val in ("偏弱", "偏旺", "中和") else None


def judge_pool(pool: dict, pool_path: Path) -> list[dict]:
    rows = []
    for case in pool.get("cases") or []:
        rec = {"id": case.get("id"), "book_strength": book_strength(pool_path, case),
               "real_datetime": case.get("real_datetime"), "engine_strength": None, "result": None}
        dt = case.get("real_datetime")
        if not dt:
            rec["result"] = "不适用·四柱不可还原为真实时刻"
            rows.append(rec)
            continue
        rec["engine_strength"] = engine_strength(dt)
        if rec["book_strength"] is None:
            rec["result"] = "不适用·书载无强弱判准"
            rows.append(rec)
            continue
        if rec["engine_strength"] is None:
            rec["result"] = "不适用·引擎未给出强弱档"
            rows.append(rec)
            continue
        rec["result"] = "命中" if rec["engine_strength"] == rec["book_strength"] else "未命中"
        rows.append(rec)
    return rows


def result_sha(rows: list[dict]) -> str:
    canon = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16]


def build_open_result(pool: dict, rows: list[dict]) -> dict:
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip() or "unknown"
    judged = [r for r in rows if r["result"] in ("命中", "未命中")]
    aggregate = None
    if len(judged) >= 30:
        aggregate = {"n": len(judged), "hit": sum(1 for r in judged if r["result"] == "命中"),
                     "rate": round(100.0 * sum(1 for r in judged if r["result"] == "命中") / len(judged), 1)}
    return {
        "opened_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "commit_at_open": commit,
        "open_count": 1,
        "metric_frozen": METRIC_FROZEN,
        "aggregate": aggregate,
        "_comment": ("开卷只此一次；aggregate 仅在可判 n≥30 时给出（n<30 恒 null、结构内无率值字段）。"
                     "判准缺失与四柱不可还原者记「不适用」，不硬判、不充数。"
                     "本池开卷结果**不入评分分片**（入册评分集须另获授权）。"),
        "cases": rows,
        "result_sha": result_sha(rows),
    }


def open_pool(pool_path: Path, dry: bool) -> int:
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    if pool.get("open_result") is not None:
        print(f"  × {pool_path.name} 已开卷（open_result 非 null）——封存事件的判卷只允许一次")
        return 1
    rows = judge_pool(pool, pool_path)
    judged = [r for r in rows if r["result"] in ("命中", "未命中")]
    red = sum(1 for r in judged if r["result"] == "未命中")
    green = len(judged) - red
    na = len(rows) - len(judged)
    print(f"  {pool_path.name}：{len(rows)} 案 → 可判 {len(judged)}（红 {red}／绿 {green}）／不适用 {na}")
    for rec in rows:
        if rec["result"] in ("命中", "未命中"):
            print(f"    {rec['id']}：书载{rec['book_strength']} vs 引擎{rec['engine_strength']} → {rec['result']}")
    if dry:
        print("    --dry-run：未写盘")
        return 0
    result = build_open_result(pool, rows)
    for case in pool.get("cases") or []:
        case["enroll_status"] = STATUS_OPEN
    pool["open_result"] = result
    pool_path.write_text(json.dumps(pool, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    agg = result.get("aggregate")
    print(f"    已开卷：aggregate={'null（n<30，只报逐例红绿）' if agg is None else agg}｜result_sha={result['result_sha']}")
    return 0


def verify_pool(pool: dict, pool_path: Path) -> list[str]:
    problems: list[str] = []
    res = pool.get("open_result")
    if res is None:
        return [f"{pool_path.name} 未开卷（open_result 为 null）"]
    rows = judge_pool(pool, pool_path)
    if result_sha(rows) != res.get("result_sha"):
        problems.append(f"{pool_path.name} 判卷结果与开卷记录不符（result_sha 漂移）")
    if res.get("cases") != rows:
        problems.append(f"{pool_path.name} 开卷记录的逐例行与现场重算不符（判卷痕迹被改写）")
    for case in pool.get("cases") or []:
        if case.get("enroll_status") != STATUS_OPEN:
            problems.append(f"{pool_path.name} {case.get('id')} 状态未改为「{STATUS_OPEN}」")
            break
    judged = [r for r in rows if r["result"] in ("命中", "未命中")]
    agg = res.get("aggregate")
    if len(judged) < 30 and agg is not None:
        problems.append(f"{pool_path.name} 可判 n={len(judged)}<30 却出现率值（违冻结口径）")
    if len(judged) >= 30 and agg is None:
        problems.append(f"{pool_path.name} 可判 n={len(judged)}≥30 却缺率值（违冻结口径）")
    return problems


def verify() -> int:
    problems: list[str] = []
    for pool_path, _label in POOLS:
        pool = json.loads(pool_path.read_text(encoding="utf-8"))
        problems += verify_pool(pool, pool_path)
    if problems:
        for p in problems:
            print("  × " + p)
        print("[open-candidate-pools] 校验判红")
        return 1
    print("  √ 已开卷池复验全绿：判卷记录与现场重算逐位一致、状态合法、率值口径合规")
    return 0


def selftest() -> int:
    """内存负例自证：正常开卷副本放行；三类篡改（删开卷记录／改判卷行／伪造率值）必被抓。"""
    probes: list[tuple[str, bool]] = []
    pool_path = POOLS[0][0]
    base = json.loads(pool_path.read_text(encoding="utf-8"))
    rows = judge_pool(base, pool_path)
    opened = copy.deepcopy(base)
    opened["open_result"] = build_open_result(opened, rows)
    for case in opened.get("cases") or []:
        case["enroll_status"] = STATUS_OPEN

    def ok(pool: dict) -> bool:
        return not verify_pool(pool, pool_path)

    probes.append(("正常开卷副本放行", ok(opened)))

    bad1 = copy.deepcopy(opened)
    bad1["open_result"] = None
    probes.append(("删掉 open_result → 判红", not ok(bad1)))

    bad2 = copy.deepcopy(opened)
    bad2["open_result"]["cases"][0]["result"] = "命中" if bad2["open_result"]["cases"][0]["result"] != "命中" else "未命中"
    probes.append(("篡改判卷行 → result_sha 漂移被抓", not ok(bad2)))

    judged = [r for r in rows if r["result"] in ("命中", "未命中")]
    bad3 = copy.deepcopy(opened)
    if len(judged) < 30:
        bad3["open_result"]["aggregate"] = {"n": len(judged), "hit": 0, "rate": 0.0}
    probes.append(("n<30 却伪造率值 → 判红", not ok(bad3)))

    bad4 = copy.deepcopy(opened)
    bad4["cases"][0]["enroll_status"] = "未开卷·不入册·不出分"
    probes.append(("状态未改为已开卷 → 判红", not ok(bad4)))

    for name, good in probes:
        print(f"  {'√' if good else '×'} {name}")
    bad = [n for n, good in probes if not good]
    if bad:
        print(f"selftest 失败 {len(bad)} 项：{'; '.join(bad)}")
        return 1
    print(f"selftest：{len(probes)} 类负例全部抓到（全程内存，真盘零写入）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="八字候选池一次性开卷")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--only", default="", help="只处理指定池文件名（如 dts_manual_candidates.json）")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.verify:
        return verify()
    rc = 0
    for pool_path, _label in POOLS:
        if args.only and args.only not in pool_path.name:
            continue
        if args.open and json.loads(pool_path.read_text(encoding="utf-8")).get("open_result") is not None:
            print(f"  · {pool_path.name}：已开卷（跳过，不重开）")
            continue
        rc |= open_pool(pool_path, dry=not args.open)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
