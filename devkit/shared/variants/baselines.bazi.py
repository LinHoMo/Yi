# -*- coding: utf-8 -*-
"""八字基线库（第一百八十七批·A3）——一行规则丈量八字判断维，配对 McNemar 与六爻侧同构。

要回答的问题：八字 holdout 97.6% 里，历法/定义维（pillars/ten_gods/hidden_stems）是
表驱动满分（README 自注），真正带判断含量的 pattern（成格/破格）、cong_ge（从/正）、
tiaohou（主神）三维，**赢一行规则多少**？每基线与引擎逐例配对，不一致对做精确 McNemar。

基线（边际/多数类只取 tune——泄漏防护自测锁死；外部集只报数不设门槛，§四.3）：
  pattern   ：tune 多数类（成/破）｜随机 1/2
  cong_ge   ：tune 多数类（从/正）｜随机 1/2
  tiaohou   ：tune 无条件边际众数主神｜**同月支条件众数**（书表若本质是查表，该基线≈地板）｜随机 1/10
零耦合合同：mcnemar/wilson 公式与六爻侧同源同式，但**各科一份本地实现**（两科内核副本
同规）；selftest 用固定向量与六爻登记值对拍，公式漂移即判红。

    python dev_tools/baselines.py                      # holdout 全维
    python dev_tools/baselines.py --split external_holdout
    python dev_tools/baselines.py --selftest
"""
from __future__ import annotations

import argparse
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
sys.path.insert(0, str(DISC / "core"))
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
import evaluate  # noqa: E402

TUNE_ONLY = ("tune",)   # 边际/多数类唯一许可来源——外部与 holdout 都不许进


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    m = min(b, c)
    p = sum(comb_(n, k) for k in range(m + 1)) / (2.0 ** n) * 2.0
    return min(1.0, p)


def comb_(n: int, k: int) -> int:
    r = 1
    for i in range(k):
        r = r * (n - i) // (i + 1)
    return r


def wilson(hits: int, n: int, z: float = 1.96):
    if n == 0:
        return (0.0, 0.0)
    ph = hits / n
    den = 1 + z * z / n
    ctr = (ph + z * z / (2 * n)) / den
    half = (z / den) * ((ph * (1 - ph) / n + z * z / (4 * n * n)) ** 0.5)
    return (max(ctr - half, 0.0), min(ctr + half, 1.0))


def _bank(ids_of_tune: set):
    def guard(ids):
        leak = [i for i in ids if i not in ids_of_tune]
        if leak:
            raise ValueError("基线边际混入 tune 之外的 id（泄漏）：%s" % leak[:3])
    return guard


def build_banks():
    """从 tune 案例的 expected 造基线答案库：多数类/边际众数/月支条件众数。
    来源锁定 tune（selftest 的泄漏负例验证 _bank 防护本身）。"""
    tune_ids = set(evaluate.load_ids("tune"))
    by_id = {c["id"]: c for c in evaluate.load_cases()}
    rows = [by_id[i] for i in sorted(tune_ids) if i in by_id]
    pat_cnt, cg_cnt, th_cnt, cond = {}, {}, {}, {}
    for c in rows:
        e = c.get("expected") or {}
        if e.get("pattern_cheng_bai") not in (None, "", "N/A"):
            pat_cnt[e["pattern_cheng_bai"]] = pat_cnt.get(e["pattern_cheng_bai"], 0) + 1
        if isinstance(e.get("cong_ge"), bool):
            cg_cnt[e["cong_ge"]] = cg_cnt.get(e["cong_ge"], 0) + 1
        t = e.get("tiaohou")
        if isinstance(t, dict) and t.get("main"):
            th_cnt[t["main"]] = th_cnt.get(t["main"], 0) + 1
            mp = (c.get("pillars") or {}).get("month") or ""
            mz = mp[-1] if mp else ""
            cond.setdefault(mz, {})
            cond[mz][t["main"]] = cond[mz].get(t["main"], 0) + 1
    top = lambda d: max(d, key=d.get) if d else None
    return {"pattern_majority": top(pat_cnt),
            "cong_majority": top(cg_cnt),
            "tiaohou_marginal": top(th_cnt) or "",
            "tiaohou_by_month": {k: top(v) for k, v in cond.items()}}


def dim_engine_hit(res_case_dims, dim):
    v = res_case_dims.get(dim)
    if not v:
        return None
    earned, applicable = v[0], v[1]
    if applicable <= 0:
        return None
    return 1 if earned >= applicable - 1e-9 else 0


def run_split(split: str) -> dict | None:
    by_id = {c["id"]: c for c in evaluate.load_cases()}
    if split == "external_holdout":
        store = evaluate.load_external_store()
        ids = list((store.get("splits") or {}).get("external_holdout") or [])
        for c in store.get("cases") or []:
            by_id.setdefault(c["id"], c)
        if not ids:
            print("× external_holdout 解析 0 例——判红（0 例≠0%）")
            return None
    else:
        ids = evaluate.load_ids(split)
    if not ids:
        print("× split=%s 解析 0 例——判红不空跑" % split)
        return None
    out_eng = evaluate.run_ids(ids, cases_by_id=by_id)
    bank = build_banks()
    percase = {}
    for c in out_eng["cases"]:
        cid = c.get("id")
        case = by_id.get(cid) or {}
        exp = case.get("expected") or {}
        if "error" in c:
            continue
        dims = evaluate.score_case(c, exp, "strict")
        eng = {d: dim_engine_hit(dims, d) for d in ("pattern", "cong_ge", "tiaohou")}
        case_pillars = case.get("pillars") or {}
        mp = str(case_pillars.get("month") or "")          # 案例级为「甲子」串（引擎级是嵌套 dict）
        mzp = mp[-1:] if len(mp) == 2 else ""
        pat_a = bank["pattern_majority"]
        bl = {
            "pattern": {"先验定答成格": 1 if (exp.get("pattern_cheng_bai") == "成格") else 0,
                        "先验定答破格": 1 if (exp.get("pattern_cheng_bai") == "破格") else 0,
                        **({"多数类(tune)": 1 if (exp.get("pattern_cheng_bai") == pat_a) else 0} if pat_a else {})},
            "cong_ge": {"先验定答从": 1 if exp.get("cong_ge") is True else 0,
                        "先验定答不从": 1 if exp.get("cong_ge") is False else 0,
                        **({"多数类(tune)": 1 if (exp.get("cong_ge") is bank["cong_majority"]) else 0}
                           if bank["cong_majority"] is not None else {})},
            "tiaohou": {"定答(tune边际)": 1 if (exp.get("tiaohou") or {}).get("main") == bank["tiaohou_marginal"] else 0,
                        "月支条件众数(tune)": 1 if (exp.get("tiaohou") or {}).get("main") == bank["tiaohou_by_month"].get(mzp) else 0},
        }
        percase[cid] = {"eng": eng, "bl": bl,
                        "na": {d: eng[d] is None for d in eng}}
    if not percase:
        print("× split=%s 可评 0 例——判红" % split)
        return None
    print("═ bazi split=%s｜可评 %d 例 ═" % (split, len(percase)))
    dist = {"pattern": {}, "cong_ge": {}, "tiaohou": {}}
    for cid in percase:
        e = (by_id.get(cid) or {}).get("expected") or {}
        pb = e.get("pattern_cheng_bai")
        if pb:
            dist["pattern"][pb] = dist["pattern"].get(pb, 0) + 1
        if isinstance(e.get("cong_ge"), bool):
            k = "从格" if e["cong_ge"] else "正格"
            dist["cong_ge"][k] = dist["cong_ge"].get(k, 0) + 1
        t = e.get("tiaohou")
        if isinstance(t, dict) and t.get("main"):
            dist["tiaohou"][t["main"]] = dist["tiaohou"].get(t["main"], 0) + 1
    report = {}
    for dim, rkey, rand_p in (("pattern", "pattern", 0.5),
                               ("cong_ge", "cong_ge", 0.5),
                               ("tiaohou", "tiaohou", 0.1)):
        eids = [cid for cid in percase if percase[cid]["eng"][dim] is not None]
        if len(eids) < 5:
            print("  %s：适用 %d 例 <5——只报数不报率（§三 MIN_APPLICABLE 口径）" % (dim, len(eids)))
            report[dim] = {"n": len(eids)}
            continue
        eh = sum(percase[c]["eng"][dim] for c in eids)
        lo, hi = wilson(eh, len(eids))
        d = dist[dim]
        if d:
            mx = max(d.values())
            print("  %s：类分布(本集期望) %s%s" % (dim, d,
                  "  ⚠ 退化：众数占 %.0f%%——本维任何『常数回答』都不弱，判别声称须过这条线"
                  % (mx * 100 / len(eids)) if mx >= 0.9 * len(eids) else ""))
        print("  %s：引擎 %d/%d = %.1f%% [CI %.1f–%.1f]（随机基线 %.1f%%）"
              % (dim, eh, len(eids), eh * 100 / len(eids), lo * 100, hi * 100, rand_p * 100))
        d_rows = {}
        for bname in percase[eids[0]]["bl"][dim]:
            if bname.startswith("随机"):
                continue
            b = sum(1 for c in eids if percase[c]["eng"][dim] == 1 and percase[c]["bl"][dim][bname] == 0)
            cc = sum(1 for c in eids if percase[c]["eng"][dim] == 0 and percase[c]["bl"][dim][bname] == 1)
            bh = sum(percase[c]["bl"][dim][bname] for c in eids)
            p = mcnemar_exact(b, cc)
            d_rows[bname] = {"hit": bh, "rate": round(bh * 100 / len(eids), 1),
                             "b": b, "c": cc, "p": round(p, 3)}
            print("    %-14s %d/%d = %5.1f%% ｜配对 b=%d c=%d McNemar p=%.3f%s"
                  % (bname, bh, len(eids), bh * 100 / len(eids), b, cc, p,
                     "（显著）" if p <= 0.05 else "（未达显著）"))
            if bh > eh:
                print("      ⚠ 常数基线 %s = %.1f%% 高于引擎 %.1f%%——本维读数以「不劣于常数回答」为最低门槛，未过"
                      % (bname, bh * 100 / len(eids), eh * 100 / len(eids)))
        report[dim] = {"n": len(eids), "engine": {"hit": eh, "rate": round(eh * 100 / len(eids), 1)},
                       "baselines": d_rows}
    return report


def cmd_selftest() -> int:
    fails = []
    # 1) 公式与六爻登记向量对拍（同式两实现互证）
    for (b, c), want in (((0, 0), 1.0), ((2, 0), 0.5), ((5, 0), 0.0625)):
        if abs(mcnemar_exact(b, c) - want) > 1e-9:
            fails.append("McNemar 对拍错 %d/%d" % (b, c))
    lo, hi = wilson(12, 44)
    if abs(lo * 100 - 16.3) > 0.6 or abs(hi * 100 - 41.8) > 0.6:
        fails.append("Wilson 与六爻侧同例读数漂移：%r" % ((lo, hi),))
    # 2) 泄漏防护：非 tune id 进 bank 必抛
    ids_t = set(evaluate.load_ids("tune"))
    try:
        _bank(ids_t)([i for i in evaluate.load_ids("holdout") if i not in ids_t][:1] or ["__probe__"])
        fails.append("非 tune id 混入未抛（泄漏防护失效）")
    except ValueError:
        pass
    # 3) bank 构建：tune 无 pattern/cong_ge 期望时对应键必须为 None（不造假多数类基线）
    bank = build_banks()
    if bank["pattern_majority"] is not None or bank["cong_majority"] is not None:
        fails.append("tune 无二元维期望却造出了『多数类』假来源：%r" % bank)
    if not (bank["tiaohou_marginal"] and bank["tiaohou_by_month"]):
        fails.append("tiaohou bank 不齐：%r" % {k: (v if k != "tiaohou_by_month" else len(v))
                                                for k, v in bank.items()})
    print("√ selftest：公式对拍/泄漏必抛/bank 齐备 全过" if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="八字基线×判断维配对对照（读数报告，不进评分面）")
    ap.add_argument("--split", default="holdout",
                    choices=["holdout", "tune", "external_holdout"])
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return cmd_selftest()
    r = run_split(args.split)
    print("\n注：基线命中语义与 score_case 同（该维满分＝命中）；随机基线列为理论值；"
          "读数属古籍吻合面，不构成现实断言（铁律三）。")
    return 0 if r else 1


if __name__ == "__main__":
    raise SystemExit(main())
