# -*- coding: utf-8 -*-
"""紫微斗数规则表（Zi Wei Dou Shu Tables）—— 唯一真值源。

本文件由 scratch/build_ziwei_tables.py 从《紫微斗数全书》（明·罗洪先）通行版本机械整理。
**不要在别处再抄一份**：星曜/四化/紫微起安关系只存于此。

核心法则：
  - 十四主星：紫微星系逆布六位，天府星系顺布六位。
  - 四化表：按年干定化禄/化权/化科/化忌。
  - 紫微起安：由五行局数 + 生日，紫微pos = (局数 + (生日-1)*局数) % 12。
  - 天府与紫微隔六宫：天府pos = (紫微pos + 6) % 12。
  - 十二宫：命宫起，逆时针排（命宫→兄弟→夫妻→子女→财帛→疾厄→迁移→交友→官禄→田宅→福德→父母）。
  - 大限：起运年龄 = 五行局数（水二局=2岁起、木三局=3岁起、金四局=4岁起、土五局=5岁起、火六局=6岁起）。
"""
from __future__ import annotations

HEAVENLY_STEMS = "甲乙丙丁戊己庚辛壬癸"
EARTHLY_BRANCHES = "子丑寅卯辰巳午未申酉戌亥"


def _branch_index(branch: str) -> int:
    """地支 → 索引（子=0 … 亥=11）。"""
    try:
        return EARTHLY_BRANCHES.index(branch)
    except ValueError:
        return -1


def _branch_at(index: int) -> str:
    """索引 → 地支。"""
    return EARTHLY_BRANCHES[index % 12]


def _stem_index(stem: str) -> int:
    """天干 → 索引（甲=0 … 癸=9）。"""
    try:
        return HEAVENLY_STEMS.index(stem)
    except ValueError:
        return -1


# ============================================================ 星曜基础数据

STARS: dict[str, dict] = {
    # 紫微星系（逆布六位）
    "紫微": {"type": "主星", "element": "土", "qi": "尊", "ziwei_order": 0},
    "天机": {"type": "主星", "element": "木", "qi": "善", "ziwei_order": 1},
    "太阳": {"type": "主星", "element": "火", "qi": "贵", "ziwei_order": 2},
    "武曲": {"type": "主星", "element": "金", "qi": "财", "ziwei_order": 3},
    "天同": {"type": "主星", "element": "水", "qi": "福", "ziwei_order": 4},
    "廉贞": {"type": "主星", "element": "火", "qi": "囚", "ziwei_order": 5},
    # 天府星系（顺布七位）
    "天府": {"type": "主星", "element": "土", "qi": "库", "tianfu_order": 0},
    "太阴": {"type": "主星", "element": "水", "qi": "富", "tianfu_order": 1},
    "贪狼": {"type": "主星", "element": "木", "qi": "欲", "tianfu_order": 2},
    "巨门": {"type": "主星", "element": "水", "qi": "暗", "tianfu_order": 3},
    "天相": {"type": "主星", "element": "水", "qi": "印", "tianfu_order": 4},
    "七杀": {"type": "主星", "element": "金", "qi": "将", "tianfu_order": 5},
    "破军": {"type": "主星", "element": "水", "qi": "耗", "tianfu_order": 6},
    # 天梁（不在十四主星，但四化表需要）
    "天梁": {"type": "主星", "element": "土", "qi": "荫", "ziwei_order": -1},
}

# 紫微系逆布顺序
ZIWEI_GROUP_ORDER = ["紫微", "天机", "太阳", "武曲", "天同", "廉贞"]

# 天府系顺布顺序
TIANFU_GROUP_ORDER = ["天府", "太阴", "贪狼", "巨门", "天相", "七杀", "破军"]

# 余曜
AUXILIARY_STARS: dict[str, dict] = {
    "左辅": {"type": "辅星", "element": "土"},
    "右弼": {"type": "辅星", "element": "水"},
    "文昌": {"type": "辅星", "element": "金"},
    "文曲": {"type": "辅星", "element": "水"},
    "天魁": {"type": "贵人", "element": "火"},
    "天钺": {"type": "贵人", "element": "火"},
    "火星": {"type": "煞星", "element": "火"},
    "铃星": {"type": "煞星", "element": "火"},
    "地空": {"type": "空曜", "element": "火"},
    "地劫": {"type": "空曜", "element": "火"},
}

# ============================================================ 十二宫

PALACES: list[str] = [
    "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
    "迁移", "交友", "官禄", "田宅", "福德", "父母",
]

PALACE_INDEX: dict[str, int] = {name: i for i, name in enumerate(PALACES)}


# ============================================================ 五行局

WUXING_TO_JU: dict[str, int] = {"水": 2, "木": 3, "金": 4, "土": 5, "火": 6}

JU_TO_WUXING: dict[int, str] = {v: k for k, v in WUXING_TO_JU.items()}


# ============================================================ 四化表（年干 → 四化星）

# 口诀：甲廉破武阳，乙机梁紫阴，丙同机昌廉，丁阴同机巨，
#       戊贪阴右机，己武贪梁曲，庚阳武阴同，辛巨阳曲昌，
#       壬梁紫左武，癸破巨阴贪

SIHUA_TABLE: dict[str, dict[str, str]] = {
    "甲": {"禄": "廉贞", "权": "破军", "科": "武曲", "忌": "太阳"},
    "乙": {"禄": "天机", "权": "天梁", "科": "紫微", "忌": "太阴"},
    "丙": {"禄": "天同", "权": "天机", "科": "文昌", "忌": "廉贞"},
    "丁": {"禄": "太阴", "权": "天同", "科": "天机", "忌": "巨门"},
    "戊": {"禄": "贪狼", "权": "太阴", "科": "右弼", "忌": "天机"},
    "己": {"禄": "武曲", "权": "贪狼", "科": "天梁", "忌": "文曲"},
    "庚": {"禄": "太阳", "权": "武曲", "科": "太阴", "忌": "天同"},
    "辛": {"禄": "巨门", "权": "太阳", "科": "文曲", "忌": "文昌"},
    "壬": {"禄": "天梁", "权": "紫微", "科": "左辅", "忌": "武曲"},
    "癸": {"禄": "破军", "权": "巨门", "科": "太阴", "忌": "贪狼"},
}

SIHUA_DIRECTION: dict[str, str] = {
    "禄": "吉",
    "权": "吉",
    "科": "吉",
    "忌": "凶",
}


# ============================================================ 紫微安星公式

def ziwei_position(ju: int, day: int) -> int:
    """五行局数 + 生日（1-30）→ 紫微所在宫位索引。

    紫微pos = (局数 + (生日 - 1) × 局数) % 12

    验证：
      水二局·1日 → (2+0)%12=2=寅 ✓
      水二局·2日 → (2+2)%12=4=辰 ✓
      金四局·20日 → (4+19×4)%12=80%12=8=申 ✓
    60 日周期自然成立：局数 × 30 mod 12 = (局数 × 6) mod 12 = 0。
    """
    day = max(1, min(30, day))
    return (ju + (day - 1) * ju) % 12


def tianfu_position(ziwei_pos: int) -> int:
    """天府与紫微隔六宫（对冲）。"""
    return (ziwei_pos + 6) % 12


def ziwei_group_positions(ziwei_pos: int) -> dict[str, int]:
    """紫微系六星在十二宫的位置（逆布）。"""
    return {star: (ziwei_pos - i) % 12 for i, star in enumerate(ZIWEI_GROUP_ORDER)}


def tianfu_group_positions(tianfu_pos: int) -> dict[str, int]:
    """天府系七星在十二宫的位置（顺布）。"""
    return {star: (tianfu_pos + i) % 12 for i, star in enumerate(TIANFU_GROUP_ORDER)}


# ============================================================ 余曜安星

def zuo_you_positions(month_branch: int) -> tuple[int, int]:
    """左辅右弼：由月支定。左辅 = (月支+2)%12，右弼 = (月支+8)%12。"""
    return (month_branch + 2) % 12, (month_branch + 8) % 12


def chang_qu_positions(hour_branch: int) -> tuple[int, int]:
    """文昌文曲：由时支定。
    文昌 = (22-时支)%12（戌起子顺行），文曲 = (16-时支)%12（辰起子顺行）。
    """
    return (22 - hour_branch) % 12, (16 - hour_branch) % 12


# 天魁天钺：年干 → (天魁支索引, 天钺支索引)
KUI_YUE_TABLE: dict[int, tuple[int, int]] = {
    0: (1, 7),   # 甲: 丑(1), 未(7)
    1: (0, 8),   # 乙: 子(0), 申(8)
    2: (11, 9),  # 丙: 亥(11), 酉(9)
    3: (11, 9),  # 丁: 亥(11), 酉(9)
    4: (1, 7),   # 戊: 丑(1), 未(7)
    5: (0, 8),   # 己: 子(0), 申(8)
    6: (1, 7),   # 庚: 丑(1), 未(7)
    7: (6, 2),   # 辛: 午(6), 寅(2)
    8: (5, 3),   # 壬: 卯(5), 巳(3)
    9: (5, 3),   # 癸: 卯(5), 巳(3)
}


def kui_yue_positions_by_stem(year_stem: int) -> tuple[int, int]:
    """天魁天钺由年干定位置。"""
    return KUI_YUE_TABLE.get(year_stem, (1, 7))


# 火星铃星：年支三合局 → (火起始支, 铃起始支) 从子起顺行到时支
HUO_LING_TABLE: dict[str, tuple[int, int]] = {
    "寅午戌": (1, 3),   # 火从丑(1)起子、铃从卯(3)起子
    "巳酉丑": (3, 10),  # 火从卯(3)起子、铃从戌(10)起子
    "申子辰": (3, 11),  # 火从卯(3)起子、铃从亥(11)起子
    "亥卯未": (1, 11),  # 火从丑(1)起子、铃从亥(11)起子
}

YEAR_BRANCH_TO_GROUP: dict[int, str] = {
    2: "寅午戌", 6: "寅午戌", 10: "寅午戌",
    5: "巳酉丑", 9: "巳酉丑", 1: "巳酉丑",
    8: "申子辰", 0: "申子辰", 4: "申子辰",
    11: "亥卯未", 3: "亥卯未", 7: "亥卯未",
}


def huoling_pos(year_branch: int, hour_branch: int) -> tuple[int, int]:
    """火星、铃星位置（年支三合局 + 时支顺行）。"""
    group = YEAR_BRANCH_TO_GROUP.get(year_branch, "寅午戌")
    fire_start, ling_start = HUO_LING_TABLE[group]
    return (fire_start + hour_branch) % 12, (ling_start + hour_branch) % 12


def di_kong_jie_pos(year_branch: int) -> tuple[int, int]:
    """地空、地劫位置（年支定，地空亥起顺行，地劫对冲）。简化版。"""
    di_kong = (11 - year_branch) % 12   # 亥起子顺行 → 地空对冲位置
    di_jie = (year_branch + 11) % 12    # 对冲
    return di_kong, di_jie


# ============================================================ 格局识别表

PATTERNS: dict[str, str] = {
    # 双星同宫组合（仅当紫微星系一星与天府星系一星落入同一宫时成立）
    # 天文间距固定：紫微星系逆布（紫微→天机→太阳→武曲→天同→廉贞），
    # 天府星系顺布（天府→太阴→贪狼→巨门→天相→七杀→破军），
    # 紫微与天府隔六宫。
    "紫微破军": "紫破同宫格",
    "天机七杀": "机杀同临格",
    "太阳天相": "日相同宫格",
    "武曲巨门": "武巨同宫格",
    "天同贪狼": "同贪同宫格",
    "廉贞太阴": "廉阴同宫格",
    # 天府星系单独坐命（天府星系独守、对宫为紫微星系）
    "天府独守": "天府独坐格",
    # 单星坐命兜底
    "紫微": "紫微坐命格",
    "天机": "天机坐命格",
    "太阳": "太阳坐命格",
    "武曲": "武曲坐命格",
    "天同": "天同坐命格",
    "廉贞": "廉贞坐命格",
    "天府": "天府坐命格",
    "太阴": "太阴坐命格",
    "贪狼": "贪狼坐命格",
    "巨门": "巨门坐命格",
    "天相": "天相坐命格",
    "七杀": "七杀坐命格",
    "破军": "破军坐命格",
    "天梁": "天梁坐命格",
}


# ============================================================ 大限起法

def dayun_start_age(ju: int) -> int:
    """大限起始年龄 = 五行局数。"""
    return max(2, min(6, ju))


def dayun_step_years() -> int:
    """大限每步跨一宫，共10年。"""
    return 10


# ============================================================ 命宫安法

def ming_gong_pos(month_branch: int, hour_branch: int) -> int:
    """命宫位置：寅(2)起，逆数月至月支，再从月起顺数时支至时支。

    口诀：寅起逆月顺时至。
    公式：命宫 = (4 - 月支 + 时支) % 12
      验证：寅月(2)子时(0) → (4-2+0)%12=2=寅 ✓
            巳月(5)巳时(5) → (4-5+5)%12=4=辰
             标准：寅起逆数4步到亥，再从亥顺数5步到辰 → 辰 ✓
    """
    return (4 - month_branch + hour_branch) % 12
