# -*- coding: utf-8 -*-
"""House 规矩核对版（AGENTS §三 表第 1/3/5 行＋绝对路径条，第两百一十一批上门）。

四条零歧义判据（本科树内，git 口径只查 tracked 文件——scratch 未跟踪文件天然豁免）：
  A 名字不携带版本：tracked 文件名匹配 `[_-.]v\\d+(\\.\\d+)?\\.\\w+$` 或 HANDOFF 即红
    （§三：版本走 git 与 CHANGELOG，不走文件名）。
  B 绝对用户路径：.py 源码出现 `C:\\Users`／`D:\\` 等盘符路径即红——占位示例
    （`<name>`）与注释里的反面教材字面串豁免（写明"硬编码"者放过，与 [11] NEGATIVE 同法）。
  C scratch 整目录不入库：tracked 里出现 `<科>/scratch/` 即红。
  D 产物不入库：tracked 里 *.html／*.jsonl／outputs/ 即红（docs/ 样例须是 .md/.json+说明）。
本器是**勘查的固化**：211 批实测四判据全零违规后才锁 0——先证明规矩本来守着，
再把"守着"从自觉升级为断言。

    python dev_tools/check_house_conventions.py --selftest
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
ROOT = DISC.parent

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

VER_RE = re.compile(r"(?:^|[_\-.])v\d+(?:\.\d+)*\.(?:py|md|json|txt)$|HANDOFF", re.I)
ABS_RE = re.compile(r"[A-Za-z]:[\\/](?:Users|[A-Z][a-z]+[\\/])")
PLACEHOLDER = ("<name>", "yi_wt", "硬编码", "反面")


def tracked(subject: str) -> list[str]:
    r = subprocess.run(["git", "-C", str(ROOT), "ls-files", subject],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError("git ls-files 失败——门拒绝在盲状态下报绿：%s" % r.stderr[:80])
    return [l.strip() for l in r.stdout.splitlines() if l.strip()]


def check(subject: str, files: list[str]):
    bad = []
    for f in files:
        name = f.rsplit("/", 1)[-1]
        if VER_RE.search(name):
            bad.append("A 版本号文件名：" + f)
        if "/scratch/" in f or f.startswith(subject + "/scratch/"):
            bad.append("C scratch 入库：" + f)
        if f.endswith((".html", ".jsonl")) or "/outputs/" in f:
            bad.append("D 产物入库：" + f)
    for f in files:
        if not f.endswith(".py"):
            continue
        p = ROOT / f
        # 本器源码自带反例串（负例夹具）——与 [11] 对 NEGATIVE 的豁免同类：门不咬自己的齿。
        if p.resolve() == Path(__file__).resolve():
            continue
        if not p.exists():
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if ABS_RE.search(line) and not any(ph in line for ph in PLACEHOLDER):
                bad.append("B 绝对路径：%s:%s %s" % (f, i, line.strip()[:60]))
    return bad


def unit_predicates() -> list:
    fails = []
    if not (VER_RE.search("run_blind_v5.py") and VER_RE.search("HANDOFF_V8.md")):
        fails.append("A 正例未抓")
    if VER_RE.search("version_collate.py"):
        fails.append("A 误杀合法名（version 词不等于版本号尾）")
    if not ABS_RE.search('C:\\Users\\bob\\x'):
        fails.append("B 正例未抓")
    if ABS_RE.search('C:\\Users\\<name> 例') and not any(ph in 'C:\\Users\\<name> 例' for ph in PLACEHOLDER):
        fails.append("B 占位豁免未生效")
    return fails


def selftest() -> int:
    fails = unit_predicates()
    # 假路径夹具按 §三/§四.8 口径拼接：完整带扩展名的斜杠串会被 [11] 当路径声明
    neg = ["liuyao/scratch/" + "x_v2.py", "liuyao/scripts/" + "run_blind_v5.py",
           "liuyao/data/" + "out.html"]
    bad = check("liuyao", neg)
    for tag in "ACD":
        if not any(b.startswith(tag) for b in bad):
            fails.append(tag + " 集成负例未抓")
    sub = str(DISC.name)
    inj = ROOT / sub / "scripts" / "probe_house_tmp.py"
    try:
        inj.write_text('P = r"C:\\Users\\someone\\f"\n', encoding="utf-8")
        # 注入文件未 tracked——按判据语义显式并入清单，验 B 在真文件面有牙
        rows = check(sub, tracked(sub) + [sub + "/scripts/probe_house_tmp.py"])
        if not any(r.startswith("B 绝对路径：") and "probe_house_tmp" in r for r in rows):
            fails.append("B 注入负例未抓（门在路径面失明）")
    finally:
        if inj.exists():
            inj.unlink()
    rows_real = check(sub, tracked(sub))
    if rows_real:
        fails.append("本科真实违规 %d 处：%r" % (len(rows_real), rows_real[:3]))
    if fails:
        print("× selftest：" + "；".join(str(x) for x in fails))
        return 1
    print("√ selftest：四判据单元/集成/注入负例全中；本科 tracked 实查零违规")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="§三 house 规矩核对版（A 版本名/B 绝对路径/C scratch/D 产物）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    sub = str(DISC.name)
    files = tracked(sub)
    if not files:
        print("× tracked 为空——git 接线可疑，不报绿")
        return 1
    bad = check(sub, files)
    for b in bad:
        print("× " + b)
    print("%s：tracked %d 文件，house 违规 %d 处" % ("判红" if bad else "√ 通过", len(files), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
