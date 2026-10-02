# -*- coding: utf-8 -*-
"""梅花易数·金标准指纹：对固定案例集产出稳定指纹，用于证明"纯结构重构不改行为"。

    python dev_tools/golden.py capture "重构排盘逻辑，字段等价"   # 改动前落基线（必须给理由）
    python dev_tools/golden.py verify                           # 默认；比对指纹，漂移退出码 1

覆盖：全部案例（tune + holdout）的 chart 段与 analyze 段逐字段快照。
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
        # 金标准只罩「固定案例集」（tune/holdout）；external_holdout 是永不调参的演进评测集，
        # 其增删属预期 churn，不应污染引擎行为指纹（否则每次加外部例都要重捕基线）。
        if case.get("split") in ("external_holdout", "excluded"):
            continue
        params = dict(case.get("input") or {})
        params.setdefault("question", case.get("question") or case.get("topic") or "")
        try:
            c = chart(params)
            a = analyze(c)
            rows.append({
                "id": case.get("id"),
                "hexagram": f"{c.get('hexagram')}·{c.get('moving')}动",
                "body_use": f"{a['body_use'].get('体卦')}{a['body_use'].get('体卦五行')}/"
                            f"{a['body_use'].get('用卦')}{a['body_use'].get('用卦五行')}/"
                            f"{a['body_use'].get('关系')}",
                "interaction": [f"{h.get('位')}{h.get('卦')}{h.get('作用')}"
                                for h in a["interaction"].get("生体之卦") or []] +
                               [f"{h.get('位')}{h.get('卦')}{h.get('作用')}"
                                for h in a["interaction"].get("克体之卦") or []],
                "qi": (a.get("body_qi") or {}).get("状态"),
                "verdict": a["conclusion"].get("方向"),
                "special": a["conclusion"].get("特断", False),
                "timing_gz": a["timing"].get("卦气应期") or [],
                "numerical": a["timing"].get("数应"),
                "narrate_sha": hashlib.sha256(str(_narrate(a)).encode("utf-8")).hexdigest()[:12],
            })
        except Exception as exc:
            rows.append({"id": case.get("id"), "error": f"{type(exc).__name__}: {exc}"})
    return rows


def main() -> int:
    from yishu_core.golden_kit import run
    return run(
        "梅花易数",
        what="金标准指纹基线（chart+analyze 逐字段）",
        how='改动引擎行为后跑 python dev_tools/golden.py capture "理由"；'
            "机械层漂移=行为变化，措辞层漂移=narrate 断语变化（两层分列归因）",
        fingerprint=fingerprint, out=OUT, digest_path=DIGEST)


if __name__ == "__main__":
    raise SystemExit(main())
