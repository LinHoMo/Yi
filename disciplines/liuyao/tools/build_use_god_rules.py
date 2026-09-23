# -*- coding: utf-8 -*-
"""生成取用神的关系优先表；每条规则的引文必须在原文里逐字找得到。

    python tools/build_use_god_rules.py            # 生成 data/rules/use_god_relations.json
    python tools/build_use_god_rules.py --check    # 只校验引文是否仍在原文中

为什么不直接把这些词塞进 `chain_tables._QUESTION_USE_GOD_MAP`
（即 `data/rules/question_use_gods.json`，186 条现代问法词典）：
  那张表是"现代问法→六亲"的扁平映射，词典本身虽已按 64 个事项族标注取舍依据
  （有引文族/推断族），但族级依据是**整族一条引文**，不是逐词的"关系优先"判断。
  刚建成的外部集（`wikisource_holdout`）上，原文明写用神的 4 例引擎只对 1 例，错在三处：
  女家占婚取了妻财（该书婚姻章明写"女家占男，皆以官為用"）、占伯取了子孙、
  占夫取了世爻。扁平表缺的不是词，是**关系优先于事项**这一层，以及每条规则的出处。
  所以规则单列成本表，且**引文逐字对不上原文就不出表**——写错出处比没出处更坏。

引文取自 `data/sources/zengshan_buyi.wikitext.txt`（维基文库《增刪卜易》原本，
tools/fetch_wikisource_cases.py 拉取并记 sha256）。本工具只做"引文→偏移量"的定位。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
RAW = DISC.parent.parent / "data" / "sources" / "zengshan_buyi.wikitext.txt"
OUT = DISC / "data" / "rules" / "use_god_relations.json"

# (触发词, 需要的上下文词(可空), 用神, 优先级, 逐字引文)
# 顺序即优先级：命中即止，所以"关系+性别"要排在泛化的"婚→财"之前。
RULES = [
    # p10 婚姻：占者性别决定用神
    (["女家", "女方", "女占", "妻占", "代女"], ["婚", "嫁", "夫", "婿"], "官鬼", 10,
     "男家占女，不拘父母親朋而代占者，無不以財為用。女家占男，皆以官為用。"),
    (["男家", "男方", "男占", "夫占"], ["婚", "娶", "妻", "妾"], "妻财", 10,
     "男家占女，不拘父母親朋而代占者，無不以財為用。"),
    # p20 六亲关系人：取该六亲之爻（用神章总纲见"兄弟"那条引文）
    (["父", "母", "爹", "娘", "爺", "婆"], [], "父母", 20,
     "子占父病，父爻為用神"),
    (["伯", "叔", "舅", "姑", "婶", "姨", "长辈", "祖", "主人"], [], "父母", 20,
     "寅月亥日占主人何時回，以父母為用"),
    (["兄", "弟", "姐", "妹", "朋友", "同辈", "姊妹"], [], "兄弟", 20,
     "占父母弟兄取用神者皆在用神章內詳之"),
    (["儿子", "女儿", "子女", "孩子", "侄", "晚輩", "孙子", "孙女", "子孙"], [], "子孙", 20,
     "如占子孫，取子孫為用神"),
    (["夫", "婿"], [], "官鬼", 20,
     "妻占夫官為用神"),
    (["妻", "妾", "婢", "僕", "仆"], [], "妻财", 20,
     "男人自占妻者，亦以財爻為用神"),
    # p30 事项类
    (["医", "醫", "药", "藥"], [], "子孙", 30,
     "占藥占醫又以子孫為用神"),
    (["宅", "房", "屋", "楼盘", "房地"], [], "父母", 25,
     "父旺持世，此處淸安宜久住"),
    (["六畜", "牲口", "猪", "馬", "牛"], [], "子孙", 30,
     "凡占一切六畜，皆以子孫為用神"),
    # 单字"畜"必须留着不进来：它同时是"小畜/大畜"卦名的一部分，
    # "占投资经营，益之小畜"会被它抢成子孙（真答案妻财）。
    (["胎", "孕", "安胎", "坐月"], [], "子孙", 15,
     "卜胎之虛實，占孕之安危，問產婦之吉凶，測胎中之男女，各宜分占，親占代占，皆用子孫"),
    (["子占母孕", "代母占孕"], [], "兄弟", 10,
     "惟子占母孕，以弟兄爻為用神也"),
    (["自占病", "占自己病", "自病", "自身病", "我病"], [], "世爻", 15,
     "自占病，世為用神"),
    # p40 自占以世为用
    (["自占", "自身", "我", "吾"], ["病", "疾", "流年", "造化"], "世爻", 40,
     "自占病，世為用神"),
]


PUNCT = "，,﹐、；;：:.。．！!？?「」『』“”‘’()（）《》〈〉"


def strip_with_map(text: str) -> tuple[str, list[int]]:
    """去标点后的文本 + 每个字符在原串里的下标。

    刻本用 ﹐(U+FE10) 而不是 ，，按整串 find 会一律失配；但引文必须逐字可核，
    所以**匹配时忽略标点、落盘时回填原文片段**。
    """
    chars, idx = [], []
    for i, ch in enumerate(text):
        if ch in PUNCT or ch.isspace():
            continue
        chars.append(ch)
        idx.append(i)
    return "".join(chars), idx


def locate(text: str, quote: str) -> tuple[int, str]:
    """返回 (下标, 原文逐字片段)；找不到返回 (-1, "")。

    下标与片段都取自"去掉 <br> 之后"的同一份文本——两边口径必须一致，
    早先一处按去标签的下标定序、另一处回原串切片，结果引文全错位。
    """
    body = re.sub(r"<br>", "", text)
    flat_s, idx = strip_with_map(body)
    q, _ = strip_with_map(quote)
    q = q.translate(str.maketrans("为占归来财医药当会实际个于", "為占歸來財醫藥當會實際個於"))
    p = flat_s.find(q)
    if p < 0 or not q:
        return -1, ""
    return idx[p], body[idx[p]:idx[p + len(q) - 1] + 1]


def flat() -> str:
    return RAW.read_text(encoding="utf-8").translate(str.maketrans({"爲": "為"}))


def main() -> int:
    for module in (str(DISC / "scripts"), str(DISC.parents[1] / "core")):
        sys.path.insert(0, module)
    from yishu_core.runtime import force_utf8_stdio
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="生成取用神关系优先表（引文须逐字命中原文）")
    ap.add_argument("--check", action="store_true", help="只校验引文，不写文件")
    args = ap.parse_args()

    if not RAW.exists():
        print(f"缺原文缓存 {RAW}，先跑 tools/fetch_wikisource_cases.py")
        return 1
    text = flat()

    rows, missing = [], []
    for trig, ctx, god, prio, quote in RULES:
        off, verbatim = locate(text, quote)
        if off < 0:
            missing.append(quote)
            continue
        rows.append({"trigger": trig, "context": ctx, "use_god": god, "priority": prio,
                     "citation": re.sub(r"<br>|\s+", "", verbatim), "offset": off})

    print(f"引文核对：{len(rows)}/{len(RULES)} 条逐字命中原文")
    for q in missing:
        print(f"  × 原文找不到，已拒收：{q}")
    if missing:
        print("没有出处的规则不进表——请改引文或删该条。")
        return 1
    if args.check:
        return 0

    rows.sort(key=lambda r: (r["priority"], -max(len(t) for t in r["trigger"])))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "_meta": {
            "description": "取用神的『关系优先于事项』规则表，出自《增刪卜易》原文，"
                           "每条带逐字引文与偏移量",
            "built_by": "tools/build_use_god_rules.py",
            "source": str(RAW.relative_to(DISC.parent.parent)),
            "usage": "chain_step2 取用神时先过本表（先命中先停），未命中再依次过覆盖层与问题词典",
            "order": "priority 小的先判；同优先级里触发词长的先判（更具体）",
            "rule_count": len(rows),
        },
        "rules": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写入 {OUT.relative_to(DISC.parent.parent)}（{len(rows)} 条）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
