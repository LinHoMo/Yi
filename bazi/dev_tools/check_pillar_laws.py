# -*- coding: utf-8 -*-
"""排盘入参的**历法自洽**回验：五虎遁·五鼠遁（不依赖 datetime，2026-10-11 第一百二十三批）。

要防的事：基准里存的四柱本身可能是**历法上不可能的盘**。`[17] 命例基准自洽` 走的是
「书载四柱 == 内核按 datetime 反算」，**它要求例子里有 datetime**；于是只给结构化四柱、
没给日期的例（实测 116 例走 `pillars` 字典这一路）一直落在该门的可见范围之外——
门自报的「不计入已验」是诚实的，但整批例的入参质量于是无人过账。

本器补的正是这一格：**不看日期，只看四柱内部是否自洽**。两条律都是历法恒等式，
与任何一书的口径无关，也不与引擎输出比对（AGENTS.md §三.4 不许用引擎输出回填基准；
这里被审的是**基准自身**，用的是内核的遁表这一独立真值源）：

  · 五虎遁：月干 = f(年干, 月支) —— `ming_tables._stem_by_tiger`
  · 五鼠遁：时干 = f(日干, 时支) —— `ganzhi_calendar.RAT_HOUR_STEM`

判据分三档，不合并：
  合律            → 计入已验
  违律且**未登记** → 判红（新出现的不可能盘必须挡在门外）
  违律且**已登记** → NOTE 可见，不判红：书自己写的两个字相背，我们不替书改写，
                     也不许这条豁免无声扩大（每条须带出处摘录；该例若日后合规，本器反向判红）

    python dev_tools/check_pillar_laws.py             # 全量
    python dev_tools/check_pillar_laws.py --verbose   # 连合律例的取源分布一起看
    python dev_tools/check_pillar_laws.py --selftest  # 负例：改坏一处必须被抓／登记例不误伤
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DISC / "core"))

from yishu_core.ganzhi_calendar import HEAVENLY_STEMS, EARTHLY_BRANCHES, RAT_HOUR_STEM  # noqa: E402
from yishu_core.ming_tables import _stem_by_tiger  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GZ = re.compile(r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]")
CN = ("年", "月", "日", "时")
EN = ("year", "month", "day", "hour")
BOOK_MARK = re.compile(r"(书源命例四柱|原局四柱|四柱[:：])\s*"
                       r"([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]"
                       r"(?:\s*[/、，,]\s*[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]){3})")

# 书内冲突登记（**逐字出处摘录为义务**，无出处的条目本器直接判红）：
# 这两例的四柱是书文明确写出来的，违律的是**书的记载本身**，不是我们的誊抄。
# 按 §三.4「书载值当基准、引擎值是被审的一方」，此处既不覆写书值，也不把它藏进通过数。
BOOK_CONFLICTS = {
    "ZC014": {
        "quote": "辛金生于孟春，天干丙丁庚辛阴阳相克，且金绝火生，地支寅木当令",
        "why": "书载年柱 丁卯 而月柱 丙寅；五虎遁丁年寅月当起壬寅，丙寅乃丙/辛年之寅月，"
               "书文两处干支自相背（滴天髓阐微·下篇·假从，任铁樵注例）",
    },
    "ZP021": {
        "quote": "禄劫用财，须带食伤……如甲子、丙子、癸丑、壬辰，张都统命是也",
        "why": "书载日柱 癸丑 而时柱 壬辰；五鼠遁戊癸日起壬子，辰时当为丙辰，"
               "壬辰须丁/壬日（子平真诠评注·第45章 论建禄月劫）",
    },
}


def four_from_case(c: dict) -> tuple[list[str], str]:
    """基准里存的四柱：`pillars`／`pillars_raw`（dict 或空格串）／note 书载值，任一来源。"""
    holders = ("pillars", "pillars_raw")
    for keyset in (EN, CN):
        for h in holders:
            v = c.get(h)
            if isinstance(v, dict):
                got = [v.get(k) if isinstance(v.get(k), str) else
                       (v.get(k) or {}).get("ganzhi", "") for k in keyset]
                if all(got):
                    return got, f"{h}/{keyset[0]}"
    v = c.get("pillars_raw")
    if isinstance(v, str):
        m = GZ.findall(v)
        if len(m) == 4:
            return m, "pillars_raw/str"
    m = BOOK_MARK.search(c.get("note") or "")
    if m:
        g = GZ.findall(m.group(2))
        if len(g) == 4:
            return g, "note"
    return [], ""


def law_errors(four: list[str]) -> list[str]:
    """两条历法恒等式；返回违律说明（空表＝合律）。"""
    if len(four) != 4 or any(len(x) != 2 for x in four):
        return ["四柱形态不合（非两位干支）"]
    ys, ms, ds, hs = (x[0] for x in four)
    yb, mb, db, hb = (x[1] for x in four)
    out = []
    if any(s not in HEAVENLY_STEMS for s in (ys, ms, ds, hs)) or \
       any(b not in EARTHLY_BRANCHES for b in (yb, mb, db, hb)):
        return ["干支不在内核表内"]
    exp_m = _stem_by_tiger(ys, mb)
    if exp_m != ms:
        out.append(f"五虎遁：年干{ys}＋月支{mb}⇒月干应为{exp_m}，实为{ms}")
    idx = (RAT_HOUR_STEM[ds] + EARTHLY_BRANCHES.index(hb)) % 10
    exp_h = HEAVENLY_STEMS[idx]
    if exp_h != hs:
        out.append(f"五鼠遁：日干{ds}＋时支{hb}⇒时干应为{exp_h}，实为{hs}")
    return out


def audit_laws(cases: list[dict], problems: list[str], rows: list[str],
               check_orphans: bool = False) -> dict:
    """返回 {可检, 合律, 登记冲突, 取源分布}。"""
    st = {"可检": 0, "合律": 0, "登记冲突": 0, "取源": {}}
    seen_conflict = set()
    for c in cases:
        cid = str(c.get("id") or "?")
        four, src = four_from_case(c)
        if len(four) != 4:
            continue
        st["可检"] += 1
        st["取源"][src] = st["取源"].get(src, 0) + 1
        errs = law_errors(four)
        if not errs:
            st["合律"] += 1
            if cid in BOOK_CONFLICTS:
                problems.append(f"{cid}：豁免清单条目已失效——该例现合律，"
                                f"请从 BOOK_CONFLICTS 删除（防豁免无声扩大）")
            continue
        if cid in BOOK_CONFLICTS:
            reg = BOOK_CONFLICTS[cid]
            if not reg.get("quote"):
                problems.append(f"{cid}：违律且豁免条目**无逐字出处**，不认这条豁免")
            else:
                st["登记冲突"] += 1
                seen_conflict.add(cid)
                rows.append(f"  NOTE {cid}（{src}）{'/'.join(four)}：{'；'.join(errs)}"
                            f" ⟵ 书内冲突已登记，出处「{reg['quote'][:40]}…」；{reg['why'][:60]}")
                continue
        problems.append(f"{cid}：排盘入参违律（{src}）{'/'.join(four)} ⟵ {'；'.join(errs)}")
    if check_orphans:  # 只在**全量语料**上判孤儿：自检按单例隔离跑，孤儿判据在那儿必然误报
        for cid in BOOK_CONFLICTS:
            if cid not in seen_conflict and cid not in {str(x.get("id")) for x in cases}:
                problems.append(f"{cid}：豁免清单指向不存在的例（该删）")
    return st


def selftest(problems: list[str]) -> None:
    """三件：新违律必须判红；已登记的书内冲突不得判红；合律正例不得误伤。"""
    bad = {"id": "ST_LAW_BAD", "pillars": {"year": "辛酉", "month": "乙酉", "day": "癸卯", "hour": "壬戌"}}
    sub: list[str] = []
    st = audit_laws([bad], sub, [])
    if not any("违律" in x and "ST_LAW_BAD" in x for x in sub):
        problems.append(f"负例自证失效：改坏月干（辛年寅月应壬，作乙）没被抓到 → {sub}")
    if st["可检"] != 1:
        problems.append(f"负例自证：本器没数到该例（可检={st['可检']}）——空跑不得当通过")
    ok = {"id": "ST_LAW_OK", "pillars": {"year": "辛酉", "month": "丁酉", "day": "癸卯", "hour": "壬戌"}}
    sub2: list[str] = []
    st2 = audit_laws([ok], sub2, [])
    if sub2 or st2["合律"] != 1:
        problems.append(f"负例自证假阳性：合律正例被判错或未计入 → {sub2}")
    reg = {"id": "ZP021", "pillars": {"year": "甲子", "month": "丙子", "day": "癸丑", "hour": "壬辰"}}
    sub3: list[str] = []
    st3 = audit_laws([reg], sub3, [])
    if any("ZP021" in x for x in sub3) or st3["登记冲突"] != 1:
        problems.append(f"负例自证失效：登记例未被认作书内冲突 → 判红{sub3}｜计数{st3}")
    stale = {"id": "ZC014", "pillars": {"year": "丁卯", "month": "壬寅", "day": "辛亥", "hour": "庚寅"}}
    sub4: list[str] = []
    audit_laws([stale], sub4, [])
    if not any("豁免清单条目已失效" in x for x in sub4):
        problems.append(f"负例自证失效：豁免例转正后没被反向要求删除 → {sub4}")


def main() -> int:
    ap = argparse.ArgumentParser(description="排盘入参历法自洽（五虎遁·五鼠遁）")
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
        cases.extend(c for c in cs if isinstance(c, dict))

    st = audit_laws(cases, problems, rows, check_orphans=True)
    if args.selftest:
        selftest(problems)
        print("  [selftest] 负例已跑（新违律判红／登记例不误伤／合律正例不误伤／豁免转正反向要求删除）")

    print(f"合计：{st['可检']} 例四柱齐可检（不看 datetime）／{st['合律']} 例合五虎遁＋五鼠遁／"
          f"{st['登记冲突']} 例书内冲突已登记（NOTE 可见）；{len(problems)} 条判红")
    if args.verbose:
        print(f"  取源分布：{st['取源']}")
    for r in rows:
        print(r)
    for x in problems:
        print("  ×", x)
    if st["可检"] == 0:
        print("× 0 例可检——本器等于没跑，不判通过")
        return 1
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
