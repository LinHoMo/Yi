# -*- coding: utf-8 -*-
"""八字四段接线冒烟（A2-A·第三百三十五批）：chart→analyze→narrate→render 都有产出。

这不是正确性测试，也不是覆盖率：只验**接线通不通**——四段各给出契约要求的形状，
且两条起盘入参路径（公历 datetime / 书载四柱）都不抛异常。内容对不对由
`dev_tools/golden.py`（指纹）与 `tests/regression_test.py`（固定断言）负责。

    python bazi/tests/smoke_test.py
    python bazi/tests/smoke_test.py -v
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
for _p in (str(DISC / "scripts"), str(DISC / "core")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from chart import chart, chart_from_pillars  # noqa: E402
from analyze import analyze  # noqa: E402
from narrate import narrate  # noqa: E402
from render import render  # noqa: E402

# CONTRACT.md §四 的键面（八字侧真值源 data/rules/layer_contract.json）
CHART_KEYS = {"birth", "calendar_policy", "discipline", "factors", "ming_shen_gong",
              "pillars", "question", "shensha", "xunkong"}
ANALYZE_KEYS = {"birth", "calendar_policy", "chart_summary", "conclusion", "dayun",
                "dayun_ming_yindong", "discipline", "factors", "female_fu_zi", "liu_yue",
                "liunian_ming_yindong", "ming_shen_gong", "pillar_relations", "pillars",
                "question", "san_hui", "shensha", "strength", "tai_yuan", "ten_god_combos",
                "tian_ke_di_chong", "tiaohou", "tong_guan", "xiao_yun", "xunkong", "bing_yao"}


def run_case(name: str, use_pillars: bool, verbose: bool) -> list[str]:
    errs: list[str] = []
    if use_pillars:
        c = chart_from_pillars({"year": "戊戌", "month": "丙辰", "day": "乙未", "hour": "丙戌"},
                               gender="男", question=name)
    else:
        c = chart(name, datetime_str="1984-02-10 10:00", gender="男")
    missing = CHART_KEYS - set(c)
    extra = set(c) - CHART_KEYS
    if missing or extra:
        errs.append(f"{name}：chart 键面越界 缺 {sorted(missing)} 多 {sorted(extra)}")
    a = analyze(c)
    missing = ANALYZE_KEYS - set(a)
    extra = set(a) - ANALYZE_KEYS
    if missing or extra:
        errs.append(f"{name}：analyze 键面越界 缺 {sorted(missing)} 多 {sorted(extra)}")
    con = a.get("conclusion") or {}
    if not con:
        errs.append(f"{name}：analyze.conclusion 为空（四段契约要求产出定性结论）")
    text = narrate(a)
    if not text or not str(text).strip():
        errs.append(f"{name}：narrate 产出为空")
    md = render(a)
    if not md or "## 机械因子" not in md:
        errs.append(f"{name}：render 未产出 Markdown 章节")
    if verbose:
        print(f"  · {name}: chart {len(c)} 键 / analyze {len(a)} 键 / "
              f"narrate {len(text)} 字 / render {len(md)} 字")
    return errs


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="八字四段接线冒烟（只验有无产出）")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    cases = [("公历起盘", False), ("书载四柱起盘", True)]
    errs: list[str] = []
    for name, use_pillars in cases:
        errs += run_case(name, use_pillars, args.verbose)
    if errs:
        for e in errs:
            print(f"  × {e}")
        return 1
    print(f"  √ 冒烟：{len(cases)} 条入参路径 × 四段全部有产出（只验接线，不验对错）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
