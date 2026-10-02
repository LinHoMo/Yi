# -*- coding: utf-8 -*-
"""梅花易数·案例运行器：案例 JSON → 引擎输出（供评分器与冒烟用）。

    python scripts/case_runner.py data/cases/meihua_cases.json [--split tune] [--save]

输出契约（与六爻一致，供 yishu_core.eval 消费）：
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

DEFAULT_CASES = DISC / "data" / "cases" / "meihua_cases.json"


def load_cases(cases_file: str | Path = DEFAULT_CASES) -> list[dict]:
    """案例库 JSON → 案例列表；合并同目录其它 *_cases.json（外部独立集，永不调参）。

    主库 meihua_cases.json 与 external_cases.json 等按 id 去重合并——
    仿 liuyao 的「外部集与主库分文件、按 split 单列」模式（AGENTS.md §四.1 +
    EVAL-AUDIT §6.2）：外部集只报命中数、永不参与 tune。
    """
    p = Path(cases_file)
    data = json.loads(p.read_text(encoding="utf-8"))
    cases = data.get("cases")
    if not isinstance(cases, list):
        raise ValueError(f"{p} 缺少 cases 列表")
    seen = {c["id"] for c in cases if c.get("id")}
    case_dir = p.parent
    for extra in sorted(case_dir.glob("*_cases.json")):
        if extra.resolve() == p.resolve():
            continue
        try:
            extra_data = json.loads(extra.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for c in extra_data.get("cases", []):
            if c.get("id") and c["id"] not in seen:
                seen.add(c["id"])
                cases.append(c)
    return cases


def load_ids(split: str = "all") -> list[str]:
    """按 split 字段取案例 id（excluded 不参与任何评分）。

    支持任意 split 值（含 external_holdout）：凡 `c.get("split") == split` 即取，
    新增书源只登记数据、不必改本函数（与 liuyao load_ids 末段同思路）。
    """
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
    c = chart(params)
    a = analyze(c)
    bu = a["body_use"]
    iv = a["interaction"]
    con = a["conclusion"]
    t = a["timing"]
    return {
        "id": case.get("id"),
        "source": case.get("source"),
        "topic": a.get("topic"),
        "hexagram": c.get("hexagram"),
        "moving": c.get("moving"),
        "movings": c.get("movings"),
        "multi_move": c.get("multi_move"),
        "body_use_rule": c.get("body_use_rule"),
        "body": bu.get("体卦"),
        "use": bu.get("用卦"),
        "body_element": bu.get("体卦五行"),
        "use_element": bu.get("用卦五行"),
        "relation": bu.get("关系"),
        "sheng_ti": [h.get("卦") for h in iv.get("生体之卦") or []],
        "ke_ti": [h.get("卦") for h in iv.get("克体之卦") or []],
        "verdict": con.get("方向"),
        "special": con.get("特断", False),
        "timing_gz": t.get("卦气应期") or [],
        "numerical_timing": t.get("数应"),   # 《占卜总诀》动静定应期（行半/立全/坐卧倍）
        "qi_state": (a.get("body_qi") or {}).get("状态"),
        "chart_summary": a.get("chart_summary"),
        "analogies_keys": list((a.get("analogies") or {}).keys()),
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
    """按 id 列表运行（与六爻 case_runner 同接口）。"""
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
