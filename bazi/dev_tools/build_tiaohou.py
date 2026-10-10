# -*- coding: utf-8 -*-
"""《穷通宝鉴》调候用神表构建器（一次性数据构建，产物入库、脚本留档可复跑）。

输入  data/sources/qiong-tong-bao-jian.wikitext.txt（维基文库原文，provenance 同目录）
输出  data/tiaohou_quotes.json   逐格 {main, assist, quote, section}——引文逐字保留，
                                铁律三口径：expected 必须能指回原文。
      stdout                     全表人审清单（月支 × 日干 → 主/佐 + 引文摘句）

提取规则（宁缺勿滥）：
  1. 按 `== 论X干 ==` 切分为每干大段；大段内再按 `=== 三X X干 ===` 记录季节段。
  2. 每 (月令, 日主) 取用神，优先级：
       a) 精确 `'''N月X干'''` 头（含其后 1-2 行 prose）命中即停；该层允许**宽松模式**
          （月令归属已由书源标题确定，只点主神亦可，assist 如实留空）；
       b) 该干大段内**逐句**检索明确提及该月词的句子（如「正月…」「冬月…」），
          命中即停（避免把别月处方错归到本月）；此层**不用**宽松模式；
       c) 季节段兜底：**仅当该 (月令, 日主) 没有精确月头时**才启用，且只用整季总论句
          （via=season，已知可能过泛）。若书中有月度专属规则而本层解析不出，
          则留空——不用季通则覆盖月度专属规则，避免口径不诚实。
  3. 禁止从引擎口径反推——本脚本只读原文；引文必须为原文子串（自动校验）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
# 内核路径必须由 DISC 反推（`Path(__file__).parents[2]` 会落到 `disciplines/` 而非仓库根，
# 在未 `pip install -e .` 的环境里直接 ModuleNotFoundError——本脚本此前正是如此）。
sys.path.insert(0, str(DISC.parent.parent / "core"))
from yishu_core.symbols import HEAVENLY_STEMS  # noqa: E402  天干序唯一真值源
from yishu_core import corpus_kit  # noqa: E402  语料可复现性比对
SRC = DISC.parent.parent / "data" / "sources" / "qiong-tong-bao-jian.wikitext.txt"
OUT = DISC / "data" / "tiaohou_quotes.json"

# `HEAVENLY_STEMS` 是 **list**：直接 f-string 插进字符类会变成
# `['甲', '乙', …, '癸']]` —— 类在首个 `]` 处提前闭合，多出一个必须匹配的字面 `]`，
# 于是「== 论癸水 ==」这类标题**永远不匹配**（实测采集到 0 段、重跑会把整个
# tiaohou_quotes.json 写成 120 个空格）。必须先 "".join 成字符串（同 ming 另一建器口径）。
STEMS = "".join(HEAVENLY_STEMS)
STEM_RE = f"[{STEMS}]"
MONTH_NAMES = {"正": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
               "七": 7, "八": 8, "九": 9, "十": 10, "冬": 11, "腊": 12}
ELEMENT_CHAR = "木火土金水"
MONTH_WORD = {1: "正", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六",
              7: "七", 8: "八", 9: "九", 10: "十", 11: "冬", 12: "腊"}
SEASON = {"三春": [1, 2, 3], "三夏": [4, 5, 6], "三秋": [7, 8, 9], "三冬": [10, 11, 12]}
BRANCH_OF_MONTH = {1: "寅", 2: "卯", 3: "辰", 4: "巳", 5: "午", 6: "未",
                   7: "申", 8: "酉", 9: "戌", 10: "亥", 11: "子", 12: "丑"}

# 条件/随宜命题句标记：命中即整句否决（宁缺勿滥）。这些句子给出的是「按旺衰/格局择一」
# 的条件规则而非该月令的固定主神，抽取任一位当唯一处方都是口径失真。
CONDITIONAL_MARKERS = ("随宜酌用", "随宜", "看旺衰", "或用", "不拘")

# 从格特例标记：弃命从杀/从财/从化等**特殊格局**的讨论句，不是该月令的调候通则。
# 例：十一月丁火整段在讲「此作弃命从杀…此格用戊」，取「用戊」当通用主神是口径失真。
# 但必须排除**否定式从格**（「不能从杀」= 不从，仍按常规用神论），否则会把正常月份整段否掉：
# 六月癸水「故癸水不能从杀，所以专用庚辛」正是该月的正常通则。
SPECIAL_GRADE_MARKERS = ("弃命从", "从杀", "从财", "从儿", "从化", "从强", "从格")
NEGATED_FROM_MARKERS = ("不能从", "不似从", "非从", "难从", "不作从", "未从",
                        "不惯从", "无从", "毋从", "弗从", "不可以从", "无从化", "不作化")

# 否定式标记分两档：
#  · 双字否词（不宜/不可/不用/忌/勿/莫/弗）—— 允许 6 字窗口。它们本身成词，其附近的
#    「用X」几乎必然是被否定的用法（十一月乙木「**不宜用**癸以冻花木，故耑用丙火」）。
#  · 单字「不」—— 只允许 **2 字**窗口。文言里「不」频率极高，实测把
#    「辛无己**不**生，故壬己并用」中的正确处方「壬己并用」误杀（5辛 由壬己变空）。
# 注意**不含「无」**：「无」在文言中满篇皆是（无壬、无癸、无湿…），作否词会大面积误杀。
NEGATION_MARKERS = ("不宜", "不可", "不用", "忌", "勿", "莫", "弗")
NEGATION_SINGLE = ("不",)
NEGATION_WINDOW = 6
NEGATION_WINDOW_SINGLE = 2
# 子句分隔符：否定窗口**不得跨越**这些字符。否则前一分句的否定会误杀后一分句的处方
# —— 实测九月戊土「不可专用丙，先看甲木，次取癸水」：「不」距「先看」3 字，
# 跨过「，」后把正确的「先看甲木」否掉，只剩宽松模式捞到「癸」。
CLAUSE_BOUNDARY = "，。；、：？！"

# ---- 用神句模式（有序，命中即停）。十干单字 + 可选五行字缓冲。 ----
S = STEM_RE
PATTERNS = [
    (re.compile(rf"先({S})后({S})"), "先X后Y"),
    (re.compile(rf"先取({S})[^，。；]*，次[用取]({S})"), "先取X次Y"),
    # 「仍取丁甲，次取丙火照暖」（十一月庚金）／「先看甲木，次取癸水」（九月戊土）
    (re.compile(rf"[仍先]取({S}){STEMS}?[^，。；]*，次[用取]({S})"), "取XY次Z"),
    (re.compile(rf"先看({S})[^，。；]*，次取({S})"), "先看X次取Y"),
    # 「先癸后丁」（四月甲木）——注意与上面「先X后Y」顺序：先字在前者更明确
    (re.compile(rf"先({S})[^，。；]*，次[用取]({S})"), "先X次Y"),
    # 以丙火为先，癸水次之 / 丙火为先，庚金次之（“次之”变体）
    (re.compile(rf"以?({S})[火木土金水]?为先[，,]?[^，。；]*?({S})[火木土金水]?次之"), "X为先Y次之"),
    (re.compile(rf"({S})[火木土金水]为尊，[^，。；]*({S})[火木土金水]次之"), "X为尊Y次之"),
    (re.compile(rf"({S})[火木土金水]为先，次[用取]({S})"), "X为先次Y"),
    (re.compile(rf"({S})[火木土金水]为主，[^，。；]*({S})[火木土金水]为佐"), "X主Y佐"),
    (re.compile(rf"用({S})[火木土金水]?，[^，。；]*佐以({S})"), "用X佐Y"),
    # 「壬水为最，戊土佐之」（十一月丙火）／「丁先庚后，丙火佐之」（十一月甲木）：
    # 明确给出主→佐的**处方次序**，必须排在下面「透干条件句」之前——否则
    # 「十一月甲木」同段里的「庚丁两透」（描述富贵格成立条件，非处方）会抢先命中，
    # 把主神误取成庚。
    (re.compile(rf"({S})[火木土金水]?为最[，,]?[^，。；]*?({S})[火木土金水]?佐之"), "X为最Y佐之"),
    (re.compile(rf"({S})先({S})后，[^，。；]*?({S})[火木土金水]?佐之"), "X先Y后Z佐"),
    # 反序句式：「非丁莫造，非丙不暖」（十月庚金）= 丁为主、丙为辅。
    # 前句「非X莫造」里 X 落在否定标记「莫」之前，需用负向回顾 (?<!莫) 排除误取。
    (re.compile(rf"非({S})[火木土金水]?(?<!莫)莫造，[^，。；]*非({S})[火木土金水]?不"), "非X莫造Y不"),
    # ---- 以下为「透干/格局条件句」：描述某格成立的条件，不是该月令的用神处方，
    # 故排在上面处方句之后（否则抢命中，把条件句里的字误当主神）。 ----
    (re.compile(rf"({S})({S})两透"), "XY两透"),
    (re.compile(rf"得({S})({S})"), "得XY"),
    (re.compile(rf"({S})({S})并用"), "XY并用"),
    (re.compile(rf"({S})({S})兼全"), "XY兼全"),
    # 「六月用壬，但借庚金为佐」——「借X为佐」给出的是**佐神**，主神在「用壬」。
    # 故必须排在单干「专用X」之前，且作为「用X + 借Y为佐」的**整体**模式，
    # 否则「借庚金」会被当成主神（实测返回 庚 而非 壬）。
    (re.compile(rf"用({S})[火木土金水]?[^。；]*?借({S})[火木土金水]?为佐"), "用X借Y为佐"),
    # 「退气，三伏生寒，壬水为用，取庚辅佐」（六月丙火）——「取X辅佐」= 佐神。
    (re.compile(rf"({S})[火木土金水]?为用[^。；]*?取({S})[火木土金水]?辅佐"), "X为用取Y辅佐"),
    # 「三冬丁火微寒，耑用庚甲」——「耑用」后接**两个相邻干字**（庚甲），
    # 第二干既无五行字也无「次/为佐」标记，只能靠相邻双干捕获。
    (re.compile(rf"(?:专|耑|姑|宜)(?:用|以|取)?({S})({S})(?:[，。；]|$)"), "耑用XY"),
    # 「专取甲木，壬水次之」（六月之丁）——「专取」+「X次之」整体模式。
    # 必须排在单干「专用X」之前，否则「专取甲木」会先命中、丢掉次之的壬。
    (re.compile(rf"(?:专|耑|姑|宜)(?:用|以|取)({S})[火木土金水]?[，,]?[^，。；]*?({S})[火木土金水]?次之"), "专取XY次之"),
    # 「五月癸水，庚辛壬参酌并用可也」（行2058）——**三干并列**「参酌并用」。
    # 契约只承载 main+assist 两槽，故取前两干（庚→辛），第三干壬由引文逐字保留可追。
    # 不加此模式时该句四种模式全不命中 → 5癸 整格留空（书源有明确处方却采不到）。
    (re.compile(rf"({S})({S})({S})参酌并用"), "XYZ参酌并用"),
    # 单主神：专用/耑用/姑用/宜用 X / X为用 / X为尊(可无五行字) / 独爱X
    (re.compile(rf"(?:专|耑|姑|宜)(?:用|以|取)?({S})[火木土金水]?"), "专用X"),
    (re.compile(rf"({S})[火木土金水]?为用"), "X为用"),
    (re.compile(rf"({S})[火木土金水]?为尊"), "X为尊"),
    (re.compile(rf"独爱({S})[火木土金水]?"), "独爱X"),
]

# 宽松模式：**只用于精确 `'''N月X干'''` 月头块内**。理由：月令归属在该块内已由书源
# 标题确定，不存在「把别月处方错归本月」的风险；因此可以接受只点主神、不点佐神的
# 句子（如「非庚不能劈甲…姑用庚金」），由 assist=None 如实留空，而不是错落到季节通则。
# 大段逐句检索与季节兜底**不得**使用宽松模式（归属不确定，必须严格）。
RELAXED_PATTERNS = [
    (re.compile(rf"(?:用|以|取|仗)({S})[火木土金水]?"), "用X(宽)"),
    # 「庚丁为要，丙火次之」（十月甲木）：双干并列「为要」，取前一位为主、后一位为佐。
    # 必须排在单干「X为要(宽)」之前，否则「庚丁为要」会只取到末字「丁」当主神。
    (re.compile(rf"({S})({S})为要"), "XY为要(宽)"),
    (re.compile(rf"({S})[火木土金水]?(?:为主|为要|为最|为急|为宜|为良)"), "X为要(宽)"),
    (re.compile(rf"非({S})[火木土金水]?不能"), "非X不能(宽)"),
]


def _negated(text: str, m) -> bool:
    """命中前的同子句窗口内若出现否定词，则该命中是被否定的用法（如「不宜用癸」）。

    窗口必须**截断在本子句开头**（不跨，。；、…），否则前一分句的否定会误杀后一分句的处方。
    """
    pre = text[max(0, m.start() - NEGATION_WINDOW):m.start()]
    cut = max(pre.rfind(c) for c in CLAUSE_BOUNDARY)
    pre = pre[cut + 1:] if cut >= 0 else pre
    if any(k in pre for k in NEGATION_MARKERS):
        return True
    pre1 = pre[-NEGATION_WINDOW_SINGLE:] if len(pre) >= NEGATION_WINDOW_SINGLE else pre
    return any(k in pre1 for k in NEGATION_SINGLE)


def try_extract(text: str, relaxed: bool = False):
    # 整句否决：条件/随宜命题句与从格特例段都不是该月令的调候通则（口径诚实，宁缺勿滥）
    if any(k in text for k in CONDITIONAL_MARKERS):
        return None, None, None
    if any(k in text for k in SPECIAL_GRADE_MARKERS) \
            and not any(k in text for k in NEGATED_FROM_MARKERS):
        return None, None, None
    for pat, name in PATTERNS:
        for m in pat.finditer(text):
            if _negated(text, m):
                continue
            main = m.group(1)
            assist = m.group(2) if pat.groups >= 2 else ""
            return main, assist, name
    if relaxed:
        for pat, name in RELAXED_PATTERNS:
            for m in pat.finditer(text):
                if _negated(text, m):
                    continue
                return m.group(1), "", name
    return None, None, None


def month_num_from_word(token: str) -> int | None:
    # 允许带「月」后缀（MONTH_TOKEN_RE 的捕获组形如「冬月」「十一月」）
    if token.endswith("月"):
        token = token[:-1]
    if token == "十一":
        return 11
    if token == "十二":
        return 12
    if token == "冬":
        return 11
    if token == "腊":
        return 12
    return MONTH_NAMES.get(token)


def mentions_month(sent: str, month: int) -> bool:
    """句子是否明确提及该月令（用于精确归属，避免错归）。

    必须用带 (?<!十) 负向回顾的正则，不能用朴素子串包含：`'''十二月辛金'''` 的句子
    含子串「二月」，朴素 `in` 会让**腊月辛金被误判成二月辛金**（已实测导致 2辛
    取到「先丙后壬」的腊月处方）。
    """
    m = MONTH_TOKEN_RE.search(sent)
    if not m:
        return False
    return month_num_from_word(m.group(1)) == month


def split_sentences(block: str) -> list[str]:
    return [s for s in re.split(r"[。；;！!？?]", block) if s.strip()]


# 显式月词（用于季节兜底时剔除「含具体月份」的句子，避免把某月专属句错归到同季另两月）。
# 负向回顾 (?<!十) 防止「十二月」被误判含「二月」。
MONTH_TOKEN_RE = re.compile(
    r"(?<!十)(正月|二月|三月|四月|五月|六月|七月|八月|九月|十月|冬月|十一月|十二月|腊月)"
)


def _has_month_word(sent: str) -> bool:
    return bool(MONTH_TOKEN_RE.search(sent))


# 维基文库示例盘（{| class="wikitable" … |}）里夹着大量「庚壬两透」一类成药例，
# 不是该月令的用神处方；检索前整段剔除，避免把示例误当处方。
WIKITABLE_RE = re.compile(r"\{\|.*?\|\}", re.S)


CONDITIONAL_QUALIFIER_RE = re.compile(rf"[甲乙丙丁戊己庚辛壬癸][甲乙丙丁戊己庚辛壬癸]"
                                       rf"{{1,3}}(?:两透|并用|兼全|齐透|俱透)")


def _is_pillar_condition(sent: str) -> bool:
    """是否为「XX两透/并用」式**透干成格条件句**。

    这类句描述「何种天干组合成格」，不是在说该月令该用哪几神；季节兜底里
    尤其密集（「丙甲两透，桃浪之人」「庚壬两透，科甲定然」）。若当处方用，会把
    富贵格条件错记成调候用神。
    """
    return bool(CONDITIONAL_QUALIFIER_RE.search(sent))


def _subject_stem(sent: str) -> str | None:
    """句子的**论说对象**日干：取句首「N月X干」/「三X X干」式主语里的干。

    季节段内会混入**别干**的通则句——如三秋丁火段第二段「三秋甲庚丙并用，仍分优劣」
    讲的是**甲木**而非丁火。季节兜底若不排除，会把甲木的处方错记到丁火格。
    """
    # 先试「三X X干」式（三秋甲庚丙并用 / 三秋丁火，退气柔弱），再试「N月X干」式。
    # 顺序要紧：若先试N月式，正则会因月字组可选而匹配空、误取「秋」等非干字符。
    m = re.match(rf"^三[春夏秋冬]([{STEMS}])", sent.strip())
    if m:
        return m.group(1)
    m = re.match(rf"^(?:十一|十二|[正二三四五六七八九十冬腊])月([{STEMS}])", sent.strip())
    if m:
        return m.group(1)
    return None


def _clean_block(text: str) -> str:
    return WIKITABLE_RE.sub(" ", text)


def build_table() -> dict:
    """书源 → 12 月 × 10 干 的调候引文表（纯计算，不落盘）。"""
    text = SRC.read_text(encoding="utf-8")
    lines = text.splitlines()

    cur_stem, cur_season = "", ""
    blocks: dict[str, list[str]] = {s: [] for s in STEMS}
    # 精确 `'''N月X干'''` 头 → 该头下的逐句原文（已逐句切分，保证每条 quote 是原文子串）
    exact_paras: dict[tuple[int, str], list[str]] = {}
    # 作者自述的**月度小结句**：`N月X干，专用X，次用Y` 独立成行（书源约 18 行）。
    # 权威性高于 `'''N月X干'''` 大段（大段含大量「若…则…」特例与示例盘），
    # 故作为最高优先级 a0 层。例如「九月壬水，专用甲木，次用丙火」是大段里
    # 「若一派壬水…斯用丙火」这句特例之外的**真正通则**。
    summary_lines: dict[tuple[int, str], list[str]] = {}
    # (月序, 日干) → 该月所属季节段名。**不能**用 season_for_stem[stem]：一个干下有
    # 四个 `=== 三X ===` 段，单值 map 会被**最后一个**段覆盖（三冬），于是三春/三夏/
    # 三秋的整季通则（如「三秋丁火，耑用甲木，仍取庚噼甲」）永远不可达。
    # 必须按月序反查该月实际落在哪个季节段。
    month_season: dict[int, str] = {}
    season_blocks: dict[tuple[str, str], list[str]] = {}  # (日干, 季名) → 该段正文行
    season_for_stem: dict[str, str] = {}

    # 作者自述月度小结句。`^` 前缀容纳两类行首引导词：
    #   「总之十月丙火，木旺宜庚，水旺宜戊，火旺用壬」（行558）——
    #   书源在一整段讲完后用「总之」收口重述该月通则，权威性等同月度小结句，
    #   但原文写「总之」而非直接以月名开头，此前整句漏出 a0 层。
    # 「(之)?」兼容「六月之丁」式异体（与月头层保持一致）。
    SUMMARY_RE = re.compile(
        rf"^(?:总之|故|凡)?((?:十一|十二|[正二三四五六七八九十冬腊])月)(?:之)?([{STEMS}])[{ELEMENT_CHAR}]?"
        rf"[，。][^=|\n]*"
    )

    for idx, ln in enumerate(lines):
        m = re.match(rf"^==\s*论([{STEMS}])[{ELEMENT_CHAR}]?\s*==\s*$", ln.strip())
        if m:
            cur_stem, cur_season = m.group(1), ""
            continue
        m = re.match(r"^===\s*(三[春夏秋冬])", ln.strip())
        if m:
            cur_season = m.group(1)
            season_for_stem[cur_stem] = cur_season
            # 记录本段覆盖的三个月→季节，供季节兜底按月取段
            for _mo in SEASON.get(cur_season, []):
                month_season[_mo] = cur_season
            continue
        if cur_stem:
            blocks[cur_stem].append(ln)
            if cur_season:
                season_blocks.setdefault((cur_stem, cur_season), []).append(ln)
        # 作者自述月度小结句（最高优先级层 a0）。排除 `'''…'''` 加粗标题与示例盘表格行。
        if not ln.strip().startswith(("'''", "|", "{|", "|}")):
            sm = SUMMARY_RE.match(ln.strip())
            if sm:
                snum = month_num_from_word(sm.group(1))
                sstem = sm.group(2)
                if snum and sstem:
                    summary_lines.setdefault((snum, sstem), []).append(ln.strip())
        # 精确 `'''N月X干'''` 头：收集该头所在行剩余文本 + 其后 1-2 行 prose，逐句切分
        # （跳过示例盘表格行，避免把成药例误当处方）
        hm = re.match(
            # 「一」必须在类内（顺序也重要：先「十一/十二」，再单字月）：
            # `'''十一月丙火'''`（十一月=11月）与 `'''十二月甲木'''`（十二月=12月）是两个
            # 不同月头。曾用 `[正二三四五六七八九十冬腊]+` 漏掉「一」，使所有
            # 「十一月X干」月头静默失配 → 该格错误回落到大段月词检索或季节兜底，
            # 取到「从杀」特例句（11丙 曾取到「宜用己土浊壬」）。
            # 「?之?」容纳书源唯一一处「之」式异体 `'''六月之丁'''`（专取甲木，壬水次之）——
            # 该句是**六月丁火的月度专属处方**，此前因月头不被识别而整格留空，
            # 且季节兜底被更泛的三夏通则抢先。异体写法有限（全书仅此一处），故窄匹配即可。
            rf"^'''(十一|十二|[正二三四五六七八九十冬腊])月(之)?([{STEMS}])[{ELEMENT_CHAR}]?'''\s*(.*)$",
            ln.strip(),
        )
        if hm:
            num = month_num_from_word(hm.group(1))
            stem = hm.group(3)
            if num is None:
                continue
            sents: list[str] = []
            if hm.group(4).strip():
                sents.append(hm.group(4).strip())
            j = idx + 1
            while j < len(lines) and len(sents) < 3 and lines[j].strip() \
                    and not lines[j].strip().startswith("'''") \
                    and not lines[j].strip().startswith("==") \
                    and not lines[j].strip().startswith(("|", "{|", "|}")):
                sents.append(lines[j].strip())
                j += 1
            exact_paras.setdefault((num, stem), []).extend(sents)

    table: dict[str, dict] = {}
    for month in range(1, 13):
        mw = MONTH_WORD[month]
        branch = BRANCH_OF_MONTH[month]
        for stem in STEMS:
            # 键 = 月序+日干（如 "4乙"）：**消费方契约**——narrate.py `_tiaohou_quote`
            # 与 core/yishu_core/evidence.py 均按「月序+日干」回索引文（见 evidence.py
            # 注释「引文按月序+日干键回指」）。注意这与引擎 TIAO_HOU 的「月支+日干」
            # 键空间不同，勿混。month 字段保留月支信息供人审。
            key = f"{month}{stem}"
            main = assist = ""
            how = ""
            quote = None
            section = None
            exact_flag = False

            # a0) 作者自述月度小结句（最高优先级）：`九月壬水，专用甲木，次用丙火`
            #     这类独立成行的通则句，权威性高于月头大段（后者含大量特例与示例盘）。
            for sent in summary_lines.get((month, stem), []):
                for sent2 in split_sentences(sent) or [sent]:
                    mm, aa, nn = try_extract(sent2, relaxed=True)
                    if mm:
                        main, assist, how = mm, aa, nn
                        quote = sent2
                        section = f"论{stem}·{mw}月（作者月度小结）"
                        exact_flag = True
                        how = (how or "") + "(summary)"
                        break
                if main:
                    break
            # a) 精确头。月令归属已由书源标题确定 → 允许宽松模式。但**必须两轮**：
            #    先把整块的**严格**模式扫完，再退回宽松。否则宽松模式会在前一句
            #    （多为「若…则用X」条件句）抢先命中，错过同块后文真正的通用处方
            #    （实测 9壬：前句「若一派壬水…斯用丙火」命中宽松，用掉了丙；
            #      后文「九月壬水，专用甲木，次用丙火」才是该月通则）。
            para = exact_paras.get((month, stem), [])
            for relaxed in (False, True):
                for sent in para:
                    mm, aa, nn = try_extract(sent, relaxed=relaxed)
                    if mm:
                        main, assist, how = mm, aa, nn
                        quote = sent
                        section = f"论{stem}·{mw}月"
                        exact_flag = True
                        break
                if main:
                    break
            # b) 大段内逐句按月词检索（剔除示例盘后检索，保证 quote 是原文逐字子串）
            if not main:
                for s in split_sentences(_clean_block("\n".join(blocks[stem]))):
                    if mentions_month(s, month):
                        mm, aa, nn = try_extract(s)
                        if mm:
                            main, assist, how = mm, aa, nn
                            quote = s.strip()
                            section = f"论{stem}（{season_for_stem.get(stem, '')}）"
                            break
            # c) 季节段兜底（**仅当该格无精确 `'''N月X干'''` 月头时**才启用）。
            #    口径理由：书中若给出月度专属规则，它可能与整季通则**相矛盾**；用季通则
            #    覆盖月度专属规则属于口径不诚实。故精确月头存在但解析不出时宁可留空，
            #    也不回落到季节兜底。仅使用「整季总论句」（不含任何月词），
            #    并优先选能给出「主+佐」的句子（季论常先点主神、后补佐神）。
            if not main and (month, stem) not in exact_paras:
                seas = month_season.get(month, "")
                if seas:
                    #只在该月所属季节段内检索（不是整干大段）：整干大段会把别季
                    # 的通则混进来，对同一格产生季节错配。
                    best = None  # (has_assist, main, assist, how, quote)
                    for s in split_sentences(_clean_block(
                            "\n".join(season_blocks.get((stem, seas), [])))):
                        if _has_month_word(s):
                            continue
                        # 跳过论说**别干**的句子（三秋丁火段里混有甲木的通则句）
                        subj = _subject_stem(s)
                        if subj is not None and subj != stem:
                            continue
                        # 兜底层排除「XX两透/并用」式成格条件句（非用神处方）
                        if _is_pillar_condition(s):
                            continue
                        mm, aa, nn = try_extract(s)
                        if mm and (best is None or (not best[0] and aa)):
                            best = (bool(aa), mm, aa, nn, s.strip())
                    if best:
                        main, assist, how = best[1], best[2], best[3]
                        quote = best[4]
                        section = f"论{stem}·{seas}（季节总论，过泛慎用）"
                        how = (how or "") + "(season)"

            table[key] = {
                "month": month, "branch": branch, "stem": stem,
                "main": main or None, "assist": assist or None,
                # 引文保留完整原句（铁律三：必须能指回原文子串，截断会破坏可验证性）
                "quote": quote,
                "section": section, "via": how or None,
                "exact_paragraph": exact_flag,
            }

    # 引文可验证性自校验：任何 quote 必须能在原文中逐字找到，否则视为臆造，强制置空
    # （宁缺勿滥）。本步在 build_table 内完成，保证 --check 与落盘产物完全一致、可复现。
    src = SRC.read_text(encoding="utf-8")
    for k, v in table.items():
        if v.get("quote") and v["quote"] not in src:
            v["main"] = v["assist"] = None
            v["quote"] = v["via"] = None
            v["exact_paragraph"] = False

    return table


def main() -> int:
    ap = argparse.ArgumentParser(description="《穷通宝鉴》调候用神引文层提取（默认写盘）")
    ap.add_argument("--check", action="store_true",
                    help="不落盘，只比对已入库 data/tiaohou_quotes.json 是否与重算一致")
    args = ap.parse_args()

    table = build_table()
    if args.check:
        return corpus_kit.report(OUT.name, corpus_kit.check(OUT, table))

    OUT.write_text(json.dumps(table, ensure_ascii=False, indent=1), encoding="utf-8")

    # 人审清单
    ok = sum(1 for v in table.values() if v["main"])
    season = sum(1 for v in table.values() if v["main"] and (v["via"] or "").endswith("(season)"))
    print(f"提取 120 格，命中主神 {ok} 格，N/A {120 - ok} 格 → {OUT.name}")
    print(f"（其中季节兜底 {season} 格，via 标记 season，已知可能过泛）")
    # 人审清单（按月支分组显示，键为月序+日干）
    for month in range(1, 13):
        br = BRANCH_OF_MONTH[month]
        row = []
        for stem in STEMS:
            v = table.get(f"{month}{stem}")
            if not v or not v["main"]:
                row.append(f"{stem}:—")
            else:
                tag = "" if v["exact_paragraph"] else ("~" if (v["via"] or "").endswith("(season)") else "·")
                row.append(f"{stem}:{v['main']}{('/' + v['assist']) if v['assist'] else ''}{tag}")
        print(f"  {br}({month})  " + "  ".join(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
