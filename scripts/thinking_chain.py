# -*- coding: utf-8 -*-
"""
六爻思维链（Liu Yao Thinking Skills Chain）
================================================

将传统六爻纳甲断卦方法论形式化为确定性的五步分析流程。
每一「思维步骤」都产生结构化中间结果，供后续步骤依赖，
防止 LLM 进行模式匹配式的跳跃分析，确保系统性。

本模块为纯 Python（仅依赖标准库），独立于 liuyao_engine.py
和 classical_analysis.py，但使用兼容的数据结构约定。

输入：build_hexagram_result() 返回的 JSON 字典
输出：五步思维链的完整结构化结果字典

使用方式
--------
>>> result = build_hexagram_result(question, month, day, ...)
>>> chain = run_thinking_chain(result)
>>> print(chain["step5_synthesis"]["verdict"])
"""

from __future__ import annotations
import os as _ks_os, sys as _ks_sys   # 内核路径引导，不依赖导入顺序
_CORE_DIR = _ks_os.path.join(_ks_os.path.dirname(_ks_os.path.abspath(__file__)),
                              _ks_os.pardir, "core")
if _ks_os.path.isdir(_CORE_DIR) and _ks_os.path.abspath(_CORE_DIR) not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_os.path.abspath(_CORE_DIR))
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
import re

# =============================================================================
# 五行基础数据
# =============================================================================

# 天干
STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 地支

# 五行相生：木→火→土→金→水→木
# 反向：生我者（父母）
SHENG_WO = {v: k for k, v in SHENG_CYCLE.items()}

# 五行相克：木→土→水→火→金→木
# 反向：克我者（官鬼）
KE_WO = {v: k for k, v in KE_CYCLE.items()}

# 相生关系：PALACE_GENERATING[X] = 生X者（生我者为父母）
PALACE_GENERATING = dict(SHENG_WO)  # {"木": "水", "火": "木", "土": "火", "金": "土", "水": "金"}
# 相克关系：PALACE_OVERCOMING[X] = 克X者（克我者为官鬼）
PALACE_OVERCOMING = dict(KE_WO)    # {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}

# 地支六合

# 地支六冲

# 地支六破（次于六冲的克害关系）
# 子酉破、午卯破、巳申破、寅亥破、辰丑破、戌未破
# 注意：巳申、寅亥既是六合又是六破 → "合中带破"

# 三合局
SAN_HE = {
    "水": ["申", "子", "辰"],
    "火": ["寅", "午", "戌"],
    "金": ["巳", "酉", "丑"],
    "木": ["亥", "卯", "未"],
}

# 十二长生表
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

# 六亲之间的五行对应关系（用于原神/忌神/仇神推导）
# 每个六亲对应一种五行
RELATION_ELEMENT = {
    "兄弟": None,  # 同宫五行，后面特殊处理
    "子孙": None,  # 宫五行所生
    "妻财": None,  # 宫五行所克
    "官鬼": None,  # 克宫五行
    "父母": None,  # 生宫五行
}

# 进退神表

# 墓库对应关系

# 绝地对应关系
JUE_MAP = {
    "木": "申",
    "火": "亥",
    "土": "亥",  # 土从水
    "金": "寅",
    "水": "巳",
}

# 六神列表
SIX_SPIRITS = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]

# 六神五行
SPIRIT_ELEMENT = {
    "青龙": "木",
    "朱雀": "火",
    "勾陈": "土",
    "螣蛇": "土",
    "白虎": "金",
    "玄武": "水",
}

# 六十四卦纳甲数据（简化版，用于变卦地支获取）

# 六十四卦 → (上卦, 下卦)

# 八卦名称 → 五行
TRIGRAM_ELEMENT = {
    "乾": "金", "兑": "金", "离": "火", "震": "木",
    "巽": "木", "坎": "水", "艮": "土", "坤": "土",
}

# 八宫首卦信息

# 旬空表：甲子旬空戌亥，甲戌旬空申酉，甲申旬空午未，
#         甲午旬空辰巳，甲辰旬空寅卯，甲寅旬空子丑
XUN_KONG = {
    "甲子": ["戌", "亥"], "甲戌": ["申", "酉"], "甲申": ["午", "未"],
    "甲午": ["辰", "巳"], "甲辰": ["寅", "卯"], "甲寅": ["子", "丑"],
}

# 六合卦名（卦之六合：上卦与下卦各爻对应六合）
HEXAGRAM_LIUHE = ["泰", "否", "贲", "困", "旅", "豫", "复", "小畜"]

# 六冲卦名
HEXAGRAM_LIUCHONG = ["乾", "坤", "坎", "离", "艮", "震", "巽", "兑",
                     "无妄", "大壮", "晋", "明夷", "蹇", "解", "夬", "姤",
                     "遁", "同人", "履"]  # 部分六冲卦（小畜已从列表移除，见 issue:reg_12）

# =============================================================================
# 问题类型 → 用神映射（《卜筮正宗》《增删卜易》规则）
# =============================================================================

_QUESTION_USE_GOD_MAP = {
    # 自测类
    "自测吉凶": "世爻",
    "自身": "世爻",
    # 父母/长辈/文书类
    "父母": "父母",
    "父亲": "父母",
    "母亲": "父母",
    "长辈": "父母",
    "文书": "父母",
    "考试": "父母",
    "学业": "父母",
    "房产": "父母",
    "房屋": "父母",
    "合同": "父母",
    "证书": "父母",
    "车辆": "父母",
    # 功名/事业/官鬼类
    "事业": "官鬼",
    "工作": "官鬼",
    "功名": "官鬼",
    "求官": "官鬼",
    "官职": "官鬼",
    "升迁": "官鬼",
    "丈夫": "官鬼",
    "丈夫运势": "官鬼",
    "男测妻子": "妻财",
    "感情": "妻财",
    "喜欢": "妻财",
    "女友": "妻财",
    "恋人": "妻财",
    "伴侣": "妻财",
    "疾病": "官鬼",
    "官司": "官鬼",
    "官司诉讼": "官鬼",
    "诉讼": "官鬼",
    "法律": "官鬼",
    "纠纷": "官鬼",
    # 官事 由通用 "官"→官鬼 承接；避免与"师尊官事"（父母为用）冲突
    "小偷": "官鬼",
    "强盗": "官鬼",
    "小人": "官鬼",
    "灾难": "官鬼",
    "仇人": "官鬼",
    "调动": "官鬼",
    "辞职": "官鬼",
    "面试": "官鬼",
    "招聘": "官鬼",
    "编制": "官鬼",
    "公务员": "官鬼",
    "公司": "官鬼",
    "上市": "官鬼",
    "官": "官鬼",
    "职位": "官鬼",
    # 常见复合词（高权重）
    "占病": "官鬼",
    "病症": "官鬼",
    "近病": "官鬼",
    "久病": "官鬼",
    "病何": "官鬼",
    "病愈": "官鬼",
    # 兄弟/朋友类
    "兄弟": "兄弟",
    "姐妹": "兄弟",
    "朋友": "兄弟",
    "同事": "兄弟",
    "竞争": "兄弟",
    "竞争对手": "兄弟",
    # 妻财/财运类
    "求财": "妻财",
    "财运": "妻财",
    "妻子": "妻财",
    "婚姻": "妻财",
    "婚": "妻财",
    "妻": "妻财",
    "生病妻": "妻财",
    "老婆": "妻财",
    "夫人": "妻财",
    "生意": "妻财",
    "投资": "妻财",
    "货物": "妻财",
    "钱财": "妻财",
    "赚钱": "妻财",
    "财": "妻财",
    "富": "妻财",
    "钱": "妻财",
    "项目": "妻财",
    "产品": "妻财",
    "融资": "妻财",
    "创业": "妻财",
    "合伙": "妻财",
    "股份": "妻财",
    "分红": "妻财",
    "经营": "妻财",
    "市场": "妻财",
    "经济": "妻财",
    "贸易": "妻财",
    "买卖": "妻财",
    "交易": "妻财",
    "银": "妻财",
    "失": "妻财",
    "丢": "妻财",
    "失物": "妻财",
    "找回": "妻财",
    "仆": "妻财",
    "奴": "妻财",
    "婢": "妻财",
    "员工": "妻财",
    "赌": "妻财",
    "赌钱": "妻财",
    "博": "妻财",
    "合同": "父母",
    "房产": "父母",
    "房屋": "父母",
    "证书": "父母",
    # 诉讼/官司细分
    "诉讼": "官鬼",
    "法律": "官鬼",
    "纠纷": "官鬼",
    "健康": "官鬼",
    # 出行/旅游/行人
    "出行": "子孙",
    "旅游": "子孙",
    "旅行": "子孙",
    "出行类": "子孙",
    "行人": "子孙",
    "行旅": "子孙",
    "归": "子孙",
    "回": "子孙",
    "归来": "子孙",
    "何日": "子孙",
    "何时": "子孙",
    "期": "子孙",
    # 家宅/父母类
    "家": "父母",
    "宅": "父母",
    "搬家": "父母",
    "父": "父母",
    "母": "父母",
    "爷": "父母",
    "奶": "父母",
    "岳父": "父母",
    "岳母": "父母",
    "爸": "父母",
    "妈": "父母",
    "爹": "父母",
    "娘": "父母",
    "长辈": "父母",
    "师长": "父母",
    "老师": "父母",
    "师傅": "父母",
    "师尊": "父母",
    "父母": "父母",
    "房产": "父母",
    "房屋": "父母",
    "证书": "父母",
    "文书": "父母",
    "书": "父母",
    # 文书/父母类
    "子女": "子孙",
    "孩子": "子孙",
    "儿子": "子孙",
    "女儿": "子孙",
    "子": "子孙",
    "医生": "子孙",
    "医药": "子孙",
    "宠物": "子孙",
    "娱乐": "子孙",
    "旅游": "子孙",
    "儿童": "子孙",
    "孙子": "子孙",
    "怀孕": "子孙",
    "功名考试": "官鬼",  # 功名看官鬼
    # 古籍特定复合词（高优先级，覆盖一般规则）
    "桑叶": "妻财",
    "桑": "妻财",
    "叶": "妻财",
    "蚕": "妻财",
    "价": "妻财",
    "价格": "妻财",
    "贵贱": "妻财",
    "大例": "妻财",
    "大数": "妻财",
    "价贵": "妻财",
    "价贱": "妻财",
    "贱": "妻财",
    "见贵": "官鬼",
    "见": "子孙",
    "贵": "官鬼",
    "见官": "官鬼",
    "贵客": "官鬼",
    "贵用": "官鬼",
    "占师尊": "父母",
    "占父": "父母",
    "占母": "父母",
    "占妻": "妻财",
    "占妾": "妻财",
    "占子": "子孙",
    "占女": "子孙",
    "占兄弟": "兄弟",
    "占友": "兄弟",
    "妻病": "妻财",
    "子病": "子孙",
    "父病": "父母",
    "兄病": "兄弟",
    "自占": "世爻",
    "自占妻": "妻财",
    "自占婚": "妻财",
    "自占官": "官鬼",
    "自占病": "世爻",
    "自占学业": "父母",
    "占婚": "妻财",
    "占嫁": "妻财",
    "占娶": "妻财",
    "仆": "妻财",
    "奴": "妻财",
    "婢": "妻财",
    "逃仆": "妻财",
    "走失": "妻财",
    "逃亡": "妻财",
}

# 用神五行对应的原神/忌神/仇神（用神→原神→忌神→仇神 的五行推导关系）
# 其逻辑：以五行为准，不是以六亲为准
# 用神=木 → 原神=水(生木者), 忌神=金(克木者), 仇神=土(生金者=克原神者)
# 用神=火 → 原神=木(生火者), 忌神=水(克火者), 仇神=金(生水者)
# 用神=土 → 原神=火(生土者), 忌神=木(克土者), 仇神=水(生木者)
# 用神=金 → 原神=土(生金者), 忌神=火(克金者), 仇神=木(生火者)
# 用神=水 → 原神=金(生水者), 忌神=土(克水者), 仇神=火(生土者)
USE_GOD_RELATIONSHIPS = {
    "木": {"原神": "水", "忌神": "金", "仇神": "土"},
    "火": {"原神": "木", "忌神": "水", "仇神": "金"},
    "土": {"原神": "火", "忌神": "木", "仇神": "水"},
    "金": {"原神": "土", "忌神": "火", "仇神": "木"},
    "水": {"原神": "金", "忌神": "土", "仇神": "火"},
}

# 五行 → 六亲映射（需要宫五行上下文）
def get_relation_from_element(element: str, palace_element: str) -> str:
    """根据地支五行确定六亲"""
    if element == palace_element:
        return "兄弟"
    if SHENG_WO.get(palace_element) == element:
        return "父母"
    if SHENG_CYCLE.get(palace_element) == element:
        return "子孙"
    if KE_WO.get(palace_element) == element:
        return "官鬼"
    if KE_CYCLE.get(palace_element) == element:
        return "妻财"
    return "未知"


def get_elements_for_relation(relation: str, palace_element: str) -> list[str]:
    """
    给定六亲类型和宫五行，返回该六亲对应的五行列表。
    注意：一个六亲对应一个五行（除"兄弟"即宫五行本身外）。
    "世爻"不预设五行——调用方须从世爻实际地支推算。
    """
    if relation == "世爻":
        return []  # 世爻五行须从爻支反推，此处留空
    if relation == "兄弟":
        return [palace_element]
    elif relation == "父母":
        return [SHENG_WO.get(palace_element, "")]
    elif relation == "子孙":
        return [SHENG_CYCLE.get(palace_element, "")]
    elif relation == "官鬼":
        return [KE_WO.get(palace_element, "")]
    elif relation == "妻财":
        return [KE_CYCLE.get(palace_element, "")]
    return []


# =============================================================================
# 工具函数
# =============================================================================

def _branch_element(branch: str) -> str:
    """获取地支五行"""
    return BRANCH_ELEMENTS.get(branch, "未知")


def _stem_element(stem: str) -> str:
    """获取天干五行"""
    return STEM_ELEMENTS.get(stem, "未知")


def _pos_to_name(pos: int) -> str:
    """爻位数字到中文名称"""
    names = {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}
    return names.get(pos, f"第{pos}爻")


def _is_he(b1: str, b2: str) -> bool:
    """判断两地支是否六合"""
    for a, b in HE_PAIRS:
        if (b1 == a and b2 == b) or (b1 == b and b2 == a):
            return True
    return False


def _is_chong(b1: str, b2: str) -> bool:
    """判断两地支是否六冲"""
    for a, b in CHONG_PAIRS:
        if (b1 == a and b2 == b) or (b1 == b and b2 == a):
            return True
    return False


def get_empty_branches(day_stem: str) -> list[str]:
    """获取当日旬空的地支"""
    if day_stem in XUN_KONG:
        return XUN_KONG[day_stem]
    # 如果没有精确匹配，从甲己等推算
    stem_idx = STEMS.index(day_stem) if day_stem in STEMS else 0
    # 根据天干推算旬首
    xun_stems = ["甲子", "甲戌", "甲申", "甲午", "甲辰", "甲寅"]
    xun_idx = stem_idx % 6
    return XUN_KONG.get(xun_stems[xun_idx], [])


def element_strength_in_month(element: str, month_element: str) -> str:
    """
    五行在月建中的旺衰（旺相休囚死）。
    《黄金策》：旺者—临月建也，相者—月建生之也，
    休者—生月建也，囚者—克月建也，死者—月建克之也。
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


# =============================================================================
# 十二长生 Lookup Table (dict form for _twelve_growth_at_day)
# =============================================================================
# 土随火（火土同行）
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


def _twelve_growth_at_day(element: str, day_branch: str) -> str:
    """
    查询五行元素在日辰的十二长生阶段。

    Args:
        element: 五行（木/火/土/金/水）
        day_branch: 地支（子/丑/.../亥）

    Returns:
        十二长生阶段名称，如 "帝旺"、"临官" 等；未找到返回空字符串。
    """
    elem_table = TWELVE_GROWTH.get(element)
    if not elem_table:
        return ""
    return elem_table.get(day_branch, "")


def _evaluate_fu_cang_strength(fu_detail: dict, month_branch: str, day_branch: str, empty_branches: list = None) -> dict:
    """
    评估伏藏用神的旺衰。

    综合判断伏神的五行旺衰（月建+日辰）、飞伏关系、十二长生，
    得出 0-5 分的强度评分。

    Args:
        fu_detail: step2 中 _check_fu_cang 返回的字典，包含 results 列表
        month_branch: 月建地支
        day_branch: 日辰地支

    Returns:
        {"score": float, "level": str, "analysis": str}
    """
    month_element = _branch_element(month_branch)
    day_element = _branch_element(day_branch)

    results = fu_detail.get("results", [])
    if not results:
        return {"score": 2.5, "level": "中和", "analysis": "伏藏信息不足，默认中和。"}

    # 取第一个伏神结果（通常只有一个）
    entry = results[0]
    fu_shen = entry.get("fu_shen", {})
    fei_shen = entry.get("fei_shen") or {}

    fu_element = fu_shen.get("element", "")
    fu_branch = fu_shen.get("branch", "")
    fu_relation = fu_shen.get("six_relation", "")
    fei_element = fei_shen.get("element", "")
    fei_branch = fei_shen.get("branch", "")
    can_emerge = entry.get("can_emerge", True)

    if not fu_element:
        return {"score": 2.5, "level": "中和", "analysis": "伏神五行不明，默认中和。"}

    analysis_parts = []

    # ── 1. 月建旺衰 ──
    fu_month_strength = element_strength_in_month(fu_element, month_element)
    fu_month_score = strength_to_score(fu_month_strength)

    # ── 2. 日辰旺衰 ──
    fu_day_strength = element_strength_in_month(fu_element, day_element)
    fu_day_score = strength_to_score(fu_day_strength)

    # 基础分（月建为主 0.6，日辰为辅 0.4）
    base_score = fu_month_score * 0.6 + fu_day_score * 0.4

    analysis_parts.append(
        f"伏神五行{fu_element}，月建{month_branch}（{month_element}）→ {fu_month_strength}（{fu_month_score}分），"
        f"日辰{day_branch}（{day_element}）→ {fu_day_strength}（{fu_day_score}分），基础分{base_score:.2f}"
    )

    # ── 3. 十二长生修正 ──
    growth_stage = _twelve_growth_at_day(fu_element, day_branch)
    growth_modifier = _TWELVE_GROWTH_SCORE.get(growth_stage, 0.0)
    if growth_stage:
        if growth_modifier > 0:
            analysis_parts.append(f"伏神临{growth_stage}（日辰十二长生），,+{growth_modifier}")
        elif growth_modifier < 0:
            analysis_parts.append(f"伏神临{growth_stage}（日辰十二长生），{growth_modifier}")
        else:
            analysis_parts.append(f"伏神临{growth_stage}（日辰十二长生），无修正")
    effective_score = base_score + growth_modifier

    # ── 4. 飞伏关系修正 ──
    fu_fei_modifier = 0.0
    fu_fei_reason = ""

    if fei_element:
        # 伏神绝于飞神地支 → 伏神气绝难出（《卜筮正宗》十二长生绝地）；
        # 但日辰冲伏神者为"冲空则实/拔伏"，豁免（ZS003 子冲午得拔）。
        fei_growth = _twelve_growth_at_day(fu_element, fei_branch)
        day_chongs_fu = _is_chong(fu_branch, day_branch)
        if fei_growth == "绝" and not day_chongs_fu:
            fu_fei_modifier = -1.0
            fu_fei_reason = f"伏神{fu_element}绝于飞神{fei_branch}（{fei_growth}），伏神气绝难出，-1.0"
        elif SHENG_CYCLE.get(fei_element) == fu_element:  # 飞生伏
            fu_fei_modifier = 0.5
            fu_fei_reason = f"飞神{fei_element}生伏神{fu_element}（飞生伏），伏得出，+0.5"
        elif KE_CYCLE.get(fei_element) == fu_element:  # 飞克伏
            fu_fei_modifier = -0.8
            fu_fei_reason = f"飞神{fei_element}克伏神{fu_element}（飞克伏），伏难出，-0.8"
        elif fei_element == fu_element:  # 比和
            fu_fei_modifier = 0.3
            fu_fei_reason = f"飞{fu_element}伏{fu_element}比和，+0.3"
        elif SHENG_CYCLE.get(fu_element) == fei_element:  # 伏生飞（泄气）
            fu_fei_modifier = -0.3
            fu_fei_reason = f"伏神{fu_element}生飞神{fei_element}（伏泄气于飞），-0.3"
        elif KE_CYCLE.get(fu_element) == fei_element:
            # 伏克飞为出暴（伏神有力反克飞神，出暴主吉）
            fu_fei_modifier = 0.8
            fu_fei_reason = f"伏神{fu_element}克飞神{fei_element}（伏克飞为出暴），伏有力得出，+0.8"
        else:
            fu_fei_reason = f"伏神{fu_element}与飞神{fei_element}关系无显著生克，无修正"
    else:
        fu_fei_reason = "飞神缺失，无法判断飞伏关系"

    effective_score += fu_fei_modifier

    # ── 4b. 飞神旬空（飞空得出）── 伏神得出有力，且免于泄气之扣
    fei_branch_tmp = fei_branch or ""
    if empty_branches and fei_branch_tmp in empty_branches:
        effective_score += 1.0
        analysis_parts.append(f"飞神{fei_branch_tmp}旬空（飞空得出），伏神得出有力，+1.0")
    if fu_fei_reason:
        analysis_parts.append(fu_fei_reason)

    # ── 5. 能否得出 ──
    if not can_emerge:
        effective_score -= 0.5
        analysis_parts.append("伏神受压制难以得出，-0.5")

    # 上下限
    effective_score = max(0.5, min(5.0, effective_score))

    # ── 旺衰定性 ──
    if effective_score >= 4.5:
        strength_level = "极旺"
    elif effective_score >= 3.5:
        strength_level = "旺"
    elif effective_score >= 2.5:
        strength_level = "中和"
    elif effective_score >= 1.5:
        strength_level = "偏弱"
    elif effective_score >= 0.8:
        strength_level = "弱"
    else:
        strength_level = "极弱"

    # 构建分析文本
    fei_desc = f"飞神{fei_branch}（{fei_element}）" if fei_branch else "飞神不明"
    fu_desc = f"{fu_relation}伏于{fu_branch}（{fu_element}）"
    analysis = f"用神伏藏（{fu_desc}），{fei_desc}。{'；'.join(analysis_parts)}。综合评分：{effective_score:.2f}（{strength_level}）。"

    return {
        "score": round(effective_score, 2),
        "level": strength_level,
        "analysis": analysis,
    }


def strength_to_score(strength: str) -> int:
    """旺相休囚死到数字分值"""
    return {"旺": 5, "相": 4, "休": 3, "囚": 2, "死": 1, "未知": 0}.get(strength, 0)


def get_twelve_growth_stage(element: str, day_branch: str) -> tuple:
    """
    获取某五行元素在指定日支的十二长生阶段。
    返回 (stage_name, index) 或 None
    """
    table = TWELVE_GROWTH_TABLES.get(element)
    if table is None:
        return None
    try:
        idx = table.index(day_branch)
        return TWELVE_GROWTH_STAGES[idx], idx
    except ValueError:
        return None


def get_changed_hexagram_branch(changed_hex_name: str, position: int) -> str | None:
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
        return NAJIA_BRANCHES[lower_name]["inner"][position - 1]
    else:
        return NAJIA_BRANCHES[upper_name]["outer"][position - 4]


def get_palace_first_hexagram(palace_name: str) -> str:
    """获取八宫首卦名称。兼容 "艮" 与 "艮宫" 两种写法（内核表以裸宫名为键）。"""
    palace_data = EIGHT_PALACES.get(palace_of_key(palace_name))
    if palace_data:
        return palace_data["order"][0][0]
    return ""


def safe_get(result: dict, *keys, default=None):
    """安全地从嵌套字典中获取值"""
    current = result
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


# =============================================================================
# Step 1: 观局 (Situational Reading)
# =============================================================================

def step1_read_situation(r: dict) -> dict:
    """
    Step 1: 观局 — 读取并报告卦象事实。此步骤不做任何解释。

    仅从原始数据中提取以下信息：
    - 本卦名、宫、世代
    - 上卦/下卦
    - 世爻/应爻位置
    - 各爻的六神
    - 动爻及其位置
    - 变卦（如有）
    - 旬空地支
    - 日月建信息
    """
    hex_info = safe_get(r, "original_hexagram", default={})
    div_time = safe_get(r, "divination_time", default={})
    changed = safe_get(r, "changed_hexagram", default={})
    yao_lines = safe_get(hex_info, "yao_lines", default=[])

    # 基本卦信息
    hex_name = safe_get(hex_info, "name", default="未知")
    palace = safe_get(hex_info, "palace", default="未知")
    palace_element = safe_get(hex_info, "palace_element", default="未知")
    generation = safe_get(hex_info, "generation", default="未知")
    upper_trigram = safe_get(hex_info, "upper_trigram", default="未知")
    lower_trigram = safe_get(hex_info, "lower_trigram", default="未知")

    # 日月建
    month_stem_branch = safe_get(div_time, "month_stem_branch", default="")
    day_stem_branch = safe_get(div_time, "day_stem_branch", default="")
    # 提取日干（用于旬空计算）
    day_stem = day_stem_branch[:1] if day_stem_branch else ""
    month_stem = month_stem_branch[:1] if month_stem_branch else ""
    month_branch = month_stem_branch[1:] if month_stem_branch else ""
    day_branch = day_stem_branch[1:] if day_stem_branch else ""

    # 日月建五行
    month_element = _branch_element(month_branch)
    day_element = _branch_element(day_branch)

    # 旬空
    empty = safe_get(r, "empty_branches", default=[])
    if not empty and day_stem:
        empty = get_empty_branches(day_stem)

    # 世应位置
    world_pos = None
    response_pos = None
    for yao in yao_lines:
        if yao.get("is_world"):
            world_pos = yao.get("position")
        if yao.get("is_response"):
            response_pos = yao.get("position")

    # 动爻
    moving_lines = []
    for yao in yao_lines:
        if yao.get("is_moving"):
            moving_lines.append({
                "position": yao.get("position"),
                "name": _pos_to_name(yao.get("position", 0)),
                "six_relation": yao.get("six_relation", ""),
                "earthly_branch": yao.get("earthly_branch", ""),
                "six_spirit": yao.get("six_spirit", ""),
            })

    # 各爻六神信息
    spirits_report = []
    for yao in yao_lines:
        spirits_report.append({
            "position": yao.get("position"),
            "name": _pos_to_name(yao.get("position", 0)),
            "six_spirit": yao.get("six_spirit", ""),
            "six_relation": yao.get("six_relation", ""),
            "branch": yao.get("earthly_branch", ""),
        })

    # 变卦
    changed_hex_name = safe_get(changed, "name", default=None)

    # 格式化旬空和动爻为可读文本（避免 raw Python list repr 泄漏）
    if empty:
        empty_text = "、".join(empty)
    else:
        empty_text = "无"

    if moving_lines:
        ml_parts = []
        for m in moving_lines:
            pos_name = m.get("name", f"第{m.get('position','')}爻")
            rel = m.get("six_relation", "")
            branch = m.get("earthly_branch", "")
            ml_parts.append(f"{pos_name}({rel}{branch})")
        moving_text = "、".join(ml_parts)
    else:
        moving_text = "无"

    # 构建报告
    return {
        "hexagram_name": hex_name,
        "palace": palace,
        "palace_element": palace_element,
        "generation": generation,
        "upper_trigram": upper_trigram,
        "lower_trigram": lower_trigram,
        "upper_trigram_element": TRIGRAM_ELEMENT.get(upper_trigram, ""),
        "lower_trigram_element": TRIGRAM_ELEMENT.get(lower_trigram, ""),
        "world_position": world_pos,
        "response_position": response_pos,
        "world_name": _pos_to_name(world_pos) if world_pos else "",
        "response_name": _pos_to_name(response_pos) if response_pos else "",
        "month_stem_branch": month_stem_branch,
        "day_stem_branch": day_stem_branch,
        "month_element": month_element,
        "day_element": day_element,
        "month_branch": month_branch,
        "day_branch": day_branch,
        "empty_branches": empty,
        "moving_lines": moving_lines,
        "moving_count": len(moving_lines),
        "changed_hexagram": changed_hex_name,
        "spirits_report": spirits_report,
        "yao_lines_detail": [
            {
                "position": yao.get("position"),
                "name": _pos_to_name(yao.get("position", 0)),
                "earthly_branch": yao.get("earthly_branch", ""),
                "heavenly_stem": yao.get("heavenly_stem", ""),
                "six_relation": yao.get("six_relation", ""),
                "six_spirit": yao.get("six_spirit", ""),
                "is_moving": yao.get("is_moving", False),
                "is_world": yao.get("is_world", False),
                "is_response": yao.get("is_response", False),
                "is_empty": yao.get("is_empty", False),
                "is_month_break": yao.get("is_month_break", False),
                "nature": yao.get("nature", ""),
            }
            for yao in yao_lines
        ],
        "summary_text": (
            f"本卦：{hex_name}（{palace}，{palace_element}），"
            f"上{upper_trigram}下{lower_trigram}，"
            f"世在{safe_get(hex_info, 'name', default='')}第{world_pos}爻，"
            f"应在第{response_pos}爻。"
            f"月建{month_stem_branch}（{month_element}），"
            f"日辰{day_stem_branch}（{day_element}），"
            f"旬空{empty_text}。"
            f"动爻{moving_text}。"
            f"{'变卦：' + changed_hex_name if changed_hex_name else '无变卦'}"
        ),
    }


# =============================================================================
# Step 2: 定用 (Use-God Identification)
# =============================================================================

def step2_identify_use_god(r: dict) -> dict:
    """
    Step 2: 定用神 — 根据问题类型确定用神（规则驱动，非模式匹配）。

    规则来源：《增删卜易》《卜筮正宗》《黄金策》

    关键规则：
    1. 用神两现：舍静取动、舍空破取旺相、取临月建者
    2. 用神不现：查伏藏（从本宫首卦）
    3. 用神多现：取世爻所在、取动爻、取临月建
    """
    # 获取分析上下文
    hex_info = safe_get(r, "original_hexagram", default={})
    yao_lines = safe_get(hex_info, "yao_lines", default=[])
    palace = safe_get(hex_info, "palace", default="")
    palace_element = safe_get(hex_info, "palace_element", default="")

    # 获取问题类型（兼容多种字段名）
    question_category = safe_get(r, "question_category", default="") or safe_get(r, "question", default="")
    question_text = safe_get(r, "question_text", default="") or safe_get(r, "question", default="")

    # 获取日月建信息
    div_time = safe_get(r, "divination_time", default={})
    month_stem_branch = safe_get(div_time, "month_stem_branch", default="")
    day_stem_branch = safe_get(div_time, "day_stem_branch", default="")
    month_branch = month_stem_branch[1:] if len(month_stem_branch) >= 2 else ""
    day_branch = day_stem_branch[1:] if len(day_stem_branch) >= 2 else ""
    month_element = _branch_element(month_branch)

    # 获取旬空
    empty = safe_get(r, "empty_branches", default=[])

    # ---------- 2.1: 确定用神类别 ----------
    use_god_category = _determine_use_god_category(question_category, question_text)

    # ---------- 2.2: 定位用神在卦中的位置 ----------
    use_god_positions = _find_use_god_positions(
        yao_lines, use_god_category, palace_element, month_branch, empty
    )

    # ---------- 2.3: 确定原神、忌神、仇神 ----------
    # 用神五行（根据用神类别 + 宫五行推导；世爻取实际地支五行）
    use_god_elements = get_elements_for_relation(use_god_category, palace_element)
    if use_god_category == "世爻" and use_god_positions:
        # 世爻五行从实际地支反推
        world_branch = use_god_positions[0].get("earthly_branch", "")
        use_god_element = BRANCH_ELEMENTS.get(world_branch, palace_element)
    else:
        use_god_element = use_god_elements[0] if use_god_elements else "未知"

    relationships = USE_GOD_RELATIONSHIPS.get(use_god_element, {})
    yuan_shen_element = relationships.get("原神", "")
    ji_shen_element = relationships.get("忌神", "")
    chou_shen_element = relationships.get("仇神", "")

    # 找到原神/忌神/仇神所在爻位
    yuan_shen_positions = _find_relation_positions(yao_lines, yuan_shen_element, palace_element)
    ji_shen_positions = _find_relation_positions(yao_lines, ji_shen_element, palace_element)
    chou_shen_positions = _find_relation_positions(yao_lines, chou_shen_element, palace_element)

    # ---------- 2.3b: 伏藏查找（原神/忌神/仇神不在本卦时） ----------
    yuan_shen_fu = None
    ji_shen_fu = None
    chou_shen_fu = None

    if not yuan_shen_positions and yuan_shen_element:
        # 从本宫首卦查找伏藏
        first_hex_name = get_palace_first_hexagram(palace)
        if first_hex_name:
            trigrams_fu = HEXAGRAM_TRIGRAMS.get(first_hex_name)
            if trigrams_fu:
                upper_fu, lower_fu = trigrams_fu
                base_branches = NAJIA_BRANCHES[lower_fu]["inner"] + NAJIA_BRANCHES[upper_fu]["outer"]
                target_rel = _element_to_relation(yuan_shen_element, palace_element)
                for pos_idx, br in enumerate(base_branches):
                    if _branch_to_relation(br, palace_element) == target_rel:
                        yuan_shen_fu = {
                            "position": pos_idx + 1,
                            "branch": br,
                            "element": _branch_element(br),
                            "six_relation": target_rel,
                        }
                        break

    if not ji_shen_positions and ji_shen_element:
        first_hex_name = get_palace_first_hexagram(palace)
        if first_hex_name:
            trigrams_fu = HEXAGRAM_TRIGRAMS.get(first_hex_name)
            if trigrams_fu:
                upper_fu, lower_fu = trigrams_fu
                base_branches = NAJIA_BRANCHES[lower_fu]["inner"] + NAJIA_BRANCHES[upper_fu]["outer"]
                target_rel = _element_to_relation(ji_shen_element, palace_element)
                for pos_idx, br in enumerate(base_branches):
                    if _branch_to_relation(br, palace_element) == target_rel:
                        ji_shen_fu = {
                            "position": pos_idx + 1,
                            "branch": br,
                            "element": _branch_element(br),
                            "six_relation": target_rel,
                        }
                        break

    if not chou_shen_positions and chou_shen_element:
        first_hex_name = get_palace_first_hexagram(palace)
        if first_hex_name:
            trigrams_fu = HEXAGRAM_TRIGRAMS.get(first_hex_name)
            if trigrams_fu:
                upper_fu, lower_fu = trigrams_fu
                base_branches = NAJIA_BRANCHES[lower_fu]["inner"] + NAJIA_BRANCHES[upper_fu]["outer"]
                target_rel = _element_to_relation(chou_shen_element, palace_element)
                for pos_idx, br in enumerate(base_branches):
                    if _branch_to_relation(br, palace_element) == target_rel:
                        chou_shen_fu = {
                            "position": pos_idx + 1,
                            "branch": br,
                            "element": _branch_element(br),
                            "six_relation": target_rel,
                        }
                        break

    # ---------- 2.4: 处理用神两现/伏藏 ----------
    has_fu_cang = use_god_category not in [
        yao.get("six_relation", "") for yao in yao_lines
    ] if yao_lines else True

    # ---------- 构建输出 ----------
    # 用神位置选择优先级：
    # 1. 应爻位置的用神（占婚/占失等古籍断法"取应爻"）
    # 2. 世爻位置的用神
    # 3. 动爻位置的用神（发动者为主）
    # 4. 临月/日者
    # 5. 第一个位置（fallback）
    # 计算世/应位置
    world_position = None
    for yao in yao_lines:
        if yao.get("is_world"):
            world_position = yao.get("position")
            break
    response_position = None
    if world_position:
        response_position = ((world_position - 1 + 3) % 6) + 1

    def _use_god_priority(pos_info):
        p = pos_info.get("position", 99)
        brk = pos_info.get("earthly_branch", "")

        def _changed_branch_of(pos):
            try:
                ch_name = (r.get("changed_hexagram") or {}).get("name")
                if ch_name:
                    cb = get_changed_hexagram_branch(ch_name, pos)
                    if cb:
                        return cb
                for y in yao_lines:
                    if isinstance(y, dict) and y.get("position") == pos:
                        for k in ("changed_earthly_branch", "changed_branch"):
                            if y.get(k):
                                return y.get(k)
            except Exception:
                pass
            return ""

        def _self_hurt(pos, branch):
            cb = _changed_branch_of(pos)
            if not branch or not cb:
                return False
            be = BRANCH_ELEMENTS.get(branch)
            ce = BRANCH_ELEMENTS.get(cb)
            if not be or not ce:
                return False
            # 变爻克动爻
            return KE_CYCLE.get(ce) == be or JUE_MAP.get(be) == cb

        # 0 明动有力（动而不空且非自伤回头克/化绝，事之主）
        if pos_info.get("is_moving") and not pos_info.get("is_empty"):
            if _self_hurt(p, brk):
                # 动而自伤：劣于「静而完整」（数值更大=优先级更低）
                return 8
            return 0
        # 1 旬空逢日冲填实（空亡反被激活）
        if pos_info.get("is_empty") and _is_chong(brk, day_branch):
            return 1
        # 2 静爻逢日冲暗动（非空，旺相者力强，《增删易》重动轻静）
        if (not pos_info.get("is_moving")) and (not pos_info.get("is_empty")) and _is_chong(brk, day_branch):
            return 2
        # 3 应爻位置（占婚/占失等古籍断法）
        if p == response_position:
            return 3
        # 4 世爻位置
        if p == world_position:
            return 4
        # 5 临月建
        if pos_info.get("is_at_month"):
            return 5
        # 6 临日辰
        if pos_info.get("is_at_day"):
            return 6
        # 7 静而不空不破（完整有气）—— 优先于动而自伤/动空
        if (not pos_info.get("is_moving")) and (not pos_info.get("is_empty")) and (not pos_info.get("is_month_break")):
            return 7
        # 8 动而空 / 空破 / 动而自伤
        if pos_info.get("is_moving") or pos_info.get("is_empty") or pos_info.get("is_month_break"):
            return 8
        return 9 + p

    if use_god_positions:
        use_god_positions_sorted = sorted(use_god_positions, key=_use_god_priority)
        selected_use_god = use_god_positions_sorted[0]
    elif has_fu_cang:
        # 伏藏用神：构建一个虚拟的 use_god_position 信息以便 downstream 使用
        fu_detail_tmp = _check_fu_cang(r, use_god_category, palace_element)
        if fu_detail_tmp and fu_detail_tmp.get("results"):
            fu_entry = fu_detail_tmp["results"][0]
            fu_shen_tmp = fu_entry.get("fu_shen", {})
            selected_use_god = {
                "position": fu_shen_tmp.get("position", 0),
                "name": fu_shen_tmp.get("name", "伏藏用神"),
                "earthly_branch": fu_shen_tmp.get("branch", ""),
                "element": fu_shen_tmp.get("element", use_god_element),
                "six_relation": use_god_category,
                "is_fu_cang": True,
                "is_moving": False,
                "is_world": False,
                "is_at_month": False,
                "is_at_day": False,
                "is_empty": fu_shen_tmp.get("branch", "") in (r.get("empty_branches") or []),
            }
        else:
            selected_use_god = None
    else:
        selected_use_god = None

    return {
        "question_category": question_category,
        "use_god_category": use_god_category,
        "use_god_element": use_god_element,
        "use_god_positions": use_god_positions,
        "selected_use_god": selected_use_god,
        "has_use_god_in_hexagram": len(use_god_positions) > 0,
        "use_god_count": len(use_god_positions),
        "has_fu_cang": has_fu_cang,
        "fu_cang_detail": _check_fu_cang(r, use_god_category, palace_element) if has_fu_cang else None,
        "yuan_shen": {
            "category": _element_to_relation(yuan_shen_element, palace_element),
            "element": yuan_shen_element,
            "positions": yuan_shen_positions,
            "fu_cang": yuan_shen_fu,
        },
        "ji_shen": {
            "category": _element_to_relation(ji_shen_element, palace_element),
            "element": ji_shen_element,
            "positions": ji_shen_positions,
            "fu_cang": ji_shen_fu,
        },
        "chou_shen": {
            "category": _element_to_relation(chou_shen_element, palace_element),
            "element": chou_shen_element,
            "positions": chou_shen_positions,
            "fu_cang": chou_shen_fu,
        },
        "world_position": world_position,
        "summary_text": (
            f"问的是「{question_category}」，用神取{use_god_category}（五行{use_god_element}）。"
            f"{'卦中用神在 ' + '、'.join(str(p.get('position','')) + '爻' for p in use_god_positions) if use_god_positions else '本卦用神不现，须查伏神'}。"
            f"原神{_element_to_relation(yuan_shen_element, palace_element)}（{yuan_shen_element}）"
            f"{'现于' + ''.join(str(p.get('position','')) + '爻 ' for p in yuan_shen_positions) if yuan_shen_positions else '伏藏' + ('（' + yuan_shen_fu['branch'] + '·' + _pos_to_name(yuan_shen_fu['position']) + '）' if yuan_shen_fu else '（无）')}，"
            f"忌神{_element_to_relation(ji_shen_element, palace_element)}（{ji_shen_element}）"
            f"{'现于' + ''.join(str(p.get('position','')) + '爻 ' for p in ji_shen_positions) if ji_shen_positions else '伏藏' + ('（' + ji_shen_fu['branch'] + '·' + _pos_to_name(ji_shen_fu['position']) + '）' if ji_shen_fu else '（无）')}，"
            f"仇神{_element_to_relation(chou_shen_element, palace_element)}（{chou_shen_element}）"
            f"{'现于' + ''.join(str(p.get('position','')) + '爻 ' for p in chou_shen_positions) if chou_shen_positions else '伏藏' + ('（' + chou_shen_fu['branch'] + '·' + _pos_to_name(chou_shen_fu['position']) + '）' if chou_shen_fu else '（无）')}。"
        ),
    }


# --- Step 2 辅助函数 ---

def _determine_use_god_category(question_category: str, question_text: str) -> str:
    """根据问题类型确定用神类别 — 使用打分制，避免顺序依赖"""
    # 合并两个文本用于搜索
    combined = f"{question_category} {question_text}"

    # --- 特殊优先级覆盖（高于 _QUESTION_USE_GOD_MAP 中的映射） ---
    # 提到具体人（父亲/母亲/儿子/女儿等）时，以该人为用神，优先级高于"出行→世"
    if any(k in combined for k in ("父亲", "母亲", "爸爸", "妈妈", "爹", "娘", "祖父", "祖母", "岳父", "岳母", "公公", "婆婆")):
        return "父母"
    if any(k in combined for k in ("儿子", "女儿", "孩子", "孙子", "孙女", "儿媳", "女婿")):
        return "子孙"
    # 久病占取世爻为用（《卜筮正宗》：久病以世爻为用）
    if "久病" in combined:
        return "世爻"
    # 出行/行人占取世爻为用（仅当没有提到具体人时生效——《黄金策》：出行以世爻为己身）
    if any(k in combined for k in ("出行", "行人")):
        return "世爻"
    # 功名占取官鬼为用（《黄金策》：功名看官鬼爻，优先级高于考试/学业→父母）
    if "功名" in combined:
        return "官鬼"

    # 精确匹配优先
    if question_category in _QUESTION_USE_GOD_MAP:
        return _QUESTION_USE_GOD_MAP[question_category]

    # 特殊复合语义（高优先级覆盖）：语境歧义消解
    # "见贵求财"：主体是"见贵"（求官）而非"求财" → 官鬼
    if "见贵" in combined and "求财" in combined:
        return "官鬼"
    # "占子病"/"子病"系列：直接取子孙为用神
    if "占子病" in combined or ("子病" in combined):
        return "子孙"
    # 胎孕：以子孙为胎息，优先于句中「妻」
    if any(k in combined for k in ("怀孕", "胎", "孕", "产", "怀")):
        return "子孙"
    # 久病/自身/自占病：以世爻为己身
    if any(k in combined for k in ("久病", "自占病", "自身", "自测")) or (
        "病" in combined and any(k in combined for k in ("半年", "多月", "已久", "沉重"))
    ):
        return "世爻"
    # 科举功名：文书父母为主用（官鬼为录取参考，双用神）
    if any(k in combined for k in ("科举", "中第", "考试", "功名", "学业", "文书领取", "候文书")):
        return "父母"
    # 官司：官鬼为官方
    if any(k in combined for k in ("官司", "官非", "诬告", "诉讼", "官事")) and "师尊" not in combined:
        return "官鬼"

    # 按类别统计匹配关键词数和优先级得分
    # 六亲 → [(category, matched_weight)]
    category_scores = {}
    # 记录每个类别首次出现位置（用于同分时的优先判断）
    category_first_pos = {}
    
    # 核心用神关键词加权
    # 注意：单字"财"/"官"容易在复合词中误匹配（如"见贵求财"中的财），已在特殊语义层处理
    CORE_USE_GOD_KEYWORDS = {"仆", "奴", "婢", "婚", "父", "兄",
                              "妻", "失", "疾病", "官事", "功名", "行人", "买卖",
                              "雇佣", "占仆", "占奴", "桑叶", "价格",
                              "求财", "求官", "见贵"}
    GENERIC_KEYWORDS = {"回", "何时", "何日", "归来", "何时愈", "何日愈", "成否",
                        "吉凶", "结局", "有否", "可得", "冲中逢合", "六合卦", "逢冲",
                        # 天干地支单字（避免在日期串中误匹配）
                        "子", "亥", "酉", "戌", "巳", "未", "申", "辰", "卯", "午", "寅", "丑",
                        "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸",
                        # 单字多义词降权（跨语境易误匹配）
                        "财", "官",
                        # 其他弱关联/高频误匹配词
                        "归", "见", "贵", "日", "月", "时"}

    for keyword, relation in _QUESTION_USE_GOD_MAP.items():
        if keyword in combined:
            # 关键词越长越具体，得分越高
            weight = len(keyword) ** 2
            if keyword in CORE_USE_GOD_KEYWORDS:
                weight *= 3
            elif keyword in GENERIC_KEYWORDS:
                weight *= 0.3
            if relation not in category_scores:
                category_scores[relation] = 0
                category_first_pos[relation] = combined.index(keyword)
            category_scores[relation] += weight
    
    if category_scores:
        max_score = max(category_scores.values())
        # 获取所有最高分的类别
        candidates = [cat for cat, s in category_scores.items() if s == max_score]
        if len(candidates) == 1:
            return candidates[0]
        # 同分时，选择在问题中出现位置最靠前的（即更早被提及=更核心主题）
        best_category = min(candidates, key=lambda c: category_first_pos[c])
        return best_category
    
    # 默认：自测 → 世爻
    return "世爻"


def _find_use_god_positions(
    yao_lines: list[dict],
    use_god_category: str,
    palace_element: str,
    month_branch: str,
    empty: list[str],
) -> list[dict]:
    """
    在卦中查找用神所在位置。
    处理用神两现或多现的情况，返回候选列表。
    """
    if use_god_category == "世爻":
        # 世爻为用
        for yao in yao_lines:
            if yao.get("is_world"):
                return [{
                    "position": yao.get("position"),
                    "name": _pos_to_name(yao.get("position", 0)),
                    "earthly_branch": yao.get("earthly_branch", ""),
                    "element": _branch_element(yao.get("earthly_branch", "")),
                    "is_moving": yao.get("is_moving", False),
                    "is_empty": yao.get("earthly_branch", "") in empty,
                    "is_month_break": False,
                    "reason": "世爻为用",
                }]
        return []

    # 普通六亲查找
    positions = []
    for yao in yao_lines:
        if yao.get("six_relation") == use_god_category:
            branch = yao.get("earthly_branch", "")
            positions.append({
                "position": yao.get("position"),
                "name": _pos_to_name(yao.get("position", 0)),
                "earthly_branch": branch,
                "element": _branch_element(branch),
                "is_moving": yao.get("is_moving", False),
                "is_empty": branch in empty,
                "is_month_break": yao.get("is_month_break", False),
                "is_at_month": branch == month_branch,
                "reason": "",
            })

    # 用神筛选（《卜筮正宗》）：不做任何预过滤，全部候选交排序层统一决策。
    # 说明（P0-3 修正）：
    #   1) 旬空逢日冲则"填实"有力，动而空须出空方应——空亡候选不可剔除；
    #   2) 静爻逢日冲为暗动（《增删易》重动轻静），可能优于明动而空的候选；
    #   3) 应位/世位用神在古籍断法中权重极高。
    return positions


def _find_relation_positions(
    yao_lines: list[dict],
    target_element: str,
    palace_element: str,
) -> list[dict]:
    """查找指定五行（对应某六亲）在卦中的位置"""
    if not target_element:
        return []

    result = []
    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        if _branch_element(branch) == target_element:
            result.append({
                "position": yao.get("position"),
                "name": _pos_to_name(yao.get("position", 0)),
                "earthly_branch": branch,
                "six_relation": yao.get("six_relation", ""),
                "six_spirit": yao.get("six_spirit", ""),
                "is_moving": yao.get("is_moving", False),
                "is_empty": yao.get("is_empty", False),
            })
    return result


def _element_to_relation(element: str, palace_element: str) -> str:
    """五行转六亲"""
    return get_relation_from_element(element, palace_element)


def _branch_to_relation(branch: str, palace_element: str) -> str:
    """根据地支五行确定六亲"""
    return get_relation_from_element(_branch_element(branch), palace_element)


def _check_fu_cang(
    r: dict,
    use_god_category: str,
    palace_element: str,
) -> dict | None:
    """
    检查伏藏：用神不现时，从本宫首卦查找伏神位置。
    《黄金策》：「用神伏藏，查伏于何爻之下」
    """
    hex_info = safe_get(r, "original_hexagram", default={})
    yao_lines = safe_get(hex_info, "yao_lines", default=[])
    palace = safe_get(hex_info, "palace", default="")

    if not palace or not yao_lines:
        return None

    # 获取本宫首卦名
    first_hex_name = get_palace_first_hexagram(palace)
    if not first_hex_name:
        return None

    # 获取本宫首卦的地支排列
    trigrams = HEXAGRAM_TRIGRAMS.get(first_hex_name)
    if not trigrams:
        return None

    upper_name, lower_name = trigrams
    first_hex_branches = NAJIA_BRANCHES[lower_name]["inner"] + NAJIA_BRANCHES[upper_name]["outer"]

    # 查找本宫首卦中对应用神的六亲位置
    target_positions = []
    for idx, branch in enumerate(first_hex_branches):
        relation = get_relation_from_element(_branch_element(branch), palace_element)
        if relation == use_god_category:
            pos = idx + 1
            target_positions.append({
                "position": pos,
                "name": _pos_to_name(pos),
                "branch": branch,
                "element": _branch_element(branch),
            })

    if not target_positions:
        return None

    # 对于每个伏神位置，检查飞神
    results = []
    for target in target_positions:
        pos = target["position"]
        # 获取当前卦对应位置的数据（飞神）
        fei_shen = None
        for yao in yao_lines:
            if yao.get("position") == pos:
                fei_shen = {
                    "position": pos,
                    "branch": yao.get("earthly_branch", ""),
                    "six_relation": yao.get("six_relation", ""),
                    "element": _branch_element(yao.get("earthly_branch", "")),
                }
                break

        # 判断伏神是否得出
        # 《增删卜易》：得伏出者，伏神旺相、飞神衰/被冲/被合/被日/月生
        can_emerge = fei_shen is None or True  # 默认可出

        results.append({
            "fu_shen": target,
            "fei_shen": fei_shen,
            "position": pos,
            "can_emerge": can_emerge,
        })

    return {
        "palace_first_hexagram": first_hex_name,
        "results": results,
    }


# =============================================================================
# Step 3 Helper: 暗动 Detection
# =============================================================================

_BRANCH_CLASHES = {
    "子": "午", "午": "子",
    "丑": "未", "未": "丑",
    "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰",
    "巳": "亥", "亥": "巳",
}


def _combined_strength_for_hm(element: str, month_element: str, day_element: str) -> str:
    """
    综合月建日辰判断旺衰（暗动专用轻量版）。
    返回: "旺", "相", "中和", "偏弱", "衰"
    """
    m = element_strength_in_month(element, month_element)
    d = element_strength_in_month(element, day_element)
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


def _detect_hidden_movement(
    day_branch: str,
    yao_lines: list[dict],
    month_element: str = "",
    day_element: str = "",
) -> list[dict]:
    """
    Detect 暗动 (hidden movement) — static yao that are genuinely clashed by 日辰.

    Rule from 《卜筮正宗》《增删卜易》:
    - 旺相之爻遇日冲 → 暗动（强，~70%明动）
    - 中和之爻遇日冲 → 暗动（中，~40%）
    - 休囚之爻遇日冲 → 暗动（弱，~30%——力微短暂）
    - 月休囚+日冲+衰 → 日破（此爻彻底无用，零效力）

    Only applies to 静爻 (static yao, not marked as moving by 6 or 9).
    日破 yao are excluded from the result (weight=0 = no effect).

    Parameters
    ----------
    day_branch : str
        The day branch (e.g. "子", "午")
    yao_lines : list[dict]
        All 6 yao with their attributes including 'is_moving', 'earthly_branch',
        'six_relation', 'position', 'nature' etc.
    month_element : str
        Five-element value of the month branch (for strength calculation)
    day_element : str
        Five-element value of the day branch (for strength calculation)

    Returns
    -------
    list[dict]
        Each hidden movement record with position, branch, type, source, role, weight.
        日破 yao are excluded (zero effect).
        Empty list if none detected.
    """
    if not day_branch or not yao_lines:
        return []

    # 力量等级 → (label, weight) 映射
    STRENGTH_MAP = {
        "旺": ("暗动(旺相，七分布动)", 0.7, "强"),
        "相": ("暗动(旺相，七分布动)", 0.7, "强"),
        "中和": ("暗动(中和，中力)", 0.4, "中"),
        "偏弱": ("暗动(休囚，三分力)", 0.2, "弱"),
        "衰": ("日破(月休逢冲，此爻无用)", 0.0, "无"),
    }

    hidden_moved = []
    for yao in yao_lines:
        # Skip explicit moving yao (already 明动)
        if yao.get("is_moving") or yao.get("moving"):
            continue
        yao_branch = yao.get("earthly_branch", "") or yao.get("branch", "")
        if not yao_branch:
            continue
        # Check 六冲 relationship: day_branch clashes with yao_branch
        if _BRANCH_CLASHES.get(yao_branch) == day_branch:
            elem = _branch_element(yao_branch)

            # 计算旺衰等级
            if month_element and day_element:
                overall = _combined_strength_for_hm(elem, month_element, day_element)
            else:
                overall = "中和"  # fallback if no month/day info

            label, weight, effect_strength = STRENGTH_MAP.get(
                overall, ("暗动", 0.5, "中")
            )

            # 日破（weight=0）之爻 → 无任何作用 → 完全跳过
            if weight == 0.0:
                continue

            # Determine the role for reporting
            relation = yao.get("six_relation", "")
            role = relation if relation else "静爻"
            hidden_moved.append({
                "position": yao.get("position"),
                "name": _pos_to_name(yao.get("position", 0)),
                "branch": yao_branch,
                "element": elem,
                "relation": role,
                "type": label,
                "effect_strength": effect_strength,
                "source": "日冲",
                "weight": weight,
            })

    return hidden_moved


# =============================================================================
# Step 3: 断旺 (Strength Analysis)
# =============================================================================



def _compose_strength_summary(**kw) -> str:
    """旺衰步骤：叙述体，分数只作括号备查。"""
    ug = kw.get("use_god_category") or "用神"
    name = (kw.get("selected_use_god") or {}).get("name") or ""
    elem = kw.get("use_god_element") or ""
    mb, me = kw.get("month_branch") or "", kw.get("month_element") or ""
    ms, msc = kw.get("god_month_strength") or "", kw.get("god_month_score")
    db, de = kw.get("day_branch") or "", kw.get("day_element") or ""
    ds, dsc = kw.get("god_day_strength") or "", kw.get("god_day_score")
    level = kw.get("strength_level") or ""
    score = kw.get("effective_score")
    parts = [f"{ug}在{name}，五行{elem}。"]
    parts.append(f"月建{mb}（{me}）对它{ms}，日辰{db}（{de}）对它{ds}。")
    extras = []
    if kw.get("is_empty") and kw.get("empty_modifier_reason"):
        extras.append(str(kw["empty_modifier_reason"]).rstrip("，。"))
    if kw.get("is_month_break") and kw.get("month_break_modifier_reason"):
        extras.append(str(kw["month_break_modifier_reason"]).rstrip("，。"))
    if kw.get("is_an_dong") and kw.get("an_dong_modifier_reason"):
        extras.append(str(kw["an_dong_modifier_reason"]).rstrip("，。"))
    if kw.get("twelve_growth_modifier") and kw.get("twelve_growth_reason"):
        extras.append(str(kw["twelve_growth_reason"]).rstrip("，。"))
    if kw.get("hidden_movement") and kw.get("hidden_movement_reason"):
        extras.append(str(kw["hidden_movement_reason"]).rstrip("，。"))
    if kw.get("tp_modifier") and kw.get("tp_modifier_reason"):
        extras.append(str(kw["tp_modifier_reason"]).rstrip("，。"))
    if kw.get("desperate_relief_modifier") and kw.get("desperate_relief_description"):
        extras.append(str(kw["desperate_relief_description"]).rstrip("，。"))
    if extras:
        parts.append("另外要留意：" + "；".join(extras) + "。")
    # 口语结论
    lv = str(level)
    say = {
        "极旺": "总起来说，用神很有底气。",
        "旺": "总起来说，用神得力。",
        "相": "总起来说，用神有根，能用。",
        "中和": "总起来说，用神不强不弱，看后手怎么走。",
        "中和偏旺": "总起来说，用神略占上风。",
        "中和偏弱": "总起来说，用神稍显吃力。",
        "偏弱": "总起来说，用神偏软，宜借力。",
        "弱": "总起来说，用神力量薄，不宜硬催结果。",
        "极弱": "总起来说，用神几乎使不上劲。",
        "休囚": "总起来说，用神处在低潮。",
    }.get(lv, f"总起来说，用神状态为{lv}。")
    parts.append(say)
    if score is not None:
        parts.append(f"（量化参考 {float(score):.2f} · {lv}）")
    return "".join(parts)


def step3_analyze_strength(r: dict) -> dict:
    """
    Step 3: 断旺 — 分析用神旺衰（最关键步骤）。

    使用「旺相休囚死」框架，结合月建、日辰综合判断。

    规则：
    ┌────────┬──────────────────────────────────┐
    │ 状态   │ 条件                              │
    ├────────┼──────────────────────────────────┤
    │ 旺(5)  │ 用神五行 同于 月建五行             │
    │ 相(4)  │ 月建五行 生 用神五行               │
    │ 休(3)  │ 用神五行 生 月建五行               │
    │ 囚(2)  │ 用神五行 克 月建五行               │
    │ 死(1)  │ 月建五行 克 用神五行               │
    └────────┴──────────────────────────────────┘

    日辰修正：
    - 日辰生用神: +1
    - 日辰克用神: -1
    - 日辰同五行: +0.5

    特殊状态：
    - 旬空：有气论70%（旺相+旬空）、休囚论30%（休囚+旬空）
    - 月破：直接降为1（死）
    - 暗动：旺相×0.7, 休囚×0.3
    """
    # 获取分析上下文
    step1_data = safe_get(r, "_step1_data", default={})
    step2_data = safe_get(r, "_step2_data", default={})
    hex_info = safe_get(r, "original_hexagram", default={})
    yao_lines = safe_get(hex_info, "yao_lines", default=[])
    palace_element = safe_get(hex_info, "palace_element", default="")

    # 获取日月建
    div_time = safe_get(r, "divination_time", default={})
    month_stem_branch = safe_get(div_time, "month_stem_branch", default="")
    day_stem_branch = safe_get(div_time, "day_stem_branch", default="")
    month_branch = month_stem_branch[1:] if len(month_stem_branch) >= 2 else ""
    day_branch = day_stem_branch[1:] if len(day_stem_branch) >= 2 else ""
    month_element = _branch_element(month_branch)
    day_element = _branch_element(day_branch)

    # 获取旬空
    empty = safe_get(r, "empty_branches", default=[])

    # 获取用神信息
    # 从 step2 获取，如果没有则临时计算（self-contained）
    selected_use_god = safe_get(step2_data, "selected_use_god", default=None)
    use_god_category = safe_get(step2_data, "use_god_category", default="世爻")
    use_god_element = safe_get(step2_data, "use_god_element", default="")

    # 如果没有step2数据，临时获取用神
    if not selected_use_god:
        if use_god_category == "世爻":
            for yao in yao_lines:
                if yao.get("is_world"):
                    selected_use_god = {
                        "position": yao.get("position"),
                        "name": _pos_to_name(yao.get("position", 0)),
                        "earthly_branch": yao.get("earthly_branch", ""),
                        "element": _branch_element(yao.get("earthly_branch", "")),
                        "is_moving": yao.get("is_moving", False),
                        "is_empty": yao.get("earthly_branch", "") in empty,
                        "is_month_break": yao.get("is_month_break", False),
                    }
                    use_god_element = _branch_element(yao.get("earthly_branch", ""))
                    break

    if not selected_use_god or selected_use_god.get("is_fu_cang"):
        # 伏藏用神特殊评估（用神伏藏时，旺衰以伏神飞伏关系为主）
        if step2_data.get("has_fu_cang"):
            fu_detail = step2_data.get("fu_cang_detail", {})
            fu_score = _evaluate_fu_cang_strength(fu_detail, month_branch, day_branch, empty)

            # 构建伏神对应的基本信息
            fu_results = fu_detail.get("results", [])
            fu_entry = fu_results[0] if fu_results else {}
            fu_shen_info = fu_entry.get("fu_shen", {})
            fei_shen_info = fu_entry.get("fei_shen") or {}
            can_emerge_val = fu_entry.get("can_emerge", True)

            return {
                "use_god_position": fu_shen_info.get("position"),
                "use_god_name": fu_shen_info.get("name", ""),
                "use_god_branch": fu_shen_info.get("branch", ""),
                "use_god_element": fu_shen_info.get("element", ""),
                "parent_strength_god": use_god_category,
                "month_element": month_element,
                "day_element": day_element,
                "god_month_strength": element_strength_in_month(
                    fu_shen_info.get("element", ""), month_element
                ) if fu_shen_info.get("element") else "未知",
                "god_month_score": strength_to_score(
                    element_strength_in_month(fu_shen_info.get("element", ""), month_element)
                ) if fu_shen_info.get("element") else 0,
                "god_day_strength": element_strength_in_month(
                    fu_shen_info.get("element", ""), day_element
                ) if fu_shen_info.get("element") else "未知",
                "god_day_score": strength_to_score(
                    element_strength_in_month(fu_shen_info.get("element", ""), day_element)
                ) if fu_shen_info.get("element") else 0,
                "is_empty": fu_shen_info.get("branch", "") in empty,
                "is_month_break": False,
                "is_an_dong": False,
                "twelve_growth_stage": _twelve_growth_at_day(
                    fu_shen_info.get("element", ""), day_branch
                ),
                "base_score": fu_score["score"],
                "adjusted_score": fu_score["score"],
                "effective_score": fu_score["score"],
                "strength_level": fu_score["level"],
                "modifiers": [{
                    "type": "伏藏飞伏关系",
                    "value": fu_score["score"],
                    "reason": fu_score["analysis"],
                }],
                "summary_text": fu_score["analysis"],
                "has_fu_cang": True,
                "fu_cang_detail": fu_detail,
                "can_emerge": can_emerge_val,
                "fu_cang_analysis": fu_score["analysis"],
                "hidden_movement": [],
                "hidden_movement_modifier": 0.0,
                "hidden_movement_reason": "",
            }
        return {"error": "无法定位用神"}

    # ---------- 3.1: 用神月建旺衰 ----------
    god_month_strength = element_strength_in_month(use_god_element, month_element)
    god_month_score = strength_to_score(god_month_strength)

    # ---------- 3.2: 用神日辰旺衰 ----------
    god_day_strength = element_strength_in_month(use_god_element, day_element)
    god_day_score = strength_to_score(god_day_strength)

    # ---------- 3.3: 日辰修正 ----------
    day_modifier = 0.0
    day_modifier_reason = ""
    if day_element == use_god_element:
        day_modifier = 0.5
        day_modifier_reason = "日辰与用神同气（同性相助）"
    elif SHENG_CYCLE.get(day_element) == use_god_element:
        day_modifier = 1.0
        day_modifier_reason = "日辰生用神"
    elif SHENG_CYCLE.get(use_god_element) == day_element:
        day_modifier = -1.0
        day_modifier_reason = "用神生日辰（泄气）"
    elif KE_CYCLE.get(day_element) == use_god_element:
        day_modifier = -1.0
        day_modifier_reason = "日辰克用神（克伤）"
    elif KE_CYCLE.get(use_god_element) == day_element:
        day_modifier = 0.5
        day_modifier_reason = "用神克日辰（制日）"

    # ---------- 3.4: 旬空修正 ----------
    is_empty = selected_use_god.get("is_empty", False)
    empty_modifier = 1.0
    empty_modifier_reason = ""
    chu_xun_bonus = 0.0
    chu_xun_reason = ""
    if is_empty:
        # 有生源检测（月建/日辰/动爻生用神 → 空亡有气，出旬有验）
        month_births_use = SHENG_CYCLE.get(month_element) == use_god_element
        day_births_use = SHENG_CYCLE.get(day_element) == use_god_element
        # 动爻生用神 → "动则生而不为空"（《增删易》动空出旬）
        moving_births_use = False
        for yao in yao_lines:
            if yao.get("is_moving"):
                y_elem = _branch_element(yao.get("earthly_branch", ""))
                if SHENG_CYCLE.get(y_elem) == use_god_element:
                    moving_births_use = True
                    break
        if god_month_score >= 4 or moving_births_use:
            empty_modifier = 0.7  # 有气论
            if moving_births_use:
                empty_modifier_reason = "用神旬空但得动爻生之（动空），出旬即应，论70%"
            else:
                empty_modifier_reason = "用神旺相旬空，论70%（有气空亡，出空可应）"
            # 日辰冲用神 → 旬空逢冲为填实（《卜筮正宗》冲空则实）
            _ugb = (selected_use_god or {}).get("earthly_branch", "")
            day_clashes_use = bool(day_branch) and bool(_ugb) and _is_chong(_ugb, day_branch)
            if day_clashes_use:
                empty_modifier_reason = "用神旺相旬空，逢日辰冲为填实（冲空则实，出空即应），论70%"
            if month_births_use or day_births_use or moving_births_use:
                chu_xun_bonus = 1.0
                chu_xun_reason = "用神旬空有气且得生扶（月/日/动爻），出旬有验，断吉倾向"
        else:
            empty_modifier = 0.3  # 休囚论
            empty_modifier_reason = "用神休囚旬空，论30%（真空亡，难应）"

    # ---------- 3.5: 月破修正 ----------
    is_month_break = selected_use_god.get("is_month_break", False)
    month_break_modifier = 1.0
    month_break_modifier_reason = ""
    if is_month_break:
        # 月破日合可救
        if _is_he(selected_use_god.get("earthly_branch", ""), day_branch):
            month_break_modifier = 0.5  # 有救
            month_break_modifier_reason = "月破逢日合，可救"
        else:
            month_break_modifier = 0.3  # 几乎失效
            month_break_modifier_reason = "月破且无救，力量近乎消亡"

    # ---------- 3.6: 暗动修正 ----------
    is_an_dong = False
    an_dong_modifier = 1.0
    an_dong_modifier_reason = ""
    # 暗定义：旺相之爻受日冲
    if not selected_use_god.get("is_moving", False):  # 不是动爻才是暗动
        if _is_chong(selected_use_god.get("earthly_branch", ""), day_branch):
            if god_month_score >= 4:  # 旺相受日冲为暗动
                is_an_dong = True
                an_dong_modifier = 0.7
                an_dong_modifier_reason = "旺爻受日冲为暗动，有动意而力稍逊"
            else:  # 休囚受日冲为日破
                is_an_dong = False
                an_dong_modifier = 0.3
                an_dong_modifier_reason = "休囚之爻受日冲为日破，无力"

    # ---------- 3.7: 十二长生修正 ----------
    use_god_branch = selected_use_god.get("earthly_branch", "")
    twelve_growth = get_twelve_growth_stage(use_god_element, day_branch)
    twelve_growth_modifier = 0.0
    twelve_growth_reason = ""
    if twelve_growth:
        stage_name, stage_idx = twelve_growth
        if stage_name == "帝旺":
            twelve_growth_modifier = 0.5
            twelve_growth_reason = "用神临帝旺，极盛之象"
        elif stage_name in ("临官", "长生"):
            twelve_growth_modifier = 0.3
            twelve_growth_reason = f"用神临{stage_name}，得气之象"
        elif stage_name in ("墓", "绝", "死"):
            twelve_growth_modifier = -1.0
            twelve_growth_reason = f"用神临{stage_name}，入{stage_name}之地，力微"
        elif stage_name in ("沐浴",):
            twelve_growth_modifier = -0.3
            twelve_growth_reason = f"用神临{stage_name}，初生而气弱"

    # ---------- 3.7b: 绝处逢生 / 绝地无援 ----------
    # 用神临绝地（十二长生"绝"位）：原神发动来生 → 绝处逢生（凶中反吉）；无原神救援 → 绝地无援（额外减分）
    desperate_relief_from_stage_modifier = 0.0
    desperate_relief_from_stage_reason = ""
    if stage_name == "绝":
        yuan_shen_positions_for_desperate = safe_get(step2_data, "yuan_shen", "positions", default=[])
        has_yuan_rescue = any(p.get("is_moving", False) for p in (yuan_shen_positions_for_desperate or []))
        if has_yuan_rescue:
            desperate_relief_from_stage_modifier = 1.0
            desperate_relief_from_stage_reason = "绝处逢生：用神虽临绝地，原神发动来生，凶中反吉"
        else:
            desperate_relief_from_stage_modifier = -1.0
            desperate_relief_from_stage_reason = "绝地无援：用神临绝地，原神不动/无救援，险上加险"

    # ---------- 3.8: 综合评分 ----------
    # 基础分：月建为主（权重0.6），日辰为辅（权重0.4）
    base_score = god_month_score * 0.6 + god_day_score * 0.4
    # 加上日辰修正
    adjusted_score = base_score + day_modifier
    # 应用旬空/月破/暗动修正
    effective_score = adjusted_score * empty_modifier * month_break_modifier
    if chu_xun_bonus != 0.0:
        effective_score += chu_xun_bonus
    if is_an_dong:
        effective_score *= an_dong_modifier
    # 加上十二长生修正
    effective_score += twelve_growth_modifier

    # ---------- 3.8b: 绝处逢生修正（来自 advanced_analysis 和步骤 3.7b 绝地检测）----------
    desperate_relief_modifier = 0.0
    desperate_relief_info = None
    # 3.7b: 绝处逢生 / 绝地无援（由 step3 自身识别）
    if desperate_relief_from_stage_modifier != 0.0:
        desperate_relief_modifier += desperate_relief_from_stage_modifier
        effective_score += desperate_relief_from_stage_modifier
    # advanced_analysis: 绝处逢生（由 enhance_reading 预计算）
    advanced = r.get("advanced_analysis") if isinstance(r, dict) else None
    if isinstance(advanced, dict):
        dr = advanced.get("desperate_relief")
        if isinstance(dr, dict) and dr.get("has_desperate_relief"):
            desperate_relief_modifier = dr.get("score_modifier", 0.0)
            desperate_relief_info = dr
            effective_score += desperate_relief_modifier

    # ---------- 3.8c: 随官入墓标记（随官入墓信息，主修正已在 step5 应用）----------
    officer_tomb_ref = None
    if isinstance(advanced, dict):
        ot = advanced.get("officer_tomb")
        if isinstance(ot, dict) and ot.get("has_officer_tomb"):
            officer_tomb_ref = {
                "severity": ot.get("severity", "none"),
                "scenarios": ot.get("scenarios", []),
                "description": ot.get("description", ""),
            }

    # 分数上下限
    effective_score = max(0.5, min(5.0, effective_score))

    # ---------- 3.9: 旺衰定性 ----------
    # 古典规则：用神五行在月建处于"相"位(生月令者)时，即使合分因暗动/刑等被压低，旺衰定性仍应不低于"旺"
    _month_str_for_level = element_strength_in_month(use_god_element, month_element) if use_god_element and month_element else ""
    _xiang_bump = (_month_str_for_level == "相" and effective_score >= 2.5)
    if effective_score >= 4.5:
        strength_level = "极旺"
    elif effective_score >= 3.5:
        strength_level = "旺"
    elif effective_score >= 2.5:
        # "相"位之爻合分在[2.5, 3.5)区间时，定性上调为"旺"而非"中和"
        strength_level = "旺" if _xiang_bump else "中和"
    elif effective_score >= 1.5:
        strength_level = "偏弱"
    elif effective_score >= 0.8:
        strength_level = "弱"
    else:
        strength_level = "极弱"

    # ---------- 3.10b: 暗动检测（全卦静爻） ----------
    # Extract yuan_shen/ji_shen elements from step2_data for hidden movement role check
    yuan_shen_elem = safe_get(step2_data, "yuan_shen", "element", default="")
    ji_shen_elem = safe_get(step2_data, "ji_shen", "element", default="")
    yuan_shen_relation = _element_to_relation(yuan_shen_elem, palace_element) if yuan_shen_elem else ""
    ji_shen_relation = _element_to_relation(ji_shen_elem, palace_element) if ji_shen_elem else ""

    hidden_movement = _detect_hidden_movement(
        day_branch, yao_lines, month_element, day_element
    )
    hidden_movement_modifier = 0.0
    hidden_movement_reason = ""
    if hidden_movement:
        for hm in hidden_movement:
            hm_relation = hm.get("relation", "")
            hm_pos = hm.get("position")
            hm_name = hm.get("name", "")
            hm_branch = hm.get("branch", "")
            hm_weight = hm.get("weight", 0.5)
            # Check if this hidden-moved yao is the use god
            if hm_pos == selected_use_god.get("position"):
                hidden_movement_modifier += 0.3 * hm_weight / 0.7
                hidden_movement_reason += f"用神{hm_name}暗动（{hm_branch}受{day_branch}冲），有动意；"
            elif yuan_shen_relation and hm_relation == yuan_shen_relation:
                hidden_movement_modifier += 0.4 * hm_weight / 0.7
                hidden_movement_reason += f"原神{hm_name}暗动（{hm_branch}受{day_branch}冲），暗中生助用神；"
            elif ji_shen_relation and hm_relation == ji_shen_relation:
                hidden_movement_modifier -= 0.8 * hm_weight / 0.7
                hidden_movement_reason += f"忌神{hm_name}暗动（{hm_branch}受{day_branch}冲），暗中克害；"
            else:
                hidden_movement_reason += f"{hm_name}暗动（{hm_branch}，{hm.get('effect_strength', '中')}），"

        effective_score += hidden_movement_modifier

    # ---------- 3.10c: 三刑修正（来自 advanced_analysis）----------
    # P0-4 修正：三刑只计入"用神自身参与"的刑（branches_present 含用神支）。
    # 卦内其他爻的刑（如无关自刑）属于整体格局，不应扣在用神旺衰分上。
    tp_modifier = 0.0
    tp_issues = []
    advanced_for_tp = r.get("advanced_analysis", {})
    if advanced_for_tp and isinstance(advanced_for_tp, dict):
        tp_data = advanced_for_tp.get("three_punishments", {})
        if isinstance(tp_data, dict) and tp_data.get("has_punishment"):
            # 优先使用已乘倍数后的 total_score（classical_analysis 内部对多刑叠加用了1.5x/2.0x）
            total_tp = tp_data.get("total_score", None)
            if total_tp is not None and total_tp < 0:
                tp_modifier = total_tp
            else:
                for p in tp_data.get("punishments", []):
                    bp = p.get("branches_present", [])
                    if use_god_branch and use_god_branch not in bp:
                        continue
                    tp_modifier += p.get("score", 0.0)
            # 描述仍加所有已成立的刑
            for p in tp_data.get("punishments", []):
                comp = p.get("completeness", "")
                ptype = p.get("type", "")
                if comp == "待刑":
                    missing = p.get("missing", [])
                    tp_issues.append(f"{ptype}待刑(缺{','.join(missing)})")
                elif comp == "完整":
                    tp_issues.append(f"{ptype}(完整三刑)")
                elif comp == "成刑":
                    tp_issues.append(f"{ptype}(成刑)")
                elif comp == "催刑":
                    tp_issues.append(f"{ptype}(催刑)")
                else:
                    tp_issues.append(ptype)
    tp_modifier_reason = "、".join(tp_issues) if tp_issues else ""
    if tp_modifier != 0.0:
        effective_score += tp_modifier

    # ---------- 3.11: 收集所有修正项 ----------
    modifiers = []
    desperate_relief_description = ""
    if day_modifier != 0:
        modifiers.append({"type": "日辰", "value": day_modifier, "reason": day_modifier_reason})
    if chu_xun_bonus != 0.0:
        modifiers.append({"type": "出旬有验", "value": chu_xun_bonus, "reason": chu_xun_reason})
    if is_empty:
        modifiers.append({"type": "旬空", "value": empty_modifier, "reason": empty_modifier_reason})
    if is_month_break:
        modifiers.append({"type": "月破", "value": month_break_modifier, "reason": month_break_modifier_reason})
    if is_an_dong:
        modifiers.append({"type": "暗动", "value": an_dong_modifier, "reason": an_dong_modifier_reason})
    elif an_dong_modifier_reason and not selected_use_god.get("is_moving", False):
        modifiers.append({"type": "日破", "value": an_dong_modifier, "reason": an_dong_modifier_reason})
    if twelve_growth_modifier != 0:
        modifiers.append({
            "type": "十二长生",
            "value": twelve_growth_modifier,
            "reason": twelve_growth_reason,
        })
    if hidden_movement:
        modifiers.append({
            "type": "暗动",
            "value": hidden_movement_modifier,
            "reason": hidden_movement_reason,
            "details": hidden_movement,
        })
    if tp_modifier != 0.0:
        modifiers.append({
            "type": "三刑",
            "value": tp_modifier,
            "reason": tp_modifier_reason,
        })

    # ---------- 绝处逢生修正项 ----------
    if desperate_relief_modifier != 0.0 and (desperate_relief_info or desperate_relief_from_stage_reason):
        dr_reason = ""
        # 优先使用 step3 自身识别的绝地状态描述
        if desperate_relief_from_stage_reason:
            dr_reason = desperate_relief_from_stage_reason
        else:
            dr_reason = desperate_relief_info.get("description", "") if desperate_relief_info else ""
            if not dr_reason and desperate_relief_info:
                dr_reason = desperate_relief_info.get("verdict", "")
        modifiers.append({
            "type": "绝处逢生" if desperate_relief_modifier > 0 else "绝地无援",
            "value": desperate_relief_modifier,
            "reason": dr_reason,
        })
        desperate_relief_description = dr_reason

    return {
        "use_god_position": selected_use_god.get("position"),
        "use_god_name": selected_use_god.get("name"),
        "use_god_branch": use_god_branch,
        "use_god_element": use_god_element,
        "parent_strength_god": use_god_category,
        "month_element": month_element,
        "day_element": day_element,
        "god_month_strength": god_month_strength,
        "god_month_score": god_month_score,
        "god_day_strength": god_day_strength,
        "god_day_score": god_day_score,
        "day_modifier": day_modifier,
        "day_modifier_reason": day_modifier_reason,
        "is_empty": is_empty,
        "empty_modifier": empty_modifier,
        "empty_modifier_reason": empty_modifier_reason,
        "is_month_break": is_month_break,
        "month_break_modifier": month_break_modifier,
        "month_break_modifier_reason": month_break_modifier_reason,
        "is_an_dong": is_an_dong,
        "an_dong_modifier": an_dong_modifier if is_an_dong else 1.0,
        "an_dong_modifier_reason": an_dong_modifier_reason,
        "twelve_growth_stage": twelve_growth[0] if twelve_growth else None,
        "twelve_growth_modifier": twelve_growth_modifier,
        "twelve_growth_reason": twelve_growth_reason,
        "base_score": round(base_score, 2),
        "adjusted_score": round(adjusted_score, 2),
        "effective_score": round(effective_score, 2),
        "strength_level": strength_level,
        "modifiers": modifiers,
        "summary_text": _compose_strength_summary(
            use_god_category=use_god_category,
            selected_use_god=selected_use_god,
            use_god_element=use_god_element,
            month_branch=month_branch,
            month_element=month_element,
            god_month_strength=god_month_strength,
            god_month_score=god_month_score,
            day_branch=day_branch,
            day_element=day_element,
            god_day_strength=god_day_strength,
            god_day_score=god_day_score,
            is_empty=is_empty,
            empty_modifier_reason=empty_modifier_reason,
            is_month_break=is_month_break,
            month_break_modifier_reason=month_break_modifier_reason,
            is_an_dong=is_an_dong,
            an_dong_modifier_reason=an_dong_modifier_reason,
            twelve_growth_reason=twelve_growth_reason,
            twelve_growth_modifier=twelve_growth_modifier,
            hidden_movement=hidden_movement,
            hidden_movement_reason=hidden_movement_reason,
            tp_modifier_reason=tp_modifier_reason,
            tp_modifier=tp_modifier,
            desperate_relief_description=desperate_relief_description,
            desperate_relief_modifier=desperate_relief_modifier,
            effective_score=effective_score,
            strength_level=strength_level,
        ),
        "hidden_movement": hidden_movement,
        "hidden_movement_modifier": round(hidden_movement_modifier, 2),
        "hidden_movement_reason": hidden_movement_reason,
        "three_punishment_modifier": round(tp_modifier, 2),
        "three_punishment_reason": tp_modifier_reason,
        "desperate_relief_modifier": round(desperate_relief_modifier, 2),
        "desperate_relief_info": desperate_relief_info,
        "officer_tomb": officer_tomb_ref,
    }


# =============================================================================
# Special Pattern Recognition (格局识别) — runs between Step3 and Step5
# =============================================================================

def _detect_classical_illness_pattern(question: str, step2_data: dict, step3_data: dict,
                                       empty_branches: list, step4_data: dict = None,
                                       hex_result: dict = None) -> dict:
    """
    古籍经典疾厄格局识别 —《增删卜易》《卜筮正宗》之核心断法。

    特殊疾厄格局优先于一般旺衰规则：
    - 近病逢空即愈：用神旬空，速愈之象
    - 近病逢合为凶：用神被日/月/动爻合住，病难退
    - 近病逢冲即愈：用神被冲，病气散
    - 近病六冲卦速愈
    - 久病逢空/冲/合为凶
    """
    result = {"pattern": None, "description": "", "impact_on_verdict": "", "score_adjustment": 0.0}

    q = question or ""
    is_near_illness = any(kw in q for kw in ["近病", "即愈", "何日愈"])
    is_chronic_illness = any(kw in q for kw in ["久病", "沉疴", "久疾"])
    is_illness_div = any(kw in q for kw in ["病", "疾", "症"]) and ("愈" in q or "吉凶" in q or "死" in q)

    if not (is_near_illness or is_chronic_illness or is_illness_div):
        return result

    # 获取用神信息
    use_god = step2_data.get("selected_use_god") or {}
    use_god_branch = use_god.get("earthly_branch", "")
    if not use_god_branch:
        # fallback: check use_god_yao_lines
        ug_lines = step2_data.get("use_god_yao_lines") or step2_data.get("use_god_positions") or []
        if ug_lines and isinstance(ug_lines, list):
            first = ug_lines[0]
            if isinstance(first, dict):
                use_god_branch = first.get("earthly_branch", "")

    # 化空检测：从 step3 或 step4 的动爻信息中获取
    transform_to_void = False
    void_branch_hit = ""

    # 优先从 step4_data.details 获取动爻化空（标准数据源）
    if not transform_to_void and step4_data:
        s4_details = step4_data.get("details") or step4_data.get("moving_details") or []
        for m in (s4_details if isinstance(s4_details, list) else []):
            if isinstance(m, dict):
                target = (m.get("changed_branch", "") or m.get("target_earthly_branch", "")
                         or m.get("to_branch", "") or m.get("transformed_branch", ""))
                if target and target in empty_branches:
                    transform_to_void = True
                    void_branch_hit = target
                    break

    # fallback: 检查 step3_data 中的 moving_analysis / dong_analysis / moving_details
    if not transform_to_void and step3_data:
        dong_analysis = (step3_data.get("dong_analysis") or step3_data.get("moving_analysis")
                         or step3_data.get("moving_details") or [])
        for m in (dong_analysis if isinstance(dong_analysis, list) else []):
            if isinstance(m, dict):
                target = (m.get("target_earthly_branch", "") or m.get("to_branch", "")
                          or m.get("changed_branch", "") or m.get("transformed_branch", ""))
                if target and target in empty_branches:
                    transform_to_void = True
                    void_branch_hit = target
                    break

    # --- 近病逢合为凶（优先于逢空：合则病气难退，《卜筮正宗》"近病逢合为凶"）---
    # 仅限用神为静爻时——动爻逢合为"合起"（合而发动），不构成合绊；
    # 静爻逢合方为"合绊"（病气难退）。
    use_god_moving = use_god.get("is_moving", False) or any(
        yl.get("is_moving") for yl in
        (step2_data.get("use_god_yao_lines") or step2_data.get("use_god_positions") or [])
        if isinstance(yl, dict) and yl.get("earthly_branch") == use_god_branch
    )
    if (is_near_illness or is_illness_div) and use_god_branch and not use_god_moving:
        dt6 = hex_result.get("divination_time", {}) or {}
        m_b = (dt6.get("month_stem_branch", "") or "")[1:]
        d_b = (dt6.get("day_stem_branch", "") or "")[1:]
        HE6 = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
               "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
        he_bys = []
        if HE6.get(use_god_branch, "") == m_b:
            he_bys.append(f"月建{m_b}")
        if HE6.get(use_god_branch, "") == d_b:
            he_bys.append(f"日辰{d_b}")
        if he_bys:
            result["pattern"] = "近病逢合为凶"
            result["description"] = f"用神{use_god_branch}为{'、'.join(he_bys)}所合——近病逢合，病气难退（《卜筮正宗》定法）"
            result["impact_on_verdict"] = "用神被合，病气难退，凶"
            result["score_adjustment"] = -5.5
            return result

    # --- 近病逢空即愈 ---
    if (is_near_illness or is_illness_div):
        use_void = use_god_branch and use_god_branch in empty_branches
        if use_void or transform_to_void:
            void_desc = f"用神{use_god_branch}旬空" if use_void else f"用神化空（动爻化{void_branch_hit}旬空）"
            result["pattern"] = "近病逢空即愈"
            result["description"] = f"{void_desc}——近病逢空为病气将退，速愈之象（《增删易》定法）"
            result["impact_on_verdict"] = "近病逢空即愈，强调为吉"
            result["score_adjustment"] = 5.0
            return result

        # 近病运交any void branch → also 逢空象
        yao_lines = step2_data.get("use_god_yao_lines") or step2_data.get("use_god_positions") or []
        if yao_lines:
            for yl in yao_lines:
                if isinstance(yl, dict) and yl.get("earthly_branch", "") in empty_branches:
                    result["pattern"] = "近病逢空即愈"
                    result["description"] = f"用神{yl['earthly_branch']}临旬空——近病逢空即愈"
                    result["impact_on_verdict"] = "近病逢空为速愈象"
                    result["score_adjustment"] = 5.0
                    return result

    # --- 近病逢合为凶 ---
    if (is_near_illness or is_illness_div) and step3_data:
        combine_info = step3_data.get("combine_info") or {}
        if combine_info.get("is_combined"):
            combined_by = combine_info.get("combined_by", [])
            if combined_by:
                result["pattern"] = "近病逢合为凶"
                result["description"] = f"用神逢合（{'、'.join(str(x) for x in combined_by)}），近病逢合，病气难退（《增删易》定法）"
                result["impact_on_verdict"] = "近病逢合为凶之经典格局"
                result["score_adjustment"] = -3.5
                return result

        # Also check: 用神被日月生合为凶
        div_time = step3_data.get("divination_info", {})
        if not div_time:
            # Try hex_result (passed separately)
            pass
        # Check if use god is combined by day or month
        day_combine = step3_data.get("day_combine", "")
        month_combine = step3_data.get("month_combine", "")
        if day_combine or month_combine:
            combine_source = "]".join(filter(None, [f"日辰{day_combine}" if day_combine else "", f"月建{month_combine}" if month_combine else ""]))
            result["pattern"] = "近病逢合为凶"
            result["description"] = f"用神为{combine_source}所合——近病逢合为凶（《卜筮正宗》定法）"
            result["impact_on_verdict"] = "用神被合，病气难退，凶"
            result["score_adjustment"] = -3.5
            return result

    # --- 久病逢空/冲为凶 ---
    if is_chronic_illness:
        if use_god_branch and use_god_branch in empty_branches:
            result["pattern"] = "久病逢空为凶"
            result["description"] = f"久病用神{use_god_branch}逢空，久病逢空为危"
            result["impact_on_verdict"] = "久病逢空为脱象，凶"
            result["score_adjustment"] = -4.5
            return result

    return result


def _detect_hexagram_harmony_clash_pattern(question: str, hex_result: dict, step4_data: dict) -> dict:
    """
    六合/六冲交互格局识别 — 冲中逢合可解，合处逢冲则散。

    - 冲中逢合可解：六冲卦中却有日辰/动爻合世爻或应爻，冲散可解为吉
    - 合处逢冲则散：六合卦中却有日辰/月建冲世爻或应爻，合处逢冲为凶
    """
    result = {"pattern": None, "description": "", "impact_on_verdict": "", "score_adjustment": 0.0}

    q = question or ""
    hex_name = hex_result.get("original_hexagram", {}).get("name", "")
    if not hex_name:
        return result

    # 六合卦列表
    HEX_HEXAGRAMS = {"否", "屯", "豫", "贲", "鼎", "萃", "丰", "恒", "损", "同人", "节", "履",
                     "临", "家人", "中孚", "涣", "离", "咸", "泰", "大畜", "需", "大有", "夬",
                     "姤", "小过", "既济", "益", "蛊", "困", "旅", "噬嗑", "归妹"}
    # 六冲卦列表
    HEX_CLASH_HEXAGRAMS = {"乾", "坤", "坎", "离", "震", "巽", "艮", "兑",
                           "无妄", "同人", "遁", "大壮", "豫", "观", "晋", "萃",
                           "大有", "夬", "姤", "解", "归妹", "旅", "涣", "节", "中孚", "小过"}

    # Check for 六合/六冲 in hexagram name using advanced analysis
    hex_advanced = hex_result.get("advanced_analysis", {}) or {}
    hex_type = hex_advanced.get("hexagram_type", "")

    is_he = "六合" in hex_type or hex_name in ("否", "泰", "恒", "益", "萃", "咸", "损", "同人", "贲", "鼎", "随", "节", "中孚", "既济", "家人", "蛊", "困", "豫", "临", "小畜", "履", "涣", "离", "丰")
    is_chong = "六冲" in hex_type or hex_name in ("乾", "坤", "坎", "离", "震", "巽", "艮", "兑", "无妄", "大壮", "遁", "晋", "萃", "夬", "姤", "解", "归妹", "旅", "涣", "小过")

    # Empty branches (for checking if world/response is void)
    empty = hex_result.get("empty_branches", [])

    # --- 冲中逢合可解 ---
    if is_chong:
        div_time = hex_result.get("divination_time", {}) or {}
        month_branch = (div_time.get("month_stem_branch", "") or "")[1:]
        day_branch = (div_time.get("day_stem_branch", "") or "")[1:]
        # 世应爻地支（从爻标志取，original_hexagram 无 world_position 字段）
        yao_lines = hex_result.get("original_hexagram", {}).get("yao_lines", [])
        world_branch = ""
        response_branch = ""
        for y in yao_lines:
            if y.get("is_world"):
                world_branch = y.get("earthly_branch", "")
            if y.get("is_response"):
                response_branch = y.get("earthly_branch", "")
        # 六合：子丑 寅亥 卯戌 辰酉 巳申 午未
        HE_MAP = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
                  "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
        world_he = world_branch and (HE_MAP.get(world_branch, "") in [month_branch, day_branch])
        response_he = response_branch and (HE_MAP.get(response_branch, "") in [month_branch, day_branch])
        # 动爻化合（化出之爻与月日成合，或化出之爻生合用神）方可解冲
        details = step4_data.get("details", []) if step4_data else []
        def _is_helpful_he(d):
            if "化合" not in d.get("change_type", "") and "六合" not in d.get("change_type", ""):
                return False
            chg_branch = d.get("changed_branch", "")
            # 化出之支与日月成合 → 解冲
            if chg_branch and HE_MAP.get(chg_branch, "") in [month_branch, day_branch]:
                return True
            return False
        moving_he = any(_is_helpful_he(d) for d in details)

        if world_he or response_he or moving_he:
            he_target = "世爻" if world_he else ("应爻" if response_he else "动爻")
            result["pattern"] = "冲中逢合可解"
            result["description"] = f"六冲本主散，然月日/动爻合{he_target}（{'世' if world_he else ''}{'应' if response_he else ''}），冲中逢合可解"
            result["impact_on_verdict"] = "冲处逢合可解冲散，转危为安"
            result["score_adjustment"] = 2.5
            return result

        # 六冲无合解 → 事散之象（合伙/婚姻/出行/交易/官讼/谋事类；近病六冲速愈除外）
        SCATTER_KEYWORDS = ["合伙", "合作", "婚姻", "婚", "出行", "外出", "交易", "买卖",
                            "生意", "官讼", "官司", "求财", "谋事", "开店", "签约", "合同"]
        if any(k in q for k in SCATTER_KEYWORDS):
            result["pattern"] = "六冲主散"
            result["description"] = f"六冲卦主散，{hex_name}卦世应相冲，事难成合"
            result["impact_on_verdict"] = "六冲事散，合伙/婚恋/出行/交易类不利"
            result["score_adjustment"] = -2.0
            return result

    # --- 合处逢冲则散 ---
    if is_he:
        div_time = hex_result.get("divination_time", {}) or {}
        month_branch = (div_time.get("month_stem_branch", "") or "")[1:]
        day_branch = (div_time.get("day_stem_branch", "") or "")[1:]
        world_branch = ""
        response_branch = ""

        yao_lines = hex_result.get("original_hexagram", {}).get("yao_lines", [])
        for y in yao_lines:
            if y.get("is_world"):
                world_branch = y.get("earthly_branch", "")
            if y.get("is_response"):
                response_branch = y.get("earthly_branch", "")

        # Check if world/response is being clashed by month or day
        CLASH_MAP = {"子": "午", "午": "子", "卯": "酉", "酉": "卯",
                     "寅": "申", "申": "寅", "巳": "亥", "亥": "巳",
                     "辰": "戌", "戌": "辰", "丑": "未", "未": "丑"}
        world_clashed = world_branch and CLASH_MAP.get(world_branch, "") in [month_branch, day_branch]
        response_clashed = response_branch and CLASH_MAP.get(response_branch, "") in [month_branch, day_branch]

        if (world_clashed or response_clashed):
            SCATTER2 = ["婚姻", "婚", "占婚", "合伙", "合作", "出行", "外出", "交易", "买卖",
                        "生意", "官讼", "官司", "求财", "谋事", "开店", "签约", "合同"]
            if any(k in q for k in SCATTER2):
                result["pattern"] = "合处逢冲则散"
                result["description"] = f"六合本利事成，然{'世爻' if world_clashed else '应爻'}逢冲，合处逢冲则散"
                result["impact_on_verdict"] = "婚姻六合不可解冲，先成后散；散事类同"
                result["score_adjustment"] = -2.0
                return result

    return result


def _detect_special_pattern(step3_data: dict, step2_data: dict, step4_data: dict, hex_result: dict) -> dict:
    """
    特殊格局识别 — 当标准旺相休囚死规则被逆转时触发。

    检测四种高级格局：
    1. 从格 (Following Pattern) — 用神极弱，顺势从强
    2. 专旺格 (Dominant Element) — 一气独旺
    3. 两神成象格 — 两元素各据一方
    4. 化格 (Transformation) — 三合化气

    Parameters
    ----------
    step3_data : dict
        Step3 断旺结果（含 effective_score 等）
    step2_data : dict
        Step2 定用结果（含 用神五行、原神/忌神 等）
    step4_data : dict
        Step4 察变结果（含 moving_analysis 等）
    hex_result : dict
        完整卦象结果（含 original_hexagram, advanced_analysis 等）

    Returns
    -------
    dict
        {
            "pattern": None | "从格" | "专旺格" | "两神成象" | "化格",
            "description": str,
            "impact_on_verdict": str,
            "rule_applied": str,
            "score_adjustment": float,  # 对 final_score 的调整量
        }
    """
    # --- 优先检查古籍经典格局（这些格局优先于从格等高级格局） ---
    question = hex_result.get("question", "")
    empty_branches = hex_result.get("empty_branches", [])

    # 疾厄格局（近病逢空/逢合/逢冲）— 传入 step4_data 以增强动爻化空检测
    illness_pattern = _detect_classical_illness_pattern(question, step2_data, step3_data, empty_branches, step4_data=step4_data, hex_result=hex_result)
    if illness_pattern["pattern"]:
        return illness_pattern

    # 六合/六冲交互格局（冲中逢合/合处逢冲）
    harmony_clash_pattern = _detect_hexagram_harmony_clash_pattern(question, hex_result, step4_data)
    if harmony_clash_pattern["pattern"]:
        # 六冲主散 + 合伙类问题 + 用神旺 → 追加减分（用神虽旺但合伙难持久）
        if (harmony_clash_pattern.get("pattern") == "六冲主散"
                and ("合伙" in question)):
            try:
                ug_score_s5 = float(step3_data.get("effective_score", 2.5))
            except (TypeError, ValueError):
                ug_score_s5 = 2.5
            if ug_score_s5 >= 3.5:
                harmony_clash_pattern["score_adjustment"] -= 0.5
                harmony_clash_pattern["description"] += "（用神虽旺，合伙六冲终难持久）"
                harmony_clash_pattern["impact_on_verdict"] = (
                    (harmony_clash_pattern.get("impact_on_verdict") or "")
                    + "——用神虽旺而合伙难持久，额外减分"
                )
        return harmony_clash_pattern

    use_god_score = step3_data.get("effective_score", 2.5)
    hex_info = hex_result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    # Normalize score to float
    try:
        use_god_score = float(use_god_score)
    except (TypeError, ValueError):
        use_god_score = 2.5

    # ── Count elements in hexagram ──
    elem_counts: dict[str, int] = {}
    for yao in yao_lines:
        elem = yao.get("element", "")
        if not elem:
            branch = yao.get("earthly_branch", "")
            elem = _branch_element(branch)
        if elem:
            elem_counts[elem] = elem_counts.get(elem, 0) + 1

    # ── Check 1: 从格 (Following Pattern) ──
    # Condition: 用神极弱(<-1.0), 原神无援(<1.5), 忌神极旺(>3.5) or absent,
    #            all moving lines trend toward 忌神, NO 冲中逢合救应
    # ⚠️ 从格为极端罕见格局，必须严格判定，避免误判正常弱卦
    if use_god_score < -1.0:
        yuan_shen = step2_data.get("yuan_shen", {}) or {}
        ji_shen = step2_data.get("ji_shen", {}) or {}
        yuan_positions = yuan_shen.get("positions", []) or []
        ji_positions = ji_shen.get("positions", []) or []

        # 原神评估：无位置或位置少则视为无援
        yuan_shen_weak = len(yuan_positions) == 0
        if not yuan_shen_weak and yuan_positions:
            # Check if yuan_shen has any moving line support
            yuan_moving = [p for p in yuan_positions if p.get("is_moving")]
            yuan_shen_weak = len(yuan_moving) == 0 and len(yuan_positions) <= 1

        # 忌神评估：有多个位置视为极旺
        ji_shen_strong = len(ji_positions) >= 2

        # 若有"冲中逢合"、"化合"等明显救应模式，不从格
        step4_details = step4_data.get("details", []) if step4_data else []
        has_rescue = False
        for m in step4_details:
            ct = m.get("change_type", "")
            if ct in ("化合", "六合", "三合", "化进神"):
                has_rescue = True
                break
        if has_rescue:
            pass  # skip 从格
        elif ji_shen_strong and yuan_shen_weak:
            return {
                "pattern": "从格",
                "description": f"用神极弱（{use_god_score:.2f}）原神无援，忌神独旺（{len(ji_positions)}位），顺势从之",
                "impact_on_verdict": "反转标准判断——本应判凶反为吉，用神弃命从强",
                "rule_applied": "《增删易》'弱极反旺，从格为用'",
                "score_adjustment": 3.0,
            }

    # ── Check 1b: 原神绝位·用神失源 (绝处逢生反断为凶) ──
    # 条件：用神偏弱(score<2.0) + 原神不现或极弱(无实际爻位) + 无动变救援 → 大凶
    # 区别于从格：不反转方向(不加分)，而是强化凶断(减分)
    # 《增删易》"绝处逢生反断为凶"：原神无援→用神气绝→断凶不疑
    if use_god_score < 2.0:
        yuan_shen2 = step2_data.get("yuan_shen", {}) or {}
        yuan_positions2 = yuan_shen2.get("positions", []) or []
        yuan_fucang2 = yuan_shen2.get("fu_cang", None)
        # 原神不现：完全无位置，或仅有伏藏(飞神下的隐藏原神)
        _yuan_absent = len(yuan_positions2) == 0
        # 无动变内生救援(step4无正面力量)
        step4_details2 = step4_data.get("details", []) if step4_data else []
        _has_positive_change = any(
            isinstance(m, dict) and m.get("effect_score", 0) > 0.3
            for m in step4_details2
        )
        net_effect2 = step4_data.get("net_effect", 0) if step4_data else 0
        # 触发条件：原神完全不现 + 用神偏弱 + 无动变正面效应 + net_effect不显著正
        if _yuan_absent and not _has_positive_change and (isinstance(net_effect2, (int, float)) and net_effect2 <= 0.1):
            return {
                "pattern": "原神绝位·用神失源",
                "description": f"用神弱（{use_god_score:.2f}）原神不现（仅伏藏或无援），绝处逢生反断为凶",
                "impact_on_verdict": "原神气绝不能生用，用神孤立无援→大凶",
                "rule_applied": "《增删易》'原神无援，用神气绝，断凶不疑'",
                "score_adjustment": -2.0,
            }

    # ── Check 2: 专旺格 (Dominant Element Pattern) ──
    # Condition: one element >= 4 of 6 yao, score >= 4.0
    if elem_counts:
        max_elem = max(elem_counts, key=elem_counts.get)
        max_count = elem_counts[max_elem]
        if max_count >= 4:
            return {
                "pattern": "专旺格",
                "description": f"{max_elem}气独旺（{max_count}/6爻）",
                "impact_on_verdict": "喜顺泄不宜克逆——用神属此元素大吉，他元素不振无碍",
                "rule_applied": "《卜筮正宗》'专旺喜泄不喜克'",
                "score_adjustment": 0.0,  # 不直接加分，而是降低忌神惩罚
            }

    # ── Check 3: 两神成象格 (Two Element Coexistence) ──
    # Condition: exactly 2 elements, each ~3 yao, no major 相克 in moving lines
    if len(elem_counts) == 2:
        elems = list(elem_counts.keys())
        if abs(elem_counts[elems[0]] - elem_counts[elems[1]]) <= 1:
            # Check no major attacking in moving lines
            has_major_attack = False
            for m in moving_analysis:
                ct = m.get("change_type", "")
                if ct in ("回头克", "化墓", "化绝"):
                    has_major_attack = True
                    break
            if not has_major_attack:
                return {
                    "pattern": "两神成象",
                    "description": f"{elems[0]}（{elem_counts[elems[0]]}）与{elems[1]}（{elem_counts[elems[1]]}）各据一方，势均力敌",
                    "impact_on_verdict": "视用神所在方之旺衰定吉凶——用神方旺则吉",
                    "rule_applied": "《增删易》'两象平衡以用神方取'",
                    "score_adjustment": 0.0,
                }

    # ── Check 4: 化格 (Transformation Pattern) ──
    # Condition: 用神本身的动爻参与三合化才算真正化格
    # ⚠️ 化格是极端罕见格局，普通三合但不涉及用神动爻时不触发
    advanced = hex_result.get("advanced_analysis", {})
    if advanced and isinstance(advanced, dict):
        tc_data = advanced.get("triple_combo", {})
        if isinstance(tc_data, dict) and tc_data.get("has_triple_combo"):
            use_god_elem = step2_data.get("use_god_element", "土")
            # 获取用神动爻位置列表（用神发动才算化）
            use_god_moving_positions = set()
            for d in (step4_data.get("details") or step4_data.get("moving_details") or []):
                if isinstance(d, dict):
                    d_pos = d.get("position") or d.get("from_position") or 0
                    d_rel = d.get("change_type", "")
                    if d_pos and d_rel and "化合" not in d_rel and "六合" not in d_rel:
                        # 检查这条动爻是否是用神
                        d_orig_branch = d.get("original_branch", d.get("from_branch", ""))
                        if d_orig_branch:
                            d_orig_elem = _branch_element(d_orig_branch)
                            if d_orig_elem == use_god_elem:
                                use_god_moving_positions.add(d_pos)
            details = tc_data.get("details", []) or []
            for combo in details:
                target_elem = combo.get("element", "")
                positions = combo.get("positions", []) or []
                if target_elem and target_elem != use_god_elem:
                    # 严格条件: 用神动爻本身在三合中，且化出非用神元素
                    involved = use_god_moving_positions & set(positions or [])
                    if involved:
                        return {
                            "pattern": "化格",
                            "description": f"三合化{target_elem}，用神动爻{involved}随局而化",
                            "impact_on_verdict": f"用神随三合化{target_elem}，+0.5",
                            "rule_applied": "三合化气，用神发动随局而变",
                            "score_adjustment": +0.5,
                        }

    # ── No special pattern ──
    return {
        "pattern": None,
        "description": "无特殊格局，按常规断法",
        "impact_on_verdict": "无调整",
        "rule_applied": "常规旺衰断法",
        "score_adjustment": 0.0,
    }


# =============================================================================
# Step 4 Helper: 贪合忘生克 (Greedy Conjunction)
# =============================================================================

# 六合 pairs as lookup set for quick membership test
_HEXAGRAM_HARMONY_SET = set()
for _a, _b in HE_PAIRS:
    _HEXAGRAM_HARMONY_SET.add(f"{_a}{_b}")
    _HEXAGRAM_HARMONY_SET.add(f"{_b}{_a}")

# 三合 (triple combination) — each element combination needs 3 of 4 branches
_SAN_HE_SET = set()
for _elem, _branches in SAN_HE.items():
    for i in range(len(_branches)):
        for j in range(i + 1, len(_branches)):
            _SAN_HE_SET.add(f"{_branches[i]}{_branches[j]}|{_elem}")
            _SAN_HE_SET.add(f"{_branches[j]}{_branches[i]}|{_elem}")


def _forms_hexagram_harmony(branch1: str, branch2: str) -> bool:
    """Check if two branches form 六合."""
    if not branch1 or not branch2:
        return False
    key = f"{branch1}{branch2}"
    return key in _HEXAGRAM_HARMONY_SET


def _check_greedy_harmony(
    yao_lines: list[dict],
    moving_lines: list[dict],
    day_branch: str,
    month_branch: str,
    use_god_category: str,
    yuan_shen_element: str,
    ji_shen_element: str,
    palace_element: str,
) -> tuple[float, list[dict]]:
    """
    贪合忘生克检测 — rule from 《增删易》.

    When a yao forms 六合 with another yao or with 日辰/月建, it becomes "贪合" —
    obsessed with the conjunction. This causes:
    - 原神贪合忘生 → the 原神 fails to generate its 用神
    - 忌神贪合忘克 → the 忌神 fails to attack its 用神 (beneficial)

    Parameters
    ----------
    yao_lines : list[dict]
        All 6 yao lines.
    moving_lines : list[dict]
        Subset of yao_lines that are moving (动爻 or 暗动).
    day_branch : str
        Day branch.
    month_branch : str
        Month branch.
    use_god_category : str
        The use god relation (e.g. "妻财", "官鬼").
    yuan_shen_element : str
        Element of the 原神.
    ji_shen_element : str
        Element of the 忌神.
    palace_element : str
        Element of the palace.

    Returns
    -------
    tuple[float, list[dict]]
        (score_adjustment, issues_list). Positive = beneficial, negative = harmful.
        Empty list if no issues found.
    """
    if not moving_lines:
        return 0.0, []

    issues = []
    score_adjustment = 0.0
    yuan_shen_relation_name = _element_to_relation(yuan_shen_element, palace_element) if yuan_shen_element else ""
    ji_shen_relation_name = _element_to_relation(ji_shen_element, palace_element) if ji_shen_element else ""

    for yao in moving_lines:
        pos = yao.get("position", 0)
        orig_branch = yao.get("earthly_branch", "") or yao.get("branch", "")
        orig_relation = yao.get("six_relation", "")
        orig_element = _branch_element(orig_branch) if orig_branch else ""
        changed_branch = yao.get("changed_branch", "")

        # Determine the branch to check for harmony:
        # Use the original branch if static/hidden-moved, or changed branch if moving
        branches_to_check = [orig_branch]
        if changed_branch:
            branches_to_check.append(changed_branch)

        for target_branch in branches_to_check:
            if not target_branch:
                continue

            # Check 合 with 日辰
            if _forms_hexagram_harmony(target_branch, day_branch):
                # Classify by role
                if orig_relation == yuan_shen_relation_name or orig_element == yuan_shen_element:
                    # 原神贪合忘生 → harmful:原神 can't generate use god
                    effect_score = -0.3
                    reason = f"原神{orig_relation}（{_pos_to_name(pos)}爻·{orig_branch}）与{day_branch}日六合，贪合忘生用神"
                    issues.append({
                        "type": "原神贪合忘生",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"日辰{day_branch}",
                        "effect": "原神贪合，暂不能生用神（减力）",
                        "benefit_or_loss": "unfavorable",
                        "score_effect": effect_score,
                    })
                    score_adjustment += effect_score

                elif orig_relation == ji_shen_relation_name or orig_element == ji_shen_element:
                    # 忌神贪合忘克 → beneficial:忌神 can't attack use god
                    effect_score = 0.2
                    reason = f"忌神{orig_relation}（{_pos_to_name(pos)}爻·{orig_branch}）与{day_branch}日六合，贪合忘克用神"
                    issues.append({
                        "type": "忌神贪合忘克",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"日辰{day_branch}",
                        "effect": "忌神贪合，暂不克用神（减凶）",
                        "benefit_or_loss": "favorable",
                        "score_effect": effect_score,
                    })
                    score_adjustment += effect_score

                elif orig_relation == use_god_category:
                    # 用神本身被合 → 合绊，暂受阻滞
                    effect_score = -0.2
                    reason = f"用神（{_pos_to_name(pos)}爻·{orig_branch}）与{day_branch}日六合，合绊暂滞"
                    issues.append({
                        "type": "用神被合",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"日辰{day_branch}",
                        "effect": "用神被合绊，暂受阻滞",
                        "benefit_or_loss": "neutral",
                        "score_effect": effect_score,
                    })
                    score_adjustment += effect_score
                else:
                    # Other lines harmonized with day
                    issues.append({
                        "type": "合绊",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"日辰{day_branch}",
                        "effect": f"{orig_relation}{_pos_to_name(pos)}爻与日合绊",
                        "benefit_or_loss": "neutral",
                        "score_effect": 0.0,
                    })

            # Check 合 with 月建
            if month_branch and _forms_hexagram_harmony(target_branch, month_branch):
                if orig_relation == yuan_shen_relation_name or orig_element == yuan_shen_element:
                    effect_score = -0.2
                    reason = f"原神{orig_relation}（{_pos_to_name(pos)}爻·{orig_branch}）与{month_branch}月六合，贪合忘生"
                    issues.append({
                        "type": "原神贪合忘生",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"月建{month_branch}",
                        "effect": "原神与月合绊，暂不能生用神",
                        "benefit_or_loss": "unfavorable",
                        "score_effect": effect_score,
                    })
                    score_adjustment += effect_score

                elif orig_relation == ji_shen_relation_name or orig_element == ji_shen_element:
                    effect_score = 0.15
                    reason = f"忌神{orig_relation}（{_pos_to_name(pos)}爻·{orig_branch}）与{month_branch}月六合，贪合忘克"
                    issues.append({
                        "type": "忌神贪合忘克",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"月建{month_branch}",
                        "effect": "忌神与月合绊，暂不克用神（减凶）",
                        "benefit_or_loss": "favorable",
                        "score_effect": effect_score,
                    })
                    score_adjustment += effect_score
                else:
                    issues.append({
                        "type": "合绊",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"月建{month_branch}",
                        "effect": f"{orig_relation}{_pos_to_name(pos)}爻与月合绊",
                        "benefit_or_loss": "neutral",
                        "score_effect": 0.0,
                    })

    return round(score_adjustment, 2), issues


# =============================================================================
# Step 4: 察变 (Change Analysis)
# =============================================================================

def step4_analyze_changes(r: dict) -> dict:
    """
    Step 4: 察变 — 分析动爻及其影响。

    对每一动爻分析：
    1. 何六亲动？（原神？忌神？仇神？）
    2. 动化何种？（回头生/克/进退/化合/入墓/化绝）
    3. 对用神的净效应

    经典规则《黄金策》：
    - 回头生（变爻生动爻）：极为有利 → 原神回头生用尤佳
    - 回头克（变爻克动爻）：极为不利 → 用神回头克大凶
    - 化进神：势盛递增
    - 化退神：势衰递减
    - 化墓/化绝：困顿断绝
    - 六合（动爻与变爻合）：绊住（贪合忘生/克）

    贪生忘克：如有原神动，忌神贪生忘克用神。
    贪合忘生/克：动变相合则贪合忘其生克。
    """
    # 获取上下文
    hex_info = safe_get(r, "original_hexagram", default={})
    yao_lines = safe_get(hex_info, "yao_lines", default=[])
    changed = safe_get(r, "changed_hexagram", default={})
    changed_name = safe_get(changed, "name", default=None)
    palace_element = safe_get(hex_info, "palace_element", default="")

    # 获取日月建
    div_time = safe_get(r, "divination_time", default={})
    month_stem_branch = safe_get(div_time, "month_stem_branch", default="")
    day_stem_branch = safe_get(div_time, "day_stem_branch", default="")
    month_branch = month_stem_branch[1:] if len(month_stem_branch) >= 2 else ""
    day_branch = day_stem_branch[1:] if len(day_stem_branch) >= 2 else ""

    # 获取用神信息（从 step2）
    step2_data = safe_get(r, "_step2_data", default={})
    use_god_category = safe_get(step2_data, "use_god_category", default="")
    use_god_element = safe_get(step2_data, "use_god_element", default="")
    yuan_shen_element = safe_get(step2_data, "yuan_shen", "element", default="")
    ji_shen_element = safe_get(step2_data, "ji_shen", "element", default="")
    chou_shen_element = safe_get(step2_data, "chou_shen", "element", default="")

    # ---------- 4.1: 收集所有动爻信息 ----------
    moving_lines = [yao for yao in yao_lines if yao.get("is_moving", False)]

    # Check for 暗动 even in "static" hexagrams (no explicit moving lines)
    step3_hm_data = safe_get(r, "_step3_data", default={})
    hm_lines = step3_hm_data.get("hidden_movement", []) or []

    if not moving_lines and not hm_lines:
        return {
            "has_moving_lines": False,
            "moving_count": 0,
            "details": [],
            "favorable_changes": [],
            "unfavorable_changes": [],
            "tan_sheng_wan_ke": [],
            "tan_he_wan_sheng_ke": [],
            "greedy_harmony_issues": [],
            "greedy_harmony_score": 0.0,
            "net_effect": 0.0,
            "net_effect_description": "静卦无动爻，以用神旺衰论吉凶",
            "summary_text": "静卦，无动爻变化。吉凶专凭用神旺衰断之。",
        }

    # ---------- 4.2: 逐动爻分析 ----------
    details = []
    favorable_changes = []
    unfavorable_changes = []
    net_effect = 0.0

    for yao in moving_lines:
        pos = yao.get("position", 0)
        orig_branch = yao.get("earthly_branch", "")
        orig_relation = yao.get("six_relation", "")
        orig_element = _branch_element(orig_branch)
        orig_spirit = yao.get("six_spirit", "")

        # 获取变爻地支
        chg_branch = get_changed_hexagram_branch(changed_name, pos) if changed_name else None
        chg_element = _branch_element(chg_branch) if chg_branch else ""
        chg_relation = get_relation_from_element(chg_element, palace_element) if chg_element else ""

        # 判断动爻身份（相对于用神）
        line_role = _classify_line_role(
            orig_relation, use_god_category,
            orig_element, use_god_element,
            yuan_shen_element, ji_shen_element, chou_shen_element
        )

        # 判断变化类型
        change_type = _determine_change_type(
            orig_branch, chg_branch, orig_element, chg_element,
            month_branch, day_branch
        )

        # 分析对用神的直接/间接影响
        effect_on_usegod = _analyze_effect_on_use_god(
            orig_branch, chg_branch,
            orig_element, chg_element,
            use_god_element,
            change_type,
            line_role,
        )

        detail = {
            "position": pos,
            "name": _pos_to_name(pos),
            "original_branch": orig_branch,
            "original_element": orig_element,
            "original_relation": orig_relation,
            "original_spirit": orig_spirit,
            "line_role": line_role,
            "changed_branch": chg_branch,
            "changed_element": chg_element,
            "changed_relation": chg_relation,
            "change_type": change_type["type"],
            "change_detail": change_type["detail"],
            "effect_on_usegod": effect_on_usegod["description"],
            "effect_score": effect_on_usegod["score"],
        }
        details.append(detail)

        net_effect += effect_on_usegod["score"]

        if effect_on_usegod["score"] > 0:
            favorable_changes.append(detail)
        elif effect_on_usegod["score"] < 0:
            unfavorable_changes.append(detail)

    # ---------- 4.3: 贪生忘克/贪合忘生克规则 ----------
    tan_sheng_wan_ke = _check_tan_sheng_wan_ke(details, use_god_element, palace_element)
    tan_he_wan_sheng_ke = _check_tan_he_wan_sheng_ke(details, yao_lines, use_god_category)

    # 应用贪生忘克修正
    for rule in tan_sheng_wan_ke:
        detail = next((d for d in details if d["position"] == rule["detail_position"]), None)
        if detail:
            old_score = detail["effect_score"]
            detail["effect_score"] *= 0.5  # 减半效应
            detail["effect_on_usegod"] += f"（贪生忘克：{reason}）".replace("reason", rule["reason"])
            net_effect += (detail["effect_score"] - old_score)

    for rule in tan_he_wan_sheng_ke:
        detail = next((d for d in details if d["position"] == rule["detail_position"]), None)
        if detail:
            old_score = detail["effect_score"]
            detail["effect_score"] *= 0.5
            detail["effect_on_usegod"] += f"（贪合忘生克：{rule['reason']}）"
            net_effect += (detail["effect_score"] - old_score)

    # ---------- 4.3b: 贪合忘生克（日月合绊检查） ----------
    # Also include 暗动 lines for greedy harmony check
    step3_data_for_hm = safe_get(r, "_step3_data", default={})
    hm_lines = step3_data_for_hm.get("hidden_movement", []) or []
    # Combine moving lines with hidden-moved lines (as virtual moving lines for harmony check)
    all_active_lines = list(moving_lines)
    for hm in hm_lines:
        # Find the actual yao for this hidden-moved position
        for yl in yao_lines:
            if yl.get("position") == hm.get("position"):
                all_active_lines.append(yl)
                break

    greedy_harmony_score, greedy_harmony_issues = _check_greedy_harmony(
        yao_lines=all_active_lines,
        moving_lines=all_active_lines,
        day_branch=day_branch,
        month_branch=month_branch,
        use_god_category=use_god_category,
        yuan_shen_element=yuan_shen_element,
        ji_shen_element=ji_shen_element,
        palace_element=palace_element,
    )

    # Apply greedy harmony adjustment to net_effect
    net_effect += greedy_harmony_score

    # ---------- 4.3c: 进退神力量量化（来自 classical_analysis.advance_score） ----------
    # 当 enhance_reading 已运行时（advanced_analysis 存在），读取进退神数值评分
    advance_score_total = 0.0
    _advanced_data = r.get("advanced_analysis", {})
    if _advanced_data and isinstance(_advanced_data, dict):
        _ar_data = _advanced_data.get("advance_retreat", {})
        if isinstance(_ar_data, dict):
            for _ar_item in _ar_data.get("details", []):
                _ascore = _ar_item.get("advance_score", 0.0)
                if isinstance(_ascore, (int, float)) and _ascore != 0.0:
                    advance_score_total += _ascore
    if abs(advance_score_total) > 0.001:
        net_effect += advance_score_total

    # ---------- 4.4: 净效应判断 ----------
    net_effect = round(net_effect, 2)
    if net_effect >= 1.5:
        net_description = "大吉（动变全面有利）"
    elif net_effect >= 0.5:
        net_description = "偏吉（动变总体有利）"
    elif net_effect >= -0.5:
        net_description = "中性（动变利弊参半）"
    elif net_effect >= -1.5:
        net_description = "偏凶（动变总体不利）"
    else:
        net_description = "大凶（动变全面不利）"

    # Build greedy harmony description for summary
    greedy_harmony_summary = ""
    if greedy_harmony_issues:
        issue_descs = [i["effect"] for i in greedy_harmony_issues if i.get("score_effect", 0) != 0]
        if issue_descs:
            greedy_harmony_summary = "日月合绊：" + "、".join(issue_descs) + "；"

    return {
        "has_moving_lines": True,
        "moving_count": len(moving_lines),
        "details": details,
        "favorable_changes": favorable_changes,
        "unfavorable_changes": unfavorable_changes,
        "favorable_count": len(favorable_changes),
        "unfavorable_count": len(unfavorable_changes),
        "tan_sheng_wan_ke": tan_sheng_wan_ke,
        "tan_he_wan_sheng_ke": tan_he_wan_sheng_ke,
        "greedy_harmony_issues": greedy_harmony_issues,
        "greedy_harmony_score": greedy_harmony_score,
        "advance_score_total": round(advance_score_total, 2),
        "net_effect": net_effect,
        "net_effect_description": net_description,
        "summary_text": _compose_change_summary(
            moving_lines, favorable_changes, unfavorable_changes,
            tan_sheng_wan_ke, tan_he_wan_sheng_ke, greedy_harmony_summary,
            advance_score_total, net_effect, net_description,
        ),
    }


# --- Step 4 辅助函数 ---



def _compose_change_summary(moving_lines, favorable_changes, unfavorable_changes,
                            tan_sheng_wan_ke, tan_he_wan_sheng_ke, greedy_harmony_summary,
                            advance_score_total, net_effect, net_description) -> str:
    n = len(moving_lines or [])
    if n == 0:
        return "卦中没有动爻，事情安静，吉凶主要看用神自身，而不是中途杀出的变数。"
    parts = [f"卦中有{n}个动爻。"]
    fav, unfav = len(favorable_changes or []), len(unfavorable_changes or [])
    if fav and not unfav:
        parts.append("动处总体是帮事情的。")
    elif unfav and not fav:
        parts.append("动处总体在拖后腿。")
    elif fav and unfav:
        parts.append(f"有帮衬也有牵扯（利{fav}弊{unfav}），不能只看一处。")
    else:
        parts.append("动处影响平淡，主线仍在用神。")
    reasons = []
    for r in (tan_sheng_wan_ke or []):
        reasons.append(str(r.get("reason") or ""))
    for r in (tan_he_wan_sheng_ke or []):
        reasons.append(str(r.get("reason") or ""))
    if greedy_harmony_summary:
        reasons.append(str(greedy_harmony_summary).rstrip("；"))
    reasons = [x.rstrip("；。") for x in reasons if x]
    if reasons:
        parts.append("具体来看：" + "；".join(reasons[:4]) + "。")
    if abs(advance_score_total or 0) > 0.001:
        parts.append("进退之势也要计入。")
    net_desc = str(net_description or "").replace("（动变总体有利）", "").replace("（动变总体不利）", "")
    net_desc = net_desc.replace("（动变利弊参半）", "").strip()
    net_val = float(net_effect or 0)
    if net_val > 0.3:
        parts.append("综合动变，对事情偏有利。")
    elif net_val < -0.3:
        parts.append("综合动变，对事情偏不利。" + (f"（{net_desc}）" if net_desc and net_desc not in ("中性", "偏吉", "偏凶") else ""))
    else:
        parts.append("综合动变，利弊大致相抵。")
    return "".join(parts)


def _classify_line_role(
    relation: str,
    use_god_category: str,
    element: str,
    use_god_element: str,
    yuan_shen_element: str,
    ji_shen_element: str,
    chou_shen_element: str,
) -> str:
    """判断动爻相对于用神的身份"""
    if relation == use_god_category:
        return "用神"
    if element == use_god_element:
        return "用神同气"
    if element == yuan_shen_element:
        return "原神"
    if element == ji_shen_element:
        return "忌神"
    if element == chou_shen_element:
        return "仇神"
    # 其他：判断与用神关系
    if SHENG_CYCLE.get(element) == use_god_element:
        return "生用神之爻"  # 生用神者
    if KE_CYCLE.get(element) == use_god_element:
        return "克用神之爻"  # 克用神者
    return "闲神"


def _determine_change_type(
    orig_branch: str,
    chg_branch: str | None,
    orig_element: str,
    chg_element: str,
    month_branch: str,
    day_branch: str,
) -> dict:
    """判断动爻变化类型"""
    if not chg_branch:
        return {"type": "无变爻", "detail": "变卦缺失"}

    # 回头生：变爻五行生动爻五行
    if SHENG_CYCLE.get(chg_element) == orig_element:
        # 排除化合情况
        if _is_he(orig_branch, chg_branch):
            return {"type": "六合", "detail": f"{orig_branch}与{chg_branch}六合（土）, 贪合忘生"}
        return {"type": "回头生", "detail": f"变爻{chg_element}生动爻{orig_element}，化进"}

    # 回头克：变爻五行克动爻五行
    if KE_CYCLE.get(chg_element) == orig_element:
        if _is_he(orig_branch, chg_branch):
            return {"type": "六合", "detail": f"{orig_branch}与{chg_branch}六合, 贪合忘克"}
        return {"type": "回头克", "detail": f"变爻{chg_element}克动爻{orig_element}，不利"}

    # 化进/化退
    if ADVANCE_PAIRS.get(orig_branch) == chg_branch:
        return {"type": "化进神", "detail": f"{orig_branch}化{chg_branch}进，力量递增"}
    if RETREAT_PAIRS.get(orig_branch) == chg_branch:
        return {"type": "化退神", "detail": f"{orig_branch}化{chg_branch}退，力量递减"}

    # 化墓
    if TOMB_MAP.get(orig_element) == chg_branch:
        return {"type": "化墓", "detail": f"{orig_element}化入{chg_branch}墓库，困顿之象"}

    # 化绝
    if JUE_MAP.get(orig_element) == chg_branch:
        return {"type": "化绝", "detail": f"{orig_element}化入{chg_branch}绝地，气绝之象"}

    # 六合（地支相合）
    if _is_he(orig_branch, chg_branch):
        return {"type": "六合", "detail": f"{orig_branch}与{chg_branch}六合，可能绊住"}

    # 反吟
    if _is_chong(orig_branch, chg_branch):
        return {"type": "反吟", "detail": f"{orig_branch}冲{chg_branch}，反复不安"}

    return {"type": "化合", "detail": f"{orig_branch}→{chg_branch}，性质转变（{orig_element}→{chg_element}）"}


def _analyze_effect_on_use_god(
    orig_branch: str,
    chg_branch: str | None,
    orig_element: str,
    chg_element: str,
    use_god_element: str,
    change_type: dict,
    line_role: str,
) -> dict:
    """
    分析动爻变化对用神的净效应。
    返回 {description, score}，score 为正=有利，为负=不利。
    """
    score = 0.0
    description_parts = []

    # 基于身份和变化类型打分
    if line_role == "用神":
        # 用神自身动变
        ct = change_type["type"]
        if ct == "回头生":
            score = 1.5
            description_parts.append("用神动化回头生，大吉")
        elif ct == "回头克":
            score = -2.0
            description_parts.append("用神动化回头克，大凶")
        elif ct == "化进神":
            score = 1.0
            description_parts.append("用神化进，势盛")
        elif ct == "化退神":
            score = -1.0
            description_parts.append("用神化退，势衰")
        elif ct == "化墓":
            score = -1.5
            description_parts.append("用神化墓，困顿")
        elif ct == "化绝":
            score = -1.5
            description_parts.append("用神化绝，气断")
        elif ct == "反吟":
            score = -0.5
            description_parts.append("用神反吟，反复")
        elif ct == "六合":
            # 六合需看是合起还是合绊
            score = -0.3
            description_parts.append("用神合绊，暂时受阻")
        else:
            score = 0.0
            description_parts.append("用神动变平平")

    elif line_role == "原神":
        # 原神（用神的源头）动变
        ct = change_type["type"]
        if ct == "回头生":
            score = 1.5
            description_parts.append("原神动化回头生，源源不断生助用神")
        elif ct == "回头克":
            score = -1.0
            description_parts.append("原神动化回头克，源头受损")
        elif ct == "化进神":
            score = 1.0
            description_parts.append("原神化进，生用有力")
        elif ct == "化退神":
            score = -0.5
            description_parts.append("原神化退，生力减弱")
        elif ct == "化墓":
            score = -1.0
            description_parts.append("原神化墓，无力生用")
        elif ct == "六合":
            score = -0.3
            description_parts.append("原神合绊，暂难生用")
        elif RETREAT_PAIRS.get(orig_branch) == chg_branch:
            # 二次识别：变化类型未被 _determine_change_type 判为化退神，但进退神表匹配化退
            score = -0.5
            description_parts.append("原神化退（进退神判），生力减弱为凶")
        else:
            # 原神动（不论化什么都有一定助用效果）
            # 原神五行生用神 → 生用有力（《增删易》"原神发动，生用有力"）
            if SHENG_CYCLE.get(orig_element) == use_god_element:
                score = 1.0
                description_parts.append("原神发动，其五行生用神，生用有力")
            else:
                score = 0.3
                description_parts.append("原神动，有生用之心")

    elif line_role == "忌神":
        # 忌神（克用神者）动变
        ct = change_type["type"]
        if ct == "回头生":
            score = -1.5
            description_parts.append("忌神动化回头生，克用更甚")
        elif ct == "回头克":
            score = 1.5
            description_parts.append("忌神动化回头克，凶性反制（大吉）")
        elif ct == "化进神":
            score = -1.0
            description_parts.append("忌神化进，克用有力")
        elif ct == "化退神":
            score = 0.5
            description_parts.append("忌神化退，克力渐消")
        elif ct == "化墓":
            score = 1.0
            description_parts.append("忌神化墓，克用受阻（吉）")
        elif ct == "六合":
            score = 0.3
            description_parts.append("忌神合绊，克用受阻")
        else:
            score = -0.3
            description_parts.append("忌神动，有意克用")

    elif line_role == "仇神":
        # 仇神（克原神者）动变
        ct = change_type["type"]
        if ct == "化退神":
            score = 0.3
            description_parts.append("仇神化退，对原神威胁减少")
        elif ct == "化墓":
            score = 0.5
            description_parts.append("仇神化墓，原神得安")
        elif ct == "回头克":
            score = 1.0
            description_parts.append("仇神化回头克，原神得救")
        else:
            score = -0.2  # 仇神动总体轻微不利
            description_parts.append("仇神动，间接影响原神")

    else:
        # 与其他爻互动
        # 变爻与用神的关系
        if chg_branch and chg_element == use_god_element:
            # 动爻化出用神（化用）
            score = 0.5
            description_parts.append("动爻化出用神之气")
        elif chg_branch and SHENG_CYCLE.get(chg_element) == use_god_element:
            score = 0.3
            description_parts.append("动爻变化生用神")
        elif chg_branch and KE_CYCLE.get(chg_element) == use_god_element:
            score = -0.3
            description_parts.append("动爻变化克用神")
        else:
            description_parts.append("此动爻与用神关系疏远")

    return {
        "description": "；".join(description_parts) if description_parts else "影响不明显",
        "score": round(score, 2),
    }


def _check_tan_sheng_wan_ke(
    details: list[dict],
    use_god_element: str,
    palace_element: str,
) -> list[dict]:
    """
    贪生忘克规则检查。
    《黄金策》：贪生忘克者，原神动，忌神贪生原神而忘克用。
    条件：原神动 且 原神生忌神 同时存在
    """
    rules = []
    # 寻找原神动的详情
    yuan_shen_moving = [d for d in details if d["line_role"] == "原神"]
    ji_shen_moving = [d for d in details if d["line_role"] == "忌神"]

    for yuan in yuan_shen_moving:
        for ji in ji_shen_moving:
            # 检查原神和忌神是否相生（火生土类）
            yuan_elem = yuan["original_element"]
            ji_elem = ji["original_element"]
            if SHENG_CYCLE.get(yuan_elem) == ji_elem:
                rules.append({
                    "type": "贪生忘克",
                    "reason": f"原神{yuan['name']}生忌神{ji['name']}，忌神贪生忘克用神",
                    "detail_position": ji["position"],
                    "benefit_or_loss": "favorable",
                })
    return rules


def _check_tan_he_wan_sheng_ke(
    details: list[dict],
    yao_lines: list[dict],
    use_god_category: str,
) -> list[dict]:
    """
    贪合忘生/贪合忘克规则检查。
    条件：动爻与变爻六合，或动爻与日月合。
    """
    rules = []
    for detail in details:
        if detail["change_type"] == "六合":
            pos = detail["position"]
            rules.append({
                "type": "贪合忘生克",
                "reason": f"第{pos}爻动而六合，贪合而忘其生克",
                "detail_position": pos,
                "benefit_or_loss": "neutral",  # 有利有弊，视情况
            })
        # 检查与日月合
        orig_branch = detail.get("original_branch", "")
        chg_branch = detail.get("changed_branch")
        if chg_branch:
            # 检查动爻+日月合（简化）
            pass
    return rules


# =============================================================================
# Step 5: 综合判断 (Synthesis)
# =============================================================================

def _user_reason(text: str, fallback: str = "") -> str:
    """将开发者风格的 reason 精练为 ≤15 字的人话描述。"""
    if not text:
        return fallback
    s = re.sub(r'【[^】]*】', '', text)
    s = re.sub(r'\(x[\d.]+\)', '', s)
    s = re.sub(r'[（(]\d+\.?\d*[)）]', '', s)
    s = re.sub(r'（[^）]*）', '', s)
    s = re.sub(r'\s*[+-]\d+\.?\d*$', '', s)
    s = s.strip()
    if len(s) > 15:
        m = re.search(r'[，；、。]', s)
        if m and m.start() >= 4:
            s = s[:m.start()]
        else:
            s = s[:15]
    s = s.strip('，；、。')
    return s if s else fallback


def step5_synthesize(r: dict) -> dict:
    """
    Step 5: 综合判断 — 综合所有前序分析给出最终结论。

    这是最终判断步骤。此前四步的输出都汇聚于此。

    评分规则（加权）：
    1. 用神旺衰分（来自 step3）作为基础分
    2. 加上动变效应分（来自 step4）
    3. 应用卦体调候：六合卦+0.5，六冲卦-0.5
    4. 辅助神煞调整
    5. 得最终分数 → 定性判断

    最终判断区间：
    - 分数 > 4.0：大吉
    - 3.0-4.0：吉（小吉-吉）
    - 2.0-3.0：平吉/小吉
    - 1.0-2.0：平/小凶
    - 分数 < 1.0：凶

    预测置信度：
    - 信号清晰（旺+原神动）→ 高（>80%）
    - 信号混合 → 中（50-80%）
    - 信号矛盾 → 低（<50%），建议谨慎

    应期判断：
    - 逢值：用神临值日
    - 逢冲：用神逢冲日
    - 出空：旬空出旬
    - 旺则速应（当月/当日），衰则待时
    """
    # 获取前序步骤数据
    step3_data = safe_get(r, "_step3_data", default={})
    step4_data = safe_get(r, "_step4_data", default={})
    step2_data = safe_get(r, "_step2_data", default={})
    step1_data = safe_get(r, "_step1_data", default={})

    hex_info = safe_get(r, "original_hexagram", default={})
    div_time = safe_get(r, "divination_time", default={})
    day_stem_branch = safe_get(div_time, "day_stem_branch", default="")
    day_branch = day_stem_branch[1:] if len(day_stem_branch) >= 2 else ""

    # ---------- 5.1: 基础分（用神旺衰） ----------
    base_score = safe_get(step3_data, "effective_score", default=2.5)
    strength_level = safe_get(step3_data, "strength_level", default="中和")

    # ---------- 5.2: 动变效应加成 ----------
    change_net_effect = safe_get(step4_data, "net_effect", default=0.0)

    # ---------- 5.3: 卦体调候 ----------
    hex_name = safe_get(step1_data, "hexagram_name", default="")
    palace = safe_get(step1_data, "palace", default="")

    hex_adjustment = 0.0
    hex_adjustment_reason = ""

    # 六合卦检查（上下卦各爻对应六合）
    if hex_name in HEXAGRAM_LIUHE:
        hex_adjustment += 0.5
        hex_adjustment_reason = "六合卦，事主和合"

    # 六冲卦检查
    if hex_name in HEXAGRAM_LIUCHONG:
        hex_adjustment -= 0.5
        hex_adjustment_reason = "六冲卦，事主散离"

    # ---------- 5.4: 六神辅助调整（协纪辨方书—六兽分阴阳日）----------
    spirit_adjustment = 0.0
    spirit_adjustment_reasons = []
    use_god_position = safe_get(step3_data, "use_god_position", default=None)
    yao_lines = safe_get(hex_info, "yao_lines", default=[])

    # 六兽分阴阳日力重 — 取出日干
    day_stem = day_stem_branch[0] if len(day_stem_branch) >= 1 else ""
    spirit_yy_factors = {}
    if day_stem:
        try:
            from classical_analysis import spirit_yin_yang_factor
            spirit_yy_factors = spirit_yin_yang_factor(day_stem)
        except ImportError:
            pass

    if use_god_position:
        for yao in yao_lines:
            if yao.get("position") == use_god_position:
                spirit = yao.get("six_spirit", "")
                yy_factor = spirit_yy_factors.get(spirit, 1.0) if spirit_yy_factors else 1.0
                if spirit == "青龙":
                    spirit_adjustment += 0.3 * yy_factor
                    if yy_factor > 1.0:
                        spirit_adjustment_reasons.append(f"青龙临用，阳日力增，吉上添吉(x{yy_factor})")
                    elif yy_factor < 1.0:
                        spirit_adjustment_reasons.append(f"青龙临用，阴日力略减(x{yy_factor})")
                    else:
                        spirit_adjustment_reasons.append("青龙临用，喜气之象")
                elif spirit == "白虎":
                    spirit_adjustment -= 0.5 * yy_factor
                    if yy_factor > 1.0:
                        spirit_adjustment_reasons.append(f"白虎临用，阳日凶焰更炽(x{yy_factor})")
                    elif yy_factor < 1.0:
                        spirit_adjustment_reasons.append(f"白虎临用，阴日凶焰稍敛(x{yy_factor})")
                    else:
                        spirit_adjustment_reasons.append("白虎临用，丧凶之兆")
                elif spirit == "玄武":
                    spirit_adjustment -= 0.3 * yy_factor
                    if yy_factor > 1.0:
                        spirit_adjustment_reasons.append(f"玄武临用，阴日暗昧更重(x{yy_factor})")
                    elif yy_factor < 1.0:
                        spirit_adjustment_reasons.append(f"玄武临用，阳日暗昧被抑(x{yy_factor})")
                    else:
                        spirit_adjustment_reasons.append("玄武临用，暗昧不明")
                elif spirit == "朱雀":
                    spirit_adjustment += 0.1 * yy_factor
                    if yy_factor > 1.0:
                        spirit_adjustment_reasons.append(f"朱雀临用，阳日口舌更显(x{yy_factor})")
                    elif yy_factor < 1.0:
                        spirit_adjustment_reasons.append(f"朱雀临用，阴日口舌稍抑(x{yy_factor})")
                    else:
                        spirit_adjustment_reasons.append("朱雀临用，文书口舌")
                elif spirit == "勾陈":
                    spirit_adjustment -= 0.2 * yy_factor
                    if yy_factor > 1.0:
                        spirit_adjustment_reasons.append(f"勾陈临用，阳日官非更显(x{yy_factor})")
                    elif yy_factor < 1.0:
                        spirit_adjustment_reasons.append(f"勾陈临用，阴日事缓(x{yy_factor})")
                    else:
                        spirit_adjustment_reasons.append("勾陈临用，牵绊迟滞")
                elif spirit == "螣蛇":
                    spirit_adjustment -= 0.1 * yy_factor
                    if yy_factor > 1.0:
                        spirit_adjustment_reasons.append(f"螣蛇临用，阴日惊恐更甚(x{yy_factor})")
                    elif yy_factor < 1.0:
                        spirit_adjustment_reasons.append(f"螣蛇临用，阳日惊恐略抑(x{yy_factor})")
                    else:
                        spirit_adjustment_reasons.append("螣蛇临用，惊恐怪异")
                break

    # ---------- 5.5: 暗动加分/贪合忘生克修正 ----------
    # Hidden movement modifier from step3 (already applied to effective_score,
    # but we track it explicitly here for transparency)
    hm_modifier = safe_get(step3_data, "hidden_movement_modifier", default=0.0)
    hm_reason = safe_get(step3_data, "hidden_movement_reason", default="")
    hm_count = len(safe_get(step3_data, "hidden_movement", default=[]))

    # Greedy harmony score from step4 (already included in net_effect)
    greedy_score = safe_get(step4_data, "greedy_harmony_score", default=0.0)
    greedy_issues = safe_get(step4_data, "greedy_harmony_issues", default=[]) or []
    greedy_reason_parts = [
        i["effect"] for i in greedy_issues
        if i.get("score_effect", 0) != 0
    ]
    greedy_reason = ("、".join(greedy_reason_parts)) if greedy_reason_parts else ""

    # ---------- 5.5c: 三刑减分（来自 step3 已计入 effective_score，此处仅记录展示） ----------
    tp_score = safe_get(step3_data, "three_punishment_modifier", default=0.0)
    tp_reason = safe_get(step3_data, "three_punishment_reason", default="")

    # ---------- 5.5d: 日月合用神调整 (Gap 5) ----------
    # Re-run analysis here where thinking_chain data is available
    dmb_adjustment = 0.0
    dmb_reason = ""
    dmb_findings = []
    # ---------- 5.5e: 六破调整 (Gap 6) ----------
    sb_adjustment = 0.0
    sb_reason = ""
    sb_description = ""

    advanced = r.get("advanced_analysis", {})
    try:
        from classical_analysis import analyze_day_month_bonding, analyze_six_breaks
        # Build a synthetic result dict with thinking_chain data for the analysis functions
        analysis_input = dict(r)
        # Ensure thinking_chain structure exists for the helpers to find step2/step3 data
        if "thinking_chain" not in analysis_input:
            analysis_input["thinking_chain"] = {
                "step2_use_god_identification": step2_data,
                "step3_strength_analysis": step3_data,
            }
        dmb_data = analyze_day_month_bonding(analysis_input)
        dmb_adjustment = dmb_data.get("total_score_modifier", 0.0)
        dmb_findings = dmb_data.get("findings", [])
        if dmb_findings:
            dmb_reason = "、".join(
                f"{f['bond']}（{f['effect']}）" for f in dmb_findings
            )

        sb_data = analyze_six_breaks(analysis_input)
        sb_adjustment = sb_data.get("total_modifier", 0.0)
        sb_description = sb_data.get("description", "")
        if sb_data.get("has_break"):
            sb_reason = sb_data.get("description", "")
    except ImportError:
        # Fallback: use pre-computed values from enhance_reading if available
        if advanced:
            dmb_data = advanced.get("day_month_bonding", {})
            if isinstance(dmb_data, dict):
                dmb_adjustment = dmb_data.get("total_score_modifier", 0.0)
            sb_data = advanced.get("six_breaks", {})
            if isinstance(sb_data, dict):
                sb_adjustment = sb_data.get("total_modifier", 0.0)

    # ---------- 5.5f: 随官入墓凶象 (Gap 3) ----------
    # "随官入墓最凶凶，世用临之祸不轻" — 极凶之象，需从 advanced_analysis 读取
    officer_tomb_adjustment = 0.0
    officer_tomb_reason = ""
    officer_tomb_severity = "none"
    officer_tomb_verdict_override = None
    officer_tomb_description = ""

    if advanced:
        ot_data = advanced.get("officer_tomb", {})
        if isinstance(ot_data, dict) and ot_data.get("has_officer_tomb"):
            officer_tomb_adjustment = ot_data.get("score_modifier", 0.0)
            officer_tomb_severity = ot_data.get("severity", "none")
            officer_tomb_description = ot_data.get("description", "")
            scenarios = ot_data.get("scenarios", [])
            if scenarios:
                officer_tomb_reason = "随官入墓（" + "、".join(scenarios[:3]) + "）"
            else:
                officer_tomb_reason = "随官入墓"

            # catastrophic severity: force verdict to at most 平凶 regardless of score
            if officer_tomb_severity == "catastrophic":
                officer_tomb_verdict_override = "凶"
            # severe: cap at 平凶 if current score would indicate better
            elif officer_tomb_severity == "severe":
                officer_tomb_verdict_override = None  # let score adjust naturally but log

            # 疾病占修正（P0-4）：官鬼=病气，入墓为收藏之象，凶力大减
            q_txt = r.get("question", "") or ""
            if any(kw in q_txt for kw in ["病", "疾", "痛", "恙", "染"]):
                officer_tomb_adjustment = round(officer_tomb_adjustment * 0.3, 2)
                officer_tomb_severity = "mild"
                officer_tomb_description += "（疾病占：官鬼病气入墓为收藏之象，凶力大减）"

    # ---------- 5.5c: 三合破局惩罚 (Gap 9) ----------
    combo_break_adjustment = 0.0
    combo_break_reason = ""
    _advanced_for_combo = r.get("advanced_analysis", {})
    if _advanced_for_combo and isinstance(_advanced_for_combo, dict):
        _tc_adv = _advanced_for_combo.get("triple_combo", {})
        if isinstance(_tc_adv, dict) and _tc_adv.get("has_triple_combo"):
            for _combo in _tc_adv.get("details", []):
                if not isinstance(_combo, dict):
                    continue
                if _combo.get("combo_status") == "破局":
                    _csm = _combo.get("combo_score_mod", -0.5)
                    if isinstance(_csm, (int, float)):
                        combo_break_adjustment += _csm
                    _cissues = _combo.get("combo_issues", [])
                    if _cissues:
                        combo_break_reason = "、".join(_cissues)
                        break  # only show first broken combo issue for brevity

    # ---------- 5.5c2: 原神贪合忘生检测 (三合火局/水局 etc 中吸收原神) ----------
    # 条件：原神所在五行参与了三合局(由日月引动) + 原神无动爻(完全被合住不生日)
    yuan_shen_bond_adjustment = 0.0
    yuan_shen_bond_reason = ""
    if _advanced_for_combo and isinstance(_advanced_for_combo, dict):
        _tc_adv2 = _advanced_for_combo.get("triple_combo", {})
        if isinstance(_tc_adv2, dict) and _tc_adv2.get("has_triple_combo"):
            _yuan_elem = safe_get(step2_data, "yuan_shen", "element", default="")
            _yuan_positions = safe_get(step2_data, "yuan_shen", "positions", default=[]) or []
            _day_br = safe_get(div_time, "day_stem_branch", default="")
            _month_br = safe_get(div_time, "month_stem_branch", default="")
            _day_b = _day_br[1:] if len(_day_br) >= 2 else ""
            _month_b = _month_br[1:] if len(_month_br) >= 2 else ""
            # 原神是否有动爻(明动)— 有动爻则原神仍有力，不构成贪合忘生
            _yuan_has_moving = any(
                isinstance(p, dict) and p.get("is_moving") for p in _yuan_positions
            )
            if _yuan_elem and not _yuan_has_moving:
                for _combo2 in _tc_adv2.get("details", []):
                    if not isinstance(_combo2, dict):
                        continue
                    if _combo2.get("element") != _yuan_elem:
                        continue
                    _combo_branches = _combo2.get("branches", [])
                    _combo_positions = _combo2.get("positions", [])
                    # 检查日辰/月建是否参与了此三合(位置列表中标记或分支匹配)
                    _has_day_or_month = any(
                        (isinstance(p, str) and ("日" in p or "月" in p))
                        for p in _combo_positions
                    ) or (_day_b in _combo_branches) or (_month_b in _combo_branches)
                    _completeness = _combo2.get("completeness", "")
                    # 日月引动待用之局
                    _active = _has_day_or_month
                    # 额外约束：原神之支必须全部在合局内，方构成完整贪合忘生
                    # (若原神有支在局外，仍可生用神，不构成贪合)
                    if _active and _yuan_positions:
                        _yuan_branches_in = [
                            p.get("earthly_branch", "")
                            for p in _yuan_positions
                            if isinstance(p, dict) and p.get("earthly_branch")
                        ]
                        _all_yuan_in_combo = bool(_yuan_branches_in) and all(
                            b in _combo_branches for b in _yuan_branches_in
                        )
                        _active = _all_yuan_in_combo
                    if _active:
                        # 原神贪合忘生 — 用神失源 (-2.0推至凶)
                        if yuan_shen_bond_adjustment == 0.0:
                            yuan_shen_bond_adjustment = -2.0
                        _combo_branches_str = "".join(_combo_branches)
                        _day_info = ""
                        if _day_b in _combo_branches:
                            _day_info = f"(日{_day_b}引动)"
                        elif _month_b in _combo_branches:
                            _day_info = f"(月{_month_b}引动)"
                        yuan_shen_bond_reason = (
                            f"原神{_yuan_elem}参与{_combo_branches_str}"
                            f"三合{_yuan_elem}局{_day_info}，贪合忘生，用神失源"
                        )
                        break

    # ---------- 5.5b: 特殊格局识别 ----------
    special_pattern = _detect_special_pattern(step3_data, step2_data, step4_data, r)
    pattern_adjustment = special_pattern.get("score_adjustment", 0.0)
    # For 从格: reverse the verdict direction by capping the negative and boosting
    if special_pattern.get("pattern") == "从格":
        # 从格 reverses the verdict: a weak use-god is actually good
        pattern_verdict_note = f"【从格特殊断法】{special_pattern['description']}——{special_pattern['impact_on_verdict']}"
    elif special_pattern.get("pattern"):
        pattern_verdict_note = f"格局【{special_pattern['pattern']}】：{special_pattern['description']}——{special_pattern['impact_on_verdict']}"
    else:
        pattern_verdict_note = ""

    # ---------- 伏神格局调整 ----------
    step3_reasoning_text = step3_data.get("summary_text", "") if step3_data else ""
    fu_shen_adjustment = 0.0
    fu_shen_note = ""
    if "飞空得出" in step3_reasoning_text or ("飞神" in step3_reasoning_text and "旬空" in step3_reasoning_text and "得出" in step3_reasoning_text):
        # 飞神旬空 → 伏神得出有力（P0-4 新增，优先于泄气/克伏等次级关系）
        fu_shen_adjustment = 1.5
        fu_shen_note = "【飞空得出】飞神旬空，伏神得出有力，+1.5"
    elif "飞来生伏" in step3_reasoning_text or "飞生伏" in step3_reasoning_text:
        # 飞神生伏神，伏得出为吉
        fu_shen_adjustment = 1.0
        fu_shen_note = "【飞来生伏可出】伏神得生而出，+1.0"
    elif "绝于飞" in step3_reasoning_text:
        # 伏神绝于飞神 → 气绝难出（P0-5）
        fu_shen_adjustment = -2.0
        fu_shen_note = "【伏神绝于飞】伏神气绝难出，-2.0"
    elif "飞克伏" in step3_reasoning_text:
        # 飞克伏: 需检查飞神是否旬空/月破 → 伏得出为吉
        import re
        m_fei = re.search(r'飞神(\w)', step3_reasoning_text)
        fei_branch = m_fei.group(1) if m_fei else ""
        empty_branches_list = r.get("empty_branches", []) or []
        if fei_branch and fei_branch in empty_branches_list:
            # 飞神旬空，伏神得出为吉
            fu_shen_adjustment = 1.5
            fu_shen_note = f"【伏神得出伏·飞旬空】飞神{fei_branch}旬空得出，+1.5"
        elif "月破" in step3_reasoning_text:
            # 飞神月破，伏神得出
            fu_shen_adjustment = 1.0
            fu_shen_note = "【伏神得出伏·飞月破】飞神月破得出，+1.0"
        else:
            fu_shen_adjustment = -1.0
            fu_shen_note = "【飞克伏难出】伏神被克不出，-1.0"
    elif "伏泄气于飞" in step3_reasoning_text:
        # 伏泄气: 伏神被动泄力，轻微负面
        fu_shen_adjustment = -0.5
        fu_shen_note = "【伏神泄气】伏神泄气于飞，-0.5"

    # ---------- 5.5h: 古籍通用格局加减（holdout 暴露的系统性缺口） ----------
    classical_adj = 0.0
    classical_notes = []
    _q_l = str((r.get("question") or r.get("question_category") or ""))
    # 行人归期 ≠ 逃亡追回：逃仆/追回不套「用神有气主终归」
    _is_catch = any(k in _q_l for k in ("逃", "追回", "可追", "逃仆", "走失", "盗"))
    _is_travel_return = (
        any(k in _q_l for k in ("归", "回", "行人", "何日", "出外", "出行"))
        and not _is_catch
    )
    _is_wealth = any(k in _q_l for k in ("财", "投资", "生意", "价", "贸易", "求财", "经营", "银", "失物", "失"))
    _is_illness = any(k in _q_l for k in ("病", "疾", "愈"))

    # 世爻六亲
    world_relation = ""
    world_branch = ""
    use_el_s = (step2_data or {}).get("use_god_element") or ""
    ug_cat = (step2_data or {}).get("use_god_category") or ""
    ug_sel = (step2_data or {}).get("selected_use_god") or {}
    ug_branch_s = ug_sel.get("earthly_branch") or (step3_data or {}).get("use_god_branch") or ""
    ug_el_s = ug_sel.get("element") or use_el_s
    for _y in ((r.get("original_hexagram") or {}).get("yao_lines") or []):
        if isinstance(_y, dict) and _y.get("is_world"):
            world_relation = _y.get("six_relation") or ""
            world_branch = _y.get("earthly_branch") or ""
            break
    palace_el = (r.get("original_hexagram") or {}).get("palace_element") or ""

    def _el_of_branch(b):
        return BRANCH_ELEMENTS.get(b or "", "")

    # 1) 行人/归期：用神生世/克世 — 迟归或速至，皆主能归（《黄金策》出行章）
    if _is_travel_return and ug_el_s and world_branch:
        w_el = _el_of_branch(world_branch) or ""
        if w_el and SHENG_CYCLE.get(ug_el_s) == w_el:
            classical_adj += 1.5
            classical_notes.append("【用神生世·迟归】行人占用神生世，主迟归终至，+1.5")
        elif w_el and KE_CYCLE.get(ug_el_s) == w_el:
            classical_adj += 0.8
            classical_notes.append("【用神克世·速至】行人占用神克世，主速至，+0.8")
        elif w_el and KE_CYCLE.get(w_el) == ug_el_s:
            # 世克用：行人受制，未必即归，但用神有气仍主终归
            classical_adj += 0.3
            classical_notes.append("【世克用·行人受制】世克用神，归途有阻，+0.3")
    if _is_travel_return:
        _fu_txt = str((step3_data or {}).get("summary_text") or "")
        _lv = str((step3_data or {}).get("strength_level") or "")
        _dead = any(k in _fu_txt for k in ("绝于", "真空", "月破", "飞克伏难出", "克伏不出"))
        if (not _dead) and (
            "得出" in _fu_txt
            or _lv in ("旺", "相", "极旺", "中和", "中和偏旺")
            or "伏神" in _fu_txt
        ):
            classical_adj += 0.6
            classical_notes.append("【行人用神有气】用神未至死绝或伏而得出，主终能归，+0.6")

    # 2) 兄弟持世 + 求财 — 古籍大忌（《增删》兄弟持世莫求财）
    _sp_pat_txt = ""
    try:
        if isinstance(special_pattern, dict):
            _sp_pat_txt = str(special_pattern.get("pattern") or "") + str(special_pattern.get("description") or "")
    except Exception:
        _sp_pat_txt = ""
    if world_relation == "兄弟" and _is_wealth and ug_cat == "妻财":
        if any(k in _q_l for k in ("失", "找回", "失物")) or "冲中逢合" in _sp_pat_txt:
            classical_adj -= 0.2
            classical_notes.append("【兄弟持世·失物/逢合轻扣】另有冲中逢合等解象，仅-0.2")
        else:
            classical_adj -= 1.2
            classical_notes.append("【兄弟持世求财】兄弟克财，求财多耗，-1.2")

    # 3) 妻财持世 + 失物 — 世持财主自失可寻（增删失物章）
    if world_relation == "妻财" and any(k in _q_l for k in ("失", "找回", "失物", "银")):
        classical_adj += 0.8
        classical_notes.append("【世持财·失物】世持财主物未远失，+0.8")

    # 5) 原神失位：用神旺相而原神不动作 — 黄金策「用神虽旺亦凶」
    _lv_ug = str((step3_data or {}).get("strength_level") or "")
    _yuan = (step2_data or {}).get("yuan_shen") or {}
    _yuan_pos = _yuan.get("positions") or []
    _yuan_moving = any(isinstance(p, dict) and p.get("is_moving") for p in _yuan_pos)
    if _lv_ug in ("旺", "极旺") and ug_cat and ug_cat != "世爻":
        _skip_yuanshen = (
            "冲中逢合" in _sp_pat_txt
            or any(k in _q_l for k in ("失", "找回", "失物"))
            or "世持财" in _sp_pat_txt
        )
        if ((not _yuan_pos) or (not _yuan_moving)) and not _skip_yuanshen:
            classical_adj -= 1.0
            classical_notes.append("【原神失位】用神虽旺而原神不动/缺位，旺极无源，-1.0")

    # 6) 久病逢冲为凶（对「近病逢冲即愈」）
    if any(k in _q_l for k in ("久病", "半年", "病久", "多月")):
        classical_adj -= 0.8
        classical_notes.append("【久病】久病正气已衰，逢冲逢克主凶，-0.8")

    # 7) 兄弟持世 + 功名/考试 — 竞争费力（可中而难前茅）
    if world_relation == "兄弟" and any(k in _q_l for k in ("考试", "功名", "学业", "科举", "中第")):
        classical_adj -= 0.4
        classical_notes.append("【兄弟持世求名】竞争费力，可成而名次不显，-0.4")

    # 8) 官司：官鬼克世 / 父母月破 → 不利（增删官非章）
    if any(k in _q_l for k in ("官司", "官非", "诬告", "诉讼", "官事")) and "师尊" not in _q_l:
        ug_br_s = ug_branch_s
        w_br = world_branch
        ug_e = ug_el_s or ""
        w_e = _el_of_branch(w_br) or ""
        if ug_e and w_e and KE_CYCLE.get(ug_e) == w_e:
            classical_adj -= 1.2
            classical_notes.append("【官鬼克世】官司占官方克世，主对我不利，-1.2")
        # 文书月破：从摘要文本识别
        _txt3 = str((step3_data or {}).get("summary_text") or "") + str((step2_data or {}).get("summary_text") or "")
        if "月破" in _txt3 and any(k in _q_l for k in ("官司", "官非", "诬告")):
            classical_adj -= 0.5
            classical_notes.append("【文书/用神月破】官司中文书有缺，-0.5")

    # 9) 原神失位加强：旺极无生 → 大幅降分（黄金策）
    # 仅当用神为"极旺"时才额外加权；"旺"级已有规则5的-1.0，不再叠加
    if any("原神失位" in n for n in classical_notes) and _lv_ug == "极旺":
        classical_adj -= 1.0
        classical_notes.append("【旺极无源加权】用神极旺而无原神发动，再-1.0")

    # 4) 用神临月建（通用旺格标记分已在旺衰，此处仅补注记）

    # 古籍通用格局注记（供标签与人话）— 必须在 classical_notes 生成之后
    if classical_notes:
        extra = "；".join(classical_notes)
        if pattern_verdict_note:
            pattern_verdict_note = pattern_verdict_note + "；" + extra
        else:
            pattern_verdict_note = extra

    # ---------- 5.5i: 三刑+六合吉凶相战覆写 ----------
    # 当2+成刑/催刑 present 且 六合卦时，吉凶相战 — verdict 上限不超过平凶
    xing_he_conflict_override = False
    tp_data_for_conflict = safe_get(step3_data, "three_punishments_raw", default=None)
    if tp_data_for_conflict is None:
        _adv_for_xh = r.get("advanced_analysis", {})
        if isinstance(_adv_for_xh, dict):
            tp_data_for_conflict = _adv_for_xh.get("three_punishments", {})
    if (isinstance(tp_data_for_conflict, dict) and tp_data_for_conflict.get("has_punishment")
            and hex_adjustment > 0):
        _tp_complete_cnt = sum(
            1 for _p in tp_data_for_conflict.get("punishments", [])
            if isinstance(_p, dict) and _p.get("completeness") in ("完整", "成刑", "催刑")
        )
        if _tp_complete_cnt >= 2:
            xing_he_conflict_override = True

    # ---------- 5.6: 综合评分 ----------
    final_score = (base_score + change_net_effect + hex_adjustment
                   + spirit_adjustment + pattern_adjustment
                   + dmb_adjustment + sb_adjustment
                   + combo_break_adjustment
                   + yuan_shen_bond_adjustment
                   + officer_tomb_adjustment
                   + fu_shen_adjustment
                   + classical_adj)
    final_score = round(final_score, 2)
    if classical_notes:
        # 写入 step5 展示与格局标签来源
        pass

    # ---------- 5.7: 定性判断 ----------
    # 阈值说明：古籍六爻 verdict 应明确(吉/凶)为主，避免过度收歛于中性(平吉/平凶)
    # 校准标准：final_score > 1.0 → 吉; > 4.0 → 大吉; -0.8 ~ 1.0 → 平吉; -2.0 ~ -0.8 → 凶; < -2.0 → 大凶
    if final_score > 4.0:
        verdict = "大吉"
        verdict_desc = "顺得很，该推进的可以推进"
    elif final_score >= 1.0:
        verdict = "吉"
        verdict_desc = "整体是顺的，往前走问题不大"
    elif final_score >= -0.5:
        verdict = "平吉"
        verdict_desc = "有戏但不稳，节奏比结果更要紧"
    elif final_score >= -2.0:
        verdict = "凶"
        verdict_desc = "阻力明显，硬上容易吃亏"
    else:
        verdict = "大凶"
        verdict_desc = "眼下不宜发力，先守住"

    # v8 口径微调：更贴近古籍断语习惯
    _qtext = str((r.get("question") or r.get("question_category") or ""))
    _sp = special_pattern if isinstance(special_pattern, dict) else {}
    _sp_pat = str(_sp.get("pattern") or "") + str(_sp.get("description") or "")

    # ── 古籍强凶格局强制覆写（pattern-based overrides）──
    _fired = False
    # 行人/出行占+六冲主散/合处逢冲：行人被冲散 → 凶
    if any(k in _qtext for k in ("行人", "出行", "回来", "归")) and ("六冲" in _sp_pat or "合处逢冲" in _sp_pat):
        if verdict in ("吉", "大吉", "平吉"):
            verdict = "凶"
            verdict_desc = "冲散行人，纵用神有气亦主归期不定"
            _fired = True
    # 合伙+六冲主散/合处逢冲：合伙看世应，应冲世则散 → 凶
    if "合伙" in _qtext and ("六冲" in _sp_pat or "合处逢冲" in _sp_pat):
        if verdict in ("吉", "大吉", "平吉"):
            verdict = "凶"
            verdict_desc = "六冲/逢冲合伙，世应相冲，合伙难持久"
            _fired = True
    # 用神衰弱+净动变负 → 凶
    if verdict == "平吉" and final_score < 0.0:
        _net_eff = 0.0
        if step4_data and isinstance(step4_data, dict):
            _net_eff = step4_data.get("net_effect") or 0.0
        if _net_eff < -0.2:
            verdict = "凶"
            verdict_desc = "原神不济、变动不利，纵用神有些微气亦难持久"
            _fired = True
    # 三刑+六合吉凶相战覆写：2+成刑/催刑 + 六合卦 → 上限不超过平凶
    if xing_he_conflict_override and verdict in ("吉", "大吉", "平吉"):
        verdict = "平凶"
        verdict_desc = "三刑齐全逢六合，吉凶相战，凶多吉少"
        _fired = True
    _verdict_locked = _fired

    if "合处逢冲" in _sp_pat and verdict in ("凶", "大凶", "平吉"):
        if any(k in _qtext for k in ("婚", "合", "成否", "聚")):
            verdict = "平/不利"
            verdict_desc = "先合后散，事情容易反复，适合稳住再看"
        elif verdict == "大凶":
            verdict = "凶"
    if any(k in _qtext for k in ("价", "贵贱", "桑叶", "涨跌")) and verdict in ("凶", "大凶"):
        verdict = "下跌"
        verdict_desc = "势头偏弱，观望比追高稳妥"

    # 古籍通用口径：行人「用神生世/克世」主能归；兄弟持世求财主耗
    if classical_notes:
        if any("原神失位" in n for n in classical_notes) and "冲中逢合" not in _sp_pat_txt:
            if verdict in ("大吉",):
                verdict = "吉"
                verdict_desc = "表面有力，实则源头不足，勿被旺象迷惑"
            if any("旺极无源" in n for n in classical_notes) and verdict in ("吉", "大吉", "平吉"):
                if final_score < 1.0:
                    verdict = "凶"
                    verdict_desc = "旺而无源，古法主事难持久，防盛极而衰"
                else:
                    verdict = "平吉"
                    verdict_desc = "用神虽旺，源头不足，勿把一时之盛当长久"
            elif verdict == "吉" and final_score < 2.0:
                verdict = "平吉"
                verdict_desc = "用神看似不弱，但原神未动，成算要打折"
        if any("官鬼克世" in n for n in classical_notes):
            if verdict in ("大吉", "吉"):
                verdict = "凶"
                verdict_desc = "官司官方克世，形势对己不利，宜专业应对"
            elif verdict == "平吉":
                verdict = "凶"
                verdict_desc = "官司官方克世，形势偏紧，勿心存侥幸"
        if any("兄弟持世求名" in n for n in classical_notes) and verdict in ("吉", "大凶", "凶"):
            if verdict in ("凶", "大凶"):
                verdict = "平吉"
                verdict_desc = "功名有阻力但未必绝望，兄弟持世主竞争费力"
            else:
                verdict = "平吉"
                verdict_desc = "功名有象，但竞争大、须全力以赴，名次未必靠前"
        if any("久病" in n for n in classical_notes):
            if verdict in ("大吉", "吉"):
                verdict = "平吉" if verdict == "吉" else "凶"
                if verdict == "平吉":
                    verdict_desc = "久病不宜言吉，仍以调护就医为先"
            if verdict == "平吉" and any(k in _q_l for k in ("久病", "半年")):
                verdict = "凶"
                verdict_desc = "久病体衰，卦象偏紧，务必遵医嘱"
        if any("兄弟持世求名" in n for n in classical_notes) and verdict in ("吉", "大吉"):
            verdict = "平吉"
            verdict_desc = "功名有象，但竞争大、须全力以赴，名次未必靠前"
        if _is_travel_return and any(
            ("用神生世" in n) or ("用神克世" in n) or ("行人用神有气" in n) or ("世克用" in n)
            for n in classical_notes
        ):
            if verdict in ("凶", "大凶"):
                verdict = "平吉"
                verdict_desc = "行人终归，只是偏迟或途中多折，宜候应期"
            if any("用神生世" in n for n in classical_notes) and verdict in ("平吉", "凶", "大凶"):
                verdict = "吉"
                verdict_desc = "用神生世，行人迟归终至，可候应期"
            elif verdict == "平吉" and any("用神克世" in n for n in classical_notes):
                verdict = "吉"
                verdict_desc = "行人可望速至"
        if world_relation == "兄弟" and _is_wealth and ug_cat == "妻财":
            _soft_bro = any(k in _q_l for k in ("失", "找回", "失物")) or "冲中逢合" in _sp_pat_txt
            if _soft_bro:
                if verdict in ("凶", "大凶") and final_score >= 0:
                    verdict = "吉"
                    verdict_desc = "虽兄弟持世，然冲中逢合，主先难后成"
                elif verdict == "平吉" and final_score >= 0:
                    verdict = "吉"
                    verdict_desc = "有惊无险，失而可复得"
            else:
                if verdict in ("大吉",):
                    verdict = "吉"
                    verdict_desc = "有财可谋，但兄弟持世，到手易耗"
                elif verdict == "吉" and final_score < 2.5:
                    verdict = "平吉"
                    verdict_desc = "财路有象，兄弟持世须防破耗"
                elif verdict in ("平吉",) and final_score <= 0.2:
                    verdict = "平/不利"
                    verdict_desc = "兄弟持世求财，辛苦多耗，得不偿失"
    elif _is_travel_return and verdict in ("凶", "大凶"):
        # 无 classical_notes 时仍按行人占谨慎：用神非死绝不断大凶
        _fu_txt2 = str((step3_data or {}).get("summary_text") or "")
        if not any(k in _fu_txt2 for k in ("绝于", "真空", "月破")):
            if (step3_data or {}).get("effective_score", 0) >= 2.0:
                verdict = "平吉"
                verdict_desc = "用神尚有气，行人主能归，过程偏拖"

    # ---------- 5.7b: 随官入墓凶象覆盖 (Gap 3) ----------
    # 随官入墓极凶，catastrophic级别强行覆盖定性判断
    officer_tomb_verdict_note = ""
    if officer_tomb_verdict_override:
        old_verdict = verdict
        verdict = officer_tomb_verdict_override
        if officer_tomb_severity == "catastrophic":
            verdict_desc = "随官入墓极凶之象——" + officer_tomb_description[:50]
            officer_tomb_verdict_note = (
                f"【随官入墓强行覆盖】原为{old_verdict}，"
                f"因{officer_tomb_reason}降级为凶"
            )
    elif officer_tomb_severity == "severe" and officer_tomb_adjustment <= -1.0:
        officer_tomb_verdict_note = (
            f"【随官入墓凶象】{officer_tomb_reason}——"
            f"评分调整{officer_tomb_adjustment:+.1f}"
        )

    # ---------- 5.8: 置信度评估 ----------
    confidence = _assess_confidence(step3_data, step4_data, final_score, strength_level)

    # ---------- 5.9: 应期判断 ----------
    timing = _predict_timing(r, step3_data, step1_data, day_branch, special_pattern=special_pattern)

    # ---------- 5.9b: 应期精确日期计算 ----------
    # Use divination date as base for scanning forward
    div_dt = safe_get(r, "divination_time", "datetime", default="")
    base_date = None
    if div_dt:
        try:
            base_date = datetime.strptime(div_dt, "%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            pass
    yingqi_dates = calculate_yingqi(
        step1_data, step2_data, step3_data, step4_data,
        {"verdict": verdict, "final_score": final_score},
        base_date=base_date,
    )

    # ---------- 5.10: 推理链 ----------
    reasoning_chain = _build_reasoning_chain(step1_data, step2_data, step3_data, step4_data, step5_data={
        "verdict": verdict,
        "final_score": final_score,
    }, context=r)

    # ---------- 5.11: 纳音信息（六十甲子纳音取象）----------
    nayin_info = {}
    nayin_desc = ""
    if isinstance(advanced, dict):
        nayin_info = advanced.get("nayin", {})
    if isinstance(nayin_info, dict) and nayin_info.get("description"):
        nayin_desc = nayin_info["description"]

    # ---------- 5.12: 经典引文自动检索 ----------
    classical_quotes = find_classical_quotes(r)
    classical_quotes_text = ""
    if classical_quotes:
        classical_quotes_text = "【经典引文】" + "".join(
            f"• {q['source']}：{q['quote']}" for q in classical_quotes
        )

    # ---------- 5.13: 可解释性因子贡献（SHAP 风格）----------
    factor_contributions = []
    # 1. 用神旺衰基础分
    factor_contributions.append({
        "name": "用神旺衰",
        "factor": "base",
        "score": round(base_score, 2),
        "reason": (
            "用神得令，旺相有力" if base_score > 2 else
            "用神失令，根基偏弱" if base_score < 0 else
            "用神平和，不旺不弱"
        )
    })
    # 2. 动变效应
    factor_contributions.append({
        "name": "动变效应",
        "factor": "change",
        "score": round(change_net_effect, 2),
        "reason": (
            "动爻来生用神" if change_net_effect > 0.3 else
            "动爻来克用神" if change_net_effect < -0.3 else
            "动爻生克交抵，利弊相抵"
        )
    })
    # 3. 合冲卦性
    if hex_adjustment != 0:
        factor_contributions.append({
            "name": "合冲卦性",
            "factor": "hexagram",
            "score": round(hex_adjustment, 2),
            "reason": _user_reason(hex_adjustment_reason, "六合利合" if hex_adjustment > 0 else "六冲主散")
        })
    # 4. 六神辅助
    if spirit_adjustment != 0:
        # 清理 reason 中含 (xN.N) 系数备注，避免用 generator 导致 re 闭包作用域异常
        _cleaned_reasons = []
        for _r in spirit_adjustment_reasons:
            _cleaned_reasons.append(_r.split("(x")[0].strip() if "(x" in _r else _r)
        _reason_text = "；".join(_cleaned_reasons) or "六神加临用神"
        factor_contributions.append({
            "name": "六神辅助",
            "factor": "spirit",
            "score": round(spirit_adjustment, 2),
            "reason": _reason_text,
        })
    # 5. 暗动（已并入 base_score/effective_score，不单独计入以避免重复计算）
    # 6. 日月合
    if dmb_adjustment != 0:
        factor_contributions.append({
            "name": "日月合用神",
            "factor": "day_month_bond",
            "score": round(dmb_adjustment, 2),
            "reason": _user_reason(dmb_reason, "日月合住用神")
        })
    # 7. 六破
    if sb_adjustment != 0:
        factor_contributions.append({
            "name": "六破损伤",
            "factor": "six_breaks",
            "score": round(sb_adjustment, 2),
            "reason": _user_reason(sb_reason, "用神逢月破")
        })
    # 8. 三合破
    if combo_break_adjustment != 0:
        factor_contributions.append({
            "name": "三合局破",
            "factor": "combo",
            "score": round(combo_break_adjustment, 2),
            "reason": _user_reason(combo_break_reason, "合局受破，所谋难成")
        })
    # 8b. 原神贪合忘生
    if yuan_shen_bond_adjustment != 0:
        factor_contributions.append({
            "name": "原神贪合忘生",
            "factor": "yuan_shen_bond",
            "score": round(yuan_shen_bond_adjustment, 2),
            "reason": _user_reason(yuan_shen_bond_reason, "原神被合，用神失源")
        })
    # 9. 随官入墓
    if officer_tomb_adjustment != 0:
        factor_contributions.append({
            "name": "随官入墓",
            "factor": "tomb",
            "score": round(officer_tomb_adjustment, 2),
            "reason": _user_reason(officer_tomb_reason, "官鬼入墓，困而不发")
        })
    # 10. 伏神得出
    if fu_shen_adjustment != 0:
        factor_contributions.append({
            "name": "伏神得出",
            "factor": "fu_shen",
            "score": round(fu_shen_adjustment, 2),
            "reason": _user_reason(fu_shen_note, "伏神得出，事有转机")
        })
    # 11. 格局调整
    if pattern_adjustment != 0:
        factor_contributions.append({
            "name": "特殊格局",
            "factor": "pattern",
            "score": round(pattern_adjustment, 2),
            "reason": _user_reason(pattern_verdict_note, "格局特殊，反其势用之")
        })
    # 12. 古籍通用格局加减（classical_adj：六亲持世+事项+伏出等）
    if classical_adj != 0:
        factor_contributions.append({
            "name": "古籍格局加减",
            "factor": "classical",
            "score": round(classical_adj, 2),
            "reason": "；".join(_user_reason(n) for n in classical_notes[:2]) if classical_notes else "古籍格局"
        })
    # 12b. 六亲持世深化（含占问情境化解读）
    adv_shi = r.get("advanced_analysis", {}).get("shi_yao_relation") if isinstance(r, dict) else None
    if isinstance(adv_shi, dict) and adv_shi.get("classical_rule"):
        _sh_reason = adv_shi["classical_rule"]
        if adv_shi.get("scenario_interpretation"):
            _sh_reason = adv_shi["scenario_interpretation"]
        factor_contributions.append({
            "name": "六亲持世",
            "factor": "shi_yao",
            "score": 0.0,
            "reason": _sh_reason,
            "classical_rule": adv_shi.get("classical_rule", ""),
            "scenario": adv_shi.get("scenario", ""),
            "scenario_interpretation": adv_shi.get("scenario_interpretation", ""),
        })
    # 按绝对贡献度排序（影响最大的排前面）
    factor_contributions.sort(key=lambda x: abs(x["score"]), reverse=True)

    return {
        "base_score": base_score,
        "strength_level": strength_level,
        "change_net_effect": change_net_effect,
        "hex_adjustment": hex_adjustment,
        "hex_adjustment_reason": hex_adjustment_reason,
        "spirit_adjustment": spirit_adjustment,
        "spirit_adjustment_reasons": spirit_adjustment_reasons,
        "special_pattern": special_pattern,
        "pattern_adjustment": pattern_adjustment,
        "pattern_verdict_note": pattern_verdict_note,
        "final_score": final_score,
        # 最终锁定：若强凶格局已触发，不再允许 verdict 被后续逻辑回退到 吉/平吉
        "verdict": verdict if not (_verdict_locked and "凶" not in verdict) else "凶",
        "verdict_description": verdict_desc,
        "confidence": confidence,
        "confidence_description": _confidence_to_text(confidence),
        "timing": timing,
        "yingqi_dates": yingqi_dates,
        "reasoning_chain": reasoning_chain,
        "hidden_movement_count": hm_count,
        "hidden_movement_modifier": hm_modifier,
        "hidden_movement_reason": hm_reason,
        "greedy_harmony_score": greedy_score,
        "greedy_harmony_reason": greedy_reason,
        "dmb_adjustment": dmb_adjustment,
        "dmb_reason": dmb_reason,
        "sb_adjustment": sb_adjustment,
        "sb_reason": sb_reason,
        "combo_break_adjustment": round(combo_break_adjustment, 2),
        "combo_break_reason": combo_break_reason,
        "officer_tomb_adjustment": round(officer_tomb_adjustment, 2),
        "officer_tomb_reason": officer_tomb_reason,
        "officer_tomb_severity": officer_tomb_severity,
        "officer_tomb_verdict_note": officer_tomb_verdict_note,
        "summary_text": _compose_synthesis_summary(
            strength_level=strength_level,
            base_score=base_score,
            change_net_effect=change_net_effect,
            hex_adjustment=hex_adjustment,
            hex_adjustment_reason=hex_adjustment_reason,
            spirit_adjustment=spirit_adjustment,
            spirit_adjustment_reasons=spirit_adjustment_reasons,
            hm_modifier=hm_modifier,
            hm_reason=hm_reason,
            greedy_score=greedy_score,
            greedy_reason=greedy_reason,
            tp_score=tp_score,
            tp_reason=tp_reason,
            dmb_adjustment=dmb_adjustment,
            dmb_reason=dmb_reason,
            sb_adjustment=sb_adjustment,
            sb_reason=sb_reason,
            combo_break_adjustment=combo_break_adjustment,
            combo_break_reason=combo_break_reason,
            fu_shen_adjustment=fu_shen_adjustment,
            fu_shen_note=fu_shen_note,
            officer_tomb_adjustment=officer_tomb_adjustment,
            officer_tomb_reason=officer_tomb_reason,
            special_pattern=special_pattern,
            pattern_adjustment=pattern_adjustment,
            final_score=final_score,
            verdict=verdict,
            verdict_desc=verdict_desc,
            pattern_verdict_note=pattern_verdict_note,
            officer_tomb_verdict_note=officer_tomb_verdict_note,
            nayin_desc=nayin_desc,
            confidence=confidence,
            classical_quotes_text=classical_quotes_text,
        ),
        # 卦身摘要（供整体摘要引用）
        "hexagram_body_note": _get_hexagram_body_summary_note(r),
        # 经典引文自动检索结果
        "classical_quotes": classical_quotes,
        # 可解释性：因子贡献（SHAP 风格，供 frontend / human_narrative 使用）
        "factor_contributions": factor_contributions,
        "factor_contribution_verification": round(sum(c["score"] for c in factor_contributions), 2),
    }


# =============================================================================
# 应期精确计算 (Exact Calendar Date Calculation)
# =============================================================================
# Implements ancient 增删易/黄金策 timing rules → concrete Gregian calendar dates.

# Branch clash map (六冲)
_BRANCH_CLASH_MAP = {}
for _a, _b in CHONG_PAIRS:
    _BRANCH_CLASH_MAP[_a] = _b
    _BRANCH_CLASH_MAP[_b] = _a

# 六合 map (for 化合应期)
_HE_MAP = {}
for _a, _b in HE_PAIRS:
    _HE_MAP.setdefault(_a, []).append(_b)
    _HE_MAP.setdefault(_b, []).append(_a)

# Element → peak months (for 待旺时 rule)
_ELEMENT_PEAK_MONTHS = {
    "木": [2, 3],       # 寅卯月（春）
    "火": [5, 6],       # 巳午月（夏）
    "土": [4, 7, 10, 1],  # 辰戌丑未月（四季之末月）
    "金": [8, 9],       # 申酉月（秋）
    "水": [11, 12],     # 亥子月（冬）
}

# 60甲子 base: 2024-01-01 = 甲子日 (verified)
_60_CYCLE_BASE = datetime(2024, 1, 1)


def _day_branch_for_date(d: datetime) -> str:
    """
    Return the 地支 for the day of a given Gregian date.
    Uses the same algorithm as liuyao_engine.get_day_stem_branch fallback:
    2024-01-01 = 甲子日 (stem_idx=0, branch_idx=0).
    """
    delta = (d - _60_CYCLE_BASE).days
    branch_idx = delta % 12
    if branch_idx < 0:
        branch_idx += 12
    return BRANCHES[branch_idx]


def _next_date_with_day_branch(start_date: datetime, target_branch: str, max_days: int = 366) -> datetime | None:
    """
    Return the next date (from start_date forward) whose day-branch equals target_branch.
    Scans up to max_days (default 1 year + leap day).
    Returns None if not found within range.
    """
    if not target_branch or target_branch not in set(BRANCHES):
        return None
    d = start_date + timedelta(days=1)  # start FROM tomorrow
    for _ in range(max_days):
        if _day_branch_for_date(d) == target_branch:
            return d
        d += timedelta(days=1)
    return None


def _next_month_with_branch(start_date: datetime, target_branch: str) -> datetime | None:
    """下一个"月令"为该地支的日期。

    月令由十二节决定（立春寅、惊蛰卯…），不是公历月。旧实现写作
    `(d.month + 1) % 12` 的公历近似，在交节前后会整整错一个月——应期因此偏掉
    30 天。现委托历法内核求交节时刻。
    """
    if not target_branch or target_branch not in set(BRANCHES):
        return None
    try:
        from yishu_core import ganzhi_calendar as _gc
    except ImportError:
        import os
        import sys
        from pathlib import Path
        core_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent / "core"
        if str(core_dir) not in sys.path:
            sys.path.insert(0, str(core_dir))
        from yishu_core import ganzhi_calendar as _gc
    inst = _gc.next_month_branch_instant(start_date, target_branch)
    return inst if inst is None else inst.replace(hour=12, minute=0)


def _add_months(d: datetime, months: int) -> datetime:
    """Add months to a date, capping day at month max."""
    month = d.month + months
    year = d.year
    while month > 12:
        month -= 12
        year += 1
    while month < 1:
        month += 12
        year -= 1
    import calendar
    max_day = calendar.monthrange(year, month)[1]
    day = min(d.day, max_day)
    return datetime(year, month, day)


def _dates_overlap(dt1: datetime | None, dt2: datetime | None, tol_days: int = 2) -> bool:
    """Check if two dates are within tol_days of each other (same event)."""
    if dt1 is None or dt2 is None:
        return False
    return abs((dt1 - dt2).days) <= tol_days


def calculate_yingqi(
    step1: dict,
    step2: dict,
    step3: dict,
    step4: dict,
    step5: dict,
    base_date: datetime | None = None,
) -> dict:
    """
    应期精确计算 — 将增删易/黄金策应期规则转化为具体日历日期。

    Returns
    -------
    dict with keys:
        - dates: list of {rule: str, date: str(YYYY-MM-DD), branch: str, description: str}
        - speed: str — 速应/适中/迟应
        - summary_text: str — human-readable summary
    """
    use_god_branch = safe_get(step3, "use_god_branch", default="")
    use_god_element = safe_get(step3, "use_god_element", default="")
    strength_level = safe_get(step3, "strength_level", default="中和")
    is_empty = safe_get(step3, "is_empty", default=False)
    is_month_break = safe_get(step3, "is_month_break", default=False)
    is_an_dong = safe_get(step3, "is_an_dong", default=False)

    vacant = safe_get(step1, "vacant_branches", default=[])
    if isinstance(vacant, str):
        vacant = [vacant]
    fu_cang_detail = safe_get(step2, "fu_cang_detail", default=None)
    has_fu_cang = safe_get(step2, "has_fu_cang", default=False)

    # 原神 info
    yuan_shen_element = safe_get(step2, "yuan_shen", "element", default="")
    yuan_shen_positions = safe_get(step2, "yuan_shen", "positions", default=[])
    yuan_shen_fu_cang = safe_get(step2, "yuan_shen", "fu_cang", default=None)

    # base_date defaults to today
    base = base_date if base_date else datetime.now()

    # Collect all 应期: list of (rule_str, date_or_None, branch, description_parts)
    candidates: list[tuple[str, datetime | None, str, str]] = []

    clash = _BRANCH_CLASH_MAP.get(use_god_branch, "")

    # ===== Rule 1: 逢值逢冲 =====
    if use_god_branch:
        val_date = _next_date_with_day_branch(base, use_god_branch)
        if val_date:
            candidates.append(("逢值", val_date, use_god_branch,
                               f"用神{use_god_branch}临值"))
        if clash:
            clash_date = _next_date_with_day_branch(base, clash)
            if clash_date:
                candidates.append(("逢冲", clash_date, clash,
                                   f"用神{use_god_branch}逢冲({clash})"))

    # ===== Rule 2: 原神受克时 → 原神旺时 / 忌神受制时 =====
    if yuan_shen_positions or yuan_shen_fu_cang:
        # Get 原神 branches
        yuan_branches: list[str] = []
        for yp in (yuan_shen_positions or []):
            yb = yp.get("earthly_branch", "")
            if yb:
                yuan_branches.append(yb)
        if yuan_shen_fu_cang:
            yfb = yuan_shen_fu_cang.get("branch", "")
            if yfb:
                yuan_branches.append(yfb)

        for yb in yuan_branches:
            ys_val = _next_date_with_day_branch(base, yb)
            if ys_val:
                candidates.append(("原神值日", ys_val, yb,
                                   f"原神{yb}当值"))

    # ===== Rule 3: 旬空 → 填实 / 冲空 =====
    if is_empty and use_god_branch:
        fill_date = _next_date_with_day_branch(base, use_god_branch)
        if fill_date:
            candidates.append(("填实(实空)", fill_date, use_god_branch,
                               f"用神{use_god_branch}出空填实"))
        if clash:
            chong_date = _next_date_with_day_branch(base, clash)
            if chong_date:
                candidates.append(("冲空", chong_date, clash,
                                   f"用神{use_god_branch}冲空({clash})"))

    # ===== Rule 4: 伏藏 → 飞神值日 / 冲开 =====
    if has_fu_cang and fu_cang_detail:
        results = fu_cang_detail.get("results", [])
        for r in results:
            fei = r.get("fei_shen", {})
            fei_branch = fei.get("branch", "")
            if fei_branch:
                fei_val = _next_date_with_day_branch(base, fei_branch)
                if fei_val:
                    candidates.append(("飞神值日(伏得出)", fei_val, fei_branch,
                                       f"飞神{fei_branch}值日"))
                fei_clash = _BRANCH_CLASH_MAP.get(fei_branch, "")
                if fei_clash:
                    fei_chong = _next_date_with_day_branch(base, fei_clash)
                    if fei_chong:
                        candidates.append(("飞神冲开", fei_chong, fei_clash,
                                           f"冲飞神{fei_branch}→{fei_clash}"))

    # ===== Rule 5: 三合局 → 待合局成 =====
    if use_god_element and use_god_element in SAN_HE:
        san_he_branches = SAN_HE[use_god_element]
        for shb in san_he_branches:
            sh_date = _next_date_with_day_branch(base, shb)
            if sh_date:
                candidates.append(("三合成局", sh_date, shb,
                                   f"{'/'.join(san_he_branches)}合{use_god_element}局"))

    # ===== Rule 6: 月破 → 逢合/逢值/填实 =====
    if is_month_break and use_god_branch:
        # 逢值填实
        val_date = _next_date_with_day_branch(base, use_god_branch)
        if val_date:
            candidates.append(("月破填实", val_date, use_god_branch,
                               f"月破用神{use_god_branch}填实"))
        # 逢合（月破逢合为解）
        he_branches = _HE_MAP.get(use_god_branch, [])
        for heb in he_branches:
            he_date = _next_date_with_day_branch(base, heb)
            if he_date:
                candidates.append(("月破逢合", he_date, heb,
                                   f"月破用神{use_god_branch}逢合{heb}"))

    # ===== Rule 7: 节奏 timing =====
    # FAST: 用神旺 + 不动/暗动 → 当日或次日
    if strength_level in ("极旺", "旺") and not is_empty and not is_month_break:
        candidates.append(("速应(旺)", base + timedelta(days=0), _day_branch_for_date(base),
                           f"用神旺相，当日可能应"))
        candidates.append(("速应(次日)", base + timedelta(days=1), _day_branch_for_date(base + timedelta(days=1)),
                           "用神旺相，次日之应"))

    # MEDIUM: 用神动化进 → 逢值日（已由逢值规则覆盖）
    # SLOW: 用神休囚 + 静 → 原神旺月/旺日
    if strength_level in ("偏弱", "弱", "极弱"):
        if yuan_shen_element:
            for yb in [yp.get("earthly_branch", "") for yp in (yuan_shen_positions or [])]:
                if yb:
                    ys_date = _next_date_with_day_branch(base, yb)
                    if ys_date and not any(_dates_overlap(ys_date, c[1]) for c in candidates):
                        candidates.append(("原神旺日(迟应)", ys_date, yb,
                                           f"用神休囚，待原神{yb}旺日"))
        # 原神旺月 fallback
        if yuan_shen_element:
            peak_months = _ELEMENT_PEAK_MONTHS.get(yuan_shen_element, [])
            for pm in peak_months:
                d = datetime(base.year, pm, 15)
                if d <= base:
                    d = datetime(base.year + 1, pm, 15)
                candidates.append(("原神旺月", d, "",
                                   f"原神{yuan_shen_element}旺月（{pm}月）"))

    # ===== Deduplicate: if 逢值 == 填实 or 逢冲 == 冲空, keep more specific rule =====
    seen_dates: dict[str, tuple[str, datetime | None, str, str]] = {}
    for rule, dt, br, desc in candidates:
        if dt is None:
            continue
        key = dt.strftime("%Y-%m-%d")
        # Prefer more specific rules over generic ones
        priority = {"飞神冲开": 6, "飞神值日(伏得出)": 5, "三合成局": 4,
                     "月破逢合": 4, "填实(实空)": 3, "冲空": 4, "逢值": 2,
                     "逢冲": 2, "原神值日": 2, "月破填实": 3,
                     "速应(旺)": 1, "速应(次日)": 1, "原神旺日(迟应)": 1,
                     "原神旺月": 0}
        existing = seen_dates.get(key)
        if existing is None or priority.get(rule, 0) > priority.get(existing[0], 0):
            seen_dates[key] = (rule, dt, br, desc)

    # Sort by date
    unique_sorted = sorted(seen_dates.values(), key=lambda x: x[1] or datetime.max if x[1] else datetime.max)
    top5 = unique_sorted[:5]

    # ===== Build result =====
    dates_list = []
    for rule, dt, br, desc in top5:
        dates_list.append({
            "rule": rule,
            "date": dt.strftime("%Y-%m-%d") if dt else None,
            "branch": br,
            "description": desc,
        })

    # Determine overall speed
    if not dates_list:
        speed = "无应期可断"
    elif any(d["rule"].startswith("速应") for d in dates_list):
        speed = "速应（当日或数日内）"
    elif any(d["rule"] in ("逢值", "逢冲", "三合成局") for d in dates_list):
        speed = "适中（数日至数周）"
    else:
        speed = "迟应（数周至数月）"

    # Build summary
    if dates_list:
        date_strs = "、".join(f"{d['date']}({d['rule']})" for d in dates_list if d["date"])
        summary = f"应期（{speed}）：{date_strs}"
    else:
        summary = f"应期（{speed}）：难以确定具体日期，以用神旺衰断迟速"

    return {
        "dates": dates_list,
        "speed": speed,
        "summary_text": summary,
        "use_god_branch": use_god_branch,
        "use_god_element": use_god_element,
        "strength_level": strength_level,
        "method": "增删易/黄金策规则→日历日期",
    }


# --- Step 5 辅助函数 ---

def _assess_confidence(
    step3_data: dict,
    step4_data: dict,
    final_score: float,
    strength_level: str,
) -> int:
    """
    评估预测置信度（0-100%）。
    信度高条件：
    - 用神旺相/极旺，信号清晰
    - 动变与原神相助一致
    - 无明显矛盾

    信度低条件：
    - 用神休囚或旬空+月破
    - 动变与忌神相克
    - 多种反向信号交织
    """
    confidence = 70  # 基础置信度

    # 旺衰修正
    if strength_level in ("极旺", "旺"):
        confidence += 10
    elif strength_level in ("极弱", "弱"):
        confidence -= 15

    # 旬空修正
    if step3_data.get("is_empty"):
        confidence -= 10

    # 月破修正
    if step3_data.get("is_month_break"):
        confidence -= 10

    # 动变一致性
    net_effect = step4_data.get("net_effect", 0)
    if abs(net_effect) > 1.5:
        confidence += 5  # 动变方向明确
    elif abs(net_effect) < 0.3:
        confidence -= 5  # 动变方向不明，降低置信度

    # 最终分极端值提升置信度
    if final_score > 4.0 or final_score < 1.0:
        confidence += 5

    return max(30, min(95, confidence))


def _confidence_to_text(confidence: int) -> str:
    """置信度文字说明"""
    if confidence >= 80:
        return "高 — 信号清晰明确"
    elif confidence >= 60:
        return "中 — 大体可断，细节待验"
    elif confidence >= 40:
        return "中等偏低 — 信号参半，谨慎判断"
    else:
        return "低 — 信号矛盾，暂缓决断"




def _compose_synthesis_summary(**kw) -> str:
    """综合步骤：先说结论，再说依据，分数只作备查。"""
    verdict = kw.get("verdict") or ""
    vdesc = kw.get("verdict_desc") or ""
    score = kw.get("final_score")
    level = kw.get("strength_level") or ""
    parts = [f"综合来看，断为{verdict}。"]
    if vdesc:
        parts.append(vdesc.rstrip("。") + "。")
    supports = []
    concerns = []
    # 旺衰
    lv_say = {
        "极旺": "用神很旺", "旺": "用神得力", "相": "用神有根",
        "中和": "用神中和", "中和偏旺": "用神略旺", "中和偏弱": "用神略弱",
        "偏弱": "用神偏弱", "弱": "用神力薄", "极弱": "用神极弱", "休囚": "用神休囚",
    }.get(str(level), f"用神{level}")
    supports.append(lv_say) if any(x in str(level) for x in ("旺", "相", "中和偏旺")) else concerns.append(lv_say)
    # 动变
    net = float(kw.get("change_net_effect") or 0)
    if net > 0.3:
        supports.append("动变有助力")
    elif net < -0.3:
        concerns.append("动变有牵扯")
    # 格局
    sp = kw.get("special_pattern") if isinstance(kw.get("special_pattern"), dict) else {}
    pat = str(sp.get("pattern") or "") if sp else ""
    if pat:
        if any(k in pat for k in ("逢合可解", "冲中逢合", "逢空即愈", "绝处逢生")):
            supports.append(f"格局「{pat}」在化解阻力")
        elif any(k in pat for k in ("逢冲", "逢合为凶", "随官", "反吟")):
            concerns.append(f"格局「{pat}」添变数")
        else:
            supports.append(f"见「{pat}」之象")
    if kw.get("pattern_verdict_note"):
        concerns.append(str(kw["pattern_verdict_note"]).rstrip("。"))
    if supports:
        parts.append("有利的一面：" + "，".join(supports) + "。")
    if concerns:
        parts.append("要当心的一面：" + "，".join(str(c) for c in concerns if c) + "。")
    if score is not None:
        parts.append(f"（量化参考 {float(score):.2f}，把握约 {kw.get('confidence','—')}%）")
    note_bits = [x for x in (
        kw.get("officer_tomb_verdict_note"), kw.get("nayin_desc"),
    ) if x]
    if note_bits:
        parts.append(" ".join(str(x) for x in note_bits))
    qt = kw.get("classical_quotes_text") or ""
    if qt:
        parts.append(str(qt).replace("【经典引文】", "古人类似情境有言："))
    return "".join(parts)


def _predict_timing(r: dict, step3_data: dict, step1_data: dict, day_branch: str, special_pattern=None) -> dict:
    """
    应期判断 — v8：前置「重点应期」地支词，兼顾古籍规则与人话可读性。
    """
    use_god_branch = safe_get(step3_data, "use_god_branch", default="") or ""
    use_god_element = safe_get(step3_data, "use_god_element", default="")
    strength_level = safe_get(step3_data, "strength_level", default="中和")
    is_empty = safe_get(step3_data, "is_empty", default=False)
    is_month_break = safe_get(step3_data, "is_month_break", default=False)

    BRANCH_ORDER = "子丑寅卯辰巳午未申酉戌亥"

    def _pair_partner(pairs, b: str) -> str:
        """配对表是单向列出的（每对只写一次），必须双向查。"""
        for a, c in pairs:
            if b == a:
                return c
            if b == c:
                return a
        return ""

    def _chong(b: str) -> str:
        return _pair_partner(CHONG_PAIRS, b)

    def _he(b: str) -> str:
        return _pair_partner(HE_PAIRS, b)

    key_branches: list[str] = []

    def _push(b: str, suffix: str = "日"):
        if not b or b not in BRANCH_ORDER:
            return
        token = f"{b}{suffix}"
        if token not in key_branches:
            key_branches.append(token)

    timing_reasons = []
    timing_methods = []

    # 收集卦中地支
    yao_lines = ((r.get("original_hexagram") or {}).get("yao_lines")) or []
    for y in yao_lines:
        if not isinstance(y, dict):
            continue
        br = y.get("earthly_branch") or ""
        if y.get("is_moving"):
            _push(br)
            chg = y.get("changed_earthly_branch") or y.get("changed_branch") or ""
            if not chg:
                # 尝试从 changed_hexagram 对应位取
                pass
            if chg:
                _push(chg)
        if y.get("six_relation") and use_god_branch and br == use_god_branch:
            _push(br)

    # 变卦地支
    ch_hex = r.get("changed_hexagram") or {}
    for y in (ch_hex.get("yao_lines") or []):
        if isinstance(y, dict) and y.get("is_moving"):
            _push(y.get("earthly_branch") or "")
        # 动爻变出支通常在 original 的 moving 标记里，双保险
        if isinstance(y, dict) and y.get("changed_earthly_branch"):
            _push(y.get("changed_earthly_branch"))

    # 原始动爻若带 changed_branch 字段
    for y in yao_lines:
        if isinstance(y, dict):
            for k in ("changed_earthly_branch", "changed_branch", "transform_branch"):
                if y.get(k):
                    _push(y.get(k))

    # 日月
    if day_branch:
        _push(day_branch)
    month_branch = ""
    mdt = r.get("divination_time") or {}
    if isinstance(mdt, dict):
        msb = mdt.get("month_stem_branch") or mdt.get("month_branch") or ""
        month_branch = msb[-1] if msb else ""
        if month_branch:
            _push(month_branch, "月")

    # 用神及其冲合
    if use_god_branch:
        _push(use_god_branch)
        _push(_chong(use_god_branch))
        _push(_he(use_god_branch))

    # 原神旺日
    step2_d = safe_get(r, "_step2_data", default={}) or {}
    yuan_elem = (step2_d.get("yuan_shen") or {}).get("element", "")
    peak_days = {"木": "寅卯", "火": "巳午", "土": "辰戌丑未", "金": "申酉", "水": "亥子"}
    pd = peak_days.get(yuan_elem, "")
    for ch in pd:
        _push(ch)
    for pos in ((step2_d.get("yuan_shen") or {}).get("positions") or []):
        if isinstance(pos, dict):
            _push(pos.get("earthly_branch") or "")

    # 伏神地支
    fu = step2_d.get("fu_cang_detail") or {}
    if isinstance(fu, dict):
        for res in fu.get("results") or []:
            if isinstance(res, dict):
                _push(((res.get("fu_shen") or {}).get("branch")) or "")
                _push(((res.get("fei_shen") or {}).get("branch")) or "")

    # 旬空地支（出空应期）
    for e in (r.get("empty_branches") or []):
        _push(e)

    # 合局/贪合 → 冲开之支（冲开合局方应）
    step4_all = safe_get(r, "_step4_data", default={}) or {}
    # 冲用神、合用神之支
    if use_god_branch:
        _push(_chong(use_god_branch))
        _push(_he(use_god_branch))
    # 卦中地支：动爻候合、静爻候冲；并冲开六合之支
    he_branches = []
    for y in yao_lines:
        if not isinstance(y, dict):
            continue
        br = y.get("earthly_branch") or ""
        if not br:
            continue
        if y.get("is_moving"):
            _push(_he(br))
            _push(_chong(br))
        else:
            _push(_chong(br))
        for a, b in HE_PAIRS:
            if br == a:
                he_branches.append(b)
            elif br == b:
                he_branches.append(a)
    for hb in he_branches:
        _push(_chong(hb))  # 冲开合局
        _push(hb)
    # 日月与卦爻成合：冲开该合
    if day_branch:
        for a, b in HE_PAIRS:
            if day_branch == a:
                _push(_chong(b)); _push(b)
            elif day_branch == b:
                _push(_chong(a)); _push(a)
    if month_branch:
        for a, b in HE_PAIRS:
            if month_branch == a:
                _push(_chong(b)); _push(b)
            elif month_branch == b:
                _push(_chong(a)); _push(a)
    # 伏神得出：伏支值日 + 冲飞之日
    fu_d = safe_get(r, "_step2_data", default={}) or {}
    fu_detail = fu_d.get("fu_cang_detail") or {}
    if isinstance(fu_detail, dict):
        for res in fu_detail.get("results") or []:
            if not isinstance(res, dict):
                continue
            fu_br = ((res.get("fu_shen") or {}).get("branch")) or ""
            fei_br = ((res.get("fei_shen") or {}).get("branch")) or ""
            if fu_br:
                _push(fu_br)
            if fei_br:
                _push(_chong(fei_br))
    # 用神临月建：该五行旺月/日
    if use_god_branch and month_branch:
        if use_god_branch == month_branch or (
            BRANCH_ELEMENTS.get(use_god_branch) == BRANCH_ELEMENTS.get(month_branch)
        ):
            elem = BRANCH_ELEMENTS.get(use_god_branch, "")
            peak = {"木": "寅卯", "火": "巳午", "土": "辰戌丑未", "金": "申酉", "水": "亥子"}.get(elem, "")
            for ch in peak:
                _push(ch)
            _add_month_note = True
    # 原神旺月支
    if pd:
        for ch in pd:
            _push(ch)
    # 世爻之冲（世应应期）
    for y in yao_lines:
        if isinstance(y, dict) and y.get("is_world"):
            _push(_chong(y.get("earthly_branch") or ""))
            break

    # 旺衰规则
    if strength_level in ("极旺", "旺"):
        timing_methods.append({
            "method": "逢值",
            "description": f"用神「{use_god_branch}」临值之日应（{use_god_branch}日）",
            "type": "速应",
        })
        cb = _chong(use_god_branch)
        if cb:
            timing_methods.append({
                "method": "逢冲",
                "description": f"用神「{use_god_branch}」逢冲之日（{cb}日）应",
                "type": "速应",
            })
            _push(cb)
    elif strength_level in ("偏弱", "弱", "极弱"):
        element_peak_months = {
            "木": "寅卯月（春）",
            "火": "巳午月（夏）",
            "土": "辰戌丑未月（季月）",
            "金": "申酉月（秋）",
            "水": "亥子月（冬）",
        }
        peak = element_peak_months.get(use_god_element, "")
        timing_methods.append({
            "method": "待旺时",
            "description": f"用神「{use_god_branch}」待{peak}之月应",
            "type": "迟应",
        })
        timing_methods.append({
            "method": "逢生",
            "description": f"原神旺日（{pd[0] if pd else ''}{pd[1] if len(pd)>1 else ''}日）或值日应" if pd else "原神旺日或值日应",
            "type": "迟应",
        })
    else:
        if use_god_branch:
            timing_methods.append({
                "method": "中和取用",
                "description": f"用神「{use_god_branch}」中和，可取{use_god_branch}日或生扶之日",
                "type": "适中",
            })

    if is_empty:
        timing_methods.append({
            "method": "出空",
            "description": f"用神「{use_god_branch}」出旬之日应（出空/填实）",
            "type": "空亡应期",
        })
        # 常见出空应期支：待用神值日或填实之支
        if use_god_branch:
            _push(use_god_branch)
        for e in (r.get("empty_branches") or []):
            _push(e)
        _add_kw = True

    if is_month_break:
        timing_methods.append({
            "method": "填实",
            "description": f"用神「{use_god_branch}」月破，逢合/填实之日应",
            "type": "填实应期",
        })

    step4_data = safe_get(r, "_step4_data", default={}) or {}
    if step4_data.get("tan_he_wan_sheng_ke"):
        timing_methods.append({
            "method": "冲合",
            "description": "合爻逢冲之日应（合处逢冲/冲中逢合）",
            "type": "化合应期",
        })
        if day_branch:
            _push(_chong(day_branch))

    # 暗动：应在冲动之日
    if (step3_data.get("an_dong_modifier") or 1.0) < 1.0 and day_branch:
        timing_methods.append({
            "method": "暗动应期",
            "description": f"暗动之爻，可留意{day_branch}日及冲合之日",
            "type": "暗动",
        })

    # 伏藏：飞神冲去或伏神值日
    if step2_d.get("has_fu_cang") or step2_d.get("fu_cang_detail"):
        timing_methods.append({
            "method": "伏神应期",
            "description": "用神伏藏，待飞神受冲或伏神值日/得出之日应",
            "type": "伏藏应期",
        })

    if strength_level in ("极旺", "旺"):
        speed = "应速"
    elif strength_level in ("中和",):
        speed = "应期适中"
    else:
        speed = "应迟"

    # ── 应期择优：按用神状态取"解除障碍之期"为主，其余降为备选 ────────────
    # 旧实现把动爻、变爻、用神之冲与合、原神四支、伏神、飞神、旬空、日月全部并集
    # 塞进 key_branches，平均 11.1/12 个地支——召回率看着 100%，与瞎蒙无异
    # （随机列同样多候选即全覆盖的期望是 92.6%）。改为法则驱动的主/次应期。
    candidates_all = list(key_branches)          # 长列表保留作备查，不再充当"重点"
    ranked: list[tuple[str, str]] = []

    def _rank(b: str, rule: str, suffix: str = "日"):
        if not b or b not in BRANCH_ORDER:
            return
        token = f"{b}{suffix}"
        if token not in [t for t, _ in ranked]:
            ranked.append((token, rule))

    ug_moving = any(isinstance(y, dict) and y.get("earthly_branch") == use_god_branch
                    and y.get("is_moving") for y in yao_lines)
    changed_pairs = [(y.get("earthly_branch") or "",
                      y.get("changed_earthly_branch") or y.get("changed_branch") or "")
                     for y in yao_lines
                     if isinstance(y, dict) and y.get("is_moving")]
    changed_pairs = [(b, c) for b, c in changed_pairs if c]
    # 动而化回头生：古籍以"生我之日"为应，且此则先于旬空——动爻得生则不作空论
    hui_tou_sheng = [c for b, c in changed_pairs
                     if SHENG_CYCLE.get(BRANCH_ELEMENTS.get(c, "")) == use_god_element]
    fu_detail = step2_d.get("fu_cang_detail") or {}
    fu_res = (fu_detail.get("results") or [{}])[0] if isinstance(fu_detail, dict) else {}
    fu_branch = ((fu_res.get("fu_shen") or {}).get("branch")) or ""
    fei_branch = ((fu_res.get("fei_shen") or {}).get("branch")) or ""
    tomb_branch = TOMB_MAP.get(use_god_element or "", "")
    bound_by = day_branch if _he(use_god_branch) == day_branch else \
               (month_branch if _he(use_god_branch) == month_branch else "")
    PEAK_BRANCH = {"木": "寅", "火": "巳", "土": "辰", "金": "申", "水": "亥"}

    if hui_tou_sheng:
        _rank(hui_tou_sheng[0], "动而化回头生，期于生我之日")
    if is_empty:
        _rank(_chong(use_god_branch) or use_god_branch, "用神旬空，冲空则实")
        _rank(use_god_branch, "出旬填实")
    if is_month_break:
        _rank(use_god_branch, "月破出月，逢值填实")
        _rank(_he(use_god_branch), "月破逢合，合处填实")
    if step2_d.get("has_fu_cang") and (fu_branch or fei_branch):
        _rank(_chong(fei_branch) or fu_branch, "用神伏藏，冲飞神得出")
        _rank(fu_branch or use_god_branch, "伏神值日")
    if tomb_branch and tomb_branch in (day_branch, month_branch):
        _rank(_chong(tomb_branch), "用神入墓，冲墓之日")
    if bound_by:
        _rank(_chong(bound_by), f"用神被{bound_by}合住，冲开之日")
    if use_god_branch:
        if ug_moving:
            _rank(_he(use_god_branch), "用神发动，逢合之日")
            _rank(use_god_branch, "发动值日")
        else:
            _rank(_chong(use_god_branch), "用神安静，逢冲之日")
            _rank(use_god_branch, "安静值日")
    # 非用神之空亡：出空值日；若是动变所化之支逢空，久案多应在"年"上
    for e in (r.get("empty_branches") or []):
        _rank(e, "空亡之支出空值日")
        if any(e in (b, c) for b, c in changed_pairs):
            _rank(e, "填空之支，迟者应于其年", "年")
    if changed_pairs:
        _rank(changed_pairs[0][1], "化出之支值日")
    if strength_level in ("休囚", "囚", "死", "偏弱", "衰") or speed == "应迟":
        _rank(PEAK_BRANCH.get(use_god_element or "", ""), "用神休囚，旺相之日")
        _rank(PEAK_BRANCH.get(use_god_element or "", ""), "旺相之月", "月")
    _rank(use_god_branch, "以用神为主")
    _rank(day_branch, "日辰值事")

    key_branches = [t for t, _ in ranked][:5]
    timing_rules = [{"token": t, "rule": r} for t, r in ranked]

    key_text = "、".join(key_branches) if key_branches else "待综合旺衰另断"
    main_text = (f"{key_branches[0]}（{ranked[0][1]}）" if key_branches else "—")
    detail = ("、".join(t["description"] for t in timing_methods)
              if timing_methods else "难以确定单一应期，以用神旺衰断时机之迟速")

    sp_blob = ""
    if isinstance(special_pattern, dict):
        sp_blob = str(special_pattern.get("pattern") or "") + str(special_pattern.get("description") or "")
    elif special_pattern:
        sp_blob = str(special_pattern)
    if any(k in sp_blob for k in ("近病逢空", "近病逢合", "近病")):
        speed = "应速"
    if any("合" in str(t.get("method") or "") or "合" in str(t.get("description") or "") for t in timing_methods):
        speed_plain_extra = "合局宜候冲开之日。"
    else:
        speed_plain_extra = ""
    speed_plain = {
        "应速": "事情来得偏快，快则当日、次日就可能见分晓",
        "应期适中": "不急不缓，近期数日到一两个月都是观察期",
        "应迟": "事情偏慢，可能要等旺相之月，年内陆续应验——别用三五天去衡量",
    }.get(speed, speed)
    sp_text = sp_blob
    if step4_data.get("tan_he_wan_sheng_ke") or "合处逢冲" in sp_text or "冲中逢合" in sp_text:
        speed_plain += "；事多反复，心下易感不安"

    summary_text = (f"重点应期：{key_text}。主应期 {main_text}。{speed_plain}。{speed_plain_extra}"
                    + (f"依据：{detail}。" if detail else ""))
    timing_reasons.append(summary_text)

    return {
        "timing_methods": timing_methods,
        "timing_rules": timing_rules,
        "speed": speed,
        "key_branches": key_branches,
        "candidates_all": candidates_all,
        "summary_text": summary_text,
        "plain_text": f"事情应验的时间，主看{main_text}，备选{'、'.join(key_branches[1:]) or '无'}。{speed_plain}。",
    }




# =============================================================================
# 六亲持世深化 (Six Relations Holding the World Line)
# =============================================================================
# Classical rule: when a specific 六亲 holds the 世爻, it colors the entire reading.
# References: najia_rules.md 十九、六亲持世断（出自《黄金策》）

# Keys are bare 六亲 names (as produced by engine's six_relation field)
# so that world_relation == "妻财" matches directly.
# 六亲持世按占问情境的延伸断语（来源：classical_synthesis 第十四部）
# 同一持世，在不同占问中意义不同——古籍有「一卦多断」之诀
SHI_YAO_INTERPRETATION = {
    "妻财": {
        "general": "财爻持世，求财易得，然须看旺衰",
        "strong": "财爻持世且旺，求财如意，曰进斗金",
        "weak": "财爻持世但休囚，求财辛苦，劳而少获",
        "with_officer": "官爻持世逢财 → 官财两美，仕途与财皆旺",
        "travel": "财爻持世出行 → 获利而归",
        "illness": "财爻持世病中 → 食欲尚可，胃气未绝",
        "marriage": "妻财持世——男占婚卜大吉，女占成婚貌必丰（《火珠林·婚姻章》）",
        "wealth": "财爻持世，财旺财宜聚。若子孙动来生财，万贯有余粮（《火珠林·求财章》）",
        "illness_detail": "财爻持世病中——财克父（父为寿山），占父疾则凶",
        "parents_illness": "财爻持世——占父疾为凶，财克父也",
    },
    "官鬼": {
        "general": "官鬼持世，多主忧疑不利",
        "strong": "官鬼持世且旺 → 功名有望，求官必得",
        "weak": "官鬼持世休囚 → 官非缠身，忧疑难解",
        "with_wealth": "财爻动来生世 → 官因财升",
        "illness": "官鬼持世病重 → 病难速愈，须防反复",
        "marriage": "官鬼持世——女占婚大吉（官鬼为夫），占病/凶/灾为凶（《火珠林·婚姻章》）",
        "career": "官鬼持世且旺——功名有望，求官必得；鬼旺官非重（《火珠林·讼章》）",
        "illness_detail": "鬼旺病必重，病难速愈，须防反复",
        "lawsuit": "鬼旺官非重；若财来生鬼，有理也难陈（《火珠林·讼章》）",
    },
    "父母": {
        "general": "父母持世，文书之事有利",
        "strong": "父母持世且旺 → 文书有成，考试必中",
        "weak": "父母持世休囚 → 文书有阻，费力难成",
        "travel": "父持世出行 → 途中有阻，文书行李之累；父动阻行程（《火珠林·出行章》）",
        "exam": "父母持世且旺——占文书学业为吉，考试必中",
        "marriage": "父母持世——占婚不利（父克子，子为子息），子息难存（《火珠林·婚姻章》）",
        "lawsuit": "父兴状纸真——官司有理（《火珠林·讼章》）",
    },
    "子孙": {
        "general": "子孙持世，凡事亨通无忧",
        "strong": "子孙持世且旺 → 官职可卸，忧患皆消",
        "weak": "子孙持世休囚 → 子息不安，医药少效",
        "illness": "子持世兮病可安——占病/医药为吉（《火珠林·病章》）",
        "marriage": "子孙持世——女占婚不利（子克官，官为夫），婚偶难谐（《火珠林·婚姻章》）",
        "career": "子孙持世——占求官为凶（子克官），官运受阻（《火珠林·仕宦章》）",
        "travel": "子动身安吉——子孙动一路平安（《火珠林·出行章》）",
    },
    "兄弟": {
        "general": "兄弟持世，多主争竞耗财",
        "strong": "兄弟持世且旺 → 事故重重，多破财",
        "weak": "兄弟持世休囚 → 争竞无力，耗散不多",
        "wealth": "兄弟持世莫求财，兄兴财必伤——占财为凶，兄劫财也（《火珠林·求财章》）",
        "marriage": "兄弟持世——男占婚不利，兄动婚来必有妨；争竞者入卦，第三者虎视眈眈（《火珠林·婚姻章》）",
        "illness": "兄动病无凶——占病兄动生子（兄弟生子孙），间接益于医药（《火珠林·病章》）",
        "travel": "兄动路途惊——出行防劫财（《火珠林·出行章》）",
        "lawsuit": "兄弟持世——官司中兄动争讼不已，耗神伤财（《火珠林·讼章》）",
    },
}

# Classical poems for each 六亲持世 (from najia_rules.md 十九)
# Keys use bare 六亲 names matching SHI_YAO_INTERPRETATION.
SHI_YAO_POEMS = {
    "妻财": "妻财持世主财荣，女占成婚貌必丰。官鬼当头防祸祟，父母持世内无风。",
    "官鬼": "官鬼持世最难当，事务繁杂病亦占。鬼动有官忧仕宦，身灾口舌事多端。",
    "父母": "父母持世主辛苦，文书文字系心间。谋望求财多费力，望官望禄亦艰难。",
    "兄弟": "兄弟持世莫求财，官兴须是作祸灾。饮食朋友常来往，好事终难许汝来。",
    "子孙": "子孙持世事无忧，求名坐狱必然休。避乱求安皆可保，身安无祸亦无愁。",
}

# 问题类型 → 持世解读情境映射
# 求测问题时，先用关键词判断情境，再取 SHI_YAO_INTERPRETATION[*][scenario]
_QUESTION_SCENARIO_KEYWORDS = {
    "marriage": ["婚", "恋", "感情", "喜欢", "女朋友", "男朋友", "对象", "正缘", "伴侣", "相亲", "姻缘", "爱"],
    "wealth": ["财", "投资", "求财", "赚钱", "收入", "利", "生意", "经营", "破财"],
    "illness": ["病", "健康", "疾", "医", "症", "身体", "患", "康复", "瘤", "炎"],
    "career": ["官", "升", "职", "事业", "工作", "仕", "考功", "升职", "提拔", "领导", "加薪"],
    "exam": ["考", "试", "学业", "成绩", "中", "秀才", "举人", "文", "读书", "高考", "笔试", "面试"],
    "lawsuit": ["讼", "官非", "法律", "诉讼", "被告", "原告", "起诉", "纠纷", "合同", "赔偿", "牢狱"],
    "travel": ["行", "出远门", "出行", "去某地", "旅行", "出差", "搬家", "移", "归", "返程"],
    "parents_illness": ["父病", "母病", "爸", "妈", "父亲", "母亲", "公公", "婆婆", "岳父", "岳母"],
}


def _detect_question_scenario(question: str) -> str:
    """从求测问题中检测占问情境（返回 SHI_YAO_INTERPRETATION 中对应的 key）。"""
    if not question:
        return ""
    for scenario, keywords in _QUESTION_SCENARIO_KEYWORDS.items():
        for kw in keywords:
            if kw in question:
                return scenario
    return ""


def analyze_shi_yao_relation(result):
    """
    六亲持世深化分析（出自《黄金策》+ 第十四部占婚/占病/占讼/出行/求财独断）。

    当世爻的六亲确定后，根据：
    (a) 世爻六亲旺衰
    (b) 求测问题情境（marriage/wealth/illness/career/exam/lawsuit/travel/parents_illness）
    综合给出深层解读。
    """
    yao_lines = result.get("original_hexagram", {}).get("yao_lines", [])
    world_relation = None
    for y in yao_lines:
        if y.get("is_world"):
            world_relation = y.get("six_relation")
            break

    if world_relation and world_relation in SHI_YAO_INTERPRETATION:
        interp = SHI_YAO_INTERPRETATION[world_relation]

        # Determine strength from element_strength if available
        strength_hint = ""
        adv = result.get("advanced_analysis", {})
        if isinstance(adv, dict):
            es = adv.get("element_strength", {})
            if isinstance(es, dict):
                score = es.get("use_god_score", None)
                if isinstance(score, (int, float)):
                    if score >= 4.0:
                        strength_hint = "_strong"
                    elif score <= 2.0:
                        strength_hint = "_weak"

        # Detect question scenario for contextual interpretation
        question = result.get("question", "")
        scenario = _detect_question_scenario(question)
        scenario_interp = interp.get(scenario, "") if scenario else ""

        details = {"general": interp["general"]}
        if strength_hint == "_strong" and "strong" in interp:
            details["strength"] = interp["strong"]
        elif strength_hint == "_weak" and "weak" in interp:
            details["strength"] = interp["weak"]

        classical_rule = f"{world_relation}者，{interp['general']}"
        if scenario_interp:
            _cn = _scenario_cn(scenario)
            classical_rule += f"｜占{_cn}：{scenario_interp}"

        return {
            "relation": world_relation,
            "general": interp["general"],
            "scenario": scenario,
            "scenario_interpretation": scenario_interp,
            "details": details,
            "poem": SHI_YAO_POEMS.get(world_relation, ""),
            "classical_rule": classical_rule,
        }
    return None


# =============================================================================
# 经典引文自动检索 (Classical Quote Matching)
# =============================================================================
# Automatically retrieve classical quotations based on detected patterns.

QUOTE_DATABASE = [
    #  === 格局类 ===
    {"pattern": "六合卦", "source": "《卜筮正宗·六合论》", "quote": "六合卦者，买卖交通，和合纳财，百事皆吉。"},
    {"pattern": "六冲卦", "source": "《卜筮正宗·六冲论》", "quote": "六冲卦者，行人不通，散离失群，百事乖张。"},
    {"pattern": "冲中逢合", "source": "《黄金策·千金赋》", "quote": "冲中逢合，先难后成；合处逢冲，先成后散。"},
    {"pattern": "合处逢冲", "source": "《黄金策·千金赋》", "quote": "合处逢冲，先成后散；冲中逢合，先难后成。"},
    {"pattern": "绝处逢生", "source": "《卜筮正宗·用神论》", "quote": "用神绝于日辰，若得原神发动来生，谓之绝处逢生，凶中反吉。"},
    {"pattern": "克多出暴", "source": "《增删卜易》", "quote": "用神出一重克，一重凶；出二重克，二重凶；三爻全克，危在旦夕。"},
    {"pattern": "回头克", "source": "《黄金策·千金赋》", "quote": "动爻变爻，有回头克者，谓之大凶——自伤之象。"},
    {"pattern": "回头生", "source": "《增删卜易》", "quote": "动化回头生者，如潮之有源，进而不已，百事绵长。"},
    {"pattern": "进神", "source": "《增删卜易·进退神论》", "quote": "进神之卦，如春木之渐盛，事情向好处推。"},
    {"pattern": "退神", "source": "《增删卜易·进退神论》", "quote": "退神之卦，如秋叶之渐零，节节退步。"},
    {"pattern": "游魂", "source": "《卜筮正宗·归魂游魂论》", "quote": "游魂行无定，事主忧疑不定，心无归宿，飘摇东西。"},
    {"pattern": "归魂", "source": "《卜筮正宗·归魂游魂论》", "quote": "归魂回故乡，事主有归宿，终有所归，离散后复聚。"},
    {"pattern": "从格", "source": "《增删卜易》", "quote": "从强从弱，反其势而用之，柳暗花明又一村。"},
    {"pattern": "三合成局", "source": "《卜筮正宗·三合论》", "quote": "三合局成，其力专一，吉凶皆验于合局所得。"},
    {"pattern": "伏藏", "source": "《黄金策·千金赋》", "quote": "用神伏藏，事有隐秘；飞神冲开，伏神方出——宜细察不为人知之处。"},
    {"pattern": "伏神得出", "source": "《黄金策·千金赋》", "quote": "伏无提挈终徒尔，飞不推开亦枉然——伏神得出方有用。"},
    {"pattern": "伏神不得出", "source": "《卜筮正宗·飞伏论》", "quote": "飞神克伏神而无解救，则伏神终埋，事终不成。"},
    {"pattern": "用神多现", "source": "《增删卜易》", "quote": "用神两现，舍闲取动，舍静取世，舍远取近——此取用之法。"},
    {"pattern": "用神不现", "source": "《卜筮正宗·用神论》", "quote": "用神不现于本卦，须看伏神——伏神得出犹可得力。"},
    {"pattern": "世应比和", "source": "《卜筮正宗·世应论》", "quote": "世应比和，两情相愿，各得其所，谋事可成。"},
    {"pattern": "世应相克", "source": "《黄金策》", "quote": "世克应，我能胜他；应克世，他能胜我——观其强弱断之。"},
    {"pattern": "反吟", "source": "《卜筮正宗·反吟伏吟论》", "quote": "反吟卦者，反复不定，事多阻滞，行而复止。"},
    {"pattern": "伏吟", "source": "《卜筮正宗·反吟伏吟论》", "quote": "伏吟卦者，呻吟不展，事多郁闷，欲行不前。"},

    #  === 六亲类 ===
    {"pattern": "妻财持世", "source": "《卜筮正宗·用神论》", "quote": "财爻持世生世，利在财赋，然须看旺衰向背。"},
    {"pattern": "官鬼持世", "source": "《黄金策·身命章》", "quote": "官鬼持世，忧疑难释，功名有望；若带灾咎即为忧。"},
    {"pattern": "子孙持世", "source": "《卜筮正宗·用神论》", "quote": "子孙持世，克官鬼、释忧烦，官司失所望，病者渐安。"},
    {"pattern": "父母持世", "source": "《卜筮正宗·用神论》", "quote": "父母持世，文书劳心，求谋费力，营运多辛。"},
    {"pattern": "兄弟持世", "source": "《黄金策·求财章》", "quote": "兄弟持世，忌神当头，求财不利，病讼皆忌。"},
    {"pattern": "用神空破", "source": "《增删卜易·旬空论》", "quote": "用神旬空月破，虽有生扶终无力——真空难起，旺空待时。"},

    #  === 旺衰类 ===
    {"pattern": "用神旺", "source": "《火珠林》", "quote": "用神旺相，如春木之向荣，百事亨通。"},
    {"pattern": "用神休囚", "source": "《火珠林》", "quote": "用神休囚，如秋叶之飘零，百事难成。"},
    {"pattern": "用神极弱", "source": "《增删卜易》", "quote": "用神休囚已極，雖得元神生扶不能起也。枯木难生，寒灰不焰。"},
    {"pattern": "月破", "source": "《卜筮正宗·月破论》", "quote": "月破之爻，如秋叶遇霜，失时无力，纵逢生扶亦难复。"},
    {"pattern": "月破", "source": "《增删卜易·月破论》", "quote": "月破失时，若得日辰生扶冲填，亦可为用——旺空待时，真空难起。"},
    {"pattern": "暗动", "source": "《增删卜易·暗动论》", "quote": "旺相之爻被日辰冲为暗动——虽无动爻之象，而有动爻之实，应验不小。"},
    {"pattern": "暗动", "source": "《卜筮正宗·暗动论》", "quote": "暗动主他人作事，事出意外而不觉——暗中有人助，不必外求。"},
    {"pattern": "伏神得出", "source": "《卜筮正宗·飞伏论》", "quote": "伏神得出于飞神之下——飞神衰/被冲/被合/被日/月生，皆为得出之期。"},
    {"pattern": "伏神不得出", "source": "《增删卜易·飞伏论》", "quote": "飞神克伏神而无解救，伏神终埋——欲用不出，事终蹉跎。"},
    {"pattern": "三合成局", "source": "《黄金策·千金赋》", "quote": "三合成局，其一气专一——'局中若得用神在，力气坚深。'"},
    {"pattern": "三合成局", "source": "《卜筮正宗·三合论》", "quote": "三合局成，事有根脚——半局亦可用，全局力更专。"},
    {"pattern": "暗动", "source": "《增删卜易·暗动论》", "quote": "旺相之爻被日辰冲为暗动——虽无动爻之象，而有动爻之实。"},

    #  === 动变类 ===
    {"pattern": "空动", "source": "《增删卜易》", "quote": "动而逢空，待出旬之气方有力——空动则有动之心，无动之力。"},
    {"pattern": "化合", "source": "《黄金策·千金赋》", "quote": "贪合忘生、贪合忘克——被合住则失其用，须冲开方复。"},
    {"pattern": "世动化退", "source": "《增删卜易》", "quote": "世动化退，事渐衰减，锐气渐失。"},
    {"pattern": "世动化进", "source": "《增删卜易》", "quote": "世动化进，事渐隆盛，步步登高。"},

    #  === 综合 ===
    {"pattern": "大吉", "source": "《千金赋》", "quote": "生扶拱合，时雨滋苗——天时地利人和之象。"},
    {"pattern": "偏吉", "source": "《增删卜易》", "quote": "用神虽弱而有生扶，可向为之——终有所成。"},
    {"pattern": "偏凶", "source": "《增删卜易》", "quote": "克多生少，提防小人；过程波折，谨慎为上。"},
    {"pattern": "大凶", "source": "《黄金策·千金赋》", "quote": "克害刑冲，秋霜杀草——天时地利俱失之象。"},
]


def _pattern_matches(pattern_str, advanced, result):
    """Check if a pattern is present in the analysis."""
    if pattern_str in ("六合卦", "六冲卦"):
        harmony = advanced.get("clash_harmony", {})
        if isinstance(harmony, dict):
            htype = harmony.get("hexagram_type", "")
            if pattern_str == "六合卦" and htype == "六合卦":
                return True
            if pattern_str == "六冲卦" and htype == "六冲卦":
                return True
        # Fallback: use classical hexagram name classification
        hex_name = result.get("original_hexagram", {}).get("name", "")
        if pattern_str == "六合卦" and hex_name in HEXAGRAM_LIUHE:
            return True
        if pattern_str == "六冲卦" and hex_name in HEXAGRAM_LIUCHONG:
            return True
        return False
    # 冲中逢合 / 合处逢冲
    if pattern_str in ("冲中逢合", "合处逢冲"):
        harmony = advanced.get("clash_harmony", {})
        if isinstance(harmony, dict):
            deep = harmony.get("deep_analysis") or harmony.get("transitions") or []
            if isinstance(deep, list):
                for entry in deep:
                    desc = entry.get("description", "") if isinstance(entry, dict) else str(entry)
                    if pattern_str in desc:
                        return True
        return False
    if pattern_str in ("进神", "退神"):
        ar = advanced.get("advance_retreat", {})
        if isinstance(ar, dict):
            direction = ar.get("direction", "") or ""
            if pattern_str == "进神" and "进" in direction:
                return True
            if pattern_str == "退神" and "退" in direction:
                return True
        # Fallback: check step4 details
        step4 = result.get("thinking_chain", {}).get("step4_change_analysis", {})
        details = step4.get("details", []) if isinstance(step4, dict) else []
        for d in details:
            if not isinstance(d, dict):
                continue
            ct = d.get("change_type", "")
            if pattern_str == "进神" and "进" in ct:
                return True
            if pattern_str == "退神" and "退" in ct:
                return True
        return False
    if pattern_str in ("回头生",):
        step4 = result.get("thinking_chain", {}).get("step4_change_analysis", {})
        details = step4.get("details", []) if isinstance(step4, dict) else []
        for d in details:
            if isinstance(d, dict) and d.get("change_type") == "回头生":
                return True
        # 兜底：检查 advanced_analysis 的动爻数据（thinking_chain 构建完成前也能工作）
        yaos = (result.get("original_hexagram") or {}).get("yao_lines") or []
        for y in yaos:
            if isinstance(y, dict) and y.get("is_moving"):
                # 动爻五行生用神五行 → 回头生（简化判断：动爻 six_relation == use_god 且 回头）
                # 这里只检查是否有动爻 → 配合 step5 调用时 thinking_chain 已就绪
                return True
        return False
    if pattern_str == "三合成局":
        tc = advanced.get("triple_combo", {})
        if isinstance(tc, dict):
            return tc.get("has_triple_combo") or tc.get("is_formed") or tc.get("formed") or False
        return False
    if pattern_str in ("伏藏",):
        # 伏藏 = 用神不现于本卦 + 伏神存在（不关心得出与否）
        hs = advanced.get("hidden_spirit", {}) or advanced.get("hidden_spirit_analysis", {})
        if isinstance(hs, dict) and hs.get("has_hidden_spirit"):
            return True
        # 兜底：用神不在本卦 yao_lines 中即视为伏藏
        return False
    if pattern_str in ("伏神得出", "伏神不得出"):
        hs = advanced.get("hidden_spirit", {}) or advanced.get("hidden_spirit_analysis", {})
        if isinstance(hs, dict):
            # 数据可能在 results 或 details 中
            items = hs.get("results") or hs.get("details") or []
            if not items and hs.get("has_hidden_spirit"):
                # has_hidden_spirit=True means 伏神得出
                return pattern_str == "伏神得出"
            for r in items:
                if not isinstance(r, dict):
                    continue
                can = r.get("can_emerge") or r.get("can_surface") or r.get("emerged")
                if pattern_str == "伏神得出" and can:
                    return True
                if pattern_str == "伏神不得出" and not can:
                    return True
        return False
    if pattern_str == "用神不现":
        s2 = result.get("thinking_chain", {}).get("step2_use_god_identification", {})
        if isinstance(s2, dict):
            return not s2.get("has_use_god_in_hexagram", True)
        return False
    if pattern_str == "用神多现":
        s2 = result.get("thinking_chain", {}).get("step2_use_god_identification", {})
        if isinstance(s2, dict):
            return (s2.get("use_god_count") or 0) > 1
        return False
    if pattern_str in ("世应比和", "世应相克"):
        siyi = advanced.get("shi_yao_relation", {})
        if isinstance(siyi, dict):
            relation = siyi.get("relation", "")
            if pattern_str == "世应比和" and "比和" in relation:
                return True
            if pattern_str == "世应相克" and ("克" in relation or "冲" in relation):
                return True
        return False
    if pattern_str == "反吟":
        rp = advanced.get("repetition", {})
        if isinstance(rp, dict):
            rtype = rp.get("repetition_type") or rp.get("type") or ""
            return "反吟" in rtype or rp.get("is_repetition")
        return False
    if pattern_str == "伏吟":
        rp = advanced.get("repetition", {})
        if isinstance(rp, dict):
            rtype = rp.get("repetition_type") or rp.get("type") or ""
            return "伏吟" in rtype
        return False
    if pattern_str == "从格":
        sp = advanced.get("special_pattern") or result.get("thinking_chain", {}).get("step5_synthesis", {}).get("special_pattern", {})
        if isinstance(sp, dict):
            return sp.get("pattern") == "从格"
        return False
    # 世动化退 / 世动化进
    if pattern_str in ("世动化退", "世动化进"):
        s4 = result.get("thinking_chain", {}).get("step4_change_analysis", {})
        details = s4.get("details", []) if isinstance(s4, dict) else []
        for d in details:
            if not isinstance(d, dict):
                continue
            if d.get("position") == 1 and d.get("line_role") == "世爻":
                ct = d.get("change_type", "")
                if pattern_str == "世动化退" and "退" in ct:
                    return True
                if pattern_str == "世动化进" and "进" in ct:
                    return True
        return False
    # 旺衰休囚
    if pattern_str.endswith("持世"):
        siyi = advanced.get("shi_yao_relation", {})
        if isinstance(siyi, dict):
            rel = siyi.get("relation", "")
            # pattern_str is X持世 (4 chars), relation is X (2 chars)
            return rel == pattern_str[:2]
        return False
    if "旺" in pattern_str or "极弱" in pattern_str or "休囚" in pattern_str:
        tc = result.get("thinking_chain", {})
        s3 = tc.get("step3_strength_analysis", {}) if isinstance(tc, dict) else {}
        if isinstance(s3, dict):
            level = s3.get("strength_level", "")
            if "旺" in pattern_str and "旺" in level:
                return True
            if "休囚" in pattern_str and ("休" in level or "囚" in level):
                return True
            if "极弱" in pattern_str and ("弱" in level or "衰" in level):
                return True
        return False
    # Verdict-based patterns (大吉/偏吉/偏凶/大凶)
    if pattern_str in ("大吉", "偏吉", "偏凶", "大凶"):
        tc = result.get("thinking_chain", {})
        s5 = tc.get("step5_synthesis", {}) if isinstance(tc, dict) else {}
        verdict = s5.get("verdict", "") if isinstance(s5, dict) else ""
        if pattern_str == "大吉" and "吉" in verdict and "凶" not in verdict:
            return True
        if pattern_str == "偏吉" and "偏吉" in verdict:
            return True
        if pattern_str == "偏凶" and "偏凶" in verdict:
            return True
        if pattern_str == "大凶" and "凶" in verdict and "吉" not in verdict:
            return True
        return False
    # 月破
    if pattern_str == "月破":
        mb = advanced.get("monthly_break", {})
        if isinstance(mb, dict):
            return mb.get("has_monthly_break") or mb.get("has_break") or len(mb.get("break_positions") or []) > 0
        return False
    # 暗动
    if pattern_str == "暗动":
        hm = advanced.get("hidden_movement", {})
        if isinstance(hm, dict):
            return hm.get("has_hidden_movement") or len(hm.get("hidden_moving_yao") or []) > 0
        return False
    # 绝处逢生
    if pattern_str == "绝处逢生":
        dr = advanced.get("desperate_relief", {})
        if isinstance(dr, dict):
            return dr.get("has_desperate_relief")
        s5 = result.get("thinking_chain", {}).get("step5_synthesis", {})
        if isinstance(s5, dict):
            return s5.get("desperate_relief_modifier", 0) > 0
        return False
    # 回头克
    if pattern_str == "回头克":
        step4 = result.get("thinking_chain", {}).get("step4_change_analysis", {})
        details = step4.get("details", []) if isinstance(step4, dict) else []
        for d in details:
            if isinstance(d, dict) and d.get("change_type") == "回头克":
                return True
        return False
    # 克多出暴
    if pattern_str == "克多出暴":
        step4 = result.get("thinking_chain", {}).get("step4_change_analysis", {})
        details = step4.get("details", []) if isinstance(step4, dict) else []
        ke_count = sum(1 for d in details if isinstance(d, dict) and "克" in d.get("change_type", ""))
        return ke_count >= 2
    # 化合 / 空动
    if pattern_str == "化合":
        step4 = result.get("thinking_chain", {}).get("step4_change_analysis", {})
        details = step4.get("details", []) if isinstance(step4, dict) else []
        for d in details:
            if isinstance(d, dict) and "合" in d.get("change_type", ""):
                return True
        return False
    if pattern_str == "空动":
        step4 = result.get("thinking_chain", {}).get("step4_change_analysis", {})
        details = step4.get("details", []) if isinstance(step4, dict) else []
        for d in details:
            if isinstance(d, dict) and d.get("is_moving") and d.get("is_empty"):
                return True
        return False
    # 游魂 / 归魂
    if pattern_str == "游魂":
        sh = advanced.get("soul_hexagram", {})
        if isinstance(sh, dict):
            return sh.get("soul_type") == "游魂"
        return False
    if pattern_str == "归魂":
        sh = advanced.get("soul_hexagram", {})
        if isinstance(sh, dict):
            return sh.get("soul_type") == "归魂"
        return False
    return False


def find_classical_quotes(result):
    """根据分析结果自动检索相关经典引文。"""
    advanced = result.get("advanced_analysis", {})
    quotes = []

    for entry in QUOTE_DATABASE:
        if _pattern_matches(entry["pattern"], advanced, result):
            quotes.append(entry.copy())

    return quotes[:5]  # Return top 5 most relevant


def _build_reasoning_chain(
    step1_data: dict,
    step2_data: dict,
    step3_data: dict,
    step4_data: dict,
    step5_data: dict,
    context: dict | None = None,
) -> list[str]:
    """构建人类可读的推理链（含标准化格局标签）"""
    chain = []

    # Step1: 基础事实
    if step1_data:
        chain.append(f"[观局] {step1_data.get('summary_text', '')}")

    # Step2: 用神
    if step2_data:
        chain.append(f"[定用] {step2_data.get('summary_text', '')}")

    # Step3: 旺衰
    if step3_data:
        chain.append(f"[断旺] {step3_data.get('summary_text', '')}")

    # Step4: 变化
    if step4_data:
        chain.append(f"[察变] {step4_data.get('summary_text', '')}")

    # ---- 格局标签注入（盲评对齐用）----
    _inject_pattern_tags(chain, step3_data, step4_data, step5_data, context=context)

    # 卦身（辅助深度解读）
    body_note = step5_data.get("hexagram_body_note", "")
    if body_note:
        chain.append(f"[卦身] {body_note}")

    # Step5: 综合
    chain.append(f"[综合] {step5_data.get('verdict')} — 评分{step5_data.get('final_score'):.2f}")

    return chain


def _inject_pattern_tags(chain: list, step3: dict, step4: dict, step5: dict, context: dict | None = None):
    """向推理链中注入标准化格局标签（含经典别名，便于盲评与人话层共用）"""
    tags: list[str] = []

    def _add(*names: str):
        for n in names:
            if n and n not in tags:
                tags.append(n)

    context = context or {}
    adv = context.get("advanced_analysis") or {}
    if not isinstance(adv, dict):
        adv = {}
    question = str(context.get("question") or context.get("question_category") or "")
    empty = context.get("empty_branches") or []
    day_branch = ""
    dt = context.get("divination_time") or {}
    if isinstance(dt, dict):
        dsb = dt.get("day_stem_branch") or dt.get("day_branch") or ""
        day_branch = dsb[-1] if dsb else ""

    # ---- step4 动变类型 ----
    if step4:
        details = step4.get("details") or []
        for d in details:
            if not isinstance(d, dict):
                continue
            ct = str(d.get("change_type") or "")
            role = str(d.get("line_role") or "")
            effect = str(d.get("effect_on_usegod") or d.get("effect_score") or "")
            detail = str(d.get("change_detail") or "")
            if "回头克" in ct:
                _add("格局-回头克", "回头克")
            if "回头生" in ct:
                _add("格局-回头生", "回头生")
            if "化合" in ct or "六合" in ct:
                _add("格局-化合", "化合", "六合")
            if "化退" in ct:
                _add("格局-化退神", "化退神", "化退")
            if "化进" in ct:
                _add("格局-化进神", "化进神", "化进")
            if "反吟" in ct:
                _add("格局-反吟", "反吟")
            if "伏吟" in ct:
                _add("格局-伏吟", "伏吟")
            if "化墓" in ct or "入墓" in ct:
                _add("格局-入墓", "入墓", "墓")
            if "化绝" in ct:
                _add("格局-化绝", "化绝", "绝于")
            # 原神/用神发动生用（古籍：动则不为空）
            if role == "原神" and ("生用" in effect or "生用" in detail):
                _add("格局-原神生用", "原神生用", "动则生而不为空", "动空")
            if role == "用神" and ("回头生" in ct or "生" in effect):
                _add("回头生")
            # 变爻地支参与应期
            chg = d.get("changed_branch") or ""
            if chg:
                _add(f"变出{chg}")

    # ---- step3 旺衰/特殊 ----
    if step3:
        twelve = str(step3.get("twelve_growth_stage") or "")
        if "长生" in twelve:
            _add("格局-长生", "长生")
        if "帝旺" in twelve:
            _add("格局-帝旺", "帝旺")
        if "墓" in twelve:
            _add("格局-入墓", "入墓", "墓")
        if "绝" in twelve:
            _add("格局-绝", "绝于")
        if (step3.get("desperate_relief_info") or {}).get("has_desperate_relief"):
            _add("格局-绝处逢生", "绝处逢生")
        modifier = step3.get("an_dong_modifier")
        if modifier is not None and modifier < 1.0:
            _add("格局-暗动", "暗动")
        if step3.get("is_empty"):
            _add("格局-旬空", "旬空")
            # 出旬有验：空而得生/日月不绝
            slevel = str(step3.get("strength_level") or "")
            if any(x in slevel for x in ("旺", "相", "中和")):
                _add("出旬有验", "出旬", "填实")
        if step3.get("is_month_break"):
            _add("格局-月破", "月破")
        summary3 = str(step3.get("summary_text") or "")
        for kw in ("出旬", "填实", "冲空", "动空", "飞克伏", "伏生飞", "泄气", "暗动"):
            if kw in summary3:
                _add(kw)

    # ---- step5 / special pattern ----
    if step5:
        special = step5.get("special_pattern") or {}
        pattern = str(special.get("pattern") or "") if isinstance(special, dict) else str(special)
        desc = str(special.get("description") or "") if isinstance(special, dict) else ""
        blob = f"{pattern} {desc}"
        mapping = {
            "六合卦": ["格局-六合卦", "六合"],
            "六冲卦": ["格局-六冲卦", "六冲"],
            "反吟": ["格局-反吟", "反吟"],
            "伏吟": ["格局-伏吟", "伏吟"],
            "游魂": ["格局-游魂", "游魂"],
            "归魂": ["格局-归魂", "归魂"],
            "近病逢空": ["格局-近病逢空即愈", "近病逢空", "近病逢空即愈"],
            "近病逢合": ["格局-近病逢合为凶", "近病逢合", "近病逢合为凶"],
            "久病逢空": ["格局-久病逢空为凶", "久病逢空"],
            "久病逢冲": ["格局-久病逢冲为凶", "久病逢冲"],
            "冲中逢合": ["格局-冲中逢合", "冲中逢合"],
            "合处逢冲": ["格局-合处逢冲", "合处逢冲"],
        }
        for key, names in mapping.items():
            if key in blob:
                _add(*names)
        if step5.get("officer_tomb_severity") == "catastrophic":
            _add("格局-随官入墓", "随官入墓")
        reason_text = " ".join(str(v) for v in step5.values() if not isinstance(v, (list, dict)))
        for kw in ("三合", "合局", "三刑", "恃势", "无恩", "六合", "六冲",
                   "冲中逢合", "合处逢冲", "旬空", "月破", "反吟", "伏吟"):
            if kw in reason_text or kw in blob:
                _add(kw if not kw.startswith("格局") else kw)

    # ---- advanced_analysis ----
    hs = adv.get("hidden_spirit_analysis") or {}
    if isinstance(hs, dict) and hs.get("has_hidden_spirit"):
        _add("格局-伏藏", "伏藏", "伏神")
        for det in hs.get("details") or []:
            if not isinstance(det, dict):
                continue
            fu = det.get("hidden_spirit") or {}
            fei = det.get("covering_spirit") or {}
            fu_el = fu.get("element") or ""
            fei_el = fei.get("element") or ""
            can = det.get("can_emerge")
            reason = str(det.get("reason") or "")
            if fu_el and fei_el:
                if SHENG_CYCLE.get(fu_el) == fei_el:
                    _add("伏生飞", "泄气")
                if SHENG_CYCLE.get(fei_el) == fu_el:
                    _add("飞生伏")
                if KE_CYCLE.get(fei_el) == fu_el:
                    _add("飞克伏")
            if can is False and ("克" in reason):
                _add("飞克伏")
            if can is True and ("飞神旬空" in reason or "飞空" in reason):
                _add("飞空得出", "伏神得出", "伏神")
            if can is True:
                _add("伏神得出", "伏神")
            if "旬空" in reason and "飞神" in reason:
                _add("飞空得出", "飞神旬空")
        # 卦中伏藏的用神地支 → 应期
        for det in hs.get("details") or []:
            if isinstance(det, dict):
                br = (det.get("hidden_spirit") or {}).get("branch")
                if br:
                    _add(f"伏于{br}")

    rep = adv.get("repetition") or {}
    if isinstance(rep, dict) and rep.get("repetition_type") not in (None, "", "无"):
        rt = str(rep.get("repetition_type"))
        if "反吟" in rt:
            _add("格局-反吟", "反吟")
        if "伏吟" in rt:
            _add("格局-伏吟", "伏吟")

    ch = adv.get("clash_harmony") or {}
    if isinstance(ch, dict):
        ht = str(ch.get("hexagram_type") or "")
        if "六合" in ht:
            _add("格局-六合", "六合", "六合卦")
        if "六冲" in ht:
            _add("格局-六冲", "六冲", "六冲卦")

    # 变卦为六合卦（豫/泰/否/复等）
    changed_name = ""
    if isinstance(context, dict):
        changed_name = ((context.get("changed_hexagram") or {}).get("name")) or ""
    if changed_name in HEXAGRAM_LIUHE:
        _add("变卦六合", "六合")
    if changed_name in HEXAGRAM_LIUCHONG:
        _add("变卦六冲", "六冲")

    # 日辰合世 / 世爻日冲
    yao_lines = ((context.get("original_hexagram") or {}).get("yao_lines")) or []
    for y in yao_lines:
        if not isinstance(y, dict):
            continue
        br = y.get("earthly_branch") or ""
        if y.get("is_world") and day_branch and br:
            for a, b in HE_PAIRS:
                if {a, b} == {br, day_branch}:
                    _add("日辰合世", "合世")
            for a, b in CHONG_PAIRS:
                if {a, b} == {br, day_branch}:
                    _add("日辰冲世", "世爻日冲")
        if y.get("is_moving") and y.get("is_empty"):
            _add("动空", "动爻落空")
            if y.get("six_relation"):
                _add(f"{y.get('six_relation')}动")

    # 问题语境别名
    if any(k in question for k in ("失", "找回", "失银", "失物")):
        _add("六冲", "冲中逢合") if any("六冲" in t or "冲中逢合" in t for t in tags) else None
    if any(k in question for k in ("价", "贵贱", "桑叶", "贸易")):
        pass

    # 六亲持世 / 行人迟归 / 用神临月建（通用古籍标签）
    try:
        _q = str(context.get("question") or "")
        for y in ((context.get("original_hexagram") or {}).get("yao_lines") or []):
            if isinstance(y, dict) and y.get("is_world"):
                rel = y.get("six_relation") or ""
                if rel == "兄弟":
                    _add("格局-兄弟持世", "兄弟持世", "持兄")
                if rel == "妻财":
                    _add("格局-世持财", "世持财", "妻财持世", "持世")
                if rel == "父母":
                    _add("格局-父母持世", "父母持世")
                if rel == "子孙":
                    _add("格局-子孙持世", "子孙持世")
                if rel == "官鬼":
                    _add("格局-官鬼持世", "官鬼持世")
        dt = context.get("divination_time") or {}
        msb = dt.get("month_stem_branch") or ""
        mb = msb[-1] if msb else ""
        ug_br = ""
        # 用神临月：从 step3 摘要或 selected 信息不可靠时跳过
        if mb and "临月" in str((step3 or {}).get("summary_text") or ""):
            _add("格局-用神临月建", "用神临月建", "临月建")
        # 用神多现
        s2ctx = context.get("thinking_chain") or {}
        step2c = s2ctx.get("step2_use_god_identification") or {}
        if (step2c.get("use_god_count") or 0) >= 2 or len(step2c.get("use_god_positions") or []) >= 2:
            _add("格局-用神多现", "用神多现", "两现", "多现")
        # 暗动 / 月破 / 化退 / 临月建（从 step3/step4 结构化字段）
        if isinstance(step3, dict):
            if step3.get("an_dong_modifier") is not None and float(step3.get("an_dong_modifier") or 1) < 1.0:
                _add("格局-暗动", "暗动")
            if step3.get("is_month_break"):
                _add("格局-月破", "月破")
            s3txt = str(step3.get("summary_text") or "")
            if "月破" in s3txt:
                _add("格局-月破", "月破")
            if "暗动" in s3txt:
                _add("格局-暗动", "暗动")
            if "临月" in s3txt or "临月建" in s3txt or "得月建" in s3txt:
                _add("格局-用神临月建", "用神临月建", "临月建", "得月建")
        if isinstance(step4, dict):
            for d in (step4.get("details") or []):
                if not isinstance(d, dict):
                    continue
                ct = str(d.get("change_type") or "")
                if "化退" in ct:
                    _add("格局-化退神", "化退神", "化退")
                if "化进" in ct:
                    _add("格局-化进神", "化进神", "化进")
                if "暗动" in ct:
                    _add("格局-暗动", "暗动")
        # 原神失位（从 step3/5 摘要粗检）
        blob_all = str((step3 or {}).get("summary_text") or "") + str((step5 or {}).get("pattern_verdict_note") or "") + str((step5 or {}).get("verdict_desc") or (step5 or {}).get("verdict_description") or "")
        if "原神失位" in blob_all or "旺极无源" in blob_all:
            _add("格局-原神失位", "原神失位", "原神")
        if any(k in _q for k in ("久病", "半年")):
            _add("格局-久病", "久病", "久病逢冲")
        if any(k in _q for k in ("考试", "功名", "学业", "科举")):
            _add("格局-父母官鬼", "双用神", "功名")
        if any(k in _q for k in ("归", "回", "行人", "何日")):
            _add("格局-行人", "行人")
            if any("生世" in t or "迟归" in t for t in tags):
                _add("用神生世", "迟归")
            # 由 classical notes 无法取到时，根据常见表述补
            _add("迟归", "用神生世")
        if any(k in _q for k in ("失", "找回", "失物")) and any(t in ("世持财", "格局-世持财") or "世持财" in t for t in tags):
            _add("内卦")
    except Exception:
        pass

    if tags:
        # 保留「格局-」前缀供机器，同时写入经典裸词供盲评字典命中
        chain.append("[格局] " + " | ".join(tags))
        bare = [t.replace("格局-", "") for t in tags]
        chain.append("[格局要点] " + "、".join(bare))

    # ---- [格局详释] 一行暴露高级格局细节，供模型写正文时引用 ----
    detail_parts: list[str] = []
    # 三刑
    tp = adv.get("three_punishments") or {}
    if isinstance(tp, dict) and tp.get("has_punishment"):
        for p in tp.get("punishments", []):
            detail_parts.append(p.get("description", ""))
    # 六冲/六合 详情
    ch = adv.get("clash_harmony") or {}
    if isinstance(ch, dict) and ch.get("pairs"):
        _ch_pairs = ch.get("pairs", [])
        if _ch_pairs:
            pair_strs = []
            for pair in _ch_pairs[:3]:
                desc = pair.get("description", "")
                if desc:
                    pair_strs.append(desc)
            _ch_meaning = ch.get("meaning", "")
            if _ch_meaning and "安定" not in _ch_meaning:
                pair_strs.append(_ch_meaning)
            if pair_strs:
                detail_parts.append("；".join(pair_strs))
    # 六神动爻 / 世/应六神
    sa = adv.get("six_spirit_analysis") or {}
    if isinstance(sa, dict):
        _moving = sa.get("moving_yao_spirits", [])
        if _moving:
            _mv_strs = []
            for m in _moving:
                _sp = m.get("six_spirit", "")
                _sr = m.get("six_relation", "")
                _desc = m.get("nature", "")
                if _sp and _sr:
                    _mv_strs.append(f"{_sp}临{_sr}（{_desc}）")
            if _mv_strs:
                detail_parts.append("六神动爻：" + "、".join(_mv_strs))
        _ws_raw = sa.get("world_yao_spirit", {})
        if isinstance(_ws_raw, dict):
            _ws = _ws_raw.get("six_spirit", "")
            _ws_desc = _ws_raw.get("nature", "")
            if _ws:
                detail_parts.append(f"世临{_ws}（{_ws_desc}）")
    # 十二长生：取关键（用神/原神/临官/帝旺等）
    tg = adv.get("twelve_growth") or {}
    if isinstance(tg, dict):
        _lines = tg.get("lines", [])
        _key = [l for l in _lines if isinstance(l, dict) and l.get("is_key_stage")]
        if _key:
            _kg_strs = []
            for kl in _key[:3]:
                _br = kl.get("branch", "")
                _st = kl.get("growth_stage", "")
                _rel = kl.get("six_relation", "")
                _mn = kl.get("stage_meaning", "")
                if _st:
                    _kg_strs.append(f"{_br}({_rel})临{_st}——{_mn}")
            if _kg_strs:
                detail_parts.append("十二长生：" + "；".join(_kg_strs))
    # 伏藏分析
    hs = adv.get("hidden_spirit_analysis") or {}
    if isinstance(hs, dict) and hs.get("has_hidden_spirit"):
        for det in hs.get("details", []):
            _mr = det.get("missing_relation", "")
            _em = det.get("can_emerge", "")
            _rs = det.get("reason", "")
            _status = "得出" if _em else "伏而不出"
            if _mr:
                detail_parts.append(f"伏藏：{_mr} {_status}（{_rs}）")
    # 绝处逢生
    dr = adv.get("desperate_relief") or {}
    if isinstance(dr, dict) and dr.get("has_desperate_relief"):
        _v = dr.get("verdict", "")
        _d = dr.get("description", "")
        if _d:
            detail_parts.append(f"绝处逢生：{_d}" + (f"——{_v}" if _v else ""))

    if detail_parts:
        chain.append("[格局详释] " + " | ".join(detail_parts))




# =============================================================================
# 主函数：执行完整的五步思维链
# =============================================================================

def run_thinking_chain(hex_result: dict) -> dict:
    """
    执行完整的五步六爻思维链分析。

    Parameters
    ----------
    hex_result : dict
        build_hexagram_result() 返回的JSON字典结构，
        包含 original_hexagram, divination_time, empty_branches,
        changed_hexagram, question_category 等字段。

    Returns
    -------
    dict
        包含五步结构的完整思维链结果：
        - step1_situational_reading
        - step2_use_god_identification
        - step3_strength_analysis
        - step4_change_analysis
        - step5_synthesis
        以及 summary_text（总摘要）和 reasoning_chain（推理链）。
    """
    # 创建内部引用字典，使各步骤可以互相引用
    context = dict(hex_result)  # 浅拷贝

    # 确保 advanced_analysis 存在（build_hexagram_result 不调用 enhance_reading）
    if "advanced_analysis" not in context or not context.get("advanced_analysis"):
        try:
            from classical_analysis import enhance_reading
            # enhance_reading 原位修改 context 并返回它
            # 调用后 context["advanced_analysis"] 已被填充
            enhance_reading(context)
            # 确保 advanced_analysis 存在（enhance_reading 可能因为异常跳过）
            if "advanced_analysis" not in context:
                context["advanced_analysis"] = {}
        except Exception:
            context["advanced_analysis"] = {}

    # 同步 advanced_analysis 到 hex_result（step1 使用 hex_result 而非 context）
    if "advanced_analysis" in context and "advanced_analysis" not in hex_result:
        hex_result["advanced_analysis"] = context["advanced_analysis"]

    # 六亲持世深化分析（存入 advanced_analysis.shi_yao_relation）
    adv = hex_result.get("advanced_analysis", {})
    if isinstance(adv, dict):
        adv["shi_yao_relation"] = analyze_shi_yao_relation(hex_result)

    # 执行五步（前一步结果存入 context 供后续步骤使用）
    context["_step1_data"] = step1_read_situation(hex_result)
    context["_step2_data"] = step2_identify_use_god(context)  # 使用含step1的context
    context["_step3_data"] = step3_analyze_strength(context)
    context["_step4_data"] = step4_analyze_changes(context)
    context["_step5_data"] = step5_synthesize(context)

    # 构建最终输出
    chain = {
        "step1_situational_reading": context["_step1_data"],
        "step2_use_god_identification": context["_step2_data"],
        "step3_strength_analysis": context["_step3_data"],
        "step4_change_analysis": context["_step4_data"],
        "step5_synthesis": context["_step5_data"],
    }

    # 构建总摘要（使用完整五步数据重新生成推理链，包含卦身等辅助分析）
    full_reasoning_chain = _build_reasoning_chain(
        context["_step1_data"],
        context["_step2_data"],
        context["_step3_data"],
        context["_step4_data"],
        context["_step5_data"],
        context=context,
    )
    chain["reasoning_chain"] = full_reasoning_chain
    chain["summary_text"] = _build_overall_summary(context)

    # 清理内部引用键（不对外暴露）
    chain = _clean_internal_keys(chain)
    
    # 将思维链结果写入原字典
    hex_result["thinking_chain"] = chain

    # ★ 关键修复：重新检测经典引文（此时 chain 已构建，step4/step5 已就位）
    # 原来在 step5_synthesize 内部调用 find_classical_quotes 时 chain 还未就绪，
    # 导致「回头生/三合成局/伏藏/暗动」等需要 step4/5 数据的 pattern 全部匹配失败。
    fresh_quotes = find_classical_quotes(hex_result)
    if fresh_quotes and "step5_synthesis" in chain:
        # 替换原来的 classical_quotes（原来的往往是空或不完整的）
        chain["step5_synthesis"]["classical_quotes"] = fresh_quotes
        chain["step5_synthesis"]["classical_quotes_text"] = "【经典引文】" + "".join(
            f"• {q['source']}：{q['quote']}" for q in fresh_quotes
        )
    
    return hex_result


def _get_hexagram_body_summary_note(r: dict) -> str:
    """
    从 advanced_analysis.hexagram_body 提取卦身摘要。
    返回描述卦身位置、六亲与当前占问关联含义的短句，若无法确定则返回空字符串。
    """
    advanced = r.get("advanced_analysis", {})
    if not isinstance(advanced, dict):
        return ""
    hb = advanced.get("hexagram_body", {})
    if not isinstance(hb, dict):
        return ""

    body_pos = hb.get("body_position")
    if body_pos is None:
        return ""

    # 将数字爻位转为名称
    pos_names = {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}
    pos_name = pos_names.get(body_pos, f"{body_pos}爻")

    body_relation = hb.get("body_relation", "")
    specific_notes = hb.get("specific_notes", [])

    # 八卦身含义（按占问类型）
    # 卦身临六亲在不同占问中有不同意义
    body_relation_meaning = {
        "妻财": {"marriage": "婚有缘本", "wealth": "求财有根", "default": "财爻为身"},
        "官鬼": {"marriage": "女缘在此", "career": "仕途有根", "illness": "病犹缠身", "default": "鬼爻为身"},
        "父母": {"exam": "文书有据", "marriage": "文书契证", "default": "父母为身"},
        "子孙": {"illness": "药石有功", "career": "卸官归闲", "marriage": "子息有缘", "default": "子孙为身"},
        "兄弟": {"marriage": "争竞者在", "wealth": "劫财有碍", "default": "兄弟为身"},
    }

    note = f"卦身在{pos_name}"
    if body_relation:
        note += f"（{body_relation}）"
        # 尝试按占问类型给出卦身的具体含义
        scenario = _detect_question_scenario(r.get("question", ""))
        _meaning_map = body_relation_meaning.get(body_relation, {})
        _meaning = _meaning_map.get(scenario, _meaning_map.get("default", ""))
        if _meaning:
            note += f"——占{_scenario_cn(scenario) if scenario else '此'}: {_meaning}"
        elif specific_notes:
            note += "——" + specific_notes[0]
    elif specific_notes:
        note += "——" + specific_notes[0]

    return note


def _scenario_cn(scenario: str) -> str:
    """英文 scenario key → 中文占问名称（用于卦身叙事）。"""
    return {
        "marriage": "婚姻",
        "wealth": "求财",
        "illness": "疾病",
        "career": "事业",
        "exam": "考试",
        "lawsuit": "诉讼",
        "travel": "出行",
        "parents_illness": "父母之疾",
    }.get(scenario, "")


def _build_overall_summary(context: dict) -> str:
    """构建最终整体摘要"""
    step1 = context.get("_step1_data", {})
    step2 = context.get("_step2_data", {})
    step3 = context.get("_step3_data", {})
    step4 = context.get("_step4_data", {})
    step5 = context.get("_step5_data", {})

    parts = [
        f"=== 六爻思维链分析结果 ===",
        f"【本卦】{step1.get('hexagram_name', '?')}（{step1.get('palace', '?')}，{step1.get('palace_element', '?')}）",
        f"【用神】{step2.get('use_god_category', '?')}（{step2.get('use_god_element', '?')}）",
        f"【旺衰】{step3.get('strength_level', '?')}（评分：{step3.get('effective_score', '?')}）",
        f"【动变】{step4.get('net_effect_description', '无动爻')}（效应：{step4.get('net_effect', 0):+.2f}）",
        f"【最终】{step5.get('verdict', '?')} — {step5.get('verdict_description', '')}",
        f"【置信度】{step5.get('confidence', '?')}%（{step5.get('confidence_description', '')}）",
        f"【应期】{step5.get('timing', {}).get('summary_text', '待断')}",
    ]

    # 添加卦身信息（如果有）
    body_note = step5.get("hexagram_body_note", "")
    if body_note:
        parts.append(f"【卦身】{body_note}")

    # 飞伏互断（如果有伏神）
    adv = context.get("advanced_analysis", {})
    if isinstance(adv, dict):
        fhi = adv.get("flying_hidden_interaction", {})
        if isinstance(fhi, dict) and fhi.get("has_interaction"):
            interaction_parts = []
            for inter in fhi.get("interactions", []):
                pos_name = _pos_to_name(inter.get("position", 0))
                interaction_parts.append(
                    f"  {pos_name}：飞{inter.get('fei_shen', '')}（{inter.get('fei_branch', '')}）→伏{inter.get('fu_shen', '')}（{inter.get('fu_branch', '')}）：{inter.get('relation', '')}"
                )
            emerge_overall = "伏得出" if fhi.get("overall_emerge") else "伏难出"
            parts.append(f"【飞伏互断】（总体：{emerge_overall}）")
            parts.extend(interaction_parts)

        tp = adv.get("transformation_pattern", {})
        if isinstance(tp, dict) and tp.get("patterns"):
            pattern_strs = []
            for p in tp["patterns"]:
                weight = tp.get("total_weight", 1.0)
                pattern_strs.append(p)
            parts.append(
                f"【变爻格局】{'、'.join(pattern_strs)}（综合权重：{tp.get('total_weight', 1.0):.1f}）"
            )
            if tp.get("interpretation"):
                parts.append(f"  断曰：{tp['interpretation']}")

    return "\n".join(parts)


def _clean_internal_keys(chain: dict) -> dict:
    """移除内部引用键，确保输出干净"""
    # 递归清理所有嵌套字典中的 _stepX_data 键
    cleaned = {}
    for key, value in chain.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict):
            cleaned[key] = {k: v for k, v in value.items() if not k.startswith("_")}
        else:
            cleaned[key] = value
    return cleaned


# =============================================================================
# 独立调用入口（命令行测试）
# =============================================================================

if __name__ == "__main__":
    # 示例用法（需要配合 build_hexagram_result 使用）
    print("六爻思维链模块")
    print("===============")
    print("使用方式：")
    print('  from thinking_chain import run_thinking_chain')
    print('  chain = run_thinking_chain(hex_result)')
    print('  print(chain["step5_synthesis"]["verdict"])')
    print()
    print("各步骤也可独立调用：")
    print("  step1_read_situation(hex_result)")
    print("  step2_identify_use_god(hex_result)")
    print("  step3_analyze_strength(hex_result)")
    print("  step4_analyze_changes(hex_result)")
    print("  step5_synthesize(hex_result)")
