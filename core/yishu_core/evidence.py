# -*- coding: utf-8 -*-
"""Evidence Contract —— 结构化证据的唯一 schema 与提取器（P0 证据链收敛）。

目标链路：Source → Rule → Engine → **Evidence** → Evaluation → Synthesis → Narrative。
本模块处在 Engine 与 Evaluation 之间：把各科 analyze 输出里**已经在**的
判语/因子/出处/应期（`factors`、`conclusion.verdicts`、`古法格局`、`应期明细`、
`advanced_analysis`、`richen`、`timing`……）折叠成统一的 Evidence 记录，
让"一条结论来自什么规则、依据什么出处、适用什么条件、观察到了什么、
有没有评测覆盖"成为机器可回答的问题。

纪律：
  * **纯计算**：不读文件、不起进程、不 import 学科代码——浏览器 Pyodide 宿主
    与本机 subprocess 宿主共用同一份提取器（同源要求，同 request.py）。
  * **不制造事实**：提取器只搬运引擎已声明的内容；`effect` 只取学科自己给出
    的方向字段，缺方向（liuren/lingqi/ming/ziwei）就留空，绝不脑补吉凶。
  * **不重写语料**：出处继续留在各科 JSON/references 里，本模块只做引用。
  * 兼容：analyze 输出 schema 不变；Evidence 是**派生视图**，由宿主在 analyze
    之后附加（本机 `YiRuntime.execute` 的 envelope、合参层 normalize 记录）。

Evidence 记录字段（`Evidence` TypedDict）：
  id                稳定 id：`<discipline>:<kind>:<index>`
  discipline        学科
  claim             结论主张（判语/说明/诀句；引擎原话，不改写）
  factor            维度/因子（如 六合/六冲、体用关系、调候、应期）
  rule_id           规则注册表 id（如 liuyao.dufa_dujing）；未注册为 ""
  source            引擎声明的出处（所本/basis/出处/引文）；无则 ""
  applicability     适用条件（判据/condition）；无则 ""
  observation       Engine 实际观察到的盘面事实（尽量给结构化事实，非断语）
  effect            学科自报方向（吉/凶/平…）；学科未表态则 ""
  evaluation_status 评测覆盖状态（见 EVALUATION_STATUSES，取值纪律见下）
  provenance        {"kind": 提取通道, "path": analyze JSON 里的确切路径}

evaluation_status 取值（传播顺序 = 列表顺序，弱 → 强）：
  unassessed           无任何评测覆盖，也没有出处声明
  source_only          有出处声明（引擎自报所本），无独立评测
  mechanical_regression 仅被 golden 指纹 / 规则自洽回归覆盖
  classical_holdout    该规则域被古籍案例 tune/holdout 对齐评测覆盖
  external_holdout     另有永不调参的外部独立集覆盖
学科级默认值来自 `execution.registry.evaluation_baseline_of`（唯一真值源，
不在此处复制任何学科事实）；规则级覆盖由各科规则注册表（如六爻
`rule_registry.json`）经 `attach_rule_registry` 升级。
"""
from __future__ import annotations

from typing import Any, TypedDict

EVIDENCE_SCHEMA_VERSION = "1.0.0"

# 评测覆盖状态（弱 → 强；传播/升级按此顺序取 max）
EVALUATION_STATUSES: tuple[str, ...] = (
    "unassessed", "source_only", "mechanical_regression",
    "classical_holdout", "external_holdout",
)
_STATUS_RANK = {s: i for i, s in enumerate(EVALUATION_STATUSES)}


class Evidence(TypedDict, total=False):
    id: str
    discipline: str
    claim: str
    factor: str
    rule_id: str
    source: str
    applicability: str
    observation: str
    effect: str
    evaluation_status: str
    provenance: dict


def max_status(a: str, b: str) -> str:
    """两个评测状态取较强者（未知状态按 unassessed 处理）。"""
    return a if _STATUS_RANK.get(a, 0) >= _STATUS_RANK.get(b, 0) else b


def status_at_least(status: str, floor: str) -> str:
    """status 低于 floor 则提升到 floor（用于「有出处 ⇒ 至少 source_only」）。"""
    return max_status(status, floor)


# ────────────────────────────────────────────────────────────────
# 提取器：analyze_out（数据契约）→ [Evidence]
# ────────────────────────────────────────────────────────────────

def _s(v) -> str:
    """字符串化（None/空 → ""，非串转串）。"""
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, (list, tuple)):
        return "、".join(_s(x) for x in v if _s(x))
    return str(v)


def _status_for(baseline: str, has_source: bool) -> str:
    """学科基线与「有出处」的合并：有出处 ⇒ 至少 source_only。"""
    st = baseline if baseline in _STATUS_RANK else "unassessed"
    if has_source:
        st = status_at_least(st, "source_only")
    return st


def _ev(discipline: str, kind: str, idx: int, *, factor: str, claim: str,
        source: str = "", applicability: str = "", observation: str = "",
        effect: str = "", rule_id: str = "", baseline: str = "unassessed",
        path: str = "") -> Evidence:
    return Evidence(
        id=f"{discipline}:{kind}:{idx}",
        discipline=discipline,
        claim=claim,
        factor=factor,
        rule_id=rule_id,
        source=source,
        applicability=applicability,
        observation=observation,
        effect=effect,
        evaluation_status=_status_for(baseline, bool(source)),
        provenance={"kind": kind, "path": path},
    )


def _headline(discipline: str, a: dict, baseline: str) -> list[Evidence]:
    """主判：conclusion 的方向/verdict/说明/所本——报告里最重要的一句话。"""
    con = a.get("conclusion") or {}
    if not isinstance(con, dict):
        return []
    direction = _s(con.get("方向") or con.get("direction") or "")
    verdict = _s(con.get("verdict") or con.get("pattern") or "")
    note = _s(con.get("说明") or con.get("note") or "")
    based_on = _s(con.get("所本") or "")
    # 方向字段不存在（liuren/lingqi）或为空（ming）都不制造吉凶
    claim = "；".join(x for x in (verdict, direction, note) if x)
    if not claim and not based_on:
        return []
    return [_ev(discipline, "headline", 0, factor="总判", claim=claim,
                source=based_on, effect=direction, baseline=baseline,
                path="conclusion")]


def _verdict_list(discipline: str, a: dict, baseline: str) -> list[Evidence]:
    """conclusion.verdicts=[{code,label,basis}]（命科机械判定条目）。"""
    con = a.get("conclusion") or {}
    out: list[Evidence] = []
    for i, v in enumerate(con.get("verdicts") or []):
        if not isinstance(v, dict):
            continue
        out.append(_ev(
            discipline, "verdicts", i,
            factor=_s(v.get("code")) or "判定",
            claim=_s(v.get("label")),
            source=_s(v.get("basis")),
            observation=_s(v.get("label")),
            baseline=baseline, path=f"conclusion.verdicts[{i}]"))
    return out


def _patterns_ziwei(discipline: str, a: dict, baseline: str) -> list[Evidence]:
    """conclusion.古法格局=[{名,成立,判据,类别,所本}]（紫微格局查找）。"""
    con = a.get("conclusion") or {}
    out: list[Evidence] = []
    for i, v in enumerate(con.get("古法格局") or []):
        if not isinstance(v, dict):
            continue
        established = bool(v.get("成立"))
        name = _s(v.get("名"))
        claim = f"{name}：{'成立' if established else '不成立'}"
        out.append(_ev(
            discipline, "patterns", i,
            factor=_s(v.get("类别")) or "格局",
            claim=claim,
            source=_s(v.get("所本")),
            applicability=_s(v.get("判据")),
            observation=f"判据查找结果：{'成立' if established else '不成立'}",
            baseline=baseline, path=f"conclusion.古法格局[{i}]"))
    return out


def _yingqi(discipline: str, a: dict, baseline: str) -> list[Evidence]:
    """conclusion.应期明细=[{date,rule}]（六爻结构化应期候选，顺序即名次）。

    rule 字段是引擎给出的**规则标签**（如「冲空填实」），归入 applicability；
    rule_id 只保留给规则注册表 id（attach_rule_registry 挂接）。
    """
    con = a.get("conclusion") or {}
    out: list[Evidence] = []
    for i, v in enumerate(con.get("应期明细") or []):
        if not isinstance(v, dict) or not v.get("date"):
            continue
        out.append(_ev(
            discipline, "timing", i,
            factor="应期",
            claim=f"应期候选第 {i + 1} 位：{v.get('date')}",
            applicability=f"规则标签：{v.get('rule')}" if v.get("rule") else "",
            observation=f"date={v.get('date')}",
            effect="",  # 应期是时间主张，不是吉凶方向
            baseline=baseline, path=f"conclusion.应期明细[{i}]"))
    return out


def _factors_list(discipline: str, a: dict, baseline: str) -> list[Evidence]:
    """factors 列表两种形态：
    a) {code,label,basis,…}（大六壬/灵棋经）
    b) {因子,权重,判据,判语,所本}（梅花/小六壬/择吉）
    """
    fac = a.get("factors")
    if not isinstance(fac, list):
        return []
    out: list[Evidence] = []
    for i, f in enumerate(fac):
        if not isinstance(f, dict):
            continue
        if "code" in f or "label" in f:            # 形态 a
            out.append(_ev(
                discipline, "factors", i,
                factor=_s(f.get("code")) or "因子",
                claim=_s(f.get("label")),
                source=_s(f.get("basis")),
                observation=_s(f.get("label")),
                baseline=baseline, path=f"factors[{i}]"))
        elif "因子" in f:                           # 形态 b
            out.append(_ev(
                discipline, "factors", i,
                factor=_s(f.get("因子")),
                claim=_s(f.get("判语")) or _s(f.get("判据")),
                source=_s(f.get("所本")),
                applicability=_s(f.get("判据")),
                baseline=baseline, path=f"factors[{i}]"))
    return out


def _bing_yao(discipline: str, a: dict, baseline: str) -> list[Evidence]:
    """conclusion.病药={illness:[…],medicine:[…]}（六爻病药，条目 {code,label,basis}）。"""
    con = a.get("conclusion") or {}
    by = con.get("病药")
    if not isinstance(by, dict):
        return []
    out: list[Evidence] = []
    idx = 0
    for side, label in (("illness", "病"), ("medicine", "药")):
        for v in by.get(side) or []:
            if not isinstance(v, dict):
                continue
            out.append(_ev(
                discipline, "bing_yao", idx,
                factor=f"病药·{label}",
                claim=_s(v.get("label")),
                source=_s(v.get("basis")),
                observation=_s(v.get("label")),
                baseline=baseline, path=f"conclusion.病药.{side}[{idx}]"))
            idx += 1
    return out


def _timing_dict(discipline: str, a: dict, baseline: str) -> list[Evidence]:
    """timing 为 dict 且带 所本（梅花卦气/数应、小六壬主数）。"""
    t = a.get("timing")
    if not isinstance(t, dict):
        return []
    out: list[Evidence] = []
    src = _s(t.get("所本"))
    for i, key in enumerate(("卦气应期", "数应", "主数", "应期速度")):
        if key in t and t.get(key) not in (None, "", []):
            out.append(_ev(
                discipline, "timing", i,
                factor=f"应期·{key}",
                claim=f"{key}：{_s(t.get(key))}",
                source=src,
                observation=f"{key}={_s(t.get(key))}",
                baseline=baseline, path=f"timing.{key}"))
    return out


def _topic_verdict(discipline: str, a: dict, baseline: str) -> list[Evidence]:
    """topic_verdict={诀句,句类,所本}（小六壬事类切诀）。"""
    tv = a.get("topic_verdict")
    if not isinstance(tv, dict) or not tv.get("诀句"):
        return []
    return [_ev(discipline, "topic_verdict", 0,
                factor=f"事类断诀·{_s(tv.get('topic'))}",
                claim=_s(tv.get("诀句")),
                source=_s(tv.get("所本")),
                applicability=f"句类：{_s(tv.get('句类'))}",
                baseline=baseline, path="topic_verdict")]


def _richen(discipline: str, a: dict, baseline: str) -> list[Evidence]:
    """richen=[{name,desc,句,出处}]（大六壬日辰课经引文）。"""
    out: list[Evidence] = []
    for i, r in enumerate(a.get("richen") or []):
        if not isinstance(r, dict):
            continue
        out.append(_ev(
            discipline, "richen", i,
            factor=_s(r.get("name")) or "日辰",
            claim=_s(r.get("句")) or _s(r.get("desc")),
            source=_s(r.get("出处")) or _s(r.get("basis")),
            observation=_s(r.get("desc")),
            baseline=baseline, path=f"richen[{i}]"))
    return out


# 六爻 advanced_analysis 里值得提证据的结构块 → 维度名（与规则注册表 domain 对齐）
_AA_FACTORS = {
    "triple_combo": "三合局",
    "monthly_break": "月破",
    "advance_retreat": "进退神",
    "repetition": "反吟/伏吟",
    "repetition_deep": "反吟/伏吟",
    "clash_harmony": "六合/六冲",
    "officer_tomb": "墓库",
    "du_fa_du_jing": "独发/独静",
    "hexagram_body": "卦身",
    "three_punishments": "三刑",
    "hidden_spirit_analysis": "伏藏",
    "hidden_movement": "暗动",
    "soul_hexagram": "游魂/归魂",
    "six_breaks": "六破",
    "day_month_bonding": "合绊",
    "desperate_relief": "绝处逢生",
}

_INACTIVE_TEXT = ("无", "", "无伏藏", "本卦无暗动之爻")


def _aa_active(block: dict) -> bool:
    """advanced_analysis 块是否有正向发现（has_*/is_* 为真，或类型字段非「无」）。"""
    for k, v in block.items():
        if k.startswith(("has_", "is_")) and v is True:
            return True
    for k in ("type", "pattern", "hexagram_type", "repetition_type"):
        v = block.get(k)
        if isinstance(v, str) and v.strip() and v.strip() not in _INACTIVE_TEXT:
            return True
    return False


def _advanced_analysis(discipline: str, a: dict, baseline: str) -> list[Evidence]:
    """六爻 advanced_analysis：有发现的块 → 证据（source 取 classical_rule/quote/rule_applied）。"""
    aa = a.get("advanced_analysis")
    if not isinstance(aa, dict):
        return []
    out: list[Evidence] = []
    idx = 0
    for key, factor in _AA_FACTORS.items():
        block = aa.get(key)
        if not isinstance(block, dict) or not _aa_active(block):
            continue
        claim = _s(block.get("summary")) or _s(block.get("description")) \
            or _s(block.get("interpretation")) or _s(block.get("meaning"))
        source = _s(block.get("classical_rule")) or _s(block.get("classical_quote")) \
            or _s(block.get("rule_applied"))
        # observation：结构化 details 的首条事实描述（有则给）
        obs = ""
        details = block.get("details") or block.get("pairs") or block.get("scenarios") or []
        if isinstance(details, list) and details and isinstance(details[0], dict):
            obs = _s(details[0].get("description")) or _s(details[0].get("summary"))
        out.append(_ev(
            discipline, "advanced_analysis", idx,
            factor=factor, claim=claim, source=source, observation=obs,
            baseline=baseline, path=f"advanced_analysis.{key}"))
        idx += 1
    return out


def evidence_from_analyze(discipline: str, analyze_out: dict, *,
                          evaluation_baseline: str = "unassessed") -> list[Evidence]:
    """学科 analyze 输出 → 结构化证据列表（纯函数，双宿主共用）。

    evaluation_baseline : 学科级评测基线默认值
                          （取 `execution.registry.evaluation_baseline_of(discipline)`，
                          由调用方传入以保持本模块零依赖注册表）。
    """
    if not isinstance(analyze_out, dict):
        return []
    baseline = evaluation_baseline
    ev: list[Evidence] = []
    ev += _headline(discipline, analyze_out, baseline)
    ev += _verdict_list(discipline, analyze_out, baseline)
    ev += _patterns_ziwei(discipline, analyze_out, baseline)
    ev += _yingqi(discipline, analyze_out, baseline)
    ev += _factors_list(discipline, analyze_out, baseline)
    ev += _bing_yao(discipline, analyze_out, baseline)
    ev += _timing_dict(discipline, analyze_out, baseline)
    ev += _topic_verdict(discipline, analyze_out, baseline)
    ev += _richen(discipline, analyze_out, baseline)
    ev += _advanced_analysis(discipline, analyze_out, baseline)
    return ev


# ────────────────────────────────────────────────────────────────
# 规则注册表挂接（Rule → Evidence provenance）
# ────────────────────────────────────────────────────────────────

def attach_rule_registry(evidence: list[Evidence],
                         registry: dict | None) -> list[Evidence]:
    """用规则注册表（如六爻 data/rules/rule_registry.json 的解析结果）升级证据。

    匹配纪律（保守）：只在 evidence.factor 与注册表 domain **互为子串**时挂接；
    挂接动作 = 补 rule_id、出处缺省时补书名、评测状态按注册表 evaluation.status
    取较强者。匹配不上的一律不动——宁缺毋滥。
    """
    if not registry:
        return evidence
    rules = registry.get("rules") or []
    out: list[Evidence] = []
    for ev in evidence:
        factor = ev.get("factor") or ""
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            domain = _s(rule.get("domain"))
            if not domain or (domain not in factor and factor not in domain):
                continue
            ev = dict(ev)  # 不改入参
            ev["rule_id"] = _s(rule.get("rule_id"))
            src = rule.get("source") or {}
            if isinstance(src, dict) and not ev.get("source"):
                ev["source"] = " ".join(x for x in (_s(src.get("book")),
                                                    _s(src.get("locator"))) if x)
            reg_status = _s((rule.get("evaluation") or {}).get("status"))
            if reg_status in _STATUS_RANK:
                ev["evaluation_status"] = max_status(ev.get("evaluation_status", ""),
                                                     reg_status)
            break  # 一个证据只挂一条最先命中的规则
        out.append(ev)
    return out


def evaluation_gaps(evidence: list[Evidence]) -> list[dict]:
    """登记评测缺口：evaluation_status ∈ {unassessed, source_only} 的证据清单。

    「没有基准例时宁可登记缺口，也不制造假评测」——这是缺口登记的标准出口，
    供报告与文档引用（不是错误，是诚实状态）。
    """
    return [
        {"id": ev.get("id"), "factor": ev.get("factor"),
         "claim": (ev.get("claim") or "")[:40],
         "evaluation_status": ev.get("evaluation_status")}
        for ev in evidence
        if ev.get("evaluation_status") in ("unassessed", "source_only")
    ]


def evidence_envelope(discipline: str, evidence: list[Evidence], *,
                      evaluation_baseline: str = "unassessed") -> dict:
    """证据信封（宿主附加到报告 envelope 的 evidence 字段）。"""
    return {
        "schema": f"yi-evidence-v{EVIDENCE_SCHEMA_VERSION}",
        "discipline": discipline,
        "evaluation_baseline": evaluation_baseline,
        "n": len(evidence),
        "evidence": evidence,
        "gaps": evaluation_gaps(evidence),
        "note": "evidence 为 analyze 输出的派生视图；effect 只含学科自报方向；"
                "evaluation_status 为评测覆盖登记（古籍对齐分/外部集读数见 docs/HANDOFF.md）",
    }
