#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`data/cases/bazi_dayun_cases.json`（行运见证集）的回验器。

本集不参与对齐分，但它是一切「运步＋流年」结论的唯一书据来源，故每一条都必须：
  ① 引文（source_quote／书判[].断／卒）逐字回到底本该行；
  ② 四柱过**五虎遁**自洽——月柱天干必须由年干推出，否则四柱是抄错或拼凑的；
  ③ 运序自月柱按声明方向**连续**，一步不差；
  ④ 方向**唯一**：书给的运名在反方向 12 步里不得出现（否则顺逆无法判定，本条不该入库）；
  ⑤ 性别与「阳男阴女顺行、阴男阳女逆行」一致（《神峰通考》起大运法 源L2606-2612）。
④ 是本器存在的主要理由：机械链检测会把段内别处干支（含日柱本身）算进链长而虚增命中，
只有「反方向无此运」才证明运序确实出自本命的排法。

⑥（第三百六十五批，`corpus_gap_check`）不看见证集，改看**主评分语料**：把「主评分语料
按行运评分 = 0 例」这句空档，变成三条可重跑的读数（决定性语汇 0 命中／广义「运」字
9 例逐例登记语境／四柱-only 起运取值是占位常数），理据见该函数上方注释。

用法：
    python dev_tools/check_dayun_cases.py            # 回验，有问题退码 1
    python dev_tools/check_dayun_cases.py --selftest # 负例自证：造假引文／反方向运序必须被抓
"""
from __future__ import annotations

import json
import re
import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "data" / "cases" / "bazi_dayun_cases.json"

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
# 五虎遁：年干 -> 正月（寅月）天干
TIGER = {"甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚",
         "辛": "庚", "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲"}
YANG = set("甲丙戊庚壬")
DROP = set("，。！？；：、（）()「」『』“”\"…·—-《》【】　 \t\r\n")
GZ_RE = re.compile(r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]")


def norm(s: str) -> str:
    return "".join(c for c in s if c not in DROP)


def gz_index(gz: str) -> int:
    for i in range(60):
        if STEMS[i % 10] + BRANCHES[i % 12] == gz:
            return i
    return -1


def month_pillar(year_stem: str, month_branch: str) -> str:
    """五虎遁推月柱：寅月起于 TIGER[年干]，逐月进一位。"""
    off = (BRANCHES.index(month_branch) - 2) % 12
    return STEMS[(STEMS.index(TIGER[year_stem]) + off) % 10] + month_branch


def dayun_seq(pillar: str, direction: str, n: int) -> list[str]:
    i = gz_index(pillar)
    step = 1 if direction == "顺" else -1
    return [STEMS[(i + step * k) % 10] + BRANCHES[(i + step * k) % 12]
            for k in range(1, n + 1)]


def line_of(case: dict, problems: list[str]) -> str:
    f = ROOT / case["provenance"]["file"]
    if not f.exists():
        problems.append(f"{case['id']}：底本不存在 {f.name}")
        return ""
    lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
    ln = case["provenance"]["line"]
    if not (1 <= ln <= len(lines)):
        problems.append(f"{case['id']}：源L{ln} 越界（底本共 {len(lines)} 行）")
        return ""
    return lines[ln - 1]


def check(case: dict, problems: list[str], notes: list[str]) -> None:
    raw = line_of(case, problems)
    nraw = norm(raw)
    if not nraw:
        return

    # ① 引文逐字
    quotes = [case.get("source_quote", "")]
    dy = case["expected"]["dayun"]
    for seg in dy.get("书判", []):
        quotes.append(seg.get("断", ""))
    quotes.append(dy.get("卒", ""))
    hit = 0
    for q in quotes:
        nq = norm(q)
        if not nq:
            continue
        if nq in nraw:
            hit += 1
        else:
            problems.append(f"{case['id']}：引文不在源行内 → {q[:30]}…")
    if not norm(case.get("source_quote", "")):
        problems.append(f"{case['id']}：无 source_quote，本器无从回验")
    if dy.get("流年") and norm(dy["流年"]) not in nraw:
        problems.append(f"{case['id']}：流年 {dy['流年']} 未在该源行出现")

    # ② 四柱过五虎遁
    pills = case["pillars_raw"].split()
    if len(pills) != 4 or any(gz_index(p) < 0 for p in pills):
        problems.append(f"{case['id']}：四柱不合法 {case['pillars_raw']}")
        return
    y, m = pills[0], pills[1]
    if y[0] not in nraw or m[0] + m[1] not in nraw:
        notes.append(f"{case['id']}：年干/月柱未在源行逐字出现（书以整柱写出者已验，散写者只记）")
    exp_m = month_pillar(y[0], m[1])
    if exp_m != m:
        problems.append(f"{case['id']}：月柱 {m} 与五虎遁自年干{y[0]}推得 {exp_m} 不符")

    # ③ 运序连续
    direction = "顺" if "顺行" in dy["排法"] else ("逆" if "逆行" in dy["排法"] else "")
    if not direction:
        problems.append(f"{case['id']}：排法未写顺行/逆行 → {dy['排法']}")
        return
    seq = dy["运序"]
    want = dayun_seq(m, direction, len(seq))
    if seq != want:
        problems.append(f"{case['id']}：运序非自月柱{m}{direction}行连续 → 书列 {seq} 应为 {want}")
        return

    # ④ 方向唯一：书给的每一个运名都不得同时出现在反方向 12 步里
    anti = set(dayun_seq(m, "顺" if direction == "逆" else "逆", 12))
    named = set()
    for seg in dy.get("书判", []):
        named.update(GZ_RE.findall(seg.get("运", "")))
    if not named:
        problems.append(f"{case['id']}：书判未给出任何大运干支，本条不配入本集")
    for gz in sorted(named):
        if gz not in want:
            problems.append(f"{case['id']}：书判运 {gz} 不在运序 {want} 内")
        elif gz in anti:
            problems.append(f"{case['id']}：书判运 {gz} 反方向亦出现 → 顺逆不唯一，不得入库")
    # 书但言方位/支者须写明定干依据
    for seg in dy.get("书判", []):
        if "运依据" in seg and not norm(seg["运依据"]):
            problems.append(f"{case['id']}：{seg.get('运')} 有 运依据 键却为空")

    # ⑤ 性别依书律
    g = case.get("gender", "")
    sex = "男" if g.startswith("男") else ("女" if g.startswith("女") else "")
    if sex == "":
        notes.append(f"{case['id']}：性别未注明，本器不核 ⑤")
        return
    rule = f"{'阳' if y[0] in YANG else '阴'}{sex}{'顺' if direction == '顺' else '逆'}行"
    if rule not in g:
        problems.append(f"{case['id']}：性别依据不含『{rule}』（年干{y[0]}/{sex}/{direction}行）")
    if sex == "男" and direction == "顺" and y[0] not in YANG:
        problems.append(f"{case['id']}：阴年男当逆行，本条却声明顺行")
    if sex == "男" and direction == "逆" and y[0] in YANG:
        problems.append(f"{case['id']}：阳年男当顺行，本条却声明逆行")


ENGINE_EXPECT = {
    # 书在该运步明言了「支/干引动命局」的机制，引擎必须出同型标签（漏标＝判据未落地）
    # 注：判据已改为运、岁共用一处实现（yindong_relations），故 kind 不再带 yun_ 前缀。
    "DY004": {"乙巳": {"gan_yin_chu_yi_ju"}},          # 源L387「引出亥卯未木局」
    "DY007": {"辛亥": {"san_he_ban_he"}},               # 源L2531「亥卯合局印授扶身」
    "DY008": {"丙申": {"san_he_ban_he"}},               # 源L1864 申与命月子半合水＝官杀局，书云「杀重」
    "DY010": {"丁丑": {"bu_san_he_di_san_zhi"}},        # 源L1856「是巳酉丑会金局」
    "DY011": {"辛丑": {"zhi_tian_shi", "gong_ge_luo_kong"},      # 源L1848 夹丑填实＋落空破拱（三处同证）
              "庚子": {"zhi_chong_ming"}},                        # 源L1848「又是午月，冲破甲子」（冲月支午，与拱无关）
    "DY012": {"辛卯": {"zhi_tian_shi"}},                # 源L1848「行辛卯运填实卒」
    "DY009": {"己丑": {"xing_ru_mu"}},                  # 源L1868「后大运行己丑…庚入墓也」（金墓在丑）
}
# 墓层还须对「何神入墓」：书在 DY009 明标庚金为癸水之印绶 ⇒ 印星入墓
# 拱格日时是否在《神峰通考》源L917 十日清单内（书内两处不一致，故分档而不擅扩清单）
GONG_ROSTER_EXPECT = {"DY011": {"辛丑": True}, "DY012": {"辛卯": False}}
# 裁定过的反面判据（落空破拱 ⇒ 无格可伤）：不该出的标签若出现，同样是判红，
# 否则「守卫」写反了方向也能一路绿过去。
ENGINE_FORBID = {"DY011": {"辛丑": {"gong_ge_shou_shang"}}}
ENGINE_REL = {"DY009": {"己丑": ("金", "印")}, "DY010": {"丁丑": ("金", "官杀")}}
SUI_EXPECT = {
    # 岁支（流年支）引动：#31⑤ 的两条逐字书例
    "DY006": [{"gz": "辛亥", "kind": "san_he_ban_he", "value": "木", "rel": "财"},
              {"gz": "乙亥", "kind": "san_he_ban_he", "value": "木", "rel": "财"}],
    # 源L2528「再行卯运，及**岁支财神**会局，受职州判，大发财利」：庚日主，命具卯（中神），岁支亥 ⇒ 半合木局＝财
    "DY002": [{"gz": "庚子", "kind": "san_he_ban_he", "value": "水", "rel": "印"}],
    # 源L388「行己巳运金生之地，见庚子年；庚金为七杀，又见子水」：甲日主，命具申，岁支子（中神）⇒ 半合水局
}
PILLAR_KEYS = ("year", "month", "day", "hour")


def engine_check(data: dict, problems: list[str], notes: list[str]) -> tuple[int, int]:
    """第二层回验：引擎自己排的大运必须与书一致，且书明言的引动机制必须出标签。"""
    sys.path.insert(0, str(ROOT / "scripts"))
    sys.path.insert(0, str(ROOT / "core"))
    try:
        from bazi_factors.dayun import (dayun_ming_yindong, dayun_table,
                                        liunian_ming_yindong, judge_dayun_cheng_bai)
    except Exception as e:
        problems.append(f"引擎回验起不来（import 失败）：{e}")
        return 0, 0
    seq_ok = mech_ok = 0
    verdict_ok = want_verdict = 0
    for case in data["cases"]:
        gzs = case["pillars_raw"].split()
        sex = "男" if case.get("gender", "").startswith("男") else "女"
        chart = {"pillars": {k: {"stem": g[0], "branch": g[1], "ganzhi": g}
                             for k, g in zip(PILLAR_KEYS, gzs)},
                 "birth": {"gender": sex}}
        dy = dayun_table(chart)
        want = case["expected"]["dayun"]["运序"]
        got = [d["ganzhi"] for d in dy][:len(want)]
        if got == want:
            seq_ok += 1
        else:
            problems.append(f"{case['id']}：引擎排运 {got} 与书列 {want} 不符"
                            f"（性别取『{sex}』，顺逆取自 dayun_direction）")
        hits = dayun_ming_yindong(chart, dayun=dy or [{"ganzhi": g, "index": i + 1}
                                                      for i, g in enumerate(want)])
        kinds = {h["dayun"]: {r["kind"] for r in h["relations"]} for h in hits}
        for gz, exp in ENGINE_EXPECT.get(case["id"], {}).items():
            if not exp <= kinds.get(gz, set()):
                problems.append(f"{case['id']} 运{gz}：书明言之机制未出标签"
                                f"（期望 {sorted(exp)}，实得 {sorted(kinds.get(gz, set()))}）")
            else:
                mech_ok += 1
                for gz2, (val, rel) in ENGINE_REL.get(case["id"], {}).items():
                    if gz2 != gz:
                        continue
                    got2 = [(r.get("value"), r.get("shishen_rel"))
                            for h in hits if h["dayun"] == gz
                            for r in h["relations"] if r["kind"] == "xing_ru_mu"]
                    if got2 and got2 != [(val, rel)]:
                        problems.append(f"{case['id']} 运{gz}：入墓之神应为 {(val, rel)}，实得 {got2}")
                    elif got2:
                        mech_ok += 1
        for gz3, flag in GONG_ROSTER_EXPECT.get(case["id"], {}).items():
            got3 = [r.get("in_roster") for h in hits if h["dayun"] == gz3
                    for r in h["relations"] if r["kind"] == "zhi_tian_shi"]
            if not got3:
                problems.append(f"{case['id']} 运{gz3}: 应有填实标签以带 in_roster 分档，实得无")
            elif got3 != [flag]:
                problems.append(f"{case['id']} 运{gz3}: in_roster 应为 {flag}，实得 {got3}")
        for gz4, forb in ENGINE_FORBID.get(case["id"], {}).items():
            bad4 = sorted(forb & kinds.get(gz4, set()))
            if bad4:
                problems.append(f"{case['id']} 运{gz4}：裁定为不该出的标签仍出现 {bad4}"
                                "（落空破拱 ⇒ 无格可伤，守卫方向写反也会一路绿）")
        for want in SUI_EXPECT.get(case["id"], []):
            sui = liunian_ming_yindong(chart, liunian=[{"ganzhi": want["gz"], "year": 0, "age": 0}])
            got = {r["kind"]: (r.get("value"), r.get("shishen_rel"))
                   for h in sui for r in h.get("relations") or []}
            if want["kind"] not in got:
                problems.append(f"{case['id']} 岁{want['gz']}：岁支引动未出标签"
                                f"（期望 {want['kind']}，实得 {sorted(got)}）")
            elif got[want["kind"]] != (want["value"], want["rel"]):
                problems.append(f"{case['id']} 岁{want['gz']}：{want['kind']} 局/十神类不符"
                                f"（期望 {(want['value'], want['rel'])}，实得 {got[want['kind']]}）")
            else:
                mech_ok += 1
        # 行运成格变格裁决层回验（363 批）：见证集登记的「成格变格」期望须与引擎
        # judge_dayun_cheng_bai 输出一致；裁决类别由 dayun_ming_yindong 已回验的结构标签派生。
        cb = judge_dayun_cheng_bai(chart, dayun=dy, yindong=hits)
        cb_map = {c["dayun"]: set(c.get("verdict") or []) for c in cb}
        for exp in case["expected"]["dayun"].get("成格变格", []) or []:
            want_verdict += 1
            gz = exp.get("运")
            want_v = set(exp.get("裁决") or [])
            got_v = cb_map.get(gz, set())
            if not want_v <= got_v:
                problems.append(f"{case['id']} 运{gz}：成格变格裁决应为 {sorted(want_v)}，"
                                f"引擎得 {sorted(got_v)}（结构标签派生，须与书据机制一致）")
            else:
                verdict_ok += 1
    want_mech = sum(len(v) for v in ENGINE_EXPECT.values()) + sum(len(v) for v in SUI_EXPECT.values())
    if mech_ok < want_mech:
        problems.append(f"引擎回验命中机制数 {mech_ok} 低于登记值 {want_mech}，疑似负例失效")
    if verdict_ok < want_verdict:
        problems.append(f"成格变格裁决回验命中 {verdict_ok} 低于登记值 {want_verdict}，疑似负例失效")
    return seq_ok, mech_ok, verdict_ok


def validate(data: dict) -> tuple[list[str], list[str], int, int]:
    problems: list[str] = []
    notes: list[str] = []
    for case in data["cases"]:
        check(case, problems, notes)
    return problems, notes, len(data["cases"]), sum(len(c["expected"]["dayun"].get("书判", []))
                                                    for c in data["cases"])


def selftest() -> None:
    """负例自证：改一处假引文、改一处反方向运序、改一处性别依据，本器必须各自指名条目抓出。"""
    def _copy(doc: dict) -> dict:
        return json.loads(json.dumps(doc, ensure_ascii=False))

    data = json.loads(CASES.read_text(encoding="utf-8"))
    ids = [c["id"] for c in data["cases"]]
    if len(ids) < 5:
        raise AssertionError(f"负例自证需 ≥5 例，现 {len(ids)} 例——本器无从自证")
    first, fifth = ids[0], ids[4]

    def pick(doc: dict, cid: str) -> dict:
        return next(c for c in doc["cases"] if c["id"] == cid)

    bad = _copy(data)
    pick(bad, first)["source_quote"] += "绝无此语"
    p1, _, _, _ = validate(bad)
    assert any(first in x and "引文不在源行内" in x for x in p1), f"假引文未被抓：{p1}"

    bad = _copy(data)                                       # 方向翻面：运序与声明仍自洽，只书判运名露馅
    c = pick(bad, fifth)
    dy = c["expected"]["dayun"]
    m = c["pillars_raw"].split()[1]
    nd = "顺" if "逆行" in dy["排法"] else "逆"
    dy["排法"] = f"{'顺行' if nd == '顺' else '逆行'}（自月柱{m}）"
    dy["运序"] = dayun_seq(m, nd, len(dy["运序"]))
    p2, _, _, _ = validate(bad)
    assert any(fifth in x and "不在运序" in x for x in p2), f"方向翻面未被 ④ 抓出：{p2}"

    bad = _copy(data)
    pick(bad, fifth)["gender"] = "女（不论依据）"
    p3, _, _, _ = validate(bad)
    assert any(fifth in x and "性别依据" in x for x in p3), f"性别依据漂移未被抓：{p3}"

    pq: list[str] = []
    nq: list[str] = []
    qiyun_check(pq, nq, spec=[(308, "甲子", 5, "己巳", 150, 6, "初五",
                               ["乙丑", "丙寅", "丁卯", "戊辰", "己巳"], "丁卯")])
    assert any("起运L308" in x for x in pq), f"余日篡改未被三层抓出：{pq}"
    pq2: list[str] = []
    nq2: list[str] = []
    qiyun_check(pq2, nq2, spec=[(329, "甲子", 4, "戊辰", 190, 7, "廿五",
                                 ["乙丑", "丙寅", "丁卯", "戊子"], "乙丑")])
    assert any("起运L329" in x for x in pq2), f"运序断链未被三层抓出：{pq2}"
    keep = SUI_EXPECT["DY006"][0]["rel"]
    SUI_EXPECT["DY006"][0]["rel"] = "官杀"
    pq3: list[str] = []
    engine_check(data, pq3, [])
    SUI_EXPECT["DY006"][0]["rel"] = keep
    assert any("DY006" in x and "十神类不符" in x for x in pq3), f"岁层十神篡改未被抓：{pq3}"

    # 墓层必须真的接进了门：给一个「书未言且结构也不该出」的期望，必须被记为漏标
    ENGINE_EXPECT["DY001"] = dict(ENGINE_EXPECT.get("DY001", {}), **{"己未": {"zhi_tian_shi"}})
    pq4: list[str] = []
    engine_check(data, pq4, [])
    ENGINE_EXPECT["DY001"].pop("己未", None)
    assert any("DY001" in x and "未出标签" in x for x in pq4), f"墓层/门未接通而未被抓：{pq4}"

    # 反面判据（不该出的标签）这一半也必须证明自己在跑
    ENGINE_FORBID["DY012"] = {"辛卯": {"zhi_tian_shi"}}
    pq5: list[str] = []
    engine_check(data, pq5, [])
    ENGINE_FORBID.pop("DY012", None)
    assert any("DY012" in x and "不该出的标签仍出现" in x for x in pq5), f"反面判据空跑未被抓：{pq5}"

    # 裁决层空转防护：给见证集塞一条与引擎实际裁决不符的期望，必须被记作不符（门没白跑）
    bad = _copy(data)
    pick(bad, "DY007")["expected"]["dayun"]["成格变格"].append(
        {"运": "辛亥", "裁决": ["守局"]})   # 引擎实际为 成格引动，与「守局」不符
    pq6: list[str] = []
    engine_check(bad, pq6, [])
    assert any("DY007" in x and "成格变格裁决应为" in x for x in pq6), f"裁决层篡改未被抓：{pq6}"

    # ⑥ 主语料空档核验也必须证明自己在扫（365 批）：
    # 塞一条「书明写顺行 + 五岁起运」的假案例 → 必须判红并要求按书证回填；
    # 同一份假集合里登记表那 9 例一个都不在 → 必须另报一条登记漂移。
    fake = {"schema": "x", "cases": [
        {"id": "GAP1", "source_quote": "此造运行顺行，初运乙丑，五岁起运", "note": ""}]}
    pg: list[str] = []
    corpus_gap_check(fake, pg, [], engine_probe=False)
    assert any("必须按书证回填" in x for x in pg), f"书证出现而未被要求回填：{pg}"
    assert any("登记漂移" in x for x in pg), f"登记漂移未被抓：{pg}"

    print(f"SELFTEST OK：11 个负例全部被抓出（假引文／方向翻面／性别依据／余日篡改／运序断链／岁层十神／墓层未接必被记漏标／反面判据空跑必被抓／成格变格裁决篡改必被抓／主语料书证必被要求回填／近失登记漂移必被抓）"
          f" → 对象 {first}／{fifth}，月柱 {m}")


# ── 第四层：歲運論 五式的**书自己给的定义例**（373 批实现、374 批挂门）──────────────
# 为什么用定义例而不是命例：书里只有《歲運論》把「运与岁」的关系**命名**了（运伐岁／岁伐运／和／好），
# 而它给的全是定义例（「如丙運庚年，謂之運伐…」），不是命例。用定义例断言，判据是书的那句话，
# 期望不是我从实现里反推的——不循环。命例只能验吉凶（§2.2 判不可评），验不了结构名。
WUSHI_SPEC = [
    ("yun_fa_sui", "丙午", "庚午",
     "源L365「如丙運庚年，謂之運伐（剋）歲。」——运干丙剋岁干庚"),
    ("sui_fa_yun", "庚午", "丙午",
     "源L370「如庚運丙年，謂之歲伐（剋）運…」——岁干丙剋运干庚（与上条互为反面，方向写反必红）"),
    ("sui_yun_he_gan", "乙酉", "庚辰",
     "源L382「如乙運庚年，庚運乙年，則和（乙庚化金）…」——运干与岁干五合"),
    ("liuhe", "甲子", "乙丑",
     "源L383「如子運丑年，丑運子年，則和（子丑合而化土）…」——支六合（由既有 liuhe 承担）"),
    ("sui_yun_hao", "庚午", "辛未",
     "源L387「如庚運辛年，辛運庚年…則好。」——两干同类"),
    ("bihe", "甲申", "乙酉",
     "源L387「…申運酉年，酉運申年，則好。」——两支同类（由既有 bihe 承担）"),
]


def wushi_check(problems: list[str], notes: list[str], spec=None) -> int:
    """第四层：把《歲運論》自己给的六个定义例喂进引擎，看它出不出书上那个名。

    三条负例同处（§四.8）：
      ① 方向反面的那一对**不得**出正向名（丙運庚年 vs 庚運丙年——方向写反必红）；
      ② 同支（岁运并临）**不得**出三合/比和（373 批修的误标：两支且同支不是局）；
      ③ 空干支不得产出任何关系（不臆造）。
    """
    spec = WUSHI_SPEC if spec is None else spec
    from bazi_factors.dayun import dayun_liunian_interactions
    chart_stub = {"pillars": {"year": {"ganzhi": "甲子", "stem": "甲", "branch": "子"},
                              "month": {"ganzhi": "丙寅", "stem": "丙", "branch": "寅"},
                              "day": {"ganzhi": "甲子", "stem": "甲", "branch": "子"},
                              "hour": {"ganzhi": "甲子", "stem": "甲", "branch": "子"}}}

    def kinds(d_gz: str, y_gz: str) -> set:
        rows = dayun_liunian_interactions(chart_stub, dayun=[{"ganzhi": d_gz}],
                                          liunian=[{"ganzhi": y_gz}])
        out = set()
        for r in rows:
            for rel in r.get("relations") or []:
                if not rel.get("kind", "").startswith("ten_god"):
                    out.add(rel["kind"])
        return out

    ok = 0
    for kind, d_gz, y_gz, why in spec:
        ks = kinds(d_gz, y_gz)
        if kind in ks:
            ok += 1
        else:
            problems.append(f"歲運論五式未落实：运{d_gz}/年{y_gz} 应出 {kind}（{why}），实得 {sorted(ks)}")
    # 负例①：方向反面
    if "yun_fa_sui" in kinds("庚午", "丙午"):
        problems.append("负例①失效：庚運丙年 也出了 yun_fa_sui——剋的方向没区分")
    # 负例②：同支不得标三合/比和
    same = kinds("丁卯", "丁卯")
    if {"sanhe", "bihe"} & same:
        problems.append(f"负例②失效：岁运同支（丁卯/丁卯）仍标出 {sorted({'sanhe','bihe'} & same)}")
    # 负例③：空干支不得臆造
    if kinds("", ""):
        problems.append("负例③失效：空干支仍产出关系")
    notes.append(f"歲運論五式：{ok}/{len(spec)} 个书定义例出对了名；三条负例（方向反面/同支误标/空值臆造）已跑")
    return ok


# (源行, 起算年干支, 书给岁数, 书给交运年干支, 余日, 书给月, 书给日, 运序列举, 书给第一部运)
QIYUN_SPEC = [(308, "甲子", 5, "己巳", 140, 6, "初五", ["乙丑", "丙寅", "丁卯", "戊辰", "己巳"], "丁卯"),
              (329, "甲子", 4, "戊辰", 190, 7, "廿五", ["乙丑", "丙寅", "丁卯", "戊辰"], "乙丑")]


# ── 第五层：化格（《滴天髓·從化論》真/假两章）的**书定义例**（383 批）────────────
# 与岁运五式同法：用书自己给的定义例（「甲己化土生於四季」「丙辛生於冬月」……），
# 期望来自**书的那句话**，不是从实现反推，故不循环。书里没有化格命例的明确定性，
# 故本层只验「书的定义例」，命例留在 384 批以后按逐字取证另立。
# 每条 = (说明, 年月日时四柱, 期望类型, 书证)
HUA_SPEC = [
    ("甲己化土・辰月・月干作合", ("丙午", "己辰", "甲子", "丁酉"), "真化",
     "《從化論－真》「如甲日主，生於四季，單遇一位己土，在月時上作合…乃為化得真」"),
    ("乙庚化金・酉月・月干作合", ("丙丑", "庚酉", "乙子", "丁戌"), "真化",
     "《從化論－真》「乙庚生於秋月…獨相作合，皆為真化」"),
    ("丙辛化水・亥月・月干作合", ("戊辰", "辛亥", "丙戌", "己丑"), "真化",
     "《從化論－真》「丙辛生於冬月…（化神要通月令）…皆為真化」"),
    ("丁壬化木・寅月・月干作合", ("戊丑", "壬寅", "丁戌", "庚酉"), "真化",
     "《從化論－真》「丁壬生於春月…皆為真化」"),
    ("戊癸化火・午月・月干作合", ("辛寅", "癸午", "戊亥", "庚酉"), "真化",
     "《從化論－真》「戊癸生於夏月…皆為真化」"),
    ("化神不得月令则不真", ("丙寅", "己申", "甲子", "丁酉"), "假化",
     "化神土不生於申月（非四季），《從化論》「化神要通月令」"),
    ("日主有本气根则不真", ("丙午", "己辰", "甲子", "丁寅"), "假化",
     "日主甲得寅中本气甲为根，《從化論》「日主孤弱無氣…絕無一毫生扶之意」"),
    ("遇印劫之干则不真", ("乙午", "己辰", "甲子", "丁酉"), "假化",
     "乙为甲之劫，《從化論》「不遇壬癸甲乙庚（印，劫，官）」"),
    ("遇官杀之干则不真", ("庚午", "己辰", "甲子", "丁酉"), "假化",
     "庚为甲之官，《從化論》「不遇…庚（印，劫，官）」（庚能剋甲）"),
    ("年干作合不作数", ("己丑", "甲辰", "甲子", "丁酉"), "不化",
     "《從化論－真》「在月時上作合，（在年幹不是）」——合在年干不算化"),
]


def hua_check(problems: list[str], notes: list[str], spec=None) -> int:
    """第五层：化格的书定义例。期望＝书那句定义例，不是实现反推（§三.4 不循环）。"""
    spec = HUA_SPEC if spec is None else spec
    from bazi_factors.congrge import hua_judge
    from yishu_core.ming_tables import CANG_GAN

    def build(cols) -> dict:
        ps = {}
        factors = {}
        for key, gz in zip(("year", "month", "day", "hour"), cols):
            ps[key] = {"stem": gz[0], "branch": gz[1]}
            factors[key] = {"hidden_stems": list(CANG_GAN.get(gz[1], []))}
        return {"pillars": ps, "factors": factors}

    ok = 0
    for name, cols, want, why in spec:
        r = hua_judge(build(cols))
        got = r.get("type") or "不化"
        if got == want:
            ok += 1
        else:
            problems.append(f"化格定义例未落实：{name} 应为 {want}（{why}），实得 {got}"
                            f"（{r.get('reason')}）")
    notes.append(f"化格定义例：{ok}/{len(spec)} 条出对名（真化5／假化4／不化1）；"
                 f"判据四条见《從化論》——合在月時、化神通月令、日主无生扶无本气根、不遇印劫官")
    return ok


# ── 第六层：化格**命例**见证集（384 批）────────────────────────────────────
# 前五层证的是「书的定义例」；这一层证的是「书自己的命例」——判据在命例上是否也成立。
# 读数从实测起步（只准前进）：HUA_CASE_FLOOR 是 384 批实测的命中数，不是拍出来的目标。
HUA_CASE_FILE = ROOT / "data" / "cases" / "bazi_hua_cases.json"
HUA_CASE_FLOOR = 3          # 384 批实测 3/10（真化5／假化4／不化1 全在）
HUA_CASE_NOTE = (
    "384 批实测 3/10：书证到齐前的第一把尺子。七处失配已逐条定性（见 CHANGELOG 384），"
    "根因是判据把书的**程度语**当成了**硬否决**（「化神要通月令」「不遇印劫官」），"
    "而命例里这些条件常以「泄气不足」「虽时逢禄印」「嫌其时透壬水克丙」等**程度/提醒**出现；"
    "重写判据是下一批的活。")


def hua_case_check(problems: list[str], notes: list[str]) -> tuple[int, int]:
    """第六层：化格命例回验。命中数 ≥ HUA_CASE_FLOOR 才算过；未命中的逐条打印（欠账可见）。"""
    from bazi_factors.congrge import hua_judge
    from yishu_core.ming_tables import CANG_GAN

    if not HUA_CASE_FILE.is_file():
        problems.append(f"化格命例见证集不存在 {HUA_CASE_FILE.name}")
        return 0, 0
    doc = json.loads(HUA_CASE_FILE.read_text(encoding="utf-8"))
    cases = doc.get("cases") or []

    def build(pill) -> dict:
        ps = {}
        factors = {}
        for key, gz in zip(("year", "month", "day", "hour"),
                           (pill["year"], pill["month"], pill["day"], pill["hour"])):
            ps[key] = {"stem": gz[0], "branch": gz[1]}
            factors[key] = {"hidden_stems": list(CANG_GAN.get(gz[1], []))}
        return {"pillars": ps, "factors": factors}

    ok = 0
    miss = []
    for c in cases:
        want = ((c.get("expected") or {}).get("hua_type")) or ""
        r = hua_judge(build(c["pillars"]))
        got = r.get("type") or "不化"
        if got == want:
            ok += 1
        else:
            miss.append((c["id"], c["location"], want, got, r.get("reason") or "",
                         (c.get("source_quote") or "")[:60]))
    if ok < HUA_CASE_FLOOR:
        problems.append(f"化格命例命中 {ok}/{len(cases)} 低于登记下限 {HUA_CASE_FLOOR}")
    notes.append(f"化格命例：{ok}/{len(cases)} 命中（下限 {HUA_CASE_FLOOR}）；"
                 f"未命中 {len(miss)} 条逐条列在下方——这是欠账，不是通过")
    print(f"  化格命例见证：{ok}/{len(cases)} 命中（下限 {HUA_CASE_FLOOR}）")
    for mid, loc, want, got, why, quote in miss:
        print(f"    · {mid} {loc}：期望 {want}，实得 {got}（{why}）")
        print(f"        书：{quote}")
    if miss:
        print(f"    → {HUA_CASE_NOTE}")
    return ok, len(cases)


def qiyun_check(problems: list[str], notes: list[str], spec=None) -> int:
    """第三层：起运算术自检（#31④）。《千里明镜》源L308／L329 是**自足的算例**
    （给了起算日、岁数、余日、交运日期与运序列举），故无需节气即可回验我们的历算口径。
    只验「干支序差＝岁数」「30 日成月的余日投射」「运序依六十甲子连续」三点，
    **不**把书的『再加 N 天』当作本仓 start_age 的同量（本仓以「距节气日数÷3」折岁，是另一件事）。
    """
    f = ROOT / "data" / "sources" / "qianli_minggao_dz.dz.txt"
    if not f.exists():
        problems.append("起运算术自检：底本 qianli_minggao_dz.dz.txt 不存在")
        return 0
    lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
    ok = 0
    spec = spec or QIYUN_SPEC
    CN = {"初一": 1, "初二": 2, "初三": 3, "初四": 4, "初五": 5, "甘五": 25, "廿五": 25}
    for ln, y0, age, y1, rem, mon, days_s, seq, first in spec:
        text = norm(lines[ln - 1])
        gz0, gz1 = gz_index(y0), gz_index(y1)
        if gz0 < 0 or gz1 < 0:
            problems.append(f"起运L{ln}：干支不合法")
            continue
        if (gz1 - gz0) % 60 != age:
            problems.append(f"起运L{ln}：书称{age}岁足，而{y0}→{y1} 干支序差 {(gz1-gz0)%60}")
            continue
        if any(gz_index(b) - gz_index(seq[0]) != i for i, b in enumerate(seq)):
            problems.append(f"起运L{ln}：运序列举不合六十甲子连续序")
            continue
        if first not in seq:
            problems.append(f"起运L{ln}：书给第一部运 {first} 不在列举 {seq} 之内")
            continue
        tot = 15 + rem                      # 正月十五日起算（书以 30 日为一月）
        m = (tot - 1) // 30 + 1
        d = (tot - 1) % 30 + 1
        if (m, d) != (mon, CN.get(days_s, -1)):
            problems.append(f"起运L{ln}：再加{rem}天 应投射为 {mon}月{days_s}，按 30 日成月算得 {m}月{d}")
            continue
        if f"{y1}年" not in text:
            problems.append(f"起运L{ln}：源行未出现交运年『{y1}年』（本器按字面回验）")
            continue
        ok += 1
    sys.path.insert(0, str(ROOT / "scripts"))
    from bazi_factors import _common as C
    if int(C.DAYS_PER_LUCK_YEAR) != 3:
        problems.append(f"起运折算常数 DAYS_PER_LUCK_YEAR={C.DAYS_PER_LUCK_YEAR}，"
                        "书『折除三日为一岁』（《神峰通考》源L2608）")
    if int(C.MONTHS_PER_DAY) != 4:
        problems.append(f"起运余日折算 MONTHS_PER_DAY={C.MONTHS_PER_DAY}，应为 1 日＝4 月")
    notes.append("起运算术：只验干支序差／运序连续／30 日成月余日投射；"
                 "本仓 start_age 走「距节气日数÷3」，与书之『再加N天』非同量，未作互等断言")
    return ok


# ── ⑥ 主评分语料「行运可评量」空档核验（第三百六十五批）────────────────────
# 归在本器而非另立一门：全库只有本器认得「运层书证长什么样」，而要判的正是「主语料里
# 有没有这种书证」——判据同源，故同门（§四.8 一门一判据）。
#
# 要关的欠账：运层进对齐分的前置是「主评分语料带行运键」，实测 0/338。但「0」自己说不清
# 两件事：是书真没写、还是扫描漏了；以及将来会不会有人无书证地把它补上，凭空长出一个
# 恒真的 100% 维度。本段把两件事都变成可重跑的读数（理据与量级见 EVAL-PLAN §五 末注）：
#   ① 决定性语汇（命例级顺逆、起运岁数）在 338 例全文 **0 命中** ⇒ 回填无书证来源；
#   ② 广义「运」字 9 命中，逐例登记语境（调候正文／吉凶断语，无干支、无岁数）；
#   ③ 四柱-only 例的引擎起运值**全部相同** ⇒ 占位常数、不含命例信息 ⇒ 起运对该类不可评。
# 将来新收案例若书文真写了顺逆/起运，①立刻判红并要求回填——空档是被监控的边界，
# 不是永久豁免（同 check.py 的 UNWIRED_CORPORA「接上了反而判红」范式）。
MAIN_CASES = ROOT / "data" / "cases" / "bazi_classical_cases.json"

DECISIVE_YUN = {
    "顺逆": re.compile(r"顺行|逆行|顺排|逆排|顺布|逆布"),
    "起交运": re.compile(r"起运|交运"),
    "岁数运": re.compile(r"[0-9一二三四五六七八九十百]+岁.{0,4}(行|起|上|交)运"),
}

# 近失语汇（广义「运」字）：逐例登记语境。机器只比 ID 集合（多一例少一例都判红），
# 说明只给人看——「这一例为什么不算书证」必须写下来，否则下一个人还得重新怀疑这个 0。
YUN_NEAR_MISS = {
    "MP064": "「庚运夺魁」——行运吉凶断语，无干支、无岁数",
    "MT011": "「但要运用相生」——「运用」是常语，非大运",
    "MT019": "「须要大运相扶」——泛论，无干支",
    "MT023": "「要运行北地为隹」——只言方位",
    "MT034": "「即运行西北，亦不死也」——只言方位",
    "MT045": "「运入火乡，亦主显达」——只言方位",
    "MT497": "「运不行北，困苦一生」——只言方位",
    "ZC012": "「运根拔尽」——《滴天髓》从杀章断语，无干支",
    "ZP003": "徐注「运上败中有成」——转述，无干支",
}


def corpus_gap_check(store: dict, problems: list[str], notes: list[str],
                     engine_probe: bool = True) -> tuple[int, int]:
    """主语料空档核验。返回 (决定性语汇命中例数, 四柱-only 起运唯一值个数)。

    两者都应当是 (0, 1)：前者 = 无书证可回填；后者 = 起运对该类案例只是占位常数。
    判红即表示口径须重判，不得「看着不习惯就改回绿」。
    """
    cases = store.get("cases") or []
    if not cases:
        problems.append("主语料 0 例——行运空档核验无从谈起（不得当作已验）")
        return 0, 0

    decisive: list[str] = []
    near: list[str] = []
    for c in cases:
        cid = c.get("id") or "?"
        blob = " ".join(str(c.get(k) or "") for k in ("source_quote", "note", "location"))
        for name, pat in DECISIVE_YUN.items():
            found = pat.findall(blob)
            if found:
                decisive.append(f"{cid}（{name}：{'/'.join(sorted(set(found)))}）")
        if "运" in blob:
            near.append(cid)

    if decisive:
        problems.append(
            f"主语料出现命例级行运书证 {len(decisive)} 例：" + "、".join(decisive)
            + "——书已经把顺逆/起运写出来了，必须按书证回填 expected.dayun_direction／"
              "expected.dayun_start_age 后重跑（AGENTS.md §三.4：回填须有书证，不得由引擎反推）")

    got, want = set(near), set(YUN_NEAR_MISS)
    if got - want:
        problems.append("主语料新增「运」字案例而未登记语境（先判定是不是书证，再登记本表）："
                        + "、".join(sorted(got - want)))
    if want - got:
        problems.append("登记表里的「运」字案例已不在主语料（登记漂移，须同批同步）："
                        + "、".join(sorted(want - got)))

    ph: set = set()
    if engine_probe:
        sys.path.insert(0, str(ROOT / "scripts"))
        sys.path.insert(0, str(ROOT / "core"))
        try:
            import analyze as analyze_mod
            import chart as chart_mod
        except Exception as e:                       # 引擎起不来如实登记，不当已验
            problems.append(f"起运占位核验起不来（import 失败）：{e}")
            return len(decisive), 0
        for c in cases:
            p = c.get("pillars") or {}
            if p.get("datetime"):
                continue
            gz = {k: p.get(k) for k in PILLAR_KEYS}
            if not all(gz.values()):
                continue
            try:
                ch = chart_mod.chart_from_pillars(gz, gender=c.get("gender") or "男")
                an = analyze_mod.analyze(ch)
            except Exception as e:                   # 单例异常不拖垮整门，但要留名
                notes.append(f"{c.get('id')}：起运占位核验跳过（{type(e).__name__}）")
                continue
            dy = an.get("dayun") or []
            ph.add(dy[0].get("start_age") if dy else None)
        if len(ph) > 1:
            problems.append(
                f"四柱-only 案例的起运值出现 {len(ph)} 个不同取值 {sorted(ph, key=str)}——"
                "起运不再是占位常数，说明引擎已能对四柱-only 案例真算起运；"
                "「起运子项对该类不可评」这条口径须重判，并检查 [25] 是否该解锁")
        elif not ph:
            notes.append("主语料无四柱-only 案例，起运占位核验本条不适用")
    return len(decisive), len(ph)


def main() -> int:
    if not CASES.exists():
        print(f"FAIL：见证集不存在 {CASES}")
        return 1
    data = json.loads(CASES.read_text(encoding="utf-8"))
    problems, notes, n, nseg = validate(data)
    if n == 0:
        print("FAIL：见证集一条案例都没有（本器一行都没检视，不得当作已验）")
        return 1
    seq_ok, mech_ok, verdict_ok = engine_check(data, problems, notes)
    qy = qiyun_check(problems, notes)
    ws = wushi_check(problems, notes)
    hs = hua_check(problems, notes)
    hcs, hcn = hua_case_check(problems, notes)
    gap_n, gap_ph = 0, 0
    n_main = 0
    if MAIN_CASES.is_file():
        main_store = json.loads(MAIN_CASES.read_text(encoding="utf-8"))
        n_main = len(main_store.get("cases") or [])
        gap_n, gap_ph = corpus_gap_check(main_store, problems, notes)
    else:
        problems.append(f"主语料不存在 {MAIN_CASES.name}——行运空档核验无从谈起")
    print(f"行运见证集：{n} 例／{nseg} 段书判 已回底本逐字＋五虎遁＋运序连续＋方向唯一 自检")
    print(f"引擎二层：{seq_ok}/{n} 例引擎排运与书一致；{mech_ok} 处书明言机制已出引动标签；"
          f"{verdict_ok} 处成格变格裁决与见证集一致")
    print(f"运岁四层：{ws}/{len(WUSHI_SPEC)} 个《歲運論》定义例出对名（運伐歲／歲伐運／和／好；"
          "三条负例：方向反面／同支误标／空值臆造）")
    print(f"化格五层：{hs}/{len(HUA_SPEC)} 个《從化論》定义例出对名（真化／假化／不化）")
    print(f"化格六层（命例）：{hcs}/{hcn} 命中，详见下方逐条")
    print(f"起运三层：{qy}/{len(QIYUN_SPEC)} 条《千里明镜》算例回验通过"
          "（干支序差＝岁数／运序合六十甲子／30 日成月余日投射）")
    print(f"主语料空档：{n_main} 例全文扫描 → 命例级顺逆/起运书证 {gap_n} 例（须 0）；"
          f"广义「运」字 {len(YUN_NEAR_MISS)} 例逐例登记语境；"
          f"四柱-only 起运取值 {gap_ph} 个（须 1＝占位常数，故起运对该类不可评）")
    for x in notes:
        print(f"NOTE  {x}")
    rc = 0
    if problems:
        print(f"FAIL：{len(problems)} 项")
        for x in problems:
            print("  " + x)
        rc = 1
    else:
        print("校验不过项: 无（引文/断语/两遁/运序/方向唯一/性别 全部自洽）")
    _ap = argparse.ArgumentParser(description="check_dayun_cases：--selftest 负例自证开关（§三）")
    _ap.add_argument("--selftest", action="store_true", help="负例自证")
    args = _ap.parse_args()
    if args.selftest:
        try:
            selftest()
        except AssertionError as e:
            print(f"FAIL SELFTEST：{e}")
            rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
