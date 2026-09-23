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
    SHENG_CYCLE,
    STEM_ELEMENTS,
    TOMB_MAP,
)

from classical_tables import KE_WO, NAYIN_TABLE, NAYIN_TO_ELEMENT, SHENG_WO, TWELVE_GROWTH_STAGES, TWELVE_GROWTH_TABLES, YANG_STEMS, _QUESTION_KEYWORDS_USE_GOD

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


def is_ba_zu_po(b1, b2):
    """判断两地支是否六破"""
    for a, b in BREAK_PAIRS:
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
    """变卦第 position 爻（1=初爻）的纳甲地支——实现已上收内核，此处仅保留旧名。"""
    return najia_branch(changed_hex_name, position)


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


def _pos_to_name(pos):
    """位置数字转为中文名称（1→初爻, 6→上爻）"""
    names = {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}
    return names.get(pos, f"{pos}爻")


def g_day_cn(element):
    """五行中文名辅助"""
    return element


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


def _strength_score(level):
    """
    将旺衰等级转换为数值评分（用于进退神量化）。
    旺=5, 相=4, 中和=3, 偏弱=2, 衰=0
    """
    return {"旺": 5, "相": 4, "中和": 3, "偏弱": 2, "衰": 0}.get(level, 2)


def _find_stage_at(lines_out, position):
    """根据位置找出对应阶段名称"""
    for l in lines_out:
        if l["position"] == position:
            return l["growth_stage"]
    return ""


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


def _infer_use_god_category(question):
    """从问题文本推断用神类别（简化版），默认返回世爻"""
    if not question:
        return "世爻"
    for relation, keywords in _QUESTION_KEYWORDS_USE_GOD.items():
        for kw in keywords:
            if kw in question:
                return relation
    return "世爻"

