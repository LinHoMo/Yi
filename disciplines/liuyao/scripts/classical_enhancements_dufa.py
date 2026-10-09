# -*- coding: utf-8 -*-
"""六爻古典增强：独发 / 独静识别域（自 classical_enhancements.py 按域切出）。

巨石看门狗（学科 .py > 2200 行）触发后的拆分：独发独静只依赖 narrative_utils 的
断语素材与本模块内的卦爻结构判定，与其他增强域（伏神/暗动/三合/长生）无耦合，
单独成域依赖最单向：classical_enhancements → 本模块 → narrative_utils。

断语素材（引文/标签句）一律取自 `data/rules/verdict_texts.json`
（经 narrative_utils 加载），代码内不写字面量。
"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

from narrative_utils import (  # noqa: E402
    DUFA_NOTES,
    DUFA_QUOTE,
    _pos_to_name,
)

__all__ = ["analyze_du_fa_du_jing"]


def analyze_du_fa_du_jing(result):
    """独发 / 独静 识别（《增删卜易·独发章第三十一》）。

    原书："五爻俱動，一爻不動，謂之獨靜；五爻不動，一爻獨動，謂之獨發。"
    但同章野鹤紧接着立界："事之成敗，由乎用神；應期遲速，亦由乎用神……如捨其
    用神，執之而決事者，謬也。"——故此处**只标象、给结构性提示，不改吉凶主判**，
    亦不进主分：独发之爻为事情主驱动力、独静之爻为事情枢纽，仅作正文辅助说明。

    返回 {type, position, name, branch, six_relation, is_use_god, is_world,
          driving_note, classical_quote, count}；非独发独静时 type 为 ""。
    """
    out = {
        "type": "",
        "position": None,
        "name": "",
        "branch": "",
        "six_relation": "",
        "is_use_god": False,
        "is_world": False,
        "driving_note": "",
        "classical_quote": DUFA_QUOTE,
        "count": {"moving": 0, "static": 0},
    }

    hex_info = result.get("original_hexagram")
    if not isinstance(hex_info, dict):
        return out
    yao_lines = hex_info.get("yao_lines", []) or []
    if len(yao_lines) != 6:
        return out

    moving = [y for y in yao_lines if isinstance(y, dict) and y.get("is_moving")]
    static = [y for y in yao_lines if isinstance(y, dict) and not y.get("is_moving")]
    out["count"] = {"moving": len(moving), "static": len(static)}

    target = None
    if len(moving) == 1 and len(static) == 5:
        out["type"] = "独发"
        target = moving[0]
    elif len(static) == 1 and len(moving) == 5:
        out["type"] = "独静"
        target = static[0]
    else:
        return out

    step2 = result.get("_step2_data") if isinstance(result.get("_step2_data"), dict) else {}
    use_god_branch = ""
    sel = step2.get("selected_use_god") or {}
    if isinstance(sel, dict):
        use_god_branch = sel.get("earthly_branch", "")

    out["position"] = target.get("position")
    out["name"] = target.get("name") or _pos_to_name(target.get("position") or 0)
    out["branch"] = target.get("earthly_branch", "")
    out["six_relation"] = target.get("six_relation", "")
    out["is_use_god"] = bool(use_god_branch) and out["branch"] == use_god_branch
    out["is_world"] = bool(target.get("is_world"))

    # 只作结构提示：是否临用神/世爻，决定"主驱动力"还是"核心阻滞点"落在何处
    if out["type"] == "独发":
        role = "用神自为发动" if out["is_use_god"] else ("世爻发动" if out["is_world"] else "他爻发动")
        out["driving_note"] = DUFA_NOTES["du_fa"].format(
            name=out["name"], branch=out["branch"], role=role)
    else:
        role = "用神独静" if out["is_use_god"] else ("世爻独静" if out["is_world"] else "他爻独静")
        out["driving_note"] = DUFA_NOTES["du_jing"].format(
            name=out["name"], branch=out["branch"], role=role)
    return out
