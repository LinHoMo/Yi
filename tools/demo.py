# -*- coding: utf-8 -*-
"""易·交互演示：一条命令看各科在跑什么、合参怎么合。

  python tools/demo.py                       # 全科演示（六爻/梅花/小六壬/择吉 + 合参），
                                             #   汇总写到 tools/scratch/demo/（gitignored）
  python tools/demo.py --discipline meihua --question "占今年财运如何"
                                             # 单科问答：chart→analyze→narrate 一条龙
  python tools/demo.py --list                # 列出可演示的学科

所有演示都走各科真实 CLI（与 SKILL.md 文档命令一致），不绕过脚本。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core"
SCRATCH = ROOT / "tools" / "scratch" / "demo"
sys.path.insert(0, str(CORE))
sys.path.insert(0, str(ROOT / "synthesis"))

from yishu_core.runtime import force_utf8_stdio  # noqa: E402

DISCIPLINES = {
    "liuyao": "六爻纳甲",
    "meihua": "梅花易数",
    "xiaoliuren": "小六壬",
    "zeji": "择吉",
}


def _run(cmd: list[str]) -> str:
    p = subprocess.run([sys.executable, *cmd], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=300)
    if p.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:2])} 失败：{(p.stderr or p.stdout)[-500:]}")
    return p.stdout.strip()


def _pipeline(disc: str, chart_args: list[str]) -> tuple[dict, str, str]:
    """chart → analyze → narrate。返回 (analyze, narrate文本, 报告文本)。"""
    SCRATCH.mkdir(parents=True, exist_ok=True)
    c = SCRATCH / f"{disc}_chart.json"
    a = SCRATCH / f"{disc}_analyze.json"
    n = SCRATCH / f"{disc}_narrate.md"
    _run(["disciplines/{}/scripts/chart.py".format(disc), *chart_args, "-o", str(c)])
    _run(["disciplines/{}/scripts/analyze.py".format(disc), str(c), "-o", str(a)])
    _run(["disciplines/{}/scripts/narrate.py".format(disc), str(a), "-o", str(n)])
    analyze = json.loads(a.read_text(encoding="utf-8"))
    return analyze, n.read_text(encoding="utf-8"), str(n)


def demo_liuyao(question: str) -> tuple[dict, str, str]:
    """六爻四段契约（M3.2 一键闭环同构）：chart → analyze → render 单文件 HTML。"""
    SCRATCH.mkdir(parents=True, exist_ok=True)
    c = SCRATCH / "liuyao_chart.json"
    a = SCRATCH / "liuyao_analyze.json"
    r = SCRATCH / "liuyao_report.html"
    when = datetime.now().strftime("%Y-%m-%d %H:%M")
    _run(["disciplines/liuyao/scripts/chart.py", "--mode", "time",
          "--datetime", when, "--question", question, "-o", str(c)])
    _run(["disciplines/liuyao/scripts/analyze.py", str(c), "-o", str(a)])
    _run(["disciplines/liuyao/scripts/render.py", str(a), "-f", "html", "-o", str(r)])
    analyze = json.loads(a.read_text(encoding="utf-8"))
    con = analyze.get("conclusion") or {}
    oh = analyze.get("original_hexagram") or {}
    ch = analyze.get("changed_hexagram") or {}
    text = (f"问：{question}\n\n本卦 **{oh.get('name', '?')}**"
            f"（变 {ch.get('name', '无动爻之变')}）。结论：{con.get('方向', '见报告')}。"
            f"\n完整报告：`{Path(r).relative_to(ROOT)}`（单文件 HTML，浏览器直开）")
    return analyze, text, str(r)


def demo_single(disc: str, question: str) -> tuple[dict, str, str]:
    chart_args = {
        "meihua": ["--datetime", "2026-09-23 10:30", "--question", question],
        "xiaoliuren": ["--way", "datetime", "--datetime", "2026-09-23 10:30",
                       "--question", question],
        "zeji": ["--date", "2026-09-29", "--question", question],
    }[disc]
    return _pipeline(disc, chart_args)


def demo_all() -> int:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    lines: list[str] = ["# 易 · 全科演示", "",
                        f"> 生成于 {__import__('datetime').date.today()}，"
                        f"全部走各科真实 CLI。", ""]

    # 六爻
    q1 = "占本月工作调动能否成"
    _, txt1, src1 = demo_liuyao(q1)
    lines += ["## 一、六爻纳甲（liuyao）", "", f"**问**：{q1}", "", txt1,
              "", f"（报告：`{Path(src1).relative_to(ROOT)}`）", ""]

    # 梅花 / 小六壬 / 择吉
    cases = [
        ("meihua", "占今年财运如何"),
        ("xiaoliuren", "占今年财运如何"),
        ("zeji", "今日签约收款吉利否"),
    ]
    for i, (disc, q) in enumerate(cases):
        _, text, src = demo_single(disc, q)
        lines += [f"## {['二', '三', '四'][i]}、{DISCIPLINES[disc]}（{disc}）", "",
                  f"**问**：{q}", "", text, "",
                  f"（报告：`{Path(src).relative_to(ROOT)}`）", ""]

    # 合参演示
    lines += ["## 五、合参演示（synthesis）", ""]
    lines += _demo_synthesis()
    summary = "\n".join(lines) + "\n"
    out = SCRATCH / "demo.md"
    out.write_text(summary, encoding="utf-8")
    print(f"全科演示完成 → {out}")
    for src in (SCRATCH / "meihua_report.md", SCRATCH / "xiaoliuren_report.md",
                SCRATCH / "zeji_report.md"):
        if src.exists():
            src.unlink()
    return 0


def _demo_synthesis() -> list[str]:
    """用本轮演示的梅花/小六壬/择吉输出合参，出一份阶段性指导（写到 scratch）。"""
    from person import PersonArchive
    from normalize import normalize
    from cross_rules import adjudicate
    from guidance import write_guidance

    person_dir = SCRATCH / "person"
    guidance_dir = SCRATCH / "guidance"
    pfile = person_dir / "P001.json"
    if pfile.exists():
        pfile.unlink()

    arch = PersonArchive.create(
        "P001", "1990-05-20 07:15", longitude=116.4,
        ganzhi={"year": "庚午", "month": "辛巳", "day": "壬辰", "hour": "丙辰"},
        policy={"boundary": "day", "zi_hour": "night_same_day"})
    for disc, fn in (("meihua", "meihua_analyze.json"),
                     ("xiaoliuren", "xiaoliuren_analyze.json"),
                     ("zeji", "zeji_analyze.json")):
        a = json.loads((SCRATCH / fn).read_text(encoding="utf-8"))
        rec = normalize(disc, a)
        arch.add_divination(rec)
    arch.add_divination({  # 越位样例：卜科问命域，应被裁决剔除
        "discipline": "xiaoliuren", "asked": "我这一生的命运如何",
        "direction": "吉", "at": "2026-09-23", "verdict": "大安·…",
    })
    arch.save(person_dir)
    recs = arch.data["divinations"]
    adj = adjudicate(recs, policies=[r.get("calendar_policy") for r in recs])
    out = write_guidance(arch, adj, guidance_dir)
    text = out.read_text(encoding="utf-8")
    return [f"档案 P001（1990-05-20 出生）+ 三次占问 + 一条越位样例，"
            f"裁决：**{adj['pattern']} / {adj['trend']}**，"
            f"剔除越位 {len(adj['excluded'])} 条，未参评维度 {adj['missing'] or '无'}。", "",
            text, ""]


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="易·全科演示")
    ap.add_argument("--discipline", choices=list(DISCIPLINES),
                    help="单科问答（缺省全科演示）")
    ap.add_argument("--question", default="占今年财运如何", help="问句")
    ap.add_argument("--list", action="store_true", help="列出可演示学科")
    args = ap.parse_args()

    if args.list:
        for k, v in DISCIPLINES.items():
            print(f"  {k:<12s} {v}")
        return 0
    if args.discipline:
        if args.discipline == "liuyao":
            _, text, src = demo_liuyao(args.question)
            print(text)
            print(f"（报告：{src}）")
            return 0
        _, text, src = demo_single(args.discipline, args.question)
        print(text)
        print(f"（报告：{src}）")
        return 0
    return demo_all()


if __name__ == "__main__":
    raise SystemExit(main())
