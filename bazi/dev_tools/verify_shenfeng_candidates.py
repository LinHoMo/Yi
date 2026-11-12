# -*- coding: utf-8 -*-
"""《神峰通考》命例候选池同源复验（第 566 批，只读）。

与 565 批《滴天髓》候选池复验器同型，逐条对拍（只读，不写任何文件）：
  ① 底本 sha256 与池内登记一致；
  ② 每条 `source_quote` 是所指行**余文的逐字子串**，且该行行首四柱可解析；
  ③ 登记四柱与行首正则复算结果一致（登记非手抄）；
  ④ `pattern_suffix`／`gender`／`labels` 三项标签可由固定规则复算；
  ⑤ 整池**无 expected／吉凶方向／用神**，`verdict` 一律 null，`open_result` 须 null（未开卷）；
  ⑥ 预注册三要素齐备；`excluded` 每项带理由；
  ⑦ 与**在册案例**及《滴天髓》候选池**三方零同四柱**；
  ⑧ 条数固定（漏案或并案即红）。

    python dev_tools/verify_shenfeng_candidates.py
    python dev_tools/verify_shenfeng_candidates.py --selftest
"""
from __future__ import annotations

import argparse
import copy
import hashlib
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

import mine_dts_candidates as M_  # noqa: E402
import mine_shenfeng_candidates as S_  # noqa: E402

POOL = DISC / "data" / "cases" / "shenfeng_candidates.json"
DTS_POOL = DISC / "data" / "cases" / "dts_candidates.json"
EXPECTED_N = 157
ID_PREFIX = "SFC"


def load_pool() -> dict:
    return json.loads(POOL.read_text(encoding="utf-8"))


def verify(pool: dict | None = None) -> list[str]:
    pool = pool if pool is not None else load_pool()
    problems: list[str] = []

    if pool.get("source", {}).get("sha256") != hashlib.sha256(S_.SRC.read_bytes()).hexdigest():
        problems.append("底本 sha256 与池内登记不一致（底本被改动或登记抄错）")

    lines = S_.SRC.read_text(encoding="utf-8").splitlines()
    parsed = {b["head_line"]: b for b in S_.parse_cases()}

    cases = pool.get("cases") or []
    if len(cases) != EXPECTED_N:
        problems.append(f"候选应为 {EXPECTED_N} 条，实为 {len(cases)}（漏案或并案）")

    ids: set[str] = set()
    for case in cases:
        cid = case.get("id", "?")
        if not str(cid).startswith(ID_PREFIX):
            problems.append(f"候选 ID 前缀不对：{cid}")
        if cid in ids:
            problems.append(f"候选 ID 重复：{cid}")
        ids.add(cid)

        line_no = case.get("source_line")
        quote = case.get("source_quote") or ""
        if not isinstance(line_no, int) or not (1 <= line_no <= len(lines)):
            problems.append(f"{cid} 行号越界：{line_no}")
        elif quote not in lines[line_no - 1]:
            problems.append(f"{cid} 引文不是源L{line_no} 的逐字子串（改字／串行）")

        block = parsed.get(line_no)
        if block is None:
            problems.append(f"{cid} 该行已不可解析为命例行（底本变动？）")
        else:
            pillars = case.get("pillars") or {}
            got = [pillars.get(k) for k in ("year", "month", "day", "hour")]
            if got != list(block["pillars"]):
                problems.append(f"{cid} 四柱与底本行不符：登记 {got} ≠ 底本 {list(block['pillars'])}")
            if case.get("pattern_suffix") != block["pattern_suffix"]:
                problems.append(f"{cid} pattern_suffix 与机械抽取结果不符")
            if case.get("gender") != block["gender"]:
                problems.append(f"{cid} gender 与机械抽取结果不符")
            if case.get("labels") != block["labels"]:
                problems.append(f"{cid} labels 与固定词表命中结果不符")

        if "expected" in case:
            problems.append(f"{cid} 写了 expected（未开卷不得有映射，反推即红）")
        if case.get("verdict") is not None:
            problems.append(f"{cid} verdict 非 null（未开卷不得判吉凶）")
        if case.get("enroll_status") != "未开卷·不入册·不出分":
            problems.append(f"{cid} enroll_status 非法：{case.get('enroll_status')}")
        if not case.get("block"):
            problems.append(f"{cid} 缺入册阻断说明")

    if pool.get("open_result") is not None:
        problems.append("open_result 非 null：本池尚未授权开卷，开卷须另获授权并留痕")

    pre = pool.get("preregistration") or {}
    for key in ("判卷规则", "禁止", "开卷条件"):
        if not pre.get(key):
            problems.append(f"预注册缺「{key}」")

    for item in pool.get("excluded") or []:
        if not item.get("reason"):
            problems.append(f"excluded L{item.get('source_line', '?')} 缺排除理由（不能悄悄丢案）")

    enrolled = M_.enrolled_pillars()
    dts_pillars: set[tuple] = set()
    if DTS_POOL.is_file():
        for case in json.loads(DTS_POOL.read_text(encoding="utf-8")).get("cases", []) or []:
            p = case.get("pillars") or {}
            dts_pillars.add((p.get("year"), p.get("month"), p.get("day"), p.get("hour")))
    for case in cases:
        p = case.get("pillars") or {}
        key = (p.get("year"), p.get("month"), p.get("day"), p.get("hour"))
        if key in enrolled:
            problems.append(f"{case.get('id')} 与在册案例同四柱：{key}")
        if key in dts_pillars:
            problems.append(f"{case.get('id')} 与《滴天髓》候选池同四柱：{key}")

    return problems


def selftest() -> int:
    pool = load_pool()
    probes: list[tuple[str, bool]] = []

    def red(name: str, mutate) -> None:
        bad = copy.deepcopy(pool)
        mutate(bad)
        probes.append((name, bool(verify(bad))))

    def green(name: str) -> None:
        probes.append((name, not verify(copy.deepcopy(pool))))

    green("健康副本放行")
    red("改一个字（引文非逐字）", lambda p: p["cases"][0].__setitem__("source_quote", (p["cases"][0]["source_quote"] or "") + "。"))
    red("行号指向别处", lambda p: p["cases"][0].__setitem__("source_line", p["cases"][0]["source_line"] + 1))
    red("四柱与底本行不符", lambda p: p["cases"][0]["pillars"].__setitem__("day", "甲子"))
    red("pattern_suffix 与机械抽取不符", lambda p: p["cases"][0].__setitem__("pattern_suffix", "假格局"))
    red("gender 与机械抽取不符", lambda p: p["cases"][0].__setitem__("gender", "男"))
    red("写了 expected", lambda p: p["cases"][0].__setitem__("expected", {"verdict": "吉"}))
    red("verdict 非 null", lambda p: p["cases"][0].__setitem__("verdict", "吉"))
    red("open_result 非 null", lambda p: p.__setitem__("open_result", {"opened": True}))
    red("删预注册", lambda p: p.__setitem__("preregistration", {}))
    red("候选漏案", lambda p: p["cases"].pop())
    red("excluded 无理由", lambda p: p["excluded"][0].pop("reason", None))
    red("底本哈希错", lambda p: p["source"].__setitem__("sha256", "0" * 64))

    bad = [name for name, ok in probes if not ok]
    for name, ok in probes:
        print(f"  {'√' if ok else '×'} {name}")
    if bad:
        print(f"selftest 失败 {len(bad)} 项：{'; '.join(bad)}")
        return 1
    print(f"selftest：{len(probes)} 类负例全部抓到（全程内存，真盘零写入）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="《神峰通考》候选池复验（只读）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    problems = verify()
    if problems:
        for p in problems:
            print("  × " + p)
        print("[shenfeng-candidates] 复验判红：候选池与底本/纪律不合")
        return 1
    pool = load_pool()
    print(f"  √ 神峰候选池复验全绿：{len(pool.get('cases') or [])} 案引文逐字、四柱可复算、标签可复算、"
          f"无 expected／verdict、未开卷、与在册及滴天髓池三方零同四柱；"
          f"excluded {len(pool.get('excluded') or [])} 项均带理由")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
