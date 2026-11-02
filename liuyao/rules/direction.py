# -*- coding: utf-8 -*-
"""六爻古典方向凶格：四条**结构判定**，只产出判定上限（cap），不产断语。

为什么要这一层（原登记于 docs/TECH-DEBT.md §2.11 D1——该台账已随扁平化删除、节号不再存在；
现行可回指处＝docs/CHANGELOG.md 第二十一批＋本模块逐字出处）：主分是十项加和 + 阈值分档，
四条古籍凶格在
加权里要么没有条目、要么被正项冲掉，于是出现「書源本案结局明写凶、引擎判吉」。
本模块把它们做成**可指回原文的上限判定**：命中即把 verdict 压到该书说的档位，
不参与加和，所以不会被别的正项"平均掉"。

五条判据与逐字出处（行号为 `data/sources/<book>` 的 1 基行号，cat -n 口径）：

1. `liuyao.chuxian_wuqing` 出现无情（功名类）
   《增删卜易》源L2786「出现无情，难遂青云之志。父与官星虽则出现，若不生合世爻，或不持世，或世爻空破，亦属无益」；
   《卜筮全书》源L7692「若不临持身世，或不生合世身，或被世爻冲克，或被月日破坏，或临死墓空绝，皆谓无情」；
   《黄金策》源L2180「皆谓无情，虽在卦中，与我无益，所以难遂青云之志也」。
   三源**同释而文字互异**，故各自逐字引，不并称"同句"（旧写法「同句同释」易被读成一字不差）。
2. `liuyao.xiong_chi_shi_ke_cai` 兄弟持世克财（婚姻·妻妾；求财半边另立第 5 条）
   《增删卜易》源L2613「财旺兄衰终须反目，克财财退必主生离」；
   《增删卜易》源L2613「兄爻持世财化退神者，亦同此意，非反目即生离」；
   《增删卜易》源L2612「弟兄持世或兄爻动於卦中，或日月临兄弟以伤财，或兄化财爻，不拘问妻问妾，皆不得长年」；
   《增删卜易》源L419「占求财妻财持世者必得，兄弟持世者难求」。
3. `liuyao.shi_hua_gui` 世爻动而变出官鬼（变鬼）——三支，旧实现只认第一支
   《增删卜易》源L1643「世若休囚，受克动而变出官星者乃为变鬼，不惟难于王家食禄，须忧梦沉黄梁」；
   《增删卜易》源L3625「化绝、化墓、化鬼、化退神、化回头克，但逢一者皆非吉地」（旺世也压的通则；
   旧写法把顺序写成「化鬼、化退神、化回头克」，与底本次序不符，已按底本改正）；
   豁免见《增删卜易》源L2822「世爻旺相动而变出官星回头生合世爻者，不作变鬼，乃为变官」；
   解救前提见《卜筮全书》源L7071「若又化出鬼爻，谓病人变鬼。卦中更无子孙日辰解救，必死无疑之断」。
4. `liuyao.yuan_shen_wu_li` 用神化凶而元神无力（源绝）
   《增删卜易》源L948「凡用神原神动化回头克、化绝、化墓、化空、化鬼、化退神皆为化凶」；
   《增删卜易》源L551「元神虽现又有不能生用神者有六」与「以上元神无力生用神，无用之元神也，虽有如无」
   （两句之间隔着六条明细，**不是一句连续引文**，故分列两段逐字，不用省略号糊成一串）。
6. `liuyao.tianqi_zhan_yu` / `liuyao.tianqi_zhan_qing` 天气占（第七十四批落门类、第七十五批接方向层）
   《黄金策》源L300 逐字「卦中父动主有雨，财动主晴」；《卜筮全书》源L5721 逐字「卦中父动，主雨；财动，主晴」；
   《卜筮全书》源L5770 逐字「五类中，唯父母为雨。此爻空亡，或休囚不动，雨未可望」
   门类门控（天气·占雨／天气·占晴），不按问句关键词加判。

5. `liuyao.qiu_cai_xiong_chi_shi` 兄弟持世占求财（安静压平凶／发动压凶）
   《增删卜易》源L419「占求财妻财持世者必得，兄弟持世者难求」、
   源L1592「占财兄爻为忌神，兄爻持世，求财不获」；
   《卜筮正宗》源L1102「求财见财爻持世则有，兄弟持世则无」、
   源L327「兄弟持世莫求财，官兴须虑祸将来」；
   《黄金策》源L2416「若临兄弟，虽或安静，亦主难得，发动尤甚」（两档量级差取此）。

**与铁律一的关系**：本模块只输出「结构事实 + 上限档位」，一切吉凶措辞都取自
`data/rules/verdict_texts.json` 的 `step5_classical_notes` / `step5_verdict_descs`，
代码里没有一条断语字面量；上限档位的档位名（吉/凶）是评分契约要求的枚举值，
不是文案。applicability 一律按书源自带限定实现，见各条 `_reason_key` 与注册表。
"""
from __future__ import annotations
import labels_loader as _labels  # noqa: E402  210批 §一.1 断语外置
_DIR = _labels.load("direction")

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))  # liuyao/rules/
_scripts_d = _ks_os.path.join(_ks_os.path.dirname(_ks_d), "scripts")  # kernel_path/labels_loader 所在
for _p in (_ks_d, _scripts_d):
    if _p not in _ks_sys.path:
        _ks_sys.path.insert(0, _p)

from kernel_path import ensure_kernel_on_path as _ensure_kernel  # noqa: E402

_ensure_kernel(__file__)


from predicates import RANK  # apply_caps 档位序；纯函数库已独立至 rules/predicates.py

def detect_direction_caps(
    lines: list[dict],
    step2: dict,
    step4: dict,
    month_branch: str,
    day_branch: str,
    empty_branches: list[str] | None,
    original_hexagram_name: str = "",
    changed_hexagram_name: str = "",
) -> list[dict]:
    """返回命中的凶格列表：每项 {rule_id, cap, src, reason_key, detail}。

    调用方（step5）按 `cap` 把 verdict 压档；一条都不命中时原样返回。
    original/changed hexagram name 供"六冲变合"类救应格局判定（T29）。
    """
    lines = [y for y in (lines or []) if isinstance(y, dict)]
    empties = list(empty_branches or [])
    from rule_engine import evaluate_caps as _re_eval
    return _re_eval(lines, step2, step4, month_branch, day_branch, empties,
                    original_hexagram_name, changed_hexagram_name)


def apply_caps(verdict: str, caps: list[dict]) -> tuple[str, bool]:
    """按最严的一条 cap 压档；返回 (新 verdict, 是否压动过)。"""
    cur = RANK.get(verdict, -1)
    fired = False
    for c in caps or []:
        tgt = RANK.get(c.get("cap"), 99)
        if cur >= 0 and tgt < cur:
            cur = tgt
            fired = True
    back = {v: k for k, v in RANK.items()}
    return (back.get(cur, verdict) if fired else verdict), fired
