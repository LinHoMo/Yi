#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""八字象层覆盖读数器（362 批）：量「象出没出」，不量「象准不准」。

与六爻侧同款口径（devkit 两科各一份，因盘面构造不同）：本器只回答
  ① 覆盖：宫位/六亲/脏腑三象在各盘上的产出率，缺的缺在哪；
  ② 性别分野：男命/女命的六亲口径是否各自生效（有没有恒通用口径的退化）。
**不产命中率、对齐分或任何质量结论**——出没出和准不准是两件事（SKILL.md 铁律三）。

    python dev_tools/xiang_coverage.py
    python dev_tools/xiang_coverage.py --json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "core"))

XIANG_KEYS = ("gongwei", "liugin", "zangfu")

# 定盘集：日干覆盖五阳干，四柱取自书源命例式的干支组合（不挑"好看"的盘）
SAMPLE_PILLARS = [
    {"year": "甲辰", "month": "己巳", "day": "甲子", "hour": "辛未"},
    {"year": "丙寅", "month": "庚寅", "day": "丙申", "hour": "癸巳"},
    {"year": "戊子", "month": "辛酉", "day": "戊午", "hour": "甲寅"},
    {"year": "庚午", "month": "壬午", "day": "庚辰", "hour": "丁丑"},
    {"year": "壬戌", "month": "癸卯", "day": "壬寅", "hour": "乙巳"},
]


def _xiang_of(pillars: dict, gender: str) -> dict:
    from chart import chart_from_pillars
    from analyze import analyze as _analyze
    from xiang import build_xiang
    a = _analyze(chart_from_pillars(pillars, gender=gender, question="象层覆盖"))
    return build_xiang({**a, "bing_yao": a.get("bing_yao")})


def _filled(blk) -> bool:
    if not isinstance(blk, dict):
        return False
    body = {k: v for k, v in blk.items() if k != "basis"}
    return any(v not in ("", None, [], {}) for v in body.values())


def scan() -> dict:
    rows = []
    for i, p in enumerate(SAMPLE_PILLARS):
        for g in ("男", "女"):
            x = _xiang_of(p, g)
            lg = x.get("liugin") or {}
            rows.append({
                "idx": i, "day": p["day"], "gender": g,
                "keys": {k: _filled(x.get(k)) for k in XIANG_KEYS},
                "liugin": {c: ((lg.get(c) or {}).get("六亲") or "")
                           for c in ("年", "月", "日", "时")},
                "has": bool(x),
            })
    return {"rows": rows, "keys": list(XIANG_KEYS)}


def report(data: dict) -> int:
    rows = data["rows"]
    keys = data["keys"]
    n = len(rows)
    print(f"象层覆盖读数：{n} 盘（{len(SAMPLE_PILLARS)} 定盘 × 男女）")
    print("口径：**有没有出**（素材覆盖），不是「准不准」（命中率）——本器不产任何质量分\n")

    print("① 象目产出率")
    for k in keys:
        hit = sum(1 for r in rows if r["keys"].get(k))
        print(f"  {k:<10} {hit}/{n}  {hit * 100 // n}%")

    print("\n② 六亲性别分野（同盘男女应给出不同口径）")
    by_idx: dict[int, dict[str, dict]] = {}
    for r in rows:
        by_idx.setdefault(r["idx"], {})[r["gender"]] = r["liugin"]
    flat = 0
    for i, per in sorted(by_idx.items()):
        m, f = per.get("男", {}), per.get("女", {})
        diff = [c for c in ("年", "月", "日", "时") if m.get(c) != f.get(c)]
        tag = f"差异柱：{'、'.join(diff)}" if diff else "（本盘四柱六亲男女同辞：该盘十神不含财官分野柱）"
        if not diff:
            flat += 1
        print(f"  盘{i} 日柱{ SAMPLE_PILLARS[i]['day'] }　{tag}")
    if flat:
        print(f"  · {flat}/{len(by_idx)} 个定盘男女口径无差异：这类盘的十神不含财/官/比劫，"
              "通用口径下男女同辞（分野只在财官比劫几途）——要确证分野生效须用含财官的盘")
    else:
        print(f"  · {len(by_idx)}/{len(by_idx)} 个定盘男女口径均有差异：分野生效"
              "（比劫的兄弟/姐妹亦按性别分列，故差异柱可满四柱）")

    zero = [r for r in rows if not r["has"]]
    if zero:
        print(f"\n× 象层整块缺失 {len(zero)} 盘")
        return 1
    print("\n读数完毕。缺哪一类就补哪一类，别拿本器的百分比当成绩。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="八字象层覆盖读数器（只报覆盖，不报命中率）")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = ap.parse_args()
    data = scan()
    if args.json:
        import json
        print(json.dumps(data, ensure_ascii=False, indent=1))
        return 0
    return report(data)


if __name__ == "__main__":
    raise SystemExit(main())
