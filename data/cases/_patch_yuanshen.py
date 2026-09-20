# -*- coding: utf-8 -*-
"""P0-4h 原神发动生用神 → +1.0（ZS005 午火生戌土）"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''        else:
            # 原神动（不论化什么都有一定助用效果）
            score = 0.3
            description_parts.append("原神动，有生用之心")'''

NEW = '''        else:
            # 原神动（不论化什么都有一定助用效果）
            # 原神五行生用神 → 生用有力（《增删易》"原神发动，生用有力"）
            if SHENG_CYCLE.get(orig_element) == use_god_element:
                score = 1.0
                description_parts.append("原神发动，其五行生用神，生用有力")
            else:
                score = 0.3
                description_parts.append("原神动，有生用之心")'''

assert OLD in src, "原神 else 段未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)

print("OK: 原神生用 +1.0 已加入")
