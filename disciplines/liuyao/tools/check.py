# -*- coding: utf-8 -*-
"""一条命令跑完全部质量门：`python tools/check.py [--only eval,calendar]`

  python tools/check.py            # 全部检查
  python tools/check.py --fast     # 跳过耗时的两套案例评测
  python tools/check.py --raise    # 把当前实测值写回基线（确认改进后才用）

门槛设计（见 AGENTS.md §四）：
  · 历法自检、段落产出冒烟 —— 必须全绿，任何回退即失败
  · 思维链用例、古籍回归、tune/holdout 对齐分 —— **只准前进不准后退**：
    与 BASELINE 比较，低于基线即失败。基线是 2026-09-22 重建评分器后的实测值，
    不是"理想值"；M1/M2 修好后用 --raise 抬上去。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]          # 学科根：disciplines/liuyao
sys.path.insert(0, str(DISC / "scripts"))
from kernel_path import kernel_dir as _kernel_dir, repo_root as _repo_root  # noqa: E402
REPO = _repo_root(__file__)                          # 仓库根：含 core/ 与 disciplines/
ROOT = DISC                                          # 兼容旧变量名：脚本与数据以学科根为基准
sys.path.insert(0, str(_kernel_dir(__file__)))
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

BASELINE_FILE = ROOT / "tools" / "check_baseline.json"


def _project_header(text: str) -> dict:
    """零依赖最小 TOML 读取：只取 [project] 段内的 name/version/dynamic。

    pyproject 只被此检查用，不值得引入 tomllib/tomli 依赖（Python 3.10 兼容）。
    """
    section = None
    out: dict = {}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            section = stripped[1:stripped.rfind("]")].strip()
            continue
        if section != "project" or "=" not in stripped:
            continue
        key, _, raw = stripped.partition("=")
        key, raw = key.strip(), raw.strip()
        if key == "dynamic":
            m = re.search(r"\[([^\]]*)\]", raw)
            items = (m.group(1) if m else "").split(",")
            out[key] = [v.strip().strip('"').strip("'")
                        for v in items if v.strip()]
        elif key in ("name", "version"):
            out[key] = raw.strip('"').strip("'")
    return out

BASELINE = {
    "calendar": 16,        # 历法自检通过项数（共 16）
    "ordering": 23,        # 爻序断言通过项数（共 23）——P0 事故看门狗
    "smoke": 36,           # 有产出的分析段
    # case_03 / reg_03 的期望值原是在"卦内三位镜像"位次下标定的，P0 后失配；
    # 已按古籍理重推（坤宫兄弟土为子孙金之原神，原神动生用 ⇒ 净效应为正），
    # 不是把爻序改回去凑绿。基线随之回到 8/11。
    "chain_tests": 8,      # /12
    "regression": 11,      # /18
    # 0.0.1 批次：动爻变出支补上后"化回头生"法则首次可触发，应期名次 2.13→2.27、
    # 对齐分 −0.1/−0.4，但 top-1 持平、两套测试各多过一例。**基线下调是有意的**，
    # 理由记于 docs/CHANGELOG.md；不许无凭据下调。
    "tune": 93.7,          # 古籍对齐分 strict，n=20（参与过调参）；2026-09-26 规则修订后重锚，见 CHANGELOG
    "holdout": 78.3,       # 古籍对齐分 strict，n=12（未参与调参）
    "tune_top1": 29.4,     # 主应期命中率 %（随机基线 8.3）
    "holdout_top1": 25.0,
}
# 基准应支平均名次：越小越好，单独按上限把关
BASELINE_MAX = {"tune_rank": 2.19, "holdout_rank": 2.6}

PATTERNS = {
    "chain_tests": r"Passed:\s*(\d+)/(\d+)",
    "regression": r"总通过:\s*(\d+)/(\d+)",
    "smoke": r"有产出:\s*(\d+)",
}


def run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def measure(name: str, out: str) -> float | None:
    pat = PATTERNS.get(name)
    if not pat:
        return None
    m = re.search(pat, out)
    return float(m.group(1)) if m else None


def eval_metrics(split: str) -> dict:
    """跑一个集合，返回 {avg, top1, rank}。"""
    import time
    path = ROOT / "data" / "cases" / f"eval_{split}.json"
    # 新鲜度守卫：评测崩溃时上一次的落盘文件还在，直接读会拿旧分数冒充本次结果。
    # P0 修正中就发生过：case_runner 报错，门却报"分数一位不动"。
    started = time.time()
    if path.exists():
        path.unlink()
    rc, out = run([sys.executable, "scripts/evaluate.py", "--split", split, "--save"])
    if rc != 0:
        return {"error": "evaluate.py 退出码 %d：%s" % (rc, " ".join(out.split())[-400:])}
    if not path.exists() or path.stat().st_mtime < started:
        return {"error": "评测未产出新文件（未落盘或路径不对）"}
    data = json.loads(path.read_text(encoding="utf-8"))
    disc = data["results"].get("yingqi_discrimination") or {}
    strict = data["results"]["strict"]
    return {"avg": strict["avg"], "n": strict.get("n"), "rc": rc,
            "top1": disc.get("top1_hit_rate"), "rank": disc.get("avg_rank_of_correct")}


def version_report() -> list[str]:
    """返回不一致项。版本唯一真值源是 yishu_core.__version__。"""
    import yishu_core

    problems = [f"版本号不合语义：{yishu_core.__version__}"] if not re.match(
        r"^\d+\.\d+\.\d+$", yishu_core.__version__) else []
    proj = _project_header((REPO / "pyproject.toml").read_bytes().decode("utf-8"))
    if proj.get("name") != "yishu-core":
        problems.append(f"仓库根 pyproject 包名是 {proj.get('name')}，应为 yishu-core")
    if "version" in proj:
        problems.append(f"pyproject [project] 里又写了字面 version={proj['version']}，"
                        f"应改走 dynamic 从 yishu_core 取")
    if "version" not in proj.get("dynamic", []):
        problems.append("pyproject [project].dynamic 未包含 version")
    if (DISC / "pyproject.toml").exists():
        problems.append("学科根不该再有一份 pyproject（内核唯一发版）")

    for rel in ("assets/portal_data.json", "index.html"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        m = re.search(r'"version"\s*:\s*"([^"]+)"', text)
        if not m:
            problems.append(f"{rel} 找不到 version 字段")
        elif m.group(1) != yishu_core.__version__:
            problems.append(f"{rel} 版本是 {m.group(1)}，应为 {yishu_core.__version__}"
                            f"（跑 python scripts/build_portal_assets.py 重建）")
    return problems


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="六爻质量门")
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

    def gate(name: str, value: float | None, *, minimum: float = 0.0, maximum: float | None = None,
             label: str, raw: str = ""):
        if value is None:
            failures.append(f"{label}: 未能从输出取到指标")
            print(f"  × {label:<34s} 取数失败")
            return
        ok = value >= minimum - 1e-9 if maximum is None else value <= maximum + 1e-9
        measured[name] = value
        mark = "√" if ok else "×"
        ref = f"基线 ≥{minimum:g}" if maximum is None else f"基线 ≤{maximum:g}"
        print(f"  {mark} {label:<34s} {value:g} ({ref})")
        if not ok:
            failures.append(f"{label} {value:g} 劣于基线")
            print(raw[-1500:])

    selected = set(args.only or ["version", "calendar", "ordering", "golden", "smoke", "style",
                                 "chain_tests", "regression", "eval"])

    if "version" in selected:
        import yishu_core
        print(f"\n[0] 版本一致性（唯一真值源 yishu_core.__version__ = {yishu_core.__version__}）")
        vproblems = version_report()
        for v in vproblems:
            print(f"  × {v}")
        if not vproblems:
            print(f"  √ 全项目统一 v{yishu_core.__version__}，无第二处版本号")
        failures.extend(vproblems)

    if "calendar" in selected:
        print("\n[1] 干支历内核自检")
        rc, out = run([sys.executable, str(REPO / "core" / "yishu_core" / "calendar_check.py")])
        passed = re.search(r"自检：(\d+) 项通过，(\d+) 项失败", out)
        if passed:
            gate("calendar", float(passed.group(1)), minimum=baseline["calendar"],
                 label="自检通过项", raw=out)
        if rc != 0:
            failures.append("历法自检退出码非 0")

    if "ordering" in selected:
        print("\n[1.5] 爻序断言（自下而上唯一约定，P0 看门狗）")
        rc, out = run([sys.executable, "tools/hexagram_check.py"])
        m = re.search(r"(\d+) 项通过，(\d+) 项失败", out)
        if m:
            gate("ordering", float(m.group(1)), minimum=baseline["ordering"],
                 label="爻序断言通过数", raw=out)
        if rc != 0:
            failures.append("爻序断言未通过")

    if "golden" in selected:
        # 金标准指纹：64 卦 × 3 爻型 × 时间的排盘＋思维链＋分析层逐字段快照。
        # 基线是 data/golden/digest.json（入库），所以换机器也拦得住行为漂移——
        # 以前它只活在 gitignore 的 scratch/ 里，等于只有我这台机器有看门狗。
        print("\n[1.6] 金标准指纹（行为漂移看门狗）")
        rc, out = run([sys.executable, "tools/golden.py"])
        if "指纹" in out:
            d = re.search(r"指纹 ([0-9a-f]{16})", out)
            print(f"  {'√' if rc == 0 else '×'} 288 例指纹 "
                  f"{d.group(1) if d else '?'} "
                  f"{'与基线一致' if rc == 0 else '— 行为已漂移，改的是不是你要改的？'}")
        if rc != 0:
            failures.append("金标准指纹与基线不一致")


    if "smoke" in selected:
        print("\n[2] 分析段落产出冒烟（只验有无产出）")
        rc, out = run([sys.executable, "scripts/smoke_test.py"])
        gate("smoke", measure("smoke", out), minimum=baseline["smoke"],
             label="段落有产出数", raw=out)

    if "style" in selected:
        # 报告外观：用到的类名必须有定义。评分与金标准指纹看不见"内容对、外观散架"这一类回归。
        # （两套 CSS 合并时就散过一次：排盘报告的 .container/.cell-* 等 29 个类没了定义。）
        print("\n[2.5] 报告样式层覆盖（类名必须有定义）")
        rc, out = run([sys.executable, "tools/style_check.py"])
        for line in out.splitlines():
            if line.strip():
                print("  " + line.strip())
        if rc != 0:
            failures.append("报告里有类名没定义（样式层缺规则）")

    if "chain_tests" in selected:
        print("\n[3] 思维链用例（12 例，逐维度断言）")
        rc, out = run([sys.executable, "scripts/thinking_chain_tests.py"])
        gate("chain_tests", measure("chain_tests", out), minimum=baseline["chain_tests"],
             label="用例通过数", raw=out)

    if "regression" in selected:
        print("\n[4] 古籍回归（18 例，用神/方向/区间三维）")
        rc, out = run([sys.executable, "scripts/regression_test.py"])
        gate("regression", measure("regression", out), minimum=baseline["regression"],
             label="回归通过数", raw=out)

    if "eval" in selected and not args.fast:
        print("\n[5] 古籍案例对齐分与应期判别力（非现实预测命中率）")
        for split in ("tune", "holdout"):
            m = eval_metrics(split)
            if m.get("error"):
                failures.append(f"{split} 评测未跑成")
                print(f"  × {split} 评测失败：{m['error'][:300]}")
                continue
            gate(split, m.get("avg"), minimum=baseline[split], label=f"{split} 对齐分 %")
            gate(f"{split}_top1", m.get("top1"), minimum=baseline.get(f"{split}_top1", 0.0),
                 label=f"{split} 主应期命中 %")
            if m.get("rank") is not None:
                gate(f"{split}_rank", m.get("rank"), maximum=BASELINE_MAX.get(f"{split}_rank", 99),
                     label=f"{split} 应支平均名次")

    if "yingqi_external" in selected or "eval" in selected:
        # 外部验证集：只报数、不设门槛。n 太小时设门槛只会逼人去过拟合它。
        print("\n[6] 外部验证集（未参与任何调参；只报数不设门槛）")
        for split, note in (("yingqi_holdout", "转写本，过六道自洽门"),
                            ("wikisource_holdout", "维基文库原本，过纳甲/卦变/世应三方校验")):
            ext = eval_metrics(split)
            if ext.get("error"):
                print(f"  ! {split} 未跑成：{ext['error'][:200]}")
            elif not ext.get("avg"):
                print(f"  ! {split} 为空（见 docs/CASE-LIBRARY-AUDIT.md）")
            else:
                print(f"  · {split}（{note}）对齐分 {ext['avg']}% (n={ext.get('n') or 0})，"
                      f"主应期命中 {ext.get('top1') or '—'}%，应支平均名次 {ext.get('rank') or '—'}")
        print("    两个集合都是**永不参与调参**的外部集；n 越小越只能当参照，"
              "别拿它当成绩，也别为过它写私有规则（扩样路线见 HANDOFF 四·三）")

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
