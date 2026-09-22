# -*- coding: utf-8 -*-
"""`yishu_core` —— 中国传统道数的共用历法与象数内核。

学科层（六爻 / 梅花 / 八字 …）只允许 `import yishu_core.*`，
不得在本地复制干支、五行、卦表等真值数据。

版本号 **全项目唯一真值源** 在此处（易 0.0.1 起）：
pyproject、门户、SKILL.md、文档与质量门都从这里读，不要再各写一份。
`python tools/check.py` 会检查是否有人又写了第二份。
"""
__version__ = "0.0.1"

from .ganzhi_calendar import (  # noqa: E402
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
    GanzhiMoment,
    day_ganzhi_index,
    ganzhi_of,
    ganzhi_pair,
    hour_branch_index,
    solar_term_instant,
    solar_terms_of_year,
)

__all__ = [
    "__version__",
    "HEAVENLY_STEMS", "EARTHLY_BRANCHES", "GanzhiMoment", "ganzhi_of", "ganzhi_pair",
    "day_ganzhi_index", "hour_branch_index", "solar_term_instant", "solar_terms_of_year",
]
