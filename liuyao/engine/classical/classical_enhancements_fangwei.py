# -*- coding: utf-8 -*-
"""方位层（#23）接入引擎：把 `fangwei_rules` 的候选方位挂进 advanced_analysis。

只出**结构与书据**，不作吉凶判词（SKILL.md 铁律三），不参与评分，也不覆写任何主判。
适用域按问语关键词开启：避乱／避难／迁移／移徙／行方（取方）与 延医／请医／求医（三档）。
三档的前件**一律取既有单一真值源**，不另起口径：独发判据取自 `advanced_analysis.du_fa_du_jing`
（`type == "独发"`，其 `branch` 即独发之爻），用神取自 `_step2_data.selected_use_god.earthly_branch`，
五行生关系由 `fangwei_rules.du_fa_sheng_yong` 判（《增刪卜易》源L3412 逐字「如卦中有一爻独发而生用神者又以此方而延医」）。本模块须在 advanced_analysis 建好之后再挂 fangwei 键。

**为什么不迁 rules/ 目录**：rules/registry.json 的 v2 scope 是 cap 规则（压档/抬档）。
fangwei 是**非 cap 结构层**——只挂候选方位到 advanced_analysis，不改 verdict、不改分、
不作吉凶判词。它不参与 direction.py 的 detect_direction_caps → apply_caps 链路，
所以不属于 rules/ 仲裁层，留在 scripts/ 与 classical_enhancements 族平铺。
"""
from __future__ import annotations

# 第五百零八批升格：本文件在 <学科根>/engine/ 下，已不在 scripts/。
# 定位只走 _bootstrap 一份实现（向上搜 scripts/kernel_path.py，不按层数硬算），
# 依次配好 本目录／scripts／学科根 三处 sys.path，再交给 kernel_path 定位内核。
import os as _ks_os, sys as _ks_sys

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))
if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

# _bootstrap 在 engine/ 根（本文件的上层）：先入该目录，本文件才不依赖调用方替它配路径。
_ks_engine = _ks_os.path.dirname(_ks_d)
if _ks_engine not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_engine)

from _bootstrap import setup as _ks_setup  # noqa: E402

_ks_setup(__file__)


import fangwei_rules as FW

TAKE_DOMAIN = ("避乱", "避难", "避", "迁移", "移徙", "行方", "迁居", "徙居")
YIYI_DOMAIN = ("延医", "请医", "求医", "医")
BASIS_TAKE = "《增删卜易》源L2532 逐字「所以生方为吉，子孙之方亦吉，又当以旺衰分别」"
BASIS_YIYI = "《增删卜易》源L3412 逐字「卦中子孙爻旺者，延医于子孙之方」"
CTEXT_BASIS = BASIS_TAKE + "；" + BASIS_YIYI


def analyze_fangwei(result: dict) -> dict:
    hex_info = result.get("original_hexagram") or {}
    yao_lines = hex_info.get("yao_lines") or []
    dt = result.get("divination_time") or {}
    month_branch = (dt.get("month_stem_branch") or "")[1:]
    question = str(result.get("question") or "")
    if not yao_lines or not month_branch:
        return {"applicable": False, "reason": "缺卦爻或月令", "candidates": [], "ji_fang": []}
    is_take = any(k in question for k in TAKE_DOMAIN)
    is_yiyi = any(k in question for k in YIYI_DOMAIN)
    if not (is_take or is_yiyi):
        return {"applicable": False, "reason": "问语不属取方／延医域", "candidates": [], "ji_fang": []}

    yao = [{"branch": y.get("earthly_branch") or "", "six_relation": y.get("six_relation") or "",
            "moving": bool(y.get("is_moving")), "empty": bool(y.get("is_empty"))}
           for y in yao_lines]
    world = next((y for y in yao_lines if y.get("is_world")), {})
    response = next((y for y in yao_lines if y.get("is_response")), {})
    out: dict = {"applicable": True, "domain": [], "basis": CTEXT_BASIS}
    if is_take:
        b = FW.bi_luan_fang((world.get("earthly_branch") or ""), yao, month_branch)
        out["domain"].append("避乱／迁移取方")
        out["candidates"] = b["candidates"]
        out["ji_fang"] = b["ji_fang"]
        out["tie"] = b["tie"]
        out["level"] = b["level"]
        out["basis_take"] = b["basis"]
    if is_yiyi:
        ug_branch = ((result.get("_step2_data") or {}).get("selected_use_god") or {}).get("earthly_branch") or ""
        du = ((result.get("advanced_analysis") or {}).get("du_fa_du_jing") or {})
        df = [du] if (du.get("type") == "独发" and ug_branch
                      and FW.du_fa_sheng_yong(du.get("branch") or "", ug_branch)) else []
        y = FW.yan_yi_fang(yao, (response.get("earthly_branch") or ""), month_branch, df)
        out["domain"].append("延医取方")
        out["yan_yi"] = y["fang"]
        out["basis_yi"] = y["basis"]
        out["yan_yi_note"] = ("第三档已触发：独发之"
                              f"{du.get('branch') or ''}生用神{ug_branch}，亦取该爻之方（书据见 basis_yi）"
                              if df else
                              "第三档本盘未触发（无独发，或独发之爻不生用神）；"
                              f"独发取自 du_fa_du_jing，用神取自 step2.selected_use_god={ug_branch or '未取'}")
    return out
