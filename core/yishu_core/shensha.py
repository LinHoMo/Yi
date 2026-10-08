# -*- coding: utf-8 -*-
"""神煞（Shen Sha）—— 起例明确、可由干支机械安出的通行神煞，安星函数与规则表。

**消费方标注（AGENTS.md §二 / CONTRACT.md §二）**：
  - 命科 `disciplines/ming`：`shensha_of_chart`（四柱盘内安星）
  - 卜科 `disciplines/liuyao`：`shensha_at_branches`（六爻按日干日支/年支安星）
  两科共用，故单独成模块；**吉凶解读不在此处**，只给机械安星结果。

拆分由来：这些表原先住在 `ming_tables.py`，而该模块头声称「唯一消费方：命科，卜科不用」，
与六爻实际取用的事实矛盾（`bing_yao_shensha.py` / `chain_tables.py` / `classical_tables.py`），
即审计 B3「内核领域命名泄漏」。驿马/桃花/华盖按三合局取，故依赖 `symbols.sanhe_group`。
出处诚实：均为通行起例，本环境无法逐字核对原文，被 analyze 引用为判据者 `verified=false`。
"""
from __future__ import annotations

from .symbols import BRANCH_ELEMENTS, NAYIN_TO_ELEMENT, sanhe_group, nayin_of

# ================================================================ 神煞
# 只收「起例明确、可由四柱机械安出」的通行神煞。神煞安法是机械步骤（属 chart），
# 吉凶解读不在这里，也不在此写断语。analyze 引用时 verified=false。
#
# 出处登记（**死链已修**，OPT-lixuzhong_mingshu_dz-01，2026-10-07）：
#   本处原写「出处见 references/rules.md」，经实测**该文件全仓不存在**
#   （`find . -name rules.md` 零命中；disciplines/ming/references/ 下只有 api_spec.md）
#   ——是一条真死链，故改指真实存在的两处：
#     ① disciplines/ming/data/rules/rule_registry.json → 条目 `ming.shensha`
#        （神煞出处的**唯一权威登记**，含 verified=false 的考证结论）
#     ② disciplines/ming/data/verdicts.json（引文层）
#   同批修正的另一处死链：core/yishu_core/ming_tables.py:26「详见
#   disciplines/ming/references/rules.md」——同指该不存在的文件，已一并改指 ①。

# 天乙贵人（以日干或年干取）：甲戊庚牛羊、乙己鼠猴乡、丙丁猪鸡位、
# 壬癸兔蛇藏、六辛逢马虎。
#
# 并列书源（OPT-lixuzhong_mingshu_dz-01，2026-10-07 补注，**取值零变更**）：
#   本表取值（甲戊庚→丑未｜乙己→子申｜丙丁→亥酉｜壬癸→卯巳｜辛→午寅）
#   与下述两份在库书源**逐字同构**，且《李虚中命书》给出更早的分组依据：
#     · data/sources/lixuzhong_mingshu_dz.dz.txt L76 逐字：
#       「本家贵人命者，如甲人有戊有庚有丑有未是也大贵，如甲人得丁丑辛未，
#         又其次也。……更有一种贵人，亦为福甚重得者必贵，**甲戊庚得乙丑癸未，
#         乙得庚子戊申，己得丙子甲申，丙丁得丁酉乙亥，壬癸得乙卯癸巳，
#         六辛得丙寅戊午**」
#       ——即本表丑未／子申／亥酉／卯巳／午寅五组**逐组对应**（本书以「本家贵人」
#       即同干贵人称之，与后世「天乙」名同实异，此处只登记**分组结构**同构）。
#     · data/sources/lixuzhong_mingshu_dz.dz.txt L82 逐字：
#       「贵合贵食，有贵合则官位穹崇所作契合。……如**甲戊庚贵在丑未**，
#         甲得己丑己未，戊得癸丑癸未，庚得乙丑乙未，**乙巳贵在申子**……
#         **丙丁贵在亥酉**，丙得辛酉辛亥……如此之类谓之贵合」
#   【勘误】本注释初稿曾并列举《火珠林》星煞章「甲戊兼牛羊，乙己鼠猴乡……」为第三源，
#     经实测该句在 data/sources/huozhulin_dz.dz.txt 中 **0 命中**（「牛羊」「鼠猴乡」
#     「猪鸡位」三词均无），故**不采此说**——不把未入库的书源写进注释
#     （AGENTS.md「引文必须逐字可指回原文」，无源不引）。
#   **verified 仍为 false**：上述只证明「分组结构在《李虚中命书》有据」，不等于本表逐字
#   出处已核定；该考证结论登记在 rule_registry.json 的 `ming.shensha` 条目，
#   本轮不改其 verified 取值（AGENTS.md「宁缺勿造」）。
TIAN_YI_GUI_REN = {
    "甲": ["丑", "未"], "戊": ["丑", "未"], "庚": ["丑", "未"],
    "乙": ["子", "申"], "己": ["子", "申"],
    "丙": ["亥", "酉"], "丁": ["亥", "酉"],
    "壬": ["卯", "巳"], "癸": ["卯", "巳"],
    "辛": ["午", "寅"],
}
# 文昌贵人（以日干取）：甲巳乙午丙戊申、丁己酉庚亥辛子、壬寅癸卯。
WEN_CHANG = {
    "甲": "巳", "乙": "午", "丙": "申", "丁": "酉", "戊": "申",
    "己": "酉", "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯",
}
# 羊刃（阳干禄前一位）：甲卯、丙戊午、庚酉、壬子。阴干刃说法不一，此处不取（宁缺勿造）。
YANG_REN = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}

# 三合局神煞：驿马、桃花（咸池）、华盖。以年支或日支所在三合局取。
YI_MA = {"水": "寅", "火": "申", "金": "亥", "木": "巳"}
TAO_HUA = {"水": "酉", "火": "卯", "金": "午", "木": "子"}
HUA_GAI = {"水": "辰", "火": "戌", "金": "丑", "木": "未"}

# 【桃花/咸池「真假」判别，OPT-sanming_tonghui_dz-05，2026-10-07 补注，**取值零变更**】
# 本表 TAO_HUA 只按三合局取落点（申子辰→酉、寅午戌→卯、巳酉丑→午、亥卯未→子），
# **未做真假判别**。书源对真假有明文，且是「加一道同类检验」而非改落点：
#   data/sources/sanming_tonghui_dz.dz.txt L456 逐字：
#     「论咸池【按此煞须天干纳音于地同类方是若只论寅午戌在卯天干纳音或不属火非是」
#   ——即寅午戌见卯只是**候选**，还须「天干纳音于地同类」（天干纳音五行 = 落点地支五行）
#   才算真咸池；纳音不属火（卯）者非是。
# 口径裁定（本轮只登记、不改判定）：
#   真假判别属**吉凶倾向**（「非是」即不算真煞），按 AGENTS.md 铁律一
#   「机械运算归代码、吉凶归 LLM」与铁律三（凶象用「偏向/有…信号」），
#   本层**不自动过滤**候选落点——那会改动 shensha_at_branches /
#   shensha_of_chart 的返回集合，属读数可见变更，须另走 §四 门槛并逐格对拍。
#   故本轮只把书源句挂在表头并提供 `taohua_zhenjia()` 供 narrate 层**旁证**，
#   引擎安星结果与读数**零变化**。要否升格为硬判据，须先有书例对齐分支撑。
TAO_HUA_ZHENJIA_NOTE = (
    "论咸池【按此煞须天干纳音于地同类方是若只论寅午戌在卯天干纳音或不属火非是"
)
TAO_HUA_ZHENJIA_SRC = "data/sources/sanming_tonghui_dz.dz.txt:456"


def taohua_zhenjia(pillar_ganzhi: str, target_branch: str) -> bool | None:
    """咸池真假旁证（《三命通会》L456「纳音同类方是」）：命柱纳音五行 == 落点地支五行？

    `pillar_ganzhi` 是取咸池的那一柱（年柱或日柱）的**完整干支两字**
    （纳音按干支对取，故须给全；`nayin_of` 只认合法干支对），
    `target_branch` 是三合局取出的桃花候选落点。

    返回 True=同类（书源谓之「是」）／False=不同类（书源谓之「非是」）／
    None=无法判定（干支非法，或落点非四支之一）。

    **只作 narrate 层旁证，不参与任何吉凶评分、不改安星结果**（见上表头裁定）。
    """
    if not pillar_ganzhi or len(pillar_ganzhi) < 2 or not target_branch:
        return None
    # nayin_of 返回纳音**名**（如「海中金」），须经 NAYIN_TO_ELEMENT 落到五行才可比
    elem = NAYIN_TO_ELEMENT.get(nayin_of(pillar_ganzhi[:2]) or "")
    if not elem:
        return None
    branch_elem = BRANCH_ELEMENTS.get(target_branch)
    if not branch_elem:
        return None
    return elem == branch_elem

# 三合局神煞（《三命通会·论神煞》通行起例，verified=false）：
#   将星 = 三合中位（申子辰→子，寅午戌→午，巳酉丑→酉，亥卯未→卯）
#   亡神 = 三合临官（申子辰→亥，寅午戌→巳，巳酉丑→申，亥卯未→寅）
#   劫煞 = 三合绝位（申子辰→巳，寅午戌→寅，巳酉丑→申，亥卯未→亥）
JIANG_XING = {"水": "子", "火": "午", "金": "酉", "木": "卯"}
WANG_SHEN = {"水": "亥", "火": "巳", "金": "申", "木": "寅"}
JIE_SHA = {"水": "巳", "火": "寅", "金": "申", "木": "亥"}

# 飞刃 = 羊刃之冲（甲刃卯→飞刃酉，丙戊刃午→子，庚刃酉→卯，壬刃子→午）。
FEI_REN = {"甲": "酉", "丙": "子", "戊": "子", "庚": "卯", "壬": "午"}
# 金舆（日干）：甲龙乙蛇丙戊羊、丁己猴庚犬辛猪、壬牛癸兔。
JIN_YU = {
    "甲": "辰", "乙": "巳", "丙": "未", "戊": "未", "丁": "申",
    "己": "申", "庚": "戌", "辛": "亥", "壬": "丑", "癸": "卯",
}
# 天医（月支前一位）：寅月见丑、卯月见寅……（地支逆一位）。
TIAN_YI_YUE = {
    "寅": "丑", "卯": "寅", "辰": "卯", "巳": "辰", "午": "巳", "未": "午",
    "申": "未", "酉": "申", "戌": "酉", "亥": "戌", "子": "亥", "丑": "子",
}
# 孤辰寡宿（方局，以年支/日支取）：亥子丑见寅孤/戌寡；寅卯辰见巳孤/丑寡；
# 巳午未见申孤/辰寡；申酉戌见亥孤/未寡。
GU_CHEN = {"亥": "寅", "子": "寅", "丑": "寅", "寅": "巳", "卯": "巳", "辰": "巳",
           "巳": "申", "午": "申", "未": "申", "申": "亥", "酉": "亥", "戌": "亥"}
GUA_SU = {"亥": "戌", "子": "戌", "丑": "戌", "寅": "丑", "卯": "丑", "辰": "丑",
          "巳": "辰", "午": "辰", "未": "辰", "申": "未", "酉": "未", "戌": "未"}
# 阴差阳错日（日柱干支，12 组，《三命通会》原文照录）。
YIN_CHA_YANG_CUO = {
    "丙子", "丁丑", "戊寅", "辛卯", "壬辰", "癸巳",
    "丙午", "丁未", "戊申", "辛酉", "壬戌", "癸亥",
}

# 禄神（日干禄位）：甲禄在寅乙禄卯、丙戊禄巳丁己午、庚禄申辛禄酉、壬禄亥癸禄子。
LU_SHEN = {
    "甲": "寅", "乙": "卯", "丙": "巳", "戊": "巳", "丁": "午",
    "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子",
}
# 童子煞（民间通胜口诀，非《渊海子平》等子平经典原文；verified=false）。
# 口诀：春秋寅子贵，冬夏卯未辰；金木马卯合，水火鸡犬多；土命逢辰巳，童子定不错。
# 释：春/秋季（以月令算）日支或时支见寅或子；冬/夏季日支或时支见卯、未或辰；
#      年柱纳音金或木，日时支见午或卯；水、火见酉或戌；土见辰或巳。
TONGZI_MONTH_SEASON = {
    "寅": "春", "卯": "春", "辰": "春",
    "巳": "夏", "午": "夏", "未": "夏",
    "申": "秋", "酉": "秋", "戌": "秋",
    "亥": "冬", "子": "冬", "丑": "冬",
}
TONGZI_SEASON_TARGETS = {
    "春": ["寅", "子"], "秋": ["寅", "子"],
    "冬": ["卯", "未", "辰"], "夏": ["卯", "未", "辰"],
}
TONGZI_NAYIN_TARGETS = {
    "金": ["午", "卯"], "木": ["午", "卯"],
    "水": ["酉", "戌"], "火": ["酉", "戌"], "土": ["辰", "巳"],
}
# 红艳（以日干取）：甲午乙午丙寅丁未戊辰、己辰庚戌辛酉壬子癸申。
HONG_YAN = {
    "甲": "午", "乙": "午", "丙": "寅", "丁": "未", "戊": "辰",
    "己": "辰", "庚": "戌", "辛": "酉", "壬": "子", "癸": "申",
}
# 天喜：红鸾对冲。红鸾卯起子逆行，天喜=冲红鸾。按年支或日支取。
# 子→酉 丑→申 寅→未 卯→午 辰→巳 巳→辰 午→卯 未→寅 申→丑 酉→子 戌→亥 亥→戌
TIAN_XI = {
    "子": "酉", "丑": "申", "寅": "未", "卯": "午", "辰": "巳", "巳": "辰",
    "午": "卯", "未": "寅", "申": "丑", "酉": "子", "戌": "亥", "亥": "戌",
}

# 择吉用：天德/月德贵人（以月支取）。《协纪辨方书》通行口径。
# 天德：正丁二申三壬四辛五亥六甲七癸八寅九丙十乙十一巳十二庚
TIAN_DE = {
    "寅": ["丁"], "卯": ["申"], "辰": ["壬"], "巳": ["辛"],
    "午": ["亥"], "未": ["甲"], "申": ["癸"], "酉": ["寅"],
    "戌": ["丙"], "亥": ["乙"], "子": ["巳"], "丑": ["庚"],
}
# 月德：寅午戌月在丙，申子辰月在壬，亥卯未月在甲，巳酉丑月在庚。
YUE_DE = {
    "寅": "丙", "午": "丙", "戌": "丙",
    "申": "壬", "子": "壬", "辰": "壬",
    "亥": "甲", "卯": "甲", "未": "甲",
    "巳": "庚", "酉": "庚", "丑": "庚",
}


def tianyi_guiren(stem: str) -> list[str]:
    """日干/年干 → 天乙贵人所落地支（甲戊庚牛羊、乙己鼠猴…）。"""
    return list(TIAN_YI_GUI_REN.get(stem, []))


def tian_de(month_branch: str) -> list[str]:
    """月支 → 天德所落地支/干（择吉用）。"""
    return list(TIAN_DE.get(month_branch, []))


def yue_de(month_branch: str) -> str | None:
    """月支 → 月德天干（择吉用）。"""
    return YUE_DE.get(month_branch)


def shensha_at_branches(day_stem: str, day_branch: str,
                        year_stem: str | None = None,
                        year_branch: str | None = None) -> list[dict]:
    """按日干/日支（及可选年柱）机械安出常见神煞，返回各神煞「应落」地支。

    供六爻/择吉挂盘使用：只返回安星结果 [{name, target_branches, basis}]，
    是否「临爻/临日」由调用方比对，本函数不写吉凶。
    """
    out: list[dict] = []

    def _one(name: str, targets: list[str], basis: str) -> None:
        if targets:
            out.append({"name": name, "target_branches": targets, "basis": basis})

    _one("天乙贵人", tianyi_guiren(day_stem), "日干")
    _one("文昌贵人", [WEN_CHANG[day_stem]] if day_stem in WEN_CHANG else [], "日干")
    _one("羊刃", [YANG_REN[day_stem]] if day_stem in YANG_REN else [], "日干")
    _one("禄神", [LU_SHEN[day_stem]] if day_stem in LU_SHEN else [], "日干")
    _one("红艳", [HONG_YAN[day_stem]] if day_stem in HONG_YAN else [], "日干")
    for label, branch in (("日支", day_branch), ("年支", year_branch or "")):
        if not branch:
            continue
        _one("天喜", [TIAN_XI[branch]] if branch in TIAN_XI else [], label)
        grp = sanhe_group(branch)
        if not grp:
            continue
        _one("驿马", [YI_MA[grp]], label)
        _one("桃花", [TAO_HUA[grp]], label)
        _one("华盖", [HUA_GAI[grp]], label)
    return out


def shensha_of_chart(day_stem: str, year_stem: str,
                     year_branch: str, day_branch: str,
                     all_branches: list[str]) -> list[dict]:
    """从四柱机械安出通行神煞。all_branches 为年/月/日/时四支，用于判断神煞是否入命。

    返回 [{name, at}]，`at` 为神煞所落地支；只报「盘中实际出现」者，未出现的不报。
    纯安星，无吉凶措辞。
    """
    present = set(all_branches)
    found = []

    def _add(name, target_branches, basis):
        hit = [b for b in target_branches if b in present]
        if hit:
            found.append({"name": name, "at": hit, "basis": basis})

    # 天乙贵人：日干为主，年干为辅
    _add("天乙贵人", tianyi_guiren(day_stem), "日干")
    if year_stem != day_stem:
        _add("天乙贵人(年干)", tianyi_guiren(year_stem), "年干")
    _add("文昌贵人", [WEN_CHANG[day_stem]] if day_stem in WEN_CHANG else [], "日干")
    # 羊刃（仅阳干）
    _add("羊刃", [YANG_REN[day_stem]] if day_stem in YANG_REN else [], "日干")
    # 飞刃 / 金舆（日干）
    _add("飞刃", [FEI_REN[day_stem]] if day_stem in FEI_REN else [], "日干（羊刃之冲）")
    _add("金舆", [JIN_YU[day_stem]] if day_stem in JIN_YU else [], "日干")
    # 三合局神煞：年支、日支各起一次
    for label, branch in (("年支", year_branch), ("日支", day_branch)):
        grp = sanhe_group(branch)
        if not grp:
            continue
        _add(f"驿马({label})", [YI_MA[grp]], label)
        _add(f"桃花({label})", [TAO_HUA[grp]], label)
        _add(f"华盖({label})", [HUA_GAI[grp]], label)
        _add(f"将星({label})", [JIANG_XING[grp]], label)
        _add(f"亡神({label})", [WANG_SHEN[grp]], label)
        _add(f"劫煞({label})", [JIE_SHA[grp]], label)
        _add(f"孤辰({label})", [GU_CHEN[branch]] if branch in GU_CHEN else [], label)
        _add(f"寡宿({label})", [GUA_SU[branch]] if branch in GUA_SU else [], label)
    # 天医：月支前一位（月支=盘内月支，all_branches 固定为年/月/日/时）
    month_branch = all_branches[1] if len(all_branches) >= 2 else ""
    if month_branch and month_branch in TIAN_YI_YUE:
        _add("天医", [TIAN_YI_YUE[month_branch]], "月支前一位")
    # 阴差阳错日（日柱干支命中 12 组，书源《三命通会》原文照录）
    if day_stem + day_branch in YIN_CHA_YANG_CUO:
        _add("阴差阳错", [day_branch], "日柱")
    # 童子煞（民间通胜口诀；非《渊海子平》等子平经典原文，verified=false）。
    # 只机械安星，不批吉凶：月令定季 + 年柱纳音五行，查日支/时支是否落入目标支。
    month_branch_tz = all_branches[1] if len(all_branches) >= 2 else ""
    hour_branch_tz = all_branches[3] if len(all_branches) >= 4 else ""
    tz_targets = set()
    if month_branch_tz in TONGZI_MONTH_SEASON:
        tz_targets.update(TONGZI_SEASON_TARGETS[TONGZI_MONTH_SEASON[month_branch_tz]])
    year_gz = (year_stem or "") + (year_branch or "")
    nayin = nayin_of(year_gz) if year_gz else None
    nayin_elem = nayin[-1] if nayin else None
    if nayin_elem in TONGZI_NAYIN_TARGETS:
        tz_targets.update(TONGZI_NAYIN_TARGETS[nayin_elem])
    tz_hit = [b for b in (day_branch, hour_branch_tz) if b in tz_targets]
    tz_hit = [b for i, b in enumerate(tz_hit) if b not in tz_hit[:i]]  # 日时同支去重
    if tz_hit:
        found.append({
            "name": "童子煞",
            "at": tz_hit,
            "basis": "民间通胜口诀『春秋寅子贵，冬夏卯未辰；金木马卯合，水火鸡犬多；"
                     "土命逢辰巳，童子定不错』；非《渊海子平》等子平经典原文（verified=false）；只安星不批吉凶",
        })
    return found
