# -*- coding: utf-8 -*-
"""天气占主判据（#23 第2步）：通用旺衰/生克对天气无效，以本书规则为唯一主判据。

书据：父动主雨、财动主晴（《黄金策》源L300「卦中父动主有雨，财动主晴」；
《卜筮全书》源L5721「卦中父动，主雨；财动，主晴」、源L5770「五类中，唯父母为雨。
此爻空亡，或休囚不动，雨未可望」；《增删卜易》源L2040「占雨以父爻为主」；
《易隐》源L1541「占晴以子孙为用，占雨以父母为用也」——故占晴以子孙／财为晴神）。
"""
from __future__ import annotations


def _weather_verdict_score(qclass: str, lines: list, ug_cat: str):
    """天气占主判据（#23 第2步）：通用旺衰/生克对天气无效，以本书规则为唯一主判据。

    书据：父动主雨、财动主晴（《黄金策》源L300「卦中父动主有雨，财动主晴」；
    《卜筮全书》源L5721「卦中父动，主雨；财动，主晴」、源L5770「五类中，唯父母为雨。
    此爻空亡，或休囚不动，雨未可望」；《增删卜易》源L2040「占雨以父爻为主」；
    《易隐》源L1541「占晴以子孙为用，占雨以父母为用也」——故占晴以子孙／财为晴神）。
    占雨：有雨=吉、无雨=凶；占晴：晴=吉、不晴=凶。
    返回 (final_score 档位, 说明)；只给档位中值，不虚构分数（铁律三：分数是与古籍要点的一致性）。
    """
    moving_rels = {str(y.get("six_relation") or "") for y in lines
                   if isinstance(y, dict) and y.get("is_moving")}
    changed_rels = {str(y.get("changed_six_relation") or "") for y in lines
                    if isinstance(y, dict) and y.get("is_moving")}
    father_move = ("父母" in moving_rels) or ("父母" in changed_rels)
    wealth_move = ("妻财" in moving_rels) or ("妻财" in changed_rels)
    children_move = "子孙" in moving_rels or "子孙" in changed_rels
    # 父母空亡（休囚不动）则雨未可望——《卜筮全书》源L5770 逐字「五类中，唯父母为雨。
    # 此爻空亡，或休囚不动，雨未可望」。
    # 注意：晴神（妻财/子孙）的空亡/月破不在此作"不晴"判——野鹤诸案（如 随风·占晴 官鬼动化官鬼、
    # 妻财月破仍天開）表明空亡与否不决定晴雨，晴雨只认动变（父动主雨、财/子孙动主晴）。
    father_empty = any((y.get("six_relation") == "父母"
                        and (y.get("is_empty") or y.get("is_month_break")))
                       for y in lines if isinstance(y, dict))
    if qclass == "天气·占雨":
        if father_move:
            return 1.6, "父动主雨（有雨）"
        if wealth_move or children_move:
            return -1.9, "财/子孙动主晴（无雨）"
        if father_empty:
            return -1.9, "父母空亡（无雨）"
        return -1.9, "父母静，雨未可望（无雨）"
    else:  # 天气·占晴
        if wealth_move or children_move:
            return 1.6, "财/子孙动主晴（晴）"
        if father_move:
            return -1.9, "父动主雨（不晴）"
        return 0.2, "无晴象（待时）"
