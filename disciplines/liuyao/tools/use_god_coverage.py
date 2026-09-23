# -*- coding: utf-8 -*-
"""用神取法来源矩阵：每条问法是靠"带引文的法则"还是靠"词典猜"定的用神。

    python tools/use_god_coverage.py                  # 汇总 + 逐条
    python tools/use_god_coverage.py --only-default   # 只看靠词典/兜底的问法
    python tools/use_god_coverage.py --json           # 机器可读，供门户或报告引用

为什么要有这张表：引擎取用神有两层——`data/rules/use_god_relations.json`（逐条带
《增刪卜易》原文引文，可复核）和 `thinking_chain._QUESTION_USE_GOD_MAP`（190 条现代
问法词典，无出处）。没有这张矩阵时，"用神 100%"这种数字分不清是**有据**还是
**词典刚好猜对**——而对外行说两者完全不同。AGENTS.md 铁律三要求口径诚实。
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
    """返回 {use_god, source: 法则|词典|兜底, citation, keys}。"""
    from yishu_core.symbols import normalize_question_text
    rule = tc._match_use_god_rule(text)
    got = tc._determine_use_god_category("", text)
    if rule and rule.get("use_god") == got:
        return {"use_god": got, "source": "法则", "citation": rule.get("citation", ""),
                "keys": rule.get("trigger", [])}
    norm = normalize_question_text(text)
    keys = [k for k in tc._QUESTION_USE_GOD_MAP if k in norm]
    src = "词典" if keys else "兜底"
    return {"use_god": got, "source": src, "citation": "", "keys": sorted(keys, key=len, reverse=True)}


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
    ap.add_argument("--only-default", action="store_true", help="只列非引文法则命中的问法")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = []
    for cid, q in questions():
        r = classify(q)
        r.update({"id": cid, "question": q[:38]})
        rows.append(r)

    by = collections.Counter(r["source"] for r in rows)
    total = len(rows)
    if args.json:
        print(json.dumps({"summary": dict(by), "rows": rows}, ensure_ascii=False, indent=2))
        return 0

    print(f"问法 {total} 条：法则 {by['法则']}（{by['法则'] * 100 // total}%，逐条可回查原文）、"
          f"词典 {by['词典']}、兜底 {by['兜底']}")
    print("\n  词典/兜底明细（这些用神没有古籍逐条依据，属推断）")
    for r in rows:
        if r["source"] == "法则" or args.only_default and r["source"] == "法则":
            continue
        if r["source"] != "法则" and (not args.only_default or r["source"] != "词典"):
            pass
        keys = ",".join(r["keys"][:4]) or "（无命中键）"
        flag = " ⚠单字键" if any(k in SINGLE_CHAR_KEYS for k in r["keys"]) else ""
        print(f"   [{r['source']}] {r['id']:9s} {r['use_god']:4s} ← {r['question']:26s} 键:{keys}{flag}")
    single = [r for r in rows if any(k in SINGLE_CHAR_KEYS for k in r["keys"])]
    print(f"\n其中靠单字键定用神的问法 {len(single)} 条（子串匹配易误命中，优先改成带引文的多字法则）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
