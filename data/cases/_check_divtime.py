# -*- coding: utf-8 -*-
"""检查 divination_time 字段结构"""
import sys
sys.path.insert(0, r'C:\Users\Lin\Desktop\skills\liu-yao\scripts')
from liuyao_engine import build_hexagram_result
from run_blind_v4 import hex2yao

h = build_hexagram_result(hex2yao("坤"), "占借银", "manual", 2024, 6, 1, 10,
                          explicit_time={"month_sb": "甲戌", "day_sb": "甲辰"})
dt = h.get("divination_time", {})
print("divination_time keys:", list(dt.keys()))
print(json_dump := __import__("json").dumps(dt, ensure_ascii=False)[:600])
og = h["original_hexagram"]
print("world_position:", og.get("world_position"), "response_position:", og.get("response_position"))
