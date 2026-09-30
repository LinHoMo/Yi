# -*- coding: utf-8 -*-
"""大六壬·课例评测（书源内嵌课例 vs 引擎复算）——**机械一致率**口径。

    python scripts/evaluate.py            # 全量课例
    python scripts/evaluate.py --verbose

口径（NEW-DISCIPLINES §2.1：机械一致率与对齐分必须分开报，不得混算互冒）：
  - 本集 expected 只有书上明写的三传（个别例兼明写门类），逐字可回指原文；
  - 度量 = 引擎九宗门复算与书面三传的**机械一致率**，检验的是起课链路
    （天地盘/四课/判据树）与古籍实例的吻合，**不是对齐分，更不是预测率**；
  - n < 20 只报命中数，不报百分比；
  - 重建方式：定位语（X加Y/干上X/支上X）→ 天地盘旋转 delta，与 `dev_tools/
    build_course_cases.py` 的提取口径一致；定位语缺失的书中课例不入集（宁缺勿滥）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(CORE), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.ganzhi_calendar import EARTHLY_BRANCHES as _BR  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from jiuzongmen import san_chuan_full  # noqa: E402

CASES = Path(__file__).resolve().parents[1] / "data" / "cases" / "course_examples.json"


def load_cases() -> list[dict]:
    return list(json.loads(CASES.read_text(encoding="utf-8")).get("cases") or [])


def tianpan_of_delta(delta: int) -> dict[str, str]:
    """天地盘旋转：天盘[地盘位] = 地盘位 + delta（δ=月将-时支 的等价形式）。"""
    return {g: _BR[(_BR.index(g) + delta) % 12] for g in _BR}


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(
        description="大六壬课例评测（书源内嵌课例；机械一致率口径，非对齐分非预测率）")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    cases = load_cases()
    if not cases:
        print("无可用课例（course_examples.json 为空）")
        return 1

    hits, men_hits, men_applicable = 0, 0, 0
    rows = []
    for c in cases:
        tianpan = tianpan_of_delta(c["delta"])
        res = san_chuan_full(c["day_ganzhi"][0], c["day_ganzhi"][1], tianpan)
        want = c["expected"]["san_chuan"]
        ok = res["san_chuan"] == want
        hits += ok
        men_ok = None
        if c.get("expected_men"):
            men_applicable += 1
            men_ok = res["men"] == c["expected_men"]
            men_hits += men_ok
        rows.append((c, res, ok, men_ok))
        if args.verbose:
            mark = "√" if ok else "×"
            men_txt = f" 门类 {res['men']}（书 {'√' if men_ok else '×'}）" if men_ok is not None else ""
            print(f"  {c['id']} {c['day_ganzhi']} δ={c['delta']} [{mark}] "
                  f"引擎 {''.join(res['san_chuan'])} vs 书 {''.join(want)}{men_txt}")
            if not ok:
                print(f"      quote: {c['source_quote'][:80]}")

    n = len(cases)
    print(f"\n=== 课例机械一致率（n={n}）===")
    if n < 20:
        print(f"  三传命中 {hits}/{n}（n<20 不报百分比）")
    else:
        print(f"  三传命中 {hits}/{n} = {hits / n:.1%}")
    if men_applicable:
        print(f"  门类命中 {men_hits}/{men_applicable}（书明写门类的例）")
    print("  口径：机械一致率（起课链路与古籍实例吻合度），不是对齐分，")
    print("  不是现实预测命中率；n<20 只报命中数（铁律三）。")
    print("  逐例引文可回指 data/cases/course_examples.json 的 source_quote。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
