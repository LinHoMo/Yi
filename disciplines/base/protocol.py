"""四段契约 Protocol 定义。

各学科必须实现这 4 个 Protocol，mypy/运行时检查强制合规。
依赖方向：disciplines/base → core，不依赖具体学科。
"""
from __future__ import annotations

from typing import Protocol, Dict, Any, List, Optional, TypedDict, runtime_checkable


# ── 数据模型（与 disciplines/base/schema.json 同步） ──────────────────────

class ChartData(TypedDict, total=False):
    discipline: str
    timestamp: str          # ISO8601
    input_params: Dict[str, Any]
    chart: Dict[str, Any]   # 盘面具体数据


class Verdict(TypedDict, total=False):
    direction: str          # "吉" | "凶" | "平"
    confidence: float       # 0.0-1.0
    description: str


class AnalysisData(TypedDict, total=False):
    chart: Dict[str, Any]
    factors: List[Dict[str, Any]]
    verdict: Verdict
    basis: List[str]


class NarrativeData(TypedDict, total=False):
    summary: str
    reasoning: str
    advice: str


# ── 四段 Protocol ──────────────────────────────────────────────────────────

@runtime_checkable
class ChartProtocol(Protocol):
    """起卦 / 排盘接口。

    职责：纯确定性计算，无解读。输入参数 → 盘面结构。
    """

    def chart(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行排盘，返回 chart_data 结构。"""
        ...


@runtime_checkable
class AnalyzeProtocol(Protocol):
    """规则推演接口。

    职责：盘面 → 因子列表 + 吉凶方向 + 所本法则。
    """

    def analyze(self, chart: Dict[str, Any]) -> Dict[str, Any]:
        """执行推演，返回 analysis_data 结构。"""
        ...


@runtime_checkable
class NarrateProtocol(Protocol):
    """人话叙述接口。

    职责：推演数据 → 用户可读的正文叙述。
    """

    def narrate(self, analysis: Dict[str, Any]) -> str:
        """生成正文，返回 Markdown 格式字符串。"""
        ...


@runtime_checkable
class RenderProtocol(Protocol):
    """报告渲染接口。

    职责：推演数据 → 完整报告（HTML / PDF / Markdown）。
    """

    def render(self, analysis: Dict[str, Any], fmt: str = "html") -> str:
        """渲染报告，fmt ∈ {html, markdown, json}。"""
        ...


# ── 合规检查 ─────────────────────────────────────────────────────────────────

def check_protocols(module_name: str, obj: Any) -> Dict[str, bool]:
    """检查某学科实例是否实现了四段契约。

    返回 {"chart": bool, "analyze": bool, "narrate": bool, "render": bool}
    """
    return {
        "chart": isinstance(obj, ChartProtocol),
        "analyze": isinstance(obj, AnalyzeProtocol),
        "narrate": isinstance(obj, NarrateProtocol),
        "render": isinstance(obj, RenderProtocol),
    }
