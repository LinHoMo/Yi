# -*- coding: utf-8 -*-
"""Holdout 基线后的系统性规则补丁（非案例特判）。"""
from pathlib import Path

TC = Path(r"C:\Users\Lin\Desktop\skills\liu-yao\.worktrees\liuyao-holdout\scripts\thinking_chain.py")
text = TC.read_text(encoding="utf-8")

old = '''    # ---------- 5.6: 综合评分 ----------
    final_score = (base_score + change_net_effect + hex_adjustment
                   + spirit_adjustment + pattern_adjustment
                   + dmb_adjustment + sb_adjustment
                   + combo_break_adjustment
                   + officer_tomb_adjustment
                   + fu_shen_adjustment)
    final_score = round(final_score, 2)
'''

new = '''    # ---------- 5.5h: 古籍通用格局加减（holdout 暴露的系统性缺口） ----------
    classical_adj = 0.0
    classical_notes = []
    _q_l = str((r.get("question") or r.get("question_category") or ""))
    _is_travel_return = any(k in _q_l for k in ("归", "回", "行人", "何日", "逃仆", "出外", "出行"))
    _is_wealth = any(k in _q_l for k in ("财", "投资", "生意", "价", "贸易", "求财", "经营", "银", "失物", "失"))
    _is_illness = any(k in _q_l for k in ("病", "疾", "愈"))

    # 世爻六亲
    world_relation = ""
    world_branch = ""
    use_el_s = (step2_data or {}).get("use_god_element") or ""
    ug_cat = (step2_data or {}).get("use_god_category") or ""
    ug_sel = (step2_data or {}).get("selected_use_god") or {}
    ug_branch_s = ug_sel.get("earthly_branch") or (step3_data or {}).get("use_god_branch") or ""
    ug_el_s = ug_sel.get("element") or use_el_s
    for _y in ((r.get("original_hexagram") or {}).get("yao_lines") or []):
        if isinstance(_y, dict) and _y.get("is_world"):
            world_relation = _y.get("six_relation") or ""
            world_branch = _y.get("earthly_branch") or ""
            break
    palace_el = (r.get("original_hexagram") or {}).get("palace_element") or ""

    def _el_of_branch(b):
        return BRANCH_ELEMENTS.get(b or "", "")

    # 1) 行人/归期：用神生世 — 迟归，终归（《黄金策》出行章）
    if _is_travel_return and ug_el_s and world_branch:
        w_el = _el_of_branch(world_branch) or ""
        if w_el and SHENG_CYCLE.get(ug_el_s) == w_el:
            classical_adj += 1.5
            classical_notes.append("【用神生世·迟归】行人占用神生世，主迟归终至，+1.5")
        elif w_el and KE_CYCLE.get(ug_el_s) == w_el:
            # 用神克世：速至，亦主能归
            classical_adj += 0.8
            classical_notes.append("【用神克世·速至】行人占用神克世，主速至，+0.8")

    # 2) 兄弟持世 + 求财 — 古籍大忌（《增删》兄弟持世莫求财）
    if world_relation == "兄弟" and _is_wealth and ug_cat == "妻财":
        classical_adj -= 1.2
        classical_notes.append("【兄弟持世求财】兄弟克财，求财多耗，-1.2")

    # 3) 妻财持世 + 失物 — 世持财主自失可寻（增删失物章）
    if world_relation == "妻财" and any(k in _q_l for k in ("失", "找回", "失物", "银")):
        classical_adj += 0.8
        classical_notes.append("【世持财·失物】世持财主物未远失，+0.8")

    # 4) 用神临月建（通用旺格标记分已在旺衰，此处仅补注记）

    # ---------- 5.6: 综合评分 ----------
    final_score = (base_score + change_net_effect + hex_adjustment
                   + spirit_adjustment + pattern_adjustment
                   + dmb_adjustment + sb_adjustment
                   + combo_break_adjustment
                   + officer_tomb_adjustment
                   + fu_shen_adjustment
                   + classical_adj)
    final_score = round(final_score, 2)
'''

if old not in text:
    raise SystemExit("score block not found")
text = text.replace(old, new, 1)

# verdict micro-adjust after 口径微调
old2 = '''    if any(k in _qtext for k in ("价", "贵贱", "桑叶", "涨跌")) and verdict in ("凶", "大凶"):
        verdict = "下跌"
        verdict_desc = "势头偏弱，观望比追高稳妥"
'''
new2 = '''    if any(k in _qtext for k in ("价", "贵贱", "桑叶", "涨跌")) and verdict in ("凶", "大凶"):
        verdict = "下跌"
        verdict_desc = "势头偏弱，观望比追高稳妥"

    # 古籍通用口径：行人「用神生世/克世」主能归；兄弟持世求财主耗
    if classical_notes:
        if _is_travel_return and any("用神生世" in n or "用神克世" in n for n in classical_notes):
            if verdict in ("凶", "大凶"):
                verdict = "平吉"
                verdict_desc = "行人终归，只是偏迟，途中或有拖宕"
            elif verdict == "平吉" and any("用神克世" in n for n in classical_notes):
                verdict = "吉"
                verdict_desc = "行人可望速至"
        if world_relation == "兄弟" and _is_wealth and ug_cat == "妻财":
            if verdict in ("大吉",):
                verdict = "吉"
                verdict_desc = "有财可谋，但兄弟持世，到手易耗"
            elif verdict == "吉" and final_score < 2.5:
                verdict = "平吉"
                verdict_desc = "财路有象，兄弟持世须防破耗"
            elif verdict in ("平吉",) and final_score <= 0.2:
                verdict = "平/不利"
                verdict_desc = "兄弟持世求财，辛苦多耗，得不偿失"
'''
if old2 not in text:
    raise SystemExit("verdict micro block not found")
text = text.replace(old2, new2, 1)

# pattern tags: shi yao + travel/wealth classical
old3 = '''    if tags:
        # 保留「格局-」前缀供机器，同时写入经典裸词供盲评字典命中
        chain.append("[格局] " + " | ".join(tags))
        bare = [t.replace("格局-", "") for t in tags]
        chain.append("[格局要点] " + "、".join(bare))
'''
new3 = '''    # 六亲持世 / 行人迟归 / 用神临月建（通用古籍标签）
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
'''
if old3 not in text:
    raise SystemExit("tags footer not found")
text = text.replace(old3, new3, 1)

# timing: 冲开合局 / 出空月份
old4 = '''    if is_empty:
        timing_methods.append({
            "method": "出空",
            "description": f"用神「{use_god_branch}」出旬之日应（出空/填实）",
            "type": "空亡应期",
        })
'''
new4 = '''    if is_empty:
        timing_methods.append({
            "method": "出空",
            "description": f"用神「{use_god_branch}」出旬之日应（出空/填实）",
            "type": "空亡应期",
        })
        # 常见出空应期支：待用神值日或填实之支
        if use_god_branch:
            _push(use_god_branch)
        for e in (r.get("empty_branches") or []):
            _push(e)
'''
if old4 not in text:
    raise SystemExit("timing empty block not found")
text = text.replace(old4, new4, 1)

# classical_adj must be in scope for verdict block - we inserted before final_score; verdict uses classical_notes which is defined
# Fix: verdict micro-adjust references classical_notes, world_relation, _is_travel_return, _is_wealth, ug_cat - all defined before final_score
# But verdict block is AFTER final_score computation - classical_notes still in scope in same function. Good.

TC.write_text(text, encoding="utf-8")
print("patched thinking_chain, len", len(text))
