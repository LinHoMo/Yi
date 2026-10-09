# -*- coding: utf-8 -*-
"""六爻用神入墓四类（日墓 / 月墓 / 动墓 / 化墓）结构判据。

出处：《增刪卜易·隨鬼入墓章第三十》「古有日墓、動墓、化墓之三墓」；〈入墓難克〉
「且如木爲用神，金爲忌神，若在丑日占者，金入墓矣……卦中動出墓爻，亦向此推。
金爻動而化丑亦是。」判据唯一实现在 `classical_enhancements.use_god_tomb_tags`，
`case_runner`（引擎侧）与 `dev_tools/build_extra_dimensions`（基准侧）同源调用，
禁止各写一份。

书源用例取自同书原本占例（`data/sources/zengshan_buyi.wikitext.txt` 行 700–709、722–731）：
  ① 戌月甲寅日占会试，小过之艮——「世爻隨官入三墓，動墓，化墓」；
  ② 未月戊辰日占重罪赦免，蛊之损——「世爻隨鬼入動墓，又動而化墓」。
两例的动墓/化墓是书里自己点名的，故可作真检验，非对表自洽。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import case_runner
from classical_enhancements import use_god_tomb_tags

CASES = (Path(__file__).resolve().parents[1] / "disciplines" / "liuyao"
         / "data" / "cases" / "classical_cases.json")


def _run(cid: str) -> dict:
    store = json.loads(CASES.read_text(encoding="utf-8"))
    case = next(c for c in store["cases"] if c["id"] == cid)
    return case_runner.run_case(case)


def _yao(pos: int, branch: str, moving: bool = False, changed: str | None = None) -> dict:
    return {"position": pos, "earthly_branch": branch,
            "is_moving": moving, "changed_branch": changed}


# ── 书源真例：动墓 / 化墓 ────────────────────────────────────────────────────

def test_smallguo_three_tombs():
    """小过之艮：世爻午火，火墓在戌 —— 戌月月墓 + 上爻戌动墓 + 世动化戌化墓。"""
    assert _run("SG001")["extra"]["use_god_muku"] == "入月墓、动墓、化墓"


def test_gu_sun_two_tombs():
    """蛊之损：世爻酉金，金墓在丑 —— 初爻丑动墓 + 世动化丑化墓。"""
    assert _run("SG002")["extra"]["use_god_muku"] == "动墓、化墓"


def test_day_tomb_anchored_case():
    """屯之震：申金父母入日丑墓（《黄金策》引例 ZS008 酉月己丑日）。"""
    assert _run("ZS008")["extra"]["use_god_muku"] == "入日墓"


# ── 判据单元：四类各自命中、以及两条排除项 ──────────────────────────────────

@pytest.mark.parametrize("branch,day,month,expect", [
    ("寅", "未", "子", "入日墓"),      # 木墓未，日建未
    ("寅", "子", "未", "入月墓"),      # 木墓未，月建未
    ("午", "寅", "子", "不入墓"),      # 火墓戌，日月皆非戌
])
def test_day_month_tomb(branch, day, month, expect):
    got = use_god_tomb_tags([_yao(1, branch)], branch, 1, day, month)
    assert got["label"] == expect


def test_moving_line_tomb():
    """他爻发动而值用神墓支 → 动墓（火用神午，三爻戌动）。"""
    lines = [_yao(1, "午"), _yao(3, "戌", moving=True, changed="申")]
    assert use_god_tomb_tags(lines, "午", 1, "寅", "子")["label"] == "动墓"


def test_changed_branch_tomb():
    """用神发动而化出墓支 → 化墓（火用神午动化戌）。"""
    lines = [_yao(1, "午", moving=True, changed="戌")]
    assert use_god_tomb_tags(lines, "午", 1, "寅", "子")["label"] == "化墓"


def test_self_tomb_line_not_moving_tomb():
    """动爻即用神本爻且值自身墓支 —— 属自坐墓，不得记动墓。"""
    lines = [_yao(3, "辰", moving=True, changed="巳")]   # 土墓辰，用神即三爻辰
    assert use_god_tomb_tags(lines, "辰", 3, "寅", "亥")["label"] == "不入墓"


def test_changed_same_branch_not_huamu():
    """化出本支属伏吟，不得记化墓（土用神辰动化辰）。"""
    lines = [_yao(3, "辰", moving=True, changed="辰")]
    assert use_god_tomb_tags(lines, "辰", 3, "寅", "亥")["label"] == "不入墓"


def test_missing_branch_is_noop():
    assert use_god_tomb_tags([_yao(1, "午")], "", None, "寅", "子")["label"] == "不入墓"
