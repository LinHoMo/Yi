# -*- coding: utf-8 -*-
"""pytest 根配置（第五百二十批建，第五百二十二批收敛清单真源）。

两科 tests/ 目录各有 __init__.py（成为 `tests` 包），但父目录 liuyao/、bazi/ 非包，
pytest 在 prepend 模式下会把两科同名测试文件都命名为 `tests.smoke_test` 等而冲突。
本 conftest 用 collect_ignore 把 main() 式文件排除出自动收集；清单不再在本文件
另抄一份，而是从 `pytest_manifest.py` 单一真源派生。

桥接由仓库根的 `bridge_test.py` 以**独立子进程** `python <file>` 完成
（进程间零 import 污染、与 CI 既有调用一致）——不是 runpy，也不在各 tests/ 目录下。
six_god_wang_shuai_test.py 是原生 pytest，正常自动收集。
增删测试文件只改 `pytest_manifest.py`，覆盖由 `pytest_manifest.py` 与本文件保持一致（557 批后无单独桥接门）。
"""
from __future__ import annotations

import sys
from pathlib import Path

# conftest 由 pytest 在收集早期加载，此时 rootdir 未必已在 sys.path；
# 显式补一次，保证单一真源可导入（仅影响本进程，不改任何测试行为）。
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pytest_manifest import MAIN_STYLE_TESTS  # noqa: E402

collect_ignore = list(MAIN_STYLE_TESTS)
