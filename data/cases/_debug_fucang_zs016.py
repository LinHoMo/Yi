# -*- coding: utf-8 -*-
"""调试 ZS016 伏藏全链路"""
import sys, json
sys.path.insert(0, r'C:\Users\Lin\Desktop\skills\liu-yao\scripts')
from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain
from run_blind_v4 import hex2yao

h = build_hexagram_result(hex2yao("升"), "酉月丙辰日占子病得升卦", "manual", 2024, 6, 1, 10,
                          explicit_time={"month_sb": "甲酉", "day_sb": "丙辰"})
tc = run_thinking_chain(h)
s2 = tc.get("step2_use_god_identification", {}) or {}
s3 = tc.get("step3_strength_analysis", {}) or {}
print("=== step2 ===")
print(json.dumps(s2, ensure_ascii=False, indent=1)[:1500])
print("=== step3 key ===")
for k in ["use_god_position", "use_god_branch", "effective_score", "strength_level", "has_fu_cang", "can_emerge", "fu_cang_analysis", "summary_text"]:
    print(k, "=", s3.get(k))
