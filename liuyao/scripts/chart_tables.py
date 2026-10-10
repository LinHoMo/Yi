# -*- coding: utf-8 -*-
"""六爻纳甲引擎数据表 + 古典断法数据表。"""

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

from yishu_core.symbols import NAJIA_STEMS  # noqa: F401  纳甲天干唯一真值源在 core（再导出供本科使用）

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    BAGUA_LINES,
    EIGHT_PALACES,
    SELF_PUNISHMENTS,
    SHENG_WO,
    KE_WO,
    THREE_PUNISHMENTS,
    THREE_PUNISHMENTS_CYCLIC,
    THREE_PUNISHMENTS_MUTUAL,
    TRIGRAM_ELEMENTS,
    TWELVE_GROWTH,
    TWELVE_GROWTH_STAGES,
    TWELVE_GROWTH_TABLES,
    NAYIN as _CORE_NAYIN,
    NAYIN_TO_ELEMENT,
    SAN_HE_GROUPS as _CORE_SAN_HE,
)

from yishu_core.relations import SIX_RELATIONS  # noqa: E402

from yishu_core.hexagram_texts import HEXAGRAMS, HEXAGRAM_LINE_TEXTS  # noqa: E402  卦辞爻辞唯一真值源（AGENTS.md §二）


import json as _kt_json










# ══════════════════════════════════════════════════════════════════════════════
# ── engine_tables 部分 ──
# ══════════════════════════════════════════════════════════════════════════════

# 爻序(lines)与卦五行(element)的唯一真值源在内核 BAGUA_LINES / TRIGRAM_ELEMENTS（AGENTS.md §二）。
# 历史教训：此处曾就地硬编码一份「上爻在前」的镜像爻序，其中 震/巽/艮/兑 四卦与内核完全相反，
# 仅靠下方覆盖循环才未暴露成 bug——一旦有人删掉循环即复活。现本地不存任何爻序/五行副本。
BAGUA = {
    "乾": {"nature": "yang", "symbol": "☰"},
    "坤": {"nature": "yin",  "symbol": "☷"},
    "震": {"nature": "yang", "symbol": "☳"},
    "巽": {"nature": "yin",  "symbol": "☴"},
    "坎": {"nature": "yang", "symbol": "☵"},
    "离": {"nature": "yin",  "symbol": "☲"},
    "艮": {"nature": "yang", "symbol": "☶"},
    "兑": {"nature": "yin",  "symbol": "☱"},
}

for _n, _lines in BAGUA_LINES.items():
    BAGUA[_n]["lines"] = _lines                  # 自下而上，唯一真值源
    BAGUA[_n]["element"] = TRIGRAM_ELEMENTS[_n]  # 卦五行同样取自内核


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



# ══════════════════════════════════════════════════════════════════════════════
# ── classical_tables 部分 ──
# ══════════════════════════════════════════════════════════════════════════════

# BAGUA：engine_tables 版本已包含 element/nature/symbol/lines，为本文件唯一 BAGUA 定义。
# 卦五行唯一真值源在内核 yishu_core.symbols.TRIGRAM_ELEMENTS（AGENTS.md §二），此处仅派生。

# PALACE_LOOKUP：engine_tables 已定义（与 classical_tables 同源 EIGHT_PALACES），此处不重复。

# 生我(SHENG_WO)/克我(KE_WO)唯一真值源在内核（AGENTS.md §二），此处仅引用（与 chain_tables 同源）。
# 三合/十二长生/三刑/纳音：真值源在 core.yishu_core（AGENTS.md §二），此处仅别名。
SAN_HE = _CORE_SAN_HE

YANG_STEMS = {"甲", "丙", "戊", "庚", "壬"}

NAYIN_TABLE = dict(_CORE_NAYIN)

_QUESTION_KEYWORDS_USE_GOD = {
    "父母": ["父", "母", "长辈", "文书", "考试", "学业", "房产", "房", "合同", "证书", "车辆"],
    "官鬼": ["事业", "工作", "官", "职", "升", "迁", "丈夫", "疾病", "病", "官司", "诉讼", "小人", "灾难"],
    "子孙": ["子", "女", "孩子", "晚辈", "学生", "宠物", "医药", "治病"],
    "妻财": ["财", "钱", "投资", "生意", "收入", "利", "赚", "妻子", "婚姻", "感情", "女友"],
    "兄弟": ["兄弟", "姐妹", "朋友", "同事", "竞争", "对手"],
}

# ── 古籍格局与六神属性表 ──
# AGENTS.md §三：断语/引文进 data/*.json，代码只留算法。
# 数据唯一真值源：data/classical_patterns_data.json


def _load_classical_patterns() -> dict:
    """从唯一 JSON 数据源加载古籍格局与六神属性表。"""
    _data_path = _ks_os.path.join(_ks_os.path.dirname(_ks_os.path.abspath(__file__)),
                                  "..", "data", "classical_patterns_data.json")
    with open(_data_path, "r", encoding="utf-8") as _f:
        return _kt_json.load(_f)


_cp = _load_classical_patterns()
TRANSFORMATION_PATTERNS: dict = _cp["transformation_patterns"]
SIX_SPIRIT_PROPERTIES: dict = _cp["six_spirit_properties"]
