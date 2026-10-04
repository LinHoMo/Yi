# -*- coding: utf-8 -*-
"""古典断法增强：伏藏/暗动/进退/三合/十二长生/绝处逢生。"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

from yishu_core.symbols import SHENG_WO  # noqa: E402  原神（生我者）五行唯一真值源

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    ADVANCE_PAIRS,
    BRANCH_ELEMENTS,
    BREAK_PAIRS,
    CHONG_PAIRS,
    HE_PAIRS,
    KE_CYCLE,
    NAJIA_BRANCHES,
    RETREAT_PAIRS,
    SHENG_CYCLE,
    TOMB_MAP,
)

from chart_tables import (  # noqa: E402
    KE_WO,
    NAYIN_TABLE,
    NAYIN_TO_ELEMENT,
    SAN_HE,
    SHENG_WO,
    SIX_RELATIONS,
    TWELVE_GROWTH,
    TWELVE_GROWTH_STAGES,
    TWELVE_GROWTH_TABLES,
    YANG_STEMS,
    _QUESTION_KEYWORDS_USE_GOD,
)

from narrative_utils import (  # noqa: E402
    CLASSICAL_INTERPRETATIONS as CINTERP,
    PATTERN_NOTES_EXTRA,
    PATTERN_VERDICTS,
    _combined_strength,
    ctext,
    ctpl,
    element_strength_in_month,
    get_changed_hexagram_branch,
)
# element_strength_in_month / get_changed_hexagram_branch / _combined_strength 的
# 唯一实现都在 narrative_utils（各自逐字经快照对照）；本模块不再各留一份，
# 只按 __all__ 再导出给 effects / classical_analysis 的消费方。

from classical_enhancements_dufa import analyze_du_fa_du_jing  # noqa: E402
# 独发/独静域在 classical_enhancements_dufa.py 实现：该域只依赖 narrative_utils
# 断语素材，与其他增强域无耦合。此处再导出维持 __all__ 与 classical_analysis 的
# 消费方零改动；依赖单向，勿回调本模块。



# ======================================================================
# section: helpers & table utils
# ======================================================================


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
        return TWELVE_GROWTH_STAGES[idx], idx
    except ValueError:
        return None


def get_stages_of_interest(stage):
    """判断是否为关键阶段"""
    return stage in ("帝旺", "临官", "长生", "墓", "绝", "死", "沐浴")


def use_god_tomb_tags(yao_lines, use_god_branch, use_god_position,
                      day_branch, month_branch):
    """用神入墓结构标签（纯结构，不批吉凶）。

    《增刪卜易·隨鬼入墓章第三十》：「古有日墓、動墓、化墓之三墓。」
    〈入墓難克〉又申之：「且如木爲用神，金爲忌神，若在丑日占者，金入墓矣……
    卦中動出墓爻，亦向此推。金爻動而化丑亦是。」故用神入墓分四类，皆可机械判：

      入日墓 — 用神五行之墓支恰值日辰
      入月墓 — 恰值月建
      动墓   — 卦中另有动爻，其地支即用神之墓支（他爻动而引入墓）
      化墓   — 用神爻自身发动，其所化之支即用神之墓支

    只判结构，不作「凶/必死」一类断语（是否成凶，看旺衰与救应，见该章后文）。
    返回 {"label": 顿号连接或"不入墓", "tomb_branch": 墓支, "hits": [标签…]}。
    """
    elem = _branch_element(use_god_branch)
    tomb = TOMB_MAP.get(elem, "") if elem else ""
    if not tomb:
        return {"label": "不入墓", "tomb_branch": "", "hits": []}

    # 爻位在不同消费方手里可能是 int 或数字字符串（案例 JSON），归一后比较
    try:
        ug_pos = int(use_god_position)
    except (TypeError, ValueError):
        ug_pos = None

    hits = []
    if tomb == day_branch:
        hits.append("入日墓")
    if tomb == month_branch:
        hits.append("入月墓")
    # 动墓：他爻发动而墓用神（用神本爻值墓支属自坐墓，不在此列）
    for yao in yao_lines:
        if (yao.get("is_moving") and yao.get("earthly_branch") == tomb
                and yao.get("position") != ug_pos):
            hits.append("动墓")
            break
    # 化墓：用神发动，化出之支即其墓支（化出本支属伏吟，非入墓）
    for yao in yao_lines:
        if (yao.get("position") == ug_pos and yao.get("is_moving")
                and yao.get("changed_branch") == tomb
                and yao.get("changed_branch") != use_god_branch):
            hits.append("化墓")
            break
    return {"label": "、".join(hits) if hits else "不入墓",
            "tomb_branch": tomb, "hits": hits}


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
                # 原神 = 生我者，其五行映射唯一真值源在 core（SHENG_WO）
                if elem == SHENG_WO.get(palace_element):
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


def find_hexagram_body(world_is_yang, world_position):
    """
    安月卦身（《卜筮正宗》安月卦身诀唯一实现）。

    「阴世则从午月起，阳世还从子月生，欲得识其卦中意，从初数至世方真。」

    - 阳世（世爻为阳）：从初爻起子，二丑三寅四卯五辰六巳；
    - 阴世（世爻为阴）：从初爻起午，二未三申四酉五戌六亥。
    「从初数至世」= 数到世爻所在爻位，所得地支即月卦身支。

    Parameters
    ----------
    world_is_yang : bool
        世爻爻画是否为阳（阳世 True / 阴世 False）
    world_position : int
        世爻所在爻位 (1=初爻 ... 6=上爻；游魂=4、归魂=3)

    Returns
    -------
    str
        卦身地支（"子"~"亥"）；世爻位不在 1..6 返回空串。
    """
    if world_position < 1 or world_position > 6:
        return ""
    seq = ("子", "丑", "寅", "卯", "辰", "巳") if world_is_yang \
        else ("午", "未", "申", "酉", "戌", "亥")
    return seq[world_position - 1]


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




# ======================================================================
# section: hidden spir emergence
#  原 classical_rules_hidden.py
# ======================================================================


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
        reasons.append(ctpl("crt_008", '生' if SHENG_CYCLE.get(day_elem) == hid_elem else '同'))
    if SHENG_CYCLE.get(month_elem) == hid_elem or month_elem == hid_elem:
        emerge_score += 1
        reasons.append(ctpl("crt_009", '生' if SHENG_CYCLE.get(month_elem) == hid_elem else '同'))

    # 2. 飞神生伏神
    if SHENG_CYCLE.get(cov_elem) == hid_elem:
        emerge_score += 2
        reasons.append(ctext("cr_001"))

    # 3. 飞神旬空
    if cov_branch in empty_branches:
        emerge_score += 1
        reasons.append(ctext("cr_002"))

    # 4. 飞神月破
    if is_ba_zu_chong(cov_branch, month_branch):
        emerge_score += 1
        reasons.append(ctext("cr_003"))

    # 5. 飞神休囚
    cov_strength = element_strength_in_month(cov_elem, month_elem)
    if cov_strength in ("休", "囚", "死"):
        emerge_score += 1
        reasons.append(ctpl("crt_010", cov_strength))

    # 6. 伏克飞为出暴（伏神有力反克飞神，出暴为吉）
    if KE_CYCLE.get(hid_elem) == cov_elem:
        emerge_score += 3
        reasons.append(ctext("cr_004"))

    # --- 不得出条件 ---
    # 1. 伏神休囚被日月克
    hid_strength = element_strength_in_month(hid_elem, month_elem)
    if hid_strength in ("死", "囚"):
        emerge_score -= 2
        reasons.append(ctpl("crt_011", hid_strength))

    day_hid_strength = element_strength_in_month(hid_elem, day_elem)
    if day_hid_strength == "死":
        emerge_score -= 2
        reasons.append(ctext("cr_005"))

    # 2. 飞神旺相克伏神
    if KE_CYCLE.get(cov_elem) == hid_elem:
        cov_strength = element_strength_in_month(cov_elem, month_elem)
        if cov_strength in ("旺", "相"):
            emerge_score -= 3
            reasons.append(ctext("cr_006"))

    # 3. 伏神入墓
    tomb = TOMB_MAP.get(hid_elem, "")
    if tomb and day_branch == tomb:
        emerge_score -= 2
        reasons.append(ctpl("crt_012", tomb))

    # 4. 伏神逢绝
    stage_name, _ = get_twelve_growth_stage(hid_elem, day_branch) or (None, None)
    if stage_name == "绝":
        emerge_score -= 2
        reasons.append(ctext("cr_007"))

    # 5. 伏神旬空
    if hid_branch in empty_branches:
        emerge_score -= 1
        reasons.append(ctext("cr_008"))

    # 6. 伏神月破
    if is_ba_zu_chong(hid_branch, month_branch):
        emerge_score -= 2
        reasons.append(ctext("cr_009"))

    can_emerge = emerge_score > 0
    reason_text = "；".join(reasons) if reasons else "条件平淡"
    return can_emerge, reason_text


def analyze_hidden_spirits(result):
    """伏藏分析：检查六亲缺失，找出伏神/飞神及其得出/不得出。"""
    hex_info = result.get("original_hexagram", {})
    palace = hex_info.get("palace", "")
    palace_element = hex_info.get("palace_element", "")
    yao_lines = hex_info.get("yao_lines", [])

    if not palace or not yao_lines:
        return {"has_hidden_spirit": False, "details": [], "summary": ctext("cr_010")}

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
            "summary": ctext("cr_011"),
        }

    # 本宫首卦（纯卦）的地支
    # 宫殿名即为八卦名，其五行为 palace_element
    # 本宫卦上下皆为该八卦
    if palace not in NAJIA_BRANCHES:
        return {"has_hidden_spirit": True, "details": [], "summary": ctext("cr_012")}

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
            ctpl("crt_013", d['missing_relation'], d['hidden_spirit']['branch'], d['covering_spirit']['six_relation'], d['covering_spirit']['branch'], status)
        )

    return {
        "has_hidden_spirit": True,
        "details": details,
        "summary": "；".join(summary_parts),
    }


def analyze_hidden_spirit_emergence(result):
    """基于《卜筮正宗》伏神规则评分伏神得出/不得出。

    得出判据同《增删卜易·飛伏神章》「伏神有用者有六」：得日月生/旺相/飛神生/
    動爻生/日月動爻沖克飛神/飛神空破休囚墓絕；《黃金策》「空下伏神，易於引撥」。
    """
    hex_info = result.get("original_hexagram", {})
    palace = hex_info.get("palace", "")
    palace_element = hex_info.get("palace_element", "")
    yao_lines = hex_info.get("yao_lines", [])

    if not palace or not yao_lines:
        return {"has_hidden_spirit": False, "spirits": [], "summary": ctext("cr_013")}

    # 收集本卦已有的六亲
    existing_relations = set()
    for yao in yao_lines:
        rel = yao.get("six_relation", "")
        if rel and rel != "未知":
            existing_relations.add(rel)

    missing_relations = [r for r in SIX_RELATIONS if r not in existing_relations]

    if not missing_relations:
        return {"has_hidden_spirit": False, "spirits": [], "summary": ctext("cr_014")}

    # 本宫首卦地支
    if palace not in NAJIA_BRANCHES:
        return {"has_hidden_spirit": True, "spirits": [], "summary": ctext("cr_015")}

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

        # === 评分 ===
        emerge_score = 0
        emerge_reasons = []
        block_reasons = []

        # --- 得出条件 ---
        # 1. 日辰生扶伏神
        if SHENG_CYCLE.get(day_element) == hidden_element:
            emerge_score += 3
            emerge_reasons.append(ctpl("crt_030", day_branch, day_element, hidden_branch, hidden_element))
        elif day_element == hidden_element:
            emerge_score += 2
            emerge_reasons.append(ctpl("crt_056", day_branch))

        # 2. 月建生扶伏神
        if SHENG_CYCLE.get(month_element) == hidden_element:
            emerge_score += 2
            emerge_reasons.append(ctpl("crt_031", month_branch, month_element, hidden_branch))
        elif month_element == hidden_element:
            emerge_score += 1
            emerge_reasons.append(ctpl("crt_057", month_branch))

        # 3. 日冲飞神（冲开飞神）
        if is_ba_zu_chong(covering_branch, day_branch):
            emerge_score += 2
            emerge_reasons.append(ctpl("crt_032", covering_branch, day_branch, covering_branch))

        # 4. 月冲飞神
        if is_ba_zu_chong(covering_branch, month_branch):
            emerge_score += 1
            emerge_reasons.append(ctpl("crt_033", covering_branch, month_branch, covering_branch))

        # 5. 飞神旬空（空则不挡）
        if covering_branch in empty_branches:
            emerge_score += 2
            emerge_reasons.append(ctpl("crt_034", covering_branch))

        # 6. 飞神月破（破则不挡）
        if is_ba_zu_chong(covering_branch, month_branch):
            emerge_score += 2
            emerge_reasons.append(ctpl("crt_035", covering_branch))

        # 7. 飞神休囚无气
        cov_strength = element_strength_in_month(covering_element, month_element)
        if cov_strength in ("休", "囚", "死"):
            emerge_score += 1
            emerge_reasons.append(ctpl("crt_036", covering_branch, cov_strength))

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
            emerge_reasons.append(ctpl("crt_037", day_element, covering_element))
        if month_attacks_cov:
            emerge_score += 1
            emerge_reasons.append(ctpl("crt_038", month_element, covering_element))
        if moving_attacks_cov:
            emerge_score += 1
            emerge_reasons.append(ctext("cr_016"))

        # 9. 伏神旺相有气
        hid_strength = element_strength_in_month(hidden_element, month_element)
        if hid_strength == "旺":
            emerge_score += 2
            emerge_reasons.append(ctpl("crt_039", hidden_branch))
        elif hid_strength == "相":
            emerge_score += 1
            emerge_reasons.append(ctpl("crt_058", hidden_branch))

        # --- 不得出条件 ---
        # 1. 伏神被月日双克
        hid_day_strength = element_strength_in_month(hidden_element, day_element)
        if hid_strength == "死" and hid_day_strength == "死":
            emerge_score -= 4
            block_reasons.append(ctpl("crt_040", hidden_branch))

        # 2. 飞神旺相克伏神（飞克伏）
        if KE_CYCLE.get(covering_element) == hidden_element:
            if cov_strength in ("旺", "相"):
                emerge_score -= 3
                block_reasons.append(ctpl("crt_059", covering_branch, covering_element, hidden_branch, hidden_element))

        # 3. 伏神入墓
        tomb = TOMB_MAP.get(hidden_element, "")
        if tomb and (day_branch == tomb or month_branch == tomb):
            emerge_score -= 2
            block_reasons.append(ctpl("crt_041", hidden_branch, tomb))

        # 4. 伏神逢绝
        stage_name, _ = get_twelve_growth_stage(hidden_element, day_branch) or (None, None)
        if stage_name == "绝":
            emerge_score -= 2
            block_reasons.append(ctpl("crt_042", hidden_branch, day_branch))

        # 5. 伏神旬空
        if hidden_branch in empty_branches:
            emerge_score -= 2
            block_reasons.append(ctpl("crt_043", hidden_branch))

        # 6. 伏神月破
        if is_ba_zu_chong(hidden_branch, month_branch):
            emerge_score -= 2
            block_reasons.append(ctpl("crt_044", hidden_branch))

        # 7. 伏神休囚无气
        if hid_strength in ("休", "囚", "死"):
            emerge_score -= 1
            block_reasons.append(ctpl("crt_045", hidden_branch, hid_strength))

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
                ctpl("crt_046", missing_rel, hidden_branch, covering_branch, cov_strength, hid_strength, emerge_score, emerge_level)
            ),
        })

    if not spirits:
        return {"has_hidden_spirit": False, "spirits": [], "summary": ctext("cr_017")}

    summary_parts = [s["summary"] for s in spirits]
    return {
        "has_hidden_spirit": True,
        "spirits": spirits,
        "summary": "；".join(summary_parts),
    }


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
        return {"has_hidden_movement": False, "details": [], "summary": ctext("cr_018")}

    dt = result.get("divination_time", {})
    day_sb = dt.get("day_stem_branch", "")
    month_sb = dt.get("month_stem_branch", "")
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    if not day_branch:
        return {"has_hidden_movement": False, "details": [], "summary": ctext("cr_019")}

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
            # 旺相逢沖則暗動，休囚則日破（《增删卜易》卦例二句）——中间档梯度为工程映射
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
                desc = ctpl("crt_047", _pos_to_name(yao['position']), branch, day_branch)
            elif overall in ("旺", "相"):
                line_type = "暗动(旺相，七分布动)"
                effect_strength = "强"
                line_score = 0.7
                desc = (
                    ctpl("crt_060", _pos_to_name(yao['position']), branch, day_branch)
                )
            elif overall == "中和":
                line_type = "暗动(中和，中力)"
                effect_strength = "中"
                line_score = 0.4
                desc = (
                    ctpl("crt_079", _pos_to_name(yao['position']), branch, day_branch)
                )
            elif overall == "偏弱":
                line_type = "暗动(休囚，三分力)"
                effect_strength = "弱"
                line_score = 0.2
                desc = (
                    ctpl("crt_087", _pos_to_name(yao['position']), branch, day_branch)
                )
            else:  # "衰"
                line_type = "日破(月休逢冲，此爻无用)"
                effect_strength = "无"
                line_score = 0.0
                desc = (
                    ctpl("crt_088", _pos_to_name(yao['position']), branch, day_branch)
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
        return {"has_hidden_movement": False, "details": [], "summary": ctext("cr_020")}

    summary = "；".join(d["description"] for d in details)
    return {"has_hidden_movement": True, "details": details, "summary": summary}




# ======================================================================
# section: wandering/returning soul, monthly break, advance/retreat
#  原 classical_rules_patterns.py
# ======================================================================


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
            "meaning": CINTERP["youhun"]["text"],
            "travel": CINTERP["youhun_traits"]["text"],
            "residence": CINTERP["youhun_trait_home"]["text"],
            "mind": CINTERP["youhun_trait_mind"]["text"],
        },
        "归魂": {
            "meaning": CINTERP["guihun"]["text"],
            "travel": CINTERP["guihun_traits"]["text"],
            "residence": CINTERP["guihun_trait_home"]["text"],
            "mind": CINTERP["guihun_trait_mind"]["text"],
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
            "summary": ctpl("crt_014", generation, soul_data['meaning'], CINTERP['youhun_dynamic']['text'] if generation == '游魂' else CINTERP['guihun_dynamic']['text']),
            "score_adjustment": 0,  # 不改变评分——仅为断卦方向指引
        }

    return {
        "is_soul_hexagram": False,
        "soul_type": None,
        "meaning": CINTERP["not_youhun_guihun"]["text"],
        "travel": PATTERN_VERDICTS["no_youhun_guihun"],
        "residence": PATTERN_VERDICTS["no_youhun_guihun"],
        "mind": PATTERN_VERDICTS["no_youhun_guihun"],
        "summary": CINTERP["not_youhun_guihun_summary"]["text"],
        "score_adjustment": 0,
    }


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
        return {"has_monthly_break": False, "details": [], "summary": ctext("cr_018")}

    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    if not month_branch:
        return {"has_monthly_break": False, "details": [], "summary": ctext("cr_021")}

    day_element = _branch_element(day_branch)
    month_element = _branch_element(month_branch)
    empty_branches = result.get("empty_branches", [])

    details = []
    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        if not branch:
            continue

        if is_ba_zu_chong(branch, month_branch):
            # 月建沖之爲月破（《增删卜易·月破章》）；野鶴動破之辨：「目下𨿽破﹐出月則不破」——salvageable 即此辨
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
                    ctpl("crt_061", _pos_to_name(yao['position']), branch)
                )
            else:
                desc_parts.append(
                    ctpl("crt_062", _pos_to_name(yao['position']), branch)
                )

            if salvageable:
                desc_parts.append(ctpl("crt_063", day_branch))
            else:
                desc_parts.append(ctext("cr_022"))

            if is_moving:
                desc_parts.append(ctext("cr_023"))
            if is_empty:
                desc_parts.append(ctext("cr_024"))

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
        return {"has_monthly_break": False, "details": [], "summary": ctext("cr_025")}

    summary = "；".join(d["description"] for d in details)
    return {"has_monthly_break": True, "details": details, "summary": summary}


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
        return {"has_advance_retreat": False, "details": [], "summary": ctext("cr_027")}

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
                ctpl("crt_018", _pos_to_name(pos), orig_branch, chg_branch)
            )
        elif RETREAT_PAIRS.get(orig_branch) == chg_branch:
            advance_type = "化退"
            desc = (
                ctpl("crt_049", _pos_to_name(pos), orig_branch, chg_branch)
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
                    ctpl("crt_066", _pos_to_name(pos), orig_branch, chg_branch)
                )
            elif KE_CYCLE.get(chg_elem) == orig_elem:
                advance_type = "回头克"
                desc = (
                    ctpl("crt_081", _pos_to_name(pos), orig_branch, chg_branch)
                )
            elif SHENG_CYCLE.get(chg_elem) == orig_elem:
                advance_type = "回头生"
                desc = (
                    ctpl("crt_090", _pos_to_name(pos), orig_branch, chg_branch)
                )
            elif SHENG_CYCLE.get(orig_elem) == chg_elem:
                advance_type = "化泄"
                desc = (
                    ctpl("crt_093", _pos_to_name(pos), orig_branch, chg_branch)
                )
            else:
                advance_type = "无进退"
                desc = (
                    ctpl("crt_094", _pos_to_name(pos), orig_branch, chg_branch)
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
        return {"has_advance_retreat": False, "details": [], "summary": ctext("cr_028")}

    summary = "；".join(d["description"] for d in details)
    return {"has_advance_retreat": True, "details": details, "summary": summary}




# ======================================================================
# section: triple combo / broken combo
#  原 classical_rules_combo.py
# ======================================================================


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

    # 各五行入墓地支：真值源在内核 TOMB_MAP（模块顶部已 import），禁止就地重定义遮蔽。

    issues = []

    for b in branches:
        # 检查日冲
        if CHONG_MAP.get(b) == day_branch:
            issues.append(ctpl("crt_048", b))
        elif CHONG_MAP.get(b) == month_branch:
            issues.append(ctpl("crt_064", b))

    # 检查合局五行是否整体入墓于日辰
    target_element = combo_dict.get("element", "")
    if target_element and day_branch == TOMB_MAP.get(target_element, ""):
        issues.append(ctpl("crt_015", day_branch))

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
        return {"has_triple_combo": False, "details": [], "summary": ctext("cr_018")}

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
                # 缺一个，看日/月是否有（虛一待用：《增删卜易》升遷例「欲成三合，因少卯字，明年卯月必升，此乃虛一待用」）
                missing = [b for b in combo_branches if not pos_map[b]][0]
                if missing in (day_branch, month_branch):
                    # 由日/月补齐
                    valid_positions = []
                    for b in combo_branches:
                        if pos_map[b]:
                            valid_positions.append(pos_map[b][0])
                        elif b == day_branch:
                            valid_positions.append(ctpl("crt_095", day_branch))
                        elif b == month_branch:
                            valid_positions.append(ctpl("crt_097", month_branch))

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
                            ctpl("crt_080", ''.join(combo_branches), combo_element, day_branch, month_branch)
                        )
                        if _broken["status"] == "破局":
                            _desc += ctpl("crt_017", '；'.join(_broken['issues']))
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
            ftype = ctpl("crt_065", moving_count, hidden_count, static_count)
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
            ctpl("crt_002", ''.join(combo_branches), combo_element, _pos_to_name(p1), _pos_to_name(p2), _pos_to_name(p3), ftype)
        )

        if completeness == "完整":
            desc += ctpl("crt_016", combo_element)
        elif completeness == "待用（需冲引发）":
            desc += PATTERN_NOTES_EXTRA["static_he_wait"]

        if _broken["status"] == "破局":
            desc += ctpl("crt_089", '；'.join(_broken['issues']))

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
        return {"has_triple_combo": False, "details": [], "summary": ctext("cr_026")}

    summary = "；".join(d["description"] for d in details)
    return {"has_triple_combo": True, "details": details, "summary": summary}



# ======================================================================
# section: twelve growth / desperate relief
#  原 classical_rules_growth.py
# ======================================================================


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
                "summary": ctext("cr_018"), "key_lines": [], "weak_lines": []}

    dt = result.get("divination_time", {})
    day_sb = dt.get("day_stem_branch", "")
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    if not day_branch:
        return {"day_branch": "", "day_element": "", "lines": [],
                "summary": ctext("cr_019"), "key_lines": [], "weak_lines": []}

    day_element = _branch_element(day_branch)
    empty_branches = result.get("empty_branches", [])

    # 关键阶段含义
    stage_meaning = {
        "长生": CINTERP["twelve_changsheng"]["长生"]["text"],
        "沐浴": CINTERP["twelve_changsheng"]["沐浴"]["text"],
        "冠带": CINTERP["twelve_changsheng"]["冠带"]["text"],
        "临官": CINTERP["twelve_changsheng"]["临官"]["text"],
        "帝旺": CINTERP["twelve_changsheng"]["帝旺"]["text"],
        "衰": CINTERP["twelve_changsheng"]["衰"]["text"],
        "病": CINTERP["twelve_changsheng"]["病"]["text"],
        "死": CINTERP["twelve_changsheng"]["死"]["text"],
        "墓": CINTERP["twelve_changsheng"]["墓"]["text"],
        "绝": CINTERP["twelve_changsheng"]["绝"]["text"],
        "胎": CINTERP["twelve_changsheng"]["胎"]["text"],
        "养": CINTERP["twelve_changsheng"]["养"]["text"],
    }

    lines_out = []
    key_lines = []
    weak_lines = []

    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        elem = _branch_element(branch)
        stage_name, _ = get_twelve_growth_stage(elem, day_branch) or (None, None)
        is_key = get_stages_of_interest(stage_name)

        is_weak_stage = stage_name in ("死", "墓", "绝")
        is_strong_stage = stage_name in ("帝旺", "临官", "长生")

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
            "growth_stage": stage_name,
            "is_key_stage": is_key,
            "stage_meaning": stage_meaning.get(stage_name, ""),
        })

    # 汇总
    parts = []
    if key_lines:
        key_desc = "、".join(f"{_pos_to_name(p)}{_find_stage_at(lines_out, p)}"
                            for p in key_lines)
        parts.append(ctpl("crt_019", key_desc))
    if weak_lines:
        weak_desc = "、".join(f"{_pos_to_name(p)}{_find_stage_at(lines_out, p)}"
                             for p in weak_lines)
        parts.append(ctpl("crt_020", weak_desc))

    summary = "；".join(parts) if parts else PATTERN_VERDICTS["yao_states_calm"]

    return {
        "day_branch": day_branch,
        "day_element": day_element,
        "lines": lines_out,
        "summary": summary,
        "key_lines": key_lines,
        "weak_lines": weak_lines,
    }


def analyze_desperate_relief(result):
    """
    绝处逢生分析：当用神在日辰处逢"绝"或"死"地时，检查原神是否发动来生。
    （《增删卜易》：「世與用神或絕於日或化絕，若得日月動爻生者，謂之絕處逢生」）

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
        out["verdict"] = PATTERN_VERDICTS["jue_chu_feng_sheng"]
        out["score_modifier"] = 2.0
        out["description"] = (
            ctpl("crt_003", use_god_element, use_god_branch, stage, yuan_shen_element, yuan_shen_combined)
        )
    elif yuan_shen_moving and not yuan_shen_empty and not yuan_shen_month_break:
        out["verdict"] = PATTERN_VERDICTS["jue_chu_feng_sheng_weak_yuan"]
        out["score_modifier"] = 0.5
        out["description"] = (
            ctpl("crt_021", use_god_element, use_god_branch, stage, yuan_shen_element, yuan_shen_combined)
        )
    elif yuan_shen_present and not yuan_shen_empty and not yuan_shen_month_break:
        out["verdict"] = PATTERN_VERDICTS["jue_wait_yuan"]
        out["score_modifier"] = 0.2
        out["description"] = (
            ctpl("crt_050", use_god_element, use_god_branch, stage, yuan_shen_element)
        )
    elif not yuan_shen_present:
        out["verdict"] = PATTERN_VERDICTS["jue_no_save"]
        out["score_modifier"] = -0.8
        out["description"] = (
            ctpl("crt_067", use_god_element, use_god_branch, stage, yuan_shen_element)
        )
    else:
        # 原神 present but empty or month-broken
        out["verdict"] = PATTERN_VERDICTS["jue_no_save"]
        out["score_modifier"] = -0.8
        out["description"] = (
            ctpl("crt_068", use_god_element, use_god_branch, stage, yuan_shen_element, ctext('cr_031') if yuan_shen_empty else ctext('cr_032'))
        )

    return out


# 实现在 effects.py、由本模块按 PEP 562 惰性再导出的名字（唯一一份清单：
# __all__ 从这里展开，避免同一串名字在文件里写两遍）。
_EFFECTS_REEXPORT = (
    "analyze_clash_harmony",
    "analyze_repetition",
    "analyze_repetition_deep",
    "analyze_hexagram_body",
    "analyze_element_strength",
    "analyze_three_punishments",
    "analyze_day_month_bonding",
    "analyze_six_breaks",
    "analyze_officer_tomb",
    "analyze_transformation_pattern",
    "analyze_flying_hidden_interaction",
)


__all__ = [
    # narrative_utils (re-exported)
    "ctext",
    "ctpl",
    # classical_support.py helpers
    "spirit_yin_yang_factor",
    "analyze_nayin",
    "_branch_element",
    "determine_six_relation",
    "is_ba_zu_he",
    "is_ba_zu_chong",
    "is_ba_zu_po",
    "element_strength_in_month",
    "get_twelve_growth_stage",
    "get_stages_of_interest",
    "use_god_tomb_tags",
    "get_changed_hexagram_branch",
    "get_month_strength_description",
    "_pos_to_name",
    "_combined_strength",
    "_strength_score",
    "_find_stage_at",
    "_find_use_god_positions",
    "_get_use_god_strength_level",
    "_score_fanyin",
    "_score_fuyin",
    "find_hexagram_body",
    "_relation_element",
    "_element_to_relation",
    "_infer_use_god_category",
    # hidden
    "_evaluate_hidden_spirit_emergence",
    "analyze_hidden_spirits",
    "analyze_hidden_spirit_emergence",
    "analyze_hidden_movement",
    # patterns
    "analyze_wandering_returning_soul",
    "analyze_monthly_break",
    "analyze_advance_retreat",
    # combo
    "_check_broken_combo",
    "analyze_triple_combo",
    # growth
    "analyze_twelve_growth",
    "analyze_desperate_relief",
    "analyze_du_fa_du_jing",
    # effects (re-exported lazily from effects.py)
    *_EFFECTS_REEXPORT,
]

# ---------------------------------------------------------------------------
# PEP 562: lazy import to avoid circular dependency with effects.py.
# effects.py imports helpers that now live in this module, so a top-level
# "from effects import …" would create an import cycle.
# ---------------------------------------------------------------------------
def __getattr__(name):
    if name in _EFFECTS_REEXPORT:
        try:
            return globals()[name]
        except KeyError:
            pass
        import effects as _effects_mod
        val = getattr(_effects_mod, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
