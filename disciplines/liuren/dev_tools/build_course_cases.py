# -*- coding: utf-8 -*-
"""书源内嵌课例提取器（一次性数据构建，产物入库、脚本留档可复跑）。

源：data/sources/liu-ren-da-quan.wikitext.txt（卷一「起例」）与
`liu-ren-da-quan-juan3..12.wikitext.txt`（卷三「歌赋」、卷七~十「课经集」、
卷十一~十二《毕法赋》）——即《六壬大全》全书散见的内嵌课例。

严格口径（三者俱备、且**唯一**才收例，宁缺勿滥）：
  ① 同一句内**恰有一个**日干支（「X日」）——多日并列句（「丁巳、丁丑二日」、
     「壬戌、壬辰日…癸丑…亦…」之类）一律不收，因一句常把同一条三传摊给数日，
     或数日各归各例，机械切分必错；
  ② 同一句内**恰有一处**明写三传（「三传XYZ」，无分隔符）；
  ③ 天地盘定位语且**出现在「三传」之前**：
     「干上X」→ δ=X-寄宫；「支上X」→ δ=X-日支；「X加Y」→ δ=X-Y。
     排除「初传/末传/中传/发用/为用 X加Y」这类**非天地盘**的传内关系语
     （如「巳加子为初传」说的是初传而非月将加时）。
每例以「日干支 + δ」唯一重建天地盘，再由九宗门复算三传；expected 只含书上明写的量
（三传；门类仅在「日」与「三传」之间明写时登记）。每例逐字 source_quote 可回指原文
（铁律三）。引文取整句、截断仅加省略号，不改字。

    python dev_tools/build_course_cases.py            # 写盘
    python dev_tools/build_course_cases.py --check    # 只比对是否与入库文件一致
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
ROOT = DISC.parents[1]
SRC = ROOT / "data" / "sources"
# 顺序即 ID 顺序：卷一、卷三在最先，故 LE001~LE004 的编号在任何扩源下都不动。
SOURCES = [SRC / "liu-ren-da-quan.wikitext.txt"] + [
    SRC / f"liu-ren-da-quan-juan{n}.wikitext.txt" for n in range(3, 13)]
OUT = DISC / "data" / "cases" / "course_examples.json"

# 寄宫唯一真值源在 core（AGENTS.md §二）
sys.path.insert(0, str(ROOT / "core"))
from yishu_core.liuren_tables import JI_GONG  # noqa: E402
from yishu_core.symbols import EARTHLY_BRANCHES, HEAVENLY_STEMS  # noqa: E402
from yishu_core import corpus_kit  # noqa: E402  语料可复现性比对

# `HEAVENLY_STEMS` 是 **list**：f-string 插进字符类会变成 `['甲', '乙', …, '癸']]`，
# 类在首个 `]` 处提前闭合并多出一个必须匹配的字面 `]` → 正则**永不匹配**。
# 本建器原写法 `STEMS = HEAVENLY_STEMS` 使 `DAY_RE` 恒不命中 → 抽到 0 例，
# 而 `main()` 无条件落盘，**重跑会把 course_examples.json 清空**（同 ming/build_tiaohou 的坑）。
STEMS = "".join(HEAVENLY_STEMS)
BRANCHES = "".join(EARTHLY_BRANCHES)
DAY_RE = re.compile(rf"([{STEMS}])([{BRANCHES}])日")
TRIPLE_RE = re.compile(rf"三传([{BRANCHES}])([{BRANCHES}])([{BRANCHES}])")
JIA_RE = re.compile(rf"([{BRANCHES}])加([{BRANCHES}])")
GANSHANG_RE = re.compile(rf"干上([{BRANCHES}])")
ZHISHANG_RE = re.compile(rf"支上([{BRANCHES}])")
# 多日并列 / 日柱列举（「丁巳、丁丑」「壬戌、壬辰」）——句内出现即视为多例，不收。
DAY_LIST_RE = re.compile(rf"[{STEMS}][{BRANCHES}][、,，]")
BR_IDX = {b: i for i, b in enumerate(EARTHLY_BRANCHES)}

# 书明写门类（「X日遥克」「夜占昴星」等）→ expected_men 锚。门类词须落在
# 「日」与「三传」之间才算数（否则句尾的泛提会把门类安到不相干的例上）。
MEN_WORDS = ("遥克", "伏吟", "返吟", "昴星", "别责", "八专", "涉害")
# 传内关系语（非天地盘定位）：其前的「X加Y」不得用作 δ
INNER_CTX = ("初传", "中传", "末传", "发用", "为用")


def sources_text() -> str:
    """并入扫描的书源全文（卷一 + 卷三~卷十二）。"""
    return "\n".join(src.read_text(encoding="utf-8") for src in SOURCES)


def build_doc() -> dict:
    """书源全文 → 课例集（纯计算，不落盘）。"""
    segment = sources_text()

    cases: list[dict] = []
    seen_keys: set[tuple] = set()
    stats = {"sentences": 0, "has_triple": 0, "has_single_day": 0,
             "has_determiner": 0, "kept": 0, "dropped_multi_triple": 0,
             "dropped_day_count": 0, "dropped_day_list": 0, "dropped_no_determiner": 0}

    for sentence in re.split(r"[。\n]", segment):
        if "三传" not in sentence:
            continue
        stats["sentences"] += 1
        tris = list(TRIPLE_RE.finditer(sentence))
        if len(tris) != 1:
            stats["dropped_multi_triple"] += 1
            continue
        stats["has_triple"] += 1
        tri_at = tris[0].start()
        expected = list(tris[0].groups())

        days = list(DAY_RE.finditer(sentence))
        if len(days) != 1:
            stats["dropped_day_count"] += 1
            continue
        if DAY_LIST_RE.search(sentence):
            stats["dropped_day_list"] += 1
            continue
        stats["has_single_day"] += 1
        stem, branch = days[0].group(1), days[0].group(2)

        # 天地盘定位语，须在「三传」之前
        delta, how = None, ""
        gs = next((m for m in GANSHANG_RE.finditer(sentence) if m.start() < tri_at), None)
        zs = next((m for m in ZHISHANG_RE.finditer(sentence) if m.start() < tri_at), None)
        if gs:
            delta = (BR_IDX[gs.group(1)] - BR_IDX[JI_GONG[stem]]) % 12
            how = f"干上{gs.group(1)}"
        elif zs:
            delta = (BR_IDX[zs.group(1)] - BR_IDX[branch]) % 12
            how = f"支上{zs.group(1)}"
        else:
            jm = next((m for m in JIA_RE.finditer(sentence)
                       if m.start() < tri_at
                       and not any(k in sentence[max(0, m.start() - 4):m.start()]
                                   for k in INNER_CTX)), None)
            if jm:
                delta = (BR_IDX[jm.group(1)] - BR_IDX[jm.group(2)]) % 12
                how = f"{jm.group(1)}加{jm.group(2)}"
        if delta is None:
            stats["dropped_no_determiner"] += 1
            continue
        stats["has_determiner"] += 1

        # 书明写门类：须落在「日」与「三传」之间
        mid = sentence[days[0].end():tri_at]
        expected_men = next((w for w in MEN_WORDS if w in mid), None)

        key = (stem + branch, delta, tuple(expected))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        # 引文取整句（不截断、不改字），保持逐字可回指（铁律三）
        quote = sentence.strip()
        cases.append({
            "id": f"LE{len(cases) + 1:03d}",
            "book": "六壬大全",
            "location": "六壬大全（内嵌课例）",
            "source_quote": quote,
            "day_ganzhi": stem + branch,
            "delta": delta,
            "determiner": how,
            "expected": {"san_chuan": expected},
            "expected_men": expected_men,
        })
        stats["kept"] += 1
    # 引文逐字可回指（铁律三）：每条 source_quote 必须是书源全文的原样子串
    stats["unverbatim"] = sum(1 for c in cases if c["source_quote"] not in segment)

    return {
        "schema": "yi-liuren-course-examples/1",
        "_comment": [
            "书源内嵌课例（《六壬大全》卷一、卷三~卷十二：起例/歌赋/课经集/毕法赋），"
            "expected 只有书上明写的三传。",
            "重建方式：定位语（X加Y/干上X/支上X，须在「三传」之前且非传内关系语）"
            "→ 天地盘旋转 delta → 九宗门复算。",
            "本集度量是**机械一致率**（引擎三传 vs 书面三传），不是对齐分，",
            "更不是现实预测命中率（NEW-DISCIPLINES §2.1：两类分数必须分开报）。",
        ],
        "stats": stats,
        "cases": cases,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="六壬大全内嵌课例提取（默认写盘）")
    ap.add_argument("--check", action="store_true",
                    help="不落盘，只比对已入库 data/cases/course_examples.json 是否与重算一致")
    args = ap.parse_args()

    doc = build_doc()
    stats, cases = doc["stats"], doc["cases"]
    if args.check:
        return corpus_kit.report(OUT.name, corpus_kit.check(OUT, doc))
    if stats["unverbatim"]:
        print(f"× 有 {stats['unverbatim']} 条 source_quote 非书源原样子串（铁律三），拒绝落盘")
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"抽取统计：{stats}")
    for c in cases:
        print(f"  {c['id']} {c['day_ganzhi']} δ={c['delta']}（{c['determiner']}）"
              f" 三传={''.join(c['expected']['san_chuan'])} | {c['source_quote'][:46]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
