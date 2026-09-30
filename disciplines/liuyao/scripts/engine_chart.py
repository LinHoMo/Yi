# -*- coding: utf-8 -*-
"""六爻纳甲引擎：数据表 / 干支历与真太阳时 / 排盘核心 / 文本输出 / 历史遗留梅花与批量接口。（拆分自 liuyao_engine.py，纯搬移不改逻辑；聚合入口见 liuyao_engine.py）。"""

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel, kernel_dir

_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    ADVANCE_PAIRS,
    BRANCH_ELEMENTS,
    BREAK_PAIRS,
    CHONG_PAIRS,
    EARTHLY_BRANCHES,
    EIGHT_PALACES,
    BAGUA_LINES,
    HEAVENLY_STEMS,
    HEXAGRAM_TRIGRAMS,
    HE_PAIRS,
    KE_CYCLE,
    NAJIA_BRANCHES,
    RETREAT_PAIRS,
    SHENG_CYCLE,
    STEM_ELEMENTS,
    TOMB_MAP,
)

from yishu_core.najia import najia_branch  # noqa: E402

import argparse

import json

import math

import os

import random

import sys

from datetime import datetime, timedelta

from pathlib import Path

from yishu_core.runtime import force_utf8_stdio as _force_utf8_stdio  # noqa: E402

from engine_calendar import get_day_stem_branch, get_hour_stem_branch, get_month_stem_branch, get_year_stem_branch
from engine_format import generate_analysis_hints
from chart_tables import BAGUA, BRANCH_NUMBERS, DAY_STEM_SPIRIT_START, EMPTY_DEATH, HEXAGRAMS, HEXAGRAM_LINE_TEXTS, HEXAGRAM_LOOKUP, NAJIA_STEMS, PALACE_LOOKUP, RESPONSE_POSITION, SIX_SPIRITS, TRIGRAM_LOOKUP, WORLD_POSITION

def coin_toss(random_gen=None):
    """
    铜钱摇卦法
    三枚铜钱投掷，每枚正面=3，反面=2
    三枚之和：6(老阴/动爻/阴), 7(少阳/静爻/阳), 8(少阴/静爻/阴), 9(老阳/动爻/阳)
    摇6次，从初爻到上爻
    
    Args:
        random_gen: 可选的 random.Random 实例，用于可复现结果。
                   为 None 时使用全局 random 模块。
    """
    rng = random_gen or random
    yao_values = []
    for _ in range(6):
        # 模拟三枚铜钱
        coins = [rng.choice([2, 3]) for _ in range(3)]
        total = sum(coins)
        yao_values.append(total)
    return yao_values


def time_based_hexagram(year, month, day, hour):
    """
    梅花易数时间起卦法
    年数 + 月数 + 日数 → ÷8 余数 = 上卦
    年数 + 月数 + 日数 + 时数 → ÷8 余数 = 下卦
    年数 + 月数 + 日数 + 时数 → ÷6 余数 = 动爻
    """
    # 年数用地支数
    year_branch = get_year_stem_branch(year, month, day)[1]
    year_num = BRANCH_NUMBERS[year_branch]
    
    # 月数用月份
    month_num = month
    
    # 日数用日期
    day_num = day
    
    # 时数用地支数
    if hour == 23 or hour == 0:
        hour_num = 1  # 子时
    elif 1 <= hour < 3:
        hour_num = 2
    elif 3 <= hour < 5:
        hour_num = 3
    elif 5 <= hour < 7:
        hour_num = 4
    elif 7 <= hour < 9:
        hour_num = 5
    elif 9 <= hour < 11:
        hour_num = 6
    elif 11 <= hour < 13:
        hour_num = 7
    elif 13 <= hour < 15:
        hour_num = 8
    elif 15 <= hour < 17:
        hour_num = 9
    elif 17 <= hour < 19:
        hour_num = 10
    elif 19 <= hour < 21:
        hour_num = 11
    else:
        hour_num = 12
    
    # 余数对应八卦: 1乾 2兑 3离 4震 5巽 6坎 7艮 8坤
    trigram_by_remainder = {
        1: "乾", 2: "兑", 3: "离", 4: "震",
        5: "巽", 6: "坎", 7: "艮", 0: "坤"
    }
    
    upper_rem = (year_num + month_num + day_num) % 8
    lower_rem = (year_num + month_num + day_num + hour_num) % 8
    
    upper_trigram = trigram_by_remainder[upper_rem]
    lower_trigram = trigram_by_remainder[lower_rem]
    
    # 动爻
    moving_rem = (year_num + month_num + day_num + hour_num) % 6
    moving_yao = moving_rem if moving_rem != 0 else 6  # 1-6, 0 means 6th
    
    # 构造六爻
    upper_lines = BAGUA[upper_trigram]["lines"]  # bottom to top: [下,中,上]
    lower_lines = BAGUA[lower_trigram]["lines"]
    
    # 合卦: yao从下到上 = lower[0],lower[1],lower[2],upper[0],upper[1],upper[2]
    yao_lines = lower_lines + upper_lines  # [y0,y1,y2,y3,y4,y5]
    
    # 转换为6/7/8/9 值
    yao_values = []
    for i, line in enumerate(yao_lines):
        if line == 1:  # yang line
            if (i + 1) == moving_yao:
                yao_values.append(9)  # old yang (moving)
            else:
                yao_values.append(7)  # young yang
        else:  # yin line
            if (i + 1) == moving_yao:
                yao_values.append(6)  # old yin (moving)
            else:
                yao_values.append(8)  # young yin
    
    return yao_values


def number_based_hexagram(a, b, c):
    """
    数字起卦法
    三个数a,b,c
    a % 8 → 上卦
    b % 8 → 下卦
    c % 6 → 动爻
    
    余数对应: 1乾 2兑 3离 4震 5巽 6坎 7艮 0坤
    """
    trigram_by_remainder = {
        1: "乾", 2: "兑", 3: "离", 4: "震",
        5: "巽", 6: "坎", 7: "艮", 0: "坤"
    }
    
    upper_rem = a % 8
    lower_rem = b % 8
    moving_rem = c % 6
    
    upper_trigram = trigram_by_remainder[upper_rem]
    lower_trigram = trigram_by_remainder[lower_rem]
    moving_yao = moving_rem if moving_rem != 0 else 6
    
    upper_lines = BAGUA[upper_trigram]["lines"]
    lower_lines = BAGUA[lower_trigram]["lines"]
    yao_lines = lower_lines + upper_lines
    
    yao_values = []
    for i, line in enumerate(yao_lines):
        if line == 1:
            if (i + 1) == moving_yao:
                yao_values.append(9)
            else:
                yao_values.append(7)
        else:
            if (i + 1) == moving_yao:
                yao_values.append(6)
            else:
                yao_values.append(8)
    
    return yao_values


def yao_value_to_lines(yao_values):
    """
    将6个数值(6/7/8/9)转为卦象信息
    返回 (下卦三爻, 上卦三爻) 的二进制列表, bottom to top
    """
    # yao_values[0]=初爻(bottom), yao_values[5]=上爻(top)
    # 下卦(内卦) = yao_values[0:3]
    # 上卦(外卦) = yao_values[3:6]
    
    lower_trigram_lines = []
    upper_trigram_lines = []
    
    for i in range(3):
        val = yao_values[i]
        # 6(old yin)=阴, 7(young yang)=阳, 8(young yin)=阴, 9(old yang)=阳
        if val in (7, 9):
            lower_trigram_lines.append(1)
        else:
            lower_trigram_lines.append(0)
    
    for i in range(3, 6):
        val = yao_values[i]
        if val in (7, 9):
            upper_trigram_lines.append(1)
        else:
            upper_trigram_lines.append(0)
    
    return lower_trigram_lines, upper_trigram_lines


def find_trigram_name(trigram_lines):
    """由三爻查找卦名"""
    key = tuple(trigram_lines)
    return TRIGRAM_LOOKUP.get(key, "未知")


def find_hexagram(upper_trigram_name, lower_trigram_name):
    """
    由上下卦查找六十四卦信息
    HEXAGRAM_LOOKUP 的 key 是 (upper, lower)
    """
    key = (upper_trigram_name, lower_trigram_name)
    result = HEXAGRAM_LOOKUP.get(key)
    if result:
        return result  # (seq, name, judgment)
    return None


def find_changed_hexagram(yao_values):
    """
    找到变卦信息（动爻变后的卦）
    返回变卦名和变了哪些爻
    """
    changed_indices = []
    new_values = list(yao_values)
    
    for i, val in enumerate(yao_values):
        if val == 9:  # 老阳变阴
            new_values[i] = 8
            changed_indices.append(i + 1)  # 1-based
        elif val == 6:  # 老阴变阳
            new_values[i] = 7
            changed_indices.append(i + 1)
    
    if not changed_indices:
        return None, []
    
    lower_lines, upper_lines = yao_value_to_lines(new_values)
    upper_name = find_trigram_name(upper_lines)
    lower_name = find_trigram_name(lower_lines)
    
    hex_info = find_hexagram(upper_name, lower_name)
    if hex_info:
        return hex_info, changed_indices
    return None, changed_indices


def get_palace_info(hex_name):
    """
    获取卦所属的宫和世代
    """
    result = PALACE_LOOKUP.get(hex_name)
    if result:
        return result  # (palace_name, generation)
    
    # 如果查不到，尝试从HEXAGRAMS中找
    for seq, name, upper, lower, judgment in HEXAGRAMS:
        if name == hex_name:
            # 尝试推断宫
            # 这里应该不会走到，因为PALACE_LOOKUP包含所有64卦
            return (upper, "未知")
    
    return ("未知", "未知")


def get_palace_element(palace_name):
    """获取宫五行"""
    if palace_name in EIGHT_PALACES:
        return EIGHT_PALACES[palace_name]["element"]
    # 如果不是宫名，可能是直接传入八卦名
    if palace_name in BAGUA:
        return BAGUA[palace_name]["element"]
    return "未知"


def determine_six_relations(branch, palace_element):
    """
    根据爻的地支五行和宫五行，确定六亲
    我(governor) = 宫五行
    生我者 = 父母
    我生者 = 子孙
    克我者 = 官鬼
    我克者 = 妻财
    同我者 = 兄弟
    """
    branch_element = BRANCH_ELEMENTS.get(branch, "未知")
    
    if branch_element == "未知" or palace_element == "未知":
        return "未知"
    
    # 五行相生: 木→火→土→金→水→木
    sheng_wo = {"木": "水", "火": "木", "土": "火", "金": "土", "水": "金"}  # 生我者的五行
    wo_sheng = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}  # 我生者的五行
    ke_wo = {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}     # 克我者的五行
    wo_ke = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}     # 我克者的五行
    
    if branch_element == palace_element:
        return "兄弟"
    elif sheng_wo.get(palace_element) == branch_element:
        return "父母"
    elif wo_sheng.get(palace_element) == branch_element:
        return "子孙"
    elif ke_wo.get(palace_element) == branch_element:
        return "官鬼"
    elif wo_ke.get(palace_element) == branch_element:
        return "妻财"
    else:
        return "未知"


def get_empty_death(day_stem_branch):
    """
    根据日柱旬空查空亡
    由日干支的前两个字符判断旬
    """
    # 提取日柱的天干地支对
    stem = day_stem_branch[0]
    branch = day_stem_branch[1]
    day_pair = stem + branch
    
    # 查表
    if day_pair in EMPTY_DEATH:
        return EMPTY_DEATH[day_pair]
    
    # 如果不在预计算表中，根据天干推算
    # 甲子旬:0-9, 甲戌旬:10-19, 甲申旬:20-29, 甲午旬:30-39, 甲辰旬:40-49, 甲寅旬:50-59
    # day_pair在60甲子中的序号
    stem_idx = HEAVENLY_STEMS.index(stem)
    branch_idx = EARTHLY_BRANCHES.index(branch)
    
    # 计算60甲子序号
    for i in range(60):
        if i % 10 == stem_idx and i % 12 == branch_idx:
            xun_index = i // 10
            break
    else:
        return []
    
    xun_keys = ["甲子", "甲戌", "甲申", "甲午", "甲辰", "甲寅"]
    return EMPTY_DEATH.get(xun_keys[xun_index], [])


def get_six_spirit(day_stem, line_position):
    """
    获取某爻的六神
    day_stem: 日天干
    line_position: 1(初爻) 到 6(上爻)
    """
    start_idx = DAY_STEM_SPIRIT_START.get(day_stem, 0)
    # line_position 1(初)对应start, 则index = start_idx + (line_position - 1)
    spirit_idx = (start_idx + line_position - 1) % 6
    return SIX_SPIRITS[spirit_idx]


def get_yao_name(position, nature):
    """
    获取爻名
    position: 1-6 (初到上)
    nature: "yang" or "yin"
    初九, 九二, 九三, 九四, 九五, 上九
    初六, 六二, 六三, 六四, 六五, 上六
    """
    yang_names = ["初九", "九二", "九三", "九四", "九五", "上九"]
    yin_names = ["初六", "六二", "六三", "六四", "六五", "上六"]
    
    if nature == "yang":
        return yang_names[position - 1]
    else:
        return yin_names[position - 1]


def get_yao_symbol(yao_value):
    """获取爻符号"""
    if yao_value in (7, 9):
        return "━━━"  # yang
    else:
        return "━ ━"  # yin


def build_hexagram_result(yao_values, question, method, year, month, day, hour,
                          explicit_time=None, minute=0):
    """
    基于6个爻值，构建完整的排盘结果

    explicit_time : dict, optional
        显式指定四柱（用于古典案例盲评——公历重算会丢失原始干支）。
        可含键：year_sb / month_sb / day_sb（完整干支，如"戊戌"），
        或 month_branch / day_branch（仅地支；天干缺失时月干用"甲"占位，
        日干缺失时按甲日计，仅影响六神与旬空精度，不影响旺衰主路径）。
        提供时跳过公历推算；未提供时行为与原来完全一致。
    minute : int, optional
        起卦时刻的分钟。只影响 divination_time.datetime 的**呈现**，
        不参与任何推演（干支以时辰为单位）。缺省 0，与旧行为一致。
    """
    # 1. 找出上下卦
    lower_lines, upper_lines = yao_value_to_lines(yao_values)
    lower_trigram_name = find_trigram_name(lower_lines)
    upper_trigram_name = find_trigram_name(upper_lines)
    
    # 2. 查找本卦信息
    hex_info = find_hexagram(upper_trigram_name, lower_trigram_name)
    if not hex_info:
        raise ValueError(f"无法识别的卦: 上{upper_trigram_name}下{lower_trigram_name}")
    
    seq, hex_name, judgment = hex_info
    
    # 3. 确定宫和世代
    palace_name, generation = get_palace_info(hex_name)
    palace_element = get_palace_element(palace_name)
    
    # 4. 世应位置
    world_pos = WORLD_POSITION.get(generation, 1)
    response_pos = RESPONSE_POSITION.get(world_pos, 4)
    
    # 5. 计算四柱
    if explicit_time and isinstance(explicit_time, dict):
        if explicit_time.get("day_sb"):
            day_sb = explicit_time["day_sb"]
            year_sb = explicit_time.get("year_sb") or get_year_stem_branch(year, month, day)
            month_sb = explicit_time.get("month_sb") or get_month_stem_branch(year, month, day)
        else:
            mb = explicit_time.get("month_branch")
            db = explicit_time.get("day_branch")
            if db:
                day_sb = "甲" + db
                month_sb = ("甲" + mb) if mb else get_month_stem_branch(year, month, day)
                year_sb = get_year_stem_branch(year, month, day)
            else:
                year_sb = get_year_stem_branch(year, month, day)
                month_sb = get_month_stem_branch(year, month, day)
                day_sb = get_day_stem_branch(year, month, day)
    else:
        year_sb = get_year_stem_branch(year, month, day)
        month_sb = get_month_stem_branch(year, month, day)
        day_sb = get_day_stem_branch(year, month, day)
    hour_sb = get_hour_stem_branch(day_sb[0], hour)
    
    # 6. 旬空
    empty_branches = get_empty_death(day_sb)
    
    # 7. 日干 (用于六神)
    day_stem = day_sb[0]
    
    # 8. 构建爻信息
    yao_lines_output = []
    moving_yaos = []
    
    for i in range(6):
        position = i + 1  # 1-based, 1=初爻(bottom), 6=上爻(top)
        val = yao_values[i]
        is_moving = val in (6, 9)
        
        # 阴阳属性
        if val in (7, 9):
            nature = "yang"
        else:
            nature = "yin"
        
        # 纳甲天干 (根据上下卦)
        if i < 3:
            # 内卦(下卦)
            stem = NAJIA_STEMS[lower_trigram_name]["inner"]
        else:
            # 外卦(上卦)
            stem = NAJIA_STEMS[upper_trigram_name]["outer"]
        
        # 纳甲地支
        if i < 3:
            branch = NAJIA_BRANCHES[lower_trigram_name]["inner"][i]
        else:
            branch = NAJIA_BRANCHES[upper_trigram_name]["outer"][i - 3]
        
        # 六亲
        six_relation = determine_six_relations(branch, palace_element)
        
        # 六神
        six_spirit = get_six_spirit(day_stem, position)
        
        # 旬空
        is_empty = branch in empty_branches
        
        # 爻名
        yao_name = get_yao_name(position, nature)
        
        # 爻符号
        symbol = get_yao_symbol(val)
        
        # 世应
        is_world = (position == world_pos)
        is_response = (position == response_pos)
        
        # 爻辞
        line_text = ""
        if hex_name in HEXAGRAM_LINE_TEXTS:
            line_text = HEXAGRAM_LINE_TEXTS[hex_name][i]
        
        yao_info = {
            "position": position,
            "name": yao_name,
            "nature": nature,
            "symbol": symbol,
            "heavenly_stem": stem,
            "earthly_branch": branch,
            "six_relation": six_relation,
            "six_spirit": six_spirit,
            "is_moving": is_moving,
            "is_world": is_world,
            "is_response": is_response,
            "is_empty": is_empty,
            "line_text": line_text,
        }
        
        yao_lines_output.append(yao_info)
        
        if is_moving:
            moving_yaos.append(position)
    
    # 9. 变卦信息
    changed_hex_name = None
    changed_judgment = None
    changed_changed_lines = []
    
    if moving_yaos:
        new_hex_info, changed_changed_lines = find_changed_hexagram(yao_values)
        if new_hex_info:
            changed_seq, changed_hex_name, changed_judgment = new_hex_info

    # 动爻所化之支与所化六亲属于"装卦"这一步的事实，必须记进爻数据。
    # 此前引擎只给 changed_hexagram.name，爻上没有变出支，于是思维链里
    # "动而化回头生，期于生我之日""化出之支值日"两条应期法则读不到输入，写了却从不触发。
    if changed_hex_name:
        for y in yao_lines_output:
            if not y.get("is_moving"):
                continue
            cb = najia_branch(changed_hex_name, y["position"])
            if not cb:
                continue
            y["changed_branch"] = cb
            y["changed_element"] = BRANCH_ELEMENTS.get(cb, "")
            y["changed_six_relation"] = determine_six_relations(cb, palace_element)
    
    # 八卦卜象解读（trigram symbolism interpretation）
    try:
        import os as _os
        _scripts_dir = _os.path.dirname(_os.path.abspath(__file__))
        if _scripts_dir not in sys.path:
            sys.path.insert(0, _scripts_dir)
        from trigram_symbolism import build_trigram_interpretation as _build_trigram_interp
        trigram_interp = _build_trigram_interp(
            {"original_hexagram": {"upper_trigram": upper_trigram_name, "lower_trigram": lower_trigram_name}},
            category="general"
        )
    except Exception as _e:
        # pragma: no cover - graceful degradation
        trigram_interp = None

    # 构建输出
    result = {
        "question": question,
        "divination_time": {
            "datetime": f"{year}-{month:02d}-{day:02d} {hour:02d}:{int(minute or 0):02d}",
            "year_stem_branch": year_sb,
            "month_stem_branch": month_sb,
            "day_stem_branch": day_sb,
            "hour_stem_branch": hour_sb,
        },
        "method": method,
        "empty_branches": empty_branches,
        "trigram_interpretation": trigram_interp,
        "original_hexagram": {
            "name": hex_name,
            "sequence": seq,
            "upper_trigram": upper_trigram_name,
            "lower_trigram": lower_trigram_name,
            "palace": palace_name,
            "palace_element": palace_element,
            "generation": generation,
            "judgment": judgment,
            "yao_lines": yao_lines_output,
        },
        "changed_hexagram": {
            "name": changed_hex_name,
            "judgment": changed_judgment,
            "changed_lines": moving_yaos if changed_hex_name else [],
        } if changed_hex_name else None,
        "analysis_hints": {
            "possible_use_gods": generate_analysis_hints(question),
        },
    }
    
    return result

