# -*- coding: utf-8 -*-
"""P1 出旬有验：用神旬空 + 月/日得生 → 出旬应验加分（《增删易》）"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

# ---- 1. 空亡分支增加"有生源"检测 ----
OLD_EMPTY = '''    if is_empty:
        if god_month_score >= 4:  # 旺或相
            empty_modifier = 0.7  # 有气论
            empty_modifier_reason = "用神旺相旬空，论70%（有气空亡，出空可应）"
        else:
            empty_modifier = 0.3  # 休囚论
            empty_modifier_reason = "用神休囚旬空，论30%（真空亡，难应）"'''

NEW_EMPTY = '''    chu_xun_bonus = 0.0
    chu_xun_reason = ""
    if is_empty:
        # 有生源检测（月建或日辰生用神 → 空亡有气，出旬有验）
        month_births_use = SHENG_CYCLE.get(month_element) == use_god_element
        day_births_use = SHENG_CYCLE.get(day_element) == use_god_element
        if god_month_score >= 4:  # 旺或相
            empty_modifier = 0.7  # 有气论
            empty_modifier_reason = "用神旺相旬空，论70%（有气空亡，出空可应）"
            if month_births_use or day_births_use:
                chu_xun_bonus = 1.0
                chu_xun_reason = "用神旬空有气且得月/日生扶，出旬有验，断吉倾向"
        else:
            empty_modifier = 0.3  # 休囚论
            empty_modifier_reason = "用神休囚旬空，论30%（真空亡，难应）"'''

assert OLD_EMPTY in src, "空亡分支未找到"
src = src.replace(OLD_EMPTY, NEW_EMPTY, 1)

# ---- 2. effective_score 汇总后加分 ----
OLD_EFF = '''    effective_score = adjusted_score * empty_modifier * month_break_modifier
    if is_an_dong:
        effective_score *= an_dong_modifier
    # 加上十二长生修正
    effective_score += twelve_growth_modifier'''

NEW_EFF = '''    effective_score = adjusted_score * empty_modifier * month_break_modifier
    if chu_xun_bonus != 0.0:
        effective_score += chu_xun_bonus
    if is_an_dong:
        effective_score *= an_dong_modifier
    # 加上十二长生修正
    effective_score += twelve_growth_modifier'''

assert OLD_EFF in src, "effective_score 汇总未找到"
src = src.replace(OLD_EFF, NEW_EFF, 1)

# ---- 3. modifiers 列表加入口 ----
OLD_MODS = '''    if is_empty:
        modifiers.append({"type": "旬空", "value": empty_modifier, "reason": empty_modifier_reason})'''

NEW_MODS = '''    if chu_xun_bonus != 0.0:
        modifiers.append({"type": "出旬有验", "value": chu_xun_bonus, "reason": chu_xun_reason})
    if is_empty:
        modifiers.append({"type": "旬空", "value": empty_modifier, "reason": empty_modifier_reason})'''

assert OLD_MODS in src, "modifiers 旬空入口未找到"
src = src.replace(OLD_MODS, NEW_MODS, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)

print("OK: 出旬有验已实现")
