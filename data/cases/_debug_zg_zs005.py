# -*- coding: utf-8 -*-
"""调试 ZS005 两现用神选择"""
import json, sys
sys.path.insert(0, r'C:\Users\Lin\Desktop\skills\liu-yao\scripts')
from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain
from run_blind_v4 import hex2yao

h = build_hexagram_result(hex2yao("恒", "鼎"), "自占婚", "manual", 2024, 1, 10, 10,
                          explicit_time={"month_sb": "甲子", "day_sb": "癸酉"})
print("卦:", h["original_hexagram"]["name"], "宫:", h["original_hexagram"].get("palace"), "世:", h["original_hexagram"].get("generation"))
print("爻表:")
for y in h["original_hexagram"]["yao_lines"]:
    print("  %d爻 %s%s 六亲=%s 动=%s 世=%s 应=%s 空=%s" % (
        y["position"], y["heavenly_stem"], y["earthly_branch"], y["six_relation"],
        y["is_moving"], y["is_world"], y["is_response"], y["is_empty"]))
tc = run_thinking_chain(h)
s2 = tc.get("step2_use_god_identification", {}) or {}
print("use_god_positions:", json.dumps(s2.get("use_god_positions"), ensure_ascii=False))
print("selected:", json.dumps(s2.get("selected_use_god"), ensure_ascii=False))
print("world:", s2.get("world_position"), "response:", (s2.get("world_position") or 0) and ((s2.get("world_position") - 1 + 3) % 6 + 1))
