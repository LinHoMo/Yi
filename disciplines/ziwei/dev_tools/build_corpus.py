# -*- coding: utf-8 -*-
"""紫微斗数语料机械提取器：从 data/sources/ 的《紫微斗數全書》原文提取外置语料。

    python dev_tools/build_corpus.py             # 提取并写 data/*.json
    python dev_tools/build_corpus.py --dry-run   # 只打印统计与抽样

只做**字符级**提取（AGENTS.md：断语/引文进 data，代码只留算法）：
  - star_nature     十四主星性情说解 ← 卷一「諸星問答論」各星段希夷先生答语
  - star_palace     十二宫诸星释义   ← 卷二「一 命宫」…「十二父母」（逐星逐宫照录）
  - star_brightness 庙陷引文层       ← 卷二「一 命宫」各主星本宫诗的「子午宫入庙」明文
                    + 同度表（「X同度」明文，「与」字可省；供安星公式回归自证）
  - sihua_quotes    四化释义         ← 卷一「問化祿/權/科/忌星所主若何」希夷先生答语
  - geju_rules      格局判据         ← 卷一「定富局/定貴局/定貧賤局/定雜局」

书名/星名键一律用简体（与本仓库引擎口径一致），引文照录原文、不做简繁转写。
原文未明写的一律不填（宁缺勿滥，与 ming 调候表同口径）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "core"))

from yishu_core.ganzhi_calendar import EARTHLY_BRANCHES  # noqa: E402  地支序唯一真值源
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.ziwei_tables import MAIN_STAR_ORDER  # noqa: E402  主星序唯一真值源
from yishu_core import corpus_kit  # noqa: E402  语料可复现性比对

SOURCE = ROOT / "data" / "sources" / "zi-wei-dou-shu-quan-shu.wikitext.txt"
BOOK = "《紫微斗數全書》"

# 星名：键为简体规范名（引擎口径），值为原文可能出现的写法（繁简并存）
STAR_ALIASES: dict[str, list[str]] = {
    "紫微": ["紫微"], "天机": ["天机", "天機"], "太阳": ["太阳", "太陽"],
    "武曲": ["武曲"], "天同": ["天同"], "廉贞": ["廉贞", "廉貞"],
    "天府": ["天府"], "太阴": ["太阴", "太陰"], "贪狼": ["贪狼", "貪狼"],
    "巨门": ["巨门", "巨門"], "天相": ["天相"], "天梁": ["天梁"],
    "七杀": ["七杀", "七殺"], "破军": ["破军", "破軍"],
    "文昌": ["文昌"], "文曲": ["文曲"], "左辅": ["左辅", "左輔"],
    "右弼": ["右弼"], "禄存": ["禄存", "祿存"],
    "擎羊": ["擎羊"], "陀罗": ["陀罗", "陀羅"], "火星": ["火星"],
    "铃星": ["铃星", "鈴星"], "天魁": ["天魁"], "天钺": ["天钺", "天鉞"],
}
ALL_STARS = list(STAR_ALIASES)
# 辅煞星 = 别名表里非主星者（本建器只用于「凡有独立标题则入 star_nature」这一层）
AUX_STARS = [s for s in ALL_STARS if s not in MAIN_STAR_ORDER]
ALIAS_TO_CANON = {a: c for c, al in STAR_ALIASES.items() for a in al}
STAR_MATCH_RE = re.compile("^(" + "|".join(
    sorted(ALIAS_TO_CANON, key=len, reverse=True)) + ")")
STAR_ANY_RE = re.compile("(" + "|".join(
    sorted(ALIAS_TO_CANON, key=len, reverse=True)) + ")")

# 卷二十二宫小节标题 → 本仓库 PALACES 宫名
PALACE_SECTIONS = [
    ("一 命宫", "命宫"), ("二兄弟", "兄弟"), ("三妻妾", "夫妻"),
    ("四子女", "子女"), ("五财帛", "财帛"), ("六疾厄", "疾厄"),
    ("七迁移", "迁移"), ("八奴仆", "交友"), ("九官禄", "官禄"),
    ("十田宅", "田宅"), ("十一福德", "福德"), ("十二父母", "父母"),
]

# 庙陷词：原文写法（长词在前，避免「入庙」被「庙」截断），按档归并
BRIGHTNESS_WORDS = ["入廟", "入庙", "廟旺", "庙旺", "廟地", "庙地", "旺地", "旺宮",
                    "旺宫", "得地", "得宮", "利益", "和平", "平和", "陷地", "陷宮",
                    "陷宫", "闲宫", "廟", "庙", "旺", "得", "利", "平", "陷"]
LEVEL_OF = {
    "入廟": "入庙", "入庙": "入庙", "廟": "入庙", "庙": "入庙",
    "廟地": "入庙", "庙地": "入庙", "廟旺": "庙旺", "庙旺": "庙旺",
    "旺地": "旺", "旺宮": "旺", "旺宫": "旺", "旺": "旺",
    "得地": "得", "得宮": "得", "得": "得",
    "利益": "利", "利": "利", "和平": "平", "平和": "平", "平": "平",
    "陷地": "陷", "陷宮": "陷", "陷宫": "陷", "陷": "陷", "闲宫": "闲",
}

BRANCH = "".join(EARTHLY_BRANCHES)   # 取自 core，不在学科内另存一份地支序
LEVEL_RE = re.compile(r"([" + BRANCH + r"]{1,2})宫(" + "|".join(BRIGHTNESS_WORDS) + r")")
BRANCH_GROUP_RE = re.compile(r"([" + BRANCH + r"]{1,2})宫")
COMPANION_RE = re.compile(
    r"与?(" + "|".join(MAIN_STAR_ORDER) + r")同度")

HUA_HEAD = re.compile(r"^={4,6}\s*(?:問|问)化(.)星所主若何\s*[？?]\s*={4,6}\s*$")
STAR_HEAD = re.compile(
    r"^={4,6}\s*(?:問|问)(.+?)(?:所主若何|所主如何|所主為何|所主為)\s*[？?]\s*={4,6}\s*$")
# 任意 4~6 级标题行：用于给星段**定界**。只按 STAR_HEAD 定界时，非星名的标题
# （如「问流年昌曲若何」「羊陀二星总论」）会被吞进上一星的说解正文里。
ANY_HEAD = re.compile(r"^={4,6}\s*\S.*?={4,6}\s*$")
# 卷二各星段落里的子标签行（「紫微入男命吉凶诀：」等），不是说解正文
LABEL_RE = re.compile(r"^.{0,6}(吉凶诀|吉凶訣|总论|總論|诀|訣)\s*[:：]\s*$")


def canon(name: str) -> str | None:
    """原文星名写法 → 简体规范名；不认得的返回 None。

    书源标题有两种写法：「問紫微所主若何」与「问文曲星所主若何」（多一个「星」字）。
    故**先认原名，再退一步试去尾「星」**——旧实现无条件 `rstrip("星")`，会把
    「火星」「铃星」这类**本身以星结尾**的合法星名削成「火」「铃」而整段丢失。
    """
    n = name.strip()
    if n in ALIAS_TO_CANON:
        return ALIAS_TO_CANON[n]
    if n.endswith("星") and n[:-1] in ALIAS_TO_CANON:
        return ALIAS_TO_CANON[n[:-1]]
    return None


# ── wiki 文本清理与切分 ────────────────────────────────────────────────────

def strip_markup(s: str) -> str:
    """去掉 wiki 模板/标签，保留正文（只做字符级清理，不改写文字、不转简繁）。"""
    s = re.sub(r"\{\{另\|([^|}]*)\|[^}]*\}\}", r"\1", s)
    s = re.sub(r"\{\{參\|([^|}]*)\|[^}]*\}\}", r"\1", s)
    s = re.sub(r"\{\{[^}]*\}\}", "", s)
    s = re.sub(r"<[^>]+>", "", s)
    return s.replace("'''", "").strip()


def headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """[(行号, 层级, 标题)]；层级 = 等号个数。"""
    out = []
    for i, line in enumerate(lines):
        m = re.match(r"^(={2,6})\s*(.+?)\s*\1\s*$", line.strip())
        if m:
            out.append((i, len(m.group(1)), m.group(2)))
    return out


def section_body(lines: list[str], heads: list[tuple[int, int, str]],
                 title: str) -> list[str]:
    """某标题的正文：直到下一个**同级或更高级**标题为止。"""
    for idx, (ln, level, t) in enumerate(heads):
        if t != title:
            continue
        end = len(lines)
        for ln2, level2, _ in heads[idx + 1:]:
            if level2 <= level:
                end = ln2
                break
        return lines[ln + 1:end]
    return []


def poems(lines: list[str]) -> list[list[str]]:
    """抽出一段原文里的所有 <poem> 块。"""
    blocks, cur = [], None
    for line in lines:
        low = line.strip().lower()
        if "<poem>" in low:
            cur = []
            continue
        if "</poem>" in low:
            if cur is not None:
                blocks.append(cur)
            cur = None
            continue
        if cur is not None:
            cur.append(line)
    return blocks


def prose_lines(lines: list[str]) -> list[str]:
    """poem 之外的正文行（滤掉空行/表格/标签行）。"""
    out, inside = [], False
    for line in lines:
        low = line.strip().lower()
        if "<poem>" in low:
            inside = True
            continue
        if "</poem>" in low:
            inside = False
            continue
        if inside:
            continue
        t = strip_markup(line)
        if t and not t.startswith(("|", "-", "<")):
            out.append(t)
    return out


def star_segments(body: list[str]) -> dict[str, dict]:
    """把「以星名起首的散文段 + 其后的 <poem> 块」切成 {星名: {prose, poems}}。

    断段信号用**结构**而非字面：原书体例是先列一星的说解、再列它的诗（本宫/男命/
    女命/限），故下一星的说解必定紧跟在某段诗之后。仅凭「行首是星名」会误断——
    天机段里有续句「天梁太阴巨门见羊陀火铃忌冲合财帛」（行首正是「天梁」）。
    """
    segs: dict[str, dict] = {}
    cur: str | None = None
    in_poem, buf = False, None
    after_poem = True          # 段首或刚出诗：下一个星名行开新段
    for line in body:
        low = line.strip().lower()
        if "<poem>" in low:
            in_poem, buf = True, []
            continue
        if "</poem>" in low:
            if cur and buf is not None:
                segs[cur]["poems"].append([strip_markup(x) for x in buf])
            in_poem, buf, after_poem = False, None, True
            continue
        if in_poem:
            if buf is not None:
                buf.append(line)
            continue
        text = strip_markup(line)
        if not text or text.startswith(("|", "-", "<")) or LABEL_RE.match(text):
            continue
        m = STAR_MATCH_RE.match(text)
        star = canon(m.group(1)) if m else None
        if star and (cur is None or after_poem):
            cur = star
            segs.setdefault(cur, {"prose": [], "poems": []})
        after_poem = False
        if cur:
            segs[cur]["prose"].append(text)
    return {k: {"prose": "".join(v["prose"]), "poems": v["poems"]}
            for k, v in segs.items()}


def split_star_entries(chunks: list[str]) -> dict[str, str]:
    """把「以星名起首的段落」归并为 {星名: 原文}（用于卷二非命宫各宫）。

    原书体例：每宫逐一列出各星，故**同一星名在宫内只起一条**；行首星名后紧接
    「同/同度」的是上一条的续句（如紫微条内的「天府同富足终身保守」），不是新条。
    """
    entries: dict[str, list[str]] = {}
    cur: str | None = None
    for raw in chunks:
        text = strip_markup(raw)
        if not text:
            continue
        m = STAR_MATCH_RE.match(text)
        star = canon(m.group(1)) if m else None
        cont = bool(star) and re.match(r"^" + re.escape(m.group(1)) + r"(同|同度)", text)
        if star and not cont and star not in entries:
            cur = star
            entries[cur] = [text]
        elif cur:
            entries[cur].append(text)
    return {k: "".join(v) for k, v in entries.items()}


def answer_segments(lines: list[str], heads: list[tuple[int, int, str]]) -> dict[str, dict]:
    """卷一諸星問答論子段 → {主星: {prose, poems}}（子标题形如「問紫微所主若何？」）。"""
    body = section_body(lines, heads, "諸星問答論")
    # 段界一律取「下一个任意标题行」，而不是「下一个星名标题行」——否则
    # 「问流年昌曲若何」「羊陀二星总论」这类非星名标题及其正文会被并入上一星段。
    head_at = [i for i, line in enumerate(body) if ANY_HEAD.match(line.strip())]
    marks: list[tuple[int, str]] = []
    for i, line in enumerate(body):
        m = STAR_HEAD.match(line.strip())
        if m:
            star = canon(m.group(1))
            if star:
                marks.append((i, star))
    out: dict[str, dict] = {}
    for start, star in marks:
        end = next((h for h in head_at if h > start), len(body))
        seg = body[start + 1:end]
        out[star] = {"prose": "".join(prose_lines(seg)),
                     "poems": [[strip_markup(x) for x in blk] for blk in poems(seg)]}
    return out


# ── 各语料表 ───────────────────────────────────────────────────────────────

# star_nature 取「说解正文」的最低实质长度（汉字数，扣除引出歌诀的尾巴后计）
MIN_NATURE_HANZI = 30
NATURE_SONG_TAILS = ("歌曰", "歌")


def nature_quote(seg: dict | None) -> str:
    """star_nature 的「说解正文」取值；实质正文不足则返回空串。

    不少星段正文以「…歌曰」收尾再引出歌诀（主星如天相/天梁/七杀亦然，属正常说解）。
    但「答曰：火星乃南斗浮星也。希夷先生歌曰」这类**只报出性就引出歌诀**的，照收会得到
    一条截断引文，反成误导。判据：扣掉结尾的「歌曰/歌」后，实质汉字数须达
    `MIN_NATURE_HANZI`（该星的卷二宫位释义仍见 `star_palace`，不因此失载）。
    """
    prose = (seg or {}).get("prose") or ""
    t = prose.rstrip()
    for tail in NATURE_SONG_TAILS:
        if t.endswith(tail):
            t = t[: -len(tail)]
            break
    return prose if len(re.findall(r"[\u4e00-\u9fff]", t)) >= MIN_NATURE_HANZI else ""


def build_brightness(segs: dict[str, dict]) -> tuple[dict, list[str]]:
    """星 × 宫支 → 庙陷（只收本宫诗明文，带逐条引文）；返回 (表, 冲突清单)。"""
    table: dict[str, dict[str, dict]] = {}
    conflicts: list[str] = []
    for star, seg in segs.items():
        for line in (seg["poems"][0] if seg["poems"] else []):
            for m in LEVEL_RE.finditer(line):
                branches, level = m.group(1), LEVEL_OF[m.group(2)]
                for br in branches:
                    slot = table.setdefault(star, {}).setdefault(
                        br, {"levels": [], "quote": line})
                    if level not in slot["levels"]:
                        slot["levels"].append(level)
                        if len(slot["levels"]) > 1:
                            conflicts.append(f"{star}{br}: {'/'.join(slot['levels'])}「{line}」")
    return table, conflicts


def build_companions(segs: dict[str, dict]) -> dict:
    """星 × 宫支 → 同度主星（原文「X同度」明文，「与」字可省；供安星回归自证）。

    原书一行常并写两宫（「寅宫旺申宫得地，与巨门同度」「子午宫入庙」），故把
    「同度」二字之前出现的**全部**宫位组都算上，而不是只取行首那一组。
    计数口径与格数的唯一权威读数在 dev_tools/regression.py（companion_cells）。
    """
    out: dict[str, dict[str, list[str]]] = {}
    for star, seg in segs.items():
        for line in (seg["poems"][0] if seg["poems"] else []):
            if "同度" not in line:
                continue
            heads = BRANCH_GROUP_RE.findall(line[:line.index("同度")])
            if not heads:
                continue
            comps = [canon(c) or c for c in COMPANION_RE.findall(line)]
            for grp in heads:
                for br in grp:
                    out.setdefault(star, {})[br] = comps
    return out


def build_sihua(lines: list[str], heads: list[tuple[int, int, str]]) -> dict:
    """问化禄/权/科/忌星所主若何 → 四化释义逐字引文。"""
    body = section_body(lines, heads, "諸星問答論")
    out: dict[str, dict[str, str]] = {}
    cur: str | None = None
    buf: list[str] = []
    for line in body:
        m = HUA_HEAD.match(line.strip())
        if m:
            if cur:
                out[cur] = {"quote": "".join(buf)}
            cur, buf = m.group(1), []
            continue
        if re.match(r"^={2,6}", line.strip()):
            if cur:
                out[cur] = {"quote": "".join(buf)}
                cur = None
            continue
        if cur is not None:
            t = strip_markup(line)
            if t:
                buf.append(t)
    if cur:
        out[cur] = {"quote": "".join(buf)}
    for k, v in out.items():
        v["location"] = f"{BOOK}卷一·諸星問答論·問化{k}星所主若何"
    return out


GEJU_SECTIONS = [("定富局", "富局"), ("定贵局", "贵局"),
                 ("定贫贱局", "贫贱局"), ("定杂局", "杂局")]


def build_geju(lines: list[str], heads: list[tuple[int, int, str]]) -> dict:
    """定富局/定贵局/定贫贱局/定杂局 → 格局名 + 判据原文。"""
    out: dict[str, dict] = {}
    for title, kind in GEJU_SECTIONS:
        blocks = poems(section_body(lines, heads, title))
        for line in (blocks[0] if blocks else []):
            text = strip_markup(line)
            m = re.match(r"^(\S+?)\s+(\S.*)$", text) if text else None
            if m:
                out[m.group(1)] = {"kind": kind, "rule": m.group(2).strip(),
                                   "location": f"{BOOK}卷一·{title}"}
    return out


def build_star_palace(lines: list[str], heads: list[tuple[int, int, str]],
                      segs: dict[str, dict]) -> dict:
    """卷二各宫 → 星名 → 原文（命宫段取逐星散文，其余宫取诗内逐星条目）。"""
    out: dict[str, dict[str, dict[str, str]]] = {}
    for title, palace in PALACE_SECTIONS:
        body = section_body(lines, heads, title)
        if not body:
            continue
        if palace == "命宫":
            entries = {star: seg["prose"] for star, seg in segs.items() if seg["prose"]}
        else:
            chunks = [ln for blk in poems(body) for ln in blk] or body
            entries = split_star_entries(chunks)
        if entries:
            out[palace] = {star: {"quote": q, "location": f"{BOOK}卷二·{title}"}
                           for star, q in entries.items()}
    return out


# ── 紫微定位表（卷二五张安紫微图）与安星诀 ──────────────────────────────────

# 卷二「安紫微圖」五张字符表的图顶界行（1-based，书源行号）。
# 每张图四个横排区块，每区块 = 空行 / 第一行日期字 / 第二行日期字 / 空行 / 地支行，
# 日期的两个数字**按字符列对齐**（如「初初」+「八九」= 初八、初九）。
ZHI_GRID_TOP = {"水二局": 1940, "木三局": 1970, "金四局": 2000,
                "土五局": 2032, "火六局": 2063}
GRID_BLOCKS = ((2, 3), (8, 9), (14, 15), (20, 21))   # (第一行偏移, 第二行偏移)；地支行 = 第二行+2

CN_NUM = {
    "初一": 1, "初二": 2, "初三": 3, "初四": 4, "初五": 5, "初六": 6, "初七": 7,
    "初八": 8, "初九": 9, "初十": 10, "十一": 11, "十二": 12, "十三": 13, "十四": 14,
    "十五": 15, "十六": 16, "十七": 17, "十八": 18, "十九": 19, "二十": 20,
    "廿一": 21, "廿二": 22, "廿三": 23, "廿四": 24, "廿五": 25, "廿六": 26,
    "廿七": 27, "廿八": 28, "廿九": 29, "三十": 30,
}

# 书源自身残缺的两格：全表结构可机械自洽推出，原文另存可复核。
#   木三局：寅格作「三九」、辰格作「一九一」→「初九」重出而全表缺「初五」；
#     本局结构为「初二起每三格一组 (x, x+1, x+4)，x 逐组加一」，30 格零例外，
#     且合本局歌诀「生逢木宫三岁起……顺回四步一辰字」之「顺回四步」。
#     按此结构：寅格之「九」当作「五」→ 初五在寅；「初九」归辰格（辰格三格 初一/初九/十一）。
#   金四局：书源只 29 格，缺「三十」；本局相邻日差呈 4 周期 (-3,+1,-2,+5)（净 +1／4 日），
#     29 格 28 个差值零例外。
GRID_DERIVED = {
    "木三局": {"初五": "寅", "初九": "辰",
               "理由": "书源寅格「三九」与辰格「一九一」致初九重出、初五无着；"
                       "按本局初二起每三格 (x,x+1,x+4) 的结构（30 格零例外）推知"
                       "寅格之九当作五（初五在寅）、初九归辰"},
    "金四局": {"三十": "亥",
               "理由": "书源只 29 格；按本局相邻日差 4 周期 (-3,+1,-2,+5)（28 个差值零例外）推得"},
}


def build_position_table(lines: list[str]) -> dict:
    """卷二五张安紫微图 → {局数: [初一…三十 的紫微宫支]}，并留原始格面。"""
    table: dict[int, list[str | None]] = {}
    raw: dict[str, dict[str, list[str]]] = {}
    for name, top in ZHI_GRID_TOP.items():
        cells: dict[str, list[str]] = {}
        for o1, o2 in GRID_BLOCKS:
            f1 = lines[top - 1 + o1].split("|")
            f2 = lines[top - 1 + o2].split("|")
            fb = lines[top - 1 + o2 + 2].split("|")
            for k in range(len(fb)):
                br = fb[k].strip()
                if br not in BRANCH:
                    continue
                cells[br] = [f1[k][x] + f2[k][x]
                             for x in range(min(len(f1[k]), len(f2[k])))
                             if f1[k][x].strip() and f2[k][x].strip()]
        raw[name] = cells
        ju = {"水二局": 2, "木三局": 3, "金四局": 4, "土五局": 5, "火六局": 6}[name]
        row: list[str | None] = [None] * 30
        for br in BRANCH:
            for day in cells.get(br, []):
                idx = CN_NUM.get(day)
                if idx is None or row[idx - 1] is not None:
                    continue
                row[idx - 1] = br
        for day, br in (GRID_DERIVED.get(name) or {}).items():
            if day in CN_NUM:
                row[CN_NUM[day] - 1] = br
        table[ju] = row
    return {"table": table, "raw": raw}


ANSHI_HEAD_RE = re.compile(r"^安[^，。；、：:]{1,20}诀")
# 诀与诀之间的其它短标签行（安命主/论××/定××…）也是块界。
# 判定用「结构」而非字面：原书这一节的标签行都很短（≤32 字），且要么含「诀」，
# 要么以 论/定/法曰 起首；正文行则是长句起例，首 20 字内不出现「诀」。
ANSHI_BOUNDARY_LEN = 32


def _is_anshi_boundary(text: str) -> bool:
    return len(text) <= ANSHI_BOUNDARY_LEN and (
        "诀" in text[:20] or text[:1] in "论定" or text.startswith("法曰"))


ANSHI_SKIP_RE = re.compile(r"^(<|\||-|\+)")


def build_anshi(lines: list[str], heads: list[tuple[int, int, str]]) -> dict:
    """卷二「安××诀」→ {诀名: {quote, 行号, location}}（逐字照录，含 <poem> 内文）。

    块界 = 下一个短标签行（诀名 / 安命主 / 论×× / 定×× …），空行透明
    ——原书此处每条正文行之间都夹空行，用空行断块会把一条诀切成半条。
    """
    start = None
    for ln, level, t in heads:
        if t.strip() in ("紫微斗数全书卷二", "紫微斗數全書卷二"):
            start = ln
            break
    if start is None:
        return {}
    end = len(lines)
    for ln, level, _ in heads:
        if ln > start and level <= 2:
            end = ln
            break
    out: dict[str, dict] = {}
    cur: str | None = None
    buf: list[str] = []
    head_line = 0

    def flush() -> None:
        if cur:
            quote = "".join(buf)
            if quote:
                out[cur] = {"quote": quote, "行号": head_line}

    for i in range(start, end):
        text = lines[i].strip().replace("'''", "").replace("<nowiki>", "").replace("</nowiki>", "")
        if not text:
            continue
        if _is_anshi_boundary(text):
            flush()
            if ANSHI_HEAD_RE.match(text):
                cur, buf, head_line = text, [], i + 1
            else:
                cur, buf = None, []
            continue
        if cur is None or "<poem>" in text or "</poem>" in text:
            continue
        body = strip_markup(text)
        if not body or ANSHI_SKIP_RE.match(body):
            continue
        buf.append(body)
        if len(buf) >= 12:                # 兜底：诀文不会有 12 行
            flush()
            cur = None
    flush()
    for name, v in out.items():
        v["location"] = f"{BOOK}卷二·{name}"
    return out


# ── 主流程 ─────────────────────────────────────────────────────────────────

def extract() -> dict:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    heads = headings(lines)
    ming_body = section_body(lines, heads, "一 命宫")
    segs2 = star_segments(ming_body)
    brightness, conflicts = build_brightness(segs2)
    return {
        "lines": len(lines), "bytes": SOURCE.stat().st_size,
        "segs1": answer_segments(lines, heads),
        "segs2": segs2,
        "brightness": brightness, "conflicts": conflicts,
        "companions": build_companions(segs2),
        "sihua": build_sihua(lines, heads),
        "geju": build_geju(lines, heads),
        "star_palace": build_star_palace(lines, heads, segs2),
        "anshi": build_anshi(lines, heads),
        "position": build_position_table(lines),
    }


def core_literal(brightness: dict) -> str:
    """把庙陷表排版成可直接粘贴进 core/ziwei_tables.py 的 Python 字面量。"""
    order = [s for s in ALL_STARS if s in brightness]
    lines = []
    for star in order:
        cells = brightness[star]
        items = ", ".join(f'"{br}": "{cells[br]["levels"][0]}"'
                          for br in BRANCH if br in cells)
        lines.append(f'    "{star}": {{{items}}},')
    return "STAR_BRIGHTNESS: dict[str, dict[str, str]] = {\n" + "\n".join(lines) + "\n}"


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="紫微斗数语料机械提取（只读原文，不改写）")
    ap.add_argument("--dry-run", action="store_true", help="只打印统计与抽样")
    ap.add_argument("--check", action="store_true",
                    help="不落盘，只比对已入库 data/*.json 是否与重算一致（防构建器与入库脱钩）")
    ap.add_argument("--emit-core", action="store_true",
                    help="打印 core/ziwei_tables.py 的 STAR_BRIGHTNESS 字面量")
    args = ap.parse_args()

    if not SOURCE.is_file():
        print(f"× 缺书源 {SOURCE}（先跑 python tools/fetch_source.py --fetch zi-wei-dou-shu-quan-shu）")
        return 2

    d = extract()
    s1, s2 = d["segs1"], d["segs2"]
    print(f"书源 {SOURCE.name}：{d['lines']} 行 / {d['bytes']} 字节")
    print(f"  卷一问答论主星段 {len(s1)} 星（期望 14）")
    print(f"  卷二命宫主星段   {len(s2)} 星（期望 14）")
    print(f"  庙陷明文 {sum(len(v) for v in d['brightness'].values())} 格"
          f"（{len(d['brightness'])} 星）｜冲突 {len(d['conflicts'])}")
    print(f"  同度明文 {sum(len(v) for v in d['companions'].values())} 格"
          f"（{len(d['companions'])} 星）")
    print(f"  四化释义 {len(d['sihua'])} 条（期望 4）")
    print(f"  格局判据 {len(d['geju'])} 条")
    print(f"  十二宫释义 {len(d['star_palace'])} 宫 / "
          f"{sum(len(v) for v in d['star_palace'].values())} 条星义")
    print(f"  安星诀 {len(d['anshi'])} 条")
    transcribed = sum(1 for row in d["position"]["table"].values() for x in row if x)
    print(f"  紫微定位表 5 局 / {transcribed} 格（含 2 格结构自洽推得）")

    # 自检：定位表必须与 core 的取值层逐格一致（两层同源）
    try:
        from yishu_core.ziwei_tables import ZIWEI_POS_TABLE  # noqa: E402
        mism = [(ju, i + 1, row[i], ZIWEI_POS_TABLE.get(ju, (None,) * 30)[i])
                for ju, row in d["position"]["table"].items()
                for i in range(30)
                if row[i] != ZIWEI_POS_TABLE.get(ju, (None,) * 30)[i]]
        print("  自检：定位表与 core 取值层一致" if not mism else f"  ! 定位表与 core 不一致 {mism[:5]}")
    except Exception as exc:  # noqa: BLE001
        print(f"  ! 无法比对 core 取值层：{exc}")

    # 自检：十四主星都必须有本宫诗（无诗=断段失败，宁可报错也不产出残缺语料）
    no_poem = [s for s in MAIN_STAR_ORDER if not (s2.get(s) or {}).get("poems")]
    print(f"  自检：十四主星缺本宫诗 {len(no_poem)} 个"
          + (f" → {no_poem}" if no_poem else " √"))
    no_nature = [s for s in MAIN_STAR_ORDER if not (s1.get(s) or {}).get("prose")]
    print(f"  自检：十四主星缺卷一问答论 {len(no_nature)} 个"
          + (f" → {no_nature}" if no_nature else " √"))
    # 辅煞星：卷一同篇有独立标题者（合并标题如「問天魁天鉞星」解析不出单星名 → 自动不入库，
    # 宁缺勿滥）。有 prose 才写，故打印只为可见性，不是失败项。
    aux_nature = [s for s in AUX_STARS if nature_quote(s1.get(s))]
    aux_only_song = [s for s in AUX_STARS
                     if (s1.get(s) or {}).get("prose") and not nature_quote(s1.get(s))]
    print(f"  自检：辅煞星卷一问答论入层 {len(aux_nature)} 个 → {aux_nature}"
          + (f"（仅歌诀未入层 {aux_only_song}）" if aux_only_song else ""))

    if args.emit_core:
        print()
        print(core_literal(d["brightness"]))
        return 0

    if args.dry_run:
        for star in ("紫微", "天机", "太阳", "破军"):
            print(f"  · {star} 庙陷：",
                  json.dumps(d["brightness"].get(star, {}), ensure_ascii=False)[:340])
        for star in ("紫微", "天府", "破军"):
            print(f"  · {star} 同度：",
                  json.dumps(d["companions"].get(star, {}), ensure_ascii=False)[:300])
        for c in d["conflicts"][:10]:
            print("  ! 冲突", c)
        print("  · 卷一紫微：", json.dumps(s1.get("紫微", {}), ensure_ascii=False)[:200])
        print("  · 化禄：", json.dumps(d["sihua"].get("禄", {}), ensure_ascii=False)[:180])
        for palace in ("命宫", "财帛", "夫妻", "官禄"):
            e = d["star_palace"].get(palace) or {}
            print(f"  · {palace} {len(e)} 条；紫微 →",
                  json.dumps(e.get("紫微", {}), ensure_ascii=False)[:180])
        for name in list(d["geju"])[:5]:
            print(f"  · 格局 {name}：", json.dumps(d["geju"][name], ensure_ascii=False)[:140])
        return 0

    meta = {
        "所本": f"{BOOK}（明·羅洪先）通行本，维基文库公版",
        "来源文件": "data/sources/zi-wei-dou-shu-quan-shu.wikitext.txt",
        "提取方式": "dev_tools/build_corpus.py 字符级提取（不改写、不做简繁转写）",
        "口径": "原文照录；星名键用简体规范名（引擎口径），引文照录原文；未明写的格不填",
    }
    files = {
        "star_nature.json": {
            "_meta": {**meta,
                      "说明": "星曜性情说解（卷一諸星問答論希夷先生答语）：十四主星 + "
                              "凡同篇有独立标题的辅煞星；合并标题（如問天魁天鉞）不拆，宁缺勿滥"},
            "stars": {s: {"quote": nature_quote(s1.get(s)),
                          "location": f"{BOOK}卷一·諸星問答論·問{s}所主若何"}
                      for s in list(MAIN_STAR_ORDER) + AUX_STARS
                      if nature_quote(s1.get(s))},
        },
        "star_palace.json": {
            "_meta": {**meta, "说明": "十二宫诸星释义（卷二逐星逐宫照录）"},
            "palaces": d["star_palace"],
        },
        "star_brightness.json": {
            "_meta": {**meta,
                      "说明": "星曜庙陷引文层（星×宫支，只收原文明文）；取值层在 "
                              "core/yishu_core/ziwei_tables.py:STAR_BRIGHTNESS，两层同源"},
            "table": d["brightness"],
            "companions": {
                "说明": "星×宫支→同度主星（原文「X同度」明文，「与」字可省——书源 L2232 "
                        "一行即省「与」，故不要求该字）。格数不写死：由 "
                        "dev_tools/regression.py 运行时算出并在 B1 打印（唯一权威读数）",
                "table": d["companions"],
            },
        },
        "sihua_quotes.json": {
            "_meta": {**meta, "说明": "四化释义逐字引文（卷一希夷先生答语）"},
            "hua": d["sihua"],
        },
        "geju_rules.json": {
            "_meta": {**meta,
                      "说明": "定富局/定贵局/定贫贱局/定杂局判据（卷一）；"
                              "analyze 只机械判定其中可判者，其余仅作文献保留"},
            "rules": d["geju"],
        },
        "anshi_quotes.json": {
            "_meta": {**meta,
                      "说明": "卷二各「安××诀」逐字原文（禄存/羊陀/火铃/天马/空劫/"
                              "刑姚/哭虚/龙池凤阁/三台八座/台辅封诰/魁钺/辅弼/昌曲/四化），"
                              "引擎各安星函数的所本"},
            "rules": d["anshi"],
        },
        "ziwei_position_table.json": {
            "_meta": {**meta,
                      "说明": "紫微定位（五行局 × 农历日 → 紫微宫支）引文层："
                              "书源卷二五张安紫微图的原始格面 + 机械解码结果；"
                              "取值层在 core/yishu_core/ziwei_tables.py:ZIWEI_POS_TABLE，两层同源"},
            "raw_grid": {k: v for k, v in d["position"]["raw"].items()},
            "table": {str(ju): [x or "" for x in row]
                      for ju, row in d["position"]["table"].items()},
            "derived_cells": GRID_DERIVED,
            "body_example": {
                "quote": "如甲生人安命在寅却起甲己之年丙为首，是丙寅丁卯炉中火，"
                         "却去火局寻某日生期起紫微帝王，如是正月初一生者是火局，"
                         "酉宫起初一日，就从酉宫起紫微，数无差迟，"
                         "若错了则失之毫厘，差之千里矣。",
                "location": f"{BOOK}卷二·安身命例",
                "行号": 1666,
            },
        },
    }
    if args.check:
        bad = 0
        for name, payload in files.items():
            bad += corpus_kit.report(name, corpus_kit.check(DISC / "data" / name, payload))
        return 1 if bad else 0
    for name, payload in files.items():
        path = DISC / "data" / name
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
        print(f"  写出 {path.relative_to(ROOT)}（{path.stat().st_size} 字节）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
