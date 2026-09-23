# -*- coding: utf-8 -*-
"""六爻思维链：基元表 / 断语库 / 通用辅助 / 五步推演 / 应期 / 叙事组装。（拆分自 thinking_chain.py，纯搬移不改逻辑；聚合入口见 thinking_chain.py）。"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel, kernel_dir

_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    ADVANCE_PAIRS,
    BRANCH_ELEMENTS,
    BREAK_PAIRS,
    CHONG_PAIRS,
    EARTHLY_BRANCHES,
    EIGHT_PALACES,
    HEAVENLY_STEMS,
    HEXAGRAM_TRIGRAMS,
    HE_PAIRS,
    KE_CYCLE,
    NAJIA_BRANCHES,
    RETREAT_PAIRS,
    SHENG_CYCLE,
    STEM_ELEMENTS,
    TOMB_MAP,
    palace_of_key,
    EARTHLY_BRANCHES as BRANCHES,
)

from datetime import datetime, timedelta

import json

import re

from pathlib import Path


# ── 断语/引文库：外置 data/verdicts.json（AGENTS.md §三），代码只留算法与加载 ──
_VERDICTS_PATH = Path(__file__).resolve().parents[1] / "data" / "verdicts.json"


def _load_verdicts() -> dict:
    try:
        return json.loads(_VERDICTS_PATH.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"缺断语库 {_VERDICTS_PATH}（应随仓库一起检出）：{exc}")


_VERDICTS = _load_verdicts()
SHI_YAO_INTERPRETATION = _VERDICTS["shi_yao_interpretation"]
SHI_YAO_POEMS = _VERDICTS["shi_yao_poems"]
QUOTE_DATABASE = _VERDICTS["quote_database"]


_QUESTION_SCENARIO_KEYWORDS = {
    "marriage": ["婚", "恋", "感情", "喜欢", "女朋友", "男朋友", "对象", "正缘", "伴侣", "相亲", "姻缘", "爱"],
    "wealth": ["财", "投资", "求财", "赚钱", "收入", "利", "生意", "经营", "破财"],
    "illness": ["病", "健康", "疾", "医", "症", "身体", "患", "康复", "瘤", "炎"],
    "career": ["官", "升", "职", "事业", "工作", "仕", "考功", "升职", "提拔", "领导", "加薪"],
    "exam": ["考", "试", "学业", "成绩", "中", "秀才", "举人", "文", "读书", "高考", "笔试", "面试"],
    "lawsuit": ["讼", "官非", "法律", "诉讼", "被告", "原告", "起诉", "纠纷", "合同", "赔偿", "牢狱"],
    "travel": ["行", "出远门", "出行", "去某地", "旅行", "出差", "搬家", "移", "归", "返程"],
    "parents_illness": ["父病", "母病", "爸", "妈", "父亲", "母亲", "公公", "婆婆", "岳父", "岳母"],
}

