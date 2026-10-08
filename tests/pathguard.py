# -*- coding: utf-8 -*-
"""根测试的同名遮蔽隔离原语（唯一实现处）。

八科 `scripts/` **目录同名**（每科都有 chart/analyze/narrate/render/evaluate），
而 pytest 在同一个解释器里按文件名字母序收集测试模块。任何测试若把别科
`scripts/` `sys.path.insert(0, ...)` 后不还，后面所有按裸名 import 的测试都会拿到
**别科**的同名模块。

2026-10-08 实踩：新增的 `test_rengui_neishiwaishi_yingqi`（R）与
`test_zhinan_wangxiang`（Z）把 `disciplines/liuren/scripts` 顶到 sys.path[0]，
字母序在中间的 `test_yingqi_windows`（Y）的 `from evaluate import RHYTHM_PAIRS`
于是解析到六壬的 evaluate → 收集期 ImportError，`tools/check.py --full` 的 [8] 判红。
根 AGENTS.md §六 早已为浏览器侧写下同一约束（`engine_runtime._isolate`），此处是它的
测试侧对应物。

用法（按文件路径加载，避免 `import conftest` 在 import-path=importlib 下不可用）：

    import importlib.util as _ilu
    from pathlib import Path
    _spec = _ilu.spec_from_file_location(
        "yi_pathguard", Path(__file__).with_name("pathguard.py"))
    _pg = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_pg)
    with _pg.discipline_scripts("disciplines/liuren/scripts"):
        from chart import chart
"""
from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def discipline_scripts(*rels: str):
    """临时把若干目录顶到 sys.path 最前，退出时还原路径并清掉本次新载的本科模块。

    清缓存按「模块文件的实际位置」判定，因此被 `with` 块内 import 出来的符号
    仍绑在调用方命名空间里可用，而后续测试重新按名解析时会拿到自己那一科的模块。
    """
    paths = [str(ROOT / r) for r in rels]
    added = [p for p in paths if p not in sys.path]
    snapshot = dict(sys.modules)
    for p in added:
        sys.path.insert(0, p)
    try:
        yield
    finally:
        for p in added:
            try:
                sys.path.remove(p)
            except ValueError:
                pass
        for name, mod in list(sys.modules.items()):
            if name in snapshot and snapshot[name] is mod:
                continue          # 本来就在、且没被替换：不动
            f = getattr(mod, "__file__", None)
            if f and Path(f).resolve().is_file() and str(Path(f).resolve()).startswith(
                    tuple(p + "\\" for p in paths) + tuple(p + "/" for p in paths)):
                del sys.modules[name]
