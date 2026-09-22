# -*- coding: utf-8 -*-
"""一条命令跑完全部质量门：`python tools/check.py [--only eval,calendar]`

  python tools/check.py            # 全部检查
  python tools/check.py --fast     # 跳过耗时的两套案例评测
  python tools/check.py --raise    # 把当前实测值写回基线（确认改进后才用）

门槛设计（见 AGENTS.md §四）：
  · 历法自检、段落产出冒烟 —— 必须全绿，任何回退即失败
  · 思维链用例、古籍回归、tune/holdout 对齐分 —— **只准前进不准后退**：
    与 BASELINE 比较，低于基线即失败。基线是 2026-09-22 重建评分器后的实测值，
    不是"理想值"；M1/M2 修好后用 --raise 抬上去。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

BASELINE_FILE = ROOT / "tools" / "check_baseline.json"

BASELINE = {
    "calendar": 16,        # 自检通过项数（共 16）
    "smoke": 36,           # 有产出的分析段
    "chain_tests": 7,      # /12  —— 已知 5 例失败（吉凶区间、动变净效应）
    "regression": 10,      # /18  —— 已知 8 例古典结论维度不符
    "tune": 97.1,          # 古籍对齐分 strict，n=20（参与过调参）
    "holdout": 86.2,       # 古籍对齐分 strict，n=12（未参与调参）
}

PATTERNS = {
    "chain_tests": r"Passed:\s*(\d+)/(\d+)",
    "regression": r"总通过:\s*(\d+)/(\d+)",
    "smoke": r"有产出:\s*(\d+)",
}


def run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def measure(name: str, out: str) -> float | None:
    pat = PATTERNS.get(name)
    if not pat:
        return None
    m = re.search(pat, out)
    return float(m.group(1)) if m else None


def eval_score(split: str) -> tuple[float | None, int]:
    path = ROOT / "data" / "cases" / f"eval_{split}.json"
    rc, _out = run([sys.executable, "scripts/evaluate.py", "--split", split, "--save"])
    if not path.exists():
        return None, rc
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["results"]["strict"]["avg"], rc


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="六爻质量门")
    ap.add_argument("--only", nargs="*", help="限定检查项")
    ap.add_argument("--fast", action="store_true", help="跳过案例评测（tune/holdout）")
    ap.add_argument("--raise", dest="raise_baseline", action="store_true",
                    help="以本次实测覆盖基线（仅在确认改进后使用）")
    args = ap.parse_args()

    baseline = dict(BASELINE)
    if BASELINE_FILE.exists():
        baseline.update(json.loads(BASELINE_FILE.read_text(encoding="utf-8")))

    measured: dict[str, float] = {}
    failures: list[str] = []

    def gate(name: str, value: float | None, *, minimum: float, label: str, raw: str = ""):
        if value is None:
            failures.append(f"{label}: 未能从输出取到指标")
            print(f"  × {label:<34s} 取数失败")
            return
        ok = value >= minimum - 1e-9
        measured[name] = value
        mark = "√" if ok else "×"
        print(f"  {mark} {label:<34s} {value:g} (基线 {minimum:g})")
        if not ok:
            failures.append(f"{label} {value:g} < 基线 {minimum:g}")
            print(raw[-1500:])

    selected = set(args.only or ["calendar", "smoke", "chain_tests", "regression", "eval"])

    if "calendar" in selected:
        print("\n[1] 干支历内核自检")
        rc, out = run([sys.executable, "core/yishu_core/calendar_check.py"])
        passed = re.search(r"自检：(\d+) 项通过，(\d+) 项失败", out)
        if passed:
            gate("calendar", float(passed.group(1)), minimum=baseline["calendar"],
                 label="自检通过项", raw=out)
        if rc != 0:
            failures.append("历法自检退出码非 0")

    if "smoke" in selected:
        print("\n[2] 分析段落产出冒烟（只验有无产出）")
        rc, out = run([sys.executable, "scripts/smoke_test.py"])
        gate("smoke", measure("smoke", out), minimum=baseline["smoke"],
             label="段落有产出数", raw=out)

    if "chain_tests" in selected:
        print("\n[3] 思维链用例（12 例，逐维度断言）")
        rc, out = run([sys.executable, "scripts/thinking_chain_tests.py"])
        gate("chain_tests", measure("chain_tests", out), minimum=baseline["chain_tests"],
             label="用例通过数", raw=out)

    if "regression" in selected:
        print("\n[4] 古籍回归（18 例，用神/方向/区间三维）")
        rc, out = run([sys.executable, "scripts/regression_test.py"])
        gate("regression", measure("regression", out), minimum=baseline["regression"],
             label="回归通过数", raw=out)

    if "eval" in selected and not args.fast:
        print("\n[5] 古籍案例对齐分（strict 口径；非现实预测命中率）")
        for split in ("tune", "holdout"):
            avg, rc = eval_score(split)
            gate(split, avg, minimum=baseline[split], label=f"{split} 对齐分 %")

    print("\n" + "=" * 62)
    if failures:
        print("质量门未通过：")
        for f in failures:
            print(f"  · {f}")
        return 1

    if args.raise_baseline:
        new = dict(BASELINE)
        new.update({k: v for k, v in measured.items()})
        BASELINE_FILE.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
        print(f"基线已抬升 → {BASELINE_FILE}")
        print(json.dumps(new, ensure_ascii=False))
        return 0

    print("质量门全部通过（或不低于基线）。")
    print("分数含义：与古籍案例要点的一致性，不代表现实预测命中率。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
