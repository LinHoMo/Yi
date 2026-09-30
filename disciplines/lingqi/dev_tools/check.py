# -*- coding: utf-8 -*-
"""灵棋经·质量门：契约文件 + 课表完整性 + 四段冒烟 + 金标准。"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
CORE = DISC.parents[1] / "core"


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run([sys.executable, *cmd], cwd=DISC, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=120,
                       env={**os.environ, "PYTHONUTF8": "1"})
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main() -> int:
    force = {"PYTHONUTF8": "1"}
    fails: list[str] = []

    required = ["SKILL.md", "scripts/chart.py", "scripts/analyze.py",
                "scripts/narrate.py", "scripts/render.py",
                "data/ketables.json", "dev_tools/check.py", "dev_tools/golden.py"]
    missing = [r for r in required if not (DISC / r).exists()]
    if missing:
        fails.append(f"缺 {missing}")
    print("[0] 契约文件", "√" if not missing else "×")

    # [1] 课表完整性：124 课、键集合 = 全部非零三部组合、课名齐全唯一
    table = json.loads((DISC / "data" / "ketables.json").read_text(encoding="utf-8"))
    courses = table.get("courses") or {}
    expect_keys = {f"{u}-{m}-{d}" for u in range(5) for m in range(5)
                   for d in range(5) if (u, m, d) != (0, 0, 0)}
    keys = set(courses)
    if len(courses) != 124 or keys != expect_keys:
        fails.append(f"课表键数 {len(courses)} ≠ 124 或键集合不匹配 "
                     f"(缺 {len(expect_keys - keys)}，多 {len(keys - expect_keys)})")
    noname = [k for k, v in courses.items() if not v.get("name")]
    if noname:
        fails.append(f"缺课名: {noname[:5]}")
    names = [v["name"] for v in courses.values()]
    dup = sorted({n for n in names if names.count(n) > 1})
    if dup:
        fails.append(f"课名重复: {dup[:5]}")
    if table.get("problems"):
        fails.append(f"构建器报告问题: {table['problems']}")
    print(f"[1] 课表完整性 √ 124 课" if not any("课表" in f or "课名" in f for f in fails)
          else "[1] 课表完整性 ×")

    # [2] 全 124 课逐一走 chart（机械查表无异常）
    sys.path.insert(0, str(DISC / "scripts"))
    from chart import chart as chart_fn  # noqa: E402
    bad = []
    for key in sorted(keys):
        u, m, d = (int(x) for x in key.split("-"))
        try:
            c = chart_fn(u, m, d)
            if c["men"] != courses[key]["name"]:
                bad.append(f"{key} 课名不匹配")
        except Exception as exc:  # noqa: BLE001
            bad.append(f"{key}: {type(exc).__name__}: {exc}")
    if bad:
        fails.extend(bad[:5])
        print("[2] 全课查表 ×", *bad[:5], sep="\n    ")
    else:
        print("[2] 全课查表 √ 124/124")

    code, out = run(["scripts/chart.py", "--up", "4", "--mid", "3", "--down", "2",
                     "--question", "占谋事", "-o", "scratch/chart.json"])
    if code != 0:
        fails.append("chart 冒烟失败")
        print(out[-600:])
    else:
        print("[3] chart 冒烟 √")

    code, out = run(["scripts/analyze.py", "scratch/chart.json", "-o", "scratch/analyze.json"])
    if code != 0:
        fails.append("analyze 冒烟失败")
        print(out[-600:])
    else:
        print("[4] analyze 冒烟 √")

    code, out = run(["scripts/narrate.py", "scratch/analyze.json"])
    if code != 0 or "不是现实预测" not in out:
        fails.append("narrate 应声明非现实预测")
        print(out[-600:])
    else:
        print("[5] narrate 口径声明 √")

    code, out = run(["scripts/render.py", "scratch/analyze.json", "-o", "scratch/report.md"])
    if code != 0 or not (DISC / "scratch" / "report.md").exists():
        fails.append("render 冒烟失败")
        print(out[-600:])
    else:
        print("[6] render 冒烟 √")

    code, out = run(["dev_tools/golden.py", "verify"])
    if code != 0:
        fails.append("金标准指纹漂移")
        print(out[-600:])
    else:
        print("[7] 金标准 √", out.strip())

    if fails:
        print("\n质量门未通过：", *fails, sep="\n  · ")
        return 1
    print("\n灵棋经质量门全部通过。")
    print("口径：查表直录《靈棋經》原文断语，非本仓推断，不是现实预测命中率。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
