# -*- coding: utf-8 -*-
"""命·因子推演（analyze 段）—— 机械格局/强弱/大运，不写命运断语。

输出契约与合参层对齐：
  {question, pillars, factors, shensha, ming_shen_gong,
   conclusion: {方向: "", verdicts: [机械标签], 说明, 所本,
                strength, pattern, useful_gods, dayun},
   chart_summary}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(CORE), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from pattern import strength_and_pattern, dayun_table, liunian_table  # noqa: E402


def analyze(chart_json: dict) -> dict:
    """chart JSON → analyze JSON。产出机械标签，不产出命运吉凶。"""
    result = dict(chart_json)
    pillars = result.get("pillars") or {}
    sp = strength_and_pattern(result)
    dayun = dayun_table(result)
    liunian = liunian_table(result, n=12)

    summary = {
        "四柱": {k: (v or {}).get("ganzhi") for k, v in pillars.items()},
        "日主": (pillars.get("day") or {}).get("stem"),
        "命宫": (result.get("ming_shen_gong") or {}).get("ming_gong"),
        "身宫": (result.get("ming_shen_gong") or {}).get("shen_gong"),
        "强弱": sp.get("strength"),
        "格局": sp.get("pattern"),
        "喜用": "、".join(sp.get("useful_gods") or []),
        "空亡": result.get("xunkong") or [],
    }

    verdicts = [
        {
            "code": "strength",
            "label": sp.get("strength"),
            "basis": f"生扶{sp.get('sheng_fu')} − 克泄耗{sp.get('ke_xie_hao')} = {sp.get('strength_score')}"
                     f"（得令加权 {sp.get('decree_bonus')}）",
        },
        {
            "code": "pattern",
            "label": sp.get("pattern"),
            "basis": sp.get("pattern_basis") or "",
        },
    ]
    if sp.get("tentative_special"):
        verdicts.append({
            "code": "special_pattern",
            "label": sp.get("tentative_special"),
            "basis": sp.get("from_basis") or "仅条件识别，未作定论；需人工复核",
        })
    if dayun:
        verdicts.append({
            "code": "dayun",
            "label": f"大运 8 步（{dayun[0]['ganzhi']}→{dayun[-1]['ganzhi']}）",
            "basis": "顺逆按年干阴阳×性别；起运岁≈距节气日数/3（三日=一年，一日=四月）",
        })
    if result.get("xunkong"):
        verdicts.append({
            "code": "xunkong",
            "label": "空亡 " + "、".join(result["xunkong"]),
            "basis": "日柱所在旬之空亡（core.symbols.xunkong_of）",
        })

    return {
        **result,
        "chart_summary": summary,
        "strength": sp,
        "dayun": dayun,
        "conclusion": {
            "方向": "",
            "verdicts": verdicts,
            "说明": (
                f"机械推演：{sp.get('strength')}·{sp.get('pattern')}；"
                f"喜用={'、'.join(sp.get('useful_gods') or [])}。"
                "不含命运吉凶断言；大运干支为近似起运。"
            ),
            "所本": "扶抑用神通行口径 + 月令本气十神定格 + core.ming_tables",
            "应期": [],
            "timing": [],
            "strength": sp.get("strength"),
            "strength_score": sp.get("strength_score"),
            "pattern": sp.get("pattern"),
            "useful_gods": sp.get("useful_gods") or [],
            "taboo_gods": sp.get("taboo_gods") or [],
            "dayun": dayun,
            "liunian": liunian,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="命·因子推演（analyze 段）")
    ap.add_argument("chart_json", nargs="?", help="chart 段输出")
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args()

    if args.chart_json:
        data = json.loads(Path(args.chart_json).read_text(encoding="utf-8"))
    else:
        from chart import chart as _chart

        data = _chart(datetime_str="1990-05-20 10:30", gender="男")

    out = analyze(data)
    text = json.dumps(out, ensure_ascii=False, indent=2, default=str)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
