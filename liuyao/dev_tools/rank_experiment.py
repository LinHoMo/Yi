# -*- coding: utf-8 -*-
"""名次键实验（第一百九十批·C1）——预声明四键，tune 选择一次，外部只报数不回碰。

协议（写死，先于任何读数）：
  1. 候选键恰四个（KEYS），不许加键、不许看结果换键——加键＝对 tune 的多重比较，
     外部一次报数即告终；再要试新键属新预注册实验，登记新批次号。
  2. 选择集＝tune（唯一许可）；评分口径＝与 181 批支池 top-1 同式（同单位池名次）。
  3. 平局（含打平于现行键）→ 判现行键胜（默认不变更）。
  4. 胜出键若≠现行：本批**不改引擎**——换序是引擎改动，按 §四 须金标准逐格对拍＋
     两集出分另批做；本实验只交付「哪个键在 tune 上更强、外部一次性读数差多少」的证据。
  5. 外部集（wikisource_holdout/zengshan_dz_holdout）只跑一次、只报数（§四.3），
     此后任何分析引用本实验都须注明"一次性读数"。

    python dev_tools/rank_experiment.py
    python dev_tools/rank_experiment.py --selftest
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
sys.path.insert(0, str(HERE))
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
import case_runner  # noqa: E402
import evaluate  # noqa: E402
from outcome import wilson  # noqa: E402


def _pool_by_unit(eng, exp):
    x = str((exp or {}).get("yingqi") or "")
    unit = evaluate._expected_unit(x)
    m = evaluate.YQ_UNIT_RE.search(x)
    needed = [m.group(1)] if m else evaluate._branches_in(x)
    pool = evaluate._offered_branches(evaluate._unit_pool(eng, unit))
    return needed, pool, unit


def moving_branches(case, eng):
    """动爻地支（本卦发动之支；化出支不算——键定义先行声明在此）。"""
    try:
        hx = case.get("hexagram") or {}
        yao = case_runner.hex2yao(hx.get("original"), hx.get("changed"))
        if yao is None:
            return set()
        dt = case_runner.resolve_case_time(case)["dt"]
        from engine import build_hexagram_result
        h = build_hexagram_result(yao, "", "manual", dt.year, dt.month, dt.day, dt.hour)
        lines = (h.get("original_hexagram") or {}).get("yao_lines") or []
        return {l.get("earthly_branch") for l in lines
                if l.get("is_moving") and l.get("earthly_branch")}
    except Exception:
        return set()


def rerank(pool, key, feats):
    b, d, mv = feats
    if key == "k1_current":
        return pool
    def rank(br):
        return 0 if ((key == "k2_usegod" and br == b) or
                     (key == "k3_daybranch" and br == d) or
                     (key == "k4_moving" and br in mv)) else 1
    # 稳定排序：命中特征者前置，池内原相对次序保持（平局不引入新信息）
    return sorted(pool, key=rank)


KEYS = ("k1_current", "k2_usegod", "k3_daybranch", "k4_moving")   # 恰四个，预声明冻结


def collect(split):
    ids = case_runner.load_ids(split)
    by_id = {c["id"]: c for c in case_runner.load_cases()}
    rows = []
    for cid in ids:
        case = by_id.get(cid) or {}
        try:
            eng = case_runner.run_case(case)
        except Exception:
            continue
        needed, pool, unit = _pool_by_unit(eng, case.get("expected") or {})
        if not needed or not pool:
            continue
        feats = (eng.get("use_god_branch") or "",
                 ((eng.get("four_pillars") or {}).get("day_stem_branch") or "")[-1:],
                 moving_branches(case, eng))
        rows.append({"id": cid, "needed": needed, "pool": pool, "feats": feats})
    return rows


def top1_hits(rows, key):
    hit = 0
    for r in rows:
        first = rerank(r["pool"], key, r["feats"])[0]
        hit += 1 if first in r["needed"] else 0
    return hit, len(rows)


def run_protocol() -> int:
    tune = collect("tune")
    if not tune:
        print("× tune 可评 0 例——判红")
        return 1
    print("═ 选择集 tune（%d 例可评）═" % len(tune))
    score = {}
    for k in KEYS:
        h, n = top1_hits(tune, k)
        score[k] = (h, n)
        print("  %-12s %d/%d = %.1f%%" % (k, h, n, h * 100 / n))
    best = max(score, key=lambda k: score[k][0])
    winner = best if score[best][0] > score["k1_current"][0] else "k1_current"  # 平局判现行
    print("  → 胜出键（平局默认现行）：%s" % winner)
    for split in ("wikisource_holdout", "zengshan_dz_holdout"):
        rows = collect(split)
        if not rows:
            print("  %s：可评 0 例（显形）" % split)
            continue
        (h1, n) = top1_hits(rows, "k1_current")
        (h2, _) = top1_hits(rows, winner)
        lo1, hi1 = wilson(h1, n)
        lo2, hi2 = wilson(h2, n)
        print("═ 外部一次性报数 %s（%d 例，永不调参）═" % (split, n))
        print("  现行键  %d/%d = %.1f%% [CI %.1f–%.1f]" % (h1, n, h1 * 100 / n, lo1 * 100, hi1 * 100))
        print("  胜出键  %d/%d = %.1f%% [CI %.1f–%.1f]  Δ%+.1fpt"
              % (h2, n, h2 * 100 / n, lo2 * 100, hi2 * 100, (h2 - h1) * 100.0 / n))
        if winner == "k1_current":
            print("  （胜出键即现行：两行同值属预期，非报数错误）")
    print("  注：本实验不改引擎。若胜出键≠现行，换序另批按 §四 全验收（金标准逐格对拍+两集出分）。")
    return 0


def cmd_selftest() -> int:
    fails = []
    pool = ["午", "辰", "卯"]
    if rerank(pool, "k1_current", ("辰", "午", set())) != pool:
        fails.append("k1 不保持原序")
    if rerank(pool, "k2_usegod", ("辰", "午", set()))[0] != "辰":
        fails.append("k2 择支前置失败")
    if rerank(pool, "k3_daybranch", ("辰", "午", set()))[0] != "午":
        fails.append("k3 日辰前置失败")
    if rerank(pool, "k4_moving", ("辰", "午", {"卯"}))[0] != "卯":
        fails.append("k4 动爻前置失败")
    if rerank(pool, "k2_usegod", ("亥", "午", set())) != pool:
        fails.append("键特征不存在时未保持原序（稳定性破）")
    if len(KEYS) != 4 or "k1_current" not in KEYS:
        fails.append("候选键集合被改动（协议要求恰四键含现行）")
    print("√ selftest：四键行为/稳定性/协议锁 全过" if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="名次键预注册实验（四键锁死、tune 选择、外部一次报数）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return cmd_selftest()
    return run_protocol()


if __name__ == "__main__":
    raise SystemExit(main())
