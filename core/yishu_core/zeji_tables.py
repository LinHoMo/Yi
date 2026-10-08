# -*- coding: utf-8 -*-
"""择吉补表（Zeji Tables）—— 择吉（通书择日）所需的历法规则表。

依 CONTRACT.md §二：「学科若需要内核没有的表，加到内核并标注只有哪几科用，
不要开第二个真值源。」本模块即择吉科的补表，**唯一消费方：择吉科 `disciplines/zeji`**
（梅花/六爻/八字不用建除、黄黑道、二十八宿）。

收录三条机械规则，全部可用「日支/月支/日期」直接算出，无解读成分：
  1. 建除十二神（建除十二值）：月建之支为「建」，逐日顺行一支值一神。
  2. 黄黑道十二神：青龙正月（寅月）起子，此后每月起支退二位（+2 阳支），
     日神由日支相对青龙起支的偏移定，时辰值神另行轮值。
  3. 二十八宿值日：固定序循环（角…轸），以 2007-09-13＝角 为锚点逐日 +1。

三条规则的数值口径均已与多家在线黄历交叉核对（2026-09-23 平/箕、
2026-09-24 定/勾陈黑道、2026-09-25 执/青龙黄道/牛 等），锚点结论记录在
`docs/CHANGELOG.md`。星宿「吉凶宜忌」属解读层，不进内核，放学科 data 并注明出处。
"""
from __future__ import annotations

from datetime import date

from .ganzhi_calendar import EARTHLY_BRANCHES

# ================================================================ 建除十二神
# 《淮南子·天文训》："太阴所居……正月建寅，则寅为建，卯为除，辰为满，巳为平，
# 主生；午为定，未为执，主陷；申为破，主衡；酉为危，主杓；戌为成，主少德；
# 亥为收，主大德；子为开，主太岁；丑为闭，主太阴。"
JIAN_CHU_ORDER = ["建", "除", "满", "平", "定", "执", "破", "危", "成", "收", "开", "闭"]


def jian_chu_index(month_branch: str, day_branch: str) -> int | None:
    """建除十二神在 JIAN_CHU_ORDER 中的下标；非法支返回 None。"""
    m = EARTHLY_BRANCHES.find(month_branch) if month_branch in EARTHLY_BRANCHES else -1
    d = EARTHLY_BRANCHES.find(day_branch) if day_branch in EARTHLY_BRANCHES else -1
    if m < 0 or d < 0:
        return None
    return (d - m) % 12


def jian_chu_of(month_branch: str, day_branch: str) -> str | None:
    """月建 + 日支 → 建除十二神之一（建/除/满/平/定/执/破/危/成/收/开/闭）。"""
    idx = jian_chu_index(month_branch, day_branch)
    return JIAN_CHU_ORDER[idx] if idx is not None else None


# ================================================================ 黄黑道十二神
# 《协纪辨方书·卷五·黄黑道》：「黄黑道十二神……青龙、明堂、天刑、朱雀、金匮、
# 天德、白虎、玉堂、天牢、玄武、司命、勾陈。」黄道六神为吉：青龙、明堂、金匮、
# 天德、玉堂、司命；黑道六神为凶：天刑、朱雀、白虎、天牢、玄武、勾陈。
# 起例：正月（寅月）青龙起子，二月（卯月）起寅，三月（辰月）起辰……
# 即 青龙起支 = (月支序 − 寅序) × 2 (mod 12)，每逢寅月轮回。
# 日神 = 日支相对青龙起支之偏移；时辰值神 = 时支 + 青龙起支偏移。
# （2026-09-24 酉月丑日 → 勾陈/黑道、2026-09-25 酉月寅日 → 青龙/黄道，与通书一致。）
HUANG_HEI_DAO_ORDER = [
    "青龙", "明堂", "天刑", "朱雀", "金匮", "天德",
    "白虎", "玉堂", "天牢", "玄武", "司命", "勾陈",
]
HUANG_DAO_GODS = {"青龙", "明堂", "金匮", "天德", "玉堂", "司命"}


def qinglong_start_index(month_branch: str) -> int | None:
    """某月支下「青龙」所起之地支序（0=子）；非法支返回 None。"""
    m = EARTHLY_BRANCHES.find(month_branch) if month_branch in EARTHLY_BRANCHES else -1
    if m < 0:
        return None
    return (m - 2) * 2 % 12


def day_god_index(month_branch: str, day_branch: str) -> int | None:
    """日值黄黑道神下标（0=青龙 … 11=勾陈）；非法支返回 None。"""
    start = qinglong_start_index(month_branch)
    d = EARTHLY_BRANCHES.find(day_branch) if day_branch in EARTHLY_BRANCHES else -1
    if start is None or d < 0:
        return None
    return (d - start) % 12


def day_god_of(month_branch: str, day_branch: str) -> str | None:
    """月建 + 日支 → 日值黄黑道神名。"""
    idx = day_god_index(month_branch, day_branch)
    return HUANG_HEI_DAO_ORDER[idx] if idx is not None else None


def is_huang_dao(god: str) -> bool:
    """该神是否属黄道（吉）；未知神名返回 False。"""
    return god in HUANG_DAO_GODS


def hour_god_index(month_branch: str, hour_branch: str) -> int | None:
    """时辰值神下标；非法支返回 None。"""
    start = qinglong_start_index(month_branch)
    h = EARTHLY_BRANCHES.find(hour_branch) if hour_branch in EARTHLY_BRANCHES else -1
    if start is None or h < 0:
        return None
    return (h + start) % 12


def hour_god_of(month_branch: str, hour_branch: str) -> str | None:
    """月建 + 时支 → 时辰值神名。"""
    idx = hour_god_index(month_branch, hour_branch)
    return HUANG_HEI_DAO_ORDER[idx] if idx is not None else None


# ================================================================ 二十八宿
# 固定序：《史记·天官书》以来通行序，由角宿起：
# 角、亢、氐、房、心、尾、箕、斗、牛、女、虚、危、室、壁、
# 奎、娄、胃、昴、毕、觜、参、井、鬼、柳、星、张、翼、轸。
# 值日按 28 天循环逐日 +1。锚点：2007-09-13 = 角宿（角亢氐房心尾箕斗牛女虚危室壁
# 奎娄胃昴毕觜参井鬼柳星张翼轸 中第 1 宿），由此推出 2026-09-23 = 箕、2026-09-25 = 牛，
# 与多家黄历一致。日禽名（角木蛟…）是二十八宿的固定配属，供展示用。
XIU_ORDER = [
    "角", "亢", "氐", "房", "心", "尾", "箕",
    "斗", "牛", "女", "虚", "危", "室", "壁",
    "奎", "娄", "胃", "昴", "毕", "觜", "参",
    "井", "鬼", "柳", "星", "张", "翼", "轸",
]
XIU_ANIMALS = [
    "蛟", "龙", "貉", "兔", "狐", "虎", "豹",
    "獬", "牛", "蝠", "鼠", "燕", "猪", "貐",
    "狼", "狗", "雉", "鸡", "乌", "猴", "猿",
    "犴", "羊", "獐", "马", "鹿", "蛇", "蚓",
]
XIU_ELEMENTS = [
    "木", "金", "土", "日", "月", "火", "水",
    "木", "金", "土", "日", "月", "火", "水",
    "木", "金", "土", "日", "月", "火", "水",
    "木", "金", "土", "日", "月", "火", "水",
]
_XIU_ANCHOR = date(2007, 9, 13)  # = 角宿


def xiuxiu_index(d: date) -> int:
    """公历日期 → 二十八宿下标（0=角 … 27=轸）。"""
    return (d - _XIU_ANCHOR).days % 28


def xiuxiu_of(d: date) -> dict:
    """公历日期 → {index, name, animal, element, full}（full 形如"角木蛟"）。"""
    idx = xiuxiu_index(d)
    return {
        "index": idx,
        "name": XIU_ORDER[idx],
        "animal": XIU_ANIMALS[idx],
        "element": XIU_ELEMENTS[idx],
        "full": XIU_ORDER[idx] + XIU_ELEMENTS[idx] + XIU_ANIMALS[idx],
    }


# ================================================================ 鸣吠 / 鸣吠对
# 《协纪辨方书》卷十一「鸣吠」「鸣吠对」：安葬、启攒专用的吉日。
# 起例（卷十一义例，源 L110，逐字原列）：
#
#   鸣吠（共 13 日）：甲丙庚壬四日配午申 + 乙丁己辛癸五日配酉
#     甲午 甲申 · 丙午 丙申 · 庚午 庚申 · 壬午 壬申 · 乙酉 丁酉 己酉 辛酉 癸酉
#
#   鸣吠对（共 11 日）：丙庚壬配子 + 甲丙庚壬配寅 + 乙丁辛癸配卯
#     丙子 庚子 壬子 · 甲寅 丙寅 庚寅 壬寅 · 乙卯 丁卯 辛卯 癸卯
#
# 两条互不重叠，共 24 日。
# 卷十一另条（源 L468/L470）所列「通书」用甲午/丙寅……装表 ≠ 义例起例，
# 清·张鉴注已指其为「俗本沿误」（通书本之吴氏，吴氏沿廖氏之旧）；
# 本书 project 以卷十一义例（起例条目本身）为唯一真值源，不同化。
MINGFEI_DAYS: tuple[str, ...] = (
    "甲午", "甲申", "丙午", "丙申", "庚午", "庚申", "壬午", "壬申",
    "乙酉", "丁酉", "己酉", "辛酉", "癸酉",
)  # 共 13 日 —— 源 L110 起例

MINGFEI_DUI_DAYS: tuple[str, ...] = (
    "丙子", "庚子", "壬子",
    "甲寅", "丙寅", "庚寅", "壬寅",
    "乙卯", "丁卯", "辛卯", "癸卯",
)  # 共 11 日 —— 源 L110 起例


def ming_fei_of(stem_branch: str) -> str | None:
    """六十甲子 → '鸣吠' / '鸣吠对' / None。纯集合查表，无推演。"""
    if stem_branch in MINGFEI_DAYS:
        return "鸣吠"
    if stem_branch in MINGFEI_DUI_DAYS:
        return "鸣吠对"
    return None


def is_mingfei_day(day_ganzhi: str) -> bool:
    """该日是否为鸣吠日（安葬吉）。"""
    return day_ganzhi in MINGFEI_DAYS


def is_mingfei_dui_day(day_ganzhi: str) -> dict:
    """该日是否为鸣吠对日（启攒吉）。返回 {'is_dui': bool, 'note': str}。"""
    return {"is_dui": day_ganzhi in MINGFEI_DUI_DAYS, "note": ""}


def ming_fei_table_60() -> list[dict]:
    """六十甲子逐日 → 鸣吠/鸣吠对，供学科 render 层用。"""
    from .ganzhi_calendar import EARTHLY_BRANCHES, HEAVENLY_STEMS

    out: list[dict] = []
    for i in range(60):
        stem = HEAVENLY_STEMS[i % 10]
        branch = EARTHLY_BRANCHES[i % 12]
        gz = stem + branch
        out.append({"index": i + 1, "ganzhi": gz, "ming_fei": ming_fei_of(gz)})
    return out


def assert_mingfei_vs_source() -> None:
    """机械自检：与源 L110 起例字面逐日对拍。"""
    assert len(MINGFEI_DAYS) == 13 and len(set(MINGFEI_DAYS)) == 13
    assert len(MINGFEI_DUI_DAYS) == 11 and len(set(MINGFEI_DUI_DAYS)) == 11
    # 两条互不重叠
    assert not (set(MINGFEI_DAYS) & set(MINGFEI_DUI_DAYS)), "鸣吠/鸣吠对不应重叠"
    # 二十四日总数
    assert len(set(MINGFEI_DAYS) | set(MINGFEI_DUI_DAYS)) == 24
    # 六十甲子全覆盖验证
    covered = sorted(set(MINGFEI_DAYS) | set(MINGFEI_DUI_DAYS))
    assert len(covered) == 24
    # 起例硬核对：甲丙庚壬＝四位阳干（源 L110 明列四天，午申两支）
    yang_stems = {"甲", "丙", "庚", "壬"}
    for gz in MINGFEI_DAYS:
        s = gz[0]
        b = gz[1]
        if s in yang_stems:
            assert b in {"午", "申"}, f"阳干鸣吠只取午申：{gz}"
        else:
            assert b == "酉", f"阴干鸣吠只取酉：{gz}"
    # 鸣吠对：丙庚壬=子、甲丙庚壬=寅、乙丁辛癸=卯
    for gz in MINGFEI_DUI_DAYS:
        s = gz[0]
        b = gz[1]
        if b == "子":
            assert s in {"丙", "庚", "壬"}, f"子日鸣吠对限丙庚壬：{gz}"
        elif b == "寅":
            assert s in yang_stems, f"寅日鸣吠对限甲丙庚壬：{gz}"
        elif b == "卯":
            assert s in {"乙", "丁", "辛", "癸"}, f"卯日鸣吠对限乙丁辛癸：{gz}"
    # 60 甲子里鸣吠/鸣吠对不会出现同一日兼具两者（已由互不重叠保证）。
    assert ming_fei_of("甲午") == "鸣吠"
    assert ming_fei_of("庚寅") == "鸣吠对"
    assert ming_fei_of("壬寅") == "鸣吠对"
    assert ming_fei_of("戊午") is None
    assert ming_fei_of("戊寅") is None


# ================================================================ 月内凶神（天罡/河魁/九空）
# 天罡河魁（源 L490 厯例）：阳建之月前三辰为天罡、后三辰为河魁；阴建之月反是。
# 阳建＝子寅辰午申戌六位（地支序偶数位），阴建＝丑卯巳未酉亥。
# 返回 (天罡支, 河魁支)；非法支返回 None。
#
# 九空（源 L530 厯例）：「正月在辰，逆行四季」 → 寅=辰、卯=丑、辰=戌、巳=未,
# …十二支循环。四季=辰戌丑未，"逆行"所以对寅=辰起、每一步往回退一支。
# 返回九空地支；非法支返回 None。
JIU_KONG_ORDER = ["辰", "丑", "戌", "未"]  # (month_idx - 2) % 4 依序取值


def tian_gang_branch(month_branch: str) -> tuple[str, str] | None:
    """月建 → (天罡支, 河魁支)，依源 L490 厯例；非法支返回 None。"""
    from .ganzhi_calendar import EARTHLY_BRANCHES

    m = EARTHLY_BRANCHES.find(month_branch) if month_branch in EARTHLY_BRANCHES else -1
    if m < 0:
        return None
    # 阳建（地支序偶数位）: 天罡=前三辰(m-3), 河魁=后三辰(m+3)
    # 阴建（奇数位）: 反是 —— 天罡=后三辰(m+3), 河魁=前三辰(m-3)
    if m % 2 == 0:
        return (EARTHLY_BRANCHES[(m - 3) % 12], EARTHLY_BRANCHES[(m + 3) % 12])
    return (EARTHLY_BRANCHES[(m + 3) % 12], EARTHLY_BRANCHES[(m - 3) % 12])


def jiu_kong_branch(month_branch: str) -> str | None:
    """月建 → 九空地支（源 L530 "正月在辰逆行四季"）；非法支返回 None。"""
    from .ganzhi_calendar import EARTHLY_BRANCHES

    m = EARTHLY_BRANCHES.find(month_branch) if month_branch in EARTHLY_BRANCHES else -1
    if m < 0:
        return None
    return JIU_KONG_ORDER[(m - 2) % 4]


# ================================================================ 人神（逐建/逐辰）
# 源 L696 逐建人神（建/除/满/平/定/执/破/危/成/收/开/闭 配 身体部位）
# 源 L698 十二辰人神（子～亥 配 身体部位）
# 纯机械零吉凶：只存定位，曹震圭「忌鍼灸」是断语——不入 core 表。
REN_SHEN_BY_JIAN_CHU: dict[str, str] = {
    "建": "足", "除": "尻", "满": "腹", "平": "背",
    "定": "心", "执": "手", "破": "口", "危": "鼻",
    "成": "肩", "收": "头", "开": "耳", "闭": "目",
}
REN_SHEN_BY_DAY_BRANCH: dict[str, str] = {
    "子": "目", "丑": "耳", "寅": "胷", "卯": "鼻",
    "辰": "腰", "巳": "手", "午": "心", "未": "足",
    "申": "肩", "酉": "头", "戌": "颈", "亥": "项",
}


def ren_shen_of(jian_chu: str, day_branch: str) -> dict:
    """人神定位输出。纯机械，不断言。返回 by_jian_chu / by_day_branch / 出处。

    jian_chu 可传 ""（无建除时 by_jian_chu = None），day_branch 必填。
    """
    if jian_chu and jian_chu not in REN_SHEN_BY_JIAN_CHU:
        jian_chu = ""
    by_jc = REN_SHEN_BY_JIAN_CHU.get(jian_chu) if jian_chu else None
    return {
        "by_jian_chu": by_jc,
        "by_day_branch": REN_SHEN_BY_DAY_BRANCH.get(day_branch),
        "出处": "《协纪辨方书》源L696（逐建人神）/ 源L698（十二辰人神）",
    }
