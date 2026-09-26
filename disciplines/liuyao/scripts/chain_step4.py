# -*- coding: utf-8 -*-
"""六爻思维链：基元表 / 断语库 / 通用辅助 / 五步推演 / 应期 / 叙事组装。（拆分自 thinking_chain.py，纯搬移不改逻辑；聚合入口见 thinking_chain.py）。"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel, kernel_dir

_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    ADVANCE_PAIRS,
    BRANCH_ELEMENTS,
    BREAK_PAIRS,
    CHONG_PAIRS,
    EARTHLY_BRANCHES,
    EIGHT_PALACES,
    HEAVENLY_STEMS,
    HEXAGRAM_TRIGRAMS,
    HE_PAIRS,
    KE_CYCLE,
    NAJIA_BRANCHES,
    RETREAT_PAIRS,
    SHENG_CYCLE,
    STEM_ELEMENTS,
    TOMB_MAP,
    palace_of_key,
    EARTHLY_BRANCHES as BRANCHES,
)

from datetime import datetime, timedelta

import json

import re

from pathlib import Path

from chain_step2 import _element_to_relation
from chain_support import _branch_element, _is_chong, _is_he, _pos_to_name, get_changed_hexagram_branch, get_relation_from_element, safe_get
from chain_tables import JUE_MAP, _HEXAGRAM_HARMONY_SET


from chain_step4_changes import (  # noqa: E402
    _compose_change_summary,
    _classify_line_role,
    _determine_change_type,
    _analyze_effect_on_use_god,
    _check_tan_sheng_wan_ke,
    _check_tan_he_wan_sheng_ke,
)
from chain_step4_patterns import (  # noqa: E402
    _detect_classical_illness_pattern,
    _detect_hexagram_harmony_clash_pattern,
    _detect_special_pattern,
    _forms_hexagram_harmony,
    _check_greedy_harmony,
)

def step4_analyze_changes(r: dict) -> dict:
    """
    Step 4: 察变 — 分析动爻及其影响。

    对每一动爻分析：
    1. 何六亲动？（原神？忌神？仇神？）
    2. 动化何种？（回头生/克/进退/化合/入墓/化绝）
    3. 对用神的净效应

    经典规则《黄金策》：
    - 回头生（变爻生动爻）：极为有利 → 原神回头生用尤佳
    - 回头克（变爻克动爻）：极为不利 → 用神回头克大凶
    - 化进神：势盛递增
    - 化退神：势衰递减
    - 化墓/化绝：困顿断绝
    - 六合（动爻与变爻合）：绊住（贪合忘生/克）

    贪生忘克：如有原神动，忌神贪生忘克用神。
    贪合忘生/克：动变相合则贪合忘其生克。
    """
    # 获取上下文
    hex_info = safe_get(r, "original_hexagram", default={})
    yao_lines = safe_get(hex_info, "yao_lines", default=[])
    changed = safe_get(r, "changed_hexagram", default={})
    changed_name = safe_get(changed, "name", default=None)
    palace_element = safe_get(hex_info, "palace_element", default="")

    # 获取日月建
    div_time = safe_get(r, "divination_time", default={})
    month_stem_branch = safe_get(div_time, "month_stem_branch", default="")
    day_stem_branch = safe_get(div_time, "day_stem_branch", default="")
    month_branch = month_stem_branch[1:] if len(month_stem_branch) >= 2 else ""
    day_branch = day_stem_branch[1:] if len(day_stem_branch) >= 2 else ""

    # 获取用神信息（从 step2）
    step2_data = safe_get(r, "_step2_data", default={})
    use_god_category = safe_get(step2_data, "use_god_category", default="")
    use_god_element = safe_get(step2_data, "use_god_element", default="")
    yuan_shen_element = safe_get(step2_data, "yuan_shen", "element", default="")
    ji_shen_element = safe_get(step2_data, "ji_shen", "element", default="")
    chou_shen_element = safe_get(step2_data, "chou_shen", "element", default="")

    # ---------- 4.1: 收集所有动爻信息 ----------
    moving_lines = [yao for yao in yao_lines if yao.get("is_moving", False)]

    # Check for 暗动 even in "static" hexagrams (no explicit moving lines)
    step3_hm_data = safe_get(r, "_step3_data", default={})
    hm_lines = step3_hm_data.get("hidden_movement", []) or []

    if not moving_lines and not hm_lines:
        return {
            "has_moving_lines": False,
            "moving_count": 0,
            "details": [],
            "favorable_changes": [],
            "unfavorable_changes": [],
            "tan_sheng_wan_ke": [],
            "tan_he_wan_sheng_ke": [],
            "greedy_harmony_issues": [],
            "greedy_harmony_score": 0.0,
            "net_effect": 0.0,
            "net_effect_description": "静卦无动爻，以用神旺衰论吉凶",
            "summary_text": "静卦，无动爻变化。吉凶专凭用神旺衰断之。",
        }

    # ---------- 4.2: 逐动爻分析 ----------
    details = []
    favorable_changes = []
    unfavorable_changes = []
    net_effect = 0.0

    for yao in moving_lines:
        pos = yao.get("position", 0)
        orig_branch = yao.get("earthly_branch", "")
        orig_relation = yao.get("six_relation", "")
        orig_element = _branch_element(orig_branch)
        orig_spirit = yao.get("six_spirit", "")

        # 获取变爻地支
        chg_branch = get_changed_hexagram_branch(changed_name, pos) if changed_name else None
        chg_element = _branch_element(chg_branch) if chg_branch else ""
        chg_relation = get_relation_from_element(chg_element, palace_element) if chg_element else ""

        # 判断动爻身份（相对于用神）
        line_role = _classify_line_role(
            orig_relation, use_god_category,
            orig_element, use_god_element,
            yuan_shen_element, ji_shen_element, chou_shen_element
        )

        # 判断变化类型
        change_type = _determine_change_type(
            orig_branch, chg_branch, orig_element, chg_element,
            month_branch, day_branch
        )

        # 分析对用神的直接/间接影响
        effect_on_usegod = _analyze_effect_on_use_god(
            orig_branch, chg_branch,
            orig_element, chg_element,
            use_god_element,
            change_type,
            line_role,
        )

        detail = {
            "position": pos,
            "name": _pos_to_name(pos),
            "original_branch": orig_branch,
            "original_element": orig_element,
            "original_relation": orig_relation,
            "original_spirit": orig_spirit,
            "line_role": line_role,
            "changed_branch": chg_branch,
            "changed_element": chg_element,
            "changed_relation": chg_relation,
            "change_type": change_type["type"],
            "change_detail": change_type["detail"],
            "effect_on_usegod": effect_on_usegod["description"],
            "effect_score": effect_on_usegod["score"],
        }
        details.append(detail)

        net_effect += effect_on_usegod["score"]

        if effect_on_usegod["score"] > 0:
            favorable_changes.append(detail)
        elif effect_on_usegod["score"] < 0:
            unfavorable_changes.append(detail)

    # ---------- 4.3: 贪生忘克/贪合忘生克规则 ----------
    tan_sheng_wan_ke = _check_tan_sheng_wan_ke(details, use_god_element, palace_element)
    tan_he_wan_sheng_ke = _check_tan_he_wan_sheng_ke(details, yao_lines, use_god_category)

    # 应用贪生忘克修正
    for rule in tan_sheng_wan_ke:
        detail = next((d for d in details if d["position"] == rule["detail_position"]), None)
        if detail:
            old_score = detail["effect_score"]
            detail["effect_score"] *= 0.5  # 减半效应
            detail["effect_on_usegod"] += f"（贪生忘克：{reason}）".replace("reason", rule["reason"])
            net_effect += (detail["effect_score"] - old_score)

    for rule in tan_he_wan_sheng_ke:
        detail = next((d for d in details if d["position"] == rule["detail_position"]), None)
        if detail:
            old_score = detail["effect_score"]
            detail["effect_score"] *= 0.5
            detail["effect_on_usegod"] += f"（贪合忘生克：{rule['reason']}）"
            net_effect += (detail["effect_score"] - old_score)

    # ---------- 4.3b: 贪合忘生克（日月合绊检查） ----------
    # Also include 暗动 lines for greedy harmony check
    step3_data_for_hm = safe_get(r, "_step3_data", default={})
    hm_lines = step3_data_for_hm.get("hidden_movement", []) or []
    # Combine moving lines with hidden-moved lines (as virtual moving lines for harmony check)
    all_active_lines = list(moving_lines)
    for hm in hm_lines:
        # Find the actual yao for this hidden-moved position
        for yl in yao_lines:
            if yl.get("position") == hm.get("position"):
                all_active_lines.append(yl)
                break

    greedy_harmony_score, greedy_harmony_issues = _check_greedy_harmony(
        yao_lines=all_active_lines,
        moving_lines=all_active_lines,
        day_branch=day_branch,
        month_branch=month_branch,
        use_god_category=use_god_category,
        yuan_shen_element=yuan_shen_element,
        ji_shen_element=ji_shen_element,
        palace_element=palace_element,
    )

    # Apply greedy harmony adjustment to net_effect
    net_effect += greedy_harmony_score

    # ---------- 4.3c: 进退神力量量化（来自 classical_analysis.advance_score） ----------
    # 当 enhance_reading 已运行时（advanced_analysis 存在），读取进退神数值评分
    advance_score_total = 0.0
    _advanced_data = r.get("advanced_analysis", {})
    if _advanced_data and isinstance(_advanced_data, dict):
        _ar_data = _advanced_data.get("advance_retreat", {})
        if isinstance(_ar_data, dict):
            for _ar_item in _ar_data.get("details", []):
                _ascore = _ar_item.get("advance_score", 0.0)
                if isinstance(_ascore, (int, float)) and _ascore != 0.0:
                    advance_score_total += _ascore
    if abs(advance_score_total) > 0.001:
        net_effect += advance_score_total

    # ---------- 4.4: 净效应判断 ----------
    net_effect = round(net_effect, 2)
    if net_effect >= 1.5:
        net_description = "大吉（动变全面有利）"
    elif net_effect >= 0.5:
        net_description = "偏吉（动变总体有利）"
    elif net_effect >= -0.5:
        net_description = "中性（动变利弊参半）"
    elif net_effect >= -1.5:
        net_description = "偏凶（动变总体不利）"
    else:
        net_description = "大凶（动变全面不利）"

    # Build greedy harmony description for summary
    greedy_harmony_summary = ""
    if greedy_harmony_issues:
        issue_descs = [i["effect"] for i in greedy_harmony_issues if i.get("score_effect", 0) != 0]
        if issue_descs:
            greedy_harmony_summary = "日月合绊：" + "、".join(issue_descs) + "；"

    return {
        "has_moving_lines": True,
        "moving_count": len(moving_lines),
        "details": details,
        "favorable_changes": favorable_changes,
        "unfavorable_changes": unfavorable_changes,
        "favorable_count": len(favorable_changes),
        "unfavorable_count": len(unfavorable_changes),
        "tan_sheng_wan_ke": tan_sheng_wan_ke,
        "tan_he_wan_sheng_ke": tan_he_wan_sheng_ke,
        "greedy_harmony_issues": greedy_harmony_issues,
        "greedy_harmony_score": greedy_harmony_score,
        "advance_score_total": round(advance_score_total, 2),
        "net_effect": net_effect,
        "net_effect_description": net_description,
        "summary_text": _compose_change_summary(
            moving_lines, favorable_changes, unfavorable_changes,
            tan_sheng_wan_ke, tan_he_wan_sheng_ke, greedy_harmony_summary,
            advance_score_total, net_effect, net_description,
        ),
    }



def _user_reason(text: str, fallback: str = "") -> str:
    """将开发者风格的 reason 精练为 ≤15 字的人话描述。"""
    if not text:
        return fallback
    s = re.sub(r'【[^】]*】', '', text)
    s = re.sub(r'\(x[\d.]+\)', '', s)
    s = re.sub(r'[（(]\d+\.?\d*[)）]', '', s)
    s = re.sub(r'（[^）]*）', '', s)
    s = re.sub(r'\s*[+-]\d+\.?\d*$', '', s)
    s = s.strip()
    if len(s) > 15:
        m = re.search(r'[，；、。]', s)
        if m and m.start() >= 4:
            s = s[:m.start()]
        else:
            s = s[:15]
    s = s.strip('，；、。')
    return s if s else fallback




__all__ = [
    "_compose_change_summary",
    "_classify_line_role",
    "_determine_change_type",
    "_analyze_effect_on_use_god",
    "_check_tan_sheng_wan_ke",
    "_check_tan_he_wan_sheng_ke",
    "_detect_classical_illness_pattern",
    "_detect_hexagram_harmony_clash_pattern",
    "_detect_special_pattern",
    "_forms_hexagram_harmony",
    "_check_greedy_harmony",
    "step4_analyze_changes",
    "_user_reason",
]
