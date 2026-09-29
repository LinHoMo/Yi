# -*- coding: utf-8 -*-
"""古典断法增强：游魂归魂 / 月破 / 进退神。（2026-09-29 巨型模块拆分：合破局→`classical_rules_combo.py`、十二长生/绝处逢生→`classical_rules_growth.py`，纯搬移不改逻辑；门面见 classical_rules.py，聚合入口见 classical_analysis.py）。"""

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel, kernel_dir

_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    ADVANCE_PAIRS,
    BRANCH_ELEMENTS,
    HE_PAIRS,
    KE_CYCLE,
    RETREAT_PAIRS,
    SHENG_CYCLE,
)

from classical_support import _branch_element, _combined_strength, _pos_to_name, _strength_score, element_strength_in_month, get_changed_hexagram_branch, is_ba_zu_chong

from classical_tables import SHENG_WO

from chain_verdicts import PATTERN_VERDICTS, CLASSICAL_INTERPRETATIONS as CINTERP, ctext, ctpl


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

