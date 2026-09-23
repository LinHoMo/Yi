# -*- coding: utf-8 -*-
"""六爻纳甲·推演（analyze 段）—— 纯机械断卦，无解读成分（CONTRACT §一）。

读 chart 段输出的排盘 JSON，跑既有 `thinking_chain.run_thinking_chain`
与 `advice_framework.generate_advice`，输出带 conclusion 的 analyze JSON：
供 narrate/render 消费，也供合参层 `synthesis.normalize_liuyao` 归一化。

不引入任何新断法：结论全部来自既有引擎推演。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from thinking_chain import run_thinking_chain  # noqa: E402


def _conclusion_from(chain: dict, result: dict) -> dict:
    """从思维链 step5 装配 conclusion（与 synthesize.normalize_liuyao 对齐）。"""
    step5 = chain.get("step5_synthesis") or {}
    verdict = step5.get("verdict") or ""

    # 应期：dates[].date 为主，speed 为节奏；不取嵌套 dict 原样（保持结论可读）
    yingqi_dates = step5.get("yingqi_dates") or {}
    yingqi_list: list[str] = []
    if isinstance(yingqi_dates, dict):
        dates = yingqi_dates.get("dates") or []
        if isinstance(dates, list):
            for d in dates:
                if not isinstance(d, dict):
                    continue
                date = d.get("date")
                rule = d.get("rule")
                yingqi_list.append(date if not rule else f"{date}（{rule}）")
        speed = yingqi_dates.get("speed")
        if speed and str(speed).strip():
            yingqi_list.append(str(speed))

    return {
        "方向": verdict,
        "verdict": verdict,
        "说明": step5.get("verdict_description") or "",
        "最终得分": step5.get("final_score"),
        "置信度": step5.get("confidence"),
        "应期": yingqi_list,
        "所本": "六爻纳甲·思维链五步（用神·旺衰·动变·月日）",
    }


def _chart_summary(result: dict, chain: dict) -> dict:
    """盘面摘要：卦名/时刻/动爻/用神/旺衰——供合参层与其他科对齐。"""
    dt = result.get("divination_time") or {}
    oh = result.get("original_hexagram") or {}
    ch = result.get("changed_hexagram") or {}
    step5 = chain.get("step5_synthesis") or {}
    step2 = chain.get("step2_use_god_identification") or {}
    sel = step2.get("selected_use_god") or {}
    moving = [y for y in (oh.get("yao_lines") or []) if y.get("is_moving")]
    return {
        "卦名": oh.get("name"),
        "变卦": ch.get("name"),
        "时间": dt.get("datetime"),
        "年柱": dt.get("year_stem_branch"),
        "月柱": dt.get("month_stem_branch"),
        "日柱": dt.get("day_stem_branch"),
        "时柱": dt.get("hour_stem_branch"),
        "旬空": result.get("empty_branches") or [],
        "动爻": [y.get("position") for y in moving],
        "用神": sel.get("category") or step2.get("use_god_category"),
        "用神爻": sel.get("position"),
        "旺衰": step5.get("strength_level"),
    }


def analyze(chart_json: dict) -> dict:
    """chart JSON → analyze JSON（含 thinking_chain + conclusion）。"""
    result = dict(chart_json)
    chain_full = run_thinking_chain(result)
    chain = chain_full.get("thinking_chain", chain_full)

    verdict = ""
    step5 = chain.get("step5_synthesis") or {}
    if isinstance(step5, dict):
        verdict = step5.get("verdict", "")
    try:
        from advice_framework import generate_advice
        result["section_advice"] = generate_advice(
            verdict, result.get("question", ""), result)
    except ImportError:
        pass

    return {
        **result,
        "thinking_chain": chain,
        "chart_summary": _chart_summary(result, chain),
        "conclusion": _conclusion_from(chain, result),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="六爻纳甲推演（analyze 段）")
    ap.add_argument("chart_json", nargs="?", help="chart 段输出的 JSON 文件（缺省跑演示）")
    ap.add_argument("-o", "--out", type=Path, help="写出 analyze JSON（缺省打印 stdout）")
    args = ap.parse_args()

    if args.chart_json:
        chart_data = json.loads(Path(args.chart_json).read_text(encoding="utf-8"))
    else:
        from chart import chart as _chart
        chart_data = _chart("coin", "占当前所问之事", seed=42)

    out = analyze(chart_data)
    text = json.dumps(out, ensure_ascii=False, indent=2, default=str)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
