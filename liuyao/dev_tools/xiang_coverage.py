#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""象层覆盖读数器（362 批）：量「象出没出」，不量「象准不准」。

为什么单独做一个读数器：本仓的评测口径（evaluate.WEIGHTS）里**没有象的维度**——
象不进评分（CONTRACT §五-bis），于是象这条线从来没有被量过。没被量过的东西会退化：
素材在盘面里、正文里一个字不出，也能一路绿灯（这正是本批之前的实况）。

本器回答两个问题，且只回答这两个：
  ① 覆盖：每个象目（trigram/ti_yong/guaci/yaoci/hu_gua/spirit/fangwei/class_image）
     在各类问法下的产出率是多少？缺的到底缺在哪一类？
  ② 题类分布：题类→象类别的映射实际生效情况（有没有整类落 general 的退化）。

**本器不产任何命中率、对齐分或质量结论**——象是素材，素材的「出没出」和
「准不准」是两件事，混着报就是把覆盖当成绩（SKILL.md 铁律三同款口径纪律）。

    python dev_tools/xiang_coverage.py            # 全题类扫描
    python dev_tools/xiang_coverage.py --json     # 机器可读
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

XIANG_KEYS = ("trigram", "ti_yong", "guaci", "yaoci", "hu_gua", "spirit",
              "fangwei", "class_image")

# 逐题类一句代表问法（问法须能命中 question_classes.json 的对应题类；
# 每类一句，不做加权——本器报的是「有没有」，不是「多常见」）
CLASS_QUESTIONS = [
    ("逃亡捕捉", "占问走失的仆人能否追回"),
    ("功名科举", "占问今年科举能否中第"),
    ("官非词讼", "占问这场官司胜负如何"),
    ("疾病·久病", "占问多年旧疾何时可愈"),
    ("疾病·近病", "占问此病何时痊愈"),
    ("失物", "占问丢失的银钱能否找回"),
    ("终身财福", "占问终身财福如何"),
    ("求财", "占问这笔生意能否获利"),
    ("天气·占雨", "占问何日有雨"),
    ("天气·占晴", "占问何日放晴"),
    ("行人", "占问远行之人何日归来"),
    ("婚姻", "占问这桩婚事可否成就"),
    ("其他", "占问此事吉凶如何"),
]


def _xiang_of(question: str, seed: int = 42) -> dict:
    from chart import chart as _chart
    from analyze import analyze as _analyze
    return _analyze(_chart("coin", question, seed=seed)).get("xiang") or {}


def _filled(blk) -> bool:
    """象目是否真的有内容（不是空 dict / 空 list / 只有 basis）。"""
    if not isinstance(blk, dict):
        return False
    body = {k: v for k, v in blk.items() if k != "basis"}
    return any(v not in ("", None, [], {}) for v in body.values())


def scan(seeds=(42, 7)) -> dict:
    rows = []
    for cls, q in CLASS_QUESTIONS:
        for seed in seeds:
            x = _xiang_of(q, seed)
            rows.append({
                "class": cls, "question": q, "seed": seed,
                "category": x.get("category") or "（缺）",
                "keys": {k: _filled(x.get(k)) for k in XIANG_KEYS},
                "has": bool(x),
            })
    return {"rows": rows, "keys": list(XIANG_KEYS)}


def report(data: dict) -> int:
    rows = data["rows"]
    keys = data["keys"]
    n = len(rows)
    print(f"象层覆盖读数：{n} 路实跑（{len(CLASS_QUESTIONS)} 题类 × {n // len(CLASS_QUESTIONS)} 种子）")
    print("口径：**有没有出**（素材覆盖），不是「准不准」（命中率）——本器不产任何质量分\n")

    print("① 象目产出率")
    for k in keys:
        hit = sum(1 for r in rows if r["keys"].get(k))
        miss = [r["class"] for r in rows if not r["keys"].get(k)]
        tail = f"　缺：{'、'.join(sorted(set(miss)))}" if miss else ""
        print(f"  {k:<12} {hit}/{n}  {hit * 100 // n}%{tail}")

    print("\n② 题类 → 象类别（对照映射表，看映射是否真生效）")
    from xiang import _CATEGORY_BY_CLASS  # 映射表唯一真源在 data/rules/xiang_layer.json
    seen: dict[str, set[str]] = {}
    for r in rows:
        seen.setdefault(r["class"], set()).add(r["category"])
    bad = 0
    for cls, cats in seen.items():
        exp = _CATEGORY_BY_CLASS.get(cls, "general")
        if cats == {exp}:
            note = "（有意取通用：本题类无专属类象）" if exp == "general" and cls != "其他" else ""
        else:
            note = f"  ← 与映射表不符（应为 {exp}）"
            bad += 1
        print(f"  {cls:<10} → {'/'.join(sorted(cats))}　{note}")
    if bad:
        print(f"  ！{bad} 个题类的象类别与映射表不符——先查问句是否真命中该题类"
              "（question_classes 的优先级与关键词族是另一条线）")

    zero = [r for r in rows if not r["has"]]
    if zero:
        print(f"\n× 象层整块缺失 {len(zero)} 路："
              + "、".join(f"{r['class']}(seed{r['seed']})" for r in zero[:6]))
        return 1
    print("\n读数完毕。缺哪一类就补哪一类，别拿本器的百分比当成绩。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="象层覆盖读数器（只报覆盖，不报命中率）")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = ap.parse_args()
    data = scan()
    if args.json:
        import json
        print(json.dumps(data, ensure_ascii=False, indent=1))
        return 0
    return report(data)


if __name__ == "__main__":
    raise SystemExit(main())
