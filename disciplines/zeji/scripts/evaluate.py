# -*- coding: utf-8 -*-
"""择吉·古籍案例对齐评分（tune / holdout 分别出分，禁止混分）。

    python scripts/evaluate.py --split all
    python scripts/evaluate.py --split tune --verbose
    python scripts/evaluate.py --split holdout
    python scripts/evaluate.py --stage score --engine-file data/cases/eval_all.json

口径说明（务必连同分数一起阅读，AGENTS.md 铁律三）：
  本脚本衡量的是**引擎输出与案例库要点的一致性**，不是现实世界预言命中率。
  案例库要点分两类：机械因子（建除/黄黑道/值宿，历法真值，对照通书核对）
  与规则应用（宜忌命中、综合方向，来自 verdicts.json 的《协纪辨方书》口径）。

维度与权重（单一真值源，总和 100）：
  建除 20 / 日值神 20 / 黄道 10 / 值宿 20 / 宜忌命中 15 / 综合方向 15
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.eval import run_eval, report  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
import case_runner  # noqa: E402

OUT_DIR = DISC / "data" / "cases"

WEIGHTS = {
    "jian_chu": 20,
    "day_god": 20,
    "huang_dao": 10,
    "xiu": 20,
    "yi_ji": 15,
    "verdict": 15,
}

MODEL = "strict"

_DIRECTION = {"吉": 1, "平": 0, "凶": -1}


def _direction(v) -> int:
    return _DIRECTION.get(str(v or "").strip(), 0)


def score_case(eng: dict, exp: dict, model: str) -> dict:
    """单例打分。返回 {dim: (earned, applicable_weight, note)}。"""
    dims: dict[str, tuple[int, int, str]] = {}

    # 建除神（历法真值：月建 + 日支）
    w = WEIGHTS["jian_chu"]
    ok = eng.get("jian_chu") == exp.get("jian_chu")
    dims["jian_chu"] = (w if ok else 0, w, f"{eng.get('jian_chu')}{'=' if ok else '≠'}{exp.get('jian_chu')}")

    # 日值神（历法真值：青龙起支 + 日支偏移）
    w = WEIGHTS["day_god"]
    ok = eng.get("day_god") == exp.get("day_god")
    dims["day_god"] = (w if ok else 0, w, f"{eng.get('day_god')}{'=' if ok else '≠'}{exp.get('day_god')}")

    # 黄道归属（黄道六神 / 黑道六神）
    w = WEIGHTS["huang_dao"]
    ok = bool(eng.get("huang_dao")) == bool(exp.get("huang_dao"))
    dims["huang_dao"] = (w if ok else 0, w, "一致" if ok else
                         f"黄道{eng.get('huang_dao')}≠基准{exp.get('huang_dao')}")

    # 值宿（历法真值：固定序循环 + 锚点）
    w = WEIGHTS["xiu"]
    ok = eng.get("xiu") == exp.get("xiu")
    dims["xiu"] = (w if ok else 0, w, f"{eng.get('xiu')}{'=' if ok else '≠'}{exp.get('xiu')}")

    # 宜忌命中（规则应用：活动在建除/值神宜忌表之落点）
    w = WEIGHTS["yi_ji"]
    ey, ej = bool(eng.get("yi_hit")), bool(eng.get("ji_hit"))
    xy, xj = bool(exp.get("yi_hit")), bool(exp.get("ji_hit"))
    hits = (ey == xy) + (ej == xj)
    if hits == 2:
        vs, note = w, f"宜{ey}/忌{ej} 一致"
    elif hits == 1:
        vs, note = int(w * 0.5), f"宜{ey}/{ej}≠基准{xy}/{xj} 半中"
    else:
        vs, note = 0, f"宜{ey}/{ej}≠基准{xy}/{xj}"
    dims["yi_ji"] = (vs, w, note)

    # 综合方向（规则应用：黄黑道±1 + 建除宜忌±1 + 星宿±0.5，阈值裁决）
    w = WEIGHTS["verdict"]
    ed, xd = _direction(eng.get("verdict")), _direction(exp.get("verdict"))
    if ed == xd:
        vs, note = w, "方向一致"
    elif ed == 0:
        vs, note = int(w * 0.33), "引擎中性回避"
    else:
        vs, note = 0, "方向相反"
    dims["verdict"] = (vs, w, f"{eng.get('verdict')}/{exp.get('verdict')} {note}")
    return dims


def evaluate(engine_out: dict, label: str, ids: list[str], verbose: bool) -> dict:
    """择吉古籍案例对齐评分（框架与 N/A 口径见 yishu_core.eval）。"""
    base = {c["id"]: c for c in case_runner.load_cases()}
    return run_eval(engine_out, base, ids, WEIGHTS, score_case, MODEL, label, verbose)


def _count(ids: list[str], **match) -> int:
    """按字段计数（口径披露用）。"""
    return sum(1 for c in case_runner.load_cases()
               if c["id"] in ids and all(c.get(k) == v for k, v in match.items()))


def provenance_note(label: str, ids: list[str], res: dict) -> None:
    """报分前先披露口径（AGENTS.md 铁律三：必带集合名 + n + 是否参与调参）。

    n < 20 不报百分比；并显式声明本集六维全部是「历法真值 + 本仓规则表」，
    expected 可由引擎确定性复算（审计实测 16/16 全等）。
    """
    meta = case_runner.load_meta()
    prov = meta.get("_provenance") or {}
    n = res.get("n") or 0
    n_book = _count(ids, provenance="book_original")
    n_synth = _count(ids, provenance="engine_derived")
    print("\n[口径披露]")
    print(f"  集合名：{label}；n={n}（古籍日例应验 {n_book} 例 / 机械因子+规则表构造 {n_synth} 例）；"
          f"{'参与过调参（tune）' if label == 'tune' else '未参与调参（holdout）'}")
    print("  分数含义：本集为**机械因子 + 规则表自洽回归数**，不是古籍案例对齐分，"
          "更不是现实预测命中率。")
    if prov.get("self_consistent_dims"):
        print(f"  ⚠ 自洽项（expected 与引擎同源，命中≠独立判断正确）："
              f"{'、'.join(prov['self_consistent_dims'])}"
              f"——六维权重合计 100/100；expected 可由引擎确定性复算。")
    if prov.get("tune_holdout_leakage"):
        print(f"  ⚠ 切分泄漏：{prov['tune_holdout_leakage']}")
    if n < 20:
        print(f"  ⚠ n={n} < 20 → 本集**不发百分比**，只报命中数；下方百分比仅供参考，"
              f"不构成可检验的泛化证据。")


def hits_summary(res: dict) -> None:
    """n<20 时的诚实读数：逐维度报 命中/适用、N/A。"""
    if not res.get("dims"):
        return
    print("  逐维度命中数（n<20 的正确读数）：")
    for k, v in res["dims"].items():
        print(f"    {k:<10s} {v['full']}/{v['applicable']} 命中，N/A {v['na']}")


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="择吉古籍案例对齐评分（非现实预测命中率）")
    ap.add_argument("--split", choices=["tune", "holdout", "all"], default="all")
    ap.add_argument("--ids", nargs="*", help="指定案例 ID，优先于 --split")
    ap.add_argument("--stage", choices=["run", "score", "all"], default="all")
    ap.add_argument("--engine-file", type=Path, help="已有的引擎输出（配合 --stage score）")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--save", action="store_true", help="写出 JSON 明细到 data/cases/")
    args = ap.parse_args()

    if args.ids:
        ids, label = args.ids, "custom"
    else:
        ids, label = case_runner.load_ids(args.split), args.split

    if args.stage == "score" and args.engine_file:
        loaded = json.loads(Path(args.engine_file).read_text(encoding="utf-8"))
        engine_out = loaded.get("engine_output", loaded)
        available = [c.get("id") for c in engine_out.get("cases", [])]
        ids = [i for i in ids if i in available] or available
        label = f"{label}(cached)"
    else:
        print(f"运行 {len(ids)} 例（{label}）…")
        engine_out = case_runner.run_ids(ids)

    res = evaluate(engine_out, label, ids, args.verbose)
    report(res)
    if res["avg"] is None:
        print("无可用结果")
        return 1

    provenance_note(label, ids, res)
    if (res.get("n") or 0) < 20:
        hits_summary(res)

    errored = [e["id"] for e in engine_out.get("errors", [])]
    if errored:
        print(f"\n引擎报错 {len(errored)} 例：{', '.join(errored)}")
    print("提示：本分数衡量与案例库要点的一致性，不代表现实预测命中率。")

    if args.save:
        out = OUT_DIR / f"eval_{label}.json"
        out.write_text(json.dumps({"results": res, "engine_output": engine_out},
                                  ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("明细 →", out)
    return 1 if errored else 0


if __name__ == "__main__":
    raise SystemExit(main())
