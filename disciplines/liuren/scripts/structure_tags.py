# -*- coding: utf-8 -*-
"""大六壬·正交结构标签维度（与课目并列，**只报结构，不出任何吉凶断语**）。

课目（`kemu.py`）判的是「像什么课」；本模块判的是「盘面在哪个维度上是什么形态」，
两者**互不覆盖、并列输出**：同一课可同时命中多条课目与多个结构标签。

铁律（AGENTS.md）：大六壬是骨架层。书源里的吉凶断语、祸福、应期一律**不得**进本层；
本模块只允许出现「某支／某位／某将／某五行」这类机械事实。
每条标签的 `basis` 必须写清书源行号与判定条件，`note` 只写判据边界（未并入哪些书源附加条件）。

标签组一览（括号内为 OPT 编号）：
  A 组 入课判别  not_entered          他处发用（发用是否落在四课之上）
  B 组 日辰旬空  xunkong_grade        旬空落初／中／末三档（斩首／折腰／刖足）
                  sanjian             三奸（亥子丑临地盘四仲，其对冲位）
  C 组 寄宫位序  qian_hou             寄宫前一位／后一位（纯位序，不含已往／将来方向）
  D 组 将神克战  jia_ke / nei_zhan / wai_zhan
  E 组 类神类将  class_god            类神之三传（初传／中传／末传）
                  class_jiang         类将主／备回退链
  F 组 昼夜分途  day_night_route      同神昼夜乘临不同将 → 生克分途
  G 组 时辰定位  san_gong_shi         三宫时（绛宫／明堂／玉堂）定位条件
                  tianluo_diwang      天罗（日前一辰）／地网（其对冲）
  H 组 干支鬼煞  gan_gui / zhi_gui / gan_xing / three_sha / jinsen_sha / four_gate
  I 组 吟式远近  fuyin_fanyin_jiuyuan  伏吟事近／返吟事远（灵辖经引，《六壬神定经》L342）
                  ri_zao_tian_yi     日辰阴阳在天一前主事速、后主事迟（源L342）
  J 组 三传几何格 san_chuan_seven_ge  全财／全鬼／全脱／俱阳／俱阴／递生／递克（《六壬鬼谷》L148-L154）
"""
from __future__ import annotations

from yishu_core.ganzhi_calendar import EARTHLY_BRANCHES as _BR
from yishu_core.liuren_tables import (
    FOUR_GATES_BY_BRANCH,
    GAN_GUI,
    GAN_XING,
    JINSEN_SHA,
    JI_GONG,
    NOBLE_DAY,
    NOBLE_NIGHT,
    THREE_SHA,
    TWELVE_JIANG_HOME,
    ZHI_GUI,
    is_day,
    tianjiang_layout,
)
from yishu_core.symbols import (
    BRANCH_ELEMENTS,
    CHONG_PAIRS,
    KE_CYCLE,
    SHENG_CYCLE,
    STEM_ELEMENTS,
    wangxiangxiuqiusi,
    xunkong_of,
)

from jiuzongmen import four_courses

_CHONG_OF: dict[str, str] = {}
for _a, _b in CHONG_PAIRS:
    _CHONG_OF[_a] = _b
    _CHONG_OF[_b] = _a

_MENG = frozenset({"寅", "子", "辰", "申"})          # 四孟
_ZHONG = frozenset({"子", "午", "卯", "酉"})          # 四仲
_JIA_GUI = frozenset({"亥", "子", "丑"})              # 三奸之孟位（书源只列此三支）


def _elem(x: str) -> str:
    return BRANCH_ELEMENTS.get(x) or STEM_ELEMENTS.get(x) or ""


def _ke(a: str, b: str) -> bool:
    """a 的五行克 b 的五行（a、b 可为天干或地支）。"""
    ea, eb = _elem(a), _elem(b)
    return bool(ea and eb) and KE_CYCLE[ea] == eb


def _sheng_elem(a: str, b: str) -> bool:
    """五行元素 a 生 b（a、b 已为五行 string，非干支符号）。"""
    return SHENG_CYCLE.get(a, "") == b and bool(a)


def _ke_cycle(a: str, b: str) -> bool:
    """五行元素 a 克 b（a、b 已为五行 string，非干支符号）。"""
    return KE_CYCLE.get(a, "") == b and bool(a)


def _tag(dim: str, name: str, basis: str, note: str = "") -> dict:
    return {"dim": dim, "name": name, "basis": basis, "note": note}


# ══════════════════════════════════════════════ A 组 · 入课判别
def not_entered(chart_out: dict) -> list[dict]:
    """`not_entered`：发用是否落在四课之上（OPT-liuren_cuiyan_dz-07）。

    书源《六壬粹言》以「他处发用」称发用不在四课之上者。本判据只作**正交标签**：
    取初传所临之地盘位，若该位不属于四课的任一「下神」（地盘四位），则为「他处发用」。
    只报在／不在，不含任何吉凶措辞。
    """
    day_gz = (chart_out.get("moment") or {}).get("day_ganzhi") or ""
    san = chart_out.get("san_chuan") or []
    tianpan = chart_out.get("tianpan") or {}
    if len(day_gz) < 2 or not san or not tianpan:
        return []
    courses = four_courses(day_gz[0], day_gz[1], tianpan)
    xia = [c["xia"] for c in courses]
    chu = san[0]
    lin = next((p for p, s in tianpan.items() if s == chu), "")
    inside = lin in xia
    return [_tag(
        "not_entered",
        "入四课" if inside else "他处发用",
        f"初传{chu}临地盘{lin or '—'}；四课下神（地盘位）{'、'.join(xia)}",
        "「他处发用」仅为位置标签，不含吉凶；书源以之起课须并入者本标签不预判",
    )]


# ══════════════════════════════════════════════ B 组 · 旬空与三奸
def xunkong_grade(chart_out: dict) -> list[dict]:
    """旬空落三传分档：初斩首／中折腰／末刖足（OPT-liuren_zhinan_dz-06）。

    书源《六壬指南》L582：`空亡乃耗散之神，初斩首、中折腰、末刖足。`
    旬空两支（旬空唯一真值源 core `xunkong_of`）落在初／中／末哪一传，即为哪一档名目。
    **只报档位与落位，不带吉凶**；「斩首／折腰／刖足」三名为书源既有档名，非本层自造。
    """
    day_gz = (chart_out.get("moment") or {}).get("day_ganzhi") or ""
    san = chart_out.get("san_chuan") or []
    if len(day_gz) < 2 or len(san) != 3:
        return []
    kong = set(xunkong_of(day_gz))
    grade = {"初": "斩首", "中": "折腰", "末": "刖足"}
    out: list[dict] = []
    for pos, br in zip(("初", "中", "末"), san):
        if br in kong:
            out.append(_tag(
                "xunkong_grade", grade[pos],
                f"旬空{'、'.join(sorted(kong))}落{pos}传{br}",
                "档名为书源既有语，只报落位档次，不判吉凶",
            ))
    return out


def sanjian(chart_out: dict) -> list[dict]:
    """三奸位置标签（OPT-liuren_zhinan_dz-06）。

    书源《六壬指南》L714：`凡亥子丑有一位加于地盘仲上，则对冲处便为三奸。对冲视天盘天后。`
    判据：亥／子／丑任一为天盘神、且所临地盘位属四仲（子午卯酉）者，取该地盘位的**对冲位**
    为三奸位；对冲取 core 六冲表（唯一真值源），不另立冲表。
    只报位置，不带吉凶。
    """
    tianpan = chart_out.get("tianpan") or {}
    if not tianpan:
        return []
    out: list[dict] = []
    for lin, sky in tianpan.items():
        if sky in _JIA_GUI and lin in _ZHONG:
            out.append(_tag(
                "sanjian", f"三奸在{_CHONG_OF[lin]}",
                f"{sky}加地盘{lin}（四仲），其对冲位为{_CHONG_OF[lin]}",
                "书源另云「对冲视天盘天后、日辰比和俱重」，此为断语 weighting，未并入本层",
            ))
    return out


# ══════════════════════════════════════════════ C 组 · 寄宫位序
def qian_hou(chart_out: dict) -> list[dict]:
    """寄宫前一位／后一位纯位序标签（OPT-liuren_zhinan_dz-08）。

    书源《六壬指南》L363：`如甲课在寅则卯为后而丑为前。盖前为已往，后为未来故也。`
    规则：甲寄寅 → 后＝寅＋一位＝卯、前＝寅－一位＝丑，故 **后＝寄宫顺行一位、前＝逆行一位**
    （十干皆同，可由该例机械推广）。本标签**只报位序**（前／后两位各是哪一支），
    「已往／将来」是书源的方向断语，**不入本层**，不参与任何方向判断。
    """
    day_gz = (chart_out.get("moment") or {}).get("day_ganzhi") or ""
    if len(day_gz) < 2:
        return []
    jigong = JI_GONG[day_gz[0]]
    i = _BR.index(jigong)
    hou, qian = _BR[(i + 1) % 12], _BR[(i - 1) % 12]
    return [_tag(
        "qian_hou", f"{day_gz[0]}寄{jigong}·前{qian}后{hou}",
        f"日干{day_gz[0]}寄宫{jigong}；前一位（逆行一位）＝{qian}，后一位（顺行一位）＝{hou}",
        "书源以「前为已往、后为未来」作方向断语，本层只取位序、不作方向判断",
    )]


# ══════════════════════════════════════════════ D 组 · 将神克战
def _jiang_elem(jiang: str) -> str:
    """天将的五行神（书源《六壬神定经》L294-L305 十二将家支五行神，core 唯一真值源）。"""
    entry = TWELVE_JIANG_HOME.get(jiang)
    return entry[1] if entry else ""


def jia_ke_nei_wai(chart_out: dict) -> list[dict]:
    """夹克／内战／外战三条**互斥**结构条件（OPT-rengui_dz-04）。

    书源出处与判据（断语一律不入本层）：
    · 夹克——用神（初传）**上下同克**：《六壬大全》卷11 L227 甲子日辰加寅为初传例，
      初传辰临寅（木克土＝下神克用）而乘六合（六合五行神木，木克土＝将神克用），
      源文自称「其财受上下夹克」；故夹克＝**下临地盘克用 且 所乘天将五行神克用**。
      同书卷12 家法不正格「乙丑、乙卯、乙亥日并寅加酉」亦为三传皆受夹克，两处互证。
    · 内战／外战——《六壬神定经》L351 `神克将为内战，将克神为外战`，
      通行表述取《六壬大全》卷10「六合附金，谓之内战…附土神谓之外战」：
      内战＝所乘之支的五行克该将的五行神；外战＝该将的五行神克所乘之支的五行。
      本层按此定义取**内／外战互斥**（二者由 KE_CYCLE 互逆，不可能同时成立）。
    · 元武无内战（《六壬粹言》L311 书源自陈）作为**负例登记**留在 note，不作正向判据。
    """
    day_gz = (chart_out.get("moment") or {}).get("day_ganzhi") or ""
    san = chart_out.get("san_chuan") or []
    tianpan = chart_out.get("tianpan") or {}
    hour = (chart_out.get("moment") or {}).get("hour_branch") or ""
    if len(day_gz) < 2 or not san or not tianpan or not hour:
        return []
    layout = tianjiang_layout(day_gz[0], hour, tianpan)
    out: list[dict] = []
    for pos, br in zip(("初", "中", "末"), san):
        lin = next((p for p, s in tianpan.items() if s == br), "")
        if not lin:
            continue
        jiang = layout.get(lin, "")
        je = _jiang_elem(jiang)
        lower_ke = _ke(lin, br)                  # 下临地盘克用神
        jiang_ke = bool(je) and KE_CYCLE.get(je) == _elem(br)   # 将神克用神
        if lower_ke and jiang_ke:
            out.append(_tag(
                "jia_ke", f"{pos}传{br}夹克",
                f"{pos}传{br}临{lin}（{_elem(lin)}克{_elem(br)}），乘{jiang}"
                f"（五行神{je}克{_elem(br)}），上下同克",
                "书源卷11 L227／卷12 家法不正格两处互证；只报结构，不判「不由己」等断语",
            ))
        # 内战／外战只就「所乘之支 vs 该将五行神」论，与用神无关，故每传只报一次
        le = BRANCH_ELEMENTS.get(lin, "")
        if je and le:
            if KE_CYCLE.get(le) == je:
                out.append(_tag(
                    "nei_zhan", f"{jiang}内战（临{lin}）",
                    f"{jiang}五行神{je}，所乘{lin}为{le}，{le}克{je}（神克将为内战）",
                    "《六壬粹言》L311 自陈「惟元武无内战例」，作负例登记，不改本判据",
                ))
            elif KE_CYCLE.get(je) == le:
                out.append(_tag(
                    "wai_zhan", f"{jiang}外战（临{lin}）",
                    f"{jiang}五行神{je}，所乘{lin}为{le}，{je}克{le}（将克神为外战）",
                    "只报内外战之别，祸害轻重之断语不入本层",
                ))
    return out


# ══════════════════════════════════════════════ E 组 · 类神类将
# 类将主／备回退链（《六壬鬼谷》L663 逐字）：
#   「如占贵人尊长，本当专视责天乙，若或课传无天局，而大吉出现，则视大吉之三传以断吉凶。
#     不必更求天乙矣。如占财帛本应专责青龙，如或无青龙，而功曹出现，则视功曹之乘临，
#     以及三传，不必更求青龙矣。或式中无青龙，而太常出现，则视太常之三传以定休咎，
#     不必更求青龙功曹矣。是即所谓变通也。」
# 源文「无天局」为「无天乙」之脱字（上下文三处皆作天乙），此处按上下文校为天乙并标注。
CLASS_JIANG_FALLBACK: dict[str, tuple[str, ...]] = {
    "天乙": ("天乙", "大吉"),
    "青龙": ("青龙", "功曹", "太常"),
}


def class_jiang(present: list[str], primary: str) -> dict:
    """类将主／备回退（《六壬鬼谷》L663）：给定课中出现的天将名，返回实际取用之类将与回退链。

    只报「取哪一将」这一机械事实，不带任何吉凶（源文「以断吉凶」「定休咎」不入本层）。
    """
    chain = CLASS_JIANG_FALLBACK.get(primary, (primary,))
    for name in chain:
        if name in present:
            return {
                "类将": name,
                "位次": "主" if name == chain[0] else "备",
                "回退链": list(chain),
                "依据": "《六壬鬼谷》L663 变通法：无主将则取次列之将",
            }
    return {"类将": "", "位次": "无", "回退链": list(chain),
            "依据": "《六壬鬼谷》L663 变通法：三列皆不在课中"}


def class_god(chart_out: dict, jiang: str) -> list[dict]:
    """类神之三传（OPT-rengui_dz-05）。

    书源《六壬鬼谷》L649：`后所乘神，即为初传，初之阴神即为中传，中再传之神，即为末传，
    是即所谓类神之三传。` —— 即**类将所乘之神＝初传；初传之阴神（上神）＝中传；
    中传之阴神（上神）＝末传**。这是与九宗门三传**并存**的另一组三传，本层只并列输出，
    **不改九宗门取传判定**（AGENTS.md：不得为让某例过关改通用规则）。
    只报三支，不带任何取象吉凶（源文「所以不必全拘课体而断吉凶」之类不入本层）。
    """
    tianpan = chart_out.get("tianpan") or {}
    if not tianpan or jiang not in TWELVE_JIANG_HOME:
        return []
    lin = next((p for p, j in tianjiang_layout_items(chart_out).items() if j == jiang), "")
    if not lin:
        return [_tag("class_god", "类将不入课",
                     f"{jiang}未乘临任何地盘位，类神之三传无从取",
                     "书源 L181「所筮不入仍凭类」：不在课中仍当视其方位，此为负例登记")]
    chu = tianpan[lin]                       # 类将所乘之神
    zhong = tianpan.get(chu, "")             # 初传之阴神
    mo = tianpan.get(zhong, "")              # 中传之阴神
    return [_tag(
        "class_god", f"类神之三传 {chu}·{zhong}·{mo}",
        f"{jiang}乘{lin}，所乘之神{chu}为初传；{chu}上神{zhong}为中传；{zhong}上神{mo}为末传",
        "类神三传与九宗门三传并存，本层并列输出、不改九宗门取传；取象吉凶不入本层",
    )]


def tianjiang_layout_items(chart_out: dict) -> dict[str, str]:
    day_gz = (chart_out.get("moment") or {}).get("day_ganzhi") or ""
    hour = (chart_out.get("moment") or {}).get("hour_branch") or ""
    tianpan = chart_out.get("tianpan") or {}
    if len(day_gz) < 2 or not hour or not tianpan:
        return {}
    return tianjiang_layout(day_gz[0], hour, tianpan)


# ══════════════════════════════════════════════ F 组 · 昼夜乘临分途
def day_night_route(chart_out: dict) -> list[dict]:
    """同神昼夜乘临不同将 → 生克分途（OPT-liuren_zhizhi_yuding_dz-05）。

    书源《六壬直指御定》L679：`巳临庚上，昼乘勾陈，则土将能生。夜乘朱雀，则火将为克，
    天将生克，吉凶分途矣。`
    ⚠ 口径澄清（本条**不是**「昼夜两套将」）：十二天将名与其五行神昼夜**同一**，
    变的是**同一位支在昼夜所乘之将不同**——因贵人昼夜取支不同，顺逆随之而异，
    故同一天盘支白昼与夜间可乘不同将，从而与用神的生克**分途**。
    本标签按此口径实现：对三传各位分别给出昼／夜两套布局下所乘之将与生克方向，
    **只在两者不同（或生克方向不同）时报出**，是纯结构对照，不含吉凶。
    """
    day_gz = (chart_out.get("moment") or {}).get("day_ganzhi") or ""
    san = chart_out.get("san_chuan") or []
    tianpan = chart_out.get("tianpan") or {}
    hour = (chart_out.get("moment") or {}).get("hour_branch") or ""
    if len(day_gz) < 2 or len(san) != 3 or not tianpan or not hour:
        return []
    day_stem = day_gz[0]
    # 昼／夜两套贵人支 → 两套布局（用同一日干，取一日之昼时与夜时两个代表时辰）
    _d, _n = "午", "子"                      # 昼、夜各取一个代表时辰（卯酉分界内）
    lay_day = tianjiang_layout(day_stem, _d, tianpan)
    lay_night = tianjiang_layout(day_stem, _n, tianpan)
    out: list[dict] = []
    for pos, br in zip(("初", "中", "末"), san):
        lin = next((p for p, s in tianpan.items() if s == br), "")
        if not lin:
            continue
        jd, jn = lay_day.get(lin, ""), lay_night.get(lin, "")
        if jd == jn:
            continue                          # 同将 → 不分途，不报
        ed, en = _jiang_elem(jd), _jiang_elem(jn)
        be = _elem(br)

        def _dir(e: str) -> str:
            if not e:
                return "—"
            if e == be:
                return "比和"
            if KE_CYCLE.get(e) == be:
                return "将克用"
            if KE_CYCLE.get(be) == e:
                return "用克将"
            return "生克无涉"

        dd, dn = _dir(ed), _dir(en)
        out.append(_tag(
            "day_night_route", f"{pos}传{br}昼夜分途",
            f"{br}临{lin}：昼乘{jd}（{ed}·{dd}）／夜乘{jn}（{en}·{dn}）",
            "口径：同神昼夜乘临不同将则生克分途，非「昼夜两套将」；只报将—用生克方向，不判吉凶",
        ))
    return out


# ══════════════════════════════════════════════ G 组 · 时辰定位
def san_gong_shi(chart_out: dict) -> list[dict]:
    """三宫时定位条件（OPT-liuren_xinjing_dz-02）。

    书源《六壬星纪》逐条给出三个**时辰**的定位条件（皆为纯定位，不附吉凶）：
      L796 `登明加四仲，名绛宫时`      → 月将登明（亥）加时，亥所临地盘位属四仲
      L800 `神后加仲为明堂时`          → 月将神后（子）加时，子所临地盘位属四仲
      L804 `大吉加四仲，名玉堂时`      → 月将大吉（丑）加时，丑所临地盘位属四仲
    实现取「月将支所临的地盘位」判四仲，不另立将名→支表（月将支唯一真值源在 core）。
    标签只报「时属何宫时」这一机械事实；源文紧随的吉凶断语**一律不入本层**。
    """
    yj = (chart_out.get("yuejiang") or {}).get("branch") or ""
    tianpan = chart_out.get("tianpan") or {}
    if not yj or not tianpan:
        return []
    lin = next((p for p, s in tianpan.items() if s == yj), "")
    if not lin or lin not in _ZHONG:
        return []
    # 将名取自 core 月将表（唯一真值源），此处只作标签显示用
    from yishu_core.liuren_tables import ZHONGQI_YUEJIANG
    jiang_name = next((n for _, (b, n) in ZHONGQI_YUEJIANG.items() if b == yj), "")
    gong = {"亥": "绛宫时", "子": "明堂时", "丑": "玉堂时"}.get(yj, "")
    if not gong:
        return []
    return [_tag(
        "san_gong_shi", gong,
        f"月将{jiang_name}（{yj}）加时，{yj}临地盘{lin}（四仲）",
        "书源 L796／L800／L804 三条定位条件；只报定位，不附任何吉凶词",
    )]


def tianluo_diwang(chart_out: dict) -> list[dict]:
    """天罗地网定位标签（OPT-liuren_xinjing_dz-02）。

    书源《六壬星纪》L466：`日前一辰天罗杀，对冲名为地网神。发用行年支干上，官灾病厄是其迍
    如庚日庚课申，则酉为天罗，卯为地网。` —— 按该例（庚日申→酉、卯）可定：
    **天罗＝日支顺行一位；地网＝天罗之对冲**。对冲取 core 六冲表（唯一真值源）。
    ⚠ 本标签**只落结构**（哪两位是罗、哪两位是网），**不占课体名**（书源名相虽作「杀／神」，
    本层不入课目表）；发用行年条件与吉凶断语不在本层。
    """
    day_gz = (chart_out.get("moment") or {}).get("day_ganzhi") or ""
    if len(day_gz) < 2:
        return []
    db = day_gz[1]
    tianluo = _BR[(_BR.index(db) + 1) % 12]
    diwang = _CHONG_OF[tianluo]
    return [_tag(
        "tianluo_diwang", f"天罗在{tianluo}·地网在{diwang}",
        f"日支{db}前（顺行一位）为天罗{tianluo}；其对冲位为地网{diwang}"
        f"（书源例：庚日庚课申则酉为天罗、卯为地网，与此式相合）",
        "只报罗网定位；「发用行年支干上」与吉凶断语不入本层，亦不占课体名",
    )]


# ══════════════════════════════════════════════ H 组 · 干支鬼煞与四门
def gui_sha_four_gate(chart_out: dict, class_jiang_name: str = "") -> list[dict]:
    """干鬼／支鬼／干刑／三杀／金神三杀／四门六组结构标签。

    全部取 core 唯一真值源（`liuren_tables.py`，2026-10-07 新，OPT-shending-05/06/02），
    书源逐字：干鬼 L150、支鬼 L151、干刑 L138、三杀 L155-L159、四门 L120-L123。
    只报「某支／某位为某名目」，不带吉凶（源文释义与断语一律不入本层）。
    """
    out: list[dict] = []
    san = chart_out.get("san_chuan") or []
    tianpan = chart_out.get("tianpan") or {}

    # 干鬼／干刑：两表书源逐字同值，故同一命中同时报两个名目
    for pos, br in zip(("初", "中", "末"), san):
        hit_stems = [s for s, g in GAN_GUI.items() if g == br]
        if hit_stems:
            out.append(_tag(
                "gan_gui", f"{pos}传{br}为{'/'.join(hit_stems)}之干鬼",
                f"干鬼表（源L150）：{'、'.join(f'{s}鬼在{br}' for s in hit_stems)}",
                f"干刑表（源L138）与干鬼表书源逐字同值，故此支同时为{'/'.join(hit_stems)}之干刑",
            ))
        hit_zhi = [z for z, g in ZHI_GUI.items() if g == br]
        if hit_zhi:
            out.append(_tag(
                "zhi_gui", f"{pos}传{br}为{'/'.join(hit_zhi)}之支鬼",
                f"支鬼表（源L151）：{'、'.join(f'{z}鬼在{br}' for z in hit_zhi)}",
                "支鬼十二项已由 core 按地支五行克关系校验",
            ))
    # 三杀位（按四组三合；只报位置）
    for grp, trio in THREE_SHA.items():
        for nm, br in zip(("劫杀", "灾杀", "天杀"), trio):
            if br in san:
                pos = ("初", "中", "末")[list(san).index(br)]
                out.append(_tag(
                    "three_sha", f"{pos}传{br}为{grp}局{nm}",
                    f"三杀表（源L155-L158）：{grp}局 {nm}在{br}",
                    "只报「某支为某杀」位置；源文释义与大段吉凶断语不入本层",
                ))
    for grp, trio in JINSEN_SHA.items():
        for br in trio:
            if br in san:
                pos = ("初", "中", "末")[list(san).index(br)]
                out.append(_tag(
                    "jinsen_sha", f"{pos}传{br}为金神三杀（{grp}）",
                    f"金神三杀（源L159）：{grp}三杀在{br}",
                    "只报位置；源文「金神三杀最恶」等断语不入本层",
                ))
    # 四门：按传神所临地盘位反查（地盘位落在某门两支之间）
    for pos, br in zip(("初", "中", "末"), san):
        lin = next((p for p, s in tianpan.items() if s == br), "")
        gate = FOUR_GATES_BY_BRANCH.get(lin, "")
        if gate:
            out.append(_tag(
                "four_gate", f"{pos}传{br}临地盘{lin}（{gate}）",
                f"四门表（源L120-L123）：{gate}跨{'/'.join(_br_pair(gate))}；"
                f"初传{br}所临地盘位为{lin}",
                "只报门位定位；源文方位吉凶与物象断语不入本层",
            ))
    return out


def _br_pair(gate: str) -> tuple[str, str]:
    from yishu_core.liuren_tables import FOUR_GATES
    return FOUR_GATES[gate]


# ══════════════════════════════════════════════ I 组 · 吟式远近与天一前后
# 《六壬神定经》L342：`伏吟事近，返吟事远。...日辰阴阳，在天一前主事速，在天一后主事迟也。`


def fuyin_fanyin_jiuyuan(chart_out: dict) -> list[dict]:
    """伏吟事近／返吟事远纯结构标签（OPT-liuren_shending_dz-07）。

    书源《六壬神定经》L342：`伏吟事近，返吟事远。`（原注「事近」/「事远」为灵辖经引文）
    —— `伏吟` 为教义/人事类卜的「时间距离」名目，本层只报「构型上属吟式」这一机械事实，
    **不带任何应期推断**；「事近/事远」是书源既有名目，非本仓断语自造。
    判据：九宗门落定宗门名（chart_out["men"]）直接映射——伏吟 → 「事近」名目、
    返吟 → 「事远」名目。其余宗门不触本标签。
    """
    men = chart_out.get("men") or ""
    if men == "伏吟":
        return [_tag(
            "fuyin_fanyin_jiuyuan", "伏吟·事近",
            "宗门为伏吟",
            "源 L342「伏吟事近」；「事近」为灵辖经引文名目，本层只报构型，不作应期断言",
        )]
    if men == "返吟":
        return [_tag(
            "fuyin_fanyin_jiuyuan", "返吟·事远",
            "宗门为返吟",
            "源 L342「返吟事远」；「事远」为灵辖经引文名目，本层只报构型，不作应期断言",
        )]
    return []


def ri_zao_tian_yi(chart_out: dict) -> list[dict]:
    """日辰阴阳在天一前主事速／在天一后主事迟（OPT-liuren_shending_dz-07）。

    书源《六壬神定经》L342：`日辰阴阳，在天一前主事速，天一后主事迟也。`
    天一 ＝ 天乙贵人（贵人支＝天乙所临之地盘位）。方位以十二支环（子→丑→寅→卯→
    辰→午未申酉戌亥→子）论，只取两支的序位远近作机械比较，**不带吉凶推断**。
    贵人支唯一真值源：core `NOBLE_DAY` / `NOBLE_NIGHT` 表（同日干昼夜两取），
    昼夜以 hour_branch 卯酉分界（core `is_day`）决定。天一(贵人支) 所临之地盘位，
    由 tianpan {地盘位: 天盘支} 反查（贵人支落在哪一个地盘位上）。
    """
    moment = chart_out.get("moment") or {}
    day_gz = moment.get("day_ganzhi") or ""
    hour = moment.get("hour_branch") or ""
    tianpan = chart_out.get("tianpan") or {}
    if len(day_gz) < 2 or not hour or not tianpan:
        return []
    day_stem = day_gz[0]
    day_flag = is_day(hour)
    noble_branch = (NOBLE_DAY if day_flag else NOBLE_NIGHT).get(day_stem, "")
    if not noble_branch:
        return []
    # 天一(贵人支)所临之地盘位
    tian_yi_pos = next((p for p, s in tianpan.items() if s == noble_branch), "")
    day_branch = day_gz[1]
    if not tian_yi_pos:
        return []
    idx_ty = _BR.index(tian_yi_pos)
    idx_rd = _BR.index(day_branch)
    dist_cw = (idx_rd - idx_ty) % 12
    dist_ccw = (idx_ty - idx_rd) % 12
    if dist_cw < dist_ccw:
        position = "在天一前（逆时针近）"
    elif dist_ccw < dist_cw:
        position = "在天一后（顺时针近）"
    else:
        position = "正对天一（等距）"
    return [_tag(
        "ri_zao_tian_yi", f"日支{day_branch}{position}",
        f"天一(贵人{noble_branch})临地盘{tian_yi_pos}({idx_ty})，日支{day_branch}({idx_rd})，"
        f"顺时针差{dist_cw}步/逆时针差{dist_ccw}步",
        f"源 L342「日辰阴阳在天一前主事速/后主事迟」；只报位置，不判吉凶/应期",
    )]


# ══════════════════════════════════════════════ J 组 · 三传几何格
# 《六壬鬼谷》卷三·明三传始终第三（L148-L154）：7 纯几何格
#   · 全财／全鬼／全脱：三传三支元素对日干元素的统一关系
#   · 俱阳／俱阴：三传三支在 子寅辰午申戌（阳）或 丑卯巳未酉亥（阴）同一侧
#   · 递生／递克：四节点（三传＋日干）间的单向链，顺逆两向皆格
_YANG_BRANCHES = frozenset({"子", "寅", "辰", "午", "申", "戌"})
_YIN_BRANCHES = frozenset({"丑", "卯", "巳", "未", "酉", "亥"})


def san_chuan_seven_ge(chart_out: dict) -> list[dict]:
    """三传结构七格（OPT-rengui_dz-01）。

    书源《六壬鬼谷》卷三·明三传始终第三（L148-L154）逐字：
      L148 三传俱为日干所克 → 全财
      L149 三传俱克日干 → 全鬼
      L150 三传俱受日干之生 → 全脱（**日干生三传**，非三传生日干）
      L152 三传俱阳（子寅辰午申戌）→ 俱阳；三传俱阴（丑卯巳未酉亥）→ 俱阴
      L153 初生中、中生末、末生干 → 递生；或 末生中、中生初、初生日干 → 递生
      L154 未克中、中克初、初克日干 → 递克；或 初克中、中克末、末克日干 → 递克
    释义与词句（「财多反为不美」「事必显著／隐秘」等）归数据层 data/verdicts.json#san_chuan，
    **本层只报几何命中**，不判吉凶。
    """
    moment = chart_out.get("moment") or {}
    day_gz = moment.get("day_ganzhi") or ""
    san = chart_out.get("san_chuan") or []
    if len(day_gz) < 2 or len(san) != 3:
        return []
    stem = day_gz[0]
    se = STEM_ELEMENTS.get(stem, "")
    be = [BRANCH_ELEMENTS.get(b, "") for b in san]
    if not se or not all(be):
        return []
    chu, zhong, mo = san
    ce, zhe, me = be
    out: list[dict] = []

    # 全财／全鬼／全脱（三支对日干统一关系）
    if se and ce and zhe and me:
        if all(KE_CYCLE.get(se) == x for x in (ce, zhe, me)):
            out.append(_tag("san_chuan", "全财",
                            f"日干{stem}({se})克三传{chu}({ce})、{zhong}({zhe})、{mo}({me})，"
                            f"三传俱为日干所克",
                            "源 L148「全财」；财多反为不美为数据层引文，本层不判吉凶"))
        if all(KE_CYCLE.get(x) == se for x in (ce, zhe, me)):
            out.append(_tag("san_chuan", "全鬼",
                            f"三传{chu}({ce})、{zhong}({zhe})、{mo}({me})俱克日干{stem}({se})，"
                            f"三传俱克日干",
                            "源 L149「全鬼」；鬼多为不吉为数据层引文，本层不判吉凶"))
        if all(SHENG_CYCLE.get(se) == x for x in (ce, zhe, me)):
            out.append(_tag("san_chuan", "全脱",
                            f"日干{stem}({se})生三传{chu}({ce})、{zhong}({zhe})、{mo}({me})，"
                            f"三传俱受日干之生",
                            "源 L150「全脱」；「受生」义为日干生之三传，本层不判吉凶"))

    # 俱阳／俱阴
    if all(b in _YANG_BRANCHES for b in san):
        out.append(_tag("san_chuan", "俱阳",
                        f"三传{chu}、{zhong}、{mo}皆在阳支（子寅辰午申戌）",
                        "源 L152「俱阳」；事必显著为数据层引文"))
    if all(b in _YIN_BRANCHES for b in san):
        out.append(_tag("san_chuan", "俱阴",
                        f"三传{chu}、{zhong}、{mo}皆在阴支（丑卯巳未酉亥）",
                        "源 L152「俱阴」；事必隐秘为数据层引文"))

    # 递生：初生中、中生末、末生干（顺链） 或 末生中、中生初、初生日干（逆链）
    shun = (_sheng_elem(ce, zhe) and _sheng_elem(zhe, me) and _sheng_elem(me, se))
    ni = (_sheng_elem(me, zhe) and _sheng_elem(zhe, ce) and _sheng_elem(ce, se))
    if shun:
        out.append(_tag("san_chuan", "递生（顺链）",
                        f"初{chu}({ce})生中{zhong}({zhe})、中生末{mo}({me})、末生日干{stem}({se})",
                        "源 L153 顺链；事成转相提携为数据层引文"))
    elif ni:
        out.append(_tag("san_chuan", "递生（逆链）",
                        f"末{mo}({me})生中{zhong}({zhe})、中生初{chu}({ce})、初生日干{stem}({se})",
                        "源 L153 逆链"))

    # 递克：未克中、中克初、初克日干（顺链） 或 初克中、中克末、末克日干（逆链）
    gshun = (_ke_cycle(me, zhe) and _ke_cycle(zhe, ce) and _ke_cycle(ce, se))
    gni = (_ke_cycle(ce, zhe) and _ke_cycle(zhe, me) and _ke_cycle(me, se))
    if gshun:
        out.append(_tag("san_chuan", "递克（顺链）",
                        f"末{mo}({me})克中{zhong}({zhe})、中克初{chu}({ce})、初克日干{stem}({se})",
                        "源 L154 顺链；辗转牵扰为数据层引文"))
    elif gni:
        out.append(_tag("san_chuan", "递克（逆链）",
                        f"初{chu}({ce})克中{zhong}({zhe})、中克末{mo}({me})、末克日干{stem}({se})",
                        "源 L154 逆链"))
    return out


# ══════════════════════════════════════════════ 汇总入口
TAG_GROUPS = (
    ("not_entered", not_entered),
    ("xunkong_grade", xunkong_grade),
    ("sanjian", sanjian),
    ("qian_hou", qian_hou),
    ("ke_zhan", jia_ke_nei_wai),
    ("day_night_route", day_night_route),
    ("san_gong_shi", san_gong_shi),
    ("tianluo_diwang", tianluo_diwang),
    ("gui_sha", gui_sha_four_gate),
    ("fuyin_fanyin_jiuyuan", fuyin_fanyin_jiuyuan),
    ("ri_zao_tian_yi", ri_zao_tian_yi),
    ("san_chuan_seven_ge", san_chuan_seven_ge),
)


def all_tags(chart_out: dict, class_jiang_name: str = "") -> dict[str, list[dict]]:
    """全部结构标签维度 → {维度名: [标签, …]}。class_god 需类将名，故单列在外。"""
    out: dict[str, list[dict]] = {}
    for dim, fn in TAG_GROUPS:
        rows = fn(chart_out) if dim != "gui_sha" else fn(chart_out, class_jiang_name)
        if rows:
            out[dim] = rows
    return out
