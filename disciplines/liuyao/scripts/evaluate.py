# -*- coding: utf-8 -*-
"""唯一评分器：古籍案例对齐分（tune / holdout 分别出分，禁止混分）。

    python scripts/evaluate.py                      # 跑全部合并出分
    python scripts/evaluate.py --split tune
    python scripts/evaluate.py --split holdout --verbose
    python scripts/evaluate.py --stage score --engine-file data/cases/eval_all.json

口径说明（务必连同分数一起阅读）：
  本脚本衡量的是**引擎输出与古籍案例要点的一致性**，不是现实世界预言命中率。

两种计分模型同时输出：
  strict —— 基准未记录某维度时该维度记 N/A 并从分母剔除；应期不对齐不得分。
  legacy —— 复刻 2026-09-20 之前的口径：N/A 按满分给、应期有 8/15 保底。
            历史上报出的 tune 100% 就是这个口径的产物，此处保持可复现。

维度与权重（单一真值源，总和 100）：
  用神六亲 15 / 用神地支 10 / 用神爻位 5 / 吉凶方向 40 / 格局覆盖 15 / 应期 15
"""
from __future__ import annotations
from kernel_path import kernel_dir  # noqa: E402

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "scripts"), str(kernel_dir(__file__))):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.runtime import force_utf8_stdio  # noqa: E402

CASES = ROOT / "data" / "cases" / "classical_cases.json"
OUT_DIR = ROOT / "data" / "cases"

DAY_CHARS = "子丑寅卯辰巳午未申酉戌亥"

WEIGHTS = {
    "use_god_category": 15,
    "use_god_branch": 10,
    "use_god_position": 5,
    "verdict": 40,
    "patterns": 15,
    "yingqi": 15,
}

PATTERNS = [
    "冲中逢合", "合处逢冲", "回头克", "回头生", "近病逢空", "近病逢合", "绝处逢生",
    "飞克伏", "伏生飞", "飞空得出", "飞生伏", "入墓", "随官入墓", "反吟", "伏吟",
    "六合", "六冲", "伏藏", "伏神", "长生", "帝旺", "沐浴", "化合", "化退神", "化进神",
    "旬空", "填实", "出空", "出旬", "暗动", "月破", "日辰合世", "变卦六合", "世爻",
    "动空", "原神生用", "泄气", "游魂", "归魂", "用神多现", "世持财", "内卦", "迟归",
    "用神生世", "兄弟持世", "墓", "绝于",
]

PATTERN_ALIASES = {
    "旬空": ["旬空", "出旬", "填实", "冲空"],
    "出空": ["出空", "出旬", "填实", "冲空"],
    "出旬": ["出旬", "填实", "冲空"],
    "伏神": ["伏神", "伏藏"],
    "伏藏": ["伏藏", "伏神"],
    "世爻": ["世爻", "持世", "世持"],
    "迟归": ["迟归", "用神生世", "生世"],
    "用神生世": ["用神生世", "生世", "迟归"],
    "兄弟持世": ["兄弟持世", "持兄", "兄弟"],
    "世持财": ["世持财", "持世"],
    "用神多现": ["用神多现", "多现", "两现", "现于"],
    "伏神得出": ["伏神得出", "飞空得出", "飞神旬空"],
    "飞空得出": ["飞空得出", "飞神旬空", "伏神得出"],
    "化退神": ["化退神", "化退"],
    "化进神": ["化进神", "化进"],
    "动则生": ["动则生", "原神生用", "动空"],
    "原神生用": ["原神生用", "动则生"],
    "近病逢空": ["近病逢空", "近病"],
    "近病逢合": ["近病逢合", "近病"],
}

RHYTHM_PAIRS = [
    (("次日", "当天", "当日"), ("应速", "次日", "当日", "快则", "近日")),
    (("年内", "月余", "经年"), ("年内", "应迟", "旺相之月", "月余", "窗口偏长", "节奏偏慢")),
    (("不安", "反复", "难成"), ("不安", "反复", "合处逢冲", "冲中逢合", "拖延")),
    (("出空", "出旬"), ("出空", "出旬", "填实", "冲空")),
]


def verdict_direction(v) -> int:
    s = str(v or "")
    if s in ("吉", "平吉", "大吉"):
        return 1
    if s in ("凶", "大凶", "下跌"):
        return -1
    if "吉" in s and "凶" not in s and "不利" not in s:
        return 1
    if "凶" in s or "跌" in s or "不利" in s:
        return -1
    return 0


def _na(value) -> bool:
    return value in (None, "", "?")


def score_case(eng: dict, exp: dict, model: str) -> dict:
    """单例打分。返回 {dim: (earned, applicable_weight, note)}。"""
    dims: dict[str, tuple[int, int, str]] = {}

    # 用神六亲
    e_cat, x_cat = eng.get("use_god_category", ""), exp.get("use_god_god") or exp.get("use_god") or ""
    hit = (e_cat == x_cat)
    dims["use_god_category"] = (WEIGHTS["use_god_category"] if hit else 0,
                                WEIGHTS["use_god_category"],
                                f"{e_cat}{'=' if hit else '≠'}{x_cat or '基准缺'}")

    # 用神地支
    e_br, x_br = eng.get("use_god_branch", ""), exp.get("use_god_branch", "")
    w = WEIGHTS["use_god_branch"]
    if _na(x_br):
        if model == "legacy":
            dims["use_god_branch"] = (w if hit else 0, w, "基准未记支，随六亲")
        else:
            dims["use_god_branch"] = (0, 0, "基准未记支 → N/A")
    else:
        ok = e_br == x_br
        dims["use_god_branch"] = (w if ok else 0, w, f"{e_br}{'=' if ok else '≠'}{x_br}")

    # 用神爻位
    e_pos, x_pos = eng.get("use_god_position"), exp.get("use_god_position")
    w = WEIGHTS["use_god_position"]
    if _na(x_pos):
        dims["use_god_position"] = (w, w, "基准未记位，满分") if model == "legacy" else (0, 0, "基准未记位 → N/A")
    else:
        ok = str(e_pos) == str(x_pos)
        dims["use_god_position"] = (w if ok else 0, w, f"{e_pos}{'=' if ok else '≠'}{x_pos}")

    # 吉凶方向
    w = WEIGHTS["verdict"]
    ed, xd = verdict_direction(eng.get("verdict")), verdict_direction(exp.get("verdict"))
    if ed == xd:
        vs, note = w, "方向一致"
    elif ed * xd > 0:
        vs, note = int(w * 0.8), "同向异强"
    elif str(exp.get("verdict")) in ("平/不利", "平") and ed <= 0:
        vs, note = int(w * 0.8), "基准平·引擎偏负"
    elif ed == 0:
        vs, note = int(w * 0.3), "引擎中性回避"
    else:
        vs, note = 0, "方向相反"
    dims["verdict"] = (vs, w, f"{eng.get('verdict')}/{exp.get('verdict')} {note}")

    # 格局覆盖
    w = WEIGHTS["patterns"]
    baseline = " ".join(str(x) for x in (exp.get("key_points") or [])) + " " + str(exp.get("detail") or "")
    needed = [p for p in PATTERNS if p in baseline]
    combined = " ".join([t for t in (eng.get("pattern_tags") or [])] +
                        [t for t in (eng.get("reasoning_chain") or []) if isinstance(t, str)])
    if not needed:
        dims["patterns"] = (w, w, "基准无格局词，满分") if model == "legacy" else (0, 0, "基准无格局词 → N/A")
    else:
        detected = [p for p in needed if p in combined or any(a in combined for a in PATTERN_ALIASES.get(p, []))]
        ratio = len(detected) / len(needed)
        vs = w if ratio >= 0.5 else (int(w * 0.66) if ratio > 0 else 0)
        dims["patterns"] = (vs, w, f"{len(detected)}/{len(needed)}:{','.join(detected[:4]) or '无'}")

    # 应期
    w = WEIGHTS["yingqi"]
    e_yq = str(eng.get("yingqi") or "")
    x_yq = str(exp.get("yingqi") or "")
    declared_tokens = [str(b) for b in (eng.get("yingqi_branches") or [])]
    declared = " ".join(declared_tokens)
    head = e_yq.split("依据")[0]
    e_all = head + " " + declared
    e_verbose = e_yq + " " + declared + " " + " ".join(
        str(d.get("date") if isinstance(d, dict) else d) for d in (eng.get("yingqi_dates") or []))
    probe = e_verbose if model == "legacy" else e_all
    if _na(x_yq):
        dims["yingqi"] = (w, w, "空白基准，满分") if model == "legacy" else (0, 0, "空白基准 → N/A")
    elif model == "legacy":
        x_branches = [c for c in DAY_CHARS if c in x_yq]
        rhythm = any(any(k in x_yq for k in xk) and any(k in probe for k in ek)
                     for xk, ek in RHYTHM_PAIRS)
        if x_yq in probe or (x_branches and all(c in probe for c in x_branches)):
            dims["yingqi"] = (w, w, "应支全覆盖")
        elif any(c in probe for c in x_branches):
            dims["yingqi"] = (int(w * 0.8), w, "应支部分覆盖")
        elif rhythm:
            dims["yingqi"] = (int(w * 0.8), w, "节奏语义对齐")
        else:
            dims["yingqi"] = (8, w, "存在即保底")
    else:
        # strict 按**名次**给分，不按"有没有提到"给分。
        # 成员制打分会奖励骑墙：候选铺到 11/12 支就能白拿 15 分（旧口径的 100% 即由此而来）。
        needed = [c for c in DAY_CHARS if c in x_yq]
        offered = []
        for token in declared_tokens:
            for ch in token[:2]:
                if ch in DAY_CHARS and ch not in offered:
                    offered.append(ch)
        rank = next((i + 1 for i, ch in enumerate(offered) if needed and ch in needed), None)
        if not needed:
            hit = x_yq in probe
            dims["yingqi"] = (w if hit else 0, w, "字面命中" if hit else f"未对齐({x_yq})")
        elif rank == 1:
            dims["yingqi"] = (w, w, "主应期命中")
        elif rank == 2:
            dims["yingqi"] = (int(w * 0.8), w, "次应期命中")
        elif rank and rank <= 4:
            dims["yingqi"] = (int(w * 0.55), w, f"第 {rank} 位命中")
        elif any(c in probe for c in needed):
            dims["yingqi"] = (int(w * 0.35), w, "仅在依据句中出现，未列为应期")
        else:
            dims["yingqi"] = (0, w, f"未给出基准应期({','.join(needed)})")
    return dims


def pct(dims: dict) -> tuple[float, int]:
    earned = sum(v[0] for v in dims.values())
    applicable = sum(v[1] for v in dims.values())
    if applicable <= 0:
        return 0.0, 0
    return earned * 100.0 / applicable, applicable


def evaluate(engine_out: dict, model: str, label: str, ids: list[str], verbose: bool) -> dict:
    base = {c["id"]: c for c in json.loads(CASES.read_text(encoding="utf-8"))["cases"]}
    by_e = {c.get("id"): c for c in engine_out.get("cases", [])}

    rows, per_dim = [], {k: [0, 0, 0] for k in WEIGHTS}  # [hit_full, applicable, na]
    for cid in ids:
        e, b = by_e.get(cid), base.get(cid)
        if b is None or e is None:
            continue
        if "error" in e and "verdict" not in e:
            rows.append({"id": cid, "pct": 0.0, "applicable": 100, "note": "引擎错误"})
            continue
        dims = score_case(e, b.get("expected") or {}, model)
        value, applicable = pct(dims)
        for k, (earned, weight, note) in dims.items():
            if weight == 0:
                per_dim[k][2] += 1
            else:
                per_dim[k][1] += 1
                if earned >= weight:
                    per_dim[k][0] += 1
        rows.append({"id": cid, "pct": round(value, 1), "applicable": applicable,
                     "dims": {k: v for k, v in dims.items()}})
        if verbose:
            worst = [f"{k}:{v[0]}/{v[1]}" for k, v in dims.items() if v[0] < v[1] and v[1]]
            print(f"[{label}] {cid:6s} {value:5.1f}%  " + ("; ".join(worst) if worst else "全中"))

    scored = [r["pct"] for r in rows if "dims" in r]
    if not scored:
        return {"label": label, "model": model, "avg": None, "n": 0, "rows": rows}
    dim_summary = {k: {"full": v[0], "applicable": v[1], "na": v[2],
                       "rate": round(v[0] * 100.0 / v[1], 1) if v[1] else None}
                   for k, v in per_dim.items()}
    avg = sum(scored) / len(scored)
    return {"label": label, "model": model, "avg": round(avg, 1), "n": len(scored),
            "min": min(scored), "max": max(scored), "dims": dim_summary, "rows": rows}


def _branches_in(text: str) -> list[str]:
    """按出现顺序抽出互不重复的地支。"""
    seen, out = set(), []
    for ch in str(text or ""):
        if ch in DAY_CHARS and ch not in seen:
            seen.add(ch)
            out.append(ch)
    return out


def yingqi_discrimination(engine_out: dict, ids: list[str]) -> dict:
    """应期的"信息量"体检。

    只看召回会被候选集大小骗过去：若引擎把十二支列个遍，字面命中 100% 也毫无意义。
    这里只数引擎**自己声明的重点应期**（yingqi_branches），报告：
      候选集平均大小、top-1 命中率、基准应支在候选中的平均名次、
      以及"随机列同样多候选即全覆盖"的期望概率（召回分的无信息基线）。
    """
    base = {c["id"]: c for c in json.loads(CASES.read_text(encoding="utf-8"))["cases"]}
    by_e = {c.get("id"): c for c in engine_out.get("cases", [])}
    sizes, ranks, top1_hit, top1_n, random_p = [], [], 0, 0, []

    for cid in ids:
        e, b = by_e.get(cid), base.get(cid)
        if not e or not b or "error" in e:
            continue
        needed = _branches_in((b.get("expected") or {}).get("yingqi"))
        if not needed:
            continue
        offered = []
        for token in (e.get("yingqi_branches") or []):
            for ch in _branches_in(str(token)[:2]):
                if ch not in offered:
                    offered.append(ch)
        if not offered:
            continue
        sizes.append(len(offered))
        k, n = len(needed), len(offered)
        p = 1.0
        for i in range(k):
            p *= max(n - i, 0) / (12 - i)
        random_p.append(p)
        top1_n += 1
        if needed[0] == offered[0] or offered[0] in needed:
            top1_hit += 1
        hit_at = next((i + 1 for i, ch in enumerate(offered) if ch in needed), None)
        if hit_at:
            ranks.append(hit_at)

    if not sizes:
        return {}
    return {
        "cases_with_yingqi": len(sizes),
        "avg_candidate_set_size": round(sum(sizes) / len(sizes), 1),
        "top1_hit_rate": round(top1_hit * 100.0 / top1_n, 1) if top1_n else None,
        "avg_rank_of_correct": round(sum(ranks) / len(ranks), 2) if ranks else None,
        "ranked_cases": len(ranks),
        "random_full_coverage_expectancy": round(sum(random_p) * 100.0 / len(random_p), 1),
    }


def report(res: dict) -> None:
    print(f"\n=== {res['label']} [{res['model']}] 平均分 = {res['avg']}%  (n={res['n']}"
          f"，最低 {res['min']}，最高 {res['max']}) ===")
    print("  维度          命中/适用   N/A   命中率")
    for k, v in res["dims"].items():
        rate = f"{v['rate']}%" if v["rate"] is not None else "—"
        print(f"  {k:<16s}{v['full']:>4d}/{v['applicable']:<4d}  {v['na']:>3d}   {rate}")


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="六爻古籍案例对齐评分（非现实预测命中率）")
    ap.add_argument("--split", choices=["tune", "holdout", "all"], default="all")
    ap.add_argument("--ids", nargs="*", help="指定案例 ID，优先于 --split")
    ap.add_argument("--stage", choices=["run", "score", "all"], default="all")
    ap.add_argument("--engine-file", type=Path, help="已有的引擎输出（配合 --stage score）")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--save", action="store_true", help="写出 JSON 明细到 data/cases/")
    args = ap.parse_args()

    import case_runner

    if args.ids:
        ids, label = case_runner.load_ids(only=args.ids), "custom"
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
        engine_out = case_runner.run_ids(ids, verbose=args.verbose)

    exit_code = 0
    results = {}
    sources = {}
    for c in engine_out.get("cases", []):
        sources[c.get("time_source", "error" if "error" in c else "?")] = \
            sources.get(c.get("time_source", "error" if "error" in c else "?"), 0) + 1
    if sources:
        print("时刻还原方式：" + "，".join(f"{k}={v}" for k, v in sorted(sources.items())))

    for model in ("strict", "legacy"):
        res = evaluate(engine_out, model, label, ids, args.verbose)
        report(res)
        results[model] = res

    strict, legacy = results["strict"], results["legacy"]
    if strict["avg"] is None:
        print("无可用结果")
        return 1

    disc = yingqi_discrimination(engine_out, ids)
    if disc:
        results["yingqi_discrimination"] = disc
        print(f"\n应期信息量体检（n={disc['cases_with_yingqi']}，只看引擎自己声明的重点应期）")
        print(f"  候选集平均大小 {disc['avg_candidate_set_size']}/12 —— 越接近 12，召回分越没有信息量")
        print(f"  随机列同样多候选即全覆盖的期望 {disc['random_full_coverage_expectancy']}%"
              f"（召回分接近此值 = 等于没判断）")
        print(f"  top-1 命中 {disc['top1_hit_rate']}%；基准应支平均排在第 {disc['avg_rank_of_correct']} 位"
              f"（{disc['ranked_cases']} 例可定位）← 这一项才见真章")

    print(f"\n口径差异：strict {strict['avg']}% vs legacy {legacy['avg']}%"
          f"（差 {round(legacy['avg'] - strict['avg'], 1)} 分来自空白基准满分与应期保底）")
    print("提示：本分数衡量与古籍案例要点的一致性，不代表现实预测命中率。")

    if args.save:
        out = OUT_DIR / f"eval_{label}.json"
        out.write_text(json.dumps({"results": results, "engine_output": engine_out},
                                  ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("明细 →", out)

    errored = [e["id"] for e in engine_out.get("errors", [])]
    if errored:
        print(f"\n引擎报错 {len(errored)} 例：{', '.join(errored)}")
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
