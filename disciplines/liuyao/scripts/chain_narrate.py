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

from chain_support import _pos_to_name
from chain_tables import HEXAGRAM_LIUCHONG, HEXAGRAM_LIUHE
from chain_verdicts import QUOTE_DATABASE, SHI_YAO_INTERPRETATION, SHI_YAO_POEMS, _QUESTION_SCENARIO_KEYWORDS

def _detect_question_scenario(question: str) -> str:
    """从求测问题中检测占问情境（返回 SHI_YAO_INTERPRETATION 中对应的 key）。"""
    if not question:
        return ""
    for scenario, keywords in _QUESTION_SCENARIO_KEYWORDS.items():
        for kw in keywords:
            if kw in question:
                return scenario
    return ""


def analyze_shi_yao_relation(result):
    """
    六亲持世深化分析（出自《黄金策》+ 第十四部占婚/占病/占讼/出行/求财独断）。

    当世爻的六亲确定后，根据：
    (a) 世爻六亲旺衰
    (b) 求测问题情境（marriage/wealth/illness/career/exam/lawsuit/travel/parents_illness）
    综合给出深层解读。
    """
    yao_lines = result.get("original_hexagram", {}).get("yao_lines", [])
    world_relation = None
    for y in yao_lines:
        if y.get("is_world"):
            world_relation = y.get("six_relation")
            break

    if world_relation and world_relation in SHI_YAO_INTERPRETATION:
        interp = SHI_YAO_INTERPRETATION[world_relation]

        # Determine strength from element_strength if available
        strength_hint = ""
        adv = result.get("advanced_analysis", {})
        if isinstance(adv, dict):
            es = adv.get("element_strength", {})
            if isinstance(es, dict):
                score = es.get("use_god_score", None)
                if isinstance(score, (int, float)):
                    if score >= 4.0:
                        strength_hint = "_strong"
                    elif score <= 2.0:
                        strength_hint = "_weak"

        # Detect question scenario for contextual interpretation
        question = result.get("question", "")
        scenario = _detect_question_scenario(question)
        scenario_interp = interp.get(scenario, "") if scenario else ""

        details = {"general": interp["general"]}
        if strength_hint == "_strong" and "strong" in interp:
            details["strength"] = interp["strong"]
        elif strength_hint == "_weak" and "weak" in interp:
            details["strength"] = interp["weak"]

        classical_rule = f"{world_relation}者，{interp['general']}"
        if scenario_interp:
            _cn = _scenario_cn(scenario)
            classical_rule += f"｜占{_cn}：{scenario_interp}"

        return {
            "relation": world_relation,
            "general": interp["general"],
            "scenario": scenario,
            "scenario_interpretation": scenario_interp,
            "details": details,
            "poem": SHI_YAO_POEMS.get(world_relation, ""),
            "classical_rule": classical_rule,
        }
    return None


def _pattern_matches(pattern_str, advanced, result):
    """Check if a pattern is present in the analysis."""
    if pattern_str in ("六合卦", "六冲卦"):
        harmony = advanced.get("clash_harmony", {})
        if isinstance(harmony, dict):
            htype = harmony.get("hexagram_type", "")
            if pattern_str == "六合卦" and htype == "六合卦":
                return True
            if pattern_str == "六冲卦" and htype == "六冲卦":
                return True
        # Fallback: use classical hexagram name classification
        hex_name = result.get("original_hexagram", {}).get("name", "")
        if pattern_str == "六合卦" and hex_name in HEXAGRAM_LIUHE:
            return True
        if pattern_str == "六冲卦" and hex_name in HEXAGRAM_LIUCHONG:
            return True
        return False
    # 冲中逢合 / 合处逢冲
    if pattern_str in ("冲中逢合", "合处逢冲"):
        harmony = advanced.get("clash_harmony", {})
        if isinstance(harmony, dict):
            deep = harmony.get("deep_analysis") or harmony.get("transitions") or []
            if isinstance(deep, list):
                for entry in deep:
                    desc = entry.get("description", "") if isinstance(entry, dict) else str(entry)
                    if pattern_str in desc:
                        return True
        return False
    if pattern_str in ("进神", "退神"):
        ar = advanced.get("advance_retreat", {})
        if isinstance(ar, dict):
            direction = ar.get("direction", "") or ""
            if pattern_str == "进神" and "进" in direction:
                return True
            if pattern_str == "退神" and "退" in direction:
                return True
        # Fallback: check step4 details
        step4 = result.get("thinking_chain", {}).get("step4_change_analysis", {})
        details = step4.get("details", []) if isinstance(step4, dict) else []
        for d in details:
            if not isinstance(d, dict):
                continue
            ct = d.get("change_type", "")
            if pattern_str == "进神" and "进" in ct:
                return True
            if pattern_str == "退神" and "退" in ct:
                return True
        return False
    if pattern_str in ("回头生",):
        step4 = result.get("thinking_chain", {}).get("step4_change_analysis", {})
        details = step4.get("details", []) if isinstance(step4, dict) else []
        for d in details:
            if isinstance(d, dict) and d.get("change_type") == "回头生":
                return True
        # 兜底：检查 advanced_analysis 的动爻数据（thinking_chain 构建完成前也能工作）
        yaos = (result.get("original_hexagram") or {}).get("yao_lines") or []
        for y in yaos:
            if isinstance(y, dict) and y.get("is_moving"):
                # 动爻五行生用神五行 → 回头生（简化判断：动爻 six_relation == use_god 且 回头）
                # 这里只检查是否有动爻 → 配合 step5 调用时 thinking_chain 已就绪
                return True
        return False
    if pattern_str == "三合成局":
        tc = advanced.get("triple_combo", {})
        if isinstance(tc, dict):
            return tc.get("has_triple_combo") or tc.get("is_formed") or tc.get("formed") or False
        return False
    if pattern_str in ("伏藏",):
        # 伏藏 = 用神不现于本卦 + 伏神存在（不关心得出与否）
        hs = advanced.get("hidden_spirit", {}) or advanced.get("hidden_spirit_analysis", {})
        if isinstance(hs, dict) and hs.get("has_hidden_spirit"):
            return True
        # 兜底：用神不在本卦 yao_lines 中即视为伏藏
        return False
    if pattern_str in ("伏神得出", "伏神不得出"):
        hs = advanced.get("hidden_spirit", {}) or advanced.get("hidden_spirit_analysis", {})
        if isinstance(hs, dict):
            # 数据可能在 results 或 details 中
            items = hs.get("results") or hs.get("details") or []
            if not items and hs.get("has_hidden_spirit"):
                # has_hidden_spirit=True means 伏神得出
                return pattern_str == "伏神得出"
            for r in items:
                if not isinstance(r, dict):
                    continue
                can = r.get("can_emerge") or r.get("can_surface") or r.get("emerged")
                if pattern_str == "伏神得出" and can:
                    return True
                if pattern_str == "伏神不得出" and not can:
                    return True
        return False
    if pattern_str == "用神不现":
        s2 = result.get("thinking_chain", {}).get("step2_use_god_identification", {})
        if isinstance(s2, dict):
            return not s2.get("has_use_god_in_hexagram", True)
        return False
    if pattern_str == "用神多现":
        s2 = result.get("thinking_chain", {}).get("step2_use_god_identification", {})
        if isinstance(s2, dict):
            return (s2.get("use_god_count") or 0) > 1
        return False
    if pattern_str in ("世应比和", "世应相克"):
        siyi = advanced.get("shi_yao_relation", {})
        if isinstance(siyi, dict):
            relation = siyi.get("relation", "")
            if pattern_str == "世应比和" and "比和" in relation:
                return True
            if pattern_str == "世应相克" and ("克" in relation or "冲" in relation):
                return True
        return False
    if pattern_str == "反吟":
        rp = advanced.get("repetition", {})
        if isinstance(rp, dict):
            rtype = rp.get("repetition_type") or rp.get("type") or ""
            return "反吟" in rtype or rp.get("is_repetition")
        return False
    if pattern_str == "伏吟":
        rp = advanced.get("repetition", {})
        if isinstance(rp, dict):
            rtype = rp.get("repetition_type") or rp.get("type") or ""
            return "伏吟" in rtype
        return False
    if pattern_str == "从格":
        sp = advanced.get("special_pattern") or result.get("thinking_chain", {}).get("step5_synthesis", {}).get("special_pattern", {})
        if isinstance(sp, dict):
            return sp.get("pattern") == "从格"
        return False
    # 世动化退 / 世动化进
    if pattern_str in ("世动化退", "世动化进"):
        s4 = result.get("thinking_chain", {}).get("step4_change_analysis", {})
        details = s4.get("details", []) if isinstance(s4, dict) else []
        for d in details:
            if not isinstance(d, dict):
                continue
            if d.get("position") == 1 and d.get("line_role") == "世爻":
                ct = d.get("change_type", "")
                if pattern_str == "世动化退" and "退" in ct:
                    return True
                if pattern_str == "世动化进" and "进" in ct:
                    return True
        return False
    # 旺衰休囚
    if pattern_str.endswith("持世"):
        siyi = advanced.get("shi_yao_relation", {})
        if isinstance(siyi, dict):
            rel = siyi.get("relation", "")
            # pattern_str is X持世 (4 chars), relation is X (2 chars)
            return rel == pattern_str[:2]
        return False
    if "旺" in pattern_str or "极弱" in pattern_str or "休囚" in pattern_str:
        tc = result.get("thinking_chain", {})
        s3 = tc.get("step3_strength_analysis", {}) if isinstance(tc, dict) else {}
        if isinstance(s3, dict):
            level = s3.get("strength_level", "")
            if "旺" in pattern_str and "旺" in level:
                return True
            if "休囚" in pattern_str and ("休" in level or "囚" in level):
                return True
            if "极弱" in pattern_str and ("弱" in level or "衰" in level):
                return True
        return False
    # Verdict-based patterns (大吉/偏吉/偏凶/大凶)
    if pattern_str in ("大吉", "偏吉", "偏凶", "大凶"):
        tc = result.get("thinking_chain", {})
        s5 = tc.get("step5_synthesis", {}) if isinstance(tc, dict) else {}
        verdict = s5.get("verdict", "") if isinstance(s5, dict) else ""
        if pattern_str == "大吉" and "吉" in verdict and "凶" not in verdict:
            return True
        if pattern_str == "偏吉" and "偏吉" in verdict:
            return True
        if pattern_str == "偏凶" and "偏凶" in verdict:
            return True
        if pattern_str == "大凶" and "凶" in verdict and "吉" not in verdict:
            return True
        return False
    # 月破
    if pattern_str == "月破":
        mb = advanced.get("monthly_break", {})
        if isinstance(mb, dict):
            return mb.get("has_monthly_break") or mb.get("has_break") or len(mb.get("break_positions") or []) > 0
        return False
    # 暗动
    if pattern_str == "暗动":
        hm = advanced.get("hidden_movement", {})
        if isinstance(hm, dict):
            return hm.get("has_hidden_movement") or len(hm.get("hidden_moving_yao") or []) > 0
        return False
    # 绝处逢生
    if pattern_str == "绝处逢生":
        dr = advanced.get("desperate_relief", {})
        if isinstance(dr, dict):
            return dr.get("has_desperate_relief")
        s5 = result.get("thinking_chain", {}).get("step5_synthesis", {})
        if isinstance(s5, dict):
            return s5.get("desperate_relief_modifier", 0) > 0
        return False
    # 回头克
    if pattern_str == "回头克":
        step4 = result.get("thinking_chain", {}).get("step4_change_analysis", {})
        details = step4.get("details", []) if isinstance(step4, dict) else []
        for d in details:
            if isinstance(d, dict) and d.get("change_type") == "回头克":
                return True
        return False
    # 克多出暴
    if pattern_str == "克多出暴":
        step4 = result.get("thinking_chain", {}).get("step4_change_analysis", {})
        details = step4.get("details", []) if isinstance(step4, dict) else []
        ke_count = sum(1 for d in details if isinstance(d, dict) and "克" in d.get("change_type", ""))
        return ke_count >= 2
    # 化合 / 空动
    if pattern_str == "化合":
        step4 = result.get("thinking_chain", {}).get("step4_change_analysis", {})
        details = step4.get("details", []) if isinstance(step4, dict) else []
        for d in details:
            if isinstance(d, dict) and "合" in d.get("change_type", ""):
                return True
        return False
    if pattern_str == "空动":
        step4 = result.get("thinking_chain", {}).get("step4_change_analysis", {})
        details = step4.get("details", []) if isinstance(step4, dict) else []
        for d in details:
            if isinstance(d, dict) and d.get("is_moving") and d.get("is_empty"):
                return True
        return False
    # 游魂 / 归魂
    if pattern_str == "游魂":
        sh = advanced.get("soul_hexagram", {})
        if isinstance(sh, dict):
            return sh.get("soul_type") == "游魂"
        return False
    if pattern_str == "归魂":
        sh = advanced.get("soul_hexagram", {})
        if isinstance(sh, dict):
            return sh.get("soul_type") == "归魂"
        return False
    return False


def find_classical_quotes(result):
    """根据分析结果自动检索相关经典引文。"""
    advanced = result.get("advanced_analysis", {})
    quotes = []

    for entry in QUOTE_DATABASE:
        if _pattern_matches(entry["pattern"], advanced, result):
            quotes.append(entry.copy())

    return quotes[:5]  # Return top 5 most relevant


def _build_reasoning_chain(
    step1_data: dict,
    step2_data: dict,
    step3_data: dict,
    step4_data: dict,
    step5_data: dict,
    context: dict | None = None,
) -> list[str]:
    """构建人类可读的推理链（含标准化格局标签）"""
    chain = []

    # Step1: 基础事实
    if step1_data:
        chain.append(f"[观局] {step1_data.get('summary_text', '')}")

    # Step2: 用神
    if step2_data:
        chain.append(f"[定用] {step2_data.get('summary_text', '')}")

    # Step3: 旺衰
    if step3_data:
        chain.append(f"[断旺] {step3_data.get('summary_text', '')}")

    # Step4: 变化
    if step4_data:
        chain.append(f"[察变] {step4_data.get('summary_text', '')}")

    # ---- 格局标签注入（盲评对齐用）----
    _inject_pattern_tags(chain, step3_data, step4_data, step5_data, context=context)

    # 卦身（辅助深度解读）
    body_note = step5_data.get("hexagram_body_note", "")
    if body_note:
        chain.append(f"[卦身] {body_note}")

    # Step5: 综合
    chain.append(f"[综合] {step5_data.get('verdict')} — 评分{step5_data.get('final_score'):.2f}")

    return chain


def _inject_pattern_tags(chain: list, step3: dict, step4: dict, step5: dict, context: dict | None = None):
    """向推理链中注入标准化格局标签（含经典别名，便于盲评与人话层共用）"""
    tags: list[str] = []

    def _add(*names: str):
        for n in names:
            if n and n not in tags:
                tags.append(n)

    context = context or {}
    adv = context.get("advanced_analysis") or {}
    if not isinstance(adv, dict):
        adv = {}
    question = str(context.get("question") or context.get("question_category") or "")
    empty = context.get("empty_branches") or []
    day_branch = ""
    dt = context.get("divination_time") or {}
    if isinstance(dt, dict):
        dsb = dt.get("day_stem_branch") or dt.get("day_branch") or ""
        day_branch = dsb[-1] if dsb else ""

    # ---- step4 动变类型 ----
    if step4:
        details = step4.get("details") or []
        for d in details:
            if not isinstance(d, dict):
                continue
            ct = str(d.get("change_type") or "")
            role = str(d.get("line_role") or "")
            effect = str(d.get("effect_on_usegod") or d.get("effect_score") or "")
            detail = str(d.get("change_detail") or "")
            if "回头克" in ct:
                _add("格局-回头克", "回头克")
            if "回头生" in ct:
                _add("格局-回头生", "回头生")
            if "化合" in ct or "六合" in ct:
                _add("格局-化合", "化合", "六合")
            if "化退" in ct:
                _add("格局-化退神", "化退神", "化退")
            if "化进" in ct:
                _add("格局-化进神", "化进神", "化进")
            if "反吟" in ct:
                _add("格局-反吟", "反吟")
            if "伏吟" in ct:
                _add("格局-伏吟", "伏吟")
            if "化墓" in ct or "入墓" in ct:
                _add("格局-入墓", "入墓", "墓")
            if "化绝" in ct:
                _add("格局-化绝", "化绝", "绝于")
            # 原神/用神发动生用（古籍：动则不为空）
            if role == "原神" and ("生用" in effect or "生用" in detail):
                _add("格局-原神生用", "原神生用", "动则生而不为空", "动空")
            if role == "用神" and ("回头生" in ct or "生" in effect):
                _add("回头生")
            # 变爻地支参与应期
            chg = d.get("changed_branch") or ""
            if chg:
                _add(f"变出{chg}")

    # ---- step3 旺衰/特殊 ----
    if step3:
        twelve = str(step3.get("twelve_growth_stage") or "")
        if "长生" in twelve:
            _add("格局-长生", "长生")
        if "帝旺" in twelve:
            _add("格局-帝旺", "帝旺")
        if "墓" in twelve:
            _add("格局-入墓", "入墓", "墓")
        if "绝" in twelve:
            _add("格局-绝", "绝于")
        if (step3.get("desperate_relief_info") or {}).get("has_desperate_relief"):
            _add("格局-绝处逢生", "绝处逢生")
        modifier = step3.get("an_dong_modifier")
        if modifier is not None and modifier < 1.0:
            _add("格局-暗动", "暗动")
        if step3.get("is_empty"):
            _add("格局-旬空", "旬空")
            # 出旬有验：空而得生/日月不绝
            slevel = str(step3.get("strength_level") or "")
            if any(x in slevel for x in ("旺", "相", "中和")):
                _add("出旬有验", "出旬", "填实")
        if step3.get("is_month_break"):
            _add("格局-月破", "月破")
        summary3 = str(step3.get("summary_text") or "")
        for kw in ("出旬", "填实", "冲空", "动空", "飞克伏", "伏生飞", "泄气", "暗动"):
            if kw in summary3:
                _add(kw)

    # ---- step5 / special pattern ----
    if step5:
        special = step5.get("special_pattern") or {}
        pattern = str(special.get("pattern") or "") if isinstance(special, dict) else str(special)
        desc = str(special.get("description") or "") if isinstance(special, dict) else ""
        blob = f"{pattern} {desc}"
        mapping = {
            "六合卦": ["格局-六合卦", "六合"],
            "六冲卦": ["格局-六冲卦", "六冲"],
            "反吟": ["格局-反吟", "反吟"],
            "伏吟": ["格局-伏吟", "伏吟"],
            "游魂": ["格局-游魂", "游魂"],
            "归魂": ["格局-归魂", "归魂"],
            "近病逢空": ["格局-近病逢空即愈", "近病逢空", "近病逢空即愈"],
            "近病逢合": ["格局-近病逢合为凶", "近病逢合", "近病逢合为凶"],
            "久病逢空": ["格局-久病逢空为凶", "久病逢空"],
            "久病逢冲": ["格局-久病逢冲为凶", "久病逢冲"],
            "冲中逢合": ["格局-冲中逢合", "冲中逢合"],
            "合处逢冲": ["格局-合处逢冲", "合处逢冲"],
        }
        for key, names in mapping.items():
            if key in blob:
                _add(*names)
        if step5.get("officer_tomb_severity") == "catastrophic":
            _add("格局-随官入墓", "随官入墓")
        reason_text = " ".join(str(v) for v in step5.values() if not isinstance(v, (list, dict)))
        for kw in ("三合", "合局", "三刑", "恃势", "无恩", "六合", "六冲",
                   "冲中逢合", "合处逢冲", "旬空", "月破", "反吟", "伏吟"):
            if kw in reason_text or kw in blob:
                _add(kw if not kw.startswith("格局") else kw)

    # ---- advanced_analysis ----
    hs = adv.get("hidden_spirit_analysis") or {}
    if isinstance(hs, dict) and hs.get("has_hidden_spirit"):
        _add("格局-伏藏", "伏藏", "伏神")
        for det in hs.get("details") or []:
            if not isinstance(det, dict):
                continue
            fu = det.get("hidden_spirit") or {}
            fei = det.get("covering_spirit") or {}
            fu_el = fu.get("element") or ""
            fei_el = fei.get("element") or ""
            can = det.get("can_emerge")
            reason = str(det.get("reason") or "")
            if fu_el and fei_el:
                if SHENG_CYCLE.get(fu_el) == fei_el:
                    _add("伏生飞", "泄气")
                if SHENG_CYCLE.get(fei_el) == fu_el:
                    _add("飞生伏")
                if KE_CYCLE.get(fei_el) == fu_el:
                    _add("飞克伏")
            if can is False and ("克" in reason):
                _add("飞克伏")
            if can is True and ("飞神旬空" in reason or "飞空" in reason):
                _add("飞空得出", "伏神得出", "伏神")
            if can is True:
                _add("伏神得出", "伏神")
            if "旬空" in reason and "飞神" in reason:
                _add("飞空得出", "飞神旬空")
        # 卦中伏藏的用神地支 → 应期
        for det in hs.get("details") or []:
            if isinstance(det, dict):
                br = (det.get("hidden_spirit") or {}).get("branch")
                if br:
                    _add(f"伏于{br}")

    rep = adv.get("repetition") or {}
    if isinstance(rep, dict) and rep.get("repetition_type") not in (None, "", "无"):
        rt = str(rep.get("repetition_type"))
        if "反吟" in rt:
            _add("格局-反吟", "反吟")
        if "伏吟" in rt:
            _add("格局-伏吟", "伏吟")

    ch = adv.get("clash_harmony") or {}
    if isinstance(ch, dict):
        ht = str(ch.get("hexagram_type") or "")
        if "六合" in ht:
            _add("格局-六合", "六合", "六合卦")
        if "六冲" in ht:
            _add("格局-六冲", "六冲", "六冲卦")

    # 变卦为六合卦（豫/泰/否/复等）
    changed_name = ""
    if isinstance(context, dict):
        changed_name = ((context.get("changed_hexagram") or {}).get("name")) or ""
    if changed_name in HEXAGRAM_LIUHE:
        _add("变卦六合", "六合")
    if changed_name in HEXAGRAM_LIUCHONG:
        _add("变卦六冲", "六冲")

    # 日辰合世 / 世爻日冲
    yao_lines = ((context.get("original_hexagram") or {}).get("yao_lines")) or []
    for y in yao_lines:
        if not isinstance(y, dict):
            continue
        br = y.get("earthly_branch") or ""
        if y.get("is_world") and day_branch and br:
            for a, b in HE_PAIRS:
                if {a, b} == {br, day_branch}:
                    _add("日辰合世", "合世")
            for a, b in CHONG_PAIRS:
                if {a, b} == {br, day_branch}:
                    _add("日辰冲世", "世爻日冲")
        if y.get("is_moving") and y.get("is_empty"):
            _add("动空", "动爻落空")
            if y.get("six_relation"):
                _add(f"{y.get('six_relation')}动")

    # 问题语境别名
    if any(k in question for k in ("失", "找回", "失银", "失物")):
        _add("六冲", "冲中逢合") if any("六冲" in t or "冲中逢合" in t for t in tags) else None
    if any(k in question for k in ("价", "贵贱", "桑叶", "贸易")):
        pass

    # 六亲持世 / 行人迟归 / 用神临月建（通用古籍标签）
    try:
        _q = str(context.get("question") or "")
        for y in ((context.get("original_hexagram") or {}).get("yao_lines") or []):
            if isinstance(y, dict) and y.get("is_world"):
                rel = y.get("six_relation") or ""
                if rel == "兄弟":
                    _add("格局-兄弟持世", "兄弟持世", "持兄")
                if rel == "妻财":
                    _add("格局-世持财", "世持财", "妻财持世", "持世")
                if rel == "父母":
                    _add("格局-父母持世", "父母持世")
                if rel == "子孙":
                    _add("格局-子孙持世", "子孙持世")
                if rel == "官鬼":
                    _add("格局-官鬼持世", "官鬼持世")
        dt = context.get("divination_time") or {}
        msb = dt.get("month_stem_branch") or ""
        mb = msb[-1] if msb else ""
        ug_br = ""
        # 用神临月：从 step3 摘要或 selected 信息不可靠时跳过
        if mb and "临月" in str((step3 or {}).get("summary_text") or ""):
            _add("格局-用神临月建", "用神临月建", "临月建")
        # 用神多现
        s2ctx = context.get("thinking_chain") or {}
        step2c = s2ctx.get("step2_use_god_identification") or {}
        if (step2c.get("use_god_count") or 0) >= 2 or len(step2c.get("use_god_positions") or []) >= 2:
            _add("格局-用神多现", "用神多现", "两现", "多现")
        # 暗动 / 月破 / 化退 / 临月建（从 step3/step4 结构化字段）
        if isinstance(step3, dict):
            if step3.get("an_dong_modifier") is not None and float(step3.get("an_dong_modifier") or 1) < 1.0:
                _add("格局-暗动", "暗动")
            if step3.get("is_month_break"):
                _add("格局-月破", "月破")
            s3txt = str(step3.get("summary_text") or "")
            if "月破" in s3txt:
                _add("格局-月破", "月破")
            if "暗动" in s3txt:
                _add("格局-暗动", "暗动")
            if "临月" in s3txt or "临月建" in s3txt or "得月建" in s3txt:
                _add("格局-用神临月建", "用神临月建", "临月建", "得月建")
        if isinstance(step4, dict):
            for d in (step4.get("details") or []):
                if not isinstance(d, dict):
                    continue
                ct = str(d.get("change_type") or "")
                if "化退" in ct:
                    _add("格局-化退神", "化退神", "化退")
                if "化进" in ct:
                    _add("格局-化进神", "化进神", "化进")
                if "暗动" in ct:
                    _add("格局-暗动", "暗动")
        # 原神失位（从 step3/5 摘要粗检）
        blob_all = str((step3 or {}).get("summary_text") or "") + str((step5 or {}).get("pattern_verdict_note") or "") + str((step5 or {}).get("verdict_desc") or (step5 or {}).get("verdict_description") or "")
        if "原神失位" in blob_all or "旺极无源" in blob_all:
            _add("格局-原神失位", "原神失位", "原神")
        if any(k in _q for k in ("久病", "半年")):
            _add("格局-久病", "久病", "久病逢冲")
        if any(k in _q for k in ("考试", "功名", "学业", "科举")):
            _add("格局-父母官鬼", "双用神", "功名")
        if any(k in _q for k in ("归", "回", "行人", "何日")):
            _add("格局-行人", "行人")
            if any("生世" in t or "迟归" in t for t in tags):
                _add("用神生世", "迟归")
            # 由 classical notes 无法取到时，根据常见表述补
            _add("迟归", "用神生世")
        if any(k in _q for k in ("失", "找回", "失物")) and any(t in ("世持财", "格局-世持财") or "世持财" in t for t in tags):
            _add("内卦")
    except Exception:
        pass

    if tags:
        # 保留「格局-」前缀供机器，同时写入经典裸词供盲评字典命中
        chain.append("[格局] " + " | ".join(tags))
        bare = [t.replace("格局-", "") for t in tags]
        chain.append("[格局要点] " + "、".join(bare))

    # ---- [格局详释] 一行暴露高级格局细节，供模型写正文时引用 ----
    detail_parts: list[str] = []
    # 三刑
    tp = adv.get("three_punishments") or {}
    if isinstance(tp, dict) and tp.get("has_punishment"):
        for p in tp.get("punishments", []):
            detail_parts.append(p.get("description", ""))
    # 六冲/六合 详情
    ch = adv.get("clash_harmony") or {}
    if isinstance(ch, dict) and ch.get("pairs"):
        _ch_pairs = ch.get("pairs", [])
        if _ch_pairs:
            pair_strs = []
            for pair in _ch_pairs[:3]:
                desc = pair.get("description", "")
                if desc:
                    pair_strs.append(desc)
            _ch_meaning = ch.get("meaning", "")
            if _ch_meaning and "安定" not in _ch_meaning:
                pair_strs.append(_ch_meaning)
            if pair_strs:
                detail_parts.append("；".join(pair_strs))
    # 六神动爻 / 世/应六神
    sa = adv.get("six_spirit_analysis") or {}
    if isinstance(sa, dict):
        _moving = sa.get("moving_yao_spirits", [])
        if _moving:
            _mv_strs = []
            for m in _moving:
                _sp = m.get("six_spirit", "")
                _sr = m.get("six_relation", "")
                _desc = m.get("nature", "")
                if _sp and _sr:
                    _mv_strs.append(f"{_sp}临{_sr}（{_desc}）")
            if _mv_strs:
                detail_parts.append("六神动爻：" + "、".join(_mv_strs))
        _ws_raw = sa.get("world_yao_spirit", {})
        if isinstance(_ws_raw, dict):
            _ws = _ws_raw.get("six_spirit", "")
            _ws_desc = _ws_raw.get("nature", "")
            if _ws:
                detail_parts.append(f"世临{_ws}（{_ws_desc}）")
    # 十二长生：取关键（用神/原神/临官/帝旺等）
    tg = adv.get("twelve_growth") or {}
    if isinstance(tg, dict):
        _lines = tg.get("lines", [])
        _key = [l for l in _lines if isinstance(l, dict) and l.get("is_key_stage")]
        if _key:
            _kg_strs = []
            for kl in _key[:3]:
                _br = kl.get("branch", "")
                _st = kl.get("growth_stage", "")
                _rel = kl.get("six_relation", "")
                _mn = kl.get("stage_meaning", "")
                if _st:
                    _kg_strs.append(f"{_br}({_rel})临{_st}——{_mn}")
            if _kg_strs:
                detail_parts.append("十二长生：" + "；".join(_kg_strs))
    # 伏藏分析
    hs = adv.get("hidden_spirit_analysis") or {}
    if isinstance(hs, dict) and hs.get("has_hidden_spirit"):
        for det in hs.get("details", []):
            _mr = det.get("missing_relation", "")
            _em = det.get("can_emerge", "")
            _rs = det.get("reason", "")
            _status = "得出" if _em else "伏而不出"
            if _mr:
                detail_parts.append(f"伏藏：{_mr} {_status}（{_rs}）")
    # 绝处逢生
    dr = adv.get("desperate_relief") or {}
    if isinstance(dr, dict) and dr.get("has_desperate_relief"):
        _v = dr.get("verdict", "")
        _d = dr.get("description", "")
        if _d:
            detail_parts.append(f"绝处逢生：{_d}" + (f"——{_v}" if _v else ""))

    if detail_parts:
        chain.append("[格局详释] " + " | ".join(detail_parts))


def _get_hexagram_body_summary_note(r: dict) -> str:
    """
    从 advanced_analysis.hexagram_body 提取卦身摘要。
    返回描述卦身位置、六亲与当前占问关联含义的短句，若无法确定则返回空字符串。
    """
    advanced = r.get("advanced_analysis", {})
    if not isinstance(advanced, dict):
        return ""
    hb = advanced.get("hexagram_body", {})
    if not isinstance(hb, dict):
        return ""

    body_pos = hb.get("body_position")
    if body_pos is None:
        return ""

    # 将数字爻位转为名称
    pos_names = {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}
    pos_name = pos_names.get(body_pos, f"{body_pos}爻")

    body_relation = hb.get("body_relation", "")
    specific_notes = hb.get("specific_notes", [])

    # 八卦身含义（按占问类型）
    # 卦身临六亲在不同占问中有不同意义
    body_relation_meaning = {
        "妻财": {"marriage": "婚有缘本", "wealth": "求财有根", "default": "财爻为身"},
        "官鬼": {"marriage": "女缘在此", "career": "仕途有根", "illness": "病犹缠身", "default": "鬼爻为身"},
        "父母": {"exam": "文书有据", "marriage": "文书契证", "default": "父母为身"},
        "子孙": {"illness": "药石有功", "career": "卸官归闲", "marriage": "子息有缘", "default": "子孙为身"},
        "兄弟": {"marriage": "争竞者在", "wealth": "劫财有碍", "default": "兄弟为身"},
    }

    note = f"卦身在{pos_name}"
    if body_relation:
        note += f"（{body_relation}）"
        # 尝试按占问类型给出卦身的具体含义
        scenario = _detect_question_scenario(r.get("question", ""))
        _meaning_map = body_relation_meaning.get(body_relation, {})
        _meaning = _meaning_map.get(scenario, _meaning_map.get("default", ""))
        if _meaning:
            note += f"——占{_scenario_cn(scenario) if scenario else '此'}: {_meaning}"
        elif specific_notes:
            note += "——" + specific_notes[0]
    elif specific_notes:
        note += "——" + specific_notes[0]

    return note


def _scenario_cn(scenario: str) -> str:
    """英文 scenario key → 中文占问名称（用于卦身叙事）。"""
    return {
        "marriage": "婚姻",
        "wealth": "求财",
        "illness": "疾病",
        "career": "事业",
        "exam": "考试",
        "lawsuit": "诉讼",
        "travel": "出行",
        "parents_illness": "父母之疾",
    }.get(scenario, "")


def _build_overall_summary(context: dict) -> str:
    """构建最终整体摘要"""
    step1 = context.get("_step1_data", {})
    step2 = context.get("_step2_data", {})
    step3 = context.get("_step3_data", {})
    step4 = context.get("_step4_data", {})
    step5 = context.get("_step5_data", {})

    parts = [
        f"=== 六爻思维链分析结果 ===",
        f"【本卦】{step1.get('hexagram_name', '?')}（{step1.get('palace', '?')}，{step1.get('palace_element', '?')}）",
        f"【用神】{step2.get('use_god_category', '?')}（{step2.get('use_god_element', '?')}）",
        f"【旺衰】{step3.get('strength_level', '?')}（评分：{step3.get('effective_score', '?')}）",
        f"【动变】{step4.get('net_effect_description', '无动爻')}（效应：{step4.get('net_effect', 0):+.2f}）",
        f"【最终】{step5.get('verdict', '?')} — {step5.get('verdict_description', '')}",
        f"【置信度】{step5.get('confidence', '?')}%（{step5.get('confidence_description', '')}）",
        f"【应期】{step5.get('timing', {}).get('summary_text', '待断')}",
    ]

    # 添加卦身信息（如果有）
    body_note = step5.get("hexagram_body_note", "")
    if body_note:
        parts.append(f"【卦身】{body_note}")

    # 飞伏互断（如果有伏神）
    adv = context.get("advanced_analysis", {})
    if isinstance(adv, dict):
        fhi = adv.get("flying_hidden_interaction", {})
        if isinstance(fhi, dict) and fhi.get("has_interaction"):
            interaction_parts = []
            for inter in fhi.get("interactions", []):
                pos_name = _pos_to_name(inter.get("position", 0))
                interaction_parts.append(
                    f"  {pos_name}：飞{inter.get('fei_shen', '')}（{inter.get('fei_branch', '')}）→伏{inter.get('fu_shen', '')}（{inter.get('fu_branch', '')}）：{inter.get('relation', '')}"
                )
            emerge_overall = "伏得出" if fhi.get("overall_emerge") else "伏难出"
            parts.append(f"【飞伏互断】（总体：{emerge_overall}）")
            parts.extend(interaction_parts)

        tp = adv.get("transformation_pattern", {})
        if isinstance(tp, dict) and tp.get("patterns"):
            pattern_strs = []
            for p in tp["patterns"]:
                weight = tp.get("total_weight", 1.0)
                pattern_strs.append(p)
            parts.append(
                f"【变爻格局】{'、'.join(pattern_strs)}（综合权重：{tp.get('total_weight', 1.0):.1f}）"
            )
            if tp.get("interpretation"):
                parts.append(f"  断曰：{tp['interpretation']}")

    return "\n".join(parts)


def _clean_internal_keys(chain: dict) -> dict:
    """移除内部引用键，确保输出干净"""
    # 递归清理所有嵌套字典中的 _stepX_data 键
    cleaned = {}
    for key, value in chain.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict):
            cleaned[key] = {k: v for k, v in value.items() if not k.startswith("_")}
        else:
            cleaned[key] = value
    return cleaned

