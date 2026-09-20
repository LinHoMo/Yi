# -*- coding: utf-8 -*-
"""
文王卦序 — standard 64-hexagram King Wen ordering with sequence-based interpretation.
"""

KING_WEN_SEQUENCE = [
    1, 2, 41, 58, 51, 54, 32, 33, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
    17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 34, 35, 36, 37, 38, 39,
    40, 42, 43, 44, 45, 46, 47, 48, 49, 50, 52, 53, 55, 56, 57, 59, 60, 61, 62, 63, 64,
]

# 序数分组（上经/下经）
UPPER_CANON = list(range(1, 31))   # 前30卦: 上经(乾至离)
LOWER_CANON = list(range(31, 65))  # 后34卦: 下经(咸至未济)

# 八卦类象 — 用于文王序解读
TRIGRAM_SYMBOLISM = {
    "乾": {"nature": "天", "trait": "刚健", "phase": "创始"},
    "坤": {"nature": "地", "trait": "柔顺", "phase": "承载"},
    "震": {"nature": "雷", "trait": "动", "phase": "激发"},
    "巽": {"nature": "风", "trait": "入", "phase": "渗透"},
    "坎": {"nature": "水", "trait": "陷", "phase": "险难"},
    "离": {"nature": "火", "trait": "丽", "phase": "光明"},
    "艮": {"nature": "山", "trait": "止", "phase": "静止"},
    "兑": {"nature": "泽", "trait": "悦", "phase": "沟通"},
}

# 文王序位置 → 人生阶段映射
LIFE_PHASES = {
    (1, 5): "潜龙勿动 — 韬光养晦，积累实力",
    (6, 10): "见龙在田 — 初露头角，小试牛刀",
    (11, 15): "终日乾乾 — 勤勉谨慎，渐入佳境",
    (16, 20): "或跃在渊 — 审时度势，把握契机",
    (21, 25): "飞龙在天 — 大展宏图，顺势而为",
    (26, 30): "亢龙有悔 — 盛极将衰，当思进退",
    (31, 35): "咸临感应 — 情感萌动，人际关系",
    (36, 40): "明夷艰贞 — 前途晦险，守正待时",
    (41, 45): "损益盈虚 — 取舍权衡，修德补过",
    (46, 50): "升萃聚集 — 人气汇聚，顺势而上",
    (51, 55): "震荡变革 — 雷厉风行，破旧立新",
    (56, 60): "守节安居 — 动静有度，持盈保泰",
    (61, 64): "中孚诚信 — 内诚外信，终始循环",
}


def sequence_number(hexagram_name: str, all_hexagrams: list) -> int:
    """Find the King Wen sequence number for a hexagram.

    Parameters
    ----------
    hexagram_name : str
        卦名 (e.g. "乾", "屯").
    all_hexagrams : list[dict]
        List of hexagram dicts (from liuyao_engine HEXAGRAMS structure),
        each with keys ``"name"`` and ``"sequence"``.
        ``"sequence"`` is the 1-based position in the original HEXAGRAMS list
        (NOT the King Wen order).  This function looks it up there.

    Returns
    -------
    int
        The position (1-64) in the King Wen sequence, or 0 if not found.
    """
    # First try direct "sequence" attribute match
    for h in all_hexagrams:
        if h["name"] == hexagram_name:
            return h.get("sequence", 0)
    return 0


def _build_kw_name_to_pos() -> dict:
    """Build mapping from original-engine sequence number → King Wen position."""
    kw_pos = {}
    for pos, orig_seq in enumerate(KING_WEN_SEQUENCE, start=1):
        kw_pos[orig_seq] = pos
    return kw_pos


_KW_POS_MAP = _build_kw_name_to_pos()


def king_wen_position(original_sequence: int) -> int:
    """Given the original-engine sequence number (1-64 as in HEXAGRAMS),
    return the position within the King Wen sequence (1-64)."""
    return _KW_POS_MAP.get(original_sequence, 0)


def sequence_symbolism(seq_num: int) -> str:
    """Return the sequence-based meaning of this hexagram's position."""
    if seq_num in (1, 2):
        return "开天辟地 — 万始之端，创始艰难但必有大成"
    elif seq_num in (63, 64):
        return "既济未济 — 终而复始，事无尽时"
    elif seq_num <= 30:
        return f"上经第序 — 先天气运，大局所系"
    else:
        return f"下经第序 — 人事修为，可为可守"


def life_phase(seq_num: int) -> str:
    """Return the life/career phase corresponding to the King Wen position."""
    for (lo, hi), desc in LIFE_PHASES.items():
        if lo <= seq_num <= hi:
            return desc
    return "循环轮转 — 周而复始，无始无终"


def canon(seq_num: int) -> str:
    """Return whether the position is in the upper (天道) or lower (人道) canon."""
    if 1 <= seq_num <= 30:
        return "上经 — 天道"
    else:
        return "下经 — 人道"


def king_wen_interpretation(original_sequence: int) -> dict:
    """Produce a full King Wen sequence interpretation for a hexagram.

    Parameters
    ----------
    original_sequence : int
        The 1-based position in the engine's HEXAGRAMS list.

    Returns
    -------
    dict
        ``king_wen_pos``, ``canon``, ``symbolism``, ``life_phase``
    """
    kw_pos = king_wen_position(original_sequence)
    return {
        "king_wen_pos": kw_pos,
        "canon": canon(kw_pos),
        "symbolism": sequence_symbolism(kw_pos),
        "life_phase": life_phase(kw_pos),
    }
