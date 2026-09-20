# -*- coding: utf-8 -*-
"""P0-5c 伏神绝于飞神 -1.0（日辰冲伏神者豁免——ZS003 得拔，ZS015 气绝）"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''    if fei_element:
        if SHENG_CYCLE.get(fei_element) == fu_element:  # 飞生伏
            fu_fei_modifier = 0.5
            fu_fei_reason = f"飞神{fei_element}生伏神{fu_element}（飞生伏），伏得出，+0.5"'''
NEW = '''    if fei_element:
        # 伏神绝于飞神地支 → 伏神气绝难出（《卜筮正宗》十二长生绝地）；
        # 但日辰冲伏神者为"冲空则实/拔伏"，豁免（ZS003 子冲午得拔）。
        fei_growth = _twelve_growth_at_day(fu_element, fei_branch)
        day_chongs_fu = _is_chong(fu_branch, day_branch)
        if fei_growth == "绝" and not day_chongs_fu:
            fu_fei_modifier = -1.0
            fu_fei_reason = f"伏神{fu_element}绝于飞神{fei_branch}（{fei_growth}），伏神气绝难出，-1.0"
        elif SHENG_CYCLE.get(fei_element) == fu_element:  # 飞生伏
            fu_fei_modifier = 0.5
            fu_fei_reason = f"飞神{fei_element}生伏神{fu_element}（飞生伏），伏得出，+0.5"'''

assert OLD in src, "飞生伏段未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)

print("OK: 伏神绝于飞神 -1.0 已加入")
