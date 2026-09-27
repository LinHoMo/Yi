# -*- coding: utf-8 -*-
"""六爻思维链：应期判断入口（_predict_timing 巨石已按职责切出至 chain_step5_yp_timing）。

本文件只保留再导出入口，供 thinking_chain.py / chain_step5.py 的
`from chain_step5_yp import _predict_timing` 继续可用（依赖单向：
chain_step5_yp → chain_step5_yp_timing）。
"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

from chain_step5_yp_timing import predict_timing_core as _predict_timing  # noqa: E402
