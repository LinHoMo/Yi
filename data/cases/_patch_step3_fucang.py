# -*- coding: utf-8 -*-
"""P0-4e step3：三刑按用神过滤 + 伏藏用神走伏藏分支 + 飞空得出"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

# ---- 1. 3.10c 三刑：只计入用神自身参与的刑 ----
OLD_TP = '''    # ---------- 3.10c: 三刑修正（来自 advanced_analysis）----------
    tp_modifier = 0.0
    tp_issues = []
    advanced_for_tp = r.get("advanced_analysis", {})
    if advanced_for_tp and isinstance(advanced_for_tp, dict):
        tp_data = advanced_for_tp.get("three_punishments", {})
        if isinstance(tp_data, dict) and tp_data.get("has_punishment"):
            tp_modifier = tp_data.get("total_score", 0.0)
            for p in tp_data.get("punishments", []):
                comp = p.get("completeness", "")
                ptype = p.get("type", "")
                if comp == "待刑":
                    missing = p.get("missing", [])
                    tp_issues.append(f"{ptype}待刑(缺{','.join(missing)})")
                elif comp == "完整":
                    tp_issues.append(f"{ptype}(完整三刑)")
                elif comp == "成刑":
                    tp_issues.append(f"{ptype}(成刑)")
                else:
                    tp_issues.append(ptype)'''

NEW_TP = '''    # ---------- 3.10c: 三刑修正（来自 advanced_analysis）----------
    # P0-4 修正：三刑只计入"用神自身参与"的刑（branches_present 含用神支）。
    # 卦内其他爻的刑（如无关自刑）属于整体格局，不应扣在用神旺衰分上。
    tp_modifier = 0.0
    tp_issues = []
    advanced_for_tp = r.get("advanced_analysis", {})
    if advanced_for_tp and isinstance(advanced_for_tp, dict):
        tp_data = advanced_for_tp.get("three_punishments", {})
        if isinstance(tp_data, dict) and tp_data.get("has_punishment"):
            for p in tp_data.get("punishments", []):
                bp = p.get("branches_present", [])
                if use_god_branch and use_god_branch not in bp:
                    continue
                tp_modifier += p.get("score", 0.0)
                comp = p.get("completeness", "")
                ptype = p.get("type", "")
                if comp == "待刑":
                    missing = p.get("missing", [])
                    tp_issues.append(f"{ptype}待刑(缺{','.join(missing)})")
                elif comp == "完整":
                    tp_issues.append(f"{ptype}(完整三刑)")
                elif comp == "成刑":
                    tp_issues.append(f"{ptype}(成刑)")
                else:
                    tp_issues.append(ptype)'''

assert OLD_TP in src, "3.10c 段未找到"
src = src.replace(OLD_TP, NEW_TP, 1)

# ---- 2. 伏藏用神也走伏藏特殊评估 ----
OLD_FC = '''    if not selected_use_god:
        # 伏藏用神特殊评估
        if step2_data.get("has_fu_cang"):'''
NEW_FC = '''    if not selected_use_god or selected_use_god.get("is_fu_cang"):
        # 伏藏用神特殊评估（用神伏藏时，旺衰以伏神飞伏关系为主）
        if step2_data.get("has_fu_cang"):'''
assert OLD_FC in src, "伏藏分支入口未找到"
src = src.replace(OLD_FC, NEW_FC, 1)

# ---- 3. 飞空得出：_evaluate_fu_cang_strength 加 empty 参数与飞空加分 ----
OLD_SIG = '''def _evaluate_fu_cang_strength(fu_detail: dict, month_branch: str, day_branch: str) -> dict:'''
NEW_SIG = '''def _evaluate_fu_cang_strength(fu_detail: dict, month_branch: str, day_branch: str, empty_branches: list = None) -> dict:'''
assert OLD_SIG in src, "签名未找到"
src = src.replace(OLD_SIG, NEW_SIG, 1)

OLD_FEI = '''    effective_score += fu_fei_modifier
    if fu_fei_reason:
        analysis_parts.append(fu_fei_reason)

    # ── 5. 能否得出 ──'''
NEW_FEI = '''    effective_score += fu_fei_modifier

    # ── 4b. 飞神旬空（飞空得出）── 伏神得出有力，且免于泄气之扣
    fei_branch_tmp = fei_branch or ""
    if empty_branches and fei_branch_tmp in empty_branches:
        effective_score += 1.0
        analysis_parts.append(f"飞神{fei_branch_tmp}旬空（飞空得出），伏神得出有力，+1.0")
    if fu_fei_reason:
        analysis_parts.append(fu_fei_reason)

    # ── 5. 能否得出 ──'''
assert OLD_FEI in src, "飞伏修正段未找到"
src = src.replace(OLD_FEI, NEW_FEI, 1)

# ---- 4. 调用处传 empty ----
OLD_CALL = '''            fu_score = _evaluate_fu_cang_strength(fu_detail, month_branch, day_branch)'''
NEW_CALL = '''            fu_score = _evaluate_fu_cang_strength(fu_detail, month_branch, day_branch, empty)'''
assert OLD_CALL in src, "调用处未找到"
src = src.replace(OLD_CALL, NEW_CALL, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)

print("OK: step3 三刑过滤 + 伏藏分支 + 飞空得出 已应用")
