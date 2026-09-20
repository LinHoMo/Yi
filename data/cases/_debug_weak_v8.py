# -*- coding: utf-8 -*-
"""Diagnose weak cases: change types, hidden spirit, harmony patterns."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain
from run_blind_v4 import date_from_str, hex2yao

cc = json.load(open(ROOT / "data" / "cases" / "classical_cases.json", encoding="utf-8"))
targets = {"ZS005", "ZS009", "ZS011", "ZS012", "ZS014", "ZS016", "ZS020"}

for case in cc["cases"]:
    if case["id"] not in targets:
        continue
    cid = case["id"]
    q = case["question"]
    inp = case.get("input", {})
    hx = case.get("hexagram", {})
    d = date_from_str(inp.get("date", ""))
    ho, hc = hx.get("original"), hx.get("changed")
    explicit = None
    if d.get("day_sb") or d.get("month_branch"):
        explicit = {}
        if d.get("day_sb"):
            explicit["day_sb"] = d["day_sb"]
        if d.get("month_branch"):
            explicit["month_sb"] = "甲" + d["month_branch"]
    yao = hex2yao(ho, hc) if ho else None
    h = build_hexagram_result(yao, q, "manual", d["year"], d["month"], d["day"], 10, explicit_time=explicit)
    tc = run_thinking_chain(h)
    s2 = tc.get("step2_use_god_identification", {})
    s4 = tc.get("step4_change_analysis", {})
    s5 = tc.get("step5_synthesis", {})
    print("=" * 70)
    print(cid, ho, "→", hc, "q=", q)
    print("use_god", s2.get("use_god_category"), (s2.get("selected_use_god") or {}).get("earthly_branch"),
          "pos", (s2.get("selected_use_god") or {}).get("position"))
    print("candidates", [(p.get("position"), p.get("earthly_branch"), p.get("is_moving"), p.get("is_empty")) for p in (s2.get("use_god_positions") or [])])
    print("yuan", s2.get("yuan_shen"), "fu", s2.get("has_fu_cang"), s2.get("fu_cang_detail"))
    print("details:")
    for det in (s4.get("details") or []):
        print(" ", det)
    print("special", s5.get("special_pattern"))
    print("timing", (s5.get("timing") or {}).get("summary_text"))
    print("verdict", s5.get("verdict"), s5.get("final_score"))
    adv = h.get("advanced_analysis") or {}
    ch = adv.get("clash_harmony") or {}
    print("clash_harmony keys", list(ch)[:20] if isinstance(ch, dict) else type(ch))
    if isinstance(ch, dict):
        print(" ", {k: ch[k] for k in list(ch)[:12]})
    print("hidden", adv.get("hidden_spirit_analysis"))
    print("repetition", adv.get("repetition"), adv.get("repetition_deep"))
