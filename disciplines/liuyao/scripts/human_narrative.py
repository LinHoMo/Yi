# -*- coding: utf-8 -*-
"""
解读正文生成 — 全文就是给人读的那一份，不是另贴一层「人话章节」。

写法：像懂行的人当面把卦讲清楚。
- 先接住问题，再亮结论，再讲为什么，最后说怎么做
- 术语出现时顺口带一句，不讲课、不堆字段
- 不把引擎的「N项/N分/效应0.0」原样倒出来
- 思维链与标签只作附录，正文不以「人话/古典」分栏
"""
from __future__ import annotations

import json
from pathlib import Path
from chain_verdicts import NARRATIVE_HINTS, PATTERN_RELATED  # noqa: E402
from chain_tables import _BRANCH_CLASH_MAP, _HE_MAP  # noqa: E402


try:
    from advice_framework import generate_advice, match_advice_category
except ImportError:
    from scripts.advice_framework import generate_advice, match_advice_category


# ── 叙事模板外置 data/narrative_templates.json（AGENTS.md 三：断语进 data，py 只组装）──
_NARRATIVE_TEMPLATES_PATH = Path(__file__).resolve().parents[1] / "data" / "narrative_templates.json"


def _load_narrative_templates() -> dict:
    try:
        return json.loads(_NARRATIVE_TEMPLATES_PATH.read_text(encoding="utf-8"))
    except OSError:
        return {}


_NARRATIVE_TPL = _load_narrative_templates()


def _pos_name(p) -> str:
    try:
        p = int(p)
    except Exception:
        return str(p or "")
    return {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}.get(p, f"{p}爻")


def _strength_sentence(level: str, use_cat: str, use_br: str, use_pos, yuan_moving: bool = False, yuan_greedy: bool = False) -> str:
    """把旺衰说成对这件事意味着什么——老师傅看盘的口吻，月破单列。

    断语文案在 data/narrative_templates.json#strength_phrases，此处只组装。
    """
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
    """第一句：先接住问题、亮明结论，并直接给出最关键的一条理由。文案在 narrative_templates。"""
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
    """动变：说清楚谁在动、对事情是帮还是扯后腿——文案在 narrative_templates#change_sentences。"""
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
            bits.append(_fmt("other", pos=pos, rel=rel or "他爻"))

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
    """应期段：优先从 yingqi_dates 读日历日期（如 9月23日），无则回退到地支描述。"""
    # 应期日历日期（来自 s5.yingqi_dates.dates）
    dates_blob = (s5 or {}).get("yingqi_dates") or {}
    calendar_dates = (dates_blob.get("dates") or []) if isinstance(dates_blob, dict) else []
    calendar_str = ""
    if calendar_dates:
        # 取前 3 条 (date, description)
        shown = []
        for d in calendar_dates[:3]:
            shown.append(f"{d.get('date','')}({d.get('description','')})")
        calendar_str = "、".join(shown)
    # 六冲合 → 对应冲合之日
    clashing = _BRANCH_CLASH_MAP
    combining = {b: (ps[0] if ps else "") for b, ps in _HE_MAP.items()}
    t = timing if isinstance(timing, dict) else {}
    keys = list(t.get("key_branches") or [])
    speed = str(t.get("speed") or "")
    use_br = str((s3 or {}).get("use_god_branch") or "")
    sp = ""
    if isinstance(special, dict):
        sp = str(special.get("pattern") or "") + str(special.get("description") or "")

    # —— 先从用神地支推应期 ——
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

    # —— 基础快慢 ——
    if "近病逢空" in sp or "近病" in sp:
        base = NARRATIVE_HINTS["timing_near_illness_void"]
    elif speed == "应速" or "应速" in str(t.get("summary_text") or "") or "次日" in str(t.get("summary_text") or ""):
        base = NARRATIVE_HINTS["timing_fast"]
    elif speed == "应迟" or "应迟" in str(t.get("summary_text") or "") or "年内" in str(t.get("summary_text") or ""):
        base = NARRATIVE_HINTS["timing_slow"]
    else:
        base = NARRATIVE_HINTS["timing_mid"]

    if "合处逢冲" in sp or "冲中逢合" in sp or "反吟" in sp:
        base += NARRATIVE_HINTS["timing_repeat"]

    if day_hint:
        base += NARRATIVE_HINTS["timing_day_detail"].format(day_hint=day_hint)
    elif keys:
        shown = "、".join(keys[:3])
        base += NARRATIVE_HINTS["timing_shown"].format(shown=shown)
    # 日历日期（若存在就补上精确日期；与 day_hint/keys 不冲突）
    if calendar_str:
        base += NARRATIVE_HINTS["timing_calendar"].format(calendar_str=calendar_str)
    return base


# ── pattern 标签 → 相关引文 pattern 映射（人工精选）──
# 每个 pattern 标签对应应该被优先引用的引文 pattern 名
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


def _meaning_paragraph(verdict, s2, s3, special, question, factor_contribs=None) -> str:
    """第五段：综合定性 + 精简引用关键因子。

    改进点：
    - 消除原来硬凑「原神当权阻力实在」这类与实际数据矛盾的套话
    - 改为直接引用 factor_contributions 里已有的因子名+理由（**不暴露评分数字**）
    - 去掉「事难成，守住等时机」这类与 advice 重复的表述
    - 内部评分是回归审计用的对齐分，不等于预测能力，不对外暴露（AGENTS.md §三）
    """
    use_cat = s2.get("use_god_category") or "用神"
    yuan = (s2.get("yuan_shen") or {}).get("category") or ""
    ji = (s2.get("ji_shen") or {}).get("category") or ""
    strength = str(s3.get("strength_level") or "") if s3 else ""
    focus = _question_focus(question)

    vdir = 1 if ("吉" in str(verdict) and "凶" not in str(verdict) and "不利" not in str(verdict)) else (
        -1 if ("凶" in str(verdict) or "跌" in str(verdict) or "不利" in str(verdict)) else 0
    )

    parts = []
    # —— 一言定性（精简、不再与 p1 重复） ——
    if vdir > 0:
        parts.append(f"方向可以推进，但别贪。")
    elif vdir < 0:
        parts.append(f"风头不利，暂把现有局面稳住更划算。")
    else:
        parts.append(f"事在两可之间，谁先动谁定局。")

    # —— 引用 factor_contributions 关键项（只说因子名+理由，不带评分数字） ——
    if factor_contribs:
        pos_items = [fc for fc in factor_contribs if (fc.get("score") or 0) > 0][:2]
        neg_items = [fc for fc in factor_contribs if (fc.get("score") or 0) < 0][:2]
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

    # —— 弱而格吉/弱而格凶，点一句 ——
    if any(x in strength for x in ("弱", "囚", "死")) and vdir > 0:
        parts.append("用神虽弱，却得格局生扶——'绝处逢生'之象，成可成，心力要花够。")
    if any(x in strength for x in ("弱", "囚", "死")) and vdir <= 0:
        parts.append("用神弱叠不利——'克多出暴'之险，此时当守不宜攻。")
    if "冲中逢合" in str(special or ""):
        parts.append("冲中逢合，先难后成——过前面那关才谈得到后面的合。")
    if "回头克" in str(special or ""):
        parts.append("回头克为'自伤'——阻力从内在格局生，稳住节奏便是破法。")

    return "".join(parts)


def _clean_reason(reason: str, name: str) -> str:
    """去掉 factor_contribution.reason 里的技术备注，只留 15 字内的人类可读短句。"""
    if not reason:
        return ""
    import re
    r = re.sub(r"[（(]\s*[+-]?\d+[\d.]*[%]?\s*[）)]", "", reason)
    r = re.sub(r"【[^】]*】", "", r)
    r = r.replace(name, "")
    r = r.strip("，。：:, ")
    r = re.split(r"[，。；,;]", r, maxsplit=1)[0]
    if len(r) > 15:
        r = r[:15]
    return r.strip() or ""


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

    # 1) 临用爻优先
    for s in stars:
        if not isinstance(s, dict):
            continue
        name = str(s.get("name") or "")
        if not name:
            continue
        on_lines = s.get("on_lines") or []
        if any(_line_on_pos(ln, use_pos) for ln in on_lines):
            _push((tpl.get("on_use_god") or "{name}临用爻").format(name=name), name)
    # 2) 其他临爻
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
    # 3) 仅临日
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


# 旧名导出
build_reading = build_human_narrative
