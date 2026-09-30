# -*- coding: utf-8 -*-
"""六爻纳甲·一键闭环（M3.2）—— 一条命令从起卦到单文件报告。

    python scripts/yi_liuyao.py "占买房子何时有结果" --when "2024-06-01 10:00"
    python scripts/yi_liuyao.py "占今日运势"                     # time 起卦，用当前时刻
    python scripts/yi_liuyao.py "占投资" --mode manual --yao "7,8,9,7,6,8" -o out.html
    python scripts/yi_liuyao.py "占某事" --mode coin --seed 42   # 可复现摇卦
    python scripts/yi_liuyao.py "占某事" -f md                    # 纯 Markdown 报告

管线固定为 chart→analyze→render（四段契约），同一份 analyze JSON 出报告，
不另行断卦；HTML 出口即 render 段唯一出口（SVG 真卦盘 + 结要 + 正文 + 判据所本）。
"""
from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kernel_path import ensure_kernel_on_path  # noqa: E402

ensure_kernel_on_path(__file__)


def _summary(a: dict) -> list[str]:
    con = a.get("conclusion") or {}
    oh = a.get("original_hexagram") or {}
    ch = a.get("changed_hexagram") or {}
    lines = [f"问：{a.get('question') or ''}"]
    if oh.get("name"):
        lines.append(f"本卦：{oh['name']}"
                     + (f"（{oh.get('palace') or ''}宫·{oh.get('generation') or ''}）"
                        if oh.get("palace") else ""))
    if ch.get("name"):
        lines.append(f"变卦：{ch['name']}")
    if con.get("方向"):
        lines.append(f"结论：{con['方向']}")
    if con.get("应期"):
        lines.append("应期：" + "、".join(map(str, con["应期"])))
    return lines


def _collect_feedback(analyze_json: dict, report_path: Path) -> None:
    """--feedback 模式：占算后追加收集实际应验日期，写入 data/feedback/。

    数据与古籍案例物理隔离，永不参与调参。
    """
    print("\n── 应期反馈（可选，按回车跳过）──")
    print("提示：此数据仅用于独立评估，永不参与引擎调参。")
    raw = input("实际应验日期（YYYY-MM-DD，跳过按回车）：").strip()
    if not raw:
        print("跳过反馈记录。")
        return
    actual = raw
    description = input("简述事件经过（可空）：").strip()
    # 使用延迟 import 避免污染主流程依赖
    from dev_tools.feedback_store import FeedbackStore
    store = FeedbackStore("liuyao")
    record = {
        "analyze_json": analyze_json,
        "actual_date": actual,
        "actual_outcome": {"date": actual, "description": description},
        "report_path": str(report_path),
    }
    rid = store.save(record)
    print(f"反馈已记录 → data/feedback/{rid}.json")


def main() -> int:
    from yishu_core.runtime import force_utf8_stdio
    force_utf8_stdio()

    ap = argparse.ArgumentParser(
        description="六爻纳甲一键闭环：chart→analyze→render 单文件报告",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("question", help="求测问题（一卦一事，换角度请另起一卦）")
    ap.add_argument("--when", default=None,
                    help='时间起卦时刻，格式 "YYYY-MM-DD HH:MM"（缺省当前时刻）')
    ap.add_argument("--mode", choices=["coin", "time", "manual", "number"],
                    default="time", help="起卦方式（缺省 time，用 --when 的时刻）")
    ap.add_argument("--yao", default=None,
                    help='manual 模式的 6 个爻值，如 "7,8,9,7,6,8"（6动阴/7静阳/8静阴/9动阳）')
    ap.add_argument("--numbers", default=None,
                    help='number 模式的三个数字，如 "3,5,8"')
    ap.add_argument("--seed", type=int, default=None,
                    help="coin 模式随机种子（可复现）")
    ap.add_argument("-f", "--fmt", choices=["md", "html"], default="html",
                    help="输出格式（缺省 html 单文件报告）")
    ap.add_argument("-o", "--out", type=Path, default=None,
                    help="输出文件路径（缺省 outputs/reports/report_<时间戳>.<ext>）")
    ap.add_argument("--open", action="store_true",
                    help="完成后用默认浏览器打开（仅 html）")
    ap.add_argument("--feedback", action="store_true",
                    help="占算后追加收集实际应验日期（写入 data/feedback/，永不参与调参）")
    args = ap.parse_args()

    from chart import chart
    from analyze import analyze
    from render import render

    if args.mode == "manual" and not args.yao:
        ap.error("--mode manual 需要 --yao \"7,8,9,7,6,8\"")
    if args.mode == "number" and not args.numbers:
        ap.error('--mode number 需要 --numbers "a,b,c"')

    when = args.when
    if args.mode == "time" and not when:
        now = datetime.now()
        when = now.strftime("%Y-%m-%d %H:%M")

    c = chart(args.mode, args.question, datetime_str=when,
              yao=args.yao, numbers=args.numbers, seed=args.seed)
    a = analyze(dict(c))
    text = render(a, fmt=args.fmt)

    if args.out:
        out = args.out
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = "html" if args.fmt == "html" else "md"
        out = Path(__file__).resolve().parents[1] / "outputs" / "reports" \
            / f"report_{stamp}.{ext}"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")

    print("六爻纳甲一键闭环完成：")
    for line in _summary(a):
        print(f"  {line}")
    print(f"  报告 → {out}")

    if args.feedback:
        _collect_feedback(a, out)

    if args.fmt == "html" and args.open:
        webbrowser.open(out.resolve().as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
