# -*- coding: utf-8 -*-
"""Canonical FeedbackRecord —— 现实反馈的唯一 schema 与评估入口。

本仓现存的真实反馈链（架构评审已确认口径差别是真实差别，不合并判定逻辑）：

  · 六爻 `liuyao/dev_tools/feedback_store.py`（读学科落盘反馈，容差窗）

本模块把该链的**记录形态**收成一份，并提供**唯一的现实效度评估入口**
`evaluate_records()`：任何来源的反馈经 adapter 折叠为同一 FeedbackRecord 后，
统计、导出只需面对一种形状、跑同一条评分路径。

纪律：
  * **不是平行反馈系统**：不新增存储路径；旧链继续各自落盘，
    adapter 是纯粹的形态映射（dict → dict）。
  * **真实/合成物理语义分离**：`provenance.kind` ∈ {real_outcome, synthetic_regression}；
    real_outcome 只能来自真实回填链；synthetic_regression 只允许存在于测试/回归
    夹具（tests/、tools scratch），禁止混入任何真实统计集合。`validate_record_set`
    对混合 kind 直接判失败。
  * **应期判定不在此处实现**：judge_record 按 evaluation_policy 转调
    `yishu_core.yingqi` 的 judge_rank / judge_window——评分表、容差常量、支关系表
    仍只有内核一份。
  * **口径诚实（SKILL.md）**：`evaluate_records` 产出的是**现实回填命中**，
    不是古籍案例对齐分，更不等于「预测率」。任何报分必须带样本量 n 与集合名。
"""
from __future__ import annotations

from typing import TypedDict

from yishu_core.eval import verdict_direction
from yishu_core.yingqi import (  # noqa: F401  （判定真值源，转调用）
    RANK_CALIBER,
    RANK_SCORE,
    WINDOW_CALIBER,
    judge_rank as _judge_rank,
    judge_window as _judge_window,
    rate as _rate,
)

FEEDBACK_SCHEMA_VERSION = "1.0.0"

# 断事判定词汇（唯一真值源；任何消费方自此处引用，不得另立一份）
JUDGED_VALUES = ("应验", "未应验", "部分应验", "超期未验")

# evaluation_policy：反馈记录声明的应期判定口径（与 yingqi 两制一一对应）
POLICY_RANK = "rank"            # 名次制：候选有序，命中第 k 位按名次给分
POLICY_WINDOW = "window"        # 容差窗：预测日集合，实际日期落窗即命中
POLICY_CALIBERS = {POLICY_RANK: RANK_CALIBER, POLICY_WINDOW: WINDOW_CALIBER}

# 反馈来源系统（provenance.source_system 取值；新学科接入在此登记）
SOURCE_SYSTEMS = ("liuyao.feedback_store", "liuyao.event_logger", "bazi.feedback_store")

# 反馈性质（真实 vs 合成——物理语义分离的唯一开关）
KIND_REAL = "real_outcome"
KIND_SYNTHETIC = "synthetic_regression"
PROVENANCE_KINDS = (KIND_REAL, KIND_SYNTHETIC)


class FeedbackRecord(TypedDict, total=False):
    event_id: str            # 事件唯一 id（与来源系统的事件 id 对齐）
    discipline: str          # 学科
    question: str            # 占问原话
    prediction: str          # 断语主判（verdict/方向文本）
    predicted_timing: list   # 结构化应期候选 [{"date": "YYYY-MM-DD", "rule": str}]，顺序即名次
    observed_outcome: str    # 回填的现实结果描述
    occurred_at: str         # 现实发生日 YYYY-MM-DD（应期判定入参）
    judged: str              # 断事判定：JUDGED_VALUES 之一；来源系统未判则 ""
    evaluation_policy: str   # POLICY_RANK / POLICY_WINDOW；无结构化候选则 ""
    provenance: dict         # {"kind", "source_system", "recorded_at", ...}


# ────────────────────────────────────────────────────────────────
# 校验
# ────────────────────────────────────────────────────────────────

def validate_feedback_record(rec: dict) -> list[str]:
    """单条记录校验；返回违规清单（空 = 合规）。每条附字段路径。"""
    errs: list[str] = []
    if not isinstance(rec, dict):
        return ["record 必须是 dict"]
    if not rec.get("event_id"):
        errs.append("event_id 缺失")
    if not rec.get("discipline"):
        errs.append("discipline 缺失")
    judged = rec.get("judged") or ""
    if judged and judged not in JUDGED_VALUES:
        errs.append(f"judged 须在 {JUDGED_VALUES}，收到 {judged!r}")
    policy = rec.get("evaluation_policy") or ""
    if policy and policy not in POLICY_CALIBERS:
        errs.append(f"evaluation_policy 须在 {list(POLICY_CALIBERS)}，收到 {policy!r}")
    occurred = rec.get("occurred_at") or ""
    if occurred:
        from yishu_core.yingqi import parse_date
        if parse_date(occurred) is None:
            errs.append(f"occurred_at 应为 YYYY-MM-DD，收到 {occurred!r}")
    timing = rec.get("predicted_timing") or []
    if not isinstance(timing, list):
        errs.append("predicted_timing 须为 list")
    else:
        for i, it in enumerate(timing):
            if not isinstance(it, dict) or not it.get("date"):
                errs.append(f"predicted_timing[{i}] 须为 {{date, rule}} 且 date 非空")
                break
    prov = rec.get("provenance") or {}
    if not isinstance(prov, dict):
        errs.append("provenance 须为 dict")
    else:
        if prov.get("kind") not in PROVENANCE_KINDS:
            errs.append(f"provenance.kind 须在 {PROVENANCE_KINDS}，收到 {prov.get('kind')!r}")
        if not prov.get("source_system"):
            errs.append("provenance.source_system 缺失")
    return errs


def validate_record_set(records: list[dict]) -> list[str]:
    """记录集合校验：逐条合规 + **真实/合成不得混集**（物理语义分离）。"""
    errs: list[str] = []
    kinds: set[str] = set()
    for i, rec in enumerate(records or []):
        for e in validate_feedback_record(rec):
            errs.append(f"[{i}] {e}")
        prov = (rec or {}).get("provenance") or {}
        if prov.get("kind"):
            kinds.add(prov["kind"])
    if len(kinds) > 1:
        errs.append(f"记录集合混入多种 provenance.kind：{sorted(kinds)}"
                    "——真实回填与合成回归数据必须物理/语义分离")
    return errs


# ────────────────────────────────────────────────────────────────
# Adapter：既有反馈链 → canonical record（纯映射）
# ────────────────────────────────────────────────────────────────

def from_liuyao_feedback(rec: dict) -> FeedbackRecord:
    """六爻 FeedbackStore 落盘记录 → FeedbackRecord（容差窗）。

    六爻侧只判应期（hit_strict/hit_loose），不断事——judged 留空，不虚构判定。
    """
    dates = [str(d) for d in (rec.get("predicted_dates") or []) if d]
    occurred = str(rec.get("actual_date") or "")
    prov = {
        "kind": KIND_REAL,
        "source_system": "liuyao.feedback_store",
        "recorded_at": str(rec.get("timestamp") or ""),
    }
    if rec.get("chart_id"):
        prov["chart_id"] = str(rec["chart_id"])
    return FeedbackRecord(
        event_id=str(rec.get("id") or ""),
        discipline=str(rec.get("discipline") or "liuyao"),
        question=str(rec.get("question") or ""),
        prediction=str(rec.get("predicted_main_yingqi") or ""),
        predicted_timing=[{"date": d, "rule": ""} for d in dates],
        observed_outcome=occurred,
        occurred_at=occurred,
        judged="",  # 六爻 store 不断事；不得把应期命中冒充断事判定
        evaluation_policy=POLICY_WINDOW if dates else "",
        provenance=prov,
    )


def from_bazi_feedback(rec: dict) -> FeedbackRecord:
    """八字 `reading_events` 落盘记录 → FeedbackRecord（断事判定）。

    八字科不作应期承诺 ⇒ `predicted_timing` 留空、`evaluation_policy` 留空；
    只把**断事方向**（格局／用神／层次之断）与后来人记的**实际情形**并列，judged 由人填。
    """
    prov = {
        "kind": KIND_REAL,
        "source_system": "bazi.feedback_store",
        "recorded_at": str(rec.get("recorded_at") or ""),
    }
    if rec.get("source_note"):
        prov["source_note"] = str(rec["source_note"])
    return FeedbackRecord(
        event_id=str(rec.get("event_id") or ""),
        discipline="bazi",
        question=str(rec.get("question") or ""),
        prediction=str(rec.get("engine_claim") or ""),
        predicted_timing=[],
        observed_outcome=str(rec.get("actual_outcome") or ""),
        occurred_at=str(rec.get("occurred_at") or ""),
        judged=str(rec.get("judged") or ""),
        evaluation_policy="",
        provenance=prov,
    )


def synthetic_record(*, event_id: str, discipline: str, question: str = "",
                     prediction: str = "", predicted_timing: list | None = None,
                     occurred_at: str = "", judged: str = "",
                     evaluation_policy: str = "",
                     source_system: str = "test.fixture") -> FeedbackRecord:
    """合成回归记录构造器（kind=synthetic_regression）。

    只允许测试 / 回归夹具调用：合成数据永远不进真实统计集合
    （validate_record_set 对混 kind 判失败）。
    """
    return FeedbackRecord(
        event_id=event_id,
        discipline=discipline,
        question=question,
        prediction=prediction,
        predicted_timing=list(predicted_timing or []),
        observed_outcome=occurred_at,
        occurred_at=occurred_at,
        judged=judged,
        evaluation_policy=evaluation_policy,
        provenance={
            "kind": KIND_SYNTHETIC,
            "source_system": source_system,
        },
    )


# ────────────────────────────────────────────────────────────────
# 判定（转调 yishu_core.yingqi——口径唯一真值源，本模块不持有任何常量表）
# ────────────────────────────────────────────────────────────────

def judge_record(rec: dict) -> dict:
    """按记录声明的口径判定应期，返回 {"policy", "caliber", "judgement"}。

    无口径 / 无候选 / 无发生日 → {"policy": …, "judgement": None}（不评，不进分母）。
    """
    policy = rec.get("evaluation_policy") or ""
    timing = rec.get("predicted_timing") or []
    occurred = rec.get("occurred_at") or ""
    if policy not in POLICY_CALIBERS or not timing or not occurred:
        return {"policy": policy, "caliber": POLICY_CALIBERS.get(policy, ""),
                "judgement": None}
    if policy == POLICY_RANK:
        judgement = _judge_rank(timing, occurred)
    else:
        dates = [it.get("date") for it in timing if isinstance(it, dict) and it.get("date")]
        jw = _judge_window(dates, occurred)
        # 容差窗双档并列（严格/宽松是同一口径的两个窗宽，非两种口径）
        judgement = {"可评": True, "命中": jw["hit_strict"],
                     "宽松命中": jw["hit_loose"], "判定":
                     ("严格命中" if jw["hit_strict"] else
                      "宽松命中" if jw["hit_loose"] else "未命中")}
    return {"policy": policy, "caliber": POLICY_CALIBERS[policy], "judgement": judgement}


# ────────────────────────────────────────────────────────────────
# 现实效度评估（唯一入口）：canonical 记录集合 → 汇总
# ────────────────────────────────────────────────────────────────

# 断事命中判定：judged → 断事结果
_JUDGED_TO_HIT = {"应验": "应验", "部分应验": "部分",
                  "未应验": "未验", "超期未验": "未验(超期)"}


def _judged_hit(judged: str | None) -> str | None:
    if not judged:
        return None
    return _JUDGED_TO_HIT.get(judged, "未验")


def _eval_record_yingqi(rec: dict) -> dict | None:
    """canonical 记录的应期判定（按记录自报口径；无可评候选 → None）。"""
    if rec.get("evaluation_policy") != POLICY_RANK:
        return None
    return judge_record(rec)["judgement"]


def evaluate_records(records: list[dict]) -> dict:
    """canonical FeedbackRecord 集合 → 现实效度汇总（逐例判定 + 汇总计数）。

    真实/合成混集直接抛错（`validate_record_set` 强制物理/语义分离）；
    合成回归数据只允许在测试夹具里单独成集，永不进真实效度统计。
    口径：这是**现实回填命中**，不是古籍案例对齐分，更不等于预测率（SKILL.md）。
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
        by = by_discipline.setdefault(
            discipline, {"n": 0, "judged": 0, "hit": 0, "yq_eval": 0, "yq_hit": 0})
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


def report_records(res: dict) -> None:
    """逐例判定 + 汇总输出（口径声明带样本量 n 与集合名）。"""
    cases = res.get("cases") or []
    if not cases:
        print("集合内无已回填的反馈记录（occurred_at / judged 齐全者才入统计）。")
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
    print(f"\n现实回填命中汇总（集合 = 本次传入的 canonical 记录，n={n}）")
    print(f"  断事可评 {res['n_断事可评']} 例 → 应验 {res['断事应验']}"
          f" / 部分 {res['断事部分']} / 未验 {res['n_断事可评'] - res['断事应验'] - res['断事部分']}"
          f"（应验率 {res['断事应验率'] or '—'}%）")
    print(f"  应期可评 {res['n_应期可评']} 例 → 命中 {res['应期命中']}"
          f"（命中率 {res['应期命中率'] or '—'}%）")
    for d, b in sorted((res.get("by_discipline") or {}).items()):
        print(f"    {d}：回填 {b['n']}，断事应验 {b['hit']}/{b['judged']}，"
              f"应期命中 {b['yq_hit']}/{b['yq_eval']}")
    print("口径：" + RANK_CALIBER + " 断事命中按 judged 判定。")


def selfcheck_scoring() -> None:
    """评分表自洽（表驱动）：把 `RANK_SCORE` 的各档位各跑一次**真实判定路径**。

    背景（架构评审 A7）：评分表长期只是纸面常量——空集合直接非零退出，
    整条评分链从未被断言跑过一次，改坏评分表不会被任何门发现。本自检**不依赖任何
    真实回填数据**（纯函数、可进常驻门），只锁「名次→得分」映射不被改坏。
    """
    cands = ["2026-10-01", "2026-10-05", "2026-10-10", "2026-10-15"]
    rec = synthetic_record(
        event_id="SELFCHK", discipline="liuyao",
        predicted_timing=[{"date": d, "rule": f"r{i}"} for i, d in enumerate(cands)],
        evaluation_policy=POLICY_RANK)

    def _score(occurred: str) -> dict:
        r = dict(rec)
        r["occurred_at"] = occurred
        yq = _eval_record_yingqi(r)
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
    assert RANK_SCORE[1] == 1.0, "主应期应记全分"
    assert RANK_SCORE["overrun"] == 0.0, "超期未验应记 0"
    # ③ 单调性：名次越靠后得分越低；提前与窗口内未对齐同档
    order = [RANK_SCORE[1], RANK_SCORE[2], RANK_SCORE[3], RANK_SCORE[4], RANK_SCORE["late"]]
    assert all(order[i] > order[i + 1] for i in range(len(order) - 1)), \
        f"应期得分须随名次单调递减，实为 {order}"
    assert RANK_SCORE["early"] == RANK_SCORE["late"], "提前与窗口内未对齐应同档（均非命中）"
