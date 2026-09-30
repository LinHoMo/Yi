# -*- coding: utf-8 -*-
"""六壬补表（Liuren Tables）—— 大六壬起课所需的内核唯一真值源。

依 CONTRACT.md §二：学科需要的表加进内核、标注消费方，不开第二真值源。
唯一消费方：`disciplines/liuren`（大六壬）。

收录（起例出处均为 data/sources/liu-ren-da-quan.wikitext.txt 卷一「入手法」/「神煞」，
逐字引文留在学科层 data/verdicts.json，本模块只存结构）：
  ① 十干寄宫 JI_GONG（「甲课寅兮乙课辰」诀）
  ② 十二月将 YUE_JIANG：中气换将（太阳过宫）口径——月将 = 太阳躔次，
     雨水后亥将、春分后戌将……（「超神接气」之争以**中气换将**为第一版口径，
     经 `yuejiang_policy` 显式声明，不静默择一）
  ③ 十二天将 TIAN_JIANG_ORDER 及昼夜贵人 NOBLE_DAY/NOBLE_NIGHT、布法 tianjiang_layout
  ④ 日德 DAY_DE（卷一「十天干神煞」表：甲寅 乙申 丙巳 丁亥 戊巳 己寅 庚申 辛巳 壬亥 癸巳；
     原文第八位作「己」第十位作「已」，按通例校为「巳」并标 verified=False）
"""
from __future__ import annotations

from datetime import datetime

from yishu_core.ganzhi_calendar import EARTHLY_BRANCHES, solar_terms_of_year

# ---------------------------------------------------------------- 十干寄宫
# 「甲课寅兮乙课辰，丙戊课巳不须论。丁己课未庚申上，辛戌壬亥是其真。
#   癸课原来丑宫坐，分明不用四正神。」（六壬大全·入手法·十干寄宫）
JI_GONG: dict[str, str] = {
    "甲": "寅", "乙": "辰", "丙": "巳", "丁": "未", "戊": "巳",
    "己": "未", "庚": "申", "辛": "戌", "壬": "亥", "癸": "丑",
}

# ---------------------------------------------------------------- 十二月将
# 中气换将（太阳过宫）：节气值（节）内月将仍是上一中气之将，交中气后换次将。
ZHONGQI_YUEJIANG: dict[str, tuple[str, str]] = {
    # 中气:   (月将支, 将名)
    "雨水": ("亥", "登明"),
    "春分": ("戌", "河魁"),
    "谷雨": ("酉", "从魁"),
    "小满": ("申", "传送"),
    "夏至": ("未", "小吉"),
    "大暑": ("午", "胜光"),
    "处暑": ("巳", "太乙"),
    "秋分": ("辰", "天罡"),
    "霜降": ("卯", "太冲"),
    "小雪": ("寅", "功曹"),
    "冬至": ("丑", "大吉"),
    "大寒": ("子", "神后"),
}

YUEJIANG_POLICY = "zhongqi"   # 中气换将（太阳过宫）；超神/接气/置闰之争日后作显式开关


def yuejiang_of(dt: datetime) -> dict:
    """datetime → {"branch", "name", "zhongqi", "instant", "policy"}。

    在上一年与本年的中气表里找最近一次已过的中气（大寒跨年由此覆盖）。
    """
    candidates: list[dict] = []
    for year in (dt.year - 1, dt.year):
        for term in solar_terms_of_year(year):
            if term["name"] in ZHONGQI_YUEJIANG:
                candidates.append(term)
    passed = [t for t in candidates if t["instant"] <= dt]
    if not passed:
        raise ValueError(f"找不到已过中气：{dt}")
    last = max(passed, key=lambda t: t["instant"])
    branch, name = ZHONGQI_YUEJIANG[last["name"]]
    return {
        "branch": branch, "name": name, "zhongqi": last["name"],
        "instant": last["instant"].strftime("%Y-%m-%d %H:%M"),
        "policy": YUEJIANG_POLICY,
    }


# ---------------------------------------------------------------- 十二天将
TIAN_JIANG_ORDER: list[str] = [
    "贵人", "螣蛇", "朱雀", "六合", "勾陈", "青龙",
    "天空", "白虎", "太常", "玄武", "太阴", "天后",
]

# 昼夜贵人（歌诀「甲戊庚牛羊，乙己鼠猴乡，丙丁猪鸡位，壬癸兔蛇藏，六辛逢马虎」）
#   昼贵 = 诀第一位（牛/鼠/猪/兔/马），夜贵 = 第二位（羊/猴/鸡/蛇/虎）
NOBLE_DAY: dict[str, str] = {
    "甲": "丑", "戊": "丑", "庚": "丑",
    "乙": "子", "己": "子",
    "丙": "亥", "丁": "亥",
    "壬": "卯", "癸": "卯",
    "辛": "午",
}
NOBLE_NIGHT: dict[str, str] = {
    "甲": "未", "戊": "未", "庚": "未",
    "乙": "申", "己": "申",
    "丙": "酉", "丁": "酉",
    "壬": "巳", "癸": "巳",
    "辛": "寅",
}

# 昼夜分界：卯时起昼、酉时起夜（卯辰巳午未申为昼，酉戌亥子丑寅为夜）——
# 流派有寅时起昼一说，第一版固定卯酉分界并显式声明。
DAY_NIGHT_POLICY = "mao_you"


def is_day(hour_branch: str) -> bool:
    return hour_branch in ("卯", "辰", "巳", "午", "未", "申")


def noble_of(day_stem: str, hour_branch: str) -> dict:
    """日干×时辰 → {"noble": 支, "day_night": "昼"|"夜"}。"""
    day = is_day(hour_branch)
    return {
        "noble": NOBLE_DAY[day_stem] if day else NOBLE_NIGHT[day_stem],
        "day_night": "昼" if day else "夜",
    }


def tianjiang_layout(day_stem: str, hour_branch: str, tianpan: dict[str, str]) -> dict[str, str]:
    """十二天将布于十二地盘位：{地盘位: 将名}。

    贵人支落在天盘所临的地盘位；该地盘位在 亥~辰 一侧顺布、巳~戌 一侧逆布
    （贵人在天盘所临之地盘位定顺逆，通行口径）。
    """
    noble = noble_of(day_stem, hour_branch)
    nb = noble["noble"]
    noble_pos = next(p for p, sky in tianpan.items() if sky == nb)
    idx = EARTHLY_BRANCHES.index(noble_pos)
    forward = noble_pos in ("亥", "子", "丑", "寅", "卯", "辰")
    out: dict[str, str] = {}
    for i, jiang in enumerate(TIAN_JIANG_ORDER):
        pos = EARTHLY_BRANCHES[(idx + i) % 12] if forward \
            else EARTHLY_BRANCHES[(idx - i) % 12]
        out[pos] = jiang
    return out


# ---------------------------------------------------------------- 日德
# 卷一「十天干神煞」表：「日徳 寅申巳亥巳寅申己亥已」（甲乙丙丁戊己庚辛壬癸）；
# 第八位原文作「己」、第十位作「已」，均按通例校为「巳」——verified=False 登记。
DAY_DE: dict[str, str] = {
    "甲": "寅", "乙": "申", "丙": "巳", "丁": "亥", "戊": "巳",
    "己": "寅", "庚": "申", "辛": "巳", "壬": "亥", "癸": "巳",
}
DAY_DE_VERIFIED = False

# 干合（日德辨伪与合神关系用，甲己/乙庚/丙辛/丁壬/戊癸）
STEM_HE = {"甲": "己", "己": "甲", "乙": "庚", "庚": "乙",
           "丙": "辛", "辛": "丙", "丁": "壬", "壬": "丁", "戊": "癸", "癸": "戊"}
