# -*- coding: utf-8 -*-
"""《穷通宝鉴》调候用神表构建器（一次性数据构建，产物入库、脚本留档可复跑）。

输入  data/sources/qiong-tong-bao-jian.wikitext.txt（维基文库原文，provenance 同目录）
输出  data/tiaohou_quotes.json   逐格 {main, assist, quote, section}——引文逐字保留，
                                铁律三口径：expected 必须能指回原文。
      stdout                     全表人审清单（月支 × 日干 → 主/佐 + 引文摘句）

提取规则（宁缺勿滥）：
  1. 按 `== 论X干 ==` 切分为每干大段；大段内再按 `=== 三X X干 ===` 记录季节段。
  2. 每 (月令, 日主) 取用神，优先级：
       a) 精确 `'''N月X干'''` 头（含其后 1-2 行 prose）命中即停；
       b) 该干大段内**逐句**检索明确提及该月词的句子（如「正月…」「冬月…」），
          命中即停（避免把别月处方错归到本月）；
       c) 季节段兜底：季节总论句（无月词）用于整季三个月（via=season，已知可能过泛，
          仅在前两步均无果时使用，且交付层与穷通外集批会校验）。
  3. 禁止从引擎口径反推——本脚本只读原文；引文必须为原文子串（自动校验）。
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
MONTH_WORD = {1: "正", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六",
              7: "七", 8: "八", 9: "九", 10: "十", 11: "冬", 12: "腊"}
SEASON = {"三春": [1, 2, 3], "三夏": [4, 5, 6], "三秋": [7, 8, 9], "三冬": [10, 11, 12]}
BRANCH_OF_MONTH = {1: "寅", 2: "卯", 3: "辰", 4: "巳", 5: "午", 6: "未",
                   7: "申", 8: "酉", 9: "戌", 10: "亥", 11: "子", 12: "丑"}

# ---- 用神句模式（有序，命中即停）。十干单字 + 可选五行字缓冲。 ----
S = STEM_RE
PATTERNS = [
    (re.compile(rf"先({S})后({S})"), "先X后Y"),
    (re.compile(rf"先取({S})[^，。；]*，次[用取]({S})"), "先取X次Y"),
    (re.compile(rf"({S})[火木土金水]为尊，[^，。；]*({S})[火木土金水]次之"), "X为尊Y次之"),
    (re.compile(rf"({S})[火木土金水]为先，次[用取]({S})"), "X为先次Y"),
    (re.compile(rf"({S})[火木土金水]为主，[^，。；]*({S})[火木土金水]为佐"), "X主Y佐"),
    (re.compile(rf"用({S})[火木土金水]?，[^，。；]*佐以({S})"), "用X佐Y"),
    (re.compile(rf"({S})({S})两透"), "XY两透"),
    (re.compile(rf"得({S})({S})"), "得XY"),
    (re.compile(rf"({S})({S})并用"), "XY并用"),
    (re.compile(rf"({S})({S})兼全"), "XY兼全"),
    (re.compile(rf"(?:专|耑)(?:用|以|取)?({S})[火木土金水]?"), "专用X"),
    (re.compile(rf"({S})[火木土金水]为用"), "X为用"),
    (re.compile(rf"独爱({S})[火木土金水]?"), "独爱X"),
]


def try_extract(text: str):
    for pat, name in PATTERNS:
        m = pat.search(text)
        if m:
            main = m.group(1)
            assist = m.group(2) if pat.groups >= 2 else ""
            return main, assist, name
    return None, None, None


def month_num_from_word(token: str) -> int | None:
    if token == "十一":
        return 11
    if token == "十二":
        return 12
    if token == "冬":
        return 11
    if token == "腊":
        return 12
    return MONTH_NAMES.get(token)


def mentions_month(sent: str, month: int) -> bool:
    """句子是否明确提及该月令（用于精确归属，避免错归）。"""
    if month <= 9:
        return f"{MONTH_WORD[month]}月" in sent
    if month == 10:
        return "十月" in sent
    if month == 11:
        return "冬月" in sent or "十一月" in sent
    if month == 12:
        return "腊月" in sent or "十二月" in sent
    return False


def split_sentences(block: str) -> list[str]:
    return [s for s in re.split(r"[。；;！!？?]", block) if s.strip()]


# 显式月词（用于季节兜底时剔除「含具体月份」的句子，避免把某月专属句错归到同季另两月）。
# 负向回顾 (?<!十) 防止「十二月」被误判含「二月」。
MONTH_TOKEN_RE = re.compile(
    r"(?<!十)(正月|二月|三月|四月|五月|六月|七月|八月|九月|十月|冬月|十一月|十二月|腊月)"
)


def _has_month_word(sent: str) -> bool:
    return bool(MONTH_TOKEN_RE.search(sent))


# 维基文库示例盘（{| class="wikitable" … |}）里夹着大量「庚壬两透」一类成药例，
# 不是该月令的用神处方；检索前整段剔除，避免把示例误当处方。
WIKITABLE_RE = re.compile(r"\{\|.*?\|\}", re.S)


def _clean_block(text: str) -> str:
    return WIKITABLE_RE.sub(" ", text)


def build_table() -> dict:
    """书源 → 12 月 × 10 干 的调候引文表（纯计算，不落盘）。"""
    text = SRC.read_text(encoding="utf-8")
    lines = text.splitlines()

    cur_stem, cur_season = "", ""
    blocks: dict[str, list[str]] = {s: [] for s in STEMS}
    # 精确 `'''N月X干'''` 头 → 该头下的逐句原文（已逐句切分，保证每条 quote 是原文子串）
    exact_paras: dict[tuple[int, str], list[str]] = {}
    season_for_stem: dict[str, str] = {}

    for idx, ln in enumerate(lines):
        m = re.match(rf"^==\s*论([{STEMS}])[{ELEMENT_CHAR}]?\s*==\s*$", ln.strip())
        if m:
            cur_stem, cur_season = m.group(1), ""
            continue
        m = re.match(r"^===\s*(三[春夏秋冬])", ln.strip())
        if m:
            cur_season = m.group(1)
            season_for_stem[cur_stem] = cur_season
            continue
        if cur_stem:
            blocks[cur_stem].append(ln)
        # 精确 `'''N月X干'''` 头：收集该头所在行剩余文本 + 其后 1-2 行 prose，逐句切分
        # （跳过示例盘表格行，避免把成药例误当处方）
        hm = re.match(
            rf"^'''([正二三四五六七八九十冬腊]+)月([{STEMS}])[{ELEMENT_CHAR}]?'''\s*(.*)$",
            ln.strip(),
        )
        if hm:
            num = month_num_from_word(hm.group(1))
            stem = hm.group(2)
            if num is None:
                continue
            sents: list[str] = []
            if hm.group(3).strip():
                sents.append(hm.group(3).strip())
            j = idx + 1
            while j < len(lines) and len(sents) < 3 and lines[j].strip() \
                    and not lines[j].strip().startswith("'''") \
                    and not lines[j].strip().startswith("==") \
                    and not lines[j].strip().startswith(("|", "{|", "|}")):
                sents.append(lines[j].strip())
                j += 1
            exact_paras.setdefault((num, stem), []).extend(sents)

    table: dict[str, dict] = {}
    for month in range(1, 13):
        mw = MONTH_WORD[month]
        branch = BRANCH_OF_MONTH[month]
        for stem in STEMS:
            # 键 = 月序+日干（如 "4乙"）：**消费方契约**——narrate.py `_tiaohou_quote`
            # 与 core/yishu_core/evidence.py 均按「月序+日干」回索引文（见 evidence.py
            # 注释「引文按月序+日干键回指」）。注意这与引擎 TIAO_HOU 的「月支+日干」
            # 键空间不同，勿混。month 字段保留月支信息供人审。
            key = f"{month}{stem}"
            main = assist = ""
            how = ""
            quote = None
            section = None
            exact_flag = False

            # a) 精确头（逐句，命中即停）
            for sent in exact_paras.get((month, stem), []):
                mm, aa, nn = try_extract(sent)
                if mm:
                    main, assist, how = mm, aa, nn
                    quote = sent
                    section = f"论{stem}·{mw}月"
                    exact_flag = True
                    break
            # b) 大段内逐句按月词检索（剔除示例盘后检索，保证 quote 是原文逐字子串）
            if not main:
                for s in split_sentences(_clean_block("\n".join(blocks[stem]))):
                    if mentions_month(s, month):
                        mm, aa, nn = try_extract(s)
                        if mm:
                            main, assist, how = mm, aa, nn
                            quote = s.strip()
                            section = f"论{stem}（{season_for_stem.get(stem, '')}）"
                            break
            # c) 季节段兜底（仅前两步均无果，且只用「整季总论句」——不含任何月词，
            #    避免把某月专属句错归到同季另两月）。优先选能给出「主+佐」的整季句，
            #    因季节总论常先点主神、后补佐神，首句可能只点主神。
            if not main:
                seas = season_for_stem.get(stem, "")
                if seas and month in SEASON.get(seas, []):
                    best = None  # (has_assist, main, assist, how, quote)
                    for s in split_sentences(_clean_block("\n".join(blocks[stem]))):
                        if _has_month_word(s):
                            continue
                        mm, aa, nn = try_extract(s)
                        if mm and (best is None or (not best[0] and aa)):
                            best = (bool(aa), mm, aa, nn, s.strip())
                    if best:
                        main, assist, how = best[1], best[2], best[3]
                        quote = best[4]
                        section = f"论{stem}·{seas}（季节总论，过泛慎用）"
                        how = (how or "") + "(season)"

            table[key] = {
                "month": month, "branch": branch, "stem": stem,
                "main": main or None, "assist": assist or None,
                # 引文保留完整原句（铁律三：必须能指回原文子串，截断会破坏可验证性）
                "quote": quote,
                "section": section, "via": how or None,
                "exact_paragraph": exact_flag,
            }

    # 引文可验证性自校验：任何 quote 必须能在原文中逐字找到，否则视为臆造，强制置空
    # （宁缺勿滥）。本步在 build_table 内完成，保证 --check 与落盘产物完全一致、可复现。
    src = SRC.read_text(encoding="utf-8")
    for k, v in table.items():
        if v.get("quote") and v["quote"] not in src:
            v["main"] = v["assist"] = None
            v["quote"] = v["via"] = None
            v["exact_paragraph"] = False

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

    # 人审清单
    ok = sum(1 for v in table.values() if v["main"])
    season = sum(1 for v in table.values() if v["main"] and (v["via"] or "").endswith("(season)"))
    print(f"提取 120 格，命中主神 {ok} 格，N/A {120 - ok} 格 → {OUT.name}")
    print(f"（其中季节兜底 {season} 格，via 标记 season，已知可能过泛）")
    # 人审清单（按月支分组显示，键为月序+日干）
    for month in range(1, 13):
        br = BRANCH_OF_MONTH[month]
        row = []
        for stem in STEMS:
            v = table.get(f"{month}{stem}")
            if not v or not v["main"]:
                row.append(f"{stem}:—")
            else:
                tag = "" if v["exact_paragraph"] else ("~" if (v["via"] or "").endswith("(season)") else "·")
                row.append(f"{stem}:{v['main']}{('/' + v['assist']) if v['assist'] else ''}{tag}")
        print(f"  {br}({month})  " + "  ".join(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
