# -*- coding: utf-8 -*-
"""学科质量门共享壳（gate kit）—— 八字·六爻两科 `dev_tools/check.py` 共用，禁止各写一份。

CONTRACT.md §四.6 要求学科门复用共享件。此前 7 科各写一份 subprocess 壳，取值互相漂移：
argv 前缀（内置 `sys.executable` 与否）、超时（无/60/120/300）、子进程环境（无 / utf8）
各不相同 —— 同一语义多份实现，正是 `AGENTS.md` §二「同类只存一份」要治的病。
本模块把实现收成一份，各科只**声明**自己的口径：

    run_step(cmd, *, cwd, timeout=None, python=False) -> (rc, 合并文本)
    measure(name, out, patterns)                      -> float | None
    eval_metrics(disc_root, split, *, model_key=None) -> dict

子进程环境一律带 `utf8_subprocess_env()`：不传则中文 Windows 上子进程按 GBK 出字节、
父进程按 UTF-8 解码，中文断言恒红（见 `yishu_core.runtime` 的说明）——那是假红，
不是被测行为有问题。口径要确定性，所以不继承调用方设置。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

from yishu_core.runtime import utf8_subprocess_env


def run_step(cmd: list[str], *, cwd, timeout: float | None = None,
             python: bool = False) -> tuple[int, str]:
    """跑一步子进程，返回 (退出码, stdout+stderr 合并文本)。

    python=True 时在 argv 前补 `sys.executable`（调用方给的是脚本相对路径）。
    """
    argv = [sys.executable, *cmd] if python else list(cmd)
    proc = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          timeout=timeout, env=utf8_subprocess_env())
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def measure(name: str, out: str, patterns: dict) -> float | None:
    """按学科的 PATTERNS 正则从门输出里取一个数值指标；取不到返回 None。"""
    pat = patterns.get(name)
    if not pat:
        return None
    m = re.search(pat, out)
    return float(m.group(1)) if m else None


def eval_metrics(split: str, *, eval_file, cwd,
                 model_key: str | None = None) -> dict:
    """跑 `scripts/evaluate.py --split <split> --save`，返回 {avg, n, rc, top1, rank}。

    `eval_file` 必须由调用方传入：内核不得知道评测落盘目录（铁律二
    「解读路径不得触达案例库」由 `tools/case_isolation_check.py` 机械守，
    内核里出现该路径字面量会直接把门判红）。

    新鲜度守卫（P0 教训）：先删上一次的落盘文件，跑完若文件不在或 mtime 早于起跑时刻，
    说明评测没产出新结果（崩溃时旧文件会冒充本次分数）→ 返回 error，不拿旧值充数。

    model_key=None 用于只出一种计分模型的学科（其 `results` 即汇总本体）；
    给 "strict" 则取 `results[model_key]`，并顺带取 `results.yingqi_discrimination` 的
    主应期命中率与平均名次（无该键的学科为 None）。
    """
    path = Path(eval_file)
    started = time.time()
    if path.exists():
        path.unlink()
    rc, out = run_step(["scripts/evaluate.py", "--split", split, "--save"],
                       cwd=cwd, python=True)
    if rc != 0:
        return {"error": "evaluate.py 退出码 %d：%s" % (rc, " ".join(out.split())[-400:])}
    if not path.exists() or path.stat().st_mtime < started:
        return {"error": "评测未产出新文件（未落盘或路径不对）"}
    results = (json.loads(path.read_text(encoding="utf-8")) or {}).get("results") or {}
    agg = results if model_key is None else (results.get(model_key) or {})
    disc = results.get("yingqi_discrimination") or {}
    return {"avg": agg.get("avg"), "n": agg.get("n"), "rc": rc,
            "top1": disc.get("top1_hit_rate"), "rank": disc.get("avg_rank_of_correct")}
