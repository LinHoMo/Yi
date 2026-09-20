# -*- coding: utf-8 -*-
"""P0-7 应期：原神旺日带具体日支（ZS005 基准巳日匹配）"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''        # 逢生（原神临值日）
        timing_methods.append({
            "method": "逢生",
            "description": "原神旺日或值日应",
            "type": "迟应",
        })'''

NEW = '''        # 逢生（原神临值日）——给出具体旺日支（按原神五行）
        step2_d = safe_get(r, "_step2_data", default={})
        yuan_elem = (step2_d.get("yuan_shen") or {}).get("element", "")
        peak_days = {"木": "寅卯日", "火": "巳午日", "土": "辰戌丑未日", "金": "申酉日", "水": "亥子日"}
        pd = peak_days.get(yuan_elem, "")
        timing_methods.append({
            "method": "逢生",
            "description": f"原神旺日（{pd}）或值日应" if pd else "原神旺日或值日应",
            "type": "迟应",
        })'''

assert OLD in src, "逢生段未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)
print("OK")
