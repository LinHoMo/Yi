# -*- coding: utf-8 -*-
"""六爻纳甲·正文叙述（narrate 段）—— 唯一交付正文，师傅口吻（CONTRACT §一）。

薄适配：读取 analyze JSON 中的排盘、思维链与高级分析数据，在
`format_reading_output` 的字段报表基础上做"翻译层"处理。

相较于直接透传字段报表，本层额外做四件事（均属适配层职责，不触碰引擎推演逻辑）：
1. **过滤内部量化暴露**：删除评分明细、综合评分、置信度百分比。
   这些是引擎内部的推演记账，对齐分≠预测准确率（AGENTS.md §三），
   对外暴露会把技术口径错念成"预测能力指标"。（口径诚实）
2. **六神临用融入正文**：`spirit_adjustment_reasons` 已是人话化文本
   （如"青龙临用，阳日力增，吉上添吉"），提取后嵌入叙述段落，
   不再只活在评分明细的括号里。
3. **持世从附录挪入正文**：持世是判断的核心辅助，应在正文叙事中
   自然呈现，不是末尾的补丁。若 `use_god_basis` 属推断/消歧/兜底
   类来源，如实标注"无古籍逐条出处"，不伪装成古籍定论。
4. **凶象措辞自然化**：象判边界声明以自然段落融入末尾，
   去"附录"感，去读起来像免责声明模板的生硬感。

正文每个象数判断都出自 analyze 输出，不新增结论。
"""
from __future__ import annotations
import json
from pathlib import Path as _P

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# format_reading_output 已弃用：正文主体改由 human_narrative.build_human_narrative 生成


_SHELL = json.loads((_P(__file__).resolve().parents[1] / 'data' / 'narrative_templates.json').read_text(encoding='utf-8')).get('narrate_shell', {})
_BOUNDARY_TEXT = _SHELL.get("disclaimer") or ""




def _filter_metric_exposure(text: str) -> str:
    """兜底过滤内部量化暴露——口径诚实（对齐 AGENTS.md §三）。

    正常情况下，正文由 human_narrative 生成，不会包含内部评分。
    此函数作为防御性层：若任何路径仍泄漏 format_reading_output 的
    评分明细/百分比，在此做最终拦截。
    """
    # 删除评分明细行
    text = re.sub(r"[ \t]+│? ?评分明细：[^\n]*\n?", "", text)
    # 删除括号内分数（如"平吉（0.58分）"）
    text = re.sub(r"（[\d.]+分）", "", text)
    # 删除评分数字
    text = re.sub(r"（评分 [\d.]+）", "", text)
    # 删除净效应数值
    text = re.sub(r"│ 动变净效应：[+\-][\d.]+（", "│ 动变净效应（", text)
    # 删除综合评分行
    text = re.sub(r"[ \t]*　　?综合评分：[^\n]*\n?", "", text)
    # 删除置信度行（含百分比）
    text = re.sub(r"[ \t]*│? ?置信度：[^\n]*\n?", "", text)
    text = re.sub(r"[ \t]*　　?置信　度：[^\n]*\n?", "", text)
    # 删除格局评分调整
    text = re.sub(r"——评分调整[+\-][\d.]+", "", text)
    # 删除置信度百分比（如 75%）
    text = re.sub(r"\d+%", "", text)
    return text


def _spirit_narrative(chain: dict) -> str:
    """六神临用：把 spirit_adjustment_reasons 转成自然句。

    `spirit_adjustment_reasons` 已由 chain_step5.py 以人话化方式生成，
    如"青龙临用，阳日力增，吉上添吉"。这里只做轻度清洗去量化因子标记。
    """
    reasons = (chain.get("step5_synthesis") or {}).get("spirit_adjustment_reasons") or []
    if not reasons:
        return ""
    cleaned = []
    for r in reasons:
        # 去掉内部的 (x1.3) 量化因子，保留人话描述
        r = re.sub(r"\(x[\d.]+\)", "", r).strip("，；、 ")
        if r:
            cleaned.append(r)
    if not cleaned:
        return ""
    return "。".join(cleaned) + "。"


def _shi_yao_narrative(a: dict) -> str:
    """持世叙述：读 advanced_analysis 已有人话数据，融入正文叙事。

    chain_narrate.analyze_shi_yao_relation 的 scenario_interpretation
    已经自带"X持世——"前缀，general 字段则不带。这里检测避免重复。
    """
    adv = a.get("advanced_analysis") or {}
    syr = adv.get("shi_yao_relation") or {}
    relation = syr.get("relation") or ""
    interp = syr.get("scenario_interpretation") or syr.get("general") or ""
    poem = syr.get("poem") or ""
    if not relation or not interp:
        return ""
    # scenario_interpretation 已以"X持世——"开头则直接用；否则加前缀
    if interp.startswith(f"{relation}持世") or interp.startswith(f"{relation}者"):
        parts = [interp]
    else:
        parts = [f"{relation}持世——{interp}"]
    if poem:
        parts.append(f"古歌诀有云：{poem}")
    return "　　".join(parts)


def _hexagram_body_narrative(chain: dict) -> str:
    """卦身叙述：辅助判断信号。"""
    chain.get("step5_synthesis") or {}
    note = (chain.get("step5_synthesis") or {}).get("hexagram_body_note") or ""
    return note.strip()


def _use_god_basis_narrative(chain: dict) -> str:
    """用神所本标注：推断/消歧/兜底类需如实说明出处。

    已带《增刪卜易》前缀的不需标注（有逐字可回查出处）。
    "推断""消歧""兜底""默认"等来源要在正文中点明"无古籍逐条出处"，
    避免把问题词典推测伪装成古籍定论。
    """
    s2 = chain.get("step2_use_god_identification") or {}
    basis = s2.get("use_god_basis") or ""
    if not basis:
        return ""
    if basis.startswith("《增刪卜易》"):
        return ""  # 有古籍原文引文，不需额外标注推断
    if any(kw in basis for kw in ("推断", "消歧", "兜底", "默认")):
        return f"（推断所本：{basis}）"
    return ""


def _build_narrative_block(a: dict, chain: dict) -> str:
    """构造正文的额外叙事段落，注入到数据展示之前给读者"读卦引导"。"""
    parts = []

    spir = _spirit_narrative(chain)
    if spir:
        parts.append(f"六神方面：{spir}")

    shiy = _shi_yao_narrative(a)
    if shiy:
        parts.append(shiy)

    body_note = _hexagram_body_narrative(chain)
    if body_note:
        parts.append(f"卦身信号：{body_note}")

    use_basis = _use_god_basis_narrative(chain)
    if use_basis:
        parts.append(use_basis)

    if not parts:
        return ""
    return "\n".join(parts) + "\n"


def narrate(a: dict) -> str:
    """analyze JSON → 完整正文（师傅口吻，人话叙述，口径诚实）。

    以 human_narrative 的叙事层为正文主体，替代 format_reading_output
    的原始字段报表结构。保留 六神临用/持世/卦身 三个专项叙事段，
    它们由 _build_narrative_block 生成，插入正文给读者"读卦引导"。

    整体结构：
      1. 专项叙事段（六神临用/持世/卦身/用神所本）
      2. 正文段落（结论→旺衰→病药/星煞→动变→格局→综合）
      3. 应期
      4. 趋避建议
      5. 经典引文
      6. 象判边界声明

    病药/星煞段由 human_narrative 从 analyze 的 bing_yao / shensha_panel
    组装（文案在 data/narrative_templates.json），本层不新增象数结论。
    """
    chain = a.get("thinking_chain") or {}
    # 注意：build_human_narrative 内部需要 reading 段字段与 thinking_chain，
    # 这里传递完整的 a（包含 thinking_chain），避免 _ensure_thinking_chain 抛异常。
    result = dict(a)

    # 1. 构造结构化叙事（human_narrative 提供）
    from liuyao_narrate import build_human_narrative
    narrative = build_human_narrative(result)

    # 2. 专项叙事段：六神临用 / 持世 / 卦身 / 用神所本
    narrative_block = _build_narrative_block(a, chain)

    # 3. 正文段落（human_narrative 已按"结论→旺衰→动变→格局→综合"排列）
    body_paragraphs = list(narrative.get("body") or [])
    # 在结论段（p1）之后插入专项叙事段，让读者先知道核心辅助信号
    if narrative_block and body_paragraphs:
        body_paragraphs = [body_paragraphs[0], narrative_block] + body_paragraphs[1:]
    elif narrative_block:
        body_paragraphs = [narrative_block]

    # 4. 应期段
    timing_plain = narrative.get("timing_plain") or ""
    timing_section = f"**时间上**：{timing_plain}" if timing_plain else ""

    # 5. 趋避建议
    advice_items = narrative.get("advice") or []
    advice_lines = []
    if advice_items:
        advice_lines = ["**可以这样做**："]
        for i, adv in enumerate(advice_items, 1):
            advice_lines.append(f"{i}. {adv}")

    # 6. 经典引文
    quotes = narrative.get("classical_quotes") or []
    quote_lines = []
    if quotes:
        # 引导句外置 narrative_templates.json#narrate_shell.quote_lead（与 liuyao_narrate 同一出处）
        quote_lines = [_SHELL.get("quote_lead") or "古人类似情境也说过："]
        for q in quotes:
            quote_lines.append(f"- （{q['source']}）{q['quote']}")

    # 7. 象判边界
    boundary = _BOUNDARY_TEXT

    # 8. 汇总
    parts = []
    for p in body_paragraphs:
        if p:
            parts.append(p)
    if timing_section:
        parts.append(timing_section)
    if advice_lines:
        parts.append("\n".join(advice_lines))
    if quote_lines:
        parts.append("\n".join(quote_lines))
    if boundary:
        parts.append(boundary)

    text = "\n\n".join(parts)

    # 9. 防御性过滤：确保无内部评分/百分比泄漏到交付正文（AGENTS.md §三）
    return _filter_metric_exposure(text)


def main() -> int:
    ap = argparse.ArgumentParser(description="六爻纳甲解读（narrate 段）")
    ap.add_argument("analyze_json", nargs="?", help="analyze 输出的 JSON 文件（缺省跑演示）")
    ap.add_argument("-o", "--out", type=Path, help="写出解读文本")
    args = ap.parse_args()

    if args.analyze_json:
        a = json.loads(Path(args.analyze_json).read_text(encoding="utf-8"))
    else:
        from analyze import analyze as _analyze
        from chart import chart as _chart
        a = _analyze(_chart("coin", "占当前所问之事", seed=42))

    text = narrate(a)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
