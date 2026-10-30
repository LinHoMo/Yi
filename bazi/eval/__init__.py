# -*- coding: utf-8 -*-
"""八字评测层（第三百五十九批起物理独立于 `scripts/`）。

真实实现 `evaluate.py` 在本目录；`scripts/evaluate.py` 只是纯 re-export 兼容入口。
案例库读取只允许发生在 `eval/` / `dev_tools/` / `tests/`，交付路径不得触达
`data/cases/`——判据见 `dev_tools/check_case_isolation.py`（本目录存在即走物理隔离档）。
"""
