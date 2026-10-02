# -*- coding: utf-8 -*-
"""女命夫子星机械标注断言（AGENTS.md 铁律三：只标所在，不批吉凶）。

口径：女命依《渊海子平·女命论》以官杀为夫星、食伤为子星；本测试只验「扫描四柱
天干与地支藏干十神、归类夫/子星、绑定 core.relations 单源」是否正确，不评旺衰吉凶。
男命不调用（analyze 顶层无 female_fu_zi）。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "core", ROOT / "disciplines" / "ming" / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from chart import chart  # noqa: E402
from analyze import analyze, female_fu_zi  # noqa: E402


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
