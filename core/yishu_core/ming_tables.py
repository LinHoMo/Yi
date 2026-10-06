# -*- coding: utf-8 -*-
"""命科补表（Ming Tables）—— 八字四柱所需、而 core 此前没有的规则表。

依 CONTRACT.md §二：「学科若需要内核没有的表（如八字的藏干、十神），
加到内核并标注只有哪几科用，不要开第二个真值源。」本模块即命科（四柱八字）的补表，
**唯一消费方：命科 `disciplines/ming`**（藏干十神 / 大运起法 / 命宫身宫）。

收录：藏干、大运起法、命宫身宫。十神本身是「关系」，其推演在
relations.py（十神↔六亲同一张表），本模块只借它给藏干逐个定十神。

**纳音、三合局分组、神煞原本也住在这里**，但卜科（六爻）同样在取——
`bing_yao_shensha.py` 取 `shensha_at_branches`、`chain_tables.py` 取 `SAN_HE_GROUPS`、
`classical_tables.py` 取 `NAYIN`/`NAYIN_TO_ELEMENT`——与本模块「唯一消费方：命科」
的声明自相矛盾，即审计 B3「内核领域命名泄漏」。2026-09-29 按归属拆出，**取值零变化**：
  - 纳音 + 三合局分组 → `symbols.py`（干支五行关系；其章程本就写着「六合六冲三合三刑六破」，
    三合却一直不在里面，顺带补齐章程）
  - 神煞 → 新建 `shensha.py`（命、卜两科共用，消费方已在该模块头标注）

真值源纪律（两处须知）：
  1. 干支、五行、五虎遁、节气一律取自 ganzhi_calendar.py / symbols.py，不在此另抄。
  2. 三合局分组（申子辰…）唯一真值源在 `symbols.SAN_HE_GROUPS`；神煞中的驿马/桃花/华盖
     按三合局取，经 `symbols.sanhe_group` 调用，绝不再开第二份。

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
from .symbols import BRANCH_ELEMENTS, nayin_of as _nayin_of
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


# ================================================================ 大运起法
# 方向：年干阴阳与性别「同性相顺」——阳年男 / 阴年女顺行，阴年男 / 阳年女逆行。
# 起运岁：出生到（顺行取未来、逆行取过去）最近一个「节」的天数，三日折一年、
# 一日折四月、一时辰折十日。节时刻由 ganzhi_calendar 求，本模块只给规则常量与方向。
DAYS_PER_LUCK_YEAR = 3        # 三日 = 一年
MONTHS_PER_DAY = 4            # 一日 = 四月


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
        "ming_gong": {"branch": mb, "ganzhi": mgz, "nayin": _nayin_of(mgz) if mgz else None},
        "shen_gong": {"branch": sb, "ganzhi": sgz, "nayin": _nayin_of(sgz) if sgz else None},
    }


# ================================================================ 调候用神表
# 《穷通宝鉴》按月令×日主定调候（"正月甲木，得丙癸逢"）。本表只收**原文有明文**的
# 格——由 `disciplines/ming/dev_tools/build_tiaohou.py` 从 data/sources/
# qiong-tong-bao-jian.wikitext.txt 机械提取并逐格校验「引文为原文子串」（109/120 格，
# 逐格引文见 disciplines/ming/data/tiaohou_quotes.json；其中 11 格为季节总论句兜底
# （仅该格无精确月头时才启用），via 标记 season，已知可能过泛，外集批会校验）。未提取到的格不在表里（宁缺勿滥，
# 查不到返回 None，调用方按"无明文"处理，不得凭记忆补格）。
# 口径：main = 原文排序在前/为尊之神，assist = 次/佐之神；assist 空串 = 原文只明写一神。
TIAO_HOU: dict[str, dict[str, dict[str, str]]] = {
    "寅": {
        "甲": {"main": "丙", "assist": "癸"},
        "乙": {"main": "丙", "assist": "癸"},
        "丙": {"main": "壬", "assist": "庚"},
        "丁": {"main": "庚", "assist": ""},
        "戊": {"main": "癸", "assist": ""},
        "己": {"main": "丙", "assist": ""},
        "庚": {"main": "丙", "assist": "甲"},
        "辛": {"main": "己", "assist": "壬"},
        "壬": {"main": "庚", "assist": ""},
        "癸": {"main": "辛", "assist": "丙"},
    },
    "卯": {
        "乙": {"main": "丙", "assist": "癸"},
        "丙": {"main": "壬", "assist": ""},
        "丁": {"main": "庚", "assist": "甲"},
        "戊": {"main": "丙", "assist": "甲"},
        "己": {"main": "甲", "assist": ""},
        "庚": {"main": "丁", "assist": ""},
        "辛": {"main": "壬", "assist": ""},
        "壬": {"main": "戊", "assist": "辛"},
        "癸": {"main": "庚", "assist": ""},
    },
    "辰": {
        "甲": {"main": "庚", "assist": "壬"},
        "乙": {"main": "癸", "assist": "丙"},
        "丙": {"main": "壬", "assist": "甲"},
        "丁": {"main": "庚", "assist": "甲"},
        "戊": {"main": "甲", "assist": "丙"},
        "己": {"main": "丙", "assist": "癸"},
        "庚": {"main": "甲", "assist": "丁"},
        "辛": {"main": "壬", "assist": "甲"},
        "壬": {"main": "甲", "assist": ""},
        "癸": {"main": "丙", "assist": ""},
    },
    "巳": {
        "甲": {"main": "癸", "assist": "丁"},
        "乙": {"main": "癸", "assist": ""},
        "丙": {"main": "壬", "assist": "庚"},
        "丁": {"main": "甲", "assist": ""},
        "戊": {"main": "甲", "assist": ""},
        "庚": {"main": "壬", "assist": ""},
        "壬": {"main": "壬", "assist": "辛"},
        "癸": {"main": "辛", "assist": ""},
    },
    "午": {
        "甲": {"main": "癸", "assist": "丁"},
        "乙": {"main": "癸", "assist": ""},
        "丙": {"main": "壬", "assist": ""},
        "戊": {"main": "壬", "assist": "甲"},
        "庚": {"main": "壬", "assist": ""},
        "辛": {"main": "壬", "assist": "己"},
        "壬": {"main": "癸", "assist": ""},
    },
    "未": {
        "甲": {"main": "庚", "assist": "丁"},
        "乙": {"main": "丙", "assist": ""},
        "丙": {"main": "壬", "assist": "庚"},
        "丁": {"main": "甲", "assist": ""},
        "戊": {"main": "癸", "assist": "丙"},
        "庚": {"main": "丁", "assist": "甲"},
        "辛": {"main": "壬", "assist": "庚"},
        "壬": {"main": "辛", "assist": "甲"},
        "癸": {"main": "庚", "assist": "辛"},
    },
    "申": {
        "甲": {"main": "丁", "assist": "庚"},
        "乙": {"main": "己", "assist": ""},
        "丙": {"main": "壬", "assist": ""},
        "丁": {"main": "甲", "assist": ""},
        "戊": {"main": "丙", "assist": "癸"},
        "己": {"main": "癸", "assist": "丙"},
        "庚": {"main": "丁", "assist": ""},
        "辛": {"main": "壬", "assist": ""},
        "壬": {"main": "戊", "assist": ""},
        "癸": {"main": "丁", "assist": ""},
    },
    "酉": {
        "甲": {"main": "丁", "assist": "丙"},
        "乙": {"main": "丙", "assist": "癸"},
        "丙": {"main": "壬", "assist": ""},
        "丁": {"main": "甲", "assist": ""},
        "戊": {"main": "丙", "assist": "癸"},
        "己": {"main": "癸", "assist": "丙"},
        "庚": {"main": "丁", "assist": ""},
        "辛": {"main": "壬", "assist": ""},
        "壬": {"main": "甲", "assist": ""},
        "癸": {"main": "辛", "assist": ""},
    },
    "戌": {
        "甲": {"main": "丁", "assist": ""},
        "乙": {"main": "丙", "assist": "癸"},
        "丙": {"main": "甲", "assist": "壬"},
        "丁": {"main": "甲", "assist": "庚"},
        "戊": {"main": "甲", "assist": "癸"},
        "己": {"main": "甲", "assist": ""},
        "庚": {"main": "甲", "assist": ""},
        "辛": {"main": "壬", "assist": "甲"},
        "壬": {"main": "甲", "assist": ""},
        "癸": {"main": "辛", "assist": "甲"},
    },
    "亥": {
        "甲": {"main": "庚", "assist": ""},
        "乙": {"main": "丙", "assist": "戊"},
        "丁": {"main": "庚", "assist": "甲"},
        "戊": {"main": "甲", "assist": ""},
        "己": {"main": "丙", "assist": ""},
        "庚": {"main": "丁", "assist": "丙"},
        "辛": {"main": "壬", "assist": "丙"},
        "壬": {"main": "戊", "assist": "庚"},
        "癸": {"main": "庚", "assist": "辛"},
    },
    "子": {
        "甲": {"main": "丁", "assist": "庚"},
        "乙": {"main": "丙", "assist": ""},
        "丙": {"main": "壬", "assist": "戊"},
        "己": {"main": "丙", "assist": ""},
        "庚": {"main": "丁", "assist": "甲"},
        "辛": {"main": "壬", "assist": "丙"},
        "壬": {"main": "戊", "assist": "丙"},
        "癸": {"main": "丙", "assist": ""},
    },
    "丑": {
        "甲": {"main": "庚", "assist": ""},
        "乙": {"main": "戊", "assist": ""},
        "丙": {"main": "壬", "assist": "甲"},
        "丁": {"main": "庚", "assist": "甲"},
        "己": {"main": "丙", "assist": ""},
        "庚": {"main": "丙", "assist": "丁"},
        "辛": {"main": "丙", "assist": "壬"},
        "壬": {"main": "丙", "assist": ""},
        "癸": {"main": "丙", "assist": ""},
    },
}


def tiaohou_of(month_branch: str, day_stem: str) -> dict | None:
    """月支×日主 → 调候用神 {main, assist}；原文无明文的格返回 None（宁缺勿滥）。"""
    cell = TIAO_HOU.get(month_branch, {}).get(day_stem)
    if not cell:
        return None
    return {"main": cell["main"], "assist": cell.get("assist") or ""}
