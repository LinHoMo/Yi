# -*- coding: utf-8 -*-
"""book_strength_probe —— **原书档诊断器**（只读，不进引擎输出；571 批）。

按《滴天髓阐微》原书判据（根元／印护／忌神克泄／从格）重算一遍日主旺衰，
用于**诊断与对照**，与引擎现有强弱档并列输出。

**571 批实测结论（负结果，如实记）**：本档在 569 批人工认定的 12 案上命中 **5/12**，
**弱于引擎档的 7/12**；且从格分类仍有偏差（把原书「从官」判成「从财」）。
故**不接入引擎输出**（不引一个已知更弱的口径进 analyze，不改任何既有读数），
本器仅作只读诊断与口径研究之用。详见 `bazi/references/judge_comparability.md` §六。

**原书档**：与引擎强弱档并列的第二套日主旺衰口径（571 批）。

为什么要有它：引擎现有 `strength.strength`（偏弱／偏旺／中和）按
「生扶 − 克泄耗 打分 ＋ 得令加权」算；而原书判旺衰常按另外三件事：
**根元**（日主有无根气）、**印护**（财旺而有印护则不破）、**从格**
（无根无护而专旺一路者从之）。570 批实测表明两套口径量纲不同——
同一批命例，引擎档与原书档在 12 案中对 8 案给出不同结论。

本模块按原书判据实现**工程近似**（不是古法全貌，只作对照）：
  ① 根元：日主五行在月／日／时三支藏干中是否得同五行（比劫）或生我（印）之气；
  ② 印护：四柱天干透印，且该印在支中有根（或月令为印）；
  ③ 忌神克泄：官杀／食伤／财三类各计权重（**不减得令加权**——原书不以月令一票决定）；
  ④ 从格候选：日主无根、无印护，而一路五行独旺（月令与多数支同气）→ 标从弱／从官杀／从财／从儿。

**口径声明（必须随引用一起转述）**：本档是**工程近似**，只表达"按原书判据重算一遍会得到什么"，
不得当作古法正解，也**不参与引擎评分**（不改任何既有读数）。

书证（逐字；底本 `bazi/data/sources/ditian_sui_chanwei_dz.dz.txt`，行号按**该 dz 副本**）：
  · 根元：《滴天髓闡微》源L4704「而日主根元亦固」
  · 印护：《滴天髓闡微》源L5623「财虽旺，不能破印」
  · 从格：《滴天髓闡微》源L735「其意向必在午中丁火而合从矣」；另《滴天髓阐微》源L749「此为天地合而从官也」
  · 不拘一端：《三命通会》源L90「皆当从其变者而论之不可拘于一端」
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent / "scripts"), str(_HERE.parent / "core")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from bazi_factors._common import (
    BRANCH_ELEMENTS,
    KE_CYCLE,
    LAYER_WEIGHT,
    SHENG_CYCLE,
    STEM_ELEMENTS,
    _element_of_stem,
    _role,
    twelve_growth,
)

_PILLARS = ("year", "month", "day", "hour")
# 根元取用的三支（原书论通根多就月日时，年柱为祖上不入根）
_ROOT_BRANCHES = ("month", "day", "hour")
_LAYER_RANK = {"本气": 3, "中气": 2, "余气": 1}


def _branch_of(chart_json: dict, pname: str) -> str:
    return ((chart_json.get("pillars") or {}).get(pname) or {}).get("branch") or ""


def _stem_of(chart_json: dict, pname: str) -> str:
    return ((chart_json.get("pillars") or {}).get(pname) or {}).get("stem") or ""


def _root_of_day_master(chart_json: dict, day_elem: str) -> dict:
    """根元：日主五行在月／日／时三支藏干中是否得气（同五行＝比劫根，生我＝印根）。"""
    roots, best = [], ""
    factors = chart_json.get("factors") or {}
    for pname in _ROOT_BRANCHES:
        block = factors.get(pname) or {}
        branch = _branch_of(chart_json, pname)
        for item in block.get("ten_gods") or []:
            if not isinstance(item, dict):
                continue
            stem = item.get("stem") or ""
            layer = item.get("layer") or "本气"
            elem = STEM_ELEMENTS.get(stem, "")
            if not elem:
                continue
            if elem != day_elem:
                continue  # 通根只论同五行（比劫）之气；生我者为印根，归「印护」不归「根元」
            if layer not in ("本气", "中气"):
                continue  # 余气不作根
            kind = "比劫根"
            roots.append({"pillar": pname, "branch": branch, "stem": stem,
                          "layer": layer, "kind": kind})
            rank = _LAYER_RANK.get(layer, 0)
            if not best or rank > _LAYER_RANK.get(best[0], 0):
                best = (layer,)
    return {
        "有根": bool(roots),
        "根": roots,
        "根支": sorted({r["branch"] for r in roots}),
        "说明": ("日主在月／日／时三支藏干得气" if roots else "日主在月／日／时三支全无根气"),
    }


def _seal_protection(chart_json: dict, day_elem: str) -> dict:
    """印护：透印且印有根（月令为印或支中藏印有气）。"""
    seal_stems, seals = [], []
    for pname in _PILLARS:
        stem = _stem_of(chart_json, pname)
        elem = STEM_ELEMENTS.get(stem, "")
        if elem and SHENG_CYCLE.get(elem) == day_elem:
            seal_stems.append({"pillar": pname, "stem": stem})
    month_branch = _branch_of(chart_json, "month")
    month_elem = BRANCH_ELEMENTS.get(month_branch, "")
    month_is_seal = bool(month_elem) and SHENG_CYCLE.get(month_elem) == day_elem
    factors = chart_json.get("factors") or {}
    for pname in _ROOT_BRANCHES:
        block = factors.get(pname) or {}
        for item in block.get("ten_gods") or []:
            if not isinstance(item, dict):
                continue
            stem = item.get("stem") or ""
            elem = STEM_ELEMENTS.get(stem, "")
            if elem and SHENG_CYCLE.get(elem) == day_elem and (item.get("layer") or "本气") in ("本气", "中气"):
                seals.append({"pillar": pname, "stem": stem, "layer": item.get("layer") or "本气"})
    has_root = bool(seals)
    if seal_stems and (has_root or month_is_seal):
        state = "印护成立"
    elif seal_stems:
        state = "印透而无根"
    else:
        state = "无印"
    return {"透印": seal_stems, "支中印": seals, "月令为印": month_is_seal,
            "成立": state == "印护成立", "状态": state}


def _harm_counts(chart_json: dict) -> dict:
    """忌神克泄：官杀／食伤／财各类权重（藏干分层计重，**不减得令加权**）。"""
    counts = {"官杀": 0.0, "食伤": 0.0, "财": 0.0}
    factors = chart_json.get("factors") or {}
    for pname in _PILLARS:
        block = factors.get(pname) or {}
        for item in block.get("ten_gods") or []:
            if not isinstance(item, dict):
                continue
            role = _role(item.get("ten_god") or "")
            if role in counts:
                counts[role] = round(counts[role] + LAYER_WEIGHT.get(item.get("layer") or "本气", 0.25), 2)
    counts["合计"] = round(sum(counts.values()), 2)
    return counts


def _support_count(chart_json: dict, day_elem: str) -> float:
    """生扶合计（印＋比劫，藏干分层计重，**不含得令加权**）。"""
    total = 0.0
    factors = chart_json.get("factors") or {}
    for pname in _PILLARS:
        block = factors.get(pname) or {}
        for item in block.get("ten_gods") or []:
            if not isinstance(item, dict):
                continue
            role = _role(item.get("ten_god") or "")
            if role in ("印", "比劫"):
                total += LAYER_WEIGHT.get(item.get("layer") or "本气", 0.25)
    return round(total, 2)


def _cong_candidate(chart_json: dict, day_elem: str, root: dict, seal: dict) -> str:
    """从格候选：日主无根、无印护，而一路五行独旺。"""
    if root["有根"] or seal["成立"] or seal["状态"] == "印透而无根":
        return ""
    month_branch = _branch_of(chart_json, "month")
    month_elem = BRANCH_ELEMENTS.get(month_branch, "")
    if not month_elem:
        return ""
    branches = [_branch_of(chart_json, p) for p in _PILLARS]
    branches = [b for b in branches if b]
    same = sum(1 for b in branches if BRANCH_ELEMENTS.get(b, "") == month_elem)
    if same < 3:
        return ""
    # 该旺气对日主而言属哪一类十神 → 从弱／从官杀／从财／从儿
    if month_elem == day_elem:
        return "从比劫"
    if SHENG_CYCLE.get(month_elem) == day_elem:
        return "从印"
    if SHENG_CYCLE.get(day_elem) == month_elem:
        return "从食伤"
    if KE_CYCLE.get(day_elem) == month_elem:
        return "从官杀"
    if KE_CYCLE.get(month_elem) == day_elem:
        return "从财"
    return ""


def book_strength(chart_json: dict) -> dict:
    """原书档（工程近似）：与引擎强弱档并列，不参与评分。"""
    day_stem = _stem_of(chart_json, "day")
    day_elem = _element_of_stem(day_stem)
    if not day_stem or not day_elem:
        return {"档": "未知", "从格候选": "", "根元": {}, "印护": {}, "忌神克泄": {},
                "依据": "缺日主"}

    root = _root_of_day_master(chart_json, day_elem)
    seal = _seal_protection(chart_json, day_elem)
    harm = _harm_counts(chart_json)
    support = _support_count(chart_json, day_elem)
    cong = _cong_candidate(chart_json, day_elem, root, seal)

    if cong:
        grade = "偏弱"
        why = f"日主无根无印护而{cong}（原书从格一路）"
    elif root["有根"] and (seal["成立"] or harm["合计"] <= support):
        grade = "偏旺"
        why = "日主有根，且印护成立或忌神克泄不重于生扶"
    elif (not root["有根"]) and (harm["合计"] > support or not seal["成立"]):
        grade = "偏弱"
        why = "日主无根，且忌神克泄重于生扶或印护不成立"
    else:
        grade = "中和"
        why = "根元、印护、忌神克泄三项相称，无一独大"

    return {
        "档": grade,
        "从格候选": cong,
        "根元": root,
        "印护": seal,
        "忌神克泄": harm,
        "生扶合计": support,
        "依据": why,
        "口径": "工程近似：按《滴天髓阐微》原书判据（根元／印护／忌神克泄／从格）重算，非古法全貌；不参与引擎评分。",
        "书证": "根元 《滴天髓阐微》源L4704「而日主根元亦固」；"
                "印护 《滴天髓阐微》源L5623「财虽旺，不能破印」；"
                "从格 《滴天髓阐微》源L735「其意向必在午中丁火而合从矣」；"
                "另《滴天髓阐微》源L749「此为天地合而从官也」。",
    }


def compare_with_manual() -> int:
    """与 569 批人工认定池（12 案）逐案对照：只打印，不改任何文件。"""
    pool_path = _HERE.parent / "data" / "cases" / "dts_manual_candidates.json"
    if not pool_path.is_file():
        print("× 人工认定池不存在，无法对照")
        return 1
    from chart import chart  # noqa: E402  仅本诊断器使用

    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    hit = miss = 0
    for case in pool.get("cases") or []:
        dt = case.get("real_datetime")
        if not dt:
            continue
        bs = book_strength(chart("命局", datetime_str=dt, gender=case.get("gender") or ""))
        same = bs["档"] == case.get("manual_strength")
        hit += same
        miss += (not same)
        print(f"  {'√' if same else '×'} {case.get('id')}｜书载 {case.get('manual_strength')}｜"
              f"原书档 {bs['档']}｜从格 {bs['从格候选'] or '—'}｜"
              f"根 {'有' if bs['根元'].get('有根') else '无'}｜印 {bs['印护'].get('状态')}")
    print(f"  原书档 vs 人工认定：命中 {hit}／{hit + miss}（引擎档同批为 7／12；本档更弱，故不接线）")
    return 0


def selftest() -> int:
    """自证：档位取值合法、同一输入两次同结果、分项字段齐备。"""
    from chart import chart  # noqa: E402
    dt = "2015-01-16 09:30"
    a = book_strength(chart("命局", datetime_str=dt, gender="女"))
    b = book_strength(chart("命局", datetime_str=dt, gender="女"))
    checks = [
        ("档位取值合法", a.get("档") in ("偏弱", "偏旺", "中和", "未知")),
        ("同一输入结果确定", json.dumps(a, ensure_ascii=False, sort_keys=True) == json.dumps(b, ensure_ascii=False, sort_keys=True)),
        ("分项齐备（根元/印护/忌神克泄）", all(k in a for k in ("根元", "印护", "忌神克泄"))),
        ("口径声明在位", "工程近似" in (a.get("口径") or "")),
        ("书证在位", "源L" in (a.get("书证") or "")),
    ]
    for name, ok in checks:
        print(f"  {'√' if ok else '×'} {name}")
    bad = [n for n, ok in checks if not ok]
    if bad:
        print(f"selftest 失败 {len(bad)} 项：{'; '.join(bad)}")
        return 1
    print(f"selftest：{len(checks)} 类检查全过（真盘零写入）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="原书档诊断器（只读）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--compare", action="store_true", help="与 569 批人工认定池 12 案逐案对照")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.compare:
        return compare_with_manual()
    from chart import chart  # noqa: E402
    print(json.dumps(book_strength(chart("命局", datetime_str="2015-01-16 09:30", gender="女")),
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
