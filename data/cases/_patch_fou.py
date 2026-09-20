# -*- coding: utf-8 -*-
"""修复：否卦从六冲列表移除（否=天地否，纯六合卦）"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''    is_chong = "六冲" in hex_type or hex_name in ("乾", "坤", "坎", "离", "震", "巽", "艮", "兑", "无妄", "大壮", "遁", "否", "晋", "萃", "夬", "姤", "解", "鼎", "归妹", "旅", "涣", "小过", "贲")'''
NEW = '''    is_chong = "六冲" in hex_type or hex_name in ("乾", "坤", "坎", "离", "震", "巽", "艮", "兑", "无妄", "大壮", "遁", "晋", "萃", "夬", "姤", "解", "鼎", "归妹", "旅", "涣", "小过", "贲")'''

assert OLD in src, "六冲列表未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)
print("OK")
