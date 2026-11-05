# -*- coding: utf-8 -*-
"""main() 式测试桥接（第五百一十九批续·引入 pytest 测试框架）。

两科测试混用两种风格（见 pyproject.toml 注释）：six_god_wang_shuai_test.py 是原生
pytest（由 pytest 直接收集）；其余是沿用 `python xxx_test.py` 习惯的 main() 式
（errs 累积 + return 1）。本文件把每个 main() 式测试作为独立子进程 `python <file>`
跑一遍（与 CI 既有调用完全一致、且进程间零 import 污染），以 pytest 用例形式报告其
退出码。被桥接文件见下 _MAIN_STYLE；这些文件已由根 conftest 的 collect_ignore 排除出
自动收集，避免两科 tests/ 同名包 `tests.*` 冲突。six_god 不在列、由 pytest 直接收集。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent

_MAIN_STYLE = [
    "liuyao/tests/smoke_test.py",
    "liuyao/tests/regression_test.py",
    "liuyao/tests/thinking_chain_tests.py",
    "bazi/tests/smoke_test.py",
    "bazi/tests/regression_test.py",
]


@pytest.mark.parametrize("rel", _MAIN_STYLE)
def test_main_style_module(rel: str) -> None:
    path = _ROOT / rel
    proc = subprocess.run(
        [sys.executable, str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0, (
        f"{rel} 以退出码 {proc.returncode} 失败\n"
        f"--- stdout (tail) ---\n{proc.stdout[-1500:]}\n"
        f"--- stderr (tail) ---\n{proc.stderr[-1500:]}"
    )
