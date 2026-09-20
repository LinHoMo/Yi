# -*- coding: utf-8 -*-
"""P0-8a 旬空填实：日辰冲用神 → 文本补"逢日辰冲为填实"（ZS001）"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''            if month_births_use or day_births_use or moving_births_use:
                chu_xun_bonus = 1.0
                chu_xun_reason = "用神旬空有气且得生扶（月/日/动爻），出旬有验，断吉倾向"'''
NEW = '''            # 日辰冲用神 → 旬空逢冲为填实（《卜筮正宗》冲空则实）
            day_clashes_use = bool(day_branch) and _is_chong(use_god_branch, day_branch)
            if day_clashes_use:
                empty_modifier_reason = "用神旺相旬空，逢日辰冲为填实（冲空则实，出空即应），论70%"
            if month_births_use or day_births_use or moving_births_use:
                chu_xun_bonus = 1.0
                chu_xun_reason = "用神旬空有气且得生扶（月/日/动爻），出旬有验，断吉倾向"'''

assert OLD in src, "出旬段未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)
print("OK")
