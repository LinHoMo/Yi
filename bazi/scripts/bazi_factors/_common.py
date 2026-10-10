# -*- coding: utf-8 -*-
"""pattern.py 拆解 —— 共享常量、导入、小工具函数（子模块都从这里取，不开第二份）。"""
from __future__ import annotations

import json as _json
import sys
from pathlib import Path as _Path

sys.path.insert(0, str(_Path(__file__).resolve().parents[2] / "core"))

from yishu_core.ming_tables import (  # noqa: E402
    dayun_direction,
    DAYS_PER_LUCK_YEAR,
    MONTHS_PER_DAY,
    tiaohou_of,
)
from yishu_core.ganzhi_calendar import TIGER_MONTH_STEM  # noqa: E402
from yishu_core.relations import STEM_YINYANG, stems_wuhe, ten_god  # noqa: E402
from yishu_core.symbols import (  # noqa: E402
    BRANCH_ELEMENTS,
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
    STEM_ELEMENTS,
    SHENG_CYCLE,
    KE_CYCLE,
    CHONG_PAIRS,
    HE_PAIRS,
    HARM_PAIRS,
    SAN_HE_GROUPS,
    SAN_HUI_GROUPS,
    sanxing_hits,
    twelve_growth,
)

# 成败救应/从格 basis 的书源引文唯一真值源在 data/verdicts.json（SKILL.md）
_MING_DATA = _Path(__file__).resolve().parents[2] / "data"
_MING_VERDICTS = _json.loads((_MING_DATA / "verdicts.json").read_text(encoding="utf-8"))
_CB = _MING_VERDICTS["格局成败引文"]
_CONG = _MING_VERDICTS["从格引文"]
_BING = _MING_VERDICTS["病药引文"]

# 十神 → 作用类
TEN_GOD_GROUP = {
    "比肩": "比劫",
    "劫财": "比劫",
    "正印": "印",
    "偏印": "印",
    "食神": "食伤",
    "伤官": "食伤",
    "正财": "财",
    "偏财": "财",
    "正官": "官杀",
    "偏官": "官杀",
    "七杀": "官杀",
}

# 日主之根的宫位分层
ROOT_STAGE_ELEMENTS = ("木", "火", "金", "水")
ROOT_HEAVY_STAGES = ("长生", "临官", "帝旺")
ROOT_HEAVY_W = 1.0
ROOT_LIGHT_W = 0.25

# 月令本气十神 → 正格名
PATTERN_BY_MONTH_GOD = {
    "正官": "正官格",
    "偏官": "偏官格",
    "七杀": "偏官格",
    "正印": "正印格",
    "偏印": "偏印格",
    "食神": "食神格",
    "伤官": "伤官格",
    "正财": "正财格",
    "偏财": "偏财格",
    "比肩": "建禄格",
    "劫财": "月刃格",
}

LAYER_WEIGHT = {"本气": 1.0, "中气": 0.5, "余气": 0.25}

WEAK_THRESHOLD = -1.5
STRONG_THRESHOLD = 1.5

JU_BONUS_W = 2.0

# 格局成败救应规则
PATTERN_CB_RULES = {
    "正官格": {"cheng": ("财", "印"), "ji": ("食伤",), "jiu": ("印",)},
    "偏官格": {"cheng": ("食伤", "印"), "ji": ("财",), "jiu": ("食伤", "印")},
    "正印格": {"cheng": ("官杀",), "ji": ("财",), "jiu": ("比劫",)},
    "偏印格": {"cheng": ("官杀",), "ji": ("财",), "jiu": ("比劫",)},
    "食神格": {"cheng": ("财",), "ji": ("印",), "jiu": ("财",)},
    "伤官格": {"cheng": ("财", "印"), "ji": ("官杀",), "jiu": ("印",)},
    "正财格": {"cheng": ("食伤", "正官"), "ji": ("七杀", "比劫"), "jiu": ("食伤", "正官")},
    "偏财格": {"cheng": ("食伤", "正官"), "ji": ("七杀", "比劫"), "jiu": ("食伤", "正官")},
    "建禄格": {"cheng": ("官杀", "财", "食伤"), "ji": ("印",), "jiu": ("财", "食伤")},
    "月刃格": {"cheng": ("官杀",), "ji": ("食伤", "财"), "jiu": ("印",)},
}
SHANGGUAN_CHENG_WITH_GUANSHA = True

# 十神组合
TEN_GOD_COMBO_RULES = (
    ("伤官见官", ("伤官",), ("正官",),
     "伤官与正官并透（《子平真诠》「伤官见官」）"),
    ("枭神夺食", ("偏印",), ("食神",),
     "偏印与食神并透（枭神夺食结构）"),
    ("食神制杀", ("食神",), ("偏官", "七杀"),
     "食神与七杀并透（食神制杀结构）"),
)

# 病药（五行层）
BING_RULES_BY_KE: dict[str, tuple[str, str, str]] = {
    "土": ("土厚埋金/土重埋身", "木", "source_backed_exact"),
    "木": ("木旺折身/木多塞塞", "金", "source_informed_generalization"),
    "金": ("金重伐身", "火", "source_informed_generalization"),
    "火": ("火炎焚身", "水", "source_informed_generalization"),
    "水": ("水泛身浮", "土", "source_informed_generalization"),
}

# 病药（十神层）
BING_RULES_BY_GOD: tuple[tuple[str, frozenset, str, frozenset, str, str], ...] = (
    ("比肩夺财", frozenset({"比肩", "劫财"}), "用财见比肩（劫财同类）为病",
     frozenset({"正官", "偏官", "七杀"}), "喜见官杀为药", "source_informed_generalization"),
    ("枭神夺食", frozenset({"偏印"}), "用食神伤官以印为病",
     frozenset({"正财", "偏财"}), "喜财为药", "source_backed_exact"),
    ("印重财轻", frozenset({"正印", "偏印"}), "印星太旺则财星受伤",
     frozenset({"正财", "偏财"}), "宜行财运以破其印", "source_informed_generalization"),
)

BING_YAO_THESIS = _BING["thesis"]

# 四柱干支关系书源依据
PILLAR_ORDER = ("year", "month", "day", "hour")
PILLAR_LABEL = {"year": "年", "month": "月", "day": "日", "hour": "时"}

_REL_BASIS = {
    "天干合": "天干五合：甲己／乙庚／丙辛／丁壬／戊癸（core.relations.STEM_WUHE）；"
              "《滴天髓·天干論》有丙辛、丁壬、戊癸相合之文；只判合之结构，不判化",
    "天干争合": "一干参与多个五合对（《滴天髓阐微》「天干三透戊土，争合癸水，则日主之情，"
               "竟无定见」；「虽合不化，有争合、妒合、分合之别」——bazi_hehua_adjudication.json）；"
               "只标结构，不判化、不批吉凶",
    "六合": "地支六合，两两相合（core.symbols.HE_PAIRS；通行子平）；只判合之结构，不判化",
    "六冲": "《滴天髓·地支論》「支神祇以沖為重，刑與害兮動不動」注：沖者必是相剋，所以必动",
    "六害": "《滴天髓·地支論》「支神祇以沖為重，刑與害兮動不動」；六害为地支相害（core.symbols.HARM_PAIRS）",
    "三刑": "《三命通会》三刑（無禮子卯／無恩寅巳申／恃勢丑戌未／自刑辰午酉亥）；core.symbols.sanxing_hits",
}


# ── 小工具函数 ──────────────────────────────────────────────────────────────

def _god_detail(chart_json: dict) -> list[dict]:
    """透干明细 [{god, stem}]（year/month/hour，排除 day 柱）。"""
    pillars = chart_json.get("pillars") or {}
    out = []
    for pname in ("year", "month", "hour"):
        p = pillars.get(pname) or {}
        tg, st = p.get("ten_god") or "", p.get("stem") or ""
        if tg and st:
            out.append({"god": tg, "stem": st})
    return out


def _has_yang_ren(chart_json: dict) -> bool:
    """阳刃在支。"""
    pillars = chart_json.get("pillars") or {}
    day_stem = (pillars.get("day") or {}).get("stem") or ""
    if not day_stem or STEM_YINYANG.get(day_stem) != "阳":
        return False
    elem = STEM_ELEMENTS.get(day_stem) or ""
    for k in ("year", "day", "hour"):
        b = (pillars.get(k) or {}).get("branch") or ""
        if b and twelve_growth(elem, b) == "帝旺":
            return True
    return False


def _role_of_elem(day_elem: str, other_elem: str) -> str:
    """五行 vs 日主五行 → 十神作用类。"""
    if not day_elem or not other_elem:
        return ""
    if other_elem == day_elem:
        return "比劫"
    if SHENG_CYCLE.get(other_elem) == day_elem:
        return "印"
    if SHENG_CYCLE.get(day_elem) == other_elem:
        return "食伤"
    if KE_CYCLE.get(other_elem) == day_elem:
        return "官杀"
    return "财"


def _role(ten_god: str) -> str:
    return TEN_GOD_GROUP.get(ten_god, "")


def _element_of_stem(stem: str) -> str:
    return STEM_ELEMENTS.get(stem, "")


def _ke_wo(elem: str) -> str:
    """克我者（官杀五行）。"""
    return next((k for k, v in KE_CYCLE.items() if v == elem), "")
