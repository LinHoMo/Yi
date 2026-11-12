# -*- coding: utf-8 -*-
"""古籍歌诀 → 引擎逐项对账（六爻科）：把《卜筮全书》《增删卜易》的歌诀变成机器可验的断言。

563 批立。本文件把四组古籍结构知识固化成回归测试：
  ① 「无某六亲」各卦歌诀（《卜筮全书》源L651-655，非逐字：类目标目）→ 引擎按纳甲实算的缺六亲卦集；
  ② 游魂／归魂八卦歌（源L667／源L672，非逐字：类目标目）→ 引擎八宫序里的游魂／归魂标记；
  ③ 六神起例歌诀（源L627，另见《增删卜易》六神章第十八，非逐字：类目标目）→ 引擎日干起六神表；
  ④ 缺六亲歌诀的**已知一处差异**（见下），如实钉住，不静默放过。

**为什么要固化成测试**：这些歌诀是"机械可验"的——歌诀列的卦集若与引擎算出的不一致，
要么是引擎错了，要么是底本讹字；无论哪种，都该立刻见红而不是等人翻书。
"""
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from chart_tables import DAY_STEM_SPIRIT_START, SIX_SPIRITS  # noqa: E402
from engine_chart import determine_six_relations, get_palace_element, get_palace_info  # noqa: E402
from yishu_core.najia import najia_branch  # noqa: E402
from yishu_core.symbols import EIGHT_PALACES, HEXAGRAM_TRIGRAMS  # noqa: E402

# ── ① 《卜筮全书》源L651-655「无某六亲」歌诀（原书名单）
# 「孚」即中孚、「二过」即大过（底本字形），「儿」为讹字——见 KNOWN_DIFF 说明。
BOOK_NO_SIX_RELATION = {
    "父母": "泰 复 夬 需 旅 鼎 解 大畜 豫 贲",
    "兄弟": "观 剥 恒 升 井 大过",
    "妻财": "遁 履 姤 中孚 渐 谦 涣 屯 睽 既济 革 明夷 小过 咸 蒙 蹇",
    "子孙": "大过 否 蛊 颐 随 大畜 贲 观 中孚 井 遁 升 归妹 晋 损",
    "官鬼": "小畜 未济 家人 旅 讼 涣 益 颐",
}
# 563 批实测：歌诀「无子孙」十六卦里未列「小过」，而引擎按纳甲算得小过亦无子孙；
# 书末另有一讹字「儿」。此处如实记为**唯一一处差异**，不判引擎错、不改歌诀，只钉住。
KNOWN_DIFF_NO_SUNSUN = {"小过"}

# ── ② 《卜筮全书》源L667、源L672 游魂／归魂歌（非逐字：类目标目）
BOOK_YOUHUN = "明夷 颐 晋 需 讼 中孚 小过 大过"
BOOK_GUIHUN = "归妹 同人 师 随 蛊 渐 比 大有"

# ── ③ 六神起例：《增删卜易》源L711-717 六列六行（行＝上爻→初爻）×《卜筮全书》源L627 歌诀
#     书用异体「腾蛇」「元武」，本仓统一「螣蛇」「玄武」。
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
# 《卜筮全书》源L627「甲乙起青龙，丙丁起朱雀，戊日起勾陈，己日起螣（1）蛇，庚辛起白虎，壬癸起玄武。」
# ——与《增删卜易》六神章**独立互证**（第二书证），亦与下表同。
# （底本「螣（1）蛇」中的「（1）」为原书脚注号，断言时按「螣蛇」取。）
_QIQSHU_SONG_STARTS = {"甲": "青龙", "乙": "青龙", "丙": "朱雀", "丁": "朱雀", "戊": "勾陈",
                       "己": "螣蛇", "庚": "白虎", "辛": "白虎", "壬": "玄武", "癸": "玄武"}
# 书证逐字（含脚注号）：《卜筮全书》源L627「甲乙起青龙，丙丁起朱雀，戊日起勾陈，己日起螣（1）蛇，庚辛起白虎，壬癸起玄武。」


def _norm(name: str) -> str:
    return _ALIAS.get(name, name)


def _engine_missing_six_relation() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {r: set() for r in BOOK_NO_SIX_RELATION}
    for name in HEXAGRAM_TRIGRAMS:
        palace, _ = get_palace_info(name)
        element = get_palace_element(palace)
        rels = {determine_six_relations(najia_branch(name, pos), element) for pos in range(1, 7)}
        for rel in out:
            if rel not in rels:
                out[rel].add(name)
    return out


def test_missing_six_relation_sets_match_book_song() -> None:
    """歌诀列出的卦，引擎必须同样「无该六亲」；引擎多出的只允许已知差异。"""
    engine = _engine_missing_six_relation()
    for rel, song in BOOK_NO_SIX_RELATION.items():
        book = set(song.split())
        extra = engine[rel] - book - KNOWN_DIFF_NO_SUNSUN
        assert not extra, f"引擎多出无{rel}之卦（歌诀未列）：{sorted(extra)}"
        missing = book - engine[rel]
        assert not missing, f"歌诀称无{rel}而引擎实有：{sorted(missing)}"


def test_known_diff_is_exactly_one_hexagram() -> None:
    """已知差异必须**恰好**是「小过」一处——差异扩大或消失都要见红。"""
    engine = _engine_missing_six_relation()
    book = set(BOOK_NO_SIX_RELATION["子孙"].split())
    assert engine["子孙"] - book == KNOWN_DIFF_NO_SUNSUN


def test_youhun_guihun_match_book_song() -> None:
    engine_you, engine_gui = set(), set()
    for _palace, info in EIGHT_PALACES.items():
        for name, tag in info["order"]:
            if "游魂" in tag:
                engine_you.add(name)
            elif "归魂" in tag:
                engine_gui.add(name)
    assert engine_you == set(BOOK_YOUHUN.split()), f"游魂卦集与歌诀不合：{sorted(engine_you)}"
    assert engine_gui == set(BOOK_GUIHUN.split()), f"归魂卦集与歌诀不合：{sorted(engine_gui)}"


def test_six_spirit_start_matches_zengshan_table() -> None:
    for ci, group in enumerate(_COL_GROUPS):
        low_to_high = [_norm(_BOOK_ROWS_UP_TO_LOW[r][ci]) for r in range(5, -1, -1)]
        for stem in group:
            start = DAY_STEM_SPIRIT_START[stem]
            rolled = [SIX_SPIRITS[(start + i) % len(SIX_SPIRITS)] for i in range(6)]
            assert rolled == low_to_high, f"{stem}日六神与《增删卜易》源L711-717 不合"


def test_six_spirit_start_matches_bushi_quanshu_song() -> None:
    """《卜筮全书》起六神歌（第二书证，逐字见本文件上方）逐干核对初爻所临之神。"""
    for stem, spirit in _QIQSHU_SONG_STARTS.items():
        start = DAY_STEM_SPIRIT_START[stem]
        assert SIX_SPIRITS[start] == _norm(spirit), (
            f"{stem}日初爻六神与《卜筮全书》起六神歌（源L627，非逐字：错误信息不引底本）不合：{SIX_SPIRITS[start]} ≠ {spirit}"
        )
