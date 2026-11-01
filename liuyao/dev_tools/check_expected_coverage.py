# -*- coding: utf-8 -*-
"""expected 书证/机械派生字段的覆盖生存线（门禁 [38]，第三百四十四批新增；419 批扩到 dz／bushi，425 批补 yiin）。

    python dev_tools/check_expected_coverage.py            # 对拍真实案例文件
    python dev_tools/check_expected_coverage.py --selftest # 加负例：证明本门抓得住

为什么需要它：案例构建器（`fetch_wikisource_cases.py`／`build_zengshan_dz_cases.py` 等）
重生成时只写自动解析字段，不会保留人工补的 `expected.use_god`／`use_god_branch`／
`use_god_note`／`use_god_wangshuai` 等书证与机械派生字段。1592923（易隐批）就是这样把
292/297/298/282 批的 74 个 use_god、52 个 branch、32 个 note、3 组
wangshuai-muku-six_spirit 和 WS035 校勘 verdict 一次性清空；聚合 strict 只从
75.8 掉到 69.8，所有既有门仍然全绿——**分数掉一点不等于标签还在**。

**419 批为什么扩到 dz／bushi**：403 批把 dz 建器扩样到 29 例时，重生成把
206／208 批逐条书证校勘的 18 例 `use_god`／`use_god_branch`／`use_god_note`
（ZD188 另有 `yingqi_note`）整段清空；当时的 [38] 只扫 wikisource，dz 读数从
57.4 级别悄悄回到 53 级别却无门报警。生存线须覆盖**每一个有建器的案例文件**，
否则同一事故换个集就能重演。

**425 批为什么补 yiin**：423 批给该集补了 4 条实录应期（7→11），但它的 expected
字段没有任何生存线；构建器重生成把 `yingqi`／`yingqi_branches` 清空不会有门报警。
该集没有 `use_god`，受控字段是 `yingqi`（≥11）、`yingqi_branches`（≥11）、
`yingqi_claim`（≥5）、`detail`（≥56），并用 `allowed_values: []` 把 `verdict` 钉死
在 null（本书断语是散文，映射吉/凶属解读）。

本门守三条：
  A. 案例数不得低于登记数（整文件重生成丢例即红）；
  B. 每个受控字段的非空数不得低于登记下限（整批清空即红）；
  C. 登记了 `allowed_blank` 的字段，空值 ID 必须逐条列名；出现未登记空值即红。
  登记了 `allowed_values` 的字段另校验取值集合，防止用任意字符串把计数凑回去。
  selftest 按各集**在册字段**注入负例（不再假定每集都有 `use_god`）。

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


def audit(data: dict, spec: dict) -> list[str]:
    """对拍一份案例 JSON 与其覆盖登记；返回问题清单（空＝通过）。"""
    problems: list[str] = []
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
    reg = json.loads(REG.read_text(encoding="utf-8"))
    data = {name: json.loads((DISC / "data" / "cases" / name).read_text(encoding="utf-8"))
            for name in reg["cases"]}
    return data, reg


def _blank_first_nonempty(data: dict, field: str = "use_god") -> None:
    for c in data["cases"]:
        if _nonempty((c.get("expected") or {}).get(field)):
            c.setdefault("expected", {})[field] = ""
            return


def selftest(data_by_file: dict, registry: dict) -> list[str]:
    """§四.8 负例自证：每个受控文件都故意破坏一次，门必须判红；完好数据必须放行。"""
    fails: list[str] = []

    def must_catch(label: str, name: str, mutate) -> None:
        broken = copy.deepcopy(data_by_file[name])
        mutate(broken)
        got = audit(broken, registry["cases"][name])
        if not got:
            fails.append(f"负例未抓到（{name}）：{label}")

    for name, spec in registry["cases"].items():
        fields = spec["fields"]
        data = data_by_file[name]

        def count(field: str, d: dict = data) -> int:
            return sum(1 for c in d["cases"]
                       if _nonempty((c.get("expected") or {}).get(field)))

        # 代表字段：优先 use_god（原有受控文件），否则取第一个有下限的字段。
        # YIIN 没有 use_god，代表字段是 yingqi（11 条实录）——425 批扩围。
        probe = ("use_god" if int(fields.get("use_god", {}).get("min", 0)) > 0
                 else next((f for f, r in fields.items() if int(r["min"]) > 0), None))
        if probe:
            must_catch(f"整批清空 {probe}", name,
                       lambda d, f=probe: [c.setdefault("expected", {}).__setitem__(f, "")
                                           for c in d["cases"]])
            # 单例置空：非空数已等于下限时，置空一个必跌破；有余量则跳过（不制造假负例）
            if count(probe) <= int(fields[probe]["min"]):
                must_catch(f"单例置空 {probe}", name,
                           lambda d, f=probe: _blank_first_nonempty(d, f))
        val_field = next((f for f, r in fields.items()
                          if r.get("allowed_values") is not None), None)
        if val_field is not None:
            must_catch(f"{val_field} 乱写取值", name,
                       lambda d, f=val_field: d["cases"][0].setdefault("expected", {}).__setitem__(f, "乱写"))
        must_catch("删掉一例", name, lambda d: d["cases"].pop())
        if "use_god_note" in fields:
            must_catch("清空 use_god_note", name,
                       lambda d: [c.setdefault("expected", {}).pop("use_god_note", None)
                                  for c in d["cases"]])
        if "detail" in fields:
            must_catch("整批清空 detail", name,
                       lambda d: [c.setdefault("expected", {}).__setitem__("detail", "")
                                  for c in d["cases"]])
        if audit(data_by_file[name], spec):
            fails.append(f"完好夹具被误伤（{name}）——本门自身口径有误")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser(description="expected 覆盖生存线（门禁 [38]）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    data_by_file, registry = load()
    problems: list[str] = []
    cases_total = 0
    notes = []
    print("expected 覆盖生存线对拍：")
    for name, spec in registry["cases"].items():
        data = data_by_file[name]
        cases = data.get("cases") or []
        cases_total += len(cases)
        # 非 wikisource 的字段名加 `dz.`／`bushi.` 前缀：账台 readout_ledger 的
        # `liuyao.expected_coverage` 只认 wikisource 段（旧正则按 `·` 直接取名字），
        # 前缀带点号即不与之相撞，同时让多集输出可读。
        prefix = f"{spec['label']}." if spec.get("label") else ""
        for field, rule in spec["fields"].items():
            n = sum(1 for c in cases if _nonempty((c.get("expected") or {}).get(field)))
            print(f"  · {prefix + field:<20} {n:>3}/{len(cases)}（下限 {rule['min']}）")
        notes.append(f"{spec.get('label') or name} {len(cases)} 例")
        ps = audit(data, spec)
        for p in ps:
            print(f"  × [{name}]", p)
        problems += [f"[{name}] {p}" for p in ps]
    if not problems:
        print(f"  √ {len(registry['cases'])} 个受控文件（{'／'.join(notes)}）案例数与受控字段"
              "非空数均不低于登记下限，空值/取值均在册")

    st_fail: list[str] = []
    if args.selftest:
        st_fail = selftest(data_by_file, registry)
        print(f"  [selftest] 负例{'全部抓到' if not st_fail else '失效'}"
              "（按各集在册字段注入：整批清空/单例/坏取值/删例，note·detail 在册即测）")
        for p in st_fail:
            print("  ×", p)

    if problems or st_fail:
        return 1
    print("expected 覆盖生存线门通过。解锁＝同批更新 data/rules/expected_coverage.json 与 docs/CHANGELOG.md。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
