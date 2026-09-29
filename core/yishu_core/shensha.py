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

from .symbols import sanhe_group

# ================================================================ 神煞
# 只收「起例明确、可由四柱机械安出」的通行神煞。神煞安法是机械步骤（属 chart），
# 吉凶解读不在这里，也不在此写断语。出处见 references/rules.md，analyze 引用时 verified=false。

# 天乙贵人（以日干或年干取）：甲戊庚牛羊、乙己鼠猴乡、丙丁猪鸡位、
# 壬癸兔蛇藏、六辛逢马虎。
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

# 禄神（日干禄位）：甲禄在寅乙禄卯、丙戊禄巳丁己午、庚禄申辛禄酉、壬禄亥癸禄子。
LU_SHEN = {
    "甲": "寅", "乙": "卯", "丙": "巳", "戊": "巳", "丁": "午",
    "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子",
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
    return list(TIAN_YI_GUI_REN.get(stem, []))


def lu_shen(stem: str) -> str | None:
    """日干 → 禄神地支。"""
    return LU_SHEN.get(stem)


def hong_yan(stem: str) -> str | None:
    """日干 → 红艳地支。"""
    return HONG_YAN.get(stem)


def tian_xi(branch: str) -> str | None:
    """年支/日支 → 天喜地支。"""
    return TIAN_XI.get(branch)


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
    # 文昌贵人
    _add("文昌贵人", [WEN_CHANG[day_stem]] if day_stem in WEN_CHANG else [], "日干")
    # 羊刃（仅阳干）
    _add("羊刃", [YANG_REN[day_stem]] if day_stem in YANG_REN else [], "日干")
    # 三合局神煞：年支、日支各起一次
    for label, branch in (("年支", year_branch), ("日支", day_branch)):
        grp = sanhe_group(branch)
        if not grp:
            continue
        _add(f"驿马({label})", [YI_MA[grp]], label)
        _add(f"桃花({label})", [TAO_HUA[grp]], label)
        _add(f"华盖({label})", [HUA_GAI[grp]], label)
    return found
