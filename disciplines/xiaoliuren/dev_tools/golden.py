# -*- coding: utf-8 -*-
"""小六壬·金标准指纹：对固定案例集产出稳定指纹，用于证明"纯结构重构不改行为"。

    python dev_tools/golden.py capture "重构排盘逻辑,字段等价"   # 改动前落基线（必须给理由）
    python dev_tools/golden.py verify                           # 默认；比对指纹，漂移退出码 1

覆盖：全部 15 例案例（tune 10 + holdout 5）的 chart 段与 analyze 段逐字段快照。
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

OUT = DISC / "scratch" / "golden_before.json"           # 全量快照（gitignore）
DIGEST = DISC / "data" / "golden" / "digest.json"       # 指纹基线（入库）


def fingerprint() -> list[dict]:
    import case_runner as cr
    from chart import chart
    from analyze import analyze
    from narrate import narrate as _narrate

    rows = []
    for case in cr.load_cases():
        if case.get("split") == "excluded":   # 空输入不可运行，不参与指纹
            continue
        params = dict(case.get("input") or {})
        params.setdefault("question", case.get("question") or case.get("topic") or "")
        params.setdefault("topic", case.get("topic"))
        try:
            c = chart(params)
            a = analyze(c)
            p = a["palace"]
            rows.append({
                "id": case.get("id"),
                "way": c.get("way"),
                "steps": [f"{s.get('步')}{s.get('落宫')}" for s in a.get("steps") or []],
                "palace": p.get("宫名"),
                "palace_el": p.get("五行"),
                "direction": p.get("方向"),
                "verdict": a["conclusion"].get("方向"),
                "topic": a.get("topic"),
                "topic_line": (a.get("topic_verdict") or {}).get("诀句"),
                "timing": a["timing"].get("主数"),
                "narrate_sha": hashlib.sha256(str(_narrate(a)).encode("utf-8")).hexdigest()[:12],
            })
        except Exception as exc:
            rows.append({"id": case.get("id"), "error": f"{type(exc).__name__}: {exc}"})
    return rows


def main() -> int:
    from yishu_core.golden_kit import run
    return run(
        "小六壬",
        what="金标准指纹基线（chart+analyze 逐字段）",
        how='改动引擎行为后跑 python dev_tools/golden.py capture "理由"；'
            "机械层漂移=行为变化，措辞层漂移=narrate 断语变化（两层分列归因）",
        fingerprint=fingerprint, out=OUT, digest_path=DIGEST)


if __name__ == "__main__":
    raise SystemExit(main())
