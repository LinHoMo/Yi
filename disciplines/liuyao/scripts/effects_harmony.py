# -*- coding: utf-8 -*-
"""古典断法增强·effects_harmony.py（拆分自 classical_rules_effects，纯搬移不改逻辑；门面见 classical_rules_effects）。"""

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
from chain_verdicts import EFFECT_LABELS, EFFECT_PHRASES, CLASSICAL_INTERPRETATIONS as CINTERP, ctext, ctpl


def analyze_clash_harmony(result):
    """
    六合/六冲卦判断：
    - 检查各对应位置爻对(1-4, 2-5, 3-6)的地支关系
    - 全部合 → 六合卦
    - 全部冲 → 六冲卦
    - 部分合、部分冲 → 描述各异
    
    返回：
        {
            "hexagram_type": str,    # "六合卦"/"六冲卦"/"半合半冲"/"无明确合冲"
            "pairs": [
                {
                    "positions": (int, int),
                    "branches": (str, str),
                    "relation": str,    # "合"/"冲"/"无特殊"
                    "description": str,
                },
                ...
            ],
            "summary": str,
            "meaning": str,  # 六合/六冲的含义解释
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    if not yao_lines:
        return {"hexagram_type": "未知", "pairs": [], "summary": ctext("cr_018"), "meaning": ""}

    yao_by_pos = {y["position"]: y for y in yao_lines}

    # 三对对应位置
    pair_positions = [(1, 4), (2, 5), (3, 6)]
    pairs = []
    he_count = 0
    chong_count = 0

    for p1, p2 in pair_positions:
        y1 = yao_by_pos.get(p1, {})
        y2 = yao_by_pos.get(p2, {})
        b1 = y1.get("earthly_branch", "")
        b2 = y2.get("earthly_branch", "")

        if is_ba_zu_he(b1, b2):
            relation = "合"
            he_count += 1
            desc = (ctpl("crt_022", _pos_to_name(p1), _pos_to_name(p2), b1, b2))
        elif is_ba_zu_chong(b1, b2):
            relation = "冲"
            chong_count += 1
            desc = (ctpl("crt_051", _pos_to_name(p1), _pos_to_name(p2), b1, b2))
        else:
            relation = "无特殊"
            desc = (ctpl("crt_052", _pos_to_name(p1), _pos_to_name(p2), b1, b2))

        pairs.append({
            "positions": (p1, p2),
            "branches": (b1, b2),
            "relation": relation,
            "description": desc,
        })

    if he_count == 3:
        hexagram_type = "六合卦"
        meaning = (
            CINTERP["liuhe_hex"]["text"]
            + CINTERP["liuhe_hex_2"]["text"]
            + CINTERP["liuhe_hex_3"]["text"]
            + CINTERP["liuhe_hex_4"]["text"]
        )
    elif chong_count == 3:
        hexagram_type = "六冲卦"
        meaning = (
            CINTERP["liuchong_hex"]["text"]
            + CINTERP["liuchong_hex_2"]["text"]
            + CINTERP["liuchong_hex_3"]["text"]
            + CINTERP["liuchong_hex_4"]["text"]
        )
    elif he_count > 0 and chong_count > 0:
        hexagram_type = "半合半冲"
        meaning = (
            ctpl("crt_069", he_count, chong_count)
            + CINTERP["half_he_half_chong"]["text"]
        )
    elif he_count > 0:
        hexagram_type = "有合"
        meaning = (
            ctpl("crt_082", he_count, '' if chong_count == 0 else ctpl("crt_096", chong_count))
            + CINTERP["has_he"]["text"]
        )
    elif chong_count > 0:
        hexagram_type = EFFECT_LABELS["hex_has_clash"]
        meaning = (
            ctpl("crt_091", chong_count)
            + CINTERP["has_chong"]["text"]
        )
    else:
        hexagram_type = EFFECT_LABELS["hex_no_he_chong"]
        meaning = CINTERP["no_he_chong"]["text"]

    pair_summaries = "；".join(p["description"] for p in pairs)
    summary = f"{hexagram_type}：{pair_summaries}"

    return {
        "hexagram_type": hexagram_type,
        "pairs": pairs,
        "summary": summary,
        "meaning": meaning,
    }


def analyze_repetition(result):
    """
    反吟伏吟分析：
    - 反吟：变卦之爻地支与本卦对应爻地支相冲（反复之意）
    - 伏吟：变卦与本卦相同（或内/外卦不变），爻位地支不变（呻吟不止）
    
    返回：
        {
            "repetition_type": str,  # "反吟"/"伏吟"/"反吟兼伏吟"/"无"
            "chong_pairs": [
                {
                    "position": int,
                    "original_branch": str,
                    "changed_branch": str,
                    "description": str,
                },
                ...
            ],
            "summary": str,
            "meaning": str,
        }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    changed = result.get("changed_hexagram") or {}
    changed_name = changed.get("name")
    changed_lines = changed.get("changed_lines", [])

    if not yao_lines or not changed_name or not changed_lines:
        return {
            "repetition_type": "无",
            "chong_pairs": [],
            "summary": ctext("cr_029"),
            "meaning": "",
        }

    # 判断伏吟：如果所有爻都没变（理论上在变卦时有changed_lines，说明有变爻）
    # 伏吟的判定：变卦=本卦（不可能，因为有changed_lines）
    # 或者：内卦或外卦的三爻全部变化但变后相同（如乾→乾，但动爻变了又变回）
    # 这里准确判定：变卦各爻的地支与本卦对比
    yao_by_pos = {y["position"]: y for y in yao_lines}

    chong_pairs = []
    same_count = 0
    diff_count = 0

    for pos in range(1, 7):
        orig_branch = yao_by_pos.get(pos, {}).get("earthly_branch", "")
        chg_branch = get_changed_hexagram_branch(changed_name, pos)

        if orig_branch and chg_branch:
            if is_ba_zu_chong(orig_branch, chg_branch):
                chong_pairs.append({
                    "position": pos,
                    "original_branch": orig_branch,
                    "changed_branch": chg_branch,
                    "description": (
                        ctpl("crt_083", _pos_to_name(pos), orig_branch, chg_branch)
                    ),
                })
                diff_count += 1
            elif orig_branch == chg_branch:
                same_count += 1
            else:
                diff_count += 1

    # 反吟判定：有地支相冲的变爻对
    has_fanyin = len(chong_pairs) > 0

    # 伏吟判定：内卦或外卦三爻变化后地支不变
    # 内卦(1-3)全部变化且变后分支不变
    inner_same = True
    inner_all_changed = True
    for pos in range(1, 4):
        in_changed = pos in changed_lines
        if not in_changed:
            inner_all_changed = False
            break
        orig_branch = yao_by_pos.get(pos, {}).get("earthly_branch", "")
        chg_branch = get_changed_hexagram_branch(changed_name, pos)
        if orig_branch != chg_branch:
            inner_same = False

    outer_same = True
    outer_all_changed = True
    for pos in range(4, 7):
        in_changed = pos in changed_lines
        if not in_changed:
            outer_all_changed = False
            break
        orig_branch = yao_by_pos.get(pos, {}).get("earthly_branch", "")
        chg_branch = get_changed_hexagram_branch(changed_name, pos)
        if orig_branch != chg_branch:
            outer_same = False

    has_fuyin = (inner_all_changed and inner_same) or (outer_all_changed and outer_same)

    if has_fanyin and has_fuyin:
        repetition_type = EFFECT_LABELS["fan_yin_and_fu_yin"]
        meaning = (
            CINTERP["fanyin_and_fuyin"]["text"]
            + CINTERP["fanyin_and_fuyin_2"]["text"]
        )
    elif has_fanyin:
        repetition_type = EFFECT_LABELS["fan_yin"]
        meaning = (
            CINTERP["fanyin"]["text"]
            + CINTERP["fanyin_2"]["text"]
            + CINTERP["fanyin_3"]["text"]
        )
    elif has_fuyin:
        repetition_type = EFFECT_LABELS["fu_yin"]
        meaning = (
            CINTERP["fuyin"]["text"]
            + CINTERP["fuyin_2"]["text"]
            + CINTERP["fuyin_3"]["text"]
        )
    else:
        repetition_type = EFFECT_LABELS["fan_fu_none"]
        meaning = CINTERP["no_fanyin_fuyin"]["text"]

    summary_parts = []
    if has_fanyin:
        summary_parts.append(
            ctpl("crt_023", len(chong_pairs), '、'.join((d['description'] for d in chong_pairs)))
        )
    if has_fuyin:
        trigram = EFFECT_LABELS["inner"] if inner_all_changed and inner_same else EFFECT_LABELS["outer"]
        summary_parts.append(ctpl("crt_024", trigram))

    summary = "；".join(summary_parts) if summary_parts else EFFECT_LABELS["fan_fu_none_summary"]

    return {
        "repetition_type": repetition_type,
        "chong_pairs": chong_pairs,
        "fuyin_trigram": ("内卦" if inner_all_changed and inner_same else
                         "外卦" if outer_all_changed and outer_same else None),
        "summary": summary,
        "meaning": meaning,
    }


def analyze_repetition_deep(result):
    """
    反吟伏吟深层析义：基于《卜筮正宗》的五行旺衰综合规则，
    对反吟伏吟进行精细化评分，而非统一扣减。

    返回：
        {
            "type": "反吟" | "伏吟" | None,
            "level": "卦" | "爻",
            "scope": "内卦" | "外卦" | "用神" | "世爻" | None,
            "interpretation": str,
            "score_modifier": float,
            "classical_quote": str,
        }
    """
    # 先调用基础分析获取类型信息
    basic = analyze_repetition(result)
    rep_type = basic.get("repetition_type", "无")

    if rep_type == "无":
        return {
            "type": None,
            "level": None,
            "scope": None,
            "interpretation": "",
            "score_modifier": 0.0,
            "classical_quote": "",
        }

    # 判断是反吟还是伏吟为主（"反吟兼伏吟"拆为反吟优先）
    if "反吟" in rep_type:
        main_type = "反吟"
    elif "伏吟" in rep_type:
        main_type = "伏吟"
    else:
        main_type = None

    # 判断 level：卦级别 vs 爻级别
    hex_info = result.get("original_hexagram", {})
    changed = result.get("changed_hexagram") or {}
    changed_name = changed.get("name")
    original_name = hex_info.get("name", "")

    level = "爻"
    if original_name and changed_name and original_name != changed_name:
        # 检查是否是整个卦变了（如六冲变六冲）
        yao_lines = hex_info.get("yao_lines", [])
        changed_lines = changed.get("changed_lines", [])
        if len(changed_lines) >= 3:
            # 检查是否内外卦地支全冲
            chong_count = basic.get("chong_pairs", [])
            if len(chong_count) >= 4:
                level = "卦"

    # 判断 scope
    scope = None
    chong_pairs = basic.get("chong_pairs", [])
    fuyin_trigram = basic.get("fuyin_trigram")

    # 检查是否涉及世爻
    generation_str = hex_info.get("generation", "")
    gen_map_reverse = {"六世": 6, "五世": 5, "四世": 4, "三世": 3,
                       "二世": 2, "一世": 1, "游魂": 4, "归魂": 3}
    world_pos = gen_map_reverse.get(generation_str, 1)

    # 获取用神位置(s)
    use_god_positions = _find_use_god_positions(result)

    # 检查反吟/伏吟是否涉及用神或世爻
    involved_positions = set()
    for cp in chong_pairs:
        if isinstance(cp, dict):
            involved_positions.add(cp.get("position", 0))

    if main_type == "伏吟":
        # 伏吟涉及变化的爻位
        changed_lines = changed.get("changed_lines", [])
        involved_positions = set(changed_lines) if changed_lines else set()

    if world_pos in involved_positions:
        scope = "世爻"
    elif any(p in involved_positions for p in use_god_positions):
        scope = "用神"
    elif fuyin_trigram:
        scope = "内卦" if fuyin_trigram == "内卦" else "外卦"
    elif chong_pairs:
        # 根据相冲爻位判断内外
        first_pos = chong_pairs[0].get("position", 1) if isinstance(chong_pairs[0], dict) else 1
        scope = "内卦" if first_pos <= 3 else "外卦"
    else:
        scope = None

    # 获取用神旺衰状态以确定评分
    use_god_strength = _get_use_god_strength_level(result)

    # 根据规则评分
    if main_type == "反吟":
        score_modifier, interpretation, classical_quote = _score_fanyin(
            scope, use_god_strength, level, chong_pairs, basic
        )
    else:  # 伏吟
        score_modifier, interpretation, classical_quote = _score_fuyin(
            scope, use_god_strength, result, basic
        )

    return {
        "type": main_type,
        "level": level,
        "scope": scope,
        "interpretation": interpretation,
        "score_modifier": round(score_modifier, 2),
        "classical_quote": classical_quote,
    }


