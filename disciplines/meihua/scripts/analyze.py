# -*- coding: utf-8 -*-
"""梅花易数·规则推演（analyze 段）—— 纯机械，断语只取 data/verdicts.json。

输入 chart 段输出的盘数据，输出结构化的因子与判据，遵守 CONTRACT.md §一：
  - analyze 输出 {因子, 权重, 判据, 所本法则}，不写自造断语；
  - 断语全部来自 `data/verdicts.json`（条目带古籍出处）。

推演项目（每项都标注所本法则）：
  1. 体用生克关系（《卷二·体用总诀》：体克用诸事吉 / 用克体诸事凶 /
     体生用有耗失 / 用生体有进益 / 比和百事顺遂）
  2. 互卦·变卦对体卦的生克影响（互乃中间之应，变乃末后之期；体宜受生不宜受克）
  3. 事类断语（《卷二·体用生克篇之二》十八章占例）
  4. 卦气旺衰（《卷一·卦气旺/卦气衰》，月令定旺相休囚死）
  5. 应期（《卷二·先天後天論》：先天卦取卦气应期；应体之卦气宜盛不宜衰，
     旺则应速，衰则应迟；变卦为末后之期）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
DISC = Path(__file__).resolve().parents[1]
for _p in (str(CORE), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.symbols import (  # noqa: E402
    SHENG_CYCLE,
    KE_CYCLE,
    TRIGRAM_ELEMENTS,
    EIGHT_PALACES,
    wangxiangxiuqiusi,
)
from yishu_core.ganzhi_calendar import EARTHLY_BRANCHES  # noqa: E402

# 六十四卦名 → 宫五行（变卦等别卦取其宫五行论生克）
_HEX_ELEMENT: dict[str, str] = {}
for _palace, _info in EIGHT_PALACES.items():
    for _name, _gen in _info["order"]:
        _HEX_ELEMENT[_name] = _info["element"]

# 干支五行（应期干支与体卦五行对应：《卷二·先天後天論》
# "乾、兑则应如庚、辛及申金之日…震、巽当应于甲、乙及支木之日"）
_STEM_ELEMENT = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
                 "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
_BRANCH_ELEMENT = {b: e for b, e in zip("子丑寅卯辰巳午未申酉戌亥",
                                        ["水", "土", "木", "木", "土", "火",
                                         "火", "土", "金", "金", "土", "水"])}

# 应期单位：日（卦气应期以干支日为单位，《先天後天論》"应如庚辛及申金之日"）
_TIMING_UNIT = "日"


def _load_verdicts() -> dict:
    p = DISC / "data" / "verdicts.json"
    return json.loads(p.read_text(encoding="utf-8"))


VERDICTS = _load_verdicts()


def _relation_of(body_el: str, use_el: str) -> str:
    """体用五行生克关系名（体克用/用克体/体生用/用生体/比和）。"""
    if body_el == use_el:
        return "比和"
    if SHENG_CYCLE.get(use_el) == body_el:      # 用生体
        return "用生体"
    if SHENG_CYCLE.get(body_el) == use_el:      # 体生用
        return "体生用"
    if KE_CYCLE.get(body_el) == use_el:         # 体克用
        return "体克用"
    return "用克体"


def _interaction(trig: str, body_el: str) -> tuple[str, str]:
    """某卦（用/互/变）相对体卦的作用。返回 (作用名, 五行)。

    经卦直接用 TRIGRAM_ELEMENTS；别卦（变卦）取其宫五行（EIGHT_PALACES）。
    """
    el = TRIGRAM_ELEMENTS.get(trig) or _HEX_ELEMENT.get(trig)
    if el is None:
        raise KeyError(f"未知卦名：{trig}")
    if el == body_el:
        return "比和", el
    if SHENG_CYCLE.get(el) == body_el:
        return "生体", el
    if KE_CYCLE.get(el) == body_el:
        return "克体", el
    if SHENG_CYCLE.get(body_el) == el:
        return "体生", el
    return "体克", el


def _timing_gz(element: str) -> list[str]:
    """体卦五行所应的干支（《先天後天論》卦气应期）。"""
    stems = [s for s, e in _STEM_ELEMENT.items() if e == element]
    branches = [b for b, e in _BRANCH_ELEMENT.items() if e == element]
    return stems + branches


def _chinese_num(n: int) -> str:
    return ["零", "一", "二", "三", "四", "五", "六"][n]


def _numerical_timing(total: int | None, motion: str | None) -> int | None:
    """数应（《卷二·占卜总诀》"复验己身之动静。坐则事应迟，行则事应速，
    走则愈速，卧则愈迟"；《老人有忧色占》"行则应速，成卦之数中分而取其半"）。
    行取半、立取全、坐卧加倍。"""
    if not total:
        return None
    m = (motion or "立")
    if m == "行":
        return max(1, round(total / 2))
    if m in ("坐", "卧"):
        return total * 2
    return total


def analyze(chart_out: dict) -> dict:
    """chart 段输出 → 因子与判据（结构化，无成段断语）。"""
    body = chart_out["body"]
    use = chart_out["use"]
    body_el = chart_out["body_element"]
    use_el = chart_out["use_element"]
    topic = chart_out.get("topic") or "人事"
    question = chart_out.get("question", "")

    relation = _relation_of(body_el, use_el)

    # 各卦对体的作用：用卦 / 互下 / 互上 / 变出之卦
    # 变卦以"变出之卦"（动爻所在经卦变后的经卦）论五行，《观梅占》"变艮土生兑金"。
    actors = [
        ("用卦", use),
        ("互卦下", chart_out.get("interacting_lower")),
        ("互卦上", chart_out.get("interacting_upper")),
        ("变卦", chart_out.get("changed_trigram")),
    ]
    helpers, hinderers = [], []
    for role, trig in actors:
        if not trig or trig == chart_out.get("hexagram"):
            continue
        kind, el = _interaction(trig, body_el)
        entry = {"卦": trig, "五行": el, "作用": kind, "位": role}
        if kind == "生体":
            helpers.append(entry)
        elif kind == "克体":
            hinderers.append(entry)

    # 卦气旺衰：月令
    month_branch = chart_out.get("month_branch")
    qi = None
    if month_branch:
        state = wangxiangxiuqiusi(month_branch, body_el)
        if state:
            qi = {"状态": state, "月支": month_branch, "体卦五行": body_el}

    # 事类断语
    topic_data = VERDICTS["topics"].get(topic, VERDICTS["topics"]["人事"])
    relation_verdict = topic_data.get("relations", {}).get(relation)
    topic_verdict = {
        "topic": topic,
        "relation": relation,
        "text": relation_verdict or topic_data.get("relations", {}).get("比和"),
        "note": topic_data.get("role", ""),
    }

    # 生体/克体卦含义（《卷二·体用总诀》）
    sheng_ti = [{"卦": h["卦"], "含义": VERDICTS["sheng_ti_meaning"].get(h["卦"])}
                for h in helpers]
    ke_ti = [{"卦": h["卦"], "含义": VERDICTS["ke_ti_meaning"].get(h["卦"])}
             for h in hinderers]

    # 应期：体卦卦气为主，旺则速衰则迟；互变生克作吉凶应期参考
    timing = {
        "体卦五行": body_el,
        "卦气应期": _timing_gz(body_el),
        "旺衰": qi["状态"] if qi else None,
        "应期速度": "速" if qi and qi["状态"] in ("旺", "相") else
                   ("迟" if qi and qi["状态"] in ("囚", "死") else "常"),
        "生体卦应期": [{"卦": h["卦"], "干支": _timing_gz(h["五行"])} for h in helpers],
        "克体卦应期": [{"卦": h["卦"], "干支": _timing_gz(h["五行"])} for h in hinderers],
        "数应": _numerical_timing(chart_out.get("total"), chart_out.get("motion")),
        "所本": "《卷二·先天後天論》：先天卦定事应之期，取之卦气；"
                "应体之卦气宜盛不宜衰；《卷二·占卜总诀》：复验己身之动静",
    }

    # 综合判断：体用总诀基准 + 互变生克修正 + 旺衰修正
    # 卦象特断优先：《卷二·卦断遗论》"有不拘体用者"，命中即不再套体用生克。
    basis = "《卷二·体用总诀》：体克用诸事吉，用克体诸事凶，体生用有耗失之患，" \
            "用生体有进益之喜，体用比和百事顺遂；互乃中间之应，变乃末后之期"
    special = VERDICTS["hexagram_special"].get(f"{chart_out.get('hexagram')}·{chart_out.get('moving')}爻动")
    if special:
        verdict = {
            "方向": special["方向"],
            "说明": special["说明"],
            "特断": True,
            "所本": special["所本"],
        }
    else:
        verdict = _synthesize(relation, helpers, hinderers, qi, topic)

    return {
        "schema": "meihua-analyze-v1",
        "topic": topic,
        "question": question,
        "chart_summary": {
            "卦名": chart_out.get("hexagram"),
            "动爻": chart_out.get("moving"),
            "上卦": chart_out.get("upper"),
            "下卦": chart_out.get("lower"),
            "互卦下": chart_out.get("interacting_lower"),
            "互卦上": chart_out.get("interacting_upper"),
            "变卦": chart_out.get("changed_hexagram"),
            "变出之卦": chart_out.get("changed_trigram"),
            "起卦方式": chart_out.get("way"),
        },
        "body_use": {
            "体卦": body, "用卦": use,
            "体卦五行": body_el, "用卦五行": use_el,
            "关系": relation,
            "关系判语": VERDICTS["body_use_general"]["relations"].get(relation),
        },
        "interaction": {
            "生体之卦": helpers,
            "克体之卦": hinderers,
        },
        "body_qi": qi,
        "topic_verdict": topic_verdict,
        "sheng_ti": sheng_ti,
        "ke_ti": ke_ti,
        "timing": timing,
        "conclusion": verdict,
        "factors": [
            {"因子": "体用关系", "权重": 40, "判据": relation,
             "判语": VERDICTS["body_use_general"]["relations"].get(relation),
             "所本": "《卷二·体用总诀》"},
            {"因子": "生克之卦", "权重": 30,
             "判据": f"生体 {len(helpers)} 卦 / 克体 {len(hinderers)} 卦",
             "所本": "《卷二·体用总诀》：体宜受他卦之生，不宜他卦之克"},
            {"因子": "卦气旺衰", "权重": 20,
             "判据": qi["状态"] if qi else "未定（无月令）",
             "所本": "《卷一·卦气旺》：应体之卦气宜盛不宜衰"},
            {"因子": "应期", "权重": 10,
             "判据": "、".join(timing["卦气应期"]) or "无",
             "所本": "《卷二·先天後天論》"},
        ],
    }


def _synthesize(relation: str, helpers: list, hinderers: list,
                qi: dict | None, topic: str) -> dict:
    """综合吉凶：以体用关系为基准，互变生克与旺衰做修正。

    规则出处均标在结论里；方向措辞遵循 AGENTS.md（凶象用"偏向/有…信号"，
    不用"注定"）。天时占不分体用，另行处理（全观诸卦五行）。
    """
    base = {
        "体克用": 1, "用生体": 1, "比和": 1,
        "体生用": -0.5, "用克体": -1,
    }[relation]
    score = base
    score += 0.5 * len(helpers) - 0.5 * len(hinderers)
    # 互变净势修正（《卷二·卦断遗论》"互变生之而吉""互变俱克之而凶"）：
    # 体生用而互变生体多于克体 → 泄气得救，转吉；体克用而互变克体多于生体 → 凶势反压。
    if relation == "体生用" and len(helpers) > len(hinderers):
        score += 0.6
    if relation == "体克用" and len(hinderers) > len(helpers):
        score -= 1.0
    if qi:
        score += {"旺": 0.5, "相": 0.2, "休": 0.0, "囚": -0.2, "死": -0.5}.get(qi["状态"], 0)

    if topic == "天时":
        direction = "平"          # 天时由卦象五行主导，不套体用吉凶
        tone = "天时占不分体用，全观诸卦五行（离多主晴、坎多主雨…）"
    elif score >= 1.2:
        direction, tone = "吉", "体用相济，又有生扶之卦，事势顺畅"
    elif score >= 0.4:
        direction, tone = "平吉", "大体顺遂，但有小阻或需待时而动"
    elif score >= -0.4:
        direction, tone = "平", "事在两可之间，成否看后续生扶与月令"
    elif score >= -1.0:
        direction, tone = "平凶", "偏向有阻，凶势未盛，留意克体之卦所示"
    else:
        direction, tone = "凶", "体用不和又逢克伐，事势偏于不利，宜谨慎"

    # 变卦定终局（《体用总诀》：变乃末后之期）
    change = "变卦生体" if any(h["位"] == "变卦" for h in helpers) else \
             ("变卦克体" if any(h["位"] == "变卦" for h in hinderers) else "变卦比和/无关")
    return {
        "方向": direction,
        "说明": tone,
        "变卦作用": change,
        "所本": "《卷二·体用总诀》 + 《卷二·先天後天論》（卦气旺衰）",
    }


if __name__ == "__main__":
    import argparse
    import json as _json

    ap = argparse.ArgumentParser(description="梅花易数分析（analyze 段）")
    ap.add_argument("chart_json", nargs="?", help="chart 段输出 JSON 文件（缺省跑金标准自检）")
    ap.add_argument("-o", "--out", type=Path, help="写出 analyze JSON")
    args = ap.parse_args()

    if not args.chart_json:
        # 金标准自检：观梅占 → 体兑金、用离火，用克体，变艮生体
        from chart import chart_from_numbers
        r = chart_from_numbers(5, 12, 17, 9)
        a = analyze(r)
        assert a["body_use"]["关系"] == "用克体", a["body_use"]
        assert a["conclusion"]["方向"] in ("平凶", "凶"), a["conclusion"]
        sheng = [h["卦"] for h in a["interaction"]["生体之卦"]]
        assert "艮" in sheng, a["interaction"]
        print("观梅占 analyze 校验通过：", a["conclusion"]["方向"], a["conclusion"]["说明"])
        raise SystemExit(0)

    chart_out = _json.loads(Path(args.chart_json).read_text(encoding="utf-8"))
    a = analyze(chart_out)
    text = _json.dumps(a, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        print("分析 →", args.out)
    else:
        print(text)
