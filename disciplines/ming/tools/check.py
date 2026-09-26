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


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, *cmd],
        cwd=DISC,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
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
        "tools/check.py",
        "tools/golden.py",
    ]
    for rel in required:
        if not (DISC / rel).exists():
            fails.append(f"缺 {rel}")
    print("[0] 契约文件", "√" if not fails else "×")

    code, out = run(["scripts/chart.py", "--datetime", "1990-05-20 10:30", "-o", "scratch/chart.json"])
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
        if (a.get("conclusion") or {}).get("verdicts"):
            fails.append("analyze 不应产出断语（M5 骨架）")
        print("[2] analyze 冒烟 √（无断语）")

    code, out = run(["scripts/narrate.py", "scratch/analyze.json"])
    if code != 0 or "未实现" not in out:
        fails.append("narrate 应明示未实现")
        print(out)
    else:
        print("[3] narrate 占位 √")

    code, out = run(["tools/golden.py", "verify"])
    if code != 0:
        fails.append("金标准指纹漂移")
        print(out)
    else:
        print("[4] 金标准 √", out.strip())

    if fails:
        print("失败：", *fails, sep="\n  ")
        return 1
    print("命科质量门通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
