# -*- coding: utf-8 -*-
"""择吉·四段管线冒烟测试：chart → analyze → narrate → render 全链路。

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

# (名称, chart params)：覆盖吉/凶/平方向、带时辰路径、活动识别
SMOKES = [
    ("2026-09-25 嫁娶（锚点日：执/青龙黄道/牛）",
     {"date": "2026-09-25", "activity": "嫁娶", "question": "结婚嫁娶吉否"}),
    ("2026-09-30 开市（吉日：开/天德黄道/壁）",
     {"date": "2026-09-30", "activity": "开市", "question": "开张营业吉否"}),
    ("2026-10-01 开市（凶日：闭/白虎黑道/奎）",
     {"date": "2026-10-01", "activity": "开市", "question": "开张营业吉否"}),
    ("2026-09-23 出行带时辰（平/司命黄道/箕 + 午时值神）",
     {"date": "2026-09-23", "hour_branch": "午", "activity": "出行",
      "question": "长途出行吉否"}),
    ("2026-09-29 纳财（吉日：收/金匮黄道/室，活动自动识别）",
     {"date": "2026-09-29", "question": "今日签约收款吉利否"}),
]


def main() -> int:
    from yishu_core.runtime import force_utf8_stdio
    force_utf8_stdio()
    ok = 0
    for name, params in SMOKES:
        try:
            c = chart(params)
            a = analyze(c)
            text = narrate(a)
            report = render(a)
            assert c.get("jian_chu") and c.get("day_god") and c.get("xiu")
            assert a.get("conclusion") and a["conclusion"].get("方向")
            assert text and "# 择吉" in text
            assert report and "盘面数据" in report
            if params.get("hour_branch"):
                assert c.get("hour") and c["hour"].get("god")
            ok += 1
            print(f"  √ {name} → {a['conclusion']['方向']}（得分 {a['conclusion']['得分']}）")
        except Exception as exc:
            print(f"  × {name}：{type(exc).__name__}: {exc}")
    print(f"\n四段管线冒烟：有产出: {ok}/{len(SMOKES)}")
    return 0 if ok == len(SMOKES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
