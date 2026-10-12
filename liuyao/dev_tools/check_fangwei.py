#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""方位层（#23）的门禁：规则必须还出书自己下的那两个结论，否则判红。

检三件事：
  ① 书据逐字在底本该行（不许挂着行号却与原文相反——本仓已犯过此错）；
  ② 规则对 WSD021…不，对 **WSD014**（巳月丙戌日占通乡避乱，乾之大有，五爻动）
     必须独立还出书的断语「午火得令而生世，往南避之为吉」⇒ 吉方只能是 **南**（唯一）；
     且「子孙属水…北方」作为候选出现但被判衰（书正是以旺衰分别否掉的）；
  ③ 延医三档还出源L3412 自带的两个例子：午火子孙旺→**南**；应爻临申金→**西南**。
`--selftest` 做负例：改坏方位表／旺衰序／引文，三处必须各自被抓。
"""
from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import fangwei_rules as F  # noqa: E402

SRC = ROOT / "data" / "sources" / "zengshan_buyi_dz.dz.txt"
QUOTE_A = "所以生方为吉，子孙之方亦吉，又当以旺衰分别"
QUOTE_B1 = "午火子孙或旺或动，请南方之医"
QUOTE_B2 = "应爻临申金，延医必在西南"
QUOTE_B3 = "且如占妻病，妻爻属水，得申金发动以相生，请钱姓之医以治之"
QUOTE_C = "占药占医又以子孙为用神"
# 同段两读（书内并列，不代书择一）：第三档「生用神」之"用神"——
#   源L3411 逐字「占药占医又以子孙为用神」（医药用神）
#   源L3412 例三逐字「占妻病，妻爻属水，得申金发动以相生」（病者用神）
# 本仓取 `_step2_data.selected_use_god`（单一真值源）为「生」之标的，并在 yan_yi_note 里外露实际所取之支。
DIVERGENCE_NOTE = ("第三档「生用神」在同段有两读（源L3411 医药用神＝子孙／源L3412 例三病者用神＝妻爻），"
                   "本仓不代书择一，用神一律取 step2.selected_use_god 并外露于 yan_yi_note")
DROP = set("，。！？；：、（）()「」『』“”\"…·—-《》【】　 \t\r\n")


def norm(s: str) -> str:
    return "".join(c for c in s if c not in DROP)


def lines() -> list[str]:
    return SRC.read_text(encoding="utf-8", errors="replace").splitlines()


def quotes_ok(problems: list[str]) -> int:
    ls = lines()
    n = 0
    for ln, q in ((2532, QUOTE_A), (3412, QUOTE_B1), (3412, QUOTE_B2),
                  (3412, QUOTE_B3), (3411, QUOTE_C)):
        if norm(q) not in norm(ls[ln - 1]):
            problems.append(f"源L{ln}：引文与底本该行不符 → {q[:28]}")
        else:
            n += 1
    return n


def cases(problems: list[str]) -> dict:
    # WSD014：乾宫（金）六世，世在上爻壬戌土；巳月丙戌日，五爻壬申金动
    yao = [{"branch": "子", "six_relation": "子孙"}, {"branch": "寅", "six_relation": "妻财"},
           {"branch": "辰", "six_relation": "父母"}, {"branch": "午", "six_relation": "官鬼"},
           {"branch": "申", "six_relation": "兄弟", "moving": True},
           {"branch": "戌", "six_relation": "父母"}]
    a = F.bi_luan_fang(shi_branch="戌", yao=yao, month_branch="巳")
    if a["ji_fang"] != ["南"]:
        problems.append(f"WSD014：吉方应为 ['南']（书「往南避之为吉」），实得 {a['ji_fang']}")
    if not any(c["direction"] == "北" for c in a["candidates"]):
        problems.append("WSD014：子孙之方（北）应作候选出现（书先举之而后以旺衰否）")
    if a["level"] != "旺":
        problems.append(f"WSD014：择方档应为『旺』，实得 {a['level']!r}")

    # 延医例一：午火子孙旺 → 南方
    b1 = F.yan_yi_fang([{"branch": "午", "six_relation": "子孙"}], "子", "巳")
    if [x["direction"] for x in b1["fang"]] != ["南"]:
        problems.append(f"源L3412 例一：应为 ['南']，实得 {[x['direction'] for x in b1['fang']]}")
    # 延医例二：子孙（子水）在巳月为囚 → 取应爻申金之方 = 西南
    b2 = F.yan_yi_fang([{"branch": "子", "six_relation": "子孙"}], "申", "巳")
    if [(x["档"], x["direction"]) for x in b2["fang"]] != [("应爻之方", "西南")]:
        problems.append(f"源L3412 例二：应为 [('应爻之方', '西南')]，实得 "
                        f"{[(x['档'], x['direction']) for x in b2['fang']]}")
    # 延医第三档（独发而生用神者）：书在同条自带实例——
    # 源L3412 逐字「且如占妻病，妻爻属水，得申金发动以相生，请钱姓之医以治之」
    if F.du_fa_sheng_yong("申", "子") is not True:
        problems.append("源L3412 例三：申金发动生妻爻（水）应判『生用神』，实得 False")
    if F.direction_of("申") != "西南":
        problems.append("源L3412 例三：独发申金之方应为西南（与「应爻临申金，延医必在西南」同表）")
    if F.du_fa_sheng_yong("申", "寅") is not False:
        problems.append("负例：申金不生于木，寅（水生木）却被判为生用神")
    for br, d in (("申", "西南"), ("午", "南"), ("子", "北")):
        if F.direction_of(br) != d:
            problems.append(f"方位表：{br} 应为 {d}（书自用），实得 {F.direction_of(br)!r}")
    return {"bi_luan": a, "yan_yi_1": b1, "yan_yi_2": b2}


def selftest() -> None:
    d, lv, qa = dict(F.BRANCH_DIR), list(F.LEVEL_ORDER), QUOTE_A
    try:
        F.BRANCH_DIR["申"] = "东"
        p: list[str] = []
        cases(p)
        assert any("西南" in x for x in p), f"方位表改坏未被抓：{p}"

        F.BRANCH_DIR["申"] = "西南"
        F.LEVEL_ORDER[:] = list(reversed(lv))   # 旺衰序翻面 ⇒ 择方必错
        p = []
        cases(p)
        assert any("WSD014" in x for x in p), f"旺衰序改坏未被抓：{p}"
    finally:
        F.BRANCH_DIR.clear()
        F.BRANCH_DIR.update(d)
        F.LEVEL_ORDER[:] = lv
    try:
        globals()["QUOTE_A"] = QUOTE_A[:10] + "绝无此语"
        p = []
        n = quotes_ok(p)
        assert p and n == 4, f"假引文未被抓：{p}"
    finally:
        globals()["QUOTE_A"] = qa
    try:
        F.SHENG["金"] = "木"                      # 让申金"生"木 ⇒ 第三档前件必然错判
        p2: list[str] = []
        cases(p2)
        assert any("负例" in x or "例三" in x for x in p2), f"五行生关系被改坏未被抓：{p2}"
    finally:
        F.SHENG["金"] = "水"
    print("SELFTEST OK：四式负例（方位表／旺衰序／假引文／五行生关系）全部被抓")


def main() -> int:
    if "--selftest" in sys.argv:
        selftest()
        return 0
    problems: list[str] = []
    if not SRC.exists():
        print(f"FAIL：底本不存在 {SRC.name}")
        return 1
    nq = quotes_ok(problems)
    got = cases(problems)
    print(f"方位层门禁：书据逐字 {nq}/5；WSD014 吉方 {got['bi_luan']['ji_fang']}"
          f"（档 {got['bi_luan']['level']}），候选 {len(got['bi_luan']['candidates'])} 方；"
          f"延医档 {[(x['档'], x['direction']) for x in got['yan_yi_2']['fang']]}")
    print(f"NOTE  {DIVERGENCE_NOTE}")
    if problems:
        print(f"FAIL：{len(problems)} 项")
        for x in problems:
            print("  " + x)
        return 1
    print("校验不过项: 无（书据逐字＋方位表＋避乱择方＋延医三档 全部还出书之断语）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
