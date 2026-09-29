# -*- coding: utf-8 -*-
"""仓库级案例对齐分一览：转发各科 evaluate，分集合打印，不写第二套给分逻辑。

  python tools/eval.py                 # 六爻 tune + holdout
  python tools/eval.py --split all
  python tools/eval.py --full          # 加六爻外部集（wikisource / yingqi）

分数是古籍案例对齐分，不是现实预测命中率（AGENTS.md 铁律三）。
评分框架唯一实现见 core/yishu_core/eval.py。

注：命科（ming）是机械推演，**没有案例对齐评测**（机械回归见
`disciplines/ming/tools/regression.py`），转发时按「无 evaluate.py」跳过、不计失败。
默认只跑 tune+holdout；`--split all` 会把已排除案例（ZS021–025，无卦名）一并送入，
触发引擎报错并返回非零——那是刻意保留的体检信号，不是默认路径。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.runtime import utf8_subprocess_env  # noqa: E402

DISCIPLINES = ("liuyao", "ming")


def run_eval(disc: str, split: str, *, verbose: bool = False) -> tuple[int, str]:
    script = ROOT / "disciplines" / disc / "scripts" / "evaluate.py"
    if not script.exists():
        # 无案例对齐评测的学科（如 ming 机械推演）不列为失败，只提示。
        return 0, f"{disc}: 无 evaluate.py（无案例对齐评测，机械回归见 disciplines/{disc}/tools/regression.py）"
    cmd = [sys.executable, str(script), "--split", split]
    if verbose:
        cmd.append("--verbose")
    try:
        p = subprocess.run(
            cmd,
            cwd=ROOT / "disciplines" / disc,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
            env=utf8_subprocess_env(),
        )
    except subprocess.TimeoutExpired:
        return 1, f"{disc}/{split}: 超时"
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="易·仓库级古籍案例对齐分一览")
    ap.add_argument("--discipline", nargs="*", choices=list(DISCIPLINES),
                    help="限定学科（缺省全部）")
    ap.add_argument("--split", default=None,
                    help="传给各科 evaluate 的 --split（缺省 tune+holdout）")
    ap.add_argument("--full", action="store_true",
                    help="六爻额外跑外部集（wikisource_holdout/yingqi_holdout）")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    discs = tuple(args.discipline) if args.discipline else DISCIPLINES
    failures = 0
    for disc in discs:
        splits = [args.split] if args.split else ["tune", "holdout"]
        if args.full and disc == "liuyao":
            splits = splits + ["wikisource_holdout", "yingqi_holdout"]
        for split in splits:
            print(f"\n=== {disc} · {split} ===")
            code, out = run_eval(disc, split, verbose=args.verbose)
            print(out.rstrip())
            if code != 0:
                failures += 1
                print(f"!! {disc}/{split} 退出码 {code}")

    print("\n分数含义：与古籍案例要点的一致性，不代表现实预测命中率。")
    if failures:
        print(f"eval 失败 {failures} 项。")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
