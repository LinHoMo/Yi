# -*- coding: utf-8 -*-
"""P0-5d fu_shen_adjustment 加"绝于飞"分支"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''    elif "飞克伏" in step3_reasoning_text:
        # 飞克伏: 需检查飞神是否旬空/月破 → 伏得出为吉'''
NEW = '''    elif "绝于飞" in step3_reasoning_text:
        # 伏神绝于飞神 → 气绝难出（P0-5）
        fu_shen_adjustment = -1.5
        fu_shen_note = "【伏神绝于飞】伏神气绝难出，-1.5"
    elif "飞克伏" in step3_reasoning_text:
        # 飞克伏: 需检查飞神是否旬空/月破 → 伏得出为吉'''

assert OLD in src, "飞克伏分支未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)

print("OK: fu_shen 绝于飞 -1.5")
