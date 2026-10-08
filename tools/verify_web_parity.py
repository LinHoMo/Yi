# -*- coding: utf-8 -*-
"""网页端与本地端**同源验收**：同一请求两边出报告，逐例比对。

  python tools/verify_web_parity.py            # 两科各一例
  python tools/verify_web_parity.py --verbose  # 附两边首段摘要

为什么需要这个脚本：
  网页端（Pyodide / 同进程 runpy）与本地端（子进程）是**同一条四段契约的两个
  执行器**。执行器可以不同，产出必须同源——否则"点开链接看到的报告"与"CI 出的
  报告"会长成两个样子，而没人会发现。本脚本把这件事变成一条命令。

额外作用：网页侧是**同一个解释器里按 CASES 顺序连跑**，而两科的 `scripts/`
目录同名（每科都有 chart.py）。所以这份顺序本身就是
`web/engine_runtime._isolate` 的回归网——某科拿到别科盘面，逐字节比对立刻会红。

比对口径：
  * Markdown：**逐字节**必须一致（两边都只写学科 render 段产出的文本）。
  * HTML   ：只有页头小字里的「运行环境」标签允许不同（这是有意标注），
             其余逐字节必须一致。
  * Evidence：结构化证据信封必须一致（同一份 core 提取器的纯函数输出；
             宿主分叉即红——2026-10-03 证据链收敛新增维度）。

覆盖不变式：
  CASES 覆盖的学科集合必须与**站点挂载集合**（`tools/build_web.py` 的
  `DISCIPLINE_META`）恒等——站点挂上了某科而这里没有正例，本脚本直接失败。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from yishu_core.report import DISCIPLINES, normalize_request, report_meta  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

CASES = (
    {"discipline": "liuyao", "question": "占本周面试能否通过", "mode": "time",
     "datetime": "2026-09-30 10:30"},
    {"discipline": "liuyao", "question": "占求财", "mode": "manual",
     "datetime": "2026-09-22 23:40", "yao": "7,8,9,7,6,8"},
    {"discipline": "ming", "datetime": "1990-05-20 10:30", "gender": "男"},
    # 再回到第一科收尾：证明"跑过别科之后，早先那科的 scripts/ 仍解析到
    # 自己那套"（同名遮蔽若被破坏，这一例最先红）。
    {"discipline": "liuyao", "question": "占出行", "mode": "time",
     "datetime": "2026-10-01 08:00"},
)


# 负例：非法 / 越界输入。两侧必须"一致地拒绝"，否则说明某一侧漏了参数门禁
# （映射层 `request.chart_argv` 是唯一入口，这条断言就是它的回归网）。
NEG_CASES = (
    {"discipline": "ming", "datetime": "1990-13-45", "gender": "男"},     # 不存在的日期
)
def _load_build_web():
    """按文件路径加载构建期唯一开关（`tools/` 不是包，按路径加载最省事）。"""
    path = ROOT / "tools" / "build_web.py"
    spec = importlib.util.spec_from_file_location("yi_build_web_for_parity", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _web_mount_ids() -> tuple[str, ...]:
    """站点挂载集合。唯一真值源是构建期 `DISCIPLINE_META`，此处不另存手写清单。"""
    return tuple(d["id"] for d in _load_build_web().DISCIPLINE_META)
