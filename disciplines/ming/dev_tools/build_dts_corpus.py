# -*- coding: utf-8 -*-
"""从《滴天髓》书源机械提取引擎所引章节 → disciplines/ming/data/ditian_sui.json（引文层）。

铁律：字符级提取，不改写、不做简繁转写、不编造。只提取引擎 narrate 实际引用者，
未引用的章不入库（避免"入库即死语料"）。取值层仍在 core，本文件只作引文层。

    python dev_tools/build_dts_corpus.py [--check]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "core"))

from yishu_core.ganzhi_calendar import HEAVENLY_STEMS  # noqa: E402  天干序唯一真值源
from yishu_core import corpus_kit  # noqa: E402  语料可复现性比对

SOURCE = ROOT / "data" / "sources" / "di-tian-sui.wikitext.txt"
OUT = DISC / "data" / "ditian_sui.json"

BOOK = "《滴天髓》（舊題京圖撰·劉基註）"
# 引擎实际引用者：日主体性 / 从化 / 岁运 / 体用 / 衰旺 / 寒暖 / 通隔 / 地支关系
# （章序即维基文库子页号，与书源 `<!-- ==== 滴天髓/NN ====` 注释一致）
WANTED = {
    "02": "天干論",
    "03": "地支論",
    "07": "從化論－真",
    "08": "從化論－假",
    "09": "歲運論",
    "10": "體用論",
    "12": "衰旺論",
    "16": "寒暖論",
    "20": "通隔論",
}
# 章内**节录**：只取与判据直接相关的原文行（1 基源行号）。未列者取整章。
# 地支論全章 16 首，四柱地支关系只据冲/刑/害/合三首；注文过长故不录
# （与 narrate `_dts_line` 的「只取原文」口径一致）。
PICK: dict[str, list[int]] = {"03": [202, 206, 210]}
TEN_STEMS = "".join(HEAVENLY_STEMS)   # 取自 core，不在学科内另存一份天干序

# 「任注对照」注记（OPT-ditian_sui_chanwei_dz-02，2026-10-07 补入本构建器产出集合）。
# 静态注记、不从书源机械提取，故作常量并入 _meta，使入库文件与构建器**可复现同构**
# （否则 --check 判「入库有、重算无」＝语料层与构建器脱钩，§四.6「静态表与 data 层
# 不同源时用同步脚本，不手改」的同类要求）。内容只述**注层归属**与引用纪律，
# 不含任何判定值，故不影响引擎取值与读数。
REN_ZHU_DUI_ZHAO = {
    "_说明": "本表所本与主源任注本属**不同注层**，引用时不得混引（OPT-ditian_sui_chanwei_dz-02，2026-10-07 补注记，**取值零变更**）",
    "_层别": {
        "本表所本_K层_刘基注本": "《滴天髓》舊題京圖撰·**劉基註**，维基文库公版。源文件 data/sources/di-tian-sui.wikitext.txt（861 行）。本文件 chapters 各章的 verse/notes 均出自此层。",
        "主源_C层_任铁樵注本": "《滴天髓》**任铁樵**注本（清道光年间任铁樵再为《滴天髓》作疏，阐微发隐）。源文件 data/sources/ditian_sui_chanwei_dz.dz.txt（7608 行，dz 为主源）；另有对勘本 data/sources/di-tian-sui-chan-wei.wikitext.txt（11495 行）。",
    },
    "_实测差异": "任注本 L4 自述 layering：「相传其原文为宋之京图撰，明代刘伯温为之注释，到清代道光年间，士人**任铁樵再为《滴天髓》作疏**，结合一生命理实践分篇增注，阐微发隐，使任注《滴天髓》成为传统命理学最重要的典籍」。故任注本＝**刘基注＋任氏疏**两层叠加，行数 7608 远多于刘基注本 861；任注本正文以「**任氏曰：**」起头（如 L72 任氏曰干为天元…、L78 任氏曰大哉乾元…、L83 任氏曰人居覆载之中…），此为刘基注本所无。",
    "_口径纪律": "①本表 chapters 的取象与判据一律以 **K 层（刘基注）**为准；②任注本（C 层）的文字若要在 narrate 引用，须走 verdicts.json 的逐字引文入口并标 offset，不得直接混入本表；③两层的同章名（如「從化論」「歲運論」「體用論」「衰旺論」「寒暖論」「通隔論」）**文字并不相同**，对同一命例可能给出不同结论——此属注层分歧，已在 docs/source-readings/ditian_sui_chanwei_dz.md §四登记；④本轮已实测：verdicts.json 原 `_meta.说明` 写「《滴天髓》通行本逐字常见句，原书全文未入库，故不标注 offset」这一前提**已失效**（任注本已入库），相关 7 条判据已改入 verdicts.json 的「滴天髓任注本」分支并各标 C 层 offset（见 OPT-ditian_sui_chanwei_dz-01）。",
    "_禁止": "不得把 C 层（任注）文字当作 K 层（刘基注）引文，也不得反向——两层的 verse/notes 与 offset 不可交叉引用。",
}

PAGE_RE = re.compile(r"^<!--\s*====\s*滴天髓/(\d+)\s*====")
TOC_RE = re.compile(r"^==\s*\[\[滴天髓/(\d+)\|([^\]]+)\]\]\s*==\s*$")
VERSE_RE = re.compile(r"^\{\{color\|red\|\{\{\+\|(.*)$")
HEAD_RE = re.compile(r"^={3,4}\s*(.+?)\s*={3,4}$")
STEM_RE = re.compile(r"^([甲乙丙丁戊己庚辛壬癸])[木火土金水]$")


def strip_verse(raw: str) -> str:
    """剥掉 {{color|red|{{+|…}} 外壳，只留原文。"""
    text = raw
    for _ in range(6):
        new = re.sub(r"\}+$", "", text).strip()
        if new == text:
            break
        text = new
    return text


def split_blocks(lines: list[str]) -> dict[str, tuple[int, list[str]]]:
    """按 `<!-- ==== 滴天髓/NN ====` 注释切子页块。

    返回 {章序: (注释行的 1 基行号, 注释之后的原文行)}——行号用于机械登记 `source_lines`。
    """
    blocks: dict[str, tuple[int, list[str]]] = {}
    cur: str | None = None
    for i, ln in enumerate(lines, start=1):
        m = PAGE_RE.match(ln.strip())
        if m:
            cur = m.group(1)
            blocks[cur] = (i, [])
            continue
        if cur is not None:
            blocks[cur][1].append(ln)
    return blocks


def parse_toc(lines: list[str]) -> dict[str, str]:
    toc = {}
    for ln in lines:
        m = TOC_RE.match(ln.strip())
        if m:
            toc[m.group(1)] = m.group(2)
    return toc


def read_page(block: list[str], first_lineno: int) -> list[tuple[str, str, int]]:
    """子页块 → 保序的 (kind, text, 源行号) 序列；kind ∈ {head, verse, note}。

    `first_lineno` 是块首行（Novel 行）的 1 基行号，逐行递增用于 `source_lines` 登记。
    """
    items: list[tuple[str, str, int]] = []
    for i, ln in enumerate(block):
        lineno = first_lineno + i
        s = ln.strip()
        m = VERSE_RE.match(s)
        if m:
            t = strip_verse(m.group(1))
            if t:
                items.append(("verse", t, lineno))
            continue
        h = HEAD_RE.match(s)
        if h:
            items.append(("head", h.group(1).strip(), lineno))
            continue
        if s.startswith(":") and not s.startswith("::"):
            t = s.lstrip(":").replace("　", "").strip()
            if t:
                items.append(("note", t, lineno))
    return items


def verses_of(items: list[tuple[str, str, int]]) -> list[str]:
    return [t for k, t, _ in items if k == "verse"]


def notes_of(items: list[tuple[str, str, int]]) -> list[str]:
    return [t for k, t, _ in items if k == "note"]


def source_lines_label(subpage: str, comment_lineno: int,
                       items: list[tuple[str, str, int]], picked: list[int] | None) -> str:
    """机械登记的出处：始取 Novel 行（注释行下一行），止于末条原文/注文行。

    节录章（`picked`）额外列明所取源行，说明本条目只含本章一部分。
    """
    lines = [ln for _k, _t, ln in items]
    if not lines:
        return ""
    start, end = comment_lineno + 1, max(lines)
    extra = f"；節錄原文行 {'/'.join(str(x) for x in picked)}" if picked else ""
    return (f"{SOURCE.relative_to(ROOT).as_posix()}:{start}-{end}"
            f"（子頁 {subpage}{extra}）")


def split_stem_sections(items: list[tuple[str, str, int]]) -> dict[str, dict]:
    """天干論：按 `===甲木===` 等子标题把原文/注文按书源原序分到十日干。"""
    out: dict[str, dict] = {}
    cur: str | None = None
    for kind, text, _lineno in items:
        if kind == "head":
            m = STEM_RE.match(text)
            cur = m.group(1) if m else None
            if cur:
                out.setdefault(cur, {"verse": [], "notes": []})
            continue
        if cur:
            out[cur]["verse" if kind == "verse" else "notes"].append(text)
    return {s: out[s] for s in TEN_STEMS if s in out}


def build() -> dict:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    toc = parse_toc(lines)
    blocks = split_blocks(lines)
    missing_toc = [k for k in WANTED if k not in toc]
    missing_blk = [k for k in WANTED if k not in blocks]
    if missing_toc or missing_blk:
        raise SystemExit(f"书源缺章：目录缺 {missing_toc}／子页缺 {missing_blk}"
                         f"（页面未展开或编号变动，勿静默跳过）")
    for k, name in WANTED.items():
        if toc[k] != name:
            raise SystemExit(f"章名与预期不符：{k} 实为「{toc[k]}」，预期「{name}」")

    chapters: dict[str, dict] = {}
    for k, name in WANTED.items():
        comment_lineno, block = blocks[k]
        items = read_page(block, comment_lineno + 1)
        picked = PICK.get(k)
        if picked:
            items = [it for it in items if it[2] in picked]
            got = [it[2] for it in items]
            if got != picked:
                raise SystemExit(f"章 {k} 节录行号对不上：期望 {picked}，实得 {got}"
                                 f"（书源页变动，勿静默跳过）")
        entry: dict = {
            "章序": k,
            "verse": verses_of(items),
            "notes": notes_of(items),
            "location": f"{BOOK}·{name}",
            "source_lines": source_lines_label(k, comment_lineno, items, picked),
        }
        if k == "02":
            entry["stems"] = split_stem_sections(items)
        chapters[name] = entry

    stems_flat = {}
    for stem, data in (chapters["天干論"].get("stems") or {}).items():
        stems_flat[stem] = {
            "verse": data["verse"],
            "notes": data["notes"],
            "location": f"{BOOK}·天干論·{stem}",
        }

    return {
        "_meta": {
            "所本": f"{BOOK}，维基文库公版",
            "来源文件": "data/sources/di-tian-sui.wikitext.txt",
            "提取方式": "按子页注释机械切块，取 {{color|red|{{+|…}} 原文行与 :　　注文行；"
                        "字符级提取，不改写、不做简繁转写",
            "口径": "只提取引擎 narrate 实际引用的章节；未引用章不入库，避免死语料。"
                    "`PICK` 所列章为节录（见各章 source_lines 的源行号）",
            "章数": len(chapters),
            # 「任注对照」是**静态注记**（OPT-ditian_sui_chanwei_dz-02，2026-10-07 补），
            # 不从书源机械提取，故以常量并入产出集合——否则入库文件会比构建器多出此键，
            # `build_dts_corpus.py --check` 判「入库有、重算无」而失败（语料层与构建器脱钩）。
            "任注对照": REN_ZHU_DUI_ZHAO,
        },
        "chapters": chapters,
        "day_stem": stems_flat,
    }


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="从《滴天髓》书源机械提取引文层")
    ap.add_argument("--check", action="store_true",
                    help="不落盘，只比对已入库 data/ditian_sui.json 是否与重算一致")
    args = ap.parse_args()

    if not SOURCE.is_file():
        print(f"× 缺书源 {SOURCE}")
        return 1
    payload = build()
    n_verse = sum(len(c["verse"]) for c in payload["chapters"].values())
    n_notes = sum(len(c["notes"]) for c in payload["chapters"].values())
    print(f"章 {len(payload['chapters'])}｜原文行 {n_verse}｜注文行 {n_notes}｜"
          f"十日干 {len(payload['day_stem'])}")
    if args.check:
        return corpus_kit.report(OUT.name, corpus_kit.check(OUT, payload))
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"写出 {OUT.relative_to(ROOT)}（{OUT.stat().st_size} 字节）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
