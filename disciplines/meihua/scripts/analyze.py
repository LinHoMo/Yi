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
  5. 应期（《卷二·先天后天论》：先天卦取卦气应期；应体之卦气宜盛不宜衰，
     旺则应速，衰则应迟；变卦为末后之期）
  6. 万物类象（《卷一·八卦万物属类》《八卦类象》）：机械挂到体/用/互/变各卦
  7. 多爻动合参（verdicts.json#multi_move_rules）：两爻及以上动时更重互变生克
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
    BRANCH_ELEMENTS,
    SHENG_CYCLE,
    KE_CYCLE,
    STEM_ELEMENTS,
    TRIGRAM_ELEMENTS,
    EIGHT_PALACES,
    HEXAGRAM_TRIGRAMS,
    wangxiangxiuqiusi,
)
from yishu_core.hexagram_texts import (  # noqa: E402
    HEXAGRAMS,
    HEXAGRAM_LINE_TEXTS,
)

# 六十四卦名 → 宫五行（变卦等别卦取其宫五行论生克）
_HEX_ELEMENT: dict[str, str] = {}
for _palace, _info in EIGHT_PALACES.items():
    for _name, _gen in _info["order"]:
        _HEX_ELEMENT[_name] = _info["element"]

# 干支五行（应期干支与体卦五行对应：《卷二·先天后天论》
# "乾、兑则应如庚、辛及申金之日…震、巽当应于甲、乙及支木之日"）
# 干支五行唯一真值源在 core（AGENTS.md §二），此处仅别名
_STEM_ELEMENT = STEM_ELEMENTS
_BRANCH_ELEMENT = dict(BRANCH_ELEMENTS)


def _load_verdicts() -> dict:
    p = DISC / "data" / "verdicts.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _load_classics() -> dict:
    p = DISC / "data" / "classics.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


VERDICTS = _load_verdicts()
CLASSICS = _load_classics()


def _classics(way, movings, helpers, hinderers, qi, multi_move, changed_hexagram) -> dict:
    """本次判读实际执行的古诀原文（逐字），供 narrate 末段附出。

    只作**所本原文**：不参与评分、不改判据（判据唯一真值源是 verdicts.json）。
    原文与出处由 `dev_tools/build_classics.py` 从书源逐字抽出并断言可回指。
    """
    rules = (CLASSICS.get("rules") or {})
    keys = ["起例_卦以八除", "起例_互卦", "体用总诀", "体用互变之诀"]
    if way in ("numbers", "two_numbers"):
        keys.append("起例_物数")
    elif way in ("datetime", "lunar"):
        keys.append("起例_年月日时")
    if qi:
        keys.append("体用衰旺之诀")
    if multi_move:
        keys.append("变卦式八则")
    if changed_hexagram:
        keys.append("占卦诀")
    picked: list[dict] = []
    for k in keys:
        if k in rules:
            picked.append({"键": k, **rules[k]})
    per_gua: list[dict] = []
    seen: set[str] = set()
    for kind, lst in (("生体", helpers), ("克体", hinderers)):
        for h in lst:
            entry = ((CLASSICS.get("per_gua") or {}).get(kind) or {}).get(h["卦"]) or {}
            if entry and h["卦"] not in seen:
                seen.add(h["卦"])
                per_gua.append({"键": f"{kind}·{h['卦']}", **entry})
    if not picked and not per_gua:
        return {}
    return {
        "规则": picked,
        "逐卦": per_gua,
        "来源": CLASSICS.get("source") or {},
        "备注": "原文为书源逐字（繁体照录），只作所本凭证，不参与评分、不改判据",
    }


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
    """体卦五行所应的干支（《先天后天论》卦气应期）。"""
    stems = [s for s, e in _STEM_ELEMENT.items() if e == element]
    branches = [b for b, e in _BRANCH_ELEMENT.items() if e == element]
    return stems + branches


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


def _analogies_of(trig: str | None) -> dict | None:
    """经卦/别卦 → 万物类象（verdicts.json#bagua_analogies）。别卦取上卦经卦类象。"""
    if not trig:
        return None
    bagua = VERDICTS.get("bagua_analogies") or {}
    if trig in bagua:
        entry = bagua[trig]
        return {k: v for k, v in entry.items() if k not in ("note", "所本", "categories")}
    # 别卦名 → 上经卦类象（辅助挂象；主类象仍看体用互变经卦）
    return None


def _analogy_table(topic: str, body: str, use: str) -> dict:
    """事类对应的书源类象**原文**（《卷一·八卦萬物屬類》逐字），挂到体卦/用卦。

    事类→类目键的映射在 `verdicts.json#wanwu_topic_keys`（数据，非代码字面量）；
    原文与行号在 `classics.json#wanwu`（构建器逐字抽取、门 [1c] 按行号回读核对）。
    只作取象依据，不参与评分。
    """
    spec = VERDICTS.get("wanwu_topic_keys") or {}
    keys = list((spec.get("topics") or {}).get(topic) or []) + list(spec.get("common") or [])
    table = CLASSICS.get("wanwu") or {}
    out: dict[str, dict] = {}
    for role, gua in (("体卦", body), ("用卦", use)):
        entry = table.get(gua) or {}
        picked = {k: entry[k]["原文"] for k in keys
                  if k in entry and isinstance(entry[k], dict)}
        if picked:
            out[role] = {"卦": gua, "类象": picked}
    return out


def _ti_yong_hu(chart_out: dict) -> dict:
    """体互／用互之分（OPT-meihua_yishu_dz-05）。

    书源《梅花易数》源L820 逐字：「然互卦则分其有体之互，有用之互。**如体在上，则上互为
    体之互，下互为用之互；体卦在下，则下互为体之互，上互为用之互。体互最紧，用互次之。**」

    实现：由 `chart.body_use_rule` 取体卦所在侧（上／下），据此把 `interacting_upper`／
    `interacting_lower` 分派为**体互**与**用互**，并按书源给的**权重次序**
    （卦用最紧 → 互次之 → 变又次之；体互最紧 → 用互次之）标注 `权重档`。
    **只作结构拆分与权重标注，不改任何方向输出**；权重档供证据层引用，不参与 verdict 计分
    （本仓 verdict 仍只由体用生克 + 卦气旺衰决定，见 `_verdict_of`）。
    """
    body_side = (chart_out.get("body_use_rule") or "")
    upper = chart_out.get("interacting_upper")
    lower = chart_out.get("interacting_lower")
    body_hu = upper if "上" in body_side else lower
    use_hu = lower if "上" in body_side else upper
    return {
        "体互": body_hu,
        "用互": use_hu,
        "体互位": "上互" if "上" in body_side else "下互",
        "用互位": "下互" if "上" in body_side else "上互",
        "权重档": {"体互": "最紧", "用互": "次之"},
        "体用位序": "卦用最紧，互次之，变卦又次之（源L820）",
        "出处": "《梅花易数》源L820",
        "计分": "否（本项只作证据层结构拆分与权重标注，不参与 verdict 计分）",
    }


_EXTERNAL_SIGNS: dict | None = None


def _external_sign_layer(chart_out: dict, external_signs: list | None) -> dict:
    """外应（三要十应）槽位（OPT-meihua_yishu_dz-04）。

    书源：
      · L729「凡占卜，体用为内，诸应卦为外卦……**苟不知合内外卦为断，谓体用自体用，
        三要十应自三要十应，如此则鲜见其有验者**……占卜之精者，无非合内外之道也。」
      · L735「凡占在静室，无所闻见，则无外卦，即不论外卦。但以全卦年月日值五行衰旺之气，
        以体用决之。」——**无外应时的口径**。
      · L970 逐字的外应取象映射：「如见老人、马、金玉圆物，得干。见老妇、牛、土瓦物，得坤之类。」
      · L978「此十应之理，凡占卜之际，耳闻目见以决吉凶，**并以体卦为主**，而详见生克
        比和之理。」——合参次序：先内（体用）后外（外应），外应**修正因子**由外应卦
        与**体卦**的生克比和给出。

    `external_signs` 由调用方**结构化传入**：每项 {物, 卦}（映射表数据化在
    `data/verdicts.json#external_signs`，见 `_external_sign_map`）。
    无外应时**显式标「外应空缺（静占）」**（源L735 口径），不静默略过。

    ⚠ 只出**修正因子**（生／克／比和三种结构标签）与外应卦本身，**不出吉凶断语**；
    因子**不参与 verdict 计分**（修正方向由 LLM 叙述，不由引擎断言）。
    """
    _blk = VERDICTS.get("external_signs") or {}
    if not external_signs:
        return {
            "有无外应": False,
            "口径": _blk.get("空缺提示", ""),
            "静占原文": _blk.get("静占口径", ""),
            "修正因子": [],
            "计分": _blk.get("计分提示", ""),
        }
    body_el = chart_out["body_element"]
    rows = []
    for item in external_signs:
        name = str(item.get("物") or item.get("sign") or "").strip()
        trig = str(item.get("卦") or item.get("trigram") or "").strip()
        if not trig:
            trig = _external_sign_map().get(name, "")
        if not trig:
            rows.append({"物": name, "卦": None,
                         "修正因子": None,
                         "备注": "映射表未收此物——不臆测其卦，须调用方补传或据"
                                 "verdicts.json#external_signs 补表"})
            continue
        kind, el = _interaction(trig, body_el)
        rows.append({
            "物": name, "卦": trig, "五行": el, "修正因子": kind,
            "合参": f"{trig}({el}) 对体卦{body_el}：{kind}",
        })
    return {
        "有无外应": True,
        "合参次序": "先内（体用）后外（外应）——源L729「合内外之道」、L978「并以体卦为主」",
        "外应": rows,
        "计分": _blk.get("计分提示", ""),
    }


def _external_sign_map() -> dict:
    """外应取象映射（源L970 逐字，数据化在 verdicts.json#external_signs.映射）。"""
    global _EXTERNAL_SIGNS
    if _EXTERNAL_SIGNS is None:
        block = VERDICTS.get("external_signs") or {}
        _EXTERNAL_SIGNS = dict(block.get("映射") or {})
    return _EXTERNAL_SIGNS


def _yao_ci_ref(movings: list[int], hexagram: str) -> dict | None:
    """挂《周易》卦辞 / 动爻爻辞到 analyze 输出（OPT-meihua_yishu_dz-02）。

    书源《梅花易数》「端法」（后天端法、物数、声音占例、字画占例等后天取数）：
    "后天占法，以《周易》爻辞断。**以定卦之主爻（动爻）取爻辞**；兼看本卦卦辞。"

    先天卦（以年月日时、干支、星辰起卦）——按《观梅占》《策数占》等古例，
    用体用生克 / 卦气旺衰断，**不挂《周易》爻辞**。
    故函数只在本仓「后天」口径下返回非 None 结构；先天口径返回 None。

    挂法：
      · `gua_ci`：本卦卦辞（`HEXAGRAMS` 第四列）
      · `yao_ci_list`：[{pos, cn_name, text}] 逐个动爻（HEXAGRAM_LINE_TEXTS[hexagram] index=pos-1）
    口径落到 `way` 时才生效 —— 调用方（`analyze`）按 `chart_out.way` 决定是否挂。
    """
    ci_list = HEXAGRAM_LINE_TEXTS.get(hexagram)
    if not ci_list:
        return None
    _YAO_NAME = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"]
    gua_ci = next((row for row in HEXAGRAMS if row[1] == hexagram), None)
    entries = []
    for pos in movings:
        if 1 <= pos <= len(ci_list):
            entries.append({
                "pos": pos,
                "cn": _YAO_NAME[pos - 1],
                "text": ci_list[pos - 1],
            })
    return {
        "gua_ci": gua_ci[4] if gua_ci else None,
        "yao_ci": entries,
        "本卦": hexagram,
        "动爻列表": list(movings),
        "口径": "后天端法：《系辞》'动则观其变而玩其占'；以动爻爻辞断",
        "出处": "《周易·系辞》+《梅花易数》后天端法",
    }


def analyze(chart_out: dict) -> dict:
    """chart 段输出 → 因子与判据（结构化，无成段断语）。"""
    body = chart_out["body"]
    use = chart_out["use"]
    body_el = chart_out["body_element"]
    use_el = chart_out["use_element"]
    topic = chart_out.get("topic") or "人事"
    question = chart_out.get("question", "")
    movings = chart_out.get("movings") or [chart_out.get("moving")]
    multi_move = bool(chart_out.get("multi_move")) or len(movings) > 1

    relation = _relation_of(body_el, use_el)

    # 各卦对体的作用：用卦 / 互下 / 互上 / 变出之卦
    # 变卦以"变出之卦"（动爻所在经卦变后的经卦）论五行，《观梅占》"变艮土生兑金"。
    # 多爻动两侧皆变时，上下变出之卦分列（《卷二》"最切看互卦变卦"）。
    actors = [
        ("用卦", use),
        ("互卦下", chart_out.get("interacting_lower")),
        ("互卦上", chart_out.get("interacting_upper")),
    ]
    changed_trigrams = chart_out.get("changed_trigrams")
    if multi_move and changed_trigrams and len(changed_trigrams) > 1:
        actors.append(("变卦下", chart_out.get("changed_lower")))
        actors.append(("变卦上", chart_out.get("changed_upper")))
    else:
        actors.append(("变卦", chart_out.get("changed_trigram")))
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

    # 万物类象：机械挂到体/用/互/变（《卷一·八卦万物属类》）
    ti_yong_hu = _ti_yong_hu(chart_out)
    analogies = {
        "体卦": {"卦": body, "类象": _analogies_of(body)},
        "用卦": {"卦": use, "类象": _analogies_of(use)},
        "互卦下": {"卦": chart_out.get("interacting_lower"),
                   "类象": _analogies_of(chart_out.get("interacting_lower"))},
        "互卦上": {"卦": chart_out.get("interacting_upper"),
                   "类象": _analogies_of(chart_out.get("interacting_upper"))},
    }
    # 体互／用互**单列**（源L820）：与上面的「互卦下／互卦上」并存，
    # 后者是位置命名，前者是按体卦所在侧的分派，二者不冲突、不互相覆盖。
    analogies["体互"] = {"卦": ti_yong_hu["体互"],
                       "类象": _analogies_of(ti_yong_hu["体互"]),
                       "权重档": ti_yong_hu["权重档"]["体互"]}
    analogies["用互"] = {"卦": ti_yong_hu["用互"],
                       "类象": _analogies_of(ti_yong_hu["用互"]),
                       "权重档": ti_yong_hu["权重档"]["用互"]}
    if multi_move and changed_trigrams and len(changed_trigrams) > 1:
        analogies["变卦下"] = {"卦": chart_out.get("changed_lower"),
                              "类象": _analogies_of(chart_out.get("changed_lower"))}
        analogies["变卦上"] = {"卦": chart_out.get("changed_upper"),
                              "类象": _analogies_of(chart_out.get("changed_upper"))}
    else:
        analogies["变出之卦"] = {"卦": chart_out.get("changed_trigram"),
                               "类象": _analogies_of(chart_out.get("changed_trigram"))}

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
        "所本": VERDICTS["basis_quotes"]["xiantian_houtian"],
    }

    # 综合判断：体用总诀基准 + 互变生克修正 + 旺衰修正
    # 卦象特断优先：《卷二·卦断遗论》"有不拘体用者"，命中即不再套体用生克。
    special = VERDICTS["hexagram_special"].get(f"{chart_out.get('hexagram')}·{chart_out.get('moving')}爻动")
    if special:
        verdict = {
            "方向": special["方向"],
            "说明": special["说明"],
            "特断": True,
            "所本": special["所本"],
        }
    else:
        verdict = _synthesize(relation, helpers, hinderers, qi, topic,
                              multi_move=multi_move, movings=movings)

    multi_info = None
    if multi_move:
        rules = VERDICTS.get("multi_move_rules") or {}
        multi_info = {
            "动爻列表": movings,
            "体用规则": chart_out.get("body_use_rule"),
            "变出之卦": chart_out.get("changed_trigrams") or [chart_out.get("changed_trigram")],
            "所本": rules.get("所本", ""),
            "体用取舍": rules.get("body_use", []),
            "合参": rules.get("synthesis", ""),
        }

    # ── 后天端法/手动挂《周易》爻辞（OPT-meihua_yishu_dz-02） ──
    # 后天起卦（以物数 / 声音 / 字画 / 手动定卦）以《周易》爻辞断 → 输出 yao_ci_ref。
    # 先天起卦（以年月日时 / 干支 / 星辰）不挂。
    way = chart_out.get("way")
    yao_ci_ref = None
    if way in ("manual", "two_numbers"):
        hexagram = chart_out.get("hexagram")
        if way == "manual":
            movings_for_yao = list(movings)
        else:
            # two_numbers：动爻由 `movings` 给出（实际自动取或显式指定）
            movings_for_yao = list(movings)
        if hexagram and movings_for_yao:
            ref = _yao_ci_ref(movings_for_yao, hexagram)
            if ref:
                ref["way"] = way
                ref["分轨口径"] = "后天端法挂《周易》爻辞（OPT-meihua_yishu_dz-02）"
                yao_ci_ref = ref

    return {
        "schema": "meihua-analyze-v2",
        "topic": topic,
        "question": question,
        "external_signs": _external_sign_layer(
            chart_out, chart_out.get("external_signs")),
        "ti_yong_hu": ti_yong_hu,
        "chart_summary": {
            "卦名": chart_out.get("hexagram"),
            "动爻": chart_out.get("moving"),
            "动爻列表": movings,
            "多爻动": multi_move,
            "体用规则": chart_out.get("body_use_rule"),
            "上卦": chart_out.get("upper"),
            "下卦": chart_out.get("lower"),
            "互卦下": chart_out.get("interacting_lower"),
            "互卦上": chart_out.get("interacting_upper"),
            "体互": ti_yong_hu["体互"],
            "用互": ti_yong_hu["用互"],
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
        "analogies": analogies,
        "multi_move": multi_info,
        "body_qi": qi,
        "topic_verdict": topic_verdict,
        "sheng_ti": sheng_ti,
        "ke_ti": ke_ti,
        "analogy_table": _analogy_table(topic, body, use),
        "timing": timing,
        "classics": _classics(chart_out.get("way"), movings, helpers, hinderers,
                              qi, multi_move, chart_out.get("changed_hexagram")),
        "yao_ci_ref": yao_ci_ref,
        "conclusion": verdict,
        "factors": [
            {"因子": "体用关系", "权重": 40, "判据": relation,
             "判语": VERDICTS["body_use_general"]["relations"].get(relation),
             "所本": "《卷二·体用总诀》"},
            {"因子": "生克之卦", "权重": 30,
             "判据": f"生体 {len(helpers)} 卦 / 克体 {len(hinderers)} 卦",
             "所本": VERDICTS["basis_quotes"]["ti_yong_shengke"]},
            {"因子": "卦气旺衰", "权重": 20,
             "判据": qi["状态"] if qi else "未定（无月令）",
             "所本": VERDICTS["basis_quotes"]["guaqi"]},
            {"因子": "应期", "权重": 10,
             "判据": "、".join(timing["卦气应期"]) or "无",
             "所本": "《卷二·先天后天论》"},
        ],
    }


def _synthesize(relation: str, helpers: list, hinderers: list,
                qi: dict | None, topic: str,
                multi_move: bool = False, movings: list | None = None) -> dict:
    """综合吉凶：以体用关系为基准，互变生克与旺衰做修正。

    规则出处均标在结论里；方向措辞遵循 AGENTS.md（凶象用"偏向/有…信号"，
    不用"注定"）。天时占不分体用，另行处理（全观诸卦五行）。
    多爻动时更重互变合参（《卷二》"生体多者则愈吉，克体多者则愈凶"）。
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
    if multi_move:
        # 多爻动更重互变净势（《卷二·体用生克篇》"生体多者则愈吉，克体多者则愈凶"）
        score += 0.4 * (len(helpers) - len(hinderers))
    if qi:
        score += {"旺": 0.5, "相": 0.2, "休": 0.0, "囚": -0.2, "死": -0.5}.get(qi["状态"], 0)

    if topic == "天时":
        direction = "平"          # 天时由卦象五行主导，不套体用吉凶
        tone = VERDICTS["basis_quotes"]["tianshi"]
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
    change = "变卦生体" if any(h["位"].startswith("变卦") for h in helpers) else \
             ("变卦克体" if any(h["位"].startswith("变卦") for h in hinderers) else "变卦比和/无关")
    # 末后克体：体用虽和，终局受克则不得言吉（《卷二·体用总诀》变乃末后之期）
    if change == "变卦克体" and direction in ("吉", "平吉"):
        direction, tone = "平凶", "体用虽顺，然变卦克体（末后之期受克），终局偏向有阻"
    result = {
        "方向": direction,
        "说明": tone,
        "变卦作用": change,
        "所本": "《卷二·体用总诀》 + 《卷二·先天后天论》（卦气旺衰）",
    }
    if multi_move:
        result["多爻动"] = True
        result["动爻列表"] = list(movings or [])
        result["所本"] += " + 《卷二·体用生克篇》（生体多者愈吉、克体多者愈凶，多爻动重互变合参）"
    return result


if __name__ == "__main__":
    import argparse
    import json as _json

    ap = argparse.ArgumentParser(description="梅花易数分析（analyze 段）")
    ap.add_argument("chart_json", nargs="?", help="chart 段输出 JSON 文件（缺省跑金标准自检）")
    ap.add_argument("-o", "--out", type=Path, help="写出 analyze JSON")
    args = ap.parse_args()

    if not args.chart_json:
        # 金标准自检：观梅占 → 体兑金、用离火，用克体，变艮生体
        from chart import chart_from_numbers, chart_from_manual
        r = chart_from_numbers(5, 12, 17, 9)
        a = analyze(r)
        assert a["body_use"]["关系"] == "用克体", a["body_use"]
        assert a["conclusion"]["方向"] in ("平凶", "凶"), a["conclusion"]
        sheng = [h["卦"] for h in a["interaction"]["生体之卦"]]
        assert "艮" in sheng, a["interaction"]
        assert a["analogies"]["体卦"]["卦"] == "兑", a["analogies"]
        assert a["analogies"]["体卦"]["类象"].get("人物"), a["analogies"]
        assert a["multi_move"] is None, a["multi_move"]
        print("观梅占 analyze 校验通过：", a["conclusion"]["方向"], a["conclusion"]["说明"])
        # 多爻动自检：乾上震下 1,2 动 → 上体下用，体克用
        m = chart_from_manual("乾", "震", [1, 2])
        ma = analyze(m)
        assert ma["body_use"]["关系"] == "体克用", ma["body_use"]
        assert ma["chart_summary"]["多爻动"] is True, ma["chart_summary"]
        assert ma["multi_move"] and ma["multi_move"]["动爻列表"] == [1, 2], ma["multi_move"]
        print("多爻动 analyze 校验通过：", ma["multi_move"]["体用规则"],
              ma["body_use"]["关系"], ma["conclusion"]["方向"])
        # OPT-meihua_yishu_dz-02：端法/手动 → 带 yao_ci_ref，先天不带
        assert ma.get("yao_ci_ref") is not None, "manual 方式应带 yao_ci_ref"
        assert ma["yao_ci_ref"]["本卦"] == "无妄", ma["yao_ci_ref"]
        assert len(ma["yao_ci_ref"]["yao_ci"]) == 2
        print("端法挂爻校验通过：", ma["yao_ci_ref"]["本卦"],
              [y["cn"] for y in ma["yao_ci_ref"]["yao_ci"]])
        return_hex = chart_from_numbers(5, 12, 17, 9)
        ra = analyze(return_hex)
        assert ra.get("yao_ci_ref") is None, "numbers(先天)方式不带 yao_ci_ref"
        print("先天分轨校验通过：numbers 方式 yao_ci_ref == None")
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
