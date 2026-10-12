# -*- coding: utf-8 -*-
"""六爻科「《书名》源L<行号> + 引文」的逐字回验器（代码注释 + 规则数据 + 文档同一口径）。

为什么需要它（2026-10-10）：本科的 249 处 `源L<n>` 书证里，绝大多数**不在文档里**，
而是写在 `scripts/*.py` 的注释/docstring 和 `data/rules/verdict_texts.json` 的 `basis` 字段中。
此前这些指针一条都没有被复核过——本批就在此处抓到真缺陷：出旬口径的书证被写成
「《增删卜易》源L1139『此等旬空到底有用，不过待其出旬』」，而该底本 L1139 是一行卦表，
句子实际在《卜筮正宗》L1066（书名与行号双错，三处引用同错）。
八字科的对等器 `bazi/dev_tools/check_source_readings.py` 只认「文档内声明 `data/sources/…` 底本」
的体例，移植过来会在本科「0 条被检视」，故按六爻体例重写（该待办见 docs/CHANGELOG.md 第四批）。

    python dev_tools/check_source_readings.py            # 全量回验
    python dev_tools/check_source_readings.py --file scripts/timing.py
    python dev_tools/check_source_readings.py --selftest  # 负例：证明本器抓得住错引/错书/裸指针

判定口径（SKILL.md 铁律：宁可显式说"没查到"，也不给假绿）：
  · 引文 ≥ FAIL_MIN 字、书名唯一可解析、归一化后在**所指行邻域**出现 → PASS
  · 同上但明确不在邻域 → MISMATCH（判红）
  · 引文落在**另一本书**的邻域而在本书没有 → WRONG_BOOK（判红，且指名该书行号）
  · 裸指针（只有行号没有引文；书名不可解析／回看窗口内无书名同理）→ **判红**（第三十二批起，
    NOTE 已从 26 清零，"未检视"不再是可长期挂靠的软档）。同一行**自声明**非逐字书证
    （大意/意译/概述/白话/是否成立/成立要件/解救条件/未核/订正…）者豁免为 NOTE，
    豁免通道本身也由 `--selftest` 反向自证（三条必须只记不判，防止硬门逼删合法声明）
  · 范围式引用（源L1925-L1931）与 < FAIL_MIN 的短引文未命中 → NOTE（只报不判红）
  · 全仓 0 条被检视 → 显式自报失败，绝不当通过
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DISC = Path(__file__).resolve().parents[1]
SRC_DIR = DISC / "data" / "sources"

# 检视范围：会被人照着执行的活文本。data/cases/* 是案例转写（有自己的三方对账），
# docs/CHANGELOG.md 是登记时点原文（文件头承诺老条目一字未改），都不进硬门。
GLOBS = ("scripts/**/*.py", "core/**/*.py", "references/**/*.md",
         "docs/**/*.md", "data/rules/*.json", "data/*.json",
         # tests/ 里同样写满 `源L<n>＋「逐字」` 书证（回归 fixture 的校勘注就是），
         # 原先不扫这一层，等于**测试文件里写的书证没有任何东西会拦**——
         # 第二十/二十一给 fixture 补的引文当时是自证过的假象：门根本没读到它们。
         "tests/**/*.py")
SKIP_NAME_PARTS = ("CHANGELOG", "__pycache__", ".pyc")

LINE_REF = re.compile(r"源\s*L\s*(\d+)")
RANGE_REF = re.compile(r"源\s*L\s*\d+\s*(?:[-–—~]\s*(?:L\s*)?\d+|/\s*L?\d+)")
BOOK = re.compile(r"《([^》]{2,24})》")   # 上限 24：书名＋章名连写（如
# 《增删卜易·用神元神忌神仇神章第九》16 字）在 12 字上限下**整个匹配不上**，
# 于是它下面几行的 源L<n> 全被判成"没有书名"——门的正则长度上限冒充成了文档的缺。
# resolve_book 按「·」取主干再回指底本，长名并不影响归属。
QUOTE_CORNER = re.compile(r"「([^」]{4,400})」")
QUOTE_BACKTICK = re.compile(r"`([^`]{8,400})`")

# 归一化：只留汉字与数字，其余（空白、中西标点、CJK 标点区、全角区、变体符号）一律剥掉。
# 用 \W 而不是手列标点：手列必然漏（本次先漏了 ﹐，又因区间写法自崩），
# 漏一个标点就把**合规引文**报成缺陷，那是门的错不是文档的错。
_DROP = re.compile(r"[\s\W_]+")
_VARIANT = str.maketrans({
    "剋": "克", "裏": "里", "羣": "群", "徧": "遍", "啓": "启", "蔵": "藏",
    "刪": "删", "鼎": "鼎", "廢": "废", "萬": "万", "為": "为", "與": "与",
    "歲": "岁", "龍": "龙", "虎": "虎", "靈": "灵", "時": "时", "來": "来",
    "爲": "为", "爾": "尔", "異": "异", "據": "据", "幾": "几", "箇": "个",
    "獨": "独", "發": "发", "靜": "静", "驗": "验", "財": "财", "沖": "冲",
    "無": "无", "應": "应", "審": "审", "隨": "随", "對": "对", "則": "则",
    "動": "动", "變": "变", "陰": "阴", "陽": "阳", "論": "论", "實": "实",
    "數": "数", "謂": "谓", "語": "语", "歲": "岁", "氣": "气", "後": "后",
    "傷": "伤", "處": "处", "動": "动", "媽": "妈",
    "內": "内", "冊": "册", "會": "会", "驗": "验", "應": "应", "卦": "卦",
    # 「黃金策」是 provenance 里的题名（底本 `huangjince_dz` 取自易藏繁体本），
    # 全仓一律写简体《黄金策》。这一对缺进去时，**所有**《黄金策》引文都被判成
    # "书名不可解析"而从未逐字核过（timing.py:54、najia_rules.md:918、
    # rule_registry.json:412、verdict_texts.json:704）——门自己的盲区冒充了文档的局限。
    "黃": "黄",
})
CJK = re.compile(r"[㐀-鿿一-龥]")
FAIL_MIN = 10   # 判红下限：短于 10 字的引文**只记不判**（速记标签容易被当成逐字承诺）
SHORT_MIN = 5   # 5 字的逐字片段（如《京氏易传》「与坤为飞伏」）也要能进检视；
#   未命中仍只记 NOTE 不判红，故降这一格只会多检出、不会多误判。   # 检视下限：6-9 字的逐句（「宜于旺相，最怕休囚」「世爻旺相有助有扶」）
#   原先被 FAIL_MIN 一刀切在门外——门把自己的长度上限报成了文档的"无引文"。
#   实测把下限直接降到 6 会捞出 51 条可验，同时爆出 9 条红：其中 3-4 条是**真缺陷**
#   （引文落在别的书上、少一个字的错引），另几条是本仓速记标签（「旺相入墓不死例」）。
#   所以这里分成两层：命中照计、短句未命中只记 NOTE，不把速记判成违规。
# 元语言黑名单：注册表/文案 JSON 里有些「…」装的是**说明**（如「暗动章定义正文缺书源」
# 「是否成立 + 成立要件 + 解救条件」），不是书证。拿它去比对底本必然假红。
META = re.compile(r"缺书源|正文缺|书源无|无逐条|待补|意译|大意|非逐字|概述|是否成立|成立要件|解救条件|"
                  r"未核|未验|结构|字段|说明")
# 结构式记法（「真空＝休囚无气＋日克」「已葬／安葬／下葬 → 官鬼」）是**规则速记**，
# 不是逐字引文：归一化会把 ＝＋／ 剥掉，于是串成一个底本里必然不存在的长句 → 假红。
NOTATION = re.compile(r"[→⇒⇔＝＋+÷≤≥≠/／\\|]")   # 半角 + 同属结构式记法：
#   「伏吟+原神动」这类引擎标签此前只列了全角 ＋，于是被当逐字引文去核，
#   把 SHORT_MIN 降到 5 之后白记一条"短引文未命中"——是门的字符类缺半角，不是文档的错。
# 撤稿记录：`basis` 里常留着「原挂《某书》『某句』经实测 0 命中，已归位」这类文字——
# 那是**缺陷的病历**，不是现行的书证。拿它去要求逐字命中，等于逼文档把病历删掉。
RETRACT = re.compile(r"原挂|原误|误挂|已归位|作废|0 ?命中|订正")
# 引号前带这些词，作者自己已声明是转述，不作逐字要求
PARAPHRASE = re.compile(r"大意|意译|概述|白话|非逐字")


def norm(s: str) -> str:
    return _DROP.sub("", str(s)).translate(_VARIANT)


def is_classical_quote(q: str) -> bool:
    n = norm(q)
    if len(n) < SHORT_MIN or LINE_REF.search(q):
        return False
    return len(CJK.findall(n)) * 10 >= len(n) * 7  # ≥70% 汉字，剔除代码标识符


def load_corpora() -> dict[str, dict]:
    """provenance.json 的 title → 底本。同名多本（wikitext 与整理本）时以 `_dz` 优先。"""
    out: dict[str, dict] = {}
    for pv in sorted(SRC_DIR.glob("*.provenance.json")):
        try:
            meta = json.loads(pv.read_text(encoding="utf-8"))
        except Exception:
            continue
        title = norm(meta.get("title") or "")
        key = pv.name.split(".")[0]
        for cand in (SRC_DIR / f"{key}.dz.txt", SRC_DIR / f"{key}.wikitext.txt"):
            if not cand.exists():
                continue
            prefer = cand.name.endswith(".dz.txt")
            cur = out.get(title)
            if cur is None or (prefer and not cur["prefer"]):
                out[title] = {"path": cand, "prefer": prefer, "key": key}
            break
    return out


def resolve_book(name: str, corpora: dict[str, dict]) -> tuple[str, list[str]]:
    """书名 → 底本。允许「增删卜易·飞伏神章」这类带篇名的写法，也允许简称唯一命中。"""
    base = norm(name.split("·")[0])
    if not base:
        return "", [f"书名「{name}」归一化后为空"]
    if base in corpora:
        return base, []
    cands = [t for t in corpora if base and (base in t or t in base)]
    if len(cands) == 1:
        return cands[0], []
    if len(cands) > 1:
        return "", [f"简称「{name}」命中多本：{','.join(cands)}"]
    return "", [f"书名「{name}」不在 data/sources provenance 里"]


def _corpus_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def _logical_line(lines: list[str], i: int) -> str:
    """本行 + 引号未闭合时的续行（古籍一段常被排成多行、注释也跨行续写）。"""
    txt = lines[i]
    for extra in (1, 2, 3):
        if txt.count("「") <= txt.count("」"):
            break
        if i + extra >= len(lines):
            break
        txt += re.sub(r"^\s*(#|\*|>|//)?\s*", "", lines[i + extra])
    return txt


ANY_REF = re.compile(r"(?:源\s*L\s*(\d+))|(?<![源\w])L\s*(\d+)(?!\s*[-–—~])")

def _anchors(txt: str) -> list[tuple[int, int, int]]:
    """逻辑行里的所有行号锚点 `(起点, 行号, 终点)`，含续锚：`源L507/L525`、
    `源L1643；L3625`、`源L1055-1056`。
    只认带「源」前缀的那个，会把后半条锚丢掉，于是把**引用完整**的写法报成缺陷。
    终点必须带出来：`_bind` 原先用 `len(f"源L{n}")` 反推锚尾，遇到裸续锚 `L3444`
    （少 1 字）或带空格的 `源 L3843`（多 1 字）就算错距离，
    把「左锚优先」的候选直接判成负距而丢弃——`verdict_texts.json:704` 的
    「、L3444『归魂卦用仍生合』」因此被配给前一条的 3843，门自己造出一条假行号漂移。"""
    out = []
    for m in ANY_REF.finditer(txt):
        n = m.group(1) or m.group(2)
        if n:
            out.append((m.start(), int(n), m.end()))
    return out


def _bind(txt: str, refs: list[tuple[int, int, int]], qpos: int, qend: int) -> tuple[list[int], int]:
    """引文与行号锚配对。本仓两种体例并存：`源L134「…」`（锚在左）与 `「…」（源L134）`（锚在右）。

    一律"取最近"会把 `源L166 逐字「A」／源L680 逐字「B」` 里的 A 配给 680
    （只差「逐字『」的距离，而 A 到 680 是「』／」的距离）——把正确引用判成行号漂移。
    规则：**左锚优先**（锚尾到引文头 ≤25 字），没有左锚才看右锚（引文尾到锚头 ≤12 字），
    两者都没有才退回最近锚。并列续锚（`源L507/L525`、`源L1643；L3625`）一起收，任一命中即过。
    """
    # 锚尾取正则给出的真实终点：`源L3444`/`L3444`/`源 L3843` 三种写法长度不同，
    # 用 len(f"源L{n}") 反推会把短锚算出负距（左锚候选被整条丢弃）。
    cands = [(qpos - e, 0, p, n) for (p, n, e) in refs if p < qpos and 0 <= qpos - e <= 25]
    # 右锚只认**括号式后置**（`「…」（源L134）`）；`源L166「A」／源L680「B」` 这种连排里
    # A 右邻的 680 其实是 B 的左锚，按纯距离会把 A 抢过去（实测差 2 字 vs 4 字）。
    between = re.compile(r"^[」』”’\s]*[（(〔【]?[、，,;；.。]*$")
    cands += [(p - qend, 1, p, n) for (p, n, _e) in refs
              if p >= qend and p - qend <= 12 and between.match(txt[qend:p])]
    if cands:
        # 距离最小者优先；同距时取左锚（`源L166 逐字「A」／源L680 逐字「B」` 里
        # A 到两侧锚几乎等距，正确的那条在左）
        _, side, cp, cn = min(cands, key=lambda t: (t[0], t[1]))
        chosen = (cp, cn)
    else:
        chosen = min([(p, n) for (p, n, _e) in refs],
                     key=lambda r: min(abs(r[0] - qpos), abs(r[0] - qend)))
    seg = sorted({n for (p, n, _e) in refs if abs(p - chosen[0]) <= 12} | {chosen[1]})
    return seg, chosen[0]


def _bound_pairs(lines: list[str], i: int) -> list[tuple[list[int], str, int]]:
    """返回 (锚点列表, 引文, 主锚位置)。"""
    txt = _logical_line(lines, i)
    refs = _anchors(txt)
    if not refs:
        return []
    out: list[tuple[list[int], str, int]] = []
    for pat in (QUOTE_CORNER, QUOTE_BACKTICK):
        for m in pat.finditer(txt):
            q = m.group(1).strip()
            if not is_classical_quote(q) or META.search(q) or NOTATION.search(q):
                continue
            if RETRACT.search(txt[max(0, m.start() - 20):m.start()]):
                continue  # 撤稿记录里的旧引文，不作逐字要求
            near = [r for r in refs if abs(r[0] - m.start()) < 80]
            if not near:
                continue
            seg, apos = _bind(txt, near, m.start(), m.end())
            gap = txt[min(apos, m.start()):max(apos, m.start())]
            if PARAPHRASE.search(gap):
                continue  # 作者已声明是转述，不作逐字要求
            out.append((seg, q, apos))
    if out:
        return out
    # **续引体例**：指针行只写「（《易林补遗·仕宦升迁章》源L811-L814）给出一组…」这类
    # 引导语，原文引号排在下面 1-3 行（本仓 docstring/表格常用）。原先只在一行内配对，
    # 这类指针一律"无可验引文"，门把自己够不到当成了文档的缺陷——105 条 NOTE 里第一大块就是它。
    # 取下面 ≤3 行的引文，但**只取自己不带行号锚的行**：带锚的行归自己管，
    # 不把别人的引文抢过来记账。绑错不怕——引文要在所标行号的邻域逐字命中，
    # 命不中当场判红，不会静默放行。
    # 续引归到**离它最近的那条锚**（＝本行最后一条锚）上，而不是把本行所有锚并成一组：
    # 一行里写两本书时（`symbols.py:120` 先《增删卜易》源L964、后《卜筮正宗》源L1066），
    # 并组会让下一行的引文去两本书的同一行号里找，必然找不中——实测造出一条假"书名/行号双疑"。
    last = refs[-1]
    for j in (1, 2, 3):
        if i + j >= len(lines):
            break
        nxt = lines[i + j]
        if _anchors(nxt) or BOOK.search(nxt):
            break  # 下一行自带锚**或自带书名**：它是一条独立书证（顶多缺行号），
            # 不能把它引的原文记到上一行的行号账上——实测就犯过这一次：
            # `step5.py:851` 只写到《增删卜易》源L1058，下一行的「伏无提挈终徒尔…」
            # 明明署《黄金策·千金赋》，被旧版续引规则抢去按 1058 验，判出一条假红。
        for pat in (QUOTE_CORNER, QUOTE_BACKTICK):
            for m in pat.finditer(nxt):
                q = m.group(1).strip()
                if not is_classical_quote(q) or META.search(q) or NOTATION.search(q):
                    continue
                if RETRACT.search(nxt[max(0, m.start() - 20):m.start()]):
                    continue
                if PARAPHRASE.search(nxt[:m.start()]):
                    continue
                out.append(([last[1]], q, last[0]))
        if out:
            break
    return out


def _books_in_order(txt: str) -> list[tuple[int, str]]:
    return [(m.start(), m.group(1)) for m in BOOK.finditer(txt)]


LOOKBACK = 8


def _book_for(txt: str, ref_pos: int, lines: list[str], i: int,
              lookback: bool = True) -> str:
    """行号归属**它前面最近**的书名；本行没有则回看上。

    回看窗口由 `LOOKBACK` 控制（当前 8 行；原先是 2）：本科的表格式登记
    （`timing.py` 八法表、`classical_enhancements_*` 的逐条书证块）习惯把《书名》
    写在块首，下面一串 `源L<n>` 都不再重复书名——只回看 2 行时这些指针全被判成
    "未检视"，门就把自己 88 条无书名的 NOTE 误当成"已经尽力了"。
    取"最近的一个书名"，所以中途若换了书（另一本书的块）自动改绑，不会跨书错配。
    """
    prior = [b for b in _books_in_order(txt) if b[0] < ref_pos]
    if prior:
        return prior[-1][1]
    if not lookback:
        return ""
    for j in range(i, max(-1, i - LOOKBACK), -1):
        bs = BOOK.findall(lines[j])
        if bs:
            return bs[-1]
    return ""


def _books_near(lines: list[str], i: int, depth: int = LOOKBACK) -> list[str]:
    """回看窗口内出现过的**全部**书名，按由近到远排序（去重）。

    混排块里（`verdict_texts.json` 求官条 1925-1931：先《易林补遗·仕宦升迁章》、
    中间插一句《增删卜易》、下面几个 源L813/814 又属于《易林补遗》）
    只取"最近一个书名"会把后两条判成"书别错"。收集全部候选再逐个试，
    全都对不上才判红——门不许把自己的解析局限算成文档的错。
    """
    out: list[str] = []
    for j in range(i - 1, max(-1, i - 1 - depth), -1):
        for b in reversed(BOOK.findall(lines[j])):
            if b not in out:
                out.append(b)
    return out


SOURCE_PATH = re.compile(r"data/sources/([A-Za-z0-9_\-\.]+)\.txt")


def _book_from_path(lines: list[str], i: int, txt: str, corpora: dict) -> str:
    """文本里若点名了 `data/sources/<key>.dz.txt`，以点名为准——比按《书名》猜测可靠。

    `rule_registry.json` 里就有一条写着「逐条实测核验（data/sources/zengshan_buyi_dz.dz.txt
    物理行）」却同时提到《卜筮正宗》，按《书名》回看会绑到兄弟块的书上，
    三条本可命中的引文被报成"书别错"。显式路径优先，书名推断退到第二位。
    """
    for j in range(i, max(-1, i - 3), -1):
        for hit in SOURCE_PATH.findall(txt) + SOURCE_PATH.findall(lines[j]):
            key = hit.split(".")[0]
            for title, meta in corpora.items():
                if meta["key"] == key:
                    return title
    return ""


def _tri(s: str) -> set[str]:
    out = set()
    for w in re.findall(r"[^，。；、：（）！？\s]+", s):
        for k in range(len(w) - 2):
            out.add(w[k:k + 3])
    return out


def _quotable_hint(lines: list[str], i: int, corpora: dict, cache: dict) -> str:
    """把"有行号无引文"这一桶分成可操作的几类。
    前几批我对这一桶连错两次描述（先说"多是硬骨头"、后说"都能抄"），
    根因是桶里只写"未检视"，不写**为什么**没被检视。现在让门自己回答：
    底本所标那一行里，到底有没有与注记同题（共享三字组）的可抄句子。"""
    txt = _logical_line(lines, i)
    refs = _anchors(txt)
    if not refs:
        return "（无行号锚：范围式或裸 L 写法）"
    b = _book_for(txt, refs[0][0], lines, i)
    title, _why = resolve_book(b, corpora) if b else ("", [])
    if not title:
        return "（书名待定位）"
    n = refs[0][1]
    if title not in cache:
        cache[title] = _corpus_lines(corpora[title]["path"])
    src = cache[title]
    if not (1 <= n <= len(src)):
        return "（行号越界）"
    if _tri(norm(txt)) & _tri(norm(src[n - 1])):
        return "（底本该行有同题句可抄＝欠账）"
    return "（该行无同题句：表格行、章题行或跨条综合引用）"


def _bare(rel: str, lineno: int, txt: str, why: str,
          problems: list[str], notes: list[str]) -> None:
    """裸指针（有行号、无可验引文）**判红**，唯一豁免是同一行已自声明非逐字书证
    （转述 / 元语言 / 订正记录 / 范围式引用）。
    第三十二批把 NOTE 从 26 清到 0 之后，"未检视"这个软档就没有容纳对象了；
    继续留着它，等于给以后每写一条裸行号都留一条不会被拦的通道——
    清零必须是**关上的门**，不是一次性的成绩。"""
    if (META.search(txt) or PARAPHRASE.search(txt)
            or RETRACT.search(txt) or RANGE_REF.search(txt)):
        notes.append(f"{rel}:{lineno} 已自声明非逐字书证（{why}），不作逐字要求")
        return
    problems.append(f"{rel}:{lineno} 裸指针：{why} —— 要么补《书名》＋该行逐字片段，"
                    f"要么在本行写明「综合数条书义、非逐字」")


def verify_file(path: Path, corpora: dict[str, dict], problems: list[str],
                notes: list[str]) -> tuple[int, int, int]:
    """返回 (可验条数, 逐字命中条数, 范围内行号指针总数)。"""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    rel = path.relative_to(DISC).as_posix()
    cache: dict[str, list[str]] = {}
    checked = passed = refs_in_scope = 0
    for i, ln in enumerate(lines):
        if "源L" not in ln and "源 L" not in ln:
            continue
        # 分母：本文件里有多少条行号指针。没有引文/书名不可解析的那些**不算验过**，
        # 但必须计入分母，否则「47 条全绿」会冒充成「本科书证全绿」。
        refs_in_scope += len(LINE_REF.findall(ln))
        txt = _logical_line(lines, i)
        pairs = _bound_pairs(lines, i)
        for seg, quote, rpos in pairs:
            # 优先级：①同一逻辑行里行号左边的《书名》最具体；②再认点名的 data/sources 路径；
            # ③最后才回看若干行找书名（块首登记）。上一条注记里「《增删卜易》源L692」被
            # 两行外的 quote_in_source 路径抢走，就是②压在①前面造成的假红。
            b_inline = _book_for(txt, rpos, lines, i, lookback=False)
            b_path = _book_from_path(lines, i, txt, corpora)
            b_near = _book_for(txt, rpos, lines, i)
            bname = b_inline or b_path or b_near
            # 混排块里书名可能逐行换书（verdict_texts 的求官条目 1925-1931 就是这样），
            # 这时按"最近书名"判红是门在冤枉文档：把所有候选书名都当一次底本试，
            # 有一个在其所标行号命中即算过（并记 NOTE 说明歧义），一个都不中才判红。
            cand_books = ([b for b in (b_inline, b_path, b_near) if b]
                          + _books_near(lines, i))
            if not bname:
                _bare(rel, i + 1, txt, f"本行与回看 {LOOKBACK} 行内都没有《书名》",
                      problems, notes)
                continue
            title, why = resolve_book(bname, corpora)
            if not title:
                _bare(rel, i + 1, txt, why[0] if why else "书名不可解析", problems, notes)
                continue
            if title not in cache:
                cache[title] = _corpus_lines(corpora[title]["path"])
            src = cache[title]
            nq = norm(quote)
            checked += 1
            bad = [n for n in seg if n < 1 or n > len(src)]
            if len(bad) == len(seg):
                problems.append(f"{rel}:{i + 1} 源L{'/'.join(str(n) for n in seg)}：超出《{title}》"
                                f"底本行数（共 {len(src)} 行）→ {quote[:26]}")
                continue
            hit = any(_hit_in(quote, "".join(norm(x) for x in src[max(0, n - 2):n + 3]))
                      for n in seg if 1 <= n <= len(src))
            if not hit:
                alt = _hit_in_any_candidate(quote, cand_books, corpora, cache, seg)
                if alt:
                    passed += 1
                    notes.append(f"{rel}:{i + 1} 书名歧义（候选 {'、'.join(cand_books)}）："
                                 f"按《{alt}》源L{'/'.join(str(n) for n in seg)} 命中，未判红")
                    continue
            if hit:
                passed += 1
                # 命中后再查一层「完全子串」。门比较前会剥标点（那是防假阳性的正确设计），
                # 于是「底本作。／我写，」这类改过标点的引文照样通过。第二十九批实测
                # 我自己新加的 14 条里有 9 条不是逐字——只靠人眼复核不可持续，
                # 故加一条信息级信号（不判红：合法的省略号引用与繁简异体也会触发它）。
                raw = "".join("".join(src[max(0, m - 2):m + 3])
                              for m in seg if 1 <= m <= len(src))
                # 比「完全子串」前先消掉两类排版噪声：跨行续写的空白、相邻字符串字面量
                # 拼接留下的 ""（那是 Python 写法，不是文档改了原文）。标点一律保留，
                # 因为「底本作。／我写，」正是这条信号要抓的东西。
                _MARKUP = ('"', "'", "“", "”", "‘", "’")
                def _cut(s):
                    return "".join(ch for ch in s if not ch.isspace() and ch not in _MARKUP)
                if "…" not in quote and "..." not in quote and _cut(quote) not in _cut(raw):
                    notes.append(f"{rel}:{i + 1} 仅归一化相等（疑改标点或异体字），不判红 → {quote[:26]}")
                continue
            elsewhere = _find_in_other_corpora(quote, corpora, cache, skip=title)
            sameline = _find_in_corpora(quote, [(title, src)])
            tag = f"源L{'/'.join(str(n) for n in seg)}"
            if sameline:
                problems.append(f"{rel}:{i + 1} 行号漂移：《{title}》确有此句但在{sameline}，"
                                f"所标 {tag} 邻域无 → {quote[:26]}")
            elif elsewhere:
                problems.append(f"{rel}:{i + 1} 书名/行号双疑：《{title}》{tag} 邻域无此句，"
                                f"却在 {elsewhere} 命中 → {quote[:26]}")
            elif len(nq) >= FAIL_MIN:
                problems.append(f"{rel}:{i + 1} 《{title}》{tag}：引文与底本这些行邻域不符"
                                f" → {quote[:30]}")
            else:
                notes.append(f"{rel}:{i + 1} 《{title}》{tag}：短引文未命中，只记不判")
        if LINE_REF.search(ln) and not pairs and not RANGE_REF.search(ln):
            _bare(rel, i + 1, txt, f"有行号无同行引文 {_quotable_hint(lines, i, corpora, cache)}",
                  problems, notes)
    return checked, passed, refs_in_scope


def _frags(q: str) -> list[str]:
    """省写号「…」是**合格的引用体例**（底本一长段里摘两头），不是错引。
    整串去比必然不命中——那会把合规写法报成缺陷，逼人改掉本来正确的引文。"""
    parts = [p for p in re.split(r"…{1,2}|\.{3}|⋯", q) if len(norm(p)) >= 4]
    return parts if len(parts) >= 2 else [q]


def _hit_in(quote: str, hay: str) -> bool:
    return all(norm(f) in hay for f in _frags(quote))


def _hit_in_any_candidate(quote: str, books: list[str], corpora: dict,
                           cache: dict, seg: list[int]) -> str:
    """按同一行号去其它候选底本里试一次；命中就返回那本书名（书名歧义兜底）。"""
    for t in dict.fromkeys(books):
        title, _why = resolve_book(t, corpora) if t not in corpora else (t, [])
        if not title or title not in corpora:
            continue
        if title not in cache:
            cache[title] = _corpus_lines(corpora[title]["path"])
        src = cache[title]
        if any(_hit_in(quote, "".join(norm(x) for x in src[max(0, n - 2):n + 3]))
               for n in seg if 1 <= n <= len(src)):
            return title
    return ""


def _find_in_corpora(quote: str, pairs: list[tuple[str, list[str]]]) -> str:
    for title, src in pairs:
        for n, t in enumerate(src, 1):
            if _hit_in(quote, norm(t)):
                return f"《{title}》源L{n}"
    return ""


def _find_in_other_corpora(quote: str, corpora: dict[str, dict],
                           cache: dict[str, list[str]], skip: str) -> str:
    pairs = []
    for title, meta in corpora.items():
        if title == skip:
            continue
        if title not in cache:
            cache[title] = _corpus_lines(meta["path"])
        pairs.append((title, cache[title]))
    return _find_in_corpora(quote, pairs)


def selftest(problems: list[str]) -> None:
    """负例四件：错引必须判红、**书名张冠李戴**必须判红、**裸指针**必须判红、
    真引文必须放行（防假阳性），且已自声明非逐字的三条不得被硬门误伤。"""
    zg = SRC_DIR / "bushi_zhengzong_dz.dz.txt"
    zb = SRC_DIR / "zengshan_buyi_dz.dz.txt"
    if not (zg.exists() and zb.exists()):
        problems.append("负例自证无法执行：缺卜筮正宗/增删卜易底本")
        return
    good = "此等旬空到底有用，不过待其出旬"   # 真句，在卜筮正宗 L1066
    ell = "飞不冲开亦枉然…须宜月建日辰冲开飞神"  # 真句的**省写**引用，在增删卜易 L1535
    tmp = DISC / "scripts" / "_selftest_fake_source_refs.py"
    tmp.write_text(
        "# -*- coding: utf-8 -*-\n"
        f"# 真引文（《卜筮正宗》源L1066 逐字）：「{good}」\n"
        "# 假引文（《卜筮正宗》源L1066 逐字）：「此串绝无可能出现在任何古籍里用来测试回验器」\n"
        f"# 张冠李戴（《增删卜易》源L1139 逐字）：「{good}」\n"
        f"# 省写引用（《增删卜易》源L1535 逐字）：「{ell}」\n"
        "# 后置锚（《卜筮正宗》）：「" + good + "」（源L1066）\n"
        "# 连排双锚（《易冒》源L166 逐字「是故随官入墓、助鬼伤身、合处逢冲，此占世之凶征也。」"
        "／源L680 逐字「然成卦之主，世应为重，其忌亦有十」）\n"
        "# 后置但有左锚竞争（《断易天机》源L136，判定式）："
        "「一、助鬼：助鬼之爻只有妻财爻。」（源L134）\n"
        "# 续锚（《卜筮正宗》源L507/L525 逐字）：「火绝在亥谓之伏神绝于飞爻」\n"
        "# 元语言非书证（《卜筮正宗》源L1066）：「是否成立 + 成立要件 + 解救条件」\n"
        "# 转述（《卜筮正宗》源L1066 大意）：「旬空之爻到底有用不必拘填实」\n"
        "# 订正记录（《卜筮正宗》源L241）：原挂「游魂行无定，归魂回故乡」经实测 0 命中，已归位\n"
        "# 裸指针负例（《卜筮正宗》源L1066）：这一行故意只写行号，测本器的硬门\n",
        encoding="utf-8")
    try:
        sub_p: list[str] = []
        sub_n: list[str] = []
        checked, passed, _ = verify_file(tmp, load_corpora(), sub_p, sub_n)
        if checked != 9:
            problems.append(f"负例自证：只验到 {checked} 条（应 9 条：真/假/张冠李戴/省写/"
                            "后置/连排两条/后置竞争/续锚），样本无效")
        if not any("绝无可能出现在任何古籍里" in x for x in sub_p):
            problems.append(f"负例自证失效：编造的错误引文没被判红 → {sub_p}")
        if not any("书名/行号双疑" in x and "卜筮正宗》源L1066" in x for x in sub_p):
            problems.append("负例自证失效：书名张冠李戴没被指认（本器不足以挡住本批真缺陷）")
        if len(sub_p) != 3:
            problems.append(f"负例自证判红数异常：应恰好 3 条（假引文 + 张冠李戴 + 裸指针），"
                            f"实得 {len(sub_p)} 条 → {sub_p}")
        if not any("裸指针" in x for x in sub_p):
            problems.append("负例自证失效：只写行号不写原文的裸指针没被判红——"
                            "第三十二批清零后这道硬门形同虚设")
        # 反向也要自证：**已声明非逐字**的行不能被硬门误伤，否则等于逼人删掉合法的转述声明
        if len(sub_n) != 3:
            problems.append(f"负例自证（豁免通道）异常：元语言/转述/订正三条应记 NOTE 不判红，"
                            f"实得 {len(sub_n)} 条 → {sub_n}")
        if passed != 7 or checked != 9:
            problems.append(f"负例自证计数异常：应「9 条可验 / 7 条命中（2 条负例必红）」，"
                            f"实得「{checked} 可验 / {passed} 命中」（{sub_p}）")
    finally:
        tmp.unlink(missing_ok=True)


def iter_targets(one: str) -> list[Path]:
    out: list[Path] = []
    if one:
        p = DISC / one
        if not p.exists():
            return []
        # 单文件模式也必须守住口径：CHANGELOG 的旧条目按文件头承诺是登记时点原文，
        # 逐字回验一旦判红，唯一"修法"就是去改历史条目——那是门在逼人伪造历史。
        if any(x in p.name for x in SKIP_NAME_PARTS):
            print(f"  （{one} 属历史散文/编译产物，本器不检视；见文件头口径）")
            return []
        return [p]
    for g in GLOBS:
        for p in sorted(DISC.glob(g)):
            if p.is_file() and not any(x in p.name for x in SKIP_NAME_PARTS):
                out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="六爻书证「《书名》源L行号+引文」逐字回验")
    ap.add_argument("--file", default="", help="只验一个文件（相对学科根）")
    ap.add_argument("--notes", action="store_true", help="打印全量 NOTE（默认只列 15 条）")
    ap.add_argument("--selftest", action="store_true", help="负例自证")
    args = ap.parse_args()

    corpora = load_corpora()
    if not corpora:
        print("× data/sources/*.provenance.json 不可用，本器无底本可回验")
        return 1
    problems: list[str] = []
    notes: list[str] = []
    total_c = total_p = total_refs = 0
    targets = iter_targets(args.file)
    if args.file and not targets:
        if any(x in Path(args.file).name for x in SKIP_NAME_PARTS):
            print("本器按口径不检视该文件（历史散文/编译产物），不判红也不判通过")
            return 0
        print(f"× 文件不存在：{args.file}")
        return 1
    for p in targets:
        try:
            c, got, n_ref = verify_file(p, corpora, problems, notes)
            total_refs += n_ref
        except Exception as exc:  # 门半途崩 =  coverage 造假，必须自报而不是留下一个绿色空档
            problems.append(f"{p.relative_to(DISC).as_posix()}：本器检视中断（{type(exc).__name__}: "
                            f"{exc}）——该文件之后的引文一条都没验过，不判通过")
            continue
        if c:
            print(f"  {p.relative_to(DISC).as_posix()}: 可验 {c} 条，逐字命中 {got} 条")
        total_c += c
        total_p += got

    if args.selftest:
        selftest(problems)
        print("  [selftest] 负例已跑")

    print(f"合计：范围内行号指针 {total_refs} 条，其中 {total_c} 条具备可验形态、"
          f"{total_p} 条逐字命中；{len(problems)} 条判红 / {len(notes)} 条 NOTE"
          f"（底本 {len(corpora)} 种）")
    if total_c == 0:
        print("× 0 条被真正检视——本器等于没跑，不判通过")
        return 1
    # NOTE 构成由本器现场分类：文档里那句「剩 N 条 NOTE，其中 x 无书名 / y 缺引文」
    # 必须是跑出来的数。上一批我手写了一组（30/41/66），实测是 27/103/6/1，
    # 大头（缺引文）被低估一半多，照着假数排工期就会去干错的事。
    bucket: dict[str, int] = {}
    for n in notes:
        if "都没有《书名》" in n:
            k = "无书名（回看窗口内也没有）"
        elif "有行号无同行引文" in n:
            # 这一桶按**为什么没引文**分开计：能抄没抄是欠账（可还），
            # 底本那一行根本没有同题句是体例问题（跨条综合引用，还不了也不该硬造）。
            # 前几批我对这桶连错两次描述（先"多是硬骨头"后"都能抄"），
            # 就是因为桶里只有一个总数，逼人去猜。
            if "有同题句可抄" in n:
                k = "缺引文·该行有同题句（欠账，可补）"
            elif "无同题句" in n:
                k = "缺引文·该行无同题句（跨条综合／表格体例）"
            else:
                k = "缺引文·书名或行号待定位"
        elif "书名歧义" in n or "书名不可解析" in n or "provenance" in n:
            k = "书名不在表／简称歧义"
        elif "短引文未命中" in n:
            k = "短引文未命中（记不判）"
        else:
            k = "其它"
        bucket[k] = bucket.get(k, 0) + 1
    if sum(bucket.values()) != len(notes):
        print(f"× NOTE 分类对不上账：各桶合计 {sum(bucket.values())} ≠ 总 {len(notes)}")
        return 1
    print("  NOTE 构成：" + "、".join(f"{k} {v}" for k, v in sorted(
        bucket.items(), key=lambda kv: -kv[1])))
    shown = notes if args.notes else notes[:15]
    for n in shown:
        print(f"  · {n}")
    if len(notes) > len(shown):
        print(f"  （只显示 {len(shown)}/{len(notes)} 条，--notes 看全量）")
    for x in problems:
        print(f"  × {x}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
