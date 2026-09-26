# -*- coding: utf-8 -*-
"""四段管线冒烟：对一组输入跑 chart→analyze→narrate→render，只验有无产出。

    python scripts/smoke_test.py   # 退出码 0 全绿；输出 "有产出: N"
"""
from __future__ import annotations

import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from chart import chart  # noqa: E402
from analyze import analyze  # noqa: E402
from narrate import narrate  # noqa: E402
from render import render  # noqa: E402

# (名称, chart params)：覆盖三种起卦方式与特断/数应路径
SMOKES = [
    ("观梅占（numbers）", {"way": "numbers", "year_num": 5, "month": 12,
                          "day": 17, "hour_num": 9, "motion": "立",
                          "question": "二雀争枝坠地，占明晚之事"}),
    ("扣门借物（two_numbers）", {"way": "two_numbers", "upper_num": 1, "lower_num": 5,
                               "hour_num": 10, "question": "扣门借物，所占何物"}),
    ("datetime 起卦", {"way": "datetime", "datetime": "2026-09-23 10:30",
                      "question": "占今日之事，能成否"}),
    ("lunar 起卦", {"way": "lunar", "year": 2026, "month": 8, "day": 13,
                   "hour_branch": "午", "question": "占出行"}),
    ("卦象特断（西林寺）", {"way": "two_numbers", "upper_num": 7, "lower_num": 8,
                          "hour_num": 0, "question": "西林寺额占"}),
    ("多爻动（manual 1,2）", {"way": "manual", "upper": "乾", "lower": "震",
                            "movings": [1, 2], "question": "占求财"}),
]


def main() -> int:
    from yishu_core.runtime import force_utf8_stdio
    force_utf8_stdio()
    ok, failures = 0, []
    for name, params in SMOKES:
        try:
            c = chart(params)
            a = analyze(c)
            n = narrate(a)
            r = render(a)
            if not (c.get("hexagram") and a.get("conclusion") and n.strip()
                    and "盘面数据" in r and r.strip()):
                failures.append(f"{name}: 产出不完整（c={bool(c.get('hexagram'))} "
                                f"a={bool(a.get('conclusion'))} "
                                f"n={len(n.strip())} r_has_table={'盘面数据' in r}）")
                continue
            ok += 1
        except Exception as exc:
            failures.append(f"{name}: {type(exc).__name__}: {exc}")
    print(f"有产出: {ok}")
    for f in failures:
        print("  !", f)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
