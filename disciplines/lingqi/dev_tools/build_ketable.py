# -*- coding: utf-8 -*-
"""灵棋经课表提取器（一次性数据构建，产物入库、脚本留档可复跑）。

源：data/sources/ling-qi-jing.wikitext.txt（维基文库《靈棋經》，provenance 同目录）。
结构：124 个课标题 ==X上Y中Z下==（X/Y/Z ∈ 一..四，缺字 = 该部 0 枚；全零不成课），
每课正文：课名（「大通卦」）、象（「升騰之象」）、卦注、象曰、詩曰——全部逐字入表。
产物 data/ketables.json：key = "up-mid-down"（0..4 三元组，全零排除），铁律三：引文可回指。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
SRC = DISC.parents[1] / "data" / "sources" / "ling-qi-jing.wikitext.txt"
OUT = DISC / "data" / "ketables.json"

CN = {"一": 1, "二": 2, "三": 3, "四": 4}
HEAD_RE = re.compile(r"^==([一二三四]*)(上|中|下)([一二三四]*)(上|中|下)?([一二三四]*)(上|中|下)?==\s*$")


def main() -> int:
    text = SRC.read_text(encoding="utf-8")
    lines = text.splitlines()

    # 收集课标题与位置
    heads = []
    for i, raw in enumerate(lines):
        s = raw.strip()
        if not (s.startswith("==") and s.endswith("==")):
            continue
        core = s.strip("=").strip()
        units = re.findall(r"([一二三四]*)([上中下])", core)
        if not units:
            continue
        pos_list = [u[1] for u in units]
        if len(set(pos_list)) != len(pos_list):
            continue                     # 部位重复 → 非课标题
        if re.sub(r"[一二三四上中下]", "", core):
            continue                     # 含其他字符 → 非课标题
        counts = {"上": 0, "中": 0, "下": 0}
        for num, pos in units:
            counts[pos] = sum(CN[ch] for ch in num) if num else 0
        if not any(counts.values()):
            continue                     # 全零不成课
        heads.append((i, counts, core))

    entries = {}
    for idx, (i, counts, core) in enumerate(heads):
        end = heads[idx + 1][0] if idx + 1 < len(heads) else len(lines)
        body = [l.strip() for l in lines[i + 1: end] if l.strip()]
        name = xiang = zhu = ""
        xiangyue: list[str] = []
        shiyue: list[str] = []
        mode = None
        for l in body:
            if l.startswith("象曰") or l.startswith("象曰："):
                mode = "xiangyue"
                rest = l.split("：", 1)[-1].strip()
                if rest:
                    xiangyue.append(rest)
                continue
            if l.startswith("詩曰") or l.startswith("诗曰"):
                mode = "shiyue"
                rest = l.split("：", 1)[-1].strip()
                if rest:
                    shiyue.append(rest)
                continue
            if mode == "xiangyue":
                xiangyue.append(l)
                continue
            if mode == "shiyue":
                shiyue.append(l)
                continue
            if not name and "之象" in l:
                # 课名行形制：名（以卦/勢/教等收尾）+ 空格 + 「X之象」
                left, _, right = l.partition(" ")
                name = left.strip()
                xiang = right.strip() or ""
                continue
            if not name and (l.endswith("卦") or l.endswith("勢")):
                name = l
                continue
            if not xiang and l.endswith("之象"):
                xiang = l
                continue
            if not zhu:
                zhu = l
                continue
        key = f"{counts['上']}-{counts['中']}-{counts['下']}"
        entries[key] = {
            "name": name, "xiang": xiang, "zhu": zhu,
            "xiangyue": xiangyue, "shiyue": shiyue,
        }

    # 校验：124 课、课名齐全唯一
    problems = []
    if len(entries) != 124:
        problems.append(f"课数 {len(entries)} ≠ 124")
    names = [v["name"] for v in entries.values()]
    if bad := [k for k, v in entries.items() if not v["name"]]:
        problems.append(f"缺课名: {bad[:5]}")
    dup = {n for n in names if names.count(n) > 1}
    if dup:
        problems.append(f"课名重复: {sorted(dup)[:5]}")

    OUT.write_text(json.dumps({
        "schema": "yi-lingqi-ketable/1",
        "_comment": [
            "灵棋经 124 课查表（key = 上-中-下 各部面数 0..4，全零不成课）。",
            "全部字段逐字取自 data/sources/ling-qi-jing.wikitext.txt（铁律三：可回指）。",
            "narrate/analyze 只查本表，代码零断语字面量。",
        ],
        "problems": problems,
        "courses": dict(sorted(entries.items(), key=lambda kv: tuple(
            -int(x) for x in kv[0].split("-")))),
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"课表 {len(entries)} 课｜问题: {problems or '无'}")
    sample = entries.get("4-3-2") or next(iter(entries.values()))
    print("样例:", json.dumps({k: sample[k] for k in ('name', 'xiang')}, ensure_ascii=False))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
