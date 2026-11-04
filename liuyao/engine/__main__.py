# -*- coding: utf-8 -*-
"""D3 收编：保留 `python -m engine` 命令行入口（原 `scripts/engine/_core.py` 的 __main__ 行为；
508 批升格后本包在 `<学科根>/engine/`，用 `python -m engine` 需学科根在路径上）。"""
import sys

from ._core import main as _main

if hasattr(sys.stdout, "reconfigure"):   # cp936 控制台下中文产物须为可读 UTF-8（§四.9）
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if __name__ == "__main__":
    _main()
