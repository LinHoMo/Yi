# -*- coding: utf-8 -*-
"""内核定位：向上搜 `core/yishu_core`，不写死目录层级。

本仓库的目录深度会变（六爻已从仓库根迁入 disciplines/liuyao/，内核上收到 Yi/core）。
凡是靠 `parents[1] / "core"` 这种算式的写法，一搬家就静默失效或落到错误目录，
所以路径规则只留这一份实现。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


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
    """把内核目录加入 sys.path 并返回它。"""
    core = kernel_dir(start_file)
    if str(core) not in sys.path:
        sys.path.insert(0, str(core))
    return core


def repo_root(start_file: str | Path) -> Path:
    """仓库根（含 core/ 与 disciplines/ 的那一级）。"""
    return kernel_dir(start_file).parent


def discipline_root(start_file: str | Path) -> Path:
    """当前学科目录（含 scripts/、data/、SKILL.md 的那一级）。"""
    p = Path(start_file).resolve()
    for cand in (p, *p.parents):
        if (cand / "SKILL.md").is_file():
            return cand
    return Path(start_file).resolve().parents[1]
