# -*- coding: utf-8 -*-
"""《卜筮全书》占验段候选池同源复验（第 564 批，只读）。

为什么新建池而不往旧池加：546 批的 BQS 池已于 547 批**一次性开卷判卷**，往开过卷的池里加新案
会同时坏掉两件事——① 一次性开卷的效力；② 同源书（《黄金策》等）承袭同案会被当新案计入。
故本批另立**未开卷**新池 `bushi_quanshu_paiyan_candidates.json`，只登记书证与定位，
不写 expected／verdict 映射；开卷须另获用户授权。

本器逐条对拍（全部只读，不写任何文件）：
  ① 底本 sha256 与池内登记一致（底本被改动即红）；
  ② 每条 `source_quote` 是所指行的**逐字子串**（防手抄改字）；
  ③ `date_text`／`hexagram_text` 确实出现在引文里，指针不悬空；
  ④ 整池**无 expected 块**、`verdict` 一律 null、`yingqi_text` 一律 null（未开卷，反推即红）；
  ⑤ `open_result` 必须为 null（未开卷；一旦开卷必须留痕，否则判红）；
  ⑥ `preregistration` 存在且含判卷规则与开卷条件（预注册不可缺）；
  ⑦ `excluded` 每条都带排除理由（不能悄悄丢案）；
  ⑧ 候选 ID 零泄漏进 `case_splits.json`（未开卷不得进任何分片）；
  ⑨ 去重：以「干支日 + 本卦名」对现有在册案例文件实跑比对，命中即红（承袭同案）；
  ⑩ 条数固定（漏案或并案即红）。

    python dev_tools/verify_bushi_paiyan_candidates.py
    python dev_tools/verify_bushi_paiyan_candidates.py --selftest
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
POOL = DISC / "data" / "cases" / "bushi_quanshu_paiyan_candidates.json"
SPLITS = DISC / "data" / "cases" / "case_splits.json"
SOURCE = DISC / "data" / "sources" / "bushi_quanshu_dz.dz.txt"

EXPECTED_N = 8
EXPECTED_EXCLUDED = 2
ID_PREFIX = "BQP"
ALLOWED_STATUS = ("未开卷·不入册·不出分",)
DAY_TOKEN = re.compile(r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]日")


def load_pool() -> dict:
    return json.loads(POOL.read_text(encoding="utf-8"))


def source_lines() -> list[str]:
    return SOURCE.read_text(encoding="utf-8").splitlines()


def _day_token(text: str) -> str:
    """日期归一：只取「干支日」，去掉月份前缀与旬空尾巴（用于跨集去重比对）。"""
    m = DAY_TOKEN.search(text or "")
    return m.group(0) if m else ""


def enrolled_pairs() -> set[tuple[str, str]]:
    """在册案例的（干支日, 本卦名）集合——来自 data/cases 下各案例文件。"""
    pairs: set[tuple[str, str]] = set()
    for path in sorted((DISC / "data" / "cases").glob("*.json")):
        if path.name == POOL.name:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        def walk(node):
            if isinstance(node, dict):
                hexa = node.get("hexagram")
                orig = hexa.get("original") if isinstance(hexa, dict) else None
                inp = node.get("input")
                date = inp.get("date") if isinstance(inp, dict) else node.get("date")
                if orig and date:
                    tok = _day_token(str(date))
                    if tok:
                        pairs.add((tok, str(orig).strip()))
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(data)
    return pairs


def split_ids(splits: dict) -> set[str]:
    ids: set[str] = set()
    for value in splits.values():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    ids.add(item)
                elif isinstance(item, dict):
                    for key in ("id", "case_id"):
                        if key in item:
                            ids.add(str(item[key]))
    return ids


def verify(pool: dict | None = None) -> list[str]:
    pool = pool if pool is not None else load_pool()
    problems: list[str] = []

    src_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if pool.get("source", {}).get("sha256") != src_sha:
        problems.append("底本 sha256 与池内登记不一致（底本被改动或登记抄错）")

    cases = pool.get("cases") or []
    if len(cases) != EXPECTED_N:
        problems.append(f"候选应为 {EXPECTED_N} 条，实为 {len(cases)}（漏案或并案）")

    lines = source_lines()
    ids: set[str] = set()
    for case in cases:
        cid = case.get("id", "?")
        if not str(cid).startswith(ID_PREFIX):
            problems.append(f"候选 ID 前缀不对：{cid}")
        if cid in ids:
            problems.append(f"候选 ID 重复：{cid}")
        ids.add(cid)
        quote = case.get("source_quote") or ""
        line_no = case.get("source_line")
        if not isinstance(line_no, int) or not (1 <= line_no <= len(lines)):
            problems.append(f"{cid} 行号越界或非整数：{line_no}")
            continue
        if quote not in lines[line_no - 1]:
            problems.append(f"{cid} 引文不是源L{line_no} 的逐字子串（改字／串行）")
        date_text = case.get("date_text") or ""
        if not date_text or date_text not in quote:
            problems.append(f"{cid} 日期不在引文内（指针悬空）")
        hexa = case.get("hexagram_text") or ""
        if not hexa or hexa not in quote:
            problems.append(f"{cid} 卦名不在引文内（指针悬空）")
        if "expected" in case:
            problems.append(f"{cid} 写了 expected（未开卷不得有映射，反推即红）")
        if case.get("verdict") is not None:
            problems.append(f"{cid} verdict 非 null（未开卷不得判吉凶）")
        if case.get("yingqi_text") is not None:
            problems.append(f"{cid} yingqi_text 非 null（未开卷不得先写应期）")
        if case.get("enroll_status") not in ALLOWED_STATUS:
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
    if len(excluded) != EXPECTED_EXCLUDED:
        problems.append(f"excluded 应为 {EXPECTED_EXCLUDED} 项，实为 {len(excluded)}")
    for item in excluded:
        if not item.get("reason"):
            problems.append(f"excluded {item.get('id', '?')} 缺排除理由（不能悄悄丢案）")

    leaked = sorted(ids & split_ids(json.loads(SPLITS.read_text(encoding="utf-8"))))
    if leaked:
        problems.append(f"候选 ID 泄漏进 case_splits（未开卷不得进任何分片）：{leaked}")

    known = enrolled_pairs()
    for case in cases:
        tok = _day_token(case.get("date_text") or "")
        key = (tok, str(case.get("hexagram_text") or "").strip())
        if key in known:
            problems.append(f"{case.get('id')} 与在册案例同案（日期＋卦名）：{key}")

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
    red("写了 expected", lambda p: p["cases"][0].__setitem__("expected", {"verdict": "吉"}))
    red("verdict 非 null", lambda p: p["cases"][0].__setitem__("verdict", "吉"))
    red("yingqi 先写", lambda p: p["cases"][0].__setitem__("yingqi_text", "午日"))
    red("open_result 非 null（未授权开卷）", lambda p: p.__setitem__("open_result", {"opened": True}))
    red("删预注册", lambda p: p.__setitem__("preregistration", {}))
    red("候选漏案", lambda p: p["cases"].pop())
    red("ID 重复", lambda p: p["cases"][1].__setitem__("id", p["cases"][0]["id"]))
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
    ap = argparse.ArgumentParser(description="《卜筮全书》占验段候选池复验（只读）")
    ap.add_argument("--selftest", action="store_true", help="负例自证（内存，不写真盘）")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    problems = verify()
    if problems:
        for p in problems:
            print("  × " + p)
        print("[bushi-paiyan] 复验判红：候选池与底本/纪律不合")
        return 1
    pool = load_pool()
    print(f"  √ 占验段候选池复验全绿：{len(pool.get('cases') or [])} 案引文逐字、行锚可达、"
          f"无 expected／verdict 映射、未开卷、零泄漏进分片、与在册案例零同案；"
          f"excluded {len(pool.get('excluded') or [])} 项均带理由")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
