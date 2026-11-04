# -*- coding: utf-8 -*-
"""CLI 输出层：HTML／JSON／Text 三路输出（呈现可以依赖推演，推演不得依赖呈现）。

装卦入口在 `engine/_core.py`；本模块只做装配，三路文案与 `golden` 指纹不得变。
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
    """CLI 输出层补出卜象解读键（analyze 段走四段管道时自行产出，二者不重复计算）。

    category 由 step2 的 `question_class` 经 xiang.resolve_xiang_category 推导，
    与 analyze 段同口径，避免同一问句在两条路径上取到不同象类别。
    """
    if not isinstance(result, dict) or "trigram_interpretation" in result:
        return result
    out = dict(result)
    try:
        from trigram_symbolism import build_trigram_interpretation
        from xiang import resolve_xiang_category
        _step2 = ((out.get("thinking_chain") or {})
                  .get("step2_use_god_identification") or {})
        _cat = resolve_xiang_category(
            _step2.get("question_class", ""), out.get("question", ""))
        out["trigram_interpretation"] = build_trigram_interpretation(
            out, category=_cat)
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

    `render` 的 import 仍在函数内，保持「未安装时回退 JSON」的旧行为。
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
