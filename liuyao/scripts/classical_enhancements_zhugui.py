# -*- coding: utf-8 -*-
"""六爻古典增强：助鬼伤身 结构凶格（自 classical_enhancements.py 按域切出）。

【OPT-duanyi_tianji_dz-01，2026-10-07 新增】

《断易天机·助鬼伤身》是一则**结构凶格**，判定式书源写得很死（源 L136 逐字）：
    「三、在鬼爻可以伤克世爻（卦身）的情况下，妻财爻又动来助鬼，就是“助鬼伤身”了。」

**只标象、不打分**（与同目录 `classical_enhancements_dufa.py` 的独发/独静同策略）：
  · 成立/不成立只作为**结构事实**透出，交 narrate 作正文辅助说明；
  · **不改吉凶主判、不进主分**——书源同段的话（「其凶愈甚」「必主身有灾殃」等）
    是吉凶断语，按 AGENTS.md 铁律一不得进结构层，一概不入本模块；
  · 断语素材（引文/标签句）一律取自 `data/rules/verdict_texts.json`
    的 `pattern_verdict_labels["助鬼伤身"]`（经 narrative_utils 加载），代码内不写字面量。

**applicability（解救条件）——本条最容易被实现错的地方**：
源 L132 说「若有子孙发动，解神来救，庶可反凶成吉」，但 **L137 逐字限定**：
    「是指卦中**只有**子孙爻发动的情况。……因为子孙发动可以克官鬼，
      如果**妻财同动**的话，子孙不但不克官鬼，反而子孙生财，财又生官，
      形成连续相生，使官鬼更旺。」
故「子孙动」**不构成解救**——只有**子孙独发（妻财不与之同动）**才是。
本模块的 `applicability` 字段即按此登记，见 `_jiejiu()`。
"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

from yishu_core.symbols import CHONG_PAIRS, KE_CYCLE  # noqa: E402

from narrative_utils import (  # noqa: E402
    PATTERN_VERDICT_LABELS,
    _pos_to_name,
)

__all__ = ["analyze_zhu_gui_shang_shen"]

_LABELS = (PATTERN_VERDICT_LABELS.get("助鬼伤身") or {})

_CHONG = set()
for _a, _b in CHONG_PAIRS:
    _CHONG.add((_a, _b))
    _CHONG.add((_b, _a))


def _ke_or_chong(attacker_branch: str, target_branch: str) -> str:
    """鬼爻对世爻（或卦身）的作用：'冲' / '克' / ''（无作用）。"""
    if not attacker_branch or not target_branch:
        return ""
    if (attacker_branch, target_branch) in _CHONG:
        return "冲"
    a_el = _elem(attacker_branch)
    t_el = _elem(target_branch)
    if a_el and t_el and KE_CYCLE.get(a_el) == t_el:
        return "克"
    return ""


def _elem(branch: str) -> str:
    from yishu_core.symbols import BRANCH_ELEMENTS
    return BRANCH_ELEMENTS.get(branch, "")


def _jiejiu(moving_cai: list[str], moving_zisun: list[str]) -> dict:
    """解救条件（源 L132 + L137 的 applicability 排除条件）。

    返回 {applicable, reason}：
      · applicable=False 当妻财与子孙**同动**——源 L137 明写此时子孙生财、财生官，
        「形成连续相生，使官鬼更旺」，故 L132 的「子孙发动来救」**不适用**；
      · applicable=True 当子孙动而妻财不动（源 L137「是指卦中只有子孙爻发动的情况」）。

    ⚠️ **书源自身的一处互斥（本函数实测四象限已确认，非实现缺陷）**：
    源 L136 的成立式要求「妻财爻又动来助鬼」，而 L132/L137 的解救要求
    「只有子孙爻发动」（即财不与之同动）。二者落在**互斥**的输入上：
      财动·子孙不动 → 成立，但解救不适用（无子可救）
      财动·子孙动   → 成立，但解救**不适用**（L137 明文排除：财子同动反使鬼更旺）
      财不动·子孙动 → 不成立（无财不助鬼，L120「无财，凶有限」），此时才是纯解救位
    即**「成立」与「可解救」在书源口径下不同真**——这不是实现取巧，
    而是源 L137 亲自设的限制。故本层**如实输出两字段、不合并成单一吉凶档**，
    由 narrate 按「结构上」措辞转述（AGENTS.md 铁律一/三）。
    """
    if not moving_zisun:
        return {"applicable": False, "reason": "子孙未发动（源L132：若有子孙发动，解神来救）"}
    if moving_cai:
        return {"applicable": False,
                "reason": "子孙与妻财同动——源L137：「如果妻财同动的话，子孙不但不克官鬼，"
                          "反而子孙生财，财又生官，形成连续相生，使官鬼更旺」，"
                          "故 L132 的子孙解救在此**不适用**"}
    return {"applicable": True,
            "reason": "子孙独发、财不与其同动（源L137：「是指卦中只有子孙爻发动的情况」）"}


def analyze_zhu_gui_shang_shen(result):
    """助鬼伤身 结构判定（《断易天机》源 L134-L137）。

    成立三要件（全部为机械可判）：
      1. 有妻财爻**发动**（源 L134：助鬼之爻只有妻财爻；L119「不宜发动」故发动方助鬼）；
      2. 有官鬼爻对世爻（或卦身爻）构成**冲或克**（源 L135：身即世爻或卦身爻，
         鬼爻冲、克世爻或卦身爻）；
      3. 二者同时成立（源 L136 判定式）。

    返回 {established, reason, gui_positions, cai_moving, shen_target,
          moving_zisun, applicability, note, classical_quote}。
    **established 只表示「结构上是否成立」，不含任何吉凶判断，也不改主分。**
    """
    out = {
        "established": False,
        "reason": "",
        "gui_positions": [],
        "gui_actions": [],
        "cai_moving": [],
        "cai_moving_count": 0,
        "shen_target": "",
        "moving_zisun": [],
        "applicability": {},
        "note": "",
        "classical_quote": _LABELS.get("古典引文", ""),
    }

    hex_info = result.get("original_hexagram")
    if not isinstance(hex_info, dict):
        return out
    yao_lines = hex_info.get("yao_lines", []) or []
    if len(yao_lines) != 6:
        return out

    # 世爻 / 卦身爻：源 L135「此处所指之“身”，就是世爻，或者是卦身爻」
    world = next((y for y in yao_lines
                  if isinstance(y, dict) and y.get("is_world")), None)
    guashen = hex_info.get("gua_shen") or hex_info.get("gua_shen_branch") or ""
    targets = []
    if world is not None:
        targets.append(("世爻", world.get("earthly_branch") or ""))
    if guashen:
        targets.append(("卦身爻", guashen))

    # 要件1：妻财发动（源 L119/L134）
    moving_cai = [y for y in yao_lines
                  if isinstance(y, dict) and y.get("six_relation") == "妻财"
                  and y.get("is_moving")]
    out["cai_moving"] = [_pos_to_name(y.get("position") or 0) for y in moving_cai]
    out["cai_moving_count"] = len(moving_cai)

    # 要件2：官鬼对世/卦身有冲或克（源 L135）
    guis = [y for y in yao_lines
            if isinstance(y, dict) and y.get("six_relation") == "官鬼"]
    for g in guis:
        gb = g.get("earthly_branch") or ""
        for tname, tb in targets:
            act = _ke_or_chong(gb, tb)
            if act:
                out["gui_positions"].append(_pos_to_name(g.get("position") or 0))
                out["gui_actions"].append(
                    {"gui": _pos_to_name(g.get("position") or 0),
                     "branch": gb, "action": act, "target": tname,
                     "target_branch": tb, "is_moving": bool(g.get("is_moving"))})
                out["shen_target"] = tname

    # 要件3：合并判定（源 L136）
    out["moving_zisun"] = [_pos_to_name(y.get("position") or 0) for y in yao_lines
                          if isinstance(y, dict) and y.get("six_relation") == "子孙"
                          and y.get("is_moving")]
    out["applicability"] = _jiejiu([c.get("branch") for c in moving_cai],
                                   out["moving_zisun"])

    if out["cai_moving_count"] and out["gui_actions"]:
        out["established"] = True
        out["reason"] = (
            f"妻财发动（{ '、'.join(out['cai_moving']) }，共{out['cai_moving_count']}处，"
            f"源L134「助鬼之爻只有妻财爻」）＋ 官鬼"
            f"（{ '、'.join(out['gui_positions']) }）"
            f"{ out['gui_actions'][0]['action'] }{out['shen_target']}"
            "（源L135「鬼爻伤身……冲、克世爻或者卦身爻」）")
    else:
        miss = []
        if not out["cai_moving_count"]:
            miss.append("无妻财发动（源L120「无财，凶有限」——财不发动则不助鬼）")
        if not out["gui_actions"]:
            miss.append("无官鬼冲克世爻/卦身爻（源L135）")
        out["reason"] = "；".join(miss)

    # 结构标签句（模板来自 verdict_texts.json，代码不写字面量）
    tpl = _LABELS.get("成立" if out["established"] else "不成立提示", "")
    if tpl:
        out["note"] = tpl.format(out["reason"])
    jtpl = _LABELS.get("解救提示", "")
    if jtpl:
        out["note"] = (out["note"] + " " + jtpl.format(out["applicability"]["reason"])).strip()

    # 两财皆动之限（源 L120「若有两财皆动，其祸大凶」）——只登记结构计数，不写成凶量判
    if out["cai_moving_count"] >= 2:
        out["note"] += "（源L120：两财皆动——结构计数上的加倍，不作吉凶量判）"
    return out
