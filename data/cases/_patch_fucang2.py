# -*- coding: utf-8 -*-
"""P0-4c thinking_chain 伏克飞出暴 +0.8"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''        else:
            # 伏克飞
            fu_fei_reason = f"伏神{fu_element}克飞神{fei_element}（伏制飞），无修正"'''

NEW = '''        elif KE_CYCLE.get(fu_element) == fei_element:
            # 伏克飞为出暴（伏神有力反克飞神，出暴主吉）
            fu_fei_modifier = 0.8
            fu_fei_reason = f"伏神{fu_element}克飞神{fei_element}（伏克飞为出暴），伏有力得出，+0.8"
        else:
            fu_fei_reason = f"伏神{fu_element}与飞神{fei_element}关系无显著生克，无修正"'''

assert OLD in src, "伏克飞段未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)

print("OK: thinking_chain 伏克飞出暴 +0.8")
