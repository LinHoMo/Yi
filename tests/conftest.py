# -*- coding: utf-8 -*-
"""测试路径引导：core 与所需学科脚本入 sys.path。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in (
    "core",
    "disciplines/liuyao/scripts",
    "disciplines/ming/scripts",
):
    p = str(ROOT / rel)
    if p not in sys.path:
        sys.path.insert(0, p)
