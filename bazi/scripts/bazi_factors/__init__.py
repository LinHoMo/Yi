# -*- coding: utf-8 -*-
"""命·格局与强弱 —— 拆解后因子工具箱（薄聚合入口）。

本包是 ``scripts/pattern.py`` 的等价拆封版，按职责切分：

- ``strength``      —— 日主强弱判据 / 扶抑用神 (``strength_and_pattern``)
- ``congrge``       —— 从格可判级 (``_from_judge``) / 格局成败救应 (``judge_pattern_cheng_bai``)
- ``dayun``         —— 大运 / 流年 / 大运×流年交互
- ``combinations``  —— 三会 / 四柱干支关系 / 天克地冲 / 十神组合 / 通关关隔
- ``bingyao``       —— 病药 (《神峰通考·病药说类》)

``scripts/pattern.py`` 保留为 re-export 壳，``import pattern`` 继续可用，
``from pattern import strength_and_pattern, ...`` 不动——不破坏现有 import 路径。
"""
from .strength import strength_and_pattern
from .congrge import _from_judge, judge_pattern_cheng_bai
from .dayun import (
    dayun_table,
    liunian_table,
    dayun_liunian_interactions,
    dayun_ming_yindong,
    liunian_ming_yindong,
    liuyue_table,
    xiao_yun_table,
    tai_yuan,
)
from .combinations import (
    san_hui_present,
    pillar_relations,
    tian_ke_di_chong,
    ten_god_combos,
    tong_guan,
)
from .bingyao import bing_yao

__all__ = [
    # strength
    "strength_and_pattern",
    # congrge
    "_from_judge",
    "judge_pattern_cheng_bai",
    # dayun
    "dayun_table",
    "liunian_table",
    "dayun_liunian_interactions",
    "dayun_ming_yindong",
    "liunian_ming_yindong",
    "liuyue_table",
    "xiao_yun_table",
    "tai_yuan",
    # combinations
    "san_hui_present",
    "pillar_relations",
    "tian_ke_di_chong",
    "ten_god_combos",
    "tong_guan",
    # bingyao
    "bing_yao",
]
