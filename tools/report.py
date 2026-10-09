# -*- coding: utf-8 -*-
"""Yi 统一报告运行器：一条命令把任一学科端到端跑出 Markdown + HTML。

  python tools/report.py --discipline liuyao --question "占买房何时有结果" \
      --datetime "2026-09-30 10:30" --outdir reports
  python tools/report.py --request request.json --outdir reports

request.json 形如：
  {"discipline": "ming", "datetime": "1990-05-20 10:30", "gender": "男",
   "question": "命局分析"}

字段宇宙只有一份：内核 `yishu_core.report.request.REQUEST_FIELDS`
（两科现收：discipline/question/datetime/gender/mode/numbers/yao/seed/longitude/
hour/distinguish_zi_hour/zi_hour_type/name）。**表外字段与本科不消费的字段直接报错**
（退出码 2），不再静默忽略——已删学科遗留的 way/activity/date/hour_branch/direction/
up/mid/down 一律拒，附可选字段清单。命令行只暴露这些真字段。

流程（四段契约，全部子进程跑学科脚本，机械运算不经过本脚本心算）：
  chart.py → analyze.py → render.py(出 Markdown) → core 报告 kit 出统一 HTML。

完成后在 stdout 末行打印一行 JSON：{"md": "...", "html": "...", "discipline": ...}，
供 GitHub Actions / 网页 AI 取回。零第三方依赖，可在干净 runner 上直接运行。

**请求 → 命令行参数的映射不在本文件**，在内核 `yishu_core.report.request`：
本机/CI 用子进程跑，浏览器 Pyodide 用同进程 runpy 跑，两边共用同一份映射，
避免"本地对的、网页端错"。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core"
DISC = ROOT / "disciplines"
sys.path.insert(0, str(CORE))

from yishu_core.report import (  # noqa: E402
    DISCIPLINES,
    DISC_TITLE,
    MD_FEEDBACK_NOTE,
    REPORT_FOOTER,
    analyze_argv,
    chart_argv,
    normalize_request,
    render_argv,
    report_meta,
    report_title,
)
from yishu_core.report.request import (  # noqa: E402
    LIUYAO_ZI_HOUR_TYPES,
    fields_for,
)
from yishu_core.report.html import report_page_from_markdown, write_html  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

CST = timezone(timedelta(hours=8))

# 运行环境标签：进报告页头，便于事后分辨这份报告是哪条链路出的
RUNTIME_LABEL = "本机/CI 子进程"


def _env() -> dict:
    env = dict(__import__("os").environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def _run(argv: list[str]) -> None:
    """跑子进程，失败即抛错（退出码非 0）。argv 首项是脚本路径，这里补解释器。"""
    proc = subprocess.run([sys.executable, *argv], env=_env(), capture_output=True,
                          text=True, encoding="utf-8")
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout or "")
        sys.stderr.write(proc.stderr or "")
        raise RuntimeError(f"命令失败（exit {proc.returncode}）：{' '.join(argv)}")


def build_report(req: dict, outdir: Path) -> dict:
    """端到端出报告，返回 {discipline, md, html}（值为落盘路径）。"""
    req = normalize_request(req)
    d = req["discipline"]

    outdir.mkdir(parents=True, exist_ok=True)
    stem = req.get("name") or f"{d}-{datetime.now(CST).strftime('%Y%m%d-%H%M%S')}"
    chart_p = outdir / f"{stem}.chart.json"
    analyze_p = outdir / f"{stem}.analyze.json"
    md_p = outdir / f"{stem}.md"
    html_p = outdir / f"{stem}.html"

    scripts = DISC / d / "scripts"
    # 1) chart（纯机械排盘）
    _run(chart_argv(req, str(scripts / "chart.py"), str(chart_p)))
    # 2) analyze（规则推演）
    _run(analyze_argv(req, str(scripts / "analyze.py"), str(chart_p), str(analyze_p)))
    # 3) render → Markdown
    _run(render_argv(req, str(scripts / "render.py"), str(analyze_p), str(md_p)))

    # 4) Markdown → 统一 HTML（尾部追加反馈引导；落盘 md 同步，通道 B 留档同文）
    md_text = md_p.read_text(encoding="utf-8") + MD_FEEDBACK_NOTE
    md_p.write_text(md_text, encoding="utf-8")
    html = report_page_from_markdown(
        title=report_title(req), markdown=md_text,
        meta=report_meta(req, runtime=RUNTIME_LABEL), footer=REPORT_FOOTER,
    )
    write_html(html, html_p)

    return {"discipline": d, "md": str(md_p), "html": str(html_p),
            "title": report_title(req)}


def _request_from_args(args) -> dict:
    if args.request:
        req = json.loads(args.request.read_text(encoding="utf-8-sig"))
        if args.name and not req.get("name"):
            req["name"] = args.name
        return req
    if not args.discipline:
        raise SystemExit("需要 --discipline（或 --request request.json）")
    return {k: v for k, v in dict(
        discipline=args.discipline, question=args.question, datetime=args.datetime,
        gender=args.gender, mode=args.mode, numbers=args.numbers,
        yao=args.yao, longitude=args.longitude, name=args.name or None,
        hour=args.hour, distinguish_zi_hour=args.distinguish_zi_hour,
        zi_hour_type=args.zi_hour_type, seed=args.seed,
    ).items() if v is not None and v != ""}


def main() -> int:
    force_utf8_stdio()
    # 字段宇宙的唯一真值源是内核；这里的每个 flag 都必须落进 REQUEST_FIELDS，
    # 否则 check.py 的结构门与 tests/test_request_parity.py 的探针会红
    # （历史缺陷：--way/--date/--activity/--hour-branch/--direction/--up/--mid/--down
    # 兜售已删学科的死字段，收了却没有任何引擎阶段读它）。
    ap = argparse.ArgumentParser(
        description="Yi 统一报告运行器（MD+HTML）；表外/本科不消费的字段直接报错",
        epilog="六爻可用字段：" + "、".join(fields_for("liuyao"))
               + "\n四柱八字可用字段：" + "、".join(fields_for("ming")),
    )
    ap.add_argument("--request", type=Path, help="请求 JSON 文件")
    ap.add_argument("--discipline", choices=DISCIPLINES)
    ap.add_argument("--question", default="")
    ap.add_argument("--datetime", default="", help='起算/出生时间 "YYYY-MM-DD HH:MM"')
    ap.add_argument("--gender", choices=["男", "女"], help="四柱八字：性别")
    ap.add_argument("--mode", help="六爻：起卦方式 coin/time/number/manual")
    ap.add_argument("--numbers", default="", help="六爻：数字起卦 \"a,b,c\"")
    ap.add_argument("--yao", default="", help='六爻 mode=manual：6 个爻值，如 "7,8,9,7,6,8"')
    ap.add_argument("--hour", type=int, help="六爻：手动指定小时 0..23（覆盖 --datetime）")
    ap.add_argument("--distinguish-zi-hour", dest="distinguish_zi_hour",
                    action="store_true", default=None,
                    help="六爻：启用早晚子时区分（开关，不带值）")
    ap.add_argument("--zi-hour-type", dest="zi_hour_type", choices=list(LIUYAO_ZI_HOUR_TYPES),
                    help="六爻：手动指定子时类型（优先级高于自动判断）")
    ap.add_argument("--longitude", type=float, help="东经（真太阳时校正）")
    ap.add_argument("--seed", type=int, help="六爻 coin：随机种子（可复现摇卦）")
    ap.add_argument("--name", default="",
                    help="产物文件主名（仅命名用途，不参与推演；缺省带时间戳）")
    ap.add_argument("--outdir", type=Path, default=Path("reports"))
    ap.add_argument("--result-json", type=Path, default=None,
                    help="额外把结果（含 MD/HTML 全文）写成一个 JSON 文件")
    args = ap.parse_args()

    try:
        req = _request_from_args(args)
        result = build_report(req, args.outdir)
    except ValueError as exc:
        # 请求不合法（表外字段/缺项/取值越界）：报错退非 0，不猜、不改方式
        print(f"请求被拒绝：{exc}", file=sys.stderr)
        return 2

    payload = dict(result)
    payload["request"] = normalize_request(req)
    payload["md_text"] = Path(result["md"]).read_text(encoding="utf-8")
    payload["html_text"] = Path(result["html"]).read_text(encoding="utf-8")
    payload["generated"] = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S%z")
    if args.result_json:
        args.result_json.parent.mkdir(parents=True, exist_ok=True)
        args.result_json.write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    print("报告已生成：")
    print("  MD:   " + result["md"])
    print("  HTML: " + result["html"])
    print("RESULT_JSON " + json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
