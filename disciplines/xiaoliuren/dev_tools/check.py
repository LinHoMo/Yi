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
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]          # 学科根：disciplines/xiaoliuren
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
    "smoke": 5,          # 四段管线冒烟有产出数（共 5）
    # 100.0 是「规则表自洽回归线」，不是能力线：四维 expected 全部与引擎同源
    # （见 data/cases/xiaoliuren_cases.json#_meta._provenance 与 docs/EVAL-AUDIT.md）。
    # 此门只防「起课/查表管线被改坏」。
    "tune": 100.0,       # 规则自洽回归数 strict，n=10
    "holdout": 100.0,    # 规则自洽回归数 strict，n=5。n<20 按 docs/EVAL-AUDIT.md 只报命中数
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


STRIP_PAREN = re.compile(r"[（(][^）)]*[）)]")


def _corpus(p: dict) -> list[str]:
    """诀辞可回指的底本：本宫总诀 / 宫义（逐字句只可能出自这两处）。"""
    return [p.get("总诀", ""), p.get("含义", "")]


def _ext_corpus(p: dict) -> list[str]:
    """引申句的同门可核底本（宫象/属神/五行/方位…），只作重叠校验，不作逐字回指。"""
    return [p.get(k, "") or "" for k in
            ("总诀", "含义", "属神", "五行", "方位", "颜色", "位置")]


def _bigrams(s: str) -> set[str]:
    han = re.sub(r"[^\u4e00-\u9fff]", "", s)
    return {han[i:i + 2] for i in range(len(han) - 1)}


def check_topic_lines() -> list[str]:
    """[1c] 断语口径门：每条事类断语必须**声明句类**且与声明相符。

    三条不变式（对应 data/verdicts.json#topic_coverage 的记账）：
      1. 矩阵完整：topic_names 每事类 × 六宫都有条目，键三选一 {kind,text,reason} 齐；
      2. 句类相符：`诀辞` → 去括注后是本宫总诀/宫义的**连续子串**（逐字可回指）；
         `引申` → text 自带「引申」标记，且至少一个双字与同宫底本重叠（防凭空造句）；
         `阙` → text 为空且带 reason（**如实阙如：不以引申充作原文**）；
      3. 记账一致：topic_coverage.per_topic 的（诀辞/引申/阙）计数与实测逐条相符。
    """
    fails: list[str] = []
    doc = json.loads((DISC / "data" / "verdicts.json").read_text(encoding="utf-8"))
    palaces, lines = doc["palaces"], doc["topic_lines"]
    names = doc.get("topic_names") or []

    if doc.get("schema") != "xiaoliuren-verdicts-v2":
        fails.append(f"schema 非 xiaoliuren-verdicts-v2：{doc.get('schema')}")
    if sorted(names) != sorted(lines):
        fails.append(f"topic_names 与 topic_lines 事类不一致：{sorted(names)} / {sorted(lines)}")
    if not doc.get("source_gap"):
        fails.append("source_gap 缺口登记缺失（公版书源缺口必须如实登记）")
    else:
        gap = doc["source_gap"]
        for k in ("book", "status", "checked", "command", "result", "handling", "basis_note"):
            if not gap.get(k):
                fails.append(f"source_gap 缺字段：{k}")

    counts: dict[str, dict[str, int]] = {}
    for topic, per_palace in lines.items():
        c = {"诀辞": 0, "引申": 0, "阙": 0}
        if sorted(per_palace) != sorted(palaces):
            fails.append(f"{topic}: 六宫不全 {sorted(per_palace)}")
        for name, entry in per_palace.items():
            if name not in palaces:
                fails.append(f"{topic}.{name}: 宫名不在 palaces")
                continue
            if not isinstance(entry, dict):
                fails.append(f"{topic}.{name}: 条目必须是 {{kind,text[,reason]}} 对象")
                continue
            kind, text = entry.get("kind"), entry.get("text") or ""
            if kind not in c:
                fails.append(f"{topic}.{name}: 句类非法 {kind!r}")
                continue
            c[kind] += 1
            base = STRIP_PAREN.sub("", text).strip()
            if kind == "诀辞":
                if not base or not any(base in s for s in _corpus(palaces[name])):
                    fails.append(f"{topic}.{name}: 标为诀辞但不可回指本宫总诀/宫义 → {text[:30]}")
            elif kind == "引申":
                if "引申" not in text:
                    fails.append(f"{topic}.{name}: 引申句未带「引申」标记 → {text[:30]}")
                if not (_bigrams(text) & _bigrams("".join(_ext_corpus(palaces[name])))):
                    fails.append(f"{topic}.{name}: 引申句与同宫底本无任何双字重叠（疑凭空造句）")
            else:
                if text:
                    fails.append(f"{topic}.{name}: 标为阙但 text 非空")
                if not entry.get("reason"):
                    fails.append(f"{topic}.{name}: 阙未写 reason")
        counts[topic] = c

    doc_cov = (doc.get("topic_coverage") or {}).get("per_topic") or {}
    for topic, c in counts.items():
        if doc_cov.get(topic) != c:
            fails.append(f"{topic}: 覆盖记账 {doc_cov.get(topic)} ≠ 实测 {c}")
    totals = {k: sum(v[k] for v in counts.values()) for k in ("诀辞", "引申", "阙")}
    doc_totals = (doc.get("topic_coverage") or {}).get("totals") or {}
    if doc_totals != totals:
        fails.append(f"覆盖合计 {doc_totals} ≠ 实测 {totals}")

    print(f"  {'√' if not fails else '×'} 断语口径门 {len(lines)} 事类 × {len(palaces)} 宫 = "
          f"{len(lines) * len(palaces)} 条")
    print(f"      诀辞（逐字可回指）{totals['诀辞']} / 引申（带标记）{totals['引申']} / "
          f"阙（如实阙如）{totals['阙']}｜公版书源缺口已登记")
    return fails


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="小六壬质量门")
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

    if want("topics"):
        print("\n[1c] 断语口径门（句类相符 + 矩阵完整 + 记账一致 + 缺口登记）")
        tfs = check_topic_lines()
        for t in tfs:
            print(f"  × {t}")
        failures.extend(tfs)

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
