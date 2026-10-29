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
from chain_tables import HEXAGRAM_LIUCHONG  # noqa: E402  六冲卦表真值源

# 方向三态；置信三档。与 data/rules/judgment_table.json 的 axes 同义。
DIRECTIONS = ("成", "滞", "不成")
CONFIDENCES = ("高", "中", "低")

# ── 题类覆盖层（v1）：书证 Z1–Z7 见 judgment_table.json.overlays ──
DOMAIN_KW = {
    "疾病": ("病", "疾", "沉疴", "痘", "症"),
    "功名": ("功名", "考试", "科", "升迁", "求名", "乡试", "会试", "面圣", "官运", "编制", "面试"),
    "求财": ("财", "利", "生意", "买卖", "开张", "索债", "借贷", "价"),
    "行人": ("行人", "归", "回", "来否", "何日到", "在外"),
}
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}  # 克

# 月令旺衰里算"有根"的档（书证 E1：用神旺相可以敌之；原文见 judgment_table.json）
ROOTED = {"旺", "相", "中和"}   # 「有气」：旺相为有气，中和不弱（书证 F5 及其注文口径）


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

    return {
        "旺衰标签": level, "日辰生扶": day_mod > 1.0,
        "用神现": present, "用神有根": rooted, "动变净效": net, "有救有帮": rescued,
        "用神月破": month_break, "用神发动": moving, "用神真空": true_void,
        "忌神发动": ji_moving, "合处逢冲": he_chong, "冲中逢合": chong_he,
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

    def rule(dom_, direction, confidence, why, cites):
        return {"domain": dom_, "direction": direction, "confidence": confidence,
                "why": why, "cites": cites}

    if dom == "疾病":
        if any(k in q for k in ("近病", "新病", "乍病")) and (liuchong or void):
            return rule(dom, "成", "中", "近病逢冲逢空，不药而愈", ["Z1", "Z2"])
        if any(k in q for k in ("久病", "沉疴", "久疾")) and (liuchong or void):
            return rule(dom, "不成", "中", "久病逢冲逢空，妙药难调", ["Z1", "Z2"])
    if dom == "功名":
        if holds and cat == "官鬼":
            return rule(dom, "成", "中", "官鬼持世即许成名", ["Z3"])
        if holds and cat == "子孙":
            return rule(dom, "不成", "中", "子孙持世，功名且待时", ["Z3"])
    if dom == "求财":
        if holds and cat == "妻财":
            return rule(dom, "成", "中", "妻财持世者必得", ["Z4"])
        if kills_world and cat == "妻财":
            return rule(dom, "成", "中", "财爻克世者必得（用克世不作凶看）", ["Z5"])
        if holds and cat == "兄弟":
            return rule(dom, "不成", "低", "兄弟持世者难求", ["Z4"])
    if dom == "行人":
        if kills_world:
            return rule(dom, "成", "中", "用神克世者即至", ["Z5", "Z6"])
        if world_kills:
            return rule(dom, "不成", "中", "世克用兮人未动", ["Z6"])
        if liuchong:
            return rule(dom, "不成", "低", "卦逢六冲，行人无定而不返", ["Z7"])
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
    if not f["用神现"]:
        dissent.append("用神不现（书证 B2 以日月为用，须另判）")

    # ── R1 不成·高：无根 + 受克 + 无救 ──
    if (not f["用神有根"]) and f["动变净效"] < 0 and not f["有救有帮"]:
        return cell("不成", "高", "用神无根而受克，且无救无帮", ["E1"])
    # ── R2 不成·中：月破而静（F2 的分界：破而动仍能伤，破而静到底破）──
    if f["用神月破"] and not f["用神发动"]:
        return cell("不成", "中", "用神月破而静、无发动自救", ["F1", "F2"])
    # ── R3 不成·低：忌神发动无制，或用神不现 ──
    if f["忌神发动"] or not f["用神现"]:
        return cell("不成", "低", "忌神发动无制／用神不现（关键事实缺）", ["E1", "B2"])
    # ── R4 成·高：有根 + 净效不逆 + 无合冲 ──
    if f["用神有根"] and f["动变净效"] >= 0 and not f["合处逢冲"] and not f["用神真空"]:
        return cell("成", "高", "用神旺相有根，动变不逆，无合冲", ["E1", "F4"])
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


def judge_with_overlay(result: dict) -> dict:
    """九格 + 题类覆盖。base 与 overlay 都留在返回值里，便于对拍时看清是谁改的。"""
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
    return out
