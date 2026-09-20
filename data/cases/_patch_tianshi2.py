# -*- coding: utf-8 -*-
"""修复 P0-8a 变量名：use_god_branch → selected_use_god"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''            # 日辰冲用神 → 旬空逢冲为填实（《卜筮正宗》冲空则实）
            day_clashes_use = bool(day_branch) and _is_chong(use_god_branch, day_branch)'''
NEW = '''            # 日辰冲用神 → 旬空逢冲为填实（《卜筮正宗》冲空则实）
            _ugb = (selected_use_god or {}).get("earthly_branch", "")
            day_clashes_use = bool(day_branch) and bool(_ugb) and _is_chong(_ugb, day_branch)'''

assert OLD in src, "填实段未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)
print("OK")
