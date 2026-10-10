# -*- coding: utf-8 -*-
"""六爻思维链：基元表 / 断语库 / 通用辅助 / 五步推演 / 应期 / 叙事组装。聚合入口见 thinking_chain.py。"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    CHONG_PAIRS,
    HEAVENLY_STEMS,
    HEXAGRAM_TRIGRAMS,
    HE_PAIRS,
    SHENG_WO,
    KE_WO,
    TRIGRAM_ELEMENTS as _CORE_TRIGRAM_ELEMENTS,
    TWELVE_GROWTH as _CORE_TWELVE_GROWTH,
    TWELVE_GROWTH_STAGES as _CORE_TWELVE_GROWTH_STAGES,
    TWELVE_GROWTH_TABLES as _CORE_TWELVE_GROWTH_TABLES,
    XUN_KONG as _CORE_XUN_KONG,
)
from yishu_core.symbols import SAN_HE_GROUPS as _CORE_SAN_HE  # noqa: E402
from yishu_core.relations import SIX_RELATIONS  # noqa: E402

from datetime import datetime

import json

import re

from pathlib import Path


STEMS = list(HEAVENLY_STEMS)


# 生我(SHENG_WO)/克我(KE_WO)唯一真值源在内核 yishu_core.symbols（SKILL.md），此处仅引用。
# 历史债务：此前本文件与 classical_tables.py 各就地推导一份，连同内核共 3 份副本。


PALACE_GENERATING = dict(SHENG_WO)


PALACE_OVERCOMING = dict(KE_WO)


# 三合/十二长生/旬空：真值源在 core.yishu_core（SKILL.md），此处仅别名。
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


TRIGRAM_ELEMENT = _CORE_TRIGRAM_ELEMENTS  # 卦五行唯一真值源在内核（SKILL.md）


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

    词典本体已按事项族结构化进 data/（dev_tools/build_question_use_gods.py 生成，
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


# ── 问事归类唯一映射表（缺陷 D 修复，2026-10-09）──────────────────────────
# 旧病灶：step5/timing 各自用关键词元组对自由文本做子串嗅探决定方向门控与应期
# 分岔，改写措辞/换简繁即静默变向。现收敛为单一结构枚举 question_class，由
# step2 单点产出；关键词族与取类优先级全部在 data/rules/question_classes.json
# （§三：判类关键词不写进 .py）。
_QUESTION_CLASSES_PATH = Path(__file__).resolve().parents[1] / "data" / "rules" / "question_classes.json"


def _load_question_classes() -> tuple[list, dict, str]:
    """装载问事归类映射表 → (优先级, {类目: 关键词表}, 未命中默认值)。

    装载失败直接抛错不降级——判类失效会让 step5/timing 的门控静默全灭，
    与问题词典同口径（见 _load_question_use_gods 注记）。
    """
    try:
        data = json.loads(_QUESTION_CLASSES_PATH.read_text(encoding="utf-8"))
        priority = list(data["priority"])
        keywords = {c["class"]: list(c["keywords"]) for c in data["classes"]}
        missing = [c for c in priority if c not in keywords]
        if missing:
            raise KeyError(f"priority 中的类目在 classes 里缺失: {missing}")
        return priority, keywords, data.get("default", "其他")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError(
            f"问事归类映射表装载失败：{_QUESTION_CLASSES_PATH}（{exc}）。"
            "缺表时 question_class 判类会静默失真，按铁律一直接报排盘异常。"
        ) from exc


QUESTION_CLASS_PRIORITY, QUESTION_CLASS_KEYWORDS, QUESTION_CLASS_DEFAULT = _load_question_classes()


def classify_question(text: str) -> str:
    """归一（简繁）后按 priority 单点判类，返回 question_class 枚举值。

    与取用神层同一 normalize_question_text 口径：繁体问法不再静默漏判。
    """
    from yishu_core.symbols import normalize_question_text
    combined = normalize_question_text(str(text or ""))
    for cls in QUESTION_CLASS_PRIORITY:
        if any(kw and kw in combined for kw in QUESTION_CLASS_KEYWORDS[cls]):
            return cls
    return QUESTION_CLASS_DEFAULT


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

