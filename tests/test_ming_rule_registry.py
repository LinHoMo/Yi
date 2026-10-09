# -*- coding: utf-8 -*-
"""命科规则注册表回验（impl 指针 / 引文指针 / 评测 dim 三张牙）。

**为什么有这个文件**：本表的回验原本住在 `tests/test_rule_registry_ming_meihua.py`，
该文件 60b2403 随梅花科一起删除（−252 行）后，注册表的 `impl` / `quote_in_data`
指针写错**再无人判红**——实盘就躺着两条错指针（`tiaohou_of` 归给 `pattern.py`、
dayun 8 步归给 `analyze.py`），而 registry `_comment` 与 `dayun_quotes.json._comment`
还在说「测试强制 / tests/…meihua 可回验」。本文件把契约重新挂上，判据是**解析**
而不是字符串对比：

  ① impl 里每一个 `<file>:<symbol>` 都必须解析到该文件里**顶层定义**的符号
     （ast 取 def/class/模块级赋值；只是被 import 进来不算——那正是原错指针的形态）；
  ② `quote_in_data` 指针逐段可解引用，其引文必须**逐字命中** `source.corpus_files`
     登记的在库语料；条目自带 `corpus_line` 者按**行级**逐字回验；
  ③ `evaluation.dim` 必须是 `scripts/evaluate.py` 里 `WEIGHTS` 的真实键
     （ast 取键，不查「文本里出现过这个名字」）。

已知边界（如实写明，不假装覆盖）：
  · impl 括号里**没写成 `file:symbol` 形式**的次要提及（如结果字段名
    `tentative_special / from_kind`、只写模块名不写符号的引用）不在解析范围内——
    本门锁「写了 `file:symbol` 的指针必须真」，不锁「所有提及都带指针」；
  · 「某 dim 在 tune/holdout 里确实有 N 例 expected」这类**覆盖读数**不在测试里重算——
    那等于把 `evaluate.py` 的适用性判据抄第二份（§二 唯一真值源）。读数由
    `disciplines/ming/dev_tools/check.py` 的分数下限门守，note 里的 n 由人工核对。
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DISC = ROOT / "disciplines" / "ming"
REG_PATH = DISC / "data" / "rules" / "rule_registry.json"
EVALUATE_PY = DISC / "scripts" / "evaluate.py"

# impl 里显式写的 `<file>:<symbol>` 指针对（路径用正斜杠，仓内约定）。
# 文件部分以 `.py` 收尾（可再跟 `:行号`），冒号前允许一个空格——
# 「…result['tiaohou']…」这类散文里的冒号不得被当成指针，故解析后仍按 .py 结尾过滤。
IMPL_PAIR_RE = re.compile(r"([\w./-]+\.py)(?::\d+)?\s*:([A-Za-z_][A-Za-z0-9_]*)")

# evaluation.status / splits 词表：与本仓既有登记一致，不在表内即虚标
ALLOWED_STATUS = {"classical_holdout", "mechanical_regression", "external_holdout",
                  "source_only", "unassessed"}
ALLOWED_SPLITS = {"tune", "holdout", "all", "external_holdout"}


@pytest.fixture(scope="module")
def registry() -> dict:
    assert REG_PATH.is_file(), f"注册表不存在：{REG_PATH}"
    return json.loads(REG_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def entries(registry) -> list[tuple[str, dict]]:
    """rules + _uncovered 一并回验：两条都声明 impl 与出处指针，都该真。"""
    out = [("rules", r) for r in (registry.get("rules") or [])]
    out += [("_uncovered", r) for r in (registry.get("_uncovered") or [])]
    return out


# ── 解析工具（只读，不执行被测模块）────────────────────────────────────────

def resolve_file(raw: str) -> Path:
    """impl/pointer 里的相对路径 → 绝对路径（先按学科根，再按仓库根）。"""
    for base in (DISC, ROOT):
        p = (base / raw)
        if p.is_file():
            return p
    raise AssertionError(f"路径无法解析（学科根与仓库根都没有）：{raw}")


def toplevel_names(path: Path) -> set[str]:
    """文件里**顶层定义**的名字：def / class / 模块级赋值（含顶层 if/try 块内）。

    刻意不用 import 求值：注册表 impl 写 `pattern.py:tiaohou_of` 时，import 后
    `hasattr` 也是 True（它在 :20 处被 import 进来），但**定义不在那里**——
    正是本次要拦的那类错指针。
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()

    def collect(body) -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(node.name)
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        names.add(t.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names.add(node.target.id)
            elif isinstance(node, (ast.If, ast.Try)):
                # 顶层条件定义（try: from x import y / if py>=3.x: …）也算定义处
                collect(node.body)
                collect(node.orelse or [])
                for handler in getattr(node, "handlers", []) or []:
                    collect(handler.body)
                collect(getattr(node, "finalbody", []) or [])

    collect(tree.body)
    return names


def resolve_data_pointer(pointer: str) -> tuple[object, dict]:
    """`file#dotted.key` → (值, 值的父字典)（父字典用于取 corpus_line）。"""
    file_part, _, path_part = pointer.partition("#")
    cur = json.loads(resolve_file(file_part).read_text(encoding="utf-8"))
    parent: dict = cur if isinstance(cur, dict) else {}
    for part in path_part.split("."):
        assert isinstance(cur, dict) and part in cur, f"指针断裂：{pointer}（缺 {part}）"
        parent, cur = cur, cur[part]
    return cur, parent


def weights_keys() -> set[str]:
    """evaluate.py 的 WEIGHTS 键（ast 取，不跑评测、不查子串）。"""
    tree = ast.parse(EVALUATE_PY.read_text(encoding="utf-8"), filename=str(EVALUATE_PY))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names, value = [node.target.id], node.value
        else:
            continue
        if "WEIGHTS" in names and isinstance(value, ast.Dict):
            return {k.value for k in value.keys if isinstance(k, ast.Constant)}
    raise AssertionError("evaluate.py 里找不到模块级 WEIGHTS 字面量字典")


def impl_pairs(impl: str) -> list[tuple[str, str]]:
    """impl 里**确实指向 .py 文件**的 `file: symbol` 对。

    只匹配 `<…py>:<symbol>`——散文里「analyze 顶层 result['shensha']」这类冒号
    不算指针（否则会误把中文说明当路径去解析）。
    """
    return [(f, s) for f, s in IMPL_PAIR_RE.findall(impl) if f.endswith(".py")]


# ── ① impl 指针必须解析到真定义 ────────────────────────────────────────────

class TestImplPointers:
    def test_entries_are_present(self, entries) -> None:
        assert len(entries) >= 5, f"注册表条目异常少：{len(entries)}"

    def test_impl_has_explicit_file_symbol_pointer(self, entries) -> None:
        """impl 至少给一个 `<file>:<symbol>`——散文式描述（「dayun 8 步」）不算指针。"""
        for where, rule in entries:
            assert impl_pairs(rule.get("impl") or ""), (
                f"{rule.get('rule_id')}：impl 没有 <file>:<symbol> 形式的指针，"
                f"无法程序化回验（实文={rule.get('impl')!r}）")

    def test_impl_symbols_really_defined(self, entries) -> None:
        cache: dict[str, set[str]] = {}
        for where, rule in entries:
            rid = rule.get("rule_id", "?")
            for file_raw, symbol in impl_pairs(rule["impl"]):
                path = resolve_file(file_raw)
                names = cache.setdefault(str(path), toplevel_names(path))
                assert symbol in names, (
                    f"{rid}：impl 指针 {file_raw}:{symbol} 处该文件**没有定义这个符号**"
                    f"（只有 import 进来/根本没有）。定义处候选："
                    f"{sorted(n for n in names if symbol.split('_')[0] in n)[:6]}")

    def test_registry_shape_and_fields(self, registry) -> None:
        assert registry["schema"] == "yi-rule-registry-v1"
        assert registry["discipline"] == "ming"
        ids = [r["rule_id"] for r in registry["rules"]]
        assert len(ids) == len(set(ids)), "rule_id 重复"
        for rule in registry["rules"]:
            rid = rule.get("rule_id", "?")
            assert rid.startswith("ming."), f"{rid}：rule_id 须带学科前缀"
            assert rule.get("domain") and rule.get("applicability"), rid
            src = rule.get("source") or {}
            assert src.get("book"), f"{rid}：缺古籍出处"
            assert isinstance(src.get("verified"), bool), f"{rid}：缺 verified 标记"
            ev = rule.get("evaluation") or {}
            assert ev.get("status") and ev.get("dim") and ev.get("splits"), f"{rid}：缺评测登记"
            assert ev.get("note"), f"{rid}：缺评测覆盖说明（须带 n 与集合名，铁律三）"
        for rule in registry.get("_uncovered") or []:
            assert rule.get("why_not_registered"), f"{rule.get('rule_id')}：未注册须说明理由"
            assert "evaluation" not in rule, \
                f"{rule.get('rule_id')}：_uncovered 不得带 evaluation 块（那是未注册项）"


# ── ② 引文指针可解引用且逐字命中书源 ───────────────────────────────────────

class TestQuotePointers:
    def test_quote_in_data_verbatim_in_corpus(self, entries) -> None:
        """rules 与 _uncovered 一视同仁：写了出处指针就必须能解引用。

        2026-10-09 补：本方法原先只遍历 `registry["rules"]`，实测把
        `_uncovered` 里 `ming.bing_yao` 的 `quote_in_data` 改成不存在的键，
        14 例仍全绿——即"说谎的指针无人报警"。同一文件里 `quote_in_code`
        走的是合并迭代器 `entries`，两条判据覆盖面不该不一致。
        """
        checked = 0
        for _sec, rule in entries:
            src = rule.get("source") or {}
            pointer = src.get("quote_in_data")
            if not pointer:
                continue
            rid = rule.get("rule_id", "?")
            corpora = src.get("corpus_files") or []
            assert corpora, f"{rid}：有 quote_in_data 却没登记 corpus_files，无法逐字回验"
            value, parent = resolve_data_pointer(pointer)
            assert isinstance(value, str) and value.strip(), f"{rid}：指针未指向非空引文串"
            texts = [resolve_file(f).read_text(encoding="utf-8") for f in corpora]
            assert any(value in t for t in texts), (
                f"{rid}：quote_in_data 引文**不是**任何一份登记语料的逐字子串：{pointer}")
            line_no = parent.get("corpus_line")
            if line_no:
                hit = False
                for t, f in zip(texts, corpora):
                    lines = t.splitlines()
                    assert 0 < int(line_no) <= len(lines), f"{rid}：corpus_line 越界（{f}）"
                    if value in lines[int(line_no) - 1]:
                        hit = True
                assert hit, (f"{rid}：引文不在 corpus_line={line_no} 那一行（{pointer}）——"
                             f"行级锚点已漂移")
            checked += 1
        assert checked >= 2, f"逐字引文指针过少（{checked}）：注册表的出处层没被回验"

    def test_quote_in_code_anchor_exists(self, entries) -> None:
        for where, rule in entries:
            anchor = (rule.get("source") or {}).get("quote_in_code")
            if not anchor:
                continue
            file_part, _, needle = anchor.partition("#")
            assert needle, f"{rule.get('rule_id')}：quote_in_code 没有锚点串"
            text = resolve_file(file_part).read_text(encoding="utf-8")
            assert needle in text, (f"{rule.get('rule_id')}：quote_in_code 锚点不在文件里："
                                    f"{anchor}")

    def test_tiaohou_quote_library_is_verbatim(self, registry) -> None:
        """引文库整库逐字回验：110 条 quote 必须都是登记语料的逐字子串。

        「照录」字段一律不改字、不转简（AGENTS.md §二 数据缺陷 vs 引擎缺陷）。
        """
        rule = next(r for r in registry["rules"] if r["rule_id"] == "ming.tiaohou")
        corpora = [(resolve_file(f), f) for f in rule["source"]["corpus_files"]]
        lib = json.loads((DISC / "data" / "tiaohou_quotes.json").read_text(encoding="utf-8"))
        quotes = {k: v["quote"] for k, v in lib.items()
                  if isinstance(v, dict) and v.get("quote")}
        assert len(quotes) >= 100, f"引文库条数异常：{len(quotes)}"
        texts = [p.read_text(encoding="utf-8") for p, _ in corpora]
        bad = [k for k, q in quotes.items() if not any(q in t for t in texts)]
        assert not bad, f"下列调候引文不在任何登记语料里（改写/漂移）：{bad[:10]}"

    def test_dayun_quote_library_matches_declared_corpus(self, registry) -> None:
        rule = next(r for r in registry["rules"] if r["rule_id"] == "ming.dayun")
        src = rule["source"]
        lib_path = resolve_file("disciplines/ming/data/rules/dayun_quotes.json")
        lib = json.loads(lib_path.read_text(encoding="utf-8"))
        declared = [resolve_file(f) for f in src["corpus_files"]]
        prov_file = lib.get("_provenance", {}).get("source_file")
        assert prov_file, "dayun_quotes.json 缺 _provenance.source_file"
        assert resolve_file(prov_file) in declared, (
            f"引文库自述语料 {prov_file} 与注册表 corpus_files 不一致——两处必须同指一份")
        for key in ("yang_male_yin_female", "yin_male_yang_female"):
            item = lib[key]
            text = declared[0].read_text(encoding="utf-8").splitlines()
            assert item["quote"] in text[item["corpus_line"] - 1], \
                f"dayun_quotes.json#{key} 不在语料行 {item['corpus_line']}"

    def test_verified_requires_a_pointer(self, registry) -> None:
        for rule in registry["rules"]:
            src = rule["source"]
            if src.get("quote_in_data") or src.get("quote_in_code"):
                continue
            assert src["verified"] is False, \
                f"{rule['rule_id']}：无引文指针却声称 verified"
            assert ("待" in src.get("locator", "") or "缺口" in src.get("locator", "")), \
                f"{rule['rule_id']}：缺引文应把 locator 明示为缺口"


# ── ③ 评测 dim 与状态口径 ──────────────────────────────────────────────────

class TestEvaluationCoverage:
    def test_dim_is_a_real_weights_key(self, registry) -> None:
        keys = weights_keys()
        assert keys, "evaluate.py WEIGHTS 解析出空集"
        for rule in registry["rules"]:
            dim = rule["evaluation"]["dim"]
            assert dim in keys, (f"{rule['rule_id']}：dim「{dim}」不在 WEIGHTS 键 "
                                 f"{sorted(keys)}——虚标评测维度")

    def test_status_and_split_vocabulary(self, registry) -> None:
        for rule in registry["rules"]:
            ev = rule["evaluation"]
            assert ev["status"] in ALLOWED_STATUS, \
                f"{rule['rule_id']}：未知 evaluation.status {ev['status']}"
            assert set(ev["splits"]) <= ALLOWED_SPLITS, \
                f"{rule['rule_id']}：未知分列 {set(ev['splits']) - ALLOWED_SPLITS}"

    def test_unverified_is_not_marked_external(self, registry) -> None:
        for rule in registry["rules"]:
            if not rule["source"]["verified"]:
                assert rule["evaluation"]["status"] != "external_holdout", \
                    f"{rule['rule_id']}：未核引文不得虚标外部验证"

    def test_no_case_specific_pointers(self, registry) -> None:
        """铁律：规则不得为个别案例开私有分支——impl/出处里不得出现案例 id。"""
        pat = re.compile(r"\b(?:MG|ZE|MC|BY)[A-Z]?\d{2,}")
        for rule in registry["rules"]:
            blob = json.dumps({k: rule[k] for k in ("impl", "source", "applicability")},
                              ensure_ascii=False)
            assert not pat.search(blob), f"{rule['rule_id']}：疑似 case-specific 引用"


# ── ④ 注册表确实被消费（否则又是一张无人读的表）────────────────────────────

class TestRegistryIsConsumed:
    def test_feeds_evidence(self, registry) -> None:
        sys.path.insert(0, str(ROOT / "core"))
        from yishu_core.evidence import attach_rule_registry

        def item(factor: str) -> dict:
            return {"id": f"ming:t:0:{factor}", "discipline": "ming",
                    "claim": f"结构标签 {factor}", "factor": factor, "rule_id": "",
                    "source": "", "applicability": "", "observation": "", "effect": "",
                    "evaluation_status": "unassessed",
                    "provenance": {"kind": factor, "path": f"result['{factor}']"}}

        # 这两个 factor 是内核 evidence 构建器真的产出的（tiaohou / shensha）
        out = attach_rule_registry([item("tiaohou"), item("shensha")], registry)
        by_factor = {e["factor"]: e for e in out}
        assert by_factor["tiaohou"]["rule_id"] == "ming.tiaohou", by_factor
        assert by_factor["tiaohou"]["evaluation_status"] == "classical_holdout"
        assert by_factor["shensha"]["rule_id"] == "ming.shensha", by_factor
        # ming.shensha 案例集 0 applicable：注册表说 mechanical_regression 就必须如实降级
        assert by_factor["shensha"]["evaluation_status"] == "mechanical_regression"


if __name__ == "__main__":  # 便于 dev_tools 直接跑（pytest 仍是主入口）
    raise SystemExit(pytest.main([__file__, "-q"]))
