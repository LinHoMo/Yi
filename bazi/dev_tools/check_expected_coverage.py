# -*- coding: utf-8 -*-
"""八字科 expected 书证/机械派生字段的覆盖生存线（门禁 [40]，第四百二十批新增）。

为什么需要它：419 批在六爻侧抓到真实事故——403 批重建 dz 案例册时把 206／208 批
逐条书证校勘的 18 例 `use_god`／`use_god_branch`／`use_god_note` 整段清空，
而当时的 [38] 只扫 wikisource，读数从 57.4 级别悄悄回到 53 级别、所有门全绿。
八字科有 7 个案例文件、多个构建器（四柱/调候/从格/化格/行运/病药/外部集），
**同一类事故换到八字侧没有任何门能拦**。本门把每个案例文件的受控字段非空数
钉成单调下限：构建器重生成只写自动解析字段时，整批清空立刻判红。

    python dev_tools/check_expected_coverage.py
    python dev_tools/check_expected_coverage.py --selftest

口径：生存线，不是逐例值锁。逐例书证由各批 CHANGELOG 与 [10] 书证回验守。
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DISC = Path(__file__).resolve().parents[1]
REG = DISC / "data" / "rules" / "expected_coverage.json"


def _nonempty(value) -> bool:
    return value not in ("", None, [], {})


def audit(data: dict, spec: dict) -> list[str]:
    problems: list[str] = []
    cases = data.get("cases") if isinstance(data, dict) else data
    if not isinstance(cases, list):
        return ["案例文件结构不可解析（不是 cases 列表）"]
    if len(cases) < int(spec["case_count"]):
        problems.append(f"案例数 {len(cases)} < 登记下限 {spec['case_count']}——构建器可能丢了案例")
    for field, rule in spec["fields"].items():
        n = sum(1 for c in cases if _nonempty((c.get("expected") or {}).get(field)))
        if n < int(rule["min"]):
            problems.append(f"{field} 非空 {n} < 登记下限 {rule['min']}——该字段被整批清空或回退")
    return problems


def load() -> tuple[dict, dict]:
    reg = json.loads(REG.read_text(encoding="utf-8"))
    data = {name: json.loads((DISC / "data" / "cases" / name).read_text(encoding="utf-8"))
            for name in reg["cases"]}
    return data, reg


def selftest(data_by_file: dict, registry: dict) -> list[str]:
    fails: list[str] = []

    def must_catch(label: str, name: str, mutate) -> None:
        broken = copy.deepcopy(data_by_file[name])
        mutate(broken)
        got = audit(broken, registry["cases"][name])
        if not got:
            fails.append(f"负例未抓到（{name}）：{label}")

    for name, spec in registry["cases"].items():
        fields = list(spec["fields"])
        if fields:
            must_catch("整批清空受控字段", name,
                       lambda d, fs=fields: [c.setdefault("expected", {}).__setitem__(f, "")
                                             for c in (d.get("cases") if isinstance(d, dict) else d)
                                             for f in fs])
        must_catch("删掉一例", name,
                   lambda d: d["cases"].pop() if isinstance(d, dict) else d.pop())
        cases = data_by_file[name].get("cases") if isinstance(data_by_file[name], dict) else data_by_file[name]
        if audit(data_by_file[name], spec):
            fails.append(f"完好夹具被误伤（{name}）——本门自身口径有误")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser(description="八字 expected 覆盖生存线（门禁 [40]）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    data_by_file, registry = load()
    problems: list[str] = []
    print("八字 expected 覆盖生存线对拍：")
    for name, spec in registry["cases"].items():
        data = data_by_file[name]
        cases = data.get("cases") if isinstance(data, dict) else data
        print(f"  [{name}] 案例 {len(cases)}（下限 {spec['case_count']}）")
        for field, rule in spec["fields"].items():
            n = sum(1 for c in cases if _nonempty((c.get("expected") or {}).get(field)))
            print(f"    · {field:<20} {n:>4}/{len(cases)}（下限 {rule['min']}）")
        ps = audit(data, spec)
        for p in ps:
            print(f"    × {p}")
        problems += [f"[{name}] {p}" for p in ps]
    if not problems:
        print(f"  √ {len(registry['cases'])} 个案例文件的受控字段非空数均不低于登记下限")

    st_fail: list[str] = []
    if args.selftest:
        st_fail = selftest(data_by_file, registry)
        print(f"  [selftest] 负例{'全部抓到' if not st_fail else '失效'}（每文件 2 类：整批清空／删例）")
        for p in st_fail:
            print("  ×", p)

    if problems or st_fail:
        return 1
    print("八字 expected 覆盖生存线门通过。解锁＝同批更新 bazi/data/rules/expected_coverage.json 与 docs/CHANGELOG.md。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
