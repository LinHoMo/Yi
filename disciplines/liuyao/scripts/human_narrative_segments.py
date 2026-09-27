# -*- coding: utf-8 -*-
"""正文段落素材生成 — 从 human_narrative 按域拆出（AGENTS.md：断语进 data，py 只组装）。

本模块只负责把各维度的机械结论翻译成「给人读的那一段」：
旺衰、结论开头、动变、特殊格局、应期、综合定性、病药、星煞。
编排（build_human_narrative）与导出（render_human_markdown）留在 human_narrative。
只 import 叶子模块，不反引 human_narrative，规避循环依赖。
"""
from __future__ import annotations

import json
from pathlib import Path
from chain_verdicts import NARRATIVE_HINTS  # noqa: E402
from chain_tables import _BRANCH_CLASH_MAP, _HE_MAP  # noqa: E402
_NARRATIVE_TEMPLATES_PATH = Path(__file__).resolve().parents[1] / "data" / "narrative_templates.json"

def _load_narrative_templates() -> dict:
    try:
        return json.loads(_NARRATIVE_TEMPLATES_PATH.read_text(encoding="utf-8"))
    except OSError:
        return {}

_NARRATIVE_TPL = _load_narrative_templates()

_ADVICE_SOFT = _NARRATIVE_TPL.get("advice_soft") or {}

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
        parts.append(_ADVICE_SOFT.get("push") or "")
    elif vdir < 0:
        parts.append(_ADVICE_SOFT.get("hold") or "")
    else:
        parts.append(_ADVICE_SOFT.get("wait") or "")

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
    import re
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
