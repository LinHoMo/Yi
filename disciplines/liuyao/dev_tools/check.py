# -*- coding: utf-8 -*-
"""一条命令跑完全部质量门：`python dev_tools/check.py [--only eval calendar]`

  python dev_tools/check.py            # 全部检查
  python dev_tools/check.py --fast     # 跳过耗时的两套案例评测
  python dev_tools/check.py --raise    # 把当前实测值写回基线（确认改进后才用）

  --only 逗号与空格等价（`--only eval,calendar` 同 `--only eval calendar`）；给的名字一个
  都对不上就报错、列出可用项并退出码 2——不会"零门执行却打印通过"。

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
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]          # 学科根：disciplines/liuyao
sys.path.insert(0, str(DISC / "scripts"))
from kernel_path import kernel_dir as _kernel_dir, repo_root as _repo_root  # noqa: E402
REPO = _repo_root(__file__)                          # 仓库根：含 core/ 与 disciplines/
ROOT = DISC                                          # 兼容旧变量名：脚本与数据以学科根为基准
sys.path.insert(0, str(_kernel_dir(__file__)))
from yishu_core.gate_kit import (  # noqa: E402
    eval_metrics as _kit_eval_metrics,
    measure as _kit_measure,
    run_step as _run_step,
)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

BASELINE_FILE = ROOT / "dev_tools" / "check_baseline.json"


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
    "tune": 93.9,          # 古籍对齐分 strict，n=20
    "holdout": 85.7,       # 古籍对齐分 strict，n=12（未参与调参）
    "tune_top1": 58.8,     # 主应期命中率 %（随机期望 ~38，+20pt）
    "holdout_top1": 50.0,
}
# 基准应支平均名次：越小越好，单独按上限把关
BASELINE_MAX = {"tune_rank": 2.0, "holdout_rank": 1.7}

PATTERNS = {
    "chain_tests": r"Passed:\s*(\d+)/(\d+)",
    "regression": r"总通过:\s*(\d+)/(\d+)",
    "smoke": r"有产出:\s*(\d+)",
}


def run(cmd: list[str]) -> tuple[int, str]:
    """本门口径：cwd=学科根、无超时、argv 自带解释器（实现在内核 gate_kit）。"""
    return _run_step(cmd, cwd=ROOT)


def measure(name: str, out: str) -> float | None:
    return _kit_measure(name, out, PATTERNS)


def eval_metrics(split: str) -> dict:
    """跑一个集合，返回 {avg, top1, rank}（新鲜度守卫与落盘点在内核 gate_kit）。"""
    return _kit_eval_metrics(split, model_key="strict", cwd=ROOT,
                             eval_file=ROOT / "data" / "cases" / f"eval_{split}.json")


# 本地门户产物，gitignore 的构建物。新克隆里没有 → 版本门跳过并说明，
# 而不是 FileNotFoundError 把整个门判红。
PORTAL_ARTIFACTS = ("assets/portal_data.json", "index.html")


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

    for rel in PORTAL_ARTIFACTS:
        p = ROOT / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        m = re.search(r'"version"\s*:\s*"([^"]+)"', text)
        if not m:
            problems.append(f"{rel} 找不到 version 字段")
        elif m.group(1) != yishu_core.__version__:
            problems.append(f"{rel} 版本是 {m.group(1)}，应为 {yishu_core.__version__}"
                            f"（跑 python scripts/build_portal_assets.py 重建）")
    return problems


def feedback_selftest() -> list[str]:
    """六爻反馈闭环假例自检（架构评审 A2）——此前本通道「有实现、无测试、无数据」。

    只跑**纯假例**，且落盘目标改成临时目录（不碰 `data/feedback/`，那是真实用户
    回填数据的落点，铁律二）。断言：应期抽取、strict/loose 判定（口径取自内核
    `yishu_core.yingqi`）、读数汇总，以及审计报告确实带口径句。
    """
    import shutil
    import tempfile

    sys.path.insert(0, str(DISC / "dev_tools"))
    from feedback_store import FeedbackStore, _extract_yingqi_dates  # noqa: E402
    import feedback_report  # noqa: E402

    problems: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="fb_selftest_"))
    try:
        store = FeedbackStore("liuyao")
        store.dir = tmp
        analyze = {"conclusion": {"应期": ["2026-10-05（冲空填实）", "2026-10-17（出旬）"]}}
        dates = _extract_yingqi_dates(analyze)
        if dates != ["2026-10-05", "2026-10-17"]:
            problems.append(f"应期抽取结果 {dates} ≠ 期望的两条 YYYY-MM-DD 候选")
        store.save({"analyze_json": analyze, "actual_date": "2026-10-06"})   # ±1 天 → 严格命中
        store.save({"analyze_json": analyze, "actual_date": "2026-11-20"})   # 远距 → 双否
        recs = {r["actual_date"]: r for r in store.load_all()}
        if len(recs) != 2:
            problems.append(f"落盘记录数 {len(recs)} ≠ 2")
        near = recs.get("2026-10-06") or {}
        if not (near.get("hit_strict") and near.get("hit_loose")):
            problems.append(f"±1 天应记严格命中，实为 strict={near.get('hit_strict')}"
                            f" loose={near.get('hit_loose')}")
        far = recs.get("2026-11-20") or {}
        if far.get("hit_strict") or far.get("hit_loose"):
            problems.append(f"远距日期不得记命中，实为 strict={far.get('hit_strict')}"
                            f" loose={far.get('hit_loose')}")
        st = store.stats()
        if (st["strict_hits"], st["loose_hits"], st["with_actual_outcome"]) != (1, 1, 2):
            problems.append(f"汇总读数 {st} ≠ （严格 1、宽松 1、可评 2）")
        if "口径" not in feedback_report.summary(store):
            problems.append("审计报告未附口径句（WINDOW_CALIBER 未接线）")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return problems


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="六爻质量门")
    ap.add_argument("--only", nargs="*", help="限定检查项（逗号与空格分隔等价；对不上即报错退出 2）")
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

    # 选择器（--only）语义：逗号与空格等价；「选了名字却一个都没匹配上」必须显式失败。
    # 历史坑：本文件 docstring 旧示例写 --only eval,calendar（逗号），而实现按空格切——整串
    # 被当成一个陌生名字，所有门被跳过却打印"全部通过"、退出码 0（假绿）。
    # 可用名字的唯一真值源 = 下面各门的调用点（want() 就地登记），不另维护清单。
    only: set[str] | None = None
    if args.only is not None:
        only = {tok.strip() for chunk in args.only for tok in chunk.split(",")}
        only = {tok for tok in only if tok}
    seen_gates: list[str] = []

    def want(name: str) -> bool:
        """段落守卫：登记可用名字（唯一真值源），并返回该段本次是否执行。"""
        if name not in seen_gates:
            seen_gates.append(name)
        return only is None or name in only

    if want("version"):
        import yishu_core
        print(f"\n[0] 版本一致性（唯一真值源 yishu_core.__version__ = {yishu_core.__version__}）")
        for rel in PORTAL_ARTIFACTS:
            if not (ROOT / rel).exists():
                print(f"  · {rel} 不存在（本地门户未构建）→ 跳过该版本门")
        vproblems = version_report()
        for v in vproblems:
            print(f"  × {v}")
        if not vproblems:
            print(f"  √ 全项目统一 v{yishu_core.__version__}，无第二处版本号")
        failures.extend(vproblems)

    if want("calendar"):
        print("\n[1] 干支历内核自检")
        rc, out = run([sys.executable, str(REPO / "core" / "yishu_core" / "calendar_check.py")])
        passed = re.search(r"自检：(\d+) 项通过，(\d+) 项失败", out)
        if passed:
            gate("calendar", float(passed.group(1)), minimum=baseline["calendar"],
                 label="自检通过项", raw=out)
        if rc != 0:
            failures.append("历法自检退出码非 0")

    if want("ordering"):
        print("\n[1.5] 爻序断言（自下而上唯一约定，P0 看门狗）")
        rc, out = run([sys.executable, "dev_tools/hexagram_check.py"])
        m = re.search(r"(\d+) 项通过，(\d+) 项失败", out)
        if m:
            gate("ordering", float(m.group(1)), minimum=baseline["ordering"],
                 label="爻序断言通过数", raw=out)
        if rc != 0:
            failures.append("爻序断言未通过")

    if want("golden"):
        # 金标准指纹：64 卦 × 3 爻型 × 时间的排盘＋思维链＋分析层逐字段快照。
        # 基线是 data/golden/digest.json（入库），所以换机器也拦得住行为漂移——
        # 以前它只活在 gitignore 的 scratch/ 里，等于只有我这台机器有看门狗。
        print("\n[1.6] 金标准指纹（行为漂移看门狗）")
        rc, out = run([sys.executable, "dev_tools/golden.py"])
        if "指纹" in out:
            d = re.search(r"指纹 ([0-9a-f]{16})", out) or re.search(r"机械 ([0-9a-f]{16})", out)
            # 用例数只认壳输出（唯一真值源）；取不到就如实说未知，不回落到自写常量。
            n = re.search(r"用例 (\d+) 条", out)
            cnt = f"{n.group(1)} 例指纹" if n else "指纹（用例数未知）"
            print(f"  {'√' if rc == 0 else '×'} {cnt} "
                  f"{d.group(1) if d else '?'} "
                  f"{'与基线一致' if rc == 0 else '— 行为已漂移，改的是不是你要改的？'}")
        if rc != 0:
            failures.append("金标准指纹与基线不一致")


    if want("feedback"):
        # 反馈闭环假例自检（架构评审 A2）：此前本通道「有实现、无测试、无数据」，
        # 任一处改坏（应期抽取、口径、读数、口径句接线）都不会有任何门发现。
        print("\n[1.7] 反馈闭环假例自检（落盘走临时目录，铁律二）")
        fproblems = feedback_selftest()
        for f in fproblems:
            print(f"  × {f}")
        if not fproblems:
            print("  √ 应期抽取 / 严格·宽松判定 / 读数汇总 / 口径句接线 全部通过（口径取自内核）")
        failures.extend(fproblems)

    if want("smoke"):
        print("\n[2] 分析段落产出冒烟（只验有无产出）")
        rc, out = run([sys.executable, "tests/smoke_test.py"])
        gate("smoke", measure("smoke", out), minimum=baseline["smoke"],
             label="段落有产出数", raw=out)

    if want("style"):
        # 报告外观：用到的类名必须有定义。评分与金标准指纹看不见"内容对、外观散架"这一类回归。
        # （两套 CSS 合并时就散过一次：排盘报告的 .container/.cell-* 等 29 个类没了定义。）
        print("\n[2.5] 报告样式层覆盖（类名必须有定义）")
        rc, out = run([sys.executable, "dev_tools/style_check.py"])
        for line in out.splitlines():
            if line.strip():
                print("  " + line.strip())
        if rc != 0:
            failures.append("报告里有类名没定义（样式层缺规则）")

    if want("chain_tests"):
        print("\n[3] 思维链用例（12 例，逐维度断言）")
        rc, out = run([sys.executable, "tests/thinking_chain_tests.py"])
        gate("chain_tests", measure("chain_tests", out), minimum=baseline["chain_tests"],
             label="用例通过数", raw=out)

    if want("regression"):
        print("\n[4] 古籍回归（18 例，用神/方向/区间三维）")
        rc, out = run([sys.executable, "tests/regression_test.py"])
        gate("regression", measure("regression", out), minimum=baseline["regression"],
             label="回归通过数", raw=out)

    if want("eval") and not args.fast:
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

    if want("yingqi_external") or want("eval"):
        # 外部验证集：只报数、不设门槛。n 太小时设门槛只会逼人去过拟合它。
        print("\n[6] 外部验证集（未参与任何调参；只报数不设门槛）")
        for split, note in (("yingqi_holdout", "转写本，过六道自洽门"),
                            ("wikisource_holdout", "维基文库原本，过纳甲/卦变/世应三方校验"),
                            ("wikisource_direction", "同书有吉凶无验期（应期 N/A，只评方向）"),
                            ("huozhulin_holdout", "火珠林原本，应期可评（含時级）"),
                            ("suigui_holdout", "增删卜易·随鬼入墓章真例（动墓/化墓结构）")):
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

    # 选择器自证：选了名字却没一个对上——"假绿"里最凶的一种（旧行为在此打印"全部通过"
    # 并退出 0）。一律显式失败并列出可用项；用法错误统一退出码 2。
    matched = [] if only is None else [n for n in seen_gates if n in only]
    unknown = [] if only is None else sorted(n for n in only if n not in seen_gates)
    if only is not None and (not matched or unknown):
        if not only:
            why = "`--only` 展开后为空，至少要给一个检查项"
        elif not matched:
            why = f"{sorted(only)} 里没有一个能对上的检查项"
        else:
            why = f"不认识这些检查项 {unknown}"
        print(f"\n--only 用法错误：{why}")
        if not matched:
            print("  （上面的 √ 不代表任何检查真的跑过——别把它当通过。）")
        print("  可用检查项（取自各门调用点；逗号与空格分隔等价）：")
        for i in range(0, len(seen_gates), 4):
            print("    " + "".join(f"{c:<18}" for c in seen_gates[i:i + 4]).rstrip())
        return 2

    if failures:
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
