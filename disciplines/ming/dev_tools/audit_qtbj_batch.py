# -*- coding: utf-8 -*-
"""逐例对拍外集 tiaohou 批：打印每个 QTBJ 案例的 expected vs 引擎实际，
并标出命中/失配。只读诊断，不改任何数据。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT))

from yishu_core.ming_tables import tiaohou_of  # noqa: E402

EXT = ROOT / "disciplines" / "ming" / "data" / "cases" / "ming_external_cases.json"

# 月支 → 引擎键直接用月支，无需再转月序（引擎 TIAO_HOU 的键就是月支）


def main() -> None:
    d = json.loads(EXT.read_text(encoding="utf-8"))
    cases = [c for c in d["cases"] if c["id"].startswith("QTBJ")]
    ok = bad = 0
    for c in cases:
        exp = (c.get("expected", {}).get("tiaohou") or {})
        p = c["pillars"]
        day_stem = p["day"][0]
        month_branch = p["month"][1]
        act = tiaohou_of(month_branch, day_stem) or {}
        em, ea = exp.get("main", ""), exp.get("assist", "") or ""
        am, aa = act.get("main", ""), act.get("assist", "") or ""
        hit = (em == am) and (ea == aa)
        ok += hit
        bad += (not hit)
        mark = "√" if hit else "×"
        print(f"{mark} {c['id']}  {p['month']}{day_stem}日  expected {em}/{ea}  引擎 {am}/{aa}   {c['location']}")
    print(f"\nQTBJ 批 tiaohou：{ok}/{len(cases)} 命中，失配 {bad}")
    print("口径：expected 逐字取自书源该格月度句；引擎取自同书同表——**同源覆盖审计，非独立验证**。")


if __name__ == "__main__":
    main()
