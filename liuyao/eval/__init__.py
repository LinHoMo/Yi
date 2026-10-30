# -*- coding: utf-8 -*-
"""六爻评测层（第三百五十六批起物理独立于 `scripts/`）。

`case_runner.py` / `evaluate.py` / `build_portal_assets.py` 的真实实现都在本目录；
`scripts/` 下同名文件只是兼容入口（纯 re-export，不读案例库）。这样
`check_case_isolation.py` 不再需要把 `scripts/` 里的评测文件列入白名单：
交付/解读路径里已经没有案例读取代码。命令行可继续用旧路径（shim），
也可用 `python eval/...` 直接跑。
"""
