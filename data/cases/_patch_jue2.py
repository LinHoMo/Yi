# -*- coding: utf-8 -*-
"""绝于飞 -1.5 → -2.0"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''        fu_shen_adjustment = -1.5
        fu_shen_note = "【伏神绝于飞】伏神气绝难出，-1.5"'''
NEW = '''        fu_shen_adjustment = -2.0
        fu_shen_note = "【伏神绝于飞】伏神气绝难出，-2.0"'''

assert OLD in src, "绝于飞段未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)
print("OK")
