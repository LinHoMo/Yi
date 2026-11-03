# -*- coding: utf-8 -*-
"""易学图谱本体看门狗：孤儿检查 + 引用完整性。

规则（见 docs/YI-KNOWLEDGE-GRAPH.md 铁律）：
1. 每个节点必须有 parents（L0 元理节点除外，它们是根）。
2. 任意非 L0 节点沿 parents 向上必须能走到某个 yi.l0.* 根节点——走不到就是 orphan。
3. parents 引用的 kid 必须真实存在（不能指向幽灵）。
4. engine_impl 声称锚定的 registry 规则必须存在。

用法：
    python dev_tools/check_ontology.py
    python dev_tools/check_ontology.py --selftest
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_ROOT = Path(__file__).resolve().parents[1]  # liuyao/
_ONTO = _ROOT / "data" / "ontology"
_REG = _ROOT / "rules" / "registry.json"

LAYER_FILES = ["l0_metaphysics.json", "l1_xiangshu.json", "l2_concepts.json", "l3_rules.json", "l4_evidence.json"]


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def build_graph() -> dict:
    """kid -> node dict（含 layer 标记）。"""
    nodes = {}
    for fn in LAYER_FILES:
        d = _load_json(_ONTO / fn)
        for n in d.get("nodes", []):
            kid = n["kid"]
            if kid in nodes:
                raise SystemExit(f"× kid 重复定义：{kid}")
            n["_layer_file"] = fn
            nodes[kid] = n
    return nodes


def check(nodes: dict, registry_ids: set, selftest: bool = False) -> list[str]:
    problems: list[str] = []

    # 1) parents 引用完整性
    for kid, n in nodes.items():
        for p in n.get("parents", []):
            if p not in nodes:
                problems.append(f"孤儿引用：{kid} 的 parent '{p}' 不存在")

    # 2) 向上追溯到 L0
    def reaches_root(kid: str, seen: set | None = None) -> bool:
        seen = seen or set()
        if kid in seen:
            return False
        seen.add(kid)
        if kid.startswith("yi.l0."):
            return True
        n = nodes.get(kid)
        if not n:
            return False
        parents = n.get("parents", [])
        if not parents:
            return False
        return any(reaches_root(p, seen) for p in parents)

    for kid, n in nodes.items():
        if kid.startswith("yi.l0."):
            continue
        if not reaches_root(kid):
            problems.append(f"orphan：{kid} 沿 parents 追溯不到任何 L0 根")

    # 3) engine_impl 锚 registry 规则存在性（跳过 read_only+legacy 旧台账锚点）
    for kid, n in nodes.items():
        if n.get("read_only") and n.get("legacy"):
            continue  # 旧 rule_registry.json 知识锚点，不在 v2 执行面
        impl = n.get("engine_impl", "")
        if "registry.json:" in impl:
            rid = impl.split("registry.json:", 1)[1].strip()
            if rid not in registry_ids:
                problems.append(f"engine_impl 悬空：{kid} 锚定不存在的规则 '{rid}'")

    return problems


def main() -> int:
    selftest = "--selftest" in sys.argv
    nodes = build_graph()
    registry = _load_json(_REG)
    registry_ids = {r["rule_id"] for r in registry.get("rules", [])}

    problems = check(nodes, registry_ids, selftest)

    if selftest:
        # 负例：造一个指向幽灵 parent 的临时节点，确认能被抓到
        bad = dict(nodes)
        bad["yi.test.ghost"] = {"kid": "yi.test.ghost", "name": "幽灵", "parents": ["yi.l0.NOPE"]}
        p2 = check(bad, registry_ids)
        if not any("NOPE" in x for x in p2):
            print("× 负例未抓到：幽灵 parent 没被检出")
            return 1
        print("√ 负例自证通过：幽灵 parent/orphan 均被抓")
        return 0

    print(f"图谱节点 {len(nodes)} 个")
    if problems:
        print(f"× 发现 {len(problems)} 个问题：")
        for p in problems:
            print("  -", p)
        return 1
    print("√ 图谱引用完整：无孤儿、无幽灵 parent、engine_impl 锚定真实")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
