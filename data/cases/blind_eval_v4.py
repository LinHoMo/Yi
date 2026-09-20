import json, re
from pathlib import Path

BASE_FILE = str(Path(__file__).parent / "classical_cases.json")
ENG_FILE  = str(Path(__file__).parent / "blind_engine_output_v4.json")

with open(BASE_FILE, encoding="utf-8") as f:
    base = json.load(f)
with open(ENG_FILE, encoding="utf-8") as f:
    eng = json.load(f)

base_cases = base["cases"][:20]  # ZS001..ZS020
eng_cases  = eng["cases"]

direction_map = {
    "吉": 1, "平吉": 1, "大吉": 1, "平": 0, "平/不利": -0.5,
    "凶": -1, "大凶": -1, "下跌": -1,
}

def verdict_to_dir(v):
    if v in direction_map:
        return direction_map[v]
    v2 = v.lower()
    if "吉" in v2: return 1
    if "凶" in v2: return -1
    if "跌" in v2: return -1
    return 0

def use_god_score(eng, exp):
    """Return (cat_score, branch_score, position_score)"""
    e_cat = eng.get("use_god_category", "")
    x_cat = exp.get("use_god_god", exp.get("use_god", ""))
    e_branch = eng.get("use_god_branch", "")
    x_branch = exp.get("use_god_branch", "")
    e_pos = eng.get("use_god_position", None)
    
    cat_score = 15 if e_cat == x_cat else 0
    
    if x_branch and e_branch and x_branch != "?":
        branch_score = 10 if e_branch == x_branch else 0
    else:
        branch_score = 5  # ambiguous baseline, give partial credit
    
    # position: check if baseline mentions position (any number in key_points)
    pos_score = 5  # default to full unless explicit mismatch
    pos_matches = re.findall(r'(\d+)爻', " ".join(exp.get("key_points", [])))
    if pos_matches and e_pos is not None:
        if str(e_pos) in pos_matches:
            pos_score = 5
        else:
            pos_score = 2
    elif x_branch and x_branch != "?" and e_branch == x_branch:
        pos_score = 5
    
    return cat_score, branch_score, pos_score

def verdict_score(eng_dir, exp_dir):
    if eng_dir == 0:
        return 10, "不确定"
    if eng_dir == exp_dir:
        return 40, "完全一致"
    if eng_dir * exp_dir > 0:
        return 25, "大致一致(强度不同)"
    # partial: engine says neutral vs baseline strong
    return 0, "方向相反"

def pattern_score(eng_tags, eng_chain, exp_branch):
    """
    Check if engine tags cover the key pattern from baseline baseline:
    - The key_points field lists required patterns.
    - The expected use_god_branch is the critical branch.
    """
    combined = " ".join(eng_tags + eng_chain)
    
    # Pattern keyword lists
    score = 0
    matched = 0
    total_patterns = len(exp_branch)
    
    # Map of baseline tags to search terms in engine output
    # We check if the engine pattern_tags contain meaningful classical patterns
    has_pattern = len(eng_tags) > 0
    
    # Known pattern keywords to check
    key_patterns_to_check = [
        "冲中逢合", "回头克", "近病逢空", "飞克伏", "绝处逢生",
        "入墓", "反吟", "六合", "伏藏", "长生", "帝旺", "沐浴",
        "化合", "化退神", "旬空", "填实", "出空", "合处逢冲",
        "回头生", "暗动", "伏神", "飞空得出", "六冲", "墓", "绝于",
    ]
    
    # Extract patterns from baseline key_points
    baseline_text = " ".join(exp_branch) if isinstance(exp_branch, list) else str(exp_branch)
    
    engine_detected = []
    for p in key_patterns_to_check:
        if p in baseline_text and p in combined:
            engine_detected.append(p)
    
    if total_patterns == 0:
        return 15, "无关键格局要求"
    
    ratio = len(engine_detected) / max(total_patterns, 1)
    if ratio >= 0.5:
        return 15, f"格局匹配({','.join(engine_detected)})"
    elif ratio > 0:
        return 8, f"格局部分覆盖({','.join(engine_detected)})"
    else:
        return 0, "无格局识别"

def time_score(eng_yingqi, exp_yingqi, exp_branch):
    """Check yingqi textual overlap — shared date hints or day/period references."""
    if not exp_branch:
        return 15, "空白基准"
    
    shared_terms = []
    day_names = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑", "巳日", "午日", "未日"]
    for term in day_names:
        if term in str(exp_yingqi) and term in str(eng_yingqi):
            shared_terms.append(term)
    
    if exp_yingqi in eng_yingqi:
        return 15, f"应期完全匹配({exp_yingqi})"
    elif shared_terms:
        return 12, f"应期有共同项({','.join(shared_terms[:3])})"
    elif eng_yingqi and exp_yingqi:
        # loose overlap check
        return 8, "应期存在但不完全匹配"
    else:
        return 0, "无法判断应期"

results = []
for i, (b, e) in enumerate(zip(base_cases, eng_cases)):
    cid = b["id"]
    q = b.get("input", {}).get("question", "")
    x_branch = b["expected"].get("use_god_branch", "")
    
    e_cat = e.get("use_god_category", "")
    e_branch = e.get("use_god_branch", "")
    e_pos = e.get("use_god_position", None)
    
    x_verdict = b["expected"]["verdict"]
    e_verdict = e["verdict"]
    e_dir = verdict_to_dir(e_verdict)
    x_dir = verdict_to_dir(x_verdict)
    
    cs = use_god_score(e, b["expected"])
    vs, vs_label = verdict_score(e_dir, x_dir)
    ptags = e.get("pattern_tags", []) + e.get("reasoning_chain", [])
    ps, ps_label = pattern_score(e.get("pattern_tags", []), e.get("reasoning_chain", []), b["expected"].get("key_points", []))
    ts, ts_label = time_score(e.get("yingqi", ""), b["expected"].get("yingqi", ""), x_branch)
    
    total = cs[0] + cs[1] + cs[2] + vs + ps + ts
    results.append((cid, q, x_branch, e_branch, x_verdict, e_verdict, vs_label, ps_label, ts_label, (cs[0], cs[1], cs[2], vs, ps, ts), total))

print("=" * 80)
print(" 六爻引擎盲评报告 v4 (ZS001-ZS020, N=20)")
print("=" * 80)

all_scores = []
under70 = []
for cid, q, x_branch, e_branch, x_verdict, e_verdict, vs_label, ps_label, ts_label, dims, total in results:
    print(f"\n=== 案例 {cid} ===")
    print(f"问题: {q}")
    print(f"标准答案: 用神={b['expected']['use_god' if 'use_god' in b['expected'] else 'use_god']}@{x_branch}; 断={x_verdict}")
    print(f"引擎输出: 用神={e.get('use_god_category')}@{e_branch}; 断={e_verdict}")
    print(f"比对: 用神六亲{'正确' if dims[0]==15 else '错误'}; 用神地支{'正确' if dims[1]==10 else '部分' if dims[1]==5 else '错误'}; verdict方向={vs_label}; 格局={ps_label}; 应期={ts_label}")
    print(f"得分: 六亲={dims[0]}/15 + 地支={dims[1]}/10 + 位置={dims[2]}/5 + verdict={dims[3]}/40 + 格局={dims[4]}/15 + 应期={dims[5]}/15 = {total}/100")
    all_scores.append(total)
    if total < 70:
        under70.append((cid, q, x_branch, e_branch, x_verdict, e_verdict, dims, total))

avg = sum(all_scores) / len(all_scores)
print("\n" + "=" * 80)
print(f" 总胜率 = {avg:.1f}%  (目标 >= 90%)")
print(f" 案例得分列表: {all_scores}")
print("=" * 80)

if avg >= 90:
    print("\n✅ 达标: 平均分 >= 90%")
else:
    print(f"\n❌ 未达标: 距离目标差 {90-avg:.1f} 分")

if under70:
    print(f"\n⚠️  {len(under70)} 个案例得分 < 70 (需修复):")
    for cid, q, x_branch, e_branch, x_verdict, e_verdict, dims, total in under70:
        print(f"    {cid}: {total}分 - 标准用神@{x_branch}断{x_verdict} vs 引擎@{e_branch}断{e_verdict}")
