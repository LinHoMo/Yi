# -*- coding: utf-8 -*-
"""expected 书证/机械派生字段的覆盖生存线（门禁 [38]，第三百四十四批新增）。

    python dev_tools/check_expected_coverage.py            # 对拍真实案例文件
    python dev_tools/check_expected_coverage.py --selftest # 加负例：证明本门抓得住

为什么需要它：案例构建器（`fetch_wikisource_cases.py`）重生成时只写自动解析字段，
不会保留人工补的 `expected.use_god`／`use_god_branch`／`use_god_note`／
`use_god_wangshuai` 等书证与机械派生字段。1592923（易隐批）就是这样把
292/297/298/282 批的 74 个 use_god、52 个 branch、32 个 note、3 组
wangshuai-muku-six_spirit 和 WS035 校勘 verdict 一次性清空；聚合 strict 只从
75.8 掉到 69.8，所有既有门仍然全绿——**分数掉一点不等于标签还在**。

本门守三条：
  A. 案例数不得低于登记数（整文件重生成丢例即红）；
  B. 每个受控字段的非空数不得低于登记下限（整批清空即红）；
  C. 登记了 `allowed_blank` 的字段，空值 ID 必须逐条列名；出现未登记空值即红
     （`use_god` 只允许 WS045／WSD007／WSD008 三例，新增空白必须同批登记）。
  `use_god` 另校验取值集合，防止用任意字符串把计数凑回去。

口径：这是**生存线**，不是逐例值锁。逐例书证仍由 `check_source_readings.py` 与
292/297/298 批 CHANGELOG 的书证条目守；本门只防“整批被构建器静默抹掉”。
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
    return value not in ("", None, [])


def audit(data: dict, registry: dict) -> list[str]:
    """对拍一份案例 JSON 与覆盖登记；返回问题清单（空＝通过）。"""
    problems: list[str] = []
    spec = registry["cases"]["wikisource_cases.json"]
    cases = data.get("cases") or []
    ids = [str(c.get("id") or "") for c in cases]

    if len(cases) < int(spec["case_count"]):
        problems.append(f"案例数 {len(cases)} < 登记下限 {spec['case_count']}——构建器可能丢了案例")

    if spec.get("meta_sum_required"):
        meta = data.get("_meta") or {}
        total, direction = meta.get("total_cases"), meta.get("direction_only_cases")
        if isinstance(total, int) and isinstance(direction, int):
            if total + direction != len(cases):
                problems.append(
                    f"_meta.total_cases+direction_only_cases={total + direction} "
                    f"≠ 实际案例数 {len(cases)}——_meta 与实际文件分家")
        else:
            problems.append("_meta 缺少 total_cases／direction_only_cases，无法核对案例数")

    for field, rule in spec["fields"].items():
        non_ids = [str(c.get("id") or "") for c in cases
                   if _nonempty((c.get("expected") or {}).get(field))]
        minimum = int(rule["min"])
        if len(non_ids) < minimum:
            problems.append(f"{field} 非空 {len(non_ids)} < 登记下限 {minimum}"
                            f"——该字段被整批清空或回退")

        allowed_blank = rule.get("allowed_blank")
        if allowed_blank is not None:
            extras = sorted(set(ids) - set(non_ids) - set(allowed_blank))
            if extras:
                problems.append(f"{field} 出现未登记空值：{extras}（空白 ID 必须逐条登记）")

        allowed_values = rule.get("allowed_values")
        if allowed_values is not None:
            bad = sorted({str((c.get("expected") or {}).get(field))
                          for c in cases
                          if _nonempty((c.get("expected") or {}).get(field))}
                         - set(allowed_values))
            if bad:
                problems.append(f"{field} 出现未登记取值：{bad}（不得用任意字符串凑计数）")

    return problems


def load() -> tuple[dict, dict]:
    return (json.loads((DISC / "data" / "cases" / "wikisource_cases.json").read_text(encoding="utf-8")),
            json.loads(REG.read_text(encoding="utf-8")))


def selftest(real: dict, registry: dict) -> list[str]:
    """§四.8 负例自证：故意破坏登记，门必须判红；完好数据必须放行。"""
    fails: list[str] = []

    def must_catch(label: str, mutate) -> None:
        broken = copy.deepcopy(real)
        mutate(broken)
        got = audit(broken, registry)
        if not got:
            fails.append(f"负例未抓到：{label}")

    must_catch("整批清空 use_god", lambda d: [c.setdefault("expected", {}).__setitem__("use_god", "")
                                              for c in d["cases"]])
    must_catch("单例未登记空值", lambda d: d["cases"][0].setdefault("expected", {}).__setitem__("use_god", ""))
    must_catch("use_god 乱写取值", lambda d: d["cases"][0].setdefault("expected", {}).__setitem__("use_god", "乱写"))
    must_catch("删掉一例", lambda d: d["cases"].pop())
    must_catch("清空 use_god_note", lambda d: [c.setdefault("expected", {}).pop("use_god_note", None)
                                               for c in d["cases"]])

    if audit(real, registry):
        fails.append("完好夹具被误伤——本门自身口径有误")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser(description="expected 覆盖生存线（门禁 [38]）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    real, registry = load()
    spec = registry["cases"]["wikisource_cases.json"]
    problems = audit(real, registry)
    print("expected 覆盖生存线对拍：")
    for field, rule in spec["fields"].items():
        n = sum(1 for c in real.get("cases") or []
                if _nonempty((c.get("expected") or {}).get(field)))
        print(f"  · {field:<20} {n:>3}/{len(real.get('cases') or [])}（下限 {rule['min']}）")
    for p in problems:
        print("  ×", p)
    if not problems:
        print("  √ 案例数与受控字段非空数均不低于登记下限，空值/取值均在册")

    st_fail: list[str] = []
    if args.selftest:
        st_fail = selftest(real, registry)
        print(f"  [selftest] 负例{'全部抓到' if not st_fail else '失效'}"
              "（5 类：整批清空／未登记空值／乱写取值／删例／清空 note）")
        for p in st_fail:
            print("  ×", p)

    if problems or st_fail:
        return 1
    print("expected 覆盖生存线门通过。解锁＝同批更新 data/rules/expected_coverage.json 与 docs/CHANGELOG.md。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
