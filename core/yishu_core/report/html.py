# -*- coding: utf-8 -*-
"""单文件 HTML 呈现 kit：统一骨架 + 内联样式 + 页脚 + 写出。

历史：六爻曾有两套并行报告引擎（visualization 排盘报告 / build_html_report
解读报告），各自手写 DOCTYPE/head/style/footer，一副卦两种长相。本模块收敛
"骨架"这一层——任何学科报告都从这里组装单文件 HTML，学科层只提供 body
内容与要点（CONTRACT.md render 段：render(analyze_out) → 交内核 report 出 HTML/MD）。
"""

from __future__ import annotations

import html as _stdlib_html
import re
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


# markdown 块级标记（行首）→ 正则替换为 HTML；不解析行内语法以外的内容
_MD_BLOCK_RULES = (
    (re.compile(r"^##### (.*)$"), r"<h5>\1</h5>"),
    (re.compile(r"^#### (.*)$"), r"<h4>\1</h4>"),
    (re.compile(r"^### (.*)$"), r"<h3>\1</h3>"),
    (re.compile(r"^## (.*)$"), r"<h2>\1</h2>"),
    (re.compile(r"^# (.*)$"), r"<h1>\1</h1>"),
    (re.compile(r"^\|(.*)\|$"), None),  # 表格行 → 交给 _md_table
)


def _md_table(lines: list[str], i: int) -> tuple[str, int]:
    """把连续的 markdown 表格行转成一个 <table>，返回 (html, 下一行下标)。"""
    head = lines[i].strip("|").split("|")
    j = i + 1
    if j < len(lines) and set(lines[j].strip().replace("|", "").replace("-", "").replace(":", "")) == set():
        j += 1  # 分隔行
    rows = []
    for k in range(j, len(lines)):
        row = lines[k].strip()
        if not row.startswith("|"):
            break
        cells = [f"<td>{_md_inline(c.strip())}</td>" for c in row.strip("|").split("|")]
        rows.append(f"<tr>{''.join(cells)}</tr>")
        j = k + 1
    thead = "".join(f"<th>{_md_inline(c.strip())}</th>" for c in head)
    return f"<table><thead><tr>{thead}</tr></thead><tbody>{''.join(rows)}</tbody></table>", j


def _md_inline(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return escape(text)


def _is_aligned_block(lines: list[str]) -> bool:
    """判定连续文本块是否含对齐痕迹（排盘表等多列空格对齐文本）。

    narrate 等正文里的排盘表是"空格对齐"而非 markdown 表格：行内出现连续
    2+ 半角/全角空格（夹在非空格字符之间）即视为对齐块，包 <pre> 保形。
    """
    hits = 0
    for line in lines:
        if re.search(r"\S(?: {2,}|　{2,})\S", line):
            hits += 1
    return hits >= 2


def md_to_html(text: str) -> str:
    """轻量 markdown → HTML（标题/表格/列表/粗体/行内码/对齐文本块）。
    只做呈现转换，不解析链接与引用语法；段落按空行切分。"""
    lines = text.split("\n")
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("|"):
            tbl, i = _md_table(lines, i)
            out.append(tbl)
            continue
        matched = False
        for pat, repl in _MD_BLOCK_RULES:
            if pat.match(line):
                if repl is not None:
                    out.append(pat.sub(repl, line))
                matched = True
                break
        if matched:
            i += 1
            continue
        if stripped.startswith("- "):
            items, j = [], i
            while j < n and lines[j].strip().startswith("- "):
                items.append(f"<li>{_md_inline(lines[j].strip()[2:])}</li>")
                j += 1
            out.append(f"<ul>{''.join(items)}</ul>")
            i = j
            continue
        # 连续段落行（空行前）→ 对齐痕迹则保形成 <pre>，否则 <p>
        block, j = [], i
        while j < n and lines[j].strip():
            block.append(lines[j])
            j += 1
        if _is_aligned_block(block):
            inner = "\n".join(escape(l) for l in block)
            out.append(f"<pre>{inner}</pre>")
        else:
            out.append(f"<p>{_md_inline(block[0])}</p>" if len(block) == 1
                       else f"<p>{'<br>'.join(_md_inline(l) for l in block)}</p>")
        i = j
    return "\n".join(out)
