# -*- coding: utf-8 -*-
"""升格后的路径引导（第五百零八批）：`engine/` 已不在 `scripts/` 下，此处只做定位，不做判定。

为什么需要它：第五百零八批把 `scripts/engine/` 与 `scripts/classical/` 升格到
`<学科根>/engine/`，搬迁后的文件既找不到 `scripts/` 里的兄弟模块（`util`／`chain_tables`），
也找不到 `kernel_path.py` 本身。若每个文件各写一遍「往上是几层」，就是本仓 2026-11-04
实测踩到的静默缺陷（`classical_enhancements_fushi` 按 `parents[1]` 定位数据表落到不存在的
`scripts/data/`，表变空且门全绿）。故定位只留这一份实现：

1. 先在盘上向上搜 `scripts/kernel_path.py`，找到学科根（不按层数硬算，目录再搬不必改）；
2. 把 本目录／`scripts/`／<学科根>/`rules/`／学科根 四处入 `sys.path`（本目录供同族兄弟模块，
   `scripts/` 供 flat import，`rules/` 供 `direction`／`rule_engine`／`predicates` 等 L2 规则层 flat import，
   学科根供 `import engine` 解析到 `<学科根>/engine/`）；
3. 再交给 `kernel_path.ensure_kernel_on_path` 做内核定位（路径规则仍只在内核定位模块一份）。

⚠ 第五百零八批实踩：升格重写路径块时把 `step5.py` 里「向上搜 `rules/`」那段一并删掉，
`from direction import …` 当场 ModuleNotFoundError——故这一步收进本文件，不再逐文件写。
"""
from __future__ import annotations

import os
import sys


def setup(start_file: str) -> str:
    """定位学科根并配好四处 sys.path，返回学科根绝对路径。"""
    here = os.path.dirname(os.path.abspath(start_file))
    root = here
    while True:
        if os.path.isfile(os.path.join(root, "scripts", "kernel_path.py")):
            break
        up = os.path.dirname(root)
        if up == root:
            raise RuntimeError(
                f"从 {start_file} 向上未找到 scripts/kernel_path.py；"
                "请确认 engine/ 与 scripts/ 同在学科根下")
        root = up
    rules = os.path.join(root, "rules")
    paths = [root, os.path.join(root, "scripts"), here]
    if os.path.isdir(rules):
        paths.append(rules)
    for path in paths:
        if path not in sys.path:
            sys.path.insert(0, path)
    from kernel_path import ensure_kernel_on_path

    ensure_kernel_on_path(start_file)
    return root
