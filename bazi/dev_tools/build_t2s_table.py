# -*- coding: utf-8 -*-
"""生成繁简字表 `dev_tools/t2s_table.json`（四库本繁体 → dz 本简体字形）。

    python dev_tools/build_t2s_table.py

**生成这一步需要 zhconv**（`pip install zhconv`）；**表入库后，校验与对拍全部零外部依赖**
（`diff_siku_sanming.py` / `scan_siku_gaps.py` 只读表，不调 zhconv）。

口径（第三百二十八批定稿，经历过一次反转，务必读完）：
  · 逐字取 zhconv 的 `zh-cn` 单字结果（如 乾→干、齋→斋、動→动）；
  · **不做「以 dz 本字集消歧」的保留**——那是 328 批中期的做法，实测**净损失**：
    dz 本是**词组转换**过的简体转录本，「乾坤」34 处保留「乾」、「天干」213 处用「干」；
    而单字表会把「乾坤」误转成「干坤」。实测四库本「乾」162 处、dz 本仅 49 处，
    若按消歧保留「乾」，则四库 113 处与 dz 的「干」对不上（净失 113），
    改成逐字转换则只错 34 处「乾坤」（净得 79）。**逐字表胜出。**

这张表只用于**对拍比对**，不用于底本本身：底本一字不改，字表不落进 `data/sources/`。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
SIKU = DISC / "data" / "sources" / "sanming_tonghui_siku.wikitext.txt"
T2S = HERE / "t2s_table.json"

try:
    import zhconv  # noqa: E402
except ImportError:
    raise SystemExit("需要 zhconv：pip install zhconv（表入库后日常校验/对拍不需要它）")


def main() -> int:
    raw = SIKU.read_text(encoding="utf-8")
    chars = sorted({c for c in raw if "\u4e00" <= c <= "\u9fff"})
    tbl = {}
    for c in chars:
        s = zhconv.convert(c, "zh-cn")
        if s != c:
            tbl[c] = s
    T2S.write_text(json.dumps(tbl, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    print(f"四库本用到的汉字 {len(chars)} 个；需转换字对 {len(tbl)} 条")
    print(f"写出 {T2S.relative_to(DISC)}")
    for c in ("乾", "齋", "動", "極", "著", "萬"):
        print(f"    {c} → {tbl.get(c, '（同形）')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
