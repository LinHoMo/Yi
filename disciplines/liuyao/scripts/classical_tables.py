# -*- coding: utf-8 -*-
"""古典断法增强：表 / 通用辅助 / 18 项断法 / 聚合入口 enhance_reading。（拆分自 classical_analysis.py，纯搬移不改逻辑；聚合入口见 classical_analysis.py）。"""

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel, kernel_dir

_ensure_kernel(__file__)

from yishu_core.najia import najia_branch

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
    SELF_PUNISHMENTS,
    SHENG_CYCLE,
    SHENG_WO,
    KE_WO,
    STEM_ELEMENTS,
    TRIGRAM_ELEMENTS as _CORE_TRIGRAM_ELEMENTS,
    THREE_PUNISHMENTS,
    THREE_PUNISHMENTS_CYCLIC,
    THREE_PUNISHMENTS_MUTUAL,
    TOMB_MAP,
    TWELVE_GROWTH,
    TWELVE_GROWTH_STAGES,
    TWELVE_GROWTH_TABLES,
)

from yishu_core.symbols import NAYIN as _CORE_NAYIN, NAYIN_TO_ELEMENT  # noqa: E402
from yishu_core.symbols import SAN_HE_GROUPS as _CORE_SAN_HE  # noqa: E402
from yishu_core.relations import SIX_RELATIONS  # noqa: E402


# 卦五行唯一真值源在内核 yishu_core.symbols.TRIGRAM_ELEMENTS（AGENTS.md §二），此处仅派生。
BAGUA = {_n: {"element": _el} for _n, _el in _CORE_TRIGRAM_ELEMENTS.items()}


PALACE_LOOKUP = {}


for _pname, _pdata in EIGHT_PALACES.items():
    for _hname, _gen in _pdata["order"]:
        PALACE_LOOKUP[_hname] = (_pname, _gen)


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


TRANSFORMATION_PATTERNS = {
    "连续三爻动": {
        "condition": "三个相邻爻位同时发动",
        "meaning": "事态集中，变动剧烈",
        "advice": "三爻齐动事必躁，宜速不宜迟",
        "weight": 1.5,
    },
    "间隔动爻": {
        "condition": "动爻交替排列（如1、3、5或2、4、6）",
        "meaning": "事多枝节，一波未平一波又起",
        "advice": "动静相间，事有反复",
        "weight": 1.2,
    },
    "上卦全动": {
        "condition": "上卦三爻（四、五、上）皆动",
        "meaning": "外局大变，局势动荡",
        "advice": "外卦全动，迁居出行之象",
        "weight": 1.3,
    },
    "下卦全动": {
        "condition": "下卦三爻（初、二、三）皆动",
        "meaning": "内局大变，根基动摇",
        "advice": "内卦全动，家宅不安",
        "weight": 1.3,
    },
    "对爻齐动": {
        "condition": "世爻与应爻同动",
        "meaning": "我他互动，主体双方关系紧张",
        "advice": "世应齐动，交涉必有变",
        "weight": 1.2,
    },
    "用神原神齐动": {
        "condition": "用神与原神（生用神之爻）同动",
        "meaning": "用神有原神暗助，虽弱不死",
        "advice": "原神助用，有惊无险",
        "weight": 1.4,
    },
    "用神忌神齐动": {
        "condition": "用神与忌神（克用神之爻）同动",
        "meaning": "用忌齐动，吉凶交战",
        "advice": "用忌交战，胜负难料，看力量孰强",
        "weight": 1.4,
    },
}


SIX_SPIRIT_PROPERTIES = {
    "青龙": {
        "nature": "吉神",
        "element": "木",
        "direction": "东",
        "virtue": "喜庆、吉祥、升迁、贵人",
        "caution": "临忌神/仇神则喜中生忧",
    },
    "朱雀": {
        "nature": "文书/口舌",
        "element": "火",
        "direction": "南",
        "virtue": "文书、言辞、沟通、考试",
        "caution": "临忌神/仇神则口舌讼事、文书之忧",
    },
    "勾陈": {
        "nature": "中土/迟滞",
        "element": "土",
        "direction": "中",
        "virtue": "稳重、田土、牵连、迟滞",
        "caution": "临忌神则蹉跎难成、官非牵连",
    },
    "螣蛇": {
        "nature": "惊恐/变动",
        "element": "土",
        "direction": "中",
        "virtue": "机智、交结、惊疑、多变",
        "caution": "临忌神则惊恐不安、怪异纠缠",
    },
    "白虎": {
        "nature": "凶煞",
        "element": "金",
        "direction": "西",
        "virtue": "威严、决断、医者",
        "caution": "临忌神/仇神则血光凶丧、重病伤亡",
    },
    "玄武": {
        "nature": "暗昧",
        "element": "水",
        "direction": "北",
        "virtue": "智谋、暗计、盗贼",
        "caution": "临忌神/仇神则奸邪盗贼、暗昧不明",
    },
}

