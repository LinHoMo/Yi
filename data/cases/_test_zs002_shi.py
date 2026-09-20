# -*- coding: utf-8 -*-
"""实测师卦还原 ZS002"""
import sys
sys.path.insert(0, r'C:\Users\Lin\Desktop\skills\liu-yao\scripts')
from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain
from run_blind_v4 import hex2yao

h = build_hexagram_result(hex2yao("师"), "岳父近病吉凶", "manual", 2024, 6, 1, 10,
                          explicit_time={"month_sb": "甲未", "day_sb": "庚辰"})
tc = run_thinking_chain(h)
s2 = tc.get("step2_use_god_identification", {}) or {}
s5 = tc.get("step5_synthesis", {}) or {}
sel = s2.get("selected_use_god") or {}
print("用神:", s2.get("use_god_category"), "@", sel.get("earthly_branch"), sel.get("position"), "爻")
print("终分:", s5.get("final_score"), "断:", s5.get("verdict"))
for ln in s5.get("reasoning_chain", []):
    if "[格局]" in ln or "[综合]" in ln:
        print(ln[:200])
