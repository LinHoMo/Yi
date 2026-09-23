# -*- coding: utf-8 -*-
"""合参层·现实回填评分（应期回收闭环）。

断卦时输出的应期候选（liuyao 的 yingqi_offered，按给出顺序即名次）事后与现实
回填（person 档案 divinations[].outcome 的 occurred_at / judged）比对：

  - 断事命中：judged = 应验 / 部分应验 → 应验；未应验 / 超期未验 → 未验。
  - 应期命中（仅 liuyao，且候选与 occurred_at 齐全）：
      候选第 1 位命中 → 主应期；第 2~4 位 → 次应期；更靠后 → 命中但名次靠后；
      occurred_at 早于全部候选 → 提前；晚于末位候选 → 超期。

口径诚实（AGENTS.md §三）：这是**现实回填命中**，不是古籍案例对齐分，也绝不
等于"预测率"。汇总必须带样本量 n 与集合名（此处集合 = 档案内已回填的占问）。
"""
from __future__ import annotations

from datetime import date


def _rate(hit: int, n: int) -> float | None:
    return round(hit * 100.0 / n, 1) if n else None

# 断事命中判定：judged → 断事结果
JUDGED_TO_HIT = {"应验": "应验", "部分应验": "部分", "未应验": "未验", "超期未验": "未验(超期)"}
YQ_HIT_LABEL = {
    (1, "hit"): "主应期命中",
    (2, "hit"): "次应期命中(第2位)",
    (3, "hit"): "第3位命中",
    (4, "hit"): "第4位命中",
    ("late", "hit"): "命中但名次靠后",
    ("early", None): "提前于全部候选",
    ("overrun", None): "超期未验",
}
# 应期命中得分（名次制，与 liuyao evaluate.strict 同精神：主应期全分，越靠后越低）
YQ_SCORE = {1: 1.0, 2: 0.8, 3: 0.7, 4: 0.55, "late": 0.35, "early": 0.35, "overrun": 0.0}


def _parse_date(text) -> date | None:
    try:
        return date.fromisoformat(str(text).strip())
    except (ValueError, TypeError):
        return None


def _judged_hit(judged: str | None) -> str | None:
    if not judged:
        return None
    return JUDGED_TO_HIT.get(judged, "未验")


def eval_outcomes(divinations: list[dict]) -> dict:
    """遍历档案内已回填的占问，逐例判定 + 汇总。未回填的条目不进统计。"""
    cases: list[dict] = []
    n_judged = n_hit = n_partial = 0
    n_yq_eval = n_yq_hit = 0
    by_discipline: dict[str, dict] = {}

    for div in divinations or []:
        oc = div.get("outcome") or {}
        if oc.get("recorded") is None:
            continue  # 未回填 → 不进现实效度统计
        discipline = div.get("discipline") or "?"
        judged = oc.get("judged")
        occurred = oc.get("occurred_at")
        row = {
            "event_id": div.get("event_id"),
            "discipline": discipline,
            "asked": str(div.get("asked") or "")[:40],
            "direction": div.get("direction"),
            "judged": judged,
            "occurred_at": occurred,
            "recorded": str(oc.get("recorded") or "")[:60],
        }
        hit = _judged_hit(judged)
        row["断事"] = hit
        if hit:
            n_judged += 1
            if hit == "应验":
                n_hit += 1
            elif hit == "部分":
                n_partial += 1

        yq = _eval_yingqi(div, occurred)
        row["应期"] = yq
        if yq and yq.get("可评"):
            n_yq_eval += 1
            if yq["命中"]:
                n_yq_hit += 1

        cases.append(row)
        by = by_discipline.setdefault(discipline, {"n": 0, "judged": 0, "hit": 0, "yq_eval": 0, "yq_hit": 0})
        by["n"] += 1
        if hit:
            by["judged"] += 1
            if hit == "应验":
                by["hit"] += 1
        if yq and yq.get("可评"):
            by["yq_eval"] += 1
            if yq["命中"]:
                by["yq_hit"] += 1

    if not cases:
        return {"n_回填": 0, "cases": []}
    return {
        "n_回填": len(cases),
        "n_断事可评": n_judged,
        "断事应验": n_hit,
        "断事部分": n_partial,
        "断事应验率": _rate(n_hit, n_judged),
        "n_应期可评": n_yq_eval,
        "应期命中": n_yq_hit,
        "应期命中率": _rate(n_yq_hit, n_yq_eval),
        "by_discipline": by_discipline,
        "cases": cases,
    }


def _eval_yingqi(div: dict, occurred: str | None) -> dict | None:
    """单例应期判定；候选/日期不全返回 None（不评，也不进分母）。"""
    if div.get("discipline") != "liuyao":
        return None  # 其余学科目前无可评的结构化候选
    if not occurred:
        return None
    obs = _parse_date(occurred)
    if obs is None:
        return {"可评": False, "判定": "occurred_at 无效", "命中": False}
    offered = div.get("yingqi_offered") or []
    dates: list[str] = []
    for it in offered:
        d = str(it.get("date") or "")
        if d not in dates:
            dates.append(d)
    if not dates:
        return None  # 六爻该卦未给结构化候选（如仅支级应期）→ 不评
    parsed = [_parse_date(d) for d in dates]
    valid = [(d, d0) for d, d0 in zip(dates, parsed) if d0 is not None]
    if not valid:
        return {"可评": False, "判定": "候选日期无效", "命中": False}

    hit = next((i for i, (_, d0) in enumerate(valid) if d0 == obs), None)
    if hit is not None:
        rank = hit + 1
        label = YQ_HIT_LABEL.get((rank, "hit")) or "命中但名次靠后"
        score = YQ_SCORE.get(rank, YQ_SCORE["late"])
        return {"可评": True, "命中": True, "名次": rank, "得分": score,
                "判定": label, "rule": offered[hit].get("rule") or ""}
    earliest, latest = valid[0][1], valid[-1][1]
    if obs < earliest:
        return {"可评": True, "命中": False, "名次": None, "得分": YQ_SCORE["early"],
                "判定": "提前于全部候选", "rule": offered[0].get("rule") or ""}
    if obs > latest:
        return {"可评": True, "命中": False, "名次": None, "得分": YQ_SCORE["overrun"],
                "判定": f"超期（末位候选 {latest}）", "rule": ""}
    return {"可评": True, "命中": False, "名次": None, "得分": YQ_SCORE["late"],
            "判定": "候选窗口内但日期未对齐", "rule": ""}


def report(res: dict) -> None:
    """逐例判定 + 汇总输出（口径声明带样本量）。"""
    cases = res.get("cases") or []
    if not cases:
        print("档案内无已回填的占问（divinations[].outcome.recorded 非 null）。")
        return
    for c in cases:
        yq = c["应期"] or {}
        yq_txt = yq.get("判定") or "应期未评"
        if yq.get("名次"):
            yq_txt += f"（第{yq['名次']}位候选）"
        rule = yq.get("rule") or ""
        if rule:
            yq_txt += f"｜法则：{rule}"
        hit = c.get("断事") or "断事未评"
        print(f"  {c['event_id']}〔{c['discipline']}·{c.get('direction')}〕{c['asked']}"
              f"\n    回填：{c['judged'] or '未评'}"
              f"（{c['occurred_at'] or '无日期'}）→ 断事{hit}；应期：{yq_txt}")
    n = res["n_回填"]
    print(f"\n现实回填命中汇总（集合 = 本档案已回填占问，n={n}）")
    print(f"  断事可评 {res['n_断事可评']} 例 → 应验 {res['断事应验']}"
          f" / 部分 {res['断事部分']} / 未验 {res['n_断事可评'] - res['断事应验'] - res['断事部分']}"
          f"（应验率 {res['断事应验率'] or '—'}%）")
    print(f"  应期可评 {res['n_应期可评']} 例 → 命中 {res['应期命中']}"
          f"（命中率 {res['应期命中率'] or '—'}%）")
    for d, b in sorted((res.get("by_discipline") or {}).items()):
        print(f"    {d}：回填 {b['n']}，断事应验 {b['hit']}/{b['judged']}，"
              f"应期命中 {b['yq_hit']}/{b['yq_eval']}")
    print("口径：断事命中按 judged 判定；应期命中按六爻结构化候选名次（第 1 位主应期）。"
          "本分数为现实回填命中，非古籍对齐分，不代表预测率。")
