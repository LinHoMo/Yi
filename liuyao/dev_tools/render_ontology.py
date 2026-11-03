# -*- coding: utf-8 -*-
"""易学图谱人读视图生成器：把 data/ontology/ 渲染成 Markdown 概念卡片。

每个 kid 一张卡片：定义、向上哲学推演链（parents）、向下派生（children）、书证、代码锚点。
人可从任意概念读懂"为什么这么判"，AI 可按 subgraph 检索。

用法：
    python dev_tools/render_ontology.py            # 生成 docs/ONTOLOGY-CARDS.md
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_ROOT = Path(__file__).resolve().parents[1]
_ONTO = _ROOT / "data" / "ontology"
_OUT = _ROOT / "docs" / "ONTOLOGY-CARDS.md"

LAYER_ORDER = ["L0", "L1", "L2", "L3", "L4"]
LAYER_NAME = {
    "L0": "元理层（哲学公理）", "L1": "象数层（模型）",
    "L2": "概念层（术语）", "L3": "规则层（判法）", "L4": "书证层（古籍断语）",
}
LAYER_FILES = {
    "L0": "l0_metaphysics.json", "L1": "l1_xiangshu.json",
    "L2": "l2_concepts.json", "L3": "l3_rules.json", "L4": "l4_evidence.json",
}


def layer_of(kid: str) -> str:
    return f"L{kid.split('.')[1][1]}"


def build() -> dict:
    nodes = {}
    for layer, fn in LAYER_FILES.items():
        d = json.loads((_ONTO / fn).read_text(encoding="utf-8"))
        for n in d.get("nodes", []):
            nodes[n["kid"]] = n
    return nodes


def chain_up(nodes: dict, kid: str) -> list[str]:
    """沿 parents 向上取到根的链。"""
    chain = [kid]
    seen = set()
    cur = kid
    while True:
        n = nodes.get(cur)
        if not n:
            break
        parents = n.get("parents", [])
        if not parents:
            break
        nxt = parents[0]
        if nxt in seen:
            break
        seen.add(nxt)
        chain.append(nxt)
        cur = nxt
    return chain


def render(nodes: dict) -> str:
    out = ["# 易学图谱概念卡片（自动生成）", "",
           "> 由 `dev_tools/render_ontology.py` 从 `data/ontology/` 生成。",
           "> 每张卡片：定义 → 向上哲学推演链 → 向下派生 → 书证 → 代码锚点。",
           "> 改 ontology 后重跑本器即可刷新。", ""]
    for layer in LAYER_ORDER:
        kids = [k for k in nodes if layer_of(k) == layer]
        if not kids:
            continue
        out.append(f"\n## {layer} · {LAYER_NAME[layer]}\n")
        for kid in sorted(kids):
            n = nodes[kid]
            out.append(f"### {n['name']}  `{kid}`")
            out.append(f"- **定义**：{n.get('def','')}")
            chain = chain_up(nodes, kid)
            if len(chain) > 1:
                out.append(f"- **向上推演**：{' → '.join(reversed(chain))}")
            children = n.get("children", [])
            if children:
                out.append(f"- **派生**：{'、'.join(children)}")
            if n.get("parents"):
                out.append(f"- **依据**：{'、'.join(n['parents'])}")
            if n.get("evidence"):
                for e in n["evidence"]:
                    out.append(f"- **书证**：《{e.get('book','')}》{e.get('text','')}")
            if n.get("book"):
                out.append(f"- **书证**：《{n['book']}》{n.get('locator','')}「{n.get('text','')}」")
            if n.get("engine_impl"):
                out.append(f"- **代码锚点**：`{n['engine_impl']}`")
            out.append("")
    return "\n".join(out)


def main() -> int:
    nodes = build()
    md = render(nodes)
    _OUT.write_text(md, encoding="utf-8")
    print(f"√ 已生成 {_OUT.relative_to(_ROOT)}：{len(nodes)} 张卡片")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
