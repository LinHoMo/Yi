#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文档符号级指认回验门（`[1b-3]`）。

**要防的病灶**（本轮真实出现）：已提交文档写「落点 `mod.py::NAME`」「`symbols.TABLE`」
「见 `y.py#func`」，而那个符号**从来不存在**或**已被删除**。既有 `[1b-2]` 文档死链门只判
「路径是否存在」，看不见符号层——`NAYIN_XIANGGE` 就是靠这个缺口在 AGENTS.md 里
以「已落实实体」活着（本轮实测：`git log -S` 显示该串历史上只进过一句注释）。

判据：AST 解析目标 .py，收集 def/class/模块级赋值名/注解式赋值/`x["key"]=` 下标键/
dict 字面量键/导入名；指认的符号命中任一即算真。
两条边界（避免把工具当真理）：
  · **语境窗口 ±2 行**内出现「已删/不存在/作废/历史/原写/订正/留档/当时/曾」等字样者跳过——
    那类句子是在**陈述缺陷**而不是指认现存实体；单行判定会把删除公告误判成指认（v1 实踩过）。
  · `docs/CHANGELOG.md` 只查本轮（2026-10-09）条目：它是按日登记的台账，历史条目描述
    当时的实体是它的职责，不是谎言。

`--selftest` 用**临时目录里的合成文档**注入一真一假两条指认，证明门真的会咬
（负例绝不往仓库植文件，与 `[1]` 唯一真值源门同一手法）。
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

ACTIVE_GLOBS = [
    "AGENTS.md", "README.md", "SKILL.md", "llms.txt", "PROMPTS.md",
    "docs/*.md", "docs/audits/*.md", "docs/source-readings/*.md",
    "disciplines/*/README.md", "disciplines/*/SKILL.md", "disciplines/*/docs/*.md",
    "web/*.md", "synthesis/README.md",
]
SEARCH_ROOTS = ("core", "disciplines", "tools", "synthesis", "cli", "web")
CHANGELOG = "docs/CHANGELOG.md"
CURRENT_ROUND_PREFIX = "### 2026-10-09"

PAT_PATHY = re.compile(r"([A-Za-z0-9_./-]+\.py)(?:::|#|:)([A-Za-z_][\w]{2,})")
PAT_MODULE_DOT = re.compile(r"\b([a-z_][a-z0-9_]*)\.([A-Z][A-Z0-9_]{2,})\b")
DELETED_CTX = re.compile(
    r"(不存在|已删|删除|删掉|清掉|撤销|GONE|不再|作废|历史|原写|误记|从未|订正|留档|当时|曾[于在]|"
    r"不实的?记载|撤回)")


def _names_in(path: Path) -> set[str] | None:
    """一个 .py 里可被文档指认的名字（含产出键名）。解析失败返回 None。"""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return None
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out.add(t.id)
                elif isinstance(t, ast.Subscript):
                    sl = getattr(t, "slice", None)
                    if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                        out.add(sl.value)          # 3.12+：x["key"] = ...
                    elif sl is not None and isinstance(getattr(sl, "value", None), ast.Constant):
                        v = sl.value.value
                        if isinstance(v, str):
                            out.add(v)             # 3.9-3.11：Index(Constant)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out.add(node.target.id)
        elif isinstance(node, ast.Dict):
            for k in node.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    out.add(k.value)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                out.add(a.asname or a.name.split(".")[0])
    return out


@lru_cache(maxsize=None)
def _by_basename(bn: str) -> tuple[str, ...]:
    hits = []
    for base in SEARCH_ROOTS:
        d = ROOT / base
        if not d.is_dir():
            continue
        hits += [str(p.relative_to(ROOT)).replace("\\", "/")
                 for p in d.rglob(bn) if "__pycache__" not in p.parts]
    return tuple(hits)


def _names_of(rel: str) -> set[str] | None:
    p = ROOT / rel
    return _names_in(p) if p.is_file() else None


@lru_cache(maxsize=None)
def _py_names(rel: str) -> frozenset:
    return frozenset(_names_of(rel) or set())


def _rel(doc: Path) -> str:
    """相对路径字符串；合成文档在仓库外（--selftest 用临时目录）时原样给出。"""
    try:
        return str(doc.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(doc)


def _lines_of(doc: Path) -> list[str]:
    raw = doc.read_text(encoding="utf-8", errors="replace").splitlines()
    if _rel(doc) != CHANGELOG:
        return raw
    keep, out = False, []
    for ln in raw:
        if ln.startswith("### "):
            keep = ln.startswith(CURRENT_ROUND_PREFIX)
        if keep:
            out.append(ln)
    return out


def check_docs(extra: list[Path] | None = None) -> list[str]:
    """返回判红明细（空列表＝全绿）。`extra` 供 --selftest 传合成文档。"""
    docs = sorted({p for g in ACTIVE_GLOBS for p in ROOT.glob(g) if p.is_file()})
    if extra:
        docs = sorted(set(docs) | {p for p in extra if p.is_file()})
    fails: list[str] = []
    for doc in docs:
        rel_doc = str(doc.relative_to(ROOT)).replace("\\", "/") if doc.is_relative_to(ROOT) else str(doc)
        base = _lines_of(doc)
        for i, line in enumerate(base, 1):
            ctx = "\n".join(base[max(0, i - 3):min(len(base), i + 2)])
            if DELETED_CTX.search(ctx):
                continue
            for path, sym in PAT_PATHY.findall(line):
                norm = path.replace("\\", "/")
                cands = [norm] if (ROOT / norm).is_file() else list(_by_basename(Path(norm).name))
                if not cands:
                    fails.append(f"{rel_doc}:{i} 指认 {path}::{sym} 找不到该文件（任何搜索根）")
                    continue
                if not any(sym in _py_names(c) for c in cands):
                    fails.append(f"{rel_doc}:{i} 指认 {path}::{sym} 解析不到符号"
                                 f"（候选 {', '.join(cands[:3])}）")
            for mod, const in PAT_MODULE_DOT.findall(line):
                cands = list(_by_basename(mod + ".py"))
                if not cands:
                    continue
                if not any(const in _py_names(c) for c in cands):
                    fails.append(f"{rel_doc}:{i} 指认 {mod}.{const} 在模块候选里解析不到"
                                 f"（{', '.join(cands[:2])}）")
    return fails


def run_selftest() -> int:
    """负例自证：一真一假两条指认，假的必须被判红、真的不得误报。"""
    with tempfile.TemporaryDirectory(prefix="yi_symbol_") as td:
        good = Path(td) / "_sym_good.md"
        bad = Path(td) / "_sym_bad.md"
        good.write_text("内核 `symbols.py::NAYIN_TO_ELEMENT` 与 `relations.ten_god` 均实存。\n",
                        encoding="utf-8")
        bad.write_text("落点 `symbols.py::THIS_SYMBOL_NEVER_EXISTS_AT_ALL`（现查）\n",
                       encoding="utf-8")
        fails = check_docs(extra=[good, bad])
    hit_bad = [f for f in fails if "THIS_SYMBOL_NEVER_EXISTS_AT_ALL" in f]
    hit_good = [f for f in fails if "NAYIN_TO_ELEMENT" in f or "ten_god" in f]
    print("符号指认门自证：合成文档 2 份（1 真指认 + 1 假指认）")
    print(f"  假指认被判红：{'√' if hit_bad else '×未判红（门无牙）'}")
    print(f"  真指认不误报：{'√' if not hit_good else '×误报 ' + hit_good[0][:70]}")
    if hit_bad and not hit_good:
        print(f"SELFTEST PASS（正例 1 例 + 负例 1 例）")
        return 0
    print("× SELFTEST FAIL")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="文档符号级指认回验（路径存在≠符号存在）")
    ap.add_argument("--selftest", action="store_true", help="临时合成文档注入真假指认各一条")
    ap.add_argument("--verbose", action="store_true", help="列出扫描文档数与明细")
    args = ap.parse_args()
    if args.selftest:
        return run_selftest()
    fails = check_docs()
    n = sum(1 for g in ACTIVE_GLOBS for _ in ROOT.glob(g))
    print(f"文档符号级指认回验：扫描面 glob 命中 {n} 项")
    for f in fails:
        print("  ×", f)
    if fails:
        print(f"共 {len(fails)} 处指认解析不到——文档在指认不存在的实体")
        return 1
    print("CHECK PASS（符号级指认全部可解析）")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
