# -*- coding: utf-8 -*-
"""调候与格局扶抑用神冲突仲裁登记层。

口径（2026-10-09 订正，体例照 `SKILL.md` §二「判据分层」）：

  子平格局层为**体**（扶抑按 strength 三分支取），调候层为**用**
  （《穷通宝鉴》月令×日主查表）。**本模块不自动选优**——书源同样不支持排序：
  《穷通宝鉴》data/sources/qiong_tong_bao_jian_dz.dz.txt:11 只言「贵在折衷，归於中道」，
  未给两层排先后。

  因此本函数只做**差异登记**：
    · 调候主神所在十神类 vs 格局扶抑喜用类 → 是否同一类？
    · 若同一类 → 标记「调候与格局一致」（无需仲裁）；
    · 若不同类 → 标记「调候与格局分歧」，输出差异标签说明分歧点，
      交给 LLM 转述——**代码不裁决哪方更优**。

返回结构：{
    conflict: bool,               # 是否出现分歧（False = 一致/无调候数据）
    label: str,                   # 一眼读的差异标签
    tiaohou_perspective: str,     # 调候口径描述
    pattern_perspective: str,     # 格局口径描述
    detail: str,                  # 详细差异说明
}
"""
from __future__ import annotations

from .relations import ten_god as _ten_god

# 十神 → 作用类（与 bazi_factors/_common.TEN_GOD_GROUP 同源，独立副本避循环依赖）
_TG = {
    "比肩": "比劫", "劫财": "比劫",
    "正印": "印", "偏印": "印",
    "食神": "食伤", "伤官": "食伤",
    "正财": "财", "偏财": "财",
    "正官": "官杀", "偏官": "官杀", "七杀": "官杀",
}


def _stem_role(stem: str, day_stem: str) -> str:
    """天干（对日主）→ 十神作用类。"""
    if not stem or not day_stem:
        return ""
    return _TG.get(_ten_god(day_stem, stem), "")


def resolve_tiaohou_vs_pattern(strength_result: dict,
                               day_stem: str,
                               tiaohou_result: dict | None = None) -> dict | None:
    """调候用神 vs 格局扶抑用神 —— **差异登记**（不自动选优）。

    参数：
      strength_result —— `strength_and_pattern()` 返回的 dict（至少含 strength /
                         useful_gods / tiaohou / pattern 字段）；
      day_stem       —— 日主天干（用于把调候天干映射到十神类）；
      tiaohou_result —— 可选，独立传入调候结果（缺省则取 strength_result["tiaohou"]）。

    返回 None = 无调候数据（宁缺勿滥，不仲裁）。
    否则返回 {conflict, label, tiaohou_perspective, pattern_perspective, detail}。
    """
    if not strength_result or not day_stem:
        return None

    # 调候查表结果
    th = tiaohou_result or strength_result.get("tiaohou")
    if not th or not th.get("main"):
        return None  # 原文无明文 → 无数据 → 不仲裁

    main_stem = th.get("main", "")
    assist_stem = th.get("assist", "")

    # 调候主神所在十神类
    main_role = _stem_role(main_stem, day_stem)
    assist_role = _stem_role(assist_stem, day_stem) if assist_stem else ""

    # 格局扶抑喜用类
    useful = list(strength_result.get("useful_gods") or [])
    taboo = list(strength_result.get("taboo_gods") or [])
    strength = strength_result.get("strength", "")
    pattern = strength_result.get("pattern", "")

    # 调候口径描述
    tiaohou_desc = f"调候主神={main_stem}（{main_role}）"
    if assist_stem:
        tiaohou_desc += f"、佐神={assist_stem}（{assist_role}）"

    # 格局口径描述
    pattern_desc = (
        f"格局={pattern}，强弱={strength}，"
        f"扶抑喜用={'、'.join(useful) or '—'}，忌={'、'.join(taboo) or '—'}"
    )

    # 调候主神的十神类映射不出来 = 数据缺失，不是分歧。
    # 本模块契约（见文件头）是「无调候数据 → 返回 None，不仲裁」；
    # 旧实现把空 main_role 落到下面的 else，登记成 conflict=True 的「边界情形」，
    # 于是报告里出现「调候格局关系：调候与格局分歧」而依据句只写着「未匹配」——
    # 缺数据被当成冲突。
    if not main_role:
        return None

    useful_set = set(useful)
    consistent_roles = {r for r in (main_role, assist_role) if r}

    if main_role in useful_set:
        # 调候主神落在格局喜用类 → 主神一致；佐神落在忌类则是**部分分歧**，
        # 不能整条标成「一致」（读者据 label 决去留，detail 里的分歧会被忽略）。
        if assist_stem and assist_role and assist_role not in useful_set:
            detail = (f"{tiaohou_desc}；{pattern_desc}。"
                      f"主神{main_stem}（{main_role}）与格局喜用{'、'.join(useful)}一致；"
                      f"佐神{assist_stem}（{assist_role}）落在格局忌类，"
                      f"书源未给两层排序，此处只登记差异、不选优。")
            return {
                "conflict": False,
                "label": "主神一致·佐神分歧",
                "tiaohou_perspective": tiaohou_desc,
                "pattern_perspective": pattern_desc,
                "detail": detail,
            }
        # 序：按格局喜用原序取交集，不用 `set & set`——集合迭代序随 PYTHONHASHSEED
        # 每进程随机，同输入两次跑会写出不同 detail（2026-10-12 实测曾令金标准随机漂移）。
        detail = (f"{tiaohou_desc}；{pattern_desc}。"
                  f"调候主神与格局扶抑喜用同属{'、'.join(r for r in useful if r in consistent_roles)}，"
                  f"两层口径一致，无需仲裁。")
        return {
            "conflict": False,
            "label": "一致",
            "tiaohou_perspective": tiaohou_desc,
            "pattern_perspective": pattern_desc,
            "detail": detail,
        }

    # 调主神落在扶抑忌类 → 分歧
    if main_role in taboo:
        conflict = True
        detail = (f"{tiaohou_desc}；{pattern_desc}。"
                  f"调候主神{main_stem}（{main_role}）落在格局扶抑忌类（{'、'.join(taboo)}），"
                  f"与格局喜用{'、'.join(useful)}方向相左——"
                  f"书源《穷通宝鉴》只言「贵在折衷，归於中道」，未给两层排先后；"
                  f"此处登记分歧、不自动选优，交 LLM 转述。")
    else:
        # 主神的十神类既不在 useful 也不在 taboo（边界情形）
        conflict = True
        detail = (f"{tiaohou_desc}；{pattern_desc}。"
                  f"调候主神{main_stem}（{main_role}）未匹配格局扶抑喜忌类——"
                  f"属边界情形，交人工复核。")

    return {
        "conflict": conflict,
        "label": "调候与格局分歧",
        "tiaohou_perspective": tiaohou_desc,
        "pattern_perspective": pattern_desc,
        "detail": detail,
    }
