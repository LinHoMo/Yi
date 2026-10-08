# -*- coding: utf-8 -*-
"""六爻·身爻启用 / 忧解忧疑 / 六神旺衰三个结构域（从 classical_enhancements 拆出）。

【2026-10-08 拆分】父文件因 2026-10-07 批（OPT-yiin_dz-01 / zengshan_buyi_dz-03 /
六神旺衰）增至 2533 行，越过 tools/check.py [1] 的 2200 行巨石预算。按域外置是本仓
既有范式（classical_enhancements_{dufa,zhugui,menlei,fushi,yimao_zhugui} 同构）。
**函数体逐字节未改**，故六爻行为指纹（机械层）必须零漂移。

依赖方向：本模块 → yishu_core / narrative_utils / chart_tables / classical_enhancements，
**不得回调本模块的名字到父文件**（父文件不 import 本模块，消费方直连此处）。
"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    BRANCH_ELEMENTS,
    CHONG_PAIRS,
)

from narrative_utils import _pos_to_name  # noqa: E402  爻位名的唯一实现

from classical_enhancements import find_hexagram_body  # noqa: E402  安月卦身诀在父模块

def analyze_shen_yao_activation(result):
    """身爻启用谓词（《易隐》源 L217）——**纯结构判定，不批吉凶**。

    【OPT-yiin_dz-01，2026-10-07 新增】书源 L217 逐字：
        「凡卦之身用之为重，世之身司事还轻，世若不空不破，不须论身，
           世或空破，祸福方凭身象，盖取身以代世之劳耳。」
    即：**卦身**（月卦身）权重高于**世身**，但**世爻不空不破时身爻不参与取用**；
    仅当**世爻旬空或月破**时，身爻才作为替代用神参与祸福判断。

    本函数只做机械判定：世爻是否旬空/月破，以及由此决定的身爻参与状态。
    「参与取用」本身是结构事实；由此导出的吉凶断语**不进结构层**（AGENTS.md 铁律一），
    由 narrate 按 src 措辞回指。

    返回
    ----
    dict：
      activated       — bool，世空/世破时 True（身爻启动参与取用）
      reason          — 判定理由
      world_empty     — bool，世爻是否旬空
      world_break     — bool，世爻是否月破
      body_branch     — str，卦身支（由 find_hexagram_body 推得）
      classical_quote — 书源逐字引文
    """
    out = {
        "activated": False,
        "reason": "",
        "world_empty": False,
        "world_break": False,
        "body_branch": "",
        "classical_quote": "《易隐》安身章源L217：「凡卦之身用之为重，世之身司事还轻，"
                           "世若不空不破，不须论身，世或空破，祸福方凭身象，"
                           "盖取身以代世之劳耳。」",
    }

    hex_info = result.get("original_hexagram")
    if not isinstance(hex_info, dict):
        return out
    yao_lines = hex_info.get("yao_lines", []) or []
    if len(yao_lines) != 6:
        return out

    # 定位世爻
    world = next((y for y in yao_lines
                  if isinstance(y, dict) and y.get("is_world")), None)
    if world is None:
        return out

    world_branch = world.get("earthly_branch") or ""
    world_pos = world.get("position") or 0

    # 世爻阴阳 → 卦身支
    world_is_yang = bool(world.get("is_yang"))
    body_branch = find_hexagram_body(world_is_yang, world_pos)
    out["body_branch"] = body_branch

    # 旬空判定：世爻支是否在 empty_branches 中
    empty_branches = result.get("empty_branches", [])
    out["world_empty"] = world_branch in empty_branches

    # 月破判定：世爻支是否被月建冲
    dt = result.get("divination_time", {})
    month_sb = dt.get("month_stem_branch", "")
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    out["world_break"] = bool(
        month_branch and world_branch
        and ((world_branch, month_branch) in CHONG_PAIRS
             or (month_branch, world_branch) in CHONG_PAIRS))

    # 身爻启用谓词：世空 OR 世破 → 身爻参与取用
    if out["world_empty"] or out["world_break"]:
        out["activated"] = True
        conds = []
        if out["world_empty"]:
            conds.append(f"世爻{world_branch}旬空")
        if out["world_break"]:
            conds.append(f"世爻{world_branch}月破（月建{month_branch}冲）")
        out["reason"] = (
            "身爻启用：" + "、".join(conds)
            + f"（源L217「世若不空不破，不须论身，世或空破，祸福方凭身象」）；"
            + f"卦身支为{body_branch}，以身代世参与取用")
    else:
        out["activated"] = False
        out["reason"] = (
            f"身爻不参与取用：世爻{world_branch}不空不破"
            f"（源L217「世若不空不破，不须论身」）；"
            f"卦身支为{body_branch}仅排盘输出")

    return out


def analyze_you_jie(result):
    """忧解/忧疑结构标签（《增刪卜易》源 L16/L419/L529/L3406）——**纯结构判定，不批吉凶**。

    【OPT-zengshan_buyi_dz-03，2026-10-07 新增】

    《增刪卜易》以**官鬼为忧神、子孙为解忧之神**：
      · 源 L419 逐字「如占防忧虑患者，若得子孙持世无忧，官鬼持世忧疑难解」
      · 源 L529 「子孙福德之神…为解忧之神…为剥官之神」
      · 源 L3406 「鬼作忧神休妄动，福为喜悦而生扶」「子孙乃制鬼之神…乃先去忧神，我无忧也」
      · 源 L16 「凡遇一切防火虑患者，但得子孙持世…管许安如泰山，唯忌官鬼持世，忧疑不解」

    **用神分域反转**（同书异说，按 AGENTS.md §三「口径分歧登记不采」原则**只标注结构事实**）：
      - 求名域（官鬼为用）：子孙发动 = 剥官（源L529「独占功名者忌之」），
        此时子孙不再是「解忧」而是「伤用」——子动伤官非忧解；
      - 病占父母域（父母为用）：子孙发动克官 = 官鬼本忧神被制，但子孙同时克用神（父母）
        时为害——需按占问域判定子孙之作用方向。
      **本层只在 output 中标明「忧解/忧疑」结构与「是否落入反转域」两个事实，
      不据此合成吉凶**（AGENTS.md 铁律一）。

    返回 dict：
      you_jie     — bool，子孙持世/动且不在反转域
      you_yi      — bool，官鬼持世/动
      zisun_moving/fgu_moving — list[str]，动爻六称
      held_zisun/held_gu      — bool，持世
      reversal_domain        — str，求名/病占父母/无
      reason                 — 判定理由
      classical_quote        — 书源引文
    """
    out = {
        "you_jie": False,
        "you_yi": False,
        "zisun_moving": [],
        "gu_moving": [],
        "held_zisun": False,
        "held_gu": False,
        "reversal_domain": "无",
        "reason": "",
        "classical_quote": "《增刪卜易》忧神/解忧判据："
                           "源L419「子孙持世无忧，官鬼持世忧疑难解」；"
                           "源L529「子孙…为解忧之神」；"
                           "L3406「鬼作忧神…子孙…先去忧神」。",
    }

    hex_info = result.get("original_hexagram")
    if not isinstance(hex_info, dict):
        return out
    yao_lines = hex_info.get("yao_lines", []) or []
    if len(yao_lines) != 6:
        return out

    # 持世判断
    for y in yao_lines:
        if not isinstance(y, dict):
            continue
        if y.get("is_world"):
            rel = y.get("six_relation")
            if rel == "子孙":
                out["held_zisun"] = True
            elif rel == "官鬼":
                out["held_gu"] = True

    # 动爻判断
    for y in yao_lines:
        if not isinstance(y, dict) or not y.get("is_moving"):
            continue
        rel = y.get("six_relation")
        pos = _pos_to_name(y.get("position") or 0)
        if rel == "子孙":
            out["zisun_moving"].append(pos)
        elif rel == "官鬼":
            out["gu_moving"].append(pos)

    # 占问域反转判断
    question = result.get("question", "")
    tc = result.get("thinking_chain") or {}
    s2 = tc.get("step2_use_god_identification") or {}
    ug_cat = s2.get("use_god_category", "")

    is_career = (ug_cat == "官鬼"
                 or any(k in question for k in
                        ("功名", "求官", "升迁", "仕宦", "官职")))
    is_illness_parent = (ug_cat == "父母"
                         and any(k in question for k in
                                 ("病", "疾", "症")))

    if is_career:
        out["reversal_domain"] = "求名（子孙剥官）"
    elif is_illness_parent:
        out["reversal_domain"] = "病占父母域"
    else:
        out["reversal_domain"] = "无"

    # 忧解/忧疑结构输出
    zisun_active = out["held_zisun"] or bool(out["zisun_moving"])
    gu_active = out["held_gu"] or bool(out["gu_moving"])

    if zisun_active:
        # 子孙持世/动 → 忧解（主结构），但在反转域中意义不同
        out["you_jie"] = True
        conds = []
        if out["held_zisun"]:
            conds.append("子孙持世")
        if out["zisun_moving"]:
            conds.append(f"子孙动（{'、'.join(out['zisun_moving'])}）")
        rev_note = ""
        if out["reversal_domain"] == "求名（子孙剥官）":
            rev_note = "（反转域：求名占子孙=剥官，源L529「独占功名者忌之」——此时非忧解而是伤用）"
        elif out["reversal_domain"] == "病占父母域":
            rev_note = "（反转域：病占父母域子孙克官但亦泄用——结构上不构成纯忧解）"
        out["reason"] = (
            f"忧解结构（源L419「子孙持世无忧」）：{'、'.join(conds)}{rev_note}")
    else:
        out["reason"] = "无忧解结构：子孙未持世亦未发动"

    if gu_active:
        out["you_yi"] = True
        conds = []
        if out["held_gu"]:
            conds.append("官鬼持世")
        if out["gu_moving"]:
            conds.append(f"官鬼动（{'、'.join(out['gu_moving'])}）")
        out["reason"] += (
            f"；忧疑结构（源L419「官鬼持世忧疑难解」）：{'、'.join(conds)}")
    else:
        out["reason"] += "；无忧疑结构：官鬼未持世亦未发动"

    return out

def analyze_six_god_wang_shuai(result: dict) -> dict:
    """六神旺衰标签（逢恩/归垣）试点结构标签函数。

    书源：《易隐》曹九锡 L879「凡六神喜逢恩要归垣，克忌神，生用神者吉……
    何谓逢恩，龙入水，雀入木，勾入火，蛇入木，虎入土，武入金，是也。
    何谓归垣，春龙，夏雀，秋虎，冬武，三九月勾，六十二月蛇，为当权之归垣。
    龙入木，雀入火，勾入辰戌，蛇入丑未，虎入金，武入水，为本象之归垣也。」

    ⚠ 本函数输出仅作叙述修饰，不参与任何 verdict/weight/final_score 判定。
    ⚠ 纳入本模块仅为「六神旺衰标签试点」，非完整判据。

    四季（月支）× 六神 × 宫（爻位）三维标签：
      逢恩 = 六神所入五行 被本爻地支所生（生我者为恩）
      当权归垣 = 六神得季节（月支落入六神旺月）
      本象归垣 = 六神地支与本宫地支同五行

    返回：{
        "month_branch": str,
        "month_element": str,
        "lines": [{position, name, six_spirit, branch, branch_element,
                   feng_en, gui_yuan_seasonal, gui_yuan_elemental, tag}],
        "summary": {逢恩: [name,…], 当权归垣: [name,…], 本象归垣: [name,…]},
        "comment": str,  # 叙述层纯文本，不参与判定
    }
    """
    hex_info = result.get("original_hexagram", {})
    yao_lines = hex_info.get("yao_lines", [])
    div_time = result.get("divination_time", {})
    month_sb = div_time.get("month_stem_branch", "")
    month_branch = month_sb[1:] if isinstance(month_sb, str) and len(month_sb) >= 2 else ""
    month_element = BRANCH_ELEMENTS.get(month_branch, "")

    line_tags: list[dict] = []
    feng_en_names: list[str] = []
    gui_yuan_seasonal_names: list[str] = []
    gui_yuan_elemental_names: list[str] = []

    for yao in yao_lines:
        spirit = yao.get("six_spirit", "")
        branch = yao.get("earthly_branch", "")
        pos = yao.get("position")
        name = yao.get("name", "")
        branch_element = BRANCH_ELEMENTS.get(branch, "")

        # 逢恩：六神所入五行地支 是否 恰为本爻地支
        feng_en_branches = _SIX_GOD_FENG_EN.get(spirit, [])
        feng_en = branch in feng_en_branches

        # 当权归垣：月支是否落入六神旺月
        seasonal = _SIX_GOD_GUI_YUAN_SEASONAL.get(spirit, {})
        sy = seasonal.get("月支", [])
        gui_yuan_seasonal = month_branch in sy

        # 本象归垣：六神本宫地支 是否 恰为本爻地支
        elemental = _SIX_GOD_GUI_YUAN_ELEMENTAL.get(spirit, [])
        gui_yuan_elemental = branch in elemental

        tag_parts: list[str] = []
        if feng_en:
            tag_parts.append(f"逢恩({spirit}入{branch_element})")
            feng_en_names.append(name)
        if gui_yuan_seasonal:
            season_label = seasonal.get("季节", "")
            tag_parts.append(f"当权归垣({season_label}{spirit})")
            gui_yuan_seasonal_names.append(name)
        if gui_yuan_elemental:
            tag_parts.append(f"本象归垣({spirit}入{branch})")
            gui_yuan_elemental_names.append(name)

        line_tags.append({
            "position": pos,
            "name": name,
            "six_spirit": spirit,
            "branch": branch,
            "branch_element": branch_element,
            "feng_en": feng_en,
            "gui_yuan_seasonal": gui_yuan_seasonal,
            "gui_yuan_elemental": gui_yuan_elemental,
            "tag": "、".join(tag_parts) if tag_parts else "",
        })

    # 叙述层 comment — 仅供 narrate 使用，绝不回写 verdict/weight
    comment_parts: list[str] = [
        f"月令{month_branch}({month_element})",
    ]
    if feng_en_names:
        comment_parts.append(f"逢恩：{'、'.join(feng_en_names)}")
    if gui_yuan_seasonal_names:
        comment_parts.append(f"当权归垣：{'、'.join(gui_yuan_seasonal_names)}")
    if gui_yuan_elemental_names:
        comment_parts.append(f"本象归垣：{'、'.join(gui_yuan_elemental_names)}")
    if not (feng_en_names or gui_yuan_seasonal_names or gui_yuan_elemental_names):
        comment_parts.append("六神无逢恩归垣特殊组合")

    return {
        "month_branch": month_branch,
        "month_element": month_element,
        "lines": line_tags,
        "summary": {
            "逢恩": feng_en_names,
            "当权归垣": gui_yuan_seasonal_names,
            "本象归垣": gui_yuan_elemental_names,
        },
        "comment": "；".join(comment_parts),
    }

__all__ = [
    "analyze_shen_yao_activation",
    "analyze_you_jie",
    "analyze_six_god_wang_shuai",
]
