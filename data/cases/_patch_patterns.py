# -*- coding: utf-8 -*-
"""P0-4a 冲中逢合/合处逢冲 修复：月日合世应检测 + 世应取法修正 + 拼接bug"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

# ---- 1. 修复六冲列表拼接 bug ----
OLD_LIST = '''    is_chong = "六冲" in hex_type or hex_name in ("乾", "坤", "坎", "离", "震", "巽", "艮", "兑", "无妄", "大壮", "遁", "否" "晋", "萃", "夬", "姤", "解", "鼎", "归妹", "旅", "涣", "小过", "贲")'''
NEW_LIST = '''    is_chong = "六冲" in hex_type or hex_name in ("乾", "坤", "坎", "离", "震", "巽", "艮", "兑", "无妄", "大壮", "遁", "否", "晋", "萃", "夬", "姤", "解", "鼎", "归妹", "旅", "涣", "小过", "贲")'''
assert OLD_LIST in src, "六冲列表未找到"
src = src.replace(OLD_LIST, NEW_LIST, 1)

# ---- 2. 重写冲中逢合分支（真正检测月/日合世应） ----
OLD_CHONG = '''    # --- 冲中逢合可解 ---
    if is_chong:
        # Check if day/month combines world or response
        # Look for harmony opportunities in step4 changes
        details = step4_data.get("details", []) if step4_data else []
        moving_lines = [d for d in details if "化合" in d.get("change_type", "") or "六合" in d.get("change_type", "")]

        # Also check if day combines something
        div_time = hex_result.get("divination_time", {}) or {}
        day_branch = div_time.get("day_branch", "")

        if moving_lines or any(kw in q for kw in ["冲", "合", "冲中"]):
            result["pattern"] = "冲中逢合可解"
            result["description"] = "六冲本主散，然有日辰/动爻相合，冲中逢合可解"
            result["impact_on_verdict"] = "冲处逢合可解冲散，转危为安"
            result["score_adjustment"] = 2.5
            return result'''

NEW_CHONG = '''    # --- 冲中逢合可解 ---
    if is_chong:
        div_time = hex_result.get("divination_time", {}) or {}
        month_branch = (div_time.get("month_stem_branch", "") or "")[1:]
        day_branch = (div_time.get("day_stem_branch", "") or "")[1:]
        # 世应爻地支（从爻标志取，original_hexagram 无 world_position 字段）
        yao_lines = hex_result.get("original_hexagram", {}).get("yao_lines", [])
        world_branch = ""
        response_branch = ""
        for y in yao_lines:
            if y.get("is_world"):
                world_branch = y.get("earthly_branch", "")
            if y.get("is_response"):
                response_branch = y.get("earthly_branch", "")
        # 六合：子丑 寅亥 卯戌 辰酉 巳申 午未
        HE_MAP = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
                  "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
        world_he = world_branch and (HE_MAP.get(world_branch, "") in [month_branch, day_branch])
        response_he = response_branch and (HE_MAP.get(response_branch, "") in [month_branch, day_branch])
        # 动爻化合（化出之爻与月日成合）也可解冲
        details = step4_data.get("details", []) if step4_data else []
        moving_he = any("化合" in d.get("change_type", "") or "六合" in d.get("change_type", "") for d in details)

        if world_he or response_he or moving_he:
            he_target = "世爻" if world_he else ("应爻" if response_he else "动爻")
            result["pattern"] = "冲中逢合可解"
            result["description"] = f"六冲本主散，然月日/动爻合{he_target}（{'世' if world_he else ''}{'应' if response_he else ''}），冲中逢合可解"
            result["impact_on_verdict"] = "冲处逢合可解冲散，转危为安"
            result["score_adjustment"] = 2.5
            return result'''

assert OLD_CHONG in src, "冲中逢合分支未找到"
src = src.replace(OLD_CHONG, NEW_CHONG, 1)

# ---- 3. 合处逢冲分支：修正世应取法与月日支来源 ----
OLD_HE = '''    # --- 合处逢冲则散 ---
    if is_he:
        div_time = hex_result.get("divination_time", {}) or {}
        month_branch = div_time.get("month_branch", "")
        day_branch = div_time.get("day_branch", "")
        world_branch = ""
        response_branch = ""

        yao_lines = hex_result.get("original_hexagram", {}).get("yao_lines", [])
        world_pos = hex_result.get("original_hexagram", {}).get("world_position", 4)
        response_pos = hex_result.get("original_hexagram", {}).get("response_position", 1)
        for y in yao_lines:
            if y.get("position") == world_pos:
                world_branch = y.get("earthly_branch", "")
            if y.get("position") == response_pos:
                response_branch = y.get("earthly_branch", "")'''

NEW_HE = '''    # --- 合处逢冲则散 ---
    if is_he:
        div_time = hex_result.get("divination_time", {}) or {}
        month_branch = (div_time.get("month_stem_branch", "") or "")[1:]
        day_branch = (div_time.get("day_stem_branch", "") or "")[1:]
        world_branch = ""
        response_branch = ""

        yao_lines = hex_result.get("original_hexagram", {}).get("yao_lines", [])
        for y in yao_lines:
            if y.get("is_world"):
                world_branch = y.get("earthly_branch", "")
            if y.get("is_response"):
                response_branch = y.get("earthly_branch", "")'''

assert OLD_HE in src, "合处逢冲分支未找到"
src = src.replace(OLD_HE, NEW_HE, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)

print("OK: 冲中逢合/合处逢冲 已修复")
