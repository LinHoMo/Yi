#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
六爻占卜事件日志系统 (Liu Yao Divination Event Logger)
======================================================
将每次占卜事件记录到 JSONL 文件，供后续分析与模型评估。

仅使用 Python 标准库。
"""

import hashlib
import json
import sys
import uuid
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

@dataclass
class DivinationEvent:
    """单次占卜事件（本标准库 JSONL 日志行对应的 dict 结构）。"""
    event_id: str = ""
    timestamp: str = ""
    question: str = ""
    method: str = ""
    seed: Optional[int] = None
    longitude: Optional[float] = None
    hexagram: str = ""
    changed_hexagram: str = ""
    use_god: str = ""
    verdict: str = ""
    final_score: float = 0.0
    signal_strength: str = ""
    confidence: str = ""
    hallucination_flags: list = field(default_factory=list)
    notes: str = ""
    result_hash: str = ""
    yingqi_main: str = ""
    yingqi_rule: str = ""
    yingqi_alt: list = field(default_factory=list)
    yingqi_window_days: int = 0
    outcome: str = ""
    verdict_hit: Optional[bool] = None
    yingqi_hit: Optional[str] = None
    verified_on: str = ""
    validation_timestamp: str = ""

def get_log_path() -> Path:
    """

    获取日志文件路径: ~/.meituan-catpaw/<uid>/skills/liu-yao/logs/divination_events.jsonl
    如果目录不存在则自动创建。
    """
    # 从当前脚本位置向上回溯确定 base 目录
    # 脚本位于 skills/liu-yao/scripts/ 下，日志在 skills/liu-yao/logs/
    script_dir = Path(__file__).resolve().parent
    log_dir = script_dir.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "divination_events.jsonl"



def _compute_result_hash(result: dict) -> str:
    """计算占卜结果的 SHA256 哈希值 (用于完整性校验)。"""
    content = json.dumps(result, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _extract_use_god(result: dict) -> str:
    """从完整结果中提取用神信息。"""
    chain = result.get("thinking_chain", {})
    if chain:
        step2 = chain.get("step2_use_god_identification", {})
        if isinstance(step2, dict):
            cat = step2.get("use_god_category", "")
            if cat:
                return cat
    hints = result.get("analysis_hints", {}).get("possible_use_gods", [])
    if hints and isinstance(hints[0], str):
        return hints[0]

    return ""


def _extract_verdict_info(result: dict) -> tuple[str, float, str]:
    """从完整结果中提取 (verdict, final_score, signal_strength)。"""
    chain = result.get("thinking_chain", {})
    step5 = None
    if chain:
        step5 = chain.get("step5_synthesis", {})

    if step5 and isinstance(step5, dict):
        verdict = step5.get("verdict", "")
        final_score = step5.get("final_score", 0.0)
        signal = str(step5.get("signal_strength", step5.get("confidence", "")))
        return verdict, float(final_score), signal
    return "", 0.0, ""


def _extract_yingqi(result: dict) -> dict:
    """取主/次应期与其法则。不落这几项，625 条历史记录就永远算不出应期命中率。"""
    chain = (result or {}).get("thinking_chain") or {}
    s5 = chain.get("step5_synthesis") or {}
    timing = s5.get("timing") or {}
    rules = timing.get("timing_rules") or []
    main = rules[0]["token"] if rules and isinstance(rules[0], dict) else ""
    rule = rules[0]["rule"] if rules and isinstance(rules[0], dict) else ""
    dates = (s5.get("yingqi_dates") or {}).get("dates") or []
    window = 0
    pick = None
    for d in dates:
        if isinstance(d, dict) and d.get("date") and main and str(d.get("branch")) == main[:1]:
            pick = d["date"]
            break
    if pick is None and dates and isinstance(dates[0], dict):
        pick = dates[0].get("date")
    if pick:
        try:
            from datetime import datetime as _dt
            d0 = _dt.fromisoformat(str(result["divination_time"]["datetime"])[:10])
            d1 = _dt.fromisoformat(pick)
            window = max((d1 - d0).days, 0)
        except Exception:
            window = 0
    return {
        "yingqi_main": main,
        "yingqi_rule": rule,
        "yingqi_alt": [r["token"] for r in rules[1:4] if isinstance(r, dict)],
        "yingqi_window_days": window,
    }


def log_divination(
    result: dict,
    notes: str = "",
    seed: Optional[int] = None,
    longitude: Optional[float] = None,
) -> str:
    """
    记录一次占卜事件到 JSONL 文件。

    Args:
        result: build_hexagram_result() 返回的完整结果字典
                 （可含思维链 advanced_analysis / thinking_chain）
        notes: 手动备注，供后续验证参考
        seed: 随机种子（如有）
        longitude: 经度（如有）

    Returns:
        event_id: 本次事件的 UUID
    """
   
    oh = result.get("original_hexagram", {})
    ch = result.get("changed_hexagram")

    verdict, final_score, signal = _extract_verdict_info(result)

    event = DivinationEvent(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        question=result.get("question", ""),
        method=result.get("method", ""),
        seed=seed,
        longitude=longitude,
        hexagram=oh.get("name", ""),
        changed_hexagram=ch.get("name", "") if ch else "",
        use_god=_extract_use_god(result),
        verdict=verdict,
        **_extract_yingqi(result),
        final_score=final_score,
        signal_strength=signal,
        confidence=signal,
        hallucination_flags=[],
        notes=notes,
        result_hash=_compute_result_hash(result),
    )

    log_path = get_log_path()
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")

    return event.event_id


def get_events(limit: int = 50) -> list[DivinationEvent]:
    """
    获取最近的占卜事件（按时间倒序）。

    Args:
        limit: 最多返回条数

    Returns:
        DivinationEvent 列表（最新在前）
    """
    log_path = get_log_path()
    if not log_path.exists():
        return []

    events = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                events.append(DivinationEvent(**data))
            except (json.JSONDecodeError, TypeError):
                continue
    events.reverse()
    return events[:limit]


def get_event(event_id: str) -> Optional[DivinationEvent]:
    """
    根据 event_id 获取单个事件。

    Args:
        event_id: 事件 UUID

    Returns:
        DivinationEvent 或 None
    """
    log_path = get_log_path()
    if not log_path.exists():
        return None

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("event_id") == event_id:
                    return DivinationEvent(**data)
            except (json.JSONDecodeError, TypeError):
                continue

    return None


def validate_event(event_id: str, outcome: str) -> bool:
    """
    事后验证：标记预测是否应验。

    更新对应事件的 outcome 和 validation_timestamp 字段。
    由于 JSONL 不可原地修改，重建整个文件。

    Args:
        event_id: 要验证的事件 ID
        outcome: 实际结果描述

    Returns:
        bool: 是否找到并更新了事件
    """
    log_path = get_log_path()
    if not log_path.exists():
        return False

    found = False
    timestamp = datetime.now(timezone.utc).isoformat()
    events = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("event_id") == event_id:
                    data["outcome"] = outcome
                    data["validation_timestamp"] = timestamp
                    found = True
                events.append(data)
            except (json.JSONDecodeError, TypeError):
                events.append(line)

    if not found:
        return False

    with open(log_path, "w", encoding="utf-8") as f:
        for event_data in events:
            if isinstance(event_data, dict):
                f.write(json.dumps(event_data, ensure_ascii=False) + "\n")
            else:
                f.write(event_data + "\n")

    return True

def get_statistics() -> dict:
    """统计历史占卜数据"""
    events = get_events(limit=99999)

    if not events:
        return {"total": 0}

    verdicts = [e.verdict for e in events]
    scores = [e.final_score for e in events]

    import statistics

    return {
        "total": len(events),
        "date_range": {
            "first": events[-1].timestamp,
            "last": events[0].timestamp,
        },
        "verdict_distribution": dict(Counter(
            "吉" if ("\u5409" in v and "\u51f6" not in v) else
            "凶" if "\u51f6" in v else "\u5e73"
            for v in verdicts
        )),
        "score_stats": {
            "mean": statistics.mean(scores),
            "stdev": statistics.stdev(scores) if len(scores) > 1 else 0,
            "min": min(scores),
            "max": max(scores),
            "median": statistics.median(scores),
        },
        "common_hexagrams": Counter(e.hexagram for e in events).most_common(5),
        "validation_rate": (
            sum(1 for e in events if e.notes) / len(events) * 100
        ),
    }


def search_events(question_contains: str = None,
                  verdict_filter: str = None,
                  date_from: str = None,
                  date_to: str = None) -> list:
    """条件检索历史记录"""
    events = get_events(limit=99999)
    results = []
    for e in events:
        if question_contains and question_contains not in e.question:
            continue
        if verdict_filter and verdict_filter not in e.verdict:
            continue
        if date_from and e.timestamp < date_from:
            continue
        if date_to and e.timestamp > date_to:
            continue
        results.append(e)
    return results



def main():
    """CLI 入口：查看 / 验证 / 统计 / 检索 / 导出 / 热力图。"""
    import argparse

    parser = argparse.ArgumentParser(
        description="六爻占卜事件日志管理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
子命令:
  list       列出最近占卜事件 (default: 20 条)
  show       查看单个事件详情 (需 --id)
  validate   事后标记验证结果 (需 --id, --outcome)
  stats      打印统计摘要 (verdict 分布、分数统计、常见卦)
  search     条件检索 (--question/--verdict/--date-from/--date-to)
  export     导出全部记录为 JSON 文件 (需 --output)
  heatmap    打印 verdict 分布 ASCII 柱状图

    示例:
  python event_logger.py list --limit 50
  python event_logger.py show --id <uuid>
  python event_logger.py validate --id <uuid> --outcome "投资获利"
  python event_logger.py stats
  python event_logger.py search --question "投资"
  python event_logger.py search --verdict "吉" --date-from "2025-07-01"
  python event_logger.py export --output data.json
  python event_logger.py heatmap
        """,
    )
    sub = parser.add_subparsers(dest="command", help="子命令")

   
    list_parser = sub.add_parser("list", help="列出最近事件")
    list_parser.add_argument("--limit", type=int, default=20, help="最大条数")
    show_parser = sub.add_parser("show", help="查看单个事件")
    show_parser.add_argument("--id", type=str, required=True, help="事件 UUID")
    val_parser = sub.add_parser("validate", help="事后验证事件")
    val_parser.add_argument("--id", type=str, required=True, help="事件 UUID")
    val_parser.add_argument("--outcome", type=str, required=True, help="实际结果")
    stats_parser = sub.add_parser("stats", help="查看统计信息")
    stats_parser.add_argument(
        "--format", choices=["text", "json"], default="text",
        help="输出格式 (默认 text)",
    )
    search_parser = sub.add_parser("search", help="条件检索历史记录")
    search_parser.add_argument("--question", type=str, default=None,
                               help="按问题关键词匹配 (包含)")
    search_parser.add_argument("--verdict", type=str, default=None,
                               help="按判语关键词匹配 (包含)")
    search_parser.add_argument("--date-from", type=str, default=None,
                               help="起始日期 (ISO 8601 前缀, 如 2025-07-01)")
    search_parser.add_argument("--date-to", type=str, default=None,
                               help="结束日期 (ISO 8601 前缀, 如 2025-08-01)")
    search_parser.add_argument("--limit", type=int, default=50,
                               help="最大返回条数")
    export_parser = sub.add_parser("export", help="导出为 JSON 文件")
    export_parser.add_argument("--output", "-o", type=str, required=True,
                               help="输出文件路径")
    export_parser.add_argument("--pretty", action="store_true",
                               help="美化 JSON 输出 (缩进2空格)")
    sub.add_parser("heatmap", help="打印 verdict 分布 ASCII 柱状图")

    args = parser.parse_args()

    if args.command == "list":
        events = get_events(limit=args.limit)
        if not events:
            print("暂无占卜事件记录。")
            return
        print(f"{'事件ID':<38} {'时间':<22} {'问题':<16} {'本卦':<6} {'变卦':<6} {'用神':<6} {'判语':<8}")
        print("-" * 120)
        for e in events:
            ts = e.timestamp[:19].replace("T", " ")
            q = (e.question[:14] + "..") if len(e.question) > 14 else e.question
            changed = e.changed_hexagram or "无"
            print(f"{e.event_id:<38} {ts:<22} {q:<16} {e.hexagram:<6} {changed:<6} {e.use_god:<6} {e.verdict:<8}")

    elif args.command == "show":
        event = get_event(args.id)
        if event is None:
            print(f"未找到事件: {args.id}")
            sys.exit(1)
        print(json.dumps(asdict(event), ensure_ascii=False, indent=2))

    elif args.command == "validate":
        success = validate_event(args.id, args.outcome)
        if success:
            print(f"事件 {args.id} 已标记验证结果: {args.outcome}")
        else:
            print(f"未找到事件: {args.id}")
            sys.exit(1)

    elif args.command == "stats":
        stats = get_statistics()
        if args.format == "json":
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            _print_stats(stats)

    elif args.command == "search":
        results = search_events(
            question_contains=args.question,
            verdict_filter=args.verdict,
            date_from=args.date_from,
            date_to=args.date_to,
        )
        results = results[: args.limit]
        if not results:
            print("未找到匹配的事件。")
            return
        print(f"共找到 {len(results)} 条匹配记录:\n")
        print(f"{'事件ID':<38} {'时间':<22} {'问题':<16} {'本卦':<6} {'判语':<8}")
        print("-" * 100)
        for e in results:
            ts = e.timestamp[:19].replace("T", " ")
            q = (e.question[:14] + "..") if len(e.question) > 14 else e.question
            print(f"{e.event_id:<38} {ts:<22} {q:<16} {e.hexagram:<6} {e.verdict:<8}")

    elif args.command == "export":
        events = get_events(limit=99999)
        export_data = [asdict(e) for e in events]
        indent = 2 if args.pretty else None
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=indent)
        print(f"已导出 {len(events)} 条记录到 {args.output}")

    elif args.command == "heatmap":
        _print_heatmap()

    else:
        parser.print_help()



def _print_stats(stats: dict) -> None:
    """以人类可读格式打印统计信息。"""
    if stats["total"] == 0:
        print("暂无占卜事件记录。")
        return

    print("=" * 50)
    print("        六爻占卜统计摘要")
    print("=" * 50)
    print(f"  总占卜次数: {stats['total']}")

    dr = stats["date_range"]
    first_str = dr["first"][:10] if dr.get("first") else "N/A"
    last_str = dr["last"][:10] if dr.get("last") else "N/A"
    print(f"  时间范围:   {first_str} ~ {last_str}")
    vd = stats["verdict_distribution"]
    if vd:
        total = sum(vd.values())
        print(f"\n  判语分布:")
        for label in ["吉", "平", "凶"]:
            count = vd.get(label, 0)
            pct = count / total * 100 if total else 0
            bar = "#" * int(pct / 5)
            print(f"    {label}: {count:>4} ({pct:5.1f}%) {bar}")

    # 分数统计
    ss = stats["score_stats"]
    print(f"\n  分数统计:")
    print(f"    均值:   {ss['mean']:+.4f}")
    print(f"    中位数: {ss['median']:+.4f}")
    print(f"    标准差: {ss['stdev']:.4f}")
    print(f"    最小值: {ss['min']:+.4f}")
    print(f"    最大值: {ss['max']:+.4f}")
    ch = stats["common_hexagrams"]
    if ch:
        print(f"\n  常见本卦 Top {len(ch)}:")
        for name, count in ch:
            print(f"    {name}: {count}")

    print(f"\n  备注填写率: {stats['validation_rate']:.1f}%")
    print("=" * 50)


def _print_heatmap() -> None:
    """打印 verdict 分布的 ASCII 柱状图。"""
    stats = get_statistics()
    if stats["total"] == 0:
        print("暂无数据，无法生成热力图。")
        return

    vd = stats["verdict_distribution"]
    labels = ["吉", "平", "凶"]
    counts = [vd.get(l, 0) for l in labels]

    if not any(counts):
        print("判语数据为空。")
        return

    max_count = max(counts)
    bar_max_width = 40

    print("\n  Verdict Distribution Heatmap")
    print("  " + "-" * 50)
    for label, count in zip(labels, counts):
        bar_len = int(count / max_count * bar_max_width) if max_count else 0
        bar = "*" * bar_len
        pct = count / stats["total"] * 100 if stats["total"] else 0
        print(f"  {label} | {bar:<{bar_max_width}} {count:>4} ({pct:4.1f}%)")
    print("  " + "-" * 50)
    print(f"  Total: {stats['total']} events\n")


if __name__ == "__main__":
    main()
