# -*- coding: utf-8 -*-
"""器具全体检扫描器（第两百一十三批）——55 个声明 --selftest 的器具逐真跑，首次系统化基线。

背景：两科 check.py 只测**已挂闸**的门；nightly/ondemand/build 层的 20+ 器具的 selftest
从未有批次级统检（"六器 selftest 全过"历来是局部口径）。本器把声明面全扫一遍：
每个器具真跑 `--selftest`，四类归档：PASS／FAIL／NOTIMPL（文档提及但 argparse 不认——
注意 check.py 系**编排器提及子门旗标**，属提及非声明，按名豁免并具名注记）／TIMEOUT。

负例即体检本身：本器的 wired 负例＝临时损坏一器具再扫（见 --selftest 内实现）——
扫不出损坏的扫描器没有存在资格。

    python dev_tools/sweep_selftests.py                # 两科全扫（重档，夜巡/月巡用）
    python dev_tools/sweep_selftests.py --selftest     # 含注入损坏负例的自检
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
ROOT = DISC.parent

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 编排器豁免：check.py 的 docstring/循环里出现 "--selftest" 是给子门传的旗，不是自身声明。
ORCHESTRATORS = {"bazi/dev_tools/check.py", "liuyao/dev_tools/check.py"}


def declared_files():
    out = []
    mine = str(HERE / "sweep_selftests.py").replace("\\", "/")
    for d in ("bazi/dev_tools", "liuyao/dev_tools"):
        for p in sorted((ROOT / d).glob("*.py")):
            rel = str(p.relative_to(ROOT)).replace("\\", "/")
            if rel in ORCHESTRATORS or rel == mine or p.name == "sweep_selftests.py":
                continue  # 扫描器自身排除：跑自身 --selftest＝注入损坏的递归套娃（213 批实踩）
            if '"--selftest"' in p.read_text(encoding="utf-8", errors="replace"):
                out.append((rel, p))
    return out


def sweep() -> tuple:
    files = declared_files()
    npass = nfail = nnot = 0
    bad = []
    for rel, p in files:
        r = subprocess.run([sys.executable, "-X", "utf8", rel, "--selftest"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=600, cwd=str(ROOT))
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode == 2 and "unrecognized arguments: --selftest" in out:
            nnot += 1
            bad.append(("NOTIMPL", rel))
        elif r.returncode == 0:
            npass += 1
        else:
            nfail += 1
            bad.append(("FAIL(%d)" % r.returncode, rel, (out.strip().splitlines() or [""])[-1][:90]))
    return len(files), npass, nfail, nnot, bad


def selftest() -> int:
    # wired 负例：损坏一个真器具→扫描必须报 FAIL→恢复归零。
    # 注入点选择标准（213 批两轮实踩后定死）：①锚文本在 victim 中唯一且必然存在
    # （count 判 1，文案区分"缺失/多命中"）；②注入后该器 --selftest 必返非零，
    # 且不写任何入库文件（不选 strict 路径——那会污染 map json；选 selftest 开头
    # 的 fails 行：强制追加一条失败项是最小致红面）。
    victim = DISC / "dev_tools" / "governance_map.py"
    bak = victim.read_text(encoding="utf-8")
    anchor = "def selftest() -> int:\n    fails = []\n"
    c = bak.count(anchor)
    if c != 1:
        print("× 注入锚在 victim %d 命中（应为 1）——负例前提失效，判红（不许静默假绿）" % c)
        return 1
    try:
        victim.write_text(bak.replace(anchor, anchor + '    fails.append("注入损坏")  # noqa\n', 1),
                          encoding="utf-8")
        n, p, f, nt, bad = sweep()
        if f < 1 or not any("governance_map" in str(b) for b in bad):
            print("× 注入损坏未被扫出——扫描器无牙，判红")
            return 1
    finally:
        victim.write_text(bak, encoding="utf-8")
    n, p, f, nt, bad = sweep()
    if f or nt:
        print("× 恢复后仍有 FAIL/NOTIMPL：%r" % (bad,))
        return 1
    print("√ selftest：注入损坏被扫出→恢复归零；声明面 %d 器具 PASS %d（负例即体检）" % (n, p))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="器具全体检扫描器（--selftest 声明面逐真跑）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    t0 = time.time()
    n, p, f, nt, bad = sweep()
    for b in bad:
        print("× " + " ".join(str(x) for x in b))
    print("═ 全体检：声明 %d｜PASS %d｜FAIL %d｜NOTIMPL %d｜%.0fs ═" % (n, p, f, nt, time.time() - t0))
    return 1 if (f or nt) else 0


if __name__ == "__main__":
    raise SystemExit(main())
