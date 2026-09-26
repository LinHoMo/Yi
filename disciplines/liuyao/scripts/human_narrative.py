# -*- coding: utf-8 -*-
"""
解读正文生成 — 全文就是给人读的那一份，不是另贴一层「人话章节」。

写法：像懂行的人当面把卦讲清楚。
- 先接住问题，再亮结论，再讲为什么，最后说怎么做
- 术语出现时顺口带一句，不讲课、不堆字段
- 不把引擎的「N项/N分/效应0.0」原样倒出来
- 思维链与标签只作附录，正文不以「人话/古典」分栏
"""
from __future__ import annotations

try:
    from advice_framework import generate_advice, match_advice_category
except ImportError:
    from scripts.advice_framework import generate_advice, match_advice_category


def _pos_name(p) -> str:
    try:
        p = int(p)
    except Exception:
        return str(p or "")
    return {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}.get(p, f"{p}爻")


def _strength_sentence(level: str, use_cat: str, use_br: str, use_pos, yuan_moving: bool = False, yuan_greedy: bool = False) -> str:
    """把旺衰说成对这件事意味着什么——老师傅看盘的口吻，月破单列。

    改进点：
    - 不再固定套用「原神生用」的话术，改为根据原神实际动作来量体裁衣
    - 增加 yuan_moving / yuan_greedy 两个flag，区分静原神、贪合原神和动原神
    """
    loc = ""
    if use_br:
        loc = f"{use_br}"
        if use_pos:
            loc += _pos_name(use_pos)
        loc = f"（落在{loc}）"
    # 月破单独伤透
    if "月破" in str(level):
        return f"{use_cat}{loc}被月建冲破，伤透了，难办——春木秋金皆失时令，纵有援手亦力衰。"
    # 原神补充短句
    def _yuan_note() -> str:
        if yuan_greedy:
            return "原神贪合忘生，动能没传导到你，旺而无源——如炉火无薪，旺极必衰"
        if yuan_moving:
            return "原神动而生用，有外力持续托一把"
        return "原神静而不动，旺而无源，靠自己撑"

    table = {
        "极旺": f"{use_cat}{loc}得月令之气极盛，气贯充盈——底气足到可以主动往外推。{_yuan_note()}。",
        "旺": f"{use_cat}{loc}得月令之气，旺而有力。{_yuan_note()}。",
        "相": f"{use_cat}{loc}有根气，能扛事。月建生扶，'生扶拱合，时雨滋苗'之象。{_yuan_note()}。",
        "中和": f"{use_cat}{loc}不旺不弱，全看原神和动爻能不能再加把劲——此时最忌坐等，人为处便是转机。",
        "中和偏旺": f"{use_cat}{loc}略占上风，顺势推则可成。{_yuan_note()}。",
        "中和偏弱": f"{use_cat}{loc}稍显吃力。'不及者益之则利'，宜借力打力。",
        "偏弱": f"{use_cat}{loc}失令，本身底子薄，需要看有没有救——先补条件再谈结果。",
        "弱": f"{use_cat}{loc}力量薄，急着要结果容易落空。须待旺相之时。",
        "极弱": f"{use_cat}{loc}几乎使不上劲。'用神休囚已極，雖得元神生扶不能起也'——妄动必凶。",
        "休囚": f"{use_cat}{loc}处在低潮，如草木逢秋。须候时而行。",
    }
    return table.get(str(level or ""), f"{use_cat}{loc}平常，需结合动静变化再断。")


def _question_focus(question: str) -> str:
    q = question or ""
    rules = [
        (("病", "疾", "愈", "医"), "身体/病情"),
        (("婚", "姻", "嫁", "娶", "感情", "缘"), "婚姻感情"),
        (("失", "丢", "找回", "银", "物"), "失物寻回"),
        (("财", "求财", "生意", "投资", "价", "贵贱", "贸易", "银"), "财运求谋"),
        (("官", "讼", "诉", "师尊"), "官非词讼"),
        (("文书", "考试", "学业", "领"), "文书学业"),
        (("出行", "出外", "归", "回", "仆"), "行人出行"),
        (("子", "孩子", "子女"), "子女相关"),
        (("父", "母", "岳父", "长辈"), "长辈相关"),
    ]
    for kws, label in rules:
        if any(k in q for k in kws):
            return label
    return "所问之事"


def _verdict_opening(verdict: str, focus: str, pattern_label: str = "", yuan_diagnosis: str = "") -> str:
    """第一句：先接住问题、亮明结论，并直接给出最关键的一条理由。

    说明：原来的「就 fans 来说 …」句式每个卦都一样、没有信息量；
    改成「结论 + 最直接原因」格式，让读者在第一句就知道「为什么」。
    对凶象，同时说明对应阻力类型，不再用抽象的「阻力是实的」。
    """
    reason_part = ""
    if yuan_diagnosis:
        reason_part = f"，主要因为{yuan_diagnosis}"
    elif pattern_label:
        reason_part = f"，主要受「{pattern_label}」影响"

    # 正向判断
    pos_table = {
        "大吉": "这卦是顺的，天时人事都站在你这边",
        "吉": "整体能成，可以往前推，不必太犹豫",
        "平吉": "有戏，但节奏比结果更要紧——别急着要痛快结果",
    }
    neg_table = {
        "凶": f"{focus}阻力不光是面上的，六冲散离加用神独旺无源{reason_part}。硬上容易吃亏",
        "大凶": f"{focus}眼下不是发力的时候——{reason_part or '内忧外患，动不如静'}",
        "下跌": "势头偏弱，观望比追高稳妥",
        "平/不定": "先在两可之间，稳住不要急着押注",
        "平/不利": "先别急着定。事情容易反复，稳住再看更划算",
        "平": "事在两可之间，谁先动谁定局",
    }
    v = str(verdict or "")
    if v in pos_table:
        return f"就{focus}来说，{pos_table[v]}。"
    if v in neg_table:
        return f"就{focus}来说，{neg_table[v]}。"
    # fallback: 按关键词匹配
    if "凶" in v or "跌" in v:
        return f"就{focus}来说，{v}。硬上容易吃亏{reason_part}。"
    if "吉" in v and "凶" not in v:
        return f"就{focus}来说，{v}。可以顺势推进。"
    return f"就{focus}来说，卦象已明，先看关键处再定节奏。"


def _change_sentence(s4: dict, s2: dict) -> str:
    """动变：说清楚谁在动、对事情是帮还是扯后腿——融入经典占语。"""
    details = (s4.get("details") or []) if s4 else []
    if not s4 or not s4.get("has_moving_lines") or not details:
        return "卦里没有动爻——'静为无为，动为有象'，事情相对安静，吉凶主要看用神本身够不够力，而不是突然杀出什么变数。"

    details = s4.get("details") or []
    net = float(s4.get("net_effect") or 0)
    yuan = (s2.get("yuan_shen") or {}).get("category") or ""
    use_cat = s2.get("use_god_category") or "用神"

    bits = []
    for d in details:
        if not isinstance(d, dict):
            continue
        pos = _pos_name(d.get("position"))
        rel = d.get("original_relation") or ""
        role = d.get("line_role") or ""
        ct = d.get("change_type") or ""
        chg = d.get("changed_branch") or ""
        if role == "用神":
            if "回头生" in ct:
                bits.append(f"{pos}{rel}发动，变出{chg}回头来生——'动化回头生者，如潮之有源，进而不已'，用神自己有劲往上走")
            elif "回头克" in ct:
                bits.append(f"{pos}{rel}动了，却化出回头克——'刑冲克害，秋霜杀草'之象，事情容易在关键处掉链子")
            elif "反吟" in ct:
                bits.append(f"{pos}{rel}动而反吟，'反吟卦者，反复不定'，过程反复，进两步可能退一步")
            else:
                bits.append(f"{pos}{rel}有动——动静阴阳反复变迁，事情在动，不是死水一潭")
        elif role == "原神":
            if "回头生" in ct or "化合" in ct:
                bits.append(f"{pos}{rel}（助{use_cat}者）发动，等于有人在后面持续托一把——'原神生用，根深蒂固'")
            else:
                bits.append(f"{pos}{rel}（助{use_cat}者）动了，'生扶拱合，时雨滋苗'，局面背后有支撑")
        elif role == "忌神":
            if "回头克" in ct:
                bits.append(f"{pos}{rel}虽是阻力，但动化回头克——忌神自伤，阻势自解")
            elif "贪合" in str(d.get("effect_on_usegod") or "") or "合" in ct:
                bits.append(f"{pos}{rel}被合住——'贪合忘克'，一时顾不上来捣乱")
            else:
                bits.append(f"{pos}{rel}有动，此为阻力之源，要留意有人或有事来添堵")
        elif role == "仇神":
            bits.append(f"{pos}{rel}（原神所忌）亦动——须防'仇神动则助纣为虐'")
        else:
            bits.append(f"{pos}{rel or '他爻'}亦有变化")

    if not bits:
        bits.append("卦中有动，变化落在细节上，主线仍看用神")

    if net > 1.0:
        tail = "动爻对用神形成有力生扶，事有助力——'动化回头生者，如潮之有源'，这是实实在在的加码。"
    elif net < -1.0:
        tail = "动爻来克用神或化退，有负面拖累——'刑冲克害，秋霜杀草'，事情会被这处动变扯住。"
    else:
        tail = "动爻有来有往，吉凶相抵——整体既不加分也不减分，关键还在用神自身强弱和下一步走势。"
    return "；".join(bits) + "。" + tail


def _special_sentence(special, s3, s2, question: str) -> str:
    if not isinstance(special, dict):
        return ""
    pat = str(special.get("pattern") or "")
    desc = str(special.get("description") or "")
    focus = _question_focus(question)
    empty = bool(s3.get("is_empty")) if s3 else False
    strength = str((s3 or {}).get("strength_level") or "")

    if "近病逢空" in pat or "近病逢空" in desc:
        return "病气逢空，古法主近病易退——不是没事，而是病势有松动的迹象，按医嘱静养，往往比想象中快见好。"
    if "近病逢合" in pat:
        return "近病本忌缠住不放，卦里又见合，病情容易拖泥带水，别大意，该看医生就看。"
    if "合处逢冲" in pat:
        if "婚" in focus or "婚姻" in focus:
            return "卦是六合，本来利成，但日辰冲动世爻——先合后散，事情容易开头热、后面凉，别急着把话说死。"
        return f"表面有合，内里逢冲，{focus}容易先顺后挫，推进时留一手。"
    if "冲中逢合" in pat:
        return "看着像散，细处又有合来解——先难后成的路子，别在第一关就放弃。"
    if "反吟" in pat:
        return "卦带反吟，过程多半反复，不是直线走完；心里有数，就不容易被一次起落打乱。"
    # 老师傅口吻断格局，不贴标签
    if "六冲" in pat:
        return f"{focus}遇六冲——'六冲卦者，凡事主散'，聚拢为难，散开容易，须看合象来救。"
    if "六合" in pat:
        return f"{focus}遇六合——'六合卦者，凡事主聚'，利成事利合局，最怕日辰冲破。"
    if "伏吟" in pat:
        return f"{focus}遇伏吟——'伏吟卦者，呻吟不出'，事多停滞难进，须待冲动方活。"
    if "游魂" in pat:
        return f"{focus}游魂卦——'游魂者，反复不定'，主意难坚，方向易改。"
    if "归魂" in pat:
        return f"{focus}归魂卦——'归魂者，性情归拢'，虽动而终归本位。"
    if "归禄" in pat or "禄" in pat:
        return f"{focus}遇禄——古法看禄为生发之气，底气不薄。"
    if pat:
        return f"此卦另有格局：{pat}。{desc}" if desc else f"此卦另有格局：{pat}。"
    if empty and any(x in strength for x in ("旺", "相", "中和")):
        return "用神虽落空亡，却得日月生扶，空而有根——事情不是没有，而是还欠一个「落实」的时机。"
    return ""


def _timing_sentence(timing: dict, special, s3, s5: dict = None) -> str:
    """应期段：优先从 yingqi_dates 读日历日期（如 9月23日），无则回退到地支描述。"""
    # 应期日历日期（来自 s5.yingqi_dates.dates）
    dates_blob = (s5 or {}).get("yingqi_dates") or {}
    calendar_dates = (dates_blob.get("dates") or []) if isinstance(dates_blob, dict) else []
    calendar_str = ""
    if calendar_dates:
        # 取前 3 条 (date, description)
        shown = []
        for d in calendar_dates[:3]:
            shown.append(f"{d.get('date','')}({d.get('description','')})")
        calendar_str = "、".join(shown)
    # 六冲合 → 对应冲合之日
    clashing = {"子": "午", "丑": "未", "寅": "申", "卯": "酉", "辰": "戌", "巳": "亥",
                "午": "子", "未": "丑", "申": "寅", "酉": "卯", "戌": "辰", "亥": "巳"}
    combining = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
                 "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
    t = timing if isinstance(timing, dict) else {}
    keys = list(t.get("key_branches") or [])
    speed = str(t.get("speed") or "")
    use_br = str((s3 or {}).get("use_god_branch") or "")
    sp = ""
    if isinstance(special, dict):
        sp = str(special.get("pattern") or "") + str(special.get("description") or "")

    # —— 先从用神地支推应期 ——
    day_hint = ""
    if use_br:
        cl = clashing.get(use_br, "")
        co = combining.get(use_br, "")
        if "伏" in str(s3.get("is_fu", "") or ""):
            day_hint = f"冲飞神之日伏神得出"
        elif cl and co:
            day_hint = f"{use_br}日应事，逢{cl}冲、逢{co}合皆动"
        elif cl:
            day_hint = f"{use_br}日或{cl}日（{use_br}{cl}冲）应事"
        else:
            day_hint = f"{use_br}日值日之时最应"

    # —— 基础快慢 ——
    if "近病逢空" in sp or "近病" in sp:
        base = "病在近，逢空即散——快则当日、慢则数日便见松动。"
    elif speed == "应速" or "应速" in str(t.get("summary_text") or "") or "次日" in str(t.get("summary_text") or ""):
        base = "应期偏速，当日或数日内就有信号，别错过。"
    elif speed == "应迟" or "应迟" in str(t.get("summary_text") or "") or "年内" in str(t.get("summary_text") or ""):
        base = "应期偏迟，按月计，旺相之月到才应——别拿天来量。"
    else:
        base = "应期在数日到一两个月之间，不出近期。"

    if "合处逢冲" in sp or "冲中逢合" in sp or "反吟" in sp:
        base += "过程有反复，别因一次起伏就下结论。"

    if day_hint:
        base += f"具体看——{day_hint}。"
    elif keys:
        shown = "、".join(keys[:3])
        base += f"对应{shown}相关之日。"
    # 日历日期（若存在就补上精确日期；与 day_hint/keys 不冲突）
    if calendar_str:
        base += f"具体应期日历上落在：{calendar_str}。"
    return base


# ── pattern 标签 → 相关引文 pattern 映射（人工精选）──
# 每个 pattern 标签对应应该被优先引用的引文 pattern 名
_PATTERN_QUOTE_RELEVANCE: dict = {
    "六冲卦": ["六冲卦", "反吟", "伏吟", "合处逢冲"],
    "六合卦": ["六合卦", "化合", "冲中逢合", "三合"],
    "反吟": ["反吟", "六冲卦", "伏吟"],
    "伏吟": ["伏吟", "反吟"],
    "游魂": ["游魂", "归魂"],
    "归魂": ["归魂", "游魂"],
    "化合": ["化合", "六合卦", "合处逢冲", "三合成局"],
    "三合成局": ["三合成局", "六合卦", "三合"],
    "绝处逢生": ["绝处逢生", "用神旺", "回头生"],
    "回头生": ["回头生", "进神", "绝处逢生"],
    "回头克": ["回头克", "退神", "大凶"],
    "进神": ["进神", "回头生"],
    "退神": ["退神", "回头克"],
    "用神旺": ["用神旺", "绝处逢生", "回头生"],
    "用神休囚": ["用神休囚", "用神极弱"],
    "用神极弱": ["用神极弱", "用神休囚", "绝处逢生"],
    "原神绝位·用神失源": ["原神绝位·用神失源", "用神休囚"],
    "月破": ["月破", "用神空破"],
    "近病逢空": ["近病逢空即愈", "用神空破"],
    "近病逢合": ["近病逢合为凶", "六合卦"],
    "久病逢空": ["久病逢空为凶", "用神极弱"],
    "兄弟持世": ["兄弟持世", "忌神"],
    "官鬼持世": ["官鬼持世", "子孙持世"],
    "子孙持世": ["子孙持世", "官鬼持世"],
    "父母持世": ["父母持世", "兄弟持世"],
    "妻财持世": ["妻财持世", "兄弟持世"],
    "从格": ["从格", "专旺格"],
    "专旺格": ["专旺格", "从格"],
    "化格": ["化合", "三合成局"],
    "暗动": ["暗动", "伏神得出"],
    "伏神得出": ["伏神得出", "伏神不得出", "暗动"],
    "伏神不得出": ["伏神不得出", "伏神得出"],
}


def _pattern_advice_hint(pattern_tag: str, verdict: str, timing: dict) -> str:
    """根据当前卦象的 pattern 标签，返回一条场景化的附加建议。"""
    v = str(verdict or "")
    tag = str(pattern_tag or "").strip()
    if not tag:
        return ""

    # 截取日历首日期（用于具体提示）
    cal = ""
    dates_blob = (timing or {}).get("yingqi_dates") or {}
    if isinstance(dates_blob, dict):
        ds = dates_blob.get("dates") or []
        if ds:
            cal = str(ds[0].get("date", ""))

    # 场景表
    HINTS = {
        "六冲卦": "六冲主散，事不宜急进，先稳住阵脚再对冲解决；最忌讳冲动决策或仓促变动。",
        "六合卦": "六合主聚，利成事利合作；最怕冲破，近期重要决定要避开与日辰相冲的时段。",
        "反吟": "反吟主反复，同一个问题会再来第二次；不要一次定论，留出余地方能周全。",
        "伏吟": "伏吟主停滞不进，硬推不如等一等；待冲动之时自然化解，期间以守为安。",
        "游魂": "游魂主意念飘摇、方向易改；当下先把方向定下来，定下来再谈执行。",
        "归魂": "归魂主最终有归宿，过程曲折但结果能收；保持节奏，别中途改道。",
        "化合": "化合主牵绊；事先解决已有的牵绊或承诺，再着手推进新事。",
        "三合成局": "三合局成则力量集中；若合局临事，说明时机已到，可顺势推进。",
        "绝处逢生": "绝处逢生是先危后救；主动寻找那个「救」——往往是原有未注意的人或资源。",
        "回头生": "回头生动化来生，属实质助力；主动推动或会得到超出预期的正向反馈。",
        "回头克": "回头克为自伤之象；凡事宜自我检视，先解决内部阻力再图发展。",
        "进神": "进神主渐盛；可小步推进，量变积累自然成质变。",
        "退神": "退神主渐衰；凡事量力而行，别把有限的筹码耗尽。",
        "原神绝位·用神失源": f"原神虽现不动，旺而无源；唯一出路是外力救扶（冲开原神之合、待原神出空）。{cal and f'可重点留意 {cal} 前后是否出现转机。' or ''}",
        "月破": "月破失时，当前阻力偏重；待冲破之爻填实或出月后再推动更为便利。",
        "近病逢空": "逢空即散，病势不深；重在规律作息、信医嘱，一般可愈。",
        "近病逢合": "逢合易拖，病势缠绵；不可轻视，主动跟进治疗以免拖成慢性。",
        "久病逢空": "久病逢空为凶象；病情不轻，以医院专业处理为要。",
        "久病逢冲": "久病逢冲为危象；古法云\"久病逢冲必死\"，虽不必尽信，但务必重视，应速备预案。",
        "近病逢冲": "近病逢冲多主散，病势有松动的迹象；观察反应，及时调整治疗方向。",
        "兄弟持世": f"兄弟持世，他人分财或阻力较重。{cal and f'{cal} 前后注意人际关系破财事项。' or '切忌合伙和投机。'}",
        "官鬼持世": "官鬼持世多忧疑烦忧；正面可理解为有责任感，负面则防小人暗动。",
        "子孙持世": "子孙持世，医药得力、忧虑消解；整体偏松，可略放宽心。",
        "父母持世": "父母持世，文事宜成、营运多辛；打持久战心态，不被一时反复影响。",
        "妻财持世": "妻财持世，利财赋事；但仍以用神旺衰定胜负，别因持世轻敌。",
        "从格": "从格反其势而用之；顺势强的一边，别做逆势挣扎。",
        "专旺格": "专旺格一方气盛；最怕冲破，宜以守代攻。",
        "化格": "化格主力量集中转化；若化向生扶方向，则事多顺，反之则宜慎。",
        "暗动": "暗动主他人作事、事出意外而不觉；暗中有人助，不必外求，但别因此大意。",
        "伏神得出": "伏神得出，潜在助力出现；可主动靠近原以为不可能的资源或人。",
        "伏神不得出": "伏神不得出，事情一个关键之处被压着没被看见；先找出那个被遮蔽的因素。",
    }
    return HINTS.get(tag, "")


def _extract_pattern_tags(tc: dict) -> set:
    """从 reasoning_chain 提取标准化格局标签集合（含所有「格局-」前缀 tag）。"""
    tags: set = set()
    chain = tc.get("reasoning_chain") or []
    for entry in chain:
        s = str(entry)
        if "[格局]" in s:
            # 解析：[格局] 格局-六冲 | 六冲 | 六冲卦 | 变卦六冲
            try:
                body = s.split("]", 1)[1].strip()
                for token in body.split("|"):
                    t = token.strip()
                    if not t:
                        continue
                    # 去掉"格局-"前缀存入 set，与原标签同存
                    tags.add(t)
                    if t.startswith("格局-"):
                        tags.add(t[3:])
                    else:
                        tags.add("格局-" + t)
            except Exception:
                continue
        elif "[格局要点]" in s:
            try:
                body = s.split("]", 1)[1].strip()
                for token in body.split("|"):
                    t = token.strip()
                    if t:
                        tags.add(t)
            except Exception:
                continue
    # 从 step5.special_pattern 补充
    sp = (tc.get("step5_synthesis") or {}).get("special_pattern") or {}
    if isinstance(sp, dict) and sp.get("pattern"):
        tags.add(str(sp["pattern"]))
    return tags


def _select_relevant_quotes(tc: dict) -> list:
    """按 reasoning_chain 中卦象格局标签打分，选出最相关的 2 条引文。

    评分规则：
    - 引文 pattern 在 reasoning_chain 「格局-」标签中出现，+3（几乎精确命中）
    - 引文 pattern 在本 pattern 的 _PATTERN_QUOTE_RELEVANCE 展开集合里出现，+1（间接相关）
    - 完全不相关（如「兄弟持世」在兄持与世爻无关的卦象中），-5（排除）
    - 同样相关度保留数据库中的原始顺序（前入先出）
    """
    tags = _extract_pattern_tags(tc)
    if not tags:
        # 退化：直接按数据库顺序取前 2 条
        raw = (tc.get("step5_synthesis", {}) or {}).get("classical_quotes") or []
        return [{"source": q.get("source", "经典"), "quote": q.get("quote")} for q in raw[:2] if isinstance(q, dict) and q.get("quote")]

    raw_quotes = (tc.get("step5_synthesis", {}) or {}).get("classical_quotes") or []
    scored: list = []
    for idx, q in enumerate(raw_quotes):
        if not isinstance(q, dict) or not q.get("quote"):
            continue
        qp = str(q.get("pattern") or "")
        score = 0
        # 直接命中：引文 pattern 与某个 tag 完全一致
        if qp in tags:
            score += 3
        # 子串命中：某个 tag 字符串包含引文 pattern（如 tag 是"回头生、回头生、变出未"，qp="回头生"）
        # 排除自身已经被 exact 命中；这给出+1 兜底
        for real_tag in tags:
            if qp != real_tag and qp in real_tag and len(qp) >= 2:
                score += 1
                break
        # 间接命中：当前卦象的某个 tag，其推荐引用集合包含本引文 pattern
        # （查表方向：tag → 推荐引文集合；命中条件：本引文的 pattern 在推荐集合中）
        for real_tag in tags:
            related = _PATTERN_QUOTE_RELEVANCE.get(real_tag, [])
            if qp in related:
                score += 1
        # 反向间接命中：引文 pattern 作为 tag 展开时，包含当前某个 tag
        # （即"引文自己推荐的 tags"与当前卦象 tag 集合有重叠）
        forward_related = _PATTERN_QUOTE_RELEVANCE.get(qp, [])
        for fr in forward_related:
            if fr in tags:
                score += 1
        # 优先数据库顺序（排序稳定性用 idx 保底）
        scored.append((score, -idx, q))
    # 按 (score ASC因为用了-idx, 降序排列 = score DESC, idx ASC)
    scored.sort(key=lambda x: (-x[0], x[1]))
    # 过滤掉 score <= 0 的（避免引用与本卦无关的引文）
    filtered = [item for item in scored if item[0] > 0]
    # 全部退化情况
    top = filtered[:2] if filtered else scored[:2]
    return [{"source": q.get("source", "经典"), "quote": q.get("quote")} for _, _, q in top]


def _meaning_paragraph(verdict, s2, s3, special, question, factor_contribs=None) -> str:
    """第五段：综合定性 + 精简引用关键因子。

    改进点：
    - 消除原来硬凑「原神当权阻力实在」这类与实际数据矛盾的套话
    - 改为直接引用 factor_contributions 里已有的因子名+理由（**不暴露评分数字**）
    - 去掉「事难成，守住等时机」这类与 advice 重复的表述
    - 内部评分是回归审计用的对齐分，不等于预测能力，不对外暴露（AGENTS.md §三）
    """
    use_cat = s2.get("use_god_category") or "用神"
    yuan = (s2.get("yuan_shen") or {}).get("category") or ""
    ji = (s2.get("ji_shen") or {}).get("category") or ""
    strength = str(s3.get("strength_level") or "") if s3 else ""
    focus = _question_focus(question)

    vdir = 1 if ("吉" in str(verdict) and "凶" not in str(verdict) and "不利" not in str(verdict)) else (
        -1 if ("凶" in str(verdict) or "跌" in str(verdict) or "不利" in str(verdict)) else 0
    )

    parts = []
    # —— 一言定性（精简、不再与 p1 重复） ——
    if vdir > 0:
        parts.append(f"方向可以推进，但别贪。")
    elif vdir < 0:
        parts.append(f"风头不利，暂把现有局面稳住更划算。")
    else:
        parts.append(f"事在两可之间，谁先动谁定局。")

    # —— 引用 factor_contributions 关键项（只说因子名+理由，不带评分数字） ——
    if factor_contribs:
        pos_items = [fc for fc in factor_contribs if (fc.get("score") or 0) > 0][:2]
        neg_items = [fc for fc in factor_contribs if (fc.get("score") or 0) < 0][:2]
        if pos_items:
            pos_strs = []
            for fc in pos_items:
                nm = fc.get("name", "")
                reason = _clean_reason(fc.get("reason", ""), nm)
                pos_strs.append(f"{nm}" + (f"（{reason}）" if reason else ""))
            parts.append("有利面：" + "；".join(pos_strs) + "。")
        if neg_items:
            neg_strs = []
            for fc in neg_items:
                nm = fc.get("name", "")
                reason = _clean_reason(fc.get("reason", ""), nm)
                neg_strs.append(f"{nm}" + (f"（{reason}）" if reason else ""))
            parts.append("拖累面：" + "；".join(neg_strs) + "。")

    # —— 弱而格吉/弱而格凶，点一句 ——
    if any(x in strength for x in ("弱", "囚", "死")) and vdir > 0:
        parts.append("用神虽弱，却得格局生扶——'绝处逢生'之象，成可成，心力要花够。")
    if any(x in strength for x in ("弱", "囚", "死")) and vdir <= 0:
        parts.append("用神弱叠不利——'克多出暴'之险，此时当守不宜攻。")
    if "冲中逢合" in str(special or ""):
        parts.append("冲中逢合，先难后成——过前面那关才谈得到后面的合。")
    if "回头克" in str(special or ""):
        parts.append("回头克为'自伤'——阻力从内在格局生，稳住节奏便是破法。")

    return "".join(parts)


def _clean_reason(reason: str, name: str) -> str:
    """去掉 factor_contribution.reason 里的技术备注，只留 15 字内的人类可读短句。"""
    if not reason:
        return ""
    import re
    r = re.sub(r"[（(]\s*[+-]?\d+[\d.]*[%]?\s*[）)]", "", reason)
    r = re.sub(r"【[^】]*】", "", r)
    r = r.replace(name, "")
    r = r.strip("，。：:, ")
    r = re.split(r"[，。；,;]", r, maxsplit=1)[0]
    if len(r) > 15:
        r = r[:15]
    return r.strip() or ""


def _ensure_thinking_chain(result: dict) -> dict:
    """已停用——铁律一合规清理。

    此函数曾内置一套独立的五行旺衰打分、进退神判断与五步思维链重建逻辑，
    与主线 chain_step1–5 形成双路径。按 AGENTS.md §二"内核唯一真值源"的要求，
    同一套推演规则（当令旺衰、进退神、三合局等）只应由链式模块一处实现，
    不应在此就地重算来"兜底"。

    当 thinking_chain 不可用时，正确做法是修复上游 chain_step1–5 的生成流程，
    而不是调一套平行逻辑绕过它。故改为显式拒绝，防止意外触发。
    """
    raise RuntimeError(
        "thinking_chain 缺失，不应在交付路径外就地重建——"
        "请检查上游 analyze / run_thinking_chain 是否执行成功；"
        "铁律一（AGENTS.md §一）要求机械运算统一由主线引擎完成。"
    )


def _build_explain_summary(factor_contribs: list, focus: str) -> str:
    """将 factor_contributions 翻译成人话段落，而非字段罗列。

    输出格式例：
        「推因：用神旺衰给力（+1.9），动变效应拖累（-0.4），
         六神辅助略助（+0.1）。综合看是用神有力为主，变爻有些牵制，
         所以对于财运来说，根基是稳的但过程会有些波折。」
    """
    if not factor_contribs:
        return "各因子均衡，无明显偏向。"

    top = [fc for fc in factor_contribs[:6] if fc.get("score", 0) != 0]
    if not top:
        return "各因子均衡，无明显偏向。"

    # 按正负分组
    positive = [fc for fc in top if fc.get("score", 0) > 0]
    negative = [fc for fc in top if fc.get("score", 0) < 0]

    def _short_reason(reason: str, name: str) -> str:
        """把 factor_contributions 里的技术备注翻译成短句。
        原则：15 字以内、去掉内部评分、只留核心含义。
        """
        if not reason:
            return ""
        import re
        # 去掉括号中的数字评分、书名号内部备注等
        r = re.sub(r"[（(]\s*[+-]?\d+[\d.]*[%]?\s*[）)]", "", reason)
        r = re.sub(r"【[^】]*】", "", r)  # 去掉【...】内的内部标注
        r = r.replace(name, "")  # 去掉与name重复的词
        r = r.strip("，。：:, ")
        # 截断到第一个停止符或前15字
        r = re.split(r"[，。；,;]", r, maxsplit=1)[0]
        if len(r) > 15:
            r = r[:15]
        r = r.strip()
        if not r or len(r) <= 1:
            return ""
        return r

    pos_parts = []
    for fc in positive[:3]:
        name = fc.get("name", "")
        reason = _short_reason(fc.get("reason", ""), name)
        tail = f"（{reason}）" if reason else ""
        pos_parts.append(f"{name}{tail}")

    neg_parts = []
    for fc in negative[:3]:
        name = fc.get("name", "")
        reason = _short_reason(fc.get("reason", ""), name)
        tail = f"（{reason}）" if reason else ""
        neg_parts.append(f"{name}{tail}")

    if pos_parts and neg_parts:
        body_text = "；".join(pos_parts) + "；拖累面：" + "；".join(neg_parts)
        summary = f"{focus}吉凶相杂，宜稳扎稳打。"
        header = "推因 —— 利好面"
    elif pos_parts:
        body_text = "；".join(pos_parts)
        summary = f"{focus}有明确助力，可顺势而为。"
        header = "推因 —— 利好面"
    else:
        body_text = "；".join(neg_parts)
        summary = f"{focus}阻力不小，宜谨慎守待时机。"
        header = "推因 —— 拖累面"

    return f"{header}：{body_text}。{summary}"


def build_human_narrative(result: dict) -> dict:
    """
    生成完整解读正文（唯一交付口吻）。
    兼容旧字段名，便于报告/门户复用。
    """
    # 确保 thinking_chain 数据可用（缺失时从引擎原始 JSON 推导）
    if not result.get("thinking_chain"):
        result = dict(result)  # 浅拷贝避免污染原始数据
        result["thinking_chain"] = _ensure_thinking_chain(result)

    tc = result.get("thinking_chain") or {}
    s1 = tc.get("step1_situational_reading") or {}
    s2 = tc.get("step2_use_god_identification") or {}
    s3 = tc.get("step3_strength_analysis") or {}
    s4 = tc.get("step4_change_analysis") or {}
    s5 = tc.get("step5_synthesis") or {}

    question = result.get("question") or ""
    hex_name = (result.get("original_hexagram") or {}).get("name") or s1.get("hexagram_name") or ""
    changed_name = ((result.get("changed_hexagram") or {}).get("name")) or ""
    palace = (result.get("original_hexagram") or {}).get("palace") or s1.get("palace") or ""
    generation = (result.get("original_hexagram") or {}).get("generation") or ""
    dt = result.get("divination_time") or {}
    empty = result.get("empty_branches") or []

    verdict = s5.get("verdict") or "未知"
    score = s5.get("final_score")
    conf = s5.get("confidence")
    use_cat = s2.get("use_god_category") or "用神"
    use_el = s2.get("use_god_element") or ""
    use_br = (s2.get("selected_use_god") or {}).get("earthly_branch") or s3.get("use_god_branch") or ""
    use_pos = (s2.get("selected_use_god") or {}).get("position")
    strength = s3.get("strength_level") or ""
    timing = s5.get("timing") or {}
    special = s5.get("special_pattern") or {}
    special_pat = special.get("pattern") if isinstance(special, dict) else ""
    # factor_contributions —— 用于开头句精确引用关键因子
    factor_contribs = s5.get("factor_contributions") or []
    # yuan_status: 从 factor_contributions 判断原神实际状态
    yuan_greedy = any("贪合" in str(fc.get("factor", "")) for fc in factor_contribs)
    yuan_diagnosis = ""
    for fc in factor_contribs:
        n = str(fc.get("name", ""))
        r = str(fc.get("reason", ""))
        if "原神" in n or "原神" in r:
            yuan_diagnosis = r
            break
    # yuan_moving：原神是否发动 —— 看 yuan_shen positions 中有无 is_moving
    yuan_data = s2.get("yuan_shen", {}) or {}
    yuan_moving = any(
        (p or {}).get("is_moving") for p in (yuan_data.get("positions") or [])
    ) if isinstance(yuan_data, dict) else False
    # pattern_label：用于开头句精简引用
    pattern_label = ""
    if isinstance(special, dict) and special.get("pattern") is not None:
        pattern_label = str(special["pattern"])
    # 若 special_pattern 为空，从 reasoning_chain 格局标签取第一个做兜底
    if not pattern_label:
        fallback_tags = _extract_pattern_tags(tc)
        # 优先顺序：六冲六合 > 反吟伏吟 > 游魂归魂 > 回头生克 > 伏藏 > 持世 > 病疾
        _priority = ["久病逢空", "久病逢冲", "近病逢空", "近病逢合",
                     "六冲卦", "六合卦", "反吟", "伏吟", "游魂", "归魂",
                     "回头生", "回头克", "化格", "三合成局", "绝处逢生",
                     "伏神得出", "伏神不得出", "暗动", "官鬼持世",
                     "兄弟持世", "子孙持世", "父母持世", "妻财持世",
                     "原神绝位·用神失源", "月破"]
        for p in _priority:
            if p in fallback_tags:
                pattern_label = p
                break

    focus = _question_focus(question)

    # —— 正文：连续几段，读起来就是一份完整解读 ——
    title_bits = []
    if question:
        # 取问题里较短的关键词，避免整句古籍占辞当标题
        title_bits.append(focus)
    if hex_name:
        title_bits.append(hex_name + ("之" + changed_name if changed_name else "卦"))
    title = " · ".join(title_bits) if title_bits else "六爻解读"

    hex_desc = f"{hex_name}"
    if palace or generation:
        hex_desc += f"（{palace}宫{('·' + generation) if generation else ''}）"
    if changed_name:
        hex_desc += f"，变卦{changed_name}"
    time_desc = ""
    if dt:
        time_desc = f"{dt.get('month_stem_branch','')}月 {dt.get('day_stem_branch','')}日".strip()
    empty_desc = f"旬空{('、'.join(empty))}" if empty else ""

    # 第1句：结论 + 最关键一条理由（避免「就?来说?」空句式）
    p1 = _verdict_opening(verdict, focus, pattern_label, yuan_diagnosis)
    scene = f"这副卦是{hex_desc}"
    if time_desc:
        scene += f"，起卦于{time_desc}"
    if empty_desc:
        scene += f"，{empty_desc}"
    p1 += scene + "。"

    # 第2句：旺衰 + 原神实际状态（静/贪合/发动），避免固定套话
    p2 = (
        f"事情的关键看{use_cat}"
        + (f"（五行属{use_el}）" if use_el else "")
        + (f"，落在{use_br}{_pos_name(use_pos)}" if use_br else "")
        + "。"
        + _strength_sentence(strength, use_cat, use_br, use_pos,
                             yuan_moving=yuan_moving, yuan_greedy=yuan_greedy)
    )

    p3 = _change_sentence(s4, s2)
    p4 = _special_sentence(special, s3, s2, question)
    p5 = _meaning_paragraph(verdict, s2, s3, special, question, factor_contribs)

    body = [x for x in (p1, p2, p3, p4, p5) if x]
    lead = p1

    timing_plain = _timing_sentence(timing, special, s3, s5)

    # ── 建议：根据 verdict + pattern 标签定制 ──
    try:
        advice = generate_advice(verdict, question or focus, result)
    except Exception:
        advice = []
    if not advice:
        if "凶" in str(verdict) or "跌" in str(verdict):
            advice = ["先稳住现有局面，不宜加码", "把风险点列出来，能避则避", "等用神得力的时段再考虑推进"]
        else:
            advice = ["顺着已有条件推进，不必反复起念试探", "抓住用神得力的时段做关键动作", "过程有起伏属正常，盯住主线即可"]
    # 根据当前卦象的 pattern 标签给建议补充一句具体场景化提示
    # 若有专属 pattern 提示，用它替换最后一条（一般是通用的时机建议），保留总数 4 条
    pattern_tag = pattern_label or ""
    extra_advice = _pattern_advice_hint(pattern_tag, verdict, timing)
    if extra_advice and len(advice) >= 2:
        advice = advice[:-1] + [extra_advice]
    elif extra_advice:
        advice = advice + [extra_advice]

    # ── 引文：按 reasoning_chain 中卦象格局标签相关性排序 ──
    quotes = _select_relevant_quotes(tc)

    caveat = (
        "这是按纳甲六爻规则推出来的一份参考，讲的是方向和节奏，不是板上钉钉的预言。"
        "看病、打官司、做重大决定，仍要以专业意见为准。"
    )
    # 置信度是内部指标，不在交付正文中暴露（AGENTS.md §三：对齐分≠预测率）。
    # "线索一致程度约 X%" 是置信度的换名表述，口径层面等同于把内部分数伪装成预测能力。
    conf_note = ""

    # —— 推因摘要（从 factor_contributions 翻译成人话）——
    factor_contribs = s5.get("factor_contributions") or []
    explain_summary = _build_explain_summary(factor_contribs, focus)

    # 附录用：推演过程（自然句，不是字段堆）
    process = []
    for label, text in (
        ("观局", s1.get("summary_text") or ""),
        ("定用", s2.get("summary_text") or ""),
        ("断旺", s3.get("summary_text") or ""),
        ("察变", s4.get("summary_text") or ""),
        ("综合", s5.get("summary_text") or ""),
    ):
        if text:
            process.append({"label": label, "text": str(text)})

    return {
        "title": title,
        "question": question,
        "hexagram": hex_name,
        "changed_hexagram": changed_name,
        "verdict": verdict,
        "final_score": score,
        "confidence": conf,
        # 正文
        "headline": p1 if len(p1) < 80 else _verdict_opening(verdict, focus),
        "lead": lead,
        "body": body,
        "reading": "\n\n".join(body),
        "timing_plain": timing_plain,
        "advice": list(advice)[:4],
        "caveat": caveat,
        "confidence_note": conf_note,
        "classical_quotes": quotes,
        "process": process,
        # 兼容旧报告字段
        "plain_summary": body[0] if body else "",
        "what_it_means": p5,
        "use_god": {
            "category": use_cat,
            "element": use_el,
            "branch": use_br,
            "position": use_pos,
            "strength": strength,
            "strength_plain": _strength_sentence(strength, use_cat, use_br, use_pos),
        },
        "special_pattern": special_pat or "",
        "reasoning_chain": tc.get("reasoning_chain") or [],
        "summary_text": tc.get("summary_text") or "",
        # 可解释性输出
        "factor_contributions": factor_contribs,
        "explain_summary": explain_summary,
    }


def render_human_markdown(narrative: dict) -> str:
    """导出为一篇完整解读，而不是「人话章节 + 附录」两张皮。"""
    if not narrative:
        return ""
    lines = [f"# {narrative.get('title') or narrative.get('headline') or '六爻解读'}", ""]
    if narrative.get("question"):
        lines += [f"问：{narrative['question']}", ""]
    for para in narrative.get("body") or []:
        lines += [para, ""]
    lines += [f"**时间上**：{narrative.get('timing_plain') or ''}", ""]
    lines += ["**可以这样做**："]
    for i, a in enumerate(narrative.get("advice") or [], 1):
        lines.append(f"{i}. {a}")
    if narrative.get("confidence_note"):
        lines += ["", narrative["confidence_note"]]
    if narrative.get("classical_quotes"):
        lines += ["", "古人类似情境也说过："]
        for q in narrative["classical_quotes"]:
            lines.append(f"- （{q['source']}）{q['quote']}")
    # 附录：推演过程（有则附，无则不硬凑）
    process = narrative.get("process") or []
    if process:
        lines += ["", "---", "", "## 推演过程（备查）", ""]
        for p in process:
            lines.append(f"**{p['label']}**：{p['text']}")
    lines += ["", "---", narrative.get("caveat") or ""]
    return "\n".join(lines)


# 旧名导出
build_reading = build_human_narrative
