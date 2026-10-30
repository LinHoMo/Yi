# -*- coding: utf-8 -*-
"""兼容入口（第三百五十六批）：真实实现已迁 `eval/case_runner.py`。

本文件不读案例库，只 re-export；保留它只为旧命令/旧 import 路径（README、
dev_tools/* 仍按 `scripts/case_runner.py` 或 `import case_runner` 使用）。
物理隔离判据见 `dev_tools/check_case_isolation.py`：实现层必须在 `eval/`，
`scripts/` 只准留这种纯 re-export shim。
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from eval.case_runner import *  # noqa: F401,F403,E402
