# -*- coding: utf-8 -*-
"""调试 ZS016 step3 完整扣分链"""
import sys, json
sys.path.insert(0, r'C:\Users\Lin\Desktop\skills\liu-yao\scripts')
from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain
from run_blind_v4 import hex2yao

h = build_hexagram_result(hex2yao("升"), "酉月丙辰日占子病得升卦", "manual", 2024, 6, 1, 10,
                          explicit_time={"month_sb": "甲酉", "day_sb": "丙辰"})
tc = run_thinking_chain(h)
s3 = tc.get("step3_strength_analysis", {}) or {}
print(json.dumps({k: s3.get(k) for k in ["base_score", "adjusted_score", "effective_score", "strength_level",
                                          "god_month_strength", "god_month_score", "god_day_strength", "god_day_score",
                                          "day_modifier", "is_empty", "is_month_break", "is_an_dong",
                                          "twelve_growth_stage", "twelve_growth_modifier", "modifiers"]},
                 ensure_ascii=False, indent=1))
