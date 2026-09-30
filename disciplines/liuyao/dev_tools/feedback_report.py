# -*- coding: utf-8 -*-
"""真实应期反馈的独立审计报告 —— 不依赖任何评分引擎。

    用法:
        python dev_tools/feedback_report.py --summary
        python dev_tools/feedback_report.py --export <path.csv>

    用途:
        从 data/feedback/ 读取真实用户应期反馈，输出独立统计。
        数据永不参与调参，报告仅用于独立审计现实命中率。
        不引用 evaluate.py 或评分引擎任何函数。
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feedback_store import FeedbackStore, _branch_of  # noqa: E402


DAYS_OF_WEEK = "一二三四五六日"
DAYS_MTWT = ["一", "二", "三", "四", "五", "六", "日"]


def _histogram(items: list, width: int = 40, char: str = "█") -> str:
    """生成一个简易文本直方图。"""
    if not items:
        return "  （无数据）"
    c = Counter(items)
    labels = sorted(c.keys())
    max_v = max(c.values()) or 1
    lines = []
    for lab in labels:
        n = c[lab]
        bar = char * max(1, int(n / max_v * width))
        lines.append(f"    {lab:10s} {bar} {n}")
    return "\n".join(lines)


def summary(store: FeedbackStore) -> str:
    records = store.load_all()
    stats = store.stats()
    lines: list[str] = []
    lines.append("═" * 60)
    lines.append("  真实应期反馈 · 独立评估报告")
    lines.append("  ⚠  本数据与古籍案例物理隔离，永不参与调参")
    lines.append("═" * 60)
    lines.append(f"\n  总记录数：{stats['total_records']}")
    lines.append(f"  有实际应验结果：{stats['with_actual_outcome']}")
    if stats.get("strict_hit_rate") is not None:
        lines.append(f"  严格命中率：{stats['strict_hit_rate']}%  "
                     f"({stats['strict_hits']}/{stats['with_actual_outcome']})")
        lines.append(f"  宽松命中率：{stats['loose_hit_rate']}%  "
                     f"({stats['loose_hits']}/{stats['with_actual_outcome']})")
    else:
        lines.append("  命中率：尚无带实际日期的反馈")
    # 应验日期分布（按星期几）
    wdays, months = [], []
    for r in records:
        d = r.get("actual_date") or (r.get("actual_outcome") or {}).get("date")
        if not d:
            continue
        try:
            from datetime import datetime
            dt = datetime.strptime(str(d)[:10], "%Y-%m-%d")
            wdays.append(DAYS_MTWT[dt.weekday()])
            months.append(str(dt.month))
        except ValueError:
            continue
    lines.append("\n  ── 应验日期·星期分布 ──")
    lines.append(_histogram(wdays))
    lines.append("\n  ── 应验日期·月份分布 ──")
    lines.append(_histogram(months))
    # 预测 vs 实际支对照
    lines.append("\n  ── 预测主应支 vs 实际支 ──")
    branch_pairs = []
    for r in records:
        actual = r.get("actual_date") or (r.get("actual_outcome") or {}).get("date")
        pred_dates = r.get("predicted_dates") or []
        if not actual or not pred_dates:
            continue
        ab = _branch_of(actual)
        pb = _branch_of(pred_dates[0])
        if ab and pb:
            status = ""
            if r.get("hit_strict"):
                status = "✓"
            elif r.get("hit_loose"):
                status = "~"
            else:
                status = "✗"
            branch_pairs.append(f"    预测{pb} → 实际{ab} [{status}]")
    if branch_pairs:
        lines.extend(branch_pairs[:20])
        if len(branch_pairs) > 20:
            lines.append(f"    … 共 {len(branch_pairs)} 条")
    else:
        lines.append("    （尚无可对照数据）")
    lines.append("\n" + "═" * 60)
    return "\n".join(lines)


def export_csv(store: FeedbackStore, out_path: Path) -> int:
    """导出 CSV 用于外部独立审计。"""
    records = store.load_all()
    if not records:
        print("无反馈可导出", file=sys.stderr)
        return 1
    fieldnames = [
        "id", "timestamp", "discipline", "chart_id",
        "predicted_main_yingqi", "predicted_window",
        "actual_date", "actual_description",
        "hit_strict", "hit_loose",
    ]
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in records:
            actual = r.get("actual_outcome") or {}
            row = {
                "id": r.get("id", ""),
                "timestamp": r.get("timestamp", ""),
                "discipline": r.get("discipline", ""),
                "chart_id": r.get("chart_id", ""),
                "predicted_main_yingqi": r.get("predicted_main_yingqi", ""),
                "predicted_window": r.get("predicted_window", ""),
                "actual_date": r.get("actual_date") or actual.get("date", ""),
                "actual_description": actual.get("description", ""),
                "hit_strict": r.get("hit_strict"),
                "hit_loose": r.get("hit_loose"),
            }
            w.writerow(row)
    print(f"已导出 {len(records)} 条反馈到 {out_path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="真实应期反馈 · 独立审计报告（永不参与调参）")
    ap.add_argument("--summary", action="store_true", help="读数汇总")
    ap.add_argument("--export", type=Path, help="导出 CSV 路径（用于独立审计）")
    args = ap.parse_args()
    if not args.summary and not args.export:
        ap.error("请指定 --summary 或 --export <path>")
    store = FeedbackStore("liuyao")
    if args.summary:
        print(summary(store))
    if args.export:
        return export_csv(store, args.export)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
