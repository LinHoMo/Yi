# -*- coding: utf-8 -*-
"""共享评分器（Eval Kit）—— 全仓库唯一给分框架。

CONTRACT.md §四.6：「复用 `yishu_core.eval`，禁止另写一套给分逻辑。」
所有学科的**古籍案例对齐分**都必须经由本模块的框架计算，学科只提供
自己的维度比较函数 `score_case()` 与维度权重表。

口径（务必连同分数一起阅读，AGENTS.md 铁律三）：
  本框架衡量的是**引擎输出与古籍案例要点的一致性**，不是现实世界预言命中率。
  两种计分模型同时输出：
    strict —— 基准未记录某维度时该维度记 N/A 并从分母剔除；名次制防骑墙。
    legacy —— 复刻旧口径：N/A 按满分给、应期有保底（历史 100% 即其产物，保持可复现）。

本模块提供：
  verdict_direction()  吉凶方向 → ±1/0（各科共用同一判法）
  pct()                维度明细 → (百分比, 适用权重)
  aggregate()          行明细 → 汇总报告结构（avg/n/min/max/dims）
  run_eval()           整批打分的通用循环（读引擎输出 + 基准，逐例调 score_case）
"""
from __future__ import annotations

from typing import Callable


def verdict_direction(v) -> int:
    """吉凶字面 → 方向：1=吉、-1=凶、0=中性/未知。各科共用同一判法。"""
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


def pct(dims: dict) -> tuple[float, int]:
    """维度明细 → (百分比, 适用权重)。dims 为 {dim: (earned, applicable_weight, note)}。"""
    earned = sum(v[0] for v in dims.values())
    applicable = sum(v[1] for v in dims.values())
    if applicable <= 0:
        return 0.0, 0
    return earned * 100.0 / applicable, applicable


def aggregate(rows: list[dict], per_dim: dict, label: str, model: str) -> dict:
    """行明细（pct 列表）+ 维度计数 → 汇总报告。"""
    scored = [r["pct"] for r in rows if "dims" in r]
    if not scored:
        return {"label": label, "model": model, "avg": None, "n": 0, "rows": rows}
    dim_summary = {
        k: {"full": v[0], "applicable": v[1], "na": v[2],
            "rate": round(v[0] * 100.0 / v[1], 1) if v[1] else None}
        for k, v in per_dim.items()
    }
    avg = sum(scored) / len(scored)
    return {"label": label, "model": model, "avg": round(avg, 1), "n": len(scored),
            "min": min(scored), "max": max(scored), "dims": dim_summary, "rows": rows}


def run_eval(engine_out: dict, base_by_id: dict, ids: list[str],
             weights: dict, score_case: Callable, model: str,
             label: str, verbose: bool = False) -> dict:
    """通用评分循环。

    engine_out : 引擎整批输出，其 `cases` 列表元素为单例引擎结果
    base_by_id : {case_id: case}，case 内 `expected` 为基准要点
    ids        : 本次要评分的案例 id 列表
    weights    : {维度名: 权重}，单一真值源，总和 100
    score_case : (engine_dict, expected_dict, model) → {dim: (earned, weight, note)}
    """
    by_e = {c.get("id"): c for c in engine_out.get("cases", [])}
    rows, per_dim = [], {k: [0, 0, 0] for k in weights}  # [hit_full, applicable, na]
    for cid in ids:
        e, b = by_e.get(cid), base_by_id.get(cid)
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
    return aggregate(rows, per_dim, label, model)


def report(res: dict) -> None:
    """汇总报告 → 控制台文本。"""
    if res["avg"] is None:
        print(f"=== {res['label']} [{res['model']}] 无可用结果（n=0）===")
        return
    print(f"\n=== {res['label']} [{res['model']}] 平均分 = {res['avg']}%  (n={res['n']}"
          f"，最低 {res['min']}，最高 {res['max']}) ===")
    print("  维度          命中/适用   N/A   命中率")
    for k, v in res["dims"].items():
        rate = f"{v['rate']}%" if v["rate"] is not None else "—"
        print(f"  {k:<16s}{v['full']:>4d}/{v['applicable']:<4d}  {v['na']:>3d}   {rate}")
