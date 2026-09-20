# -*- coding: utf-8 -*-
"""P0-9 六冲主散：六冲无合解 + 合作/婚恋/出行/交易/官讼类 → -2.0"""
import io

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = '''        if world_he or response_he or moving_he:
            he_target = "世爻" if world_he else ("应爻" if response_he else "动爻")
            result["pattern"] = "冲中逢合可解"
            result["description"] = f"六冲本主散，然月日/动爻合{he_target}（{'世' if world_he else ''}{'应' if response_he else ''}），冲中逢合可解"
            result["impact_on_verdict"] = "冲处逢合可解冲散，转危为安"
            result["score_adjustment"] = 2.5
            return result

    # --- 合处逢冲则散 ---'''

NEW = '''        if world_he or response_he or moving_he:
            he_target = "世爻" if world_he else ("应爻" if response_he else "动爻")
            result["pattern"] = "冲中逢合可解"
            result["description"] = f"六冲本主散，然月日/动爻合{he_target}（{'世' if world_he else ''}{'应' if response_he else ''}），冲中逢合可解"
            result["impact_on_verdict"] = "冲处逢合可解冲散，转危为安"
            result["score_adjustment"] = 2.5
            return result

        # 六冲无合解 → 事散之象（合伙/婚姻/出行/交易/官讼/谋事类；近病六冲速愈除外）
        SCATTER_KEYWORDS = ["合伙", "合作", "婚姻", "婚", "出行", "外出", "交易", "买卖",
                            "生意", "官讼", "官司", "求财", "谋事", "开店", "签约", "合同"]
        if any(k in q for k in SCATTER_KEYWORDS):
            result["pattern"] = "六冲主散"
            result["description"] = f"六冲卦主散，{hex_name}卦世应相冲，事难成合"
            result["impact_on_verdict"] = "六冲事散，合伙/婚恋/出行/交易类不利"
            result["score_adjustment"] = -2.0
            return result

    # --- 合处逢冲则散 ---'''

assert OLD in src, "冲中逢合段未找到"
src = src.replace(OLD, NEW, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)
print("OK")
