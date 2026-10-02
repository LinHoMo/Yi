# -*- coding: utf-8 -*-
"""六爻「用神伏藏而不得出」方向权重锁定（TECH-DEBT 2.3，2026-10-02）。

口径：《黄金策·千金赋》"伏无提挈终徒尔，飞不推开亦枉然"——伏神无提挈
（日月生扶、飞神空破、伏克飞皆无）则终不得出头。旧引擎对「伏而不得出」
只有应期效果、方向分零反馈；现补有界方向权重 -1.0，判据读
step2 `fu_cang_detail.results[].can_emerge` 结构（不嗅探文本）。
本测试只验判据接线与有界性，不评现实吉凶（AGENTS.md 铁律三）。
"""
from liuyao_step5 import compute_fu_shen_adjustment
from narrative_utils import note_text


def _step2(can_emerge):
    """构造用神伏藏的 step2 最小结构：fu_cang_detail 只含用神伏/飞对。"""
    return {
        "has_fu_cang": True,
        "fu_cang_detail": {"results": [{"can_emerge": can_emerge,
                                        "fu_shen": {"branch": "子"},
                                        "fei_shen": {"branch": "寅"}}]},
    }


def test_hidden_and_cannot_emerge_gets_bounded_negative():
    """伏而不得出（结构 can_emerge=False，文本无得出/泄气字样）→ -1.0，注记带所本。"""
    step2 = _step2(can_emerge=False)
    step3 = {"summary_text": "伏神休囚，飞神不空不破"}  # 不含任何旧文本分支关键词
    adj, note = compute_fu_shen_adjustment(step2, step3, {})
    assert adj == -1.0
    assert "不得出" in note
    # 古籍出处外置且可回指（note_text 取 text；basis 存于同一 JSON 条目）
    import json
    from pathlib import Path
    vt = json.loads((Path(__file__).resolve().parents[1]
                     / "disciplines" / "liuyao" / "data" / "rules" / "verdict_texts.json")
                    .read_text(encoding="utf-8"))
    entry = vt["step5_classical_notes"]["fu_no_emerge"]
    assert "伏无提挈终徒尔" in entry["basis"]
    assert "《黄金策" in entry["basis"]


def test_hidden_but_can_emerge_not_penalized():
    """伏而有提挈（can_emerge=True）：新权重不触发，方向分不受此规则影响。"""
    step2 = _step2(can_emerge=True)
    step3 = {"summary_text": "伏神休囚，飞神不空不破"}
    adj, note = compute_fu_shen_adjustment(step2, step3, {})
    assert adj == 0.0
    assert note == ""


def test_text_branches_keep_priority_over_structure():
    """旧文本分支优先级不变：飞空得出仍 +1.5（回归保护，行为零漂移）。"""
    step2 = _step2(can_emerge=False)
    step3 = {"summary_text": "飞神寅旬空（飞空得出），伏神得出有力"}
    adj, note = compute_fu_shen_adjustment(step2, step3, {})
    assert adj == 1.5
    assert "得出" in note


def test_no_hidden_use_god_is_noop():
    """用神不伏藏（无 fu_cang_detail）：恒零，不得误伤盘面可见用神的卦。"""
    adj, note = compute_fu_shen_adjustment(
        {"has_fu_cang": False, "fu_cang_detail": None},
        {"summary_text": "用神旺相"}, {})
    assert adj == 0.0 and note == ""
