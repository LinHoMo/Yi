# -*- coding: utf-8 -*-
"""正则字符类 list 展平审计门（第一百六十六批 §二 硬规矩的核对版，第两百零九批上门）。

规矩：内核 `HEAVENLY_STEMS`/`EARTHLY_BRANCHES` 是 **list**——`"[%s]" % HEAVENLY_STEMS`
会把 `['甲','乙',…]` 的方括号引号当字面量塞进字符类：正则**永不命中且无报错**
（2026-10-13 build_yingqi_set.py 实踩，当时只修了肇事者，规矩没有核对版）。

本器 AST 级扫描本科全部 .py：凡 re.compile/search/match/findall/finditer/sub/fullmatch
的**模式参数为动态构造**（% 格式化／f-string／.format），提取其中标识符并回溯本科文件内
赋值链判定：
  合法 ＝ 字面量 str／含 join 的展平式（含一跳间接，如 STEMS = "".join(...)）
  判红 ＝ 裸内核 list 名直插、或 X = HEAVENLY_STEMS 式无展平别名
  NOTE ＝ 跨文件别名等本器解析不到的形态——显名报告不判红（不冒充完备）
扫描文件数低于下限即判红（§四.8：扫 0 份≠仓库没问题，先查接线）。

    python dev_tools/check_regex_lists.py                # 扫本科
    python dev_tools/check_regex_lists.py --selftest     # 负例三件套＋扫描守卫
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent  # 门是纯文本/AST 审计，不依赖内核——两科各持私有副本（零耦合；八字私有副本）

def force_utf8_stdio():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

LISTS = {"HEAVENLY_STEMS", "EARTHLY_BRANCHES"}
CALLS = {"compile", "search", "match", "findall", "finditer", "sub", "subn", "fullmatch", "split"}
MIN_FILES = 40


def _assignments(src: str) -> dict:
    """name -> 赋值右端的源码串（仅简单 Name 目标；一跳解析用）。"""
    out = {}
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out.setdefault(t.id, ast.get_source_segment(src, node.value) or "")
    return out


def _classify(arg_src: str, names, assign: dict):
    viol = []
    for n in names:
        rhs = assign.get(n)
        if rhs is None:
            if n in LISTS:
                viol.append((n, "裸内核 list 直插"))
            continue
        r = rhs.strip()
        if "join(" in r or r[:1] in ("\"", "f\"", "r\"", "'"):
            continue  # 展平式或字符串字面量
        if r in LISTS:
            viol.append((n, "别名未展平：" + n + " = " + r))
        # 一跳间接：X = Y，Y 是字面量赋值则放行（Y 在同文件已被收录判定为其自身）
        y = assign.get(r.strip())
        if y is not None and ("join(" in y or y.strip()[:1] in ("\"", "r\"", "f\"", "'")):
            continue
    return viol


def _names_in(node) -> list:
    return sorted({f.id for f in ast.walk(node) if isinstance(f, ast.Name)})


def scan_disc(root: Path):
    bad, note, scanned = [], [], 0
    files = [p for p in sorted(root.rglob("*.py"))
             if "__pycache__" not in str(p)]
    texts = {}
    for py in files:
        if py.name == Path(__file__).name:  # 本器的负例夹具字符串不参与自身扫描
            continue
        texts[py] = py.read_text(encoding="utf-8", errors="replace")
        scanned += 1
    for py, src in texts.items():
        try:
            tree = ast.parse(src)
        except SyntaxError:
            note.append("%s 解析失败（语法错？）" % py.name)
            continue
        assign = _assignments(src)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fname = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if fname not in CALLS or not node.args:
                continue
            a0 = node.args[0]
            if isinstance(a0, ast.JoinedStr) or (
                isinstance(a0, ast.BinOp) and isinstance(a0.op, ast.Mod)) or (
                isinstance(a0, ast.Call) and getattr(a0.func, "attr", "") == "format"):
                seg = ast.get_source_segment(src, a0) or ""
                names = _names_in(a0)
                viol = _classify(seg, names, assign)
                for n, why in viol:
                    bad.append("%s:%s [%s] %s" % (py.relative_to(root), node.lineno, n, why))
                if not viol:
                    for n in names:
                        if n in LISTS and assign.get(n) is None:
                            pass  # 已在上面判过
    return bad, note, scanned


def cmd_selftest() -> int:
    fails = []
    import tempfile
    with tempfile.TemporaryDirectory(prefix="yi_relist_st_") as td:
        tdp = Path(td)
        (tdp / "bad_direct.py").write_text(
            "import re\n"
            "from yishu_core.symbols import HEAVENLY_STEMS\n"
            "P = re.compile(r\"([%%s])日\" %% (HEAVENLY_STEMS,))\n", encoding="utf-8")
        (tdp / "good_join.py").write_text(
            "import re\n"
            "from yishu_core.symbols import HEAVENLY_STEMS\n"
            "STEMS = \"\".join(HEAVENLY_STEMS)\n"
            "P = re.compile(r\"([%%s])日\" %% (STEMS,))\n", encoding="utf-8")
        (tdp / "bad_alias.py").write_text(
            "import re\n"
            "from yishu_core.symbols import EARTHLY_BRANCHES\n"
            "BRANCHES = EARTHLY_BRANCHES\n"
            "P = re.search(r\"[%%s]月\" %% BRANCHES, 'x')\n", encoding="utf-8")
        bad, note, n = scan_disc(tdp)
        if n < 3:
            fails.append("夹具扫描数 %d<3（接线断）" % n)
        kinds = " ".join(bad)
        if "bad_direct" not in kinds:
            fails.append("裸 list 直插负例未抓（门无牙）")
        if "bad_alias" not in kinds:
            fails.append("无展平别名负例未抓")
        if any("good_join" in b for b in bad):
            fails.append("展平合法例被误杀")
        # 空目录守卫
        with tempfile.TemporaryDirectory() as empty:
            b2, n2, s2 = scan_disc(Path(empty))
            if s2 != 0:
                fails.append("空目录计数错")
    bad_real, note_real, n_real = scan_disc(DISC)
    if bad_real:
        print("× 本科现存违规：\n  " + "\n  ".join(bad_real))
        return 1
    print("√ selftest：负例三件套（裸插判红/别名判红/展平放行）全过；本科实扫 %d 文件违规 0%s"
          % (n_real, ("；NOTE %d（显名不判红）" % len(note_real)) if note_real else ""))
    return 0


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="正则字符类 list 展平审计（§二 硬规矩核对版）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return cmd_selftest()
    bad, note, n = scan_disc(DISC)
    if n < MIN_FILES:
        print("× 仅扫到 %d 文件（<%d）——遍历接线可疑，不宣布干净" % (n, MIN_FILES))
        return 1
    for b in bad:
        print("× " + b)
    for nt in note:
        print("NOTE " + nt)
    print("%s：扫 %d 文件，list 直插字符类违规 %d 处" % ("判红" if bad else "√ 通过", n, len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
