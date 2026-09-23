# -*- coding: utf-8 -*-
"""六爻纳甲引擎：数据表 / 干支历与真太阳时 / 排盘核心 / 文本输出 / 历史遗留梅花与批量接口。（拆分自 liuyao_engine.py，纯搬移不改逻辑；聚合入口见 liuyao_engine.py）。"""

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel, kernel_dir

_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    ADVANCE_PAIRS,
    BRANCH_ELEMENTS,
    BREAK_PAIRS,
    CHONG_PAIRS,
    EARTHLY_BRANCHES,
    EIGHT_PALACES,
    BAGUA_LINES,
    HEAVENLY_STEMS,
    HEXAGRAM_TRIGRAMS,
    HE_PAIRS,
    KE_CYCLE,
    NAJIA_BRANCHES,
    RETREAT_PAIRS,
    SHENG_CYCLE,
    STEM_ELEMENTS,
    TOMB_MAP,
)

from yishu_core.najia import najia_branch  # noqa: E402

from yishu_core.hexagram_texts import HEXAGRAMS, HEXAGRAM_LINE_TEXTS  # noqa: E402  卦辞爻辞唯一真值源（AGENTS.md §二）

import argparse

import json

import math

import os

import random

import sys

from datetime import datetime, timedelta

from pathlib import Path

from yishu_core.runtime import force_utf8_stdio as _force_utf8_stdio  # noqa: E402


BAGUA = {
    "乾": {"lines": [1, 1, 1], "nature": "yang", "element": "金", "symbol": "☰"},
    "坤": {"lines": [0, 0, 0], "nature": "yin",  "element": "土", "symbol": "☷"},
    "震": {"lines": [0, 0, 1], "nature": "yang", "element": "木", "symbol": "☳"},
    "巽": {"lines": [1, 1, 0], "nature": "yin",  "element": "木", "symbol": "☴"},
    "坎": {"lines": [0, 1, 0], "nature": "yang", "element": "水", "symbol": "☵"},
    "离": {"lines": [1, 0, 1], "nature": "yin",  "element": "火", "symbol": "☲"},
    "艮": {"lines": [1, 0, 0], "nature": "yang", "element": "土", "symbol": "☶"},
    "兑": {"lines": [0, 1, 1], "nature": "yin",  "element": "金", "symbol": "☱"},
}

for _n, _lines in BAGUA_LINES.items():
    BAGUA[_n]["lines"] = _lines      # 爻序唯一真值源在内核，且自下而上


def _build_trigram_lookup():
    lookup = {}
    for name, info in BAGUA.items():
        key = tuple(info["lines"])
        lookup[key] = name
    return lookup


TRIGRAM_LOOKUP = _build_trigram_lookup()


BRANCH_NUMBERS = {
    "子": 1, "丑": 2, "寅": 3, "卯": 4, "辰": 5, "巳": 6,
    "午": 7, "未": 8, "申": 9, "酉": 10, "戌": 11, "亥": 12
}


NAJIA_STEMS = {
    "乾": {"inner": "甲", "outer": "壬", "nature": "yang"},
    "坤": {"inner": "乙", "outer": "癸", "nature": "yin"},
    "震": {"inner": "庚", "outer": "庚", "nature": "yang"},
    "坎": {"inner": "戊", "outer": "戊", "nature": "yang"},
    "艮": {"inner": "丙", "outer": "丙", "nature": "yang"},
    "巽": {"inner": "辛", "outer": "辛", "nature": "yin"},
    "离": {"inner": "己", "outer": "己", "nature": "yin"},
    "兑": {"inner": "丁", "outer": "丁", "nature": "yin"},
}


def _build_hexagram_lookup():
    lookup = {}
    for seq, name, upper, lower, judgment in HEXAGRAMS:
        key = (upper, lower)
        lookup[key] = (seq, name, judgment)
    return lookup


HEXAGRAM_LOOKUP = _build_hexagram_lookup()


def _build_palace_lookup():
    lookup = {}
    for palace_name, palace_data in EIGHT_PALACES.items():
        for hex_name, generation in palace_data["order"]:
            lookup[hex_name] = (palace_name, generation)
    return lookup


PALACE_LOOKUP = _build_palace_lookup()


WORLD_POSITION = {
    "六世": 6,
    "五世": 5,
    "四世": 4,
    "三世": 3,
    "二世": 2,
    "一世": 1,
    "游魂": 4,
    "归魂": 3,
}


RESPONSE_POSITION = {
    1: 4,
    2: 5,
    3: 6,
    4: 1,
    5: 2,
    6: 3,
}


SIX_SPIRITS = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]


DAY_STEM_SPIRIT_START = {
    "甲": 0,  # 青龙起初爻
    "乙": 0,  # 青龙起初爻
    "丙": 1,  # 朱雀起初爻
    "丁": 1,  # 朱雀起初爻
    "戊": 2,  # 勾陈起初爻
    "己": 3,  # 螣蛇起初爻
    "庚": 4,  # 白虎起初爻
    "辛": 4,  # 白虎起初爻
    "壬": 5,  # 玄武起初爻
    "癸": 5,  # 玄武起初爻
}


EMPTY_DEATH = {
    "甲子": ["戌", "亥"],
    "甲戌": ["申", "酉"],
    "甲申": ["午", "未"],
    "甲午": ["辰", "巳"],
    "甲辰": ["寅", "卯"],
    "甲寅": ["子", "丑"],
}

