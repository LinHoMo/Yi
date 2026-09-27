#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""梅花易数 MCP JSON-RPC 服务器（薄入口，路由在 tools/mcp_router.py）。

方法: meihua.chart / meihua.analyze / meihua.narrate / meihua.render / list_methods
协议: JSON-RPC 2.0 over stdio（复用 scripts/{chart,analyze,narrate,render}.py，不另写推演）。

  python scripts/mcp_server.py --help
  python scripts/mcp_server.py --list-methods
  python scripts/mcp_server.py --test-narrate
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_TOOLS = _ROOT / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from mcp_router import main_for_discipline  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main_for_discipline("meihua"))
