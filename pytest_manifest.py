# -*- coding: utf-8 -*-
"""pytest 桥接清单**单一真源**（第五百二十批建，第五百二十二批收敛）。

两科 `tests/` 混用两种风格：

  · 原生 pytest（`def test_*` + `assert`）：由 pytest 直接收集，不入本表；
  · main() 式（沿用 `python xxx_test.py` 习惯，errs 累积 + return 1）：
    不能进自动收集（两科 `tests` 同名包会撞 `tests.smoke_test`），由根
    `conftest.py` 的 `collect_ignore` 排除，再由根 `bridge_test.py` 以独立
    子进程 `python <file>` 桥接成 pytest 用例。

本表是这三种消费方（conftest / bridge / 根级覆盖门）**唯一**允许写清单的地方。
增删测试文件只改这一处；557 批瘦身后不再有桥接门；本表与盘上
各 tests/ 目录、CI 的直跑命令逐格对拍，漏一项即判红。

路径一律相对仓库根、用 `/` 分隔（Windows 下也按此写法，由 Path 解析）。
"""
from __future__ import annotations

MAIN_STYLE_TESTS: tuple[str, ...] = (
    "liuyao/tests/smoke_test.py",
    "liuyao/tests/regression_test.py",
    "liuyao/tests/thinking_chain_tests.py",
    "bazi/tests/smoke_test.py",
    "bazi/tests/regression_test.py",
)
