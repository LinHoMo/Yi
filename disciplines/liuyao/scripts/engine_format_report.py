# -*- coding: utf-8 -*-
"""六爻报告排版：format_reading_output 的各段落（自 engine_format.py 按段切出）。

纯搬移不改写逻辑：每个函数对应原报告中的一段（求测信息 / 卦象 / Step1–5 /
格局 / 卜象 / 应期 / 判语 / 页脚），顺序由调用方编排。

本模块**不 import engine_format**，依赖单向：engine_format → engine_format_report。
验收口径：拆分前后报告文本逐字符一致（零指纹漂移）。
"""

from __future__ import annotations

REPORT_WIDTH = 52  # 报告宽度（原 format_reading_output 内的 W）


def build_head(result: dict, dt: dict, empty: list, W: int = REPORT_WIDTH) -> list:
    """标题头 + 求测信息 + 干支历法。"""
    lines = []
    lines.append("=" * W)
    lines.append("六 爻 纳 甲 占 卜 报 告".center(W))
    lines.append("=" * W)
    lines.append("")

    # ── 求测信息 ──
    lines.append("【求测信息】")
    lines.append(f"  问  题：{result.get('question', '未指明')}")
    lines.append(f"  方  式：{result.get('method', '铜钱摇卦')}")
    lines.append(f"  时  间：{dt.get('datetime', '未知')}")
    lines.append("")

    # ── 干支历法 ──
    lines.append("【干支历法】")
    lines.append(f"  年柱：{dt.get('year_stem_branch', '?')}　"
                 f"月柱：{dt.get('month_stem_branch', '?')}")
    lines.append(f"  日柱：{dt.get('day_stem_branch', '?')}　"
                 f"时柱：{dt.get('hour_stem_branch', '?')}")
    if empty:
        lines.append(f"  旬  空：{', '.join(empty)}")
    lines.append("")
    return lines


def build_hexagram(oh: dict, ch: dict, hints: list, W: int = REPORT_WIDTH) -> list:
    """卦象一览 + 排盘详表 + 变卦 + 用神建议。"""
    lines = []
    lines.append("─" * W)
    lines.append("【卦象一览】")
    lines.append(f"  本 卦：{oh.get('name', '?')}　"
                 f"{oh.get('upper_trigram', '?')}上{oh.get('lower_trigram', '?')}下　"
                 f"第{oh.get('sequence', '?')}卦")
    lines.append(f"  归 属：{oh.get('palace', '?')}宫（{oh.get('palace_element', '?')}行）"
                 f"　{oh.get('generation', '?')}卦")
    if oh.get('judgment'):
        lines.append(f"卦　辞：{oh['judgment']}")
    lines.append("")

    # 排盘表（上爻→下爻）
    yao_lines = oh.get("yao_lines", [])
    if yao_lines:
        lines.append("  排盘详表：")
        lines.append(f"  {'爻位':<4}{'六神':<5}{'六亲':<5}{'地支':<5}{'干支':<7}{'动静':<5}{'标记':<6}")
        lines.append("  " + "-" * (W - 4))
        for yao in reversed(yao_lines):
            pos_s = yao.get("name", "?")
            spirit_s = yao.get("six_spirit", "?")
            rel_s = yao.get("six_relation", "?")
            branch_s = yao.get("earthly_branch", "?")
            stem_s = f"{yao.get('heavenly_stem', '')}{branch_s}"
            moving_s = "动" if yao.get("is_moving") else "静"
            markers = []
            if yao.get("is_world"):
                markers.append("世")
            if yao.get("is_response"):
                markers.append("应")
            if yao.get("is_empty"):
                markers.append("空")
            mark_s = "/".join(markers) if markers else "－"
            lines.append(
                f"  {pos_s:<4}{spirit_s:<5}{rel_s:<5}{branch_s:<5}{stem_s:<7}{moving_s:<5}{mark_s:<6}"
            )
        lines.append("")

    # 变卦
    if ch:
        lines.append(f"  变 卦：{ch.get('name', '?')}")
        if ch.get('judgment'):
            lines.append(f"  变卦辞：{ch['judgment']}")
        changed_pos = ch.get("changed_lines", [])
        if changed_pos:
            pos_txt = "、".join(f"第{n}爻" for n in changed_pos)
            lines.append(f"  动 爻：{pos_txt}")
        lines.append("")

    # ── 用神建议 ──
    if hints:
        lines.append("─" * W)
        lines.append("【用神建议】")
        for h in hints[:5]:
            lines.append(f"  · {h}")
        lines.append("")
    return lines


def build_step_block(title: str, step: dict, body) -> list:
    """五步思维链通用外框：标题头 + body(step) + 尾框。

    原实现中每步都是「空行 + ┌标题┐ + (if step: 内容) + └┘」，此处收成一个外框函数。
    """
    lines = ["", f"  ┌──{title}┐"]
    if step:
        lines.extend(body(step))
    lines.append("  └──────────────────────────────────────────┘")
    return lines


def _step1_body(step1: dict) -> list:
    lines = [f"  │ 本卦：{step1.get('hexagram_name', '?')}　"
             f"{step1.get('palace', '?')}宫　{step1.get('palace_element', '?')}行"]
    desc1 = step1.get("description", "")
    if desc1:
        # 分行显示长描述
        for para in desc1.split("。"):
            para = para.strip()
            if para:
                lines.append(f"  │ {para}")
    return lines


def _step2_body(step2: dict) -> list:
    lines = [f"  │ 用神：{step2.get('use_god_category', '?')}　"
             f"五行：{step2.get('use_god_element', '?')}"]
    pos2 = step2.get("selected_position")
    if pos2:
        lines.append(f"  │ 位置：第{pos2}爻　"
                     f"六亲：{step2.get('selected_relation', '?')}")
    desc2 = step2.get("description", "")
    if desc2:
        for para in desc2.split("。"):
            para = para.strip()
            if para:
                lines.append(f"  │ {para}")
    # 原神/忌神
    ys_text = step2.get("yuan_shen_text", "")
    js_text = step2.get("ji_shen_text", "")
    if ys_text:
        lines.append(f"  │ 原神：{ys_text}")
    if js_text:
        lines.append(f"  │ 忌神：{js_text}")
    return lines


def _step3_body(step3: dict) -> list:
    strength = step3.get("strength_level", "?")
    eff_score = step3.get("effective_score", 0)
    lines = [f"  │ 旺衰等级：{strength}（评分 {eff_score:.2f}）"]
    desc3 = step3.get("description", "")
    if desc3:
        for para in desc3.split("。"):
            para = para.strip()
            if para:
                lines.append(f"  │ {para}")
    # 关键因素
    factors = step3.get("key_factors", step3.get("factors", []))
    if isinstance(factors, list) and factors:
        lines.append(f"  │ 关键因素：")
        for f in factors[:6]:
            lines.append(f"  │   · {f}")
    return lines


def _step4_body(step4: dict) -> list:
    net_eff = step4.get("net_effect", 0)
    net_desc = step4.get("net_effect_description", "无动爻")
    lines = [f"  │ 动变净效应：{net_eff:+.2f}（{net_desc}）"]
    desc4 = step4.get("description", "")
    if desc4:
        for para in desc4.split("。"):
            para = para.strip()
            if para:
                lines.append(f"  │ {para}")
    # 逐爻分析
    yaos_detail = step4.get("yao_analysis", step4.get("moving_details", []))
    if isinstance(yaos_detail, list) and yaos_detail:
        lines.append(f"  │ 逐爻分析：")
        for yd in yaos_detail[:6]:
            if isinstance(yd, dict):
                yd_pos = yd.get("position", "?")
                yd_desc = yd.get("description", yd.get("analysis", ""))
                if not yd_desc and yd.get("change_type"):
                    yd_desc = yd["change_type"]
                if yd_desc:
                    lines.append(f"  │   第{yd_pos}爻：{yd_desc}")
            elif isinstance(yd, str) and yd:
                lines.append(f"  │   {yd}")
    return lines


def _step5_body(step5: dict) -> list:
    verdict = step5.get("verdict", "?")
    final_score = step5.get("final_score", 0)
    verdict_desc = step5.get("verdict_description", "")
    confidence = step5.get("confidence", "?")
    conf_desc = step5.get("confidence_description", "")

    lines = [f"  │ 判　语：{verdict}（{final_score:.2f}分）"]
    if verdict_desc:
        lines.append(f"  │ 说　明：{verdict_desc}")
    lines.append(f"  │ 置信度：{confidence}%（{conf_desc}）")

    # 格局识别
    sp = step5.get("special_pattern", {})
    if isinstance(sp, dict) and sp.get("pattern"):
        lines.append(f"  │ 格　局：{sp['pattern']} — {sp.get('description', '')}")

    # 各项调整明细
    adj_items = []
    bc = step5.get("base_score", 0)
    adj_items.append(f"基础旺衰 {bc:.2f}")
    ce = step5.get("change_net_effect", 0)
    if ce != 0:
        adj_items.append(f"动变 {ce:+.2f}")
    ha = step5.get("hex_adjustment", 0)
    if ha != 0:
        hr = step5.get("hex_adjustment_reason", "")
        adj_items.append(f"卦体 {ha:+.1f}（{hr}）")
    sa = step5.get("spirit_adjustment", 0)
    if sa != 0:
        sr = step5.get("spirit_adjustment_reasons", "")
        if isinstance(sr, list) and sr:
            sr = "、".join(sr)
        adj_items.append(f"六神 {sa:+.1f}（{sr}）")
    tp_s = step5.get("tp_score", 0)
    if tp_s != 0:
        tp_r = step5.get("tp_reason", "")
        adj_items.append(f"三刑 {tp_s:+.1f}（{tp_r}）")
    dmb = step5.get("dmb_adjustment", 0)
    if dmb != 0:
        adj_items.append(f"日月合 {dmb:+.2f}")
    sb_a = step5.get("sb_adjustment", 0)
    if sb_a != 0:
        adj_items.append(f"六破 {sb_a:+.2f}")
    hm_c = step5.get("hidden_movement_count", 0)
    if hm_c and hm_c > 0:
        hm_r = step5.get("hidden_movement_reason", "")
        hm_m = step5.get("hidden_movement_modifier", 0)
        adj_items.append(f"暗动 {hm_m:+.1f}（{hm_r}）")
    ghr = step5.get("greedy_harmony_reason", "")
    if ghr:
        ghs = step5.get("greedy_harmony_score", 0)
        adj_items.append(f"贪合 {ghs:+.2f}（{ghr}）")
    pa = step5.get("pattern_adjustment", 0)
    if pa != 0:
        adj_items.append(f"格局 {pa:+.1f}")

    if adj_items:
        lines.append(f"  │ 评分明细：{' + '.join(adj_items)} = {final_score:.2f}")
    return lines


def build_steps(step1: dict, step2: dict, step3: dict, step4: dict, step5: dict, W: int = REPORT_WIDTH) -> list:
    """五步思维链整体（含章节头与 Step1–5 五个外框）。"""
    lines = ["=" * W, "【五步思维链分析】", "=" * W]
    lines.extend(build_step_block(" Step 1 ─ 观局 ──────────────────────────", step1, _step1_body))
    lines.extend(build_step_block(" Step 2 ─ 定用神 ────────────────────────", step2, _step2_body))
    lines.extend(build_step_block(" Step 3 ─ 断旺衰 ────────────────────────", step3, _step3_body))
    lines.extend(build_step_block(" Step 4 ─ 察动变 ────────────────────────", step4, _step4_body))
    lines.extend(build_step_block(" Step 5 ─ 综合判断 ──────────────────────", step5, _step5_body))
    return lines


def build_patterns(aa: dict, step5: dict, sp: dict, W: int = REPORT_WIDTH) -> list:
    """格局识别摘要：advanced_analysis 各项 + 特殊格局。"""
    lines = ["", "─" * W, "【格局识别】"]
    patterns_found = []
    if isinstance(aa, dict):
        # 伏藏
        hs = aa.get("hidden_spirit_analysis", {})
        if isinstance(hs, dict) and hs.get("has_hidden_spirit"):
            patterns_found.append(f"伏藏：{hs.get('summary', '')}")
        # 暗动
        hm = aa.get("hidden_movement", {})
        if isinstance(hm, dict) and hm.get("has_hidden_movement"):
            patterns_found.append(f"暗动：{hm.get('summary', '')}")
        # 月破
        mb = aa.get("monthly_break", {})
        if isinstance(mb, dict) and mb.get("has_monthly_break"):
            patterns_found.append(f"月破：{mb.get('summary', '')}")
        # 三合局
        tc = aa.get("triple_combo", {})
        if isinstance(tc, dict) and tc.get("has_triple_combo"):
            patterns_found.append(f"三合局：{tc.get('summary', '')}")
        # 进退神
        ar = aa.get("advance_retreat", {})
        if isinstance(ar, dict) and ar.get("has_advance_retreat"):
            patterns_found.append(f"进退神：{ar.get('summary', '')}")
        # 六合六冲
        ch_aa = aa.get("clash_harmony", {})
        if isinstance(ch_aa, dict) and ch_aa.get("summary"):
            patterns_found.append(f"卦格：{ch_aa['summary']}")
        # 反吟伏吟
        rp = aa.get("repetition", {})
        if isinstance(rp, dict) and rp.get("summary"):
            patterns_found.append(f"吟反：{rp['summary']}")
        # 三刑
        tp = aa.get("three_punishments", {})
        if isinstance(tp, dict) and tp.get("has_punishment"):
            patterns_found.append(f"三刑：{tp.get('summary', '')}")
        # 六亲持世
        sy = aa.get("shi_yao_relation", {})
        if isinstance(sy, dict) and sy.get("description"):
            patterns_found.append(f"六亲持世：{sy['description']}")
        # 纳音
        ny = aa.get("nayin", {})
        if isinstance(ny, dict) and ny.get("description"):
            patterns_found.append(f"纳音：{ny['description']}")

    if step5 and isinstance(sp, dict) and sp.get("pattern"):
        patterns_found.append(f"特殊格局：{sp['pattern']}（{sp.get('description', '')}）")

    if patterns_found:
        for p in patterns_found:
            lines.append(f"  · {p}")
    else:
        lines.append("  （无特殊格局）")
    lines.append("")
    return lines


def build_trigram(result: dict, W: int = REPORT_WIDTH) -> list:
    """卜象解析（可选段：无卜象则返回空列表，由调用方决定是否落行）。"""
    ti_r = result.get("trigram_interpretation") if isinstance(result, dict) else None
    if not (ti_r and isinstance(ti_r, dict) and not ti_r.get("error")):
        return []
    try:
        from trigram_symbolism import format_trigram_interpretation_text as _fmt_trigram_r
        tri_lines = _fmt_trigram_r(ti_r).split("\n")
    except Exception:
        tri_lines = []
    if not tri_lines:
        return []
    lines = ["─" * W, "【卜象解析】"]
    lines.extend(tri_lines)
    lines.append("")
    return lines


def build_timing(step5: dict, W: int = REPORT_WIDTH) -> list:
    """应期推断。"""
    lines = ["─" * W, "【应期推断】"]
    timing = step5.get("timing", {}) if step5 else {}
    ying_dates = step5.get("yingqi_dates", {}) if step5 else {}

    if timing:
        speed = timing.get("speed", "待断")
        summary_t = timing.get("summary_text", "")
        lines.append(f"  整体节奏：{speed}")
        if summary_t:
            lines.append(f"  方法综述：{summary_t}")

    if ying_dates and ying_dates.get("dates"):
        use_branch = ying_dates.get("use_god_branch", "")
        use_elem = ying_dates.get("use_god_element", "")
        if use_branch:
            lines.append(f"  用　　神：{use_branch}（{use_elem}）")
        strength_l = ying_dates.get("strength_level", "")
        if strength_l:
            lines.append(f"  旺　　衰：{strength_l}")
        lines.append(f"  应期日期：")
        for d in ying_dates.get("dates", []):
            dt_s = d.get("date", "?")
            rule = d.get("rule", "")
            branch = d.get("branch", "")
            desc = d.get("description", "")
            br_info = f" [{branch}]" if branch else ""
            lines.append(f"    {dt_s}{br_info} — {rule}（{desc}）")
        yq_summary = ying_dates.get("summary_text", "")
        if yq_summary:
            lines.append(f"  小　　结：{yq_summary}")
    elif step5 and step5.get("verdict"):
        # fallback: use step5 verdict to estimate timing
        verdict_now = step5.get("verdict", "")
        if verdict_now in ("大吉", "吉"):
            lines.append("  应期推断：事顺势而为，逢值逢合应速。")
        elif verdict_now in ("凶", "平凶"):
            lines.append("  应期推断：守静安时，待用神旺相之月可转。")
        else:
            lines.append("  应期推断：吉凶参半，逢值逢冲应之。")
    else:
        lines.append("  应期推断：待定")
    lines.append("")
    return lines


def build_verdict(step5: dict, W: int = REPORT_WIDTH) -> list:
    """最终判语（含页眉页脚）。"""
    lines = ["=" * W, "【最 终 判 语】".center(W), "=" * W, ""]

    if step5:
        verdict = step5.get("verdict", "待定")
        final_score = step5.get("final_score", 0)
        verdict_desc = step5.get("verdict_description", "")
        confidence = step5.get("confidence", "?")

        # 判语大字
        lines.append(f"　　　　　　◖ {verdict} ◗")
        lines.append("")
        if verdict_desc:
            lines.append(f"　　{verdict_desc}")
        lines.append("")
        lines.append(f"　　综合评分：{final_score:.2f} / 5.00")
        lines.append(f"　　置信　度：{confidence}%（{step5.get('confidence_description', '')}）")

        # pattern override notes
        pvn = step5.get("pattern_verdict_note", "")
        if pvn:
            lines.append("")
            lines.append(f"　　※ {pvn}")
        otn = step5.get("officer_tomb_verdict_note", "")
        if otn:
            lines.append("")
            lines.append(f"　　※ {otn}")

        # 经典引文
        cqs = step5.get("classical_quotes", [])
        if isinstance(cqs, list) and cqs:
            lines.append("")
            lines.append("　　【经典引文】")
            for cq in cqs:
                if isinstance(cq, dict):
                    src = cq.get("source", "")
                    quote = cq.get("quote", "")
                    lines.append(f"　　· {src}：「{quote}」")

        # 卦身摘要
        body_note = step5.get("hexagram_body_note", "")
        if body_note:
            lines.append("")
            lines.append(f"　　【卦身】{body_note}")

    lines.append("")
    lines.append("=" * W)
    lines.append("报告中　·　仅供参考".center(W))
    lines.append("=" * W)
    return lines
