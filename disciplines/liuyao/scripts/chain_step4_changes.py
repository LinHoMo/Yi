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


