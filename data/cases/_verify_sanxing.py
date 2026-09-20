# -*- coding: utf-8 -*-
"""验证三刑修正：ZS005/ZS010/ZS002"""
import json, sys
sys.path.insert(0, r'C:\Users\Lin\Desktop\skills\liu-yao\scripts')
from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain
from run_blind_v4 import hex2yao

cases = [
    ("ZS005恒", hex2yao("恒", "鼎"), "自占婚", {"month_sb": "甲子", "day_sb": "癸酉"}),
    ("ZS010坤", hex2yao("坤"), "占借银", {"month_sb": "甲戌", "day_sb": "甲辰"}),
    ("ZS002蒙", hex2yao("蒙", "未济"), "岳父近病", {"month_sb": "甲巳", "day_sb": "庚辰"}),
]
for cid, yao, q, ex in cases:
    h = build_hexagram_result(yao, q, "manual", 2024, 6, 1, 10, explicit_time=ex)
    tc = run_thinking_chain(h)
    s3 = tc.get("step3_strength_analysis", {}) or {}
    s5 = tc.get("step5_synthesis", {}) or {}
    print("%s: 三刑修正=%s (reason=%s) | 旺衰分=%s | 终分=%s 断=%s" % (
        cid, s3.get("three_punishment_modifier"), s3.get("three_punishment_reason"),
        s3.get("effective_score"), s5.get("final_score"), s5.get("verdict")))
