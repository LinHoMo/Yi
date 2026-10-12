# -*- coding: utf-8 -*-
"""从《增删卜易》殆知阁转录本（data/sources/zengshan_buyi_dz.dz.txt）抽取带明确应期的占验案例，
建成**永不参与调参**的外部验证集 `zengshan_dz_holdout`。

    python dev_tools/build_zengshan_dz_cases.py [--dry-run]

为什么另立一个抽取器（第一百五十五批）：batch-154 实测证明应期语料的材料一直在库里——
底本 161743 字里「日柱＋应期锚＋可解析卦名」三备段有 25 处，瓶颈是既有抽取器
（build_yingqi_set.py）读的是 references/case_library.md，不是底本本身。

dz 本案例形态（与维基文库本不同，逐字示例）：
    例：酉月辛亥日
    占求财得兑为泽卦变雷水解卦
    父母未土″世              父母戌土″
    兄弟酉金′    动          兄弟申金″应
    …（六爻渲染，动爻带「动」字）…
    断曰：寅日得见财，亦如心。……果于寅日早见木日得财。

七道门（任一门不过即 excluded，写明原因，绝不放宽）：
  1. 本卦名可解析（全名→内核短名；转录讹字按登记表归一，假设由门 2 验证；
     「得X化Y」「得XY」两种无变/之连接字的卦变形态先拆后解，防后缀匹配丢本卦）
  2. 卦变自洽：渲染里「动」标记的爻位 ≡ 本卦⊕变卦 的差集（无变卦时以标记/静卦计）
  3. 时间可还原：案例块前一条**完整**日期行（月建＋日柱）紧邻本案例
     （中间不得插入别的案例；标题前 10 字内出现只记支的弱日期行 ⇒ 真实日期行
      就是它，segment 配到的远处完整日期属于别案，不收——ZD019/ZD066 实测）
  4. 断语段有占验实录句（结果标记＋日期令牌），且令牌不宽于三支
  5. 令牌只取实录：预测句、或曰假设段、「X年占」占测年、占测日自重，一律不计
     （自重豁免只认 果/竟/卒 强标记；「应卯时者…辰日相合」形的应=解释，不是应验）
  6. 不与在册案例同案（同卦变＋月建＋日柱，或同卦变＋应期支＋占题）——转录差异不补
  7. 吉凶判不出记空串（N/A 不进分母），不整例剔除（与维基文库集同口径）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

# 控制台编码守卫：GBK/cp936 控制台下本器的中文输出会退化成乱码甚至 UnicodeEncodeError
# （rc 仍为 0、金标准看不见，只有这条守卫管得住）。判据见 dev_tools/check.py 的编码不变式。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
from kernel_path import kernel_dir  # noqa: E402

sys.path.insert(0, str(kernel_dir(__file__)))

from yishu_core.symbols import (  # noqa: E402
    BAGUA_LINES,
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
    HEXAGRAM_TRIGRAMS,
)

SRC = HERE.parent / "data" / "sources" / "zengshan_buyi_dz.dz.txt"
OUT = HERE.parent / "data" / "cases" / "zengshan_dz_cases.json"
SPLITS = HERE.parent / "data" / "cases" / "case_splits.json"
REPORT = HERE.parent / "docs" / "CASE-LIBRARY-AUDIT.md"
CASES_GLOB = (HERE.parent / "data" / "cases").glob("*_cases.json")

STEMS = "".join(HEAVENLY_STEMS)
# dz 转录本把日干「己」写作「已」（曾於午月**已**卯日）——已知转录混淆，抽取时归一并登记
STEMS_SRC = STEMS + "已"
BRANCHES = "".join(EARTHLY_BRANCHES)

# 案例标题：占<题>[，]得<卦>[变<卦>|之<卦>][卦]。
# 卦名段**不含**「变之」但**含**「卦」（尾卦由 strip 处理）——早期版把「卦」排除在卦名段外，
# 懒惰匹配＋可选「变」组会把「得离卦变火山旅」截成「得离卦」（变卦整段丢失，ZD017 实测）。
HEX = r"[^\n。；：，、变之\s]{1,6}"
CASE_RE = re.compile(
    r"占([^\n。；：，、变之卦得]{2,24}?)[，,]?得(%s)(?:(?:变(%s))|之(%s))?" % (HEX, HEX, HEX))
# 日期行：前缀不限（例：/又如：/如/曾於/即如…）；日字可省（「申月癸巳占父外任」）；
# 须月建＋日柱俱全（日柱＝干＋支）。弱日期（只记支不记干）另有守卫，见 segment()。
DATE_RE = re.compile(r"([%s])月([%s])([%s])日?" % (BRANCHES, STEMS_SRC, BRANCHES))
# 弱日期行：只记月建＋日支（「巳月亥日」「巳月未日」）——不满足门 3 的完整日期要求。
# 若它紧邻案例标题（≤10 字内），说明本案真实日期行就是它，segment 配到的远处完整
# 日期属于别案（ZD019 配到申月戊午日、ZD066 配到丑月壬子日，实测均张冠李戴）。
WEAK_DATE_RE = re.compile(r"([%s])月([%s])日" % (BRANCHES, BRANCHES))
# 渲染行：六神名开头，或 六亲＋地支＋五行＋阴阳符（父母未土″）的本卦列
SIX_SPIRIT_RE = re.compile(r"[元玄武朱雀青龙白虎勾陈滕蛇]")
YIN_YANG_RE = re.compile(r"[%s][金木水火土][′″]" % BRANCHES)
# 章标题行（断语搜索的止界：「……章第十八」类；不停止就会读进下一章的理论文本，
# 把别案的占验实录当成本案锚句——ZD027 实测）
CHAPTER_RE = re.compile(r"^[^\n。；：]{2,15}章第?[一二三四五六七八九十百]+$")

GOOD_WORDS = ("愈", "成", "得", "吉", "生", "安", "泰", "喜", "起", "复", "治", "救",
              "归", "还", "利", "旺", "顺", "遂", "免", "登", "荣",
              "显", "升", "平安", "无碍", "有效", "富贵", "兴旺", "相生")
# 「中」「见」二字歧义实测误判：ZD016「动于卦**中**」、ZD102「**中**秋有雨」把天气占读成吉；
# ZD065「还**见**凶灾」、ZD151「八九月必**见**」把凶案读成吉（必见=灾祸将现）。
# 「发」是六爻技术词（爻发动）：ZD102「辰父**发**动」把天气占读成吉，同去。
# 「许」是预测词（许之可治／当许有雨）：ZD023「许之可治…后死于寅日」同型误判的根源，
# ZD102「当**许**中秋有雨」实测把天气占读成吉，同去。
# 只收**结果词**；技术词（月破/逢伤/化进/化退/回头克/旬空）不是结果，
# 收进来会把「许之可治…后死于寅日」同型的案子误判（ZD023 实测去伤、ZD009 实测去破）。
BAD_WORDS = ("死", "亡", "凶", "刑", "害", "败", "失", "盗", "疾", "灾", "祸",
             "丧", "忧", "亏", "损", "累", "殃", "遭", "卒", "危", "沉",
             "哭", "讼", "狱", "下狱", "重刑", "不吉", "无望", "不利", "悔",
             "艰")   # 丁艰＝遭父母丧（ZD151）

# 月序 → 月建（正月寅起，标准月建表；「应六月者」= 未月）。只用于应期记法
MONTH_ORDER_BRANCH = {"正": "寅", "一": "寅", "二": "卯", "三": "辰", "四": "巳",
                      "五": "午", "六": "未", "七": "申", "八": "酉", "九": "戌",
                      "十": "亥", "十一": "子", "十二": "丑", "冬": "子", "腊": "丑"}
# 结果标记（已实现）：占验实录句的起句词
REALIZED_RE = re.compile(r"[果竟卒后应]")
# 强实现标记：占测日自重令牌的豁免只认这三个弱不行——
# ZD018「**应**卯时者，酉金与辰日相合」、ZD027「**应**临戌父，巳月生之」、
# ZD088「**应**辰时者，戌日冲辰父」都是"解释为何应某时辰"的句式，
# 被豁免的辰日/巳月/戌日全是占测日本身，不是应期（三例实测漏收）。
STRONG_REALIZED_RE = re.compile(r"[果竟卒]")
OUTCOME_RE = re.compile(r"[果应验竟卒后至待许]")
# 应期令牌四种记法（《增删卜易》实测都存在）
YQ_TOKEN_RE = re.compile(r"([%s])(日|月|年)" % BRANCHES)
YQ_FULL_DAY_RE = re.compile(r"([%s])([%s])日" % (STEMS_SRC, BRANCHES))
YQ_IMPLIED_DAY_RE = re.compile(r"(?:果于|得于|应于|至)([%s])([%s])(?![日月年])" % (STEMS_SRC, BRANCHES))
YQ_MONTH_ORDER_RE = re.compile(r"([正一二三四五六七八九十十一十二]|[冬腊])月")

# 六亲简称 → 全称（dz 渲染写「财爻」「子水」「父动」，期望值要全称）
REL_SHORTHAND = {"财": "妻财", "子": "子孙", "父": "父母", "兄": "兄弟",
                 "官": "官鬼", "鬼": "官鬼"}

# ────────────────────────── 卦名解析 ──────────────────────────

TRIGRAM_IMAGE = {"天": "乾", "地": "坤", "雷": "震", "风": "巽",
                 "水": "坎", "火": "离", "山": "艮", "泽": "兑"}

# dz 转录本卦名讹字登记表：写出的名字不在六十四卦内、而另一卦名仅差一字且读音相近。
# 这些归一是**假设**——门 2「卦变自洽」会验证它：猜错的门上必然对不上，案例照样剔除。
# 每个条目在案例 provenance 里留痕。
HEX_NAME_VARIANTS = {"暌": "睽", "即济": "既济", "骞": "蹇", "覆": "履", "逐": "遁"}


def apply_hex_variants(raw: str) -> tuple[str, bool]:
    """转录讹字归一；返回 (归一后名, 是否发生过归一)。"""
    mapped = HEX_NAME_VARIANTS.get(raw, raw)
    return mapped, mapped != raw


def strip_tail_gua(name: str) -> str:
    """去掉卦名段尾部的「卦」字（「火山旅卦」→「火山旅」）。"""
    return name[:-1] if len(name) > 1 and name.endswith("卦") else name


def split_concat_names(raw: str) -> tuple[str, str] | None:
    """「明夷小过」形：两个合法卦名连写、无连接字（ZD022 实测：原文「得明夷小过」，
    本卦明夷变卦小过；直接按整串解析会被后缀匹配静悄悄读成单卦「小过」，本卦整段丢失）。
    两段都须是内核短名；找不到唯一拆分返回 None（交回常规解析）。
    """
    for cut in range(2, len(raw) - 1):
        a, b = raw[:cut], raw[cut:]
        if a in HEXAGRAM_TRIGRAMS and b in HEXAGRAM_TRIGRAMS:
            return a, b
    return None


def resolve_hex_name(raw: str) -> tuple[str | None, str]:
    """全名（兑为泽/雷水解/山地剥）→ 内核短名。

    返回 (卦名, 存疑说明)。说明非空分两种：
      ·「前缀顺序按 X 反查得 Y」——书把上下卦序写反（火天同人＝天火同人），
        卦体集合相符，**可用**（调用方登记后放行）；
      ·「与卦体 … 不符」／「不可解析」——真存疑，调用方须剔除。
    """
    if not raw:
        return None, "未记卦名"
    if raw in HEXAGRAM_TRIGRAMS:
        return raw, ""
    m = re.match(r"^(.)(为)(.)$", raw)              # 乾为天 / 坤为地 / 震为雷
    if m and m.group(1) in BAGUA_LINES:
        return m.group(1), ""
    for L in (3, 2, 1):
        cand = raw[-L:]
        if cand in HEXAGRAM_TRIGRAMS:
            prefix = raw[:-L]
            note = ""
            if len(prefix) == 2:
                up = TRIGRAM_IMAGE.get(prefix[0])
                lo = TRIGRAM_IMAGE.get(prefix[1])
                if up and lo:
                    if HEXAGRAM_TRIGRAMS[cand] == (up, lo):
                        pass
                    elif HEXAGRAM_TRIGRAMS[cand] == (lo, up):
                        note = f"前缀顺序按 {prefix} 反查得 {cand}"
                    else:
                        return cand, f"全名前缀 {prefix} 与卦体 {HEXAGRAM_TRIGRAMS[cand]} 不符"
            return cand, note
    return None, f"卦名不可解析（{raw}）"


def hex_lines(name: str) -> list[int] | None:
    tri = HEXAGRAM_TRIGRAMS.get(name)
    if not tri:
        return None
    upper, lower = tri
    return BAGUA_LINES[lower] + BAGUA_LINES[upper]


def moving_from_diff(base: list[int], chg: list[int]) -> list[int]:
    return [i + 1 for i, (x, y) in enumerate(zip(base, chg)) if x != y]


def render_moving_positions(render: str) -> set[int]:
    """渲染文本（本卦六行）中标记「动」的爻位次（自上而下第 n 行 = 第 7-n 爻）。"""
    rows = [ln for ln in render.splitlines() if YIN_YANG_RE.search(ln)]
    pos: set[int] = set()
    for i, ln in enumerate(rows[:6]):
        if "动" in ln:
            pos.add(6 - i)
    return pos


def has_render(block_text: str) -> bool:
    """真案例门：块内须有六爻渲染（≥3 行六神开头，或 ≥4 行干支＋阴阳符）。

    「占求财，得困之坎，主亥日得财，余仿此」这类**规则陈述**没有渲染，
    不加这道门就会把书中假设例当占验案例收进来——那是给自己打假分。
    """
    rows = block_text.splitlines()[:14]
    spirit_rows = sum(1 for ln in rows if SIX_SPIRIT_RE.search(ln))
    yinyang_rows = sum(1 for ln in rows if YIN_YANG_RE.search(ln))
    return spirit_rows >= 3 or yinyang_rows >= 4


def _date_tokens(s: str) -> list[tuple[str, str, int]]:
    """从一个句子里抽应期令牌 [(支, 单位, 位置)]。

    四种记法都收（《增删卜易》实测都存在）：
      ① 支＋日/月/年            —— 「果于寅日」「应卯年」
      ② 全日干支＋日            —— 「至戊申日」「果得见于丙子日」
      ③ 果于|得于|应于|至＋全日干支（单位隐含为日）—— 「果于甲寅得之」
      ④ 月序＋月（正月寅起标准月建表）—— 「应六月者」「八月伙计盗尽」
    """
    seen: dict[tuple[str, str], int] = {}

    def put(b: str, u: str, pos: int) -> None:
        seen.setdefault((b, u), pos)

    for m in YQ_TOKEN_RE.finditer(s):
        put(m.group(1), m.group(2), m.start())
    for m in YQ_FULL_DAY_RE.finditer(s):
        put(m.group(2), "日", m.start())
    for m in YQ_IMPLIED_DAY_RE.finditer(s):
        put(m.group(2), "日", m.start())
    for m in YQ_MONTH_ORDER_RE.finditer(s):
        br = MONTH_ORDER_BRANCH.get(m.group(1))
        if br:
            put(br, "月", m.start())
    return [(b, u, p) for (b, u), p in sorted(seen.items(), key=lambda kv: kv[1])]


# ────────────────────────── 分段 ──────────────────────────

def segment(text: str) -> list[dict]:
    """按文档顺序收集日期行与案例标题，切成案例块。

    案例块 = 案例标题 → 下一个事件（日期行/案例标题）之前，上限 1200 字。
    日期归属：取本案例之前最近的一条日期行，且该日期行与此案例之间
    **不得插入别的案例标题**——插入了就说明那条日期属于后面的案例，
    本案例的时间不可还原（门 3 的判据）。
    """
    events: list[tuple[int, str, re.Match]] = []
    for m in DATE_RE.finditer(text):
        events.append((m.start(), "date", m))
    for m in CASE_RE.finditer(text):
        events.append((m.start(), "case", m))
    events.sort(key=lambda e: e[0])

    blocks: list[dict] = []
    for i, (pos, kind, m) in enumerate(events):
        if kind != "case":
            continue
        # 向前找最近日期行，中途遇案例标题即弃
        the_date = None
        for j in range(i - 1, -1, -1):
            if events[j][1] == "case":
                break
            the_date = events[j][2]
            break
        nxt = events[i + 1][0] if i + 1 < len(events) else len(text)
        blocks.append({"case": m, "date": the_date,
                       "end": min(nxt, m.start() + 1200)})
    return blocks


def parse_case(block: dict, seq: int) -> tuple[dict | None, dict]:
    m: re.Match = block["case"]
    cid = f"ZD{seq:03d}"
    topic = m.group(1).strip()
    raw_orig = strip_tail_gua(m.group(2).strip())
    raw_chg = strip_tail_gua((m.group(3) or m.group(4) or "").strip())   # 变X卦 与 X之Y

    # ── 无连接字的两种卦变形态（都实测存在， early 版因此丢卦/丢本卦）──
    # c) 「得火雷噬嗑化屯卦」：连接字是「化」，不在 CASE_RE 里，整段落进 g2
    #    （ZD056：曾被后缀匹配读成单卦「屯」，本卦噬嗑整段丢失）
    # d) 「得明夷小过」：两个卦名直接连写（ZD022：曾被读成单卦「小过」）
    split_note = ""
    if not raw_chg and "化" in raw_orig:
        head, _, tail = raw_orig.partition("化")
        if head and tail:
            raw_orig, raw_chg = strip_tail_gua(head), strip_tail_gua(tail)
            split_note = "化"
    if not raw_chg:
        sp = split_concat_names(raw_orig)
        if sp:
            raw_orig, raw_chg = sp
            split_note = "连写"

    # 转录讹字归一（假设，由卦变自洽门验证）；归一留痕进 provenance
    raw_orig, norm_o = apply_hex_variants(raw_orig)
    raw_chg, norm_c = apply_hex_variants(raw_chg)
    normalized = {}
    if norm_o:
        normalized["original"] = [m.group(2).strip(), raw_orig]
    if norm_c:
        normalized["changed"] = [m.group(3) or m.group(4) or "", raw_chg]
    if split_note:
        normalized["hex_name_split"] = [split_note, raw_orig, raw_chg]

    orig, orig_note = resolve_hex_name(raw_orig)
    chg, chg_note = (resolve_hex_name(raw_chg) if raw_chg else (None, ""))

    body = m.string[m.start():block["end"]]

    def excl(reason: str, **extra) -> tuple[None, dict]:
        rec = {"id": cid, "reason": reason, "topic": topic[:40],
               "raw_original": raw_orig, "raw_changed": raw_chg,
               "original": orig, "changed": chg}
        rec.update(extra)
        return None, rec

    # 弱日期紧邻守卫：标题前 10 字内有「X月Y日」（只记支）⇒ 本案真实日期行是它，
    # segment 配到的完整日期属于别案（ZD019/ZD066 实测张冠李戴）
    pre = m.string[max(0, m.start() - 10):m.start()]
    if WEAK_DATE_RE.search(pre):
        return excl(f"弱日期行紧邻（{WEAK_DATE_RE.search(pre).group(0)}），时间不可还原")

    if not has_render(body):
        return excl("无六爻渲染（规则陈述／行文提及，非占验案例）")

    dm: re.Match | None = block["date"]
    if dm is None:
        return excl("时间不可还原：案例前无紧邻的完整日期行")
    month_branch = dm.group(1)
    day_stem = dm.group(2)
    if day_stem == "已":                       # dz 转录本 已/己 混淆，归一并登记
        day_stem = "己"
    day_gz = day_stem + dm.group(3)

    # 上下卦序写反（火天同人＝天火同人）是书名变体，登记后放行；
    # 真存疑（卦体不符／不可解析）才剔除。
    if orig_note and ("不符" in orig_note or "不可解析" in orig_note):
        return excl(f"本卦存疑：{orig_note}")
    if chg_note and ("不符" in chg_note or "不可解析" in chg_note):
        return excl(f"变卦存疑：{chg_note}")
    base = hex_lines(orig) if orig else None
    if base is None:
        return excl(f"本卦名不可解析（{raw_orig}）")

    marked = render_moving_positions(body[:400])
    if chg:
        chg_lines = hex_lines(chg)
        if chg_lines is None:
            return excl(f"变卦名不可解析（{raw_chg}）")
        diff = set(moving_from_diff(base, chg_lines))
        if not diff:
            return excl("本卦与变卦相同却记有变卦")
        if marked and marked != diff:
            return excl(f"卦变不自洽：渲染动爻 {sorted(marked)} ≠ 卦变差集 {sorted(diff)}")
        moving = sorted(diff)
    else:
        # 静卦是合法卦型（与 build_yingqi_set.py 同口径）：应期由用神旺衰与日辰定。
        # 有动爻标记而漏记变卦的，以标记为准。
        moving = sorted(marked)

    # ── 断语段：渲染之后、下一案例/章标题之前的文本 ──
    rows = [ln for ln in body.splitlines() if YIN_YANG_RE.search(ln)]
    tail = body[body.find(rows[-1]) + len(rows[-1]):] if rows else body
    # 章标题止界：不停就会读进下一章理论文本，把别案实录当本家锚句（ZD027 实测）
    cut = len(tail)
    for cm in CHAPTER_RE.finditer(tail):
        ln_start = tail.rfind("\n", 0, cm.start()) + 1
        if tail[ln_start:cm.end()] == cm.group(0):
            cut = min(cut, ln_start)
    tail = tail[:cut]
    sentences = [s for s in re.split(r"[。；\n]", tail) if s.strip()]

    # ── 应期锚：第一个**结果标记句＋日期令牌**的句子 ──
    anchor = None
    for s in sentences:
        if OUTCOME_RE.search(s) and _date_tokens(s):
            anchor = s
            break
    if anchor is None:
        return excl("无应期锚：断语段无「结果标记句＋日期令牌」")

    # ── 子句级过滤：只收**占验实录**的令牌 ──
    # 锚句常把预测、他人假设、占测年引用和实录混在一句里（实测四类都出现过）：
    #   预测   ：「六月可望」——书上的期望，不是结果（ZD042）
    #   他人假设：「或曰：何不许冲空之午日」——被作者否掉的候选（ZD169）
    #   占测年  ：「戌年占及至次年」——占卦发生的年份，不是应期（ZD122）
    #   实录    ：「果于六月疾至，八月伙计盗尽」——同域并列，都要收（ZD011）
    # 规则：子句含已实现标记（果/竟/卒/后/应）→ 收；无标记但紧跟已标记子句 → 收（共域）；
    #       或曰/若曰/设若 起到 余曰/断曰 之间 → 全丢；「X年占」形 → 丢该令牌。
    clauses = re.split(r"[，,；;？?]", anchor)
    kept: list[tuple[str, str]] = []
    verdict_parts: list[str] = []     # 非假设子句——吉凶词只从这里读
    carry = False
    hypo = False
    for cl in clauses:
        if re.search(r"或曰|若曰|设若|假如|或问", cl):
            hypo = True
        if re.search(r"余曰|断曰|余谓|余断", cl):
            hypo = False
        if hypo:
            continue
        verdict_parts.append(cl)
        has_real = bool(REALIZED_RE.search(cl))
        toks = [t for t in _date_tokens(cl)
                if not (t[1] == "年" and re.search(r"[%s]年[^，。；]{0,4}占" % BRANCHES, cl))]
        if has_real:
            carry = True
            kept += [(b, u) for b, u, _ in toks]
        elif carry and toks:
            kept += [(b, u) for b, u, _ in toks]
    # 占测日/月自重：答案句里复述本案日支/月建的令牌，只有**紧邻强实现标记**才记
    # （「酉金与辰日相合」指占日本身，不计——ZD012 实测）。
    # 豁免只认 果/竟/卒：认弱标记（应/后）时，「应卯时者，酉金与辰日相合」（ZD018）、
    # 「应临戌父，巳月生之」（ZD027）、「应辰时者，戌日冲辰父」（ZD088）三例的
    # 占测日自重全部漏收——那三处的「应」是"解释为何应某时辰"，不是"已应验"。
    tokens = []
    for b, u in kept:
        self_date = (u == "日" and b == day_gz[1]) or (u == "月" and b == month_branch)
        if self_date:
            pos = next((p for bb, uu, p in _date_tokens(anchor)
                        if (bb, uu) == (b, u)), -1)
            ctx = anchor[max(0, pos - 8):pos] if pos >= 0 else ""
            if not STRONG_REALIZED_RE.search(ctx):
                continue
        if (b, u) not in tokens:      # 同支同单位重复令牌去重（ZD022/ZD066 实测「辰日、辰日」）
            tokens.append((b, u))
    if not tokens:
        return excl("应期锚只剩占测日/占测年自重或预测假设，无可评分令牌")
    branches = sorted({b for b, _ in tokens})
    if len(branches) > 3:
        return excl(f"应期含 {len(branches)} 支（{','.join(branches)}），过宽，不构成可检验断言")

    # 用神：「亥水财爻为用神」「以子孙爻为用神」「即用辰土为用神」；简称归一为全称。
    # 地支段 1-2 字（「酉金兄爻」「寅木财爻」都只有一个支——早版写 {2} 全军 N/A）
    use_rel = ""
    um = re.search(r"以?[%s]{1,2}[金木水火土]?(官鬼|父母|兄弟|子孙|妻财|财|子|父|兄|官|鬼)[爻]?"
                    r"[^。；\n]{0,10}为用神" % BRANCHES, tail)
    if um:
        use_rel = REL_SHORTHAND.get(um.group(1), um.group(1))
    else:
        um2 = re.search(r"以[【\[]?(官鬼|父母|兄弟|子孙|妻财|财|子|父|兄)[爻】\]]?"
                        r"[^。；\n]{0,6}为用神", tail)
        if um2:
            use_rel = REL_SHORTHAND.get(um2.group(1), um2.group(1))

    # 吉凶：只从**非假设子句**读（或曰/若曰段是作者否掉的候选，其吉凶词不是本案结果——
    # ZD065「或曰…世应相生，必相救解，余曰…果于五月下狱」实测：读全句会把凶案读成 N/A）。
    # 预测句里的「许之可治」与实录句的「后死于寅日」同现时记 N/A（ZD029 实测）。
    # 判不出（吉凶词同现或俱无）→ verdict 记空串，按 N/A 不进分母
    # （与维基文库集 23/81「基准未记吉凶」同口径，不整例剔除）。
    verdict_src = "，".join(verdict_parts)
    good = any(k in verdict_src for k in GOOD_WORDS)
    bad = any(k in verdict_src for k in BAD_WORDS)
    verdict = "" if good == bad else ("吉" if good else "凶")

    case = {
        "id": cid,
        "source": "《增删卜易》（殆知阁转录本）",
        "topic": topic[:24],
        "question": topic,
        "input": {"date": f"{month_branch}月{day_gz}日", "question": topic},
        "hexagram": {"original": orig, "changed": chg, "moving": moving},
        "expected": {
            "verdict": verdict,
            "use_god": use_rel,
            "use_god_branch": "",
            "use_god_position": "",
            "yingqi": "、".join(f"{b}{u}" for b, u in tokens),
            "yingqi_branches": branches,
            "detail": anchor.strip()[:200],
            "same_as_day_branch": day_gz[1] in branches,
        },
        "provenance": {
            "source_file": "data/sources/zengshan_buyi_dz.dz.txt",
            "sha256": hashlib.sha256(SRC.read_bytes()).hexdigest(),
            "offset": m.start(),
            "text_head": m.group(0)[:60],
            "day_stem_normalized": dm.group(2) == "已",
            "hex_name_normalized": normalized or None,
            "hex_prefix_note": (orig_note or "") or (chg_note or "") or None,
        },
        "notes": "dev_tools/build_zengshan_dz_cases.py 抽取，过卦名可解析/卦变自洽/时间可还原/"
                 "实录句有应期令牌/不宽于三支/不与在册同案 六道门；吉凶判不出记 N/A；永不参与调参",
    }
    return case, None


def load_existing_keys() -> tuple[set, set]:
    """在册案例的去重键：(本卦,变卦,月建,日柱) 与 (本卦,变卦,应期支,占题前 6 字)。

    跳过本器自己的产出文件（OUT）——否则二次运行时 22 例会全量撞上自己，
    「可评分 0」不说，审计报告还会被这轮空结果污染（2026-10-12 实测）。
    """
    k1: set = set()
    k2: set = set()
    for f in CASES_GLOB:
        if f.resolve() == OUT.resolve():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for c in (data.get("cases", []) if isinstance(data, dict) else data):
            hx = c.get("hexagram") or {}
            orig, chg = hx.get("original"), hx.get("changed")
            d = (c.get("input") or {}).get("date", "")
            md = re.search(r"([%s])月([%s])([%s])日" % (BRANCHES, STEMS, BRANCHES), d or "")
            if orig and md:
                k1.add((orig, chg, md.group(1), md.group(2) + md.group(3)))
            yq = (c.get("expected") or {}).get("yingqi_branches") or []
            topic = (c.get("topic") or "")[:6]
            if orig and yq:
                k2.add((orig, chg, tuple(sorted(yq)), topic))
    return k1, k2


def main() -> int:
    ap = argparse.ArgumentParser(description="从增删卜易 dz 底本抽取应期案例作外部验证集")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    text = SRC.read_text(encoding="utf-8")
    blocks = segment(text)
    print(f"分段：{len(blocks)} 个案例块")

    k1, k2 = load_existing_keys()
    kept, excluded = [], []
    for i, b in enumerate(blocks, 1):
        case, rec = parse_case(b, i)
        if case is None:
            excluded.append(rec)
            continue
        hx = case["hexagram"]
        d = case["input"]["date"]
        md = re.search(r"([%s])月([%s])([%s])日" % (BRANCHES, STEMS, BRANCHES), d)
        key1 = (hx["original"], hx["changed"], md.group(1), md.group(2) + md.group(3))
        key2 = (hx["original"], hx["changed"],
                tuple(case["expected"]["yingqi_branches"]), case["topic"][:6])
        if key1 in k1:
            excluded.append({"id": case["id"], "reason": "与在册案例同案（同卦变＋月建＋日柱），转录差异不补",
                             "topic": case["topic"]})
            continue
        if key2 in k2:
            excluded.append({"id": case["id"], "reason": "与在册案例同案（同卦变＋应期支＋占题）",
                             "topic": case["topic"]})
            continue
        kept.append(case)
        k1.add(key1)
        k2.add(key2)

    print(f"可评分 {len(kept)} 例，剔除 {len(excluded)} 例")
    for e in excluded[:20]:
        print(f"  × {e['id']}: {e['reason']}")
    if len(excluded) > 20:
        print(f"  …另 {len(excluded) - 20} 例")
    for c in kept:
        print(f"  √ {c['id']} {c['topic']}｜{c['hexagram']['original']}"
              f"→{c['hexagram']['changed'] or '—'} 动{c['hexagram']['moving']}｜"
              f"{c['input']['date']}｜应期 {c['expected']['yingqi']}｜{c['expected']['verdict'] or 'N/A'}")

    lines = ["# 案例库应期抽取审计（dz 底本通道）", "",
             f"抽取器：`dev_tools/build_zengshan_dz_cases.py`｜分段 {len(blocks)} → "
             f"可评分 {len(kept)} 例｜生成于 {date.today().isoformat()}", "",
             "收录门：卦名可解析（讹字登记表归一＋卦变门验证；「得X化Y」「得XY」两种无连接字",
             "卦变形态先拆后解）、卦变自洽（渲染动爻≡卦变差集）、时间可还原（紧邻**完整**日期行；",
             "标题前 10 字内出现只记支的弱日期行即不可还原）、实录句有应期令牌且不宽于三支、",
             "令牌只取实录（预测/或曰假设/占测年/占测日自重不计，自重豁免只认果/竟/卒强标记）、",
             "不与在册案例同案。吉凶判不出记 N/A 不进分母。",
             "**任一门不过即 excluded，不放宽收录；与在册同案者不算新例（防重复计数）。**", "",
             "## 可收录（未参与调参的外部验证集 zengshan_dz_holdout）", ""]
    lines += [f"- `{c['id']}` {c['topic']}｜{c['hexagram']['original']}"
              f"→{c['hexagram']['changed'] or '—'}｜{c['input']['date']}｜"
              f"应期 `{'、'.join(c['expected']['yingqi_branches'])}`｜{c['expected']['verdict'] or 'N/A'}"
              for c in kept] or ["（无）"]
    lines += ["", "## 剔除清单与原因", "", "| 案例 | 原因 | 占题 |", "|---|---|---|"]
    lines += [f"| {e['id']} {e.get('topic','')} | {e['reason']} |" for e in excluded]
    lines += ["", "## 结论", "",
              "本通道与 build_yingqi_set.py（case_library.md 通道）平行：同六道门纪律、同外部集身份。",
              "与在册案例同案者一律剔除——重复计数是八字科 #39 的病灶，外部集扩样先过这一关。", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("审计报告 →", REPORT.relative_to(HERE.parent))

    if args.dry_run or not kept:
        return 0

    OUT.write_text(json.dumps({"_meta": {
        "description": "《增删卜易》殆知阁转录本抽取的应期外部验证集；六道门＋同案去重；永不参与调参",
        "built_by": "dev_tools/build_zengshan_dz_cases.py",
        "source_sha256": hashlib.sha256(SRC.read_bytes()).hexdigest(),
        "total_cases": len(kept),
        "excluded": excluded,
    }, "cases": kept}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n写入 {OUT.relative_to(HERE.parent)}（{len(kept)} 例）")

    sp = json.loads(SPLITS.read_text(encoding="utf-8")) if SPLITS.exists() else {}
    sp["zengshan_dz_holdout"] = [c["id"] for c in kept]
    sp["note_externals"] = (sp.get("note_externals", "") +
                            "；zengshan_dz_holdout=增删卜易 dz 底本通道，永不参与调参").lstrip("；")
    SPLITS.write_text(json.dumps(sp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("case_splits.json 已登记 zengshan_dz_holdout")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
