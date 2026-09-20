# -*- coding: utf-8 -*-
"""P0-5b 近病逢合仅限静爻：动爻逢合为合起（ZS007 亥动化空 → 逢空即愈）"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''    # --- 近病逢合为凶（优先于逢空：合则病气难退，《卜筮正宗》"近病逢合为凶"）---
    if (is_near_illness or is_illness_div) and use_god_branch:
        dt6 = hex_result.get("divination_time", {}) or {}'''
NEW = '''    # --- 近病逢合为凶（优先于逢空：合则病气难退，《卜筮正宗》"近病逢合为凶"）---
    # 仅限用神为静爻时——动爻逢合为"合起"（合而发动），不构成合绊；
    # 静爻逢合方为"合绊"（病气难退）。
    use_god_moving = use_god.get("is_moving", False) or any(
        yl.get("is_moving") for yl in
        (step2_data.get("use_god_yao_lines") or step2_data.get("use_god_positions") or [])
        if isinstance(yl, dict) and yl.get("earthly_branch") == use_god_branch
    )
    if (is_near_illness or is_illness_div) and use_god_branch and not use_god_moving:
        dt6 = hex_result.get("divination_time", {}) or {}'''

assert OLD in src, "逢合优先块未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)

print("OK: 近病逢合限静爻")
