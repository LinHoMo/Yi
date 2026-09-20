# -*- coding: utf-8 -*-
"""P0-3 两现用神修复：不剔除空破候选；优先级重排（动>填实>应>世>月>日>空破>位）"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

# ---- 1. _find_use_god_positions：不再剔除空破/临月候选 ----
OLD_FILTER = '''    # 用神筛选规则（《卜筮正宗》）
    if len(positions) > 1:
        # 规则1：舍静取动
        moving = [p for p in positions if p["is_moving"]]
        if moving:
            for p in moving:
                p["reason"] += "取动爻；"
            positions = moving

        # 规则2：舍空破取旺相
        not_empty = [p for p in positions if not p["is_empty"] and not p["is_month_break"]]
        if not_empty:
            for p in not_empty:
                p["reason"] += "舍空破取旺相；"
            positions = not_empty

        # 规则3：取临月建者
        at_month = [p for p in positions if p["is_at_month"]]
        if at_month:
            for p in at_month:
                p["reason"] += "取临月建；"
            positions = at_month

    return positions'''

NEW_FILTER = '''    # 用神筛选（《卜筮正宗》）：只做"舍静取动"，其余候选保留给排序层统一决策。
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

assert OLD_FILTER in src, "筛选段未找到"
src = src.replace(OLD_FILTER, NEW_FILTER, 1)

# ---- 2. _use_god_priority 重排 ----
OLD_PRIO = '''    def _use_god_priority(pos_info):
        p = pos_info.get("position", 99)
        if p == response_position:
            return 0
        if p == world_position:
            return 1
        if pos_info.get("is_moving"):
            return 2
        if pos_info.get("is_at_month"):
            return 3
        if pos_info.get("is_at_day"):
            return 4
        return 5 + p'''

NEW_PRIO = '''    def _use_god_priority(pos_info):
        p = pos_info.get("position", 99)
        brk = pos_info.get("earthly_branch", "")
        # 0 明动有力（动而不空，事之主）
        if pos_info.get("is_moving") and not pos_info.get("is_empty"):
            return 0
        # 1 旬空逢日冲填实（空亡反被激活）
        if pos_info.get("is_empty") and _is_chong(brk, day_branch):
            return 1
        # 2 静爻逢日冲暗动（非空，旺相者力强）
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

assert OLD_PRIO in src, "优先级函数未找到"
src = src.replace(OLD_PRIO, NEW_PRIO, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)

print("OK: 两现用神规则已修复")
