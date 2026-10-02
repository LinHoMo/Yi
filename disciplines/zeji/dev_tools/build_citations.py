# -*- coding: utf-8 -*-
"""择吉·外置书证构建器（《玉匣記》逐字引文，产物入库、脚本留档可复跑）。

    python dev_tools/build_citations.py [--write]

为什么有这份数据：
  择吉科的判据表（建除/黄黑道/二十八宿/彭祖百忌，见 `data/verdicts.json`）来自传统
  通书，但仓库此前**没有任何可核验的公版书证**——报告里只有结论，读者无法回指原书。
  本构建器把《玉匣記》里与各事类/各判据对应的篇目**逐字**摘出，落成
  `data/citations.json`（外置、带篇名与行号出处），由 narrate 附在报告末段供对照。

口径（不得含糊）：
  · 这些引文是**参考书证**，不是本引擎判据的真值源——引擎判据仍只在
    `data/verdicts.json`（唯一真值源），引文不参与评分、不改判据；
  · 引文**逐字**取自书源，构建器逐条断言"是书源某行"（铁律三可回指）；
  · 《協紀辨方書》（本可作择吉口径正源）在维基文库**无公版可抓**（实测 missingtitle），
    如实登记在 `gap`，不以《玉匣記》冒充它。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
SRC = DISC.parents[1] / "data" / "sources" / "yuxiaji.wikitext.txt"
OUT = DISC / "data" / "citations.json"

# 内核（二十八宿名唯一真值源）——构建期结构断言要用
sys.path.insert(0, str(DISC.parents[1] / "core"))
from yishu_core import corpus_kit  # noqa: E402  语料可复现性比对

# 事类 → [(篇名, [该篇内待摘行的前缀, …]), …]
# 行前缀必须在该篇内**唯一命中**，摘出的却是整行原文（不截断、不改字）。
PICKS: dict[str, list[tuple[str, list[str]]]] = {
    # 通则：引擎两项计分判据（黄黑道 + 建除宜忌）在本书的对应歌诀
    "common": [
        ("民俗吉凶日篇　黃黑道用事吉日", [
            "建滿平收黑，除危定執黃",
            "又，黃黑道日當用之事",
            "建宜出行收嫁娶，定直冠帶滿修倉",
            "破除療病執宜捕，危本安床開葬良",
            "成開作所成交吉，平乃作事總平常",
        ]),
    ],
    "嫁娶": [
        ("民俗吉凶日篇　嫁娶不將圖", ["是書雲，凡嫁娶須擇不將吉日"]),
        ("民俗吉凶日篇　嫁娶周堂圖", ["只論月分大小，不問節氣"]),
    ],
    "开市": [
        ("民俗吉凶日篇　開張店肆吉日", ["與開倉、入倉、出寶、藏寶日同用", "甲子，乙丑，丙寅，己巳"]),
        ("民俗吉凶日篇　立契交易吉日", ["辛未，丙子，丁醜"]),
    ],
    "出行": [
        ("民俗吉凶日篇　出行通用吉日", ["甲子，乙丑，丙寅，丁卯", "宜滿、成、開日"]),
        ("民俗吉凶日篇　逐月出行吉凶日", ["黃道日吉，宜出行"]),
    ],
    "入宅": [
        ("民俗吉凶日篇　入宅移居吉日", ["甲子，乙丑，丙寅，戊辰"]),
    ],
    "安葬": [
        ("民俗吉凶日篇　安葬吉日", ["壬申，癸酉，壬午，甲申", "庚午，壬辰，甲辰",
                                     "忌重喪、重複、天賊"]),
        ("民俗吉凶日篇　殯葬日忌二十八宿中七星", ["角、元、奎、婁、鬼、牛、星",
                                                    "忌天火日"]),
    ],
    "动土": [
        ("民俗吉凶日篇　動土開基吉日", ["甲子，癸酉，戊寅", "宜天德、月德、月空",
                                        "忌土瘟、土府、土忌"]),
        ("民俗吉凶日篇　逐月斬草破土吉日", ["正月：丁卯，壬午，庚午"]),
    ],
    "祭祀": [
        ("民俗吉凶日篇　祈祀灶神吉日", ["丁卯，壬申，癸酉，甲戌", "宜除、成、開日"]),
        ("民俗吉凶日篇　天赦、母倉吉日", ["天赦吉日", "母倉吉日"]),
    ],
    "入学": [
        ("民俗吉凶日篇　入學吉日", ["甲戌，乙亥，丙子", "宜平、定、成、開日",
                                    "忌閉、破、先賢死葬"]),
    ],
    "上任": [
        ("民俗吉凶日篇　上官赴任吉日", ["甲子，丙寅，丁卯，戊辰", "忌建、破、平、收"]),
        ("民俗吉凶日篇　臨政親民吉日", ["宜旺、官、民、相、守日"]),
    ],
    "纳财": [
        ("民俗吉凶日篇　出財放債與納財收債吉日", ["納財收債吉日", "乙丑，丙寅，壬午，庚寅"]),
        ("民俗吉凶日篇　五穀入倉吉日", ["庚午己卯，辛巳，壬午"]),
    ],
    "通用": [
        ("民俗吉凶日篇　大明吉日", ["此二十一日，乃天地開通", "辛未，壬申，癸酉"]),
    ],
}

GAP = {
    "book": "《協紀辨方書》（擇吉科口径正源）",
    "status": "维基文库无公版可抓",
    "checked": ["協紀辨方書", "欽定協紀辨方書", "星曆考原", "御定星曆考原", "選擇宗鏡"],
    "result": "全部 missingtitle（tools/fetch_source.py --check 实测）",
    "handling": "以同源通书《玉匣記》作参考书证，不据以新增或修改任何宜忌规则；"
                "判据仍只以 data/verdicts.json 为唯一真值源",
    "basis_note": "本仓判据表 basis 引据属通行口径转述，库内无可核书证，不作逐字书证",
}

# 二十八宿值日吉凶歌（《玉匣記·理論吉凶日篇》）：引擎 `verdicts.json#xiu` 的吉宿/凶宿
# 此前只自述"取通行口径"，库内无书证；本篇把它逐字落库，并由门断言**书证吉凶与判据表一致**。
XIU_SECTION = "理論吉凶日篇　二十八宿值日吉凶歌"
# 书源（繁体）宿名 → 内核 `zeji_tables.XIU_ORDER` 的简体宿名（归化只影响字典键）
XIU_ALIAS = {"虛": "虚", "婁": "娄", "畢": "毕", "參": "参", "張": "张",
             "軫": "轸", "鬥": "斗"}
XIU_HEADER = re.compile(r"^(\S{2,4})[\s\u3000]+(\S{2,3})[\s\u3000]+(吉|凶)\s*$")


def _xiu_verses(lines: list[str], blocks: dict, problems: list[str]) -> dict:
    """二十八宿值日吉凶歌 → {宿: {宿名书源, 值宿神将, 吉凶, 歌诀[], 行号[], 出处}}。

    宿块由表头行（`角木蛟 　鄧禹　吉`）切分；歌诀取表头到下一表头之间的非空行。
    结构性断言：28 宿齐（与内核 XIU_ORDER 同集）、每宿有歌诀且吉凶为吉/凶——
    书源一变形即判败，不静默降级。
    """
    title = XIU_SECTION
    if title not in blocks:
        problems.append(f"篇名不存在：{title}")
        return {}
    lo, hi = blocks[title]
    rows: dict[str, dict] = {}
    cur: str | None = None
    for j in range(lo + 1, hi):
        raw = lines[j].strip()
        if not raw:
            continue
        head = XIU_HEADER.match(raw)
        if head:
            name = head.group(1)[0]
            cur = XIU_ALIAS.get(name, name)
            rows[cur] = {
                "宿名书源": head.group(1), "值宿神将": head.group(2),
                "吉凶": head.group(3), "歌诀": [], "行号": [],
                "出处": f"《玉匣記》{title}（源文件第 {j + 1} 行起）",
            }
            continue
        if cur is None:
            continue
        rows[cur]["歌诀"].append(raw)
        rows[cur]["行号"].append(j + 1)

    from yishu_core.zeji_tables import XIU_ORDER as _XIU
    if set(rows) != set(_XIU):
        problems.append(f"{title} 宿集不齐：多 {sorted(set(rows) - set(_XIU))} "
                        f"缺 {sorted(set(_XIU) - set(rows))}")
    for k, v in rows.items():
        if not v["歌诀"] or len(v["歌诀"]) != len(v["行号"]):
            problems.append(f"{title}·{k}：歌诀与行号不配对")
        if v["吉凶"] not in ("吉", "凶"):
            problems.append(f"{title}·{k}：吉凶值非法 {v['吉凶']}")
    return rows


def _blocks(lines: list[str]) -> dict[str, tuple[int, int]]:
    """篇名 → (标题行号 0-based, 篇尾行号 exclusive)。篇名重复即报错。"""
    heads = [(i, l.strip()) for i, l in enumerate(lines) if l.strip().startswith("==")]
    out: dict[str, tuple[int, int]] = {}
    for k, (i, raw) in enumerate(heads):
        title = raw.strip("=").strip()
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        if title in out:
            raise SystemExit(f"篇名重复，无法唯一定位：{title}")
        out[title] = (i, end)
    return out


def _pick(lines: list[str], blocks: dict, title: str, prefix: str) -> tuple[str, int]:
    if title not in blocks:
        raise SystemExit(f"篇名不存在：{title}")
    lo, hi = blocks[title]
    hits = [(j, lines[j].strip()) for j in range(lo + 1, hi)
            if lines[j].strip().startswith(prefix)]
    if len(hits) != 1:
        raise SystemExit(f"前缀在篇内命中 {len(hits)} 行（要求唯一）：{title} / {prefix}")
    return hits[0][1], hits[0][0] + 1          # (整行原文, 1-based 行号)


def build() -> tuple[dict, list[str]]:
    lines = SRC.read_text(encoding="utf-8").splitlines()
    blocks = _blocks(lines)
    problems: list[str] = []
    flat = "\n".join(lines)                     # 逐字回指底本（含换行，行级唯一）

    def entry(title: str, prefixes: list[str]) -> dict:
        picked = [_pick(lines, blocks, title, p) for p in prefixes]
        for text, _ in picked:
            if text not in flat:
                problems.append(f"{title}: 引文不可回指 → {text[:24]}")
        lo, hi = blocks[title]
        return {
            "title": title,
            "lines": [t for t, _ in picked],
            "provenance": f"《玉匣記》{title}（源文件第 {lo + 1}–{hi} 行）",
        }

    activities = {act: [entry(t, ps) for t, ps in picks]
                  for act, picks in PICKS.items() if act != "common"}
    common = [entry(t, ps) for t, ps in PICKS["common"]]
    xiu_verses = _xiu_verses(lines, blocks, problems)

    doc = {
        "schema": "zeji-citations-v1",
        "_comment": [
            "择吉参考书证（《玉匣記》逐字引文，带篇名与源文件行号）。",
            "口径：引文只作对照书证，**不参与评分、不改判据**；判据唯一真值源是"
            " data/verdicts.json。",
            "构建器 dev_tools/build_citations.py 逐条断言引文为书源整行原文（铁律三可回指）。",
            "common = 引擎两项计分判据（黄黑道、建除宜忌）在本书的对应歌诀。",
            "xiu_verses = 二十八宿值日吉凶歌（28 宿，各带值宿神将与吉凶）；门 [1c] 另断言"
            "**其吉凶与判据表 verdicts.json#xiu 的吉宿/凶宿完全一致**——书证与判据不一致即判败。",
        ],
        "source": {
            "book": "《玉匣記》",
            "file": "data/sources/yuxiaji.wikitext.txt",
            "site": "维基文库 zh.wikisource.org",
            "provenance": "data/sources/yuxiaji.provenance.json",
        },
        "gap": GAP,
        "common": common,
        "activities": activities,
        "xiu_verses": xiu_verses,
    }
    return doc, problems


def main() -> int:
    ap = argparse.ArgumentParser(description="择吉外置书证构建（默认 dry-run）")
    ap.add_argument("--write", action="store_true", help="落盘 data/citations.json")
    ap.add_argument("--check", action="store_true",
                    help="不落盘，只比对已入库 data/citations.json 是否与重算一致")
    args = ap.parse_args()

    doc, problems = build()
    n = sum(len(v) for v in doc["activities"].values()) + len(doc["common"])
    print(f"篇目引文 {n} 条｜事类 {len(doc['activities'])} 个："
          f"{'、'.join(doc['activities'])}")
    print(f"通则书证 {len(doc['common'])} 条（{doc['common'][0]['provenance']}）")
    xv = doc.get("xiu_verses") or {}
    print(f"二十八宿值日吉凶歌 {len(xv)} 宿 / 歌诀 "
          f"{sum(len(v['歌诀']) for v in xv.values())} 行")
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
