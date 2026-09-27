# -*- coding: utf-8 -*-
"""内核机械 API 自测：旬空/三刑/十二长生/十神/节气方向/纳音。

挂在 tools/check.py 质量门；只验机械正确性，不涉及任何预测率。
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from yishu_core.symbols import (  # noqa: E402
    xunkong_of,
    sanxing_hits,
    twelve_growth,
    twelve_growth_index,
    yao_values,
)
from yishu_core.ming_tables import (  # noqa: E402
    NAYIN,
    NAYIN_TO_ELEMENT,
    dayun_direction,
    DAYS_PER_LUCK_YEAR,
)
from yishu_core.relations import ten_god, six_relation  # noqa: E402
from yishu_core.ganzhi_calendar import next_jie_after, prev_jie_before  # noqa: E402


def check_core_apis() -> list[str]:
    fails: list[str] = []

    # 旬空
    if xunkong_of("甲子") != ["戌", "亥"]:
        fails.append(f"xunkong 甲子 应为 戌亥，得 {xunkong_of('甲子')}")
    if xunkong_of("乙丑") != ["戌", "亥"]:
        fails.append(f"xunkong 乙丑 同旬应为 戌亥，得 {xunkong_of('乙丑')}")
    if xunkong_of("甲戌") != ["申", "酉"]:
        fails.append(f"xunkong 甲戌 应为 申酉，得 {xunkong_of('甲戌')}")
    if xunkong_of("") != []:
        fails.append("xunkong 非法输入应返回 []")

    # 三刑
    if "无礼之刑" not in sanxing_hits(["子", "卯", "午"]):
        fails.append("sanxing 子卯 应报 无礼之刑")
    if "无恩之刑" not in sanxing_hits(["寅", "巳", "申"]):
        fails.append("sanxing 寅巳申 应报 无恩之刑")
    if sanxing_hits(["子", "午", "辰"]):
        fails.append("sanxing 子午辰 不应报刑")

    # 十二长生
    if twelve_growth("木", "亥") != "长生":
        fails.append(f"木长生在亥，得 {twelve_growth('木', '亥')}")
    if twelve_growth("火", "午") != "帝旺":
        fails.append(f"火帝旺在午，得 {twelve_growth('火', '午')}")
    if twelve_growth_index("水", "辰") != 8:  # 墓
        fails.append(f"水墓在辰 序号 8，得 {twelve_growth_index('水', '辰')}")
    if twelve_growth("土", "寅") != "长生":
        fails.append("火土同宫：土长生应在寅")

    # 纳音唯一写法
    if NAYIN.get("甲午") != "沙中金":
        fails.append(f"甲午纳音应为 沙中金，得 {NAYIN.get('甲午')}")
    if NAYIN_TO_ELEMENT.get("沙中金") != "金":
        fails.append("沙中金五行应为 金")

    # 十神
    if ten_god("甲", "甲") != "比肩":
        fails.append(f"甲见甲应为 比肩，得 {ten_god('甲', '甲')}")
    if ten_god("甲", "乙") != "劫财":
        fails.append(f"甲见乙应为 劫财，得 {ten_god('甲', '乙')}")
    if ten_god("甲", "辛") != "正官":
        fails.append(f"甲见辛应为 正官，得 {ten_god('甲', '辛')}")
    if six_relation("木", "水") != "父母":
        fails.append(f"木见水应为 父母，得 {six_relation('木', '水')}")

    # 大运方向
    if dayun_direction("甲", "男") != "forward":
        fails.append("阳年男应顺行")
    if dayun_direction("甲", "女") != "backward":
        fails.append("阳年女应逆行")
    if dayun_direction("乙", "男") != "backward":
        fails.append("阴年男应逆行")

    # 节气：顺行取后一节、逆行取前一节
    bdt = datetime(1984, 2, 10, 10, 0)
    nxt = next_jie_after(bdt)
    prv = prev_jie_before(bdt)
    if not nxt.get("instant") or nxt["instant"] <= bdt:
        fails.append("next_jie_after 应晚于给定时刻")
    if not prv.get("instant") or prv["instant"] >= bdt:
        fails.append("prev_jie_before 应早于给定时刻")

    # yao_values：八纯卦应返回 6 爻（六十四卦优先）
    yq = yao_values("乾")
    if len(yq) != 6:
        fails.append(f"yao_values(乾) 应 6 爻（六十四卦），得 {yq}")
    yq2 = yao_values("姤", moving=(1,))
    if yq2[0] not in (9, 6):
        fails.append(f"yao_values(姤, moving=1) 初爻应为动爻 9/6，得 {yq2}")

    if DAYS_PER_LUCK_YEAR != 3:
        fails.append("DAYS_PER_LUCK_YEAR 应为 3（三日=一年）")
    return fails


if __name__ == "__main__":
    fails = check_core_apis()
    if fails:
        print("内核 API 自测失败：")
        for f in fails:
            print("  ·", f)
        raise SystemExit(1)
    print("内核 API 自测通过（旬空/三刑/十二长生/纳音/十神/节气/大运方向）")
