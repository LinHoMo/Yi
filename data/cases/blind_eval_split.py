# -*- coding: utf-8 -*-
"""分集盲评：分别报告 tune / holdout 均分，禁止混分。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "data" / "cases" / "classical_cases.json"
SPLITS = ROOT / "data" / "cases" / "case_splits.json"

DAY_CHARS = list("子丑寅卯辰巳午未申酉戌亥")
KEY_PATTERNS = [
    "冲中逢合", "回头克", "回头生", "近病逢空", "近病逢合", "近病逢空即愈", "近病逢合为凶",
    "飞克伏", "伏生飞", "飞空得出", "飞生伏", "绝处逢生", "入墓", "反吟", "伏吟",
    "六合", "六冲", "伏藏", "伏神", "长生", "帝旺", "沐浴",
    "化合", "化退神", "化进神", "旬空", "填实", "出空", "出旬", "合处逢冲",
    "暗动", "墓", "绝于", "日辰合世", "合世", "变卦六合", "世爻", "动空",
    "原神生用", "动则生", "泄气", "月破", "随官入墓", "游魂", "归魂",
    "用神多现", "世持财", "内卦", "迟归", "用神生世", "兄弟持世", "出空",
]


def verdict_to_dir(v):
    s = str(v or "")
    if s in ("吉", "平吉", "大吉"):
        return 1
    if s in ("凶", "大凶", "下跌"):
        return -1
    if "吉" in s and "凶" not in s and "不利" not in s:
        return 1
    if "凶" in s or "跌" in s or "不利" in s:
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
        branch_score = 10 if cat_score == 15 else 0
    pos_score = 5
    return cat_score, branch_score, pos_score


def verdict_score(eng_v, exp_v):
    ed, xd = verdict_to_dir(eng_v), verdict_to_dir(exp_v)
    if ed == xd:
        return 40, "完全一致"
    if ed * xd > 0:
        return 32, "方向一致强度略异"
    if exp_v in ("平/不利", "平") and eng_v in ("凶", "平吉", "平"):
        return 32, "基准平/不利 vs 引擎偏负向"
    if ed == 0:
        return 12, "引擎中性"
    return 0, "方向相反"


def pattern_score(eng_tags, eng_chain, exp_key_points, exp_detail=""):
    combined = " ".join(list(eng_tags or []) + list(eng_chain or []))
    baseline = " ".join(exp_key_points or []) + " " + str(exp_detail or "")
    needed = [p for p in KEY_PATTERNS if p in baseline]
    if not needed:
        return 15, "无词典内格局词"
    detected = [p for p in needed if p in combined]
    aliases = {
        "旬空": ["旬空", "出旬", "填实", "冲空"],
        "出空": ["出空", "出旬", "填实", "冲空"],
        "伏神": ["伏神", "伏藏"],
        "伏藏": ["伏藏", "伏神"],
        "世爻": ["世爻", "持世", "世持"],
        "六合": ["六合"],
        "迟归": ["迟归", "用神生世", "生世"],
        "用神生世": ["用神生世", "生世", "迟归"],
        "兄弟持世": ["兄弟持世", "持兄", "兄弟"],
        "内卦": ["内卦"],
        "世持财": ["世持财", "持世"],
        "用神多现": ["用神多现", "多现", "两现"],
        "伏神得出": ["伏神得出", "飞空得出", "飞神旬空"],
        "飞空得出": ["飞空得出", "飞神旬空", "伏神得出"],
        "化退神": ["化退神", "化退"],
        "动则生": ["动则生", "原神生用", "动空"],
        "原神生用": ["原神生用", "动则生"],
        "暗动": ["暗动"],
        "冲空": ["冲空", "填实", "出旬", "旬空"],
        "月破": ["月破"],
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


def time_score(eng_yingqi, exp_yingqi):
    eng_yingqi = str(eng_yingqi or "")
    exp_yingqi = str(exp_yingqi or "")
    if not exp_yingqi:
        return 15, "空白基准"
    if exp_yingqi in eng_yingqi:
        return 15, f"应期完全匹配({exp_yingqi})"
    exp_days = [ch for ch in DAY_CHARS if ch in exp_yingqi]
    if exp_days and all(ch in eng_yingqi for ch in exp_days):
        return 15, f"应期地支全覆盖({','.join(exp_days)})"
    shared = [ch for ch in exp_days if ch in eng_yingqi]
    vague = [
        (("次日", "当天", "当日"), ("应速", "次日", "当日", "快则")),
        (("年内", "月余", "年"), ("年内", "应迟", "旺相之月", "月余", "节奏偏慢")),
        (("不安", "反复", "难成", "难"), ("不安", "反复", "合处逢冲", "冲中逢合", "难")),
        (("巳午月", "出空"), ("出空", "出旬", "填实", "巳", "午")),
        (("戌月",), ("戌", "季月")),
        (("子日",), ("子",)),
        (("丑日",), ("丑",)),
        (("未日",), ("未",)),
    ]
    vague_hit = False
    for exp_kws, eng_kws in vague:
        if any(k in exp_yingqi for k in exp_kws) and any(k in eng_yingqi for k in eng_kws):
            vague_hit = True
            break
    if shared:
        return 12, f"应期有共同项({','.join(shared[:4])})"
    if vague_hit:
        return 12, "应期节奏语义对齐"
    if "重点应期" in eng_yingqi:
        return 10, "应期已结构化但未对齐基准词"
    return 8, "应期存在但不完全匹配"


def evaluate(engine_file: Path, ids: list[str], label: str):
    base = json.loads(CASES.read_text(encoding="utf-8"))
    eng = json.loads(engine_file.read_text(encoding="utf-8"))
    by_b = {c["id"]: c for c in base["cases"]}
    by_e = {c.get("id"): c for c in eng.get("cases", [])}

    rows = []
    for cid in ids:
        if cid not in by_b or cid not in by_e:
            continue
        e = by_e[cid]
        if "error" in e and "verdict" not in e:
            rows.append((cid, 0, "引擎错误"))
            continue
        b = by_b[cid]["expected"]
        cs = use_god_score(e, b)
        vs, vs_l = verdict_score(e.get("verdict"), b.get("verdict"))
        ps, ps_l = pattern_score(e.get("pattern_tags"), e.get("reasoning_chain"), b.get("key_points"), b.get("detail"))
        ts, ts_l = time_score(e.get("yingqi"), b.get("yingqi"))
        total = cs[0] + cs[1] + cs[2] + vs + ps + ts
        rows.append((cid, total, f"verdict={vs_l}; 格局={ps_l}; 应期={ts_l}; dims={cs+(vs,ps,ts)}"))
        print(f"[{label}] {cid}: {total}/100  {vs_l} | {ps_l} | {ts_l}")

    if not rows:
        print(f"[{label}] 无可用结果")
        return {"label": label, "avg": None, "scores": []}
    scores = [r[1] for r in rows]
    avg = sum(scores) / len(scores)
    print(f"\n=== {label} 平均分 = {avg:.1f}%  (n={len(scores)})  分数={scores} ===\n")
    return {"label": label, "avg": round(avg, 2), "scores": scores, "ids": [r[0] for r in rows]}


def main():
    splits = json.loads(SPLITS.read_text(encoding="utf-8")) if SPLITS.exists() else {}
    tune_ids = splits.get("tune") or [f"ZS{i:03d}" for i in range(1, 21)]
    holdout_ids = splits.get("holdout") or []

    summary = {"tune": None, "holdout": None}
    tune_file = ROOT / "data" / "cases" / "blind_engine_output_v5.json"
    holdout_file = ROOT / "data" / "cases" / "blind_engine_output_holdout.json"
    all_file = ROOT / "data" / "cases" / "blind_engine_output_all.json"

    if tune_file.exists():
        summary["tune"] = evaluate(tune_file, tune_ids, "tune")
    elif all_file.exists():
        summary["tune"] = evaluate(all_file, tune_ids, "tune")
    else:
        print("缺少 tune 输出，请先: python scripts/run_blind_v5.py tune")

    if holdout_file.exists():
        summary["holdout"] = evaluate(holdout_file, holdout_ids, "holdout")
    elif all_file.exists():
        summary["holdout"] = evaluate(all_file, holdout_ids, "holdout")
    else:
        print("缺少 holdout 输出，请先: python scripts/run_blind_v5.py holdout")

    out = ROOT / "data" / "cases" / "blind_eval_split_summary.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("summary ->", out)
    if summary["tune"]:
        print(f"TUNE={summary['tune']['avg']}%")
    if summary["holdout"]:
        print(f"HOLDOUT={summary['holdout']['avg']}%")


if __name__ == "__main__":
    main()
