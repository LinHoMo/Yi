# -*- coding: utf-8 -*-
"""紫微斗数因子推演（analyze 段）—— 机械格局/四化/大限，不写命运断语。

推演规则（全部机械可执行，lookup 表）：
  - 命宫主星 → 格局（PATTERNS 表 lookup）
  - 四化入宫 → 吉凶方向（SIHUA_DIRECTION + 宫位）
  - 大限 → 起运年龄 = 局数，每十年一宫，阳男阴女顺行 / 阴男阳女逆行
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(CORE), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.ziwei_tables import (  # noqa: E402
    PATTERNS,
    SIHUA_DIRECTION,
    PALACES,
    HEAVENLY_STEMS,
    dayun_start_age,
    dayun_step_years,
)

_VERDICTS_CACHE: dict | None = None


def _load_verdicts() -> dict:
    """读 data/verdicts.json（结论措辞唯一真值源）；缓存避免每局重读。"""
    global _VERDICTS_CACHE
    if _VERDICTS_CACHE is None:
        with open(Path(__file__).resolve().parent.parent / "data" / "verdicts.json",
                  encoding="utf-8") as fh:
            _VERDICTS_CACHE = json.load(fh)
    return _VERDICTS_CACHE


def _stem_yinyang(stem: str) -> str:
    """天干阴阳：甲丙戊庚壬 = 阳，乙丁己辛癸 = 阴。"""
    yang = "甲丙戊庚壬"
    return "阳" if stem in yang else "阴"


def identify_pattern(ming_stars: list[str]) -> tuple[str, str]:
    """命宫主星 → 格局名（lookup）。

    匹配优先级：两颗同宫组合 > 单星名称 > '命宫无主星'。
    返回 (格局名, basis 说明)。
    """
    if not ming_stars:
        return "命宫无主星", "命宫无主星，借对宫星曜"
    # 尝试两两组合
    for i in range(len(ming_stars)):
        for j in range(i + 1, len(ming_stars)):
            combo = ming_stars[i] + ming_stars[j]
            if combo in PATTERNS:
                return PATTERNS[combo], f"命宫主星 {ming_stars[i]}、{ming_stars[j]}"
    # 单星
    for s in ming_stars:
        if s in PATTERNS:
            return PATTERNS[s], f"命宫主星 {s}"
    return "未入榜格局", f"命宫主星 {'、'.join(ming_stars)}"


def sihua_impact(sihua_list: list[dict]) -> list[str]:
    """四化星 → 影响标签列表（机械：星+四化+入宫 → 描述）。"""
    impacts = []
    for item in sihua_list:
        dtype = item.get("type", "")
        star = item.get("star", "")
        palace = item.get("palace", "?")
        direction = item.get("direction", "平")
        if dtype and star and palace:
            impacts.append(f"{direction}：{star}{dtype}入{palace}")
    return impacts


def dayun_table(
    ju: int, ming_gong_idx: int, gender: str, birth_stem: str,
    year_stem: str,
) -> list[dict]:
    """大限排法（机械）。

    起运年龄 = 五行局。
    阳男阴女顺行，阴男阳女逆行。
    顺行 = 从命宫起 +1 +1...；逆行 = 从命宫起 -1 -1...
    """
    start = dayun_start_age(ju)
    step = dayun_step_years()
    male = gender == "男"
    stem_yy = _stem_yinyang(year_stem)
    forward = (male and stem_yy == "阳") or (not male and stem_yy == "阴")

    table = []
    for i in range(12):
        age_start = start + i * step
        age_end = age_start + step - 1
        if forward:
            palace_off = (ming_gong_idx + i) % 12
        else:
            palace_off = (ming_gong_idx - i) % 12
        table.append({
            "step": i + 1,
            "start_age": age_start,
            "end_age": age_end,
            "palace_idx": palace_off,
            "direction": "顺行" if forward else "逆行",
        })
    return table


def ziwei_analyze(chart_json: dict) -> dict:
    """chart JSON → analyze JSON。产出机械标签，不产出命运吉凶。"""
    result = dict(chart_json)
    palaces = chart_json.get("palaces", {})
    sihua_list = chart_json.get("sihua_list", [])
    pillars = chart_json.get("pillars", {})
    ming_gong = chart_json.get("ming_gong", {})
    ju = chart_json.get("wuxing_ju", 5)
    birth = chart_json.get("birth", {})
    gender = birth.get("gender")
    year_stem = (pillars.get("year") or "")[0:1] if pillars.get("year") else ""
    day_stem = (pillars.get("day") or "")[0:1] if pillars.get("day") else ""

    # 命宫主星
    mg_data = palaces.get("命宫", {})
    mg_stars = mg_data.get("main_stars", [])

    # 格局
    pattern, pattern_basis = identify_pattern(mg_stars)

    # 四化影响
    si_impact = sihua_impact(sihua_list)

    # 方向判定：只要有一化忌入命宫/迁移/官禄/财帛 → 有凶信号；全部禄权科且无凶 → 吉
    # 默认平，只有"命宫或三方四正有忌入"判有凶信号
    has_ji_in_critical = False
    has_lu_in_critical = False
    critical_palaces = {"命宫", "迁移", "官禄", "财帛"}
    for item in sihua_list:
        if item.get("type") == "忌" and item.get("palace") in critical_palaces:
            has_ji_in_critical = True
        if item.get("type") == "禄" and item.get("palace") in critical_palaces:
            has_lu_in_critical = True
    # 结论措辞唯一真值源在 data/verdicts.json#方向说明，此处只做查表
    direction_note = _load_verdicts()["方向说明"]
    if has_ji_in_critical:
        direction = direction_note["忌入三方四正"]
    elif has_lu_in_critical:
        direction = direction_note["禄入三方四正"]
    else:
        direction = "平"

    # 大限
    mg_idx = ming_gong.get("palace_idx", -1)
    dy_table = []
    if mg_idx >= 0:
        # 阳男阴女顺行
        dy_table = dayun_table(
            ju, mg_idx, gender or "男", day_stem, year_stem,
        )

    # 推论总结
    mg_stars_str = "、".join(mg_stars) if mg_stars else "无主星"

    summary = {
        "命宫主星": mg_stars_str,
        "格局": pattern,
        "格局依据": pattern_basis,
        "五行局": chart_json.get("ju_name", ""),
        "命宫地支": mg_data.get("branch", ""),
        "紫微所在": f"{chart_json.get('ziwei', {}).get('branch', '')}宫",
        "天府所在": f"{chart_json.get('tianfu', {}).get('branch', '')}宫",
        "四化": chart_json.get("sihua", {}),
        "四化影响": si_impact,
        "大限位序": f"{'顺行' if dy_table and dy_table[0]['direction']=='顺行' else '逆行'}（{'阳男阴女顺' if dy_table and dy_table[0]['direction']=='顺行' else '阴男阳女逆'}）",
    }

    return {
        **result,
        "chart_summary": summary,
        "conclusion": {
            "命宫主星": mg_stars_str,
            "格局": pattern,
            "格局依据": pattern_basis,
            "四化影响": si_impact,
            "方向": direction,
            "说明": (
                f"机械推演：命宫在{mg_data.get('branch', '')}，主星{mg_stars_str}，{pattern}。"
                f"四化：{'；'.join(si_impact) if si_impact else '无四化入三方'}。"
                "不含命运吉凶断言。"
            ),
            "所本": (
                "格局 lookup table（core.ziwei_tables.PATTERNS）+ "
                "四化表（SIHUA_TABLE）+ 大限起法（dayun_start_age=局数，阳男阴女顺行）"
            ),
            "timing": [],
            "dayun": dy_table,
        },
    }


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="紫微斗数因子推演（analyze 段）")
    ap.add_argument("chart_json", nargs="?", help="chart 段输出")
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args()

    if args.chart_json:
        data = json.loads(Path(args.chart_json).read_text(encoding="utf-8"))
    else:
        from chart import chart as _chart

        data = _chart(datetime_str="1990-05-20 10:30", gender="男")

    out = ziwei_analyze(data)
    text = json.dumps(out, ensure_ascii=False, indent=2, default=str)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
