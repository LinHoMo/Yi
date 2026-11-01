# -*- coding: utf-8 -*-
"""八字科案例引文逐字性门（[41]，第四百三十批恢复；前身是扁平化前已删除的旧案例引文门）。

为什么恢复：扁平化（commit `e2c77ad`）删除了旧的 `tools/` 案例引文门与 `check.py [1k]`，
但 `bazi_external_cases.json` 的 `_provenance` 仍写着旧路径上线——登记成了假事实
（§六.2），同时 464 条 `source_quote` 没有任何常设门。

本门守什么：
  A. `source_quote`（自称照录的书源句）必须是该书底本的归一化连续子串；
  B. 书源路由优先 `book`（BOOK_SOURCES），其次案例 `provenance.file`；
     两者都没有且书在 UNROUTABLE_BOOKS → 逐条披露、不判红（有数、可见）；
  C. `case_quote_exempt.json` 登记的「夹注段/跨段摘录不在库内连续子串」逐条豁免；
     若豁免项的引文后来能在底本连续命中 → 判红（豁免过期，必须回接）；
     每条豁免同时报**最长连续块**（432 批），让「不在库」是实测数而不是一句声明；
  C2. 多底本（如《子平真诠评注》＝dz 本＋《命理探原》第二底本）逐本比对：
     只在第二底本命中、主底本不含 → `wrongbook` 判红（434 批；拼成一串时看不见）；
  C3. 豁免项的四柱/已登记专名一旦在底本出现 → `exempt_bad` 判红
     （436 批四柱、437 批专名）：「不在库」不能只靠自述；泛称（某侍郎/某知府）
     与无专名项不做人名机械判，见 `case_quote_exempt.json` 的 `_case_names_note`；
  C4. 豁免册自身一致性（446 批）：`case_names` 的 key 必须在 `ids` 内（否则那组专名
     永远不会被核对）；`ids` 中无专名的项必须在 `_case_names_note` 显式披露；
     专名值必须是非空字符串列表。

  D. 下限守卫：含引文文件数、引文总数、逐字比对数低于登记基线即判红
     （0 结果 ≠ 通过；路径挪动/解析失败必须先显形）。

  E. 案例目录 tests 指针可达（459 批）：`data/cases/*.json` 的正文不受 [11] 扫描
     （[11] 因案例正文含书文而整目录跳过），于是「回验由 tests/…承担」这类幽灵测试
     指针在四份案例/裁决文件里长期无人抓。本门逐行抓 `tests/*.py` 并解析（学科根/
     仓库根/同名文件），不可达即判红；显式病史行（从未存在等）豁免。

    python dev_tools/check_case_quotes.py            # 全量对拍
    python dev_tools/check_case_quotes.py --selftest # 正负例自证
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DISC = Path(__file__).resolve().parents[1]
ROOT = DISC.parent
CASE_DIR = DISC / "data" / "cases"
SRC_DIR = DISC / "data" / "sources"
EXEMPT = DISC / "data" / "rules" / "case_quote_exempt.json"

# 459 批：案例目录里的 `tests/` 指针必须可达——[11] 因案例正文含书文而不扫
# `data/cases/`，四份案例/裁决文件的「回验由 tests/…承担」幽灵指针长期无人抓。
# 459 批修：原 `(?:^|/)tests/` 在整行 finditer 时，`tests/` 前面是空格（「回验由 tests/…」），
# 两个锚点都不成立→永不命中（--selftest 的负例自证当场抓到）。改为「前面不是 ASCII 词字符/点/反斜杠」。
TEST_PTR = re.compile(r"(?<![A-Za-z0-9_.\\])tests/[A-Za-z0-9_\-./\\\u4e00-\u9fff]*\.py")
STRONG_HISTORY = re.compile(r"从未存在|全仓不存在|该文件不存在|该测试文件|全历史\s*0\s*命中"
                            r"|已随扁平化消失|从未重建|现已不存在|已不存在")


def _resolves(rel: str) -> bool:
    clean = rel.lstrip("./")
    for base in (DISC, ROOT):
        if (base / clean).exists():
            return True
    return any(p.name == Path(clean).name for p in DISC.rglob(Path(clean).name) if p.is_file())


def pointer_problems(text: str, rel: str) -> list[str]:
    """案例文件里的 tests 指针：必须可达；显式病史行（标注“不存在”）豁免。"""
    out: list[str] = []
    for n, line in enumerate(text.splitlines(), 1):
        if STRONG_HISTORY.search(line):
            continue
        for m in TEST_PTR.finditer(line):
            ref = m.group(0).lstrip("/")
            if not _resolves(ref):
                out.append(f"{rel}:{n} tests 指针不可达 → {ref}")
    return out

# book → 底本（相对 DISC）。新增引用书源时在此登记；未登记且无 provenance.file 即判红。
BOOK_SOURCES = {
    "穷通宝鉴": ["data/sources/qiong-tong-bao-jian.wikitext.txt"],
    "滴天髓阐微": ["data/sources/di-tian-sui-chan-wei.wikitext.txt"],
    "神峰通考": ["data/sources/shen-feng-tong-kao.wikitext.txt"],
    "渊海子平": ["data/sources/yuan-hai-zi-ping.wikitext.txt"],
    "千里命稿": ["data/sources/qianli_minggao_dz.dz.txt"],
    # 第一项为主底本（必须命中）；命理探原作第二底本只用于对照：
    # 只在第二底本命中 → wrongbook 判红（434 批；旧版把两本拼成一串，分辨不出）。
    "子平真诠评注": ["data/sources/ziping_zhenquan_pingzhu_dz.dz.txt",
                     "data/sources/mingli_tanyuan_dz.dz.txt"],
}

# 书源不在库（本仓 data/sources 无该书）：逐条披露，不判红。
UNROUTABLE_BOOKS = {
    "珞琭子三命消息赋注": "书源不在库（Wikisource 在线转录；data/sources 无该书）",
    "命理约言": "书源不在库（data/sources 无该书）",
    "袁氏命谱": "书源不在库（data/sources 无该书）",
}

MARKUP_RE = re.compile(r"''+|={2,}|\{\{[^{}]*\}\}|\{\||\|\}|\|")
MIN_FILES = 7       # 有 source_quote 的案例文件
MIN_QUOTES = 464    # 340 classical + 69 external + 12 dayun + 22 hua + 9 cong + 10 zhuan + 2 bing
MIN_ROUTED = 445    # 464 - 7 不可路由 - 12 夹注段豁免（431 批 10 条连续化、432 批 ZP025 截短后命中）


def norm(text: str) -> str:
    return re.sub(r"\s+", "", MARKUP_RE.sub("", str(text)))


# 仅用于「四柱在不在底本」这一项：连标点一起折掉，免得因底本顿号/逗号用法不同漏判。
FOLD = re.compile(r"[\s，。、；：,.;:]+")


def pillars_key(case: dict) -> str:
    p = case.get("pillars") or {}
    parts = [str(p.get(k) or "") for k in ("year", "month", "day", "hour")]
    return FOLD.sub("", "、".join(parts)) if all(parts) else ""


def longest_block(text: str, corpus: str) -> int:
    """归一化引文与底本的最长**连续**公共块长度（豁免项的实测证据）。"""
    if not text or not corpus:
        return 0
    m = SequenceMatcher(None, text, corpus, autojunk=False).find_longest_match(
        0, len(text), 0, len(corpus))
    return m.size


def book_name(case: dict) -> str:
    return str(case.get("book") or "").strip("《》 ")


def resolve_sources(case: dict) -> tuple[list[str] | None, str | None]:
    """返回 (底本相对路径列表, 不可路由原因)。两者互斥。"""
    book = book_name(case)
    if book in UNROUTABLE_BOOKS:
        return None, UNROUTABLE_BOOKS[book]
    if book in BOOK_SOURCES:
        return BOOK_SOURCES[book], None
    prov = case.get("provenance")
    if isinstance(prov, dict):
        f = str(prov.get("file") or "")
        if f:
            p = DISC / f
            if p.is_file():
                return [f], None
            return None, f"provenance.file 指向不存在的文件：{f}"
    return None, f"未登记书源：{book or '<无 book>'!r}（请登记 BOOK_SOURCES/UNROUTABLE_BOOKS 或 provenance.file）"


def load_corpus(names: tuple[str, ...]) -> tuple[str, ...]:
    """每本底本单独归一化（不拼在一起）：多底本时须能分辨引文落在哪一本。"""
    return tuple(norm((DISC / n).read_text(encoding="utf-8")) for n in names)


def verify_case(case: dict, corpus_by_names: dict, exempt: dict) -> tuple[str, str | None]:
    """返回 (状态, 消息)。状态 ∈ ok / exempt / exempt_bad / unrouted / missing / wrongbook / stale / error。"""
    cid = str(case.get("id") or "?")
    q = case.get("source_quote")
    if q is not None and (not isinstance(q, str) or not q.strip()):
        return "error", f"{cid}: source_quote 必须是非空字符串，实为 {q!r}"
    if not isinstance(q, str) or not q.strip():
        return "ok", None
    names, why = resolve_sources(case)
    if names is None:
        return "unrouted", f"{cid} book={book_name(case) or '?'}：{why}"
    key = tuple(names)
    if key not in corpus_by_names:
        corpus_by_names[key] = load_corpus(key)
    nq = norm(q)
    hits = [nq in text for text in corpus_by_names[key]]
    hit, primary = any(hits), hits[0]
    if cid in exempt["ids"]:
        if primary:
            return "stale", f"{cid}：豁免项已能在主底本连续命中（{names[0]}）——豁免过期，请回接逐字"
        pk = pillars_key(case)
        if pk and any(pk in FOLD.sub("", text) for text in corpus_by_names[key]):
            return "exempt_bad", (f"{cid}：豁免项的四柱「{pk}」已在底本出现——"
                                  f"「不在库」理由不成立，请回接逐字")
        for nm in (exempt.get("case_names") or {}).get(cid) or []:
            fn = FOLD.sub("", str(nm))
            if fn and any(fn in FOLD.sub("", text) for text in corpus_by_names[key]):
                return "exempt_bad", (f"{cid}：豁免项的人名「{nm}」已在底本出现——"
                                      f"「不在库」理由不成立，请回接逐字")
        return "exempt", f"{cid}：{exempt['reason']}"
    if not hit:
        return "missing", f"{cid}：引文非书源逐字子串（{names[0]}）→ {q[:70]!r}"
    if not primary:
        return "wrongbook", (f"{cid}：引文只在第二底本命中（{names[1]}），"
                             f"所署《{book_name(case)}》主底本不含——书源归属不成立 → {q[:50]!r}")
    return "ok", None


def iter_cases():
    for p in sorted(CASE_DIR.glob("*.json")):
        if p.name == "eval_all.json":
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            yield p, None, f"JSON 解析失败：{exc}"
            continue
        cases = d.get("cases") if isinstance(d, dict) else None
        if not isinstance(cases, list):
            yield p, None, None
            continue
        yield p, cases, None


def audit_exempt_ledger(exempt: dict) -> list[str]:
    """豁免册自身一致性（446 批）：专名/说明不得指向册外或不存在的 id。

    为什么需要它：`case_names` 只对 `ids` 里的案例执行核对，可一旦出现
    「case_names 有、ids 没有」的 key，那组专名**永远不会被比对**（静默死登记）；
    反过来，`ids` 里既无专名也未在 `_case_names_note` 披露的项，等于「不机械判」
    没有记录。两者都不会影响既有读数，却会让豁免册的「逐条披露」变成半真声明。
    """
    failures: list[str] = []
    ids = {str(x) for x in (exempt.get("ids") or [])}
    names = exempt.get("case_names") or {}
    note = str(exempt.get("_case_names_note") or "")
    for cid, vals in names.items():
        if cid not in ids:
            failures.append(f"豁免册：case_names 的 {cid} 不在 ids 中——该组专名永远不会被核对")
        if not isinstance(vals, list) or not vals:
            failures.append(f"豁免册：case_names[{cid}] 必须是非空列表")
        elif not all(isinstance(v, str) and v.strip() for v in vals):
            failures.append(f"豁免册：case_names[{cid}] 含空值/非字符串")
    # 披露写法允许简写：`ZP003/004/005/031/032` 要展开成五个 id，不能只认第一个。
    # 本仓既有注记就是这么写的——判红等于逼人为过门重写人类可读的说明（反向激励）。
    described: set[str] = set()
    for m in re.finditer(r"([A-Z]{2,})(\d{3})((?:[/／、]\d{3})*)", note):
        prefix = m.group(1)
        described.add(f"{prefix}{m.group(2)}")
        for extra in re.findall(r"\d{3}", m.group(3)):
            described.add(f"{prefix}{extra}")
    undisclosed = sorted(ids - set(names) - described)
    if undisclosed:
        failures.append(f"豁免册：{len(undisclosed)} 个豁免 id 既无专名登记、"
                        f"也未在 _case_names_note 披露：{undisclosed[:6]}")
    return failures


def check_all(exempt: dict) -> tuple[list[str], dict]:
    failures: list[str] = audit_exempt_ledger(exempt)
    # 459 批：案例目录 tests 指针可达性（[11] 不扫 data/cases，本门补上）
    for p in sorted(CASE_DIR.glob("*.json")):
        if p.name == "eval_all.json":
            continue
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        failures.extend(pointer_problems(txt, str(p.relative_to(DISC))))
    stats = {"files": 0, "quotes": 0, "routed": 0, "unrouted": 0, "exempt": 0,
             "per_file": [], "unrouted_detail": [], "exempt_detail": []}
    corpus: dict = {}
    seen_exempt: set[str] = set()
    for path, cases, err in iter_cases():
        rel = str(path.relative_to(DISC))
        if err:
            failures.append(f"{rel}: {err}")
            continue
        if cases is None:
            continue
        n_file = 0
        for case in cases:
            if not isinstance(case, dict):
                continue
            cid = str(case.get("id") or "?")
            if case.get("source_quote"):
                n_file += 1
                stats["quotes"] += 1
            status, msg = verify_case(case, corpus, exempt)
            if status == "ok":
                if case.get("source_quote"):
                    stats["routed"] += 1
            elif status == "exempt":
                stats["exempt"] += 1
                seen_exempt.add(cid)
                _names, _why = resolve_sources(case)
                _q = norm(case.get("source_quote") or "")
                _blk = max(longest_block(_q, t) for t in corpus[tuple(_names)])
                stats["exempt_detail"].append(
                    f"  {cid}：最长连续 {_blk}/{len(_q)} 字（夹注段不在库，逐条披露）")
            elif status == "unrouted":
                stats["unrouted"] += 1
                stats["unrouted_detail"].append(f"  {rel}: {msg}")
            elif status == "stale":
                seen_exempt.add(cid)   # 豁免项确实存在，只是过期；别误报「册内 id 找不到」
                failures.append(f"{rel}: {msg}")
            elif status == "wrongbook":
                failures.append(f"{rel}: {msg}")
            elif status == "exempt_bad":
                seen_exempt.add(cid)   # 同上：id 在案例集里，失败原因是四柱回潮
                failures.append(f"{rel}: {msg}")
            elif status == "missing":
                failures.append(f"{rel}: {msg}")
            elif status == "error":
                failures.append(f"{rel}: {msg}")
        if n_file:
            stats["files"] += 1
            stats["per_file"].append(f"  {rel}: 引文 {n_file} 条")

    stale_ids = sorted(set(exempt["ids"]) - seen_exempt)
    if stale_ids:
        failures.append(f"豁免册里的 id 在案例集中找不到（{len(stale_ids)} 个）：{stale_ids[:6]}…")
    if stats["files"] < MIN_FILES or stats["quotes"] < MIN_QUOTES:
        failures.append(f"下限守卫：{stats['files']} 份含引文文件 / {stats['quotes']} 条引文，"
                        f"低于基线 {MIN_FILES} 份 / {MIN_QUOTES} 条——先确认路径没挪动")
    if stats["quotes"] == 0:
        failures.append("扫描到 0 条引文——0 结果 ≠ 通过，先确认扫描路径")
    if stats["routed"] < MIN_ROUTED:
        failures.append(f"逐字比对只到 {stats['routed']} 条（基线 {MIN_ROUTED}）——"
                        "有引文被静默漏掉，这半边等于没挂门")
    return failures, stats


def selftest() -> int:
    needle = "五月丁火，时归建禄，不宜乱用甲木"
    qiong = load_corpus(tuple(BOOK_SOURCES["穷通宝鉴"]))[0]
    zip_key = tuple(BOOK_SOURCES["子平真诠评注"])
    corpus = {tuple(BOOK_SOURCES["穷通宝鉴"]): (qiong,),
              # 多底本夹具：主底本不含该句、第二底本含——用来判「只命中副底本」；
              # 主底本另含一组四柱，用来判「豁免项四柱已在底本」。
              zip_key: ("甲子乙丑丙寅丁卯", "本书没有这句话")}
    exempt = {"reason": "夹具：夹注段不在库", "ids": ["ZP001"]}
    cases = [
        ({"id": "POS", "book": "穷通宝鉴", "source_quote": needle}, "ok", "正例：书源逐字"),
        ({"id": "NEG", "book": "穷通宝鉴", "source_quote": needle + "；例：四柱"},
         "missing", "负例：尾拼非书源"),
        ({"id": "NEG2", "book": "穷通宝鉴", "source_quote": "本书没有这句话"},
         "missing", "负例：凭空句"),
        ({"id": "POS2", "book": "子平真诠评注", "source_quote": "甲子乙丑"},
         "ok", "正例：多底本时命中主底本"),
        ({"id": "WB", "book": "子平真诠评注", "source_quote": "本书没有这句话"},
         "wrongbook", "负例：只在第二底本命中＝书源归属不成立"),
        ({"id": "ZP001", "book": "子平真诠评注", "source_quote": "本书没有这句话"},
         "exempt", "豁免：夹注段在册披露、不判红"),
        ({"id": "ZP001", "book": "子平真诠评注", "source_quote": "本书没有这句话",
          "pillars": {"year": "戊辰", "month": "己巳", "day": "庚午", "hour": "辛未"}},
         "exempt", "豁免：四柱也不在底本"),
        ({"id": "ZP001", "book": "子平真诠评注", "source_quote": "本书没有这句话",
          "pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"}},
         "exempt_bad", "负例：豁免项四柱已在底本出现"),
        ({"id": "ZP001", "book": "穷通宝鉴", "source_quote": needle},
         "stale", "豁免过期：登记为不在库却已能连续命中"),
        ({"id": "XF001", "book": "珞琭子三命消息赋注", "source_quote": "任意"},
         "unrouted", "不可路由：书源不在库逐条披露"),
    ]
    bad = 0
    for case, want, why in cases:
        got, _msg = verify_case(case, corpus, exempt)
        ok = got == want
        if not ok:
            bad += 1
        print(f"  {'√' if ok else '×'} {why}（期望 {want}，实为 {got}）")
    name_cases = [
        (dict(exempt, ids=["ZP002"], case_names={"ZP002": ["龙济光"]}), "exempt",
         "豁免：登记专名也不在底本"),
        (dict(exempt, ids=["ZP002"], case_names={"ZP002": ["甲子乙丑"]}), "exempt_bad",
         "负例：豁免项登记专名已在底本出现"),
    ]
    for ex, want, why in name_cases:
        case = {"id": "ZP002", "book": "子平真诠评注", "source_quote": "本书没有这句话",
                "pillars": {"year": "戊辰", "month": "己巳", "day": "庚午", "hour": "辛未"}}
        got, _msg = verify_case(case, corpus, ex)
        ok = got == want
        if not ok:
            bad += 1
        print(f"  {'√' if ok else '×'} {why}（期望 {want}，实为 {got}）")
    ledger_cases = [
        ({"ids": ["ZP001", "ZP002"], "case_names": {"ZP001": ["龙济光"]},
          "_case_names_note": "ZP002 为泛称，不做人名机械判"}, 0,
         "豁免册正例：专名+披露齐全"),
        ({"ids": ["ZP001"], "case_names": {"ZP099": ["某"]},
          "_case_names_note": "ZP001 无专名"}, 1,
         "负例：case_names 的 key 不在 ids（死登记）"),
        ({"ids": ["ZP001", "ZP002"], "case_names": {},
          "_case_names_note": "ZP001 无专名"}, 1,
         "负例：ids 有既无专名也未披露的项"),
        ({"ids": ["ZP001"], "case_names": {"ZP001": []}, "_case_names_note": ""}, 1,
         "负例：专名列表为空"),
        ({"ids": ["ZP003", "ZP004", "ZP005"], "case_names": {},
          "_case_names_note": "ZP003/004/005 无专名"}, 0,
         "豁免册正例：披露用斜杠简写也要展开"),
    ]
    for ex, want, why in ledger_cases:
        n = len(audit_exempt_ledger(ex))
        ok = n == want
        if not ok:
            bad += 1
        print(f"  {'√' if ok else '×'} {why}（期望 {want} 条，实为 {n} 条）")
    # 459 批：案例目录 tests 指针（活指针必抓；显式病史行不误伤）
    # 负例名按 §四.8 约定走 `__` 双下划线前缀，才不会被 [11] 当成对本仓的活声明。
    if not pointer_problems("回验由 tests/__no_such__ghost_459.py 承担", "夹具"):
        bad += 1
        print("  × 负例未抓到：案例目录里的幽灵 tests 指针")
    else:
        print("  √ 负例被抓：案例目录 tests 指针不可达")
    if pointer_problems("该测试文件 tests/test_ghost_hist.py 从未存在", "夹具"):
        bad += 1
        print("  × 正例被误伤：显式病史行")
    else:
        print("  √ 正例放行：显式病史行（从未存在）")
    if pointer_problems("回验由 tests/regression_test.py 承担", "夹具"):
        bad += 1
        print("  × 正例被误伤：可达的 tests 指针")
    else:
        print("  √ 正例放行：可达 tests 指针")
    full = longest_block(norm(needle), qiong)
    part = longest_block(norm("本书并无此语"), qiong)
    ok_blk = full == len(norm(needle)) and part < 6
    print(f"  {'√' if ok_blk else '×'} 最长连续块自证（库内整句 {full}/{len(norm(needle))} 字；"
          f"库外句 {part} 字）")
    if not ok_blk:
        bad += 1
    if bad:
        print(f"  × selftest 失败 {bad} 例——比对逻辑/路由漂移，先修器")
        return 1
    print(f"  √ selftest：{len(cases) + len(name_cases) + len(ledger_cases)} 件"
          f"（正例×2/尾拼/凭空句/副底本误挂/"
          f"豁免×2/豁免四柱回潮/豁免专名×2/豁免过期/不可路由/豁免册自洽×5/"
          f"tests 指针×3）＋最长连续块全过")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="八字科案例引文逐字性门（[41]）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    exempt = json.loads(EXEMPT.read_text(encoding="utf-8"))
    failures, stats = check_all(exempt)
    print(f"[41] 案例引文逐字性：{stats['files']} 份案例文件，引文 {stats['quotes']} 条"
          f"（逐字比对 {stats['routed']}，豁免 {stats['exempt']}，"
          f"书源不在库披露 {stats['unrouted']}）")
    for line in stats["per_file"]:
        print(line)
    for line in stats["unrouted_detail"]:
        print(f"  （披露·书源不在库）{line}")
    for line in stats["exempt_detail"]:
        print(line)
    st_fail = selftest() if args.selftest else 0
    if failures:
        print(f"\n失败 {len(failures)} 项：")
        for f in failures:
            print(f"  × {f}")
        return 1
    if st_fail:
        return 1
    print("  √ 全部逐字通过（豁免册逐条披露，过期即红）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
