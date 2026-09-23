# -*- coding: utf-8 -*-
"""样式层覆盖检查：报告里用到的类名，assets/report.css 必须都有定义。

    python tools/style_check.py

为什么单独设这道门：排盘报告与解读报告原先各带一套 CSS，合并成一份（assets/report.css）时
第一版只把"看起来像图形"的 12 条规则搬过来，同名选择器一让位，.container/.footer/.cell-*
等 29 个类当场没了定义——报告照样能生成、字段照样对，只是散架。
这类"内容没错、外观崩了"的回归，评分与金标准指纹都看不见，只能直接核对类名。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
from kernel_path import ensure_kernel_on_path  # noqa: E402

ensure_kernel_on_path(__file__)
CSS = DISC / "assets" / "report.css"


def defined_classes(css: str) -> set[str]:
    sel = "\n".join(re.findall(r"([^{}]+)\{", re.sub(r"/\*.*?\*/", "", css, flags=re.S)))
    return set(re.findall(r"\.([A-Za-z][\w-]*)", sel))


def used_classes(html: str) -> set[str]:
    return {c for grp in re.findall(r'class="([^"]+)"', html) for c in grp.split()}


def defined_in_document(html: str, page_css: str) -> set[str]:
    """定义域是**整份交付文档**：样式层之外，各 SVG 生成器还自带内嵌 <style>。

    早先只拿 report.css 当全域，一次报出 22 个"未定义"，全是误报——
    .cell-bg / .elem-hz / .gen-line 这些都定义在图形函数自己的 <style> 里。
    """
    out = defined_classes(page_css)
    for block in re.findall(r"<style>(.*?)</style>", html, re.S):
        out |= defined_classes(block)
    return out


def render_samples() -> dict[str, str]:
    """单一出口采样：render 段 HTML（M3.1 后报告产物只此一份）。"""
    from chart import chart
    from analyze import analyze
    from render import render
    a = analyze(chart("manual", "占买房子何时有结果", yao="7,8,7,7,8,7",
                      datetime_str="2024-06-01 10:00"))
    return {"render 报告": render(a, fmt="html")}


def main() -> int:
    from yishu_core.runtime import force_utf8_stdio
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="报告样式层覆盖检查")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if not CSS.exists():
        print(f"× 缺样式层 {CSS}")
        return 1
    page_css = CSS.read_text(encoding="utf-8")
    bad = 0
    for name, html in render_samples().items():
        defined = defined_in_document(html, page_css)
        missing = sorted(used_classes(html) - defined)
        bad += len(missing)
        mark = "√" if not missing else "×"
        print(f"  {mark} {name}: 用到 {len(used_classes(html))} 个类，未定义 {len(missing)} 个"
              + (f" → {missing[:10]}" if missing or args.verbose else ""))
    print(f"缺定义 {bad} 处（定义域含样式层与各 SVG 内嵌样式）")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
