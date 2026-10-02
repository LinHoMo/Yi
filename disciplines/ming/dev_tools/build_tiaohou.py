# -*- coding: utf-8 -*-
"""《穷通宝鉴》调候用神表构建器（一次性数据构建，产物入库、脚本留档可复跑）。

输入  data/sources/qiong-tong-bao-jian.wikitext.txt（维基文库原文，provenance 同目录）
输出  data/tiaohou_quotes.json   逐格 {main, assist, quote, section}——引文逐字保留，
                                铁律三口径：expected 必须能指回原文。
      stdout                     全表人审清单（月支 × 日干 → 主/佐 + 引文摘句）

提取规则（宁缺勿滥）：
  1. 只认 '''N月X干''' 段首；精确月段优先于合月段（正二月/五六月/三春X干…）。
  2. 只在段首两句话内找用神句，命中一组即停；命中不了的格**不产 main**（N/A），
     引文仍保留供人工补录。
  3. 禁止从引擎口径反推——本脚本只读原文。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
# 内核路径必须由 DISC 反推（`Path(__file__).parents[2]` 会落到 `disciplines/` 而非仓库根，
# 在未 `pip install -e .` 的环境里直接 ModuleNotFoundError——本脚本此前正是如此）。
sys.path.insert(0, str(DISC.parent.parent / "core"))
from yishu_core.symbols import HEAVENLY_STEMS  # noqa: E402  天干序唯一真值源
from yishu_core import corpus_kit  # noqa: E402  语料可复现性比对
SRC = DISC.parent.parent / "data" / "sources" / "qiong-tong-bao-jian.wikitext.txt"
OUT = DISC / "data" / "tiaohou_quotes.json"

# `HEAVENLY_STEMS` 是 **list**：直接 f-string 插进字符类会变成
# `['甲', '乙', …, '癸']]` —— 类在首个 `]` 处提前闭合，多出一个必须匹配的字面 `]`，
# 于是「== 论癸水 ==」这类标题**永远不匹配**（实测采集到 0 段、重跑会把整个
# tiaohou_quotes.json 写成 120 个空格）。必须先 "".join 成字符串（同 ming 另一建器口径）。
STEMS = "".join(HEAVENLY_STEMS)
STEM_RE = f"[{STEMS}]"
MONTH_NAMES = {"正": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
               "七": 7, "八": 8, "九": 9, "十": 10, "冬": 11, "腊": 12}
ELEMENT_CHAR = "木火土金水"

# ---- 段首标记：'''正月甲木''' / '''五六月甲木''' / '''三秋甲木''' / '''十冬月甲木''' 等
HEADER_RE = re.compile(r"'''([^']+?)'''")

# ---- 用神句模式（有序，命中即停）。十干单字 + 可选五行字缓冲。 ----
S = STEM_RE
PATTERNS = [
    # 先癸后丁 / 先取庚金，次用壬水 / 丁火为尊，庚金次之 / 丁火为先，次用丙火
    (re.compile(rf"先({S})后({S})"), "先X后Y"),
    (re.compile(rf"先取({S})[^，。；]*，次[用取]({S})"), "先取X次用Y"),
    (re.compile(rf"({S})[火木土金水]为尊，[^，。；]*({S})[火木土金水]次之"), "X为尊Y次之"),
    (re.compile(rf"({S})[火木土金水]为先，次[用取]({S})"), "X为先次Y"),
    # X为主，Y为佐 / 用X，以Y为佐
    (re.compile(rf"({S})[火木土金水]为主，[^，。；]*({S})[火木土金水]为佐"), "X主Y佐"),
    (re.compile(rf"用({S})[火木土金水]?，[^，。；]*佐以({S})"), "用X佐Y"),
    # 得丙癸逢 / 得癸丁两透 / X Y 两透 / X Y 并用 / X Y 兼备
    (re.compile(rf"得({S})({S})"), "得XY"),
    (re.compile(rf"({S})({S})两透"), "XY两透"),
    (re.compile(rf"({S})({S})并用"), "XY并用"),
    (re.compile(rf"({S})({S})兼全"), "XY兼全"),
    # 单主神：专用X / X为用 / 当以X为先
    (re.compile(rf"专(?:用|以)({S})[火木土金水]?"), "专用X"),
    (re.compile(rf"({S})[火木土金水]为用"), "X为用"),
    (re.compile(rf"独爱({S})[火木土金水]?"), "独爱X"),
]


def month_nums(header: str) -> list[int]:
    """段首月份标记 → 月序列表（精确月 or 合月段）。

    接受：'''正月甲木''' '''五六月甲木''' '''十冬月甲木''' '''三春甲木''' 等。
    段首结构 = [月份字一至两个]月[日干][五行字]，季节段 = 三春/三夏/三秋/三冬 + 干木。
    """
    if header.startswith("三春"):
        return [1, 2, 3]
    if header.startswith("三夏"):
        return [4, 5, 6]
    if header.startswith("三秋"):
        return [7, 8, 9]
    if header.startswith("三冬"):
        return [10, 11, 12]
    m = re.match(rf"^([正二三四五六七八九十冬腊]+)月[{STEMS}][{ELEMENT_CHAR}]?$", header)
    if not m:
        return []
    token = m.group(1)
    if token == "十一":
        return [11]
    if token == "十二":
        return [12]
    return [MONTH_NAMES[c] for c in token if c in MONTH_NAMES]


def build_table() -> dict:
    """书源 → 12 月 × 10 干 的调候引文表（纯计算，不落盘）。"""
    text = SRC.read_text(encoding="utf-8")
    lines = text.splitlines()

    # 1) 收集段落：current stem / season 由 == 论X干 == 与 === 三X X干 === 行推进
    cur_stem, cur_season = "", ""
    paragraphs: list[dict] = []
    for ln in lines:
        m = re.match(rf"^==\s*论([{STEMS}])[{ELEMENT_CHAR}]\s*==\s*$", ln.strip())
        if m:
            cur_stem, cur_season = m.group(1), ""
            continue
        m = re.match(r"^===\s*(三[春夏秋冬])", ln.strip())
        if m:
            cur_season = m.group(1)
            continue
        if "'''" in ln:
            for h in HEADER_RE.findall(ln):
                nums = month_nums(h)
                stem = h[-1] if h[-1] in STEMS else cur_stem
                if nums and stem:
                    paragraphs.append({
                        "header": h, "stem": stem, "months": nums,
                        "season": cur_season, "text": ln,
                    })

    # 2) 逐格取最具体段落（精确月 > 合月段 > 季节泛段），提取用神
    table: dict[str, dict] = {}
    for month in range(1, 13):
        for stem in STEMS:
            cands = [p for p in paragraphs if p["stem"] == stem and month in p["months"]]
            if not cands:
                table[f"{month}{stem}"] = {
                    "month": month, "stem": stem, "main": None, "assist": None,
                    "quote": None, "section": None, "via": None,
                    "exact_paragraph": False, "no_paragraph": True,
                }
                continue
            exact = [p for p in cands if p["months"] == [month]]
            para = (exact or cands)[0]
            body = HEADER_RE.sub("", para["text"], count=1).strip("，。 ")
            # 合月段（正二月/五六月/三秋…）必须命中"提及该月"的句子才提取，
            # 否则五月用神会错归属到六月（宁缺勿滥）。
            cn = {1: "正", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六",
                  7: "七", 8: "八", 9: "九", 10: "十", 11: "冬", 12: "腊"}[month]
            if len(para["months"]) > 1:
                mentions = [s for s in body.split("。") if f"{cn}月" in s]
                if not mentions:
                    table[f"{month}{stem}"] = {
                        "month": month, "stem": stem, "main": None, "assist": None,
                        "quote": body[:120], "section": f"论{stem}（{para['season']}）",
                        "via": None, "exact_paragraph": bool(exact),
                        "skipped": "合月段未逐月分句",
                    }
                    continue
                head = "。".join(mentions[:2])
            else:
                # 只看段首两句话
                head = "。".join(body.split("。")[:2])
            main = assist = ""
            how = ""
            for pat, name in PATTERNS:
                m = pat.search(head)
                if m:
                    main, how = m.group(1), name
                    if pat.groups == 2:
                        assist = m.group(2)
                    break
            table[f"{month}{stem}"] = {
                "month": month, "stem": stem,
                "main": main or None, "assist": assist or None,
                "quote": body[:120], "section": f"论{stem}（{para['season']}）",
                "via": how or None, "exact_paragraph": bool(exact),
            }

    return table


def main() -> int:
    ap = argparse.ArgumentParser(description="《穷通宝鉴》调候用神引文层提取（默认写盘）")
    ap.add_argument("--check", action="store_true",
                    help="不落盘，只比对已入库 data/tiaohou_quotes.json 是否与重算一致")
    args = ap.parse_args()

    table = build_table()
    if args.check:
        return corpus_kit.report(OUT.name, corpus_kit.check(OUT, table))

    OUT.write_text(json.dumps(table, ensure_ascii=False, indent=1), encoding="utf-8")

    # 3) 人审清单
    ok = sum(1 for v in table.values() if v["main"])
    print(f"提取 {len(table)} 格，命中主神 {ok} 格，N/A {len(table) - ok} 格 → {OUT.name}")
    for month in range(1, 13):
        row = []
        for stem in STEMS:
            v = table[f"{month}{stem}"]
            row.append(f"{stem}:{v['main'] or '—'}{('/' + v['assist']) if v['assist'] else ''}"
                       f"{'' if v['exact_paragraph'] else '(泛)'}")
        print(f"  {month:>2}月  " + "  ".join(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
