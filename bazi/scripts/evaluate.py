# -*- coding: utf-8 -*-
"""兼容入口（第三百五十九批）：真实实现已迁 `eval/evaluate.py`。

本文件不读案例库，只 re-export；保留它只为 README/CAPABILITY/CI 里的旧命令路径。
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# AGENTS §四.9：中文 CLI 的 UTF-8 守卫写在入口文件自身（cp936 控制台下产物须可读）
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from eval.evaluate import *  # noqa: F401,F403,E402
import eval.evaluate as _impl  # noqa: E402


def __getattr__(name):
    """星号导出不含下划线名；旧 `import evaluate` 的 dev_tools 仍可访问实现模块属性。"""
    return getattr(_impl, name)


if __name__ == "__main__":
    raise SystemExit(main())  # noqa: F405  CLI 兼容：旧命令 python scripts/evaluate.py ...
