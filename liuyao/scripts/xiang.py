#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""象层：卦爻象素材的唯一装配点（category/ti_yong/guaci/yaoci/hu_gua/spirit/fangwei/class_image）。

三条纪律（CONTRACT §五-bis）：只呈现素材不做吉凶判定；每个象目带 `basis`；
规则表缺失即抛错，绝不塞空壳冒充覆盖。素材外置在 data/rules/domain/xiang_layer.json。
"""
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import json  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kernel_path import ensure_kernel_on_path, repo_root  # noqa: E402

ensure_kernel_on_path(__file__)

from chart_tables import BAGUA, SIX_SPIRIT_PROPERTIES  # noqa: E402
from trigram_symbolism import (  # noqa: E402
    HEXAGRAM_NAMES,
    TRIGRAM_DIRECTIONS,
    TRIGRAM_SYMBOLISM,
    interpret_trigram_combination,
)

_XIANG_RULES_PATH = repo_root(__file__) / "data" / "rules" / "domain" / "xiang_layer.json"

_VALID_CATEGORIES = ("general", "career", "health", "relationship", "travel", "loss")


def _load_rules() -> dict:
    data = json.loads(_XIANG_RULES_PATH.read_text(encoding="utf-8"))
    missing = [k for k in ("basis", "category_by_class", "render")
               if not isinstance(data.get(k), dict) or not data[k]]
    if missing:
        raise RuntimeError(f"{_XIANG_RULES_PATH.name} 缺表或表为空：{', '.join(missing)}")
    return data


_RULES = _load_rules()
_BASIS = _RULES["basis"]
_CATEGORY_BY_CLASS = _RULES["category_by_class"]
_CATEGORY_KEYWORDS = _RULES.get("category_fallback_keywords") or {}
_RENDER = _RULES["render"]


# =============================================================================
# 一、事类 → 象类别
# =============================================================================

def resolve_xiang_category(question_class: str = "", question: str = "") -> str:
    """把 step2 的 `question_class` 映射到象类别。

    映射表在 data/rules/xiang_layer.json#category_by_class；题类缺失或判为
    『其他』时，退到问句关键词直判（同源同口径，同为**现代问法启发式**，
    不冒充古籍定式）。都不中落 general。
    """
    qc = (question_class or "").strip()
    mapped = _CATEGORY_BY_CLASS.get(qc)
    if mapped in _VALID_CATEGORIES:
        return mapped
    text = question or ""
    for cat in ("career", "health", "relationship", "travel", "loss"):
        for kw in _CATEGORY_KEYWORDS.get(cat) or []:
            if kw and kw in text:
                return cat
    return "general"


# =============================================================================
# 二、互体（京房：二三四爻为下互，三四五爻为上互）
# =============================================================================

def _is_yang(yao: dict) -> int:
    """爻阴阳 → 1/0。仅认盘面已定的 nature 字面（yang/阳），其余一律作阴。"""
    n = str((yao or {}).get("nature", "")).strip()
    return 1 if n in ("yang", "阳", "老阳", "少阳", "9", "7") else 0


def _lines_to_trigram(lines: list) -> str:
    """三爻阴阳序列（自下而上）→ 卦名。"""
    for name, info in BAGUA.items():
        if list(info.get("lines") or []) == list(lines):
            return name
    return ""


def build_hu_gua(yao_lines: list) -> dict:
    """互体：下互取二三四爻，上互取三四五爻。

    不足五爻（盘面不全）时返回 {}——不猜、不补。
    """
    if not isinstance(yao_lines, list) or len(yao_lines) < 5:
        return {}
    lower = _lines_to_trigram([_is_yang(yao_lines[i]) for i in (1, 2, 3)])
    upper = _lines_to_trigram([_is_yang(yao_lines[i]) for i in (2, 3, 4)])
    if not lower or not upper:
        return {}
    return {
        "lower_trigram": lower,
        "upper_trigram": upper,
        "name": HEXAGRAM_NAMES.get((upper, lower), f"{upper}上{lower}下"),
        "lower_element": (BAGUA.get(lower) or {}).get("element", ""),
        "upper_element": (BAGUA.get(upper) or {}).get("element", ""),
        "lower_nature": (TRIGRAM_SYMBOLISM.get(lower) or {}).get("nature", ""),
        "upper_nature": (TRIGRAM_SYMBOLISM.get(upper) or {}).get("nature", ""),
        "basis": _BASIS.get("hu_gua", ""),
    }


# =============================================================================
# 三、卦辞 / 爻辞
# =============================================================================

def build_guaci(result: dict) -> dict:
    """本卦卦辞 + 变卦卦辞（有变才出）。"""
    oh = result.get("original_hexagram") or {}
    ch = result.get("changed_hexagram") or {}
    out = {
        "ben": {"name": oh.get("name", ""), "judgment": oh.get("judgment", "")},
        "basis": _BASIS.get("texts", ""),
    }
    if ch.get("name"):
        out["bian"] = {"name": ch.get("name", ""), "judgment": ch.get("judgment", "")}
    return out


def build_yaoci(result: dict) -> dict:
    """动爻爻辞，并附世爻爻辞（世爻是「我」这一爻，不看象是断不清的）。"""
    lines = (result.get("original_hexagram") or {}).get("yao_lines") or []
    items = []
    for y in lines or []:
        if not isinstance(y, dict):
            continue
        if not (y.get("is_moving") or y.get("is_world")):
            continue
        items.append({
            "position": y.get("position"),
            "name": y.get("name", ""),
            "line_text": y.get("line_text", ""),
            "six_spirit": y.get("six_spirit", ""),
            "six_relation": y.get("six_relation", ""),
            "is_moving": bool(y.get("is_moving")),
            "is_world": bool(y.get("is_world")),
        })
    return {"lines": items, "moving_count": sum(1 for i in items if i["is_moving"]),
            "basis": _BASIS.get("texts", "")}


# =============================================================================
# 四、六神象义
# =============================================================================

def _spirit_image(yao: dict) -> dict:
    """单爻六神象义（属性表唯一真值源 classical_patterns_data.json）。"""
    sp = (yao or {}).get("six_spirit", "")
    prop = SIX_SPIRIT_PROPERTIES.get(sp) or {}
    if not prop:
        return {}
    return {
        "spirit": sp,
        "position": (yao or {}).get("position"),
        "six_relation": (yao or {}).get("six_relation", ""),
        "nature": prop.get("nature", ""),
        "element": prop.get("element", ""),
        "direction": prop.get("direction", ""),
        "virtue": prop.get("virtue", ""),
        "caution": prop.get("caution", ""),
    }


def build_spirit(result: dict, chain: dict) -> dict:
    """世/应/用神/动爻四处的六神象义。

    取象位置是**取象惯例**（世为我、应为彼、用神为所问、动爻为机），
    不是吉凶判定——caution 一栏照抄古籍属性表，不因临何爻而改口。
    """
    lines = (result.get("original_hexagram") or {}).get("yao_lines") or []
    if not lines:
        return {}
    step2 = (chain or {}).get("step2_use_god_identification") or {}
    ug_cat = step2.get("use_god_category") or ""
    # use_god_positions 是爻位对象列表（[{position,name,...}]），不是裸整数位号
    ug_pos = {p.get("position") for p in (step2.get("use_god_positions") or [])
              if isinstance(p, dict) and p.get("position") is not None}

    out = {}
    for y in lines:
        if not isinstance(y, dict):
            continue
        if y.get("is_world"):
            out.setdefault("shi", _spirit_image(y))
        if y.get("is_response"):
            out.setdefault("ying", _spirit_image(y))
        # 用神取世爻时（step2 兜底口径），六亲名对不上任何爻，改认世爻位
        if ug_cat == "世爻":
            _is_ug = bool(y.get("is_world"))
        else:
            _is_ug = bool(ug_cat) and y.get("six_relation") == ug_cat and (
                not ug_pos or y.get("position") in ug_pos)
        if _is_ug:
            out.setdefault("use_god", _spirit_image(y))
    moving = [ _spirit_image(y) for y in lines
               if isinstance(y, dict) and y.get("is_moving") ]
    if moving:
        out["moving"] = [m for m in moving if m]
    if not out:
        return {}
    out["basis"] = _BASIS.get("spirit", "")
    return out


# =============================================================================
# 五、体用 / 方位
# =============================================================================

def build_ti_yong(result: dict, interp: dict) -> dict:
    """体用与方位：下卦为体（我/内），上卦为用（事/外）。"""
    hex_info = result.get("original_hexagram") or {}
    lower = hex_info.get("lower_trigram", "")
    upper = hex_info.get("upper_trigram", "")
    if not lower or not upper:
        return {}
    return {
        "ti": lower,                       # 体卦
        "yong": upper,                     # 用卦
        "ti_element": (TRIGRAM_SYMBOLISM.get(lower) or {}).get("element", ""),
        "yong_element": (TRIGRAM_SYMBOLISM.get(upper) or {}).get("element", ""),
        "element_relation": (interp or {}).get("element_relation", ""),
        "body_use": (interp or {}).get("body_use", ""),
        "basis": _BASIS.get("trigram", ""),
    }


def build_fangwei(result: dict) -> dict:
    """方位：体卦方位（我方/近处）+ 用卦方位（彼方/远处）。"""
    hex_info = result.get("original_hexagram") or {}
    lower = hex_info.get("lower_trigram", "")
    upper = hex_info.get("upper_trigram", "")
    if not lower or not upper:
        return {}
    return {
        "ti_direction": TRIGRAM_DIRECTIONS.get(lower, ""),
        "yong_direction": TRIGRAM_DIRECTIONS.get(upper, ""),
        "ti_trigram": lower,
        "yong_trigram": upper,
        "basis": _BASIS.get("fangwei", ""),
    }


# =============================================================================
# 六、装配
# =============================================================================

def build_xiang(result: dict, chain: dict = None, category: str = "") -> dict:
    """象层总装。

    任一分项取不到素材就不写该键（而不是写空串充数）——
    `xiang` 的覆盖度是要被读数器量的，空壳会把读数带偏。
    """
    chain = chain or {}
    step2 = chain.get("step2_use_god_identification") or {}
    if not category:
        category = resolve_xiang_category(
            step2.get("question_class", ""), result.get("question", ""))

    xiang = {"category": category}

    try:
        interp = interpret_trigram_combination(
            (result.get("original_hexagram") or {}).get("upper_trigram", ""),
            (result.get("original_hexagram") or {}).get("lower_trigram", ""),
            category,
        )
    except Exception:
        interp = {}
    if interp and "error" not in interp:
        # 题类专属类象：只取该类别真正产出的子项，避免 general 键混入
        for key in ("career", "advice", "organ_risk", "health_advice",
                    "dynamic", "relationship_dynamic", "direction_suggestion",
                    "favorable_direction", "travel_advice", "search_direction",
                    "search_hint", "overview"):
            if interp.get(key):
                xiang.setdefault("class_image", {})[key] = interp[key]
        xiang["trigram"] = {
            "compound_name": interp.get("compound_name", ""),
            "symbol_meaning": interp.get("symbol_meaning", ""),
            "outer_trigram": interp.get("outer_trigram", ""),
            "inner_trigram": interp.get("inner_trigram", ""),
            "outer_symbols": interp.get("outer_symbols") or [],
            "inner_symbols": interp.get("inner_symbols") or [],
            "nature": interp.get("nature", ""),
            "basis": _BASIS.get("trigram", ""),
        }

    ty = build_ti_yong(result, interp)
    if ty:
        xiang["ti_yong"] = ty

    gc = build_guaci(result)
    if gc.get("ben", {}).get("judgment"):
        xiang["guaci"] = gc

    yc = build_yaoci(result)
    if yc.get("lines"):
        xiang["yaoci"] = yc

    hg = build_hu_gua((result.get("original_hexagram") or {}).get("yao_lines"))
    if hg:
        xiang["hu_gua"] = hg

    sp = build_spirit(result, chain)
    if sp:
        xiang["spirit"] = sp

    fw = build_fangwei(result)
    if fw:
        xiang["fangwei"] = fw

    xiang["basis"] = {
        "question_class": step2.get("question_class", ""),
        "category_source": "data/rules/xiang_layer.json#category_by_class"
        if step2.get("question_class") in _CATEGORY_BY_CLASS
        else "data/rules/xiang_layer.json#category_fallback_keywords（问句直判）",
        "registry": "data/rules/xiang_layer.json#basis",
        "note": "象层不进评分、不参与 verdict（CONTRACT §五-bis）",
    }
    return xiang


# =============================================================================
# 七、正文【象】段（呈现层调用；文案骨架外置 xiang_layer.json#render）
# =============================================================================

def format_xiang_text(xiang: dict) -> str:
    """象层 → 正文一段。只读素材、不下判词；无素材返回空串。"""
    if not xiang:
        return ""
    lead = _RENDER.get("lead") or "**象上看**："
    sep = _RENDER.get("separator") or "；"
    parts = []

    trg = xiang.get("trigram") or {}
    if trg.get("compound_name"):
        parts.append(f"{trg.get('compound_name')}——{trg.get('symbol_meaning', '')}".strip("——"))

    ty = xiang.get("ti_yong") or {}
    if ty.get("body_use"):
        parts.append(ty["body_use"])

    hg = xiang.get("hu_gua") or {}
    if hg.get("name"):
        parts.append(f"互体见{hg['name']}（下{hg.get('lower_trigram','')}上{hg.get('upper_trigram','')}）")

    gc = xiang.get("guaci") or {}
    if gc.get("ben", {}).get("judgment"):
        s = f"卦辞：{gc['ben'].get('name','')}「{gc['ben']['judgment']}」"
        if gc.get("bian", {}).get("judgment"):
            s += f"；之卦{gc['bian'].get('name','')}「{gc['bian']['judgment']}」"
        parts.append(s)

    yc = xiang.get("yaoci") or {}
    yc_txt = []
    for it in (yc.get("lines") or []):
        if not it.get("line_text"):
            continue
        tag = "动" if it.get("is_moving") else ("世" if it.get("is_world") else "")
        yc_txt.append(f"{it.get('name','')}{tag}「{it['line_text']}」")
    if yc_txt:
        parts.append("爻辞：" + sep.join(yc_txt))

    sp = xiang.get("spirit") or {}
    sp_txt = []
    for label, key in (("世", "shi"), ("应", "ying"), ("用神", "use_god")):
        v = sp.get(key) or {}
        if v.get("spirit"):
            sp_txt.append(f"{label}临{v['spirit']}（{v.get('virtue','')}）")
    for m in (sp.get("moving") or []):
        if m.get("spirit"):
            sp_txt.append(f"动爻临{m['spirit']}（{m.get('virtue','')}）")
    if sp_txt:
        parts.append("六神：" + sep.join(sp_txt))

    fw = xiang.get("fangwei") or {}
    if fw.get("ti_direction") or fw.get("yong_direction"):
        parts.append(f"方位：体在{fw.get('ti_direction','')}方，用在{fw.get('yong_direction','')}方")

    ci = xiang.get("class_image") or {}
    for key, label in (("organ_risk", "身体"), ("health_advice", "医理"),
                       ("career", "事业"), ("advice", "谋为"),
                       ("relationship_dynamic", "关系"),
                       ("direction_suggestion", "利方"),
                       ("travel_advice", "行象"),
                       ("search_direction", "寻向"), ("search_hint", "寻物"),
                       ("overview", "总论")):
        if ci.get(key):
            parts.append(f"{label}：{ci[key]}")

    if not parts:
        return ""
    return lead + sep.join(parts)


# =============================================================================
# 自测演示，非 CLI 入口（无 argparse；engine.py 为正式入口）
# =============================================================================

if __name__ == "__main__":
    from chart import chart as _chart
    _q = sys.argv[1] if len(sys.argv) > 1 else "占问事业能否升迁"
    _c = _chart("coin", _q, seed=42)
    _x = build_xiang(_c, {}, resolve_xiang_category("", _q))
    print(json.dumps(_x, ensure_ascii=False, indent=2))
    print()
    print(format_xiang_text(_x))
