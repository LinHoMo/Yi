# -*- coding: utf-8 -*-
"""六爻古籍方向凶格（上限压档）的回归断言。

覆盖 TECH-DEBT §2.11 D1 落地的四条格与**它们的 applicability 边界**：
每格都配"该 fire"与"不该 fire"两侧——上一版实现正是因为漏了書源自带的限定
（婚姻章 vs 求财章、久事 vs 近事、休囚与受克并见），把 tune 从 97.2 压到 92.9
并误伤 HO008/WS001/SG001/YQ003 等 8 例。边界必须由测试钉住，不能靠注释。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "disciplines" / "liuyao" / "scripts"))
sys.path.insert(0, str(ROOT / "core"))

import classical_enhancements_direction as m  # noqa: E402


def yao(pos, branch, rel, *, world=False, response=False, moving=False,
        chg_branch=None, chg_rel=None, empty=False):
    return {"position": pos, "earthly_branch": branch, "six_relation": rel,
            "element": m.BRANCH_ELEMENTS[branch], "is_world": world,
            "is_response": response, "is_moving": moving,
            "changed_branch": chg_branch, "changed_six_relation": chg_rel,
            "is_empty": empty}


def step2(cls="功名科举", el="木", cat="父母", positions=(1,)):
    return {"question_class": cls, "use_god_element": el, "use_god_category": cat,
            "use_god_positions": [{"position": p} for p in positions]}


def step4(types: dict):
    return {"details": [{"position": p, "change_type": t, "changed_relation": ""}
                        for p, t in types.items()]}


def ids(caps):
    return {c["rule_id"] for c in caps}


# ───────────────────────── 1 出现无情 ─────────────────────────
def test_chuxian_wuqing_fires_when_no_officer_parent_reaches_world():
    # 世爻戌土；官鬼申金、父母子水既不生土也不与戌合，且不持世
    lines = [yao(5, "戌", "妻财", world=True), yao(4, "申", "官鬼"),
             yao(2, "亥", "父母")]
    caps = m.detect_direction_caps(lines, step2(), step4({}), "申", "亥", [])
    assert "liuyao.chuxian_wuqing" in ids(caps)


def test_chuxian_wuqing_quiet_when_officer_holds_world():
    lines = [yao(5, "申", "官鬼", world=True), yao(2, "亥", "父母")]
    assert "liuyao.chuxian_wuqing" not in ids(
        m.detect_direction_caps(lines, step2(), step4({}), "申", "亥", []))


def test_chuxian_wuqing_quiet_when_officer_generates_world():
    # 巳火生戌土 → 生合世爻，格不成
    lines = [yao(5, "戌", "妻财", world=True), yao(1, "巳", "官鬼")]
    assert "liuyao.chuxian_wuqing" not in ids(
        m.detect_direction_caps(lines, step2(), step4({}), "申", "亥", []))


def test_chuxian_wuqing_does_not_apply_outside功名():
    lines = [yao(5, "戌", "妻财", world=True), yao(4, "申", "官鬼")]
    for cls in ("其他", "求财", "行人", "婚姻"):
        assert "liuyao.chuxian_wuqing" not in ids(
            m.detect_direction_caps(lines, step2(cls=cls), step4({}), "申", "亥", [])), cls


# ───────────────────────── 2 兄弟持世克财 ─────────────────────────
def test_brother_world_fires_for_marriage_only():
    lines = [yao(3, "辰", "兄弟", world=True), yao(1, "亥", "妻财")]
    assert "liuyao.xiong_chi_shi_ke_cai" in ids(
        m.detect_direction_caps(lines, step2(cls="婚姻", el="木", cat="官鬼"),
                                step4({}), "酉", "巳", []))


def test_brother_world_silent_for_wealth_and_loss_questions():
    """求财/失物半边本轮不编码：自有基准里 4 例判吉，收窄前实测被误压。"""
    lines = [yao(3, "辰", "兄弟", world=True), yao(1, "亥", "妻财")]
    for cls in ("求财", "失物", "其他"):
        assert "liuyao.xiong_chi_shi_ke_cai" not in ids(
            m.detect_direction_caps(lines, step2(cls=cls), step4({}), "酉", "巳", [])), cls


# ───────────────────────── 3 世爻变鬼 ─────────────────────────
def test_shi_hua_gui_needs_both_weak_and_ke():
    lines = [yao(3, "辰", "妻财", world=True, moving=True, chg_branch="申", chg_rel="官鬼")]
    # 戌月冲辰＝月破，寅日木克土 → 两事并见
    assert "liuyao.shi_hua_gui" in ids(
        m.detect_direction_caps(lines, step2(cat="妻财", el="土"), step4({}), "戌", "寅", []))


def test_shi_hua_gui_silent_when_world_is_in_season():
    """書源是「世若休囚，受克…」两事并见；只受克不休囚不得入格（YQ003 教训）。

    辰月建：世爻辰土得令不囚、辰辰非冲不月破；只剩寅日木克一事 → 格不成。
    """
    lines = [yao(3, "辰", "妻财", world=True, moving=True, chg_branch="申", chg_rel="官鬼")]
    caps = m.detect_direction_caps(lines, step2(cat="妻财", el="土"), step4({}),
                                   "辰", "寅", [])
    assert "liuyao.shi_hua_gui" not in ids(caps), f"旺相之世仅受日克不得入变鬼格：{caps}"


def test_shi_hua_gui_requires_moving_and_officer_change():
    still = [yao(3, "辰", "妻财", world=True), yao(1, "亥", "官鬼")]
    assert "liuyao.shi_hua_gui" not in ids(
        m.detect_direction_caps(still, step2(el="土"), step4({}), "戌", "寅", []))
    no_gui = [yao(3, "辰", "妻财", world=True, moving=True, chg_branch="卯", chg_rel="兄弟")]
    assert "liuyao.shi_hua_gui" not in ids(
        m.detect_direction_caps(no_gui, step2(el="土"), step4({}), "戌", "寅", []))


# ───────────────────────── 4 元神无力 ─────────────────────────
def test_yuan_shen_wu_li_fires_for_chronic_illness_only():
    lines = [yao(1, "卯", "父母", moving=True), yao(4, "子", "官鬼")]
    caps = m.detect_direction_caps(lines, step2(cls="疾病·久病", el="木", cat="父母", positions=(1,)),
                                   step4({1: "化退神"}), "戌", "卯", [])
    assert "liuyao.yuan_shen_wu_li" in ids(caps)


def test_yuan_shen_wu_li_silent_for_recent_or_non_illness():
    """L1182 逐字「占近事岂可曰退？」——近事/行人/功名不得用本条（HO008/WS001/SG001 教训）。"""
    lines = [yao(1, "卯", "父母", moving=True), yao(4, "子", "官鬼")]
    for cls in ("疾病·近病", "行人", "功名科举", "其他"):
        caps = m.detect_direction_caps(lines, step2(cls=cls, el="木", cat="父母", positions=(1,)),
                                       step4({1: "化退神"}), "戌", "卯", [])
        assert "liuyao.yuan_shen_wu_li" not in ids(caps), cls


def test_yuan_shen_not_on_board_is_a_different_matter():
    """元神不上卦属伏藏，不在 L551「元神虽现」的适用面内（SG001 教训）。"""
    lines = [yao(1, "卯", "父母", moving=True), yao(3, "午", "兄弟")]
    caps = m.detect_direction_caps(lines, step2(cls="疾病·久病", el="木", cat="父母", positions=(1,)),
                                   step4({1: "化退神"}), "戌", "卯", [])
    assert "liuyao.yuan_shen_wu_li" not in ids(caps)


# ───────────────────────── 压档语义 ─────────────────────────
@pytest.mark.parametrize("v,expected,fired", [
    ("大吉", "凶", True), ("吉", "凶", True), ("平吉", "凶", True),
    ("凶", "凶", False), ("大凶", "大凶", False),
    # cap 的含义是"至多到这一档"：平凶比凶轻，所以 cap=凶 时同样要压下去
    ("平凶", "凶", True),
])
def test_apply_caps_only_downgrades(v, expected, fired):
    got, f = m.apply_caps(v, [{"cap": "凶"}])
    assert (got, f) == (expected, fired)


def test_apply_caps_takes_the_strictest_of_several():
    got, f = m.apply_caps("吉", [{"cap": "平凶"}, {"cap": "大凶"}])
    assert (got, f) == ("大凶", True)


def test_apply_caps_never_invents_a_unknown_rank():
    got, f = m.apply_caps("吉", [{"cap": "不知所云"}])
    assert (got, f) == ("吉", False)


# ───────────────────────── 端到端：那四例 ─────────────────────────
@pytest.mark.parametrize("cid", ["WSD002", "WSD006", "WSD022", "WSD024"])
def test_four_book_cases_now_judge_xiong(cid):
    """書源本案结局明写凶的 4 例，引擎方向必须为凶侧（TECH-DEBT §2.11 D1）。"""
    import case_runner
    from engine_chart import build_hexagram_result
    from thinking_chain import run_thinking_chain
    case = next(c for c in case_runner.load_cases() if c["id"] == cid)
    hx = case["hexagram"]
    yao_lines = case_runner.hex2yao(hx["original"], hx.get("changed"))
    assert yao_lines is not None, f"{cid} 卦象无法解析"
    dt = case_runner.resolve_case_time(case)["dt"]
    h = build_hexagram_result(yao_lines, case.get("question", ""), "manual",
                              dt.year, dt.month, dt.day, dt.hour)
    s5 = run_thinking_chain(h).get("thinking_chain", {}).get("step5_synthesis", {})
    assert s5.get("verdict") in ("凶", "大凶", "平凶"), f"{cid} 引擎仍判 {s5.get('verdict')}"
    assert s5.get("direction_caps"), f"{cid} 应有结构化凶格记录"


def test_direction_caps_are_registered_and_quotes_resolve_to_the_book():
    """四条格必须登记进注册表，且指针指向的引文确实逐字出现在書源那一行。

    指针链：rule_registry.source.quote_in_data → verdict_texts.json 短键 → quote，
    再回 data/sources/zengshan_buyi_dz.dz.txt 的 locator 行号逐字比对。
    注册表内不重复存引文（引文只存一处），所以必须靠指针解析来证明它没漂。
    """
    reg = json_load(ROOT / "disciplines" / "liuyao" / "data" / "rules" / "rule_registry.json")
    src_lines = (ROOT / "data" / "sources" / "zengshan_buyi_dz.dz.txt").read_text(
        encoding="utf-8").splitlines()
    by = {r["rule_id"]: r for r in reg["rules"]}
    for rid in ("liuyao.chuxian_wuqing", "liuyao.xiong_chi_shi_ke_cai",
                "liuyao.shi_hua_gui", "liuyao.yuan_shen_wu_li"):
        assert rid in by, f"{rid} 未登记进 rule_registry.json"
        s = by[rid]["source"]
        assert s.get("verified") is True and s.get("quote_in_data"), f"{rid} 缺可核查引文指针"
        file_part, _, dotted = s["quote_in_data"].partition("#")
        cur = json_load(ROOT / file_part)
        for part in dotted.split("."):
            assert isinstance(cur, dict) and part in cur, f"指针断裂：{s['quote_in_data']}"
            cur = cur[part]
        n = int(s["locator"].lstrip("L"))
        assert cur in src_lines[n - 1], f"{rid}：指针引文不在書源 L{n}"


def json_load(p):
    import json
    return json.loads(Path(p).read_text(encoding="utf-8"))


def test_module_emits_no_verdict_prose():
    """铁律一/§三：模块**发出的文本**里不许有断语字面量，展示句一律走 verdict_texts.json。

    只查函数体内会被返回/拼进产物的字符串常量与 f-string；模块级 docstring 是取证引文，
    按 §二「照录不改字」反而要求逐字，所以用 AST 精确划界，而不是按行去注释糊过去。
    """
    import ast
    tree = ast.parse(Path(m.__file__).read_text(encoding="utf-8"))
    banned = ("不惟难于", "非反目即生离", "难遂青云", "虽有如无", "相见如仇")
    emitted: list[str] = []
    for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
        for node in ast.walk(fn):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                emitted.append(node.value)
            elif isinstance(node, ast.JoinedStr):
                emitted.append("".join(v.value for v in node.values
                                       if isinstance(v, ast.Constant)
                                       and isinstance(v.value, str)))
    hits = [b for b in banned if any(b in e for e in emitted)]
    assert not hits, f"断语字面量从函数体内发出：{hits}"
