# -*- coding: utf-8 -*-
"""修复 run_blind_v4: reasoning_chain 取自 tc 顶层（pattern_tags 恒空的根因）"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\run_blind_v4.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''            tc = run_thinking_chain(h)
            s2 = tc.get("step2_use_god_identification", {}) or {}
            s3 = tc.get("step3_strength_analysis", {}) or {}
            s5 = tc.get("step5_synthesis", {}) or {}

            pt = []
            for ln in s5.get("reasoning_chain", []):
                if isinstance(ln, str) and "[格局]" in ln:
                    pt.append(ln)'''

NEW = '''            tc = run_thinking_chain(h)
            s2 = tc.get("step2_use_god_identification", {}) or {}
            s3 = tc.get("step3_strength_analysis", {}) or {}
            s5 = tc.get("step5_synthesis", {}) or {}
            rc_lines = tc.get("reasoning_chain", []) or []

            pt = []
            for ln in rc_lines:
                if isinstance(ln, str) and "[格局]" in ln:
                    pt.append(ln)'''

assert OLD in src, "pt 段未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)
print("OK")
