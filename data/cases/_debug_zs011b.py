# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain, get_changed_hexagram_branch, KE_CYCLE, BRANCH_ELEMENTS, JUE_MAP
from run_blind_v4 import date_from_str, hex2yao

cc = json.load(open(ROOT / "data" / "cases" / "classical_cases.json", encoding="utf-8"))
case = next(c for c in cc["cases"] if c["id"] == "ZS011")
d = date_from_str(case["input"]["date"])
yao = hex2yao(case["hexagram"]["original"], case["hexagram"]["changed"])
h = build_hexagram_result(yao, case["question"], "manual", d["year"], d["month"], d["day"], 10,
                          explicit_time={"day_sb": d["day_sb"], "month_sb": "甲" + d["month_branch"]})
print("changed_hexagram type", type(h.get("changed_hexagram")), h.get("changed_hexagram"))
ch = h.get("changed_hexagram") or {}
print("ch name", ch.get("name") if isinstance(ch, dict) else ch)
print("lookup", get_changed_hexagram_branch((ch.get("name") if isinstance(ch, dict) else None) or "讼", 1))

# simulate priority
branch, cb = "丑", get_changed_hexagram_branch("讼", 1)
be, ce = BRANCH_ELEMENTS.get(branch), BRANCH_ELEMENTS.get(cb)
print("self_hurt calc", branch, cb, be, ce, KE_CYCLE.get(ce) == be, JUE_MAP.get(be) == cb)

tc = run_thinking_chain(h)
s2 = tc["step2_use_god_identification"]
print("selected", s2.get("selected_use_god"))
print("all candidates", s2.get("use_god_positions"))
