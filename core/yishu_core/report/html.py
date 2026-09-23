# -*- coding: utf-8 -*-
"""单文件 HTML 呈现 kit：统一骨架 + 内联样式 + 页脚 + 写出。

历史：六爻曾有两套并行报告引擎（visualization 排盘报告 / build_html_report
解读报告），各自手写 DOCTYPE/head/style/footer，一副卦两种长相。本模块收敛
"骨架"这一层——任何学科报告都从这里组装单文件 HTML，学科层只提供 body
内容与要点（CONTRACT.md render 段：render(analyze_out) → 交内核 report 出 HTML/MD）。
"""

from __future__ import annotations

import html as _stdlib_html
from pathlib import Path


def escape(text) -> str:
    """HTML/XML 实体转义统一入口。"""
    if text is None:
        return ""
    return _stdlib_html.escape(str(text), quote=True)


def render_page(
    *,
    title: str,
    body: str,
    css: str,
    footer: str = "",
    script: str | None = None,
    container: bool = True,
) -> str:
    """组装单文件 HTML 页面。

    title     : <title> 文本（自动转义）
    body      : body 内容（标签页/卡片/表格/正文，由学科层组装）
    css       : CSS 文本，内联进 <style>
    footer    : 页脚文本（生成时间戳由调用方传入，保持报告语义）
    script    : <script> 内容（交互 JS，可选）
    container : 是否包 <div class="container">。排盘报告（标签页布局）用
                960px 居中容器；解读报告（全宽 header + 720px 正文）不包，
                容器宽度由学科 CSS 自行控制。
    """
    footer_html = f'    <div class="footer">{footer}</div>\n' if footer else ""
    script_html = f"<script>\n{script}\n</script>\n" if script else ""
    inner = f"{body}\n{footer_html}"
    if container:
        inner = f'<div class="container">\n{inner}</div>\n'
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f"<title>{escape(title)}</title>\n"
        f"<style>\n{css}\n</style>\n"
        "</head>\n"
        "<body>\n"
        f"{inner}"
        f"{script_html}"
        "</body>\n"
        "</html>\n"
    )


def write_html(text: str, path: str | Path) -> Path:
    """写出单文件 HTML，自动建父目录。"""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out
