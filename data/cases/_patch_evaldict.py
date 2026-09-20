# -*- coding: utf-8 -*-
"""评估词典补：回头生/暗动/伏神/飞空得出"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\data\cases\blind_eval_v4.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''        "化合", "化退神", "旬空", "填实", "出空", "合处逢冲",
    ]'''
NEW = '''        "化合", "化退神", "旬空", "填实", "出空", "合处逢冲",
        "回头生", "暗动", "伏神", "飞空得出",
    ]'''

assert OLD in src, "词典段未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)
print("OK")
