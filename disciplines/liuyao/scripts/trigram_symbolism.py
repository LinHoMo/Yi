#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
八卦万物类象数字化解读系统 (Trigram Symbolism Digital Interpretation)
=============================================================
基于易经八卦万物类象体系，提供上下卦组合象数解读。

核心思想：
- 上卦主外、主动、主空间（天/表/远）
- 下卦主内、主静、主地/里/近
- 体用关系：下卦为"体"（本体），上卦为"用"（作用）
- 象数复合：将两卦的象征意义叠加，产生更丰富的解读

参考经典：《周易·说卦传》《黄金策》《卜筮正宗》
"""
# =============================================================================
# 数据加载（AGENTS.md §三：断语/象征文案进 data/*.json，代码只留算法）
#
# 下面三张表原先内嵌在本文件共约 230 行，是纯文案例项，不属于算法，已整体外提：
#   trigram_symbolism —— 八卦万物类象（自然/五行/方位/身体/六亲/象征物/性情…）
#   trigram_directions —— 八卦方位
#   hexagram_names    —— 六十四卦复合卦名，键为 "上卦/下卦"
# =============================================================================
import json
from pathlib import Path

_TRIGRAM_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "trigram_symbolism.json"


def _load_trigram_data() -> dict:
    try:
        return json.loads(_TRIGRAM_DATA_PATH.read_text(encoding="utf-8"))
    except OSError:
        return {}


_TRIGRAM_DATA = _load_trigram_data()

TRIGRAM_SYMBOLISM = _TRIGRAM_DATA.get("trigram_symbolism") or {}

TRIGRAM_DIRECTIONS = _TRIGRAM_DATA.get("trigram_directions") or {}

# 复合卦名：JSON 无法表达 tuple 键，故序列化为 "上卦/下卦"；此处还原成 tuple，
# 使下游 HEXAGRAM_NAMES.get((上, 下)) 的调用方式与外提前完全一致（零行为漂移）。
HEXAGRAM_NAMES = {
    tuple(_k.split("/")): _v for _k, _v in (_TRIGRAM_DATA.get("hexagram_names") or {}).items()
}



# =============================================================================
# 八卦五行生克关系（用于象数推演）
# =============================================================================

ELEMENT_ORDER = ["木", "火", "土", "金", "水"]  # 相生序

def _element_relation(elem_a: str, elem_b: str) -> str:
    """返回 elem_a 对 elem_b 的五行关系"""
    if elem_a == elem_b:
        return "比和"
    # 相生：木→火→土→金→水→木
    sheng_map = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    if sheng_map.get(elem_a) == elem_b:
        return "生"  # a生b
    if sheng_map.get(elem_b) == elem_a:
        return "被生"  # a被b生
    # 相克：木→土→水→火→金→木
    ke_map = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
    if ke_map.get(elem_a) == elem_b:
        return "克"  # a克b
    if ke_map.get(elem_b) == elem_a:
        return "被克"  # a被b克
    return "未知"

# =============================================================================
# 核心函数
# =============================================================================

def interpret_trigram_combination(upper: str, lower: str, category: str = "general") -> dict:
    """
    卜象复合解读：上下卦组合象数。

    上卦主外/主动，下卦主内/主静。体用中下卦为"体卦"（不变），
    上卦为"用卦"（动）。象数复合即取两卦象征意义叠加。

    Parameters
    ----------
    upper : str
        上卦名（八卦之一：乾/坤/震/巽/坎/离/艮/兑）
    lower : str
        下卦名
    category : str
        解读类别：
        - "general"：通用解读
        - "career"：事业求谋
        - "health"：疾病健康
        - "relationship"：人际婚姻
        - "travel"：出行行旅
        - "loss"：失物寻找

    Returns
    -------
    dict
        包含完整象数解读的字典。
    """
    u = TRIGRAM_SYMBOLISM.get(upper, {})
    l = TRIGRAM_SYMBOLISM.get(lower, {})

    if not u or not l:
        return {"error": f"未知卦象: upper={upper}, lower={lower}"}

    # ── 基本象数复合 ──
    # 上卦主外/主动，下卦主内/主静
    nature_compound = f"{u.get('nature', '?')}在上，{l.get('nature', '?')}在下"
    element_upper = u.get("element", "?")
    element_lower = l.get("element", "?")
    element_relation = _element_relation(element_upper, element_lower)

    symbolism = {
        "nature": nature_compound,
        "symbol_meaning": (
            f"{upper}为{u.get('nature', '')}，"
            f"{lower}为{l.get('nature', '')}"
        ),
        "compound_name": _compound_name(upper, lower),
        "outer_trigram": upper,
        "inner_trigram": lower,
        "outer_nature": u.get("nature", ""),
        "inner_nature": l.get("nature", ""),
        "outer_element": element_upper,
        "inner_element": element_lower,
        "element_relation": element_relation,
        "outer_meaning": u.get("trait", ""),
        "inner_meaning": l.get("trait", ""),
        "outer_personality": u.get("personality", ""),
        "inner_personality": l.get("personality", ""),
        "outer_symbols": u.get("symbols", []),
        "inner_symbols": l.get("symbols", []),
        "outer_direction": u.get("direction", ""),
        "inner_direction": l.get("direction", ""),
        "outer_weather": u.get("weather", ""),
        "inner_weather": l.get("weather", ""),
    }

    # ── 体用五行关系推演 ──
    symbolism["body_use"] = _body_use_analysis(upper, lower, element_upper, element_lower, element_relation)

    # ── 类别特定解读 ──
    if category == "career":
        symbolism["career"] = (
            f"外显{u.get('career', '')}之象，"
            f"内有{l.get('career', '')}之质"
        )
        career_advice = _career_advice(element_relation)
        symbolism["advice"] = f"事业求谋：{career_advice}"

    elif category == "health":
        symbolism["upper_organ_risk"] = u.get("illness", "")
        symbolism["lower_organ_risk"] = l.get("illness", "")
        symbolism["organ_risk"] = (
            f"上卦{u.get('nature', '')}主{u.get('illness', '')}；"
            f"下卦{l.get('nature', '')}主{l.get('illness', '')}"
        )
        health_advice = _health_advice(element_relation, element_upper, element_lower)
        symbolism["health_advice"] = health_advice

    elif category == "relationship":
        symbolism["dynamic"] = (
            f"外相{u.get('personality', '')}，"
            f"内具{l.get('personality', '')}"
        )
        relationship_dynamic = _relationship_dynamic(upper, lower, element_relation)
        symbolism["relationship_dynamic"] = relationship_dynamic

    elif category == "travel":
        favorable = trigram_to_favorable_direction(upper)
        symbolism["direction_suggestion"] = f"利往{favorable}方"
        symbolism["favorable_direction"] = favorable
        travel_advice = _travel_advice(lower)
        symbolism["travel_advice"] = travel_advice

    elif category == "loss":
        symbolism["search_direction"] = (
            f"上卦{upper}方（{trigram_to_favorable_direction(upper)}）"
            f"或下卦{lower}方（{trigram_to_favorable_direction(lower)}）"
        )
        symbolism["search_hint"] = f"寻{l.get('nature', '')}类之所"

    elif category == "general":
        symbolism["overview"] = _general_overview(upper, lower, u, l, element_relation)

    return symbolism

def build_trigram_interpretation(result: dict, category: str = "general") -> dict:
    """
    从 build_hexagram_result 的输出中提取上下卦信息并生成卜象解读。

    Parameters
    ----------
    result : dict
        build_hexagram_result() 返回的字典。
    category : str
        解读类别。

    Returns
    -------
    dict
        卜象解读结果。
    """
    hex_info = result.get("original_hexagram", {})
    upper = hex_info.get("upper_trigram", "")
    lower = hex_info.get("lower_trigram", "")

    if not upper or not lower:
        return {"error": "hexagram result missing trigram info"}

    return interpret_trigram_combination(upper, lower, category)

def trigram_to_favorable_direction(trigram: str) -> str:
    """
    八卦先天方位——返回对应方位。

    Parameters
    ----------
    trigram : str
        八卦名

    Returns
    -------
    str
        方位字符串
    """
    return TRIGRAM_DIRECTIONS.get(trigram, "中")

def get_trigram_info(trigram: str) -> dict:
    """
    获取单个卦的完整类象信息。

    Parameters
    ----------
    trigram : str
        八卦名

    Returns
    -------
    dict
        该卦的全部类象数据
    """
    return TRIGRAM_SYMBOLISM.get(trigram, {}).copy()

def format_trigram_interpretation_text(interp: dict) -> str:
    """
    将卜象解读结果格式化为可读的中文文本。

    Parameters
    ----------
    interp : dict
        interpret_trigram_combination() 返回的字典。

    Returns
    -------
    str
        格式化文本
    """
    lines = []

    nature = interp.get("nature", "")
    compound = interp.get("compound_name", "")
    lines.append(f"　　【卦象】{nature}（{compound}）")

    symbol = interp.get("symbol_meaning", "")
    if symbol:
        lines.append(f"　　【象意】{symbol}")

    outer_elem = interp.get("outer_element", "")
    inner_elem = interp.get("inner_element", "")
    relation = interp.get("element_relation", "")
    lines.append(f"　　【体用】上{outer_elem}下{inner_elem}，{outer_elem}对{inner_elem}为{relation}")

    body_use = interp.get("body_use", "")
    if body_use:
        lines.append(f"　　【生克】{body_use}")

    # 类别特定内容
    if interp.get("career"):
        lines.append(f"　　【事业】{interp['career']}")
    if interp.get("advice"):
        lines.append(f"　　【建议】{interp['advice']}")

    if interp.get("organ_risk"):
        lines.append(f"　　【健康】{interp['organ_risk']}")
    if interp.get("health_advice"):
        lines.append(f"　　【医理】{interp['health_advice']}")

    if interp.get("dynamic"):
        lines.append(f"　　【人际】{interp['dynamic']}")
    if interp.get("relationship_dynamic"):
        lines.append(f"　　【关系】{interp['relationship_dynamic']}")

    if interp.get("direction_suggestion"):
        lines.append(f"　　【出行】{interp['direction_suggestion']}")
    if interp.get("travel_advice"):
        lines.append(f"　　【行象】{interp['travel_advice']}")

    if interp.get("search_direction"):
        lines.append(f"　　【寻向】{interp['search_direction']}")
    if interp.get("search_hint"):
        lines.append(f"　　【寻物】{interp['search_hint']}")

    if interp.get("overview"):
        lines.append(f"　　【总论】{interp['overview']}")

    # 方位与气象
    od = interp.get("outer_direction", "")
    id_ = interp.get("inner_direction", "")
    ow = interp.get("outer_weather", "")
    iw = interp.get("inner_weather", "")
    if od or id_:
        lines.append(f"　　【方位】上卦{od}，下卦{id_}")
    if ow or iw:
        lines.append(f"　　【气象】上{ow}，下{iw}")

    return "\n".join(lines)

# =============================================================================
# 辅助函数（内部使用）
# =============================================================================

# 六十四卦名复合表（上卦+下卦 → 卦名）

def _compound_name(upper: str, lower: str) -> str:
    """获取六十四卦名"""
    return HEXAGRAM_NAMES.get((upper, lower), f"{upper}上{lower}下")

def _body_use_analysis(upper: str, lower: str, elem_u: str, elem_l: str, relation: str) -> str:
    """
    体用五行分析。
    下卦为体（本体/求测人），上卦为用（外部环境/所求之事）。
    """
    body = f"下卦{lower}({elem_l})为体，上卦{upper}({elem_u})为用"

    if relation == "生":
        return f"{body}；用生体——事顺易成，外力相助之象"
    elif relation == "被生":
        return f"{body}；体生用——耗费心力，我求于外"
    elif relation == "克":
        return f"{body}；用克体——外力压制，事多阻碍"
    elif relation == "被克":
        return f"{body}；体克用——我为主动，需费力争取"
    elif relation == "比和":
        return f"{body}；体用比和——内外谐顺，事多圆满"
    else:
        return f"{body}；体用关系待察"

def _career_advice(element_relation: str) -> str:
    """根据体用关系给事业建议"""
    if element_relation in ("生", "比和"):
        return "顺势而为，可积极进取"
    elif element_relation == "被生":
        return "需付出心力，终有成就"
    elif element_relation in ("克",):
        return "阻力较大，宜守不宜攻"
    elif element_relation == "被克":
        return "需努力争取，不可松懈"
    return "观察形势，待时而动"

def _health_advice(relation: str, elem_u: str, elem_l: str) -> str:
    """根据体用关系给健康分析"""
    if relation == "克":
        return f"用克体不利健康——{elem_u}克{elem_l}，病情有进展之象，宜早治"
    elif relation == "被克":
        return f"体克用——{elem_l}克{elem_u}，抗病有力，但耗费体力"
    elif relation == "生":
        return f"用生体——{elem_u}生{elem_l}，正虚得补，恢复有望"
    elif relation == "被生":
        return f"体生用——{elem_l}生{elem_u}，元气消耗，需养精蓄锐"
    elif relation == "比和":
        return f"体用比和——{elem_l}平调，病情稳定"
    return "平和观察，详查脉证"

def _relationship_dynamic(upper: str, lower: str, relation: str) -> str:
    """人际关系与婚姻分析"""
    u_info = TRIGRAM_SYMBOLISM.get(upper, {})
    l_info = TRIGRAM_SYMBOLISM.get(lower, {})
    u_fam = u_info.get("family", "")
    l_fam = l_info.get("family", "")

    family_map = f"上卦{u_fam}外，下卦{l_fam}内"

    if relation == "比和":
        return f"{family_map}；两气相投，和睦之美——交涉顺利，感情融洽"
    elif relation == "生":
        return f"{family_map}；外助内生——对方主动付出，关系中有施予之象"
    elif relation == "被生":
        return f"{family_map}；内助外生——付出为主，我主动迎合"
    elif relation == "克":
        return f"{family_map}；外克于内——对方强势或条件不利，需在压力中调整"
    elif relation == "被克":
        return f"{family_map}；内克于外——主动权在我，但恐过于主导"

    return f"{family_map}；两象相参，局势微妙"

def _travel_advice(lower: str) -> str:
    """出行分析"""
    info = TRIGRAM_SYMBOLISM.get(lower, {})
    body = info.get("body", "")
    direction = info.get("direction", "")
    trait = info.get("trait", "")

    if "刚健" in trait or "动" in trait:
        return f"下卦{trait}——利于速行，方向宜{direction}方"
    elif "柔顺" in trait or "止" in trait or "静" in trait:
        return f"下卦{trait}——宜缓行，稳扎稳打"
    elif "险" in trait or "陷" in trait:
        return f"下卦{trait}——出行有险，须防不测"
    return f"下卦类象{body}——出行宜备周全"

def _general_overview(upper: str, lower: str, u: dict, l: dict, relation: str) -> str:
    """通用总论"""
    u_nature = u.get("nature", "")
    l_nature = u.get("nature", "") if upper == lower else l.get("nature", "")

    if upper == lower:
        return (
            f"八纯卦——上下皆{upper}（{u.get('nature','')}），"
            f"纯{u.get('element','')}之象。{u.get('trait','')}"
            f"占事专一，力量集中而不杂。"
        )

    body_use_judgment = ""
    if relation in ("生", "比和"):
        body_use_judgment = "体用相生比和，事多顺遂"
    elif relation == "克":
        body_use_judgment = "用克体外力压制，须谨慎"
    elif relation == "被克":
        body_use_judgment = "体克用虽主动，然耗费心力"
    elif relation == "被生":
        body_use_judgment = "体生用有所付出，待时收功"

    u_nature_val = u.get("nature", "")
    u_trait_val = u.get("trait", "")
    l_nature_val = l.get("nature", "")
    l_trait_val = l.get("trait", "")

    return (
        f"上{u_nature}下{l_nature}"
        + f"——外显{u_nature_val}{u_trait_val}之象，"
        + f"内蕴{l_nature_val}{l_trait_val}之质。"
        + f"{body_use_judgment}。"
    )

# =============================================================================
# CLI 快速测试
# =============================================================================

if __name__ == "__main__":
    import argparse

    trigrams = list(TRIGRAM_SYMBOLISM.keys())
    ap = argparse.ArgumentParser(description="八卦象意组合解读（机械查表）")
    ap.add_argument("upper", nargs="?", help="上卦名")
    ap.add_argument("lower", nargs="?", help="下卦名")
    ap.add_argument("category", nargs="?", default="general",
                    choices=("general", "career", "health", "relationship", "travel", "loss"),
                    help="事类")
    ap.add_argument("--list", action="store_true", help="列出可用卦名与类别")
    args = ap.parse_args()

    if args.list or not args.upper or not args.lower:
        print("可用卦:", ", ".join(trigrams))
        print("类别: general, career, health, relationship, travel, loss")
        if not args.list:
            print()
            print("── 演示：乾上坤下(天地否) ──")
            print(format_trigram_interpretation_text(
                interpret_trigram_combination("乾", "坤", args.category)))
            print()
            print("── 演示：坤上乾下(地天泰) ──")
            print(format_trigram_interpretation_text(
                interpret_trigram_combination("坤", "乾", args.category)))
        raise SystemExit(0)

    if args.upper not in trigrams or args.lower not in trigrams:
        print(f"错误: 卦名无效。可用: {', '.join(trigrams)}")
        raise SystemExit(1)
    result = interpret_trigram_combination(args.upper, args.lower, args.category)
    print(format_trigram_interpretation_text(result))
