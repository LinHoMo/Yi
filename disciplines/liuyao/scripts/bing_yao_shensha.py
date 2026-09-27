# -*- coding: utf-8 -*-
"""用神病药与盘面星煞 —— 机械结构化，无吉凶成段断语（AGENTS 铁律一）。

病药（《增删卜易》通行口径，子平/六爻皆用「有病有药」思路）：
  病：休囚死、旬空、月破、受日月克、伏藏受压、入墓
  药：原神动来生、日月生扶、冲空填实、冲开墓库、飞神受制出伏
星煞：安星自 core.ming_tables，是否临爻由本模块比对后挂到爻位。
"""
from __future__ import annotations

import sys
from pathlib import Path

_CORE = Path(__file__).resolve().parents[3] / "core"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

from yishu_core.ming_tables import shensha_at_branches  # noqa: E402
from yishu_core.symbols import BRANCH_ELEMENTS  # noqa: E402
from pathlib import Path as _P
import json as _json
_VT = _P(__file__).resolve().parents[1] / 'data' / 'rules' / 'verdict_texts.json'
BING_YAO_LABELS = _json.loads(_VT.read_text(encoding='utf-8')).get('bing_yao_labels', {})


_WEAK_LEVELS = {"极弱", "弱", "偏弱", "休囚", "囚", "死"}
_STRONG_LEVELS = {"旺", "极旺"}


def evaluate_bing_yao(step2: dict, step3: dict, step5: dict | None = None) -> dict:
    """从 step2/step3 汇总用神「病」与「药」。

    返回 {illness: [{code, label, basis}], medicine: [...], has_illness: bool, has_medicine: bool}
    """
    illness: list[dict] = []
    medicine: list[dict] = []

    level = str((step3 or {}).get("strength_level") or "")
    is_empty = bool((step3 or {}).get("is_empty"))
    is_month_break = bool((step3 or {}).get("is_month_break"))
    has_fu = bool((step2 or {}).get("has_fu_cang"))
    yuan = (step2 or {}).get("yuan_shen") or {}
    yuan_pos = yuan.get("positions") or []
    yuan_moving = any(isinstance(p, dict) and p.get("is_moving") for p in yuan_pos)

    ug_branch = str((step3 or {}).get("use_god_branch") or "")
    ug_element = str((step3 or {}).get("use_god_element") or "")
    month_el = str((step3 or {}).get("month_element") or "")
    day_el = str((step3 or {}).get("day_element") or "")

    def _rel(env_el: str) -> str:
        if not ug_element or not env_el:
            return ""
        if env_el == ug_element:
            return "比和"
        # 生我/克我/我生/我克 —— 用五行生克简表
        cycle = ["木", "火", "土", "金", "水"]
        try:
            i, j = cycle.index(ug_element), cycle.index(env_el)
        except ValueError:
            return ""
        if (i + 1) % 5 == j:
            return "我生"
        if (j + 1) % 5 == i:
            return "生我"
        if (i + 2) % 5 == j:
            return "我克"
        if (j + 2) % 5 == i:
            return "克我"
        return "比和"

    if level in _WEAK_LEVELS:
        illness.append({"code": "weak", "label": BING_YAO_LABELS["weak"]["label"], "basis": BING_YAO_LABELS["weak"]["basis"].format(level=level)})
    if is_empty:
        illness.append({"code": "void", "label": BING_YAO_LABELS["void"]["label"], "basis": BING_YAO_LABELS["void"]["basis"]})
    if is_month_break:
        illness.append({"code": "month_break", "label": BING_YAO_LABELS["month_break"]["label"], "basis": BING_YAO_LABELS["month_break"]["basis"]})
    if has_fu:
        illness.append({"code": "hidden", "label": BING_YAO_LABELS["hidden"]["label"], "basis": BING_YAO_LABELS["hidden"]["basis"]})
    if _rel(month_el) == "克我" or _rel(day_el) == "克我":
        illness.append({"code": "controlled", "label": BING_YAO_LABELS["controlled"]["label"], "basis": BING_YAO_LABELS["controlled"]["basis"].format(month_el=month_el, day_el=day_el)})

    if level in _STRONG_LEVELS:
        medicine.append({"code": "strong_root", "label": BING_YAO_LABELS["strong_root"]["label"], "basis": BING_YAO_LABELS["strong_root"]["basis"].format(level=level)})
    if _rel(month_el) == "生我" or _rel(day_el) == "生我":
        medicine.append({"code": "day_month_sheng", "label": BING_YAO_LABELS["day_month_sheng"]["label"], "basis": BING_YAO_LABELS["day_month_sheng"]["basis"].format(month_el=month_el, day_el=day_el)})
    if yuan_moving:
        medicine.append({"code": "yuan_moving", "label": BING_YAO_LABELS["yuan_moving"]["label"], "basis": BING_YAO_LABELS["yuan_moving"]["basis"]})
    elif yuan_pos:
        medicine.append({"code": "yuan_present", "label": BING_YAO_LABELS["yuan_present"]["label"], "basis": BING_YAO_LABELS["yuan_present"]["basis"]})
    if is_empty and ug_branch:
        medicine.append({"code": "fill_void", "label": BING_YAO_LABELS["fill_void"]["label"], "basis": BING_YAO_LABELS["fill_void"]["basis"].format(ug_branch=ug_branch)})
    if has_fu:
        medicine.append({"code": "out_of_hiding", "label": BING_YAO_LABELS["out_of_hiding"]["label"], "basis": BING_YAO_LABELS["out_of_hiding"]["basis"]})
    if is_month_break and ug_branch:
        medicine.append({"code": "heal_break", "label": BING_YAO_LABELS["heal_break"]["label"], "basis": BING_YAO_LABELS["heal_break"]["basis"]})

    return {
        "illness": illness,
        "medicine": medicine,
        "has_illness": bool(illness),
        "has_medicine": bool(medicine),
        "illness_codes": [x["code"] for x in illness],
        "medicine_codes": [x["code"] for x in medicine],
        "basis": "《增删卜易》有病取药；本模块只做结构化识别，吉凶仍由 step5 综合",
    }


def attach_shensha(chart_result: dict, step3: dict | None = None) -> dict:
    """把常见神煞挂到卦中爻位/日月。纯安星，无吉凶措辞。"""
    dt = (chart_result or {}).get("divination_time") or {}
    day_stem = str(dt.get("day_stem") or "")
    day_branch = str(dt.get("day_branch") or "")
    year_stem = str(dt.get("year_stem") or "")
    year_branch = str(dt.get("year_branch") or "")
    # chart 输出为合写干支（如「癸卯」）
    if not day_stem and dt.get("day_stem_branch"):
        pair = str(dt["day_stem_branch"])
        day_stem, day_branch = pair[0], pair[1:]
    if not year_stem and dt.get("year_stem_branch"):
        pair = str(dt["year_stem_branch"])
        year_stem, year_branch = pair[0], pair[1:]
    if len(day_stem) == 2:
        day_branch = day_stem[1:]
        day_stem = day_stem[0]
    if len(year_stem) == 2:
        year_branch = year_stem[1:]
        year_stem = year_stem[0]
    if not day_stem and not day_branch:
        return {"shensha": [], "shensha_note": "缺日柱，未安星",
            "shensha_policy": "旁参不进主分（《卜筮正宗》辟星煞之谬；《增删卜易》删星煞）"}

    stars = shensha_at_branches(day_stem, day_branch, year_stem or None, year_branch or None)
    oh = (chart_result or {}).get("original_hexagram") or {}
    lines = oh.get("yao_lines") or []
    branch_to_lines: dict[str, list[str]] = {}
    for ln in lines:
        b = str(ln.get("earthly_branch") or "")
        if b:
            branch_to_lines.setdefault(b, []).append(str(ln.get("name") or ln.get("position") or ""))

    hit: list[dict] = []
    for s in stars:
        targets = s.get("target_branches") or []
        on_lines = []
        for b in targets:
            on_lines.extend(branch_to_lines.get(b, []))
        hit.append({
            "name": s["name"],
            "target_branches": targets,
            "basis": s.get("basis", ""),
            "on_lines": on_lines,
            "on_day": day_branch in targets,
        })
    return {
        "shensha": hit,
        "day_stem": day_stem,
        "day_branch": day_branch,
        "basis": "core.yishu_core.ming_tables 安星；是否吉凶由 narrate 按语境表述，不在此断",
    }
