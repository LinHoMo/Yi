# -*- coding: utf-8 -*-
"""年上起月歌／日上起时歌 → 引擎五虎遁、五鼠遁对账（八字科）。

563 批立。依据《卜筮全书》「年上起月歌」与「日上起时歌」（该底本收在**六爻科**书源目录，
行号与逐字引文见六爻科判据《interpretation_guide》第十二节；本文件只引歌文、不引行号，
以免形成跨科书证指针）。

歌文要点：
  年上起月歌——甲己之年丙作首，乙庚之岁戊为头，丙辛之位从庚上，丁壬壬位顺行流，
                更加戊癸从何起，甲寅之上好追求；
  日上起时歌——甲己还加甲，乙庚丙作初，丙辛从戊起，丁壬庚子居，戊癸何方发，壬子是真途。

引擎两表（`yishu_core.ganzhi_calendar`）与歌文逐组一致，此测试把该一致性钉住。

**为什么是 main() 式而不是原生 pytest**：根 `pyproject.toml` 的 `pythonpath` 同时含两科的
`core`，同名的 `yishu_core` 包只会被先到的那一科解析——原生 pytest 跑本文件会取到六爻副本，
命科的两张表就取不到。故按本仓惯例写成 main() 式，由根 `bridge_test.py` 以**独立子进程**
（cwd＝本科目录、sys.path 不含别科）运行，杜绝跨科串包。
"""
from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
if str(HERE.parent / "core") not in sys.path:
    sys.path.insert(0, str(HERE.parent / "core"))

from yishu_core.ganzhi_calendar import RAT_HOUR_STEM, TIGER_MONTH_STEM  # noqa: E402

STEMS = "甲乙丙丁戊己庚辛壬癸"
# 年上起月歌：甲己→丙、乙庚→戊、丙辛→庚、丁壬→壬、戊癸→甲（正月干支）
TIGER_FROM_SONG = {
    "甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚",
    "辛": "庚", "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲",
}
# 日上起时歌：甲己→甲、乙庚→丙、丙辛→戊、丁壬→庚、戊癸→壬（子时干支）
RAT_FROM_SONG = {
    "甲": "甲", "己": "甲", "乙": "丙", "庚": "丙", "丙": "戊",
    "辛": "戊", "丁": "庚", "壬": "庚", "戊": "壬", "癸": "壬",
}


def main() -> int:
    errs: list[str] = []
    for year_stem, first_month_stem in TIGER_FROM_SONG.items():
        got = STEMS[TIGER_MONTH_STEM[year_stem]]
        if got != first_month_stem:
            errs.append(f"{year_stem}年正月月干 {got} ≠ 歌文 {first_month_stem}")
    for day_stem, zi_hour_stem in RAT_FROM_SONG.items():
        got = STEMS[RAT_HOUR_STEM[day_stem]]
        if got != zi_hour_stem:
            errs.append(f"{day_stem}日子时时干 {got} ≠ 歌文 {zi_hour_stem}")
    if errs:
        for e in errs:
            print("× " + e)
        print(f"ganzhi_song_test: {len(errs)} 项不合")
        return 1
    print("√ 干支歌诀对账：五虎遁、五鼠遁各五组，与《卜筮全书》年上起月歌／日上起时歌逐组一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
