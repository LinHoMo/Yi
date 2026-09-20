# -*- coding: utf-8 -*-
"""打印每案例维度得分明细"""
import sys
sys.path.insert(0, r'C:\Users\Lin\Desktop\skills\liu-yao\data\cases')
import json, re
from pathlib import Path

P = Path(r'C:\Users\Lin\Desktop\skills\liu-yao\data\cases')
base = json.load(open(P / 'classical_cases.json', encoding='utf-8'))
eng = json.load(open(P / 'blind_engine_output_v4.json', encoding='utf-8'))

direction_map = {"吉":1,"平吉":1,"大吉":1,"平":0,"平/不利":-0.5,"凶":-1,"大凶":-1,"下跌":-1}
def verdict_to_dir(v):
    if v in direction_map: return direction_map[v]
    v2 = v.lower()
    if "吉" in v2: return 1
    if "凶" in v2 or "跌" in v2: return -1
    return 0

def use_god_score(e, x):
    cat = 15 if e.get("use_god_category","") == x.get("use_god", x.get("use_god_god","")) else 0
    xb = x.get("use_god_branch",""); eb = e.get("use_god_branch","")
    if xb and eb and xb != "?": branch = 10 if eb == xb else 0
    else: branch = 5
    pos = 5
    pm = re.findall(r'(\d+)爻', " ".join(x.get("key_points", [])))
    if pm and e.get("use_god_position") is not None:
        pos = 5 if str(e.get("use_god_position")) in pm else 2
    elif xb and xb != "?" and eb == xb: pos = 5
    return cat, branch, pos

def pattern_score(tags, chain, kp):
    combined = " ".join(tags + chain)
    key = ["冲中逢合","回头克","近病逢空","飞克伏","绝处逢生","入墓","反吟","六合","伏藏","长生","帝旺","沐浴","化合","化退神","旬空","填实","出空","合处逢冲","回头生","暗动","伏神","飞空得出"]
    total = len(kp)
    if total == 0: return 15
    det = [p for p in key if p in " ".join(kp) and p in combined]
    r = len(det)/total
    return 15 if r >= 0.5 else (8 if r > 0 else 0)

def time_score(ey, xy, xb):
    if not xb: return 15
    dn = ["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑","巳日","午日","未日"]
    shared = [t for t in dn if t in str(xy) and t in str(ey)]
    if xy in ey: return 15
    if shared: return 12
    if ey and xy: return 8
    return 0

for b, e in zip(base["cases"][:20], eng["cases"]):
    cid = b["id"]
    cs = use_god_score(e, b["expected"])
    vs = verdict_score = 40 if verdict_to_dir(e["verdict"]) == verdict_to_dir(b["expected"]["verdict"]) else (25 if verdict_to_dir(e["verdict"]) * verdict_to_dir(b["expected"]["verdict"]) > 0 else 0)
    ps = pattern_score(e.get("pattern_tags",[]), e.get("reasoning_chain",[]), b["expected"].get("key_points",[]))
    ts = time_score(e.get("yingqi",""), b["expected"].get("yingqi",""), b["expected"].get("use_god_branch",""))
    tot = sum(cs) + vs + ps + ts
    if tot < 90:
        print(f"{cid}: cat{cs[0]} branch{cs[1]} pos{cs[2]} verdict{vs} pattern{ps} timing{ts} = {tot} | eng_branch={e.get('use_god_branch')} vs exp={b['expected'].get('use_god_branch')} | eng_verdict={e['verdict']} exp={b['expected']['verdict']} | exp_kp={b['expected'].get('key_points')} | exp_yq={b['expected'].get('yingqi')} | eng_yq={e.get('yingqi')}")
