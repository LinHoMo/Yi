# -*- coding: utf-8 -*-
"""梅花易数·起卦（chart 段）—— 纯机械，无解读成分。

三种起卦输入，任选其一：
  datetime : 公历时刻（自动取 年支序 / 农历月日 / 时辰序）
  lunar    : 农历年月日 + 时支（观梅占原文式输入）
  numbers  : 直接给 (年数, 月数, 日数, 时数) 四数

取数（《卷一·年月日时起例》"子年一数…亥年十二数；月如正月一数…
日如初一一数…子时一数直至亥时十二数"）：
  上卦 = (年数 + 月数 + 日数) 除以 8 之余（余 0 作 8）
  下卦 = (年数 + 月数 + 日数 + 时数) 除以 8 之余
  动爻 = (年数 + 月数 + 日数 + 时数) 除以 6 之余（余 0 作 6）

体用（《梅花易数》通行法，动者为用、静者为体）：
  动爻在下卦（1–3 爻）→ 上卦为体、下卦为用；
  动爻在上卦（4–6 爻）→ 下卦为体、上卦为用。
  多爻动（两爻及以上，通行扩展口径，规则见 data/verdicts.json#multi_move_rules）：
    动尽下卦 → 上体下用；动尽上卦 → 下体上用；
    上下皆动 → 动爻多者所在卦为用；两卦动数相同 → 初动爻（序号最小）所在卦为用。
互卦：去初爻与上爻，二三四爻为下互、三四五爻为上互。
变卦：诸动爻同时阴阳互变后的别卦。
"""
from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(CORE), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.ganzhi_calendar import (  # noqa: E402
    EARTHLY_BRANCHES,
    ganzhi_of,
)
from yishu_core.lunar import solar_to_lunar, lunar_to_solar, lunar_month_name  # noqa: E402
from yishu_core.symbols import (  # noqa: E402
    HEXAGRAM_TRIGRAMS,
    BAGUA_LINES,
    XIAN_TIAN_TRIGRAM_NUMBERS,
    NUMBER_TO_TRIGRAM,
    TRIGRAM_ELEMENTS,
)

# (上卦, 下卦) → 六十四卦名（逆查 HEXAGRAM_TRIGRAMS）
_TRIGRAMS_TO_NAME = {v: k for k, v in HEXAGRAM_TRIGRAMS.items()}

# 年支 → 序数（子1…亥12，观梅占"辰年五数"）
_YEAR_BRANCH_ORDINAL = {b: i + 1 for i, b in enumerate(EARTHLY_BRANCHES)}
# 时辰支 → 序数（子1…亥12）
_HOUR_ORDINAL = {b: i + 1 for i, b in enumerate(EARTHLY_BRANCHES)}

TOPIC_KEYWORDS = [
    ("天时", ["天时", "天气", "晴", "雨", "阴晴", "刮风"]),
    ("家宅", ["家宅", "住宅", "搬家", "迁居", "安宅", "居家"]),
    ("屋舍", ["屋舍", "房屋", "买房", "购房", "置业"]),
    ("婚姻", ["婚姻", "婚", "嫁娶", "定亲", "相亲", "感情", "恋爱", "对象"]),
    ("生产", ["生产", "分娩", "临盆", "生子", "生育"]),
    ("饮食", ["饮食", "吃饭", "请客", "酒席", "餐饮"]),
    ("求谋", ["求谋", "谋事", "谋划", "计划", "筹划"]),
    ("求名", ["求名", "功名", "考试", "升学", "晋升", "评优", "求职", "面试"]),
    ("求财", ["求财", "财", "赚钱", "生意", "投资", "财运", "利市"]),
    ("交易", ["交易", "买卖", "成交", "谈生意", "订单"]),
    ("出行", ["出行", "出门", "旅行", "旅游", "出差", "远行"]),
    ("行人", ["行人", "行人", "归期", "找人", "走失"]),
    ("谒见", ["谒见", "拜见", "求见", "拜访", "谒见"]),
    ("失物", ["失物", "丢失", "遗失", "找东西", "寻物"]),
    ("疾病", ["疾病", "病", "健康", "治疗", "康复", "体检"]),
    ("官讼", ["官讼", "官司", "诉讼", "官非", "纠纷", "起诉", "开庭"]),
    ("坟墓", ["坟墓", "坟", "墓地", "迁坟", "安葬", "殡葬"]),
]


def detect_topic(question: str) -> str:
    """问事文本 → 事类（卷二十八占例之一）；无命中默认「人事」。"""
    q = question or ""
    for topic, words in TOPIC_KEYWORDS:
        if any(w in q for w in words):
            return topic
    return "人事"


def _normalize(remainder: int, base: int) -> int:
    """余数归一：余 0 作 base（卦以八除余 0 作坤八；爻以六除余 0 作第六爻）。"""
    return base if remainder == 0 else remainder


def _hexagram_of(upper: str, lower: str) -> str:
    return _TRIGRAMS_TO_NAME[(upper, lower)]


def _trigram_from_number(n: int) -> str:
    """先天卦数 1..8 → 经卦（乾1…坤8）。"""
    return NUMBER_TO_TRIGRAM[_normalize(n, 8)]


def interacting_trigrams(lines: list[int]) -> tuple[str, str]:
    """六爻线（自下而上）→ (下互卦, 上互卦)。去初爻与上爻。"""
    lower = _trigram_from_lines(lines[1:4])
    upper = _trigram_from_lines(lines[2:5])
    return lower, upper


def _trigram_from_lines(three: list[int]) -> str:
    for name, pat in BAGUA_LINES.items():
        if pat == three:
            return name
    raise ValueError(f"非八卦爻线：{three}")


def _moving_in_upper(moving: int) -> bool:
    return moving >= 4


def _normalize_movings(moving=None, movings=None) -> list[int]:
    """动爻归一为升序去重列表（1–6）。接受 int / list；movings 优先于 moving。"""
    raw = movings if movings is not None else moving
    if raw is None:
        raise ValueError("必须给动爻（moving 或 movings）")
    if isinstance(raw, int):
        raw = [raw]
    out = sorted({int(x) for x in raw})
    if not out:
        raise ValueError("动爻列表不能为空")
    for m in out:
        if m < 1 or m > 6:
            raise ValueError(f"动爻须在 1–6：{m}")
    return out


def _body_use_of(movings: list[int]) -> tuple[str, str, str]:
    """多爻动体用取舍（通行口径，verdicts.json#multi_move_rules）。

    返回 (体所在侧, 用所在侧, 规则名)，侧为 "upper"/"lower"。
    动者为用：动尽一侧 → 该侧为用；两侧皆动 → 动多者为用；相同 → 初动爻所在侧为用。
    """
    lower_m = [m for m in movings if m <= 3]
    upper_m = [m for m in movings if m >= 4]
    if lower_m and not upper_m:
        return "upper", "lower", "动尽下卦：上体下用"
    if upper_m and not lower_m:
        return "lower", "upper", "动尽上卦：下体上用"
    if len(lower_m) > len(upper_m):
        return "upper", "lower", "下卦动多：上体下用"
    if len(upper_m) > len(lower_m):
        return "lower", "upper", "上卦动多：下体上用"
    if min(movings) <= 3:
        return "upper", "lower", "动数相同·初动在下：上体下用"
    return "lower", "upper", "动数相同·初动在上：下体上用"


def _build_chart(upper: str, lower: str, movings: list[int], **extra) -> dict:
    """经卦 + 动爻列表 → 完整盘数据（单动/多动共用）。"""
    u_lines, l_lines = BAGUA_LINES[upper], BAGUA_LINES[lower]
    lines = l_lines + u_lines  # 自下而上 6 爻
    changed = list(lines)
    for m in movings:
        changed[m - 1] = 1 - changed[m - 1]

    body_side, use_side, rule = _body_use_of(movings)
    body_trig = upper if body_side == "upper" else lower
    use_trig = upper if use_side == "upper" else lower

    lower_hu, upper_hu = interacting_trigrams(lines)
    changed_upper = _trigram_from_lines(changed[3:])
    changed_lower = _trigram_from_lines(changed[:3])
    changed_hex = _TRIGRAMS_TO_NAME.get((changed_upper, changed_lower))
    # 变出之卦：动爻所在经卦变后的经卦（《观梅占》"变艮土生兑金"即取动爻侧）
    # 多爻动两侧皆变时取用侧变出之卦，并以 changed_trigrams 给出两侧。
    if body_side == "upper":
        use_changed = changed_lower
        body_changed = changed_upper
    else:
        use_changed = changed_upper
        body_changed = changed_lower
    lower_moved = any(m <= 3 for m in movings)
    upper_moved = any(m >= 4 for m in movings)
    if lower_moved and upper_moved:
        changed_trigrams = [changed_lower, changed_upper]
        changed_trigram = use_changed
    elif lower_moved:
        changed_trigrams = [changed_lower]
        changed_trigram = changed_lower
    else:
        changed_trigrams = [changed_upper]
        changed_trigram = changed_upper

    out = {
        "upper": upper,
        "lower": lower,
        "moving": movings[0],          # 主动爻（兼容一爻动接口；多动取初动爻）
        "movings": movings,
        "moving_count": len(movings),
        "multi_move": len(movings) > 1,
        "body_use_rule": rule,
        "hexagram": _hexagram_of(upper, lower),
        "body": body_trig,
        "use": use_trig,
        "body_element": TRIGRAM_ELEMENTS[body_trig],
        "use_element": TRIGRAM_ELEMENTS[use_trig],
        "interacting_lower": lower_hu,
        "interacting_upper": upper_hu,
        "changed_hexagram": changed_hex,
        "changed_trigram": changed_trigram,
        "changed_trigrams": changed_trigrams,
        "changed_upper": changed_upper,
        "changed_lower": changed_lower,
        "body_changed_trigram": body_changed,
        "use_changed_trigram": use_changed,
        "lines": lines,
        "changed_lines": changed,
    }
    out.update(extra)
    return out


def chart_from_numbers(year_num: int, month: int, day: int, hour_num: int,
                       movings: list[int] | None = None) -> dict:
    """四数起卦（年月日时起例，观梅占式）。movings 可显式指定多动爻（默认单动）。"""
    up_num = _normalize((year_num + month + day) % 8, 8)
    down_num = _normalize((year_num + month + day + hour_num) % 8, 8)
    auto = _normalize((year_num + month + day + hour_num) % 6, 6)
    upper, lower = NUMBER_TO_TRIGRAM[up_num], NUMBER_TO_TRIGRAM[down_num]
    use_movings = _normalize_movings(movings if movings is not None else auto)
    return _build_chart(
        upper, lower, use_movings,
        year_num=year_num, month=month, day=day, hour_num=hour_num,
        total=year_num + month + day + hour_num,
    )


def chart_from_two_numbers(upper_num: int, lower_num: int, hour_num: int = 0,
                           movings: list[int] | None = None) -> dict:
    """两数起卦（《卷一·物数占例/声音占例/字画占》）：上卦=物数、下卦=时数（或字数），
    动爻 = (上卦数 + 下卦数 + 时数) 以六除之余。
    邻夜扣门借物占：一声乾(1)为上卦、五声巽(5)为下卦、酉时(10) → 姤四爻动。
    数过八者先以八递除（《卷一·卦以八除》"过八数即以八数递除"），
    如西林寺添勾占：林字十画 → 除八得二为兑卦。
    movings 可显式指定多动爻（默认单动）。
    """
    upper = _trigram_from_number(upper_num % 8)
    lower = _trigram_from_number(lower_num % 8)
    auto = _normalize((upper_num + lower_num + hour_num) % 6, 6)
    use_movings = _normalize_movings(movings if movings is not None else auto)
    return _build_chart(
        upper, lower, use_movings,
        upper_num=upper_num, lower_num=lower_num, hour_num=hour_num,
        # 成卦之数（数应迟速用，《老人有忧色占》"成卦之数中分而取其半"）
        total=upper_num + lower_num + hour_num,
    )


def chart_from_manual(upper: str, lower: str, movings: list[int]) -> dict:
    """手工指定上下经卦与动爻列表（多爻动/外部卦例校验用）。

    起卦不走数除，直接给卦；体用仍按动者为用分（verdicts.json#multi_move_rules）。
    """
    if upper not in BAGUA_LINES or lower not in BAGUA_LINES:
        raise ValueError(f"上下卦须是八卦名：{upper!r}/{lower!r}")
    return _build_chart(upper, lower, _normalize_movings(movings))


def chart_from_datetime(dt: datetime) -> dict:
    """公历时刻起卦：年数取年支序（立春定年，同 ganzhi_calendar）。"""
    gz = ganzhi_of(dt)
    year_branch = gz.year_ganzhi[1]
    year_num = _YEAR_BRANCH_ORDINAL[year_branch]
    lun = solar_to_lunar(dt.date())
    if lun is None:
        raise ValueError(f"{dt.date()} 超出农历表范围（1900-01-31 起 150 年）")
    hour_num = _HOUR_ORDINAL[gz.hour_ganzhi[1]]
    out = chart_from_numbers(year_num, lun["month"], lun["day"], hour_num)
    out["month_branch"] = gz.month_branch
    out["time"] = {
        "dt": dt.strftime("%Y-%m-%d %H:%M"),
        "ganzhi": gz.summary(),
        "year_branch": year_branch,
        "lunar_month": lun["month"],
        "lunar_month_name": lunar_month_name(lun["month"], lun["leap"]),
        "lunar_day": lun["day"],
        "hour_branch": gz.hour_ganzhi[1],
    }
    return out


def chart_from_lunar(year: int, month: int, day: int, hour_branch: str) -> dict:
    """农历年月日 + 时支起卦（观梅占原文式：辰年十二月十七申时）。

    月令（卦气旺衰用）按节气定月：由农历日期反查公历日期，
    再经 ganzhi_calendar 求当月支——梅花起卦取农历月日数，
    旺衰仍以实际节气月为准（两套月制各司其职）。
    """
    ygz = _ganzhi_year_of_lunar_year(year)
    year_num = _YEAR_BRANCH_ORDINAL[ygz[1]]
    hour_num = _HOUR_ORDINAL.get(hour_branch)
    if hour_num is None:
        raise ValueError(f"未知时支：{hour_branch}")
    out = chart_from_numbers(year_num, month, day, hour_num)
    solar = lunar_to_solar(year, month, day)
    if solar is not None:
        # 月令以节气定月（与 datetime 路径同口径），只取支字符，勿取三元组
        out["month_branch"] = ganzhi_of(
            datetime(solar.year, solar.month, solar.day, 12, 0)).month_branch
    else:
        out["month_branch"] = None
    out["time"] = {
        "lunar_year": year,
        "lunar_year_ganzhi": ygz,
        "lunar_month": month,
        "lunar_day": day,
        "hour_branch": hour_branch,
    }
    return out


def _ganzhi_year_of_lunar_year(year: int) -> str:
    """农历年 → 年干支（正月初一之后属该干支年；年底交立春前亦属该年）。

    农历年干支以正月初一为界，与 ganzhi_calendar 的立春定年略有出入；
    梅花起卦取年支数按通行法用农历年干支，此处按 (year - 4) % 60 直接给出，
    与六爻「立春定年界」属同一内核的不同口径，仅用于取年支序数。
    """
    idx = (year - 4) % 60
    stems = "甲乙丙丁戊己庚辛壬癸"
    branches = EARTHLY_BRANCHES
    return stems[idx % 10] + branches[idx % 12]


def chart(params: dict) -> dict:
    """统一入口：params 含 way("datetime"/"lunar"/"numbers"/"two_numbers"/"manual") 与对应字段。

    numbers / two_numbers / manual 可传 `movings`（动爻列表）覆盖自动单动，
    以支持两爻及以上动（多爻动规则见 data/verdicts.json#multi_move_rules）。
    numbers / two_numbers 方式没有真实时刻，月令必须由调用方显式传
    `month_branch`（地支字符）；不传则为 None，旺衰判"未定"，
    保证同一组数字在任何时刻都得到同一盘（可复现）。
    """
    way = params.get("way", "datetime")
    movings = params.get("movings")
    if movings is None and isinstance(params.get("moving"), (list, tuple)):
        movings = params["moving"]
    if way == "datetime":
        dt = params.get("datetime")
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        out = chart_from_datetime(dt)
    elif way == "lunar":
        out = chart_from_lunar(
            int(params["year"]), int(params["month"]), int(params["day"]),
            params.get("hour_branch", params.get("hour")),
        )
    elif way == "numbers":
        out = chart_from_numbers(int(params["year_num"]), int(params["month"]),
                                 int(params["day"]), int(params["hour_num"]),
                                 movings=movings)
        out["month_branch"] = _checked_month_branch(params.get("month_branch"))
    elif way == "two_numbers":
        out = chart_from_two_numbers(int(params["upper_num"]), int(params["lower_num"]),
                                     int(params.get("hour_num", 0)), movings=movings)
        out["month_branch"] = _checked_month_branch(params.get("month_branch"))
    elif way == "manual":
        out = chart_from_manual(str(params["upper"]), str(params["lower"]),
                                movings if movings is not None else params.get("moving"))
        out["month_branch"] = _checked_month_branch(params.get("month_branch"))
    else:
        raise ValueError(f"未知起卦方式：{way}")
    # datetime/lunar 路径若显式给了多动爻，重建体用（自动路径默认单动）
    if movings is not None and way in ("datetime", "lunar"):
        out = _build_chart(out["upper"], out["lower"], _normalize_movings(movings),
                           **{k: v for k, v in out.items()
                              if k not in {"upper", "lower", "moving", "movings",
                                           "moving_count", "multi_move", "body_use_rule",
                                           "hexagram", "body", "use", "body_element",
                                           "use_element", "interacting_lower",
                                           "interacting_upper", "changed_hexagram",
                                           "changed_trigram", "changed_trigrams",
                                           "changed_upper", "changed_lower",
                                           "body_changed_trigram", "use_changed_trigram",
                                           "lines", "changed_lines"}})
    out["question"] = params.get("question", "")
    out["topic"] = detect_topic(out["question"])
    out["way"] = way
    out["motion"] = params.get("motion", "立")   # 数应迟速：行/立/坐/卧（《占卜总诀》）
    return out


def _checked_month_branch(mb) -> str | None:
    """月令只认地支字符；传错类型（如 int 序号/三元组）立即报错而非静默失效。"""
    if mb is None:
        return None
    if mb not in EARTHLY_BRANCHES:
        raise ValueError(f"月令必须是地支字符（如 '寅'），收到：{mb!r}")
    return mb


if __name__ == "__main__":
    import argparse
    import json as _json
    import sys as _sys

    CORE = Path(__file__).resolve().parents[3] / "core"
    for _p in (str(Path(__file__).resolve().parent), str(CORE)):
        if _p not in _sys.path:
            _sys.path.insert(0, _p)
    from yishu_core.runtime import force_utf8_stdio  # noqa: E402
    force_utf8_stdio()

    ap = argparse.ArgumentParser(description="梅花易数起卦（chart 段）")
    ap.add_argument("--way", choices=["datetime", "lunar", "numbers", "two_numbers", "manual"],
                    default="datetime", help="起卦方式（缺省 datetime）")
    ap.add_argument("--datetime", help="datetime 方式：公历时刻 ISO 字符串")
    ap.add_argument("--year", type=int, help="lunar 方式：农历年")
    ap.add_argument("--month", type=int, help="lunar/numbers 方式：月数")
    ap.add_argument("--day", type=int, help="lunar/numbers 方式：日数")
    ap.add_argument("--hour-branch", help="lunar 方式：时支（如 酉）")
    ap.add_argument("--year-num", type=int, help="numbers 方式：年数")
    ap.add_argument("--hour-num", type=int, help="numbers 方式：时数")
    ap.add_argument("--upper-num", type=int, help="two_numbers 方式：上卦数")
    ap.add_argument("--lower-num", type=int, help="two_numbers 方式：下卦数")
    ap.add_argument("--upper", help="manual 方式：上经卦名（如 乾）")
    ap.add_argument("--lower", help="manual 方式：下经卦名（如 震）")
    ap.add_argument("--movings", help="动爻列表，逗号分隔（如 1,2 或 2,4,5）；缺省按起卦数取单动")
    ap.add_argument("--month-branch", help="numbers/two_numbers/manual 方式的月令地支（旺衰用）")
    ap.add_argument("--question", default="")
    ap.add_argument("--motion", default="立", help="数应迟速：行/立/坐/卧")
    ap.add_argument("--selfcheck", action="store_true", help="跑金标准自检")
    ap.add_argument("-o", "--out", type=Path, help="写出 chart JSON（缺省打印 stdout）")
    args = ap.parse_args()

    movings = None
    if args.movings:
        try:
            movings = [int(x) for x in args.movings.replace("，", ",").split(",") if x.strip()]
        except ValueError:
            ap.error(f"--movings 不是整数列表：{args.movings!r}")

    # 无任何起卦参数或显式 --selfcheck → 金标准自检；否则按 --way 装配起局参数
    no_input = (args.selfcheck or (args.way == "datetime" and not args.datetime))
    if no_input:
        params = None
    elif args.way == "datetime":
        params = {"way": "datetime", "datetime": args.datetime,
                  "question": args.question, "motion": args.motion, "movings": movings}
    elif args.way == "lunar":
        if None in (args.year, args.month, args.day) or not args.hour_branch:
            ap.error("--way lunar 需要 --year/--month/--day/--hour-branch")
        params = {"way": "lunar", "year": args.year, "month": args.month,
                  "day": args.day, "hour_branch": args.hour_branch,
                  "question": args.question, "motion": args.motion, "movings": movings}
    elif args.way == "numbers":
        if None in (args.year_num, args.month, args.day, args.hour_num):
            ap.error("--way numbers 需要 --year-num/--month/--day/--hour-num")
        params = {"way": "numbers", "year_num": args.year_num,
                  "month": args.month, "day": args.day, "hour_num": args.hour_num,
                  "month_branch": args.month_branch, "movings": movings,
                  "question": args.question, "motion": args.motion}
    elif args.way == "manual":
        if not args.upper or not args.lower or not movings:
            ap.error("--way manual 需要 --upper/--lower/--movings")
        params = {"way": "manual", "upper": args.upper, "lower": args.lower,
                  "movings": movings, "month_branch": args.month_branch,
                  "question": args.question, "motion": args.motion}
    else:
        if None in (args.upper_num, args.lower_num):
            ap.error("--way two_numbers 需要 --upper-num/--lower-num")
        params = {"way": "two_numbers", "upper_num": args.upper_num,
                  "lower_num": args.lower_num, "hour_num": args.hour_num or 0,
                  "month_branch": args.month_branch, "movings": movings,
                  "question": args.question, "motion": args.motion}

    if params is None:
        r = chart_from_numbers(5, 12, 17, 9)
        # 卦名为简称（与 core HEXAGRAM_TRIGRAMS、六爻 HEXAGRAMS 同一惯例：革=泽火革）
        assert r["hexagram"] == "革", r["hexagram"]
        assert r["moving"] == 1 and r["body"] == "兑" and r["use"] == "离", r
        assert r["interacting_upper"] == "乾" and r["interacting_lower"] == "巽", r
        assert r["changed_hexagram"] == "咸", r
        assert r["movings"] == [1] and r["multi_move"] is False, r
        m2 = chart_from_manual("乾", "震", [1, 2])
        assert m2["multi_move"] is True and m2["body"] == "乾" and m2["use"] == "震", m2
        assert m2["body_use_rule"] == "动尽下卦：上体下用", m2
        print("观梅占 chart 校验通过（含多爻动体用）")
        print(r["hexagram"], "动", r["moving"], "体", r["body"], "用", r["use"])
        raise SystemExit(0)

    out = chart(params)
    text = _json.dumps(out, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        print("起卦 →", args.out)
    else:
        print(text)
