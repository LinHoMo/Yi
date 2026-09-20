# -*- coding: utf-8 -*-
"""验证 ZS010/ZS012 冲合格局 + ZS016 现状"""
import sys
sys.path.insert(0, r'C:\Users\Lin\Desktop\skills\liu-yao\scripts')
from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain
from run_blind_v4 import hex2yao

cases = [
    ("ZS010", hex2yao("坤"), "戌月甲辰日占借银有否得坤卦", {"month_sb": "甲戌", "day_sb": "甲辰"}),
    ("ZS012", hex2yao("否"), "辰月丁酉日占婚姻成否得否卦", {"month_sb": "甲辰", "day_sb": "丁酉"}),
    ("ZS016", hex2yao("升"), "酉月丙辰日占子病得升卦", {"month_sb": "甲酉", "day_sb": "丙辰"}),
]
for cid, yao, q, ex in cases:
    h = build_hexagram_result(yao, q, "manual", 2024, 6, 1, 10, explicit_time=ex)
    tc = run_thinking_chain(h)
    s5 = tc.get("step5_synthesis", {}) or {}
    sp = s5.get("special_pattern") or {}
    print("%s: 格局=%s | 终分=%s 断=%s" % (cid, sp.get("pattern"), s5.get("final_score"), s5.get("verdict")))
    print("   desc:", sp.get("description", "")[:100])
    for ln in s5.get("reasoning_chain", []):
        if "[格局]" in ln or "[综合]" in ln:
            print("   ", ln[:180])
