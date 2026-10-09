# -*- coding: utf-8 -*-
"""命科从格 kind「杀势当权」判据锁定（CHANGELOG 2026-10-02t）。

口径：任注从势者须「财官食伤**并旺**」势均；官杀「当令且透干」或「透干≥2」
即杀势当权，不成并旺 → kind=从官杀（书例 ZC011/012/014）；反例 ZC009
（辰令官**不透**）与 ZC010（官透仅 1 且不当令）不触发，仍判从势。
只验机械判定，不评命运（AGENTS.md 铁律一/三）。
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core"
MING_SCRIPTS = ROOT / "disciplines" / "ming" / "scripts"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))


def _load_ming(name: str):
    """唯一名加载命科脚本（conftest 让六爻 scripts 在前，裸 import 会撞名）。"""
    spec = importlib.util.spec_from_file_location(f"ming_{name}_cong_under_test",
                                                  MING_SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    before = list(sys.path)
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path[:] = before
    return mod


_chart = _load_ming("chart")
_pattern = _load_ming("pattern")
chart_from_pillars = _chart.chart_from_pillars
strength_and_pattern = _pattern.strength_and_pattern


def _judge(year, month, day, hour):
    c = chart_from_pillars({"year": year, "month": month,
                            "day": day, "hour": hour})
    sp = strength_and_pattern(c)
    return sp.get("from_kind"), sp.get("from_type")


def test_sha_dangling_and_tou():
    """ZC011 己土：卯月杀本气当令 + 月干乙杀透 → 从官杀（书「杀势当权」）。"""
    kind, _ = _judge("癸巳", "乙卯", "己亥", "癸酉")
    assert kind == "从官杀"


def test_sha_shuang_tou():
    """ZC012 丙火：月时双壬杀透（月令寅为印）→ 从官杀（书「杀势愈旺」）。"""
    kind, _ = _judge("丁丑", "壬寅", "丙申", "壬辰")
    assert kind == "从官杀"


def test_guan_dangling_but_not_tou_stays_cong_shi():
    """ZC009 癸水：辰月官本气当令但官不透 → 不触发，仍从势（反例受控）。"""
    kind, ftype = _judge("丙戌", "壬辰", "癸巳", "甲寅")
    assert (kind, ftype) == ("从势", "真从")
