# -*- coding: utf-8 -*-
"""六壬补表（Liuren Tables）—— 大六壬起课所需的内核唯一真值源。

依 CONTRACT.md §二：学科需要的表加进内核、标注消费方，不开第二真值源。
唯一消费方：`disciplines/liuren`（大六壬）。

收录（起例出处均为 data/sources/liu-ren-da-quan.wikitext.txt 卷一「入手法」/「神煞」，
逐字引文留在学科层 data/verdicts.json，本模块只存结构）：
  ① 十干寄宫 JI_GONG（「甲课寅兮乙课辰」诀）
  ② 十二月将 YUE_JIANG：中气换将（太阳过宫）口径——月将 = 太阳躔次，
     雨水后亥将、春分后戌将……（「超神接气」之争以**中气换将**为第一版口径，
     经 `yuejiang_policy` 显式声明，不静默择一）
  ③ 十二天将 TIAN_JIANG_ORDER 及昼夜贵人 NOBLE_DAY/NOBLE_NIGHT、布法 tianjiang_layout
  ④ 日德 DAY_DE（卷一「十天干神煞」表：甲寅 乙申 丙巳 丁亥 戊巳 己寅 庚申 辛巳 壬亥 癸巳；
     原文第八位作「己」第十位作「已」，按通例校为「巳」并标 verified=False）

跨书同源对源（2026-10-07 补注，OPT-dunjia_yanyi_dz-02；该书**无对应学科** none-qimen，
本注释只登记同源事实，**不改本表取值、不引入遁甲拆局**）：
《遁甲演义》源L722：「盖太乙奇门六壬，皆同此应，故为之三式。然入门各有不同，要其极至，
则无二理也。」——即**太乙／奇门／六壬三式同源**（与本模块 docstring 所记六壬为三式之一相合）。
同书源L36「分阴阳二遁，按节推排」、源L120「皆起五虎」是奇门侧的节气推排与五虎遁口径，
对源 `ganzhi_calendar.TWELVE_JIE` / `TIGER_MONTH_STEM`（详见该处注释）。
⚠ 奇门另有拆局法（三日一局、阴阳二遁、置闰），**属奇门用法**；本仓月将仍只取
中气换将一版（见 `YUEJIANG_POLICY`），**不为奇门改动六壬任何口径**。
"""
from __future__ import annotations

from datetime import datetime

from yishu_core.ganzhi_calendar import (
    EARTHLY_BRANCHES,
    ganzhi_pair,
    solar_terms_of_year,
)

# ---------------------------------------------------------------- 十干寄宫
# 「甲课寅兮乙课辰，丙戊课巳不须论。丁己课未庚申上，辛戌壬亥是其真。
#   癸课原来丑宫坐，分明不用四正神。」（六壬大全·入手法·十干寄宫）
JI_GONG: dict[str, str] = {
    "甲": "寅", "乙": "辰", "丙": "巳", "丁": "未", "戊": "巳",
    "己": "未", "庚": "申", "辛": "戌", "壬": "亥", "癸": "丑",
}

# ---------------------------------------------------------------- 十二月将
# 中气换将（太阳过宫）：节气值（节）内月将仍是上一中气之将，交中气后换次将。
ZHONGQI_YUEJIANG: dict[str, tuple[str, str]] = {
    # 中气:   (月将支, 将名)
    "雨水": ("亥", "登明"),
    "春分": ("戌", "河魁"),
    "谷雨": ("酉", "从魁"),
    "小满": ("申", "传送"),
    "夏至": ("未", "小吉"),
    "大暑": ("午", "胜光"),
    # ⚠ 异名警示（OPT-taiyi_jinjing_dz-03，2026-10-07）：此处「太乙」是**十二月将名**
    # （处暑后月将，与登明/河魁/从革…十二将同列），**不是**太乙经义之太乙（九宫之主）。
    # 两者同名异义，全仓凡引本表者不得据「太乙」二字推断太乙科语义。
    # 详见 docs/source-readings/taiyi_jinjing_dz.md §四 第4条（该书 L24-187 的太乙为九宫之主）。
    "处暑": ("巳", "太乙"),
    "秋分": ("辰", "天罡"),
    "霜降": ("卯", "太冲"),
    "小雪": ("寅", "功曹"),
    "冬至": ("丑", "大吉"),
    "大寒": ("子", "神后"),
}

YUEJIANG_POLICY = "zhongqi"   # 中气换将（太阳过宫）；超神/接气/置闰之争日后作显式开关


def yuejiang_of(dt: datetime) -> dict:
    """datetime → {"branch", "name", "zhongqi", "instant", "policy"}。

    在上一年与本年的中气表里找最近一次已过的中气（大寒跨年由此覆盖）。
    """
    candidates: list[dict] = []
    for year in (dt.year - 1, dt.year):
        for term in solar_terms_of_year(year):
            if term["name"] in ZHONGQI_YUEJIANG:
                candidates.append(term)
    passed = [t for t in candidates if t["instant"] <= dt]
    if not passed:
        raise ValueError(f"找不到已过中气：{dt}")
    last = max(passed, key=lambda t: t["instant"])
    branch, name = ZHONGQI_YUEJIANG[last["name"]]
    return {
        "branch": branch, "name": name, "zhongqi": last["name"],
        "instant": last["instant"].strftime("%Y-%m-%d %H:%M"),
        "policy": YUEJIANG_POLICY,
    }


# ---------------------------------------------------------------- 十二天将
# 十二天将位次说明（2026-10-07 补注，OPT-liuren_cuiyan_dz-03）：
#   本序第 1 位为「贵人」本位，天将自第 2 位起布。以贵人位为起算点，本序与《六壬粹言》
#   L98-L108 逐位相合（结论成立；原核查报告的换算未计贵人位、论据有误，此处补正口径）：
#     螣蛇＝贵前一位(L98)、朱雀＝贵前二位(L99)、六合＝贵前三位(L100)、勾陈＝贵前四位(L101)、
#     青龙＝贵前五位(L102)、天空＝贵人前六位(L108)、天后＝贵后一位(L103)、
#     太阴＝贵后二位(L104)、玄武＝贵后三位(L105)、太常＝贵后四位(L106)、白虎＝贵后五位(L107)。
#   昼夜贵人十干取值亦与粹言 L97 零偏离。故「粹言天将位次未采」之疑虑可消。
TIAN_JIANG_ORDER: list[str] = [
    "贵人", "螣蛇", "朱雀", "六合", "勾陈", "青龙",
    "天空", "白虎", "太常", "玄武", "太阴", "天后",
]

# 昼夜贵人（歌诀「甲戊庚牛羊，乙己鼠猴乡，丙丁猪鸡位，壬癸蛇兔藏，六辛逢马虎」）
#   昼贵 = 诀第一位（牛/鼠/猪/蛇/马），夜贵 = 第二位（羊/猴/鸡/兔/虎）
# 2026-10-07 数据缺陷修复（OPT-liuren_shending_dz-01）：壬癸原误作昼卯夜巳，与书源相反。
#   三源互证：
#     ① 《六壬神定经》L291「壬癸之日，旦治太乙，暮治太冲」＋同书将名换算
#        L204「太乙于辰在巳」、L194「太冲于辰在卯」→昼巳夜卯；
#     ② 《六壬大全》卷四 L60 贵人歌「壬癸蛇兔藏巳卯」（巳=昼、卯=夜）；
#     ③ 《六壬大全》卷十一课例 L118「壬子日初传巳加子为昼贵，末传卯加戌为夜贵」。
#   按 AGENTS.md「数据缺陷 vs 引擎缺陷」判定为引擎取值错、书源三源一致，故改引擎。
NOBLE_DAY: dict[str, str] = {
    "甲": "丑", "戊": "丑", "庚": "丑",
    "乙": "子", "己": "子",
    "丙": "亥", "丁": "亥",
    "壬": "巳", "癸": "巳",
    "辛": "午",
}
NOBLE_NIGHT: dict[str, str] = {
    "甲": "未", "戊": "未", "庚": "未",
    "乙": "申", "己": "申",
    "丙": "酉", "丁": "酉",
    "壬": "卯", "癸": "卯",
    "辛": "寅",
}

# 昼夜分界：卯时起昼、酉时起夜（卯辰巳午未申为昼，酉戌亥子丑寅为夜）——
# 流派有寅时起昼一说，第一版固定卯酉分界并显式声明。


def is_day(hour_branch: str) -> bool:
    return hour_branch in ("卯", "辰", "巳", "午", "未", "申")


def noble_of(day_stem: str, hour_branch: str) -> dict:
    """日干×时辰 → {"noble": 支, "day_night": "昼"|"夜"}。"""
    day = is_day(hour_branch)
    return {
        "noble": NOBLE_DAY[day_stem] if day else NOBLE_NIGHT[day_stem],
        "day_night": "昼" if day else "夜",
    }


def tianjiang_layout(day_stem: str, hour_branch: str, tianpan: dict[str, str]) -> dict[str, str]:
    """十二天将布于十二地盘位：{地盘位: 将名}。

    贵人支落在天盘所临的地盘位；该地盘位在 亥~辰 一侧顺布、巳~戌 一侧逆布
    （贵人在天盘所临之地盘位定顺逆，通行口径）。
    """
    noble = noble_of(day_stem, hour_branch)
    nb = noble["noble"]
    noble_pos = next(p for p, sky in tianpan.items() if sky == nb)
    idx = EARTHLY_BRANCHES.index(noble_pos)
    forward = noble_pos in ("亥", "子", "丑", "寅", "卯", "辰")
    out: dict[str, str] = {}
    for i, jiang in enumerate(TIAN_JIANG_ORDER):
        pos = EARTHLY_BRANCHES[(idx + i) % 12] if forward \
            else EARTHLY_BRANCHES[(idx - i) % 12]
        out[pos] = jiang
    return out


# ---- 十二将家支与五行神（2026-10-07 新增，OPT-liuren_shending_dz-03）----
# 书源：《六壬神定经》L294-L305，逐将为一行，形如「天乙居中贵神主……家在己丑，土神」。
#   L294 天乙己丑土／L295 螣蛇丁巳火／L296 朱雀丙午火／L297 六合乙卯木／L298 勾陈戊辰土／
#   L299 青龙甲寅木／L300 天后壬子水／L301 太阴辛酉金／L302 玄武癸亥水／L303 太常己未土／
#   L304 白虎庚申金／L305 天空戊戌土。
# 本表**只收机械结构**（家支＋五行神）；源文紧随其后的「在旺…在相…在死…在囚…」四段
# 属吉凶断语，按 AGENTS.md 大六壬骨架层纪律**不入结构层**（见 source-readings §五）。
# 五行神与 core 既有一行映射一致，此处只作书源留底，不重造。
TWELVE_JIANG_HOME: dict[str, tuple[str, str]] = {
    "天乙": ("己", "土"), "螣蛇": ("丁", "火"), "朱雀": ("丙", "火"),
    "六合": ("乙", "木"), "勾陈": ("戊", "土"), "青龙": ("甲", "木"),
    "天后": ("壬", "水"), "太阴": ("辛", "金"), "玄武": ("癸", "水"),
    "太常": ("己", "土"), "白虎": ("庚", "金"), "天空": ("戊", "土"),
}

# ---- 四门（2026-10-07 新增，OPT-liuren_shending_dz-02）----
# 书源：《六壬神定经》「释四门第十四」L120-L123 逐门定位（**只录定位，不录吉凶**）：
#   L120「天门：在西北。西北者，戌亥之间……」   L121「地户：在东南。东南者，辰巳之间……」
#   L122「人门：在西南。西南者，申未之间……」   L123「鬼门：在东北。东北者，丑寅之间……」
# 四门本质是**地盘四正（子午卯酉）各带两个「之间」支**的定位，取向即其方位。
# 源文随后的草木黄落／万物已生／万物既成而死／万物死而得生等句属**吉凶物象**，
# 按大六壬骨架层纪律不入结构层（见 AGENTS.md 与 source-readings §五）。
# 每门只存「门名 → 所跨二支」，不存方位吉凶；方位词（西北/东南/西南/东北）亦为
# 书源定位语的一部分，此处**不落**，只保留可机械比对的支对。
FOUR_GATES: dict[str, tuple[str, str]] = {
    "天门": ("戌", "亥"),
    "地户": ("辰", "巳"),
    "人门": ("申", "未"),
    "鬼门": ("丑", "寅"),
}

# 四门所跨支的补集（天地盘各支可反查所属门）：支 → 门名。
FOUR_GATES_BY_BRANCH: dict[str, str] = {
    b: gate for gate, pair in FOUR_GATES.items() for b in pair
}


# ---- 干鬼 / 支鬼 / 干刑三表（2026-10-07 新增，OPT-liuren_shending_dz-05）----
# 书源逐字（去空白后完全一致，故可作「同值必相等」断言）：
#   L150「干鬼者：甲鬼在申，乙鬼在酉，丙鬼在子，丁鬼在亥，戊鬼在寅，己鬼在卯，
#         庚鬼在午，辛鬼在巳，壬鬼在戌，癸鬼在未。」
#   L138「凡干刑所加，战争不出其下。甲刑在申，乙刑在酉，丙刑在子，丁刑在亥，
#         戊刑在寅，己刑在卯，庚刑在午，辛刑在巳，壬刑在戌，癸刑在未。」
#   → 十干刑表与十干鬼表**书源逐字同值**，故此处断言 `GAN_GUI == GAN_XING`
#     （见下方 assert_gan_gui_matches_gan_xing()，供 check.py 负例自证）。
#   L151「支鬼者：子鬼在辰，丑鬼在卯，寅鬼在申，卯鬼在酉，辰鬼在寅，巳鬼在亥，
#         午鬼在子，未鬼在卯，申鬼在午，酉鬼在巳，戌鬼在寅，亥鬼在未。」
#   → 支鬼十二项按地支五行克关系校验：鬼支之五行必克本支之五行（唯一真值源
#     `symbols.KE_CYCLE` / `BRANCH_ELEMENTS`），由 assert_zhi_gui_by_wuxing() 守门。
# 只收「某干/某支之鬼在某支」这一结构映射；源文「谓支干皆有之」等释义断语不入表。
GAN_GUI: dict[str, str] = {
    "甲": "申", "乙": "酉", "丙": "子", "丁": "亥", "戊": "寅",
    "己": "卯", "庚": "午", "辛": "巳", "壬": "戌", "癸": "未",
}
GAN_XING: dict[str, str] = {
    "甲": "申", "乙": "酉", "丙": "子", "丁": "亥", "戊": "寅",
    "己": "卯", "庚": "午", "辛": "巳", "壬": "戌", "癸": "未",
}
ZHI_GUI: dict[str, str] = {
    "子": "辰", "丑": "卯", "寅": "申", "卯": "酉", "辰": "寅", "巳": "亥",
    "午": "子", "未": "卯", "申": "午", "酉": "巳", "戌": "寅", "亥": "未",
}


def assert_gan_gui_matches_gan_xing() -> None:
    """干鬼十项与干刑十项逐项相等（书源 L150 与 L138 逐字同值）。"""
    bad = {k: (GAN_GUI[k], GAN_XING[k]) for k in GAN_GUI if GAN_GUI[k] != GAN_XING[k]}
    if bad:
        raise AssertionError(f"干鬼表与干刑表同值断言失败：{bad}")


def assert_zhi_gui_by_wuxing() -> None:
    """支鬼十二项：鬼支五行必克本支五行（依 core 五行/克关系校验，不另立五行表）。"""
    from .symbols import BRANCH_ELEMENTS, KE_CYCLE  # 内联避免循环 import
    bad = {}
    for zhi, gui in ZHI_GUI.items():
        if KE_CYCLE.get(BRANCH_ELEMENTS[gui]) != BRANCH_ELEMENTS[zhi]:
            bad[zhi] = gui
    if bad:
        raise AssertionError(f"支鬼表五行校验失败：{bad}")


# ---- 三杀位（2026-10-07 新增，OPT-liuren_shending_dz-06）----
# 书源：《六壬神定经》「释杀第十九」L155-L158 按**四组三合**逐组给三位，
#   依 L161「年月三杀者，申子辰，杀在未，亥卯未，杀在戌，寅午戌，杀在丑，巳酉丑，杀在辰」
#   的同一「三合局 → 杀位」句式可推出机械规则：**杀位 = 该三合局顺行第三支**
#   （申子辰→巳，顺三；亥卯未→申；寅午戌→亥；巳酉丑→寅），
#   灾杀居劫杀后一位、天杀再后一位。故下表由该规则生成并与 L155-L158 逐位相等。
# 三杀只报「某支为某杀」的位置标签；源文「寅中有阴气生火也」「卯为日门」等释义
# 与紧随其后的 L160-L161 大段吉凶断语，**一律不入结构层**。
THREE_SHA: dict[str, tuple[str, str, str]] = {
    # 三合局: (劫杀, 灾杀, 天杀)
    "申子辰": ("巳", "午", "未"),
    "亥卯未": ("申", "酉", "戌"),
    "寅午戌": ("亥", "子", "丑"),
    "巳酉丑": ("寅", "卯", "辰"),
}
# 支 → (杀名) 反查表：某支在四组三合下各可能承担的三杀名（并集，不带吉凶）。
BRANCH_SHA_NAMES: dict[str, tuple[str, ...]] = {}
for _grp, _trio in THREE_SHA.items():
    for _nm, _b in zip(("劫杀", "灾杀", "天杀"), _trio):
        BRANCH_SHA_NAMES.setdefault(_b, ())
        if _nm not in BRANCH_SHA_NAMES[_b]:
            BRANCH_SHA_NAMES[_b] += (_nm,)

# 金神三杀（L159）：「金神三杀者，寅申巳亥，三杀在酉。子午卯酉，三杀在巳。
#   辰戌丑未，三杀在丑。」——按支组（非三合）给唯一一位，三组互异不重叠。
JINSEN_SHA: dict[str, tuple[str, ...]] = {
    "寅申巳亥": ("酉",),
    "子午卯酉": ("巳",),
    "辰戌丑未": ("丑",),
}


def assert_three_sha_vs_source() -> None:
    """四组三合各 3 位（共 12 项）与书源 L155-L158 逐位相等；四组并计不重不漏。"""
    # L155-L158 逐位硬录（第一真值即书源；THREE_SHA 由顺行规则生成，此处互校）
    verbatim = {
        "巳酉丑": ("寅", "卯", "辰"),
        "申子辰": ("巳", "午", "未"),
        "亥卯未": ("申", "酉", "戌"),
        "寅午戌": ("亥", "子", "丑"),
    }
    if THREE_SHA != verbatim:
        raise AssertionError(f"三杀位与书源 L155-L158 不等：{THREE_SHA} ≠ {verbatim}")
    seen = [b for trio in THREE_SHA.values() for b in trio]
    if len(seen) != len(set(seen)):
        raise AssertionError(f"四组三合三杀位有重：{sorted(seen)}")


# ---------------------------------------------------------------- 日德
# 卷一「十天干神煞」表：「日徳 寅申巳亥巳寅申己亥已」（甲乙丙丁戊己庚辛壬癸）；
# 第八位原文作「己」、第十位作「已」，均按通例校为「巳」——verified=False 登记。
DAY_DE: dict[str, str] = {
    "甲": "寅", "乙": "申", "丙": "巳", "丁": "亥", "戊": "巳",
    "己": "寅", "庚": "申", "辛": "巳", "壬": "亥", "癸": "巳",
}

# ---- 日德·神定经双表（2026-10-07 新增，OPT-liuren_shending_dz-04）----
# 与上表 **语义不同、并非讹误**，故并存而不互相覆盖，消费方须显式择表：
#   · DAY_DE（大全套）：日干寄宫，取自卷一「十天干神煞」，甲→寅、乙→申…
#   · DAY_DE_SHENDING（本表）：干合配对，取自《六壬神定经》源L127
#     「十干德者，甲、丙、戊、庚、壬阳干，德自处。乙德在庚，丁德在壬，己德在甲，
#       辛德在丙，癸德在戊。」——即阳干德自处（配自身宫）、阴干德在干合之干的宫。
#   两套口径若混用会得出相反结论，故在表名与注释中显式区分书源与口径。
DAY_DE_SHENDING: dict[str, str] = {
    "甲": "甲", "丙": "丙", "戊": "戊", "庚": "庚", "壬": "壬",  # 阳干：德自处
    "乙": "庚", "丁": "壬", "己": "甲", "辛": "丙", "癸": "戊",  # 阴干：德在干合之干
}

# 支德（神定经体系）：源L128「子在巳，丑在午，寅在未，卯在申，辰在酉，巳在戌，
#   午在亥，未在子，申在丑，酉在寅，戌在卯，亥在辰。十二支德，岁月日时同用。」
ZHI_DE_SHENDING: dict[str, str] = {
    "子": "巳", "丑": "午", "寅": "未", "卯": "申", "辰": "酉", "巳": "戌",
    "午": "亥", "未": "子", "申": "丑", "酉": "寅", "戌": "卯", "亥": "辰",
}

# 干合（日德辨伪与合神关系用，甲己/乙庚/丙辛/丁壬/戊癸）——唯一真值源在 relations.STEM_WUHE
from .relations import STEM_WUHE as STEM_HE  # noqa: E402


# ---- 行年起法（2026-10-14 新增，OPT-liuren_cuiyan_dz-02）----
# 书源：《六壬粹言》L27「行年第九」逐字：
#   「行年之法，男起丙寅，女起壬申，此正法也。……夫人生于寅，为岁月之首建，
#      是以男从寅起，申者寅之对也，是以女人申起。」
# ── 口径 ──────────────────────────────────────────────────────────────
# · 男从地盘「寅」位起「丙寅」，**顺行**（每岁天盘支退一位，干从支遁）；
# · 女从地盘「申」位起「壬申」，**逆行**（每岁天盘支进一位，干从支遁）；
# · 此函数**只提供起法换算**：给 生年干支＋性别＋年数（几岁），循上述规则
#   机械反推「行年落点干支」；**不接入推理链**（analyze 不调用），留待后续
#   接入层按需取用。
# ── 机械定义 ──────────────────────────────────────────────────────────
# 十干寄宫 JI_GONG（core 唯一真值源）知：丙午同寄「巳」、壬亥同寄「亥」。
# 「从地盘寅起丙寅」＝天盘寅上神起算落在「丙寅」这一对 → 天盘寅位起丙干、
# 天盘申位起壬干；配合 EARTHLY_BRANCHES 顺/逆位移即得。
_CINXING_MALE = "丙寅"    # 男起丙寅（地盘寅位、顺行）
_CINXING_FEMALE = "壬申"  # 女起壬申（地盘申位、逆行）


def _ganzhi_at(start_ganzhi: str, direction: int, age: int) -> str:
    """从 `start_ganzhi` 起，按 direction（+1 顺行／-1 逆行）位移 age 步得干支。

    六十甲子循环：start_ganzhi 须以六十甲子序索引（ganzhi_calendar.ganzhi_pair）
    反推；位移 age 步后回取配对干支。
    """
    s_idx = next(i for i in range(60) if ganzhi_pair(i) == start_ganzhi)
    t_idx = (s_idx + direction * age) % 60
    return ganzhi_pair(t_idx)


def xingnian_of(birth_ganzhi: str, gender: str, age: int) -> dict:
    """行年起法：男起丙寅顺行／女起壬申逆行（OPT-liuren_cuiyan_dz-02）。

    书源：《六壬粹言》行年第九 L27 逐字「行年之法，男起丙寅，女起壬申，此正法也。」
    唐·一行禅师《六壬髓胻》通行口径同此。

    Args:
        birth_ganzhi: 求测者出生年干支（六十甲子之一，如「甲子」）
        gender: "男" 或 "女"
        age: 行年数（几岁；实岁；0 岁为出生当年）

    Returns: {"gender", "birth_ganzhi", "start_ganzhi", "direction", "age",
              "xingnian_ganzhi", "basis"}
        direction: "顺行"｜"逆行"；start_ganzhi: 起算点对（男丙寅／女壬申）；
        xingnian_ganzhi: 行年落点干支。

    只提供起法换算，**不接入推理链**——留待 synthesis / narrate 层按需调用；
    引擎 analyze.py 段**不调此函数**，避免在结构层引入吉凶路径。
    """
    if gender == "男":
        start = _CINXING_MALE
        direction = +1
    elif gender == "女":
        start = _CINXING_FEMALE
        direction = -1
    else:
        raise ValueError(f"gender 须为「男」或「女」：{gender!r}")
    xingnian_ganzhi = _ganzhi_at(start, direction, age)
    return {
        "gender": gender,
        "birth_ganzhi": birth_ganzhi,
        "start_ganzhi": start,
        "direction": "顺行" if direction > 0 else "逆行",
        "age": age,
        "xingnian_ganzhi": xingnian_ganzhi,
        "basis": "《六壬粹言》L27「行年之法，男起丙寅，女起壬申，此正法也。」",
    }
