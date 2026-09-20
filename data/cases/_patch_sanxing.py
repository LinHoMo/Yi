# -*- coding: utf-8 -*-
"""P0-1 三刑规则修正：变卦不参与本卦三刑；卦内齐备才-1.0；月日催刑降权"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\classical_analysis.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

# ---- 1. 替换"收集所有地支及其来源"段：分离卦内/外部（月日），剔除变卦 ----
OLD_COLLECT = '''    # ── 收集所有地支及其来源 ──
    branches_with_source = []
    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        if branch:
            branches_with_source.append((branch, f"爻{_pos_to_name(yao['position'])}"))

    # 加入月建和日辰
    if month_branch:
        branches_with_source.append((month_branch, f"月建({month_branch})"))
    if day_branch:
        branches_with_source.append((day_branch, f"日辰({day_branch})"))

    # 变卦地支也纳入
    changed = result.get("changed_hexagram") or {}
    changed_name = changed.get("name")
    if changed_name:
        for pos in range(1, 7):
            chg_branch = get_changed_hexagram_branch(changed_name, pos)
            if chg_branch:
                branches_with_source.append(
                    (chg_branch, f"变{_pos_to_name(pos)}({chg_branch})")
                )

    # ── 建立全量地支集合（用于完整性判断）──
    all_branches_set = set(b for b, _ in branches_with_source)

    # ── 辅助：从 branches_with_source 中找出指定地支的所有来源位置 ──
    def _find_sources(branchesNeeded):
        return [(b, s) for b, s in branches_with_source if b in branchesNeeded]'''

NEW_COLLECT = '''    # ── 收集所有地支及其来源 ──
    # 三刑口径（P0-1 修正）：
    #   1) 以本卦六爻为主（hex_branches）；
    #   2) 月建/日辰仅作"催刑"（external_branches），参与补足但不按完整三刑计；
    #   3) 变卦地支不参与本卦三刑（化出之爻不构成原局刑伤）。
    hex_branches = []
    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        if branch:
            hex_branches.append((branch, f"爻{_pos_to_name(yao['position'])}"))

    external_branches = []
    if month_branch:
        external_branches.append((month_branch, f"月建({month_branch})"))
    if day_branch:
        external_branches.append((day_branch, f"日辰({day_branch})"))

    branches_with_source = hex_branches + external_branches

    # ── 建立全量地支集合（用于完整性判断）──
    all_branches_set = set(b for b, _ in branches_with_source)
    hex_set = set(b for b, _ in hex_branches)

    # ── 辅助：从 branches_with_source 中找出指定地支的所有来源位置 ──
    def _find_sources(branchesNeeded):
        return [(b, s) for b, s in branches_with_source if b in branchesNeeded]'''

assert OLD_COLLECT in src, "收集段未找到"
src = src.replace(OLD_COLLECT, NEW_COLLECT, 1)

# ---- 2. 替换循环刑判定段：分层计分 ----
OLD_CYCLIC = '''        if len(present_set) == 3:
            # 完整三刑 — 极凶
            sources = _find_sources(set(required))
            pos_list = list(dict.fromkeys(s for _, s in sources))  # deduplicated, keep order
            punishments.append({
                "type": ptype,
                "completeness": "完整",
                "branches_present": present,
                "missing": [],
                "formed_by": "卦内",
                "positions": pos_list,
                "description": (
                    f"{ptype}（完整三刑）：{present[0]}刑{present[1]}刑{present[2]}，"
                    f"三字全见于{ '、'.join(pos_list) }，极凶之象"
                ),
            })
            total_score -= 1.0
        elif len(present_set) == 2:
            # 待刑 — 需月日补齐
            sources = _find_sources(present_set)
            pos_list = list(dict.fromkeys(s for _, s in sources))
            punishments.append({
                "type": ptype,
                "completeness": "待刑",
                "branches_present": present,
                "missing": missing,
                "formed_by": "待月日补齐",
                "positions": pos_list,
                "description": (
                    f"{ptype}（待刑）：{present[0]}、{present[1]}相见，"
                    f"缺{missing[0]}，待月日逢{missing[0]}方成刑，"
                    f"目前刑伤未全，但有刑伤之象"
                ),
            })
            total_score -= 0.3
        # len == 0 or 1: 不构成任何刑'''

NEW_CYCLIC = '''        present_hex_cnt = len(hex_set & required_set)
        if present_hex_cnt == 3:
            # 卦内三字齐备 — 完整三刑，极凶
            sources = _find_sources(set(required))
            pos_list = list(dict.fromkeys(s for _, s in sources))  # deduplicated, keep order
            punishments.append({
                "type": ptype,
                "completeness": "完整",
                "branches_present": present,
                "missing": [],
                "formed_by": "卦内",
                "positions": pos_list,
                "description": (
                    f"{ptype}（完整三刑）：{present[0]}刑{present[1]}刑{present[2]}，"
                    f"三字全见于{ '、'.join(pos_list) }，极凶之象"
                ),
            })
            total_score -= 1.0
        elif len(present_set) == 3:
            # 卦内二字 + 月日补足一字 — 催刑（月日催成，力减半）
            sources = _find_sources(set(required))
            pos_list = list(dict.fromkeys(s for _, s in sources))
            punishments.append({
                "type": ptype,
                "completeness": "催刑",
                "branches_present": present,
                "missing": [],
                "formed_by": "卦内为主，月日催刑",
                "positions": pos_list,
                "description": (
                    f"{ptype}（催刑）：卦内{ '、'.join(p for p in present if p in hex_set) or '无'}，"
                    f"月日{ '、'.join(p for p in present if p not in hex_set) }补足成刑，"
                    f"刑伤力减半"
                ),
            })
            total_score -= 0.5
        elif len(present_set) == 2:
            # 待刑 — 需月日补齐
            sources = _find_sources(present_set)
            pos_list = list(dict.fromkeys(s for _, s in sources))
            punishments.append({
                "type": ptype,
                "completeness": "待刑",
                "branches_present": present,
                "missing": missing,
                "formed_by": "待月日补齐",
                "positions": pos_list,
                "description": (
                    f"{ptype}（待刑）：{present[0]}、{present[1]}相见，"
                    f"缺{missing[0]}，待月日逢{missing[0]}方成刑，"
                    f"目前刑伤未全，但有刑伤之象"
                ),
            })
            total_score -= 0.3
        # 卦内及月日合计不足两字: 不构成任何刑'''

assert OLD_CYCLIC in src, "循环刑段未找到"
src = src.replace(OLD_CYCLIC, NEW_CYCLIC, 1)

# ---- 3. 无礼之刑：卦内两字成刑，卦内一+月日一为待刑 ----
OLD_MUTUAL = '''    # ── 2. 互刑（无礼之刑子卯）：两字相见即成刑 ──
    b1_key, b2_key = THREE_PUNISHMENTS_MUTUAL["无礼之刑"]
    if b1_key in all_branches_set and b2_key in all_branches_set:
        sources = _find_sources({b1_key, b2_key})
        pos_list = list(dict.fromkeys(s for _, s in sources))
        punishments.append({
            "type": "无礼之刑",
            "completeness": "成刑",
            "branches_present": [b1_key, b2_key],
            "missing": [],
            "formed_by": "卦内",
            "positions": pos_list,
            "description": (
                f"无礼之刑（成刑）：{b1_key}刑{b2_key}，"
                f"见于{ '、'.join(pos_list) }，主无礼刑伤、恩中之怨"
            ),
        })
        total_score -= 0.5'''

NEW_MUTUAL = '''    # ── 2. 互刑（无礼之刑子卯）：卦内两字成刑；卦内一+月日一为待刑 ──
    b1_key, b2_key = THREE_PUNISHMENTS_MUTUAL["无礼之刑"]
    in_hex = (b1_key in hex_set and b2_key in hex_set)
    in_all = (b1_key in all_branches_set and b2_key in all_branches_set)
    if in_all:
        sources = _find_sources({b1_key, b2_key})
        pos_list = list(dict.fromkeys(s for _, s in sources))
        if in_hex:
            punishments.append({
                "type": "无礼之刑",
                "completeness": "成刑",
                "branches_present": [b1_key, b2_key],
                "missing": [],
                "formed_by": "卦内",
                "positions": pos_list,
                "description": (
                    f"无礼之刑（成刑）：{b1_key}刑{b2_key}，"
                    f"见于{ '、'.join(pos_list) }，主无礼刑伤、恩中之怨"
                ),
            })
            total_score -= 0.5
        else:
            punishments.append({
                "type": "无礼之刑",
                "completeness": "待刑",
                "branches_present": [b1_key, b2_key],
                "missing": [],
                "formed_by": "卦内为主，月日催刑",
                "positions": pos_list,
                "description": (
                    f"无礼之刑（待刑）：{b1_key}、{b2_key}月日相见，"
                    f"刑伤未全，主微咎"
                ),
            })
            total_score -= 0.3'''

assert OLD_MUTUAL in src, "无礼之刑段未找到"
src = src.replace(OLD_MUTUAL, NEW_MUTUAL, 1)

# ---- 4. 自刑：仅统计卦内同支 ----
OLD_SELF = '''    # ── 3. 自刑（辰午酉亥）：同一地支出现两次以上 ──
    from collections import Counter
    branch_counts = Counter(b for b, _ in branches_with_source)
    for sp_branch in SELF_PUNISHMENTS:
        count = branch_counts.get(sp_branch, 0)
        if count >= 2:
            sources = _find_sources({sp_branch})
            pos_list = list(dict.fromkeys(s for _, s in sources))
            punishments.append({
                "type": "自刑",
                "completeness": "完整",
                "branches_present": [sp_branch],
                "missing": [],
                "formed_by": "卦内",
                "positions": pos_list,
                "description": (
                    f"自刑：{sp_branch}出现{count}次"
                    f"（{ '、'.join(pos_list) }），"
                    f"自刑主自我纠结、自作自受、内心矛盾"
                ),
            })
            total_score -= 0.3 * (count - 1)  # 每多一次减0.3'''

NEW_SELF = '''    # ── 3. 自刑（辰午酉亥）：仅卦内同一地支两次以上 ──
    from collections import Counter
    hex_branch_counts = Counter(b for b, _ in hex_branches)
    for sp_branch in SELF_PUNISHMENTS:
        count = hex_branch_counts.get(sp_branch, 0)
        if count >= 2:
            sources = _find_sources({sp_branch})
            pos_list = list(dict.fromkeys(s for _, s in sources))
            punishments.append({
                "type": "自刑",
                "completeness": "完整",
                "branches_present": [sp_branch],
                "missing": [],
                "formed_by": "卦内",
                "positions": pos_list,
                "description": (
                    f"自刑：{sp_branch}出现{count}次"
                    f"（{ '、'.join(pos_list) }），"
                    f"自刑主自我纠结、自作自受、内心矛盾"
                ),
            })
            total_score -= 0.3 * (count - 1)  # 每多一次减0.3'''

assert OLD_SELF in src, "自刑段未找到"
src = src.replace(OLD_SELF, NEW_SELF, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)

print("OK: analyze_three_punishments 三刑口径已修正")
