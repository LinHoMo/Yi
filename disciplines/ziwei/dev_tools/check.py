# -*- coding: utf-8 -*-
"""紫微斗数质量门：`python dev_tools/check.py [--fast]`

   python dev_tools/check.py            # 全部检查（目前仅_struct_contract + golden + pipeline 冒烟）
   python dev_tools/check.py --fast     # 跳过论文档评测

紫微斗数是机械命科（出生时空→格局/四化/大限），无案例对齐评测（类比 ming 机械回归）。
验证点：四段契约文件齐全、JSON 排盘产出正确、金标准指纹稳定。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.runtime import force_utf8_stdio  # noqa: E402


def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=str(DISC), capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def check_structure() -> list[str]:
    """四段契约 + 目录结构验证。"""
    CONTRACT_FILES = (
        "SKILL.md", "scripts/chart.py", "scripts/analyze.py",
        "scripts/narrate.py", "scripts/render.py",
        "data/verdicts.json", "dev_tools/check.py", "dev_tools/golden.py",
    )
    fails = []
    for f in CONTRACT_FILES:
        if not (DISC / f).exists():
            fails.append(f"学科缺 {f}（CONTRACT 契约）")
    if not (DISC / "data" / "cases").is_dir():
        fails.append("data/cases 目录缺失")
    # 内核表唯一：学科内不得重新定义 core 已有表
    CORE_TABLE = re.compile(
        r"^\s*(PALACES|WUXING_TO_JU|SIHUA_TABLE|ZIWEI_GROUP_ORDER|TIANFU_GROUP_ORDER|"
        r"STARS|AUXILIARY_STARS|PATTERNS)\s*=\s*[\[\{]", re.M)
    for p in (DISC / "scripts").rglob("*.py"):
        if "scratch" in p.parts:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if CORE_TABLE.match(line):
                name = line.strip().split("=", 1)[0].strip()
                fails.append(f"{p.relative_to(DISC)}:{i}: 复制核心表 {name}（应从 core.ziwei_tables import）")
    return fails


def check_pipeline() -> list[str]:
    """四段管线冒烟：chart→analyze→narrate→render 端到端。"""
    import tempfile
    fails = []
    scratch = DISC / "scratch"
    scratch.mkdir(exist_ok=True)
    chart_json = scratch / "chart.json"
    analyze_json = scratch / "analyze.json"
    narrate_md = scratch / "narrate.md"
    render_md = scratch / "render.md"

    steps = [
        ([sys.executable, "scripts/chart.py", "--datetime", "1990-05-20 10:30",
          "--gender", "男", "-o", str(chart_json)], "chart"),
        ([sys.executable, "scripts/analyze.py", str(chart_json),
          "-o", str(analyze_json)], "analyze"),
        ([sys.executable, "scripts/narrate.py", str(analyze_json),
          "-o", str(narrate_md)], "narrate"),
        ([sys.executable, "scripts/render.py", str(analyze_json),
          "-o", str(render_md)], "render"),
    ]
    for cmd, label in steps:
        rc, out = _run(cmd)
        if rc != 0:
            fails.append(f"{label} 段退出码 {rc}: {out[:200]}")
    # 验证 JSON 结构
    if chart_json.exists():
        c = json.loads(chart_json.read_text(encoding="utf-8"))
        if c.get("palaces", {}).get("命宫", {}).get("main_stars") in (None, []):
            fails.append("chart 命宫无主星（可能排盘异常）")
    return fails


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="紫微斗数质量门")
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()

    selected = set(args.only or ["structure", "golden", "pipeline"])
    failures: list[str] = []

    if "structure" in selected:
        print("\n[1] 四段契约与结构")
        fails = check_structure()
        if fails:
            for f in fails:
                print(f"  × {f}")
            failures.extend(fails)
        else:
            print("  √ 四段契约文件齐全")

    if "pipeline" in selected:
        print("\n[2] 四段管线冒烟")
        fails = check_pipeline()
        if fails:
            for f in fails:
                print(f"  × {f}")
            failures.extend(fails)
        else:
            print("  √ 四段管线端到端通过")

    if "golden" in selected and not args.fast:
        print("\n[3] 金标准指纹")
        rc, out = _run([sys.executable, "dev_tools/golden.py"])
        if rc == 0:
            print(f"  √ {out.strip()}")
        else:
            failures.append("金标准指纹失败")
            print(f"  × {out.strip()}")

    print()
    if failures:
        print(f"质量门未通过 {len(failures)} 项")
        for f in failures:
            print(f"  · {f}")
        return 1
    print("紫微斗数质量门全部通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
