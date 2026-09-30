# -*- coding: utf-8 -*-
"""把 docs/ 下的规划类 Markdown 渲染成**单文件 HTML**（便于直接给人看/分享）。

    python tools/doc_html.py docs/DEEP-DIVE-PLAN.md
    python tools/doc_html.py docs/NEW-DISCIPLINES.md docs/AI-SOP.md
    python tools/doc_html.py --all-plan     # 规划类文档一次全渲

为什么需要它：规划文档里满是表格，在 GitHub 上看还行，发给不做技术的人看就不行。
这里复用**报告同一套** CSS（`core/yishu_core/report/html.py`）与同一个轻量
markdown 转换器——文档与报告长同一个样子，也顺带把转换器的能力边界暴露在真实文本上。

产物路径：与源文件同目录、同名 `.html`。是否入库由你决定（默认建议 gitignore）。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core"
sys.path.insert(0, str(CORE))

from yishu_core.report.html import report_page_from_markdown, write_html  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

# 规划类文档：真正需要"发给人看"的那几份
PLAN_DOCS = (
    "docs/DEEP-DIVE-PLAN.md",
    "docs/NEW-DISCIPLINES.md",
    "docs/AI-SOP.md",
    "docs/YI-PLAN.md",
    "docs/ARCHITECTURE.md",
)

FOOTER = (
    "本文由 Yi 的文档渲染器生成（与报告同一套样式与转换器）。<br>"
    "文档中的分数一律为古籍案例对齐分（回归审计用），不是现实预测命中率。"
)


def render_one(src: Path, *, out: Path | None = None) -> Path:
    if not src.is_file():
        raise SystemExit(f"文件不存在：{src}")
    text = src.read_text(encoding="utf-8")
    title = src.stem
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    html = report_page_from_markdown(
        title=title, markdown=text,
        meta=f"源文件：{src.relative_to(ROOT).as_posix()}",
        footer=FOOTER,
    )
    dst = out or src.with_suffix(".html")
    write_html(html, dst)
    return dst


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="把规划类 Markdown 渲染成单文件 HTML")
    ap.add_argument("files", nargs="*", type=Path, help="要渲染的 Markdown 文件")
    ap.add_argument("--all-plan", action="store_true", help="渲染 PLAN_DOCS 里的全部")
    ap.add_argument("--outdir", type=Path, default=None, help="输出到别的目录（默认同目录）")
    args = ap.parse_args()

    targets: list[Path] = []
    if args.all_plan:
        targets += [ROOT / p for p in PLAN_DOCS]
    targets += [p if p.is_absolute() else (ROOT / p) for p in args.files]
    if not targets:
        ap.error("需要至少一个文件，或用 --all-plan")

    for src in targets:
        if not src.is_file():
            print(f"  × 跳过（不存在）：{src}")
            continue
        out = None
        if args.outdir:
            args.outdir.mkdir(parents=True, exist_ok=True)
            out = args.outdir / (src.stem + ".html")
        dst = render_one(src, out=out)
        try:
            shown = dst.relative_to(ROOT).as_posix()
        except ValueError:
            shown = str(dst)
        print(f"  √ {src.name:28s} → {shown}  ({dst.stat().st_size / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
