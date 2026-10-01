# -*- coding: utf-8 -*-
"""书源内嵌课例提取器（一次性数据构建，产物入库、脚本留档可复跑）。

源：data/sources/liu-ren-da-quan.wikitext.txt（卷一「课经/格局」段，行 2400–2720）。
严格口径——三者俱备才收例：
  ① 日干支（「X日」，支持「乙丑、乙巳二日」多日并列，逐日各成一例）；
  ② 天地盘定位语（「戌加未发用」→ δ=戌-未；「干上辰」→ δ=辰-寄宫；
     「支上寅」→ δ=寅-日支），由此唯一重建天地盘；
  ③ 明写三传（「三传戌丑辰」，无分隔符）。
expected 只含书上明写的量：三传（其余维度一律不入 expected）。
每例逐字 source_quote 可回指原文（铁律三）。定位语缺失/歧义的句子一律不收
（宁缺勿滥），统计见构建输出。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
ROOT = DISC.parents[1]
SOURCES = [ROOT / "data" / "sources" / "liu-ren-da-quan.wikitext.txt",
           ROOT / "data" / "sources" / "liu-ren-da-quan-juan3.wikitext.txt"]
OUT = DISC / "data" / "cases" / "course_examples.json"

# 寄宫唯一真值源在 core（AGENTS.md §二）
sys.path.insert(0, str(ROOT / "core"))
from yishu_core.liuren_tables import JI_GONG  # noqa: E402

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "寅卯辰巳午未申酉戌亥子丑"
DAY_RE = re.compile(rf"([{STEMS}])([{BRANCHES}])日")
TRIPLE_RE = re.compile(rf"三传([{BRANCHES}])([{BRANCHES}])([{BRANCHES}])")
JIA_RE = re.compile(rf"([{BRANCHES}])加([{BRANCHES}])")
GANSHANG_RE = re.compile(rf"干上([{BRANCHES}])")
ZHISHANG_RE = re.compile(rf"支上([{BRANCHES}])")
BR_IDX = {b: i for i, b in enumerate("子丑寅卯辰巳午未申酉戌亥")}

# 全文扫描：内嵌课例散见于 课经/格局/毕法引文/占法 各段（两份书源全文）


def main() -> int:
    segment = "\n".join(src.read_text(encoding="utf-8") for src in SOURCES)

    cases: list[dict] = []
    seen_quotes: set[str] = set()
    stats = {"sentences": 0, "has_triple": 0, "has_day": 0, "has_determiner": 0,
             "kept": 0, "dropped_multi_day_list": 0}

    for sentence in re.split(r"[。\n]", segment):
        if "三传" not in sentence:
            continue
        stats["sentences"] += 1
        tm = TRIPLE_RE.search(sentence)
        if not tm:
            continue
        stats["has_triple"] += 1
        expected = list(tm.groups())

        # 多日并列「乙丑、乙巳二日」：逐日各成一例
        days = DAY_RE.findall(sentence)
        if not days:
            continue
        stats["has_day"] += 1

        # 天地盘定位语（优先 加法，其次 干上，再次 支上）
        delta = None
        how = ""
        jm = JIA_RE.search(sentence)
        gs = GANSHANG_RE.search(sentence)
        zs = ZHISHANG_RE.search(sentence)
        if len(days) == 1:
            stem, branch = days[0]
            if jm:
                delta = (BR_IDX[jm.group(1)] - BR_IDX[jm.group(2)]) % 12
                how = f"{jm.group(1)}加{jm.group(2)}"
            elif gs:
                delta = (BR_IDX[gs.group(1)] - BR_IDX[JI_GONG[stem]]) % 12
                how = f"干上{gs.group(1)}"
            elif zs:
                delta = (BR_IDX[zs.group(1)] - BR_IDX[branch]) % 12
                how = f"支上{zs.group(1)}"
            if delta is None:
                continue
            stats["has_determiner"] += 1
            day_list = [(stem, branch)]
        else:
            # 多日并列：须有「X加Y」定位（与日干支无关的天地盘全局量）
            if not jm:
                stats["dropped_multi_day_list"] += 1
                continue
            delta = (BR_IDX[jm.group(1)] - BR_IDX[jm.group(2)]) % 12
            how = f"{jm.group(1)}加{jm.group(2)}"
            stats["has_determiner"] += 1
            day_list = days

        # 书明写门类（「X日遥克」「课名伏吟」等）→ expected_men 锚
        expected_men = None
        for men_word in ("遥克", "伏吟", "返吟", "昴星", "别责", "八专", "涉害"):
            if men_word in sentence:
                expected_men = men_word
                break

        for stem, branch in day_list:
            quote = sentence.strip()
            key = (stem + branch, delta, tuple(expected))
            if key in seen_quotes:
                continue
            seen_quotes.add(key)
            cases.append({
                "id": f"LE{len(cases) + 1:03d}",
                "book": "六壬大全",
                "location": "六壬大全（内嵌课例）",
                "source_quote": quote[:160],
                "day_ganzhi": stem + branch,
                "delta": delta,
                "determiner": how,
                "expected": {"san_chuan": expected},
                "expected_men": expected_men,
            })
            stats["kept"] += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "schema": "yi-liuren-course-examples/1",
        "_comment": [
            "书源内嵌课例（六壬大全 卷一课经/格局段），expected 只有书上明写的三传。",
            "重建方式：定位语（X加Y/干上X/支上X）→ 天地盘旋转 delta → 九宗门复算。",
            "本集度量是**机械一致率**（引擎三传 vs 书面三传），不是对齐分，",
            "更不是现实预测命中率（NEW-DISCIPLINES §2.1：两类分数必须分开报）。",
        ],
        "stats": stats,
        "cases": cases,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"抽取统计：{stats}")
    for c in cases:
        print(f"  {c['id']} {c['day_ganzhi']} δ={c['delta']}（{c['determiner']}）"
              f" 三传={''.join(c['expected']['san_chuan'])} | {c['source_quote'][:46]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
