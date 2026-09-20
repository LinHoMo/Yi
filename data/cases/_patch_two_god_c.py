# -*- coding: utf-8 -*-
"""P0-3c _find_use_god_positions 不预过滤：全部候选交排序层"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''    # 用神筛选（《卜筮正宗》）：只做"舍静取动"，其余候选保留给排序层统一决策。
    # 说明（P0-3 修正）：旬空/月破的用神不可一刀切剔除——
    #   1) 旬空逢日冲则"填实"有力（《增删易》）；
    #   2) 应位/世位用神在古籍断法中权重极高；
    #   3) 空亡用神出旬应事亦为常法。
    if len(positions) > 1:
        # 规则1：舍静取动（动爻为事之主）
        moving = [p for p in positions if p["is_moving"]]
        if moving:
            for p in moving:
                p["reason"] += "取动爻；"
            positions = moving

    return positions'''

NEW = '''    # 用神筛选（《卜筮正宗》）：不做任何预过滤，全部候选交排序层统一决策。
    # 说明（P0-3 修正）：
    #   1) 旬空逢日冲则"填实"有力，动而空须出空方应——空亡候选不可剔除；
    #   2) 静爻逢日冲为暗动（《增删易》重动轻静），可能优于明动而空的候选；
    #   3) 应位/世位用神在古籍断法中权重极高。
    return positions'''

assert OLD in src, "筛选段未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)

print("OK: 候选不再预过滤")
