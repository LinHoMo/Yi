# -*- coding: utf-8 -*-
"""小六壬·规则推演（analyze 段）—— 纯机械，断语只取 data/verdicts.json。

输入 chart 段输出的课体（落宫），输出结构化的因子与判据：
  1. 落宫六要素（五行/颜色/方位/属神/主数/掌诀位置）——《贺氏六壬小手册》第一节
  2. 吉凶方向（六宫释义所定：大安/速喜/小吉吉，赤口/空亡凶，留连平）
  3. 事类诀辞（按 topic 取各宫『诀曰』切句）
  4. 应期主数（谋事主一五七/二八十/三六九/四七十）
  5. 邻宫速断（进/退/临，规则查 data/verdicts.json）
  6. 方位/五行综合断（生克关系查表，五行生克原语取 core）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
DISC = Path(__file__).resolve().parents[1]
for _p in (str(CORE), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from chart import CN_NUM as _CN, PALACES  # noqa: E402
from yishu_core.relations import wuxing_relation  # noqa: E402


def _load_verdicts() -> dict:
    p = DISC / "data" / "verdicts.json"
    return json.loads(p.read_text(encoding="utf-8"))


VERDICTS = _load_verdicts()

_WEIGHTS = {"落宫": 30, "吉凶方向": 30, "事类断语": 20, "应期主数": 20}


def _num_list(nums: list[int]) -> str:
    return "、".join(_CN[n] if n <= 10 else str(n) for n in nums)


def _neighbor_rule(palace_name: str, rel: str, neighbor_name: str) -> dict:
    """邻宫速断：先查 overrides，再按主速属性查通用交互表。纯查表。"""
    key = f"{palace_name}|{rel}|{neighbor_name}"
    hit = VERDICTS["neighbor_overrides"].get(key)
    if hit:
        return dict(hit)
    sc = VERDICTS["speed_class"]
    ikey = f"{sc[palace_name]}|{sc[neighbor_name]}"
    generic = VERDICTS["speed_interactions"].get(ikey) or {}
    out = dict(generic)
    out.setdefault("速断", "")
    out.setdefault("说明", "")
    out["所本"] = VERDICTS["speed_interaction_basis"]
    return out


def _neighbors(palace_idx: int, palace_name: str) -> dict:
    """落宫 + 进/退/临邻宫 → 速断结构（规则全在 verdicts.json）。"""
    meta = VERDICTS["neighbors_meta"]
    seq = meta["sequence"]
    sc = VERDICTS["speed_class"]
    jin_name = seq[(palace_idx + 1) % len(seq)]
    tui_name = seq[(palace_idx - 1) % len(seq)]

    def _entry(rel: str, name: str) -> dict:
        e = {"宫名": name, "关系": rel, "主速": sc.get(name, "")}
        e.update(_neighbor_rule(palace_name, rel, name))
        return e

    lin_list = [_entry("临", n) for n in meta["adjacency"].get(palace_name, [])]
    return {
        "进宫": _entry("进", jin_name),
        "退宫": _entry("退", tui_name),
        "临宫": lin_list,
        "所本": VERDICTS["neighbor_rule_basis"],
    }


def _direction_element(palace_name: str, target_direction: str | None) -> dict:
    """方位/五行综合断：方位→五行→与落宫五行生克（生克原语取 core）。"""
    p = VERDICTS["palaces"][palace_name]
    palace_el = p["五行"]
    out = {
        "输入方位": target_direction,
        "方位五行": None,
        "落宫五行": palace_el,
        "关系": None,
        "倾向": None,
        "说明": None,
        "所本": VERDICTS["direction_element_basis"],
    }
    if not target_direction:
        return out
    dir_el = VERDICTS["direction_element_map"].get(target_direction)
    if not dir_el:
        out["说明"] = VERDICTS["narrate_phrases"]["dir_unknown"].replace("{target_direction}", target_direction)
        return out
    rel = wuxing_relation(palace_el, dir_el)
    rel_meta = (VERDICTS["direction_relation"] or {}).get(rel) or {}
    out["方位五行"] = dir_el
    out["关系"] = rel
    out["倾向"] = rel_meta.get("倾向")
    out["说明"] = rel_meta.get("说明")
    return out


def analyze(chart_out: dict) -> dict:
    """chart 段输出 → 因子与判据（结构化，无成段断语）。"""
    palace_idx = chart_out["palace"]
    palace_name = PALACES[palace_idx]
    topic = chart_out.get("topic") or "人事"
    question = chart_out.get("question", "")

    p = VERDICTS["palaces"][palace_name]
    direction = VERDICTS["direction"][palace_name]

    # 事类诀辞：该宫对应 topic 的切句（v2 起为 {kind, text} 对象）；无此门时如实阙如
    topic_lines_map = VERDICTS["topic_lines"].get(topic) or {}
    entry = topic_lines_map.get(palace_name) or {}
    if isinstance(entry, str):                       # 兼容 v1 裸字符串（旧存档）
        entry = {"kind": "诀辞", "text": entry}
    line_kind = entry.get("kind") or "阙"
    line = entry.get("text") or ""
    if not line and line_kind != "阙":               # 未知事类：回退本宫总诀（逐字）
        line, line_kind = p["总诀"], "诀辞"
    if not line:                                     # 如实阙如：不造句、不冒充原文
        line, line_kind = "", "阙"

    steps = chart_out.get("steps") or []
    step_names = chart_out.get("step_names") or []
    steps_info = [{"步": n, "落宫": PALACES[i]}
                  for n, i in zip(step_names, steps)]

    # 综合判断标记：《贺氏》难点释疑3 明示不可死板套宫义的事类
    comprehensive_topics = {"出行", "求财"}
    comprehensive = topic in comprehensive_topics

    neighbors = _neighbors(palace_idx, palace_name)
    direction_element = _direction_element(palace_name, chart_out.get("direction"))

    conclusion = {
        "方向": direction,
        "说明": _conclusion_text(direction, palace_name, line, topic),
        "宫义": p["含义"],
        "所本": p["所本"],
    }

    return {
        "schema": "xiaoliuren-analyze-v2",
        "topic": topic,
        "question": question,
        "chart_summary": {
            "落宫": palace_name,
            "起课方式": chart_out.get("way"),
            "报数": chart_out.get("numbers"),
            "月日时": (f"{chart_out.get('month')}月{chart_out.get('day')}日"
                      if chart_out.get("way") == "month_day_hour" else None),
            "时辰序": chart_out.get("hour_ordinal"),
        },
        "steps": steps_info,
        "palace": {
            "宫名": palace_name,
            "五行": p["五行"],
            "颜色": p["颜色"] or "—",
            "方位": p["方位"] or "—",
            "属神": p["属神"],
            "位置": p["位置"],
            "主数": p["主数"],
            "含义": p["含义"],
            "总诀": p["总诀"],
            "方向": direction,
        },
        "neighbors": neighbors,
        "direction_element": direction_element,
        "topic_verdict": {
            "topic": topic,
            "诀句": line,
            "句类": line_kind,
            "覆盖": (VERDICTS.get("topic_coverage") or {}).get("per_topic", {}).get(topic),
            "宫义": p["含义"],
            "所本": VERDICTS["topic_line_basis"],
        },
        "timing": {
            "主数": p["主数"],
            "解读": f"谋事主{_num_list(p['主数'])}之数（时间、日辰或数量皆可应）",
            "所本": VERDICTS["number_basis"],
        },
        "comprehensive": comprehensive,
        "conclusion": conclusion,
        "factors": [
            {"因子": "落宫", "权重": _WEIGHTS["落宫"], "判据": palace_name,
             "所本": VERDICTS["narrate_phrases"]["basis_calc"]},
            {"因子": "吉凶方向", "权重": _WEIGHTS["吉凶方向"], "判据": direction,
             "所本": p["所本"]},
            {"因子": "事类断语", "权重": _WEIGHTS["事类断语"],
             "判据": f"{line or '（本门无据，阙）'}［{line_kind}］",
             "所本": VERDICTS["topic_line_basis"]},
            {"因子": "应期主数", "权重": _WEIGHTS["应期主数"], "判据": _num_list(p["主数"]),
             "所本": VERDICTS["number_basis"]},
            {"因子": "邻宫速断", "权重": 0, "判据": neighbors["进宫"].get("速断", ""),
             "所本": VERDICTS["neighbor_rule_basis"]},
            {"因子": "方位五行", "权重": 0,
             "判据": (direction_element.get("关系") or "未提供方位"),
             "所本": VERDICTS["direction_element_basis"]},
        ],
    }


def _conclusion_text(direction: str, palace: str, line: str, topic: str) -> str:
    """方向 + 事类诀句 → 一句结论底色（不出新象数结论，只装配）。

    三档底色措辞唯一真值源在 `verdicts.json#direction_tone`（此前硬编码在这段代码里，
    与 zeji 的 `narrate_phrases.sum_*` 是同一种重复形态）。
    """
    tone = VERDICTS["direction_tone"][direction]
    if line and line != VERDICTS["palaces"][palace]["总诀"]:
        return f"{tone}；就{topic}而言：{line}"
    return f"{tone}；{VERDICTS['palaces'][palace]['总诀']}"


if __name__ == "__main__":
    import argparse
    import json as _json

    ap = argparse.ArgumentParser(description="小六壬分析（analyze 段）")
    ap.add_argument("chart_json", nargs="?", help="chart 段输出 JSON 文件（缺省跑金标准自检）")
    ap.add_argument("-o", "--out", type=Path, help="写出 analyze JSON")
    args = ap.parse_args()

    if not args.chart_json:
        # 金标准自检：八月初十五申时 → 空亡（凶系）；报数77234 → 大安（吉系）
        from chart import chart_from_month_day_hour, chart_from_numbers
        a1 = analyze(chart_from_month_day_hour(8, 15, 9))
        assert a1["palace"]["宫名"] == "空亡", a1["palace"]
        assert a1["conclusion"]["方向"] == "凶", a1["conclusion"]
        assert a1["neighbors"]["进宫"]["宫名"] == "大安", a1["neighbors"]
        assert a1["neighbors"]["退宫"]["宫名"] == "小吉", a1["neighbors"]
        assert a1["direction_element"]["落宫五行"] == "土", a1["direction_element"]
        a2 = analyze(chart_from_numbers([7, 7, 2, 3, 4]))
        assert a2["palace"]["宫名"] == "大安", a2["palace"]
        assert a2["conclusion"]["方向"] == "吉", a2["conclusion"]
        assert a2["timing"]["主数"] == [1, 5, 7], a2["timing"]
        assert a2["neighbors"]["进宫"]["宫名"] == "留连", a2["neighbors"]
        # 留连临速喜「不久即归」——《贺氏》难点释疑3例3
        a3 = analyze({**chart_from_numbers([9, 9, 8, 6, 4]), "direction": "西方"})
        assert a3["palace"]["宫名"] == "留连", a3["palace"]
        assert a3["neighbors"]["临宫"][1]["宫名"] == "速喜", a3["neighbors"]
        assert a3["neighbors"]["临宫"][1]["速断"] == "不久即归", a3["neighbors"]
        assert a3["direction_element"]["方位五行"] == "金", a3["direction_element"]
        assert a3["direction_element"]["关系"] == "生我", a3["direction_element"]
        print("小六壬 analyze 校验通过（空亡/大安/留连临速喜三例方向、邻宫、方位五行正确）")
        raise SystemExit(0)

    chart_out = _json.loads(Path(args.chart_json).read_text(encoding="utf-8"))
    a = analyze(chart_out)
    text = _json.dumps(a, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        print("分析 →", args.out)
    else:
        print(text)
