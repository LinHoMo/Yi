# -*- coding: utf-8 -*-
"""测试路径引导：core 与所需学科脚本入 sys.path。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# insert(0) 循环后「最后插入者在 sys.path 最前」。
# liuyao/scripts 必须先于 ming/scripts 解析：两科 scripts/ 有 5 个同名模块
# （chart/analyze/evaluate/narrate/render），根测试
# test_yingqi_windows 的 `from evaluate import RHYTHM_PAIRS` 要的是六爻的；
# 而 `import pattern`（test_ming_dayun）六爻没有，仍落到命科的。
# 2026-09-30e 记：b329228 给 ming 新增 evaluate.py 后，旧顺序让 ming 遮蔽了
# 六爻 evaluate，根 pytest 当场收集失败。
for rel in (
    "core",
    "disciplines/ming/scripts",
    "disciplines/liuyao/scripts",
):
    p = str(ROOT / rel)
    if p not in sys.path:
        sys.path.insert(0, p)
