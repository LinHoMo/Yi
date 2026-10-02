# -*- coding: utf-8 -*-
"""择吉·金标准指纹：对固定案例集产出稳定指纹，用于证明"纯结构重构不改行为"。

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
        if case.get("split") == "excluded":   # 超范围输入不可运行，不参与指纹
            continue
        params = dict(case.get("input") or {})
        params.setdefault("question", case.get("question") or "")
        params.setdefault("activity", case.get("activity"))
        try:
            c = chart(params)
            a = analyze(c)
            rows.append({
                "id": case.get("id"),
                "date": c.get("date"),
                "activity": a.get("activity"),
                "jian_chu": a["factors_detail"]["jian_chu"].get("神"),
                "day_god": a["factors_detail"]["huang_dao"].get("神"),
                "huang_dao": a["factors_detail"]["huang_dao"].get("黄道"),
                "xiu": a["factors_detail"]["xiu"].get("宿"),
                "yi_hit": a.get("yi_hit"),
                "ji_hit": a.get("ji_hit"),
                "verdict": a["conclusion"].get("方向"),
                "score": a["conclusion"].get("得分"),
                "narrate_sha": hashlib.sha256(str(_narrate(a)).encode("utf-8")).hexdigest()[:12],
            })
        except Exception as exc:
            rows.append({"id": case.get("id"), "error": f"{type(exc).__name__}: {exc}"})
    return rows


def main() -> int:
    from yishu_core.golden_kit import run
    return run(
        "择吉",
        what="金标准指纹基线（chart+analyze 逐字段）",
        how='改动引擎行为后跑 python dev_tools/golden.py capture "理由"；'
            "机械层漂移=行为变化，措辞层漂移=narrate 断语变化（两层分列归因）",
        fingerprint=fingerprint, out=OUT, digest_path=DIGEST)


if __name__ == "__main__":
    raise SystemExit(main())
