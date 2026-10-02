# -*- coding: utf-8 -*-
"""紫微斗数质量门：`python dev_tools/check.py [--fast] [--only structure golden]`

   python dev_tools/check.py            # 全部检查（目前仅_struct_contract + golden + pipeline 冒烟）
   python dev_tools/check.py --fast     # 跳过论文档评测

   --only 逗号与空格等价（`--only structure,golden` 同 `--only structure golden`）；
   给的名字一个都对不上就报错、列出可用项并退出码 2——不会"零门执行却打印全部通过"。

紫微斗数是机械命科（出生时空→格局/四化/大限），无案例对齐评测（类比 ming 机械回归）。
验证点：四段契约文件齐全、JSON 排盘产出正确、金标准指纹稳定。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.gate_kit import run_step  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402


def _run(cmd: list[str]) -> tuple[int, str]:
    """本门口径：cwd=学科根、无超时、argv 自带解释器（实现在内核 gate_kit）。"""
    return run_step(cmd, cwd=DISC)


def check_structure() -> list[str]:
    """四段契约 + 目录结构验证。"""
    CONTRACT_FILES = (
        "SKILL.md", "scripts/chart.py", "scripts/analyze.py",
        "scripts/narrate.py", "scripts/render.py",
        "data/verdicts.json", "dev_tools/check.py", "dev_tools/golden.py",
    )
    fails = []
    for f in CONTRACT_FILES:
        if not (DISC / f).exists():
            fails.append(f"学科缺 {f}（CONTRACT 契约）")
    # 案例分层同根门：目录本身不是硬条件（空目录克隆带不走），没案例库就明说。
    cases = DISC / "data" / "cases"
    if not (cases.is_dir() and any(cases.glob("*.json"))):
        print("  · 尚无案例库（data/cases 下没有 *.json）")
    # 内核表唯一：学科内不得重新定义 core 已有表
    CORE_TABLE = re.compile(
        r"^\s*(PALACES|WUXING_TO_JU|SIHUA_TABLE|ZIWEI_GROUP_ORDER|TIANFU_GROUP_ORDER|"
        r"STARS|AUXILIARY_STARS|PATTERNS)\s*=\s*[\[\{]", re.M)
    for p in (DISC / "scripts").rglob("*.py"):
        if "scratch" in p.parts:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if CORE_TABLE.match(line):
                name = line.strip().split("=", 1)[0].strip()
                fails.append(f"{p.relative_to(DISC)}:{i}: 复制核心表 {name}（应从 core.ziwei_tables import）")
    return fails


def check_pipeline() -> list[str]:
    """四段管线冒烟：chart→analyze→narrate→render 端到端。"""
    fails = []
    scratch = DISC / "scratch"
    scratch.mkdir(exist_ok=True)
    chart_json = scratch / "chart.json"
    analyze_json = scratch / "analyze.json"
    narrate_md = scratch / "narrate.md"
    render_md = scratch / "render.md"

    steps = [
        ([sys.executable, "scripts/chart.py", "--datetime", "1990-05-20 10:30",
          "--gender", "男", "-o", str(chart_json)], "chart"),
        ([sys.executable, "scripts/analyze.py", str(chart_json),
          "-o", str(analyze_json)], "analyze"),
        ([sys.executable, "scripts/narrate.py", str(analyze_json),
          "-o", str(narrate_md)], "narrate"),
        ([sys.executable, "scripts/render.py", str(analyze_json),
          "-o", str(render_md)], "render"),
    ]
    for cmd, label in steps:
        rc, out = _run(cmd)
        if rc != 0:
            fails.append(f"{label} 段退出码 {rc}: {out[:200]}")
    # 验证 JSON 结构
    if chart_json.exists():
        c = json.loads(chart_json.read_text(encoding="utf-8"))
        if c.get("palaces", {}).get("命宫", {}).get("main_stars") in (None, []):
            fails.append("chart 命宫无主星（可能排盘异常）")
    return fails


def check_regression() -> list[str]:
    """古法回归：core 安星取值层对着书源原文逐条核对（非比对上次输出）。"""
    rc, out = _run([sys.executable, "dev_tools/regression.py"])
    fails = []
    tail = out.strip().splitlines()
    for line in tail:
        print(f"  {line}" if not line.startswith("  ") else line)
    if rc != 0:
        fails.append("古法回归未通过（见上）")
    return fails


def _leaf_strings(obj) -> list[str]:
    """语料 JSON → 全部叶子字符串（跳过 _meta：元信息本就不进报告）。"""
    if isinstance(obj, dict):
        out = []
        for k, v in obj.items():
            if k == "_meta":
                continue
            out.extend(_leaf_strings(v))
        return out
    if isinstance(obj, list):
        return [s for v in obj for s in _leaf_strings(v)]
    return [obj] if isinstance(obj, str) else []


def check_corpus_wiring() -> list[str]:
    """接线自检：data/*.json 每个语料文件都必须真的被报告消费（否则是死语料）。"""
    fails = []
    render_md = DISC / "scratch" / "render.md"
    if not render_md.is_file():
        return ["scratch/render.md 不存在（管线未跑）"]
    text = render_md.read_text(encoding="utf-8")
    for path in sorted((DISC / "data").glob("*.json")):
        leaves = [s for s in _leaf_strings(json.loads(path.read_text(encoding="utf-8")))
                  if len(s) >= 12]
        if not leaves:
            continue
        hit = sum(1 for s in leaves if s in text)
        if hit == 0:
            fails.append(f"{path.name}: {len(leaves)} 条语料一条未进报告（接线缺失）")
        else:
            print(f"  √ {path.name}：{hit}/{len(leaves)} 条进入报告")
    return fails


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="紫微斗数质量门")
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--only", nargs="*", help="限定检查项（逗号与空格分隔等价；对不上即报错退出 2）")
    args = ap.parse_args()

    # 选择器（--only）语义：逗号与空格等价；「选了名字却一个都没匹配上」必须显式失败。
    # 历史坑：旧实现没有未知门校验——名字打错/写错分隔符时所有 if 全部落空，末尾照样
    # 打印"紫微斗数质量门全部通过。"并退出 0（假绿）。
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
    failures: list[str] = []

    if want("structure"):
        print("\n[1] 四段契约与结构")
        fails = check_structure()
        if fails:
            for f in fails:
                print(f"  × {f}")
            failures.extend(fails)
        else:
            print("  √ 四段契约文件齐全")

    if want("pipeline"):
        print("\n[2] 四段管线冒烟")
        fails = check_pipeline()
        if fails:
            for f in fails:
                print(f"  × {f}")
            failures.extend(fails)
        else:
            print("  √ 四段管线端到端通过")

    if want("regression"):
        print("\n[3] 古法回归（对着书源原文核）")
        fails = check_regression()
        if fails:
            failures.extend(fails)
        else:
            print("  √ 安星取值层与书源例题/五局图逐条一致")

    if want("corpus"):
        print("\n[4] 语料接线")
        fails = check_corpus_wiring()
        if fails:
            for f in fails:
                print(f"  × {f}")
            failures.extend(fails)
        else:
            print("  √ 各语料文件均有条目进入报告")

    if want("golden") and not args.fast:
        print("\n[5] 金标准指纹")
        rc, out = _run([sys.executable, "dev_tools/golden.py"])
        if rc == 0:
            print(f"  √ {out.strip()}")
        else:
            failures.append("金标准指纹失败")
            print(f"  × {out.strip()}")

    print()
    if failures:
        print(f"质量门未通过 {len(failures)} 项")
        for f in failures:
            print(f"  · {f}")

    # 选择器自证：选了名字却没一个对上——旧行为在此打印"全部通过"并退出 0。
    # 一律显式失败并列出可用项；用法错误统一退出码 2。
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
    print("紫微斗数质量门全部通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
