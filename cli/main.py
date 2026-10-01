# -*- coding: utf-8 -*-
"""易 · 统一命令行入口：yi <discipline> <command> [options]

Usage:
    yi <discipline> <command> [options]

Disciplines:
    liuyao       六爻纳甲      commands: cast chart analyze narrate render
    ming         命理四柱      commands: chart analyze
    meihua       梅花易数      commands: cast chart
    xiaoliuren   小六壬        commands: cast
    zeji         择吉          commands: chart

Examples:
    yi liuyao cast "占买房子何时有结果"
    yi liuyao chart --mode coin
    yi liuyao analyze chart.json
    yi liuyao narrate analyze.json
    yi liuyao render analyze.json
    yi ming chart --datetime "1990-05-20 10:30" --gender 男
    yi ming analyze chart.json
    yi meihua cast "占投资"
    yi meihua chart --way time
    yi xiaoliuren cast "占出行"
    yi zeji chart --date "2026-09-30" --activity 开市
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# 仓库根 & 学科目录（从本文件位置向上两层即为仓库根）
REPO_ROOT = Path(__file__).resolve().parents[1]
DISCIPLINES_DIR = REPO_ROOT / "disciplines"

# ── 学科命令注册表 ────────────────────────────────────────────────────────
# discipline → { command: (相对路径, 帮助文本) }
# 相对路径以 disciplines/ 为基准
DISCIPLINE_COMMANDS: dict[str, dict[str, tuple[str, str]]] = {
    "liuyao": {
        "cast":     ("liuyao/scripts/yi_liuyao.py", "一键占算（chart→analyze→render→报告）"),
        "chart":    ("liuyao/scripts/chart.py",     "起卦（纯机械排盘）"),
        "analyze":  ("liuyao/scripts/analyze.py",   "规则推演（盘面→因子+吉凶）"),
        "narrate":  ("liuyao/scripts/narrate.py",   "人话解读"),
        "render":   ("liuyao/scripts/render.py",    "渲染报告"),
    },
    "ming": {
        "chart":    ("ming/scripts/chart.py",       "出生排盘（四柱+机械因子）"),
        "analyze":  ("ming/scripts/analyze.py",     "命局推演"),
    },
    "meihua": {
        "cast":     ("meihua/scripts/chart.py",     "一键起卦"),
        "chart":    ("meihua/scripts/chart.py",     "起卦"),
    },
    "xiaoliuren": {
        "cast":     ("xiaoliuren/scripts/chart.py", "一键起课"),
    },
    "zeji": {
        "chart":    ("zeji/scripts/chart.py",       "择日起局"),
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
    """构建顶层 argparse 解析器：yi <discipline> <command>。"""
    parser = argparse.ArgumentParser(
        prog="yi",
        description="易 · 统一命令行入口：yi <discipline> <command> [options]",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sp_disc = parser.add_subparsers(
        dest="discipline",
        title="学科",
        metavar="<discipline>",
    )

    for discipline, commands in DISCIPLINE_COMMANDS.items():
        desc = DISCIPLINE_DESC.get(discipline, discipline)
        p = sp_disc.add_parser(discipline, help=desc)
        p.description = f"{discipline}：{desc}"

        sp_cmd = p.add_subparsers(
            dest="command",
            title="命令",
            metavar="<command>",
        )
        for cmd, (_script, cmd_help) in commands.items():
            sp_cmd.add_parser(cmd, help=cmd_help)

    return parser


def main(argv: list[str] | None = None) -> int:
    """统一 CLI 主入口。

    根据 discipline 子命令将剩余参数透传给对应学科的脚本入口。

    为什么手动路由而不交给 argparse parse_args()：
    各命令的真正参数由**学科脚本自己的 argparse** 定义（--mode、--datetime 等），
    顶层解析器不知道也不该知道它们。若在这里 parse_args()，未知参数会被顶层
    直接拒绝、无法透传。argparse 在此只负责生成 `--help` 帮助视图；
    discipline/command 的合法性校验与转发是本函数的职责。
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = _build_parser()

    # 无参数或首参数为 --help/-h → 顶层帮助
    if not argv or argv[0] in ("-h", "--help"):
        parser.print_help()
        return 0

    discipline = argv[0]

    # 未知学科
    if discipline not in DISCIPLINE_COMMANDS:
        print(f"未知学科：{discipline!r}", file=sys.stderr)
        print(f"可用学科：{'、'.join(ALL_DISCIPLINES)}", file=sys.stderr)
        parser.print_help()
        return 1

    # 仅学科无命令 → 学科帮助
    commands = DISCIPLINE_COMMANDS[discipline]
    if len(argv) < 2 or argv[1] not in commands:
        parser.parse_args([discipline, "--help"])
        return 0

    command = argv[1]

    # 命令校验（防御性，理论上已被上面分支覆盖）
    if command not in commands:
        print(f"未知命令：{command!r}", file=sys.stderr)
        print(f"可用命令：{'、'.join(commands.keys())}", file=sys.stderr)
        parser.parse_args([discipline, "--help"])
        return 1

    # 定位脚本
    script_rel = commands[command][0]
    script_path = DISCIPLINES_DIR / script_rel

    if not script_path.is_file():
        print(f"脚本不存在：{script_path}", file=sys.stderr)
        return 1

    # 透传剩余参数给学科脚本
    script_argv = argv[2:]

    try:
        result = subprocess.run(
            [sys.executable, str(script_path), *script_argv],
        )
        return result.returncode
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"执行异常：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
