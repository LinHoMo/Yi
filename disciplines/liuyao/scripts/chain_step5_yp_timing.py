# -*- coding: utf-8 -*-
"""六爻思维链 step5 应期：_predict_timing 巨石按职责切出。

纯搬移不改逻辑：原 491 行巨石拆成「收集候选支 / 组装法则应期方法 / 应期择优排序 /
组装输出」四段，外加 5 个从原闭包提升的纯辅助（pair/chong/he/push/rank）。

本模块**不 import chain_step5_yp / chain_step5 / thinking_chain**，依赖单向：
chain_step5_yp → chain_step5_yp_timing（再导出入口见 chain_step5_yp.py）。

验收口径：拆分前后 step5 应期输出与下游叙述必须逐例一致（零指纹漂移）。
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
    HE_PAIRS,
    SHENG_CYCLE,
    TOMB_MAP,
)
from chain_support import safe_get  # noqa: E402
from chain_verdicts import STEP5_YINGQI as YINGQI_TXT  # noqa: E402

import json as _json  # noqa: E402
from pathlib import Path as _P  # noqa: E402
_YD = _json.loads((_P(__file__).resolve().parents[1] / 'data' / 'narrative_templates.json').read_text(encoding='utf-8')).get('yingqi_descriptions', {})

# 原闭包内本地常量；提升为模块常量供 _push / _rank 复用。
BRANCH_ORDER = "子丑寅卯辰巳午未申酉戌亥"


# ────────────────────────────────────────────────────────────────
# 原闭包内 5 个辅助：提升为模块级纯函数（不再捕获外层作用域）。
# ────────────────────────────────────────────────────────────────

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


def _push(key_branches: list, b: str, suffix: str = "日") -> None:
    if not b or b not in BRANCH_ORDER:
        return
    token = f"{b}{suffix}"
    if token not in key_branches:
        key_branches.append(token)


def _rank(ranked: list, b: str, rule: str, suffix: str = "日") -> None:
    if not b or b not in BRANCH_ORDER:
        return
    token = f"{b}{suffix}"
    if token not in [t for t, _ in ranked]:
        ranked.append((token, rule))


# ────────────────────────────────────────────────────────────────
# 职责一：收集候选地支（原 103–247 收集段）
# ────────────────────────────────────────────────────────────────

def _collect_key_branches(r: dict, use_god_branch: str, day_branch: str):
    """遍历卦爻/日月/用神/伏神/旬空，按规则把应期候选支推入 key_branches。

    返回 (key_branches, month_branch, step2_d, pd)：
      - key_branches 是会被下游「法则应期」段继续追加的可变列表；
      - month_branch / step2_d / pd 是收集段顺手算出的派生量，下游排序与组装都要用。
    """
    key_branches: list[str] = []

    # 收集卦中地支
    yao_lines = ((r.get("original_hexagram") or {}).get("yao_lines")) or []
    for y in yao_lines:
        if not isinstance(y, dict):
            continue
        br = y.get("earthly_branch") or ""
        if y.get("is_moving"):
            _push(key_branches, br)
            chg = y.get("changed_earthly_branch") or y.get("changed_branch") or ""
            if not chg:
                # 尝试从 changed_hexagram 对应位取
                pass
            if chg:
                _push(key_branches, chg)
        if y.get("six_relation") and use_god_branch and br == use_god_branch:
            _push(key_branches, br)

    # 变卦地支
    ch_hex = r.get("changed_hexagram") or {}
    for y in (ch_hex.get("yao_lines") or []):
        if isinstance(y, dict) and y.get("is_moving"):
            _push(key_branches, y.get("earthly_branch") or "")
        # 动爻变出支通常在 original 的 moving 标记里，双保险
        if isinstance(y, dict) and y.get("changed_earthly_branch"):
            _push(key_branches, y.get("changed_earthly_branch"))

    # 原始动爻若带 changed_branch 字段
    for y in yao_lines:
        if isinstance(y, dict):
            for k in ("changed_earthly_branch", "changed_branch", "transform_branch"):
                if y.get(k):
                    _push(key_branches, y.get(k))

    # 日月
    if day_branch:
        _push(key_branches, day_branch)
    month_branch = ""
    mdt = r.get("divination_time") or {}
    if isinstance(mdt, dict):
        msb = mdt.get("month_stem_branch") or mdt.get("month_branch") or ""
        month_branch = msb[-1] if msb else ""
        if month_branch:
            _push(key_branches, month_branch, "月")

    # 用神及其冲合
    if use_god_branch:
        _push(key_branches, use_god_branch)
        _push(key_branches, _chong(use_god_branch))
        _push(key_branches, _he(use_god_branch))

    # 原神旺日
    step2_d = safe_get(r, "_step2_data", default={}) or {}
    yuan_elem = (step2_d.get("yuan_shen") or {}).get("element", "")
    peak_days = {"木": "寅卯", "火": "巳午", "土": "辰戌丑未", "金": "申酉", "水": "亥子"}
    pd = peak_days.get(yuan_elem, "")
    for ch in pd:
        _push(key_branches, ch)
    for pos in ((step2_d.get("yuan_shen") or {}).get("positions") or []):
        if isinstance(pos, dict):
            _push(key_branches, pos.get("earthly_branch") or "")

    # 伏神地支
    fu = step2_d.get("fu_cang_detail") or {}
    if isinstance(fu, dict):
        for res in fu.get("results") or []:
            if isinstance(res, dict):
                _push(key_branches, ((res.get("fu_shen") or {}).get("branch")) or "")
                _push(key_branches, ((res.get("fei_shen") or {}).get("branch")) or "")

    # 旬空地支（出空应期）
    for e in (r.get("empty_branches") or []):
        _push(key_branches, e)

    # 合局/贪合 → 冲开之支（冲开合局方应）
    # （原 step4_all 本地变量已废弃：从未被读取，删除不影响任何输出）
    # 冲用神、合用神之支
    if use_god_branch:
        _push(key_branches, _chong(use_god_branch))
        _push(key_branches, _he(use_god_branch))
    # 卦中地支：动爻候合、静爻候冲；并冲开六合之支
    he_branches = []
    for y in yao_lines:
        if not isinstance(y, dict):
            continue
        br = y.get("earthly_branch") or ""
        if not br:
            continue
        if y.get("is_moving"):
            _push(key_branches, _he(br))
            _push(key_branches, _chong(br))
        else:
            _push(key_branches, _chong(br))
        for a, b in HE_PAIRS:
            if br == a:
                he_branches.append(b)
            elif br == b:
                he_branches.append(a)
    for hb in he_branches:
        _push(key_branches, _chong(hb))  # 冲开合局
        _push(key_branches, hb)
    # 日月与卦爻成合：冲开该合
    if day_branch:
        for a, b in HE_PAIRS:
            if day_branch == a:
                _push(key_branches, _chong(b)); _push(key_branches, b)
            elif day_branch == b:
                _push(key_branches, _chong(a)); _push(key_branches, a)
    if month_branch:
        for a, b in HE_PAIRS:
            if month_branch == a:
                _push(key_branches, _chong(b)); _push(key_branches, b)
            elif month_branch == b:
                _push(key_branches, _chong(a)); _push(key_branches, a)
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
                _push(key_branches, fu_br)
            if fei_br:
                _push(key_branches, _chong(fei_br))
    # 用神临月建：该五行旺月/日
    if use_god_branch and month_branch:
        if use_god_branch == month_branch or (
            BRANCH_ELEMENTS.get(use_god_branch) == BRANCH_ELEMENTS.get(month_branch)
        ):
            elem = BRANCH_ELEMENTS.get(use_god_branch, "")
            peak = {"木": "寅卯", "火": "巳午", "土": "辰戌丑未", "金": "申酉", "水": "亥子"}.get(elem, "")
            for ch in peak:
                _push(key_branches, ch)
    # 原神旺月支
    if pd:
        for ch in pd:
            _push(key_branches, ch)
    # 世爻之冲（世应应期）
    for y in yao_lines:
        if isinstance(y, dict) and y.get("is_world"):
            _push(key_branches, _chong(y.get("earthly_branch") or ""))
            break

    return key_branches, month_branch, step2_d, pd


# ────────────────────────────────────────────────────────────────
# 职责二：组装「法则应期」方法与速迟基调（原 249–342 段）
# ────────────────────────────────────────────────────────────────

def _build_timing_methods(r: dict, step3_data: dict, use_god_branch: str, use_god_element: str,
                          strength_level: str, is_empty, is_month_break,
                          day_branch: str, step2_d: dict, step4_data: dict,
                          key_branches: list, pd: str):
    """按旺衰/空亡/月破/暗动/伏藏等通则生成 timing_methods，并定 speed 基调。

    注意：本段仍会向 key_branches 追加支（逢冲之支、空亡支、贪合冲日支），
    须在执行完本段之后、排序之前再对 key_branches 做 candidates_all 快照。
    """
    timing_methods = []

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
            _push(key_branches, cb)
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
            "description": (_YD["yuan_peak"].format(pd0=pd[0] if pd else "", pd1=pd[1] if len(pd) > 1 else "") if pd else _YD["yuan_peak_short"]),
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
            _push(key_branches, use_god_branch)
        for e in (r.get("empty_branches") or []):
            _push(key_branches, e)

    if is_month_break:
        timing_methods.append({
            "method": "填实",
            "description": _YD["month_break"].format(use_god_branch=use_god_branch),
            "type": "填实应期",
        })

    if step4_data.get("tan_he_wan_sheng_ke"):
        timing_methods.append({
            "method": "冲合",
            "description": _YD["he_clash"],
            "type": "化合应期",
        })
        if day_branch:
            _push(key_branches, _chong(day_branch))

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

    return timing_methods, speed


# ────────────────────────────────────────────────────────────────
# 职责三：应期择优排序（原 344–491 段）
# ────────────────────────────────────────────────────────────────

def _rank_candidates(r: dict, use_god_branch: str, use_god_element: str, strength_level: str,
                     is_empty, is_month_break, day_branch: str, month_branch: str,
                     step2_d: dict, speed: str) -> list:
    """法则驱动的主/次应期排序：日/月/年分列、各自封顶（避免单位互相饿死）。"""
    ranked: list[tuple[str, str]] = []

    yao_lines = ((r.get("original_hexagram") or {}).get("yao_lines")) or []
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
            _rank(ranked, _c, YINGQI_TXT["change_branch_empty_fill"]["text"])
    if hui_tou_sheng and is_empty:
        _rank(ranked, hui_tou_sheng[0], YINGQI_TXT["change_hui_tou_sheng_empty"]["text"])
    elif hui_tou_sheng:
        pass  # 后面统一排
    if is_empty and not hui_tou_sheng:
        if day_branch and day_branch == _chong_ug:
            _rank(ranked, day_branch, YINGQI_TXT["use_empty_day_chong"]["text"])
        elif _is_chronic and _chong_ug:
            # 久病逢空多应冲空之日（《增删卜易》久病之忌）
            _rank(ranked, _chong_ug, YINGQI_TXT["chronic_empty_wait_chong"]["text"])
            _rank(ranked, use_god_branch, "出旬填实")
        elif _is_illness_q:
            # 近病逢空即愈：出空填实为应
            _rank(ranked, use_god_branch, YINGQI_TXT["acute_empty_fill"]["text"])
            _rank(ranked, _chong_ug or use_god_branch, "冲空则实")
        else:
            _rank(ranked, use_god_branch, YINGQI_TXT["empty_fill"]["text"])
            _rank(ranked, _chong_ug or use_god_branch, YINGQI_TXT["empty_chong_real"]["text"])
    if is_month_break:
        _rank(ranked, use_god_branch, YINGQI_TXT["month_break_fill"]["text"])
        _rank(ranked, _he(use_god_branch), YINGQI_TXT["month_break_he"]["text"])
    # 病药结构化码不进应期主排序：holdout 实测会挤掉正确日支（见 CHANGELOG 2026-09-26g）。
    # 药码仅在 score 层有界加减；解除障碍之期仍由空/破/伏/化出既有通则覆盖。
    # 化空出空 / 回头生：先于合住冲开与伏藏（ZS005/007/013）
    if step2_d.get("has_fu_cang") and (fu_branch or fei_branch):
        fei_empty = fei_branch in _empty_list if fei_branch else False
        _fu_txt = str(step2_d.get("fu_cang_detail") or "") + str(step2_d.get("fu_cang_summary") or "")
        _fei_ke_fu = any(k in _fu_txt for k in ("飞克伏", "飞神克"))
        _fu_sheng_fei = any(k in _fu_txt for k in ("伏生飞", "伏神生"))
        if _fei_ke_fu and fei_branch:
            _rank(ranked, _chong(fei_branch) or fu_branch, YINGQI_TXT["fu_fei_ke_chong_fei"]["text"])
            if fu_branch:
                _rank(ranked, fu_branch, "伏神值日")
        elif fei_empty and fu_branch:
            _rank(ranked, fu_branch, YINGQI_TXT["fu_fei_empty_wait_fu_day"]["text"])
        elif fu_branch:
            _rank(ranked, fu_branch, YINGQI_TXT["fu_out_wait_fu_day"]["text"])
            if fei_branch and _fu_sheng_fei:
                _rank(ranked, _chong(fei_branch) or fei_branch, YINGQI_TXT["fu_sheng_fei_chong"]["text"])
            elif fei_branch:
                _rank(ranked, _chong(fei_branch) or fu_branch, "冲飞神得出")
        if fu_branch and fu_branch != use_god_branch:
            _rank(ranked, fu_branch, "伏神值日")
    if tomb_branch and tomb_branch in (day_branch, month_branch):
        _rank(ranked, _chong(tomb_branch), YINGQI_TXT["use_tomb_chong_tomb"]["text"])
    if bound_by:
        _rank(ranked, _chong(bound_by), f"用神被{bound_by}合住，冲开之日")
    # 用神不空时，本气值日优先于其他空亡出空
    if use_god_branch and not is_empty:
        if ug_moving:
            _rank(ranked, use_god_branch, "发动值日")
            _rank(ranked, _he(use_god_branch), YINGQI_TXT["use_moving_he_day"]["text"])
        else:
            _rank(ranked, use_god_branch, "用神值日")
            _rank(ranked, _chong_ug, YINGQI_TXT["use_quiet_chong_day"]["text"])
    # 其余化出之支
    if changed_pairs and _chg0 and _chg0 not in _empty_list and not hui_tou_sheng:
        _rank(ranked, _chg0, "化出之支值日")
    # 同五行之空亡支
    ug_el = use_god_element or ""
    for e in _empty_list:
        if e and e != use_god_branch and ug_el and BRANCH_ELEMENTS.get(e) == ug_el:
            _rank(ranked, e, YINGQI_TXT["empty_same_element_fill"]["text"])
    for e in _empty_list:
        if e and e != use_god_branch:
            _rank(ranked, e, "空亡之支出空填实")
    if use_god_branch and is_empty:
        _rank(ranked, use_god_branch, "以用神为主")
    if strength_level in ("休囚", "囚", "死", "偏弱", "衰") or speed == "应迟":
        _rank(ranked, PEAK_BRANCH.get(use_god_element or "", ""), YINGQI_TXT["use_weak_wait_prosper"]["text"])
    _rank(ranked, use_god_branch, "以用神为主")
    _rank(ranked, day_branch, "日辰值事")

    # 月级阶梯：《增刪卜易》「遠則應月﹐近則應日」（norm@79289）——同一套"解除障碍之期"
    # 在月单位上另排一遍。旧实现把月级候选与日级候选挤在同一个 5 支窗口里，
    # 结果是月级答案占掉日级名额、日级答案又盖住月级，两个单位互相饿死
    # （HANDOFF 四·7 记的那次三集全降即由此）。分列后各单位各自有序、各自封顶。
    peak = PEAK_BRANCH.get(use_god_element or "", "")
    if is_empty:
        _rank(ranked, use_god_branch, YINGQI_TXT["use_empty_fill_month"]["text"], "月")
        _rank(ranked, _chong(use_god_branch) or use_god_branch, YINGQI_TXT["use_empty_chong_month"]["text"], "月")
    if is_month_break:
        _rank(ranked, use_god_branch, YINGQI_TXT["month_break_real_month"]["text"], "月")
    if tomb_branch and tomb_branch in (day_branch, month_branch):
        _rank(ranked, _chong(tomb_branch), YINGQI_TXT["use_tomb_chong_month"]["text"], "月")
    if bound_by:
        _rank(ranked, _chong(bound_by), f"用神被{bound_by}合住，冲开之月", "月")
    if step2_d.get("has_fu_cang") and (fu_branch or fei_branch):
        _rank(ranked, _chong(fei_branch) or fu_branch, YINGQI_TXT["fu_hidden_chong_fei_month"]["text"], "月")
    if use_god_branch:
        if ug_moving:
            _rank(ranked, _he(use_god_branch), YINGQI_TXT["use_moving_he_month"]["text"], "月")
        else:
            _rank(ranked, _chong(use_god_branch), YINGQI_TXT["use_quiet_chong_month"]["text"], "月")
        _rank(ranked, use_god_branch, "用神值月", "月")
    if strength_level in ("休囚", "囚", "死", "偏弱", "衰") or speed == "应迟":
        _rank(ranked, peak, YINGQI_TXT["use_weak_prosper_month"]["text"], "月")
    _rank(ranked, use_god_branch, "以用神为主", "月")

    return ranked


# ────────────────────────────────────────────────────────────────
# 职责四：分级预算 + 组装输出（原 493–554 段）
# ────────────────────────────────────────────────────────────────

def _assemble_timing(ranked: list, timing_methods: list, speed: str,
                     special_pattern, step4_data: dict, use_god_branch: str,
                     candidates_all: list) -> dict:
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
    timing_reasons = [summary_text]  # 原实现保留该本地列表（不进返回字典）

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


# ────────────────────────────────────────────────────────────────
# 编排入口（原 _predict_timing 巨石本体，签名不变以兼容再导出）
# ────────────────────────────────────────────────────────────────

def predict_timing_core(r: dict, step3_data: dict, step1_data: dict, day_branch: str, special_pattern=None) -> dict:
    """
    应期判断 — v8：前置「重点应期」地支词，兼顾古籍规则与人话可读性。
    （原 491 行巨石已按职责切分为 _collect_key_branches / _build_timing_methods /
    _rank_candidates / _assemble_timing，见本模块。）
    """
    use_god_branch = safe_get(step3_data, "use_god_branch", default="") or ""
    use_god_element = safe_get(step3_data, "use_god_element", default="")
    strength_level = safe_get(step3_data, "strength_level", default="中和")
    is_empty = safe_get(step3_data, "is_empty", default=False)
    is_month_break = safe_get(step3_data, "is_month_break", default=False)

    step4_data = safe_get(r, "_step4_data", default={}) or {}

    key_branches, month_branch, step2_d, pd = _collect_key_branches(r, use_god_branch, day_branch)
    timing_methods, speed = _build_timing_methods(
        r, step3_data, use_god_branch, use_god_element, strength_level,
        is_empty, is_month_break, day_branch, step2_d, step4_data, key_branches, pd)
    # candidates_all 必须在「法则应期」段追加支之后、排序之前快照
    candidates_all = list(key_branches)
    ranked = _rank_candidates(
        r, use_god_branch, use_god_element, strength_level, is_empty,
        is_month_break, day_branch, month_branch, step2_d, speed)
    return _assemble_timing(
        ranked, timing_methods, speed, special_pattern, step4_data,
        use_god_branch, candidates_all)
