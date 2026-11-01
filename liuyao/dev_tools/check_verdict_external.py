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

452 批追加：① 扫描层判据抽成 `audit_scan`，**`--selftest` 与主入口共用**——此前 selftest
只验「无回潮」，不验「扫到 0 文件」，`scripts/` 路径挪动或空目录会假绿（§四.8 的
0 结果守卫在 selftest 路径上是空的）；② 外置目录形状：`verdict_texts.json` 与
`scripts_labels.json` 不得有空节、空字符串、空列表/空对象（`basis` 按目录自带 _meta
的「可空」声明豁免）——断语搬家后被静默清空时，报告缺句没有任何别的门看得见。

    python dev_tools/check_verdict_external.py --selftest
"""
from __future__ import annotations

import argparse
import ast
import json
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
       "不受局助", "无援之象",
       # advisory 语族（第两百一十五批迁入并锁——210 批登记"不装完备"的那块，至此补齐）
       "宜早治", "顺势而为", "待时而动", "积极进取", "不可松懈", "终有成就",
       "宜备周全", "和睦之美", "交涉顺利", "感情融洽", "体用关系待察", "事多圆满", "需付出心力")
EXEMPT_FILES = ("narrate", "narrative_utils")
LOCK = 0
MIN_FILES = 40
# 452 批：外置目录本身也要守——断语搬进 JSON 后，若某条被清空，报告会静默缺句。
LABEL_FILES = ("data/rules/verdict_texts.json", "data/rules/scripts_labels.json")
META_KEYS = ("_meta", "schema", "_comment", "discipline")


def audit_scan(rows: list[str], n: int) -> list[str]:
    """扫描层的判据（主入口与 --selftest 共用，0 结果与回潮都在这里判）。"""
    problems: list[str] = []
    if n < MIN_FILES:
        problems.append("仅扫 %d 文件（<%d）——接线可疑；0 结果 ≠ 通过" % (n, MIN_FILES))
    if len(rows) > LOCK:
        problems.append("结构层判语字面量回潮 %d 处（LOCK=%d）——搬家进 labels 册，不解锁"
                        % (len(rows), LOCK))
    return problems


def _empty_leaves(obj, path: str = "") -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(obj, dict):
        if not obj:
            out.append((path or "<root>", "空对象"))
        for k, v in obj.items():
            out.extend(_empty_leaves(v, "%s/%s" % (path, k)))
    elif isinstance(obj, list):
        if not obj:
            out.append((path, "空列表"))
        for i, v in enumerate(obj):
            out.extend(_empty_leaves(v, "%s[%d]" % (path, i)))
    elif isinstance(obj, str) and not obj.strip():
        # 452 批：`basis` 按 verdict_texts 自身的 _meta 声明「可空」，不判；
        # 其余展示字段（text／label／template…）空即判红。
        if path.rsplit("/", 1)[-1] != "basis":
            out.append((path, "空字符串"))
    return out


def audit_doc(doc, rel: str) -> list[str]:
    """外置目录的结构完整性：非空节、无空值、无空列表/空对象（`_meta` 等说明节豁免）。"""
    problems: list[str] = []
    if not isinstance(doc, dict):
        return ["%s：顶层不是对象" % rel]
    for sec, v in doc.items():
        if sec in META_KEYS:
            continue
        if isinstance(v, (dict, list)) and not v:
            problems.append("%s：节「%s」为空" % (rel, sec))
    for path, why in _empty_leaves(doc):
        if path.startswith("/_meta") or path.startswith("/schema") or path.startswith("/_comment"):
            continue
        problems.append("%s%s：%s" % (rel, path, why))
    return problems


def audit_label_files() -> tuple[int, list[str]]:
    problems: list[str] = []
    n = 0
    for rel in LABEL_FILES:
        p = DISC / rel
        if not p.is_file():
            problems.append("%s：文件不存在" % rel)
            continue
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append("%s：JSON 解析失败（%s）" % (rel, exc))
            continue
        n += 1
        problems.extend(audit_doc(doc, rel))
    if n == 0:
        problems.append("外置目录 0 份读入——0 结果 ≠ 通过")
    return n, problems


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
    probs = audit_scan(rows_real, n_real)
    # 452 批负例：0 文件/0 判语不得当通过（照 §四.8「0 结果 ≠ 通过」）
    if not audit_scan([], 0):
        fails.append("负例未抓到：扫描 0 文件应判红")
    if audit_scan([], MIN_FILES + 1):
        fails.append("正例被误伤：管线正常时应 0 问题")
    # 452 批：外置目录形状负例（空字符串、空节必须抓到；正常节不误伤）
    if len(audit_doc({"section": {"k": ""}, "empty": {}}, "夹具")) < 2:
        fails.append("负例未抓到：空字符串/空节应至少 2 条")
    if audit_doc({"section": {"k": "正常文本"}}, "夹具"):
        fails.append("正例被误伤：正常外置目录不该判")
    n_lab, lab_probs = audit_label_files()
    if n_lab != len(LABEL_FILES):
        fails.append("外置目录只读入 %d/%d 份——接线断" % (n_lab, len(LABEL_FILES)))
    if probs or lab_probs or fails:
        for x in (probs + lab_probs + fails):
            print("× " + x)
        return 1
    print("√ selftest：判红/三豁免/0 文件/空目录全中；本科 scripts 实扫 %d 文件、"
          "结构层判语 %d 处（≤LOCK %d）；外置目录 %d 份无非空值"
          % (n_real, len(rows_real), LOCK, n_lab))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="结构层断语外置审计（§一.1 核对版）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    rows, n = scan(DISC / "scripts")
    probs = audit_scan(rows, n)
    n_lab, lab_probs = audit_label_files()
    if probs or lab_probs:
        for r in rows[:20]:
            print("× " + r)
        for x in probs + lab_probs:
            print("× " + x)
        return 1
    print("√ 结构层判语字面量 0 处（扫 %d 文件）；外置目录 %d 份无非空值" % (n, n_lab))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
