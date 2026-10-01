# -*- coding: utf-8 -*-
"""大六壬金标准：固定输入集产出稳定指纹，防「纯重构改行为」。

    python dev_tools/golden.py capture "理由"   # 重构前落盘 / 有意漂移后重落
    python dev_tools/golden.py verify           # 重构后比对（退出码判门）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"),
                str(ROOT.parents[1] / "core")]

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
        dt = datetime.strptime(when, "%Y-%m-%d %H:%M")
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


def _digest(rows: list[dict]) -> str:
    blob = json.dumps(rows, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


DIGEST = ROOT / "data" / "golden" / "digest.json"


def main() -> int:
    ap = argparse.ArgumentParser(description="大六壬金标准指纹（capture/verify）")
    ap.add_argument("action", nargs="?", default="verify", choices=["capture", "verify"])
    ap.add_argument("reason", nargs="?", default="", help="capture 模式必填理由")
    args = ap.parse_args()
    rows = fingerprint()
    digest = _digest(rows)
    if args.action == "capture":
        if not args.reason:
            print("capture 必须写理由（AGENTS.md §四：为何允许漂移）")
            return 2
        DIGEST.parent.mkdir(parents=True, exist_ok=True)
        DIGEST.write_text(json.dumps(
            {"digest": digest, "reason": args.reason, "n": len(rows)},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"用例 {len(rows)} 条｜指纹 {digest}｜已落盘 {DIGEST.name}")
        return 0
    if not DIGEST.is_file():
        print("无金标准基线，先 capture")
        return 2
    base = json.loads(DIGEST.read_text(encoding="utf-8"))
    if base["digest"] == digest:
        print(f"指纹一致 {digest}（{len(rows)} 例）")
        return 0
    print(f"× 指纹漂移：基线 {base['digest']} ≠ 现在 {digest}")
    for old, new in zip(base.get("rows") or [], rows):
        if old != new:
            print("  变化例：", json.dumps(old, ensure_ascii=False), "→",
                  json.dumps(new, ensure_ascii=False))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
