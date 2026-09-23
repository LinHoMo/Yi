# -*- coding: utf-8 -*-
"""小六壬·四段管线冒烟测试：chart → analyze → narrate → render 全链路。

    python scripts/smoke_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(CORE), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from chart import chart  # noqa: E402
from analyze import analyze  # noqa: E402
from narrate import narrate  # noqa: E402
from render import render  # noqa: E402

# (名称, chart params)：覆盖月日时起课与变通/随机取数两种路径
SMOKES = [
    ("八月初十五申时（实例1 找人）",
     {"way": "month_day_hour", "month": 8, "day": 15, "hour_ordinal": 9,
      "question": "去朋友家，测有人否"}),
    ("报数15138（实例2 讨债）",
     {"way": "numbers", "numbers": [1, 5, 1, 3, 8], "question": "明日讨债顺利否"}),
    ("datetime 起课",
     {"way": "datetime", "datetime": "2026-09-23 10:30", "question": "今日出行顺利否"}),
    ("lunar 起课",
     {"way": "lunar", "year": 2026, "month": 8, "day": 15, "hour_branch": "申",
      "question": "占天气"}),
    ("随机取数（开饭店）",
     {"way": "numbers", "numbers": [10], "question": "开饭店吉利否"}),
]


def main() -> int:
    ok = 0
    for name, params in SMOKES:
        try:
            c = chart(params)
            a = analyze(c)
            text = narrate(a)
            report = render(a)
            assert c.get("palace") is not None and c["palace"] in range(6)
            assert a.get("palace") and a["palace"].get("宫名")
            assert text and "# 小六壬" in text
            assert report and "盘面数据" in report
            ok += 1
            print(f"  √ {name} → {a['palace']['宫名']}（{a['conclusion']['方向']}）")
        except Exception as exc:
            print(f"  × {name}：{type(exc).__name__}: {exc}")
    print(f"\n四段管线冒烟：有产出: {ok}/{len(SMOKES)}")
    return 0 if ok == len(SMOKES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
