# -*- coding: utf-8 -*-
"""step5 应期计算模块（T31 第二步：从 step5.py 提取 calculate_yingqi）。"""
from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现
_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))
if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)
# D3 收编：同目录兄弟 step* 由 _ks_d 覆盖，scripts/ 兄弟由 _ks_parent 覆盖
_ks_parent = _ks_os.path.dirname(_ks_os.path.dirname(_ks_d))
_ks_grandparent = _ks_os.path.dirname(_ks_parent)
if _ks_parent not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_parent)
if _ks_grandparent not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_grandparent)
from kernel_path import ensure_kernel_on_path as _ks_ensure
_ks_ensure(__file__)

from datetime import datetime, timedelta

from util import safe_get
from chain_tables import (
    _BRANCH_CLASH_MAP,
    _ELEMENT_PEAK_MONTHS,
    _HE_MAP,
    SAN_HE,
)
from chain_verdicts import STEP5_YINGQI as YINGQI_TXT
from _step5_dates import (
    _day_branch_for_date,
    _dates_overlap,
    _next_date_with_day_branch,
)


def calculate_yingqi(
    step1: dict,
    step2: dict,
    step3: dict,
    step4: dict,
    step5: dict,
    base_date: datetime | None = None,
    ladder: list | None = None,
) -> dict:
    """应期精确计算（《增删卜易》《黄金策》）：{日期+规则列表, speed, summary_text}。

    `ladder` 是 `timing._rank_candidates` 排好的日级阶梯 [(token, rule), ...]。
    接它的原因不是补功能，而是**消除同一次占断里的两个答案**：阶梯把戌日排为主应期，
    而下面的日期投影此前只按"最早五个日期"出列，报告读的是日期层（narrate 应期段
    「优先从 yingqi_dates 读」），于是阶梯上所有排序在产出面被丢掉。现行接线
    （第七十九批＋第一百六十批）：日历层 5 槽按七条规则时间序取，阶梯未覆盖名次
    最多追加 2 条；随后**逐出改首条**——阶梯第 1 名（主应期）置首（不在槽内则挤掉
    原第 5 槽），报告首条自此恒等于阶梯主应期。
    """
    use_god_branch = safe_get(step3, "use_god_branch", default="")
    use_god_element = safe_get(step3, "use_god_element", default="")
    strength_level = safe_get(step3, "strength_level", default="中和")
    is_empty = safe_get(step3, "is_empty", default=False)
    is_month_break = safe_get(step3, "is_month_break", default=False)
    is_an_dong = safe_get(step3, "is_an_dong", default=False)

    vacant = safe_get(step1, "vacant_branches", default=[])
    if isinstance(vacant, str):
        vacant = [vacant]
    fu_cang_detail = safe_get(step2, "fu_cang_detail", default=None)
    has_fu_cang = safe_get(step2, "has_fu_cang", default=False)

    # 原神 info
    yuan_shen_element = safe_get(step2, "yuan_shen", "element", default="")
    yuan_shen_positions = safe_get(step2, "yuan_shen", "positions", default=[])
    yuan_shen_fu_cang = safe_get(step2, "yuan_shen", "fu_cang", default=None)

    # base_date defaults to today
    base = base_date if base_date else datetime.now()

    # Collect all 应期: list of (rule_str, date_or_None, branch, description_parts)
    candidates: list[tuple[str, datetime | None, str, str]] = []

    clash = _BRANCH_CLASH_MAP.get(use_god_branch, "")

    # ===== Rule 1: 逢值逢冲 =====
    if use_god_branch:
        val_date = _next_date_with_day_branch(base, use_god_branch)
        if val_date:
            candidates.append(("逢值", val_date, use_god_branch,
                               f"用神{use_god_branch}临值"))
        if clash:
            clash_date = _next_date_with_day_branch(base, clash)
            if clash_date:
                candidates.append(("逢冲", clash_date, clash,
                                   f"用神{use_god_branch}逢冲({clash})"))

    # ===== Rule 2: 原神受克时 → 原神旺时 / 忌神受制时 =====
    if yuan_shen_positions or yuan_shen_fu_cang:
        yuan_branches: list[str] = []
        for yp in (yuan_shen_positions or []):
            yb = yp.get("earthly_branch", "")
            if yb:
                yuan_branches.append(yb)
        if yuan_shen_fu_cang:
            yfb = yuan_shen_fu_cang.get("branch", "")
            if yfb:
                yuan_branches.append(yfb)

        for yb in yuan_branches:
            ys_val = _next_date_with_day_branch(base, yb)
            if ys_val:
                candidates.append(("原神值日", ys_val, yb,
                                   f"原神{yb}当值"))

    # ===== Rule 3: 旬空 → 填实 / 冲空 =====
    if is_empty and use_god_branch:
        fill_date = _next_date_with_day_branch(base, use_god_branch)
        if fill_date:
            candidates.append(("填实(实空)", fill_date, use_god_branch,
                               f"用神{use_god_branch}出空填实"))
        if clash:
            chong_date = _next_date_with_day_branch(base, clash)
            if chong_date:
                candidates.append(("冲空", chong_date, clash,
                                   f"用神{use_god_branch}冲空({clash})"))

    # ===== Rule 4: 伏藏 → 飞神值日 / 冲开 =====
    if has_fu_cang and fu_cang_detail:
        results = fu_cang_detail.get("results", [])
        for r in results:
            fei = r.get("fei_shen", {})
            fei_branch = fei.get("branch", "")
            if fei_branch:
                fei_val = _next_date_with_day_branch(base, fei_branch)
                if fei_val:
                    candidates.append(("飞神值日(伏得出)", fei_val, fei_branch,
                                       f"飞神{fei_branch}值日"))
                fei_clash = _BRANCH_CLASH_MAP.get(fei_branch, "")
                if fei_clash:
                    fei_chong = _next_date_with_day_branch(base, fei_clash)
                    if fei_chong:
                        candidates.append(("飞神冲开", fei_chong, fei_clash,
                                           f"冲飞神{fei_branch}→{fei_clash}"))

    # ===== Rule 5: 三合局 → 待合局成 =====
    if use_god_element and use_god_element in SAN_HE:
        san_he_branches = SAN_HE[use_god_element]
        for shb in san_he_branches:
            sh_date = _next_date_with_day_branch(base, shb)
            if sh_date:
                candidates.append(("三合成局", sh_date, shb,
                                   f"{'/'.join(san_he_branches)}合{use_god_element}局"))

    # ===== Rule 6: 月破 → 逢合/逢值/填实 =====
    if is_month_break and use_god_branch:
        # 逢值填实
        val_date = _next_date_with_day_branch(base, use_god_branch)
        if val_date:
            candidates.append(("月破填实", val_date, use_god_branch,
                               f"月破用神{use_god_branch}填实"))
        # 逢合（月破逢合为解）
        he_branches = _HE_MAP.get(use_god_branch, [])
        for heb in he_branches:
            he_date = _next_date_with_day_branch(base, heb)
            if he_date:
                candidates.append(("月破逢合", he_date, heb,
                                   f"月破用神{use_god_branch}逢合{heb}"))

    # ===== Rule 7: 节奏 timing =====
    # FAST: 用神旺 + 不动/暗动 → 当日或次日
    if strength_level in ("极旺", "旺") and not is_empty and not is_month_break:
        candidates.append(("速应(旺)", base + timedelta(days=0), _day_branch_for_date(base),
                           f"用神旺相，当日可能应"))
        candidates.append(("速应(次日)", base + timedelta(days=1), _day_branch_for_date(base + timedelta(days=1)),
                           YINGQI_TXT["use_alive_next_day"]["text"]))

    # MEDIUM: 用神动化进 → 逢值日（已由逢值规则覆盖）
    # SLOW: 用神休囚 + 静 → 原神旺月/旺日
    if strength_level in ("偏弱", "弱", "极弱"):
        if yuan_shen_element:
            for yb in [yp.get("earthly_branch", "") for yp in (yuan_shen_positions or [])]:
                if yb:
                    ys_date = _next_date_with_day_branch(base, yb)
                    if ys_date and not any(_dates_overlap(ys_date, c[1]) for c in candidates):
                        candidates.append(("原神旺日(迟应)", ys_date, yb,
                                           f"用神休囚，待原神{yb}旺日"))
        # 原神旺月 fallback
        if yuan_shen_element:
            peak_months = _ELEMENT_PEAK_MONTHS.get(yuan_shen_element, [])
            for pm in peak_months:
                d = datetime(base.year, pm, 15)
                if d <= base:
                    d = datetime(base.year + 1, pm, 15)
                candidates.append(("原神旺月", d, "",
                                   f"原神{yuan_shen_element}旺月（{pm}月）"))

    # ===== 阶梯接线（第七十九批「只增不换」＋第一百六十批用户裁「逐出改首条」）=====
    # 名次表按阶梯支首次出现建立。第七十九批实测过**逐出效应**（把阶梯支并进七条规则
    # 一起竞争那 5 个日期槽位：tune loose 100.0→94.1、wikisource_holdout 92.1→73.7——
    # 排序靠前但日期靠后的阶梯支把原本在窗口内的支顶了出去），故当时改为只增不换：
    # 日历层的 5 个槽位仍按七条规则的时间序取，阶梯里未被子集覆盖的名次最多追加 2 条。
    # 遗留口径问题：追加条目排在尾部，日期层第一个日期仍不保证等于阶梯主应期。
    # 第一百六十批用户裁「逐出改首条」——取**最小逐出**而非第七十九批否掉的全序重排：
    # 阶梯第 1 名（主应期）不在 5 槽内 ⇒ 置首并挤掉原第 5 槽（至多丢一条）；
    # 已在 5 槽内 ⇒ 提前到首位（一条不丢）。代价实测见 docs/CHANGELOG.md 第一百六十批。
    _rank_of: dict[str, int] = {}
    _BRANCH_LADDER_RULE: dict[str, str] = {}
    for _i, _item in enumerate(ladder or []):
        _tok, _rule_txt = (_item if isinstance(_item, (list, tuple)) and len(_item) >= 2
                           else (str(_item or ""), ""))
        _b = str(_tok or "")[:1]
        if not _b or _b in _rank_of or _b not in _BRANCH_CLASH_MAP:
            continue
        _rank_of[_b] = _i
        _BRANCH_LADDER_RULE[_b] = str(_rule_txt or "")[:40]

    # ===== Deduplicate: if 逢值 == 填实 or 逢冲 == 冲空, keep more specific rule =====
    seen_dates: dict[str, tuple[str, datetime | None, str, str]] = {}
    for rule, dt, br, desc in candidates:
        if dt is None:
            continue
        key = dt.strftime("%Y-%m-%d")
        # Prefer more specific rules over generic ones
        priority = {"飞神冲开": 6, "飞神值日(伏得出)": 5, "三合成局": 4,
                     "月破逢合": 4, "填实(实空)": 3, "冲空": 4, "逢值": 2,
                     "逢冲": 2, "原神值日": 2, "月破填实": 3,
                     "速应(旺)": 1, "速应(次日)": 1, "原神旺日(迟应)": 1,
                     "原神旺月": 0}
        existing = seen_dates.get(key)
        if existing is None or priority.get(rule, 0) > priority.get(existing[0], 0):
            seen_dates[key] = (rule, dt, br, desc)

    unique_sorted = sorted(seen_dates.values(),
                           key=lambda x: x[1] or datetime.max if x[1] else datetime.max)
    top5 = unique_sorted[:5]
    # 阶梯里名次最靠前、却没被上面 5 个日期覆盖的支，最多补 2 条（只增不换，见上注释）。
    _covered = {x[2] for x in top5 if x[1]}
    _extra: list = []
    for _b, _i in sorted(_rank_of.items(), key=lambda kv: kv[1]):
        if len(_extra) >= 2 or _b in _covered:
            continue
        _d = _next_date_with_day_branch(base, _b)
        if _d and all(_d != _x[1] for _x in top5 + _extra if _x[1]):
            _extra.append((_rank_of[_b], _BRANCH_LADDER_RULE.get(_b, f"应期阶梯第{_i + 1}"),
                           _d, _b, f"主应期阶梯名次 {_i + 1}（{_b}日）"))
    if _extra:
        top5 = top5 + [( _ru, _dt, _br, _de) for _rk, _ru, _dt, _br, _de
                       in sorted(_extra, key=lambda x: x[0])]

    # ===== 逐出改首条（第一百六十批，用户裁）=====
    # 报告首条必须等于阶梯主应期（第 1 名）。最小逐出：不在 5 槽内则置首并挤掉原第 5 槽；
    # 已在槽内则提前（不丢条目）。date 为 None 的槽不参与比较。
    if _rank_of and top5:
        _top_b = min(_rank_of, key=_rank_of.get)
        _hit = next((x for x in top5 if x[2] == _top_b), None)
        if _hit is not None:
            top5 = [_hit] + [x for x in top5 if x is not _hit]
        else:
            _d = _next_date_with_day_branch(base, _top_b)
            if _d and all(_d != _x[1] for _x in top5 if _x[1]):
                top5 = [(_BRANCH_LADDER_RULE.get(_top_b, "应期阶梯第1"),
                         _d, _top_b,
                         f"主应期阶梯第 1（{_top_b}日）")] + top5[:4]

    # ===== Build result =====
    dates_list = []
    for rule, dt, br, desc in top5:
        dates_list.append({
            "rule": rule,
            "date": dt.strftime("%Y-%m-%d") if dt else None,
            "branch": br,
            "description": desc,
        })

    if not dates_list:
        speed = YINGQI_TXT["no_yingqi"]["text"]
    elif any(d["rule"].startswith("速应") for d in dates_list):
        speed = YINGQI_TXT["speed_fast_desc"]["text"]
    elif any(d["rule"] in ("逢值", "逢冲", "三合成局") for d in dates_list):
        speed = YINGQI_TXT["speed_medium_desc"]["text"]
    else:
        speed = YINGQI_TXT["speed_slow_desc"]["text"]

    if dates_list:
        date_strs = "、".join(f"{d['date']}({d['rule']})" for d in dates_list if d["date"])
        summary = f"应期（{speed}）：{date_strs}"
    else:
        summary = f"应期（{speed}）：难以确定具体日期，以用神旺衰断迟速"

    return {
        "dates": dates_list,
        "speed": speed,
        "summary_text": summary,
        "use_god_branch": use_god_branch,
        "use_god_element": use_god_element,
        "strength_level": strength_level,
        "method": "增删易/黄金策规则→日历日期",
    }
