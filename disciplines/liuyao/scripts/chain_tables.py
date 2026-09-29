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
    SHENG_WO,
    KE_WO,
    STEM_ELEMENTS,
    TOMB_MAP,
    TRIGRAM_ELEMENTS as _CORE_TRIGRAM_ELEMENTS,
    TWELVE_GROWTH as _CORE_TWELVE_GROWTH,
    TWELVE_GROWTH_STAGES as _CORE_TWELVE_GROWTH_STAGES,
    TWELVE_GROWTH_TABLES as _CORE_TWELVE_GROWTH_TABLES,
    XUN_KONG as _CORE_XUN_KONG,
    palace_of_key,
    EARTHLY_BRANCHES as BRANCHES,
)
from yishu_core.symbols import SAN_HE_GROUPS as _CORE_SAN_HE  # noqa: E402
from yishu_core.relations import SIX_RELATIONS  # noqa: E402

from datetime import datetime, timedelta

import json

import re

from pathlib import Path


STEMS = list(HEAVENLY_STEMS)


# 生我(SHENG_WO)/克我(KE_WO)唯一真值源在内核 yishu_core.symbols（AGENTS.md §二），此处仅引用。
# 历史债务：此前本文件与 classical_tables.py 各就地推导一份，连同内核共 3 份副本。


PALACE_GENERATING = dict(SHENG_WO)


PALACE_OVERCOMING = dict(KE_WO)


# 三合/十二长生/旬空：真值源在 core.yishu_core（AGENTS.md §二），此处仅别名。
SAN_HE = _CORE_SAN_HE  # core.symbols.SAN_HE_GROUPS 别名


TWELVE_GROWTH_TABLES = _CORE_TWELVE_GROWTH_TABLES


TWELVE_GROWTH_STAGES = _CORE_TWELVE_GROWTH_STAGES




RELATION_ELEMENT = {
    "兄弟": None,
    "子孙": None,
    "妻财": None,
    "官鬼": None,
    "父母": None,
}


JUE_MAP = {
    "木": "申",
    "火": "亥",
    "土": "亥",
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


TRIGRAM_ELEMENT = _CORE_TRIGRAM_ELEMENTS  # 卦五行唯一真值源在内核（AGENTS.md §二）


XUN_KONG = _CORE_XUN_KONG


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


TWELVE_GROWTH = _CORE_TWELVE_GROWTH


_TWELVE_GROWTH_SCORE = {
    "帝旺": 0.4, "临官": 0.3, "长生": 0.2,
    "衰": -0.2, "病": -0.2,
    "死": -0.4, "墓": -0.4,
    "绝": -0.6,
    "沐浴": 0.0, "冠带": 0.0, "胎": 0.0, "养": 0.0,
}


# 六冲对照：由 core.CHONG_PAIRS 派生，不另抄一份
_BRANCH_CLASHES = {a: b for a, b in CHONG_PAIRS}
_BRANCH_CLASHES.update({b: a for a, b in CHONG_PAIRS})


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

