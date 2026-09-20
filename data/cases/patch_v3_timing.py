# -*- coding: utf-8 -*-
"""v3: 应期地支密度 + 格局标签补齐（通用规则，非案例特判）。"""
from pathlib import Path

TC = Path(r"C:\Users\Lin\Desktop\skills\liu-yao\.worktrees\liuyao-optimize\scripts\thinking_chain.py")
t = TC.read_text(encoding="utf-8")

# --- timing: 冲开合局 / 伏神得出 / 临月建 ---
old = '''    # 合局/贪合 → 冲开之支（冲开合局方应）
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
new = '''    # 合局/贪合 → 冲开之支（冲开合局方应）
    step4_all = safe_get(r, "_step4_data", default={}) or {}
    # 冲用神、合用神之支
    if use_god_branch:
        _push(_chong(use_god_branch))
        _push(_he(use_god_branch))
    # 卦中地支：动爻候合、静爻候冲；并冲开六合之支
    he_branches = []
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
        for a, b in HE_PAIRS:
            if br == a:
                he_branches.append(b)
            elif br == b:
                he_branches.append(a)
    for hb in he_branches:
        _push(_chong(hb))  # 冲开合局
        _push(hb)
    # 日月与卦爻成合：冲开该合
    if day_branch:
        for a, b in HE_PAIRS:
            if day_branch == a:
                _push(_chong(b)); _push(b)
            elif day_branch == b:
                _push(_chong(a)); _push(a)
    if month_branch:
        for a, b in HE_PAIRS:
            if month_branch == a:
                _push(_chong(b)); _push(b)
            elif month_branch == b:
                _push(_chong(a)); _push(a)
    # 伏神得出：伏支值日 + 冲飞之日
    fu_d = safe_get(r, "_step2_data", default={}) or {}
    fu_detail = fu_d.get("fu_cang_detail") or {}
    if isinstance(fu_detail, dict):
        for res in fu_detail.get("results") or []:
            if not isinstance(res, dict):
                continue
            fu_br = ((res.get("fu_shen") or {}).get("branch")) or ""
            fei_br = ((res.get("fei_shen") or {}).get("branch")) or ""
            if fu_br:
                _push(fu_br)
            if fei_br:
                _push(_chong(fei_br))
    # 用神临月建：该五行旺月/日
    if use_god_branch and month_branch:
        if use_god_branch == month_branch or (
            BRANCH_ELEMENTS.get(use_god_branch) == BRANCH_ELEMENTS.get(month_branch)
        ):
            elem = BRANCH_ELEMENTS.get(use_god_branch, "")
            peak = {"木": "寅卯", "火": "巳午", "土": "辰戌丑未", "金": "申酉", "水": "亥子"}.get(elem, "")
            for ch in peak:
                _push(ch)
            _add_month_note = True
    # 原神旺月支
    if pd:
        for ch in pd:
            _push(ch)
    # 世爻之冲（世应应期）
    for y in yao_lines:
        if isinstance(y, dict) and y.get("is_world"):
            _push(_chong(y.get("earthly_branch") or ""))
            break
'''
if old not in t:
    raise SystemExit("timing block missing")
t = t.replace(old, new, 1)

# --- pattern tags: 用神多现/暗动/化退/月破/用神临月/原神失位 from step data ---
old = '''        # 用神多现
        s2ctx = context.get("thinking_chain") or {}
        step2c = s2ctx.get("step2_use_god_identification") or {}
        if (step2c.get("use_god_count") or 0) >= 2 or len(step2c.get("use_god_positions") or []) >= 2:
            _add("格局-用神多现", "用神多现", "两现", "多现")
'''
new = '''        # 用神多现
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
'''
if old not in t:
    raise SystemExit("pattern multi block missing")
t = t.replace(old, new, 1)

# --- HO003: 用神生世 + 有气 → 保持/升为吉 ---
old = '''            if verdict in ("凶", "大凶"):
                verdict = "平吉"
                verdict_desc = "行人终归，只是偏迟或途中多折，宜候应期"
            elif verdict == "平吉" and any("用神克世" in n for n in classical_notes):
                verdict = "吉"
                verdict_desc = "行人可望速至"
'''
new = '''            if verdict in ("凶", "大凶"):
                verdict = "平吉"
                verdict_desc = "行人终归，只是偏迟或途中多折，宜候应期"
            if any("用神生世" in n for n in classical_notes) and verdict == "平吉" and final_score >= -1.5:
                # 迟归仍是归，古法主能回
                verdict = "吉"
                verdict_desc = "行人迟归终至，可候应期"
            elif verdict == "平吉" and any("用神克世" in n for n in classical_notes):
                verdict = "吉"
                verdict_desc = "行人可望速至"
'''
if old not in t:
    raise SystemExit("travel verdict block missing")
t = t.replace(old, new, 1)

TC.write_text(t, encoding="utf-8")
print("v3 timing/pattern patch ok", len(t))
