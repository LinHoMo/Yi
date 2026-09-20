# -*- coding: utf-8 -*-
"""optimize: 通用规则 — 原神失位、久病逢冲、应期地支密度、格局标签。"""
from pathlib import Path

TC = Path(r"C:\Users\Lin\Desktop\skills\liu-yao\.worktrees\liuyao-optimize\scripts\thinking_chain.py")
text = TC.read_text(encoding="utf-8")

# --- 1) classical rules: add 原神失位 / 久病 / 官鬼暗动 after 世持财 block ---
old = '''    # 3) 妻财持世 + 失物 — 世持财主自失可寻（增删失物章）
    if world_relation == "妻财" and any(k in _q_l for k in ("失", "找回", "失物", "银")):
        classical_adj += 0.8
        classical_notes.append("【世持财·失物】世持财主物未远失，+0.8")
'''
new = '''    # 3) 妻财持世 + 失物 — 世持财主自失可寻（增删失物章）
    if world_relation == "妻财" and any(k in _q_l for k in ("失", "找回", "失物", "银")):
        classical_adj += 0.8
        classical_notes.append("【世持财·失物】世持财主物未远失，+0.8")

    # 5) 原神失位：用神旺相而原神不动作 — 黄金策「用神虽旺亦凶」
    _lv_ug = str((step3_data or {}).get("strength_level") or "")
    _yuan = (step2_data or {}).get("yuan_shen") or {}
    _yuan_pos = _yuan.get("positions") or []
    _yuan_moving = any(isinstance(p, dict) and p.get("is_moving") for p in _yuan_pos)
    if _lv_ug in ("旺", "极旺") and ug_cat and ug_cat != "世爻":
        if (not _yuan_pos) or (not _yuan_moving):
            # 原神不在卦或全静：旺而无源
            classical_adj -= 1.0
            classical_notes.append("【原神失位】用神虽旺而原神不动/缺位，旺极无源，-1.0")

    # 6) 久病逢冲为凶（对「近病逢冲即愈」）
    if any(k in _q_l for k in ("久病", "半年", "病久", "多月")):
        classical_adj -= 0.8
        classical_notes.append("【久病】久病正气已衰，逢冲逢克主凶，-0.8")

    # 7) 兄弟持世 + 功名/考试 — 竞争费力（可中而难前茅）
    if world_relation == "兄弟" and any(k in _q_l for k in ("考试", "功名", "学业", "科举", "中第")):
        classical_adj -= 0.4
        classical_notes.append("【兄弟持世求名】竞争费力，可成而名次不显，-0.4")
'''
if old not in text:
    raise SystemExit("classical block anchor missing")
text = text.replace(old, new, 1)

# --- 2) verdict micro: 原神失位/久病 cap 大吉; 考试兄弟持世 → 平吉 ---
old2 = '''    # 古籍通用口径：行人「用神生世/克世」主能归；兄弟持世求财主耗
    if classical_notes:
'''
new2 = '''    # 古籍通用口径：行人「用神生世/克世」主能归；兄弟持世求财主耗
    if classical_notes:
        if any("原神失位" in n for n in classical_notes):
            if verdict == "大吉":
                verdict = "吉"
                verdict_desc = "表面有力，实则源头不足，勿被旺象迷惑"
            elif verdict == "吉" and final_score < 2.0:
                verdict = "平吉"
                verdict_desc = "用神看似不弱，但原神未动，成算要打折"
            elif final_score < 0 and verdict in ("平吉", "吉"):
                verdict = "凶"
                verdict_desc = "旺而无源，古法主事难持久"
        if any("久病" in n for n in classical_notes):
            if verdict in ("大吉", "吉"):
                verdict = "平吉" if verdict == "吉" else "凶"
                if verdict == "平吉":
                    verdict_desc = "久病不宜言吉，仍以调护就医为先"
            if verdict == "平吉" and any(k in _q_l for k in ("久病", "半年")):
                verdict = "凶"
                verdict_desc = "久病体衰，卦象偏紧，务必遵医嘱"
        if any("兄弟持世求名" in n for n in classical_notes) and verdict in ("吉", "大吉"):
            verdict = "平吉"
            verdict_desc = "功名有象，但竞争大、须全力以赴，名次未必靠前"
'''
if old2 not in text:
    raise SystemExit("verdict classical header missing")
text = text.replace(old2, new2, 1)

# --- 3) timing: denser branches ---
old3 = '''    # 旬空地支（出空应期）
    for e in (r.get("empty_branches") or []):
        _push(e)
'''
new3 = '''    # 旬空地支（出空应期）
    for e in (r.get("empty_branches") or []):
        _push(e)

    # 合局/贪合 → 冲开之支（冲开合局方应）
    step4_all = safe_get(r, "_step4_data", default={}) or {}
    blob4 = str(step4_all.get("summary_text") or "") + str(step4_all.get("change_net_effect_description") or "")
    special_blob = ""
    # 冲用神、合用神之支
    if use_god_branch:
        _push(_chong(use_god_branch))
        _push(_he(use_god_branch))
    # 卦中所有地支的冲合（古法：静者逢冲应，动者逢合应）
    for y in yao_lines:
        if not isinstance(y, dict):
            continue
        br = y.get("earthly_branch") or ""
        if not br:
            continue
        if y.get("is_moving"):
            _push(_he(br))
            _push(_chong(br))
        else:
            _push(_chong(br))
    # 原神旺月支
    if pd:
        for ch in pd:
            _push(ch)
'''
if old3 not in text:
    raise SystemExit("timing empty block missing")
text = text.replace(old3, new3, 1)

# --- 4) pattern tags: 原神失位/久病/用神多现/用神临月建 ---
old4 = '''        if any(k in _q for k in ("归", "回", "行人", "何日")):
            _add("格局-行人", "行人")
'''
new4 = '''        # 用神多现
        s2ctx = context.get("thinking_chain") or {}
        step2c = s2ctx.get("step2_use_god_identification") or {}
        if (step2c.get("use_god_count") or 0) >= 2 or len(step2c.get("use_god_positions") or []) >= 2:
            _add("格局-用神多现", "用神多现", "两现", "多现")
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
'''
if old4 not in text:
    raise SystemExit("pattern travel anchor missing")
text = text.replace(old4, new4, 1)

# pattern notes from classical_adj live in step5 summary - also inject via step5 summary_text compose
# ensure _compose_synthesis_summary includes classical notes if present in kwargs - optional

# --- 5) timing summary includes 冲开合局 phrase when he pairs exist ---
old5 = '''    speed_plain = {
        "应速": "事情来得偏快，快则当日、次日就可能见分晓",
'''
new5 = '''    if any("合" in str(t.get("method") or "") or "合" in str(t.get("description") or "") for t in timing_methods):
        speed_plain_extra = "合局宜候冲开之日。"
    else:
        speed_plain_extra = ""
    speed_plain = {
        "应速": "事情来得偏快，快则当日、次日就可能见分晓",
'''
if old5 not in text:
    raise SystemExit("speed_plain anchor missing")
text = text.replace(old5, new5, 1)

# append extra to summary_text construction
old6 = '''    summary_text = f"重点应期：{key_text}。{speed_plain}。" + (f"依据：{detail}。" if detail else "")
'''
new6 = '''    summary_text = f"重点应期：{key_text}。{speed_plain}。{speed_plain_extra}" + (f"依据：{detail}。" if detail else "")
'''
if old6 not in text:
    # try other form
    if 'summary_text = f"重点应期：{key_text}' in text:
        import re
        text2, n = re.subn(
            r'summary_text = f"重点应期：\{key_text\}。[^"]*"',
            'summary_text = f"重点应期：{key_text}。{speed_plain}。{speed_plain_extra}" + (f"依据：{detail}。" if detail else "")',
            text,
            count=1,
        )
        if n != 1:
            print("WARN: summary_text pattern not replaced")
        else:
            text = text2
    else:
        print("WARN: no summary_text key_text line")
else:
    text = text.replace(old6, new6, 1)

# classical notes into step5 summary for pattern detection - inject after classical_adj applied
old7 = '''    final_score = round(final_score, 2)

    # ---------- 5.7: 定性判断 ----------
'''
new7 = '''    final_score = round(final_score, 2)
    if classical_notes:
        # 写入 step5 展示与格局标签来源
        pass

    # ---------- 5.7: 定性判断 ----------
'''
if old7 in text:
    text = text.replace(old7, new7, 1)

# classical notes must be folded into pattern_verdict_note AFTER they are computed
old8 = '''    # ---------- 5.6: 综合评分 ----------
    final_score = (base_score + change_net_effect + hex_adjustment
'''
new8 = '''    # 古籍通用格局注记（供标签与人话）— 必须在 classical_notes 生成之后
    if classical_notes:
        extra = "；".join(classical_notes)
        if pattern_verdict_note:
            pattern_verdict_note = pattern_verdict_note + "；" + extra
        else:
            pattern_verdict_note = extra

    # ---------- 5.6: 综合评分 ----------
    final_score = (base_score + change_net_effect + hex_adjustment
'''
if old8 not in text:
    raise SystemExit("final_score block missing")
text = text.replace(old8, new8, 1)

# remove the broken inject at pattern_verdict_note = ""
old_bad = '''        pattern_verdict_note = ""
    # 古籍通用格局注记（供标签与人话）
    try:
        if classical_notes:
            extra = "；".join(classical_notes)
            if pattern_verdict_note:
                pattern_verdict_note = pattern_verdict_note + "；" + extra
            else:
                pattern_verdict_note = extra
    except Exception:
        pass
'''
if old_bad in text:
    text = text.replace(old_bad, '        pattern_verdict_note = ""\n', 1)


TC.write_text(text, encoding="utf-8")
print("optimize patch written", len(text))
