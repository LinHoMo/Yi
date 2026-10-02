# -*- coding: utf-8 -*-
"""语料层可复现性：构建器重跑结果与已入库 `data/*.json` 是否一致。

为什么需要这一层：引文/语料层常被**手工补录**（先由构建器铺底，再经人工裁决补条目）。
一旦构建器的「应产出集合」与入库文件脱钩，**重跑构建器会静默删掉手工补录的条目**——
本仓 2026-10-02f 就实测到 `disciplines/ming/data/ditian_sui.json` 的「通隔論」章
会被 `build_dts_corpus.py` 删除（构建器 `WANTED` 未收录它）。

故各科语料构建器一律提供 `--check`：按同一口径重算，再用本模块与入库文件**语义比对**
（JSON 解析后逐键比，不比排版/缩进），不一致即判失败并列出差异路径。
"""
from __future__ import annotations

import json
from pathlib import Path

MAX_REPORT = 40          # 差异清单最多列多少条（其余以计数收尾）


def _diff(disk, made, path: str) -> list[str]:
    """逐键/逐元素比对；path 用 `$.a.b[0]` 形式指路，便于直接定位。"""
    if isinstance(disk, dict) and isinstance(made, dict):
        out: list[str] = []
        for k in sorted(set(disk) | set(made)):
            if k not in disk:
                out.append(f"{path}.{k}: 重算有、入库无（重跑将新增）")
            elif k not in made:
                out.append(f"{path}.{k}: 入库有、重算无（**重跑将删除**）")
            else:
                out.extend(_diff(disk[k], made[k], f"{path}.{k}"))
        return out
    if isinstance(disk, list) and isinstance(made, list):
        out = []
        if len(disk) != len(made):
            out.append(f"{path}: 条数不同 入库 {len(disk)} ≠ 重算 {len(made)}")
        for i in range(min(len(disk), len(made))):
            out.extend(_diff(disk[i], made[i], f"{path}[{i}]"))
        return out
    return [] if disk == made else [f"{path}: 值不同 {disk!r} ≠ {made!r}"]


def check(path: Path, payload) -> list[str]:
    """入库文件是否与重算结果一致；返回差异清单（空 = 一致）。"""
    if not path.is_file():
        return [f"{path.name}: 入库文件不存在（先跑一次构建器）"]
    disk = json.loads(path.read_text(encoding="utf-8"))
    diffs = _diff(disk, payload, f"$.{path.name}")
    return diffs[:MAX_REPORT] + ([f"… 另有 {len(diffs) - MAX_REPORT} 处差异"]
                                 if len(diffs) > MAX_REPORT else [])


def report(name: str, diffs: list[str]) -> int:
    """按语料文件名打印结论；一致返回 0，不一致返回 1。"""
    if not diffs:
        print(f"  √ {name} 与重算一致（可复现）")
        return 0
    print(f"  × {name} 与重算不一致（{len(diffs)} 处；重跑构建器会改变入库文件）：")
    for d in diffs:
        print(f"      · {d}")
    print("      处置：确认是有意补录则把条目并入构建器的产出集合（令其可复现），"
          "不要放任构建器与入库文件长期脱钩。")
    return 1
