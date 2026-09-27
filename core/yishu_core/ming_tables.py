# -*- coding: utf-8 -*-
"""命科补表（Ming Tables）—— 八字四柱所需、而 core 此前没有的规则表。

依 CONTRACT.md §二：「学科若需要内核没有的表（如八字的藏干、十神、神煞），
加到内核并标注只有哪几科用，不要开第二个真值源。」本模块即命科（四柱八字）的补表，
**唯一消费方：命科 `disciplines/ming`**；卜科不用（六亲/卦象另有 symbols、najia）。

收录：藏干、纳音、神煞、大运起法、命宫身宫。十神本身是「关系」，其推演在
relations.py（十神↔六亲同一张表），本模块只借它给藏干逐个定十神。

真值源纪律（两处须知）：
  1. 干支、五行、五虎遁、节气一律取自 ganzhi_calendar.py / symbols.py，不在此另抄。
  2. 三合局分组（申子辰…）core 此前没有——六爻把它写在 `thinking_chain.py` 里（学科内副本）。
     神煞中的驿马/桃花/华盖按三合局取，故在**内核**此处立一份规范分组；
     六爻那份副本应日后上收归并（已记入 `synthesis/notes/CORE-GAPS.md`）。
     这不是在学科里开第二真值源，而是把共用表补进 core。

出处诚实：以下诸表均为子平通行定式（多托名《渊海子平》《三命通会》），
本环境无法逐字核对原文，凡被 analyze 引用为判据者，其 `verified` 一律标 false，
详见 `disciplines/ming/references/rules.md` 与 `data/verdicts.json`。
"""
from __future__ import annotations

from .ganzhi_calendar import (
    HEAVENLY_STEMS,
    EARTHLY_BRANCHES,
    TIGER_MONTH_STEM,
    ganzhi_pair,
)
from .symbols import BRANCH_ELEMENTS
from . import relations as rel

# ================================================================ 藏干（人元司令）
# 地支所藏天干：本气在前，中气、余气依次。子平通行「三元藏干」。
# 十神由日主对每个藏干逐一推（见 canggan_ten_gods）。
CANG_GAN = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}
CANG_GAN_LAYER = ["本气", "中气", "余气"]


def hidden_stems(branch: str) -> list[str]:
    """地支 → 藏干列表（本气在前）；非法地支返回空。"""
    return list(CANG_GAN.get(branch, []))


def canggan_ten_gods(day_stem: str, branch: str) -> list[dict]:
    """某地支的每个藏干对日主的十神。返回 [{stem, ten_god, layer}]。"""
    out = []
    for i, stem in enumerate(CANG_GAN.get(branch, [])):
        out.append({
            "stem": stem,
            "ten_god": rel.ten_god(day_stem, stem),
            "layer": CANG_GAN_LAYER[i] if i < len(CANG_GAN_LAYER) else "余气",
        })
    return out


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


# ================================================================ 大运起法
# 方向：年干阴阳与性别「同性相顺」——阳年男 / 阴年女顺行，阴年男 / 阳年女逆行。
# 起运岁：出生到（顺行取未来、逆行取过去）最近一个「节」的天数，三日折一年、
# 一日折四月、一时辰折十日。节时刻由 ganzhi_calendar 求，本模块只给规则常量与方向。
DAYS_PER_LUCK_YEAR = 3        # 三日 = 一年
MONTHS_PER_DAY = 4            # 一日 = 四月
DAYS_PER_SHICHEN = 10         # 一时辰 = 十日


def dayun_direction(year_stem: str, gender: str) -> str | None:
    """大运顺逆：返回 "forward"（顺行）/ "backward"（逆行）；输入非法返回 None。

    gender 取 "male"/"female"（或 "男"/"女"）。
    """
    yy = rel.yinyang_of(year_stem)
    if yy is None:
        return None
    g = {"男": "male", "女": "female"}.get(gender, gender)
    if g not in ("male", "female"):
        return None
    yang_male = (yy == "阳" and g == "male")
    yin_female = (yy == "阴" and g == "female")
    return "forward" if (yang_male or yin_female) else "backward"


# ================================================================ 命宫 / 身宫
# 命宫：以寅起正月顺数至生月定月宫，再从月宫起子时**逆**数至生时。
# 身宫：同法定月宫，再从月宫起子时**顺**数至生时。（子平通行起例，流派有别，见 references）
def _month_num(month_branch: str) -> int | None:
    """月支 → 月序（寅=1、卯=2 … 子=11、丑=12）。"""
    if month_branch not in BRANCH_ELEMENTS:
        return None
    idx = EARTHLY_BRANCHES.index(month_branch)
    return (idx - 2) % 12 + 1


def _hour_num(hour_branch: str) -> int | None:
    """时支 → 时序（子=1 … 亥=12）。"""
    if hour_branch not in BRANCH_ELEMENTS:
        return None
    return EARTHLY_BRANCHES.index(hour_branch) + 1


def ming_gong_branch(month_branch: str, hour_branch: str) -> str | None:
    """命宫地支。"""
    mn, hn = _month_num(month_branch), _hour_num(hour_branch)
    if mn is None or hn is None:
        return None
    return EARTHLY_BRANCHES[(mn - hn + 2) % 12]


def shen_gong_branch(month_branch: str, hour_branch: str) -> str | None:
    """身宫地支。"""
    mn, hn = _month_num(month_branch), _hour_num(hour_branch)
    if mn is None or hn is None:
        return None
    return EARTHLY_BRANCHES[(mn + hn) % 12]


def _stem_by_tiger(year_stem: str, branch: str) -> str | None:
    """五虎遁：由年干给某地支配天干（与月干同一遁法）。"""
    if year_stem not in TIGER_MONTH_STEM or branch not in BRANCH_ELEMENTS:
        return None
    idx = EARTHLY_BRANCHES.index(branch)
    stem_idx = (TIGER_MONTH_STEM[year_stem] + (idx - 2) % 12) % 10
    return HEAVENLY_STEMS[stem_idx]


def palace_ganzhi(year_stem: str, palace_branch: str) -> str | None:
    """命宫/身宫的完整干支（五虎遁配干）。"""
    stem = _stem_by_tiger(year_stem, palace_branch)
    return (stem + palace_branch) if stem else None


def ming_shen_gong(year_stem: str, month_branch: str, hour_branch: str) -> dict:
    """一次算出命宫、身宫（地支、干支、纳音）。"""
    mb = ming_gong_branch(month_branch, hour_branch)
    sb = shen_gong_branch(month_branch, hour_branch)
    mgz = palace_ganzhi(year_stem, mb) if mb else None
    sgz = palace_ganzhi(year_stem, sb) if sb else None
    return {
        "ming_gong": {"branch": mb, "ganzhi": mgz, "nayin": nayin_of(mgz) if mgz else None},
        "shen_gong": {"branch": sb, "ganzhi": sgz, "nayin": nayin_of(sgz) if sgz else None},
    }
