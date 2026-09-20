#!/usr/bin/env python3
"""Inline batch runner - bypasses module import issues"""
import json, sys, traceback, random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain

OUTPUT = Path(__file__).parent.parent / "data" / "cases" / "blind_engine_output_v3.json"
INPUT = Path(__file__).parent.parent / "data" / "cases" / "blind_input.json"

TY = {"乾":[7,7,7],"坤":[8,8,8],"坎":[8,7,8],"离":[7,8,7],"震":[8,8,7],"巽":[7,7,8],"艮":[7,8,8],"兑":[8,7,7]}
HT = {
    "乾":("乾","乾"),"坤":("坤","坤"),"屯":("坎","震"),"蒙":("艮","坎"),"需":("坎","乾"),"讼":("乾","坎"),
    "师":("坤","坎"),"比":("坎","坤"),"小畜":("巽","乾"),"履":("乾","兑"),"泰":("坤","乾"),"否":("乾","坤"),
    "同人":("乾","离"),"大有":("离","乾"),"谦":("坤","艮"),"豫":("震","坤"),"随":("兑","震"),"蛊":("艮","巽"),
    "临":("坤","兑"),"观":("巽","坤"),"噬嗑":("离","震"),"贲":("艮","离"),"剥":("艮","坤"),"复":("坤","震"),
    "无妄":("乾","震"),"大畜":("艮","乾"),"颐":("艮","震"),"大过":("兑","巽"),"坎":("坎","坎"),"离":("离","离"),
    "咸":("兑","艮"),"恒":("震","巽"),"遁":("乾","艮"),"大壮":("震","乾"),"晋":("离","坤"),"明夷":("坤","离"),
    "家人":("巽","离"),"睽":("离","兑"),"蹇":("坎","艮"),"解":("震","坎"),"损":("艮","兑"),"益":("巽","震"),
    "夬":("兑","乾"),"姤":("乾","巽"),"萃":("兑","坤"),"升":("坤","巽"),"困":("兑","坎"),"井":("坎","巽"),
    "革":("兑","离"),"鼎":("离","巽"),"震":("震","震"),"艮":("艮","艮"),"渐":("巽","艮"),"归妹":("震","兑"),
    "丰":("震","离"),"旅":("离","艮"),"巽":("巽","巽"),"兑":("兑","兑"),"涣":("巽","坎"),"节":("坎","兑"),
    "中孚":("巽","兑"),"小过":("震","艮"),"既济":("坎","离"),"未济":("离","坎"),
}

def h2y(hx, mv=None):
    if hx not in HT: return None
    u,l = HT[hx]; b = TY[l]+TY[u]
    if mv:
        for p in mv:
            if 1<=p<=6: b[p-1]=9 if b[p-1]==7 else 6
    return b

DATES = {"ZS001":{"y":2024,"m":6,"d":3},"ZS002":{"y":2024,"m":4,"d":10},"ZS003":{"y":2024,"m":11,"d":8},"ZS004":{"y":2024,"m":8,"d":19},"ZS005":{"y":2024,"m":12,"d":11},"ZS006":{"y":2024,"m":6,"d":6},"ZS007":{"y":2024,"m":2,"d":4},"ZS008":{"y":2024,"m":9,"d":10},"ZS009":{"y":2024,"m":6,"d":9},"ZS010":{"y":2024,"m":10,"d":19},"ZS011":{"y":2024,"m":2,"d":4},"ZS012":{"y":2024,"m":4,"d":15},"ZS013":{"y":2024,"m":4,"d":16},"ZS014":{"y":2024,"m":5,"d":17},"ZS015":{"y":2024,"m":4,"d":14},"ZS016":{"y":2024,"m":3,"d":17},"ZS017":{"y":2024,"m":3,"d":17},"ZS018":{"y":2024,"m":2,"d":4},"ZS019":{"y":2024,"m":4,"d":15},"ZS020":{"y":2024,"m":6,"d":10}}

HEX = {"ZS001":{"h":"益","M":[]},"ZS002":None,"ZS003":{"h":"革","M":[]},"ZS004":{"h":"同人","M":[]},"ZS005":{"h":"恒","M":[4]},"ZS006":{"h":"萃","M":[2]},"ZS007":{"h":"姤","M":[]},"ZS008":{"h":"屯","M":[5]},"ZS009":{"h":"恒","M":[]},"ZS010":{"h":"坤","M":[]},"ZS011":{"h":"巽","M":[3]},"ZS012":{"h":"否","M":[]},"ZS013":{"h":"姤","M":[]},"ZS014":{"h":"蹇","M":[]},"ZS015":{"h":"既济","M":[]},"ZS016":{"h":"升","M":[]},"ZS017":{"h":"贲","M":[]},"ZS018":{"h":"复","M":[]},"ZS019":{"h":"巽","M":[3]},"ZS020":{"h":"蹇","M":[]}}

with open(INPUT) as f:
    data = json.load(f)
cases = data.get("cases", data)

results = []
for i, case in enumerate(cases):
    cid = case["id"]; q = case["question"]
    di = DATES[cid]; hi = HEX[cid]
    try:
        if hi is not None:
            yao = h2y(hi["h"], hi.get("M"))
            h = build_hexagram_result(yao, q, "manual", di["y"], di["m"], di["d"], 10)
        else:
            random.seed(abs(hash(cid)) % 10000)
            yao = [sum(random.choice([2,3]) for _ in range(3)) for _ in range(6)]
            h = build_hexagram_result(yao, q, "coin", di["y"], di["m"], di["d"], 10)
        
        tc = run_thinking_chain(h)
        s2 = tc.get("step2_use_god_identification",{}) or {}
        s3 = tc.get("step3_strength_analysis",{}) or {}
        s5 = tc.get("step5_synthesis",{}) or {}
        
        pt = []
        for ln in s5.get("reasoning_chain",[]):
            if isinstance(ln, str) and "[格局]" in ln: pt.append(ln)
        
        ch = h.get("changed_hexagram") or {}
        r = {"id":cid,"question":q,"hexagram":h["original_hexagram"]["name"],
             "moving":[m.get("position") for m in h.get("moving_lines",[])],
             "changed_hexagram":ch.get("name","?"),
             "use_god_category":s2.get("use_god_category","?"),
             "use_god_branch":(s2.get("selected_use_god") or {}).get("earthly_branch","?"),
             "use_god_element":s2.get("use_god_element","?"),
             "use_god_position":(s2.get("selected_use_god") or {}).get("position","?"),
             "strength_level":s3.get("strength_level","?"),
             "strength_score":s3.get("effective_score","?"),
             "final_score":s5.get("final_score","?"),
             "verdict":s5.get("verdict","?"),
             "special_pattern":(s5.get("special_pattern") or {}).get("pattern"),
             "yingqi":(s5.get("timing") or {}).get("summary_text","?"),
             "reasoning_chain":s5.get("reasoning_chain",[]),
             "pattern_tags":pt,
             "classical_quotes":h.get("classical_quotes",[]),
             "empty_branches":h.get("empty_branches",[])}
        results.append(r)
        sp = f' 格局={(s5.get("special_pattern") or {}).get("pattern","")}' if (s5.get("special_pattern") or {}).get("pattern") else ''
        print(f'{cid}: 卦={h["original_hexagram"]["name"]} 用={s2.get("use_god_category")} 断={s5.get("verdict")} 分={s5.get("final_score")} 标={len(pt)}{sp}')
    except Exception as e:
        tb = traceback.format_exc()
        print(f'{cid}: ERROR: {e}')
        for line in tb.strip().split('\n')[-5:]:
            print(f'  {line}')
        results.append({"id":cid,"question":q,"error":str(e)[:200]})

with open(OUTPUT,"w",encoding="utf-8") as f:
    json.dump({"engine":"liuyao_engine.py v3","method":"deterministic","total":len(cases),"cases":results},f,ensure_ascii=False,indent=2)

ok = sum(1 for r in results if "error" not in r)
print(f'\n=== 成功: {ok}/{len(cases)} ===')
if ok:
    vdist = {}
    for r in results:
        if "verdict" in r:
            vdist[r["verdict"]]=vdist.get(r["verdict"],0)+1
    print(f"断语分布: {vdist}")
print(f"保存: {OUTPUT}")
