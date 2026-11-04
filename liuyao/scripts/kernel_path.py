# -*- coding: utf-8 -*-
"""内核定位：向上搜 `core/yishu_core`，不写死目录层级。

本仓库的目录深度会变（六爻已从仓库根迁入 liuyao/，内核上收到 Yi/core）。
凡是靠 `parents[1] / "core"` 这种算式的写法，一搬家就静默失效或落到错误目录，
所以路径规则只留这一份实现。
"""
from __future__ import annotations

import sys
from pathlib import Path

# 第五百零八批（engine/ 升格）：`engine/` 与 `engine/classical/` 已从 scripts/ 移到学科根下，
# 于是 `from engine import …` 现在需要**学科根**在 sys.path 上（不再是 scripts/）。
# 本模块是两科路径规则唯一实现，且被全仓最先导入，故在导入时就把学科根加入路径：
# 调用方只要 `import kernel_path`（或下面的 ensure_kernel_on_path）即可解析到 <学科根>/engine。
# 不按层数硬算——本文件恒在 <学科根>/scripts/ 下。
_DISCIPLINE_ROOT = Path(__file__).resolve().parents[1]
if str(_DISCIPLINE_ROOT) not in sys.path:
    sys.path.insert(0, str(_DISCIPLINE_ROOT))


def _search(start, marker_parts):
    """向上找第一个含 `marker_parts` 相对路径的目录，返回**该相对路径本身**。"""
    p = Path(start).resolve()
    for cand in (p, *p.parents):
        hit = cand.joinpath(*marker_parts)
        if hit.is_dir():
            return hit
    return None


def kernel_dir(start_file: str | Path) -> Path:
    """返回包含 `yishu_core` 包的 core 目录绝对路径。

    注意返回的是 core 本身（插进 sys.path 后才能 `import yishu_core`），
    不是 core/yishu_core。
    """
    found = _search(Path(start_file).parent, ("core", "yishu_core"))
    if found is None:
        raise RuntimeError(
            f"从 {start_file} 向上未找到 core/yishu_core；请确认内核在仓库根的 core/ 下")
    return found.parent


def ensure_kernel_on_path(start_file: str | Path) -> Path:
    """把内核目录加入 sys.path 并返回它。

    第五百零八批起同时保证**学科根**在路径上（`import engine` 需要它；
    见模块头 `_DISCIPLINE_ROOT` 的说明）。
    """
    core = kernel_dir(start_file)
    if str(core) not in sys.path:
        sys.path.insert(0, str(core))
    disc = core.parent
    if str(disc) not in sys.path:
        sys.path.insert(0, str(disc))
    return core


def repo_root(start_file: str | Path) -> Path:
    """学科根（core 的父目录；扁平化后每科自包含 core，故等于本学科目录）。"""
    return kernel_dir(start_file).parent
