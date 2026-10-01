# -*- coding: utf-8 -*-
"""紫微斗数·金标准指纹：固定出生时刻 → 生产稳定指纹，证明"纯机械逻辑不变"。

   python dev_tools/golden.py capture "新建学科,初始指纹"  # 改动前落基线（必须给理由）
   python dev_tools/golden.py verify                           # 默认；比对指纹，漂移退出码 1
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
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
    from yishu_core.runtime import force_utf8_stdio
    force_utf8_stdio()
    ap = argparse.ArgumentParser(
        description="紫微斗数金标准指纹：capture 落基线 / verify 比对漂移")
    ap.add_argument("mode", nargs="?", default="verify", choices=("capture", "verify"))
    ap.add_argument("reason", nargs="?", default="")
    args = ap.parse_args()

    rows = fingerprint()
    blob = json.dumps(rows, ensure_ascii=False, sort_keys=True, indent=1)
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]
    errors = [r for r in rows if "error" in r]
    print(f"用例 {len(rows)} 条｜指纹 {digest}｜异常 {len(errors)} 条")
    for e in errors[:10]:
        print(f"  ! {e['id']} {e['error']}")

    if args.mode == "capture":
        if not args.reason.strip():
            print("× 重新落基线必须给理由")
            return 2
        OUT.parent.mkdir(exist_ok=True, parents=True)
        OUT.write_text(blob, encoding="utf-8")
        DIGEST.parent.mkdir(parents=True, exist_ok=True)
        prior = {}
        if DIGEST.exists():
            prior = json.loads(DIGEST.read_text(encoding="utf-8"))
        log = list(prior.get("drift_log") or [])
        log.append({"from": prior.get("digest"), "to": digest,
                    "date": datetime.now().strftime("%Y-%m-%d"), "reason": args.reason.strip()})
        DIGEST.write_text(json.dumps({
            "_meta": {"what": "紫微斗数金标准指纹基线",
                      "how": "改动引擎后跑 python dev_tools/golden.py capture \"理由\""},
            "digest": digest,
            "drift_log": log[-20:]}, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
        print(f"金标准已落盘 → {DIGEST}")
        return 0

    if not DIGEST.exists():
        print(f"缺指纹基线 {DIGEST.relative_to(DISC)}")
        return 2
    want = json.loads(DIGEST.read_text(encoding="utf-8")).get("digest")
    if digest == want:
        print(" 与基线指纹一致（行为未漂移）")
        return 0
    print(f"\n行为漂移：基线 {want} → 现在 {digest}")
    if OUT.exists():
        before = json.loads(OUT.read_text(encoding="utf-8"))
        changed = [(a, b) for a, b in zip(before, rows) if a != b]
        print(f" 逐条比对：{len(changed)} 条变化")
        for a, b in changed[:6]:
            keys = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
            print(f"  {a.get('id')}: {keys}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
