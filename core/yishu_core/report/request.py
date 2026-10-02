# -*- coding: utf-8 -*-
"""报告请求 → 四段命令行参数的**唯一映射层**。

为什么放在内核里：同一条映射现在有三个消费方——
  * `tools/report.py`（本机与 CI：起子进程分步跑）
  * `web/engine_runtime.py`（浏览器 Pyodide：无 subprocess，用 runpy 同进程跑）
  * 将来任何新的执行器（本地服务 / 别的宿主）
映射若各写一份，必然出现"本地对的、网页端错"（历史教训：同一张规则表在三个
文件里各存一份且取值不一致）。所以映射只此一份，执行器只负责"怎么跑"。

本模块**只做纯计算**：不读文件、不起进程、不碰网络、不 import 任何学科代码。

设计纪律（缺陷防复发）：
  * 各科起卦/起课方式走**白名单**，表外取值明确报错——不许"转发给 argparse 让它炸"，
    更不许静默忽略（旧实现里 xiaoliuren `way=numbers` 会被无声地按 datetime 出课，
    求测者拿到的是另一种方式的盘而报告不会说）。
  * 日期一律归一化为 ISO；`2026/09/30`、`2026.9.30`、`20260930` 都吃。
  * 只透传学科 argparse 真正认识的键，不猜。
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

CST = timezone(timedelta(hours=8))

DISCIPLINES = ("liuyao", "ming", "ziwei", "meihua", "xiaoliuren", "zeji", "liuren", "lingqi")

DISC_TITLE = {
    "liuyao": "六爻纳甲",
    "ming": "四柱八字",
    "ziwei": "紫微斗数",
    "meihua": "梅花易数",
    "xiaoliuren": "小六壬",
    "zeji": "择吉",
    "liuren": "大六壬",
    "lingqi": "灵棋经",
}

# 各科起卦/起课方式白名单（与学科 chart.py 的 argparse choices 逐字对齐）
LIUYAO_MODES = ("coin", "time", "number", "manual")
MEIHUA_WAYS = ("datetime", "lunar", "numbers", "two_numbers", "manual")
XIAOLIUREN_WAYS = ("datetime", "lunar", "month_day_hour", "numbers")

# 各科的必填字段（用于早期报错，附人话提示）
REQUIRED = {
    "liuyao": (),
    "ming": ("datetime",),
    "ziwei": ("datetime",),
    "meihua": (),
    "xiaoliuren": (),
    "zeji": (),
    "liuren": ("datetime",),
    "lingqi": (),
}

FIELD_HINT = {
    "datetime": "出生/起算时间，格式 YYYY-MM-DD HH:MM",
    "date": "用事日期，格式 YYYY-MM-DD",
    "gender": "性别：男 或 女",
}

# 请求字段白名单（唯一真值源）：本地 CLI 与深链短键（web/web.js 的 DEEPLINK_KEYS）
# 共用此集合。短键表只存在于 JS 侧、不受输入协议指纹覆盖，[1h] 门把它锁在此集合内，
# 防「短键悄悄指向一个没有任何 argv 会读的死字段」——那会让本地与网页端行为不一致且零报警。
REQUEST_FIELDS = (
    "discipline", "question", "datetime", "gender", "mode", "way", "numbers",
    "yao", "date", "activity", "hour_branch", "direction", "longitude", "name",
    "up", "mid", "down", "seed",
)


# ── 基础归一化 ─────────────────────────────────────────────────────────────

def now_str() -> str:
    return datetime.now(CST).strftime("%Y-%m-%d %H:%M")


def norm_iso(dt: str) -> str:
    """'YYYY-MM-DD HH:MM' → 'YYYY-MM-DDTHH:MM:SS'（梅花/小六壬 datetime 方式用）。"""
    text = str(dt).strip().replace(" ", "T")
    if len(text) == 16:
        text += ":00"
    return text


def norm_date(value) -> str:
    """日期归一化为 ISO：`2026/09/30`、`2026.9.30`、`20260930` 都吃。"""
    text = str(value).strip().replace("/", "-").replace(".", "-")
    if len(text) == 8 and text.isdigit():
        text = f"{text[:4]}-{text[4:6]}-{text[6:]}"
    parts = text.split("-")
    if len(parts) == 3:
        try:
            text = "%04d-%02d-%02d" % (int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            raise ValueError(f"无法解析日期：{value!r}（需要 YYYY-MM-DD）")
    try:
        date.fromisoformat(text)
    except ValueError:
        raise ValueError(f"无法解析日期：{value!r}（需要 YYYY-MM-DD）")
    return text


def split_ints(text, expect: int | None = None, field: str = "numbers") -> list[int]:
    try:
        vals = [int(x.strip()) for x in str(text).replace("，", ",").split(",") if x.strip()]
    except ValueError:
        raise ValueError(f"{field} 需要逗号分隔的整数，收到 {text!r}")
    if expect is not None and len(vals) != expect:
        raise ValueError(f"{field} 需要 {expect} 个整数，收到 {len(vals)} 个：{text!r}")
    return vals


def normalize_request(req: dict) -> dict:
    """校验并补全请求；返回新 dict（不改入参）。表外/缺项一律抛 ValueError。"""
    if not isinstance(req, dict):
        raise ValueError("请求必须是 JSON 对象")
    out = {k: v for k, v in req.items() if v not in (None, "")}
    d = out.get("discipline")
    if d not in DISCIPLINES:
        raise ValueError(f"未知/未启用学科：{d!r}，可选：{'、'.join(DISCIPLINES)}")
    for key in REQUIRED[d]:
        if not out.get(key):
            raise ValueError(f"{DISC_TITLE[d]} 需要 {key}（{FIELD_HINT.get(key, '')}）")
    if out.get("gender") and out["gender"] not in ("男", "女"):
        raise ValueError(f"gender 只能是 男 或 女，收到 {out['gender']!r}")
    return out


# ── 三个阶段各自的命令行 ───────────────────────────────────────────────────

def chart_argv(req: dict, program: str, out_path: str) -> list[str]:
    """chart 段命令行。program 为学科 chart.py 的路径（由调用方按宿主环境给出）。"""
    d = req["discipline"]
    q = req.get("question", "")
    dt = req.get("datetime", "")
    argv = [program]

    if d == "lingqi":
        # 三部掷数缺一即无课——结构性澄清门禁（0 为合法面数，只拦"未给"）
        vals = {}
        for k, label in (("up", "上"), ("mid", "中"), ("down", "下")):
            v = req.get(k)
            if v is None:
                raise ValueError(
                    f"lingqi（灵棋经）需要 {k}（{label}部掷面数 0..4）：十二棋分三部，"
                    "三部掷数缺一不可；请向求测者确认掷棋结果后再试")
            if not isinstance(v, int) or not 0 <= v <= 4:
                raise ValueError(f"lingqi {k}（{label}部）必须是 0..4 的整数，收到 {v!r}")
            vals[k] = v
        argv += ["--up", str(vals["up"]), "--mid", str(vals["mid"]),
                 "--down", str(vals["down"])]
        if req.get("question"):
            argv += ["--question", req["question"]]
    if d == "liuren":
        # 六壬起课=月将加时，无时刻即无课——结构性缺参必须报错并给出澄清话术，
        # 不允许 AI 脑补一个时刻开算（AGENTS.md 铁律一）
        if not dt:
            raise ValueError(
                "liuren（大六壬）需要 datetime（YYYY-MM-DD HH:MM）：起课以月将加时，"
                "无时刻不可起课；请向求测者确认起课的公历时刻后再试")
        argv += ["--datetime", dt]
        if q:
            argv += ["--question", q]

    if d == "liuyao":
        mode = req.get("mode") or ("time" if dt else "coin")
        if mode not in LIUYAO_MODES:
            raise ValueError(
                f"liuyao 起卦方式 mode 只能是 {'/'.join(LIUYAO_MODES)}，收到 {mode!r}")
        argv += ["--mode", mode, "--question", q]
        if dt:
            argv += ["--datetime", dt]
        if req.get("numbers"):
            argv += ["--numbers", req["numbers"]]
        if mode == "manual":
            # 手动录入爻值（6=老阴动 7=少阳静 8=少阴静 9=老阳动），如 "7,8,9,7,6,8"。
            # 用途：把古籍案例或线下手摇结果照原样录进来复核，是"盲评"的入口。
            if not req.get("yao"):
                raise ValueError('liuyao mode=manual 需要 yao（6 个爻值，如 "7,8,9,7,6,8"）')
            vals = split_ints(req["yao"], 6, "liuyao yao")
            bad = [v for v in vals if v not in (6, 7, 8, 9)]
            if bad:
                raise ValueError(f"liuyao yao 只能是 6/7/8/9，收到 {bad}")
            argv += ["--yao", ",".join(str(v) for v in vals)]
        if mode == "coin" and req.get("seed") is not None:
            argv += ["--seed", str(req["seed"])]
        if req.get("longitude") is not None:
            argv += ["--longitude", str(req["longitude"])]

    elif d in ("ming", "ziwei"):
        argv += ["--datetime", dt]
        if req.get("gender"):
            argv += ["--gender", req["gender"]]
        if req.get("longitude") is not None:
            argv += ["--longitude", str(req["longitude"])]
        if d == "ming" and q:
            argv += ["--question", q]

    elif d == "meihua":
        way = req.get("way") or ("numbers" if req.get("numbers") else "datetime")
        if way not in MEIHUA_WAYS:
            raise ValueError(
                f"meihua 起卦方式 way 只能是 {'/'.join(MEIHUA_WAYS)}，收到 {way!r}")
        argv += ["--way", way]
        if way == "datetime":
            argv += ["--datetime", norm_iso(dt) if dt else norm_iso(now_str())]
        elif way == "numbers":
            # 梅花以数起卦：上卦=(年数+月数+日数) mod 8，下卦再+时数。
            # numbers 按"年数,月数,日数"三数解释（与学科
            # chart_from_numbers(year_num, month, day, hour_num) 同序）。
            a, b, c = split_ints(req.get("numbers", ""), 3, "meihua numbers")
            argv += ["--year-num", str(a), "--month", str(b), "--day", str(c),
                     "--hour-num", "0"]
        if q:
            argv += ["--question", q]

    elif d == "xiaoliuren":
        way = req.get("way") or ("numbers" if req.get("numbers") else "datetime")
        if way not in XIAOLIUREN_WAYS:
            raise ValueError(
                f"xiaoliuren 起课方式 way 只能是 {'/'.join(XIAOLIUREN_WAYS)}，收到 {way!r}")
        argv += ["--way", way]
        if way == "datetime":
            argv += ["--datetime", norm_iso(dt) if dt else norm_iso(now_str())]
        elif way == "numbers":
            if not req.get("numbers"):
                raise ValueError("xiaoliuren way=numbers 需要 numbers（如 7,7,2）")
            argv += ["--numbers", req["numbers"]]
        if q:
            argv += ["--question", q]
        if req.get("activity"):
            argv += ["--topic", req["activity"]]
        if req.get("hour_branch"):
            argv += ["--hour-branch", req["hour_branch"]]
        if req.get("direction"):
            argv += ["--direction", req["direction"]]

    elif d == "zeji":
        argv += ["--date", norm_date(req.get("date") or now_str().split(" ")[0])]
        if req.get("activity"):
            argv += ["--activity", req["activity"]]
        if q:
            argv += ["--question", q]
        if req.get("hour_branch"):
            argv += ["--hour-branch", req["hour_branch"]]

    argv += ["-o", out_path]
    return argv


def analyze_argv(req: dict, program: str, chart_path: str, out_path: str) -> list[str]:
    """analyze 段命令行：八科同形（chart.json → analyze.json）。"""
    return [program, chart_path, "-o", out_path]


def render_argv(req: dict, program: str, analyze_path: str, out_path: str) -> list[str]:
    """render 段命令行。六爻的 render.py 多一个 `-f md`（缺省即 md，显式给更稳）。"""
    argv = [program, analyze_path]
    if req.get("discipline") == "liuyao":
        argv += ["-f", "md"]
    return argv + ["-o", out_path]


def report_title(req: dict) -> str:
    """报告主标题（页头与 HTML <title>）。"""
    d = req["discipline"]
    q = req.get("question", "")
    title = DISC_TITLE[d]
    if d in ("ming", "ziwei"):
        return f"{title} · 命盘分析"
    return f"{title} · {q}" if q else title


def report_meta(req: dict, *, runtime: str = "") -> str:
    """页头小字：学科、起算/出生、性别、日期、运行环境、生成时间。"""
    d = req["discipline"]
    bits = [f"学科：{DISC_TITLE[d]}（{d}）"]
    if req.get("datetime"):
        bits.append(f"起算/出生：{req['datetime']}")
    if req.get("gender"):
        bits.append(f"性别：{req['gender']}")
    if req.get("date"):
        bits.append(f"日期：{req['date']}")
    if req.get("activity"):
        bits.append(f"事类：{req['activity']}")
    if runtime:
        bits.append(f"运行环境：{runtime}")
    bits.append(f"生成：{now_str()}")
    return "　｜　".join(bits)


# 口径声明唯一真值源（铁律三）：HTML 页脚与 issue 回评都用它，禁止各处另写副本
FOOTER_TEXT = (
    "本报告由 Yi 机械排盘与规则库生成；文中分数为古籍案例对齐分（非现实命中率）。"
    "凶吉均为条件化倾向，而非注定结论；医疗、法律、投资及重大人生决策，请以专业意见为准。"
)
REPORT_FOOTER = FOOTER_TEXT.replace("。凶吉", "。<br>凶吉", 1)

# 反馈回路尾注（SYS-REVIEW #6）：本地 CLI / 通道 B / 通道 A 三宿主在同一逻辑点
# 追加到 MD 尾部；通道 B 的 issue 回评由 ci_deliver 另行附带引导句。
MD_FEEDBACK_NOTE = (
    "\n---\n\n"
    "> 结果如何？占问事件的现实反馈可回填本仓（`synthesis record-outcome`），"
    "或在触发报告的 issue 下回复；反馈进入应期/效度统计。"
    "反馈 n=0 时，一切效度讨论无从谈起。\n"
)
