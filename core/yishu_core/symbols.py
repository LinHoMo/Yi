# -*- coding: utf-8 -*-
"""象数基元（Xiangshu Primitives）—— 六爻及后续各科共用的规则表，唯一真值源。

本文件由 `scratch/unify_tables.py` 从三份重复副本机械搬入；搬动前已逐条目比对，
除 EIGHT_PALACES 外三份取值完全一致（取证：`scratch/dup_table_audit.py`）。
EIGHT_PALACES 以 liuyao_engine 副本为准——thinking_chain 旧副本的兑宫世次排错
（把 小过 记作五世、归妹 游魂、谦 归魂）。

**不要在别处再抄一份**：新增关系表先查这里有没有，没有就加进来。
EIGHT_PALACES 的键是裸宫名（"乾" 而非 "乾宫"），本宫首卦的世代标签为 "六世"；
兼容 "X宫" 写法请用 `palace_of_key()`。

**纳音（`NAYIN_COUPLETS`/`NAYIN`/`NAYIN_TO_ELEMENT`/`nayin_of`）与三合局分组
（`SAN_HE_GROUPS`/`sanhe_group`）2026-09-29 自 `ming_tables.py` 迁入**：两者本是
命、卜两科共用的干支关系表，住在以 `ming_` 命名的模块里等于挂错了门牌
（审计 B3）。三合局迁入也补齐了本模块章程原本就写着的「六合六冲**三合**三刑六破」。
**取值零变化**（迁移前后逐表比对）。命、卜两科均从本模块取，不再经过 `ming_tables`。
"""
from __future__ import annotations

from .ganzhi_calendar import (  # 纳音按六十甲子序取（nayin_of_index）
    ganzhi_pair,
    HEAVENLY_STEMS as _GC_HEAVENLY_STEMS,
    EARTHLY_BRANCHES as _GC_EARTHLY_BRANCHES,
)

# 天干地支唯一字面量在 ganzhi_calendar（依赖链最底层），此处派生 list 形态供各科使用
HEAVENLY_STEMS = list(_GC_HEAVENLY_STEMS)

EARTHLY_BRANCHES = list(_GC_EARTHLY_BRANCHES)

STEM_ELEMENTS = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"
}

BRANCH_ELEMENTS = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"
}

SHENG_CYCLE = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}

KE_CYCLE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

HE_PAIRS = [
    ("子", "丑"), ("寅", "亥"), ("卯", "戌"),
    ("辰", "酉"), ("巳", "申"), ("午", "未"),
]

CHONG_PAIRS = [
    ("子", "午"), ("丑", "未"), ("寅", "申"),
    ("卯", "酉"), ("辰", "戌"), ("巳", "亥"),
]

BREAK_PAIRS = [
    ("子", "酉"), ("酉", "子"),
    ("午", "卯"), ("卯", "午"),
    ("巳", "申"), ("申", "巳"),
    ("寅", "亥"), ("亥", "寅"),
    ("辰", "丑"), ("丑", "辰"),
    ("戌", "未"), ("未", "戌"),
]

# 六害（支害）：命卜两科共用（ming 八字地支相害、liuyao 卦爻关系）。
HARM_PAIRS = [
    ("子", "未"), ("未", "子"),
    ("丑", "午"), ("午", "丑"),
    ("寅", "巳"), ("巳", "寅"),
    ("卯", "辰"), ("辰", "卯"),
    ("申", "亥"), ("亥", "申"),
    ("酉", "戌"), ("戌", "酉"),
]

TOMB_MAP = {
    "火": "戌",   # 火墓在戌
    "水": "辰",   # 水墓在辰
    "木": "未",   # 木墓在未
    "金": "丑",   # 金墓在丑
    "土": "辰",   # 土墓在辰（从水）
}

ADVANCE_PAIRS = {
    "子": "寅", "寅": "辰", "辰": "午", "午": "申", "申": "戌", "戌": "子",
    "亥": "丑", "丑": "卯", "卯": "巳", "巳": "未", "未": "酉", "酉": "亥",
}

RETREAT_PAIRS = {v: k for k, v in ADVANCE_PAIRS.items()}

# ============================================================ 旬空（空亡）
# 六十甲子每旬（甲…癸）余下两支为「空」。甲子旬空戌亥，余仿此。
# 消费方：六爻（用神旬空/出空）、命科（日柱空亡）。
XUN_KONG = {
    "甲子": ["戌", "亥"], "甲戌": ["申", "酉"], "甲申": ["午", "未"],
    "甲午": ["辰", "巳"], "甲辰": ["寅", "卯"], "甲寅": ["子", "丑"],
}


def xunkong_of(day_ganzhi: str) -> list[str]:
    """日柱干支 → 该旬空亡两支；非法返回 []。旬首按甲x 取，其余干支回溯本旬甲x。"""
    gz = (day_ganzhi or "").strip()
    if len(gz) != 2:
        return []
    stem, branch = gz[0], gz[1]
    if stem not in HEAVENLY_STEMS or branch not in EARTHLY_BRANCHES:
        return []
    si, bi = HEAVENLY_STEMS.index(stem), EARTHLY_BRANCHES.index(branch)
    # 本旬甲支：从日支回溯到最近的甲*（天干序差）
    xun_start_branch = EARTHLY_BRANCHES[(bi - si) % 12]
    key = "甲" + xun_start_branch
    return list(XUN_KONG.get(key, []))


# ============================================================ 三刑
# 《三命通会》通行口径：无礼之刑（子卯）、无恩之刑（寅巳申）、恃势之刑（丑戌未），
# 另有自刑辰午酉亥。这里只存结构，判刑由机械函数 `sanxing_hits` 给出，不断吉凶。
THREE_PUNISHMENTS_CYCLIC = {
    "无恩之刑": ["寅", "巳", "申"],
    "恃势之刑": ["丑", "戌", "未"],
}
THREE_PUNISHMENTS_MUTUAL = {
    "无礼之刑": ("子", "卯"),
}
SELF_PUNISHMENTS = ["辰", "午", "酉", "亥"]
THREE_PUNISHMENTS = {
    "无礼之刑": [("子", "卯")],
    "无恩之刑": [("寅", "巳"), ("巳", "申"), ("申", "寅")],
    "恃势之刑": [("丑", "戌"), ("戌", "未"), ("未", "丑")],
    "自刑": ["辰", "午", "酉", "亥"],
}


def sanxing_hits(branches: list[str]) -> list[str]:
    """地支集合 → 命中的三刑类型名列表（只报结构，不报吉凶）。"""
    bs = [b for b in (branches or []) if b in BRANCH_ELEMENTS]
    hits: list[str] = []
    set_bs = set(bs)
    if "子" in set_bs and "卯" in set_bs:
        hits.append("无礼之刑")
    for name, cycle in THREE_PUNISHMENTS_CYCLIC.items():
        if all(b in set_bs for b in cycle):
            hits.append(name)
    for b in SELF_PUNISHMENTS:
        if bs.count(b) >= 2:
            hits.append("自刑")
            break
    return hits


# ============================================================ 十二长生
# 阳干顺行、阴干逆行的通行表已折算成「五行 → 支序」固定盘（火土同宫）。
# 只存结构；旺衰加减由学科层按自身口径消费。
TWELVE_GROWTH_STAGES = [
    "长生", "沐浴", "冠带", "临官", "帝旺",
    "衰", "病", "死", "墓", "绝", "胎", "养",
]
TWELVE_GROWTH_TABLES = {
    "木": ["亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌"],
    "火": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
    "金": ["巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰"],
    "水": ["申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未"],
    "土": ["申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未"],
}
# 火土同长生（寅起）；与上表「土从水（申起）」并存是流派差异，本仓库默认火土同宫。
TWELVE_GROWTH = {
    "木": {b: TWELVE_GROWTH_STAGES[i] for i, b in enumerate(TWELVE_GROWTH_TABLES["木"])},
    "火": {b: TWELVE_GROWTH_STAGES[i] for i, b in enumerate(TWELVE_GROWTH_TABLES["火"])},
    "土": {b: TWELVE_GROWTH_STAGES[i] for i, b in enumerate(TWELVE_GROWTH_TABLES["火"])},  # 火土同宫
    "金": {b: TWELVE_GROWTH_STAGES[i] for i, b in enumerate(TWELVE_GROWTH_TABLES["金"])},
    "水": {b: TWELVE_GROWTH_STAGES[i] for i, b in enumerate(TWELVE_GROWTH_TABLES["水"])},
}


def twelve_growth(element: str, branch: str) -> str | None:
    """五行 + 地支 → 十二长生阶段名；非法返回 None。"""
    return TWELVE_GROWTH.get(element, {}).get(branch)


def twelve_growth_index(element: str, branch: str) -> int | None:
    """五行 + 地支 → 长生序号（0=长生 … 11=养）；非法返回 None。"""
    stage = twelve_growth(element, branch)
    if stage is None:
        return None
    return TWELVE_GROWTH_STAGES.index(stage)


NAJIA_BRANCHES = {
    "乾": {
        "inner": ["子", "寅", "辰"],   # 下卦从下到上
        "outer": ["午", "申", "戌"],   # 上卦从下到上
    },
    "坤": {
        "inner": ["未", "巳", "卯"],   # 阴卦逆排
        "outer": ["丑", "亥", "酉"],
    },
    "震": {
        "inner": ["子", "寅", "辰"],
        "outer": ["午", "申", "戌"],
    },
    "坎": {
        "inner": ["寅", "辰", "午"],
        "outer": ["申", "戌", "子"],
    },
    "艮": {
        "inner": ["辰", "午", "申"],
        "outer": ["戌", "子", "寅"],
    },
    "巽": {
        "inner": ["丑", "亥", "酉"],   # 阴卦逆排
        "outer": ["未", "巳", "卯"],
    },
    "离": {
        "inner": ["卯", "丑", "亥"],   # 阴卦逆排
        "outer": ["酉", "未", "巳"],
    },
    "兑": {
        "inner": ["巳", "卯", "丑"],   # 阴卦逆排
        "outer": ["亥", "酉", "未"],
    },
}

# 纳甲天干表（与 NAJIA_BRANCHES 合璧：纳甲干支整体唯一真值源）
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

HEXAGRAM_TRIGRAMS = {
    "乾": ("乾", "乾"), "坤": ("坤", "坤"), "屯": ("坎", "震"), "蒙": ("艮", "坎"),
    "需": ("坎", "乾"), "讼": ("乾", "坎"), "师": ("坤", "坎"), "比": ("坎", "坤"),
    "小畜": ("巽", "乾"), "履": ("乾", "兑"), "泰": ("坤", "乾"), "否": ("乾", "坤"),
    "同人": ("乾", "离"), "大有": ("离", "乾"), "谦": ("坤", "艮"), "豫": ("震", "坤"),
    "随": ("兑", "震"), "蛊": ("艮", "巽"), "临": ("坤", "兑"), "观": ("巽", "坤"),
    "噬嗑": ("离", "震"), "贲": ("艮", "离"), "剥": ("艮", "坤"), "复": ("坤", "震"),
    "无妄": ("乾", "震"), "大畜": ("艮", "乾"), "颐": ("艮", "震"), "大过": ("兑", "巽"),
    "坎": ("坎", "坎"), "离": ("离", "离"), "咸": ("兑", "艮"), "恒": ("震", "巽"),
    "遁": ("乾", "艮"), "大壮": ("震", "乾"), "晋": ("离", "坤"), "明夷": ("坤", "离"),
    "家人": ("巽", "离"), "睽": ("离", "兑"), "蹇": ("坎", "艮"), "解": ("震", "坎"),
    "损": ("艮", "兑"), "益": ("巽", "震"), "夬": ("兑", "乾"), "姤": ("乾", "巽"),
    "萃": ("兑", "坤"), "升": ("坤", "巽"), "困": ("兑", "坎"), "井": ("坎", "巽"),
    "革": ("兑", "离"), "鼎": ("离", "巽"), "震": ("震", "震"), "艮": ("艮", "艮"),
    "渐": ("巽", "艮"), "归妹": ("震", "兑"), "丰": ("震", "离"), "旅": ("离", "艮"),
    "巽": ("巽", "巽"), "兑": ("兑", "兑"), "涣": ("巽", "坎"), "节": ("坎", "兑"),
    "中孚": ("巽", "兑"), "小过": ("震", "艮"), "既济": ("坎", "离"), "未济": ("离", "坎"),
}

EIGHT_PALACES = {
    "乾": {
        "element": "金",
        "order": [
            ("乾",   "六世"),
            ("姤",   "一世"),
            ("遁",   "二世"),
            ("否",   "三世"),
            ("观",   "四世"),
            ("剥",   "五世"),
            ("晋",   "游魂"),
            ("大有", "归魂"),
        ],
    },
    "坎": {
        "element": "水",
        "order": [
            ("坎",   "六世"),
            ("节",   "一世"),
            ("屯",   "二世"),
            ("既济", "三世"),
            ("革",   "四世"),
            ("丰",   "五世"),
            ("明夷", "游魂"),
            ("师",   "归魂"),
        ],
    },
    "艮": {
        "element": "土",
        "order": [
            ("艮",   "六世"),
            ("贲",   "一世"),
            ("大畜", "二世"),
            ("损",   "三世"),
            ("睽",   "四世"),
            ("履",   "五世"),
            ("中孚", "游魂"),
            ("渐",   "归魂"),
        ],
    },
    "震": {
        "element": "木",
        "order": [
            ("震",   "六世"),
            ("豫",   "一世"),
            ("解",   "二世"),
            ("恒",   "三世"),
            ("升",   "四世"),
            ("井",   "五世"),
            ("大过", "游魂"),
            ("随",   "归魂"),
        ],
    },
    "巽": {
        "element": "木",
        "order": [
            ("巽",   "六世"),
            ("小畜", "一世"),
            ("家人", "二世"),
            ("益",   "三世"),
            ("无妄", "四世"),
            ("噬嗑", "五世"),
            ("颐",   "游魂"),
            ("蛊",   "归魂"),
        ],
    },
    "离": {
        "element": "火",
        "order": [
            ("离",   "六世"),
            ("旅",   "一世"),
            ("鼎",   "二世"),
            ("未济", "三世"),
            ("蒙",   "四世"),
            ("涣",   "五世"),
            ("讼",   "游魂"),
            ("同人", "归魂"),
        ],
    },
    "坤": {
        "element": "土",
        "order": [
            ("坤",   "六世"),
            ("复",   "一世"),
            ("临",   "二世"),
            ("泰",   "三世"),
            ("大壮", "四世"),
            ("夬",   "五世"),
            ("需",   "游魂"),
            ("比",   "归魂"),
        ],
    },
    "兑": {
        "element": "金",
        "order": [
            ("兑",   "六世"),
            ("困",   "一世"),
            ("萃",   "二世"),
            ("咸",   "三世"),
            ("蹇",   "四世"),
            ("谦",   "五世"),
            ("小过", "游魂"),
            ("归妹", "归魂"),
        ],
    },
}


# ── 八卦爻序（唯一真值源）──────────────────────────────────────────────
# 约定：列表自下而上，index 0 = 初爻，1 = 二爻，2 = 三爻；1=阳，0=阴。
# 这是 P0 爻序事故的终止点：震巽艮兑四个非回文卦曾在四处（引擎 BAGUA、
# case_runner、batch_round3_direct、data/hexagrams.json 的 binary）各存一份
# **上爻在前**的镜像编码，而所有消费代码都按"自下而上"解读，于是每个经卦内部
# 三个爻的位次被整体颠倒——恒之鼎的上六动会被算成第四爻动。
# 现在只有这里一份；其余处一律 import 或由此派生。
BAGUA_LINES = {
    "乾": [1, 1, 1],   # 三连
    "坤": [0, 0, 0],   # 三断
    "震": [1, 0, 0],   # 初阳，仰盂
    "巽": [0, 1, 1],   # 初阴，下断
    "坎": [0, 1, 0],   # 中满
    "离": [1, 0, 1],   # 中虚
    "艮": [0, 0, 1],   # 覆碗，上阳
    "兑": [1, 1, 0],   # 上缺
}

# 六爻数组里的位置索引 → 该爻在其经卦内的序号（下卦 0-2、上卦 3-5 各自自下而上）


def trigram_lines(name: str) -> list[int]:
    """经卦爻线（自下而上）。"""
    return list(BAGUA_LINES[name])


def yao_values(name: str, moving: tuple[int, ...] = ()) -> list[int]:
    """经卦/别卦起卦值序列（自下而上，7 少阳 8 少阴 9 老阳 6 老阴）。

    `name` 可以是经卦（乾…兑）或六十四卦卦名（需 HEXAGRAM_TRIGRAMS 有记录）。
    `moving` 是 1..6 的爻位。

    八纯卦（乾/坤/坎/离/震/巽/艮/兑）同名既有经卦也有别卦：本函数**优先按六十四卦**
    返回 6 爻；要经卦 3 爻请直接用 `BAGUA_LINES[name]`。
    """
    # 六十四卦优先（八纯卦与经卦重名）
    if name in HEXAGRAM_TRIGRAMS:
        upper, lower = HEXAGRAM_TRIGRAMS[name]
        lines = BAGUA_LINES[lower] + BAGUA_LINES[upper]
    elif name in BAGUA_LINES:
        lines = BAGUA_LINES[name]
    else:
        raise KeyError(f"未知卦名：{name}")
    out = []
    for i, bit in enumerate(lines, start=1):
        moving_now = i in moving
        out.append((9 if bit else 6) if moving_now else (7 if bit else 8))
    return out


SHENG_WO = {v: k for k, v in SHENG_CYCLE.items()}   # 生我者（原神方向）
KE_WO = {v: k for k, v in KE_CYCLE.items()}         # 克我者（忌神方向）


# ── 先天八卦数（梅花易数取数用）──────────────────────────────────────────
# 《梅花易数·卷一·周易卦数》："乾一、兑二、离三、震四、巽五、坎六、艮七、坤八。"
# 梅花起卦"卦以八除"取余即此数表；六爻纳甲不用此表。
XIAN_TIAN_TRIGRAM_NUMBERS = {
    "乾": 1, "兑": 2, "离": 3, "震": 4,
    "巽": 5, "坎": 6, "艮": 7, "坤": 8,
}
NUMBER_TO_TRIGRAM = {v: k for k, v in XIAN_TIAN_TRIGRAM_NUMBERS.items()}

# 八宫所属五行（经卦层面）：《梅花易数·卷一·八宮所屬五行》
# "乾、兑，金；坤、艮，土；震、巽，木；坎，水；离，火。"
# 六十四卦宫五行另见 EIGHT_PALACES（以卦宫为准），此处是单经卦的五行。
TRIGRAM_ELEMENTS = {
    "乾": "金", "兑": "金", "坤": "土", "艮": "土",
    "震": "木", "巽": "木", "坎": "水", "离": "火",
}

# ── 五行旺相休囚死（月令旺衰，梅花卦气旺衰/择吉共用）────────────────────
# 由月支定五行旺相休囚死：当令者旺、旺所生者相、生旺者休、克旺者囚、旺所克者死。
# 《梅花易数·卷一·卦氣旺》"震巽木旺于春、离火旺于夏、乾兑金旺于秋、坎水旺于冬、
# 坤艮土旺于辰戌丑未月"即当令者旺；其余四位依相生相克的常规次序。
WANG_XIANG_XIU_QIU_SI = {
    "寅": {"木": "旺", "火": "相", "水": "休", "金": "囚", "土": "死"},
    "卯": {"木": "旺", "火": "相", "水": "休", "金": "囚", "土": "死"},
    "辰": {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"},
    "巳": {"火": "旺", "土": "相", "木": "休", "水": "囚", "金": "死"},
    "午": {"火": "旺", "土": "相", "木": "休", "水": "囚", "金": "死"},
    "未": {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"},
    "申": {"金": "旺", "水": "相", "土": "休", "火": "囚", "木": "死"},
    "酉": {"金": "旺", "水": "相", "土": "休", "火": "囚", "木": "死"},
    "戌": {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"},
    "亥": {"水": "旺", "木": "相", "金": "休", "土": "囚", "火": "死"},
    "子": {"水": "旺", "木": "相", "金": "休", "土": "囚", "火": "死"},
    "丑": {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"},
}


def wangxiangxiuqiusi(month_branch: str, element: str) -> str | None:
    """某月支下某五行的旺相休囚死状态；非法输入返回 None。"""
    table = WANG_XIANG_XIU_QIU_SI.get(month_branch)
    return table.get(element) if table else None


def hexagram_branches(name: str) -> list[str] | None:
    """别卦六爻纳甲地支（自下而上，index 0 = 初爻）；卦名不可解析返回 None。

    下卦取 `NAJIA_BRANCHES[lower]["inner"]`、上卦取 `NAJIA_BRANCHES[upper]["outer"]`，
    与六爻排盘的装卦口径一致（阴卦逆排已写在表里，此处不再另作顺逆判断）。
    """
    tri = HEXAGRAM_TRIGRAMS.get(name)
    if not tri:
        return None
    upper, lower = tri
    return list(NAJIA_BRANCHES[lower]["inner"]) + list(NAJIA_BRANCHES[upper]["outer"])


def palace_of_key(name: str) -> str:
    """"艮宫" → "艮"。EIGHT_PALACES 的键是裸宫名。"""
    return name[:-1] if name.endswith("宫") else name


def palace_element(name: str) -> str | None:
    data = EIGHT_PALACES.get(palace_of_key(name))
    return data["element"] if data else None


def palace_first_hexagram(name: str) -> str | None:
    data = EIGHT_PALACES.get(palace_of_key(name))
    return data["order"][0][0] if data else None


# ── 问事文本用字归一（只覆盖占问常用字，不是通用繁简转换器）──────────────
# 为什么要有：用神取法靠问事文本里的关键词匹配，而关键词表是按简体写的。
# 《增刪卜易》原文（以及从它建起来的外部集）通篇繁体——"占候文書""占升遷"
# 里的 書/遷 与表中的 书/迁 不是同一个码位，匹配静默失败：外部集上原文明写
# 用神的 6 例引擎一例没取对，其中 2 例纯粹是这个原因。
# 只登记占问语境真会碰到的字；要加新字先确认关键词表里对应有简体词，
# 否则加了也不产生任何匹配，只是把"没覆盖"伪装成"已覆盖"。
Q_TEXT_VARIANTS = str.maketrans({
    "來": "来", "將": "将", "歸": "归", "書": "书", "貸": "贷", "過": "过",
    "遷": "迁", "還": "还", "開": "开", "關": "关", "領": "领", "試": "试",
    "財": "财", "銀": "银", "盤": "盘", "僕": "仆", "終": "终", "壽": "寿",
    "脫": "脱", "選": "选", "業": "业", "產": "产", "發": "发", "變": "变",
    "觀": "观", "馬": "马", "車": "车", "門": "门", "長": "长", "問": "问",
    "間": "间", "時": "时", "號": "号", "處": "处", "員": "员", "費": "费",
    "資": "资", "損": "损", "賣": "卖", "購": "购",
    "買": "买", "貨": "货", "價": "价", "與": "与", "舉": "举", "應": "应",
    "癒": "愈", "殤": "殇", "歿": "殁", "墳": "坟",
})


def normalize_question_text(text: str) -> str:
    """把问事文本里的繁体用字归一到关键词表用的写法；长度不变。"""
    return (text or "").translate(Q_TEXT_VARIANTS)


# ================================================================ 纳音（六十甲子）
NAYIN_COUPLETS = [
    ("海中金", "甲子", "乙丑"), ("炉中火", "丙寅", "丁卯"), ("大林木", "戊辰", "己巳"),
    ("路旁土", "庚午", "辛未"), ("剑锋金", "壬申", "癸酉"), ("山头火", "甲戌", "乙亥"),
    ("涧下水", "丙子", "丁丑"), ("城头土", "戊寅", "己卯"), ("白蜡金", "庚辰", "辛巳"),
    ("杨柳木", "壬午", "癸未"), ("泉中水", "甲申", "乙酉"), ("屋上土", "丙戌", "丁亥"),
    ("霹雳火", "戊子", "己丑"), ("松柏木", "庚寅", "辛卯"), ("长流水", "壬辰", "癸巳"),
    ("沙中金", "甲午", "乙未"), ("山下火", "丙申", "丁酉"), ("平地木", "戊戌", "己亥"),
    ("壁上土", "庚子", "辛丑"), ("金箔金", "壬寅", "癸卯"), ("覆灯火", "甲辰", "乙巳"),
    ("天河水", "丙午", "丁未"), ("大驿土", "戊申", "己酉"), ("钗钏金", "庚戌", "辛亥"),
    ("桑柘木", "壬子", "癸丑"), ("大溪水", "甲寅", "乙卯"), ("沙中土", "丙辰", "丁巳"),
    ("天上火", "戊午", "己未"), ("石榴木", "庚申", "辛酉"), ("大海水", "壬戌", "癸亥"),
]
NAYIN = {}
for _ny, _g1, _g2 in NAYIN_COUPLETS:
    NAYIN[_g1] = _ny
    NAYIN[_g2] = _ny


# 纳音 → 五行（六爻断法与命科共用；名字取《三命通会》通行写法）
NAYIN_TO_ELEMENT = {
    "海中金": "金", "炉中火": "火", "大林木": "木", "路旁土": "土", "剑锋金": "金",
    "山头火": "火", "涧下水": "水", "城头土": "土", "白蜡金": "金", "杨柳木": "木",
    "泉中水": "水", "屋上土": "土", "霹雳火": "火", "松柏木": "木", "长流水": "水",
    "沙中金": "金", "山下火": "火", "平地木": "木", "壁上土": "土", "金箔金": "金",
    "覆灯火": "火", "天河水": "水", "大驿土": "土", "钗钏金": "金", "桑柘木": "木",
    "大溪水": "水", "沙中土": "土", "天上火": "火", "石榴木": "木", "大海水": "水",
}


def nayin_of(ganzhi: str) -> str | None:
    """干支（两字）→ 纳音；非法返回 None。"""
    return NAYIN.get(ganzhi)


def nayin_of_index(index60: int) -> str | None:
    """六十甲子序号 → 纳音。"""
    return NAYIN.get(ganzhi_pair(index60 % 60))


# ================================================================ 三合局分组
# 驿马/桃花/华盖按三合局取，故需要「一支属哪一局」。core 此前无此表（见模块头注释）。
SAN_HE_GROUPS = {
    "水": ["申", "子", "辰"],
    "木": ["亥", "卯", "未"],
    "火": ["寅", "午", "戌"],
    "金": ["巳", "酉", "丑"],
}
_BRANCH_TO_SANHE = {b: elem for elem, bs in SAN_HE_GROUPS.items() for b in bs}


def sanhe_group(branch: str) -> str | None:
    """地支 → 所属三合局五行（水/木/火/金）；非法返回 None。"""
    return _BRANCH_TO_SANHE.get(branch)


# ================================================================ 三会方局
# 《三命通会》通行口径：寅卯辰会东方木、巳午未会南方火、申酉戌会西方金、亥子丑会北方水。
# 方局是一季三支之气全，力大于三合（三合是隔三之支，长生于帝旺之三支）。
# 只存结构；吉凶与优先序由学科层按自身口径消费。
SAN_HUI_GROUPS = {
    "木": ["寅", "卯", "辰"],
    "火": ["巳", "午", "未"],
    "金": ["申", "酉", "戌"],
    "水": ["亥", "子", "丑"],
}


# ================================================================ 卦级反吟 / 伏吟
# 《卜筮正宗》"内卦反吟内不安，外卦反吟外不宁"；《火珠林》`小畜`条
# "上卦巳丑酉·六合，下卦午卯子·六冲"——同一卦可以半反半伏。
# 判定在**卦位**上做：本卦与变卦同一爻位的地支，冲＝反吟、同＝伏吟，逐位统计。
# 逐位关系只算冲/同/合三类（合另立 `pair_he`）：地支值域里既冲又合、既合又同的组合
# 并不存在，故三类互斥；"其他"即无关系。这里只出结构名，吉凶由学科层叠旺衰定。
HEXAGRAM_LEVEL_FULL_CLASH = "全卦反吟"
HEXAGRAM_LEVEL_FULL_SAME = "全卦伏吟"
HEXAGRAM_LEVEL_TRIGRAM_CLASH = "内外反吟"
HEXAGRAM_LEVEL_TRIGRAM_SAME = "内外伏吟"
HEXAGRAM_LEVEL_MIXED = "半反半伏"
HEXAGRAM_LEVEL_NONE = "无反吟伏吟"

# 卦体六合/六冲（按对应位 (1,4)(2,5)(3,6) 的地支关系判，非卦名表）
HEXAGRAM_KIND_LIUHE = "六合卦"
HEXAGRAM_KIND_LIUCHONG = "六冲卦"
HEXAGRAM_KIND_HALF = "半合半冲"
HEXAGRAM_KIND_SOME_HE = "有合"
HEXAGRAM_KIND_SOME_CHONG = "有冲"
HEXAGRAM_KIND_NONE = "无明确合冲"
HEXAGRAM_KIND_UNKNOWN = "未知"

_CHONG_PAIR_SET = {frozenset(p) for p in CHONG_PAIRS}
_HE_PAIR_SET = {frozenset(p) for p in HE_PAIRS}


def hexagram_he_chong_kind(name: str) -> str:
    """卦名 → 卦体六合/六冲类别（对应位三对地支皆合/皆冲才算）。

    口径与六爻排盘层 `analyze_clash_harmony` 一致：取 (初,四)(二,五)(三,六) 三对
    地支，三对皆六合＝六合卦、三对皆六冲＝六冲卦。**不用卦名白名单**——白名单
    会把 `小畜`（下乾上巽：内三爻子寅辰、外三爻未巳卯，三对为合、合、合）这类
    双象卦判成单一类。八纯卦（乾兑离震巽坎艮坤）与 `无妄`/`大壮` 判为六冲，
    `否`/`泰`/`贲`/`困`/`旅`/`豫`/`复`/`节` 判为六合，与《卜卦正宗》卦体六冲六合
    的通行口径一致。卦名不可解析返回 `未知`。
    """
    branches = hexagram_branches(name) if name else None
    if not branches:
        return HEXAGRAM_KIND_UNKNOWN
    he = chong = 0
    for i, j in ((0, 3), (1, 4), (2, 5)):
        pair = frozenset((branches[i], branches[j]))
        if pair in _CHONG_PAIR_SET:
            chong += 1
        elif pair in _HE_PAIR_SET:
            he += 1
    if he == 3:
        return HEXAGRAM_KIND_LIUHE
    if chong == 3:
        return HEXAGRAM_KIND_LIUCHONG
    if he and chong:
        return HEXAGRAM_KIND_HALF
    if he:
        return HEXAGRAM_KIND_SOME_HE
    if chong:
        return HEXAGRAM_KIND_SOME_CHONG
    return HEXAGRAM_KIND_NONE


def hexagram_level_relations(original_name: str, changed_name: str) -> dict:
    """本卦 / 变卦按爻位逐一比对地支 → 反吟（冲）伏吟（同）的卦级结构。

    返回 {pairs, clash_count, same_count, he_count, other_count,
          full_clash, full_same, inner_clash, outer_clash, inner_same, outer_same,
          scope, category}；卦名不可解析时 category/scope 为 None（调用方按"未判定"处理）。

    口径（三层，逐层收严）：
      1. **爻位关系**：同一位上本卦支 vs 变卦支，冲＝反吟、同＝伏吟、合＝化合。
         一对爻位不可能既冲又同，冲与合在六爻地支里也无交集，故三类互斥。
      2. **卦级**：六位全冲＝`全卦反吟`（乾变巽：子冲午、寅冲申、辰冲戌，两位皆然）；
         六位全同＝`全卦伏吟`（八纯卦不动之变）。
      3. **内外卦级**：内三爻或外三爻全冲（内卦反吟）／全同（内卦伏吟）。
         小畜（下乾上巽）变乾（下乾上乾）：下卦三位子寅辰不变而全同、上卦巳丑酉
         三位全冲——《火珠林》以小畜为六合六冲双卦，正是此象。

    `scope` 另报经卦层面的"变与不变"：经卦未变而爻支全同 = 真伏吟；经卦变了却
    纳甲支全同（如乾→震，同为子寅辰）＝纳甲同而卦体已易，按古籍只作"伏吟之象"
    而不作真伏吟，两个标志分开报，由消费方定口径。`valid` 为 False 表示卦名无法
    从 HEXAGRAM_TRIGRAMS 解析，此时各计数均为 0，调用方不得据以断卦。
    """
    base = hexagram_branches(original_name) if original_name else None
    chg = hexagram_branches(changed_name) if changed_name else None
    tri_base = HEXAGRAM_TRIGRAMS.get(original_name) if original_name else None
    tri_chg = HEXAGRAM_TRIGRAMS.get(changed_name) if changed_name else None
    if not base or not chg or not tri_base or not tri_chg:
        return {
            "valid": False,
            "pairs": [], "clash_count": 0, "same_count": 0, "he_count": 0,
            "other_count": 0, "full_clash": False, "full_same": False,
            "inner_clash": False, "outer_clash": False,
            "inner_same": False, "outer_same": False,
            "scope": None, "category": None,
        }

    base_upper, base_lower = tri_base
    chg_upper, chg_lower = tri_chg
    inner_trigram_unchanged = base_lower == chg_lower
    outer_trigram_unchanged = base_upper == chg_upper

    clash_set = {frozenset(p) for p in CHONG_PAIRS}
    he_set = {frozenset(p) for p in HE_PAIRS}
    pairs = []
    for idx, (b1, b2) in enumerate(zip(base, chg)):
        if frozenset((b1, b2)) in clash_set:
            rel = "冲"
        elif b1 == b2:
            rel = "同"
        elif frozenset((b1, b2)) in he_set:
            rel = "合"
        else:
            rel = "其他"
        pairs.append({"position": idx + 1, "original": b1, "changed": b2,
                      "relation": rel,
                      "scope": "内卦" if idx < 3 else "外卦"})

    def _scope_all(idx_set, rel):
        return all(p["relation"] == rel for p in pairs if p["position"] - 1 in idx_set)

    inner_idx, outer_idx = (0, 1, 2), (3, 4, 5)
    clash_count = sum(1 for p in pairs if p["relation"] == "冲")
    same_count = sum(1 for p in pairs if p["relation"] == "同")
    he_count = sum(1 for p in pairs if p["relation"] == "合")
    full_clash = clash_count == 6
    full_same = same_count == 6
    inner_clash, outer_clash = _scope_all(inner_idx, "冲"), _scope_all(outer_idx, "冲")
    inner_same, outer_same = _scope_all(inner_idx, "同"), _scope_all(outer_idx, "同")

    # 经卦层面：该半卦是否"经卦未变 + 爻支全同"（真伏吟）／"经卦变了 + 爻支全冲"（真反吟）
    inner_true_fuyin = inner_same and inner_trigram_unchanged
    outer_true_fuyin = outer_same and outer_trigram_unchanged
    inner_najia_same = inner_same and not inner_trigram_unchanged
    outer_najia_same = outer_same and not outer_trigram_unchanged
    inner_true_fanyin = inner_clash and not inner_trigram_unchanged
    outer_true_fanyin = outer_clash and not outer_trigram_unchanged

    if full_clash:
        category = HEXAGRAM_LEVEL_FULL_CLASH
    elif full_same:
        category = HEXAGRAM_LEVEL_FULL_SAME
    elif inner_true_fanyin or outer_true_fanyin or inner_true_fuyin or outer_true_fuyin:
        category = (HEXAGRAM_LEVEL_TRIGRAM_CLASH
                    if (inner_true_fanyin or outer_true_fanyin) else HEXAGRAM_LEVEL_TRIGRAM_SAME)
    elif inner_clash or outer_clash or inner_najia_same or outer_najia_same:
        # 半卦爻支全冲/全同而经卦已易：纳甲同或卦体易，只作"杂反伏"记象
        category = HEXAGRAM_LEVEL_MIXED
    elif clash_count or same_count:
        category = HEXAGRAM_LEVEL_MIXED
    else:
        category = HEXAGRAM_LEVEL_NONE

    scope = {
        "inner_trigram_unchanged": inner_trigram_unchanged,
        "outer_trigram_unchanged": outer_trigram_unchanged,
        "inner_true_fanyin": inner_true_fanyin,
        "outer_true_fanyin": outer_true_fanyin,
        "inner_true_fuyin": inner_true_fuyin,
        "outer_true_fuyin": outer_true_fuyin,
        "inner_najia_same_but_trigram_changed": inner_najia_same,
        "outer_najia_same_but_trigram_changed": outer_najia_same,
    }

    return {
        "valid": True,
        "pairs": pairs,
        "clash_count": clash_count,
        "same_count": same_count,
        "he_count": he_count,
        "other_count": sum(1 for p in pairs if p["relation"] == "其他"),
        "full_clash": full_clash,
        "full_same": full_same,
        "inner_clash": inner_clash,
        "outer_clash": outer_clash,
        "inner_same": inner_same,
        "outer_same": outer_same,
        "scope": scope,
        "category": category,
    }
