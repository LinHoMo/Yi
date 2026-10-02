# -*- coding: utf-8 -*-
"""合参层·裁决规则（cross_rules）—— 谁定什么、同向如何确、异向如何裁。

规则来源：synthesis/README.md §二（与 cross_rules.md 同源），逐条落为代码：

  1. 各守其位：命定趋势节律、卜决具体一事。卜科问命域（一生/命运/格局…）
     → 判为无效输入，不参与合参，报告说明剔除原因。
  2. 各科同向 → 可提升陈述强度，但不用「注定/一定」；给出触发条件与时间窗。
  3. 两科同向、一科异向 → 以两科为趋向，异向单列并给出其成立条件。
  4. 各科异向 → 先查输入是否同一时空（年界/月界/日辰口径），再查起局时间与
     用神选取；核对后仍分歧 → 如实并列两种趋向及触发条件，不做平均、不编调和说。
  5. 任一科缺数据 → 降级为「该维度未参评」，不得用其他科补位猜测。

裁决只输出结构化判定与说明，不写任何成段断语（解释权归解读层）。
"""
from __future__ import annotations

from yishu_core.report.request import DISCIPLINES

# 命科＝定趋势节律，卜科＝决具体一事；分区只此一份，其余模块 import 本处。
MING_DISCIPLINES = ("ming", "ziwei")
BU_DISCIPLINES = tuple(d for d in DISCIPLINES if d not in MING_DISCIPLINES)

# 卜科问这些主题＝越位问命（《周易》语境下命理与占卜各守其位）
MING_DOMAIN_KEYWORDS = ("一生", "命运", "命理", "八字", "格局", "寿命",
                        "前程", "大运", "流年", "贵人", "克夫", "克妻")

# 命理主题词（缺数据判定用，区别于越位表）：财运/婚姻/事业等可一事一占
# （卜科合法），但问句落在命理主题时，趋势层面缺命科佐证 → 命科未参评
MING_TOPIC_KEYWORDS = MING_DOMAIN_KEYWORDS + (
    "财运", "求财", "婚姻", "姻缘", "官运", "学业", "健康", "仕途")


def domain_check(rec: dict) -> tuple[bool, str]:
    """越位判定：返回 (是否合法, 剔除原因)。"""
    disc = rec.get("discipline")
    asked = str(rec.get("asked") or "")
    if disc in MING_DISCIPLINES:
        return True, ""
    if disc not in BU_DISCIPLINES:
        return False, f"未知学科 {disc!r}"
    hit = [w for w in MING_DOMAIN_KEYWORDS if w in asked]
    if hit:
        return False, (f"越位：{disc} 为卜科（一事之成败趋向与应期），"
                       f"问句含命域主题词 {hit}——命定趋势归命科，"
                       f"判为无效输入，不参与合参")
    return True, ""


def _tally(records: list[dict]) -> dict:
    """方向计数：{吉, 平, 凶}。平为中性，不参与多数判定。"""
    t = {"吉": 0, "平": 0, "凶": 0}
    for r in records:
        d = r.get("direction")
        if d in t:
            t[d] += 1
    return t


def adjudicate(records: list[dict], *, policies: list | None = None) -> dict:
    """归一化占问记录列表 → 合参裁决。

    policies : 各记录的日历口径（calendar_policy dict 或可哈希标签）；
               口径不一致时标记时空分歧（规则 4 第一步）。
    """
    excluded, valid = [], []
    for r in records:
        ok, reason = domain_check(r)
        (valid if ok else excluded).append((r, reason))

    valid_recs = [r for r, _ in valid]
    tally = _tally(valid_recs)
    n = len(valid_recs)

    policy_conflict = False
    if policies:
        distinct = {json_dumps(p) for p in policies if p is not None}
        policy_conflict = len(distinct) > 1

    notes: list[str] = []
    pattern, trend = "none", "未参评"

    if n == 0:
        pattern, trend = "none", "未参评"
        notes.append("无可参评的合法占问记录")
    elif n == 1:
        pattern, trend = "single", valid_recs[0].get("direction") or "平"
        notes.append("单科结论：无互证，陈述强度不提升（规则 2 只适用于多科同向）")
    else:
        pos = tally["吉"]
        neg = tally["凶"]
        if pos and neg:
            if pos >= 2 or neg >= 2:
                pattern = "two_one"
                trend = "吉" if pos > neg else "凶"
                other = "凶" if pos > neg else "吉"
                notes.append(
                    f"两科同向（{trend}）、{other} 单列：以 {trend} 为趋向，"
                    f"异向结论单列并给出其成立条件（规则 3）")
            else:
                pattern = "split"
                trend = "分歧"
                notes.append(
                    "各科异向：先查输入是否同一时空（年界/月界/日辰口径）与起局时间、"
                    "用神选取；核对后仍分歧则如实并列两种趋向及各自触发条件，"
                    "交当事人，不做平均、不编调和说（规则 4）")
                if policy_conflict:
                    notes.append("检测到日历口径不一致（calendar_policy 存在分歧）："
                                 "此为假分歧首要来源，先统一口径再谈结论")
        elif pos or neg:
            pattern = "same"
            trend = "吉" if pos else "凶"
            notes.append(
                f"各科同向（{trend}，{pos + neg}/{n} 表态、{tally['平']} 中性）："
                f"可提升陈述强度，仍不用「注定/一定」；给出触发条件与时间窗（规则 2）")
            if policy_conflict:
                notes.append("注意：虽同向，但日历口径不一致，建议复核各科起局时间")
        else:
            pattern = "flat"
            trend = "平"
            notes.append("各科均两可（无明确趋向）：以应期、事类细节与建议为主，"
                         "不强行给定论")

    missing = []
    wants_ming = any(str(r.get("asked") or "").find(w) >= 0
                     for r in records for w in MING_TOPIC_KEYWORDS)
    if wants_ming and not any(r.get("discipline") in MING_DISCIPLINES for r in records):
        missing.append("ming")

    return {
        "pattern": pattern,
        "trend": trend,
        "tally": tally,
        "n": n,
        "valid": valid_recs,
        "excluded": [{"asked": r.get("asked"), "reason": reason} for r, reason in excluded],
        "missing": missing,
        "policy_conflict": policy_conflict,
        "notes": notes,
    }


def json_dumps(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def selfcheck() -> None:
    """金标准自检：五条规则逐条构造最小用例。"""
    def rec(direction, discipline="liuyao", asked="讨债能成否"):
        return {"discipline": discipline, "asked": asked, "direction": direction}

    # 分区完备性：命科 ∪ 卜科 == 全科且不相交；ziwei 属命科，不再被判「未知学科」
    assert not (set(MING_DISCIPLINES) & set(BU_DISCIPLINES)), "命卜分区相交"
    assert set(MING_DISCIPLINES) | set(BU_DISCIPLINES) == set(DISCIPLINES), "命卜分区不完备"
    ok, reason = domain_check(rec("平", discipline="ziwei", asked="今年事业如何"))
    assert ok, f"ziwei 应属命科，却被判：{reason}"

    # 规则 1：越位
    ok, reason = domain_check(rec("吉", asked="我这一生的命运如何"))
    assert not ok and "越位" in reason, reason

    # 规则 2：同向
    r = adjudicate([rec("吉"), rec("吉"), rec("平")])
    assert r["pattern"] == "same" and r["trend"] == "吉", r
    assert any("不用" in x and "注定" in x for x in r["notes"]), r["notes"]

    # 规则 3：两同一异
    r = adjudicate([rec("吉"), rec("吉"), rec("凶")])
    assert r["pattern"] == "two_one" and r["trend"] == "吉", r

    # 规则 4：各科异向 + 口径分歧
    r = adjudicate([rec("吉"), rec("凶"), rec("平")])
    assert r["pattern"] == "split" and r["trend"] == "分歧", r
    r = adjudicate([rec("吉"), rec("凶"), rec("平")],
                   policies=[{"boundary": "day"}, {"boundary": "solar"}])
    assert r["policy_conflict"] and any("口径" in x for x in r["notes"]), r

    # 规则 5：缺数据降级
    r = adjudicate([rec("吉", asked="占今年财运如何")])
    assert "ming" in r["missing"], r
    r = adjudicate([rec("吉", discipline="ming", asked="今年财运如何")])
    assert "ming" not in r["missing"] and r["pattern"] == "single", r
    print("cross_rules 自检通过（越位/同向/两同一异/异向口径/缺数据降级）")


if __name__ == "__main__":
    selfcheck()
