# -*- coding: utf-8 -*-
"""盲评运行器 v5：支持 tune / holdout / 自定义 ID 列表。"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain
from run_blind_v4 import date_from_str, hex2yao
from human_narrative import build_human_narrative, render_human_markdown
from advice_framework import generate_advice

CASES = ROOT / "data" / "cases" / "classical_cases.json"
SPLITS = ROOT / "data" / "cases" / "case_splits.json"


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
    human = build_human_narrative(h)
    h["human_narrative"] = human

    s2 = tc.get("step2_use_god_identification") or {}
    s3 = tc.get("step3_strength_analysis") or {}
    s5 = tc.get("step5_synthesis") or {}
    rc_lines = tc.get("reasoning_chain", []) or []
    pt = [ln for ln in rc_lines if isinstance(ln, str) and ("[格局]" in ln or "[格局要点]" in ln)]
    timing = s5.get("timing") or {}

    return {
        "id": cid,
        "question": q,
        "hexagram": h["original_hexagram"]["name"],
        "changed_hexagram": (h.get("changed_hexagram") or {}).get("name", "?"),
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
