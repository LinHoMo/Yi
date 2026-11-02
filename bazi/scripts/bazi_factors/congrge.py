# -*- coding: utf-8 -*-
"""congrge —— 从格可判级 (``_from_judge``) / 格局成败救应 (``judge_pattern_cheng_bai``)。
"""
from __future__ import annotations

from ._common import (
    _CB,
    _CONG,
    _god_detail,
    _has_yang_ren,
    _role,
    _role_of_elem,
    PATTERN_CB_RULES,
    SHANGGUAN_CHENG_WITH_GUANSHA,
    BRANCH_ELEMENTS,
    CHONG_PAIRS,
    HE_PAIRS,
    SAN_HE_GROUPS,
    SAN_HUI_GROUPS,
    SHENG_CYCLE,
    KE_CYCLE,
    STEM_ELEMENTS,
    STEM_YINYANG,
    stems_wuhe,
    twelve_growth,
    twelve_growth_stem,
    wuhe_hua_element,
    _HUA,
)


def _from_judge(chart_json: dict, details: list[dict], day_stem: str,
                decree: float = 0.0, sheng_fu: float = 0.0,
                strength: str = "") -> tuple:
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
      - 从弱成立 = from_weight≥4.0 且 失令 且 无有力印比根（见下方「有气生扶」）。
        旧实现在此处写的是 `(not day_root or strong_yinbi)`，与本行自述的口径相反：
        印比有力时那个 OR 反而**放行**从格。2026-10-10 按自述口径与书例改正。
      - 有气生扶（不从）= 印或比劫通根于本气/中气（余气不算）的支 **≥2 处**，
        且该支不在三合局内（根被合化为从神）、不被相邻柱之冲（紧贴之冲力专，
        隔位之冲不作拔根），且该五行不遭月令克制（囚/死不算有气）。
        书证：ZC002「戊土虽生犹死」、ZC003「一点庚金临绝」、ZC010「乙木凋枯无根」、
        ZC012「嫩木逢金，紧贴相冲，运根拔尽」、ZC013「坐下辰土…格取从官」——
        皆带印比而书仍作从；ZP004 己辛透而通根、ZP015 戌戌重根本气、
        ZP020 癸禄在子（建禄格属《子平真诠》正格）、ZP029 卯印相于子月——
        皆书不作从论，实测改正后 pattern 28/36→29/36。
      - 从旺/从强须 得令 且 sheng_fu≥5.0（「旺之极矣」），防月刃/建禄等正格误入
      - 从气须 失令 且 日主有根 且 四支本气集中于金水/木火
      - 从儿（顺局，388 批）另立一门，不走「从弱侧」：日主偏弱＋食伤有藏根（≥1.5）＋
        印/官不透干＋顺局链（食伤+财）≥4.0 且 > 印+比劫＋食伤成气（≥3.5，或 ≥3.0 且财紧贴，
        或财居首而食伤第二且差 <0.8）；书证《顺局》「从儿不管身强弱，只要吾儿又得儿」
      - 灰区（① 于 368 批部分收口，② 仍登记）：
        ① 真/假从判据＝「有本气根／有力印比／**天干层有气印比**」三者任一 → 假从。
          仍有一例书判假从而此处判真（ZC014 辛金天干丙丁庚辛）；ZC015（丁印被癸克）
          已由 368 批的天干层判据收掉。**367 批（2026-10-30）起本条由"约数"改为实测，
          并证明 ZC014 不是"再调一次阈值"能收的**：
          · 旧注写「改读任一层生扶使 ZC001/ZC005/ZC010 三例反吐、净 −1」——实测不符：
            ZC001 根本没有印比透干（戊丙丙，全是财伤），不会翻转；实际翻转的是
            ZC002/ZC003/ZC005/ZC009/ZC010 **五例**（+2 −5，净 −3，15 例中 13→10）。
            旧注的三例名单与净数一并作废，勿再引用。
          · 另测四种更细的读法（坐支藏干生之／坐支有同类根／再加"不受月令克"／
            再加"得月令旺相休"），15 例命中分别为 9／9／11／12，**没有一种超过当时的 13**。
          · **ZC014 不可能由"印比自身状态"修复**（这不是没试，是有反例的证明）：
            ZC003 与 ZC014 的印比局部配置逐项相同——同一颗庚金、同坐寅、同在寅月、
            同被丙火克——而书判 ZC003 真从（「一点庚金临绝，丙火力能锻之，从财格真」）、
            ZC014 假从。任何只读（印比干、其坐支、月令）的判据对二者返回同一个值，
            故必有一例判错。要分开它们只能引入日主/从神侧的特征（如日主克从神＝从财、
            从神克日主＝从杀），而该线索在 15 例里与"从官杀→假"高度重合（6 例从官杀
            中 5 例假，唯一反例 ZC005 因支全金局），样本不足以立判据，强立即过拟合
            （AGENTS.md §四.3）。⇒ **ZC014 一例按「读得懂、不能机械判」结案**，缺的前置是
            **从神纯度 / 日主与从神生克方向**这一层判据，未立（368 批复核后仍无变化）。
          · **ZC015 已于 368 批收掉**：落的是「天干层有气生扶」判据（见下方
            `dry_yinbi_youqi` 段）——印比透干 + 其五行得月令（旺/相/休）+ 坐支有效五行
            生我或同我 ⇒ 仍算「有微弱生扶之意」⇒ 假从；无气（囚/死/坐支不生）⇒ 真从。
            实测 15 例 13→**14**，零回归；带书证的读数变化只有 ZC015 一例。
            代价如实登记：另有 **15 例不带 `from_type` 期望的从格**由真从改判假从
            （MP158/164/356/382、MT023/465/488/489/538/539/544/546/560、ZP005/036），
            书文对它们未定性，故**不构成读数变化**，也不得据此声称"修对了"（§四.7）。
        ② 「有气生扶」阈值取 ≥2 处：单处有气根的正格（ZP004/ZP020/ZP029/ZP032 等）
          仍会误入从格而抑制成败判定，收到 1 处则 ZC009（印伏戌中）等书例反判不从，
          两侧不可同时满足，须先引入六合化气与透干通根的联合判据再复核。
    """
    if not day_stem:
        return None, None, "", None
    day_elem = STEM_ELEMENTS.get(day_stem) or ""
    if not day_elem:
        return None, None, "", None
    pillars = chart_json.get("pillars") or {}

    # 支本气角色
    main_roles = {}
    main_gods = {}
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

    # 地支互动
    sanhe_branches: set = set()
    sanhe_elem = ""
    for elem, grp in SAN_HE_GROUPS.items():
        if set(grp) <= set(branch_list):
            sanhe_elem = elem
            sanhe_branches = {b for b in branch_list if b in grp}
            break
    # 395 批：三会方局（寅卯辰／巳午未／申酉戌／亥子丑）与三合同为「成局」，
    # 从格 role_score 若只认三合，会把「申酉戌财局」的从财例判成从势（QH-C1 实测）。
    sanhui_elem = ""
    sanhui_branches: set = set()
    for elem, grp in SAN_HUI_GROUPS.items():
        if set(grp) <= set(branch_list):
            sanhui_elem = elem
            sanhui_branches = {b for b in branch_list if b in grp}
            break
    chong_map: dict = {}
    for b in branch_list:
        for o in branch_list:
            if o != b and ((b, o) in CHONG_PAIRS or (o, b) in CHONG_PAIRS):
                chong_map.setdefault(b, set()).add(o)
    chonged: set = set(chong_map)

    def _eff(br: str) -> bool:
        if br in sanhe_branches:
            return False
        if br in chong_map:
            return _chong_same_elem(br)
        return True

    def _chong_same_elem(br: str) -> bool:
        return any(BRANCH_ELEMENTS.get(o) == BRANCH_ELEMENTS.get(br)
                   for o in chong_map.get(br, ()))

    # 月令有效
    month_branch = (pillars.get("month") or {}).get("branch") or ""
    month_elem = BRANCH_ELEMENTS.get(month_branch, "")
    ling_effective = bool(
        month_elem and day_elem and _eff(month_branch) and
        (month_elem == day_elem or SHENG_CYCLE.get(month_elem) == day_elem))

    # 透干十神与坐支根气
    dry_has_yinbi = False
    dry_strong_yinbi = False
    for pname in ("year", "month", "hour"):
        p = pillars.get(pname) or {}
        tg = p.get("ten_god") or ""
        br = p.get("branch") or ""
        st = p.get("stem") or ""
        if tg in ("正印", "偏印", "比肩", "劫财"):
            dry_has_yinbi = True
            if not _eff(br):
                continue
            want_elem = ({v: k for k, v in SHENG_CYCLE.items()}.get(day_elem)
                         if tg in ("正印", "偏印") else day_elem)
            f = (chart_json.get("factors") or {}).get(pname) or {}
            hidden = f.get("hidden_stems") or []
            if hidden and want_elem:
                if STEM_ELEMENTS.get(hidden[0]) == want_elem or (
                        len(hidden) > 1 and STEM_ELEMENTS.get(hidden[1]) == want_elem):
                    dry_strong_yinbi = True

    # 日主本气根
    day_root = any(r == "比劫" and _eff(br) for p, r in main_roles.items()
                   for br in [(pillars.get(p) or {}).get("branch") or ""])
    day_root_strong = any(
        r == "比劫" and _eff(br) and day_elem and
        twelve_growth(day_elem, br) in ("临官", "帝旺")
        for p, r in main_roles.items()
        for br in [(pillars.get(p) or {}).get("branch") or ""])
    hidden_strong_yinbi = any(
        r in ("印", "比劫") and _eff((pillars.get(p) or {}).get("branch") or "")
        for p, r in main_roles.items())
    hidden_benqi_yin = any(
        r == "印" and _eff((pillars.get(p) or {}).get("branch") or "")
        for p, r in main_roles.items())
    yin_zhongqi_hidden = day_root and any(
        d.get("role") == "印" and d.get("layer") in ("本气", "中气")
        and _eff((pillars.get(d.get("pillar") or "") or {}).get("branch") or "")
        for d in details)
    strong_yinbi = dry_strong_yinbi or hidden_strong_yinbi
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

    # ── 日主「有气生扶」判定（从/不从的真正分界）───────────────────────
    # 《滴天髓·从象》原注：「绝无一毫生扶之意，财官等强甚，乃为真从」；
    # 《假从》：「中有比劫暗生，从之不真」。书例两面都有「见印比仍从」，
    # 故「有印比」本身不是分界，**印比是否「有气」**才是：
    #   有气 = 通根于本气或中气（余气不算），且该支未被三合化局取走、
    #          未被紧贴之冲拔去，且该五行不遭月令克制。
    # 书证逐条对应：ZC002「戊土虽生犹死」（春月木克土）、ZC003「一点庚金临绝」、
    # ZC010「乙木凋枯无根」（虚浮）、ZC012「嫩木逢金，紧贴相冲，运根拔尽」、
    # ZC013「坐下辰土…格取从官」（卯月木克土）；
    # 反之 ZP004 己辛透而通根、ZP015 戌戌两重本气根、ZP020 癸禄在子（建禄格
    # 本属《子平真诠》正格）、ZP029 卯印相于子月 —— 皆书不作从论。
    _ADJ = (("year", "month"), ("month", "day"), ("day", "hour"))
    _yin_elem = {v: k for k, v in SHENG_CYCLE.items()}.get(day_elem, "")

    def _hidden(pname: str) -> list[str]:
        return ((chart_json.get("factors") or {}).get(pname) or {}).get("hidden_stems") or []

    def _yinyang_state(elem: str) -> str:
        """日主之印/比五行在月令的旺相休囚死（黄金策口径，内核同表）。"""
        if not elem or not month_elem:
            return ""
        if elem == month_elem:
            return "旺"
        if SHENG_CYCLE.get(month_elem) == elem:
            return "相"
        if SHENG_CYCLE.get(elem) == month_elem:
            return "休"
        if KE_CYCLE.get(month_elem) == elem:
            return "死"
        if KE_CYCLE.get(elem) == month_elem:
            return "囚"
        return ""

    def _tightly_clashed(pname: str) -> bool:
        """该支是否被相邻柱之支相冲（紧贴之冲力专，隔位之冲不作拔根论）。"""
        br = (pillars.get(pname) or {}).get("branch") or ""
        if not br:
            return False
        for a, b in _ADJ:
            for x, y in ((a, b), (b, a)):
                bx, by = (pillars.get(x) or {}).get("branch") or "", (pillars.get(y) or {}).get("branch") or ""
                if x == pname and bx and by and ((bx, by) in CHONG_PAIRS or (by, bx) in CHONG_PAIRS):
                    return True
        return False

    def _root_pillars(elem: str) -> list[str]:
        """elem 通根（本气或中气）且未被合化/紧贴冲拔的柱。"""
        hits = []
        for pn in ("year", "month", "day", "hour"):
            br = (pillars.get(pn) or {}).get("branch") or ""
            if not br or br in sanhe_branches or _tightly_clashed(pn):
                continue
            hid = _hidden(pn)
            if len(hid) >= 2 and (STEM_ELEMENTS.get(hid[0]) == elem
                                  or STEM_ELEMENTS.get(hid[1]) == elem):
                hits.append(pn)
        return hits

    # 印/比各自有气者（不受月令克：囚/死 为受克，休/旺/相 为有气）
    _qi_roots = []
    for _e in (_yin_elem, day_elem):
        if _e and _yinyang_state(_e) in ("旺", "相", "休"):
            _qi_roots.extend(_root_pillars(_e))
    support_strong = len(set(_qi_roots)) >= 2

    # ── 天干层「有气生扶」（368 批）────────────────────────────────────
    # 《假从》任注：「局中虽有劫印，亦自顾不暇」＋「虽有比劫印绶生扶，而…」——
    # 假从的门槛不是「有没有印比透干」，而是**那点半透的印比还有没有气**：
    #   有气 → 仍算「有（微弱的）生扶之意」，从之不真 ⇒ 假从；
    #   无气（囚/死、坐支无生、根被合冲） → 「绝无一毫生扶之意」⇒ 真从。
    # 这与 `support_strong` 分工不同：那条问「有几处通根」（≥2 处即不入从格），
    # 这条问「透干的那点印比是否还有气」——1 处有气不足以自立，却足以令从之不真。
    # 书证：ZC015「时干丁火，被年上癸水克去」——丁相于卯月、坐卯得乙木生（本可有气），
    # 故其从为假；反之 ZC002「戊土虽生犹死」（戊死于寅月）、ZC003「一点庚金临绝」
    # （庚囚于寅月）、ZC005/ZC009/ZC010 的印比同属死囚，皆书判真从。
    dry_yinbi_youqi = False
    for pname in ("year", "month", "hour"):
        p = pillars.get(pname) or {}
        tg = p.get("ten_god") or ""
        if tg not in ("正印", "偏印", "比肩", "劫财"):
            continue
        br = p.get("branch") or ""
        e = STEM_ELEMENTS.get(p.get("stem") or "") or ""
        if not e or not br or _tightly_clashed(pname):
            continue
        if _yinyang_state(e) not in ("旺", "相", "休"):
            continue
        # 坐支的**有效五行**：三合局内按局五行，否则按本气。
        # 注意三合只化「根」，不化「生」——ZC015 的卯在亥卯未局内，木仍是木，仍生丁火；
        # 若照「根被合化」的写法整支排除，就会把「被合」误当成「断了生」。
        br_elem = sanhe_elem if br in sanhe_branches else BRANCH_ELEMENTS.get(br, "")
        if br_elem and (br_elem == e or SHENG_CYCLE.get(br_elem) == e):
            dry_yinbi_youqi = True
            break

    # 从神权重
    from_weight = weight_by_role["财"] + weight_by_role["官杀"] + weight_by_role["食伤"]
    for pname in ("year", "month", "hour"):
        tg = (pillars.get(pname) or {}).get("ten_god") or ""
        if tg in ("正财", "偏财", "正官", "偏官", "七杀", "食神", "伤官"):
            from_weight += 1.0
    if (sanhe_elem or sanhui_elem) and day_elem:
        from_weight += 2.0

    # ── 五行专旺格（《千里命稿》外格：曲直／炎上／稼穑／从革／润下，396 批）
    # 书证逐格：甲乙春月支全寅卯辰或亥卯未、无庚辛申酉（曲直）；丙丁夏月巳午未或寅午戌、
    # 无壬癸亥子（炎上）；戊己四季月辰戌丑未或纯土、无甲乙寅卯（稼穑）；庚辛秋月申酉戌或
    # 巳酉丑、无丙丁午未（从革）；壬癸冬月亥子丑或申子辰、无戊己未戌（润下）。
    # 「无官杀」= 天干官杀不透（合日主者不算，QH 壬合丁）且支中官杀本气不在三合/三会局内
    # （QX08 巳中丙、QX09 辰中戊、QX10 丑中己都被合化）。
    _zw_name = {"木": "曲直", "火": "炎上", "土": "稼穑", "金": "从革", "水": "润下"}
    _zw_season = {"木": ("寅", "卯", "辰"), "火": ("巳", "午", "未"),
                  "土": ("辰", "戌", "丑", "未"), "金": ("申", "酉", "戌"),
                  "水": ("亥", "子", "丑")}
    _guan = next((k for k, v in KE_CYCLE.items() if v == day_elem), "")
    _guan_tou = any(
        (STEM_ELEMENTS.get((pillars.get(pn) or {}).get("stem") or "") or "") == _guan
        and not stems_wuhe((pillars.get(pn) or {}).get("stem") or "", day_stem)
        for pn in ("year", "month", "hour"))
    _guan_br = any(
        (BRANCH_ELEMENTS.get(b) or "") == _guan
        and b not in sanhe_branches and b not in sanhui_branches
        for b in branch_list)
    _zw_group = (sanhe_elem == day_elem or sanhui_elem == day_elem
                 or (day_elem == "土" and all(BRANCH_ELEMENTS.get(b) == "土" for b in branch_list)))
    if (day_elem in _zw_name and month_branch in _zw_season.get(day_elem, ())
            and _zw_group and not _guan_tou and not _guan_br):
        kind = _zw_name[day_elem]
        key = {"木": "mu", "火": "huo", "土": "tu", "金": "jin", "水": "shui"}[day_elem]
        basis = "《千里命稿·%s格之构成》『%s』" % (kind, _CONG["zhuan_wang_" + key])
        return kind, "真从", basis, f"{kind}·真从"

    # ── 从旺/从强
    branch_roles = list(main_roles.values())
    dry_has_caiguansha = any(
        (pillars.get(p) or {}).get("ten_god") in ("正财", "偏财", "正官", "偏官", "七杀")
        for p in ("year", "month", "hour"))
    dry_has_shishang = any(
        (pillars.get(p) or {}).get("ten_god") in ("食神", "伤官")
        for p in ("year", "month", "hour"))
    if ling_effective and sheng_fu >= 5.0 and day_root and branch_roles \
            and all(r in ("印", "比劫") for r in branch_roles) \
            and not dry_has_caiguansha and not dry_has_shishang:
        bj = sum(1 for r in branch_roles if r == "比劫")
        yin = sum(1 for r in branch_roles if r == "印")
        kind = "从旺" if bj >= yin else "从强"
        label = f"{kind}（真从）"
        basis = (f"得令且旺之极（sheng_fu={sheng_fu:.1f}），四支本气全印比（比劫{bj}/印{yin}），"
                 "干不透财官杀，日主有根——" + _CONG["cong_wang_qiang"])
        return kind, "真从", basis, label

    # ── 从气
    if not ling_effective and day_root and branch_main_elems:
        elems = {e for e in branch_main_elems if e}
        if (elems and elems <= {"金", "水"}) or (elems and elems <= {"木", "火"}):
            kind = "从气"
            label = f"{kind}（真从）"
            basis = ("日主失令有根，四支本气集中于" + "/".join(sorted(elems)) +
                     "两行——" + _CONG["cong_qi"])
            return kind, "真从", basis, label

    # 从神权重（从儿/从势共用：底权重 + 透干 +1 + 三合 +2）
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
    ju_elem = sanhe_elem or sanhui_elem
    if ju_elem and day_elem:
        ju_role = _role_of_elem(day_elem, ju_elem)
        if ju_role in role_score:
            role_score[ju_role] += 2.0
    ordered = sorted(role_score.items(), key=lambda kv: kv[1], reverse=True)
    top_role, top_w = ordered[0]
    second_role, second_w = ordered[1] if len(ordered) > 1 else ("", 0.0)

    # ── 从儿（顺局，《滴天髓》十六）：食伤成气 ＋ 财为儿之儿（388 批）──
    # 书证：《顺局》诗（dz 源L5265）「从儿不管身强弱，只要吾儿又得儿」＋任注「只见儿者，
    # 食伤多也……不论身强弱者，四柱虽有比劫仍去生助食伤也；吾儿又得儿者，必要局中有财」。
    # 与从财/官的「从弱侧」门**不同**：本门不要求日主无根、不失令——「不论身强弱」是书明文；
    # 但也不许把正格食伤/伤官吞成从儿，故加四道守（均以 386 批 9 造见证与全库 0 翻转为验收）：
    #   ① **印/官透干**即不作从儿：任注「如见印绶……焉能容子」「见官杀必为已害」；
    #      9 造见证的印/官都只在支，无一透干（CE007 辰戊、CE009 亥壬皆为藏支）。
    #   ② 日主**偏弱**且食伤有藏干之根（底权重 ≥1.5）：「不论身强弱」是说比劫/禄不碍事
    #      （CE005 甲坐寅禄、CE006 戊生辰月仍从），不是说旺刃/建禄的正格也算从儿；
    #      9 造见证全为偏弱，全库中和/偏旺的食伤格 0 翻转（ZP008/MP072/MT037/MT512…）。
    #      纯透干虚浮的食伤不算成气（MT533 食伤底权重 0 → 不作从儿）。
    #   ③ 顺局链（食伤＋财）≥4.0 且 > 印＋比劫：「只见儿」「食伤多也」是量级判据。
    #   ④ 食伤须成气：≥3.5；或 ≥3.0 且财紧贴（差 <0.8）；或财居首而食伤第二且差 <0.8。
    tou_gods = {(pillars.get(pn) or {}).get("ten_god") or ""
                for pn in ("year", "month", "hour")}
    yin_tou = bool(tou_gods & {"正印", "偏印"})
    guan_tou = bool(tou_gods & {"正官", "偏官", "七杀"})
    chain_w = role_score["食伤"] + role_score["财"]
    if (strength == "偏弱" and weight_by_role["食伤"] >= 1.5
            and not yin_tou and not guan_tou
            and role_score["食伤"] > 0 and role_score["财"] > 0
            and chain_w >= 4.0
            and chain_w > weight_by_role["印"] + weight_by_role["比劫"]
            and ((top_role == "食伤"
                  and (role_score["食伤"] >= 3.5
                       or (role_score["食伤"] >= 3.0 and top_w - second_w < 0.8)))
                 or (top_role == "财" and second_role == "食伤"
                     and top_w - second_w < 0.8 and role_score["食伤"] >= 2.5))):
        kind = "从儿"
        ftype = "真从" if (not day_root and not strong_yinbi
                           and not dry_yinbi_youqi) else "假从"
        label = f"{kind}·{ftype}"
        basis = ("食伤成气（%.1f）＋财（%.1f）成顺局，印/官不透干，日主强弱不论——%s"
                 % (role_score["食伤"], role_score["财"], _CONG["cong_er"]))
        if ftype == "真从" and dry_has_yinbi:
            basis += "；" + _CONG["yinbi_wuqi"]
        return kind, ftype, basis, label

    dry_bijie_count = sum(
        1 for pname in ("year", "month", "hour")
        if (pillars.get(pname) or {}).get("ten_god") in ("比肩", "劫财"))

    # ── 从弱侧 ──
    # 旧末项写作 `(not day_root or strong_yinbi)`，与本函数 docstring 自述的口径
    # （「有根有印比者归正格」）直接相反：印比有力时 OR 反而放行了从格。
    # 现按书源改为「日主生扶有力者不入从格」。
    if from_weight >= 4.0 and not ling_effective and not day_root_strong \
            and not hidden_benqi_yin \
            and dry_bijie_count < 3 \
            and not (dry_yinbi_zhongqi or yin_zhongqi_hidden) \
            and not support_strong:
        if top_w - second_w < 0.8:
            kind = "从势"
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
            ftype = "真从" if (not day_root and not strong_yinbi
                               and not dry_yinbi_youqi) else "假从"
            label = f"{kind}·{ftype}"
            basis += "；生扶口径：%s" % (
                _CONG["yinbi_wuqi"] if (ftype == "真从" and dry_has_yinbi)
                else _CONG["sheng_fu_jue_wu"] if ftype == "真从"
                else _CONG["zhong_you_yin_bi"])
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
        ftype = "真从" if (not day_root and not strong_yinbi
                           and not dry_yinbi_youqi) else "假从"
        label = f"{kind}·{ftype}"
        basis = ("从神压倒（%s=%.1f），日主失令%s——%s" % (
            top_role, top_w,
            "无本气根" if not day_root else "有本气根",
            _CONG["zhen_cong"] if ftype == "真从" else _CONG["jia_cong"]))
        if ftype == "真从" and dry_has_yinbi:
            # 别让报告自相矛盾：此处书判真从、干上确有印比，则必须说清「那点印比无气」，
            # 不能照抄「绝无一毫生扶」——ZC002/ZC003 的书文正是这么写的（虽生犹死／临绝）。
            basis += "；" + _CONG["yinbi_wuqi"]
        return kind, ftype, basis, label

    return None, None, "", None


def judge_pattern_cheng_bai(pattern: str, chart_json: dict,
                            tentative_from: bool = False,
                            strength: str = "") -> dict:
    """格局成败救应（《子平真诠》主干）：{pattern_cheng_bai, basis}。

    判定顺序（书源「何谓成→何谓败→何谓救应」三层）：
      1. 成条件满足 → 成格
      2. 否则忌神透干：救应透 → 救应成格；无救 → 破格
      3. 忌神未透 → 成格
    """
    # 第三百二十批：从格「试探档」不再吞正格成败——《子平真诠》格局法以月令定格
    # 论成败，身弱疑似从（tentative）时书仍按正格论成败救应（ZP004/005/020/029/
    # 032/034/036 七例书答皆在正格框架）；「从格不判」只适用于确定从格（彼时
    # pattern 已是从格名，不在 PATTERN_CB_RULES，自然早退）。试探档照判 + 备注备参。
    if pattern not in PATTERN_CB_RULES:
        return {"pattern_cheng_bai": "", "basis": _CONG["cong_bu_pan"]}
    rule = PATTERN_CB_RULES[pattern]
    gods_detail = _god_detail(chart_json)
    roles = set(_role(g["god"]) for g in gods_detail)
    weak = strength == "偏弱"

    cheng_hit = [c for c in rule["cheng"] if c in roles]
    ji_hit = [c for c in rule["ji"] if c in roles]
    jiu_hit = [c for c in rule["jiu"] if c in roles]

    basis_parts = [f"月令本气十神定格={pattern}"]
    if tentative_from:
        basis_parts.append("另有从格试探未定，成败按正格论备参")
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

    # 偏官格+阳刃在支 = 煞刃格
    if pattern == "偏官格" and _has_yang_ren(chart_json) and "印" in roles:
        return _cb("破格", _CB["sha_ren_yin_po"])

    # 伤官格特例
    if pattern == "伤官格" and ("官杀" in roles) and ("印" in roles):
        return _cb("成格", _CB["shang_pei_sha_yin"])

    # 财格特判
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
            return _cb("破格", _CB["cai_po_shenruo_guan"])
        if zheng_guan or shi_shang:
            return _cb("成格", _CB["cai_cheng_guan_shi"])
        if qi_sha:
            if shi_shang or he_sha:
                return _cb("救应成格", _CB["cai_jiu_sha"])
            return _cb("破格", _CB["cai_po_sha"])
        if bi_jie:
            if shi_shang:
                return _cb("救应成格", _CB["cai_jiu_shi_hua"])
            return _cb("破格", _CB["cai_po_bi"])
        return _cb("成格", _CB["cheng_wu_ji"])

    # 印格特判：忌财透，财干与日主六合 = 合财存印
    if pattern in ("正印格", "偏印格"):
        day_stem = ((chart_json.get("pillars") or {}).get("day") or {}).get("stem") or ""
        cai = [g for g in gods_detail if _role(g["god"]) == "财"]
        if cai and day_stem and not any(_role(g["god"]) == "比劫" for g in gods_detail):
            he_cai = [g for g in cai if stems_wuhe(g["stem"], day_stem)]
            if he_cai:
                return _cb("救应成格", _CB["yin_jiu_he_cai"])

    # 建禄格特判
    if pattern == "建禄格":
        zheng_guan = [g for g in gods_detail if g["god"] == "正官"]
        shang_guan = [g for g in gods_detail if g["god"] == "伤官"]
        if zheng_guan and shang_guan:
            he_shang = [g for g in gods_detail
                        if g["stem"] != shang_guan[0]["stem"]
                        and stems_wuhe(g["stem"], shang_guan[0]["stem"])]
            if he_shang:
                return _cb("救应成格", _CB["jianlu_jiu_he_shang"])

    # 七杀格食伤制煞：身弱时不算成条件
    if pattern == "偏官格" and "食伤" in roles and weak:
        cheng_hit = [c for c in cheng_hit if c != "食伤"]

    if cheng_hit:
        return _cb("成格", _CB["cheng_structure"])
    if ji_hit:
        if jiu_hit:
            return _cb("救应成格", _CB["jiu_cheng"])
        return _cb("破格", _CB["po_no_jiu"])
    return _cb("成格", _CB["cheng_wu_ji"])


# ── 化格（《滴天髓·從化論》真/假两章，383 批）──────────────────────────────
# 化神通月令的月支集合，逐条对着书里的「生於某月」写：
#   甲己化土「生於四季」→ 辰戌丑未（土旺四季）；乙庚化金「生於秋月」→ 申酉戌；
#   丙辛化水「生於冬月」→ 亥子丑；戊癸化火「生於夏月」→ 巳午未；丁壬化木「生於春月」→ 寅卯。
_HUA_TONG_LING = {
    "土": ("辰", "戌", "丑", "未"),
    "金": ("申", "酉", "戌"),
    "水": ("亥", "子", "丑"),
    "火": ("巳", "午", "未"),
    "木": ("寅", "卯"),
}


def hua_judge(chart_json: dict) -> dict:
    """化格判定——**只出结构名（真化／假化／不化），不判吉凶**。385 批按命例重写。

    书证（《滴天髓·從化論》真/假两章 ＋ 化象段/假化章命例）：
      真化定义：「如甲日主，生於四季，單遇一位己土，在月時上作合，（在年幹不是）
                不遇壬癸甲乙庚（印，劫，官），乃為化得真」
                「又如丙辛生於冬月，（化神要通月令）戊癸生於夏月，乙庚生於秋月，
                  丁壬生於春月，獨相作合，皆為真化」
      假化定义：「日主孤弱，而遇合神，不能不化，但有暗扶日主，如合神虛弱，則化不真」
      日主前提：「日主孤弱無氣，天地人三元，絕無一毫生扶之意」
      不能从合：「合神真而且旺，日主不能从合矣」（命例 L5238）

    385 批据 10 条命例重写（384 批首测仅 3/10）：把书的**程度语**从硬否决改回程度——
      「化神要通月令」不是「非当令即假」而是**化神须有力**（当令／月生／有根／得有力之印）；
      「不遇印劫官」不是「有干即废」而是**印劫须有力**（无根或被制者不算生扶）；
      **官不作硬否决**：五组化气里四组的官是化神的印／比，只有甲己化土的庚泄化神，
      而命例 HU001（秋金当令泄化神）书仍断真化——泄不废真化；HU003 壬日见己官仍真化；
      「單遇一位」是**合神须专一**（两甲逢两己则不专 ⇒ 假化）；
      另立第三态：**日主临帝旺则旺而不从合**（不化）。

    394 批扩《千里命稿》12 造（两书合计 22 例）后补三处：
      ① **妒合两两相配**（合神数 == 日主侧同五行干数，且 ≥2）⇒ 仍算专一，帝旺 veto 让位
         （QH012「两丁两壬如璧人双双」、QH013「年丁克去月辛…仍可合时上之辛」）；
      ② **日主有本气根 ∧ 化神不通月令** ⇒ 不化（QH015；日主不孤弱，不能从合）；
      ③ 与 385 的「化神有力即可」不冲突：HU001 日主无本气根、HU010 化神当令，均仍真化。

    为什么只标结构不批吉凶：书把吉凶挂在「化神喜忌」与「岁运」上（方向），且明说
    「土遇陰寒，要火為印」这类随宜命题属**量级/取向**判断，与 363 批 `dayun_cheng_bai`、
    373 批岁运五式同一口径——本层不做。
    """
    out = {"kind": "", "type": "", "basis": "", "partner": "", "element": "",
           "tong_ling": False, "reason": ""}
    pillars = chart_json.get("pillars") or {}
    day = (pillars.get("day") or {}).get("stem") or ""
    stems = {"year": (pillars.get("year") or {}).get("stem") or "",
             "month": (pillars.get("month") or {}).get("stem") or "",
             "hour": (pillars.get("hour") or {}).get("stem") or ""}
    month_stem, hour_stem, year_stem = stems["month"], stems["hour"], stems["year"]
    month_branch = (pillars.get("month") or {}).get("branch") or ""
    day_branch = (pillars.get("day") or {}).get("branch") or ""
    if not day:
        return out

    hidden = {}
    for key in ("year", "month", "day", "hour"):
        hidden[key] = list(((chart_json.get("factors") or {}).get(key) or {})
                           .get("hidden_stems") or [])

    def root_of(stem: str) -> bool:
        """该干在任一支**本气**有根（中气以下不作根，见 383 批注）。"""
        el = STEM_ELEMENTS.get(stem) or ""
        for hs in hidden.values():
            if hs and STEM_ELEMENTS.get(hs[0]) == el:
                return True
        return False

    # 月支本气：用月支的藏干首字（藏干表按本气在前）
    month_main = (hidden.get("month") or [""])[0]
    month_elem = STEM_ELEMENTS.get(month_main) or ""

    # ① 合在月干或时干（年干不算——《書明写「在年幹不是」）；并数「与日干相合的干」个数（专一与否）
    cands = [x for x in (year_stem, month_stem, hour_stem) if x and stems_wuhe(day, x)]
    partner = ""
    if stems_wuhe(day, month_stem):
        partner = month_stem
    elif stems_wuhe(day, hour_stem):
        partner = hour_stem
    if not partner:
        out["reason"] = "无月/时干之合（《從化論》合神須在月時上作合）"
        return out
    out["partner"] = partner
    element = wuhe_hua_element(day, partner) or ""
    out["element"] = element
    if not element:
        out["reason"] = "合而无化气"
        return out
    out["kind"] = "化" + element
    out["tong_ling"] = month_branch in _HUA_TONG_LING.get(element, ())

    day_elem = STEM_ELEMENTS.get(day) or ""

    def _stem_strong(stem: str, el: str) -> bool:
        """该干在局中是否**有力**：有本气根 ∧ 未被旺令所克 ∧ 未被有力者所制。

        384/385 批命例实证（「克去壬水」「辛金无根临绝」「申金制化」「则火亦虚脱」）：
        **无根、被克、被旺令所制者，都不算"有力"**——书的程度语落在这一层，不在"有没有干"那一层。
        """
        if not el or not root_of(stem):
            return False
        if KE_CYCLE.get(month_elem) == el:      # 被旺令所克 ⇒ 虚脱（如子月之火）
            return False
        for other in stems.values():
            if not other or other == stem:
                continue
            oe = STEM_ELEMENTS.get(other) or ""
            if not oe or KE_CYCLE.get(oe) != el:
                continue
            if oe == month_elem or root_of(other):   # 被当令或有力者所制
                return False
        return True

    def _support_strong(stem: str) -> bool:
        """该干作为日主的**印或劫**时是否有力（劫＝同我，亦算生扶）。"""
        el = STEM_ELEMENTS.get(stem) or ""
        if not el:
            return False
        if el != day_elem and SHENG_CYCLE.get(el) != day_elem:
            return False            # 既非同我（劫）也不是生我（印）
        return _stem_strong(stem, el)

    def _has_strong_yuan(elem: str) -> bool:
        """化神 elem 是否得**有力**的生扶（其印有力）。"""
        for other in stems.values():
            if not other:
                continue
            oe = STEM_ELEMENTS.get(other) or ""
            if not oe or SHENG_CYCLE.get(oe) != elem:
                continue
            if _stem_strong(other, oe):
                return True
        return False

    # ② 化神是否有力：当令／月令生之／本身有根／得有力之印
    hua_strong = (month_elem == element
                  or SHENG_CYCLE.get(month_elem) == element
                  or any(STEM_ELEMENTS.get(hs[0]) == element for hs in hidden.values() if hs)
                  or _has_strong_yuan(element))

    # ③ 日主本气根：**不作硬否决**（385 批命例实证：HU010「虽时逢禄印，而化神当令…
    #    日干不得不从合而化矣」——日主有禄有印仍真化）。把关的是「**有力**的劫/印」：
    #    HU008 因「年之禄比」**有力**（年干甲得寅根）而书断假化。
    #    383 批的注仍然有效：根只认本气（否则「甲日生於四季」那条书证永远不成立）。

    # ④ 日主是否有**有力**的生扶（印/劫），合神本身不计入（它已化去）
    others = [x for x in (year_stem, month_stem, hour_stem) if x and x != partner]
    bing = any(_support_strong(x) for x in others)

    # ⑤ 合神是否专一（「單遇一位」；两甲逢两己则不专 ⇒ 假化）
    # 394 批（《千里命稿》QH012/QH013）：两合神与日主侧**两两相配**时，妒合已被配平
    # （「两丁两壬如璧人双双，何妒之有」）或被克去（「年丁克去月辛…仍可合时上之辛」），
    # 不再算「不专一」。判据：合神个数 == 日主侧同五行干数（日主本身算一个），且 ≥2。
    day_side_count = sum(1 for x in (day, year_stem, month_stem, hour_stem)
                         if x and STEM_ELEMENTS.get(x) == day_elem)
    pairing = len(cands) >= 2 and len(cands) == day_side_count
    exclusive = len(cands) <= 1 or pairing

    # ⑥ 日主临帝旺 ⇒ 旺而不从合（命例 L5238「日主不能从合矣」）
    # 干级（阴干逆行）：壬在亥＝临官而书不认其旺，癸在亥＝帝旺而书说「日主虽旺地」——
    # 五行级表分不出同五行的阴阳两干，故这里必须走 **twelve_growth_stem**（385 批内核新增）。
    # 394 批：妒合已配平时（QH012 壬子帝旺、QH013 丙午帝旺），书仍判化——帝旺 veto 让位。
    day_is_wang = bool(day_branch) and twelve_growth_stem(day, day_branch) == "帝旺"

    if day_is_wang and not pairing:
        out["type"] = "不化"
        out["basis"] = "《滴天髓·從化論》源文「%s」" % _HUA["hua_bu"]
        out["reason"] = "日主临帝旺（%s在%s），旺而不从合" % (day, day_branch)
        return out
    # 394 批（QH015）：日主**临官/帝旺（有气之禄旺）**而化神**不通月令** ⇒ 日主不孤弱，不能从合。
    # 为什么不写「有本气根」：385 批据 HU010 已证「日主本气根不作硬否决」——冠带/墓/余气根
    # 不构成「旺而不从」；只有禄/旺（临官/帝旺）才是「日主有气」。HU010 壬亥禄但化神当令
    # （卯月木通令）故仍真化；HU001 日主无禄旺（申月土不得令仍真化）。QH015 丁午临官、
    # 化神木在戌月不通 ⇒ 不化。
    branches = [(pillars.get(p) or {}).get("branch") or ""
                for p in ("year", "month", "day", "hour")]
    day_lu_wang = any(b and twelve_growth_stem(day, b) in ("临官", "帝旺") for b in branches)
    if not pairing and day_lu_wang and not out["tong_ling"]:
        out["type"] = "不化"
        out["basis"] = "《滴天髓·從化論》源文「%s」" % _HUA["hua_tong_ling"]
        out["reason"] = ("日主得禄旺（%s）、化神%s不通月令（%s月）——日主不孤弱，不能从合"
                         % (day, element, month_branch))
        return out
    if hua_strong and not bing and exclusive:
        out["type"] = "真化"
        out["basis"] = "《滴天髓·從化論》源文「%s」；「%s」" % (_HUA["hua_zhen"], _HUA["hua_tong_ling"])
        out["reason"] = ("合神专一且有力、化神有力、日主无有力生扶"
                         + ("（妒合已配平/克去）" if pairing else ""))
        return out
    out["type"] = "假化"
    out["basis"] = "《滴天髓·從化論》源文「%s」" % _HUA["hua_jia"]
    why = []
    if not exclusive:
        why.append("合神不专一（两合相并）")
    if not hua_strong:
        why.append("化神无力")
    if bing:
        why.append("日主有有力生扶")
    out["reason"] = "合而不真：" + "、".join(why)
    return out
