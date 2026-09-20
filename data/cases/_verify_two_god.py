# -*- coding: utf-8 -*-
"""验证两现用神：ZS001/ZS005/ZS009/ZS011"""
import json, sys
sys.path.insert(0, r'C:\Users\Lin\Desktop\skills\liu-yao\scripts')
from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain
from run_blind_v4 import hex2yao

cases = [
    ("ZS001", hex2yao("益"), "求财", {"month_sb": "甲巳", "day_sb": "戊戌"}),
    ("ZS005", hex2yao("恒", "鼎"), "自占婚", {"month_sb": "甲子", "day_sb": "癸酉"}),
    ("ZS009", hex2yao("恒", "豫"), "出外贸易", {"month_sb": "甲午", "day_sb": "丙辰"}),
    ("ZS011", hex2yao("巽", "讼"), "失银", {"month_sb": "甲寅", "day_sb": "戊戌"}),
]
for cid, yao, q, ex in cases:
    h = build_hexagram_result(yao, q, "manual", 2024, 6, 1, 10, explicit_time=ex)
    tc = run_thinking_chain(h)
    s2 = tc.get("step2_use_god_identification", {}) or {}
    s5 = tc.get("step5_synthesis", {}) or {}
    sel = s2.get("selected_use_god") or {}
    cands = [p.get("earthly_branch") + str(p.get("position")) + ("动" if p.get("is_moving") else "") + ("空" if p.get("is_empty") else "") for p in (s2.get("use_god_positions") or [])]
    print("%s: 候选=[%s] -> 选中=%s@%s(%s爻) reason=%s | 终分=%s 断=%s" % (
        cid, ",".join(cands), s2.get("use_god_category"), sel.get("earthly_branch"),
        sel.get("position"), sel.get("reason"), s5.get("final_score"), s5.get("verdict")))
