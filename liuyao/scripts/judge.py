# -*- coding: utf-8 -*-
"""判定器（A3·第三百一十七批）：把"一维分数 + 覆写栈"换成"方向 × 置信"的 9 格。

**本批是影子模式**：`judge()` 只被 `dev_tools/judge_shadow.py` 调用做逐例对拍，
**不参与** `step5` 的 `verdict` 计算——改判要等对拍结果摆上桌、并由人另批放行（§四）。

判据来源：`data/rules/judgment_table.json`（9 格 + 25 书证）与 `docs/JUDGMENT-TABLE.md`。
本模块只读事实、不读 `verdict`：所有输入都取自 step2/3/4/5 的结构字段，
**不读 `final_score`**——读分数就等于把被审对象当判据，那是自证。

四条已签裁决（317 批，用户按建议签）：
  JT-A 月破兼动 → 采 F2（破而静/破而动分开，见 R2 的 `moving` 条件）
  JT-B 月日权重 → 6:4 标为"非书证·工程默认"，本器不碰该常数
  JT-C 用神与世 → **方向由用神定，世只降置信**（本器不读世爻吉凶）
  JT-D 时间题   → 判定表只管吉凶题（本器不识别题型，时间题由调用方跳过）

    from judge import judge
    j = judge(analyze_result)   # → {"direction","confidence","cell","support","dissent","facts"}
"""
from __future__ import annotations

import os as _os
import sys as _sys

_here = _os.path.dirname(_os.path.abspath(__file__))
if _here not in _sys.path:
    _sys.path.insert(0, _here)

from kernel_path import ensure_kernel_on_path as _ensure  # noqa: E402

_ensure(__file__)

from yishu_core.symbols import BRANCH_ELEMENTS  # noqa: E402  五行真值源，不在本模块复制
from chain_tables import HEXAGRAM_LIUCHONG, HEXAGRAM_LIUHE  # noqa: E402  六冲/六合卦表真值源

# 方向三态；置信三档。与 data/rules/judgment_table.json 的 axes 同义。
DIRECTIONS = ("成", "滞", "不成")
CONFIDENCES = ("高", "中", "低")

# ── 题类覆盖层（v1）：书证 Z1–Z7 见 judgment_table.json.overlays ──
DOMAIN_KW = {
    "疾病": ("病", "疾", "沉疴", "痘", "症"),
    "功名": ("功名", "考试", "科", "升迁", "求名", "乡试", "会试", "面圣", "官运", "编制", "面试"),
    "求财": ("财", "利", "生意", "买卖", "开张", "索债", "借贷", "价"),
    "行人": ("行人", "归", "回", "来否", "何日到", "在外"),
    "合伙": ("合伙", "合伙做", "合作", "合资"),
    # 323 批修：裸「讼」会命中卦名（巽之讼／天水讼），把行人/失物题误判成讼事题；
    # 只留确实指打官司的词。
    "讼事": ("词讼", "官司", "诉讼", "争讼", "打官司", "官非"),
    "婚姻": ("婚姻", "嫁娶", "娶妻", "嫁女", "配偶", "夫妻", "婚"),
    "失物": ("失银", "失物", "失脱", "失落", "遗失", "寻物", "丢东西"),
}

# 323 批：两个"轴不适用"判据（依据已签的 JT-D「时间题另表」＋ verdict_map 里
# 「下跌」那条的注「义为价跌不是事败，不得直接映射」）
TIME_KEYS = ("何日", "何时", "几时", "哪天", "何年月日", "几日", "何月")

# 题类默认口径（题类在场而本类规则未命中时用）：每条都有书证
DOMAIN_DEFAULT = {
    "功名": {"why": "功名只以官鬼持世为成，余者且待时", "cites": ["Z3"]},
    "求财": {"why": "求财以妻财持世为必得，余者未可定", "cites": ["Z4"]},
    "疾病": {"why": "不逢六冲不遇旬空，旺不旺而衰不衰，不可断", "cites": ["Z1", "Z2"]},
    "行人": {"why": "行人以用神克世为至，世克用为未动", "cites": ["Z6"]},
    "讼事": {"why": "官鬼持世忧疑难解，余者未可定", "cites": ["Z17"]},
    "合伙": {"why": "世应临兄不吉，余者未可定", "cites": ["Z14"]},
    "婚姻": {"why": "诸合皆以用神旺者为吉，余者未可定", "cites": ["Z16"]},
}
PRICE_KEYS = ("价", "贵贱", "涨跌", "市价", "大例", "行情")
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}  # 克
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}  # 生

# 月令旺衰里算"有根"的档（书证 E1：用神旺相可以敌之；原文见 judgment_table.json）
ROOTED = {"旺", "相", "极旺"}   # 「有气」＝旺相（书证 F5 注文：旺相为有气，休囚为无气）


def _s2(tc: dict) -> dict:
    return tc.get("step2_use_god_identification") or {}


def _s3(tc: dict) -> dict:
    return tc.get("step3_strength_analysis") or {}


def _s4(tc: dict) -> dict:
    return tc.get("step4_change_analysis") or {}


def _s5(tc: dict) -> dict:
    return tc.get("step5_synthesis") or {}


def facts(result: dict) -> dict:
    """从 analyze 结果里取判定所需的结构事实（不读 verdict／final_score）。"""
    tc = result.get("thinking_chain") or result
    s2, s3, s4, s5 = _s2(tc), _s3(tc), _s4(tc), _s5(tc)
    sel = s2.get("selected_use_god") or {}
    ji = (s2.get("ji_shen") or {})
    ji_positions = ji.get("positions") or []
    sp = s5.get("special_pattern")
    sp_text = str(sp.get("pattern") if isinstance(sp, dict) else sp or "")

    present = bool(s2.get("has_use_god_in_hexagram")) or bool(sel)
    level = str(s3.get("strength_level") or "")
    day_mod = s3.get("day_modifier")
    day_mod = float(day_mod) if isinstance(day_mod, (int, float)) else 1.0
    # 「有气」不是单看月令标签：日辰生扶（书证 A3：日辰能生克卦爻）也算有气，
    # 这正是标 极弱 却书判吉的那批例子的入口（见 judge_shadow 的逐例事实表）。
    rooted = level in ROOTED or day_mod > 1.0
    net = s4.get("net_effect")
    net = float(net) if isinstance(net, (int, float)) else 0.0
    rescued = bool(s4.get("favorable_changes")) or float(s4.get("greedy_harmony_score") or 0) > 0
    month_break = bool(s3.get("is_month_break"))
    moving = bool(sel.get("is_moving"))
    true_void = bool(s3.get("is_true_void"))
    ji_moving = any(p.get("is_moving") for p in ji_positions if isinstance(p, dict))
    he_chong = "合处逢冲" in sp_text
    chong_he = "冲中逢合" in sp_text

    # ── 二级事实（319 批）：原神有力／忌神无力 ──
    # 书证：Z8（元神能生用神者有五）／Z9（忌神不能克用神者有七）／Z11（接续相生化凶为吉）
    yuan = s2.get("yuan_shen") or {}
    ji = s2.get("ji_shen") or {}
    yuan_pos = yuan.get("positions") or []
    ji_pos = ji.get("positions") or []
    yuan_moving = any(p.get("is_moving") for p in yuan_pos if isinstance(p, dict))
    ji_moving = any(p.get("is_moving") for p in ji_pos if isinstance(p, dict))
    ji_void = any(p.get("is_empty") for p in ji_pos if isinstance(p, dict))
    ji_hidden = bool(ji.get("fu_cang")) and not ji_pos
    yuan_el = yuan.get("element") or ""
    ji_el = ji.get("element") or ""
    yuan_ke_ji = bool(yuan_el and ji_el and KE.get(yuan_el) == ji_el)
    yuan_ji_both = yuan_moving and ji_moving
    # 元神有力：动（书证 Z8）或接续相生克忌（书证 Z11）
    yuan_power = yuan_moving or yuan_ke_ji
    # 忌神无力：静临空破／与元神同动（书证 Z9）／忌神反生元神（接续相生，书证 Z11）
    # 321 批修 bug：此处原写成 `... or ji_pos`，而 ji_pos 是**列表**——
    # 于是 `if 忌神无力` 恒真（任何忌神都在位即成立）。此处必须是 bool。
    ji_no_power = bool((ji_void or ji_hidden or (not ji_moving and ji_pos))
                       or yuan_ji_both or yuan_ke_ji)

    # 世应关系（321 批）：用神持世 / 用神生世
    wl = _world_line(result)
    w_el = BRANCH_ELEMENTS.get(wl.get("earthly_branch") or "") or ""
    ug_el = s2.get("use_god_element") or ""
    holds = bool(sel.get("position")) and sel.get("position") == s2.get("world_position")
    sheng_world = bool(ug_el and w_el and SHENG.get(ug_el) == w_el)
    # 世爻六亲与兄爻发动（322 批：合伙题覆盖层用）
    ji_el = (s2.get("ji_shen") or {}).get("element") or ""
    world_killed_by_god = bool(ug_el and w_el and KE.get(ug_el) == w_el)
    world_killed_by_ji = bool(ji_el and w_el and KE.get(ji_el) == w_el)
    world_is_brother = (wl.get("six_relation") or "") == "兄弟"
    brother_moving = any((y.get("six_relation") or "") == "兄弟" and y.get("is_moving")
                          for y in (result.get("original_hexagram") or {}).get("yao_lines") or [])
    changed_liuhe = (result.get("changed_hexagram") or {}).get("name") in HEXAGRAM_LIUHE

    return {
        "旺衰标签": level, "日辰生扶": day_mod > 1.0, "题类": domain_of(str(result.get("question") or "")),
        "用神持世": holds, "用神生世": sheng_world,
        "世临兄弟": world_is_brother, "兄弟爻发动": brother_moving, "变卦六合": changed_liuhe,
        "世受克": (world_killed_by_god or world_killed_by_ji),
        "用神克世": world_killed_by_god, "忌神克世": world_killed_by_ji,
        "用神现": present, "用神有根": rooted, "动变净效": net, "有救有帮": rescued,
        "用神月破": month_break, "用神发动": moving, "用神真空": true_void,
        "忌神发动": ji_moving, "合处逢冲": he_chong, "冲中逢合": chong_he,
        "原神发动": yuan_moving, "原神有力": yuan_power, "忌神无力": ji_no_power,
        "接续相生": yuan_ke_ji, "元神忌神同动": yuan_ji_both,
        "特殊格局": sp_text,
    }



# ─────────────────────────────────────────────────────────────────────────────
# 题类覆盖层（v1）
# ─────────────────────────────────────────────────────────────────────────────
def domain_of(question: str) -> str:
    """题类分流：先按关键词定题类；定不出就返回空串（不猜）。"""
    q = str(question or "")
    for dom, kws in DOMAIN_KW.items():
        if any(k in q for k in kws):
            return dom
    return ""


def _world_line(result: dict) -> dict:
    for y in (result.get("original_hexagram") or {}).get("yao_lines") or []:
        if y.get("is_world"):
            return y
    return {}


def overlay(result: dict) -> dict | None:
    """四条题类规则（疾病/功名/求财/行人），条件全部来自书证，见 judgment_table.json.overlays。"""
    tc = result.get("thinking_chain") or result
    q = str(result.get("question") or "")
    dom = domain_of(q)
    if not dom:
        return None
    s2, s3 = _s2(tc), _s3(tc)
    sel = s2.get("selected_use_god") or {}
    cat = s2.get("use_god_category") or ""
    ug_el = s2.get("use_god_element") or ""
    wl = _world_line(result)
    w_el = BRANCH_ELEMENTS.get(wl.get("earthly_branch") or "") or ""
    holds = bool(sel.get("position")) and sel.get("position") == s2.get("world_position")
    kills_world = bool(ug_el and w_el and KE.get(ug_el) == w_el)
    world_kills = bool(ug_el and w_el and KE.get(w_el) == ug_el)
    liuchong = (result.get("original_hexagram") or {}).get("name") in HEXAGRAM_LIUCHONG
    void = bool(s3.get("is_true_void"))
    _wl = _world_line(result)
    f_brother_world = (_wl.get("six_relation") or "") == "兄弟"
    f_brother_moving = any((y.get("six_relation") or "") == "兄弟" and y.get("is_moving")
                            for y in (result.get("original_hexagram") or {}).get("yao_lines") or [])
    f_changed_liuhe = (result.get("changed_hexagram") or {}).get("name") in HEXAGRAM_LIUHE

    def rule(oid, dom_, direction, confidence, why, cites):
        return {"id": oid, "domain": dom_, "direction": direction, "confidence": confidence,
                "why": why, "cites": cites}

    if dom == "疾病":
        if any(k in q for k in ("久病", "沉疴", "久疾")) and (liuchong or void):
            return rule("OV-D2", dom, "不成", "中", "久病逢冲逢空，妙药难调", ["Z1", "Z2"])
        if (liuchong or void) and any(k in q for k in ("近病", "新病", "乍病", "病")):
            return rule("OV-D1", dom, "成", "中", "近病逢冲逢空，不药而愈", ["Z1", "Z2"])
    if dom == "功名":
        if holds and cat == "官鬼":
            return rule("OV-G1", dom, "成", "中", "官鬼持世即许成名", ["Z3"])
        if holds and cat == "子孙":
            return rule("OV-G2", dom, "不成", "中", "子孙持世，功名且待时", ["Z3"])
    if dom == "求财":
        if holds and cat == "妻财":
            return rule("OV-C1", dom, "成", "中", "妻财持世者必得", ["Z4"])
        if kills_world and cat == "妻财":
            return rule("OV-C2", dom, "成", "中", "财爻克世者必得（用克世不作凶看）", ["Z5"])
        if holds and cat == "兄弟":
            return rule("OV-C3", dom, "不成", "低", "兄弟持世者难求", ["Z4"])
    if dom == "合伙":
        # 书证 Z14：世应临兄不吉、兄爻发动不吉（除非日月作财星冲克世，反为吉也——例外未实现）
        if f_brother_world or f_brother_moving:
            return rule("OV-H1", dom, "不成", "中", "世应临兄不吉，兄爻发动不吉", ["Z14"])
    if dom == "讼事":
        # 书证 Z17：官鬼持世忧疑难解（其例外「日月动爻冲克世者反为吉」需日月动爻冲世判定，未实现）
        if holds and cat == "官鬼":
            return rule("OV-S1", dom, "不成", "低", "官鬼持世，忧疑难解", ["Z17"])
    if dom == "婚姻":
        # 书证 Z16：独此六冲卦变六合得不看用神，竟以吉断
        if f_changed_liuhe:
            return rule("OV-M1", dom, "成", "中", "卦变六合，不看用神亦以吉断", ["Z16"])
    if dom == "行人":
        if kills_world:
            return rule("OV-X1", dom, "成", "中", "用神克世者即至", ["Z5", "Z6"])
        if world_kills:
            return rule("OV-X2", dom, "不成", "中", "世克用兮人未动", ["Z6"])
        if liuchong:
            return rule("OV-X3", dom, "不成", "低", "卦逢六冲，行人无定而不返", ["Z7"])
    # 324 批：窄版题类优先——只对书证明说"且待时/难求"的题类（功名/求财/婚姻），
    # 本类规则未命中时按本类默认口径判"待时/未决"；其余题类仍走九格。
    # （323 批的全量版题类接管实测更差，已回退——书的总纲与分类占法是叠加关系。）
    default = DOMAIN_DEFAULT.get(dom) if dom in ("功名", "求财", "婚姻") else None
    if default:
        return rule(f"OV-{dom}-DEF", dom, "滞", "低", default["why"], default["cites"])
    # 323 批**试过"题类接管"并已回退**：题类在场而本类规则未命中时改判"待时/未决"，
    # 实测 tune 42.9→28.6、wiki·dev 75.0→66.7 —— **书的总纲与分类占法是叠加关系，不是替代关系**。
    # 结论：分类规则命中就接管，没命中就仍走九格（DOMAIN_DEFAULT 已废，保留在此作反面记录）。
    return None


def judge(result: dict) -> dict:
    """九格判定（rules-as-predicates，顺序即优先级）。返回方向/置信与支持·反证两类事实。"""
    f = facts(result)
    support: list[str] = []
    dissent: list[str] = []

    def cell(direction: str, confidence: str, why: str, cites: list[str]) -> dict:
        return {"direction": direction, "confidence": confidence, "cell": f"{direction}·{confidence}",
                "why": why, "cites": cites, "facts": f, "support": support, "dissent": dissent}

    # ── 支持/反证两侧先各自登记（供叙述层"两面都讲"用，也供对拍时看判定依据）──
    if f["用神有根"]:
        support.append("用神有根：旺衰=%s（书证 E1）" % f.get("旺衰标签", ""))
    else:
        dissent.append("用神无根：旺衰不足（书证 E1 后半）")
    if f["动变净效"] > 0:
        support.append("动变净生用：净效 %+.2f" % f["动变净效"])
    elif f["动变净效"] < 0:
        dissent.append("动变净克用：净效 %+.2f" % f["动变净效"])
    if f["有救有帮"]:
        support.append("有救有帮（书证 E2）")
    if f["用神月破"]:
        dissent.append("用神月破（书证 F1／F2 分破而静与破而动）")
    if f["用神真空"]:
        dissent.append("用神真空（书证 F3 仅近病论空不论克）")
    if f["忌神发动"]:
        dissent.append("忌神发动（书证 E1 末句：忌得动助则不可敌）")
    if f["合处逢冲"]:
        dissent.append("合处逢冲（书证 D1／F4 合被冲破则无功）")
    if f["冲中逢合"]:
        support.append("冲中逢合（书证 D1 贪合忘冲）")
    if f["原神有力"]:
        support.append("原神有力：发动或接续相生（书证 Z8）")
    if f["忌神无力"]:
        support.append("忌神无力：静临空破／与元神同动／反生元神（书证 Z9、Z11）")
    else:
        dissent.append("忌神有力：可克害用神（书证 Z9 反面）")
    if not f["用神现"]:
        dissent.append("用神不现（书证 B2 以日月为用，须另判）")

    # 327 批**试过"世受克 → 不成"并已回退**：书证说「诸占最怕克世」（Z18），但底本紧跟着
    # 就给了反例「用克世勿作凶看」（占财／行人／医药反作吉），且忌神克世在实践中极常见——
    # 做成通用规则实测 wiki·dev 75.0→33.3、wiki_direction·dev 50.0→35.7，**大幅变差**。
    # 结论：这条只能进**题类覆盖层**（按题类分别判），不能作通用九格规则。
    # 事实仍保留（判断块会报"世受克/用神克世/忌神克世"），供后续按题类取用。
    # ── R4c 不成·中：忌神发动而用神无根，虽有生世亦不吉 ──
    # 书证反面条款：Z13「谓忌神既旺，用衰矣，世虽逢生何益」（忌旺用衰时不因生世转吉）
    if (not f["用神有根"]) and f["忌神发动"] and (f["用神生世"] or f["用神持世"]):
        return cell("不成", "中", "忌神既旺、用神无根，虽生世亦无益", ["Z13"])
    # ── R4d 成·中：生世或持世（书证 Z12：生世者反得其济）──
    if (not f["用神有根"]) and (f["用神生世"] or f["用神持世"]) and not f["忌神发动"]:
        return cell("成", "中", "用神生世或持世，生世者反得其济", ["Z12"])
    # ── R0′ 成·低：无根，但原神有力且忌神无力（接续相生）──
    # 书证两面：Z8 元神能生用神者有五；Z10 末句「倘若用神无根，谓之元神有力亦难生」
    # → 方向可成，但**置信只能是低**（无根难生）。这正是 v0 漏掉的那类事实。
    if (not f["用神有根"]) and f["原神有力"] and f["忌神无力"]:
        return cell("成", "低", "用神无根，然原神有力且忌神无力，接续相生（无根难生，故置信低）",
                    ["Z8", "Z9", "Z10", "Z11"])
    # ── R1 不成·高：无根 + 受克 + 无救 + 忌神有力 ──
    if (not f["用神有根"]) and f["动变净效"] < 0 and not f["有救有帮"] and not f["忌神无力"]:
        return cell("不成", "高", "用神无根而受克，无救，且忌神有力", ["E1", "Z9"])
    # ── R2 不成·中：月破而静（F2 的分界：破而动仍能伤，破而静到底破）──
    if f["用神月破"] and not f["用神发动"]:
        return cell("不成", "中", "用神月破而静、无发动自救", ["F1", "F2"])
    # ── R3 不成·低：忌神发动无制，或用神不现 ──
    if f["忌神发动"] or not f["用神现"]:
        return cell("不成", "低", "忌神发动无制／用神不现（关键事实缺）", ["E1", "B2"])
    # ── R4 成·高：有根 + 净效不逆 + 无合冲 ──
    if f["用神有根"] and f["动变净效"] >= 0 and not f["合处逢冲"] and not f["用神真空"]:
        return cell("成", "高", "用神旺相有根，动变不逆，无合冲", ["E1", "F4"])
    # ── R4b 成·中：用神有根，而忌神无力（化凶为吉）──
    if f["用神有根"] and f["忌神无力"] and f["动变净效"] >= 0:
        return cell("成", "中", "用神有根，忌神无力，化凶为吉", ["Z9", "Z11"])
    # ── R5 成·中：有根但受克，克有救 ──
    if f["用神有根"] and f["动变净效"] < 0 and f["有救有帮"]:
        return cell("成", "中", "用神有根受克，克有救", ["E1", "D1", "F4"])
    # ── R6 滞·中：合冲并见 ──
    if f["合处逢冲"] or f["冲中逢合"]:
        return cell("滞", "中", "合冲并见：先合后冲／先冲后合", ["D1", "F4"])
    # ── R7 滞·低：空破待填 ──
    if f["用神真空"] or f["用神月破"]:
        return cell("滞", "低", "空破待填，关键事实未定", ["F3", "F2"])
    # ── R8 默认：未决 ──
    return cell("滞", "低", "九格未覆盖，按未决处理（不冒充平吉）", ["F5"])


def axis_of(result: dict) -> tuple[str, str]:
    """判断这道题属不属于"吉凶轴"。

    返回 (axis, 理由)：``吉凶`` 正常入九格；``时间`` / ``价势`` 两类**不参与吉凶方向**
    ——时间题问的是"何时"（已签 JT-D：判定表只管吉凶题，时间题另表），
    价势题问的是"价涨还是价跌"（verdict_map 注：下跌义为价跌不是事败，不得直接映射）。
    """
    q = str(result.get("question") or "")
    dom = domain_of(q)
    if dom == "求财" and any(k in q for k in PRICE_KEYS):
        return "价势", "题问价势（涨落），方向轴是价不是事成败"
    if any(k in q for k in TIME_KEYS):
        return "时间", "题问时间（何日/何时），吉凶轴不判"
    return "吉凶", ""


def judge_with_overlay(result: dict) -> dict:
    """九格 + 题类覆盖。base 与 overlay 都留在返回值里，便于对拍时看清是谁改的。"""
    axis, why_axis = axis_of(result)
    if axis != "吉凶":
        base = judge(result)
        out = dict(base)
        out["base_cell"] = base["cell"]
        out["cell"] = f"不适用·{axis}"
        out["direction"] = None
        out["confidence"] = None
        out["axis"] = axis
        out["why"] = why_axis
        out["support"] = []
        out["dissent"] = []
        out["overlay"] = None
        out["domain"] = domain_of(result.get("question") or "")
        return out
    base = judge(result)
    ov = overlay(result)
    if not ov:
        base["domain"] = domain_of(result.get("question") or "")
        base["overlay"] = None
        base["base_cell"] = base["cell"]
        return base
    out = dict(base)
    out["base_cell"] = base["cell"]
    out["cell"] = f"{ov['direction']}·{ov['confidence']}"
    out["direction"] = ov["direction"]
    out["confidence"] = ov["confidence"]
    out["why"] = "题类覆盖：" + ov["why"]
    out["cites"] = sorted(set(base.get("cites", [])) | set(ov["cites"]))
    out["domain"] = ov["domain"]
    out["overlay"] = ov
    out["axis"] = "吉凶"
    return out
