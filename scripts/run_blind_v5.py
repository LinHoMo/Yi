# -*- coding: utf-8 -*-
"""盲评运行器 v5：支持 tune / holdout / 自定义 ID 列表。"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import re

from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain
from human_narrative import build_human_narrative, render_human_markdown
from advice_framework import generate_advice

CASES = ROOT / "data" / "cases" / "classical_cases.json"
SPLITS = ROOT / "data" / "cases" / "case_splits.json"

# ── trigram yao values: 7=少阳, 8=少阴 ──
_TRIGRAM_YAO = {
    "乾": [7, 7, 7], "坤": [8, 8, 8], "坎": [8, 7, 8], "离": [7, 8, 7],
    "震": [8, 8, 7], "巽": [7, 7, 8], "艮": [7, 8, 8], "兑": [8, 7, 7],
}

# ── hexagram → (upper_trigram, lower_trigram) ──
_HEX2TRIGRAM = {
    "乾": ("乾", "乾"), "坤": ("坤", "坤"), "屯": ("坎", "震"), "蒙": ("艮", "坎"),
    "需": ("坎", "乾"), "讼": ("乾", "坎"), "师": ("坤", "坎"), "比": ("坎", "坤"),
    "小畜": ("巽", "乾"), "履": ("乾", "兑"), "泰": ("坤", "乾"), "否": ("乾", "坤"),
    "同人": ("乾", "离"), "大有": ("离", "乾"), "谦": ("坤", "艮"), "豫": ("震", "坤"),
    "随": ("兑", "震"), "蛊": ("艮", "巽"), "临": ("坤", "兑"), "观": ("巽", "坤"),
    "噬嗑": ("离", "震"), "贲": ("艮", "离"), "剥": ("艮", "坤"), "复": ("坤", "震"),
    "无妄": ("乾", "震"), "大畜": ("艮", "乾"), "颐": ("艮", "震"), "大过": ("兑", "巽"),
    "坎": ("坎", "坎"), "离": ("离", "离"), "咸": ("兑", "艮"), "恒": ("震", "巽"),
    "遁": ("乾", "艮"), "大壮": ("震", "乾"), "晋": ("离", "坤"), "明夷": ("坤", "离"),
    "家人": ("巽", "离"), "睽": ("离", "兑"), "蹇": ("坎", "艮"), "解": ("震", "坎"),
    "损": ("艮", "兑"), "益": ("巽", "震"), "夬": ("兑", "乾"), "姤": ("乾", "巽"),
    "萃": ("兑", "坤"), "升": ("坤", "巽"), "困": ("兑", "坎"), "井": ("坎", "巽"),
    "革": ("兑", "离"), "鼎": ("离", "巽"), "震": ("震", "震"), "艮": ("艮", "艮"),
    "渐": ("巽", "艮"), "归妹": ("震", "兑"), "丰": ("震", "离"), "旅": ("离", "艮"),
    "巽": ("巽", "巽"), "兑": ("兑", "兑"), "涣": ("巽", "坎"), "节": ("坎", "兑"),
    "中孚": ("巽", "兑"), "小过": ("震", "艮"), "既济": ("坎", "离"), "未济": ("离", "坎"),
}


def hex2yao(hx_name, changed_hx=None):
    """给定本卦名和变卦名, 返回六爻列表 (7/8=少阳/少阴, 9/6=动爻)"""
    if hx_name not in _HEX2TRIGRAM:
        return None
    u, l = _HEX2TRIGRAM[hx_name]
    base = _TRIGRAM_YAO[l] + _TRIGRAM_YAO[u]
    if changed_hx is None or changed_hx == hx_name:
        return base
    if changed_hx not in _HEX2TRIGRAM:
        return base
    cu, cl = _HEX2TRIGRAM[changed_hx]
    base_changed = _TRIGRAM_YAO[cl] + _TRIGRAM_YAO[cu]
    out = []
    for orig, chg in zip(base, base_changed):
        if orig == chg:
            out.append(orig)
        else:
            out.append(9 if orig == 7 else 6)
    return out


def date_from_str(date_str, default_year=2024, default_month=6):
    """从 '酉月丙辰日' / '庚辰日' / '丁巳日子丑旬空' 提取月支与日柱干支。"""
    branch_order = "子丑寅卯辰巳午未申酉戌亥"
    stems = "甲乙丙丁戊己庚辛壬癸"
    month_branch = None
    day_sb = None
    m = re.search(r"([%s])月" % branch_order, date_str)
    if m:
        month_branch = m.group(1)
    d = re.search(r"([%s])([%s])日" % (stems, branch_order), date_str)
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


def load_ids(split: str | None, only: list[str] | None) -> list[str]:
    data = json.loads(CASES.read_text(encoding="utf-8"))
    all_ids = [c["id"] for c in data["cases"]]
    if only:
        return [i for i in only if i in all_ids]
    if split == "tune":
        return [f"ZS{i:03d}" for i in range(1, 21) if f"ZS{i:03d}" in all_ids]
    if split == "holdout":
        if SPLITS.exists():
            sp = json.loads(SPLITS.read_text(encoding="utf-8"))
            return [i for i in sp.get("holdout", []) if i in all_ids]
        return [i for i in all_ids if i.startswith("HO")]
    return all_ids


def run_case(case: dict) -> dict:
    cid = case["id"]
    q = case.get("question") or (case.get("input") or {}).get("question", "")
    inp = case.get("input") or {}
    hx = case.get("hexagram") or {}
    d = date_from_str(inp.get("date", ""))
    ho, hc = hx.get("original"), hx.get("changed")
    if not ho:
        raise ValueError("缺少卦名")

    explicit = None
    if d.get("day_sb") or d.get("month_branch"):
        explicit = {}
        if d.get("day_sb"):
            explicit["day_sb"] = d["day_sb"]
        if d.get("month_branch"):
            explicit["month_sb"] = "甲" + d["month_branch"]

    yao = hex2yao(ho, hc)
    if yao is None:
        raise ValueError(f"无法解析卦象 {ho}->{hc}")
    h = build_hexagram_result(yao, q, "manual", d["year"], d["month"], d["day"], 10, explicit_time=explicit)
    tc = run_thinking_chain(h)
    thinking = tc.get("thinking_chain", tc)
    human = build_human_narrative(tc)
    tc["human_narrative"] = human

    s2 = thinking.get("step2_use_god_identification") or {}
    s3 = thinking.get("step3_strength_analysis") or {}
    s5 = thinking.get("step5_synthesis") or {}
    rc_lines = thinking.get("reasoning_chain", []) or []
    pt = [ln for ln in rc_lines if isinstance(ln, str) and ("[格局]" in ln or "[格局要点]" in ln)]
    timing = s5.get("timing") or {}

    return {
        "id": cid,
        "question": q,
        "hexagram": tc["original_hexagram"]["name"],
        "changed_hexagram": (tc.get("changed_hexagram") or {}).get("name", "?"),
        "use_god_category": s2.get("use_god_category", "?"),
        "use_god_branch": (s2.get("selected_use_god") or {}).get("earthly_branch", "?"),
        "use_god_element": s2.get("use_god_element", "?"),
        "use_god_position": (s2.get("selected_use_god") or {}).get("position", "?"),
        "strength_level": s3.get("strength_level", "?"),
        "strength_score": s3.get("effective_score", "?"),
        "final_score": s5.get("final_score", "?"),
        "verdict": s5.get("verdict", "?"),
        "special_pattern": (s5.get("special_pattern") or {}).get("pattern"),
        "yingqi": timing.get("summary_text", "?"),
        "yingqi_branches": timing.get("key_branches") or [],
        "reasoning_chain": rc_lines,
        "pattern_tags": pt,
        "classical_quotes": h.get("classical_quotes", []),
        "empty_branches": h.get("empty_branches", []),
        "human_narrative": human,
        "human_markdown": render_human_markdown(human),
    }


def main():
    split = "all"
    only = None
    if len(sys.argv) > 1:
        if sys.argv[1] in ("tune", "holdout", "all"):
            split = sys.argv[1]
        else:
            only = sys.argv[1:]

    ids = load_ids(split, only)
    data = json.loads(CASES.read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in data["cases"]}

    results, errors = [], []
    for cid in ids:
        try:
            r = run_case(by_id[cid])
            results.append(r)
            print(f"{cid}: {r['hexagram']} use={r['use_god_category']}@{r['use_god_branch']} verdict={r['verdict']} score={r['final_score']}")
        except Exception as e:
            tb = traceback.format_exc()
            print(f"{cid}: ERROR {e}")
            print("\n".join(tb.strip().splitlines()[-6:]))
            errors.append({"id": cid, "error": str(e)[:300]})
            results.append({"id": cid, "error": str(e)[:200]})

    out_name = {
        "tune": "blind_engine_output_v5.json",
        "holdout": "blind_engine_output_holdout.json",
        "all": "blind_engine_output_all.json",
    }.get(split, "blind_engine_output_custom.json")
    if only:
        out_name = "blind_engine_output_custom.json"

    out = ROOT / "data" / "cases" / out_name
    out.write_text(
        json.dumps(
            {
                "engine": "liuyao v5 holdout-pipeline",
                "split": split if not only else "custom",
                "ids": ids,
                "total": len(ids),
                "cases": results,
                "errors": errors,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"saved {out}  ok={sum(1 for r in results if 'error' not in r)}/{len(ids)}")


if __name__ == "__main__":
    main()
