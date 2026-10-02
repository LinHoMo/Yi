# -*- coding: utf-8 -*-
"""大六壬金标准：固定输入集产出稳定指纹，防「纯重构改行为」。

    python dev_tools/golden.py capture "理由"   # 有意漂移后重落
    python dev_tools/golden.py verify           # 重构后比对（退出码判门）
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"),
                str(ROOT.parents[1] / "core")]

OUT = ROOT / "scratch" / "golden_before.json"
DIGEST = ROOT / "data" / "golden" / "digest.json"

# 覆盖：四时月将（含中气换将边界前后）、昼夜贵人两侧、刚柔日各半
TIMES = [
    "2024-02-03 10:30",   # 立春后·雨水前（月将仍子·神后）
    "2024-02-20 10:30",   # 雨水后（亥将·登明）
    "2024-08-08 23:10",   # 夜贯
    "2026-09-22 12:00",
]
QUESTIONS = ["占求财", "占病", "占行人", "占讼"]


def fingerprint() -> list[dict]:
    from analyze import analyze as _analyze
    from narrate import narrate as _narrate
    from chart import chart as _chart

    rows = []
    for i, when in enumerate(TIMES):
        q = QUESTIONS[i % len(QUESTIONS)]
        c = _chart(when, q)
        a = _analyze(c)
        rows.append({
            "case": f"{when}|{q}",
            "day": c["moment"]["day_ganzhi"],
            "hour_branch": c["moment"]["hour_branch"],
            "yuejiang": c["yuejiang"]["branch"],
            "men": c["men"],
            "ke_name": c["ke_name"],
            "san_chuan": c["san_chuan"],
            "dun_gan": c["dun_gan"],
            "four_courses": [(x["xia"], x["shang"]) for x in c["four_courses"]],
            "chuan_tianjiang": [(x["chuan"], x["jiang"]) for x in c["chuan_tianjiang"]],
            "factors": [f["basis"] for f in a["factors"]],
            "narrate_sha": hashlib.sha256(str(_narrate(a)).encode("utf-8")).hexdigest()[:12],
        })
    return rows


def main() -> int:
    from yishu_core.golden_kit import run
    return run(
        "大六壬",
        what="大六壬金标准指纹基线（排盘+九宗门+天将逐字段）",
        how='改动引擎行为后跑 python dev_tools/golden.py capture "理由"；'
            "机械层漂移=行为变化，措辞层漂移=narrate 断语变化（两层分列归因）",
        fingerprint=fingerprint, out=OUT, digest_path=DIGEST)


if __name__ == "__main__":
    raise SystemExit(main())
