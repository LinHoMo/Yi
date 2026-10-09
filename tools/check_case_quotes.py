# -*- coding: utf-8 -*-
"""[1k] 案例引文逐字性门：案例集里自称"照录自古籍"的字段必须是所引书源的逐字子串。

两个字段面（口径不同，见下）：
- `source_quote`（命科）：剥 wikitext 标记 + **全剥空白**后要求连续子串；
- `expected.detail`（六爻，2026-10-09 扩）：只在记录带 `provenance.page` 时才算照录，
  且走更严一档的 `normalize_strict`（并行走/制空白，但**保留字间空格**）。

背景（2026-10-06m，docs/TECH-DEBT.md §2.4）：外集 QTBJ 批 9 条引文系压缩改写/拼接
（如把三秋句安到三夏标题下、引文尾拼『；例：四柱』），静默入库且全门 EXIT=0——
现行 [1j] 语料可复现只校验「构建器重跑 == 入库」，不校验案例集引文是否逐字。
本门补这个洞。
扩面背景（2026-10-09）：六爻 82 条 wikisource `expected.detail` 无人回验，实测 8 条
非书源逐字（7 条 爲→为 异体改字、1 条「後果」被写成「後 果」＝构建器把扫描用的
改写当产物）。若不保留字间空格，插一个空格就能过——所以这一面单独用严口径。
不带 provenance.page 的 detail（classical_cases 44 条、yingqi_cases 2 条）是
case_library 的现代转写基准，**不做逐字要求**，但要报出条数（不静默消失在门里）。

口径：
- 书源路由：`source_quote` 按案例 `book` 字段查 BOOK_SOURCES，`book` 未登记且
  `_provenance.source_file` 也指不到文件 → 判败（不是静默跳过）；
  `expected.detail` 按 `provenance.page` 查 PAGE_SOURCES，页源未登记即判败。
  书源不在库的书列入 UNROUTABLE_BOOKS，逐条披露后跳过（有数、可见，防
  「0 结果 = 通过」假绿）。
- 逐字判定：两侧剥 wikitext 标记（''' 粗体、== 标题、{| |} | 表格、{{模板}}）。
  `source_quote` 再剥**全部**空白后要求连续子串——引文常跨表格单元格/换行；
  `expected.detail` 只并行走/制空白、**保留字间空格**，否则「後果→後 果」这类
  单字符插入根本测不出。两种形态（压缩删字、跨段乱序拼接）都必判败。
- 下限守卫：扫描文件数 / 引文总数 / 六爻 detail 回验数低于登记基线即判败——
  防「路径解析错了扫 0 份文件」（0 结果 ≠ 通过，同 [1b-2] 死链门教训）。

--selftest：内置负例自证（命科面尾拼/压缩/跨段 + 六爻面异体改字/插入空格/跨段拼接，
正例各一），负例必须全被抓、正例必须过，否则本工具自身判败。
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

# 六爻侧的"照录"字段不是 `source_quote` 而是 `expected.detail`，它靠
# `provenance.page` 指回原本。此前 [1k] 只看 ming 的 source_quote，六爻 89 条
# 自称"取自原本"的 detail 无人回验——实测其中 8 条被改写（爲→为 7 条、
# 被插入空格 1 条）而全门 EXIT=0。
PAGE_SOURCES = {
    "增刪卜易": ["data/sources/zengshan_buyi.wikitext.txt"],
    "火珠林": ["data/sources/huozhulin.wikitext.txt",
               "data/sources/huozhulin_dz.dz.txt"],
}

# 书源不在库、无法逐字对拍的书：逐条披露（计 unrouted），不算失败也不静默。
UNROUTABLE_BOOKS = {
    "子平真诠评注": "维基文库实测 missingtitle，书源不在库（TECH-DEBT §2.8 同记录）",
}

MARKUP_RE = re.compile(r"''+|={2,}|\{\{[^{}]*\}\}|\{\||\|\}|\|")

# 下限守卫（2026-10-06m 基线）：低于即判败，改基线须在 CHANGELOG 登记理由
# 2026-10-09 scope-reduction：4→3 份 / 380→341 条 —— 差额正是随范围收缩删除的
# 已删学科案例文件（zeji/xiaoliuren 等），非扫描面被意外挪动（逐条比对见 CHANGELOG）。
# 2026-10-09 扩面：3→6 份 / 341→430 条（新增六爻 expected.detail 89 条，
# 分布在 wikisource_cases 82 + huozhulin_cases 2 + huozhulin_qualitative 5），
# 另加一条"六爻 detail 回验数 <89 即判败"的专面守卫。
MIN_FILES_WITH_QUOTES = 6
MIN_QUOTES_TOTAL = 430


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", MARKUP_RE.sub("", text))


def normalize_strict(text: str) -> str:
    """六爻 `expected.detail` 用的口径：并行走空白，但**保留字间空格**。

    比命科口径严一档是必要的：本轮实测到的病灶之一就是把「後果」写成「後 果」
    （构建器把扫描用的改写当成了产物）。全剥空白的口径对它无感——留一个空格
    就能蒙过去，等于这门对"照录不许改字"没有牙。
    """
    t = MARKUP_RE.sub("", text)
    return re.sub(r"[ \t　]+", " ", re.sub(r"\s*\n\s*", "", t)).strip()


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
    """书源原文 + 两种归一口径的缓存。

    430 条引文若每条都重新读文件、重跑正则，门会慢到没人愿意跑默认档；
    两种口径（全剥空白 / 保留字间空格）分别缓存，比对时零重复计算。
    """

    def __init__(self) -> None:
        self._raw: dict[tuple, str] = {}
        self._norm: dict[tuple, dict[str, str]] = {}

    def get(self, names: tuple, mode: str = "loose") -> str:
        if names not in self._raw:
            self._raw[names] = "\n".join(
                (ROOT / n).read_text(encoding="utf-8") for n in names)
            self._norm[names] = {"loose": normalize(self._raw[names]),
                                 "strict": normalize_strict(self._raw[names])}
        return self._norm[names][mode]


def resolve_page(case: dict):
    """六爻侧走 `provenance.page`；返回 (书线索, 文件列表, 错误消息) 或 (None,...) 表示不适用。"""
    prov = case.get("provenance")
    if not isinstance(prov, dict):
        return None, None, None          # provenance 不是对象（实测命科 BY* 是字符串）
    page = prov.get("page") or ""
    if not page:
        return None, None, None
    if page in PAGE_SOURCES:
        return page, PAGE_SOURCES[page], None
    if page in BOOK_SOURCES:
        return page, BOOK_SOURCES[page], None
    return page, None, f"provenance.page {page!r} 未登记 PAGE_SOURCES/BOOK_SOURCES"


def quote_faces(case: dict) -> list[tuple[str, str]]:
    """该案例里自称"照录自古籍"的字段。

    `expected.detail` 只有在带 `provenance.page` 时才算照录——不带页源的 detail
    是 case_library 的现代转写基准（classical_cases 44 条、yingqi_cases 2 条），
    要求它逐字反而是错的。这类由调用方计入披露数，不静默消失。
    """
    faces: list[tuple[str, str]] = []
    q = case.get("source_quote")
    if isinstance(q, str) and q.strip():
        faces.append(("source_quote", q))
    exp = case.get("expected")
    det = exp.get("detail") if isinstance(exp, dict) else None
    page = resolve_page(case)[0]
    if isinstance(det, str) and det.strip() and page:
        faces.append(("expected.detail", det))
    return faces


def check_all():
    """返回 (failures, stats)。failures 为消息列表；stats 供报告与下限守卫。"""
    failures: list[str] = []
    stats = {"files": 0, "quotes": 0, "routed": 0, "unrouted": 0, "per_file": [],
             "detail_total": 0, "detail_routed": 0, "transcribed": 0}
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
            cid = case.get("id", "?")
            q = case.get("source_quote")
            if q is not None and (not isinstance(q, str) or not q.strip()):
                failures.append(f"{rel}:{cid}: source_quote 必须是非空字符串，实为 {q!r}")
            page, page_names, page_err = resolve_page(case)
            exp = case.get("expected")
            det = exp.get("detail") if isinstance(exp, dict) else None
            if isinstance(det, str) and det.strip() and not page:
                stats["transcribed"] += 1     # 转写基准：不做逐字要求，但要有数
            faces = quote_faces(case)
            if not faces:
                continue
            n_file += len(faces)
            if page and page_err:
                unrouted += len(faces)
                unrouted_detail.append((rel, str(cid), str(page), page_err))
                continue
            for field, text in faces:
                if field == "expected.detail":
                    names, book = page_names, page
                    stats["detail_total"] += 1
                else:
                    book, names, problem = resolve_book(case)
                    if names is None:
                        unrouted += 1
                        unrouted_detail.append((rel, str(cid), str(book), str(problem)))
                        continue
                routed += 1
                if field == "expected.detail":
                    if normalize_strict(text) not in corpus.get(tuple(names), "strict"):
                        failures.append(f"{rel}:{cid} {field} 書源={book}: "
                                        f"照录串非书源逐字子串（严口径，字间空格也算改动）"
                                        f" → {text[:60]!r}")
                elif normalize(text) not in corpus.get(tuple(names), "loose"):
                    failures.append(f"{rel}:{cid} {field} book={book}: "
                                    f"引文非书源逐字子串 → {text[:60]!r}")
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
    if stats["detail_total"] < 89:
        failures.append(f"六爻 expected.detail 只回验到 {stats['detail_total']} 条（基线 89）——"
                        "带 provenance.page 的记录被静默漏掉＝这半边等于没挂门")
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
        print(f"  {mark} {'书源命中' if hit else '书源不命中'}"
              f"（期望{'命中' if not must_fail else '不命中'}）命科面：{why}")
    # 六爻 detail 面：负例取自本轮真实复现过的两种病灶（转简、被插入的空格）
    zsb = normalize_strict((SRC_DIR / "zengshan_buyi.wikitext.txt").read_text(encoding="utf-8"))
    real = "應外卦世與日月同爲三合﹐以爲吉卦﹐不宜世爻變鬼﹐又化回頭之克﹐上爻未土又克"
    liuyao = [
        (real, False, "正例：WSD018 照录串在書源逐字（严口径）"),
        (real.replace("爲", "为"), True, "异体改字：爲→为（实测 7 条 detail 有此病灶）"),
        ("應爻﹐一定不得﹐後 果另選別人", True, "字间被插入空格（实测 WSD024 原状）"),
        ("應外卦世與日月同爲三合﹐以爲吉卦﹐身入墓鄕到老求謀多淚", True,
         "跨段拼接：本案斷曰 + 后文通论（构建器窗口漂移的产物形态）"),
    ]
    for quote, must_fail, why in liuyao:
        hit = normalize_strict(quote) in zsb
        ok = (not hit) if must_fail else hit
        if not ok:
            bad += 1
        print(f"  {'√' if ok else '×'} {'书源不命中' if hit else '书源命中'}"
              f"（期望{'不命中' if must_fail else '命中'}）六爻面：{why}")
    if bad:
        print(f"  自证失败 {bad} 例——比对逻辑或书源锚句漂移，先修本工具再挂门")
        return 1
    print(f"  负例全被抓、正例通过——比对逻辑自证成立"
          f"（命科面 {len(SELFTEST_CASES)} 例 + 六爻面 {len(liuyao)} 例）")
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
    print(f"    其中六爻 expected.detail 回验 {stats['detail_total']} 条"
          f"（带 provenance.page 者）；另有 {stats['transcribed']} 条 detail 属"
          f"case_library 现代转写基准，不做逐字要求")
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
