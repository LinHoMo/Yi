# -*- coding: utf-8 -*-
"""易学图谱 AI subgraph 检索：按 kid 输出该概念的完整子图。

输出 = 该节点 + 向上哲学链（parents 到根）+ 向下派生（children）+ 关联书证（evidence）。
供 AI 检索增强：给定一个概念 kid，取回它从哲学到书证的全部上下文。

用法：
    python dev_tools/ontology_subgraph.py yi.l3.rule.shi_hua_ke_wang
    python dev_tools/ontology_subgraph.py yi.l2.concept.huitouke --json
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

LAYER_FILES = ["l0_metaphysics.json", "l1_xiangshu.json", "l2_concepts.json",
               "l3_rules.json", "l4_evidence.json"]


def build() -> dict:
    nodes = {}
    for fn in LAYER_FILES:
        d = json.loads((_ONTO / fn).read_text(encoding="utf-8"))
        for n in d.get("nodes", []):
            nodes[n["kid"]] = n
    return nodes


def upward_chain(nodes: dict, kid: str) -> list[str]:
    """沿 parents 取到根（深度优先第一条链）。"""
    chain = [kid]
    seen = {kid}
    cur = kid
    while True:
        n = nodes.get(cur)
        if not n or not n.get("parents"):
            break
        nxt = n["parents"][0]
        if nxt in seen:
            break
        seen.add(nxt)
        chain.append(nxt)
        cur = nxt
    return chain


def evidence_of(nodes: dict, kid: str) -> list[dict]:
    """挂在这个 kid 上的书证：节点自身的 evidence 字段 + parents 指向它的 L4 节点。"""
    ev = []
    n = nodes.get(kid, {})
    for e in n.get("evidence", []):
        ev.append({"book": e.get("book", ""), "locator": "", "text": e.get("text", "")})
    for v in nodes.values():
        if v["kid"].startswith("yi.l4.") and kid in (v.get("parents") or []):
            ev.append({"book": v.get("book", ""), "locator": v.get("locator", ""), "text": v.get("text", "")})
    return ev


def subgraph(nodes: dict, kid: str) -> dict:
    if kid not in nodes:
        return {"error": f"kid 不存在: {kid}", "available": sorted(nodes.keys())}
    n = nodes[kid]
    up = upward_chain(nodes, kid)
    return {
        "kid": kid,
        "name": n.get("name"),
        "def": n.get("def", ""),
        "upward_chain": [{"kid": k, "name": nodes.get(k, {}).get("name", k)} for k in up],
        "children": [{"kid": c, "name": nodes.get(c, {}).get("name", c)} for c in n.get("children", [])],
        "evidence": evidence_of(nodes, kid),
        "engine_impl": n.get("engine_impl", ""),
    }


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    if not args:
        print("用法: ontology_subgraph.py <kid> [--json]")
        return 1
    nodes = build()
    g = subgraph(nodes, args[0])
    if as_json:
        print(json.dumps(g, ensure_ascii=False, indent=2))
        return 0
    if "error" in g:
        print(f"× {g['error']}")
        print("可用 kid：", ", ".join(g["available"][:10]), "…")
        return 1
    print(f"【{g['name']}】{g['kid']}")
    print(f"定义：{g['def']}")
    print(f"向上哲学链：{' → '.join(x['name'] for x in g['upward_chain'])}")
    if g["children"]:
        print(f"派生：{'、'.join(x['name'] for x in g['children'])}")
    if g["evidence"]:
        for e in g["evidence"]:
            print(f"书证：《{e['book']}》{e['locator']}「{e['text']}」")
    if g["engine_impl"]:
        print(f"代码锚点：{g['engine_impl']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
