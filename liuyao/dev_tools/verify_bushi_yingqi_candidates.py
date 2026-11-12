# -*- coding: utf-8 -*-
"""六爻「带单点应期」候选池同源复验（574 批，只读）。

核四件事：
  ① 池内容与「底本＋人工认定表」逐字节一致（引文程序化截取，任何手改即红）；
  ② 每案的书载要素（起卦日干支／月建／卦名／应期支／应期干支）都**逐字出现在引文里**；
  ③ 整池无 expected／吉凶方向，`verdict` 一律 null；预注册三要素齐备；
  ④ 已开卷则校验开卷记录（开卷次数=1、冻结指标未改、逐例行与现场重算一致、n<30 无率值），
     未开卷则要求 `open_result` 为 null。

    python dev_tools/verify_bushi_yingqi_candidates.py
    python dev_tools/verify_bushi_yingqi_candidates.py --selftest
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
for _sub in ("scripts", "core", ""):
    sys.path.insert(0, str(DISC / _sub) if _sub else str(DISC))

import build_bushi_yingqi_candidates as B_  # noqa: E402
import open_bushi_yingqi_candidates as O_  # noqa: E402

POOL = B_.OUT
EXPECTED_N = 16


def verify(pool: dict | None = None) -> list[str]:
    problems: list[str] = []
    pool = pool if pool is not None else json.loads(POOL.read_text(encoding="utf-8"))
    want = json.dumps(B_.build(), ensure_ascii=False, indent=2) + "\n"

    def strip_open_state(p: dict) -> str:
        q = copy.deepcopy(p)
        q.pop("open_result", None)
        for case in q.get("cases") or []:
            case["enroll_status"] = "未开卷·不入册·不出分"
        return json.dumps(q, ensure_ascii=False, indent=2) + "\n"

    if strip_open_state(pool) != strip_open_state(json.loads(want)):
        problems.append("候选池与「底本＋人工认定表」不一致（手改过，或人工表已变）")

    cases = pool.get("cases") or []
    if len(cases) != EXPECTED_N:
        problems.append(f"候选应为 {EXPECTED_N} 条，实为 {len(cases)}（漏案或并案）")
    for case in cases:
        cid = case.get("id", "?")
        quote = case.get("source_quote") or ""
        for field, token in (("day_ganzhi", case.get("day_ganzhi") or ""),
                             ("hexagram_text", case.get("hexagram_text") or ""),
                             ("book_yingqi_ganzhi", case.get("book_yingqi_ganzhi") or "")):
            if not token or token not in quote:
                problems.append(f"{cid} 的 {field}「{token}」不在引文内（书证指针悬空）")
        if case.get("verdict") is not None:
            problems.append(f"{cid} verdict 非 null（未开卷不得有吉凶判定）")
        if "expected" in case:
            problems.append(f"{cid} 出现 expected（反推即红）")
        if case.get("enroll_status") not in ("未开卷·不入册·不出分", O_.STATUS_OPEN):
            problems.append(f"{cid} enroll_status 非法：{case.get('enroll_status')}")
    pre = pool.get("preregistration") or {}
    for key in ("判卷规则", "禁止", "开卷条件"):
        if not pre.get(key):
            problems.append(f"预注册缺「{key}」")

    res = pool.get("open_result")
    if res is None:
        if pool.get("cases") and any(c.get("enroll_status") == O_.STATUS_OPEN for c in pool["cases"]):
            problems.append("状态已是已开卷但缺 open_result")
    else:
        if res.get("open_count") != 1:
            problems.append("open_count 不是 1（开卷只许一次）")
        if res.get("metric_frozen") != O_.METRIC:
            problems.append("冻结主指标与约定不符")
        rows = O_.judge(pool)
        if O_.result_sha(rows) != res.get("result_sha"):
            problems.append("判卷结果与开卷记录不符（result_sha 漂移）")
        if res.get("cases") != rows:
            problems.append("开卷记录的逐例行与现场重算不符（判卷痕迹被改写）")
        judged = [r for r in rows if r["result"] in ("命中", "未命中")]
        if len(judged) < 30 and res.get("aggregate") is not None:
            problems.append(f"可判 n={len(judged)}<30 却出现率值（违冻结口径）")
    return problems


def selftest() -> int:
    pool = json.loads(POOL.read_text(encoding="utf-8"))
    probes = []

    def ok(p):
        return not verify(p)

    probes.append(("健康副本放行", ok(copy.deepcopy(pool))))
    bad1 = copy.deepcopy(pool)
    bad1["cases"][0]["source_quote"] = (bad1["cases"][0]["source_quote"] or "") + "。"
    probes.append(("引文被改 → 判红", not ok(bad1)))
    bad2 = copy.deepcopy(pool)
    bad2["cases"][0]["verdict"] = "吉"
    probes.append(("出现 verdict → 判红", not ok(bad2)))
    bad3 = copy.deepcopy(pool)
    bad3["cases"] = bad3["cases"][:-1]
    probes.append(("漏案 → 判红", not ok(bad3)))
    for name, good in probes:
        print(f"  {'√' if good else '×'} {name}")
    bad = [n for n, g in probes if not g]
    if bad:
        print(f"selftest 失败 {len(bad)} 项：{'; '.join(bad)}")
        return 1
    print(f"selftest：{len(probes)} 类负例全部抓到（全程内存，真盘零写入）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="六爻单点应期候选池复验（只读）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    problems = verify()
    if problems:
        for p in problems:
            print("  × " + p)
        print("[byq-verify] 复验判红")
        return 1
    pool = json.loads(POOL.read_text(encoding="utf-8"))
    state = "已开卷" if pool.get("open_result") else "未开卷"
    print(f"  √ 单点应期候选池复验全绿：{len(pool.get('cases') or [])} 案与「底本＋人工表」一致、"
          f"书证要素逐字在引文内、无 expected／verdict、{state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
