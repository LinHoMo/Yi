# -*- coding: utf-8 -*-
"""六爻纳甲·起卦（chart 段）—— 纯机械排盘，无解读成分（CONTRACT §一）。

对既有 `engine.build_hexagram_result` 的薄适配：不改引擎内部，
只负责按契约产出结构化的 chart JSON（排盘 + 干支 + 旬空 + 六亲），供 analyze 段消费。

chart 段**不做**经典增强分析（enhance_reading）：其输出含 summary/comment/meaning
级别的断语文本（"回头克（大凶）"一类），违反 CONTRACT §一「chart 禁一切吉凶措辞」；
且 analyze 段（thinking_chain.run_thinking_chain）本就按需自行产出 advanced_analysis，
消费链（step3/4/5、narrate、render、evidence、faithfulness）读的都是 analyze 输出，
换产地不删数据。验证走既有 `dev_tools/check.py` 与金标准指纹，不新增推演逻辑。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import engine as engine  # noqa: E402
from engine import build_hexagram_result, coin_toss  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

# 根 README 的运行示例是 `python liuyao/scripts/chart.py --mode coin … --question "某事如何"`：
# 不带这行，GBK/cp936 控制台下 JSON 里的中文会输出成乱码（实测 rc=0 但 "question":"ĳ"），
# 命令"跑通了"却给出读不懂的产物。八字侧 chart.py 早有同名调用，此处补齐孪生差异。
force_utf8_stdio()


def _parse_yao_values(text: str) -> list[int]:
    vals = [int(x.strip()) for x in text.split(",") if x.strip()]
    if len(vals) != 6 or any(v not in (6, 7, 8, 9) for v in vals):
        raise ValueError("--yao 需要 6 个爻值（6=老阴动,7=少阳静,8=少阴静,9=老阳动），如 7,8,9,7,6,8")
    return vals


def _resolve_moment(datetime_str: str | None, hour: int | None,
                    zi_hour_type: str | None = None,
                    distinguish_zi_hour: bool = False) -> tuple:
    """解析起卦时刻（含 --hour 覆盖与早晚子时），返回 (年, 月, 日, 时, 分, zi_info)。

    分只用于报告里"起卦时刻"的呈现：干支以时辰为单位，分钟不参与推演。
    --hour 覆盖小时时，分钟随之归零（否则会印出"覆盖后的小时 + 原分钟"这种
    并不存在的时刻）。

    子时口径（2026-10-09 修 G）：旧代码 `except TypeError` 兜底把
    `zi_hour_type=` kwarg 调用静默吞回默认口径——engine_calendar.handle_zi_hour
    当时根本没有该参数，early/late 旗标全部无效（SKILL.md 明禁的静默替代）。
    现签名真实支持，兜底删除：再出 TypeError 就直接炸，不允许就地降级。
    --distinguish-zi-hour 只启用夜子/晨子记录，口径仍为默认（当日换日）；
    欲采 23 点换日一派必须显式 --zi-hour-type late。
    """
    if datetime_str:
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
    else:
        now = datetime.now()
        dt = datetime(now.year, now.month, now.day, now.hour, now.minute)

    if hour is not None:
        hh, minute = hour, 0
    else:
        hh, minute = dt.hour, dt.minute
    year, month, day = dt.year, dt.month, dt.day

    zi_info = None
    if zi_hour_type or distinguish_zi_hour:
        zi_info = engine.handle_zi_hour(
            hh, minute, year, month, day, zi_hour_type=zi_hour_type)
        if zi_info is not None:
            year = zi_info["day_year"]
            month = zi_info["day_month"]
            day = zi_info["day_day"]
    return year, month, day, hh, minute, zi_info


def chart(mode: str, question: str, *, datetime_str: str | None = None,
          numbers: str | None = None, yao: str | None = None, seed: int | None = None,
          year: int | None = None, month: int | None = None, day: int | None = None,
          hour: int | None = None, longitude: float | None = None,
          distinguish_zi_hour: bool = False, zi_hour_type: str | None = None) -> dict:
    """四段契约 chart：起卦 → 排盘 JSON。

    参数与 `engine.py` 对齐：mode ∈ coin|time|number|manual。
    """
    # 子时口径：--zi-hour-type 是唯一能改日柱的旗标（late=23点换日、early=00点换日）；
    # --distinguish-zi-hour 只记录夜子/晨子，不改口径（旧代码把它映射成 "late"，
    # 等于默认启用换日派，与 engine_calendar 文档「不默认生效」直接矛盾，已纠）。
    zi_type = zi_hour_type

    # 时间模式：显式年月日时优先，否则解析 datetime_str
    if mode == "time" and year is not None and month is not None and day is not None:
        yy, mm, dd, hh = year, month, day, hour if hour is not None else 12
        minute = 0
        _zi = engine.handle_zi_hour(hh, minute, yy, mm, dd,
                                    zi_hour_type=zi_type) if (
            zi_type or distinguish_zi_hour) else None
        if _zi is not None:
            yy, mm, dd = _zi["day_year"], _zi["day_month"], _zi["day_day"]
    else:
        yy, mm, dd, hh, minute, _zi = _resolve_moment(
            datetime_str, hour, zi_type, distinguish_zi_hour)

    if mode == "coin":
        # coin_toss() 自身即摇满六爻、返回 6 个爻值；外面再套一层 range(6) 会把
        # 6 个子列表当成 6 个爻值，`val in (6, 9)` 恒 False → 恒阴、恒坤、永无动爻。
        # 2026-10-25 实测：连续五次铜钱起卦全部得「坤」，静卦无动，起卦彻底失效。
        rng = engine.random.Random(seed) if seed is not None else None
        yao_values = coin_toss(rng)
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
        yao_values = coin_toss(rng)

    result = build_hexagram_result(
        yao_values, question, mode, yy, mm, dd, hh, minute=minute,
    )

    # 早晚子时信息（与引擎 main 一致地挂到 enhancements）
    if _zi is not None:
        result.setdefault("enhancements", {})["zi_hour_handling"] = {
            k: (v.strftime("%Y-%m-%d") if hasattr(v, "strftime") else v)
            for k, v in _zi.items()
        }

    # 经典增强分析（advanced_analysis）不在本段产出：其 summary/comment/meaning
    # 含吉凶断语，属 analyze/narrate 层素材（CONTRACT §一 chart 禁吉凶措辞）。
    # analyze 段的 thinking_chain.run_thinking_chain 检测到 advanced_analysis
    # 缺失时会自行调 enhance_reading，产出的字段与消费链与此前完全一致。

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
    ap.add_argument("--distinguish-zi-hour", action="store_true",
                    help="记录夜子/晨子信息（日柱口径仍为默认：当日换日，不换日）")
    ap.add_argument("--zi-hour-type", choices=["early", "late"], default=None,
                    help="子时换日口径：late=23:00 换日（夜子时日柱取翌日）；"
                         "early=00:00 换日（与默认口径日柱相同）。不指定则不启用流派切换")
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
