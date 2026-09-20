# -*- coding: utf-8 -*-
"""P0-5 近病逢合为凶优先：用神被月/日合 → 逢合凶（先于逢空即愈）"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''    # --- 近病逢空即愈 ---
    if (is_near_illness or is_illness_div):
        use_void = use_god_branch and use_god_branch in empty_branches
        if use_void or transform_to_void:'''

NEW = '''    # --- 近病逢合为凶（优先于逢空：合则病气难退，《卜筮正宗》"近病逢合为凶"）---
    if (is_near_illness or is_illness_div) and use_god_branch:
        dt6 = hex_result.get("divination_time", {}) or {}
        m_b = (dt6.get("month_stem_branch", "") or "")[1:]
        d_b = (dt6.get("day_stem_branch", "") or "")[1:]
        HE6 = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
               "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
        he_bys = []
        if HE6.get(use_god_branch, "") == m_b:
            he_bys.append(f"月建{m_b}")
        if HE6.get(use_god_branch, "") == d_b:
            he_bys.append(f"日辰{d_b}")
        if he_bys:
            result["pattern"] = "近病逢合为凶"
            result["description"] = f"用神{use_god_branch}为{'、'.join(he_bys)}所合——近病逢合，病气难退（《卜筮正宗》定法）"
            result["impact_on_verdict"] = "用神被合，病气难退，凶"
            result["score_adjustment"] = -3.5
            return result

    # --- 近病逢空即愈 ---
    if (is_near_illness or is_illness_div):
        use_void = use_god_branch and use_god_branch in empty_branches
        if use_void or transform_to_void:'''

assert OLD in src, "逢空段未找到"
src = src.replace(OLD, NEW, 1)

# 函数签名补 hex_result 参数
OLD_SIG = '''def _detect_classical_illness_pattern(question: str, step2_data: dict, step3_data: dict,
                                       empty_branches: list, step4_data: dict = None) -> dict:'''
NEW_SIG = '''def _detect_classical_illness_pattern(question: str, step2_data: dict, step3_data: dict,
                                       empty_branches: list, step4_data: dict = None,
                                       hex_result: dict = None) -> dict:'''
assert OLD_SIG in src, "签名未找到"
src = src.replace(OLD_SIG, NEW_SIG, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)

print("OK: 近病逢合优先已加入")
