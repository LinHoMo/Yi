# -*- coding: utf-8 -*-
"""运行时适配：Windows 控制台默认 GBK，中文断语与 ✗/✓ 标记会直接抛 UnicodeEncodeError。

所有面向终端的 CLI 在入口调用 `force_utf8_stdio()`。
"""
from __future__ import annotations

import sys


def force_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):  # 已被重定向或不支持 reconfigure
            pass
