# -*- coding: utf-8 -*-
"""星历考源补表（Xingli Tables）—— 取自《星历考源》《堪舆经》的择吉机械日表。

依 CONTRACT.md §二，本模块为择吉/八字/多学科复用层。唯一消费方规划：
  · 择吉科 `disciplines/zeji/scripts/analyze.py`（大防/小防作 **veto 层**接入）；
  · 八字科 `disciplines/ming` 可供日后复用（目前未强制）。
唯一真值源：干支历走 `yishu_core.ganzhi_calendar`；神煞/建除/鸣吠走 `yishu_core.zeji_tables`；
干支序列/字符类一律 import，不复制（AGENTS.md §二「唯一真值源」）。
"""
from __future__ import annotations

# ================================================================ 阴阳大防
# 《星历考源》源L708-709（堪舆经起例）：正月甲戌 二月乙酉 五月丙午 六月丁巳
#   七月庚辰 八月辛卯 十一月壬子 十二月癸亥。
# 所领日从大防日起逆数至他月大小防止（源L718）。"士" 为 殆知阁 OCR 对 "壬" 的误识，
#   正月领日"士申"壬申（六十甲子表中壬申位序 9，源 L709）。
# 口径：大防 = 「阳防于阴」（L727），属地门内阴阳正防之辰，**望后用之**（L718）。
#   只报「某月该日表」的位置列表，不含吉凶断语；解读层在 verdicts.json。
# 未列月支（辰/巳/戌/亥 = 三四九十月）= 该月无大防，函返 []。

DAFANG: dict[str, list[str]] = {
    # 正月(寅) 甲戌，领 11 日（L710）
    "寅": ["甲戌", "癸酉", "壬申", "辛未", "庚午", "己巳", "戊辰", "丁卯", "丙寅", "乙丑", "甲子", "癸亥"],
    # 二月(卯) 乙酉，领 5 日（L711）
    "卯": ["乙酉", "甲申", "癸未", "壬午", "辛巳", "庚辰"],
    # 三月(辰) 无大防（L727：辰中乙不能配阴建之申）
    "辰": [],
    # 四月(巳) 无大防（L727：巳中丙不能配阴建之未）
    "巳": [],
    # 五月(午) 丙午，领 15 日（L712）
    "午": ["丙午", "乙巳", "甲辰", "癸卯", "壬寅", "辛丑", "庚子", "己亥", "戊戌", "丁酉", "丙申", "乙未", "甲午", "癸巳", "壬辰", "辛卯"],
    # 六月(未) 丁巳，领 5 日（L713）
    "未": ["丁巳", "丙辰", "乙卯", "甲寅", "癸丑", "壬子"],
    # 七月(申) 庚辰，领 6 日（L710 末段）
    "申": ["庚辰", "己卯", "戊寅", "丁丑", "丙子", "乙亥", "甲戌"],
    # 八月(酉) 辛卯，领 6 日（L711 末段）
    "酉": ["辛卯", "庚寅", "己丑", "戊子", "丁亥", "丙戌", "乙酉"],
    # 九月(戌) 无大防（同 L727 理）
    "戌": [],
    # 十月(亥) 无大防（同 L727 理）
    "亥": [],
    # 十一月(子) 壬子，领 6 日（L712 末段）
    "子": ["壬子", "辛亥", "庚戌", "己酉", "戊申", "丁未", "丙午"],
    # 十二月(丑) 癸亥，领 7 日（L713 末段）
    "丑": ["癸亥", "壬戌", "辛酉", "庚申", "己未", "戊午", "丁巳"],
}


def dafang_days(month_branch: str) -> list[str]:
    """月支 → 大防日表（含大防当日 + 所领日，源L710-718）。无大防月支返回 []。"""
    return list(DAFANG.get(month_branch, []))


# ================================================================ 阴阳小防
# 《星历考源》源L719-726（堪舆经起例）：二月己酉 三月戊辰 四月己巳 五月戊午
#   八月己卯 九月戊戌 十月己亥 十一月戊子。
# 口径：小防 = 「阴防于阳」（L727），**望前用之**（L726）。
#   大防已领或小防他月已领者，该月不设（L727）。
# 未列月支（寅/未/申/丑 = 正七十十二月）= 该月无小防，函返 []。

XIAOFANG: dict[str, list[str]] = {
    # 正月(寅) 无小防（L727：正月无领日可独立）
    "寅": [],
    # 二月(卯) 己酉，领 3 日（L722）
    "卯": ["己酉", "戊申", "丁未", "丙午"],
    # 三月(辰) 戊辰，领 5 日（L722）
    "辰": ["戊辰", "丁卯", "丙寅", "乙丑", "甲子", "癸亥"],
    # 四月(巳) 己巳，领 1 日（L722）
    "巳": ["己巳", "戊辰"],
    # 五月(午) 戊午，领 1 日（L722）
    "午": ["戊午", "丁巳"],
    # 六月(未) 无小防（L727：六月大防已有之）
    "未": [],
    # 七月(申) 无小防（L727：七月大防已有之）
    "申": [],
    # 八月(酉) 己卯，领 5 日（L724）
    "酉": ["己卯", "戊寅", "丁丑", "丙子", "乙亥", "甲戌"],
    # 九月(戌) 戊戌，领 7 日（L724）
    "戌": ["戊戌", "丁酉", "丙申", "乙未", "甲午", "癸巳", "壬辰", "辛卯"],
    # 十月(亥) 己亥，领 1 日（L725）
    "亥": ["己亥", "戊戌"],
    # 十一月(子) 戊子，领 3 日（L726）
    "子": ["戊子", "丁亥", "丙戌", "乙酉"],
    # 十二月(丑) 无小防（L727：十二月大防已有之）
    "丑": [],
}


def xiaofang_days(month_branch: str) -> list[str]:
    """月支 → 小防日表（含小防当日 + 所领日，源L720-726）。无小防月支返回 []。"""
    return list(XIAOFANG.get(month_branch, []))


def assert_dafang_xiaofang_vs_source() -> None:
    """大防 8 有 / 小防 8 有 与《星历考源》源L710-726 逐月对拍；防日与领日无交叉、六十甲子内无重复。"""
    # ---- 大防 ----
    expect_dafang_gang = {
        "寅": "甲戌", "卯": "乙酉", "午": "丙午", "未": "丁巳",
        "申": "庚辰", "酉": "辛卯", "子": "壬子", "丑": "癸亥",
    }
    # 有且仅有 8 月支有大防
    dafang_nonempty = {m for m, days in DAFANG.items() if days}
    if dafang_nonempty != set(expect_dafang_gang):
        raise AssertionError(f"大防支应为 {set(expect_dafang_gang)}，实得 {dafang_nonempty}")
    # 每月首支 == 当日大防
    for m, gang in expect_dafang_gang.items():
        if DAFANG[m][0] != gang:
            raise AssertionError(f"大防{m}首支 {DAFANG[m][0]} 不等于防日 {gang}（源L708-713）")
    # 大防领日数量与源对拍（逆数本支到前一防日）
    expect_dafang_len = {"寅": 12, "卯": 6, "午": 16, "未": 6, "申": 7, "酉": 7, "子": 7, "丑": 7}
    for m, ln in expect_dafang_len.items():
        if len(DAFANG[m]) != ln:
            raise AssertionError(f"大防{m}领日数 {len(DAFANG[m])} 应为 {ln}（源L710-713）")
    # 大防 12 月支全覆盖
    if set(DAFANG) != {"寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"}:
        raise AssertionError("大防须覆盖 12 月支")
    # 每月内无重复（跨月边界重复属正常：每防逆数至上月大防止，见源L718）
    for m, days in DAFANG.items():
        if len(days) != len(set(days)):
            raise AssertionError(f"大防{m}月内领日不应重复：{days}")

    # ---- 小防 ----
    expect_xiaofang_gang = {
        "卯": "己酉", "辰": "戊辰", "巳": "己巳", "午": "戊午",
        "酉": "己卯", "戌": "戊戌", "亥": "己亥", "子": "戊子",
    }
    xiaofang_nonempty = {m for m, days in XIAOFANG.items() if days}
    if xiaofang_nonempty != set(expect_xiaofang_gang):
        raise AssertionError(f"小防支应为 {set(expect_xiaofang_gang)}，实得 {xiaofang_nonempty}")
    for m, gang in expect_xiaofang_gang.items():
        if XIAOFANG[m][0] != gang:
            raise AssertionError(f"小防{m}首支 {XIAOFANG[m][0]} 不等于防日 {gang}（源L719）")
    # 小防领日数量与源L722-726对拍
    expect_xiaofang_len = {"卯": 4, "辰": 6, "巳": 2, "午": 2, "酉": 6, "戌": 8, "亥": 2, "子": 4}
    for m, ln in expect_xiaofang_len.items():
        if len(XIAOFANG[m]) != ln:
            raise AssertionError(f"小防{m}领日数 {len(XIAOFANG[m])} 应为 {ln}（源L722-726）")
    if set(XIAOFANG) != {"寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"}:
        raise AssertionError("小防须覆盖 12 月支")
    # 每月内无重复（跨月边界同上）
    for m, days in XIAOFANG.items():
        if len(days) != len(set(days)):
            raise AssertionError(f"小防{m}月内领日不应重复：{days}")
