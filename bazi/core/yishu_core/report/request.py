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
  * 字段白名单**由本模块执行**：`normalize_request` 收到白名单外的键、或收到
    "本学科不消费"的键，一律抛 ValueError 并列出该科可选项。静默忽略是本模块
    最危险的失效模式（旧实现里 `way=numbers`、`activity=开市` 会被无声收下，
    没有任何引擎阶段读它，而报告页头照样印出来——求测者以为它参与了推演）。
  * 每个请求字段都必须在 `FIELD_USAGE` 里声明**消费方式**：`argv`（真的进命令行，
    由 `chart_inputs`/`chart_argv` 接线）或 `display`（不进命令行，但必须在
    `DISPLAY_PURPOSE` 里写明用途）。收缩学科时没接线字段要从表里删，不许留成
    "看着像输入、其实没人读"的死字段——回归判据见 `tests/test_request_parity.py`
    （逐字段探针），改 `tools/check.py` 的 [1h] 门时应对齐同一判据。
  * 页头回显（`report_meta`）只列 `chart_inputs()` 的产物：凡页面上看得见的
    输入，一定真的进了 chart 段命令行；仅用于命名的字段带用途标注明示（铁律三）。
  * 各科起卦/起课方式走**白名单**（`LIUYAO_MODES`、`LIUYAO_ZI_HOUR_TYPES`），
    表外取值明确报错——不许"转发给 argparse 让它炸"，更不许静默忽略。
  * 只透传学科 argparse 真正认识的键，不猜。新增旗标前先跑该科
    `scripts/chart.py --help` 核对 choices 与参数名（逐字对齐，不转写）。
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

CST = timezone(timedelta(hours=8))

DISCIPLINES = ("liuyao", "ming")

DISC_TITLE = {
    "liuyao": "六爻纳甲",
    "ming": "四柱八字",
}

# 各科起卦/起课方式白名单（与学科 chart.py 的 argparse choices 逐字对齐）
LIUYAO_MODES = ("coin", "time", "number", "manual")
# 六爻 chart.py `--zi-hour-type` 的 choices（逐字对齐）
LIUYAO_ZI_HOUR_TYPES = ("early", "late")

# 各科的必填字段（用于早期报错，附人话提示）
REQUIRED = {
    "liuyao": (),
    "ming": ("datetime",),
}

FIELD_HINT = {
    "datetime": "出生/起算时间，格式 YYYY-MM-DD HH:MM",
    "gender": "性别：男 或 女",
}

# ── 字段宇宙（唯一真值源）─────────────────────────────────────────────────
# 请求字段白名单：本地 CLI（tools/report.py、cli/main.py）、深链短键
# （web/web.js 的 DEEPLINK_KEYS）、通道 B 的 extra JSON（tools/ci_request.py）
# 共用此集合——四处任一处出现本表没有的键，就是"死字段"复发的信号。
#
# 每个字段在这里声明自己的**消费方式**：
#   "argv"    必须真的出现在 chart_argv/analyze_argv/render_argv 的产出里
#             （由 chart_inputs 接线；tests/test_request_parity.py 逐字段探针实测）
#   "display" 不进命令行，但用途必须在 DISPLAY_PURPOSE 写明、并由 report_meta
#             带用途标注回显——不许看起来像判据输入
USAGE_ARGV = "argv"
USAGE_DISPLAY = "display"

FIELD_USAGE: dict[str, str] = {
    "discipline": USAGE_DISPLAY,       # 选科：决定走哪条分支，页头如实回显
    "question": USAGE_ARGV,            # 两科 chart.py 都收 --question
    "datetime": USAGE_ARGV,
    "gender": USAGE_ARGV,              # 仅 ming（真太阳时/大运顺逆）
    "mode": USAGE_ARGV,                # 仅 liuyao
    "numbers": USAGE_ARGV,             # 仅 liuyao（数字起卦）
    "yao": USAGE_ARGV,                 # 仅 liuyao（manual 爻值）
    "seed": USAGE_ARGV,                # 仅 liuyao（coin 可复现摇卦）
    "longitude": USAGE_ARGV,
    "hour": USAGE_ARGV,                # 仅 liuyao --hour（手动指定小时，覆盖 datetime）
    "distinguish_zi_hour": USAGE_ARGV,  # 仅 liuyao --distinguish-zi-hour（开关）
    "zi_hour_type": USAGE_ARGV,        # 仅 liuyao --zi-hour-type {early,late}
    "name": USAGE_DISPLAY,             # 只当产物文件主名，绝不进命令行
}

# 白名单由 FIELD_USAGE 派生：两处各存一份必然漂移（内核唯一真值源纪律）
REQUEST_FIELDS = tuple(FIELD_USAGE)

# 字段 → 消费它的学科。某科收到不消费的字段 = 会被静默丢弃 = 死字段，
# 因此按学科拒绝（报错并列出该科可选项），而不是收下后不转发。
FIELD_SCOPE: dict[str, tuple[str, ...]] = {
    "discipline": DISCIPLINES,
    "question": DISCIPLINES,
    "datetime": DISCIPLINES,
    "longitude": DISCIPLINES,
    "name": DISCIPLINES,
    "gender": ("ming",),
    "mode": ("liuyao",),
    "numbers": ("liuyao",),
    "yao": ("liuyao",),
    "seed": ("liuyao",),
    "hour": ("liuyao",),
    "distinguish_zi_hour": ("liuyao",),
    "zi_hour_type": ("liuyao",),
}

# display 类字段的页头口径：字段 → report_meta 里必须出现的用途标注片段。
# tests/test_request_parity.py 据此断言"回显必带用途"，防页头出现无口径字段。
NAMING_PURPOSE_NOTE = "仅用于产物文件命名，不参与任何推演"
DISPLAY_PURPOSE: dict[str, str] = {
    "discipline": "学科：",
    "name": NAMING_PURPOSE_NOTE,
}

# 页头中文标签（report_meta 唯一用得到；与 chart_inputs 的键一一对应）
FIELD_LABEL: dict[str, str] = {
    "question": "所问",
    "datetime": "起算/出生时间",
    "gender": "性别",
    "mode": "起卦方式",
    "numbers": "起卦数字",
    "yao": "爻值",
    "seed": "摇卦种子",
    "longitude": "东经",
    "hour": "指定小时",
    "distinguish_zi_hour": "区分早晚子时",
    "zi_hour_type": "子时口径",
}


# ── 基础归一化 ─────────────────────────────────────────────────────────────

def now_str() -> str:
    return datetime.now(CST).strftime("%Y-%m-%d %H:%M")


def split_ints(text, expect: int | None = None, field: str = "numbers") -> list[int]:
    try:
        vals = [int(x.strip()) for x in str(text).replace("，", ",").split(",") if x.strip()]
    except ValueError:
        raise ValueError(f"{field} 需要逗号分隔的整数，收到 {text!r}")
    if expect is not None and len(vals) != expect:
        raise ValueError(f"{field} 需要 {expect} 个整数，收到 {len(vals)} 个：{text!r}")
    return vals


def _one_of(value, choices: tuple[str, ...], field: str) -> str:
    """取值白名单：表外一律报错并列出可选，不猜、不静默改默认值。"""
    text = str(value).strip()
    if text not in choices:
        raise ValueError(f"{field} 只能是 {'/'.join(choices)}，收到 {value!r}")
    return text


_FLAG_TRUE = ("1", "true", "yes", "y", "on", "是")
_FLAG_FALSE = ("0", "false", "no", "n", "off", "否", "")


def _as_flag(value, field: str) -> bool:
    """开关字段归一化：接受 bool 与常见真假字符串，其余报错。

    JSON / GitHub 表单 / issue 正文三种来源给的值形态不同（true / "1" / "是" /
    "true"），归一化只在这一处做，chart_inputs 不再各自判真假。
    """
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in _FLAG_TRUE:
        return True
    if text in _FLAG_FALSE:
        return False
    raise ValueError(
        f"{field} 是开关字段，只能给真/假（1/0、true/false、是/否），收到 {value!r}")


def _norm_hour(value) -> str:
    """六爻 `--hour`：0..23 的整数小时（覆盖 datetime 的小时位）。"""
    try:
        hour = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"liuyao hour 需要 0..23 的整数，收到 {value!r}")
    if not 0 <= hour <= 23:
        raise ValueError(f"liuyao hour 需要 0..23 的整数，收到 {value!r}")
    return str(hour)


def _normalize_values(req: dict) -> dict:
    """按字段做取值级校验/归一化（白名单之外的第二道：值不合法也拒）。

    归一化写回 dict 的是"命令行实际会拿到的形态"，因此 normalize_request 的产物
    与 chart_argv 的入参同源；非法 mode 在这里就炸，不用等子进程。
    """
    out = dict(req)
    if out.get("mode") is not None:
        out["mode"] = _one_of(out["mode"], LIUYAO_MODES, "liuyao mode（起卦方式）")
    if out.get("zi_hour_type") is not None:
        out["zi_hour_type"] = _one_of(out["zi_hour_type"], LIUYAO_ZI_HOUR_TYPES,
                                      "liuyao zi_hour_type（子时口径）")
    if out.get("hour") is not None:
        out["hour"] = _norm_hour(out["hour"])
    if out.get("distinguish_zi_hour") is not None:
        out["distinguish_zi_hour"] = _as_flag(out["distinguish_zi_hour"],
                                              "liuyao distinguish_zi_hour")
    return out


def fields_for(discipline: str) -> tuple[str, ...]:
    """本学科请求可带的字段（报错时列"可选"；也是外层 CLI 生成 help 的依据）。"""
    return tuple(f for f in REQUEST_FIELDS if discipline in FIELD_SCOPE.get(f, ()))


def normalize_request(req: dict) -> dict:
    """校验并补全请求；返回新 dict（不改入参）。

    拒绝三类输入，都抛 ValueError 并列出该科可选项：
      * 缺必填项（`REQUIRED`）；
      * 白名单外的字段（`REQUEST_FIELDS`）——**不静默忽略**；
      * 本学科不消费的字段（`FIELD_SCOPE`，如给六爻传 gender）——收下就等于
        让读者以为它参与了推演，同样拒绝。
    """
    if not isinstance(req, dict):
        raise ValueError("请求必须是 JSON 对象")
    out = {k: v for k, v in req.items() if v not in (None, "")}
    d = out.get("discipline")
    if d not in DISCIPLINES:
        raise ValueError(f"未知/未启用学科：{d!r}，可选：{'、'.join(DISCIPLINES)}")
    available = "、".join(fields_for(d))
    unknown = sorted(k for k in out if k not in REQUEST_FIELDS)
    if unknown:
        raise ValueError(
            f"请求含未知字段：{'、'.join(unknown)}——没有任何引擎阶段会读它们，"
            f"收下只会让读者误以为它参与了推演。{DISC_TITLE[d]} 可用字段：{available}")
    off_scope = sorted(k for k in out if d not in FIELD_SCOPE.get(k, ()))
    if off_scope:
        detail = "、".join(
            f"{k}（仅 {'、'.join(DISC_TITLE[x] for x in FIELD_SCOPE[k])} 消费）"
            for k in off_scope)
        raise ValueError(
            f"{DISC_TITLE[d]} 不消费这些字段：{detail}。请删除它们或改投对应学科；"
            f"{DISC_TITLE[d]} 可用字段：{available}")
    for key in REQUIRED[d]:
        if not out.get(key):
            raise ValueError(f"{DISC_TITLE[d]} 需要 {key}（{FIELD_HINT.get(key, '')}）")
    if out.get("gender") and out["gender"] not in ("男", "女"):
        raise ValueError(f"gender 只能是 男 或 女，收到 {out['gender']!r}")
    return _normalize_values(out)


# ── 三个阶段各自的命令行 ───────────────────────────────────────────────────

def chart_inputs(req: dict) -> dict:
    """本次请求**真正进入 chart 段命令行**的输入：字段 → 实际值。

    唯一判据处：`chart_argv` 据此拼旗标，`report_meta` 据此回显页头。
    两者因此同源——页头看得见每一项，都真的被引擎收到了；没被转发的字段
    （如已收缩学科的 way/activity/date/hour_branch/direction/up/mid/down）
    既进不了命令行，也不会出现在页面上。
    """
    d = req["discipline"]
    ins: dict[str, object] = {}

    if d == "liuyao":
        dt = req.get("datetime", "")
        mode = req.get("mode") or ("time" if dt else "coin")
        mode = _one_of(mode, LIUYAO_MODES, "liuyao mode（起卦方式）")
        ins["mode"] = mode
        ins["question"] = req.get("question", "")
        if dt:
            ins["datetime"] = dt
        if req.get("numbers"):
            ins["numbers"] = str(req["numbers"])
        if mode == "manual":
            # 手动录入爻值（6=老阴动 7=少阳静 8=少阴静 9=老阳动），如 "7,8,9,7,6,8"。
            # 用途：把古籍案例或线下手摇结果照原样录进来复核，是"盲评"的入口。
            if not req.get("yao"):
                raise ValueError('liuyao mode=manual 需要 yao（6 个爻值，如 "7,8,9,7,6,8"）')
            vals = split_ints(req["yao"], 6, "liuyao yao")
            bad = [v for v in vals if v not in (6, 7, 8, 9)]
            if bad:
                raise ValueError(f"liuyao yao 只能是 6/7/8/9，收到 {bad}")
            ins["yao"] = ",".join(str(v) for v in vals)
        if mode == "coin" and req.get("seed") is not None:
            ins["seed"] = str(req["seed"])
        if req.get("longitude") is not None:
            ins["longitude"] = str(req["longitude"])
        if req.get("hour") is not None:
            ins["hour"] = _norm_hour(req["hour"])
        if _as_flag(req.get("distinguish_zi_hour", False), "liuyao distinguish_zi_hour"):
            ins["distinguish_zi_hour"] = "是"
        if req.get("zi_hour_type"):
            ins["zi_hour_type"] = _one_of(req["zi_hour_type"], LIUYAO_ZI_HOUR_TYPES,
                                          "liuyao zi_hour_type（子时口径）")

    elif d == "ming":
        dt = req.get("datetime", "")
        if not dt:
            raise ValueError(f"{DISC_TITLE[d]} 需要 datetime（{FIELD_HINT['datetime']}）")
        ins["datetime"] = dt
        if req.get("gender"):
            ins["gender"] = req["gender"]
        if req.get("longitude") is not None:
            ins["longitude"] = str(req["longitude"])
        if req.get("question"):
            ins["question"] = req["question"]

    return ins


def chart_argv(req: dict, program: str, out_path: str) -> list[str]:
    """chart 段命令行（旗标名与该科 chart.py 的 argparse 逐字对齐）。"""
    d = req["discipline"]
    ins = chart_inputs(req)
    argv = [program]

    if d == "liuyao":
        argv += ["--mode", str(ins["mode"]), "--question", str(ins["question"])]
        pairs = (("--datetime", "datetime"), ("--numbers", "numbers"), ("--yao", "yao"),
                 ("--seed", "seed"), ("--longitude", "longitude"), ("--hour", "hour"),
                 ("--zi-hour-type", "zi_hour_type"))
        for flag, key in pairs:
            if key in ins:
                argv += [flag, str(ins[key])]
        if "distinguish_zi_hour" in ins:
            argv.append("--distinguish-zi-hour")

    elif d == "ming":
        argv += ["--datetime", str(ins["datetime"])]
        if "gender" in ins:
            argv += ["--gender", str(ins["gender"])]
        if "longitude" in ins:
            argv += ["--longitude", str(ins["longitude"])]
        if "question" in ins:
            argv += ["--question", str(ins["question"])]

    argv += ["-o", out_path]
    return argv


def analyze_argv(req: dict, program: str, chart_path: str, out_path: str) -> list[str]:
    """analyze 段命令行：两科同形（chart.json → analyze.json）。"""
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
    if d == "ming":
        return f"{title} · 命盘分析"
    return f"{title} · {q}" if q else title


def report_meta(req: dict, *, runtime: str = "") -> str:
    """页头小字：学科 + **真正进入推演的输入** + 运行环境 + 生成时间。

    输入项一律取自 `chart_inputs()`（与 chart_argv 同一判据处），所以：
      * 白名单里没被转发的字段不可能出现在页头（旧实现把 `date`/`activity`
        印成「日期 ｜ 事类」却没有任何引擎收到它，是铁律三的违规）；
      * 仅用于命名的 `name` 显式带用途标注，不许看起来像判据输入。
    """
    d = req["discipline"]
    bits = [f"学科：{DISC_TITLE[d]}（{d}）"]
    title = report_title(req)
    for key, value in chart_inputs(req).items():
        text = str(value)
        if not text:
            continue  # 空值不占页头一位（如未填所问之事）
        if key == "question" and text in title:
            continue  # 标题里已经写着所问之事，页头不重复
        bits.append(f"{FIELD_LABEL.get(key, key)}：{text}")
    if req.get("name"):
        bits.append(f"命名：{req['name']}（{NAMING_PURPOSE_NOTE}）")
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
