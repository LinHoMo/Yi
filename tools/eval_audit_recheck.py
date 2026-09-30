# -*- coding: utf-8 -*-
"""三科评测口径复核探针（只读，可重复运行）。

用途：任何时候想复核 disciplines/{meihua,xiaoliuren,zeji} 的"100% 是怎么来的"，
跑这一条命令即可复现各科 docs/EVAL-AUDIT.md 里的每个数字：

    python tools/eval_audit_recheck.py

产出：
  A. expected 来源计数（逐例 provenance）与 split 分布
  B. 信息加权分与 N/A 权重占比（读已落盘的 eval_<split>.json）
  C. 梅花 timing 维度是否同义反复（expected == 起卦总数经 motion 折算）
  D. 小六壬四维 expected 是否逐字来自 data/verdicts.json
  E. 择吉 expected 是否与 analyze() 输出逐字段全等

纪律：本脚本只读，不改任何文件，也不参与质量门评分。
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

force_utf8_stdio()


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def section_a() -> None:
    print("== A. expected 来源（逐例 provenance）==")
    for disc, rel in (("meihua", "disciplines/meihua/data/cases/meihua_cases.json"),
                      ("xiaoliuren", "disciplines/xiaoliuren/data/cases/xiaoliuren_cases.json"),
                      ("zeji", "disciplines/zeji/data/cases/zeji_cases.json")):
        d = load(rel)
        meta = d.get("_meta") or {}
        sp = Counter(c.get("split") for c in d["cases"])
        pv = Counter(c.get("provenance") for c in d["cases"])
        print(f"  {disc:11s} meta="
              f"{ {k: meta.get(k) for k in ('total_cases', 'tune', 'holdout', 'excluded')} }")
        print(f"              split={dict(sp)}  provenance={dict(pv)}")


def section_b() -> None:
    print("\n== B. 信息加权分与 N/A（读已落盘明细）==")
    for disc in ("meihua", "xiaoliuren", "zeji"):
        for split in ("tune", "holdout"):
            p = ROOT / f"disciplines/{disc}/data/cases/eval_{split}.json"
            if not p.exists():
                print(f"  {disc}/{split}: 无落盘（先跑 evaluate.py --split {split} --save）")
                continue
            res = json.loads(p.read_text(encoding="utf-8"))["results"]
            rows = res["rows"]
            earned = sum(v[0] for r in rows for v in r["dims"].values())
            applic = sum(v[1] for r in rows for v in r["dims"].values())
            full = 100 * len(rows)
            print(f"  {disc:11s}/{split:8s} n={res['n']:<3} 平均分={res['avg']:<6} "
                  f"适用权重 {applic}/{full}（N/A {round((full-applic)*100.0/full,1)}%） "
                  f"信息加权分={round(earned*100.0/applic,1)}")


def section_c() -> None:
    print("\n== C. 梅花 timing 是否同义反复 ==")
    sys.path.insert(0, str(ROOT / "disciplines/meihua/scripts"))
    import chart as mh_chart  # noqa: E402
    import analyze as mh_analyze  # noqa: E402
    d = load("disciplines/meihua/data/cases/meihua_cases.json")
    hit = tot = 0
    for c in d["cases"]:
        exp = c["expected"].get("timing")
        if not exp:
            continue
        params = dict(c.get("input") or {})
        params.setdefault("question", c.get("question") or "")
        ch = mh_chart.chart(params)
        num = mh_analyze.analyze(ch)["timing"]["数应"]
        want = exp["value"] if isinstance(exp, dict) else exp
        tot += 1
        hit += int(num == want)
        print(f"  {c['id']} total={ch.get('total')} motion={ch.get('motion')} "
              f"数应={num} expected={want}")
    print(f"  → expected == 引擎同式复算：{hit}/{tot}（同义反复）")


def section_d() -> None:
    print("\n== D. 小六壬 expected 是否逐字来自 verdicts.json ==")
    v = load("disciplines/xiaoliuren/data/verdicts.json")
    d = load("disciplines/xiaoliuren/data/cases/xiaoliuren_cases.json")
    for c in d["cases"]:
        if c.get("split") == "excluded":
            continue
        e, pal = c["expected"], c["expected"]["palace"]
        p = v["palaces"][pal]
        line = e.get("topic_line")
        tbl = (v["topic_lines"].get(c.get("topic")) or {}).get(pal)
        print(f"  {c['id']} 宫={pal} 吉凶同表={e.get('verdict') == v['direction'].get(pal)} "
              f"主数同表={sorted(e.get('timing') or []) == sorted(p['主数'])} "
              f"诀句同表={bool(line) and line == tbl}"
              f"{'（回退总诀）' if line == p['总诀'] else ''}")


def section_e() -> None:
    print("\n== E. 择吉 expected 是否与 analyze() 逐字段全等 ==")
    for m in ("chart", "analyze"):
        sys.modules.pop(m, None)
    sys.path.insert(0, str(ROOT / "disciplines/zeji/scripts"))
    import chart as zj_chart  # noqa: E402
    import analyze as zj_analyze  # noqa: E402
    assert "zeji" in zj_chart.__file__, zj_chart.__file__
    d = load("disciplines/zeji/data/cases/zeji_cases.json")
    hit = tot = 0
    for c in d["cases"]:
        if c.get("split") == "excluded":
            continue
        e = c["expected"]
        params = dict(c.get("input") or {})
        params.setdefault("activity", c.get("activity"))
        params.setdefault("question", c.get("question") or "")
        ch = zj_chart.chart(params)
        an = zj_analyze.analyze(ch)
        f = an["factors_detail"]
        same = (e["jian_chu"] == f["jian_chu"]["神"]
                and e["day_god"] == f["huang_dao"]["神"]
                and bool(e["huang_dao"]) == bool(f["huang_dao"]["黄道"])
                and e["xiu"] == f["xiu"]["宿"]
                and bool(e["yi_hit"]) == bool(an["yi_hit"])
                and bool(e["ji_hit"]) == bool(an["ji_hit"])
                and e["verdict"] == an["conclusion"]["方向"])
        tot += 1
        hit += int(same)
        print(f"  {c['id']} {c['input']['date']} {c.get('activity'):4s} 全等={same}")
    print(f"  → expected == 引擎复算：{hit}/{tot}（确定性复算）")


if __name__ == "__main__":
    section_a()
    section_b()
    section_c()
    section_d()
    section_e()
