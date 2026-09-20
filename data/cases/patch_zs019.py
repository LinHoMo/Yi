# -*- coding: utf-8 -*-
from pathlib import Path
TC = Path(r"C:\Users\Lin\Desktop\skills\liu-yao\.worktrees\liuyao-optimize\scripts\thinking_chain.py")
t = TC.read_text(encoding="utf-8")

old = '''    # 2) 兄弟持世 + 求财 — 古籍大忌（《增删》兄弟持世莫求财）
    if world_relation == "兄弟" and _is_wealth and ug_cat == "妻财":
        classical_adj -= 1.2
        classical_notes.append("【兄弟持世求财】兄弟克财，求财多耗，-1.2")
'''
new = '''    # 2) 兄弟持世 + 求财 — 古籍大忌（《增删》兄弟持世莫求财）
    _sp_pat_txt = ""
    try:
        if isinstance(special_pattern, dict):
            _sp_pat_txt = str(special_pattern.get("pattern") or "") + str(special_pattern.get("description") or "")
    except Exception:
        _sp_pat_txt = ""
    if world_relation == "兄弟" and _is_wealth and ug_cat == "妻财":
        if any(k in _q_l for k in ("失", "找回", "失物")) or "冲中逢合" in _sp_pat_txt:
            classical_adj -= 0.2
            classical_notes.append("【兄弟持世·失物/逢合轻扣】另有冲中逢合等解象，仅-0.2")
        else:
            classical_adj -= 1.2
            classical_notes.append("【兄弟持世求财】兄弟克财，求财多耗，-1.2")
'''
if old not in t:
    raise SystemExit("block2 missing")
t = t.replace(old, new, 1)

old = '''    if _lv_ug in ("旺", "极旺") and ug_cat and ug_cat != "世爻":
        if (not _yuan_pos) or (not _yuan_moving):
            # 原神不在卦或全静：旺而无源
            classical_adj -= 1.0
            classical_notes.append("【原神失位】用神虽旺而原神不动/缺位，旺极无源，-1.0")
'''
new = '''    if _lv_ug in ("旺", "极旺") and ug_cat and ug_cat != "世爻":
        _skip_yuanshen = (
            "冲中逢合" in _sp_pat_txt
            or any(k in _q_l for k in ("失", "找回", "失物"))
            or "世持财" in _sp_pat_txt
        )
        if ((not _yuan_pos) or (not _yuan_moving)) and not _skip_yuanshen:
            classical_adj -= 1.0
            classical_notes.append("【原神失位】用神虽旺而原神不动/缺位，旺极无源，-1.0")
'''
if old not in t:
    raise SystemExit("yuanshen block missing")
t = t.replace(old, new, 1)

old = '''        if any("原神失位" in n for n in classical_notes):
            if verdict in ("大吉",):
                verdict = "吉"
                verdict_desc = "表面有力，实则源头不足，勿被旺象迷惑"
'''
new = '''        if any("原神失位" in n for n in classical_notes) and "冲中逢合" not in _sp_pat_txt:
            if verdict in ("大吉",):
                verdict = "吉"
                verdict_desc = "表面有力，实则源头不足，勿被旺象迷惑"
'''
if old not in t:
    raise SystemExit("verdict yuanshen missing")
t = t.replace(old, new, 1)

old = '''        if world_relation == "兄弟" and _is_wealth and ug_cat == "妻财":
            if verdict in ("大吉",):
                verdict = "吉"
                verdict_desc = "有财可谋，但兄弟持世，到手易耗"
            elif verdict == "吉" and final_score < 2.5:
                verdict = "平吉"
                verdict_desc = "财路有象，兄弟持世须防破耗"
            elif verdict in ("平吉",) and final_score <= 0.2:
                verdict = "平/不利"
                verdict_desc = "兄弟持世求财，辛苦多耗，得不偿失"
'''
new = '''        if world_relation == "兄弟" and _is_wealth and ug_cat == "妻财":
            _soft_bro = any(k in _q_l for k in ("失", "找回", "失物")) or "冲中逢合" in _sp_pat_txt
            if _soft_bro:
                if verdict in ("凶", "大凶") and final_score >= 0:
                    verdict = "吉"
                    verdict_desc = "虽兄弟持世，然冲中逢合，主先难后成"
                elif verdict == "平吉" and final_score >= 0:
                    verdict = "吉"
                    verdict_desc = "有惊无险，失而可复得"
            else:
                if verdict in ("大吉",):
                    verdict = "吉"
                    verdict_desc = "有财可谋，但兄弟持世，到手易耗"
                elif verdict == "吉" and final_score < 2.5:
                    verdict = "平吉"
                    verdict_desc = "财路有象，兄弟持世须防破耗"
                elif verdict in ("平吉",) and final_score <= 0.2:
                    verdict = "平/不利"
                    verdict_desc = "兄弟持世求财，辛苦多耗，得不偿失"
'''
if old not in t:
    raise SystemExit("verdict brother missing")
t = t.replace(old, new, 1)

TC.write_text(t, encoding="utf-8")
print("patched soft brother/yuanshen")
