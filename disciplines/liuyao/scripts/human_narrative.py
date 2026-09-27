# -*- coding: utf-8 -*-
"""解读正文生成 — 编排与导出层（human_narrative_segments 提供段落素材）。

铁律一合规：机械运算在主线引擎完成，本层只把结构化结论翻译成人话并装配成交付对象。
"""
from __future__ import annotations

from chain_verdicts import NARRATIVE_HINTS, PATTERN_RELATED  # noqa: E402
try:
    from advice_framework import generate_advice
except ImportError:
    from scripts.advice_framework import generate_advice
from human_narrative_segments import (  # noqa: E402
    _NARRATIVE_TPL,
    _pos_name,
    _question_focus,
    _strength_sentence,
    _verdict_opening,
    _change_sentence,
    _special_sentence,
    _timing_sentence,
    _meaning_paragraph,
    _bing_yao_paragraph,
    _shensha_paragraph,
)
_PATTERN_QUOTE_RELEVANCE = PATTERN_RELATED

def _pattern_advice_hint(pattern_tag: str, verdict: str, timing: dict) -> str:
    """根据当前卦象的 pattern 标签，返回一条场景化的附加建议。"""
    v = str(verdict or "")
    tag = str(pattern_tag or "").strip()
    if not tag:
        return ""

    # 截取日历首日期（用于具体提示）
    cal = ""
    dates_blob = (timing or {}).get("yingqi_dates") or {}
    if isinstance(dates_blob, dict):
        ds = dates_blob.get("dates") or []
        if ds:
            cal = str(ds[0].get("date", ""))

    # 场景表
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
            # 解析：[格局] 格局-六冲 | 六冲 | 六冲卦 | 变卦六冲
            try:
                body = s.split("]", 1)[1].strip()
                for token in body.split("|"):
                    t = token.strip()
                    if not t:
                        continue
                    # 去掉"格局-"前缀存入 set，与原标签同存
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
    # 从 step5.special_pattern 补充
    sp = (tc.get("step5_synthesis") or {}).get("special_pattern") or {}
    if isinstance(sp, dict) and sp.get("pattern"):
        tags.add(str(sp["pattern"]))
    return tags

def _select_relevant_quotes(tc: dict) -> list:
    """按 reasoning_chain 中卦象格局标签打分，选出最相关的 2 条引文。

    评分规则：
    - 引文 pattern 在 reasoning_chain 「格局-」标签中出现，+3（几乎精确命中）
    - 引文 pattern 在本 pattern 的 _PATTERN_QUOTE_RELEVANCE 展开集合里出现，+1（间接相关）
    - 完全不相关（如「兄弟持世」在兄持与世爻无关的卦象中），-5（排除）
    - 同样相关度保留数据库中的原始顺序（前入先出）
    """
    tags = _extract_pattern_tags(tc)
    if not tags:
        # 退化：直接按数据库顺序取前 2 条
        raw = (tc.get("step5_synthesis", {}) or {}).get("classical_quotes") or []
        return [{"source": q.get("source", "经典"), "quote": q.get("quote")} for q in raw[:2] if isinstance(q, dict) and q.get("quote")]

    raw_quotes = (tc.get("step5_synthesis", {}) or {}).get("classical_quotes") or []
    scored: list = []
    for idx, q in enumerate(raw_quotes):
        if not isinstance(q, dict) or not q.get("quote"):
            continue
        qp = str(q.get("pattern") or "")
        score = 0
        # 直接命中：引文 pattern 与某个 tag 完全一致
        if qp in tags:
            score += 3
        # 子串命中：某个 tag 字符串包含引文 pattern（如 tag 是"回头生、回头生、变出未"，qp="回头生"）
        # 排除自身已经被 exact 命中；这给出+1 兜底
        for real_tag in tags:
            if qp != real_tag and qp in real_tag and len(qp) >= 2:
                score += 1
                break
        # 间接命中：当前卦象的某个 tag，其推荐引用集合包含本引文 pattern
        # （查表方向：tag → 推荐引文集合；命中条件：本引文的 pattern 在推荐集合中）
        for real_tag in tags:
            related = _PATTERN_QUOTE_RELEVANCE.get(real_tag, [])
            if qp in related:
                score += 1
        # 反向间接命中：引文 pattern 作为 tag 展开时，包含当前某个 tag
        # （即"引文自己推荐的 tags"与当前卦象 tag 集合有重叠）
        forward_related = _PATTERN_QUOTE_RELEVANCE.get(qp, [])
        for fr in forward_related:
            if fr in tags:
                score += 1
        # 优先数据库顺序（排序稳定性用 idx 保底）
        scored.append((score, -idx, q))
    # 按 (score ASC因为用了-idx, 降序排列 = score DESC, idx ASC)
    scored.sort(key=lambda x: (-x[0], x[1]))
    # 过滤掉 score <= 0 的（避免引用与本卦无关的引文）
    filtered = [item for item in scored if item[0] > 0]
    # 全部退化情况
    top = filtered[:2] if filtered else scored[:2]
    return [{"source": q.get("source", "经典"), "quote": q.get("quote")} for _, _, q in top]

def _ensure_thinking_chain(result: dict) -> dict:
    """已停用——铁律一合规清理。

    此函数曾内置一套独立的五行旺衰打分、进退神判断与五步思维链重建逻辑，
    与主线 chain_step1–5 形成双路径。按 AGENTS.md §二"内核唯一真值源"的要求，
    同一套推演规则（当令旺衰、进退神、三合局等）只应由链式模块一处实现，
    不应在此就地重算来"兜底"。

    当 thinking_chain 不可用时，正确做法是修复上游 chain_step1–5 的生成流程，
    而不是调一套平行逻辑绕过它。故改为显式拒绝，防止意外触发。
    """
    raise RuntimeError(
        "thinking_chain 缺失，不应在交付路径外就地重建——"
        "请检查上游 analyze / run_thinking_chain 是否执行成功；"
        "铁律一（AGENTS.md §一）要求机械运算统一由主线引擎完成。"
    )

def _build_explain_summary(factor_contribs: list, focus: str) -> str:
    """将 factor_contributions 翻译成人话段落，而非字段罗列。

    输出格式例：
        「推因：用神旺衰给力（+1.9），动变效应拖累（-0.4），
         六神辅助略助（+0.1）。综合看是用神有力为主，变爻有些牵制，
         所以对于财运来说，根基是稳的但过程会有些波折。」
    """
    if not factor_contribs:
        return "各因子均衡，无明显偏向。"

    top = [fc for fc in factor_contribs[:6] if fc.get("score", 0) != 0]
    if not top:
        return "各因子均衡，无明显偏向。"

    # 按正负分组
    positive = [fc for fc in top if fc.get("score", 0) > 0]
    negative = [fc for fc in top if fc.get("score", 0) < 0]

    def _short_reason(reason: str, name: str) -> str:
        """把 factor_contributions 里的技术备注翻译成短句。
        原则：15 字以内、去掉内部评分、只留核心含义。
        """
        if not reason:
            return ""
        import re
        # 去掉括号中的数字评分、书名号内部备注等
        r = re.sub(r"[（(]\s*[+-]?\d+[\d.]*[%]?\s*[）)]", "", reason)
        r = re.sub(r"【[^】]*】", "", r)  # 去掉【...】内的内部标注
        r = r.replace(name, "")  # 去掉与name重复的词
        r = r.strip("，。：:, ")
        # 截断到第一个停止符或前15字
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
    # 确保 thinking_chain 数据可用（缺失时从引擎原始 JSON 推导）
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
    conf = s5.get("confidence")
    use_cat = s2.get("use_god_category") or "用神"
    use_el = s2.get("use_god_element") or ""
    use_br = (s2.get("selected_use_god") or {}).get("earthly_branch") or s3.get("use_god_branch") or ""
    use_pos = (s2.get("selected_use_god") or {}).get("position")
    strength = s3.get("strength_level") or ""
    timing = s5.get("timing") or {}
    special = s5.get("special_pattern") or {}
    special_pat = special.get("pattern") if isinstance(special, dict) else ""
    # factor_contributions —— 用于开头句精确引用关键因子
    factor_contribs = s5.get("factor_contributions") or []
    # yuan_status: 从 factor_contributions 判断原神实际状态
    yuan_greedy = any("贪合" in str(fc.get("factor", "")) for fc in factor_contribs)
    yuan_diagnosis = ""
    for fc in factor_contribs:
        n = str(fc.get("name", ""))
        r = str(fc.get("reason", ""))
        if "原神" in n or "原神" in r:
            yuan_diagnosis = r
            break
    # yuan_moving：原神是否发动 —— 看 yuan_shen positions 中有无 is_moving
    yuan_data = s2.get("yuan_shen", {}) or {}
    yuan_moving = any(
        (p or {}).get("is_moving") for p in (yuan_data.get("positions") or [])
    ) if isinstance(yuan_data, dict) else False
    # pattern_label：用于开头句精简引用
    pattern_label = ""
    if isinstance(special, dict) and special.get("pattern") is not None:
        pattern_label = str(special["pattern"])
    # 若 special_pattern 为空，从 reasoning_chain 格局标签取第一个做兜底
    if not pattern_label:
        fallback_tags = _extract_pattern_tags(tc)
        # 优先顺序：六冲六合 > 反吟伏吟 > 游魂归魂 > 回头生克 > 伏藏 > 持世 > 病疾
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

    # —— 正文：连续几段，读起来就是一份完整解读 ——
    title_bits = []
    if question:
        # 取问题里较短的关键词，避免整句古籍占辞当标题
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

    # 第1句：结论 + 最关键一条理由（避免「就?来说?」空句式）
    p1 = _verdict_opening(verdict, focus, pattern_label, yuan_diagnosis)
    scene = f"这副卦是{hex_desc}"
    if time_desc:
        scene += f"，起卦于{time_desc}"
    if empty_desc:
        scene += f"，{empty_desc}"
    p1 += scene + "。"

    # 第2句：旺衰 + 原神实际状态（静/贪合/发动），避免固定套话
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

    # 病药短段 + 星煞简短提及（消费 analyze 的 bing_yao / shensha_panel）
    p_bing = _bing_yao_paragraph(result)
    p_shen = _shensha_paragraph(result, use_pos=use_pos)

    body = [x for x in (p1, p2, p_bing, p_shen, p3, p4, p5) if x]
    lead = p1

    timing_plain = _timing_sentence(timing, special, s3, s5)

    # ── 建议：根据 verdict + pattern 标签定制 ──
    try:
        advice = generate_advice(verdict, question or focus, result)
    except Exception:
        advice = []
    if not advice:
        if "凶" in str(verdict) or "跌" in str(verdict):
            advice = list(NARRATIVE_HINTS["advice_xiong"])
        else:
            advice = list(NARRATIVE_HINTS["advice_ji"])
    # 根据当前卦象的 pattern 标签给建议补充一句具体场景化提示
    # 若有专属 pattern 提示，用它替换最后一条（一般是通用的时机建议），保留总数 4 条
    pattern_tag = pattern_label or ""
    extra_advice = _pattern_advice_hint(pattern_tag, verdict, timing)
    if extra_advice and len(advice) >= 2:
        advice = advice[:-1] + [extra_advice]
    elif extra_advice:
        advice = advice + [extra_advice]

    # ── 引文：按 reasoning_chain 中卦象格局标签相关性排序 ──
    quotes = _select_relevant_quotes(tc)

    caveat = (
        NARRATIVE_HINTS["disclaimer"]
    )
    # 置信度是内部指标，不在交付正文中暴露（AGENTS.md §三：对齐分≠预测率）。
    # "线索一致程度约 X%" 是置信度的换名表述，口径层面等同于把内部分数伪装成预测能力。
    conf_note = ""

    # —— 推因摘要（从 factor_contributions 翻译成人话）——
    factor_contribs = s5.get("factor_contributions") or []
    explain_summary = _build_explain_summary(factor_contribs, focus)

    # 附录用：推演过程（自然句，不是字段堆）
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
        "confidence": conf,
        # 正文
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
        # 兼容旧报告字段
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
        # 可解释性输出
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
        lines += ["", "古人类似情境也说过："]
        for q in narrative["classical_quotes"]:
            lines.append(f"- （{q['source']}）{q['quote']}")
    # 附录：推演过程（有则附，无则不硬凑）
    process = narrative.get("process") or []
    if process:
        lines += ["", "---", "", "## 推演过程（备查）", ""]
        for p in process:
            lines.append(f"**{p['label']}**：{p['text']}")
    lines += ["", "---", narrative.get("caveat") or ""]
    return "\n".join(lines)

build_reading = build_human_narrative
