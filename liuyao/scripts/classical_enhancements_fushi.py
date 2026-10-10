# -*- coding: utf-8 -*-
"""《火珠林》财官伏五乡（占财/占鬼伏兄财父母子孙官）——**只出结构标签，不打分**。

【OPT-huozhulin_dz-01，2026-10-07 新增】

**先做归因（AGENTS.md §四.3，本条硬前置）**：任务提示「本书以『财官为主』立论，
与引擎用神框架口径不同，落地前须先做归因」。归因结论如下，逐条可核：

  ① **口径差异是「立论主轴」层面，不是判据层面**。本书九章通篇以「占财」「占鬼」
     立题（如 L55「8．占财伏鬼」、L71「11．占鬼伏兄」），即**先定问类、再论伏乡**；
     引擎 `liuyao_step2._check_fu_cang` 是**先定用神、再查伏藏**。两者**不是两套
     飞伏取法**（取法仍都是本宫首卦寻伏，与 OPT 建议里「经《增删卜易·飞伏神章》
     互证」一致），差别只在**叙述主轴**：本书按「财/官」这类**六亲**分类，
     引擎按「用神」这个**角色**分类。
  ② **因此本层只做「六亲×伏乡」的结构登记，不改引擎取伏神逻辑、不改用神选取**：
     引擎 `analyze_flying_hidden_interaction` 已给出每组飞伏的
     `covering_spirit.six_relation`（飞神六亲）与 `hidden_spirit.six_relation`（伏神六亲），
     本层**只把这两个六亲组成对**读出来打结构标签，**不新增任何判定、不改任何分数**。
  ③ **「财官为主」不等于「财官恒为用神」**：本书自己也分问类（占财则财为用、
     占官事则官为用），且明写取法条件（L54「本宫财官伏世下，方可取，不伏世下，
     则不取也」）。故本层**不假设财官即用神**，只按「伏神六亲 × 飞神六亲」配对。
  ④ **吉凶断语一律不入结构层**（铁律一）：九章的歌诀（「买卖遭伤」「口舌相侵」
     「同类欺凌」「因财有伤」「举状经官」「去路无门」「小人作难」）与其注文的
     断语，**全部只作 data 侧逐字引文登记**，由 narrate 按 `src` 回指自取。
     本函数只输出 `{pair, label, src}` 这样的**结构事实**。

**九条组合的源行（已 Read 逐字核验）**：见 data 侧 `data/rules/caiguan_fushi.json`
的 `九宫` 字段——L55 财伏鬼｜L60 财伏兄｜L65 财伏父（该章题「财伏父子」含财伏子，
见 L67「财伏子孙，有气必满」）｜L71 鬼伏兄｜L76 鬼伏财｜L82 鬼伏父｜L87 鬼伏子｜
L93 官鬼伏官；另 L49「出现伏藏」为总纲（出现旺相/伏藏有气/本宫财官伏世下方可取）。
"""
from __future__ import annotations

import json
import os as _ks_os, sys as _ks_sys
from pathlib import Path

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))
if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel  # noqa: E402

_ensure_kernel(__file__)

__all__ = ["huozhulin_fushi_tags", "FU_SHI_PAIRS"]

_DATA = Path(__file__).resolve().parents[1] / "data" / "rules" / "caiguan_fushi.json"
_TABLE: dict | None = None


def _table() -> dict:
    global _TABLE
    if _TABLE is None:
        try:
            _TABLE = json.loads(_DATA.read_text(encoding="utf-8"))
        except OSError:
            _TABLE = {}
    return _TABLE


def FU_SHI_PAIRS() -> dict:
    """(伏神六亲, 飞神六亲) → 结构标签名；缺表返回 {}。"""
    return (_table().get("九宫") or {})


def huozhulin_fushi_tags(result) -> list[dict]:
    """财官伏五乡结构标签（源 L55/L60/L65/L71/L76/L82/L87/L93）。

    读 `advanced_analysis.flying_hidden_interaction.interactions` 里每组飞伏的
    飞神/伏神六亲，配对后打标签。**只出结构名 + 出处行号**，无吉凶、无分数。

    返回 [{伏神, 飞神, 标签, src}]；无伏藏或不在九宫内则返回 []。
    """
    table = FU_SHI_PAIRS()
    if not table:
        return []
    fhi = ((result.get("advanced_analysis") or {})
           .get("flying_hidden_interaction") or {})
    if not isinstance(fhi, dict) or not fhi.get("has_interaction"):
        return []
    out = []
    for it in fhi.get("interactions") or []:
        if not isinstance(it, dict):
            continue
        # effects.analyze_flying_hidden_interaction 的字段名为 fei_shen（飞神六亲）
        # / fu_shen（伏神六亲），本层按此读，不新造字段名。
        fei = it.get("fei_shen") or ""
        fu = it.get("fu_shen") or ""
        if not fu or not fei:
            continue
        rec = table.get(f"{fu}伏{fei}")
        if rec:
            out.append({"伏神": fu, "飞神": fei,
                        "标签": rec.get("标签") or f"{fu}伏{fei}",
                        "src": rec.get("src") or ""})
    return out
