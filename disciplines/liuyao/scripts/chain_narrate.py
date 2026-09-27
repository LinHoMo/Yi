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
    EARTHLY_BRANCHES,
    EIGHT_PALACES,
    HEAVENLY_STEMS,
    HEXAGRAM_TRIGRAMS,
    NAJIA_BRANCHES,
    RETREAT_PAIRS,
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
from chain_narrate_patterns import _inject_pattern_tags  # noqa: E402

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

