# -*- coding: utf-8 -*-
"""六爻古典判定纯函数库（L2 规则仲裁层共享谓词原语）。

从 `classical_enhancements_direction` 抽出，供 `rule_engine`（仲裁器）与
`classical_enhancements_direction`（apply_caps 用 RANK）共同复用，打破旧环：
    旧：rule_engine ──import──> classical_enhancements_direction（纯函数）
        classical_enhancements_direction ──延迟 import──> rule_engine.evaluate_caps
    新：rule_engine ──import──> predicates（本库）
        classical_enhancements_direction ──import──> predicates（RANK）
        两者不再互相 import，环断开。

本库只放**无状态、无盘面 IO 的纯函数**：卦爻查找、月建旺衰、六合六冲、
月破/旬空判定、档位序、化凶枚举。不做判定组合（那是 rule_engine 的 when/gates）。
"""
from __future__ import annotations
import os as _ks_os, sys as _ks_sys

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))  # liuyao/rules/
_scripts_d = _ks_os.path.join(_ks_os.path.dirname(_ks_d), "scripts")  # liuyao/scripts/（kernel_path 所在）
for _p in (_ks_d, _scripts_d):
    if _p not in _ks_sys.path:
        _ks_sys.path.insert(0, _p)

from kernel_path import ensure_kernel_on_path as _ensure_kernel  # noqa: E402
_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402
    BRANCH_ELEMENTS,
    CHONG_PAIRS,
    HE_PAIRS,
    KE_CYCLE,
    SHENG_CYCLE,
)

# 判定上限的档位序（与 step5 的 verdict 枚举一致）
RANK = {"大凶": 0, "凶": 1, "平凶": 2, "平吉": 3, "吉": 4, "大吉": 5}

_HE_SET = {frozenset(p) for p in HE_PAIRS}
_CHONG_SET = {frozenset(p) for p in CHONG_PAIRS}

# 化凶之七（《增删卜易》源L948「凡用神原神动化回头克、化绝、化墓、化空、化鬼、化退神皆为化凶」
# 的枚举，只列引擎已能结构化识别的形态）
HUA_XIONG = ("化退神", "化绝", "化墓", "化空", "回头克", "化鬼")


def _he(a: str, b: str) -> bool:
    return frozenset((a, b)) in _HE_SET


def _chong(a: str, b: str) -> bool:
    return frozenset((a, b)) in _CHONG_SET


def _month_state(element: str, month_element: str) -> str:
    """月令下的旺/相/休/囚/死（五行同法：同我旺、我生相、生我休、克我囚、我克死）。

    只用于**无力判定**，取《增删卜易》源L551「以上元神无力生用神，无用之元神也，虽有如无」
    的"休囚"口径，不引入新的量纲。
    """
    if not month_element or not element:
        return ""
    if element == month_element:
        return "旺"
    if SHENG_CYCLE.get(month_element) == element:
        return "相"
    if SHENG_CYCLE.get(element) == month_element:
        return "休"
    if KE_CYCLE.get(month_element) == element:
        return "囚"
    if KE_CYCLE.get(element) == month_element:
        return "死"
    return ""


def _world_line(lines: list[dict]) -> dict | None:
    return next((y for y in lines if isinstance(y, dict) and y.get("is_world")), None)


def _broken(branch: str, month_branch: str, empty_branches: list[str]) -> bool:
    return branch in (empty_branches or []) or _chong(branch, month_branch)
