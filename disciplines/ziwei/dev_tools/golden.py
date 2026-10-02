# -*- coding: utf-8 -*-
"""紫微斗数·金标准指纹：固定出生时刻 → 生产稳定指纹，证明"纯机械逻辑不变"。

   python dev_tools/golden.py capture "理由"  # 改动后落基线（必须给理由）
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

OUT = DISC / "scratch" / "golden_ziwei_before.json"
DIGEST = DISC / "data" / "golden" / "digest.json"

GOLDEN_CASES = [
    {"id": "ZM001", "datetime": "1990-05-20 10:30", "gender": "男"},
    {"id": "ZM002", "datetime": "1968-03-15 01:00", "gender": "男"},
    {"id": "ZM003", "datetime": "1977-11-08 14:20", "gender": "女"},
    {"id": "ZM004", "datetime": "1984-02-04 08:00", "gender": "男"},
]


def fingerprint() -> list[dict]:
    from chart import ziwei_chart
    from analyze import ziwei_analyze
    from narrate import narrate as _narrate

    rows = []
    for case in GOLDEN_CASES:
        try:
            c = ziwei_chart(
                datetime_str=case["datetime"],
                gender=case["gender"],
            )
            a = ziwei_analyze(c)
            con = a.get("conclusion") or {}
            cs = a.get("chart_summary") or {}
            rows.append({
                "id": case["id"],
                "mg_stars": cs.get("命宫主星"),
                "pattern": cs.get("格局"),
                "ju": cs.get("五行局"),
                "ziwei": c.get("ziwei", {}).get("branch"),
                "tianfu": c.get("tianfu", {}).get("branch"),
                "ming_gong": c.get("ming_gong", {}).get("branch"),
                "sihua": c.get("sihua", {}),
                "direction": con.get("方向"),
                "dayun_step1_age": (con.get("dayun") or [{}])[0].get("start_age"),
                "narrate_sha": hashlib.sha256(str(_narrate(a)).encode("utf-8")).hexdigest()[:12],
            })
        except Exception as exc:
            rows.append({"id": case["id"], "error": f"{type(exc).__name__}: {exc}"})
    return rows


def main() -> int:
    from yishu_core.golden_kit import run
    return run(
        "紫微斗数",
        what="紫微斗数金标准指纹基线",
        how='改动引擎后跑 python dev_tools/golden.py capture "理由"；'
            "机械层漂移=行为变化，措辞层漂移=narrate 断语变化（两层分列归因）",
        fingerprint=fingerprint, out=OUT, digest_path=DIGEST)


if __name__ == "__main__":
    raise SystemExit(main())
