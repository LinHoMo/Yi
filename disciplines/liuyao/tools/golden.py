# -*- coding: utf-8 -*-
"""排盘金标准：对固定输入集产出稳定指纹，用来证明"纯结构重构不改行为"。

    python tools/golden.py capture   # 重构前落盘 scratch/golden_before.json
    python tools/golden.py verify    # 重构后比对，任何字段差异都列出来并退出码 1

覆盖：64 卦在三个干支时刻（含立春边界内外、夜子时）下，静卦 + 单动 + 双动三种爻型。
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from kernel_path import kernel_dir as _kernel_dir  # noqa: E402
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(_kernel_dir(__file__))]
OUT = ROOT / "scratch" / "golden_before.json"

TIMES = ["2024-02-03 10:30", "2024-02-05 10:30", "2026-09-22 23:40"]
QUESTIONS = ["占求财", "占病", "占行人", "占婚姻", "占讼", "占失物"]


def fingerprint() -> list[dict]:
    from liuyao_engine import build_hexagram_result
    from thinking_chain import run_thinking_chain
    from classical_analysis import enhance_reading
    import case_runner as cr

    names = sorted(cr.HEXAGRAM_TRIGRAMS)
    rows = []
    for i, name in enumerate(names):
        base = cr.hex2yao(name)
        for moving in ([], [i % 6], [i % 6, (i + 3) % 6]):
            yao = [9 if (v == 7 and idx in moving) else (6 if (v == 8 and idx in moving) else v)
                   for idx, v in enumerate(base)]
            for when in (TIMES[0], TIMES[2]) if i % 2 == 0 else (TIMES[1],):
                dt = datetime.strptime(when, "%Y-%m-%d %H:%M")
                q = QUESTIONS[i % len(QUESTIONS)]
                try:
                    h = build_hexagram_result(yao, q, "manual",
                                              dt.year, dt.month, dt.day, dt.hour)
                    enriched = run_thinking_chain(h)
                    inner = enriched.get("thinking_chain", {})
                    adv = enhance_reading(h) or {}
                    s2 = inner.get("step2_use_god_identification", {}) or {}
                    s5 = inner.get("step5_synthesis", {}) or {}
                    sel = s2.get("selected_use_god") or {}
                    t = h["divination_time"]
                    rows.append({
                        "case": f"{name}|{moving}|{when}|{q}",
                        "pillars": f"{t['year_stem_branch']}-{t['month_stem_branch']}-{t['day_stem_branch']}-{t.get('hour_stem_branch', '')}",
                        "lines": [
                            f"{y['six_relation']}{y['earthly_branch']}{y['six_spirit']}"
                            f"{'*动' if y.get('is_moving') else ''}"
                            f"{'#世' if y.get('is_world') else ''}"
                            f"{'@应' if y.get('is_response') else ''}"
                            f"{'○空' if y.get('is_empty') else ''}"
                            for y in h["original_hexagram"]["yao_lines"]],
                        "palace": f"{h['original_hexagram'].get('palace')}/{h['original_hexagram'].get('generation')}",
                        "empty": h.get("empty_branches"),
                        "changed": (h.get("changed_hexagram") or {}).get("name"),
                        "use_god": f"{s2.get('use_god_category')}@{sel.get('earthly_branch')}#{sel.get('position')}",
                        "strength": (inner.get("step3_strength_analysis") or {}).get("strength_level"),
                        "verdict": s5.get("verdict"),
                        "score": s5.get("final_score"),
                        "yingqi_branches": (s5.get("timing") or {}).get("key_branches"),
                        "adv_keys": sorted(adv.keys()),
                        "adv_summary": {k: json.dumps(v, ensure_ascii=False, sort_keys=True)[:220]
                                        for k, v in sorted(adv.items())},
                        "patterns": [t2 for t2 in (inner.get("reasoning_chain") or [])
                                     if isinstance(t2, str) and t2.startswith("[格局")],
                    })
                except Exception as exc:
                    rows.append({"case": f"{name}|{moving}|{when}|{q}",
                                 "error": f"{type(exc).__name__}: {exc}"})
    return rows


def main() -> int:
    from yishu_core.runtime import force_utf8_stdio
    force_utf8_stdio()
    mode = sys.argv[1] if len(sys.argv) > 1 else "verify"
    rows = fingerprint()
    blob = json.dumps(rows, ensure_ascii=False, sort_keys=True, indent=1)
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]
    errors = [r for r in rows if "error" in r]
    print(f"用例 {len(rows)} 条｜指纹 {digest}｜异常 {len(errors)} 条")
    for e in errors[:10]:
        print("  !", e["case"], e["error"])

    if mode == "capture":
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(blob, encoding="utf-8")
        print("金标准已落盘 →", OUT)
        return 0

    if not OUT.exists():
        print("缺金标准基线，请先 capture")
        return 2
    before = json.loads(OUT.read_text(encoding="utf-8"))
    changed = [(a, b) for a, b in zip(before, rows) if a != b]
    if len(before) != len(rows):
        print(f"\n× 用例数变化：{len(before)} → {len(rows)}")
        return 1
    if changed:
        print(f"\n× 行为发生变化（{len(changed)}/{len(rows)} 条）：")
        for a, b in changed[:6]:
            keys = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
            print(f"  {a.get('case')}: {keys}")
            for k in keys[:3]:
                print(f"      旧 {str(a.get(k))[:200]}")
                print(f"      新 {str(b.get(k))[:200]}")
        return 1
    print("√ 与重构前逐字段一致（纯结构重构，无行为漂移）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
