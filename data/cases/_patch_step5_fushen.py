# -*- coding: utf-8 -*-
"""P0-4f step5：飞空得出 +1.5 优先；疾病占随官入墓凶力减半"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

# ---- 1. fu_shen_adjustment：飞空得出优先 ----
OLD_FS = '''    # ---------- 伏神格局调整 ----------
    step3_reasoning_text = step3_data.get("summary_text", "") if step3_data else ""
    fu_shen_adjustment = 0.0
    fu_shen_note = ""
    if "飞来生伏" in step3_reasoning_text or "飞生伏" in step3_reasoning_text:'''
NEW_FS = '''    # ---------- 伏神格局调整 ----------
    step3_reasoning_text = step3_data.get("summary_text", "") if step3_data else ""
    fu_shen_adjustment = 0.0
    fu_shen_note = ""
    if "飞空得出" in step3_reasoning_text or ("飞神" in step3_reasoning_text and "旬空" in step3_reasoning_text and "得出" in step3_reasoning_text):
        # 飞神旬空 → 伏神得出有力（P0-4 新增，优先于泄气/克伏等次级关系）
        fu_shen_adjustment = 1.5
        fu_shen_note = "【飞空得出】飞神旬空，伏神得出有力，+1.5"
    elif "飞来生伏" in step3_reasoning_text or "飞生伏" in step3_reasoning_text:'''
assert OLD_FS in src, "伏神格局段未找到"
src = src.replace(OLD_FS, NEW_FS, 1)

# ---- 2. 疾病占随官入墓减半 ----
OLD_OT = '''            # catastrophic severity: force verdict to at most 平凶 regardless of score
            if officer_tomb_severity == "catastrophic":
                officer_tomb_verdict_override = "凶"
            # severe: cap at 平凶 if current score would indicate better
            elif officer_tomb_severity == "severe":
                officer_tomb_verdict_override = None  # let score adjust naturally but log'''
NEW_OT = '''            # catastrophic severity: force verdict to at most 平凶 regardless of score
            if officer_tomb_severity == "catastrophic":
                officer_tomb_verdict_override = "凶"
            # severe: cap at 平凶 if current score would indicate better
            elif officer_tomb_severity == "severe":
                officer_tomb_verdict_override = None  # let score adjust naturally but log

            # 疾病占修正（P0-4）：官鬼=病气，入墓为收藏之象，凶力大减
            q_txt = r.get("question", "") or ""
            if any(kw in q_txt for kw in ["病", "疾", "痛", "恙", "染"]):
                officer_tomb_adjustment = round(officer_tomb_adjustment * 0.3, 2)
                officer_tomb_severity = "mild"
                officer_tomb_description += "（疾病占：官鬼病气入墓为收藏之象，凶力大减）"'''
assert OLD_OT in src, "随官入墓段未找到"
src = src.replace(OLD_OT, NEW_OT, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)

print("OK: 飞空得出 + 疾病占入墓减半 已应用")
