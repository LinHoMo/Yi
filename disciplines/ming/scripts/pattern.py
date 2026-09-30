# -*- coding: utf-8 -*-
"""命·格局与强弱（纯机械表驱动，无命运断语）。

规则口径（通行子平，可回溯）：
- 藏干十神本/中/余气权重 1.0 / 0.5 / 0.25
- 生扶 = 印 + 比劫；克泄耗 = 官杀 + 食伤 + 财
- 身旺喜克泄耗，身弱喜生扶（《渊海子平》扶抑用神通行口径）
- 格局取月支本气十神正格名；从格条件仅作 tentative 标注
大运顺逆走 core.ming_tables.dayun_direction；起运岁数按三日=一年近似。
"""
from __future__ import annotations

from yishu_core.ming_tables import (
    canggan_ten_gods,
    dayun_direction,
    DAYS_PER_LUCK_YEAR,
    MONTHS_PER_DAY,
    tiaohou_of,
)
from yishu_core.symbols import BRANCH_ELEMENTS, STEM_ELEMENTS, SHENG_CYCLE, KE_CYCLE

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
    "正财格": {"cheng": ("食伤", "官杀"), "ji": ("比劫",), "jiu": ("食伤", "官杀")},
    "偏财格": {"cheng": ("食伤", "官杀"), "ji": ("比劫",), "jiu": ("食伤", "官杀")},
    "建禄格": {"cheng": ("官杀", "财", "食伤"), "ji": ("印",), "jiu": ("财", "食伤")},
    "月刃格": {"cheng": ("官杀",), "ji": ("食伤", "财"), "jiu": ("印",)},
}
# 伤官格补充成条件：书源「伤官旺、身主弱而透煞印」「伤官带煞而无财」亦成——
# 即官杀透而印透（带煞佩印）直接成格，不算「救应」。主表 cheng 之后特判。
SHANGGUAN_CHENG_WITH_GUANSHA = True


def _pillar_ten_gods(chart_json: dict) -> list[str]:
    """四柱天干十神（chart 已算好，直接取，不重算）。

    注意排除 **day 柱**（日主自身）：日主对日主恒为比肩，若计入会把「比劫」
    误当忌神/相神（2026-09-30s 修正，命中徐注命例比对时暴露）。
    """
    pillars = chart_json.get("pillars") or {}
    out = []
    for pname in ("year", "month", "hour"):
        tg = (pillars.get(pname) or {}).get("ten_god") or ""
        if tg:
            out.append(tg)
    return out


def judge_pattern_cheng_bai(pattern: str, chart_json: dict,
                            tentative_from: bool = False,
                            strength: str = "") -> dict:
    """格局成败救应（《子平真诠》主干）：{pattern_cheng_bai, basis}。

    判定顺序（书源「何谓成→何谓败→何谓救应」三层）：
      1. 成条件满足（书源明写的成格结构，如官逢财印、食神制煞、带煞透印）→ 成格
      2. 否则忌神透干：救应类透 → 救应成格（败中有成，全凭救应）；无救 → 破格
      3. 忌神未透 → 成格
    身强条件（书源明文）：
      - 七杀格「身强七煞逢制，煞格成也；若身强煞弱，或煞强身弱，皆不能以制伏为用，
        必身煞两停者，方许成格」→ 食伤制煞的成条件需身强
      - 财格「财旺生官，美格也，身弱透官，即为破格」→ 身弱透官直接破格
    - 从格（tentative）不判成败（结构特殊，另走从格论）
    """
    if tentative_from or pattern not in PATTERN_CB_RULES:
        return {"pattern_cheng_bai": "", "basis": "从格/未定义格不判成败"}
    rule = PATTERN_CB_RULES[pattern]
    gods = _pillar_ten_gods(chart_json)
    roles = set(_role(g) for g in gods if _role(g))
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

    # 伤官格特例（书源成条件）：官杀透而印透 = 带煞佩印，直接成格，不算救应
    if pattern == "伤官格" and ("官杀" in roles) and ("印" in roles):
        return {"pattern_cheng_bai": "成格",
                "basis": "；".join(basis_parts)
                         + "——伤官带煞而透印，格之成也（《子平真诠·论用神成败救应》）"}

    # 财格身弱透官：书源原文「身弱透官，即为破格」；
    # 但印透则印可生身（徐注刘澄如造「时透甲印……格局以成」），不落此破
    if (pattern in ("正财格", "偏财格") and "官杀" in roles and weak
            and "印" not in roles):
        return {"pattern_cheng_bai": "破格",
                "basis": "；".join(basis_parts)
                         + "——财旺生官，美格也，身弱透官，即为破格（《子平真诠·论用神成败救应》）"}

    # 七杀格食伤制煞：书源「必身煞两停者方许成格」——身弱时不算成条件
    if pattern == "偏官格" and "食伤" in roles and weak:
        cheng_hit = [c for c in cheng_hit if c != "食伤"]

    if cheng_hit:
        return {"pattern_cheng_bai": "成格",
                "basis": "；".join(basis_parts) + "——成格结构（《子平真诠·何谓成》）"}
    if ji_hit:
        if jiu_hit:
            return {"pattern_cheng_bai": "救应成格",
                    "basis": "；".join(basis_parts) + "——败中有成，全凭救应（《子平真诠》）"}
        return {"pattern_cheng_bai": "破格",
                "basis": "；".join(basis_parts) + "——忌神犯格且无救应（《子平真诠》）"}
    return {"pattern_cheng_bai": "成格",
            "basis": "；".join(basis_parts) + "——忌神未犯，格成（《子平真诠》）"}


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

    # 从格条件识别（通行子平口径，只标结构不断吉凶）：
    # 日主无根且克泄耗/生扶一方压倒 → 从弱/从强；再按主导十神细分从儿/从财/从杀/从势。
    tentative_from = None
    from_kind = None
    from_basis = ""
    if sheng_fu < 0.5 and ke_xie_hao >= 4.0:
        # 从弱：看克泄耗里谁最强
        role_score = {"官杀": 0.0, "食伤": 0.0, "财": 0.0}
        for d in details:
            r = d.get("role")
            if r in role_score:
                role_score[r] += float(d.get("w") or 0)
        top_role = max(role_score, key=role_score.get)
        from_kind = {"官杀": "从杀", "食伤": "从儿", "财": "从财"}.get(top_role, "从弱")
        tentative_from = f"{from_kind}（tentative）"
        from_basis = (
            f"生扶{sheng_fu}≈无根，克泄耗{ke_xie_hao}压倒；"
            f"主导={top_role}({role_score[top_role]})"
        )
    elif ke_xie_hao < 0.5 and sheng_fu >= 4.0:
        from_kind = "从强/专旺"
        tentative_from = f"{from_kind}（tentative）"
        from_basis = f"克泄耗{ke_xie_hao}≈无，生扶{sheng_fu}压倒（专旺结构）"

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

    stems = "甲乙丙丁戊己庚辛壬癸"
    branches = "子丑寅卯辰巳午未申酉戌亥"
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

    stems = "甲乙丙丁戊己庚辛壬癸"
    branches = "子丑寅卯辰巳午未申酉戌亥"
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
    from yishu_core.relations import ten_god as _tg, wuxing_relation as _wx
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
