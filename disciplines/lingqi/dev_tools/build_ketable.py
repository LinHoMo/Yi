# -*- coding: utf-8 -*-
"""灵棋经课表提取器（数据构建，产物入库、脚本留档可复跑）。

    python dev_tools/build_ketable.py [--write]

源：`data/sources/ling-qi-jing.wikitext.txt`（维基文库《靈棋經》，provenance 同目录）。
结构：124 个课标题 `==X上Y中Z下==`（X/Y/Z ∈ 一..四，缺字 = 该部 0 枚；全零不成课），
每课头部三行（课名行「大通卦 升騰之象」/ 卦注行「純陽得令 乾天西北」），
其后是若干**标注组**：象曰 / 詩曰 / 又 / 又曰 / 許曰（各带自己的标注名与书目原文），
源内亦有个别课把标注分隔符写成「，」「；」（不齐不静默，见下）。

保真要求（本脚本内置断言，任一不成立即拒绝写入）：
  1. 124 课、键集合 = 全部非零三部组合、课名齐全且唯一；
  2. 每课 name/xiang/zhu 齐全，**恰有一组「象曰」**，且每组至少一行；
  3. 卦宫（卦注末段，如「乾天西北」）恰 **8** 种，全部由书源卦注归纳（不另立卦宫表）；
  4. **引文可回指**：每个入库字符串去掉空白后必须是书源连续子串；
  5. 非课标题的章节（如书末 `==純陰饅==`，全陰不成课）**显式登记到 appendix**，
     不再静默并入相邻课正文。

产物 `data/ketables.json`（schema `yi-lingqi-ketable/2`）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
SRC = DISC.parents[1] / "data" / "sources" / "ling-qi-jing.wikitext.txt"
OUT = DISC / "data" / "ketables.json"

sys.path.insert(0, str(DISC.parents[1] / "core"))
from yishu_core import corpus_kit  # noqa: E402  语料可复现性比对

CN = {"一": 1, "二": 2, "三": 3, "四": 4}
HEAD_RE = re.compile(r"^=+\s*(.+?)\s*=+$")
KE_ONLY = re.compile(r"^[一二三四上中下]+$")
# 标注分隔符：源内以「：」为主，个别课写作「，」「；」——一律认作标注行
MARK_RE = re.compile(r"^(象曰|詩曰|诗曰|又曰|又|許曰)\s*[：:，；]?\s*(.*)$")
# 卦宫：八卦 × 象 × 方位（正東/西北/東南…），由书源卦注归纳，本文件不另立表。
# 书源「兌」两见（兌澤正西 / 兌金正西），异文保留原样，八宫齐以卦名首字判。
GONG_RE = re.compile(r"[乾兌離震巽坎艮坤][天澤金火雷風水山地](?:正[東西南北]|[東西南北]{2})")


def _counts(units: list[tuple[str, str]]) -> dict[str, int]:
    counts = {"上": 0, "中": 0, "下": 0}
    for num, pos in units:
        counts[pos] = sum(CN[ch] for ch in num) if num else 0
    return counts


def _split_head(head_lines: list[str]) -> tuple[str, str, str, list[str]]:
    """头部三行 → (课名, 象, 卦注, 未归类行)。未归类行不静默丢弃，交调用方报问题。"""
    name = xiang = zhu = ""
    rest: list[str] = []
    for l in head_lines:
        if not name and "之象" in l:
            left, _, right = l.partition(" ")
            name, xiang = left.strip(), right.strip()
            continue
        if not name and l.endswith(("卦", "勢", "教")):
            name = l
            continue
        if not zhu:
            zhu = l
            continue
        rest.append(l)
    return name, xiang, zhu, rest


def _parse_block(body: list[str]) -> tuple[str, str, str, list[str], list[dict]]:
    """一个标题块 → (课名, 象, 卦注, 未归类行, 标注组)。"""
    head_lines: list[str] = []
    notes: list[dict] = []
    for l in body:
        m = MARK_RE.match(l)
        if m:
            text = m.group(2).strip()
            notes.append({"mark": m.group(1), "lines": [text] if text else []})
            continue
        if notes:
            notes[-1]["lines"].append(l)
            continue
        head_lines.append(l)
    name, xiang, zhu, rest = _split_head(head_lines)
    return name, xiang, zhu, rest, notes


def _gong_of(*texts: str) -> str:
    for t in texts:
        m = GONG_RE.search(t)
        if m:
            return m.group(0)
    return ""


def build() -> tuple[dict, list[str]]:
    text = SRC.read_text(encoding="utf-8")
    lines = text.splitlines()
    flat = re.sub(r"\s+", "", text)          # 引文可回指用的空白归一底本

    heads: list[tuple[int, bool, str]] = []   # (行号, 是否课标题, 标题文字)
    for i, raw in enumerate(lines):
        m = HEAD_RE.match(raw.strip())
        if not m:
            continue
        title = m.group(1)
        heads.append((i, bool(KE_ONLY.match(title)), title))

    courses: dict[str, dict] = {}
    appendix: list[dict] = []
    problems: list[str] = []

    for idx, (i, is_ke, title) in enumerate(heads):
        end = heads[idx + 1][0] if idx + 1 < len(heads) else len(lines)
        body = [l.strip() for l in lines[i + 1:end] if l.strip()]
        name, xiang, zhu, rest, notes = _parse_block(body)
        gong = _gong_of(zhu, title)

        if not is_ke:                          # 非课标题章节：显式登记，不并入相邻课
            if not notes and not name:
                continue
            appendix.append({
                "title": title, "name": name, "xiang": xiang, "zhu": zhu,
                "gong": gong, "notes": notes,
                "note": "书源非课标题章节，按原文存档；不成课（三部皆无面），不参与查表",
            })
            continue

        units = re.findall(r"([一二三四]*)([上中下])", title)
        if len(units) != len(set(u[1] for u in units)):
            problems.append(f"{title}: 部位重复，非课标题")
            continue
        counts = _counts(units)
        if not any(counts.values()):
            problems.append(f"{title}: 三部全零，不成课（应入 appendix）")
            continue
        key = f"{counts['上']}-{counts['中']}-{counts['下']}"
        if key in courses:
            problems.append(f"{title}: 课键 {key} 重复")
        if rest:
            problems.append(f"{title}: 头部存在未归类行 {rest[:2]}")
        courses[key] = {"name": name, "xiang": xiang, "zhu": zhu, "gong": gong,
                        "notes": notes}

    # —— 内置断言（任一不成立即不写盘）——
    expect_keys = {f"{u}-{m}-{d}" for u in range(5) for m in range(5)
                   for d in range(5) if (u, m, d) != (0, 0, 0)}
    if len(courses) != 124 or set(courses) != expect_keys:
        problems.append(f"课表 {len(courses)} 条 ≠ 124 或键集合不匹配"
                        f"（缺 {sorted(expect_keys - set(courses))[:5]}）")
    names = [v["name"] for v in courses.values()]
    dup = sorted({n for n in names if names.count(n) > 1})
    if dup:
        problems.append(f"课名重复: {dup[:5]}")
    for k, v in courses.items():
        if not (v["name"] and v["xiang"] and v["zhu"]):
            problems.append(f"{k}: 缺 name/xiang/zhu")
        if not v["gong"]:
            problems.append(f"{k}: 卦注未含卦宫（如「乾天西北」）")
        marks = [g["mark"] for g in v["notes"]]
        if marks.count("象曰") != 1:
            problems.append(f"{k}: 象曰组数 {marks.count('象曰')} ≠ 1（标注序列 {marks}）")
        if not v["notes"]:
            problems.append(f"{k}: 无任何标注组")
        for g in v["notes"]:
            if not g["lines"]:
                problems.append(f"{k}: 标注组「{g['mark']}」无内容")
    gongs = sorted({v["gong"] for v in courses.values()})
    bagua = sorted({g[0] for g in gongs})
    if len(bagua) != 8:
        problems.append(f"卦宫八卦 {len(bagua)} 种 ≠ 8：{bagua}")
    if any(not GONG_RE.fullmatch(g) for g in gongs):
        problems.append(f"卦宫有非「卦+象+方位」形制者：{[g for g in gongs if not GONG_RE.fullmatch(g)]}")

    # 引文可回指（去掉空白后必须是书源连续子串）
    def chk(where: str, s: str) -> None:
        if s and re.sub(r"\s+", "", s) not in flat:
            problems.append(f"{where}: 文本不可回指书源 → {s[:24]}")

    for k, v in courses.items():
        chk(f"{k}.name", v["name"])
        chk(f"{k}.xiang", v["xiang"])
        chk(f"{k}.zhu", v["zhu"])
        for gi, g in enumerate(v["notes"]):
            for li, line in enumerate(g["lines"]):
                chk(f"{k}.notes[{gi}]({g['mark']})[{li}]", line)
    for a in appendix:
        chk(f"appendix[{a['title']}].name", a["name"])
        for gi, g in enumerate(a["notes"]):
            for li, line in enumerate(g["lines"]):
                chk(f"appendix[{a['title']}].notes[{gi}][{li}]", line)

    doc = {
        "schema": "yi-lingqi-ketable/2",
        "_comment": [
            "灵棋经 124 课查表（key = 上-中-下 各部面数 0..4，全零不成课）。",
            "name/xiang/zhu/gong + notes（有序标注组：象曰/詩曰/又/又曰/許曰，"
            "标注名随书源原文）全部逐字取自 data/sources/ling-qi-jing.wikitext.txt；",
            "卦宫 gong 由书源卦注归纳（八宫齐，以卦名首字判；「兌」书源两见"
            "「兌澤正西」「兌金正西」，异文保留原样），本仓不另立卦宫表。",
            "铁律三：引文可回指——构建器逐条断言入库文本为书源连续子串。",
            "appendix = 书源内非课标题章节（全陰不成课），存档不参与查表。",
            "narrate/analyze 只查本表，代码零断语字面量。",
        ],
        "problems": problems,
        "gongs": gongs,
        "courses": dict(sorted(courses.items(), key=lambda kv: tuple(
            -int(x) for x in kv[0].split("-")))),
        "appendix": appendix,
    }
    return doc, problems


def main() -> int:
    ap = argparse.ArgumentParser(description="灵棋经课表提取（默认 dry-run）")
    ap.add_argument("--write", action="store_true", help="落盘 data/ketables.json")
    ap.add_argument("--check", action="store_true",
                    help="不落盘，只比对已入库 data/ketables.json 是否与重算一致")
    args = ap.parse_args()

    doc, problems = build()
    courses = doc["courses"]
    marks = sum(len(v["notes"]) for v in courses.values())
    print(f"课表 {len(courses)} 课｜标注组 {marks} 组｜卦宫 {len(doc['gongs'])} 种："
          f"{'、'.join(doc['gongs'])}")
    print(f"附录 {len(doc['appendix'])} 条："
          f"{'、'.join(a['title'] for a in doc['appendix']) or '无'}")
    print(f"问题 {len(problems)} 项：{problems or '无'}")
    if problems:
        print("有断言未过，拒绝写盘。")
        return 1
    if args.check:
        return corpus_kit.report(OUT.name, corpus_kit.check(OUT, doc))
    if not args.write:
        print("dry-run（未写盘）；加 --write 落盘。")
        return 0
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"已写出 → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
