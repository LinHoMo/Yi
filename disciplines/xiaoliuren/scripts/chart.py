# -*- coding: utf-8 -*-
"""小六壬·起课（chart 段）—— 纯机械，无解读成分。

起课法（《贺氏六壬小手册·小六壬预测法》第二节推算方法）：
  六宫次序固定：大安→留连→速喜→赤口→小吉→空亡（循环）。
  以"大安"起正月，顺数至所求月 → 月宫；
  以月宫起初一，顺数至所求日 → 日宫；
  以日宫起子时，顺数至所求时辰 → 时宫（课体）。
  地支对应：寅位起大安（寅卯辰巳午未申酉戌亥子丑两轮六宫）。

变通取数法（第三节）：三个数字代替月、日、时，效果一样——
  第一数自大安起数，第二数自上数落宫起数，第三数同理。任意个数均可
  （随机取数法，第四节：电话号、扑克牌等化成数即掐）。

本文件只做上述机械掐算；掌诀断辞一律在 data/verdicts.json。
"""
from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(CORE), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.ganzhi_calendar import EARTHLY_BRANCHES, ganzhi_of  # noqa: E402
from yishu_core.lunar import solar_to_lunar, lunar_month_name  # noqa: E402

PALACES = ["大安", "留连", "速喜", "赤口", "小吉", "空亡"]

TOPIC_KEYWORDS = [
    ("失物", ["失物", "丢", "遗失", "找东西", "寻物", "被偷"]),
    ("行人", ["行人", "归期", "找人", "走失", "下落"]),
    ("求财", ["求财", "财", "赚钱", "生意", "投资", "财运", "讨债", "还钱", "借款"]),
    ("官讼", ["官讼", "官司", "诉讼", "官非", "纠纷", "口舌", "是非", "起诉"]),
    ("疾病", ["疾病", "病", "健康", "治疗", "康复", "体检"]),
    ("婚姻", ["婚姻", "婚", "嫁娶", "定亲", "相亲", "感情", "恋爱", "对象"]),
    ("出行", ["出行", "出门", "旅行", "旅游", "出差", "远行", "游玩"]),
    ("家宅", ["家宅", "住宅", "搬家", "迁居", "安宅", "居家", "开张", "开店", "开业"]),
    ("工作", ["工作", "求职", "面试", "升迁", "晋升", "事业", "考试", "学业"]),
    ("天气", ["天气", "晴", "雨", "阴晴", "下雨", "刮风"]),
]


def detect_topic(question: str) -> str:
    q = question or ""
    for topic, words in TOPIC_KEYWORDS:
        if any(w in q for w in words):
            return topic
    return "人事"


def chart_from_month_day_hour(month: int, day: int, hour_ordinal: int) -> dict:
    """月日时起课（月日时即三个数，自大安起顺数六宫）。"""
    month_palace = (month - 1) % 6
    day_palace = (month_palace + (day - 1)) % 6
    hour_palace = (day_palace + (hour_ordinal - 1)) % 6
    return {
        "way": "month_day_hour",
        "steps": [month_palace, day_palace, hour_palace],
        "step_names": ["月宫", "日宫", "时宫"],
        "palace": hour_palace,
        "month": month,
        "day": day,
        "hour_ordinal": hour_ordinal,
    }


def chart_from_numbers(nums: list[int]) -> dict:
    """变通/随机取数：任意个数，第一数自大安起数，其后自上数落宫起数。"""
    if not nums:
        raise ValueError("报数起课至少需要一个数")
    steps, cur = [], 0
    for n in nums:
        if n < 1:
            raise ValueError(f"报数须为正整数，收到 {n}")
        cur = (cur + (n - 1)) % 6
        steps.append(cur)
    return {
        "way": "numbers",
        "steps": steps,
        "step_names": [f"第{i + 1}数" for i in range(len(steps))],
        "palace": cur,
        "numbers": list(nums),
    }


def chart_from_datetime(dt: datetime) -> dict:
    """公历时刻起课：农历月日为月、日，时辰为时（《贺氏六壬》用农历月日）。"""
    lun = solar_to_lunar(dt.date())
    if lun is None:
        raise ValueError(f"{dt.date()} 超出农历表范围（1900-01-31 起 150 年）")
    hour_branch = ganzhi_of(dt).hour_ganzhi[1]
    hour_ordinal = EARTHLY_BRANCHES.index(hour_branch) + 1
    out = chart_from_month_day_hour(lun["month"], lun["day"], hour_ordinal)
    out["time"] = {
        "dt": dt.strftime("%Y-%m-%d %H:%M"),
        "ganzhi": ganzhi_of(dt).summary(),
        "lunar_month": lun["month"],
        "lunar_month_name": lunar_month_name(lun["month"], lun["leap"]),
        "lunar_day": lun["day"],
        "hour_branch": hour_branch,
    }
    return out


def chart_from_lunar(year: int, month: int, day: int, hour_branch: str) -> dict:
    """农历月日 + 时支起课（贺氏实例原文式：八月初十五申时）。"""
    if not 1 <= month <= 12:
        raise ValueError(f"农历月须在 1–12，收到 {month}")
    if not 1 <= day <= 30:
        raise ValueError(f"农历日须在 1–30，收到 {day}")
    if hour_branch not in EARTHLY_BRANCHES:
        raise ValueError(f"未知时支：{hour_branch}")
    hour_ordinal = EARTHLY_BRANCHES.index(hour_branch) + 1
    out = chart_from_month_day_hour(month, day, hour_ordinal)
    out["time"] = {
        "lunar_year": year,
        "lunar_month": month,
        "lunar_day": day,
        "hour_branch": hour_branch,
    }
    return out


def chart(params: dict) -> dict:
    """统一入口：params 含 way("datetime"/"lunar"/"month_day_hour"/"numbers")。"""
    way = params.get("way", "datetime")
    if way == "datetime":
        dt = params.get("datetime")
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        out = chart_from_datetime(dt)
    elif way == "lunar":
        out = chart_from_lunar(
            int(params.get("year", 0)), int(params["month"]), int(params["day"]),
            params.get("hour_branch", params.get("hour")),
        )
    elif way == "month_day_hour":
        out = chart_from_month_day_hour(
            int(params["month"]), int(params["day"]), int(params["hour_ordinal"]))
    elif way == "numbers":
        out = chart_from_numbers([int(n) for n in params["numbers"]])
    else:
        raise ValueError(f"未知起课方式：{way}")
    out["question"] = params.get("question", "")
    out["topic"] = params.get("topic") or detect_topic(out["question"])
    if params.get("direction"):
        out["direction"] = params["direction"]
    return out


def palace_name(index: int) -> str:
    return PALACES[index]


def _selfcheck() -> None:
    """金标准自检（《贺氏六壬小手册》实例，逐条可复核）：
    八月初十五申时 → 空亡（申=9）；四月初十三辰时 → 留连（辰=5）"""
    r1 = chart_from_month_day_hour(8, 15, 9)
    assert palace_name(r1["palace"]) == "空亡", r1
    r2 = chart_from_month_day_hour(4, 13, 5)
    assert palace_name(r2["palace"]) == "留连", r2
    #   报数 77234 → 大安；99864 → 留连
    r3 = chart_from_numbers([7, 7, 2, 3, 4])
    assert palace_name(r3["palace"]) == "大安", r3
    r4 = chart_from_numbers([9, 9, 8, 6, 4])
    assert palace_name(r4["palace"]) == "留连", r4
    #   四月初二未时 → 空亡（未=8）；十月初六巳时 → 留连（巳=6）
    r5 = chart_from_month_day_hour(4, 2, 8)
    assert palace_name(r5["palace"]) == "空亡", r5
    r6 = chart_from_month_day_hour(10, 6, 6)
    assert palace_name(r6["palace"]) == "留连", r6
    print("小六壬 chart 校验通过（6 例贺氏实例全部复现）")


if __name__ == "__main__":
    import argparse
    import json as _json

    ap = argparse.ArgumentParser(description="小六壬起课（chart 段）")
    ap.add_argument("--selfcheck", action="store_true", help="跑金标准自检")
    ap.add_argument("--way", choices=["datetime", "lunar", "month_day_hour", "numbers"],
                    default="month_day_hour")
    ap.add_argument("--datetime", help="公历时刻 ISO 字符串")
    ap.add_argument("--year", type=int)
    ap.add_argument("--month", type=int)
    ap.add_argument("--day", type=int)
    ap.add_argument("--hour-branch", dest="hour_branch", help="时支（如 申）")
    ap.add_argument("--hour-ordinal", dest="hour_ordinal", type=int, help="时辰序数 子=1…亥=12")
    ap.add_argument("--numbers", help="报数，逗号分隔（如 7,7,2,3,4）")
    ap.add_argument("--topic", help="显式事类（覆盖问句识别）")
    ap.add_argument("--direction", help="目标方位（东/南/中/西/北等，供 analyze 方位/五行综合断）")
    ap.add_argument("--question", default="")
    ap.add_argument("-o", "--out", type=Path, help="写出 chart JSON（缺省打印 stdout）")
    args = ap.parse_args()

    if args.selfcheck:
        _selfcheck()
        raise SystemExit(0)

    if args.way == "datetime":
        if not args.datetime:
            ap.error("--way datetime 需要 --datetime")
        params = {"way": "datetime", "datetime": args.datetime}
    elif args.way == "lunar":
        if not (args.year and args.month and args.day and args.hour_branch):
            ap.error("--way lunar 需要 --year --month --day --hour-branch")
        params = {"way": "lunar", "year": args.year, "month": args.month,
                  "day": args.day, "hour_branch": args.hour_branch}
    elif args.way == "month_day_hour":
        if not (args.month and args.day and args.hour_ordinal):
            ap.error("--way month_day_hour 需要 --month --day --hour-ordinal")
        params = {"way": "month_day_hour", "month": args.month,
                  "day": args.day, "hour_ordinal": args.hour_ordinal}
    else:
        if not args.numbers:
            ap.error("--way numbers 需要 --numbers")
        params = {"way": "numbers", "numbers": [int(n) for n in args.numbers.split(",")]}
    params.update({"question": args.question, "topic": args.topic,
                   "direction": args.direction})
    try:
        out = chart(params)
    except Exception as exc:
        print(f"起课异常：{type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
    out["palace_name"] = palace_name(out["palace"])
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(_json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("起课 →", args.out)
    else:
        print(_json.dumps(out, ensure_ascii=False, indent=2))
