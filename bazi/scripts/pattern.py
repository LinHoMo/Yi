# -*- coding: utf-8 -*-
"""命·格局与强弱 —— 薄 re-export 壳（拆解后因子仍从 ``bazi_factors`` 提供）。

本文件已按职责拆到 ``scripts/bazi_factors/`` 子包（strength / congrge / dayun /
combinations / bingyao）。本文件只作 re-export，保持 ``from pattern import ...``
不动——``scripts/analyze.py`` 与下游评测器仍可直接 import 本模块，无需改动。

注：``evaluate.py`` 只 import ``analyze`` 与 ``chart``，不直接碰 ``pattern``，
故本 re-export 对其完全透明。
"""
from __future__ import annotations

# 全量 re-export，保持 import 路径不变
from bazi_factors import *  # noqa: F401,F403  -- 薄聚合入口，下游 import pattern 不报错
from bazi_factors import __all__  # noqa: E402,F401

# ── 兼容旧私有引用 ──────────────────────────────────────────────────────────
# 以下名称在原 pattern.py 中是小写私有的工具函数，可能被外部直接引用（如测试）。
# 从 _common 同步一份命名，避免 ``from pattern import _god_detail`` 之类的路径断掉。
from bazi_factors._common import (  # noqa: E401,F403,E402
    _god_detail,
    _has_yang_ren,
    _role_of_elem,
    _role,
    _element_of_stem,
    _ke_wo,
)
