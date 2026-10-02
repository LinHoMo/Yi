# -*- coding: utf-8 -*-
"""六爻叙述层：思维链格局标签 / 五步推演推理链 / 解读正文生成 / 段落素材。

铁律一合规：机械运算在主线引擎完成，本层只把结构化结论翻译成人话并装配成交付对象。
"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    CHONG_PAIRS,
    HE_PAIRS,
    KE_CYCLE,
    SHENG_CYCLE,
    hexagram_he_chong_kind,
)


import json

import re

from pathlib import Path

from narrative_utils import _pos_to_name
from narrative_utils import QUOTE_DATABASE, SHI_YAO_INTERPRETATION, SHI_YAO_POEMS, _QUESTION_SCENARIO_KEYWORDS
from narrative_utils import NARRATIVE_HINTS, PATTERN_RELATED
from narrative_rules import resolve_marriage_interpretation, select_timing_base
from chain_tables import HEXAGRAM_LIUCHONG, HEXAGRAM_LIUHE
from chain_tables import _BRANCH_CLASH_MAP, _HE_MAP  # noqa: E402

try:
    from advice_framework import generate_advice
except ImportError:
    from scripts.advice_framework import generate_advice

_NARRATIVE_TEMPLATES_PATH = Path(__file__).resolve().parents[1] / "data" / "narrative_templates.json"


def _load_narrative_templates() -> dict:
    try:
        return json.loads(_NARRATIVE_TEMPLATES_PATH.read_text(encoding="utf-8"))
    except OSError:
        return {}


_NARRATIVE_TPL = _load_narrative_templates()

_ADVICE_SOFT = _NARRATIVE_TPL.get("advice_soft") or {}

_PATTERN_QUOTE_RELEVANCE = PATTERN_RELATED


# ────────────────────────────────────────────────────────────────
# chain_narrate 部分：五步推演 / 应期 / 世应深化 / 格局匹配 / 推理链组装
# ────────────────────────────────────────────────────────────────

def _detect_question_scenario(question: str) -> str:
    """从求测问题中检测占问情境（返回 SHI_YAO_INTERPRETATION 中对应的 key）。"""
    if not question:
        return ""
    for scenario, keywords in _QUESTION_SCENARIO_KEYWORDS.items():
        for kw in keywords:
            if kw in question:
                return scenario
    return ""


def _infer_use_god_category_fallback(result: dict) -> str:
    """use_god_category 未显式传入时的回退：从 result 中已有的 step2 / advanced_analysis 取用神类别。"""
    tc = (result.get("thinking_chain", {}) or {}).get("step2_use_god_identification", {}) or {}
    cat = tc.get("use_god_category") or (tc.get("selected_use_god") or {}).get("category")
    if cat:
        return cat
    adv = result.get("advanced_analysis", {}) or {}
    return adv.get("use_god_category", "") or ""


def analyze_shi_yao_relation(result, use_god_category=None):
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

        question = result.get("question", "")
        scenario = _detect_question_scenario(question)
        # 婚姻情境按用神（问测者性别视角）分流：男问女→用神妻财，子孙为原神，持世有利；
        # 女问男→用神官鬼，子孙克官，持世不利。Bug3 根因：原先只有女占模板，男占姻缘被误判为不利。
        if scenario == "marriage":
            ug = use_god_category or _infer_use_god_category_fallback(result)
            scenario_interp = resolve_marriage_interpretation(interp, ug)
        else:
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
    if pattern_str == "月破":
        mb = advanced.get("monthly_break", {})
        if isinstance(mb, dict):
            return mb.get("has_monthly_break") or mb.get("has_break") or len(mb.get("break_positions") or []) > 0
        return False
    if pattern_str == "暗动":
        hm = advanced.get("hidden_movement", {})
        if isinstance(hm, dict):
            return hm.get("has_hidden_movement") or len(hm.get("hidden_moving_yao") or []) > 0
        return False
    if pattern_str == "绝处逢生":
        dr = advanced.get("desperate_relief", {})
        if isinstance(dr, dict):
            return dr.get("has_desperate_relief")
        s5 = result.get("thinking_chain", {}).get("step5_synthesis", {})
        if isinstance(s5, dict):
            return s5.get("desperate_relief_modifier", 0) > 0
        return False
    if pattern_str == "回头克":
        step4 = result.get("thinking_chain", {}).get("step4_change_analysis", {})
        details = step4.get("details", []) if isinstance(step4, dict) else []
        for d in details:
            if isinstance(d, dict) and d.get("change_type") == "回头克":
                return True
        return False
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

    body_positions = hb.get("body_positions") or []
    body_branch = hb.get("body_branch", "")
    body_relation = hb.get("body_relation", "")
    specific_notes = hb.get("specific_notes", [])

    # 卦身不现：古籍「无卦身则事无头绪」，specific_notes 首条（crt_098）已含卦身支
    if hb.get("body_not_present") or not body_positions:
        return specific_notes[0] if specific_notes else f"卦身{body_branch}不现于卦，事无定向"

    # 将数字爻位转为名称（卦身可一卦多现）
    pos_names = {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}
    pos_name = "、".join(pos_names.get(p, f"{p}爻") for p in body_positions)

    # 八卦身含义（按占问类型）
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
        f"【信号强度】{step5.get('signal_strength', step5.get('confidence', '?'))}（{step5.get('signal_strength_description', step5.get('confidence_description', ''))}）",
        f"【应期】{step5.get('timing', {}).get('summary_text', '待断')}",
    ]

    body_note = step5.get("hexagram_body_note", "")
    if body_note:
        parts.append(f"【卦身】{body_note}")

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
    cleaned = {}
    for key, value in chain.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict):
            cleaned[key] = {k: v for k, v in value.items() if not k.startswith("_")}
        else:
            cleaned[key] = value
    return cleaned


# ────────────────────────────────────────────────────────────────
# chain_narrate_patterns 部分：标准化格局标签注入
# ────────────────────────────────────────────────────────────────

def _collect_pattern_tags(context, step3: dict, step4: dict, step5: dict) -> list:
    """向推理链注入用的标准化格局标签（含经典别名，便于盲评与人话层共用）。"""
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
            if role == "原神" and ("生用" in effect or "生用" in detail):
                _add("格局-原神生用", "原神生用", "动则生而不为空", "动空")
            if role == "用神" and ("回头生" in ct or "生" in effect):
                _add("回头生")
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
            slevel = str(step3.get("strength_level") or "")
            if any(x in slevel for x in ("旺", "相", "中和")):
                _add("出旬有验", "出旬", "填实")
            # 真空 / 假空（《增删卜易》"旺空待出，真空难起"；判定在 compute_empty_modifier）
            _vk = str(step3.get("void_kind") or "")
            if _vk == "true":
                _add("格局-真空", "真空")
            elif _vk == "false":
                _add("格局-假空", "假空")
        if step3.get("is_month_break"):
            _add("格局-月破", "月破")
        # 暗动 / 冲空：读结构（`advanced_analysis.hidden_movement` 逐爻），不扫 summary 文本。
        # 旧实现按 summary_text 子串取词——「无暗动」也会命中「暗动」，属假阳来源。
        hm_ = adv.get("hidden_movement") or {}
        if isinstance(hm_, dict) and hm_.get("has_hidden_movement"):
            for d in hm_.get("details") or []:
                kind = str((d or {}).get("type") or "")
                if "暗动" in kind:
                    _add("格局-暗动", "暗动")
                if "冲空" in kind:
                    _add("冲空")

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
            # 双卦对比（《黄金策》"合处逢冲事已散，冲中逢合事迟成"）：本卦定始、变卦定终
            "事已散": ["格局-合处逢冲事已散", "合处逢冲", "变卦六冲"],
            "事迟成": ["格局-冲中逢合事迟成", "冲中逢合", "变卦六合"],
            # 三会方局（《三命通会》）：力大于三合，不得被当作三合破局
            "三会局": ["格局-三会局", "三会", "三会局"],
        }
        for key, names in mapping.items():
            if key in blob:
                _add(*names)
        if step5.get("officer_tomb_severity") == "catastrophic":
            _add("格局-随官入墓", "随官入墓")
        # 三传克制（《增删卜易》"三传俱克，虽旺亦危"）：**未验证项**，只标象不计分
        sc = step5.get("sanchuan") or {}
        if isinstance(sc, dict) and sc.get("fired"):
            _add("格局-三传克制", "三传克制")
        # 三合局 / 三刑 / 月破：读结构（`advanced_analysis` 各段），不扫 step5 文本。
        # 旧实现把 step5 全部标量拼成字符串子串取词，是「格局词子串匹配」的假阳来源。
        tc_ = adv.get("triple_combo") or {}
        if isinstance(tc_, dict) and tc_.get("has_triple_combo"):
            _add("三合", "合局")
        tp_ = adv.get("three_punishments") or {}
        if isinstance(tp_, dict) and tp_.get("has_punishment"):
            for p in tp_.get("punishments") or []:
                # 只认成刑（完整/成刑/催刑）；「待刑」缺月日补齐，不计结构命中（口径同 effects/step5）
                if str((p or {}).get("completeness") or "") not in ("完整", "成刑", "催刑"):
                    continue
                _add("三刑")
                pt = str((p or {}).get("type") or "")
                if "恃势" in pt:
                    _add("恃势")
                if "无恩" in pt:
                    _add("无恩")
        mb_ = adv.get("monthly_break") or {}
        if isinstance(mb_, dict) and mb_.get("has_monthly_break"):
            _add("格局-月破", "月破")

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
    # 卦级反吟/伏吟（《卜筮正宗》"内卦反吟内不安，外卦反吟外不宁"；
    # 判定在内核 hexagram_level_relations：六位全冲/全同 + 内外卦 flag）
    _hl = rep.get("hexagram_level") if isinstance(rep, dict) else None
    if isinstance(_hl, dict) and _hl.get("valid"):
        if _hl.get("full_clash") or _hl.get("inner_clash") or _hl.get("outer_clash"):
            _add("卦反吟")
        if _hl.get("full_same") or _hl.get("inner_same") or _hl.get("outer_same"):
            _add("卦伏吟")
        _scope = _hl.get("scope") or {}
        if _scope.get("inner_clash") or _scope.get("inner_same"):
            _add("内卦")
        if _scope.get("outer_clash") or _scope.get("outer_same"):
            _add("外卦")

    ch = adv.get("clash_harmony") or {}
    if isinstance(ch, dict):
        ht = str(ch.get("hexagram_type") or "")
        if "六合" in ht:
            _add("格局-六合", "六合", "六合卦")
        if "六冲" in ht:
            _add("格局-六冲", "六冲", "六冲卦")

    # 独发 / 独静（《增删卜易·独发章》：五爻俱动一爻不动为独静，五爻不动一爻独动为独发）
    df = adv.get("du_fa_du_jing") or {}
    if isinstance(df, dict) and df.get("type") in ("独发", "独静"):
        if df.get("type") == "独发":
            _add("格局-独发", "独发")
        else:
            _add("格局-独静", "独静")

    changed_name = ""
    if isinstance(context, dict):
        changed_name = ((context.get("changed_hexagram") or {}).get("name")) or ""
    if changed_name:
        # 变卦定终：卦体六合/六冲按对应位三对地支判（内核 hexagram_he_chong_kind），
        # 与排盘层 analyze_clash_harmony 同一口径，不用卦名白名单。
        _chg_kind = hexagram_he_chong_kind(changed_name)
        if _chg_kind == "六合卦":
            _add("变卦六合", "六合")
        elif _chg_kind == "六冲卦":
            _add("变卦六冲", "六冲")
    if changed_name in HEXAGRAM_LIUHE:
        _add("变卦六合", "六合")
    if changed_name in HEXAGRAM_LIUCHONG:
        _add("变卦六冲", "六冲")

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

    if any(k in question for k in ("失", "找回", "失银", "失物")):
        _add("六冲", "冲中逢合") if any("六冲" in t or "冲中逢合" in t for t in tags) else None
    if any(k in question for k in ("价", "贵贱", "桑叶", "贸易")):
        pass

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
        if mb and "临月" in str((step3 or {}).get("summary_text") or ""):
            _add("格局-用神临月建", "用神临月建", "临月建")
        s2ctx = context.get("thinking_chain") or {}
        step2c = s2ctx.get("step2_use_god_identification") or {}
        if (step2c.get("use_god_count") or 0) >= 2 or len(step2c.get("use_god_positions") or []) >= 2:
            _add("格局-用神多现", "用神多现", "两现", "多现")
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
            _add("迟归", "用神生世")
        if any(k in _q for k in ("失", "找回", "失物")) and any(t in ("世持财", "格局-世持财") or "世持财" in t for t in tags):
            _add("内卦")
    except Exception:
        pass

    return tags


def _collect_pattern_details(context) -> list:
    """收集 [格局详释] 一行的结构化细节（三刑/六冲六合/六神/十二长生/伏藏/绝处逢生）。"""
    adv = context.get("advanced_analysis") or {}
    if not isinstance(adv, dict):
        adv = {}
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
    # 独发 / 独静（《增删卜易·独发章》）：只作结构性提示
    df = adv.get("du_fa_du_jing") or {}
    if isinstance(df, dict) and df.get("driving_note"):
        detail_parts.append(f"{df.get('type')}：{df['driving_note']}")

    return detail_parts


def _inject_pattern_tags(chain: list, step3: dict, step4: dict, step5: dict, context: dict | None = None):
    """向推理链中注入标准化格局标签（含经典别名，便于盲评与人话层共用）"""
    context = context or {}
    tags = _collect_pattern_tags(context, step3, step4, step5)
    detail_parts = _collect_pattern_details(context)

    if tags:
        # 保留「格局-」前缀供机器，同时写入经典裸词供盲评字典命中
        chain.append("[格局] " + " | ".join(tags))
        bare = [t.replace("格局-", "") for t in tags]
        chain.append("[格局要点] " + "、".join(bare))

    # ---- [格局详释] 一行暴露高级格局细节，供模型写正文时引用 ----
    if detail_parts:
        chain.append("[格局详释] " + " | ".join(detail_parts))


# ────────────────────────────────────────────────────────────────
# human_narrative_segments 部分：正文段落素材生成
# ────────────────────────────────────────────────────────────────

def _pos_name(p) -> str:
    try:
        p = int(p)
    except Exception:
        return str(p or "")
    return {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}.get(p, f"{p}爻")


def _strength_sentence(level: str, use_cat: str, use_br: str, use_pos, yuan_moving: bool = False, yuan_greedy: bool = False) -> str:
    """把旺衰说成对这件事意味着什么——老师傅看盘的口吻，月破单列。"""
    loc = ""
    if use_br:
        loc = f"{use_br}"
        if use_pos:
            loc += _pos_name(use_pos)
        loc = f"（落在{loc}）"
    sp = _NARRATIVE_TPL.get("strength_phrases") or {}
    if "月破" in str(level):
        return (sp.get("month_break") or "").format(use_cat=use_cat, loc=loc)

    def _yuan_note() -> str:
        if yuan_greedy:
            return sp.get("yuan_greed_he") or ""
        if yuan_moving:
            return sp.get("yuan_moving") or ""
        return sp.get("yuan_static") or ""

    table = {
        "极旺": (sp.get("极旺") or "").format(use_cat=use_cat, loc=loc, yuan_note=_yuan_note()),
        "旺": (sp.get("旺") or "").format(use_cat=use_cat, loc=loc, yuan_note=_yuan_note()),
        "相": (sp.get("相") or "").format(use_cat=use_cat, loc=loc, yuan_note=_yuan_note()),
        "中和": (sp.get("中和") or "").format(use_cat=use_cat, loc=loc),
        "中和偏旺": (sp.get("中和偏旺") or "").format(use_cat=use_cat, loc=loc, yuan_note=_yuan_note()),
        "中和偏弱": (sp.get("中和偏弱") or "").format(use_cat=use_cat, loc=loc),
        "偏弱": (sp.get("偏弱") or "").format(use_cat=use_cat, loc=loc),
        "弱": (sp.get("弱") or "").format(use_cat=use_cat, loc=loc),
        "极弱": (sp.get("极弱") or "").format(use_cat=use_cat, loc=loc),
        "休囚": (sp.get("休囚") or "").format(use_cat=use_cat, loc=loc),
    }
    return table.get(str(level or ""), (sp.get("default") or "").format(use_cat=use_cat, loc=loc))


def _question_focus(question: str) -> str:
    q = question or ""
    rules = [
        (("病", "疾", "愈", "医"), "身体/病情"),
        (("婚", "姻", "嫁", "娶", "感情", "缘"), "婚姻感情"),
        (("失", "丢", "找回", "银", "物"), "失物寻回"),
        (("财", "求财", "生意", "投资", "价", "贵贱", "贸易", "银"), "财运求谋"),
        (("官", "讼", "诉", "师尊"), "官非词讼"),
        (("文书", "考试", "学业", "领"), "文书学业"),
        (("出行", "出外", "归", "回", "仆"), "行人出行"),
        (("子", "孩子", "子女"), "子女相关"),
        (("父", "母", "岳父", "长辈"), "长辈相关"),
    ]
    for kws, label in rules:
        if any(k in q for k in kws):
            return label
    return "所问之事"


def _verdict_opening(verdict: str, focus: str, pattern_label: str = "", yuan_diagnosis: str = "") -> str:
    """第一句：先接住问题、亮明结论，并直接给出最关键的一条理由。"""
    tpl = _NARRATIVE_TPL.get("verdict_openings") or {}
    reason_part = ""
    if yuan_diagnosis:
        reason_part = (tpl.get("reason_yuan") or "").format(yuan_diagnosis=yuan_diagnosis)
    elif pattern_label:
        reason_part = (tpl.get("reason_pattern") or "").format(pattern_label=pattern_label)

    pos_table = tpl.get("pos_table") or {}
    neg_table = tpl.get("neg_table") or {}
    wrap = tpl.get("wrap_pos") or "就{focus}来说，{text}。"

    v = str(verdict or "")
    if v in pos_table:
        return wrap.format(focus=focus, text=pos_table[v])
    if v in neg_table:
        raw = neg_table[v]
        if "{reason_part_or_default}" in raw:
            text = raw.format(
                focus=focus,
                reason_part=reason_part,
                reason_part_or_default=reason_part or (tpl.get("neg_default_reason") or ""),
            )
        elif "{reason_part}" in raw:
            text = raw.format(focus=focus, reason_part=reason_part)
        else:
            text = raw
        return wrap.format(focus=focus, text=text)
    if "凶" in v or "跌" in v:
        return (tpl.get("fallback_xiong") or "").format(focus=focus, v=v, reason_part=reason_part)
    if "吉" in v and "凶" not in v:
        return (tpl.get("fallback_ji") or "").format(focus=focus, v=v)
    return (tpl.get("fallback_neu") or "").format(focus=focus)


def _change_sentence(s4: dict, s2: dict) -> str:
    """动变：说清楚谁在动、对事情是帮还是扯后腿。"""
    tpl = _NARRATIVE_TPL.get("change_sentences") or {}
    details = (s4.get("details") or []) if s4 else []
    if not s4 or not s4.get("has_moving_lines") or not details:
        return tpl.get("no_moving") or ""

    details = s4.get("details") or []
    net = float(s4.get("net_effect") or 0)
    use_cat = s2.get("use_god_category") or "用神"

    def _fmt(key: str, **kw) -> str:
        return (tpl.get(key) or "").format(**kw)

    bits = []
    for d in details:
        if not isinstance(d, dict):
            continue
        pos = _pos_name(d.get("position"))
        rel = d.get("original_relation") or ""
        role = d.get("line_role") or ""
        ct = d.get("change_type") or ""
        chg = d.get("changed_branch") or ""
        if role == "用神":
            if "回头生" in ct:
                bits.append(_fmt("use_huisheng", pos=pos, rel=rel, chg=chg))
            elif "回头克" in ct:
                bits.append(_fmt("use_huike", pos=pos, rel=rel))
            elif "反吟" in ct:
                bits.append(_fmt("use_fanyin", pos=pos, rel=rel))
            else:
                bits.append(_fmt("use_moving", pos=pos, rel=rel))
        elif role == "原神":
            if "回头生" in ct or "化合" in ct:
                bits.append(_fmt("yuan_help", pos=pos, rel=rel, use_cat=use_cat))
            else:
                bits.append(_fmt("yuan_support", pos=pos, rel=rel, use_cat=use_cat))
        elif role == "忌神":
            if "回头克" in ct:
                bits.append(_fmt("taboo_self_hurt", pos=pos, rel=rel))
            elif "贪合" in str(d.get("effect_on_usegod") or "") or "合" in ct:
                bits.append(_fmt("taboo_bound", pos=pos, rel=rel))
            else:
                bits.append(_fmt("taboo_block", pos=pos, rel=rel))
        elif role == "仇神":
            bits.append(_fmt("foe", pos=pos, rel=rel))
        else:
            bits.append(_fmt("other", pos=pos, rel=(rel or "他爻")))

    if not bits:
        bits.append(tpl.get("bits_empty") or "")

    if net > 1.0:
        tail = tpl.get("tail_pos") or ""
    elif net < -1.0:
        tail = tpl.get("tail_neg") or ""
    else:
        tail = tpl.get("tail_neu") or ""
    return "；".join(bits) + "。" + tail


def _special_sentence(special, s3, s2, question: str) -> str:
    if not isinstance(special, dict):
        return ""
    tpl = _NARRATIVE_TPL.get("special_sentences") or {}
    pat = str(special.get("pattern") or "")
    desc = str(special.get("description") or "")
    focus = _question_focus(question)
    empty = bool(s3.get("is_empty")) if s3 else False
    strength = str((s3 or {}).get("strength_level") or "")

    def _g(key: str, **kw) -> str:
        return (tpl.get(key) or "").format(**kw)

    if "近病逢空" in pat or "近病逢空" in desc:
        return (_NARRATIVE_TPL.get("strength_phrases") or {}).get("near_illness_void") or ""
    if "近病逢合" in pat:
        return (_NARRATIVE_TPL.get("change_sentences") or {}).get("near_he") or ""
    if "合处逢冲" in pat:
        if "婚" in focus or "婚姻" in focus:
            return _g("he_then_scatter_marriage")
        return _g("he_then_scatter", focus=focus)
    if "冲中逢合" in pat:
        return _g("chong_then_he")
    if "反吟" in pat:
        return _g("fan_yin")
    if "六冲" in pat:
        return _g("liu_chong", focus=focus)
    if "六合" in pat:
        return _g("liu_he", focus=focus)
    if "伏吟" in pat:
        return _g("fu_yin", focus=focus)
    if "游魂" in pat:
        return _g("you_hun", focus=focus)
    if "归魂" in pat:
        return _g("gui_hun", focus=focus)
    if "归禄" in pat or "禄" in pat:
        return _g("lu", focus=focus)
    if pat:
        return _g("other_pattern_desc", pat=pat, desc=desc) if desc else _g("other_pattern", pat=pat)
    if empty and any(x in strength for x in ("旺", "相", "中和")):
        return _g("void_but_rooted")
    return ""


def _timing_sentence(timing: dict, special, s3, s5: dict = None) -> str:
    """应期段：优先从 yingqi_dates 读日历日期，无则回退到地支描述。"""
    dates_blob = (s5 or {}).get("yingqi_dates") or {}
    calendar_dates = (dates_blob.get("dates") or []) if isinstance(dates_blob, dict) else []
    calendar_str = ""
    if calendar_dates:
        shown = []
        for d in calendar_dates[:3]:
            shown.append(f"{d.get('date','')}({d.get('description','')})")
        calendar_str = "、".join(shown)
    clashing = _BRANCH_CLASH_MAP
    combining = {b: (ps[0] if ps else "") for b, ps in _HE_MAP.items()}
    t = timing if isinstance(timing, dict) else {}
    keys = list(t.get("key_branches") or [])
    speed = str(t.get("speed") or "")
    use_br = str((s3 or {}).get("use_god_branch") or "")
    sp = ""
    if isinstance(special, dict):
        sp = str(special.get("pattern") or "") + str(special.get("description") or "")

    day_hint = ""
    if use_br:
        cl = clashing.get(use_br, "")
        co = combining.get(use_br, "")
        if "伏" in str(s3.get("is_fu", "") or ""):
            day_hint = NARRATIVE_HINTS["day_hint_fu_out"]
        elif cl and co:
            day_hint = NARRATIVE_HINTS["day_hint_value_or_clash_he"].format(use_br=use_br, cl=cl, co=co)
        elif cl:
            day_hint = NARRATIVE_HINTS["day_hint_value_or_clash"].format(use_br=use_br, cl=cl)
        else:
            day_hint = NARRATIVE_HINTS["day_hint_value"].format(use_br=use_br)

    base = select_timing_base(sp, speed, str((t or {}).get("summary_text") or ""), calendar_str)

    if "合处逢冲" in sp or "冲中逢合" in sp or "反吟" in sp:
        base += NARRATIVE_HINTS["timing_repeat"]

    if day_hint:
        base += NARRATIVE_HINTS["timing_day_detail"].format(day_hint=day_hint)
    elif keys:
        shown = "、".join(keys[:3])
        base += NARRATIVE_HINTS["timing_shown"].format(shown=shown)
    if calendar_str:
        base += NARRATIVE_HINTS["timing_calendar"].format(calendar_str=calendar_str)
    return base


def _meaning_paragraph(verdict, s2, s3, special, question, factor_contribs=None) -> str:
    """第五段：综合定性 + 精简引用关键因子。"""
    use_cat = s2.get("use_god_category") or "用神"
    yuan = (s2.get("yuan_shen") or {}).get("category") or ""
    ji = (s2.get("ji_shen") or {}).get("category") or ""
    strength = str(s3.get("strength_level") or "") if s3 else ""
    focus = _question_focus(question)

    vdir = 1 if ("吉" in str(verdict) and "凶" not in str(verdict) and "不利" not in str(verdict)) else (
        -1 if ("凶" in str(verdict) or "跌" in str(verdict) or "不利" in str(verdict)) else 0
    )

    parts = []
    if vdir > 0:
        parts.append(_ADVICE_SOFT.get("push") or "")
    elif vdir < 0:
        parts.append(_ADVICE_SOFT.get("hold") or "")
    else:
        parts.append(_ADVICE_SOFT.get("wait") or "")

    if factor_contribs:
        def _factor_polarity(fc):
            p = fc.get("polarity")
            if p is None:
                s = fc.get("score") or 0
                p = 1 if s > 0 else (-1 if s < 0 else 0)
            return p

        def _sort_key(fc):
            explicit = 0 if fc.get("polarity") is not None else 1
            mag = abs(fc.get("score") or 0)
            return (explicit, -mag)
        pos_items = sorted(
            [fc for fc in factor_contribs if _factor_polarity(fc) > 0], key=_sort_key
        )[:2]
        neg_items = sorted(
            [fc for fc in factor_contribs if _factor_polarity(fc) < 0], key=_sort_key
        )[:2]
        if pos_items:
            pos_strs = []
            for fc in pos_items:
                nm = fc.get("name", "")
                reason = _clean_reason(fc.get("reason", ""), nm)
                pos_strs.append(f"{nm}" + (f"（{reason}）" if reason else ""))
            parts.append("有利面：" + "；".join(pos_strs) + "。")
        if neg_items:
            neg_strs = []
            for fc in neg_items:
                nm = fc.get("name", "")
                reason = _clean_reason(fc.get("reason", ""), nm)
                neg_strs.append(f"{nm}" + (f"（{reason}）" if reason else ""))
            parts.append("拖累面：" + "；".join(neg_strs) + "。")

    if any(x in strength for x in ("弱", "囚", "死")) and vdir > 0:
        parts.append((_ADVICE_SOFT.get("weak_but_pattern") or "") + "'绝处逢生'之象，成可成，心力要花够。")
    if any(x in strength for x in ("弱", "囚", "死")) and vdir <= 0:
        parts.append((_ADVICE_SOFT.get("weak_and_bad") or "") + "'克多出暴'" + (_ADVICE_SOFT.get("weak_and_bad_tail") or ""))
    if "冲中逢合" in str(special or ""):
        parts.append(_ADVICE_SOFT.get("chong_then_he") or "")
    if "回头克" in str(special or ""):
        parts.append("回头克为'自伤'" + (_ADVICE_SOFT.get("internal_block") or ""))

    return "".join(parts)


def _clean_reason(reason: str, name: str) -> str:
    """去掉 factor_contribution.reason 里的技术备注，只留 15 字内的人类可读短句。"""
    if not reason:
        return ""
    r = re.sub(r"[（(]\s*[+-]?\d+[\d.]*[%]?\s*[）)]", "", reason)
    r = re.sub(r"【[^】]*】", "", r)
    r = r.replace(name, "")
    r = r.strip("，。：:, ")
    r = re.split(r"[，。；,;]", r, maxsplit=1)[0]
    if len(r) > 15:
        r = r[:15]
    return r.strip() or ""


def _resolve_bing_yao_shensha(result: dict) -> tuple[dict, dict]:
    """取 analyze 已有 bing_yao / shensha_panel；缺失时从思维链机械补算。"""
    concl = result.get("conclusion") or {}
    bing = result.get("bing_yao") or {}
    if not bing and isinstance(concl.get("病药"), dict):
        bing = concl["病药"]
    shen = result.get("shensha_panel") or {}
    if not shen and isinstance(concl.get("星煞"), dict):
        shen = concl["星煞"]
    if bing and shen:
        return bing, shen

    tc = result.get("thinking_chain") or {}
    s2 = tc.get("step2_use_god_identification") or {}
    s3 = tc.get("step3_strength_analysis") or {}
    if not s3:
        for v in tc.values():
            if isinstance(v, dict) and "strength_level" in v:
                s3 = v
                break
    try:
        from bing_yao_shensha import attach_shensha, evaluate_bing_yao
        if not bing and (s2 or s3):
            bing = evaluate_bing_yao(s2, s3, tc.get("step5_synthesis") or {})
        if not shen and result.get("divination_time"):
            shen = attach_shensha(result, s3)
    except Exception:
        pass
    return bing or {}, shen or {}


def _line_on_pos(line_name, use_pos) -> bool:
    """爻名（初六/九三/上九…）是否落在用神爻位。"""
    try:
        p = int(use_pos)
    except Exception:
        return False
    mark = {1: "初", 2: "二", 3: "三", 4: "四", 5: "五", 6: "上"}.get(p)
    return bool(mark) and mark in str(line_name or "")


def _line_plain(line_name, tpl: dict) -> str:
    s = str(line_name or "")
    words = (tpl.get("line_words") or {})
    for key, word in words.items():
        if key in s:
            return word
    return s


def _bing_yao_paragraph(result: dict) -> str:
    """病药短段：列出病与药，口吻偏向/有…信号/结构上（口径诚实）。"""
    tpl = _NARRATIVE_TPL.get("bing_yao") or {}
    if not tpl:
        return ""
    bing, _ = _resolve_bing_yao_shensha(result)
    illness = (bing or {}).get("illness") or []
    medicine = (bing or {}).get("medicine") or []
    if not illness and not medicine:
        return ""

    ill_phrases = tpl.get("illness_phrases") or {}
    med_phrases = tpl.get("medicine_phrases") or {}
    joiner = tpl.get("item_joiner") or "；"
    ills = [ill_phrases.get(x.get("code")) or x.get("label") or ""
            for x in illness if isinstance(x, dict)]
    meds = [med_phrases.get(x.get("code")) or x.get("label") or ""
            for x in medicine if isinstance(x, dict)]
    ills = [x for x in ills if x]
    meds = [x for x in meds if x]
    if not ills and not meds:
        return ""

    intro = tpl.get("intro") or ""
    tail = tpl.get("tail") or ""
    if ills and meds:
        core = (
            f"{intro}"
            f"{tpl.get('illness_lead') or '病'}有——{joiner.join(ills)}"
            f"{tpl.get('pair_joiner') or '；药偏向：'}{joiner.join(meds)}"
        )
    elif ills:
        core = f"{intro}{tpl.get('only_illness_lead') or '病有——'}{joiner.join(ills)}"
    else:
        core = f"{intro}{tpl.get('only_medicine_lead') or '药偏向——'}{joiner.join(meds)}"
    return f"{core}。{tail}".strip()


def _shensha_paragraph(result: dict, use_pos=None) -> str:
    """星煞短提及：仅临爻/临日，不吉凶夸张；无命中不硬造段。"""
    tpl = _NARRATIVE_TPL.get("shensha") or {}
    if not tpl:
        return ""
    _, shen = _resolve_bing_yao_shensha(result)
    stars = (shen or {}).get("shensha") or []
    if not stars:
        return ""

    max_items = int(tpl.get("max_items") or 3)
    joiner = tpl.get("joiner") or "；"
    seen: set[str] = set()
    mentions: list[str] = []

    def _push(text: str, key: str) -> None:
        if text and key not in seen and len(mentions) < max_items:
            mentions.append(text)
            seen.add(key)

    for s in stars:
        if not isinstance(s, dict):
            continue
        name = str(s.get("name") or "")
        if not name:
            continue
        on_lines = s.get("on_lines") or []
        if any(_line_on_pos(ln, use_pos) for ln in on_lines):
            _push((tpl.get("on_use_god") or "{name}临用爻").format(name=name), name)
    for s in stars:
        if not isinstance(s, dict):
            continue
        name = str(s.get("name") or "")
        if not name or name in seen:
            continue
        on_lines = [ln for ln in (s.get("on_lines") or []) if not _line_on_pos(ln, use_pos)]
        if on_lines:
            line = _line_plain(on_lines[0], tpl)
            _push((tpl.get("on_line") or "{name}临{line}").format(name=name, line=line), name)
    for s in stars:
        if not isinstance(s, dict):
            continue
        name = str(s.get("name") or "")
        if not name or name in seen:
            continue
        if s.get("on_day"):
            _push((tpl.get("on_day") or "{name}临日").format(name=name), name)

    if not mentions:
        return ""
    lead = tpl.get("lead") or ""
    tail = tpl.get("tail") or ""
    core = f"{lead}{joiner.join(mentions)}"
    return f"{core}。{tail}".strip() if tail else f"{core}。"


# ────────────────────────────────────────────────────────────────
# human_narrative 部分：解读正文编排与导出
# ────────────────────────────────────────────────────────────────

def _pattern_advice_hint(pattern_tag: str, verdict: str, timing: dict) -> str:
    """根据当前卦象的 pattern 标签，返回一条场景化的附加建议。"""
    v = str(verdict or "")
    tag = str(pattern_tag or "").strip()
    if not tag:
        return ""

    cal = ""
    dates_blob = (timing or {}).get("yingqi_dates") or {}
    if isinstance(dates_blob, dict):
        ds = dates_blob.get("dates") or []
        if ds:
            cal = str(ds[0].get("date", ""))

    HINTS = _NARRATIVE_TPL.get("pattern_hints") or {}
    text = HINTS.get(tag, "")
    if not text:
        return ""
    if tag == "原神绝位·用神失源" and cal:
        text = text + (HINTS.get("原神绝位·补转机") or "").format(cal=cal)
    if tag == "兄弟持世":
        text = text + ((HINTS.get("兄弟持世·补") or "").format(cal=cal) if cal else (HINTS.get("兄弟持世·补_default") or ""))
    return text


def _extract_pattern_tags(tc: dict) -> set:
    """从 reasoning_chain 提取标准化格局标签集合（含所有「格局-」前缀 tag）。"""
    tags: set = set()
    chain = tc.get("reasoning_chain") or []
    for entry in chain:
        s = str(entry)
        if "[格局]" in s:
            try:
                body = s.split("]", 1)[1].strip()
                for token in body.split("|"):
                    t = token.strip()
                    if not t:
                        continue
                    tags.add(t)
                    if t.startswith("格局-"):
                        tags.add(t[3:])
                    else:
                        tags.add("格局-" + t)
            except Exception:
                continue
        elif "[格局要点]" in s:
            try:
                body = s.split("]", 1)[1].strip()
                for token in body.split("|"):
                    t = token.strip()
                    if t:
                        tags.add(t)
            except Exception:
                continue
    sp = (tc.get("step5_synthesis") or {}).get("special_pattern") or {}
    if isinstance(sp, dict) and sp.get("pattern"):
        tags.add(str(sp["pattern"]))
    return tags


def _select_relevant_quotes(tc: dict) -> list:
    """按 reasoning_chain 中卦象格局标签打分，选出最相关的 2 条引文。"""
    tags = _extract_pattern_tags(tc)
    if not tags:
        raw = (tc.get("step5_synthesis", {}) or {}).get("classical_quotes") or []
        return [{"source": q.get("source", "经典"), "quote": q.get("quote")} for q in raw[:2] if isinstance(q, dict) and q.get("quote")]

    raw_quotes = (tc.get("step5_synthesis", {}) or {}).get("classical_quotes") or []
    scored: list = []
    for idx, q in enumerate(raw_quotes):
        if not isinstance(q, dict) or not q.get("quote"):
            continue
        qp = str(q.get("pattern") or "")
        score = 0
        if qp in tags:
            score += 3
        for real_tag in tags:
            if qp != real_tag and qp in real_tag and len(qp) >= 2:
                score += 1
                break
        for real_tag in tags:
            related = _PATTERN_QUOTE_RELEVANCE.get(real_tag, [])
            if qp in related:
                score += 1
        forward_related = _PATTERN_QUOTE_RELEVANCE.get(qp, [])
        for fr in forward_related:
            if fr in tags:
                score += 1
        scored.append((score, -idx, q))
    scored.sort(key=lambda x: (-x[0], x[1]))
    filtered = [item for item in scored if item[0] > 0]
    top = filtered[:2] if filtered else scored[:2]
    return [{"source": q.get("source", "经典"), "quote": q.get("quote")} for _, _, q in top]


def _ensure_thinking_chain(result: dict) -> dict:
    """已停用——铁律一合规清理。"""
    raise RuntimeError(
        "thinking_chain 缺失，不应在交付路径外就地重建——"
        "请检查上游 analyze / run_thinking_chain 是否执行成功；"
        "铁律一（AGENTS.md §一）要求机械运算统一由主线引擎完成。"
    )


def _build_explain_summary(factor_contribs: list, focus: str) -> str:
    """将 factor_contributions 翻译成人话段落，而非字段罗列。"""
    if not factor_contribs:
        return "各因子均衡，无明显偏向。"

    top = [fc for fc in factor_contribs[:6] if fc.get("score", 0) != 0]
    if not top:
        return "各因子均衡，无明显偏向。"

    positive = [fc for fc in top if fc.get("score", 0) > 0]
    negative = [fc for fc in top if fc.get("score", 0) < 0]

    def _short_reason(reason: str, name: str) -> str:
        if not reason:
            return ""
        r = re.sub(r"[（(]\s*[+-]?\d+[\d.]*[%]?\s*[）)]", "", reason)
        r = re.sub(r"【[^】]*】", "", r)
        r = r.replace(name, "")
        r = r.strip("，。：:, ")
        r = re.split(r"[，。；,;]", r, maxsplit=1)[0]
        if len(r) > 15:
            r = r[:15]
        r = r.strip()
        if not r or len(r) <= 1:
            return ""
        return r

    pos_parts = []
    for fc in positive[:3]:
        name = fc.get("name", "")
        reason = _short_reason(fc.get("reason", ""), name)
        tail = f"（{reason}）" if reason else ""
        pos_parts.append(f"{name}{tail}")

    neg_parts = []
    for fc in negative[:3]:
        name = fc.get("name", "")
        reason = _short_reason(fc.get("reason", ""), name)
        tail = f"（{reason}）" if reason else ""
        neg_parts.append(f"{name}{tail}")

    if pos_parts and neg_parts:
        body_text = "；".join(pos_parts) + "；拖累面：" + "；".join(neg_parts)
        summary = f"{focus}吉凶相杂，宜稳扎稳打。"
        header = "推因 —— 利好面"
    elif pos_parts:
        body_text = "；".join(pos_parts)
        summary = f"{focus}有明确助力，可顺势而为。"
        header = "推因 —— 利好面"
    else:
        body_text = "；".join(neg_parts)
        summary = f"{focus}阻力不小，宜谨慎守待时机。"
        header = "推因 —— 拖累面"

    return f"{header}：{body_text}。{summary}"


def build_human_narrative(result: dict) -> dict:
    """
    生成完整解读正文（唯一交付口吻）。
    兼容旧字段名，便于报告/门户复用。
    """
    if not result.get("thinking_chain"):
        result = dict(result)  # 浅拷贝避免污染原始数据
        result["thinking_chain"] = _ensure_thinking_chain(result)

    tc = result.get("thinking_chain") or {}
    s1 = tc.get("step1_situational_reading") or {}
    s2 = tc.get("step2_use_god_identification") or {}
    s3 = tc.get("step3_strength_analysis") or {}
    s4 = tc.get("step4_change_analysis") or {}
    s5 = tc.get("step5_synthesis") or {}

    question = result.get("question") or ""
    hex_name = (result.get("original_hexagram") or {}).get("name") or s1.get("hexagram_name") or ""
    changed_name = ((result.get("changed_hexagram") or {}).get("name")) or ""
    palace = (result.get("original_hexagram") or {}).get("palace") or s1.get("palace") or ""
    generation = (result.get("original_hexagram") or {}).get("generation") or ""
    dt = result.get("divination_time") or {}
    empty = result.get("empty_branches") or []

    verdict = s5.get("verdict") or "未知"
    score = s5.get("final_score")
    conf = s5.get("signal_strength", s5.get("confidence"))
    use_cat = s2.get("use_god_category") or "用神"
    use_el = s2.get("use_god_element") or ""
    use_br = (s2.get("selected_use_god") or {}).get("earthly_branch") or s3.get("use_god_branch") or ""
    use_pos = (s2.get("selected_use_god") or {}).get("position")
    strength = s3.get("strength_level") or ""
    timing = s5.get("timing") or {}
    special = s5.get("special_pattern") or {}
    special_pat = special.get("pattern") if isinstance(special, dict) else ""
    factor_contribs = s5.get("factor_contributions") or []
    yuan_greedy = any("贪合" in str(fc.get("factor", "")) for fc in factor_contribs)
    yuan_diagnosis = ""
    for fc in factor_contribs:
        n = str(fc.get("name", ""))
        r = str(fc.get("reason", ""))
        if "原神" in n or "原神" in r:
            yuan_diagnosis = r
            break
    yuan_data = s2.get("yuan_shen", {}) or {}
    yuan_moving = any(
        (p or {}).get("is_moving") for p in (yuan_data.get("positions") or [])
    ) if isinstance(yuan_data, dict) else False
    pattern_label = ""
    if isinstance(special, dict) and special.get("pattern") is not None:
        pattern_label = str(special["pattern"])
    if not pattern_label:
        fallback_tags = _extract_pattern_tags(tc)
        _priority = ["久病逢空", "久病逢冲", "近病逢空", "近病逢合",
                     "六冲卦", "六合卦", "反吟", "伏吟", "游魂", "归魂",
                     "回头生", "回头克", "化格", "三合成局", "绝处逢生",
                     "伏神得出", "伏神不得出", "暗动", "官鬼持世",
                     "兄弟持世", "子孙持世", "父母持世", "妻财持世",
                     "原神绝位·用神失源", "月破"]
        for p in _priority:
            if p in fallback_tags:
                pattern_label = p
                break

    focus = _question_focus(question)

    title_bits = []
    if question:
        title_bits.append(focus)
    if hex_name:
        title_bits.append(hex_name + ("之" + changed_name if changed_name else "卦"))
    title = " · ".join(title_bits) if title_bits else "六爻解读"

    hex_desc = f"{hex_name}"
    if palace or generation:
        hex_desc += f"（{palace}宫{('·' + generation) if generation else ''}）"
    if changed_name:
        hex_desc += f"，变卦{changed_name}"
    time_desc = ""
    if dt:
        time_desc = f"{dt.get('month_stem_branch','')}月 {dt.get('day_stem_branch','')}日".strip()
    empty_desc = f"旬空{('、'.join(empty))}" if empty else ""

    p1 = _verdict_opening(verdict, focus, pattern_label, yuan_diagnosis)
    scene = f"这副卦是{hex_desc}"
    if time_desc:
        scene += f"，起卦于{time_desc}"
    if empty_desc:
        scene += f"，{empty_desc}"
    p1 += scene + "。"

    p2 = (
        f"事情的关键看{use_cat}"
        + (f"（五行属{use_el}）" if use_el else "")
        + (f"，落在{use_br}{_pos_name(use_pos)}" if use_br else "")
        + "。"
        + _strength_sentence(strength, use_cat, use_br, use_pos,
                             yuan_moving=yuan_moving, yuan_greedy=yuan_greedy)
    )

    p3 = _change_sentence(s4, s2)
    p4 = _special_sentence(special, s3, s2, question)
    p5 = _meaning_paragraph(verdict, s2, s3, special, question, factor_contribs)

    p_bing = _bing_yao_paragraph(result)
    p_shen = _shensha_paragraph(result, use_pos=use_pos)

    body = [x for x in (p1, p2, p_bing, p_shen, p3, p4, p5) if x]
    lead = p1

    timing_plain = _timing_sentence(timing, special, s3, s5)

    try:
        advice = generate_advice(verdict, question or focus, result)
    except Exception:
        advice = []
    if not advice:
        if "凶" in str(verdict) or "跌" in str(verdict):
            advice = list(NARRATIVE_HINTS["advice_xiong"])
        else:
            advice = list(NARRATIVE_HINTS["advice_ji"])
    pattern_tag = pattern_label or ""
    extra_advice = _pattern_advice_hint(pattern_tag, verdict, timing)
    if extra_advice and len(advice) >= 2:
        advice = advice[:-1] + [extra_advice]
    elif extra_advice:
        advice = advice + [extra_advice]

    quotes = _select_relevant_quotes(tc)

    caveat = (
        NARRATIVE_HINTS["disclaimer"]
    )
    conf_note = ""

    factor_contribs = s5.get("factor_contributions") or []
    explain_summary = _build_explain_summary(factor_contribs, focus)

    process = []
    for label, text in (
        ("观局", s1.get("summary_text") or ""),
        ("定用", s2.get("summary_text") or ""),
        ("断旺", s3.get("summary_text") or ""),
        ("察变", s4.get("summary_text") or ""),
        ("综合", s5.get("summary_text") or ""),
    ):
        if text:
            process.append({"label": label, "text": str(text)})

    return {
        "title": title,
        "question": question,
        "hexagram": hex_name,
        "changed_hexagram": changed_name,
        "verdict": verdict,
        "final_score": score,
        "signal_strength": conf,
        "confidence": conf,
        "headline": p1 if len(p1) < 80 else _verdict_opening(verdict, focus),
        "lead": lead,
        "body": body,
        "reading": "\n\n".join(body),
        "timing_plain": timing_plain,
        "advice": list(advice)[:4],
        "caveat": caveat,
        "confidence_note": conf_note,
        "classical_quotes": quotes,
        "process": process,
        "plain_summary": body[0] if body else "",
        "what_it_means": p5,
        "use_god": {
            "category": use_cat,
            "element": use_el,
            "branch": use_br,
            "position": use_pos,
            "strength": strength,
            "strength_plain": _strength_sentence(strength, use_cat, use_br, use_pos),
        },
        "special_pattern": special_pat or "",
        "reasoning_chain": tc.get("reasoning_chain") or [],
        "summary_text": tc.get("summary_text") or "",
        "factor_contributions": factor_contribs,
        "explain_summary": explain_summary,
    }


def render_human_markdown(narrative: dict) -> str:
    """导出为一篇完整解读，而不是「人话章节 + 附录」两张皮。"""
    if not narrative:
        return ""
    lines = [f"# {narrative.get('title') or narrative.get('headline') or '六爻解读'}", ""]
    if narrative.get("question"):
        lines += [f"问：{narrative['question']}", ""]
    for para in narrative.get("body") or []:
        lines += [para, ""]
    lines += [f"**时间上**：{narrative.get('timing_plain') or ''}", ""]
    lines += ["**可以这样做**："]
    for i, a in enumerate(narrative.get("advice") or [], 1):
        lines.append(f"{i}. {a}")
    if narrative.get("confidence_note"):
        lines += ["", narrative["confidence_note"]]
    if narrative.get("classical_quotes"):
        # 引导句外置 narrative_templates.json#narrate_shell.quote_lead（此前与 narrate.py
        # 各内联一份字面量，语料审计判该键零消费——两处合一后单一出处）
        lines += ["", _NARRATIVE_TPL.get("narrate_shell", {}).get("quote_lead", "古人类似情境也说过：")]
        for q in narrative["classical_quotes"]:
            lines.append(f"- （{q['source']}）{q['quote']}")
    process = narrative.get("process") or []
    if process:
        lines += ["", "---", "", "## 推演过程（备查）", ""]
        for p in process:
            lines.append(f"**{p['label']}**：{p['text']}")
    lines += ["", "---", narrative.get("caveat") or ""]
    return "\n".join(lines)


build_reading = build_human_narrative
