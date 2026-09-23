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

DISCIPLINES = ("liuyao", "meihua", "xiaoliuren", "zeji")


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


def normalize_xiaoliuren(a: dict, *, at: str | None = None) -> dict:
    con = _conclusion(a)
    palace = a.get("palace") or {}
    timing = (a.get("timing") or {}).get("主数") or []
    return {
        "discipline": "xiaoliuren",
        "asked": (a.get("question") or "").strip(),
        "at": _at_of(a, at) or "",
        "verdict": f"{palace.get('宫名') or '?'}·{con.get('说明') or ''}",
        "direction": _direction_label(con.get("方向")),
        "timing": [f"主数 {n}" for n in timing],
        "based_on": _based_on(a),
        "chart_summary": a.get("chart_summary"),
    }


def normalize_meihua(a: dict, *, at: str | None = None) -> dict:
    con = _conclusion(a)
    timing = (a.get("timing") or {}).get("卦气应期") or []
    return {
        "discipline": "meihua",
        "asked": (a.get("question") or "").strip(),
        "at": _at_of(a, at) or "",
        "verdict": f"{con.get('说明') or ''}",
        "direction": _direction_label(con.get("方向")),
        "timing": [f"卦气应期 {t}" for t in timing],
        "based_on": _based_on(a),
        "chart_summary": a.get("chart_summary"),
    }


def normalize_zeji(a: dict, *, at: str | None = None) -> dict:
    con = _conclusion(a)
    cs = a.get("chart_summary") or {}
    score = con.get("得分")
    return {
        "discipline": "zeji",
        "asked": (a.get("question") or "").strip(),
        "at": _at_of(a, at) or "",
        "verdict": (f"{cs.get('日期') or '?'} {cs.get('建除') or '?'}日"
                    f"{cs.get('日值神') or '?'}·{con.get('说明') or ''}"
                    + (f"（得分 {score}）" if score is not None else "")),
        "direction": _direction_label(con.get("方向")),
        "timing": [],
        "based_on": _based_on(a),
        "chart_summary": cs,
    }


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
    return {
        "discipline": "liuyao",
        "asked": (a.get("question") or "").strip(),
        "at": _at_of(a, at) or "",
        "verdict": str(verdict),
        "direction": _direction_label(verdict),
        "timing": [f"应期 {t}" for t in yingqi],
        "based_on": _based_on(a),
        "chart_summary": a.get("chart_summary"),
    }


_NORMALIZERS = {
    "xiaoliuren": normalize_xiaoliuren,
    "meihua": normalize_meihua,
    "zeji": normalize_zeji,
    "liuyao": normalize_liuyao,
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
