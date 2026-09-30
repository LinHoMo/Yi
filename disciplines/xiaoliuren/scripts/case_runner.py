# -*- coding: utf-8 -*-
"""小六壬·案例运行器：案例 JSON → 引擎输出（供评分器与冒烟用）。

    python scripts/case_runner.py data/cases/xiaoliuren_cases.json [--split tune] [--save]

输出契约（与六爻/梅花一致，供 yishu_core.eval 消费）：
  {"cases": [单例引擎输出…], "errors": [{"id", "error"}…]}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
for _p in (str(DISC / "scripts"), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from chart import chart  # noqa: E402
from analyze import analyze  # noqa: E402

DEFAULT_CASES = DISC / "data" / "cases" / "xiaoliuren_cases.json"


def load_cases(cases_file: str | Path = DEFAULT_CASES) -> list[dict]:
    """案例库 JSON → 案例列表。文件根必须是 {"cases": [...]}。"""
    p = Path(cases_file)
    data = json.loads(p.read_text(encoding="utf-8"))
    cases = data.get("cases")
    if not isinstance(cases, list):
        raise ValueError(f"{p} 缺少 cases 列表")
    return cases


def load_ids(split: str = "all") -> list[str]:
    """按 split 字段取案例 id（excluded 不参与任何评分）。"""
    return [c["id"] for c in load_cases()
            if split == "all" or c.get("split") == split]


def load_meta(cases_file: str | Path = DEFAULT_CASES) -> dict:
    """案例库 `_meta` 块（口径审计元数据：expected 来源、自洽项清单）。"""
    p = Path(cases_file)
    return json.loads(p.read_text(encoding="utf-8")).get("_meta") or {}


def run_case(case: dict) -> dict:
    """单个案例 → 引擎输出（评分维度的原始材料）。"""
    input_data = case.get("input") or {}
    params = dict(input_data)
    params.setdefault("question", case.get("question") or case.get("topic") or "")
    params.setdefault("topic", case.get("topic"))  # 案例声明的事类优先（问句措辞常歧义）
    c = chart(params)
    a = analyze(c)
    p = a["palace"]
    con = a["conclusion"]
    t = a["timing"]
    tv = a["topic_verdict"]
    return {
        "id": case.get("id"),
        "source": case.get("source"),
        "topic": a.get("topic"),
        "palace": p.get("宫名"),
        "palace_element": p.get("五行"),
        "verdict": con.get("方向"),
        "topic_line": tv.get("诀句"),
        "timing": t.get("主数"),
        "steps": [s.get("落宫") for s in a.get("steps") or []],
        "chart_summary": a.get("chart_summary"),
    }


def run_cases(cases: list[dict]) -> dict:
    """批量运行 → 输出契约。单个案例失败不拖垮整批。"""
    results, errors = [], []
    for case in cases:
        try:
            results.append(run_case(case))
        except Exception as exc:  # 单个案例失败不拖垮整批
            errors.append({"id": case.get("id"), "error": f"{type(exc).__name__}: {exc}"})
    return {"cases": results, "errors": errors}


def run_ids(ids: list[str]) -> dict:
    """按 id 列表运行（与六爻/梅花 case_runner 同接口）。"""
    by_id = {c["id"]: c for c in load_cases()}
    return run_cases([by_id[i] for i in ids if i in by_id])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cases_file", nargs="?", default=str(DEFAULT_CASES))
    ap.add_argument("--split", choices=["tune", "holdout", "all"], default="all")
    ap.add_argument("--save", action="store_true", help="写 data/cases/eval_<split>.json")
    args = ap.parse_args()

    all_cases = load_cases(args.cases_file)
    split = args.split
    picked = [c for c in all_cases if c.get("split") == split] if split != "all" else all_cases
    out = run_cases(picked)
    errs = out["errors"]
    ok = len(out["cases"]) - len(errs)
    print(f"案例 {len(picked)} 条｜成功 {ok}｜异常 {len(errs)} 条")
    for e in errs[:5]:
        print("  !", e["id"], e["error"])

    if args.save:
        name = "eval_all" if split == "all" else f"eval_{split}"
        dest = DISC / "data" / "cases" / f"{name}.json"
        dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已写", dest)
    return 1 if errs else 0


if __name__ == "__main__":
    from yishu_core.runtime import force_utf8_stdio  # noqa: E402
    force_utf8_stdio()
    sys.exit(main())
