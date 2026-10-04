# -*- coding: utf-8 -*-
"""命科外部独立集（external_holdout，`ming_external_cases.json`）守护测试。

防三类自欺（GOAL §十一：测试锁 provenance / split / non-promotion，不锁研究结论）：

1. **provenance 造假**：每例必须有书源逐字引文，且引文含所标书源类别原词、
   类别原词到引擎三档的映射与评测器一致——expected 不许凭空填。
2. **split 污染**：external_holdout 与主案例集（tune/holdout）零交集。
3. **静默晋升**：expected 只允许 strength 相关键（report-only）——若有人把外部集
   偷偷接进加权维度而不登记口径变更，这里会咬人。

实现注记：评测器映射用 **ast 从 `evaluate.py` 源码读取**，不 import 该模块——
conftest 路径序下（liuyao/scripts 先于 ming/scripts）裸名 `import chart/analyze`
会拿到六爻模块并缓存进 sys.modules，污染 test_ming_dayun（2026-10-04 实测）；
同因本测试不用 spec_from_file_location 执行 evaluate（其模块体自带裸名 import）。
"""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_PATH = ROOT / "disciplines" / "ming" / "data" / "cases" / "ming_external_cases.json"
MAIN_PATH = ROOT / "disciplines" / "ming" / "data" / "cases" / "ming_classical_cases.json"
EVAL_SRC = (ROOT / "disciplines" / "ming" / "scripts" / "evaluate.py").read_text(encoding="utf-8")


def _mapping_from_eval_source() -> dict:
    """从 evaluate.py 源码 ast 提取 STRENGTH_BOOK_CATEGORY 字面量（不执行模块）。"""
    tree = ast.parse(EVAL_SRC)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            getattr(t, "id", "") == "STRENGTH_BOOK_CATEGORY" for t in node.targets
        ) and isinstance(node.value, ast.Dict):
            keys = [ast.literal_eval(k) for k in node.value.keys]
            vals = [ast.literal_eval(v) for v in node.value.values]
            return dict(zip(keys, vals))
    raise AssertionError("evaluate.py 缺 STRENGTH_BOOK_CATEGORY 字面量（映射被移动？请同步本测试）")


def _cases() -> dict:
    d = json.loads(EXT_PATH.read_text(encoding="utf-8"))
    assert d["schema"] == "yi-ming-external-cases/1"
    ids = d["splits"]["external_holdout"]
    by_id = {c["id"]: c for c in d["cases"]}
    assert set(ids) == set(by_id), "splits 与 cases 不一致"
    return by_id


def test_external_cases_provenance_honest():
    """每例：书源逐字引文含类别原词；expected.strength 与评测器映射一致。"""
    mapping = _mapping_from_eval_source()
    for cid, case in _cases().items():
        assert case["split"] == "external_holdout", f"{cid}：须恒为 external_holdout"
        assert case["book"] == "滴天髓阐微", f"{cid}：书源须为阐微"
        cat = case["expected"]["strength_book_category"]
        assert cat in mapping, f"{cid}：未知书源类别 {cat}"
        assert cat in case["source_quote"], \
            f"{cid}：引文不含类别原词「{cat}」——expected 必须指得回原文"
        assert case["expected"]["strength"] == mapping[cat], \
            f"{cid}：与评测器映射漂移（{cat} 应为 {mapping[cat]}）"
        for k in ("year", "month", "day", "hour"):
            assert len(case["pillars"].get(k) or "") == 2, f"{cid}：{k} 柱缺失"


def test_external_split_isolated_from_main_store():
    """外部集与主案例集（tune/holdout）零共享——永不调参的物理隔离。"""
    main = json.loads(MAIN_PATH.read_text(encoding="utf-8"))
    main_ids = {c["id"] for c in main["cases"]}
    cases = _cases()
    assert not (set(cases) & main_ids), "外部集案例不得混入主案例集"
    for split, ids in main["splits"].items():
        overlap = set(ids) & set(cases)
        assert not overlap, f"{split} 与外部集重叠：{sorted(overlap)}"


def test_external_expected_is_report_only():
    """expected 只允许 strength 相关键（report-only）。

    若外部集要接入加权维度（pillars/调候/格局…），那是**口径变更**：
    必须先在 docs/CHANGELOG.md 登记，再有意扩展本白名单——不许静默晋升。
    """
    allowed = {"strength", "strength_book_category"}
    for cid, case in _cases().items():
        extra = set(case.get("expected") or {}) - allowed
        assert not extra, f"{cid}：出现未登记的可计分维度 {sorted(extra)}"
