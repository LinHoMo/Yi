# -*- coding: utf-8 -*-
"""YiRuntime: Yi 的统一执行入口。

所有宿主 (CLI / GitHub Actions / Web / 未来 MCP) 都通过本包调用 Yi 引擎,
不再直接拼接命令行参数或起子进程。

from yishu_core.execution import YiRuntime
rt = YiRuntime()
result = rt.execute({"discipline": "liuyao", "question": ...})
print(result.markdown)
"""

from yishu_core.execution.runtime import YiRuntime, RuntimeResult
from yishu_core.execution.schemas import (
    RequestEnvelope,
    ChartEnvelope,
    AnalysisEnvelope,
    ResultEnvelope,
    SCHEMA_VERSION,
)
from yishu_core.execution.registry import (
    list_disciplines,
    discipline_capability,
    capability_matrix,
    supports,
)

__all__ = [
    "YiRuntime",
    "RuntimeResult",
    "RequestEnvelope",
    "ChartEnvelope",
    "AnalysisEnvelope",
    "ResultEnvelope",
    "SCHEMA_VERSION",
    "list_disciplines",
    "discipline_capability",
    "capability_matrix",
    "supports",
]
