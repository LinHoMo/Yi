# -*- coding: utf-8 -*-
"""大六壬·规则推演（analyze 段）—— 纯机械标签，无吉凶断语。

第一版判据（NEW-DISCIPLINES §2.1，本轮落地 ①②③）：
  ① 九宗门取三传（chart 段已完成，此处带出课体与门类）；
  ② 三传与日干支关系：鬼/德/合/墓/破/害/刑/冲（卷一「神煞」篇与 core 关系表）；
  ③ 十二天将乘临（chart 段布好，此处逐传带出）。
④ 课目识别（判据见 `scripts/kemu.py` 的 `IMPLEMENTED`，条数由该元组实算）、
⑤应期未落地——登记于 docs/TECH-DEBT.md（不写占位实现）。
本段**不出吉凶方向**：大六壬判吉凶须课目全表与《毕法赋》支撑，那两块落地前
任何「方向」输出都是臆测（AGENTS.md 铁律一/三）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
DISC = Path(__file__).resolve().parents[1]
for _p in (str(CORE), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.liuren_tables import DAY_DE, JI_GONG  # noqa: E402
from yishu_core.symbols import (  # noqa: E402
    BREAK_PAIRS,
    BRANCH_ELEMENTS,
    CHONG_PAIRS,
    HARM_PAIRS,
    HE_PAIRS,
    KE_CYCLE,
    SELF_PUNISHMENTS,
    SHENG_CYCLE,
    STEM_ELEMENTS,
    THREE_PUNISHMENTS_CYCLIC,
    THREE_PUNISHMENTS_MUTUAL,
    TOMB_MAP,
    WANG_XIANG_XIU_QIU_SI,
    wangxiangxiuqiusi,
)
from jiuzongmen import four_courses  # noqa: E402
from kemu import IMPLEMENTED as KEMU_IMPLEMENTED  # noqa: E402
from kemu import recognize as kemu_recognize  # noqa: E402
import structure_tags as _tags  # noqa: E402


def _load_verdicts() -> dict:
    return json.loads((DISC / "data" / "verdicts.json").read_text(encoding="utf-8"))


_XING: dict[str, set[str]] = {}
for _cyc in THREE_PUNISHMENTS_CYCLIC.values():
    for _i, _b in enumerate(_cyc):
        _XING.setdefault(_b, set()).add(_cyc[(_i + 1) % 3])
for _a, _b in THREE_PUNISHMENTS_MUTUAL.values():
    _XING.setdefault(_a, set()).add(_b)
    _XING.setdefault(_b, set()).add(_a)
for _s in SELF_PUNISHMENTS:
    _XING.setdefault(_s, set()).add(_s)
_KE_OF = dict(KE_CYCLE)
_HE_SET = {frozenset(p) for p in HE_PAIRS}
_CHONG_SET = {frozenset(p) for p in CHONG_PAIRS}
_HARM_SET = {frozenset(p) for p in HARM_PAIRS}
_BREAK_SET = {frozenset(p) for p in BREAK_PAIRS}
# 墓库唯一真值源在 core（AGENTS.md §二），此处仅别名
_TOMB_OF_ELEM = dict(TOMB_MAP)


def _relations_of(chuan: str, day_stem: str, day_branch: str) -> list[dict]:
    """一传与日干（寄宫）/日支的结构关系（鬼德合墓破害刑冲）。"""
    rels: list[dict] = []
    jigong = JI_GONG[day_stem]
    day_elem = STEM_ELEMENTS[day_stem]
    chuan_elem = BRANCH_ELEMENTS[chuan]
    if _KE_OF.get(chuan_elem) == day_elem:
        rels.append({"kind": "鬼", "target": "日干",
                     "note": f"{chuan_elem}克{day_elem}"})
    if chuan == DAY_DE[day_stem]:
        rels.append({"kind": "德", "target": "日干",
                     "note": f"日德在{DAY_DE[day_stem]}"})
    if chuan == _TOMB_OF_ELEM[day_elem]:
        rels.append({"kind": "墓", "target": "日干",
                     "note": f"{day_elem}墓在{chuan}"})
    for name, base in (("日干寄宫", jigong), ("日支", day_branch)):
        if chuan != base:
            pair = frozenset({chuan, base})
            if pair in _HE_SET:
                rels.append({"kind": "合", "target": name})
            if pair in _CHONG_SET:
                rels.append({"kind": "冲", "target": name})
            if pair in _HARM_SET:
                rels.append({"kind": "害", "target": name})
            if pair in _BREAK_SET:
                rels.append({"kind": "破", "target": name})
        if chuan in _XING.get(base, set()) or base in _XING.get(chuan, set()):
            kind = "自刑" if chuan == base else "刑"
            rels.append({"kind": kind, "target": name})
    return rels


def _richen(chart_out: dict, verdicts: dict) -> list[dict]:
    """日辰关系（《六壬大全》卷三「日辰」歌赋）：干/支与其上神的生克结构标签。

    只判**日干、日支**各自与其上神（四课之上神）之间的生克，共 10 条判据；
    标签名、释义与诀文一律取 `data/verdicts.json#richen`（代码零断语字面量）。
    只出结构标签与书源引文，不作吉凶方向（AGENTS.md 铁律一/三）。
    """
    moment = chart_out.get("moment") or {}
    day_gz = moment.get("day_ganzhi") or ""
    tianpan = chart_out.get("tianpan") or {}
    if len(day_gz) < 2 or not tianpan:
        return []
    day_stem, day_branch = day_gz[0], day_gz[1]
    courses = four_courses(day_stem, day_branch, tianpan)
    sg, sz = courses[0]["shang"], courses[2]["shang"]          # 干上神 / 支上神
    g, z = STEM_ELEMENTS[day_stem], BRANCH_ELEMENTS[day_branch]
    sge, sze = BRANCH_ELEMENTS[sg], BRANCH_ELEMENTS[sz]
    spec = verdicts.get("richen") or {}
    src = spec.get("出处") or ""
    cond = (
        ("日上生干", SHENG_CYCLE.get(sge) == g),
        ("日上克干", KE_CYCLE.get(sge) == g),
        ("干生上神", SHENG_CYCLE.get(g) == sge),
        ("干克上神", KE_CYCLE.get(g) == sge),
        ("日上生辰", SHENG_CYCLE.get(sge) == z),
        ("辰上生干", SHENG_CYCLE.get(sze) == g),
        ("日上克辰", KE_CYCLE.get(sge) == z),
        ("辰上克干", KE_CYCLE.get(sze) == g),
        ("日辰俱受生", SHENG_CYCLE.get(sge) == g and SHENG_CYCLE.get(sze) == z),
        ("日辰俱受克", KE_CYCLE.get(sge) == g and KE_CYCLE.get(sze) == z),
    )
    out: list[dict] = []
    for name, ok in cond:
        if not ok:
            continue
        entry = spec.get(name) or {}
        out.append({"name": name, "desc": entry.get("desc") or "",
                    "basis": (f"干上神{sg}({sge})、支上神{sz}({sze})与日"
                              f"{day_stem}({g})、支{day_branch}({z})论生克"),
                    "句": entry.get("句") or "", "出处": src})
    return out


def _richen_alias(richen: list[dict], verdicts: dict) -> dict:
    """日辰四气别名显示字段（OPT-rengui_dz-06）。

    书源《六壬鬼谷》L65-L68 逐字给出四气别名：
      L65 `凡日上神生日，谓之益气。`   L66 `凡日生上神，谓之脱气者`
      L67 `凡日上神克日，谓之损气；`   L68 `凡日克上神，谓之制气；`
    映射到《六壬大全》卷三「日辰」歌十句直陈式（**判定键仍用直陈式，不改判定**）：
      益气＝日上生干／日上生辰；脱气＝干生上神；
      损气＝日上克干／日上克辰；制气＝干克上神。
    另立 `六亲交叉校验` 段：书源 L180「凡三传所属五行，皆当与日干较取六亲，如甲日见太乙为子孙，
    见大吉为妻财，见登明为父母，见从魁为官星，见太冲为兄弟之类。」的五例登记为**交叉校验用例**——
    **不改四课取六亲的主实现**（本仓未实现六亲取法，故此段只作数据登记与对拍参照）。
    """
    alias_map = (verdicts.get("richen_alias") or {})
    pairs = alias_map.get("映射") or {}
    out: dict[str, list[str]] = {}
    for r in richen:
        hit = [a for a, keys in pairs.items() if r["name"] in (keys or [])]
        if hit:
            out[r["name"]] = hit
    return {
        "别名": out,
        "六亲交叉校验": alias_map.get("六亲交叉校验") or [],
        "口径": "别名为《六壬鬼谷》L65-L68 四气名，判定键仍用卷三直陈式十句；"
                "六亲五例只作交叉校验登记，不改四课取六亲主实现",
    }


def _class_god_block(chart_out: dict, verdicts: dict) -> dict:
    """类神类将结构标签组（OPT-rengui_dz-05）。

    与九宗门三传**并存**的附加标签组：类将取自《六壬鬼谷》L663 主／备回退链，
    类神之三传取自同书 L649。**不改九宗门取传判定**（AGENTS.md §四：禁改通用规则凑分）。
    只报「取哪一将」「类神之三传是哪三支」，不带任何取象吉凶。
    """
    layout = _tags.tianjiang_layout_items(chart_out)
    jiang = _tags.class_jiang(list(layout.values()), "青龙")
    tags = _tags.class_god(chart_out, jiang["类将"]) if jiang["类将"] else []
    return {
        "类将回退": jiang,
        "类神之三传": tags,
        "口径": "取象派专有层，与九宗门三传并存；书源 L649／L663 只取定位与回退链，取象吉凶不入结构层",
    }


def analyze(chart_out: dict) -> dict:
    day_gz = chart_out["moment"]["day_ganzhi"]
    day_stem, day_branch = day_gz[0], day_gz[1]
    verdicts = _load_verdicts()
    men_desc = (verdicts.get("men") or {}).get(chart_out["men"], {})

    chuan_rows = []
    for i, b in enumerate(chart_out["san_chuan"], start=1):
        chuan_rows.append({
            "pos": ("初", "中", "末")[i - 1],
            "branch": b,
            "dun_gan": chart_out["dun_gan"][i - 1],
            "tianjiang": (chart_out.get("chuan_tianjiang") or [{}])[i - 1].get("jiang", ""),
            "tianjiang_pos": (chart_out.get("chuan_tianjiang") or [{}])[i - 1].get("lin", ""),
            "relations": _relations_of(b, day_stem, day_branch),
        })

    kemu_hits = kemu_recognize(chart_out)
    richen = _richen(chart_out, verdicts)
    richen_alias = _richen_alias(richen, verdicts)
    struct_tags = _tags.all_tags(chart_out)
    class_god_blk = _class_god_block(chart_out, verdicts)

    _month_branch = (chart_out.get("moment") or {}).get("month_branch") or ""
    _tianpan = chart_out.get("tianpan") or {}

    # 旺相休囚死状态标签（OPT-liuren_zhinan_dz-02）：core wangxiangxiuqiusi 表按月支判，纯机械标签，不判吉凶不计分。
    # 用神内外事定位 + 六级应期刻度（OPT-rengui_dz-02）：纯结构标签，不判吉凶。
    # 书源《壬归》L109：「凡用在日上两课，为外事，主远，主去；用在辰上两课，为内事，主近，主来。」
    # 书源《壬归》L112：「凡用得太岁，事在年中；用得月建，事在本月；用得旬首，事在本旬；
    #   用得节气中立之首，事在半月之内；用得本日之干，事在本日之内；气得气首，事在五日之内。」
    _neishi_waishi = ""
    _chu_branch = chart_out["san_chuan"][0] if chart_out.get("san_chuan") else ""
    if _chu_branch:
        _c4 = four_courses(day_stem, day_branch, _tianpan)
        _ri_shang = {_c4[0]["shang"], _c4[1]["shang"]}  # 日上两课的上神
        _chen_shang = {_c4[2]["shang"], _c4[3]["shang"]}  # 辰上两课的上神
        if _chu_branch in _ri_shang:
            _neishi_waishi = "外事"
        elif _chu_branch in _chen_shang:
            _neishi_waishi = "内事"
    # 应期层级映射表（静态参考表）：六个参考支 → 时间粒度，不输出吉凶。
    _yingqi_map: dict[str, dict] = {
        "太岁": {"granularity": "年", "basis": "用得太岁，事在年中"},
        "月建": {"granularity": "月", "basis": "用得月建，事在本月"},
        "旬首": {"granularity": "旬", "basis": "用得旬首，事在本旬"},
        "节气首": {"granularity": "半月", "basis": "用得节气中立之首，事在半月之内"},
        "本日干": {"granularity": "日", "basis": "用得本日之干，事在本日之内"},
        "气首": {"granularity": "五日", "basis": "用得气首，事在五日之内"},
    }
    rengui_labels: dict = {"内外事": _neishi_waishi, "应期映射表": _yingqi_map}
    # 动态应期命中：比对初传与各参考项（可验证的项逐项报出，未实项留待后续接入）。
    _yingqi_hits: list[dict] = []
    if _chu_branch:
        # 旬首支反解：空亡两支为「旬首前二位、前一位」（唯一真值源 core ganzhi_calendar）
        _kong = chart_out["moment"].get("xunkong") or []
        _order = list(BRANCH_ELEMENTS.keys())  # 12支固定序（BRANCH_ELEMENTS 唯一真值源）
        _xun_head_val = _order[(_order.index(_kong[1]) + 1) % 12] if len(_kong) == 2 else ""
        for _ref, _info in _yingqi_map.items():
            _matched = False
            if _ref == "月建" and _chu_branch == _month_branch:
                _matched = True
            elif _ref == "旬首" and _xun_head_val and _chu_branch == _xun_head_val:
                _matched = True
            # 太岁/节气首/气首：需年支/节气表，本轮留待接入；本日干见下方判断
            elif _ref == "本日干":
                # 发用地支 vs 日干（仅同五行时需另行判断；本轮以位置映射为准）
                _matched = False  # 「本日之干」指日干本身（天干），与地支不同体系
            if _matched:
                _yingqi_hits.append({"reference": _ref,
                                     "granularity": _info["granularity"],
                                     "basis": _info["basis"]})
    rengui_labels["动态应期命中"] = _yingqi_hits

    wangxiang_labels: dict[str, dict] = {}
    if _month_branch:
        _chu_state = wangxiangxiuqiusi(_month_branch, BRANCH_ELEMENTS.get(_chu_branch, ""))
        wangxiang_labels["用神(初传)"] = {
            "branch": _chu_branch, "element": BRANCH_ELEMENTS.get(_chu_branch, ""),
            "state": _chu_state, "basis": f"{_month_branch}月，用神{_chu_branch}({BRANCH_ELEMENTS.get(_chu_branch, '')})"}
        _stem_state = wangxiangxiuqiusi(_month_branch, STEM_ELEMENTS.get(day_stem, ""))
        wangxiang_labels["日干"] = {
            "branch": day_stem, "element": STEM_ELEMENTS.get(day_stem, ""),
            "state": _stem_state, "basis": f"{_month_branch}月，日干{day_stem}({STEM_ELEMENTS.get(day_stem, '')})"}
        _branch_state = wangxiangxiuqiusi(_month_branch, BRANCH_ELEMENTS.get(day_branch, ""))
        wangxiang_labels["日支"] = {
            "branch": day_branch, "element": BRANCH_ELEMENTS.get(day_branch, ""),
            "state": _branch_state, "basis": f"{_month_branch}月，日支{day_branch}({BRANCH_ELEMENTS.get(day_branch, '')})"}
    factors = [
        {"code": "men", "label": chart_out["men"],
         "basis": chart_out.get("men_trigger", "")},
        {"code": "ke_name", "label": chart_out["ke_name"],
         "basis": men_desc.get("basis", "")},
        {"code": "san_chuan", "label": "、".join(chart_out["san_chuan"]),
         "basis": "三传遁干：" + "、".join(chart_out["dun_gan"])},
        {"code": "relations", "label": "三传与日干支关系",
         "basis": "；".join(f"{r['pos']}{r['branch']}"
                            + ("（" + "/".join(x["kind"] for x in r["relations"]) + "）"
                               if r["relations"] else "（无关系标签）")
                            for r in chuan_rows)},
        {"code": "richen", "label": "日辰关系（卷三「日辰」歌）",
         "basis": "；".join(r["name"] for r in richen) if richen
                  else "无已落判据的日辰关系命中"},  # 诀文见 data/verdicts.json#richen
        {"code": "kemu", "label": f"课目识别（已落机械判据 {len(KEMU_IMPLEMENTED)} 条）",
         "basis": "；".join(h["name"] for h in kemu_hits) if kemu_hits
                  else "无已落判据的课目命中"},  # 诀文/释义见 data/kemu.json
        {"code": "structure_tags", "label": f"结构标签（{sum(len(v) for v in struct_tags.values())} 条／"
                                            f"{len(struct_tags)} 个维度）",
         "basis": "；".join(f"{d}：{'、'.join(x['name'] for x in rows)}"
                            for d, rows in struct_tags.items()) or "无结构标签命中"},
    ]
    return {
        "discipline": "liuren",
        "id": chart_out.get("id", ""),
        "question": chart_out.get("question", ""),
        "chart_summary": {
            "日干支": day_gz,
            "时支": chart_out["moment"]["hour_branch"],
            "月将": chart_out["yuejiang"]["name"] + "（" + chart_out["yuejiang"]["branch"] + "）",
            "空亡": chart_out["moment"]["xunkong"],
            "天地盘": chart_out["tianpan"],
        },
        "men": chart_out["men"],
        "ke_name": chart_out["ke_name"],
        "richen": richen,
        "richen_alias": richen_alias,
        "san_chuan": chuan_rows,
        "kemu": kemu_hits,
        "structure_tags": struct_tags,
        "class_god": class_god_blk,
        "wangxiangxiuqiusi": wangxiang_labels,
        "rengui": rengui_labels,
        "factors": factors,
        "conclusion": {
            "strength": None,
            "pattern": chart_out["ke_name"],
            "direction": None,
            "note": f"不含吉凶方向：课目识别已落 {len(KEMU_IMPLEMENTED)} 条**纯结构**判据"
                    "（旺相/神煞/年命依赖者仍未落地），"
                    "《毕法赋》判据未接入，不写占位实现（TECH-DEBT 登记）",
        },
        "verdicts_note": verdicts.get("preamble", []),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="大六壬规则推演（机械标签，无吉凶断语）")
    ap.add_argument("chart_file", help="chart 段输出的 JSON 路径")
    ap.add_argument("--out", "-o", help="输出 JSON 路径（缺省打印 stdout）")
    args = ap.parse_args()
    chart_out = json.loads(Path(args.chart_file).read_text(encoding="utf-8"))
    out = analyze(chart_out)
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"analyze 已写出 → {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
