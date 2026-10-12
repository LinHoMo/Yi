# -*- coding: utf-8 -*-
"""[22] 案例考点查重门：同一考点（书·逐字引文·判准）在一套考卷里不得出现两次。

为什么需要它：build_tiaohou_cases.py 历史上按 **id** 查重，而它的 id 由
len(cases)+1 顺排——重跑永远撞不到旧 id，去重分支是死代码。同一批 12×10 调候格
因此被建了三份（location 一种写「论甲（三春）」一种写「论甲·正月」，是两遍之间
section 换了写法）。后果不是"文件里多了几行"，而是**考卷分母被同一考点重复计数**：
逐字引文与判准都相同、夹具日期也相同的两例，引擎必然同判同分，测不出任何新东西，
却让某一格的权重变成别格的 2–6 倍。

口径：
- 判重看考点，不看 id、不看 location 措辞（同一句话两种抄法仍是同一考点）；
- 判重键**不含夹具日期**，故"同一条规则配两个不同夹具日"也算重复；
- 已知历史重复登记在 data/cases/dup_ledger.json（考点哈希 → 当次在册 id）。
  本门只对**台账之外**的重复判红，并点名到组与 id——用计数棘轮做不到这点：
  新增一组时按大小排序会报出旧的 6× 组，把人的注意力送去查一条没动过的老债；
- 本门不擅自删语料：清例＝口径变更，须另批裁定并按 §四.4 声明新旧读数不可比。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

DISC = pathlib.Path(__file__).resolve().parents[1]
for _p in (str(DISC / "scripts"), str(DISC / "core"), str(DISC / "dev_tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from build_tiaohou_cases import content_key  # noqa: E402  判重键唯一真值源（与构建器同源）

CASES_DIR = DISC / "data" / "cases"
LEDGER = CASES_DIR / "dup_ledger.json"


def key_hash(key: tuple) -> str:
    return hashlib.sha1(json.dumps(key, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def load_cases(cases_dir: pathlib.Path) -> list[dict]:
    out: list[dict] = []
    for p in sorted(cases_dir.glob("*.json")):
        if p.name == LEDGER.name:
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            raise SystemExit(f"{p.name} 解析失败 {type(exc).__name__}: {str(exc)[:80]}")
        if not isinstance(d, (list, dict)):
            continue
        for c in (d if isinstance(d, list) else d.get("cases") or []):
            if isinstance(c, dict) and c.get("id"):
                c["_file"] = p.name
                out.append(c)
    return out


def group(cases: list[dict]) -> dict[str, list[dict]]:
    g: dict[str, list[dict]] = {}
    for c in cases:
        g.setdefault(key_hash(content_key(c)), []).append(c)
    return g


def audit(cases: list[dict], registered: set[str]) -> tuple[list[str], list[str], dict]:
    problems: list[str] = []
    rows: list[str] = []
    g = group(cases)
    dups = {h: v for h, v in g.items() if len(v) > 1}
    redundant = sum(len(v) - 1 for v in dups.values())

    new_dups = {h: v for h, v in dups.items() if h not in registered}
    for h, v in sorted(new_dups.items(), key=lambda x: -len(x[1])):
        problems.append(
            f"台账之外的考点重复 {len(v)}×：[{v[0].get('book')}] "
            f"{(v[0].get('source_quote') or '')[:44]}… → {sorted(c.get('id') for c in v)}"
            f"（文件 {sorted({c.get('_file', '?') for c in v})}）")

    per_raw: dict[str, int] = {}
    per_uni: dict[str, int] = {}
    for v in g.values():
        for c in v:
            s = c.get("split") or "?"
            per_raw[s] = per_raw.get(s, 0) + 1
        per_uni[v[0].get("split") or "?"] = per_uni.get(v[0].get("split") or "?", 0) + 1

    rows.append(f"  · 考点 {len(g)} 个，其中 {len(dups)} 组重复，净多余 {redundant} 例；"
                f"台账在册 {len(registered)} 组")
    for s in sorted(per_raw):
        rows.append(f"  · split={s}：原始 {per_raw[s]} 例 → 唯一考点 {per_uni[s]} 个"
                    f"（重复计数 {per_raw[s] - per_uni[s]}）")
    return problems, rows, {"raw": len(cases), "unique": len(g),
                            "groups": len(dups), "redundant": redundant,
                            "new": len(new_dups), "per_raw": per_raw, "per_uni": per_uni}


def selftest(problems: list[str]) -> None:
    """三件：造重复且台账没有，必须点名判红（有牙齿）；不同考点不得误伤（不假阳性）；
    台账在册的重复不判红（否则历史债把门关死）；查 0 例必须报 0（不冒充测过）。"""
    base = {"book": "测试书", "source_quote": "丙火救甲，主显达", "split": "tune",
            "pillars": {"datetime": "1984-01-01 10:00"},
            "expected": {"tiaohou": {"main": "丙"}}}
    dup = [dict(base, id="T1"), dict(base, id="T2", location="论甲（三春）")]
    h = key_hash(content_key(dup[0]))
    p, _r, i = audit(dup, registered=set())
    if not p or "T1" not in p[0] or "T2" not in p[0]:
        problems.append(f"负例自证失效：台账之外的重复没判红或没点名到 id → {p}")
    p2, _r2, _i2 = audit(dup, registered={h})
    if p2:
        problems.append(f"负例自证：台账在册的重复被判红（历史债误伤）→ {p2}")
    ok = [dict(base, id="T3"),
          dict(base, id="T4", source_quote="壬水救丙，主清高",
               expected={"tiaohou": {"main": "壬"}})]
    p3, _r3, i3 = audit(ok, registered=set())
    if p3 or i3["unique"] != 2 or i3["redundant"] != 0:
        problems.append(f"负例自证假阳性：两个不同考点被判成重复 → {p3}｜{i3}")
    _p4, _r4, i4 = audit([], registered=set())
    if i4["raw"] != 0 or i4["unique"] != 0:
        problems.append(f"空跑自曝失效：0 例却报出非零计数 → {i4}")


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="八字科案例考点查重门")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--update-ledger", action="store_true",
                    help="把当前全部重复组登记进台账（清债/建库时人工执行一次）")
    ap.add_argument("--cases-dir", type=pathlib.Path, default=CASES_DIR)
    args = ap.parse_args()

    problems: list[str] = []
    cases = load_cases(args.cases_dir)
    if not cases:
        print(f"× {args.cases_dir} 下 0 例——本器等于没跑，不判通过")
        return 1

    if args.update_ledger:
        g = group(cases)
        dups = {h: sorted(c["id"] for c in v) for h, v in g.items() if len(v) > 1}
        LEDGER.write_text(json.dumps({
            "_comment": ["[22] 查重门的已知历史重复台账：键＝考点哈希（书·逐字引文·判准，"
                         "不含夹具日期与 id），值＝当次在册 id。",
                         "本文件只登记不改判：台账之外的新重复才判红。清例后请人工重跑 "
                         "python dev_tools/check_case_dupes.py --update-ledger。",
                         "生成器：dev_tools/check_case_dupes.py（2026-10-12 实测）。"],
            "generated": "2026-10-12",
            "dup_groups": len(dups),
            "redundant_cases": sum(len(v) - 1 for v in dups.values()),
            "ledger": dups,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"√ 已登记 {len(dups)} 组重复 → {LEDGER.name}")
        return 0

    if not LEDGER.exists():
        print("× 台账 dup_ledger.json 不存在——无从区分历史债与新增重复，不判通过")
        print("  （首次使用请人工执行 python dev_tools/check_case_dupes.py --update-ledger）")
        return 1
    registered = set(json.loads(LEDGER.read_text(encoding="utf-8")).get("ledger") or {})

    dup_problems, rows, info = audit(cases, registered)

    if args.selftest:
        selftest(problems)
        print("  [selftest] 负例已跑（新增重复点名判红 / 在册重复不误伤 / 不同考点不误伤 / 空跑报 0）")

    print(f"合计：案例 {info['raw']} 例，唯一考点 {info['unique']} 个，"
          f"重复组 {info['groups']} 组（台账在册 {len(registered)}），"
          f"净多余 {info['redundant']} 例，台账之外 {info['new']} 组")
    if info["groups"] < len(registered):
        print(f"· 较台账已清 {len(registered) - info['groups']} 组——"
              f"如属裁定过的删例，请重跑 --update-ledger 并按 §四.4 声明口径变更")
    if args.verbose:
        for r in rows:
            print(r)
    if dup_problems:
        print("× 台账之外存在考点重复——同一考点被计了两次以上，考卷分母失真")
        for x in dup_problems:
            print("  " + x)
        return 1
    print("√ 考点重复全部在册（构建器已改按考点查重，重跑实测新增 0 例、语料指纹不变）")
    for x in problems:
        print("× " + x)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
