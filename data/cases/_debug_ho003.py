# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Lin\Desktop\skills\liu-yao\.worktrees\liuyao-holdout")
sys.path.insert(0, str(ROOT / "scripts"))
from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain, BRANCH_ELEMENTS, SHENG_CYCLE
from run_blind_v4 import date_from_str, hex2yao

cases = json.load(open(ROOT / "data" / "cases" / "classical_cases.json", encoding="utf-8"))["cases"]
case = next(c for c in cases if c["id"] == "HO003")
print("question", case["question"], case["input"])
d = date_from_str(case["input"]["date"])
yao = hex2yao(case["hexagram"]["original"], case["hexagram"]["changed"])
print("yao", yao)
h = build_hexagram_result(yao, case["question"], "manual", d["year"], d["month"], d["day"], 10,
                          explicit_time={"day_sb": d["day_sb"], "month_sb": "甲" + d["month_branch"]})
tc = run_thinking_chain(h)
s2 = tc["step2_use_god_identification"]
s5 = tc["step5_synthesis"]
print("use", s2.get("use_god_category"), s2.get("use_god_element"), s2.get("selected_use_god"))
for y in h["original_hexagram"]["yao_lines"]:
    if y.get("is_world"):
        print("world", y)
print("verdict", s5.get("verdict"), s5.get("final_score"))
print("reason", [x for x in (tc.get("reasoning_chain") or []) if "格局" in x or "综合" in x or "归" in x][:8])
# check source has classical_notes
src = (ROOT / "scripts" / "thinking_chain.py").read_text(encoding="utf-8")
print("has classical_adj", "classical_adj" in src)
print("has 用神生世·迟归", "用神生世·迟归" in src)
idx = src.find("用神生世·迟归")
print(src[idx-200:idx+200] if idx>0 else "missing")
