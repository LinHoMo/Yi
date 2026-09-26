# -*- coding: utf-8 -*-
"""六爻思维链：基元表 / 断语库 / 通用辅助 / 五步推演 / 应期 / 叙事组装。（拆分自 thinking_chain.py，纯搬移不改逻辑；聚合入口见 thinking_chain.py）。"""

from __future__ import annotations

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
    HEAVENLY_STEMS,
    HEXAGRAM_TRIGRAMS,
    HE_PAIRS,
    KE_CYCLE,
    NAJIA_BRANCHES,
    RETREAT_PAIRS,
    SHENG_CYCLE,
    STEM_ELEMENTS,
    TOMB_MAP,
    palace_of_key,
    EARTHLY_BRANCHES as BRANCHES,
)

from datetime import datetime, timedelta

import json

import re

from pathlib import Path


STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]


SHENG_WO = {v: k for k, v in SHENG_CYCLE.items()}


KE_WO = {v: k for k, v in KE_CYCLE.items()}


PALACE_GENERATING = dict(SHENG_WO)  # {"木": "水", "火": "木", "土": "火", "金": "土", "水": "金"}


PALACE_OVERCOMING = dict(KE_WO)    # {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}


SAN_HE = {
    "水": ["申", "子", "辰"],
    "火": ["寅", "午", "戌"],
    "金": ["巳", "酉", "丑"],
    "木": ["亥", "卯", "未"],
}


TWELVE_GROWTH_TABLES = {
    "木": ["亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌"],
    "火": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
    "金": ["巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰"],
    "水": ["申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未"],
    "土": ["申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未"],
}


TWELVE_GROWTH_STAGES = [
    "长生", "沐浴", "冠带", "临官", "帝旺",
    "衰", "病", "死", "墓", "绝", "胎", "养",
]


SIX_RELATIONS = ["父母", "官鬼", "子孙", "妻财", "兄弟"]


RELATION_ELEMENT = {
    "兄弟": None,  # 同宫五行，后面特殊处理
    "子孙": None,  # 宫五行所生
    "妻财": None,  # 宫五行所克
    "官鬼": None,  # 克宫五行
    "父母": None,  # 生宫五行
}


JUE_MAP = {
    "木": "申",
    "火": "亥",
    "土": "亥",  # 土从水
    "金": "寅",
    "水": "巳",
}


SIX_SPIRITS = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]


SPIRIT_ELEMENT = {
    "青龙": "木",
    "朱雀": "火",
    "勾陈": "土",
    "螣蛇": "土",
    "白虎": "金",
    "玄武": "水",
}


TRIGRAM_ELEMENT = {
    "乾": "金", "兑": "金", "离": "火", "震": "木",
    "巽": "木", "坎": "水", "艮": "土", "坤": "土",
}


XUN_KONG = {
    "甲子": ["戌", "亥"], "甲戌": ["申", "酉"], "甲申": ["午", "未"],
    "甲午": ["辰", "巳"], "甲辰": ["寅", "卯"], "甲寅": ["子", "丑"],
}


HEXAGRAM_LIUHE = ["泰", "否", "贲", "困", "旅", "豫", "复", "小畜"]


# 小畜：巽宫一世，巽上乾下，上卦「巳丑酉·六合」，下卦「午卯子·六冲」。
# 《火珠林》以小畜为 六合+六冲 双卦 (本利见合而逢冲则散) — 象数同源表须两存。
# hex_adjustment 中 六合+0.5 与 六冲-0.5 相抵为 0，三刑+六合覆写 (chain_step5 §5.5i)
# 以「在 HEXAGRAM_LIUHE」判定，不依赖 hex_adjustment>0，确保叠加六冲后仍被覆写。
HEXAGRAM_LIUCHONG = ["乾", "坤", "坎", "离", "艮", "震", "巽", "兑",
                     "无妄", "大壮", "晋", "明夷", "蹇", "解", "夬", "姤",
                     "遁", "同人", "履", "小畜"]


_USE_GOD_DICT_PATH = Path(__file__).resolve().parents[1] / "data" / "rules" / "question_use_gods.json"


def _load_question_use_gods() -> tuple[dict, dict, dict]:
    """装载问题词典 data/rules/question_use_gods.json → (词典, 按键依据, 覆盖层引文)。

    词典本体已按事项族结构化进 data/（tools/build_question_use_gods.py 生成，
    每族带 label + 引文/推断依据）；这里只做装载与展平。装载失败直接抛错、不降级：
    词典缺了打分层会把一切静默判成世爻，那是"错得安静"——按铁律一宁可整个排盘
    报异常。entries 顺序即 JSON 顺序（同分 tie-break 依赖插入序），装载保持原序，
    与搬移前的字面量零漂移（键序与取值经快照对照 + 金标准 288 例核验）。
    """
    try:
        data = json.loads(_USE_GOD_DICT_PATH.read_text(encoding="utf-8"))
        word_map: dict = {}
        basis: dict = {}
        for fam in data["families"]:
            fb = dict(fam.get("basis") or {})
            fb["label"] = fam.get("label", "")
            if fam.get("note"):
                fb["note"] = fam["note"]
            for ent in fam["entries"]:
                word_map[ent["k"]] = ent["v"]
                basis[ent["k"]] = fb
        layers = data.get("layer_citations") or {}
        return word_map, basis, layers
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError(
            f"问题词典装载失败：{_USE_GOD_DICT_PATH}（{exc}）。"
            "缺词典时取用神会静默退化成一律世爻，按铁律一不降级、直接报排盘异常。"
        ) from exc


_QUESTION_USE_GOD_MAP, _QUESTION_USE_GOD_BASIS, _USE_GOD_LAYER_CITATIONS = _load_question_use_gods()


USE_GOD_RELATIONSHIPS = {
    "木": {"原神": "水", "忌神": "金", "仇神": "土"},
    "火": {"原神": "木", "忌神": "水", "仇神": "金"},
    "土": {"原神": "火", "忌神": "木", "仇神": "水"},
    "金": {"原神": "土", "忌神": "火", "仇神": "木"},
    "水": {"原神": "金", "忌神": "土", "仇神": "火"},
}


TWELVE_GROWTH = {
    "木": {"亥": "长生", "子": "沐浴", "丑": "冠带", "寅": "临官", "卯": "帝旺",
           "辰": "衰", "巳": "病", "午": "死", "未": "墓", "申": "绝", "酉": "胎", "戌": "养"},
    "火": {"寅": "长生", "卯": "沐浴", "辰": "冠带", "巳": "临官", "午": "帝旺",
           "未": "衰", "申": "病", "酉": "死", "戌": "墓", "亥": "绝", "子": "胎", "丑": "养"},
    "土": {"寅": "长生", "卯": "沐浴", "辰": "冠带", "巳": "临官", "午": "帝旺",
           "未": "衰", "申": "病", "酉": "死", "戌": "墓", "亥": "绝", "子": "胎", "丑": "养"},
    "金": {"巳": "长生", "午": "沐浴", "未": "冠带", "申": "临官", "酉": "帝旺",
           "戌": "衰", "亥": "病", "子": "死", "丑": "墓", "寅": "绝", "卯": "胎", "辰": "养"},
    "水": {"申": "长生", "酉": "沐浴", "戌": "冠带", "亥": "临官", "子": "帝旺",
           "丑": "衰", "寅": "病", "卯": "死", "辰": "墓", "巳": "绝", "午": "胎", "未": "养"},
}


_TWELVE_GROWTH_SCORE = {
    "帝旺": 0.4, "临官": 0.3, "长生": 0.2,
    "衰": -0.2, "病": -0.2,
    "死": -0.4, "墓": -0.4,
    "绝": -0.6,
    "沐浴": 0.0, "冠带": 0.0, "胎": 0.0, "养": 0.0,
}


_BRANCH_CLASHES = {
    "子": "午", "午": "子",
    "丑": "未", "未": "丑",
    "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰",
    "巳": "亥", "亥": "巳",
}


_HEXAGRAM_HARMONY_SET = set()


_SAN_HE_SET = set()


_BRANCH_CLASH_MAP = {}


_HE_MAP = {}


for _a, _b in HE_PAIRS:
    _HEXAGRAM_HARMONY_SET.add(f"{_a}{_b}")
    _HEXAGRAM_HARMONY_SET.add(f"{_b}{_a}")

for _elem, _branches in SAN_HE.items():
    for i in range(len(_branches)):
        for j in range(i + 1, len(_branches)):
            _SAN_HE_SET.add(f"{_branches[i]}{_branches[j]}|{_elem}")
            _SAN_HE_SET.add(f"{_branches[j]}{_branches[i]}|{_elem}")

for _a, _b in CHONG_PAIRS:
    _BRANCH_CLASH_MAP[_a] = _b
    _BRANCH_CLASH_MAP[_b] = _a

for _a, _b in HE_PAIRS:
    _HE_MAP.setdefault(_a, []).append(_b)
    _HE_MAP.setdefault(_b, []).append(_a)


_ELEMENT_PEAK_MONTHS = {
    "木": [2, 3],       # 寅卯月（春）
    "火": [5, 6],       # 巳午月（夏）
    "土": [4, 7, 10, 1],  # 辰戌丑未月（四季之末月）
    "金": [8, 9],       # 申酉月（秋）
    "水": [11, 12],     # 亥子月（冬）
}


_60_CYCLE_BASE = datetime(2024, 1, 1)


_HEX_NAMES = sorted((n for n in HEXAGRAM_TRIGRAMS if len(n) >= 2), key=len, reverse=True)


_CHART_TAIL = re.compile(r"[，,、]?\s*(?P<orig>[一-鿿]{1,4})[之變变](?P<chg>[一-鿿]{1,4})\s*$")

