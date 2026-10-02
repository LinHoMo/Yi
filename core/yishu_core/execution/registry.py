# -*- coding: utf-8 -*-
"""Discipline Registry: 机器可读的学科能力清单。

Capability Matrix 的唯一真值源。CLI / Web / Actions 都通过本模块查询
"某学科是否支持某能力",而非各自维护列表。

成熟度级别:
  stable      - 能力稳定,评测基线已建,可安全对外
  experimental - 能力已实现但评测基线未稳 / 覆盖率不全
  unavailable  - 本版本不提供
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from yishu_core.report import DISCIPLINES, DISC_TITLE

CapabilityStatus = Literal["stable", "experimental", "unavailable"]


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
        }


_REGISTRY: dict[str, DisciplineCapability] = {}


def _build_registry() -> dict[str, DisciplineCapability]:
    """构建能力注册表: 默认八科均 stable, 再逐科覆盖差异。"""
    reg: dict[str, DisciplineCapability] = {}
    for d in DISCIPLINES:
        reg[d] = DisciplineCapability(discipline=d)

    # 六爻: 全能力最完整
    reg["liuyao"] = DisciplineCapability(
        discipline="liuyao",
        external_evaluation="stable",
        holdout="stable",
        maturity_note="评测基线最严格, 含 wikisource/huozhulin 外部集",
    )
    # 命科
    reg["ming"] = DisciplineCapability(
        discipline="ming",
        external_evaluation="stable",
        holdout="stable",
        maturity_note="246 例 holdout",
    )
    # 紫微
    reg["ziwei"] = DisciplineCapability(
        discipline="ziwei",
        external_evaluation="experimental",
        holdout="unavailable",
        maturity_note="无独立案例库, 无 holdout",
    )
    # 梅花
    reg["meihua"] = DisciplineCapability(
        discipline="meihua",
        external_evaluation="stable",
        holdout="stable",
        maturity_note="external_holdout 4 例 (永不调参)",
    )
    # 小六壬
    reg["xiaoliuren"] = DisciplineCapability(
        discipline="xiaoliuren",
        external_evaluation="unavailable",
        holdout="unavailable",
        maturity_note="外部集待建",
    )
    # 择吉
    reg["zeji"] = DisciplineCapability(
        discipline="zeji",
        external_evaluation="unavailable",
        holdout="unavailable",
        maturity_note="评测框架已搭, 未挂门",
    )
    # 大六壬
    reg["liuren"] = DisciplineCapability(
        discipline="liuren",
        external_evaluation="experimental",
        holdout="unavailable",
        maturity_note="机械一致率集, 未 tune/holdout 分列",
    )
    # 灵棋经
    reg["lingqi"] = DisciplineCapability(
        discipline="lingqi",
        external_evaluation="unavailable",
        holdout="unavailable",
        maturity_note="查表直录 124 课, 无自由推演",
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
    """判定学科是否具备某能力 (不论 stable/experimental 都算"具备")。"""
    dc = _REGISTRY.get(disc)
    if dc is None:
        return False
    status = getattr(dc, capability, "unavailable")
    return status != "unavailable"
