# -*- coding: utf-8 -*-
"""六爻古典方向凶格：四条**结构判定**，只产出判定上限（cap），不产断语。

为什么要这一层（TECH-DEBT §2.11 D1）：主分是十项加和 + 阈值分档，四条古籍凶格在
加权里要么没有条目、要么被正项冲掉，于是出现「書源本案结局明写凶、引擎判吉」。
本模块把它们做成**可指回原文的上限判定**：命中即把 verdict 压到该书说的档位，
不参与加和，所以不会被别的正项"平均掉"。

四条判据与逐字出处（行号为 `data/sources/<book>` 的 1 基行号，cat -n 口径）：

1. `liuyao.chuxian_wuqing` 出现无情（功名类）
   `zengshan_buyi_dz.dz.txt` L2786「出现无情，难遂青云之志。父与官星虽则出现，
   若不生合世爻，或不持世，或世爻空破，亦属无益」；
   `bushi_quanshu_dz.dz.txt` L7692、`huangjince_dz.dz.txt` L2180 同句同释（三源同证）。
2. `liuyao.xiong_chi_shi_ke_cai` 兄弟持世克财（婚姻·妻妾·求财）
   `zengshan_buyi_dz.dz.txt` L2613「财旺兄衰终须反目，克财财退必主生离……
   兄爻持世财化退神者，亦同此意，非反目即生离」、L2612「弟兄持世……不拘问妻问妾，
   皆不得长年」、L419「占求财……兄弟持世者难求」。
3. `liuyao.shi_hua_gui` 世爻休囚受克而动变出官鬼（变鬼）
   `zengshan_buyi_dz.dz.txt` L1643「世若休囚，受克动而变出官星者乃为变鬼，
   不惟难于王家食禄，须忧梦沉黄梁」、L3625「世爻子孙爻……不宜……化鬼、化退神、
   化回头克，但逢一者皆非吉地」。
4. `liuyao.yuan_shen_wu_li` 用神化凶而元神无力（源绝）
   `zengshan_buyi_dz.dz.txt` L948「凡用神原神动化回头克、化绝、化墓、化空、化鬼、
   化退神皆为化凶」、L551「元神虽现又有不能生用神者有六……以上元神无力生用神，
   无用之元神也，虽有如无」。

**与铁律一的关系**：本模块只输出「结构事实 + 上限档位」，一切吉凶措辞都取自
`data/rules/verdict_texts.json` 的 `step5_classical_notes` / `step5_verdict_descs`，
代码里没有一条断语字面量；上限档位的档位名（吉/凶）是评分契约要求的枚举值，
不是文案。applicability 一律按书源自带限定实现，见各条 `_reason_key` 与注册表。
"""
from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))
if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel  # noqa: E402

_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402
    BRANCH_ELEMENTS,
    CHONG_PAIRS,
    HE_PAIRS,
    KE_CYCLE,
    SHENG_CYCLE,
)

# 判定上限的档位序（与 liuyao_step5 的 verdict 枚举一致）
RANK = {"大凶": 0, "凶": 1, "平凶": 2, "平吉": 3, "吉": 4, "大吉": 5}

_HE_SET = {frozenset(p) for p in HE_PAIRS}
_CHONG_SET = {frozenset(p) for p in CHONG_PAIRS}

# 化凶之七（書源 L948 的枚举，只列引擎已能结构化识别的形态）
HUA_XIONG = ("化退神", "化绝", "化墓", "化空", "回头克", "化鬼")


def _he(a: str, b: str) -> bool:
    return frozenset((a, b)) in _HE_SET


def _chong(a: str, b: str) -> bool:
    return frozenset((a, b)) in _CHONG_SET


def _month_state(element: str, month_element: str) -> str:
    """月令下的旺/相/休/囚/死（五行同法：同我旺、我生相、生我休、克我囚、我克死）。

    这里只用于**无力判定**，取書源 L551 的"休囚"口径，不引入新的量纲。
    """
    if not month_element or not element:
        return ""
    if element == month_element:
        return "旺"
    if SHENG_CYCLE.get(month_element) == element:
        return "相"
    if SHENG_CYCLE.get(element) == month_element:
        return "休"
    if KE_CYCLE.get(month_element) == element:
        return "囚"
    if KE_CYCLE.get(element) == month_element:
        return "死"
    return ""


def _world_line(lines: list[dict]) -> dict | None:
    return next((y for y in lines if isinstance(y, dict) and y.get("is_world")), None)


def _sheng_or_he_world(y: dict, world_branch: str, world_element: str) -> bool:
    """该爻与世爻「相生」或「六合」——書源 L2786 的"生合世爻"。"""
    if y.get("is_world"):
        return True
    e = y.get("element") or BRANCH_ELEMENTS.get(y.get("earthly_branch", ""), "")
    if SHENG_CYCLE.get(e) == world_element:
        return True
    return _he(y.get("earthly_branch", ""), world_branch)


def _broken(branch: str, month_branch: str, empty_branches: list[str]) -> bool:
    return branch in (empty_branches or []) or _chong(branch, month_branch)


def detect_direction_caps(
    lines: list[dict],
    step2: dict,
    step4: dict,
    month_branch: str,
    day_branch: str,
    empty_branches: list[str] | None,
) -> list[dict]:
    """返回命中的凶格列表：每项 {rule_id, cap, src, reason_key, detail}。

    调用方（liuyao_step5）按 `cap` 把 verdict 压档；一条都不命中时原样返回。
    """
    caps: list[dict] = []
    lines = [y for y in (lines or []) if isinstance(y, dict)]
    world = _world_line(lines)
    # 世爻缺失（异常盘面/单元构造输入）只关掉三条以世爻为主语的格，
    # 不能整函数早退——第 4 格的主语是用神与元神，与世爻无关。
    wb = (world or {}).get("earthly_branch", "")
    we = BRANCH_ELEMENTS.get(wb, "")
    qcls = str((step2 or {}).get("question_class") or "")
    ug_cat = str((step2 or {}).get("use_god_category") or "")
    ug_el = str((step2 or {}).get("use_god_element") or "")
    me = BRANCH_ELEMENTS.get(month_branch, "")
    de = BRANCH_ELEMENTS.get(day_branch, "")
    empties = list(empty_branches or [])
    changes = {int(d.get("position", -1)): d
               for d in ((step4 or {}).get("details") or []) if isinstance(d, dict)}

    # ── 1 出现无情（功名类）────────────────────────────────────────
    if world and qcls == "功名科举":
        guan_fu = [y for y in lines if y.get("six_relation") in ("官鬼", "父母")]
        if guan_fu and not any(_sheng_or_he_world(y, wb, we) for y in guan_fu):
            caps.append({
                "rule_id": "liuyao.chuxian_wuqing",
                "cap": "凶",
                "src": "zengshan_buyi_dz.dz.txt:2786",
                "reason_key": "chuxian_wuqing",
                "detail": f"官鬼父母{sorted({y.get('six_relation', '') for y in guan_fu})}"
                          f"出现，而不持世、不生不合世爻{wb}",
            })

    # ── 2 兄弟持世克财（只取婚姻章）───────────────────────────────
    # L2612/L2613 的原文主语是「问妻问妾」；「兄弟持世者难求」(L419) 属求财章，
    # 其限定（财旺、子孙生财等）本轮未逐条取证，硬并入会把自有基准里 4 例判吉的
    # 失物·求财案压成凶——宁缺不假。
    if (world and qcls == "婚姻" and world.get("six_relation") == "兄弟"
            and any(y.get("six_relation") == "妻财" for y in lines)):
        caps.append({
            "rule_id": "liuyao.xiong_chi_shi_ke_cai",
            "cap": "凶",
            "src": "zengshan_buyi_dz.dz.txt:2613",
            "reason_key": "xiong_chi_shi_ke_cai",
            "detail": f"兄弟{wb}持世，卦有妻财（克妻财之神临身）",
        })

    # ── 3 世爻休囚受克而动变出官鬼（变鬼）─────────────────────────
    wchg = ""
    if world:
        wchg = world.get("changed_six_relation") or (
            (changes.get(int(world.get("position", -1)), {}) or {}).get("changed_relation"))
    if world and world.get("is_moving") and wchg == "官鬼":
        weak = _month_state(we, me) in ("囚", "死")
        broken = _broken(wb, month_branch, empties)
        ke_day = bool(de) and KE_CYCLE.get(de) == we
        ke_dong = any(
            y.get("is_moving") and y.get("position") != world.get("position")
            and KE_CYCLE.get(BRANCH_ELEMENTS.get(y.get("earthly_branch", ""), ""), "") == we
            for y in lines
        )
        if (weak or broken) and (ke_day or ke_dong):
            caps.append({
                "rule_id": "liuyao.shi_hua_gui",
                "cap": "凶",
                "src": "zengshan_buyi_dz.dz.txt:1643",
                "reason_key": "shi_hua_gui",
                "detail": f"世爻{wb}{'月破' if broken else ''}{'日克' if ke_day else ''}"
                          f"{'动克' if ke_dong else ''}"
                          f"{'休囚' if weak else ''}而动化出官鬼（名变鬼）",
            })

    # ── 4 用神化凶而元神无力（源绝）───────────────────────────────
    god_positions = {int(p.get("position", -1))
                     for p in ((step2 or {}).get("use_god_positions") or [])
                     if isinstance(p, dict)}
    yong = [y for y in lines if int(y.get("position", -1)) in god_positions] or \
        [y for y in lines if y.get("six_relation") == ug_cat]
    yong_moving = [y for y in yong if y.get("is_moving")]
    hua_xiong = [y for y in yong_moving
                 if (changes.get(int(y.get("position", -1)), {}) or {}).get("change_type")
                 in HUA_XIONG]
    # applicability 只取久病·寿类：L1182 逐字「占近事岂可曰退？」、L1287「退神之法有四」
    # 都把"退而不退"限定在得令旺相与近事；把本条用在行人/功名/会试上会压坏自有基准
    # （实测 HO008 占升迁、WS001 占父何日归、SG001 占会试三例），故只按書源的落点开放。
    if hua_xiong and ug_el and qcls == "疾病·久病":
        yuan_el = next((e for e, t in SHENG_CYCLE.items() if t == ug_el), "")
        yuan_lines = [y for y in lines
                      if BRANCH_ELEMENTS.get(y.get("earthly_branch", ""), "") == yuan_el]
        if not yuan_lines:
            # L551 说的是「元神虽现」而无力；不上卦属伏藏另一题，不在本条适用面内
            wu_li, why = False, ""
        else:
            states = {_month_state(yuan_el, me)}
            broken_all = all(_broken(y.get("earthly_branch", ""), month_branch, empties)
                             for y in yuan_lines)
            quiet = not any(y.get("is_moving") for y in yuan_lines)
            moved_bad = any(
                (changes.get(int(y.get("position", -1)), {}) or {}).get("change_type")
                in HUA_XIONG for y in yuan_lines if y.get("is_moving"))
            # L551 第一款有两个形态：「元神休囚，不动」与「或动而休囚又被伤克者」——
            # 动而受克同样无力，漏掉这一支会让 WSD002 这类"忌神旺克元神"的源绝格不判。
            ke_month = bool(me) and KE_CYCLE.get(me, "") == yuan_el
            ke_day = bool(de) and KE_CYCLE.get(de, "") == yuan_el
            yuan_positions = {y.get("position") for y in yuan_lines}
            ke_dong = any(
                y.get("is_moving")
                and KE_CYCLE.get(BRANCH_ELEMENTS.get(y.get("earthly_branch", ""), ""), "")
                == yuan_el and y.get("position") not in yuan_positions
                for y in lines)
            weak = bool(states & {"休", "囚", "死"})
            if (weak and (quiet or ke_month or ke_day or ke_dong)) or broken_all or moved_bad:
                tags = [t for t, on in (("休囚", weak),
                                       ("静而不动", quiet),
                                       ("被日月克", ke_month or ke_day),
                                       ("被动爻克", ke_dong),
                                       ("空破", broken_all),
                                       ("动而化凶", moved_bad)) if on]
                wu_li, why = True, f"元神{yuan_el}" + "、".join(tags)
            else:
                wu_li, why = False, ""
        if wu_li:
            caps.append({
                "rule_id": "liuyao.yuan_shen_wu_li",
                "cap": "平凶",
                "src": "zengshan_buyi_dz.dz.txt:551",
                "reason_key": "yuan_shen_wu_li",
                "detail": f"用神动而"
                          f"{(changes.get(int(yong_moving[0].get('position', -1)), {}) or {}).get('change_type', '')}"
                          f"，{why}",
            })
    return caps


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
