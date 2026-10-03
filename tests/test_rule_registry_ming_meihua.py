# -*- coding: utf-8 -*-
"""ming / meihua 规则注册表测试（Phase 5 Evidence Maturation）。

覆盖：registry 结构与字段完备（范式同六爻 tests/test_rule_registry.py）、
     出处指针逐条可解析、dim 必须是各科 evaluate.py WEIGHTS 真实维度、
     verified=false 诚实登记、真实 analyze 输出端到端挂接（含规则级状态
     **如实降级**：dayun/shensha 从学科基线 classical_holdout 降到
     mechanical_regression——注册表是比学科默认更细的真值）、
     claim_policy 断言边界（有方向/仅弱覆盖/无方向三种口径）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

REGISTRIES = {
    "ming": ROOT / "disciplines" / "ming" / "data" / "rules" / "rule_registry.json",
    "meihua": ROOT / "disciplines" / "meihua" / "data" / "rules" / "rule_registry.json",
}
SPLIT_WHITELIST = {
    "ming": ("tune", "holdout"),
    "meihua": ("tune", "holdout", "external_holdout"),
}


def _resolve_data_pointer(pointer: str):
    file_part, _, path_part = pointer.partition("#")
    data = json.loads((ROOT / file_part).read_text(encoding="utf-8"))
    cur = data
    for part in path_part.split("."):
        assert isinstance(cur, dict) and part in cur, f"指针断裂：{pointer}（{part}）"
        cur = cur[part]
    return cur


@pytest.fixture(scope="module", params=["ming", "meihua"])
def reg(request) -> tuple[str, dict]:
    disc = request.param
    return disc, json.loads(REGISTRIES[disc].read_text(encoding="utf-8"))


class TestRegistryShape:
    def test_schema_and_discipline(self, reg) -> None:
        disc, registry = reg
        assert registry["schema"] == "yi-rule-registry-v1"
        assert registry["discipline"] == disc

    def test_rule_fields_complete(self, reg) -> None:
        disc, registry = reg
        for rule in registry["rules"]:
            rid = rule.get("rule_id", "?")
            assert rid.startswith(f"{disc}."), f"{rid}：rule_id 须带学科前缀"
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

    def test_no_case_specific_rules(self, reg) -> None:
        import re
        _, registry = reg
        for rule in registry["rules"]:
            blob = json.dumps(rule, ensure_ascii=False)
            assert not re.search(r"\b(ZC|MH|reg)_?\d+", blob), \
                f"{rule['rule_id']}：疑似 case-specific 引用"

    def test_unique_rule_ids(self, reg) -> None:
        _, registry = reg
        ids = [r["rule_id"] for r in registry["rules"]]
        assert len(ids) == len(set(ids))

    def test_impl_files_exist(self, reg) -> None:
        disc, registry = reg
        disc_root = ROOT / "disciplines" / disc
        for rule in registry["rules"]:
            file_part = rule["impl"].split(":")[0]
            p = disc_root / file_part
            if not p.is_file():
                p = ROOT / file_part
            assert p.is_file(), f"{rule['rule_id']}：impl 文件不存在 {file_part}"


class TestSourceProvenance:
    def test_quote_pointers_resolve(self, reg) -> None:
        _, registry = reg
        checked = 0
        for rule in registry["rules"]:
            src = rule["source"]
            if src.get("quote_in_data"):
                value = _resolve_data_pointer(src["quote_in_data"])
                assert value, src["quote_in_data"]
                checked += 1
            if src.get("quote_in_code"):
                file_part, _, needle = src["quote_in_code"].partition("#")
                text = (ROOT / file_part).read_text(encoding="utf-8")
                assert needle in text, \
                    f"引文锚点不在实现文件中：{src['quote_in_code']}"
                checked += 1
        assert checked >= len(registry["rules"]), "每条规则应有可核查引文指针"

    def test_unverified_honest(self, reg) -> None:
        _, registry = reg
        for rule in registry["rules"]:
            if not rule["source"]["verified"]:
                assert rule["evaluation"]["status"] != "external_holdout", \
                    f"{rule['rule_id']}：未核引文不得虚标外部验证"


class TestEvaluationCoverage:
    def test_dims_are_real_eval_dims(self, reg) -> None:
        disc, registry = reg
        text = (ROOT / "disciplines" / disc / "scripts" / "evaluate.py").read_text(
            encoding="utf-8")
        for rule in registry["rules"]:
            dim = rule["evaluation"]["dim"]
            assert f'"{dim}"' in text, f"{rule['rule_id']}：dim {dim} 不在评分器权重表"
            for split in rule["evaluation"]["splits"]:
                assert split in SPLIT_WHITELIST[disc], \
                    f"{rule['rule_id']}：未知评测分列 {split}"

    def test_no_fake_classical_status_for_zero_applicable(self, reg) -> None:
        """0 applicable 的维度（dayun/shensha）不得标 classical_holdout。"""
        _, registry = reg
        for rule in registry["rules"]:
            note = rule["evaluation"]["note"]
            if "0 applicable" in note:
                assert rule["evaluation"]["status"] == "mechanical_regression", \
                    f"{rule['rule_id']}：0 applicable 须如实标 mechanical_regression"


class TestAttachEndToEnd:
    def _analyze(self, discipline: str) -> dict:
        from yishu_core.execution import YiRuntime
        rt = YiRuntime(str(ROOT))
        req = {"discipline": discipline, "question": "测试占问"}
        if discipline == "ming":
            req.update({"datetime": "1990-05-20 07:15", "gender": "男"})
        else:
            req.update({"mode": "time"})
        return rt.analyze(req)

    def test_ming_attach_and_downgrade(self) -> None:
        """规则级状态是比学科基线更细的真值：dayun/shensha 如实降级。"""
        from yishu_core.evidence import (
            attach_rule_registry,
            evidence_from_analyze,
        )
        from yishu_core.execution.registry import evaluation_baseline_of

        a = self._analyze("ming")
        ev = evidence_from_analyze("ming", a,
                                   evaluation_baseline=evaluation_baseline_of("ming"))
        assert evaluation_baseline_of("ming") == "classical_holdout"
        out = attach_rule_registry(ev, json.loads(
            REGISTRIES["ming"].read_text(encoding="utf-8")))
        by_factor = {e["factor"]: e for e in out}
        # 调候：从顶层键进证据，挂 rule_id + 注册表补书名
        th = by_factor["tiaohou"]
        assert th["rule_id"] == "ming.tiaohou"
        assert "穷通宝鉴" in th["source"]
        assert th["evaluation_status"] == "classical_holdout"
        # 格局成败：verdict code 先命中 pattern 规则（顺序优先级）
        assert by_factor["pattern"]["rule_id"] == "ming.pattern"
        # 从格 verdict（special_pattern）挂 cong_ge 规则
        assert by_factor["special_pattern"]["rule_id"] == "ming.cong_ge"
        # 如实降级：学科基线 classical_holdout → 规则级 mechanical_regression
        assert by_factor["dayun"]["rule_id"] == "ming.dayun"
        assert by_factor["dayun"]["evaluation_status"] == "mechanical_regression"
        assert by_factor["shensha"]["rule_id"] == "ming.shensha"
        assert by_factor["shensha"]["evaluation_status"] == "mechanical_regression"

    def test_meihua_attach_external_status(self) -> None:
        """体用关系域受外部独立集覆盖 → 状态如实升到 external_holdout。"""
        from yishu_core.evidence import (
            attach_rule_registry,
            evidence_from_analyze,
        )
        from yishu_core.execution.registry import evaluation_baseline_of

        a = self._analyze("meihua")
        ev = evidence_from_analyze("meihua", a,
                                   evaluation_baseline=evaluation_baseline_of("meihua"))
        out = attach_rule_registry(ev, json.loads(
            REGISTRIES["meihua"].read_text(encoding="utf-8")))
        by_factor = {e["factor"]: e for e in out}
        ty = by_factor["体用关系"]
        assert ty["rule_id"] == "meihua.ti_yong_shengke"
        assert ty["evaluation_status"] == "external_holdout"
        assert by_factor["生克之卦"]["rule_id"] == "meihua.sheng_ke"
        # 应期因子与 timing 派生证据都挂 yingqi 规则
        assert by_factor["应期"]["rule_id"] == "meihua.yingqi"


class TestClaimPolicy:
    def _policy_for(self, discipline: str) -> dict:
        from yishu_core.evidence import (
            claim_policy,
            evidence_from_analyze,
        )
        from yishu_core.execution.registry import evaluation_baseline_of
        a = TestAttachEndToEnd()._analyze(discipline)
        ev = evidence_from_analyze(discipline, a,
                                   evaluation_baseline=evaluation_baseline_of(discipline))
        return claim_policy(discipline, ev)

    def test_ming_no_directional(self) -> None:
        """命科不表态吉凶 → 断言边界必须禁止自行补充方向。"""
        cp = self._policy_for("ming")
        assert cp["directional"]["supported_n"] == 0
        assert "不得自行补充吉凶" in cp["boundary"]

    def test_liuyao_directional_supported(self) -> None:
        """六爻有方向表态且评测覆盖 → 可陈述（带口径纪律）。"""
        cp = self._policy_for("liuyao")
        assert cp["directional"]["supported_n"] >= 1
        assert "不是现实预测" in cp["boundary"]

    def test_weak_only_requires_disclaimer(self) -> None:
        """仅有出处/无评测覆盖的方向表态 → 必须声明未独立验证。"""
        ev = [{"id": "x", "discipline": "lingqi", "claim": "吉", "factor": "总判",
               "rule_id": "", "source": "《靈棋經》", "applicability": "",
               "observation": "", "effect": "吉",
               "evaluation_status": "source_only",
               "provenance": {"kind": "headline", "path": "conclusion"}}]
        from yishu_core.evidence import claim_policy
        cp = claim_policy("lingqi", ev)
        assert cp["directional"]["weak_n"] == 1
        assert "未独立验证" in cp["boundary"]
        assert cp["unassessed_n"] == 1

    def test_timing_candidates_counted(self) -> None:
        """应期候选计数：时间主张单列，不与吉凶混评。"""
        ev = [{"id": "y", "discipline": "liuyao", "claim": "应期候选第 1 位：2026-10-05",
               "factor": "应期", "rule_id": "", "source": "", "applicability": "",
               "observation": "date=2026-10-05", "effect": "",
               "evaluation_status": "classical_holdout",
               "provenance": {"kind": "timing", "path": "conclusion.应期明细[0]"}}]
        from yishu_core.evidence import claim_policy
        cp = claim_policy("liuyao", ev)
        assert cp["timing_candidates_n"] == 1
        assert "不与吉凶混评" in cp["timing_note"]
