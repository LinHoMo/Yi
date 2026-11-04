# -*- coding: utf-8 -*-
"""D3 收编：保留 `python -m engine` 命令行入口（原 scripts/engine/_core.py 的 __main__ 行为）。"""
from ._core import main as _main

if __name__ == "__main__":
    _main()
