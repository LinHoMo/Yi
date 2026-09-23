# -*- coding: utf-8 -*-
"""从维基文库《增刪卜易》原本抓取占验案例，本地确定性解析并三方校验后成外部集。

    python tools/fetch_wikisource_cases.py            # 下载＋解析＋校验＋落盘
    python tools/fetch_wikisource_cases.py --no-fetch # 用已缓存原文重跑解析
    python tools/fetch_wikisource_cases.py --report   # 只看校验统计，不落盘
    python tools/fetch_wikisource_cases.py --report --show 8   # 附带前 8 条剔除样本

为什么走"原文＋本地解析"而不是让模型读一遍再抄：
  本仓库现有 `references/case_library.md` 有 29 例，其中 14 例"文记动爻"与卦变差集矛盾
  （见 docs/CASE-LIBRARY-AUDIT.md）——那种矛盾正是"模型转写古籍"的典型产物。
  转写会造出自洽性失败的假案例，而假案例比没有案例更坏。所以这里全程只做
  **字符级解析 + 与引擎独立比对**，不引入任何语言模型的转写。

原文是繁体清代刻本，故卦名/世应/動變都需先做字头归一（TRAD）；归一表只覆盖
六十四卦与六亲会用到的字，不做通用繁简转换——通用转换会把"未濟"这类卦名改坏。

三方校验（任一不过即弃，并记原因）：
  V1 纳甲：原文每爻写的地支，必须与内核按该卦推出的纳甲一致；
  V2 卦变：○/ㄨ 标出的动爻位次，必须等于 本卦⊕變卦 的差集；
  V3 世应：原文标的世/应位置，必须与内核八宫世应一致。
能通过 V1–V3 的案例，说明"卦装对了"；再要求应验句含可检验干支，才进外部集。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
from kernel_path import ensure_kernel_on_path  # noqa: E402

ensure_kernel_on_path(__file__)
from yishu_core import symbols as sym                            # noqa: E402
from yishu_core.najia import najia_branch, response_position    # noqa: E402

API = "https://zh.wikisource.org/w/api.php"
PAGE = "增刪卜易"
SOURCES = DISC.parent.parent / "data" / "sources"
RAW = SOURCES / "zengshan_buyi.wikitext.txt"
PROV = SOURCES / "zengshan_buyi.provenance.json"
OUT = DISC / "data" / "cases" / "wikisource_cases.json"
SPLITS = DISC / "data" / "cases" / "case_splits.json"

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

# 繁体字头 → 内核（简体）卦名用字。只列六十四卦、八卦前缀与世应/動變会碰到的字。
TRAD = {
    "兌": "兑", "離": "离", "剝": "剥", "蠱": "蛊", "恆": "恒", "歸": "归",
    "無": "无", "晉": "晋", "賁": "贲", "頤": "颐", "豐": "丰", "澤": "泽",
    "風": "风", "臨": "临", "渙": "涣", "漸": "渐", "師": "师", "損": "损",
    "節": "节", "訟": "讼", "謙": "谦", "隨": "随", "壯": "壮", "過": "过",
    "復": "复", "觀": "观", "暌": "睽", "旣": "既", "卽": "即", "濟": "济",
}
# 卦象前缀（天地風雷水火山泽）——四字卦名如"火天同人"要去掉前缀才对上内核名
TRI_CHARS = set("天地風雷水火山泽泽震巽乾坤坎离艮兑")

# 引例头：〔月建〕〔日辰〕+ 占问 + 得 本卦〔之/變/化 变卦〕
# 古籍写"革之夬""家人變益""噬嗑化屯"，也写"澤天夬卦變大壯"（變字在卦字之后）。
# 卦名里绝不会出现"之變化得"，故把它们排除在名字之外；量词取贪婪，
# 否则 lazy 会把"恆之大過"截成"大"（变卦名少一字 → 认不出卦 → 白丢一例）。
_EXCL = r"，,。；;：:？?、\s　卦得之變变化"
_NAME = r"(?P<orig>[^" + _EXCL + r"]{1,6})"
_TAIL = r"(?P<chg>[^" + _EXCL + r"]{1,4})"
_TAIL2 = r"(?P<chg2>[^" + _EXCL + r"]{1,4})"
# 必须见"卦"字或见變卦标记，才认定这是个引例头：
# 放开后"得此""得山火"一类碎句会被认成头，头图错配 → 六爻纳甲全不合（实测 3 例假阳）。
_CHG = r"(?:[之變变化]\s*" + _TAIL + r"卦?|卦(?:[之變变化]\s*" + _TAIL2 + r")?)"
HEAD = re.compile(
    r"(?:于|於)?(?P<month>[" + BRANCHES + r"])月\s*(?P<day>[" + STEMS + r"]?[" + BRANCHES + r"])日"
    r"(?P<q>[^。\n]{0,40}?)得\s*" + _NAME + _CHG)
# 无月建的头（"戊戌日占…"式）
HEAD_NO_MONTH = re.compile(
    r"(?P<day>[" + STEMS + r"][" + BRANCHES + r"])日"
    r"(?P<q>[^。\n]{0,40}?)得\s*" + _NAME + _CHG)

_REL = r"(兄弟|妻財|財|官鬼|父母|子孫)"
_MARK = r"([⚊⚋○ㄨ×⚍]?)"
_ITEM = (_REL + r"\s*([" + BRANCHES + r"])([金木水火土])" + _MARK + r"\s*(世|應)?")
LINE_ITEM = re.compile(_ITEM)
ROW_FULL = re.compile(r"^\s*" + _ITEM + r"(?:[\s　]+" + _ITEM + r")?\s*$")
YINGQI = re.compile(r"[甲乙丙丁戊己庚辛壬癸]?[" + BRANCHES + r"](日|月|年)")
# 锚定期：應/果/期/驗 后面（允许两三字赘词）直接跟"（干）支+日/月/年"。
# 只认这一种形态，是为了把"所以然"句里的支排除掉——见 _yingqi_of 的注释。
YINGQI_ANCHORED = re.compile(
    r"(?P<a>[應果期驗]).{0,3}?[甲乙丙丁戊己庚辛壬癸]?(?P<b>[" + BRANCHES + r"])(?P<u>[日月年])")
# 应验句锚点。古籍用 ﹐（异体逗号）断句，"，果於X日"是最常见的写法，
# 只认"。果"会漏掉一大半（实测 21 例）。文言的"後果"是"后来果然"，不是名词"后果"，
# 早先我把它当现代词整段挖掉，等于把真验句删了——故这里 此?後?果 都要接住。
OUTCOME_ANCHOR = re.compile(r"(?:此?後?果|其驗|驗得|應驗).{0,44}")
GOOD_WORDS = ("愈", "到", "至", "遂", "中举", "中試", "得選", "获選", "安", "晴",
              "吉", "生", "归", "來", "返回", "起用", "升")
BAD_WORDS = ("死", "卒", "亡", "敗", "凶", "獄", "革職", "降級", "耗", "失",
             "絕", "病重", "不成", "無成", "杖", "絞")
# 词条只留原文里真的存在的字（用 `--report` 的覆盖体检核过）：
# 上面那批简化字在本源出现 0 次，留着只会让人以为"两边都照顾到了"。
GOOD_WORDS += ("得", "中")
# 古籍点用神的三种写法："以父母爲用"、"父母爲用神"、"妻占夫官爲用神"。
# 这一维原来一律抽不到 → 37 例全记 N/A，等于放过了 M2.1 最该被测的地方。
USE_GOD = re.compile(r"(?:以\s*)?(兄弟|妻財|財|官鬼|父母|子孫)(?:爻)?\s*(?:為|爲|为)\s*用神?")
# 单字省写："妻占夫官爲用神""占伯父父母爲用"——古籍点用神常只写一字
USE_GOD_SHORT = re.compile(r"(父|兄|財|官|子|孫)(?:爻)?\s*(?:為|爲|为)\s*用神?")
ONE_CHAR_GOD = {"父": "父母", "兄": "兄弟", "財": "妻财", "官": "官鬼", "子": "子孙", "孫": "子孙"}


# 异体字归一（整书一次，作用于所有下游正则）。
# 教训：刻本通篇用 爲(U+7232)，而我写的是 為(U+70BA)/为——
# 结果 "以父母爲用神" 一条都没抽到，用神维 37 例全记 N/A 却看起来"正常"。
# 只统计不合数、不统计比对分母的话，这种漏是发现不了的。
VARIANTS = str.maketrans({"爲": "為"})   # 只做等长替换：偏移量要对得上原文


def norm_text(raw: str) -> str:
    out = raw.translate(VARIANTS)
    assert len(out) == len(raw), "异体字归一改变了长度，provenance 偏移量会失准"
    return out


def fetch_raw() -> str:
    url = API + "?" + urllib.parse.urlencode(
        {"action": "parse", "format": "json", "prop": "wikitext", "page": PAGE, "redirects": "1"})
    req = urllib.request.Request(url, headers={"User-Agent": "Yi-research/0.0.1 (case data acquisition)"})
    data = json.loads(urllib.request.urlopen(req, timeout=90).read().decode("utf-8"))
    return data["parse"]["wikitext"]["*"]


def norm(name: str) -> str:
    return "".join(TRAD.get(c, c) for c in (name or ""))


def resolve_hex(name: str) -> str | None:
    """原文卦名 → 内核卦名。先去繁简，再剥"火天/澤天"式卦象前缀。"""
    n = norm(name).strip()
    if n in sym.HEXAGRAM_TRIGRAMS:
        return n
    for cut in (1, 2):
        if len(n) > cut:
            tail = n[cut:]
            if tail in sym.HEXAGRAM_TRIGRAMS and all(c in TRI_CHARS for c in n[:cut]):
                return tail
    return None


def hex_lines(name: str) -> list[int] | None:
    tri = sym.HEXAGRAM_TRIGRAMS.get(name)
    if not tri:
        return None
    upper, lower = tri
    return sym.BAGUA_LINES[lower] + sym.BAGUA_LINES[upper]


def palace_of(name: str):
    """(宫名, 世代, 世爻位)；世爻位 0 表示本宫首卦（无世爻标记）。"""
    for palace, data in sym.EIGHT_PALACES.items():
        for hx, gen in data["order"]:
            if hx == name:
                pos = {"一世": 1, "二世": 2, "三世": 3, "四世": 4, "五世": 5,
                       "游魂": 4, "归魂": 3}.get(gen, 0)
                return palace, gen, pos
    return None


def parse_row(seg: str) -> list[dict] | None:
    """一行的 1~2 列爻（左＝本卦，右＝變卦）。不整行匹配则返回 None。"""
    m = ROW_FULL.match(seg.strip())
    if not m:
        return None
    g = m.groups()
    out = []
    for base in (g[0:5], g[5:10]):
        if not base or not base[0]:
            continue
        rel, br, elem, mark, shi = base
        out.append({"six_relation": norm_rel(rel), "branch": br, "element": elem,
                    "mark": mark or "", "shiyao": shi or ""})
    return out


def norm_rel(rel: str) -> str:
    rel = "妻財" if rel.startswith("兄弟姐") else rel
    return "妻财" if rel == "妻財" else ("子孙" if rel == "子孫" else rel)


def find_diagrams(segments: list[tuple[int, str]]) -> list[dict]:
    """把 <br> 分段扫成爻图块。

    块 = 连续 6 行、每行列数一致（1 列＝静卦全图，2 列＝本卦+變卦并排）。
    两段爻图之间若无正文（run 长 12 等），按 6 行一节切开。
    """
    parsed = {}
    for idx, (_off, seg) in enumerate(segments):
        rows = parse_row(seg)
        if rows:
            parsed[idx] = rows
    keys = sorted(parsed)
    blocks, k = [], 0
    while k < len(keys):
        run = [keys[k]]
        j = k + 1
        while j < len(keys) and keys[j] == run[-1] + 1 and \
                len(parsed[keys[j]]) == len(parsed[run[0]]):
            run.append(keys[j])
            j += 1
        for s in range(0, len(run) - 5, 6):
            take = run[s:s + 6]
            blocks.append({"start": take[0], "end": take[-1],
                           "rows": [parsed[i] for i in take],
                           "cols": len(parsed[take[0]])})
        k = j
    return blocks


def diagram_items(block: dict, col: int) -> list[dict]:
    """块内某一列的六爻，自上爻往下 → 转成自下而上，附位次。"""
    items = []
    for r, row in enumerate(block["rows"], start=1):
        if col < len(row):
            it = dict(row[col])
            it["top_down"] = r
            items.append(it)
    items.reverse()
    for i, it in enumerate(items, start=1):
        it["position"] = i
    return items


# 正文边界。维基文库本里卷首/卷尾夹着纳甲诀、安世应要领这类韵文附录（<poem> 块、
# "=== 章 ===" 标题），爻图后若无边界就会一路读进附录——
# 结果"占升遷"的用神被从附录里抓成"父母"（正解是官鬼），基准反而是错的。
SECTION_CUT = re.compile(r"===|<poem>|</poem>|卷之[一二三四五六七八九十]|章第[一二三四五六七八九十百]+")


def _clip(text: str, limit: int = 600) -> str:
    m = SECTION_CUT.search(text)
    if m:
        text = text[:m.start()]
    return text[:limit]


def outcome_of(text: str, verdict_zone: str = "") -> tuple[str | None, str | None, str, str]:
    """取 (吉凶, 应验干支, 用神六亲, 原句)。

    应验只认验句里写明"（干）支 + 日/月/年"的期；"次日""次年""七月"这类相对
    或数字表述不可与引擎输出比对，一律不算命中。同一级里出现两个不同应支时也弃
    ——分不清哪个是验期，留着只是给引擎一个假的对照。
    吉凶按验句里的 outcome 词判（愈／到／中試 对 死／敗／下獄）；
    两向词同现即判为不明，返回 None，调用方据此不入六维评分集。
    """
    clause = ""
    text = text.replace("後果", "後 果").replace("后果", "后 果")   # 别让"後果"两字被当一词跳过
    for pat in (OUTCOME_ANCHOR, re.compile(r"應[^。\n]{0,34}")):
        # 逐锚点试，取第一个能给出可检应期的：先出现的"果﹐…"若是按语的果，
        # 后面那句"果於X日"才是验句。
        for mm in pat.finditer(text):
            clause = mm.group(0)
            if _yingqi_of(clause):
                break
    yq = _yingqi_of(clause)
    good = any(k in clause for k in GOOD_WORDS)
    bad = any(k in clause for k in BAD_WORDS)
    verdict = "吉" if good and not bad else ("凶" if bad and not good else None)
    ug = USE_GOD.search(text) or USE_GOD_SHORT.search(text)
    use_god = ""
    if ug:
        g = ug.group(1)
        use_god = ONE_CHAR_GOD.get(g, norm_rel(g))
    return verdict, yq, use_god, clause.strip()[:160]


def _yingqi_of(clause: str) -> str | None:
    """取书自己**写在锚词后面**的那一期：「應X日者」「果於X日到」「期在X日」。

    早先的实现是"整句里扫（干）支+日/月/年，日级优先"，结果把机制句当成了答案：
      「應未月者﹐土爻未土乃世爻之墓﹐**丑日**沖開」→ 抽成"丑日"（书答的是未月）
      「應**子年**者﹐占時原有**子日**沖其午火」→ 抽成"子日"
    两句都是"应期 + 所以然"的结构，所以然里的支不是应期。改成锚定抽取后：
    只认紧跟應/果/期/驗（可带"于、在、得、結"等两三字赘字）的那一期；
    同一句出现两个不一致的锚定期即判不可检。数字月（"七月"）与相对期
    （"次日""次年"）要靠"夏正建寅"这类读法换算，读错就是给引擎假对照，不接。
    """
    found = [(h.group("b") + h.group("u")) for h in YINGQI_ANCHORED.finditer(clause)
             if h.group("u") in ("日", "月", "年")]
    uniq = sorted(set(found))
    return uniq[0] if len(uniq) == 1 else None


def main() -> int:
    from yishu_core.runtime import force_utf8_stdio
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="抓取并解析《增刪卜易》原本占验")
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--show", type=int, default=0, help="报告里附带多少条剔除样本")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    SOURCES.mkdir(parents=True, exist_ok=True)
    if args.no_fetch and RAW.exists():
        raw = RAW.read_text(encoding="utf-8")
    else:
        raw = fetch_raw()
        RAW.write_text(raw, encoding="utf-8")
        PROV.write_text(json.dumps({
            "work": "增刪卜易（清·野鶴老人 著，李文輝 等編）",
            "source": "维基文库 zh.wikisource.org",
            "page": PAGE, "api": API,
            "retrieved": date.today().isoformat(),
            "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            "license": "原作清代，公有领域；转录本依维基文库授权条款",
            "chars": len(raw),
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"已下载 {len(raw)} 字 → {RAW.name}（sha256 见 provenance）")

    raw = norm_text(raw)      # sha256 记的是未归一的原文，偏移量记归一后的（等长，故一致）
    offsets, segs = [], []
    pos = 0
    for piece in raw.split("<br>"):
        offsets.append(pos)
        segs.append(piece)
        pos += len(piece) + len("<br>")
    segments = list(zip(offsets, segs))

    blocks = find_diagrams(segments)
    row_idx = {i for i, (_o, s) in enumerate(segments) if parse_row(s)}
    heads = {m.start() for pat in (HEAD, HEAD_NO_MONTH) for m in pat.finditer(raw)}
    print(f"爻图块 {len(blocks)} 个；引例头 {len(heads)} 处")

    kept, dropped = [], []
    stats = {"no_head": 0, "bad_hex_name": 0, "no_day": 0, "no_month": 0, "few_lines": 0,
             "validate_fail": 0, "no_yingqi": 0, "dup": 0}
    partial = {"verdict_missing": 0}   # 仍可评应期，只是缺吉凶对照
    cov: dict[str, int] = {}          # 比对分母：不合是 0 还得说清比了多少
    def bump(key: str) -> None:
        cov[key] = cov.get(key, 0) + 1
    v1 = v2 = v3 = 0
    seen = set()
    prev_end = -1

    for bi, blk in enumerate(blocks):
        # 引例头在图之前、应验句在图之后；两段都不含爻图行
        before = "".join(segments[i][1] for i in range(prev_end + 1, blk["start"])
                         if i not in row_idx)
        prev_end = blk["end"]
        head = None
        for pat in (HEAD, HEAD_NO_MONTH):
            for mm in pat.finditer(before):
                # 同一条头会被两个式子各命中一次：带月建的那个起点更早、终点相同，
                # 必须选它，否则 input.date 只剩"月丁卯日"，月令丢失 → 旺衰无据。
                if not head or (mm.end(), -mm.start()) > (head[0].end(), -head[0].start()):
                    head = (mm, pat)
        if not head:
            stats["no_head"] += 1
            dropped.append((blk["start"], "no_head", ""))
            continue
        m, pat = head
        month_branch = m.groupdict().get("month") or ""
        day_gz, q = m.group("day"), m.group("q")
        orig_raw, chg_raw = m.group("orig"), m.groupdict().get("chg")
        chg_raw = chg_raw or m.groupdict().get("chg2")
        orig, changed = resolve_hex(orig_raw), resolve_hex(chg_raw) if chg_raw else None
        if chg_raw and not changed:
            stats["bad_hex_name"] += 1
            dropped.append((blk["start"], "bad_hex_name", f"{orig_raw}之{chg_raw}"))
            continue
        if not orig:
            stats["bad_hex_name"] += 1
            dropped.append((blk["start"], "bad_hex_name", str(orig_raw)))
            continue
        if not day_gz or len(day_gz) < 2:
            stats["no_day"] += 1
            continue
        if not month_branch:
            # 月建缺失时引擎的月破/旺衰全无所据，评出来的分不是引擎的分
            stats["no_month"] += 1
            dropped.append((blk["start"], "no_month", m.group(0)[:40]))
            continue

        base = hex_lines(orig)
        diagram = diagram_items(blk, 0)
        if len(diagram) != 6 or not base:
            stats["few_lines"] += 1
            dropped.append((blk["start"], "few_lines", f"{len(diagram)} 爻"))
            continue

        problems, info = [], {}
        for it in diagram:
            want = najia_branch(orig, it["position"])
            if want:
                bump("纳甲比对(爻)")
                if it["branch"] != want:
                    problems.append(f"V1 纳甲 {it['position']}爻 原文{it['branch']} 内核{want}")
                    v1 += 1
        marks = {it["position"] for it in diagram if it["mark"] in ("○", "ㄨ", "×")}
        if changed:
            chg = hex_lines(changed)
            diff = {i + 1 for i, (a, b) in enumerate(zip(base, chg)) if a != b}
            if marks:
                bump("卦变比对(例)")
            if marks and marks != diff:
                problems.append(f"V2 卦变 ○ㄨ{sorted(marks)} ≠ 差集{sorted(diff)}")
                v2 += 1
            info["moving"] = sorted(marks or diff)
        else:
            if marks:
                problems.append(f"V2 无變卦却标动爻 {sorted(marks)}")
                v2 += 1
            info["moving"] = []
        pal = palace_of(orig)
        if pal:
            palace, gen, world = pal
            info["palace"], info["generation"] = palace, gen
            tw = {it["position"] for it in diagram if it["shiyao"] == "世"}
            tr = {it["position"] for it in diagram if it["shiyao"] == "應"}
            if world:
                want_resp = response_position(world)
                if tw:
                    bump("世位比对(例)")
                if tr:
                    bump("应位比对(例)")
                if tw and world not in tw:
                    problems.append(f"V3 世位 原文{sorted(tw)} 内核{world}")
                    v3 += 1
                if tr and want_resp not in tr:
                    problems.append(f"V3 应位 原文{sorted(tr)} 内核{want_resp}")
                    v3 += 1
        if problems:
            stats["validate_fail"] += 1
            dropped.append((blk["start"], "validate_fail", "；".join(problems)))
            if not args.report:
                continue

        after_idx = blk["end"] + 1
        nxt = blocks[bi + 1]["start"] if bi + 1 < len(blocks) else len(segments)
        after = "".join(segments[i][1] for i in range(after_idx, min(nxt, len(segments)))
                        if i not in row_idx)
        # 本例正文止于"下一个引例头"。用定长窗口截断，既会砍掉自己的验句，
        # 更坏的是可能把下一例的验句当本例的——那是假基准，不是缺基准。
        cut = len(after)
        for pat in (HEAD, HEAD_NO_MONTH):
            mm = pat.search(after)
            if mm and mm.start() < cut:
                cut = mm.start()
        after = _clip(after[:max(cut, 0)])
        # 用神只在"断语区"里找（图后到第一个验句之前）。
        # 整段扫会一路读进卷首的纳甲诀，"占升遷"因此被抓成"父母"（正解官鬼）——
        # 基准错比基准缺更坏：它会把引擎判成"错"。
        duan = re.split(r"[。，,﹐]?果|其驗|後果", after)[0][:220]
        verdict, yq, _ig, clause = outcome_of(m.group(0) + after)
        _, _, use_god, _ = outcome_of(duan, verdict_zone=duan)
        if not yq:
            stats["no_yingqi"] += 1
            dropped.append((blk["start"], "no_yingqi", clause))
            continue
        if not verdict:
            # 没有明确吉凶不等于坏案例：应期判别力只看应支名次，不看吉凶。
            # 这类例照样入集，只是 expected.verdict=null，评分器该维记 N/A（见 evaluate.py）。
            partial["verdict_missing"] += 1
        # 用神之支/位从原文爻图里取（唯一一处该六亲出现时才取，多现则留给引擎判）：
        # 古籍对"用神多现"是舍旺弃衰，逐例另断，这里硬取一个反而是假基准。
        ug_br, ug_pos = "", ""
        same = [it for it in diagram if it["six_relation"] == use_god] if use_god else []
        if len(same) == 1:
            ug_br, ug_pos = same[0]["branch"], same[0]["position"]
        key = (orig, changed, month_branch, day_gz, yq)
        if key in seen:
            stats["dup"] += 1
            continue
        seen.add(key)
        kept.append({
            "id": f"WS{len(kept) + 1:03d}",
            "source": "《增刪卜易》（维基文库原本）",
            "topic": (q or "占事").strip()[:24],
            "question": (q or "").strip() or f"占{orig}卦事",
            "input": {"date": f"{month_branch}月{day_gz}日",
                      "question": (q or "").strip()},
            "hexagram": {"original": orig, "changed": changed,
                         "moving": info.get("moving") or [],
                         "palace": info.get("palace", ""),
                         "generation": info.get("generation", "")},
            "expected": {"verdict": verdict, "use_god": use_god,
                         "use_god_branch": ug_br, "use_god_position": ug_pos,
                         "yingqi": yq,
                         "yingqi_branches": sorted({yq[0]}), "detail": clause},
            "provenance": {"page": PAGE,
                           "sha256_head": hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12],
                           "offset": blk["start"], "wikitext_head": m.group(0)[:80]},
        })
        if args.limit and len(kept) >= args.limit:
            break

    print(f"\n校验统计：纳甲不合 {v1} 处、卦变不合 {v2} 处、世应不合 {v3} 处")
    print("比对分母：" + json.dumps(cov, ensure_ascii=False))
    print("剔除计数：" + json.dumps(stats, ensure_ascii=False))
    print("入集但缺对照：" + json.dumps(partial, ensure_ascii=False))
    print(f"可入外部集 {len(kept)} 例")
    # 字段覆盖也要报数：某关键字只写了另一种异体（爲/為），抽取会静默全空，
    # 报表上却像"这一维没测到"而不是"这个模式根本匹配不上"。
    filled = {f: sum(1 for c in kept if c["expected"].get(f))
              for f in ("use_god", "use_god_branch", "verdict", "yingqi")}
    print("字段覆盖：" + json.dumps(filled, ensure_ascii=False))
    anchors = {k: raw.count(k) for k in ("為用", "用神", "果", "應", "世", "○", "ㄨ")}
    print("源文本锚点计数：" + json.dumps(anchors, ensure_ascii=False)
          + "（某项为 0 而正则依赖它＝静默漏抽，先查用字是否与刻本一致）")
    if args.show:
        by_reason: dict[str, list] = {}
        for off, r, why in dropped:
            by_reason.setdefault(r, []).append((off, why))
        for r, lst in by_reason.items():
            print(f"\n-- {r}（{len(lst)}）")
            for off, why in lst[:args.show]:
                print(f"   @{off:<7d} {why}")
    if args.report:
        return 0

    OUT.write_text(json.dumps({
        "_meta": {
            "description": "《增刪卜易》维基文库原本自动解析的占验案例；通过纳甲/卦变/世应三方校验",
            "built_by": "tools/fetch_wikisource_cases.py",
            "retrieved": json.loads(PROV.read_text(encoding="utf-8"))["retrieved"] if PROV.exists() else "",
            "sha256": json.loads(PROV.read_text(encoding="utf-8"))["sha256"] if PROV.exists() else "",
            "total_cases": len(kept),
            "usage": "永不参与调参的外部验证集；评分前请先看 expected 是否需人工复核",
            "dropped": stats,
            "partial": partial,
        },
        "cases": kept}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写入 {OUT.relative_to(DISC.parent.parent)}")

    sp = json.loads(SPLITS.read_text(encoding="utf-8")) if SPLITS.exists() else {}
    sp["wikisource_holdout"] = [c["id"] for c in kept]
    SPLITS.write_text(json.dumps(sp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("case_splits.json 已登记 wikisource_holdout")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
