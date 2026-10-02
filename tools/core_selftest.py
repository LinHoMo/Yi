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
    NAYIN,
    NAYIN_TO_ELEMENT,
    sanhe_group,
    xunkong_of,
    sanxing_hits,
    twelve_growth,
    twelve_growth_index,
    yao_values,
)
from yishu_core.ming_tables import (  # noqa: E402
    dayun_direction,
    DAYS_PER_LUCK_YEAR,
)
from yishu_core.shensha import shensha_at_branches, shensha_of_chart  # noqa: E402
from yishu_core.relations import ten_god, six_relation  # noqa: E402
from yishu_core.najia import najia_branch, response_position  # noqa: E402
from yishu_core.hexagram_texts import HEXAGRAMS  # noqa: E402
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

    # 神煞（命科 shensha_of_chart）
    ss_chart = shensha_of_chart("甲", "子", "寅", "辰", "申")
    if not isinstance(ss_chart, list):
        fails.append(f"shensha_of_chart 应返回 list，得 {type(ss_chart)}")
    elif not ss_chart:
        fails.append("shensha_of_chart(甲/子/寅/辰/申) 应至少安出天乙/文昌等")
    else:
        s0 = ss_chart[0]
        if not isinstance(s0, dict) or "name" not in s0:
            fails.append(f"shensha_of_chart 条目应为含 name 的 dict，得 {s0!r}")

    # 神煞（卜科 shensha_at_branches）
    ss_ly = shensha_at_branches("甲", "寅", year_branch="子")
    if not isinstance(ss_ly, list):
        fails.append(f"shensha_at_branches 应返回 list，得 {type(ss_ly)}")
    elif not ss_ly:
        fails.append("shensha_at_branches(甲/寅) 应至少安出一项神煞")

    # 纳甲
    nb = najia_branch("乾", 1)
    if nb != "子":
        fails.append(f"乾卦初九纳子，得 {nb}")
    nb6 = najia_branch("坤", 6)
    if nb6 != "酉":
        fails.append(f"坤卦六三纳酉，得 {nb6}")
    if najia_branch("ZZZ_not_exist", 1) is not None:
        fails.append("未知卦纳甲应返回 None")

    # 世应定位（世在X爻则应隔两位：1→4, 2→5, 3→6, 4→1, 5→2, 6→3）
    if response_position(1) != 4:
        fails.append(f"世在初爻应在四，得 {response_position(1)}")
    if response_position(3) != 6:
        fails.append(f"世在三爻应在六，得 {response_position(3)}")
    if response_position(4) != 1:
        fails.append(f"世在四爻应在初，得 {response_position(4)}")
    if response_position(6) != 3:
        fails.append(f"世在上爻应在三，得 {response_position(6)}")

    # 六十四卦表完整
    if len(HEXAGRAMS) != 64:
        fails.append(f"HEXAGRAMS 应为 64 卦，实际 {len(HEXAGRAMS)}")

    return fails


if __name__ == "__main__":
    fails = check_core_apis()
    if fails:
        print("内核 API 自测失败：")
        for f in fails:
            print("  ·", f)
        raise SystemExit(1)
    print("内核 API 自测通过（旬空/三刑/十二长生/纳音/十神/节气/大运方向/神煞/纳甲/世应/六十四卦表）")
