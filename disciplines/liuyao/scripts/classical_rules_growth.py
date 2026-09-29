# -*- coding: utf-8 -*-
"""古典断法增强：十二长生 / 绝处逢生。（拆分自 classical_rules_patterns.py，纯搬移不改逻辑；门面见 classical_rules.py）。"""
import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel, kernel_dir

_ensure_kernel(__file__)

from classical_support import _branch_element, _combined_strength, _find_stage_at, _pos_to_name, element_strength_in_month, get_stages_of_interest, get_twelve_growth_stage, is_ba_zu_chong
from classical_tables import SHENG_WO, TWELVE_GROWTH
from chain_verdicts import PATTERN_VERDICTS, CLASSICAL_INTERPRETATIONS as CINTERP, ctext, ctpl

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
