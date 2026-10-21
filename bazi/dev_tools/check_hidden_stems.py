#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`hidden_stems` 维度的**独立出处**回验器（#14 第①项）。

EVAL-PLAN §五 步 6 记 `hidden_stems` 的 expected 键「打分代码齐备、缺独立于引擎的出处」；
AGENTS.md §三.4 禁止用引擎输出反推 expected ⇒ 只能去书里找**散文里写明的藏干**。
库书确实在论冲/论墓的段落里逐支写出所藏之干，例如：
  《滴天髓阐微》源L286「申中庚金，克寅中甲木，寅中丙火…申中壬水…寅中戊土」
  《滴天髓阐微》源L753「甲见申中壬水庚金、戊见寅中甲木丙火」
  《神峰通考》源L1819「辰中有乙木余气，壬癸之库墓，有戊己之正位」
本器把这些「支中干」逐字抽出来，与内核 `ming_tables.HIDDEN_STEMS` 对账：
  · **书有而表无** = 真缺陷（判红，须按书改表或登记分歧，不许改书就表）；
  · **表有而书未言** = 只记 NOTE（书散文本非全表，不构成反证）；
  · 逐字命中数与覆盖支数一并报出，**0 支可核即判红**（防本器空跑）。
`--selftest` 注入一条「寅中癸水」的假书据，必须被抓——否则「书有表无」这一半是空的。
"""
from __future__ import annotations

import io
import re
import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))
from yishu_core.ming_tables import CANG_GAN as HIDDEN_STEMS  # noqa: E402

BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
STEMS = "甲乙丙丁戊己庚辛壬癸"
# 「寅中甲木」「丑中辛金」「辰中有乙木余气」——限支后紧跟「中」再紧跟天干，避开「中水/中火」等五行字
PAT = re.compile(f"[{BRANCHES}]中[有]?([{STEMS}])")
CUE = re.compile("藏|本气|中气|余气|正位")
SRC_DIR = ROOT / "data" / "sources"


def extract(extra_lines=None):
    """抽「藏」字族的藏干陈述：支 + 中 + …藏 + 若干天干（可带五行后缀）。

    实测句形（第二次口径修正的依据，不是猜的）：
      《千里命稿》源L807「申中再藏戊土，午中再藏己土」——藏与支之间有「再」；
      源L810「寅中所藏丙火」；源L813「申中暗藏戊壬」——藏后可带**两个**干；
      源L825「申酉戌巳丑中皆藏金」——藏后是**五行字**不是天干，须排除（本器只认天干）。
    排除项（第一次口径的教训）：十二宫与气论句（「亥中丙戊俱絶」「丑中丁火无气」）
    与人元司令用事日数表（源L283「午中丙火用事七日」）——它们没有「藏」字，天然不入库。
    """
    found: dict[str, set[str]] = {}
    where: list[tuple[str, int, str]] = []
    after = re.compile(f"^藏[有]?((?:[{STEMS}][金木水火土]?){{1,4}})")
    linesets = [(f.name[:-9], io.open(f, encoding="utf-8", errors="replace").read().splitlines())
                for f in sorted(SRC_DIR.glob("*_dz.dz.txt"))]
    if extra_lines:
        linesets.append(("<自测注入>", extra_lines))
    for book, ls in linesets:
        for i, line in enumerate(ls, 1):
            for m in re.finditer("藏", line):
                pre = line[max(0, m.start() - 6):m.start()]
                # 宿主＝紧邻「藏」之前 ≤3 字内的**最近**一支；窗口内出现第二支即弃
                # （实测两类误判：《滴天髓阐微》源L7518「辰亥皆藏甲乙」两支共一藏，归属不定；
                #   《神峰通考》源L1971「癸亥巳藏丙戊」——亥是日柱、藏干主语是巳，取最近支才对）。
                pre = pre.rstrip("中内里")          # 「寅中藏」「亥内藏」——先剥方位字
                if not pre or pre[-1] not in BRANCHES:
                    continue
                if any(c in BRANCHES for c in pre[:-1]):
                    continue                      # 窗口内还有第二支 ⇒ 归属不定，弃
                b = pre[-1]
                ma = after.search(line[m.start():])
                if not ma:
                    continue
                for s in re.findall(f"[{STEMS}]", ma.group(1)):
                    found.setdefault(b, set()).add(s)
                    where.append((book, i, b + "中藏" + s))
    return found, where


def compare(found: dict, problems: list, notes: list) -> tuple[int, int, int]:
    """书表对账：返回（书给三元组数, 命中表数, 可核支数）。"""
    total = hit = 0
    for b in sorted(found):
        table = set(HIDDEN_STEMS.get(b) or [])
        if not table:
            problems.append(f"内核 HIDDEN_STEMS 缺地支 {b}")
            continue
        for s in sorted(found[b]):
            total += 1
            if s in table:
                hit += 1
            else:
                problems.append(f"书有而表无：{b} 中 {s}（表={sorted(table)}）——按书改表或登记分歧，不许就表改书")
        miss = sorted(table - found[b])
        if miss:
            notes.append(f"{b}：表有而散文未言 {miss}（散文非全表，不作反证）")
    return total, hit, len(found)


def main() -> int:
    problems: list[str] = []
    notes: list[str] = []
    _ap = argparse.ArgumentParser(description="check_hidden_stems：--selftest 负例自证开关（§三）")
    _ap.add_argument("--selftest", action="store_true", help="负例自证")
    args = _ap.parse_args()
    if args.selftest:
        fake = ["　　按古法，寅中藏癸水者，正气也（此句为本器自造的负例，底本无此文）"]
        f2, _ = extract(extra_lines=fake)
        p2: list[str] = []
        n2: list[str] = []
        compare(f2, p2, n2)
        if not any("寅 中 癸" in x for x in p2):
            print("FAIL SELFTEST：假书据「寅中癸水」未被抓——「书有表无」这一半是空的")
            return 1
        if not p2 or len([x for x in p2 if "书有而表无" in x]) < 1:
            print("FAIL SELFTEST：负例断言无明细计数")
            return 1
        print(f"SELFTEST OK：假书据被抓出并指名（{[x for x in p2 if '寅' in x][0][:34]}…）")
        return 0

    found, where = extract()
    total, hit, nbranch = compare(found, problems, notes)
    print(f"藏干独立出处：底本散文抽出「支中干」{total} 条（涉及 {nbranch}/12 支），"
          f"与内核 HIDDEN_STEMS 对账命中 {hit} 条；出处行 {len(where)} 处")
    for x in notes:
        print("NOTE  " + x)
    if nbranch < 4:
        problems.append(f"可核地支仅 {nbranch} 支（<4），本器近乎空跑，不得当作已验")
    if problems:
        print(f"FAIL：{len(problems)} 项")
        for x in problems:
            print("  " + x)
        return 1
    print("校验不过项: 无（书中所写藏干逐条见于内核表，无「书有表无」冲突）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
