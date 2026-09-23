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

from chain_support import _branch_element, _pos_to_name, get_empty_branches, safe_get
from chain_tables import TRIGRAM_ELEMENT

def step1_read_situation(r: dict) -> dict:
    """
    Step 1: 观局 — 读取并报告卦象事实。此步骤不做任何解释。

    仅从原始数据中提取以下信息：
    - 本卦名、宫、世代
    - 上卦/下卦
    - 世爻/应爻位置
    - 各爻的六神
    - 动爻及其位置
    - 变卦（如有）
    - 旬空地支
    - 日月建信息
    """
    hex_info = safe_get(r, "original_hexagram", default={})
    div_time = safe_get(r, "divination_time", default={})
    changed = safe_get(r, "changed_hexagram", default={})
    yao_lines = safe_get(hex_info, "yao_lines", default=[])

    # 基本卦信息
    hex_name = safe_get(hex_info, "name", default="未知")
    palace = safe_get(hex_info, "palace", default="未知")
    palace_element = safe_get(hex_info, "palace_element", default="未知")
    generation = safe_get(hex_info, "generation", default="未知")
    upper_trigram = safe_get(hex_info, "upper_trigram", default="未知")
    lower_trigram = safe_get(hex_info, "lower_trigram", default="未知")

    # 日月建
    month_stem_branch = safe_get(div_time, "month_stem_branch", default="")
    day_stem_branch = safe_get(div_time, "day_stem_branch", default="")
    # 提取日干（用于旬空计算）
    day_stem = day_stem_branch[:1] if day_stem_branch else ""
    month_stem = month_stem_branch[:1] if month_stem_branch else ""
    month_branch = month_stem_branch[1:] if month_stem_branch else ""
    day_branch = day_stem_branch[1:] if day_stem_branch else ""

    # 日月建五行
    month_element = _branch_element(month_branch)
    day_element = _branch_element(day_branch)

    # 旬空
    empty = safe_get(r, "empty_branches", default=[])
    if not empty and day_stem:
        empty = get_empty_branches(day_stem)

    # 世应位置
    world_pos = None
    response_pos = None
    for yao in yao_lines:
        if yao.get("is_world"):
            world_pos = yao.get("position")
        if yao.get("is_response"):
            response_pos = yao.get("position")

    # 动爻
    moving_lines = []
    for yao in yao_lines:
        if yao.get("is_moving"):
            moving_lines.append({
                "position": yao.get("position"),
                "name": _pos_to_name(yao.get("position", 0)),
                "six_relation": yao.get("six_relation", ""),
                "earthly_branch": yao.get("earthly_branch", ""),
                "six_spirit": yao.get("six_spirit", ""),
            })

    # 各爻六神信息
    spirits_report = []
    for yao in yao_lines:
        spirits_report.append({
            "position": yao.get("position"),
            "name": _pos_to_name(yao.get("position", 0)),
            "six_spirit": yao.get("six_spirit", ""),
            "six_relation": yao.get("six_relation", ""),
            "branch": yao.get("earthly_branch", ""),
        })

    # 变卦
    changed_hex_name = safe_get(changed, "name", default=None)

    # 格式化旬空和动爻为可读文本（避免 raw Python list repr 泄漏）
    if empty:
        empty_text = "、".join(empty)
    else:
        empty_text = "无"

    if moving_lines:
        ml_parts = []
        for m in moving_lines:
            pos_name = m.get("name", f"第{m.get('position','')}爻")
            rel = m.get("six_relation", "")
            branch = m.get("earthly_branch", "")
            ml_parts.append(f"{pos_name}({rel}{branch})")
        moving_text = "、".join(ml_parts)
    else:
        moving_text = "无"

    # 构建报告
    return {
        "hexagram_name": hex_name,
        "palace": palace,
        "palace_element": palace_element,
        "generation": generation,
        "upper_trigram": upper_trigram,
        "lower_trigram": lower_trigram,
        "upper_trigram_element": TRIGRAM_ELEMENT.get(upper_trigram, ""),
        "lower_trigram_element": TRIGRAM_ELEMENT.get(lower_trigram, ""),
        "world_position": world_pos,
        "response_position": response_pos,
        "world_name": _pos_to_name(world_pos) if world_pos else "",
        "response_name": _pos_to_name(response_pos) if response_pos else "",
        "month_stem_branch": month_stem_branch,
        "day_stem_branch": day_stem_branch,
        "month_element": month_element,
        "day_element": day_element,
        "month_branch": month_branch,
        "day_branch": day_branch,
        "empty_branches": empty,
        "moving_lines": moving_lines,
        "moving_count": len(moving_lines),
        "changed_hexagram": changed_hex_name,
        "spirits_report": spirits_report,
        "yao_lines_detail": [
            {
                "position": yao.get("position"),
                "name": _pos_to_name(yao.get("position", 0)),
                "earthly_branch": yao.get("earthly_branch", ""),
                "heavenly_stem": yao.get("heavenly_stem", ""),
                "six_relation": yao.get("six_relation", ""),
                "six_spirit": yao.get("six_spirit", ""),
                "is_moving": yao.get("is_moving", False),
                "is_world": yao.get("is_world", False),
                "is_response": yao.get("is_response", False),
                "is_empty": yao.get("is_empty", False),
                "is_month_break": yao.get("is_month_break", False),
                "nature": yao.get("nature", ""),
            }
            for yao in yao_lines
        ],
        "summary_text": (
            f"本卦：{hex_name}（{palace}，{palace_element}），"
            f"上{upper_trigram}下{lower_trigram}，"
            f"世在{safe_get(hex_info, 'name', default='')}第{world_pos}爻，"
            f"应在第{response_pos}爻。"
            f"月建{month_stem_branch}（{month_element}），"
            f"日辰{day_stem_branch}（{day_element}），"
            f"旬空{empty_text}。"
            f"动爻{moving_text}。"
            f"{'变卦：' + changed_hex_name if changed_hex_name else '无变卦'}"
        ),
    }

