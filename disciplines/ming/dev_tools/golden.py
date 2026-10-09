# -*- coding: utf-8 -*-
"""命·金标准指纹：固定 6 样例的强弱/格局/大运字段快照。

   python dev_tools/golden.py capture "理由"  # 有意漂移后落基线（必须给理由）
   python dev_tools/golden.py verify           # 默认；比对指纹，漂移退出码 1
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

OUT = DISC / "scratch" / "golden_ming_before.json"
DIGEST = DISC / "data" / "golden" / "digest.json"

# 覆盖身旺/身弱/中和与不同月令格的固定样例
SAMPLES = [
    {"datetime": "1984-02-10 10:00", "gender": "男", "label": "mid_jianlu"},
    {"datetime": "1996-11-11 22:00", "gender": "男", "label": "strong_jianlu"},
    {"datetime": "1990-05-20 10:30", "gender": "男", "label": "weak_shangguan"},
    {"datetime": "1984-12-08 08:00", "gender": "女", "label": "weak_zhengguan"},
    {"datetime": "2000-08-15 14:00", "gender": "男", "label": "weak_zhengguan2"},
    {"datetime": "1955-04-20 04:00", "gender": "女", "label": "mid_zhengyin"},
]


def fingerprint() -> list[dict]:
    from chart import chart
    from analyze import analyze
    from narrate import narrate as _narrate

    out = []
    for s in SAMPLES:
        c = chart(
            s["label"],
            datetime_str=s["datetime"],
            gender=s["gender"],
        )
        a = analyze(c)
        con = a.get("conclusion") or {}
        out.append({
            "sample": s["label"],
            "datetime": s["datetime"],
            "pillars": {k: (v or {}).get("ganzhi") for k, v in (c.get("pillars") or {}).items()},
            "strength": con.get("strength"),
            "strength_score": con.get("strength_score"),
            "pattern": con.get("pattern"),
            "useful_gods": con.get("useful_gods"),
            "dayun_head": (con.get("dayun") or [{}])[0] if con.get("dayun") else None,
            "narrate_sha": hashlib.sha256(str(_narrate(a)).encode("utf-8")).hexdigest()[:12],
        })
    return out


def main() -> int:
    from yishu_core.golden_kit import run
    return run(
        "命科（四柱）",
        what="命科金标准指纹基线（强弱/格局/大运逐字段）",
        how='改动引擎行为后跑 python dev_tools/golden.py capture "理由"；'
            "机械层漂移=行为变化，措辞层漂移=narrate 断语变化（两层分列归因）",
        fingerprint=fingerprint, out=OUT, digest_path=DIGEST)


if __name__ == "__main__":
    raise SystemExit(main())
