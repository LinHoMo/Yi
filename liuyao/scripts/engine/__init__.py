# -*- coding: utf-8 -*-
"""D3 收编：engine/ 收 step1~5 与 T31 抽出的 _step5_* 辅助模块；模块名保持不变，调用方经 scripts/engine/pipeline/ 入 sys.path 转发。

本包正文原位于 scripts/engine/_core.py（装卦排盘聚合入口），D3 收编时与 engine/pipeline/ 子包同驻
scripts/engine/，为避免 engine.py（模块）与 engine/（包）二义冲突，正文迁入 engine/_core.py，
此处仅做再导出，保证 `from engine import build_hexagram_result, coin_toss, main` 等公开 API 不变。
"""
from ._core import *  # noqa: F401,F403
from ._core import main  # noqa: F401
