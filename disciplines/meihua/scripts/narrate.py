# -*- coding: utf-8 -*-
"""梅花易数·正文叙述（narrate 段）—— 唯一交付正文，师傅口吻。

职责（CONTRACT §一）：把 analyze 输出的因子与判据翻译成人话。
边界：不自行推断任何新的象数结论；正文每个象数判断都能在
analyze 输出里找到出处；术语出现时顺口带一句，不堆字段。

写法：
  先接住问题 → 亮结论方向 → 讲为什么（体用、互变、旺衰）
  → 生体/克体卦的具体含义 → 应期与节奏 → 口径收尾。
"""
from __future__ import annotations
import json
from pathlib import Path as _P

from pathlib import Path

_VD = json.loads((_P(__file__).resolve().parents[1] / 'data' / 'verdicts.json').read_text(encoding='utf-8'))
_NP = _VD.get('narrate_phrases', {})
_BQ = _VD.get('basis_quotes', {})

_MOVING_CN = {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}

_DIRECTION_OPENING = {
    "吉": _NP["open_daji"],
    "平吉": _NP["open_ji"],
    "平": _NP["open_ping"],
    "平凶": _NP["open_xiao_xiong"],
    "凶": _NP["open_xiong"],
}

_DIRECTION_SKIP = {"平": "两可", "平吉": "小吉", "平凶": "偏阻", "吉": "吉", "凶": "凶"}




def _direction_label(direction: str) -> str:
    return _DIRECTION_SKIP.get(direction, direction or "两可")


def _relation_plain(relation: str) -> str:
    return {
        "体克用": _NP["rel_ti_ke_yong"],
        "用克体": _NP["rel_yong_ke_ti"],
        "体生用": _NP["rel_ti_sheng_yong"],
        "用生体": _NP["rel_yong_sheng_ti"],
        "比和": "体用比和——双方同气，不相妨碍，顺遂之象",
    }.get(relation, relation)


def _classics_lines(cl: dict) -> list[str]:
    """所本原文小节：逐字照录（含篇名与源文件行号），只作所本凭证。"""
    rules = cl.get("规则") or []
    per_gua = cl.get("逐卦") or []
    if not rules and not per_gua:
        return []
    out = [f"## {_NP.get('classics_title', '')}", "", _NP.get("classics_lead", ""), ""]
    for it in rules:
        out.append(f"- {it.get('出处', '')}")
        out += [f"  > {t}" for t in (it.get("原文") or [])]
    if per_gua:
        out += ["", f"**{_NP.get('classics_per_gua_label', '')}**", ""]
        for it in per_gua:
            out.append(f"- {it.get('出处', '')}")
            out.append(f"  > {it.get('原文', '')}")
    out.append("")
    return out


def narrate(a: dict) -> str:
    """analyze 输出 → 完整正文（markdown）。"""
    q = (a.get("question") or "").strip()
    topic = a.get("topic") or "人事"
    s = a.get("chart_summary") or {}
    bu = a.get("body_use") or {}
    iv = a.get("interaction") or {}
    t = a.get("timing") or {}
    con = a.get("conclusion") or {}
    special = con.get("特断")

    # 标题
    hex_name = s.get("卦名")
    moving = s.get("动爻")
    movings = s.get("动爻列表") or ([moving] if moving else [])
    multi = bool(s.get("多爻动")) or (movings and len(movings) > 1)
    title = f"梅花易数·{topic}占"
    if hex_name:
        if multi and movings:
            mv_txt = "、".join(_MOVING_CN.get(m, m) for m in movings)
            title += f"（{hex_name}卦 {mv_txt}动）"
        elif moving:
            title += f"（{hex_name}卦 {_MOVING_CN.get(moving, moving)}动）"
        else:
            title += f"（{hex_name}卦）"

    lines = [f"# {title}", ""]

    # 一、接住问题 + 亮结论
    opening = _DIRECTION_OPENING.get(con.get("方向"), "")
    if q:
        lines.append(f"你问「{q}」。先说结论：**{opening}**，整体是「{_direction_label(con.get('方向'))}」。")
    else:
        lines.append(f"就此事来说：**{opening}**，整体是「{_direction_label(con.get('方向'))}」。")
    lines.append("")

    # 二、盘面一句话
    if hex_name:
        rel = bu.get("关系", "")
        body, use = bu.get("体卦"), bu.get("用卦")
        summary = f"这一卦得**{hex_name}**"
        if multi and movings:
            mv_txt = "、".join(_MOVING_CN.get(m, m) for m in movings)
            summary += f"，{mv_txt}齐动"
            rule = s.get("体用规则") or (a.get("multi_move") or {}).get("体用规则")
            if rule:
                summary += f"（{rule}）"
        elif moving:
            summary += f"，{_MOVING_CN.get(moving, moving)}动"
        if body and use and rel:
            summary += _NP.get("rel_two_sides", "").format(body=body, use=use, rel=rel)
        change = s.get("变卦")
        if change:
            summary += f"，变卦为{change}"
        lines.append(summary + "。")
        lines.append("")

    # 二·五、万物类象（《卷一·八卦万物属类》挂到体用互变，供说人话）
    # 体互／用互分派（OPT-meihua_yishu_dz-05，源L820「体互最紧，用互次之」）——
    # 只报「哪个互是体互、哪个是用互」这一结构事实与书源权重档，**不据权重下吉凶断语**。
    tyh = a.get("ti_yong_hu") or {}
    if tyh.get("体互") or tyh.get("用互"):
        lines.append(_NP.get("ti_yong_hu_lead", ""))
        lines.append("- " + _NP.get("ti_yong_hu_body", "").format(
            hu=f"**{tyh.get('体互')}**", pos=tyh.get("体互位"),
            rank=tyh.get("权重档", {}).get("体互")))
        lines.append("- " + _NP.get("ti_yong_hu_use_body", "").format(
            hu=f"**{tyh.get('用互')}**", pos=tyh.get("用互位"),
            rank=tyh.get("权重档", {}).get("用互")))
        lines.append("  > " + _NP.get("ti_yong_hu_src", "").format(
            order=tyh.get("体用位序"), src=tyh.get("出处")))
        lines.append("")

    # 外应（三要十应）槽位（OPT-meihua_yishu_dz-04）：无外应时**显式声明静占**（源L735）。
    ext = a.get("external_signs") or {}
    if ext:
        if not ext.get("有无外应"):
            lines.append(f"**外应**：{ext.get('口径') or '空缺'}")
            lines.append("")
        else:
            lines.append(_NP.get("external_sign_lead", "").format(
                order=ext.get("合参次序") or ""))
            for row in ext.get("外应") or []:
                if row.get("卦"):
                    lines.append("- " + _NP.get("external_sign_hit", "").format(
                        sign=row["物"], trig=row["卦"], elem=row.get("五行"),
                        relation=row.get("合参")))
                else:
                    lines.append("- " + _NP.get("external_sign_miss", "").format(
                        sign=row.get("物"), note=row.get("备注")))
            lines.append("  > " + _NP.get("external_sign_note", "").format(
                score=ext.get("计分") or ""))
            lines.append("")

    analogies = a.get("analogies") or {}
    if analogies:
        picks = []
        for role in ("体卦", "用卦"):
            item = analogies.get(role) or {}
            lex = item.get("类象") or {}
            if not lex:
                continue
            people = "、".join((lex.get("人物") or [])[:3])
            body_bits = "、".join((lex.get("身体") or [])[:3])
            things = "、".join((lex.get("物类") or [])[:3])
            bits = [x for x in (people, body_bits, things) if x]
            if bits:
                picks.append(f"{role}**{item.get('卦')}**取象：" + " / ".join(bits))
        if picks:
            lines.append(_NP["analogy_lead"])
            for p in picks:
                lines.append(f"- {p}")
            lines.append("")
        # 书源类象正表原文（《卷一·八卦萬物屬類》按事类取象；逐字，供回指）
        wt = a.get("analogy_table") or {}
        wx = [f"{role}**{item.get('卦')}**" + "；".join((item.get("类象") or {}).values())
              for role, item in ((r, wt.get(r) or {}) for r in ("体卦", "用卦"))
              if item.get("类象")]
        if wx:
            lines.append(_NP["wanwu_table_lead"])
            for line in wx:
                lines.append(f"- {line}")
            lines.append("")

    # 三、为什么：体用总诀 + 事类断语
    g = (bu.get("关系判语") or "").strip()
    if g:
        lines.append(f"按《体用总诀》，{_relation_plain(bu.get('关系'))}——古诀说「{g}」。")
    tv = a.get("topic_verdict") or {}
    tv_text = (tv.get("text") or "").strip()
    if tv_text and tv_text != g:
        role = (tv.get("note") or "").strip()
        prefix = f"就{topic}这一问而言" + (f"（{role}）" if role else "") + "，"
        lines.append(prefix + "古诀断「" + tv_text + "」。")
    if topic == "天时":
        rules = ((_VD.get("topics") or {}).get("天时") or {}).get("hexagram_rules") or []
        if rules:
            lines.append("天时观卦五行歌（《卷一》通行口径引文）：")
            for r in rules:
                lines.append(f"> {r}")
    lines.append("")

    # 四、互变生克
    helpers = iv.get("生体之卦") or []
    hinderers = iv.get("克体之卦") or []
    st = a.get("sheng_ti") or []
    kt = a.get("ke_ti") or []
    if multi:
        lines.append("这回是多爻同动，体用照「动者为用」分侧之外，更看互变合参——"
                     f"{_BQ.get('duo_gong', '')}。")
    if helpers or hinderers:
        lines.append(_NP.get("hu_bian_lead", ""))
        if helpers:
            names = "、".join(h.get("卦") for h in helpers)
            lines.append(f"- 有**{names}**生体，是来帮你的。《体用总诀》说生体之卦各有所应："
                         + "；".join((x.get("含义") or "").strip() for x in st if x.get("含义")))
        if hinderers:
            names = "、".join(h.get("卦") for h in hinderers)
            lines.append(_NP.get("hinder_lead", "").format(names=names)
                         + "；".join((x.get("含义") or "").strip() for x in kt if x.get("含义")))
        if not helpers and not hinderers:
            lines.append("- 用互变都与体卦无生克，事势平铺，全看月令推助。")
        if helpers and len(helpers) > len(hinderers):
            lines.append("生体之卦多于克体，中间与终局都在帮体卦，体用上的不利被这一层接住了不少。")
        lines.append("")

    # 五、卦象特断（不拘体用）
    if special:
        lines.append(f"这卦有不能只按体用看的处（《卦断遗论》：占卜决断有不拘体用者）：{con.get('说明')}。")
        lines.append("")

    # 六、旺衰与应期
    qi = a.get("body_qi")
    if qi:
        state = qi.get("状态")
        speed = t.get("应期速度")
        if state:
            speed_txt = _NP.get("speed_text", {}).get(speed, "")
            lines.append(f"体卦{bu.get('体卦')}（{bu.get('体卦五行')}）在当下月令是**{state}**"
                         + (f"，{speed_txt}" if speed_txt else "") + "。")
    timing = t.get("卦气应期") or []
    if timing:
        gz = "、".join(timing)
        lines.append(_NP.get("timing_lead", "").format(gz=gz))
        for item in (t.get("生体卦应期") or []):
            if item.get("干支"):
                lines.append(f"- {item.get('卦')}生体：应于{('、'.join(item['干支']))}之日")
        for item in (t.get("克体卦应期") or []):
            if item.get("干支"):
                lines.append(f"- {item.get('卦')}克体：其阻应于{('、'.join(item['干支']))}之日")
    if timing or qi:
        lines.append("")

    # 六·五、所本原文（逐字，供逐一核对；只作凭证不参与评分）
    lines += _classics_lines(a.get("classics") or {})

    # 七、口径收尾
    conclusion = con.get("说明") or ""
    if conclusion and not special:
        lines.append(f"综合下来：**{conclusion}**。")
        lines.append("")
    if con.get("方向") in ("凶", "平凶"):
        lines.append("需要说明的是：这是卦象结构上**偏向**的走向，不是注定；紧要处仍以专业意见为准。")
    else:
        lines.append("以上是卦象给出的趋向，供参考；涉及医疗、法律、投资等大事，仍以专业意见为准。")
    lines.append("")

    if con.get("所本"):
        lines.append(f"> 所本：{con.get('所本')}")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    import json as _json
    import sys as _sys

    CORE = Path(__file__).resolve().parents[3] / "core"
    for _p in (str(Path(__file__).resolve().parent), str(CORE)):
        if _p not in _sys.path:
            _sys.path.insert(0, _p)
    from yishu_core.runtime import force_utf8_stdio  # noqa: E402
    force_utf8_stdio()

    ap = argparse.ArgumentParser(description="梅花易数解读（narrate 段）")
    ap.add_argument("analyze_json", nargs="?",
                    help="analyze 输出 JSON 文件（缺省跑观梅占演示）")
    ap.add_argument("-o", "--out", type=Path, help="写出解读文本")
    args = ap.parse_args()

    if args.analyze_json:
        a = _json.loads(Path(args.analyze_json).read_text(encoding="utf-8"))
    else:
        from chart import chart
        from analyze import analyze
        params = {"way": "numbers", "year_num": 5, "month": 12, "day": 17,
                  "hour_num": 9, "question": "明晚会有女子来折花吗？"}
        a = analyze(chart(params))
    text = narrate(a)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        print("解读 →", args.out)
    else:
        print(text)
