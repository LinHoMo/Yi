# -*- coding: utf-8 -*-
"""六爻纳甲·推演（analyze 段）—— 结构推演 + 定性结论，不含成段正文（CONTRACT §一）。

读 chart 段输出的排盘 JSON，跑既有 `thinking_chain.run_thinking_chain`
与 `advice_framework.generate_advice`，输出带 conclusion 的 analyze JSON：
供 narrate/render 消费——本段是唯一产出 `conclusion` 的地方（CONTRACT §四）。

不引入任何新断法：结论全部来自既有引擎推演。
"""
from __future__ import annotations

import argparse
import json
import sys
# 第八十六批：本文件是门面入口，实测在 cp936（GBK）控制台上 `print(text)` 因正文里的
# 「•」直接 UnicodeEncodeError 崩溃——修法是重定向 stdout 编码，不是删字符。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from thinking_chain import run_thinking_chain  # noqa: E402
from bing_yao_shensha import evaluate_bing_yao, attach_shensha  # noqa: E402


def _conclusion_from(chain: dict, result: dict) -> dict:
    """从思维链 step5 装配 conclusion（与 synthesize.normalize_liuyao 对齐）。"""
    step5 = chain.get("step5_synthesis") or {}
    verdict = step5.get("verdict") or ""

    # 应期：dates[].date 为主，speed 为节奏；不取嵌套 dict 原样（保持结论可读）
    yingqi_dates = step5.get("yingqi_dates") or {}
    yingqi_list: list[str] = []
    yingqi_items: list[dict] = []
    if isinstance(yingqi_dates, dict):
        dates = yingqi_dates.get("dates") or []
        if isinstance(dates, list):
            for d in dates:
                if not isinstance(d, dict):
                    continue
                date = d.get("date")
                rule = d.get("rule")
                yingqi_list.append(date if not rule else f"{date}（{rule}）")
                if date:
                    yingqi_items.append({"date": date, "rule": rule or ""})
        speed = yingqi_dates.get("speed")
        if speed and str(speed).strip():
            yingqi_list.append(str(speed))

    # 应期窗口（第一百九十二批·D1 第一半）：从名次前 3 的日历候选纯派生——
    # 不引入新事实、不改任何既有键；断言窗化的结构底座（181 批读数：支池 top-3 对
    # 书载应支覆盖 52.3%/47.6%，top-1 仅 27.3%/33.3%——信息在窗不在点）。
    # 本键是事实容器：无概率、无吉凶、无「必应」措辞（AGENTS.md §一.3 在结构层的落点）。
    win_dates: list[str] = []
    _seen_d = set()
    for _it in yingqi_items:
        _d = _it.get("date")
        if _d and _d not in _seen_d:
            win_dates.append(_d)
            _seen_d.add(_d)
        if len(win_dates) >= 3:
            break
    _span = 0
    if win_dates:
        try:
            from datetime import date as _date
            _ds = sorted(_date.fromisoformat(x) for x in win_dates)
            _span = (_ds[-1] - _ds[0]).days + 1
        except ValueError:
            _span = 0
    window = {"候选": win_dates,
              "起": min(win_dates) if win_dates else "",
              "止": max(win_dates) if win_dates else "",
              "跨日": _span}

    return {
        "方向": verdict,
        "verdict": verdict,
        "说明": step5.get("verdict_description") or "",
        "最终得分": step5.get("final_score"),
        "信号强度": step5.get("signal_strength", step5.get("confidence")),
        "应期": yingqi_list,
        # 结构化应期候选（date+rule），供现实回填评分（dev_tools/outcome.py 通道）；按引擎给出顺序即名次
        "应期明细": yingqi_items,
        "应期窗口": window,
        "病药": (result.get("bing_yao") or {}),
        "星煞": (result.get("shensha_panel") or {}),
        "所本": "六爻纳甲·思维链五步（用神·旺衰·动变·月日）+ 病药/星煞结构化",
    }


def _chart_summary(result: dict, chain: dict) -> dict:
    """盘面摘要：卦名/时刻/动爻/用神/旺衰——供 MCP 层与报告层取用。"""
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


def _judgment_block(chain: dict, result: dict) -> dict:
    """判定块：九格判定的结构化产出（第三百二十批）。

    失败不静默：判定器导入不了或内部出错，就**不产出该键**并在日志里说明，
    绝不塞一个看起来像结论的空块。
    """
    try:
        from judge import judge_with_overlay
    except Exception as exc:  # pragma: no cover - 导入失败路径
        import logging
        logging.getLogger(__name__).warning(
            "judge 导入失败：判定块跳过（verdict 不受影响）。排查 sys.path 是否含 scripts/。",
            exc_info=True)
        return {}
    try:
        j = judge_with_overlay({
            "thinking_chain": chain,
            "question": result.get("question"),
            "original_hexagram": result.get("original_hexagram"),
        })
    except Exception as exc:  # pragma: no cover - 运行失败路径
        import logging
        logging.getLogger(__name__).warning("判定块生成失败：跳过（verdict 不受影响）。", exc_info=True)
        return {}
    ov = j.get("overlay") or {}
    return {
        "direction": j.get("direction"),
        "confidence": j.get("confidence"),
        "cell": j.get("cell"),
        "base_cell": j.get("base_cell"),
        "why": j.get("why"),
        "cites": j.get("cites") or [],
        "support": j.get("support") or [],
        "dissent": j.get("dissent") or [],
        "domain": j.get("domain") or "",
        "overlay": ov.get("id") or "",
        "verdict_now": (chain.get("step5_synthesis") or {}).get("verdict") or "",
    }


def analyze(chart_json: dict, judgment_enabled: bool = True) -> dict:
    """chart JSON → analyze JSON（含 thinking_chain + conclusion）。

    `judgment_enabled`（第三百二十批）：是否在 `conclusion` 里附上**判定块**
    （方向 × 置信的九格判定，与 `verdict` 并列对照）。
    默认开＝产物里有；关＝**该键整个不出现**（不是空块），契约面随之少一维。
    接线期 `verdict` 仍由现行引擎产出——两者并列，是为了能逐例对拍，
    不是因为判定器已经取代判词（`judgment_table.json.implementation.verdict` 在册）。
    """
    result = dict(chart_json)
    chain_full = run_thinking_chain(result)
    chain = chain_full.get("thinking_chain", chain_full)

    # 第三百五十批：chart 段不再产 `trigram_interpretation`（CONTRACT §六-1）；
    # 由 analyze 段补出。362 批：category 不再恒 `general`——改由 step2 的
    # `question_class` 推导（映射表 data/rules/xiang_layer.json），故装配点
    # 必须移到 chain 之后。graceful degradation 照旧：失败记 None，不阻塞推演。
    _cat = "general"
    try:
        from xiang import resolve_xiang_category
        _step2 = chain.get("step2_use_god_identification") or {}
        _cat = resolve_xiang_category(
            _step2.get("question_class", ""), result.get("question", ""))
        from trigram_symbolism import build_trigram_interpretation
        result["trigram_interpretation"] = build_trigram_interpretation(
            result, category=_cat)
    except Exception:
        result["trigram_interpretation"] = None
    # 362 批：象层——把卦爻辞/互体/六神象义/类象/方位收成一处带出处的块。
    # 纪律（CONTRACT §五-bis）：象层不进评分、不参与 verdict；失败即整块不产。
    try:
        from xiang import build_xiang
        _xiang = build_xiang(result, chain, category=_cat)
        if _xiang:
            result["xiang"] = _xiang
    except Exception as exc:  # pragma: no cover - 象层失败不得拖垮推演
        import logging
        logging.getLogger(__name__).warning(
            "象层装配失败：跳过（推演与 verdict 不受影响）：%s", exc, exc_info=True)

    step2 = chain.get("step2_use_god_identification") or {}
    step3 = chain.get("step3_strength_analysis") or {}
    if not step3:
        # 兼容键名差异
        for k, v in chain.items():
            if isinstance(v, dict) and "strength_level" in v:
                step3 = v
                break
    bing_yao = evaluate_bing_yao(step2, step3, chain.get("step5_synthesis") or {})
    shensha = attach_shensha(result, step3)
    result["bing_yao"] = bing_yao
    result["shensha_panel"] = shensha

    # 354 批：`section_advice` 从 analyze 迁呈现层（render/output 用
    # advice_framework.ensure_section_advice 补出）；analyze 不再产这段成句。

    conclusion = _conclusion_from(chain, result)
    if judgment_enabled:
        jb = _judgment_block(chain, result)
        if jb:
            conclusion["judgment"] = jb
    return {
        **result,
        "thinking_chain": chain,
        "chart_summary": _chart_summary(result, chain),
        "conclusion": conclusion,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="六爻纳甲推演（analyze 段）")
    ap.add_argument("chart_json", nargs="?", help="chart 段输出的 JSON 文件（缺省跑演示）")
    ap.add_argument("-o", "--out", type=Path, help="写出 analyze JSON（缺省打印 stdout）")
    ap.add_argument("--no-judgment", action="store_true",
                    help="不产出结论里的判定块（conclusion.judgment 整个不出现）")
    args = ap.parse_args()

    if args.chart_json:
        chart_data = json.loads(Path(args.chart_json).read_text(encoding="utf-8"))
    else:
        from chart import chart as _chart
        chart_data = _chart("coin", "占当前所问之事", seed=42)

    out = analyze(chart_data, judgment_enabled=not args.no_judgment)
    text = json.dumps(out, ensure_ascii=False, indent=2, default=str)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
