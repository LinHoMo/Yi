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

from classical_enhancements_dufa import (  # noqa: E402
    analyze_du_fa_du_jing,
    analyze_luandong,
    attach_luandong_looks,
)
from classical_enhancements_zhugui import analyze_zhu_gui_shang_shen  # noqa: E402
from classical_enhancements_menlei import analyze_menlei_dongjing  # noqa: E402
from classical_enhancements_fushi import huozhulin_fushi_tags  # noqa: E402
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
            "tomb_branch": tomb, "hits": hits,
            "yimao_corrections": yimao_tomb_corrections(
                yao_lines, ug_pos, tomb, day_branch, month_branch)}


def yimao_tomb_corrections(yao_lines, ug_pos, tomb, day_branch, month_branch):
    """化墓三修正（《易冒》随墓章 源L526「火官戌墓，辰日冲而成伪，戌月实而作真，戌空自伪，戌破非真」/L528/L530）——**只出结构修正标记，不改吉凶**。

    【OPT-yimao_dz-05，2026-10-07 新增】引擎原只依《卜筮正宗》判「是否入墓」，
    《易冒》另给三条**修正/限定**，本函数把它们转成可机械判的结构标记：

      ① **化爻墓冲破成伪**（源L526 逐字）：「化爻随鬼入墓，与命墓世墓无差等，而有真伪，
         火官戌墓，辰日冲而成伪，戌月实而作真，戌空自伪，戌破非真。」
         → 化墓遇**日辰冲**该墓支 → 标记 `化墓逢冲`（书源谓之「成伪」）。
         本函数只标「逢冲」这一**结构事实**；「成伪/作真」的吉凶断语**不入结构层**
         （SKILL.md 铁律一），由 narrate 按 src 回指原文自取。
      ② **官衰则减**（源L528 注）：「然遇鬼旺则凶，官衰则减，视世墓化墓则轻尔。」
         → 本条是**程度递减**，属半吉凶判断。本层**只登记出处、不实现**：
         「官衰」需先定「官」在用神入墓语境下的所指（用神本身即官鬼？或另指官爻），
         口径未裁定前实现即属 §四.3 禁止的凭空造判据。见 `unimplemented` 字段。
      ③ **避患占空破反吉**（《易冒》源L530 逐字）：「若避患、忧害、防非，见空破而祸消，
         祸消而随墓何凶也。」→ 占问类属**避患/忧害/防非**者，见空破则**减凶**。
         本层只标 `避患占见空破` 这一**结构事实**（问类命中 + 该墓支逢空/破），
         「反吉」的断语不入结构层。

    铁律四.3 说明：①③ 是**可机械判的结构限定**，本轮落地为**只读标记**（不参与
    step5 方向聚合、不改 final_score/verdict），故读数应为零漂移；
    ② 因口径未裁定**明确不实现**并登记理由，不做半吊子实现。
    """
    out = {
        "化墓逢冲": False,       # ① 化爻墓被日辰冲（书源谓之「成伪」）
        "避患占见空破": False,   # ③ 避患类占 + 该墓逢空破
        "适用问类": [],          # 由调用方按问类填入（本函数不猜问类）
        "unimplemented": [
            {"修正": "官衰则减（《易冒》源L528「然遇鬼旺则凶，官衰则减，视世墓化墓则轻尔」）",
             "理由": "「官衰」在用神入墓语境下所指未裁定（用神本身即官鬼？或另指官爻？），"
                     "且「减凶」属程度吉凶判断；按 SKILL.md，"
                     "口径未裁定前不实现，只登记出处。"},
        ],
        "src": {
            "化墓逢冲": "data/sources/yimao_dz.dz.txt:526",
            "官衰则减": "data/sources/yimao_dz.dz.txt:528",
            "避患占见空破": "data/sources/yimao_dz.dz.txt:530",
        },
    }
    if not tomb or not ug_pos:
        return out
    yao_list = yao_lines if isinstance(yao_lines, (list, tuple)) else []
    # CHONG_PAIRS 只存**单向**对（(辰,戌) 有、(戌,辰) 无），故按无向判：两向皆查。
    chong = lambda a, b: ((a, b) in CHONG_PAIRS) or ((b, a) in CHONG_PAIRS)  # noqa: E731
    # ① 化墓逢冲：化墓爻自身发动、化出墓支，而日辰冲该墓支
    for yao in yao_list:
        if (yao.get("position") == ug_pos and yao.get("is_moving")
                and yao.get("changed_branch") == tomb):
            if day_branch and chong(tomb, day_branch):
                out["化墓逢冲"] = True
            break
    # ③ 避患占见空破：墓支逢日辰之空或逢冲（空/破皆为「见空破」）
    if day_branch and chong(tomb, day_branch):
        # 该位由调用方结合问类判定是否属「避患/忧害/防非」类；此处只报「见冲」
        out["_见冲"] = True
    return out


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
    # 断语/引文进 data/rules/verdict_texts.json#classical_rules_notes（§三），
    # 代码只留算法与键名（缺陷 E 修复，2026-10-09；文本逐字不变）。
    quote = ctext("cr_052")

    # 根据用神旺衰定基调
    if use_god_strength == "旺":
        score -= 0.1
        parts.append(ctext("cr_053"))
    elif use_god_strength == "衰":
        score -= 0.5
        parts.append(ctext("cr_054"))
        quote = ctext("cr_055")
    else:
        score -= 0.3
        parts.append(ctext("cr_056"))

    # 根据 scope 追加
    if scope == "世爻":
        score -= 0.3
        parts.append(ctext("cr_057"))
        quote = ctext("cr_058")
    elif scope == "用神":
        score -= 0.4
        parts.append(ctext("cr_059"))
    elif scope == "内卦":
        score -= 0.2
        parts.append(ctext("cr_060"))
    elif scope == "外卦":
        score -= 0.2
        parts.append(ctext("cr_061"))

    # 卦级别额外
    if level == "卦":
        score -= 0.2
        parts.append(ctext("cr_062"))

    interpretation = "；".join(parts) if parts else ctext("cr_063")
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
    # 断语进 data 层（缺陷 E 修复，2026-10-09；文本逐字不变）
    quote = ctext("cr_064")

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
        parts.append(ctext("cr_065"))
        quote = ctext("cr_066")
    else:
        score -= 0.2
        parts.append(ctext("cr_067"))

    # 用神伏吟
    use_positions = _find_use_god_positions(result)
    if any(p in changed_lines for p in use_positions):
        score -= 0.4
        parts.append(ctext("cr_068"))

    interpretation = "；".join(parts) if parts else ctext("cr_069")
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
                                       covering_yao, moving_elems=None):
    """
    评估伏神得出/不得出。
    
    得出（吉）：
      - 日/月生伏神
      - 日/月与伏神同五行（持之）
      - 飞神生伏神
      - 飞神被月支冲（作"飞神月破"算）
      **六款落支逐条核对（第五十三批读代码所得，历批补齐，现状截至第一百五十六批）**：
      款一 日月生扶→有（crt_008/crt_009）；款二 伏神旺相→有（crt_039 旺／crt_058 相，
      第六十二批并一前补，量级沿用原报告路值）；款三 飞神生伏→有（cr_001）；
      款四 动爻生伏→有（crt_009c，第五十批补）；款五 日月动爻冲克飞神→齐
      （crt_009b 日冲／crt_009d 动爻冲克／crt_009e 日克／crt_009f 月克，末两支第五十三批补）；
      款六 飞神空破休囚墓绝→齐（cr_002 空／cr_003 月破／crt_010 休囚／crt_009g 入墓／crt_009h 逢绝，末两支第六十五批补）。
      **#17 已闭**（第六十二批）：报告路 analyze_hidden_spirit_emergence 删掉自套条件改为
      调用本函数，两路不可能再判相反（对拍 208 项一致、0 分歧）；本段旧记载「款二本函数缺…
      属 #17 两路未并一的剩余分歧」是并一前历史，按实改正——那条注记曾在并一后继续挂了很久。
      旧版本这段把"日/月/动爻冲克飞神"列为已实现，而当时"克"三支全缺，属自述超出实现
      （第四十九批改正后仍缺两支，本批补齐）。
      旁证核对：《卜筮全书》源L5524 逐字「六冲最紧，六害不能出」——下面加分项里没有一条
      以六害作开门手段，与此一致。
      - 飞神旬空、月破、休囚
    
    不得出（凶）：
      - 伏神休囚被日月克
      - 飞神旺相克伏神
      - 伏神入墓、逢绝
      - 伏神旬空、月破
    """
    emerge_score = 0
    emerge_reasons: list[str] = []
    block_reasons: list[str] = []
    hid_strength_pos = element_strength_in_month(hid_elem, month_elem)

    # --- 得出条件 ---
    # 1. 日/月生伏神
    if SHENG_CYCLE.get(day_elem) == hid_elem or day_elem == hid_elem:
        emerge_score += 2
        emerge_reasons.append(ctpl("crt_008", '生' if SHENG_CYCLE.get(day_elem) == hid_elem else '同'))
    if SHENG_CYCLE.get(month_elem) == hid_elem or month_elem == hid_elem:
        emerge_score += 1
        emerge_reasons.append(ctpl("crt_009", '生' if SHENG_CYCLE.get(month_elem) == hid_elem else '同'))

    # 2. 飞神生伏神
    if SHENG_CYCLE.get(cov_elem) == hid_elem:
        emerge_score += 2
        emerge_reasons.append(ctext("cr_001"))

    # 3. 飞神旬空
    if cov_branch in empty_branches:
        emerge_score += 1
        emerge_reasons.append(ctext("cr_002"))

    # 4. 飞神月破
    if is_ba_zu_chong(cov_branch, month_branch):
        emerge_score += 1
        emerge_reasons.append(ctext("cr_003"))

    # 4b. 日辰冲飞（《增删卜易》源L1055 逐字「伏神得遇日月动爻冲克飞神者五也」的"日冲"半支）
    #     旧实现只有月支冲飞，日支冲飞漏了——与同文件 analyze_hidden_spirit_emergence
    #     （报告路）实测 16 条里分歧 3 条，reg_05 妻财被判"难出"而报告路给"极易出"，
    #     正是这一缺支所致（第四十九批实测）。动爻冲克飞仍缺（本函数拿不到动爻）。
    if cov_branch and day_branch and is_ba_zu_chong(cov_branch, day_branch):
        emerge_score += 1
        emerge_reasons.append(ctpl("crt_009b", day_branch, cov_branch))

    # 5. 飞神休囚
    cov_strength = element_strength_in_month(cov_elem, month_elem)
    if cov_strength in ("休", "囚", "死"):
        emerge_score += 1
        emerge_reasons.append(ctpl("crt_010", cov_strength))

    # 5b/5c. 动爻一支的两半（《增删卜易》源L1055 逐字「伏神得动爻生者四」
    #        与「伏神得遇日月动爻冲克飞神者五也」）——旧判据路两款全缺，
    #        报告路却有，故同一盘两路相反（第五十批对拍量出 3 条）。
    for me in (moving_elems or []):
        if not me:
            continue
        if SHENG_CYCLE.get(me) == hid_elem:
            emerge_score += 1
            emerge_reasons.append(ctpl("crt_009c", me, hid_elem))
        if is_ba_zu_chong(me, cov_branch) or KE_CYCLE.get(me) == cov_elem:
            emerge_score += 1
            emerge_reasons.append(ctpl("crt_009d", me, cov_branch, cov_elem))

    # 4c/4d. 款五的「日月克飞」两支（《增删卜易》源L1055 逐字
    #        「伏神得遇日月动爻冲克飞神者五也」）：旧判据路只落了"冲"，
    #        "克"两支漏了——报告路（analyze_hidden_spirit_emergence）却有，
    #        同一盘两路相反即由此来（第五十二批前的 16 项对拍量出 3 条分歧）。
    #        动爻一支仍由下面 moving_elems 循环承担。
    if day_elem and cov_elem and KE_CYCLE.get(day_elem) == cov_elem:
        emerge_score += 1
        emerge_reasons.append(ctpl("crt_009e", day_branch, cov_branch))
    if month_elem and cov_elem and KE_CYCLE.get(month_elem) == cov_elem:
        emerge_score += 1
        emerge_reasons.append(ctpl("crt_009f", month_branch, cov_branch))

    # 5d. 款二 伏神旺相（《增删卜易》源L1055 逐字「伏神旺相者二也」——并一前旧判据路缺这一款
    #    （只在报告路自套的那一套里），第六十二批并一前补齐；量级沿用原报告路值，
    #    属引擎设计而非书写数字（书只给条件不给分值，见函数头 #17 已闭注记）。
    if hid_strength_pos in ("旺", "相"):
        emerge_score += 2 if hid_strength_pos == "旺" else 1
        emerge_reasons.append(ctpl("crt_039" if hid_strength_pos == "旺" else "crt_058", hid_branch))

    # 5e/5f. 款六的「飞神墓·绝」两支（《增删卜易》源L1055 逐字「伏神得遇飞神空破休囚墓绝者六也」）：
    #        旧判据路只落了 空／破／休囚 三支，墓、绝 两支缺——本批补齐，量级沿用同支的 +1。
    cov_tomb = TOMB_MAP.get(cov_elem, "")
    if cov_tomb and day_branch == cov_tomb:
        emerge_score += 1
        emerge_reasons.append(ctpl("crt_009g", cov_branch, cov_tomb))
    cov_stage, _ = get_twelve_growth_stage(cov_elem, day_branch) or (None, None)
    if cov_stage == "绝":
        emerge_score += 1
        emerge_reasons.append(ctpl("crt_009h", cov_branch, cov_elem))

    # 6. 伏克飞为出暴（伏神有力反克飞神，出暴为吉）
    if KE_CYCLE.get(hid_elem) == cov_elem:
        emerge_score += 3
        emerge_reasons.append(ctext("cr_004"))

    # --- 不得出条件 ---
    # 【书据边界，第六十七批取证后停在明处】《增删卜易》源L1058 逐字「伏神被日月冲克者二也」
    #   里的"克"，本器目前只在伏神休囚语境下扣分；是否扩到"旺相伏神被日月克也扣"，两条检索都不支持：
    #   ① 《增删卜易》源L2787 逐字「若伏而旺相，或得日月冲去飞神，生起伏神，准登科及第」——书上对伏而旺相判**吉**；
    #   ② 本仓案例里"伏藏＋旺相/有气"六条（ZS014/015/016/030/HO002/HO005）中，
    #      判不得出的三条（ZS014/ZS015/ZS030）给的都是**伏而被飞神克／绝于飞神**，
    #      没有一例是"伏神旺相而被日月克仍判不得出"。
    #   故不扩写；要扩须先有一条那样的书转真例。（款四的"绝于飞爻"已由 ZS015
    #   「财爻伏藏且绝于飞神亥水」这一型支撑，第六十六批①把飞神纳入墓绝位置。）
    # 1. 伏神休囚被日月克
    hid_strength = element_strength_in_month(hid_elem, month_elem)
    if hid_strength in ("死", "囚"):
        emerge_score -= 2
        block_reasons.append(ctpl("crt_011", hid_strength))

    day_hid_strength = element_strength_in_month(hid_elem, day_elem)
    if day_hid_strength == "死":
        emerge_score -= 2
        block_reasons.append(ctext("cr_005"))

    # 2. 飞神旺相克伏神
    if KE_CYCLE.get(cov_elem) == hid_elem:
        cov_strength = element_strength_in_month(cov_elem, month_elem)
        if cov_strength in ("旺", "相"):
            emerge_score -= 3
            block_reasons.append(ctext("cr_006"))

    # 3. 款四 伏神墓绝于日月飞爻（《增删卜易》源L1058 逐字「伏神墓绝于日月飞爻者四也」）
    #    旧实现把这一款拆成「日辰入墓 −2」与「日辰逢绝 −2」两条各扣一次＝同一款重复计分，
    #    且「月建」「飞爻」两个位置全缺。现合为一条：三处任一命中只扣一次，理由逐项列出。
    _tomb_hid = TOMB_MAP.get(hid_elem, "")
    _mu_jue = []
    for _b, _lbl in ((day_branch, "日辰"), (month_branch, "月建"), (cov_branch, "飞神")):
        if not _b:
            continue
        if _tomb_hid and _b == _tomb_hid:
            _mu_jue.append(f"{_lbl}为墓({_tomb_hid})")
        _st, _ = get_twelve_growth_stage(hid_elem, _b) or (None, None)
        if _st == "绝":
            _mu_jue.append(f"{_lbl}处绝")
    if _mu_jue:
        emerge_score -= 2
        block_reasons.append(ctpl("crt_009k", "、".join(_mu_jue)))

    # 4b. 款二「伏神被日月冲克」里的**日辰冲**一支（《增删卜易》源L1058 逐字
    #     「伏神被日月冲克者二也」）：旧实现只有月破（`cr_009`），日辰冲整支缺；量级对齐月破 −2。
    if hid_branch and day_branch and is_ba_zu_chong(hid_branch, day_branch):
        emerge_score -= 2
        block_reasons.append(ctpl("crt_009l", day_branch, hid_branch))

    # 5. 伏神旬空
    if hid_branch in empty_branches:
        emerge_score -= 1
        block_reasons.append(ctext("cr_008"))

    # 6. 伏神月破
    if is_ba_zu_chong(hid_branch, month_branch):
        emerge_score -= 2
        block_reasons.append(ctext("cr_009"))

    can_emerge = emerge_score > 0
    reason_text = "；".join(emerge_reasons + block_reasons) if (emerge_reasons or block_reasons) else "条件平淡"
    return can_emerge, reason_text, emerge_score, emerge_reasons, block_reasons


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
        can_emerge, reason, _escore, _ereasons, _breasons = _evaluate_hidden_spirit_emergence(
            hidden_element, hidden_branch, covering_relation, covering_branch,
            covering_element, month_branch, day_branch, month_element, day_element,
            empty_branches, yao_by_position.get(hidden_pos, {}),
            moving_elems=[_branch_element(y.get("earthly_branch", ""))
                          for y in yao_lines if y.get("is_moving")]
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
            "emerge_score": _escore,
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
    # 【确定性红线】必须是**有序**容器：旧实现用 `set()`，下面的 `moving_elems`
    # 循环据此追加 emerge_reasons，迭代顺序随 PYTHONHASHSEED 变（str 哈希随进程
    # 随机化），于是同一卦在不同进程里产出不同次序的「取得出」理由串。
    # 实测：同一案例（小畜，动爻五六）PYTHONHASHSEED=0 与 =1 得到顺序相反的
    # emerge_reasons，金标准指纹因此虚报行为漂移（第两百六十四批查获）。
    # 按爻位（下→上）固定顺序，与全仓「爻序自下而上」的约定同向。
    moving_branches = []
    for yao in sorted(yao_lines, key=lambda y: y.get("position", 0)):
        if yao.get("is_moving", False):
            _b = yao.get("earthly_branch", "")
            if _b and _b not in moving_branches:
                moving_branches.append(_b)

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

        # === 评分：唯一真值源在判据路 _evaluate_hidden_spirit_emergence（第六十二批并一）===
        #   此前两路各写一套条件与权重（报告路有款二伏神旺相、缺款三飞神生伏与伏克飞；
        #   判据路反之），同一盘可判相反——第五十二批前 16 项对拍量出 3 条分歧即由此来。
        #   现在**得出与否只由判据路判定**，本路只把分值映射成档位与文案。
        #   数字口径如实记：《增删卜易》源L1055 逐字「伏神有用者有六：伏神得日月生者一也；伏神旺相者二也；
        #   伏神得飞神生者三也；伏神得动爻生者四；伏神得遇日月动爻冲克飞神者五也；
        #   伏神得遇飞神空破休囚墓绝者六也。」与源L1058 逐字「又伏神终不得出者有五」——
        #   **书只给条件不给分值**，故权重是引擎设计量，集中留在判据路一处，不再有两套。
        can_emerge, reason_text, emerge_score, emerge_reasons, block_reasons = (
            _evaluate_hidden_spirit_emergence(
                hidden_element, hidden_branch,
                determine_six_relation(covering_branch, palace_element),
                covering_branch, covering_element, month_branch, day_branch,
                month_element, day_element, empty_branches, covering_yao,
                moving_elems=[_branch_element(b) for b in moving_branches if b]))
        cov_strength = element_strength_in_month(covering_element, month_element)
        hid_strength = element_strength_in_month(hidden_element, month_element)
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


def analyze_tianqi_structure(result):
    """天气占的结构标签：只标"动/空/化出"的事实，不产任何吉凶断语（SKILL.md 铁律一）。

    书据（父动主雨、财动主晴一类机制的行号，断语用语文案另在 verdict_texts.json 取）：
      《黄金策》源L300 逐字「卦中父动主有雨，财动主晴」；
      《卜筮全书》源L5770 逐字「五类中，唯父母为雨」；
      《增删卜易》源L2040 逐字「占雨以父爻为主」。
    """
    hex_info = result.get("original_hexagram", {}) or {}
    yao_lines = hex_info.get("yao_lines", []) or []
    empty = list(result.get("empty_branches") or [])

    def _flags(rel):
        lines = [y for y in yao_lines if isinstance(y, dict) and y.get("six_relation") == rel]
        moving = any(bool(y.get("is_moving")) for y in lines)
        changed_into = any(bool(y.get("is_moving")) and (
            (y.get("changed_six_relation") or "") == rel) for y in yao_lines if isinstance(y, dict))
        quiet = bool(lines) and not moving
        empt = any((y.get("earthly_branch") or "") in empty for y in lines)
        return {"present": bool(lines), "moving": moving, "quiet": quiet,
                "empty": empt, "changed_into": changed_into}

    father = _flags("父母")
    wealth = _flags("妻财")
    tags = []
    if father["moving"]:
        tags.append("父动")
    if father["changed_into"]:
        tags.append("化出父母")
    if wealth["moving"]:
        tags.append("财动")
    if wealth["changed_into"]:
        tags.append("化出妻财")
    if father["present"] and father["empty"]:
        tags.append("父空")
    if wealth["present"] and wealth["empty"]:
        tags.append("财空")
    if father["present"] and not father["moving"] and not wealth["moving"]:
        tags.append("父财皆静")
    return {"father": father, "wealth": wealth, "tags": tags,
            "note": "结构标签，不含吉凶评断；取用以问题词典·天气族为准（占雨父母／占晴子孙财）"}


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

    参考《黄金策》游魂归魂章：
    > 「卦得游魂，漂泊他方无定迹」（源 L3843）
    > 「归魂卦用仍生合；不捕而自回；游魂卦应又交重，能潜而会遁」（源 L3444）
    > 世应安装另见《卜筮正宗》源 L241「游魂八宫四爻立，归魂八卦三爻详。」

    2026-10-07 订正（OPT-huangjince_dz-02）：原注《卜筮正宗》「游魂行无定，归魂回故乡」
    实测该八字在《卜筮正宗》源 0 命中（属跨书误挂），现改挂《黄金策》真实原文，
    并补《卜筮正宗》L241 世应歌诀为游魂/归魂世次出处。判定逻辑未变。
    > 游魂卦主在外、不安、忧疑、反复。
    > 归魂卦主在内、有归、安定、终有所归。

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
    （《增删卜易》「予用生旺墓絕，其餘不驗」——key/weak 分档只取生旺与死墓绝，
    其余八宫仅作 stage 标注展示，与书源同构）
    
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
    # 用神只能来自 step2。**禁止回退世爻**：书证主语是「世與用神」（《增删卜易》
    # 源L1706「大凡世与用神或绝于日或化绝，若得日月动爻生者，谓之绝处逢生」），
    # 世爻不是用神的替代品——回退世爻会把「用神绝处逢生」错算成「世爻绝处逢生」，
    # 与书证主语不符，且实测造成 4 例用神错位加分（2026-10-21 第两百六十四批：
    # WS007 用神父母@卯木，本条断言却写「用神水（亥）」并给出 +2.0）。
    # 本函数在 enhance_reading 阶段（step1 之前）调用时 `_step2_data` 尚不存在，
    # 那时**不产结论**；由 thinking_chain 在 step2 之后经
    # `attach_desperate_relief` 重算（既有范式同 `attach_luandong_looks`）。
    use_god_element = ""
    step2_data = result.get("_step2_data")
    if isinstance(step2_data, dict):
        use_god_element = step2_data.get("use_god_element", "") or ""
        use_god_position = step2_data.get("use_god_position")
    else:
        use_god_position = None

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


def attach_desperate_relief(result, step2_data):
    """step2 之后重算「绝处逢生」并回写 advanced_analysis（第两百六十四批·六爻）。

    为什么必须补挂而不是在 `analyze_desperate_relief` 里就地算：`enhance_reading`
    运行在 `thinking_chain` 的 step1 **之前**，那时 `_step2_data` 还不存在。
    旧实现在此情况下回退取世爻当用神，于是：
      · 断言句写出的用神与实际 step2 用神不符（实测 4/50 例，WS007/WS023/WS024/WS040）；
      · 其中 2 例因此凭空拿到 +2.0「凶中反吉」，把书证判凶的案例翻成吉。
    既有范式：`shi_yao_relation`、`attach_luandong_looks` 同样在 step2 后补挂。

    只重算这一个段，不改用神选取、不动其他增强段的判据。
    """
    if not isinstance(result, dict) or not isinstance(step2_data, dict):
        return
    adv = result.get("advanced_analysis")
    if not isinstance(adv, dict):
        return
    with_step2 = dict(result)
    with_step2["_step2_data"] = step2_data
    adv["desperate_relief"] = analyze_desperate_relief(with_step2)


# ======================================================================
# section: 六神旺衰标签（逢恩/归垣）试点 — OPT-yiin_dz-05
# 书源：《易隐》卷首 L879（通行曹九锡本）
# 口径：输出仅作叙述修饰，不参与 verdict/weight/final_score 判定
# ======================================================================

# （六神旺衰三表已随函数迁至 classical_enhancements_shen_yao.py——220 批拆分病修复，§二唯一真值源）



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
    "element_strength_in_month",
    "get_twelve_growth_stage",
    "get_stages_of_interest",
    "use_god_tomb_tags",
    "yimao_tomb_corrections",
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
    "attach_desperate_relief",
    "analyze_du_fa_du_jing",
    "analyze_luandong",
    "attach_luandong_looks",
    "analyze_zhu_gui_shang_shen",
    "analyze_menlei_dongjing",
    "huozhulin_fushi_tags",
    # six god wang shuai pilot (逢恩/归垣, OPT-yiin_dz-05)
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
