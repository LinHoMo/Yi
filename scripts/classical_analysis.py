#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
六爻高级经典分析模块 (Classical Liu Yao Advanced Analysis)
=========================================================
基于火珠林、黄金策、卜筮正宗、增删易等经典文献，
对 liuyao_engine.py 产出的排盘结果进行深层分析。

本模块完全自包含（self-contained），仅依赖 Python 标准库。

主入口函数：
    enhance_reading(result_dict) -> dict

用法：
    from classical_analysis import enhance_reading
    enhanced = enhance_reading(base_result)
    # enhanced['advanced_analysis'] 包含 9 个分析段
"""

# =============================================================================
# 基础数据
# =============================================================================

# 天干
HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 地支
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 地支五行
BRANCH_ELEMENTS = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

# 天干五行
STEM_ELEMENTS = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}

# 八卦基础信息
BAGUA = {
    "乾": {"element": "金"},
    "坤": {"element": "土"},
    "震": {"element": "木"},
    "巽": {"element": "木"},
    "坎": {"element": "水"},
    "离": {"element": "火"},
    "艮": {"element": "土"},
    "兑": {"element": "金"},
}

# 纳甲地支（内卦/外卦，从下到上）
NAJIA_BRANCHES = {
    "乾": {"inner": ["子", "寅", "辰"], "outer": ["午", "申", "戌"]},
    "坤": {"inner": ["未", "巳", "卯"], "outer": ["丑", "亥", "酉"]},
    "震": {"inner": ["子", "寅", "辰"], "outer": ["午", "申", "戌"]},
    "坎": {"inner": ["寅", "辰", "午"], "outer": ["申", "戌", "子"]},
    "艮": {"inner": ["辰", "午", "申"], "outer": ["戌", "子", "寅"]},
    "巽": {"inner": ["丑", "亥", "酉"], "outer": ["未", "巳", "卯"]},
    "离": {"inner": ["卯", "丑", "亥"], "outer": ["酉", "未", "巳"]},
    "兑": {"inner": ["巳", "卯", "丑"], "outer": ["亥", "酉", "未"]},
}

# 八宫系统
EIGHT_PALACES = {
    "乾": {"element": "金", "order": [
        ("乾", "六世"), ("姤", "一世"), ("遁", "二世"), ("否", "三世"),
        ("观", "四世"), ("剥", "五世"), ("晋", "游魂"), ("大有", "归魂"),
    ]},
    "坎": {"element": "水", "order": [
        ("坎", "六世"), ("节", "一世"), ("屯", "二世"), ("既济", "三世"),
        ("革", "四世"), ("丰", "五世"), ("明夷", "游魂"), ("师", "归魂"),
    ]},
    "艮": {"element": "土", "order": [
        ("艮", "六世"), ("贲", "一世"), ("大畜", "二世"), ("损", "三世"),
        ("睽", "四世"), ("履", "五世"), ("中孚", "游魂"), ("渐", "归魂"),
    ]},
    "震": {"element": "木", "order": [
        ("震", "六世"), ("豫", "一世"), ("解", "二世"), ("恒", "三世"),
        ("升", "四世"), ("井", "五世"), ("大过", "游魂"), ("随", "归魂"),
    ]},
    "巽": {"element": "木", "order": [
        ("巽", "六世"), ("小畜", "一世"), ("家人", "二世"), ("益", "三世"),
        ("无妄", "四世"), ("噬嗑", "五世"), ("颐", "游魂"), ("蛊", "归魂"),
    ]},
    "离": {"element": "火", "order": [
        ("离", "六世"), ("旅", "一世"), ("鼎", "二世"), ("未济", "三世"),
        ("蒙", "四世"), ("涣", "五世"), ("讼", "游魂"), ("同人", "归魂"),
    ]},
    "坤": {"element": "土", "order": [
        ("坤", "六世"), ("复", "一世"), ("临", "二世"), ("泰", "三世"),
        ("大壮", "四世"), ("夬", "五世"), ("需", "游魂"), ("比", "归魂"),
    ]},
    "兑": {"element": "金", "order": [
        ("兑", "六世"), ("困", "一世"), ("萃", "二世"), ("咸", "三世"),
        ("蹇", "四世"), ("谦", "五世"), ("小过", "游魂"), ("归妹", "归魂"),
    ]},
}

# 反向查找：卦名 → (宫名, 世代)
PALACE_LOOKUP = {}
for _pname, _pdata in EIGHT_PALACES.items():
    for _hname, _gen in _pdata["order"]:
        PALACE_LOOKUP[_hname] = (_pname, _gen)

# 六十四卦→(上卦, 下卦)
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

# =============================================================================
# 五行关系常量
# =============================================================================

# 五行相生: 木→火→土→金→水→木
SHENG_CYCLE = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
# 反向: 生我者
SHENG_WO = {v: k for k, v in SHENG_CYCLE.items()}

# 五行相克: 木→土→水→火→金→木
KE_CYCLE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
# 反向:  克我者
KE_WO = {v: k for k, v in KE_CYCLE.items()}

# 地支六合
HE_PAIRS = [
    ("子", "丑"), ("寅", "亥"), ("卯", "戌"),
    ("辰", "酉"), ("巳", "申"), ("午", "未"),
]

# 地支六冲
CHONG_PAIRS = [
    ("子", "午"), ("丑", "未"), ("寅", "申"),
    ("卯", "酉"), ("辰", "戌"), ("巳", "亥"),
]

# 地支六破（次于六冲的克害关系）
# 子酉破、午卯破、巳申破、寅亥破、辰丑破、戌未破
# 注意：巳申、寅亥既是六合又是六破 → "合中带破"
BREAK_PAIRS = [
    ("子", "酉"), ("酉", "子"),
    ("午", "卯"), ("卯", "午"),
    ("巳", "申"), ("申", "巳"),
    ("寅", "亥"), ("亥", "寅"),
    ("辰", "丑"), ("丑", "辰"),
    ("戌", "未"), ("未", "戌"),
]

# 三合局
SAN_HE = {
    "水": ["申", "子", "辰"],
    "火": ["寅", "午", "戌"],
    "金": ["巳", "酉", "丑"],
    "木": ["亥", "卯", "未"],
}

# 十二长生表
# key=element, value=[分支以长生起始顺序排列对应 长生→养]
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

# 六亲完整列表
SIX_RELATIONS = ["父母", "官鬼", "子孙", "妻财", "兄弟"]

# 进退神表
# 化进: 顺时针跳两位（yang: 子寅辰午申戌 → 下一步；yin: 亥丑卯巳未酉 → 下一步）
ADVANCE_PAIRS = {
    "子": "寅", "寅": "辰", "辰": "午", "午": "申", "申": "戌", "戌": "子",
    "亥": "丑", "丑": "卯", "卯": "巳", "巳": "未", "未": "酉", "酉": "亥",
}
# 化退: 逆时针跳两位
RETREAT_PAIRS = {v: k for k, v in ADVANCE_PAIRS.items()}

# 墓库对应关系（用于判断入墓）
TOMB_MAP = {
    "火": "戌",   # 火墓在戌
    "水": "辰",   # 水墓在辰
    "木": "未",   # 木墓在未
    "金": "丑",   # 金墓在丑
    "土": "辰",   # 土墓在辰（从水）
}

# 十二长生快速查找表：element → {branch: stage}
# 用于绝处逢生分析（直接用日支索引，无需计算offset）
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

# 三刑规则（卜筮正宗）
# 循环刑三合局：三字全见方成刑，仅见两字为"待刑"
THREE_PUNISHMENTS_CYCLIC = {
    "无恩之刑": ["寅", "巳", "申"],
    "恃势之刑": ["丑", "戌", "未"],
}
# 互刑：两字相见即成刑
THREE_PUNISHMENTS_MUTUAL = {
    "无礼之刑": ("子", "卯"),
}
# 自刑地支
SELF_PUNISHMENTS = ["辰", "午", "酉", "亥"]

# 旧常量保留（向后兼容引用）
THREE_PUNISHMENTS = {
    "无礼之刑": [("子", "卯")],
    "无恩之刑": [("寅", "巳"), ("巳", "申"), ("申", "寅")],
    "恃势之刑": [("丑", "戌"), ("戌", "未"), ("未", "丑")],
    "自刑": ["辰", "午", "酉", "亥"],
}

# =============================================================================
# 六兽分阴阳日 — 协纪辨方书
# =============================================================================

YANG_STEMS = {"甲", "丙", "戊", "庚", "壬"}


def spirit_yin_yang_factor(day_stem: str) -> dict:
    """
    六兽分阴阳日力重。
    返回各六兽的力重系数。

    规则来源：《协纪辨方书》——阳日（甲丙戊庚壬）六兽力重，阴日（乙丁己辛癸）六兽力轻。
    """
    is_yang = day_stem in YANG_STEMS

    if is_yang:
        return {
            "青龙": 1.2,   # 阳日青龙力增，吉上加吉
            "白虎": 1.3,   # 阳日白虎力增，凶者更凶
            "朱雀": 1.2,   # 阳日朱雀口舌更显
            "玄武": 0.8,   # 阳日玄武暗昧被抑
            "勾陈": 1.2,   # 阳日勾陈官非更显
            "螣蛇": 0.9,   # 阳日螣蛇惊恐略抑
        }
    else:
        return {
            "青龙": 0.9,   # 阴日青龙力略减
            "白虎": 0.8,   # 阴日白虎凶焰稍敛
            "朱雀": 0.8,   # 阴日朱雀口舌稍抑
            "玄武": 1.3,   # 阴日玄武暗昧更重
            "勾陈": 0.9,   # 阴日勾陈事缓
            "螣蛇": 1.3,   # 阴日螣蛇惊恐更甚
        }


# =============================================================================
# 六十甲子纳音系统 (Nayin — Sound Elements)
# =============================================================================

NAYIN_TABLE = {
    "甲子": "海中金", "乙丑": "海中金",
    "丙寅": "炉中火", "丁卯": "炉中火",
    "戊辰": "大林木", "己巳": "大林木",
    "庚午": "路旁土", "辛未": "路旁土",
    "壬申": "剑锋金", "癸酉": "剑锋金",
    "甲戌": "山头火", "乙亥": "山头火",
    "丙子": "涧下水", "丁丑": "涧下水",
    "戊寅": "城头土", "己卯": "城头土",
    "庚辰": "白蜡金", "辛巳": "白蜡金",
    "壬午": "杨柳木", "癸未": "杨柳木",
    "甲申": "泉中水", "乙酉": "泉中水",
    "丙戌": "屋上土", "丁亥": "屋上土",
    "戊子": "霹雳火", "己丑": "霹雳火",
    "庚寅": "松柏木", "辛卯": "松柏木",
    "壬辰": "长流水", "癸巳": "长流水",
    "甲午": "沙中金", "乙未": "沙中金",
    "丙申": "山下火", "丁酉": "山下火",
    "戊戌": "平地木", "己亥": "平地木",
    "庚子": "壁上土", "辛丑": "壁上土",
    "壬寅": "金箔金", "癸卯": "金箔金",
    "甲辰": "覆灯火", "乙巳": "覆灯火",
    "丙午": "天河水", "丁未": "天河水",
    "戊申": "大驿土", "己酉": "大驿土",
    "庚戌": "钗钏金", "辛亥": "钗钏金",
    "壬子": "桑柘木", "癸丑": "桑柘木",
    "甲寅": "大溪水", "乙卯": "大溪水",
    "丙辰": "沙中土", "丁巳": "沙中土",
    "戊午": "天上火", "己未": "天上火",
    "庚申": "石榴木", "辛酉": "石榴木",
    "壬戌": "大海水", "癸亥": "大海水",
}

NAYIN_TO_ELEMENT = {
    "海中金": "金", "炉中火": "火", "大林木": "木", "路旁土": "土", "剑锋金": "金",
    "山头火": "火", "涧下水": "水", "城头土": "土", "白蜡金": "金", "杨柳木": "木",
    "泉中水": "水", "屋上土": "土", "霹雳火": "火", "松柏木": "木", "长流水": "水",
    "沙中金": "金", "山下火": "火", "平地木": "木", "壁上土": "土", "金箔金": "金",
    "覆灯火": "火", "天河水": "水", "大驿土": "土", "钗钏金": "金", "桑柘木": "木",
    "大溪水": "水", "沙中土": "土", "天上火": "火", "石榴木": "木", "大海水": "水",
}


def analyze_nayin(result):
    """
    纳音分析 — 返回各柱纳音及其对断卦的象数补充。
    """
    dt = result.get("divination_time", {})
    year_gz = dt.get("year_stem_branch", "")
    month_gz = dt.get("month_stem_branch", "")
    day_gz = dt.get("day_stem_branch", "")
    hour_gz = dt.get("hour_stem_branch", "")

    year_nayin = NAYIN_TABLE.get(year_gz, "未知")
    month_nayin = NAYIN_TABLE.get(month_gz, "未知")
    day_nayin = NAYIN_TABLE.get(day_gz, "未知")
    hour_nayin = NAYIN_TABLE.get(hour_gz, "未知")

    # 日柱纳音取象 — 最核心
    day_nayin_element = NAYIN_TO_ELEMENT.get(day_nayin, "未知")

    return {
        "year_nayin": year_nayin,
        "month_nayin": month_nayin,
        "day_nayin": day_nayin,
        "hour_nayin": hour_nayin,
        "day_nayin_element": day_nayin_element,
        "description": f"日柱{day_gz}纳音{day_nayin}({day_nayin_element})",
    }


# =============================================================================
# 工具函数
# =============================================================================

def _branch_element(branch):
    """获取地支五行"""
    return BRANCH_ELEMENTS.get(branch, "未知")


def determine_six_relation(branch, palace_element):
    """
    根据爻的地支五行确定六亲。
    我(governor) = 宫五行
    生我者=父母, 我生者=子孙, 克我者=官鬼, 我克者=妻财, 同我者=兄弟
    """
    be = _branch_element(branch)
    if be == "未知" or palace_element == "未知":
        return "未知"
    if be == palace_element:
        return "兄弟"
    if SHENG_WO.get(palace_element) == be:
        return "父母"
    if SHENG_CYCLE.get(palace_element) == be:
        return "子孙"
    if KE_WO.get(palace_element) == be:
        return "官鬼"
    if KE_CYCLE.get(palace_element) == be:
        return "妻财"
    return "未知"


def is_ba_zu_he(b1, b2):
    """判断两地支是否六合"""
    for a, b in HE_PAIRS:
        if (b1 == a and b2 == b) or (b1 == b and b2 == a):
            return True
    return False


def is_ba_zu_chong(b1, b2):
    """判断两地支是否六冲"""
    for a, b in CHONG_PAIRS:
        if (b1 == a and b2 == b) or (b1 == b and b2 == a):
            return True
    return False


def element_strength_in_month(element, month_element):
    """
    五行在月建中的旺衰（旺相休囚死）。
    旺: 同月, 相: 月所生, 休: 生月, 囚: 克月, 死: 月克
    """
    if element == month_element:
        return "旺"
    if SHENG_CYCLE.get(month_element) == element:
        return "相"
    if SHENG_CYCLE.get(element) == month_element:
        return "休"
    if KE_CYCLE.get(month_element) == element:
        return "死"
    if KE_CYCLE.get(element) == month_element:
        return "囚"
    return "未知"


def element_strength_text(element, month_element):
    """旺相休囚死完整描述"""
    s = element_strength_in_month(element, month_element)
    return s


def get_twelve_growth_stage(element, day_branch):
    """
    获取某五行元素在指定日支的十二长生阶段。
    返回 (stage_name, index) 或 None（如果branch不在表中）
    """
    table = TWELVE_GROWTH_TABLES.get(element)
    if table is None:
        return None
    try:
        idx = table.index(day_branch)
        return TWELVE_GROWTH_STAGES[idx]
    except ValueError:
        return None


def get_stages_of_interest(stage):
    """判断是否为关键阶段"""
    return stage in ("帝旺", "临官", "长生", "墓", "绝", "死", "沐浴")


def get_changed_hexagram_branch(changed_hex_name, position):
    """
    获取变卦中指定位置(1-6)的地支。
    position: 1=初爻(bottom), ..., 6=上爻(top)
    """
    if changed_hex_name is None:
        return None
    trigrams = HEXAGRAM_TRIGRAMS.get(changed_hex_name)
    if trigrams is None:
        return None
    upper_name, lower_name = trigrams
    if position <= 3:
        # 内卦
        return NAJIA_BRANCHES[lower_name]["inner"][position - 1]
    else:
        # 外卦
        return NAJIA_BRANCHES[upper_name]["outer"][position - 4]


def get_month_strength_description(month_element):
    """
    生成旺相休囚死完整描述文本。
    格式：X旺X相X休X囚X死
    """
    parts = []
    for elem in ["木", "火", "土", "金", "水"]:
        s = element_strength_in_month(elem, month_element)
        parts.append(f"{elem}{s}")
    return "、".join(parts)


# =============================================================================
# 分析段 1：伏藏分析 (基于卜筮正宗)
# =============================================================================

def analyze_hidden_spirits(result):
    """
    伏藏分析：检查六亲是否有缺失，找出伏神、飞神及其得出/不得出。
    
    返回：
        {
            "has_hidden_spirit": bool,
            "details": [
                {
                    "missing_relation": str,        # 缺失的六亲
                    "hidden_spirit": {              # 伏神（来自本宫首卦）
                        "position": int,
                        "branch": str,
                        "six_relation": str,
                        "element": str,
                    },
                    "covering_spirit": {            # 飞神（当前卦中的该位置）
                        "position": int,
                        "branch": str,
                        "six_relation": str,
                        "element": str,
                    },
                    "can_emerge": bool,             # 伏神得出/不得出
                    "reason": str,                  # 得出/不得出判断理由
                },
                ...
            ],
            "summary": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    palace = hex_info.get("palace", "")
    palace_element = hex_info.get("palace_element", "")
    yao_lines = hex_info.get("yao_lines", [])

    if not palace or not yao_lines:
        return {"has_hidden_spirit": False, "details": [], "summary": "无足够数据进行伏藏分析"}

    # 收集本卦已有的六亲
    existing_relations = set()
    for yao in yao_lines:
        rel = yao.get("six_relation", "")
        if rel and rel != "未知":
            existing_relations.add(rel)

    # 找出缺失的六亲
    missing_relations = [r for r in SIX_RELATIONS if r not in existing_relations]

    if not missing_relations:
        return {
            "has_hidden_spirit": False,
            "details": [],
            "summary": "本卦六亲齐备，无伏藏",
        }

    # 本宫首卦（纯卦）的地支
    # 宫殿名即为八卦名，其五行为 palace_element
    # 本宫卦上下皆为该八卦
    if palace not in NAJIA_BRANCHES:
        return {"has_hidden_spirit": True, "details": [], "summary": "宫名异常，无法分析"}

    base_inner = NAJIA_BRANCHES[palace]["inner"]
    base_outer = NAJIA_BRANCHES[palace]["outer"]
    base_branches = base_inner + base_outer  # pos 1-6

    # 获取月建日辰信息
    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    month_element = _branch_element(month_branch)
    day_element = _branch_element(day_branch)
    empty_branches = result.get("empty_branches", [])

    details = []
    yao_by_position = {yao["position"]: yao for yao in yao_lines}

    for missing_rel in missing_relations:
        # 在本宫首卦中找该六亲的位置
        hidden_pos = None
        hidden_branch = None
        hidden_element = None
        for pos_idx, branch in enumerate(base_branches):
            rel = determine_six_relation(branch, palace_element)
            if rel == missing_rel:
                hidden_pos = pos_idx + 1
                hidden_branch = branch
                hidden_element = _branch_element(branch)
                break

        if hidden_pos is None:
            # 不应该发生，但保险
            continue

        # 飞神：本卦中该位置的六亲
        covering_yao = yao_by_position.get(hidden_pos, {})
        covering_relation = covering_yao.get("six_relation", "未知")
        covering_branch = covering_yao.get("earthly_branch", "")
        covering_element = _branch_element(covering_branch)

        # 判断伏神得出/不得出
        can_emerge, reason = _evaluate_hidden_spirit_emergence(
            hidden_element, hidden_branch, covering_relation, covering_branch,
            covering_element, month_branch, day_branch, month_element, day_element,
            empty_branches, yao_by_position.get(hidden_pos, {})
        )

        details.append({
            "missing_relation": missing_rel,
            "hidden_spirit": {
                "position": hidden_pos,
                "name": _pos_to_name(hidden_pos),
                "branch": hidden_branch,
                "six_relation": missing_rel,
                "element": hidden_element,
            },
            "covering_spirit": {
                "position": hidden_pos,
                "name": _pos_to_name(hidden_pos),
                "branch": covering_branch,
                "six_relation": covering_relation,
                "element": covering_element,
            },
            "can_emerge": can_emerge,
            "reason": reason,
        })

    summary_parts = []
    for d in details:
        status = "得出" if d["can_emerge"] else "不得出"
        summary_parts.append(
            f"{d['missing_relation']}伏藏（{d['hidden_spirit']['branch']}）"
            f"飞神{d['covering_spirit']['six_relation']}({d['covering_spirit']['branch']})"
            f"→ {status}"
        )

    return {
        "has_hidden_spirit": True,
        "details": details,
        "summary": "；".join(summary_parts),
    }


def _evaluate_hidden_spirit_emergence(hid_elem, hid_branch, cov_rel, cov_branch,
                                       cov_elem, month_branch, day_branch,
                                       month_elem, day_elem, empty_branches,
                                       covering_yao):
    """
    评估伏神得出/不得出。
    
    得出（吉）：
      - 日/月生伏神
      - 日/月与伏神同五行（持之）
      - 飞神生伏神
      - 日/月/动爻冲克飞神
      - 飞神旬空、月破、休囚
    
    不得出（凶）：
      - 伏神休囚被日月克
      - 飞神旺相克伏神
      - 伏神入墓、逢绝
      - 伏神旬空、月破
    """
    emerge_score = 0
    reasons = []

    # --- 得出条件 ---
    # 1. 日/月生伏神
    if SHENG_CYCLE.get(day_elem) == hid_elem or day_elem == hid_elem:
        emerge_score += 2
        reasons.append(f"日辰{'生' if SHENG_CYCLE.get(day_elem) == hid_elem else '同'}伏神")
    if SHENG_CYCLE.get(month_elem) == hid_elem or month_elem == hid_elem:
        emerge_score += 1
        reasons.append(f"月建{'生' if SHENG_CYCLE.get(month_elem) == hid_elem else '同'}伏神")

    # 2. 飞神生伏神
    if SHENG_CYCLE.get(cov_elem) == hid_elem:
        emerge_score += 2
        reasons.append("飞神生伏神")

    # 3. 飞神旬空
    if cov_branch in empty_branches:
        emerge_score += 1
        reasons.append("飞神旬空")

    # 4. 飞神月破
    if is_ba_zu_chong(cov_branch, month_branch):
        emerge_score += 1
        reasons.append("飞神月破")

    # 5. 飞神休囚
    cov_strength = element_strength_in_month(cov_elem, month_elem)
    if cov_strength in ("休", "囚", "死"):
        emerge_score += 1
        reasons.append(f"飞神{cov_strength}")

    # 6. 伏克飞为出暴（伏神有力反克飞神，出暴为吉）
    if KE_CYCLE.get(hid_elem) == cov_elem:
        emerge_score += 3
        reasons.append("伏克飞为出暴")

    # --- 不得出条件 ---
    # 1. 伏神休囚被日月克
    hid_strength = element_strength_in_month(hid_elem, month_elem)
    if hid_strength in ("死", "囚"):
        emerge_score -= 2
        reasons.append(f"伏神{hid_strength}")

    day_hid_strength = element_strength_in_month(hid_elem, day_elem)
    if day_hid_strength == "死":
        emerge_score -= 2
        reasons.append("日辰克伏神")

    # 2. 飞神旺相克伏神
    if KE_CYCLE.get(cov_elem) == hid_elem:
        cov_strength = element_strength_in_month(cov_elem, month_elem)
        if cov_strength in ("旺", "相"):
            emerge_score -= 3
            reasons.append("飞神旺相克伏神")

    # 3. 伏神入墓
    tomb = TOMB_MAP.get(hid_elem, "")
    if tomb and day_branch == tomb:
        emerge_score -= 2
        reasons.append(f"伏神入墓({tomb})")

    # 4. 伏神逢绝
    stage = get_twelve_growth_stage(hid_elem, day_branch)
    if stage == "绝":
        emerge_score -= 2
        reasons.append("伏神逢绝")

    # 5. 伏神旬空
    if hid_branch in empty_branches:
        emerge_score -= 1
        reasons.append("伏神旬空")

    # 6. 伏神月破
    if is_ba_zu_chong(hid_branch, month_branch):
        emerge_score -= 2
        reasons.append("伏神月破")

    can_emerge = emerge_score > 0
    reason_text = "；".join(reasons) if reasons else "条件平淡"
    return can_emerge, reason_text


# =============================================================================
# 分析段 11（附加）：伏神得出不得出优化评分
# =============================================================================

def analyze_hidden_spirit_emergence(result):
    """
    伏神得出不得出优化版评分。
    基于卜筮正宗四大伏神规则完整实现：

    伏神得出（可出）的条件:
      1. 日辰生扶伏神
      2. 月建生扶伏神
      3. 日冲飞神（冲开飞神）
      4. 月冲飞神
      5. 飞神旬空（空则不挡）
      6. 飞神月破（破则不挡）
      7. 飞神休囚无气
      8. 飞神被日/月/动爻克
      9. 伏神旺相有气

    伏神不得出（难出）的条件:
      1. 伏神被月日双克
      2. 飞神旺相克伏神（飞克伏）
      3. 伏神入墓于日/月
      4. 伏神逢绝地
      5. 伏神旬空
      6. 伏神月破
      7. 伏神休囚无气

    返回：
        {
            "has_hidden_spirit": bool,
            "spirits": [
                {
                    "missing_relation": str,
                    "hidden_branch": str,
                    "covering_branch": str,
                    "can_emerge": bool,
                    "emerge_score": int,
                    "emerge_level": str,    # "极易出"/"可以出"/"难出"/"不得出"
                    "emerge_reasons": [str],
                    "block_reasons": [str],
                    "summary": str,
                },
                ...
            ],
            "summary": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    palace = hex_info.get("palace", "")
    palace_element = hex_info.get("palace_element", "")
    yao_lines = hex_info.get("yao_lines", [])

    if not palace or not yao_lines:
        return {"has_hidden_spirit": False, "spirits": [], "summary": "无足够数据"}

    # 收集本卦已有的六亲
    existing_relations = set()
    for yao in yao_lines:
        rel = yao.get("six_relation", "")
        if rel and rel != "未知":
            existing_relations.add(rel)

    missing_relations = [r for r in SIX_RELATIONS if r not in existing_relations]

    if not missing_relations:
        return {"has_hidden_spirit": False, "spirits": [], "summary": "六亲齐备，无伏藏"}

    # 本宫首卦地支
    if palace not in NAJIA_BRANCHES:
        return {"has_hidden_spirit": True, "spirits": [], "summary": "宫名异常"}

    base_branches = NAJIA_BRANCHES[palace]["inner"] + NAJIA_BRANCHES[palace]["outer"]

    # 月建日辰信息
    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    month_element = _branch_element(month_branch)
    day_element = _branch_element(day_branch)
    empty_branches = result.get("empty_branches", [])

    # 收集动爻地支
    moving_branches = set()
    for yao in yao_lines:
        if yao.get("is_moving", False):
            moving_branches.add(yao.get("earthly_branch", ""))

    yao_by_position = {yao["position"]: yao for yao in yao_lines}

    spirits = []
    for missing_rel in missing_relations:
        hidden_pos = None
        hidden_branch = None
        hidden_element = None
        for pos_idx, branch in enumerate(base_branches):
            rel = determine_six_relation(branch, palace_element)
            if rel == missing_rel:
                hidden_pos = pos_idx + 1
                hidden_branch = branch
                hidden_element = _branch_element(branch)
                break

        if hidden_pos is None:
            continue

        covering_yao = yao_by_position.get(hidden_pos, {})
        covering_branch = covering_yao.get("earthly_branch", "")
        covering_element = _branch_element(covering_branch)

        # === 优化版评分 ===
        emerge_score = 0
        emerge_reasons = []
        block_reasons = []

        # --- 得出条件 ---
        # 1. 日辰生扶伏神
        if SHENG_CYCLE.get(day_element) == hidden_element:
            emerge_score += 3
            emerge_reasons.append(f"日辰{day_branch}({day_element})生伏神{hidden_branch}({hidden_element})")
        elif day_element == hidden_element:
            emerge_score += 2
            emerge_reasons.append(f"日辰{day_branch}与伏神同五行")

        # 2. 月建生扶伏神
        if SHENG_CYCLE.get(month_element) == hidden_element:
            emerge_score += 2
            emerge_reasons.append(f"月建{month_branch}({month_element})生伏神{hidden_branch}")
        elif month_element == hidden_element:
            emerge_score += 1
            emerge_reasons.append(f"月建{month_branch}与伏神同五行")

        # 3. 日冲飞神（冲开飞神）
        if is_ba_zu_chong(covering_branch, day_branch):
            emerge_score += 2
            emerge_reasons.append(f"日冲飞神{covering_branch}（{day_branch}冲{covering_branch}，冲开）")

        # 4. 月冲飞神
        if is_ba_zu_chong(covering_branch, month_branch):
            emerge_score += 1
            emerge_reasons.append(f"月冲飞神{covering_branch}（{month_branch}冲{covering_branch}）")

        # 5. 飞神旬空（空则不挡）
        if covering_branch in empty_branches:
            emerge_score += 2
            emerge_reasons.append(f"飞神{covering_branch}旬空")

        # 6. 飞神月破（破则不挡）
        if is_ba_zu_chong(covering_branch, month_branch):
            emerge_score += 2
            emerge_reasons.append(f"飞神{covering_branch}月破")

        # 7. 飞神休囚无气
        cov_strength = element_strength_in_month(covering_element, month_element)
        if cov_strength in ("休", "囚", "死"):
            emerge_score += 1
            emerge_reasons.append(f"飞神{covering_branch}休囚({cov_strength})")

        # 8. 飞神被日/月/动爻克
        day_attacks_cov = KE_CYCLE.get(day_element) == covering_element
        month_attacks_cov = KE_CYCLE.get(month_element) == covering_element
        moving_attacks_cov = False
        for mb in moving_branches:
            if KE_CYCLE.get(_branch_element(mb)) == covering_element:
                moving_attacks_cov = True
                break
        if day_attacks_cov:
            emerge_score += 1
            emerge_reasons.append(f"日辰{g_day_cn(day_element)}克飞神{g_day_cn(covering_element)}")
        if month_attacks_cov:
            emerge_score += 1
            emerge_reasons.append(f"月建{g_day_cn(month_element)}克飞神{g_day_cn(covering_element)}")
        if moving_attacks_cov:
            emerge_score += 1
            emerge_reasons.append("动爻克飞神")

        # 9. 伏神旺相有气
        hid_strength = element_strength_in_month(hidden_element, month_element)
        if hid_strength == "旺":
            emerge_score += 2
            emerge_reasons.append(f"伏神{hidden_branch}旺相")
        elif hid_strength == "相":
            emerge_score += 1
            emerge_reasons.append(f"伏神{hidden_branch}有气")

        # --- 不得出条件 ---
        # 1. 伏神被月日双克
        hid_day_strength = element_strength_in_month(hidden_element, day_element)
        if hid_strength == "死" and hid_day_strength == "死":
            emerge_score -= 4
            block_reasons.append(f"伏神{hidden_branch}被月日双克")

        # 2. 飞神旺相克伏神（飞克伏）
        if KE_CYCLE.get(covering_element) == hidden_element:
            if cov_strength in ("旺", "相"):
                emerge_score -= 3
                block_reasons.append(f"飞神{covering_branch}({covering_element})旺相克伏神{hidden_branch}({hidden_element})")

        # 3. 伏神入墓
        tomb = TOMB_MAP.get(hidden_element, "")
        if tomb and (day_branch == tomb or month_branch == tomb):
            emerge_score -= 2
            block_reasons.append(f"伏神{hidden_branch}入墓于{tomb}")

        # 4. 伏神逢绝
        stage = get_twelve_growth_stage(hidden_element, day_branch)
        if stage == "绝":
            emerge_score -= 2
            block_reasons.append(f"伏神{hidden_branch}逢绝地(日辰{day_branch})")

        # 5. 伏神旬空
        if hidden_branch in empty_branches:
            emerge_score -= 2
            block_reasons.append(f"伏神{hidden_branch}旬空")

        # 6. 伏神月破
        if is_ba_zu_chong(hidden_branch, month_branch):
            emerge_score -= 2
            block_reasons.append(f"伏神{hidden_branch}月破")

        # 7. 伏神休囚无气
        if hid_strength in ("休", "囚", "死"):
            emerge_score -= 1
            block_reasons.append(f"伏神{hidden_branch}休囚无气({hid_strength})")

        # 判断得出/不得出
        can_emerge = emerge_score > 0
        if emerge_score >= 4:
            emerge_level = "极易出"
        elif emerge_score >= 2:
            emerge_level = "可以出"
        elif emerge_score >= 0:
            emerge_level = "勉强得出"
        elif emerge_score >= -2:
            emerge_level = "难出"
        else:
            emerge_level = "不得出"

        all_reasons = emerge_reasons + block_reasons
        reason_text = "；".join(all_reasons) if all_reasons else "条件平淡"

        spirit_pos_name = _pos_to_name(hidden_pos)
        spirits.append({
            "missing_relation": missing_rel,
            "hidden_branch": hidden_branch,
            "covering_branch": covering_branch,
            "can_emerge": can_emerge,
            "emerge_score": emerge_score,
            "emerge_level": emerge_level,
            "emerge_reasons": emerge_reasons,
            "block_reasons": block_reasons,
            "summary": (
                f"{missing_rel}伏{hidden_branch}于{covering_branch}之下，"
                f"飞神{cov_strength}，伏神{hid_strength}，"
                f"得出评分={emerge_score}({emerge_level})"
            ),
        })

    if not spirits:
        return {"has_hidden_spirit": False, "spirits": [], "summary": "无需分析"}

    summary_parts = [s["summary"] for s in spirits]
    return {
        "has_hidden_spirit": True,
        "spirits": spirits,
        "summary": "；".join(summary_parts),
    }


def g_day_cn(element):
    """五行中文名辅助"""
    return element


def _pos_to_name(pos):
    """位置数字转为中文名称（1→初爻, 6→上爻）"""
    names = {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}
    return names.get(pos, f"{pos}爻")


# =============================================================================
# 分析段 2：暗动分析
# =============================================================================

def analyze_hidden_movement(result):
    """
    暗动分析：静爻逢日冲且旺相=暗动；静爻旬空逢日冲=冲空则实。
    
    返回：
        {
            "has_hidden_movement": bool,
            "details": [
                {
                    "position": int,
                    "name": str,
                    "branch": str,
                    "element": str,
                    "six_relation": str,
                    "type": str,          # "暗动" or "冲空则实"
                    "strength": str,       # 旺相休囚死 based on month+day
                    "description": str,
                },
                ...
            ],
            "summary": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    if not yao_lines:
        return {"has_hidden_movement": False, "details": [], "summary": "无数据"}

    dt = result.get("divination_time", {})
    day_sb = dt.get("day_stem_branch", "")
    month_sb = dt.get("month_stem_branch", "")
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    if not day_branch:
        return {"has_hidden_movement": False, "details": [], "summary": "无日辰数据"}

    day_element = _branch_element(day_branch)
    month_element = _branch_element(month_branch)
    empty_branches = result.get("empty_branches", [])

    details = []
    for yao in yao_lines:
        if yao.get("is_moving", False):
            continue  # 只分析静爻

        branch = yao.get("earthly_branch", "")
        if not branch:
            continue

        # 判断是否被日冲
        if is_ba_zu_chong(branch, day_branch):
            is_empty = branch in empty_branches
            elem = _branch_element(branch)

            # 计算旺衰：综合月建+日辰
            m_strength = element_strength_in_month(elem, month_element)
            d_strength = element_strength_in_month(elem, day_element)

            # 综合判断：月建日辰综合
            overall = _combined_strength(elem, month_element, day_element)

            if is_empty and day_branch:
                line_type = "冲空则实"
                effect_strength = "实"
                line_score = 1.0
                desc = f"{_pos_to_name(yao['position'])}({branch}旬空)被日辰{day_branch}冲，冲空则实，此爻由虚转实"
            elif overall in ("旺", "相"):
                line_type = "暗动(旺相，七分布动)"
                effect_strength = "强"
                line_score = 0.7
                desc = (
                    f"{_pos_to_name(yao['position'])}({branch})静爻被日辰{day_branch}冲，"
                    f"旺相暗动，其力约当明动七成"
                )
            elif overall == "中和":
                line_type = "暗动(中和，中力)"
                effect_strength = "中"
                line_score = 0.4
                desc = (
                    f"{_pos_to_name(yao['position'])}({branch})静爻被日辰{day_branch}冲，"
                    f"中和暗动，力量中等"
                )
            elif overall == "偏弱":
                line_type = "暗动(休囚，三分力)"
                effect_strength = "弱"
                line_score = 0.2
                desc = (
                    f"{_pos_to_name(yao['position'])}({branch})静爻被日辰{day_branch}冲，"
                    f"休囚暗动，力微短暂"
                )
            else:  # "衰"
                line_type = "日破(月休逢冲，此爻无用)"
                effect_strength = "无"
                line_score = 0.0
                desc = (
                    f"{_pos_to_name(yao['position'])}({branch})静爻被日辰{day_branch}冲，"
                    f"月休囚逢冲为日破，此爻彻底无用"
                )

            details.append({
                "position": yao["position"],
                "name": yao.get("name", ""),
                "branch": branch,
                "element": elem,
                "six_relation": yao.get("six_relation", ""),
                "six_spirit": yao.get("six_spirit", ""),
                "type": line_type,
                "effect_strength": effect_strength,
                "line_score": line_score,
                "month_strength": m_strength,
                "day_strength": d_strength,
                "overall_strength": overall,
                "is_day_break": (line_score == 0.0),
                "description": desc,
            })

    if not details:
        return {"has_hidden_movement": False, "details": [], "summary": "本卦无暗动之爻"}

    summary = "；".join(d["description"] for d in details)
    return {"has_hidden_movement": True, "details": details, "summary": summary}


def _combined_strength(element, month_element, day_element):
    """
    综合月建日辰判断旺衰：日辰权重更高。
    """
    m = element_strength_in_month(element, month_element)
    d = element_strength_in_month(element, day_element)

    # 力量等级: 旺=5, 相=4, 休=3, 囚=2, 死=1
    strength_val = {"旺": 5, "相": 4, "休": 3, "囚": 2, "死": 1, "未知": 0}
    total = strength_val.get(m, 0) + strength_val.get(d, 0)

    if total >= 9:
        return "旺"
    elif total >= 7:
        return "相"
    elif total >= 5:
        return "中和"
    elif total >= 3:
        return "偏弱"
    else:
        return "衰"


# =============================================================================
# 分析段 2b：游魂归魂卦特殊断法 (Gap 7)
# =============================================================================

def analyze_wandering_returning_soul(result):
    """
    游魂归魂卦特殊断法。

    游魂卦/归魂卦是各宫第7、8卦，具有特殊的卦类特质：
    - 游魂：行无定、忧疑不安、心无归宿
    - 归魂：回故乡、有归属、终有所归

    参考《卜筮正宗》：
    > "游魂行无定，归魂回故乡。"
    > "游魂卦主在外、不安、忧疑、反复。"
    > "归魂卦主在内、有归、安定、终有所归。"

    此分析不改变评分（score_adjustment=0），仅提供断卦方向指引。

    返回:
        {
            "is_soul_hexagram": bool,
            "soul_type": str or None,       # "游魂" / "归魂" / None
            "meaning": str,                  # 卦类整体含义
            "travel": str,                   # 出行断法
            "residence": str,                # 居家断法
            "mind": str,                     # 心境断法
            "score_adjustment": 0,           # 不改变评分
        }
    """
    hex_info = result.get("original_hexagram", {})
    hex_name = hex_info.get("name", "")
    generation = hex_info.get("generation", "")

    # 游魂/归魂的卦类特质
    SOUL_GEN = {
        "游魂": {
            "meaning": "游魂行无定，事主忧疑不定，心无归宿",
            "travel": "行无方、四处飘荡、不定",
            "residence": "不安于室，思迁",
            "mind": "忧疑不决，心思散乱",
        },
        "归魂": {
            "meaning": "归魂回故乡，事主有归宿，终有所归",
            "travel": "归期可定，终有所返",
            "residence": "安居乐业，归家安定",
            "mind": "疑虑消解，心有所属",
        },
    }

    soul_data = SOUL_GEN.get(generation)

    if soul_data:
        return {
            "is_soul_hexagram": True,
            "soul_type": generation,
            "meaning": soul_data["meaning"],
            "travel": soul_data["travel"],
            "residence": soul_data["residence"],
            "mind": soul_data["mind"],
            "summary": f"{generation}卦——{soul_data['meaning']}。事多{'往复飘摇，暂难定居' if generation == '游魂' else '反复纠结，终有归依'}",
            "score_adjustment": 0,  # 不改变评分——仅为断卦方向指引
        }

    return {
        "is_soul_hexagram": False,
        "soul_type": None,
        "meaning": "本卦非游魂归魂主事卦，不以游魂归魂论断",
        "travel": "无游魂归魂特征",
        "residence": "无游魂归魂特征",
        "mind": "无游魂归魂特征",
        "summary": "非游魂归魂卦——事态以常规世应生克为断，不涉飘泊依附之象",
        "score_adjustment": 0,
    }


# =============================================================================
# 分析段 3：月破分析
# =============================================================================

def analyze_monthly_break(result):
    """
    月破分析：某爻地支被月建冲则为月破。
    
    返回：
        {
            "has_monthly_break": bool,
            "details": [
                {
                    "position": int,
                    "name": str,
                    "branch": str,
                    "element": str,
                    "six_relation": str,
                    "is_moving": bool,
                    "is_empty": bool,
                    "day_branch": str,
                    "both_broken": bool,    # 同时被日冲+月冲
                    "salvageable": bool,    # 是否可救（日辰生扶或旺相）
                    "description": str,
                },
                ...
            ],
            "summary": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    if not yao_lines:
        return {"has_monthly_break": False, "details": [], "summary": "无数据"}

    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    if not month_branch:
        return {"has_monthly_break": False, "details": [], "summary": "无月建数据"}

    day_element = _branch_element(day_branch)
    month_element = _branch_element(month_branch)
    empty_branches = result.get("empty_branches", [])

    details = []
    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        if not branch:
            continue

        if is_ba_zu_chong(branch, month_branch):
            elem = _branch_element(branch)
            is_moving = yao.get("is_moving", False)
            is_empty = branch in empty_branches
            both_broken = is_ba_zu_chong(branch, day_branch)

            # 判断是否有救
            salvageable = False
            month_str = element_strength_in_month(elem, month_element)
            day_str = element_strength_in_month(elem, day_element)

            # 日辰生扶或旺相可救
            if day_str in ("旺", "相"):
                salvageable = True
            if SHENG_WO.get(day_element) == elem or SHENG_CYCLE.get(day_element) == elem:
                # 日辰生之
                salvageable = True

            desc_parts = []
            if both_broken:
                desc_parts.append(
                    f"{_pos_to_name(yao['position'])}({branch})既破于月建又冲于日辰，力量极弱"
                )
            else:
                desc_parts.append(
                    f"{_pos_to_name(yao['position'])}({branch})为月破之爻"
                )

            if salvageable:
                desc_parts.append(f"但得日辰{day_branch}生扶，尚可补救")
            else:
                desc_parts.append("无解救之力")

            if is_moving:
                desc_parts.append("动爻月破，力量减半")
            if is_empty:
                desc_parts.append("又逢旬空，更为无力")

            relation_str = yao.get("six_relation", "")
            details.append({
                "position": yao["position"],
                "name": yao.get("name", ""),
                "branch": branch,
                "element": elem,
                "six_relation": relation_str,
                "six_spirit": yao.get("six_spirit", ""),
                "is_moving": is_moving,
                "is_empty": is_empty,
                "month_branch": month_branch,
                "day_branch": day_branch,
                "both_broken": both_broken,
                "month_strength": month_str,
                "day_strength": day_str,
                "salvageable": salvageable,
                "description": "，".join(desc_parts),
            })

    if not details:
        return {"has_monthly_break": False, "details": [], "summary": "本卦无月破之爻"}

    summary = "；".join(d["description"] for d in details)
    return {"has_monthly_break": True, "details": details, "summary": summary}


# =============================================================================
# 分析段 4：三合局分析
# =============================================================================

def _check_broken_combo(combo_dict, day_branch, month_branch):
    """
    检查一个已完成的三合局是否被破坏。

    破局条件（《卜筮正宗》）：
      - 合局中一字被日/月冲 → 局破
      - 合局中一字入墓/逢绝 → 局力大减

    参数:
        combo_dict: {"element": str, "branches": [str,str,str], ...}
        day_branch: 日辰地支
        month_branch: 月建地支

    返回:
        {"status": "破局"/"完整", "issues": [...], "score_mod": float}
    """
    branches = combo_dict.get("branches", [])

    # 六冲映射
    CHONG_MAP = {
        "子": "午", "午": "子", "丑": "未", "未": "丑",
        "寅": "申", "申": "寅", "卯": "酉", "酉": "卯",
        "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
    }

    # 各五行入墓地支
    TOMB_MAP = {"金": "丑", "木": "未", "火": "戌", "水": "辰", "土": "辰"}

    issues = []

    for b in branches:
        # 检查日冲
        if CHONG_MAP.get(b) == day_branch:
            issues.append(f"{b}被日冲，合局不稳")
        elif CHONG_MAP.get(b) == month_branch:
            issues.append(f"{b}被月冲，合局有隙")

    # 检查合局五行是否整体入墓于日辰
    target_element = combo_dict.get("element", "")
    if target_element and day_branch == TOMB_MAP.get(target_element, ""):
        issues.append(f"合局入墓于{day_branch}，局力不显")

    if issues:
        return {"status": "破局", "severity": "减力", "issues": issues, "score_mod": -0.5}
    return {"status": "完整", "issues": [], "score_mod": 0}


def analyze_triple_combo(result):
    """
    三合局分析：检查是否存在申子辰(水)、寅午戌(火)、巳酉丑(金)、亥卯未(木)。
    增加破局检测：合局中一字被日/月冲或入墓时判定为破局。
    
    返回：
        {
            "has_triple_combo": bool,
            "details": [
                {
                    "element": str,         # 合局五行
                    "branches": [str, str, str],  # 合局三地支
                    "positions": [int, int, int], # 出现在哪些位置
                    "completeness": str,    # "完整"/"待日"/"待月"
                    "formation_type": str,  # "三爻齐发"/"二爻动+一静"/"二爻动+日/月补"
                    "description": str,
                },
                ...
            ],
            "summary": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    if not yao_lines:
        return {"has_triple_combo": False, "details": [], "summary": "无数据"}

    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""

    # 收集每个位置的地支和是否明动/暗动
    pos_branch = {}
    pos_moving = {}
    pos_hidden_move = {}  # 是否是暗动

    moving_positions = set()
    for yao in yao_lines:
        pos = yao.get("position", 0)
        branch = yao.get("earthly_branch", "")
        pos_branch[pos] = branch
        is_moving = yao.get("is_moving", False)
        pos_moving[pos] = is_moving
        if is_moving:
            moving_positions.add(pos)

    # 检查暗动
    hidden_move = set()
    for yao in yao_lines:
        pos = yao.get("position", 0)
        if pos_moving.get(pos, False):
            continue
        branch = yao.get("earthly_branch", "")
        if branch and is_ba_zu_chong(branch, day_branch):
            hidden_move.add(pos)

    # 所有有力爻的位置（明动 + 暗动）
    active_positions = moving_positions | hidden_move
    # 也包括静爻（三合可以以静爻参与），但我们只需要确认静爻有对应地支即可

    details = []

    for combo_element, combo_branches in SAN_HE.items():
        b1, b2, b3 = combo_branches

        # 找到每个地支在本卦中出现的位置
        pos_map = {b: [] for b in combo_branches}
        for pos, branch in pos_branch.items():
            if branch in pos_map:
                pos_map[branch].append(pos)

        # 检查是否能形成三合
        # 需要 b1, b2, b3 各至少在一个位置出现
        if any(len(pos_map[b]) == 0 for b in combo_branches):
            # 检查是否能由日/月补齐
            locations = {b: pos_map[b] for b in combo_branches if pos_map[b]}
            if len(locations) == 2:
                # 缺一个，看日/月是否有
                missing = [b for b in combo_branches if not pos_map[b]][0]
                if missing in (day_branch, month_branch):
                    # 由日/月补齐
                    valid_positions = []
                    for b in combo_branches:
                        if pos_map[b]:
                            valid_positions.append(pos_map[b][0])
                        elif b == day_branch:
                            valid_positions.append(f"日({day_branch})")
                        elif b == month_branch:
                            valid_positions.append(f"月({month_branch})")

                    # 需要至少两个明动的爻才成局
                    actual_pos = [p for p in valid_positions if isinstance(p, int)]
                    if len(actual_pos) >= 2:
                        formation = "二爻动+日/月补"
                        _combo_d = {
                            "element": combo_element,
                            "branches": combo_branches,
                        }
                        _broken = _check_broken_combo(_combo_d, day_branch, month_branch)
                        _desc = (
                            f"{''.join(combo_branches)}合{combo_element}局，"
                            f"由日辰{day_branch}或月建{month_branch}补齐，"
                            f"力量稍逊但仍有合力"
                        )
                        if _broken["status"] == "破局":
                            _desc += f"。⚠破局：{'；'.join(_broken['issues'])}"
                        details.append({
                            "element": combo_element,
                            "branches": combo_branches,
                            "positions": valid_positions,
                            "completeness": "待日/月",
                            "formation_type": formation,
                            "combo_status": _broken["status"],
                            "combo_issues": _broken["issues"],
                            "combo_score_mod": _broken["score_mod"],
                            "description": _desc,
                        })
            continue

        # 三个地支都在本卦中
        # 取第一个出现的位置
        p1 = pos_map[b1][0]
        p2 = pos_map[b2][0]
        p3 = pos_map[b3][0]
        positions = [p1, p2, p3]

        # 判断参与方式：几个明动？几个暗动？几个静？
        moving_count = sum(1 for p in positions if p in moving_positions)
        hidden_count = sum(1 for p in positions if p in hidden_move)
        static_count = sum(1 for p in positions
                          if p not in moving_positions and p not in hidden_move)

        if moving_count >= 2 and hidden_count + static_count == 1:
            ftype = "二爻动+一静"
            completeness = "完整" if hidden_count == 0 and static_count == 1 else "完整"
        elif moving_count == 3:
            ftype = "三爻齐发"
            completeness = "完整"
        elif moving_count >= 1 or hidden_count >= 1:
            ftype = f"{moving_count}爻动+{hidden_count}暗动+{static_count}静"
            completeness = "完整"
        else:
            ftype = "三爻皆静"
            # 三个静爻三合，名为"合局待用"，需日/月引动
            completeness = "待用（需冲引发）"

        # 如果有静爻但被暗动减轻
        _combo_d = {
            "element": combo_element,
            "branches": combo_branches,
        }
        _broken = _check_broken_combo(_combo_d, day_branch, month_branch)

        desc = (
            f"{''.join(combo_branches)}成{combo_element}局，"
            f"位置{_pos_to_name(p1)}/{_pos_to_name(p2)}/{_pos_to_name(p3)}，"
            f"构成方式：{ftype}"
        )

        if completeness == "完整":
            desc += f"。{combo_element}力大增"
        elif completeness == "待用（需冲引发）":
            desc += "。静爻合局，待时日引发方成"

        if _broken["status"] == "破局":
            desc += f"。⚠破局：{'；'.join(_broken['issues'])}"

        details.append({
            "element": combo_element,
            "branches": combo_branches,
            "positions": sorted(positions),
            "completeness": completeness,
            "formation_type": ftype,
            "moving_count": moving_count,
            "hidden_count": hidden_count,
            "static_count": static_count,
            "combo_status": _broken["status"],
            "combo_issues": _broken["issues"],
            "combo_score_mod": _broken["score_mod"],
            "description": desc,
        })

    if not details:
        return {"has_triple_combo": False, "details": [], "summary": "本卦无三合局"}

    summary = "；".join(d["description"] for d in details)
    return {"has_triple_combo": True, "details": details, "summary": summary}


# =============================================================================
# 分析段 5：进退神分析 (基于增删易)
# =============================================================================

def _strength_score(level):
    """
    将旺衰等级转换为数值评分（用于进退神量化）。
    旺=5, 相=4, 中和=3, 偏弱=2, 衰=0
    """
    return {"旺": 5, "相": 4, "中和": 3, "偏弱": 2, "衰": 0}.get(level, 2)


def analyze_advance_retreat(result):
    """
    进出神分析：动爻化进则势盛，化退则势衰。
    
    返回：
        {
            "has_advance_retreat": bool,
            "details": [
                {
                    "position": int,
                    "name": str,
                    "original_branch": str,
                    "changed_branch": str,
                    "type": "化进" or "化退" or "回头合" or "回头克" or "回头生" or "化泄" or "无进退",
                    "six_relation": str,
                    "six_spirit": str,
                    "description": str,
                },
                ...
            ],
            "summary": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    changed = result.get("changed_hexagram") or {}
    changed_name = changed.get("name")

    if not yao_lines or not changed_name:
        return {"has_advance_retreat": False, "details": [], "summary": "无动爻或无变卦"}

    # 获取月建日辰五行用于旺衰评分
    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    month_elem = BRANCH_ELEMENTS.get(month_branch, "")
    day_elem = BRANCH_ELEMENTS.get(day_branch, "")

    details = []
    for yao in yao_lines:
        if not yao.get("is_moving", False):
            continue

        pos = yao.get("position", 0)
        orig_branch = yao.get("earthly_branch", "")

        # 变卦中该位置的地支
        chg_branch = get_changed_hexagram_branch(changed_name, pos)
        if not chg_branch:
            continue

        # 判断进退
        advance_score = 0.0
        if ADVANCE_PAIRS.get(orig_branch) == chg_branch:
            advance_type = "化进"
            desc = (
                f"{_pos_to_name(pos)}({orig_branch}→{chg_branch})"
                f"化进神，力量递增，事态向前发展顺利"
            )
        elif RETREAT_PAIRS.get(orig_branch) == chg_branch:
            advance_type = "化退"
            desc = (
                f"{_pos_to_name(pos)}({orig_branch}→{chg_branch})"
                f"化退神，力量递减，事态逐渐后退/消退"
            )
        else:
            # 检查 回头合/回头克/回头生/化泄
            orig_elem = BRANCH_ELEMENTS.get(orig_branch, "")
            chg_elem = BRANCH_ELEMENTS.get(chg_branch, "")
            he_pair_match = ((orig_branch, chg_branch) in HE_PAIRS or
                             (chg_branch, orig_branch) in HE_PAIRS)
            if he_pair_match:
                advance_type = "回头合"
                desc = (
                    f"{_pos_to_name(pos)}({orig_branch}→{chg_branch})"
                    f"回头合（合住事态胶着）"
                )
            elif KE_CYCLE.get(chg_elem) == orig_elem:
                advance_type = "回头克"
                desc = (
                    f"{_pos_to_name(pos)}({orig_branch}→{chg_branch})"
                    f"回头克（大凶）"
                )
            elif SHENG_CYCLE.get(chg_elem) == orig_elem:
                advance_type = "回头生"
                desc = (
                    f"{_pos_to_name(pos)}({orig_branch}→{chg_branch})"
                    f"回头生（有救济）"
                )
            elif SHENG_CYCLE.get(orig_elem) == chg_elem:
                advance_type = "化泄"
                desc = (
                    f"{_pos_to_name(pos)}({orig_branch}→{chg_branch})"
                    f"化泄（力量消散）"
                )
            else:
                advance_type = "无进退"
                desc = (
                    f"{_pos_to_name(pos)}({orig_branch}→{chg_branch})"
                    f"不涉及进退神，需结合其他因素分析"
                )

        # ── 进退神五行力量量化（《增删卜易》） ──
        orig_elem = BRANCH_ELEMENTS.get(orig_branch, "")
        chg_elem = BRANCH_ELEMENTS.get(chg_branch, "")

        advance_orig_strength = _combined_strength(orig_elem, month_elem, day_elem)
        advance_orig_val = _strength_score(advance_orig_strength)
        advance_chg_strength = _combined_strength(chg_elem, month_elem, day_elem)
        advance_chg_val = _strength_score(advance_chg_strength)

        if advance_type == "化进":
            base_score = 2.0
            if advance_orig_val >= 4:
                base_score += 1.0  # 旺进有力
            elif advance_orig_val <= 2:
                base_score -= 0.5  # 休囚进而力微
            if advance_chg_val >= 4:
                base_score += 0.5  # 变爻旺，力量传导强
            # 逢冲减半
            if is_ba_zu_chong(orig_branch, day_branch) or is_ba_zu_chong(orig_branch, month_branch):
                base_score *= 0.5
                desc += "，逢冲减半"
            advance_score = base_score

        elif advance_type == "化退":
            base_score = -2.0
            if advance_orig_val >= 4:
                base_score += 0.5  # 旺退力弱（减衰减缓）
            elif advance_orig_val <= 2:
                base_score -= 0.5  # 休囚退而更凶
            if advance_chg_val <= 1:
                base_score -= 0.5  # 退入绝地，更凶
            # 逢冲加速退
            if is_ba_zu_chong(chg_branch, day_branch):
                base_score *= 0.7
                desc += "，逢冲加速退"
            advance_score = base_score

        details.append({
            "position": pos,
            "name": yao.get("name", ""),
            "original_branch": orig_branch,
            "changed_branch": chg_branch,
            "type": advance_type,
            "six_relation": yao.get("six_relation", ""),
            "six_spirit": yao.get("six_spirit", ""),
            "advance_score": advance_score,
            "advance_orig_strength": advance_orig_strength,
            "advance_chg_strength": advance_chg_strength,
            "description": desc,
        })

    if not details:
        return {"has_advance_retreat": False, "details": [], "summary": "无有效进退神分析"}

    summary = "；".join(d["description"] for d in details)
    return {"has_advance_retreat": True, "details": details, "summary": summary}


# =============================================================================
# 分析段 6：十二长生分析
# =============================================================================

def analyze_twelve_growth(result):
    """
    十二长生分析：各爻在十二长生中的位置。
    
    返回：
        {
            "day_branch": str,
            "day_element": str,
            "lines": [
                {
                    "position": int,
                    "name": str,
                    "branch": str,
                    "element": str,
                    "six_relation": str,
                    "growth_stage": str,
                    "is_key_stage": bool,
                    "stage_meaning": str,
                },
                ...
            ],
            "summary": str,
            "key_lines": [int],  # 处于帝旺/长生/临官的关键爻位
            "weak_lines": [int], # 处于死/墓/绝的弱爻位
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    if not yao_lines:
        return {"day_branch": "", "day_element": "", "lines": [],
                "summary": "无数据", "key_lines": [], "weak_lines": []}

    dt = result.get("divination_time", {})
    day_sb = dt.get("day_stem_branch", "")
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    if not day_branch:
        return {"day_branch": "", "day_element": "", "lines": [],
                "summary": "无日辰数据", "key_lines": [], "weak_lines": []}

    day_element = _branch_element(day_branch)
    empty_branches = result.get("empty_branches", [])

    # 关键阶段含义
    stage_meaning = {
        "长生": "新生之象，事有先机，力量初萌",
        "沐浴": "初生柔嫩，需防贻害，纯正尚待时日",
        "冠带": "渐趋成熟，力量渐增，气色渐隆",
        "临官": "正当显达，力量充实，可担重任",
        "帝旺": "极盛之时，力量最旺，盛极将衰之先",
        "衰": "物极必反，力量开始减退",
        "病": "力不从心，内耗渐显，弊端初露",
        "死": "气数已尽，力量极微，难以作为",
        "墓": "收藏归库，力量隐伏，待冲开方可",
        "绝": "绝地无援，力量极弱，最难施为",
        "胎": "孕育新机，力量暗藏，有复生之机",
        "养": "休养恢复，力量渐聚，新生在前",
    }

    lines_out = []
    key_lines = []
    weak_lines = []

    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        elem = _branch_element(branch)
        stage = get_twelve_growth_stage(elem, day_branch)
        is_key = get_stages_of_interest(stage)

        is_weak_stage = stage in ("死", "墓", "绝")
        is_strong_stage = stage in ("帝旺", "临官", "长生")

        if is_weak_stage:
            weak_lines.append(yao["position"])
        if is_strong_stage:
            key_lines.append(yao["position"])

        lines_out.append({
            "position": yao["position"],
            "name": yao.get("name", ""),
            "branch": branch,
            "element": elem,
            "six_relation": yao.get("six_relation", ""),
            "growth_stage": stage,
            "is_key_stage": is_key,
            "stage_meaning": stage_meaning.get(stage, ""),
        })

    # 汇总
    parts = []
    if key_lines:
        key_desc = "、".join(f"{_pos_to_name(p)}{_find_stage_at(lines_out, p)}"
                            for p in key_lines)
        parts.append(f"得力之爻：{key_desc}")
    if weak_lines:
        weak_desc = "、".join(f"{_pos_to_name(p)}{_find_stage_at(lines_out, p)}"
                             for p in weak_lines)
        parts.append(f"无力之爻：{weak_desc}")

    summary = "；".join(parts) if parts else "各爻状态平和"

    return {
        "day_branch": day_branch,
        "day_element": day_element,
        "lines": lines_out,
        "summary": summary,
        "key_lines": key_lines,
        "weak_lines": weak_lines,
    }


# =============================================================================
# 分析段 12：绝处逢生 (Life at Dead End / Desperate Relief)
# 基于《卜筮正宗》"用神绝于日辰，若得原神发动来生，谓之绝处逢生，凶中反吉"
# =============================================================================

def analyze_desperate_relief(result):
    """
    绝处逢生分析：当用神在日辰处逢"绝"或"死"地时，检查原神是否发动来生。

    若原神发动且有力 → "绝处逢生"（凶中反吉，+2.0）
    若原神发动但无力 → "绝处逢生但原神无力"（+0.5）
    若原神未发动但现于卦中 → "绝地待原神"（+0.2）
    若原神不现或旬空/月破 → "绝地无救"（-0.8）

    返回：
        {
            "has_desperate_relief": bool,
            "stage": str,               # "绝" / "死" / ""
            "yuan_shen_moving": bool,   # 原神是否发动
            "yuan_shen_strength": str,  # 原神综合旺衰
            "verdict": str,             # 断语标签
            "score_modifier": float,    # 分数修正
            "description": str,
        }
    """
    out = {
        "has_desperate_relief": False,
        "stage": "",
        "yuan_shen_moving": False,
        "yuan_shen_strength": "",
        "verdict": "",
        "score_modifier": 0.0,
        "description": "",
    }

    # Guard: requires original_hexagram and divination_time
    hex_info = result.get("original_hexagram")
    if not hex_info or not isinstance(hex_info, dict):
        return out

    yao_lines = hex_info.get("yao_lines", [])
    if not yao_lines:
        return out

    div_time = result.get("divination_time", {})
    day_sb = div_time.get("day_stem_branch", "")
    month_sb = div_time.get("month_stem_branch", "")
    day_branch = day_sb[1:] if isinstance(day_sb, str) and len(day_sb) >= 2 else ""
    month_branch = month_sb[1:] if isinstance(month_sb, str) and len(month_sb) >= 2 else ""
    if not day_branch:
        return out

    # ── Determine 用神 element ──
    use_god_element = ""
    # Prefer _step2_data (thinking chain) if present (put there by analyze)
    step2_data = result.get("_step2_data")
    if isinstance(step2_data, dict):
        use_god_element = step2_data.get("use_god_element", "")
        use_god_position = step2_data.get("use_god_position")
    else:
        use_god_position = None

    # Fallback: use 世爻 element
    if not use_god_element:
        for yao in yao_lines:
            if yao.get("is_world"):
                use_god_element = _branch_element(yao.get("earthly_branch", ""))
                break

    if not use_god_element:
        return out

    # ── Determine use-god position's branch for exact stage lookup ──
    use_god_branch = ""
    if use_god_position:
        for yao in yao_lines:
            if yao.get("position") == use_god_position:
                use_god_branch = yao.get("earthly_branch", "")
                break
    if not use_god_branch:
        # Fallback when position is unknown: use the 世爻 branch directly
        for yao in yao_lines:
            if yao.get("is_world"):
                use_god_branch = yao.get("earthly_branch", "")
                break
    if not use_god_branch:
        return out

    # ── Lookup 十二长生 stage ──
    tg = TWELVE_GROWTH.get(use_god_element)
    if not tg:
        return out

    stage = tg.get(day_branch, "")

    if stage not in ("绝", "死"):
        return out

    out["has_desperate_relief"] = True
    out["stage"] = stage

    # ── Determine 原神 element (the element that generates 用神) ──
    yuan_shen_element = SHENG_WO.get(use_god_element, "")
    if not yuan_shen_element:
        return out

    # ── Check 原神 status in the hexagram ──
    empty_branches = result.get("empty_branches", [])
    month_element = _branch_element(month_branch) if month_branch else _branch_element(day_branch)
    day_element = _branch_element(day_branch)

    yuan_shen_present = False
    yuan_shen_moving = False
    yuan_shen_empty = False
    yuan_shen_month_break = False
    yuan_shen_combined = "休"

    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        elem = _branch_element(branch)
        if elem != yuan_shen_element:
            continue
        yuan_shen_present = True
        if yao.get("is_moving", False):
            yuan_shen_moving = True
        if branch in empty_branches:
            yuan_shen_empty = True
        if month_branch and is_ba_zu_chong(branch, month_branch):
            yuan_shen_month_break = True

        # Compute combined strength (first match is enough — they share element)
        yuan_shen_combined = _combined_strength(yuan_shen_element, month_element, day_element)

    # If 原神 not found in main hexagram, check 伏藏 (hidden spirit analysis)
    if not yuan_shen_present:
        adv = result.get("advanced_analysis")
        if isinstance(adv, dict):
            hs_analysis = adv.get("hidden_spirit_analysis", {})
            if isinstance(hs_analysis, dict):
                details = hs_analysis.get("details", [])
                for detail in details:
                    hs = detail.get("hidden_spirit", {}) or {}
                    hs_elem = hs.get("element", "") or _branch_element(hs.get("branch", ""))
                    if hs_elem == yuan_shen_element:
                        yuan_shen_present = True
                        # 伏藏之原神 is dormant; not actively moving
                        yuan_shen_combined = element_strength_in_month(
                            yuan_shen_element, month_element
                        )
                        break

    out["yuan_shen_moving"] = yuan_shen_moving
    out["yuan_shen_strength"] = yuan_shen_combined

    # ── Apply judgment logic ──
    if yuan_shen_moving and yuan_shen_combined in ("旺", "相", "中和") and \
       not yuan_shen_empty and not yuan_shen_month_break:
        out["verdict"] = "绝处逢生"
        out["score_modifier"] = 2.0
        out["description"] = (
            f"用神{use_god_element}（{use_god_branch}）处{stage}地，"
            f"原神{yuan_shen_element}发动来生，原神{yuan_shen_combined}有力，"
            f"绝处逢生，凶中反吉"
        )
    elif yuan_shen_moving and not yuan_shen_empty and not yuan_shen_month_break:
        out["verdict"] = "绝处逢生但原神无力"
        out["score_modifier"] = 0.5
        out["description"] = (
            f"用神{use_god_element}（{use_god_branch}）处{stage}地，"
            f"原神{yuan_shen_element}发动来生，但原神{yuan_shen_combined}无力，"
            f"虽生而力微"
        )
    elif yuan_shen_present and not yuan_shen_empty and not yuan_shen_month_break:
        out["verdict"] = "绝地待原神"
        out["score_modifier"] = 0.2
        out["description"] = (
            f"用神{use_god_element}（{use_god_branch}）处{stage}地，"
            f"原神{yuan_shen_element}虽现于卦中但未发动，待时而动"
        )
    elif not yuan_shen_present:
        out["verdict"] = "绝地无救"
        out["score_modifier"] = -0.8
        out["description"] = (
            f"用神{use_god_element}（{use_god_branch}）处{stage}地，"
            f"原神{yuan_shen_element}不现于卦中，绝地无救"
        )
    else:
        # 原神 present but empty or month-broken
        out["verdict"] = "绝地无救"
        out["score_modifier"] = -0.8
        out["description"] = (
            f"用神{use_god_element}（{use_god_branch}）处{stage}地，"
            f"原神{yuan_shen_element}虽现但{'旬空' if yuan_shen_empty else '月破'}，"
            f"无力救援，绝地无救"
        )

    return out


def _find_stage_at(lines_out, position):
    """根据位置找出对应阶段名称"""
    for l in lines_out:
        if l["position"] == position:
            return l["growth_stage"]
    return ""


# =============================================================================
# 分析段 7：六合六冲卦判断
# =============================================================================

def analyze_clash_harmony(result):
    """
    六合/六冲卦判断：
    - 检查各对应位置爻对(1-4, 2-5, 3-6)的地支关系
    - 全部合 → 六合卦
    - 全部冲 → 六冲卦
    - 部分合、部分冲 → 描述各异
    
    返回：
        {
            "hexagram_type": str,    # "六合卦"/"六冲卦"/"半合半冲"/"无明确合冲"
            "pairs": [
                {
                    "positions": (int, int),
                    "branches": (str, str),
                    "relation": str,    # "合"/"冲"/"无特殊"
                    "description": str,
                },
                ...
            ],
            "summary": str,
            "meaning": str,  # 六合/六冲的含义解释
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    if not yao_lines:
        return {"hexagram_type": "未知", "pairs": [], "summary": "无数据", "meaning": ""}

    yao_by_pos = {y["position"]: y for y in yao_lines}

    # 三对对应位置
    pair_positions = [(1, 4), (2, 5), (3, 6)]
    pairs = []
    he_count = 0
    chong_count = 0

    for p1, p2 in pair_positions:
        y1 = yao_by_pos.get(p1, {})
        y2 = yao_by_pos.get(p2, {})
        b1 = y1.get("earthly_branch", "")
        b2 = y2.get("earthly_branch", "")

        if is_ba_zu_he(b1, b2):
            relation = "合"
            he_count += 1
            desc = (f"位置{_pos_to_name(p1)}与{_pos_to_name(p2)}"
                    f"（{b1}与{b2}）六合")
        elif is_ba_zu_chong(b1, b2):
            relation = "冲"
            chong_count += 1
            desc = (f"位置{_pos_to_name(p1)}与{_pos_to_name(p2)}"
                    f"（{b1}与{b2}）六冲")
        else:
            relation = "无特殊"
            desc = (f"位置{_pos_to_name(p1)}与{_pos_to_name(p2)}"
                    f"（{b1}与{b2}）无合冲")

        pairs.append({
            "positions": (p1, p2),
            "branches": (b1, b2),
            "relation": relation,
            "description": desc,
        })

    if he_count == 3:
        hexagram_type = "六合卦"
        meaning = (
            "六合卦主团聚、缠绵、迟缓、牵绊。"
            "占事多主反复纠缠、不易决断、需要耐心。"
            "占物则聚集不散，占病则缠绵难愈。"
            "然若用神旺相，则六合亦可为吉，主聚合之象。"
        )
    elif chong_count == 3:
        hexagram_type = "六冲卦"
        meaning = (
            "六冲卦主散、速决、分离、变动。"
            "占事多主动散不聚、难以坚守、事来事去迅速。"
            "占出行利，占散事宜，占聚合则不利。"
            "若用神休囚受克，则冲散太过，须防意外。"
        )
    elif he_count > 0 and chong_count > 0:
        hexagram_type = "半合半冲"
        meaning = (
            f"本卦有六合又有六冲（合{he_count}对、冲{chong_count}对），"
            "主事态复杂，表面和谐内有矛盾，或聚散交织需视具体情形而定。"
        )
    elif he_count > 0:
        hexagram_type = "有合"
        meaning = (
            f"本卦有{he_count}对合{'' if chong_count == 0 else f'，{chong_count}对冲'}，"
            "合处逢事宜斟酌，主有聚合之象但不完整。"
        )
    elif chong_count > 0:
        hexagram_type = "有冲"
        meaning = (
            f"本卦有{chong_count}对冲，"
            "冲处逢事宜谨慎，主有散动之象但不完整。"
        )
    else:
        hexagram_type = "无明确合冲"
        meaning = "本卦各对应爻位无合无冲，平顺之象，吉凶需依用神决断。"

    pair_summaries = "；".join(p["description"] for p in pairs)
    summary = f"{hexagram_type}：{pair_summaries}"

    return {
        "hexagram_type": hexagram_type,
        "pairs": pairs,
        "summary": summary,
        "meaning": meaning,
    }


# =============================================================================
# 分析段 8：反吟伏吟判断
# =============================================================================

def analyze_repetition(result):
    """
    反吟伏吟分析：
    - 反吟：变卦之爻地支与本卦对应爻地支相冲（反复之意）
    - 伏吟：变卦与本卦相同（或内/外卦不变），爻位地支不变（呻吟不止）
    
    返回：
        {
            "repetition_type": str,  # "反吟"/"伏吟"/"反吟兼伏吟"/"无"
            "chong_pairs": [
                {
                    "position": int,
                    "original_branch": str,
                    "changed_branch": str,
                    "description": str,
                },
                ...
            ],
            "summary": str,
            "meaning": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    changed = result.get("changed_hexagram") or {}
    changed_name = changed.get("name")
    changed_lines = changed.get("changed_lines", [])

    if not yao_lines or not changed_name or not changed_lines:
        return {
            "repetition_type": "无",
            "chong_pairs": [],
            "summary": "本卦无动爻，不存在反吟伏吟",
            "meaning": "",
        }

    # 判断伏吟：如果所有爻都没变（理论上在变卦时有changed_lines，说明有变爻）
    # 伏吟的判定：变卦=本卦（不可能，因为有changed_lines）
    # 或者：内卦或外卦的三爻全部变化但变后相同（如乾→乾，但动爻变了又变回）
    # 这里准确判定：变卦各爻的地支与本卦对比
    yao_by_pos = {y["position"]: y for y in yao_lines}

    chong_pairs = []
    same_count = 0
    diff_count = 0

    for pos in range(1, 7):
        orig_branch = yao_by_pos.get(pos, {}).get("earthly_branch", "")
        chg_branch = get_changed_hexagram_branch(changed_name, pos)

        if orig_branch and chg_branch:
            if is_ba_zu_chong(orig_branch, chg_branch):
                chong_pairs.append({
                    "position": pos,
                    "original_branch": orig_branch,
                    "changed_branch": chg_branch,
                    "description": (
                        f"{_pos_to_name(pos)}：{orig_branch}→{chg_branch}，"
                        f"本支被冲，反复变动之象"
                    ),
                })
                diff_count += 1
            elif orig_branch == chg_branch:
                same_count += 1
            else:
                diff_count += 1

    # 反吟判定：有地支相冲的变爻对
    has_fanyin = len(chong_pairs) > 0

    # 伏吟判定：内卦或外卦三爻变化后地支不变
    # 内卦(1-3)全部变化且变后分支不变
    inner_same = True
    inner_all_changed = True
    for pos in range(1, 4):
        in_changed = pos in changed_lines
        if not in_changed:
            inner_all_changed = False
            break
        orig_branch = yao_by_pos.get(pos, {}).get("earthly_branch", "")
        chg_branch = get_changed_hexagram_branch(changed_name, pos)
        if orig_branch != chg_branch:
            inner_same = False

    outer_same = True
    outer_all_changed = True
    for pos in range(4, 7):
        in_changed = pos in changed_lines
        if not in_changed:
            outer_all_changed = False
            break
        orig_branch = yao_by_pos.get(pos, {}).get("earthly_branch", "")
        chg_branch = get_changed_hexagram_branch(changed_name, pos)
        if orig_branch != chg_branch:
            outer_same = False

    has_fuyin = (inner_all_changed and inner_same) or (outer_all_changed and outer_same)

    if has_fanyin and has_fuyin:
        repetition_type = "反吟兼伏吟"
        meaning = (
            "既反吟又伏吟，主反复多端、牵制难解、呻吟不止。"
            "事情反复无常，内心焦虑不安，是最不安定的卦象。"
        )
    elif has_fanyin:
        repetition_type = "反吟"
        meaning = (
            "反吟主反复、变动不安、事多反复。"
            "化反吟多为先成后败、先聚后散之象。"
            "若用神旺相可解，主虽有波折终可成；若休囚则反复无定。"
        )
    elif has_fuyin:
        repetition_type = "伏吟"
        meaning = (
            "伏吟主呻吟不止、忧郁难舒、事有内心之苦。"
            "占事多停滞不前、郁闷焦虑、欲行又止。"
            "宜静不宜动，宜守不宜攻。"
        )
    else:
        repetition_type = "无"
        meaning = "本卦变爻无反吟伏吟，卦象安定。"

    summary_parts = []
    if has_fanyin:
        summary_parts.append(
            f"反吟：{len(chong_pairs)}处地支相冲 "
            f"({'、'.join(d['description'] for d in chong_pairs)})"
        )
    if has_fuyin:
        trigram = "内卦" if inner_all_changed and inner_same else "外卦"
        summary_parts.append(f"伏吟：{trigram}伏吟")

    summary = "；".join(summary_parts) if summary_parts else "无反吟伏吟"

    return {
        "repetition_type": repetition_type,
        "chong_pairs": chong_pairs,
        "fuyin_trigram": ("内卦" if inner_all_changed and inner_same else
                         "外卦" if outer_all_changed and outer_same else None),
        "summary": summary,
        "meaning": meaning,
    }


# =============================================================================
# 分析段 8b：反吟伏吟深层析义
# =============================================================================

def analyze_repetition_deep(result):
    """
    反吟伏吟深层析义：基于《卜筮正宗》的五行旺衰综合规则，
    对反吟伏吟进行精细化评分，而非统一扣减。

    返回：
        {
            "type": "反吟" | "伏吟" | None,
            "level": "卦" | "爻",
            "scope": "内卦" | "外卦" | "用神" | "世爻" | None,
            "interpretation": str,
            "score_modifier": float,
            "classical_quote": str,
        }
    """
    # 先调用基础分析获取类型信息
    basic = analyze_repetition(result)
    rep_type = basic.get("repetition_type", "无")

    if rep_type == "无":
        return {
            "type": None,
            "level": None,
            "scope": None,
            "interpretation": "",
            "score_modifier": 0.0,
            "classical_quote": "",
        }

    # 判断是反吟还是伏吟为主（"反吟兼伏吟"拆为反吟优先）
    if "反吟" in rep_type:
        main_type = "反吟"
    elif "伏吟" in rep_type:
        main_type = "伏吟"
    else:
        main_type = None

    # 判断 level：卦级别 vs 爻级别
    hex_info = result.get("original_hexagram", {})
    changed = result.get("changed_hexagram") or {}
    changed_name = changed.get("name")
    original_name = hex_info.get("name", "")

    level = "爻"
    if original_name and changed_name and original_name != changed_name:
        # 检查是否是整个卦变了（如六冲变六冲）
        yao_lines = hex_info.get("yao_lines", [])
        changed_lines = changed.get("changed_lines", [])
        if len(changed_lines) >= 3:
            # 检查是否内外卦地支全冲
            chong_count = basic.get("chong_pairs", [])
            if len(chong_count) >= 4:
                level = "卦"

    # 判断 scope
    scope = None
    chong_pairs = basic.get("chong_pairs", [])
    fuyin_trigram = basic.get("fuyin_trigram")

    # 检查是否涉及世爻
    generation_str = hex_info.get("generation", "")
    gen_map_reverse = {"六世": 6, "五世": 5, "四世": 4, "三世": 3,
                       "二世": 2, "一世": 1, "游魂": 4, "归魂": 3}
    world_pos = gen_map_reverse.get(generation_str, 1)

    # 获取用神位置(s)
    use_god_positions = _find_use_god_positions(result)

    # 检查反吟/伏吟是否涉及用神或世爻
    involved_positions = set()
    for cp in chong_pairs:
        if isinstance(cp, dict):
            involved_positions.add(cp.get("position", 0))

    if main_type == "伏吟":
        # 伏吟涉及变化的爻位
        changed_lines = changed.get("changed_lines", [])
        involved_positions = set(changed_lines) if changed_lines else set()

    if world_pos in involved_positions:
        scope = "世爻"
    elif any(p in involved_positions for p in use_god_positions):
        scope = "用神"
    elif fuyin_trigram:
        scope = "内卦" if fuyin_trigram == "内卦" else "外卦"
    elif chong_pairs:
        # 根据相冲爻位判断内外
        first_pos = chong_pairs[0].get("position", 1) if isinstance(chong_pairs[0], dict) else 1
        scope = "内卦" if first_pos <= 3 else "外卦"
    else:
        scope = None

    # 获取用神旺衰状态以确定评分
    use_god_strength = _get_use_god_strength_level(result)

    # 根据规则评分
    if main_type == "反吟":
        score_modifier, interpretation, classical_quote = _score_fanyin(
            scope, use_god_strength, level, chong_pairs, basic
        )
    else:  # 伏吟
        score_modifier, interpretation, classical_quote = _score_fuyin(
            scope, use_god_strength, result, basic
        )

    return {
        "type": main_type,
        "level": level,
        "scope": scope,
        "interpretation": interpretation,
        "score_modifier": round(score_modifier, 2),
        "classical_quote": classical_quote,
    }


def _find_use_god_positions(result):
    """找到用神六亲对应的所有爻位"""
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    # 从 thinking_chain 或 category 推断用神六亲
    category = result.get("question_category", "")
    category_to_relation = {
        "career": "官鬼",
        "wealth": "妻财",
        "health": "官鬼",
        "love": "妻财",
        "family": "父母",
        "travel": "官鬼",
        "study": "父母",
        "lawsuit": "官鬼",
    }
    target_relation = category_to_relation.get(category)

    if not target_relation:
        # 尝试从 question 推断
        question = result.get("question", "")
        if any(k in question for k in ["升迁", "事业", "工作", "功名", "官职", "升官"]):
            target_relation = "官鬼"
        elif any(k in question for k in ["投资", "生意", "婚姻", "财运", "钱财", "财"]):
            target_relation = "妻财"
        elif any(k in question for k in ["孩子", "儿子", "女儿", "医药", "医生"]):
            target_relation = "子孙"
        elif any(k in question for k in ["父亲", "母亲", "父母", "长辈", "文书"]):
            target_relation = "父母"
        elif any(k in question for k in ["兄弟", "朋友", "同事"]):
            target_relation = "兄弟"

    if not target_relation:
        return []

    positions = []
    for yao in yao_lines:
        if yao.get("six_relation") == target_relation:
            positions.append(yao.get("position", 0))
    return positions


def _get_use_god_strength_level(result):
    """获取用神旺衰等级: '旺', '中和', '衰'"""
    dt = result.get("divination_time", {})
    day_sb = dt.get("day_stem_branch", "")
    month_sb = dt.get("month_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    empty_branches = result.get("empty_branches", [])

    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    palace_element = hex_info.get("palace_element", "")

    use_positions = _find_use_god_positions(result)
    if not use_positions:
        return "中和"

    # 取用神爻中最重要的一个
    for pos in use_positions:
        for yao in yao_lines:
            if yao.get("position") == pos:
                branch = yao.get("earthly_branch", "")
                elem = _branch_element(branch)
                if not elem:
                    continue
                month_strength = element_strength_in_month(elem, _branch_element(month_branch))
                day_strength = element_strength_in_month(elem, _branch_element(day_branch))
                is_empty = branch in empty_branches

                # 综合判断
                if month_strength == "旺" or day_strength == "旺":
                    return "旺"
                elif month_strength == "死" or day_strength == "死":
                    return "衰"
                elif is_empty:
                    return "衰"
                elif month_strength == "囚" or day_strength == "囚":
                    return "衰"
                elif month_strength == "相" or day_strength == "相":
                    return "旺"
    return "中和"


def _score_fanyin(scope, use_god_strength, level, chong_pairs, basic_detail):
    """
    反吟精细评分
    规则:
    - 用神旺 + 反吟 → 虽反复但终吉 (-0.1)
    - 用神衰 + 反吟 → 反复且凶 (-0.7)
    - 世爻反吟 → 本人不安 (-0.3)
    - 用神爻反吟 → 事体反复 (-0.4)
    - 卦反吟(全局) → 额外 -0.2
    """
    score = 0.0
    parts = []
    quote = "反吟卦主反复不定，事多不顺，然反吟有变，亦有反复后成功者。"

    # 根据用神旺衰定基调
    if use_god_strength == "旺":
        score -= 0.1
        parts.append("用神旺相遇反吟，虽反复但终有转机")
    elif use_god_strength == "衰":
        score -= 0.5
        parts.append("用神衰弱遇反吟，反复多凶")
        quote = "反吟伏吟，哭泣淋淋。用神休囚逢之，反复无定。"
    else:
        score -= 0.3
        parts.append("用神中和遇反吟，主事有反复")

    # 根据 scope 追加
    if scope == "世爻":
        score -= 0.3
        parts.append("世爻反吟，本人心身不安，进退不决")
        quote = "内卦反吟，内不安；外卦反吟，外不宁。"
    elif scope == "用神":
        score -= 0.4
        parts.append("用神爻反吟，事体反复难定")
    elif scope == "内卦":
        score -= 0.2
        parts.append("内卦反吟，内事不安")
    elif scope == "外卦":
        score -= 0.2
        parts.append("外卦反吟，外事不宁")

    # 卦级别额外
    if level == "卦":
        score -= 0.2
        parts.append("卦反吟(全局反复)，事涉全面")

    interpretation = "；".join(parts) if parts else "反吟之象"
    return score, interpretation, quote


def _score_fuyin(scope, use_god_strength, result, basic_detail):
    """
    伏吟精细评分
    规则:
    - 原神不动 → futile, just persist (-0.2)
    - 原神发动 → can overcome stagnation (+0.3)
    - 用神伏吟 → 事久拖不决 (-0.4)
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    changed = result.get("changed_hexagram") or {}
    changed_lines = changed.get("changed_lines", [])
    palace_element = hex_info.get("palace_element", "")

    score = 0.0
    parts = []
    quote = "伏吟卦主呻吟不止，事多郁闷难伸，安静守时为上。"

    # 检查原神（生用神之五行）是否发动
    # 原神 = 生宫五行的六亲。例如宫为金，土生金 → 父母为原神
    shenyuan_moved = False
    for yao in yao_lines:
        if yao.get("is_moving") and yao.get("position") in changed_lines:
            branch = yao.get("earthly_branch", "")
            elem = _branch_element(branch)
            if elem:
                # 原神五行为：金→土，木→水，水→金，火→木，土→火
                shenyuan_elem_map = {"金": "土", "木": "水", "水": "金", "火": "木", "土": "火"}
                if elem == shenyuan_elem_map.get(palace_element):
                    shenyuan_moved = True
                    break

    if shenyuan_moved:
        score += 0.3
        parts.append("原神发动，虽伏吟可突破瓶颈，终有所成")
        quote = "伏吟之卦，原神动者，呻吟中有生机。"
    else:
        score -= 0.2
        parts.append("原神不动，伏吟难伸，宜静守")

    # 用神伏吟
    use_positions = _find_use_god_positions(result)
    if any(p in changed_lines for p in use_positions):
        score -= 0.4
        parts.append("用神伏吟，事久拖不决")

    interpretation = "；".join(parts) if parts else "伏吟之象，郁闷难伸"
    return score, interpretation, quote


# =============================================================================
# 分析段 8c：卦身法 (出自《黄金策》)
# =============================================================================

def find_hexagram_body(generation, day_stem):
    """
    定位卦身爻位 (1-6)。

    Parameters
    ----------
    generation : int
        卦的代数：一世=1, 二世=2, ..., 六世=6, 游魂=7, 归魂=8
    day_stem : str
        日干（十个天干的字符串），决定顺逆

    Returns
    -------
    int
        卦身爻位 (1-6, 1=初爻, 6=上爻)
    """
    YANG_STEMS = {"甲", "丙", "戊", "庚", "壬"}
    is_yang_day = day_stem in YANG_STEMS

    if is_yang_day:
        # 阳日起，顺数：世数即位数
        body_pos = 1 + (generation - 1)
    else:
        # 阴日起，逆数：从 7 逆推
        body_pos = 7 - generation

    return ((body_pos - 1) % 6) + 1  # clamp to 1-6


def analyze_hexagram_body(result):
    """
    卦身法分析：卦身为一卦之身体，代表事物的本体与根基。

    Returns
    -------
    dict with keys: body_position, body_element, body_relation,
        meaning, classical_rule, implications
    """
    hex_info = result.get("original_hexagram", {})
    generation = hex_info.get("generation", "")

    # 解析 generation 为数字
    gen_map = {
        "六世": 6, "五世": 5, "四世": 4, "三世": 3,
        "二世": 2, "一世": 1,
        "游魂": 7, "归魂": 8,
    }
    gen_num = gen_map.get(generation, 0)

    if gen_num == 0:
        return {
            "body_position": None,
            "body_element": "",
            "body_relation": "",
            "meaning": "无法确定卦身（卦代未知）",
            "classical_rule": "阳世子起顺推，阴世应起逆推",
            "implications": [],
        }

    # 获取日干
    dt = result.get("divination_time", {})
    day_sb = dt.get("day_stem_branch", "甲")
    day_stem = day_sb[0] if day_sb else "甲"

    body_pos = find_hexagram_body(gen_num, day_stem)

    # 获取对应爻信息
    yao_lines = hex_info.get("yao_lines", [])
    body_yao = {}
    for yao in yao_lines:
        if yao.get("position") == body_pos:
            body_yao = yao
            break

    body_element = _branch_element(body_yao.get("earthly_branch", ""))
    body_relation = body_yao.get("six_relation", "")
    is_empty = body_yao.get("earthly_branch", "") in result.get("empty_branches", [])

    # 判断卦身与世爻/用神的关系
    response_texts = []

    # 卦身持世检查
    gen_map_reverse = {"六世": 6, "五世": 5, "四世": 4, "三世": 3,
                       "二世": 2, "一世": 1, "游魂": 4, "归魂": 3}
    world_pos = gen_map_reverse.get(generation, 1)

    if body_pos == world_pos:
        response_texts.append("卦身持世——一身系于此事，全身心投入")

    # 卦身临用神检查
    use_positions = _find_use_god_positions(result)
    if body_pos in use_positions:
        response_texts.append("卦身临用神——事有主骨，终有所成")

    # 卦身空破
    if is_empty:
        response_texts.append("卦身逢空——事无本体，虚晃一枪")

    # 卦身临官鬼
    if body_relation == "官鬼":
        response_texts.append("卦身临鬼——忧患围绕本体，需防内患")
    elif body_relation == "妻财":
        response_texts.append("卦身临财——求财有根本")
    elif body_relation == "子孙":
        response_texts.append("卦身临子孙——事有福德庇护")

    if not response_texts:
        response_texts.append(f"卦身在{_pos_to_name(body_pos)}，{body_relation}坐镇，本位安定")

    return {
        "body_position": body_pos,
        "body_element": body_element,
        "body_relation": body_relation,
        "meaning": f"卦身在{_pos_to_name(body_pos)}，代表事体核心与根基",
        "classical_rule": "阳世子起顺推，阴世应起逆推",
        "implications": [
            "卦身临用神 → 事有主骨，终有所成",
            "卦身临忌神 → 事有内患，防不胜防",
            "卦身持世 → 一身系于此事",
            "卦身逢空 → 事无本体，虚晃一枪",
        ],
        "body_is_world": body_pos == world_pos,
        "body_is_empty": is_empty,
        "body_is_use_god": body_pos in use_positions,
        "specific_notes": response_texts,
    }


# =============================================================================
# 分析段 9：纳甲四柱旺衰总结
# =============================================================================

def analyze_element_strength(result):
    """
    纳甲四柱旺衰总结：基于月建日辰的五行旺衰体系。
    
    返回：
        {
            "month_branch": str,
            "month_element": str,
            "day_branch": str,
            "day_element": str,
            "strength_description": str,  # 如"木旺火相水休金囚土死"
            "use_god_advice": str,        # 通用旺衰判断建议
            "details": [
                {
                    "position": int,
                    "name": str,
                    "branch": str,
                    "element": str,
                    "six_relation": str,
                    "month_strength": str,  # 在月建的状态
                    "day_strength": str,    # 在日辰的状态
                    "overall": str,         # 综合状态
                },
                ...
            ],
            "summary": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    palace_element = hex_info.get("palace_element", "")

    if not yao_lines:
        return {"month_branch": "", "month_element": "", "day_branch": "",
                "day_element": "", "strength_description": "",
                "details": [], "summary": "无数据"}

    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""

    month_element = _branch_element(month_branch)
    day_element = _branch_element(day_branch)
    empty_branches = result.get("empty_branches", [])

    strength_desc = get_month_strength_description(month_element)

    details = []
    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        elem = _branch_element(branch)
        m_str = element_strength_in_month(elem, month_element)
        d_str = element_strength_in_month(elem, day_element)
        overall = _combined_strength(elem, month_element, day_element)

        # 特殊标记
        special = []
        if branch in empty_branches:
            special.append("旬空")
        if is_ba_zu_chong(branch, month_branch):
            special.append("月破")
        if is_ba_zu_chong(branch, day_branch):
            special.append("日冲")
        stage = get_twelve_growth_stage(elem, day_branch)
        if stage in ("墓", "绝", "死"):
            special.append(f"{stage}")

        details.append({
            "position": yao["position"],
            "name": yao.get("name", ""),
            "branch": branch,
            "element": elem,
            "six_relation": yao.get("six_relation", ""),
            "month_strength": m_str,
            "day_strength": d_str,
            "overall": overall,
            "growth_stage": stage,
            "special_markers": special,
        })

    # 通用建议
    advice_parts = [
        f"月建{month_branch}({month_element})，日辰{day_branch}({day_element})",
        f"当月旺衰：{strength_desc}",
    ]

    # 综合总结
    summary_lines = advice_parts.copy()
    strong_yaos = [d for d in details if d["overall"] in ("旺", "相")]
    weak_yaos = [d for d in details if d["overall"] in ("偏弱", "衰")]

    if strong_yaos:
        s_desc = "、".join(
            f"{d['six_relation']}({d['branch']},{d['month_strength']}/{d['day_strength']})"
            for d in strong_yaos
        )
        summary_lines.append(f"旺相之爻：{s_desc}")
    if weak_yaos:
        w_desc = "、".join(
            f"{d['six_relation']}({d['branch']},{d['month_strength']}/{d['day_strength']})"
            for d in weak_yaos
        )
        summary_lines.append(f"休囚之爻：{w_desc}")

    return {
        "month_branch": month_branch,
        "month_element": month_element,
        "day_branch": day_branch,
        "day_element": day_element,
        "strength_description": strength_desc,
        "palace_element": palace_element,
        "details": details,
        "summary": "。".join(summary_lines),
    }


# =============================================================================
# 分析段 10：三刑分析 (基于卜筮正宗)
# =============================================================================

def analyze_three_punishments(result):
    """
    三刑分析（卜筮正宗定量版）：区分完整三刑、待刑、自刑。

    规则：
      - 循环刑（无恩寅巳申、恃势丑戌未）：三字全见 → 完整三刑（极凶）；
        仅见两字 → 待刑（待月日补齐方成刑）。
      - 互刑（无礼子卯）：两字相见即成刑。
      - 自刑（辰午酉亥）：同一地支两见以上。

    返回：
        {
            "has_punishment": bool,
            "punishments": [
                {
                    "type": str,              # 刑的类型
                    "completeness": str,      # "完整" | "待刑" | "成刑"
                    "branches_present": [str], # 卦中及月日出现的地支
                    "missing": [str],          # 缺失的地支（待刑时）
                    "formed_by": str,          # "卦内" | "待月日补齐"
                    "positions": [str],        # 涉及的位置
                    "description": str,
                },
                ...
            ],
            "total_score": float,  # 完整三刑 -1.0, 待刑 -0.3, 无礼成刑 -0.5, 自刑 -0.3/次
            "summary": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    if not yao_lines:
        return {"has_punishment": False, "punishments": [], "total_score": 0.0, "summary": "无数据"}

    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""

    # ── 收集所有地支及其来源 ──
    # 三刑口径（P0-1 修正）：
    #   1) 以本卦六爻为主（hex_branches）；
    #   2) 月建/日辰仅作"催刑"（external_branches），参与补足但不按完整三刑计；
    #   3) 变卦地支不参与本卦三刑（化出之爻不构成原局刑伤）。
    hex_branches = []
    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        if branch:
            hex_branches.append((branch, f"爻{_pos_to_name(yao['position'])}"))

    external_branches = []
    if month_branch:
        external_branches.append((month_branch, f"月建({month_branch})"))
    if day_branch:
        external_branches.append((day_branch, f"日辰({day_branch})"))

    branches_with_source = hex_branches + external_branches

    # ── 建立全量地支集合（用于完整性判断）──
    all_branches_set = set(b for b, _ in branches_with_source)
    hex_set = set(b for b, _ in hex_branches)

    # ── 辅助：从 branches_with_source 中找出指定地支的所有来源位置 ──
    def _find_sources(branchesNeeded):
        return [(b, s) for b, s in branches_with_source if b in branchesNeeded]

    punishments = []
    total_score = 0.0

    # ── 1. 循环刑（无恩、恃势）：三字全见 vs 仅见两字 ──
    for ptype, required in THREE_PUNISHMENTS_CYCLIC.items():
        required_set = set(required)
        present_set = all_branches_set & required_set
        present = sorted(present_set, key=required.index)
        missing = sorted(required_set - present_set, key=required.index)

        present_hex_cnt = len(hex_set & required_set)
        if present_hex_cnt == 3:
            # 卦内三字齐备 — 完整三刑，极凶
            sources = _find_sources(set(required))
            pos_list = list(dict.fromkeys(s for _, s in sources))  # deduplicated, keep order
            punishments.append({
                "type": ptype,
                "completeness": "完整",
                "branches_present": present,
                "missing": [],
                "formed_by": "卦内",
                "positions": pos_list,
                "description": (
                    f"{ptype}（完整三刑）：{present[0]}刑{present[1]}刑{present[2]}，"
                    f"三字全见于{ '、'.join(pos_list) }，极凶之象"
                ),
                "score": -1.0,
            })
            total_score -= 1.0
        elif len(present_set) == 3:
            # 卦内二字 + 月日补足一字 — 催刑（月日催成，力减半）
            sources = _find_sources(set(required))
            pos_list = list(dict.fromkeys(s for _, s in sources))
            punishments.append({
                "type": ptype,
                "completeness": "催刑",
                "branches_present": present,
                "missing": [],
                "formed_by": "卦内为主，月日催刑",
                "positions": pos_list,
                "description": (
                    f"{ptype}（催刑）：卦内{ '、'.join(p for p in present if p in hex_set) or '无'}，"
                    f"月日{ '、'.join(p for p in present if p not in hex_set) }补足成刑，"
                    f"刑伤力减半"
                ),
                "score": -0.5,
            })
            total_score -= 0.5
        elif len(present_set) == 2:
            # 待刑 — 需月日补齐
            sources = _find_sources(present_set)
            pos_list = list(dict.fromkeys(s for _, s in sources))
            punishments.append({
                "type": ptype,
                "completeness": "待刑",
                "branches_present": present,
                "missing": missing,
                "formed_by": "待月日补齐",
                "positions": pos_list,
                "description": (
                    f"{ptype}（待刑）：{present[0]}、{present[1]}相见，"
                    f"缺{missing[0]}，待月日逢{missing[0]}方成刑，"
                    f"目前刑伤未全，但有刑伤之象"
                ),
                "score": -0.3,
            })
            total_score -= 0.3
        # 卦内及月日合计不足两字: 不构成任何刑

    # ── 2. 互刑（无礼之刑子卯）：卦内两字成刑；卦内一+月日一为待刑 ──
    b1_key, b2_key = THREE_PUNISHMENTS_MUTUAL["无礼之刑"]
    in_hex = (b1_key in hex_set and b2_key in hex_set)
    in_all = (b1_key in all_branches_set and b2_key in all_branches_set)
    if in_all:
        sources = _find_sources({b1_key, b2_key})
        pos_list = list(dict.fromkeys(s for _, s in sources))
        if in_hex:
            punishments.append({
                "type": "无礼之刑",
                "completeness": "成刑",
                "branches_present": [b1_key, b2_key],
                "missing": [],
                "formed_by": "卦内",
                "positions": pos_list,
                "description": (
                    f"无礼之刑（成刑）：{b1_key}刑{b2_key}，"
                    f"见于{ '、'.join(pos_list) }，主无礼刑伤、恩中之怨"
                ),
                "score": -0.5,
            })
            total_score -= 0.5
        else:
            punishments.append({
                "type": "无礼之刑",
                "completeness": "待刑",
                "branches_present": [b1_key, b2_key],
                "missing": [],
                "formed_by": "卦内为主，月日催刑",
                "positions": pos_list,
                "description": (
                    f"无礼之刑（待刑）：{b1_key}、{b2_key}月日相见，"
                    f"刑伤未全，主微咎"
                ),
                "score": -0.3,
            })
            total_score -= 0.3

    # ── 3. 自刑（辰午酉亥）：仅卦内同一地支两次以上 ──
    from collections import Counter
    hex_branch_counts = Counter(b for b, _ in hex_branches)
    for sp_branch in SELF_PUNISHMENTS:
        count = hex_branch_counts.get(sp_branch, 0)
        if count >= 2:
            sources = _find_sources({sp_branch})
            pos_list = list(dict.fromkeys(s for _, s in sources))
            punishments.append({
                "type": "自刑",
                "completeness": "完整",
                "branches_present": [sp_branch],
                "missing": [],
                "formed_by": "卦内",
                "positions": pos_list,
                "description": (
                    f"自刑：{sp_branch}出现{count}次"
                    f"（{ '、'.join(pos_list) }），"
                    f"自刑主自我纠结、自作自受、内心矛盾"
                ),
                "score": -0.3 * (count - 1),
            })
            total_score -= 0.3 * (count - 1)  # 每多一次减0.3

    # ── 三刑齐全加重（多个成刑/完整/催刑叠加时凶性倍增）──
    # 经典规则："三刑齐全，凶不可解"——两处以上成刑时按1.5x折算，三处以上2.0x
    complete_cnt = sum(1 for p in punishments if p.get("completeness") in ("完整", "成刑", "催刑"))
    if complete_cnt >= 3:
        total_score *= 2.0  # 三处以上成刑 → 极凶
        # 三刑杂见（循环刑+无礼刑+自刑以上至少两类并列）额外加罚
        ptype_set = set(p.get("type", "") for p in punishments)
        if len(ptype_set) >= 3:
            total_score -= 0.8  # 三类以上刑并见 → 更凶
        elif len(ptype_set) >= 2:
            total_score -= 0.5  # 多种刑类杂见，凶性更甚
    elif complete_cnt >= 2:
        total_score *= 1.5  # 两处成刑 → 凶性加重
        ptype_set = set(p.get("type", "") for p in punishments)
        if len(ptype_set) >= 2:
            total_score *= 1.25  # 多种刑类杂见，再乘1.25
        # 两处以上成刑额外定罚(不乘倍数直接加)
        total_score -= 0.5  # 2+ 成刑叠加的固定附加减分
    # 1处成刑维持原分数（线性加减已足够）

    if not punishments:
        return {"has_punishment": False, "punishments": [], "total_score": 0.0, "summary": "本卦无三刑"}

    summary_parts = [p["description"] for p in punishments]

    return {
        "has_punishment": True,
        "punishments": punishments,
        "total_score": round(total_score, 2),
        "summary": "；".join(summary_parts),
    }


# =============================================================================
# 工具函数：六破判断
# =============================================================================

def is_ba_zu_po(b1, b2):
    """判断两地支是否六破"""
    for a, b in BREAK_PAIRS:
        if (b1 == a and b2 == b) or (b1 == b and b2 == a):
            return True
    return False


# =============================================================================
# 分析段 12：日月合用神检测 (Gap 5)
# =============================================================================

def analyze_day_month_bonding(result):
    """
    检测用神/忌神与日辰/月建的六合关系。

    经典规则：
    - 用神合日："切近有力" — immediate power, near-term response
    - 用神合月："事必成就" — success within the month
    - 月日同合：大吉之极
    - 忌神合月日：忌神有力为祸

    返回:
        {
            "findings": [{"bond": str, "effect": str, "score": float}, ...],
            "total_score_modifier": float,
            "summary": str,
        }
    """
    # Build bidirectional 六合 lookup
    HE_SET_BI = set()
    for a, b in HE_PAIRS:
        HE_SET_BI.add((a, b))
        HE_SET_BI.add((b, a))

    # Extract 用神 branch from thinking chain step2
    use_god_branch = ""
    use_god_data = result.get("thinking_chain", {}).get("step2_use_god_identification", {})
    selected = use_god_data.get("selected_use_god", {})
    if isinstance(selected, dict):
        use_god_branch = selected.get("earthly_branch", "")

    # Also check step3 which has use_god_branch explicitly
    if not use_god_branch:
        step3 = result.get("thinking_chain", {}).get("step3_strength_analysis", {})
        use_god_branch = step3.get("use_god_branch", "")

    # Fallback: find use_god from yao_lines via six_relation matching use_god_category
    if not use_god_branch:
        yao_lines = result.get("original_hexagram", {}).get("yao_lines", [])
        use_god_cat = use_god_data.get("use_god_category", "")
        for yao in yao_lines:
            if yao.get("six_relation") == use_god_cat:
                use_god_branch = yao.get("earthly_branch", "")
                break

    # Extract 忌神 positions/branches from step2
    ji_shen_branches = []
    ji_shen_data = use_god_data.get("ji_shen", {})
    if isinstance(ji_shen_data, dict):
        ji_positions = ji_shen_data.get("positions", [])
        if isinstance(ji_positions, list):
            for jp in ji_positions:
                if isinstance(jp, dict):
                    jb = jp.get("earthly_branch", "")
                    if jb:
                        ji_shen_branches.append(jb)
        # Also check fu_cang
        ji_fu = ji_shen_data.get("fu_cang")
        if isinstance(ji_fu, dict):
            jb = ji_fu.get("branch", "")
            if jb:
                ji_shen_branches.append(jb)

    div_time = result.get("divination_time", {})
    # day_branch/month_branch may be stored directly or derived from stem_branch
    day_branch = div_time.get("day_branch", "")
    month_branch = div_time.get("month_branch", "")
    if not day_branch:
        day_sb = div_time.get("day_stem_branch", "")
        if len(day_sb) >= 2:
            day_branch = day_sb[1]
    if not month_branch:
        month_sb = div_time.get("month_stem_branch", "")
        if len(month_sb) >= 2:
            month_branch = month_sb[1]

    findings = []

    # 用神合日
    if use_god_branch and day_branch and (use_god_branch, day_branch) in HE_SET_BI:
        findings.append({"bond": "日合用神", "effect": "切近有力", "score": 0.5})

    # 用神合月
    if use_god_branch and month_branch and (use_god_branch, month_branch) in HE_SET_BI:
        findings.append({"bond": "月合用神", "effect": "事必成就", "score": 0.4})

    # 月日同合 check
    if (use_god_branch and day_branch and month_branch
            and (use_god_branch, day_branch) in HE_SET_BI
            and (use_god_branch, month_branch) in HE_SET_BI):
        findings.append({"bond": "月日同合用神", "effect": "大吉之极", "score": 0.3})

    # 忌神合日/月 (negative effect)
    for ji_b in ji_shen_branches:
        if ji_b and day_branch and (ji_b, day_branch) in HE_SET_BI:
            findings.append({"bond": "日合忌神", "effect": "忌神有力为祸", "score": -0.3})
        if ji_b and month_branch and (ji_b, month_branch) in HE_SET_BI:
            findings.append({"bond": "月合忌神", "effect": "忌神缠月不解", "score": -0.25})

    total_modifier = sum(f["score"] for f in findings)

    # Build summary
    if findings:
        summary_parts = [f"{f['bond']}（{f['effect']}）" for f in findings]
        summary = "；".join(summary_parts)
    else:
        summary = "无用神/忌神与日辰月建之合"

    return {
        "findings": findings,
        "use_god_branch": use_god_branch,
        "ji_shen_branches": ji_shen_branches,
        "day_branch": day_branch,
        "month_branch": month_branch,
        "total_score_modifier": total_modifier,
        "summary": summary,
    }


# =============================================================================
# 分析段 13：六破系统 (Gap 6)
# =============================================================================

def analyze_six_breaks(result):
    """
    六破系统：次级冲克关系，弱于六冲但仍有害。

    六破对：子酉破、午卯破、巳申破、寅亥破、辰丑破、戌未破
    注意：巳申、寅亥既是六合又是六破 → "合中带破"

    检查：
    - 各爻与月建之间的六破
    - 各爻与日辰之间的六破
    - 世爻/用爻被破 → 加重

    返回:
        {
            "breaks": [break_dict, ...],
            "has_break": bool,
            "total_modifier": float,
            "description": str,
            "summary": str,
        }
    """
    HE_SET_BI = set()
    for a, b in HE_PAIRS:
        HE_SET_BI.add((a, b))
        HE_SET_BI.add((b, a))

    BREAK_SET_BI = set()
    for a, b in BREAK_PAIRS:
        BREAK_SET_BI.add((a, b))
        BREAK_SET_BI.add((b, a))

    yao_lines = result.get("original_hexagram", {}).get("yao_lines", [])
    div_time = result.get("divination_time", {})
    # day_branch/month_branch may be stored directly or derived from stem_branch
    day_b = div_time.get("day_branch", "")
    month_b = div_time.get("month_branch", "")
    if not day_b:
        day_sb = div_time.get("day_stem_branch", "")
        if len(day_sb) >= 2:
            day_b = day_sb[1]
    if not month_b:
        month_sb = div_time.get("month_stem_branch", "")
        if len(month_sb) >= 2:
            month_b = month_sb[1]

    # Identify use-god branch and is_world flags
    use_god_branch = ""
    step3 = result.get("thinking_chain", {}).get("step3_strength_analysis", {})
    use_god_branch = step3.get("use_god_branch", "")

    use_god_cat = result.get("thinking_chain", {}).get("step2_use_god_identification", {}).get("use_god_category", "")

    world_positions = set()
    use_god_positions = set()
    for yao in yao_lines:
        if yao.get("is_world"):
            world_positions.add(yao.get("position"))
        if yao.get("six_relation") == use_god_cat and use_god_cat:
            use_god_positions.add(yao.get("position"))
        # Also match by branch if step3 has it
        if use_god_branch and yao.get("earthly_branch") == use_god_branch:
            use_god_positions.add(yao.get("position"))

    breaks = []
    for yao in yao_lines:
        b = yao.get("earthly_branch", "")
        if not b:
            continue
        pos = yao.get("position")
        is_critical = pos in world_positions or pos in use_god_positions

        # Check vs 日辰
        for ref_branch, ref_label in [(day_b, "日"), (month_b, "月")]:
            if not ref_branch:
                continue
            if (b, ref_branch) in BREAK_SET_BI:
                is_both_he = (b, ref_branch) in HE_SET_BI
                break_type = "合中带破" if is_both_he else "纯破"
                severity = "重" if is_critical else "轻"
                score = -0.3 if is_critical else -0.15
                breaks.append({
                    "branch": b,
                    "vs": ref_label,
                    "vs_branch": ref_branch,
                    "position": pos,
                    "type": break_type,
                    "severity": severity,
                    "is_critical": is_critical,
                    "score": score,
                    "description": (
                        f"{'世/用爻' if is_critical else ''}{_pos_to_name(pos)}爻{b}"
                        f"与{ref_label}{ref_label == '日' and '辰' or '建'}{ref_branch}"
                        f"成{break_type}，{'破损不遂' if is_critical else '微有损伤'}"
                    ),
                })

    total_modifier = sum(br.get("score", 0) for br in breaks)

    if breaks:
        po_count = len(breaks)
        he_po_count = sum(1 for br in breaks if br["type"] == "合中带破")
        desc = f"六破{po_count}处，皆主破损不遂"
        if he_po_count > 0:
            desc += f"（其中{he_po_count}处合中带破，恩中有怨）"
        summary_parts = [br["description"] for br in breaks]
        summary = "；".join(summary_parts)
    else:
        desc = ""
        summary = "无六破"

    return {
        "breaks": breaks,
        "has_break": len(breaks) > 0,
        "total_modifier": total_modifier,
        "description": desc,
        "summary": summary,
    }


# =============================================================================
# 分析段 11：随官入墓分析 (基于卜筮正宗)
# =============================================================================

# 问题关键词 -> 用神六亲映射（简化版，用于classical_analysis内部推断）
_QUESTION_KEYWORDS_USE_GOD = {
    "父母": ["父", "母", "长辈", "文书", "考试", "学业", "房产", "房", "合同", "证书", "车辆"],
    "官鬼": ["事业", "工作", "官", "职", "升", "迁", "丈夫", "疾病", "病", "官司", "诉讼", "小人", "灾难"],
    "子孙": ["子", "女", "孩子", "晚辈", "学生", "宠物", "医药", "治病"],
    "妻财": ["财", "钱", "投资", "生意", "收入", "利", "赚", "妻子", "婚姻", "感情", "女友"],
    "兄弟": ["兄弟", "姐妹", "朋友", "同事", "竞争", "对手"],
}


def _infer_use_god_category(question):
    """从问题文本推断用神类别（简化版），默认返回世爻"""
    if not question:
        return "世爻"
    for relation, keywords in _QUESTION_KEYWORDS_USE_GOD.items():
        for kw in keywords:
            if kw in question:
                return relation
    return "世爻"


def analyze_officer_tomb(result):
    """
    随官入墓分析：世爻/用神与官鬼同临墓库地支的凶象。

    《卜筮正宗》"随官入墓"歌诀：
    > "随官入墓最凶凶，世用临之祸不轻。官鬼入墓身难保，病人入墓必归冥。"

    检测五种情形：
    1. 官鬼入墓：官鬼五行对应的墓库地支出现在卦中
    2. 世随官入墓：世爻地支 = 官鬼的墓库地支
    3. 用随官入墓：用神地支 = 官鬼的墓库地支（极凶）
    4. 鬼用同墓：官鬼自身地支 = 墓支 且 世/用也临此墓
    5. 官鬼动化墓：官鬼动爻的变爻为墓库地支

    墓库对应：金墓丑、木墓未、火墓戌、水墓辰、土墓辰

    返回：
        {
            "has_officer_tomb": bool,
            "severity": "mild" | "severe" | "catastrophic" | "none",
            "scenarios": [str],
            "officer_branches": [str],
            "tomb_branch": str,
            "description": str,
            "score_modifier": float,
            "classical_quote": str,
            "details": [dict],
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    palace_element = hex_info.get("palace_element", "")
    question = result.get("question", "")

    if not yao_lines or not palace_element:
        return {
            "has_officer_tomb": False,
            "severity": "none",
            "scenarios": [],
            "officer_branches": [],
            "tomb_branch": "",
            "description": "数据不足，无法分析随官入墓",
            "score_modifier": 0.0,
            "classical_quote": "随官入墓最凶凶，世用临之祸不轻",
            "details": [],
        }

    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""

    # 1. 找世爻地支
    world_branch = None
    world_pos = None
    for yao in yao_lines:
        if yao.get("is_world"):
            world_branch = yao.get("earthly_branch", "")
            world_pos = yao.get("position")
            break

    # 2. 推断用神类别并找用神地支
    use_god_category = _infer_use_god_category(question)
    use_god_branch = None
    use_god_pos = None
    if use_god_category == "世爻":
        use_god_branch = world_branch
        use_god_pos = world_pos
    else:
        for yao in yao_lines:
            if yao.get("six_relation") == use_god_category:
                use_god_branch = yao.get("earthly_branch", "")
                use_god_pos = yao.get("position")
                break
        # 用神不现则fallback到世爻
        if use_god_branch is None:
            use_god_branch = world_branch
            use_god_pos = world_pos

    # 3. 收集卦中所有地支（本卦 + 变卦 + 日月）
    present_branches = set()
    for yao in yao_lines:
        b = yao.get("earthly_branch", "")
        if b:
            present_branches.add(b)
    changed = result.get("changed_hexagram") or {}
    changed_name = changed.get("name")
    if changed_name:
        for pos_idx in range(1, 7):
            chg_branch = get_changed_hexagram_branch(changed_name, pos_idx)
            if chg_branch:
                present_branches.add(chg_branch)
    if month_branch:
        present_branches.add(month_branch)
    if day_branch:
        present_branches.add(day_branch)

    # 4. 找所有官鬼爻
    officer_lines = []
    for yao in yao_lines:
        if yao.get("six_relation") == "官鬼":
            officer_lines.append(yao)

    # 如果本卦无显式官鬼，检查伏藏官鬼
    if not officer_lines:
        hidden_analysis = result.get("advanced_analysis", {}).get("hidden_spirit_analysis", {})
        if isinstance(hidden_analysis, dict) and hidden_analysis.get("has_hidden_spirit"):
            for d in hidden_analysis.get("details", []):
                if d.get("missing_relation") == "官鬼":
                    hs = d.get("hidden_spirit", {})
                    officer_lines.append({
                        "position": hs.get("position", 0),
                        "name": hs.get("name", ""),
                        "earthly_branch": hs.get("branch", ""),
                        "six_relation": "官鬼",
                        "is_moving": False,
                        "is_hidden": True,
                    })

    if not officer_lines:
        return {
            "has_officer_tomb": False,
            "severity": "none",
            "scenarios": [],
            "officer_branches": [],
            "tomb_branch": "",
            "description": "本卦无官鬼爻，不论随官入墓",
            "score_modifier": 0.0,
            "classical_quote": "随官入墓最凶凶，世用临之祸不轻",
            "details": [],
        }

    # 5. 逐官鬼分析入墓
    scenarios = []
    details = []
    officer_branches_collected = []
    worst_severity = "none"
    total_score_modifier = 0.0
    primary_tomb_branch = ""

    for officer in officer_lines:
        off_branch = officer.get("earthly_branch", "")
        if not off_branch:
            continue
        off_pos = officer.get("position", 0)
        off_name = officer.get("name") or _pos_to_name(off_pos)
        off_element = _branch_element(off_branch)
        is_moving = officer.get("is_moving", False)

        officer_branches_collected.append(off_branch)

        # 官鬼五行对应的墓库地支
        tomb = TOMB_MAP.get(off_element, "")
        if not tomb:
            continue

        if not primary_tomb_branch:
            primary_tomb_branch = tomb

        # 场景a: 官鬼入墓 -- 墓库地支出现在本卦/变卦/日月中
        officer_in_tomb = tomb in present_branches
        self_tomb = (off_branch == tomb)

        if officer_in_tomb or self_tomb:
            if "官鬼入墓" not in scenarios:
                scenarios.append("官鬼入墓")
            source = "本卦/变卦/日月中" if officer_in_tomb else "本支即墓"
            details.append({
                "type": "官鬼入墓",
                "officer_branch": off_branch,
                "officer_element": off_element,
                "tomb_branch": tomb,
                "description": f"官鬼{off_element}({off_name}·{off_branch})入墓于{tomb}（{source}）",
            })
            if worst_severity == "none":
                worst_severity = "mild"
            total_score_modifier += (-0.2 if self_tomb else -0.3)

        # 场景b: 世随官入墓 -- 世爻地支 = 官鬼墓库
        if world_branch and world_branch == tomb:
            if "世随官入墓" not in scenarios:
                scenarios.append("世随官入墓")
            details.append({
                "type": "世随官入墓",
                "officer_branch": off_branch,
                "world_branch": world_branch,
                "tomb_branch": tomb,
                "description": f"世爻{world_branch}临官鬼{off_element}之墓{tomb}，自身随鬼入墓，凶象显著",
            })
            worst_severity = "severe"
            total_score_modifier += -1.0

        # 场景c: 用随官入墓 -- 用神地支 = 官鬼墓库
        if use_god_branch and use_god_branch == tomb:
            if "用随官入墓" not in scenarios:
                scenarios.append("用随官入墓")
            details.append({
                "type": "用随官入墓",
                "officer_branch": off_branch,
                "use_god_branch": use_god_branch,
                "use_god_category": use_god_category,
                "tomb_branch": tomb,
                "description": (
                    f"用神{use_god_category}({use_god_branch})临官鬼{off_element}之墓{tomb}，"
                    f"用神被鬼所困，极凶"
                ),
            })
            worst_severity = "severe"
            total_score_modifier += -1.5

        # 场景d: 鬼用同墓 -- 官鬼自身地支即墓 且 世/用也临此墓
        if off_branch == tomb and (world_branch == tomb or use_god_branch == tomb):
            if "鬼用同墓" not in scenarios:
                scenarios.append("鬼用同墓")
            details.append({
                "type": "鬼用同墓",
                "officer_branch": off_branch,
                "world_branch": world_branch,
                "use_god_branch": use_god_branch,
                "tomb_branch": tomb,
                "description": f"官鬼({off_branch})与世/用神同墓于{tomb}，鬼用同墓，灾难性凶象",
            })
            worst_severity = "catastrophic"
            total_score_modifier += -2.0

        # 场景e: 官鬼动化墓 -- 官鬼发动且变爻为墓库地支
        if is_moving and changed_name:
            chg_branch = get_changed_hexagram_branch(changed_name, off_pos)
            if chg_branch == tomb:
                if "官鬼动化墓" not in scenarios:
                    scenarios.append("官鬼动化墓")
                details.append({
                    "type": "官鬼动化墓",
                    "officer_branch": off_branch,
                    "changed_branch": chg_branch,
                    "tomb_branch": tomb,
                    "description": (
                        f"官鬼{off_name}({off_branch})动而化墓({chg_branch})，"
                        f"鬼动入墓，凶象加剧"
                    ),
                })
                if worst_severity in ("none", "mild"):
                    worst_severity = "severe"
                else:
                    worst_severity = "severe"
                total_score_modifier += -1.0

    # 6. 综合输出
    if not scenarios:
        return {
            "has_officer_tomb": False,
            "severity": "none",
            "scenarios": [],
            "officer_branches": officer_branches_collected,
            "tomb_branch": primary_tomb_branch,
            "description": (
                f"官鬼({','.join(officer_branches_collected)})未入墓"
                f"或世/用未随鬼入墓，无随官入墓凶象"
            ),
            "score_modifier": 0.0,
            "classical_quote": "随官入墓最凶凶，世用临之祸不轻",
            "details": [],
        }

    severity_text = {
        "mild": "轻微",
        "severe": "严重",
        "catastrophic": "极凶/灾难性",
    }

    scenario_descriptions = {
        "官鬼入墓": "官鬼入墓（鬼入墓中，凶象暗藏）",
        "世随官入墓": "世随官入墓（自身随鬼入墓，凶不可避）",
        "用随官入墓": "用随官入墓（用神随鬼入墓，事必遭凶）",
        "鬼用同墓": "鬼用同墓（官鬼与世用同归墓中，灾难性凶象）",
        "官鬼动化墓": "官鬼动化墓（鬼动入墓，凶象加剧）",
    }

    desc_parts = [scenario_descriptions.get(s, s) for s in scenarios]
    description = (
        f"检测到随官入墓格局（{severity_text.get(worst_severity, '')}）："
        f"{'、'.join(desc_parts)}。"
    )
    if worst_severity == "catastrophic":
        description += "此为极凶之象，占病/占讼尤忌，宜慎重对待。"
    elif worst_severity == "severe":
        description += "此为严重凶象，宜慎防祸患。"
    else:
        description += "官鬼入墓，其力受困，吉凶需综合判断。"

    return {
        "has_officer_tomb": True,
        "severity": worst_severity,
        "scenarios": scenarios,
        "officer_branches": officer_branches_collected,
        "tomb_branch": primary_tomb_branch,
        "description": description,
        "score_modifier": round(total_score_modifier, 2),
        "classical_quote": "随官入墓最凶凶，世用临之祸不轻",
        "details": details,
    }


# =============================================================================
# =============================================================================
# 分析段 18：八卦变爻深度推演（飞伏互变之动爻格局）
# =============================================================================

# 变爻格局规则表
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


def analyze_transformation_pattern(result):
    """
    八卦变爻深度推演：分析动爻排列规律及其附加意义。

    检查以下格局：
    - 连续三爻动：三个相邻动爻
    - 间隔动爻：1,3,5 或 2,4,6 交替
    - 上卦全动：四、五、上皆动
    - 下卦全动：初、二、三皆动
    - 对爻齐动：世爻与应爻同动
    - 用神原神齐动/用神忌神齐动

    返回：
        {
            "moving_positions": [int],
            "moving_count": int,
            "patterns": [str],
            "total_weight": float,
            "interpretation": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    # 世爻和应爻位置从爻中提取
    world_pos = 0
    response_pos = 0
    for yao in yao_lines:
        if yao.get("is_world"):
            world_pos = yao.get("position", 0)
        if yao.get("is_response"):
            response_pos = yao.get("position", 0)

    moving = []
    for yao in yao_lines:
        if yao.get("is_moving", False):
            moving.append(yao.get("position", 0))

    if len(moving) < 2:
        return {"pattern": None}

    patterns = []

    # 检查连续三爻动
    for i in range(1, 5):  # position 1~4 as starting point
        if all(p in moving for p in [i, i + 1, i + 2]):
            patterns.append("连续三爻动")
            break

    # 检查间隔动爻
    if moving == [1, 3, 5] or moving == [2, 4, 6]:
        patterns.append("间隔动爻")

    # 检查上卦全动 (positions 4,5,6)
    if all(p in moving for p in [4, 5, 6]):
        patterns.append("上卦全动")

    # 检查下卦全动 (positions 1,2,3)
    if all(p in moving for p in [1, 2, 3]):
        patterns.append("下卦全动")

    # 检查对爻齐动（世爻与应爻同动）
    if world_pos and response_pos and world_pos in moving and response_pos in moving:
        patterns.append("对爻齐动")

    # 检查用神原神齐动/用神忌神齐动
    # 需要从 thinking-chain 的用神信息获取
    question = result.get("question", "")
    use_god_cat = _infer_use_god_category(question)
    if use_god_cat and use_god_cat != "世爻":
        # 原神 = 生用神之五行对应的六亲
        use_god_elem = _relation_element(use_god_cat, hex_info.get("palace_element", ""))
        if use_god_elem:
            yuan_shen_elem = SHENG_WO.get(use_god_elem)  # 生我者为原神
            ji_shen_elem = KE_WO.get(use_god_elem)  # 克我者为忌神

            yuan_shen_rel = _element_to_relation(yuan_shen_elem, hex_info.get("palace_element", "")) if yuan_shen_elem else None
            ji_shen_rel = _element_to_relation(ji_shen_elem, hex_info.get("palace_element", "")) if ji_shen_elem else None

            use_god_moving = any(
                yao.get("is_moving") and yao.get("six_relation") == use_god_cat
                for yao in yao_lines
            )
            yuan_shen_moving = any(
                yao.get("is_moving") and yao.get("six_relation") == yuan_shen_rel
                for yao in yao_lines
            ) if yuan_shen_rel else False
            ji_shen_moving = any(
                yao.get("is_moving") and yao.get("six_relation") == ji_shen_rel
                for yao in yao_lines
            ) if ji_shen_rel else False

            if use_god_moving and yuan_shen_moving:
                patterns.append("用神原神齐动")
            if use_god_moving and ji_shen_moving:
                patterns.append("用神忌神齐动")

    total_weight = sum(
        TRANSFORMATION_PATTERNS.get(p, {}).get("weight", 1.0) for p in patterns
    )

    if patterns:
        interpretation = "；".join(
            TRANSFORMATION_PATTERNS.get(p, {}).get("advice", "") for p in patterns
        )
    else:
        interpretation = "无特殊格局"

    return {
        "moving_positions": moving,
        "moving_count": len(moving),
        "patterns": patterns,
        "total_weight": total_weight,
        "interpretation": interpretation,
    }


def _relation_element(relation, palace_element):
    """六亲 → 五行（辅助函数）"""
    # 六亲五行关系：我=宫五行
    # 父母=生我者（用SHENG_WO反推），子孙=我生者，官鬼=克我者，妻财=我克者，兄弟=同我
    mapping = {
        "父母": SHENG_WO.get(palace_element, ""),
        "子孙": SHENG_CYCLE.get(palace_element, ""),
        "官鬼": KE_WO.get(palace_element, ""),
        "妻财": KE_CYCLE.get(palace_element, ""),
        "兄弟": palace_element,
    }
    return mapping.get(relation, "")


def _element_to_relation(element, palace_element):
    """五行 → 六亲（辅助函数）"""
    if not element or not palace_element:
        return None
    if element == SHENG_WO.get(palace_element):
        return "父母"
    elif element == SHENG_CYCLE.get(palace_element):
        return "子孙"
    elif element == KE_WO.get(palace_element):
        return "官鬼"
    elif element == KE_CYCLE.get(palace_element):
        return "妻财"
    elif element == palace_element:
        return "兄弟"
    return None


# =============================================================================
# 分析段 19：飞伏神深度互断
# =============================================================================

def analyze_flying_hidden_interaction(result):
    """
    飞伏深度互断：飞神与伏神的生克制化关系分析。
    基于《火珠林》《卜筮正宗》伏神得出/不得出规则，
    细化飞神与伏神的五行生克关系及得出难易。

    返回：
        {
            "has_interaction": bool,
            "interactions": [
                {
                    "position": int,
                    "fei_shen": str,       # 飞神六亲
                    "fu_shen": str,        # 伏神名称
                    "relation": str,       # 关系定性
                    "can_emerge": bool,
                    "description": str,
                },
                ...
            ],
            "overall_emerge": bool,
        }
    """
    fu_analysis = result.get("advanced_analysis", {}).get("hidden_spirit_analysis", {})
    if not fu_analysis or not fu_analysis.get("has_hidden_spirit"):
        return {"has_interaction": False}

    details = fu_analysis.get("details", [])
    if not details:
        return {"has_interaction": False}

    interactions = []
    for fu in details:
        covering = fu.get("covering_spirit", {})  # 飞神
        hidden = fu.get("hidden_spirit", {})      # 伏神
        fei_elem = covering.get("element", "")
        fu_elem = hidden.get("element", "")
        can_emerge = fu.get("can_emerge", True)

        if not fei_elem or not fu_elem:
            continue

        # 飞伏关系定性
        if fei_elem == fu_elem:
            relation = "比和"  # 飞伏同类 → 伏得出易
        elif SHENG_CYCLE.get(fei_elem) == fu_elem:
            relation = "飞生伏"  # 飞神生伏神 → 伏神易出，受荫
        elif KE_CYCLE.get(fei_elem) == fu_elem:
            relation = "飞克伏"  # 飞神克伏神 → 伏神难出，受压
        elif SHENG_CYCLE.get(fu_elem) == fei_elem:
            relation = "伏生飞"  # 伏神泄气 → 伏得出但力弱
        else:
            relation = "伏克飞"  # 伏神克飞神 → 伏得出但多阻

        fu_name = hidden.get("six_relation", "伏神")
        fei_name = covering.get("six_relation", "")

        interactions.append({
            "position": hidden.get("position"),
            "fei_shen": fei_name,
            "fu_shen": fu_name,
            "fei_branch": covering.get("branch", ""),
            "fu_branch": hidden.get("branch", ""),
            "relation": relation,
            "can_emerge": can_emerge,
            "description": (
                f"{_pos_to_name(hidden.get('position', 0))}："
                f"飞{fei_name}({fei_elem})与伏{fu_name}({fu_elem})：{relation}，"
                f"{'伏得出' if can_emerge else '伏难出'}"
            ),
        })

    overall_emerge = all(i["can_emerge"] for i in interactions) if interactions else True

    return {
        "has_interaction": True,
        "interactions": interactions,
        "overall_emerge": overall_emerge,
        "summary": "；".join(i["description"] for i in interactions) if interactions else "无伏神",
    }


# =============================================================================
# 主入口：enhance_reading
# =============================================================================

def enhance_reading(result_dict):
    """
    对 liuyao_engine.py 产出的基础排盘结果进行经典深度分析。
    
    参数:
        result_dict: build_hexagram_result() 返回的字典
        
    返回:
        同一个字典（被原位修改），新增 'advanced_analysis' 键，
        包含 19 个经典分析段：
            - hidden_spirit_analysis:    伏藏分析
            - hidden_movement:           暗动分析
            - soul_hexagram:             游魂归魂卦（Gap 7）
            - monthly_break:             月破分析
            - triple_combo:              三合局分析
            - advance_retreat:           进退神分析
            - twelve_growth:             十二长生分析
            - clash_harmony:             六合六冲卦判断
            - repetition:                反吟伏吟判断
            - element_strength:          纳甲四柱旺衰总结
            - three_punishments:         三刑分析
            - hidden_spirit_scoring:     伏神得出不得出（优化版）
            - day_month_bonding:         日月合用神（Gap 5）
            - six_breaks:                六破系统（Gap 6）
            - desperate_relief:          绝处逢生（Gap 2）
            - transformation_pattern:    八卦变爻深度推演（动爻格局）
            - flying_hidden_interaction: 飞伏神深度互断（飞伏生克）
            - officer_tomb:              随官入墓（Gap 3）
            - nayin:                     六十甲子纳音取象

    用法：
        result = build_hexagram_result(...)
        result = enhance_reading(result)
        # result['advanced_analysis']['hidden_spirit_analysis'] ...

    注意：
        本函数会原位修改输入字典并返回它。如需保留原数据请先 copy。
    """
    if result_dict is None:
        return result_dict

    if not isinstance(result_dict, dict):
        raise TypeError("result_dict 应是由 build_hexagram_result() 返回的字典")

    # 检查必要字段
    if "original_hexagram" not in result_dict:
        raise ValueError("输入缺少 'original_hexagram' 字段")
    if "divination_time" not in result_dict:
        raise ValueError("输入缺少 'divination_time' 字段")

    # 执行各段分析
    result_dict["advanced_analysis"] = {
        "hidden_spirit_analysis": analyze_hidden_spirits(result_dict),
        "hidden_movement": analyze_hidden_movement(result_dict),
        "soul_hexagram": analyze_wandering_returning_soul(result_dict),
        "monthly_break": analyze_monthly_break(result_dict),
        "triple_combo": analyze_triple_combo(result_dict),
        "advance_retreat": analyze_advance_retreat(result_dict),
        "twelve_growth": analyze_twelve_growth(result_dict),
        "clash_harmony": analyze_clash_harmony(result_dict),
        "repetition": analyze_repetition(result_dict),
        "repetition_deep": analyze_repetition_deep(result_dict),
        "hexagram_body": analyze_hexagram_body(result_dict),
        "element_strength": analyze_element_strength(result_dict),
        "three_punishments": analyze_three_punishments(result_dict),
        "hidden_spirit_scoring": analyze_hidden_spirit_emergence(result_dict),
        "day_month_bonding": analyze_day_month_bonding(result_dict),
        "six_breaks": analyze_six_breaks(result_dict),
        "desperate_relief": analyze_desperate_relief(result_dict),
    }

    # 八卦变爻深度推演（动爻格局分析）
    result_dict["advanced_analysis"]["transformation_pattern"] = analyze_transformation_pattern(result_dict)

    # 飞伏神深度互断（需要引用伏藏分析的结果）
    result_dict["advanced_analysis"]["flying_hidden_interaction"] = analyze_flying_hidden_interaction(result_dict)

    # 随官入墓分析（需要引用伏藏分析的结果）
    result_dict["advanced_analysis"]["officer_tomb"] = analyze_officer_tomb(result_dict)

    # 六神（六兽）辅助分析——根据各爻六神 + 六亲 + 世应综合研判
    result_dict["advanced_analysis"]["six_spirit_analysis"] = _analyze_six_spirits(result_dict)

    # 纳音系统（六十甲子纳音取象）
    result_dict["advanced_analysis"]["nayin"] = analyze_nayin(result_dict)

    return result_dict


# -----------------------------------------------------------------------------
# 六神辅助分析（内部函数，由 enhance_reading 调用）
# -----------------------------------------------------------------------------

# 六神吉凶与象征（按《卜筮正宗·六神论》）
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


def _analyze_six_spirits(result_dict):
    """
    六神（六兽）辅助分析。

    根据各爻的六神叠加六亲+动静+世应，提供综合研判：
    - 用神/原神之六神：助力性质
    - 忌神/仇神之六神：阻力性质
    - 世应之六神：主体/客体之象
    """
    hex_info = result_dict.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    div_time = result_dict.get("divination_time", {})

    # 提取关键
    world_yao = None
    response_yao = None
    moving_yaos = []
    spirit_summary = []

    for yao in yao_lines:
        pos = yao.get("position")
        spirit = yao.get("six_spirit", "")
        relation = yao.get("six_relation", "")
        moving = yao.get("is_moving", False)
        empty = yao.get("is_empty", False)
        branch = yao.get("earthly_branch", "")
        line_name = yao.get("name", "")
        is_world = yao.get("is_world", False)
        is_response = yao.get("is_response", False)

        props = SIX_SPIRIT_PROPERTIES.get(spirit, {})
        entry = {
            "position": pos,
            "name": line_name,
            "six_spirit": spirit,
            "six_relation": relation,
            "earthly_branch": branch,
            "element": props.get("element", ""),
            "nature": props.get("nature", ""),
            "is_moving": moving,
            "is_empty": empty,
            "is_world": is_world,
            "is_response": is_response,
        }
        spirit_summary.append(entry)

        if is_world:
            world_yao = entry
        if is_response:
            response_yao = entry
        if moving:
            moving_yaos.append(entry)

    # 用神与六神（若能从 question_category / thinking_chain 获取更佳，此处用启发式判断）
    palace_element = hex_info.get("palace_element", "")
    # 六神与宫五行相同（比值）的加分（《黄金策》云："六神生旺则吉，克害则凶"）
    value_aligned = []
    for entry in spirit_summary:
        sp_elem = entry.get("element", "")
        if sp_elem and sp_elem == palace_element:
            value_aligned.append(entry)

    # 综合判断
    comment_parts = []
    if world_yao:
        comment_parts.append(
            f"世爻{world_yao['name']}临{world_yao['six_spirit']}"
            f"（{world_yao['nature']}），"
            f"{'同气于宫，根基尚稳' if world_yao.get('element') == palace_element else '与宫气异，主体有变'}"
        )
    if value_aligned:
        names = "、".join(f"{e['name']}({e['six_spirit']})" for e in value_aligned if not e.get("is_world"))
        if names:
            comment_parts.append(f"值宫五行之六神：{names}——与宫同气")
    if response_yao:
        comment_parts.append(
            f"应爻{response_yao['name']}临{response_yao['six_spirit']}（{response_yao['nature']}）"
        )

    # 动爻六神的特殊意义
    if moving_yaos:
        move_desc = []
        for m in moving_yaos:
            move_desc.append(
                f"{m['name']}{m['six_spirit']}动（{m['nature']}/{m['six_relation']}）"
            )
        comment_parts.append("动爻六神：" + "、".join(move_desc))

    # 六神生克综合（简化）：统计各六神出现频次
    spirit_count = {}
    for entry in spirit_summary:
        sp = entry.get("six_spirit", "")
        spirit_count[sp] = spirit_count.get(sp, 0) + 1

    return {
        "palace_element": palace_element,
        "day_stem": div_time.get("day_stem_branch", "")[:1] if div_time.get("day_stem_branch") else "",
        "lines": spirit_summary,
        "world_yao_spirit": world_yao,
        "response_yao_spirit": response_yao,
        "moving_yao_spirits": moving_yaos,
        "value_aligned_spirits": value_aligned,
        "spirit_count": spirit_count,
        "comment": "；".join(comment_parts) if comment_parts else "六神分布平稳，无特殊格局",
    }


# =============================================================================
# 测试用：快速验证语法和导入
# =============================================================================

if __name__ == "__main__":
    import json
    from liuyao_engine import build_hexagram_result, coin_toss
    from datetime import datetime

    # 简单测试
    now = datetime.now()
    yao = coin_toss()
    result = build_hexagram_result(
        yao, "测试：模块是否正常运行？", "测试",
        now.year, now.month, now.day, now.hour
    )

    # 应用高级分析
    result = enhance_reading(result)

    adv = result["advanced_analysis"]
    # 打印摘要
    for key in adv:
        section = adv[key]
        if isinstance(section, dict):
            summary = section.get("summary", "无")
            if key == "transformation_pattern":
                patterns = section.get("patterns", [])
                interp = section.get("interpretation", "")
                summary = f"格局：{'、'.join(patterns) if patterns else '无'}；{interp}"
            elif key == "flying_hidden_interaction":
                interactions = section.get("interactions", [])
                if interactions:
                    summary = "；".join(i.get("description", "") for i in interactions)
                else:
                    summary = section.get("summary", "无")
        elif isinstance(section, list):
            summary = f"{len(section)}条记录"
        else:
            summary = str(section)
        print(f"\n【{key}】")
        print(f"  {summary}")

    print("\n完整结果长度：", len(json.dumps(adv, ensure_ascii=False)))
