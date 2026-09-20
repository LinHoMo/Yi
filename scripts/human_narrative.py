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

from advice_framework import generate_advice, match_advice_category


def _pos_name(p) -> str:
    try:
        p = int(p)
    except Exception:
        return str(p or "")
    return {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}.get(p, f"{p}爻")


def _strength_sentence(level: str, use_cat: str, use_br: str, use_pos) -> str:
    """把旺衰说成对这件事意味着什么，而不是报分数。"""
    loc = ""
    if use_br:
        loc = f"{use_br}"
        if use_pos:
            loc += _pos_name(use_pos)
        loc = f"（落在{loc}）"
    table = {
        "极旺": f"{use_cat}{loc}气很足，事情有底气往外推。",
        "旺": f"{use_cat}{loc}得力，条件比表面上看起来更好。",
        "相": f"{use_cat}{loc}有根，能扛事，不是虚的。",
        "中和": f"{use_cat}{loc}不弱也不冲，成败更看后手怎么做。",
        "中和偏旺": f"{use_cat}{loc}略占上风，顺着来容易成。",
        "中和偏弱": f"{use_cat}{loc}稍显吃力，宜借力不宜硬顶。",
        "偏弱": f"{use_cat}{loc}偏软，先补条件再谈结果。",
        "弱": f"{use_cat}{loc}力量薄，急着要结果容易空。",
        "极弱": f"{use_cat}{loc}几乎使不上劲，此时强求多半反复。",
        "休囚": f"{use_cat}{loc}处在低潮，宜等转机不宜妄动。",
    }
    return table.get(str(level or ""), f"{use_cat}{loc}状态一般，需结合动变再看。")


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


def _verdict_opening(verdict: str, focus: str) -> str:
    table = {
        "大吉": f"就{focus}来说，这卦是顺的，天时人事都站在你这边。",
        "吉": f"就{focus}来说，整体能成，可以往前推，不必太犹豫。",
        "平吉": f"就{focus}来说，有戏，但别急着要一个痛快结果——节奏比结果更要紧。",
        "平/不利": f"就{focus}来说，先别急着定。事情容易反复，稳住再看更划算。",
        "下跌": f"就{focus}来说，势头偏弱，观望比追高稳妥。",
        "凶": f"就{focus}来说，阻力是实的，硬上容易吃亏。",
        "大凶": f"就{focus}来说，眼下不是发力的时候，先守住比较重要。",
    }
    return table.get(str(verdict or ""), f"就{focus}来说，卦象已明，先看关键处再定节奏。")


def _change_sentence(s4: dict, s2: dict) -> str:
    """动变：说清楚谁在动、对事情是帮还是扯后腿。"""
    details = (s4.get("details") or []) if s4 else []
    if not s4 or not s4.get("has_moving_lines") or not details:
        return "卦里没有动爻，事情相对安静，吉凶主要看用神本身够不够力，而不是突然杀出什么变数。"

    details = s4.get("details") or []
    net = float(s4.get("net_effect") or 0)
    yuan = (s2.get("yuan_shen") or {}).get("category") or ""
    use_cat = s2.get("use_god_category") or "用神"

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
                bits.append(f"{pos}{rel}发动，变出{chg}回头来生，用神自己有劲往上走")
            elif "回头克" in ct:
                bits.append(f"{pos}{rel}动了，却化出回头克，事情容易在关键处掉链子")
            elif "反吟" in ct:
                bits.append(f"{pos}{rel}动而反吟，过程反复，进两步可能退一步")
            else:
                bits.append(f"{pos}{rel}有动，事情在动，不是死水一潭")
        elif role == "原神":
            bits.append(f"{pos}{rel}（生助{use_cat}的力量）发动，等于有人在后面托一把")
        elif role == "忌神":
            if "回头克" in ct:
                bits.append(f"{pos}{rel}虽是阻力，但动化回头克，阻力自己先受损")
            elif "贪合" in str(d.get("effect_on_usegod") or "") or "合" in ct:
                bits.append(f"{pos}{rel}被合住，一时顾不上来捣乱")
            else:
                bits.append(f"{pos}{rel}有动，要留意有人或有事来添堵")
        else:
            bits.append(f"{pos}{rel or '他爻'}亦有变化")

    if not bits:
        bits.append("卦中有动，变化落在细节上，主线仍看用神")

    tail = "这些动处总体对事情有利。" if net > 0.3 else (
        "这些动处总体偏扯后腿。" if net < -0.3 else "动处利弊参半，关键还在用神自身强弱。"
    )
    return "；".join(bits) + "。" + tail


def _special_sentence(special, s3, s2, question: str) -> str:
    if not isinstance(special, dict):
        return ""
    pat = str(special.get("pattern") or "")
    desc = str(special.get("description") or "")
    focus = _question_focus(question)
    empty = bool(s3.get("is_empty")) if s3 else False
    strength = str((s3 or {}).get("strength_level") or "")

    if "近病逢空" in pat or "近病逢空" in desc:
        return "病气逢空，古法主近病易退——不是没事，而是病势有松动的迹象，按医嘱静养，往往比想象中快见好。"
    if "近病逢合" in pat:
        return "近病本忌缠住不放，卦里又见合，病情容易拖泥带水，别大意，该看医生就看。"
    if "合处逢冲" in pat:
        if "婚" in focus or "婚姻" in focus:
            return "卦是六合，本来利成，但日辰冲动世爻——先合后散，事情容易开头热、后面凉，别急着把话说死。"
        return f"表面有合，内里逢冲，{focus}容易先顺后挫，推进时留一手。"
    if "冲中逢合" in pat:
        return "看着像散，细处又有合来解——先难后成的路子，别在第一关就放弃。"
    if "反吟" in pat:
        return "卦带反吟，过程多半反复，不是直线走完；心里有数，就不容易被一次起落打乱。"
    if pat:
        return f"此卦另有格局：{pat}。{desc}" if desc else f"此卦另有格局：{pat}。"
    if empty and any(x in strength for x in ("旺", "相", "中和")):
        return "用神虽落空亡，却得日月生扶，空而有根——事情不是没有，而是还欠一个「落实」的时机。"
    return ""


def _timing_sentence(timing: dict, special, s3) -> str:
    t = timing if isinstance(timing, dict) else {}
    keys = list(t.get("key_branches") or [])
    speed = str(t.get("speed") or "")
    sp = ""
    if isinstance(special, dict):
        sp = str(special.get("pattern") or "") + str(special.get("description") or "")

    if "近病逢空" in sp or "近病" in sp:
        base = "病这类事，卦象偏快——近日、快则次日就该见松动，不必按「很久以后」来等。"
    elif speed == "应速" or "应速" in str(t.get("summary_text") or "") or "次日" in str(t.get("summary_text") or ""):
        base = "事情来得偏快，快则当日、次日就值得多留心。"
    elif speed == "应迟" or "应迟" in str(t.get("summary_text") or "") or "年内" in str(t.get("summary_text") or ""):
        base = "事情偏慢，可能要等旺相之月，年内陆续应验——别用三五天去衡量。"
    else:
        base = "时间上不急不缓，近期数日到一两个月都算有效观察期。"

    if "合处逢冲" in sp or "冲中逢合" in sp or "反吟" in sp:
        base += "过程中容易反复，心里预期放稳一点。"

    if keys:
        shown = "、".join(keys[:5])
        base += f"可多留意：{shown}。"
    return base


def _meaning_paragraph(verdict, s2, s3, special, question) -> str:
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
        parts.append(f"换句话说：{focus}不是没机会，而是机会在——关键是别把顺局做成僵局。")
    elif vdir < 0:
        parts.append(f"换句话说：{focus}现在卡住的地方是真的，硬闯多半耗神，先止损、先蓄势更聪明。")
    else:
        parts.append(f"换句话说：{focus}成败不在一锤定音，而在时机与配合是否到位。")

    if yuan and ji:
        parts.append(f"帮你的一侧是{yuan}所主之事，要防的是{ji}所主的阻力。")
    elif yuan:
        parts.append(f"局面里还有{yuan}这一路助力可用。")
    elif ji:
        parts.append(f"阻力主要来自{ji}所主的方面。")

    if any(x in strength for x in ("弱", "囚", "死")) and vdir > 0:
        parts.append("用神偏弱却仍断偏吉，多半是另有生扶或格局在撑——成是能成，过程会比「一路绿灯」费些心。")
    if any(x in strength for x in ("弱", "囚", "死")) and vdir <= 0:
        parts.append("用神本就偏弱，再叠上不利格局，此时更要控制预期，先求稳再求成。")
    if "冲中逢合" in str(special or ""):
        parts.append("古书说「冲中逢合，先难后成」，正合此象。")

    return "".join(parts)


def build_human_narrative(result: dict) -> dict:
    """
    生成完整解读正文（唯一交付口吻）。
    兼容旧字段名，便于报告/门户复用。
    """
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

    p1 = _verdict_opening(verdict, focus)
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
        + _strength_sentence(strength, use_cat, use_br, use_pos)
    )

    p3 = _change_sentence(s4, s2)
    p4 = _special_sentence(special, s3, s2, question)
    p5 = _meaning_paragraph(verdict, s2, s3, special, question)

    body = [x for x in (p1, p2, p3, p4, p5) if x]
    lead = p1

    timing_plain = _timing_sentence(timing, special, s3)

    try:
        advice = generate_advice(verdict, question or focus, result)
    except Exception:
        advice = []
    if not advice:
        if "凶" in str(verdict) or "跌" in str(verdict):
            advice = ["先稳住现有局面，不宜加码", "把风险点列出来，能避则避", "等用神得力的时段再考虑推进"]
        else:
            advice = ["顺着已有条件推进，不必反复起念试探", "抓住用神得力的时段做关键动作", "过程有起伏属正常，盯住主线即可"]

    quotes = []
    for q in (result.get("classical_quotes") or [])[:2]:
        if isinstance(q, dict) and q.get("quote"):
            quotes.append({"source": q.get("source", "经典"), "quote": q.get("quote")})

    caveat = (
        "这是按纳甲六爻规则推出来的一份参考，讲的是方向和节奏，不是板上钉钉的预言。"
        "看病、打官司、做重大决定，仍要以专业意见为准。"
    )
    conf_note = f"线索一致程度约 {conf}%，供你判断这份解读有多「齐心」。" if conf not in (None, "") else ""

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
