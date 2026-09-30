from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ks_ensure, kernel_dir

_ks_ensure(__file__)

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
    hexagram_branches,          # 别卦六爻纳甲地支（三会判据要逐支比对）
    hexagram_he_chong_kind,     # 卦体六合/六冲：对应位三对地支判（内核唯一实现）
    SAN_HUI_GROUPS,             # 三会方局：寅卯辰/巳午未/申酉戌/亥子丑（内核唯一真值源）
    EARTHLY_BRANCHES as BRANCHES,
)

from datetime import datetime, timedelta

import json

import re

from pathlib import Path

from chain_tables import (_BRANCH_CLASHES, _BRANCH_CLASH_MAP, _CHART_TAIL,
    _ELEMENT_PEAK_MONTHS, _HE_MAP, _HEXAGRAM_HARMONY_SET, _HEX_NAMES,
    _QUESTION_USE_GOD_BASIS, _QUESTION_USE_GOD_MAP, _USE_GOD_LAYER_CITATIONS,
    HEXAGRAM_LIUCHONG, HEXAGRAM_LIUHE, JUE_MAP, SAN_HE, TRIGRAM_ELEMENT,
    USE_GOD_RELATIONSHIPS, _60_CYCLE_BASE)

from liuyao_narrate import (_build_reasoning_chain,
    _get_hexagram_body_summary_note, find_classical_quotes)

from liuyao_timing import predict_timing_core as _predict_timing

from narrative_rules import strength_reason, strength_polarity

from narrative_utils import (  # noqa: E402
    _branch_element,
    _evaluate_fu_cang_strength,
    _is_chong,
    _is_he,
    _pos_to_name,
    _twelve_growth_at_day,
    CLASSICAL_INTERPRETATIONS as CINTERP,
    element_strength_in_month,
    get_changed_hexagram_branch,
    get_elements_for_relation,
    get_empty_branches,
    get_palace_first_hexagram,
    get_relation_from_element,
    get_twelve_growth_stage,
    note_text,
    safe_get,
    strength_to_score,
    STEP5_CONFIDENCE as CONF_TXT,
    STEP5_FACTOR_REASONS as FREASON,
    STEP5_SPIRIT_REASONS as SPIRIT_TXT,
    STEP5_VERDICT_DESCS as VDESC,
    STEP5_YINGQI as YINGQI_TXT,
    vdesc,
)

# ─── 全局变量 ───
_USE_GOD_RULES: list[dict] | None = None

from liuyao_step2 import _element_to_relation  # 跨文件引用

# ═══ chain_step4.py ═══


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


# ═══ chain_step4_changes.py ═══


def _compose_change_summary(moving_lines, favorable_changes, unfavorable_changes,
                            tan_sheng_wan_ke, tan_he_wan_sheng_ke, greedy_harmony_summary,
                            advance_score_total, net_effect, net_description) -> str:
    n = len(moving_lines or [])
    if n == 0:
        return "卦中没有动爻，事情安静，吉凶主要看用神自身，而不是中途杀出的变数。"
    parts = [f"卦中有{n}个动爻。"]
    fav, unfav = len(favorable_changes or []), len(unfavorable_changes or [])
    if fav and not unfav:
        parts.append("动处总体是帮事情的。")
    elif unfav and not fav:
        parts.append("动处总体在拖后腿。")
    elif fav and unfav:
        parts.append(f"有帮衬也有牵扯（利{fav}弊{unfav}），不能只看一处。")
    else:
        parts.append("动处影响平淡，主线仍在用神。")
    reasons = []
    for r in (tan_sheng_wan_ke or []):
        reasons.append(str(r.get("reason") or ""))
    for r in (tan_he_wan_sheng_ke or []):
        reasons.append(str(r.get("reason") or ""))
    if greedy_harmony_summary:
        reasons.append(str(greedy_harmony_summary).rstrip("；"))
    reasons = [x.rstrip("；。") for x in reasons if x]
    if reasons:
        parts.append("具体来看：" + "；".join(reasons[:4]) + "。")
    if abs(advance_score_total or 0) > 0.001:
        parts.append("进退之势也要计入。")
    net_desc = str(net_description or "").replace("（动变总体有利）", "").replace("（动变总体不利）", "")
    net_desc = net_desc.replace("（动变利弊参半）", "").strip()
    net_val = float(net_effect or 0)
    if net_val > 0.3:
        parts.append("综合动变，对事情偏有利。")
    elif net_val < -0.3:
        parts.append("综合动变，对事情偏不利。" + (f"（{net_desc}）" if net_desc and net_desc not in ("中性", "偏吉", "偏凶") else ""))
    else:
        parts.append("综合动变，利弊大致相抵。")
    return "".join(parts)


def _classify_line_role(
    relation: str,
    use_god_category: str,
    element: str,
    use_god_element: str,
    yuan_shen_element: str,
    ji_shen_element: str,
    chou_shen_element: str,
) -> str:
    """判断动爻相对于用神的身份"""
    if relation == use_god_category:
        return "用神"
    if element == use_god_element:
        return "用神同气"
    if element == yuan_shen_element:
        return "原神"
    if element == ji_shen_element:
        return "忌神"
    if element == chou_shen_element:
        return "仇神"
    # 其他：判断与用神关系
    if SHENG_CYCLE.get(element) == use_god_element:
        return "生用神之爻"  # 生用神者
    if KE_CYCLE.get(element) == use_god_element:
        return "克用神之爻"  # 克用神者
    return "闲神"


def _determine_change_type(
    orig_branch: str,
    chg_branch: str | None,
    orig_element: str,
    chg_element: str,
    month_branch: str,
    day_branch: str,
) -> dict:
    """判断动爻变化类型"""
    if not chg_branch:
        return {"type": "无变爻", "detail": "变卦缺失"}

    # 回头生：变爻五行生动爻五行
    if SHENG_CYCLE.get(chg_element) == orig_element:
        # 排除化合情况
        if _is_he(orig_branch, chg_branch):
            return {"type": "六合", "detail": f"{orig_branch}与{chg_branch}六合（土）, 贪合忘生"}
        return {"type": "回头生", "detail": f"变爻{chg_element}生动爻{orig_element}，化进"}

    # 回头克：变爻五行克动爻五行
    if KE_CYCLE.get(chg_element) == orig_element:
        if _is_he(orig_branch, chg_branch):
            return {"type": "六合", "detail": f"{orig_branch}与{chg_branch}六合, 贪合忘克"}
        return {"type": "回头克", "detail": f"变爻{chg_element}克动爻{orig_element}，不利"}

    # 化进/化退
    if ADVANCE_PAIRS.get(orig_branch) == chg_branch:
        return {"type": "化进神", "detail": f"{orig_branch}化{chg_branch}进，力量递增"}
    if RETREAT_PAIRS.get(orig_branch) == chg_branch:
        return {"type": "化退神", "detail": f"{orig_branch}化{chg_branch}退，力量递减"}

    # 化墓
    if TOMB_MAP.get(orig_element) == chg_branch:
        return {"type": "化墓", "detail": f"{orig_element}化入{chg_branch}墓库，困顿之象"}

    # 化绝
    if JUE_MAP.get(orig_element) == chg_branch:
        return {"type": "化绝", "detail": f"{orig_element}化入{chg_branch}绝地，气绝之象"}

    # 六合（地支相合）
    if _is_he(orig_branch, chg_branch):
        return {"type": "六合", "detail": f"{orig_branch}与{chg_branch}六合，可能绊住"}

    # 反吟
    if _is_chong(orig_branch, chg_branch):
        return {"type": "反吟", "detail": f"{orig_branch}冲{chg_branch}，反复不安"}

    return {"type": "化合", "detail": f"{orig_branch}→{chg_branch}，性质转变（{orig_element}→{chg_element}）"}


def _analyze_effect_on_use_god(
    orig_branch: str,
    chg_branch: str | None,
    orig_element: str,
    chg_element: str,
    use_god_element: str,
    change_type: dict,
    line_role: str,
) -> dict:
    """
    分析动爻变化对用神的净效应。
    返回 {description, score}，score 为正=有利，为负=不利。
    """
    score = 0.0
    description_parts = []

    # 基于身份和变化类型打分
    if line_role == "用神":
        # 用神自身动变
        ct = change_type["type"]
        if ct == "回头生":
            score = 1.5
            description_parts.append("用神动化回头生，大吉")
        elif ct == "回头克":
            score = -2.0
            description_parts.append("用神动化回头克，大凶")
        elif ct == "化进神":
            score = 1.0
            description_parts.append("用神化进，势盛")
        elif ct == "化退神":
            score = -1.0
            description_parts.append("用神化退，势衰")
        elif ct == "化墓":
            score = -1.5
            description_parts.append("用神化墓，困顿")
        elif ct == "化绝":
            score = -1.5
            description_parts.append("用神化绝，气断")
        elif ct == "反吟":
            score = -0.5
            description_parts.append("用神反吟，反复")
        elif ct == "六合":
            # 六合需看是合起还是合绊
            score = -0.3
            description_parts.append("用神合绊，暂时受阻")
        else:
            score = 0.0
            description_parts.append("用神动变平平")

    elif line_role == "原神":
        # 原神（用神的源头）动变
        ct = change_type["type"]
        if ct == "回头生":
            score = 1.5
            description_parts.append("原神动化回头生，源源不断生助用神")
        elif ct == "回头克":
            score = -1.0
            description_parts.append("原神动化回头克，源头受损")
        elif ct == "化进神":
            score = 1.0
            description_parts.append("原神化进，生用有力")
        elif ct == "化退神":
            score = -0.5
            description_parts.append("原神化退，生力减弱")
        elif ct == "化墓":
            score = -1.0
            description_parts.append("原神化墓，无力生用")
        elif ct == "六合":
            score = -0.3
            description_parts.append("原神合绊，暂难生用")
        elif RETREAT_PAIRS.get(orig_branch) == chg_branch:
            # 二次识别：变化类型未被 _determine_change_type 判为化退神，但进退神表匹配化退
            score = -0.5
            description_parts.append("原神化退（进退神判），生力减弱为凶")
        else:
            # 原神动（不论化什么都有一定助用效果）
            # 原神五行生用神 → 生用有力（《增删易》"原神发动，生用有力"）
            if SHENG_CYCLE.get(orig_element) == use_god_element:
                score = 1.0
                description_parts.append("原神发动，其五行生用神，生用有力")
            else:
                score = 0.3
                description_parts.append("原神动，有生用之心")

    elif line_role == "忌神":
        # 忌神（克用神者）动变
        ct = change_type["type"]
        if ct == "回头生":
            score = -1.5
            description_parts.append("忌神动化回头生，克用更甚")
        elif ct == "回头克":
            score = 1.5
            description_parts.append("忌神动化回头克，凶性反制（大吉）")
        elif ct == "化进神":
            score = -1.0
            description_parts.append("忌神化进，克用有力")
        elif ct == "化退神":
            score = 0.5
            description_parts.append("忌神化退，克力渐消")
        elif ct == "化墓":
            score = 1.0
            description_parts.append("忌神化墓，克用受阻（吉）")
        elif ct == "六合":
            score = 0.3
            description_parts.append("忌神合绊，克用受阻")
        else:
            score = -0.3
            description_parts.append("忌神动，有意克用")

    elif line_role == "仇神":
        # 仇神（克原神者）动变
        ct = change_type["type"]
        if ct == "化退神":
            score = 0.3
            description_parts.append("仇神化退，对原神威胁减少")
        elif ct == "化墓":
            score = 0.5
            description_parts.append("仇神化墓，原神得安")
        elif ct == "回头克":
            score = 1.0
            description_parts.append("仇神化回头克，原神得救")
        else:
            score = -0.2  # 仇神动总体轻微不利
            description_parts.append("仇神动，间接影响原神")

    else:
        # 与其他爻互动
        # 变爻与用神的关系
        if chg_branch and chg_element == use_god_element:
            # 动爻化出用神（化用）
            score = 0.5
            description_parts.append("动爻化出用神之气")
        elif chg_branch and SHENG_CYCLE.get(chg_element) == use_god_element:
            score = 0.3
            description_parts.append("动爻变化生用神")
        elif chg_branch and KE_CYCLE.get(chg_element) == use_god_element:
            score = -0.3
            description_parts.append("动爻变化克用神")
        else:
            description_parts.append("此动爻与用神关系疏远")

    return {
        "description": "；".join(description_parts) if description_parts else "影响不明显",
        "score": round(score, 2),
    }


def _check_tan_sheng_wan_ke(
    details: list[dict],
    use_god_element: str,
    palace_element: str,
) -> list[dict]:
    """
    贪生忘克规则检查。
    《黄金策》：贪生忘克者，原神动，忌神贪生原神而忘克用。
    条件：原神动 且 原神生忌神 同时存在
    """
    rules = []
    # 寻找原神动的详情
    yuan_shen_moving = [d for d in details if d["line_role"] == "原神"]
    ji_shen_moving = [d for d in details if d["line_role"] == "忌神"]

    for yuan in yuan_shen_moving:
        for ji in ji_shen_moving:
            # 检查原神和忌神是否相生（火生土类）
            yuan_elem = yuan["original_element"]
            ji_elem = ji["original_element"]
            if SHENG_CYCLE.get(yuan_elem) == ji_elem:
                rules.append({
                    "type": "贪生忘克",
                    "reason": f"原神{yuan['name']}生忌神{ji['name']}，忌神贪生忘克用神",
                    "detail_position": ji["position"],
                    "benefit_or_loss": "favorable",
                })
    return rules


def _check_tan_he_wan_sheng_ke(
    details: list[dict],
    yao_lines: list[dict],
    use_god_category: str,
) -> list[dict]:
    """
    贪合忘生/贪合忘克规则检查。
    条件：动爻与变爻六合，或动爻与日月合。
    """
    rules = []
    for detail in details:
        if detail["change_type"] == "六合":
            pos = detail["position"]
            rules.append({
                "type": "贪合忘生克",
                "reason": f"第{pos}爻动而六合，贪合而忘其生克",
                "detail_position": pos,
                "benefit_or_loss": "neutral",  # 有利有弊，视情况
            })
        # 检查与日月合
        orig_branch = detail.get("original_branch", "")
        chg_branch = detail.get("changed_branch")
        if chg_branch:
            # 检查动爻+日月合（简化）
            pass
    return rules


# ═══ chain_step4_patterns.py ═══


def _detect_classical_illness_pattern(question: str, step2_data: dict, step3_data: dict,
                                       empty_branches: list, step4_data: dict = None,
                                       hex_result: dict = None) -> dict:
    """
    古籍经典疾厄格局识别 —《增删卜易》《卜筮正宗》之核心断法。

    特殊疾厄格局优先于一般旺衰规则：
    - 近病逢空即愈：用神旬空，速愈之象
    - 近病逢合为凶：用神被日/月/动爻合住，病难退
    - 近病逢冲即愈：用神被冲，病气散
    - 近病六冲卦速愈
    - 久病逢空/冲/合为凶
    """
    result = {"pattern": None, "description": "", "impact_on_verdict": "", "score_adjustment": 0.0}

    q = question or ""
    is_near_illness = any(kw in q for kw in ["近病", "即愈", "何日愈"])
    is_chronic_illness = any(kw in q for kw in ["久病", "沉疴", "久疾"])
    is_illness_div = any(kw in q for kw in ["病", "疾", "症"]) and ("愈" in q or "吉凶" in q or "死" in q)

    if not (is_near_illness or is_chronic_illness or is_illness_div):
        return result

    # 获取用神信息
    use_god = step2_data.get("selected_use_god") or {}
    use_god_branch = use_god.get("earthly_branch", "")
    if not use_god_branch:
        # fallback: check use_god_yao_lines
        ug_lines = step2_data.get("use_god_yao_lines") or step2_data.get("use_god_positions") or []
        if ug_lines and isinstance(ug_lines, list):
            first = ug_lines[0]
            if isinstance(first, dict):
                use_god_branch = first.get("earthly_branch", "")

    # 化空检测：从 step3 或 step4 的动爻信息中获取
    transform_to_void = False
    void_branch_hit = ""

    # 优先从 step4_data.details 获取动爻化空（标准数据源）
    if not transform_to_void and step4_data:
        s4_details = step4_data.get("details") or step4_data.get("moving_details") or []
        for m in (s4_details if isinstance(s4_details, list) else []):
            if isinstance(m, dict):
                target = (m.get("changed_branch", "") or m.get("target_earthly_branch", "")
                         or m.get("to_branch", "") or m.get("transformed_branch", ""))
                if target and target in empty_branches:
                    transform_to_void = True
                    void_branch_hit = target
                    break

    # fallback: 检查 step3_data 中的 moving_analysis / dong_analysis / moving_details
    if not transform_to_void and step3_data:
        dong_analysis = (step3_data.get("dong_analysis") or step3_data.get("moving_analysis")
                         or step3_data.get("moving_details") or [])
        for m in (dong_analysis if isinstance(dong_analysis, list) else []):
            if isinstance(m, dict):
                target = (m.get("target_earthly_branch", "") or m.get("to_branch", "")
                          or m.get("changed_branch", "") or m.get("transformed_branch", ""))
                if target and target in empty_branches:
                    transform_to_void = True
                    void_branch_hit = target
                    break

    # --- 近病逢合为凶（优先于逢空：合则病气难退，《卜筮正宗》"近病逢合为凶"）---
    # 仅限用神为静爻时——动爻逢合为"合起"（合而发动），不构成合绊；
    # 静爻逢合方为"合绊"（病气难退）。
    use_god_moving = use_god.get("is_moving", False) or any(
        yl.get("is_moving") for yl in
        (step2_data.get("use_god_yao_lines") or step2_data.get("use_god_positions") or [])
        if isinstance(yl, dict) and yl.get("earthly_branch") == use_god_branch
    )
    if (is_near_illness or is_illness_div) and use_god_branch and not use_god_moving:
        dt6 = hex_result.get("divination_time", {}) or {}
        m_b = (dt6.get("month_stem_branch", "") or "")[1:]
        d_b = (dt6.get("day_stem_branch", "") or "")[1:]
        HE6 = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
               "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
        he_bys = []
        if HE6.get(use_god_branch, "") == m_b:
            he_bys.append(f"月建{m_b}")
        if HE6.get(use_god_branch, "") == d_b:
            he_bys.append(f"日辰{d_b}")
        if he_bys:
            result["pattern"] = "近病逢合为凶"
            result["description"] = f"用神{use_god_branch}为{'、'.join(he_bys)}所合——近病逢合，病气难退（《卜筮正宗》定法）"
            result["impact_on_verdict"] = "用神被合，病气难退，凶"
            result["score_adjustment"] = -5.5
            return result

    # --- 近病逢空即愈 ---
    if (is_near_illness or is_illness_div):
        use_void = use_god_branch and use_god_branch in empty_branches
        if use_void or transform_to_void:
            void_desc = f"用神{use_god_branch}旬空" if use_void else f"用神化空（动爻化{void_branch_hit}旬空）"
            result["pattern"] = "近病逢空即愈"
            result["description"] = f"{void_desc}——近病逢空为病气将退，速愈之象（《增删易》定法）"
            result["impact_on_verdict"] = "近病逢空即愈，强调为吉"
            result["score_adjustment"] = 5.0
            return result

        # 近病运交any void branch → also 逢空象
        yao_lines = step2_data.get("use_god_yao_lines") or step2_data.get("use_god_positions") or []
        if yao_lines:
            for yl in yao_lines:
                if isinstance(yl, dict) and yl.get("earthly_branch", "") in empty_branches:
                    result["pattern"] = "近病逢空即愈"
                    result["description"] = f"用神{yl['earthly_branch']}临旬空——近病逢空即愈"
                    result["impact_on_verdict"] = "近病逢空为速愈象"
                    result["score_adjustment"] = 5.0
                    return result

    # --- 近病逢合为凶 ---
    if (is_near_illness or is_illness_div) and step3_data:
        combine_info = step3_data.get("combine_info") or {}
        if combine_info.get("is_combined"):
            combined_by = combine_info.get("combined_by", [])
            if combined_by:
                result["pattern"] = "近病逢合为凶"
                result["description"] = f"用神逢合（{'、'.join(str(x) for x in combined_by)}），近病逢合，病气难退（《增删易》定法）"
                result["impact_on_verdict"] = "近病逢合为凶之经典格局"
                result["score_adjustment"] = -3.5
                return result

        # Also check: 用神被日月生合为凶
        div_time = step3_data.get("divination_info", {})
        if not div_time:
            # Try hex_result (passed separately)
            pass
        # Check if use god is combined by day or month
        day_combine = step3_data.get("day_combine", "")
        month_combine = step3_data.get("month_combine", "")
        if day_combine or month_combine:
            combine_source = "]".join(filter(None, [f"日辰{day_combine}" if day_combine else "", f"月建{month_combine}" if month_combine else ""]))
            result["pattern"] = "近病逢合为凶"
            result["description"] = f"用神为{combine_source}所合——近病逢合为凶（《卜筮正宗》定法）"
            result["impact_on_verdict"] = "用神被合，病气难退，凶"
            result["score_adjustment"] = -3.5
            return result

    # --- 久病逢空/冲为凶 ---
    if is_chronic_illness:
        if use_god_branch and use_god_branch in empty_branches:
            result["pattern"] = "久病逢空为凶"
            result["description"] = f"久病用神{use_god_branch}逢空，久病逢空为危"
            result["impact_on_verdict"] = "久病逢空为脱象，凶"
            result["score_adjustment"] = -4.5
            return result

    return result


# 六冲/六合对的无序集合（由内核 CHONG_PAIRS / HE_PAIRS 派生，不另抄一份表）
_CHONG_PAIRS_SET = {frozenset(p) for p in CHONG_PAIRS}
_HE_PAIRS_SET = {frozenset(p) for p in HE_PAIRS}


def _hexagram_he_chong_kind(name: str) -> str:
    """（门面）卦名 → 六合卦/六冲卦/半合半冲/有合/有冲/无明确合冲/未知。

    机器判定唯一实现在内核 `yishu_core.symbols.hexagram_he_chong_kind`：按对应位
    (1,4)(2,5)(3,6) 三对地支判，不用卦名白名单。此处只转发，供本模块内
    `_detect_hexagram_harmony_clash_pattern` 的"本卦定始、变卦定终"双卦对比使用。
    """
    return hexagram_he_chong_kind(name)


def _detect_hexagram_harmony_clash_pattern(question: str, hex_result: dict, step4_data: dict) -> dict:
    """
    六合/六冲交互格局识别 — 冲中逢合可解，合处逢冲则散；并做"本卦定始、变卦定终"双卦对比。

    - 冲中逢合可解：六冲卦中却有日辰/动爻合世爻或应爻，冲散可解为吉
    - 合处逢冲则散：六合卦中却有日辰/月建冲世爻或应爻，合处逢冲为凶
    - 双卦对比（《黄金策》"合处逢冲事已散，冲中逢合事迟成"）：
      本卦六合而变卦六冲 → 先合后散（事已散）；本卦六冲而变卦六合 → 先散后合（事迟成）。
      本卦言始、变卦言终，两卦同为合或同为冲则只作同向叠加，不另出格局。
    """
    result = {"pattern": None, "description": "", "impact_on_verdict": "", "score_adjustment": 0.0}

    q = question or ""
    hex_name = hex_result.get("original_hexagram", {}).get("name", "")
    if not hex_name:
        return result

    # Check for 六合/六冲 in hexagram name using advanced analysis
    hex_advanced = hex_result.get("advanced_analysis", {}) or {}
    hex_type = hex_advanced.get("hexagram_type", "")

    is_he = "六合" in hex_type or hex_name in ("否", "泰", "恒", "益", "萃", "咸", "损", "同人", "贲", "鼎", "随", "节", "中孚", "既济", "家人", "蛊", "困", "豫", "临", "小畜", "履", "涣", "离", "丰")
    is_chong = "六冲" in hex_type or hex_name in ("乾", "坤", "坎", "离", "震", "巽", "艮", "兑", "无妄", "大壮", "遁", "晋", "萃", "夬", "姤", "解", "归妹", "旅", "涣", "小过")

    # Empty branches (for checking if world/response is void)
    empty = hex_result.get("empty_branches", [])

    # --- 冲中逢合可解 ---
    if is_chong:
        div_time = hex_result.get("divination_time", {}) or {}
        month_branch = (div_time.get("month_stem_branch", "") or "")[1:]
        day_branch = (div_time.get("day_stem_branch", "") or "")[1:]
        # 世应爻地支（从爻标志取，original_hexagram 无 world_position 字段）
        yao_lines = hex_result.get("original_hexagram", {}).get("yao_lines", [])
        world_branch = ""
        response_branch = ""
        for y in yao_lines:
            if y.get("is_world"):
                world_branch = y.get("earthly_branch", "")
            if y.get("is_response"):
                response_branch = y.get("earthly_branch", "")
        # 六合：由 core.HE_PAIRS 派生的 _HE_MAP（chain_tables），不另抄
        def _he_with(b: str) -> bool:
            partners = _HE_MAP.get(b) or []
            return month_branch in partners or day_branch in partners
        world_he = world_branch and _he_with(world_branch)
        response_he = response_branch and _he_with(response_branch)
        # 动爻化合（化出之爻与月日成合，或化出之爻生合用神）方可解冲
        details = step4_data.get("details", []) if step4_data else []
        def _is_helpful_he(d):
            if "化合" not in d.get("change_type", "") and "六合" not in d.get("change_type", ""):
                return False
            chg_branch = d.get("changed_branch", "")
            # 化出之支与日月成合 → 解冲
            if chg_branch and (month_branch in (_HE_MAP.get(chg_branch) or [])
                               or day_branch in (_HE_MAP.get(chg_branch) or [])):
                return True
            return False
        moving_he = any(_is_helpful_he(d) for d in details)

        if world_he or response_he or moving_he:
            he_target = "世爻" if world_he else ("应爻" if response_he else "动爻")
            result["pattern"] = "冲中逢合可解"
            result["description"] = f"六冲本主散，然月日/动爻合{he_target}（{'世' if world_he else ''}{'应' if response_he else ''}），冲中逢合可解"
            result["impact_on_verdict"] = "冲处逢合可解冲散，转危为安"
            result["score_adjustment"] = 2.5
            return result

        # 六冲无合解 → 事散之象（合伙/婚姻/出行/交易/官讼/谋事类；近病六冲速愈除外）
        SCATTER_KEYWORDS = ["合伙", "合作", "婚姻", "婚", "出行", "外出", "交易", "买卖",
                            "生意", "官讼", "官司", "求财", "谋事", "开店", "签约", "合同"]
        if any(k in q for k in SCATTER_KEYWORDS):
            result["pattern"] = "六冲主散"
            result["description"] = f"六冲卦主散，{hex_name}卦世应相冲，事难成合"
            result["impact_on_verdict"] = "六冲事散，合伙/婚恋/出行/交易类不利"
            result["score_adjustment"] = -2.0
            return result

    # --- 合处逢冲则散 ---
    if is_he:
        div_time = hex_result.get("divination_time", {}) or {}
        month_branch = (div_time.get("month_stem_branch", "") or "")[1:]
        day_branch = (div_time.get("day_stem_branch", "") or "")[1:]
        world_branch = ""
        response_branch = ""

        yao_lines = hex_result.get("original_hexagram", {}).get("yao_lines", [])
        for y in yao_lines:
            if y.get("is_world"):
                world_branch = y.get("earthly_branch", "")
            if y.get("is_response"):
                response_branch = y.get("earthly_branch", "")

        # Check if world/response is being clashed by month or day（_BRANCH_CLASH_MAP 由 core 派生）
        def _clashed_by(b: str) -> bool:
            partner = _BRANCH_CLASH_MAP.get(b, "")
            return partner and partner in (month_branch, day_branch)
        world_clashed = world_branch and _clashed_by(world_branch)
        response_clashed = response_branch and _clashed_by(response_branch)

        if (world_clashed or response_clashed):
            SCATTER2 = ["婚姻", "婚", "占婚", "合伙", "合作", "出行", "外出", "交易", "买卖",
                        "生意", "官讼", "官司", "求财", "谋事", "开店", "签约", "合同"]
            if any(k in q for k in SCATTER2):
                result["pattern"] = "合处逢冲则散"
                result["description"] = f"六合本利事成，然{'世爻' if world_clashed else '应爻'}逢冲，合处逢冲则散"
                result["impact_on_verdict"] = "婚姻六合不可解冲，先成后散；散事类同"
                result["score_adjustment"] = -2.0
                return result

    # --- 双卦对比：本卦定始、变卦定终（《黄金策》"合处逢冲事已散，冲中逢合事迟成"）---
    changed_name = (hex_result.get("changed_hexagram") or {}).get("name") or ""
    if changed_name and changed_name != hex_name:
        # 同一口径（对应位三对地支）分别判本卦与变卦，两个 kind 才可比
        orig_kind = _hexagram_he_chong_kind(hex_name)
        chg_kind = _hexagram_he_chong_kind(changed_name)
        orig_he, orig_chong = orig_kind == "六合卦", orig_kind == "六冲卦"
        chg_he, chg_chong = chg_kind == "六合卦", chg_kind == "六冲卦"
        if orig_he and chg_chong:
            result["pattern"] = "合处逢冲事已散"
            result["description"] = (
                f"本卦{hex_name}六合（始合），变卦{changed_name}六冲（终冲）——"
                f"合处逢冲，事已散（《黄金策》）"
            )
            result["impact_on_verdict"] = "先合后散：开头顺、终局散，先成后败之象"
            result["score_adjustment"] = -1.5
            return result
        if orig_chong and chg_he:
            result["pattern"] = "冲中逢合事迟成"
            result["description"] = (
                f"本卦{hex_name}六冲（始散），变卦{changed_name}六合（终合）——"
                f"冲中逢合，事迟成（《黄金策》）"
            )
            result["impact_on_verdict"] = "先散后合：开头受阻、终局有成，成之迟而非不成"
            result["score_adjustment"] = 1.5
            return result

    return result


def _detect_special_pattern(step3_data: dict, step2_data: dict, step4_data: dict, hex_result: dict) -> dict:
    """
    特殊格局识别 — 当标准旺相休囚死规则被逆转时触发。

    检测四种高级格局：
    1. 从格 (Following Pattern) — 用神极弱，顺势从强
    2. 专旺格 (Dominant Element) — 一气独旺
    3. 两神成象格 — 两元素各据一方
    4. 化格 (Transformation) — 三合化气

    Parameters
    ----------
    step3_data : dict
        Step3 断旺结果（含 effective_score 等）
    step2_data : dict
        Step2 定用结果（含 用神五行、原神/忌神 等）
    step4_data : dict
        Step4 察变结果（含 moving_analysis 等）
    hex_result : dict
        完整卦象结果（含 original_hexagram, advanced_analysis 等）

    Returns
    -------
    dict
        {
            "pattern": None | "从格" | "专旺格" | "两神成象" | "化格",
            "description": str,
            "impact_on_verdict": str,
            "rule_applied": str,
            "score_adjustment": float,  # 对 final_score 的调整量
        }
    """
    # --- 优先检查古籍经典格局（这些格局优先于从格等高级格局） ---
    question = hex_result.get("question", "")
    empty_branches = hex_result.get("empty_branches", [])

    # 疾厄格局（近病逢空/逢合/逢冲）— 传入 step4_data 以增强动爻化空检测
    illness_pattern = _detect_classical_illness_pattern(question, step2_data, step3_data, empty_branches, step4_data=step4_data, hex_result=hex_result)
    if illness_pattern["pattern"]:
        return illness_pattern

    # 六合/六冲交互格局（冲中逢合/合处逢冲）
    harmony_clash_pattern = _detect_hexagram_harmony_clash_pattern(question, hex_result, step4_data)
    if harmony_clash_pattern["pattern"]:
        # 六冲主散 + 合伙类问题 + 用神旺 → 追加减分（用神虽旺但合伙难持久）
        if (harmony_clash_pattern.get("pattern") == "六冲主散"
                and ("合伙" in question)):
            try:
                ug_score_s5 = float(step3_data.get("effective_score", 2.5))
            except (TypeError, ValueError):
                ug_score_s5 = 2.5
            if ug_score_s5 >= 3.5:
                harmony_clash_pattern["score_adjustment"] -= 0.5
                harmony_clash_pattern["description"] += "（用神虽旺，合伙六冲终难持久）"
                harmony_clash_pattern["impact_on_verdict"] = (
                    (harmony_clash_pattern.get("impact_on_verdict") or "")
                    + "——用神虽旺而合伙难持久，额外减分"
                )
        return harmony_clash_pattern

    use_god_score = step3_data.get("effective_score", 2.5)
    hex_info = hex_result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    # Normalize score to float
    try:
        use_god_score = float(use_god_score)
    except (TypeError, ValueError):
        use_god_score = 2.5

    # ── Count elements in hexagram ──
    elem_counts: dict[str, int] = {}
    for yao in yao_lines:
        elem = yao.get("element", "")
        if not elem:
            branch = yao.get("earthly_branch", "")
            elem = _branch_element(branch)
        if elem:
            elem_counts[elem] = elem_counts.get(elem, 0) + 1

    # ── Check 1: 从格 (Following Pattern) ──
    # Condition: 用神极弱(<-1.0), 原神无援(<1.5), 忌神极旺(>3.5) or absent,
    #            all moving lines trend toward 忌神, NO 冲中逢合救应
    # ⚠️ 从格为极端罕见格局，必须严格判定，避免误判正常弱卦
    if use_god_score < -1.0:
        yuan_shen = step2_data.get("yuan_shen", {}) or {}
        ji_shen = step2_data.get("ji_shen", {}) or {}
        yuan_positions = yuan_shen.get("positions", []) or []
        ji_positions = ji_shen.get("positions", []) or []

        # 原神评估：无位置或位置少则视为无援
        yuan_shen_weak = len(yuan_positions) == 0
        if not yuan_shen_weak and yuan_positions:
            # Check if yuan_shen has any moving line support
            yuan_moving = [p for p in yuan_positions if p.get("is_moving")]
            yuan_shen_weak = len(yuan_moving) == 0 and len(yuan_positions) <= 1

        # 忌神评估：有多个位置视为极旺
        ji_shen_strong = len(ji_positions) >= 2

        # 若有"冲中逢合"、"化合"等明显救应模式，不从格
        step4_details = step4_data.get("details", []) if step4_data else []
        has_rescue = False
        for m in step4_details:
            ct = m.get("change_type", "")
            if ct in ("化合", "六合", "三合", "化进神"):
                has_rescue = True
                break
        if has_rescue:
            pass  # skip 从格
        elif ji_shen_strong and yuan_shen_weak:
            return {
                "pattern": "从格",
                "description": f"用神极弱（{use_god_score:.2f}）原神无援，忌神独旺（{len(ji_positions)}位），顺势从之",
                "impact_on_verdict": "反转标准判断——本应判凶反为吉，用神弃命从强",
                "rule_applied": "《增删易》'弱极反旺，从格为用'",
                "score_adjustment": 3.0,
            }

    # ── Check 1b: 原神绝位·用神失源 (绝处逢生反断为凶) ──
    # 条件：用神偏弱(score<2.0) + 原神不现或极弱(无实际爻位) + 无动变救援 → 大凶
    # 区别于从格：不反转方向(不加分)，而是强化凶断(减分)
    # 《增删易》"绝处逢生反断为凶"：原神无援→用神气绝→断凶不疑
    if use_god_score < 2.0:
        yuan_shen2 = step2_data.get("yuan_shen", {}) or {}
        yuan_positions2 = yuan_shen2.get("positions", []) or []
        yuan_fucang2 = yuan_shen2.get("fu_cang", None)
        # 原神不现：完全无位置，或仅有伏藏(飞神下的隐藏原神)
        _yuan_absent = len(yuan_positions2) == 0
        # 无动变内生救援(step4无正面力量)
        step4_details2 = step4_data.get("details", []) if step4_data else []
        _has_positive_change = any(
            isinstance(m, dict) and m.get("effect_score", 0) > 0.3
            for m in step4_details2
        )
        net_effect2 = step4_data.get("net_effect", 0) if step4_data else 0
        # 触发条件：原神完全不现 + 用神偏弱 + 无动变正面效应 + net_effect不显著正
        if _yuan_absent and not _has_positive_change and (isinstance(net_effect2, (int, float)) and net_effect2 <= 0.1):
            return {
                "pattern": "原神绝位·用神失源",
                "description": f"用神弱（{use_god_score:.2f}）原神不现（仅伏藏或无援），绝处逢生反断为凶",
                "impact_on_verdict": "原神气绝不能生用，用神孤立无援→大凶",
                "rule_applied": "《增删易》'原神无援，用神气绝，断凶不疑'",
                "score_adjustment": -2.0,
            }

    # ── Check 2: 专旺格 (Dominant Element Pattern) ──
    # Condition: one element >= 4 of 6 yao, score >= 4.0
    if elem_counts:
        max_elem = max(elem_counts, key=elem_counts.get)
        max_count = elem_counts[max_elem]
        if max_count >= 4:
            return {
                "pattern": "专旺格",
                "description": f"{max_elem}气独旺（{max_count}/6爻）",
                "impact_on_verdict": "喜顺泄不宜克逆——用神属此元素大吉，他元素不振无碍",
                "rule_applied": "《卜筮正宗》'专旺喜泄不喜克'",
                "score_adjustment": 0.0,  # 不直接加分，而是降低忌神惩罚
            }

    # ── Check 3: 两神成象格 (Two Element Coexistence) ──
    # Condition: exactly 2 elements, each ~3 yao, no major 相克 in moving lines
    if len(elem_counts) == 2:
        elems = list(elem_counts.keys())
        if abs(elem_counts[elems[0]] - elem_counts[elems[1]]) <= 1:
            # Check no major attacking in moving lines
            has_major_attack = False
            for m in moving_analysis:
                ct = m.get("change_type", "")
                if ct in ("回头克", "化墓", "化绝"):
                    has_major_attack = True
                    break
            if not has_major_attack:
                return {
                    "pattern": "两神成象",
                    "description": f"{elems[0]}（{elem_counts[elems[0]]}）与{elems[1]}（{elem_counts[elems[1]]}）各据一方，势均力敌",
                    "impact_on_verdict": "视用神所在方之旺衰定吉凶——用神方旺则吉",
                    "rule_applied": "《增删易》'两象平衡以用神方取'",
                    "score_adjustment": 0.0,
                }

    # ── Check 3b: 三会方局（优先于三合；《三命通会》寅卯辰会东方木、巳午未会南方火、
    #    申酉戌会西方金、亥子丑会北方水）──
    # 一季三支之气全，力大于三合（三合是隔三之支：长生-帝旺-墓）。判据只认"三支俱现
    # 于本卦"（含日辰/月建补一字）；三会成立时不再按三合破局论——三会不是三合，
    # 拿三合的破局条件去套三会属误判（本函数在化格之前先认三会，即为此）。
    # 分类只给象（用神会入／会成他气），寒暖燥湿为通行取象，不作为本条加减依据。
    _bl = hexagram_branches(hex_info.get("name", "")) or []
    _dt = hex_result.get("divination_time", {}) or {}
    _m_br = (_dt.get("month_stem_branch", "") or "")[1:]
    _d_br = (_dt.get("day_stem_branch", "") or "")[1:]
    for _hui_elem, _hui_branches in SAN_HUI_GROUPS.items():
        _missing = [b for b in _hui_branches if b not in _bl]
        if len(_missing) == 1 and _missing[0] in (_m_br, _d_br):
            _via = "月建" if _missing[0] == _m_br else "日辰"
        elif not _missing:
            _via = "本卦三支俱现"
        else:
            continue
        _hui_desc = f"{''.join(_hui_branches)}会{_hui_elem}方局（{_via}）"
        if use_god_score >= 3.5:
            return {
                "pattern": "三会局",
                "description": f"{_hui_desc}，用神旺而随局，气聚一方",
                "impact_on_verdict": "三会力大于三合，用神旺则局助其势，事有可成之基",
                "rule_applied": "《三命通会》三会方局：寅卯辰会木、巳午未会火、申酉戌会金、亥子丑会水",
                "score_adjustment": 0.5,
            }
        if use_god_score <= 1.5:
            return {
                "pattern": "三会局",
                "description": f"{_hui_desc}，用神衰而局气偏枯，独木难支",
                "impact_on_verdict": "局气虽聚而用神不任，凶中无援之象",
                "rule_applied": "《三命通会》三会方局；用神衰则不受局助",
                "score_adjustment": -0.5,
            }
        return {
            "pattern": "三会局",
            "description": f"{_hui_desc}，用神中和，随局而尚未定",
            "impact_on_verdict": "三会成局而不偏枯，成事之机在用神得力之时",
            "rule_applied": "《三命通会》三会方局",
            "score_adjustment": 0.0,
        }

    # ── Check 4: 化格 (Transformation Pattern) ──
    # Condition: 用神本身的动爻参与三合化才算真正化格
    # ⚠️ 化格是极端罕见格局，普通三合但不涉及用神动爻时不触发
    advanced = hex_result.get("advanced_analysis", {})
    if advanced and isinstance(advanced, dict):
        tc_data = advanced.get("triple_combo", {})
        if isinstance(tc_data, dict) and tc_data.get("has_triple_combo"):
            use_god_elem = step2_data.get("use_god_element", "土")
            # 获取用神动爻位置列表（用神发动才算化）
            use_god_moving_positions = set()
            for d in (step4_data.get("details") or step4_data.get("moving_details") or []):
                if isinstance(d, dict):
                    d_pos = d.get("position") or d.get("from_position") or 0
                    d_rel = d.get("change_type", "")
                    if d_pos and d_rel and "化合" not in d_rel and "六合" not in d_rel:
                        # 检查这条动爻是否是用神
                        d_orig_branch = d.get("original_branch", d.get("from_branch", ""))
                        if d_orig_branch:
                            d_orig_elem = _branch_element(d_orig_branch)
                            if d_orig_elem == use_god_elem:
                                use_god_moving_positions.add(d_pos)
            details = tc_data.get("details", []) or []
            for combo in details:
                target_elem = combo.get("element", "")
                positions = combo.get("positions", []) or []
                if target_elem and target_elem != use_god_elem:
                    # 严格条件: 用神动爻本身在三合中，且化出非用神元素
                    involved = use_god_moving_positions & set(positions or [])
                    if involved:
                        return {
                            "pattern": "化格",
                            "description": f"三合化{target_elem}，用神动爻{involved}随局而化",
                            "impact_on_verdict": f"用神随三合化{target_elem}，+0.5",
                            "rule_applied": "三合化气，用神发动随局而变",
                            "score_adjustment": +0.5,
                        }

    # ── No special pattern ──
    return {
        "pattern": None,
        "description": "无特殊格局，按常规断法",
        "impact_on_verdict": "无调整",
        "rule_applied": "常规旺衰断法",
        "score_adjustment": 0.0,
    }


def _forms_hexagram_harmony(branch1: str, branch2: str) -> bool:
    """Check if two branches form 六合."""
    if not branch1 or not branch2:
        return False
    key = f"{branch1}{branch2}"
    return key in _HEXAGRAM_HARMONY_SET


def _check_greedy_harmony(
    yao_lines: list[dict],
    moving_lines: list[dict],
    day_branch: str,
    month_branch: str,
    use_god_category: str,
    yuan_shen_element: str,
    ji_shen_element: str,
    palace_element: str,
) -> tuple[float, list[dict]]:
    """
    贪合忘生克检测 — rule from 《增删易》.

    When a yao forms 六合 with another yao or with 日辰/月建, it becomes "贪合" —
    obsessed with the conjunction. This causes:
    - 原神贪合忘生 → the 原神 fails to generate its 用神
    - 忌神贪合忘克 → the 忌神 fails to attack its 用神 (beneficial)

    Parameters
    ----------
    yao_lines : list[dict]
        All 6 yao lines.
    moving_lines : list[dict]
        Subset of yao_lines that are moving (动爻 or 暗动).
    day_branch : str
        Day branch.
    month_branch : str
        Month branch.
    use_god_category : str
        The use god relation (e.g. "妻财", "官鬼").
    yuan_shen_element : str
        Element of the 原神.
    ji_shen_element : str
        Element of the 忌神.
    palace_element : str
        Element of the palace.

    Returns
    -------
    tuple[float, list[dict]]
        (score_adjustment, issues_list). Positive = beneficial, negative = harmful.
        Empty list if no issues found.
    """
    if not moving_lines:
        return 0.0, []

    issues = []
    score_adjustment = 0.0
    yuan_shen_relation_name = _element_to_relation(yuan_shen_element, palace_element) if yuan_shen_element else ""
    ji_shen_relation_name = _element_to_relation(ji_shen_element, palace_element) if ji_shen_element else ""

    for yao in moving_lines:
        pos = yao.get("position", 0)
        orig_branch = yao.get("earthly_branch", "") or yao.get("branch", "")
        orig_relation = yao.get("six_relation", "")
        orig_element = _branch_element(orig_branch) if orig_branch else ""
        changed_branch = yao.get("changed_branch", "")

        # Determine the branch to check for harmony:
        # Use the original branch if static/hidden-moved, or changed branch if moving
        branches_to_check = [orig_branch]
        if changed_branch:
            branches_to_check.append(changed_branch)

        for target_branch in branches_to_check:
            if not target_branch:
                continue

            # Check 合 with 日辰
            if _forms_hexagram_harmony(target_branch, day_branch):
                # Classify by role
                if orig_relation == yuan_shen_relation_name or orig_element == yuan_shen_element:
                    # 原神贪合忘生 → harmful:原神 can't generate use god
                    effect_score = -0.3
                    reason = f"原神{orig_relation}（{_pos_to_name(pos)}爻·{orig_branch}）与{day_branch}日六合，贪合忘生用神"
                    issues.append({
                        "type": "原神贪合忘生",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"日辰{day_branch}",
                        "effect": "原神贪合，暂不能生用神（减力）",
                        "benefit_or_loss": "unfavorable",
                        "score_effect": effect_score,
                    })
                    score_adjustment += effect_score

                elif orig_relation == ji_shen_relation_name or orig_element == ji_shen_element:
                    # 忌神贪合忘克 → beneficial:忌神 can't attack use god
                    effect_score = 0.2
                    reason = f"忌神{orig_relation}（{_pos_to_name(pos)}爻·{orig_branch}）与{day_branch}日六合，贪合忘克用神"
                    issues.append({
                        "type": "忌神贪合忘克",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"日辰{day_branch}",
                        "effect": "忌神贪合，暂不克用神（减凶）",
                        "benefit_or_loss": "favorable",
                        "score_effect": effect_score,
                    })
                    score_adjustment += effect_score

                elif orig_relation == use_god_category:
                    # 用神本身被合 → 合绊，暂受阻滞
                    effect_score = -0.2
                    reason = f"用神（{_pos_to_name(pos)}爻·{orig_branch}）与{day_branch}日六合，合绊暂滞"
                    issues.append({
                        "type": "用神被合",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"日辰{day_branch}",
                        "effect": "用神被合绊，暂受阻滞",
                        "benefit_or_loss": "neutral",
                        "score_effect": effect_score,
                    })
                    score_adjustment += effect_score
                else:
                    # Other lines harmonized with day
                    issues.append({
                        "type": "合绊",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"日辰{day_branch}",
                        "effect": f"{orig_relation}{_pos_to_name(pos)}爻与日合绊",
                        "benefit_or_loss": "neutral",
                        "score_effect": 0.0,
                    })

            # Check 合 with 月建
            if month_branch and _forms_hexagram_harmony(target_branch, month_branch):
                if orig_relation == yuan_shen_relation_name or orig_element == yuan_shen_element:
                    effect_score = -0.2
                    reason = f"原神{orig_relation}（{_pos_to_name(pos)}爻·{orig_branch}）与{month_branch}月六合，贪合忘生"
                    issues.append({
                        "type": "原神贪合忘生",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"月建{month_branch}",
                        "effect": "原神与月合绊，暂不能生用神",
                        "benefit_or_loss": "unfavorable",
                        "score_effect": effect_score,
                    })
                    score_adjustment += effect_score

                elif orig_relation == ji_shen_relation_name or orig_element == ji_shen_element:
                    effect_score = 0.15
                    reason = f"忌神{orig_relation}（{_pos_to_name(pos)}爻·{orig_branch}）与{month_branch}月六合，贪合忘克"
                    issues.append({
                        "type": "忌神贪合忘克",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"月建{month_branch}",
                        "effect": "忌神与月合绊，暂不克用神（减凶）",
                        "benefit_or_loss": "favorable",
                        "score_effect": effect_score,
                    })
                    score_adjustment += effect_score
                else:
                    issues.append({
                        "type": "合绊",
                        "position": pos,
                        "name": _pos_to_name(pos),
                        "relation": orig_relation,
                        "branch": orig_branch,
                        "harmony_with": f"月建{month_branch}",
                        "effect": f"{orig_relation}{_pos_to_name(pos)}爻与月合绊",
                        "benefit_or_loss": "neutral",
                        "score_effect": 0.0,
                    })

    return round(score_adjustment, 2), issues



__all__ = [
    "step4_analyze_changes",
    "_user_reason",
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
]
