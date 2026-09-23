# -*- coding: utf-8 -*-
"""择吉·起局（chart 段）—— 纯机械，无解读成分。

对给定公历日期（可带时辰）装配择日盘：
  1. 干支历（年/月/日柱，内核 ganzhi_calendar）
  2. 建除十二神（月建 + 日支，内核 zeji_tables）
  3. 日值黄黑道神 + 黄道/黑道归属（内核 zeji_tables）
  4. 二十八宿值日（内核 zeji_tables，含日禽名）
  5. 时辰值神（给了时支才出）

星宿吉凶宜忌、建除宜忌、黄黑道宜忌属解读层，一律在 data/verdicts.json。
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
from yishu_core.zeji_tables import (  # noqa: E402
    jian_chu_of,
    day_god_of,
    hour_god_of,
    is_huang_dao,
    xiuxiu_of,
)

ACTIVITY_KEYWORDS = [
    ("嫁娶", ["嫁", "娶", "婚", "订婚", "结婚", "提亲", "迎亲"]),
    ("开市", ["开市", "开业", "开张", "开店", "开张", "开公司", "开张营业", "开盘"]),
    ("出行", ["出行", "出门", "旅行", "旅游", "出差", "远行", "启程", "动身"]),
    ("入宅", ["入宅", "搬家", "迁居", "乔迁", "进宅", "新居", "入住"]),
    ("安葬", ["安葬", "下葬", "落葬", "出殡", "殡葬", "迁坟", "合葬"]),
    ("动土", ["动土", "开工", "奠基", "修造", "装修", "建房", "拆建"]),
    ("祭祀", ["祭祀", "祈福", "还愿", "拜神", "祭祖", "扫墓", "上香"]),
    ("入学", ["入学", "考试", "开学", "拜师", "开笔"]),
    ("上任", ["上任", "赴任", "就职", "述职", "入职"]),
    ("纳财", ["纳财", "交易", "签约", "签合同", "收款", "进货", "买", "购"]),
]


def detect_activity(question: str) -> str:
    q = question or ""
    for act, words in ACTIVITY_KEYWORDS:
        if any(w in q for w in words):
            return act
    return "通用"


def _parse_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def chart_from_date(d: date, hour_branch: str | None = None) -> dict:
    """公历日期（+ 可选时支）→ 择日盘。"""
    gz = ganzhi_of(datetime(d.year, d.month, d.day, 12))
    lun = solar_to_lunar(d)
    if lun is None:
        raise ValueError(f"{d} 超出农历表范围（1900-01-31 起 150 年）")

    month_branch = gz.month_branch
    day_branch = gz.day_ganzhi[1]
    xiu = xiuxiu_of(d)
    god = day_god_of(month_branch, day_branch)
    out = {
        "way": "date",
        "date": d.isoformat(),
        "weekday": "一二三四五六日"[d.weekday()],
        "lunar": {
            "year": lun["year"], "month": lun["month"], "day": lun["day"],
            "leap": lun["leap"],
            "month_name": lunar_month_name(lun["month"], lun["leap"]),
        },
        "ganzhi": {
            "年柱": gz.year_ganzhi,
            "月柱": gz.month_ganzhi,
            "日柱": gz.day_ganzhi,
            "月建": month_branch,
            "日支": day_branch,
        },
        "jian_chu": jian_chu_of(month_branch, day_branch),
        "day_god": god,
        "huang_dao": is_huang_dao(god) if god else False,
        "xiu": xiu,
    }
    if hour_branch:
        if hour_branch not in EARTHLY_BRANCHES:
            raise ValueError(f"未知时支：{hour_branch}")
        out["hour"] = {
            "branch": hour_branch,
            "god": hour_god_of(month_branch, hour_branch),
        }
    return out


def chart(params: dict) -> dict:
    """统一入口：params 含 date（公历 ISO 字符串）/ datetime；可选 hour_branch。"""
    d = _parse_date(params.get("date") or params.get("datetime"))
    out = chart_from_date(d, params.get("hour_branch"))
    out["question"] = params.get("question", "")
    out["activity"] = params.get("activity") or detect_activity(out["question"])
    return out


def _selfcheck() -> None:
    """金标准自检（内核锚点已与多家黄历核对）：
    2026-09-23 → 平/箕；2026-09-24 → 定/勾陈黑道；2026-09-25 → 执/青龙黄道/牛。"""
    c1 = chart_from_date(date(2026, 9, 23))
    assert c1["jian_chu"] == "平" and c1["xiu"]["name"] == "箕", c1
    c2 = chart_from_date(date(2026, 9, 24))
    assert c2["jian_chu"] == "定" and c2["day_god"] == "勾陈" and not c2["huang_dao"], c2
    c3 = chart_from_date(date(2026, 9, 25))
    assert c3["jian_chu"] == "执" and c3["day_god"] == "青龙" and c3["huang_dao"], c3
    assert c3["xiu"]["name"] == "牛", c3
    print("择吉 chart 校验通过（2026-09-23~25 与通书黄历一致）")


if __name__ == "__main__":
    import argparse
    import json as _json

    ap = argparse.ArgumentParser(description="择吉起局（chart 段）")
    ap.add_argument("--selfcheck", action="store_true", help="跑金标准自检")
    ap.add_argument("--date", default="2026-09-25", help="公历日期 YYYY-MM-DD")
    ap.add_argument("--hour-branch", dest="hour_branch", help="时支（如 午），可选")
    ap.add_argument("--activity", help="显式事类（覆盖问句识别）")
    ap.add_argument("--question", default="")
    ap.add_argument("-o", "--out", type=Path, help="写出 chart JSON（缺省打印 stdout）")
    args = ap.parse_args()

    if args.selfcheck:
        _selfcheck()
        raise SystemExit(0)

    try:
        out = chart({"date": args.date, "hour_branch": args.hour_branch,
                     "question": args.question, "activity": args.activity})
    except Exception as exc:
        print(f"起局异常：{type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(_json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("起局 →", args.out)
    else:
        print(_json.dumps(out, ensure_ascii=False, indent=2))
