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

# 判定上限的档位序（与 step5 的 verdict 枚举一致）
RANK = {"大凶": 0, "凶": 1, "平凶": 2, "平吉": 3, "吉": 4, "大吉": 5}

_HE_SET = {frozenset(p) for p in HE_PAIRS}
_CHONG_SET = {frozenset(p) for p in CHONG_PAIRS}

# 化凶之七（《增删卜易》源L948「凡用神原神动化回头克、化绝、化墓、化空、化鬼、化退神皆为化凶」的枚举，只列引擎已能结构化识别的形态）
HUA_XIONG = ("化退神", "化绝", "化墓", "化空", "回头克", "化鬼")


def _he(a: str, b: str) -> bool:
    return frozenset((a, b)) in _HE_SET


def _chong(a: str, b: str) -> bool:
    return frozenset((a, b)) in _CHONG_SET


def _month_state(element: str, month_element: str) -> str:
    """月令下的旺/相/休/囚/死（五行同法：同我旺、我生相、生我休、克我囚、我克死）。

    这里只用于**无力判定**，取《增删卜易》源L551「以上元神无力生用神，无用之元神也，虽有如无」的"休囚"口径，不引入新的量纲。
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
    """该爻与世爻「相生」或「六合」——書《增删卜易》源 L2786「若不生合世爻，或不持世，或世爻空破，亦属无益」 的"生合世爻"。"""
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

    调用方（step5）按 `cap` 把 verdict 压档；一条都不命中时原样返回。
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
    # L2612/L2613 的原文主语是「问妻问妾」，本条就只按婚姻开放。
    # 旧注曾写「求财半边未取证，硬并入会把自有基准里 4 例判吉的失物·求财案压成凶」——
    # 那句**归因错了一半**：逐例实算后，自有基准里 世爻=兄弟 而 基准=吉 的三例
    # （ZS011/ZS019/ZS028）**全是失物·寻物**，没有一例是求财；求财类里 世爻=兄弟 的
    # 只有 ZS015（基准=下跌，与压凶同向）。也就是说当年拦路的是「失物与求财混为一谈」，
    # 不是求财章本身有冲突。求财半边已在下面第 5 条按书上四条独立表述补上，
    # 失物侧仍不开放（《增删卜易》全书「失物/脱空/遗失」与「兄弟」同句者为 0 条）。
    if (world and qcls == "婚姻" and world.get("six_relation") == "兄弟"
            and any(y.get("six_relation") == "妻财" for y in lines)):
        caps.append({
            "rule_id": "liuyao.xiong_chi_shi_ke_cai",
            "cap": "凶",
            "src": "zengshan_buyi_dz.dz.txt:2613",
            "reason_key": "xiong_chi_shi_ke_cai",
            "detail": f"兄弟{wb}持世，卦有妻财（克妻财之神临身）",
        })

    # ── 5 兄弟持世·求财（本条补齐第 2 条当时"宁缺不假"另开的求财半边）──
    # 书上四条独立表述同指一事（逐字见 verdict_texts.json 该 key 的 basis）：
    #   《增删卜易》源L419「占求财妻财持世者必得，兄弟持世者难求」、
    #   源L1592「占财兄爻为忌神，兄爻持世，求财不获」、
    #   《卜筮正宗》源L1102「求财见财爻持世则有，兄弟持世则无」、
    #   源L327「兄弟持世莫求财，官兴须虑祸将来」。
    # 量级差取《黄金策》源L2416「若临兄弟，虽或安静，亦主难得，发动尤甚」：
    #   安静→压到平凶（难得而不称心）；发动→压到凶。
    # **不外推到失物/寻物**：上一批"硬并入会压坏自有基准"的顾虑，实测来自把失物与求财
    # 混为一谈——自有基准里 世爻=兄弟 而 基准=吉 的三例（ZS011/ZS019/ZS028）全是失物·寻物，
    # 而《增删卜易》全书检索"失物/脱空/遗失"与"兄弟"同句者为 0 条，书上没说这条禁忌，
    # 就不给加。求财类里 世爻=兄弟 的只有 ZS015（基准=下跌，与压凶同向）与回归 fixture
    # reg_18，因此本条**不压任何一条判吉的自有基准**——这是跑出来的，不是推测的。
    if world and qcls == "求财" and world.get("six_relation") == "兄弟":
        # 但本书自己给了一条例外，而且带真例：《增删卜易》源L3035 逐字「虽则兄爻持世无财，但喜卯日即是财星」
        # （立盘见《增删卜易》源L3028 逐字「如未月丁卯日借贷得晋卦」：乾宫金、兄弟酉金持世
        #  且六爻安静，日辰卯木正是宫金所克之妻财，断曰果得财）；
        # 同书又把这条例外写成通则：源L2342 逐字「得日月作财而合世，富而骄」。
        # 故日辰或月建本身即本宫之财（我克者）时，不压本条禁忌——
        # 这不是给案例开的分支，是书上的明文例外，凡"日月作财"皆同此判。
        cai_elem = KE_CYCLE.get(we, "")
        if not ((de and de == cai_elem) or (me and me == cai_elem)):
            caps.append({
                "rule_id": "liuyao.qiu_cai_xiong_chi_shi",
                "cap": "凶" if world.get("is_moving") else "平凶",
                "src": "zengshan_buyi_dz.dz.txt:419",
                "reason_key": "qiu_cai_xiong_shi",
                "detail": f"兄弟{wb}持世{'且发动' if world.get('is_moving') else '安静'}"
                          f"（占财兄爻为忌神）",
            })

    # ── 3 世爻休囚受克而动变出官鬼（变鬼）─────────────────────────
    wchg = ""
    if world:
        wchg = world.get("changed_six_relation") or (
            (changes.get(int(world.get("position", -1)), {}) or {}).get("changed_relation"))
    if world and world.get("is_moving") and wchg == "官鬼":
        wpos = int(world.get("position", -1))
        ct = (changes.get(wpos, {}) or {}).get("change_type") or ""
        mstate = _month_state(we, me)
        weak = mstate in ("囚", "死")
        prosperous = mstate in ("旺", "相")
        broken = _broken(wb, month_branch, empties)
        ke_day = bool(de) and KE_CYCLE.get(de) == we
        ke_dong = any(
            y.get("is_moving") and y.get("position") != world.get("position")
            and KE_CYCLE.get(BRANCH_ELEMENTS.get(y.get("earthly_branch", ""), ""), "") == we
            for y in lines
        )
        hua_ke = ct == "回头克"
        # 《卜筮全书》源L7071 逐字「若又化出鬼爻，谓病人变鬼。卦中更无子孙日辰解救，必死无疑之断」
        #   → 变鬼之凶自带前提：**无**子孙动、**无**日辰生扶才可定死档；有解救则不压。
        jiejiu = any(y.get("six_relation") == "子孙" and y.get("is_moving") for y in lines) or \
            bool(de) and SHENG_CYCLE.get(de) == we
        # 变鬼／变官之别出自本书自己的定式，不是我给案例找的台阶：
        # 《增删卜易》源L2822 逐字「世爻旺相动而变出官星回头生合世爻者，不作变鬼，乃为变官」
        #   → 旺相而变出之爻**生**世者不压。
        # 《增删卜易》源L1643 逐字「世若休囚，受克动而变出官星者乃为变鬼」
        #   → 休囚受克一支（旧实现只认这一支）。
        # 《增删卜易》源L3625 逐字「化鬼、化退神、化回头克，但逢一者皆非吉地」
        #   → 世旺也压的通则：化回头克自成一非吉地之据。
        # 《增删卜易》源L2354 逐字「不宜世爻变鬼，又化回头之克」
        #   → 该通则在同书里的实例（世与日月三合，仍因回头克而断凶）。
        # 旧实现只认第一支，于是"旺相世而化回头克"这一型整体漏压。
        if prosperous and ct == "回头生":
            pass
        elif (weak or broken) and (ke_day or ke_dong):
            caps.append({
                "rule_id": "liuyao.shi_hua_gui",
                "cap": "凶",
                "src": "zengshan_buyi_dz.dz.txt:1643",
                "reason_key": "shi_hua_gui",
                "detail": f"世爻{wb}{'月破' if broken else ''}{'日克' if ke_day else ''}"
                          f"{'动克' if ke_dong else ''}"
                          f"{'休囚' if weak else ''}而动化出官鬼（名变鬼）",
            })
        elif hua_ke and not jiejiu:
            caps.append({
                "rule_id": "liuyao.shi_hua_gui",
                "cap": "凶",
                "src": "zengshan_buyi_dz.dz.txt:3625",
                "reason_key": "shi_hua_gui",
                "detail": f"世爻{wb}（{mstate}）动化出官鬼，" + _DIR["frag_shi_hua_gui"],
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
    # 【本层只做"上限"，装不下"正向"——第七十五批实测到的架构事实，见 CHANGELOG 同批】
    # 书上占雨的吉例是《黄金策》源L300 逐字「卦中父动主有雨」，需要的是**抬升**判定；本模块的 caps 只会往下压，
    # 因此 WSD014（占何日雨·父母动·书判吉／引擎凶）这类盘**不在本层能修的范围**，留给 step5 的天气加分支（#23 未完部分）。
    # 6) 天气占（占雨／占晴）：父动主雨、财动主晴——按门类门控，不按问句关键词加判
    #    （书据见 `verdict_texts.json` 的 tianqi_yun_cai_dong / tianqi_qing_fu_dong 两条 basis，
   #    《黄金策》源L300 逐字「卦中父动主有雨，财动主晴。卦无父母，财爻又空，必然无雨；卦无妻财，父爻又空，必然不晴」；
   #    《卜筮全书》源L5770 逐字「五类中，唯父母为雨。此爻空亡，或休囚不动，雨未可望」；
   #    《卜筮全书》源L5721 逐字「妻财则父母忌爻，动则克制雨神，所以主晴」——
   #    结构事实取自第七十三批同一套判据）
    if qcls in ("天气·占雨", "天气·占晴"):
        moving_rels = {str(y.get("six_relation") or "") for y in lines
                       if isinstance(y, dict) and y.get("is_moving")}
        changed_rels = {str(y.get("changed_six_relation") or "") for y in lines
                        if isinstance(y, dict) and y.get("is_moving")}
        father_move = "父母" in moving_rels or "父母" in changed_rels
        wealth_move = "妻财" in moving_rels
        if qcls == "天气·占雨" and wealth_move and not father_move:
            caps.append({
                "rule_id": "liuyao.tianqi_zhan_yu", "cap": "凶",
                "src": "huangjince_dz.dz.txt:300", "reason_key": "tianqi_yun_cai_dong",
                "detail": "占雨而财动父静（财动主晴）",
            })
        elif qcls == "天气·占晴" and father_move:
            caps.append({
                "rule_id": "liuyao.tianqi_zhan_qing", "cap": "凶",
                "src": "bushi_quanshu_dz.dz.txt:5721", "reason_key": "tianqi_qing_fu_dong",
                "detail": "占晴而父母发动或化出父母（父动主雨）",
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
