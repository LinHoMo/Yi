# -*- coding: utf-8 -*-
"""门与工具的"扫描面不得随仓库所在路径变化"回归。

实测教训（2026-10-09）：把复验用的 worktree 放在仓库内的 `scratch/clone_wt`，
三条门同时失真——
  · `tools/check.py` 真值源门扫到 **0 个文件**；
  · `tools/verdict_audit.py` 语料池被清空，报 **285 句"未外置"**（工作树内实测 0 句）；
  · `tools/check_doc_deadlinks.py` 的 `EXCLUDE_PARTS` 含 `archive`，仓库只要位于任何
    名为 archive/ 的目录下就会把**全部**文档判成非活动 → 扫 0 份 → "无死链"假绿。
根因都是同一句写法：用**绝对路径**的段名做排除（`"scratch" in p.parts`）。
本测试把"仓库坐在 scratch/archive 之下"这一形态固化下来：排除只准看仓库内相对路径。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def _fake_repo(tmp_path: Path, outer: str) -> Path:
    """造一个坐在 `tmp/<outer>/Yi` 的假仓库，内含门要扫的各类文件。"""
    repo = tmp_path / outer / "Yi"
    (repo / "disciplines" / "ming" / "scripts").mkdir(parents=True)
    (repo / "disciplines" / "ming" / "data").mkdir(parents=True)
    (repo / "tools").mkdir(parents=True)
    (repo / "docs").mkdir(parents=True)
    (repo / "core" / "yishu_core").mkdir(parents=True)
    (repo / "disciplines" / "ming" / "scripts" / "chart.py").write_text(
        'STEMS = "甲乙丙丁戊己庚辛壬癸"\n', encoding="utf-8")
    (repo / "tools" / "some_tool.py").write_text("X = {}\n", encoding="utf-8")
    (repo / "core" / "yishu_core" / "symbols.py").write_text(
        "HEAVENLY_STEMS = ['甲', '乙']\n", encoding="utf-8")
    (repo / "disciplines" / "ming" / "data" / "rules.json").write_text(
        '{"k": "旺相"}', encoding="utf-8")
    (repo / "docs" / "PLAN.md").write_text("# 规划\n正文\n", encoding="utf-8")
    return repo


@pytest.mark.parametrize("outer", ["scratch", "archive", "site"])
def test_truth_source_scan_not_blanketed_by_repo_location(tmp_path, monkeypatch, outer):
    """仓库放在 scratch/archive/site 之下时，真值源门仍须扫到文件。"""
    import check as gate

    repo = _fake_repo(tmp_path, outer)
    monkeypatch.setattr(gate, "ROOT", repo)
    monkeypatch.setattr(gate, "SCAN_ROOTS_OVERRIDE", None)
    files = gate._truth_source_files()
    names = {p.name for p in files}
    assert files, f"仓库位于 {outer}/ 下时扫描面归零（真值源门空转）"
    assert {"chart.py", "some_tool.py"} <= names
    # 真正该排除的仍是仓库内的 scratch：
    (repo / "tools" / "scratch").mkdir(parents=True)
    (repo / "tools" / "scratch" / "oneoff.py").write_text("Y = 1\n", encoding="utf-8")
    assert "oneoff.py" not in {p.name for p in gate._truth_source_files()}, \
        "tools/scratch 下的一次性脚本仍应被排除"


@pytest.mark.parametrize("outer", ["scratch", "archive"])
def test_deadlink_gate_keeps_docs_active(tmp_path, monkeypatch, outer):
    repo = _fake_repo(tmp_path, outer)
    import check_doc_deadlinks as cdd

    monkeypatch.setattr(cdd, "ROOT", repo)
    doc = repo / "docs" / "PLAN.md"
    assert cdd.is_active(doc), f"仓库位于 {outer}/ 下时文档被判成非活动（死链门会假绿）"


@pytest.mark.parametrize("outer", ["scratch", "guard"])
def test_verdict_audit_corpus_pool_not_emptied(tmp_path, monkeypatch, outer):
    repo = _fake_repo(tmp_path, outer)
    import verdict_audit as va

    monkeypatch.setattr(va, "ROOT", repo)
    pool = va._corpus("ming")
    assert pool.strip(), f"仓库位于 {outer}/ 下时语料池为空（审计会把所有句子判成未外置）"
    assert "旺相" in pool


def test_deadlink_still_excludes_repo_archive(tmp_path, monkeypatch):
    """反向：仓库**内部**的 archive/ 仍须被排除，不能为了修假绿把真排除拆掉。"""
    repo = _fake_repo(tmp_path, "work")
    (repo / "archive").mkdir(parents=True)
    old = repo / "archive" / "OLD.md"
    old.write_text("# 旧文\n", encoding="utf-8")
    import check_doc_deadlinks as cdd

    monkeypatch.setattr(cdd, "ROOT", repo)
    assert not cdd.is_active(old), "仓库内 archive/ 的排除被改坏了"
