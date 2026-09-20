# -*- coding: utf-8 -*-
"""ZS015 全链"""
import sys, json
sys.path.insert(0, r'C:\Users\Lin\Desktop\skills\liu-yao\scripts')
from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain

with open(r'C:\Users\Lin\Desktop\skills\liu-yao\data\cases\classical_cases.json', encoding='utf-8') as f:
    cc = json.load(f)
c = next(x for x in cc["cases"] if x["id"] == "ZS015")
print("ZS015:", json.dumps(c.get("hexagram"), ensure_ascii=False), c.get("input", {}).get("date"), json.dumps(c.get("expected"), ensure_ascii=False)[:300])
import run_blind_v4 as d
dt = d.date_from_str(c["input"]["date"])
ho = c["hexagram"].get("original"); hc = c["hexagram"].get("changed")
yao = d.hex2yao(ho, hc)
print("yao:", yao)
h = build_hexagram_result(yao, c["input"]["question"], "manual", dt["year"], dt["month"], dt["day"], 10,
                          explicit_time={"month_sb": "甲" + (dt["month_branch"] or "未"), "day_sb": dt["day_sb"]})
tc = run_thinking_chain(h)
s2 = tc.get("step2_use_god_identification", {}) or {}
s5 = tc.get("step5_synthesis", {}) or {}
sel = s2.get("selected_use_god") or {}
print("用神:", s2.get("use_god_category"), "@", sel.get("earthly_branch"), "伏藏:", sel.get("is_fu_cang"))
print("终分:", s5.get("final_score"), "断:", s5.get("verdict"))
for ln in s5.get("reasoning_chain", []):
    print(ln[:200])
