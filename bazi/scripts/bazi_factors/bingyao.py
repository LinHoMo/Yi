# -*- coding: utf-8 -*-
"""bingyao —— 病药 (《神峰通考·病药说类》/《雕枯旺弱四病说类》)。
"""
from __future__ import annotations

from ._common import (
    _BING,
    _god_detail,
    BING_RULES_BY_GOD,
    BING_RULES_BY_KE,
    BRANCH_ELEMENTS,
    STEM_ELEMENTS,
    TEN_GOD_GROUP,
)


def bing_yao(chart_json: dict, strength: str = "") -> dict:
    """病药结构（《神峰通考·病药说类》）。

    两条机械路径：
      1. 五行层：主轴五行（月令本气）过剩为病，所克者为药。
      2. 十神层：病药成对共现则成立。

    返回 {thesis, axis_element, element_counts, bing, consumed_by_bing,
    medicines, has_medicine, provenance, note, basis}。
    """
    pillars = chart_json.get("pillars") or {}
    counts: dict[str, int] = {}
    for key in ("year", "month", "day", "hour"):
        p = pillars.get(key) or {}
        for el in (STEM_ELEMENTS.get(p.get("stem") or ""),
                   BRANCH_ELEMENTS.get(p.get("branch") or "")):
            if el:
                counts[el] = counts.get(el, 0) + 1
    if not counts:
        return {}
    # 主轴 = 月令本气
    month_branch = (pillars.get("month") or {}).get("branch") or ""
    day_stem = (pillars.get("day") or {}).get("stem") or ""
    axis = BRANCH_ELEMENTS.get(month_branch) or STEM_ELEMENTS.get(day_stem) or ""
    if not axis:
        return {}
    bing_elem_name, yao_elem, bing_prov = BING_RULES_BY_KE.get(axis, ("", "", ""))
    bing = {
        "病": bing_elem_name,
        "病之五行": axis,
        "主轴": axis,
        "所重": counts.get(axis, 0),
        "药": yao_elem,
        "药在局中": bool(yao_elem) and yao_elem in counts,
        "provenance": bing_prov,
        "basis": (f"《神峰通考·病药说类》「如八字中看了日干，次看了月令，且如月令中支中"
                  f"所属是{axis}，先看月令中此一{axis}字起，又看年上或{axis}，又看月时上"
                  f"或有{axis}，宜将以上各{axis}做一处看，或为病，或非病…故曰：从重者论」；"
                  f"本造月令={month_branch}（主轴{axis}）、日主={day_stem}，"
                  f"局中{axis}共{counts.get(axis, 0)}见。"
                  + (f"原文例「如金日干，则为土厚埋金」类此：{axis}重则"
                     f"{BING_RULES_BY_KE[axis][0]}，俱喜{yao_elem}为医药，以去其病也。"
                     if axis in BING_RULES_BY_KE else "")),
    }
    consumed: list[dict] = []
    medicines: list[dict] = []
    if yao_elem and yao_elem in counts:
        medicines.append({"药": yao_elem, "味数": counts[yao_elem],
                           "note": f"以{yao_elem}克{axis}去其病"})
    gods = {g["god"] for g in _god_detail(chart_json)}
    for name, bing_gods, bing_note, yao_gods, yao_note, god_prov in BING_RULES_BY_GOD:
        if not (gods & set(bing_gods)):
            continue
        hit_yao = sorted(gods & set(yao_gods))
        consumed.append({"病": name, "所病": bing_note, "provenance": god_prov,
                         "药在局中": bool(hit_yao), "所见之药": hit_yao})
        if hit_yao:
            medicines.append({"药": name, "药神": hit_yao, "note": yao_note})
    return {
        "thesis": _BING["thesis"],
        "axis_element": axis,
        "element_counts": counts,
        "bing": bing,
        "consumed_by_bing": consumed,
        "medicines": medicines,
        "has_medicine": bool(medicines),
        "provenance": {
            "五行层": bing_prov,
            "十神层": sorted({c["provenance"] for c in consumed}) or [],
            "口径": ("source_backed_exact＝原文逐字可回指；"
                     "source_informed_generalization＝依原文通例结构推得、书源未逐字列该句。"
                     "generalization 项只作通则回归，不冒充逐字对齐。"),
        },
        "note": ("病药为《神峰通考》正说第一家紧要；此处只标病、药及其在否，"
                 "不批吉凶——有病方为贵是原文命题，落到具体命造须人工复核（铁律三）。"
                 "命例级分歧见跨书源取证集 bingyao_cross_source.json（_verdict_summary 与 open 两键）："
                 "书源命例取病取药落在藏干与具体字，"
                 "与本实现层级不同，故该两例不计对齐分。"),
        "basis": f"{_BING['所本']}：「{_BING['thesis']}」{_BING['note']}",
    }
