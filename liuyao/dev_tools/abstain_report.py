# -*- coding: utf-8 -*-
"""弃权分型读数 v0（第一百九十一批·C2 第一半）——只出观察，不动输出面。

分桶（优先级取主判，先于读数声明——一卦只落一桶）：
  B1_全静   ：本卦无动爻——书自注「六爻不动者，务必求其动而验之」（源L1953），书都嫌难应
  B2_乱动   ：动爻数 >2——《火珠林》乱动法总纲（167/173 批只标象不打分）
  B4_伏神用神：用神不现于本卦（has_use_god_in_hexagram=False）——须查伏，取用链条最长
  B3_两现   ：用神两现及以上（use_god_count≥2）——172 批冻结的取舍序就是为它立的
  B0_常规   ：其余
待检验假设（C2 第二半是否值得做，由本读数裁决）：
  H：弃权桶（B1-B4）的 verdict／top-1 精度显著低于 B0 →「引擎知道自己什么时候不该说」
    有信息量，接线进输出断语层（触发金标准漂移，另批 §四 全验收）值得做；
    无差 → 按 §六.5 结案登记：结构标签不构成弃权信号，C2 停在这里。
零引擎改动、零评分面、不挂门；外部集只报数（§四.3）。

    python dev_tools/abstain_report.py
    python dev_tools/abstain_report.py --selftest
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
from engine import build_hexagram_result  # noqa: E402
from thinking_chain import run_thinking_chain  # noqa: E402
from outcome import wilson  # noqa: E402

SPLITS = ("tune", "holdout", "wikisource_holdout", "zengshan_dz_holdout")
BUCKETS = ("B1_全静", "B2_乱动", "B4_伏神用神", "B3_两现", "B0_常规")


def bucket_of(case) -> str:
    hx = case.get("hexagram") or {}
    yao = case_runner.hex2yao(hx.get("original"), hx.get("changed"))
    if yao is None:
        return "B0_常规"          # 装配不能→不装桶污染读数，量由 err 计数显形
    try:
        dt = case_runner.resolve_case_time(case)["dt"]
    except Exception:
        return "B0_常规"
    h = build_hexagram_result(yao, "", "manual", dt.year, dt.month, dt.day, dt.hour)
    moving = [l for l in (h.get("original_hexagram") or {}).get("yao_lines", []) if l.get("is_moving")]
    tc = run_thinking_chain(h)
    s2 = ((tc.get("thinking_chain") or tc).get("step2_use_god_identification")) or {}
    if not moving:
        return "B1_全静"
    if len(moving) > 2:
        return "B2_乱动"
    if not s2.get("has_use_god_in_hexagram", True):
        return "B4_伏神用神"
    if (s2.get("use_god_count") or 1) >= 2:
        return "B3_两现"
    return "B0_常规"


def run() -> int:
    by_id = {c["id"]: c for c in case_runner.load_cases()}
    agg = {b: {"n": 0, "v_hit": 0, "t_hit": 0, "t_n": 0} for b in BUCKETS}
    for split in SPLITS:
        ids = case_runner.load_ids(split)
        per = {b: {"n": 0, "v_hit": 0, "t_hit": 0, "t_n": 0} for b in BUCKETS}
        err = 0
        for cid in ids:
            case = by_id.get(cid) or {}
            if "expected" not in case:
                continue
            try:
                b = bucket_of(case)
                eng = case_runner.run_case(case)
            except Exception:
                err += 1
                continue
            dims = evaluate.score_case(eng, case.get("expected") or {}, "strict")
            vw, aw, _ = dims.get("verdict", (0, 0, ""))
            yw, ay, _ = dims.get("yingqi", (0, 0, ""))
            per[b]["n"] += 1
            agg[b]["n"] += 1
            if aw:
                per[b]["v_hit"] += 1 if vw >= aw - 1e-9 else 0
                agg[b]["v_hit"] += 1 if vw >= aw - 1e-9 else 0
            if ay:
                per[b]["t_n"] += 1
                agg[b]["t_n"] += 1
                hit = 1 if yw >= ay - 1e-9 else 0
                per[b]["t_hit"] += hit
                agg[b]["t_hit"] += hit
        tot_cases = sum(p["n"] for p in per.values())
        print("═ %s（%d 例装配判卷，err %d）═" % (split, tot_cases, err))
        for b in BUCKETS:
            p = per[b]
            if not p["n"]:
                continue
            vr = p["v_hit"] * 100.0 / p["n"]
            tr = (p["t_hit"] * 100.0 / p["t_n"]) if p["t_n"] else None
            print("  %-10s %3d 例 (%4.1f%%) ｜verdict %5.1f%%｜top-1 %s"
                  % (b, p["n"], p["n"] * 100 / (tot_cases or 1), vr,
                     ("%.1f%%" % tr) if tr is not None else "—"))
    print("═ 合计（跨四集）═")
    for b in BUCKETS:
        p = agg[b]
        if not p["n"]:
            continue
        lo, hi = wilson(p["v_hit"], p["n"])
        tr = (p["t_hit"] * 100.0 / p["t_n"]) if p["t_n"] else None
        print("  %-10s %3d 例｜verdict %5.1f%% [CI %.1f–%.1f]｜top-1 %s"
              % (b, p["n"], p["v_hit"] * 100.0 / p["n"], lo * 100, hi * 100,
                 ("%.1f%%" % tr) if tr is not None else "—"))
    b0, ab = agg["B0_常规"], sum(agg[b]["n"] for b in BUCKETS if b != "B0_常规")
    if b0["n"] >= 20 and ab >= 20:
        r0 = b0["v_hit"] / b0["n"]
        ra = sum(agg[b]["v_hit"] for b in BUCKETS if b != "B0_常规") / ab
        print("  H 预声明对比：B0 verdict %.1f%% vs 弃权桶合 %.1f%%（差 %+.1fpt；%s）"
              % (r0 * 100, ra * 100, (r0 - ra) * 100,
                 "弃权桶确有信息量→C2 第二半值得接线（另批 §四 全验收）" if r0 - ra >= 0.10
                 else "差距 <10pt→按 §六.5 登记结案，不接线"))
    return 0


def cmd_selftest() -> int:
    fails = []
    by_id = {c["id"]: c for c in case_runner.load_cases()}
    ids = case_runner.load_ids("tune")[:3]
    bs = [bucket_of(by_id[i]) for i in ids]
    if any(b not in BUCKETS for b in bs):
        fails.append("分桶越界：%r" % bs)
    if bs != [bucket_of(by_id[i]) for i in ids]:
        fails.append("装配不确定（引擎 [23] 同口径应可复现）")
    all_silence = {"id": "ST", "hexagram": {"original": "乾"},
                   "input": {"year": 2024, "month": 6, "day": 1, "date": "巳月甲子日"}}
    if bucket_of(all_silence) not in ("B1_全静", "B0_常规"):
        fails.append("静卦桶判错：%s" % bucket_of(all_silence))
    print("√ selftest：分桶合法/两次一致/静卦路径 全过" if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="弃权分型读数（观察，不动输出面）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return cmd_selftest()
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
