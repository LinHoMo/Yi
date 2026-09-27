# -*- coding: utf-8 -*-
"""六爻思维链：基元表 / 断语库 / 通用辅助 / 五步推演 / 应期 / 叙事组装。（拆分自 thinking_chain.py，纯搬移不改逻辑；聚合入口见 thinking_chain.py）。"""

from __future__ import annotations

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
    HEAVENLY_STEMS,
    HEXAGRAM_TRIGRAMS,
    HE_PAIRS,
    KE_CYCLE,
    NAJIA_BRANCHES,
    RETREAT_PAIRS,
    SHENG_CYCLE,
    STEM_ELEMENTS,
    TOMB_MAP,
    palace_of_key,
    EARTHLY_BRANCHES as BRANCHES,
)

from datetime import datetime, timedelta

import json

import re

from pathlib import Path

from chain_narrate import _build_reasoning_chain, _get_hexagram_body_summary_note, find_classical_quotes
from chain_step4 import _detect_special_pattern, _user_reason
from chain_support import safe_get
from chain_tables import HEXAGRAM_LIUCHONG, HEXAGRAM_LIUHE, SAN_HE, _60_CYCLE_BASE, _BRANCH_CLASH_MAP, _ELEMENT_PEAK_MONTHS, _HE_MAP

import json as _json
from pathlib import Path as _P
_YD = _json.loads((_P(__file__).resolve().parents[1] / 'data' / 'narrative_templates.json').read_text(encoding='utf-8')).get('yingqi_descriptions', {})
from chain_verdicts import (
    CLASSICAL_INTERPRETATIONS as CINTERP,
    STEP5_CONFIDENCE as CONF_TXT,
    STEP5_FACTOR_REASONS as FREASON,
    STEP5_SPIRIT_REASONS as SPIRIT_TXT,
    STEP5_VERDICT_DESCS as VDESC,
    STEP5_YINGQI as YINGQI_TXT,
    note_text,
    vdesc,
)

def _predict_timing(r: dict, step3_data: dict, step1_data: dict, day_branch: str, special_pattern=None) -> dict:
    """
    应期判断 — v8：前置「重点应期」地支词，兼顾古籍规则与人话可读性。
    """
    use_god_branch = safe_get(step3_data, "use_god_branch", default="") or ""
    use_god_element = safe_get(step3_data, "use_god_element", default="")
    strength_level = safe_get(step3_data, "strength_level", default="中和")
    is_empty = safe_get(step3_data, "is_empty", default=False)
    is_month_break = safe_get(step3_data, "is_month_break", default=False)

    BRANCH_ORDER = "子丑寅卯辰巳午未申酉戌亥"

    def _pair_partner(pairs, b: str) -> str:
        """配对表是单向列出的（每对只写一次），必须双向查。"""
        for a, c in pairs:
            if b == a:
                return c
            if b == c:
                return a
        return ""

    def _chong(b: str) -> str:
        return _pair_partner(CHONG_PAIRS, b)

    def _he(b: str) -> str:
        return _pair_partner(HE_PAIRS, b)

    key_branches: list[str] = []

    def _push(b: str, suffix: str = "日"):
        if not b or b not in BRANCH_ORDER:
            return
        token = f"{b}{suffix}"
        if token not in key_branches:
            key_branches.append(token)

    timing_reasons = []
    timing_methods = []

    # 收集卦中地支
    yao_lines = ((r.get("original_hexagram") or {}).get("yao_lines")) or []
    for y in yao_lines:
        if not isinstance(y, dict):
            continue
        br = y.get("earthly_branch") or ""
        if y.get("is_moving"):
            _push(br)
            chg = y.get("changed_earthly_branch") or y.get("changed_branch") or ""
            if not chg:
                # 尝试从 changed_hexagram 对应位取
                pass
            if chg:
                _push(chg)
        if y.get("six_relation") and use_god_branch and br == use_god_branch:
            _push(br)

    # 变卦地支
    ch_hex = r.get("changed_hexagram") or {}
    for y in (ch_hex.get("yao_lines") or []):
        if isinstance(y, dict) and y.get("is_moving"):
            _push(y.get("earthly_branch") or "")
        # 动爻变出支通常在 original 的 moving 标记里，双保险
        if isinstance(y, dict) and y.get("changed_earthly_branch"):
            _push(y.get("changed_earthly_branch"))

    # 原始动爻若带 changed_branch 字段
    for y in yao_lines:
        if isinstance(y, dict):
            for k in ("changed_earthly_branch", "changed_branch", "transform_branch"):
                if y.get(k):
                    _push(y.get(k))

    # 日月
    if day_branch:
        _push(day_branch)
    month_branch = ""
    mdt = r.get("divination_time") or {}
    if isinstance(mdt, dict):
        msb = mdt.get("month_stem_branch") or mdt.get("month_branch") or ""
        month_branch = msb[-1] if msb else ""
        if month_branch:
            _push(month_branch, "月")

    # 用神及其冲合
    if use_god_branch:
        _push(use_god_branch)
        _push(_chong(use_god_branch))
        _push(_he(use_god_branch))

    # 原神旺日
    step2_d = safe_get(r, "_step2_data", default={}) or {}
    yuan_elem = (step2_d.get("yuan_shen") or {}).get("element", "")
    peak_days = {"木": "寅卯", "火": "巳午", "土": "辰戌丑未", "金": "申酉", "水": "亥子"}
    pd = peak_days.get(yuan_elem, "")
    for ch in pd:
        _push(ch)
    for pos in ((step2_d.get("yuan_shen") or {}).get("positions") or []):
        if isinstance(pos, dict):
            _push(pos.get("earthly_branch") or "")

    # 伏神地支
    fu = step2_d.get("fu_cang_detail") or {}
    if isinstance(fu, dict):
        for res in fu.get("results") or []:
            if isinstance(res, dict):
                _push(((res.get("fu_shen") or {}).get("branch")) or "")
                _push(((res.get("fei_shen") or {}).get("branch")) or "")

    # 旬空地支（出空应期）
    for e in (r.get("empty_branches") or []):
        _push(e)

    # 合局/贪合 → 冲开之支（冲开合局方应）
    step4_all = safe_get(r, "_step4_data", default={}) or {}
    # 冲用神、合用神之支
    if use_god_branch:
        _push(_chong(use_god_branch))
        _push(_he(use_god_branch))
    # 卦中地支：动爻候合、静爻候冲；并冲开六合之支
    he_branches = []
    for y in yao_lines:
        if not isinstance(y, dict):
            continue
        br = y.get("earthly_branch") or ""
        if not br:
            continue
        if y.get("is_moving"):
            _push(_he(br))
            _push(_chong(br))
        else:
            _push(_chong(br))
        for a, b in HE_PAIRS:
            if br == a:
                he_branches.append(b)
            elif br == b:
                he_branches.append(a)
    for hb in he_branches:
        _push(_chong(hb))  # 冲开合局
        _push(hb)
    # 日月与卦爻成合：冲开该合
    if day_branch:
        for a, b in HE_PAIRS:
            if day_branch == a:
                _push(_chong(b)); _push(b)
            elif day_branch == b:
                _push(_chong(a)); _push(a)
    if month_branch:
        for a, b in HE_PAIRS:
            if month_branch == a:
                _push(_chong(b)); _push(b)
            elif month_branch == b:
                _push(_chong(a)); _push(a)
    # 伏神得出：伏支值日 + 冲飞之日
    fu_d = safe_get(r, "_step2_data", default={}) or {}
    fu_detail = fu_d.get("fu_cang_detail") or {}
    if isinstance(fu_detail, dict):
        for res in fu_detail.get("results") or []:
            if not isinstance(res, dict):
                continue
            fu_br = ((res.get("fu_shen") or {}).get("branch")) or ""
            fei_br = ((res.get("fei_shen") or {}).get("branch")) or ""
            if fu_br:
                _push(fu_br)
            if fei_br:
                _push(_chong(fei_br))
    # 用神临月建：该五行旺月/日
    if use_god_branch and month_branch:
        if use_god_branch == month_branch or (
            BRANCH_ELEMENTS.get(use_god_branch) == BRANCH_ELEMENTS.get(month_branch)
        ):
            elem = BRANCH_ELEMENTS.get(use_god_branch, "")
            peak = {"木": "寅卯", "火": "巳午", "土": "辰戌丑未", "金": "申酉", "水": "亥子"}.get(elem, "")
            for ch in peak:
                _push(ch)
            _add_month_note = True
    # 原神旺月支
    if pd:
        for ch in pd:
            _push(ch)
    # 世爻之冲（世应应期）
    for y in yao_lines:
        if isinstance(y, dict) and y.get("is_world"):
            _push(_chong(y.get("earthly_branch") or ""))
            break

    # 旺衰规则
    if strength_level in ("极旺", "旺"):
        timing_methods.append({
            "method": "逢值",
            "description": _YD["value_day"].format(use_god_branch=use_god_branch),
            "type": "速应",
        })
        cb = _chong(use_god_branch)
        if cb:
            timing_methods.append({
                "method": "逢冲",
                "description": _YD["clash_day"].format(use_god_branch=use_god_branch, cb=cb),
                "type": "速应",
            })
            _push(cb)
    elif strength_level in ("偏弱", "弱", "极弱"):
        element_peak_months = {
            "木": "寅卯月（春）",
            "火": "巳午月（夏）",
            "土": "辰戌丑未月（季月）",
            "金": "申酉月（秋）",
            "水": "亥子月（冬）",
        }
        peak = element_peak_months.get(use_god_element, "")
        timing_methods.append({
            "method": "待旺时",
            "description": _YD["peak_month"].format(use_god_branch=use_god_branch, peak=peak),
            "type": "迟应",
        })
        timing_methods.append({
            "method": "逢生",
            "description": (_YD["yuan_peak"].format(pd0=pd[0] if pd else "", pd1=pd[1] if len(pd)>1 else "") if pd else _YD["yuan_peak_short"]),
            "type": "迟应",
        })
    else:
        if use_god_branch:
            timing_methods.append({
                "method": "中和取用",
                "description": _YD["neutral"].format(use_god_branch=use_god_branch),
                "type": "适中",
            })

    if is_empty:
        timing_methods.append({
            "method": "出空",
            "description": _YD["out_void"].format(use_god_branch=use_god_branch),
            "type": "空亡应期",
        })
        # 常见出空应期支：待用神值日或填实之支
        if use_god_branch:
            _push(use_god_branch)
        for e in (r.get("empty_branches") or []):
            _push(e)
        _add_kw = True

    if is_month_break:
        timing_methods.append({
            "method": "填实",
            "description": _YD["month_break"].format(use_god_branch=use_god_branch),
            "type": "填实应期",
        })

    step4_data = safe_get(r, "_step4_data", default={}) or {}
    if step4_data.get("tan_he_wan_sheng_ke"):
        timing_methods.append({
            "method": "冲合",
            "description": _YD["he_clash"],
            "type": "化合应期",
        })
        if day_branch:
            _push(_chong(day_branch))

    # 暗动：应在冲动之日
    if (step3_data.get("an_dong_modifier") or 1.0) < 1.0 and day_branch:
        timing_methods.append({
            "method": "暗动应期",
            "description": _YD["an_dong"].format(day_branch=day_branch),
            "type": "暗动",
        })

    # 伏藏：飞神冲去或伏神值日
    if step2_d.get("has_fu_cang") or step2_d.get("fu_cang_detail"):
        timing_methods.append({
            "method": "伏神应期",
            "description": _YD["fu_hidden"],
            "type": "伏藏应期",
        })

    if strength_level in ("极旺", "旺"):
        speed = "应速"
    elif strength_level in ("中和",):
        speed = "应期适中"
    else:
        speed = "应迟"

    # ── 应期择优：按用神状态取"解除障碍之期"为主，其余降为备选 ────────────
    # 旧实现把动爻、变爻、用神之冲与合、原神四支、伏神、飞神、旬空、日月全部并集
    # 塞进 key_branches，平均 11.1/12 个地支——召回率看着 100%，与瞎蒙无异
    # （随机列同样多候选即全覆盖的期望是 92.6%）。改为法则驱动的主/次应期。
    candidates_all = list(key_branches)          # 长列表保留作备查，不再充当"重点"
    ranked: list[tuple[str, str]] = []

    def _rank(b: str, rule: str, suffix: str = "日"):
        if not b or b not in BRANCH_ORDER:
            return
        token = f"{b}{suffix}"
        if token not in [t for t, _ in ranked]:
            ranked.append((token, rule))

    ug_moving = any(isinstance(y, dict) and y.get("earthly_branch") == use_god_branch
                    and y.get("is_moving") for y in yao_lines)
    changed_pairs = [(y.get("earthly_branch") or "",
                      y.get("changed_earthly_branch") or y.get("changed_branch") or "")
                     for y in yao_lines
                     if isinstance(y, dict) and y.get("is_moving")]
    changed_pairs = [(b, c) for b, c in changed_pairs if c]
    # 动而化回头生：古籍以"生我之日"为应，且此则先于旬空——动爻得生则不作空论
    hui_tou_sheng = [c for b, c in changed_pairs
                     if SHENG_CYCLE.get(BRANCH_ELEMENTS.get(c, "")) == use_god_element]
    fu_detail = step2_d.get("fu_cang_detail") or {}
    fu_res = (fu_detail.get("results") or [{}])[0] if isinstance(fu_detail, dict) else {}
    fu_branch = ((fu_res.get("fu_shen") or {}).get("branch")) or ""
    fei_branch = ((fu_res.get("fei_shen") or {}).get("branch")) or ""
    tomb_branch = TOMB_MAP.get(use_god_element or "", "")
    bound_by = day_branch if _he(use_god_branch) == day_branch else \
               (month_branch if _he(use_god_branch) == month_branch else "")
    PEAK_BRANCH = {"木": "寅", "火": "巳", "土": "辰", "金": "申", "水": "亥"}

    # ── 病药解除优先（《增删卜易》空则实之、破则补之、墓则冲之）──
    # 古例规律（tune 实测）：
    #   · 用神旬空而日辰已冲 → 当日冲空填实即应（ZS001）
    #   · 化出之支逢空 → 出空值日为应（ZS007/013）
    #   · 飞神旬空、伏神得出 → 伏神值日为应（ZS016）
    #   · 空亡支与用神同五行 → 亦作出空应期（ZS006/010）
    _empty_list = list(r.get("empty_branches") or [])
    _chong_ug = _chong(use_god_branch)
    _q_txt = str(r.get("question") or "") + str(r.get("topic") or "")
    _is_illness_q = any(k in _q_txt for k in ("病", "疾", "愈", "医"))
    _is_chronic = any(k in _q_txt for k in ("久病", "沉疴", "久疾", "半年"))
    _chg0 = changed_pairs[0][1] if changed_pairs else ""
    # 化空 / 回头生优先；动而化回头生则不作空论（ZS005/007/013）
    # 注意：非空卦的回头生不前插（ZS009 化绝+回头生仍应逢值）
    for _b, _c in changed_pairs:
        if _c and _c in _empty_list:
            _rank(_c, YINGQI_TXT["change_branch_empty_fill"]["text"])
    if hui_tou_sheng and is_empty:
        _rank(hui_tou_sheng[0], YINGQI_TXT["change_hui_tou_sheng_empty"]["text"])
    elif hui_tou_sheng:
        pass  # 后面统一排
    if is_empty and not hui_tou_sheng:
        if day_branch and day_branch == _chong_ug:
            _rank(day_branch, YINGQI_TXT["use_empty_day_chong"]["text"])
        elif _is_chronic and _chong_ug:
            # 久病逢空多应冲空之日（《增删卜易》久病之忌）
            _rank(_chong_ug, YINGQI_TXT["chronic_empty_wait_chong"]["text"])
            _rank(use_god_branch, "出旬填实")
        elif _is_illness_q:
            # 近病逢空即愈：出空填实为应
            _rank(use_god_branch, YINGQI_TXT["acute_empty_fill"]["text"])
            _rank(_chong_ug or use_god_branch, "冲空则实")
        else:
            _rank(use_god_branch, YINGQI_TXT["empty_fill"]["text"])
            _rank(_chong_ug or use_god_branch, YINGQI_TXT["empty_chong_real"]["text"])
    if is_month_break:
        _rank(use_god_branch, YINGQI_TXT["month_break_fill"]["text"])
        _rank(_he(use_god_branch), YINGQI_TXT["month_break_he"]["text"])
    # 病药结构化码不进应期主排序：holdout 实测会挤掉正确日支（见 CHANGELOG 2026-09-26g）。
    # 药码仅在 score 层有界加减；解除障碍之期仍由空/破/伏/化出既有通则覆盖。
    # 化空出空 / 回头生：先于合住冲开与伏藏（ZS005/007/013）
    if step2_d.get("has_fu_cang") and (fu_branch or fei_branch):
        fei_empty = fei_branch in _empty_list if fei_branch else False
        _fu_txt = str(step2_d.get("fu_cang_detail") or "") + str(step2_d.get("fu_cang_summary") or "")
        _fei_ke_fu = any(k in _fu_txt for k in ("飞克伏", "飞神克"))
        _fu_sheng_fei = any(k in _fu_txt for k in ("伏生飞", "伏神生"))
        if _fei_ke_fu and fei_branch:
            _rank(_chong(fei_branch) or fu_branch, YINGQI_TXT["fu_fei_ke_chong_fei"]["text"])
            if fu_branch:
                _rank(fu_branch, "伏神值日")
        elif fei_empty and fu_branch:
            _rank(fu_branch, YINGQI_TXT["fu_fei_empty_wait_fu_day"]["text"])
        elif fu_branch:
            _rank(fu_branch, YINGQI_TXT["fu_out_wait_fu_day"]["text"])
            if fei_branch and _fu_sheng_fei:
                _rank(_chong(fei_branch) or fei_branch, YINGQI_TXT["fu_sheng_fei_chong"]["text"])
            elif fei_branch:
                _rank(_chong(fei_branch) or fu_branch, "冲飞神得出")
        if fu_branch and fu_branch != use_god_branch:
            _rank(fu_branch, "伏神值日")
    if tomb_branch and tomb_branch in (day_branch, month_branch):
        _rank(_chong(tomb_branch), YINGQI_TXT["use_tomb_chong_tomb"]["text"])
    if bound_by:
        _rank(_chong(bound_by), f"用神被{bound_by}合住，冲开之日")
    # 用神不空时，本气值日优先于其他空亡出空
    if use_god_branch and not is_empty:
        if ug_moving:
            _rank(use_god_branch, "发动值日")
            _rank(_he(use_god_branch), YINGQI_TXT["use_moving_he_day"]["text"])
        else:
            _rank(use_god_branch, "用神值日")
            _rank(_chong_ug, YINGQI_TXT["use_quiet_chong_day"]["text"])
    # 其余化出之支
    if changed_pairs and _chg0 and _chg0 not in _empty_list and not hui_tou_sheng:
        _rank(_chg0, "化出之支值日")
    # 同五行之空亡支
    ug_el = use_god_element or ""
    for e in _empty_list:
        if e and e != use_god_branch and ug_el and BRANCH_ELEMENTS.get(e) == ug_el:
            _rank(e, YINGQI_TXT["empty_same_element_fill"]["text"])
    for e in _empty_list:
        if e and e != use_god_branch:
            _rank(e, "空亡之支出空填实")
    if use_god_branch and is_empty:
        _rank(use_god_branch, "以用神为主")
    if strength_level in ("休囚", "囚", "死", "偏弱", "衰") or speed == "应迟":
        _rank(PEAK_BRANCH.get(use_god_element or "", ""), YINGQI_TXT["use_weak_wait_prosper"]["text"])
    _rank(use_god_branch, "以用神为主")
    _rank(day_branch, "日辰值事")

    # 月级阶梯：《增刪卜易》「遠則應月﹐近則應日」（norm@79289）——同一套"解除障碍之期"
    # 在月单位上另排一遍。旧实现把月级候选与日级候选挤在同一个 5 支窗口里，
    # 结果是月级答案占掉日级名额、日级答案又盖住月级，两个单位互相饿死
    # （HANDOFF 四·7 记的那次三集全降即由此）。分列后各单位各自有序、各自封顶。
    peak = PEAK_BRANCH.get(use_god_element or "", "")
    if is_empty:
        _rank(use_god_branch, YINGQI_TXT["use_empty_fill_month"]["text"], "月")
        _rank(_chong(use_god_branch) or use_god_branch, YINGQI_TXT["use_empty_chong_month"]["text"], "月")
    if is_month_break:
        _rank(use_god_branch, YINGQI_TXT["month_break_real_month"]["text"], "月")
    if tomb_branch and tomb_branch in (day_branch, month_branch):
        _rank(_chong(tomb_branch), YINGQI_TXT["use_tomb_chong_month"]["text"], "月")
    if bound_by:
        _rank(_chong(bound_by), f"用神被{bound_by}合住，冲开之月", "月")
    if step2_d.get("has_fu_cang") and (fu_branch or fei_branch):
        _rank(_chong(fei_branch) or fu_branch, YINGQI_TXT["fu_hidden_chong_fei_month"]["text"], "月")
    if use_god_branch:
        if ug_moving:
            _rank(_he(use_god_branch), YINGQI_TXT["use_moving_he_month"]["text"], "月")
        else:
            _rank(_chong(use_god_branch), YINGQI_TXT["use_quiet_chong_month"]["text"], "月")
        _rank(use_god_branch, "用神值月", "月")
    if strength_level in ("休囚", "囚", "死", "偏弱", "衰") or speed == "应迟":
        _rank(peak, YINGQI_TXT["use_weak_prosper_month"]["text"], "月")
    _rank(use_god_branch, "以用神为主", "月")

    # 分级预算：单位不同不可同窗排序，否则加一个"生旺之月"就把正确的日支挤出窗口。
    UNIT_BUDGET = (("日", 5), ("月", 3), ("年", 2))
    by_unit = {u: [] for u, _ in UNIT_BUDGET}
    for token, rule in ranked:
        unit = token[-1]
        if unit in by_unit and len(by_unit[unit]) < dict(UNIT_BUDGET)[unit]:
            by_unit[unit].append((token, rule))
    yingqi_days = [t for t, _ in by_unit["日"]]
    yingqi_months = [t for t, _ in by_unit["月"]]
    yingqi_years = [t for t, _ in by_unit["年"]]
    ranked_top = by_unit["日"] or ranked

    key_branches = yingqi_days
    timing_rules = [{"token": t, "rule": r, "unit": t[-1]} for t, r in ranked]

    key_text = "、".join(key_branches) if key_branches else YINGQI_TXT["wait_strength"]["text"]
    main_text = f"{ranked_top[0][0]}（{ranked_top[0][1]}）" if ranked_top else "—"
    month_text = "、".join(yingqi_months) if yingqi_months else ""
    year_text = "、".join(yingqi_years) if yingqi_years else ""
    detail = ("、".join(t["description"] for t in timing_methods)
              if timing_methods else YINGQI_TXT["hard_to_single_yingqi"]["text"])

    sp_blob = ""
    if isinstance(special_pattern, dict):
        sp_blob = str(special_pattern.get("pattern") or "") + str(special_pattern.get("description") or "")
    elif special_pattern:
        sp_blob = str(special_pattern)
    if any(k in sp_blob for k in ("近病逢空", "近病逢合", "近病")):
        speed = "应速"
    if any("合" in str(t.get("method") or "") or "合" in str(t.get("description") or "") for t in timing_methods):
        speed_plain_extra = YINGQI_TXT["he_wait_chong"]["text"]
    else:
        speed_plain_extra = ""
    speed_plain = {
        "应速": YINGQI_TXT["speed_fast"]["text"],
        "应期适中": YINGQI_TXT["speed_medium"]["text"],
        "应迟": YINGQI_TXT["speed_slow"]["text"],
    }.get(speed, speed)
    sp_text = sp_blob
    if step4_data.get("tan_he_wan_sheng_ke") or "合处逢冲" in sp_text or "冲中逢合" in sp_text:
        speed_plain += YINGQI_TXT["repeat_uneasy"]["text"]

    summary_text = (f"重点应期：{key_text}。主应期 {main_text}。{speed_plain}。{speed_plain_extra}"
                    + (f"若事应迟，则看月级：{month_text}。" if month_text else "")
                    + (f"久案应于年：{year_text}。" if year_text else "")
                    + (f"依据：{detail}。" if detail else ""))
    timing_reasons.append(summary_text)

    return {
        "timing_methods": timing_methods,
        "timing_rules": timing_rules,
        "speed": speed,
        "key_branches": key_branches,
        "yingqi_days": yingqi_days,
        "yingqi_months": yingqi_months,
        "yingqi_years": yingqi_years,
        "candidates_all": candidates_all,
        "summary_text": summary_text,
        "plain_text": (f"事情应验的时间，主看{main_text}，备选{'、'.join(key_branches[1:]) or '无'}。"
                       + (f"若拖得久，月级看{month_text}。" if month_text else "")
                       + f"{speed_plain}。"),
    }

