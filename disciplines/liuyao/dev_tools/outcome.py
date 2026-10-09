# -*- coding: utf-8 -*-
"""实占结果回填与真实效度统计。

    python dev_tools/outcome.py list [--limit 20]        # 哪些事件还欠回填
    python dev_tools/outcome.py record <event_id> \\
           --yingqi main|alt|miss|none --verdict hit|miss|partial \\
           --on 2026-09-25 --note "…"
    python dev_tools/outcome.py stats                    # 命中率（必带 n，n 小即拒绝给结论）
    python dev_tools/outcome.py stats --json

为什么需要它：本仓库所有分数都是**古籍案例对齐分**，衡量不了现实命中率（AGENTS.md 铁律三）。
唯一能产生现实证据的路径，是把已经发生的占测结果回填进来。`logs/divination_events.jsonl`
已有数百条真实求测记录，但过去没有任何回收机制——所以"准不准"这个问题一直没有资格被回答。

设计取舍：
  - 事件日志只追加不改写；结果另存 `data/feedback/outcomes.jsonl`，按 event_id 关联。
    保持原始记录不可变，审计时能分清"当时说了什么"与"后来知道什么"。
  - 统计坚持三件事：给 n、给置信区间、n 不足直接拒绝出结论。
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core import ganzhi_calendar as gc  # noqa: E402

EVENTS = DISC / "logs" / "divination_events.jsonl"
OUTCOMES = DISC / "data" / "feedback" / "outcomes.jsonl"
MIN_N_FOR_CONCLUSION = 30      # 低于此数不出"命中率"结论，只报计数


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    return out


def load_events() -> dict[str, dict]:
    evs = read_jsonl(EVENTS)
    by_id = {}
    for e in evs:
        eid = e.get("event_id")
        if eid:
            by_id[eid] = e            # 同 id 后写覆盖先写
    return by_id


def wilson(hits: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 区间。小样本下比 ±σ 的正态近似诚实得多。"""
    if n == 0:
        return (0.0, 0.0)
    ph = hits / n
    den = 1 + z * z / n
    ctr = (ph + z * z / (2 * n)) / den
    half = (z / den) * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))
    return (max(ctr - half, 0.0), min(ctr + half, 1.0))


def cmd_list(args) -> int:
    events = load_events()
    done = {o.get("event_id") for o in read_jsonl(OUTCOMES)}
    pending = [(eid, e) for eid, e in events.items()
               if eid not in done and (e.get("yingqi_main") or e.get("verdict"))]
    unscorable = [eid for eid, e in events.items() if eid not in done and not e.get("yingqi_main")]
    pending.sort(key=lambda kv: kv[1].get("timestamp", ""), reverse=True)
    print(f"已回填 {len(done)} 条；待回填 {len(pending)} 条"
          f"（其中 {len(unscorable)} 条无应期候选，只能评吉凶方向）")
    for eid, e in pending[:args.limit]:
        print(f"  {eid[:8]}  {e.get('timestamp', '')[:10]}  {e.get('question', '')[:22]:22s} "
              f"断={e.get('verdict', ''):4s} 主应期={e.get('yingqi_main') or '—':4s} "
              f"备={','.join(e.get('yingqi_alt') or []) or '—'}")
    if pending:
        eid, e = pending[0]
        print(f"\n回填示例：\n  python dev_tools/outcome.py record {eid} "
              f"--yingqi main --verdict hit --on {date.today().isoformat()}")
    return 0


def cmd_record(args) -> int:
    events = load_events()
    eid = args.event_id
    match = [k for k in events if k.startswith(eid)]
    if len(match) != 1:
        print(f"× event_id 需能唯一定位：匹配到 {len(match)} 条（{eid}）")
        return 1
    eid = match[0]
    ev = events[eid]
    if args.on:
        try:
            on = datetime.strptime(args.on, "%Y-%m-%d")
        except ValueError:
            print("× --on 需为 YYYY-MM-DD")
            return 1
        # 应验日与起卦日比较，看落在主/次应期的哪个候选上
        try:
            start = datetime.fromisoformat(str(ev.get("timestamp", ""))[:19])
            gap = (on.date() - start.date()).days
        except ValueError:
            gap = None
    else:
        on, gap = None, None

    rec = {
        "event_id": eid,
        "recorded_at": datetime.now().isoformat(timespec="seconds"),
        "question": ev.get("question", ""),
        "hexagram": ev.get("hexagram", ""),
        "predicted_verdict": ev.get("verdict", ""),
        "yingqi_main": ev.get("yingqi_main", ""),
        "yingqi_alt": ev.get("yingqi_alt") or [],
        "verdict_judgement": args.verdict,          # hit / miss / partial / na
        "yingqi_judgement": args.yingqi,            # main / alt / miss / early / late / na
        "verified_on": args.on or "",
        "days_after_divination": gap,
        "note": args.note or "",
    }
    OUTCOMES.parent.mkdir(parents=True, exist_ok=True)
    existing = [o for o in read_jsonl(OUTCOMES) if o.get("event_id") != eid]
    existing.append(rec)
    OUTCOMES.write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in existing),
                        encoding="utf-8")
    print(f"√ 已记录 {eid[:8]}：吉凶={args.verdict} 应期={args.yingqi} "
          + (f"应验日={args.on}（起卦后 {gap} 天）" if args.on else ""))
    if gap is not None and rec["yingqi_judgement"] == "main":
        main_branch = (rec["yingqi_main"] or "")[:1]
        actual = gc.day_ganzhi_of(on.year, on.month, on.day)[1]
        if main_branch and actual != main_branch:
            print(f"  注意：应验日实际日支为 {actual}，与主应期 {rec['yingqi_main']} 不合；"
                  f"如属提前/延后应验，可改用 --yingqi early|late 重记")
    return 0


def cmd_stats(args) -> int:
    outs = read_jsonl(OUTCOMES)
    if not outs:
        print("尚无回填记录。先跑 `python dev_tools/outcome.py list` 看欠哪些。")
        return 0
    v = [o.get("verdict_judgement") for o in outs if o.get("verdict_judgement") not in (None, "", "na")]
    y = [o.get("yingqi_judgement") for o in outs if o.get("yingqi_judgement") not in (None, "", "na")]
    def block(name: str, vals: list[str], positives: tuple[str, ...]) -> dict:
        n = len(vals)
        hits = sum(1 for x in vals if x in positives)
        lo, hi = wilson(hits, n) if n else (0.0, 0.0)
        d = {"n": n, "hits": hits}
        if n:
            d["rate_pct"] = round(hits * 100.0 / n, 1)
            d["wilson95"] = [round(lo * 100, 1), round(hi * 100, 1)]
            d["sufficient_n"] = n >= MIN_N_FOR_CONCLUSION
        return d
    vs, ys = block("吉凶方向", v, ("hit",)), block("应期（主应期算命中）", y, ("main",))
    ys_any = block("应期（主或备任一算命中）", y, ("main", "alt"))
    if args.json:
        print(json.dumps({"outcomes_total": len(outs), "verdict": vs,
                          "yingqi_strict": ys, "yingqi_inclusive": ys_any,
                          "min_n_for_conclusion": MIN_N_FOR_CONCLUSION},
                         ensure_ascii=False, indent=2))
        return 0
    print(f"回填记录 {len(outs)} 条")
    for label, d in (("吉凶方向", vs), ("应期·严格(仅主)", ys), ("应期·宽松(主或备)", ys_any)):
        if not d["n"]:
            print(f"  {label:18s} 无数据")
            continue
        flag = "样本足" if d["sufficient_n"] else f"样本不足(<{MIN_N_FOR_CONCLUSION})，仅为计数，不构成结论"
        print(f"  {label:18s} {d['hits']}/{d['n']} = {d['rate_pct']}% "
              f"[95%CI {d['wilson95'][0]}–{d['wilson95'][1]}]  {flag}")
    print("\n注：这是本仓库唯一能反映现实表现的指标；古籍对齐分衡量不了命中率。")
    return 0


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="实占结果回填与真实效度统计")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_l = sub.add_parser("list", help="列出待回填事件")
    p_l.add_argument("--limit", type=int, default=20)
    p_r = sub.add_parser("record", help="回填一条结果")
    p_r.add_argument("event_id")
    p_r.add_argument("--yingqi", choices=["main", "alt", "miss", "early", "late", "na"],
                     required=True, help="应期是否应验；early/late＝方向对但不在所列候选上")
    p_r.add_argument("--verdict", choices=["hit", "miss", "partial", "na"], required=True)
    p_r.add_argument("--on", help="实际应验公历日 YYYY-MM-DD")
    p_r.add_argument("--note", default="")
    p_s = sub.add_parser("stats", help="统计真实命中率（必带 n 与区间）")
    p_s.add_argument("--json", action="store_true")
    args = ap.parse_args()
    return {"list": cmd_list, "record": cmd_record, "stats": cmd_stats}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
