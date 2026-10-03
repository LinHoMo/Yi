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

判定口径与得分表**不在此处持有**：唯一真值源在 `yishu_core.yingqi`（架构评审 A2
把合参层与六爻侧两套并行实现收成一份，门 `tools/check.py [1i]` 锁死）。

2026-10-03 反馈模型统一：本模块的评估路径改为**先经 canonical FeedbackRecord**
（`core/yishu_core/feedback.py` 的 adapter）再判定——档案条目与六爻落盘记录
折叠成同一记录形态后进入评分；输出结构与口径不变。六爻侧
`dev_tools/feedback_store.py` 同步提供 `load_all_canonical()`，两条链的记录
形态自此同源（存储与判定口径仍各自保留）。
"""
from __future__ import annotations

from yishu_core.eval import verdict_direction
from yishu_core.feedback import (  # noqa: F401  （canonical 反馈模型）
    FeedbackRecord,
    from_synthesis_divination,
    judge_record,
    validate_record_set,
)
from yishu_core.yingqi import (  # noqa: F401  （YQ_SCORE 为对外旧名的再导出）
    RANK_CALIBER,
    RANK_SCORE as YQ_SCORE,
    judge_rank as _judge_rank,
    rate as _rate,
)

# 断事命中判定：judged → 断事结果
JUDGED_TO_HIT = {"应验": "应验", "部分应验": "部分", "未应验": "未验", "超期未验": "未验(超期)"}


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
        # canonical 反馈记录（形态统一的唯一入口；字段映射不改变判定语义）
        rec = from_synthesis_divination(div)
        discipline = rec["discipline"] or "?"
        judged = rec.get("judged") or ""
        occurred = rec.get("occurred_at") or ""
        row = {
            "event_id": rec.get("event_id") or div.get("event_id"),
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

        yq = _eval_record_yingqi(rec)
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


def _eval_record_yingqi(rec: dict) -> dict | None:
    """canonical 记录的应期判定（名次制，口径见 `yishu_core.yingqi`）。

    非六爻（其余学科目前无可评的结构化候选）或未声明名次制口径 → None。
    """
    if rec.get("discipline") != "liuyao":
        return None
    if rec.get("evaluation_policy") != "rank":
        return None
    return judge_record(rec)["judgement"]


def _eval_yingqi(div: dict, occurred: str | None) -> dict | None:
    """兼容入口（selfcheck_scoring 与既有调用方）：档案条目 → canonical → 判定。"""
    rec = from_synthesis_divination(div)
    rec["occurred_at"] = occurred or ""
    return _eval_record_yingqi(rec)


def eval_feedback_records(records: list[dict]) -> dict:
    """canonical FeedbackRecord 集合 → 现实效度汇总（与 eval_outcomes 同形）。

    供未来学科与导出数据使用：任何链路只要折叠成 canonical 记录即可入评。
    真实/合成混集直接抛错（`validate_record_set` 强制物理/语义分离）；
    合成回归数据只允许在测试夹具里单独成集，永不进真实效度统计。
    """
    errs = validate_record_set(records)
    if errs:
        raise ValueError("反馈记录集不合规：" + "；".join(errs))

    cases: list[dict] = []
    n_judged = n_hit = n_partial = 0
    n_yq_eval = n_yq_hit = 0
    by_discipline: dict[str, dict] = {}

    for rec in records or []:
        discipline = rec.get("discipline") or "?"
        judged = rec.get("judged") or ""
        hit = _judged_hit(judged)
        yq = _eval_record_yingqi(rec)
        row = {
            "event_id": rec.get("event_id"),
            "discipline": discipline,
            "asked": str(rec.get("question") or "")[:40],
            "direction": {1: "吉", -1: "凶", 0: "平"}[verdict_direction(rec.get("prediction"))],
            "judged": judged,
            "occurred_at": rec.get("occurred_at") or "",
            "recorded": str(rec.get("observed_outcome") or "")[:60],
            "断事": hit,
            "应期": yq,
        }
        if hit:
            n_judged += 1
            if hit == "应验":
                n_hit += 1
            elif hit == "部分":
                n_partial += 1
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


def selfcheck_scoring() -> None:
    """评分表自洽（表驱动）：把 `YQ_SCORE` 的 7 个档位各跑一次**真实判定路径**，断言取值与单调性。

    背景（架构评审 A7）：`YQ_SCORE` 长期只是纸面常量——档案空集直接非零退出，
    整条评分链从未被断言跑过一次，改坏评分表不会被任何门发现。本自检**不依赖任何真实回填数据**
    （纯函数、可进常驻门），只锁「名次→得分」映射不被改坏。
    """
    cands = ["2026-10-01", "2026-10-05", "2026-10-10", "2026-10-15"]
    div = {"discipline": "liuyao",
           "yingqi_offered": [{"date": d, "rule": f"r{i}"} for i, d in enumerate(cands)]}

    def _score(occurred: str) -> dict:
        yq = _eval_yingqi(div, occurred)
        assert yq and yq.get("可评"), (occurred, yq)
        return yq

    # ① 档位**路由**：同一份候选，不同 occurred_at 必须落到正确档（非恒真断言）
    assert _score("2026-10-01")["名次"] == 1, "首位候选应为第 1 名"
    assert _score("2026-10-05")["名次"] == 2, "第 2 位候选应为第 2 名"
    assert _score("2026-10-10")["名次"] == 3
    assert _score("2026-10-15")["名次"] == 4
    assert _score("2026-09-01")["判定"].startswith("提前"), "早于全部候选 → 提前档"
    assert _score("2026-10-03")["判定"].startswith("候选窗口内"), "窗口内未对齐 → late 档"
    assert _score("2026-11-01")["判定"].startswith("超期"), "晚于末位候选 → 超期档"

    # ② 边界字面量：主应期全分、超期零分（表被改坏即红）
    assert YQ_SCORE[1] == 1.0, "主应期应记全分"
    assert YQ_SCORE["overrun"] == 0.0, "超期未验应记 0"
    # ③ 单调性：名次越靠后得分越低；提前与窗口内未对齐同档
    order = [YQ_SCORE[1], YQ_SCORE[2], YQ_SCORE[3], YQ_SCORE[4], YQ_SCORE["late"]]
    assert all(order[i] > order[i + 1] for i in range(len(order) - 1)), \
        f"应期得分须随名次单调递减，实为 {order}"
    assert YQ_SCORE["early"] == YQ_SCORE["late"], "提前与窗口内未对齐应同档（均非命中）"


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
    print("口径：" + RANK_CALIBER + " 断事命中按 judged 判定。")
