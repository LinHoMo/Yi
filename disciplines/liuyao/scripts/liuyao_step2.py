from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ks_ensure

_ks_ensure(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    BRANCH_ELEMENTS,
    HEXAGRAM_TRIGRAMS,
    KE_CYCLE,
    NAJIA_BRANCHES,
)


import json


from pathlib import Path

from chain_tables import (
    _CHART_TAIL,
    _HEX_NAMES,
    _QUESTION_USE_GOD_BASIS,
    _QUESTION_USE_GOD_MAP,
    _USE_GOD_LAYER_CITATIONS,
    JUE_MAP,
    USE_GOD_RELATIONSHIPS,
)




from narrative_utils import (  # noqa: E402
    _branch_element,
    _is_chong,
    _pos_to_name,
    get_changed_hexagram_branch,
    get_elements_for_relation,
    get_palace_first_hexagram,
    get_relation_from_element,
    safe_get,
)

# ─── 全局变量 ───
_USE_GOD_RULES: list[dict] | None = None

# ═══ chain_step2.py ═══


def step2_identify_use_god(r: dict) -> dict:
    """
    Step 2: 定用神 — 根据问题类型确定用神（规则驱动，非模式匹配）。

    规则来源：《增删卜易》《卜筮正宗》《黄金策》

    关键规则：
    1. 用神两现：舍静取动、舍空破取旺相、取临月建者
    2. 用神不现：查伏藏（从本宫首卦）
    3. 用神多现：取世爻所在、取动爻、取临月建
    """
    # 获取分析上下文
    hex_info = safe_get(r, "original_hexagram", default={})
    yao_lines = safe_get(hex_info, "yao_lines", default=[])
    palace = safe_get(hex_info, "palace", default="")
    palace_element = safe_get(hex_info, "palace_element", default="")

    # 获取问题类型（兼容多种字段名）
    question_category = safe_get(r, "question_category", default="") or safe_get(r, "question", default="")
    question_text = safe_get(r, "question_text", default="") or safe_get(r, "question", default="")

    # 获取日月建信息
    div_time = safe_get(r, "divination_time", default={})
    month_stem_branch = safe_get(div_time, "month_stem_branch", default="")
    day_stem_branch = safe_get(div_time, "day_stem_branch", default="")
    month_branch = month_stem_branch[1:] if len(month_stem_branch) >= 2 else ""
    day_branch = day_stem_branch[1:] if len(day_stem_branch) >= 2 else ""
    month_element = _branch_element(month_branch)

    # 获取旬空
    empty = safe_get(r, "empty_branches", default=[])

    # ---------- 2.1: 确定用神类别 ----------
    use_god_category = _determine_use_god_category(question_category, question_text)
    use_god_basis = _use_god_basis(question_category, question_text, use_god_category)

    # ---------- 2.2: 定位用神在卦中的位置 ----------
    use_god_positions = _find_use_god_positions(
        yao_lines, use_god_category, palace_element, month_branch, empty
    )

    # ---------- 2.3: 确定原神、忌神、仇神 ----------
    # 用神五行（根据用神类别 + 宫五行推导；世爻取实际地支五行）
    use_god_elements = get_elements_for_relation(use_god_category, palace_element)
    if use_god_category == "世爻" and use_god_positions:
        # 世爻五行从实际地支反推
        world_branch = use_god_positions[0].get("earthly_branch", "")
        use_god_element = BRANCH_ELEMENTS.get(world_branch, palace_element)
    else:
        use_god_element = use_god_elements[0] if use_god_elements else "未知"

    relationships = USE_GOD_RELATIONSHIPS.get(use_god_element, {})
    yuan_shen_element = relationships.get("原神", "")
    ji_shen_element = relationships.get("忌神", "")
    chou_shen_element = relationships.get("仇神", "")

    # 找到原神/忌神/仇神所在爻位
    yuan_shen_positions = _find_relation_positions(yao_lines, yuan_shen_element, palace_element)
    ji_shen_positions = _find_relation_positions(yao_lines, ji_shen_element, palace_element)
    chou_shen_positions = _find_relation_positions(yao_lines, chou_shen_element, palace_element)

    # ---------- 2.3b: 伏藏查找（原神/忌神/仇神不在本卦时） ----------
    yuan_shen_fu = None
    ji_shen_fu = None
    chou_shen_fu = None

    if not yuan_shen_positions and yuan_shen_element:
        # 从本宫首卦查找伏藏
        first_hex_name = get_palace_first_hexagram(palace)
        if first_hex_name:
            trigrams_fu = HEXAGRAM_TRIGRAMS.get(first_hex_name)
            if trigrams_fu:
                upper_fu, lower_fu = trigrams_fu
                base_branches = NAJIA_BRANCHES[lower_fu]["inner"] + NAJIA_BRANCHES[upper_fu]["outer"]
                target_rel = _element_to_relation(yuan_shen_element, palace_element)
                for pos_idx, br in enumerate(base_branches):
                    if _branch_to_relation(br, palace_element) == target_rel:
                        yuan_shen_fu = {
                            "position": pos_idx + 1,
                            "branch": br,
                            "element": _branch_element(br),
                            "six_relation": target_rel,
                        }
                        break

    if not ji_shen_positions and ji_shen_element:
        first_hex_name = get_palace_first_hexagram(palace)
        if first_hex_name:
            trigrams_fu = HEXAGRAM_TRIGRAMS.get(first_hex_name)
            if trigrams_fu:
                upper_fu, lower_fu = trigrams_fu
                base_branches = NAJIA_BRANCHES[lower_fu]["inner"] + NAJIA_BRANCHES[upper_fu]["outer"]
                target_rel = _element_to_relation(ji_shen_element, palace_element)
                for pos_idx, br in enumerate(base_branches):
                    if _branch_to_relation(br, palace_element) == target_rel:
                        ji_shen_fu = {
                            "position": pos_idx + 1,
                            "branch": br,
                            "element": _branch_element(br),
                            "six_relation": target_rel,
                        }
                        break

    if not chou_shen_positions and chou_shen_element:
        first_hex_name = get_palace_first_hexagram(palace)
        if first_hex_name:
            trigrams_fu = HEXAGRAM_TRIGRAMS.get(first_hex_name)
            if trigrams_fu:
                upper_fu, lower_fu = trigrams_fu
                base_branches = NAJIA_BRANCHES[lower_fu]["inner"] + NAJIA_BRANCHES[upper_fu]["outer"]
                target_rel = _element_to_relation(chou_shen_element, palace_element)
                for pos_idx, br in enumerate(base_branches):
                    if _branch_to_relation(br, palace_element) == target_rel:
                        chou_shen_fu = {
                            "position": pos_idx + 1,
                            "branch": br,
                            "element": _branch_element(br),
                            "six_relation": target_rel,
                        }
                        break

    # ---------- 2.4: 处理用神两现/伏藏 ----------
    has_fu_cang = use_god_category not in [
        yao.get("six_relation", "") for yao in yao_lines
    ] if yao_lines else True

    # ---------- 构建输出 ----------
    # 用神位置选择优先级：
    # 1. 应爻位置的用神（占婚/占失等古籍断法"取应爻"）
    # 2. 世爻位置的用神
    # 3. 动爻位置的用神（发动者为主）
    # 4. 临月/日者
    # 5. 第一个位置（fallback）
    # 计算世/应位置
    world_position = None
    for yao in yao_lines:
        if yao.get("is_world"):
            world_position = yao.get("position")
            break
    response_position = None
    if world_position:
        from yishu_core.najia import response_position as _resp_of
        response_position = _resp_of(world_position)

    def _use_god_priority(pos_info):
        p = pos_info.get("position", 99)
        brk = pos_info.get("earthly_branch", "")

        def _changed_branch_of(pos):
            try:
                ch_name = (r.get("changed_hexagram") or {}).get("name")
                if ch_name:
                    cb = get_changed_hexagram_branch(ch_name, pos)
                    if cb:
                        return cb
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
                # 动而自伤：劣于「静而完整」（数值更大=优先级更低）
                return 8
            return 0
        # 1 旬空逢日冲填实（空亡反被激活）
        if pos_info.get("is_empty") and _is_chong(brk, day_branch):
            return 1
        # 2 静爻逢日冲暗动（非空，旺相者力强，《增删易》重动轻静）
        if (not pos_info.get("is_moving")) and (not pos_info.get("is_empty")) and _is_chong(brk, day_branch):
            return 2
        # 3 应爻位置（占婚/占失等古籍断法）
        if p == response_position:
            return 3
        # 4 世爻位置
        if p == world_position:
            return 4
        # 5 临月建
        if pos_info.get("is_at_month"):
            return 5
        # 6 临日辰
        if pos_info.get("is_at_day"):
            return 6
        # 7 静而不空不破（完整有气）—— 优先于动而自伤/动空
        if (not pos_info.get("is_moving")) and (not pos_info.get("is_empty")) and (not pos_info.get("is_month_break")):
            return 7
        # 8 动而空 / 空破 / 动而自伤
        if pos_info.get("is_moving") or pos_info.get("is_empty") or pos_info.get("is_month_break"):
            return 8
        return 9 + p

    if use_god_positions:
        use_god_positions_sorted = sorted(use_god_positions, key=_use_god_priority)
        selected_use_god = use_god_positions_sorted[0]
    elif has_fu_cang:
        # 伏藏用神：构建一个虚拟的 use_god_position 信息以便 downstream 使用
        fu_detail_tmp = _check_fu_cang(r, use_god_category, palace_element)
        if fu_detail_tmp and fu_detail_tmp.get("results"):
            fu_entry = fu_detail_tmp["results"][0]
            fu_shen_tmp = fu_entry.get("fu_shen", {})
            selected_use_god = {
                "position": fu_shen_tmp.get("position", 0),
                "name": fu_shen_tmp.get("name", "伏藏用神"),
                "earthly_branch": fu_shen_tmp.get("branch", ""),
                "element": fu_shen_tmp.get("element", use_god_element),
                "six_relation": use_god_category,
                "is_fu_cang": True,
                "is_moving": False,
                "is_world": False,
                "is_at_month": False,
                "is_at_day": False,
                "is_empty": fu_shen_tmp.get("branch", "") in (r.get("empty_branches") or []),
            }
        else:
            selected_use_god = None
    else:
        selected_use_god = None

    return {
        "question_category": question_category,
        "use_god_category": use_god_category,
        "use_god_basis": use_god_basis,
        "use_god_element": use_god_element,
        "use_god_positions": use_god_positions,
        "selected_use_god": selected_use_god,
        "has_use_god_in_hexagram": len(use_god_positions) > 0,
        "use_god_count": len(use_god_positions),
        "has_fu_cang": has_fu_cang,
        "fu_cang_detail": _check_fu_cang(r, use_god_category, palace_element) if has_fu_cang else None,
        "yuan_shen": {
            "category": _element_to_relation(yuan_shen_element, palace_element),
            "element": yuan_shen_element,
            "positions": yuan_shen_positions,
            "fu_cang": yuan_shen_fu,
        },
        "ji_shen": {
            "category": _element_to_relation(ji_shen_element, palace_element),
            "element": ji_shen_element,
            "positions": ji_shen_positions,
            "fu_cang": ji_shen_fu,
        },
        "chou_shen": {
            "category": _element_to_relation(chou_shen_element, palace_element),
            "element": chou_shen_element,
            "positions": chou_shen_positions,
            "fu_cang": chou_shen_fu,
        },
        "world_position": world_position,
        "summary_text": (
            f"问的是「{question_category}」，用神取{use_god_category}（五行{use_god_element}）。"
            f"{'卦中用神在 ' + '、'.join(str(p.get('position','')) + '爻' for p in use_god_positions) if use_god_positions else '本卦用神不现，须查伏神'}。"
            f"原神{_element_to_relation(yuan_shen_element, palace_element)}（{yuan_shen_element}）"
            f"{'现于' + ''.join(str(p.get('position','')) + '爻 ' for p in yuan_shen_positions) if yuan_shen_positions else '伏藏' + ('（' + yuan_shen_fu['branch'] + '·' + _pos_to_name(yuan_shen_fu['position']) + '）' if yuan_shen_fu else '（无）')}，"
            f"忌神{_element_to_relation(ji_shen_element, palace_element)}（{ji_shen_element}）"
            f"{'现于' + ''.join(str(p.get('position','')) + '爻 ' for p in ji_shen_positions) if ji_shen_positions else '伏藏' + ('（' + ji_shen_fu['branch'] + '·' + _pos_to_name(ji_shen_fu['position']) + '）' if ji_shen_fu else '（无）')}，"
            f"仇神{_element_to_relation(chou_shen_element, palace_element)}（{chou_shen_element}）"
            f"{'现于' + ''.join(str(p.get('position','')) + '爻 ' for p in chou_shen_positions) if chou_shen_positions else '伏藏' + ('（' + chou_shen_fu['branch'] + '·' + _pos_to_name(chou_shen_fu['position']) + '）' if chou_shen_fu else '（无）')}。"
        ),
    }


def _use_god_rules() -> list[dict]:
    """装载规则表；读不到就返回空表（宁可退回词典，也不硬编一份"假装有出处"的规则）。"""
    global _USE_GOD_RULES
    if _USE_GOD_RULES is None:
        path = Path(__file__).resolve().parents[1] / "data" / "rules" / "use_god_relations.json"
        try:
            _USE_GOD_RULES = json.loads(path.read_text(encoding="utf-8")).get("rules") or []
        except (OSError, ValueError):
            _USE_GOD_RULES = []
    return _USE_GOD_RULES


_USE_GOD_RULES: list[dict] | None = None


def _strip_hex_names(text: str) -> str:
    """从待匹配文本里剥掉六十四卦名。

    卦名里的字不是问事内容："益之小畜"的"畜"会让"凡占六畜皆以子孫為用"误触发，
    "归妹"的"妹"会让"占兄弟姐妹→兄弟"误触发。用神只由问的事决定，不由起的卦决定。
    """
    for name in _HEX_NAMES:
        text = text.replace(name, "")
    return text


def _strip_chart_tail(text: str) -> str:
    """剥掉题面末尾的卦名（"…占投资经营，益之小畜"里的"益之小畜"）。

    用神只该由"问的是什么事"决定。不剥的话，"小畜"的"畜"会去命中"凡占六畜皆以子孫為用"，
    把投资经营判成占牲口——卦名混进问事文本是关键词法的通病，不是一条规则的事。
    """
    m = _CHART_TAIL.search(text)
    if m and m.group("orig") in HEXAGRAM_TRIGRAMS and m.group("chg") in HEXAGRAM_TRIGRAMS:
        return text[:m.start()]
    return text


def _match_use_god_rule(text: str) -> dict | None:
    """命中原书取用法则 → 该条规则。priority 小者优先，同级取更长（更具体）的触发词。"""
    from yishu_core.symbols import normalize_question_text
    text = _strip_chart_tail(normalize_question_text(text))
    text = _strip_hex_names(text)
    best = None
    for rule in _use_god_rules():
        hits = [t for t in rule.get("trigger") or [] if t and t in text]
        if not hits:
            continue
        ctx = rule.get("context") or []
        if ctx and not any(c in text for c in ctx):
            continue
        rank = (rule.get("priority", 99), -max(len(h) for h in hits))
        if best is None or rank < best[0]:
            best = (rank, rule)
    return best[1] if best else None


def _use_god_basis(question_category: str, question_text: str, chosen: str) -> str:
    """用神所本：消费 _decide_use_god 的决策元信息，四层各说各的实话。

    法则与"词典·有引文族"报「《增刪卜易》：…」并带族标签；覆盖层报「覆盖规则「…」」；
    词典·推断族明说是推断；兜底保留原默认文案。不许把词典猜的说成古籍定论（铁律三）。
    """
    got, meta = _decide_use_god(question_category, question_text)
    if got != chosen:
        # 决策与调用方拿到的用神对不上时不编故事：退回最保守的默认说法。
        return "问题词典默认（无古籍逐条出处，未见过的问法会退化）"
    if meta["source"] == "法则":
        return f"《增刪卜易》：{meta.get('citation', '')}"
    if meta["source"] == "覆盖":
        cite = meta.get("citation") or ""
        if cite:
            return f"覆盖规则「{meta['label']}」·《增刪卜易》：{cite}"
        return f"覆盖规则「{meta['label']}」（消歧层，无逐字引文）"
    if meta["source"] == "词典":
        keys = meta.get("keys") or []
        top = max(keys, key=len) if keys else ""
        b = _QUESTION_USE_GOD_BASIS.get(top) or {}
        label = b.get("label") or "问题词典"
        if b.get("kind") == "citation" and b.get("citation"):
            return f"《增刪卜易》：{b['citation']}（问题词典·{label}）"
        return f"问题词典推断（{label}·无古籍逐条出处）"
    return "问题词典默认（无古籍逐条出处，未见过的问法会退化）"


def _decide_use_god(question_category: str, question_text: str) -> tuple[str, dict]:
    """根据问题类型确定用神类别 — 使用打分制，避免顺序依赖。

    返回 (用神类别, 决策元信息 meta)：meta["source"] ∈ 法则|覆盖|词典|兜底，
    另带 label/citation/keys。`use_god_coverage` 的来源矩阵与 `_use_god_basis` 的
    所本文案都直接消费这份元信息，不再各自复刻判断（复刻过的那份把覆盖层命中的
    问法误报成了"兜底"）。分层顺序与重构前逐字一致；`_determine_use_god_category`
    取 [0] 供旧调用方，行为零漂移（金标准 288 例 + 三集分数核验）。
    """
    from yishu_core.symbols import normalize_question_text
    layer_cite = _USE_GOD_LAYER_CITATIONS  # data 层装载的覆盖层展示引文（逐字核验过）

    def _layer(label: str, god: str, cite_key: str = "") -> tuple[str, dict]:
        cite = (layer_cite.get(cite_key) or {}).get("citation", "") if cite_key else ""
        return god, {"source": "覆盖", "label": label, "citation": cite, "keys": []}

    # 关键词表按简体写，而问事文本可能是繁体（《增刪卜易》原文、以及任何繁体输入）。
    # 不归一时"占候文書"匹配不上"文书"，用神静默退化成世爻——外部集上错的那 2 例即此。
    combined = normalize_question_text(f"{question_category} {question_text}")

    # --- 原书明写的取用法则优先（带引文可核；《增刪卜易·用神章》"占父母弟兄取用神者
    #     皆在用神章內詳之"——关系定了用神就定了，不该由现代问法词典猜） ---
    rule = _match_use_god_rule(combined)
    if rule:
        return rule["use_god"], {"source": "法则", "label": "关系优先法则",
                                 "citation": rule.get("citation", ""),
                                 "keys": list(rule.get("trigger") or [])}

    # --- 特殊优先级覆盖（高于 _QUESTION_USE_GOD_MAP 中的映射） ---
    # 提到具体人（父亲/母亲/儿子/女儿等）时，以该人为用神，优先级高于"出行→世"
    if any(k in combined for k in ("父亲", "母亲", "爸爸", "妈妈", "爹", "娘", "祖父", "祖母", "岳父", "岳母", "公公", "婆婆")):
        return _layer("尊长称谓→父母", "父母")
    if any(k in combined for k in ("儿子", "女儿", "孩子", "孙子", "孙女", "儿媳", "女婿")):
        return _layer("晚辈称谓→子孙", "子孙")
    # 久病占取世爻为用（书名归属《卜筮正宗》，该书原文未入库——覆盖层不挂逐字引文）
    if "久病" in combined:
        return _layer("久病→世爻", "世爻")
    # 出行/行人占取世爻为用（仅当没有提到具体人时生效；出行章"世為出行人"见层引文表）
    if any(k in combined for k in ("出行", "行人")):
        return _layer("出行行人→世爻", "世爻", "出行")
    # 功名占取官鬼为用（原书驳"子动反为用"仍看官爻，引文见层引文表；优先级高于考试/学业→父母）
    if "功名" in combined:
        return _layer("功名→官鬼", "官鬼", "功名")

    # 精确匹配优先
    if question_category in _QUESTION_USE_GOD_MAP:
        return _QUESTION_USE_GOD_MAP[question_category],             {"source": "词典", "label": "", "citation": "", "keys": [question_category]}

    # 特殊复合语义（高优先级覆盖）：语境歧义消解
    # "见贵求财"：主体是"见贵"（求官）而非"求财" → 官鬼
    if "见贵" in combined and "求财" in combined:
        return _layer("见贵求财→官鬼", "官鬼", "见贵")
    # "占子病"/"子病"系列：直接取子孙为用神
    if "占子病" in combined or ("子病" in combined):
        return _layer("占子病→子孙", "子孙", "占子")
    # 胎孕：以子孙为胎息，优先于句中「妻」
    if any(k in combined for k in ("怀孕", "胎", "孕", "产", "怀")):
        return _layer("胎孕→子孙", "子孙", "胎孕")
    # 久病/自身/自占病：以世爻为己身
    if any(k in combined for k in ("久病", "自占病", "自身", "自测")) or (
        "病" in combined and any(k in combined for k in ("半年", "多月", "已久", "沉重"))
    ):
        return _layer("自占/久病→世爻", "世爻")
    # 科举功名：文书父母为主用（官鬼为录取参考，双用神）
    if any(k in combined for k in ("科举", "中第", "考试", "功名", "学业", "文书领取", "候文书")):
        return _layer("科举文书→父母", "父母", "文书")
    # 官司：官鬼为官方
    if any(k in combined for k in ("官司", "官非", "诬告", "诉讼", "官事")) and "师尊" not in combined:
        return _layer("司法官讼→官鬼", "官鬼")

    # 按类别统计匹配关键词数和优先级得分
    # 六亲 → [(category, matched_weight)]
    category_scores = {}
    # 记录每个类别首次出现位置（用于同分时的优先判断）
    category_first_pos = {}
    matched_pairs: list[tuple[str, str]] = []

    # 核心用神关键词加权
    # 注意：单字"财"/"官"容易在复合词中误匹配（如"见贵求财"中的财），已在特殊语义层处理
    CORE_USE_GOD_KEYWORDS = {"仆", "奴", "婢", "婚", "父", "兄",
                              "妻", "失", "疾病", "官事", "功名", "行人", "买卖",
                              "雇佣", "占仆", "占奴", "桑叶", "价格",
                              "求财", "求官", "见贵"}
    GENERIC_KEYWORDS = {"回", "何时", "何日", "归来", "何时愈", "何日愈", "成否",
                        "吉凶", "结局", "有否", "可得", "冲中逢合", "六合卦", "逢冲",
                        # 天干地支单字（避免在日期串中误匹配）
                        "子", "亥", "酉", "戌", "巳", "未", "申", "辰", "卯", "午", "寅", "丑",
                        "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸",
                        # 单字多义词降权（跨语境易误匹配）
                        "财", "官",
                        # 其他弱关联/高频误匹配词
                        "归", "见", "贵", "日", "月", "时"}

    for keyword, relation in _QUESTION_USE_GOD_MAP.items():
        if keyword in combined:
            matched_pairs.append((keyword, relation))
            # 关键词越长越具体，得分越高
            weight = len(keyword) ** 2
            if keyword in CORE_USE_GOD_KEYWORDS:
                weight *= 3
            elif keyword in GENERIC_KEYWORDS:
                weight *= 0.3
            if relation not in category_scores:
                category_scores[relation] = 0
                category_first_pos[relation] = combined.index(keyword)
            category_scores[relation] += weight

    if category_scores:
        max_score = max(category_scores.values())
        # 获取所有最高分的类别
        candidates = [cat for cat, s in category_scores.items() if s == max_score]
        if len(candidates) == 1:
            got = candidates[0]
        else:
            # 同分时，选择在问题中出现位置最靠前的（即更早被提及=更核心主题）
            got = min(candidates, key=lambda c: category_first_pos[c])
        deciding = [k for k, rel in matched_pairs if rel == got]
        return got, {"source": "词典", "label": "", "citation": "", "keys": deciding}

    # 默认：自测 → 世爻
    return "世爻", {"source": "兜底", "label": "", "citation": "", "keys": []}


def _determine_use_god_category(question_category: str, question_text: str) -> str:
    """（薄包装）取用神类别；决策与来源标签一并返回的版本见 _decide_use_god。"""
    return _decide_use_god(question_category, question_text)[0]


def _find_use_god_positions(
    yao_lines: list[dict],
    use_god_category: str,
    palace_element: str,
    month_branch: str,
    empty: list[str],
) -> list[dict]:
    """
    在卦中查找用神所在位置。
    处理用神两现或多现的情况，返回候选列表。
    """
    if use_god_category == "世爻":
        # 世爻为用
        for yao in yao_lines:
            if yao.get("is_world"):
                return [{
                    "position": yao.get("position"),
                    "name": _pos_to_name(yao.get("position", 0)),
                    "earthly_branch": yao.get("earthly_branch", ""),
                    "element": _branch_element(yao.get("earthly_branch", "")),
                    "is_moving": yao.get("is_moving", False),
                    "is_empty": yao.get("earthly_branch", "") in empty,
                    "is_month_break": False,
                    "reason": "世爻为用",
                }]
        return []

    # 普通六亲查找
    positions = []
    for yao in yao_lines:
        if yao.get("six_relation") == use_god_category:
            branch = yao.get("earthly_branch", "")
            positions.append({
                "position": yao.get("position"),
                "name": _pos_to_name(yao.get("position", 0)),
                "earthly_branch": branch,
                "element": _branch_element(branch),
                "is_moving": yao.get("is_moving", False),
                "is_empty": branch in empty,
                "is_month_break": yao.get("is_month_break", False),
                "is_at_month": branch == month_branch,
                "reason": "",
            })

    # 用神筛选（《卜筮正宗》）：不做任何预过滤，全部候选交排序层统一决策。
    # 说明（P0-3 修正）：
    #   1) 旬空逢日冲则"填实"有力，动而空须出空方应——空亡候选不可剔除；
    #   2) 静爻逢日冲为暗动（《增删易》重动轻静），可能优于明动而空的候选；
    #   3) 应位/世位用神在古籍断法中权重极高。
    return positions


def _find_relation_positions(
    yao_lines: list[dict],
    target_element: str,
    palace_element: str,
) -> list[dict]:
    """查找指定五行（对应某六亲）在卦中的位置"""
    if not target_element:
        return []

    result = []
    for yao in yao_lines:
        branch = yao.get("earthly_branch", "")
        if _branch_element(branch) == target_element:
            result.append({
                "position": yao.get("position"),
                "name": _pos_to_name(yao.get("position", 0)),
                "earthly_branch": branch,
                "six_relation": yao.get("six_relation", ""),
                "six_spirit": yao.get("six_spirit", ""),
                "is_moving": yao.get("is_moving", False),
                "is_empty": yao.get("is_empty", False),
            })
    return result


def _element_to_relation(element: str, palace_element: str) -> str:
    """五行转六亲"""
    return get_relation_from_element(element, palace_element)


def _branch_to_relation(branch: str, palace_element: str) -> str:
    """根据地支五行确定六亲"""
    return get_relation_from_element(_branch_element(branch), palace_element)


def _check_fu_cang(
    r: dict,
    use_god_category: str,
    palace_element: str,
) -> dict | None:
    """
    检查伏藏：用神不现时，从本宫首卦查找伏神位置。
    《黄金策》：「用神伏藏，查伏于何爻之下」
    """
    hex_info = safe_get(r, "original_hexagram", default={})
    yao_lines = safe_get(hex_info, "yao_lines", default=[])
    palace = safe_get(hex_info, "palace", default="")

    if not palace or not yao_lines:
        return None

    # 获取本宫首卦名
    first_hex_name = get_palace_first_hexagram(palace)
    if not first_hex_name:
        return None

    # 获取本宫首卦的地支排列
    trigrams = HEXAGRAM_TRIGRAMS.get(first_hex_name)
    if not trigrams:
        return None

    upper_name, lower_name = trigrams
    first_hex_branches = NAJIA_BRANCHES[lower_name]["inner"] + NAJIA_BRANCHES[upper_name]["outer"]

    # 查找本宫首卦中对应用神的六亲位置
    target_positions = []
    for idx, branch in enumerate(first_hex_branches):
        relation = get_relation_from_element(_branch_element(branch), palace_element)
        if relation == use_god_category:
            pos = idx + 1
            target_positions.append({
                "position": pos,
                "name": _pos_to_name(pos),
                "branch": branch,
                "element": _branch_element(branch),
            })

    if not target_positions:
        return None

    # 对于每个伏神位置，检查飞神
    results = []
    for target in target_positions:
        pos = target["position"]
        # 获取当前卦对应位置的数据（飞神）
        fei_shen = None
        for yao in yao_lines:
            if yao.get("position") == pos:
                fei_shen = {
                    "position": pos,
                    "branch": yao.get("earthly_branch", ""),
                    "six_relation": yao.get("six_relation", ""),
                    "element": _branch_element(yao.get("earthly_branch", "")),
                }
                break

        can_emerge = True  # 本层不做判定：真正判据在 classical_enhancements._evaluate_hidden_spirit_emergence

        results.append({
            "fu_shen": target,
            "fei_shen": fei_shen,
            "position": pos,
            "can_emerge": can_emerge,
        })

    return {
        "palace_first_hexagram": first_hex_name,
        "results": results,
    }



__all__ = [
    "step2_identify_use_god",
    "_use_god_rules",
    "_strip_hex_names",
    "_strip_chart_tail",
    "_match_use_god_rule",
    "_use_god_basis",
    "_decide_use_god",
    "_determine_use_god_category",
    "_find_use_god_positions",
    "_find_relation_positions",
    "_element_to_relation",
    "_branch_to_relation",
    "_check_fu_cang",
]
