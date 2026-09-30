# -*- coding: utf-8 -*-
"""唯一呈现 kit：单文件 HTML 导出（CONTRACT.md render 段）。

学科层只组装 body 内容与要点，页面骨架统一从这里出，避免各科各写一套
HTML 模板（历史教训：六爻两套并行引擎一副卦两种长相）。
"""

from .html import escape, render_page, write_html
from .request import (
    DISCIPLINES,
    DISC_TITLE,
    REPORT_FOOTER,
    analyze_argv,
    chart_argv,
    norm_date,
    norm_iso,
    normalize_request,
    render_argv,
    report_meta,
    report_title,
)

__all__ = [
    "escape", "render_page", "write_html",
    "DISCIPLINES", "DISC_TITLE", "REPORT_FOOTER",
    "analyze_argv", "chart_argv", "render_argv",
    "norm_date", "norm_iso", "normalize_request", "report_meta", "report_title",
]
