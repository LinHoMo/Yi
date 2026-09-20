# -*- coding: utf-8 -*-
"""把思维链各步 summary_text 改成可读叙述；结构化分数字段保留不动。"""
from pathlib import Path

TC = Path(r"C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py")
text = TC.read_text(encoding="utf-8")

# ---- step3 旺衰 summary ----
old3 = '''        "summary_text": (
            f"用神{use_god_category}居{selected_use_god.get('name')}，"
            f"五行{use_god_element}。"
            f"月建{month_branch}（{month_element}）→ {god_month_strength}（{god_month_score}分），"
            f"日辰{day_branch}（{day_element}）→ {god_day_strength}（{god_day_score}分）。"
            + (f"旬空：{empty_modifier_reason}，" if is_empty else "")
            + (f"月破：{month_break_modifier_reason}，" if is_month_break else "")
            + (f"暗动：{an_dong_modifier_reason}，" if is_an_dong else "")
            + (f"日破：{an_dong_modifier_reason}，" if an_dong_modifier_reason and not is_an_dong and not selected_use_god.get("is_moving", False) else "")
            + (f"十二长生：{twelve_growth_reason}，" if twelve_growth_modifier != 0 else "")
            + (f"{hidden_movement_reason}，" if hidden_movement and hidden_movement_reason else "")
            + (f"三刑：{tp_modifier_reason}（{tp_modifier:+.1f}），" if tp_modifier != 0 else "")
            + (f"绝处逢生：{desperate_relief_description}（{desperate_relief_modifier:+.1f}），" if desperate_relief_modifier != 0 and desperate_relief_description else "")
            + f"综合评分：{effective_score:.2f}（{strength_level}）。"
        ),'''

new3 = '''        "summary_text": _compose_strength_summary(
            use_god_category=use_god_category,
            selected_use_god=selected_use_god,
            use_god_element=use_god_element,
            month_branch=month_branch,
            month_element=month_element,
            god_month_strength=god_month_strength,
            god_month_score=god_month_score,
            day_branch=day_branch,
            day_element=day_element,
            god_day_strength=god_day_strength,
            god_day_score=god_day_score,
            is_empty=is_empty,
            empty_modifier_reason=empty_modifier_reason,
            is_month_break=is_month_break,
            month_break_modifier_reason=month_break_modifier_reason,
            is_an_dong=is_an_dong,
            an_dong_modifier_reason=an_dong_modifier_reason,
            twelve_growth_reason=twelve_growth_reason,
            twelve_growth_modifier=twelve_growth_modifier,
            hidden_movement=hidden_movement,
            hidden_movement_reason=hidden_movement_reason,
            tp_modifier_reason=tp_modifier_reason,
            tp_modifier=tp_modifier,
            desperate_relief_description=desperate_relief_description,
            desperate_relief_modifier=desperate_relief_modifier,
            effective_score=effective_score,
            strength_level=strength_level,
        ),'''

if old3 not in text:
    raise SystemExit("step3 summary not found")
text = text.replace(old3, new3, 1)

# insert helper before step3 return - find a unique anchor near analyze strength
anchor = '''# =============================================================================
# Step 3: 断旺'''
# actually find function that returns the summary - inject helper before "Step 4" or after USE_GOD tables
helper = '''

def _compose_strength_summary(**kw) -> str:
    """旺衰步骤：叙述体，分数只作括号备查。"""
    ug = kw.get("use_god_category") or "用神"
    name = (kw.get("selected_use_god") or {}).get("name") or ""
    elem = kw.get("use_god_element") or ""
    mb, me = kw.get("month_branch") or "", kw.get("month_element") or ""
    ms, msc = kw.get("god_month_strength") or "", kw.get("god_month_score")
    db, de = kw.get("day_branch") or "", kw.get("day_element") or ""
    ds, dsc = kw.get("god_day_strength") or "", kw.get("god_day_score")
    level = kw.get("strength_level") or ""
    score = kw.get("effective_score")
    parts = [f"{ug}在{name}，五行{elem}。"]
    parts.append(f"月建{mb}（{me}）对它{ms}，日辰{db}（{de}）对它{ds}。")
    extras = []
    if kw.get("is_empty") and kw.get("empty_modifier_reason"):
        extras.append(str(kw["empty_modifier_reason"]).rstrip("，。"))
    if kw.get("is_month_break") and kw.get("month_break_modifier_reason"):
        extras.append(str(kw["month_break_modifier_reason"]).rstrip("，。"))
    if kw.get("is_an_dong") and kw.get("an_dong_modifier_reason"):
        extras.append(str(kw["an_dong_modifier_reason"]).rstrip("，。"))
    if kw.get("twelve_growth_modifier") and kw.get("twelve_growth_reason"):
        extras.append(str(kw["twelve_growth_reason"]).rstrip("，。"))
    if kw.get("hidden_movement") and kw.get("hidden_movement_reason"):
        extras.append(str(kw["hidden_movement_reason"]).rstrip("，。"))
    if kw.get("tp_modifier") and kw.get("tp_modifier_reason"):
        extras.append(str(kw["tp_modifier_reason"]).rstrip("，。"))
    if kw.get("desperate_relief_modifier") and kw.get("desperate_relief_description"):
        extras.append(str(kw["desperate_relief_description"]).rstrip("，。"))
    if extras:
        parts.append("另外要留意：" + "；".join(extras) + "。")
    # 口语结论
    lv = str(level)
    say = {
        "极旺": "总起来说，用神很有底气。",
        "旺": "总起来说，用神得力。",
        "相": "总起来说，用神有根，能用。",
        "中和": "总起来说，用神不强不弱，看后手怎么走。",
        "中和偏旺": "总起来说，用神略占上风。",
        "中和偏弱": "总起来说，用神稍显吃力。",
        "偏弱": "总起来说，用神偏软，宜借力。",
        "弱": "总起来说，用神力量薄，不宜硬催结果。",
        "极弱": "总起来说，用神几乎使不上劲。",
        "休囚": "总起来说，用神处在低潮。",
    }.get(lv, f"总起来说，用神状态为{lv}。")
    parts.append(say)
    if score is not None:
        parts.append(f"（量化参考 {float(score):.2f} · {lv}）")
    return "".join(parts)


'''

# insert helper just before def step3 or a known function
if "_compose_strength_summary(" in text and "def _compose_strength_summary" not in text:
    # place before `# --- Step 2 辅助函数 ---` is wrong; put before step3 related
    # Use unique string from step3 function
    key = "def step3_analyze_strength"
    if key not in text:
        key = "Step 3"
    idx = text.find("def step3_analyze_strength")
    if idx < 0:
        # find another marker
        idx = text.find("月建日辰")
        if idx < 0:
            raise SystemExit("cannot find insert point for strength helper")
    text = text[:idx] + helper + text[idx:]

# ---- step4 summary ----
old4 = '''        "summary_text": (
            f"共有{len(moving_lines)}个动爻。"
            f"有利变化{len(favorable_changes)}项，不利变化{len(unfavorable_changes)}项。"
            f"{'贪生忘克：' + '、'.join(r['reason'] for r in tan_sheng_wan_ke) + '；' if tan_sheng_wan_ke else ''}"
            f"{'贪合忘生克：' + '、'.join(r['reason'] for r in tan_he_wan_sheng_ke) + '；' if tan_he_wan_sheng_ke else ''}"
            f"{greedy_harmony_summary}"
            f"{'进退神量化：{:+.2f}（加权评分）；'.format(advance_score_total) if abs(advance_score_total) > 0.001 else ''}"
            f"总体动变效应：{net_effect}（{net_description}）。"
        ),'''

new4 = '''        "summary_text": _compose_change_summary(
            moving_lines, favorable_changes, unfavorable_changes,
            tan_sheng_wan_ke, tan_he_wan_sheng_ke, greedy_harmony_summary,
            advance_score_total, net_effect, net_description,
        ),'''

if old4 not in text:
    raise SystemExit("step4 summary not found")
text = text.replace(old4, new4, 1)

helper4 = '''

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
    if net > 0.3:
        parts.append("综合动变，对事情偏有利。")
    elif net < -0.3:
        parts.append("综合动变，对事情偏不利。" + (f"（{net_desc}）" if net_desc and net_desc not in ("中性", "偏吉", "偏凶") else ""))
    else:
        parts.append("综合动变，利弊大致相抵。")
    return "".join(parts)


'''
idx4 = text.find("def _classify_line_role")
if idx4 < 0:
    raise SystemExit("cannot find _classify_line_role")
if "def _compose_change_summary" not in text:
    text = text[:idx4] + helper4 + text[idx4:]

# ---- step5 综合 summary ----
old5_start = '''        "summary_text": (
            f"【综合判断】"'''
idx5 = text.find(old5_start)
if idx5 < 0:
    raise SystemExit("step5 summary not found")
end5 = text.find("        # 卦身摘要", idx5)
if end5 < 0:
    raise SystemExit("step5 summary end not found")

new5 = '''        "summary_text": _compose_synthesis_summary(
            strength_level=strength_level,
            base_score=base_score,
            change_net_effect=change_net_effect,
            hex_adjustment=hex_adjustment,
            hex_adjustment_reason=hex_adjustment_reason,
            spirit_adjustment=spirit_adjustment,
            spirit_adjustment_reasons=spirit_adjustment_reasons,
            hm_modifier=hm_modifier,
            hm_reason=hm_reason,
            greedy_score=greedy_score,
            greedy_reason=greedy_reason,
            tp_score=tp_score,
            tp_reason=tp_reason,
            dmb_adjustment=dmb_adjustment,
            dmb_reason=dmb_reason,
            sb_adjustment=sb_adjustment,
            sb_reason=sb_reason,
            combo_break_adjustment=combo_break_adjustment,
            combo_break_reason=combo_break_reason,
            fu_shen_adjustment=fu_shen_adjustment,
            fu_shen_note=fu_shen_note,
            officer_tomb_adjustment=officer_tomb_adjustment,
            officer_tomb_reason=officer_tomb_reason,
            special_pattern=special_pattern,
            pattern_adjustment=pattern_adjustment,
            final_score=final_score,
            verdict=verdict,
            verdict_desc=verdict_desc,
            pattern_verdict_note=pattern_verdict_note,
            officer_tomb_verdict_note=officer_tomb_verdict_note,
            nayin_desc=nayin_desc,
            confidence=confidence,
            classical_quotes_text=classical_quotes_text,
        ),
'''
text = text[:idx5] + new5 + text[end5:]

helper5 = '''

def _compose_synthesis_summary(**kw) -> str:
    """综合步骤：先说结论，再说依据，分数只作备查。"""
    verdict = kw.get("verdict") or ""
    vdesc = kw.get("verdict_desc") or ""
    score = kw.get("final_score")
    level = kw.get("strength_level") or ""
    parts = [f"综合来看，断为{verdict}。"]
    if vdesc:
        parts.append(vdesc.rstrip("。") + "。")
    supports = []
    concerns = []
    # 旺衰
    lv_say = {
        "极旺": "用神很旺", "旺": "用神得力", "相": "用神有根",
        "中和": "用神中和", "中和偏旺": "用神略旺", "中和偏弱": "用神略弱",
        "偏弱": "用神偏弱", "弱": "用神力薄", "极弱": "用神极弱", "休囚": "用神休囚",
    }.get(str(level), f"用神{level}")
    supports.append(lv_say) if any(x in str(level) for x in ("旺", "相", "中和偏旺")) else concerns.append(lv_say)
    # 动变
    net = float(kw.get("change_net_effect") or 0)
    if net > 0.3:
        supports.append("动变有助力")
    elif net < -0.3:
        concerns.append("动变有牵扯")
    # 格局
    sp = kw.get("special_pattern") if isinstance(kw.get("special_pattern"), dict) else {}
    pat = str(sp.get("pattern") or "") if sp else ""
    if pat:
        if any(k in pat for k in ("逢合可解", "冲中逢合", "逢空即愈", "绝处逢生")):
            supports.append(f"格局「{pat}」在化解阻力")
        elif any(k in pat for k in ("逢冲", "逢合为凶", "随官", "反吟")):
            concerns.append(f"格局「{pat}」添变数")
        else:
            supports.append(f"见「{pat}」之象")
    if kw.get("pattern_verdict_note"):
        concerns.append(str(kw["pattern_verdict_note"]).rstrip("。"))
    if supports:
        parts.append("有利的一面：" + "，".join(supports) + "。")
    if concerns:
        parts.append("要当心的一面：" + "，".join(str(c) for c in concerns if c) + "。")
    if score is not None:
        parts.append(f"（量化参考 {float(score):.2f}，把握约 {kw.get('confidence','—')}%）")
    note_bits = [x for x in (
        kw.get("officer_tomb_verdict_note"), kw.get("nayin_desc"),
    ) if x]
    if note_bits:
        parts.append(" ".join(str(x) for x in note_bits))
    qt = kw.get("classical_quotes_text") or ""
    if qt:
        parts.append(str(qt).replace("【经典引文】", "古人类似情境有言："))
    return "".join(parts)


'''
if "def _compose_synthesis_summary" not in text:
    idx_s = text.find("def _predict_timing")
    if idx_s < 0:
        raise SystemExit("cannot find _predict_timing for helper5 insert")
    text = text[:idx_s] + helper5 + text[idx_s:]

# ---- 近病应期：强制偏快 ----
old_sp = '''    if "近病逢空" in sp or "近病" in sp:'''
# that's in human_narrative; in thinking_chain _predict_timing:
old_t = '''    speed_plain = {
        "应速": "节奏偏快，快则当日或次日可见分晓",
        "应期适中": "节奏适中，近期数日到一两月内更需留意",
        "应迟": "节奏偏慢，可能要等旺相之月，年内陆续应验",
    }.get(speed, speed)'''
new_t = '''    sp_blob = ""
    if isinstance(special_pattern, dict):
        sp_blob = str(special_pattern.get("pattern") or "") + str(special_pattern.get("description") or "")
    elif special_pattern:
        sp_blob = str(special_pattern)
    if any(k in sp_blob for k in ("近病逢空", "近病逢合", "近病")):
        speed = "应速"
    speed_plain = {
        "应速": "事情来得偏快，最近几天就值得多留心",
        "应期适中": "不急不缓，近期数日到一两个月都是观察期",
        "应迟": "事情偏慢，别用三五天衡量，放到更长的窗口里看",
    }.get(speed, speed)'''
if old_t not in text:
    raise SystemExit("timing speed_plain not found")
text = text.replace(old_t, new_t, 1)

# also humanize summary_text for timing slightly - keep 重点应期 for eval
old_ts = '''    summary_text = f"重点应期：{key_text}。{detail}。整体节奏：{speed}。{speed_plain}。"'''
new_ts = '''    # 保留「重点应期」与地支词供评估；叙述用人话
    summary_text = f"重点应期：{key_text}。{speed_plain}。" + (f"依据：{detail}。" if detail else "")'''
if old_ts not in text:
    raise SystemExit("timing summary_text not found")
text = text.replace(old_ts, new_ts, 1)

# ---- step1/step2 summary 更口语（若有） ----
old_s2 = '''            f"问题类型「{question_category}」→ 用神为{use_god_category}（五行属{use_god_element}）。"
            f"{'用神现于' + ''.join(str(p.get('position','')) + '爻 ' for p in use_god_positions) if use_god_positions else '用神不现，需查伏藏'}。"'''
new_s2 = '''            f"问的是「{question_category}」，用神取{use_god_category}（五行{use_god_element}）。"
            f"{'卦中用神在 ' + '、'.join(str(p.get('position','')) + '爻' for p in use_god_positions) if use_god_positions else '本卦用神不现，须查伏神'}。"'''
if old_s2 not in text:
    print("WARN: step2 summary fragment not found, skip")
else:
    text = text.replace(old_s2, new_s2, 1)

# verdict_desc 也改成自然句
old_vd = '''        verdict = "大吉"
        verdict_desc = "大吉之象，万事如意，顺应天时"
    elif final_score >= 1.0:
        verdict = "吉"
        verdict_desc = "吉祥之象，顺势而为，可得所愿"
    elif final_score >= -0.5:
        verdict = "平吉"
        verdict_desc = "小吉之象，吉中有凶，须防微杜渐"
    elif final_score >= -2.0:
        verdict = "凶"
        verdict_desc = "凶险之象，诸事不宜，守静安时"
    else:
        verdict = "大凶"
        verdict_desc = "大凶之象，万事不顺，宜静不宜动"
'''
new_vd = '''        verdict = "大吉"
        verdict_desc = "顺得很，该推进的可以推进"
    elif final_score >= 1.0:
        verdict = "吉"
        verdict_desc = "整体是顺的，往前走问题不大"
    elif final_score >= -0.5:
        verdict = "平吉"
        verdict_desc = "有戏但不稳，节奏比结果更要紧"
    elif final_score >= -2.0:
        verdict = "凶"
        verdict_desc = "阻力明显，硬上容易吃亏"
    else:
        verdict = "大凶"
        verdict_desc = "眼下不宜发力，先守住"
'''
if old_vd not in text:
    raise SystemExit("verdict_desc block not found")
text = text.replace(old_vd, new_vd, 1)

old_vd2 = '''            verdict = "平/不利"
            verdict_desc = "合处逢冲，先成后破，事多反复，平中带阻"
'''
new_vd2 = '''            verdict = "平/不利"
            verdict_desc = "先合后散，事情容易反复，适合稳住再看"
'''
if old_vd2 in text:
    text = text.replace(old_vd2, new_vd2, 1)

old_vd3 = '''        verdict = "下跌"
        verdict_desc = "用神失势，价格趋跌，宜观望不宜追高"
'''
new_vd3 = '''        verdict = "下跌"
        verdict_desc = "势头偏弱，观望比追高稳妥"
'''
if old_vd3 in text:
    text = text.replace(old_vd3, new_vd3, 1)

TC.write_text(text, encoding="utf-8")
print("thinking_chain summaries rewritten, len", len(text))

