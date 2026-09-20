# -*- coding: utf-8 -*-
"""P0-4b 伏克飞为出暴：伏神有力反克飞神 → 得出（ZS016 午火克酉金）"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\classical_analysis.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''    # 5. 飞神休囚
    cov_strength = element_strength_in_month(cov_elem, month_elem)
    if cov_strength in ("休", "囚", "死"):
        emerge_score += 1
        reasons.append(f"飞神{cov_strength}")

    # --- 不得出条件 ---'''

NEW = '''    # 5. 飞神休囚
    cov_strength = element_strength_in_month(cov_elem, month_elem)
    if cov_strength in ("休", "囚", "死"):
        emerge_score += 1
        reasons.append(f"飞神{cov_strength}")

    # 6. 伏克飞为出暴（伏神有力反克飞神，出暴为吉）
    if KE_CYCLE.get(hid_elem) == cov_elem:
        emerge_score += 3
        reasons.append("伏克飞为出暴")

    # --- 不得出条件 ---'''

assert OLD in src, "伏藏评估段未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)

print("OK: 伏克飞出暴 已加入")
