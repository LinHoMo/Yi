# -*- coding: utf-8 -*-
"""[23] 输出确定性门：同一输入在**任何进程**里必须产出同一份引擎结论。

起因（第一百二十九批）：金标准想加"conclusion 全字段哈希"，capture 之后复跑 verify
发现同一段代码两次跑出不同指纹——差异在 `core/yishu_core/conflict_resolution.py` 的
`'、'.join(consistent_roles & useful_set)`：集合迭代序随 PYTHONHASHSEED 每进程随机。
修好之后必须有人盯着它回来，因为这类 bug 的特征是**平时看不出来**：单次运行永远自洽，
只有换进程才变；而门禁若只在一只进程里跑，就永远认为它是好的。

两层，缺一不可：
1. **行为层**：`dev_tools/golden.py verify` 在三个不同 `PYTHONHASHSEED` 子进程里跑，
   三次的机械/措辞 digest 必须完全相同且都判通过。任一分歧 ⇒ 判红并点名是哪个种子，
   并贴出该次的逐行 diff（"随机漂移"本身不是线索，行与字段才是）。
2. **静态层**：扫 `scripts/` 与 `core/` 里"把集合直接 join 进字符串"的写法
   （`join(x & y)`／`join({...})`／`join(set(...))`／`join(x - y)`），命中即点名到行。
   本项按 2026-10-12 实测"两科 0 处命中"才敢做成硬门；若将来出现正当用法，
   须在此登记例外并附出处，不许静默放宽。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
for _p in (str(DISC / "core"),):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.runtime import force_utf8_stdio  # noqa: E402

SEEDS = ("0", "7", "999")
SCAN_DIRS = (DISC / "scripts", DISC / "core")
SET_JOIN_RE = re.compile(r"""\.join\(\s*(?:[^()]*\s[&\-]\s[^()]*|\{\s*[^}]*\}|set\()""", re.X)


def scan_static(roots) -> tuple[list[str], int]:
    hits: list[str] = []
    n_files = 0
    for root in roots:
        for p in sorted(Path(root).rglob("*.py")):
            n_files += 1
            try:
                lines = p.read_text(encoding="utf-8").splitlines()
            except Exception as exc:
                hits.append(f"{p.name}: 读取失败 {type(exc).__name__}")
                continue
            for i, line in enumerate(lines, 1):
                if line.lstrip().startswith("#"):
                    continue
                if SET_JOIN_RE.search(line):
                    try:
                        rel = str(p.relative_to(DISC))
                    except ValueError:
                        rel = p.name
                    hits.append(f"{rel}:{i}: {line.strip()[:88]}")
    return hits, n_files


def run_seed(seed: str) -> tuple[int, str]:
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = seed
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, "dev_tools/golden.py", "verify"],
                       cwd=str(DISC), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, timeout=900)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def digest_of(out: str) -> str:
    m = re.search(r"机械 ([0-9a-f]{16})｜措辞 ([0-9a-f]{16})", out)
    return m.group(0) if m else ""


def negative_selftest(problems: list[str]) -> None:
    """三式：①顺序变了 digest 必须变（证明行为层真在比内容而非比时间戳）；
    ②人造集合 join 必须被静态层抓到；③确定性写法不得被误抓。夹具只落临时目录（铁律二）。"""
    dig = lambda x: hashlib.sha256(json.dumps(x, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
    if dig(["印", "财", "官杀"]) == dig(["官杀", "财", "印"]):
        problems.append("负例自证失效：顺序变了 digest 却不变——行为层比的是无关形状")
    with tempfile.TemporaryDirectory(prefix="det_selftest_") as td:
        tmp = Path(td) / "_det_selftest_tmp.py"
        tmp.write_text("a = '、'.join(roles & useful_set)\n"
                       "b = '、'.join(r for r in useful if r in roles)\n", encoding="utf-8")
        hits, n = scan_static([Path(td)])
    if n == 0:
        problems.append("负例自证失效：静态层在临时夹具目录扫到 0 个文件（等于没扫）")
    if not any("_det_selftest_tmp.py:1" in h for h in hits):
        problems.append(f"负例自证失效：人造集合 join 没被抓到 → {hits}")
    if any("_det_selftest_tmp.py:2" in h for h in hits):
        problems.append("负例自证假阳性：确定性写法（按原序取交集）被静态层误抓")


def main() -> int:
    force_utf8_stdio()
    problems: list[str] = []

    hits, n_files = scan_static(SCAN_DIRS)
    if n_files == 0:
        print(f"× 静态层 0 个文件可扫（{SCAN_DIRS}）——本器等于没跑，不判通过")
        return 1
    _ap = argparse.ArgumentParser(description="check_determinism：--selftest 负例自证开关（§三）")
    _ap.add_argument("--selftest", action="store_true", help="负例自证")
    args = _ap.parse_args()
    if args.selftest:
        negative_selftest(problems)
        print("  [selftest] 负例已跑（顺序变更必被 digest 认出 / 集合 join 必被抓 / 确定性写法不误伤）")

    print(f"静态层：扫 {n_files} 个文件，集合直接 join 命中 {len(hits)} 处")
    for h in hits:
        problems.append("静态层命中（集合迭代序随进程随机，须改为显式序）：" + h)

    digests: list[str] = []
    for seed in SEEDS:
        try:
            rc, out = run_seed(seed)
        except Exception as exc:
            print(f"× seed={seed} 子进程未能跑成 {type(exc).__name__}: {str(exc)[:120]}")
            return 1
        dg = digest_of(out)
        print(f"行为层 seed={seed}：rc={rc}｜{dg or '壳没交出 digest 形状'}")
        if rc != 0 or not dg:
            for line in out.splitlines():
                if line.strip():
                    print("    " + line.strip())
            problems.append(f"seed={seed}：金标准未通过或没交出确当的 digest 形状（rc={rc}）")
        digests.append(dg)
    uniq = {d for d in digests if d}
    if len(uniq) > 1:
        bad = [s for s, d in zip(SEEDS, digests) if d != digests[0]]
        problems.append(
            f"跨进程 digest 不一致（以 seed={SEEDS[0]} 为参照，{bad} 漂移）"
            "＝同输入不同输出的引擎非确定性；这种看门狗会随机报警，也会随机漏报")

    for x in problems:
        print("× " + x)
    if problems:
        return 1
    print(f"√ 三个 hash seed 下 digest 全同（{digests[0]}），静态层 {n_files} 文件零集合 join")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
