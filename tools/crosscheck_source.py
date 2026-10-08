# -*- coding: utf-8 -*-
"""跨源对勘器：同一部古籍两个来源的转录本机械比对，留痕引用质量。

    python tools/crosscheck_source.py --pairs-table          # 跑内置对勘表（维基文库 ↔ 殆知阁）
    python tools/crosscheck_source.py --pair zengshan_buyi zengshan_buyi_dz
    python tools/crosscheck_source.py --file A.txt --file2 B.txt --name 自定义名
    python tools/crosscheck_source.py --selftest             # 正/负例自证（先怀疑再证明）

为什么必须有这个工具：
  殆知阁是志愿转录/OCR 数据集，未经专业校勘；维基文库同样是志愿转录。
  两源同书时，谁也不能空口说"质量可以"——本工具把一致性变成可复核的数字：
    1. 繁简折叠（zhconv，双侧转简体）后只留汉字，去标点/空白/维基标记；
    2. 12 字 shingle 集合：主源 shingle 被副源覆盖率（containment）、Jaccard；
    3. 随机 16 字窗口逐字命中（seed 固定 42，可复现），给出命中/未命中实例；
  结论分四档，<0.15 一律判"对不上"，绝无"差不多就行"的口径。

结果落 `data/sources/crosscheck_report.json`（按对累计），供 LEDGER/评审引用。
依赖：`pip install zhconv`（仅本工具；仓库其余工具零第三方依赖）。
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import unicodedata
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources"
REPORT = SOURCES / "crosscheck_report.json"
CST = timezone(timedelta(hours=8))

WINDOW = 16          # 逐字命中窗口长度（字）
N_WINDOWS = 40       # 抽窗数量
SHINGLE = 12         # shingle 长度（字）
SEED = 42

try:
    from zhconv import convert as _zhconv
except ImportError:
    _zhconv = None

# 内置对勘表：wiki key ↔ dz key（DZ_CATALOG 里 kind 带「对勘」的书）。
# 主源＝维基文库（<key>.wikitext.txt），副源＝殆知阁（<key>_dz.dz.txt）。
PAIRS_TABLE = (
    ("zengshan_buyi", "zengshan_buyi_dz"),
    ("huangjin_ce", "huangjince_dz"),
    ("huozhulin", "huozhulin_dz"),
    ("qiong-tong-bao-jian", "qiong_tong_bao_jian_dz"),
    ("shen-feng-tong-kao", "shenfeng_tongkao_dz"),
    ("di-tian-sui-chan-wei", "ditian_sui_chanwei_dz"),
    ("mei-hua-yi-shu", "meihua_yishu_dz"),
    ("ling-qi-jing", "lingqijing_dz"),
    ("liu-ren-zhi-nan", "liuren_zhinan_dz"),
    ("yuan-hai-zi-ping", "yuanhai_ziping_dz"),
)

# 结论分档（对 containment_primary）：
#   ≥0.85 高度一致；≥0.50 基本一致；≥0.15 低一致；<0.15 对不上。
BANDS = ((0.85, "高度一致"), (0.50, "基本一致（有卷次/版本差异或缺漏）"),
         (0.15, "低一致（版本差异大，引用前须人工核对）"), (0.0, "对不上/存疑"))


def band_of(containment: float) -> str:
    for lo, label in BANDS:
        if containment >= lo:
            return label
    return BANDS[-1][1]


# ── 归一化 ──────────────────────────────────────────────────────────────────

_CJK = re.compile(r"[^\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufa29]+")


def normalize(text: str) -> str:
    """双侧同一口径：NFKC → 繁简折叠为简体 → 只留汉字。"""
    if _zhconv is None:
        raise SystemExit("需要 zhconv：pip install zhconv（繁简折叠是跨源比对前提）")
    text = unicodedata.normalize("NFKC", text)
    text = _zhconv(text, "zh-hans")
    return _CJK.sub("", text)


def shingles(norm: str, n: int = SHINGLE) -> set[str]:
    if len(norm) < n:
        return {norm} if norm else set()
    return {norm[i:i + n] for i in range(len(norm) - n + 1)}


# ── 取文 ────────────────────────────────────────────────────────────────────

def load_wiki(key: str) -> str:
    from clean_wikitext import clean  # 同目录工具；去维基标记后再归一化
    p = SOURCES / f"{key}.wikitext.txt"
    if not p.is_file():
        raise SystemExit(f"× 找不到 {p.relative_to(ROOT)}（先跑 tools/fetch_source.py --fetch {key}）")
    return clean(p.read_text(encoding="utf-8"))


def load_dz(key: str) -> str:
    p = SOURCES / f"{key}.dz.txt"
    if not p.is_file():
        raise SystemExit(f"× 找不到 {p.relative_to(ROOT)}（先跑 tools/fetch_source.py --fetch {key}）")
    return p.read_text(encoding="utf-8")


# ── 比对 ────────────────────────────────────────────────────────────────────

def compare(primary_raw: str, secondary_raw: str) -> dict:
    """双侧归一化 → shingle 覆盖率 + 随机窗口逐字命中。数字即结论。"""
    p, s = normalize(primary_raw), normalize(secondary_raw)
    sp, ss = shingles(p), shingles(s)
    inter = len(sp & ss)
    containment_p = inter / len(sp) if sp else 0.0
    containment_s = inter / len(ss) if ss else 0.0
    jaccard = inter / len(sp | ss) if (sp | ss) else 0.0

    rng = random.Random(SEED)
    windows = []
    if len(p) > WINDOW:
        for _ in range(N_WINDOWS):
            windows.append(p[rng.randrange(0, len(p) - WINDOW + 1):
                             rng.randrange(0, len(p) - WINDOW + 1) + WINDOW])
    hits, misses = [], []
    for w in windows:
        (hits if w in s else misses).append(w)
    hit_rate = len(hits) / len(windows) if windows else 0.0

    return {
        "primary_chars": len(p), "secondary_chars": len(s),
        "shingles_primary": len(sp), "shingles_secondary": len(ss),
        "containment_primary": round(containment_p, 4),
        "containment_secondary": round(containment_s, 4),
        "jaccard": round(jaccard, 4),
        "windows": len(windows), "window_hits": len(hits),
        "window_hit_rate": round(hit_rate, 4),
        "hit_examples": hits[:3], "miss_examples": misses[:3],
        "verdict": band_of(containment_p),
    }


def crosscheck(name: str, primary_raw: str, secondary_raw: str,
               meta: dict | None = None) -> dict:
    st = stat_files(primary_raw, secondary_raw)
    res = compare(primary_raw, secondary_raw)
    res.update({
        "pair": name,
        "primary": st[0], "secondary": st[1],
        "checked": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S%z"),
        "method": (f"NFKC+zh-hans 折叠后取汉字；{SHINGLE} 字 shingle containment + "
                   f"{N_WINDOWS}×{WINDOW} 字随机窗口逐字命中（seed={SEED}）"),
    })
    if meta:
        res.update(meta)
    print(f"  {name}: containment={res['containment_primary']:.2%} "
          f"jaccard={res['jaccard']:.2%} 窗口命中={res['window_hit_rate']:.2%} "
          f"→ {res['verdict']}")
    return res


def stat_files(a: str, b: str) -> tuple[str, str]:
    def desc(t: str) -> str:
        return f"{len(t.encode('utf-8'))}B"
    return (f"原文 {desc(a)}", f"原文 {desc(b)}")


def save_report(name: str, res: dict) -> None:
    report = {}
    if REPORT.is_file():
        try:
            report = json.loads(REPORT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report = {}
    report[name] = res
    SOURCES.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")


# ── 自证 ────────────────────────────────────────────────────────────────────

def selftest() -> int:
    """正例＝同文自比必须≈1.0；负例＝两部不同的书必须判"对不上"。

    这是对本工具自身的负例自证（AGENTS §四.8 纪律）：防止 matcher 把
    什么都判成一致——"全绿的对勘"要先怀疑、再证明。
    """
    print("自证 1（正例）：同一段文本自比，containment 必须 = 1.0")
    sample = ("凡占卜者，须以体卦为主，用卦为应。体用既分，生克可判；"
              "体衰用旺则凶，体旺用衰则吉。此梅花心易之大纲也。") * 3
    res = compare(sample, sample)
    ok1 = res["containment_primary"] == 1.0 and res["window_hit_rate"] == 1.0
    print(f"    containment={res['containment_primary']} 命中={res['window_hit_rate']} "
          f"{'√ 通过' if ok1 else '× 失败'}")

    print("自证 2（负例）：两部不相干的书互比，必须判「对不上」（<0.15）")
    if not (SOURCES / "zengshan_buyi.wikitext.txt").is_file() or \
       not (SOURCES / "mei-hua-yi-shu.wikitext.txt").is_file():
        print("    × 需要在库文本 zengshan_buyi / mei-hua-yi-shu 作负例底料")
        return 2
    a = load_wiki("zengshan_buyi")
    b = load_wiki("mei-hua-yi-shu")
    res = compare(a, b)
    ok2 = res["containment_primary"] < 0.15
    print(f"    containment={res['containment_primary']:.4f} → {res['verdict']} "
          f"{'√ 通过' if ok2 else '× 失败（matcher 把不相干文本判成一致——工具不可信）'}")
    return 0 if (ok1 and ok2) else 1


# ── CLI ─────────────────────────────────────────────────────────────────────

def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(
        description="跨源对勘器：同书两源转录本的机械一致性比对（落痕 crosscheck_report.json）")
    ap.add_argument("--pairs-table", action="store_true",
                    help="跑内置对勘表全部书对（维基文库 ↔ 殆知阁）")
    ap.add_argument("--pair", nargs=2, metavar=("WIKI_KEY", "DZ_KEY"),
                    help="对勘指定一对（key 见 tools/fetch_source.py --list）")
    ap.add_argument("--file", nargs=2, metavar=("A", "B"),
                    help="对勘任意两个文本文件（配 --name）")
    ap.add_argument("--name", help="--file 模式的报告键名")
    ap.add_argument("--selftest", action="store_true",
                    help="正/负例自证：同文=1.0，异书=<0.15")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    results: dict[str, dict] = {}
    if args.pairs_table:
        for wiki_key, dz_key in PAIRS_TABLE:
            try:
                res = crosscheck(wiki_key, load_wiki(wiki_key), load_dz(dz_key),
                                 meta={"primary_key": wiki_key, "secondary_key": dz_key,
                                       "primary_site": "zh.wikisource.org",
                                       "secondary_site": "github.com/garychowcmu/daizhigev20"})
            except SystemExit as exc:
                print(f"  {wiki_key}: 跳过（{exc}）")
                continue
            results[wiki_key] = res
            save_report(wiki_key, res)
    elif args.pair:
        wiki_key, dz_key = args.pair
        res = crosscheck(wiki_key, load_wiki(wiki_key), load_dz(dz_key),
                         meta={"primary_key": wiki_key, "secondary_key": dz_key,
                               "primary_site": "zh.wikisource.org",
                               "secondary_site": "github.com/garychowcmu/daizhigev20"})
        results[wiki_key] = res
        save_report(wiki_key, res)
    elif args.file:
        a, b = (Path(p).read_text(encoding="utf-8") for p in args.file)
        name = args.name or f"custom::{Path(args.file[0]).stem}~{Path(args.file[1]).stem}"
        res = crosscheck(name, a, b, meta={"primary": args.file[0], "secondary": args.file[1]})
        results[name] = res
        save_report(name, res)
    else:
        ap.error("给 --pairs-table / --pair / --file，或 --selftest")

    n_ok = sum(1 for r in results.values() if r["containment_primary"] >= 0.5)
    print(f"\n完成 {len(results)} 对：基本一致以上 {n_ok} 对；"
          f"报告 → {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
