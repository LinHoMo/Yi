# -*- coding: utf-8 -*-
"""灵棋经金标准：124 课全量表指纹——课表数据漂移即报。

    python dev_tools/golden.py capture "理由" / verify
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

KETABLE = ROOT / "data" / "ketables.json"
DIGEST = ROOT / "data" / "golden" / "digest.json"


def fingerprint() -> dict:
    table = json.loads(KETABLE.read_text(encoding="utf-8"))
    courses = table["courses"]
    return {"n": len(courses),
            "names": {k: v["name"] for k, v in sorted(courses.items())},
            "xiang": {k: v["xiang"] for k, v in sorted(courses.items())}}


def digest_of(rows: dict) -> str:
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False,
                                     sort_keys=True).encode("utf-8")).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser(description="灵棋经金标准指纹（capture/verify）")
    ap.add_argument("action", nargs="?", default="verify", choices=["capture", "verify"])
    ap.add_argument("reason", nargs="?", default="")
    args = ap.parse_args()
    rows = fingerprint()
    digest = digest_of(rows)
    if args.action == "capture":
        if not args.reason:
            print("capture 必须写理由（AGENTS.md §四）")
            return 2
        DIGEST.parent.mkdir(parents=True, exist_ok=True)
        DIGEST.write_text(json.dumps({"digest": digest, "reason": args.reason,
                                      "n": rows["n"]}, ensure_ascii=False, indent=1),
                          encoding="utf-8")
        print(f"课表 {rows['n']} 课｜指纹 {digest}｜已落盘")
        return 0
    base = json.loads(DIGEST.read_text(encoding="utf-8"))
    if base["digest"] == digest:
        print(f"指纹一致 {digest}（{rows['n']} 课）")
        return 0
    print(f"× 指纹漂移：基线 {base['digest']} ≠ 现在 {digest}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
