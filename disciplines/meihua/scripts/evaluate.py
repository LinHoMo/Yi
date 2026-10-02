# -*- coding: utf-8 -*-
"""梅花易数·古籍案例对齐评分（tune / holdout 分别出分，禁止混分）。

    python scripts/evaluate.py --split all
    python scripts/evaluate.py --split tune --verbose
    python scripts/evaluate.py --split holdout
    python scripts/evaluate.py --stage score --engine-file data/cases/eval_all.json

口径说明（务必连同分数一起阅读，AGENTS.md 铁律三）：
  本脚本衡量的是**引擎输出与古籍案例要点的一致性**，不是现实世界预言命中率。
  基准未记录某维度（如物类断不考吉凶、朝夕之故不取数应）时该维度记 N/A，
  从分母剔除——不得把"基准没要求"算成"引擎答对"。

维度与权重（单一真值源，总和 100）：
  体用关系 30 / 吉凶方向 30 / 生体之卦 15 / 克体之卦 15 / 数应 10
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
    "relation": 30,
    "verdict": 30,
    "sheng_ti": 15,
    "ke_ti": 15,
    "timing": 10,
}

MODEL = "strict"


def _na(value) -> bool:
    return value in (None, "", "?", [])


def _set_hit(offered, needed) -> tuple[float, str]:
    """集合命中：全含满分；半数以上含 0.66；否则 0（不给"多列即多中"的骑墙分）。"""
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

    # 体用关系
    w = WEIGHTS["relation"]
    x_rel = exp.get("relation")
    if _na(x_rel):
        dims["relation"] = (0, 0, "基准未记关系 → N/A")
    else:
        ok = eng.get("relation") == x_rel
        dims["relation"] = (w if ok else 0, w,
                            f"{eng.get('relation')}{'=' if ok else '≠'}{x_rel}")

    # 吉凶方向
    w = WEIGHTS["verdict"]
    ed, xd = verdict_direction(eng.get("verdict")), verdict_direction(exp.get("verdict"))
    if _na(exp.get("verdict")):
        # 物类断（如扣门借物占只断何物）不考吉凶 → N/A
        dims["verdict"] = (0, 0, "基准未记吉凶（物类断）→ N/A")
    else:
        if ed == xd:
            vs, note = w, "方向一致"
        elif ed * xd > 0:
            vs, note = int(w * 0.8), "同向异强"
        elif ed == 0:
            vs, note = int(w * 0.3), "引擎中性回避"
        else:
            vs, note = 0, "方向相反"
        dims["verdict"] = (vs, w, f"{eng.get('verdict')}/{exp.get('verdict')} {note}")

    # 生体/克体之卦（集合命中）
    for dim, key in (("sheng_ti", "sheng_ti"), ("ke_ti", "ke_ti")):
        w = WEIGHTS[dim]
        needed = [str(x) for x in (exp.get(key) or [])]
        if not needed:
            dims[dim] = (0, 0, "基准未记 → N/A")
        else:
            ratio, note = _set_hit(eng.get(key) or [], needed)
            dims[dim] = (int(w * ratio), w, note)

    # 数应（《占卜总诀》动静定应期；基准按"花朝夕之故"不取数应 → N/A）
    w = WEIGHTS["timing"]
    x_t = exp.get("timing")
    if _na(x_t):
        dims["timing"] = (0, 0, "基准未记应期 → N/A")
    else:
        xv = x_t.get("value") if isinstance(x_t, dict) else x_t
        ev = eng.get("numerical_timing")
        ok = ev is not None and int(ev) == int(xv)
        dims["timing"] = (w if ok else 0, w,
                          f"{'命中' if ok else f'{ev} vs {xv}'}")
    return dims


def evaluate(engine_out: dict, label: str, ids: list[str], verbose: bool) -> dict:
    """梅花古籍案例对齐评分（框架与 N/A 口径见 yishu_core.eval，此处只给维度比较）。"""
    base = {c["id"]: c for c in case_runner.load_cases()}
    return run_eval(engine_out, base, ids, WEIGHTS, score_case, MODEL, label, verbose)


def _count(ids: list[str], **match) -> int:
    """按字段计数（用于口径披露：多少例是原书应验、多少例是构造校验）。"""
    return sum(1 for c in case_runner.load_cases()
               if c["id"] in ids and all(c.get(k) == v for k, v in match.items()))


def provenance_note(label: str, ids: list[str], res: dict) -> None:
    """报分前先披露口径（AGENTS.md 铁律三：必带集合名 + n + 是否参与调参）。

    n < 20 时不报百分比，只报命中数/适用数——20 例以下的百分比是伪精度。
    同时点明本集的自洽项：这些维度上 expected 与引擎同源，命中的是"是否与规则表一致"，
    不是"是否与古籍原断一致"。
    """
    meta = case_runner.load_meta()
    n = res.get("n") or 0
    prov = meta.get("_provenance") or {}
    n_book = _count(ids, provenance="book_original")
    n_synth = _count(ids, provenance="engine_derived")
    if label == "tune":
        tuning = "参与过调参（tune）"
    elif label == "external_holdout":
        tuning = "未参与调参（外部独立集，永不调参）"
    else:
        tuning = "未参与调参（holdout）"
    print("\n[口径披露]")
    print(f"  集合名：{label}；n={n}（原书应验 {n_book} 例 / 由引擎口径构造 {n_synth} 例）；{tuning}")
    print("  分数含义：引擎输出与案例库要点的**对齐分**，不是现实预测命中率。")
    if label == "external_holdout":
        # 外部独立集的 expected 全部取自《梅花易数》原书（book_original），
        # 与引擎实现不同源，是真正的独立对齐校验——不报"自洽项"。
        print("  独立性：本集 expected 全部源自《梅花易数》卷三原书（book_original），"
              "与引擎实现不同源；命中=引擎与古籍原断一致，是独立对齐证据（非同义反复）。")
        print("  口径收窄：卷三·變卦式八則为「物类断」且部分互变陈述采用非标准口径，"
              "故 verdict 维度整体 N/A，归妹·夬·履 的 生体/克体 维度 N/A；"
              "仅 体用关系（4 例全维度适用）+ 革 的 生体(艮)/克体(离) 为可对齐维度。")
    elif prov.get("self_consistent_dims"):
        print(f"  自洽项（expected 与引擎同源，命中≠独立判断正确）："
              f"{'、'.join(prov['self_consistent_dims'])}")
    if prov.get("tune_holdout_leakage") and label != "external_holdout":
        print(f"  ⚠ 切分泄漏：{prov['tune_holdout_leakage']}")
    if n < 20:
        print(f"  ⚠ n={n} < 20 → 本集**不发百分比**，只报命中数；下方百分比仅供参考，"
              f"不构成可检验的泛化证据。")


def hits_summary(res: dict, ids: list[str]) -> None:
    """n<20 时的诚实读数：逐维度报 命中/适用、N/A。"""
    if not res.get("dims"):
        return
    print("  逐维度命中数（n<20 的正确读数）：")
    for k, v in res["dims"].items():
        print(f"    {k:<12s} {v['full']}/{v['applicable']} 命中，N/A {v['na']}")


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="梅花易数古籍案例对齐评分（非现实预测命中率）")
    ap.add_argument("--split", choices=["tune", "holdout", "external_holdout", "all"], default="all")
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
        hits_summary(res, ids)

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
