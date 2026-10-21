# -*- coding: utf-8 -*-
"""窗化读数：主应期 top-k 覆盖曲线 vs 随机基线（第一百八十一批）。

背景：外部集上 top-1 与随机持平（27.3% vs 31.1%），但候选池覆盖 88.6%——即**选支有信号、
排序没有**。若产品断言从「top-1 单日」改为「top-k 日窗」，断言强度=窗覆盖率，本工具给出
其现算读数（复用 `evaluate.yingqi_discrimination` 的 additive `coverage_by_k` 字段，
口径唯一、不另建测量管道），每点带 Wilson 95%CI 与 k/12 均匀随机基线对照。

纯读数工具：不参与评分、不触任何门基线；外部集只报数不设门槛（§四.3）。

    python dev_tools/window_report.py
    python dev_tools/window_report.py --splits wikisource_holdout tune
"""
from __future__ import annotations

import argparse
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
from outcome import MIN_N_FOR_CONCLUSION, wilson  # noqa: E402

DEFAULT_SPLITS = ("wikisource_holdout", "zengshan_dz_holdout", "tune", "holdout")
TUNED = {"tune", "holdout"}


def measure(split: str):
    ids = case_runner.load_ids(split)
    if not ids:
        print("× split=%s 解析后 0 例——先查 case_splits.json 的登记，0 例≠0% 命中" % split)
        return None
    by_id = {c["id"]: c for c in case_runner.load_cases()}
    outs, errs = [], 0
    for cid in ids:
        try:
            outs.append(case_runner.run_case(by_id[cid]))
        except Exception as e:  # noqa: BLE001 —— 单例失败不吞：计入 errs 并显形
            errs += 1
            outs.append({"id": cid, "error": str(e)})
    disc = evaluate.yingqi_discrimination({"cases": outs}, ids)
    if not disc:
        print("× split=%s 引擎产出 0 例可评（ errs=%d）——只报数不猜" % (split, errs))
        return None
    print("═ %s（%s）═ 评 %d 例｜引擎错 %d"
          % (split, "内部集·参与过口径史" if split in TUNED else "外部原本集·永不调参",
             disc.get("cases_with_yingqi", 0), errs))
    cov = disc.get("coverage_by_k") or {}
    print("  k  覆盖率(窗断言强度)      Wilson95%CI          随机k/12  超出")
    for key in ("top1", "top2", "top3", "top4", "top5"):
        c = cov.get(key)
        if not c or not c["n"]:
            continue
        k = int(key[3])
        lo, hi = wilson(c["hits"], c["n"])
        flag = "样本不足(<%d)" % MIN_N_FOR_CONCLUSION if c["n"] < MIN_N_FOR_CONCLUSION else "n 达标"
        print("  %d  %3d/%d = %5.1f%%  [%5.1f–%5.1f]  %5.1f%%  %+5.1fpt  %s"
              % (k, c["hits"], c["n"], c["rate"], lo * 100, hi * 100,
                 c["random_rate"], c["rate"] - c["random_rate"], flag))
    print("  池均值=%.1f/12｜全池 loose=%.1f%%｜全池随机=%.1f%%"
          % (disc.get("avg_candidate_set_size", 0),
             disc.get("loose_hit_rate") or 0,
             disc.get("random_full_coverage_expectancy") or 0))
    return disc


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="主应期窗化读数（top-k 覆盖 vs k/12 随机）")
    ap.add_argument("--splits", nargs="*", default=list(DEFAULT_SPLITS))
    args = ap.parse_args()
    got = 0
    for s in args.splits:
        if measure(s) is not None:
            got += 1
    print("\n注：覆盖率与名次均取引擎**自声明池**按书内名次计算；断言若窗化，须先把 k 与判据"
          "写进封存（prospective），不得看结果后挑 k。读数不构成现实命中率（铁律三）。")
    return 0 if got else 1


if __name__ == "__main__":
    raise SystemExit(main())
