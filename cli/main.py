# -*- coding: utf-8 -*-
"""易 · 统一命令行入口：yi <discipline> <command> [options]

Usage:
    yi <discipline> <command> [options]
    yi execute --discipline <disc> --question <q> [options]

Disciplines:
    liuyao       六爻纳甲      commands: cast chart analyze narrate render
    ming         命理四柱      commands: chart analyze narrate render
    meihua       梅花易数      commands: cast chart analyze narrate render
    xiaoliuren   小六壬        commands: cast analyze narrate render
    zeji         择吉          commands: chart analyze narrate render
    ziwei        紫微斗数      commands: chart analyze narrate render
    liuren       大六壬        commands: chart analyze narrate render
    lingqi       灵棋经        commands: chart analyze narrate render

统一 Runtime 入口（推荐）:
    yi execute --discipline liuyao --question "占买房子何时有结果"
    yi execute --discipline ming --question "命盘" --datetime "1990-05-20 10:30" --gender 男

分步命令（精细调试）:
    yi liuyao cast "占买房子何时有结果"
    yi liuyao chart --mode coin
    yi liuyao analyze chart.json
    yi liuyao narrate analyze.json
    yi liuyao render analyze.json
    yi ming chart --datetime "1990-05-20 10:30" --gender 男
    yi ming analyze chart.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# 仓库根 & 学科目录（从本文件位置向上两层即为仓库根）
REPO_ROOT = Path(__file__).resolve().parents[1]
DISCIPLINES_DIR = REPO_ROOT / "disciplines"
CORE_DIR = REPO_ROOT / "core"

# 确保能 import yishu_core
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

# ── 学科命令注册表 ────────────────────────────────────────────────────────
# discipline → { command: (相对路径, 帮助文本) }
# 相对路径以 disciplines/ 为基准
DISCIPLINE_COMMANDS: dict[str, dict[str, tuple[str, str]]] = {
    "liuyao": {
        "cast":     ("liuyao/scripts/yi_liuyao.py", "一键占算（Runtime: chart→analyze→render→报告）"),
        "chart":    ("liuyao/scripts/chart.py",     "起卦（纯机械排盘）"),
        "analyze":  ("liuyao/scripts/analyze.py",   "规则推演（盘面→因子+吉凶）"),
        "narrate":  ("liuyao/scripts/narrate.py",   "人话解读"),
        "render":   ("liuyao/scripts/render.py",    "渲染报告"),
    },
    "ming": {
        "chart":    ("ming/scripts/chart.py",       "出生排盘（四柱+机械因子）"),
        "analyze":  ("ming/scripts/analyze.py",     "命局推演"),
        "narrate":  ("ming/scripts/narrate.py",     "命盘解读"),
        "render":   ("ming/scripts/render.py",      "渲染报告"),
    },
    "meihua": {
        "cast":     ("meihua/scripts/chart.py",     "一键起卦"),
        "chart":    ("meihua/scripts/chart.py",     "起卦"),
        "analyze":  ("meihua/scripts/analyze.py",   "体用生克推演"),
        "narrate":  ("meihua/scripts/narrate.py",   "人话解读"),
        "render":   ("meihua/scripts/render.py",    "渲染报告"),
    },
    "xiaoliuren": {
        "cast":     ("xiaoliuren/scripts/chart.py", "一键起课"),
        "analyze":  ("xiaoliuren/scripts/analyze.py", "推演"),
        "narrate":  ("xiaoliuren/scripts/narrate.py", "人话解读"),
        "render":   ("xiaoliuren/scripts/render.py", "渲染报告"),
    },
    "zeji": {
        "chart":    ("zeji/scripts/chart.py",       "择日起局"),
        "analyze":  ("zeji/scripts/analyze.py",     "神煞/建除推演"),
        "narrate":  ("zeji/scripts/narrate.py",     "人话解读"),
        "render":   ("zeji/scripts/render.py",      "渲染报告"),
    },
    "ziwei": {
        "chart":    ("ziwei/scripts/chart.py",      "斗数排盘（纯机械）"),
        "analyze":  ("ziwei/scripts/analyze.py",    "格局/四化/大限推演"),
        "narrate":  ("ziwei/scripts/narrate.py",    "命盘因子说明"),
        "render":   ("ziwei/scripts/render.py",     "命盘报告（Markdown/HTML）"),
    },
    "liuren": {
        "chart":    ("liuren/scripts/chart.py",     "起课（月将加时，天地盘四课三传）"),
        "analyze":  ("liuren/scripts/analyze.py",   "课体/三传与日干支关系/天将乘临"),
        "narrate":  ("liuren/scripts/narrate.py",   "人话叙述（机械标签，无吉凶断语）"),
        "render":   ("liuren/scripts/render.py",    "渲染报告（Markdown）"),
    },
    "lingqi": {
        "chart":    ("lingqi/scripts/chart.py",     "起课（三部掷数查 124 课表）"),
        "analyze":  ("lingqi/scripts/analyze.py",   "课名/象/卦注/象曰/詩曰直录"),
        "narrate":  ("lingqi/scripts/narrate.py",   "书源断语叙述（不做书外发挥）"),
        "render":   ("lingqi/scripts/render.py",    "渲染报告（Markdown）"),
    },
}

DISCIPLINE_DESC: dict[str, str] = {
    "liuyao":     "六爻纳甲",
    "ming":       "命理四柱",
    "meihua":     "梅花易数",
    "xiaoliuren": "小六壬",
    "zeji":       "择吉",
    "ziwei":      "紫微斗数",
    "liuren":     "大六壬",
    "lingqi":     "灵棋经",
}

ALL_DISCIPLINES = list(DISCIPLINE_COMMANDS.keys())


def _build_parser() -> argparse.ArgumentParser:
    """构建顶层 argparse 解析器：yi <discipline> <command> + yi execute。"""
    parser = argparse.ArgumentParser(
        prog="yi",
        description="易 · 统一命令行入口：yi <discipline> <command> [options]",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    sub = parser.add_subparsers(dest="top", title="顶层命令", metavar="<top>")

    # execute: 统一 Runtime 入口
    p_exec = sub.add_parser("execute", help="通过 YiRuntime 统一入口出报告")
    p_exec.description = "YiRuntime 统一入口：chart → analyze → render（推荐）"
    p_exec.add_argument("--discipline", "-d", required=True, choices=ALL_DISCIPLINES,
                        help="学科")
    p_exec.add_argument("--question", "-q", required=True, help="求测主题")
    p_exec.add_argument("--datetime", help="YYYY-MM-DD HH:MM")
    p_exec.add_argument("--gender", choices=["男", "女"])
    p_exec.add_argument("--mode", help="起卦方式（六爻/紫微）")
    p_exec.add_argument("--way", help="起卦方式（梅花/小六壬）")
    p_exec.add_argument("--numbers", help="数字起卦（逗号分隔）")
    p_exec.add_argument("--date", help="用事日期")
    p_exec.add_argument("--activity", help="事类（择吉/小六壬）")
    p_exec.add_argument("--output", "-o", help="输出 Markdown 文件路径")
    p_exec.add_argument("--output-html", help="输出 HTML 文件路径")

    # 分步命令：yi <discipline> <command>
    sp_disc = sub.add_parser("disc", help="(内部) 学科分步命令路由")
    sp_disc_sub = sp_disc.add_subparsers(dest="discipline", title="学科", metavar="<discipline>")
    for discipline, commands in DISCIPLINE_COMMANDS.items():
        desc = DISCIPLINE_DESC.get(discipline, discipline)
        p = sp_disc_sub.add_parser(discipline, help=desc)
        p.description = f"{discipline}：{desc}"
        sp_cmd = p.add_subparsers(dest="command", title="命令", metavar="<command>")
        for cmd, (_script, cmd_help) in commands.items():
            sp_cmd.add_parser(cmd, help=cmd_help)

    return parser


def _run_via_runtime(req: dict, output: str | None = None,
                     output_html: str | None = None) -> int:
    """通过 YiRuntime 统一入口出报告。"""
    from yishu_core.execution import YiRuntime
    rt = YiRuntime(str(REPO_ROOT))
    result = rt.execute(req)

    # stdout 输出 Markdown
    print(result.markdown)

    # 可选落盘
    if output:
        Path(output).write_text(result.markdown, encoding="utf-8")
        print(f"\n[已写入] {output}", file=sys.stderr)
    if output_html:
        Path(output_html).write_text(result.html, encoding="utf-8")
        print(f"\n[已写入] {output_html}", file=sys.stderr)

    return 0


def main(argv: list[str] | None = None) -> int:
    """统一 CLI 主入口。"""
    if argv is None:
        argv = sys.argv[1:]

    parser = _build_parser()

    # 兼容旧语法：yi <discipline> <command> ...（无前缀）
    if argv and argv[0] not in ("execute", "disc", "-h", "--help") and argv[0] in ALL_DISCIPLINES:
        return _run_legacy(argv)

    # 标准 argparse 路径
    if not argv or argv[0] in ("-h", "--help"):
        parser.print_help()
        return 0

    args = parser.parse_args(argv)

    if args.top == "execute":
        # 收集 Runtime 请求
        req = {"discipline": args.discipline, "question": args.question}
        for fld in ("datetime", "gender", "mode", "way", "numbers",
                     "date", "activity"):
            v = getattr(args, fld, None)
            if v is not None:
                req[fld] = v
        return _run_via_runtime(req, args.output, args.output_html)

    if args.top == "disc":
        return _run_legacy([args.discipline, args.command] + argv[3:])

    parser.print_help()
    return 0


def _run_legacy(argv: list[str]) -> int:
    """兼容旧语法：yi <discipline> <command> [options]。"""
    discipline = argv[0]

    if discipline not in DISCIPLINE_COMMANDS:
        print(f"未知学科：{discipline!r}", file=sys.stderr)
        print(f"可用学科：{'、'.join(ALL_DISCIPLINES)}", file=sys.stderr)
        return 1

    commands = DISCIPLINE_COMMANDS[discipline]

    if len(argv) < 2 or argv[1] not in commands:
        print(f"用法：yi {discipline} <command> [options]", file=sys.stderr)
        print(f"可用命令：{'、'.join(commands.keys())}", file=sys.stderr)
        return 1

    command = argv[1]
    script_rel = commands[command][0]
    script_path = DISCIPLINES_DIR / script_rel

    if not script_path.is_file():
        print(f"脚本不存在：{script_path}", file=sys.stderr)
        return 1

    script_argv = argv[2:]

    try:
        if command == "cast":
            # cast 走 Runtime（一键流程）
            req = _parse_legacy_cast(discipline, command, script_argv)
            if req is not None:
                return _run_via_runtime(req)
        # 其他分步命令：直接走子进程（精细调试）
        result = subprocess.run(
            [sys.executable, str(script_path), *script_argv],
        )
        return result.returncode
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"执行异常：{exc}", file=sys.stderr)
        return 1


def _parse_legacy_cast(discipline: str, command: str,
                        script_argv: list[str]) -> dict | None:
    """尝试把 yi <disc> cast 的 argv 解析成 Runtime 请求。失败则返回 None 走旧路径。"""
    # cast 专用参数少, 直接用最简单的(question + 学科默认参数)
    if not script_argv:
        return None
    req: dict = {"discipline": discipline, "question": script_argv[0]}
    # 透传 --key value
    i = 1
    while i < len(script_argv) - 1:
        k = script_argv[i]
        if k.startswith("--"):
            req[k[2:]] = script_argv[i + 1]
            i += 2
        else:
            i += 1
    return req


if __name__ == "__main__":
    raise SystemExit(main())
