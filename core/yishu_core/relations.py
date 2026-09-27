# -*- coding: utf-8 -*-
"""关系内核（Relations）—— 五行生克关系的两种命名：卜科「六亲」与命科「十神」。

YI-PLAN §二 架构图注明「命科与卜科是同一张表的两侧」，本模块就是那张表。
六爻的六亲（父母/兄弟/子孙/妻财/官鬼）与八字的十神（比肩/劫财/食神/伤官/
偏财/正财/七杀/正官/偏印/正印），都是「以我为准、看对方五行对我是生是克是同」
推出来的。区别只有一个：**六亲只看五行生克（5 类），十神在此基础上再分阴阳（10 类）**。

把两者建在同一份生克原语上，合参才有技术前提：当六爻说「妻财爻旺」、
八字说「正财得力」，二者指向的是同一条关系（我克＝财），可以被对齐、互证或据以裁决。
消费方：命科（十神）、卜科（六亲）、合参层（跨科对齐）。

真值源纪律：五行生克取自 symbols.py，本模块不另抄一份；此处只加两科共用的
「关系 → 命名」映射。卜科既有实现 `classical_analysis.determine_six_relation()`
与本模块 `six_relation()` 逐条一致（同一五行判据），已由 `disciplines/ming` 的断言锁定。
"""
from __future__ import annotations

from .symbols import (
    HEAVENLY_STEMS,
    EARTHLY_BRANCHES,
    STEM_ELEMENTS,
    BRANCH_ELEMENTS,
    SHENG_CYCLE,
    KE_CYCLE,
    SHENG_WO,
    KE_WO,
)

# ---------------------------------------------------------------- 阴阳
# 天干地支的阴阳是序位奇偶：甲(0)丙(2)…为阳，乙(1)丁(3)…为阴；子寅辰…为阳。
# 这是十神「同阴阳/异阴阳」分岔的唯一依据，core 此前没有，故在此立一份。
STEM_YINYANG = {s: ("阳" if i % 2 == 0 else "阴") for i, s in enumerate(HEAVENLY_STEMS)}
BRANCH_YINYANG = {b: ("阳" if i % 2 == 0 else "阴") for i, b in enumerate(EARTHLY_BRANCHES)}


def yinyang_of(symbol: str) -> str | None:
    """一个天干或地支的阴阳；非法字符返回 None。"""
    return STEM_YINYANG.get(symbol) or BRANCH_YINYANG.get(symbol)


def same_polarity(a: str, b: str) -> bool | None:
    """两个干支是否同阴阳；任一非法返回 None。"""
    pa, pb = yinyang_of(a), yinyang_of(b)
    if pa is None or pb is None:
        return None
    return pa == pb


# ---------------------------------------------------------------- 五行生克关系
# 「我」为基准，对方五行对我只有五种关系。这五类是六亲与十神共同的底层。
RELATION_SAME = "同我"
RELATION_SHENG_WO = "生我"
RELATION_WO_SHENG = "我生"
RELATION_KE_WO = "克我"
RELATION_WO_KE = "我克"


def element_of(symbol: str) -> str | None:
    """天干或地支 → 五行（取本气；地支藏干的十神另由 ming_tables 逐个藏干推）。"""
    return STEM_ELEMENTS.get(symbol) or BRANCH_ELEMENTS.get(symbol)


def wuxing_relation(me_wx: str, other_wx: str) -> str | None:
    """以 `me_wx` 为我，`other_wx` 对我的五行关系。非法五行返回 None。"""
    if me_wx not in SHENG_CYCLE or other_wx not in SHENG_CYCLE:
        return None
    if other_wx == me_wx:
        return RELATION_SAME
    if SHENG_WO.get(me_wx) == other_wx:      # 生我者
        return RELATION_SHENG_WO
    if SHENG_CYCLE.get(me_wx) == other_wx:   # 我生者
        return RELATION_WO_SHENG
    if KE_WO.get(me_wx) == other_wx:         # 克我者
        return RELATION_KE_WO
    if KE_CYCLE.get(me_wx) == other_wx:      # 我克者
        return RELATION_WO_KE
    return None


# ---------------------------------------------------------------- 六亲（卜科命名）
# 与 classical_analysis.determine_six_relation 同一判据：生我父母、同我兄弟、
# 我生子孙、克我官鬼、我克妻财。卜科以「卦宫五行」为我，此处以任意五行为我。
LIUQIN_OF_RELATION = {
    RELATION_SHENG_WO: "父母",
    RELATION_SAME: "兄弟",
    RELATION_WO_SHENG: "子孙",
    RELATION_KE_WO: "官鬼",
    RELATION_WO_KE: "妻财",
}
LIUQIN_NAMES = ["父母", "兄弟", "子孙", "妻财", "官鬼"]
# 卜科惯用序（六爻 classical/chain 层）；与 LIUQIN_NAMES 同集不同序
SIX_RELATIONS = ["父母", "官鬼", "子孙", "妻财", "兄弟"]


def six_relation(me_wx: str, other_wx: str) -> str | None:
    """五行关系 → 六亲名。等价于卜科按卦宫五行定六亲。"""
    rel = wuxing_relation(me_wx, other_wx)
    return LIUQIN_OF_RELATION.get(rel) if rel else None


# ---------------------------------------------------------------- 十神（命科命名）
# 在五行关系之上再分阴阳：同阴阳为「偏」，异阴阳为「正」（比劫食伤另有专名）。
# (关系, 是否同阴阳) → 十神名。
SHISHEN_TABLE = {
    (RELATION_SAME, True): "比肩",
    (RELATION_SAME, False): "劫财",
    (RELATION_WO_SHENG, True): "食神",
    (RELATION_WO_SHENG, False): "伤官",
    (RELATION_WO_KE, True): "偏财",
    (RELATION_WO_KE, False): "正财",
    (RELATION_KE_WO, True): "七杀",
    (RELATION_KE_WO, False): "正官",
    (RELATION_SHENG_WO, True): "偏印",
    (RELATION_SHENG_WO, False): "正印",
}
SHISHEN_NAMES = ["比肩", "劫财", "食神", "伤官", "偏财",
                 "正财", "七杀", "正官", "偏印", "正印"]
# 别名（同物异名，只作查表用，不参与判定）
SHISHEN_ALIAS = {"七杀": "偏官", "偏印": "枭神"}


def ten_god(day_stem: str, other_stem: str) -> str | None:
    """以日主天干 `day_stem` 为我，`other_stem`（天干）对我之十神。"""
    me_wx = STEM_ELEMENTS.get(day_stem)
    other_wx = STEM_ELEMENTS.get(other_stem)
    rel = wuxing_relation(me_wx, other_wx)
    if rel is None:
        return None
    pol = same_polarity(day_stem, other_stem)
    if pol is None:
        return None
    return SHISHEN_TABLE.get((rel, pol))


# ---------------------------------------------------------------- 十神 ↔ 六亲（合参对齐桥）
# 六亲是十神去掉阴阳后的「五行关系大类」。合参层据此把命科十神结论与卜科六亲结论
# 落到同一条关系上：正财/偏财 → 妻财，正官/七杀 → 官鬼，余类推。
SHISHEN_TO_LIUQIN = {
    "比肩": "兄弟", "劫财": "兄弟",
    "食神": "子孙", "伤官": "子孙",
    "偏财": "妻财", "正财": "妻财",
    "七杀": "官鬼", "正官": "官鬼",
    "偏印": "父母", "正印": "父母",
}
# 反向：一条六亲对应「同阴阳」「异阴阳」两个十神（顺序固定，供合参层展开）
LIUQIN_TO_SHISHEN = {
    "兄弟": ("比肩", "劫财"),
    "子孙": ("食神", "伤官"),
    "妻财": ("偏财", "正财"),
    "官鬼": ("七杀", "正官"),
    "父母": ("偏印", "正印"),
}


def shishen_to_liuqin(shishen: str) -> str | None:
    """十神 → 所属六亲大类；未知十神返回 None。"""
    return SHISHEN_TO_LIUQIN.get(shishen)


def liuqin_to_shishen(liuqin: str) -> tuple[str, str] | None:
    """六亲 → (同阴阳十神, 异阴阳十神)；未知六亲返回 None。"""
    return LIUQIN_TO_SHISHEN.get(liuqin)


def relation_class(me_wx: str, other_wx: str) -> dict | None:
    """一次性给出两五行之间的关系大类、六亲名、以及若加阴阳可得的两支十神。

    合参层用它把「卜科某六亲」与「命科某十神」判为同源，返回结构化对齐信息。
    """
    rel = wuxing_relation(me_wx, other_wx)
    if rel is None:
        return None
    liuqin = LIUQIN_OF_RELATION[rel]
    same, diff = LIUQIN_TO_SHISHEN[liuqin]
    return {"relation": rel, "liuqin": liuqin,
            "shishen_same_polarity": same, "shishen_diff_polarity": diff}
