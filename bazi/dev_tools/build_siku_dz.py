# -*- coding: utf-8 -*-
"""把维基文库转写件规范化为**校订件**形态：`*_siku.dz.txt` ＋ `*_siku.provenance.json`。

    python dev_tools/build_siku_dz.py [--check]

为什么要有这一步（第三百二十九批）：仓库 `.gitignore` 第 23–30 行早已定调——

    # 抓取/校对原始件（维基文库转写 *.wikitext.txt、元数据 *.meta.json）与衍生比对件 *_diff.json：
    # 不入库——校订件 *.dz.txt + *.provenance.json 才是真源。

也就是说，**抓来的维基文库转写件按规矩不能入库**，能入库的是「校订件」。本脚本就是那条
从抓取件到校订件的通道，让新底本以真源形态进库、随仓分发。

规范化只动**标记形态**，正文与注文**一字不改**：
  · `{{SK anchor|章名}}`  → 独立成行的章名（与 dz 本的卷标/章题同体例）
  · `{{SK notes|注文}}` → `【注文】`（与在库 dz 本**同一套**注文标记）
  · `{{SKQS header|…}}` / `<poem>` / `<onlyinclude>` / `<!-- … -->` → 删除（版式包装，非内容）
  · 卷次标记 `<!-- ==== 三命通會 卷NN ==== -->` → 保留并转成行首标记（便于 grep 定位）

规范化之后，两本的注文标记统一为【】，**对拍口径可以再简化一层**
（此前需靠归一化剥【】来消解两边标记形态差异）。

底本内容本身仍来自维基文库（公有领域转录），出处、逐卷哈希、许可记进 provenance。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
RAW = DISC / "data" / "sources" / "sanming_tonghui_siku.wikitext.txt"
RAW_META = DISC / "data" / "sources" / "sanming_tonghui_siku.meta.json"
OUT = DISC / "data" / "sources" / "sanming_tonghui_siku.dz.txt"
PROV = DISC / "data" / "sources" / "sanming_tonghui_siku.provenance.json"

HEADER_RE = re.compile(r"\{\{SKQS header\|[^\n]*\}\}")
SK_ANCHOR = re.compile(r"\{\{SK anchor\|([^}]*)\}\}")
SK_NOTES = re.compile(r"\{\{SK notes\|([^\n]*?)\}\}")
VOL_MARK = re.compile(r"^<!-- ==== 三命通會 卷(\d{2}) ==== -->$")
COMMENT = re.compile(r"<!--.*?-->", re.S)
TAGS = re.compile(r"</?(?:poem|onlyinclude)[^>]*>")
# 卷尾页脚包装（版式，非内容）：{{SKQS footer|…}} 与 <子部,術數類,…>
FOOTER = re.compile(r"\{\{SKQS footer\|[^\n]*\}\}")
PAGE_MARK = re.compile(r"<子部,[^\n>]*>")


def normalize(raw: str) -> str:
    """把 wikitext 转写件转成 dz 体例（只动标记，不动字）。"""
    # 注释块**跨行**（卷首那段「請根據四庫全書掃描版校對本頁…」），必须先在全文级去掉；
    # 逐行调用会漏掉，导致校订件开头残留半截注释。
    raw = COMMENT.sub("", raw)
    out = []
    for line in raw.splitlines():
        m = VOL_MARK.match(line.strip())
        if m:
            out.append(f"　　三命通會卷{m.group(1)}")
            continue
        line = HEADER_RE.sub("", line)
        line = FOOTER.sub("", line)
        line = PAGE_MARK.sub("", line)
        line = TAGS.sub("", line)
        # 注文：{{SK notes|X}} → 【X】（与在库 dz 本同一套标记）
        line = SK_NOTES.sub(lambda mm: f"【{mm.group(1)}】", line)
        # 章名：{{SK anchor|X}} → 独立成行
        if SK_ANCHOR.search(line):
            head, sep, tail = line.partition(SK_ANCHOR.search(line).group(0))
            rest = line.split(SK_ANCHOR.search(line).group(0), 1)[1]
            # 行内可能同时有章名与注文，先取章名，其余按注文规则再处理一次
            titles = SK_ANCHOR.findall(line)
            body = SK_ANCHOR.sub("", line)
            body = SK_NOTES.sub(lambda mm: f"【{mm.group(1)}】", body)
            # 只去尾部空白：**头部缩进必须留着**——正文行一律缩进、章名顶格，
            # 这是「哪些是正文、哪些是章名」的唯一判据；strip 掉缩进会让正文顶格、
            # 章节切分失效（实测章数从 981 掉到 98）。
            body = body.rstrip()
            if body:
                out.append(body)
            for t in titles:
                # 顶格（无全角空格缩进）：正文行一律缩进，顶格者即章名，识别无歧义。
                # 章名带缩进会让「哪些是正文、哪些是章名」无从判别（实测章数从 981 掉到 98）。
                out.append(t.strip())
            continue
        out.append(line)
    # 去掉空行与尾随空白，压掉连续空行
    cleaned = [ln.rstrip() for ln in out]
    res, prev_blank = [], False
    for ln in cleaned:
        blank = (ln.strip() == "")
        if blank and prev_blank:
            continue
        res.append(ln)
        prev_blank = blank
    return "\n".join(res).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="维基文库转写件 → dz 校订件（真源形态）")
    ap.add_argument("--check", action="store_true", help="只比对在库校订件与重算结果，不写文件")
    args = ap.parse_args()

    raw = RAW.read_text(encoding="utf-8")
    text = normalize(raw)
    raw_bytes = text.encode("utf-8")
    sha = hashlib.sha256(raw_bytes).hexdigest()

    if args.check:
        if not OUT.is_file():
            print(f"× 校订件不存在：{OUT}")
            return 1
        cur = OUT.read_bytes()
        ok = hashlib.sha256(cur).hexdigest() == sha
        print(f"校订件 {OUT.name}：{len(cur)} 字节  sha256={hashlib.sha256(cur).hexdigest()[:16]}…  "
              f"与重算一致={ok}")
        return 0 if ok else 1

    OUT.write_bytes(raw_bytes)

    meta = json.loads(RAW_META.read_text(encoding="utf-8"))
    prov = {
        "key": "sanming_tonghui_siku",
        "kind": "八字",
        # 书名须与在库 dz 本（title=「三命通会」）区分开：八字科 `_source_titles()` 按
        # title→同名「dz 体例底本」建映射，两者同名会让锚点回验指向错误的底本。
        "title": "三命通会（四库全书本）",
        "work": "《三命通会》明·万民英撰（四库全书本）",
        "origin": "维基文库《三命通會 (四庫全書本)》卷01–卷12 逐页转写",
        "site": "zh.wikisource.org",
        "api": "https://zh.wikisource.org/w/api.php",
        "retrieved": meta.get("retrieved", "2026-10-29"),
        "license": "原作明代，公有领域；转录本依维基文库授权条款",
        "source_file": "data/sources/sanming_tonghui_siku.dz.txt",
        "raw_transcription": "data/sources/sanming_tonghui_siku.wikitext.txt（抓取件，按 .gitignore 不入库）",
        "chars": len(text),
        "bytes": len(raw_bytes),
        "sha256": sha,
        "sha256_convention": "对落盘字节取哈希（与在盘文件一致）",
        "eol_on_disk": "LF",
        "punctuation": "无标点（四库扫描版原文如此，卷首自注「加標點請另外建立頁面」）",
        "normalization": "只改标记形态，正文与注文一字不改：SK anchor→章名行、SK notes→【】、"
                         "版式包装（SKQS header/poem/onlyinclude/注释）删除",
        "relation_to_dz": "与在库 `sanming_tonghui_dz.dz.txt`（殆知阁转录）是**同一四库底本的两条"
                          "转录渠道**，不是两个版本；两者差异即转录脱漏，可逐段对拍。",
        "volumes": meta.get("volumes", []),
    }
    PROV.write_text(json.dumps(prov, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"校订件 {OUT.relative_to(DISC)}：{len(text)} 字 / {len(raw_bytes)} 字节  sha256={sha[:16]}…")
    print(f"出处     {PROV.relative_to(DISC)}：title=「{prov['title']}」")
    print(f"标记形态统一：章名行 {len(re.findall(r'^　　', text, re.M))} 处、注文【】{text.count('【')} 处")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
