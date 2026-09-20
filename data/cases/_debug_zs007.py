# -*- coding: utf-8 -*-
"""ZS007 全链"""
import sys, json
sys.path.insert(0, r'C:\Users\Lin\Desktop\skills\liu-yao\scripts')
from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain
from run_blind_v4 import hex2yao

with open(r'C:\Users\Lin\Desktop\skills\liu-yao\data\cases\classical_cases.json', encoding='utf-8') as f:
    cc = json.load(f)
c = next(x for x in cc["cases"] if x["id"] == "ZS007")
print("ZS007:", json.dumps(c.get("hexagram"), ensure_ascii=False), c.get("input", {}).get("date"), c.get("expected"))
ho = c["hexagram"].get("original")
hc = c["hexagram"].get("changed")
d = __import__("run_blind_v4", fromlist=["date_from_str", "hex2yao"])
dt = d.date_from_str(c["input"]["date"])
yao = d.hex2yao(ho, hc)
h = build_hexagram_result(yao, c["input"]["question"], "manual", dt["year"], dt["month"], dt["day"], 10,
                          explicit_time={"month_sb": "甲" + (dt["month_branch"] or "未"), "day_sb": dt["day_sb"]})
tc = run_thinking_chain(h)
s5 = tc.get("step5_synthesis", {}) or {}
s2 = tc.get("step2_use_god_identification", {}) or {}
sel = s2.get("selected_use_god") or {}
print("用神:", s2.get("use_god_category"), "@", sel.get("earthly_branch"), "| 终分:", s5.get("final_score"), "断:", s5.get("verdict"))
print("special:", json.dumps(s5.get("special_pattern"), ensure_ascii=False)[:400])
for ln in s5.get("reasoning_chain", []):
    print(ln[:200])
