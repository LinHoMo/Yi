# -*- coding: utf-8 -*-
"""ZS005 全链调试"""
import sys, json
sys.path.insert(0, r'C:\Users\Lin\Desktop\skills\liu-yao\scripts')
from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain
from run_blind_v4 import hex2yao

h = build_hexagram_result(hex2yao("恒", "鼎"), "子月癸酉日自占婚得恒之鼎", "manual", 2024, 6, 1, 10,
                          explicit_time={"month_sb": "甲子", "day_sb": "癸酉"})
tc = run_thinking_chain(h)
for name in ["step2_use_god_identification", "step3_strength_analysis", "step4_change_analysis"]:
    d = tc.get(name, {}) or {}
    print("====", name)
    if name == "step3_strength_analysis":
        print(json.dumps({k: d.get(k) for k in ["use_god_branch", "effective_score", "strength_level", "is_empty", "empty_modifier_reason", "modifiers", "summary_text"]}, ensure_ascii=False, indent=1)[:1200])
    elif name == "step4_change_analysis":
        print(json.dumps({k: d.get(k) for k in ["net_effect", "details", "moving_summary"]}, ensure_ascii=False, indent=1)[:1500])
s5 = tc.get("step5_synthesis", {}) or {}
print("step5 final:", s5.get("final_score"), s5.get("verdict"))
for ln in s5.get("reasoning_chain", []):
    print(ln[:180])
