# -*- coding: utf-8 -*-
"""命·金标准指纹：固定 6 样例的强弱/格局/大运字段快照。"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.runtime import force_utf8_stdio  # noqa: E402

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


def digest() -> str:
    blob = json.dumps(fingerprint(), ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="命·金标准指纹")
    ap.add_argument("mode", nargs="?", default="verify", choices=("capture", "verify"))
    ap.add_argument("reason", nargs="?", help="capture 理由")
    args = ap.parse_args()

    d = digest()
    if args.mode == "capture":
        if not args.reason:
            print("capture 必须写理由", file=sys.stderr)
            return 1
        DIGEST.parent.mkdir(parents=True, exist_ok=True)
        DIGEST.write_text(
            json.dumps(
                {"fingerprint": d, "reason": args.reason, "n_samples": len(SAMPLES)},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"captured {d} n={len(SAMPLES)}")
        return 0

    if not DIGEST.exists():
        print("缺 digest.json，先 capture", file=sys.stderr)
        return 1
    base = json.loads(DIGEST.read_text(encoding="utf-8")).get("fingerprint")
    if d != base:
        print(f"指纹漂移: now={d} base={base}", file=sys.stderr)
        return 1
    print(f"指纹一致 {d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
