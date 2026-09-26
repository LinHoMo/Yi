# -*- coding: utf-8 -*-
"""根级质量门：一条命令跑完全仓库检查。

  python tools/check.py          # 快速门（默认）：版本/结构契约/内核自检/三科快速门/六爻冒烟/合参自检
  python tools/check.py --full   # 全量门：再加三科 tune/holdout 案例评测与六爻黑箱回归（慢）
  python tools/check.py --only version,structure,core   # 只跑指定检查项

设计口径（与各科 tools/check.py 一致）：
  - 分数都是古籍案例对齐分，只用于回归审计（AGENTS.md 铁律三）；
  - 版本号唯一真值源 core/yishu_core/__init__.py::__version__，此处负责抓第二份；
  - 依赖方向单向（disciplines → core，synthesis → disciplines 的 schema），违反即缺陷。
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core"
sys.path.insert(0, str(CORE))

from yishu_core import __version__  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

# 四段契约要求的文件（新三科严格核验；liuyao 为迁移前旧实现，另立检查项）
CONTRACT_FILES = ("SKILL.md", "scripts/chart.py", "scripts/analyze.py",
                  "scripts/narrate.py", "scripts/render.py",
                  "data/verdicts.json", "tools/check.py", "tools/golden.py")
NEW_DISCIPLINES = ("meihua", "xiaoliuren", "zeji", "ming")

# 内核唯一真值表名：学科内出现同名赋值即视为复制（AGENTS.md 内核唯一真值源）
CORE_TABLE_ASSIGN = re.compile(
    r"^\s*(EARTHLY_BRANCHES|HEAVENLY_STEMS|BAGUA_LINES|HEXAGRAM_TRIGRAMS|"
    r"EIGHT_PALACES|TRIGRAM_ELEMENTS|XIAN_TIAN_TRIGRAM_NUMBERS|NUMBER_TO_TRIGRAM|"
    r"SHENG_CYCLE|KE_CYCLE|TWELVE_CHANGES|NAJIA|LIU_QIN|LIU_SHEN|"
    r"ER_SHISI_XIU|JIAN_CHU|HUANG_HEI_DAO)\s*=\s*[\[\{]", re.M)

# 学科间 import（违反 disciplines 禁止互相 import 的契约）
CROSS_DISC_IMPORT = re.compile(
    r"^\s*(from|import)\s+(liuyao|meihua|xiaoliuren|zeji)\b", re.M)


def _run_py(cmd: list[str], *, label: str, cwd: Path = ROOT) -> tuple[int, str]:
    """子进程跑一个质量门；返回 (退出码, 输出)。"""
    try:
        p = subprocess.run([sys.executable, *cmd], cwd=cwd,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=1200)
    except subprocess.TimeoutExpired:
        return 1, f"{label}: 超时（>1200s）"
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def check_version() -> list[str]:
    """版本唯一真值源：除 core/yishu_core/__init__.py 外，任何 .py 不得写死版本。"""
    fails = []
    pat = re.compile(r'(__version__\s*=\s*["\']|version\s*=\s*["\']\d)')
    for p in ROOT.rglob("*.py"):
        if "__pycache__" in p.parts or "scratch" in p.parts:
            continue
        if p == CORE / "yishu_core" / "__init__.py":
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if pat.search(line):
                fails.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()}")
    return fails


def check_structure() -> list[str]:
    """学科目录契约：新三科四段文件齐全；依赖方向单向。"""
    fails = []
    for disc in NEW_DISCIPLINES:
        d = ROOT / "disciplines" / disc
        for f in CONTRACT_FILES:
            if not (d / f).exists():
                fails.append(f"{disc}/ 缺 {f}（CONTRACT.md 四段契约）")
        if not (d / "data" / "cases").is_dir():
            fails.append(f"{disc}/data/cases 目录缺失（案例分层）")
    # 学科互相 import
    for disc in ("liuyao", "meihua", "xiaoliuren", "zeji"):
        scripts = ROOT / "disciplines" / disc / "scripts"
        if not scripts.is_dir():
            continue
        for p in scripts.rglob("*.py"):
            if "scratch" in p.parts:
                continue
            for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                m = CROSS_DISC_IMPORT.match(line)
                if m and m.group(2) != disc:
                    fails.append(f"{p.relative_to(ROOT)}:{i}: 学科间 import {m.group(2)}")
    return fails


def check_core_tables() -> list[str]:
    """内核表唯一：学科内不得重新定义 core 已有规则表。"""
    fails = []
    for p in (ROOT / "disciplines").rglob("*.py"):
        if "scratch" in p.parts or "__pycache__" in p.parts:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if CORE_TABLE_ASSIGN.match(line):
                name = line.strip().split("=", 1)[0].strip()
                fails.append(f"{p.relative_to(ROOT)}:{i}: 复制内核表 {name}"
                             f"（唯一真值源在 core）")
    return fails


def _tail(out: str, n: int = 3) -> str:
    return "\n".join(out.strip().splitlines()[-n:])


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="易·仓库级质量门")
    ap.add_argument("--only", nargs="*", help="限定检查项：version,structure,tables,core,"
                                              "meihua,xiaoliuren,zeji,liuyao,synthesis")
    ap.add_argument("--full", action="store_true",
                    help="全量：三科案例评测（tune/holdout）+ 六爻黑箱回归（慢）")
    args = ap.parse_args()

    only = set(args.only) if args.only else None
    failures: list[str] = []
    run_all = only is None

    def gate(name: str, fails: list[str], label: str):
        if only is not None and name not in only:
            return
        if fails:
            failures.extend(fails)
            print(f"  × {label}")
            for f in fails:
                print(f"      · {f}")
        else:
            print(f"  √ {label}")

    def gate_sub(name: str, cmd: list[str], label: str, *, fast: bool = True):
        if only is not None and name not in only:
            return
        argv = list(cmd)
        if fast:
            argv.insert(1, "--fast") if cmd[0].endswith("check.py") else None
        code, out = _run_py(argv, label=label)
        if code == 0:
            print(f"  √ {label}")
        else:
            failures.append(f"{label} 退出码 {code}")
            print(f"  × {label}")
            print(f"      …{_tail(out)}")

    print(f"[0] 版本一致性（唯一真值源 yishu_core.__version__ = {__version__}）")
    gate("version", check_version(), "全仓库无第二处版本号")

    print("\n[1] 结构契约（CONTRACT.md 四段 + 依赖方向单向 + 内核表唯一）")
    gate("structure", check_structure(), "学科目录完整、无学科间 import")
    gate("tables", check_core_tables(), "内核规则表无学科复制")

    print("\n[2] 内核自检（干支历/农历/评分器）")
    if only is None or "core" in only:
        code, out = _run_py(["core/yishu_core/calendar_check.py"], label="内核自检")
        if code == 0:
            print("  √ 干支历内核自检")
        else:
            failures.append("内核自检失败")
            print("  × 干支历内核自检")
            print(f"      …{_tail(out)}")

    for disc in NEW_DISCIPLINES:
        print(f"\n[{NEW_DISCIPLINES.index(disc) + 3}] {disc} 质量门"
              f"{'（含案例评测）' if args.full else '（快速：指纹+冒烟）'}")
        gate_sub(disc, [f"disciplines/{disc}/tools/check.py"], disc, fast=not args.full)

    print("\n[6] 六爻（迁移前旧实现：冒烟 + 四段契约端到端；--full 加黑箱回归）")
    gate_sub("liuyao", ["disciplines/liuyao/scripts/smoke_test.py"], "六爻冒烟", fast=False)
    # 六爻四段契约薄适配层（chart→analyze→render）端到端冒烟
    scratch = ROOT / "tools" / "scratch" / "liuyao_pipeline"
    scratch.mkdir(parents=True, exist_ok=True)
    chart_json = scratch / "chart.json"
    analyze_json = scratch / "analyze.json"
    report_md = scratch / "report.md"
    pipe_steps = [
        (["disciplines/liuyao/scripts/chart.py", "--mode", "time",
          "--datetime", "2026-09-23 10:00", "--question", "占合同能否成交",
          "-o", str(chart_json)], "六爻 chart"),
        (["disciplines/liuyao/scripts/analyze.py", str(chart_json),
          "-o", str(analyze_json)], "六爻 analyze"),
        (["disciplines/liuyao/scripts/render.py", str(analyze_json),
          "-o", str(report_md)], "六爻 render"),
    ]
    pipe_ok = True
    for cmd, label in pipe_steps:
        code, out = _run_py(cmd, label=label)
        if code != 0:
            pipe_ok = False
            print(f"  × {label}")
            print(f"      …{_tail(out)}")
    if pipe_ok and report_md.is_file() and analyze_json.is_file():
        print("  √ 六爻四段契约端到端（chart→analyze→render）")
    elif pipe_ok:
        pipe_ok = False
        failures.append("六爻四段契约产物缺失")
        print("  × 六爻四段契约产物缺失")
    if not pipe_ok:
        failures.append("六爻四段契约端到端失败")
    if args.full and (only is None or "liuyao" in only):
        # 六爻自身质量门对回归用基线口径（11/18，2026-09-22 实测），
        # 残余案例待古籍重推（README/HANDOFF 已声明）——根门对齐该口径，不得要求全过。
        code, out = _run_py(["disciplines/liuyao/scripts/regression_test.py"], label="六爻回归")
        m = re.search(r"总通过:\s*(\d+)/(\d+)", out)
        if code == 0 or (m and int(m.group(1)) >= 11):
            print(f"  √ 六爻黑箱回归（{m.group(0) if m else '通过'}，基线 11/18）")
        else:
            failures.append("六爻黑箱回归低于基线")
            print("  × 六爻黑箱回归（低于基线 11/18）")
            print(f"      …{_tail(out)}")

    print("\n[7] 合参层（synthesis 自检：person 校验 + 裁决规则 + 归一化）")
    gate_sub("synthesis", ["synthesis/cli.py", "selfcheck"], "synthesis 自检", fast=False)

    print()
    if failures:
        print(f"质量门失败 {len(failures)} 项。")
        for f in failures:
            print(f"  × {f}")
        return 1
    print("仓库级质量门全部通过。")
    print("分数含义：与古籍案例要点的一致性，不代表现实预测命中率。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
