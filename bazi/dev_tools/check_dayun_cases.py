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

用法：
    python dev_tools/check_dayun_cases.py            # 回验，有问题退码 1
    python dev_tools/check_dayun_cases.py --selftest # 负例自证：造假引文／反方向运序必须被抓
"""
from __future__ import annotations

import json
import re
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
        from bazi_factors.dayun import dayun_ming_yindong, dayun_table, liunian_ming_yindong
    except Exception as e:
        problems.append(f"引擎回验起不来（import 失败）：{e}")
        return 0, 0
    seq_ok = mech_ok = 0
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
    want_mech = sum(len(v) for v in ENGINE_EXPECT.values()) + sum(len(v) for v in SUI_EXPECT.values())
    if mech_ok < want_mech:
        problems.append(f"引擎回验命中机制数 {mech_ok} 低于登记值 {want_mech}，疑似负例失效")
    return seq_ok, mech_ok


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
    print(f"SELFTEST OK：8 个负例全部被抓出（假引文／方向翻面／性别依据／余日篡改／运序断链／岁层十神／墓层未接必被记漏标／反面判据空跑必被抓）"
          f" → 对象 {first}／{fifth}，月柱 {m}")


# (源行, 起算年干支, 书给岁数, 书给交运年干支, 余日, 书给月, 书给日, 运序列举, 书给第一部运)
QIYUN_SPEC = [(308, "甲子", 5, "己巳", 140, 6, "初五", ["乙丑", "丙寅", "丁卯", "戊辰", "己巳"], "丁卯"),
              (329, "甲子", 4, "戊辰", 190, 7, "廿五", ["乙丑", "丙寅", "丁卯", "戊辰"], "乙丑")]


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


def main() -> int:
    if not CASES.exists():
        print(f"FAIL：见证集不存在 {CASES}")
        return 1
    data = json.loads(CASES.read_text(encoding="utf-8"))
    problems, notes, n, nseg = validate(data)
    if n == 0:
        print("FAIL：见证集一条案例都没有（本器一行都没检视，不得当作已验）")
        return 1
    seq_ok, mech_ok = engine_check(data, problems, notes)
    qy = qiyun_check(problems, notes)
    print(f"行运见证集：{n} 例／{nseg} 段书判 已回底本逐字＋五虎遁＋运序连续＋方向唯一 自检")
    print(f"引擎二层：{seq_ok}/{n} 例引擎排运与书一致；{mech_ok} 处书明言机制已出引动标签")
    print(f"起运三层：{qy}/{len(QIYUN_SPEC)} 条《千里明镜》算例回验通过"
          "（干支序差＝岁数／运序合六十甲子／30 日成月余日投射）")
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
    if "--selftest" in sys.argv:
        try:
            selftest()
        except AssertionError as e:
            print(f"FAIL SELFTEST：{e}")
            rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
