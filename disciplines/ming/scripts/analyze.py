# -*- coding: utf-8 -*-
"""命·因子推演（analyze 段）—— 机械格局/强弱/大运，不写命运断语。

输出契约与合参层对齐：
  {question, pillars, factors, shensha, ming_shen_gong,
   conclusion: {方向: "", verdicts: [机械标签], 说明, 所本,
                strength, pattern, useful_gods, dayun},
   chart_summary}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(CORE), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.relations import LIUQIN_TO_SHISHEN  # noqa: E402  单源：官鬼=夫星、子孙=子星
from pattern import (  # noqa: E402
    strength_and_pattern,
    dayun_table,
    liunian_table,
    dayun_liunian_interactions,
    san_hui_present,
    pillar_relations,
    tai_yuan,
    liuyue_table,
    xiao_yun_table,
    tian_ke_di_chong,
    ten_god_combos,
    tong_guan,
    bing_yao,
)


def female_fu_zi(chart_json: dict) -> dict | None:
    """女命夫子星（机械标注，不批吉凶）。

    《渊海子平·女命论》：女命以官杀为夫星（正官正夫、七杀偏夫），以食伤为子星
    （食神为女、伤官为男）。机械扫描四柱天干 `ten_god` 与地支藏干 `ten_gods`，
    标出夫星/子星所在柱与位置；不评旺衰吉凶（AGENTS.md 铁律三）。男命不调用。
    夫星/子星取法绑定 core.relations.LIUQIN_TO_SHISHEN 单源，不另写字面量。

    ⚠️ 跨书源异说（2026-10-04j 登记）：《滴天髓阐微·女命章》任注持弹性体系——
    「凡女命之夫星，即是用神，女命之子星，即是喜神，不可专论官星为夫、伤食为子」
    （data/sources/di-tian-sui-chan-wei.wikitext.txt 行6254；命例有夫星＝伤官者，行6824）。
    两书两体系，照病药案保留差异、不强行统一；本函数的固定官杀/食伤映射
    是渊海子平系（库外书源）的机械标注实现。
    """
    birth = chart_json.get("birth") or {}
    if birth.get("gender") != "女":
        return None
    pillars = chart_json.get("pillars") or {}
    factors = chart_json.get("factors") or {}
    # 夫星=官鬼(正官/七杀)；子星=子孙(食神/伤官)
    fu_stars = set(LIUQIN_TO_SHISHEN.get("官鬼") or ())
    zi_stars = set(LIUQIN_TO_SHISHEN.get("子孙") or ())
    fu_hits, zi_hits = [], []
    for name, p in pillars.items():
        tg = (p or {}).get("ten_god") or ""
        if tg in fu_stars:
            fu_hits.append({"柱": name, "位": "天干", "十神": tg})
        if tg in zi_stars:
            zi_hits.append({"柱": name, "位": "天干", "十神": tg})
    for name, f in factors.items():
        for cg in (f or {}).get("ten_gods") or []:
            tg = (cg or {}).get("ten_god") or ""
            layer = (cg or {}).get("layer") or ""
            if tg in fu_stars:
                fu_hits.append({"柱": name, "位": f"藏干({layer})", "十神": tg})
            if tg in zi_stars:
                zi_hits.append({"柱": name, "位": f"藏干({layer})", "十神": tg})
    return {
        "gender": "女",
        "夫星": fu_hits,
        "子星": zi_hits,
        "basis": "《渊海子平·女命论》：官杀为夫星（正官正夫、七杀偏夫），"
                 "食伤为子星（食神女、伤官男）；仅机械标注所在，不评旺衰吉凶",
    }


def analyze(chart_json: dict) -> dict:
    """chart JSON → analyze JSON。产出机械标签，不产出命运吉凶。"""
    result = dict(chart_json)
    pillars = result.get("pillars") or {}
    sp = strength_and_pattern(result)
    dayun = dayun_table(result)
    liunian = liunian_table(result, n=12)
    interactions = dayun_liunian_interactions(result, dayun=dayun, liunian=liunian)
    # 调候用神（《穷通宝鉴》查表结果透出到 analyze 顶层；无明文的格为 None）
    result["tiaohou"] = sp.get("tiaohou")

    # 四柱结构补充因子（三会方局 / 胎元 / 流月 / 小运 / 天克地冲 / 十神组合）——
    # 均为机械结构标签，只出结构名与依据，不批吉凶（AGENTS.md 铁律三）。
    month_gz = (pillars.get("month") or {}).get("ganzhi") or ""
    year_stem = (pillars.get("year") or {}).get("stem") or ""
    day_stem = (pillars.get("day") or {}).get("stem") or ""
    san_hui = san_hui_present(pillars)
    pillar_rel = pillar_relations(result)
    tai = tai_yuan(month_gz)
    liuyue = liuyue_table(year_stem, day_stem, 12)
    xiaoyun = xiao_yun_table(result, 12)
    tkdc = tian_ke_di_chong(result, dayun=dayun, liunian=liunian)
    combos = ten_god_combos(result, strength=sp.get("strength") or "")
    tg = tong_guan(result)
    # 病药（《神峰通考·病药说类》）：病＝原所害之神，药＝得一字以去之
    by = bing_yao(result, strength=sp.get("strength") or "")
    # 女命夫子星（机械标注；男命返回 None）
    ffz = female_fu_zi(result)

    summary = {
        "四柱": {k: (v or {}).get("ganzhi") for k, v in pillars.items()},
        "日主": (pillars.get("day") or {}).get("stem"),
        "命宫": (result.get("ming_shen_gong") or {}).get("ming_gong"),
        "身宫": (result.get("ming_shen_gong") or {}).get("shen_gong"),
        "强弱": sp.get("strength"),
        "格局": sp.get("pattern"),
        "喜用": "、".join(sp.get("useful_gods") or []),
        "空亡": result.get("xunkong") or [],
        "胎元": (tai or {}).get("ganzhi"),
    }

    verdicts = [
        {
            "code": "strength",
            "label": sp.get("strength"),
            "basis": f"生扶{sp.get('sheng_fu')} − 克泄耗{sp.get('ke_xie_hao')} = {sp.get('strength_score')}"
                     f"（得令加权 {sp.get('decree_bonus')}）",
        },
        {
            "code": "pattern",
            "label": sp.get("pattern"),
            "basis": sp.get("pattern_basis") or "",
        },
    ]
    if sp.get("tentative_special"):
        verdicts.append({
            "code": "special_pattern",
            "label": sp.get("tentative_special"),
            "basis": sp.get("from_basis") or "仅条件识别，未作定论；需人工复核",
        })
    if dayun:
        verdicts.append({
            "code": "dayun",
            "label": f"大运 8 步（{dayun[0]['ganzhi']}→{dayun[-1]['ganzhi']}）",
            "basis": "顺逆按年干阴阳×性别；起运岁≈距节气日数/3（三日=一年，一日=四月）",
        })
    if result.get("xunkong"):
        verdicts.append({
            "code": "xunkong",
            "label": "空亡 " + "、".join(result["xunkong"]),
            "basis": "日柱所在旬之空亡（core.symbols.xunkong_of）",
        })
    if san_hui:
        verdicts.append({
            "code": "san_hui",
            "label": "三会 " + "、".join(f"{x['element']}局" for x in san_hui),
            "basis": san_hui[0]["basis"],
        })
    if pillar_rel:
        verdicts.append({
            "code": "pillar_relations",
            "label": "四柱干支关系 " + "、".join(r["text"] for r in pillar_rel),
            "basis": pillar_rel[0]["basis"],
        })
    if tai:
        verdicts.append({"code": "tai_yuan", "label": f"胎元 {tai['ganzhi']}",
                         "basis": tai["basis"]})
    if combos:
        verdicts.append({
            "code": "ten_god_combo",
            "label": "十神组合 " + "、".join(c["name"] for c in combos),
            "basis": "；".join(c["basis"] for c in combos),
        })
    if tkdc:
        verdicts.append({
            "code": "tian_ke_di_chong",
            "label": f"天克地冲 {len(tkdc)} 处",
            "basis": "运/年柱与日柱天干相克且地支相冲（《渊海子平》）；只标记不批吉凶",
        })
    if tg:
        verdicts.append({
            "code": "tong_guan",
            "label": "通关/关隔 " + "、".join(t["name"] for t in tg),
            "basis": tg[0]["basis"],
        })
    if ffz:
        verdicts.append({
            "code": "female_fu_zi",
            "label": f"女命夫星 {len(ffz['夫星'])} 处 / 子星 {len(ffz['子星'])} 处",
            "basis": ffz["basis"],
        })
    if by:
        _b = by["bing"]
        verdicts.append({
            "code": "bing_yao",
            "label": f"病药 {_b['病']}（药 {_b['药']}"
                     f"{'·在局中' if _b['药在局中'] else '·局中未见'}）",
            "basis": _b["basis"],
        })
        if by["medicines"]:
            verdicts.append({
                "code": "bing_yao_medicine",
                "label": "得药 " + "、".join(
                    (m.get("药神") and "、".join(m["药神"])) or m.get("药", "")
                    for m in by["medicines"]),
                "basis": by["basis"],
            })

    result["female_fu_zi"] = ffz

    return {
        **result,
        "chart_summary": summary,
        "strength": sp,
        "dayun": dayun,
        "san_hui": san_hui,
        "pillar_relations": pillar_rel,
        "tai_yuan": tai,
        "liu_yue": liuyue,
        "xiao_yun": xiaoyun,
        "tian_ke_di_chong": tkdc,
        "ten_god_combos": combos,
        "tong_guan": tg,
        "bing_yao": by,
        "conclusion": {
            "方向": "",
            "verdicts": verdicts,
            "说明": (
                f"机械推演：{sp.get('strength')}·{sp.get('pattern')}；"
                f"喜用={'、'.join(sp.get('useful_gods') or [])}。"
                "不含命运吉凶断言；大运干支为近似起运。"
            ),
            "所本": "扶抑用神通行口径 + 月令本气十神定格 + core.ming_tables",
            "应期": [],
            "timing": [],
            "strength": sp.get("strength"),
            "strength_score": sp.get("strength_score"),
            "pattern": sp.get("pattern"),
            "pattern_cheng_bai": sp.get("pattern_cheng_bai") or "",
            "pattern_cheng_bai_basis": sp.get("pattern_cheng_bai_basis") or "",
            "useful_gods": sp.get("useful_gods") or [],
            "taboo_gods": sp.get("taboo_gods") or [],
            "dayun": dayun,
            "liunian": liunian,
            "dayun_liunian": interactions[:12],
            "san_hui": san_hui,
            "pillar_relations": [r["text"] for r in pillar_rel],
            "tai_yuan": (tai or {}).get("ganzhi"),
            "ten_god_combos": [c["name"] for c in combos],
            "tian_ke_di_chong": [t["text"] for t in tkdc],
            "tong_guan": [t["label"] for t in tg],
            "bing_yao": (_b["病"] if (_b := (by or {}).get("bing")) else ""),
            "bing_yao_has_medicine": bool((by or {}).get("has_medicine")),
            "female_fu_zi": ffz,
        },
    }


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="命·因子推演（analyze 段）")
    ap.add_argument("chart_json", nargs="?", help="chart 段输出")
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args()

    if args.chart_json:
        data = json.loads(Path(args.chart_json).read_text(encoding="utf-8"))
    else:
        from chart import chart as _chart

        data = _chart(datetime_str="1990-05-20 10:30", gender="男")

    out = analyze(data)
    text = json.dumps(out, ensure_ascii=False, indent=2, default=str)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
