# -*- coding: utf-8 -*-
"""案例库隔离门：解读/推演路径不得触达 `data/cases/`（评测层专用）。

为什么需要它（2026-10-10）：`core/yishu_core/gate_kit.py` 头注曾写
「解读路径不得触达案例库」由 tools/case_isolation_check.py 机械守（该脚本已随扁平化删除），
那段时间这句话是空话——本器就是补上的那道门。

这条纪律为什么是 P0：一旦 narrate/render/step 层读到 `expected`，
「引擎输出 vs 古籍要点」就不再是两个独立量，对齐分可以被动inflate 而门禁全绿——
正是评测方法学 §三.4 与 SKILL.md 铁律所禁的"用引擎输出反推期望"的反方向风险。

口径（第三百五十六批起按科分两档，不再是单一白名单）：
  · **物理隔离档**（`<科>/eval/` 已建）：实现层 `eval/` 下的 case_runner / evaluate /
    build_portal_assets 允许读案例库；`scripts/` 下一律不给目录白名单——同名文件只准
    是纯 re-export shim，凡出现案例库字面路径 / expected 取数即红；`eval/` 内必须
    存在 evaluate.py，若该科原本有 case_runner.py 则它也必须存在于 `eval/`
    （正面断言，防止"宣称搬了其实没搬"）。
  · **白名单档**（尚未物理搬迁的科）：沿用 346 批口径，`scripts/` 下 evaluate.py /
    case_runner.py / build_portal_assets.py 允许读案例库，其余解读模块禁读。
  两档都按「源码里出现案例库字面路径或 expected 取数」判定，纯静态、零依赖。

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
EVAL = DISC / "eval"

# 评测实现文件名（两档共用）；该科 eval/ 里已有实现即走物理隔离档
WHITELIST = {"evaluate.py", "case_runner.py", "build_portal_assets.py"}
PHYSICAL = (EVAL / "evaluate.py").is_file() or (EVAL / "case_runner.py").is_file()
ALLOWED: set[str] = set() if PHYSICAL else set(WHITELIST)
# 案例库/期望值的字面痕迹
FORBIDDEN = re.compile(
    r"data/cases|cases/[a-z_]*cases|classical_cases|eval_holdout|eval_tune|eval_all"
    r"|case_splits|\[\s*[\"']expected[\"']\s*\]|\.get\(\s*[\"']expected[\"']")


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
    n_files = len([p for p in SCRIPTS.rglob("*.py")
                   if p.name not in ALLOWED and "__pycache__" not in p.parts])
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
