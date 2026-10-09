# -*- coding: utf-8 -*-
"""女命夫子星机械标注断言（AGENTS.md 铁律三：只标所在，不批吉凶）。

口径：女命依《渊海子平·女命论》以官杀为夫星、食伤为子星；本测试只验「扫描四柱
天干与地支藏干十神、归类夫/子星、绑定 core.relations 单源」是否正确，不评旺衰吉凶。
男命不调用（analyze 顶层无 female_fu_zi）。
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
    """按**唯一模块名**从路径加载命科脚本，避免各科同名模块互相遮蔽。

    八科 `scripts/` 同名（每科都有 chart/analyze），conftest 又有意让六爻
    `scripts/` 排在 `sys.path` 前列（test_yingqi_windows 依赖）。裸
    `from analyze import ...` 会拿到六爻的 analyze（或被先收集测试缓存进
    `sys.modules` 的那份）。故此处照 `test_ziwei_patterns.py` 的惯例：
    ① `spec_from_file_location` 给唯一名（不进 `sys.modules['analyze']`）；
    ② 加载后还原 `sys.path`，不污染根 pytest 对同名模块的解析。
    """
    spec = importlib.util.spec_from_file_location(f"ming_{name}_under_test",
                                                  MING_SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    before = list(sys.path)
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path[:] = before
    return mod


_chart_mod = _load_ming("chart")
_analyze_mod = _load_ming("analyze")
chart = _chart_mod.chart
analyze = _analyze_mod.analyze
female_fu_zi = _analyze_mod.female_fu_zi


def test_female_fu_zi_scans_gan_and_hidden():
    """女命：扫描天干与藏干十神，夫星限于官杀、子星限于食伤；绑定 core 单源。"""
    c = chart("weak_zhengguan", datetime_str="1984-12-08 08:00", gender="女")
    a = analyze(c)
    ffz = a["female_fu_zi"]
    assert ffz["gender"] == "女"
    assert {h["十神"] for h in ffz["夫星"]} <= {"正官", "七杀"}
    assert {h["十神"] for h in ffz["子星"]} <= {"食神", "伤官"}
    # 此造夫星（时干七杀+多柱藏干正官）、子星（时支藏干食神）均应命中
    assert ffz["夫星"] and ffz["子星"]
    # 出处诚实《渊海子平》
    assert "渊海子平" in ffz["basis"]
    # verdict 已挂到 conclusion
    assert any(v["code"] == "female_fu_zi" for v in a["conclusion"]["verdicts"])


def test_female_fu_zi_absent_for_male():
    """男命不调用：analyze 顶层无 female_fu_zi，helper 返回 None。"""
    c = chart("weak_shangguan", datetime_str="1990-05-20 10:30", gender="男")
    a = analyze(c)
    assert a.get("female_fu_zi") is None
    assert female_fu_zi(c) is None
