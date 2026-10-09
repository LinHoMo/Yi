# -*- coding: utf-8 -*-
"""Synthesis 证据层测试（P0 合参信息粒度）。

覆盖：Evidence → Synthesis（normalize 挂 evidence → cross_examine）、
     conflicting evidence（冲突保留双方 conditions）、missing evidence（unassessed
     显式登记）、evaluation-status 传播进合参、旧接口兼容（adjudicate 不受影响）、
     「跨科同向不制造新事实」（无 trend/score 类输出）。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT / "synthesis"))

from evidence_cross import SCHEMA, cross_examine, selfcheck as ec_selfcheck  # noqa: E402
from normalize import normalize  # noqa: E402


def _rec(disc, direction, factor, claim, effect, status="classical_holdout",
         applicability="", source="《某书》"):
    return {"discipline": disc, "asked": "占事", "direction": direction,
            "evidence": [{
                "id": f"{disc}:x:0", "discipline": disc, "claim": claim,
                "factor": factor, "rule_id": "", "source": source,
                "applicability": applicability, "observation": "",
                "effect": effect, "evaluation_status": status,
                "provenance": {"kind": "headline", "path": "conclusion"},
            }]}


LIUYAO_SAMPLE = {
    "question": "本季度能否入职",
    "conclusion": {
        "方向": "吉", "verdict": "吉", "说明": "顺", "所本": "六爻纳甲·思维链五步",
        "应期": ["2026-10-05（冲空填实）"],
        "应期明细": [{"date": "2026-10-05", "rule": "冲空填实"}],
    },
    "advanced_analysis": {"clash_harmony": {"hexagram_type": "六合卦",
                                             "pairs": [], "summary": "六合卦，事主和合"}},
}


class TestNormalizeAttachesEvidence:
    def test_liuyao_record_has_evidence(self) -> None:
        rec = normalize("liuyao", LIUYAO_SAMPLE, at="2026-10-03 10:00")
        assert rec["evidence"], "归一化记录应携带结构化证据"
        kinds = {e["provenance"]["kind"] for e in rec["evidence"]}
        assert {"headline", "timing", "advanced_analysis"} <= kinds, kinds
        # 旧字段不丢：verdict/direction/timing 照旧
        assert rec["direction"] == "吉"
        assert rec["yingqi_offered"] == [{"date": "2026-10-05", "rule": "冲空填实"}]

    def test_baseline_from_registry(self) -> None:
        """评测状态传播：归一化证据的基线取自能力注册表（六爻=classical_holdout）。"""
        rec = normalize("liuyao", LIUYAO_SAMPLE, at="2026-10-03 10:00")
        headline = next(e for e in rec["evidence"]
                        if e["provenance"]["kind"] == "headline")
        assert headline["evaluation_status"] == "classical_holdout"

    def test_mechanical_discipline_no_direction(self) -> None:
        rec = normalize("ming", {"question": "命局排盘",
                                 "conclusion": {"strength": "中和", "pattern": "正官格",
                                                "方向": "", "说明": "机械推演"}},
                        at="1990-05-20 07:15")
        assert rec["direction"] == "平"
        assert all(e["effect"] == "" for e in rec["evidence"]), \
            "命科不表态吉凶，证据层不得制造方向"


class TestEvidenceCross:
    def test_selfcheck(self) -> None:
        ec_selfcheck()  # 同向/冲突保留条件/unassessed/弱状态/旧记录兼容

    def test_schema_and_no_fact_manufacturing(self) -> None:
        r = cross_examine([_rec("liuyao", "吉", "总判", "吉", "吉"),
                           _rec("ming", "平", "格局", "正官格", "平")])
        assert r["schema"] == SCHEMA
        # 不用「两个吉 > 一个凶」：输出无 trend/得分，只有一致性描述
        for banned in ("trend", "score", "verdict", "direction"):
            assert banned not in r, f"证据级检视不得输出 {banned}"
        assert r["consistency"]["same"] == 0  # 一吉一平 → 非纯同向
        assert len(r["directional"]["平"]) == 1

    def test_conflict_preserves_conditions(self) -> None:
        r = cross_examine([
            _rec("liuyao", "吉", "总判", "财爻旺相", "吉", applicability="月建生扶",
                 source="《增删卜易》"),
            _rec("ming", "凶", "总判", "七杀攻身", "凶", applicability="杀旺无制",
                 source="《子平真诠》"),
        ])
        assert len(r["conflicts"]) == 1
        c = r["conflicts"][0]
        sides = {s["discipline"]: s for s in c["sides"]}
        assert sides["liuyao"]["applicability"] == "月建生扶"
        assert sides["ming"]["applicability"] == "杀旺无制"
        assert sides["liuyao"]["source"] == "《增删卜易》"
        assert "不做平均" in c["note"]

    def test_missing_evidence_unassessed(self) -> None:
        """缺失证据必须显式 unassessed，不冒充表态。"""
        r = cross_examine([
            _rec("liuyao", "吉", "总判", "吉", "吉", status="unassessed", source=""),
            _rec("ming", None, "格局", "正官格", ""),  # 命科机械标签无方向
        ])
        assert any(g["evaluation_status"] == "unassessed"
                   for g in r["unassessed"]["evaluation_gaps"])
        assert "ming" in r["unassessed"]["silent_disciplines"]
        # 未表态学科不进方向计数
        assert r["directional"]["吉"] and not r["directional"]["凶"]

    def test_weak_status_flagged_in_dimension(self) -> None:
        r = cross_examine([_rec("ming", "吉", "格局", "吉", "吉",
                                status="classical_holdout")])
        dim = next(d for d in r["dimensions"] if d["factor"] == "格局")
        assert dim["relation"] == "single"
        assert dim["note"] == ""
        r2 = cross_examine([_rec("ming", "吉", "格局", "吉", "吉",
                                 status="source_only")])
        assert any(g["evaluation_status"] == "source_only"
                   for g in r2["unassessed"]["evaluation_gaps"])

    def test_legacy_adjudicate_untouched(self) -> None:
        """兼容：旧五条裁决接口行为不变（两个吉仍只是趋向，不制造事实由本层补足）。"""
        from cross_rules import adjudicate
        r = adjudicate([{"discipline": "liuyao", "asked": "占事", "direction": "吉"},
                        {"discipline": "ming", "asked": "占事", "direction": "吉"}])
        assert r["pattern"] == "same" and r["trend"] == "吉"

    def test_real_analyze_record_end_to_end(self) -> None:
        """端到端：真实引擎 analyze → normalize → cross_examine（单科冒烟）。"""
        from yishu_core.execution import YiRuntime
        rt = YiRuntime(str(ROOT))
        a = rt.analyze({"discipline": "liuyao", "question": "test", "mode": "time"})
        rec = normalize("liuyao", a, at="2026-10-03 10:00")
        r = cross_examine([rec])
        assert r["schema"] == SCHEMA
        assert r["dimensions"], "真实占问应产出维度"
        factors = {d["factor"] for d in r["dimensions"]}
        assert "总判" in factors and "应期" in factors, factors


class TestGuidanceEvidenceView:
    """guide 主合参文档内嵌证据级检视（「两个吉>一个凶」不再是最终逻辑）。

    合参指导的趋向声明必须带「方向级计数倾向」口径限定，异向结论与成立条件
    并列保留，缺失证据显式 unassessed；跨科同向只提升一致性描述强度。
    """

    def _arch(self, recs):
        from person import PersonArchive
        arch = PersonArchive.create(
            "TEST", "1990-05-20 07:15",
            ganzhi={"year": "庚午", "month": "辛巳", "day": "壬辰", "hour": "丙辰"},
            policy={"boundary": "day", "zi_hour": "night_same_day"})
        for r in recs:
            arch.add_divination(dict(r))
        return arch

    def _guidance_text(self, recs) -> str:
        from cross_rules import adjudicate
        from evidence_cross import attach_rule_registries
        from guidance import build_guidance
        arch = self._arch(recs)
        stored = arch.data["divinations"]
        adj = adjudicate(stored, policies=[r.get("calendar_policy") for r in stored])
        ev = cross_examine(attach_rule_registries(stored))
        return build_guidance(arch, adj, ev)

    def test_two_one_conflict_conditions_preserved(self) -> None:
        """两吉一凶：趋向降级为方向级计数倾向。"""
        text = self._guidance_text([
            _rec("liuyao", "吉", "总判", "财爻旺相", "吉", applicability="月建生扶"),
            _rec("ming", "吉", "用神", "中和偏旺", "吉"),
            _rec("liuyao", "凶", "应期", "逢冲不利", "凶", applicability="月破"),
        ])
        assert "证据级检视" in text
        assert "方向级计数倾向" in text          # 趋向口径限定
        assert "不制造新事实" in text

    def test_same_direction_only_consistency(self) -> None:
        """多科同向：只提升证据一致性描述强度。"""
        text = self._guidance_text([
            _rec("liuyao", "吉", "总判", "吉", "吉"),
            _rec("ming", "平", "格局", "中和", "平"),
        ])
        assert "一致性" in text
        assert "不制造新事实" in text

    def test_unassessed_gaps_listed(self) -> None:
        """缺失评测覆盖的证据在指导文档显式登记，不冒充已验证。"""
        text = self._guidance_text([
            _rec("liuyao", "吉", "总判", "吉", "吉", status="unassessed", source=""),
        ])
        assert "unassessed 评测缺口" in text
        assert "宁登记缺口，不制造假评测" in text

    def test_legacy_records_without_evidence_honest_note(self) -> None:
        """旧档案无结构化证据：如实声明检视不可用，描述强度不提升。"""
        rec = {"discipline": "liuyao", "asked": "占事", "direction": "吉",
               "verdict": "吉"}
        text = self._guidance_text([rec])
        assert "证据级检视不可用" in text
        assert "描述强度不提升" in text

    def test_legacy_signature_no_evidence_section(self) -> None:
        """兼容：不传 evidence_view 的旧调用路径不渲染检视小节，行为不变。"""
        from cross_rules import adjudicate
        from guidance import build_guidance
        arch = self._arch([_rec("liuyao", "吉", "总判", "吉", "吉")])
        stored = arch.data["divinations"]
        adj = adjudicate(stored, policies=[r.get("calendar_policy") for r in stored])
        text = build_guidance(arch, adj)
        assert "证据级检视" not in text
