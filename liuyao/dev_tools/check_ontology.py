# -*- coding: utf-8 -*-
"""易学图谱本体看门狗：引用完整性 + 机器锚点可达 + 人读产物同源。

规则（见 docs/YI-KNOWLEDGE-GRAPH.md 铁律）：
1. 每个节点必须有 parents（L0 元理节点除外，它们是根）。
2. 任意非 L0 节点沿 parents 向上必须能走到某个 yi.l0.* 根节点——走不到就是 orphan。
3. parents 引用的 kid 必须真实存在（不能指向幽灵）。
4. engine_impl 是**机器锚点**，四种形态都须可回指：
   a. `...registry.json:RULE_ID` → 规则 ID 在 rules/registry.json 里（512 批原有）；
   b. `path.json[:section]` → 文件按 `liuyao/` 根可达（524 批）；
   c. `path.py:SYMBOL` → 文件可达且符号在该文件顶层定义（524 批）；
   d. 其它形态 → 判红，不许静默逃逸。
   跳过 read_only+legacy 旧台账锚点（原有豁免）。
5. `docs/ONTOLOGY-CARDS.md` 是生成物，必须与 `render_ontology.render(当前图谱)`
   逐字一致——防「源数据错了、产物被手改对」把缺陷盖住（524 批）。

用法：
    python dev_tools/check_ontology.py
    python dev_tools/check_ontology.py --selftest

524 批扩面缘起：512 批上线时第 4 条只认 registry 形态，41 条守住了，而 12 条
路径形态锚点（8 条少 `core/`、4 条少 `domain/`）全部指向不存在的文件却一直全绿；
同期 `docs/ONTOLOGY-CARDS.md` 的 4 条 JSON 锚点被手改成正确路径，按源重生成
反而写回死引用。「门只覆盖一种形态」＋「产物与源分家」两处同型病，一次补齐。
"""
from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_ROOT = Path(__file__).resolve().parents[1]  # liuyao/
_ONTO = _ROOT / "data" / "ontology"
_REG = _ROOT / "rules" / "registry.json"
_CARDS = _ROOT / "docs" / "ONTOLOGY-CARDS.md"

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


def _top_symbols(p: Path) -> set[str]:
    """文件顶层定义的名字（函数/类/赋值）。"""
    tree = ast.parse(p.read_text(encoding="utf-8"))
    out: set[str] = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name)
        elif isinstance(n, ast.Assign):
            out |= {t.id for t in n.targets if isinstance(t, ast.Name)}
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            out.add(n.target.id)
    return out


def impl_problems(kid: str, impl: str, registry_ids: set) -> list[str]:
    """engine_impl 单条锚点判据；散文式宽松解析在这里不适用（这是机器锚点）。"""
    if "registry.json:" in impl:
        rid = impl.split("registry.json:", 1)[1].strip()
        if rid not in registry_ids:
            return [f"engine_impl 悬空：{kid} 锚定不存在的规则 '{rid}'"]
        return []
    rel, sep, tail = impl.partition(":")
    if rel.endswith(".json"):
        if not (_ROOT / rel).is_file():
            return [f"engine_impl 死引用：{kid} → `{impl}`（`{rel}` 不存在）"]
        return []
    if rel.endswith(".py"):
        target = _ROOT / rel
        if not target.is_file():
            return [f"engine_impl 死引用：{kid} → `{impl}`（`{rel}` 不存在）"]
        if not sep or not tail:
            return [f"engine_impl 形态不全：{kid} → `{impl}`（.py 锚点须写 `:SYMBOL`）"]
        try:
            syms = _top_symbols(target)
        except (OSError, SyntaxError, UnicodeError) as e:
            return [f"engine_impl 无法解析：{kid} → `{impl}`（{e}）"]
        if tail not in syms:
            return [f"engine_impl 符号缺失：{kid} → `{impl}`（`{tail}` 不在文件顶层）"]
        return []
    return [f"engine_impl 未知形态：{kid} → `{impl}`"
            f"（须为 registry.json:ID／*.json[:段]／*.py:SYMBOL）"]


def render_cards(nodes: dict) -> str:
    """复用渲染器的纯函数重算人读视图，不写盘。"""
    p = Path(__file__).with_name("render_ontology.py")
    spec = importlib.util.spec_from_file_location("_yi_render_ontology", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render(nodes)


def card_problems(nodes: dict, artifact_text: str | None = None) -> list[str]:
    if artifact_text is None:
        if not _CARDS.is_file():
            return [f"生成物缺失：{_CARDS.name}（改 ontology 后须重跑 render_ontology.py）"]
        artifact_text = _CARDS.read_text(encoding="utf-8")
    expected = render_cards(nodes)
    if artifact_text == expected:
        return []
    a, e = artifact_text.splitlines(), expected.splitlines()
    diff = [i for i in range(min(len(a), len(e))) if a[i] != e[i]]
    head = diff[0] + 1 if diff else min(len(a), len(e)) + 1
    av = a[head - 1][:60] if head <= len(a) else "—"
    ev = e[head - 1][:60] if head <= len(e) else "—"
    return [f"生成物与图谱分家：{_CARDS.name} 与 render_ontology.render(当前图谱) 不一致"
            f"（{len(diff)} 行不同／行数 {len(a)} vs {len(e)}；首处第 {head} 行："
            f"盘上 `{av}` ≠ 重算 `{ev}`）——改 ontology 后须重跑 render_ontology.py"]


def check(nodes: dict, registry_ids: set, selftest: bool = False,
          artifact_text: str | None = None) -> list[str]:
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

    # 3+4) engine_impl 全形态（跳过 read_only+legacy 旧台账锚点）
    for kid, n in nodes.items():
        if n.get("read_only") and n.get("legacy"):
            continue
        impl = n.get("engine_impl", "")
        if impl:
            problems += impl_problems(kid, impl, registry_ids)

    # 5) 生成物同源
    problems += card_problems(nodes, artifact_text)
    return problems


def main() -> int:
    selftest = "--selftest" in sys.argv
    nodes = build_graph()
    registry = _load_json(_REG)
    registry_ids = {r["rule_id"] for r in registry.get("rules", [])}
    cards = _CARDS.read_text(encoding="utf-8") if _CARDS.is_file() else ""

    problems = check(nodes, registry_ids, selftest, artifact_text=cards if selftest else None)

    if selftest:
        # 512 批原有负例：幽灵 parent / orphan
        bad = dict(nodes)
        bad["yi.test.ghost"] = {"kid": "yi.test.ghost", "name": "幽灵", "parents": ["yi.l0.NOPE"]}
        p2 = check(bad, registry_ids, artifact_text=render_cards(bad))
        if not any("NOPE" in x for x in p2):
            print("× 负例未抓到：幽灵 parent 没被检出")
            return 1
        # 524 批：engine_impl 每种形态各造一个，判红须来自目标分支
        root_kid = next(k for k in nodes if k.startswith("yi.l0."))
        # 假路径一律拼接构造：源码里不留完整死路径串，否则 check_doc_refs 会把
        # 负例字面量静态扫成「真死链」（AGENTS.md §四.8 的既定范式）。
        dead_json = "data/rules/" + "__no_such_" + "probe.json"
        dead_py = "core/" + "__no_such_" + "probe.py"
        cases = [
            ("死 JSON 路径", dead_json, "死引用"),
            ("死 PY 路径", dead_py + ":SYM", "死引用"),
            ("PY 缺符号", "core/yishu_core/symbols.py:" + "__NO_SUCH_SYMBOL__", "符号缺失"),
            ("悬空规则 ID", "rules/registry.json:" + "__no_such_rule__", "悬空"),
            ("未知形态", "随手写的说明文字", "未知形态"),
        ]
        for label, impl, want in cases:
            probe = dict(nodes)
            probe["yi.test.impl"] = {"kid": "yi.test.impl", "name": "锚点探针",
                                    "parents": [root_kid], "engine_impl": impl}
            # 探针 kid 不匹配任何 L 层，不会进渲染产物；传重算文本确保产物面放行
            got = check(probe, registry_ids, artifact_text=render_cards(probe))
            if not any(want in x for x in got):
                print(f"× 负例未抓到：{label}（{impl}）")
                return 1
        # 产物漂移负例：手改一行必须判红
        drift = check(nodes, registry_ids, artifact_text=cards + "\n<!-- 手改污染 -->\n")
        if not any("生成物与图谱分家" in x for x in drift):
            print("× 负例未抓到：生成物被手改却放行")
            return 1
        print("√ 负例自证通过：幽灵 parent／orphan／四种锚点形态／产物漂移均被抓")
        # 512 批：负例过了不等于真实图干净，仍须报真账。
        if problems:
            print(f"× 真实图谱发现 {len(problems)} 个问题：")
            for p in problems:
                print("  -", p)
            return 1
        print(f"√ 真实图谱引用完整（{len(nodes)} 节点）：无孤儿、无幽灵 parent、"
              f"engine_impl 全形态可达、人读产物与图谱同源")
        return 0

    print(f"图谱节点 {len(nodes)} 个")
    if problems:
        print(f"× 发现 {len(problems)} 个问题：")
        for p in problems:
            print("  -", p)
        return 1
    print("√ 图谱引用完整：无孤儿、无幽灵 parent、engine_impl 全形态可达、人读产物同源")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
