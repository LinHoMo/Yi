# -*- coding: utf-8 -*-
"""--raise 合并基回归守卫（第两百四十四批）——241 修的病不许无声复发。

背景（241 批）：两科 check.py 的 --raise 曾以代码字面 BASELINE 为合并基写盘，
`--only/--fast` 部分跑会把盘上历史抬线整段丢弃；修复＝合并基改用生效视图。
本器给修复上双层齿：
  静态钉：两科 check.py 源码必须各含其"生效视图"合并行（回改即红）；
  功能探针（六爻）：预埋 tune:99 基线覆盖 → `--raise --only version` → 键必须存活
    （备份/恢复一律 bytes——236 批行尾漂白教训的正面执行）。
负例即本器 selftest：临时回改两科合并基行 → 必须红 → 恢复归零。

**540 批补「脏基线自我延续」防线**：本器探针会往真盘 `check_baseline.json`
预埋 `tune:99`，靠 finally 恢复。540 批实证发现，一旦真盘**本来就被污染成 99**
（某次中断/夹具遗留），`bak` 读到的就是脏值，finally 会把它原样写回——于是每跑
一次探针就把污染重刷一遍；而 `check.py [5]` 拿 99 当基线，实测 97.9 便恒判红。
仓内从无 ≥98 的 tune 登记（代码默认 93.9、账台/CAPABILITY 均 97.9），故本批：
① 前置检测脏值即**拒绝把脏值当基线、不写盘**；② finally 恢复后逐字节自证；
③ selftest 加「预埋脏基线 → 必须判红且零副作用」负例。

    python dev_tools/check_raise_regression.py            # 守卫跑一遍（账台/月巡用）
    python dev_tools/check_raise_regression.py --selftest # 含回改负例与脏基线负例的自检
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
BZ_CHECK_PY = BZ_CHECK
BZ_BASE = ROOT / "bazi" / "dev_tools" / "check_baseline.json"

# 540 批：仓内 tune 的登记上限。代码默认 `BASELINE["tune"] = 93.9`，
# 账台 `liuyao.tune(97.9/64.7/1.53)` 与 CAPABILITY 均钉死 97.9（tune 集，n=20）。
# 高于此值即不属于任何在册基线，按夹具遗留污染处理。
LU_TUNE_CEILING = 98.0


def _probe_baseline_state(raw: bytes | None) -> tuple[float | None, bool]:
    """读真盘本地基线，返回 (tune, 是否超出仓内登记上限)。解析失败按无覆盖处理。"""
    if raw is None:
        return None, False
    try:
        tune = float(json.loads(raw.decode("utf-8")).get("tune", 93.9))
    except (ValueError, UnicodeDecodeError, AttributeError, TypeError):
        return None, False
    return tune, tune > LU_TUNE_CEILING


def functional_probe_bazi() -> list:
    """慢档（分钟级，月巡用）：八字的病防在**另一层**——246 批两轮实探发现：
    `--fast --raise` 被八字 raise 入口守卫直接拒绝（"未取到任何对齐分，拒绝登记基线"），
    部分跑路径在八字侧本就被封。故本探针验的是**拒绝守卫**而非键存活：
    预埋 tune:100.1 → `--fast --raise` → 必 rc≠0（拒登）且文件原样未动（失败路径零副作用）。
    （顺带首验了读侧"覆盖只准抬"守卫：低于登记值的预埋会被拒——本探针换 100.1 过境。）"""
    bak = BZ_BASE.read_bytes() if BZ_BASE.exists() else None
    try:
        BZ_BASE.write_bytes(json.dumps({"tune": 100.1}, ensure_ascii=False).encode("utf-8"))
        r = subprocess.run([sys.executable, "-X", "utf8", str(BZ_CHECK_PY), "--raise", "--fast"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=1200, cwd=str(BZ_CHECK_PY.parent.parent))
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode == 0:
            return ["八字 --fast --raise 竟被接受——入口拒绝守卫失效（246 语义）"]
        if "拒绝登记基线" not in out:
            return [f"八字 rc={r.returncode} 但非因拒绝守卫，需人工定性: {out[-120:]}"]
        if not BZ_BASE.exists() or json.loads(BZ_BASE.read_text(encoding="utf-8")).get("tune") != 100.1:
            return ["八字拒绝路径动了基线文件（失败应零副作用）——异常"]
    finally:
        if bak is not None:
            BZ_BASE.write_bytes(bak)
        elif BZ_BASE.exists():
            BZ_BASE.unlink()
    return []


def static_pins() -> list:
    bad = []
    if PIN_LU not in LU_CHECK.read_text(encoding="utf-8"):
        bad.append("六爻 --raise 合并基回改成了字面默认（241 病复发）")
    if PIN_BZ not in BZ_CHECK.read_text(encoding="utf-8"):
        bad.append("八字 --raise 合并基回改成了字面默认（241 病复发）")
    return bad


def functional_probe() -> list:
    """六爻：预埋历史抬升键 → 部分跑 --raise → 键必须存活。bytes 级备份恢复。

    540 批：前置拒绝脏基线（否则 finally 会把污染值当正常 bak 写回，自我延续）；
    try 内不再 return——统一收集 bad，finally 的恢复自证才能一起返回。
    """
    bak = LU_BASE.read_bytes() if LU_BASE.exists() else None
    tune, dirty = _probe_baseline_state(bak)
    if dirty:
        return [f"真盘 check_baseline.json 的 tune={tune:g} 超出仓内登记上限 "
                f"{LU_TUNE_CEILING:g}（代码默认 93.9／账台与 CAPABILITY 均 97.9），"
                "疑为夹具遗留污染；本器拒绝把它当基线、不写盘，请先按 CHANGELOG 归位"]
    bad = []
    try:
        LU_BASE.write_bytes(json.dumps({"tune": 99.0}, ensure_ascii=False).encode("utf-8"))
        r = subprocess.run([sys.executable, "-X", "utf8", str(LU_CHECK), "--raise", "--only", "version"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=600, cwd=str(DISC))
        if r.returncode != 0:
            bad.append(f"探针运行失败 rc={r.returncode}: {(r.stderr or r.stdout)[-120:]}")
        else:
            data = json.loads(LU_BASE.read_text(encoding="utf-8"))
            if data.get("tune") != 99.0:
                bad.append("部分跑 --raise 抹掉了历史抬升键（tune:99 丢失）——241 病复发")
    finally:
        if bak is not None:
            LU_BASE.write_bytes(bak)
        elif LU_BASE.exists():
            LU_BASE.unlink()
        now = LU_BASE.read_bytes() if LU_BASE.exists() else None
        if now != bak:
            bad.append("探针恢复后真盘与备份逐字节不一致（夹具写脏真盘）")
    return bad


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

    # 540 批负例：预埋脏基线 → functional_probe 必须判红、且真盘零改动
    # （否则污染值会被 finally 当正常 bak 写回，形成自我延续）。bytes 级恢复。
    dirty_bak = LU_BASE.read_bytes() if LU_BASE.exists() else None
    try:
        LU_BASE.write_bytes(json.dumps({"tune": 99.0}, ensure_ascii=False).encode("utf-8"))
        snapshot = LU_BASE.read_bytes()
        dirty_bad = functional_probe()
        if not dirty_bad or "超出仓内登记上限" not in " ".join(dirty_bad):
            fails.append("脏基线未被 functional_probe 拦住（540 防线失效）")
        if LU_BASE.read_bytes() != snapshot:
            fails.append("脏基线探针动了真盘（应零副作用）")
    finally:
        if dirty_bak is not None:
            LU_BASE.write_bytes(dirty_bak)
        elif LU_BASE.exists():
            LU_BASE.unlink()

    print("√ selftest：双科回改＋脏基线负例均被抓、恢复后静+动全净"
          if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="--raise 合并基回归守卫（241 病的常设齿）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--with-bazi", action="store_true",
                    help="加八字慢档探针（分钟级，月巡第⑤步用；周度只跑秒级形）")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    bad = static_pins() + functional_probe()
    if args.with_bazi:
        bad += functional_probe_bazi()
    for b in bad:
        print("× " + b)
    scope = "静钉×2＋六爻探针＋八字慢档" if args.with_bazi else "静钉×2＋功能探针（秒级形）"
    print(("√ raise 回归守卫全净（%s）" % scope) if not bad else "判红 %d 处" % len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
