# -*- coding: utf-8 -*-
"""判定表门（A3·第三百一十四批）：`data/rules/judgment_table.json` 的六条判据。

为什么需要它：
  313 批把"谁压谁"从古籍读成了 25 条书证与 9 格草案，但那还是**文档**。
  文档会烂：行号会漂、格会少填、书证会抄错，最要命的是**代码改了覆写而表不知道**——
  于是"判定表"变成又一份没人维护的台账（§六.1 反复清除的那类）。

本门只做六件事，每件都能判红：
  1. **格面**：方向 3 × 置信 3 恰好 9 格，无缺无重；每格有 enter 谓词与至少一条书证。
  2. **书证逐字**：每条 citation 的 quote 必须在《书》源L 所指行的邻域逐字命中
     （复用 `check_source_readings` 的底本表与归一化，不另建第二套口径）。
  3. **引用闭合**：cells / priority / adjudications 引到的 id 必须存在于 citations；
     且没有未被任何一处引用的孤儿书证。
  4. **表随码动**：从 `step5.py` 的 AST **重算**覆写清单（哪一行、条件原文），
     与 JSON 的 `overrides` 逐条对齐——多一处、少一处、改一个字都判红。
  5. **覆写分类**：每处覆写必须有 kind∈{priority,exception,domain_overlay}；
     domain_overlay 必须带 domain；kind 分布与 `stats.by_kind` 一致。
  6. **值面覆盖**：step5 里赋给 verdict 的每个字符串字面量，必须在 `verdict_map` 里有归处——
     新增一个判词而不登记，即红（防"下跌"这类词再次偷偷长出来）。

状态机：`status` 只许 `proposed` / `accepted`。**改成 accepted 的硬条件**是
`adjudications` 四条全部签押（status != pending）——因为那四条是人的判断，不是机器的。

    python dev_tools/check_judgment_table.py
    python dev_tools/check_judgment_table.py --selftest   # 负例：证明本器抓得住
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
import tempfile
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DISC / "core"))
sys.path.insert(0, str(DISC / "dev_tools"))
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

import check_source_readings as _csr  # noqa: E402  底本表与归一化只认它一份

TABLE = DISC / "data" / "rules" / "judgment_table.json"
STEP5 = DISC / "scripts" / "step5.py"
KINDS = ("priority", "exception", "domain_overlay")


def _inventory(step5_src: str) -> list[dict]:
    """从 step5 AST 重算"改判分支"清单：(行号, 条件原文, 赋值语句)。"""
    tree = ast.parse(step5_src)
    lines = step5_src.split("\n")
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        cond = (ast.get_source_segment(step5_src, node.test) or "").replace("\n", " ")
        if "verdict" not in cond:
            continue
        body = [ln.strip() for ln in lines[node.lineno - 1:node.end_lineno] if ln.strip()]
        assigns = [ln for ln in body if ln.startswith("verdict =")]
        if not assigns:
            continue
        out.append({"line": node.lineno, "cond": cond[:90], "assigns": assigns[:2]})
    out.sort(key=lambda x: x["line"])
    return out


def _verdict_literals(step5_src: str) -> set:
    """`verdict = "X"` 的**直接取值**字面量（含 `A if c else B` 两臂）。

    只认直接赋值面的常量：早先版本对整个右值 ast.walk，把 `d.get("verdict")` 这类
    调用参数里的字符串也当成判词，凭空多出 `''`／`'verdict'` 两个假值——
    **门的取数面比语义宽一圈，就会逼文档去登记不存在的东西**。
    """
    got = set()
    for node in ast.walk(ast.parse(step5_src)):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "verdict" for t in node.targets):
            continue
        val = node.value
        arms = [val.body, val.orelse] if isinstance(val, ast.IfExp) else [val]
        for arm in arms:
            if isinstance(arm, ast.Constant) and isinstance(arm.value, str) and arm.value.strip():
                got.add(arm.value)
    return got


def _check_citations(table: dict, corpora: dict, cache: dict) -> list[str]:
    bad = []
    for c in table.get("citations", []):
        cid, book, line, quote = c.get("id"), c.get("book"), c.get("line"), c.get("quote", "")
        title, why = _csr.resolve_book(book or "", corpora)
        if not title:
            bad.append(f"书证 {cid}：书名《{book}》不可解析（{why[:1]}）")
            continue
        if title not in cache:
            cache[title] = _csr._corpus_lines(corpora[title]["path"])
        src = cache[title]
        if not isinstance(line, int) or not (1 <= line <= len(src)):
            bad.append(f"书证 {cid}：行号 {line} 越界（《{title}》共 {len(src)} 行）")
            continue
        hay = "".join(_csr.norm(x) for x in src[max(0, line - 2):line + 3])
        miss = [f for f in _csr._frags(quote) if _csr.norm(f) not in hay]
        if miss:
            bad.append(f"书证 {cid}：《{title}》源L{line} 邻域无「{miss[0][:18]}」")
    return bad


def check(table_path: Path = TABLE) -> list[str]:
    problems: list[str] = []
    table = json.loads(table_path.read_text(encoding="utf-8"))
    corpora = _csr.load_corpora()
    cache: dict = {}

    # 1. 格面
    axes = table.get("axes", {})
    dirs, confs = axes.get("direction", []), axes.get("confidence", [])
    if len(dirs) != 3 or len(confs) != 3:
        problems.append(f"轴面不对：direction={dirs} confidence={confs}（应为各 3 档）")
    seen = set()
    for c in table.get("cells", []):
        key = (c.get("direction"), c.get("confidence"))
        if key in seen:
            problems.append(f"格重复：{key}")
        seen.add(key)
        if not str(c.get("enter", "")).strip():
            problems.append(f"格 {key} 缺 enter 谓词")
        if not c.get("cites"):
            problems.append(f"格 {key} 缺书证")
    want = {(d, k) for d in dirs for k in confs}
    if seen != want:
        problems.append(f"格面不全：缺 {sorted(want - seen)}，多 {sorted(seen - want)}")

    # 2. 书证逐字
    problems += _check_citations(table, corpora, cache)

    # 3. 引用闭合
    ids = {c.get("id") for c in table.get("citations", [])}
    used: set = set()
    for grp in ("cells", "priority", "adjudications", "overlays"):
        for item in table.get(grp, []):
            for cid in item.get("cites", []):
                used.add(cid)
                if cid not in ids:
                    problems.append(f"{grp} 引用了不存在的书证 id：{cid}")
    orphans = sorted(ids - used)
    if orphans:
        problems.append(f"孤儿书证（未被任何格/优先级/裁决引用）：{orphans}")

    # 3b. 题类覆盖层（v1）：条件/产出/书证三件齐全，方向置信必须在轴内
    for o in table.get("overlays", []):
        oid = o.get("id")
        if not str(o.get("domain") or "").strip():
            problems.append(f"覆盖层 {oid} 缺 domain")
        if not str(o.get("when") or "").strip():
            problems.append(f"覆盖层 {oid} 缺 when 条件")
        emit = o.get("emit") or {}
        if emit.get("direction") not in dirs:
            problems.append(f"覆盖层 {oid} 的 emit.direction 不在轴内：{emit.get('direction')}")
        if emit.get("confidence") not in confs:
            problems.append(f"覆盖层 {oid} 的 emit.confidence 不在轴内：{emit.get('confidence')}")
        if o.get("book_verified") and not o.get("cites"):
            problems.append(f"覆盖层 {oid} 声称有书证却没有 cites")

    # 4/5. 表随码动 + 覆写分类
    src = STEP5.read_text(encoding="utf-8")
    live = _inventory(src)
    reg = table.get("overrides", [])
    if len(live) != len(reg):
        problems.append(f"覆写数量分家：盘上 {len(live)} 处，表内 {len(reg)} 处——代码改了表没跟")
    for a, b in zip(live, reg):
        if a["line"] != b.get("line") or a["cond"] != b.get("cond"):
            problems.append(
                f"覆写错位：盘上 L{a['line']}「{a['cond'][:28]}」vs 表内 "
                f"L{b.get('line')}「{str(b.get('cond'))[:28]}」")
            break
    by_kind = {k: 0 for k in KINDS}
    for o in reg:
        k = o.get("kind")
        if k not in KINDS:
            problems.append(f"覆写 {o.get('id')} 的 kind 非法：{k}")
            continue
        by_kind[k] += 1
        if k == "domain_overlay" and not o.get("domain"):
            problems.append(f"覆写 {o.get('id')} 是题类覆盖但没有 domain")
    stats = table.get("stats", {}).get("by_kind", {})
    if stats != by_kind:
        problems.append(f"stats.by_kind 与实算不符：表 {stats} vs 实 {by_kind}")

    # 6. 值面覆盖
    lits = _verdict_literals(src)
    vmap = table.get("verdict_map", {})
    missing = sorted(x for x in lits if x not in vmap)
    if missing:
        problems.append(f"step5 会产出但 verdict_map 未登记的判词：{missing}")

    # 状态机
    status = table.get("status")
    if status not in ("proposed", "accepted"):
        problems.append(f"status 非法：{status}")
    if status == "accepted":
        unsigned = [a["id"] for a in table.get("adjudications", []) if a.get("status") == "pending"]
        if unsigned:
            problems.append(f"标 accepted 但裁决未签：{unsigned}")
    return problems


def selftest() -> int:
    """负例自证：五类伤病必须被本器抓到，健康副本必须放行。"""
    base = json.loads(TABLE.read_text(encoding="utf-8"))
    cases = []

    t = json.loads(json.dumps(base))
    t["citations"][0]["line"] = t["citations"][0]["line"] + 300
    cases.append(("书证行号漂移", t))

    t = json.loads(json.dumps(base))
    t["cells"] = t["cells"][:-1]
    cases.append(("少一格", t))

    t = json.loads(json.dumps(base))
    t["overrides"] = t["overrides"][:-1]
    cases.append(("覆写少登记一处", t))

    t = json.loads(json.dumps(base))
    t["overrides"][0]["kind"] = "someday"
    cases.append(("kind 非法", t))

    t = json.loads(json.dumps(base))
    t["verdict_map"].pop("下跌", None)
    cases.append(("判词未登记", t))

    t = json.loads(json.dumps(base))
    if t.get("overlays"):
        t["overlays"][0]["emit"] = {"direction": "大吉", "confidence": "中"}
    cases.append(("覆盖层方向不在轴内", t))

    t = json.loads(json.dumps(base))
    if t.get("overlays"):
        t["overlays"][0]["cites"] = ["Z9"]
    cases.append(("覆盖层引用不存在的书证", t))

    t = json.loads(json.dumps(base))
    t["status"] = "accepted"
    if t.get("adjudications"):
        t["adjudications"][0]["status"] = "pending"
        t["adjudications"][0].pop("chosen", None)
    cases.append(("未签就 accepted", t))

    fails = []
    with tempfile.TemporaryDirectory() as td:
        for name, obj in cases:
            p = Path(td) / "t.json"
            p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
            got = check(p)
            if not got:
                fails.append(name)
            else:
                print(f"  √ 负例被抓：{name} → {got[0][:60]}")
        # 健康副本必须放行
        p = Path(td) / "ok.json"
        p.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
        if check(p):
            fails.append("健康副本被误判")
    if fails:
        print(f"  × selftest 失败：{fails}")
        return 1
    print(f"  √ selftest：{len(cases)} 类负例全部抓到；健康副本放行")
    return 0


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="判定表门（A3）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    problems = check()
    if problems:
        for p in problems:
            print(f"  × {p}")
        return 1
    t = json.loads(TABLE.read_text(encoding="utf-8"))
    st = t.get("stats", {})
    print(f"  √ 格面 {st.get('cells')}／书证 {st.get('citations')}／覆写 {st.get('overrides')}"
          f"／覆盖层 {st.get('overlays', 0)}"
          f"（priority {st.get('by_kind', {}).get('priority')}·exception "
          f"{st.get('by_kind', {}).get('exception')}·domain "
          f"{st.get('by_kind', {}).get('domain_overlay')}），status={t.get('status')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
