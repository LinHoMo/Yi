#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成**多盘报告并集**文本，供 `[8] 语料接线` 量真正的覆盖率。

旧口径的缺陷（第一百一十七批按 §四.4 变更）：接线门只拿 `scratch/analyze.json` **一盘**的
narrate 输出去比语料叶子串，于是「2/302」这类读数其实接近**单盘天花板**——语料里绝大多数条目
本就不该在这一盘出现，门既证明不了「接上了」，也看不见「接错了」。本器把 `data/cases/eval_all.json`
里 `engine_output` 的全部盘逐条 `analyze → narrate` 拼成并集，覆盖率才有分母意义：
一条语料在 276 盘里**一次都没出现**，才是真的没接线。

用法：python dev_tools/corpus_reports.py [--out PATH]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "core"))
OUT_DEFAULT = ROOT / "scratch" / "corpus_reports.txt"
EVAL_ALL = ROOT / "data" / "cases" / "eval_all.json"


def ensure_eval_all() -> None:
    """干净树自足（第一百八十四批，与 liuyao 第一百七十六批同族）：
    eval_all.json 是 gitignored 生成物（`**/data/cases/eval_*.json`），全新克隆上不存在——
    本器此前因此只在作者机器可跑，接线门 [8] 在新树必红。修法＝缺件时按 `evaluate.py`
    文档头声明的既有生成路径（`--split all --save`）现做；生成失败仍判红，
    不静默、不回退单盘口径。"""
    if EVAL_ALL.exists():
        return
    import subprocess
    print("· eval_all.json 缺失（生成物不入库）——现场调用 evaluate --split all --save 生成")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "evaluate.py"),
                        "--split", "all", "--save"], cwd=str(ROOT))
    if r.returncode != 0 or not EVAL_ALL.exists():
        raise SystemExit("FAIL：eval_all.json 现生成失败——接线门不退回单盘口径，也不装绿")


def build(out_path: Path) -> tuple[int, int, int]:
    from analyze import analyze
    from narrate import narrate
    ensure_eval_all()
    data = json.loads(EVAL_ALL.read_text(encoding="utf-8"))
    chunks, errs = [], 0
    for _split, charts in (data.get("engine_output") or {}).items():
        for ch in charts or []:
            try:
                chunks.append(narrate(analyze(ch)))
            except Exception as e:                      # 一盘跑不通不能悄悄少算
                errs += 1
                print(f"× 盘面 narrate 失败：{type(e).__name__}: {str(e)[:120]}")
    if not chunks:
        raise SystemExit("FAIL：engine_output 为空或全部跑不通，本器无从产出并集")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(chunks), encoding="utf-8")
    return len(chunks), errs, sum(len(c) for c in chunks)


def main() -> int:
    out = OUT_DEFAULT
    if "--out" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--out") + 1])
    try:
        n, errs, chars = build(out)
    except SystemExit as e:
        print(e)
        return 1
    if errs:
        print(f"FAIL：{errs} 盘 narrate 失败（并集缺盘，不得当作全量）")
        return 1
    print(f"多盘并集：{n} 盘 → {out.name} {chars} 字")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
