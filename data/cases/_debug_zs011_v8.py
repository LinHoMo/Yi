# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain
from run_blind_v4 import date_from_str, hex2yao

cc = json.load(open(ROOT / "data" / "cases" / "classical_cases.json", encoding="utf-8"))
case = next(c for c in cc["cases"] if c["id"] == "ZS011")
q = case["question"]
hx = case["hexagram"]
d = date_from_str(case["input"]["date"])
yao = hex2yao(hx["original"], hx["changed"])
print("yao values", yao)
h = build_hexagram_result(yao, q, "manual", d["year"], d["month"], d["day"], 10,
                          explicit_time={"day_sb": d["day_sb"], "month_sb": "甲" + d["month_branch"]})
print("orig yao_lines:")
for y in h["original_hexagram"]["yao_lines"]:
    print(" ", {k: y.get(k) for k in ("position","earthly_branch","six_relation","is_moving","is_empty")})
ch = h.get("changed_hexagram") or {}
print("changed name", ch.get("name"))
print("changed yao_lines:")
for y in ch.get("yao_lines") or []:
    print(" ", y)
tc = run_thinking_chain(h)
s2 = tc["step2_use_god_identification"]
print("selected", s2.get("selected_use_god"))
print("candidates", s2.get("use_god_positions"))
