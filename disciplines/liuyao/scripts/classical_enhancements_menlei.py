# -*- coding: utf-8 -*-
"""六爻古典增强：门类动静反转（求官域「子孙发动为忌」）结构标签。

【OPT-yilin_buyi_dz-02，2026-10-07 新增】

《易林补遗·仕宦升迁章》（源 L811-L814）给出一组**门类专属**的动静喜忌：
  · L813 歌诀逐字：「官职升迁子莫刚，唯求官鬼动为良，值生值旺当迁转。临陷临空且守常。
    鬼化子字忧调降，官连财位沐恩光。」
  · L814 注文逐字：「凡占升迁，须评官鬼，**子乃忌神，不宜发动**，官为主象，最利交重……」

即：**求官/升迁问类下，官鬼发动为良、子孙发动为忌**。这是**门类层**的判断，
与「用神发动为吉」的一般律不同向，故本层只**标结构事实**（官动/子动及其结构），
**不评分、不改吉凶主判**（AGENTS.md 铁律一）。

⚠️ **分歧登记（任务要求「先登记分歧再实现」）——本层的关键前置**：
现有 `data/rules/question_use_gods.json#功名·求官·官职·升迁` 一族已有一条 note，
其书源是**《增删卜易》**（citation 逐字：「今以自占功名﹐子動而克官也﹐如何反為用﹖
非也﹐仍看官爻」，offset 73026）。初看似与本书「子乃忌神」张力，实测**二者同向**：
  · 《增删卜易》该句是**驳**「子动即可反为用神」之说——「非也，仍看官爻」，
    即**否定以子孙为用**，与本书「子乃忌神，不宜发动」**一致**；
  · 真正的差异只在**表述层**：增删驳「子动为用」，易林明立「子乃忌神」；
    两者都把官爻立为主（增删「仍看官爻」／易林「须评官鬼」）。
故**不构成口径冲突，判定方向亦不冲突**，本层据此只加结构标签。
登记处见 `data/rules/verdict_texts.json#pattern_verdict_labels["门类动静/求官"]`
的 `分歧登记` 字段（含两书源逐字），**不擅自统一改写任何一方**。

另注：本书 L814 同时给出**两处相反方向的细则**，本层据「同书并存即异说」原则
**一并登记、不择一**：
  · 「官化子孙，非降即调，**卦中财子动亦然**」（财子动 → 降调）
  · 「若还**财子同兴转助官爻，又不降调**」（财子动且转助官 → 不降调）
  → 即「财子同动」的方向取决于是否**转助官爻**，这是本书内部的**条件分支**，
    不是矛盾。本层因此**不把「财子同动」单独打成某个标签**，只如实输出
    `zisun_moving`/`cai_moving` 两个结构事实，由 narrate 按分支表述。
"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

from narrative_utils import (  # noqa: E402
    PATTERN_VERDICT_LABELS,
    _pos_to_name,
)

__all__ = ["analyze_menlei_dongjing"]

_LABELS = (PATTERN_VERDICT_LABELS.get("门类动静/求官") or {})

# 求官/升迁问类词面（与 question_use_gods.json 同族同口径：功名/求官/官职/升迁）
_QIU_GUAN_KEYS = ("求官", "功名", "官职", "升迁", "仕宦", "官")


def _is_qiu_guan(question: str) -> bool:
    q = question or ""
    return any(k in q for k in _QIU_GUAN_KEYS)


def analyze_menlei_dongjing(result):
    """门类动静反转（求官域：官动为良 / 子动为忌）——只标结构，不评分。

    仅在**问类命中求官/升迁族**时生效（任务要求「仅限问类命中时生效」）；
    非求官问类返回 `hit=False`，不产出任何标签——避免与安神位/择日类
    「官宜静」等其他门类口径互相污染。

    返回 {hit, question_category, guan_moving, zisun_moving, cai_moving,
          zisun_moving_count, note, classical_quote}。
    **不判吉凶、不打分**：只如实报「官鬼发动了几处」「子孙发动了几处」。
    """
    out = {
        "hit": False,
        "question_category": "",
        "guan_moving": [],
        "zisun_moving": [],
        "cai_moving": [],
        "zisun_moving_count": 0,
        "note": "",
        "classical_quote": _LABELS.get("古典引文", ""),
    }
    question = str(result.get("question") or result.get("question_category") or "")
    if not _is_qiu_guan(question):
        return out
    out["hit"] = True
    out["question_category"] = "功名·求官·官职·升迁"

    hex_info = result.get("original_hexagram")
    if not isinstance(hex_info, dict):
        return out
    yao_lines = hex_info.get("yao_lines") or []
    if len(yao_lines) != 6:
        return out

    for y in yao_lines:
        if not isinstance(y, dict):
            continue
        rel = y.get("six_relation")
        if not y.get("is_moving"):
            continue
        pos = _pos_to_name(y.get("position") or 0)
        if rel == "官鬼":
            out["guan_moving"].append(pos)
        elif rel == "子孙":
            out["zisun_moving"].append(pos)
        elif rel == "妻财":
            out["cai_moving"].append(pos)
    out["zisun_moving_count"] = len(out["zisun_moving"])

    tpl = _LABELS.get("成立" if out["zisun_moving"] else "不成立提示", "")
    if tpl:
        out["note"] = tpl.format(
            guan="、".join(out["guan_moving"]) or "不动",
            zisun="、".join(out["zisun_moving"]) or "不动",
            cai="、".join(out["cai_moving"]) or "不动",
        )
    bt = _LABELS.get("财子同动分支", "")
    if bt and out["cai_moving"] and out["zisun_moving"]:
        out["note"] = (out["note"] + " " + bt.format(
            cai="、".join(out["cai_moving"]), zisun="、".join(out["zisun_moving"]))).strip()
    return out
