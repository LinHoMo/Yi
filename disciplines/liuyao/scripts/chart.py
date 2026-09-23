# -*- coding: utf-8 -*-
"""六爻纳甲·起卦（chart 段）—— 纯机械排盘，无解读成分（CONTRACT §一）。

对既有 `liuyao_engine.build_hexagram_result` 的薄适配：不改引擎内部，
只负责按契约产出结构化的 chart JSON（排盘 + 干支 + 旬空 + 六亲 + 增强分析），
供 analyze 段消费。验证走既有 `tools/check.py` 与金标准指纹，不新增推演逻辑。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import liuyao_engine as engine  # noqa: E402
from liuyao_engine import build_hexagram_result, coin_toss  # noqa: E402


def _parse_yao_values(text: str) -> list[int]:
    vals = [int(x.strip()) for x in text.split(",") if x.strip()]
    if len(vals) != 6 or any(v not in (6, 7, 8, 9) for v in vals):
        raise ValueError("--yao 需要 6 个爻值（6=老阴动,7=少阳静,8=少阴静,9=老阳动），如 7,8,9,7,6,8")
    return vals


def _resolve_moment(datetime_str: str | None, hour: int | None,
                    zi_hour_type: str | None = None) -> tuple:
    """解析起卦时刻（含 --hour 覆盖与早晚子时），返回 (year, month, day, hour, zi_info)。"""
    if datetime_str:
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
    else:
        now = datetime.now()
        dt = datetime(now.year, now.month, now.day, now.hour, now.minute)

    hh = hour if hour is not None else dt.hour
    year, month, day = dt.year, dt.month, dt.day

    zi_info = None
    if zi_hour_type:
        try:
            zi_info = engine.handle_zi_hour(
                hh, 0, year, month, day, zi_hour_type=zi_hour_type)
        except TypeError:
            zi_info = engine.handle_zi_hour(hh, 0, year, month, day)
        if zi_info is not None:
            year = zi_info["day_year"]
            month = zi_info["day_month"]
            day = zi_info["day_day"]
    return year, month, day, hh, zi_info


def chart(mode: str, question: str, *, datetime_str: str | None = None,
          numbers: str | None = None, yao: str | None = None, seed: int | None = None,
          year: int | None = None, month: int | None = None, day: int | None = None,
          hour: int | None = None, longitude: float | None = None,
          distinguish_zi_hour: bool = False, zi_hour_type: str | None = None) -> dict:
    """四段契约 chart：起卦 → 排盘 JSON。

    参数与 `liuyao_engine.py` 对齐：mode ∈ coin|time|number|manual。
    """
    zi_type = zi_hour_type
    if zi_type is None and distinguish_zi_hour:
        zi_type = "late"  # 与引擎默认：晚子时按翌日

    # 时间模式：显式年月日时优先，否则解析 datetime_str
    if mode == "time" and year is not None and month is not None and day is not None:
        yy, mm, dd, hh = year, month, day, hour if hour is not None else 12
        _zi = None
    else:
        yy, mm, dd, hh, _zi = _resolve_moment(datetime_str, hour, zi_type)

    if mode == "coin":
        rng = engine.random.Random(seed) if seed is not None else None
        yao_values = [coin_toss(rng) for _ in range(6)]
    elif mode == "number":
        if not numbers:
            raise ValueError("--mode number 需要 --numbers \"a,b,c\"")
        parts = [int(x.strip()) for x in numbers.split(",") if x.strip()]
        if len(parts) != 3:
            raise ValueError("--numbers 需要三个数字")
        yao_values = engine.number_based_hexagram(*parts)
    elif mode == "manual":
        yao_values = _parse_yao_values(yao)
    else:  # coin 兜底
        rng = engine.random.Random(seed) if seed is not None else None
        yao_values = [coin_toss(rng) for _ in range(6)]

    result = build_hexagram_result(
        yao_values, question, mode, yy, mm, dd, hh,
    )

    # 早晚子时信息（与引擎 main 一致地挂到 enhancements）
    if _zi is not None:
        result.setdefault("enhancements", {})["zi_hour_handling"] = {
            k: (v.strftime("%Y-%m-%d") if hasattr(v, "strftime") else v)
            for k, v in _zi.items()
        }

    # 增强分析：伏藏、暗动、月破、三合局等经典断法
    try:
        from classical_analysis import enhance_reading
        enhance_reading(result)
    except ImportError:
        pass

    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="六爻纳甲起卦（chart 段）")
    ap.add_argument("--mode", choices=["coin", "time", "number", "manual"],
                    default="coin", help="起卦方式（缺省 coin）")
    ap.add_argument("--question", default="", help="求测问题")
    ap.add_argument("--datetime", help='时间起卦的指定时间，格式: "YYYY-MM-DD HH:MM"')
    ap.add_argument("--numbers", help='数字起卦的三个数字，格式: "a,b,c"')
    ap.add_argument("--yao", help='手动指定的6个爻值，格式: "v1,...,v6"')
    ap.add_argument("--seed", type=int, default=None, help="随机种子，用于可复现的铜钱摇卦")
    ap.add_argument("--longitude", type=float, default=None, help="东经，用于真太阳时校正")
    ap.add_argument("--hour", type=int, default=None, help="手动指定小时(0-23)，覆盖 --datetime")
    ap.add_argument("--distinguish-zi-hour", action="store_true", help="启用早晚子时区分")
    ap.add_argument("--zi-hour-type", choices=["early", "late"], default=None,
                    help="手动指定子时类型（优先级高于自动判断）")
    ap.add_argument("-o", "--out", type=Path, help="写出 chart JSON（缺省打印 stdout）")
    args = ap.parse_args()

    result = chart(
        args.mode, args.question,
        datetime_str=args.datetime, numbers=args.numbers, yao=args.yao,
        seed=args.seed, longitude=args.longitude, hour=args.hour,
        distinguish_zi_hour=args.distinguish_zi_hour, zi_hour_type=args.zi_hour_type,
    )
    text = json.dumps(result, ensure_ascii=False, indent=2, default=str)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
