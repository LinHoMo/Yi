# -*- coding: utf-8 -*-
"""六爻规则注册表测试（P0 Rule → Evidence → Evaluation 链）。

覆盖：registry schema 与九个优先域齐全、出处指针（quote_in_data / quote_in_code）
     逐条可解析（引文真实存在于仓库）、评测覆盖只登记真实维度（dim 必须在
     liuyao evaluate.py WEIGHTS 里）、无引文指针必须 verified=false、
     evidence 挂接后 rule_id 可回溯。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

REG_PATH = ROOT / "disciplines" / "liuyao" / "data" / "rules" / "rule_registry.json"


@pytest.fixture(scope="module")
def registry() -> dict:
    return json.loads(REG_PATH.read_text(encoding="utf-8"))


PRIORITY_DOMAINS = {
    "三会局", "独发/独静", "反吟/伏吟", "六合/六冲", "旬空（真空/假空）",
    "墓库", "进退神", "用神多现", "应期",
}


def _resolve_data_pointer(pointer: str):
    """`file#dotted.path` → 值（存在性由断言保证）。"""
    file_part, _, path_part = pointer.partition("#")
    p = ROOT / file_part
    data = json.loads(p.read_text(encoding="utf-8"))
    cur = data
    for part in path_part.split("."):
        assert isinstance(cur, dict) and part in cur, f"指针断裂：{pointer}（{part}）"
        cur = cur[part]
    return cur


class TestRegistryShape:
    def test_schema_and_discipline(self, registry) -> None:
        assert registry["schema"] == "yi-rule-registry-v1"
        assert registry["discipline"] == "liuyao"

    def test_priority_domains_covered(self, registry) -> None:
        domains = {r["domain"] for r in registry["rules"]}
        missing = PRIORITY_DOMAINS - domains
        assert not missing, f"九个优先规则域缺：{missing}"

    def test_rule_fields_complete(self, registry) -> None:
        for rule in registry["rules"]:
            rid = rule.get("rule_id", "?")
            assert rid.startswith("liuyao."), f"{rid}：rule_id 须带学科前缀"
            assert rule.get("domain"), rid
            assert rule.get("impl"), f"{rid}：缺实现位置"
            assert rule.get("applicability"), f"{rid}：缺适用条件"
            src = rule.get("source") or {}
            assert src.get("book"), f"{rid}：缺古籍出处"
            assert isinstance(src.get("verified"), bool), f"{rid}：缺 verified 标记"
            ev = rule.get("evaluation") or {}
            assert ev.get("status"), f"{rid}：缺评测覆盖登记"
            assert ev.get("splits") and ev.get("dim"), f"{rid}：缺评测分列/维度"
            assert ev.get("note"), f"{rid}：缺评测覆盖说明"

    def test_no_case_specific_rules(self, registry) -> None:
        """铁律：禁止 case-specific 规则——impl/出处里不得引用具体案例 id。"""
        import re
        for rule in registry["rules"]:
            blob = json.dumps(rule, ensure_ascii=False)
            assert not re.search(r"\b(ZC|MH|reg)_?\d+", blob), \
                f"{rule['rule_id']}：疑似 case-specific 引用"

    def test_unique_rule_ids(self, registry) -> None:
        ids = [r["rule_id"] for r in registry["rules"]]
        assert len(ids) == len(set(ids))


class TestSourceProvenance:
    def test_quote_in_data_resolves(self, registry) -> None:
        checked = 0
        for rule in registry["rules"]:
            pointer = rule["source"].get("quote_in_data")
            if not pointer:
                continue
            value = _resolve_data_pointer(pointer)
            if isinstance(value, str):
                assert value.strip(), pointer
            else:
                assert value, pointer  # 列表/结构指针须非空
            checked += 1
        assert checked >= 4, f"逐字引文指针过少：{checked}"

    def test_quote_in_code_resolves(self, registry) -> None:
        checked = 0
        for rule in registry["rules"]:
            anchor = rule["source"].get("quote_in_code")
            if not anchor:
                continue
            file_part, _, needle = anchor.partition("#")
            text = (ROOT / file_part).read_text(encoding="utf-8")
            assert needle in text, f"引文锚点不在实现文件中：{anchor}"
            checked += 1
        assert checked >= 2, f"代码锚点过少：{checked}"

    def test_every_rule_has_one_quote_pointer(self, registry) -> None:
        """每条规则至少一种可核查引文指针；两种都没有必须 verified=false。"""
        for rule in registry["rules"]:
            src = rule["source"]
            has_pointer = bool(src.get("quote_in_data") or src.get("quote_in_code"))
            if not has_pointer:
                assert src["verified"] is False, \
                    f"{rule['rule_id']}：无引文指针却声称 verified"
                assert "缺口" in src.get("locator", "") or "待" in src.get("locator", ""), \
                    f"{rule['rule_id']}：缺引文应明示为缺口"

    def test_impl_files_exist(self, registry) -> None:
        disc_root = ROOT / "disciplines" / "liuyao"
        for rule in registry["rules"]:
            impl = rule["impl"]
            file_part = impl.split(":")[0]
            # impl 路径相对学科根；内核引用（core/...）相对仓库根
            p = disc_root / file_part
            if not p.is_file():
                p = ROOT / file_part
            assert p.is_file(), f"{rule['rule_id']}：impl 文件不存在 {file_part}"


class TestEvaluationCoverage:
    def test_dims_are_real_eval_dims(self, registry) -> None:
        """评测覆盖只登记真实维度：dim 必须是 liuyao evaluate.py WEIGHTS 的键。"""
        text = (ROOT / "disciplines" / "liuyao" / "scripts" / "evaluate.py").read_text(
            encoding="utf-8")
        for rule in registry["rules"]:
            dim = rule["evaluation"]["dim"]
            assert f'"{dim}"' in text, f"{rule['rule_id']}：dim {dim} 不在评分器权重表"
            for split in rule["evaluation"]["splits"]:
                assert split in ("tune", "holdout", "yingqi_holdout", "wikisource_holdout",
                                 "wikisource_direction", "huozhulin_holdout",
                                 "suigui_holdout"), \
                    f"{rule['rule_id']}：未知评测分列 {split}"

    def test_unverified_honest(self, registry) -> None:
        """unverified 规则（若有）不得虚标外部验证。不锁「必须存在缺口」——
        缺口补挂后合法消失（2026-10-04f 三合局引文已逐字挂接翻 verified）；
        无指针必 verified=false 的护栏由 test_every_rule_has_one_quote_pointer 承担。"""
        for r in registry["rules"]:
            if not r["source"]["verified"]:
                assert r["evaluation"]["status"] != "external_holdout", \
                    f"{r['rule_id']}：未核引文不得虚标外部验证"


class TestEvidenceAttach:
    def test_registry_feeds_evidence(self, registry) -> None:
        from yishu_core.evidence import attach_rule_registry
        ev = [{"id": "liuyao:t:0", "discipline": "liuyao", "claim": "应期候选第 1 位：2026-10-05",
               "factor": "应期", "rule_id": "", "source": "", "applicability": "",
               "observation": "", "effect": "", "evaluation_status": "unassessed",
               "provenance": {"kind": "timing", "path": "conclusion.应期明细[0]"}}]
        out = attach_rule_registry(ev, registry)
        assert out[0]["rule_id"] == "liuyao.yingqi_rules"
        assert out[0]["evaluation_status"] == "classical_holdout"
