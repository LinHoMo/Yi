# -*- coding: utf-8 -*-
"""P0-3b 优先级升级：暗动优先 + 动而空降级"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''    def _use_god_priority(pos_info):
        p = pos_info.get("position", 99)
        # 0 动爻优先（事之主）
        if pos_info.get("is_moving"):
            return 0
        # 1 旬空逢日冲填实（空亡反被激活，最有力）
        brk = pos_info.get("earthly_branch", "")
        if pos_info.get("is_empty") and _is_chong(brk, day_branch):
            return 1
        # 2 应爻位置（占婚/占失等古籍断法）
        if p == response_position:
            return 2
        # 3 世爻位置
        if p == world_position:
            return 3
        # 4 临月建
        if pos_info.get("is_at_month"):
            return 4
        # 5 临日辰
        if pos_info.get("is_at_day"):
            return 5
        # 6 普通旬空/月破（降级但不剔除）
        if pos_info.get("is_empty") or pos_info.get("is_month_break"):
            return 6
        return 7 + p'''

NEW = '''    def _use_god_priority(pos_info):
        p = pos_info.get("position", 99)
        brk = pos_info.get("earthly_branch", "")
        # 0 明动有力（动而不空，事之主）
        if pos_info.get("is_moving") and not pos_info.get("is_empty"):
            return 0
        # 1 旬空逢日冲填实（空亡反被激活）
        if pos_info.get("is_empty") and _is_chong(brk, day_branch):
            return 1
        # 2 静爻逢日冲暗动（非空，旺相者力强，《增删易》重动轻静）
        if (not pos_info.get("is_moving")) and (not pos_info.get("is_empty")) and _is_chong(brk, day_branch):
            return 2
        # 3 应爻位置（占婚/占失等古籍断法）
        if p == response_position:
            return 3
        # 4 世爻位置
        if p == world_position:
            return 4
        # 5 临月建
        if pos_info.get("is_at_month"):
            return 5
        # 6 临日辰
        if pos_info.get("is_at_day"):
            return 6
        # 7 动而空（明动但旬空，须出空方应）及普通空破
        if pos_info.get("is_moving") or pos_info.get("is_empty") or pos_info.get("is_month_break"):
            return 7
        return 8 + p'''

assert OLD in src, "优先级函数未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)

print("OK: 优先级已升级（暗动优先、动而空降级）")
