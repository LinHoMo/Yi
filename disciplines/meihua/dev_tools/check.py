# -*- coding: utf-8 -*-
"""一条命令跑完全部质量门：`python dev_tools/check.py [--only eval golden]`

  python dev_tools/check.py            # 全部检查
  python dev_tools/check.py --fast     # 跳过案例评测
  python dev_tools/check.py --raise    # 把本次实测值写回基线（确认改进后才用）

  --only 逗号与空格等价（`--only eval,golden` 同 `--only eval golden`）；给的名字一个
  都对不上就报错、列出可用项并退出码 2——不会"零门执行却打印通过"。

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

from yishu_core.gate_kit import (  # noqa: E402
    eval_metrics as _kit_eval_metrics,
    measure as _kit_measure,
    run_step as _run_step,
)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

BASELINE_FILE = DISC / "dev_tools" / "check_baseline.json"

BASELINE = {
    "smoke": 5,          # 四段管线冒烟有产出数（最低 5；现跑 6，含多爻动 manual）
    # 100.0 是「规则表自洽回归线」，不是能力线：relation/sheng_ti/ke_ti/timing 四项
    # expected 与引擎同源（见 data/cases/meihua_cases.json#_meta._provenance 与
    # docs/EVAL-AUDIT.md）。此门只防「查表/生克管线被改坏」。
    "tune": 100.0,       # 古籍对齐分 strict，n=10（参与过调参）
    "holdout": 100.0,    # 古籍对齐分 strict，n=13（未参与调参）。
                         # n<20 按 docs/EVAL-AUDIT.md 只报命中数，不报百分比。
}

PATTERNS = {
    "smoke": r"有产出:\s*(\d+)",
}


def run(cmd: list[str]) -> tuple[int, str]:
    """本门口径：cwd=学科根、无超时、argv 自带解释器（实现在内核 gate_kit）。"""
    return _run_step(cmd, cwd=DISC)


def measure(name: str, out: str) -> float | None:
    return _kit_measure(name, out, PATTERNS)


def eval_metrics(split: str) -> dict:
    """跑一个集合，返回 {avg, n}（新鲜度守卫与落盘点在内核 gate_kit）。"""
    return _kit_eval_metrics(split, cwd=DISC,
                             eval_file=DISC / "data" / "cases" / f"eval_{split}.json")


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


# 占验/占例篇（书源里以具体占例说理的篇目）：**不得**进 data/classics.json
# （AGENTS.md 铁律二：案例库与预测过程物理隔离）
CASE_SECTIONS = (
    "觀梅占", "牡丹占", "鄰夜扣門借物占", "今日動靜如何", "西林寺牌額占",
    "老人有憂色占", "少年有喜色占", "牛哀鳴占", "雞悲鳴占", "枯枝墜地占",
    "風覺鳥占", "風覺占", "鳥占", "聽聲音占", "形物占", "驗色占",
    "觀物用易例", "萬物戲驗",
)


def check_classics() -> list[str]:
    """[1c] 古籍原文门：逐字可回指 + 卷次覆盖 + 案例篇隔离（铁律二）。

    原文是**所本凭证**，不是判据（判据唯一真值源 = data/verdicts.json）。本门既防
    「引文不是原书原文」，也防「占验案例混进语料与报告」。
    """
    fails: list[str] = []
    cit_p = DISC / "data" / "classics.json"
    vols = {
        v: DISC / "data" / "sources" / f"meihua_yishu_{v}.wikitext.txt"
        for v in ("卷一", "卷二", "卷三")
    }
    if not cit_p.exists():
        return ["data/classics.json 不存在（跑 python dev_tools/build_classics.py --write）"]
    missing = [str(p) for p in vols.values() if not p.exists()]
    if missing:
        return [f"书源缺失：{missing}"]
    cit = json.loads(cit_p.read_text(encoding="utf-8"))
    src = {v: p.read_text(encoding="utf-8") for v, p in vols.items()}

    if cit.get("schema") != "meihua-classics-v1":
        fails.append(f"schema 非 meihua-classics-v1：{cit.get('schema')}")

    rules = cit.get("rules") or {}
    per_gua = cit.get("per_gua") or {}
    wanwu = cit.get("wanwu") or {}
    texts: list[tuple[str, str, str]] = []          # (标签, 卷, 原文)
    for key, entry in rules.items():
        vol = entry.get("卷")
        for t in (entry.get("原文") or []):
            texts.append((f"rules.{key}", vol, t))
        if not entry.get("出处") or not entry.get("篇"):
            fails.append(f"规则缺篇名/出处：{key}")
    for kind, items in per_gua.items():
        for gua, entry in (items or {}).items():
            texts.append((f"per_gua.{kind}.{gua}", entry.get("卷"), entry.get("原文", "")))
            if not entry.get("出处"):
                fails.append(f"逐卦条缺出处：{kind}·{gua}")
    # 逐卦类象正表（卷一·八卦萬物屬類）：每条都按记录行号回读核对（比子串断言更强）
    vol1 = src.get("卷一", "")
    lines1 = vol1.splitlines()
    n_wanwu = 0
    for gua, items in wanwu.items():
        cls = {k: v for k, v in items.items() if not k.startswith("_")}
        if len(cls) < 20:
            fails.append(f"wanwu.{gua} 类目 {len(cls)} < 20（书源结构或抽取变了）")
        for name in ("天時", "地理", "人物"):
            if name not in cls:
                fails.append(f"wanwu.{gua} 缺必备类「{name}」")
        for cname, entry in cls.items():
            n_wanwu += 1
            texts.append((f"wanwu.{gua}.{cname}", "卷一", entry.get("原文", "")))
            ln = entry.get("行号")
            if not isinstance(ln, int) or not (1 <= ln <= len(lines1)) \
                    or lines1[ln - 1].strip() != entry.get("原文", ""):
                fails.append(f"wanwu.{gua}.{cname}：行号 {ln} 回读与原文不符")
    if len(wanwu) != 8:
        fails.append(f"wanwu 应含八经卦 8 项，实为 {len(wanwu)}")
    if not texts:
        fails.append("classics.json 无任何原文")

    for label, vol, text in texts:
        if vol not in src:
            fails.append(f"{label}: 卷次未知 {vol}")
            continue
        if not text or text not in src[vol]:
            fails.append(f"{label}: 原文不可回指 {vol} / {str(text)[:24]}")

    if sorted(vols) != sorted({v for _, v, _ in texts}):
        fails.append(f"卷次覆盖不全：{[v for _, v, _ in texts]}")
    if len(per_gua.get("生体") or {}) != 8 or len(per_gua.get("克体") or {}) != 8:
        fails.append("逐卦生体/克体条应各 8 条")

    # 案例篇只查**原文载荷**（rules/per_gua/wanwu）；_comment 里点名"哪些篇目被排除"是说明性文字，
    # 不构成把案例带进语料（与 build_classics.py 的断言同一范围）。
    body = json.dumps({"rules": rules, "per_gua": per_gua, "wanwu": wanwu},
                      ensure_ascii=False)
    for sec in CASE_SECTIONS:
        if sec in body:
            fails.append(f"案例篇混入（铁律二）：{sec}")

    print(f"  {'√' if not fails else '×'} 原文门 规则 {len(rules)} 条 / 原文段 {len(texts)} 段"
          f"（含逐卦类象 {n_wanwu} 条，按行号回读核对）")
    print(f"      逐字回指：卷一/卷二/卷三 三卷书源均已核对；"
          f"案例篇隔离断言 {len(CASE_SECTIONS)} 个篇名")
    return fails


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="梅花易数质量门")
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

    # 选择器（--only）语义：逗号与空格等价；「选了名字却一个都没匹配上」必须显式失败。
    # 历史坑：本文件 docstring 旧示例写 --only eval,golden（逗号），而实现按空格切——整串
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
        vproblems = version_report()
        for v in vproblems:
            print(f"  × {v}")
        if not vproblems:
            print("  √ 全项目统一 v" + str(yishu_core.__version__) + "，无第二处版本号")
        failures.extend(vproblems)

    if want("golden"):
        print("\n[1] 金标准指纹（行为漂移看门狗）")
        rc, out = run([sys.executable, "dev_tools/golden.py"])
        d = re.search(r"指纹 ([0-9a-f]{16})", out) or re.search(r"机械 ([0-9a-f]{16})", out)
        # 用例数只认壳输出（唯一真值源）；取不到就如实说未知，不回落到自写常量。
        n = re.search(r"用例 (\d+) 条", out)
        cnt = f"{n.group(1)} 例指纹" if n else "指纹（用例数未知）"
        print(f"  {'√' if rc == 0 else '×'} {cnt} "
              f"{d.group(1) if d else '?'} "
              f"{'与基线一致' if rc == 0 else '— 行为已漂移，改的是不是你要改的？'}")
        if rc != 0:
            failures.append("金标准指纹与基线不一致")

    if want("classics"):
        print("\n[1c] 古籍原文门（逐字可回指 + 卷次覆盖 + 案例篇隔离）")
        cfs = check_classics()
        for c in cfs:
            print(f"  × {c}")
        failures.extend(cfs)

    if want("smoke"):
        print("\n[2] 四段管线产出冒烟（只验有无产出）")
        rc, out = run([sys.executable, "scripts/smoke_test.py"])
        gate("smoke", measure("smoke", out), minimum=baseline["smoke"],
             label="管线有产出数", raw=out)

    if want("eval") and not args.fast:
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
