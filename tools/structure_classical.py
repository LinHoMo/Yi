# -*- coding: utf-8 -*-
"""古文结构化转换器：将清洗后的连续古文转为带层级标题与段落的 Markdown。

核心策略（不删不改一字原文）：
1. 识别章节标题行（短行、含数字/篇名特征、或被 =原标记= 残迹标识）→ 转为 # / ## 标题
2. 按已有句读（。！？）切段：同一话题内若干句组成一个自然段；遇明显话题转换处另起段
3. 移除残留维基标记行（{{ }} 残留、仅空白行、meta 行）
4. 在首部追加 H1 书名 + 元信息块

用法：
  python tools/structure_classical.py modernized/liuyao/huangjin_ce.txt -o modernized/liuyao/huangjin_ce.md
  python tools/structure_classical.py --all

"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODERN = ROOT / "modernized"

# 六壬多卷统一主前缀
JUAN_RE = re.compile(r"^(.*)-juan(\d+)$")


def is_meta_line(ln: str) -> bool:
    """元信息行 / 维基残留标记行。"""
    s = ln.strip()
    if not s:
        return True
    if s.startswith("# ") and ("来源" in s or "sha256" in s or "字节" in s):
        return True
    if s.startswith("{{") or s.startswith("}}"):
        return True
    return False


def is_probably_heading(ln: str) -> int | None:
    """
    判断一行是否像章节标题，返回 Markdown 级别（1-3）或 None。
    启发式规则（保守，宁可漏过不可误判）：
    - 极短行（≤12 字）且以数字/总断/论/赋/章/卷/诀/歌开头
    - 含「卷」「篇」「章」「门」「部」等章节标识词
    - 含「诀」「赋」「歌」「论」「法」「法」等文体词
    """
    s = ln.strip()
    if not s:
        return None
    # 段落至少需要一句话的长度，超 28 字大概率不是标题
    if len(s) > 28:
        return None
    # 已有标点结尾的通常不是标题
    s_end = s[-1]
    if s_end in "。！？；,.!?;":
        return None
    # 章节标识词
    chapter_markers = ["卷", "篇", "章", "门", "部", "节", "则", "类"]
    form_markers = ["诀", "赋", "歌", "论", "法", "断", "序", "例", "义", "解", "说", "占"]
    start_digits = bool(re.match(r"^[\d一二三四五六七八九十百、.．\s]+", s))
    has_chapter = any(m in s for m in chapter_markers)
    has_form = any(m in s for m in form_markers)
    if start_digits and (has_form or has_chapter or len(s) <= 12):
        return 2
    if has_chapter and len(s) <= 20:
        return 2
    if has_form and len(s) <= 14 and not re.search(r"[。！？、]", s):
        return 2
    # 纯数字 + 短名
    if re.match(r"^[\d一二三四五六七八九十百]+\s*、?\s*\S{1,8}$", s):
        return 3
    return None


def split_paragraphs(lines: list[str]) -> list[str]:
    """把连续正文行按句读合并为段落。"""
    paragraphs: list[str] = []
    buf: list[str] = []
    for ln in lines:
        s = ln.strip()
        if not s:
            if buf:
                paragraphs.append("".join(buf))
                buf = []
            continue
        buf.append(s)
        # 以句末标点切段：同一话题内的句子合并；遇到明显结尾则成段
        if s[-1] in "。！？!?\n":
            # 观察下句开头是否新话题 — 这里保守地：每 1-3 句成一段
            if buf:
                paragraphs.append("".join(buf))
                buf = []
    if buf:
        paragraphs.append("".join(buf))
    return paragraphs


def prov_title(key: str) -> str | None:
    """从 data/sources/<key>.provenance.json 取书名，给 H1 用。"""
    p = ROOT / "data" / "sources" / f"{key}.provenance.json"
    if p.is_file():
        try:
            t = (json.loads(p.read_text(encoding="utf-8")) or {}).get("title")
            return t or None
        except Exception:
            return None
    return None


def process(infile: Path, outfile: Path) -> None:
    raw = infile.read_text(encoding="utf-8")
    lines = raw.splitlines()

    # 跳过 meta 区：以 "# " 开头且为元信息的连续行（出处/字节/sha256/时刻），直到第一个非 "#" 正文行
    body_start = 0
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("# ") and (
            "来源" in s or "出处" in s or "字节" in s or
            "sha256" in s or "清洗时刻" in s or re.match(r"^# \S+$", s)
        ):
            body_start = i + 1
            continue
        break
    # 如遇空行继续掠过
    while body_start < len(lines) and not lines[body_start].strip():
        body_start += 1
    body = lines[body_start:]

    # 提取可选的 H1：书名取 provenance 实测题名；取不到再用 key
    key = infile.stem[:-3] if infile.stem.endswith(".dz") else \
        infile.stem.replace(".wikitext", "")
    book_title = prov_title(key) or key

    out: list[str] = []
    out.append(f"# {book_title}")
    out.append("")

    i = 0
    while i < len(body):
        ln = body[i]
        # 跳过维基残留 + 空行
        if is_meta_line(ln) or not ln.strip():
            i += 1
            continue
        # 识别标题
        level = is_probably_heading(ln)
        if level:
            out.append("")
            out.append(f"{'#' * level} {ln.strip()}")
            out.append("")
            i += 1
            continue
        # 正文块：收集连续正文行再切段
        block: list[str] = []
        while i < len(body) and not is_meta_line(body[i]) and is_probably_heading(body[i]) is None:
            if body[i].strip():
                block.append(body[i])
            i += 1
        if block:
            paragraphs = split_paragraphs(block)
            for p in paragraphs:
                out.append(p)
                out.append("")

    # 清理连续空行
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)

    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(text, encoding="utf-8")
    rel_out = outfile.resolve().relative_to(ROOT)
    rel_in = infile.resolve().relative_to(ROOT)
    print(f"  ✓ {rel_in} → {rel_out}")


def main():
    ap = argparse.ArgumentParser(description="古文结构化 → Markdown")
    ap.add_argument("input", nargs="?", help="输入 .txt")
    ap.add_argument("-o", "--output", help="输出 .md")
    ap.add_argument("--all", action="store_true", help="处理 modernized/ 下全部子目录的 .txt")
    args = ap.parse_args()

    if args.all:
        files = []
        for d in sorted(MODERN.iterdir()):
            if d.is_dir() and d.name != "__pycache__":
                for f in sorted(d.glob("*.txt")):
                    files.append(f)
        print(f"共 {len(files)} 个清洗文本需结构化：")
        for f in files:
            out = f.with_suffix(".md")
            try:
                process(f, out)
            except Exception as e:
                print(f"  ✗ {f.name}: {e}")
        return

    if not args.input:
        ap.error("指定输入文件或使用 --all")
        return
    infile = Path(args.input)
    outfile = Path(args.output) if args.output else infile.with_suffix(".md")
    process(infile, outfile)


if __name__ == "__main__":
    main()
