# -*- coding: utf-8 -*-
"""[1k] 案例引文逐字性门：`disciplines/*/data/cases/*.json` 里每条 `source_quote`
必须是所引书源的逐字子串（剥 wikitext 标记 + 去空白后）。

背景（2026-10-06m，docs/TECH-DEBT.md §2.4）：外集 QTBJ 批 9 条引文系压缩改写/拼接
（如把三秋句安到三夏标题下、引文尾拼『；例：四柱』），静默入库且全门 EXIT=0——
现行 [1j] 语料可复现只校验「构建器重跑 == 入库」，不校验案例集引文是否逐字。
本门补这个洞。

口径：
- 书源路由按案例 `book` 字段查 BOOK_SOURCES；`book` 未登记且 `_provenance.source_file`
  也指不到文件 → 判败（不是静默跳过）。书源不在库的书列入 UNROUTABLE_BOOKS，
  逐条披露后跳过（有数、可见，防「0 结果 = 通过」假绿）。
- 逐字判定：两侧剥 wikitext 标记（''' 粗体、== 标题、{| |} | 表格、{{模板}}）并去
  全部空白后要求**连续子串**。剥标记是因维基文库底本的 ''' / === 是排版标记不是书文；
  去空白是因引文常跨表格单元格/换行。压缩（删字）、拼接（跨段、乱序）仍必判败。
- 下限守卫：扫描文件数 / 引文总数低于登记基线即判败——防「路径解析错了扫 0 份文件」
  （0 结果 ≠ 通过，同 [1b-2] 死链门教训）。

--selftest：内置负例自证（假引文三种病灶 + 正例），负例必须全被抓、正例必须过，
否则本工具自身判败。
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "data" / "sources"

# book → 书源文件（仓库相对路径）。新增引用书源时在此登记；未登记书名即判败。
BOOK_SOURCES = {
    "穷通宝鉴": ["data/sources/qiong-tong-bao-jian.wikitext.txt"],
    "滴天髓阐微": ["data/sources/di-tian-sui-chan-wei.wikitext.txt"],
    "神峰通考": ["data/sources/shen-feng-tong-kao.wikitext.txt"],
    # 六壬大全分卷入库：引文可能在任何一卷，全部拼接后比对
    "六壬大全": [str(p.relative_to(ROOT))
                 for p in sorted(SRC_DIR.glob("liu-ren-da-quan*.wikitext.txt"))],
}

# 书源不在库、无法逐字对拍的书：逐条披露（计 unrouted），不算失败也不静默。
UNROUTABLE_BOOKS = {
    "子平真诠评注": "维基文库实测 missingtitle，书源不在库（TECH-DEBT §2.8 同记录）",
}

MARKUP_RE = re.compile(r"''+|={2,}|\{\{[^{}]*\}\}|\{\||\|\}|\|")

# 下限守卫（2026-10-06m 基线）：低于即判败，改基线须在 CHANGELOG 登记理由
MIN_FILES_WITH_QUOTES = 4
MIN_QUOTES_TOTAL = 380


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", MARKUP_RE.sub("", text))


def iter_case_files():
    for p in sorted(ROOT.glob("disciplines/*/data/cases/*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            yield p, None, [], f"JSON 解析失败：{e}"
            continue
        cases = d.get("cases") if isinstance(d, dict) else d
        if not isinstance(cases, list):
            yield p, None, [], "无 cases 列表（非案例集，跳过）"
            continue
        yield p, d, cases, None


def resolve_book(case: dict):
    """返回 (book名, 文件名列表, 错误消息)。三类出口：routed / unroutable / error。"""
    prov = case.get("_provenance") or {}
    book = case.get("book") or prov.get("book") or ""
    if book in BOOK_SOURCES:
        return book, BOOK_SOURCES[book], None
    if book in UNROUTABLE_BOOKS:
        return book, None, UNROUTABLE_BOOKS[book]
    sf = prov.get("source_file")
    if sf:
        cand = ROOT / sf
        if cand.is_file():
            return book or sf, [str(cand.relative_to(ROOT))], None
        return book or sf, None, f"_provenance.source_file 指向不存在的文件：{sf}"
    return book or "<无 book>", None, f"未登记路由的书源：{book!r}（请登记 BOOK_SOURCES/UNROUTABLE_BOOKS）"


class CorpusCache:
    def __init__(self) -> None:
        self._cache: dict[tuple, str] = {}

    def get(self, names: tuple) -> str:
        if names not in self._cache:
            self._cache[names] = "\n".join(
                (ROOT / n).read_text(encoding="utf-8") for n in names)
        return self._cache[names]


def check_all():
    """返回 (failures, stats)。failures 为消息列表；stats 供报告与下限守卫。"""
    failures: list[str] = []
    stats = {"files": 0, "quotes": 0, "routed": 0, "unrouted": 0, "per_file": []}
    corpus = CorpusCache()
    unrouted_detail: list[str] = []
    for path, _d, cases, err in iter_case_files():
        rel = str(path.relative_to(ROOT))
        if err:
            if err != "无 cases 列表（非案例集，跳过）":
                failures.append(f"{rel}: {err}")
            continue
        n_file = routed = unrouted = 0
        for case in cases:
            if not isinstance(case, dict):
                continue
            q = case.get("source_quote")
            if q is None:
                continue
            if not isinstance(q, str) or not q.strip():
                failures.append(f"{rel}:{case.get('id', '?')}: source_quote 必须是非空字符串，实为 {q!r}")
                continue
            n_file += 1
            cid = case.get("id", "?")
            book, names, problem = resolve_book(case)
            if names is None:
                unrouted += 1
                unrouted_detail.append((rel, str(cid), str(book), str(problem)))
                continue
            routed += 1
            if normalize(q) not in normalize(corpus.get(tuple(names))):
                failures.append(f"{rel}:{cid} book={book}: 引文非书源逐字子串 → {q[:60]!r}")
        if n_file:
            stats["files"] += 1
            stats["quotes"] += n_file
            stats["routed"] += routed
            stats["unrouted"] += unrouted
            stats["per_file"].append(f"  {rel}: 引文 n={n_file} 逐字比对={routed} "
                                     f"书源不在库披露={unrouted}")
    if stats["files"] < MIN_FILES_WITH_QUOTES or stats["quotes"] < MIN_QUOTES_TOTAL:
        failures.append(
            f"下限守卫触发：扫描到 {stats['files']} 份含引文文件 / {stats['quotes']} 条引文，"
            f"低于基线（{MIN_FILES_WITH_QUOTES} 份 / {MIN_QUOTES_TOTAL} 条）——"
            "先确认案例文件路径没被挪动或解析失败，再考虑改基线（须登记 CHANGELOG）")
    if stats["quotes"] == 0:
        failures.append("扫描到 0 条引文——0 结果 ≠ 通过，先确认扫描路径")
    # 不可路由按（文件×书×原因）分组汇总：保留条数与首末例号可审计，不逐条刷屏
    grouped: dict[tuple, list[str]] = {}
    for rel, cid, book, reason in unrouted_detail:
        grouped.setdefault((rel, book, reason), []).append(cid)
    stats["unrouted_detail"] = [
        f"{rel} book={book}（{len(ids)} 例：{ids[0]}…{ids[-1]}）—— {reason}"
        for (rel, book, reason), ids in sorted(grouped.items())]
    return failures, stats


NEEDLE = "五月丁火"  # 自证用锚句（书源真实句，非假路径约定）

# 负例（三种病灶，取自 2026-10-06m 实挖的真实缺陷形态）+ 正例
SELFTEST_CASES = [
    # (引文, 期望结果 True=必须判败 / False=必须通过, 病灶说明)
    (NEEDLE + "，时归建禄，不宜乱用甲木", False, "正例：书源行715 逐字"),
    ("正月用壬，庚辛为助；例：丙午庚寅丙午庚寅", True, "尾拼非书源文字（QTBJ001 原病灶）"),
    ("三秋丁火，耑用甲木，仍取庚噼甲", True, "压缩改写：删『退气柔弱』等句（QTBJ015 原病灶）"),
    (NEEDLE + "，时归建禄，耑用甲木，仍取庚噼甲", True, "跨段拼接：五月否定句+三秋处方（QTBJ013 原病灶）"),
]


def selftest() -> int:
    corpus = normalize((SRC_DIR / "qiong-tong-bao-jian.wikitext.txt").read_text(encoding="utf-8"))
    bad = 0
    for quote, must_fail, why in SELFTEST_CASES:
        hit = normalize(quote) in corpus
        ok = (not hit) if must_fail else hit
        mark = "√" if ok else "×"
        if not ok:
            bad += 1
        print(f"  {mark} {'判败' if hit else '通过'}（期望{'判败' if must_fail else '通过'}）{why}")
    if bad:
        print(f"  自证失败 {bad} 例——比对逻辑或书源锚句漂移，先修本工具再挂门")
        return 1
    print("  负例全被抓、正例通过——比对逻辑自证成立")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="案例集引文逐字性门（详见模块 docstring）")
    ap.add_argument("--selftest", action="store_true",
                    help="内置负例自证：三种假引文病灶必须全被判败")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    failures, stats = check_all()
    print(f"[1k] 案例引文逐字性：扫描 {stats['files']} 份案例文件，"
          f"引文 {stats['quotes']} 条（逐字比对 {stats['routed']}，"
          f"书源不在库披露 {stats['unrouted']}）")
    for line in stats["per_file"]:
        print(line)
    for line in stats["unrouted_detail"]:
        print(f"  （披露·书源不在库）{line}")
    if failures:
        print(f"\n失败 {len(failures)} 项：")
        for f in failures:
            print(f"  × {f}")
        return 1
    print("  √ 全部逐字通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
