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
import tempfile
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
    "archive/NEW-DISCIPLINES.md",   # 2026-10-09 修正：原写 docs/NEW-DISCIPLINES.md 是死路径
    "docs/AI-SOP.md",
    "docs/YI-PLAN.md",
    "docs/ARCHITECTURE.md",
    "disciplines/ming/docs/EVAL-PLAN.md",
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


def run_selftest() -> int:
    """负例自证（§四.8）：清单能渲染＝正例；显式点名不存在文件＝必须非 0 退出。

    旧实现的病正是"目标不存在只打印跳过、然后 return 0"——所以这一条负例
    测的就是它有没有被改回来（不往仓库植任何文件，用的是必然不存在的路径）。
    """
    bad: list[str] = []
    for p in PLAN_DOCS:
        if not (ROOT / p).is_file():
            bad.append(f"PLAN_DOCS 里的死路径：{p}")
    probe = ROOT / "docs" / "__no_such_plan_probe__.md"
    rc = 0
    try:
        rc = _run_check([probe])
    except SystemExit as exc:      # argparse/SystemExit 也算"没有静默放过"
        rc = 1
    if rc == 0:
        bad.append("负例失败：点名不存在的文件仍退 0（沉默跳过复活）")
    if bad:
        print("× SELFTEST FAIL")
        for b in bad:
            print("   -", b)
        return 1
    print(f"SELFTEST PASS（正例 {len(PLAN_DOCS)} 例 + 负例 1 例）")
    return 0


def _run_check(files: list[Path]) -> int:
    """供 --selftest 复用的最小检查路径：只判在位与可渲染，返回退出码。"""
    missing = [f for f in files if not f.is_file()]
    for src in missing:
        print(f"  × 目标不存在：{src}")
    with tempfile.TemporaryDirectory(prefix="yi_dochtml_st_") as td:
        for src in files:
            if src.is_file():
                render_one(src, out=Path(td) / (src.stem + ".html"))
    return 1 if missing else 0


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="把规划类 Markdown 渲染成单文件 HTML")
    ap.add_argument("files", nargs="*", type=Path, help="要渲染的 Markdown 文件")
    ap.add_argument("--all-plan", action="store_true", help="渲染 PLAN_DOCS 里的全部")
    ap.add_argument("--outdir", type=Path, default=None, help="输出到别的目录（默认同目录）")
    ap.add_argument("--selftest", action="store_true",
                    help="负例自证：清单死路径与「点名不存在仍退 0」都必须被抓")
    ap.add_argument("--check", action="store_true",
                    help="只验「清单在位 + 渲染跑得通」，不落盘（给质量门用；失败退出码非 0）")
    args = ap.parse_args()
    if args.selftest:
        return run_selftest()

    targets: list[Path] = []
    if args.all_plan:
        targets += [ROOT / p for p in PLAN_DOCS]
    targets += [p if p.is_absolute() else (ROOT / p) for p in args.files]
    if not targets:
        ap.error("需要至少一个文件，或用 --all-plan")

    # §三 入口规约：失败必须非 0 退出。旧实现是 `print("× 跳过（不存在）") + continue`
    # 再 `return 0`——清单里躺着死路径（`docs/NEW-DISCIPLINES.md` 实测已迁 archive/）时
    # 照样"成功"，等于把人敲的入口变成假绿。
    missing = [t for t in targets if not t.is_file()]
    for src in missing:
        print(f"  × 目标不存在：{src.relative_to(ROOT) if src.is_relative_to(ROOT) else src}")

    rendered = 0
    with tempfile.TemporaryDirectory(prefix="yi_dochtml_") as td:
        for src in targets:
            if not src.is_file():
                continue
            try:
                dst = render_one(src, out=Path(td) / (src.stem + ".html")) if args.check \
                    else render_one(src, out=(args.outdir / (src.stem + ".html")) if args.outdir else None)
            except (SystemExit, OSError, ValueError) as exc:
                print(f"  × 渲染失败：{src} —— {exc}")
                missing.append(src)
                continue
            rendered += 1
            if args.check:
                size = dst.stat().st_size
                print(f"  √ 可渲染 {src.name}（{size / 1024:.1f} KB，--check 不落盘）")
            else:
                try:
                    shown = dst.relative_to(ROOT).as_posix()
                except ValueError:
                    shown = str(dst)
                print(f"  √ {src.name:28s} → {shown}  ({dst.stat().st_size / 1024:.1f} KB)")
    if args.check:
        print(f"DOC-HTML CHECK PASS（渲染 {rendered} 份，缺目标 {len(missing)}）"
              if not missing else f"× DOC-HTML CHECK FAIL（{len(missing)} 项不可用）")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
