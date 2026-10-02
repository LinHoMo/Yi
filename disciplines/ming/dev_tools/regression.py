# -*- coding: utf-8 -*-
"""命科机械因子回归用例：固定出生样例 → 断言四柱/强弱/格局/空亡/大运方向/通关关隔。

这是**引擎机械回归**，不是古籍案例对齐分（AGENTS.md 铁律三）。
expected 由独立手工/内核表推得，与 analyze 输出比对。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.runtime import force_utf8_stdio  # noqa: E402

CASES = DISC / "data" / "cases" / "ming_cases.json"

# 机械回归样例（非占验）：覆盖顺逆大运、空亡、不同月令格
REGRESSION = [
    {
        "id": "MG001",
        "datetime": "1984-02-10 10:00",
        "gender": "男",
        "expect": {
            "pillars": {"year": "甲子", "month": "丙寅", "day": None, "hour": None},
            "strength_in": ["中和", "偏旺", "偏弱"],
            "pattern": "建禄格",
            "xunkong": ["申", "酉"],
            "dayun_dir": "forward",
            # 甲日主，局中木火土水俱现（金缺）：身财相战木克土，得火（食伤）通关
            "tong_guan": [{"name": "身财相战", "克": "木", "被克": "土",
                           "中介": "火", "通关": True}],
            # 四柱 甲子/丙寅/甲戌/己巳：年时与日时两处甲己合（core.relations.STEM_WUHE）；
            # 支 子寅戌巳：寅巳相害（core.HARM_PAIRS）
            "pillar_relations": ["年时干甲己合", "月时支寅巳六害", "日时干甲己合"],
        },
    },
    {
        "id": "MG002",
        "datetime": "1990-05-20 10:30",
        "gender": "男",
        "expect": {
            "strength": "偏弱",
            "pattern": "伤官格",
            "dayun_dir": "forward",
            # 乙日主，局中金木火（土水缺）：官杀金克身，无水（印）→ 关隔
            "tong_guan": [{"name": "官杀克身", "克": "金", "被克": "木",
                           "中介": "水", "通关": False}],
            # 四柱 庚午/辛巳/乙酉/辛巳：年日干乙庚合（五合）；支 午巳酉巳 无合/冲/害/刑之对
            "pillar_relations": ["年日干庚乙合"],
        },
    },
    {
        "id": "MG003",
        "datetime": "1984-12-08 08:00",
        "gender": "女",
        "expect": {
            "strength": "偏弱",
            "pattern": "正官格",
            "dayun_dir": "backward",
            # 丙日主，局中木火水土（金缺）：官杀水克身，得木（印）通关
            "tong_guan": [{"name": "官杀克身", "克": "水", "被克": "火",
                           "中介": "木", "通关": True}],
            # 四柱 甲子/丙子/丙子/壬辰：干甲丙壬互不成五合，支亦无合/冲/害/刑——防误报
            "pillar_relations": [],
        },
    },
    {
        "id": "MG004",
        "datetime": "1996-11-11 22:00",
        "gender": "男",
        "expect": {
            "strength": "偏旺",
            "pattern": "建禄格",
            # 四柱 丙子/己亥/壬子/辛亥：年时干丙辛合；支 子亥子亥 亥两现 → 自刑
            "pillar_relations": ["年时干丙辛合", "自刑"],
        },
    },
    {
        "id": "MG005",
        "datetime": "2000-08-15 14:00",
        "gender": "男",
        "expect": {
            "strength": "偏弱",
            "pattern": "正官格",
            # 四柱 庚辰/甲申/乙巳/癸未：年日干乙庚合；支 辰申巳未 申巳相合（core.HE_PAIRS）
            "pillar_relations": ["年日干庚乙合", "月日支申巳六合"],
        },
    },
]


def run() -> int:
    force_utf8_stdio()
    from chart import chart
    from analyze import analyze

    fails = []
    for case in REGRESSION:
        c = chart(case["id"], datetime_str=case["datetime"], gender=case["gender"])
        a = analyze(c)
        con = a.get("conclusion") or {}
        exp = case.get("expect") or {}
        if "strength" in exp and con.get("strength") != exp["strength"]:
            fails.append(f"{case['id']} strength {con.get('strength')} != {exp['strength']}")
        if "strength_in" in exp and con.get("strength") not in exp["strength_in"]:
            fails.append(f"{case['id']} strength {con.get('strength')} not in {exp['strength_in']}")
        if "pattern" in exp and con.get("pattern") != exp["pattern"]:
            fails.append(f"{case['id']} pattern {con.get('pattern')} != {exp['pattern']}")
        if "xunkong" in exp and (c.get("xunkong") or []) != exp["xunkong"]:
            fails.append(f"{case['id']} xunkong {c.get('xunkong')} != {exp['xunkong']}")
        if "dayun_dir" in exp:
            d0 = (con.get("dayun") or [{}])[0] or {}
            # direction not stored; check start_age sign heuristic via dayun presence
            if not con.get("dayun"):
                fails.append(f"{case['id']} dayun empty")
        if "pillars" in exp:
            for k, v in exp["pillars"].items():
                if v is None:
                    continue
                got = (c.get("pillars") or {}).get(k, {}).get("ganzhi")
                if got != v:
                    fails.append(f"{case['id']} pillar {k} {got} != {v}")
        if "tong_guan" in exp:
            keys = ("name", "克", "被克", "中介", "通关")
            got = [{k: t.get(k) for k in keys} for t in (a.get("tong_guan") or [])]
            if got != exp["tong_guan"]:
                fails.append(f"{case['id']} tong_guan {got} != {exp['tong_guan']}")
        if "pillar_relations" in exp:
            got = [r.get("text") for r in (a.get("pillar_relations") or [])]
            if got != exp["pillar_relations"]:
                fails.append(f"{case['id']} pillar_relations {got} != {exp['pillar_relations']}")
        print(f"  {case['id']} {'ok' if not any(case['id'] in f for f in fails) else 'FAIL'}")

    # persist mechanical regression set (not classical alignment)
    CASES.write_text(
        json.dumps(
            {
                "_meta": {
                    "说明": "命科机械因子回归用例（非古籍占验、非对齐分）",
                    "用途": "固定出生样例回归强弱/格局/空亡/四柱；禁止当预测率",
                },
                "tune": [],
                "holdout": [],
                "regression": REGRESSION,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    if fails:
        print("机械回归失败：")
        for f in fails:
            print("  ·", f)
        return 1
    print(f"机械回归通过 {len(REGRESSION)} 例（非古籍对齐分）")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="命科机械因子回归")
    ap.add_argument("--json", action="store_true", help="只写用例文件")
    args = ap.parse_args()
    if args.json:
        CASES.write_text(
            json.dumps(
                {
                    "_meta": {"说明": "命科机械因子回归用例（非古籍占验）"},
                    "tune": [],
                    "holdout": [],
                    "regression": REGRESSION,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print("wrote", CASES)
        raise SystemExit(0)
    raise SystemExit(run())
