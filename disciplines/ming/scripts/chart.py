# -*- coding: utf-8 -*-
"""命·四柱起盘（chart 段）—— 纯机械，无解读（CONTRACT §一）。

输入出生公历时刻（可选性别，仅记录不推大运方向结论），输出四柱与机械因子。
年界立春、月界节气、日柱儒略日——复用 core.ganzhi_calendar。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(CORE), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.ganzhi_calendar import ganzhi_of  # noqa: E402
from yishu_core.ming_tables import (  # noqa: E402
    hidden_stems,
    canggan_ten_gods,
    nayin_of,
    shensha_of_chart,
    ming_shen_gong,
    dayun_direction,
)
from yishu_core.relations import ten_god as _stem_ten_god  # noqa: E402
from yishu_core.symbols import EARTHLY_BRANCHES, HEAVENLY_STEMS, xunkong_of  # noqa: E402


def _split_gz(gz: str) -> tuple[str, str]:
    if not gz or len(gz) < 2:
        return "", ""
    return gz[0], gz[1]


def chart(
    question: str = "命局排盘",
    *,
    datetime_str: str | None = None,
    gender: str | None = None,
    longitude: float | None = None,
) -> dict:
    """出生时刻 → 四柱盘 JSON（机械因子）。"""
    if datetime_str:
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
    else:
        dt = datetime.now()

    moment = ganzhi_of(dt, boundary="day")
    year_gz = moment.year_ganzhi
    month_gz = moment.month_ganzhi
    day_gz = moment.day_ganzhi
    hour_gz = moment.hour_ganzhi

    pillars = {}
    for name, gz in (("year", year_gz), ("month", month_gz), ("day", day_gz), ("hour", hour_gz)):
        stem, branch = _split_gz(gz)
        pillars[name] = {
            "ganzhi": gz,
            "stem": stem,
            "branch": branch,
            "nayin": nayin_of(gz) if gz else None,
        }

    day_stem = pillars["day"]["stem"]
    factors = {}
    for name, p in pillars.items():
        br = p["branch"]
        st = p["stem"]
        stem_god = _stem_ten_god(day_stem, st) if (day_stem and st) else None
        p["ten_god"] = stem_god or ""
        if br:
            factors[name] = {
                "hidden_stems": hidden_stems(br),
                "ten_gods": canggan_ten_gods(day_stem, br),
                "stem_ten_god": stem_god,
            }
        else:
            factors[name] = {"hidden_stems": [], "ten_gods": [], "stem_ten_god": stem_god}

    day_gz = pillars["day"]["ganzhi"] or ""
    xunkong = xunkong_of(day_gz) if day_gz else []

    shensha = []
    try:
        all_branches = [pillars[k]["branch"] for k in ("year", "month", "day", "hour") if pillars[k]["branch"]]
        shensha = shensha_of_chart(
            day_stem,
            year_stem=pillars["year"]["stem"] or "",
            year_branch=pillars["year"]["branch"] or "",
            day_branch=pillars["day"]["branch"] or "",
            all_branches=all_branches,
        )
    except Exception:
        shensha = []

    ming_shen = {}
    try:
        ming_shen = ming_shen_gong(
            pillars["year"]["stem"] or "",
            pillars["month"]["branch"] or "",
            pillars["hour"]["branch"] or "",
        )
    except Exception:
        ming_shen = {}

    return {
        "question": question,
        "discipline": "ming",
        "birth": {
            "datetime": dt.strftime("%Y-%m-%d %H:%M"),
            "gender": gender,
            "longitude": longitude,
        },
        "pillars": pillars,
        "factors": factors,
        "shensha": shensha,
        "ming_shen_gong": ming_shen,
        "xunkong": xunkong,
        "calendar_policy": {"boundary": "day", "zi_hour": "same-day"},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="命·四柱起盘（chart 段，纯机械）")
    ap.add_argument("--datetime", help='出生公历 "YYYY-MM-DD HH:MM"')
    ap.add_argument("--gender", choices=["男", "女"], default=None)
    ap.add_argument("--longitude", type=float, default=None)
    ap.add_argument("--question", default="命局排盘")
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args()

    out = chart(
        args.question,
        datetime_str=args.datetime,
        gender=args.gender,
        longitude=args.longitude,
    )
    text = json.dumps(out, ensure_ascii=False, indent=2, default=str)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
