# -*- coding: utf-8 -*-
"""大六壬·起课（chart 段）—— 纯机械，无解读成分。

起课法（data/sources/liu-ren-da-quan.wikitext.txt 卷一「入手法」）：
  1. 干支时刻：日干支、时支由内核历法给出；
  2. 月将：中气换将（太阳过宫），内核 `liuren_tables.yuejiang_of`；
  3. 月将加时 → 天地盘：天盘[地盘位] = 月将起时支顺数；
  4. 十干寄宫 → 四课（一二自日干、三四自日支）；
  5. 九宗门取三传（`jiuzongmen.san_chuan_full`）＋三传遁干（本旬）；
  6. 十二天将（昼夜贵人定顺逆布）。
断语/诀文一律在 data/verdicts.json；本文件只做机械排盘。
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

from yishu_core.ganzhi_calendar import (  # noqa: E402
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
    ganzhi_of,
)
from yishu_core.symbols import xunkong_of  # noqa: E402
from yishu_core.liuren_tables import (  # noqa: E402
    tianjiang_layout,
    yuejiang_of,
)
from jiuzongmen import four_courses, san_chuan_full  # noqa: E402


def build_tianpan(yuejiang_branch: str, hour_branch: str) -> dict[str, str]:
    """月将加于时支之上 → 天地盘 {地盘位: 天盘神}。"""
    jiang_idx = EARTHLY_BRANCHES.index(yuejiang_branch)
    hour_idx = EARTHLY_BRANCHES.index(hour_branch)
    return {ground: EARTHLY_BRANCHES[(jiang_idx - hour_idx + i) % 12]
            for i, ground in enumerate(EARTHLY_BRANCHES)}


def dun_gan_of(day_ganzhi: str, branch: str) -> str:
    """本旬遁干：旬首支 = 日支回溯日干序差，支距即干序。"""
    si = HEAVENLY_STEMS.index(day_ganzhi[0])
    bi = EARTHLY_BRANCHES.index(day_ganzhi[1])
    xun_start = EARTHLY_BRANCHES[(bi - si) % 12]
    d = (EARTHLY_BRANCHES.index(branch) - EARTHLY_BRANCHES.index(xun_start)) % 12
    return HEAVENLY_STEMS[d % 10]


def chart(datetime_str: str, question: str = "", gender: str = "") -> dict:
    dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
    moment = ganzhi_of(dt, boundary="day")
    day_gz = moment.day_ganzhi
    hour_branch = moment.hour_ganzhi[1]

    yj = yuejiang_of(dt)
    tianpan = build_tianpan(yj["branch"], hour_branch)
    san = san_chuan_full(day_gz[0], day_gz[1], tianpan)
    courses = four_courses(day_gz[0], day_gz[1], tianpan)

    chuan = san["san_chuan"]
    dun = [dun_gan_of(day_gz, b) for b in chuan]
    jiang = tianjiang_layout(day_gz[0], hour_branch, tianpan)
    # 天将乘临：三传各支今临何位、乘何将（传神为天盘神，临其本家地盘位之将）
    chuan_tianjiang = []
    for b in chuan:
        pos = next(p for p, sky in tianpan.items() if sky == b)
        chuan_tianjiang.append({"chuan": b, "lin": pos, "jiang": jiang.get(pos, "")})

    return {
        "discipline": "liuren",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "question": question,
        "input": {"datetime": datetime_str, "gender": gender},
        "calendar_policy": {"yuejiang": yj["policy"], "ganzhi_boundary": "day",
                            "day_night": "mao_you"},
        "moment": {
            "day_ganzhi": day_gz,
            "hour_ganzhi": moment.hour_ganzhi,
            "month_ganzhi": moment.month_ganzhi,
            "month_branch": moment.month_ganzhi[1],
            "hour_branch": hour_branch,
            "xunkong": xunkong_of(day_gz),
        },
        "yuejiang": yj,
        "tianpan": {g: tianpan[g] for g in EARTHLY_BRANCHES},
        "four_courses": [
            {"pos": c["pos"], "xia": c["xia"], "shang": c["shang"]}
            for c in courses
        ],
        "men": san["men"],
        "ke_name": san["ke_name"],
        "men_trigger": san["trigger"],
        "men_verified": san["verified"],
        "day_kind": san["day_kind"],
        "san_chuan": chuan,
        "dun_gan": dun,
        "tianjiang_layout": jiang,
        "chuan_tianjiang": chuan_tianjiang,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="大六壬起课（纯机械排盘，非吉凶断语）")
    ap.add_argument("--datetime", "-t", required=True, help="公历时刻 YYYY-MM-DD HH:MM")
    ap.add_argument("--question", "-q", default="", help="所问之事")
    ap.add_argument("--gender", "-g", default="", help="性别（本段不参与推演）")
    ap.add_argument("--out", "-o", help="输出 JSON 路径（缺省打印 stdout）")
    args = ap.parse_args()
    out = chart(args.datetime, args.question, args.gender)
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"chart 已写出 → {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
