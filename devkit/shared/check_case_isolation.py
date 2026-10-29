# -*- coding: utf-8 -*-
"""案例库隔离门：解读/推演路径不得触达 `data/cases/`（评测层专用）。

为什么需要它（2026-10-10）：`core/yishu_core/gate_kit.py` 头注写着
「解读路径不得触达案例库」由 tools/case_isolation_check.py 机械守，
而 `tools/` 随仓库扁平化已删除——这句话自那以后就是空话，**没有任何东西在守它**。

这条纪律为什么是 P0：一旦 narrate/render/step 层读到 `expected`，
「引擎输出 vs 古籍要点」就不再是两个独立量，对齐分可以被动inflate 而门禁全绿——
正是评测方法学 §三.4 与 SKILL.md 铁律所禁的"用引擎输出反推期望"的反方向风险。

口径：
  · **白名单**（允许读案例库）：评测与案例装载层 —— evaluate.py / case_runner.py /
    dev_tools/* / tests/*；
  · **黑名单**（解读路径，禁读）：scripts/ 下其余全部模块；
  · 判定按「源码里出现案例库字面路径或 expected 取数」，纯静态、零依赖。

    python dev_tools/check_case_isolation.py
    python dev_tools/check_case_isolation.py --selftest   # 负例：证明本器抓得住
"""
from __future__ import annotations

import re
import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DISC = Path(__file__).resolve().parents[1]
SCRIPTS = DISC / "scripts"

# 允许读案例库的文件（评测层）；其余 scripts/*.py 一律视为解读路径
ALLOWED = {"evaluate.py", "case_runner.py", "build_portal_assets.py"}
# 案例库/期望值的字面痕迹
FORBIDDEN = re.compile(
    r"data/cases|cases/[a-z_]*cases|classical_cases|eval_holdout|eval_tune|eval_all"
    r"|case_splits|\[\s*[\"']expected[\"']\s*\]|\.get\(\s*[\"']expected[\"']")


def scan() -> list[str]:
    problems: list[str] = []
    if not SCRIPTS.exists():
        return [f"目录不存在：{SCRIPTS}"]
    for p in sorted(SCRIPTS.rglob("*.py")):
        if p.name in ALLOWED or "__pycache__" in p.parts:
            continue
        body = p.read_text(encoding="utf-8", errors="replace")
        for n, line in enumerate(body.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue          # 注释里讨论案例库不算触达
            if FORBIDDEN.search(stripped):
                problems.append(f"{p.relative_to(DISC)}:{n} 解读路径触达案例库 → {stripped[:80]}")
    return problems


def selftest(problems: list[str]) -> None:
    """负例：在解读路径造一个读案例库的文件，本器必须抓到并清零后不留痕。"""
    tmp = SCRIPTS / "_selftest_isolation_leak.py"
    tmp.write_text('CASES = "data/cases/classical_cases.json"\n'
                   'EXPECT = cases[0]["expected"]\n', encoding="utf-8")
    try:
        got = scan()
        hits = [g for g in got if "_selftest_isolation_leak.py" in g]
        if len(hits) < 2:
            problems.append(f"负例自证失效：造的 2 处泄漏只抓到 {len(hits)} 处")
    finally:
        tmp.unlink(missing_ok=True)
    if any("_selftest_isolation_leak" in g for g in scan()):
        problems.append("负例样本未清理干净")


def main() -> int:
    _ap = argparse.ArgumentParser(description="check_case_isolation：--selftest 负例自证开关（§三）")
    _ap.add_argument("--selftest", action="store_true", help="负例自证")
    args = _ap.parse_args()
    if args.selftest:
        base = scan()
        sink: list[str] = []
        selftest(sink)
        for s in sink:
            print(f"  × {s}")
        print(f"  [selftest] 负例已跑（{'抓到' if not sink else '失效'}）")
        if sink:
            return 1
    problems = scan()
    n_files = len([p for p in SCRIPTS.rglob("*.py")
                   if p.name not in ALLOWED and "__pycache__" not in p.parts])
    print(f"{DISC.name}：检视解读路径 {n_files} 个模块，{len(problems)} 处触达案例库")
    if n_files == 0:
        print("× 0 个模块被检视——本器等于没跑，不判通过")
        return 1
    for x in problems:
        print(f"  × {x}")
    if not problems:
        print(f"  √ 案例库只由评测层（{', '.join(sorted(ALLOWED))}）读取")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
