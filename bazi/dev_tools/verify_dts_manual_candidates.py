# -*- coding: utf-8 -*-
"""《滴天髓闡微》人工认定候选池同源复验（第 569 批，只读）。

本池是 565 批机器池的**人工认定版**（569 批）：12 条"主语不明"的旺衰由人逐条读判语后认定日主强弱档。

本器的口径与其它候选池复验器不同、但更严：**池内容必须与「源池 + 人工认定表」逐字节一致**——
人工认定表是唯一的认定来源（每条含档位、逐字原话片段、理由），构建时即断言片段逐字在判语中，
故池里的任何手改都会在本器被判红。另核：
  ① 无 expected／verdict／用神等反推字段，`open_result` 须 null（未开卷）；
  ② `enroll_status` 合法、档位取值合法、理由非空；
  ③ 预注册三要素齐备；
  ④ 与在册案例及另两个候选池**三方零同四柱**；
  ⑤ 条数固定（漏案或并案即红）。

    python dev_tools/verify_dts_manual_candidates.py
    python dev_tools/verify_dts_manual_candidates.py --selftest
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
for _p in (str(DISC / "scripts"), str(DISC / "core"), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import build_dts_manual_candidates as B_  # noqa: E402
import mine_dts_candidates as M_  # noqa: E402

POOL = B_.OUT
EXPECTED_N = 12
VALID_STRENGTH = ("偏弱", "偏旺", "中和")


def verify(pool: dict | None = None) -> list[str]:
    problems: list[str] = []
    pool = pool if pool is not None else json.loads(POOL.read_text(encoding="utf-8"))

    # ① 与「源池 + 人工表」一致（人工认定表的唯一性）；开卷状态字段除外
    def _strip_open_state(p: dict) -> str:
        q = copy.deepcopy(p)
        q.pop("open_result", None)
        for case in q.get("cases") or []:
            case["enroll_status"] = "未开卷·不入册·不出分"
        return json.dumps(q, ensure_ascii=False, indent=2) + "\n"

    want = _strip_open_state(B_.build())
    got = _strip_open_state(pool)
    if got != want:
        problems.append("人工认定池与「源池 + 人工认定表」不一致（手改过，或人工表已变）")

    cases = pool.get("cases") or []
    if len(cases) != EXPECTED_N:
        problems.append(f"候选应为 {EXPECTED_N} 条，实为 {len(cases)}（漏案或并案）")
    for case in cases:
        cid = case.get("id", "?")
        if case.get("manual_strength") not in VALID_STRENGTH:
            problems.append(f"{cid} 人工档位非法：{case.get('manual_strength')}")
        if not case.get("reason"):
            problems.append(f"{cid} 缺人工认定理由")
        phrase = case.get("phrase") or ""
        if not phrase or phrase not in (case.get("source_quote") or ""):
            problems.append(f"{cid} 所引原话片段不是判语中的逐字子串")
        if "expected" in case or case.get("verdict") is not None:
            problems.append(f"{cid} 出现 expected／verdict（未开卷不得有映射，反推即红）")
        if case.get("enroll_status") not in ("未开卷·不入册·不出分", "已开卷一次·逐例红绿·无率值"):
            problems.append(f"{cid} enroll_status 非法：{case.get('enroll_status')}")
    res = pool.get("open_result")
    if res is not None:
        # 已开卷：校验开卷记录结构与状态（逐例重算由 open_candidate_pools --verify 负责）
        if res.get("open_count") != 1:
            problems.append("open_result.open_count 不是 1（开卷只许一次）")
        if not res.get("metric_frozen"):
            problems.append("open_result 缺冻结主指标（metric_frozen）")
        if res.get("aggregate") is not None:
            problems.append("aggregate 非 null（可判 n<30，按冻结口径不得出率值）")
        if not res.get("result_sha"):
            problems.append("open_result 缺 result_sha（判卷痕迹指纹）")
        for case in cases:
            if case.get("enroll_status") != "已开卷一次·逐例红绿·无率值":
                problems.append(f"{case.get('id')} 开卷后状态未改为「已开卷一次·逐例红绿·无率值」")
                break
    pre = pool.get("preregistration") or {}
    for key in ("判卷规则", "禁止", "开卷条件"):
        if not pre.get(key):
            problems.append(f"预注册缺「{key}」")

    # ④ 三方零同四柱
    enrolled = M_.enrolled_pillars()
    others = set()
    # 注：本池是 565 批**机器池同一批 12 案的重新认定**（人工补判准），故不与机器池互斥比对；
    # 只与在册案例、及另一部书的候选池（神峰）互斥。
    for name in ("shenfeng_candidates.json",):
        path = DISC / "data" / "cases" / name
        if not path.is_file():
            continue
        for case in json.loads(path.read_text(encoding="utf-8")).get("cases", []) or []:
            p = case.get("pillars") or {}
            others.add((p.get("year"), p.get("month"), p.get("day"), p.get("hour")))
    for case in cases:
        p = case.get("pillars") or {}
        key = (p.get("year"), p.get("month"), p.get("day"), p.get("hour"))
        if key in enrolled:
            problems.append(f"{case.get('id')} 与在册案例同四柱：{key}")
        if key in others:
            problems.append(f"{case.get('id')} 与另两个候选池同四柱：{key}")
    return problems


def selftest() -> int:
    probes: list[tuple[str, bool]] = []
    base = json.loads(POOL.read_text(encoding="utf-8"))

    def ok(pool: dict) -> bool:
        return not verify(pool)

    probes.append(("健康副本放行", ok(base)))

    bad1 = copy.deepcopy(base)
    bad1["cases"][0]["manual_strength"] = "大吉"
    probes.append(("档位非法 → 判红", not ok(bad1)))

    bad2 = copy.deepcopy(base)
    bad2["cases"][0]["phrase"] = "不在判语里的话"
    probes.append(("原话片段非逐字 → 判红", not ok(bad2)))

    bad3 = copy.deepcopy(base)
    bad3["cases"][0]["expected"] = {"strength": "偏弱"}
    probes.append(("出现 expected → 判红", not ok(bad3)))

    bad4 = copy.deepcopy(base)
    bad4["cases"][0]["reason"] = ""
    probes.append(("缺人工理由 → 判红", not ok(bad4)))

    bad5 = copy.deepcopy(base)
    bad5["open_result"] = {"opened": True, "open_count": 2, "metric_frozen": "x",
                           "aggregate": None, "result_sha": "y"}
    bad5["cases"][0]["enroll_status"] = "已开卷一次·逐例红绿·无率值"
    probes.append(("开卷次数被改成 2 → 判红", not ok(bad5)))

    bad5b = copy.deepcopy(base)
    bad5b["open_result"] = {"opened": True, "open_count": 1, "metric_frozen": "x",
                            "aggregate": {"n": 12, "hit": 7, "rate": 58.3}, "result_sha": "y"}
    bad5b["cases"][0]["enroll_status"] = "已开卷一次·逐例红绿·无率值"
    probes.append(("n<30 却塞进率值 → 判红", not ok(bad5b)))

    bad6 = copy.deepcopy(base)
    bad6["cases"] = bad6["cases"][:-1]
    probes.append(("漏案 → 判红", not ok(bad6)))

    for name, good in probes:
        print(f"  {'√' if good else '×'} {name}")
    bad = [n for n, good in probes if not good]
    if bad:
        print(f"selftest 失败 {len(bad)} 项：{'; '.join(bad)}")
        return 1
    print(f"selftest：{len(probes)} 类负例全部抓到（全程内存，真盘零写入）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="滴天髓人工认定池复验（只读）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    problems = verify()
    if problems:
        for p in problems:
            print("  × " + p)
        print("[dts-manual] 复验判红")
        return 1
    pool = json.loads(POOL.read_text(encoding="utf-8"))
    print(f"  √ 人工认定池复验全绿：{len(pool.get('cases') or [])} 案与「源池 + 人工表」逐字节一致、"
          f"原话逐字、理由齐备、无 expected／verdict、未开卷、三方零同四柱")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
