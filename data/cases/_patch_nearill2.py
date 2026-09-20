# -*- coding: utf-8 -*-
"""近病逢合 -3.5 → -5.5（优先块）"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''            result["impact_on_verdict"] = "用神被合，病气难退，凶"
            result["score_adjustment"] = -3.5
            return result

    # --- 近病逢空即愈 ---'''
NEW = '''            result["impact_on_verdict"] = "用神被合，病气难退，凶"
            result["score_adjustment"] = -5.5
            return result

    # --- 近病逢空即愈 ---'''

assert OLD in src, "优先块未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)
print("OK: 近病逢合 -5.5")
