# -*- coding: utf-8 -*-
"""Canonical FeedbackRecord —— 现实反馈的唯一 schema（P1 反馈模型统一）。

本仓有两条真实反馈链（架构评审已确认口径差别是真实差别，不合并判定逻辑）：

  · 合参层 `synthesis/outcome_eval.py`（读 person 档案 divinations[].outcome，名次制）
  · 六爻 `disciplines/liuyao/dev_tools/feedback_store.py`（读学科落盘反馈，容差窗）

两链的**存储**与**判定口径**各自保留（判定口径唯一真值源仍是
`core/yishu_core/yingqi.py`，门 `[1i]` 锁死）；本模块把两链的**记录形态**收成一份：
任何学科、任何宿主产生的反馈，经 adapter 折叠为同一 FeedbackRecord 后，
统计、导出、跨科汇总只需面对一种形状。

纪律：
  * **不是平行反馈系统**：不新增存储路径；两条旧链继续各自落盘，
    adapter 是纯粹的形态映射（dict → dict），可双向往返。
  * **真实/合成物理语义分离**：`provenance.kind` ∈ {real_outcome, synthetic_regression}；
    real_outcome 只能来自真实回填链；synthetic_regression 只允许存在于测试/回归
    夹具（tests/、tools scratch），禁止混入任何真实统计集合。`validate_record_set`
    对混合 kind 直接判失败。
  * **应期判定不在此处实现**：judge_record 按 evaluation_policy 转调
    `yishu_core.yingqi` 的 judge_rank / judge_window——评分表、容差常量、支关系表
    仍只有内核一份。
"""
from __future__ import annotations

from typing import TypedDict

from yishu_core.yingqi import (  # noqa: F401  （判定真值源，转调用）
    RANK_CALIBER,
    WINDOW_CALIBER,
    judge_rank as _judge_rank,
    judge_window as _judge_window,
)

FEEDBACK_SCHEMA_VERSION = "1.0.0"

# 断事判定词汇（唯一真值源在此；synthesis/person.JUDGED 自此处引用）
JUDGED_VALUES = ("应验", "未应验", "部分应验", "超期未验")
JUDGED = JUDGED_VALUES  # 对外旧名（synthesis/person 历史导出名），同一对象

# evaluation_policy：反馈记录声明的应期判定口径（与 yingqi 两制一一对应）
POLICY_RANK = "rank"            # 名次制：候选有序，命中第 k 位按名次给分
POLICY_WINDOW = "window"        # 容差窗：预测日集合，实际日期落窗即命中
POLICY_CALIBERS = {POLICY_RANK: RANK_CALIBER, POLICY_WINDOW: WINDOW_CALIBER}

# 反馈来源系统（provenance.source_system 取值；新学科接入在此登记）
SOURCE_SYSTEMS = ("synthesis.person", "liuyao.feedback_store", "liuyao.event_logger")

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
# Adapter：既有两条链 → canonical record（纯映射，双向可往返）
# ────────────────────────────────────────────────────────────────

def from_synthesis_divination(div: dict) -> FeedbackRecord:
    """合参档案 divinations[] 条目 → FeedbackRecord（名次制）。

    outcome.recorded is None（未回填）也照常折叠——judged/occurred_at 留空，
    统计侧以 `judged == ""` 识别「未回填，不进效度统计」。
    """
    oc = div.get("outcome") or {}
    offered = [{"date": str(it.get("date")), "rule": str(it.get("rule") or "")}
               for it in (div.get("yingqi_offered") or [])
               if isinstance(it, dict) and it.get("date")]
    return FeedbackRecord(
        event_id=str(div.get("event_id") or ""),
        discipline=str(div.get("discipline") or ""),
        question=str(div.get("asked") or ""),
        prediction=str(div.get("verdict") or ""),
        predicted_timing=offered,
        observed_outcome=str(oc.get("recorded") or "") if oc.get("recorded") else "",
        occurred_at=str(oc.get("occurred_at") or "") if oc.get("occurred_at") else "",
        judged=str(oc.get("judged") or "") if oc.get("judged") else "",
        evaluation_policy=POLICY_RANK if offered else "",
        provenance={
            "kind": KIND_REAL,
            "source_system": "synthesis.person",
            "recorded_at": str(oc.get("recorded") or "") if oc.get("recorded") else "",
        },
    )


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
