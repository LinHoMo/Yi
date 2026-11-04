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

八道门（任一门不过即 excluded，写明原因，绝不放宽）：
  1. 本卦名可解析（全名→内核短名；转录讹字按登记表归一，假设由门 2 验证；
     「得X化Y」「得XY」两种无变/之连接字的卦变形态先拆后解，防后缀匹配丢本卦）
  2. 卦变自洽：渲染里「动」标记的爻位 ≡ 本卦⊕变卦 的差集（无变卦时以标记/静卦计）
  3. 时间可还原：案例块前一条**完整**日期行（月建＋日柱）紧邻本案例
     （中间不得插入别的案例；标题前 10 字内出现只记支的弱日期行 ⇒ 真实日期行
      就是它，segment 配到的远处完整日期属于别案，不收——ZD019/ZD066 实测）
  4. 断语段有占验实录句（结果标记＋日期令牌），且令牌不宽于三支
  5. 锚句归属本案：块内又起他卦且本案为静卦时，锚句及其理据句（前一句带
     余曰/断曰/余谓/余断）引用的「支＋五行」若有本案渲染所无 ⇒ 应期属后卦
     （ZD124 一块三卦实测；ZD036 同属多占块但锚句理据不引支五行，保留；
      动卦有化出支、无反例，不拦——新规则须有可判真例）
  6. 令牌只取实录：预测句、或曰假设段、「X年占」占测年、占测日自重，一律不计
     （自重豁免只认 果/竟/卒 强标记；「应卯时者…辰日相合」形的应=解释，不是应验）
  7. 不与在册案例同案（同卦变＋月建＋日柱，或同卦变＋应期支＋占题）——转录差异不补
  8. 吉凶判不出记空串（N/A 不进分母），不整例剔除（与维基文库集同口径）

占题重切（第一百五十六批，ZD160 实测）：题含「得」时（「占何时得价得归妹」），
CASE_RE 题组排除「得」而 HEX 段不排除——分隔「得」被题吞掉半个，题读成「何时」、
卦名段顶前面成「价得归妹」，引擎用神错成子孙亥（书答寅月，须妻财卯才可能命中）。
按解析出的内核卦名回溯补全占题（见 retitle()），变更留痕 provenance.question_retitled。
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
# 固化：glob 返回生成器，赋给模块全局后若被二次迭代会静默返回空（§四.8「扫了 0 份 ≠ 没文档」类隐患）。
# 此处仅 L595 单次消费，但为防止日后追加扫描时静默全盲，预先 materialize 成 list。
CASES_GLOB = list((HERE.parent / "data" / "cases").glob("*_cases.json"))

STEMS = "".join(HEAVENLY_STEMS)
# dz 转录本把日干「己」写作「已」（曾於午月**已**卯日）——已知转录混淆，抽取时归一并登记
STEMS_SRC = STEMS + "已"
BRANCHES = "".join(EARTHLY_BRANCHES)

# 案例标题：占<题>[，]得<卦>[变<卦>|之<卦>][卦]。
# 卦名段**不含**「变之」但**含**「卦」（尾卦由 strip 处理）——早期版把「卦」排除在卦名段外，
# 懒惰匹配＋可选「变」组会把「得离卦变火山旅」截成「得离卦」（变卦整段丢失，ZD017 实测）。
HEX = r"[^\n。；：，、变之\s]{1,6}"
# 402 批：占题字符类不再排除「之」、最短降到 1 字——「占官之升迁」「占寿」「自占病」
# 三类真实占例头此前整条不被 segment 识别。1 字题由 ONE_CHAR_BLOCK 挡行文（「占又得…」）。
CASE_RE = re.compile(
    r"占([^\n。；：，、变卦得]{1,24}?)[，,]?得(%s)(?:(?:变(%s))|之(%s))?" % (HEX, HEX, HEX))
# 513 批：句号式占例头（「如戌日丙午日占何日雨。得坎之井卦」）CASE_RE 认不出，整段并进前一案，
# 使 ZD214 的应期读到下一案（酉日天变／戌日而雨）。此式**只作切块止界**，不新建案例：
# 全局放宽 CASE_RE 会连带 ZD102 消失、多出 ZD230／ZD233（实测），动的是集身份，不做。
STOP_HEAD_RE = re.compile(
    r"(?m)^\s*(?:如|又|例|即如|又如)?[^\n]{0,12}占[^\n。；：，、变卦得]{1,24}?[。；]得[^\n。；：，、变之\s]{1,6}")
# 单字题黑名单：这些是行文连接词，不是占题（「占又得大有之大壮」实测假头）。
ONE_CHAR_BLOCK = set("又此其之者事卦得问曰也而即")


def topic_allowed(topic: str) -> bool:
    """单字题只挡行文连接词；真实单字题（寿/病/财/梦/时/缺/地…）放行。"""
    return not (len(topic) == 1 and topic in ONE_CHAR_BLOCK)
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
# 513 批补「而雨／而晴」：ZD102（临之蒙）实录句写作「亥日而雨，即于亥日酉时晴」，
# 无 果/竟/卒/后/应 起句词，该案因此被整案剔除；二字短语只在天时占里出现，窄口径。
REALIZED_RE = re.compile(r"[果竟卒后应]|而[雨晴]")
# 强实现标记：占测日自重令牌的豁免只认这三个弱不行——
# ZD018「**应**卯时者，酉金与辰日相合」、ZD027「**应**临戌父，巳月生之」、
# ZD088「**应**辰时者，戌日冲辰父」都是"解释为何应某时辰"的句式，
# 被豁免的辰日/巳月/戌日全是占测日本身，不是应期（三例实测漏收）。
STRONG_REALIZED_RE = re.compile(r"[果竟卒]")
OUTCOME_RE = re.compile(r"[果应验竟卒后至待许]")
# 多占法守卫：块内锚句之前又起他卦的标记（「又于乙酉日占得无妄」「乙酉日又占得
# 节之坎卦」「又得明夷之丰」三种句式实测都存在）。
RECAST_RE = re.compile(r"又[^\n。；]{0,16}?(?:占得|得)")
# 锚句理据里的「支＋五行」引用（「世下巳火变寅木子孙」→ 巳、寅）——
# 用于多占法守卫：静卦案例的锚句引用了本案渲染里不存在的支，说明应期属后卦。
BRANCH_ELEMENT_REF_RE = re.compile(r"([%s])([金木水火土])" % BRANCHES)
# 应期令牌四种记法（《增删卜易》实测都存在）
YQ_TOKEN_RE = re.compile(r"([%s])(日|月|年)" % BRANCHES)
YQ_FULL_DAY_RE = re.compile(r"([%s])([%s])日" % (STEMS_SRC, BRANCHES))
YQ_IMPLIED_DAY_RE = re.compile(r"(?:果于|得于|应于|至)([%s])([%s])(?![日月年])" % (STEMS_SRC, BRANCHES))
YQ_MONTH_ORDER_RE = re.compile(r"([正一二三四五六七八九十十一十二]|[冬腊])月")

# 六亲简称 → 全称（dz 渲染写「财爻」「子水」「父动」，期望值要全称）
REL_SHORTHAND = {"财": "妻财", "子": "子孙", "父": "父母", "兄": "兄弟",
                 "官": "官鬼", "鬼": "官鬼"}

# 用神句的三种**书载**形态（与卜筮正宗建器 412/417 批同一口径；419 批补支）：
#   ① 支＋六亲：「寅木财爻为用神」「以辰爻父母为用」 → 六亲＋支都取句内
#   ② 仅六亲：  「以财爻为用神」                     → 只取六亲（支书上未写，留空）
#   ③ 支式：    「世爻亥水为用神」「以子水为用」     → 支取句内，六亲由**本书原卦列**
#                 的纳甲六亲定；同支在卦中出现两种六亲时留空（不猜）
# 「为用(?:神)?」收省文（「亥水父爻为用」）是同一句式，不是新判据；
# 否定语境（前 3 字含 非/不/勿/莫/无）不取；「卦中土为用神」只有五行、无支无六亲 → 不取。
USE_GOD_REL_RE = re.compile(
    r"以?([%s]{1,2})[金木水火土]?[爻]?"
    r"(官鬼|父母|兄弟|子孙|妻财|财|子|父|兄|官|鬼)[爻]?"
    r"[^。；\n]{0,10}为用(?:神)?" % BRANCHES)
USE_GOD_CAT_RE = re.compile(
    r"以[【\[]?(官鬼|父母|兄弟|子孙|妻财|财|子|父|兄)[爻】\]]?"
    r"[^。；\n]{0,6}为用(?:神)?")
USE_GOD_BRANCH_RE = re.compile(r"([%s])[金木水火土]?[爻]?为用(?:神)?" % BRANCHES)
# 原卦列行：六亲＋支＋五行（每行第一个匹配即原卦列，其后是变卦列）
ROW_REL_RE = re.compile(r"(官鬼|父母|兄弟|子孙|妻财)([%s])([金木水火土])" % BRANCHES)


def _negated_use_god(tail: str, m: re.Match) -> bool:
    return bool(re.search(r"[非不勿莫无]", tail[max(0, m.start() - 3):m.start()]))


def extract_use_god(tail: str, rows: list[str]) -> tuple[str, str, str, str]:
    """从本案断语段取书载用神；返回 (六亲, 支, 出处, 引文)。

    只认书上明写的形态，不由引擎/旺衰反推；取不到返回四个空串。
    """
    m = USE_GOD_REL_RE.search(tail)
    if m and not _negated_use_god(tail, m):
        return (REL_SHORTHAND.get(m.group(2), m.group(2)), m.group(1)[-1],
                "断语「支+六亲为用」句", m.group(0).strip())
    m2 = USE_GOD_CAT_RE.search(tail)
    if m2 and not _negated_use_god(tail, m2):
        return (REL_SHORTHAND.get(m2.group(1), m2.group(1)), "",
                "断语「以六亲为用」句", m2.group(0).strip())
    m3 = USE_GOD_BRANCH_RE.search(tail)
    if m3 and not _negated_use_god(tail, m3):
        br = m3.group(1)
        rels = set()
        for ln in rows:
            mm = ROW_REL_RE.search(ln)      # 每行第一项＝原卦列
            if mm and mm.group(2) == br:
                rels.add(mm.group(1))
        if len(rels) == 1:
            return rels.pop(), br, "支式用神·本书原卦列定六亲", m3.group(0).strip()
    return "", "", "", ""

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


def retitle(m: re.Match, hex_name: str) -> tuple[str, bool]:
    """占<题>得<卦>：把被 CASE_RE 切短的占题补全（题含「得」时）。

    CASE_RE 题组排除「得」、HEX 段不排除：「占何时得价得归妹」的分隔「得」
    被题吞掉半个——题读成「何时」、卦名段顶前面成「价得归妹」（ZD160 实测：
    题丢「得价」，引擎用神错成子孙亥；补全为「何时得价」后转妻财卯，
    书答寅月才可能命中）。按解析出的内核卦名回溯：占 与 卦名之间最后一个
    「得」是分隔字，其间全是占题。

    不会误切的安全性：题组字符集不含「得」，故真占题里不可能出现「得」——
    若卦名恰好在题内先出现一次（「占求兑得兑为泽」），回溯区间 whole[1:h]
    整个落在题内、找不到「得」⇒ 原样返回。只有卦名出现在某个「得」之后
    （真卦名位或其后的巧合位）才可能改写，且改写只会把题补长、不会截短。
    返回 (占题, 是否补全)。
    """
    if not hex_name:
        return m.group(1).strip(), False
    whole = m.group(0)
    h = whole.find(hex_name)
    if h < 0:
        return m.group(1).strip(), False
    d = whole.rfind("得", 1, h)
    if d < 0:
        return m.group(1).strip(), False
    t = whole[1:d].strip("，,。；;：: 、")
    return (t or m.group(1).strip()), t != m.group(1).strip()


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
    for m in STOP_HEAD_RE.finditer(text):
        events.append((m.start(), "stop", m))
    events.sort(key=lambda e: e[0])

    blocks: list[dict] = []
    for i, (pos, kind, m) in enumerate(events):
        if kind != "case":
            continue
        # 向前找最近日期行，中途遇案例标题即弃（句号式占例头不是本案日期，跳过不取）
        the_date = None
        for j in range(i - 1, -1, -1):
            if events[j][1] == "case":
                break
            if events[j][1] == "stop":
                continue
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

    # 占题重切（ZD160 实测）：题含「得」被 CASE_RE 切短（见 retitle 文档），
    # 补全后 question 才能驱动引擎用神判定；变更留痕 provenance.question_retitled。
    topic_retitle = None
    new_topic, retitled = retitle(m, orig)
    if retitled:
        topic_retitle = [m.group(1).strip(), new_topic]
        topic = new_topic

    body = m.string[m.start():block["end"]]

    def excl(reason: str, **extra) -> tuple[None, dict]:
        rec = {"id": cid, "reason": reason, "topic": topic[:40],
               "raw_original": raw_orig, "raw_changed": raw_chg,
               "original": orig, "changed": chg}
        rec.update(extra)
        return None, rec

    # 402 批：单字行文题（占又得…）不是占例头；真实单字题（寿/病/财/梦…）保留。
    if not topic_allowed(topic):
        return excl("单字占题疑为行文（占%s得…）" % topic)

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

    # ── 应期锚：**先找强实现句（果/竟/卒）＋日期令牌**，再退回弱结果词 ──
    # 402 批：旧写法按 OUTCOME_RE（含 待/许/应）取第一句，遇到「待甲寅日出空」
    # 这类预测句就先锁定，后面的「果于寅日…」反而读不到（L550/L2084 实测）。
    # 强实现句优先，弱结果句只作退路；预测句不再抢占实录锚。
    anchor = None
    anchor_idx = -1
    for i, s in enumerate(sentences):
        if STRONG_REALIZED_RE.search(s) and _date_tokens(s):
            anchor = s
            anchor_idx = i
            break
    if anchor is None:
        for i, s in enumerate(sentences):
            if OUTCOME_RE.search(s) and _date_tokens(s):
                anchor = s
                anchor_idx = i
                break
    if anchor is None:
        return excl("无应期锚：断语段无「结果标记句＋日期令牌」")

    # ── 门 5：多占法错位（ZD124 实测）──
    # 一块三卦（夬→无妄→节之坎）：锚句「果结于甲寅日」连理据「世下巳火变寅木子孙」
    # 都属第三卦，本案（静卦夬）渲染里没有巳火——收进来就是拿后卦的应期给前卦打分。
    # 判据：块内又起他卦（RECAST_RE）且本案为静卦时，锚句＋理据句（前一句带
    # 余曰/断曰/余谓/余断）引用的「支＋五行」，若有本案渲染所无 ⇒ 应期属后卦。
    # ZD036 同属多占块，但锚句理据（「世爻出空」）不引支五行，保留；
    # 动卦有化出支、无反例，不拦（新规则须有可判真例）。
    if not chg:
        rm = RECAST_RE.search(body)
        if rm:
            ctx = anchor
            if anchor_idx > 0 and re.search(r"余曰|断曰|余谓|余断", sentences[anchor_idx - 1]):
                ctx = sentences[anchor_idx - 1] + "，" + anchor
            refs = {x.group(1) for x in BRANCH_ELEMENT_REF_RE.finditer(ctx)}
            if refs:
                own = {ym.group(0)[0] for ln in body[:rm.start()].splitlines()
                       for ym in YIN_YANG_RE.finditer(ln)}
                missing = refs - own
                if missing:
                    return excl(f"多占法错位：锚句理据引用本案渲染没有的支"
                                f"（{'、'.join(sorted(missing))}），应期属后卦")

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

    # 用神：只取书上明写的三种形态（支+六亲／仅六亲／支式·六亲由本书卦表定），
    # 详见 extract_use_god()。419 批：此前只收六亲，书里的支被整段丢掉
    # （ZD014「寅木财爻」、ZD016「酉金兄爻」），支式「世爻亥水为用神」整句漏收（ZD195）。
    use_rel, use_branch, use_src, use_quote = extract_use_god(tail, rows)

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
            "use_god_branch": use_branch,
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
            "question_retitled": topic_retitle,
        },
        "notes": "dev_tools/build_zengshan_dz_cases.py 抽取，过卦名可解析/卦变自洽/时间可还原/"
                 "实录句有应期令牌/不宽于三支/锚句归属本案/不与在册同案 七道门；吉凶判不出记 N/A；永不参与调参",
        # 暂存原始卦名，仅供「与在册同案」去重记录带走（写盘前 pop，不进产物）
        "_raw": {"raw_original": raw_orig, "raw_changed": raw_chg,
                 "original": orig, "changed": chg},
    }
    if use_rel:     # 只给书载明示的案例留痕（取不到时不写空键，26 例逐字段不变）
        case["provenance"]["use_god_source"] = use_src
        case["provenance"]["use_god_quote"] = use_quote
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


def merge_old_expected(case: dict, old_case: dict) -> None:
    """建器不产出的书证字段不得因重建而清空（419 批追认 403 批的静默清空事故）。

    206／208 批逐条做过 dz 用神书证校勘（18 例 `use_god`／`use_god_branch`／
    `use_god_note`，ZD188 另有 `yingqi_note`）；403 批建器扩样重生成时只写自己
    抽到的字段，旧册这 18 例被整段置空，而 `check_expected_coverage` 只盯
    wikisource，没有门发现。本函数按**空位填补**：新建器抽到的值优先（书载
    「X为用神」句），抽不到则沿用旧册书证值；note 类字段建器从不产出，旧册有则沿用。
    """
    e, oe = case["expected"], (old_case.get("expected") or {})
    if not e.get("use_god") and oe.get("use_god"):
        e["use_god"] = oe["use_god"]
        e["use_god_branch"] = oe.get("use_god_branch", "")
    for k in ("use_god_note", "yingqi_note", "verdict_note"):
        if not e.get(k) and oe.get(k):
            e[k] = oe[k]
    # 512 批：verdict 也有建器推不出的部分。词表读不到结论的六例（ZD029 治+死同现、
    # ZD221/222「卒」不在词表、ZD125 险厄而人免、ZD139「相逢」、ZD188 登科中魁），
    # 是历批按书载实录句校勘定下的；旧版重建会把它们静默清成 N/A（同 419 批 18 例用神
    # 书证被清空的病）。此处同样按空位沿用，且只沿用它——建器读出的值优先，不被旧值覆盖。
    if not e.get("verdict") and oe.get("verdict"):
        e["verdict"] = oe["verdict"]


def assign_stable_ids(kept: list[dict], excluded: list[dict], old_doc: dict) -> tuple[list[dict], list[dict]]:
    """保留在册 id，新条目取 max+1；不因 parser 扩块而整体重编号（test_seal 依赖旧 id）。

    旧 id 匹配键：kept＝(日期, 本卦, 变卦)；excluded＝(占题, 原始卦名, 变卦名)。
    匹配不上的新条目按块序（临时 ZD{seq}）追加，从 max(旧 id)+1 起编。
    """
    old_cases = old_doc.get("cases") or []
    old_ex = (old_doc.get("_meta") or {}).get("excluded") or []
    by_kept = {}
    for c in old_cases:
        hx = c.get("hexagram") or {}
        key = ((c.get("input") or {}).get("date"), hx.get("original"), hx.get("changed"))
        by_kept.setdefault(key, c.get("id"))
    by_ex = {}
    for e in old_ex:
        key = (e.get("topic"), e.get("raw_original"), e.get("raw_changed"))
        by_ex.setdefault(key, e.get("id"))
    old_ex_by_id = {str(e.get("id")): e for e in old_ex if e.get("id")}
    # 旧册「与在册同案」去重记录原本只带占题（无原始卦名），无法按键回指；按**占题＋顺序**
    # 一批一配对（419 批实测 48 条逐条顺序一致）。新记录开始带 raw_original/raw_changed，
    # 下一轮起改走键匹配，本表只服务这次一次性迁移。
    keyless_same = [(str(e.get("id")), str(e.get("topic"))) for e in old_ex
                    if not e.get("raw_original")
                    and str(e.get("reason", "")).startswith("与在册案例同案")]
    claimed: set[str] = set()
    pending: list[dict] = []
    for c in kept:
        hx = c.get("hexagram") or {}
        key = ((c.get("input") or {}).get("date"), hx.get("original"), hx.get("changed"))
        oid = by_kept.get(key)
        if oid and oid not in claimed:
            c["id"] = oid
            claimed.add(oid)
        else:
            pending.append(c)
    for e in excluded:
        key = (e.get("topic"), e.get("raw_original"), e.get("raw_changed"))
        oid = by_ex.get(key)
        if oid and oid not in claimed:
            e["id"] = oid
            claimed.add(oid)
            continue
        # 旧册无键的去重记录：按占题取最早一条未认领的旧 id（顺序对齐已由 selftest 守着）
        if str(e.get("reason", "")).startswith("与在册案例同案"):
            for j, (oid2, t2) in enumerate(keyless_same):
                if oid2 not in claimed and t2 == str(e.get("topic")):
                    e["id"] = oid2
                    claimed.add(oid2)
                    keyless_same.pop(j)
                    break
            else:
                pending.append(e)
            continue
        # 块序确定时临时 id 就是块号——占题一致即认定同一条，保留旧号；不符才当新条目
        tid = str(e.get("id") or "")
        old = old_ex_by_id.get(tid)
        if tid and old and tid not in claimed and str(old.get("topic")) == str(e.get("topic")):
            claimed.add(tid)
            continue
        pending.append(e)
    nums = []
    for rec in old_cases + old_ex:
        mm = re.search(r"ZD(\d+)", str(rec.get("id") or ""))
        if mm:
            nums.append(int(mm.group(1)))
    next_id = (max(nums) if nums else 0) + 1
    # 新条目按块序（临时 id 的序号）编，不按 kept/excluded 分列表的顺序
    def _seq(obj: dict) -> int:
        mm = re.search(r"ZD(\d+)", str(obj.get("id") or ""))
        return int(mm.group(1)) if mm else 0
    for obj in sorted(pending, key=_seq):
        while True:
            cand = f"ZD{next_id:03d}"
            next_id += 1
            if cand not in claimed:
                obj["id"] = cand
                claimed.add(cand)
                break
    return kept, excluded


def selftest() -> int:
    fails = []
    for s in ("占官之升迁得艮卦变山雷颐", "占寿得剥之无妄卦", "自占病得泽风大过变火风鼎卦"):
        if not CASE_RE.search(s):
            fails.append("真实占例头未被识别：%r" % s)
    if topic_allowed("又"):
        fails.append("行文单字题「又」未被挡住")
    if not topic_allowed("寿"):
        fails.append("真实单字题「寿」被误挡")
    # 用神三形态（419 批）：支+六亲／仅六亲／支式·六亲由原卦列定。
    # 原卦列样本取自 ZD195 本书渲染（亥水两现均为父母）。
    rows195 = ["妻财未土″    动          子孙巳火′",
               "官鬼酉金′    动          妻财未土″应",
               "父母亥水′世              官鬼酉金′",
               "官鬼酉金′                官鬼酉金′",
               "父母亥水′                父母亥水′世",
               "妻财丑土″应              妻财丑土″"]
    if extract_use_god("自占病世爻亥水为用神，被未土忌神动而克水", rows195)[:2] != ("父母", "亥"):
        fails.append("支式用神未按原卦列定为父母亥（ZD195 真例）")
    if extract_use_god("断曰：寅木财爻为用神，财爻克世", [])[:2] != ("妻财", "寅"):
        fails.append("支+六亲用神未取全（应妻财·寅）")
    if extract_use_god("酉金兄爻为用神", [])[:2] != ("兄弟", "酉"):
        fails.append("支+六亲用神未取全（应兄弟·酉）")
    if extract_use_god("亥水父爻为用，虽值旬空", [])[:2] != ("父母", "亥"):
        fails.append("「为用」省文未取（应父母·亥）")
    if extract_use_god("以财爻为用神", [])[:2] != ("妻财", ""):
        fails.append("仅六亲用神未取（应妻财、支留空）")
    # 负例：同支两六亲不猜／只有五行不取／否定语境不取
    if extract_use_god("世爻子水为用神", ["父母子水″", "妻财子水′"])[:2] != ("", ""):
        fails.append("同支两种六亲时不应猜（negative）")
    if extract_use_god("卦中土为用神", [])[:2] != ("", ""):
        fails.append("只有五行、无支无六亲不应取（negative）")
    if extract_use_god("不可以财爻为用神", [])[:2] != ("", ""):
        fails.append("否定语境不应取（negative）")
    old = {"cases": [{"id": "ZD001", "input": {"date": "卯月壬辰日"},
                      "hexagram": {"original": "贲", "changed": None}}], "_meta": {"excluded": []}}
    kept = [{"id": "ZD999", "input": {"date": "卯月壬辰日"},
             "hexagram": {"original": "贲", "changed": None}}]
    kept, _ = assign_stable_ids(kept, [], old)
    if kept[0]["id"] != "ZD001":
        fails.append("旧 kept id 未保留：%r" % kept[0]["id"])
    old2 = {"cases": [], "_meta": {"excluded": [
        {"id": "ZD100", "topic": "t", "raw_original": "o", "raw_changed": ""}]}}
    ex = [{"id": "ZD999", "topic": "t", "raw_original": "o", "raw_changed": ""},
          {"id": "ZD998", "topic": "n", "raw_original": "n", "raw_changed": ""}]
    _, ex = assign_stable_ids([], ex, old2)
    ids = {e["id"] for e in ex}
    if "ZD100" not in ids or "ZD101" not in ids:
        fails.append("旧 excluded id 未保留/新 id 未取 max+1：%r" % ids)
    # 无键去重记录（旧册只带占题）按「临时 id＋占题」回指；占题不符不复用（419 批）
    old3 = {"cases": [], "_meta": {"excluded": [
        {"id": "ZD202", "topic": "病", "reason": "与在册案例同案（同卦变＋月建＋日柱），转录差异不补"}]}}
    ex3 = [{"id": "ZD202", "topic": "病", "reason": "与在册案例同案（同卦变＋月建＋日柱），转录差异不补"}]
    _, ex3 = assign_stable_ids([], ex3, old3)
    if ex3[0]["id"] != "ZD202":
        fails.append("无键去重记录未保留旧 id（重编号会让 --why 指错块）")
    ex4 = [{"id": "ZD202", "topic": "何日雨", "reason": "x"}]
    _, ex4 = assign_stable_ids([], ex4, old3)
    if ex4[0]["id"] == "ZD202":
        fails.append("占题不符的条目不应复用旧 id（negative）")
    # 旧册书证字段空位填补（419 批：403 批重建曾整段清空 18 例）
    newc = {"expected": {"use_god": "", "use_god_branch": "", "verdict": "吉"}}
    oldc = {"expected": {"use_god": "父母", "use_god_branch": "卯",
                         "use_god_note": "书证：卯木父爻发动而生世",
                         "yingqi_note": "流年后验叙事轨"}}
    merge_old_expected(newc, oldc)
    if newc["expected"].get("use_god") != "父母" or newc["expected"].get("use_god_branch") != "卯":
        fails.append("旧册用神书证未按空位填补")
    if newc["expected"].get("use_god_note") != "书证：卯木父爻发动而生世":
        fails.append("旧册 use_god_note 未沿用")
    if newc["expected"].get("yingqi_note") != "流年后验叙事轨":
        fails.append("旧册 yingqi_note 未沿用")
    new2 = {"expected": {"use_god": "妻财", "use_god_branch": "寅"}}
    merge_old_expected(new2, oldc)
    if new2["expected"].get("use_god") != "妻财" or new2["expected"].get("use_god_branch") != "寅":
        fails.append("建器抽到的用神被旧值覆盖（negative）")
    # 512 批：verdict 空位沿用（建器读不出结论的六例不得被重建清成 N/A）
    new3 = {"expected": {"verdict": ""}}
    merge_old_expected(new3, {"expected": {"verdict": "凶",
                                           "verdict_note": "书证：果卒于卯年"}})
    if new3["expected"].get("verdict") != "凶" or new3["expected"].get("verdict_note") != "书证：果卒于卯年":
        fails.append("旧册 verdict／verdict_note 未按空位填补")
    new4 = {"expected": {"verdict": "吉"}}
    merge_old_expected(new4, {"expected": {"verdict": "凶"}})
    if new4["expected"].get("verdict") != "吉":
        fails.append("建器读出的 verdict 被旧值覆盖（negative）")
    print("√ selftest：之/单字题识别、行文黑名单、用神三形态（真 5 + 负 3）、稳定 id、verdict 空位沿用全过"
          if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="从增删卜易 dz 底本抽取应期案例作外部验证集")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--reject-stats", action="store_true",
                    help="按「哪一道门」归并打印剔除原因直方图——回答「扩容该改哪一处」而不是逐条问")
    ap.add_argument("--why", action="append", default=[], metavar="ID",
                    help="打印指定案例 id 的去留理由（可重复）。为什么不默认全打：剔除例逾百条，"
                         "全打会淹掉 √ 清单；而**只打前 20 条**又让「某条为什么没进册」变成查不到——"
                         "378 批加此参数就是为了不再靠猜。")
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    text = SRC.read_text(encoding="utf-8")
    blocks = segment(text)
    old_doc = {}
    if OUT.exists():
        try:
            old_doc = json.loads(OUT.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            old_doc = {}
    print(f"分段：{len(blocks)} 个案例块")

    k1, k2 = load_existing_keys()
    kept, excluded = [], []
    for i, b in enumerate(blocks, 1):
        case, rec = parse_case(b, i)
        if case is None:
            excluded.append(rec)
            continue
        raw = case.pop("_raw", {})      # 去重记录带上原始卦名，下一轮按键回指旧 id
        hx = case["hexagram"]
        d = case["input"]["date"]
        md = re.search(r"([%s])月([%s])([%s])日" % (BRANCHES, STEMS, BRANCHES), d)
        key1 = (hx["original"], hx["changed"], md.group(1), md.group(2) + md.group(3))
        key2 = (hx["original"], hx["changed"],
                tuple(case["expected"]["yingqi_branches"]), case["topic"][:6])
        if key1 in k1:
            excluded.append({"id": case["id"], "reason": "与在册案例同案（同卦变＋月建＋日柱），转录差异不补",
                             "topic": case["topic"], **raw})
            continue
        if key2 in k2:
            excluded.append({"id": case["id"], "reason": "与在册案例同案（同卦变＋应期支＋占题）",
                             "topic": case["topic"], **raw})
            continue
        kept.append(case)
        k1.add(key1)
        k2.add(key2)

    # 402 批：parser 扩块会改变临时序号；按旧册键保留 id，新条目取 max+1。
    kept, excluded = assign_stable_ids(kept, excluded, old_doc)
    # 419 批：建器不产出的书证字段按空位沿用旧册——403 批重建曾把 206/208 批的
    # 18 例用神书证整段清空（无门拦得住），此处堵死再犯。
    old_by_id = {c.get("id"): c for c in (old_doc.get("cases") or [])}
    for c in kept:
        oc = old_by_id.get(c.get("id"))
        if oc:
            merge_old_expected(c, oc)

    if args.why:
        _want = set(args.why)
        _hit = {c["id"]: "KEPT" for c in kept}
        _hit.update({e["id"]: e["reason"] for e in excluded})
        print("按 id 查去留：")
        for i in args.why:
            print(f"  · {i}: {_hit.get(i, '★ 不在任何一份名单里（segment 未产出该块）')}")
    if args.reject_stats:
        import re as _re
        from collections import Counter as _C
        def _bucket(r: str) -> str:
            # 归并到「哪一道门」——剔除理由文案前后改过，故按关键词归桶而不是按整串
            for k, name in (("无应期锚", "应期锚缺失"), ("应期锚只剩", "应期锚不可评（只剩占测日）"),
                            ("同案", "与在册同案"),
                            ("卦名不可解析", "卦名不可解析"), ("无六爻渲染", "无六爻渲染（非占验）"),
                            ("日期", "日期不可还原"), ("弱日期", "日期不可还原")):
                if k in r:
                    return name
            return "其他：" + r[:24]
        cnt = _C(_bucket(e["reason"]) for e in excluded)
        print(f"剔除归因（共 {len(excluded)} 例）：")
        for name, c in cnt.most_common():
            print(f"  {c:>4}  {name}")
        # 应期锚缺失再拆一层：书里真没写验期，还是规则没配上（381 批实测，见 CHANGELOG）
        import re as _re2
        _sub = _C()
        for _e in excluded:
            if "无应期锚" not in _e["reason"]:
                continue
            _i = int(_e["id"][2:])
            _b = blocks[_i - 1]
            _m = _b["case"]
            _body = _m.string[_m.start():_b["end"]]
            _rows = [x for x in _body.splitlines() if YIN_YANG_RE.search(x)]
            _tail = _body[_body.find(_rows[-1]) + len(_rows[-1]):] if _rows else _body
            _cut = len(_tail)
            for _cm in CHAPTER_RE.finditer(_tail):
                _ls = _tail.rfind("\n", 0, _cm.start()) + 1
                if _tail[_ls:_cm.end()] == _cm.group(0):
                    _cut = min(_cut, _ls)
            _sents = [x for x in _re2.split(r"[。；\n]", _tail[:_cut]) if x.strip()]
            _has_date = [x for x in _sents if _date_tokens(x)]
            _has_out = [x for x in _sents if OUTCOME_RE.search(x)]
            if not _has_date:
                _sub["① 书里没写验期（真没有）"] += 1
            elif _has_out:
                _sub["② 结果词与日期跨句（须逐条读）"] += 1
            else:
                _sub["③ 有日期无结果词（结果词表外）"] += 1
        print("  —— 应期锚缺失 %d 条再拆：" % sum(_sub.values()))
        for _n, _c in _sub.most_common():
            print(f"       {_c:>4} {_n}")
        # ② 类逐条读（382 批实测）：结果句自带日期的只有 1 条，且是「申时」——
        # 时辰档在引擎与评分里都没有（既有登记：evaluate._expected_unit 把 时/时 归日池近似），
        # 故 ② 类**可回收 0 条**；其余结果句是评注（野鹤曰/觉子曰/黄金策/应期章有注）
        # 或无验期的后果叙述。这一层把「18 条跨句」的可读性留给复核者。
        _cross = []
        for _e in excluded:
            if "无应期锚" not in _e["reason"]:
                continue
            _i = int(_e["id"][2:])
            _b = blocks[_i - 1]
            _m = _b["case"]
            _body = _m.string[_m.start():_b["end"]]
            _rows = [x for x in _body.splitlines() if YIN_YANG_RE.search(x)]
            _tail = _body[_body.find(_rows[-1]) + len(_rows[-1]):] if _rows else _body
            _cut = len(_tail)
            for _cm in CHAPTER_RE.finditer(_tail):
                _ls = _tail.rfind("\n", 0, _cm.start()) + 1
                if _tail[_ls:_cm.end()] == _cm.group(0):
                    _cut = min(_cut, _ls)
            _sents = [x.strip() for x in _re2.split(r"[。；\n]", _tail[:_cut]) if x.strip()]
            _hd = [x for x in _sents if _date_tokens(x)]
            _ho = [x for x in _sents if OUTCOME_RE.search(x)]
            if not (_hd and _ho):
                continue
            _d_here = [x for x in _ho if _date_tokens(x)]
            _shi_here = [x for x in _ho if not _date_tokens(x)
                         and _re2.search(r"[子丑寅卯辰巳午未申酉戌亥].{0,2}时", x)]
            if _d_here:
                _cross.append((_e["id"], "结果句自带日期（可回收）", _d_here[0][:40]))
            elif _shi_here:
                _cross.append((_e["id"], "结果句是时辰（时辰档不可评）", _shi_here[0][:40]))
            else:
                _cross.append((_e["id"], "结果句无日期（评注／无验期叙述）", (_ho[0][:34] if _ho else "")))
        if _cross:
            _rec = [c for c in _cross if c[1].startswith("结果句自带日期")]
            _shi = [c for c in _cross if c[1].startswith("结果句是时辰")]
            print(f"       —— ② 类 {len(_cross)} 条逐条读：自带日期 {len(_rec)} 条／"
                  f"时辰 {len(_shi)} 条／无日期 {len(_cross) - len(_rec) - len(_shi)} 条"
                  f" ⇒ **可回收 {len(_rec)} 条**")
            for _cid, _why, _txt in _cross:
                print(f"          {_cid} {_why}：{_txt}")
        _recov = sum(c for n, c in cnt.items() if n in ("应期锚缺失", "卦名不可解析", "日期不可还原"))
        print(f"  —— 其中「可修但未修」的候选（应期锚/卦名/日期三类）共 {_recov} 例；"
              f"其余是「同案重复」或「非占验文本」，改了也进不来。")
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
             "锚句归属本案（块内又起他卦的静卦，锚句理据引用本案渲染没有的支即属后卦）、",
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
              "本通道与 build_yingqi_set.py（case_library.md 通道）平行：同七道门纪律、同外部集身份。",
              "与在册案例同案者一律剔除——重复计数是八字科 #39 的病灶，外部集扩样先过这一关。", ""]
    # 379 批：「dry-run」此前并不 dry——它照样把审计报告写回 docs/。后果不是"多一个文件"，
    # 而是**探测动作会改仓库**：378 批只是跑了几次 --dry-run 查 id，就把该文档的日期戳
    # 从 2026-10-12 改成 2026-10-30 并混进了提交。现按语义分开：dry-run 只算不写。
    if args.dry_run:
        print("（--dry-run：审计报告未写盘；去掉该参数才落 %s）" % REPORT.relative_to(HERE.parent))
    else:
        REPORT.write_text("\n".join(lines), encoding="utf-8")
        print("审计报告 →", REPORT.relative_to(HERE.parent))

    if args.dry_run or not kept:
        return 0

    OUT.write_text(json.dumps({"_meta": {
        "description": "《增删卜易》殆知阁转录本抽取的应期外部验证集；七道门＋同案去重；永不参与调参",
        "built_by": "dev_tools/build_zengshan_dz_cases.py",
        "source_sha256": hashlib.sha256(SRC.read_bytes()).hexdigest(),
        "total_cases": len(kept),
        "excluded": excluded,
    }, "cases": kept}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n写入 {OUT.relative_to(HERE.parent)}（{len(kept)} 例）")

    sp = json.loads(SPLITS.read_text(encoding="utf-8")) if SPLITS.exists() else {}
    sp["zengshan_dz_holdout"] = [c["id"] for c in kept]
    # 幂等：早版每次重建都往 note_externals 追加同一句（二次运行即出现重复片段，
    # case_splits.json 里已留着两条）。只在缺失时补，杜绝第三次。
    _note_frag = "zengshan_dz_holdout=增删卜易 dz 底本通道，永不参与调参"
    if _note_frag not in sp.get("note_externals", ""):
        sp["note_externals"] = (sp.get("note_externals", "") +
                                "；" + _note_frag).lstrip("；")
    SPLITS.write_text(json.dumps(sp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("case_splits.json 已登记 zengshan_dz_holdout")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
