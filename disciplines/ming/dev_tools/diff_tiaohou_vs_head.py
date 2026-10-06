# -*- coding: utf-8 -*-
"""改动前后逐格对拍：把当前 build 出的表与 HEAD 版表逐格比对，只报差异。
用于判定「是否真改进」，防止悄悄回归。只读（git show 取旧表）。"""
import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
QJSON = ROOT / "disciplines" / "ming" / "data" / "tiaohou_quotes.json"


def old_table() -> dict:
    """从 HEAD 取回 tiaohou_quotes.json（不依赖 git stash）。"""
    txt = subprocess.run(
        ["git", "show", f"HEAD:{QJSON.relative_to(ROOT).as_posix()}"],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout.decode("utf-8")
    return json.loads(txt)


def main() -> None:
    old = old_table()
    new = json.loads(QJSON.read_text(encoding="utf-8"))
    changed, to_empty, filled = [], [], []
    for k in sorted(set(old) | set(new)):
        o = old.get(k) or {}
        n = new.get(k) or {}
        om, oa = o.get("main"), o.get("assist")
        nm, na = n.get("main"), n.get("assist")
        if (om, oa) == (nm, na):
            continue
        changed.append(k)
        if om and not nm:
            to_empty.append(k)
        elif not om and nm:
            filled.append(k)
    print(f"HEAD 表 {len(old)} 格 → 当前表 {len(new)} 格")
    print(f"差异 {len(changed)} 格：新填 {len(filled)}，变空 {len(to_empty)}，改值 {len(changed) - len(filled) - len(to_empty)}")
    for k in changed:
        o, n = old.get(k) or {}, new.get(k) or {}
        print(f"  {k}: {o.get('main')}/{o.get('assist')} [{o.get('via')}]  →  {n.get('main')}/{n.get('assist')} [{n.get('via')}]")
        print(f"        新引文: {str(n.get('quote'))[:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
