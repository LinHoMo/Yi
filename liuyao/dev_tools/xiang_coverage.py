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

**540 批新增 `--probe`**：现代白话问法词表的常驻判据（只读）。象不进评分、golden 案例
又是古籍体问句，词表被删/改不会有任何评分门发现——属静默退化面。探针逐条对拍
`data/rules/domain/xiang_layer.json#modern_question_probe`，并做纯内存负例自证。
**541 批补 `--selftest` 同名入口**：全体检 `sweep_selftests.py` 只扫 `--selftest` 字面量，
540 批新增的判据只有 `--probe`，故没进声明面（G9「全部」假全称同族）。别名让声明面
现算时把它收进来；两个旗标跑的是同一个 `probe()`，不产生第二份判据。

**544 批扩判据面**：象层另有两份素材表（六十四卦／八卦类象 `trigram_symbolism.json`、
动变格局与六神象义 `classical_patterns_data.json`）被消费却无任何门守着——象不进评分、
golden 又不覆盖，整块被清空全仓照绿。本批在同一 `--probe` 里加结构下限与六神枚举
断言（只守定义式不变量、不钉内容哈希），并加删键负例；不新增门号、不新增门文件。

**本器不产任何命中率、对齐分或质量结论**——象是素材，素材的「出没出」和
「准不准」是两件事，混着报就是把覆盖当成绩（SKILL.md 铁律三同款口径纪律）。

    python dev_tools/xiang_coverage.py            # 全题类扫描
    python dev_tools/xiang_coverage.py --json     # 机器可读
"""
from __future__ import annotations

import argparse
import json
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


def _probe_cases(cases: list, resolve) -> tuple[int, list[str]]:
    """纯判据：逐条对拍，空表一律判红（0 条不许伪装成全绿）。"""
    if not cases:
        return 1, ["探针表为空或路径解析失败——不许报绿"]
    bad = []
    for c in cases:
        got = resolve("", c["question"])
        if got != c["expect"]:
            bad.append(f"{c['question']}：期望 {c['expect']}，实得 {got}")
    return (1, bad) if bad else (0, [])


# 544 批：象层另有两份素材表被 chart_tables.py / trigram_symbolism.py / xiang.py
# 消费，却没有任何门守着——象不进评分（CONTRACT §五-bis）、golden 288 例又不命中
# 现代词，整块被清空时全仓门禁照样全绿。这里只守**定义式不变量**（六十四卦／八卦／
# 六神是枚举，不是会变的统计数），不钉内容哈希，词表增补不误报、删键即判红。
AUX_TABLES = {
    "data/trigram_symbolism.json": {
        "hexagram_names": 64, "trigram_directions": 8, "trigram_symbolism": 8,
    },
    "data/classical_patterns_data.json": {
        "transformation_patterns": 7, "six_spirit_properties": 6,
    },
}
SIX_SPIRITS = ("青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武")


def _probe_aux_tables(tables: dict) -> list[str]:
    """纯判据：不读盘，便于内存负例自证。"""
    bad = []
    for rel, spec in AUX_TABLES.items():
        doc = tables.get(rel)
        if not isinstance(doc, dict):
            bad.append(f"{rel}：缺失或不是对象")
            continue
        for key, floor in spec.items():
            val = doc.get(key)
            size = len(val) if isinstance(val, dict) else -1
            if size < floor:
                bad.append(f"{rel}#{key}：应 ≥{floor} 项，实得 {size}")
        if rel.endswith("classical_patterns_data.json"):
            spirits = doc.get("six_spirit_properties") or {}
            miss = [s for s in SIX_SPIRITS if s not in spirits]
            if miss:
                bad.append(f"六神象义缺：{'、'.join(miss)}")
    return bad


def probe() -> int:
    """540 批：现代白话问法词表的常驻判据 + 负例自证（纯内存，不写真盘）。

    为什么需要：象不进评分（CONTRACT §五-bis），golden 288 例又是古籍体问句，
    词表被删/改时 `check.py` 与账台都会照常全绿。这里把「启发式有没有生效」
    做成可重放断言，逐条读 `xiang_layer.json#modern_question_probe`（词表与判据同源）。
    """
    rules_path = ROOT / "data" / "rules" / "domain" / "xiang_layer.json"
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    cases = (rules.get("modern_question_probe") or {}).get("cases") or []
    import xiang
    resolve = xiang.resolve_xiang_category

    rc, bad = _probe_cases(cases, resolve)
    if rc:
        for b in bad:
            print(f"  × 现代问法探针：{b}")
        return 1
    print(f"  √ 现代问法探针：{len(cases)}/{len(cases)} 条与预声明一致（含 general 对照）")

    # 负例 1：内存里删掉一个新增词，该问句必须退化——证明词表漂移会被抓到。
    # 不写真盘、不动模块级字典本体，finally 复原（526 批的字节副作用教训）。
    orig = xiang._CATEGORY_KEYWORDS
    victim_case = next((c for c in cases if c["expect"] == "career"), None)
    if not victim_case:
        print("  × 负例缺 career 样本，无从自证")
        return 1
    try:
        xiang._CATEGORY_KEYWORDS = {
            k: [w for w in v if w != "考公"] for k, v in orig.items()
        }
        rc_shrunk, _ = _probe_cases(cases, resolve)
        degraded = resolve("", victim_case["question"])
        if rc_shrunk == 0 or degraded == victim_case["expect"]:
            print("  × 负例自证失效：删掉「考公」后仍判绿（门是瞎的）")
            return 1
        print(f"  √ 负例自证：删掉「考公」后该问句退为 {degraded}、整组判红（词表退化抓得到）")
    finally:
        xiang._CATEGORY_KEYWORDS = orig

    # 负例 2：真调用同一个纯判据喂空表，必须判红（不是写死一句「会判红」）
    rc_empty, _ = _probe_cases([], resolve)
    if rc_empty == 0:
        print("  × 负例自证失效：0 条探针仍判绿")
        return 1
    print("  √ 负例自证：0 条探针判红；真盘逐字节未改")

    # 544 批：两份象层素材表的常驻判据（结构下限 + 六神枚举）
    aux = {rel: json.loads((ROOT / rel).read_text(encoding="utf-8"))
           for rel in AUX_TABLES}
    aux_bad = _probe_aux_tables(aux)
    if aux_bad:
        for b in aux_bad:
            print(f"  × 象层素材表：{b}")
        return 1
    print(f"  √ 象层素材表：{len(AUX_TABLES)} 份结构下限与六神枚举齐备（不钉内容哈希）")

    # 负例 3：内存删掉一张表的一个键，纯判据必须判红（不写真盘）
    shrunk = {rel: dict(doc) for rel, doc in aux.items()}
    shrunk["data/trigram_symbolism.json"].pop("hexagram_names", None)
    if not _probe_aux_tables(shrunk):
        print("  × 负例自证失效：素材表被删键仍判绿（门是瞎的）")
        return 1
    print("  √ 负例自证：素材表删键判红；真盘逐字节未改")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="象层覆盖读数器（只报覆盖，不报命中率）")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    ap.add_argument("--probe", action="store_true",
                    help="540 批：现代白话问法词表常驻判据（只读 + 负例自证）")
    ap.add_argument("--selftest", action="store_true",
                    help="同 --probe。541 批：让本器进入 sweep_selftests 的声明面——"
                         "全体检只扫 `--selftest` 字面量，540 批新增的常驻判据只有 --probe，"
                         "于是「全部声明器具逐真跑」又一次名不副实（G9 同族）")
    args = ap.parse_args()
    if args.probe or args.selftest:
        return probe()
    data = scan()
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=1))
        return 0
    return report(data)


if __name__ == "__main__":
    raise SystemExit(main())
