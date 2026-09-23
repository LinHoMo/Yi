# -*- coding: utf-8 -*-
"""唯一呈现 kit：单文件 HTML 导出（CONTRACT.md render 段）。

学科层只组装 body 内容与要点，页面骨架统一从这里出，避免各科各写一套
HTML 模板（历史教训：六爻两套并行引擎一副卦两种长相）。
"""

from .html import escape, render_page, write_html

__all__ = ["escape", "render_page", "write_html"]
