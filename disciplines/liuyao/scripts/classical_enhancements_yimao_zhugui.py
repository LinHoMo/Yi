# -*- coding: utf-8 -*-
"""六爻古典增强：助鬼伤身（《易冒》助伤章）结构凶格（自 classical_enhancements.py 按域切出）。

【OPT-yimao_dz-02，2026-10-07 新增】

《易冒·助伤章第三十六》的「助鬼伤身」与《断易天机》同名格局**不同判定式**：
《易冒》判定式（源 L541 逐字）：
    「助鬼伤身，以世爻受鬼克，而鬼长生于日，是为引祸以自害。世亦称身，实世而非身也。」
即**世爻受官鬼克 + 官鬼长生于日辰 → 成局**。

**双修正**（源 L542 逐字）：
  「然官鬼遇空破者弗能伤，世爻逢旺相者弗能伤。」
  ① 鬼空/鬼破 → 弗能伤 → 不成局；
  ② 世旺相 → 弗能伤 → 不成局。

**用官占豁免**（源 L547）：
  「若女占夫而官星为用者，遇之反吉也；占官骤升，占武即发。」
  即用神恰为官鬼时（求官擢升类），不以「助鬼伤身」论凶——官鬼为用则不构成此格。

**只标象、不打分**（与 `classical_enhancements_zhugui.py` 同策略）：
  · 成立/不成立作为**结构事实**透出，交 narrate 作正文辅助说明；
  · **不改吉凶主判、不进主分**；
  · 断语素材（引文/标签句）取自 `data/rules/verdict_texts.json`
    的 `pattern_verdict_labels["助鬼伤身_易冒"]`（经 narrative_utils 加载），代码内不写字面量。
"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    BRANCH_ELEMENTS,
    KE_CYCLE,
    TWELVE_GROWTH_STAGES,
)

from narrative_utils import (  # noqa: E402
    PATTERN_VERDICT_LABELS,
    _pos_to_name,
    element_strength_in_month,
)

__all__ = ["analyze_zhu_gui_shang_shen_yimao"]

_LABELS = (PATTERN_VERDICT_LABELS.get("助鬼伤身_易冒") or {})


def _elem(branch: str) -> str:
    return BRANCH_ELEMENTS.get(branch, "")


def _gui_ke_shishen(gui_branch: str, world_palace_elem: str) -> bool:
    """官鬼爻五行是否克世爻宫五行。"""
    gui_el = _elem(gui_branch)
    if not gui_el or not world_palace_elem:
        return False
    return KE_CYCLE.get(gui_el) == world_palace_elem


def _gui_changsheng_ri(gui_branch: str, day_branch: str) -> bool:
    """官鬼五行是否长生于日支。

    十二长生：五行在日支的十二长生阶段为「长生」。
    取 TWELVE_GROWTH_STAGES，索引 0 对应长生。
    """
    gui_el = _elem(gui_branch)
    if not gui_el or not day_branch:
        return False
    from chart_tables import TWELVE_GROWTH_TABLES
    table = TWELVE_GROWTH_TABLES.get(gui_el)
    if table is None:
        return False
    try:
        idx = table.index(day_branch)
        return TWELVE_GROWTH_STAGES[idx] == "长生"
    except ValueError:
        return False


def analyze_zhu_gui_shang_shen_yimao(result):
    """助鬼伤身 易冒版结构判定（《易冒》助伤章，源 L541-L550）。

    成立三要件（全部为机械可判）：
      1. 世爻受官鬼克（源 L541：世爻受鬼克）；
      2. 官鬼长生于日（源 L541：鬼长生于日）；
      3. 双 correction 均不命中：
         a. 官鬼**不**空破（源 L542：鬼空破弗能伤）；
         b. 世爻**非**旺相（源 L542：世旺相弗能伤）。

    用官占豁免（源 L547）：用神恰为「官鬼」时，遇此格局不以凶论——
    「若女占夫而官星为用者，遇之反吉也；占官骤升，占武即发」。

    返回 {established, reason, shen_target, gui_moving, applicability,
          correction_a, correction_b, use_god_exempt, note, classical_quote}。
    **established 只表示「结构上是否成立」，不含任何吉凶判断，也不改主分。**
    """
    out = {
        "established": False,
        "reason": "",
        "shen_target": "",
        "gui_positions": [],
        "gui_branches": [],
        "gui_changsheng": False,
        "gui_empty": False,
        "gui_broken": False,
        "world_strong": False,
        "correction_a": False,   # 鬼空破 → 不成
        "correction_b": False,    # 世旺相 → 不成
        "use_god_exempt": False,  # 用官占豁免
        "note": "",
        "classical_quote": _LABELS.get("古典引文", ""),
    }

    hex_info = result.get("original_hexagram")
    if not isinstance(hex_info, dict):
        return out
    yao_lines = hex_info.get("yao_lines", []) or []
    if len(yao_lines) != 6:
        return out

    palace_element = hex_info.get("palace_element", "")

    # 世爻
    world = next((y for y in yao_lines
                  if isinstance(y, dict) and y.get("is_world")), None)
    if world is None:
        return out
    world_branch = world.get("earthly_branch") or ""

    # 日/月支
    dt = result.get("divination_time", {})
    day_sb = dt.get("day_stem_branch", "")
    month_sb = dt.get("month_stem_branch", "")
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    empty_branches = result.get("empty_branches", [])

    # 用官占豁免：取 result 的用神类别判断
    use_god_category = result.get("question_category", "")
    # 检查用神是否为官鬼（从 question_category 或 thinking_chain 推断）
    tc = result.get("thinking_chain") or {}
    s2 = tc.get("step2_use_god_identification") or {}
    if s2.get("use_god_category") == "官鬼" or use_god_category == "career":
        # 用官占豁免（源 L547）
        out["use_god_exempt"] = True
        out["reason"] = (
            f"用官占豁免：用神为官鬼（源L547「若女占夫而官星为用者，遇之反吉也；占官骤升，占武即发」）。"
            f"官鬼为用时不以助鬼伤身论凶。")
        return out

    # 要件1：世爻受鬼克
    guis = [y for y in yao_lines
            if isinstance(y, dict) and y.get("six_relation") == "官鬼"]
    gui_attacks = []
    for g in guis:
        gb = g.get("earthly_branch") or ""
        if _gui_ke_shishen(gb, palace_element):
            gui_attacks.append(g)

    if not gui_attacks:
        out["reason"] = "不构成助鬼伤身（源L541）：无官鬼克世爻（世不受鬼克）"
        return out

    # 要件2：鬼长生于日
    changsheng_guis = [g for g in gui_attacks
                       if _gui_changsheng_ri(g.get("earthly_branch") or "", day_branch)]
    out["gui_changsheng"] = bool(changsheng_guis)

    if not changsheng_guis:
        out["reason"] = (
            f"不构成助鬼伤身（源L541）：官鬼虽克世但无鬼长生于日"
            f"（日辰{day_branch}，源L543「虽曰长生，临于岁月动变之位者则非」）")
        return out

    # 双修正
    # 修正 a：鬼空破 → 弗能伤
    for g in changsheng_guis:
        gb = g.get("earthly_branch") or ""
        if gb in empty_branches:
            out["gui_empty"] = True
            out["correction_a"] = True
            break
        from classical_enhancements import is_ba_zu_chong as _cb
        if month_branch and _cb(gb, month_branch):
            out["gui_broken"] = True
            out["correction_a"] = True
            break

    if out["correction_a"]:
        reason_a = "鬼空" if out["gui_empty"] else "鬼破（月冲）"
        out["reason"] = (
            f"不构成助鬼伤身（源L542 修正一）：官鬼遇{reason_a}——"
            f"「然官鬼遇空破者弗能伤」")
        return out

    # 修正 b：世旺相 → 弗能伤
    if world_branch:
        world_el = _elem(world_branch)
        if world_el:
            world_month_strength = element_strength_in_month(world_el, _elem(month_branch))
            if world_month_strength in ("旺", "相"):
                out["world_strong"] = True
                out["correction_b"] = True
                out["reason"] = (
                    f"不构成助鬼伤身（源L542 修正二）：世爻{world_branch}"
                    f"「{world_month_strength}」——「世爻逢旺相者弗能伤」")
                return out

    # 三要件齐备 + 双修正均未命中 → 成局
    out["established"] = True
    out["shen_target"] = "世爻"
    out["gui_positions"] = [_pos_to_name(g.get("position") or 0) for g in changsheng_guis]
    out["gui_branches"] = [g.get("earthly_branch") or "" for g in changsheng_guis]

    out["reason"] = (
        f"助鬼伤身（易冒格）成立：世爻{world_branch}受官鬼"
        f"（{'、'.join(out['gui_branches'])}）克"
        f"且鬼长生于{day_branch}日（源L541「世爻受鬼克，而鬼长生于日」）；"
        f"双修正未命中——鬼不空破、世非旺相（源L542）")

    # 结构标签句（模板来自 verdict_texts.json）
    tpl = _LABELS.get("成立" if out["established"] else "不成立提示", "")
    if tpl:
        fmt_kwargs = {
            "world": world_branch,
            "gui_changsheng": "、".join(out["gui_branches"]),
            "d": day_branch,
            "branch_info": "、".join(f"{_pos_to_name(g.get('position') or 0)}{g.get('earthly_branch', '')}"
                                    for g in changsheng_guis),
            "correction_info": "鬼不空破+世非旺相",
            "use_god_info": "",
        }
        try:
            out["note"] = tpl.format(**fmt_kwargs)
        except (KeyError, IndexError):
            out["note"] = out["reason"]

    return out
