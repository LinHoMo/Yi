#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语料接线残差的**归类器**：把 `[8]` 报出的「未进并集」逐条分成四类，防止一个悲观计数被当成结论。

分法（能机械判的绝不猜）：
  A 键不可达（盘外）  —— 该条语的**索引键在 276 盘里根本不出现**，报告不引它是正确的：
      · `tiaohou_quotes.json` 键 =「月序+日干」（12×10=120 格），一盘只占 1 格；
      · `nayin_quxiang.json` 键 = 六十甲子，一盘四柱只占 4 支。
  B 元数据/自述串      —— 路径、行号、`OPT-*` 编号、给工程师看的按语（含「本表」「条目为」「data/sources」等），
      设计上就不进报告。
  C 键名/模板串        —— 形如 `X为先Y次之`、`专用X(season)`、`论乙·正月` 的键名或占位模板，不是正文。
  D **未归类**         —— 既在可达盘内、又像正文的漏网条目：**这一类必须点名**，它是真缺陷的候选。

本器**不替换** `[8]` 的判定（0 命中即红、豁免表过期即红都留在原处），只补「计数看不懂」这一段。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dev_tools"))
STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
ORDER = {b: i + 1 for i, b in enumerate(BRANCHES)}
META = re.compile(r"data/sources|\.dz\.txt|\.wikitext|OPT-|AGENTS\.md|铁律|本表|本字典|条目为|以下|未引用章|"
                 r"口径|说明|示例|理由|登记|舊題|维基文库|劉基|刘伯温|任铁樵|注本|机械切块|offset|提取")
BOOKHEAD = re.compile(r"^《.{2,12}》")     # 书题／章题行（如《滴天髓》…·天干論）：是出处标注，不是正文
TPL = re.compile(r"^X|^论.|[（(]season[)]]|^[A-Z]{1,2}[为两先]")


def walk(node, path=(), out=None):
    """→ [(容器路径=前两级键, 叶子串)]

    记到**第二级**是这套归类的关键：`ditian_sui.json` 顶层只有 `chapters`，
    真正决定「报告会不会引它」的是章名（天干論／從化論－真…）。只记顶层会把整本书
    当成一个容器，既看不出「章未触发」也看不出「章内漏引」。
    """
    out = [] if out is None else out
    if isinstance(node, str):
        cont = "›".join(path[:2])
        if "别称" in path:                      # 旁支字段：narrate 按主「性质名」取，别称另存出处
            cont += "›别称"                     # （实测 60 支里唯 己丑 有：L262「己丑为天将之火」）
        out.append((cont, node))
    elif isinstance(node, dict):
        for k, v in node.items():
            walk(v, path + (k,), out)
    elif isinstance(node, list):
        for v in node:
            walk(v, path, out)
    return out


def reachable():
    """276 盘里可达的索引键集合：调候（月序+日干）与纳音（六十甲子）。"""
    eo = json.loads((ROOT / "data" / "cases" / "eval_all.json").read_text(encoding="utf-8"))
    tiao, nayin = set(), set()
    for charts in (eo.get("engine_output") or {}).values():
        for ch in charts or []:
            p = ch.get("pillars") or {}
            day = ((p.get("day") or {}).get("stem") or "")
            mb = ((p.get("month") or {}).get("branch") or "")
            if day and mb in ORDER:
                tiao.add(f"{ORDER[mb]}{day}")
            for key in ("year", "month", "day", "hour"):
                gz = (p.get(key) or {}).get("ganzhi") or ""
                if len(gz) == 2:
                    nayin.add(gz)
    return tiao, nayin


def main() -> int:
    big = ROOT / "scratch" / "corpus_reports.txt"
    if not big.exists():
        print("FAIL：先跑 dev_tools/corpus_reports.py 生成多盘并集")
        return 1
    text = big.read_text(encoding="utf-8")
    tiao_reach, nayin_reach = reachable()
    tot = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    unk: list[str] = []
    conts: dict[str, tuple[int, int]] = {}
    for f in sorted((ROOT / "data").glob("*.json")):
        obj = json.loads(f.read_text(encoding="utf-8"))
        leaves = [(k, s) for k, s in walk(obj) if len(s) >= 4]
        hit_by_cont: dict[str, int] = {}
        for top, s in leaves:
            if s in text or s.lstrip("，、。；：") in text:
                hit_by_cont[top] = hit_by_cont.get(top, 0) + 1
        for top, s in leaves:
            if s in text or s.lstrip("，、。；：") in text:
                continue
            if f.name == "tiaohou_quotes.json" and top not in tiao_reach:
                tot["A"] += 1
                continue
            if f.name == "nayin_quxiang.json" and top not in nayin_reach:
                tot["A"] += 1
                continue
            if META.search(s) or (BOOKHEAD.search(s) and "·" in s):
                tot["B"] += 1
                continue
            if TPL.search(s) or s in (obj if isinstance(obj, dict) else {}):
                tot["C"] += 1
                continue
            if not hit_by_cont.get(top):
                tot["E"] += 1        # 同容器**一条都没被引** ⇒ 该容器在 276 盘里从未触发（盘外，正确不引）
                continue
            tot["D"] += 1
            unk.append(f"{f.name}〔{top or '?'}〕{s[:60]}")
            conts[top] = (hit_by_cont.get(top, 0), sum(1 for x, _ in leaves if x == top))
    print(f"接线残差归类：A 键不可达（盘外，正确）{tot['A']} ｜ B 元数据/自述串 {tot['B']} ｜ "
          f"C 键名/模板串 {tot['C']} ｜ E 容器未触发（盘外，正确）{tot['E']} ｜ D 未归类 {tot['D']}")
    print(f"可达键：调候 {len(tiao_reach)}/120 格、纳音 {len(nayin_reach)}/60 支")
    for u in unk[:12]:
        print("  D·", u)
    if tot["D"]:
        print(f"提示：D 类 {tot['D']} 条**未归类**（既在可达键内、又不像元数据）——是缺陷候选而非定论，"
          "须逐条点名定性后才决定是否入门判红；本器不静默改分母，也不把 D 当通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
