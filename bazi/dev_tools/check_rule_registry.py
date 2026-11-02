# -*- coding: utf-8 -*-
"""规则注册表的书源指针回验器：`verified: true` 不许是自说自话。

为什么需要它（2026-10-10）：`core/yishu_core/ming_tables.py` 头注写着
「指针由 tests/test_ming_rule_registry.py 回验」——该测试文件**全仓不存在**，
bazi 也没有 tests/ 目录。也就是说 `rule_registry.json` 里每一条
`"verified": true` 从写下那天起没有任何东西复核过。本器把这条声明变成真话：

    python dev_tools/check_rule_registry.py             # 校验
    python dev_tools/check_rule_registry.py --selftest  # 负例：证明本器抓得住假 verified

校验三类指针（两科 schema 同源 `yi-rule-registry-v1`）：
  · `source.quote_in_data` = "<file>#<a.b.c>"   → 文件在、点分路径可解析、值非空；
        若同条带 `corpus_files`，则该值须**逐字命中**其中至少一份语料（归一化后）；
  · `source.quote_in_code` = "<file>#<text|IDENT>" → 目标文件里能找到该字串，
        或该标识符作为名字存在（`BING_YAO_THESIS` 这类是常量名，不是引文）；
  · `source.corpus_files` 自身必须存在；
  · 【362 批】`source.quote_in_source` = "<底本>:<行号>" → 该行逐字含本条 `quote`
        （quote2/quote3 同理）。写了行号就是在声称「引文在此」，故不看 verified 一律判红——
        此前本形态无人守，六爻 2 条 `verified=false` 因此长期挂着（362 批回验 4/4 命中后转真）；
  · **【第一百六十八批】`impl`** = "<file>.py[:symbol]" → 文件在，且 `:标识符` 形态时
        该符号确在文件内（`:1058`／`:4.3` 是定位记号不是符号，跳过）。此前本器从不看
        `impl`，六爻科同批实抓到两条悬空指针，本科是同一潜在缺口，本批两侧拉齐。
`verified: true` 而上述任一步失败 → 判红；`verified: false` 只作 NOTE（那是诚实的未核实）。
**`impl` 例外：不看 `verified` 一律判红**——代码指针不存在「诚实未核实」状态，指错就是指错。

447 批追加（仅六爻册；八字无此文件时跳过）：`qianjin_fu_map.json` 的**统计块自洽**——
`统计.联句总数` 必须等于 `联句映射` 条数；每个状态分项必须等于实际条目数（状态允许
`已落地_<机制>_<日期>` 后缀，按 `_` 前前缀计数）；统计键必须是 `_meta` 状态词汇的子集，
词汇表里的每个状态也必须出现在统计里（防漏项）；`registry_未被本表联句直接挂上`
里的 id 必须都存在于 `rule_registry`。本批首跑抓到 `_meta` 仍写「四态」而实际条目已用
第五态「已落地」——文档与实际状态词汇分家（§六.2），同批改为「五态」。

457 批追加：**逐联书源回指**。`_meta.纪律` 写着「联句与 src 逐字从书源抄来」，但 447
只核统计块，100 条联句与行号从未对拍。现按 [14] 同口径（所指行 ±2 行拼接、去空白标点）
逐条验证：`src` 必须带行号（`L8` 或 `《黄金策》源L124…`），行号须在底本范围内，联句须
在该行邻域逐字命中。首跑 100/100 全符（0 处改值）。

462 批追加（仅八字册）：**大运起例引文库的行锚**。`dayun_quotes.json` 自称「引文必须与
`corpus_line` 那一行逐字一致」，而本器此前只验 quote_in_data「值在语料某处出现过」，
不看行号——声明比门宽。现按该声明核对：`_provenance.source_file` 在盘、`corpus_line`
在册、`quote` 落在该行（[14] 同归一化）。两科 selftest 都跑夹具（六爻无此册则跳过）。

465 批追加（仅八字册）：**裁决引文书源回验**。`data/verdicts.json` 自称「书源引文唯一
真值源」：20 个字段带 `locator`（`data/sources/<书>:<行>`），4 条分支总则（病药 thesis、
化格/从格 verse）在 `_meta` 声明了底本。此前 [12] 只回指 `病药引文.thesis` 一个点，
locator 从未被读取。现按声明核对：行号在册、`quote/full_quote/cond_quote/verse_quote`
落在该行；分支总则逐行命中声明底本（不跨行拼接）。两科 selftest 都跑夹具。

466 批追加（仅八字册）：**六神取象/十神作用的行号出处**。`liushen_image.json` 声明
「值只收逐字引文与行号」，但实抓到两条 `取象` 是注释式改写且无 `_src`，`narrate`
仍按引文渲染出空行号（§六.3）。现核：每个非空 `能力/构成/取象/别名` 必须有
`<字段>_src`、行号在册、值落在该行；`shi_shen_actions` 每条 `source` 必须能解析
行号（`L####` 或 `:####`），`actions` 每项落在该行 ±3 行邻域。两科 selftest 都跑夹具。

467 批追加（仅六爻册）：**引文库 `quote_kind`**。`liuyao/data/verdicts.json#quote_database`
旧称「引文库，source 字段为古籍出处」，全库实测 49 条仅 1 条逐字可回原文，其余 48 条
是今译。现要求每条声明 `quote_kind`：`verbatim` 必须带 `source_ref`（`file[:line]`）
且逐字命中（折叠标点）；`paraphrase` 只要求非空 `source`（所本篇章）。报告层标题
沿用「经典引文」的问题登记为下一批（468）。两科 selftest 都跑夹具。

469 批追加（仅六爻册）：**六亲持世括注口径**。`shi_yao_interpretation` 19 条断语
文末标「（《火珠林·X章》）」，全库实测无一条逐字（全是今译）。现要求今译标记
改为 `（据《…》今译）`，出现裸 `（《…》）` 即判红；标记数下限 19。两科 selftest 都跑夹具。

470 批追加（仅六爻册）：**叙述层持世引文的行锚**。`narrative_templates.json` 的
`pattern_hints._wenwang_chishi._meta` 明写「每条 quote 为底本逐字子串，src 为主源行号」，
但 14 个 quote/补 字段此前无门（[14] 认「源L」形态，这里的 `file:NNNN` 不在扫描面）。
现核 `src`/`补_src` 行号在册、值落在该行；字段数下限 14。两科 selftest 都跑夹具。

485 批追加（仅六爻册）：**分占域判据引文库的章界回验**。`domain_citations.json` 的
`_extension_note` 自称「N 域逐字引文（一行一锚一逐字，行号均可回指底本）」，但该册
`consumed_by_engine=false`、全仓无代码读取，132 个 L 引用从未被任何门回验。现核：
每域 `章节` 的「L#### 起」必须正落在该章标题行，`引文` 的「源L#### 逐字「…」」须在
本章行界内且逐字命中；`_source_lines` 若带行号须与 `章节` 同锚；`_extension_note`
声明的域数须等于实际域数。首跑抓到「神听」锚在 L1262（用人章注文行）、引文取 L1263
的用人章六神句——整个域错章。两科 selftest 都跑夹具。

487 批追加（仅六爻册）：**叙述层自由文本字段的内联引用**。
`pattern_hints.liu_shen_chishi.歌源` 是一条摘要字符串（`L465-L470`＋六神各一段
`'…'`），`pattern_hints.yigua_yishi.口径` 是散文（`源L31「…」`／裸 `源L1802`），
两者都不是 476 的 `quote/src` 结构，此前无门。现核：歌源的范围端点、六个
`名＝'…'` 片段逐行对应且逐字命中；口径的每个 `源L####（「…」）` 行号在册、
带引文者逐字命中（书别取同组 `src` 的底本）。首跑 13/13 全符、0 处漂移
（L31 的长句含「但有一卦爻逢六冲或卦变六冲」，此前只核过同组的 6 个
`src`，摘要句本身从未对拍）。两科 selftest 都跑夹具。

488 批追加（仅六爻册）：**问题题类表注记里的书源引用**。
`question_classes.json` 的 `classes[*].source_gates`／`note` 有 4 个 `源L####`
（L2219/L2221、L1953、L1541），其中 3 处带 `「…」` 引文，此前无门——题类析出
与天气分轨的「书据」全靠人读。现核：每个 `源L` 的书名取同串最近《…》、
经 provenance 解析（同名多本 `_dz` 优先）、行号在册；锚后到下一锚之间的首个
`「…」` 须在该行逐字命中。首跑 4/4 行锚、3/3 引文全符（0 处漂移）。
两科 selftest 都跑夹具。

489 批追加（仅八字册）：**裁决表散文里的裸行号**。`bazi/data/verdicts.json`
除 465 的 `locator` 字段与 480 的内联`源L「…」`外，还有 12 处只写行号、
不带引文的散文锚（`_zhuan_wang_meta` 五格 L1657…、`_meta` L5265、
`cong_sha/cong_cai.note` L1668/L1704、`看命口诀` L5115/L5137、
杂气格 L1734、渊海子平 L179）。这些是「哪一段是哪一格的书源」的定位声明，
此前无门。现核：带 `data/sources/<书>` 的按路径、带《书名》的按 provenance、
裸 `源L` 按同条目 `locator` 底本，行号在册；紧邻 `「` 的锚已由 479/480 覆盖，
本门不重复判。首跑 12/12 在册（0 处越界）。两科 selftest 都跑夹具。

491 批追加（仅六爻册）：**用神词典族注里的「…」引文**。
`question_use_gods.json` 的构建器明写「note 不参与核验」，family 64–69 的
`note` 有 7 段 `「…」`（占雨/借贷/讨债/六畜/坟墓），都称「章内逐字」却无行号
锚（`[14]` 只认 `源L` 形态，只核到 1 条）。现核：每段 `「…」` 须在
《增刪卜易》dz＋wikitext 任一底本中逐字出现（省略号分段）；首跑 7/7 命中。
两科 selftest 都跑夹具。

493 批追加（仅六爻册）：**用神词典 `_meta` 声明数**。`question_use_gods.json`
的 `_meta.description` 仍写「195 条现代问法」，而 `family_count=74`、
`key_count=275`、落盘 entries 合计 275——同一份元数据里两个数自相矛盾，
构建器也照抄 195 写入。现核：`family_count == len(families)`、
`key_count == Σentries`、`description` 里的「N 条现代问法」== 实际键数。
首跑即抓到 195≠275。两科 selftest 都跑夹具。

494 批追加（两科书目解析）：**同书异名归一**。《命理探源》在库底本标题作「命理探源」，
而八字代码/资料另有写作「命理探原」的（袁树珊书两版题名，学界两写并存）。
此前 `_corpora_for_book` 只按字面匹配，`《命理探原》源L605` 因此被当作无书名，
486/490 的行号检查都跳过了它。现加书目别名表（命理探原→命理探源），
两个解析函数统一走 `_book_key`；L605 因此归入可解析并受行号检查。
两科 selftest 都跑夹具。

492 批追加（仅八字册）：**注册表「语料行 NNNN」声明**。
`bazi/data/rules/rule_registry.json` 有 3 处不以 `L####` 写的行号声明：
`ming.dayun.locator` 的「语料行 2608/2612」与 `_uncovered[1].locator` 的
「语料行 2452」。465 只看 verdicts、474 只跑六爻，这些声明此前无门。
现核：底本取同串 `data/sources/<书>` 路径、否则 `source.corpus_files`、
否则 `source.book` 经 provenance，行号须在册；首跑 3/3 在册。两科 selftest 都跑夹具。

490 批追加（仅八字册）：**代码注释里的 `《书名》源L####「…」`**。
`bazi/scripts/**/*.py` 与 `bazi/core/**/*.py` 有 51 个 `源L` 锚（`dayun.py` 的
岁运五式、虚拱填实、三合补支等），482 只认 `<file>.txt:<行>「…」` 形态、
八字 [10] 只扫 `references/`，这批 `源L` 书证此前无门。现核：书名取同行
或前 9 行最近的《…》（同名多本全收），行号在册；同行 40 字内的 `「…」`
须在该行逐字命中（省略号分段）。首跑 51 锚中 31 条带同行引文全符、
49 条书名可解析（另 2 条 `dayun.py` 的「同书源L1848／源L922」超出前 9 行书名
上下文，按无书名只计不判）。代码里的《》也可能是篇名（《顺局》），故不可解析时
先向上找可解析书名（《滴天髓》），仍无才记无书名，不臆造归属。两科 selftest 都跑夹具。

495 批追加（仅八字册）：**`dev_tools/**` 与 `eval/**` 的书证进同一门**。
490 只扫 `scripts/`＋`core/`，而 `dev_tools/`（96 锚）与 `eval/`（12 锚）同样在写
「书云源L####」：`check_dayun_cases.py` 的化格前置、`check_hidden_stems.py` 的藏干
句型、《千里命稿》起运算例，`evaluate.py` 的行运缺口说明——此前完全无人回验。
扩面同时改三个口径：① `selftest` 函数体内的锚是负例夹具（`《测试书》L2` 等），
按 AST 区间跳过；② 引文闭合放宽到整行（真引文超过 40 字时不再被静默跳过），
整行不闭合才接下一行；③ f-string 模板（`「{stem}…」`）不是逐字引文，按无引文处理。
扩面首跑判红 10 条：9 条是真实错锚/错归属，1 条是本门自身文档的括号说明被误当引文
（已改写）。9 条中：`check_hidden_stems.py` 把《三命通会》L283 的「午中丙火用事七日」
记在《千里命稿》名下（L283 实为「（第四部运）壬戌」）；`check_dayun_cases.py` 的
《滴天髓·從化論》L5251／L5238 在底本里实为 L5260／L5247（且 從化論章在《滴天髓闡微》
而非 861 行的《滴天髓》）；`evaluate.py` 的《千里明镜》两处（484 批已确认库中只有
《千里命稿》）；`evaluate.py` 的「折除三日为一岁」被同行「再加 N 天」顶替、
「见庚子年」「L917」分别被近指的《神峰通考》/《千里命稿》顶替；
`dayun.py` 的「纔交乙巳运」被近指的《神峰通考》顶替（实出《渊海子平》）；
`congrge.py` 的《顺局》诗锚在句后、引文在锚前，旧规则取到了后面的任注。
另同步修正 3 处未带引文但同属《千里明镜》误名的说明（`evaluate.py` 两处、
`bazi_dayun_cases.json` 的 note）。两科 selftest 都跑夹具。
"""
from __future__ import annotations

import ast
import json
import re
import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DISC = Path(__file__).resolve().parents[1]
ROOT = DISC.parent
REG = DISC / "data" / "rules" / "rule_registry.json"
# 447 批：千金赋联句映射（仅六爻有该册；八字无文件则跳过，不判红）。
QIANJIN = DISC / "data" / "rules" / "qianjin_fu_map.json"
QIANJIN_SRC = DISC / "data" / "sources" / "huangjince_dz.dz.txt"
# 462 批：大运起例引文库（仅八字有该册；六爻无文件则跳过，不判红）。
DAYUN = DISC / "data" / "rules" / "dayun_quotes.json"
# 465 批：裁决引文真值源（仅八字有该册；六爻无文件则跳过）。
VERDICTS = DISC / "data" / "verdicts.json"
# 466 批：六神取象 / 十神作用（仅八字有该册）。
LIUSHEN = DISC / "data" / "liushen_image.json"
SHISHEN = DISC / "data" / "shi_shen_actions.json"
# 467 批：六爻引文库（仅六爻有该结构；八字同名文件结构不同）。
LIUYAO_QUOTES = DISC / "data" / "verdicts.json"
# 470 批：叙述层模板（仅六爻有该册）。
NARRATIVE_TPL = DISC / "data" / "narrative_templates.json"
# 471 批：火珠林财官伏藏引文库（仅六爻有该册）。
FUSHI = DISC / "data" / "rules" / "caiguan_fushi.json"
# 473 批：易林补遗门类定位映射（仅六爻有该册）。
YILIN = DISC / "data" / "yilin_buyi_maps.json"
# 475 批：纳音取象表（仅八字有该册）。
NAYIN = DISC / "data" / "nayin_quxiang.json"
# 477 批：六爻判词文案表（仅六爻有该册）。
VERDICT_TEXTS = DISC / "data" / "rules" / "verdict_texts.json"
# 483 批：六爻问题词典（仅六爻有该册）。
QUESTION_USE_GODS = DISC / "data" / "rules" / "question_use_gods.json"
# 485 批：六爻分占域判据引文库（仅六爻有该册）。
DOMAIN_CITES = DISC / "data" / "rules" / "domain_citations.json"
# 488 批：六爻问题题类表（仅六爻有该册）。
QUESTION_CLASSES = DISC / "data" / "rules" / "question_classes.json"
DOMAIN_CITES_SRC = DISC / "data" / "sources" / "yimao_dz.dz.txt"
_VERDICT_LOCATOR = re.compile(r"(data/sources/[^:]+):(\d+)")
_VERDICT_MARK = re.compile(r"''+|={2,}|\{\{|\}\}|\||\*")
_VERDICT_FIELDS = ("quote", "full_quote", "cond_quote", "verse_quote")


def _verdict_plain(s: str) -> str:
    return re.sub(r"\s+", "", _VERDICT_MARK.sub("", str(s)))


# 478 批：内联引文的折叠口径（去全部标点/空白，兼容底本全角 ﹕﹐）。省略号
# 「……」表示省略，不能整串比对；按省略号切段，逐段命中。
_FOLD = re.compile(r"[\s\W_]+")


def _fold(s) -> str:
    return _FOLD.sub("", str(s))


def _segments(q) -> list[str]:
    return [x for x in re.split(r"…+|\.{3,}", str(q)) if x]


def _seg_hit(q, text) -> bool:
    return all(_fold(x) in _fold(text) for x in _segments(q))


def _walk_entries(obj, path: str = "$"):
    if isinstance(obj, dict):
        yield path, obj
        for k, v in obj.items():
            yield from _walk_entries(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_entries(v, f"{path}[{i}]")


_QN_DROP = re.compile(r"[\s，。、；：「」『』“”\"'‘’（）()\[\]【】《》〈〉·．\-—_]+")

_DROP = re.compile(r"[\s，。、；：「」『』“”\"'‘’（）()【】\[\]《》<>·．\-—_/\\|+=:;,.*]+")
VARIANT = str.maketrans({"剋": "克", "裏": "里", "羣": "群", "徧": "遍", "啓": "启",
                         "蔵": "藏", "峯": "峰", "梟": "枭", "煙": "烟",
                         "刪": "删", "黃": "黄", "淵": "渊", "闡": "阐",
                         "寧": "宁", "逹": "达", "爲": "为", "與": "与"})


def norm(s: str) -> str:
    return _DROP.sub("", str(s)).translate(VARIANT)


# 同书异名（仅列已实见、可确认同书的异写；不做模糊近音匹配）。
_TITLE_ALIAS = (("命理探原", "命理探源"),)


def _book_key(s: str) -> str:
    b = norm(s)
    for alias, canonical in _TITLE_ALIAS:
        b = b.replace(alias, canonical)
    return b


def _resolve_any(rel: str) -> Path | None:
    """指针按仓库根写（`bazi/data/…`），也容忍相对学科根的写法。"""
    rel = rel.split("#", 1)[0].strip().lstrip("./")
    for base in (ROOT, DISC):
        p = base / rel
        if p.exists():
            return p
    return None


def _dig(obj, dotted: str):
    """按 `a.b.c` 取嵌套值；键本身可含 `/`（如「独发/独静」），故从右往左不可分，
    改用逐段前缀尝试。"""
    parts = dotted.split(".")
    cur = obj
    i = 0
    while i < len(parts):
        if not isinstance(cur, dict):
            return None, parts[i:]
        # 尽量吃掉更多段（键里带点的罕见，带 / 的常见但已被 split 保留）
        matched = False
        for j in range(len(parts), i, -1):
            key = ".".join(parts[i:j])
            if key in cur:
                cur = cur[key]
                i, matched = j, True
                break
        if not matched:
            return None, parts[i:]
    return cur, []


def _iter_entries(doc: dict):
    for bucket in ("rules", "_uncovered"):
        for item in doc.get(bucket) or []:
            if isinstance(item, dict):
                yield bucket, item


# 【第一百六十八批·照六爻第一百六十九批同步】`impl` 是**可执行契约**，本器此前只回验
# `source.quote_in_*`／`corpus_files`，从没看过 `impl`。六爻科实抓到两条悬空指针
# （第一百六十六批「域拆分」把函数搬进子模块、父模块无 re-export，impl 仍指父模块），
# 于是「指针写了没人验」在本科同样是真事——本批把两侧判据拉齐。
#
# 口径（**宁可少判**，与六爻科同）：只认 `<path>.py` 后紧跟 `:标识符` 且标识符首字符是
# 字母/下划线的形态；行号 `:1058`、`:4.3` 这类**定位记号不是符号**，一律跳过，否则本器
# 会逼人改写正确定位记号。多段实现（`；`／`＋`／`（）`）逐段各自判。
#
# ⚠ 扫描面是**整条 impl 串，含括号内的说明文字**：注释里若把「旧壳 + 符号」拼成一条
# `path.py:symbol`，本器一样判红（本批实踩——更正死指针时在注里写了旧写法，当场被抓）。
# 这是**特性不是误伤**：说明文字里的死指针同样是死指针。登记旧值时**只写文件、不拼符号**。
# A1-1 归并：路径前缀两科都认（原八字版只认 bazi/，六爻版只认 liuyao/）
_PATH_RE = re.compile(r"(?<![\w/])((?:(?:liuyao|bazi)/)?(?:scripts|core|dev_tools)/[\w/]+\.py)")
_SYM_RE = re.compile(r":([A-Za-z_][A-Za-z0-9_]*)")
# 薄 re-export 壳（职责拆走后只留 `from X import *` 的模块）：
# 符号**在壳里不落字面**但运行时可达——照字面判会造 4 条假红（实测踩到）。
_REEXPORT = re.compile(r"from\s+[\w.]+\s+import\s+\*")


def _reachable_via_import(tp: Path, sym: str) -> bool:
    """薄 re-export 壳专用：改用**运行时可达性**判（真可达就不算死指针）。"""
    import importlib.util

    name = "_impl_probe_" + tp.stem
    try:
        spec = importlib.util.spec_from_file_location(name, tp)
        if spec is None or spec.loader is None:
            return False
        mod = importlib.util.module_from_spec(spec)
        parent = str(tp.parent)
        inserted = parent not in sys.path
        if inserted:
            sys.path.insert(0, parent)
        try:
            spec.loader.exec_module(mod)
            return hasattr(mod, sym)
        finally:
            if inserted and parent in sys.path:
                sys.path.remove(parent)
    except Exception:
        return False


def check_impl(impl: str) -> list[str]:
    """回验 `impl` 里的 `file.py:symbol`；返回问题清单（空＝全部可回指）。"""
    bad: list[str] = []
    for m in _PATH_RE.finditer(impl):
        rel = m.group(1)
        tp = _resolve_any(rel)
        if tp is None:
            bad.append(f"文件不存在 → {rel}")
            continue
        sm = _SYM_RE.match(impl[m.end():m.end() + 80])
        if not sm:
            continue          # 纯路径 / 行号 / 4.3：无符号可验，不判
        sym = sm.group(1)
        body = tp.read_text(encoding="utf-8", errors="replace")
        if re.search(rf"\b{re.escape(sym)}\b", body):
            continue
        if _REEXPORT.search(body):
            # 壳里不落字面但运行时可达 → 不是死指针；真不可达（如未进 __all__）仍判红
            if _reachable_via_import(tp, sym):
                continue
            bad.append(f"符号不可达（re-export 壳未导出）→ {rel}:{sym}")
            continue
        bad.append(f"符号不在该文件内 → {rel}:{sym}")
    return bad


def check(doc: dict, problems: list[str], notes: list[str]) -> tuple[int, int]:
    """返回 (检视指针数, 通过数)。"""
    checked = passed = 0
    for bucket, item in _iter_entries(doc):
        rid = item.get("rule_id") or "?"
        src = item.get("source") or {}
        verified = src.get("verified")
        for field in ("quote_in_data", "quote_in_code"):
            ref = src.get(field)
            if not ref or "#" not in str(ref):
                continue
            checked += 1
            target, _, ptr = str(ref).partition("#")
            tp = _resolve_any(target)
            if tp is None:
                msg = f"{rid}.{field}：目标文件不存在 → {target}"
                (problems if verified else notes).append(msg)
                continue
            body = tp.read_text(encoding="utf-8", errors="replace")
            ok = False
            detail = ""
            if field == "quote_in_code":
                # 允许两种：字面串命中，或作为标识符存在
                ok = ptr in body or bool(re.search(rf"\b{re.escape(ptr)}\b", body))
                detail = ptr[:32]
            else:
                try:
                    data = json.loads(body)
                except Exception as exc:
                    problems.append(f"{rid}.quote_in_data：目标不是合法 JSON（{exc}）")
                    continue
                val, rest = _dig(data, ptr)
                if val is None or (isinstance(val, str) and not val.strip()):
                    detail = f"路径解不到值（余 {rest[:2]}）"
                else:
                    val_s = val if isinstance(val, str) else json.dumps(val, ensure_ascii=False)
                    corpora = src.get("corpus_files") or []
                    hit_in = None
                    for c in corpora:
                        cp = _resolve_any(c)
                        if cp and norm(val_s) in norm(cp.read_text(encoding="utf-8", errors="replace")):
                            hit_in = cp.name
                            break
                    if corpora and not hit_in:
                        detail = "语料逐字未命中：" + val_s[:28] + "…"
                    else:
                        ok = True
                        detail = (f"{val_s[:24]}…（语料命中 {hit_in}）" if hit_in
                                  else val_s[:24] + "…")
            if ok:
                passed += 1
            else:
                line = f"{rid}.{field}：{detail}"
                (problems if verified else notes).append(line + "（verified=false，只记）"
                                                         if not verified else line)
        for c in (src.get("corpus_files") or []):
            checked += 1
            if _resolve_any(c) is None:
                (problems if verified else notes).append(f"{rid}.corpus_files：不存在 → {c}")
            else:
                passed += 1
        # 【第三百六十二批】`quote_in_source`（"底本文件:行号" 形态）此前**没有任何门在守**：
        # 门只认 `#` 形态的 quote_in_data/quote_in_code，而六爻 33 条里有 2 条用的是行号形态，
        # 于是它们的 `verified=false` 从登记那天起躺到今天——不是"无法核实"，是"没人核实"
        # （362 批回验：4 条引文 4/4 逐字命中底本该行）。本判据补上这个空档。
        for key, ptr_key in (("quote", "quote_in_source"),
                             ("quote2", "quote2_in_source"),
                             ("quote3", "quote3_in_source")):
            ref = src.get(ptr_key)
            quote = src.get(key)
            if not ref or ":" not in str(ref) or not quote:
                continue
            checked += 1
            target, _, ln = str(ref).rpartition(":")
            tp = _resolve_any(target)
            if tp is None:
                (problems if verified else notes).append(
                    f"{rid}.{ptr_key}：底本不存在 → {target}")
                continue
            try:
                lines = tp.read_text(encoding="utf-8", errors="replace").split("\n")
                body = lines[int(ln) - 1]
            except (ValueError, IndexError):
                (problems if verified else notes).append(
                    f"{rid}.{ptr_key}：行号不可解析或越界 → {ref}")
                continue
            # 行号形态的指针是「引文就在这一行」的强声明：命中即过，不命中即红
            # （不看 verified——既然写了行号，就是在声称引文在此）
            if norm(quote) in norm(body):
                passed += 1
            else:
                a, b = norm(quote), norm(body)
                i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]),
                         min(len(a), len(b)))
                (problems if verified else notes).append(
                    f"{rid}.{ptr_key}：引文不在 {ref} 该行（首异于第 {i} 字："
                    f"…{a[max(0, i - 12):i + 12]}… ≠ …{b[max(0, i - 12):i + 12]}…）"
                    + ("" if verified else "（verified=false，只记）"))
        # 【第一百六十八批】`impl` 回验：代码指针没有「诚实未核实」状态，指错即指错，
        # 故不看 verified 一律判红（§六.3 文实不符等同代码缺陷）。
        impl = item.get("impl")
        if impl:
            checked += 1
            bad = check_impl(str(impl))
            if bad:
                problems.append(f"{rid}.impl：{'；'.join(bad)}")
            else:
                passed += 1
    return checked, passed


def check_qianjin_map(doc: dict, problems: list[str],
                      registry_ids: set[str] | None = None,
                      src_lines: list[str] | None = None) -> tuple[int, int]:
    """千金赋联句映射的统计自洽＋逐联书源回指（447／457 批）。返回 (联句数, 状态种数)。"""
    entries = doc.get("联句映射")
    if not isinstance(entries, list) or not entries:
        problems.append("千金赋映射：联句映射缺失或为空——0 结果 ≠ 通过")
        return 0, 0
    meta = doc.get("_meta") or {}
    states = meta.get("五态") or meta.get("四态") or {}   # 兼容旧键名，词表仍须覆盖实际状态
    if not isinstance(states, dict) or not states:
        problems.append("千金赋映射：_meta 未登记状态词汇（五态/四态）")
        states = {}

    def state_of(e: dict) -> str:
        return str(e.get("状态") or "").split("_", 1)[0]

    usage: dict[str, int] = {}
    unknown: dict[str, str] = {}
    for e in entries:
        s = state_of(e)
        usage[s] = usage.get(s, 0) + 1
        if states and s not in states:
            unknown.setdefault(s, str(e.get("句") or "")[:16])
    for s, q in unknown.items():
        problems.append(f"千金赋映射：状态「{s}」未在 _meta 状态词汇中登记（{q}…）")

    stats = doc.get("统计") or {}
    total = stats.get("联句总数")
    if total != len(entries):
        problems.append(f"千金赋映射：统计.联句总数 {total} ≠ 实际 {len(entries)}")
    per_state = 0
    for key, val in stats.items():
        if key == "联句总数":
            continue
        if states and key not in states:
            problems.append(f"千金赋映射：统计里有未登记的状态键「{key}」")
        if not isinstance(val, int) or val != usage.get(key, 0):
            problems.append(f"千金赋映射：统计.{key} {val} ≠ 实际 {usage.get(key, 0)}")
        if isinstance(val, int):
            per_state += val
    if per_state != len(entries):
        problems.append(f"千金赋映射：统计分项之和 {per_state} ≠ 联句总数 {len(entries)}")
    if states:
        absent = sorted(set(states) - set(stats))
        if absent:
            problems.append(f"千金赋映射：状态词汇 {absent} 未在统计中列出")

    registry = doc.get("registry_未被本表联句直接挂上")
    if registry is not None:
        if not isinstance(registry, list):
            problems.append("千金赋映射：registry_未被本表联句直接挂上 必须是列表")
        elif registry_ids is not None:
            missing = [str(x) for x in registry if str(x) not in registry_ids]
            if missing:
                problems.append(f"千金赋映射：registry 列表有 {len(missing)} 个 id "
                                f"不在 rule_registry：{missing[:4]}")

    # 457 批：逐联书源回指——`_meta.纪律` 声明「联句与 src 逐字从书源抄来」，
    # 此前只核统计块，联句与行号从未对拍。窗口与 [14] 同口径（所指行 ±2 行拼接）。
    lines = src_lines
    if lines is None:
        if not QIANJIN_SRC.is_file():
            problems.append(f"千金赋映射：底本不存在 {QIANJIN_SRC.name}——无从回指")
            lines = []
        else:
            lines = QIANJIN_SRC.read_text(encoding="utf-8", errors="replace").splitlines()
    line_ref = re.compile(r"(?:源)?L(\d+)")
    qbad = 0
    for e in entries:
        m = line_ref.search(str(e.get("src") or ""))
        if not m:
            problems.append(f"千金赋映射：条目缺行号 src（{(e.get('句') or '')[:16]}…）")
            qbad += 1
            continue
        n = int(m.group(1))
        if lines and (n < 1 or n > len(lines)):
            problems.append(f"千金赋映射：src 行号 L{n} 超出底本（共 {len(lines)} 行）")
            qbad += 1
            continue
        q = _QN_DROP.sub("", str(e.get("句") or ""))
        window = "".join(_QN_DROP.sub("", x) for x in lines[max(0, n - 2):n + 3])
        if not q or q not in window:
            problems.append(f"千金赋映射：联句与底本源L{n} 邻域不符 → "
                            f"{(e.get('句') or '')[:24]}…")
            qbad += 1
    if qbad:
        problems.append(f"千金赋映射：逐联回指失败 {qbad}/{len(entries)} 条")
    return len(entries), len(usage)


def check_dayun_quotes(doc: dict, problems: list[str],
                       lines: list[str] | None = None) -> int:
    """大运起例引文库的行锚回验（462 批）。返回条目数。

    为什么需要它：`dayun_quotes.json` 的 `_comment` 声明「引文必须与 …
    `corpus_line` 那一行逐字一致」，但 [12] 的 `quote_in_data` 只验「值在语料
    某处出现过」，从不看行号——声明比门宽（§六.3）。本函数按该声明逐条核对：
    `_provenance.source_file` 在盘、`corpus_line` 在册、`quote` 落在该行。

    `lines` 参数供 selftest 注入夹具底本；正式路径由 `source_file` 现场读。
    """
    entries = [(k, v) for k, v in doc.items()
               if isinstance(v, dict) and "quote" in v and "corpus_line" in v]
    if not entries:
        problems.append("大运起例引文：0 条 corpus_line+quote——0 结果 ≠ 通过")
        return 0
    if len(entries) < 2:
        problems.append(f"大运起例引文：只扫到 {len(entries)} 条（下限 2）——先确认字段/路径")
    if lines is None:
        src = str((doc.get("_provenance") or {}).get("source_file") or "")
        rp = _resolve_any(src) if src else None
        if rp is None:
            problems.append(f"大运起例引文：source_file 不存在 → {src!r}")
            return len(entries)
        lines = rp.read_text(encoding="utf-8", errors="replace").splitlines()
    bad = 0
    for key, e in entries:
        try:
            n = int(str(e.get("corpus_line")).strip())
        except Exception:
            problems.append(f"大运起例引文：{key} 的 corpus_line 非整数 → {e.get('corpus_line')!r}")
            bad += 1
            continue
        if not (1 <= n <= len(lines)):
            problems.append(f"大运起例引文：{key} 的行号 L{n} 超出底本（共 {len(lines)} 行）")
            bad += 1
            continue
        q = _QN_DROP.sub("", str(e.get("quote") or ""))
        if not q or q not in _QN_DROP.sub("", lines[n - 1]):
            problems.append(f"大运起例引文：{key} 的引文不在所署行 L{n} → "
                            f"{str(e.get('quote') or '')[:30]!r}")
            bad += 1
    if bad:
        problems.append(f"大运起例引文：行锚不符 {bad}/{len(entries)} 条")
    return len(entries)


def check_verdicts_quotes(doc: dict, problems: list[str], lines_of=None) -> tuple[int, int]:
    """裁决引文的书源回验（465 批）。返回 (locator 字段数, 分支总则引文数)。

    为什么需要它：`data/verdicts.json` 自称「书源引文唯一真值源」，其中 20 个字段
    带 `locator`（`data/sources/<书>:<行>`）、4 条分支总则（病药 thesis、化格/从格
    verse）在 `_meta` 声明了底本——但 [12] 的 quote_in_data 只指向 `病药引文.thesis`
    一个点，`locator` 从未被任何门读取。本函数按声明核对：

      · 带 locator 的条目：行号在册、quote/full_quote/cond_quote/verse_quote 落在该行；
      · 三条分支总则：逐行命中 `_meta` 声明的底本（不跨行拼接，避免假阳性）。

    `lines_of` 供 selftest 注入夹具底本；正式路径按 locator/固定路径现场读。
    """
    n_loc = n_grp = 0
    cache: dict[str, list[str] | None] = {}

    def get_lines(f: str) -> list[str] | None:
        if lines_of is not None:
            return lines_of(f)
        if f not in cache:
            p = _resolve_any(f)
            cache[f] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                        if p else None)
        return cache[f]

    for path, e in _walk_entries(doc):
        loc = str(e.get("locator") or "").strip()
        m = _VERDICT_LOCATOR.fullmatch(loc)
        if not m:
            continue
        f, n = m.group(1), int(m.group(2))
        L = get_lines(f)
        if L is None:
            problems.append(f"verdicts：{path}.locator 指向不存在的底本 {f}")
            continue
        if not (1 <= n <= len(L)):
            problems.append(f"verdicts：{path}.locator 行号 L{n} 超出底本（共 {len(L)} 行）")
            continue
        for key in _VERDICT_FIELDS:
            q = e.get(key)
            if not q:
                continue
            n_loc += 1
            if _verdict_plain(q) not in _verdict_plain(L[n - 1]):
                problems.append(f"verdicts：{path}.{key} 不在所署行 {f}:{n} → "
                                f"{str(q)[:30]!r}")

    for group, field, src in (
            ("病药引文", "thesis", "data/sources/shen-feng-tong-kao.wikitext.txt"),
            ("化格引文", "verse", "data/sources/di-tian-sui.wikitext.txt"),
            ("从格引文", "verse", "data/sources/di-tian-sui.wikitext.txt")):
        v = (doc.get(group) or {}).get(field)
        if v is None:
            continue
        vals = v if isinstance(v, list) else [v]
        as_list = isinstance(v, list)
        L = get_lines(src)
        if L is None:
            problems.append(f"verdicts：{group}.{field} 的底本不存在 {src}")
            continue
        for i, q in enumerate(vals):
            if not q:
                continue
            n_grp += 1
            label = f"{group}.{field}[{i}]" if as_list else f"{group}.{field}"
            if not any(_verdict_plain(q) in _verdict_plain(x) for x in L):
                problems.append(f"verdicts：{label} 非书源逐字（{src}）→ "
                                f"{str(q)[:30]!r}")
    return n_loc, n_grp


def check_liushen_sources(doc_img: dict, doc_acts: dict, problems: list[str],
                          lines_of=None) -> tuple[int, int]:
    """六神取象/十神作用的行号出处回验（466 批）。返回 (取象字段数, 作用条目数)。

    为什么需要它：`liushen_image.json` 的 `_meta` 明写「值只收逐字引文与行号，
    不做改写（铁律二）」；但 466 批实抓到两条 `取象` 是**注释式改写**且没有
    `_src`，`narrate` 仍按引文渲染成「（《千里命稿》 行）」——空行号+改写句冒充
    引文（§六.3）。本函数把声明变成机械判据：

      · 每个非空 `能力/构成/取象/别名` 必须有 `<字段>_src`，形态 `data/sources/<书>:<行>`；
        行号在册、值落在该行（保标点，与 465 批同口径）；
      · `shi_shen_actions` 每条 `source` 必须能解析出行号（`L####` 或 `:####`），
        `actions` 每项须落在该行 ±3 行邻域。

    `lines_of` 供 selftest 注入夹具底本；正式路径现场读。
    """
    n_fields = n_acts = 0
    cache: dict[str, list[str] | None] = {}

    def get_lines(f: str) -> list[str] | None:
        if lines_of is not None:
            return lines_of(f)
        if f not in cache:
            p = _resolve_any(f)
            cache[f] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                        if p else None)
        return cache[f]

    img = (doc_img or {}).get("十神取象")
    if not isinstance(img, dict) or not img:
        problems.append("六神取象：十神取象缺失或为空——0 结果 ≠ 通过")
    else:
        for god, e in img.items():
            if not isinstance(e, dict):
                continue
            for key in ("能力", "构成", "取象", "别名"):
                q = e.get(key)
                if not q:
                    continue
                n_fields += 1
                src = str(e.get(key + "_src") or "").strip()
                m = _VERDICT_LOCATOR.fullmatch(src)
                if not m:
                    problems.append(f"六神取象：{god}.{key} 缺行号出处（_meta 声明"
                                    f"「值只收逐字引文与行号」）→ {str(q)[:24]!r}")
                    continue
                f, n = m.group(1), int(m.group(2))
                L = get_lines(f)
                if L is None:
                    problems.append(f"六神取象：{god}.{key} 的底本不存在 {f}")
                    continue
                if not (1 <= n <= len(L)):
                    problems.append(f"六神取象：{god}.{key} 行号 L{n} 超出底本（共 {len(L)} 行）")
                    continue
                if _verdict_plain(q) not in _verdict_plain(L[n - 1]):
                    problems.append(f"六神取象：{god}.{key} 不在所署行 {f}:{n} → "
                                    f"{str(q)[:24]!r}")

    acts = (doc_acts or {}).get("shi_shen_actions")
    if not isinstance(acts, dict) or not acts:
        problems.append("十神作用：shi_shen_actions 缺失或为空——0 结果 ≠ 通过")
    else:
        for god, e in acts.items():
            if not isinstance(e, dict):
                continue
            n_acts += 1
            src = str(e.get("source") or "")
            fm = re.match(r"(data/sources/[^: \s]+)", src)
            nm = re.search(r"(?:L|:)(\d+)", src)
            if not fm or not nm:
                problems.append(f"十神作用：{god}.source 缺可解析底本/行号 → {src!r}")
                continue
            f, n = fm.group(1), int(nm.group(1))
            L = get_lines(f)
            if L is None:
                problems.append(f"十神作用：{god}.source 的底本不存在 {f}")
                continue
            if not (1 <= n <= len(L)):
                problems.append(f"十神作用：{god}.source 行号 L{n} 超出底本（共 {len(L)} 行）")
                continue
            window = _verdict_plain("".join(L[max(0, n - 3):n + 2]))
            missing = [a for a in (e.get("actions") or [])
                       if _verdict_plain(a) not in window]
            if missing:
                problems.append(f"十神作用：{god} 的 actions 不在所署行 L{n} 邻域 → "
                                f"{missing[:3]}")
    return n_fields, n_acts


def check_quote_database(doc: dict, problems: list[str], text_of=None) -> tuple[int, int]:
    """六爻引文库 `quote_kind` 自洽与逐字回验（467 批）。返回 (verbatim 数, paraphrase 数)。

    为什么需要它：`liuyao/data/verdicts.json#quote_database` 的 `_meta` 旧写
    「引文库，source 字段为古籍出处」，但 467 批全库实测 **49 条只有 1 条能逐字回原文**，
    其余 48 条是现代今译。声明把「释义」说成「古籍引文」，属口径分家（§六.3）。
    本函数把区分变成机械判据：

      · 每条的 `quote_kind` 必须是 `verbatim` 或 `paraphrase`；
      · `verbatim` 必须带 `source_ref`（`data/sources/<file>[:<line>]`），
        文件在盘；带行号时按该行、不带行号时按整文件逐字命中（折叠标点）；
      · `paraphrase` 只需非空 `source`（所本篇章），不做逐字断言。

    `text_of` 供 selftest 注入夹具底本；正式路径现场读。
    """
    qs = (doc or {}).get("quote_database")
    if not isinstance(qs, list) or not qs:
        problems.append("引文库：quote_database 缺失或为空——0 结果 ≠ 通过")
        return 0, 0
    cache: dict[str, str | None] = {}

    def get_text(f: str) -> str | None:
        if text_of is not None:
            return text_of(f)
        if f not in cache:
            p = _resolve_any(f)
            cache[f] = p.read_text(encoding="utf-8", errors="replace") if p else None
        return cache[f]

    n_v = n_p = 0
    for i, q in enumerate(qs):
        if not isinstance(q, dict):
            problems.append(f"引文库：第 {i} 条不是对象")
            continue
        kind = str(q.get("quote_kind") or "")
        quote = str(q.get("quote") or "")
        src = str(q.get("source") or "")
        if kind not in ("verbatim", "paraphrase"):
            problems.append(f"引文库：第 {i} 条 quote_kind 缺失/非法 → {kind!r}")
            continue
        if not quote or not src:
            problems.append(f"引文库：第 {i} 条 quote/source 为空")
            continue
        if kind == "paraphrase":
            n_p += 1
            continue
        n_v += 1
        ref = str(q.get("source_ref") or "").strip()
        m = re.fullmatch(r"(data/sources/[^:]+)(?::(\d+))?", ref)
        if not m:
            problems.append(f"引文库：第 {i} 条 verbatim 缺 source_ref（file[:line]）→ {ref!r}")
            continue
        f, ln = m.group(1), m.group(2)
        body = get_text(f)
        if body is None:
            problems.append(f"引文库：第 {i} 条 source_ref 底本不存在 {f}")
            continue
        if ln:
            lines = body.splitlines()
            n = int(ln)
            if not (1 <= n <= len(lines)):
                problems.append(f"引文库：第 {i} 条 source_ref 行号 L{n} 超出底本")
                continue
            ok = _DROP.sub("", quote) in _DROP.sub("", lines[n - 1])
        else:
            ok = _DROP.sub("", quote) in _DROP.sub("", body)
        if not ok:
            problems.append(f"引文库：第 {i} 条 verbatim 引文非书源逐字（{ref}）→ "
                            f"{quote[:30]!r}")
    return n_v, n_p


def check_shi_yao_interp(doc: dict, problems: list[str]) -> int:
    """六亲持世断语的括注口径（469 批）。返回『据《…》今译』标记数。

    为什么需要它：`shi_yao_interpretation` 有 19 条纹末标「（《火珠林·X章》）」，
    但 469 批全库实测这些句子**没有一条能逐字回原文**（都是现代今译）。括号直接
    署书等于把今译当引文（§六.3）。本函数要求今译标记必须是
    `（据《…》今译）`，出现裸 `（《…》）` 即判红。
    """
    vals = (doc or {}).get("shi_yao_interpretation")
    if not isinstance(vals, dict) or not vals:
        problems.append("六亲持世：shi_yao_interpretation 缺失或为空——0 结果 ≠ 通过")
        return 0
    n_claim = 0
    for god, e in vals.items():
        if not isinstance(e, dict):
            continue
        for k, v in e.items():
            if not isinstance(v, str):
                continue
            if re.search(r"（《[^》]+》）", v):
                problems.append(f"六亲持世：{god}.{k} 仍用裸书证括注（《…》）——"
                                f"今译须标『（据《…》今译）』→ {v[:36]!r}")
            n_claim += len(re.findall(r"（据《[^》]+》今译）", v))
    return n_claim


def check_wenwang_chishi(doc: dict, problems: list[str], lines_of=None) -> int:
    """《文王金钱课》六亲持世引文的行锚回验（470 批）。返回字段数。

    为什么需要它：`narrative_templates.json` 的 `pattern_hints._wenwang_chishi._meta`
    明写「每条 `quote` 为 wenwang_jinqianke_dz.dz.txt 的逐字子串，
    `src` 为主源行号」；`补`/`补_src` 同构。但此前没有任何门读这 14 个字段——
    [14] 认的是「源L」形态，这里的 `file:NNNN` 不在其扫描面。470 批实测 14/14 全符，
    本函数把声明变成常设判据；`lines_of` 供 selftest 注入夹具底本。
    """
    W = ((doc or {}).get("pattern_hints") or {}).get("_wenwang_chishi")
    if not isinstance(W, dict) or not W:
        problems.append("文王持世：pattern_hints._wenwang_chishi 缺失或为空——0 结果 ≠ 通过")
        return 0
    cache: dict[str, list[str] | None] = {}

    def get_lines(f: str) -> list[str] | None:
        if lines_of is not None:
            return lines_of(f)
        if f not in cache:
            p = _resolve_any(f)
            cache[f] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                        if p else None)
        return cache[f]

    n = 0
    for k, v in W.items():
        if not isinstance(v, dict):
            continue
        for field, skey in (("quote", "src"), ("补", "补_src")):
            q = v.get(field)
            if not q:
                continue
            n += 1
            src = str(v.get(skey) or "").strip()
            m = _VERDICT_LOCATOR.fullmatch(src)
            if not m:
                problems.append(f"文王持世：{k}.{skey} 缺行号出处 → {src!r}")
                continue
            f, ln = m.group(1), int(m.group(2))
            L = get_lines(f)
            if L is None:
                problems.append(f"文王持世：{k}.{skey} 的底本不存在 {f}")
                continue
            if not (1 <= ln <= len(L)):
                problems.append(f"文王持世：{k}.{skey} 行号 L{ln} 超出底本（共 {len(L)} 行）")
                continue
            if _verdict_plain(q) not in _verdict_plain(L[ln - 1]):
                problems.append(f"文王持世：{k}.{field} 不在所署行 {f}:{ln} → {str(q)[:28]!r}")
    return n


def check_fushi_quotes(doc: dict, problems: list[str], lines_of=None) -> int:
    """《火珠林》财官伏藏引文库的行锚回验（471 批）。返回 src/_src 字段数。

    为什么需要它：`caiguan_fushi.json`（六爻，`data/rules/`）的 `_meta.铁律` 明写
    「九章歌诀与注文**只作逐字引文登记**，由 narrate 按 `*_src` 回指原文自取」，
    `classical_enhancements_fushi.py` 的 docstring 也自称「已 Read 逐字核验」。
    但 [14] 只认「《书名》源L」形态，本册用的是 `data/sources/<书>:<行>`，
    21 个 `歌诀/歌诀续/取法条件/注文` 字段长期无门（§六.3）。本函数按声明核对：

      · `总纲` 与 `九宫` 的每个 `*_src` / `src` 必须是 `data/sources/<书>:<行>`；
      · 行号在册；`歌诀/歌诀续/取法条件` 须落在**所署那一行**，`注文`（段落常跨
        两条物理行）给 ±1 行邻域；
      · `_src` 必须有配对的同名字段（`src` 配对 `歌诀`）。

    `lines_of` 供 selftest 注入夹具底本；正式路径现场读。
    """
    root = doc or {}
    dg = root.get("九宫")
    if not isinstance(dg, dict) or not dg:
        problems.append("财官伏藏：九宫 缺失或为空——0 结果 ≠ 通过")
        return 0
    cache: dict[str, list[str] | None] = {}

    def get_lines(f: str) -> list[str] | None:
        if lines_of is not None:
            return lines_of(f)
        if f not in cache:
            p = _resolve_any(f)
            cache[f] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                        if p else None)
        return cache[f]

    n = 0
    # `总纲` 是**单条**（字段直接在它下面）；`九宫` 才是「条目名 → 条目」的集合。
    entries: list[tuple[str, str, dict]] = []
    zz = root.get("总纲")
    if isinstance(zz, dict):
        entries.append(("总纲", "", zz))
    for name, e in dg.items():
        if isinstance(e, dict):
            entries.append(("九宫", str(name), e))
    for block, name, e in entries:
        label = f"{block}.{name}" if name else block
        pairs: list[tuple[str, str]] = []
        for base in ("歌诀", "歌诀续", "取法条件", "注文"):
            if not (isinstance(e.get(base), str) and e.get(base).strip()):
                continue
            if base + "_src" in e:
                pairs.append((base, base + "_src"))
            elif base == "歌诀" and "src" in e:
                pairs.append((base, "src"))
            else:
                pairs.append((base, base + "_src"))   # 缺 _src → 进分母并判红
        if "src" in e and not any(sk == "src" for _b, sk in pairs):
            pairs.append(("歌诀", "src"))
        # 有 `_src` 却找不到配对引文的孤儿，也要进分母并判红
        for key in e:
            if key == "src" or key.endswith("_src"):
                if not any(sk == key for _b, sk in pairs):
                    pairs.append((key[:-4] if key.endswith("_src") else "歌诀", key))
        for base, skey in pairs:
            n += 1
            q = e.get(base)
            if not isinstance(q, str) or not q.strip():
                problems.append(f"财官伏藏：{label}.{skey} 无配对引文 {base}")
                continue
            src = e.get(skey)
            if not src:
                problems.append(f"财官伏藏：{label}.{base} 缺行号出处 {skey}")
                continue
            m = _VERDICT_LOCATOR.fullmatch(str(src).strip())
            if not m:
                problems.append(f"财官伏藏：{label}.{skey} 缺行号出处 → {src!r}")
                continue
            f, ln = m.group(1), int(m.group(2))
            L = get_lines(f)
            if L is None:
                problems.append(f"财官伏藏：{label}.{skey} 的底本不存在 {f}")
                continue
            if not (1 <= ln <= len(L)):
                problems.append(f"财官伏藏：{label}.{skey} 行号 L{ln}"
                                f"超出底本（共 {len(L)} 行）")
                continue
            # 歌诀/总纲都是单行句，按**所署那一行**逐字核；注文是段落，底本常把
            # 同一段排成两条物理行（如 L68 末句接 L69），给 ±1 行邻域。
            if base == "注文":
                window = _verdict_plain("".join(L[max(0, ln - 2):ln + 1]))
            else:
                window = _verdict_plain(L[ln - 1])
            if _verdict_plain(q) not in window:
                problems.append(f"财官伏藏：{label}.{base} 不在所署行 {f}:{ln} → "
                                f"{q[:28]!r}")
    return n


def check_yilin_buyi_maps(doc: dict, problems: list[str], lines_of=None) -> tuple[int, int]:
    """《易林补遗》门类定位映射的行锚回验（473 批）。返回 (引文数, 行锚数)。

    为什么需要它：`yilin_buyi_maps.json` 的 `_meta.定位` 明写「书源大量断语须由
    narrate 层按 `src` 行号回指原文自取」，`_source` 逐组点名底本与行号、条目用
    `_src: L###`。但 [14] 只认「《书名》源L」形态，这里的 `data/sources/<书>:<行>`
    与裸 `L###` 都不在其扫描面；本册唯一的机械门是 `[12]` 的 `quote_in_data`
    （只验 registry 指针），不读本表。10 条 `_引文`／34 个行锚长期无门（§六.3）。

    判据：
      · 每个非 `_` 组必须有 `_source`，其中 `data/sources/<书>` 在盘；
        `:NNN`／`:NNN-LMMM` 行号在册（范围两端都查）；
      · 条目 `_src`（以及组级 `_src`）必须是裸 `L####`，继承本组底本、行号在册；
      · 组级/条目 `_引文` 落在所署那一行逐字（`_verdict_plain` 口径）；
      · 【478 批】组级/条目字符串里的内联 `L####「…」` 也按所署行核，
        省略号按段拆分（底本夹注常以「……」省略中间文）。

    `lines_of` 供 selftest 注入夹具底本；正式路径现场读。
    """
    groups = [(k, v) for k, v in (doc or {}).items()
              if not k.startswith("_") and isinstance(v, dict)]
    if not groups:
        problems.append("易林补遗：0 个映射组——0 结果 ≠ 通过")
        return 0, 0
    cache: dict[str, list[str] | None] = {}

    def get_lines(f: str) -> list[str] | None:
        if lines_of is not None:
            return lines_of(f)
        if f not in cache:
            p = _resolve_any(f)
            cache[f] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                        if p else None)
        return cache[f]

    n_q = n_a = 0
    for gname, group in groups:
        src = str(group.get("_source") or "")
        fm = re.search(r"(data/sources/[A-Za-z0-9_.\-]+)", src)
        if not fm:
            problems.append(f"易林补遗：{gname}._source 未点名底本")
            continue
        f = fm.group(1)
        L = get_lines(f)
        if L is None:
            problems.append(f"易林补遗：{gname}._source 的底本不存在 {f}")
            continue
        for a, b in re.findall(r":(\d+)(?:-L?(\d+))?", src):
            for n in (a, b):
                if not n:
                    continue
                n_a += 1
                if not (1 <= int(n) <= len(L)):
                    problems.append(f"易林补遗：{gname}._source 行号 L{n}"
                                    f"超出底本（共 {len(L)} 行）")

        def quote_at(q: str, n: int, label: str) -> None:
            nonlocal n_q
            n_q += 1
            if not (1 <= n <= len(L)):
                problems.append(f"易林补遗：{label} 行号 L{n}超出底本")
                return
            if _verdict_plain(q) not in _verdict_plain(L[n - 1]):
                problems.append(f"易林补遗：{label} 引文不在所署行 {f}:{n} → {q[:26]!r}")

        gq = group.get("_引文")
        if isinstance(gq, str) and gq:
            gs = str(group.get("_src") or "")
            gm = re.fullmatch(r"L(\d+)", gs)
            if gm:
                n_a += 1
                quote_at(gq, int(gm.group(1)), f"{gname}._引文")
            else:
                fm2 = re.search(r":(\d+)", src)
                if fm2:
                    quote_at(gq, int(fm2.group(1)), f"{gname}._引文")
                else:
                    problems.append(f"易林补遗：{gname}._引文 无可解析的行锚")

        for name, e in group.items():
            if not isinstance(e, dict):
                continue
            es = e.get("_src")
            if not isinstance(es, str) or not es:
                continue
            n_a += 1
            m = re.fullmatch(r"L(\d+)", es)
            if not m:
                problems.append(f"易林补遗：{gname}.{name}._src 必须是裸 L#### → {es!r}")
                continue
            n = int(m.group(1))
            if not (1 <= n <= len(L)):
                problems.append(f"易林补遗：{gname}.{name}._src 行号 L{n}超出底本")
                continue
            q = e.get("_引文")
            if isinstance(q, str) and q:
                quote_at(q, n, f"{gname}.{name}._引文")

        # 478 批：组级/条目字符串里的内联 `L####「…」`（省略号分段比对）
        inline_pat = re.compile(r"L(\d+)[^「]{0,30}「([^」]{4,200})」")

        def scan_inline(obj, owner: str) -> None:
            nonlocal n_q
            if not isinstance(obj, dict):
                return
            for kk, vv in obj.items():
                if not isinstance(vv, str):
                    continue
                for mm in inline_pat.finditer(vv):
                    n_q += 1
                    ln2, q2 = int(mm.group(1)), mm.group(2)
                    if not (1 <= ln2 <= len(L)):
                        problems.append(f"易林补遗：{gname}.{owner}{kk} 内联行号 "
                                        f"L{ln2} 超出底本")
                    elif not _seg_hit(q2, L[ln2 - 1]):
                        problems.append(f"易林补遗：{gname}.{owner}{kk} 内联引文不在"
                                        f"所署行 L{ln2} → {q2[:24]!r}")

        scan_inline(group, "")
        for name, e in group.items():
            if isinstance(e, dict):
                scan_inline(e, f"{name}.")
    return n_q, n_a


def _corpus_for_book(book: str) -> Path | None:
    """书名 → 底本文件（**全仓同名多本时优先 `_dz`**）。供裸 `locator`/内联书证用。

    为何不能「先命中先返回」：`渊海子平` 有 `yuan-hai-zi-ping.wikitext.txt` 与
    `yuanhai_ziping_dz.dz.txt`，前者按文件名排序在前；内联书证的源L387 实际
    指 dz 本（wikitext 的 L387 是另一段）。与 [14] 的 load_corpora 同理：
    同名多本一律 `_dz` 优先，否则会把正确引用判成漂移（479 批实踩）。
    """
    base = _book_key(book)
    if not base:
        return None
    cands: list[tuple[int, Path]] = []
    for pv in sorted((DISC / "data" / "sources").glob("*.provenance.json")):
        try:
            meta = json.loads(pv.read_text(encoding="utf-8"))
        except Exception:
            continue
        title = _book_key(meta.get("title") or "")
        if not title or not (base in title or title in base):
            continue
        key = pv.name.split(".")[0]
        dz = DISC / "data" / "sources" / f"{key}.dz.txt"
        wt = DISC / "data" / "sources" / f"{key}.wikitext.txt"
        if dz.exists():
            cands.append((0, dz))
        elif wt.exists():
            cands.append((1, wt))
    return min(cands, key=lambda t: t[0])[1] if cands else None


def _corpora_for_book(book: str) -> list[Path]:
    """书名 → **全部**候选底本（同名 dz／wikitext 都收；479 批内联书证用）。

    内联书证常不写版本（同一《神峰通考》有的行号指 dz、有的指 wikitext），
    只取 `_dz` 会把正确引用判成漂移；候选取全，任一命中即过并记 NOTE。
    """
    base = _book_key(book)
    if not base:
        return []
    out: list[Path] = []
    for pv in sorted((DISC / "data" / "sources").glob("*.provenance.json")):
        try:
            meta = json.loads(pv.read_text(encoding="utf-8"))
        except Exception:
            continue
        title = _book_key(meta.get("title") or "")
        if not title or not (base in title or title in base):
            continue
        key = pv.name.split(".")[0]
        for cand in (DISC / "data" / "sources" / f"{key}.dz.txt",
                     DISC / "data" / "sources" / f"{key}.wikitext.txt"):
            if cand.exists() and cand not in out:
                out.append(cand)
    return out


def check_bare_locators(doc: dict, problems: list[str], notes: list[str] | None = None,
                        lines_of=None, data_of=None) -> int:
    """注册表裸 `locator` 的行锚回验（474 批）。返回**行锚形态**的 locator 数。

    为什么需要它：`liuyao/data/rules/rule_registry.json` 有 6 条 `source.locator`
    写成裸 `L####`（书别在 `source.book`），其中 5 条另有 `quote_in_data` 指向
    `verdict_texts.json` 的引文。但本器此前只认 `quote_in_source`（`<底本>:<行>`）
    与 `quote_in_data` 的**路径可达性**——裸 `L####` 的行号从未被解析，引文是否
    真在那一行也从未对拍（§六.3；这些条目的 `verified: true` 等于自说自话）。

    判据：
      · 裸 `L####`：`source.book` 必须能解析到底本，行号在册；
      · 若 `quote_in_data` 可解析出字符串，该值须落在所署行逐字；
      · `<底本>:<行>` 形态同样回验（行号在册＋引文落位）；
      · 其余 locator 是**章名／说明**（如「月破章第二十七」），不是行锚，
        计入 NOTE、不判红——口径与「裸指针必须能解析」区分开。

    `lines_of` / `data_of` 供 selftest 注入夹具；正式路径现场读。
    """
    cache: dict[str, list[str] | None] = {}

    def get_lines(book: str) -> list[str] | None:
        if lines_of is not None:
            return lines_of(book)
        if book not in cache:
            p = _corpus_for_book(book)
            cache[book] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                           if p else None)
        return cache[book]

    def get_quote(ref: str):
        target, _, ptr = str(ref).partition("#")
        if not target or not ptr:
            return None
        if data_of is not None:
            return _dig(data_of(target), ptr)[0]
        tp = _resolve_any(target)
        if tp is None:
            return None
        try:
            return _dig(json.loads(tp.read_text(encoding="utf-8")), ptr)[0]
        except Exception:
            return None

    n = 0
    descriptive = 0
    for _bucket, item in _iter_entries(doc):
        src = item.get("source") or {}
        loc = str(src.get("locator") or "").strip()
        if not loc:
            continue
        rid = item.get("rule_id") or item.get("id") or "?"
        q = get_quote(src.get("quote_in_data"))
        m = re.fullmatch(r"L(\d+)", loc)
        if m:
            n += 1
            book = str(src.get("book") or "")
            if not book:
                problems.append(f"{rid}.locator={loc}：裸行号缺 source.book，无法定书")
                continue
            L = get_lines(book)
            if L is None:
                problems.append(f"{rid}.locator={loc}：书名不可解析 → {book}")
                continue
            ln = int(m.group(1))
            if not (1 <= ln <= len(L)):
                problems.append(f"{rid}.locator={loc}：超出底本 {book}（共 {len(L)} 行）")
                continue
            if isinstance(q, str) and q and _verdict_plain(q) not in _verdict_plain(L[ln - 1]):
                problems.append(f"{rid}.locator={loc}：quote_in_data 的引文不在所署行 → "
                                f"{q[:26]!r}")
            continue
        m2 = _VERDICT_LOCATOR.fullmatch(loc)
        if m2:
            n += 1
            f, ln = m2.group(1), int(m2.group(2))
            if lines_of is not None:
                L = lines_of(f)
            else:
                p = _resolve_any(f)
                L = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                     if p else None)
            if L is None:
                problems.append(f"{rid}.locator：底本不存在 {f}")
                continue
            if not (1 <= ln <= len(L)):
                problems.append(f"{rid}.locator={loc}：行号超出底本（共 {len(L)} 行）")
                continue
            if isinstance(q, str) and q and _verdict_plain(q) not in _verdict_plain(L[ln - 1]):
                problems.append(f"{rid}.locator={loc}：quote_in_data 的引文不在所署行 → "
                                f"{q[:26]!r}")
            continue
        descriptive += 1
    if descriptive and notes is not None:
        notes.append(f"裸 locator：{descriptive} 条 locator 为章名/说明（非行锚），不判红")
    return n


def check_nayin_quxiang(doc: dict, problems: list[str], lines_of=None) -> int:
    """纳音取象 60 格的底本行锚回验（475 批）。返回格数。

    为什么需要它：`nayin_quxiang.json` 的 `_meta.性质名口径` 自称「引文字段一律照录
    底本原字」。八字 [14] 是「纳音取象表 data↔内核同步」（`sync_nayin_engine`），
    只核 data↔core 的干支/性质名/行号三点，**不碰底本原文**；真正扫「源L」的
    `check_source_readings.py` 只扫 `references/`，对本表 `--doc` 运行得 **0 条可验**。
    60 条 `性质行 + 性质引文` 的底本逐字长期没有机械回验（§六.3）。

    判据：
      · `_meta.书源` 必须点名 `data/sources/<书>`，文件在盘；`L179-L309` 若出现，两端在册；
      · 每格 `性质行` 为裸 `L####`、行号在册；`性质引文` 落在该行逐字；
      · `性质名` 必须能在 `性质引文` 中命中（名称是引文去掉干支前缀/系词的产物）；
      · 键与 `ganzhi` 必须一致；
      · 【478 批】`_meta` 里的内联 `L####「…」`（如 L298「已卯自死之水」）也按
        所署行核，省略号按段拆分。

    `lines_of` 供 selftest 注入夹具底本；正式路径现场读。
    """
    e = (doc or {}).get("纳音性质")
    if not isinstance(e, dict) or not e:
        problems.append("纳音取象：纳音性质缺失或为空——0 结果 ≠ 通过")
        return 0
    meta = (doc or {}).get("_meta") or {}
    src = str(meta.get("书源") or "")
    fm = re.search(r"(data/sources/[A-Za-z0-9_.\-]+)", src)
    if not fm:
        problems.append("纳音取象：_meta.书源 未点名底本")
        return 0
    f = fm.group(1)
    if lines_of is not None:
        L = lines_of(f)
    else:
        p = _resolve_any(f)
        L = (p.read_text(encoding="utf-8", errors="replace").splitlines()
             if p else None)
    if L is None:
        problems.append(f"纳音取象：底本不存在 {f}")
        return len(e)
    for a, b in re.findall(r"L(\d+)(?:-L?(\d+))?", src):
        for n in (a, b):
            if n and not (1 <= int(n) <= len(L)):
                problems.append(f"纳音取象：_meta.书源 行号 L{n} 超出底本（共 {len(L)} 行）")
    n_ok = 0
    for gz, item in e.items():
        if not isinstance(item, dict):
            problems.append(f"纳音取象：{gz} 不是对象")
            continue
        n_ok += 1
        if str(item.get("ganzhi") or "") != gz:
            problems.append(f"纳音取象：{gz}.ganzhi 与键不符 → {item.get('ganzhi')!r}")
        lref = str(item.get("性质行") or "").strip()
        m = re.fullmatch(r"L(\d+)", lref)
        if not m:
            problems.append(f"纳音取象：{gz}.性质行 必须是裸 L#### → {lref!r}")
            continue
        ln = int(m.group(1))
        if not (1 <= ln <= len(L)):
            problems.append(f"纳音取象：{gz}.性质行 L{ln} 超出底本")
            continue
        quote = str(item.get("性质引文") or "")
        name = str(item.get("性质名") or "")
        if not quote or not name:
            problems.append(f"纳音取象：{gz} 缺性质引文/性质名")
            continue
        if _verdict_plain(quote) not in _verdict_plain(L[ln - 1]):
            problems.append(f"纳音取象：{gz}.性质引文 不在所署行 {f}:{ln} → {quote[:24]!r}")
            continue
        if _verdict_plain(name) not in _verdict_plain(quote):
            problems.append(f"纳音取象：{gz}.性质名 不在性质引文中 → {name!r}")

    # 478 批：_meta 里的内联 `L####「…」`（如 L298「已卯自死之水」）
    inline_pat = re.compile(r"L(\d+)[^「]{0,30}「([^」]{4,200})」")
    inline_n = 0
    for k, v in meta.items():
        if not isinstance(v, str):
            continue
        for mm in inline_pat.finditer(v):
            inline_n += 1
            ln, q = int(mm.group(1)), mm.group(2)
            if not (1 <= ln <= len(L)):
                problems.append(f"纳音取象：_meta.{k} 内联行号 L{ln} 超出底本")
            elif not _seg_hit(q, L[ln - 1]):
                problems.append(f"纳音取象：_meta.{k} 内联引文不在所署行 L{ln} → "
                                f"{q[:24]!r}")
    if inline_n == 0:
        problems.append("纳音取象：_meta 0 条内联书源引文——0 结果 ≠ 通过")
    return n_ok


def check_narrative_anchors(doc: dict, problems: list[str], lines_of=None) -> int:
    """叙述层其余 `quote/src` 行锚回验（476 批）。返回字段数。

    为什么需要它：`narrative_templates.json` 的 `pattern_hints.liu_shen_kongwang`、
    `liu_shen_chishi`、`yigua_yishi` 三组 `_meta` 都写「每条 `quote` 为底本逐字
    子串，`src` 为主源行号」，但它们的 `src` 是 `data/sources/<书>:L###`（冒号后
    带 `L`），不在 470 批 `file:NNNN` 的扫描面；[14] 只认「《书名》源L」。10 条
    `quote/src` 因此长期无门（§六.3）。

    判据：`src` 必须是 `data/sources/<书>:L####`，行号在册，`quote` 落在该行逐字。
    `lines_of` 供 selftest 注入夹具底本；正式路径现场读。
    """
    ph = (doc or {}).get("pattern_hints") or {}
    targets: list[tuple[str, dict]] = []
    ks = ph.get("liu_shen_kongwang") or {}
    if isinstance(ks, dict) and isinstance(ks.get("歌源"), dict):
        targets.append(("liu_shen_kongwang.歌源", ks["歌源"]))
    for sec in ("liu_shen_chishi", "yigua_yishi"):
        for k, v in (ph.get(sec) or {}).items():
            if isinstance(v, dict) and v.get("quote") and v.get("src"):
                targets.append((f"{sec}.{k}", v))
    # 481 批：家宅取象 `_出处` 的内联 `L####「…」`（L2533 夹注是改写，不按逐字）
    jz = (doc or {}).get("jiazhai_take_image") or {}
    jz_src = str(jz.get("_出处") or "")
    jz_file = re.search(r"(data/sources/[A-Za-z0-9_.\-]+)", jz_src)
    if jz_file:
        for mm in re.finditer(r"L(\d+)\s*「([^」]{4,200})」", jz_src):
            targets.append((
                f"jiazhai_take_image._出处:L{mm.group(1)}",
                {"quote": mm.group(2),
                 "src": f"{jz_file.group(1)}:L{mm.group(1)}"}))
    if not targets:
        problems.append("叙述层引文：0 条 quote/src——0 结果 ≠ 通过")
        return 0
    cache: dict[str, list[str] | None] = {}

    def get_lines(f: str) -> list[str] | None:
        if lines_of is not None:
            return lines_of(f)
        if f not in cache:
            p = _resolve_any(f)
            cache[f] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                        if p else None)
        return cache[f]

    n = 0
    for label, e in targets:
        q = e.get("quote")
        if not q:
            continue
        n += 1
        src = str(e.get("src") or "").strip()
        m = re.fullmatch(r"(data/sources/[^:]+):L(\d+)", src)
        if not m:
            problems.append(f"叙述层引文：{label}.src 缺行号出处 → {src!r}")
            continue
        f, ln = m.group(1), int(m.group(2))
        L = get_lines(f)
        if L is None:
            problems.append(f"叙述层引文：{label}.src 的底本不存在 {f}")
            continue
        if not (1 <= ln <= len(L)):
            problems.append(f"叙述层引文：{label}.src 行号 L{ln} 超出底本（共 {len(L)} 行）")
            continue
        if _verdict_plain(q) not in _verdict_plain(L[ln - 1]):
            problems.append(f"叙述层引文：{label}.quote 不在所署行 {f}:{ln} → "
                            f"{str(q)[:26]!r}")

    # 487 批：自由文本字段的内联引用（歌源摘要 / 口径散文）
    gs = (ph.get("liu_shen_chishi") or {}).get("歌源")
    if isinstance(gs, str) and gs:
        n += 1
        mg = re.search(r"(data/sources/[A-Za-z0-9_.\-]+):L(\d+)-L(\d+)", gs)
        if not mg:
            problems.append("叙述层引文：liu_shen_chishi.歌源 缺 L###-L### 范围 → "
                            f"{gs[:30]!r}")
        else:
            f, a, b = mg.group(1), int(mg.group(2)), int(mg.group(3))
            L = get_lines(f)
            if L is None:
                problems.append(f"叙述层引文：liu_shen_chishi.歌源 的底本不存在 {f}")
            elif not (1 <= a <= b <= len(L)):
                problems.append(f"叙述层引文：liu_shen_chishi.歌源 的范围 L{a}-L{b} "
                                f"超出底本（共 {len(L)} 行）")
            else:
                pairs = re.findall(r"(青龙|朱雀|勾陈|螣蛇|鰧蛇|白虎|玄武)＝'([^']+)'", gs)
                if len(pairs) != b - a + 1:
                    problems.append(f"叙述层引文：liu_shen_chishi.歌源 有 {len(pairs)} 段，"
                                    f"但范围 L{a}-L{b} 是 {b - a + 1} 行")
                for i, (name, q) in enumerate(pairs):
                    ln = a + i
                    if ln > b:
                        break
                    line = L[ln - 1]
                    # 底本作「鰧蛇」、数据写「螣蛇」，两种写法都认（同字异形）
                    name_ok = any(v in line for v in
                                  (name, name.replace("螣", "鰧"), name.replace("鰧", "螣")))
                    if not name_ok:
                        problems.append(f"叙述层引文：liu_shen_chishi.歌源 第 {i + 1} 段"
                                        f"「{name}」不在所署行 L{ln}")
                    if _fold(q) not in _fold(line):
                        problems.append(f"叙述层引文：liu_shen_chishi.歌源 「{name}」的"
                                        f"引文不在所署行 L{ln} → {q[:24]!r}")
    kj = (ph.get("yigua_yishi") or {}).get("口径")
    if isinstance(kj, str) and kj:
        n += 1
        f = None
        for v in (ph.get("yigua_yishi") or {}).values():
            if isinstance(v, dict):
                mm = re.search(r"(data/sources/[A-Za-z0-9_.\-]+):", str(v.get("src") or ""))
                if mm:
                    f = mm.group(1)
                    break
        if not f:
            problems.append("叙述层引文：yigua_yishi.口径 缺可解析的底本（同组 src 为空）")
        else:
            L = get_lines(f)
            if L is None:
                problems.append(f"叙述层引文：yigua_yishi.口径 的底本不存在 {f}")
            else:
                for mm in re.finditer(r"源L(\d+)(?:「([^」]{2,200})」)?", kj):
                    ln = int(mm.group(1))
                    q = mm.group(2)
                    if not (1 <= ln <= len(L)):
                        problems.append(f"叙述层引文：yigua_yishi.口径 的源L{ln} 超出底本"
                                        f"（共 {len(L)} 行）")
                    elif q and _fold(q) not in _fold(L[ln - 1]):
                        problems.append(f"叙述层引文：yigua_yishi.口径 的内联引文不在 "
                                        f"L{ln} → {q[:24]!r}")
    return n


def check_verdict_text_anchors(doc: dict, problems: list[str], lines_of=None) -> int:
    """六爻 `verdict_texts` 的「文件+L」行锚回验（477 批）。返回字段数。

    为什么需要它：
      · `direction_cap_quotes.*` 的 `locator` 写成 `<file>.txt L####`，5 条 quote
        只被 474 批间接覆盖（经 registry 的 L####）；locator 自身若漂移无人拦。
      · `step5_classical_notes.officer_tomb_wang_you_jiu.basis` 写
        「随鬼入墓章覺子总论（zengshan_buyi.wikitext.txt L685）」——实测该引文
        在 **L687**（覺子曰段），L685 是「古有日墓…」另一行。477 批首跑即抓到。
      · 其余 `step5_classical_notes` 用「源L」或章名，归 [14]/NOTE 面，不在此列。

    判据：`<file> L<line>` 行号在册；`direction_cap_quotes.quote` 与
    `step5_classical_notes.text` 里的 `「…」` 引文须落在该行逐字。
    `lines_of` 供 selftest 注入夹具底本；正式路径现场读。
    """
    cache: dict[str, list[str] | None] = {}

    def get_lines(f: str) -> list[str] | None:
        if lines_of is not None:
            return lines_of("data/sources/" + f)
        key = "data/sources/" + f
        if key not in cache:
            p = _resolve_any(key)
            cache[key] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                          if p else None)
        return cache[key]

    n = 0
    for k, e in ((doc or {}).get("direction_cap_quotes") or {}).items():
        if not isinstance(e, dict):
            continue
        loc = str(e.get("locator") or "").strip()
        m = re.fullmatch(r"([A-Za-z0-9_.\-]+\.txt) L(\d+)", loc)
        q = e.get("quote")
        if not m or not q:
            continue
        n += 1
        f, ln = m.group(1), int(m.group(2))
        L = get_lines(f)
        if L is None:
            problems.append(f"裁决引文：direction_cap_quotes.{k} 底本不存在 {f}")
            continue
        if not (1 <= ln <= len(L)):
            problems.append(f"裁决引文：direction_cap_quotes.{k} 行号 L{ln} 超出底本")
            continue
        if _fold(q) not in _fold(L[ln - 1]):
            problems.append(f"裁决引文：direction_cap_quotes.{k}.quote 不在所署行 "
                            f"{f}:{ln} → {str(q)[:26]!r}")
    for k, e in ((doc or {}).get("step5_classical_notes") or {}).items():
        if not isinstance(e, dict):
            continue
        basis = str(e.get("basis") or "")
        m = re.search(r"([A-Za-z0-9_.\-]+\.txt) L(\d+)", basis)
        if not m:
            continue
        n += 1
        f, ln = m.group(1), int(m.group(2))
        L = get_lines(f)
        if L is None:
            problems.append(f"裁决引文：step5_classical_notes.{k} 底本不存在 {f}")
            continue
        if not (1 <= ln <= len(L)):
            problems.append(f"裁决引文：step5_classical_notes.{k} 行号 L{ln} 超出底本")
            continue
        qs = re.findall(r"「([^」]{4,400})」", str(e.get("text") or ""))
        if not qs:
            problems.append(f"裁决引文：step5_classical_notes.{k} 有行锚但 text 无「」引文")
            continue
        for q in qs:
            if _fold(q) not in _fold(L[ln - 1]):
                problems.append(f"裁决引文：step5_classical_notes.{k}.text 引文不在"
                                f"所署行 {f}:{ln} → {q[:26]!r}")
    return n


def check_registry_inline_quotes(doc: dict, problems: list[str],
                                 notes: list[str] | None = None,
                                 lines_of=None, books_of=None) -> int:
    """注册表散文里的「《书名》源L####「…」」内联书证回验（479 批）。

    为什么需要它：`bazi/data/rules/rule_registry.json` 的 `locator` /
    `provenance_note_*` / `applicability` 等字段把书证写成散文：
    「《五行精纪》源L1999 逐字「甲戊庚牛羊…」」。八字 [10] 只扫 `references/`，
    [12] 只验 `quote_in_source`／`quote_in_data` 的**结构化值**，这些内联引文
    此前无人回验。先实测 22 条，逐条按所署行核。

    书名归属：散文里的裸 `源L` 常省略书名（同一段先写《神峰通考》再连引数条），
    故候选书名 = 引文前最近的《…》 ＋ 本条 `source.book` 里的全部书名；候选
    底本 = 同名 dz／wikitext **全收**（同一书不同引文可能分别指两版）。任一
    候选命中即过；若命中的书不是最近书名，记 NOTE（书名歧义，不判红）。
    引文前无任何书名、或全部候选都解析不到、或行号越界、或引文不符 → 判红。

    `lines_of` / `books_of` 供 selftest 注入夹具；正式路径现场解析。
    """
    cache: dict[str, list[str] | None] = {}

    def get_lines(key: str) -> list[str] | None:
        if lines_of is not None:
            return lines_of(key)
        if key not in cache:
            p = Path(key)
            cache[key] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                          if p.exists() else None)
        return cache[key]

    def paths_for(book: str) -> list[str]:
        if books_of is not None:
            return books_of(book)
        return [str(p) for p in _corpora_for_book(book)]

    BOOK_RE = re.compile(r"《([^》]{2,24})》")
    PAT = re.compile(r"源L(\d+)[^「]{0,20}「([^」]{4,200})」")
    n = 0

    for _bucket, item in _iter_entries(doc):
        rid = item.get("rule_id") or item.get("id") or "?"
        src = item.get("source") or {}
        src_books = BOOK_RE.findall(str(src.get("book") or ""))

        def walk(o, path: str) -> None:
            nonlocal n
            if isinstance(o, dict):
                for k, v in o.items():
                    walk(v, f"{path}.{k}")
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    walk(v, f"{path}[{i}]")
            elif isinstance(o, str):
                for m in PAT.finditer(o):
                    n += 1
                    bms = list(BOOK_RE.finditer(o[:m.start()]))
                    nearest = bms[-1].group(1) if bms else ""
                    cands: list[str] = []
                    for b in ([nearest] if nearest else []) + src_books:
                        if b and b not in cands:
                            cands.append(b)
                    if not cands:
                        problems.append(f"注册表内联书证：{rid}{path} 的"
                                        f"源L{m.group(1)} 前无《书名》→ {m.group(2)[:24]!r}")
                        continue
                    ln = int(m.group(1))
                    q = m.group(2)
                    resolved = max_len = 0
                    hit = ""
                    for b in cands:
                        for key in paths_for(b):
                            L = get_lines(key)
                            if L is None:
                                continue
                            resolved += 1
                            max_len = max(max_len, len(L))
                            if 1 <= ln <= len(L) and _seg_hit(q, L[ln - 1]):
                                hit = b
                                break
                        if hit:
                            break
                    if not resolved:
                        problems.append(f"注册表内联书证：{rid}{path} 书名全部不可解析 → "
                                        f"{cands}")
                    elif not hit:
                        if ln > max_len:
                            problems.append(f"注册表内联书证：{rid}{path} 源L{ln} 超出底本"
                                            f"（最长 {max_len} 行）")
                        else:
                            problems.append(f"注册表内联书证：{rid}{path} 「{q[:24]}」"
                                            f" 不在所署源L{ln}（候选 {cands}）")
                    elif nearest and hit != nearest and notes is not None:
                        notes.append(f"注册表内联书证：{rid} 源L{ln} 书名歧义"
                                     f"（近指《{nearest}》），按《{hit}》命中，不判红")
        walk(item, "")
    if n == 0:
        problems.append("注册表内联书证：0 条——0 结果 ≠ 通过")
    return n


def check_verdict_inline_quotes(doc: dict, problems: list[str],
                                notes: list[str] | None = None,
                                lines_of=None, books_of=None) -> int:
    """八字 `verdicts.json` 散文里的「源L####「…」」内联书证（480 批）。

    为什么需要它：`从格引文._meta` 写「data/sources/<书> 源L5265（…作
    「从儿不管身强弱，只要吾儿又得儿」）」；`cong_cai_sanming.note`
    写「源L1704。…「若逢根气命损无猜」…」。465 批只验带 `locator` 的结构化条目，
    [10] 只扫 references，这两条内联引文此前无门（§六.3）。

    书名归属：优先同一串里 `data/sources/<file>` 路径；其次引文前最近《书名》
    （同名 dz/wikitext 全收）；再次条目键后缀 `_sanming`＝《三命通会》（本表既有
    命名约定，`zheng_guan_chun_yi_sanming` 等均同）。仍无归属 → 判红。
    `lines_of` / `books_of` 供 selftest 注入夹具；正式路径现场解析。
    """
    cache: dict[str, list[str] | None] = {}

    def get_lines(key: str) -> list[str] | None:
        if lines_of is not None:
            return lines_of(key)
        if key not in cache:
            p = _resolve_any(key)
            cache[key] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                          if p else None)
        return cache[key]

    def paths_for(book: str) -> list[str]:
        if books_of is not None:
            return books_of(book)
        return [str(p) for p in _corpora_for_book(book)]

    BOOK_RE = re.compile(r"《([^》]{2,24})》")
    PATH_RE = re.compile(r"(data/sources/[A-Za-z0-9_.\-]+)")
    PAT = re.compile(r"源L(\d+)[^「]{0,120}「([^」]{4,200})」")
    n = 0

    def walk(o, entry: str) -> None:
        nonlocal n
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, dict):
                    walk(v, str(k))
                else:
                    walk(v, entry)
        elif isinstance(o, list):
            for v in o:
                walk(v, entry)
        elif isinstance(o, str):
            for m in PAT.finditer(o):
                n += 1
                before = o[:m.start()]
                pm = list(PATH_RE.finditer(before))
                bms = list(BOOK_RE.finditer(before))
                cand_paths: list[str] = []
                book = ""
                if pm:
                    cand_paths = [pm[-1].group(1)]
                elif bms:
                    book = bms[-1].group(1)
                elif entry.endswith("_sanming"):
                    book = "三命通会"
                if not cand_paths and book:
                    cand_paths = paths_for(book)
                if not cand_paths:
                    problems.append(f"裁决内联书证：{entry or '?'} 源L{m.group(1)}"
                                    f" 无底本归属 → {m.group(2)[:24]!r}")
                    continue
                ln, q = int(m.group(1)), m.group(2)
                resolved = max_len = 0
                hit = False
                for key in cand_paths:
                    L = get_lines(key)
                    if L is None:
                        continue
                    resolved += 1
                    max_len = max(max_len, len(L))
                    if 1 <= ln <= len(L) and _seg_hit(q, L[ln - 1]):
                        hit = True
                        break
                if not resolved:
                    problems.append(f"裁决内联书证：{entry or '?'} 底本不存在 {cand_paths}")
                elif not hit:
                    if ln > max_len:
                        problems.append(f"裁决内联书证：{entry or '?'} 源L{ln} 超出底本"
                                        f"（最长 {max_len} 行）")
                    else:
                        problems.append(f"裁决内联书证：{entry or '?'} 「{q[:24]}」"
                                        f" 不在所署源L{ln}（候选 {book or cand_paths}）")
    walk(doc or {}, "")
    if n == 0:
        problems.append("裁决内联书证：0 条——0 结果 ≠ 通过")
    return n


def check_code_anchors(problems: list[str], files=None, lines_of=None) -> int:
    """`core/`、`scripts/` 注释里的「<file>.txt:<行>「…」」逐字回验（482 批）。

    为什么需要它：内核注释把书证写成 `file:242「亥卯未亡神在寅…」` 形态，
    既无「源L」前缀，也不在数据表里；[14]/[10] 只扫 references 与「源L」，
    这些代码级引文此前无门。先实测：八字 5 处命中。六爻副本同一份
    `shensha.py` 引的是《兰台妙选》《命理探源》等**八字专有底本**（六爻
    `data/sources/` 无此三书），按「各科独立可跑、不跨科读底本」口径不在
    六爻侧挂门（已在 CHANGELOG 登记为跨科注释遗留，不在本批裁定）。
    判据：底本 `data/sources/<file>` 在盘、行号在册、引文按省略号分段落位；
    `files` / `lines_of` 供 selftest 注入夹具。
    """
    cache: dict[str, list[str] | None] = {}

    def get_lines(key: str) -> list[str] | None:
        if lines_of is not None:
            return lines_of(key)
        if key not in cache:
            p = _resolve_any(key)
            cache[key] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                          if p else None)
        return cache[key]

    PAT = re.compile(r"([A-Za-z0-9_.\-]+\.txt)(?:\s+|:)(\d+)"
                     r"[^「]{0,30}「([^」]{4,200})」")
    n = 0
    sources = files if files is not None else [
        (str(p.relative_to(DISC)), p.read_text(encoding="utf-8", errors="replace"))
        for root in (DISC / "core", DISC / "scripts")
        for p in sorted(root.glob("**/*.py"))]
    for label, text in sources:
        for m in PAT.finditer(text):
            n += 1
            f, ln, q = m.group(1), int(m.group(2)), m.group(3)
            L = get_lines(f"data/sources/{f}")
            if L is None:
                problems.append(f"代码书证：{label} 底本不存在 {f}")
                continue
            if not (1 <= ln <= len(L)):
                problems.append(f"代码书证：{label} {f}:{ln} 超出底本（共 {len(L)} 行）")
                continue
            if not _seg_hit(q, L[ln - 1]):
                problems.append(f"代码书证：{label} 「{q[:24]}」不在 {f}:{ln}")
    if n == 0:
        problems.append("代码书证：0 条——0 结果 ≠ 通过")
    return n


def check_usegod_notes(doc: dict, problems: list[str], lines_of=None) -> int:
    """`question_use_gods` 各族的 note 内「file L####『…』」回验（483 批）。

    为什么需要它：`build_question_use_gods.py` 明写「note 不参与核验」，
    但 families[71] 的 note 把案例起句与断辞都挂在 `zengshan_buyi.wikitext.txt
    L1120` 上——实测起句在 L1120，断辞「世爻之鬼，乃滿腹憂疑之象」在 **L1129**。
    这类 note 行锚此前无门（§六.3）。

    判据：note 内 `<file> L####` 后 **30 字内**的 `『…』` 按所署行逐字核
    （30 字外的是标签/泛指，不冒充书证）；无锚引文不计数。
    `lines_of` 供 selftest 注入夹具；正式路径现场读。
    """
    fams = (doc or {}).get("families")
    if not isinstance(fams, list) or not fams:
        problems.append("用神词典注记：families 缺失或为空——0 结果 ≠ 通过")
        return 0
    cache: dict[str, list[str] | None] = {}

    def get_lines(f: str) -> list[str] | None:
        if lines_of is not None:
            return lines_of("data/sources/" + f)
        key = "data/sources/" + f
        if key not in cache:
            p = _resolve_any(key)
            cache[key] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                          if p else None)
        return cache[key]

    A = re.compile(r"([A-Za-z0-9_.\-]+\.txt)\s*L(\d+)")
    Q = re.compile(r"『([^』]{4,200})』")
    n = 0
    for i, fam in enumerate(fams):
        if not isinstance(fam, dict):
            continue
        note = str(fam.get("note") or "")
        anchors = [(m.start(), m.end(), m.group(1), int(m.group(2)))
                   for m in A.finditer(note)]
        for qm in Q.finditer(note):
            before = [a for a in anchors
                      if 0 <= qm.start() - a[1] <= 30]
            after = [a for a in anchors
                     if 0 <= a[0] - qm.end() <= 30]
            if before:
                _, _, f, ln = max(before, key=lambda a: a[1])
            elif after:
                _, _, f, ln = min(after, key=lambda a: a[0])
            else:
                continue
            n += 1
            L = get_lines(f)
            if L is None:
                problems.append(f"用神词典注记：families[{i}] 底本不存在 {f}")
                continue
            if not (1 <= ln <= len(L)):
                problems.append(f"用神词典注记：families[{i}] {f}:L{ln} 超出底本")
                continue
            if _seg_hit(qm.group(1), L[ln - 1]):
                continue
            # 同一 note 里若另有邻近锚能命中，按「锚点次序错」处理（不判红）
            alt = [(a[2], a[3]) for a in anchors
                   if 0 <= qm.start() - a[0] <= 120 and (a[2], a[3]) != (f, ln)]
            hit = False
            for af, aln in alt:
                AL = get_lines(af)
                if AL and 1 <= aln <= len(AL) and _seg_hit(qm.group(1), AL[aln - 1]):
                    problems.append(f"用神词典注记：families[{i}] 引文不在 {f}:L{ln}，"
                                    f"实应挂 {af}:L{aln}（同 note 另锚命中）")
                    hit = True
                    break
            if not hit:
                problems.append(f"用神词典注记：families[{i}] 「{qm.group(1)[:24]}」"
                                f" 不在 {f}:L{ln}")
    if n == 0:
        problems.append("用神词典注记：0 条带锚引文——0 结果 ≠ 通过")
    return n


def check_usegod_family_notes(doc: dict, problems: list[str],
                              lines: list[str] | None = None) -> int:
    """用神词典族注里 `「…」` 的书源回验（491 批）。返回引文段数。

    为什么需要它：`build_question_use_gods.py` 明写「note 不参与核验」，
    family 64–69 的 `note` 有 7 段 `「…」`（占雨/借贷/讨债/六畜/坟墓），
    都称「章内逐字」却无行号锚——[14] 只认 `源L` 形态，此前只核到 1 条。
    判据：每段 `「…」` 须在《增刪卜易》dz＋wikitext 任一底本中逐字出现
    （省略号分段、折叠标点）；`lines` 供 selftest 注入夹具。
    """
    fams = doc.get("families") or []
    if not fams:
        problems.append("用神词典族注：0 个 families——0 结果 ≠ 通过")
        return 0
    if lines is None:
        lines = []
        # 《增刪卜易》在库两版：dz 与 wikitext。wikitext 的 provenance 无 title，
        # `_corpora_for_book` 只认得到 dz；族注引文实测在 wikitext 版，故两版全收。
        for p in sorted((DISC / "data" / "sources").glob("zengshan_buyi*.txt")):
            lines += p.read_text(encoding="utf-8", errors="replace").splitlines()
    n = 0
    for i, fam in enumerate(fams):
        if not isinstance(fam, dict):
            continue
        note = str(fam.get("note") or "")
        for q in re.findall(r"「([^」]{2,200})」", note):
            n += 1
            if not any(_seg_hit(q, line) for line in lines):
                problems.append(f"用神词典族注：families[{i}].note 的引文不在"
                                f"《增刪卜易》底本 → {q[:26]!r}")
    if n == 0:
        problems.append("用神词典族注：0 段「…」引文——0 结果 ≠ 通过")
    return n


def check_usegod_meta(doc: dict, problems: list[str]) -> tuple[int, int]:
    """用神词典 `_meta` 声明数自洽（493 批）。返回 (族数, 键数)。

    为什么需要它：`question_use_gods.json` 的 `_meta.description` 写「195 条
    现代问法」，而 `family_count=74`、`key_count=275`、落盘 entries 合计 275；
    同一份元数据两个数自相矛盾，构建器也照抄 195 写入。判据：族数、键数、
    description 里的「N 条现代问法」三项都须等于实际值。
    """
    meta = doc.get("_meta") or {}
    fams = doc.get("families") or []
    actual_f = len(fams)
    actual_k = sum(len(f.get("entries") or []) for f in fams if isinstance(f, dict))
    fc, kc = meta.get("family_count"), meta.get("key_count")
    if fc != actual_f:
        problems.append(f"用神词典元数据：family_count {fc} ≠ 实际 {actual_f} 族")
    if kc != actual_k:
        problems.append(f"用神词典元数据：key_count {kc} ≠ 实际 {actual_k} 键")
    m = re.search(r"(\d+)\s*条现代问法", str(meta.get("description") or ""))
    if not m:
        problems.append("用神词典元数据：description 未声明「N 条现代问法」")
    elif int(m.group(1)) != actual_k:
        problems.append(f"用神词典元数据：description 声明 {m.group(1)} 条 ≠ "
                        f"实际 {actual_k} 键")
    return actual_f, actual_k


def check_question_classes_notes(doc: dict, problems: list[str],
                                 lines_of=None) -> tuple[int, int]:
    """问题题类表注记的书源回验（488 批）。返回 (行锚数, 引文数)。

    为什么需要它：`question_classes.json` 的 `classes[*].source_gates`／`note`
    有 4 个 `源L####`（题类析出与天气分轨的「书据」），其中 3 处带 `「…」`，
    此前没有任何门读取。现核：书名取同串最近的《…》，经 provenance 解析
    （`_corpus_for_book`，同名多本 `_dz` 优先），行号在册；锚后到下一锚之间的
    首个 `「…」` 须在该行逐字命中。
    `lines_of` 供 selftest 注入底本；正式路径现场读。
    """
    classes = doc.get("classes") or []
    entries = [c for c in classes if isinstance(c, dict)]
    if not entries:
        problems.append("问题题类：0 个 classes 条目——0 结果 ≠ 通过")
        return 0, 0
    cache: dict[str, list[str] | None] = {}

    def get_lines(book: str) -> list[str] | None:
        if lines_of is not None:
            return lines_of(book)
        if book not in cache:
            p = _corpus_for_book(book)
            cache[book] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                           if p else None)
        return cache[book]

    A = re.compile(r"源L(\d+)")
    B = re.compile(r"《([^》]{2,24})》")
    Q = re.compile(r"「([^」]{2,200})」")
    n_ref = n_q = 0
    for i, c in enumerate(entries):
        for field, val in c.items():
            vals = val if isinstance(val, list) else [val]
            for si, s in enumerate(vals):
                if not isinstance(s, str) or "源L" not in s:
                    continue
                where = f"classes[{i}].{field}" + (f"[{si}]" if isinstance(val, list) else "")
                anchors = list(A.finditer(s))
                for j, m in enumerate(anchors):
                    n_ref += 1
                    ln = int(m.group(1))
                    books = B.findall(s[:m.start()])
                    book = books[-1] if books else ""
                    if not book:
                        problems.append(f"问题题类：{where} 的源L{ln} "
                                        "缺《书名》，无法定书")
                        continue
                    L = get_lines(book)
                    if L is None:
                        problems.append(f"问题题类：{where} 的书名不可解析 → "
                                        f"《{book}》")
                        continue
                    if not (1 <= ln <= len(L)):
                        problems.append(f"问题题类：{where} 的源L{ln} "
                                        f"超出底本《{book}》（共 {len(L)} 行）")
                        continue
                    end = anchors[j + 1].start() if j + 1 < len(anchors) else len(s)
                    qm = Q.search(s[m.end():end])
                    if qm:
                        n_q += 1
                        if _fold(qm.group(1)) not in _fold(L[ln - 1]):
                            problems.append(f"问题题类：{where} 的引文不在 "
                                            f"《{book}》源L{ln} → {qm.group(1)[:24]!r}")
    return n_ref, n_q


_PROSE_PATH = re.compile(r"data/sources/[A-Za-z0-9_.\-]+")
_PROSE_BOOK = re.compile(r"《([^》]{2,24})》")
_PROSE_ANCHOR = re.compile(r"(?:源\s*)?(?<![A-Za-z0-9_])L(\d{1,5})")
_PROSE_LOC = re.compile(r"(data/sources/[^:]+):(\d+)")


def _first_locator_path(o) -> str:
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "locator" and isinstance(v, str):
                m = _PROSE_LOC.fullmatch(v.strip())
                if m:
                    return m.group(1)
            got = _first_locator_path(v)
            if got:
                return got
    elif isinstance(o, list):
        for v in o:
            got = _first_locator_path(v)
            if got:
                return got
    return ""


def check_verdicts_prose_anchors(doc: dict, problems: list[str],
                                 lines_of=None, books_of=None) -> int:
    """八字裁决表散文裸行号的在册回验（489 批）。返回解析到的锚数。

    为什么需要它：`bazi/data/verdicts.json` 除 465 的 `locator` 字段与 480 的
    `源L「…」` 内联书证外，还有一批**只写行号、不带引文**的定位声明
    （`_zhuan_wang_meta` 五格 L1657…、`从格._meta` L5265、`cong_sha/cong_cai.note`
    L1668/L1704、`看命口诀.verification_note` L5115/L5137、杂气格 L1734、
    渊海子平 L179）。它们说明「哪一段是哪一格的书源」，此前没有任何门。
    判据：带 `data/sources/<书>` 的按路径；带《书名》的按 provenance
    （`_corpus_for_book`，同名多本 `_dz` 优先）；裸 `源L` 按同条目最近的
    `locator` 底本；行号须在册。紧邻 `「` 的锚由 479/480 覆盖，本门跳过。
    `lines_of` / `books_of` 供 selftest 注入夹具；正式路径现场解析。
    """
    cache: dict[str, list[str] | None] = {}

    def get_lines(f: str) -> list[str] | None:
        if lines_of is not None:
            return lines_of(f)
        if f not in cache:
            p = _resolve_any(f) if f.startswith("data/sources/") else Path(f)
            cache[f] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                        if p and p.is_file() else None)
        return cache[f]

    def path_for_book(b: str) -> str:
        if books_of is not None:
            paths = books_of(b)
            return paths[0] if paths else ""
        p = _corpus_for_book(b)
        return str(p) if p else ""

    n = 0

    def walk(o, where: str, parent) -> None:
        nonlocal n
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, f"{where}.{k}", o)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{where}[{i}]", parent)
        elif isinstance(o, str):
            if not _PROSE_ANCHOR.search(o):
                return
            paths = [(m.start(), m.group(0)) for m in _PROSE_PATH.finditer(o)]
            books = [(m.start(), m.group(1)) for m in _PROSE_BOOK.finditer(o)]
            for m in _PROSE_ANCHOR.finditer(o):
                if "「" in o[m.start():m.start() + 24]:
                    continue
                ln = int(m.group(1))
                before_p = [p for s, p in paths if s <= m.start()]
                f = before_p[-1] if before_p else ""
                if not f:
                    before_b = [b for s, b in books if s <= m.start()]
                    if before_b:
                        f = path_for_book(before_b[-1])
                        if not f:
                            problems.append(f"裁决散文行号：{where} 的《{before_b[-1]}》"
                                            f" 无可解析底本（源L{ln}）")
                            continue
                if not f and parent is not None:
                    f = _first_locator_path(parent)
                if not f:
                    continue
                L = get_lines(f)
                if L is None:
                    problems.append(f"裁决散文行号：{where} 的底本不存在 {f}")
                    continue
                n += 1
                if not (1 <= ln <= len(L)):
                    problems.append(f"裁决散文行号：{where} 的 L{ln} 超出底本 "
                                    f"{f}（共 {len(L)} 行）")

    walk(doc, "$", None)
    if n == 0:
        problems.append("裁决散文行号：0 条可解析锚——0 结果 ≠ 通过")
    return n


_CODE_BOOK = re.compile(r"《([^》]{2,24})》")
_CODE_ANCHOR = re.compile(r"源\s*L(\d+)")
_CODE_QUOTE = re.compile(r"「([^」]{2,300})」")


_CODE_QUOTE_OPEN = 40          # `源L####` 之后多少字内算「同行引文」
_SELFTEST_SKIP = re.compile(r"selftest", re.I)


def _selftest_spans(text: str) -> set[int]:
    """返回模块内 `selftest` 函数（同名含大小写）的 1-based 行号集合。

    495 批为什么需要它：`dev_tools/*.py` 的 `--selftest` 里塞了大量**明知不存在**
    的假书证（`《测试书》源L2`、`《易冒》源L3 另章判语`），那是负例夹具不是真声明；
    不跳过就会把夹具当缺陷。函数名是现行约定（两科各门的负例都叫 selftest）。
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    skip: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _SELFTEST_SKIP.search(node.name):
                skip.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
    return skip


def _code_quote(lines: list[str], i: int, end: int) -> str:
    """取 `源L####` 之后那条引文；行内不闭合才接下一行（495 批）。

    为什么放宽到整行：490 批只看 40 字窗口的**闭合**，超过 40 字的真引文被静默跳过
    （eval 的《子平真诠评注》/《穷通宝鉴》两条长句因此从未被核）。现改为：窗口内找
    开引号，闭合在整行里找；整行没有闭合才接下一行，且下一行在第一个 `」` 之前
    不得再出现新 `「`（否则说明这是下一条引文，不是本条的续行）。
    含 `{…}` 的是 f-string 模板（如 `「{stem}…长生在{br}」`），不是逐字引文，按无引文处理。
    """
    rest = lines[i][end:]
    j = rest.find("「")
    if j < 0 or j > _CODE_QUOTE_OPEN:
        return ""
    seg = rest[j:]
    if "」" not in seg:
        if i + 1 >= len(lines):
            return ""
        nxt = lines[i + 1]
        k = nxt.find("」")
        if k < 0 or "「" in nxt[:k]:
            return ""
        seg += "\n" + nxt
    m = _CODE_QUOTE.search(seg)
    if not m:
        return ""
    q = m.group(1)
    return "" if ("{" in q or "}" in q) else q


def check_bazi_code_anchors(problems: list[str], files=None, lines_of=None,
                            books_of=None) -> tuple[int, int, int]:
    """八字代码注释的 `源L` 书证回验（490 批；495 批扩到 dev_tools／eval）。返回
    (锚数, 带引文锚, 无书名锚)。

    为什么需要它：`scripts/**/*.py` 与 `core/**/*.py` 有 51 个 `源L` 锚
    （`dayun.py` 的岁运五式、虚拱填实、三合补支…），482 只认
    `<file>.txt:<行>「…」`，八字 [10] 只扫 `references/`——这批书证此前无门。
    495 批扩面：`dev_tools/**`（96 锚）与 `eval/**`（12 锚）同样在写「书云源L####」，
    此前完全无人回验；首跑抓到 7 处真错（见 CHANGELOG 第四百九十五批）。
    判据：书名取同行或前 9 行最近的《…》，经 provenance 全收（同名 dz／wikitext），
    行号须在册；引文取同行（行内不闭合才接下一行）的 `「…」`，按省略号分段在该行逐字命中。
    无书名的裸 `源L` 只计数、不判红（留给上一行书名/版式判断，不臆造归属）。
    `selftest` 函数体内的锚一律跳过（那是负例夹具，不是声明）。
    `files` / `lines_of` / `books_of` 供 selftest 注入夹具；正式路径现场读。
    """
    if files is None:
        files = []
        for sub in ("scripts", "core", "dev_tools", "eval"):
            for p in sorted((DISC / sub).rglob("*.py")):
                files.append((str(p.relative_to(DISC)),
                              p.read_text(encoding="utf-8", errors="replace")))
    cache: dict[str, list[str] | None] = {}

    def get_lines(key: str) -> list[str] | None:
        if lines_of is not None:
            return lines_of(key)
        if key not in cache:
            p = _resolve_any(key)
            cache[key] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                          if p and p.is_file() else None)
        return cache[key]

    n_ref = n_q = n_nobook = 0
    for rel, text in files:
        lines = text.splitlines()
        skip_lines = _selftest_spans(text)
        for i, line in enumerate(lines):
            if i + 1 in skip_lines:
                continue
            for m in _CODE_ANCHOR.finditer(line):
                n_ref += 1
                ln = int(m.group(1))
                pre = _CODE_BOOK.findall(line[:m.start()])
                book = pre[-1] if pre else ""
                if not book:
                    for j in range(i - 1, max(-1, i - 9), -1):
                        bs = _CODE_BOOK.findall(lines[j])
                        if bs:
                            book = bs[-1]
                            break
                if not book:
                    n_nobook += 1
                    continue
                paths = (books_of(book) if books_of is not None
                         else [str(p) for p in _corpora_for_book(book)])
                if not paths:
                    # 《》在代码注释里也可能是篇名（如《顺局》），不能当书判红；
                    # 先向上找更早一个可解析书名（《滴天髓》→ 滴天髓两底本）。
                    for j in range(i - 1, max(-1, i - 9), -1):
                        for b in _CODE_BOOK.findall(lines[j]):
                            cand = (books_of(b) if books_of is not None
                                    else [str(p) for p in _corpora_for_book(b)])
                            if cand:
                                paths = cand
                                break
                        if paths:
                            break
                if not paths:
                    n_nobook += 1
                    continue
                q = _code_quote(lines, i, m.end())
                in_range = quoted_ok = False
                for key in paths:
                    L = get_lines(key)
                    if L is None:
                        continue
                    if 1 <= ln <= len(L):
                        in_range = True
                        if not q or _seg_hit(q, L[ln - 1]):
                            quoted_ok = bool(q)
                            break
                if not in_range:
                    problems.append(f"代码源L：{rel}:{i + 1} 的《{book}》源L{ln} "
                                    "超出底本")
                elif q:
                    n_q += 1
                    if not quoted_ok:
                        problems.append(f"代码源L：{rel}:{i + 1} 的《{book}》源L{ln} "
                                        f"引文不在该行 → {q[:26]!r}")
    if n_ref == 0:
        problems.append("代码源L：0 个源L 锚——0 结果 ≠ 通过")
    return n_ref, n_q, n_nobook


_LINE_CLAIM = re.compile(r"语料行\s*(\d+(?:\s*/\s*\d+)*)")
_CLAIM_PATH = re.compile(r"data/sources/[A-Za-z0-9_.\-]+")


def check_registry_line_claims(doc: dict, problems: list[str],
                               lines_of=None, books_of=None) -> int:
    """注册表「语料行 NNNN」声明的在册回验（492 批）。返回行号数。

    为什么需要它：`rule_registry.json` 有 3 处不以 `L####` 写的声明——
    `ming.dayun.locator` 的「语料行 2608/2612」与 `_uncovered[1].locator` 的
    「语料行 2452」。465 只看 verdicts、474 只跑六爻，这类声明此前无门。
    判据：底本优先取同串 `data/sources/<书>` 路径；否则 `source.corpus_files`；
    否则 `source.book` 经 provenance（同名多本全收）；每个行号须在任一底本在册。
    `lines_of` / `books_of` 供 selftest 注入夹具；正式路径现场读。
    """
    cache: dict[str, list[str] | None] = {}

    def get_lines(key: str) -> list[str] | None:
        if lines_of is not None:
            return lines_of(key)
        if key not in cache:
            p = _resolve_any(key)
            cache[key] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                          if p and p.is_file() else None)
        return cache[key]

    n = 0
    for _bucket, item in _iter_entries(doc):
        src = item.get("source") or {}
        if not isinstance(src, dict):
            continue
        rid = item.get("rule_id") or item.get("id") or "?"

        def walk(o, where: str) -> None:
            nonlocal n
            if isinstance(o, dict):
                for k, v in o.items():
                    walk(v, f"{where}.{k}")
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    walk(v, f"{where}[{i}]")
            elif isinstance(o, str):
                for m in _LINE_CLAIM.finditer(o):
                    nums = [int(x) for x in re.findall(r"\d+", m.group(1))]
                    paths = _CLAIM_PATH.findall(o)
                    if not paths:
                        cf = src.get("corpus_files") or []
                        paths = [str(p) for p in (cf if isinstance(cf, list) else [cf]) if p]
                    if not paths:
                        book = ""
                        for b in re.findall(r"《([^》]{2,24})》", str(src.get("book") or "")):
                            book = b
                            break
                        if book:
                            paths = (books_of(book) if books_of is not None
                                     else [str(p) for p in _corpora_for_book(book)])
                    if not paths:
                        problems.append(f"注册表语料行：{rid}{where} 的「语料行 "
                                        f"{m.group(1)}」无可解析底本")
                        continue
                    for ln in nums:
                        n += 1
                        ok = False
                        for key in paths:
                            L = get_lines(key)
                            if L and 1 <= ln <= len(L):
                                ok = True
                                break
                        if not ok:
                            problems.append(f"注册表语料行：{rid}{where} 的语料行 "
                                            f"{ln} 超出底本（{paths[0]}）")

        walk(item, "")
    if n == 0:
        problems.append("注册表语料行：0 个行号声明——0 结果 ≠ 通过")
    return n


def check_registry_books(doc: dict, problems: list[str], books_of=None) -> int:
    """注册表 `source.book` 里的每个《书名》都必须有在盘底本（484 批）。

    为什么需要它：`ming.dayun_yindong` 的 `source.book` 列了《千里明镜》，
    `data/sources/` 并无此书（provenance 只有《千里命稿》）；其 locator 的
    「《千里明镜》源L308／L329 两条自足算例」实测两行正在 `qianli_minggao_dz`
    L308/L329——书名误写，gates 只验行号/引文，从未检查书名本身。
    判据：`source.book` 的每个《…》经 provenance 解析，无底本即判红。
    `books_of` 供 selftest 注入；正式路径 `_corpora_for_book` 现场解析。
    """
    BOOK_RE = re.compile(r"《([^》]{2,24})》")
    n = 0
    for _bucket, item in _iter_entries(doc):
        rid = item.get("rule_id") or item.get("id") or "?"
        src = item.get("source") or {}
        for b in BOOK_RE.findall(str(src.get("book") or "")):
            n += 1
            paths = books_of(b) if books_of is not None else _corpora_for_book(b)
            if not paths:
                problems.append(f"注册表书目：{rid} 的《{b}》无在盘底本")
    if n == 0:
        problems.append("注册表书目：0 个书名——0 结果 ≠ 通过")
    return n


_DC_CHAPTER = re.compile(r"^《易冒》(\S+?)（(?:底本 )?L(\d+) 起）$")
_DC_QUOTE = re.compile(r"^《易冒》源L(\d+) 逐字「(.*)」$")
_DC_HEADING = re.compile(r"[\u4e00-\u9fff]+章(第[\u4e00-\u9fff]+)?")


def check_domain_citations(doc: dict, problems: list[str],
                           lines: list[str] | None = None) -> tuple[int, int]:
    """分占域判据引文库的章界＋行内逐字回验（485 批）。返回 (域数, 引文数)。

    为什么需要它：`domain_citations.json` 自称「一行一锚一逐字，行号均可回指底本」，
    但 `consumed_by_engine=false`，全仓无代码读取——132 个 L 引用此前没有一道门。
    只看「引文是否在该行」仍不够：**行对而章错**同样是把引用挂到别的篇章。故按
    `章节` 里的「L#### 起」定位章标题行，再以该章到下一章标题为行界，要求：
      · `章节` 的锚点必须落在标题行（章名按标题前缀匹配，允许数据只写「X章」）；
      · `引文` 必须在本章行界内，且 `_fold` 后逐字命中所署行；
      · `_source_lines` 非空；若带行号，须与 `章节` 同锚；
      · `_extension_note` 的「N 域」须等于实际域数（声明数自洽）。
    `lines` 供 selftest 注入夹具底本；正式路径读 `data/sources/yimao_dz.dz.txt`。
    """
    domains = doc.get("domains") or {}
    entries = [(k, v) for k, v in domains.items() if isinstance(v, dict)]
    if not entries:
        problems.append("占域引文：0 个域条目——0 结果 ≠ 通过")
        return 0, 0
    # 在盘数据把总注记放在 domains 里（字符串键），也接受根级写法。
    note = str(doc.get("_extension_note") or domains.get("_extension_note") or "")
    m_note = re.search(r"本表现收\s*(\d+)\s*域", note)
    if not m_note:
        problems.append("占域引文：_extension_note 未声明「本表现收 N 域」——域数无法核对")
    elif int(m_note.group(1)) != len(entries):
        problems.append(f"占域引文：_extension_note 声明 {m_note.group(1)} 域，"
                        f"实际 {len(entries)} 域")
    if lines is None:
        if not DOMAIN_CITES_SRC.is_file():
            problems.append(f"占域引文：底本不存在 → {DOMAIN_CITES_SRC.name}")
            return len(entries), 0
        lines = DOMAIN_CITES_SRC.read_text(encoding="utf-8",
                                           errors="replace").splitlines()
    heads = [(i, re.sub(r"\s+", "", ln)) for i, ln in enumerate(lines, 1)
             if _DC_HEADING.fullmatch(re.sub(r"\s+", "", ln))]
    if not heads:
        problems.append("占域引文：底本未扫到任何章标题行——0 结果 ≠ 通过")
        return len(entries), 0
    n_q = 0
    for name, item in entries:
        ch = str(item.get("章节") or "").strip()
        m_ch = _DC_CHAPTER.match(ch)
        if not m_ch:
            problems.append(f"占域引文：{name} 的章节格式无法解析 → {ch!r}")
            continue
        token, start = m_ch.group(1), int(m_ch.group(2))
        if not (1 <= start <= len(lines)):
            problems.append(f"占域引文：{name} 的章节锚 L{start} 超出底本（共 {len(lines)} 行）")
            continue
        idx = next((j for j, (i, _h) in enumerate(heads) if i == start), None)
        if idx is None or not heads[idx][1].startswith(token):
            got = heads[idx][1] if idx is not None else lines[start - 1].strip()[:30]
            problems.append(f"占域引文：{name} 的章节锚 L{start} 不在章标题行"
                            f"（该行为 {got!r}，声明 {token}）")
            continue
        end = heads[idx + 1][0] - 1 if idx + 1 < len(heads) else len(lines)
        src_lines = str(item.get("_source_lines") or "").strip()
        if not src_lines:
            problems.append(f"占域引文：{name} 缺 _source_lines")
        else:
            m_sl = re.search(r"L(\d+)", src_lines)
            if m_sl and int(m_sl.group(1)) != start:
                problems.append(f"占域引文：{name} 的 _source_lines 锚 L{m_sl.group(1)} "
                                f"与章节锚 L{start} 不一致")
        quotes = item.get("引文")
        if not isinstance(quotes, list) or not quotes:
            problems.append(f"占域引文：{name} 缺引文")
            continue
        for q in quotes:
            n_q += 1
            m_q = _DC_QUOTE.match(str(q).strip())
            if not m_q:
                problems.append(f"占域引文：{name} 的引文格式无法解析 → {str(q)[:40]!r}")
                continue
            ql, quote = int(m_q.group(1)), m_q.group(2)
            if not (1 <= ql <= len(lines)):
                problems.append(f"占域引文：{name} 的引文行 L{ql} 超出底本")
            elif not (start <= ql <= end):
                problems.append(f"占域引文：{name} 的引文行 L{ql} 越出本章 "
                                f"[L{start}–L{end}]")
            elif _fold(quote) not in _fold(lines[ql - 1]):
                problems.append(f"占域引文：{name} 的引文不在所署行 L{ql} → {quote[:30]!r}")
    return len(entries), n_q


def selftest(problems: list[str]) -> None:
    """负例：造一条 verified=true 却指向不存在文件/解不到值的条目，必须判红。"""
    fake = {"schema": "yi-rule-registry-v1", "rules": [
        {"rule_id": "test.bad_pointer", "source": {
            "verified": True,
            "quote_in_data": "data/rules/rule_registry.json#no.such.path"}},
        {"rule_id": "test.missing_file", "source": {
            "verified": True,
            "quote_in_code": "dev_tools/__does_not_exist__.py#ANY"}},
        # 【第一百六十八批】impl 两式负例：①文件不存在 ②文件在、符号不在
        {"rule_id": "test.impl_missing_file",
         "impl": "dev_tools/__does_not_exist__.py:analyze_x", "source": {"verified": True}},
        {"rule_id": "test.impl_missing_symbol",
         "impl": "scripts/chart.py:__no_such_symbol__", "source": {"verified": True}},
        # 【362 批】行号形态（quote_in_source）两式负例：①引文不在该行 ②底本不存在
        {"rule_id": "test.quote_in_source_mismatch", "source": {
            "verified": True,
            "quote": "这句话绝不在底本该行",
            "quote_in_source": "data/rules/rule_registry.json:1"}},
        {"rule_id": "test.quote_in_source_missing_file", "source": {
            "verified": True,
            "quote": "任意引文",
            "quote_in_source": "data/sources/__no_such__.dz.txt:1"}},
    ], "_uncovered": []}
    p: list[str] = []
    n: list[str] = []
    checked, passed = check(fake, p, n)
    if checked < 6 or passed != 0:
        problems.append(f"负例自证失效：应为 ≥6 检视 0 通过，实得 检视 {checked} 通过 {passed}")
    if len(p) < 6:
        problems.append(f"负例自证失效：6 条假指针只判红 {len(p)} 条 → {p}")
    if n:
        problems.append(f"负例不该产生 NOTE（verified=true 应判红）→ {n}")

    # 【第一百六十八批】正例不误伤：行号/版本号式定位记号无符号可验，必须放行
    if check_impl("scripts/chart.py:128（成破救应分支）"):
        problems.append("正例被误伤：行号式定位记号不该判")
    if check_impl("scripts/chart.py"):
        problems.append("正例被误伤：纯路径不该判")
    # 六爻专属负例（A1-1 归并保留，不在八字侧跑）：第一百六十六批域拆分后，
    # 父模块无 re-export 的悬空符号必须仍被抓住。
    _hist = "scripts/" + "classical_enhancements.py" + ":analyze_shen_yao_activation"
    if DISC.name == "liuyao" and not check_impl(_hist):
        problems.append("负例未抓到：父模块并无该符号（已搬入 shen_yao 子模块）")

    # 447 批：千金赋映射统计自洽（正例不误伤＋四类负例必须抓到）
    _states = ("已挂", "已落地", "未实现", "不适用", "无对应")
    _qlines = ["天玄地黄", "宇宙洪荒", "日月盈昃", "辰宿列张"]
    qbase = {
        "_meta": {"五态": {s: "" for s in _states}},
        "统计": {"联句总数": 3, "已挂": 1, "已落地": 1, "未实现": 0,
                 "不适用": 1, "无对应": 0},
        "联句映射": [{"句": "天玄地黄", "src": "L1", "状态": "已挂"},
                     {"句": "宇宙洪荒", "src": "L2", "状态": "已落地_日辰并爻_20261014"},
                     {"句": "日月盈昃", "src": "L3", "状态": "不适用"}],
        "registry_未被本表联句直接挂上": ["liuyao.andong"],
    }
    p_q: list[str] = []
    n_q = check_qianjin_map(qbase, p_q, {"liuyao.andong"}, _qlines)
    if p_q or n_q != (3, 3):
        problems.append(f"千金赋映射正例被误伤：{p_q}")

    def _qbad(mut) -> list[str]:
        d = json.loads(json.dumps(qbase, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_qianjin_map(d, p, {"liuyao.andong"}, _qlines)
        return p

    if not any("统计.已挂" in x for x in _qbad(lambda d: d["统计"].__setitem__("已挂", 2))):
        problems.append("负例未抓到：统计分项与实际条目数不符")
    if not any("未在 _meta 状态词汇" in x for x in
               _qbad(lambda d: d["联句映射"][0].__setitem__("状态", "新态"))):
        problems.append("负例未抓到：条目用了未登记的状态")
    if not any("不在 rule_registry" in x for x in
               _qbad(lambda d: d["registry_未被本表联句直接挂上"].__setitem__(0, "liuyao.nope"))):
        problems.append("负例未抓到：registry 列表含 rule_registry 不存在的 id")
    if not any("未在统计中列出" in x for x in _qbad(lambda d: d["统计"].pop("无对应"))):
        problems.append("负例未抓到：状态词汇漏进统计块")
    # 457 批：联句与 src 不符必须抓到；缺行号也必须抓到
    if not any("联句与底本源L1 邻域不符" in x for x in
               _qbad(lambda d: d["联句映射"][0].__setitem__("句", "绝无此语"))):
        problems.append("负例未抓到：联句与 src 行不符")
    if not any("缺行号 src" in x for x in
               _qbad(lambda d: d["联句映射"][0].pop("src", None))):
        problems.append("负例未抓到：条目缺行号 src")

    # 462 批：大运起例引文行锚（正例不误伤＋四类负例必抓）
    _dlines = ["如乙丑年，乙庚之岁戊为头，正月起戊寅",
               "如甲子年，甲己之年丙作首，正月逢丙寅"]
    dbase = {"_provenance": {"source_file": "data/sources/shen-feng-tong-kao.wikitext.txt"},
             "a": {"corpus_line": 2, "quote": "甲己之年丙作首"},
             "b": {"corpus_line": 1, "quote": "乙庚之岁戊为头"}}
    p_d: list[str] = []
    n_d = check_dayun_quotes(dbase, p_d, _dlines)
    if p_d or n_d != 2:
        problems.append(f"大运起例引文正例被误伤：{p_d}")

    def _dbad(mut) -> list[str]:
        d = json.loads(json.dumps(dbase, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_dayun_quotes(d, p, _dlines)
        return p

    if not any("不在所署行 L1" in x for x in
               _dbad(lambda d: d["a"].__setitem__("corpus_line", 1))):
        problems.append("负例未抓到：行号错（引文不在所署行）")
    if not any("超出底本" in x for x in
               _dbad(lambda d: d["a"].__setitem__("corpus_line", 99))):
        problems.append("负例未抓到：corpus_line 超出底本")
    if not any("0 条" in x for x in _dbad(lambda d: (d.pop("a"), d.pop("b")))):
        problems.append("负例未抓到：0 条目")
    p_m: list[str] = []
    check_dayun_quotes({"_provenance": {"source_file": "data/sources/__no_such__dayun.txt"},
                        "a": {"corpus_line": 1, "quote": "任意"}}, p_m)
    if not any("source_file 不存在" in x for x in p_m):
        problems.append("负例未抓到：source_file 不存在")

    # 465 批：裁决引文 locator/分支总则（夹具底本注入，不落盘）
    _vdefault = ["有病方为贵，无伤不是奇；格中如去病，财禄两相随"]
    _vlines = {
        "data/sources/__no_such__v.txt": ["", "有病方为贵，无伤不是奇"],
        "data/sources/shen-feng-tong-kao.wikitext.txt": _vdefault,
        "data/sources/di-tian-sui.wikitext.txt": _vdefault,
    }
    vbase = {
        "a": {"locator": "data/sources/__no_such__v.txt:2", "quote": "有病方为贵"},
        "病药引文": {"thesis": "有病方为贵"},
        "化格引文": {"verse": ["有病方为贵", "无伤不是奇"]},
        "从格引文": {"verse": "有病方为贵"},
    }
    p_v: list[str] = []
    n_v = check_verdicts_quotes(vbase, p_v, lambda f: _vlines.get(f))
    if p_v or n_v != (1, 4):
        problems.append(f"裁决引文正例被误伤：{p_v}（返回 {n_v}）")

    def _vbad(mut) -> list[str]:
        d = json.loads(json.dumps(vbase, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_verdicts_quotes(d, p, lambda f: _vlines.get(f))
        return p

    if not any("不在所署行" in x for x in
               _vbad(lambda d: d["a"].__setitem__("locator", "data/sources/__no_such__v.txt:1"))):
        problems.append("负例未抓到：locator 行号错（引文不在该行）")
    if not any("行号 L99 超出底本" in x for x in
               _vbad(lambda d: d["a"].__setitem__("locator", "data/sources/__no_such__v.txt:99"))):
        problems.append("负例未抓到：locator 行号越界")
    if not any("指向不存在的底本" in x for x in
               _vbad(lambda d: d["a"].__setitem__("locator",
                                                  "data/sources/__no_such__v2.txt:1"))):
        problems.append("负例未抓到：locator 底本不存在")
    if not any("病药引文.thesis" in x for x in
               _vbad(lambda d: d["病药引文"].__setitem__("thesis", "有病方为贼"))):
        problems.append("负例未抓到：分支总则引文非书源逐字")

    # 466 批：六神取象/十神作用（夹具底本注入，不落盘）
    _lline = ["", "泄身，生财，敌杀，损官"]
    limg = {"十神取象": {"伤官": {"能力": "泄身，生财",
                                  "能力_src": "data/sources/__no_such__l.txt:2"}}}
    lact = {"shi_shen_actions": {"伤官": {"actions": ["泄身", "生财"],
                                          "source": "data/sources/__no_such__l.txt:2"}}}
    p_l: list[str] = []
    n_l = check_liushen_sources(limg, lact, p_l,
                                lambda f: _lline if f.endswith("__no_such__l.txt") else None)
    if p_l or n_l != (1, 1):
        problems.append(f"六神取象/十神作用正例被误伤：{p_l}（返回 {n_l}）")

    def _lbad(mut_img=None, mut_act=None) -> list[str]:
        i = json.loads(json.dumps(limg, ensure_ascii=False))
        a = json.loads(json.dumps(lact, ensure_ascii=False))
        if mut_img:
            mut_img(i)
        if mut_act:
            mut_act(a)
        p: list[str] = []
        check_liushen_sources(i, a, p,
                              lambda f: _lline if f.endswith("__no_such__l.txt") else None)
        return p

    if not any("缺行号出处" in x for x in
               _lbad(mut_img=lambda d: d["十神取象"]["伤官"].pop("能力_src", None))):
        problems.append("负例未抓到：取象值无 _src")
    if not any("不在所署行" in x for x in
               _lbad(mut_img=lambda d: d["十神取象"]["伤官"].__setitem__("能力", "泄身，破财"))):
        problems.append("负例未抓到：取象值不在所署行")
    if not any("actions 不在所署行" in x for x in
               _lbad(mut_act=lambda d: d["shi_shen_actions"]["伤官"]["actions"].append("制杀"))):
        problems.append("负例未抓到：作用项不在所署行邻域")
    if not any("缺可解析底本/行号" in x for x in
               _lbad(mut_act=lambda d: d["shi_shen_actions"]["伤官"].__setitem__(
                   "source", "data/sources/__no_such__l.txt"))):
        problems.append("负例未抓到：作用 source 无行号")

    # 467 批：六爻引文库 quote_kind（夹具底本注入）
    _qtext = {"data/sources/__no_such__q.txt": "六合卦者，买卖交通，和合纳财，百事皆吉。"}
    qdb = {"quote_database": [
        {"pattern": "六合卦", "source": "《卜筮正宗·六合论》",
         "quote": "六合卦者，买卖交通，和合纳财，百事皆吉。",
         "quote_kind": "verbatim", "source_ref": "data/sources/__no_such__q.txt"},
        {"pattern": "六冲卦", "source": "《卜筮正宗·六冲论》",
         "quote": "六冲卦者，行人不通。", "quote_kind": "paraphrase"},
    ]}
    p_q: list[str] = []
    n_q = check_quote_database(qdb, p_q, lambda f: _qtext.get(f))
    if p_q or n_q != (1, 1):
        problems.append(f"引文库正例被误伤：{p_q}（返回 {n_q}）")

    def _qbad(mut) -> list[str]:
        d = json.loads(json.dumps(qdb, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_quote_database(d, p, lambda f: _qtext.get(f))
        return p

    if not any("quote_kind 缺失/非法" in x for x in
               _qbad(lambda d: d["quote_database"][0].pop("quote_kind", None))):
        problems.append("负例未抓到：quote_kind 缺失")
    if not any("缺 source_ref" in x for x in
               _qbad(lambda d: d["quote_database"][0].pop("source_ref", None))):
        problems.append("负例未抓到：verbatim 缺 source_ref")
    if not any("非书源逐字" in x for x in
               _qbad(lambda d: d["quote_database"][0].__setitem__(
                   "quote", "六合卦者，买卖不通，和合纳财"))):
        problems.append("负例未抓到：verbatim 引文不在底本")
    if not any("quote/source 为空" in x for x in
               _qbad(lambda d: d["quote_database"][1].__setitem__("source", ""))):
        problems.append("负例未抓到：paraphrase 缺 source")
    if not any("行号 L99 超出底本" in x for x in
               _qbad(lambda d: d["quote_database"][0].__setitem__(
                   "source_ref", "data/sources/__no_such__q.txt:99"))):
        problems.append("负例未抓到：verbatim source_ref 行号越界")

    # 469 批：六亲持世的括注口径（今译标『据…』，裸书证括注必红）
    _interp = {"shi_yao_interpretation":
               {"妻财": {"marriage": "妻财持世……（据《火珠林·婚姻章》今译）"}}}
    p_i: list[str] = []
    n_i = check_shi_yao_interp(_interp, p_i)
    if p_i or n_i != 1:
        problems.append(f"六亲持世正例被误伤：{p_i}（标记 {n_i}）")
    p_bad: list[str] = []
    check_shi_yao_interp(
        {"shi_yao_interpretation":
         {"妻财": {"marriage": "妻财持世……（《火珠林·婚姻章》）"}}}, p_bad)
    if not any("裸书证括注" in x for x in p_bad):
        problems.append("负例未抓到：六亲持世仍用裸书证括注")
    p_empty: list[str] = []
    check_shi_yao_interp({}, p_empty)
    if not any("缺失或为空" in x for x in p_empty):
        problems.append("负例未抓到：六亲持世整块缺失")

    # 470 批：文王持世行锚（夹具底本注入）
    _wtext = {"data/sources/__no_such__w.txt": ["", "世爻旺相最为强，作事享通大吉昌。"]}
    wdoc = {"pattern_hints": {"_wenwang_chishi": {"世爻": {
        "quote": "世爻旺相最为强，作事享通大吉昌。",
        "src": "data/sources/__no_such__w.txt:2"}}}}
    p_w: list[str] = []
    n_w = check_wenwang_chishi(wdoc, p_w, lambda f: _wtext.get(f))
    if p_w or n_w != 1:
        problems.append(f"文王持世正例被误伤：{p_w}（字段 {n_w}）")

    def _wbad(mut) -> list[str]:
        d = json.loads(json.dumps(wdoc, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_wenwang_chishi(d, p, lambda f: _wtext.get(f))
        return p

    if not any("缺行号出处" in x for x in
               _wbad(lambda d: d["pattern_hints"]["_wenwang_chishi"]["世爻"].pop("src", None))):
        problems.append("负例未抓到：文王持世缺 src")
    if not any("不在所署行" in x for x in
               _wbad(lambda d: d["pattern_hints"]["_wenwang_chishi"]["世爻"].__setitem__(
                   "src", "data/sources/__no_such__w.txt:1"))):
        problems.append("负例未抓到：文王持世行号错")
    if not any("行号 L99 超出底本" in x for x in
               _wbad(lambda d: d["pattern_hints"]["_wenwang_chishi"]["世爻"].__setitem__(
                   "src", "data/sources/__no_such__w.txt:99"))):
        problems.append("负例未抓到：文王持世行号越界")

    # 471 批：火珠林财官伏藏行锚（夹具底本注入）
    _flines = {"data/sources/__no_such__f.txt": [
        "", "出现旺相，为久为远；", "财伏鬼乡，买卖遭伤；",
        "财爻伏官鬼之下，乃财爻泄鬼无气"]}
    fbase = {
        "总纲": {"歌诀": "出现旺相，为久为远；",
                 "歌诀_src": "data/sources/__no_such__f.txt:2"},
        "九宫": {"妻财伏官鬼": {
            "歌诀": "财伏鬼乡，买卖遭伤；",
            "src": "data/sources/__no_such__f.txt:3",
            "注文": "财爻伏官鬼之下，乃财爻泄鬼无气",
            "注文_src": "data/sources/__no_such__f.txt:4"}},
    }
    p_f: list[str] = []
    n_f = check_fushi_quotes(fbase, p_f, lambda f: _flines.get(f))
    if p_f or n_f != 3:
        problems.append(f"财官伏藏正例被误伤：{p_f}（字段 {n_f}）")

    def _fbad(mut) -> list[str]:
        d = json.loads(json.dumps(fbase, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_fushi_quotes(d, p, lambda f: _flines.get(f))
        return p

    if not any("缺行号出处" in x for x in
               _fbad(lambda d: d["总纲"].pop("歌诀_src", None))):
        problems.append("负例未抓到：财官伏藏缺 _src")
    if not any("无配对引文" in x for x in
               _fbad(lambda d: d["总纲"].pop("歌诀", None))):
        problems.append("负例未抓到：财官伏藏 _src 无配对引文")
    if not any("不在所署行" in x for x in
               _fbad(lambda d: d["九宫"]["妻财伏官鬼"].__setitem__("歌诀", "财伏鬼乡，买卖兴隆"))):
        problems.append("负例未抓到：财官伏藏引文不在所署行")
    if not any("超出底本" in x for x in
               _fbad(lambda d: d["九宫"]["妻财伏官鬼"].__setitem__(
                   "src", "data/sources/__no_such__f.txt:99"))):
        problems.append("负例未抓到：财官伏藏行号越界")
    if not any("缺失或为空" in x for x in _fbad(lambda d: d.pop("九宫", None))):
        problems.append("负例未抓到：财官伏藏九宫整块缺失")

    # 473 批：易林补遗门类定位映射的行锚（夹具底本注入）
    _ylines = {"data/sources/__no_such__y.txt": [
        "", "初爻为基址、为井、为沟", "单占有月老，当看应爻"]}
    ybase = {
        "间爻四角色": {
            "_source": "data/sources/__no_such__y.txt:2（x）、:3（y）",
            "_口径": "如 L3「单占有月老，当看应爻」",
            "媒妁": {"_src": "L3", "_引文": "单占有月老，当看应爻"}},
        "家宅三层分宫": {
            "_source": "data/sources/__no_such__y.txt:3",
            "六爻分宫": {"_src": "L2", "_引文": "初爻为基址、为井、为沟"}},
    }
    p_y: list[str] = []
    y_q, y_a = check_yilin_buyi_maps(ybase, p_y, lambda f: _ylines.get(f))
    if p_y or (y_q, y_a) != (3, 5):
        problems.append(f"易林补遗正例被误伤：{p_y}（引文 {y_q}／锚 {y_a}）")

    def _ybad(mut) -> list[str]:
        d = json.loads(json.dumps(ybase, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_yilin_buyi_maps(d, p, lambda f: _ylines.get(f))
        return p

    if not any("未点名底本" in x for x in
               _ybad(lambda d: d["间爻四角色"].pop("_source", None))):
        problems.append("负例未抓到：易林补遗 _source 未点名底本")
    if not any("必须是裸 L####" in x for x in
               _ybad(lambda d: d["间爻四角色"]["媒妁"].__setitem__("_src", "3"))):
        problems.append("负例未抓到：易林补遗 _src 非裸 L####")
    if not any("引文不在所署行" in x for x in
               _ybad(lambda d: d["间爻四角色"]["媒妁"].__setitem__("_引文", "单占无月老"))):
        problems.append("负例未抓到：易林补遗 _引文 不在所署行")
    if not any("超出底本" in x for x in
               _ybad(lambda d: d["间爻四角色"]["媒妁"].__setitem__("_src", "L99"))):
        problems.append("负例未抓到：易林补遗 _src 行号越界")
    if not any("0 个映射组" in x for x in _ybad(lambda d: d.clear())):
        problems.append("负例未抓到：易林补遗 0 个映射组")
    if not any("内联引文不在" in x for x in
               _ybad(lambda d: d["间爻四角色"].__setitem__(
                   "_口径", "如 L3「单占无月老，当看应爻」"))):
        problems.append("负例未抓到：易林补遗组级内联引文不在所署行")

    # 474 批：注册表裸 locator 行锚（夹具底本/数据注入）
    _bl = {"《测试书》": ["", "有病方为贵", "无伤不是奇"]}
    _bd = lambda _target: {"x": {"q": "有病方为贵", "q2": "无伤不是奇"}}
    bbase = {"rules": [
        {"rule_id": "t.a", "source": {
            "book": "《测试书》", "locator": "L2",
            "quote_in_data": "data/rules/rule_registry.json#x.q"}},
        {"rule_id": "t.b", "source": {
            "book": "《测试书》", "locator": "L1",
            "quote_in_code": "scripts/chart.py#x"}},
        {"rule_id": "t.c", "source": {
            "book": "《测试书》", "locator": "独发章第三十一"}},
    ], "_uncovered": []}
    p_b: list[str] = []
    n_b_notes: list[str] = []
    n_b = check_bare_locators(bbase, p_b, n_b_notes, lambda b: _bl.get(b), _bd)
    if p_b or n_b != 2:
        problems.append(f"裸 locator 正例被误伤：{p_b}（字段 {n_b}）")
    if not any("章名/说明" in x for x in n_b_notes):
        problems.append("裸 locator 正例：描述式 locator 未进 NOTE（不许静默跳过）")

    def _bbad(mut) -> list[str]:
        d = json.loads(json.dumps(bbase, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_bare_locators(d, p, [], lambda b: _bl.get(b), _bd)
        return p

    if not any("缺 source.book" in x for x in
               _bbad(lambda d: d["rules"][0]["source"].pop("book", None))):
        problems.append("负例未抓到：裸 locator 缺书名")
    if not any("超出底本" in x for x in
               _bbad(lambda d: d["rules"][0]["source"].__setitem__("locator", "L99"))):
        problems.append("负例未抓到：裸 locator 行号越界")
    if not any("引文不在所署行" in x for x in
               _bbad(lambda d: d["rules"][0]["source"].__setitem__(
                   "quote_in_data", "data/rules/rule_registry.json#x.q2"))):
        problems.append("负例未抓到：裸 locator 引文不在所署行")
    if not any("底本不存在" in x for x in
               _bbad(lambda d: d["rules"][0]["source"].__setitem__(
                   "locator", "data/sources/__no_such__z.txt:2"))):
        problems.append("负例未抓到：colon locator 底本不存在")

    # 475 批：纳音取象 60 格（夹具底本注入）
    _nl = {"data/sources/__no_such__n.txt": [
        "", "甲子从革之金", "乙丑自库之金"]}
    ndoc = {
        "_meta": {"书源": "《测试纳音》data/sources/__no_such__n.txt L1-L2",
                  "口径": "含 L2「甲子从革之金」"},
        "纳音性质": {
            "甲子": {"ganzhi": "甲子", "性质名": "从革之金",
                     "性质行": "L2", "性质引文": "甲子从革之金"},
            "乙丑": {"ganzhi": "乙丑", "性质名": "自库之金",
                     "性质行": "L3", "性质引文": "乙丑自库之金"},
        }}
    p_n: list[str] = []
    n_n = check_nayin_quxiang(ndoc, p_n, lambda f: _nl.get(f))
    if p_n or n_n != 2:
        problems.append(f"纳音取象正例被误伤：{p_n}（格 {n_n}）")

    def _nbad(mut) -> list[str]:
        d = json.loads(json.dumps(ndoc, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_nayin_quxiang(d, p, lambda f: _nl.get(f))
        return p

    if not any("不在所署行" in x for x in
               _nbad(lambda d: d["纳音性质"]["乙丑"].__setitem__("性质行", "L2"))):
        problems.append("负例未抓到：纳音性质引文不在所署行")
    if not any("性质名 不在性质引文" in x for x in
               _nbad(lambda d: d["纳音性质"]["甲子"].__setitem__("性质名", "从革之火"))):
        problems.append("负例未抓到：纳音性质名不在引文")
    if not any("必须是裸 L####" in x for x in
               _nbad(lambda d: d["纳音性质"]["甲子"].__setitem__("性质行", "2"))):
        problems.append("负例未抓到：纳音性质行非裸 L####")
    if not any("未点名底本" in x for x in
               _nbad(lambda d: d["_meta"].pop("书源", None))):
        problems.append("负例未抓到：纳音书源未点名底本")
    if not any("缺失或为空" in x for x in
               _nbad(lambda d: d.pop("纳音性质", None))):
        problems.append("负例未抓到：纳音性质整块缺失")
    if not any("内联引文不在" in x for x in
               _nbad(lambda d: d["_meta"].__setitem__("口径", "含 L2「乙丑自库之金」"))):
        problems.append("负例未抓到：纳音 _meta 内联引文不在所署行")
    if not any("0 条内联书源引文" in x for x in
               _nbad(lambda d: d["_meta"].pop("口径", None))):
        problems.append("负例未抓到：纳音 _meta 0 条内联引文")

    # 476 批：叙述层其余 quote/src 行锚（夹具底本注入）
    # 487 批：加歌源摘要（L2-L7 六段）与口径散文（源L8「…」/裸 源L8）
    _nsl = {"data/sources/__no_such__s.txt": [
        "", "青龙空亡家虚喜", "朱雀空亡口舌临", "勾陈空亡田土荒",
        "螣蛇空亡惊怪至", "白虎空亡疾病侵", "玄武空亡盗贼来", "恍惚可再占"]}
    nsdoc = {"pattern_hints": {
        "liu_shen_kongwang": {"歌源": {
            "quote": "青龙空亡家虚喜",
            "src": "data/sources/__no_such__s.txt:L2"}},
        "liu_shen_chishi": {"歌源":
            "六段持世歌词（逐字 data/sources/__no_such__s.txt:L2-L7）："
            "青龙＝'青龙空亡家虚喜'；朱雀＝'朱雀空亡口舌临'；"
            "勾陈＝'勾陈空亡田土荒'；螣蛇＝'螣蛇空亡惊怪至'；"
            "白虎＝'白虎空亡疾病侵'；玄武＝'玄武空亡盗贼来'"},
        "yigua_yishi": {"恍惚": {
            "quote": "恍惚可再占",
            "src": "data/sources/__no_such__s.txt:L8"},
            "口径": "恍惚时可再占（源L8「恍惚可再占」）；代占另看（源L8）"},
    },
        "jiazhai_take_image": {
            "_出处": "data/sources/__no_such__s.txt L2「青龙空亡家虚喜」"}}
    p_ns: list[str] = []
    n_ns = check_narrative_anchors(nsdoc, p_ns, lambda f: _nsl.get(f))
    if p_ns or n_ns != 5:
        problems.append(f"叙述层引文正例被误伤：{p_ns}（字段 {n_ns}）")

    def _nsbad(mut) -> list[str]:
        d = json.loads(json.dumps(nsdoc, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_narrative_anchors(d, p, lambda f: _nsl.get(f))
        return p

    if not any("缺行号出处" in x for x in
               _nsbad(lambda d: d["pattern_hints"]["yigua_yishi"]["恍惚"]
                      .__setitem__("src", "L3"))):
        problems.append("负例未抓到：叙述层 src 缺行号出处")
    if not any("不在所署行" in x for x in
               _nsbad(lambda d: d["pattern_hints"]["yigua_yishi"]["恍惚"]
                      .__setitem__("quote", "恍惚不可再占"))):
        problems.append("负例未抓到：叙述层 quote 不在所署行")
    if not any("超出底本" in x for x in
               _nsbad(lambda d: d["pattern_hints"]["yigua_yishi"]["恍惚"]
                      .__setitem__("src", "data/sources/__no_such__s.txt:L99"))):
        problems.append("负例未抓到：叙述层 src 行号越界")
    if not any("0 条 quote/src" in x for x in
               _nsbad(lambda d: (d["pattern_hints"].clear(),
                                 d.pop("jiazhai_take_image", None)))):
        problems.append("负例未抓到：叙述层 0 条 quote/src")
    if not any("不在所署行" in x for x in
               _nsbad(lambda d: d["jiazhai_take_image"].__setitem__(
                   "_出处", "data/sources/__no_such__s.txt L3「青龙空亡家虚喜」"))):
        problems.append("负例未抓到：家宅取象 _出处 内联引文不在所署行")
    # 487 批：歌源摘要/口径散文的负例
    if not any("「青龙」的引文不在所署行 L2" in x for x in
               _nsbad(lambda d: d["pattern_hints"]["liu_shen_chishi"].__setitem__(
                   "歌源", d["pattern_hints"]["liu_shen_chishi"]["歌源"].replace(
                       "青龙空亡家虚喜", "青龙空亡家虚忧")))):
        problems.append("负例未抓到：歌源片段不在所署行")
    if not any("歌源 的范围 L2-L9" in x for x in
               _nsbad(lambda d: d["pattern_hints"]["liu_shen_chishi"].__setitem__(
                   "歌源", d["pattern_hints"]["liu_shen_chishi"]["歌源"].replace(
                       "L2-L7", "L2-L9")))):
        problems.append("负例未抓到：歌源范围越界")
    if not any("口径 的内联引文不在 L3" in x for x in
               _nsbad(lambda d: d["pattern_hints"]["yigua_yishi"].__setitem__(
                   "口径", "恍惚时可再占（源L3「恍惚可再占」）"))):
        problems.append("负例未抓到：口径内联引文不在所署行")
    if not any("0 条 quote/src" in x for x in
               _nsbad(lambda d: (d["pattern_hints"].pop("liu_shen_chishi", None),
                                 d["pattern_hints"].pop("yigua_yishi", None),
                                 d["pattern_hints"].pop("liu_shen_kongwang", None),
                                 d.pop("jiazhai_take_image", None)))):
        problems.append("负例未抓到：叙述层整块缺失仍须 0 条判红")

    # 488 批：问题题类注记的书源引用（夹具注入）
    _ccl = {"测试书": ["", "旺兄持世，克妻耶？耗财耶？",
                       "凡占终身财福，定是家殷户足",
                       "占雨用父爻，占晴用子孙爻、财爻"]}
    ccdoc = {"classes": [
        {"source_gates": "《测试书》源L2 野鹤驳『旺兄』，"
                         "源L3「凡占终身财福，定是家殷户足」"},
        {"note": "《测试书》源L4 逐字「占雨用父爻，占晴用子孙爻、财爻」"}]}
    p_cc: list[str] = []
    n_cc = check_question_classes_notes(ccdoc, p_cc, lambda b: _ccl.get(b))
    if p_cc or n_cc != (3, 2):
        problems.append(f"问题题类正例被误伤：{p_cc}（锚/引文 {n_cc}）")

    def _ccbad(mut) -> list[str]:
        d = json.loads(json.dumps(ccdoc, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_question_classes_notes(d, p, lambda b: _ccl.get(b))
        return p

    if not any("引文不在" in x for x in
               _ccbad(lambda d: d["classes"][0].__setitem__(
                   "source_gates", "《测试书》源L3「凡占终身财福，定是家殷户绝」"))):
        problems.append("负例未抓到：问题题类引文不在所署行")
    if not any("超出底本" in x for x in
               _ccbad(lambda d: d["classes"][1].__setitem__(
                   "note", "《测试书》源L99 逐字「占雨用父爻」"))):
        problems.append("负例未抓到：问题题类行号越界")
    if not any("缺《书名》" in x for x in
               _ccbad(lambda d: d["classes"][1].__setitem__(
                   "note", "源L4 逐字「占雨用父爻，占晴用子孙爻、财爻」"))):
        problems.append("负例未抓到：问题题类缺书名")
    if not any("0 个 classes" in x for x in _ccbad(lambda d: d["classes"].clear())):
        problems.append("负例未抓到：问题题类 0 个 classes")

    # 489 批：裁决表散文裸行号（夹具注入）
    _ppl = {"data/sources/__no_such__p.txt": ["", "甲判", "乙判", "丙判"]}
    ppdoc = {
        "a": {"_text": "data/sources/__no_such__p.txt 篇（甲L2／乙L3）"},
        "b": {"note": "《测试书》源L3"},
        "c": {"locator": "data/sources/__no_such__p.txt:2", "note": "源L2"},
    }
    p_pp: list[str] = []
    n_pp = check_verdicts_prose_anchors(
        ppdoc, p_pp, lines_of=lambda f: _ppl.get(f),
        books_of=lambda b: ["data/sources/__no_such__p.txt"] if b == "测试书" else [])
    if p_pp or n_pp != 4:
        problems.append(f"裁决散文行号正例被误伤：{p_pp}（锚 {n_pp}）")

    def _ppbad(mut) -> list[str]:
        d = json.loads(json.dumps(ppdoc, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_verdicts_prose_anchors(
            d, p, lines_of=lambda f: _ppl.get(f),
            books_of=lambda b: ["data/sources/__no_such__p.txt"] if b == "测试书" else [])
        return p

    if not any("超出底本" in x for x in
               _ppbad(lambda d: d["a"].__setitem__(
                   "_text", "data/sources/__no_such__p.txt 篇（甲L99）"))):
        problems.append("负例未抓到：裁决散文行号越界")
    if not any("无可解析底本" in x for x in
               _ppbad(lambda d: d["b"].__setitem__("note", "《无此书》源L3"))):
        problems.append("负例未抓到：裁决散文书名无底本")
    if not any("底本不存在" in x for x in
               _ppbad(lambda d: d["a"].__setitem__(
                   "_text", "data/sources/__no_such__q.txt 篇（甲L2）"))):
        problems.append("负例未抓到：裁决散文路径不存在")
    if not any("0 条可解析锚" in x for x in _ppbad(lambda d: d.clear())):
        problems.append("负例未抓到：裁决散文 0 条锚")

    # 494 批：同书异名归一（命理探原→命理探源）
    if _book_key("《命理探原》") != _book_key("《命理探源》"):
        problems.append("负例自证失效：书目异名未归一到同一键")

    # 490 批：代码注释里的《书名》源L「…」（夹具注入）
    _cfl = {"data/sources/__no_such__c3.txt": ["", "甲判", "乙判"]}
    cfiles = [("sample.py", "# 《测试书》源L2「甲判」\n# 《测试书》源L3 无引文\n")]
    p_cf: list[str] = []
    n_cf, q_cf, nb_cf = check_bazi_code_anchors(
        p_cf, cfiles, lines_of=lambda f: _cfl.get(f),
        books_of=lambda b: ["data/sources/__no_such__c3.txt"] if b == "测试书" else [])
    if p_cf or (n_cf, q_cf, nb_cf) != (2, 1, 0):
        problems.append(f"代码源L正例被误伤：{p_cf}（锚/引文/无书名 {n_cf}/{q_cf}/{nb_cf}）")

    def _cfbad(text) -> list[str]:
        p: list[str] = []
        check_bazi_code_anchors(
            p, [("sample.py", text)], lines_of=lambda f: _cfl.get(f),
            books_of=lambda b: ["data/sources/__no_such__c3.txt"] if b == "测试书" else [])
        return p

    if not any("引文不在该行" in x for x in
               _cfbad("# 《测试书》源L2「乙判」")):
        problems.append("负例未抓到：代码源L引文不在该行")
    if not any("超出底本" in x for x in
               _cfbad("# 《测试书》源L99 无引文")):
        problems.append("负例未抓到：代码源L行号越界")
    p_un: list[str] = []
    _, _, nb_un = check_bazi_code_anchors(
        p_un, [("sample.py", "# 《无此书》源L2「甲判」")],
        lines_of=lambda f: _cfl.get(f), books_of=lambda b: [])
    if p_un or nb_un != 1:
        problems.append(f"代码源L篇名式书名处理失效：{p_un}（无书名 {nb_un}）")
    if not any("0 个源L" in x for x in _cfbad("# 无书证")):
        problems.append("负例未抓到：代码源L 0 个锚")

    # 495 批：dev_tools/eval 扩面后的三个新口径（夹具注入）
    #   ① selftest 函数体内的假书证是负例夹具，必须跳过；
    #   ② 跨行引文（开引号在本行、闭引号在下一行）须按整句在该行命中；
    #   ③ f-string 模板（含 {…}）不是逐字引文，按无引文处理。
    p_skip: list[str] = []
    n_skip, q_skip, _ = check_bazi_code_anchors(
        p_skip,
        [("gate.py", "X = 1  # 《测试书》源L2「甲判」\n"
                     "def selftest():\n"
                     "    Y = '# 《测试书》源L99「乙判」'\n")],
        lines_of=lambda f: _cfl.get(f),
        books_of=lambda b: ["data/sources/__no_such__c3.txt"] if b == "测试书" else [])
    if p_skip or (n_skip, q_skip) != (1, 1):
        problems.append(f"代码源L：selftest 夹具未被跳过：{p_skip}"
                        f"（锚/引文 {n_skip}/{q_skip}）")
    p_ml: list[str] = []
    check_bazi_code_anchors(
        p_ml, [("gate.py", "# 《测试书》源L3「乙\n判」")],
        lines_of=lambda f: _cfl.get(f),
        books_of=lambda b: ["data/sources/__no_such__c3.txt"] if b == "测试书" else [])
    if p_ml:
        problems.append(f"代码源L：跨行引文被误判：{p_ml}")
    p_tpl: list[str] = []
    n_tpl, q_tpl, _ = check_bazi_code_anchors(
        p_tpl, [("gate.py", '# 《测试书》源L2「{stem}…甲判」')],
        lines_of=lambda f: _cfl.get(f),
        books_of=lambda b: ["data/sources/__no_such__c3.txt"] if b == "测试书" else [])
    if p_tpl or (n_tpl, q_tpl) != (1, 0):
        problems.append(f"代码源L：模板引文未按无引文处理：{p_tpl}"
                        f"（锚/引文 {n_tpl}/{q_tpl}）")

    # 477 批：verdict_texts 的文件+L 行锚（夹具底本注入）
    _vtl = {"data/sources/__no_such__v.txt": [
        "", "有病方为贵", "亦是休囚無气始見危"]}
    vtdoc = {
        "direction_cap_quotes": {"x": {
            "locator": "__no_such__v.txt L2", "quote": "有病方为贵"}},
        "step5_classical_notes": {"y": {
            "basis": "（__no_such__v.txt L3）",
            "text": "「亦是休囚無气始見危」重档减免"}},
    }
    p_vt: list[str] = []
    n_vt = check_verdict_text_anchors(vtdoc, p_vt, lambda f: _vtl.get(f))
    if p_vt or n_vt != 2:
        problems.append(f"裁决引文行锚正例被误伤：{p_vt}（字段 {n_vt}）")

    def _vtbad(mut) -> list[str]:
        d = json.loads(json.dumps(vtdoc, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_verdict_text_anchors(d, p, lambda f: _vtl.get(f))
        return p

    if not any("不在所署行" in x for x in
               _vtbad(lambda d: d["direction_cap_quotes"]["x"].__setitem__(
                   "locator", "__no_such__v.txt L1"))):
        problems.append("负例未抓到：direction_cap_quotes 行号错")
    if not any("不在所署行" in x for x in
               _vtbad(lambda d: d["step5_classical_notes"]["y"].__setitem__(
                   "basis", "（__no_such__v.txt L2）"))):
        problems.append("负例未抓到：step5_classical_notes 行号错")
    if not any("底本不存在" in x for x in
               _vtbad(lambda d: d["direction_cap_quotes"]["x"].__setitem__(
                   "locator", "__no_such__v2.txt L2"))):
        problems.append("负例未抓到：verdict_texts 底本不存在")
    if not any("text 无「」引文" in x for x in
               _vtbad(lambda d: d["step5_classical_notes"]["y"].__setitem__(
                   "text", "无引文的重档减免说明"))):
        problems.append("负例未抓到：verdict_texts 行锚但无引文")

    # 479 批：注册表散文内联「《书名》源L####「…」」（夹具注入）
    _rl = {"data/sources/__no_such__r.txt": ["", "甲戊庚牛羊，乙庚鼠猴乡"]}
    _rbooks = lambda b: ["data/sources/__no_such__r.txt"] if b == "测试书" else []
    rdoc = {"rules": [{"rule_id": "t.inline", "source": {
        "book": "《测试书》",
        "locator": "《测试书》源L2「甲戊庚牛羊，乙庚鼠猴乡」"}}, ],
        "_uncovered": []}
    p_r: list[str] = []
    n_r_notes: list[str] = []
    n_r = check_registry_inline_quotes(rdoc, p_r, n_r_notes,
                                       lambda k: _rl.get(k), _rbooks)
    if p_r or n_r != 1:
        problems.append(f"注册表内联书证正例被误伤：{p_r}（条 {n_r}）")

    def _rbad(mut) -> list[str]:
        d = json.loads(json.dumps(rdoc, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_registry_inline_quotes(d, p, [], lambda k: _rl.get(k), _rbooks)
        return p

    if not any("不在所署源L2" in x for x in
               _rbad(lambda d: d["rules"][0]["source"].__setitem__(
                   "locator", "《测试书》源L2「甲戊庚牛羊，乙己鼠猴乡」"))):
        problems.append("负例未抓到：注册表内联引文不符")
    if not any("超出底本" in x for x in
               _rbad(lambda d: d["rules"][0]["source"].__setitem__(
                   "locator", "《测试书》源L99「甲戊庚牛羊，乙庚鼠猴乡」"))):
        problems.append("负例未抓到：注册表内联行号越界")
    if not any("前无《书名》" in x for x in
               _rbad(lambda d: (d["rules"][0]["source"].pop("book", None),
                                d["rules"][0]["source"].__setitem__(
                                    "locator", "源L2「甲戊庚牛羊，乙庚鼠猴乡」")))):
        problems.append("负例未抓到：注册表内联无书名")
    if not any("书名全部不可解析" in x for x in
               _rbad(lambda d: (d["rules"][0]["source"].pop("book", None),
                                d["rules"][0]["source"].__setitem__(
                                    "locator",
                                    "《无此书》源L2「甲戊庚牛羊，乙庚鼠猴乡」")))):
        problems.append("负例未抓到：注册表内联书名不可解析")
    if not any("0 条" in x for x in _rbad(lambda d: d["rules"].clear())):
        problems.append("负例未抓到：注册表内联 0 条")

    # 480 批：八字 verdicts 散文内联书证（夹具注入）
    _vd = {"data/sources/__no_such__vd.txt": [
        "", "从儿不管身强弱，只要吾儿又得儿", "若逢根气命损无猜"]}
    _vbooks = lambda b: ["data/sources/__no_such__vd.txt"] if b == "三命通会" else []
    vddoc = {"从格引文": {
        "_meta": "原文见 data/sources/__no_such__vd.txt 源L2"
                 "（该本作「从儿不管身强弱，只要吾儿又得儿」）",
        "cong_cai_sanming": {
            "note": "源L3。条件：日干无气；「若逢根气命损无猜」为反面限定"}}}
    p_vd: list[str] = []
    n_vd = check_verdict_inline_quotes(vddoc, p_vd, [],
                                       lambda k: _vd.get(k), _vbooks)
    if p_vd or n_vd != 2:
        problems.append(f"裁决内联书证正例被误伤：{p_vd}（条 {n_vd}）")

    def _vdbad(mut) -> list[str]:
        d = json.loads(json.dumps(vddoc, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_verdict_inline_quotes(d, p, [], lambda k: _vd.get(k), _vbooks)
        return p

    if not any("不在所署源L2" in x for x in
               _vdbad(lambda d: d["从格引文"].__setitem__(
                   "_meta", "原文见 data/sources/__no_such__vd.txt 源L2"
                            "（该本作「从儿不管身强弱，只要吾儿又得妻」）"))):
        problems.append("负例未抓到：裁决内联引文不符")
    if not any("超出底本" in x for x in
               _vdbad(lambda d: d["从格引文"].__setitem__(
                   "_meta", "原文见 data/sources/__no_such__vd.txt 源L99"
                            "（该本作「从儿不管身强弱，只要吾儿又得儿」）"))):
        problems.append("负例未抓到：裁决内联行号越界")
    if not any("无底本归属" in x for x in
               _vdbad(lambda d: d["从格引文"].__setitem__(
                   "other", "源L2「从儿不管身强弱，只要吾儿又得儿」"))):
        problems.append("负例未抓到：裁决内联无底本归属")
    if not any("0 条" in x for x in _vdbad(lambda d: d.clear())):
        problems.append("负例未抓到：裁决内联 0 条")

    # 482 批：core/scripts 注释里的 <file>.txt:<行>「…」（夹具注入）
    _cl = {"data/sources/__no_such__c.txt": ["", "贵在折衷，归於中道"]}
    cfiles = [("sample.py", "# __no_such__c.txt:2「贵在折衷，归於中道」")]
    p_c: list[str] = []
    n_c = check_code_anchors(p_c, cfiles, lambda k: _cl.get(k))
    if p_c or n_c != 1:
        problems.append(f"代码书证正例被误伤：{p_c}（条 {n_c}）")

    def _cbad(text, lines=None) -> list[str]:
        p: list[str] = []
        check_code_anchors(p, [("sample.py", text)],
                           lambda k: (lines or _cl).get(k))
        return p

    if not any("不在 __no_such__c.txt:2" in x for x in
               _cbad("# __no_such__c.txt:2「贵在折衷，归於中道也」")):
        problems.append("负例未抓到：代码书证引文不符")
    if not any("超出底本" in x for x in
               _cbad("# __no_such__c.txt:99「贵在折衷，归於中道」")):
        problems.append("负例未抓到：代码书证行号越界")
    if not any("底本不存在" in x for x in
               _cbad("# __no_such__c2.txt:2「贵在折衷，归於中道」")):
        problems.append("负例未抓到：代码书证底本不存在")
    if not any("0 条" in x for x in _cbad("# 无书证")):
        problems.append("负例未抓到：代码书证 0 条")

    # 483 批：用神词典 note 的 file+L『…』（夹具注入）
    _ug = {"data/sources/__no_such__ug.txt": [
        "", "辰月戊子日占小舟過關恐盤阻", "世爻之鬼，乃滿腹憂疑之象"]}
    ugdoc = {"families": [
        {"label": "ok", "note": "实案『辰月戊子日占小舟過關恐盤阻』"
                                "（__no_such__ug.txt L2）"},
        {"label": "ok2", "note": "断辞（__no_such__ug.txt L3）"
                                 "『世爻之鬼，乃滿腹憂疑之象』"}]}
    p_ug: list[str] = []
    n_ug = check_usegod_notes(ugdoc, p_ug, lambda f: _ug.get(f))
    if p_ug or n_ug != 2:
        problems.append(f"用神词典注记正例被误伤：{p_ug}（条 {n_ug}）")

    def _ugbad(mut) -> list[str]:
        d = json.loads(json.dumps(ugdoc, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_usegod_notes(d, p, lambda f: _ug.get(f))
        return p

    if not any("不在 __no_such__ug.txt:L2" in x for x in
               _ugbad(lambda d: d["families"][1].__setitem__(
                   "note", "断辞（__no_such__ug.txt L2）『世爻之鬼，乃滿腹憂疑之象』"))):
        problems.append("负例未抓到：用神词典注记引文不在所署行")
    if not any("超出底本" in x for x in
               _ugbad(lambda d: d["families"][1].__setitem__(
                   "note", "断辞（__no_such__ug.txt L99）『世爻之鬼，乃滿腹憂疑之象』"))):
        problems.append("负例未抓到：用神词典注记行号越界")
    if not any("缺失或为空" in x for x in
               _ugbad(lambda d: d["families"].clear())):
        problems.append("负例未抓到：用神词典注记 families 为空")

    # 491 批：用神词典族注「…」引文（夹具注入）
    _fnl = ["", "占雨用父爻，占晴用子孫爻", "索財不予"]
    fndoc = {"families": [
        {"note": "占雨章「占雨用父爻」逐字"},
        {"note": "讨债章「索財不予」逐字"}]}
    p_fn: list[str] = []
    n_fn = check_usegod_family_notes(fndoc, p_fn, _fnl)
    if p_fn or n_fn != 2:
        problems.append(f"用神词典族注正例被误伤：{p_fn}（段 {n_fn}）")
    p_fnb: list[str] = []
    check_usegod_family_notes(
        {"families": [{"note": "占雨章「占雨用母爻」逐字"}]}, p_fnb, _fnl)
    if not any("不在《增刪卜易》底本" in x for x in p_fnb):
        problems.append("负例未抓到：用神词典族注引文不在底本")
    p_fn0: list[str] = []
    check_usegod_family_notes({"families": []}, p_fn0, _fnl)
    if not any("0 个 families" in x for x in p_fn0):
        problems.append("负例未抓到：用神词典族注 0 个 families")
    p_fnq: list[str] = []
    check_usegod_family_notes({"families": [{"note": "无引文"}]}, p_fnq, _fnl)
    if not any("0 段「…」引文" in x for x in p_fnq):
        problems.append("负例未抓到：用神词典族注 0 段引文")

    # 493 批：用神词典 _meta 声明数（夹具注入）
    mdoc = {"_meta": {"description": "3 条现代问法→六亲", "family_count": 2,
                      "key_count": 3},
            "families": [{"entries": [{"k": "a"}]},
                         {"entries": [{"k": "b"}, {"k": "c"}]}]}
    p_md: list[str] = []
    n_md = check_usegod_meta(mdoc, p_md)
    if p_md or n_md != (2, 3):
        problems.append(f"用神词典元数据正例被误伤：{p_md}（族/键 {n_md}）")

    def _mdbad(mut) -> list[str]:
        d = json.loads(json.dumps(mdoc, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_usegod_meta(d, p)
        return p

    if not any("description 声明 195" in x for x in
               _mdbad(lambda d: d["_meta"].__setitem__(
                   "description", "195 条现代问法→六亲"))):
        problems.append("负例未抓到：用神词典 description 条数不符")
    if not any("family_count 3" in x for x in
               _mdbad(lambda d: d["_meta"].__setitem__("family_count", 3))):
        problems.append("负例未抓到：用神词典 family_count 不符")
    if not any("key_count 4" in x for x in
               _mdbad(lambda d: d["_meta"].__setitem__("key_count", 4))):
        problems.append("负例未抓到：用神词典 key_count 不符")
    if not any("未声明「N 条现代问法」" in x for x in
               _mdbad(lambda d: d["_meta"].__setitem__("description", "无条数"))):
        problems.append("负例未抓到：用神词典 description 缺条数")

    # 492 批：注册表「语料行 NNNN」（夹具注入）
    _ll = {"data/sources/__no_such__l.txt": ["", "甲", "乙", "丙"]}
    ldoc = {"rules": [
        {"rule_id": "t.line", "source": {
            "corpus_files": ["data/sources/__no_such__l.txt"],
            "locator": "语料行 2/3 在库"}},
        {"rule_id": "t.line2", "source": {
            "locator": "data/sources/__no_such__l.txt（语料行 4）"}}]}
    p_ll: list[str] = []
    n_ll = check_registry_line_claims(ldoc, p_ll, lines_of=lambda k: _ll.get(k))
    if p_ll or n_ll != 3:
        problems.append(f"注册表语料行正例被误伤：{p_ll}（行号 {n_ll}）")

    def _llbad(mut) -> list[str]:
        d = json.loads(json.dumps(ldoc, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_registry_line_claims(d, p, lines_of=lambda k: _ll.get(k))
        return p

    if not any("超出底本" in x for x in
               _llbad(lambda d: d["rules"][0]["source"].__setitem__(
                   "locator", "语料行 99 在库"))):
        problems.append("负例未抓到：注册表语料行越界")
    if not any("无可解析底本" in x for x in
               _llbad(lambda d: (d["rules"][0]["source"].pop("corpus_files", None),
                                 d["rules"][1]["source"].__setitem__(
                                     "locator", "语料行 4")))):
        problems.append("负例未抓到：注册表语料行无可解析底本")
    if not any("0 个行号声明" in x for x in _llbad(lambda d: d["rules"].clear())):
        problems.append("负例未抓到：注册表语料行 0 个声明")

    # 484 批：注册表 source.book 书名可解析（夹具注入）
    _bks = lambda b: ["x"] if b == "测试书" else []
    bkdoc = {"rules": [{"rule_id": "t.book", "source": {"book": "《测试书》"}}]}
    p_bk: list[str] = []
    n_bk = check_registry_books(bkdoc, p_bk, _bks)
    if p_bk or n_bk != 1:
        problems.append(f"注册表书目正例被误伤：{p_bk}（书名 {n_bk}）")
    p_bkb: list[str] = []
    check_registry_books({"rules": [{"rule_id": "t.book",
                                     "source": {"book": "《无此书》"}}]}, p_bkb, _bks)
    if not any("无在盘底本" in x for x in p_bkb):
        problems.append("负例未抓到：注册表书目无底本")
    p_bk0: list[str] = []
    check_registry_books({"rules": []}, p_bk0, _bks)
    if not any("0 个书名" in x for x in p_bk0):
        problems.append("负例未抓到：注册表书目 0 个")

    # 485 批：分占域判据引文库章界（夹具注入）
    _dc = ["易冒卷之一", "甲子章第一", "    以世应分内外，动静别吉凶。",
           "", "附录章第二", "    另章判语在此。"]
    dcbase = {"domains": {
        "_extension_note": "本表现收 2 域逐字引文（一行一锚一逐字）",
        "甲子": {"_source_lines": "《易冒》甲子章第一（底本 L2 起）",
                 "章节": "《易冒》甲子章第一（底本 L2 起）",
                 "引文": ["《易冒》源L3 逐字「以世应分内外」"]},
        "附录": {"_source_lines": "《易冒》附录章第二（底本 L5 起）",
                 "章节": "《易冒》附录章第二（底本 L5 起）",
                 "引文": ["《易冒》源L6 逐字「另章判语在此」"]}}}
    p_dc: list[str] = []
    n_dc = check_domain_citations(dcbase, p_dc, _dc)
    if p_dc or n_dc != (2, 2):
        problems.append(f"占域引文正例被误伤：{p_dc}（域/引文 {n_dc}）")

    def _dcbad(mut) -> list[str]:
        d = json.loads(json.dumps(dcbase, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_domain_citations(d, p, _dc)
        return p

    if not any("不在所署行 L3" in x for x in
               _dcbad(lambda d: d["domains"]["甲子"]["引文"].__setitem__(
                   0, "《易冒》源L3 逐字「以世应分外内」"))):
        problems.append("负例未抓到：占域引文不在所署行")
    if not any("不在章标题行" in x for x in
               _dcbad(lambda d: d["domains"]["甲子"].__setitem__(
                   "章节", "《易冒》甲子章第一（底本 L1 起）"))):
        problems.append("负例未抓到：占域章节锚不在标题行")
    if not any("越出本章" in x for x in
               _dcbad(lambda d: d["domains"]["甲子"]["引文"].__setitem__(
                   0, "《易冒》源L6 逐字「另章判语在此」"))):
        problems.append("负例未抓到：占域引文越章")
    if not any("不一致" in x for x in
               _dcbad(lambda d: d["domains"]["甲子"].__setitem__(
                   "_source_lines", "《易冒》甲子章第一（底本 L3 起）"))):
        problems.append("负例未抓到：占域 _source_lines 与章节锚不一致")
    if not any("实际 2 域" in x for x in
               _dcbad(lambda d: d["domains"].__setitem__(
                   "_extension_note", "本表现收 3 域"))):
        problems.append("负例未抓到：占域声明域数与实际不符")
    if not any("0 个域条目" in x for x in _dcbad(lambda d: d["domains"].clear())):
        problems.append("负例未抓到：占域 0 个域条目")


def main() -> int:
    if not REG.exists():
        print(f"× 注册表不存在：{REG}")
        return 1
    doc = json.loads(REG.read_text(encoding="utf-8"))
    problems: list[str] = []
    notes: list[str] = []
    checked, passed = check(doc, problems, notes)
    print(f"{DISC.name}：检视 {checked} 条书源指针，{passed} 条可回指")
    registry_ids = {str(item.get("rule_id") or item.get("id"))
                    for _bucket, item in _iter_entries(doc)}
    registry_ids.discard("None")
    # 447 批：千金赋联句映射（仅六爻有该册；八字无文件则跳过，不判红）
    if QIANJIN.is_file():
        qdoc = json.loads(QIANJIN.read_text(encoding="utf-8"))
        q_total, q_states = check_qianjin_map(qdoc, problems, registry_ids)
        print(f"  千金赋映射：{q_total} 联、{q_states} 个状态；"
              f"统计块/五态词表/registry 列表/逐联书源回指已逐项核对")
    elif DISC.name == "liuyao":
        problems.append(f"千金赋映射：{QIANJIN.name} 不存在——0 结果 ≠ 通过，先确认路径")
    # 462 批：大运起例引文行锚（仅八字有该册；六爻无文件则跳过，不判红）
    if DAYUN.is_file():
        ddoc = json.loads(DAYUN.read_text(encoding="utf-8"))
        d_total = check_dayun_quotes(ddoc, problems)
        print(f"  大运起例引文：{d_total} 条 corpus_line+quote；source_file/行号/行内逐字已核对")
    # 465 批：裁决引文 locator/分支总则（仅八字册；六爻另有同名 data/verdicts.json，结构不同，跳过）
    if DISC.name == "bazi" and VERDICTS.is_file():
        vdoc = json.loads(VERDICTS.read_text(encoding="utf-8"))
        v_loc, v_grp = check_verdicts_quotes(vdoc, problems)
        if v_loc < 20 or v_grp < 4:
            problems.append(f"裁决引文：locator 字段 {v_loc}（下限 20）／分支总则 {v_grp}"
                            f"（下限 4）——先确认字段/路径")
        if v_loc == 0 or v_grp == 0:
            problems.append("裁决引文：有一面扫到 0 条——0 结果 ≠ 通过")
        print(f"  裁决引文：{v_loc} 个 locator 字段、{v_grp} 条分支总则引文；"
              f"行锚/文件内逐字已核对")
        # 480 批：verdicts 散文内联「源L####「…」」
        n_vi = check_verdict_inline_quotes(vdoc, problems, notes)
        if n_vi < 3:
            problems.append(f"裁决内联书证：只有 {n_vi} 条（下限 3）")
        print(f"  裁决内联书证：{n_vi} 条；路径/书名归属与行内逐字已核对")
        # 489 批：verdicts 散文裸行号（无引文的定位声明）
        n_pp = check_verdicts_prose_anchors(vdoc, problems)
        if n_pp < 10:
            problems.append(f"裁决散文行号：只有 {n_pp} 条可解析锚（下限 10）")
        print(f"  裁决散文行号：{n_pp} 条；路径/书名/同条 locator→底本行号已核对")
    # 482 批：core/scripts 注释里的 <file>.txt:<行>「…」（仅八字册；
    # 六爻 shensha 副本引八字专有底本，按独立科口径不跨科读取，见 docstring）
    if DISC.name == "bazi":
        n_code = check_code_anchors(problems)
        if n_code < 5:
            problems.append(f"代码书证：只有 {n_code} 条（下限 5）")
        print(f"  代码书证：{n_code} 条；底本/行号/行内逐字已核对")
        # 490 批：代码注释里的《书名》源L「…」；495 批扩到 dev_tools／eval
        # （下限随扩面实测抬到 115／55——扫不到就说明目录/路径漂了，0 结果 ≠ 通过）
        n_cr, n_cq, n_cnb = check_bazi_code_anchors(problems)
        if n_cr < 115 or n_cq < 55:
            problems.append(f"代码源L：锚 {n_cr}（下限 115）／带引文 {n_cq}"
                            f"（下限 55）——先确认目录/字段/路径")
        print(f"  代码源L：{n_cr} 个锚（{n_cq} 条带引文、{n_cnb} 条无书名）；"
              f"书名→底本/行号/行内逐字已核对")
        # 484 批：source.book 书名可解析
        n_bk = check_registry_books(doc, problems)
        if n_bk < 18:
            problems.append(f"注册表书目：只有 {n_bk} 个书名（下限 18）")
        print(f"  注册表书目：{n_bk} 个书名；provenance 解析已核对")
        # 492 批：「语料行 NNNN」声明（不写 L 的行号）
        n_lc = check_registry_line_claims(doc, problems)
        if n_lc < 2:
            problems.append(f"注册表语料行：只有 {n_lc} 个行号声明（下限 2）")
        print(f"  注册表语料行：{n_lc} 个行号声明；底本→行号在册已核对")
    # 466 批：六神取象 / 十神作用（仅八字册）
    if DISC.name == "bazi":
        if not LIUSHEN.is_file() or not SHISHEN.is_file():
            problems.append("六神取象/十神作用：数据文件缺失——0 结果 ≠ 通过")
        else:
            limg = json.loads(LIUSHEN.read_text(encoding="utf-8"))
            lact = json.loads(SHISHEN.read_text(encoding="utf-8"))
            l_fields, l_acts = check_liushen_sources(limg, lact, problems)
            if l_fields < 16 or l_acts < 7:
                problems.append(f"六神取象/十神作用：取象字段 {l_fields}（下限 16）／"
                                f"作用条目 {l_acts}（下限 7）——先确认字段/路径")
            print(f"  六神取象/十神作用：{l_fields} 个引文字段、{l_acts} 条作用枚举；"
                  f"行号出处/邻域已核对")
        # 475 批：纳音取象 60 格的底本行锚（仅八字册）
        if not NAYIN.is_file():
            problems.append("纳音取象：nayin_quxiang.json 不存在——0 结果 ≠ 通过")
        else:
            ndoc = json.loads(NAYIN.read_text(encoding="utf-8"))
            n_n = check_nayin_quxiang(ndoc, problems)
            if n_n < 60:
                problems.append(f"纳音取象：只有 {n_n} 格（下限 60）——先确认字段/路径")
            print(f"  纳音取象：{n_n} 格；性质行/性质引文/性质名/_meta 内联已逐条核对")
        # 479 批：注册表散文内联「《书名》源L####「…」」
        n_in = check_registry_inline_quotes(doc, problems, notes)
        if n_in < 25:
            problems.append(f"注册表内联书证：只有 {n_in} 条（下限 25）——先确认字段/路径")
        print(f"  注册表内联书证：{n_in} 条；书名候选/行号/行内逐字已核对")
    # 467 批：六爻引文库 quote_kind（仅六爻册；八字同名文件结构不同）
    if DISC.name == "liuyao" and LIUYAO_QUOTES.is_file():
        qdoc = json.loads(LIUYAO_QUOTES.read_text(encoding="utf-8"))
        qv, qp = check_quote_database(qdoc, problems)
        if qv < 1 or qp < 48 or qv + qp < 49:
            problems.append(f"引文库：verbatim {qv}／paraphrase {qp}／合计 {qv + qp}"
                            f"（下限 1/48/49）——先确认字段/路径")
        print(f"  引文库：{qv + qp} 条（verbatim {qv}／paraphrase {qp}）；"
              f"quote_kind 与逐字回验已核对")
        n_claim = check_shi_yao_interp(qdoc, problems)
        if n_claim < 19:
            problems.append(f"六亲持世：『据《…》今译』标记只有 {n_claim}（下限 19）")
        print(f"  六亲持世：{n_claim} 条『据《…》今译』标记；裸书证括注 0 条")
        # 470 批：叙述层《文王金钱课》持世引文行锚
        if not NARRATIVE_TPL.is_file():
            problems.append("文王持世：narrative_templates.json 不存在——0 结果 ≠ 通过")
        else:
            tpl = json.loads(NARRATIVE_TPL.read_text(encoding="utf-8"))
            n_w = check_wenwang_chishi(tpl, problems)
            if n_w < 14:
                problems.append(f"文王持世：行锚字段只有 {n_w}（下限 14）")
            print(f"  文王持世：{n_w} 个 quote/补 字段；src/补_src 行内逐字已核对")
            # 476 批：叙述层六神空亡/六神持世/一卦一事 quote/src 行锚
            n_na = check_narrative_anchors(tpl, problems)
            if n_na < 13:
                problems.append(f"叙述层引文：只有 {n_na} 条 quote/src（下限 13）")
            print(f"  叙述层引文：{n_na} 条（含歌源摘要/口径散文）；"
                  f"src 行号与行内逐字已核对")
            # 477 批：裁决表文案里的文件+L 行锚
            if not VERDICT_TEXTS.is_file():
                problems.append("裁决引文：verdict_texts.json 不存在——0 结果 ≠ 通过")
            else:
                vtdoc = json.loads(VERDICT_TEXTS.read_text(encoding="utf-8"))
                n_vt = check_verdict_text_anchors(vtdoc, problems)
                if n_vt < 6:
                    problems.append(f"裁决引文：文件+L 行锚只有 {n_vt} 条（下限 6）")
                print(f"  裁决引文：{n_vt} 条文件+L 行锚；行号/引文落位已核对")
        # 483 批：用神词典 note 的 file+L『…』
        if not QUESTION_USE_GODS.is_file():
            problems.append("用神词典注记：question_use_gods.json 不存在——0 结果 ≠ 通过")
        else:
            ugdoc = json.loads(QUESTION_USE_GODS.read_text(encoding="utf-8"))
            n_ug = check_usegod_notes(ugdoc, problems)
            if n_ug < 2:
                problems.append(f"用神词典注记：只有 {n_ug} 条带锚引文（下限 2）")
            print(f"  用神词典注记：{n_ug} 条带锚引文；底本/行号/行内逐字已核对")
            # 491 批：族注「…」引文（构建器明写 note 不参与核验）
            n_fn = check_usegod_family_notes(ugdoc, problems)
            if n_fn < 6:
                problems.append(f"用神词典族注：只有 {n_fn} 段「…」引文（下限 6）")
            print(f"  用神词典族注：{n_fn} 段「…」引文；《增刪卜易》底本逐字已核对")
            # 493 批：_meta 声明数（description/族数/键数）
            n_mf, n_mk = check_usegod_meta(ugdoc, problems)
            print(f"  用神词典元数据：{n_mf} 族／{n_mk} 键；"
                  f"description/family_count/key_count 自洽已核对")
        # 488 批：问题题类注记的书源引用（仅六爻册）
        if not QUESTION_CLASSES.is_file():
            problems.append("问题题类：question_classes.json 不存在——0 结果 ≠ 通过")
        else:
            qcdoc = json.loads(QUESTION_CLASSES.read_text(encoding="utf-8"))
            qc_n, qc_q = check_question_classes_notes(qcdoc, problems)
            if qc_n < 4 or qc_q < 3:
                problems.append(f"问题题类：源L 行锚 {qc_n}（下限 4）／引文 {qc_q}"
                                f"（下限 3）——先确认字段/路径")
            print(f"  问题题类注记：{qc_n} 个源L、{qc_q} 条引文；"
                  f"书名/行号/行内逐字已核对")
        # 471 批：火珠林财官伏藏引文行锚（仅六爻册）
        if not FUSHI.is_file():
            problems.append("财官伏藏：caiguan_fushi.json 不存在——0 结果 ≠ 通过")
        else:
            fdoc = json.loads(FUSHI.read_text(encoding="utf-8"))
            n_f = check_fushi_quotes(fdoc, problems)
            if n_f < 21:
                problems.append(f"财官伏藏：src/_src 行锚字段只有 {n_f}（下限 21）")
            print(f"  财官伏藏：{n_f} 个 src/_src 行锚；歌诀/注文/总纲行内逐字已核对")
        # 473 批：易林补遗门类定位映射的行锚（仅六爻册）
        if not YILIN.is_file():
            problems.append("易林补遗：yilin_buyi_maps.json 不存在——0 结果 ≠ 通过")
        else:
            ydoc = json.loads(YILIN.read_text(encoding="utf-8"))
            y_q, y_a = check_yilin_buyi_maps(ydoc, problems)
            if y_q < 16 or y_a < 34:
                problems.append(f"易林补遗：引文 {y_q}（下限 16）／行锚 {y_a}"
                                f"（下限 34）——先确认字段/路径")
            print(f"  易林补遗：{y_q} 条引文（含内联）、{y_a} 个行锚；"
                  f"底本/行号/行内逐字已核对")
        # 474 批：注册表裸 locator 行锚（仅六爻册；八字 locator 走 verdicts 的 465 面）
        n_loc = check_bare_locators(doc, problems, notes)
        if n_loc < 6:
            problems.append(f"裸 locator：只有 {n_loc} 条（下限 6）——先确认字段/路径")
        print(f"  裸 locator：{n_loc} 条行锚；书名→底本/行号/引文落位已核对")
        # 485 批：分占域判据引文库的章界＋行内逐字（仅六爻册）
        if not DOMAIN_CITES.is_file():
            problems.append("占域引文：domain_citations.json 不存在——0 结果 ≠ 通过")
        else:
            dcdoc = json.loads(DOMAIN_CITES.read_text(encoding="utf-8"))
            dc_n, dc_q = check_domain_citations(dcdoc, problems)
            if dc_n < 40 or dc_q < 56:
                problems.append(f"占域引文：域 {dc_n}（下限 40）／引文 {dc_q}"
                                f"（下限 56）——先确认字段/路径")
            print(f"  占域引文：{dc_n} 域、{dc_q} 条引文；章节锚/章界/行内逐字已核对")
    _ap = argparse.ArgumentParser(description="check_rule_registry：--selftest 负例自证开关（§三）")
    _ap.add_argument("--selftest", action="store_true", help="负例自证")
    args = _ap.parse_args()
    if args.selftest:
        before = len(problems)
        selftest(problems)
        added = len(problems) - before
        # 447 批修旧缺陷：原文 `problems = problems[:before]` 会把**自证失败**的消息一起截掉，
        # 于是「负例没抓到」也以 EXIT=0 通过。自证失败必须保留并判红；通过则无新增。
        print(f"  [selftest] {'异常：' + str(added) + ' 条自证失败（保留并判红）' if added else '负例已跑（抓到）'}")
    if checked == 0:
        print("× 0 条指针可检视——本器等于没跑，不判通过")
        return 1
    for x in notes[:10]:
        print(f"  · {x}")
    for x in problems:
        print(f"  × {x}")
    if not problems:
        print("  √ 全部 verified 指针均可回指（verified=false 者只记不判）")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
