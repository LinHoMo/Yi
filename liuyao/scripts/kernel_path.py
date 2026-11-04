# -*- coding: utf-8 -*-
"""路径规则唯一真源：向上搜 `core/yishu_core`，不按 `parents[N]` 硬算层级。

引擎族与各 scripts 模块一律用 `disc_path` / `data_path` / `load_data_json` 取路径；
本文件恒在 `<学科根>/scripts/` 下，导入时顺带把学科根加进 sys.path（`import engine` 需要）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# 唯一一处层级推算：仅用于把学科根加进 sys.path，不用于取数据路径（本文件恒在 <学科根>/scripts/）
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
    """返回 core 目录本身（插进 sys.path 后才能 `import yishu_core`）。"""
    found = _search(Path(start_file).parent, ("core", "yishu_core"))
    if found is None:
        raise RuntimeError(f"从 {start_file} 向上未找到 core/yishu_core")
    return found.parent


def ensure_kernel_on_path(start_file: str | Path) -> Path:
    """把内核目录与学科根加入 sys.path，返回内核目录。"""
    core = kernel_dir(start_file)
    if str(core) not in sys.path:
        sys.path.insert(0, str(core))
    disc = core.parent
    if str(disc) not in sys.path:
        sys.path.insert(0, str(disc))
    return core


def repo_root(start_file: str | Path) -> Path:
    """学科根（core 的父目录）。"""
    return kernel_dir(start_file).parent


def disc_path(*parts: str) -> Path:
    """学科根下的路径：向上搜内核定位，不依赖调用方目录、不按层数硬算。"""
    return kernel_dir(__file__).parent.joinpath(*parts)


def data_path(*parts: str) -> Path:
    """学科根 `data/` 下的路径。"""
    return disc_path("data", *parts)


def load_data_json(*parts: str, required: tuple[str, ...] = ()) -> dict:
    """读 `data/*.json`；缺文件、非法 JSON、必需键为空一律抛错，绝不静默降级为空表。"""
    path = data_path(*parts)
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = [k for k in required
               if not isinstance(data.get(k), (dict, list)) or not data.get(k)]
    if missing:
        raise RuntimeError(f"{path.name} 缺表或表为空：{', '.join(missing)}")
    return data
