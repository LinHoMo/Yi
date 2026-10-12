# -*- coding: utf-8 -*-
"""回归 fixture 不变量门：注释/声明里的干支与卦名，必须由日期和爻数组**算得出来**。

为什么需要它（2026-10-10 校勘）：`tests/regression_test.py` 的 18 例里，
按旧写法（干支只出现在注释散文里）**6 例的 date 算不出注释自己声明的月建/日辰**，
另有 4 例注释写的卦名与 yao 数组派生出来的不一致。最严重的两条：
  · `reg_01` 引《增删卜易》源L532「辰月戊申日占父近病，得乾为天变天小畜」，
    而 fixture 用的是**全 7 静卦**（根本没有动爻，也就没有"变卦"），
    日期 2024-05-10 实算**巳月甲戌日**——本例立论的「辰土父母临月建」与
    「申日冲寅木而暗动」两条前提同时失效；
  · `reg_18` 注释写「风雷益六合」，数组派生出来是**乾为天（六冲卦）**，
    兄弟持世求财忌六冲，注释与数组的语义正好相反。
这类假基准只会表现为"引擎回归不过"，然后诱人去改引擎。本门把它拦在 fixture 侧。

    python dev_tools/check_fixture_invariants.py            # 全量对账
    python dev_tools/check_fixture_invariants.py --selftest # 负例：假干支/假卦名必须被抓

口径：
  · 只判**声明了** `classical_ganzhi` / `expected_hexagrams` 的案例；未声明的计入
    "未检视"并报数（0 声明 = 本门没跑，判失败）；
  · 干支用内核 `ganzhi_of()` 实算（含节气交节），不比字符串近似；
  · 卦名用 `HEXAGRAM_TRIGRAMS`/`BAGUA_LINES` 反查，与 `case_runner.hex_lines` 同一张表，
    避免第二套真值源。
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from datetime import datetime
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DISC / "scripts"))
sys.path.insert(0, str(DISC / "core"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from yishu_core.symbols import BAGUA_LINES, HEXAGRAM_TRIGRAMS  # noqa: E402
from yishu_core.ganzhi_calendar import ganzhi_of  # noqa: E402

_REVERSE: dict[tuple, list[str]] = {}
for _n, (_up, _low) in HEXAGRAM_TRIGRAMS.items():
    _REVERSE.setdefault(tuple(BAGUA_LINES[_low] + BAGUA_LINES[_up]), []).append(_n)


def name_of(lines: tuple) -> str:
    got = _REVERSE.get(lines)
    return got[0] if got else "?"


def derived_hexagrams(yao: list) -> tuple:
    base = tuple(1 if y in (7, 9) else 0 for y in yao)
    moving = [i for i, y in enumerate(yao) if y in (6, 9)]
    if not moving:
        return (name_of(base),)
    chg = tuple((0 if b == 1 else 1) if yao[i] in (6, 9) else b
                for i, b in enumerate(base))
    return (name_of(base), name_of(chg))


def load_cases():
    spec = importlib.util.spec_from_file_location(
        "rt", str(DISC / "tests" / "regression_test.py"))
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except SystemExit:
        pass
    return list(getattr(m, "REGRESSION_CASES", []))


def check_case(c) -> list[str]:
    problems: list[str] = []
    gz = str(getattr(c, "classical_ganzhi", "") or "")
    if gz:
        d = datetime(*list(c.date)[:3])
        gm = ganzhi_of(d)
        mb = str(getattr(gm, "month_branch", "") or "")
        dg = str(getattr(gm, "day_ganzhi", "") or "")
        want_m = gz[0] if gz and gz[1:2] == "月" else ""
        want_d = gz[2:4] if want_m else ""
        if want_m and mb != want_m:
            problems.append(f"{c.id}：声明月建「{want_m}月」，但 date={c.date} 实算为「{mb}月」")
        if want_d and dg != want_d:
            problems.append(f"{c.id}：声明日辰「{want_d}日」，但 date={c.date} 实算为「{dg}日」")
    hx = tuple(getattr(c, "expected_hexagrams", ()) or ())
    if hx:
        got = derived_hexagrams(list(c.yao))
        # 注释往往只写本卦（"引擎: 火风鼎"），声明几项就只核几项，不逼人造出变卦名
        if len(hx) > len(got) or tuple(hx) != got[:len(hx)]:
            problems.append(f"{c.id}：声明卦名{tuple(hx)}，但 yao={list(c.yao)} 派生为{got}")
    dm = tuple(getattr(c, "declared_moving", ()) or ())
    if dm:
        got_mv = tuple(i + 1 for i, y in enumerate(c.yao) if y in (6, 9))
        if dm != got_mv:
            problems.append(f"{c.id}：声明动爻{dm}，但 yao={list(c.yao)} 算出的是{got_mv}")
    return problems


def selftest(cases, problems: list[str]) -> None:
    """负例：把 reg_01 的日期换回校勘前那个"巳月甲戌日"，本门必须报两条。"""
    good = [c for c in cases if getattr(c, "classical_ganzhi", "")
            and getattr(c, "expected_hexagrams", ())]
    if not good:
        problems.append("负例自证无法执行：没有任何案例声明了干支/卦名")
        return
    base = good[0]
    fake = base._replace(date=(2024, 5, 10, 10))
    hits = check_case(fake)
    if len(hits) < 2:
        problems.append(f"负例失效：把日期换成校勘前的假干支，只抓到 {len(hits)} 条"
                        f"（应同时抓到月建与日辰两条）→ {hits}")
    hx0 = tuple(getattr(base, "expected_hexagrams", ()) or ())
    if not hx0:
        problems.append("负例自证无法执行：声明卦名的第一条案例其实没有卦名")
        return
    fake2 = base._replace(expected_hexagrams=hx0 + ("未济",))
    if not any("派生为" in x for x in check_case(fake2)):
        problems.append("负例失效：声明一个不存在的变卦名没被抓到")
    mv = [c for c in cases if getattr(c, "declared_moving", ())]
    if not mv:
        problems.append("负例自证无法执行：没有案例声明动爻，动爻这一维等于没跑")
    else:
        b0 = mv[0]
        bad_mv = b0._replace(declared_moving=tuple(x + 1 for x in b0.declared_moving))
        if not any("声明动爻" in x for x in check_case(bad_mv)):
            problems.append("负例失效：把声明动爻整体挪一位没被抓到——动爻对账形同虚设")
    print("  [selftest] 负例已跑（假干支两条 / 假卦名一条 / 假动爻一条）")


def main() -> int:
    ap = argparse.ArgumentParser(description="回归 fixture 干支/卦名不变量对账")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    cases = load_cases()
    if not cases:
        print("× 读不到 REGRESSION_CASES——本门等于没跑，不判通过")
        return 1
    problems: list[str] = []
    declared = 0
    for c in cases:
        if getattr(c, "classical_ganzhi", "") or getattr(c, "expected_hexagrams", ()):
            declared += 1
        problems.extend(check_case(c))
    if args.selftest:
        selftest(cases, problems)
    mv_n = sum(1 for c in cases if getattr(c, "declared_moving", ()))
    print(f"  对账：{declared}/{len(cases)} 例声明了干支或卦名、{mv_n}/{len(cases)} 例声明了动爻"
          f"（其余未声明，不计入已验）")
    if declared == 0:
        print("× 0 例声明——本门无从对账，不判通过")
        return 1
    for p in problems:
        print(f"  × {p}")
    if not problems:
        print("  √ 声明的月建/日辰与 date 实算一致，声明的卦名与 yao 派生一致，声明的动爻与数组一致")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
