# -*- coding: utf-8 -*-
"""命·质量门：契约完整性 + 四段冒烟 + 金标准。"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.runtime import utf8_subprocess_env  # noqa: E402


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, *cmd],
        cwd=DISC,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        env=utf8_subprocess_env(),
    )
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main() -> int:
    force_utf8_stdio()
    fails = []

    required = [
        "SKILL.md",
        "scripts/chart.py",
        "scripts/analyze.py",
        "scripts/narrate.py",
        "scripts/render.py",
        "data/verdicts.json",
        "dev_tools/check.py",
        "dev_tools/golden.py",
    ]
    for rel in required:
        if not (DISC / rel).exists():
            fails.append(f"缺 {rel}")
    print("[0] 契约文件", "√" if not fails else "×")

    code, out = run(["scripts/chart.py", "--datetime", "1990-05-20 10:30", "--gender", "男", "-o", "scratch/chart.json"])
    if code != 0:
        fails.append("chart 冒烟失败")
        print(out)
    else:
        print("[1] chart 冒烟 √")

    code, out = run(["scripts/analyze.py", "scratch/chart.json", "-o", "scratch/analyze.json"])
    if code != 0:
        fails.append("analyze 冒烟失败")
        print(out)
    else:
        a = json.loads((DISC / "scratch" / "analyze.json").read_text(encoding="utf-8"))
        con = a.get("conclusion") or {}
        # 机械标签允许；禁止「命运吉凶」总断
        if con.get("方向"):
            fails.append("analyze 不应给出命运方向总断")
        for v in con.get("verdicts") or []:
            if not isinstance(v, dict) or not v.get("basis"):
                fails.append("verdicts 须带 basis")
                break
        if not con.get("strength") or not con.get("pattern"):
            fails.append("缺 strength/pattern 机械推演")
        if not con.get("dayun"):
            fails.append("缺 dayun 大运表")
        print("[2] analyze 机械推演 √" if not any("analyze" in f or "verdicts" in f or "strength" in f or "dayun" in f or "方向" in f for f in fails) else "[2] analyze ×")

    code, out = run(["scripts/narrate.py", "scratch/analyze.json"])
    if code != 0 or "不是命运断言" not in out:
        fails.append("narrate 应声明非命运断言")
        print(out)
    else:
        print("[3] narrate 口径声明 √")

    code, out = run(["dev_tools/golden.py", "verify"])
    if code != 0:
        fails.append("金标准指纹漂移")
        print(out)
    else:
        print("[4] 金标准 √", out.strip())

    code, out = run(["dev_tools/regression.py"])
    if code != 0:
        fails.append("机械因子回归失败")
        print(out)
    else:
        print("[5] 机械回归 √", out.strip().splitlines()[-1] if out.strip() else "")

    # 评测器存在性 + 框架自检 + 空集可跑（命科评测是新立的尺子，必须校准）
    if not (DISC / "scripts" / "evaluate.py").is_file():
        fails.append("缺 scripts/evaluate.py（命科评测器）")
        print("[6] 评测器 ×")
    else:
        code, out = run(["dev_tools/eval_selftest.py"])
        if code != 0:
            fails.append("评测框架自检失败")
            print(out)
        else:
            print("[6] 评测框架自检 √", out.strip().splitlines()[-2]
                  if len(out.strip().splitlines()) > 1 else "")
        # tune / holdout 都必须能跑（n=0 时如实报"尚无案例"，不是报错）
        for split in ("tune", "holdout"):
            code, out = run(["scripts/evaluate.py", "--split", split])
            if code != 0 and "无可用结果" not in out:
                fails.append(f"评测 {split} 跑不通")
                print(out)
            else:
                head = out.strip().splitlines()[0] if out.strip() else ""
                print(f"[7] 评测 {split} √ {head}")

    if fails:
        print("失败：", *fails, sep="\n  ")
        return 1
    print("命科质量门通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
