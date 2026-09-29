# -*- coding: utf-8 -*-
"""古典断法增强：合 / 破局（三合局成局与破局判别）。（拆分自 classical_rules_patterns.py，纯搬移不改逻辑；门面见 classical_rules.py）。"""
import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel, kernel_dir

_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    TOMB_MAP,
)
from classical_support import _pos_to_name, is_ba_zu_chong
from classical_tables import SAN_HE
from chain_verdicts import PATTERN_NOTES_EXTRA, ctext, ctpl

def _check_broken_combo(combo_dict, day_branch, month_branch):
    """
    检查一个已完成的三合局是否被破坏。

    破局条件（《卜筮正宗》）：
      - 合局中一字被日/月冲 → 局破
      - 合局中一字入墓/逢绝 → 局力大减

    参数:
        combo_dict: {"element": str, "branches": [str,str,str], ...}
        day_branch: 日辰地支
        month_branch: 月建地支

    返回:
        {"status": "破局"/"完整", "issues": [...], "score_mod": float}
    """
    branches = combo_dict.get("branches", [])

    # 六冲映射
    CHONG_MAP = {
        "子": "午", "午": "子", "丑": "未", "未": "丑",
        "寅": "申", "申": "寅", "卯": "酉", "酉": "卯",
        "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
    }

    # 各五行入墓地支：真值源在内核 TOMB_MAP（模块顶部已 import），禁止就地重定义遮蔽。

    issues = []

    for b in branches:
        # 检查日冲
        if CHONG_MAP.get(b) == day_branch:
            issues.append(ctpl("crt_048", b))
        elif CHONG_MAP.get(b) == month_branch:
            issues.append(ctpl("crt_064", b))

    # 检查合局五行是否整体入墓于日辰
    target_element = combo_dict.get("element", "")
    if target_element and day_branch == TOMB_MAP.get(target_element, ""):
        issues.append(ctpl("crt_015", day_branch))

    if issues:
        return {"status": "破局", "severity": "减力", "issues": issues, "score_mod": -0.5}
    return {"status": "完整", "issues": [], "score_mod": 0}


def analyze_triple_combo(result):
    """
    三合局分析：检查是否存在申子辰(水)、寅午戌(火)、巳酉丑(金)、亥卯未(木)。
    增加破局检测：合局中一字被日/月冲或入墓时判定为破局。
    
    返回：
        {
            "has_triple_combo": bool,
            "details": [
                {
                    "element": str,         # 合局五行
                    "branches": [str, str, str],  # 合局三地支
                    "positions": [int, int, int], # 出现在哪些位置
                    "completeness": str,    # "完整"/"待日"/"待月"
                    "formation_type": str,  # "三爻齐发"/"二爻动+一静"/"二爻动+日/月补"
                    "description": str,
                },
                ...
            ],
            "summary": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    if not yao_lines:
        return {"has_triple_combo": False, "details": [], "summary": ctext("cr_018")}

    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""

    # 收集每个位置的地支和是否明动/暗动
    pos_branch = {}
    pos_moving = {}
    pos_hidden_move = {}  # 是否是暗动

    moving_positions = set()
    for yao in yao_lines:
        pos = yao.get("position", 0)
        branch = yao.get("earthly_branch", "")
        pos_branch[pos] = branch
        is_moving = yao.get("is_moving", False)
        pos_moving[pos] = is_moving
        if is_moving:
            moving_positions.add(pos)

    # 检查暗动
    hidden_move = set()
    for yao in yao_lines:
        pos = yao.get("position", 0)
        if pos_moving.get(pos, False):
            continue
        branch = yao.get("earthly_branch", "")
        if branch and is_ba_zu_chong(branch, day_branch):
            hidden_move.add(pos)

    # 所有有力爻的位置（明动 + 暗动）
    active_positions = moving_positions | hidden_move
    # 也包括静爻（三合可以以静爻参与），但我们只需要确认静爻有对应地支即可

    details = []

    for combo_element, combo_branches in SAN_HE.items():
        b1, b2, b3 = combo_branches

        # 找到每个地支在本卦中出现的位置
        pos_map = {b: [] for b in combo_branches}
        for pos, branch in pos_branch.items():
            if branch in pos_map:
                pos_map[branch].append(pos)

        # 检查是否能形成三合
        # 需要 b1, b2, b3 各至少在一个位置出现
        if any(len(pos_map[b]) == 0 for b in combo_branches):
            # 检查是否能由日/月补齐
            locations = {b: pos_map[b] for b in combo_branches if pos_map[b]}
            if len(locations) == 2:
                # 缺一个，看日/月是否有
                missing = [b for b in combo_branches if not pos_map[b]][0]
                if missing in (day_branch, month_branch):
                    # 由日/月补齐
                    valid_positions = []
                    for b in combo_branches:
                        if pos_map[b]:
                            valid_positions.append(pos_map[b][0])
                        elif b == day_branch:
                            valid_positions.append(ctpl("crt_095", day_branch))
                        elif b == month_branch:
                            valid_positions.append(ctpl("crt_097", month_branch))

                    # 需要至少两个明动的爻才成局
                    actual_pos = [p for p in valid_positions if isinstance(p, int)]
                    if len(actual_pos) >= 2:
                        formation = "二爻动+日/月补"
                        _combo_d = {
                            "element": combo_element,
                            "branches": combo_branches,
                        }
                        _broken = _check_broken_combo(_combo_d, day_branch, month_branch)
                        _desc = (
                            ctpl("crt_080", ''.join(combo_branches), combo_element, day_branch, month_branch)
                        )
                        if _broken["status"] == "破局":
                            _desc += ctpl("crt_017", '；'.join(_broken['issues']))
                        details.append({
                            "element": combo_element,
                            "branches": combo_branches,
                            "positions": valid_positions,
                            "completeness": "待日/月",
                            "formation_type": formation,
                            "combo_status": _broken["status"],
                            "combo_issues": _broken["issues"],
                            "combo_score_mod": _broken["score_mod"],
                            "description": _desc,
                        })
            continue

        # 三个地支都在本卦中
        # 取第一个出现的位置
        p1 = pos_map[b1][0]
        p2 = pos_map[b2][0]
        p3 = pos_map[b3][0]
        positions = [p1, p2, p3]

        # 判断参与方式：几个明动？几个暗动？几个静？
        moving_count = sum(1 for p in positions if p in moving_positions)
        hidden_count = sum(1 for p in positions if p in hidden_move)
        static_count = sum(1 for p in positions
                          if p not in moving_positions and p not in hidden_move)

        if moving_count >= 2 and hidden_count + static_count == 1:
            ftype = "二爻动+一静"
            completeness = "完整" if hidden_count == 0 and static_count == 1 else "完整"
        elif moving_count == 3:
            ftype = "三爻齐发"
            completeness = "完整"
        elif moving_count >= 1 or hidden_count >= 1:
            ftype = ctpl("crt_065", moving_count, hidden_count, static_count)
            completeness = "完整"
        else:
            ftype = "三爻皆静"
            # 三个静爻三合，名为"合局待用"，需日/月引动
            completeness = "待用（需冲引发）"

        # 如果有静爻但被暗动减轻
        _combo_d = {
            "element": combo_element,
            "branches": combo_branches,
        }
        _broken = _check_broken_combo(_combo_d, day_branch, month_branch)

        desc = (
            ctpl("crt_002", ''.join(combo_branches), combo_element, _pos_to_name(p1), _pos_to_name(p2), _pos_to_name(p3), ftype)
        )

        if completeness == "完整":
            desc += ctpl("crt_016", combo_element)
        elif completeness == "待用（需冲引发）":
            desc += PATTERN_NOTES_EXTRA["static_he_wait"]

        if _broken["status"] == "破局":
            desc += ctpl("crt_089", '；'.join(_broken['issues']))

        details.append({
            "element": combo_element,
            "branches": combo_branches,
            "positions": sorted(positions),
            "completeness": completeness,
            "formation_type": ftype,
            "moving_count": moving_count,
            "hidden_count": hidden_count,
            "static_count": static_count,
            "combo_status": _broken["status"],
            "combo_issues": _broken["issues"],
            "combo_score_mod": _broken["score_mod"],
            "description": desc,
        })

    if not details:
        return {"has_triple_combo": False, "details": [], "summary": ctext("cr_026")}

    summary = "；".join(d["description"] for d in details)
    return {"has_triple_combo": True, "details": details, "summary": summary}
