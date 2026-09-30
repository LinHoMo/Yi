# -*- coding: utf-8 -*-
"""排盘金标准：对固定输入集产出稳定指纹，用来证明"纯结构重构不改行为"。

    python dev_tools/golden.py capture   # 重构前落盘 scratch/golden_before.json
    python dev_tools/golden.py verify    # 重构后比对，任何字段差异都列出来并退出码 1

覆盖：64 卦在三个干支时刻（含立春边界内外、夜子时）下，静卦 + 单动 + 双动三种爻型。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from kernel_path import kernel_dir as _kernel_dir  # noqa: E402
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(_kernel_dir(__file__))]
OUT = ROOT / "scratch" / "golden_before.json"          # 全量快照（gitignore，只在本地做逐条比对）
DIGEST = ROOT / "data" / "golden" / "digest.json"      # 指纹基线（入库，换机器也拦得住漂移）

TIMES = ["2024-02-03 10:30", "2024-02-05 10:30", "2026-09-22 23:40"]
# 问法要覆盖到"关系人"：用神那层关系法则只在句中出现父/母/夫/妻/伯… 时才触发，
# 旧题面六种全不触发，等于给那层法则留了盲区（改了也没人报警）。
QUESTIONS = ["占求财", "占病", "占行人", "占婚姻", "占讼", "占失物",
             "占父病", "占夫外出", "占妻胎安否", "占伯何日回", "占子久病",
             "占升遷", "占候文書"]


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
                    row = {
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
                    }
                    # 文案门：抽样子集记 narrate 文案哈希（HANDOFF：指纹原不含 narrate）
                    if i % 24 == 0 and not moving:
                        try:
                            from analyze import analyze as _analyze
                            from narrate import narrate as _narrate
                            a = _analyze(h)
                            text = _narrate(a)
                            row["narrate_sha"] = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
                            row["narrate_len"] = len(text)
                        except Exception as nex:
                            row["narrate_sha"] = f"ERR:{type(nex).__name__}"
                    rows.append(row)
                except Exception as exc:
                    rows.append({"case": f"{name}|{moving}|{when}|{q}",
                                 "error": f"{type(exc).__name__}: {exc}"})
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
        print("  !", e["case"], e["error"])

    if mode == "capture":
        if not reason.strip():
            print("× 重新落基线必须给理由：python dev_tools/golden.py capture \"为何允许漂移\"")
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
            "_meta": {"what": "金标准指纹基线（排盘+思维链+分析层逐字段；抽样含 narrate 文案哈希）",
                      "how": "改动引擎行为后跑 python dev_tools/golden.py capture \"理由\"；"
                             "无理由不落盘，历次漂移见 drift_log",
                      "cases": len(rows)},
            "digest": digest,
            "drift_log": log[-20:]}, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
        print("金标准已落盘 →", OUT, "与", DIGEST)
        return 0

    if not DIGEST.exists():
        print(f"缺指纹基线 {DIGEST.relative_to(ROOT)}")
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
        print(f"  {a.get('case')}: {keys}")
        for k in keys[:3]:
            print(f"      旧 {str(a.get(k))[:160]}")
            print(f"      新 {str(b.get(k))[:160]}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
