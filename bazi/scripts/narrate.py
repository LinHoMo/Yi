# -*- coding: utf-8 -*-
"""命·正文（narrate 段）—— 叙述机械因子；禁止命运断言。"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[1] / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.symbols import EARTHLY_BRANCHES  # noqa: E402

_DATA = Path(__file__).resolve().parent.parent / "data"
# 第五百三十九批：交付边界声明外置到 data/*.json（AGENTS.md §一.1 / §三），
# 与六爻 narrative_templates.json#narrate_shell 同一形状。**逐字照搬，不改措辞**——
# 本批是「字面量归位」不是「文案改写」，故 narrate 输出与 golden 措辞指纹不变。
_NARRATIVE_TEMPLATES = json.loads(
    (_DATA / "narrative_templates.json").read_text(encoding="utf-8"))
_BOUNDARY_LINES = _NARRATIVE_TEMPLATES["narrate_shell"]["boundary_lines"]
_VERDICTS = json.loads((_DATA / "verdicts.json").read_text(encoding="utf-8"))
_TIAO_HOU_QUOTES = json.loads((_DATA / "tiaohou_quotes.json").read_text(encoding="utf-8"))
_DTS = json.loads((_DATA / "ditian_sui.json").read_text(encoding="utf-8"))
# 十神取象旁证素材（OPT-qianli_minggao_dz-03）：**仅本 narrate 层可读**，
# analyze/chart/pattern 不得 import（铁律一：象数解读不归机械推演）。
_LIUSHEN_IMAGE = json.loads((_DATA / "liushen_image.json").read_text(encoding="utf-8"))
# 十神作用枚举旁证素材（OPT-qianli_minggao_dz-02）：与 liushen_image 同一口径——
# **仅本 narrate 层可读**，不进 analyze/chart/pattern，不参与任何评分（铁律一/三）。
_SHI_SHEN_ACTIONS_DOC = json.loads(
    (_DATA / "shi_shen_actions.json").read_text(encoding="utf-8"))
_SHI_SHEN_ACTIONS = _SHI_SHEN_ACTIONS_DOC["shi_shen_actions"]
# 正月建寅：月序表由内核地支序旋转得到，不另抄一份（SKILL.md 唯一真值源）。
_BRANCH_FROM_YIN = EARTHLY_BRANCHES[2:] + EARTHLY_BRANCHES[:2]
_MONTH_ORDINAL = dict(zip(_BRANCH_FROM_YIN, range(1, 13)))
# 纳音取象旁证素材（《五行精纪》纳音性质名）：**仅本 narrate 层可读**，
# analyze/chart/pattern 不得 import（铁律一：象数解读不归机械推演）。
# ⚡ 接线状态：已落地（2026-10-09f）。展示为"物性标签旁证"，**不计格、不评分**，
# 与子平格局层并列输出（engine 为体、纳音性质名为物性标签扩展，并行不混用）。
_NAYIN_QUXIANG = json.loads((_DATA / "nayin_quxiang.json").read_text(encoding="utf-8"))
_NAYIN_QUXIANG_MAP = _NAYIN_QUXIANG.get("纳音性质", {})


def _dts_chapter(name: str) -> dict:
    return (_DTS.get("chapters") or {}).get(name) or {}


def _dts_verse(name: str) -> str:
    """《滴天髓》某章原文（逐字，不改写）。"""
    ch = _dts_chapter(name)
    return "".join(ch.get("verse") or [])


def _dts_block(name: str, label: str) -> list[str]:
    """《滴天髓》某章原文 + 注文（逐字），返回引用块行。"""
    ch = _dts_chapter(name)
    if not ch.get("verse"):
        return []
    out = [f"> **{label}**（《滴天髓》·{name}）：{''.join(ch['verse'])}"]
    for note in ch.get("notes") or []:
        out.append(f"> 　{note}")
    return out


def _dts_line(name: str, label: str) -> list[str]:
    """《滴天髓》某章原文（逐字，只取原文；注文过长时不入报告）。"""
    ch = _dts_chapter(name)
    if not ch.get("verse"):
        return []
    return [f"> **{label}**（《滴天髓》·{name}）：{''.join(ch['verse'])}"]


def _day_stem_block(a: dict) -> list[str]:
    """日主本气体性：《滴天髓》天干論逐字（十日干各一条原文 + 注）。"""
    s = a.get("chart_summary") or {}
    day = str((s.get("四柱") or {}).get("day") or "")
    stem = day[0] if day else ""
    e = (_DTS.get("day_stem") or {}).get(stem)
    if not e:
        return []
    out = [f"**日主体性**（《滴天髓》天干論·{stem}）：{''.join(e.get('verse') or [])}"]
    for note in e.get("notes") or []:
        out.append(f"> 　{note}")
    return out


def _cong_hua_block(pattern: str) -> list[str]:
    """从格／化格：《滴天髓》從化論真、假两段逐字原文。"""
    if not pattern.startswith(("从", "化")):
        return []
    zhen = _dts_verse("從化論－真")
    jia = _dts_verse("從化論－假")
    if not (zhen or jia):
        return []
    return [f"**从化所本**（《滴天髓》從化論）：真——「{zhen}」；假——「{jia}」。"]


def _zhuan_wang_block(from_kind: str) -> list[str]:
    """五行专旺五格（《千里命稿》外格）书证：曲直／炎上／稼穑／从革／润下。

    专旺判据在 `strength.from_kind`（396 批单列门），与 `conclusion.pattern`（如月刃格）
    是两条轴——叙述默认只印 pattern，专旺性质成了「算出来了但看不到」（EVAL-PLAN §六）。
    本块按 from_kind 补印《千里命稿》外格书证，只出书源句、不批吉凶（铁律三）。
    """
    _ZW = {"曲直": "mu", "炎上": "huo", "稼穑": "tu", "从革": "jin", "润下": "shui"}
    key = _ZW.get(from_kind)
    if not key:
        return []
    cg = _VERDICTS.get("从格引文") or {}
    q = cg.get(f"zhuan_wang_{key}") or ""
    if not q:
        return []
    return [f"> **{from_kind}格所本**（《千里命稿·外格·{from_kind}格之构成》）：「{q}」"]


def _geju_line(pattern: str) -> str:
    """格局名 → 《子平真诠》引文行（查 data/verdicts.json；建禄格走「不适用」口径）。"""
    if not pattern:
        return ""
    for side, info in (_VERDICTS.get("格局顺逆") or {}).items():
        if pattern in (info.get("covers") or []):
            tg = _VERDICTS.get("格局提纲") or {}
            return (f"**格局所本**（{tg.get('所本')}）：「{tg.get('text')}」；"
                    f"{pattern}属{side}——「{info.get('text')}」（{info.get('所本')}）。")
    na = (_VERDICTS.get("不适用") or {}).get(pattern)
    if na:
        return f"**格局口径**：{na}"
    cong = _VERDICTS.get("从格引文") or {}
    if cong and pattern.startswith("从"):
        head = (f"**从格所本**：「{cong.get('verse')}」（{cong.get('verse_source')}）"
                f"{cong.get('verse_note') or ''}。")
        # 《三命通会》从煞/从财书源句（OPT-sanming_tonghui_dz-03）：按格局名分流补一句，
        # 与上方《滴天髓》引文并列，不替换。只出书源句，不作吉凶断言（铁律三）。
        extra = ""
        if pattern.startswith("从官杀") or pattern.startswith("从煞"):
            extra = cong.get("cong_sha_sanming") or {}
        elif pattern.startswith("从财"):
            extra = cong.get("cong_cai_sanming") or {}
        if isinstance(extra, dict) and extra.get("verse_quote"):
            head += (f"《三命通会》另立从煞/从财一节：「{extra['verse_quote']}」"
                     f"（{extra.get('locator') or ''}）。")
        return head
    return ""


def _kanming_block() -> list[str]:
    r"""《三命通会》看命总纲方法论引文（OPT-sanming_tonghui_dz-04）。

    只说明「引擎为什么这样取」（月令为命、神煞以五行为本），
    是方法论登记，**不是判据、不进任何评分**（SKILL.md 铁律一）。

    排版约束：① 引文一律用「」包成独立分句，且出处括注以 `（《…` 开头、行号置括注内
    ——历史上 tools/verdict_audit.py 的 NON_VERDICT ① 以「（《」开头豁免出处标注行
    （与 `_dts_line`／`_geju_line` 的 `**X所本**（《书名》…）：「原文」` 同款排版），
    且若行号紧贴引文尾会被并进同一句误判成「未外置断语」。② 引文本体在
    `data/verdicts.json#看命口诀`，属已外置。
    """
    km = _VERDICTS.get("看命口诀") or {}
    out = []
    for label in ("月令为命", "神煞以五行为本"):
        e = km.get(label) or {}
        q = e.get("full_quote") or e.get("quote") or ""
        if not q:
            continue
        loc = (e.get("locator") or "").split(":")[-1]
        out.append(f"> **看命所本**（《三命通会》{loc} 行·{label}）：「{q}」")
    return out


def _tiaohou_quote(a: dict) -> dict | None:
    """调候原文引文（月建×日主 → data/tiaohou_quotes.json 查引文）。"""
    pillars = (a.get("chart_summary") or {}).get("四柱") or {}
    month_gz = str(pillars.get("month") or "")
    day_gz = str(pillars.get("day") or "")
    if len(month_gz) < 2 or not day_gz:
        return None
    n = _MONTH_ORDINAL.get(month_gz[1])
    return _TIAO_HOU_QUOTES.get(f"{n}{day_gz[0]}") if n else None


def _pillar_detail(a: dict) -> list[str]:
    """四柱十神 + 四柱藏干（定义式机械量，不批吉凶）。

    十神按日主对其他三干起（日主自身记作「日主」而非比肩，避免读者把
    「比肩」误读成「命里比肩多」）；藏干取该支所藏，本气在前。
    """
    pil = a.get("pillars") or (a.get("chart_summary") or {}).get("四柱") or {}
    fac = a.get("factors") or {}
    if not pil:
        return []
    rows = []
    for key, cn in (("year", "年"), ("month", "月"), ("day", "日"), ("hour", "时")):
        p = pil.get(key) or {}
        gz = p.get("ganzhi") or "—"
        if key == "day":
            tg = "日主"
        else:
            tg = p.get("ten_god") or (fac.get(key) or {}).get("stem_ten_god") or "—"
        hs = (fac.get(key) or {}).get("hidden_stems") or []
        rows.append(f"- {cn}柱 {gz}：干十神={tg}；支藏干={'、'.join(str(h) for h in hs) or '—'}")
    return ["**四柱十神与四柱藏干**（定义式机械量，不批吉凶）："] + rows


def _gong_text(gong) -> str:
    """命宫/身宫在内核是 {branch, ganzhi, nayin} 结构体，报告里不能直接印 dict。"""
    if not gong:
        return "—"
    if isinstance(gong, str):
        return gong
    gz = gong.get("ganzhi") or gong.get("branch") or ""
    nayin = gong.get("nayin") or ""
    if gz and nayin:
        return f"{gz}（纳音{nayin}）"
    return gz or "—"


def narrate(a: dict) -> str:
    s = a.get("chart_summary") or {}
    con = a.get("conclusion") or {}
    pillars = s.get("四柱") or {}
    gz = " ".join(str(pillars.get(k) or "—") for k in ("year", "month", "day", "hour"))
    dayun = a.get("dayun") or con.get("dayun") or []

    lines = [
        "# 命局因子说明",
        "",
        f"四柱：{gz}（年月日时）。日主：{s.get('日主') or '—'}。",
        f"命宫：{_gong_text(s.get('命宫'))}；身宫：{_gong_text(s.get('身宫'))}。",
        "",
    ]
    ds = _day_stem_block(a)
    if ds:
        lines += ds + [""]
    # 四柱十神 / 四柱藏干：这两项都是**计分维度**（ten_gods 16 分、hidden_stems 8 分），
    # 引擎一直算得出却从不进正文——EVAL-PLAN §六 禁的「算出来了但看不到」正是这种。
    pd = _pillar_detail(a)
    if pd:
        lines += pd + [""]
    # 362 批：象段（宫位／六亲／脏腑）——只呈现素材，不进评分、不作命运断言。
    # 装配失败（analyze 未产 xiang）时整段不出，不留空壳。
    try:
        from xiang import format_xiang_text
        _xt = format_xiang_text(a.get("xiang") or {})
    except Exception:  # pragma: no cover - 象段缺失不得拖垮正文
        _xt = ""
    if _xt:
        lines += [_xt, ""]
    lines += [
        f"**强弱**：{con.get('strength') or s.get('强弱') or '—'}（得分 {con.get('strength_score')}）。",
    ]
    lines += _dts_block("衰旺論", "衰旺所本")
    lines += [
        f"**格局**：{con.get('pattern') or s.get('格局') or '—'}。",
    ]
    gy = _geju_line(con.get("pattern") or s.get("格局") or "")
    if gy:
        lines.append(gy)
    # 化格（383 批）：与从格并列的另一条主线——《滴天髓·從化論》真/假两章。
    # 只出结构名与依据，不作吉凶断言（铁律三：凶象用「偏向/有…信号」，此处连方向都不给）。
    _st = a.get("strength") or {}      # 化格字段挂在 strength 段内（chart_summary 不含）
    _hk = _st.get("hua_kind") or ""
    _ht = _st.get("hua_type") or ""
    if _hk and _ht:
        _hq = _VERDICTS.get("化格引文") or {}
        _verb = _hq.get("verse") or ""
        _vv = _verb[1] if isinstance(_verb, list) and len(_verb) > 1 else ""
        lines.append(f"**化格**：{_hk}·{_ht}（{_st.get('hua_reason') or ''}）")
        if _vv:
            lines.append(f"> 化格所本（《滴天髓·從化論》）：{_vv}")
    lines += _cong_hua_block(con.get("pattern") or s.get("格局") or "")
    lines.append("")
    # 五行专旺五格（396 批单列门）：from_kind 在 strength 段、与 conclusion.pattern 不同轴，
    # 叙述默认只印 pattern（如月刃格），专旺性质「算出来了但看不到」（EVAL-PLAN §六）。
    # 按 strength.from_kind 补印《千里命稿》外格书证（旁证、非吉凶断语，铁律三）。
    _zw = (_st or a.get("strength") or {}).get("from_kind") or ""
    if _zw in ("曲直", "炎上", "稼穑", "从革", "润下"):
        lines += _zhuan_wang_block(_zw)
        lines.append("")
    cb = con.get("pattern_cheng_bai") or ""
    if cb:
        cb_basis = con.get("pattern_cheng_bai_basis") or ""
        lines.append(
            f"**格局成败**（《子平真诠》主干判据，机械判定）：{cb}"
            + (f"　— {cb_basis}。" if cb_basis else "。")
        )
    lines += [
        f"**喜用**：{'、'.join(con.get('useful_gods') or []) or '—'}；"
        f"忌：{'、'.join(con.get('taboo_gods') or []) or '—'}。",
        "",
    ]
    lines += _dts_line("體用論", "体用所本")
    lines += _kanming_block()
    lines.append("")
    xunkong = s.get("空亡") or a.get("xunkong") or []
    th = a.get("tiaohou")
    if th and th.get("main"):
        assist = f"、佐{th['assist']}" if th.get("assist") else "（原文未单列佐神）"
        lines.append(f"**调候**（《穷通宝鉴》月令×日主查表）：主{th['main']}{assist}。")
        huan = _dts_verse("寒暖論")
        if huan:
            lines.append(f"（《滴天髓》寒暖論：「{huan}」）")
        tq = _tiaohou_quote(a)
        if tq and tq.get("quote"):
            # 语料是按句切下来的片段，741 条里有 82 条以「，」起头（切片留下的
            # 句法残留，不是原文标点）；直接拼进「）：{quote}」会印成"）：，自有丙火…"。
            _q = str(tq["quote"]).lstrip("，、。；：")
            lines.append(f"> 调候原文（《穷通宝鉴》·{tq.get('section') or ''}）：{_q}")
        lines.append("")
    shensha = a.get("shensha") or []
    if shensha:
        items = []
        for s_ in shensha:
            at = "、".join(s_.get("at") or [])
            name = s_.get("name", "")
            basis = s_.get("basis", "")
            # 仅展示短起例标注（如「日干」「年支」），不引入完整口诀引文
            # （完整口诀在 data/verdicts.json 与 core/shensha.py 中，进报告会触发断语外置取证门）
            if basis and len(basis) <= 6:
                items.append(f"{name}{'@'+at if at else ''}（{basis}起）")
            else:
                items.append(f"{name}{'@'+at if at else ''}")
        lines.append(f"**神煞**（机械安星，不批吉凶）：{'；'.join(items)}。")
        lines.append("")
    ffz = a.get("female_fu_zi")
    if ffz:
        fu = ffz.get("夫星") or []
        zi = ffz.get("子星") or []
        lines.append("**女命夫子星**（《渊海子平·女命论》，机械标注，不批吉凶）：")
        lines.append("- 夫星（官杀）：" + (
            "；".join(f"{h['柱']}{h['位']}{h['十神']}" for h in fu) or "局中不见"))
        lines.append("- 子星（食伤）：" + (
            "；".join(f"{h['柱']}{h['位']}{h['十神']}" for h in zi) or "局中不见"))
        lines.append("")
    if xunkong:
        lines.append(f"**空亡**：{'、'.join(xunkong)}（日柱旬空）。")
        lines.append("")
    if dayun:
        lines.append("**大运**（起运岁为近似）：")
        for d in dayun:
            lines.append(
                f"- {d.get('start_age')}–{d.get('end_age')} 岁　{d.get('ganzhi')}"
                f"（{d.get('ten_god') or '—'}）"
            )
        sui = _dts_verse("歲運論")
        if sui:
            lines.append(f"> 岁运所本（《滴天髓》歲運論）：{sui}")
        lines.append("")
    xs = con.get("dayun_liunian") or []
    if xs:
        lines.append("**大运×流年对照**（机械关系，不批吉凶）：")
        for x in xs[:4]:
            rel = "；".join(r.get("text", "") for r in (x.get("relations") or [])[:2])
            lines.append(f"- {x.get('year')}（{x.get('liunian')}）× 运{x.get('dayun')}：{rel or '—'}")
        lines.append("")
    liunian = con.get("liunian") or []
    if liunian:
        head = "、".join(f"{x.get('year')}{x.get('ganzhi')}({x.get('ten_god') or '—'})" for x in liunian[:6])
        lines.append(f"**流年前六年**（干支×十神对照，不批吉凶）：{head}…")
        lines.append("")
    # 四柱结构补充因子（三会/胎元/十神组合/天克地冲/流月/小运）——机械标签，不批吉凶
    ty = a.get("tai_yuan")
    sh = a.get("san_hui") or []
    combos = a.get("ten_god_combos") or []
    tkdc = a.get("tian_ke_di_chong") or []
    if ty or sh or combos or tkdc:
        lines.append("**四柱结构与组合**（机械标签，不批吉凶）：")
        if ty:
            lines.append(f"- 胎元：{ty.get('ganzhi')}（{ty.get('basis')}）。")
        if sh:
            lines.append("- 三会：" + "、".join(
                f"{x.get('element')}局（{'、'.join(x.get('branches') or [])}）" for x in sh) + "。")
        if combos:
            lines.append("- 十神组合：" + "、".join(c.get("name") for c in combos) + "。")
        if tkdc:
            lines.append("- 天克地冲：" + "；".join(t.get("text") for t in tkdc) + "。")
        lines.append("")
    # 行运引动（#31②③）：运干/运支对**本命四柱**的结构标签。独立成列——不并入本命判档、
    # 不覆写格局成败结论，只把「运到了哪一步动了命里哪一支」摆出来供回指书例。
    yin = a.get("dayun_ming_yindong") or []
    sui = a.get("liunian_ming_yindong") or []
    cheng = a.get("dayun_cheng_bai") or []
    yin_map = {h.get("dayun"): h for h in yin}
    if yin or sui or cheng:
        lines.append("**行运引动**（运与岁对本命四柱的结构标签，独立成列、不覆写本命结论，不批吉凶）：")
        if cheng:
            lines.append("**行运成格变格（分列读数：运层结构命名，不覆写本命格局成败、不批吉凶）**：")
            for c in cheng:
                gz = c.get("dayun")
                verdict = "、".join(c.get("verdict") or [])
                seg = "；".join(str(r.get("text") or "") for r in
                              (yin_map.get(gz, {}) or {}).get("relations") or [])
                line = f"- 大运{gz}（{c.get('start_age')}岁起）：裁决【{verdict}】"
                if c.get("detail"):
                    line += f"；{c['detail']}"
                elif seg:
                    line += f"；结构引动：{seg}"
                lines.append(line)
        for h in sui[:6]:      # 岁层只列前六个有引动的流年（表长以可读为限）
            seg = "；".join(str(r.get("text") or "") for r in h.get("relations") or [])
            if seg:
                lines.append(f"- 流年{h.get('liunian')}（{h.get('year')}年）：{seg}。")
        lines.append("")
    # 十神取象旁证（《千里命稿·六神篇》）：**只作象数旁证，不进结构、不评分**。
    # 数据源 data/liushen_image.json 按 OPT-qianli_minggao_dz-03 约定**仅 narrate 可读**；
    # 措辞守铁律三：用「结构上/有…信号」，且逐字引文自带定位，便于回指原文。
    img = _LIUSHEN_IMAGE.get("十神取象") or {}
    if img:
        lines.append("**十神取象**（《千里命稿·六神篇》引文，结构上旁证、非吉凶断语）：")
        # 本书按篇合立（偏正印/偏正财/比劫禄刃），作用表按单星登记 → 合篇取首个单星。
        _HE_PIN = {"偏正印": "正印", "偏正财": "正财", "比劫禄刃": "比劫"}
        for god, e in img.items():
            # 取象（定义式取象句）→ 能力（提纲：泄身/生财/…）→ 构成，逐条引文外置
            # （带行号出处），只作象数旁证、不批吉凶（铁律三）。把此前 G 桶未进报告的
            # 能力/构成叶子补进正文，闭合「算出来了但看不到」（EVAL-PLAN §六）。
            q = e.get("取象") or ""
            if q:
                loc = (e.get("取象_src") or "").split(":")[-1]
                lines.append(f"> **{god}·取象**（《千里命稿》{loc} 行）：「{q}」")
            ab = e.get("能力") or ""
            if ab and ab != q:
                loc2 = (e.get("能力_src") or "").split(":")[-1]
                lines.append(f"> **{god}·能力**（《千里命稿》{loc2} 行）：「{ab}」")
            cz = e.get("构成") or ""
            if cz:
                loc3 = (e.get("构成_src") or "").split(":")[-1]
                lines.append(f"> **{god}·构成**（《千里命稿》{loc3} 行）：「{cz}」")
            note = e.get("注") or ""
            if note:
                lines.append(f"> 　{note}")
            pin = _HE_PIN.get(god, god)
            act = _SHI_SHEN_ACTIONS.get(pin)
            if act and act.get("narrative_hint"):
                # 整行前缀与正文都取自本表（hint_prefix / narrative_hint），代码不组句
                lines.append(f"> {act['hint_prefix']}：{act['narrative_hint']}")
            note2 = (act or {}).get("note") or ""
            if note2:
                # 十神作用篇提纲（《千里命稿·六神篇》直引，带行号）：与取象/能力/构成同属
                # 「算出来了但看不到」的结构化象数旁证，补印闭合 EVAL-PLAN §六。
                # 466 批：source 有两种写法（`file:NNNN` 与 `file LNNNN 附近`），
                # 旧 `split(':')[-1]` 对后者返回整串，渲染成「（《千里命稿》data/sources/… 行）」。
                m = re.search(r"(?:L|:)(\d+)", act.get("source") or "")
                sloc = m.group(1) if m else "?"
                lines.append(f"> 　「{note2}」（《千里命稿》{sloc} 行）")
        lines.append("")

    # 纳音取象旁证（《五行精纪》纳音性质名）：**只作物性标签旁证、不进结构、不评分**。
    # 接线口径（与 liushen_image / shi_shen_actions 同一约束）：仅 narrate 层可读，
    # 不进 analyze/chart/pattern。性质名出自原书逐字引文，只作物性分类标签。
    if _NAYIN_QUXIANG_MAP:
        prs = a.get("pillars") or (a.get("chart_summary") or {}).get("四柱") or {}
        nq_items = []
        for pname in ("year", "month", "day", "hour"):
            if isinstance(prs, dict):
                gz = (prs.get(pname) or {}).get("ganzhi") if pname in prs else None
                if not gz and isinstance(prs.get(pname), str):
                    gz = prs[pname]
            else:
                gz = None
            if not gz or len(gz) < 2:
                continue
            qx = _NAYIN_QUXIANG_MAP.get(gz) or {}
            xm = qx.get("性质名")
            if not xm:
                continue
            loc = str(qx.get("性质行") or "").replace("data/sources/", "").split(".")[0]
            # 带上底本原句：只印一个「从革之金」这类裸标签，读者无从核证它是不是书上的话；
            # 引文字段是逐字抽取物（[14] 同步门逐字回校验底本），贴出来才算可回指的旁证。
            yw = str(qx.get("性质引文") or "").strip()
            nq_items.append(f"{pname}={gz}「{xm}」"
                            + (f"——原书作「{yw}」" if yw else "")
                            + f"（{loc}）")
        if nq_items:
            lines.append("**纳音取象**（《五行精纪》纳音性质名，物性标签旁证、非吉凶断语）：")
            for it in nq_items:
                lines.append(f"- {it}")
            lines.append("")

    pr = a.get("pillar_relations") or []
    if pr:
        lines.append("**四柱干支关系**（机械关系，不批吉凶）："
                     + "、".join(t.get("text") for t in pr) + "。")
        lines += _dts_line("地支論", "地支关系所本")
        lines.append("")
    tg = a.get("tong_guan") or []
    if tg:
        lines.append("**通关／关隔**（《滴天髓·通隔論》机械判据，不批吉凶）：")
        for t in tg:
            lines.append(f"- {t.get('label')}。")
        ds_tg = _dts_block("通隔論", "所本")
        lines += ds_tg
        lines.append("")
    by = a.get("bing_yao") or {}
    if by.get("bing"):
        _bb = by["bing"]
        lines.append("**病药**（《神峰通考·病药说类》机械判据，不批吉凶）：")
        lines.append(f"- 病：{_bb.get('病')}（四柱最重五行{_bb.get('病之五行')}，"
                     f"原文「从重者论」）；药：{_bb.get('药')}"
                     f"（{'在局中' if _bb.get('药在局中') else '局中未见'}）。")
        for c in by.get("consumed_by_bing") or []:
            lines.append(f"- 十神层病：{c.get('病')}（{c.get('所病')}）"
                         f"——药{'在局中：' + '、'.join(c.get('所见之药') or []) if c.get('药在局中') else '局中未见'}。")
        # 「病药总纲」四字是渲染标签，与引文同属数据层（SKILL.md；
        # 真值源 data/verdicts.json#病药引文.label，与 pattern.py 的 thesis 同分支）
        lines.append(f"> {_VERDICTS['病药引文']['label']}：「{by.get('thesis')}」"
                     f"（{by.get('basis')}）。")
        lines.append("")
    ly = a.get("liu_yue") or []
    if ly:
        head = "、".join(f"{x.get('ganzhi')}({x.get('ten_god') or '—'})" for x in ly)
        lines.append(f"**流月**（正月起五虎遁，干支×十神对照，不批吉凶）：{head}。")
        lines.append("")
    xy = a.get("xiao_yun") or []
    if xy:
        head = "、".join(f"{x.get('age')}岁{x.get('ganzhi')}" for x in xy[:6])
        lines.append(f"**小运**（自生时起，机械对照；通行起法，流派有别）：{head}…")
        lines.append("")
    lines += list(_BOUNDARY_LINES)  # data/narrative_templates.json#narrate_shell（539 批外置）
    return "\n".join(lines) + "\n"


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="命·正文（narrate 段）")
    ap.add_argument("analyze_json", nargs="?")
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args()

    if args.analyze_json:
        a = json.loads(Path(args.analyze_json).read_text(encoding="utf-8"))
    else:
        from analyze import analyze as _analyze
        from chart import chart as _chart

        a = _analyze(_chart(datetime_str="1990-05-20 10:30", gender="男"))

    text = narrate(a)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
