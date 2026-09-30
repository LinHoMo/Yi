"""学科 CLI 基类。

子类只需重写 discipline_name() 和四个核心方法的具体实现，
即可自动获得统一的 cli 入口（chart / analyze / narrate / render）。
"""
from __future__ import annotations

import argparse
import json
import sys
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class DisciplineCLI(ABC):
    """学科 CLI 基类。子类继承并实现抽象方法即可。

    用法：
        class MyCLI(DisciplineCLI):
            @staticmethod
            def discipline_name() -> str:
                return "mydiscipline"

            def run_chart(self, args): ...
            def run_analyze(self, args): ...
            def run_narrate(self, args): ...
            def run_render(self, args): ...
    """

    # ── 子类必须实现的抽象方法 ──────────────────────────────────────────────

    @staticmethod
    @abstractmethod
    def discipline_name() -> str:
        """学科标识字符串（如 'liuyao', 'ming'）。"""
        ...

    @abstractmethod
    def run_chart(self, args: argparse.Namespace) -> int:
        """执行 chart 步骤，返回退出码。"""
        ...

    @abstractmethod
    def run_analyze(self, args: argparse.Namespace) -> int:
        """执行 analyze 步骤，返回退出码。"""
        ...

    @abstractmethod
    def run_narrate(self, args: argparse.Namespace) -> int:
        """执行 narrate 步骤，返回退出码。"""
        ...

    @abstractmethod
    def run_render(self, args: argparse.Namespace) -> int:
        """执行 render 步骤，返回退出码。"""
        ...

    # ── 通用实现（子类通常不需要覆盖） ──────────────────────────────────────

    def build_parser(self) -> argparse.ArgumentParser:
        """构建统一的 argparse 解析器。"""
        parser = argparse.ArgumentParser(
            prog=f"yi {self.discipline_name()}",
            description=f"{self.discipline_name()}：{self.short_desc()}",
        )
        sub = parser.add_subparsers(dest="command", help="可用命令")

        # chart
        p_chart = sub.add_parser("chart", help="起卦 / 排盘（纯确定性，无解读）")
        p_chart.add_argument("--out", help="输出文件路径（JSON）")

        # analyze
        p_ana = sub.add_parser("analyze", help="规则推演（盘面→因子+吉凶）")
        p_ana.add_argument("--input", required=True, help="chart JSON 文件路径")
        p_ana.add_argument("--out", help="输出文件路径（JSON）")

        # narrate
        p_nar = sub.add_parser("narrate", help="人话解读")
        p_nar.add_argument("--input", required=True, help="analyze JSON 文件路径")
        p_nar.add_argument("--out", help="输出文件路径（MD）")

        # render
        p_rend = sub.add_parser("render", help="报告渲染")
        p_rend.add_argument("--input", required=True, help="analyze JSON 文件路径")
        p_rend.add_argument("--format", default="html", choices=["html", "markdown", "json"])
        p_rend.add_argument("--out", help="输出文件路径")

        # cast（一键：chart→analyze→render）
        p_cast = sub.add_parser("cast", help="一键占算（chart→analyze→render）")
        p_cast.add_argument("--format", default="html", choices=["html", "markdown", "json"])
        p_cast.add_argument("--out", help="输出文件路径")

        return parser

    def short_desc(self) -> str:
        """子类可覆盖：一行简短描述。"""
        return "易 · 学科推演"

    def run(self, argv: Optional[list] = None) -> int:
        """主入口。"""
        parser = self.build_parser()
        args = parser.parse_args(argv)

        if not args.command:
            parser.print_help()
            return 1

        handler = {
            "chart": self.run_chart,
            "analyze": self.run_analyze,
            "narrate": self.run_narrate,
            "render": self.run_render,
            "cast": self.run_cast,
        }.get(args.command)

        if handler is None:
            parser.print_help()
            return 1

        try:
            return handler(args)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def run_cast(self, args: argparse.Namespace) -> int:
        """一键占算：依次执行 chart → analyze → narrate → render。"""
        import tempfile, os
        # 先跑 chart 到临时文件
        chart_args = argparse.Namespace(out=None)
        # 子类可重写以提供默认 chart 参数
        rc = self.run_chart(chart_args)
        if rc != 0:
            return rc

        # 注意：这是基类的默认实现，通常子类会重写 run_cast
        # 使用更具体的方式串联步骤
        print("cast: use discipline-specific implementation", file=sys.stderr)
        return 0

    @staticmethod
    def load_json(path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_json(path: str, data: Any) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def save_text(path: str, text: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
