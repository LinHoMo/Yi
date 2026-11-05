# -*- coding: utf-8 -*-
"""案例库隔离门：解读/推演路径不得触达 `data/cases/`（评测层专用）。

一旦解读层读到 expected，对齐分就可被动 inflate 而门全绿，故为 P0 禁边。
按科分两档：`<科>/eval/` 已建走物理隔离档（eval/ 必须有实现，原 scripts/ 同名兼容 shim 已于 521 批删除）；
未建走白名单档。判据是静态扫案例库字面路径或 expected 取数。

扫描面：scripts/、engine/、core/、data/ 下的 .py；eval/ 与 dev_tools/ 允许读案例库故不扫，
内核 eval.py 同语义豁免。含 scripts/ 与 core/ 两处负例自证。

    python dev_tools/check_case_isolation.py [--selftest]
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
EVAL = DISC / "eval"

# 评测实现文件名（两档共用）；该科 eval/ 里已有实现即走物理隔离档
WHITELIST = {"evaluate.py", "case_runner.py", "build_portal_assets.py"}
PHYSICAL = (EVAL / "evaluate.py").is_file() or (EVAL / "case_runner.py").is_file()
ALLOWED: set[str] = set() if PHYSICAL else set(WHITELIST)
# 交付路径扫描面：scripts/ 与 engine/ 之外，core/ 和 data/ 的 .py 同样不许触达案例库。
# eval/ 与 dev_tools/ 不扫——那两处本就是评测/门禁层，按铁律二允许读案例库。
SCAN_ROOTS = (SCRIPTS, DISC / "engine", DISC / "core", DISC / "data")
SKIP_NAMES = ALLOWED | {"eval.py"}  # 内核里的评测工具，与 eval/ 同语义
# 案例库/期望值的字面痕迹
FORBIDDEN = re.compile(
    r"data/cases|cases/[a-z_]*cases|classical_cases|eval_holdout|eval_tune|eval_all"
    r"|case_splits|case_library|source_quote"
    r"|\[\s*[\"']expected[\"']\s*\]|\.get\(\s*[\"']expected[\"']")


def scan() -> list[str]:
    problems: list[str] = []
    if not SCRIPTS.exists():
        return [f"目录不存在：{SCRIPTS}"]
    # 正面断言：物理隔离档下，案例装载/评分的真实实现必须在 eval/
    if PHYSICAL:
        required = ["evaluate.py"]
        if (DISC / "scripts" / "case_runner.py").exists() or (EVAL / "case_runner.py").exists():
            required.append("case_runner.py")
        for name in required:
            if not (EVAL / name).is_file():
                problems.append(f"评测实现不在 eval/{name}——物理搬迁缺失，scripts/ 里的 shim 不能当实现")
    # 第五百零八批升格：engine/ 与 engine/classical/ 已移出 scripts/；交付路径扫描面必须跟着扩，
    # 否则搬出去的文件既不在本门判据内，也没人接手——隔离门就成了「扫了剩下的那部分」。
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*.py")):
            if p.name in SKIP_NAMES or "__pycache__" in p.parts:
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
    # 扩面负例：core/ 下的案例库触达同样必须判红（不能只守 scripts/）
    core_probe = DISC / "core" / "_selftest_isolation_core_leak.py"
    if core_probe.parent.is_dir():
        core_probe.write_text('CASES = "case_library.md"\n', encoding="utf-8")
        try:
            got = scan()
            if not any("_selftest_isolation_core_leak.py" in g for g in got):
                problems.append("负例自证失效：core/ 里的案例库触达未被抓到")
        finally:
            core_probe.unlink(missing_ok=True)
    if PHYSICAL:
        # 物理隔离档的正面断言也要有负例：把 EVAL 指到空目录，必须判红
        global EVAL
        old = EVAL
        import tempfile
        try:
            with tempfile.TemporaryDirectory() as td:
                EVAL = Path(td)
                got = scan()
        finally:
            EVAL = old
        if not any("评测实现不在 eval/" in g for g in got):
            problems.append("负例自证失效：eval/ 实现缺失未被抓到")


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
    n_files = len([p for root in SCAN_ROOTS if root.exists()
                   for p in root.rglob("*.py")
                   if p.name not in SKIP_NAMES and "__pycache__" not in p.parts])
    print(f"{DISC.name}：检视解读路径 {n_files} 个模块，{len(problems)} 处触达案例库")
    if n_files == 0:
        print("× 0 个模块被检视——本器等于没跑，不判通过")
        return 1
    for x in problems:
        print(f"  × {x}")
    if not problems:
        if PHYSICAL:
            impl = sorted(p.name for p in EVAL.glob("*.py") if p.name in WHITELIST)
            print(f"  √ 物理隔离档：案例库只由 eval/（{', '.join(impl)}）读取；scripts/ 为纯 re-export 交付路径")
        else:
            print(f"  √ 白名单档：案例库只由脚本层（{', '.join(sorted(ALLOWED))}）读取；物理搬迁待办")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
