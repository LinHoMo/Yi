# -*- coding: utf-8 -*-
"""合参层·证据级检视（evidence_cross）—— P0 合参信息粒度收敛的兼容层。

现状：`normalize.py` 把各科输出折成 `{verdict, direction, timing}`，
`cross_rules.adjudicate` 按吉/平/凶计数做五条裁决。**这两个接口都保留**，
本模块不替代它们；它在其下新增一层：基于 Evidence Contract 的
claim / dimension / evidence / timing / source / applicability / evaluation_status
做同向/分歧/缺失判定，让「为什么这样处理」可以指到具体证据。

三条硬纪律（对齐 GOAL）：
  1. **跨科同向只提升"证据一致性"的描述强度，不自动制造新的事实**——
     本模块输出里没有任何"趋势/得分"，只有一致性描述（same/single/conflict）。
  2. **缺失证据必须显式 unassessed**——证据无评测覆盖（unassessed/source_only）
     或学科无方向表态，都进 `unassessed` 清单，不参与也不冒充表态。
  3. **冲突必须保留 conditions**——conflict 条目保留双方各自的
     claim/applicability/source/effect，不做平均、不编调和说。

诚实边界：**跨科维度词表尚未统一**（六爻说「六合/六冲」，梅花说「体用关系」），
维度级对照只对同名词（同 factor 字符串）成立；方向级分歧的裁决权仍在
`cross_rules.adjudicate`（五条规则），本模块提供的是证据底稿。
"""
from __future__ import annotations

import sys
from pathlib import Path

# 内核路径（本模块被 cli.py 导入时已就位；直跑 `python evidence_cross.py` 自举）
_CORE = str(Path(__file__).resolve().parents[1] / "core")
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)

from yishu_core.eval import verdict_direction

SCHEMA = "synthesis-evidence-v1"

# 方向表态的评测状态下限：低于此状态的证据只能进 unassessed，不算"已验证表态"
_WEAK_STATUSES = ("unassessed", "source_only")

# direction（吉/平/凶）→ sign（与 eval.verdict_direction 同一判法，不另立一套）
_SIGN_LABEL = {1: "吉", -1: "凶", 0: "平"}


def _entry(ev: dict) -> dict:
    """Evidence → 检视条目（保留全部可答责字段）。"""
    return {
        "discipline": ev.get("discipline"),
        "factor": ev.get("factor"),
        "claim": ev.get("claim"),
        "effect": ev.get("effect") or "",
        "rule_id": ev.get("rule_id") or "",
        "source": ev.get("source") or "",
        "applicability": ev.get("applicability") or "",
        "evaluation_status": ev.get("evaluation_status") or "unassessed",
        "evidence_id": ev.get("id"),
        "provenance": ev.get("provenance"),
    }


def cross_examine(records: list[dict], *,
                  concept_map: dict | None = None) -> dict:
    """归一化占问记录（含 evidence 列表）→ 证据级检视结果。

    records : normalize() 输出的占问记录列表；每条含 `evidence`（Evidence 列表）。
              旧记录无 evidence 键时按空处理（兼容层不要求重写历史档案）。
    concept_map : 跨科概念映射注册表（None → 自动读 synthesis/concept_map.json；
                  传 {} 可在纯内存测试中禁用映射）。仅 verified=true 的映射
                  参与维度归并（factor → canonical concept，全等匹配）；
                  无已验证映射时行为与按原词分组完全一致。
    """
    if concept_map is None:
        concept_map = load_concept_map()
    verified = [m for m in (concept_map.get("mappings") or [])
                if isinstance(m, dict) and m.get("verified") is True]

    directional: dict[int, list[dict]] = {1: [], -1: [], 0: []}
    non_directional: list[dict] = []
    by_factor: dict[str, list[dict]] = {}
    gaps: list[dict] = []

    for rec in records or []:
        for ev in rec.get("evidence") or []:
            entry = _entry(ev)
            factor = entry["factor"] or "未命名维度"
            canon = canonical_factor(factor, verified)
            by_factor.setdefault(canon, []).append(entry)
            status = entry["evaluation_status"]
            if status in _WEAK_STATUSES:
                gaps.append({"evidence_id": entry["evidence_id"],
                             "discipline": entry["discipline"],
                             "factor": factor,
                             "evaluation_status": status,
                             "claim": (entry["claim"] or "")[:40]})
            sign = verdict_direction(entry["effect"])
            if entry["effect"]:
                # 有方向表态（含明确说「平」的中性表态）
                directional[sign].append(entry)
            else:
                # effect 为空：学科未表态（机械结构/书源直录/命科机械标签）
                non_directional.append(entry)

    # ── 维度级：同名词才成立（已验证概念映射归并的除外）─────────────────
    dimensions: list[dict] = []
    conflicts: list[dict] = []
    n_same = n_single = 0
    for factor, entries in sorted(by_factor.items()):
        signed = [e for e in entries if e["effect"]]
        signs = {verdict_direction(e["effect"]) for e in signed}
        pos, neg = 1 in signs, -1 in signs
        if pos and neg:
            relation = "conflict"
            conflicts.append({
                "factor": factor,
                "sides": [
                    {"discipline": e["discipline"], "claim": e["claim"],
                     "effect": e["effect"], "applicability": e["applicability"],
                     "source": e["source"], "rule_id": e["rule_id"],
                     "evidence_id": e["evidence_id"]}
                    for e in signed
                ],
                "note": "证据级冲突：双方 claim 与成立条件（applicability）如上保留，"
                        "不做平均、不编调和说；裁决走 cross_rules 规则 4（先查口径与起局）",
            })
        elif (len(signs) == 1 and 0 not in signs
              and len({e["discipline"] for e in signed}) >= 2):
            relation = "same"
            n_same += 1
        elif len(entries) == 1:
            relation = "single"
            n_single += 1
        else:
            relation = "noted"
        weak = any(e["evaluation_status"] in _WEAK_STATUSES for e in entries)
        merged = sorted({e["factor"] for e in entries if e["factor"] != factor})
        dimensions.append({
            "factor": factor,
            "factors": sorted({e["factor"] for e in entries}),
            "relation": relation,
            "entries": entries,
            "note": ("含未独立评测的证据（evaluation_status: "
                     f"{sorted({e['evaluation_status'] for e in entries} & set(_WEAK_STATUSES))}）"
                     if weak else ""),
            **({"merged_from": merged,
                "merge_note": "经已验证概念映射归并（出处与适用条件见 concept_map.json）"}
               if merged else {}),
        })

    # ── 未表态学科（有记录但没有任何方向表态）──────────────────────────
    # silent  = 该科**携带证据**但全部无方向表态（机械骨架/书源直录/命科机械标签）
    # no_ev   = 该科记录**未携带结构化证据**（旧档案/绕过归一化）——不算表态也不算未表态
    def _has_dir(rec: dict) -> bool:
        return any(e.get("effect") for e in (rec.get("evidence") or []))

    silent_disciplines = sorted({
        rec.get("discipline") for rec in (records or [])
        if rec.get("discipline") and rec.get("evidence") and not _has_dir(rec)
    })
    no_evidence_disciplines = sorted({
        rec.get("discipline") for rec in (records or [])
        if rec.get("discipline") and not rec.get("evidence")
    } - {None})

    return {
        "schema": SCHEMA,
        "evidence_present": any(rec.get("evidence") for rec in (records or [])),
        "directional": {(_SIGN_LABEL[s] if s else "平"): directional[s]
                        for s in (1, -1, 0)},
        "non_directional_n": len(non_directional),
        "dimensions": dimensions,
        "conflicts": conflicts,
        "unassessed": {
            "evaluation_gaps": gaps,
            "silent_disciplines": silent_disciplines,
            "no_evidence_disciplines": no_evidence_disciplines,
            "note": "gaps=无评测覆盖/仅有出处声明的证据（宁登记缺口不造假评测）；"
                    "silent=该科有证据但无方向表态（机械骨架/书源直录/命科机械标签）；"
                    "no_evidence=旧档案记录未携带结构化证据，不参与证据级对照",
        },
        "consistency": {"same": n_same, "conflict": len(conflicts),
                        "single": n_single},
        "note": "跨科同向只提升证据一致性描述强度，不制造新事实；"
                "方向级分歧裁决以 cross_rules.adjudicate（五条规则）为准；"
                "维度级对照仅对同名词成立（跨科维度词表尚未统一）",
    }


# ────────────────────────────────────────────────────────────────
# 规则注册表挂接（guide / evidence-cross 两条命令共用，只读契约元数据）
# ────────────────────────────────────────────────────────────────

def load_rule_registry(discipline: str) -> dict | None:
    """读学科规则注册表（如六爻 data/rules/rule_registry.json）。

    规则注册表是学科输出契约的一部分（声明 rule_id、出处与评测覆盖），
    synthesis 只读这份契约元数据、不碰学科内部实现；
    文件不存在时返回 None（evidence 保持未挂接状态——宁缺毋滥）。
    """
    import json as _json
    p = (Path(__file__).resolve().parent.parent / "disciplines" / discipline
         / "data" / "rules" / "rule_registry.json")
    if not p.is_file():
        return None
    try:
        return _json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


def attach_rule_registries(records: list[dict]) -> list[dict]:
    """为每条记录的 evidence 挂接其学科的规则注册表（不改入参，返回副本）。

    guide 与 evidence-cross 都走本助手，保证两条命令看到的
    rule_id / evaluation_status 升级口径一致。
    """
    from yishu_core.evidence import attach_rule_registry
    out: list[dict] = []
    for rec in records or []:
        rec = dict(rec)
        reg = load_rule_registry(rec.get("discipline") or "")
        if reg and rec.get("evidence"):
            rec["evidence"] = attach_rule_registry(rec["evidence"], reg)
        out.append(rec)
    return out


# ────────────────────────────────────────────────────────────────
# 跨科概念对齐（Phase 5/6：verified-only，宁缺毋滥）
# ────────────────────────────────────────────────────────────────

def load_concept_map() -> dict:
    """读跨科概念映射注册表（synthesis/concept_map.json）。

    文件缺失/损坏 → {"mappings": []}（机制可用、映射为空——宁缺毋滥）。
    映射纪律见该文件 _comment：每条必须带古籍出处与适用条件，
    `verified=false` 的映射**不参与对照**。
    """
    import json as _json
    p = Path(__file__).resolve().parent / "concept_map.json"
    if not p.is_file():
        return {"schema": "yi-concept-map-v1", "mappings": []}
    try:
        data = _json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"mappings": []}
    except (ValueError, OSError):
        return {"schema": "yi-concept-map-v1", "mappings": []}


def canonical_factor(factor: str, verified_mappings: list[dict]) -> str:
    """factor → canonical concept（仅已验证映射；**全等匹配**，保守）。

    无命中时原样返回——跨科维度词表未统一前，只有显式登记且
    verified=true 的同义对才允许归入同一概念。
    """
    for m in verified_mappings or []:
        for member in (m.get("members") or []):
            if isinstance(member, dict) and member.get("factor") == factor:
                return m.get("concept") or factor
    return factor


def selfcheck() -> None:
    """最小用例自检：同向提升/冲突保留条件/缺失 unassessed/无制造事实。"""
    def rec(disc, direction, factor, claim, effect, status="classical_holdout",
            applicability="", source="《某书》"):
        return {"discipline": disc, "asked": "占事", "direction": direction,
                "evidence": [{
                    "id": f"{disc}:x:0", "discipline": disc, "claim": claim,
                    "factor": factor, "rule_id": "", "source": "《某书》",
                    "applicability": applicability, "observation": "",
                    "effect": effect, "evaluation_status": status,
                    "provenance": {"kind": "headline", "path": "conclusion"},
                }]}

    # ① 同向：两科同向 → same；输出无 trend/score 键（不制造新事实）
    r = cross_examine([rec("liuyao", "吉", "总判", "吉", "吉"),
                       rec("ming", "吉", "总判", "平吉", "平吉")])
    assert r["consistency"]["same"] == 1, r["consistency"]
    assert "trend" not in r and "score" not in r, r.keys()

    # ② 冲突：同 factor 异向 → conflict 且双方 conditions（applicability）保留
    r = cross_examine([rec("liuyao", "吉", "总判", "吉", "吉", applicability="A 条件"),
                       rec("ming", "凶", "总判", "凶", "凶", applicability="B 条件")])
    assert len(r["conflicts"]) == 1 and r["conflicts"][0]["factor"] == "总判", r
    sides = r["conflicts"][0]["sides"]
    assert {s["applicability"] for s in sides} == {"A 条件", "B 条件"}, sides

    # ③ 缺失：无评测覆盖的证据 → unassessed 登记；未表态学科 → silent
    r = cross_examine([rec("liuyao", "吉", "总判", "吉", "吉",
                           status="unassessed", source=""),
                       rec("ming", None, "格局", "平", "")])
    assert r["unassessed"]["evaluation_gaps"], r["unassessed"]
    assert "ming" in r["unassessed"]["silent_disciplines"], r["unassessed"]

    # ④ 弱状态证据不冒充已验证表态：source_only 仍在 gaps（即便有方向）
    r = cross_examine([rec("liuyao", "吉", "总判", "吉", "吉", status="source_only")])
    assert r["unassessed"]["evaluation_gaps"][0]["evaluation_status"] == "source_only"

    # ⑤ 旧记录兼容：无 evidence 键不报错，且不算「未表态」（是未携带证据）
    r = cross_examine([{"discipline": "ming", "direction": "平"}])
    assert r["consistency"]["same"] == 0 and r["non_directional_n"] == 0
    assert r["evidence_present"] is False
    assert r["unassessed"]["no_evidence_disciplines"] == ["ming"]
    assert r["unassessed"]["silent_disciplines"] == []

    # ⑥ 概念映射：verified=false 不归并（宁缺毋滥）；verified=true 才按 concept 归并
    def rec_f(disc, factor, effect):
        return rec(disc, "吉", factor, effect, effect)

    unverified_map = {"mappings": [
        {"concept": "命卜互证",
         "members": [{"discipline": "liuyao", "factor": "六合/六冲"},
                     {"discipline": "ming", "factor": "三合/三会"}],
         "verified": False}]}
    r = cross_examine([rec_f("liuyao", "六合/六冲", "吉"),
                       rec_f("ming", "三合/三会", "吉")],
                      concept_map=unverified_map)
    assert r["consistency"]["same"] == 0, "未验证映射不得归并维度"
    verified_map = {"mappings": [dict(unverified_map["mappings"][0], verified=True)]}
    r = cross_examine([rec_f("liuyao", "六合/六冲", "吉"),
                       rec_f("ming", "三合/三会", "吉")],
                      concept_map=verified_map)
    assert r["consistency"]["same"] == 1, "已验证映射按 concept 归并"
    dim = next(d for d in r["dimensions"] if d["factor"] == "命卜互证")
    assert sorted(dim["merged_from"]) == sorted(["六合/六冲", "三合/三会"]), dim

    # ⑦ 真实注册表：当前全部 verified=false → 默认行为与无映射完全一致
    real = load_concept_map()
    assert all(not m.get("verified") for m in real.get("mappings") or []), \
        "concept_map 出现 verified=true 条目：须先落逐字引文并经 CHANGELOG 登记"
    r_plain = cross_examine([rec_f("liuyao", "六合/六冲", "吉"),
                             rec_f("ming", "三合/三会", "吉")])
    r_real = cross_examine([rec_f("liuyao", "六合/六冲", "吉"),
                            rec_f("ming", "三合/三会", "吉")], concept_map=real)
    assert r_plain["consistency"] == r_real["consistency"], \
        "真实 concept_map（全未验证）不得改变对照行为"
    print("evidence_cross 自检通过（同向/冲突保留条件/unassessed/弱状态/旧记录兼容/"
          "概念映射 verified-only）")


if __name__ == "__main__":
    selfcheck()
