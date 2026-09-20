# -*- coding: utf-8 -*-
"""P0-4g 动空（动则生而不为空）：动爻生用神 → 空亡按有气论 + 出旬有验"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''    if is_empty:
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

NEW = '''    if is_empty:
        # 有生源检测（月建/日辰/动爻生用神 → 空亡有气，出旬有验）
        month_births_use = SHENG_CYCLE.get(month_element) == use_god_element
        day_births_use = SHENG_CYCLE.get(day_element) == use_god_element
        # 动爻生用神 → "动则生而不为空"（《增删易》动空出旬）
        moving_births_use = False
        for yao in yao_lines:
            if yao.get("is_moving"):
                y_elem = _branch_element(yao.get("earthly_branch", ""))
                if SHENG_CYCLE.get(y_elem) == use_god_element:
                    moving_births_use = True
                    break
        if god_month_score >= 4 or moving_births_use:
            empty_modifier = 0.7  # 有气论
            if moving_births_use:
                empty_modifier_reason = "用神旬空但得动爻生之（动空），出旬即应，论70%"
            else:
                empty_modifier_reason = "用神旺相旬空，论70%（有气空亡，出空可应）"
            if month_births_use or day_births_use or moving_births_use:
                chu_xun_bonus = 1.0
                chu_xun_reason = "用神旬空有气且得生扶（月/日/动爻），出旬有验，断吉倾向"
        else:
            empty_modifier = 0.3  # 休囚论
            empty_modifier_reason = "用神休囚旬空，论30%（真空亡，难应）"'''

assert OLD in src, "空亡段未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)

print("OK: 动空逻辑已加入")
