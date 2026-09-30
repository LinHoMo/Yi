# -*- coding: utf-8 -*-
"""大六壬·课目识别（第一批九条，全部机械判据）。

判据源：data/kemu.json（六壬大全 卷一「课目」诀表逐字引文）。
识别只报**结构命中**，不报吉凶——诀文中的旺衰/吉将/神煞附加条件未落地者，
在 hit 的 `partial` 字段显式声明，不得当作完整判据输出（AGENTS.md 铁律一/三）。

第一批（机械可检）：
  轩盖（三传午卯子）/ 斲轮（太冲卯加申发用）/
  引从（初末引从干支寄宫）/ 亨通（三传递生日干）/ 三交（三传皆四仲）/
  乱首（支加干克干）/ 赎胥（支临干被克 或 干加支上克支）/ 冲破（初传冲日干寄宫或日支）
"""
from __future__ import annotations

from yishu_core.ganzhi_calendar import EARTHLY_BRANCHES as _BR
from yishu_core.liuren_tables import JI_GONG
from yishu_core.symbols import (
    CHONG_PAIRS,
    BRANCH_ELEMENTS,
    KE_CYCLE,
    SELF_PUNISHMENTS,
    SHENG_CYCLE,
    STEM_ELEMENTS,
    THREE_PUNISHMENTS_CYCLIC,
    THREE_PUNISHMENTS_MUTUAL,
)

CHONG_OF: dict[str, str] = {}
for _a, _b in CHONG_PAIRS:
    CHONG_OF[_a] = _b
    CHONG_OF[_b] = _a

_XING: dict[str, set[str]] = {}
for _cyc in THREE_PUNISHMENTS_CYCLIC.values():
    for _i, _b in enumerate(_cyc):
        _XING.setdefault(_b, set()).add(_cyc[(_i + 1) % 3])
for _a, _b in THREE_PUNISHMENTS_MUTUAL.values():
    _XING.setdefault(_a, set()).add(_b)
    _XING.setdefault(_b, set()).add(_a)
for _s in SELF_PUNISHMENTS:
    _XING.setdefault(_s, set()).add(_s)


def _elem(x: str) -> str:
    return BRANCH_ELEMENTS.get(x) or STEM_ELEMENTS.get(x) or ""


def _ke(a: str, b: str) -> bool:
    """a 克 b。"""
    ea, eb = _elem(a), _elem(b)
    return bool(ea and eb) and KE_CYCLE[ea] == eb


def _sheng(a: str, b: str) -> bool:
    """a 生 b。"""
    ea, eb = _elem(a), _elem(b)
    return bool(ea and eb) and SHENG_CYCLE[ea] == eb


def _neighbors(target: str, a: str, b: str) -> bool:
    """a、b 恰为 target 在支环上的前后两位（引从）。"""
    i = _BR.index(target)
    prev, nxt = _BR[(i - 1) % 12], _BR[(i + 1) % 12]
    return {a, b} == {prev, nxt}


def recognize(chart_out: dict) -> list[dict]:
    """chart 段输出 → 命中课目列表 [{name, basis, partial}]。"""
    san = chart_out.get("san_chuan") or []
    if len(san) != 3:
        return []
    chu, zhong, mo = san
    day_gz = chart_out["moment"]["day_ganzhi"]
    day_stem, day_branch = day_gz[0], day_gz[1]
    jigong = JI_GONG[day_stem]
    tianpan = chart_out.get("tianpan") or {}
    hits: list[dict] = []

    def hit(name: str, basis: str, partial: str = "") -> None:
        hits.append({"name": name, "basis": basis, "partial": partial})

    # 轩盖：三传午卯子（诀注「正七两月」为应期加强条件）
    if san == ["午", "卯", "子"]:
        hit("轩盖", "三传午卯子", "诀又须正/七两月，月支条件未并入判据")
    # 斲轮：太冲（卯）加申发用（「庚斧乙庚」遁干条件未并入）
    if chu == "卯" and tianpan.get("申") == "卯":
        hit("斲轮", "太冲卯加申发用", "诀又须遁干庚/乙庚，未并入判据")
    # 引从：初末二传引从日干寄宫或日支
    for target, label in ((jigong, "日干寄宫"), (day_branch, "日支")):
        if _neighbors(target, chu, mo):
            hit("引从", f"初传末传引从{label}（{chu}…{mo}）")
            break
    # 亨通：三传递生日干（初生中、中生末、末生日干；「地生」一式未实现）
    if _sheng(chu, zhong) and _sheng(zhong, mo) and _sheng(mo, day_stem):
        hit("亨通", "三传递生日干（天生一式）", "「地生」一式未实现")
    # 三交：三传皆四仲（「阴合逢」条件未并入）
    if all(b in ("子", "午", "卯", "酉") for b in san):
        hit("三交", "三传皆四仲", "诀又须阴不备/合逢，未并入判据")
    # 乱首：支加干克干
    if tianpan.get(jigong) == day_branch and _ke(day_branch, day_stem):
        hit("乱首", "支加干上而克干")
    # 赎胥：支临干被干克，或干加支上克支
    if tianpan.get(jigong) == day_branch and _ke(day_stem, day_branch):
        hit("赎胥", "支临干上而被干克")
    elif tianpan.get(day_branch) == jigong and _ke(jigong, day_branch):
        hit("赎胥", "干加支上而克支")
    # 冲破：初传冲日干寄宫或日支（「更兼岁月破神」未并入）
    if chu in (CHONG_OF.get(jigong), CHONG_OF.get(day_branch)):
        hit("冲破", f"初传{chu}冲日辰", "诀又须岁月破神并，未并入判据")
    return hits
