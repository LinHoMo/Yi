# -*- coding: utf-8 -*-
"""一条命令跑完全部质量门：`python dev_tools/check.py [--only eval,golden]`

  python dev_tools/check.py            # 全部检查
  python dev_tools/check.py --fast     # 跳过案例评测
  python dev_tools/check.py --raise    # 把本次实测值写回基线（确认改进后才用）

门槛设计（见 AGENTS.md §四）：
  · 四段管线冒烟、金标准指纹 —— 必须全绿，任何回退即失败
  · tune/holdout 对齐分 —— **只准前进不准后退**：与 BASELINE 比较，低于基线即失败。
    基线是首次全绿时的实测值，不是"理想值"；改进后用 --raise 抬上去。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]          # 学科根：disciplines/meihua
CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.runtime import force_utf8_stdio  # noqa: E402

BASELINE_FILE = DISC / "dev_tools" / "check_baseline.json"

BASELINE = {
    "smoke": 5,          # 四段管线冒烟有产出数（最低 5；现跑 6，含多爻动 manual）
    # 100.0 是「规则表自洽回归线」，不是能力线：relation/sheng_ti/ke_ti/timing 四项
    # expected 与引擎同源（见 data/cases/meihua_cases.json#_meta._provenance 与
    # docs/EVAL-AUDIT.md）。此门只防「查表/生克管线被改坏」。
    "tune": 100.0,       # 古籍对齐分 strict，n=10（参与过调参）
    "holdout": 100.0,    # 古籍对齐分 strict，n=13（未参与调参；原注释写 n=8 已过期）。
                         # n<20 按 docs/EVAL-AUDIT.md 只报命中数，不报百分比。
}

PATTERNS = {
    "smoke": r"有产出:\s*(\d+)",
}


def run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=str(DISC), capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def measure(name: str, out: str) -> float | None:
    pat = PATTERNS.get(name)
    if not pat:
        return None
    m = re.search(pat, out)
    return float(m.group(1)) if m else None


def eval_metrics(split: str) -> dict:
    """跑一个集合，返回 {avg, n}。落盘文件带新鲜度守卫，防旧文件冒充本次结果。"""
    import time
    path = DISC / "data" / "cases" / f"eval_{split}.json"
    started = time.time()
    if path.exists():
        path.unlink()
    rc, out = run([sys.executable, "scripts/evaluate.py", "--split", split, "--save"])
    if rc != 0:
        return {"error": "evaluate.py 退出码 %d：%s" % (rc, " ".join(out.split())[-400:])}
    if not path.exists() or path.stat().st_mtime < started:
        return {"error": "评测未产出新文件（未落盘或路径不对）"}
    data = json.loads(path.read_text(encoding="utf-8"))
    strict = data["results"]
    return {"avg": strict["avg"], "n": strict.get("n"), "rc": rc}


def version_report() -> list[str]:
    """返回不一致项。版本唯一真值源是 yishu_core.__version__。"""
    import yishu_core
    problems = [f"版本号不合语义：{yishu_core.__version__}"] if not re.match(
        r"^\d+\.\d+\.\d+$", yishu_core.__version__) else []
    # 不引 tomllib/tomli：仓库零第三方依赖，用目标行正则即可（字段是项目自己维护的）
    text = (CORE.parent / "pyproject.toml").read_text(encoding="utf-8")
    m_name = re.search(r'^name\s*=\s*"([^"]+)"', text, re.M)
    if not m_name or m_name.group(1) != "yishu-core":
        problems.append(f"仓库根 pyproject 包名是 {m_name.group(1) if m_name else '?'}，应为 yishu-core")
    if re.search(r'^version\s*=\s*"', text, re.M):
        problems.append("pyproject [project] 里又写了字面 version，应改走 dynamic 从 yishu_core 取")
    if 'dynamic = ["version"]' not in text:
        problems.append("pyproject [project].dynamic 未包含 version")
    return problems


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="梅花易数质量门")
    ap.add_argument("--only", nargs="*", help="限定检查项")
    ap.add_argument("--fast", action="store_true", help="跳过案例评测（tune/holdout）")
    ap.add_argument("--raise", dest="raise_baseline", action="store_true",
                    help="以本次实测覆盖基线（仅在确认改进后使用）")
    args = ap.parse_args()

    baseline = dict(BASELINE)
    if BASELINE_FILE.exists():
        baseline.update(json.loads(BASELINE_FILE.read_text(encoding="utf-8")))

    measured: dict[str, float] = {}
    failures: list[str] = []

    def gate(name: str, value: float | None, *, minimum: float = 0.0, label: str, raw: str = ""):
        if value is None:
            failures.append(f"{label}: 未能从输出取到指标")
            print(f"  × {label:<34s} 取数失败")
            return
        ok = value >= minimum - 1e-9
        measured[name] = value
        mark = "√" if ok else "×"
        print(f"  {mark} {label:<34s} {value:g} (基线 ≥{minimum:g})")
        if not ok:
            failures.append(f"{label} {value:g} 劣于基线")
            print(raw[-1500:])

    selected = set(args.only or ["version", "golden", "smoke", "eval"])

    if "version" in selected:
        import yishu_core
        print(f"\n[0] 版本一致性（唯一真值源 yishu_core.__version__ = {yishu_core.__version__}）")
        vproblems = version_report()
        for v in vproblems:
            print(f"  × {v}")
        if not vproblems:
            print("  √ 全项目统一 v" + str(yishu_core.__version__) + "，无第二处版本号")
        failures.extend(vproblems)

    if "golden" in selected:
        print("\n[1] 金标准指纹（行为漂移看门狗）")
        rc, out = run([sys.executable, "dev_tools/golden.py"])
        d = re.search(r"指纹 ([0-9a-f]{16})", out)
        print(f"  {'√' if rc == 0 else '×'} 案例指纹 "
              f"{d.group(1) if d else '?'} "
              f"{'与基线一致' if rc == 0 else '— 行为已漂移，改的是不是你要改的？'}")
        if rc != 0:
            failures.append("金标准指纹与基线不一致")

    if "smoke" in selected:
        print("\n[2] 四段管线产出冒烟（只验有无产出）")
        rc, out = run([sys.executable, "scripts/smoke_test.py"])
        gate("smoke", measure("smoke", out), minimum=baseline["smoke"],
             label="管线有产出数", raw=out)

    if "eval" in selected and not args.fast:
        print("\n[3] 古籍案例对齐分（非现实预测命中率）")
        for split in ("tune", "holdout"):
            m = eval_metrics(split)
            if m.get("error"):
                failures.append(f"{split} 评测未跑成")
                print(f"  × {split} 评测失败：{m['error'][:300]}")
                continue
            gate(split, m.get("avg"), minimum=baseline[split], label=f"{split} 对齐分 %")

    print("\n" + "=" * 62)
    if failures:
        print("质量门未通过：")
        for f in failures:
            print(f"  · {f}")
        return 1

    if args.raise_baseline:
        new = dict(BASELINE)
        new.update({k: v for k, v in measured.items()})
        BASELINE_FILE.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
        print(f"基线已抬升 → {BASELINE_FILE}")
        print(json.dumps(new, ensure_ascii=False))
        return 0

    print("质量门全部通过（或不低于基线）。")
    print("分数含义：与古籍案例要点的一致性，不代表现实预测命中率。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
