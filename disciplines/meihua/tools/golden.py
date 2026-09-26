# -*- coding: utf-8 -*-
"""梅花易数·金标准指纹：对固定案例集产出稳定指纹，用于证明"纯结构重构不改行为"。

    python tools/golden.py capture "重构排盘逻辑，字段等价"   # 改动前落基线（必须给理由）
    python tools/golden.py verify                          # 默认；比对指纹，漂移退出码 1

覆盖：全部案例（tune + holdout）的 chart 段与 analyze 段逐字段快照。
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

OUT = DISC / "scratch" / "golden_before.json"           # 全量快照（gitignore）
DIGEST = DISC / "data" / "golden" / "digest.json"       # 指纹基线（入库）


def fingerprint() -> list[dict]:
    import case_runner as cr
    from chart import chart
    from analyze import analyze

    rows = []
    for case in cr.load_cases():
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
            })
        except Exception as exc:
            rows.append({"id": case.get("id"), "error": f"{type(exc).__name__}: {exc}"})
    return rows


def main() -> int:
    from yishu_core.runtime import force_utf8_stdio
    force_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="金标准指纹：capture 落基线 / verify 比对漂移（默认）")
    parser.add_argument("mode", nargs="?", default="verify", choices=("capture", "verify"),
                        help="capture 落新基线；verify 比对基线指纹（默认）")
    parser.add_argument("reason", nargs="?", default="",
                        help="capture 模式必填：为何允许漂移（防掩盖退步，见 AGENTS.md 四）")
    args = parser.parse_args()
    mode, reason = args.mode, args.reason
    rows = fingerprint()
    blob = json.dumps(rows, ensure_ascii=False, sort_keys=True, indent=1)
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]
    errors = [r for r in rows if "error" in r]
    print(f"用例 {len(rows)} 条｜指纹 {digest}｜异常 {len(errors)} 条")
    for e in errors[:10]:
        print("  !", e["id"], e["error"])

    if mode == "capture":
        if not reason.strip():
            print("× 重新落基线必须给理由：python tools/golden.py capture \"为何允许漂移\"")
            print("  基线下调/漂移不写理由＝掩盖退步（AGENTS.md 四）。")
            return 2
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(blob, encoding="utf-8")
        DIGEST.parent.mkdir(parents=True, exist_ok=True)
        prior = {}
        if DIGEST.exists():
            prior = json.loads(DIGEST.read_text(encoding="utf-8"))
        log = list(prior.get("drift_log") or [])
        log.append({"from": prior.get("digest"), "to": digest,
                    "date": datetime.now().strftime("%Y-%m-%d"), "reason": reason.strip()})
        DIGEST.write_text(json.dumps({
            "_meta": {"what": "金标准指纹基线（chart+analyze 逐字段）",
                      "how": "改动引擎行为后跑 python tools/golden.py capture \"理由\"；"
                             "无理由不落盘，历次漂移见 drift_log",
                      "cases": len(rows)},
            "digest": digest,
            "drift_log": log[-20:]}, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
        print("金标准已落盘 →", OUT, "与", DIGEST)
        return 0

    if not DIGEST.exists():
        print(f"缺指纹基线 {DIGEST.relative_to(DISC)}")
        return 2
    want = json.loads(DIGEST.read_text(encoding="utf-8")).get("digest")
    if digest == want:
        print("√ 与基线指纹一致（行为未漂移）")
        return 0
    print(chr(10) + f"× 行为漂移：基线 {want} → 现在 {digest}")
    if not OUT.exists():
        print("  本地无全量快照时只能据此判断「改的是不是你要改的东西」；"
              "要逐条比对请先 capture 再改动。")
        return 1
    before = json.loads(OUT.read_text(encoding="utf-8"))
    changed = [(a, b) for a, b in zip(before, rows) if a != b] if len(before) == len(rows) else []
    print(f"  逐条比对（本地快照 {len(before)} 条）：{len(changed)} 条变化")
    for a, b in changed[:6]:
        keys = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
        print(f"  {a.get('id')}: {keys}")
        for k in keys[:3]:
            print(f"      旧 {str(a.get(k))[:160]}")
            print(f"      新 {str(b.get(k))[:160]}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
