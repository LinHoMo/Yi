# -*- coding: utf-8 -*-
"""对 120 格做「缺口归因」：每一格的书源月头来源与状态分类。只读。

状态分类：
  exact      书源有该 月×干 精确月头
  merged     书源只有合并/季节月头（如 五六月甲木 / 三秋甲木 / 十一二月）
  nosrc      书源确无该 月×干 任何月头
并对 merged / nosrc 分别给出书源可用的最近替代段落行号，便于人工判断。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "core"))
# 干支序列与五行字唯一真值源在 core，此处只导入不复制（tools/check.py 第 6 项门禁会拦复制）
from yishu_core.symbols import HEAVENLY_STEMS, STEM_ELEMENTS  # noqa: E402

SRC = ROOT / "data" / "sources" / "qiong-tong-bao-jian.wikitext.txt"
QJSON = ROOT / "disciplines" / "ming" / "data" / "tiaohou_quotes.json"

STEMS = "".join(HEAVENLY_STEMS)  # HEAVENLY_STEMS 是 list，插进字符类前须展平
E = "".join(dict.fromkeys(STEM_ELEMENTS.values()))  # 木火土金水
MONTHS = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]
# 引擎键用阿拉伯月序（1..12），书源用中文月名。必须全量映射，
# 只映射 {1,11,12} 会把 3 错成 "3" 从而全表落进 nosrc 桶。
W = {
    "1": "正", "2": "二", "3": "三", "4": "四", "5": "五", "6": "六",
    "7": "七", "8": "八", "9": "九", "10": "十", "11": "十一", "12": "十二",
}

STRICT = re.compile(r"^'''(十一|十二|[正二三四五六七八九十冬腊])月([" + STEMS + r"])[" + E + r"]?'''")
LOOSE_A = re.compile(r"^'''(十一|十二|[正二三四五六七八九十冬腊])月(?:之)?([" + STEMS + r"])[" + E + r"]?'''")
LOOSE_B = re.compile(r"^'''(十一|十二|[正二三四五六七八九十冬腊])月'''([" + STEMS + r"])")
# 合并月头：'''五六月甲木''' '''正二月甲木''' '''十一二月'''(无干) '''三秋甲木'''(季节)
MERGED = re.compile(r"^'''(十一二月|[正二五]?[十]?[一二]?月)([" + STEMS + r"])?[" + E + r"]?'''")
SEASON = re.compile(r"^'''(三[春夏秋冬][春夏秋冬]?)([" + STEMS + r"])[" + E + r"]?'''")


def main() -> None:
    lines = SRC.read_text(encoding="utf-8").splitlines()
    data = json.loads(QJSON.read_text(encoding="utf-8"))

    exact, merged, season = {}, [], []
    for i, ln in enumerate(lines):
        t = ln.strip()
        m = STRICT.match(t) or LOOSE_A.match(t) or LOOSE_B.match(t)
        if m:
            exact[(m.group(1), m.group(2))] = i + 1
            continue
        m = SEASON.match(t)
        if m:
            season.append((i + 1, m.group(1), m.group(2)))
            continue
        m = MERGED.match(t)
        if m:
            merged.append((i + 1, m.group(1), m.group(2)))

    print(f"精确月头 {len(exact)}   合并月头 {len(merged)}   季节月头 {len(season)}\n")
    print("=== 合并月头 ===")
    for ln, mo, st in merged:
        print(f"  行{ln:5} {mo}{st or '(无干)'}  {lines[ln - 1].strip()[:120]}")
    print("\n=== 季节月头 ===")
    for ln, mo, st in season:
        print(f"  行{ln:5} {mo}{st}  {lines[ln - 1].strip()[:120]}")

    buckets = {"exact": [], "merged": [], "season": [], "nosrc": []}
    for k, v in sorted(data.items()):
        mo_n, st = k[:-1], k[-1]
        w = W.get(mo_n, mo_n)
        if (w, st) in exact:
            buckets["exact"].append(k)
            continue
        hit_m = [x for x in merged if x[2] == st and (x[1].startswith(w[:1]) or w in x[1])]
        hit_s = [x for x in season if x[2] == st]
        if hit_m:
            buckets["merged"].append((k, hit_m[0]))
        elif hit_s:
            buckets["season"].append((k, hit_s[0]))
        else:
            buckets["nosrc"].append(k)

    print("\n=== 120 格状态分桶 ===")
    for b in ("exact", "merged", "season", "nosrc"):
        print(f"  {b:7}: {len(buckets[b])}")

    print(f"\n=== 合并月头可覆盖但当前为空的格（{len(buckets['merged'])}）===")
    for k, src in buckets["merged"]:
        v = data[k]
        flag = "★空" if not v.get("main") else "有值"
        print(f"  {k} [{flag}] ← 合并月头 行{src[0]} {src[1]}{src[2] or ''}")

    print(f"\n=== 季节月头可覆盖但当前为空的格（{len(buckets['season'])}）===")
    for k, src in buckets["season"]:
        v = data[k]
        flag = "★空" if not v.get("main") else "有值"
        print(f"  {k} [{flag}] ← 季节月头 行{src[0]} {src[1]}{src[2]}")

    print(f"\n=== 书源真无任何月头的格（{len(buckets['nosrc'])}）===")
    print(" ", " ".join(buckets["nosrc"]))

    # 剩余空缺格的**逐格定性**。空缺不等于同一种原因，必须分开记账，
    # 否则会把「书源没写」和「书源写了但只讲格局/从格」混为一谈。
    na = [k for k, v in sorted(data.items()) if not v.get("main")]
    print(f"\n=== 剩余空缺格逐格定性（{len(na)} 格）===")
    for k in na:
        mo_n, st = k[:-1], k[-1]
        w = W.get(mo_n, mo_n)
        ln = exact.get((w, st))
        if not ln:
            print(f"  {k}  [书源无月头]  该月该日干在书源中无任何 `'''N月X干'''` 标题")
            continue
        text = lines[ln - 1].strip()
        tag = "从格判据" if ("从杀" in text or "从财" in text or "从化" in text) else "只讲格局/否定"
        print(f"  {k}  [{tag}]  行{ln}")
        print(f"        {text[:150]}")

    print("\n口径说明：以上空缺一律**不再补格**。理由分三类——")
    print("  1) 书源无该月该日干标题 → 真实缺口，无明文可采（宁缺勿滥）")
    print("  2) 书源该段只讲成格条件/富贵成败/从格判据，未给调候处方 → 无明文可采")
    print("  3) 书源明写否定（如「不宜乱用甲木」）或随宜命题（如「随宜酌用」）")
    print("     → 主动留空是**正确行为**，补格反而违背口径诚实")
    print("  异源补格（用滴天髓阐微等）会造成两书标准混用，故不做。")


if __name__ == "__main__":
    main()
