# -*- coding: utf-8 -*-
"""P0-9b 合处逢冲扩展至散事类（合伙/出行/交易/官讼）"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''        if (world_clashed or response_clashed) and ("婚姻" in q or "婚" in q or "占婚" in q):
            result["pattern"] = "合处逢冲则散"
            result["description"] = f"六合本利婚，然{'世爻' if world_clashed else '应爻'}逢冲，合处逢冲则散"
            result["impact_on_verdict"] = "婚姻六合不可解冲，先成后散"
            result["score_adjustment"] = -2.0
            return result'''

NEW = '''        if (world_clashed or response_clashed):
            SCATTER2 = ["婚姻", "婚", "占婚", "合伙", "合作", "出行", "外出", "交易", "买卖",
                        "生意", "官讼", "官司", "求财", "谋事", "开店", "签约", "合同"]
            if any(k in q for k in SCATTER2):
                result["pattern"] = "合处逢冲则散"
                result["description"] = f"六合本利事成，然{'世爻' if world_clashed else '应爻'}逢冲，合处逢冲则散"
                result["impact_on_verdict"] = "婚姻六合不可解冲，先成后散；散事类同"
                result["score_adjustment"] = -2.0
                return result'''

assert OLD in src, "合处逢冲段未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)
print("OK")
