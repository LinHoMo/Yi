# -*- coding: utf-8 -*-
"""仓库级案例对齐分一览：转发各科 evaluate，分集合打印，不写第二套给分逻辑。

  python tools/eval.py                 # 各科 tune + holdout
  python tools/eval.py --split all
  python tools/eval.py --full          # 加外部集（各科见 EXTRA_SPLITS）
  python tools/eval.py --allow-missing # 显式豁免"该科没有 evaluate.py"（默认判败）

分数是古籍案例对齐分，不是现实预测命中率（AGENTS.md 铁律三）。
评分框架唯一实现见 core/yishu_core/eval.py。

学科清单唯一真值源：`core/yishu_core/report/request.py::DISCIPLINES`。
2026-10-09 之前这里另存一份写死的 `("liuyao", "ming")`，与 `tools/check.py` 里的
第二份、`build_web.py` 的第三份并列——正是 AGENTS.md §二「同一批表在三个文件里
各存一份」的同一种病。

**缺 evaluate.py 默认判败**（2026-10-09 修）：旧实现 `return 0, "无 evaluate.py"`
把"评测器不存在"记成通过，于是**把某科的评测器删掉也能让根门 [7d] 绿**。
确实有意不评的学科请显式 `--allow-missing`，让豁免出现在命令行上而不是消失在代码里。
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from yishu_core.report.request import DISCIPLINES  # noqa: E402  学科清单唯一真值源
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.runtime import utf8_subprocess_env  # noqa: E402

# 默认集合：每科都必须出这两个分数（根门 [7d] 按此断言，缺一即判红）。
DEFAULT_SPLITS = ("tune", "holdout")
# `--full` 追加的外部独立集（**永不并入默认均分**）。按学科登记：evaluate.py 的
# `--split` 是 argparse choices，名字给错就直接退出码 2，所以这张表必须与各科对齐。
EXTRA_SPLITS = {
    "liuyao": ("wikisource_holdout", "yingqi_holdout"),
    "ming": ("external_holdout",),
}

# 分数行：`=== tune [strict] 平均分 = 96.8%  (n=20，最低 84.3，最高 100.0) ===`
SCORE_RE = re.compile(r"===\s*(\w+)\s*\[strict\]\s*平均分\s*=\s*([\d.]+)%\s*\(n=(\d+)")


def run_eval(disc: str, split: str, *, verbose: bool = False,
             allow_missing: bool = False) -> tuple[int, str]:
    script = ROOT / "disciplines" / disc / "scripts" / "evaluate.py"
    if not script.exists():
        msg = (f"{disc}/{split}: 没有 disciplines/{disc}/scripts/evaluate.py"
               "（案例对齐评测器不在位——机械回归见 "
               f"disciplines/{disc}/dev_tools/；要豁免这条判败须显式 --allow-missing）")
        # 判败（退出码 1）而不是判胜：删掉评测器 ≠ 评测通过。
        return (0, f"{disc}/{split}: 显式豁免：无 evaluate.py") if allow_missing else (1, msg)
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
                    help="限定学科（缺省全部；学科清单取自 request.DISCIPLINES）")
    ap.add_argument("--split", default=None,
                    help="传给各科 evaluate 的 --split（缺省 tune+holdout）")
    ap.add_argument("--full", action="store_true",
                    help="额外跑外部集（按 EXTRA_SPLITS 登记；永不并入默认均分）")
    ap.add_argument("--allow-missing", action="store_true",
                    help="显式豁免「该科没有 evaluate.py」（默认判败：删掉评测器不等于通过）")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    discs = tuple(args.discipline) if args.discipline else tuple(DISCIPLINES)
    failures = 0
    scored: list[str] = []
    for disc in discs:
        splits = [args.split] if args.split else list(DEFAULT_SPLITS)
        if args.full:
            splits = splits + list(EXTRA_SPLITS.get(disc, ()))
        elif args.split is None and disc not in EXTRA_SPLITS:
            print(f"! {disc}：EXTRA_SPLITS 未登记外部集（--full 时不会追加任何外部集，"
                  "这不是失败项，但别把它当「覆盖齐全」）")
        for split in splits:
            print(f"\n=== {disc} · {split} ===")
            code, out = run_eval(disc, split, verbose=args.verbose,
                                 allow_missing=args.allow_missing)
            print(out.rstrip())
            if code != 0:
                failures += 1
                print(f"!! {disc}/{split} 退出码 {code}")
                continue
            m = SCORE_RE.search(out or "")
            if "显式豁免：无 evaluate.py" in (out or ""):
                continue          # --allow-missing 的豁免行本来就不可能有分数，别重复计败
            if m and args.split is None and split in DEFAULT_SPLITS:
                scored.append(f"{disc}/{split} {m.group(2)}% (n={m.group(3)})")
            elif not m:
                # 退出 0 却没有分数行：评测器被改成"什么都不算"也长这样。
                failures += 1
                print(f"!! {disc}/{split}：退出码 0 但输出里没有「[strict] 平均分」行——"
                      "没有读数的运行不能作为评测结果")

    print("\n分数含义：与古籍案例要点的一致性，不代表现实预测命中率。")
    if scored and not failures:
        print("默认集合读数：" + "；".join(scored))
    if failures:
        print(f"eval 失败 {failures} 项。")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
