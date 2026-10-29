# -*- coding: utf-8 -*-
"""一行规则基线库（第一百八十三批·A1）——用最小策略丈量整个引擎的保真增量。

要回答的问题（176 批"工程重心转移"清单 A1）：21,880 行的六爻引擎，在**书语料**上
比下列一行规则多买到多少保真？答案无论朝哪边都是硬结论——
若引擎 top-1 打不过"日辰即答"这类零知识规则，则判词/应期层后续扩建须重新定义价值。

    python dev_tools/baselines.py                      # 两个外部集全对照
    python dev_tools/baselines.py --split wikisource_holdout
    python dev_tools/baselines.py --selftest

纪律（不碰的东西）：
  - 案例读取走 `case_runner`（[13] 案例隔离白名单既有通道），本工具不新建 data/cases 直读；
  - 只出**读数报告**：不进任何评分面、不触任何门基线（外部集只报数不设门槛，§四.3）；
  - 频率基线的边际分布**只取内部集**（tune+holdout）作来源——外部集答案支参与边际
    即泄漏（selftest 负例锁死）；
  - 口径：答案支 ∈ 书载应支 记命中（支层二值，不分日/月/年单位；引擎同屏给两个参照：
    自声明首支 与 同单位池 top-1〔=既有 27.3% 口径〕），全部同一分母。
"""
from __future__ import annotations

import argparse
import io
import random
import sys
import tempfile
from contextlib import redirect_stdout
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
from outcome import MIN_N_FOR_CONCLUSION, wilson  # noqa: E402

INTERNAL_SPLITS = ("tune", "holdout")          # 频率基线唯一许可来源
DEFAULT_SPLITS = ("wikisource_holdout", "zengshan_dz_holdout")
RANDOM_P = 1.0 / 12.0


def needed_branch(case: dict):
    """书载应支列表（不分单位）；无支可核 → None（该例对本表不可评，显形不充数）。"""
    x = str((case.get("expected") or {}).get("yingqi") or "")
    m = evaluate.YQ_UNIT_RE.search(x)
    brs = [m.group(1)] if m else evaluate._branches_in(x)
    return brs or None


def branch_answers(case: dict, eng: dict):
    """六条基线的答案支。返回 (name→branch|None, 显形注)。缺键返回 None 并点名——静默跳过禁止。"""
    notes = []
    ans = {}
    ans["用神值支"] = eng.get("use_god_branch") or None
    if ans["用神值支"] is None:
        notes.append("use_god_branch 缺失")
    day_sb = month_sb = ""
    world_br = None
    try:
        yao = case_runner.hex2yao(case["hexagram"]["original"], case["hexagram"].get("changed"))
        dt = case_runner.resolve_case_time(case)["dt"]
        h = build_hexagram_result(yao, case.get("question", ""), "manual",
                                  dt.year, dt.month, dt.day, dt.hour)
        div = h.get("divination_time") or {}
        day_sb = div.get("day_stem_branch", "")
        month_sb = div.get("month_stem_branch", "")
        world = next((y for y in (h.get("original_hexagram") or {}).get("yao_lines", [])
                      if y.get("is_world")), None)
        world_br = (world or {}).get("earthly_branch")
    except Exception as e:  # noqa: BLE001 —— 盘面重装配失败必须显形
        notes.append("盘面重装配失败:%s" % str(e)[:30])
    ans["世爻值支"] = world_br
    ans["日辰即答"] = day_sb[-1] if len(day_sb) == 2 else None
    ans["月建即答"] = month_sb[-1] if len(month_sb) == 2 else None
    return ans, ("；".join(notes) if notes else "")


def internal_marginal():
    """频率基线边际：仅内部集（tune+holdout）书载应支频次；外部 id 混入即抛（防泄漏）。"""
    by_id = {c["id"]: c for c in case_runner.load_cases()}
    src_ids = []
    for s in INTERNAL_SPLITS:
        src_ids += case_runner.load_ids(s)
    ext = set()
    for s in DEFAULT_SPLITS:
        ext |= set(case_runner.load_ids(s))
    leak = [i for i in src_ids if i in ext]
    if leak:
        raise ValueError("频率基线边际混入外部集 id（泄漏）：%s" % leak[:3])
    cnt = {}
    for cid in src_ids:
        brs = needed_branch(by_id[cid])
        for b in (brs or []):
            cnt[b] = cnt.get(b, 0) + 1
    if not cnt:
        raise ValueError("内部集应支边际为空——先查语料装配，不出假基线")
    top = max(cnt, key=cnt.get)
    return top, cnt


def measure(split: str):
    ids = case_runner.load_ids(split)
    by_id = {c["id"]: c for c in case_runner.load_cases()}
    if not ids:
        print("× split=%s 解析 0 例——显形，不当 0%% 用（§四.8）" % split)
        return None
    top_guess, marg = internal_marginal()
    rows = {}
    n_score = n_skip_missing = n_eng_pool_top1 = n_eng_pool_top3 = 0
    pool_den = first_den = 0
    eng_first = eng_pool_top1 = eng_pool_top3 = 0
    for cid in ids:
        case = by_id[cid]
        need = needed_branch(case)
        try:
            eng = case_runner.run_case(case)
        except Exception as e:  # noqa: BLE001
            eng = {"error": str(e)}
        if "error" in eng:
            rows.setdefault("__err__", 0)
            rows["__err__"] += 1
            continue
        if not need:
            n_skip_missing += 1
            continue
        n_score += 1
        ans, note = branch_answers(case, eng)
        for name, br in ans.items():
            st = rows.setdefault(name, {"hit": 0, "n": 0, "miss_ans": 0})
            if br is None:
                st["miss_ans"] += 1
                continue
            st["n"] += 1
            st["hit"] += 1 if br in need else 0
        rows.setdefault("频率猜测(内部边际)", {"hit": 0, "n": 0, "miss_ans": 0})
        fr = rows["频率猜测(内部边际)"]
        fr["n"] += 1
        fr["hit"] += 1 if top_guess in need else 0
        e_pool_all = evaluate._offered_branches(eng.get("yingqi_branches") or [])
        e_first = e_pool_all[0] if e_pool_all else None
        if e_first:
            first_den += 1
            eng_first += 1 if e_first in need else 0
        unit = evaluate._expected_unit(str((case.get("expected") or {}).get("yingqi") or ""))
        pool = evaluate._offered_branches(evaluate._unit_pool(eng, unit))
        if pool:
            pool_den += 1
            eng_pool_top1 += 1 if pool[0] in need else 0
            eng_pool_top3 += 1 if any(b in need for b in pool[:3]) else 0
        if note:
            rows.setdefault("__notes__", []).append("%s:%s" % (cid, note))
    if n_score == 0:
        print("× split=%s 可评 0 例（答案支全缺？）——判红不空跑" % split)
        return None
    out = {"split": split, "n_score": n_score, "n_no_answer_branch": n_skip_missing,
           "engine_err": rows.get("__err__", 0),
           "pool_den": pool_den,
           "baselines": {},
           "notes": rows.get("__notes__", [])}
    print("═ %s ═ 可评 %d 例｜书载应支不可核 %d｜引擎错 %d" %
          (split, n_score, n_skip_missing, out["engine_err"]))
    for name in ("用神值支", "世爻值支", "日辰即答", "月建即答", "频率猜测(内部边际)"):
        st = rows.get(name, {"hit": 0, "n": 0, "miss_ans": 0})
        lo, hi = wilson(st["hit"], st["n"]) if st["n"] else (0, 0)
        rate = st["hit"] * 100.0 / st["n"] if st["n"] else 0.0
        flag = "样本不足(<%d)" % MIN_N_FOR_CONCLUSION if st["n"] < MIN_N_FOR_CONCLUSION else ""
        print("  %-12s %3d/%3d = %5.1f%%  [CI %4.1f–%4.1f]  无答案 %d  %s"
              % (name, st["hit"], st["n"], rate, lo * 100, hi * 100, st["miss_ans"], flag))
        out["baselines"][name] = {"hit": st["hit"], "n": st["n"], "rate": round(rate, 1),
                                  "ci": [round(lo * 100, 1), round(hi * 100, 1)],
                                  "no_answer": st["miss_ans"]}
    print("  %-12s          理论 1/12 = %5.1f%%" % ("随机", RANDOM_P * 100))
    r1 = eng_first * 100.0 / first_den if first_den else 0.0
    lo1, hi1 = wilson(eng_first, first_den) if first_den else (0, 0)
    r2 = eng_pool_top1 * 100.0 / pool_den if pool_den else 0.0
    r3 = eng_pool_top3 * 100.0 / pool_den if pool_den else 0.0
    lo2, hi2 = wilson(eng_pool_top1, pool_den) if pool_den else (0, 0)
    print("  引擎·自声明首支   %3d/%3d = %5.1f%%  [CI %4.1f–%4.1f]"
          % (eng_first, first_den, r1, lo1 * 100, hi1 * 100))
    print("  引擎·同单位池top1 %3d/%3d = %5.1f%%  [CI %4.1f–%4.1f]（与 window_report 同口径）"
          % (eng_pool_top1, pool_den, r2, lo2 * 100, hi2 * 100))
    print("  引擎·池内top3窗   %3d/%3d = %5.1f%%" % (eng_pool_top3, pool_den, r3))
    out["engine"] = {"first": {"hit": eng_first, "n": first_den, "rate": round(r1, 1)},
                     "pool_top1": {"hit": eng_pool_top1, "n": pool_den, "rate": round(r2, 1)},
                     "pool_top3": {"hit": eng_pool_top3, "n": pool_den, "rate": round(r3, 1)}}
    return out


def cmd_selftest() -> int:
    fails = []
    # 1) 泄漏防护：把外部 id 塞进边际来源必须抛
    real_load_ids = case_runner.load_ids
    try:
        tmp_ids = real_load_ids("wikisource_holdout")[:1]

        def tainted(s):
            if s == "tune":
                return tmp_ids + real_load_ids("tune")   # 外部 id 冒充内部成员
            return real_load_ids(s)                      # 外部集照常可见
        case_runner.load_ids = tainted
        try:
            internal_marginal()
            fails.append("外部 id 混入边际未抛出（泄漏防护失效）")
        except ValueError:
            pass
        except Exception as e:  # noqa: BLE001
            fails.append("泄漏路径异常：%s" % str(e)[:60])
    finally:
        case_runner.load_ids = real_load_ids
    # 2) 缺键显形：删掉 use_god_branch 的用神基线必须是 None 并被点名
    by_id = {c["id"]: c for c in case_runner.load_cases()}
    case = by_id[real_load_ids("tune")[0]]
    ans, note = branch_answers(case, {"use_god_branch": ""})
    if ans["用神值支"] is not None or "缺失" not in note:
        fails.append("use_god_branch 空缺未显形")
    # 3) 0 例可评判红：空 split 路径
    buf = io.StringIO()
    with redirect_stdout(buf):
        case_runner.load_ids = lambda s: []
        try:
            r = measure("anything")
        finally:
            case_runner.load_ids = real_load_ids
    if r is not None:
        fails.append("0 例可评未判红")
    print("√ selftest：泄漏防护/缺键显形/0 例判红 全过" if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="一行规则基线×引擎 同屏对照（读数报告，不进评分面）")
    ap.add_argument("--split", action="append", dest="splits")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return cmd_selftest()
    splits = args.splits or list(DEFAULT_SPLITS)
    rc = 0
    for s in splits:
        if measure(s) is None:
            rc = 1
    print("\n注：同一分母（书载应支可核例）；随机 1/12 为理论值；本表只报数不设门槛（§四.3），"
          "结论属书吻合面、不构成现实命中率（铁律三）。")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
