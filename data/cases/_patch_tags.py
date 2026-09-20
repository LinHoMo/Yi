# -*- coding: utf-8 -*-
"""P0-6 格局标签补疾厄类：近病逢空/近病逢合/久病"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''        elif special.get("pattern") == "归魂":
            tags.append("格局-归魂")
        
        # 随官入墓'''
NEW = '''        elif special.get("pattern") == "归魂":
            tags.append("格局-归魂")
        elif special.get("pattern") == "近病逢空即愈":
            tags.append("格局-近病逢空即愈")
        elif special.get("pattern") == "近病逢合为凶":
            tags.append("格局-近病逢合为凶")
        elif special.get("pattern") == "久病逢空为凶":
            tags.append("格局-久病逢空为凶")
        elif special.get("pattern") == "久病逢冲为凶":
            tags.append("格局-久病逢冲为凶")
        
        # 随官入墓'''

assert OLD in src, "归魂段未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)

print("OK: 疾厄格局标签已加")
