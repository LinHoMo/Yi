# -*- coding: utf-8 -*-
"""案例库自洽门：一条案例的「日辰 / 应期」必须与它**自己引用的那段书文**一致。

为什么需要它（2026-10-10 校勘）：`huozhulin_holdout` 只有 2 例，实测两例都是坏的——
  · HZL001 把《火珠林》源L458（癸亥日占坎之蒙、断**晴**）与源L459（甲辰日占乾之大壮、
    **申时**雷雨）拼成一条：date/topic 来自前一条，卦与应期来自后一条；
  · HZL002 的 expected.yingqi「甲寅日」取自「九二甲寅财动」——那是**动爻**不是验期，
    书上唯一验期在源L581「直待午火官，辰土印绶年可求」，还是**双列**（午或辰）。
抓取器在段落归属失败时标 `section="__trailing__"`，上下文窗口于是串到邻条。
**串档不会被任何现有门发现**，只表现为"外部落分很低"，然后逼人去看引擎——
本门把"基准自身是否自洽"变成红线：基准坏了先修基准，不动引擎去凑分。

    python dev_tools/check_case_selfconsistency.py            # 全量对账
    python dev_tools/check_case_selfconsistency.py --selftest # 负例：串档必须被抓到
    python dev_tools/check_case_selfconsistency.py --verbose  # 看信息性 NOTE

判定口径（为什么这样判，第一版的假红都在这儿）：
  · 只判"案例自己引用了书文片段"的条目（`provenance.context_head` / `wikitext_head`）；
    没有自引书文的（classical_cases、yingqi_cases）不计入已验，并报出条数；
  · **判据只用干支，不用整句**：底本多作繁体（大壯／離／粵東帶貨），而片段是抓取时
    把 `<br>` 归一成换行的产物，拿整句回底本找必然假红——本器第一版就是这样
    一口气报出 8 条"片段在底本里找不到"。干支与地支繁简同形，"日辰""应期支"
    两类判据因此是**字符安全**的；
  · 片段里写明日辰而 `input.date` 是另一个日子 → 判红（串档的直接特征）；
  · `expected.yingqi` 的支在片段与断语里都不出现 → 判红（把动爻/别条的字当验期）；
  · 卦名与"片段可定位性" → 只记不判（繁简与标记差异不足以支撑硬约束，如实降级）；
  · 双列验期的正确处置是 expected 置空（评测按 N/A 剔除），不硬选一个当基准。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CASE_DIR = DISC / "data" / "cases"
SETS = ("wikisource_cases.json", "huozhulin_cases.json", "yingqi_cases.json",
        "classical_cases.json")
GZ = "甲乙丙丁戊己庚辛壬癸"
BRS = "子丑寅卯辰巳午未申酉戌亥"
DAY_RE = re.compile(f"[{GZ}][{BRS}]日")
BR_RE = re.compile(f"[{BRS}]")
NOTE: list[str] = []


def book_text(case: dict) -> str:
    """该案例**自己引用**的书文片段；没有就返回空串（→ 不计入已验）。"""
    pv = case.get("provenance") or {}
    return str(pv.get("context_head") or pv.get("wikitext_head") or "")


def check_case(case: dict) -> tuple[int, list[str]]:
    """返回 (本例命中的判据数, 判红清单)。纯函数：负例可以直接喂构造数据。"""
    frag = book_text(case)
    if not frag:
        return 0, []
    cid = case.get("id", "?")
    problems: list[str] = []
    checked = 1                                   # 有自引书文，本身算一条
    inp = case.get("input") or {}
    cited_days = DAY_RE.findall(frag)
    dm = DAY_RE.search(str(inp.get("date") or ""))

    if dm and cited_days:                         # ① 日辰必须与自引片段一致
        checked += 1
        if len(set(cited_days)) > 1:
            NOTE.append(f"{cid}：自引片段里有 {len(set(cited_days))} 个不同日辰"
                        f"{sorted(set(cited_days))}，出处窗口不唯一——只记不判")
        elif dm.group(0) not in cited_days:
            problems.append(f"{cid}：自引书文片段里写的是「{cited_days[0]}」，"
                            f"而 input.date 是「{dm.group(0)}」——两条占验被拼成一条")

    yq = (case.get("expected") or {}).get("yingqi")
    if yq:                                        # ② 应期支必须出现在片段或断语里
        checked += 1
        brs = BR_RE.findall(str(yq))
        hay = frag + str((case.get("expected") or {}).get("detail") or "")
        if brs and not any(b in hay for b in brs):
            problems.append(f"{cid}：应期「{yq}」的支{brs}在自引片段与断语里都不出现"
                            f"——多半是把动爻或别条的字当成了验期")

    hx = case.get("hexagram") or {}               # ③ 卦名：繁简差异不足以硬判
    for label, nm in (("本卦", str(hx.get("original") or "")),
                      ("变卦", str(hx.get("changed") or ""))):
        if nm and nm not in frag:
            NOTE.append(f"{cid}：{label}「{nm}」未以简体形出现在片段里（底本多繁体，只记不判）")
    return checked, problems


def load_sets() -> list[tuple[str, dict]]:
    out: list[tuple[str, dict]] = []
    for name in SETS:
        p = CASE_DIR / name
        if not p.exists():
            NOTE.append(f"{name}：文件不存在，本门未检视该集")
            continue
        for c in (json.loads(p.read_text(encoding="utf-8")).get("cases") or []):
            out.append((name, c))
    return out


def selftest(problems: list[str], examined: int) -> None:
    """负例＝HZL001 校勘**前**的真实状态；正例＝校勘后；再加"无书文不算已验"。"""
    head = ("又问：壬癸动雨要言克日定时取验，何如?曰：如六月甲辰日占雨得乾之大壮，"
            "当日申时雷雨骤至，此壬癸克日定时")

    def mk(day: str) -> dict:
        return {"id": f"NEG_{day}", "input": {"date": day},
                "hexagram": {"original": "乾", "changed": "大壮"},
                "expected": {"yingqi": "申时", "detail": head},
                "provenance": {"context_head": head}}

    if not check_case(mk("癸亥日"))[1]:
        problems.append("负例失效：把日辰换成邻条的「癸亥日」没被判红")
    if check_case(mk("甲辰日"))[1]:
        problems.append("负例假阳性：日辰与自引片段一致的条目也被判红，判据不成立")
    ghost = {"id": "NEG_无书文", "input": {"date": "甲子日"},
             "hexagram": {"original": "乾"}, "expected": {"yingqi": "午日"}}
    if check_case(ghost)[0] != 0:
        problems.append("没有自引书文的条目被算成了已检视")
    if examined == 0:
        problems.append("全量 0 条被检视，本门等于没跑")
    print("  [selftest] 负例已跑（串档 / 一致 / 无书文三件）")


def main() -> int:
    ap = argparse.ArgumentParser(description="案例库 日辰/应期 与自引书文的同源自洽门")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--verbose", action="store_true", help="打印信息性 NOTE")
    args = ap.parse_args()

    problems: list[str] = []
    examined = skipped = 0
    for name, c in load_sets():
        n, ps = check_case(c)
        examined += 1 if n else 0
        skipped += 0 if n else 1
        problems.extend(f"[{name}] {x}" for x in ps)
    print(f"  对账：{examined} 例有自引书文可判，{skipped} 例无书文（不计入已验）")
    if args.selftest:
        selftest(problems, examined)
    if args.verbose:
        for x in NOTE[:20]:
            print(f"  · {x}")
    elif NOTE:
        print(f"  · 另有 {len(NOTE)} 条信息性提示（卦名繁简/片段多日辰等），--verbose 查看")
    for p in problems:
        print(f"  × {p}")
    if examined == 0:
        print("× 0 例可检视——本门等于没跑，不判通过")
        return 1
    if not problems:
        print("  √ 各例的日辰与应期支均出自其自引书文（基准自洽）")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
