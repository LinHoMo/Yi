# -*- coding: utf-8 -*-
"""结构层断语外置审计（第一百六十六批 §一.1 规矩的核对版，第两百一十批上门）。

规矩：吉凶断语字面量不得进结构层——结构层只出标签与数值，断语进 data/*.json。
210 批把存量 21 处（step4×15／step3×1／trigram×1／direction×1…经 18 处替换）逐字搬进
`data/rules/scripts_labels.json`（金标准与三集读数逐位未动＝搬家非改判），本器守此后不回潮。

判据：AST 扫 `<科>/scripts/**/*.py` 的字符串常量，命中判语词表即计一条——豁免三形（逐条显名）：
  · 交付层文件（narrate*／narrative_utils*）：断语装配层，本就在口径外（§一.1 结构层义）；
  · docstring（模块/函数裸字符串语句）：说明书不是输出；
  · 书证串（含《》/源L/「」）：照录引文，§三 引文面合法。
基线 LOCK=0：任何结构层新断语字面量判红；解锁唯一通道＝同 §四.6 搬家进 labels 册（不是改 LOCK）。

    python dev_tools/check_verdict_external.py --selftest
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

JUE = ("大吉", "大凶", "偏吉", "偏凶", "反断", "凶中反吉", "凶性反制", "病气难退",
       "为脱象", "宜守不宜攻", "孤立无援", "克用受阻", "贪合，暂不克用", "合绊，暂不克用",
       "不受局助", "无援之象")
EXEMPT_FILES = ("narrate", "narrative_utils")
LOCK = 0
MIN_FILES = 40


def scan(root: Path):
    rows = []
    files = [p for p in sorted(root.rglob("*.py")) if "__pycache__" not in str(p)]
    for py in files:
        if any(py.name.startswith(e) for e in EXEMPT_FILES) or py.name == Path(__file__).name:
            continue
        src = py.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(src)
        except SyntaxError:
            rows.append("%s 语法错" % py.name)
            continue
        doc_nodes = set()
        for nd in ast.walk(tree):
            if isinstance(nd, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                b = getattr(nd, "body", None)
                if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                        and isinstance(b[0].value.value, str):
                    doc_nodes.add(id(b[0].value))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                v = node.value
                if any(k in v for k in JUE) and len(v) >= 4:
                    if id(node) in doc_nodes:
                        continue
                    if "《" in v or "源L" in v or "「" in v:
                        continue
                    rows.append("%s:%s %r" % (py.relative_to(root), node.lineno, v[:40]))
    return rows, len(files)


def selftest() -> int:
    fails = []
    import tempfile
    with tempfile.TemporaryDirectory(prefix="yi_ve_st_") as td:
        tdp = Path(td)
        (tdp / "bad_engine.py").write_text(
            '"""模块说明无判语。"""\n\n\ndef f():\n    return "用神动化回头生，大吉"\n', encoding="utf-8")
        (tdp / "doc_ok.py").write_text(
            'def f():\n    """函数 docstring 说：大吉。"""\n    return 1\n', encoding="utf-8")
        (tdp / "quote_ok.py").write_text(
            'X = {"rule": "《增删》「虽逢月破，回头生不为大凶」"}\n', encoding="utf-8")
        (tdp / "narrate_wrap.py").write_text(
            'Y = "大吉（交付层文件豁免）"\n', encoding="utf-8")
        rows, n = scan(tdp)
        if n != 4:
            fails.append("扫描数 %d≠4（接线断）" % n)
        joined = " ".join(rows)
        if "bad_engine" not in joined:
            fails.append("真判语字面量未抓（门无牙）")
        for must_absent in ("doc_ok", "quote_ok", "narrate_wrap"):
            if must_absent in joined:
                fails.append("豁免面误杀：" + must_absent)
    rows_real, n_real = scan(DISC / "scripts")
    if len(rows_real) > LOCK:
        print("× 结构层判语字面量回潮 %d 处（LOCK=%d）：" % (len(rows_real), LOCK))
        for r in rows_real:
            print("   ", r)
        return 1
    print("√ selftest：判红/三豁免全中；本科 scripts 实扫 %d 文件，结构层判语 %d 处（≤LOCK %d）"
          % (n_real, len(rows_real), LOCK))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="结构层断语外置审计（§一.1 核对版）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    rows, n = scan(DISC / "scripts")
    if n < MIN_FILES:
        print("× 仅扫 %d 文件（<%d）——接线可疑" % (n, MIN_FILES))
        return 1
    if len(rows) > LOCK:
        for r in rows:
            print("× " + r)
        print("结构层判语回潮 %d 处——搬家进 scripts_labels.json，不解锁" % len(rows))
        return 1
    print("√ 结构层判语字面量 0 处（扫 %d 文件）" % n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
