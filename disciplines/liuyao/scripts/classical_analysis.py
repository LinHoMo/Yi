# 本文件为聚合入口：子模块见 engine_*/chain_*/classical_*。
import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)



from chart_tables import SIX_SPIRIT_PROPERTIES
from classical_enhancements import (
    analyze_hidden_spirits,
    analyze_hidden_spirit_emergence,
    analyze_hidden_movement,
    analyze_wandering_returning_soul,
    analyze_monthly_break,
    analyze_triple_combo,
    analyze_advance_retreat,
    analyze_twelve_growth,
    analyze_desperate_relief,
    analyze_du_fa_du_jing,
    analyze_clash_harmony,
    analyze_repetition,
    analyze_repetition_deep,
    analyze_hexagram_body,
    analyze_element_strength,
    analyze_three_punishments,
    analyze_day_month_bonding,
    analyze_six_breaks,
    analyze_officer_tomb,
    analyze_transformation_pattern,
    analyze_flying_hidden_interaction,
    spirit_yin_yang_factor,
    analyze_nayin,
)

def enhance_reading(result_dict):
    """
    对 liuyao_engine.py 产出的基础排盘结果进行经典深度分析。
    
    参数:
        result_dict: build_hexagram_result() 返回的字典
        
    返回:
        同一个字典（被原位修改），新增 'advanced_analysis' 键，
        包含 19 个经典分析段：
            - hidden_spirit_analysis:    伏藏分析
            - hidden_movement:           暗动分析
            - soul_hexagram:             游魂归魂卦（Gap 7）
            - monthly_break:             月破分析
            - triple_combo:              三合局分析
            - advance_retreat:           进退神分析
            - twelve_growth:             十二长生分析
            - clash_harmony:             六合六冲卦判断
            - repetition:                反吟伏吟判断
            - element_strength:          纳甲四柱旺衰总结
            - three_punishments:         三刑分析
            - hidden_spirit_scoring:     伏神得出不得出（优化版）
            - day_month_bonding:         日月合用神（Gap 5）
            - six_breaks:                六破系统（Gap 6）
            - desperate_relief:          绝处逢生（Gap 2）
            - transformation_pattern:    八卦变爻深度推演（动爻格局）
            - flying_hidden_interaction: 飞伏神深度互断（飞伏生克）
            - officer_tomb:              随官入墓（Gap 3）
            - nayin:                     六十甲子纳音取象

    用法：
        result = build_hexagram_result(...)
        result = enhance_reading(result)
        # result['advanced_analysis']['hidden_spirit_analysis'] ...

    注意：
        本函数会原位修改输入字典并返回它。如需保留原数据请先 copy。
    """
    if result_dict is None:
        return result_dict

    if not isinstance(result_dict, dict):
        raise TypeError("result_dict 应是由 build_hexagram_result() 返回的字典")

    # 检查必要字段
    if "original_hexagram" not in result_dict:
        raise ValueError("输入缺少 'original_hexagram' 字段")
    if "divination_time" not in result_dict:
        raise ValueError("输入缺少 'divination_time' 字段")

    # 执行各段分析
    result_dict["advanced_analysis"] = {
        "hidden_spirit_analysis": analyze_hidden_spirits(result_dict),
        "hidden_movement": analyze_hidden_movement(result_dict),
        "soul_hexagram": analyze_wandering_returning_soul(result_dict),
        "monthly_break": analyze_monthly_break(result_dict),
        "triple_combo": analyze_triple_combo(result_dict),
        "advance_retreat": analyze_advance_retreat(result_dict),
        "twelve_growth": analyze_twelve_growth(result_dict),
        "clash_harmony": analyze_clash_harmony(result_dict),
        "repetition": analyze_repetition(result_dict),
        "repetition_deep": analyze_repetition_deep(result_dict),
        "hexagram_body": analyze_hexagram_body(result_dict),
        "element_strength": analyze_element_strength(result_dict),
        "three_punishments": analyze_three_punishments(result_dict),
        "hidden_spirit_scoring": analyze_hidden_spirit_emergence(result_dict),
        "day_month_bonding": analyze_day_month_bonding(result_dict),
        "six_breaks": analyze_six_breaks(result_dict),
        "desperate_relief": analyze_desperate_relief(result_dict),
        # 独发/独静（《增删卜易·独发章》）：只标象不进主分，供正文辅助说明
        "du_fa_du_jing": analyze_du_fa_du_jing(result_dict),
    }

    # 八卦变爻深度推演（动爻格局分析）
    result_dict["advanced_analysis"]["transformation_pattern"] = analyze_transformation_pattern(result_dict)

    # 飞伏神深度互断（需要引用伏藏分析的结果）
    result_dict["advanced_analysis"]["flying_hidden_interaction"] = analyze_flying_hidden_interaction(result_dict)

    # 随官入墓分析（需要引用伏藏分析的结果）
    result_dict["advanced_analysis"]["officer_tomb"] = analyze_officer_tomb(result_dict)

    # 六神（六兽）辅助分析——根据各爻六神 + 六亲 + 世应综合研判
    result_dict["advanced_analysis"]["six_spirit_analysis"] = _analyze_six_spirits(result_dict)

    # 纳音系统（六十甲子纳音取象）
    result_dict["advanced_analysis"]["nayin"] = analyze_nayin(result_dict)

    return result_dict


def _analyze_six_spirits(result_dict):
    """
    六神（六兽）辅助分析。

    根据各爻的六神叠加六亲+动静+世应，提供综合研判：
    - 用神/原神之六神：助力性质
    - 忌神/仇神之六神：阻力性质
    - 世应之六神：主体/客体之象
    """
    hex_info = result_dict.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    div_time = result_dict.get("divination_time", {})

    # 提取关键
    world_yao = None
    response_yao = None
    moving_yaos = []
    spirit_summary = []

    for yao in yao_lines:
        pos = yao.get("position")
        spirit = yao.get("six_spirit", "")
        relation = yao.get("six_relation", "")
        moving = yao.get("is_moving", False)
        empty = yao.get("is_empty", False)
        branch = yao.get("earthly_branch", "")
        line_name = yao.get("name", "")
        is_world = yao.get("is_world", False)
        is_response = yao.get("is_response", False)

        props = SIX_SPIRIT_PROPERTIES.get(spirit, {})
        entry = {
            "position": pos,
            "name": line_name,
            "six_spirit": spirit,
            "six_relation": relation,
            "earthly_branch": branch,
            "element": props.get("element", ""),
            "nature": props.get("nature", ""),
            "is_moving": moving,
            "is_empty": empty,
            "is_world": is_world,
            "is_response": is_response,
        }
        spirit_summary.append(entry)

        if is_world:
            world_yao = entry
        if is_response:
            response_yao = entry
        if moving:
            moving_yaos.append(entry)

    # 用神与六神（若能从 question_category / thinking_chain 获取更佳，此处用启发式判断）
    palace_element = hex_info.get("palace_element", "")
    # 六神与宫五行相同（比值）的加分（《黄金策》云："六神生旺则吉，克害则凶"）
    value_aligned = []
    for entry in spirit_summary:
        sp_elem = entry.get("element", "")
        if sp_elem and sp_elem == palace_element:
            value_aligned.append(entry)

    # 综合判断
    comment_parts = []
    if world_yao:
        comment_parts.append(
            f"世爻{world_yao['name']}临{world_yao['six_spirit']}"
            f"（{world_yao['nature']}），"
            f"{'同气于宫，根基尚稳' if world_yao.get('element') == palace_element else '与宫气异，主体有变'}"
        )
    if value_aligned:
        names = "、".join(f"{e['name']}({e['six_spirit']})" for e in value_aligned if not e.get("is_world"))
        if names:
            comment_parts.append(f"值宫五行之六神：{names}——与宫同气")
    if response_yao:
        comment_parts.append(
            f"应爻{response_yao['name']}临{response_yao['six_spirit']}（{response_yao['nature']}）"
        )

    # 动爻六神的特殊意义
    if moving_yaos:
        move_desc = []
        for m in moving_yaos:
            move_desc.append(
                f"{m['name']}{m['six_spirit']}动（{m['nature']}/{m['six_relation']}）"
            )
        comment_parts.append("动爻六神：" + "、".join(move_desc))

    # 六神生克综合（简化）：统计各六神出现频次
    spirit_count = {}
    for entry in spirit_summary:
        sp = entry.get("six_spirit", "")
        spirit_count[sp] = spirit_count.get(sp, 0) + 1

    return {
        "palace_element": palace_element,
        "day_stem": div_time.get("day_stem_branch", "")[:1] if div_time.get("day_stem_branch") else "",
        "lines": spirit_summary,
        "world_yao_spirit": world_yao,
        "response_yao_spirit": response_yao,
        "moving_yao_spirits": moving_yaos,
        "value_aligned_spirits": value_aligned,
        "spirit_count": spirit_count,
        "comment": "；".join(comment_parts) if comment_parts else "六神分布平稳，无特殊格局",
    }


if __name__ == "__main__":
    import json
    from liuyao_engine import build_hexagram_result, coin_toss
    from datetime import datetime

    # 简单测试
    now = datetime.now()
    yao = coin_toss()
    result = build_hexagram_result(
        yao, "测试：模块是否正常运行？", "测试",
        now.year, now.month, now.day, now.hour
    )

    # 应用高级分析
    result = enhance_reading(result)

    adv = result["advanced_analysis"]
    # 打印摘要
    for key in adv:
        section = adv[key]
        if isinstance(section, dict):
            summary = section.get("summary", "无")
            if key == "transformation_pattern":
                patterns = section.get("patterns", [])
                interp = section.get("interpretation", "")
                summary = f"格局：{'、'.join(patterns) if patterns else '无'}；{interp}"
            elif key == "flying_hidden_interaction":
                interactions = section.get("interactions", [])
                if interactions:
                    summary = "；".join(i.get("description", "") for i in interactions)
                else:
                    summary = section.get("summary", "无")
        elif isinstance(section, list):
            summary = f"{len(section)}条记录"
        else:
            summary = str(section)
        print(f"\n【{key}】")
        print(f"  {summary}")

    print("\n完整结果长度：", len(json.dumps(adv, ensure_ascii=False)))
