# -*- coding: utf-8 -*-
"""命例基准自洽审计（六爻科 `[16]` 的八字科等价物，2026-10-11 第八批）。

要防的事很具体：**基准本身没人验过**。八字科的案例把书上的四柱抄在 `note`
（「书源命例四柱 丙午/庚寅/丙午/庚寅」），再另存一个公历 `datetime` 让内核反算。
两套记载一旦漂移——日期反查错、时区/立春分界口径不同、干支誊抄串行——
所有对齐分都是在跟一个**并不存在的命盘**比，而报表上一个字都不会提示。
六爻科有 `[16] 案例基准自洽`（各例的日辰与应期支须出自其自引书文），
八字科此前只有 `pillars_raw` 两例带书载四柱，其余无人对账。

    python dev_tools/check_case_pillars.py            # 全量对账
    python dev_tools/check_case_pillars.py --verbose  # 连未计入的例一起列
    python dev_tools/check_case_pillars.py --selftest # 负例：改坏一例必须被抓、正例不误伤

判定口径（AGENTS.md §三.4：不许用引擎输出反推 expected，故这里**只用书载值当基准**，
内核值算作"被审的一方"）：
  · 书载四柱（note 或 pillars_raw）＋ datetime 可算 → 计入对账，四柱逐位相等才 PASS
  · 书上没写四柱的例 → 显式记"不计入已验"，不冒充已验，也不算失败
  · 一条都没对账 → 本器自报失败，绝不当通过
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DISC / "scripts"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GZ = re.compile(r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]")
# note 里"书载四柱"的写法不统一：书源命例四柱 / 原局四柱 / 四柱：，都算书载值
BOOK_MARK = re.compile(r"(书源命例四柱|原局四柱|四柱[:：])\s*"
                       r"([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]"
                       r"(?:\s*[/、，,]\s*[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]){3})")
POS_KEYS = ("年", "月", "日", "时")


def engine_four(dt_str: str, gender: str) -> list[str]:
    """内核按 datetime 反算的四柱（年/月/日/时），失败返回空表。"""
    import chart as C  # noqa: PLC0415  延迟导入：让 --selftest 在无内核环境下也能单独跑
    r = C.chart(datetime_str=dt_str, gender=gender or "男")
    four = r.get("四柱") or r.get("pillars") or {}
    out = []
    for k in POS_KEYS:
        v = four.get(k)
        out.append(v if isinstance(v, str) else (v or {}).get("ganzhi", ""))
    if not all(out):  # 英文键位兜底，避免换了字段名就静默少验
        en = [("year", "month", "day", "hour")]
        for tup in en:
            alt = [four.get(x) for x in tup]
            alt = [a if isinstance(a, str) else (a or {}).get("ganzhi", "") for a in alt]
            if all(alt):
                return alt
    return out


def book_four(case: dict) -> tuple[list[str], str]:
    """该例**书上自己写的**四柱；返回 (四位或空表, 出处字段)。"""
    raw = case.get("pillars_raw")
    if isinstance(raw, dict):
        vals = [raw.get(k) if isinstance(raw.get(k), str) else
                (raw.get(k) or {}).get("ganzhi", "") for k in POS_KEYS]
        if all(vals):
            return vals, "pillars_raw"
    m = BOOK_MARK.search(case.get("note") or "")
    if m:
        return GZ.findall(m.group(2))[:4], "note"
    return [], ""


def audit(cases: list[dict], problems: list[str], rows: list[str]) -> tuple[int, int, int]:
    """返回 (可对账例数, 一致例数, 书载四柱缺失例数)。"""
    checked = agreed = no_book = 0
    for c in cases:
        cid = c.get("id") or "?"
        dt = (c.get("pillars") or {}).get("datetime") or c.get("datetime") or ""
        if not dt:
            rows.append(f"  · {cid}：无 datetime，无法反算四柱，不计入已验")
            continue
        bf, src = book_four(c)
        if len(bf) != 4:
            no_book += 1
            rows.append(f"  · {cid}：书上未写四柱（只给了日期），不计入已验")
            continue
        try:
            ef = engine_four(dt, c.get("gender") or "")
        except Exception as exc:
            problems.append(f"{cid}：内核反算四柱失败 {type(exc).__name__}: {str(exc)[:80]}")
            continue
        checked += 1
        if ef == bf:
            agreed += 1
        else:
            problems.append(f"{cid}：基准不自洽——书载（{src}）{('/'.join(bf))} "
                            f"vs 内核按 {dt} 算得 {('/'.join(ef or ['?']*4))}")
    return checked, agreed, no_book


def selftest(problems: list[str]) -> None:
    """两件：把书载值改坏必须判错（有牙齿）；正例不得误伤（不假阳性）。"""
    good = {"id": "ST_OK", "pillars": {"datetime": "1966-02-16 03:30"}, "gender": "男",
            "note": "书源命例四柱 丙午/庚寅/丙午/庚寅；示例"}
    bf, src = book_four(good)
    if len(bf) != 4 or src != "note":
        problems.append(f"负例自证：书载四柱抽取失效 → {bf}｜{src}")
        return
    bad = dict(good)
    bad["note"] = "书源命例四柱 甲子/乙丑/丙寅/丁卯；故意写坏的一例"
    sub_p: list[str] = []
    rows: list[str] = []
    _c, _a, _n = audit([bad], sub_p, rows)
    if not any("基准不自洽" in x for x in sub_p):
        problems.append(f"负例自证失效：改坏书载四柱没被抓到 → {sub_p}")
    sub_p2: list[str] = []
    c2, a2, _n2 = audit([good], sub_p2, rows)
    if sub_p2 or c2 != 1 or a2 != 1:
        problems.append(f"负例自证假阳性：正例被判错或未计入 → {sub_p2}｜计{c2}中{a2}")


def main() -> int:
    ap = argparse.ArgumentParser(description="八字科命例基准自洽审计")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    problems: list[str] = []
    rows: list[str] = []
    cases: list[dict] = []
    for p in sorted((DISC / "data" / "cases").glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(f"{p.name} 解析失败 {type(exc).__name__}")
            continue
        cs = d if isinstance(d, list) else (d.get("cases") or [])
        for c in cs:
            if isinstance(c, dict):
                c["_file"] = p.name
                cases.append(c)

    checked, agreed, no_book = audit(cases, problems, rows)

    if args.selftest:
        selftest(problems)
        print("  [selftest] 负例已跑（改坏书载值 / 正例不误伤）")

    print(f"合计：案例 {len(cases)} 例，其中 {checked} 例书上写了四柱可对账，"
          f"{agreed} 例与内核反算一致，{no_book} 例无书载四柱（不计入已验）；"
          f"{len(problems)} 条判红")
    if checked == 0:
        print("× 0 例被真正对账——本器等于没跑，不判通过")
        return 1
    if args.verbose:
        for r in rows[:40]:
            print(r)
    elif len(rows) > 0:
        print(f"  （另有 {len(rows)} 条例外说明，--verbose 查看）")
    for x in problems:
        print(f"  × {x}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
