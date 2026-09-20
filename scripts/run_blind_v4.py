#!/usr/bin/env python3
"""Inline batch runner v4 — driven by classical_cases.json, NOT hardcoded HEX dict"""
import json, re, sys, traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain
try:
    from human_narrative import build_human_narrative, render_human_markdown
except Exception:
    build_human_narrative = None
    render_human_markdown = None

SCRIPT_DIR = Path(__file__).parent
OUTPUT = SCRIPT_DIR.parent / "data" / "cases" / "blind_engine_output_v5.json"
CLASSICAL = SCRIPT_DIR.parent / "data" / "cases" / "classical_cases.json"

# trigram yao values: 7=少阳, 8=少阴
TY = {"乾":[7,7,7],"坤":[8,8,8],"坎":[8,7,8],"离":[7,8,7],
      "震":[8,8,7],"巽":[7,7,8],"艮":[7,8,8],"兑":[8,7,7]}
# hex → (upper_trigram, lower_trigram)
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

def hex2yao(hx_name, changed_hx=None):
    """给定本卦名和变卦名, 返回六爻列表 (7/8=少阳/少阴, 9/6=动爻)"""
    if hx_name not in HT:
        return None
    u, l = HT[hx_name]
    base = TY[l] + TY[u]
    if changed_hx is None or changed_hx == hx_name:
        return base
    if changed_hx not in HT:
        return base
    cu, cl = HT[changed_hx]
    base_changed = TY[cl] + TY[cu]
    out = []
    for orig, chg in zip(base, base_changed):
        if orig == chg:
            out.append(orig)
        else:
            # 动爻: 原阳(7)→老阳(9), 原阴(8)→老阴(6)
            out.append(9 if orig == 7 else 6)
    return out


def date_from_str(date_str, default_year=2024, default_month=6):
    """从 '酉月丙辰日' / '庚辰日' / '丁巳日子丑旬空' 提取月支与日柱干支。

    修复 v4 遗留缺陷：此前只提取地支并转成公历日期，引擎用公历重算四柱，
    导致 20 个古典案例的月建/日辰/空亡全部失真（如 '巳月戊戌日' 被算成
    '庚午月丙午日'）。现在直接解析原始干支并原样传给引擎。

    返回：
        {
            "year": default_year, "month": default_month, "day": 1,
            "month_branch": str|None,   # 月支（如 '巳'），无月则 None
            "day_sb": str|None,         # 完整日柱干支（如 '戊戌'），无日则 None
        }
    """
    BRANCH_ORDER = "子丑寅卯辰巳午未申酉戌亥"
    STEMS = "甲乙丙丁戊己庚辛壬癸"
    month_branch = None
    day_sb = None
    m = re.search(r"([%s])月" % BRANCH_ORDER, date_str)
    if m:
        month_branch = m.group(1)
    d = re.search(r"([%s])([%s])日" % (STEMS, BRANCH_ORDER), date_str)
    if d:
        day_sb = d.group(1) + d.group(2)
    return {
        "year": default_year,
        "month": default_month,
        "day": 1,
        "month_branch": month_branch,
        "day_branch": day_sb[1] if day_sb else None,
        "day_sb": day_sb,
    }


def main():
    with open(CLASSICAL, encoding="utf-8") as f:
        cc = json.load(f)

    target_ids = {f"ZS{i:03d}" for i in range(1, 21)}
    cases = [c for c in cc["cases"] if c["id"] in target_ids]

    if len(cases) < 20:
        print(f"WARNING: only {len(cases)} cases found, expected 20")
        print(f"Missing: {target_ids - {c['id'] for c in cases}}")

    results = []
    errors = []
    for case in cases:
        cid = case["id"]
        q = case["question"]
        inp = case.get("input", {})
        hex_info = case.get("hexagram", {})
        date_str = inp.get("date", "")

        try:
            d = date_from_str(date_str)
            ho = hex_info.get("original")
            hc = hex_info.get("changed")

            explicit = {}
            if d.get("day_sb"):
                explicit["day_sb"] = d["day_sb"]
            if d.get("month_branch"):
                explicit["month_sb"] = "甲" + d["month_branch"]  # 月干缺失，用甲占位（仅影响显示）
            explicit = explicit or None

            if ho:
                yao = hex2yao(ho, hc)
                if yao is None:
                    raise ValueError(f"无法解析卦象: {ho} → {hc}")
                h = build_hexagram_result(yao, q, "manual", d["year"], d["month"], d["day"], 10, explicit_time=explicit)
            else:
                # 无卦（如ZS002占岳父近病）：数据缺陷，随机种子起卦仅保证可运行
                import random
                random.seed(abs(hash(cid)) % 10000)
                yao = [sum(random.choice([2, 3]) for _ in range(3)) for _ in range(6)]
                h = build_hexagram_result(yao, q, "coin", d["year"], d["month"], d["day"], 10, explicit_time=explicit)

            tc = run_thinking_chain(h)
            s2 = tc.get("step2_use_god_identification", {}) or {}
            s3 = tc.get("step3_strength_analysis", {}) or {}
            s5 = tc.get("step5_synthesis", {}) or {}
            rc_lines = tc.get("reasoning_chain", []) or []

            pt = []
            for ln in rc_lines:
                if isinstance(ln, str) and ("[格局]" in ln or "[格局要点]" in ln):
                    pt.append(ln)

            timing = s5.get("timing") or {}
            yingqi = timing.get("summary_text", "?")
            yingqi_branches = timing.get("key_branches") or []

            human = None
            human_md = ""
            if build_human_narrative:
                try:
                    human = build_human_narrative(h)
                    human_md = render_human_markdown(human) if render_human_markdown else ""
                except Exception as he:
                    human = {"error": str(he)[:200]}

            ch = h.get("changed_hexagram") or {}
            r = {
                "id": cid,
                "question": q,
                "hexagram": h["original_hexagram"]["name"],
                "changed_hexagram": ch.get("name", "?"),
                "use_god_category": s2.get("use_god_category", "?"),
                "use_god_branch": (s2.get("selected_use_god") or {}).get("earthly_branch", "?"),
                "use_god_element": s2.get("use_god_element", "?"),
                "use_god_position": (s2.get("selected_use_god") or {}).get("position", "?"),
                "strength_level": s3.get("strength_level", "?"),
                "strength_score": s3.get("effective_score", "?"),
                "final_score": s5.get("final_score", "?"),
                "verdict": s5.get("verdict", "?"),
                "special_pattern": (s5.get("special_pattern") or {}).get("pattern"),
                "yingqi": yingqi,
                "yingqi_branches": yingqi_branches,
                "reasoning_chain": s5.get("reasoning_chain", rc_lines),
                "pattern_tags": pt,
                "classical_quotes": h.get("classical_quotes", []),
                "empty_branches": h.get("empty_branches", []),
                "human_narrative": human,
                "human_markdown": human_md,
            }
            results.append(r)
            sp = f' 格局={(s5.get("special_pattern") or {}).get("pattern", "")}' if (s5.get("special_pattern") or {}).get("pattern") else ""
            print(f'{cid}: 卦={h["original_hexagram"]["name"]} 用={s2.get("use_god_category")} 断={s5.get("verdict")} 分={s5.get("final_score")} 标={len(pt)}{sp}')
        except Exception as e:
            tb = traceback.format_exc()
            print(f'{cid}: ERROR: {e}')
            for line in tb.strip().split('\n')[-8:]:
                print(f'  {line}')
            errors.append({"id": cid, "question": q, "error": str(e)[:300]})
            results.append({"id": cid, "question": q, "error": str(e)[:200]})

    output_data = {
        "engine": "liuyao_engine.py v4 (driven by classical_cases.json)",
        "method": "deterministic",
        "total": len(cases),
        "source_hash": abs(hash(json.dumps(cc["cases"][:20], sort_keys=True))) % 100000,
        "cases": results,
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    ok = sum(1 for r in results if "error" not in r)
    print(f'\n=== 成功: {ok}/{len(cases)} ===')
    if ok:
        vdist = {}
        for r in results:
            if "verdict" in r:
                vdist[r["verdict"]] = vdist.get(r["verdict"], 0) + 1
        print(f"断语分布: {vdist}")
    if errors:
        print(f"错误: {[e['id'] for e in errors]}")
    print(f"保存: {OUTPUT}")


if __name__ == "__main__":
    main()
