# -*- coding: utf-8 -*-
"""六爻古典增强：独发 / 独静识别域（自 classical_enhancements.py 按域切出）。

巨石看门狗（学科 .py > 2200 行）触发后的拆分：独发独静只依赖 narrative_utils 的
断语素材与本模块内的卦爻结构判定，与其他增强域（伏神/暗动/三合/长生）无耦合，
单独成域依赖最单向：classical_enhancements → 本模块 → narrative_utils。

断语素材（引文/标签句）一律取自 `data/rules/verdict_texts.json`
（经 narrative_utils 加载），代码内不写字面量。
"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

from narrative_utils import (  # noqa: E402
    DUFA_NOTES,
    DUFA_QUOTE,
    LUANDONG_LABELS,
    _pos_to_name,
)

__all__ = ["analyze_du_fa_du_jing", "analyze_luandong", "attach_luandong_looks"]


def analyze_du_fa_du_jing(result):
    """独发 / 独静 识别（《增删卜易·独发章第三十一》）。

    原书："五爻俱動，一爻不動，謂之獨靜；五爻不動，一爻獨動，謂之獨發。"
    但同章野鹤紧接着立界："事之成敗，由乎用神；應期遲速，亦由乎用神……如捨其
    用神，執之而決事者，謬也。"——故此处**只标象、给结构性提示，不改吉凶主判**，
    亦不进主分：独发之爻为事情主驱动力、独静之爻为事情枢纽，仅作正文辅助说明。

    返回 {type, position, name, branch, six_relation, is_use_god, is_world,
          driving_note, classical_quote, count}；非独发独静时 type 为 ""。
    """
    out = {
        "type": "",
        "position": None,
        "name": "",
        "branch": "",
        "six_relation": "",
        "is_use_god": False,
        "is_world": False,
        "driving_note": "",
        "classical_quote": DUFA_QUOTE,
        "count": {"moving": 0, "static": 0},
    }

    hex_info = result.get("original_hexagram")
    if not isinstance(hex_info, dict):
        return out
    yao_lines = hex_info.get("yao_lines", []) or []
    if len(yao_lines) != 6:
        return out

    moving = [y for y in yao_lines if isinstance(y, dict) and y.get("is_moving")]
    static = [y for y in yao_lines if isinstance(y, dict) and not y.get("is_moving")]
    out["count"] = {"moving": len(moving), "static": len(static)}

    target = None
    if len(moving) == 1 and len(static) == 5:
        out["type"] = "独发"
        target = moving[0]
    elif len(static) == 1 and len(moving) == 5:
        out["type"] = "独静"
        target = static[0]
    else:
        return out

    step2 = result.get("_step2_data") if isinstance(result.get("_step2_data"), dict) else {}
    use_god_branch = ""
    sel = step2.get("selected_use_god") or {}
    if isinstance(sel, dict):
        use_god_branch = sel.get("earthly_branch", "")

    out["position"] = target.get("position")
    out["name"] = target.get("name") or _pos_to_name(target.get("position") or 0)
    out["branch"] = target.get("earthly_branch", "")
    out["six_relation"] = target.get("six_relation", "")
    out["is_use_god"] = bool(use_god_branch) and out["branch"] == use_god_branch
    out["is_world"] = bool(target.get("is_world"))

    # 只作结构提示：是否临用神/世爻，决定"主驱动力"还是"核心阻滞点"落在何处
    if out["type"] == "独发":
        role = "用神自为发动" if out["is_use_god"] else ("世爻发动" if out["is_world"] else "他爻发动")
        out["driving_note"] = DUFA_NOTES["du_fa"].format(
            name=out["name"], branch=out["branch"], role=role)
    else:
        role = "用神独静" if out["is_use_god"] else ("世爻独静" if out["is_world"] else "他爻独静")
        out["driving_note"] = DUFA_NOTES["du_jing"].format(
            name=out["name"], branch=out["branch"], role=role)
    return out


# ---------------------------------------------------------------- 乱动卦（纯结构象）
# 【第一百六十七批】rule_registry liuyao.huozhulin_luandong 条「未实现_乱动标记」的落地。
# 【第一百七十批】《火珠林》源L27 四看口诀收口：①「一看世上旁爻生财旺相，忌应爻克世」与
# ②「二看世下亲爻财官喜静」拆为两条**纯结构标签**（look1/look2），只标象不打分；
# ③「三看何爻最旺为用神」裁定为**与现行 `_use_god_priority` 同向、不另立口径**
# （书载口径＝《火珠林》源L20-23 四季旺相休囚死表，与内核 step3 同一把尺）；④与已落地之
# liuyao.dufa_dujing 相通。据实收口见 docs/CHANGELOG.md 第一百七十批。
# 纪律与独发独静**完全同策略**：只标结构象、不打分、不改用神选取、不改判定值。
# 为什么放在本模块：`du_fa_du_jing` 已经算出 count{moving,static}（唯一真值源），
# 另起一套数法就是第二个真值源——本条直接读它。
# **边界（勿越界）**：《火珠林》源L33 的取用口径「乱动之卦只取旺爻，旺爻即用神也」
# **不另立实现**（第一百七十批裁定同向，见上）——本条只报结构事实，
# 不据此取用神、不据此定吉凶。
LUANDONG_THRESHOLD = 2      # 动爻数 > 2 即乱动（与注册表 gap_detail 登记口径一致）


def _luandong_step2(result) -> dict:
    """取 step2 数据（用神类别/位置/世应），读不到就返回空 dict。

    与 `analyze_du_fa_du_jing` 同一取法：`_step2_data` 由 thinking_chain 在 step2 后写入。
    """
    step2 = result.get("_step2_data")
    return step2 if isinstance(step2, dict) else {}


def _luandong_wang_score(result, branch: str) -> float | None:
    """按内核四季旺相休囚死表取该支的旺相分（唯一真值源＝step3 的 element_strength_in_month）。

    判据不新造：`advanced_analysis.element_strength` 已由 effects.py 用同一把尺
    算好逐爻 `overall`（旺/相/偏弱/衰），直接读它；读不到则回退到月令旺相表自算一次
    （同一内核函数，不引入第二口径）。返回 None 表示「无法判定」，调用方按不判处理。
    """
    if not branch:
        return None
    adv = result.get("advanced_analysis")
    if isinstance(adv, dict):
        es = adv.get("element_strength")
        if isinstance(es, dict):
            for d in (es.get("details") or []):
                if isinstance(d, dict) and d.get("branch") == branch:
                    label = d.get("overall") or ""
                    if label:
                        return _WANG_LABEL_SCORE.get(label)
    # 回退：按 divination_time 的月令旺相表自算（与 step3 同一内核函数）
    try:
        from yishu_core.relations import element_strength_in_month
        from yishu_core.symbols import BRANCH_ELEMENTS
    except Exception:
        return None
    dt = result.get("divination_time") or {}
    month_sb = dt.get("month_stem_branch") or ""
    month_branch = month_sb[1:] if len(month_sb) >= 2 else ""
    if not month_branch:
        return None
    el = BRANCH_ELEMENTS.get(branch, "")
    if not el:
        return None
    try:
        label = element_strength_in_month(el, month_branch)
    except Exception:
        return None
    return _WANG_LABEL_SCORE.get(label or "")


# 旺相标签 → 分（与 step3 `strength_to_score` 同口径的粗档：旺/相为旺侧）
# 判据单一真值源在 `yishu_core.relations.element_strength_in_month`（四季旺相休囚死表），
# 本表只把它的字面量档位映成可比较的分数，**不改判据本身**。
_WANG_LABEL_SCORE = {
    "旺": 5.0, "相": 4.0,
    "中和": 3.0, "偏弱": 2.0, "衰": 1.5, "休": 1.0, "囚": 1.0, "死": 0.5,
}
_WANG_MIN_SCORE = 4.0    # 「旺相」门槛：旺(5)／相(4) 过线，其余不过


def analyze_luandong(result):
    """乱动卦识别（《火珠林·乱动法总纲》＋源L27 四看口诀的结构标签化）。

    书源：《火珠林》源L33 逐字「乱动之卦只取旺爻，旺爻即用神也。生克吉凶皆在此爻。」；
    源L27 逐字「一看世上旁爻生财旺相，忌应爻克世；二看世下亲爻财官喜静；
    三看何爻最旺为用神，如发动，动要生世；四看独发之爻，旺相最急，休囚事慢。」；
    源L25 逐字「独发易取，乱动难寻」——以「难寻」点明乱动与独发为难易之别。

    本判据**只出结构事实**：①是否乱动（动爻数>2）；②源L27 一看/二看的两个结构标签
    （旁爻生助用神且旺相、应爻是否克世；世下亲爻财/官是否安静）。
    **不实现《火珠林》源L33 逐字「乱动之卦只取旺爻，旺爻即用神也」的取用口径**：
    第一百七十批裁定「旺」的书载口径（源L20-23 四季旺相休囚死表，与内核 step3
    同一把尺），并判定该口径与现行 `_use_god_priority` **同向、故不另立**
    （同向依据：现行序「明动有力＞空逢日冲＞暗动＞应＞世＞临月建＞临日辰＞静而完整
    ＞动而空/破/自伤」中，「动而不空且非自伤」居首＝源L33「若发动，却要生世之爻为用神」
    的同向读法，「静而完整（不空不破）」居次＝「若伏藏安静要旺相」的同向读法）。
    见 rule_registry liuyao.huozhulin_luandong 条 gap_detail 与 CHANGELOG 第一百七十批。

    返回 {is_luandong, moving_count, positions, classical_quote, note,
          look1, look2}；后两者为源L27 一看/二看的纯结构标签（只标象）。
    """
    out = {
        "is_luandong": False,
        "moving_count": 0,
        "positions": [],
        "classical_quote": LUANDONG_LABELS.get("古典引文", ""),
        "note": "",
        "look1": None,
        "look2": None,
    }
    hex_info = result.get("original_hexagram")
    if not isinstance(hex_info, dict):
        return out
    yao_lines = hex_info.get("yao_lines", []) or []
    if len(yao_lines) != 6:
        return out

    moving = [y for y in yao_lines if isinstance(y, dict) and y.get("is_moving")]
    out["moving_count"] = len(moving)
    out["positions"] = [y.get("position") for y in moving if isinstance(y.get("position"), int)]
    out["is_luandong"] = len(moving) > LUANDONG_THRESHOLD
    _pos = "、".join(f"{p}爻" for p in out["positions"]) or "无"
    out["note"] = (LUANDONG_LABELS.get("乱动提示" if out["is_luandong"] else "非乱动提示", "")
                   .format(n=len(moving), positions=_pos))

    # ---- 源L27 一看/二看：纯结构标签（第一百七十批，只标象不打分） ----
    # ⚠ 这两看要读 step2 的用神/世应，而 `enhance_reading` 在 step2 **之前**跑
    # （thinking_chain: enhance_reading → step1 → step2），此处必然读不到。
    # 故照 `shi_yao_relation` 的既有范式：**由 step2 完成后补挂**
    # （`attach_luandong_looks(result, step2_data)`，见下），本函数只出占位 None。
    out["look1"] = None
    out["look2"] = None
    return out


def attach_luandong_looks(result, step2_data) -> None:
    """step2 完成后补挂《火珠林》源L27 一看/二看的结构标签（第一百七十批）。

    书源逐字（源L27）：「一看世上旁爻生财旺相，忌应爻克世；二看世下亲爻财官喜静；
    三看何爻最旺为用神，如发动，动要生世；四看独发之爻，旺相最急，休囚事慢。」

    为什么补挂而不是在 `analyze_luandong` 里直接算：`enhance_reading` 运行在
    `thinking_chain` 的 step1 **之前**，那时 `_step2_data` 还不存在，
    在 `analyze_luandong` 里读必得 None——那会让标签**永远为空而无人知晓**
    （静默缺陷的典型形态）。既有范式：`shi_yao_relation` 同样在 step2 后补挂
    （`thinking_chain.py` step2 之后显式调用）。

    只标象、不打分、不改用神选取、不改判定值（与独发独静同策略）。
    """
    if not isinstance(result, dict):
        return
    adv = result.get("advanced_analysis")
    if not isinstance(adv, dict):
        return
    ld = adv.get("luandong")
    if not isinstance(ld, dict) or not isinstance(step2_data, dict):
        return
    hex_info = result.get("original_hexagram")
    yao_lines = (hex_info or {}).get("yao_lines", []) if isinstance(hex_info, dict) else []
    if len(yao_lines) != 6:
        return
    with_step2 = dict(result)
    with_step2["_step2_data"] = step2_data
    ld["look1"] = _look1_pang_sheng_wang(with_step2, yao_lines)
    ld["look2"] = _look2_shixia_qin_jing(with_step2, yao_lines)


def _look1_pang_sheng_wang(result, yao_lines) -> dict:
    """《火珠林》源L27 一看逐字「一看世上旁爻生财旺相，忌应爻克世」→ 结构标签。

    判据（全部读已算好的结构化字段，不新造真值源）：
      · 「旁爻生（财）旺相」：**旁爻**（非世爻）中，有六亲为用神之**原神**
        （生助用神之五行所对应六亲）且**旺相**（内核四季旺相表分 ≥4，与 step3 同一把尺）；
      · 「忌应爻克世」：应爻五行**克**世爻五行（`wuxing_relation(世, 应) == 克我`）。
    只报这两个结构事实，**不据此取用神、不据此定吉凶、不打分**。
    取不到用神/世应位置时返回 None（调用方按「不判」处理，不猜）。
    """
    step2 = _luandong_step2(result)
    if not step2:
        return None
    world_pos = step2.get("world_position")
    if not world_pos:
        return None
    # 应爻位置：由世爻按六爻纳甲定（内核唯一真值源，与 step2 同法）
    try:
        from yishu_core.najia import response_position as _resp_of
        resp_pos = _resp_of(world_pos)
    except Exception:
        resp_pos = None

    world_el = resp_el = ""
    yuan_rel = ""
    for y in yao_lines:
        if not isinstance(y, dict):
            continue
        if y.get("position") == world_pos:
            world_el = _branch_element_of(y.get("earthly_branch", ""))
        elif resp_pos is not None and y.get("position") == resp_pos:
            resp_el = _branch_element_of(y.get("earthly_branch", ""))

    # 用神原神的六亲名（step2 已算好 yuan_shen.category）
    ys = step2.get("yuan_shen")
    if isinstance(ys, dict):
        yuan_rel = ys.get("category") or ""

    pang_yuan_wang = []
    if yuan_rel:
        for y in yao_lines:
            if not isinstance(y, dict) or y.get("position") == world_pos:
                continue
            if y.get("six_relation") != yuan_rel:
                continue
            score = _luandong_wang_score(result, y.get("earthly_branch", ""))
            if score is not None and score >= _WANG_MIN_SCORE:   # 旺/相（与 step3 同一把尺）
                pang_yuan_wang.append({
                    "position": y.get("position"),
                    "branch": y.get("earthly_branch", ""),
                    "six_relation": yuan_rel,
                    "score": score,
                })

    ying_ke_shi = None
    if world_el and resp_el:
        try:
            from yishu_core.relations import wuxing_relation
            rel = wuxing_relation(world_el, resp_el)
            if rel:
                ying_ke_shi = (rel == "克我")   # 以世为我，应克世
        except Exception:
            ying_ke_shi = None

    return {
        "旁爻原神旺相": pang_yuan_wang,
        "旁爻原神六亲": yuan_rel,
        "应爻克世": ying_ke_shi,
        "note": _fmt_look1(pang_yuan_wang, yuan_rel, ying_ke_shi),
    }


def _look2_shixia_qin_jing(result, yao_lines) -> dict:
    """《火珠林》源L27 二看逐字「二看世下亲爻财官喜静」→ 结构标签。

    判据：「世下亲爻」＝世爻**之下（次一位）**那一爻（自世上数下一位）；
    若其六亲为**妻财或官鬼**，则报它「静/动」这一结构事实。
    只标象：不据此取用神、不据此定吉凶、不打分（源L31-32 的问答说明
    「喜静」是「不欲乱动之爻去冲克之」，属解经，本层只报动静事实）。
    """
    step2 = _luandong_step2(result)
    if not step2:
        return None
    world_pos = step2.get("world_position")
    if not world_pos:
        return None
    target_pos = world_pos - 1        # 世下一位（初爻为 1）
    target = None
    for y in yao_lines:
        if isinstance(y, dict) and y.get("position") == target_pos:
            target = y
            break
    if target is None:
        return None
    rel = target.get("six_relation", "")
    if rel not in ("妻财", "官鬼"):
        return {"适用": False, "position": target_pos, "six_relation": rel,
                "note": f"《火珠林》源L27 逐字「二看世下亲爻财官喜静」——二看不适用：世下爻（{target_pos}爻）六亲为{rel or '—'}，非财官"}
    return {
        "适用": True,
        "position": target_pos,
        "branch": target.get("earthly_branch", ""),
        "six_relation": rel,
        "is_moving": bool(target.get("is_moving")),
        "note": (f"世下亲爻（{target_pos}爻·{rel}·{target.get('earthly_branch', '')}）"
                 f"{'动' if target.get('is_moving') else '静'}"),
    }


def _branch_element_of(branch: str) -> str:
    """支 → 五行（内核 BRANCH_ELEMENTS，唯一真值源）。"""
    if not branch:
        return ""
    try:
        from yishu_core.symbols import BRANCH_ELEMENTS
        return BRANCH_ELEMENTS.get(branch, "")
    except Exception:
        return ""


def _fmt_look1(pang_yuan_wang, yuan_rel, ying_ke_shi) -> str:
    """一看的展示句（素材口径见 verdict_texts.json「乱动」条 look1 提示）。"""
    if not yuan_rel:
        return "用神原神未定，本看不判"
    if pang_yuan_wang:
        info = "、".join(f"{p['position']}爻{p['branch']}({p['six_relation']},旺相{p['score']:.1f})"
                        for p in pang_yuan_wang)
        head = f"旁爻生助（{yuan_rel}）旺相者：{info}"
    else:
        head = f"旁爻无旺相之{yuan_rel}（生助用神之爻不现或休囚）"
    if ying_ke_shi is True:
        return head + "；应爻克世"
    if ying_ke_shi is False:
        return head + "；应爻不克世"
    return head + "；应世关系不可判"
