# -*- coding: utf-8 -*-
"""Discipline Registry: 机器可读的学科能力清单。

Capability / 评测状态 的唯一真值源。CLI / Web / Actions / 文档都通过本模块查询
"某学科是否支持某能力、评测到什么程度"，而非各自维护列表。

两级状态（2026-10-03 证据链收敛，各自回答不同的问题，禁止混用）：

  CapabilityStatus —— 「这个能力是什么性质」：
    stable          - 能力稳定,机械基线（golden/回归）已锁,可安全对外
    experimental    - 能力已实现但机械基线未稳 / 覆盖率不全
    mechanical_only - 只输出机械结构标签,不含吉凶断语（如大六壬骨架）
    source_only     - 输出为古籍原文直录,本科不做任何独立推断（如灵棋经查表）
    unavailable     - 本版本不提供

  EvaluationBaseline —— 「这个能力的结论有没有独立评测覆盖」（评测成熟度）：
    classical_holdout    - 古籍案例 tune/holdout 对齐评测已建（tune/holdout 分列出分）
    external_holdout     - 另有永不调参的外部独立集（样本量见各科评测,禁止虚报精度）
    mechanical_regression - 只有规则自洽回归 / golden 指纹,无古籍对齐分
    source_only          - 书源直录,无评测（也不需要常规评测,忠实度门即其基线）
    unassessed           - 尚无任何评测覆盖

分数本身**不放在本表**（读数会漂移）：分数唯一权威源是 `docs/HANDOFF.md` §一,
口径变更史在 `docs/CHANGELOG.md`。本表只声明「哪类评测存在」,两者引用不复制。

`evaluation_splits` 只登记**通用评测种类**（tune / holdout / external_holdout /
yingqi_holdout / mechanical_consistency 等）；具体 split 标识符（含案例语料命名）
的唯一真值源是各科 `evaluate.py` 的 `--split choices`——内核不持有案例语料名
（铁律二隔离边界的静态门会拦截）。

agent_available 的回答：`yishu_core.agent` 的五个稳定入口对八科一律可用
（capabilities / validate_request / run_report / get_evidence / get_evaluation_status）,
学科差异全部由本表承载——Agent 不需要知道某科内部用了哪个脚本。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from yishu_core.report import DISCIPLINES

CapabilityStatus = Literal[
    "stable", "experimental", "mechanical_only", "source_only", "unavailable",
]
EvaluationBaseline = Literal[
    "classical_holdout", "external_holdout", "mechanical_regression",
    "source_only", "unassessed",
]

# 两级状态词表（供校验门 / 文档生成器引用）
CAPABILITY_STATUSES: tuple[str, ...] = (
    "stable", "experimental", "mechanical_only", "source_only", "unavailable",
)
EVALUATION_BASELINES: tuple[str, ...] = (
    "classical_holdout", "external_holdout", "mechanical_regression",
    "source_only", "unassessed",
)


@dataclass(frozen=True)
class DisciplineCapability:
    """单个学科的能力声明。"""
    discipline: str
    chart: CapabilityStatus = "stable"
    analyze: CapabilityStatus = "stable"
    evidence: CapabilityStatus = "stable"
    render: CapabilityStatus = "stable"
    narrate: CapabilityStatus = "stable"
    mcp: CapabilityStatus = "unavailable"          # MCP 10-01g 已清除,未来再议
    external_evaluation: CapabilityStatus = "unavailable"
    holdout: CapabilityStatus = "unavailable"
    synthesis: CapabilityStatus = "stable"
    source_provenance: CapabilityStatus = "stable"
    outcome_feedback: CapabilityStatus = "experimental"
    evaluation_baseline: EvaluationBaseline = "unassessed"
    # 该科已建的评测分列（结构性事实,非分数；分数读 docs/HANDOFF.md §一）
    evaluation_splits: tuple[str, ...] = ()
    maturity_note: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "discipline": self.discipline,
            "chart": self.chart,
            "analyze": self.analyze,
            "evidence": self.evidence,
            "render": self.render,
            "narrate": self.narrate,
            "mcp": self.mcp,
            "external_evaluation": self.external_evaluation,
            "holdout": self.holdout,
            "synthesis": self.synthesis,
            "source_provenance": self.source_provenance,
            "outcome_feedback": self.outcome_feedback,
            "evaluation_baseline": self.evaluation_baseline,
            "evaluation_splits": list(self.evaluation_splits),
            "maturity_note": self.maturity_note,
        }


_REGISTRY: dict[str, DisciplineCapability] = {}


def _build_registry() -> dict[str, DisciplineCapability]:
    """构建能力注册表: 默认八科均 stable, 再逐科覆盖差异。"""
    reg: dict[str, DisciplineCapability] = {}
    for d in DISCIPLINES:
        reg[d] = DisciplineCapability(discipline=d)

    # 六爻: 全能力最完整；外部独立候选集（书源例，永不调参——语料命名清单
    # 唯一真值源是该科 evaluate.py 的 --split choices，内核不持有案例语料名）
    reg["liuyao"] = DisciplineCapability(
        discipline="liuyao",
        external_evaluation="stable",
        holdout="stable",
        evaluation_baseline="classical_holdout",
        evaluation_splits=("tune", "holdout", "yingqi_holdout", "external_holdout"),
        maturity_note="评测基线最严格；外部独立候选集与读数见 docs/HANDOFF.md §一",
    )
    # 命科
    reg["ming"] = DisciplineCapability(
        discipline="ming",
        external_evaluation="unavailable",
        holdout="stable",
        evaluation_baseline="classical_holdout",
        evaluation_splits=("tune", "holdout"),
        maturity_note="古籍案例对齐评测已建（调候/格局成败/从格分维度）；外部独立集待建（语料已取得,判据未落地）",
    )
    # 紫微：机械结构（安星/格局查找）有 golden+回归锁,但无案例对齐评测
    reg["ziwei"] = DisciplineCapability(
        discipline="ziwei",
        external_evaluation="unavailable",
        holdout="unavailable",
        evaluation_baseline="mechanical_regression",
        maturity_note="无案例对齐评测, 只有机械自检与行为指纹",
    )
    # 梅花：古籍对齐评测已建, 另有 n=4 外部独立集（永不调参, 只报命中数不报百分比）
    reg["meihua"] = DisciplineCapability(
        discipline="meihua",
        external_evaluation="stable",
        holdout="stable",
        evaluation_baseline="classical_holdout",
        evaluation_splits=("tune", "holdout", "external_holdout"),
        maturity_note="external_holdout 已建（n=4, 永不调参；语料与读数见 meihua docs/EVAL-AUDIT.md）",
    )
    # 小六壬：只有规则自洽回归（engine_derived）, 无古籍对齐分
    reg["xiaoliuren"] = DisciplineCapability(
        discipline="xiaoliuren",
        external_evaluation="unavailable",
        holdout="unavailable",
        evaluation_baseline="mechanical_regression",
        evaluation_splits=("tune", "holdout"),
        maturity_note="tune/holdout 为规则自洽回归, 非古籍对齐；外部集待建",
    )
    # 择吉：同小六壬——评测框架已搭但基准 engine_derived, 古籍日例应验 0 例
    reg["zeji"] = DisciplineCapability(
        discipline="zeji",
        external_evaluation="unavailable",
        holdout="unavailable",
        evaluation_baseline="mechanical_regression",
        evaluation_splits=("tune", "holdout"),
        maturity_note="基准 engine_derived（自洽回归）；古籍日例外部集待建",
    )
    # 大六壬：机械骨架（结构标签, 无吉凶断语）；43 例三传机械一致率（书源例,测结构非吉凶）
    reg["liuren"] = DisciplineCapability(
        discipline="liuren",
        analyze="mechanical_only",
        external_evaluation="experimental",
        holdout="unavailable",
        evaluation_baseline="mechanical_regression",
        evaluation_splits=("mechanical_consistency",),
        maturity_note="机械骨架: 结构标签无吉凶；43 例机械一致率只验三传结构, 非吉凶评测",
    )
    # 灵棋经：查表直录 124 课书源断语, 本科不做独立推断
    reg["lingqi"] = DisciplineCapability(
        discipline="lingqi",
        analyze="source_only",
        narrate="source_only",
        external_evaluation="unavailable",
        holdout="unavailable",
        evaluation_baseline="source_only",
        maturity_note="查表直录《靈棋經》124 课原文断语, 吉凶属原文文本非本仓推断",
    )
    return reg


_REGISTRY = _build_registry()


def list_disciplines() -> list[str]:
    """列出本版本所有学科 (与 yishu_core.report.DISCIPLINES 同序)。"""
    return list(DISCIPLINES)


def discipline_capability(disc: str) -> DisciplineCapability:
    """查询单科能力。"""
    if disc not in _REGISTRY:
        raise ValueError(f"未知学科: {disc!r}")
    return _REGISTRY[disc]


def all_capabilities() -> list[DisciplineCapability]:
    """列出全部学科能力 (注册表顺序)。"""
    return [_REGISTRY[d] for d in DISCIPLINES]


def capability_matrix() -> list[dict[str, str]]:
    """机器可读能力矩阵 (用于文档 / README 渲染)。"""
    return [dc.to_dict() for dc in all_capabilities()]


def supports(disc: str, capability: str) -> bool:
    """判定学科是否具备某能力 (unavailable 之外都算"具备")。"""
    dc = _REGISTRY.get(disc)
    if dc is None:
        return False
    status = getattr(dc, capability, "unavailable")
    return status != "unavailable"


def evaluation_baseline_of(disc: str) -> EvaluationBaseline:
    """学科评测基线（Evidence.evaluation_status 的学科级默认值）。"""
    return discipline_capability(disc).evaluation_baseline
