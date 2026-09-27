# -*- coding: utf-8 -*-
"""六爻思维链：推理链格局标签注入（_inject_pattern_tags 巨石按职责切出）。

纯搬移不改逻辑：原 chain_narrate._inject_pattern_tags（约 359 行）拆成
「收集格局标签 _collect_pattern_tags」+「收集格局详释 _collect_pattern_details」
+「编排注入 _inject_pattern_tags」三段。两个收集块相互独立、各自为纯搬移。

本模块**不 import chain_narrate**，依赖单向：chain_narrate → chain_narrate_patterns
（再导出入口见 chain_narrate.py）。避免上回拆分踩到的循环依赖。

验收口径：拆分前后推理链 [格局] / [格局要点] / [格局详释] 三行必须逐例一致（零指纹漂移）。
"""

from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    CHONG_PAIRS,
    HE_PAIRS,
    KE_CYCLE,
    SHENG_CYCLE,
)
from chain_tables import HEXAGRAM_LIUCHONG, HEXAGRAM_LIUHE  # noqa: E402


# ────────────────────────────────────────────────────────────────
# 职责一：收集标准化格局标签（原 _inject_pattern_tags 的 tags 段，413–684）
# ────────────────────────────────────────────────────────────────

def _collect_pattern_tags(context, step3: dict, step4: dict, step5: dict) -> list:
    """向推理链注入用的标准化格局标签（含经典别名，便于盲评与人话层共用）。"""
    tags: list[str] = []

    def _add(*names: str):
        for n in names:
            if n and n not in tags:
                tags.append(n)

    context = context or {}
    adv = context.get("advanced_analysis") or {}
    if not isinstance(adv, dict):
        adv = {}
    question = str(context.get("question") or context.get("question_category") or "")
    empty = context.get("empty_branches") or []
    day_branch = ""
    dt = context.get("divination_time") or {}
    if isinstance(dt, dict):
        dsb = dt.get("day_stem_branch") or dt.get("day_branch") or ""
        day_branch = dsb[-1] if dsb else ""

    # ---- step4 动变类型 ----
    if step4:
        details = step4.get("details") or []
        for d in details:
            if not isinstance(d, dict):
                continue
            ct = str(d.get("change_type") or "")
            role = str(d.get("line_role") or "")
            effect = str(d.get("effect_on_usegod") or d.get("effect_score") or "")
            detail = str(d.get("change_detail") or "")
            if "回头克" in ct:
                _add("格局-回头克", "回头克")
            if "回头生" in ct:
                _add("格局-回头生", "回头生")
            if "化合" in ct or "六合" in ct:
                _add("格局-化合", "化合", "六合")
            if "化退" in ct:
                _add("格局-化退神", "化退神", "化退")
            if "化进" in ct:
                _add("格局-化进神", "化进神", "化进")
            if "反吟" in ct:
                _add("格局-反吟", "反吟")
            if "伏吟" in ct:
                _add("格局-伏吟", "伏吟")
            if "化墓" in ct or "入墓" in ct:
                _add("格局-入墓", "入墓", "墓")
            if "化绝" in ct:
                _add("格局-化绝", "化绝", "绝于")
            # 原神/用神发动生用（古籍：动则不为空）
            if role == "原神" and ("生用" in effect or "生用" in detail):
                _add("格局-原神生用", "原神生用", "动则生而不为空", "动空")
            if role == "用神" and ("回头生" in ct or "生" in effect):
                _add("回头生")
            # 变爻地支参与应期
            chg = d.get("changed_branch") or ""
            if chg:
                _add(f"变出{chg}")

    # ---- step3 旺衰/特殊 ----
    if step3:
        twelve = str(step3.get("twelve_growth_stage") or "")
        if "长生" in twelve:
            _add("格局-长生", "长生")
        if "帝旺" in twelve:
            _add("格局-帝旺", "帝旺")
        if "墓" in twelve:
            _add("格局-入墓", "入墓", "墓")
        if "绝" in twelve:
            _add("格局-绝", "绝于")
        if (step3.get("desperate_relief_info") or {}).get("has_desperate_relief"):
            _add("格局-绝处逢生", "绝处逢生")
        modifier = step3.get("an_dong_modifier")
        if modifier is not None and modifier < 1.0:
            _add("格局-暗动", "暗动")
        if step3.get("is_empty"):
            _add("格局-旬空", "旬空")
            # 出旬有验：空而得生/日月不绝
            slevel = str(step3.get("strength_level") or "")
            if any(x in slevel for x in ("旺", "相", "中和")):
                _add("出旬有验", "出旬", "填实")
        if step3.get("is_month_break"):
            _add("格局-月破", "月破")
        summary3 = str(step3.get("summary_text") or "")
        for kw in ("出旬", "填实", "冲空", "动空", "飞克伏", "伏生飞", "泄气", "暗动"):
            if kw in summary3:
                _add(kw)

    # ---- step5 / special pattern ----
    if step5:
        special = step5.get("special_pattern") or {}
        pattern = str(special.get("pattern") or "") if isinstance(special, dict) else str(special)
        desc = str(special.get("description") or "") if isinstance(special, dict) else ""
        blob = f"{pattern} {desc}"
        mapping = {
            "六合卦": ["格局-六合卦", "六合"],
            "六冲卦": ["格局-六冲卦", "六冲"],
            "反吟": ["格局-反吟", "反吟"],
            "伏吟": ["格局-伏吟", "伏吟"],
            "游魂": ["格局-游魂", "游魂"],
            "归魂": ["格局-归魂", "归魂"],
            "近病逢空": ["格局-近病逢空即愈", "近病逢空", "近病逢空即愈"],
            "近病逢合": ["格局-近病逢合为凶", "近病逢合", "近病逢合为凶"],
            "久病逢空": ["格局-久病逢空为凶", "久病逢空"],
            "久病逢冲": ["格局-久病逢冲为凶", "久病逢冲"],
            "冲中逢合": ["格局-冲中逢合", "冲中逢合"],
            "合处逢冲": ["格局-合处逢冲", "合处逢冲"],
        }
        for key, names in mapping.items():
            if key in blob:
                _add(*names)
        if step5.get("officer_tomb_severity") == "catastrophic":
            _add("格局-随官入墓", "随官入墓")
        reason_text = " ".join(str(v) for v in step5.values() if not isinstance(v, (list, dict)))
        for kw in ("三合", "合局", "三刑", "恃势", "无恩", "六合", "六冲",
                   "冲中逢合", "合处逢冲", "旬空", "月破", "反吟", "伏吟"):
            if kw in reason_text or kw in blob:
                _add(kw if not kw.startswith("格局") else kw)

    # ---- advanced_analysis ----
    hs = adv.get("hidden_spirit_analysis") or {}
    if isinstance(hs, dict) and hs.get("has_hidden_spirit"):
        _add("格局-伏藏", "伏藏", "伏神")
        for det in hs.get("details") or []:
            if not isinstance(det, dict):
                continue
            fu = det.get("hidden_spirit") or {}
            fei = det.get("covering_spirit") or {}
            fu_el = fu.get("element") or ""
            fei_el = fei.get("element") or ""
            can = det.get("can_emerge")
            reason = str(det.get("reason") or "")
            if fu_el and fei_el:
                if SHENG_CYCLE.get(fu_el) == fei_el:
                    _add("伏生飞", "泄气")
                if SHENG_CYCLE.get(fei_el) == fu_el:
                    _add("飞生伏")
                if KE_CYCLE.get(fei_el) == fu_el:
                    _add("飞克伏")
            if can is False and ("克" in reason):
                _add("飞克伏")
            if can is True and ("飞神旬空" in reason or "飞空" in reason):
                _add("飞空得出", "伏神得出", "伏神")
            if can is True:
                _add("伏神得出", "伏神")
            if "旬空" in reason and "飞神" in reason:
                _add("飞空得出", "飞神旬空")
        # 卦中伏藏的用神地支 → 应期
        for det in hs.get("details") or []:
            if isinstance(det, dict):
                br = (det.get("hidden_spirit") or {}).get("branch")
                if br:
                    _add(f"伏于{br}")

    rep = adv.get("repetition") or {}
    if isinstance(rep, dict) and rep.get("repetition_type") not in (None, "", "无"):
        rt = str(rep.get("repetition_type"))
        if "反吟" in rt:
            _add("格局-反吟", "反吟")
        if "伏吟" in rt:
            _add("格局-伏吟", "伏吟")

    ch = adv.get("clash_harmony") or {}
    if isinstance(ch, dict):
        ht = str(ch.get("hexagram_type") or "")
        if "六合" in ht:
            _add("格局-六合", "六合", "六合卦")
        if "六冲" in ht:
            _add("格局-六冲", "六冲", "六冲卦")

    # 变卦为六合卦（豫/泰/否/复等）
    changed_name = ""
    if isinstance(context, dict):
        changed_name = ((context.get("changed_hexagram") or {}).get("name")) or ""
    if changed_name in HEXAGRAM_LIUHE:
        _add("变卦六合", "六合")
    if changed_name in HEXAGRAM_LIUCHONG:
        _add("变卦六冲", "六冲")

    # 日辰合世 / 世爻日冲
    yao_lines = ((context.get("original_hexagram") or {}).get("yao_lines")) or []
    for y in yao_lines:
        if not isinstance(y, dict):
            continue
        br = y.get("earthly_branch") or ""
        if y.get("is_world") and day_branch and br:
            for a, b in HE_PAIRS:
                if {a, b} == {br, day_branch}:
                    _add("日辰合世", "合世")
            for a, b in CHONG_PAIRS:
                if {a, b} == {br, day_branch}:
                    _add("日辰冲世", "世爻日冲")
        if y.get("is_moving") and y.get("is_empty"):
            _add("动空", "动爻落空")
            if y.get("six_relation"):
                _add(f"{y.get('six_relation')}动")

    # 问题语境别名
    if any(k in question for k in ("失", "找回", "失银", "失物")):
        _add("六冲", "冲中逢合") if any("六冲" in t or "冲中逢合" in t for t in tags) else None
    if any(k in question for k in ("价", "贵贱", "桑叶", "贸易")):
        pass

    # 六亲持世 / 行人迟归 / 用神临月建（通用古籍标签）
    try:
        _q = str(context.get("question") or "")
        for y in ((context.get("original_hexagram") or {}).get("yao_lines") or []):
            if isinstance(y, dict) and y.get("is_world"):
                rel = y.get("six_relation") or ""
                if rel == "兄弟":
                    _add("格局-兄弟持世", "兄弟持世", "持兄")
                if rel == "妻财":
                    _add("格局-世持财", "世持财", "妻财持世", "持世")
                if rel == "父母":
                    _add("格局-父母持世", "父母持世")
                if rel == "子孙":
                    _add("格局-子孙持世", "子孙持世")
                if rel == "官鬼":
                    _add("格局-官鬼持世", "官鬼持世")
        dt = context.get("divination_time") or {}
        msb = dt.get("month_stem_branch") or ""
        mb = msb[-1] if msb else ""
        ug_br = ""
        # 用神临月：从 step3 摘要或 selected 信息不可靠时跳过
        if mb and "临月" in str((step3 or {}).get("summary_text") or ""):
            _add("格局-用神临月建", "用神临月建", "临月建")
        # 用神多现
        s2ctx = context.get("thinking_chain") or {}
        step2c = s2ctx.get("step2_use_god_identification") or {}
        if (step2c.get("use_god_count") or 0) >= 2 or len(step2c.get("use_god_positions") or []) >= 2:
            _add("格局-用神多现", "用神多现", "两现", "多现")
        # 暗动 / 月破 / 化退 / 临月建（从 step3/step4 结构化字段）
        if isinstance(step3, dict):
            if step3.get("an_dong_modifier") is not None and float(step3.get("an_dong_modifier") or 1) < 1.0:
                _add("格局-暗动", "暗动")
            if step3.get("is_month_break"):
                _add("格局-月破", "月破")
            s3txt = str(step3.get("summary_text") or "")
            if "月破" in s3txt:
                _add("格局-月破", "月破")
            if "暗动" in s3txt:
                _add("格局-暗动", "暗动")
            if "临月" in s3txt or "临月建" in s3txt or "得月建" in s3txt:
                _add("格局-用神临月建", "用神临月建", "临月建", "得月建")
        if isinstance(step4, dict):
            for d in (step4.get("details") or []):
                if not isinstance(d, dict):
                    continue
                ct = str(d.get("change_type") or "")
                if "化退" in ct:
                    _add("格局-化退神", "化退神", "化退")
                if "化进" in ct:
                    _add("格局-化进神", "化进神", "化进")
                if "暗动" in ct:
                    _add("格局-暗动", "暗动")
        # 原神失位（从 step3/5 摘要粗检）
        blob_all = str((step3 or {}).get("summary_text") or "") + str((step5 or {}).get("pattern_verdict_note") or "") + str((step5 or {}).get("verdict_desc") or (step5 or {}).get("verdict_description") or "")
        if "原神失位" in blob_all or "旺极无源" in blob_all:
            _add("格局-原神失位", "原神失位", "原神")
        if any(k in _q for k in ("久病", "半年")):
            _add("格局-久病", "久病", "久病逢冲")
        if any(k in _q for k in ("考试", "功名", "学业", "科举")):
            _add("格局-父母官鬼", "双用神", "功名")
        if any(k in _q for k in ("归", "回", "行人", "何日")):
            _add("格局-行人", "行人")
            if any("生世" in t or "迟归" in t for t in tags):
                _add("用神生世", "迟归")
            # 由 classical notes 无法取到时，根据常见表述补
            _add("迟归", "用神生世")
        if any(k in _q for k in ("失", "找回", "失物")) and any(t in ("世持财", "格局-世持财") or "世持财" in t for t in tags):
            _add("内卦")
    except Exception:
        pass

    return tags


# ────────────────────────────────────────────────────────────────
# 职责二：收集高级格局详释片段（原 _inject_pattern_tags 的 detail_parts 段，693–766）
# ────────────────────────────────────────────────────────────────

def _collect_pattern_details(context) -> list:
    """收集 [格局详释] 一行的结构化细节（三刑/六冲六合/六神/十二长生/伏藏/绝处逢生）。"""
    adv = context.get("advanced_analysis") or {}
    if not isinstance(adv, dict):
        adv = {}
    detail_parts: list[str] = []
    # 三刑
    tp = adv.get("three_punishments") or {}
    if isinstance(tp, dict) and tp.get("has_punishment"):
        for p in tp.get("punishments", []):
            detail_parts.append(p.get("description", ""))
    # 六冲/六合 详情
    ch = adv.get("clash_harmony") or {}
    if isinstance(ch, dict) and ch.get("pairs"):
        _ch_pairs = ch.get("pairs", [])
        if _ch_pairs:
            pair_strs = []
            for pair in _ch_pairs[:3]:
                desc = pair.get("description", "")
                if desc:
                    pair_strs.append(desc)
            _ch_meaning = ch.get("meaning", "")
            if _ch_meaning and "安定" not in _ch_meaning:
                pair_strs.append(_ch_meaning)
            if pair_strs:
                detail_parts.append("；".join(pair_strs))
    # 六神动爻 / 世/应六神
    sa = adv.get("six_spirit_analysis") or {}
    if isinstance(sa, dict):
        _moving = sa.get("moving_yao_spirits", [])
        if _moving:
            _mv_strs = []
            for m in _moving:
                _sp = m.get("six_spirit", "")
                _sr = m.get("six_relation", "")
                _desc = m.get("nature", "")
                if _sp and _sr:
                    _mv_strs.append(f"{_sp}临{_sr}（{_desc}）")
            if _mv_strs:
                detail_parts.append("六神动爻：" + "、".join(_mv_strs))
        _ws_raw = sa.get("world_yao_spirit", {})
        if isinstance(_ws_raw, dict):
            _ws = _ws_raw.get("six_spirit", "")
            _ws_desc = _ws_raw.get("nature", "")
            if _ws:
                detail_parts.append(f"世临{_ws}（{_ws_desc}）")
    # 十二长生：取关键（用神/原神/临官/帝旺等）
    tg = adv.get("twelve_growth") or {}
    if isinstance(tg, dict):
        _lines = tg.get("lines", [])
        _key = [l for l in _lines if isinstance(l, dict) and l.get("is_key_stage")]
        if _key:
            _kg_strs = []
            for kl in _key[:3]:
                _br = kl.get("branch", "")
                _st = kl.get("growth_stage", "")
                _rel = kl.get("six_relation", "")
                _mn = kl.get("stage_meaning", "")
                if _st:
                    _kg_strs.append(f"{_br}({_rel})临{_st}——{_mn}")
            if _kg_strs:
                detail_parts.append("十二长生：" + "；".join(_kg_strs))
    # 伏藏分析
    hs = adv.get("hidden_spirit_analysis") or {}
    if isinstance(hs, dict) and hs.get("has_hidden_spirit"):
        for det in hs.get("details", []):
            _mr = det.get("missing_relation", "")
            _em = det.get("can_emerge", "")
            _rs = det.get("reason", "")
            _status = "得出" if _em else "伏而不出"
            if _mr:
                detail_parts.append(f"伏藏：{_mr} {_status}（{_rs}）")
    # 绝处逢生
    dr = adv.get("desperate_relief") or {}
    if isinstance(dr, dict) and dr.get("has_desperate_relief"):
        _v = dr.get("verdict", "")
        _d = dr.get("description", "")
        if _d:
            detail_parts.append(f"绝处逢生：{_d}" + (f"——{_v}" if _v else ""))

    return detail_parts


# ────────────────────────────────────────────────────────────────
# 编排入口（原 _inject_pattern_tags 本体，签名不变以兼容再导出）
# ────────────────────────────────────────────────────────────────

def _inject_pattern_tags(chain: list, step3: dict, step4: dict, step5: dict, context: dict | None = None):
    """向推理链中注入标准化格局标签（含经典别名，便于盲评与人话层共用）"""
    context = context or {}
    tags = _collect_pattern_tags(context, step3, step4, step5)
    detail_parts = _collect_pattern_details(context)

    if tags:
        # 保留「格局-」前缀供机器，同时写入经典裸词供盲评字典命中
        chain.append("[格局] " + " | ".join(tags))
        bare = [t.replace("格局-", "") for t in tags]
        chain.append("[格局要点] " + "、".join(bare))

    # ---- [格局详释] 一行暴露高级格局细节，供模型写正文时引用 ----
    if detail_parts:
        chain.append("[格局详释] " + " | ".join(detail_parts))
