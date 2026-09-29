# -*- coding: utf-8 -*-
"""运行时适配：Windows 控制台默认 GBK，中文断语与 ✗/✓ 标记会直接抛 UnicodeEncodeError。

所有面向终端的 CLI 在入口调用 `force_utf8_stdio()`；
质量门按 `encoding="utf-8"` 解码子进程时，配套传 `utf8_subprocess_env()`。
"""
from __future__ import annotations

import os
import sys


def force_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):  # 已被重定向或不支持 reconfigure
            pass


def utf8_subprocess_env(base: dict | None = None) -> dict:
    """给 `subprocess.run(..., text=True, encoding="utf-8")` 配套的子进程环境。

    子进程 stdout 的编码由**它自己**的控制台代码页决定（Windows 上默认 GBK），
    与父进程怎么解码无关。父进程按 UTF-8 解码 GBK 字节流，中文全成替换字符，
    gate 里 `中文 in out` 一类断言于是与控制台代码页耦合——中文 Windows 上恒红
    （命科 [3] narrate 口径声明曾因此失败），UTF-8 环境（CI）却全绿，两处读数不可比。

    传本环境给子进程，强制其无论代码页一律输出 UTF-8，与父进程解码对齐。
    PYTHONUTF8/PYTHONIOENCODING 无条件覆盖：质量门要的是确定性，不是继承调用方设置。
    """
    env = dict(os.environ if base is None else base)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env
