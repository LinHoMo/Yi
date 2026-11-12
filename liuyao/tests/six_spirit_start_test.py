# -*- coding: utf-8 -*-
"""六神起例逐格对账：日干 → 各爻所临之神，必须与《增删卜易》六神章第十八一致。

书证：`liuyao/data/sources/zengshan_buyi_dz.dz.txt` 源L711-717——六神章第十八，
表以六列排日干组（甲乙／丙丁／戊／己／庚辛／壬癸）、六行排爻位（书上排 上爻→初爻）。
本测试把书表逐格抄下（异体「腾蛇」「元武」按本仓写法归一为「螣蛇」「玄武」），
与 `chart_tables.DAY_STEM_SPIRIT_START` 推出的 60 格（10 干 × 6 爻）逐格比对。

为什么钉这一条：560 批曾据《周易尚占》源L36「日建六神例」（其表见源L341-346，戊己同起勾陈），
把本表「己」误改为勾陈起；561 批据《增删卜易》逐格对账证明**原表是对的**，异说另记。
本测试即该次误判的看门狗：谁再改这张表，先问自己与哪部书对得上。
"""
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from chart_tables import DAY_STEM_SPIRIT_START, SIX_SPIRITS  # noqa: E402

# 《增删卜易》源L712-717：行＝上爻→初爻，列＝甲乙/丙丁/戊/己/庚辛/壬癸
_BOOK_ROWS_UP_TO_LOW = [
    ["元武", "青龙", "朱雀", "勾陈", "滕蛇", "白虎"],
    ["白虎", "元武", "青龙", "朱雀", "勾陈", "滕蛇"],
    ["滕蛇", "白虎", "元武", "青龙", "朱雀", "勾陈"],
    ["勾陈", "滕蛇", "白虎", "元武", "青龙", "朱雀"],
    ["朱雀", "勾陈", "滕蛇", "白虎", "元武", "青龙"],
    ["青龙", "朱雀", "勾陈", "滕蛇", "白虎", "元武"],
]
_COL_GROUPS = ("甲乙", "丙丁", "戊", "己", "庚辛", "壬癸")
_ALIAS = {"腾蛇": "螣蛇", "滕蛇": "螣蛇", "元武": "玄武"}


def _norm(name: str) -> str:
    return _ALIAS.get(name, name)


def _book_table() -> dict[str, list[str]]:
    table: dict[str, list[str]] = {}
    for ci, group in enumerate(_COL_GROUPS):
        low_to_high = [_norm(_BOOK_ROWS_UP_TO_LOW[r][ci]) for r in range(5, -1, -1)]
        for stem in group:
            table[stem] = low_to_high
    return table


def test_six_spirit_start_matches_zengshan_table() -> None:
    book = _book_table()
    for stem, expected in book.items():
        start = DAY_STEM_SPIRIT_START[stem]
        rolled = [SIX_SPIRITS[(start + i) % len(SIX_SPIRITS)] for i in range(6)]
        assert rolled == expected, (
            f"{stem}日六神与《增删卜易》源L711-717 不合：{rolled} ≠ {expected}"
        )


def test_ji_is_its_own_group() -> None:
    """戊日初爻勾陈、己日初爻腾蛇——两书此处分列，勿并成一组。"""
    assert _norm(SIX_SPIRITS[DAY_STEM_SPIRIT_START["戊"]]) == "勾陈"
    assert _norm(SIX_SPIRITS[DAY_STEM_SPIRIT_START["己"]]) == "螣蛇"
