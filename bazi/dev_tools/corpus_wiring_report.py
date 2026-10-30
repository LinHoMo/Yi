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
  F 判据未实现         —— 书证在库、引擎无对应判据 ⇒ 论说句无处可引。**这是真欠账**，逐容器登记理由。
  G 按题意取用         —— 象层／取象语料按 SKILL.md 意图路由取用，不常驻默认正文（正确不引）。
  D **未归类**         —— 既在可达盘内、又像正文的漏网条目：**这一类必须点名**，它是真缺陷的候选。
      （372 批把原 D 的 68 条逐容器定性后分入 F／G／B 三桶，见下方 CLASS_F／CLASS_G 表。）

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

# ── D 类 68 条的逐容器定性（372 批）────────────────────────────────────
# 为什么单列这两桶：D 此前是「68 条未归类，缺陷候选」，可它混着两种完全不同的东西——
# 一种是**引擎真的缺判据**（书证在库、无处可引），一种是**按题意取用**（象层只在问到
# 对应话题时引用，不常驻默认正文）。混在一起，前者（真欠账）就被后者的数量淹没了。
# 本表**只做归类，不改判定**：判定仍是「0 命中即红」；下面两桶都是「不引用是正确的」。
CLASS_F = {   # 判据论述在库、引擎无对应判据 ⇒ 论说句无处可引（**真欠账，已登记**）
    ("ditian_sui.json", "chapters›體用論"):
        "论「日主为体、用神为用」的方法论层；引擎以「用神／格局」表达体用，未单列体用判据，"
        "故其论说句不逐条引用。",
    ("ditian_sui.json", "chapters›寒暖論"):
        "与调候同旨而表述不同（寒暖 vs 调候表）；引擎走 `TIAO_HOU` 查表，不逐句引用寒暖论述。",
}
CLASS_B = {   # 方法论登记：_meta 自述「不是判据、不进任何评分」，只供逐字回指
    ("verdicts.json", "看命口诀"):
        "《三命通会》看命总纲方法论引文，_meta 明写「不是判据、不进任何评分」，只作 narrate 与文档的逐字回指",
}
CLASS_G = {   # 按 SKILL.md 意图路由取用：问到对应话题才引用，不常驻默认正文
    ("ditian_sui.json", "chapters›歲運論"):
        "**373 批已实现**：运岁五式（運伐歲／歲伐運／和〔干五合〕／好〔干同类〕）已落进 "
        "`dayun_liunian_interactions`，书证逐字挂各 relation 的 `basis`（源L365/370/382/387）。"
        "论说句仍不进报告，是因为**正文只印结构名、不印 basis**（与 363 批 `dayun_cheng_bai` 同）——"
        "属渲染取舍，不是判据缺失。（372 批曾按「判据未实现」登记，本批据实移出 F。）",

    "xiang_layer.json": "象层（宫位／脏腑／六亲）：SKILL.md 意图路由决定是否取用，不常驻正文",
    "liushen_image.json": "十神取象：随题意取用（问六亲／性格时才引）",
    "shi_shen_actions.json": "十神作用：随题意取用",
}
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
    eo = json.loads((ROOT / "data" / "cache" / "eval_all.json").read_text(encoding="utf-8"))
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
    tot = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0, "G": 0}
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
            _top1 = top.split("›")[0]     # 容器可能到二级（看命口诀›月令为命），表按一/二级都可登记
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
            if (f.name, top) in CLASS_B or (f.name, _top1) in CLASS_B:
                tot["B"] += 1        # 方法论登记（_meta 自述不进评分）
                continue
            if (f.name, top) in CLASS_F:
                tot["F"] += 1        # 判据在库、引擎无判据 ⇒ 真欠账（已登记）
                continue
            if (f.name in CLASS_G or (f.name, top) in CLASS_G
                    or (f.name, _top1) in CLASS_G):
                tot["G"] += 1        # 按题意取用，不常驻正文
                continue
                continue
            tot["D"] += 1
            unk.append(f"{f.name}〔{top or '?'}〕{s[:60]}")
            conts[top] = (hit_by_cont.get(top, 0), sum(1 for x, _ in leaves if x == top))
    print(f"接线残差归类：A 键不可达（盘外，正确）{tot['A']} ｜ B 元数据/自述串 {tot['B']} ｜ "
          f"C 键名/模板串 {tot['C']} ｜ E 容器未触发（盘外，正确）{tot['E']} ｜ "
          f"F 判据未实现（真欠账）{tot['F']} ｜ G 按题意取用（正确不常驻）{tot['G']} ｜ D 未归类 {tot['D']}")
    for (fn, cn), why in CLASS_F.items():
        print(f"  F· {fn}〔{cn}〕{why[:110]}")
    print(f"可达键：调候 {len(tiao_reach)}/120 格、纳音 {len(nayin_reach)}/60 支")
    for u in unk[:12]:
        print("  D·", u)
    if not tot["D"]:
        print(f"√ D 未归类 0 条——残差已全部逐容器定性：F {tot['F']}（判据未实现，真欠账）／"
              f"G {tot['G']}（按题意取用，正确不常驻）／B 方法论登记（并入 B {tot['B']}）")
    if tot["D"]:
        print(f"提示：D 类 {tot['D']} 条**未归类**（既在可达键内、又不像元数据）——是缺陷候选而非定论，"
          "须逐条点名定性后才决定是否入门判红；本器不静默改分母，也不把 D 当通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
