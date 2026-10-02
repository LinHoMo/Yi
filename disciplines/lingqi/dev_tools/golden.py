# -*- coding: utf-8 -*-
"""灵棋经金标准：124 课全量表指纹——课表数据漂移即报。

    python dev_tools/golden.py capture "理由" / verify
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT.parents[1] / "core")]

KETABLE = ROOT / "data" / "ketables.json"
OUT = ROOT / "scratch" / "golden_before.json"
DIGEST = ROOT / "data" / "golden" / "digest.json"


def fingerprint() -> list[dict]:
    table = json.loads(KETABLE.read_text(encoding="utf-8"))
    courses = table["courses"]
    # 机械层：课表**全字段**（含卦宫与标注组原文）——原指纹只罩 name/xiang，
    # 象曰/詩曰被静默并入相邻课这类数据漂移不会报警（曾漏到用户眼前）。
    canon = json.dumps({
        "courses": courses,
        "appendix": table.get("appendix") or [],
        "gongs": table.get("gongs") or [],
    }, ensure_ascii=False, sort_keys=True)
    row = {"case": "ketables-124",
           "n": len(courses),
           "names": {k: v["name"] for k, v in sorted(courses.items())},
           "xiang": {k: v["xiang"] for k, v in sorted(courses.items())},
           "gong": {k: v.get("gong", "") for k, v in sorted(courses.items())},
           "notes": sum(len(v.get("notes") or []) for v in courses.values()),
           "appendix": [a.get("title") for a in table.get("appendix") or []],
           "table_sha": hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16]}
    # 四段契约的 analyze / narrate 段也要进指纹：原指纹只罩课表数据，
    # 改 analyze 或 narrate 的措辞不会报警（曾漏到用户眼前）。
    from analyze import analyze
    from chart import chart
    from narrate import narrate as _narrate
    import io
    import contextlib
    nrows = []
    for key in sorted(courses):
        up, mid, down = (int(x) for x in key.split("-"))
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                a = analyze(chart(up, mid, down, question="占问"))
                text = _narrate(a)
        except Exception as exc:                      # noqa: BLE001 — 指纹要记死错误类型
            nrows.append(f"{key}:ERR:{type(exc).__name__}")
            continue
        nrows.append(f"{key}:{hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]}")
    row["narrate_lines"] = nrows
    return [row]


def main() -> int:
    from yishu_core.golden_kit import run
    return run(
        "灵棋经",
        what="灵棋经金标准指纹基线（124 课全量表 + analyze/narrate 逐课哈希）",
        how='改动引擎行为后跑 python dev_tools/golden.py capture "理由"；'
            "机械层漂移=课表/analyze 结构变化，措辞层漂移=narrate 断语变化（两层分列归因）",
        fingerprint=fingerprint, out=OUT, digest_path=DIGEST)


if __name__ == "__main__":
    raise SystemExit(main())
