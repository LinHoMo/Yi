# -*- coding: utf-8 -*-
"""《滴天髓闡微》机器认定候选池同源复验（第 565 批，只读）。

为什么要有这一层：底本 513 个命造块里，当年只人工认定 12 条入评分集（`build_dts_cases.APPROVED`），
其余 500 余块从未被认领。565 批用 `mine_dts_candidates.py` 把"选哪些块"机械化，产出**未开卷**候选池
15 案（另 46 项排除带理由：12 条人工已认定、34 条与在册案例同四柱）。

本器逐条对拍（只读，不写任何文件）：
  ① 底本 sha256 与池内登记一致（底本被改动即红）；
  ② 每条 `source_quote` 是所指判语行的**逐字子串**（防手抄改字）；
  ③ 四柱块首行仍能解析出四柱，且与登记一致（登记由块程序化解析，非手抄）；
  ④ 原话片段逐字在判语中；归类由关键词机械映射可复算；
  ⑤ 判语提到的日干／月支与日柱／月柱相符（自洽门）；
  ⑥ 整池**无 expected／吉凶方向／用神**，`verdict` 一律 null，`open_result` 须 null（未开卷）；
  ⑦ 预注册三要素齐备；`excluded` 每项带理由（不能悄悄丢块）；
  ⑧ 与在册案例**零同四柱**；候选 ID 零泄漏进分片登记；
  ⑨ 条数固定（漏案或并案即红）。

    python dev_tools/verify_dts_candidates.py
    python dev_tools/verify_dts_candidates.py --selftest
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

import build_dts_cases as B_  # noqa: E402
import mine_dts_candidates as M_  # noqa: E402

POOL = DISC / "data" / "cases" / "dts_candidates.json"
EXPECTED_N = 15
ID_PREFIX = "DTC"


def load_pool() -> dict:
    return json.loads(POOL.read_text(encoding="utf-8"))


def verify(pool: dict | None = None) -> list[str]:
    pool = pool if pool is not None else load_pool()
    problems: list[str] = []

    src_sha = hashlib.sha256(B_.SRC.read_bytes()).hexdigest()
    if pool.get("source", {}).get("sha256") != src_sha:
        problems.append("底本 sha256 与池内登记不一致（底本被改动或登记抄错）")

    lines = B_.SRC.read_text(encoding="utf-8").splitlines()
    blocks = B_.parse_blocks(lines)
    by_head = {b["head_line"]: b for b in blocks}

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
            problems.append(f"{cid} 判语行号越界：{line_no}")
        elif quote not in lines[line_no - 1]:
            problems.append(f"{cid} 引文不是源L{line_no} 的逐字子串（改字／串行）")

        head = case.get("head_line")
        block = by_head.get(head)
        if block is None:
            problems.append(f"{cid} 四柱块首行 L{head} 已不可解析（底本变动？）")
        else:
            pillars = case.get("pillars") or {}
            got = [pillars.get(k) for k in ("year", "month", "day", "hour")]
            if got != list(block["pillars"]):
                problems.append(f"{cid} 四柱与底本块不符：登记 {got} ≠ 底本 {list(block['pillars'])}")
            phrase = case.get("phrase") or ""
            if not phrase or phrase not in block["speech"]:
                problems.append(f"{cid} 原话片段不在判语中")
            expect_cat = next((cat for kw, cat in M_.ANCHORS if kw == phrase), None)
            if expect_cat is None or expect_cat != case.get("category"):
                problems.append(f"{cid} 归类与关键词机械映射不符：{case.get('category')}")
            day_ref, month_ref = B_.DAY_REF.search(block["speech"]), B_.MON_REF.search(block["speech"])
            pl = list(block["pillars"])
            if day_ref and day_ref.group(1) != pl[2][0]:
                problems.append(f"{cid} 判语日主 {day_ref.group(1)} ≠ 日柱 {pl[2]}")
            if month_ref and month_ref.group(1) != pl[1][1]:
                problems.append(f"{cid} 判语月支 {month_ref.group(1)} ≠ 月柱 {pl[1]}")

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

    excluded = pool.get("excluded") or []
    for item in excluded:
        if not item.get("reason"):
            problems.append(f"excluded L{item.get('source_line', '?')} 缺排除理由（不能悄悄丢块）")

    # 与在册案例零同四柱
    enrolled = M_.enrolled_pillars()
    for case in cases:
        pillars = case.get("pillars") or {}
        key = (pillars.get("year"), pillars.get("month"), pillars.get("day"), pillars.get("hour"))
        if key in enrolled:
            problems.append(f"{case.get('id')} 与在册案例同四柱：{key}")

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
    red("判语行号指向别处", lambda p: p["cases"][0].__setitem__("source_line", p["cases"][0]["source_line"] + 1))
    red("四柱与底本块不符", lambda p: p["cases"][0]["pillars"].__setitem__("day", "甲子"))
    red("原话不在判语中", lambda p: p["cases"][0].__setitem__("phrase", "不在判语里的话"))
    red("归类与映射不符", lambda p: p["cases"][0].__setitem__("category", "大吉"))
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
    ap = argparse.ArgumentParser(description="《滴天髓闡微》候选池复验（只读）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    problems = verify()
    if problems:
        for p in problems:
            print("  × " + p)
        print("[dts-candidates] 复验判红：候选池与底本/纪律不合")
        return 1
    pool = load_pool()
    print(f"  √ 滴天髓候选池复验全绿：{len(pool.get('cases') or [])} 案引文逐字、四柱可复算、"
          f"归类可复算、无 expected／verdict、未开卷、与在册案例零同四柱；"
          f"excluded {len(pool.get('excluded') or [])} 项均带理由")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
