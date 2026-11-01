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
  D. 下限守卫：含引文文件数、引文总数、逐字比对数低于登记基线即判红
     （0 结果 ≠ 通过；路径挪动/解析失败必须先显形）。

    python dev_tools/check_case_quotes.py            # 全量对拍
    python dev_tools/check_case_quotes.py --selftest # 正负例自证
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
CASE_DIR = DISC / "data" / "cases"
SRC_DIR = DISC / "data" / "sources"
EXEMPT = DISC / "data" / "rules" / "case_quote_exempt.json"

# book → 底本（相对 DISC）。新增引用书源时在此登记；未登记且无 provenance.file 即判红。
BOOK_SOURCES = {
    "穷通宝鉴": ["data/sources/qiong-tong-bao-jian.wikitext.txt"],
    "滴天髓阐微": ["data/sources/di-tian-sui-chan-wei.wikitext.txt"],
    "神峰通考": ["data/sources/shen-feng-tong-kao.wikitext.txt"],
    "渊海子平": ["data/sources/yuan-hai-zi-ping.wikitext.txt"],
    "千里命稿": ["data/sources/qianli_minggao_dz.dz.txt"],
    # 案例夹注段在 dz 本只部分可寻；命理探原同段可作第二底本（逐条仍须连续命中）
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
MIN_ROUTED = 434    # 464 - 7 不可路由 - 23 夹注段豁免


def norm(text: str) -> str:
    return re.sub(r"\s+", "", MARKUP_RE.sub("", str(text)))


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


def load_corpus(names: tuple[str, ...]) -> str:
    return "\n".join((DISC / n).read_text(encoding="utf-8") for n in names)


def verify_case(case: dict, corpus_by_names: dict, exempt: dict) -> tuple[str, str | None]:
    """返回 (状态, 消息)。状态 ∈ ok / exempt / unrouted / missing / stale / error。"""
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
        corpus_by_names[key] = norm(load_corpus(key))
    hit = norm(q) in corpus_by_names[key]
    if cid in exempt["ids"]:
        if hit:
            return "stale", f"{cid}：豁免项已能在底本连续命中（{names[0]}）——豁免过期，请回接逐字"
        return "exempt", f"{cid}：{exempt['reason']}"
    if not hit:
        return "missing", f"{cid}：引文非书源逐字子串（{names[0]}）→ {q[:70]!r}"
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


def check_all(exempt: dict) -> tuple[list[str], dict]:
    failures: list[str] = []
    stats = {"files": 0, "quotes": 0, "routed": 0, "unrouted": 0, "exempt": 0,
             "per_file": [], "unrouted_detail": []}
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
            elif status == "unrouted":
                stats["unrouted"] += 1
                stats["unrouted_detail"].append(f"  {rel}: {msg}")
            elif status == "stale":
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
    qiong = norm(load_corpus(tuple(BOOK_SOURCES["穷通宝鉴"])))
    corpus = {tuple(BOOK_SOURCES["穷通宝鉴"]): qiong}
    exempt = {"reason": "夹具：夹注段不在库", "ids": ["ZP001"]}
    cases = [
        ({"id": "POS", "book": "穷通宝鉴", "source_quote": needle}, "ok", "正例：书源逐字"),
        ({"id": "NEG", "book": "穷通宝鉴", "source_quote": needle + "；例：四柱"},
         "missing", "负例：尾拼非书源"),
        ({"id": "NEG2", "book": "穷通宝鉴", "source_quote": "本书没有这句话"},
         "missing", "负例：凭空句"),
        ({"id": "ZP001", "book": "子平真诠评注", "source_quote": "本书没有这句话"},
         "exempt", "豁免：夹注段在册披露、不判红"),
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
    if bad:
        print(f"  × selftest 失败 {bad} 例——比对逻辑/路由漂移，先修器")
        return 1
    print(f"  √ selftest：{len(cases)} 件（正例/尾拼/凭空句/豁免/豁免过期/不可路由）全过")
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
