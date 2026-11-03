# -*- coding: utf-8 -*-
"""六爻叙述层：解读正文生成 / 段落素材——唯一正文出口（CONTRACT §一）。

铁律一合规：机械运算在主线引擎完成，本层只把结构化结论翻译成人话并装配成交付对象。

第三百一十一批：五步链组装 / 格局标签 / 引文选取 / 持世深化搬往 chain_assembly.py
（CONTRACT §二：那是 analyze 段内部实现）；本层只剩正文装配，输入是 analyze JSON，
不 import 任何 analyze/step 模块、不重算象数。
"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

import json

import re

from pathlib import Path

from chain_verdicts import NARRATIVE_HINTS, PATTERN_RELATED, pattern_label, select_timing_base  # noqa: E402
from chain_tables import _BRANCH_CLASH_MAP, _HE_MAP  # noqa: E402

try:
    from advice_framework import generate_advice
except ImportError:
    from scripts.advice_framework import generate_advice

from narrative_assembly import build_reasoning_chain, build_summary  # noqa: E402  355 批 fact builder

_NARRATIVE_TEMPLATES_PATH = Path(__file__).resolve().parents[1] / "data" / "narrative_templates.json"


def _load_narrative_templates() -> dict:
    try:
        return json.loads(_NARRATIVE_TEMPLATES_PATH.read_text(encoding="utf-8"))
    except OSError:
        return {}


_NARRATIVE_TPL = _load_narrative_templates()

_ADVICE_SOFT = _NARRATIVE_TPL.get("advice_soft") or {}

_PATTERN_QUOTE_RELEVANCE = PATTERN_RELATED

# ────────────────────────────────────────────────────────────────
# human_narrative_segments 部分：正文段落素材生成
# ────────────────────────────────────────────────────────────────

def _pos_name(p) -> str:
    try:
        p = int(p)
    except Exception:
        return str(p or "")
    return {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}.get(p, f"{p}爻")


def _strength_sentence(level: str, use_cat: str, use_br: str, use_pos, yuan_moving: bool = False, yuan_greedy: bool = False) -> str:
    """把旺衰说成对这件事意味着什么——老师傅看盘的口吻，月破单列。"""
    loc = ""
    if use_br:
        loc = f"{use_br}"
        if use_pos:
            loc += _pos_name(use_pos)
        loc = f"（落在{loc}）"
    sp = _NARRATIVE_TPL.get("strength_phrases") or {}
    if "月破" in str(level):
        return (sp.get("month_break") or "").format(use_cat=use_cat, loc=loc)

    def _yuan_note() -> str:
        if yuan_greedy:
            return sp.get("yuan_greed_he") or ""
        if yuan_moving:
            return sp.get("yuan_moving") or ""
        return sp.get("yuan_static") or ""

    table = {
        "极旺": (sp.get("极旺") or "").format(use_cat=use_cat, loc=loc, yuan_note=_yuan_note()),
        "旺": (sp.get("旺") or "").format(use_cat=use_cat, loc=loc, yuan_note=_yuan_note()),
        "相": (sp.get("相") or "").format(use_cat=use_cat, loc=loc, yuan_note=_yuan_note()),
        "中和": (sp.get("中和") or "").format(use_cat=use_cat, loc=loc),
        "中和偏旺": (sp.get("中和偏旺") or "").format(use_cat=use_cat, loc=loc, yuan_note=_yuan_note()),
        "中和偏弱": (sp.get("中和偏弱") or "").format(use_cat=use_cat, loc=loc),
        "偏弱": (sp.get("偏弱") or "").format(use_cat=use_cat, loc=loc),
        "弱": (sp.get("弱") or "").format(use_cat=use_cat, loc=loc),
        "极弱": (sp.get("极弱") or "").format(use_cat=use_cat, loc=loc),
        "休囚": (sp.get("休囚") or "").format(use_cat=use_cat, loc=loc),
    }
    return table.get(str(level or ""), (sp.get("default") or "").format(use_cat=use_cat, loc=loc))


def _question_focus(question: str) -> str:
    q = question or ""
    rules = [
        (("病", "疾", "愈", "医"), "身体/病情"),
        (("婚", "姻", "嫁", "娶", "感情", "缘"), "婚姻感情"),
        (("失", "丢", "找回", "银", "物"), "失物寻回"),
        (("财", "求财", "生意", "投资", "价", "贵贱", "贸易", "银"), "财运求谋"),
        (("官", "讼", "诉", "师尊"), "官非词讼"),
        (("文书", "考试", "学业", "领"), "文书学业"),
        (("出行", "出外", "归", "回", "仆"), "行人出行"),
        (("子", "孩子", "子女"), "子女相关"),
        (("父", "母", "岳父", "长辈"), "长辈相关"),
    ]
    for kws, label in rules:
        if any(k in q for k in kws):
            return label
    return "所问之事"


def _dedash(text: str) -> str:
    """折叠「——，」：破折号与逗号不得相连（模板拼接产物，非书源原文）。"""
    return text.replace("——，", "——")


def _verdict_opening(verdict: str, focus: str, pattern_label: str = "", yuan_diagnosis: str = "") -> str:
    """第一句：先接住问题、亮明结论，并直接给出最关键的一条理由。"""
    tpl = _NARRATIVE_TPL.get("verdict_openings") or {}
    reason_part = ""
    if yuan_diagnosis:
        reason_part = (tpl.get("reason_yuan") or "").format(yuan_diagnosis=yuan_diagnosis)
    elif pattern_label:
        reason_part = (tpl.get("reason_pattern") or "").format(pattern_label=pattern_label)

    pos_table = tpl.get("pos_table") or {}
    neg_table = tpl.get("neg_table") or {}
    wrap = tpl.get("wrap_pos") or "就{focus}来说，{text}。"

    v = str(verdict or "")
    if v in pos_table:
        return _dedash(wrap.format(focus=focus, text=pos_table[v]))
    if v in neg_table:
        raw = neg_table[v]
        if "{reason_part_or_default}" in raw:
            text = raw.format(
                focus=focus,
                reason_part=reason_part,
                reason_part_or_default=reason_part or (tpl.get("neg_default_reason") or ""),
            )
        elif "{reason_part}" in raw:
            text = raw.format(focus=focus, reason_part=reason_part)
        else:
            text = raw
        # 模板尾部自带「——」，而 reason_* 模板自带前导「，」→ 拼出「——，」残句
        # （2026-10-08 实测交付报告首句：`…不是发力的时候——，主要因为…`）。
        return _dedash(wrap.format(focus=focus, text=text))
    if "凶" in v or "跌" in v:
        return (tpl.get("fallback_xiong") or "").format(focus=focus, v=v, reason_part=reason_part)
    if "吉" in v and "凶" not in v:
        return (tpl.get("fallback_ji") or "").format(focus=focus, v=v)
    return (tpl.get("fallback_neu") or "").format(focus=focus)


def _change_sentence(s4: dict, s2: dict) -> str:
    """动变：说清楚谁在动、对事情是帮还是扯后腿。"""
    tpl = _NARRATIVE_TPL.get("change_sentences") or {}
    details = (s4.get("details") or []) if s4 else []
    if not s4 or not s4.get("has_moving_lines") or not details:
        return tpl.get("no_moving") or ""

    details = s4.get("details") or []
    net = float(s4.get("net_effect") or 0)
    use_cat = s2.get("use_god_category") or "用神"

    def _fmt(key: str, **kw) -> str:
        return (tpl.get(key) or "").format(**kw)

    bits = []
    for d in details:
        if not isinstance(d, dict):
            continue
        pos = _pos_name(d.get("position"))
        rel = d.get("original_relation") or ""
        role = d.get("line_role") or ""
        ct = d.get("change_type") or ""
        chg = d.get("changed_branch") or ""
        if role == "用神":
            if "回头生" in ct:
                bits.append(_fmt("use_huisheng", pos=pos, rel=rel, chg=chg))
            elif "回头克" in ct:
                bits.append(_fmt("use_huike", pos=pos, rel=rel))
            elif "反吟" in ct:
                bits.append(_fmt("use_fanyin", pos=pos, rel=rel))
            else:
                bits.append(_fmt("use_moving", pos=pos, rel=rel))
        elif role == "原神":
            if "回头生" in ct or "化合" in ct:
                bits.append(_fmt("yuan_help", pos=pos, rel=rel, use_cat=use_cat))
            else:
                bits.append(_fmt("yuan_support", pos=pos, rel=rel, use_cat=use_cat))
        elif role == "忌神":
            if "回头克" in ct:
                bits.append(_fmt("taboo_self_hurt", pos=pos, rel=rel))
            elif "贪合" in str(d.get("effect_on_usegod") or "") or "合" in ct:
                bits.append(_fmt("taboo_bound", pos=pos, rel=rel))
            else:
                bits.append(_fmt("taboo_block", pos=pos, rel=rel))
        elif role == "仇神":
            bits.append(_fmt("foe", pos=pos, rel=rel))
        else:
            bits.append(_fmt("other", pos=pos, rel=(rel or "他爻")))

    if not bits:
        bits.append(tpl.get("bits_empty") or "")

    if net > 1.0:
        tail = tpl.get("tail_pos") or ""
    elif net < -1.0:
        tail = tpl.get("tail_neg") or ""
    else:
        tail = tpl.get("tail_neu") or ""
    return "；".join(bits) + "。" + tail


def _strip_internal_scores(text: str) -> str:
    """抹掉会漏进正文的内部量化分数（SKILL.md §3.2：禁把字段/评分公式贴进正文）。

    缺陷来源（2026-10-25 第两百六十七批）：step4 的格局 description 是给**引擎/备查**用的
    结构化文本，形如「用神弱（1.71）原神不现（仅伏藏或无援），绝处逢生反断为凶」。
    `_special_sentence` 把整段 `description` 原样填进 {desc}，于是交付正文里出现了
    「用神弱（1.71）」这类裸评分——实测见蛊之未济报告第 30 行。
    narrate 是**翻译层**，不得转贴内部读数：把 `（数字）` 折成「偏弱／乏力」的语气，
    分数照旧留在 JSON 里供复核，不动任何判据。
    """
    if not text:
        return text

    def _band(raw: str) -> str:
        try:
            v = float(raw)
        except ValueError:
            return ""
        # 与 step3 strength_level 的档位口径一致（仅供措辞，不参与判分）
        if v >= 3.5:
            return "有力"
        if v >= 2.0:
            return "不旺不弱"
        if v >= 0.0:
            return "偏弱"
        return "极弱"

    # 「用神弱（1.71）」→「用神偏弱」；「用神极弱（-1.63）」→「用神极弱」
    _BAND_RE = re.compile(r"(用神|世爻|原神)?(极弱|弱|偏弱|中和|旺)?（(-?\d+\.\d+)）")

    def _sub_band(m: re.Match) -> str:
        band = _band(m.group(3)) or (m.group(2) or "")
        word = f"{m.group(1) or ''}{band}"
        # 原串是「用神弱（1.71）原神不现」——括号一去，两词会粘成「偏弱原神」，
        # 故后面紧跟中文时补一个逗号断句。
        rest = text[m.end():m.end() + 1]
        if word and rest and "\u4e00" <= rest <= "\u9fff":
            word += "，"
        return word

    text = _BAND_RE.sub(_sub_band, text)
    # 「（量化参考 4.56，信号强度 70）」整句剔除
    text = re.sub(r"（\s*量化参考[^）]*）", "", text)
    return text


def _special_sentence(special, s3, s2, question: str) -> str:
    if not isinstance(special, dict):
        return ""
    tpl = _NARRATIVE_TPL.get("special_sentences") or {}
    pat = str(special.get("pattern") or "")
    desc = _strip_internal_scores(str(special.get("description") or ""))
    focus = _question_focus(question)
    empty = bool(s3.get("is_empty")) if s3 else False
    strength = str((s3 or {}).get("strength_level") or "")

    def _g(key: str, **kw) -> str:
        return (tpl.get(key) or "").format(**kw)

    if "近病逢空" in pat or "近病逢空" in desc:
        return (_NARRATIVE_TPL.get("strength_phrases") or {}).get("near_illness_void") or ""
    if "近病逢合" in pat:
        return (_NARRATIVE_TPL.get("change_sentences") or {}).get("near_he") or ""
    if "合处逢冲" in pat:
        if "婚" in focus or "婚姻" in focus:
            return _g("he_then_scatter_marriage")
        return _g("he_then_scatter", focus=focus)
    if "冲中逢合" in pat:
        return _g("chong_then_he")
    if "反吟" in pat:
        return _g("fan_yin")
    if "六冲" in pat:
        return _g("liu_chong", focus=focus)
    if "六合" in pat:
        return _g("liu_he", focus=focus)
    if "伏吟" in pat:
        return _g("fu_yin", focus=focus)
    if "游魂" in pat:
        return _g("you_hun", focus=focus)
    if "归魂" in pat:
        return _g("gui_hun", focus=focus)
    if "归禄" in pat or "禄" in pat:
        return _g("lu", focus=focus)
    if pat:
        return _g("other_pattern_desc", pat=pat, desc=desc) if desc else _g("other_pattern", pat=pat)
    if empty and any(x in strength for x in ("旺", "相", "中和")):
        return _g("void_but_rooted")
    return ""


def _timing_sentence(timing: dict, special, s3, s5: dict = None) -> str:
    """应期段：优先从 yingqi_dates 读日历日期，无则回退到地支描述。"""
    dates_blob = (s5 or {}).get("yingqi_dates") or {}
    calendar_dates = (dates_blob.get("dates") or []) if isinstance(dates_blob, dict) else []
    calendar_str = ""
    if calendar_dates:
        shown = []
        for d in calendar_dates[:3]:
            shown.append(f"{d.get('date','')}({d.get('description','')})")
        calendar_str = "、".join(shown)
    clashing = _BRANCH_CLASH_MAP
    combining = {b: (ps[0] if ps else "") for b, ps in _HE_MAP.items()}
    t = timing if isinstance(timing, dict) else {}
    keys = list(t.get("key_branches") or [])
    speed = str(t.get("speed") or "")
    use_br = str((s3 or {}).get("use_god_branch") or "")
    sp = ""
    if isinstance(special, dict):
        sp = str(special.get("pattern") or "") + str(special.get("description") or "")

    day_hint = ""
    if use_br:
        cl = clashing.get(use_br, "")
        co = combining.get(use_br, "")
        if "伏" in str(s3.get("is_fu", "") or ""):
            day_hint = NARRATIVE_HINTS["day_hint_fu_out"]
        elif cl and co:
            day_hint = NARRATIVE_HINTS["day_hint_value_or_clash_he"].format(use_br=use_br, cl=cl, co=co)
        elif cl:
            day_hint = NARRATIVE_HINTS["day_hint_value_or_clash"].format(use_br=use_br, cl=cl)
        else:
            day_hint = NARRATIVE_HINTS["day_hint_value"].format(use_br=use_br)

    base = select_timing_base(sp, speed, str((t or {}).get("summary_text") or ""), calendar_str)

    if "合处逢冲" in sp or "冲中逢合" in sp or "反吟" in sp:
        base += NARRATIVE_HINTS["timing_repeat"]

    if day_hint:
        base += NARRATIVE_HINTS["timing_day_detail"].format(day_hint=day_hint)
    elif keys:
        shown = "、".join(keys[:3])
        base += NARRATIVE_HINTS["timing_shown"].format(shown=shown)
    if calendar_str:
        base += NARRATIVE_HINTS["timing_calendar"].format(calendar_str=calendar_str)
    # 窗句（第一百九十三批·D1 第二半）：名次前 3 个不重复日历日折成区间——
    # 与 conclusion.应期窗口 同一派生口径；措辞按 AGENTS.md §一.3 钉死为「结构范围提示」不升格必应。
    _uniq = []
    for _d in calendar_dates:
        _v = _d.get("date")
        if _v and _v not in _uniq:
            _uniq.append(_v)
        if len(_uniq) >= 3:
            break
    if len(_uniq) >= 2:
        try:
            from datetime import date as _dt
            _ds = sorted(_dt.fromisoformat(x) for x in _uniq)
            _win = "%s—%s（跨%d日）" % (_ds[0].isoformat(), _ds[-1].isoformat(),
                                        (_ds[-1] - _ds[0]).days + 1)
            base += " " + NARRATIVE_HINTS["timing_window"].format(win=_win)
        except (ValueError, KeyError):
            pass
    return base


def _meaning_paragraph(verdict, s2, s3, special, question, factor_contribs=None) -> str:
    """第五段：综合定性 + 精简引用关键因子。"""
    use_cat = s2.get("use_god_category") or "用神"
    yuan = (s2.get("yuan_shen") or {}).get("category") or ""
    ji = (s2.get("ji_shen") or {}).get("category") or ""
    strength = str(s3.get("strength_level") or "") if s3 else ""
    focus = _question_focus(question)

    vdir = 1 if ("吉" in str(verdict) and "凶" not in str(verdict) and "不利" not in str(verdict)) else (
        -1 if ("凶" in str(verdict) or "跌" in str(verdict) or "不利" in str(verdict)) else 0
    )

    parts = []
    if vdir > 0:
        parts.append(_ADVICE_SOFT.get("push") or "")
    elif vdir < 0:
        parts.append(_ADVICE_SOFT.get("hold") or "")
    else:
        parts.append(_ADVICE_SOFT.get("wait") or "")

    if factor_contribs:
        def _factor_polarity(fc):
            p = fc.get("polarity")
            if p is None:
                s = fc.get("score") or 0
                p = 1 if s > 0 else (-1 if s < 0 else 0)
            return p

        def _sort_key(fc):
            explicit = 0 if fc.get("polarity") is not None else 1
            mag = abs(fc.get("score") or 0)
            return (explicit, -mag)
        pos_items = sorted(
            [fc for fc in factor_contribs if _factor_polarity(fc) > 0], key=_sort_key
        )[:2]
        neg_items = sorted(
            [fc for fc in factor_contribs if _factor_polarity(fc) < 0], key=_sort_key
        )[:2]
        if pos_items:
            pos_strs = []
            for fc in pos_items:
                nm = fc.get("name", "")
                reason = _clean_reason(fc.get("reason", ""), nm)
                pos_strs.append(f"{nm}" + (f"（{reason}）" if reason else ""))
            parts.append("有利面：" + "；".join(pos_strs) + "。")
        if neg_items:
            neg_strs = []
            for fc in neg_items:
                nm = fc.get("name", "")
                reason = _clean_reason(fc.get("reason", ""), nm)
                neg_strs.append(f"{nm}" + (f"（{reason}）" if reason else ""))
            parts.append("拖累面：" + "；".join(neg_strs) + "。")

    # 三处判据短语（绝处逢生／克多出暴／回头克自伤）的措辞全部在
    # data/narrative_templates.json#advice_soft，本层只按卦象结构选分支（SKILL.md）
    if any(x in strength for x in ("弱", "囚", "死")) and vdir > 0:
        parts.append((_ADVICE_SOFT.get("weak_but_pattern") or "")
                     + (_ADVICE_SOFT.get("weak_but_pattern_tail") or ""))
    if any(x in strength for x in ("弱", "囚", "死")) and vdir <= 0:
        parts.append((_ADVICE_SOFT.get("weak_and_bad") or "")
                     + (_ADVICE_SOFT.get("weak_and_bad_quote") or "")
                     + (_ADVICE_SOFT.get("weak_and_bad_tail") or ""))
    if "冲中逢合" in str(special or ""):
        parts.append(_ADVICE_SOFT.get("chong_then_he") or "")
    if "回头克" in str(special or ""):
        parts.append((_ADVICE_SOFT.get("huitou_ke_quote") or "")
                     + (_ADVICE_SOFT.get("internal_block") or ""))

    return "".join(parts)


def _clean_reason(reason: str, name: str) -> str:
    """去掉 factor_contribution.reason 里的技术备注，只留 15 字内的人类可读短句。"""
    if not reason:
        return ""
    r = re.sub(r"[（(]\s*[+-]?\d+[\d.]*[%]?\s*[）)]", "", reason)
    r = re.sub(r"【[^】]*】", "", r)
    r = r.replace(name, "")
    r = r.strip("，。：:, ")
    r = re.split(r"[，。；,;]", r, maxsplit=1)[0]
    if len(r) > 15:
        r = r[:15]
    return r.strip() or ""


def _resolve_bing_yao_shensha(result: dict) -> tuple[dict, dict]:
    """取 analyze 已有 bing_yao / shensha_panel；缺失时从思维链机械补算。"""
    concl = result.get("conclusion") or {}
    bing = result.get("bing_yao") or {}
    if not bing and isinstance(concl.get("病药"), dict):
        bing = concl["病药"]
    shen = result.get("shensha_panel") or {}
    if not shen and isinstance(concl.get("星煞"), dict):
        shen = concl["星煞"]
    if bing and shen:
        return bing, shen

    tc = result.get("thinking_chain") or {}
    s2 = tc.get("step2_use_god_identification") or {}
    s3 = tc.get("step3_strength_analysis") or {}
    if not s3:
        for v in tc.values():
            if isinstance(v, dict) and "strength_level" in v:
                s3 = v
                break
    try:
        from bing_yao_shensha import attach_shensha, evaluate_bing_yao
        if not bing and (s2 or s3):
            bing = evaluate_bing_yao(s2, s3, tc.get("step5_synthesis") or {})
        if not shen and result.get("divination_time"):
            shen = attach_shensha(result, s3)
    except Exception:
        pass
    return bing or {}, shen or {}


def _line_on_pos(line_name, use_pos) -> bool:
    """爻名（初六/九三/上九…）是否落在用神爻位。"""
    try:
        p = int(use_pos)
    except Exception:
        return False
    mark = {1: "初", 2: "二", 3: "三", 4: "四", 5: "五", 6: "上"}.get(p)
    return bool(mark) and mark in str(line_name or "")


def _line_plain(line_name, tpl: dict) -> str:
    s = str(line_name or "")
    words = (tpl.get("line_words") or {})
    for key, word in words.items():
        if key in s:
            return word
    return s


def _jiazhai_paragraph(result: dict) -> str:
    """家宅爻位取象短段（《黄金策·千金赋》家宅章）。

    出处（逐字，行号=data/sources/huangjince_dz.dz.txt）：
      L2533 夹注「凡内卦初爻为宅基，二爻为宅舍，三爻为门外，外卦四爻为父母，
            五爻为兄弟，六爻为妻财。内卦宅生人吉，外卦宅克人凶。」
      源L2536「合为门，冲为路，不论卦内之有无。」

    口径（SKILL.md 铁律三）：只说「看哪个爻」，**不断宅吉凶**；
    本段不进评分、不作吉凶断语来源（OPT-huangjince_dz-07）。
    """
    tpl = _NARRATIVE_TPL.get("jiazhai_take_image") or {}
    if not tpl:
        return ""
    question = str(result.get("question") or result.get("topic") or "")
    if not question:
        return ""
    if not any(k in question for k in (tpl.get("触发问法词") or [])):
        return ""

    yao_map = tpl.get("爻位取象_简") or tpl.get("爻位取象") or {}
    hexa = result.get("original_hexagram") or {}
    yao_lines = hexa.get("yao_lines") or []
    if not yao_lines:
        return ""
    world_pos = None
    for y in yao_lines:
        if isinstance(y, dict) and y.get("is_world"):
            world_pos = y.get("position")
            break
    try:
        world_pos = int(world_pos)
    except (TypeError, ValueError):
        world_pos = None

    pos_name = {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}
    parts = []
    for i in sorted(yao_map):
        mark = "，今世爻正在此位" if world_pos == int(i) else ""
        parts.append(f"{yao_map[i]}{mark}")
    inner_outer = tpl.get("内外生克_叙述") or ""
    door_road = tpl.get("门路取象_叙述") or ""
    tpl_str = tpl.get("段落模板") or ""
    if not tpl_str:
        return ""
    return tpl_str.format(yao_map="；".join(parts), inner_outer=inner_outer, door_road=door_road)


def _bing_yao_paragraph(result: dict) -> str:
    """病药短段：列出病与药，口吻偏向/有…信号/结构上（口径诚实）。"""
    tpl = _NARRATIVE_TPL.get("bing_yao") or {}
    if not tpl:
        return ""
    bing, _ = _resolve_bing_yao_shensha(result)
    illness = (bing or {}).get("illness") or []
    medicine = (bing or {}).get("medicine") or []
    if not illness and not medicine:
        return ""

    ill_phrases = tpl.get("illness_phrases") or {}
    med_phrases = tpl.get("medicine_phrases") or {}
    joiner = tpl.get("item_joiner") or "；"
    ills = [ill_phrases.get(x.get("code")) or x.get("label") or ""
            for x in illness if isinstance(x, dict)]
    meds = [med_phrases.get(x.get("code")) or x.get("label") or ""
            for x in medicine if isinstance(x, dict)]
    ills = [x for x in ills if x]
    meds = [x for x in meds if x]
    if not ills and not meds:
        return ""

    intro = tpl.get("intro") or ""
    tail = tpl.get("tail") or ""
    if ills and meds:
        core = (
            f"{intro}"
            f"{tpl.get('illness_lead') or '病'}有——{joiner.join(ills)}"
            f"{tpl.get('pair_joiner') or '；药偏向：'}{joiner.join(meds)}"
        )
    elif ills:
        core = f"{intro}{tpl.get('only_illness_lead') or '病有——'}{joiner.join(ills)}"
    else:
        core = f"{intro}{tpl.get('only_medicine_lead') or '药偏向——'}{joiner.join(meds)}"
    return f"{core}。{tail}".strip()


def _shensha_paragraph(result: dict, use_pos=None) -> str:
    """星煞短提及：仅临爻/临日，不吉凶夸张；无命中不硬造段。"""
    tpl = _NARRATIVE_TPL.get("shensha") or {}
    if not tpl:
        return ""
    _, shen = _resolve_bing_yao_shensha(result)
    stars = (shen or {}).get("shensha") or []
    if not stars:
        return ""

    max_items = int(tpl.get("max_items") or 3)
    joiner = tpl.get("joiner") or "；"
    seen: set[str] = set()
    mentions: list[str] = []

    def _push(text: str, key: str) -> None:
        if text and key not in seen and len(mentions) < max_items:
            mentions.append(text)
            seen.add(key)

    for s in stars:
        if not isinstance(s, dict):
            continue
        name = str(s.get("name") or "")
        if not name:
            continue
        on_lines = s.get("on_lines") or []
        if any(_line_on_pos(ln, use_pos) for ln in on_lines):
            _push((tpl.get("on_use_god") or "{name}临用爻").format(name=name), name)
    for s in stars:
        if not isinstance(s, dict):
            continue
        name = str(s.get("name") or "")
        if not name or name in seen:
            continue
        on_lines = [ln for ln in (s.get("on_lines") or []) if not _line_on_pos(ln, use_pos)]
        if on_lines:
            line = _line_plain(on_lines[0], tpl)
            _push((tpl.get("on_line") or "{name}临{line}").format(name=name, line=line), name)
    for s in stars:
        if not isinstance(s, dict):
            continue
        name = str(s.get("name") or "")
        if not name or name in seen:
            continue
        if s.get("on_day"):
            _push((tpl.get("on_day") or "{name}临日").format(name=name), name)

    if not mentions:
        return ""
    lead = tpl.get("lead") or ""
    tail = tpl.get("tail") or ""
    core = f"{lead}{joiner.join(mentions)}"
    return f"{core}。{tail}".strip() if tail else f"{core}。"


# ────────────────────────────────────────────────────────────────
# human_narrative 部分：解读正文编排与导出
# ────────────────────────────────────────────────────────────────

def _pattern_advice_hint(pattern_tag: str, verdict: str, timing: dict) -> str:
    """根据当前卦象的 pattern 标签，返回一条场景化的附加建议。"""
    v = str(verdict or "")
    tag = str(pattern_tag or "").strip()
    if not tag:
        return ""

    cal = ""
    dates_blob = (timing or {}).get("yingqi_dates") or {}
    if isinstance(dates_blob, dict):
        ds = dates_blob.get("dates") or []
        if ds:
            cal = str(ds[0].get("date", ""))

    HINTS = _NARRATIVE_TPL.get("pattern_hints") or {}
    text = HINTS.get(tag, "")
    if not text:
        return ""
    if tag == "原神绝位·用神失源" and cal:
        text = text + (HINTS.get("原神绝位·补转机") or "").format(cal=cal)
    if tag == "兄弟持世":
        text = text + ((HINTS.get("兄弟持世·补") or "").format(cal=cal) if cal else (HINTS.get("兄弟持世·补_default") or ""))
    # 《文王金钱课·诸爻持事诀》书源原句（OPT-wenwang_jinqianke_dz-01）：
    # **只作叙述层旁证**——在现代意译句后附一句「书云」，不改判定、不进结构、不评分。
    # 措辞守铁律三：只说「书云/古法云」，不把古判语转成对用户的确定性断言。
    _wq = _wenwang_quote(tag)
    if _wq:
        text = f"{text}（书云：「{_wq}」）"
    return text


def _wenwang_quote(tag: str) -> str:
    """六亲持世 → 《文王金钱课》对应书源原句；无对应返回 ""（不硬配）。"""
    W = ((_NARRATIVE_TPL.get("pattern_hints") or {}).get("_wenwang_chishi") or {})
    key = "官鬼持世" if tag == "鬼爻持世" else tag
    e = W.get(key) or W.get("世爻") or {}
    return (e.get("quote") or "") if isinstance(e, dict) else ""


def _extract_pattern_tags(tc: dict) -> set:
    """提取标准化格局标签集合（含所有「格局-」前缀 tag）。

    第三百五十一批：优先读 analyze 产出的结构化 `thinking_chain.pattern_tags`
    （CONTRACT §六-7 第一半）；只有旧输入没有该键时才回落正则解析
    `reasoning_chain` 的 `[格局] A|B` 串（兼容历史 analyze JSON）。
    """
    tags: set = set()
    structured = tc.get("pattern_tags")
    if structured:
        for token in structured:
            t = str(token).strip()
            if not t:
                continue
            tags.add(t)
            if t.startswith("格局-"):
                tags.add(t[3:])
            else:
                tags.add("格局-" + t)
    else:
        chain = tc.get("reasoning_chain") or []
        for entry in chain:
            s = str(entry)
            if "[格局]" in s:
                try:
                    body = s.split("]", 1)[1].strip()
                    for token in body.split("|"):
                        t = token.strip()
                        if not t:
                            continue
                        tags.add(t)
                        if t.startswith("格局-"):
                            tags.add(t[3:])
                        else:
                            tags.add("格局-" + t)
                except Exception:
                    continue
            elif "[格局要点]" in s:
                try:
                    body = s.split("]", 1)[1].strip()
                    for token in body.split("|"):
                        t = token.strip()
                        if t:
                            tags.add(t)
                except Exception:
                    continue
    sp = (tc.get("step5_synthesis") or {}).get("special_pattern") or {}
    if isinstance(sp, dict) and sp.get("pattern"):
        tags.add(str(sp["pattern"]))
    return tags


def _select_relevant_quotes(tc: dict) -> list:
    """按 reasoning_chain 中卦象格局标签打分，选出最相关的 2 条引文。"""
    tags = _extract_pattern_tags(tc)
    if not tags:
        raw = (tc.get("step5_synthesis", {}) or {}).get("classical_quotes") or []
        return [{"source": q.get("source", "经典"), "quote": q.get("quote"),
                 "quote_kind": q.get("quote_kind")}
                for q in raw[:2] if isinstance(q, dict) and q.get("quote")]

    raw_quotes = (tc.get("step5_synthesis", {}) or {}).get("classical_quotes") or []
    scored: list = []
    for idx, q in enumerate(raw_quotes):
        if not isinstance(q, dict) or not q.get("quote"):
            continue
        qp = str(q.get("pattern") or "")
        score = 0
        if qp in tags:
            score += 3
        for real_tag in tags:
            if qp != real_tag and qp in real_tag and len(qp) >= 2:
                score += 1
                break
        for real_tag in tags:
            related = _PATTERN_QUOTE_RELEVANCE.get(real_tag, [])
            if qp in related:
                score += 1
        forward_related = _PATTERN_QUOTE_RELEVANCE.get(qp, [])
        for fr in forward_related:
            if fr in tags:
                score += 1
        scored.append((score, -idx, q))
    scored.sort(key=lambda x: (-x[0], x[1]))
    filtered = [item for item in scored if item[0] > 0]
    top = filtered[:2] if filtered else scored[:2]
    return [{"source": q.get("source", "经典"), "quote": q.get("quote"),
             "quote_kind": q.get("quote_kind")} for _, _, q in top]


def _ensure_thinking_chain(result: dict) -> dict:
    """已停用——铁律一合规清理。"""
    raise RuntimeError(
        "thinking_chain 缺失，不应在交付路径外就地重建——"
        "请检查上游 analyze / run_thinking_chain 是否执行成功；"
        "铁律一（SKILL.md）要求机械运算统一由主线引擎完成。"
    )


def _build_explain_summary(factor_contribs: list, focus: str) -> str:
    """将 factor_contributions 翻译成人话段落，而非字段罗列。"""
    if not factor_contribs:
        return "各因子均衡，无明显偏向。"

    top = [fc for fc in factor_contribs[:6] if fc.get("score", 0) != 0]
    if not top:
        return "各因子均衡，无明显偏向。"

    positive = [fc for fc in top if fc.get("score", 0) > 0]
    negative = [fc for fc in top if fc.get("score", 0) < 0]

    def _short_reason(reason: str, name: str) -> str:
        if not reason:
            return ""
        r = re.sub(r"[（(]\s*[+-]?\d+[\d.]*[%]?\s*[）)]", "", reason)
        r = re.sub(r"【[^】]*】", "", r)
        r = r.replace(name, "")
        r = r.strip("，。：:, ")
        r = re.split(r"[，。；,;]", r, maxsplit=1)[0]
        if len(r) > 15:
            r = r[:15]
        r = r.strip()
        if not r or len(r) <= 1:
            return ""
        return r

    pos_parts = []
    for fc in positive[:3]:
        name = fc.get("name", "")
        reason = _short_reason(fc.get("reason", ""), name)
        tail = f"（{reason}）" if reason else ""
        pos_parts.append(f"{name}{tail}")

    neg_parts = []
    for fc in negative[:3]:
        name = fc.get("name", "")
        reason = _short_reason(fc.get("reason", ""), name)
        tail = f"（{reason}）" if reason else ""
        neg_parts.append(f"{name}{tail}")

    if pos_parts and neg_parts:
        body_text = "；".join(pos_parts) + "；拖累面：" + "；".join(neg_parts)
        summary = f"{focus}吉凶相杂，宜稳扎稳打。"
        header = "推因 —— 利好面"
    elif pos_parts:
        body_text = "；".join(pos_parts)
        summary = f"{focus}有明确助力，可顺势而为。"
        header = "推因 —— 利好面"
    else:
        body_text = "；".join(neg_parts)
        summary = f"{focus}阻力不小，宜谨慎守待时机。"
        header = "推因 —— 拖累面"

    return f"{header}：{body_text}。{summary}"


def build_human_narrative(result: dict) -> dict:
    """
    生成完整解读正文（唯一交付口吻）。
    兼容旧字段名，便于报告/门户复用。
    """
    if not result.get("thinking_chain"):
        result = dict(result)  # 浅拷贝避免污染原始数据
        result["thinking_chain"] = _ensure_thinking_chain(result)

    tc = result.get("thinking_chain") or {}
    s1 = tc.get("step1_situational_reading") or {}
    s2 = tc.get("step2_use_god_identification") or {}
    s3 = tc.get("step3_strength_analysis") or {}
    s4 = tc.get("step4_change_analysis") or {}
    s5 = tc.get("step5_synthesis") or {}

    question = result.get("question") or ""
    hex_name = (result.get("original_hexagram") or {}).get("name") or s1.get("hexagram_name") or ""
    changed_name = ((result.get("changed_hexagram") or {}).get("name")) or ""
    palace = (result.get("original_hexagram") or {}).get("palace") or s1.get("palace") or ""
    generation = (result.get("original_hexagram") or {}).get("generation") or ""
    dt = result.get("divination_time") or {}
    empty = result.get("empty_branches") or []

    verdict = s5.get("verdict") or "未知"
    # T29 第二批：读三段 verdict 新字段（旧 verdict 作为 fallback）
    present_verdict = s5.get("present_verdict") or verdict
    rescue_verdict = s5.get("rescue_verdict") or verdict
    timing_speed = s5.get("timing_speed") or ""
    score = s5.get("final_score")
    conf = s5.get("signal_strength", s5.get("confidence"))
    use_cat = s2.get("use_god_category") or "用神"
    use_el = s2.get("use_god_element") or ""
    use_br = (s2.get("selected_use_god") or {}).get("earthly_branch") or s3.get("use_god_branch") or ""
    use_pos = (s2.get("selected_use_god") or {}).get("position")
    strength = s3.get("strength_level") or ""
    timing = s5.get("timing") or {}
    special = s5.get("special_pattern") or {}
    special_pat = special.get("pattern") if isinstance(special, dict) else ""
    factor_contribs = s5.get("factor_contributions") or []
    yuan_greedy = any("贪合" in str(fc.get("factor", "")) for fc in factor_contribs)
    yuan_diagnosis = ""
    for fc in factor_contribs:
        n = str(fc.get("name", ""))
        r = str(fc.get("reason", ""))
        if "原神" in n or "原神" in r:
            yuan_diagnosis = r
            break
    yuan_data = s2.get("yuan_shen", {}) or {}
    yuan_moving = any(
        (p or {}).get("is_moving") for p in (yuan_data.get("positions") or [])
    ) if isinstance(yuan_data, dict) else False
    pattern_label = ""
    if isinstance(special, dict) and special.get("pattern") is not None:
        pattern_label = str(special["pattern"])
    if not pattern_label:
        fallback_tags = _extract_pattern_tags(tc)
        _priority = ["久病逢空", "久病逢冲", "近病逢空", "近病逢合",
                     "六冲卦", "六合卦", "反吟", "伏吟", "游魂", "归魂",
                     "回头生", "回头克", "化格", "三合成局", "绝处逢生",
                     "伏神得出", "伏神不得出", "暗动", "官鬼持世",
                     "兄弟持世", "子孙持世", "父母持世", "妻财持世",
                     "原神绝位·用神失源", "月破"]
        for p in _priority:
            if p in fallback_tags:
                pattern_label = p
                break

    focus = _question_focus(question)

    title_bits = []
    if question:
        title_bits.append(focus)
    if hex_name:
        title_bits.append(hex_name + ("之" + changed_name if changed_name else "卦"))
    title = " · ".join(title_bits) if title_bits else "六爻解读"

    hex_desc = f"{hex_name}"
    if palace or generation:
        hex_desc += f"（{palace}宫{('·' + generation) if generation else ''}）"
    if changed_name:
        hex_desc += f"，变卦{changed_name}"
    time_desc = ""
    if dt:
        time_desc = f"{dt.get('month_stem_branch','')}月 {dt.get('day_stem_branch','')}日".strip()
    empty_desc = f"旬空{('、'.join(empty))}" if empty else ""

    p1 = _verdict_opening(verdict, focus, pattern_label, yuan_diagnosis)
    scene = f"这副卦是{hex_desc}"
    if time_desc:
        scene += f"，起卦于{time_desc}"
    if empty_desc:
        scene += f"，{empty_desc}"
    p1 += scene + "。"

    # T29 第二批：三段 verdict 分段叙述（当下 vs 最终）
    p_rescue = ""
    if rescue_verdict != present_verdict:
        p_rescue = f"当下{present_verdict}，但最终{rescue_verdict}（救应链分段）。"

    p2 = (
        f"事情的关键看{use_cat}"
        + (f"（五行属{use_el}）" if use_el else "")
        + (f"，落在{use_br}{_pos_name(use_pos)}" if use_br else "")
        + "。"
        + _strength_sentence(strength, use_cat, use_br, use_pos,
                             yuan_moving=yuan_moving, yuan_greedy=yuan_greedy)
    )

    p3 = _change_sentence(s4, s2)
    p4 = _special_sentence(special, s3, s2, question)
    p5 = _meaning_paragraph(verdict, s2, s3, special, question, factor_contribs)

    p_bing = _bing_yao_paragraph(result)
    p_jiazhai = _jiazhai_paragraph(result)
    p_shen = _shensha_paragraph(result, use_pos=use_pos)

    body = [x for x in (p1, p_rescue, p2, p_bing, p_jiazhai, p_shen, p3, p4, p5) if x]
    lead = p1

    timing_plain = _timing_sentence(timing, special, s3, s5)

    try:
        advice = generate_advice(verdict, question or focus, result)
    except Exception:
        advice = []
    if not advice:
        if "凶" in str(verdict) or "跌" in str(verdict):
            advice = list(NARRATIVE_HINTS["advice_xiong"])
        else:
            advice = list(NARRATIVE_HINTS["advice_ji"])
    pattern_tag = pattern_label or ""
    extra_advice = _pattern_advice_hint(pattern_tag, verdict, timing)
    if extra_advice and len(advice) >= 2:
        advice = advice[:-1] + [extra_advice]
    elif extra_advice:
        advice = advice + [extra_advice]

    quotes = _select_relevant_quotes(tc)

    caveat = (
        NARRATIVE_HINTS["disclaimer"]
    )
    conf_note = ""

    factor_contribs = s5.get("factor_contributions") or []
    explain_summary = _build_explain_summary(factor_contribs, focus)

    process = []
    for label, text in (
        ("观局", s1.get("summary_text") or ""),
        ("定用", s2.get("summary_text") or ""),
        ("断旺", s3.get("summary_text") or ""),
        ("察变", s4.get("summary_text") or ""),
        ("综合", s5.get("summary_text") or ""),
    ):
        if text:
            process.append({"label": label, "text": str(text)})

    # 355 批：analyze 不再产叙述链/总摘要；从同一批 step 事实重建（旧 JSON 仍优先原键）
    rc_lines = tc.get("reasoning_chain") or build_reasoning_chain(result)
    summary_text = tc.get("summary_text") or build_summary(result)

    return {
        "title": title,
        "question": question,
        "hexagram": hex_name,
        "changed_hexagram": changed_name,
        "verdict": verdict,
        "final_score": score,
        "signal_strength": conf,
        "confidence": conf,
        "headline": p1 if len(p1) < 80 else _verdict_opening(verdict, focus),
        "lead": lead,
        "body": body,
        "reading": "\n\n".join(body),
        "timing_plain": timing_plain,
        "advice": list(advice)[:4],
        "caveat": caveat,
        "confidence_note": conf_note,
        "classical_quotes": quotes,
        "process": process,
        "plain_summary": body[0] if body else "",
        "what_it_means": p5,
        "use_god": {
            "category": use_cat,
            "element": use_el,
            "branch": use_br,
            "position": use_pos,
            "strength": strength,
            "strength_plain": _strength_sentence(strength, use_cat, use_br, use_pos),
        },
        "special_pattern": special_pat or "",
        "reasoning_chain": rc_lines,
        "summary_text": summary_text,
        "factor_contributions": factor_contribs,
        "explain_summary": explain_summary,
    }


def render_human_markdown(narrative: dict) -> str:
    """导出为一篇完整解读，而不是「人话章节 + 附录」两张皮。"""
    if not narrative:
        return ""
    lines = [f"# {narrative.get('title') or narrative.get('headline') or '六爻解读'}", ""]
    if narrative.get("question"):
        lines += [f"问：{narrative['question']}", ""]
    for para in narrative.get("body") or []:
        lines += [para, ""]
    lines += [f"**时间上**：{narrative.get('timing_plain') or ''}", ""]
    lines += ["**可以这样做**："]
    for i, a in enumerate(narrative.get("advice") or [], 1):
        lines.append(f"{i}. {a}")
    if narrative.get("confidence_note"):
        lines += ["", narrative["confidence_note"]]
    if narrative.get("classical_quotes"):
        # 引导句外置 narrative_templates.json#narrate_shell.quote_lead（此前与 narrate.py
        # 各内联一份字面量，语料审计判该键零消费——两处合一后单一出处）
        lines += ["", _NARRATIVE_TPL.get("narrate_shell", {}).get("quote_lead", "古人类似情境也说过：")]
        for q in narrative["classical_quotes"]:
            tag = "（今译）" if q.get("quote_kind") == "paraphrase" else ""
            lines.append(f"- （{q['source']}）{tag}{q['quote']}")
    process = narrative.get("process") or []
    if process:
        lines += ["", "---", "", "## 推演过程（备查）", ""]
        for p in process:
            lines.append(f"**{p['label']}**：{p['text']}")
    lines += ["", "---", narrative.get("caveat") or ""]
    return "\n".join(lines)


build_reading = build_human_narrative
