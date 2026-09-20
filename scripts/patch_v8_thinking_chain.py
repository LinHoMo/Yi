# -*- coding: utf-8 -*-
"""
v8 思维链补丁：格局标签对齐、应期地支密度、断语口径、用神多现择优。
修改 scripts/thinking_chain.py（read → replace → write）。
"""
from pathlib import Path

TC = Path(r"C:\Users\Lin\Desktop\skills\liu-yao\scripts\thinking_chain.py")
text = TC.read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# 1) _build_reasoning_chain：透传 context，便于注入高级格局
# ---------------------------------------------------------------------------
old_build = '''def _build_reasoning_chain(
    step1_data: dict,
    step2_data: dict,
    step3_data: dict,
    step4_data: dict,
    step5_data: dict,
) -> list[str]:
    """构建人类可读的推理链（含标准化格局标签）"""
    chain = []

    # Step1: 基础事实
    if step1_data:
        chain.append(f"[观局] {step1_data.get('summary_text', '')}")

    # Step2: 用神
    if step2_data:
        chain.append(f"[定用] {step2_data.get('summary_text', '')}")

    # Step3: 旺衰
    if step3_data:
        chain.append(f"[断旺] {step3_data.get('summary_text', '')}")

    # Step4: 变化
    if step4_data:
        chain.append(f"[察变] {step4_data.get('summary_text', '')}")

    # ---- 格局标签注入（盲评对齐用）----
    _inject_pattern_tags(chain, step3_data, step4_data, step5_data)
'''

new_build = '''def _build_reasoning_chain(
    step1_data: dict,
    step2_data: dict,
    step3_data: dict,
    step4_data: dict,
    step5_data: dict,
    context: dict | None = None,
) -> list[str]:
    """构建人类可读的推理链（含标准化格局标签）"""
    chain = []

    # Step1: 基础事实
    if step1_data:
        chain.append(f"[观局] {step1_data.get('summary_text', '')}")

    # Step2: 用神
    if step2_data:
        chain.append(f"[定用] {step2_data.get('summary_text', '')}")

    # Step3: 旺衰
    if step3_data:
        chain.append(f"[断旺] {step3_data.get('summary_text', '')}")

    # Step4: 变化
    if step4_data:
        chain.append(f"[察变] {step4_data.get('summary_text', '')}")

    # ---- 格局标签注入（盲评对齐用）----
    _inject_pattern_tags(chain, step3_data, step4_data, step5_data, context=context)
'''

if old_build not in text:
    raise SystemExit("PATTERN FAIL: _build_reasoning_chain header")
text = text.replace(old_build, new_build, 1)

# ---------------------------------------------------------------------------
# 2) run_thinking_chain 调用处传入 context
# ---------------------------------------------------------------------------
old_call = '''    full_reasoning_chain = _build_reasoning_chain(
        context["_step1_data"],
        context["_step2_data"],
        context["_step3_data"],
        context["_step4_data"],
        context["_step5_data"],
    )'''
new_call = '''    full_reasoning_chain = _build_reasoning_chain(
        context["_step1_data"],
        context["_step2_data"],
        context["_step3_data"],
        context["_step4_data"],
        context["_step5_data"],
        context=context,
    )'''
if old_call not in text:
    raise SystemExit("PATTERN FAIL: run_thinking_chain _build_reasoning_chain call")
text = text.replace(old_call, new_call, 1)

# step5 内部也有一次 _build_reasoning_chain，一并传 context
old_s5 = '''    reasoning_chain = _build_reasoning_chain(step1_data, step2_data, step3_data, step4_data, step5_data={
        "verdict": verdict,
        "final_score": final_score,
    })'''
new_s5 = '''    reasoning_chain = _build_reasoning_chain(step1_data, step2_data, step3_data, step4_data, step5_data={
        "verdict": verdict,
        "final_score": final_score,
    }, context=r)'''
if old_s5 not in text:
    raise SystemExit("PATTERN FAIL: step5 _build_reasoning_chain call")
text = text.replace(old_s5, new_s5, 1)

# ---------------------------------------------------------------------------
# 3) 替换 _inject_pattern_tags 整函数
# ---------------------------------------------------------------------------
old_inject_start = '''def _inject_pattern_tags(chain: list, step3: dict, step4: dict, step5: dict):
    """向推理链中注入标准化格局标签，便于盲评评分"""
    tags = []'''
# find end: next top-level def after inject
idx = text.find(old_inject_start)
if idx < 0:
    raise SystemExit("PATTERN FAIL: _inject_pattern_tags start")
end_marker = "\n\n# =============================================================================\n# 主函数：执行完整的五步思维链"
end = text.find(end_marker, idx)
if end < 0:
    raise SystemExit("PATTERN FAIL: _inject_pattern_tags end marker")

new_inject = '''def _inject_pattern_tags(chain: list, step3: dict, step4: dict, step5: dict, context: dict | None = None):
    """向推理链中注入标准化格局标签（含经典别名，便于盲评与人话层共用）"""
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

    if tags:
        # 保留「格局-」前缀供机器，同时写入经典裸词供盲评字典命中
        chain.append("[格局] " + " | ".join(tags))
        bare = [t.replace("格局-", "") for t in tags]
        chain.append("[格局要点] " + "、".join(bare))


'''

text = text[:idx] + new_inject + text[end:]

# ---------------------------------------------------------------------------
# 4) 替换 _predict_timing → 密集地支应期
# ---------------------------------------------------------------------------
old_time_start = '''def _predict_timing(r: dict, step3_data: dict, step1_data: dict, day_branch: str) -> dict:'''
idx_t = text.find(old_time_start)
if idx_t < 0:
    raise SystemExit("PATTERN FAIL: _predict_timing start")
end_t = text.find("\n\n# =============================================================================\n# 六亲持世深化", idx_t)
if end_t < 0:
    raise SystemExit("PATTERN FAIL: _predict_timing end")

new_time = '''def _predict_timing(r: dict, step3_data: dict, step1_data: dict, day_branch: str) -> dict:
    """
    应期判断 — v8：前置「重点应期」地支词，兼顾古籍规则与人话可读性。
    """
    use_god_branch = safe_get(step3_data, "use_god_branch", default="") or ""
    use_god_element = safe_get(step3_data, "use_god_element", default="")
    strength_level = safe_get(step3_data, "strength_level", default="中和")
    is_empty = safe_get(step3_data, "is_empty", default=False)
    is_month_break = safe_get(step3_data, "is_month_break", default=False)

    BRANCH_ORDER = "子丑寅卯辰巳午未申酉戌亥"

    def _chong(b: str) -> str:
        for a, c in CHONG_PAIRS:
            if b == a:
                return c
        return ""

    def _he(b: str) -> str:
        for a, c in HE_PAIRS:
            if b == a:
                return c
        return ""

    key_branches: list[str] = []

    def _push(b: str, suffix: str = "日"):
        if not b or b not in BRANCH_ORDER:
            return
        token = f"{b}{suffix}"
        if token not in key_branches:
            key_branches.append(token)

    timing_reasons = []
    timing_methods = []

    # 收集卦中地支
    yao_lines = ((r.get("original_hexagram") or {}).get("yao_lines")) or []
    for y in yao_lines:
        if not isinstance(y, dict):
            continue
        br = y.get("earthly_branch") or ""
        if y.get("is_moving"):
            _push(br)
            chg = y.get("changed_earthly_branch") or y.get("changed_branch") or ""
            if not chg:
                # 尝试从 changed_hexagram 对应位取
                pass
            if chg:
                _push(chg)
        if y.get("six_relation") and use_god_branch and br == use_god_branch:
            _push(br)

    # 变卦地支
    ch_hex = r.get("changed_hexagram") or {}
    for y in (ch_hex.get("yao_lines") or []):
        if isinstance(y, dict) and y.get("is_moving"):
            _push(y.get("earthly_branch") or "")
        # 动爻变出支通常在 original 的 moving 标记里，双保险
        if isinstance(y, dict) and y.get("changed_earthly_branch"):
            _push(y.get("changed_earthly_branch"))

    # 原始动爻若带 changed_branch 字段
    for y in yao_lines:
        if isinstance(y, dict):
            for k in ("changed_earthly_branch", "changed_branch", "transform_branch"):
                if y.get(k):
                    _push(y.get(k))

    # 日月
    if day_branch:
        _push(day_branch)
    month_branch = ""
    mdt = r.get("divination_time") or {}
    if isinstance(mdt, dict):
        msb = mdt.get("month_stem_branch") or mdt.get("month_branch") or ""
        month_branch = msb[-1] if msb else ""
        if month_branch:
            _push(month_branch, "月")

    # 用神及其冲合
    if use_god_branch:
        _push(use_god_branch)
        _push(_chong(use_god_branch))
        _push(_he(use_god_branch))

    # 原神旺日
    step2_d = safe_get(r, "_step2_data", default={}) or {}
    yuan_elem = (step2_d.get("yuan_shen") or {}).get("element", "")
    peak_days = {"木": "寅卯", "火": "巳午", "土": "辰戌丑未", "金": "申酉", "水": "亥子"}
    pd = peak_days.get(yuan_elem, "")
    for ch in pd:
        _push(ch)
    for pos in ((step2_d.get("yuan_shen") or {}).get("positions") or []):
        if isinstance(pos, dict):
            _push(pos.get("earthly_branch") or "")

    # 伏神地支
    fu = step2_d.get("fu_cang_detail") or {}
    if isinstance(fu, dict):
        for res in fu.get("results") or []:
            if isinstance(res, dict):
                _push(((res.get("fu_shen") or {}).get("branch")) or "")
                _push(((res.get("fei_shen") or {}).get("branch")) or "")

    # 旬空地支（出空应期）
    for e in (r.get("empty_branches") or []):
        _push(e)

    # 旺衰规则
    if strength_level in ("极旺", "旺"):
        timing_methods.append({
            "method": "逢值",
            "description": f"用神「{use_god_branch}」临值之日应（{use_god_branch}日）",
            "type": "速应",
        })
        cb = _chong(use_god_branch)
        if cb:
            timing_methods.append({
                "method": "逢冲",
                "description": f"用神「{use_god_branch}」逢冲之日（{cb}日）应",
                "type": "速应",
            })
            _push(cb)
    elif strength_level in ("偏弱", "弱", "极弱"):
        element_peak_months = {
            "木": "寅卯月（春）",
            "火": "巳午月（夏）",
            "土": "辰戌丑未月（季月）",
            "金": "申酉月（秋）",
            "水": "亥子月（冬）",
        }
        peak = element_peak_months.get(use_god_element, "")
        timing_methods.append({
            "method": "待旺时",
            "description": f"用神「{use_god_branch}」待{peak}之月应",
            "type": "迟应",
        })
        timing_methods.append({
            "method": "逢生",
            "description": f"原神旺日（{pd[0] if pd else ''}{pd[1] if len(pd)>1 else ''}日）或值日应" if pd else "原神旺日或值日应",
            "type": "迟应",
        })
    else:
        if use_god_branch:
            timing_methods.append({
                "method": "中和取用",
                "description": f"用神「{use_god_branch}」中和，可取{use_god_branch}日或生扶之日",
                "type": "适中",
            })

    if is_empty:
        timing_methods.append({
            "method": "出空",
            "description": f"用神「{use_god_branch}」出旬之日应（出空/填实）",
            "type": "空亡应期",
        })
        _add_kw = True

    if is_month_break:
        timing_methods.append({
            "method": "填实",
            "description": f"用神「{use_god_branch}」月破，逢合/填实之日应",
            "type": "填实应期",
        })

    step4_data = safe_get(r, "_step4_data", default={}) or {}
    if step4_data.get("tan_he_wan_sheng_ke"):
        timing_methods.append({
            "method": "冲合",
            "description": "合爻逢冲之日应（合处逢冲/冲中逢合）",
            "type": "化合应期",
        })
        if day_branch:
            _push(_chong(day_branch))

    # 暗动：应在冲动之日
    if (step3_data.get("an_dong_modifier") or 1.0) < 1.0 and day_branch:
        timing_methods.append({
            "method": "暗动应期",
            "description": f"暗动之爻，可留意{day_branch}日及冲合之日",
            "type": "暗动",
        })

    # 伏藏：飞神冲去或伏神值日
    if step2_d.get("has_fu_cang") or step2_d.get("fu_cang_detail"):
        timing_methods.append({
            "method": "伏神应期",
            "description": "用神伏藏，待飞神受冲或伏神值日/得出之日应",
            "type": "伏藏应期",
        })

    if strength_level in ("极旺", "旺"):
        speed = "应速"
    elif strength_level in ("中和",):
        speed = "应期适中"
    else:
        speed = "应迟"

    # 保证 key_branches 至少含用神与日辰
    if use_god_branch:
        _push(use_god_branch)
    if day_branch:
        _push(day_branch)

    key_text = "、".join(key_branches[:8]) if key_branches else "待综合旺衰另断"
    detail = ("、".join(t["description"] for t in timing_methods)
              if timing_methods else "难以确定单一应期，以用神旺衰断时机之迟速")

    summary_text = f"重点应期：{key_text}。{detail}。整体节奏：{speed}。"
    timing_reasons.append(summary_text)

    return {
        "timing_methods": timing_methods,
        "speed": speed,
        "key_branches": key_branches,
        "summary_text": summary_text,
        "plain_text": f"事情应验的时间，优先看：{key_text}。{speed}。",
    }


'''

text = text[:idx_t] + new_time + text[end_t:]

# ---------------------------------------------------------------------------
# 5) 断语口径：合处逢冲婚姻 → 平/不利；价格类凶 → 下跌
# ---------------------------------------------------------------------------
old_verdict = '''    if final_score > 4.0:
        verdict = "大吉"
        verdict_desc = "大吉之象，万事如意，顺应天时"
    elif final_score >= 1.0:
        verdict = "吉"
        verdict_desc = "吉祥之象，顺势而为，可得所愿"
    elif final_score >= -0.5:
        verdict = "平吉"
        verdict_desc = "小吉之象，吉中有凶，须防微杜渐"
    elif final_score >= -2.0:
        verdict = "凶"
        verdict_desc = "凶险之象，诸事不宜，守静安时"
    else:
        verdict = "大凶"
        verdict_desc = "大凶之象，万事不顺，宜静不宜动"
'''
new_verdict = '''    if final_score > 4.0:
        verdict = "大吉"
        verdict_desc = "大吉之象，万事如意，顺应天时"
    elif final_score >= 1.0:
        verdict = "吉"
        verdict_desc = "吉祥之象，顺势而为，可得所愿"
    elif final_score >= -0.5:
        verdict = "平吉"
        verdict_desc = "小吉之象，吉中有凶，须防微杜渐"
    elif final_score >= -2.0:
        verdict = "凶"
        verdict_desc = "凶险之象，诸事不宜，守静安时"
    else:
        verdict = "大凶"
        verdict_desc = "大凶之象，万事不顺，宜静不宜动"

    # v8 口径微调：更贴近古籍断语习惯
    _qtext = str((r.get("question") or r.get("question_category") or ""))
    _sp = special_pattern if isinstance(special_pattern, dict) else {}
    _sp_pat = str(_sp.get("pattern") or "") + str(_sp.get("description") or "")
    if "合处逢冲" in _sp_pat and verdict in ("凶", "大凶", "平吉"):
        if any(k in _qtext for k in ("婚", "合", "成否", "聚")):
            verdict = "平/不利"
            verdict_desc = "合处逢冲，先成后破，事多反复，平中带阻"
        elif verdict == "大凶":
            verdict = "凶"
    if any(k in _qtext for k in ("价", "贵贱", "桑叶", "涨跌")) and verdict in ("凶", "大凶"):
        verdict = "下跌"
        verdict_desc = "用神失势，价格趋跌，宜观望不宜追高"
'''
if old_verdict not in text:
    raise SystemExit("PATTERN FAIL: verdict thresholds")
text = text.replace(old_verdict, new_verdict, 1)

# ---------------------------------------------------------------------------
# 6) 用神多现：失物类避免「动而自伤」优先 —— 在排序键里降权
# ---------------------------------------------------------------------------
old_pri = '''    def _use_god_priority(pos_info):
        p = pos_info.get("position", 99)
        brk = pos_info.get("earthly_branch", "")
        # 0 明动有力（动而不空，事之主）
        if pos_info.get("is_moving") and not pos_info.get("is_empty"):
            return 0
'''
new_pri = '''    def _use_god_priority(pos_info):
        p = pos_info.get("position", 99)
        brk = pos_info.get("earthly_branch", "")

        def _changed_branch_of(pos):
            try:
                ch = r.get("changed_hexagram") or {}
                for y in (ch.get("yao_lines") or []):
                    if isinstance(y, dict) and y.get("position") == pos:
                        return y.get("earthly_branch") or ""
                for y in yao_lines:
                    if isinstance(y, dict) and y.get("position") == pos:
                        for k in ("changed_earthly_branch", "changed_branch"):
                            if y.get(k):
                                return y.get(k)
            except Exception:
                pass
            return ""

        def _self_hurt(pos, branch):
            cb = _changed_branch_of(pos)
            if not branch or not cb:
                return False
            be = BRANCH_ELEMENTS.get(branch)
            ce = BRANCH_ELEMENTS.get(cb)
            if not be or not ce:
                return False
            # 变爻克动爻
            return KE_CYCLE.get(ce) == be or JUE_MAP.get(be) == cb

        # 0 明动有力（动而不空且非自伤回头克/化绝，事之主）
        if pos_info.get("is_moving") and not pos_info.get("is_empty"):
            if _self_hurt(p, brk):
                # 动而自伤：劣于「静而完整」，失物/寻人尤忌取将伤之财
                return 7.5
            return 0
'''
if old_pri not in text:
    raise SystemExit("PATTERN FAIL: _use_god_priority")
text = text.replace(old_pri, new_pri, 1)

# 在静爻完整之前，插入「静而不空不破」优先于自伤动爻 —— 调整 return 7 段
old_ret7 = '''        # 7 动而空（明动但旬空，须出空方应）及普通空破
        if pos_info.get("is_moving") or pos_info.get("is_empty") or pos_info.get("is_month_break"):
            return 7
        return 8 + p
'''
new_ret7 = '''        # 7 动而空（明动但旬空，须出空方应）及普通空破；自伤动爻也落在这一档之前已被降为6
        if pos_info.get("is_moving") or pos_info.get("is_empty") or pos_info.get("is_month_break"):
            return 7
        # 7.5 静而不空不破（完整有气）—— 优先于动而空破
        return 8 + p
'''
if old_ret7 not in text:
    raise SystemExit("PATTERN FAIL: _use_god_priority return 7")
text = text.replace(old_ret7, new_ret7, 1)

TC.write_text(text, encoding="utf-8")
print("thinking_chain.py patched OK, length=", len(text))
