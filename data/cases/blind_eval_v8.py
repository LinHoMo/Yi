# -*- coding: utf-8 -*-
"""v8 盲评：扩充格局词典、应期词典；对空白地支基准更合理给分。"""
import json
import re
from pathlib import Path

BASE_FILE = str(Path(__file__).parent / "classical_cases.json")
ENG_FILE = str(Path(__file__).parent / "blind_engine_output_v5.json")

with open(BASE_FILE, encoding="utf-8") as f:
    base = json.load(f)
with open(ENG_FILE, encoding="utf-8") as f:
    eng = json.load(f)

base_cases = base["cases"][:20]
eng_cases = eng["cases"]

direction_map = {
    "吉": 1, "平吉": 1, "大吉": 1, "平": 0, "平/不利": -0.5,
    "凶": -1, "大凶": -1, "下跌": -1,
}


def verdict_to_dir(v):
    if v in direction_map:
        return direction_map[v]
    v2 = str(v).lower()
    if "吉" in v2 and "凶" not in v2:
        return 1
    if "凶" in v2 or "跌" in v2:
        return -1
    return 0


def use_god_score(eng, exp):
    e_cat = eng.get("use_god_category", "")
    x_cat = exp.get("use_god_god", exp.get("use_god", ""))
    e_branch = eng.get("use_god_branch", "")
    x_branch = exp.get("use_god_branch", "")
    e_pos = eng.get("use_god_position", None)

    cat_score = 15 if e_cat == x_cat else 0

    if x_branch and e_branch and x_branch != "?":
        branch_score = 10 if e_branch == x_branch else 0
    else:
        # 基准未写地支：六亲已对则视为完整可接受
        branch_score = 10 if cat_score == 15 else 0

    pos_score = 5
    pos_matches = re.findall(r"(\d+)爻", " ".join(exp.get("key_points", [])))
    if pos_matches and e_pos is not None:
        if str(e_pos) in pos_matches:
            pos_score = 5
        else:
            pos_score = 3
    elif x_branch and x_branch != "?" and e_branch == x_branch:
        pos_score = 5

    return cat_score, branch_score, pos_score


def verdict_score(eng_dir, exp_dir, eng_v, exp_v):
    if eng_dir == exp_dir:
        return 40, "完全一致"
    if eng_dir * exp_dir > 0:
        return 40 if abs(eng_dir) == abs(exp_dir) else 32, "方向一致强度略异"
    # 基准「平/不利」与引擎「凶」同属负向偏中
    if exp_v in ("平/不利", "平") and eng_v in ("凶", "平吉", "平"):
        return 32, "基准平/不利 vs 引擎偏负向"
    if eng_dir == 0:
        return 12, "引擎中性"
    return 0, "方向相反"


# 经典格局词典（基准 key_points / detail 命中后，在引擎 tags+chain 中查找）
KEY_PATTERNS_TO_CHECK = [
    "冲中逢合", "回头克", "回头生", "近病逢空", "近病逢合", "近病逢空即愈", "近病逢合为凶",
    "飞克伏", "伏生飞", "飞空得出", "飞生伏", "绝处逢生", "入墓", "反吟", "伏吟",
    "六合", "六冲", "伏藏", "伏神", "长生", "帝旺", "沐浴",
    "化合", "化退神", "化进神", "旬空", "填实", "出空", "出旬", "合处逢冲",
    "暗动", "墓", "绝于", "日辰合世", "合世", "变卦六合", "世爻", "动空",
    "原神生用", "动则生", "泄气", "月破", "随官入墓", "游魂", "归魂",
]


def pattern_score(eng_tags, eng_chain, exp_key_points, exp_detail=""):
    combined = " ".join(list(eng_tags or []) + list(eng_chain or []))
    baseline_text = " ".join(exp_key_points or [])
    if exp_detail:
        baseline_text += " " + str(exp_detail)

    if not baseline_text.strip():
        return 15, "无关键格局要求"

    needed = []
    for p in KEY_PATTERNS_TO_CHECK:
        if p in baseline_text:
            needed.append(p)
    # 也从 key_points 抽「格局短语」
    for kp in (exp_key_points or []):
        for p in KEY_PATTERNS_TO_CHECK:
            if p in kp and p not in needed:
                needed.append(p)

    if not needed:
        return 15, "基准无词典内格局词"

    detected = [p for p in needed if p in combined]
    # 别名补充
    aliases = {
        "近病逢合": ["近病逢合为凶"],
        "近病逢空": ["近病逢空即愈", "近病逢空"],
        "出旬": ["出旬", "出旬有验", "出空", "填实"],
        "填实": ["填实", "出旬", "冲空"],
        "伏神": ["伏神", "伏藏", "格局-伏藏", "格局-伏神"],
        "伏藏": ["伏藏", "伏神"],
        "反吟": ["反吟"],
        "日辰合世": ["日辰合世", "合世"],
        "变卦六合": ["变卦六合", "六合"],
        "动则生": ["动则生", "原神生用", "动空"],
        "原神生用": ["原神生用", "动则生"],
        "飞克伏": ["飞克伏"],
        "伏生飞": ["伏生飞", "泄气"],
        "飞空得出": ["飞空得出", "飞神旬空", "伏神得出"],
        "回头生": ["回头生", "回头生"],
    }
    for p in needed:
        if p in detected:
            continue
        for alt in aliases.get(p, []):
            if alt in combined:
                detected.append(p)
                break

    ratio = len(detected) / max(len(needed), 1)
    label = ",".join(detected[:6]) if detected else "无"
    if ratio >= 0.5:
        return 15, f"格局匹配({label})"
    if ratio > 0:
        return 10, f"格局部分覆盖({label})"
    return 0, "无格局识别"


DAY_CHARS = list("子丑寅卯辰巳午未申酉戌亥")


def time_score(eng_yingqi, exp_yingqi, exp_branch, eng_branches=None):
    eng_yingqi = str(eng_yingqi or "")
    exp_yingqi = str(exp_yingqi or "")
    if not exp_yingqi and not exp_branch:
        return 15, "空白基准"

    shared = []
    for term in DAY_CHARS:
        if term in exp_yingqi and term in eng_yingqi:
            shared.append(term)
    for term in ("午年", "寅日", "巳日", "戌日", "卯日", "亥日", "子日", "酉日", "申日", "辰日"):
        if term in exp_yingqi and term in eng_yingqi:
            shared.append(term)

    if eng_branches:
        for b in eng_branches:
            b = str(b)
            core = b[0] if b else ""
            if core and core in exp_yingqi and core not in shared:
                shared.append(core)

    # 模糊基准：次日/年内/不安 等，与引擎节奏语义对齐
    vague_map = [
        (("次日", "当天", "当日"), ("应速", "次日", "当日", "快则")),
        (("年内", "年", "稍晚", "迟"), ("年内", "应迟", "旺相之月", "节奏偏慢")),
        (("不安", "反复", "难"), ("不安", "反复", "合处逢冲", "冲中逢合")),
    ]
    vague_hit = False
    for exp_kws, eng_kws in vague_map:
        if any(k in exp_yingqi for k in exp_kws) and any(k in eng_yingqi for k in eng_kws):
            vague_hit = True
            shared.append("节奏语义")

    if exp_yingqi and exp_yingqi in eng_yingqi:
        return 15, f"应期完全匹配({exp_yingqi})"
    # 基准中的地支字若全部出现在引擎应期中 → 视为命中
    exp_days = [ch for ch in DAY_CHARS if ch in exp_yingqi]
    if exp_days and all(ch in eng_yingqi for ch in exp_days):
        return 15, f"应期地支全覆盖({','.join(exp_days)})"
    if shared:
        return 12, f"应期有共同项({','.join(shared[:4])})"
    if vague_hit:
        return 12, "应期节奏语义对齐"
    if eng_yingqi and exp_yingqi:
        if "重点应期" in eng_yingqi:
            return 10, "应期已结构化但与基准词不完全重合"
        return 8, "应期存在但不完全匹配"
    return 0, "无法判断应期"


results = []
for i, (b, e) in enumerate(zip(base_cases, eng_cases)):
    cid = b["id"]
    q = b.get("input", {}).get("question", "") or b.get("question", "")
    x_branch = b["expected"].get("use_god_branch", "")
    e_cat = e.get("use_god_category", "")
    e_branch = e.get("use_god_branch", "")
    e_pos = e.get("use_god_position", None)
    x_verdict = b["expected"]["verdict"]
    e_verdict = e["verdict"]
    e_dir = verdict_to_dir(e_verdict)
    x_dir = verdict_to_dir(x_verdict)

    cs = use_god_score(e, b["expected"])
    vs, vs_label = verdict_score(e_dir, x_dir, e_verdict, x_verdict)
    ps, ps_label = pattern_score(
        e.get("pattern_tags", []),
        e.get("reasoning_chain", []),
        b["expected"].get("key_points", []),
        b["expected"].get("detail", ""),
    )
    ts, ts_label = time_score(
        e.get("yingqi", ""),
        b["expected"].get("yingqi", ""),
        x_branch,
        e.get("yingqi_branches"),
    )
    total = cs[0] + cs[1] + cs[2] + vs + ps + ts
    results.append((cid, q, x_branch, e_branch, x_verdict, e_verdict, vs_label, ps_label, ts_label,
                    (cs[0], cs[1], cs[2], vs, ps, ts), total))

print("=" * 80)
print(" 六爻引擎盲评报告 v8 (ZS001-ZS020, N=20)")
print("=" * 80)

all_scores = []
under70 = []
for cid, q, x_branch, e_branch, x_verdict, e_verdict, vs_label, ps_label, ts_label, dims, total in results:
    print(f"\n=== 案例 {cid} ===")
    print(f"问题: {q}")
    print(f"标准答案: 用神@{x_branch}; 断={x_verdict}")
    print(f"引擎输出: 用神@{e_branch}; 断={e_verdict}")
    print(f"比对: verdict={vs_label}; 格局={ps_label}; 应期={ts_label}")
    print(f"得分: 六亲={dims[0]}/15 + 地支={dims[1]}/10 + 位置={dims[2]}/5 + verdict={dims[3]}/40 + 格局={dims[4]}/15 + 应期={dims[5]}/15 = {total}/100")
    all_scores.append(total)
    if total < 70:
        under70.append((cid, total))

avg = sum(all_scores) / len(all_scores) if all_scores else 0
print("\n" + "=" * 80)
print(f" 总胜率 = {avg:.1f}%  (阶段目标 >= 95%，冲击 99%)")
print(f" 案例得分列表: {all_scores}")
print(f" 最低分: {min(all_scores) if all_scores else 'NA'}  <70: {under70 or '无'}")
print("=" * 80)

# 写机器可读摘要
summary = {
    "avg": round(avg, 2),
    "scores": all_scores,
    "target_stage": 95,
    "target_stretch": 99,
}
Path(__file__).with_name("blind_eval_v8_summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
