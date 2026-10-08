# -*- coding: utf-8 -*-
"""tests/pathguard.py 的自证：隔离用完必须把路径与模块缓存还干净。

守的是同名遮蔽路径隔离的原子性保证。

本文件**不 assert「哪一科在最前」**：根测试共用一个解释器、按文件名字母序收集，
先跑的测试会把自己那科插到 sys.path[0]——那是收集顺序，不是 pathguard 的职责
（写死它曾让本测整跑时假红两次）。它只保证两件事：进去什么样、出来什么样；
CM 内新载的同名模块不留缓存。
"""
from __future__ import annotations

import importlib.util as _ilu
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MING = ROOT / "disciplines" / "ming" / "scripts"

_spec = _ilu.spec_from_file_location(
    "yi_pathguard", Path(__file__).with_name("pathguard.py"))
pathguard = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(pathguard)


def _resolve_evaluate() -> Path:
    """当前 `evaluate` 实际解析到哪一科的 scripts/ 目录。"""
    import evaluate
    return Path(evaluate.__file__).resolve().parent


def test_cm_restores_sys_path_exactly():
    """CM 退出后 sys.path 必须逐位等于进入前。"""
    before = list(sys.path)
    with pathguard.discipline_scripts("disciplines/ming/scripts"):
        pass  # 不确保最前，仅验证退出还原
    assert sys.path == before, "CM 退出后 sys.path 未逐位还原"


def test_cm_puts_discipline_at_front():
    """ensure_front=True 时目标路径必须顶到 sys.path[0]。"""
    with pathguard.discipline_scripts("disciplines/ming/scripts", ensure_front=True):
        assert Path(sys.path[0]).resolve() == MING, "CM 未把命科 scripts 顶到最前"


def test_cm_evicts_modules_it_loaded():
    """CM 内新载的同名模块必须清出 sys.modules，否则会发给后续测试。"""
    saved = sys.modules.get("analyze")
    try:
        sys.modules.pop("analyze", None)
        with pathguard.discipline_scripts("disciplines/ming/scripts", ensure_front=True):
            import analyze as _ming_analyze    # noqa: F401  与别科同名
            assert Path(_ming_analyze.__file__).resolve().parent == MING
            assert "analyze" in sys.modules
        assert "analyze" not in sys.modules, "命科 analyze 留在缓存里"
    finally:
        if saved is not None:
            sys.modules["analyze"] = saved       # 复位：不替别的测试换缓存


def test_negative_probe_shadowing_is_real():
    """负例自证：不套 CM 的裸 `sys.path.insert` 必须**确实造成**遮蔽。

    若哪天同名遮蔽不再可能（目录改名/判据失效），本测会红——它证明前两测不是
    空跑，而不是让人相信"门应该会咬"（AGENTS.md §四.8）。
    """
    
    snapshot_path = list(sys.path)
    snapshot_mod = dict(sys.modules)
    before = _resolve_evaluate()
    try:
        sys.path.insert(0, str(MING))
        sys.modules.pop("evaluate", None)
        assert _resolve_evaluate() == MING, "裸 insert 不再遮蔽——隔离测试的前提已失效"
    finally:
        sys.path[:] = snapshot_path
        sys.modules.clear()
        sys.modules.update(snapshot_mod)
    assert _resolve_evaluate() == before, "污染没清干净，会串到后续测试"
