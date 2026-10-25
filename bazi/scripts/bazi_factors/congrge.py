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
)


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
      - 灰区（仍登记，未解）：
        ① 真/假从仍只认「无本气根且无有力印比」，故透干比劫虚浮无根而书判假从者
          此处按真从（ZC014 辛金天干丙丁庚辛、ZC015 丁印被癸克）——把 ftype 改读
          「任一层生扶」实测使 ZC001/ZC005/ZC010 三例真从反吐成假从，净 −1，故不改；
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

    # 从神权重
    from_weight = weight_by_role["财"] + weight_by_role["官杀"] + weight_by_role["食伤"]
    for pname in ("year", "month", "hour"):
        tg = (pillars.get(pname) or {}).get("ten_god") or ""
        if tg in ("正财", "偏财", "正官", "偏官", "七杀", "食神", "伤官"):
            from_weight += 1.0
    if sanhe_elem and day_elem:
        from_weight += 2.0

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
