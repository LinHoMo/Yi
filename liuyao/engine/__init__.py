# -*- coding: utf-8 -*-
"""engine 包（D3 收编、508 批升格到 `<学科根>/engine/`）：收 step1~5 与 T31 抽出的 _step5_*
辅助模块，另含 `classical/` 古籍增强族；模块名保持不变，调用方经
「学科根入 sys.path」或 `engine/_bootstrap.setup` 转发，故 `from engine import …` 语义不变。

本包正文原位于 `scripts/engine/_core.py`（装卦排盘聚合入口），D3 收编时与 `pipeline/` 子包同驻
`scripts/engine/`；508 批把整树升到 `<学科根>/engine/`（与 `scripts/` 平级）。
为避免旧模块名 engine 与 `engine/`（包）二义冲突，正文迁入 `engine/_core.py`，
此处仅做再导出，保证 `from engine import build_hexagram_result, coin_toss, main` 等公开 API 不变。
"""
from ._core import *  # noqa: F401,F403
from ._core import main  # noqa: F401
