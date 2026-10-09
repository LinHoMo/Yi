# -*- coding: utf-8 -*-
r"""六爻「用神伏藏而不得出」方向权重锁定（TECH-DEBT 2.3，2026-10-02；2026-10-09 判据改接结构）。

口径：《黄金策·千金赋》"伏无提挈终徒尔，飞不推开亦枉然"——伏神无提挈
（日月生扶、飞神空破、伏克飞皆无）则终不得出头。旧引擎对「伏而不得出」
只有应期效果、方向分零反馈；现补有界方向权重 -1.0。

2026-10-09 行为变更（缺陷 C，见 docs/CHANGELOG.md）：
  · 方向门控**不再嗅探 step3 散文**（旧实现靠 `"飞克伏" in summary_text` 与
    `re.search(r'飞神(\w)')` 抠字，上游改写措辞即静默变向）；
  · `can_emerge` 的唯一真值源改为 `advanced_analysis.hidden_spirit_analysis.details[]`
    （由 `classical_enhancements._evaluate_hidden_spirit_emergence` 算出）——
    step2 里那个恒真占位 `can_emerge = True` 已删，**旧本文件的 fixture 因此全部空跑**
    （`_fu_structural_state` 需要 `element`，而旧 fixture 只给 `branch` → 提前返回 None）；
  · 故本测试同步改为按新契约构造结构值，并新增「散文惰性」断言取代旧的「散文优先」断言。
本测试只验判据接线与有界性，不评现实吉凶（AGENTS.md 铁律三）。
"""
from liuyao_step5 import compute_fu_shen_adjustment


def _step2(use_god_category="妻财"):
    """用神伏藏的 step2 最小结构：伏=卯木，飞=午土（飞不生伏、不克伏、伏不绝于飞）。"""
    return {
        "has_fu_cang": True,
        "use_god_category": use_god_category,
        "fu_cang_detail": {"results": [{
            "fu_shen": {"branch": "卯", "element": "木"},
            "fei_shen": {"branch": "午", "element": "土"},
        }]},
    }


def _r(can_emerge=None, empty_branches=(), month_branch="子", day_branch="丑"):
    """chart/analyze 侧结构：旬空、月日干支，以及真实 can_emerge（缺陷 C 的唯一来源）。"""
    r = {
        "empty_branches": list(empty_branches),
        "divination_time": {"month_stem_branch": "戊" + month_branch,
                            "day_stem_branch": "己" + day_branch},
    }
    if can_emerge is not None:
        r["advanced_analysis"] = {"hidden_spirit_analysis": {
            "has_hidden_spirit": True,
            "details": [{"missing_relation": "妻财", "can_emerge": can_emerge}],
        }}
    return r


def test_hidden_and_cannot_emerge_gets_bounded_negative():
    """伏而不得出（真实结构 can_emerge=False，飞不空不破）→ -1.0，注记带所本。"""
    adj, note = compute_fu_shen_adjustment(_step2(), {"summary_text": "伏神休囚"}, _r(can_emerge=False))
    assert adj == -1.0
    assert "不得出" in note
    # 古籍出处外置且可回指（verdict_texts.json，§三；铁律一：结构层不出吉凶措辞）
    import json
    from pathlib import Path
    vt = json.loads((Path(__file__).resolve().parents[1]
                     / "disciplines" / "liuyao" / "data" / "rules" / "verdict_texts.json")
                    .read_text(encoding="utf-8"))
    entry = vt["step5_classical_notes"]["fu_no_emerge"]
    assert "伏无提挈终徒尔" in entry["basis"]
    assert "《黄金策" in entry["basis"]


def test_hidden_but_can_emerge_not_penalized():
    """伏而有提挈（真实 can_emerge=True）：新权重不触发，方向分不受此规则影响。"""
    adj, note = compute_fu_shen_adjustment(_step2(), {"summary_text": "伏神休囚"}, _r(can_emerge=True))
    assert adj == 0.0 and note == ""


def test_fei_empty_out_by_structure_not_prose():
    """飞神旬空 → 伏得出 +1.5，判据来自 chart 的 empty_branches 结构（非散文）。"""
    step2 = {"has_fu_cang": True, "use_god_category": "妻财",
             "fu_cang_detail": {"results": [{
                 "fu_shen": {"branch": "午", "element": "火"},
                 "fei_shen": {"branch": "子", "element": "水"}}]}}
    adj, note = compute_fu_shen_adjustment(
        step2, {"summary_text": "（散文什么都不写）"}, _r(can_emerge=False, empty_branches=("子",)))
    assert adj == 1.5
    assert "得出" in note


def test_prose_cannot_change_direction_score():
    """散文惰性（取代旧「文本优先」回归保护）：把旧关键词全塞进 step3，方向分仍由结构定。

    旧实现此处会给 +1.5（`"飞空得出" in summary_text` 命中），而盘面结构是
    飞不空不破、真实 can_emerge=False —— 即**上游改写一句话就能翻掉吉凶方向**。
    2026-10-09 起这类嗅探分支已删除，本断言把"散文不参与门控"钉住。
    """
    noisy = {"summary_text": "飞神午旬空（飞空得出），飞来生伏，伏神得出有力，忌神午火动克"}
    adj, note = compute_fu_shen_adjustment(_step2(), noisy, _r(can_emerge=False))
    assert adj == -1.0
    adj_none, _ = compute_fu_shen_adjustment(_step2(), noisy, _r(can_emerge=True))
    assert adj_none == 0.0


def test_no_hidden_use_god_is_noop():
    """用神不伏藏（无 fu_cang_detail）：恒零，不得误伤盘面可见用神的卦。"""
    adj, note = compute_fu_shen_adjustment(
        {"has_fu_cang": False, "fu_cang_detail": None},
        {"summary_text": "用神旺相"}, _r())
    assert adj == 0.0 and note == ""
