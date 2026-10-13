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
    LUANDONG_LABELS,
    _pos_to_name,
)

__all__ = ["analyze_du_fa_du_jing", "analyze_luandong"]


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


# ---------------------------------------------------------------- 乱动卦（纯结构象）
# 【第一百六十七批】rule_registry liuyao.huozhulin_luandong 条「未实现_乱动标记」的落地。
# 纪律与独发独静**完全同策略**：只标结构象、不打分、不改用神选取、不改判定值。
# 为什么放在本模块：`du_fa_du_jing` 已经算出 count{moving,static}（唯一真值源），
# 另起一套数法就是第二个真值源——本条直接读它。
# **边界（勿越界）**：《火珠林》源L33 的取用口径「乱动之卦只取旺爻，旺爻即用神也」
# **未实现**——它须先裁定「旺」的量化与四看取舍序（见该条 gap_detail）。本条只报
# 「动爻多」这一结构事实，不据此取用神、不据此定吉凶。
LUANDONG_THRESHOLD = 2      # 动爻数 > 2 即乱动（与注册表 gap_detail 登记口径一致）


def analyze_luandong(result):
    """乱动卦识别（《火珠林·乱动法总纲》）。

    书源：《火珠林》源L33 逐字「乱动之卦只取旺爻，旺爻即用神也。生克吉凶皆在此爻。」；
    "独发易取，乱动难寻"——以「难寻」点明乱动与独发为难易之别。

    本判据**只取动爻数这一结构事实**（判据 >2），**不实现《火珠林》源L33 逐字「乱动之卦只取旺爻，旺爻即用神也」的取用口径**：
    那须先裁定「旺」的量化与四看取舍序，属另一立项（rule_registry 同条 gap_detail）。
    故此处只出「是否乱动」的标签与动爻位置，供叙述层提示，不进主分、不改判定值。

    返回 {is_luandong, moving_count, positions, classical_quote, note}。
    """
    out = {
        "is_luandong": False,
        "moving_count": 0,
        "positions": [],
        "classical_quote": LUANDONG_LABELS.get("古典引文", ""),
        "note": "",
    }
    hex_info = result.get("original_hexagram")
    if not isinstance(hex_info, dict):
        return out
    yao_lines = hex_info.get("yao_lines", []) or []
    if len(yao_lines) != 6:
        return out

    moving = [y for y in yao_lines if isinstance(y, dict) and y.get("is_moving")]
    out["moving_count"] = len(moving)
    out["positions"] = [y.get("position") for y in moving if isinstance(y.get("position"), int)]
    out["is_luandong"] = len(moving) > LUANDONG_THRESHOLD
    _pos = "、".join(f"{p}爻" for p in out["positions"]) or "无"
    out["note"] = (LUANDONG_LABELS.get("乱动提示" if out["is_luandong"] else "非乱动提示", "")
                   .format(n=len(moving), positions=_pos))
    return out
