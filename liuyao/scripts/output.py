# -*- coding: utf-8 -*-
"""CLI 输出层（第三百四十九批）：HTML／JSON／Text 三路输出从 engine.py 搬出。

为什么搬：`CONTRACT.md §三` 的禁边 `engine.py → render` 是 310 批登记的两条既存
欠账之一——引擎门面在 `--html` 分支里直接 import 呈现层。349 批把整段输出逻辑
（含 HTML 的 `render_html` 调用）移到本模块：`engine.py` 只调 `output_result`，
不再直接触达 `render`；呈现层由本模块承担，符合“呈现可以依赖推演、推演不得依赖
呈现”的方向。

行为不变：三路分支的文案、缩进、`--save-html` 路径处理与 ImportError 回退
逐行照搬；`golden` 指纹不得变。`_apply_depth_to_result` 与 `format_*` 仍是
`engine_format` 的唯一真源，本模块只做装配。
"""
from __future__ import annotations

import json
import os
import sys

from engine_format import (
    _apply_depth_to_result,
    apply_depth_limit,
    format_reading_output,
    format_text_output,
)
from narrative_assembly import attach_narrative


def attach_trigram(result: dict) -> dict:
    """第三百五十批：chart 段不再产卜象解读；CLI 输出层在此补出。

    `engine.py` 直接消费 `build_hexagram_result`（chart），不再触达
    `trigram_symbolism`；为保持 engine 的 JSON/Text/HTML 输出面不变，本模块
    在输出前补键。`analyze.py` 走四段管道时自行产出同一键，二者不重复计算。
    """
    if not isinstance(result, dict) or "trigram_interpretation" in result:
        return result
    out = dict(result)
    try:
        from trigram_symbolism import build_trigram_interpretation
        out["trigram_interpretation"] = build_trigram_interpretation(
            out, category="general")
    except Exception:
        out["trigram_interpretation"] = None
    return out


def append_advice(text: str, result: dict, sep: str, title: str) -> str:
    """将 section_advice 追加到文本报告末尾，统一两种分隔符格式。"""
    if not result.get("section_advice"):
        return text
    parts = [text, "\n", sep, "\n", title, "\n"]
    parts += [f"  {i}. {a}\n" for i, a in enumerate(result["section_advice"], 1)]
    return "".join(parts)


def output_result(result: dict, chain, output_format: str, depth: str, args) -> None:
    """输出三路分支：HTML 委托 render.py / JSON 原始 / Text 委托 engine_format。

    349 批：本模块是 CLI 呈现层，`engine.py` 不再直接 import `render`；
    `render` 的 import 仍留在函数内，保持“未安装时回退 JSON”的旧行为。
    """
    result = attach_trigram(result)
    result = attach_narrative(result)
    if isinstance(chain, dict) and isinstance(result.get("thinking_chain"), dict):
        chain = result["thinking_chain"]
    if output_format == "html":
        try:
            from render import render_html
            a = dict(result)
            a["thinking_chain"] = chain
            html_out = render_html(a)
            save_path = getattr(args, "save_html", None)
            if save_path:
                save_dir = os.path.dirname(save_path)
                if save_dir and not os.path.exists(save_dir):
                    os.makedirs(save_dir, exist_ok=True)
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(html_out)
                print(f"[已保存] HTML 报告 → {save_path}", file=sys.stderr)
            if getattr(args, "open_browser", False):
                import tempfile
                import webbrowser
                if not save_path:
                    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False,
                                                     mode="w", encoding="utf-8")
                    tmp.write(html_out)
                    tmp.close()
                    save_path = tmp.name
                webbrowser.open(f"file:///{save_path.replace(os.sep, '/')}")
            if not save_path:
                print(html_out)
        except ImportError:
            print("[WARN] render module not installed, fallback to JSON", file=sys.stderr)
            _apply_depth_to_result(result, depth)
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    elif output_format == "json":
        _apply_depth_to_result(result, depth)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    elif output_format == "text":
        if chain is not None:
            full_text = format_reading_output(result, chain)
            full_text = append_advice(full_text, result, "=" * 52, "【趋避建议】")
        else:
            full_text = format_text_output(result)
            full_text = append_advice(full_text, result, "-" * 50, "趋避建议：")
        print(apply_depth_limit(full_text, depth))
    else:
        # 默认：纯文本
        full_text = format_text_output(result)
        full_text = append_advice(full_text, result, "-" * 50, "趋避建议：")
        print(apply_depth_limit(full_text, depth))
