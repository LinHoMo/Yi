# -*- coding: utf-8 -*-
"""验证出旬有验：ZS004 / ZS011 / ZS019 / ZS001"""
import sys
sys.path.insert(0, r'C:\Users\Lin\Desktop\skills\liu-yao\scripts')
from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain
from run_blind_v4 import hex2yao

cases = [
    ("ZS004", hex2yao("同人"), "见贵求财", {"month_sb": "甲申", "day_sb": "丁卯"}),
    ("ZS011", hex2yao("巽", "讼"), "失银", {"month_sb": "甲寅", "day_sb": "戊戌"}),
    ("ZS019", hex2yao("巽", "讼"), "失银", {"month_sb": "甲辰", "day_sb": "丁亥"}),
    ("ZS001", hex2yao("益"), "求财", {"month_sb": "甲巳", "day_sb": "戊戌"}),
]
for cid, yao, q, ex in cases:
    h = build_hexagram_result(yao, q, "manual", 2024, 6, 1, 10, explicit_time=ex)
    tc = run_thinking_chain(h)
    s3 = tc.get("step3_strength_analysis", {}) or {}
    s5 = tc.get("step5_synthesis", {}) or {}
    mods = ", ".join("%s:%s" % (m.get("type"), m.get("value")) for m in s3.get("modifiers", []))
    print("%s: 旺衰分=%s | 终分=%s 断=%s | 格局=%s | mods=[%s]" % (
        cid, s3.get("effective_score"), s5.get("final_score"), s5.get("verdict"),
        (s5.get("special_pattern") or {}).get("pattern"), mods))
