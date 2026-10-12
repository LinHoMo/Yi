# -*- coding: utf-8 -*-
"""应期候选池「信息量」硬门：把铺量涨分这条路堵死。

为什么需要它（2026-10-10 实测）：本仓一直**只报**候选集平均大小与随机全覆盖期望，
没有任何东西拦住"把池子铺大"的改法。本批用一个运行时补丁做了对照实验：
把 `_collect_key_branches` 收集的原始候选直接并进 `key_branches`——

    tune   候选池 4.5/12 → **11.4/12**，随机全覆盖期望 37.7% → **94.6%**，
           strict 对齐分 97.3% → **97.5%**（+0.2），
           top-1 命中 64.7% 不变，基准应支平均名次 **1.53 → 2.00（变差）**
    外部集 候选池 3.7/12 → 7.2/12，随机期望 30.7% → 60.1%

也就是说：**铺到 12 支里的 11.4 支只换来 +0.2 分**，而名次这一项"才见真章"的读数在退步。
分数基线又是"只准前进"的，这 +0.2 会被登记成"抬高基线"——没有硬门时，门禁自己会奖励作弊。
本门把两条无信息量判据变成红线（口径来自 `scripts/evaluate.py:yingqi_discrimination` 的注释）。

    python dev_tools/check_yingqi_information.py             # 量 tune + 外部两集
    python dev_tools/check_yingqi_information.py --selftest  # 负例：证明铺量样本会被判红
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DISC / "scripts"))
sys.path.insert(0, str(DISC / "core"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POOL_MAX = 6.0        # 平均候选池上限：十二支里超过半池就不再是"择一"而是"列全"
EDGE_MIN = 20.0       # loose 全覆盖 − 随机铺量期望，至少要拉开这么多分（百分点）
# 第八十批补：以上两条只约束**日支阶梯**。日历日期层（`yingqi_dates.dates`）曾长期无人管，
# 而报告应期段优先读它——不封顶等于把"铺量涨分"这条路从日期侧留着。
DATES_MAX = 8.0       # 平均日期条数上限（现状实测 ~6.9：5 条时间序 ＋最多 2 条阶梯追加）
DATE_BRANCH_MAX = 9.0 # 日期层平均覆盖地支数上限/12（覆盖 12 支＝把十二天列全）


def date_stats(cases: list) -> dict:
    """纯函数：从逐例产出里量日历日期层的宽度（条数与覆盖支数）。0 例时如实报 0。"""
    n = cnt = br = 0
    for c in cases or []:
        yd = (c or {}).get("yingqi_dates")
        dates = yd.get("dates") if isinstance(yd, dict) else None
        if not dates:
            continue
        n += 1
        cnt += len(dates)
        br += len({str(d.get("branch") or "") for d in dates if isinstance(d, dict)})
    if not n:
        return {"cases_with_dates": 0}
    return {"cases_with_dates": n, "avg_date_count": round(cnt / n, 2),
            "avg_date_branches": round(br / n, 2)}


def assess(label: str, disc: dict, dstat: dict | None = None) -> list[str]:
    """纯函数：从一份 discrimination 读数里推出违规清单（便于负例直接喂构造数据）。"""
    n = disc.get("cases_with_yingqi") or 0
    if not n:
        return [f"{label}：0 例可检——本门在这里等于没跑，不判通过"]
    bad: list[str] = []
    size = disc.get("avg_candidate_set_size")
    rnd = disc.get("random_full_coverage_expectancy")
    loose = disc.get("loose_hit_rate")
    if size is not None and size > POOL_MAX:
        bad.append(f"{label}：候选池平均 {size}/12 > {POOL_MAX}——铺量，不是择一")
    if loose is not None and rnd is not None and (loose - rnd) < EDGE_MIN:
        bad.append(f"{label}：loose 全覆盖 {loose}% 距随机铺量期望 {rnd}% 只有 "
                   f"{round(loose - rnd, 1)} 分（要求 ≥{EDGE_MIN}）——召回分等于没判断")
    if dstat is not None:
        dn = dstat.get("cases_with_dates") or 0
        if not dn:
            bad.append(f"{label}：日期层 0 例可检——本门在日历层等于没跑，不判通过")
        else:
            dc = dstat.get("avg_date_count")
            db = dstat.get("avg_date_branches")
            if dc is not None and dc > DATES_MAX:
                bad.append(f"{label}：日历日期平均 {dc} 条 > {DATES_MAX}——日期层铺量")
            if db is not None and db > DATE_BRANCH_MAX:
                bad.append(f"{label}：日期层平均覆盖 {db}/12 支 > {DATE_BRANCH_MAX}"
                           "——把十二天列全不是定应期")
    return bad


def measure(label: str, split: str) -> dict:
    import case_runner
    import evaluate
    ids = case_runner.load_ids(split)
    engine_out = case_runner.run_ids(ids, verbose=False)
    disc = evaluate.yingqi_discrimination(engine_out, ids) or {}
    dstat = date_stats(engine_out.get("cases") or [])
    disc["_date_stats"] = dstat
    print(f"  {label}({split}) n={disc.get('cases_with_yingqi', 0)} "
          f"候选池={disc.get('avg_candidate_set_size')}/12 "
          f"top-1={disc.get('top1_hit_rate')}% 平均名次={disc.get('avg_rank_of_correct')} "
          f"loose={disc.get('loose_hit_rate')}% 随机期望={disc.get('random_full_coverage_expectancy')}% "
          f"｜日期层 n={dstat.get('cases_with_dates', 0)} "
          f"平均条数={dstat.get('avg_date_count', '—')} 覆盖支={dstat.get('avg_date_branches', '—')}/12")
    return disc


def selftest(problems: list[str]) -> None:
    """负例三件：铺量样本必须判红、现状形态必须放行、0 例必须自报。"""
    padded = {"cases_with_yingqi": 17, "avg_candidate_set_size": 11.4,
              "top1_hit_rate": 64.7, "avg_rank_of_correct": 2.0,
              "random_full_coverage_expectancy": 94.6, "loose_hit_rate": 95.0}
    ok = {"cases_with_yingqi": 17, "avg_candidate_set_size": 4.5,
          "top1_hit_rate": 64.7, "avg_rank_of_correct": 1.53,
          "random_full_coverage_expectancy": 37.7, "loose_hit_rate": 68.8}
    empty = {"cases_with_yingqi": 0}
    if not assess("铺量负例", padded):
        problems.append("负例失效：4.5→11.4 支、只赢随机期望 0.4 分的形态没被判红")
    if assess("现状负例", ok):
        problems.append("负例假阳性：现状（池 4.5/12、领先随机 31 分）被本门判红，阈值不成立")
    if not any("0 例可检" in x for x in assess("空跑负例", empty)):
        problems.append("空跑没自报：本门在 0 例时也报通过")
    # 日期层三件（第八十批新增）：铺量必须判红、现状不得误伤、0 例必须自报
    d_pad = {"cases_with_dates": 20, "avg_date_count": 12.0, "avg_date_branches": 11.4}
    d_ok = {"cases_with_dates": 17, "avg_date_count": 6.9, "avg_date_branches": 6.2}
    d_none = {"cases_with_dates": 0}
    if not assess("日期层铺量负例", ok, d_pad):
        problems.append("日期层负例失效：平均 12 条、覆盖 11.4/12 支的形态没被判红")
    if assess("日期层现状负例", ok, d_ok):
        problems.append(f"日期层假阳性：现状形态（{d_ok['avg_date_count']} 条、"
                        f"{d_ok['avg_date_branches']} 支）被本门判红，阈值不成立")
    if not any("日期层 0 例" in x for x in assess("日期层空跑负例", ok, d_none)):
        problems.append("日期层空跑没自报：日期层 0 例时本门等于没跑，却报通过")
    print("  [selftest] 负例已跑")


def main() -> int:
    ap = argparse.ArgumentParser(description="应期候选池信息量硬门")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    problems: list[str] = []
    measured = 0
    for label, split in (("tune", "tune"), ("wikisource_holdout", "wikisource_holdout")):
        try:
            disc = measure(label, split)
        except Exception as exc:      # 量不到 = 门没跑，必须响，不能留下一片绿
            problems.append(f"{label}：读数失败（{type(exc).__name__}: {exc}），本门未检视该集")
            continue
        measured += 1
        problems.extend(assess(label, disc, disc.get("_date_stats")))
    if args.selftest:
        selftest(problems)
    if measured == 0:
        print("  × 两个集都没量到——本门等于没跑，不判通过")
        return 1
    for p in problems:
        print(f"  × {p}")
    print(f"  阈值：候选池平均 ≤{POOL_MAX}/12，loose 全覆盖须领先随机铺量期望 ≥{EDGE_MIN} 分")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
