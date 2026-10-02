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

DISC = Path(__file__).resolve().parents[1]          # 学科根：disciplines/zeji
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
    # 100.0 是「历法表 + 规则表自洽回归线」，不是能力线：expected 可由引擎确定性复算
    # （审计实测 16/16 逐字段全等；见 data/cases/zeji_cases.json#_meta._provenance
    # 与 docs/EVAL-AUDIT.md）。此门只防「历法/宜忌表被改坏」。
    "tune": 100.0,       # 机械因子+规则表自洽回归数 strict，n=10
    "holdout": 100.0,    # 同口径 strict，n=6。n<20 按 docs/EVAL-AUDIT.md 只报命中数
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


# 判据真值源专属键（data/verdicts.json）：书证文件出现同名键即视为「双份真值源」
VERDICT_KEYS = {"jian_chu", "huang_hei_dao", "xiu", "verdict_rule", "shensha",
                "chong_sha", "pengzu", "validity_gap", "activity_names"}


def check_citations() -> list[str]:
    """[1c] 参考书证门：引文逐字可回指 + 事类全覆盖 + 缺口如实登记 + 不混判据。

    书证是**对照原料**，不是判据（判据唯一真值源 = data/verdicts.json）。故本门
    既防「引文不是原书原文」，也防「书证悄悄长成第二份判据表」。
    """
    fails: list[str] = []
    cit_p = DISC / "data" / "citations.json"
    src_p = DISC.parents[1] / "data" / "sources" / "yuxiaji.wikitext.txt"
    prov_p = DISC.parents[1] / "data" / "sources" / "yuxiaji.provenance.json"
    if not cit_p.exists():
        return ["data/citations.json 不存在（跑 python dev_tools/build_citations.py --write）"]
    if not src_p.exists():
        return [f"书源缺失：{src_p}"]
    cit = json.loads(cit_p.read_text(encoding="utf-8"))
    src = src_p.read_text(encoding="utf-8")
    verd = json.loads((DISC / "data" / "verdicts.json").read_text(encoding="utf-8"))

    if cit.get("schema") != "zeji-citations-v1":
        fails.append(f"schema 非 zeji-citations-v1：{cit.get('schema')}")
    if not prov_p.exists():
        fails.append("书源 provenance 缺失（无抓取留档）")

    acts = cit.get("activities") or {}
    entries = list(cit.get("common") or []) + [e for v in acts.values() for e in v]
    for e in entries:
        title = e.get("title") or "?"
        lines = e.get("lines") or []
        if not lines:
            fails.append(f"篇目无引文：{title}")
        if not e.get("provenance"):
            fails.append(f"篇目无出处：{title}")
        for ln in lines:
            if ln not in src:
                fails.append(f"引文不可回指：{title} / {ln[:24]}")

    names = set(verd.get("activity_names") or {})
    missing, extra = sorted(names - set(acts)), sorted(set(acts) - names)
    if missing:
        fails.append(f"事类无书证：{missing}")
    if extra:
        fails.append(f"书证出现表外事类：{extra}")

    gap = cit.get("gap") or {}
    for k in ("book", "status", "checked", "result", "handling", "basis_note"):
        if not gap.get(k):
            fails.append(f"缺口登记缺字段：gap.{k}")
    if "missingtitle" not in str(gap.get("result", "")):
        fails.append("缺口未登记实测结论（missingtitle）")

    # 二十八宿值日吉凶歌（书证）：逐字 + **按行号回读** + 与判据表吉凶一致
    from yishu_core.zeji_tables import XIU_ORDER as _XIU
    src_lines = src.splitlines()
    xv = cit.get("xiu_verses") or {}
    n_xiu_verse = 0
    if set(xv) != set(_XIU):
        fails.append(f"宿歌书证宿集与内核 XIU_ORDER 不一致：多 "
                     f"{sorted(set(xv) - set(_XIU))} 缺 {sorted(set(_XIU) - set(xv))}")
    ji_set = set((verd.get("xiu") or {}).get("吉宿") or [])
    xiong_set = set((verd.get("xiu") or {}).get("凶宿") or [])
    for su, item in xv.items():
        for text, ln in zip(item.get("歌诀") or [], item.get("行号") or []):
            n_xiu_verse += 1
            if text not in src:
                fails.append(f"宿歌不可回指：{su} / {str(text)[:20]}")
            if not isinstance(ln, int) or not (1 <= ln <= len(src_lines)) \
                    or src_lines[ln - 1].strip() != text:
                fails.append(f"宿歌行号 {ln} 回读与原文不符：{su} / {str(text)[:20]}")
        want = "吉" if su in ji_set else ("凶" if su in xiong_set else None)
        if want is None:
            fails.append(f"宿「{su}」不在判据表吉宿/凶宿内（书证与判据表两不相认）")
        elif item.get("吉凶") != want:
            fails.append(f"宿「{su}」书证吉凶 {item.get('吉凶')} ≠ 判据表 {want}"
                         f"（书证与判据必须一致，不一致需人裁决）")
        if len(item.get("歌诀") or []) != len(item.get("行号") or []):
            fails.append(f"宿「{su}」歌诀与行号不配对")

    bleed = sorted(set(cit) & VERDICT_KEYS)
    if bleed:
        fails.append(f"书证混入判据键（双份真值源风险）：{bleed}")

    print(f"  {'√' if not fails else '×'} 书证门 "
          f"引文 {sum(len(e.get('lines') or []) for e in entries)} 条 / 篇目 {len(entries)} 篇 "
          f"/ 事类 {len(acts)} 个 / 通则 {len(cit.get('common') or [])} 篇"
          f" / 宿歌 {len(xv)} 宿 {n_xiu_verse} 行")
    print(f"      逐字回指底本：{src_p.name}（{src_p.stat().st_size} 字节）；"
          f"缺口登记：{gap.get('book', '?')}")
    print("      宿歌与判据表交叉断言：书证吉凶 ≡ verdicts.json#xiu 吉宿/凶宿")
    return fails


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="择吉质量门")
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

    if want("citations"):
        print("\n[1c] 参考书证门（《玉匣記》引文可回指 + 事类覆盖 + 缺口登记）")
        for f in check_citations():
            failures.append(f)

    if want("golden"):
        print("\n[1] 金标准指纹（行为漂移看门狗）")
        rc, out = run([sys.executable, "dev_tools/golden.py"])
        d = re.search(r"指纹 ([0-9a-f]{16})", out) or re.search(r"机械 ([0-9a-f]{16})", out)
        n = re.search(r"用例 (\d+) 条", out)
        print(f"  {'√' if rc == 0 else '×'} {n.group(1) if n else '?'} 例指纹 "
              f"{d.group(1) if d else '?'} "
              f"{'与基线一致' if rc == 0 else '— 行为已漂移，改的是不是你要改的？'}")
        if rc != 0:
            failures.append("金标准指纹与基线不一致")

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
    print("分数含义：与案例库要点的一致性，不代表现实预测命中率。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
