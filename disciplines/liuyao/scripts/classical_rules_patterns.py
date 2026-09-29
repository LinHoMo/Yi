# -*- coding: utf-8 -*-
"""古典断法增强：表 / 通用辅助 / 18 项断法 / 聚合入口 enhance_reading。（拆分自 classical_analysis.py，纯搬移不改逻辑；聚合入口见 classical_analysis.py）。"""

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel, kernel_dir

_ensure_kernel(__file__)

from yishu_core.najia import najia_branch

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
)

from classical_support import _branch_element, _combined_strength, _element_to_relation, _find_stage_at, _find_use_god_positions, _get_use_god_strength_level, _infer_use_god_category, _pos_to_name, _relation_element, _score_fanyin, _score_fuyin, _strength_score, determine_six_relation, element_strength_in_month, find_hexagram_body, g_day_cn, get_changed_hexagram_branch, get_month_strength_description, get_stages_of_interest, get_twelve_growth_stage, is_ba_zu_chong, is_ba_zu_he
from classical_tables import KE_WO, SAN_HE, SELF_PUNISHMENTS, SHENG_WO, SIX_RELATIONS, THREE_PUNISHMENTS_CYCLIC, THREE_PUNISHMENTS_MUTUAL, TRANSFORMATION_PATTERNS, TWELVE_GROWTH
from chain_verdicts import PATTERN_NOTES_EXTRA,  PATTERN_VERDICTS, CLASSICAL_INTERPRETATIONS as CINTERP, CLASSICAL_RULES_NOTES as _CR_NOTES, CLASSICAL_RULES_TEMPLATES as _CR_TPL


def ctext(key: str, **fmt) -> str:
    """取 classical_rules 可交付断语；key 见 data/rules/verdict_texts.json#classical_rules_notes。"""
    entry = _CR_NOTES[key]
    text = entry["text"]
    return text.format(**fmt) if fmt else text



def ctpl(key: str, *args) -> str:
    """取 classical_rules 拼装句模板；{0}{1}… 为位置参数。"""
    text = _CR_TPL[key]["text"]
    return text.format(*args) if args else text


def analyze_wandering_returning_soul(result):
    """
    游魂归魂卦特殊断法。

    游魂卦/归魂卦是各宫第7、8卦，具有特殊的卦类特质：
    - 游魂：行无定、忧疑不安、心无归宿
    - 归魂：回故乡、有归属、终有所归

    参考《卜筮正宗》：
    > "游魂行无定，归魂回故乡。"
    > "游魂卦主在外、不安、忧疑、反复。"
    > "归魂卦主在内、有归、安定、终有所归。"

    此分析不改变评分（score_adjustment=0），仅提供断卦方向指引。

    返回:
        {
            "is_soul_hexagram": bool,
            "soul_type": str or None,       # "游魂" / "归魂" / None
            "meaning": str,                  # 卦类整体含义
            "travel": str,                   # 出行断法
            "residence": str,                # 居家断法
            "mind": str,                     # 心境断法
            "score_adjustment": 0,           # 不改变评分
        }
    """
    hex_info = result.get("original_hexagram", {})
    hex_name = hex_info.get("name", "")
    generation = hex_info.get("generation", "")

    # 游魂/归魂的卦类特质
    SOUL_GEN = {
        "游魂": {
            "meaning": CINTERP["youhun"]["text"],
            "travel": CINTERP["youhun_traits"]["text"],
            "residence": CINTERP["youhun_trait_home"]["text"],
            "mind": CINTERP["youhun_trait_mind"]["text"],
        },
        "归魂": {
            "meaning": CINTERP["guihun"]["text"],
            "travel": CINTERP["guihun_traits"]["text"],
            "residence": CINTERP["guihun_trait_home"]["text"],
            "mind": CINTERP["guihun_trait_mind"]["text"],
        },
    }

    soul_data = SOUL_GEN.get(generation)

    if soul_data:
        return {
            "is_soul_hexagram": True,
            "soul_type": generation,
            "meaning": soul_data["meaning"],
            "travel": soul_data["travel"],
            "residence": soul_data["residence"],
            "mind": soul_data["mind"],
            "summary": ctpl("crt_014", generation, soul_data['meaning'], CINTERP['youhun_dynamic']['text'] if generation == '游魂' else CINTERP['guihun_dynamic']['text']),
            "score_adjustment": 0,  # 不改变评分——仅为断卦方向指引
        }

    return {
        "is_soul_hexagram": False,
        "soul_type": None,
        "meaning": CINTERP["not_youhun_guihun"]["text"],
        "travel": PATTERN_VERDICTS["no_youhun_guihun"],
        "residence": PATTERN_VERDICTS["no_youhun_guihun"],
        "mind": PATTERN_VERDICTS["no_youhun_guihun"],
        "summary": CINTERP["not_youhun_guihun_summary"]["text"],
        "score_adjustment": 0,
    }


def analyze_monthly_break(result):
    """
    月破分析：某爻地支被月建冲则为月破。
    
    返回：
        {
            "has_monthly_break": bool,
            "details": [
                {
                    "position": int,
                    "name": str,
                    "branch": str,
                    "element": str,
                    "six_relation": str,
                    "is_moving": bool,
                    "is_empty": bool,
                    "day_branch": str,
                    "both_broken": bool,    # 同时被日冲+月冲
                    "salvageable": bool,    # 是否可救（日辰生扶或旺相）
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
        return {"has_monthly_break": False, "details": [], "summary": ctext("cr_018")}

    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    if not month_branch:
        return {"has_monthly_break": False, "details": [], "summary": ctext("cr_021")}

    day_element = _branch_element(day_branch)
    month_element = _branch_element(month_branch)
    empty_branches = result.get("empty_branches", [])

    details = []
    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        if not branch:
            continue

        if is_ba_zu_chong(branch, month_branch):
            elem = _branch_element(branch)
            is_moving = yao.get("is_moving", False)
            is_empty = branch in empty_branches
            both_broken = is_ba_zu_chong(branch, day_branch)

            # 判断是否有救
            salvageable = False
            month_str = element_strength_in_month(elem, month_element)
            day_str = element_strength_in_month(elem, day_element)

            # 日辰生扶或旺相可救
            if day_str in ("旺", "相"):
                salvageable = True
            if SHENG_WO.get(day_element) == elem or SHENG_CYCLE.get(day_element) == elem:
                # 日辰生之
                salvageable = True

            desc_parts = []
            if both_broken:
                desc_parts.append(
                    ctpl("crt_061", _pos_to_name(yao['position']), branch)
                )
            else:
                desc_parts.append(
                    ctpl("crt_062", _pos_to_name(yao['position']), branch)
                )

            if salvageable:
                desc_parts.append(ctpl("crt_063", day_branch))
            else:
                desc_parts.append(ctext("cr_022"))

            if is_moving:
                desc_parts.append(ctext("cr_023"))
            if is_empty:
                desc_parts.append(ctext("cr_024"))

            relation_str = yao.get("six_relation", "")
            details.append({
                "position": yao["position"],
                "name": yao.get("name", ""),
                "branch": branch,
                "element": elem,
                "six_relation": relation_str,
                "six_spirit": yao.get("six_spirit", ""),
                "is_moving": is_moving,
                "is_empty": is_empty,
                "month_branch": month_branch,
                "day_branch": day_branch,
                "both_broken": both_broken,
                "month_strength": month_str,
                "day_strength": day_str,
                "salvageable": salvageable,
                "description": "，".join(desc_parts),
            })

    if not details:
        return {"has_monthly_break": False, "details": [], "summary": ctext("cr_025")}

    summary = "；".join(d["description"] for d in details)
    return {"has_monthly_break": True, "details": details, "summary": summary}


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


def analyze_advance_retreat(result):
    """
    进出神分析：动爻化进则势盛，化退则势衰。
    
    返回：
        {
            "has_advance_retreat": bool,
            "details": [
                {
                    "position": int,
                    "name": str,
                    "original_branch": str,
                    "changed_branch": str,
                    "type": "化进" or "化退" or "回头合" or "回头克" or "回头生" or "化泄" or "无进退",
                    "six_relation": str,
                    "six_spirit": str,
                    "description": str,
                },
                ...
            ],
            "summary": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    changed = result.get("changed_hexagram") or {}
    changed_name = changed.get("name")

    if not yao_lines or not changed_name:
        return {"has_advance_retreat": False, "details": [], "summary": ctext("cr_027")}

    # 获取月建日辰五行用于旺衰评分
    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    month_elem = BRANCH_ELEMENTS.get(month_branch, "")
    day_elem = BRANCH_ELEMENTS.get(day_branch, "")

    details = []
    for yao in yao_lines:
        if not yao.get("is_moving", False):
            continue

        pos = yao.get("position", 0)
        orig_branch = yao.get("earthly_branch", "")

        # 变卦中该位置的地支
        chg_branch = get_changed_hexagram_branch(changed_name, pos)
        if not chg_branch:
            continue

        # 判断进退
        advance_score = 0.0
        if ADVANCE_PAIRS.get(orig_branch) == chg_branch:
            advance_type = "化进"
            desc = (
                ctpl("crt_018", _pos_to_name(pos), orig_branch, chg_branch)
            )
        elif RETREAT_PAIRS.get(orig_branch) == chg_branch:
            advance_type = "化退"
            desc = (
                ctpl("crt_049", _pos_to_name(pos), orig_branch, chg_branch)
            )
        else:
            # 检查 回头合/回头克/回头生/化泄
            orig_elem = BRANCH_ELEMENTS.get(orig_branch, "")
            chg_elem = BRANCH_ELEMENTS.get(chg_branch, "")
            he_pair_match = ((orig_branch, chg_branch) in HE_PAIRS or
                             (chg_branch, orig_branch) in HE_PAIRS)
            if he_pair_match:
                advance_type = "回头合"
                desc = (
                    ctpl("crt_066", _pos_to_name(pos), orig_branch, chg_branch)
                )
            elif KE_CYCLE.get(chg_elem) == orig_elem:
                advance_type = "回头克"
                desc = (
                    ctpl("crt_081", _pos_to_name(pos), orig_branch, chg_branch)
                )
            elif SHENG_CYCLE.get(chg_elem) == orig_elem:
                advance_type = "回头生"
                desc = (
                    ctpl("crt_090", _pos_to_name(pos), orig_branch, chg_branch)
                )
            elif SHENG_CYCLE.get(orig_elem) == chg_elem:
                advance_type = "化泄"
                desc = (
                    ctpl("crt_093", _pos_to_name(pos), orig_branch, chg_branch)
                )
            else:
                advance_type = "无进退"
                desc = (
                    ctpl("crt_094", _pos_to_name(pos), orig_branch, chg_branch)
                )

        # ── 进退神五行力量量化（《增删卜易》） ──
        orig_elem = BRANCH_ELEMENTS.get(orig_branch, "")
        chg_elem = BRANCH_ELEMENTS.get(chg_branch, "")

        advance_orig_strength = _combined_strength(orig_elem, month_elem, day_elem)
        advance_orig_val = _strength_score(advance_orig_strength)
        advance_chg_strength = _combined_strength(chg_elem, month_elem, day_elem)
        advance_chg_val = _strength_score(advance_chg_strength)

        if advance_type == "化进":
            base_score = 2.0
            if advance_orig_val >= 4:
                base_score += 1.0  # 旺进有力
            elif advance_orig_val <= 2:
                base_score -= 0.5  # 休囚进而力微
            if advance_chg_val >= 4:
                base_score += 0.5  # 变爻旺，力量传导强
            # 逢冲减半
            if is_ba_zu_chong(orig_branch, day_branch) or is_ba_zu_chong(orig_branch, month_branch):
                base_score *= 0.5
                desc += "，逢冲减半"
            advance_score = base_score

        elif advance_type == "化退":
            base_score = -2.0
            if advance_orig_val >= 4:
                base_score += 0.5  # 旺退力弱（减衰减缓）
            elif advance_orig_val <= 2:
                base_score -= 0.5  # 休囚退而更凶
            if advance_chg_val <= 1:
                base_score -= 0.5  # 退入绝地，更凶
            # 逢冲加速退
            if is_ba_zu_chong(chg_branch, day_branch):
                base_score *= 0.7
                desc += "，逢冲加速退"
            advance_score = base_score

        details.append({
            "position": pos,
            "name": yao.get("name", ""),
            "original_branch": orig_branch,
            "changed_branch": chg_branch,
            "type": advance_type,
            "six_relation": yao.get("six_relation", ""),
            "six_spirit": yao.get("six_spirit", ""),
            "advance_score": advance_score,
            "advance_orig_strength": advance_orig_strength,
            "advance_chg_strength": advance_chg_strength,
            "description": desc,
        })

    if not details:
        return {"has_advance_retreat": False, "details": [], "summary": ctext("cr_028")}

    summary = "；".join(d["description"] for d in details)
    return {"has_advance_retreat": True, "details": details, "summary": summary}


def analyze_twelve_growth(result):
    """
    十二长生分析：各爻在十二长生中的位置。
    
    返回：
        {
            "day_branch": str,
            "day_element": str,
            "lines": [
                {
                    "position": int,
                    "name": str,
                    "branch": str,
                    "element": str,
                    "six_relation": str,
                    "growth_stage": str,
                    "is_key_stage": bool,
                    "stage_meaning": str,
                },
                ...
            ],
            "summary": str,
            "key_lines": [int],  # 处于帝旺/长生/临官的关键爻位
            "weak_lines": [int], # 处于死/墓/绝的弱爻位
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    if not yao_lines:
        return {"day_branch": "", "day_element": "", "lines": [],
                "summary": ctext("cr_018"), "key_lines": [], "weak_lines": []}

    dt = result.get("divination_time", {})
    day_sb = dt.get("day_stem_branch", "")
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""
    if not day_branch:
        return {"day_branch": "", "day_element": "", "lines": [],
                "summary": ctext("cr_019"), "key_lines": [], "weak_lines": []}

    day_element = _branch_element(day_branch)
    empty_branches = result.get("empty_branches", [])

    # 关键阶段含义
    stage_meaning = {
        "长生": CINTERP["twelve_changsheng"]["长生"]["text"],
        "沐浴": CINTERP["twelve_changsheng"]["沐浴"]["text"],
        "冠带": CINTERP["twelve_changsheng"]["冠带"]["text"],
        "临官": CINTERP["twelve_changsheng"]["临官"]["text"],
        "帝旺": CINTERP["twelve_changsheng"]["帝旺"]["text"],
        "衰": CINTERP["twelve_changsheng"]["衰"]["text"],
        "病": CINTERP["twelve_changsheng"]["病"]["text"],
        "死": CINTERP["twelve_changsheng"]["死"]["text"],
        "墓": CINTERP["twelve_changsheng"]["墓"]["text"],
        "绝": CINTERP["twelve_changsheng"]["绝"]["text"],
        "胎": CINTERP["twelve_changsheng"]["胎"]["text"],
        "养": CINTERP["twelve_changsheng"]["养"]["text"],
    }

    lines_out = []
    key_lines = []
    weak_lines = []

    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        elem = _branch_element(branch)
        stage = get_twelve_growth_stage(elem, day_branch)
        is_key = get_stages_of_interest(stage)

        is_weak_stage = stage in ("死", "墓", "绝")
        is_strong_stage = stage in ("帝旺", "临官", "长生")

        if is_weak_stage:
            weak_lines.append(yao["position"])
        if is_strong_stage:
            key_lines.append(yao["position"])

        lines_out.append({
            "position": yao["position"],
            "name": yao.get("name", ""),
            "branch": branch,
            "element": elem,
            "six_relation": yao.get("six_relation", ""),
            "growth_stage": stage,
            "is_key_stage": is_key,
            "stage_meaning": stage_meaning.get(stage, ""),
        })

    # 汇总
    parts = []
    if key_lines:
        key_desc = "、".join(f"{_pos_to_name(p)}{_find_stage_at(lines_out, p)}"
                            for p in key_lines)
        parts.append(ctpl("crt_019", key_desc))
    if weak_lines:
        weak_desc = "、".join(f"{_pos_to_name(p)}{_find_stage_at(lines_out, p)}"
                             for p in weak_lines)
        parts.append(ctpl("crt_020", weak_desc))

    summary = "；".join(parts) if parts else PATTERN_VERDICTS["yao_states_calm"]

    return {
        "day_branch": day_branch,
        "day_element": day_element,
        "lines": lines_out,
        "summary": summary,
        "key_lines": key_lines,
        "weak_lines": weak_lines,
    }


def analyze_desperate_relief(result):
    """
    绝处逢生分析：当用神在日辰处逢"绝"或"死"地时，检查原神是否发动来生。

    若原神发动且有力 → "绝处逢生"（凶中反吉，+2.0）
    若原神发动但无力 → "绝处逢生但原神无力"（+0.5）
    若原神未发动但现于卦中 → "绝地待原神"（+0.2）
    若原神不现或旬空/月破 → "绝地无救"（-0.8）

    返回：
        {
            "has_desperate_relief": bool,
            "stage": str,               # "绝" / "死" / ""
            "yuan_shen_moving": bool,   # 原神是否发动
            "yuan_shen_strength": str,  # 原神综合旺衰
            "verdict": str,             # 断语标签
            "score_modifier": float,    # 分数修正
            "description": str,
        }
    """
    out = {
        "has_desperate_relief": False,
        "stage": "",
        "yuan_shen_moving": False,
        "yuan_shen_strength": "",
        "verdict": "",
        "score_modifier": 0.0,
        "description": "",
    }

    # Guard: requires original_hexagram and divination_time
    hex_info = result.get("original_hexagram")
    if not hex_info or not isinstance(hex_info, dict):
        return out

    yao_lines = hex_info.get("yao_lines", [])
    if not yao_lines:
        return out

    div_time = result.get("divination_time", {})
    day_sb = div_time.get("day_stem_branch", "")
    month_sb = div_time.get("month_stem_branch", "")
    day_branch = day_sb[1:] if isinstance(day_sb, str) and len(day_sb) >= 2 else ""
    month_branch = month_sb[1:] if isinstance(month_sb, str) and len(month_sb) >= 2 else ""
    if not day_branch:
        return out

    # ── Determine 用神 element ──
    use_god_element = ""
    # Prefer _step2_data (thinking chain) if present (put there by analyze)
    step2_data = result.get("_step2_data")
    if isinstance(step2_data, dict):
        use_god_element = step2_data.get("use_god_element", "")
        use_god_position = step2_data.get("use_god_position")
    else:
        use_god_position = None

    # Fallback: use 世爻 element
    if not use_god_element:
        for yao in yao_lines:
            if yao.get("is_world"):
                use_god_element = _branch_element(yao.get("earthly_branch", ""))
                break

    if not use_god_element:
        return out

    # ── Determine use-god position's branch for exact stage lookup ──
    use_god_branch = ""
    if use_god_position:
        for yao in yao_lines:
            if yao.get("position") == use_god_position:
                use_god_branch = yao.get("earthly_branch", "")
                break
    if not use_god_branch:
        # Fallback when position is unknown: use the 世爻 branch directly
        for yao in yao_lines:
            if yao.get("is_world"):
                use_god_branch = yao.get("earthly_branch", "")
                break
    if not use_god_branch:
        return out

    # ── Lookup 十二长生 stage ──
    tg = TWELVE_GROWTH.get(use_god_element)
    if not tg:
        return out

    stage = tg.get(day_branch, "")

    if stage not in ("绝", "死"):
        return out

    out["has_desperate_relief"] = True
    out["stage"] = stage

    # ── Determine 原神 element (the element that generates 用神) ──
    yuan_shen_element = SHENG_WO.get(use_god_element, "")
    if not yuan_shen_element:
        return out

    # ── Check 原神 status in the hexagram ──
    empty_branches = result.get("empty_branches", [])
    month_element = _branch_element(month_branch) if month_branch else _branch_element(day_branch)
    day_element = _branch_element(day_branch)

    yuan_shen_present = False
    yuan_shen_moving = False
    yuan_shen_empty = False
    yuan_shen_month_break = False
    yuan_shen_combined = "休"

    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        elem = _branch_element(branch)
        if elem != yuan_shen_element:
            continue
        yuan_shen_present = True
        if yao.get("is_moving", False):
            yuan_shen_moving = True
        if branch in empty_branches:
            yuan_shen_empty = True
        if month_branch and is_ba_zu_chong(branch, month_branch):
            yuan_shen_month_break = True

        # Compute combined strength (first match is enough — they share element)
        yuan_shen_combined = _combined_strength(yuan_shen_element, month_element, day_element)

    # If 原神 not found in main hexagram, check 伏藏 (hidden spirit analysis)
    if not yuan_shen_present:
        adv = result.get("advanced_analysis")
        if isinstance(adv, dict):
            hs_analysis = adv.get("hidden_spirit_analysis", {})
            if isinstance(hs_analysis, dict):
                details = hs_analysis.get("details", [])
                for detail in details:
                    hs = detail.get("hidden_spirit", {}) or {}
                    hs_elem = hs.get("element", "") or _branch_element(hs.get("branch", ""))
                    if hs_elem == yuan_shen_element:
                        yuan_shen_present = True
                        # 伏藏之原神 is dormant; not actively moving
                        yuan_shen_combined = element_strength_in_month(
                            yuan_shen_element, month_element
                        )
                        break

    out["yuan_shen_moving"] = yuan_shen_moving
    out["yuan_shen_strength"] = yuan_shen_combined

    # ── Apply judgment logic ──
    if yuan_shen_moving and yuan_shen_combined in ("旺", "相", "中和") and \
       not yuan_shen_empty and not yuan_shen_month_break:
        out["verdict"] = PATTERN_VERDICTS["jue_chu_feng_sheng"]
        out["score_modifier"] = 2.0
        out["description"] = (
            ctpl("crt_003", use_god_element, use_god_branch, stage, yuan_shen_element, yuan_shen_combined)
        )
    elif yuan_shen_moving and not yuan_shen_empty and not yuan_shen_month_break:
        out["verdict"] = PATTERN_VERDICTS["jue_chu_feng_sheng_weak_yuan"]
        out["score_modifier"] = 0.5
        out["description"] = (
            ctpl("crt_021", use_god_element, use_god_branch, stage, yuan_shen_element, yuan_shen_combined)
        )
    elif yuan_shen_present and not yuan_shen_empty and not yuan_shen_month_break:
        out["verdict"] = PATTERN_VERDICTS["jue_wait_yuan"]
        out["score_modifier"] = 0.2
        out["description"] = (
            ctpl("crt_050", use_god_element, use_god_branch, stage, yuan_shen_element)
        )
    elif not yuan_shen_present:
        out["verdict"] = PATTERN_VERDICTS["jue_no_save"]
        out["score_modifier"] = -0.8
        out["description"] = (
            ctpl("crt_067", use_god_element, use_god_branch, stage, yuan_shen_element)
        )
    else:
        # 原神 present but empty or month-broken
        out["verdict"] = PATTERN_VERDICTS["jue_no_save"]
        out["score_modifier"] = -0.8
        out["description"] = (
            ctpl("crt_068", use_god_element, use_god_branch, stage, yuan_shen_element, ctext('cr_031') if yuan_shen_empty else ctext('cr_032'))
        )

    return out


