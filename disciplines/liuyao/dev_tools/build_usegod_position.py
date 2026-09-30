# -*- coding: utf-8 -*-
"""use_god_position 基准例补全器（一次性数据构建，产物入库、脚本留档可复跑）。

口径：expected.use_god_position 只在**纳甲唯一可定**时填写——
  书面已明写 用神六亲（expected.use_god）与 用神地支（expected.use_god_branch），
  而该（六亲, 地支）组合在本卦爻线中**恰出现一处**，则爻位由纳甲唯一确定，
  属卦表机械事实（对表回归性质），不涉解读分歧；多处出现（用神多现）一律跳过。
数据源：卦面爻线由引擎 build_hexagram_result 按 core 纳甲真值表排出
（与 case_runner 同一入口），本脚本不做任何手工指定。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
for _p in (str(DISC / "scripts"), str(DISC.parents[1] / "core")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from liuyao_engine import build_hexagram_result  # noqa: E402
import case_runner as cr  # noqa: E402

CASES = DISC / "data" / "cases" / "classical_cases.json"


def main() -> int:
    store = json.loads(CASES.read_text(encoding="utf-8"))
    filled = skipped_multi = skipped_no_base = 0
    for case in store.get("cases", []):
        exp = case.get("expected") or {}
        god, branch = exp.get("use_god"), exp.get("use_god_branch")
        if not god or not branch or exp.get("use_god_position"):
            if exp.get("use_god_position"):
                filled += 1
            else:
                skipped_no_base += 1
            continue
        hx = case.get("hexagram") or {}
        yao_vals = cr.hex2yao(hx.get("original"), hx.get("changed"))
        if yao_vals is None:
            skipped_no_base += 1
            continue
        resolved = cr.resolve_case_time(case)
        dt = resolved["dt"]
        h = build_hexagram_result(yao_vals, case.get("question", ""), "manual",
                                  dt.year, dt.month, dt.day, dt.hour)
        matches = [y["position"] for y in h["original_hexagram"]["yao_lines"]
                   if y.get("six_relation") == god and y.get("earthly_branch") == branch]
        if len(matches) == 1:
            exp["use_god_position"] = matches[0]
            exp.setdefault("use_god_position_basis",
                          f"纳甲唯一可定：{god}({branch})在本卦仅{matches[0]}爻一处")
            filled += 1
        else:
            skipped_multi += 1

    CASES.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"已填 {filled}（含原有）｜用神多现等跳过 {skipped_multi}｜无基准 {skipped_no_base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
