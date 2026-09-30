# -*- coding: utf-8 -*-
"""小六壬·古籍案例对齐评分（tune / holdout 分别出分，禁止混分）。

    python scripts/evaluate.py --split all
    python scripts/evaluate.py --split tune --verbose
    python scripts/evaluate.py --split holdout
    python scripts/evaluate.py --stage score --engine-file data/cases/eval_all.json

口径说明（务必连同分数一起阅读，AGENTS.md 铁律三）：
  本脚本衡量的是**引擎输出与古籍案例要点的一致性**，不是现实世界预言命中率。
  基准未记录某维度（综合判断例不记单一吉凶/事类）时该维度记 N/A，从分母剔除。

维度与权重（单一真值源，总和 100）：
  落宫 30 / 吉凶方向 30 / 事类诀句 20 / 应期主数 20
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

from yishu_core.eval import verdict_direction, run_eval, report  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
import case_runner  # noqa: E402

OUT_DIR = DISC / "data" / "cases"

WEIGHTS = {
    "palace": 30,
    "verdict": 30,
    "topic": 20,
    "timing": 20,
}

MODEL = "strict"


def _na(value) -> bool:
    return value in (None, "", "?", [])


def _set_hit(offered, needed) -> tuple[float, str]:
    """主数集合命中：全含满分；半数以上含 0.66；否则 0。"""
    needed = set(needed)
    if not needed:
        return 0.0, ""
    inter = needed & set(offered)
    ratio = len(inter) / len(needed)
    if ratio >= 1:
        return 1.0, f"{len(inter)}/{len(needed)}"
    if ratio >= 0.5:
        return 0.66, f"{len(inter)}/{len(needed)}"
    return 0.0, f"{len(inter)}/{len(needed)}"


def score_case(eng: dict, exp: dict, model: str) -> dict:
    """单例打分。返回 {dim: (earned, applicable_weight, note)}。"""
    dims: dict[str, tuple[int, int, str]] = {}

    # 落宫（纯机械真值：月上起日、日上起时）
    w = WEIGHTS["palace"]
    x = exp.get("palace")
    ok = eng.get("palace") == x
    dims["palace"] = (w if ok else 0, w, f"{eng.get('palace')}{'=' if ok else '≠'}{x}")

    # 吉凶方向（宫义所定；综合判断例基准不记 → N/A）
    w = WEIGHTS["verdict"]
    if _na(exp.get("verdict")):
        dims["verdict"] = (0, 0, "基准未记吉凶（综合判断例）→ N/A")
    else:
        ed, xd = verdict_direction(eng.get("verdict")), verdict_direction(exp.get("verdict"))
        if ed == xd:
            vs, note = w, "方向一致"
        elif ed * xd > 0:
            vs, note = int(w * 0.8), "同向异强"
        elif ed == 0:
            vs, note = int(w * 0.3), "引擎中性回避"
        else:
            vs, note = 0, "方向相反"
        dims["verdict"] = (vs, w, f"{eng.get('verdict')}/{exp.get('verdict')} {note}")

    # 事类诀句（文本一致：测的是『按事类取对诀句』的管线）
    w = WEIGHTS["topic"]
    xl = (exp.get("topic_line") or "").strip()
    if not xl:
        dims["topic"] = (0, 0, "基准未记事类（综合判断例）→ N/A")
    else:
        ok = (eng.get("topic_line") or "").strip() == xl
        dims["topic"] = (w if ok else 0, w, "命中" if ok else
                         f"{eng.get('topic_line')} ≠ {xl[:24]}")

    # 应期主数（宫义主数，集合命中）
    w = WEIGHTS["timing"]
    needed = [int(x) for x in (exp.get("timing") or [])]
    if not needed:
        dims["timing"] = (0, 0, "基准未记主数 → N/A")
    else:
        ratio, note = _set_hit(eng.get("timing") or [], needed)
        dims["timing"] = (int(w * ratio), w, note)
    return dims


def evaluate(engine_out: dict, label: str, ids: list[str], verbose: bool) -> dict:
    """小六壬古籍案例对齐评分（框架与 N/A 口径见 yishu_core.eval）。"""
    base = {c["id"]: c for c in case_runner.load_cases()}
    return run_eval(engine_out, base, ids, WEIGHTS, score_case, MODEL, label, verbose)


def _count(ids: list[str], **match) -> int:
    """按字段计数（口径披露用：多少例取自书上原例、多少例是按规则表构造）。"""
    return sum(1 for c in case_runner.load_cases()
               if c["id"] in ids and all(c.get(k) == v for k, v in match.items()))


def provenance_note(label: str, ids: list[str], res: dict) -> None:
    """报分前先披露口径（AGENTS.md 铁律三：必带集合名 + n + 是否参与调参）。

    n < 20 不报百分比；并显式声明本集四维全部与引擎同源。
    """
    meta = case_runner.load_meta()
    prov = meta.get("_provenance") or {}
    n = res.get("n") or 0
    n_book = _count(ids, provenance="book_original")
    n_synth = _count(ids, provenance="engine_derived")
    print("\n[口径披露]")
    print(f"  集合名：{label}；n={n}（书上原例 {n_book} 例 / 按规则表构造 {n_synth} 例）；"
          f"{'参与过调参（tune）' if label == 'tune' else '未参与调参（holdout）'}")
    print("  分数含义：引擎输出与案例库要点的**对齐分**，不是现实预测命中率。")
    if prov.get("self_consistent_dims"):
        print(f"  ⚠ 自洽项（expected 与引擎同源，命中≠独立判断正确）："
              f"{'、'.join(prov['self_consistent_dims'])}"
              f"——本集四维权重合计 100/100，本读数衡量的是「引擎与自己的规则表是否一致」。")
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
    ap = argparse.ArgumentParser(description="小六壬古籍案例对齐评分（非现实预测命中率）")
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
    print("提示：本分数衡量与古籍案例要点的一致性，不代表现实预测命中率。")

    if args.save:
        out = OUT_DIR / f"eval_{label}.json"
        out.write_text(json.dumps({"results": res, "engine_output": engine_out},
                                  ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("明细 →", out)
    return 1 if errored else 0


if __name__ == "__main__":
    raise SystemExit(main())
