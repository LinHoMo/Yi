# -*- coding: utf-8 -*-
"""命·金标准指纹（骨架）：固定样例字段快照，证明结构重构不改行为。"""
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

DIGEST = DISC / "data" / "golden" / "digest.json"


def fingerprint() -> list[dict]:
    from chart import chart

    return [chart("金标准", datetime_str="1990-05-20 10:30", gender="男")]


def digest() -> str:
    blob = json.dumps(fingerprint(), ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def main() -> int:
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
            json.dumps({"fingerprint": d, "reason": args.reason}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"captured {d}")
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
