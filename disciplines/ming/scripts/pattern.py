# -*- coding: utf-8 -*-
"""命·格局与强弱（纯机械表驱动，无命运断语）。

规则口径（通行子平，可回溯）：
- 藏干十神本/中/余气权重 1.0 / 0.5 / 0.25
- 生扶 = 印 + 比劫；克泄耗 = 官杀 + 食伤 + 财
- 身旺喜克泄耗，身弱喜生扶（《渊海子平》扶抑用神通行口径）
- 格局取月支本气十神正格名；从格按《滴天髓》从化论/从象/假从章分级
  （真从/假从/从旺/从强/从气/从势，机械口径见 `_from_judge`）
大运顺逆走 core.ming_tables.dayun_direction；起运岁数按三日=一年近似。
"""
from __future__ import annotations

from yishu_core.ming_tables import (
    dayun_direction,
    DAYS_PER_LUCK_YEAR,
    MONTHS_PER_DAY,
    tiaohou_of,
)
from yishu_core.ganzhi_calendar import TIGER_MONTH_STEM
from yishu_core.relations import STEM_YINYANG, stems_wuhe, ten_god
from yishu_core.symbols import (
    BRANCH_ELEMENTS,
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
    STEM_ELEMENTS,
    SHENG_CYCLE,
    KE_CYCLE,
    CHONG_PAIRS,
    HE_PAIRS,
    HARM_PAIRS,
    SAN_HE_GROUPS,
    SAN_HUI_GROUPS,
    sanxing_hits,
    twelve_growth,
)

# 成败救应/从格 basis 的书源引文唯一真值源在 data/verdicts.json（AGENTS.md §三）
import json as _json
from pathlib import Path as _Path

_MING_DATA = _Path(__file__).resolve().parent.parent / "data"
_MING_VERDICTS = _json.loads((_MING_DATA / "verdicts.json").read_text(encoding="utf-8"))
_CB = _MING_VERDICTS["格局成败引文"]
_CONG = _MING_VERDICTS["从格引文"]


# 十神 → 作用类
TEN_GOD_GROUP = {
    "比肩": "比劫",
    "劫财": "比劫",
    "正印": "印",
    "偏印": "印",
    "食神": "食伤",
    "伤官": "食伤",
    "正财": "财",
    "偏财": "财",
    "正官": "官杀",
    "偏官": "官杀",
    "七杀": "官杀",
}

# 月令本气十神 → 正格名
PATTERN_BY_MONTH_GOD = {
    "正官": "正官格",
    "偏官": "偏官格",
    "七杀": "偏官格",
    "正印": "正印格",
    "偏印": "偏印格",
    "食神": "食神格",
    "伤官": "伤官格",
    "正财": "正财格",
    "偏财": "偏财格",
    "比肩": "建禄格",
    "劫财": "月刃格",
}

LAYER_WEIGHT = {"本气": 1.0, "中气": 0.5, "余气": 0.25}

# 身旺/身弱临界（strength_score：生扶 − 克泄耗，含得令加权）
WEAK_THRESHOLD = -1.5
STRONG_THRESHOLD = 1.5


# 格局成败救应规则（《子平真诠·论用神成败救应/论相神紧要》，机械主干版）。
# 每格定义：成条件（书源「何谓成」的成格结构，满足即成）、忌神类（破格者）、
# 救应类（制忌神者）。判据只取**透干十神有无**（主干规则）；地支会合、位置、合化
# 等细节徐注才谈，机械层不做——基准例只选主干可判的书源命例（ming 案例集）。
# 判定顺序：成条件满足 → 成格；否则忌神透：救应透 → 救应成格，无救 → 破格；
# 忌神未透 → 成格。
# 原文依据（逐条可溯）：
#   官格：成「官逢财印，又无刑冲破害」；败「官逢伤克刑冲」；救「官逢伤而透印以解之」
#   财格：成「财生官旺」「财逢食生而身强带比」；败「财轻比重，财透七煞」；
#        救「财逢劫而透食以化之，生官以制之」
#   印格：成「印轻逢煞」「官印双全」；败「印轻逢财」；救「印逢财而劫财以解之」
#   食神格：成「食神生财」「食带煞而无财，弃食就煞而透印」；败「食神逢枭」；
#           救「食逢枭而就煞以成格，或生财以护食」
#   伤官格：成「伤官生财」「伤官佩印」「伤官旺、身主弱而透煞印」「伤官带煞而无财」；
#           败「伤官…见官」「佩印而伤轻身旺」；救（伤官见官）以印制伤
#   七杀格：成「身强七煞逢制」（食制/印化）；败「七煞逢财无制」；
#   阳刃格：成「阳刃透官煞而露财印，不见伤官」；败「阳刃无官煞」；救官杀制刃
#   建禄月劫：成「透官而逢财印，透财而逢食伤，透煞而遇制伏」；
#             败「无财官，透煞印」（月劫日主旺，透印助旺、无财官泄制）
PATTERN_CB_RULES = {
    "正官格": {"cheng": ("财", "印"), "ji": ("食伤",), "jiu": ("印",)},
    "偏官格": {"cheng": ("食伤", "印"), "ji": ("财",), "jiu": ("食伤", "印")},
    "正印格": {"cheng": ("官杀",), "ji": ("财",), "jiu": ("比劫",)},
    "偏印格": {"cheng": ("官杀",), "ji": ("财",), "jiu": ("比劫",)},
    "食神格": {"cheng": ("财",), "ji": ("印",), "jiu": ("财",)},
    "伤官格": {"cheng": ("财", "印"), "ji": ("官杀",), "jiu": ("印",)},
    # 财格：成=食伤生财 / 正官生财（书源「财生官旺」「财逢食生而身强带比」）；
    # 败=七杀透（财党煞，「财透七煞，财格败也」）/ 比劫透（财轻比重）；
    # 救=食伤制煞生财 / 合煞存财。官与煞须细分（七杀≠正官），故财格走特判分支。
    "正财格": {"cheng": ("食伤", "正官"), "ji": ("七杀", "比劫"), "jiu": ("食伤", "正官")},
    "偏财格": {"cheng": ("食伤", "正官"), "ji": ("七杀", "比劫"), "jiu": ("食伤", "正官")},
    "建禄格": {"cheng": ("官杀", "财", "食伤"), "ji": ("印",), "jiu": ("财", "食伤")},
    "月刃格": {"cheng": ("官杀",), "ji": ("食伤", "财"), "jiu": ("印",)},
}
# 伤官格补充成条件：书源「伤官旺、身主弱而透煞印」「伤官带煞而无财」亦成——
# 即官杀透而印透（带煞佩印）直接成格，不算「救应」。主表 cheng 之后特判。
SHANGGUAN_CHENG_WITH_GUANSHA = True


def _god_detail(chart_json: dict) -> list[dict]:
    """透干明细 [{god, stem}]（year/month/hour，排除 day 柱）。"""
    pillars = chart_json.get("pillars") or {}
    out = []
    for pname in ("year", "month", "hour"):
        p = pillars.get(pname) or {}
        tg, st = p.get("ten_god") or "", p.get("stem") or ""
        if tg and st:
            out.append({"god": tg, "stem": st})
    return out


def _has_yang_ren(chart_json: dict) -> bool:
    """阳刃在支（年/日/时支为阳干日主之帝旺位）。

    书源：《三命通会》阳刃起例（甲刃卯、丙戊刃午、庚刃酉、壬刃子）；
    阴干无刃。用 core 十二长生表推，不另存表。
    """
    pillars = chart_json.get("pillars") or {}
    day_stem = (pillars.get("day") or {}).get("stem") or ""
    if not day_stem or STEM_YINYANG.get(day_stem) != "阳":
        return False
    elem = STEM_ELEMENTS.get(day_stem) or ""
    for k in ("year", "day", "hour"):
        b = (pillars.get(k) or {}).get("branch") or ""
        if b and twelve_growth(elem, b) == "帝旺":
            return True
    return False


def _role_of_elem(day_elem: str, other_elem: str) -> str:
    """五行 vs 日主五行 → 十神作用类（比劫/印/食伤/官杀/财）。

    书源：十神定义（生我者印、我生者食伤、克我者官杀、我克者财、
    同我者比劫），用 core 五行相生/相克表推，不另存表。
    """
    if not day_elem or not other_elem:
        return ""
    if other_elem == day_elem:
        return "比劫"
    if SHENG_CYCLE.get(other_elem) == day_elem:      # 他生我 → 印
        return "印"
    if SHENG_CYCLE.get(day_elem) == other_elem:      # 我生他 → 食伤
        return "食伤"
    if KE_CYCLE.get(other_elem) == day_elem:         # 他克我 → 官杀
        return "官杀"
    return "财"                                      # 我克他


def _from_judge(chart_json: dict, details: list[dict], day_stem: str,
                decree: float = 0.0, sheng_fu: float = 0.0) -> tuple:
    """从格可判级判定（《滴天髓·从化论/从象/假从》章）。

    返回 (from_kind, from_type, from_basis, from_label)；
    from_label 兼容旧字段 tentative_special（形如「从杀·真从」）。

    原文依据（逐条可溯）：
      - 从得真者只论从，从神又有吉和凶（《从化论》）
      - 日主孤弱无气，天地人三元，绝无一毫生扶之意，财官等强甚，乃为真从也（《从象》原注）
      - 日主弱矣，财官强矣，不能不从；中有比劫暗生，从之不真（《假从》原注）
      - 从旺者四柱皆比劫；从强者印绶重重比劫叠叠；从气者不论财官印绶食伤，
        气势在木火/金水；从势者日主无根，财官食伤并旺（《从象》任氏注）

    机械口径（v3，2026-09-30；边界诚实登记于 CHANGELOG）：
      - 生扶只认本气根；透干印比须坐支本气/中气为其五行才算有力（虚浮不算）
      - 地支互动（core 唯一真值源，无私有表）：
        三合局（三支全）→ 局内支本气被合化：日主根/印比失效、从神加权 +2.0；
        六冲（任一他支相冲）→ 日主根/印比/月令被冲则失效；
        从神主导本气支被冲 → 从之不真（type 强制假从，如 ZC011 卯酉冲杀）
      - 月令有效（ling_effective）：月支生扶日主且不被冲、不在三合局内
      - 从弱成立 = from_weight≥4.0 且 失令 且（无日主根 或 有印比）——有根有印比者
        归正格（成败救应按《子平真诠》），不再误入从格
      - 从旺/从强须 得令 且 sheng_fu≥5.0（「旺之极矣」），防月刃/建禄等正格误入
      - 从气须 失令 且 日主有根 且 四支本气集中于金水/木火
      - 灰区（登记）：透干比劫/印绶坐支无根书判假从而本判据按真从
        （ZC014 辛金天干丙丁庚辛、ZC015 丁印被癸克）；ZC012 寅令被申冲后
        印比俱失书仍判假从——三者待六合化气/合冲互动引入后复核。
    """
    if not day_stem:
        return None, None, "", None
    day_elem = STEM_ELEMENTS.get(day_stem) or ""
    if not day_elem:
        return None, None, "", None
    pillars = chart_json.get("pillars") or {}

    # 支本气角色（details 已含四支藏干十神，day 柱计入）；四支五行取地支本身
    main_roles = {}   # pillar -> role（本气）
    main_gods = {}    # pillar -> god（本气，细分用）
    weight_by_role = {"印": 0.0, "比劫": 0.0, "官杀": 0.0, "食伤": 0.0, "财": 0.0}
    branch_main_elems = []
    branch_list = []
    for pname in ("year", "month", "day", "hour"):
        br = (pillars.get(pname) or {}).get("branch") or ""
        if br:
            branch_list.append(br)
            branch_main_elems.append(BRANCH_ELEMENTS.get(br) or "")
    for d in details:
        role = d.get("role") or ""
        if role not in weight_by_role:
            continue
        w = float(d.get("w") or 0)
        weight_by_role[role] += w
        if d.get("layer") == "本气":
            main_roles[d.get("pillar") or ""] = role
            main_gods[d.get("pillar") or ""] = d.get("god") or ""

    # ── 地支互动（core 唯一真值源）：三合局（三支全）化气 + 六冲 ──
    sanhe_branches: set = set()
    sanhe_elem = ""
    for elem, grp in SAN_HE_GROUPS.items():
        if set(grp) <= set(branch_list):
            sanhe_elem = elem
            sanhe_branches = {b for b in branch_list if b in grp}
            break
    chong_map: dict = {}          # 支 -> {与之相冲的他支}（同类相冲=库冲不破）
    for b in branch_list:
        for o in branch_list:
            if o != b and ((b, o) in CHONG_PAIRS or (o, b) in CHONG_PAIRS):
                chong_map.setdefault(b, set()).add(o)
    chonged: set = set(chong_map)

    def _eff(br: str) -> bool:
        """支是否"有效"：未被三合局化；被冲者仅异类相冲算破
        （辰戌/丑未等同类库冲气不破——ZP003 甲印坐辰被戌冲仍算有根）。"""
        if br in sanhe_branches:
            return False
        if br in chong_map:
            return _chong_same_elem(br)   # 同类冲保留（库冲不破），异类冲破
        return True

    def _chong_same_elem(br: str) -> bool:
        """br 被同类五行支冲（辰戌/丑未等库冲、同气冲）→ 气不破，不算缺角。"""
        return any(BRANCH_ELEMENTS.get(o) == BRANCH_ELEMENTS.get(br)
                   for o in chong_map.get(br, ()))

    # 月令有效：月支生扶日主 且 未被冲、未被三合局化
    month_branch = (pillars.get("month") or {}).get("branch") or ""
    month_elem = BRANCH_ELEMENTS.get(month_branch, "")
    ling_effective = bool(
        month_elem and day_elem and _eff(month_branch) and
        (month_elem == day_elem or SHENG_CYCLE.get(month_elem) == day_elem))

    # 透干十神（year/month/hour）与坐支根气
    dry_has_yinbi = False          # 干透印比（虚浮也算，仅灰区登记参考）
    dry_strong_yinbi = False       # 干透印比且坐支本气/中气为该十神五行（有力）
    for pname in ("year", "month", "hour"):
        p = pillars.get(pname) or {}
        tg = p.get("ten_god") or ""
        br = p.get("branch") or ""
        st = p.get("stem") or ""
        if tg in ("正印", "偏印", "比肩", "劫财"):
            dry_has_yinbi = True
            if not _eff(br):
                continue          # 坐支被合化/被冲 → 印比虚浮，不算有力
            # 印五行 = 生我者（SHENG_CYCLE 是"我生"方向，须反向）；
            # 比劫五行 = 日主五行
            want_elem = ({v: k for k, v in SHENG_CYCLE.items()}.get(day_elem)
                         if tg in ("正印", "偏印") else day_elem)
            f = (chart_json.get("factors") or {}).get(pname) or {}
            hidden = f.get("hidden_stems") or []
            if hidden and want_elem:
                # 本气或中气是该五行 → 印比坐支有根（有力）
                if STEM_ELEMENTS.get(hidden[0]) == want_elem or (
                        len(hidden) > 1 and STEM_ELEMENTS.get(hidden[1]) == want_elem):
                    dry_strong_yinbi = True

    # 日主本气根：任一支本气 role 为比劫，且支未被合化/被冲
    day_root = any(r == "比劫" and _eff(br) for p, r in main_roles.items()
                   for br in [(pillars.get(p) or {}).get("branch") or ""])
    # 强根：本气比劫且该支为日主五行临官/帝旺（禄刃位）→ 身可自立，正格（ZC013
    # 辰戊冠带、ZP017 未己冠带为弱根，不在此列；ZP020 甲坐卯帝旺即属此）
    day_root_strong = any(
        r == "比劫" and _eff(br) and day_elem and
        twelve_growth(day_elem, br) in ("临官", "帝旺")
        for p, r in main_roles.items()
        for br in [(pillars.get(p) or {}).get("branch") or ""])
    # 藏干本气印比（如巳中丙=印、寅中甲=印）：有力生扶；被合化/被冲者失效
    hidden_strong_yinbi = any(
        r in ("印", "比劫") and _eff((pillars.get(p) or {}).get("branch") or "")
        for p, r in main_roles.items())
    # 藏干本气印（未冲/未合化，如未中己=辛金之印、子中癸=甲木之印）→ 印绶
    # 有力可用 → 身弱正格（ZP009/011/013/016/020/026/033）；无根者本气印
    # 伏藏无气仍从（ZC003 巳中庚印书从财『一点庚金临绝』、ZC009 戌中辛印
    # 书从势『印星伏而无气』——二者印在中气且日主无根，不在此列）
    hidden_benqi_yin = any(
        r == "印" and _eff((pillars.get(p) or {}).get("branch") or "")
        for p, r in main_roles.items())
    # 藏干中气印（未中丁=印、巳中庚=印等）：须与日主弱根同在才使身可自立
    # → 身弱正格（ZP009/017 未己比劫根+未丁印中气）；无根者印伏藏无气仍从
    # （ZC003 巳中庚印书从财『一点庚金临绝』、ZC009 戌中辛印书从势『印星
    # 伏而无气』）
    yin_zhongqi_hidden = day_root and any(
        d.get("role") == "印" and d.get("layer") in ("本气", "中气")
        and _eff((pillars.get(d.get("pillar") or "") or {}).get("branch") or "")
        for d in details)
    # 透干印比须坐支本气/中气为该十神五行才算有力（坐支无根 = 虚浮，不算生扶之意）
    strong_yinbi = dry_strong_yinbi or hidden_strong_yinbi
    # 透干印比坐支中气根（库中印/中气印，如 ZP003 甲印坐辰中气乙）→ 印绶可用
    # → 身弱正格，不判从弱（余气根 ZC002 戊坐寅仍判从，任注『虽生犹死』）
    dry_yinbi_zhongqi = False
    for pname in ("year", "month", "hour"):
        p = pillars.get(pname) or {}
        tg = p.get("ten_god") or ""
        br = p.get("branch") or ""
        if tg not in ("正印", "偏印") or not _eff(br):
            continue
        want_elem = {v: k for k, v in SHENG_CYCLE.items()}.get(day_elem)
        f = (chart_json.get("factors") or {}).get(pname) or {}
        hidden = f.get("hidden_stems") or []
        if len(hidden) > 1 and STEM_ELEMENTS.get(hidden[1]) == want_elem:
            dry_yinbi_zhongqi = True
    # 干透印比（无论有力与否）：仅作灰区登记参考，不直接定真假（ZC002/003/005
    # 透印比坐支无根仍为真从；ZC014/015 透干印比书判假从，属灰区，待六合化复核）

    # 从神（财/官杀/食伤）综合权重（藏干全权重 + 透干 w=1.0 + 三合局化气 +2.0）
    from_weight = weight_by_role["财"] + weight_by_role["官杀"] + weight_by_role["食伤"]
    for pname in ("year", "month", "hour"):
        tg = (pillars.get(pname) or {}).get("ten_god") or ""
        if tg in ("正财", "偏财", "正官", "偏官", "七杀", "食神", "伤官"):
            from_weight += 1.0
    if sanhe_elem and day_elem:
        from_weight += 2.0        # 三合局化气助从神（如 ZC004 寅午戌火局党杀）

    # ── 从旺/从强（专旺）：得令且旺之极 + 四支本气全印比 + 干不透财官杀食伤 + 日主有根 ──
    branch_roles = list(main_roles.values())
    dry_has_caiguansha = any(
        (pillars.get(p) or {}).get("ten_god") in ("正财", "偏财", "正官", "偏官", "七杀")
        for p in ("year", "month", "hour"))
    # 干透食伤泄秀（如 ZP022 甲子丙寅甲子丙寅 透双丙）→ 旺气有泄 → 建禄/月刃
    # 正格论，非专旺（《从象》『从旺者四柱皆比劫』，透食伤则不纯）
    dry_has_shishang = any(
        (pillars.get(p) or {}).get("ten_god") in ("食神", "伤官")
        for p in ("year", "month", "hour"))
    if ling_effective and sheng_fu >= 5.0 and day_root and branch_roles \
            and all(r in ("印", "比劫") for r in branch_roles) \
            and not dry_has_caiguansha and not dry_has_shishang:
        # 比劫本气权重 vs 印本气权重 → 从旺 / 从强
        bj = sum(1 for r in branch_roles if r == "比劫")
        yin = sum(1 for r in branch_roles if r == "印")
        kind = "从旺" if bj >= yin else "从强"
        label = f"{kind}（真从）"
        basis = (f"得令且旺之极（sheng_fu={sheng_fu:.1f}），四支本气全印比（比劫{bj}/印{yin}），"
                 "干不透财官杀，日主有根——" + _CONG["cong_wang_qiang"])
        return kind, "真从", basis, label

    # ── 从气：失令 + 日主有根 + 四支本气五行集中于金水/木火两行 ──
    if not ling_effective and day_root and branch_main_elems:
        elems = {e for e in branch_main_elems if e}
        if (elems and elems <= {"金", "水"}) or (elems and elems <= {"木", "火"}):
            kind = "从气"
            label = f"{kind}（真从）"
            basis = ("日主失令有根，四支本气集中于" + "/".join(sorted(elems)) +
                     "两行——" + _CONG["cong_qi"])
            return kind, "真从", basis, label

    # 透干比劫计数（帮身之心）：≥3 者身弱有比劫可帮 → 正格论成败
    # （ZP029 丙子丙子丁酉 透丙丙丁、ZP005 透甲丙丙；ZC010 透丙丙虽 2 仍从——
    # 任注『衰绝无气』，见 CHANGELOG 口径登记）
    dry_bijie_count = sum(
        1 for pname in ("year", "month", "hour")
        if (pillars.get(pname) or {}).get("ten_god") in ("比肩", "劫财"))

    # ── 从弱侧：从神压倒 + 日主难自立（失令，无强根、无可用印绶；无根或有印比） ──
    if from_weight >= 4.0 and not ling_effective and not day_root_strong \
            and not hidden_benqi_yin \
            and dry_bijie_count < 3 \
            and not (dry_yinbi_zhongqi or yin_zhongqi_hidden) \
            and (not day_root or strong_yinbi):
        # 主导十神：藏干全权重 + 透干 + 三合局化气
        role_score = {"财": weight_by_role["财"], "官杀": weight_by_role["官杀"],
                      "食伤": weight_by_role["食伤"]}
        for pname in ("year", "month", "hour"):
            tg = (pillars.get(pname) or {}).get("ten_god") or ""
            if tg in ("正财", "偏财"):
                role_score["财"] += 1.0
            elif tg in ("正官", "偏官", "七杀"):
                role_score["官杀"] += 1.0
            elif tg in ("食神", "伤官"):
                role_score["食伤"] += 1.0
        if sanhe_elem and day_elem:
            sanhe_role = _role_of_elem(day_elem, sanhe_elem)
            if sanhe_role in role_score:
                role_score[sanhe_role] += 2.0
        ordered = sorted(role_score.items(), key=lambda kv: kv[1], reverse=True)
        top_role, top_w = ordered[0]
        second_w = ordered[1][1] if len(ordered) > 1 else 0.0
        if top_w - second_w < 0.8:
            kind = "从势"
            # 杀势当权则不落从势（2026-10-02t，通用规则）：任注从势者须「财官食伤
            # **并旺**」势均——官杀「当令且透干」或「透干≥2（成党）」即杀势当权，
            # 非并旺，书例皆判从杀（ZC011「杀势当权…弃命从杀」卯令乙透、
            # ZC012「杀势愈旺」双壬透、ZC014 丙丁并透；对照 ZC009 辰令官**不透**
            # 书仍从势——当令而不透不成当权）。仅改 kind，真假口径不变。
            guansha_chou = sum(
                1 for pname in ("year", "month", "hour")
                if (pillars.get(pname) or {}).get("ten_god") in ("正官", "偏官", "七杀"))
            sha_dangling_tou = (main_roles.get("month") == "官杀" and guansha_chou >= 1)
            sha_shuang_tou = guansha_chou >= 2
            if sha_dangling_tou or sha_shuang_tou:
                kind = "从官杀"
                basis = ("官杀当权（%s），杀势成党非「并旺」，书例判从杀——" %
                         ("杀临月令且透干" if sha_dangling_tou else "官杀双透成党")
                         + _CONG["cong_shi"])
            else:
                basis = ("日主失令无自立，财官食伤并旺（主导差 <0.8）——"
                         + _CONG["cong_shi"])
            ftype = "真从" if (not day_root and not strong_yinbi) else "假从"
            label = f"{kind}·{ftype}"
            basis += "；生扶口径：%s" % (_CONG["sheng_fu_jue_wu"] if ftype == "真从" else _CONG["zhong_you_yin_bi"])
            # 从势（从神非唯一主导）时，某从神本气支仅一支且被异类支冲
            # （卯酉金克木、寅申金木）→ 从神缺角 → 从之不纯（ZC011 卯酉冲杀、
            # ZC012 寅申冲财）；同类相冲（辰戌库冲）不破（ZC009/001 仍真从）。
            cong_shen_chong = False
            for p, r in main_roles.items():
                br = (pillars.get(p) or {}).get("branch") or ""
                if r in ("财", "官杀", "食伤") and br in chong_map:
                    same = sum(1 for pp, rr in main_roles.items()
                               if rr == r and (pillars.get(pp) or {}).get("branch") == br)
                    if same == 1 and not _chong_same_elem(br):
                        cong_shen_chong = True
                        break
            if cong_shen_chong:
                ftype = "假从"
                label = f"{kind}·{ftype}"
                basis += "；" + _CONG["cong_shen_chong"]
            return kind, ftype, basis, label
        kind = {"财": "从财", "官杀": "从官杀", "食伤": "从儿"}[top_role]
        ftype = "真从" if (not day_root and not strong_yinbi) else "假从"
        label = f"{kind}·{ftype}"
        basis = ("从神压倒（%s=%.1f），日主失令%s——%s" % (
            top_role, top_w,
            "无本气根" if not day_root else "有本气根",
            _CONG["zhen_cong"] if ftype == "真从" else _CONG["jia_cong"]))
        return kind, ftype, basis, label

    return None, None, "", None


def judge_pattern_cheng_bai(pattern: str, chart_json: dict,
                            tentative_from: bool = False,
                            strength: str = "") -> dict:
    """格局成败救应（《子平真诠》主干）：{pattern_cheng_bai, basis}。

    判定顺序（书源「何谓成→何谓败→何谓救应」三层）：
      1. 成条件满足（书源明写的成格结构）→ 成格
      2. 否则忌神透干：救应透 → 救应成格（败中有成，全凭救应）；无救 → 破格
      3. 忌神未透 → 成格
    特判（书源原文/徐注明文的救应结构）：
      - 财格：正官/食伤透=成；七杀透（财党煞）/比劫透=败；
        救=食伤制煞生财、合煞存财；身弱透正官=破（印透生身除外）
      - 印格：忌财透，财干与日主六合 = 合财存印 → 救应成格（「或合财而存印」）
      - 建禄格：用官而伤透，伤干被合 = 去伤存官 → 救应成格（「遇伤而伤被合」）
      - 偏官格+阳刃在支（煞刃格）：印透化煞=破格（「煞刃格需要七煞抑刃，
        则偏印为破格」）
    身强条件（书源明文）：
      - 偏官格食制煞需身强（「必身煞两停者方许成格」）
      - 财格身弱透正官即破（「身弱透官，即为破格」）
    - 从格（tentative）不判成败（结构特殊，另走从格论）
    """
    if tentative_from or pattern not in PATTERN_CB_RULES:
        return {"pattern_cheng_bai": "", "basis": _CONG["cong_bu_pan"]}
    rule = PATTERN_CB_RULES[pattern]
    gods_detail = _god_detail(chart_json)
    roles = set(_role(g["god"]) for g in gods_detail)
    weak = strength == "偏弱"

    cheng_hit = [c for c in rule["cheng"] if c in roles]
    ji_hit = [c for c in rule["ji"] if c in roles]
    jiu_hit = [c for c in rule["jiu"] if c in roles]

    basis_parts = [f"月令本气十神定格={pattern}"]
    if cheng_hit:
        basis_parts.append(f"成条件透:{'/'.join(cheng_hit)}")
    if ji_hit:
        basis_parts.append(f"忌神透:{'/'.join(ji_hit)}")
    if jiu_hit:
        basis_parts.append(f"救应透:{'/'.join(jiu_hit)}")
    if weak:
        basis_parts.append("身弱")

    def _cb(label: str, quote: str) -> dict:
        return {"pattern_cheng_bai": label,
                "basis": "；".join(basis_parts) + f"——{quote}"}

    # 偏官格+阳刃在支 = 煞刃格：印透化煞则刃无制 → 破（书源第13章）
    if pattern == "偏官格" and _has_yang_ren(chart_json) and "印" in roles:
        return _cb("破格",
                   _CB["sha_ren_yin_po"])

    # 伤官格特例（书源成条件）：官杀透而印透 = 带煞佩印，直接成格，不算救应
    if pattern == "伤官格" and ("官杀" in roles) and ("印" in roles):
        return _cb("成格", _CB["shang_pei_sha_yin"])

    # 财格特判（官/煞须细分，不落通用官杀组）：
    #   正官/食伤透=成；身弱透正官=破（印透生身除外）；七杀透=败（财党煞），
    #   食伤制煞/合煞存财=救应；比劫透=败（财轻比重），食伤化劫=救应
    if pattern in ("正财格", "偏财格"):
        zheng_guan = [g for g in gods_detail if g["god"] == "正官"]
        shi_shang = [g for g in gods_detail if _role(g["god"]) == "食伤"]
        qi_sha = [g for g in gods_detail if g["god"] in ("偏官", "七杀")]
        bi_jie = [g for g in gods_detail if _role(g["god"]) == "比劫"]
        yin_tou = any(_role(g["god"]) == "印" for g in gods_detail)
        he_sha = [g for g in gods_detail
                  if qi_sha and g["stem"] != qi_sha[0]["stem"]
                  and stems_wuhe(g["stem"], qi_sha[0]["stem"])]
        if zheng_guan and weak and not yin_tou:
            return _cb("破格",
                       _CB["cai_po_shenruo_guan"])
        if zheng_guan or shi_shang:
            return _cb("成格",
                       _CB["cai_cheng_guan_shi"])
        if qi_sha:
            if shi_shang or he_sha:
                return _cb("救应成格",
                           _CB["cai_jiu_sha"])
            return _cb("破格",
                       _CB["cai_po_sha"])
        if bi_jie:
            if shi_shang:
                return _cb("救应成格",
                           _CB["cai_jiu_shi_hua"])
            return _cb("破格", _CB["cai_po_bi"])
        return _cb("成格", _CB["cheng_wu_ji"])

    # 印格特判：忌财透，财干与日主六合 = 合财存印 → 救应成格（书源「或合财而存印」）
    if pattern in ("正印格", "偏印格"):
        day_stem = ((chart_json.get("pillars") or {}).get("day") or {}).get("stem") or ""
        cai = [g for g in gods_detail if _role(g["god"]) == "财"]
        if cai and day_stem and not any(_role(g["god"]) == "比劫" for g in gods_detail):
            he_cai = [g for g in cai if stems_wuhe(g["stem"], day_stem)]
            if he_cai:
                return _cb("救应成格",
                           _CB["yin_jiu_he_cai"])

    # 建禄格特判：用官而伤透，伤干被合 = 去伤存官 → 救应成格（书源「遇伤而伤被合」）
    if pattern == "建禄格":
        zheng_guan = [g for g in gods_detail if g["god"] == "正官"]
        shang_guan = [g for g in gods_detail if g["god"] == "伤官"]
        if zheng_guan and shang_guan:
            he_shang = [g for g in gods_detail
                        if g["stem"] != shang_guan[0]["stem"]
                        and stems_wuhe(g["stem"], shang_guan[0]["stem"])]
            if he_shang:
                return _cb("救应成格",
                           _CB["jianlu_jiu_he_shang"])

    # 七杀格食伤制煞：书源「必身煞两停者方许成格」——身弱时不算成条件
    if pattern == "偏官格" and "食伤" in roles and weak:
        cheng_hit = [c for c in cheng_hit if c != "食伤"]

    if cheng_hit:
        return _cb("成格", _CB["cheng_structure"])
    if ji_hit:
        if jiu_hit:
            return _cb("救应成格", _CB["jiu_cheng"])
        return _cb("破格", _CB["po_no_jiu"])
    return _cb("成格", _CB["cheng_wu_ji"])


def _role(ten_god: str) -> str:
    return TEN_GOD_GROUP.get(ten_god, "")


def _element_of_stem(stem: str) -> str:
    return STEM_ELEMENTS.get(stem, "")


def strength_and_pattern(chart_json: dict) -> dict:
    """四柱 → {strength, strength_score, pattern, pattern_basis, useful_gods, taboo_gods}。"""
    pillars = chart_json.get("pillars") or {}
    day_stem = (pillars.get("day") or {}).get("stem") or ""
    day_elem = _element_of_stem(day_stem)
    if not day_stem:
        return {
            "strength": "未知",
            "strength_score": 0.0,
            "pattern": "未知",
            "pattern_basis": "缺日主",
            "useful_gods": [],
            "taboo_gods": [],
        }

    # 藏干十神打分
    sheng_fu = 0.0  # 印 + 比劫
    ke_xie_hao = 0.0  # 官杀 + 食伤 + 财
    month_main_god = ""
    details = []

    factors = chart_json.get("factors") or {}
    for pname in ("year", "month", "day", "hour"):
        block = factors.get(pname) or {}
        gods = block.get("ten_gods") or []
        for item in gods:
            if not isinstance(item, dict):
                continue
            god = item.get("ten_god") or ""
            layer = item.get("layer") or "本气"
            w = LAYER_WEIGHT.get(layer, 0.25)
            role = _role(god)
            # 日支比劫/印也算，但日干本身不重复计
            if role in ("印", "比劫"):
                sheng_fu += w
            elif role in ("官杀", "食伤", "财"):
                ke_xie_hao += w
            if pname == "month" and layer == "本气":
                month_main_god = god
            details.append({"pillar": pname, "god": god, "layer": layer, "role": role, "w": w})

    # 得令：月支本气五行生扶日主则 +1.2，克泄耗则 −1.2
    month_branch = (pillars.get("month") or {}).get("branch") or ""
    month_elem = BRANCH_ELEMENTS.get(month_branch, "")
    decree = 0.0
    if month_elem and day_elem:
        if month_elem == day_elem or SHENG_CYCLE.get(month_elem) == day_elem:
            decree = 1.2
            sheng_fu += decree
        elif SHENG_CYCLE.get(day_elem) == month_elem or KE_CYCLE.get(day_elem) == month_elem or KE_CYCLE.get(month_elem) == day_elem:
            decree = -1.2
            ke_xie_hao += 1.2

    score = round(sheng_fu - ke_xie_hao, 2)
    if score >= STRONG_THRESHOLD:
        strength = "偏旺"
    elif score <= WEAK_THRESHOLD:
        strength = "偏弱"
    else:
        strength = "中和"

    pattern = PATTERN_BY_MONTH_GOD.get(month_main_god, "")
    pattern_basis = ""
    if month_main_god:
        pattern = pattern or "杂气/未分类"
        pattern_basis = f"月令本气十神={month_main_god}"
    else:
        pattern = "未知"
        pattern_basis = "缺月令十神"

    # 从格可判级判定（《滴天髓·从化论/从象/假从》；机械口径见 _from_judge 文档）：
    # 真从/假从/从旺/从强/从气/从势 分级，不再只标 tentative。
    from_kind, from_type, from_basis, tentative_from = _from_judge(
        chart_json, details, day_stem, decree=decree, sheng_fu=sheng_fu)

    if strength == "偏旺":
        useful = ["官杀", "食伤", "财"]
        taboo = ["印", "比劫"]
    elif strength == "偏弱":
        useful = ["印", "比劫"]
        taboo = ["官杀", "食伤", "财"]
    else:
        useful = ["印", "财", "官杀"]  # 中和取流通
        taboo = ["比劫"]  # 防过旺

    # 格局成败救应（《子平真诠》主干；从格 tentative 不判）
    cb = judge_pattern_cheng_bai(pattern, chart_json,
                                 tentative_from=bool(tentative_from),
                                 strength=strength)

    return {
        "strength": strength,
        "strength_score": score,
        "decree_bonus": decree,
        "sheng_fu": round(sheng_fu, 2),
        "ke_xie_hao": round(ke_xie_hao, 2),
        "pattern": pattern,
        "pattern_basis": pattern_basis,
        "pattern_cheng_bai": cb["pattern_cheng_bai"],
        "pattern_cheng_bai_basis": cb["basis"],
        "tentative_special": tentative_from,
        "from_kind": from_kind,
        "from_type": from_type,
        "from_basis": from_basis,
        # 调候用神（《穷通宝鉴》月令×日主查表，内核唯一真值源 ming_tables.TIAO_HOU；
        # 原文无明文的格为 None——宁缺勿滥，不凭记忆补格）
        "tiaohou": tiaohou_of(month_branch, day_stem),
        "useful_gods": useful,
        "taboo_gods": taboo,
        "useful_basis": (
            "身旺喜克泄耗（官杀/食伤/财），身弱喜生扶（印/比劫）——扶抑用神通行口径"
            if strength != "中和"
            else "中和取五行流通（印/财/官杀）"
        ),
        "details": details,
    }


def dayun_table(chart_json: dict) -> list[dict]:
    """大运 8 步（顺逆按年干阴阳×性别；起运岁按距节气日数折算）。

    顺行取出生后下一节，逆行取出生前上一节（《渊海子平》通行口径）。
    起运：三日=一年，一日=四月（`DAYS_PER_LUCK_YEAR` / `MONTHS_PER_DAY`）；
    十神取**运干**对日主（不是运支藏干）。
    """
    from datetime import datetime
    from yishu_core.ganzhi_calendar import next_jie_after, prev_jie_before
    from yishu_core.relations import ten_god as _ten_god

    pillars = chart_json.get("pillars") or {}
    year_stem = (pillars.get("year") or {}).get("stem") or ""
    month_gz = (pillars.get("month") or {}).get("ganzhi") or ""
    gender = (chart_json.get("birth") or {}).get("gender") or ""
    day_stem = (pillars.get("day") or {}).get("stem") or ""
    birth_dt_s = (chart_json.get("birth") or {}).get("datetime") or ""

    direction = dayun_direction(year_stem, gender) if year_stem and gender else None
    if not direction or len(month_gz) < 2:
        return []

    start_age = 3.0
    start_age_months = 0
    approximate = True
    jie_name = ""
    if birth_dt_s:
        try:
            bdt = datetime.strptime(str(birth_dt_s)[:16], "%Y-%m-%d %H:%M")
            jie = next_jie_after(bdt) if direction == "forward" else prev_jie_before(bdt)
            jie_dt = jie.get("instant") if isinstance(jie, dict) else None
            jie_name = (jie.get("name") or "") if isinstance(jie, dict) else ""
            if isinstance(jie_dt, datetime):
                days = abs((jie_dt - bdt).total_seconds()) / 86400.0
                years = days / float(DAYS_PER_LUCK_YEAR)
                start_age = round(years, 1)
                # 一日=四月，把小数年折成月（粗粒度余数）
                rem_days = days - int(days / DAYS_PER_LUCK_YEAR) * DAYS_PER_LUCK_YEAR
                start_age_months = int(round(rem_days * MONTHS_PER_DAY))
                approximate = True
        except Exception:
            start_age = 3.0

    # 干支序列唯一真值源在 core（此前此处写死两份字符串，改 core 漏改即口径分叉）
    stems, branches = HEAVENLY_STEMS, EARTHLY_BRANCHES
    ms, mb = month_gz[0], month_gz[1]
    try:
        si = stems.index(ms)
        bi = branches.index(mb)
    except ValueError:
        return []

    step = 1 if direction == "forward" else -1
    out = []
    for i in range(8):
        s = stems[(si + step * (i + 1)) % 10]
        b = branches[(bi + step * (i + 1)) % 12]
        gz = s + b
        main_god = _ten_god(day_stem, s) if day_stem else None
        a0 = round(start_age + i * 10, 1)
        out.append({
            "index": i + 1,
            "ganzhi": gz,
            "start_age": a0,
            "end_age": round(a0 + 9.9, 1),
            "ten_god": main_god or "",
            "approximate": approximate,
        })
    return out


def liunian_table(chart_json: dict, n: int = 12) -> list[dict]:
    """流年干支×十神对照表（只机械对照，不批吉凶）。

    自出生年起 n 个流年；十神取流年干对日主。
    """
    from datetime import datetime
    from yishu_core.relations import ten_god as _ten_god

    pillars = chart_json.get("pillars") or {}
    year_gz = (pillars.get("year") or {}).get("ganzhi") or ""
    day_stem = (pillars.get("day") or {}).get("stem") or ""
    birth_dt_s = (chart_json.get("birth") or {}).get("datetime") or ""
    if len(year_gz) < 2:
        return []

    # 干支序列唯一真值源在 core
    stems, branches = HEAVENLY_STEMS, EARTHLY_BRANCHES
    try:
        yi, yb = stems.index(year_gz[0]), branches.index(year_gz[1])
    except ValueError:
        return []

    try:
        birth_year = datetime.strptime(str(birth_dt_s)[:10], "%Y-%m-%d").year
    except Exception:
        birth_year = datetime.now().year

    out = []
    for i in range(int(n)):
        s = stems[(yi + i) % 10]
        b = branches[(yb + i) % 12]
        gz = s + b
        out.append({
            "year": birth_year + i,
            "age": i,
            "ganzhi": gz,
            "ten_god": (_ten_god(day_stem, s) if day_stem else "") or "",
        })
    return out


def dayun_liunian_interactions(chart_json: dict, dayun: list[dict] | None = None,
                               liunian: list[dict] | None = None) -> list[dict]:
    """大运×流年机械交互因子（只对照干支关系，不批吉凶）。

    对每一组（运，年）给出：
      - 流年干对运干之十神
      - 流年支对运支：六合 / 六冲 / 三合 / 相刑 / 比和
    结构化输出供 narrate/合参消费；**禁止**据此写命运断语。
    """
    from yishu_core.relations import ten_god as _tg
    from yishu_core.symbols import (
        BRANCH_ELEMENTS,
        HE_PAIRS,
        CHONG_PAIRS,
        sanxing_hits,
        SHENG_CYCLE,
        KE_CYCLE,
    )

    pillars = chart_json.get("pillars") or {}
    day_stem = (pillars.get("day") or {}).get("stem") or ""
    if dayun is None:
        dayun = dayun_table(chart_json)
    if liunian is None:
        liunian = liunian_table(chart_json, n=12)

    he_set = {frozenset(p) for p in HE_PAIRS}
    chong_set = {frozenset(p) for p in CHONG_PAIRS}
    from yishu_core.symbols import SAN_HE_GROUPS
    sanhe = {k: set(v) for k, v in SAN_HE_GROUPS.items()}

    out = []
    for d in dayun or []:
        d_gz = d.get("ganzhi") or ""
        if len(d_gz) < 2:
            continue
        d_stem, d_branch = d_gz[0], d_gz[1]
        for y in liunian or []:
            y_gz = y.get("ganzhi") or ""
            if len(y_gz) < 2:
                continue
            y_stem, y_branch = y_gz[0], y_gz[1]
            rels = []
            # 岁运并临：大运干支 == 流年干支（《渊海子平》「岁运并临，灾殃立至」——
            # 只标记这一结构，禁止据此批吉凶）
            if d_gz == y_gz:
                rels.append({"kind": "sui_yun_bing_lin",
                             "text": f"岁运并临（大运{d_gz}=流年{y_gz}，干支相同；"
                                     "《渊海子平》有此结构之名——只标记，不批吉凶）"})
            tg = _tg(d_stem, y_stem) if day_stem else None
            if tg:
                rels.append({"kind": "ten_god_stem", "text": f"流年干{y_stem}对运干{d_stem}={tg}", "value": tg})
            pair = frozenset((d_branch, y_branch))
            if pair in he_set:
                rels.append({"kind": "liuhe", "text": f"流年支{y_branch}与运支{d_branch}六合"})
            elif pair in chong_set:
                rels.append({"kind": "liuchong", "text": f"流年支{y_branch}与运支{d_branch}六冲"})
            else:
                hits = sanxing_hits([d_branch, y_branch])
                if hits:
                    rels.append({"kind": "sanxing", "text": f"流年支{y_branch}与运支{d_branch}见{'/'.join(hits)}", "value": hits})
                for elem, bs in sanhe.items():
                    if d_branch in bs and y_branch in bs:
                        rels.append({"kind": "sanhe", "text": f"流年支{y_branch}与运支{d_branch}三合{elem}局", "value": elem})
                de, ye = BRANCH_ELEMENTS.get(d_branch), BRANCH_ELEMENTS.get(y_branch)
                if de and ye:
                    if de == ye:
                        rels.append({"kind": "bihe", "text": f"流年支{y_branch}与运支{d_branch}比和（{de}）"})
                    elif SHENG_CYCLE.get(ye) == de or SHENG_CYCLE.get(de) == ye:
                        rels.append({"kind": "sheng", "text": f"流年支{y_branch}与运支{d_branch}有相生"})
                    elif KE_CYCLE.get(ye) == de or KE_CYCLE.get(de) == ye:
                        rels.append({"kind": "ke", "text": f"流年支{y_branch}与运支{d_branch}有相克"})
            out.append({
                "year": y.get("year"),
                "liunian": y_gz,
                "dayun": d_gz,
                "dayun_index": d.get("index"),
                "start_age": d.get("start_age"),
                "relations": rels,
                "basis": "干支对照（core.relations / symbols）；只记关系，不批吉凶",
            })
    return out


# ================================================================ 四柱结构补充因子
# 以下均为**机械结构标签**，只出结构名与依据，不批吉凶（AGENTS.md 铁律三）。
# 取值层一律取自 core（SAN_HUI_GROUPS / TIGER_MONTH_STEM / CHONG_PAIRS），不另建第二份表。


def san_hui_present(pillars: dict) -> list[dict]:
    """四支中构成完整三会方局者（《三命通会》三会方局：一季三支之气全，力大于三合）。

    core.symbols.SAN_HUI_GROUPS 为唯一真值源；方局须三支全（四柱只四支，故至多一局）。
    """
    branches = [(pillars.get(k) or {}).get("branch") or ""
                for k in ("year", "month", "day", "hour")]
    bs = [b for b in branches if b]
    out = []
    for elem, grp in SAN_HUI_GROUPS.items():
        if set(grp) <= set(bs):
            out.append({"element": elem, "branches": list(grp),
                        "basis": "三会方局（《三命通会》：寅卯辰木/巳午未火/申酉戌金/亥子丑水）"})
    return out


_PILLAR_ORDER = ("year", "month", "day", "hour")
_PILLAR_LABEL = {"year": "年", "month": "月", "day": "日", "hour": "时"}

# 四柱干支关系的书源依据（地支逐字引文真值源在 data/ditian_sui.json#chapters.地支論；
# 天干合见同书 天干論「逄辛反怯」「合壬而忠」「合戊見火」等句）
_REL_BASIS = {
    "天干合": "天干五合：甲己／乙庚／丙辛／丁壬／戊癸（core.relations.STEM_WUHE）；"
              "《滴天髓·天干論》有丙辛、丁壬、戊癸相合之文；只判合之结构，不判化",
    "六合": "地支六合，两两相合（core.symbols.HE_PAIRS；通行子平）；只判合之结构，不判化",
    "六冲": "《滴天髓·地支論》「支神祇以沖為重，刑與害兮動不動」注：沖者必是相剋，所以必動",
    "六害": "《滴天髓·地支論》「支神祇以沖為重，刑與害兮動不動」；六害为地支相害（core.symbols.HARM_PAIRS）",
    "三刑": "《三命通会》三刑（無禮子卯／無恩寅巳申／恃勢丑戌未／自刑辰午酉亥）；core.symbols.sanxing_hits",
}


def pillar_relations(chart_json: dict) -> list[dict]:
    """四柱干支两两关系（天干五合 + 地支六合/六冲/六害 + 三刑）：机械结构标签，不批吉凶。

    古法：天干「甲己合土、乙庚合金…」五合（《滴天髓·天干論》「逄辛反怯」（丙辛）、
    「合壬而忠」（丁壬）、注「合戊見火」（戊癸）即是）；地支「支神祇以沖為重，
    刑與害兮動不動」（《滴天髓·地支論》）——以相冲为最重，刑、害次之。本层把年/月/日/时
    的**四干两两**与**四支两两**（各六对）按内核关系表逐一判定，并另列四支中的三刑组合
    （`sanxing_hits`）。表一律取自内核（`relations.STEM_WUHE`／`symbols.HE_PAIRS` 等），
    **不在本模块新建第二份干支关系表**（AGENTS.md §二「内核唯一真值源」）。

    诚实边界：**只判「合/冲/害/刑」之结构，不判「化」**。合化须透干、得月令等附加条件，
    本环境无对应语料可逐字核对，故不落「合化」结论（与 `shensha`/`xiao_yun` 的
    `verified=false` 同一诚实口径）。只出结构名与位置，不批吉凶（AGENTS.md 铁律三）。
    """
    pillars = chart_json.get("pillars") or {}
    he = {frozenset(p) for p in HE_PAIRS}
    chong = {frozenset(p) for p in CHONG_PAIRS}
    harm = {frozenset(p) for p in HARM_PAIRS}

    out: list[dict] = []
    for i, a in enumerate(_PILLAR_ORDER):
        for b in _PILLAR_ORDER[i + 1:]:
            sa = (pillars.get(a) or {}).get("stem") or ""
            sb = (pillars.get(b) or {}).get("stem") or ""
            if sa and sb and stems_wuhe(sa, sb):
                la, lb = _PILLAR_LABEL[a], _PILLAR_LABEL[b]
                out.append({
                    "type": "天干合",
                    "positions": [la, lb],
                    "stems": [sa, sb],
                    "text": f"{la}{lb}干{sa}{sb}合",
                    "basis": _REL_BASIS["天干合"],
                })
            ba = (pillars.get(a) or {}).get("branch") or ""
            bb = (pillars.get(b) or {}).get("branch") or ""
            if not ba or not bb:
                continue
            pair = frozenset((ba, bb))
            kind = ("六合" if pair in he else "六冲" if pair in chong
                    else "六害" if pair in harm else "")
            if not kind:
                continue
            la, lb = _PILLAR_LABEL[a], _PILLAR_LABEL[b]
            out.append({
                "type": kind,
                "positions": [la, lb],
                "branches": [ba, bb],
                "text": f"{la}{lb}支{ba}{bb}{kind}",
                "basis": _REL_BASIS[kind],
            })

    branches = [(pillars.get(k) or {}).get("branch") or "" for k in _PILLAR_ORDER]
    for name in sanxing_hits([b for b in branches if b]):
        out.append({
            "type": "三刑",
            "positions": [],
            "branches": [],
            "text": name,
            "basis": _REL_BASIS["三刑"],
        })
    return out


def tai_yuan(month_ganzhi: str) -> dict | None:
    """胎元：月柱天干进一位、地支进三位（《三命通会》胎元起法）。

    例：月柱辛巳 → 干进一位壬、支进三位申 → 胎元壬申。
    """
    if len(month_ganzhi) < 2:
        return None
    s, b = month_ganzhi[0], month_ganzhi[1]
    if s not in HEAVENLY_STEMS or b not in EARTHLY_BRANCHES:
        return None
    si = (HEAVENLY_STEMS.index(s) + 1) % 10
    bi = (EARTHLY_BRANCHES.index(b) + 3) % 12
    return {"ganzhi": HEAVENLY_STEMS[si] + EARTHLY_BRANCHES[bi],
            "basis": "月干进一位、月支进三位（《三命通会》胎元起法）"}


def liuyue_table(year_stem: str, day_stem: str = "", n: int = 12) -> list[dict]:
    """流月：正月（寅）起，五虎遁配干，顺行 n 月；十神取流月干对日主。只对照，不批吉凶。"""
    if year_stem not in TIGER_MONTH_STEM:
        return []
    start = TIGER_MONTH_STEM[year_stem]
    out = []
    for i in range(int(n)):
        b = EARTHLY_BRANCHES[(2 + i) % 12]           # 寅起
        s = HEAVENLY_STEMS[(start + i) % 10]
        out.append({
            "month_index": i + 1,
            "branch": b,
            "ganzhi": s + b,
            "ten_god": (ten_god(day_stem, s) if day_stem else "") or "",
        })
    return out


def xiao_yun_table(chart_json: dict, n: int = 12) -> list[dict]:
    """小运：自生时干支起，顺逆同大运（阳男阴女顺、阴男阳女逆），一岁一位。

    口径诚实：此系子平通行「小运补大运之不足」起法，各家于起点与顺逆有出入
    （或谓不分阴阳男顺女逆、或谓起于时柱次干支），本环境无法逐字核对原文，
    故作**机械对照**呈现，`verified` 为 false，不批吉凶（同 `shensha` 的诚实口径）。
    """
    pillars = chart_json.get("pillars") or {}
    year_stem = (pillars.get("year") or {}).get("stem") or ""
    day_stem = (pillars.get("day") or {}).get("stem") or ""
    hour_gz = (pillars.get("hour") or {}).get("ganzhi") or ""
    gender = (chart_json.get("birth") or {}).get("gender") or ""
    if len(hour_gz) < 2 or not year_stem:
        return []
    direction = dayun_direction(year_stem, gender) if gender else None
    if not direction:
        return []
    try:
        si = HEAVENLY_STEMS.index(hour_gz[0])
        bi = EARTHLY_BRANCHES.index(hour_gz[1])
    except ValueError:
        return []
    step = 1 if direction == "forward" else -1
    out = []
    for k in range(1, int(n) + 1):
        s = HEAVENLY_STEMS[(si + step * k) % 10]
        b = EARTHLY_BRANCHES[(bi + step * k) % 12]
        out.append({
            "age": k,
            "ganzhi": s + b,
            "ten_god": (ten_god(day_stem, s) if day_stem else "") or "",
            "verified": False,
        })
    return out


def _tian_ke(ganzhi_a: str, ganzhi_b: str) -> bool:
    """两柱天干五行相克（任一方向）。"""
    if len(ganzhi_a) < 1 or len(ganzhi_b) < 1:
        return False
    ea, eb = STEM_ELEMENTS.get(ganzhi_a[0]), STEM_ELEMENTS.get(ganzhi_b[0])
    if not ea or not eb:
        return False
    return KE_CYCLE.get(ea) == eb or KE_CYCLE.get(eb) == ea


def _di_chong(ganzhi_a: str, ganzhi_b: str) -> bool:
    """两柱地支相冲。"""
    if len(ganzhi_a) < 2 or len(ganzhi_b) < 2:
        return False
    return frozenset((ganzhi_a[1], ganzhi_b[1])) in {frozenset(p) for p in CHONG_PAIRS}


def tian_ke_di_chong(chart_json: dict, *, dayun: list[dict] | None = None,
                     liunian: list[dict] | None = None) -> list[dict]:
    """天克地冲：某大运柱 / 流年柱 与 **日柱** 天干相克且地支相冲（《渊海子平》有此结构之名）。

    只标记结构，禁止据此批吉凶。
    """
    pillars = chart_json.get("pillars") or {}
    day_gz = (pillars.get("day") or {}).get("ganzhi") or ""
    if len(day_gz) < 2:
        return []
    if dayun is None:
        dayun = dayun_table(chart_json)
    if liunian is None:
        liunian = liunian_table(chart_json, n=12)
    out = []
    for d in dayun or []:
        gz = d.get("ganzhi") or ""
        if _tian_ke(gz, day_gz) and _di_chong(gz, day_gz):
            out.append({"kind": "dayun", "ganzhi": gz, "vs": day_gz,
                        "start_age": d.get("start_age"),
                        "text": f"大运{gz}与日柱{day_gz}天克地冲"})
    for y in liunian or []:
        gz = y.get("ganzhi") or ""
        if _tian_ke(gz, day_gz) and _di_chong(gz, day_gz):
            out.append({"kind": "liunian", "ganzhi": gz, "vs": day_gz,
                        "year": y.get("year"),
                        "text": f"流年{gz}与日柱{day_gz}天克地冲"})
    return out


# 十神组合（《子平真诠》《渊海子平》常见组合名）：只按透干十神共现判结构，不批吉凶
TEN_GOD_COMBO_RULES = (
    ("伤官见官", ("伤官",), ("正官",),
     "伤官与正官并透（《子平真诠》「伤官见官」）"),
    ("枭神夺食", ("偏印",), ("食神",),
     "偏印与食神并透（枭神夺食结构）"),
    ("食神制杀", ("食神",), ("偏官", "七杀"),
     "食神与七杀并透（食神制杀结构）"),
)


def ten_god_combos(chart_json: dict, strength: str = "") -> list[dict]:
    """十神组合结构标签（透干层面）：伤官见官 / 枭神夺食 / 食神制杀 / 财滋弱杀。

    只出结构名与依据；不做成败吉凶论断（成败归 `judge_pattern_cheng_bai`）。
    """
    gods = {g["god"] for g in _god_detail(chart_json)}
    out = []
    for name, lhs, rhs, basis in TEN_GOD_COMBO_RULES:
        if gods & set(lhs) and gods & set(rhs):
            out.append({"name": name, "basis": basis})
    if ({"正财", "偏财"} & gods) and ({"偏官", "七杀"} & gods) and strength == "偏弱":
        out.append({"name": "财滋弱杀", "basis": "财与七杀并透而身弱（财滋弱杀结构）"})
    return out


def tong_guan(chart_json: dict) -> list[dict]:
    """日主两路「通关／关隔」结构标签（《滴天髓·通隔論》）。

    原文：「兩意本相通，中間有關隔，此關若通也，到處歡相得。」注文五例——木土而得火、
    火金而得土、土水而得金、金木而得水、水火而得木——皆是「兩行相克，中有生序中介之神
    則氣通」（如木土得火：木生火、火生土）。落到日主即子平常论的两路：

      · 官杀克身：克日主之神（官杀）与日主相战，中介为印（金克木得水），局中有印则通；
      · 身克财  ：日主克财（身财相战），中介为食伤（木克土得火），局中有食伤则通。

    判据纯机械：取四干五行 ∪ 四支本气五行为「局中所有」；两路各自若相克双方俱现，
    则为相战，再看中介之神是否亦现——现则「通关」，不现则「关隔」。只出结构名与依据，
    不批吉凶。无相战（该路之神不现）则不出条目。
    """
    pillars = chart_json.get("pillars") or {}
    present: list[str] = []
    for key in ("year", "month", "day", "hour"):
        p = pillars.get(key) or {}
        for el in (STEM_ELEMENTS.get(p.get("stem") or ""),
                   BRANCH_ELEMENTS.get(p.get("branch") or "")):
            if el and el not in present:
                present.append(el)
    day_elem = STEM_ELEMENTS.get((pillars.get("day") or {}).get("stem") or "")
    if not day_elem:
        return []
    pset = set(present)
    out = []
    # 两路：克日主者（官杀）→ 印通关；日主所克者（财）→ 食伤通关
    for name, attacker, victim, mediator_role in (
            ("官杀克身", _ke_wo(day_elem), day_elem, "印"),
            ("身财相战", day_elem, KE_CYCLE.get(day_elem, ""), "食伤")):
        if not attacker or not victim or attacker not in pset or victim not in pset:
            continue                      # 相战双方未俱现 → 无相战，不出条目
        mediator = SHENG_CYCLE.get(attacker, "")
        if not mediator:
            continue
        through = mediator in pset
        relation = f"{attacker}克{victim}"
        out.append({
            "name": name,
            "克": attacker,
            "被克": victim,
            "中介": mediator,
            "中介角色": mediator_role,
            "通关": through,
            "label": f"{name}（{relation}）：得{mediator}（{mediator_role}）通关" if through
                     else f"{name}（{relation}）：无{mediator}（{mediator_role}）为关隔",
            "basis": "《滴天髓·通隔論》：兩意本相通，中間有關隔，此關若通也，到處歡相得"
                     f"（局中{'有' if through else '无'}{mediator}）",
        })
    return out


def _ke_wo(elem: str) -> str:
    """克我者（官杀五行）：与 KE_CYCLE 逆向查表，不新建第二份表。"""
    return next((k for k, v in KE_CYCLE.items() if v == elem), "")


# ────────────────────────────────────────────────────────────────
# 病药（《神峰通考·病药说类》/《雕枯旺弱四病说类》）
# ────────────────────────────────────────────────────────────────

# 病药总纲原文（「有病方为贵，无伤不是奇；格中如去病，财禄两相随」）
BING_YAO_THESIS = "有病方为贵，无伤不是奇；格中如去病，财禄两相随"

# 五行层病药规则：主轴五行 →（病名, 药, 规则性质 provenance）
#
# **provenance 纪律**（评审 2026-10-03 要求，勿删）：
#   "source_backed_exact"        —— 原文明写该字句，可逐字回指；
#   "source_informed_generalization" —— 原文只举「土厚埋金」一例，其余四行依
#                                    「则土为诸格之病，俱喜木为医药，以去其病也」
#                                    的**通则结构**推得；书源未逐字列其余四行病名。
# 评测时两类知识不得混同（前者可直接对表，后者只能作通则回归）。
#
# 原文：「如金日干，则为土厚埋金，火日干，则为比肩太重，是则土为诸格之病，
#       俱喜木为医药，以去其病也。」
# 「土厚埋金」为逐字例；「金重伐身/火炎焚身/水泛身浮/木旺折身」为据同句通则推得。
BING_RULES_BY_KE: dict[str, tuple[str, str, str]] = {
    "土": ("土厚埋金/土重埋身", "木", "source_backed_exact"),          # 原文逐字
    "木": ("木旺折身/木多塞塞", "金", "source_informed_generalization"),  # 依「以去其病」通则推得
    "金": ("金重伐身", "火", "source_informed_generalization"),
    "火": ("火炎焚身", "水", "source_informed_generalization"),
    "水": ("水泛身浮", "土", "source_informed_generalization"),
}

# 十神层病药对：每条同样标 provenance
#   原文逐字：「如用财见比肩为病，喜见官杀为药也」——病为「比肩」二字是逐字；
#             本实现取比劫全类（含劫财）属语义扩展，故该条为 generalization。
#   原文逐字：「如用食神伤官，以印为病，喜财为药也」——「印」含正偏印，是十神大类，
#             与「比肩」同类处理，故仍记 generalization 以示口径等价性来自推得。
BING_RULES_BY_GOD: tuple[tuple[str, frozenset, str, frozenset, str, str], ...] = (
    # (病名, 病神集合, 病之说明, 药神集合, 药之说明, provenance)
    ("比肩夺财", frozenset({"比肩", "劫财"}), "用财见比肩（劫财同类）为病",
     frozenset({"正官", "偏官", "七杀"}), "喜见官杀为药", "source_informed_generalization"),
    ("枭神夺食", frozenset({"偏印"}), "用食神伤官以印为病",
     frozenset({"正财", "偏财"}), "喜财为药", "source_backed_exact"),
    ("印重财轻", frozenset({"正印", "偏印"}), "印星太旺则财星受伤",
     frozenset({"正财", "偏财"}), "宜行财运以破其印", "source_backed_exact"),
)


def bing_yao(chart_json: dict, strength: str = "") -> dict:
    """病药结构（《神峰通考·病药说类》）。

    原文病药总纲：「何以为之病？原八字中原所害之神也；何以为之药？如八字原
    有所害之字，而得一字以去之谓了，如朱子所谓各因其病而药之也。故书云：
    **有病方为贵，无伤不是奇；格中如去病，财禄两相随。**」

    两条机械路径（均为原文明写，不引申）：

      1. **五行层**：「假如人八字中，四柱纯土水…如金日干，则为土厚埋金，
         火日干，则为比肩太重，是则土为诸格之病，俱喜木为医药，以去其病也。」
         → 病是**相对于主轴**的过剩：原文举例皆以「金日干…土厚埋金」「火日干…比肩
         太重」为式，病神即主轴所惧之神。主轴取月令本气（原文「看了日干，次看了
         月令」），再依「从重者论」聚合该五行——原文明写「先看月令中此一火字起，
         又看年上或火…宜将以上各火做一处看，或为病，或非病…故曰：从重者论」，
         即**先定主轴五行，再看该五行在各柱积重**，非全盘取最重者为病。药为
         所克之神（去病即以所克之神克之），局中见药则「有药」。
      2. **十神层**：「如用财见比肩为病，喜见官杀为药也。如用食神伤官，
         以印为病，喜财为药也。」→ 病药成对共现则成立，局中见药则「有药」。

    只出结构名与依据，**不批吉凶**（AGENTS.md 铁律三）：有药不等于吉，无药不等于凶。
    藏干口径依原文自注「地支虽又藏有别物，且不必看，若再看别物，由混杂不明」——
    五行层只用四干与四支**本气**，藏干不入此层（十神层仍透干，引擎既有口径不变）。

    返回结构：{thesis, axis_element 主轴, bing 病, consumed_by_bing 十神层病药对,
    medicines, has_medicine, counts, note, basis}
    """
    pillars = chart_json.get("pillars") or {}
    # 局中五行（四干 + 四支本气；藏干不入此层，依原文自注）
    counts: dict[str, int] = {}
    for key in ("year", "month", "day", "hour"):
        p = pillars.get(key) or {}
        for el in (STEM_ELEMENTS.get(p.get("stem") or ""),
                   BRANCH_ELEMENTS.get(p.get("branch") or "")):
            if el:
                counts[el] = counts.get(el, 0) + 1
    if not counts:
        return {}
    # 主轴 = 月令本气（原文「看了日干，次看了月令」）；无月支则退日元主
    month_branch = (pillars.get("month") or {}).get("branch") or ""
    day_stem = (pillars.get("day") or {}).get("stem") or ""
    axis = BRANCH_ELEMENTS.get(month_branch) or STEM_ELEMENTS.get(day_stem) or ""
    if not axis:
        return {}
    # 病神 = 主轴所惧之神（土厚埋金之于金、木旺折身之于土……依原文五行通例）
    bing_elem_name, yao_elem, bing_prov = BING_RULES_BY_KE.get(axis, ("", "", ""))
    bing = {
        "病": bing_elem_name,
        "病之五行": axis,
        "主轴": axis,
        "所重": counts.get(axis, 0),
        "药": yao_elem,
        "药在局中": bool(yao_elem) and yao_elem in counts,
        "provenance": bing_prov,
        "basis": (f"《神峰通考·病药说类》「如八字中看了日干，次看了月令，且如月令中支中"
                  f"所属是{axis}，先看月令中此一{axis}字起，又看年上或{axis}，又看月时上"
                  f"或有{axis}，宜将以上各{axis}做一处看，或为病，或非病…故曰：从重者论」；"
                  f"本造月令={month_branch}（主轴{axis}）、日主={day_stem}，"
                  f"局中{axis}共{counts.get(axis, 0)}见。"
                  + (f"原文例「如金日干，则为土厚埋金」类此：{axis}重则"
                     f"{BING_RULES_BY_KE[axis][0]}，俱喜{yao_elem}为医药，以去其病也。"
                     if axis in BING_RULES_BY_KE else "")),
    }
    consumed: list[dict] = []
    medicines: list[dict] = []
    if yao_elem and yao_elem in counts:
        medicines.append({"药": yao_elem, "味数": counts[yao_elem],
                           "note": f"以{yao_elem}克{axis}去其病"})
    # 十神层病药成对
    gods = {g["god"] for g in _god_detail(chart_json)}
    for name, bing_gods, bing_note, yao_gods, yao_note, god_prov in BING_RULES_BY_GOD:
        if not (gods & set(bing_gods)):
            continue
        hit_yao = sorted(gods & set(yao_gods))
        consumed.append({"病": name, "所病": bing_note, "provenance": god_prov,
                         "药在局中": bool(hit_yao), "所见之药": hit_yao})
        if hit_yao:
            medicines.append({"药": name, "药神": hit_yao, "note": yao_note})
    return {
        "thesis": BING_YAO_THESIS,
        "axis_element": axis,
        "element_counts": counts,
        "bing": bing,
        "consumed_by_bing": consumed,
        "medicines": medicines,
        "has_medicine": bool(medicines),
        # 规则性质汇总：原文逐字 vs 据通例推得——两类不得混同评（评测口径用）
        "provenance": {
            "五行层": bing_prov,
            "十神层": sorted({c["provenance"] for c in consumed}) or [],
            "口径": ("source_backed_exact＝原文逐字可回指；"
                     "source_informed_generalization＝依原文通例结构推得、书源未逐字列该句。"
                     "generalization 项只作通则回归，不冒充逐字对齐。"),
        },
        "note": ("病药为《神峰通考》正说第一家紧要；此处只标病、药及其在否，"
                 "不批吉凶——有病方为贵是原文命题，落到具体命造须人工复核（铁律三）。"
                 "命例级分歧见 TECH-DEBT §2.7：书源命例取病取药落在藏干与具体字，"
                 "与本实现层级不同，故该两例不计对齐分。"),
        "basis": f"《神峰通考·病药说类》：「{BING_YAO_THESIS}」"
                 "（病＝原所害之神，药＝得一字以去之）",
    }
