# -*- coding: utf-8 -*-
import json
from pathlib import Path

p = Path(__file__).parent
base = json.load(open(p / "classical_cases.json", encoding="utf-8"))
eng = json.load(open(p / "blind_engine_output_v4.json", encoding="utf-8"))

lines = []
for i in range(20):
    b = base["cases"][i]
    e = eng["cases"][i]
    x_cat = b["expected"].get("use_god_god", b["expected"].get("use_god", ""))
    e_cat = e.get("use_god_category", "")
    x_br = b["expected"].get("use_god_branch")
    e_br = e.get("use_god_branch")
    lines.append(
        f"{b['id']}: base={x_cat!r} eng={e_cat!r} match={x_cat==e_cat} "
        f"br_x={x_br!r} br_e={e_br!r} v_x={b['expected'].get('verdict')!r} v_e={e.get('verdict')!r} "
        f"tags={e.get('pattern_tags')}"
    )

out = "\n".join(lines)
(p / "_debug_compare.txt").write_text(out, encoding="utf-8")
print(out)
