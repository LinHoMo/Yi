# -*- coding: utf-8 -*-
"""pytest 根配置（第五百一十九批续·引入 pytest 测试框架）。

两科 tests/ 目录各有 __init__.py（成为 `tests` 包），但父目录 liuyao/、bazi/ 非包，
pytest 在 prepend 模式下会把两科同名测试文件都命名为 `tests.smoke_test` 等而冲突。
本 conftest 用 collect_ignore 把沿用 `python xxx_test.py` 习惯的 main() 式文件排除出
自动收集，改由同目录 bridge_test.py 用 runpy 桥接成 pytest 用例（见该文件）。
six_god_wang_shuai_test.py 是原生 pytest，正常自动收集。
"""
collect_ignore = [
    "liuyao/tests/smoke_test.py",
    "liuyao/tests/regression_test.py",
    "liuyao/tests/thinking_chain_tests.py",
    "bazi/tests/smoke_test.py",
    "bazi/tests/regression_test.py",
]
