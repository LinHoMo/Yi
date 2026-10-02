# -*- coding: utf-8 -*-
"""古典断法增强·effects.py。

分域实现：
  合绊 / 六破 / 入墓 / 化格 / 飞伏
  六合六冲 / 反吟伏吟
  卦身 / 五行旺衰 / 三刑

门面聚合入口见 classical_analysis.py。
"""

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现
from collections import Counter

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)


from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    BREAK_PAIRS,
    HE_PAIRS,
    KE_CYCLE,
    SHENG_CYCLE,
    TOMB_MAP,
    hexagram_level_relations,
)

from classical_enhancements import (
    _branch_element,
    _combined_strength,
    _element_to_relation,
    _find_use_god_positions,
    _get_use_god_strength_level,
    _infer_use_god_category,
    _pos_to_name,
    _relation_element,
    _score_fanyin,
    _score_fuyin,
    element_strength_in_month,
    find_hexagram_body,
    get_changed_hexagram_branch,
    get_month_strength_description,
    get_twelve_growth_stage,
    is_ba_zu_chong,
    is_ba_zu_he,
)
from chart_tables import (
    KE_WO,
    SELF_PUNISHMENTS,
    SHENG_WO,
    THREE_PUNISHMENTS_CYCLIC,
    THREE_PUNISHMENTS_MUTUAL,
    TRANSFORMATION_PATTERNS,
)
from narrative_utils import EFFECT_LABELS, EFFECT_PHRASES, CLASSICAL_INTERPRETATIONS as CINTERP, ctext, ctpl


# ─────────────────────────────────────────────────────────────────────────────
# 合绊 / 六破 / 入墓 / 化格 / 飞伏
# ─────────────────────────────────────────────────────────────────────────────

def analyze_day_month_bonding(result):
    """用神/忌神在日辰/月建上的六合关系（bond/effect/score）。
    
    来源：《卜筮正宗》"用神合日切近有力，合月事必成就"。
    """
    HE_SET_BI = set()
    for a, b in HE_PAIRS:
        HE_SET_BI.add((a, b))
        HE_SET_BI.add((b, a))

    use_god_branch = ""
    use_god_data = result.get("thinking_chain", {}).get("step2_use_god_identification", {})
    selected = use_god_data.get("selected_use_god", {})
    if isinstance(selected, dict):
        use_god_branch = selected.get("earthly_branch", "")

    if not use_god_branch:
        step3 = result.get("thinking_chain", {}).get("step3_strength_analysis", {})
        use_god_branch = step3.get("use_god_branch", "")

    # Fallback: find use_god from yao_lines via six_relation matching use_god_category
    if not use_god_branch:
        yao_lines = result.get("original_hexagram", {}).get("yao_lines", [])
        use_god_cat = use_god_data.get("use_god_category", "")
        for yao in yao_lines:
            if yao.get("six_relation") == use_god_cat:
                use_god_branch = yao.get("earthly_branch", "")
                break

    ji_shen_branches = []
    ji_shen_data = use_god_data.get("ji_shen", {})
    if isinstance(ji_shen_data, dict):
        ji_positions = ji_shen_data.get("positions", [])
        if isinstance(ji_positions, list):
            for jp in ji_positions:
                if isinstance(jp, dict):
                    jb = jp.get("earthly_branch", "")
                    if jb:
                        ji_shen_branches.append(jb)
        ji_fu = ji_shen_data.get("fu_cang")
        if isinstance(ji_fu, dict):
            jb = ji_fu.get("branch", "")
            if jb:
                ji_shen_branches.append(jb)

    div_time = result.get("divination_time", {})
    # day_branch/month_branch may be stored directly or derived from stem_branch
    day_branch = div_time.get("day_branch", "")
    month_branch = div_time.get("month_branch", "")
    if not day_branch:
        day_sb = div_time.get("day_stem_branch", "")
        if len(day_sb) >= 2:
            day_branch = day_sb[1]
    if not month_branch:
        month_sb = div_time.get("month_stem_branch", "")
        if len(month_sb) >= 2:
            month_branch = month_sb[1]

    findings = []

    # 用神合日
    if use_god_branch and day_branch and (use_god_branch, day_branch) in HE_SET_BI:
        findings.append({"bond": "日合用神", "effect": EFFECT_PHRASES["day_he_use_close"], "score": 0.5})

    # 用神合月
    if use_god_branch and month_branch and (use_god_branch, month_branch) in HE_SET_BI:
        findings.append({"bond": "月合用神", "effect": EFFECT_PHRASES["month_he_use_success"], "score": 0.4})

    # 月日同合 check
    if (use_god_branch and day_branch and month_branch
            and (use_god_branch, day_branch) in HE_SET_BI
            and (use_god_branch, month_branch) in HE_SET_BI):
        findings.append({"bond": "月日同合用神", "effect": EFFECT_PHRASES["day_month_he_use_peak"], "score": 0.3})

    # 忌神合日/月 (negative effect)
    for ji_b in ji_shen_branches:
        if ji_b and day_branch and (ji_b, day_branch) in HE_SET_BI:
            findings.append({"bond": "日合忌神", "effect": EFFECT_PHRASES["day_he_taboo_harm"], "score": -0.3})
        if ji_b and month_branch and (ji_b, month_branch) in HE_SET_BI:
            findings.append({"bond": "月合忌神", "effect": EFFECT_PHRASES["month_he_taboo_stick"], "score": -0.25})

    total_modifier = sum(f["score"] for f in findings)

    if findings:
        summary_parts = [f"{f['bond']}（{f['effect']}）" for f in findings]
        summary = "；".join(summary_parts)
    else:
        summary = ctext("cr_035")

    return {
        "findings": findings,
        "use_god_branch": use_god_branch,
        "ji_shen_branches": ji_shen_branches,
        "day_branch": day_branch,
        "month_branch": month_branch,
        "total_score_modifier": total_modifier,
        "summary": summary,
    }


def analyze_six_breaks(result):
    """六破：子酉/午卯/巳申/寅亥/辰丑/戌未，弱于六冲但仍有害（含世/用被破加重）。"""
    HE_SET_BI = set()
    for a, b in HE_PAIRS:
        HE_SET_BI.add((a, b))
        HE_SET_BI.add((b, a))

    BREAK_SET_BI = set()
    for a, b in BREAK_PAIRS:
        BREAK_SET_BI.add((a, b))
        BREAK_SET_BI.add((b, a))

    yao_lines = result.get("original_hexagram", {}).get("yao_lines", [])
    div_time = result.get("divination_time", {})
    # day_branch/month_branch may be stored directly or derived from stem_branch
    day_b = div_time.get("day_branch", "")
    month_b = div_time.get("month_branch", "")
    if not day_b:
        day_sb = div_time.get("day_stem_branch", "")
        if len(day_sb) >= 2:
            day_b = day_sb[1]
    if not month_b:
        month_sb = div_time.get("month_stem_branch", "")
        if len(month_sb) >= 2:
            month_b = month_sb[1]

    # Identify use-god branch and is_world flags
    use_god_branch = ""
    step3 = result.get("thinking_chain", {}).get("step3_strength_analysis", {})
    use_god_branch = step3.get("use_god_branch", "")

    use_god_cat = result.get("thinking_chain", {}).get("step2_use_god_identification", {}).get("use_god_category", "")

    world_positions = set()
    use_god_positions = set()
    for yao in yao_lines:
        if yao.get("is_world"):
            world_positions.add(yao.get("position"))
        if yao.get("six_relation") == use_god_cat and use_god_cat:
            use_god_positions.add(yao.get("position"))
        if use_god_branch and yao.get("earthly_branch") == use_god_branch:
            use_god_positions.add(yao.get("position"))

    breaks = []
    for yao in yao_lines:
        b = yao.get("earthly_branch", "")
        if not b:
            continue
        pos = yao.get("position")
        is_critical = pos in world_positions or pos in use_god_positions

        for ref_branch, ref_label in [(day_b, "日"), (month_b, "月")]:
            if not ref_branch:
                continue
            if (b, ref_branch) in BREAK_SET_BI:
                is_both_he = (b, ref_branch) in HE_SET_BI
                break_type = "合中带破" if is_both_he else "纯破"
                severity = "重" if is_critical else "轻"
                score = -0.3 if is_critical else -0.15
                breaks.append({
                    "branch": b,
                    "vs": ref_label,
                    "vs_branch": ref_branch,
                    "position": pos,
                    "type": break_type,
                    "severity": severity,
                    "is_critical": is_critical,
                    "score": score,
                    "description": (
                        ctpl("crt_085", '世/用爻' if is_critical else '', _pos_to_name(pos), b, ref_label, ref_label == '日' and '辰' or '建', ref_branch, break_type, '破损不遂' if is_critical else '微有损伤')
                    ),
                })

    total_modifier = sum(br.get("score", 0) for br in breaks)

    if breaks:
        po_count = len(breaks)
        he_po_count = sum(1 for br in breaks if br["type"] == "合中带破")
        desc = ctpl("crt_007", po_count)
        if he_po_count > 0:
            desc += ctpl("crt_028", he_po_count)
        summary_parts = [br["description"] for br in breaks]
        summary = "；".join(summary_parts)
    else:
        desc = ""
        summary = ctext("cr_036")

    return {
        "breaks": breaks,
        "has_break": len(breaks) > 0,
        "total_modifier": total_modifier,
        "description": desc,
        "summary": summary,
    }


def analyze_officer_tomb(result):
    """随官入墓（《卜筮正宗》凶象）：世/用同临墓库。五情形：官鬼入墓/世随/用随/鬼用同墓/化墓。"""
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    palace_element = hex_info.get("palace_element", "")
    question = result.get("question", "")

    if not yao_lines or not palace_element:
        return {
            "has_officer_tomb": False,
            "severity": "none",
            "scenarios": [],
            "officer_branches": [],
            "tomb_branch": "",
            "description": ctext("cr_037"),
            "score_modifier": 0.0,
            "classical_quote": CINTERP["guan_tomb_poem"]["text"],
            "details": [],
        }

    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""

    # 1. 找世爻地支
    world_branch = None
    world_pos = None
    for yao in yao_lines:
        if yao.get("is_world"):
            world_branch = yao.get("earthly_branch", "")
            world_pos = yao.get("position")
            break

    # 2. 推断用神类别并找用神地支
    use_god_category = _infer_use_god_category(question)
    use_god_branch = None
    use_god_pos = None
    if use_god_category == "世爻":
        use_god_branch = world_branch
        use_god_pos = world_pos
    else:
        for yao in yao_lines:
            if yao.get("six_relation") == use_god_category:
                use_god_branch = yao.get("earthly_branch", "")
                use_god_pos = yao.get("position")
                break
        # 用神不现则fallback到世爻
        if use_god_branch is None:
            use_god_branch = world_branch
            use_god_pos = world_pos

    # 3. 收集卦中所有地支（本卦 + 变卦 + 日月）
    present_branches = set()
    for yao in yao_lines:
        b = yao.get("earthly_branch", "")
        if b:
            present_branches.add(b)
    changed = result.get("changed_hexagram") or {}
    changed_name = changed.get("name")
    if changed_name:
        for pos_idx in range(1, 7):
            chg_branch = get_changed_hexagram_branch(changed_name, pos_idx)
            if chg_branch:
                present_branches.add(chg_branch)
    if month_branch:
        present_branches.add(month_branch)
    if day_branch:
        present_branches.add(day_branch)

    # 4. 找所有官鬼爻
    officer_lines = []
    for yao in yao_lines:
        if yao.get("six_relation") == "官鬼":
            officer_lines.append(yao)

    # 如果本卦无显式官鬼，检查伏藏官鬼
    if not officer_lines:
        hidden_analysis = result.get("advanced_analysis", {}).get("hidden_spirit_analysis", {})
        if isinstance(hidden_analysis, dict) and hidden_analysis.get("has_hidden_spirit"):
            for d in hidden_analysis.get("details", []):
                if d.get("missing_relation") == "官鬼":
                    hs = d.get("hidden_spirit", {})
                    officer_lines.append({
                        "position": hs.get("position", 0),
                        "name": hs.get("name", ""),
                        "earthly_branch": hs.get("branch", ""),
                        "six_relation": "官鬼",
                        "is_moving": False,
                        "is_hidden": True,
                    })

    if not officer_lines:
        return {
            "has_officer_tomb": False,
            "severity": "none",
            "scenarios": [],
            "officer_branches": [],
            "tomb_branch": "",
            "description": ctext("cr_038"),
            "score_modifier": 0.0,
            "classical_quote": CINTERP["guan_tomb_poem"]["text"],
            "details": [],
        }

    # 5. 逐官鬼分析入墓
    scenarios = []
    details = []
    officer_branches_collected = []
    worst_severity = "none"
    total_score_modifier = 0.0
    primary_tomb_branch = ""

    for officer in officer_lines:
        off_branch = officer.get("earthly_branch", "")
        if not off_branch:
            continue
        off_pos = officer.get("position", 0)
        off_name = officer.get("name") or _pos_to_name(off_pos)
        off_element = _branch_element(off_branch)
        is_moving = officer.get("is_moving", False)

        officer_branches_collected.append(off_branch)

        # 官鬼五行对应的墓库地支
        tomb = TOMB_MAP.get(off_element, "")
        if not tomb:
            continue

        if not primary_tomb_branch:
            primary_tomb_branch = tomb

        # 场景a: 官鬼入墓 -- 墓库地支出现在本卦/变卦/日月中
        officer_in_tomb = tomb in present_branches
        self_tomb = (off_branch == tomb)

        if officer_in_tomb or self_tomb:
            if ctext("cr_039") not in scenarios:
                scenarios.append(ctext("cr_039"))
            source = "本卦/变卦/日月中" if officer_in_tomb else "本支即墓"
            details.append({
                "type": ctext("cr_039"),
                "officer_branch": off_branch,
                "officer_element": off_element,
                "tomb_branch": tomb,
                "description": ctpl("crt_075", off_element, off_name, off_branch, tomb, source),
            })
            if worst_severity == "none":
                worst_severity = "mild"
            total_score_modifier += (-0.2 if self_tomb else -0.3)

        # 场景b: 世随官入墓 -- 世爻地支 = 官鬼墓库
        if world_branch and world_branch == tomb:
            if ctext("cr_040") not in scenarios:
                scenarios.append(ctext("cr_040"))
            details.append({
                "type": ctext("cr_040"),
                "officer_branch": off_branch,
                "world_branch": world_branch,
                "tomb_branch": tomb,
                "description": ctpl("crt_076", world_branch, off_element, tomb),
            })
            worst_severity = "severe"
            total_score_modifier += -1.0

        # 场景c: 用随官入墓 -- 用神地支 = 官鬼墓库
        if use_god_branch and use_god_branch == tomb:
            if ctext("cr_041") not in scenarios:
                scenarios.append(ctext("cr_041"))
            details.append({
                "type": ctext("cr_041"),
                "officer_branch": off_branch,
                "use_god_branch": use_god_branch,
                "use_god_category": use_god_category,
                "tomb_branch": tomb,
                "description": (
                    ctpl("crt_077", use_god_category, use_god_branch, off_element, tomb)
                ),
            })
            worst_severity = "severe"
            total_score_modifier += -1.5

        # 场景d: 鬼用同墓 -- 官鬼自身地支即墓 且 世/用也临此墓
        if off_branch == tomb and (world_branch == tomb or use_god_branch == tomb):
            if ctext("cr_042") not in scenarios:
                scenarios.append(ctext("cr_042"))
            details.append({
                "type": ctext("cr_042"),
                "officer_branch": off_branch,
                "world_branch": world_branch,
                "use_god_branch": use_god_branch,
                "tomb_branch": tomb,
                "description": ctpl("crt_078", off_branch, tomb),
            })
            worst_severity = "catastrophic"
            total_score_modifier += -2.0

        # 场景e: 官鬼动化墓 -- 官鬼发动且变爻为墓库地支
        if is_moving and changed_name:
            chg_branch = get_changed_hexagram_branch(changed_name, off_pos)
            if chg_branch == tomb:
                if ctext("cr_043") not in scenarios:
                    scenarios.append(ctext("cr_043"))
                details.append({
                    "type": ctext("cr_043"),
                    "officer_branch": off_branch,
                    "changed_branch": chg_branch,
                    "tomb_branch": tomb,
                    "description": (
                        ctpl("crt_086", off_name, off_branch, chg_branch)
                    ),
                })
                if worst_severity in ("none", "mild"):
                    worst_severity = "severe"
                else:
                    worst_severity = "severe"
                total_score_modifier += -1.0

    # 6. 综合输出
    if not scenarios:
        return {
            "has_officer_tomb": False,
            "severity": "none",
            "scenarios": [],
            "officer_branches": officer_branches_collected,
            "tomb_branch": primary_tomb_branch,
            "description": (
                ctpl("crt_029", ','.join(officer_branches_collected))
            ),
            "score_modifier": 0.0,
            "classical_quote": CINTERP["guan_tomb_poem"]["text"],
            "details": [],
        }

    severity_text = {
        "mild": "轻微",
        "severe": "严重",
        "catastrophic": "极凶/灾难性",
    }

    scenario_descriptions = {
        ctext("cr_039"): CINTERP["officer_tomb_officer"]["text"],
        ctext("cr_040"): CINTERP["officer_tomb_world"]["text"],
        ctext("cr_041"): CINTERP["officer_tomb_use"]["text"],
        ctext("cr_042"): CINTERP["officer_tomb_both"]["text"],
        ctext("cr_043"): CINTERP["officer_tomb_moving"]["text"],
    }

    desc_parts = [scenario_descriptions.get(s, s) for s in scenarios]
    description = (
        ctpl("crt_001", severity_text.get(worst_severity, ''), '、'.join(desc_parts))
    )
    if worst_severity == "catastrophic":
        description += CINTERP["officer_tomb_catastrophic"]["text"]
    elif worst_severity == "severe":
        description += CINTERP["officer_tomb_severe"]["text"]
    else:
        description += CINTERP["officer_tomb_mild"]["text"]

    return {
        "has_officer_tomb": True,
        "severity": worst_severity,
        "scenarios": scenarios,
        "officer_branches": officer_branches_collected,
        "tomb_branch": primary_tomb_branch,
        "description": description,
        "score_modifier": round(total_score_modifier, 2),
        "classical_quote": CINTERP["guan_tomb_poem"]["text"],
        "details": details,
    }


def analyze_transformation_pattern(result):
    """动爻格局：连续三爻/间隔动/上下卦全动/对爻齐动/用原齐动/用忌齐动。"""
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    # 世爻和应爻位置从爻中提取
    world_pos = 0
    response_pos = 0
    for yao in yao_lines:
        if yao.get("is_world"):
            world_pos = yao.get("position", 0)
        if yao.get("is_response"):
            response_pos = yao.get("position", 0)

    moving = []
    for yao in yao_lines:
        if yao.get("is_moving", False):
            moving.append(yao.get("position", 0))

    if len(moving) < 2:
        return {"pattern": None}

    patterns = []

    # 检查连续三爻动
    for i in range(1, 5):  # position 1~4 as starting point
        if all(p in moving for p in [i, i + 1, i + 2]):
            patterns.append(ctext("cr_044"))
            break

    # 检查间隔动爻
    if moving == [1, 3, 5] or moving == [2, 4, 6]:
        patterns.append(ctext("cr_045"))

    # 检查上卦全动 (positions 4,5,6)
    if all(p in moving for p in [4, 5, 6]):
        patterns.append(ctext("cr_046"))

    # 检查下卦全动 (positions 1,2,3)
    if all(p in moving for p in [1, 2, 3]):
        patterns.append(ctext("cr_047"))

    # 检查对爻齐动（世爻与应爻同动）
    if world_pos and response_pos and world_pos in moving and response_pos in moving:
        patterns.append(ctext("cr_048"))

    # 检查用神原神齐动/用神忌神齐动
    # 需要从 thinking-chain 的用神信息获取
    question = result.get("question", "")
    use_god_cat = _infer_use_god_category(question)
    if use_god_cat and use_god_cat != "世爻":
        # 原神 = 生用神之五行对应的六亲
        use_god_elem = _relation_element(use_god_cat, hex_info.get("palace_element", ""))
        if use_god_elem:
            yuan_shen_elem = SHENG_WO.get(use_god_elem)  # 生我者为原神
            ji_shen_elem = KE_WO.get(use_god_elem)  # 克我者为忌神

            yuan_shen_rel = _element_to_relation(yuan_shen_elem, hex_info.get("palace_element", "")) if yuan_shen_elem else None
            ji_shen_rel = _element_to_relation(ji_shen_elem, hex_info.get("palace_element", "")) if ji_shen_elem else None

            use_god_moving = any(
                yao.get("is_moving") and yao.get("six_relation") == use_god_cat
                for yao in yao_lines
            )
            yuan_shen_moving = any(
                yao.get("is_moving") and yao.get("six_relation") == yuan_shen_rel
                for yao in yao_lines
            ) if yuan_shen_rel else False
            ji_shen_moving = any(
                yao.get("is_moving") and yao.get("six_relation") == ji_shen_rel
                for yao in yao_lines
            ) if ji_shen_rel else False

            if use_god_moving and yuan_shen_moving:
                patterns.append(ctext("cr_049"))
            if use_god_moving and ji_shen_moving:
                patterns.append(ctext("cr_050"))

    total_weight = sum(
        TRANSFORMATION_PATTERNS.get(p, {}).get("weight", 1.0) for p in patterns
    )

    if patterns:
        interpretation = "；".join(
            TRANSFORMATION_PATTERNS.get(p, {}).get("advice", "") for p in patterns
        )
    else:
        interpretation = ctext("cr_051")

    return {
        "moving_positions": moving,
        "moving_count": len(moving),
        "patterns": patterns,
        "total_weight": total_weight,
        "interpretation": interpretation,
    }


def analyze_flying_hidden_interaction(result):
    """飞伏互断（《火珠林》）：飞神与伏神的生克制化及得出/不得出。"""
    fu_analysis = result.get("advanced_analysis", {}).get("hidden_spirit_analysis", {})
    if not fu_analysis or not fu_analysis.get("has_hidden_spirit"):
        return {"has_interaction": False}

    details = fu_analysis.get("details", [])
    if not details:
        return {"has_interaction": False}

    interactions = []
    for fu in details:
        covering = fu.get("covering_spirit", {})  # 飞神
        hidden = fu.get("hidden_spirit", {})      # 伏神
        fei_elem = covering.get("element", "")
        fu_elem = hidden.get("element", "")
        can_emerge = fu.get("can_emerge", True)

        if not fei_elem or not fu_elem:
            continue

        # 飞伏关系定性
        if fei_elem == fu_elem:
            relation = "比和"  # 飞伏同类 → 伏得出易
        elif SHENG_CYCLE.get(fei_elem) == fu_elem:
            relation = "飞生伏"  # 飞神生伏神 → 伏神易出，受荫
        elif KE_CYCLE.get(fei_elem) == fu_elem:
            relation = "飞克伏"  # 飞神克伏神 → 伏神难出，受压
        elif SHENG_CYCLE.get(fu_elem) == fei_elem:
            relation = "伏生飞"  # 伏神泄气 → 伏得出但力弱
        else:
            relation = "伏克飞"  # 伏神克飞神 → 伏得出但多阻

        fu_name = hidden.get("six_relation", "伏神")
        fei_name = covering.get("six_relation", "")

        interactions.append({
            "position": hidden.get("position"),
            "fei_shen": fei_name,
            "fu_shen": fu_name,
            "fei_branch": covering.get("branch", ""),
            "fu_branch": hidden.get("branch", ""),
            "relation": relation,
            "can_emerge": can_emerge,
            "description": (
                ctpl("crt_055", _pos_to_name(hidden.get('position', 0)), fei_name, fei_elem, fu_name, fu_elem, relation, '伏得出' if can_emerge else '伏难出')
            ),
        })

    overall_emerge = all(i["can_emerge"] for i in interactions) if interactions else True

    return {
        "has_interaction": True,
        "interactions": interactions,
        "overall_emerge": overall_emerge,
        "summary": "；".join(i["description"] for i in interactions) if interactions else "无伏神",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 六合六冲 / 反吟伏吟
# ─────────────────────────────────────────────────────────────────────────────

def analyze_clash_harmony(result):
    """六合/六冲卦判断：逐位(1-4,2-5,3-6)地支关系 → 合卦/冲卦/半合半冲/无明确。"""
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
    """反吟伏吟：本卦逐位比对变卦地支。反吟=六冲；伏吟=不变。"""
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
            "hexagram_level": None,
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
        # 卦级反吟/伏吟：本卦与变卦逐位比对地支（内核 hexagram_level_relations）。
        # 《卜筮正宗》"内卦反吟内不安，外卦反吟外不宁"——scope 即此处给出的内外卦级。
        "hexagram_level": hexagram_level_relations(
            hex_info.get("name", ""), changed_name
        ),
    }


def analyze_repetition_deep(result):
    """反吟伏吟深层析义（《卜筮正宗》）：五行旺衰综合的精细化评分，非统一扣减。"""
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

    # 卦级判定以内核逐位比对为准（六位全冲/全同；半卦经卦未变而爻支全冲/全同）
    hl = basic.get("hexagram_level") or {}
    scope_info = hl.get("scope") or {}
    full_hexagram = bool(hl.get("full_clash") or hl.get("full_same"))

    level = "爻"
    if original_name and changed_name and original_name != changed_name:
        yao_lines = hex_info.get("yao_lines", [])
        changed_lines = changed.get("changed_lines", [])
        if len(changed_lines) >= 3:
            # 检查是否内外卦地支全冲
            chong_count = basic.get("chong_pairs", [])
            if len(chong_count) >= 4:
                level = "卦"
    if full_hexagram:
        level = "卦"

    # 判断 scope
    scope = None
    chong_pairs = basic.get("chong_pairs", [])
    fuyin_trigram = basic.get("fuyin_trigram")

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
    elif full_hexagram:
        scope = "内卦"      # 全卦反吟/伏吟：六爻俱动，内卦先受（"内不安"为其本象）
    elif (main_type == "反吟" and (scope_info.get("inner_true_fanyin")
                                   or scope_info.get("outer_true_fanyin"))):
        scope = "内卦" if scope_info.get("inner_true_fanyin") else "外卦"
    elif (main_type == "伏吟" and (scope_info.get("inner_true_fuyin")
                                   or scope_info.get("outer_true_fuyin"))):
        scope = "内卦" if scope_info.get("inner_true_fuyin") else "外卦"
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
        # 卦级判定（内核 hexagram_level_relations）：full_clash/full_same/内外卦 flag + category
        "hexagram_level": hl,
        "hexagram_category": hl.get("category"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 卦身 / 五行旺衰 / 三刑
# ─────────────────────────────────────────────────────────────────────────────

def analyze_hexagram_body(result):
    """卦身法（《卜筮正宗》安月卦身诀）：世爻阴阳 + 爻位 → 卦身支。"""
    hex_info = result.get("original_hexagram", {})
    generation = hex_info.get("generation", "")
    yao_lines = hex_info.get("yao_lines", [])

    # 世爻爻位（游魂=4、归魂=3，与装卦通则一致）
    gen_map_reverse = {"六世": 6, "五世": 5, "四世": 4, "三世": 3,
                       "二世": 2, "一世": 1, "游魂": 4, "归魂": 3}
    world_pos = gen_map_reverse.get(generation, 0)

    if world_pos == 0 or not yao_lines:
        return {
            "body_position": None, "body_positions": [], "body_branch": "",
            "body_element": "", "body_relation": "",
            "meaning": ctext("cr_030"),
            "classical_rule": "《卜筮正宗》安月卦身诀：阴世则从午月起，阳世还从子月生；从初数至世方真。",
            "implications": [],
            "body_not_present": False,
        }

    world_yao = next((y for y in yao_lines if y.get("position") == world_pos), None)
    if world_yao is None:
        return {
            "body_position": None, "body_positions": [], "body_branch": "",
            "body_element": "", "body_relation": "",
            "meaning": ctext("cr_030"),
            "classical_rule": "《卜筮正宗》安月卦身诀：阴世则从午月起，阳世还从子月生；从初数至世方真。",
            "implications": [],
            "body_not_present": False,
        }

    world_is_yang = world_yao.get("nature") == "yang"
    body_branch = find_hexagram_body(world_is_yang, world_pos)  # 月卦身支

    # 卦身支在卦中所现爻位（可 0 / 1 / 2 处）
    body_positions = [y.get("position") for y in yao_lines
                      if y.get("earthly_branch") == body_branch]
    body_yao = next((y for y in yao_lines if y.get("earthly_branch") == body_branch), {})

    body_element = _branch_element(body_branch)
    body_relation = body_yao.get("six_relation", "")
    is_empty = body_branch in result.get("empty_branches", [])

    response_texts = []
    body_pos = body_positions[0] if body_positions else None
    if not body_positions:
        response_texts.append(ctpl("crt_098", body_branch))
    else:
        if world_pos in body_positions:
            response_texts.append(CINTERP["hex_body_world"]["text"])
        use_positions = _find_use_god_positions(result)
        if any(p in use_positions for p in body_positions):
            response_texts.append(CINTERP["hex_body_use"]["text"])
        if is_empty:
            response_texts.append(CINTERP["hex_body_empty"]["text"])
        if body_relation == "官鬼":
            response_texts.append(CINTERP["hex_body_officer"]["text"])
        elif body_relation == "妻财":
            response_texts.append(CINTERP["hex_body_wealth"]["text"])
        elif body_relation == "子孙":
            response_texts.append(CINTERP["hex_body_child"]["text"])
        if not response_texts:
            response_texts.append(ctpl("crt_025", _pos_to_name(body_pos), body_relation))

    return {
        "body_position": body_pos,
        "body_positions": body_positions,
        "body_branch": body_branch,
        "body_element": body_element,
        "body_relation": body_relation,
        "meaning": ctpl("crt_004", _pos_to_name(body_pos)) if body_pos else "卦身不现",
        "classical_rule": "《卜筮正宗》安月卦身诀：阴世则从午月起，阳世还从子月生；从初数至世方真。",
        "implications": [
            CINTERP["hex_body_use_arrow"]["text"],
            CINTERP["hex_body_ji_arrow"]["text"],
            CINTERP["hex_body_world_arrow"]["text"],
            CINTERP["hex_body_empty_arrow"]["text"],
        ],
        "body_is_world": world_pos in body_positions,
        "body_is_empty": is_empty,
        "body_is_use_god": any(p in _find_use_god_positions(result) for p in body_positions),
        "body_not_present": not body_positions,
        "specific_notes": response_texts,
    }


def analyze_element_strength(result):
    """纳甲四柱旺衰（月建日辰五行旺衰体系 + 用神 monthly/daily 综合）。"""
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    palace_element = hex_info.get("palace_element", "")

    if not yao_lines:
        return {"month_branch": "", "month_element": "", "day_branch": "",
                "day_element": "", "strength_description": "",
                "details": [], "summary": ctext("cr_018")}

    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""

    month_element = _branch_element(month_branch)
    day_element = _branch_element(day_branch)
    empty_branches = result.get("empty_branches", [])

    strength_desc = get_month_strength_description(month_element)

    details = []
    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        elem = _branch_element(branch)
        m_str = element_strength_in_month(elem, month_element)
        d_str = element_strength_in_month(elem, day_element)
        overall = _combined_strength(elem, month_element, day_element)

        # 特殊标记
        special = []
        if branch in empty_branches:
            special.append(ctext("cr_031"))
        if is_ba_zu_chong(branch, month_branch):
            special.append(ctext("cr_032"))
        if is_ba_zu_chong(branch, day_branch):
            special.append(ctext("cr_033"))
        stage = get_twelve_growth_stage(elem, day_branch)
        if stage in ("墓", "绝", "死"):
            special.append(f"{stage}")

        details.append({
            "position": yao["position"],
            "name": yao.get("name", ""),
            "branch": branch,
            "element": elem,
            "six_relation": yao.get("six_relation", ""),
            "month_strength": m_str,
            "day_strength": d_str,
            "overall": overall,
            "growth_stage": stage,
            "special_markers": special,
        })

    # 通用建议
    advice_parts = [
        ctpl("crt_005", month_branch, month_element, day_branch, day_element),
        ctpl("crt_006", strength_desc),
    ]

    # 综合总结
    summary_lines = advice_parts.copy()
    strong_yaos = [d for d in details if d["overall"] in ("旺", "相")]
    weak_yaos = [d for d in details if d["overall"] in ("偏弱", "衰")]

    if strong_yaos:
        s_desc = "、".join(
            f"{d['six_relation']}({d['branch']},{d['month_strength']}/{d['day_strength']})"
            for d in strong_yaos
        )
        summary_lines.append(ctpl("crt_026", s_desc))
    if weak_yaos:
        w_desc = "、".join(
            f"{d['six_relation']}({d['branch']},{d['month_strength']}/{d['day_strength']})"
            for d in weak_yaos
        )
        summary_lines.append(ctpl("crt_027", w_desc))

    return {
        "month_branch": month_branch,
        "month_element": month_element,
        "day_branch": day_branch,
        "day_element": day_element,
        "strength_description": strength_desc,
        "palace_element": palace_element,
        "details": details,
        "summary": "。".join(summary_lines),
    }


def analyze_three_punishments(result):
    """三刑（《卜筮正宗》定量版）：完整/待刑/自刑。循环刑寅巳申丑戌未、互刑子卯、自刑辰午酉亥。"""
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    if not yao_lines:
        return {"has_punishment": False, "punishments": [], "total_score": 0.0, "summary": ctext("cr_018")}

    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    day_sb = dt.get("day_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    day_branch = day_sb[1:] if len(day_sb) >= 2 else ""

    # ── 收集所有地支及其来源 ──
    # 三刑口径（P0-1 修正）：
    #   1) 以本卦六爻为主（hex_branches）；
    #   2) 月建/日辰仅作"催刑"（external_branches），参与补足但不按完整三刑计；
    #   3) 变卦地支不参与本卦三刑（化出之爻不构成原局刑伤）。
    hex_branches = []
    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        if branch:
            hex_branches.append((branch, ctpl("crt_070", _pos_to_name(yao['position']))))

    external_branches = []
    if month_branch:
        external_branches.append((month_branch, ctpl("crt_053", month_branch)))
    if day_branch:
        external_branches.append((day_branch, ctpl("crt_054", day_branch)))

    branches_with_source = hex_branches + external_branches

    # ── 建立全量地支集合（用于完整性判断）──
    all_branches_set = set(b for b, _ in branches_with_source)
    hex_set = set(b for b, _ in hex_branches)

    # ── 辅助：从 branches_with_source 中找出指定地支的所有来源位置 ──
    def _find_sources(branchesNeeded):
        return [(b, s) for b, s in branches_with_source if b in branchesNeeded]

    punishments = []
    total_score = 0.0

    # ── 1. 循环刑（无恩、恃势）：三字全见 vs 仅见两字 ──
    for ptype, required in THREE_PUNISHMENTS_CYCLIC.items():
        required_set = set(required)
        present_set = all_branches_set & required_set
        present = sorted(present_set, key=required.index)
        missing = sorted(required_set - present_set, key=required.index)

        present_hex_cnt = len(hex_set & required_set)
        if present_hex_cnt == 3:
            # 卦内三字齐备 — 完整三刑，极凶
            sources = _find_sources(set(required))
            pos_list = list(dict.fromkeys(s for _, s in sources))  # deduplicated, keep order
            punishments.append({
                "type": ptype,
                "completeness": "完整",
                "branches_present": present,
                "missing": [],
                "formed_by": "卦内",
                "positions": pos_list,
                "description": (
                    ctpl("crt_071", ptype, present[0], present[1], present[2], '、'.join(pos_list))
                ),
                "score": -1.0,
            })
            total_score -= 1.0
        elif len(present_set) == 3:
            # 卦内二字 + 月日补足一字 — 催刑（月日催成，力减半）
            sources = _find_sources(set(required))
            pos_list = list(dict.fromkeys(s for _, s in sources))
            punishments.append({
                "type": ptype,
                "completeness": "催刑",
                "branches_present": present,
                "missing": [],
                "formed_by": "卦内为主，月日催刑",
                "positions": pos_list,
                "description": (
                    ctpl("crt_084", ptype, '、'.join((p for p in present if p in hex_set)) or '无', '、'.join((p for p in present if p not in hex_set)))
                ),
                "score": -0.5,
            })
            total_score -= 0.5
        elif len(present_set) == 2:
            # 待刑 — 需月日补齐
            sources = _find_sources(present_set)
            pos_list = list(dict.fromkeys(s for _, s in sources))
            punishments.append({
                "type": ptype,
                "completeness": "待刑",
                "branches_present": present,
                "missing": missing,
                "formed_by": "待月日补齐",
                "positions": pos_list,
                "description": (
                    ctpl("crt_092", ptype, present[0], present[1], missing[0], missing[0])
                ),
                "score": -0.3,
            })
            total_score -= 0.3
        # 卦内及月日合计不足两字: 不构成任何刑

    # ── 2. 互刑（无礼之刑子卯）：卦内两字成刑；卦内一+月日一为待刑 ──
    b1_key, b2_key = THREE_PUNISHMENTS_MUTUAL["无礼之刑"]
    in_hex = (b1_key in hex_set and b2_key in hex_set)
    in_all = (b1_key in all_branches_set and b2_key in all_branches_set)
    if in_all:
        sources = _find_sources({b1_key, b2_key})
        pos_list = list(dict.fromkeys(s for _, s in sources))
        if in_hex:
            punishments.append({
                "type": "无礼之刑",
                "completeness": "成刑",
                "branches_present": [b1_key, b2_key],
                "missing": [],
                "formed_by": "卦内",
                "positions": pos_list,
                "description": (
                    ctpl("crt_072", b1_key, b2_key, '、'.join(pos_list))
                ),
                "score": -0.5,
            })
            total_score -= 0.5
        else:
            punishments.append({
                "type": "无礼之刑",
                "completeness": "待刑",
                "branches_present": [b1_key, b2_key],
                "missing": [],
                "formed_by": "卦内为主，月日催刑",
                "positions": pos_list,
                "description": (
                    ctpl("crt_073", b1_key, b2_key)
                ),
                "score": -0.3,
            })
            total_score -= 0.3

    # ── 3. 自刑（辰午酉亥）：仅卦内同一地支两次以上 ──
    hex_branch_counts = Counter(b for b, _ in hex_branches)
    for sp_branch in SELF_PUNISHMENTS:
        count = hex_branch_counts.get(sp_branch, 0)
        if count >= 2:
            sources = _find_sources({sp_branch})
            pos_list = list(dict.fromkeys(s for _, s in sources))
            punishments.append({
                "type": "自刑",
                "completeness": "完整",
                "branches_present": [sp_branch],
                "missing": [],
                "formed_by": "卦内",
                "positions": pos_list,
                "description": (
                    ctpl("crt_074", sp_branch, count, '、'.join(pos_list))
                ),
                "score": -0.3 * (count - 1),
            })
            total_score -= 0.3 * (count - 1)  # 每多一次减0.3

    # ── 三刑齐全加重（多个成刑/完整/催刑叠加时凶性倍增）──
    # 经典规则："三刑齐全，凶不可解"——两处以上成刑时按1.5x折算，三处以上2.0x
    complete_cnt = sum(1 for p in punishments if p.get("completeness") in ("完整", "成刑", "催刑"))
    if complete_cnt >= 3:
        total_score *= 2.0  # 三处以上成刑 → 极凶
        # 三刑杂见（循环刑+无礼刑+自刑以上至少两类并列）额外加罚
        ptype_set = set(p.get("type", "") for p in punishments)
        if len(ptype_set) >= 3:
            total_score -= 0.8  # 三类以上刑并见 → 更凶
        elif len(ptype_set) >= 2:
            total_score -= 0.5  # 多种刑类杂见，凶性更甚
    elif complete_cnt >= 2:
        total_score *= 1.5  # 两处成刑 → 凶性加重
        ptype_set = set(p.get("type", "") for p in punishments)
        if len(ptype_set) >= 2:
            total_score *= 1.25  # 多种刑类杂见，再乘1.25
        # 两处以上成刑额外定罚(不乘倍数直接加)
        total_score -= 0.5  # 2+ 成刑叠加的固定附加减分
    # 1处成刑维持原分数（线性加减已足够）

    if not punishments:
        return {"has_punishment": False, "punishments": [], "total_score": 0.0, "summary": ctext("cr_034")}

    summary_parts = [p["description"] for p in punishments]

    return {
        "has_punishment": True,
        "punishments": punishments,
        "total_score": round(total_score, 2),
        "summary": "；".join(summary_parts),
    }
