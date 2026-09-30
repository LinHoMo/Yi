# -*- coding: utf-8 -*-
"""合参层·学科输出归一化：各科 analyze_out（数据契约）→ 归一化占问记录。

synthesis 只依赖 disciplines 的输出 schema（CONTRACT.md §二），不 import 学科内部。
归一化记录（person 档案 divinations[] 条目）：

  {event_id, asked, at, discipline, verdict, direction,
   timing, based_on, chart_summary}

  direction : 吉 / 平 / 凶（由 verdict_direction 折叠：含凶→凶、含吉→吉、否则平）
  timing    : 应期要点列表（学科有则取，无则 []；「该维度未参评」不补位）
  based_on  : 判据所本法则（conclusion.所本，无则空串）
"""
from __future__ import annotations

from yishu_core.eval import verdict_direction

DISCIPLINES = ("liuyao", "ming", "meihua", "xiaoliuren", "zeji")


def _direction_label(text) -> str:
    v = verdict_direction(text)
    return {1: "吉", -1: "凶", 0: "平"}[v]


def _conclusion(a: dict) -> dict:
    return a.get("conclusion") or {}


def _based_on(a: dict) -> str:
    return str(_conclusion(a).get("所本") or "").strip()


def _at_of(a: dict, fallback: str | None) -> str | None:
    """从 analyze 输出里找起局时间；找不到用 fallback。"""
    cs = a.get("chart_summary") or {}
    for key in ("日期", "时间", "datetime", "date"):
        v = cs.get(key)
        if isinstance(v, dict):
            continue
        if v:
            return str(v)
    for key in ("datetime", "date"):
        v = a.get(key)
        if v:
            return str(v)
    return fallback


def normalize_liuyao(a: dict, *, at: str | None = None) -> dict:
    """六爻为迁移前旧实现，输出结构不统一，逐层防御取数。"""
    con = _conclusion(a)
    verdict = con.get("方向") or con.get("verdict")
    if not verdict:
        chain = a.get("thinking_chain") or {}
        s5 = chain.get("step5_synthesis") or {}
        verdict = s5.get("verdict") or "待定"
    yingqi = []
    for key in ("yingqi", "应期"):
        v = (a.get(key) or con.get(key))
        if v:
            yingqi = list(v) if isinstance(v, (list, tuple)) else [str(v)]
            break
    # 结构化应期候选（date+rule，按引擎给出顺序即名次），供现实回填评分
    items = con.get("应期明细") or []
    offered = [{"date": str(it.get("date")), "rule": str(it.get("rule") or "")}
               for it in items if isinstance(it, dict) and it.get("date")]
    return {
        "discipline": "liuyao",
        "asked": (a.get("question") or "").strip(),
        "at": _at_of(a, at) or "",
        "verdict": str(verdict),
        "direction": _direction_label(verdict),
        "timing": [f"应期 {t}" for t in yingqi],
        "yingqi_offered": offered,
        "based_on": _based_on(a),
        "chart_summary": a.get("chart_summary"),
    }


def normalize_ming(a: dict, *, at: str | None = None) -> dict:
    """命科：机械强弱/格局/大运入记录；方向不编吉凶，固定平。"""
    cs = a.get("chart_summary") or {}
    con = a.get("conclusion") or {}
    birth = a.get("birth") or {}
    pillars = cs.get("四柱") or {}
    gz = " ".join(str(pillars.get(k) or "—") for k in ("year", "month", "day", "hour"))
    strength = con.get("strength") or cs.get("强弱") or ""
    pattern = con.get("pattern") or cs.get("格局") or ""
    useful = "、".join(con.get("useful_gods") or [])
    return {
        "discipline": "ming",
        "asked": (a.get("question") or "").strip() or "命局排盘",
        "at": birth.get("datetime") or _at_of(a, at) or "",
        "verdict": f"四柱 {gz}·{strength}·{pattern}" + (f"·喜用{useful}" if useful else ""),
        "direction": "平",
        "timing": [],
        "based_on": _based_on(a),
        "chart_summary": {
            **cs,
            "strength": strength,
            "pattern": pattern,
            "useful_gods": con.get("useful_gods") or [],
        },
    }


def normalize_meihua(a: dict, *, at: str | None = None) -> dict:
    """梅花易数：体用生克→方向，应期为卦气/数应，仅供趋势参考。"""
    con = _conclusion(a)
    verdict = con.get("方向") or con.get("verdict") or "待定"
    cs = a.get("chart_summary") or {}
    # 应期取卦气干支与数应（非精确日期，仅供大致迟速参考）
    timing_raw = a.get("timing") or {}
    timing_parts = []
    if isinstance(timing_raw, dict):
        gz = timing_raw.get("卦气应期")
        if gz:
            timing_parts.append(f"卦气应期 {gz}")
        num = timing_raw.get("数应")
        if num:
            timing_parts.append(f"数应 {num}")
    return {
        "discipline": "meihua",
        "asked": (a.get("question") or "").strip(),
        "at": _at_of(a, at) or "",
        "verdict": str(verdict),
        "direction": _direction_label(verdict),
        "timing": timing_parts,
        "based_on": _based_on(a),
        "chart_summary": cs,
    }


def normalize_xiaoliuren(a: dict, *, at: str | None = None) -> dict:
    """小六壬：落宫→方向，应期取主数（非精确日期）。"""
    con = _conclusion(a)
    verdict = con.get("方向") or "待定"
    cs = a.get("chart_summary") or {}
    timing_raw = a.get("timing") or {}
    timing_parts = []
    if isinstance(timing_raw, dict):
        num = timing_raw.get("主数")
        if num:
            timing_parts.append(f"主数 {num}")
    return {
        "discipline": "xiaoliuren",
        "asked": (a.get("question") or "").strip(),
        "at": _at_of(a, at) or "",
        "verdict": str(verdict),
        "direction": _direction_label(verdict),
        "timing": timing_parts,
        "based_on": _based_on(a),
        "chart_summary": cs,
    }


def normalize_zeji(a: dict, *, at: str | None = None) -> dict:
    """择吉：建除/黄黑道/星宿→综合裁决，应期即日期本身。"""
    cs = a.get("chart_summary") or {}
    # 综合裁决从 factors/吉凶 里取（判据形如「吉（1.5）」）
    verdict_text = ""
    for f in (a.get("factors") or []):
        if f.get("因子") == "吉凶":
            verdict_text = f.get("判据", "")
            break
    if not verdict_text:
        con = _conclusion(a)
        verdict_text = con.get("方向") or con.get("verdict") or "平"
    return {
        "discipline": "zeji",
        "asked": (a.get("question") or "").strip() or "择日",
        "at": (cs.get("日期") or _at_of(a, at) or ""),
        "verdict": str(verdict_text),
        "direction": _direction_label(verdict_text),
        "timing": [],  # 择吉的「应期」就是所选日期本身，不另列
        "based_on": _based_on(a),
        "chart_summary": cs,
    }


def normalize_ziwei(a: dict, *, at: str | None = None) -> dict:
    """紫微斗数：机械格局/四化入宫→归一记录；方向固定平（三元命科不断吉凶）。"""
    cs = a.get("chart_summary") or {}
    con = a.get("conclusion") or {}
    birth = a.get("birth") or {}
    mg_stars = cs.get("命宫主星") or "—"
    pattern = cs.get("格局") or "—"
    si_impact = con.get("四化影响") or []
    ju = cs.get("五行局") or ""
    mg_branch = cs.get("命宫地支") or ""
    return {
        "discipline": "ziwei",
        "asked": (a.get("question") or "").strip() or "紫微命盘",
        "at": birth.get("datetime") or _at_of(a, at) or "",
        "verdict": (f"命宫在{mg_branch} 主星{mg_stars} {pattern}" +
                    (f" 四化：{'、'.join(si_impact)}" if si_impact else "")),
        "direction": "平",
        "timing": [],  # 紫微"大限"为主，精确日级应期不讲
        "based_on": _based_on(a),
        "chart_summary": {
            **cs,
            "pattern": pattern,
            "命宫主星": mg_stars,
        },
    }


_NORMALIZERS = {
    "liuyao": normalize_liuyao,
    "ming": normalize_ming,
    "meihua": normalize_meihua,
    "xiaoliuren": normalize_xiaoliuren,
    "zeji": normalize_zeji,
    "ziwei": normalize_ziwei,
}


def normalize(discipline: str, analyze_out: dict, *, at: str | None = None) -> dict:
    """学科 analyze_out → 归一化占问记录。"""
    if discipline not in _NORMALIZERS:
        raise ValueError(f"暂无归一化适配器：{discipline}"
                         f"（支持 {list(_NORMALIZERS)}）")
    rec = _NORMALIZERS[discipline](analyze_out, at=at)
    rec["discipline"] = discipline
    if not rec["asked"]:
        rec["asked"] = f"{discipline} 占问"
    return rec
