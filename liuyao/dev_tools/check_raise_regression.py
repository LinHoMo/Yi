# -*- coding: utf-8 -*-
"""--raise 合并基回归守卫（第两百四十四批）——241 修的病不许无声复发。

背景（241 批）：两科 check.py 的 --raise 曾以代码字面 BASELINE 为合并基写盘，
`--only/--fast` 部分跑会把盘上历史抬线整段丢弃；修复＝合并基改用生效视图。
本器给修复上双层齿：
  静态钉：两科 check.py 源码必须各含其"生效视图"合并行（回改即红）；
  功能探针（六爻）：预埋 tune:99 基线覆盖 → `--raise --only version` → 键必须存活
    （备份/恢复一律 bytes——236 批行尾漂白教训的正面执行）。
负例即本器 selftest：临时回改两科合并基行 → 必须红 → 恢复归零。

    python dev_tools/check_raise_regression.py            # 守卫跑一遍（账台/月巡用）
    python dev_tools/check_raise_regression.py --selftest # 含回改负例的自检
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
ROOT = DISC.parent
BZ_CHECK = ROOT / "bazi" / "dev_tools" / "check.py"
LU_CHECK = DISC / "dev_tools" / "check.py"
LU_BASE = DISC / "dev_tools" / "check_baseline.json"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PIN_LU = "new = dict(baseline)"       # 241 修复行（六爻）
PIN_BZ = "new = dict(_effective_baseline())"  # 241 修复行（八字）


def static_pins() -> list:
    bad = []
    if PIN_LU not in LU_CHECK.read_text(encoding="utf-8"):
        bad.append("六爻 --raise 合并基回改成了字面默认（241 病复发）")
    if PIN_BZ not in BZ_CHECK.read_text(encoding="utf-8"):
        bad.append("八字 --raise 合并基回改成了字面默认（241 病复发）")
    return bad


def functional_probe() -> list:
    """六爻：预埋历史抬升键 → 部分跑 --raise → 键必须存活。bytes 级备份恢复。"""
    bak = LU_BASE.read_bytes() if LU_BASE.exists() else None
    try:
        LU_BASE.write_bytes(json.dumps({"tune": 99.0}, ensure_ascii=False).encode("utf-8"))
        r = subprocess.run([sys.executable, "-X", "utf8", str(LU_CHECK), "--raise", "--only", "version"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=600, cwd=str(DISC))
        if r.returncode != 0:
            return [f"探针运行失败 rc={r.returncode}: {(r.stderr or r.stdout)[-120:]}"]
        data = json.loads(LU_BASE.read_text(encoding="utf-8"))
        if data.get("tune") != 99.0:
            return ["部分跑 --raise 抹掉了历史抬升键（tune:99 丢失）——241 病复发"]
    finally:
        if bak is not None:
            LU_BASE.write_bytes(bak)
        elif LU_BASE.exists():
            LU_BASE.unlink()
    return []


def run_all() -> list:
    return static_pins() + functional_probe()


def selftest() -> int:
    fails = []
    # 负例：临时回改两科合并基行 → static_pins 必须各红 → 恢复归零（bytes 级）
    targets = [(LU_CHECK, PIN_LU, "new = dict(BASELINE)"),
               (BZ_CHECK, PIN_BZ, "new = dict(BASELINE)")]
    for path, good, evil in targets:
        bak = path.read_bytes()
        try:
            s = bak.decode("utf-8")
            if good not in s:
                fails.append(f"{path.name}: 守卫钉的行本就不在（前提崩）")
                continue
            path.write_bytes(s.replace(good, evil, 1).encode("utf-8"))
            if not static_pins():
                fails.append(f"{path.name} 回改未被 static_pins 抓到（无牙）")
        finally:
            path.write_bytes(bak)
    if static_pins():
        fails.append("恢复后静态钉仍红：" + "; ".join(static_pins()))
    bad = functional_probe()
    if bad:
        fails.append("恢复后功能探针仍红：" + "; ".join(bad))
    print("√ selftest：双科回改负例均被抓、恢复后静+动全净" if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="--raise 合并基回归守卫（241 病的常设齿）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    bad = run_all()
    for b in bad:
        print("× " + b)
    print("√ raise 回归守卫全净（静钉×2＋功能探针）" if not bad else "判红 %d 处" % len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
