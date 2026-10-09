# -*- coding: utf-8 -*-
"""重构看门狗：拆分/搬家前后的「零指纹漂移」验收。

    python dev_tools/refactor_guard.py --write guard/step5.json     # 改动前存基线
    python dev_tools/refactor_guard.py --compare guard/step5.json   # 改动后比对

覆盖两条链路（都是 step3/step5 的下游，`AGENTS.md` 铁律一要求机械运算零漂移）：
  reading —— format_reading_output + format_text_output 的逐字符报告文本
  chain   —— 五步思维链产出（判语/分数/应期/推理链/叙述）

只报差异不做修复。差异非空即说明改动动了逻辑，不许拿「分数没变」当挡箭牌——
分数是 20+ 例的聚合，个别案例的文本漂移会被均分吃掉。

用法约定：拆分这类纯搬移的活，先 --write，改完 --compare，两条都零差异才算过。
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

from kernel_path import ensure_kernel_on_path  # noqa: E402

ensure_kernel_on_path(ROOT / "scripts" / "kernel_path.py")

import case_runner  # noqa: E402
from case_runner import build_hexagram_result, hex2yao, resolve_case_time  # noqa: E402
from engine_format import format_reading_output, format_text_output  # noqa: E402
from thinking_chain import run_thinking_chain  # noqa: E402
from liuyao_narrate import build_human_narrative, render_human_markdown  # noqa: E402

# 案例库里本就有少数缺卦名的条目会固定失败；超过这个数就是脚本自己的问题。
# 教训：曾经因为传错参数让 115 例全挂，两次「指纹一致」其实是两次同样的全失败——
# 空跑比对出的零漂移是假的，所以这里强制自检有效样本数，不合格直接拒绝出结论。
MAX_ERRORS = 8

# step5 直接产出、以及会被 step5/step3 输出改写的一切下游字段
CHAIN_KEYS = [
    "final_score", "verdict", "special_pattern", "yingqi",
    "yingqi_branches", "yingqi_months", "yingqi_years", "yingqi_dates",
    "reasoning_chain", "pattern_tags", "human_narrative", "human_markdown",
]


def _build(case: dict) -> tuple:
    """还原时刻 → 排盘 → 思维链 → 报告，返回 (排盘结果, 思维链结果)。"""
    q = case.get("question") or (case.get("input") or {}).get("question", "")
    hx = case.get("hexagram") or {}
    yao = hex2yao(hx.get("original"), hx.get("changed"))
    if yao is None:
        raise ValueError(f"无法解析卦象 {hx.get('original')}")
    dt = resolve_case_time(case)["dt"]
    h = build_hexagram_result(yao, q, "manual", dt.year, dt.month, dt.day, dt.hour)
    return h, run_thinking_chain(h)


def snapshot() -> dict:
    out = {}
    for case in case_runner.load_cases():
        cid = case.get("id")
        if not cid:
            continue
        try:
            h, tc = _build(case)
            thinking = tc.get("thinking_chain", tc)
            s5 = thinking.get("step5_synthesis") or {}
            timing = s5.get("timing") or {}
            rc = thinking.get("reasoning_chain", []) or []
            human = build_human_narrative(tc)
            out[cid] = {
                "reading": format_reading_output(h, tc),
                "text": format_text_output(h),
                "chain": {
                    "final_score": s5.get("final_score"),
                    "verdict": s5.get("verdict"),
                    "special_pattern": (s5.get("special_pattern") or {}).get("pattern"),
                    "yingqi": timing.get("summary_text"),
                    "yingqi_branches": timing.get("key_branches") or [],
                    "yingqi_months": timing.get("yingqi_months") or [],
                    "yingqi_years": timing.get("yingqi_years") or [],
                    "yingqi_dates": s5.get("yingqi_dates") or [],
                    "reasoning_chain": rc,
                    "pattern_tags": [ln for ln in rc
                                     if isinstance(ln, str) and ("[格局]" in ln or "[格局要点]" in ln)],
                    "human_narrative": human,
                    "human_markdown": render_human_markdown(human),
                },
            }
        except Exception as exc:  # 失败方式本身也参与指纹
            out[cid] = {"error": f"{type(exc).__name__}: {exc}"}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="重构看门狗：零指纹漂移验收")
    ap.add_argument("--write", help="把快照明细写入文件（改动前跑）")
    ap.add_argument("--compare", help="与既有快照比对（改动后跑）")
    ap.add_argument("--diff-limit", type=int, default=3, help="最多展开几个差异案例")
    args = ap.parse_args()

    if not args.write and not args.compare:
        ap.error("至少给 --write 或 --compare 之一")

    snap = snapshot()
    errs = [v for v in snap.values() if "error" in v]
    if len(errs) > MAX_ERRORS:
        print(f"× 失败 {len(errs)}/{len(snap)} 例，超过上限 {MAX_ERRORS}——快照不可信，拒绝出结论")
        print(f"  首个错误：{errs[0]['error'] if errs else ''}")
        return 2
    blob = json.dumps(snap, ensure_ascii=False, sort_keys=True, default=str)
    print(f"案例 {len(snap)} 条（失败 {len(errs)}）｜指纹 {hashlib.sha256(blob.encode('utf-8')).hexdigest()[:16]}")

    if args.write:
        p = Path(args.write)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(blob, encoding="utf-8")
        print(f"明细已写入 {p}")

    if args.compare:
        old = Path(args.compare).read_text(encoding="utf-8")
        if old == blob:
            print("√ 与基线一致（零漂移）")
            return 0
        import difflib
        o, n = json.loads(old), json.loads(blob)
        diff = 0
        for k in sorted(set(o) | set(n)):
            if o.get(k) == n.get(k):
                continue
            diff += 1
            if diff > args.diff_limit:
                continue
            print(f"  --- {k}")
            ov, nv = o.get(k) or {}, n.get(k) or {}
            for field in ("reading", "text"):
                if ov.get(field) != nv.get(field):
                    print(f"      [{field}]")
                    for ln in list(difflib.unified_diff(
                            str(ov.get(field)).splitlines(),
                            str(nv.get(field)).splitlines(),
                            "旧", "新", lineterm=""))[:20]:
                        print("        " + ln)
            if ov.get("chain") != nv.get("chain"):
                for f in CHAIN_KEYS:
                    a, b = (ov.get("chain") or {}).get(f), (nv.get("chain") or {}).get(f)
                    if a != b:
                        print(f"      chain.{f}:\n        旧 {str(a)[:240]}\n        新 {str(b)[:240]}")
        print(f"共 {diff} 例不同")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
