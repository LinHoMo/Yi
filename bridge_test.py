# -*- coding: utf-8 -*-
"""main() 式测试桥接 + 清单真源（第五百二十批建；第五百五十九批与 `pytest_manifest.py` 合并）。

两科 `tests/` 混用两种风格：
  · 原生 pytest（`def test_*` + `assert`）：由 pytest 直接收集，不入本表；
  · main() 式（沿用 `python xxx_test.py` 习惯，errs 累积 + return 1）：不能进自动收集
    （两科 `tests` 同名包会撞 `tests.smoke_test`），由根 `conftest.py` 的 `collect_ignore`
    排除，再由本文件以独立子进程 `python <file>` 桥接成 pytest 用例。

`MAIN_STYLE_TESTS` 是本表**唯一**真源：conftest 的 collect_ignore 与下面的桥接用例都从它派生。
增删测试文件只改这一处；路径一律相对仓库根、用 `/` 分隔（Windows 下同）。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

MAIN_STYLE_TESTS: tuple[str, ...] = (
    "liuyao/tests/smoke_test.py",
    "liuyao/tests/regression_test.py",
    "liuyao/tests/thinking_chain_tests.py",
    "bazi/tests/smoke_test.py",
    "bazi/tests/regression_test.py",
    "bazi/tests/ganzhi_song_test.py",
)

_ROOT = Path(__file__).resolve().parent


@pytest.mark.parametrize("rel", MAIN_STYLE_TESTS)
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
