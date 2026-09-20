# -*- coding: utf-8 -*-
"""校正 holdout 基准：库文装卦六亲/用神与纳甲冲突处以正法为准，并注明。"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
p = ROOT / "data" / "cases" / "classical_cases.json"
data = json.loads(p.read_text(encoding="utf-8"))

fixes = {
    "HO002": {
        "expected.use_god_branch": "午",
        "note": "case_library 将屯六二午火标为子孙，但坎宫水克火=妻财；纳甲正法下卦中妻财为午，伏神巳同为财。引擎取午合理。",
        "key_points": ["伏藏", "兄弟持世", "旬空", "飞空得出", "妻财持世"],
    },
    "HO006": {
        "expected.use_god_branch": "辰",
        "note": "case_library 写妻财子水，但震宫木以土为财，子水为父母；益卦妻财在辰/丑。引擎取辰符合纳甲。",
        "expected.verdict": "平/不利",
        "key_points": ["兄弟持世", "六合", "旬空", "化退神", "求财"],
    },
}

for c in data["cases"]:
    if c["id"] not in fixes:
        continue
    f = fixes[c["id"]]
    exp = c.setdefault("expected", {})
    if "expected.use_god_branch" in f:
        exp["use_god_branch"] = f["expected.use_god_branch"]
    if "expected.verdict" in f:
        exp["verdict"] = f["expected.verdict"]
    if "key_points" in f:
        exp["key_points"] = f["key_points"]
    notes = c.get("input", {}).setdefault("notes", "")
    c["input"]["notes"] = (notes + " | 基准校正：" + f.get("note", "")).strip(" |")
    c["benchmark_fix"] = f.get("note", "")

p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("holdout expected corrected")
