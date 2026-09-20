# -*- coding: utf-8 -*-
"""ZS016 step5 各调整项"""
import sys, json
sys.path.insert(0, r'C:\Users\Lin\Desktop\skills\liu-yao\scripts')
from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain
from run_blind_v4 import hex2yao

h = build_hexagram_result(hex2yao("升"), "酉月丙辰日占子病得升卦", "manual", 2024, 6, 1, 10,
                          explicit_time={"month_sb": "甲酉", "day_sb": "丙辰"})
tc = run_thinking_chain(h)
s5 = tc.get("step5_synthesis", {}) or {}
keys = [k for k in s5.keys()]
print("step5 keys:", keys)
for k in keys:
    v = s5.get(k)
    if isinstance(v, (int, float)) and v != 0:
        print(f"  {k} = {v}")
    elif isinstance(v, str) and v:
        print(f"  {k} = {v[:150]}")
