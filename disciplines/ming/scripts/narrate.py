# -*- coding: utf-8 -*-
"""命·正文（narrate 段）—— 叙述机械因子；禁止命运断言。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.symbols import EARTHLY_BRANCHES  # noqa: E402

_DATA = Path(__file__).resolve().parent.parent / "data"
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
# 正月建寅：月序表由内核地支序旋转得到，不另抄一份（AGENTS.md §二 唯一真值源）。
_BRANCH_FROM_YIN = EARTHLY_BRANCHES[2:] + EARTHLY_BRANCHES[:2]
_MONTH_ORDINAL = dict(zip(_BRANCH_FROM_YIN, range(1, 13)))


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
    是方法论登记，**不是判据、不进任何评分**（AGENTS.md 铁律一）。

    排版约束：① 引文一律用「」包成独立分句，且出处括注以 `（《…` 开头、行号置括注内
    ——`tools/verdict_audit.py` 的 NON_VERDICT ① 以 `（\s*[《＜]` 豁免出处标注行
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
        f"命宫：{s.get('命宫') or '—'}；身宫：{s.get('身宫') or '—'}。",
        "",
    ]
    ds = _day_stem_block(a)
    if ds:
        lines += ds + [""]
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
    lines += _cong_hua_block(con.get("pattern") or s.get("格局") or "")
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
            lines.append(f"> 调候原文（《穷通宝鉴》·{tq.get('section') or ''}）：{tq['quote']}")
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
    # 十神取象旁证（《千里命稿·六神篇》）：**只作象数旁证，不进结构、不评分**。
    # 数据源 data/liushen_image.json 按 OPT-qianli_minggao_dz-03 约定**仅 narrate 可读**；
    # 措辞守铁律三：用「结构上/有…信号」，且逐字引文自带定位，便于回指原文。
    img = _LIUSHEN_IMAGE.get("十神取象") or {}
    if img:
        lines.append("**十神取象**（《千里命稿·六神篇》引文，结构上旁证、非吉凶断语）：")
        # 本书按篇合立（偏正印/偏正财/比劫禄刃），作用表按单星登记 → 合篇取首个单星。
        _HE_PIN = {"偏正印": "正印", "偏正财": "正财", "比劫禄刃": "比劫"}
        for god, e in img.items():
            q = e.get("取象") or e.get("能力") or ""
            if not q:
                continue
            loc = (e.get("取象_src") or e.get("能力_src") or "").split(":")[-1]
            lines.append(f"> **{god}**（《千里命稿》{loc} 行）：「{q}」")
            act = _SHI_SHEN_ACTIONS.get(_HE_PIN.get(god, god))
            if act and act.get("narrative_hint"):
                # 整行前缀与正文都取自本表（hint_prefix / narrative_hint），代码不组句
                lines.append(f"> {act['hint_prefix']}：{act['narrative_hint']}")
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
        lines.append(f"> 病药总纲：「{by.get('thesis')}」（{by.get('basis')}）。")
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
    lines += [
        "以上为机械排盘与扶抑口径推演，**不是命运断言**。",
        "格局从格仅作 tentative 标注；重大决策以专业意见为准。",
        "本模块不宣称现实预测命中率（`AGENTS.md` 铁律三）。",
    ]
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
