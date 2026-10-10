# -*- coding: utf-8 -*-
"""用神取法来源矩阵：每条问法是靠带引文的法则、覆盖层、词典还是兜底定的用神。

    python tools/use_god_coverage.py                  # 汇总 + 逐条
    python tools/use_god_coverage.py --only-default   # 只看兜底（三层都未命中的题）
    python tools/use_god_coverage.py --only-inference # 只看词典·推断族（无出处）
    python tools/use_god_coverage.py --json           # 机器可读，供门户或报告引用

为什么要有这张表：引擎取用神分四层——`data/rules/use_god_relations.json`（关系法则，
逐条带《增刪卜易》原文引文）、chain_step2 覆盖层（消歧层，7 类带层引文）、
`data/rules/question_use_gods.json`（186 条现代问法词典，按 64 族分 有据/推断）、
世爻兜底。分类直接消费 `_decide_use_god` 的 meta.source，不再各自复刻判断
（复刻过的那份把覆盖层命中的问法误报成了"兜底"）。没有这张矩阵时，
"用神 100%"这种数字分不清是**有据**还是**词典刚好猜对**——而对外行说两者
完全不同。AGENTS.md 铁律三要求口径诚实。
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
from kernel_path import ensure_kernel_on_path  # noqa: E402

ensure_kernel_on_path(__file__)
import case_runner                                                # noqa: E402
import thinking_chain as tc                                       # noqa: E402
from yishu_core.runtime import force_utf8_stdio                   # noqa: E402

# 词典里可能误命中的单字键（子串匹配，会命中无关词："占买房子"的"子"）
SINGLE_CHAR_KEYS = {k for k in tc._QUESTION_USE_GOD_MAP if len(k) == 1}


def classify(text: str) -> dict:
    """返回 {use_god, source: 法则|覆盖|词典|兜底, layer, citation, keys, basis_kind}。

    source 取自 chain_step2._decide_use_god 的决策元信息；词典层再按族的
    basis.kind 分 有据(citation)/推断(inference)，覆盖层按有无层引文分。
    """
    got, meta = tc._decide_use_god("", text)
    source = meta.get("source", "兜底")
    layer = meta.get("label", "")
    citation = meta.get("citation", "")
    keys = list(meta.get("keys") or [])
    basis_kind = ""
    if source == "词典":
        top = max(keys, key=len) if keys else ""
        basis_kind = (tc._QUESTION_USE_GOD_BASIS.get(top) or {}).get("kind", "")
    elif source == "覆盖":
        basis_kind = "citation" if citation else "inference"
    return {"use_god": got, "source": source, "layer": layer,
            "citation": citation, "keys": keys, "basis_kind": basis_kind}


def questions() -> list[tuple[str, str]]:
    """案例库/外部集里的问法，加上一批现代常见问法（词典就是为它们写的）。
    现代问法标 (现代)，它们没有古籍答案，只用来暴露"这条靠不靠词典猜"。"""
    out = [(c["id"], (c.get("question") or c.get("topic") or "").strip())
           for c in case_runner.load_cases()]
    modern = ["问感情他喜不喜欢我", "问正缘什么时候出现", "问跳槽还是留下", "问这只股票该不该抛",
              "问面试能否通过", "问合伙做生意", "问租房签约", "问孩子升学", "问婆婆病情",
              "问贷款能批吗", "问官司会不会输", "问丢失的钱包能否找回", "问对方是否已婚"]
    out += [(f"现代{i + 1:02d}", q) for i, q in enumerate(modern)]
    return [(cid, q) for cid, q in out if q]


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="用神取法来源矩阵")
    ap.add_argument("--only-default", action="store_true", help="只列三层都未命中的兜底问法")
    ap.add_argument("--only-inference", action="store_true",
                    help="只列依据为推断的问法（词典·推断族 + 无引文覆盖层）")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = []
    for cid, q in questions():
        r = classify(q)
        r.update({"id": cid, "question": q[:38]})
        rows.append(r)

    by = collections.Counter(r["source"] for r in rows)
    grounded = sum(1 for r in rows if r["source"] == "法则"
                   or r["basis_kind"] == "citation")
    total = len(rows)
    if args.json:
        print(json.dumps({"summary": dict(by), "grounded": grounded, "rows": rows},
                         ensure_ascii=False, indent=2))
        return 0

    pct = lambda v: f"{v * 100 // total}%" if total else "0%"  # noqa: E731
    print(f"问法 {total} 条：法则 {by['法则']}（逐条可回查原文）、"
          f"覆盖 {by['覆盖']}、词典 {by['词典']}、兜底 {by['兜底']}")
    n_cit = sum(1 for r in rows if r["source"] == "词典" and r["basis_kind"] == "citation")
    print(f"其中有古籍依据（法则 + 词典·有据族 + 带引文覆盖层）≈ {grounded}；"
          f"词典·有据族 {n_cit}，其余为推断/兜底")

    print("\n  非法则明细（这些用神靠覆盖层消歧或词典推断，逐条说清所本）")
    for r in rows:
        if r["source"] == "法则":
            continue
        if args.only_default and r["source"] != "兜底":
            continue
        if args.only_inference and r["basis_kind"] != "inference":
            continue
        keys = ",".join(sorted(r["keys"], key=len, reverse=True)[:4]) or "（无命中键）"
        flag = " ⚠单字键" if any(k in SINGLE_CHAR_KEYS for k in r["keys"]) else ""
        layer = f" ·{r['layer']}" if r["layer"] else ""
        print(f"   [{r['source']}|{r['basis_kind'] or '-'}] {r['id']:9s} "
              f"{r['use_god']:4s} ← {r['question']:26s} 键:{keys}{layer}{flag}")
    single = [r for r in rows if any(k in SINGLE_CHAR_KEYS for k in r["keys"])]
    print(f"\n其中靠单字键定用神的问法 {len(single)} 条（子串匹配易误命中，优先改成带引文的多字法则）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
