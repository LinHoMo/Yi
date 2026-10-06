# -*- coding: utf-8 -*-
"""唯一评分器：古籍案例对齐分（tune / holdout 分别出分，禁止混分）。

    python scripts/evaluate.py                      # 跑全部合并出分
    python scripts/evaluate.py --split tune
    python scripts/evaluate.py --split holdout --verbose
    python scripts/evaluate.py --stage score --engine-file data/cases/eval_all.json
    python scripts/evaluate.py --split wikisource_holdout --yingqi-mode both

口径说明（务必连同分数一起阅读）：
  本脚本衡量的是**引擎输出与古籍案例要点的一致性**，不是现实世界预言命中率。

两种计分模型同时输出：
  strict —— 基准未记录某维度时该维度记 N/A 并从分母剔除；应期不对齐不得分。
  legacy —— 复刻 2026-09-20 之前的口径：N/A 按满分给、应期有 8/15 保底。
            历史上报出的 tune 100% 就是这个口径的产物，此处保持可复现。

应期体检评分（--yingqi-mode）：
  strict —— 主应期支精确命中才算命中（与 score_case 一致）
  loose  —— 命中任一区间化规则即算命中（相对窗 / 绝对日期 / 位置无关）
  both   —— 双列对比输出（默认）

维度与权重（单一真值源，总和 100）：
  用神六亲 12 / 用神地支 8 / 用神爻位 4 / 六神临用 4 / 月令旺衰 5 / 墓库 3 /
  卦身支 2 / 三合局 2 / 用神入三合 2 /
  吉凶方向 35 / 格局覆盖 12 / 应期 11
"""
from __future__ import annotations
from kernel_path import kernel_dir  # noqa: E402

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "scripts"), str(kernel_dir(__file__))):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.eval import verdict_direction, run_eval, report as _report  # noqa: E402
from yishu_core.symbols import EARTHLY_BRANCHES  # noqa: E402  地支序唯一真值源
from liuyao_timing import relative_window, resolve_case_anchor, date_in_window  # noqa: E402
import case_runner  # noqa: E402

CASES = ROOT / "data" / "cases" / "classical_cases.json"
OUT_DIR = ROOT / "data" / "cases"

DAY_CHARS = EARTHLY_BRANCHES
# 进正则字符类前必须先 "".join：DAY_CHARS 是 core 的 list，直接插值会把 list 的
# repr 写进去，字符类在第一个 ] 处提前闭合、正则永不匹配。
BRANCH_CLASS = "".join(DAY_CHARS)

# 应期的单位必须对上才算命中。旧口径只比地支字符，基准写"未月"而引擎给"未日"
# 也判为主应期命中——三个单位互相顶替等于给应期白送分，这是外部集 17.1% 仍偏高的原因之一。
YQ_UNIT_RE = re.compile(f"([{BRANCH_CLASS}])(年|月|日|時|时)")


def _expected_unit(label: str) -> str:
    m = YQ_UNIT_RE.search(str(label or ""))
    if not m or m.group(2) in ("時", "时"):
        return "日"
    return m.group(2)


def _unit_pool(eng: dict, unit: str) -> list:
    if unit == "月":
        return eng.get("yingqi_months") or []
    if unit == "年":
        return eng.get("yingqi_years") or []
    return eng.get("yingqi_branches") or []


def _offered_branches(pool) -> list:
    offered = []
    for token in pool:
        for ch in _branches_in(str(token)[:2]):
            if ch not in offered:
                offered.append(ch)
    return offered

WEIGHTS = {
    "use_god_category": 12,
    "use_god_branch": 8,
    "use_god_position": 4,
    "use_god_six_spirit": 4,
    "use_god_wangshuai": 5,
    "use_god_muku": 3,
    "gua_shen_branch": 2,
    "sanhe_full_combo": 2,
    "use_god_in_sanhe": 2,
    "verdict": 35,
    "patterns": 12,
    "yingqi": 11,
}

PATTERNS = [
    "冲中逢合", "合处逢冲", "回头克", "回头生", "近病逢空", "近病逢合", "绝处逢生",
    "飞克伏", "伏生飞", "飞空得出", "飞生伏", "入墓", "随官入墓", "反吟", "伏吟",
    "六合", "六冲", "伏藏", "伏神", "长生", "帝旺", "沐浴", "化合", "化退神", "化进神",
    "旬空", "填实", "出空", "出旬", "暗动", "月破", "日辰合世", "变卦六合", "世爻",
    "动空", "原神生用", "泄气", "游魂", "归魂", "用神多现", "世持财", "内卦", "迟归",
    "用神生世", "兄弟持世", "墓", "绝于",
    # 格局十三/十四（references/pattern_reference.md）：真空·假空、独发·独静、
    # 变卦六冲（"合处逢冲/冲中逢合"的双卦落点）、三会方局、三传克制。
    "真空", "假空", "独发", "独静", "变卦六冲", "三会", "三传克制", "卦反吟", "卦伏吟",
]

PATTERN_ALIASES = {
    "旬空": ["旬空", "出旬", "填实", "冲空"],
    "出空": ["出空", "出旬", "填实", "冲空"],
    "出旬": ["出旬", "填实", "冲空"],
    "伏神": ["伏神", "伏藏"],
    "伏藏": ["伏藏", "伏神"],
    "世爻": ["世爻", "持世", "世持"],
    "迟归": ["迟归", "用神生世", "生世"],
    "用神生世": ["用神生世", "生世", "迟归"],
    "兄弟持世": ["兄弟持世", "持兄", "兄弟"],
    "世持财": ["世持财", "持世"],
    "用神多现": ["用神多现", "多现", "两现", "现于"],
    "伏神得出": ["伏神得出", "飞空得出", "飞神旬空"],
    "飞空得出": ["飞空得出", "飞神旬空", "伏神得出"],
    "化退神": ["化退神", "化退"],
    "化进神": ["化进神", "化进"],
    "动则生": ["动则生", "原神生用", "动空"],
    "原神生用": ["原神生用", "动则生"],
    "近病逢空": ["近病逢空", "近病"],
    "近病逢合": ["近病逢合", "近病"],
    # 格局十三/十四：真空假空互斥、独发独静互斥、三会与三合同源别名
    "真空": ["真空"],
    "假空": ["假空"],
    "独发": ["独发"],
    "独静": ["独静"],
    "三会": ["三会", "三会局"],
    "变卦六冲": ["变卦六冲", "六冲"],
    "三传克制": ["三传克制", "三传俱克"],
    "卦反吟": ["卦反吟", "反吟"],
    "卦伏吟": ["卦伏吟", "伏吟"],
}

RHYTHM_PAIRS = [
    (("次日", "当天", "当日"), ("应速", "次日", "当日", "快则", "近日")),
    (("年内", "月余", "经年"), ("年内", "应迟", "旺相之月", "月余", "窗口偏长", "节奏偏慢")),
    (("不安", "反复", "难成"), ("不安", "反复", "合处逢冲", "冲中逢合", "拖延")),
    (("出空", "出旬"), ("出空", "出旬", "填实", "冲空")),
]


def _na(value) -> bool:
    return value in (None, "", "?")


def score_case(eng: dict, exp: dict, model: str, case: dict | None = None) -> dict:
    """单例打分。返回 {dim: (earned, applicable_weight, note)}。

    case —— 完整案例（可选）。相对期基准（"次日/月余/年内"，无应支可排）需要
    案例顶层的 year/month/day 锚日才能换算天数窗；exp 只是 expected 子字典，
    拿不到锚日。此前该分支的锚日恒为 None → 相对窗比对从未生效（死代码）。
    """
    dims: dict[str, tuple[int, int, str]] = {}

    # 用神六亲
    e_cat, x_cat = eng.get("use_god_category", ""), exp.get("use_god_god") or exp.get("use_god") or ""
    hit = (e_cat == x_cat)
    w = WEIGHTS["use_god_category"]
    if _na(x_cat):
        # 基准未取用神（古籍那条只记了验期）→ 无从对照，记 N/A，不算引擎失分。
        # legacy 沿用旧口径（跟着六亲走），两模型因此不可跨口径比较。
        dims["use_god_category"] = (w if hit else 0, w, "基准未记用神，随六亲") if model == "legacy" \
            else (0, 0, "基准未记用神 → N/A")
    else:
        dims["use_god_category"] = (w if hit else 0, w,
                                    f"{e_cat}{'=' if hit else '≠'}{x_cat}")

    # 用神地支
    e_br, x_br = eng.get("use_god_branch", ""), exp.get("use_god_branch", "")
    w = WEIGHTS["use_god_branch"]
    if _na(x_br):
        if model == "legacy":
            dims["use_god_branch"] = (w if hit else 0, w, "基准未记支，随六亲")
        else:
            dims["use_god_branch"] = (0, 0, "基准未记支 → N/A")
    else:
        ok = e_br == x_br
        dims["use_god_branch"] = (w if ok else 0, w, f"{e_br}{'=' if ok else '≠'}{x_br}")

    # 用神爻位
    e_pos, x_pos = eng.get("use_god_position"), exp.get("use_god_position")
    w = WEIGHTS["use_god_position"]
    if _na(x_pos):
        dims["use_god_position"] = (w, w, "基准未记位，满分") if model == "legacy" else (0, 0, "基准未记位 → N/A")
    else:
        ok = str(e_pos) == str(x_pos)
        dims["use_god_position"] = (w if ok else 0, w, f"{e_pos}{'=' if ok else '≠'}{x_pos}")

    # 六神临用 / 月令旺衰 / 墓库 / 卦身 / 三合（附加对表维度，expected 由书面用神机械派生，对表回归性质）
    e_extra = eng.get("extra") or {}
    for dim in ("use_god_six_spirit", "use_god_wangshuai", "use_god_muku",
                "gua_shen_branch", "sanhe_full_combo", "use_god_in_sanhe"):
        w = WEIGHTS[dim]
        e_v, x_v = e_extra.get(dim, ""), exp.get(dim)
        if _na(x_v):
            dims[dim] = (w, w, "基准未记，满分") if model == "legacy" else (0, 0, "基准未记 → N/A")
        else:
            ok = str(e_v) == str(x_v)
            dims[dim] = (w if ok else 0, w, f"{e_v}{'=' if ok else '≠'}{x_v}")

    # 吉凶方向
    w = WEIGHTS["verdict"]
    ed, xd = verdict_direction(eng.get("verdict")), verdict_direction(exp.get("verdict"))
    if _na(exp.get("verdict")):
        # 基准只记了验期、没记吉凶（外部集里过半是这种）→ 该维无从对照，记 N/A。
        # 否则 40 分会凭空判给"引擎说了不算"，把分数压成假低。
        dims["verdict"] = (w, w, "基准未记吉凶，满分") if model == "legacy" \
            else (0, 0, "基准未记吉凶 → N/A")
    else:
        if ed == xd:
            vs, note = w, "方向一致"
        elif ed * xd > 0:
            vs, note = int(w * 0.8), "同向异强"
        elif str(exp.get("verdict")) in ("平/不利", "平") and ed <= 0:
            vs, note = int(w * 0.8), "基准平·引擎偏负"
        elif ed == 0:
            vs, note = int(w * 0.3), "引擎中性回避"
        else:
            vs, note = 0, "方向相反"
        dims["verdict"] = (vs, w, f"{eng.get('verdict')}/{exp.get('verdict')} {note}")

    # 格局覆盖
    w = WEIGHTS["patterns"]
    baseline = " ".join(str(x) for x in (exp.get("key_points") or [])) + " " + str(exp.get("detail") or "")
    needed = [p for p in PATTERNS if p in baseline]
    combined = " ".join([t for t in (eng.get("pattern_tags") or [])] +
                        [t for t in (eng.get("reasoning_chain") or []) if isinstance(t, str)])
    if not needed:
        dims["patterns"] = (w, w, "基准无格局词，满分") if model == "legacy" else (0, 0, "基准无格局词 → N/A")
    else:
        detected = [p for p in needed if p in combined or any(a in combined for a in PATTERN_ALIASES.get(p, []))]
        ratio = len(detected) / len(needed)
        vs = w if ratio >= 0.5 else (int(w * 0.66) if ratio > 0 else 0)
        dims["patterns"] = (vs, w, f"{len(detected)}/{len(needed)}:{','.join(detected[:4]) or '无'}")

    # 应期
    w = WEIGHTS["yingqi"]
    e_yq = str(eng.get("yingqi") or "")
    x_yq = str(exp.get("yingqi") or "")
    declared_tokens = [str(b) for b in (eng.get("yingqi_branches") or [])]
    declared_all = declared_tokens + [str(b) for b in (eng.get("yingqi_months") or [])] \
        + [str(b) for b in (eng.get("yingqi_years") or [])]
    declared = " ".join(declared_all)
    head = e_yq.split("依据")[0]
    e_all = head + " " + declared
    e_verbose = e_yq + " " + declared + " " + " ".join(
        str(d.get("date") if isinstance(d, dict) else d) for d in (eng.get("yingqi_dates") or []))
    probe = e_verbose if model == "legacy" else e_all
    if _na(x_yq):
        dims["yingqi"] = (w, w, "空白基准，满分") if model == "legacy" else (0, 0, "空白基准 → N/A")
    elif model == "legacy":
        x_branches = [c for c in DAY_CHARS if c in x_yq]
        rhythm = any(any(k in x_yq for k in xk) and any(k in probe for k in ek)
                     for xk, ek in RHYTHM_PAIRS)
        if x_yq in probe or (x_branches and all(c in probe for c in x_branches)):
            dims["yingqi"] = (w, w, "应支全覆盖")
        elif any(c in probe for c in x_branches):
            dims["yingqi"] = (int(w * 0.8), w, "应支部分覆盖")
        elif rhythm:
            dims["yingqi"] = (int(w * 0.8), w, "节奏语义对齐")
        else:
            dims["yingqi"] = (8, w, "存在即保底")
    else:
        # strict 按**名次**给分，不按"有没有提到"给分。
        # 成员制打分会奖励骑墙：候选铺到 11/12 支就能白拿 15 分（旧口径的 100% 即由此而来）。
        # 名次只在**同单位**的候选池里数：基准是月级答案就去月级池里排名次。
        exp_unit = _expected_unit(x_yq)
        m_unit = YQ_UNIT_RE.search(x_yq)
        needed = [m_unit.group(1)] if m_unit else [c for c in DAY_CHARS if c in x_yq]
        offered = _offered_branches(_unit_pool(eng, exp_unit))
        rank = next((i + 1 for i, ch in enumerate(offered) if needed and ch in needed), None)
        if not needed:
            hit = x_yq in probe
            # 相对窗：锚日优先取案例顶层 year/month/day（case_runner 干支反查的
            # 同一实现落盘），否则退回 expected 内的公历日期；有锚日则换算绝对日窗
            # 比对引擎日期（引擎的"速应(次日)"等规则输出的就是锚日+N 的日历日期）；
            # 否则节奏语义对齐。
            from liuyao_timing import relative_window, resolve_case_anchor, date_in_window
            win = relative_window(x_yq)
            anchor = resolve_case_anchor((case or {}).get("input") or {}, case or {}) \
                if case else None
            if anchor is None:
                anchor = resolve_case_anchor((exp.get("input") or {}), exp) if isinstance(exp, dict) else None
            abs_hit = False
            if win and anchor:
                lo, hi, label = win
                yq_dates = eng.get("yingqi_dates") or []
                if isinstance(yq_dates, dict):
                    yq_dates = yq_dates.get("dates") or []
                dates = [str(d.get("date") if isinstance(d, dict) else d) for d in yq_dates]
                abs_hit = any(date_in_window(anchor, d, lo, hi) for d in dates if d)
            rhythm = any(
                any(k in x_yq for k in xk) and any(k in probe for k in ek)
                for xk, ek in RHYTHM_PAIRS
            )
            if abs_hit:
                dims["yingqi"] = (w, w, "绝对日窗命中")
            elif hit:
                dims["yingqi"] = (w, w, "字面命中")
            elif rhythm:
                dims["yingqi"] = (int(w * 0.7), w, "相对窗节奏语义对齐")
            else:
                dims["yingqi"] = (0, w, f"未对齐({x_yq})")
        elif rank == 1:
            dims["yingqi"] = (w, w, f"主应期命中（{exp_unit}级）")
        elif rank == 2:
            dims["yingqi"] = (int(w * 0.8), w, f"次应期命中（{exp_unit}级）")
        elif rank and rank <= 4:
            dims["yingqi"] = (int(w * 0.55), w, f"{exp_unit}级第 {rank} 位命中")
        elif any(c in probe for c in needed):
            dims["yingqi"] = (int(w * 0.35), w, f"仅在依据句中出现，未列为{exp_unit}级应期")
        else:
            dims["yingqi"] = (0, w, f"未给出基准应期({','.join(needed)}{exp_unit})")
    return dims


def score_yingqi_loose(eng: dict, exp: dict, case: dict | None = None) -> tuple[int, int, str]:
    """应期 loose 评分：命中任一即满分。

    命中规则（OR 逻辑）：
      1. 主应期支 = expected 支（与 strict top-1 同）
      2. expected 支出现在引擎任何单位级候选池中（位置无关）
      3. 引擎给出的相对窗 (relative_window) 覆盖 expected 支
         — 解析引擎文本中的相对关键词，锚日优先取 case 顶层，其次从 input.date 抽取
      4. 引擎给出的绝对日 (yingqi_dates) 含 expected 支

    参数：
      eng  —— 引擎单例输出
      exp  —— 基准 expected 子字典（必须含 yingqi）
      case —— 完整案例（可选，用于 resolve_case_anchor 的年月日/input.date 解析）
    """
    w = WEIGHTS["yingqi"]
    x_yq = str(exp.get("yingqi") or "")

    if _na(x_yq):
        return (0, 0, "空白基准 → N/A")

    exp_unit = _expected_unit(x_yq)
    m_unit = YQ_UNIT_RE.search(x_yq)
    needed = [m_unit.group(1)] if m_unit else _branches_in(x_yq)
    if not needed:
        e_yq = str(eng.get("yingqi") or "")
        if x_yq in e_yq:
            return (w, w, "字面命中 [loose]")
        return (0, w, f"未命中({x_yq})")

    offered = _offered_branches(_unit_pool(eng, exp_unit))

    # 引擎所有单位支集合
    eng_yq = str(eng.get("yingqi") or "")
    declared_tokens = [str(t) for t in (eng.get("yingqi_branches") or [])] + \
                      [str(t) for t in (eng.get("yingqi_months") or [])] + \
                      [str(t) for t in (eng.get("yingqi_years") or [])]
    declared_branches = _branches_in(" ".join(declared_tokens))

    # 引擎绝对日期集 (date, branch)
    eng_dates_data = eng.get("yingqi_dates") or {}
    if isinstance(eng_dates_data, dict):
        eng_date_list = [(d.get("date", ""), d.get("branch", ""))
                         for d in eng_dates_data.get("dates", []) if isinstance(d, dict)]
    else:
        eng_date_list = []

    # 锚日：优先从引擎 assembled_time 取，否则 resolve_case_anchor 退到 case 顶层
    anchor = None
    assembled = str(eng.get("assembled_time") or "")
    if assembled:
        try:
            anchor = datetime.strptime(assembled[:10], "%Y-%m-%d")
        except ValueError:
            pass
    if anchor is None and case is not None:
        anchor = resolve_case_anchor((case.get("input") or {}), case)

    # 规则 1: 主应期 = expected
    main_hit = bool(offered and offered[0] in needed)

    # 规则 2: 任何位置有 expected 支
    any_hit = bool(any(n in declared_branches for n in needed))

    # 规则 3: 相对窗覆盖
    rel_hit = False
    rel_note = ""
    win = relative_window(eng_yq)
    if win and anchor:
        lo_rel, hi_rel, label = win
        for d, br in eng_date_list:
            if d and br and br in needed and date_in_window(anchor, d, lo_rel, hi_rel):
                rel_hit = True
                rel_note = f"{label}覆盖{''.join(needed)}"
                break

    # 规则 4: 绝对日期含 expected 支
    abs_hit = False
    abs_note = ""
    if needed:
        for d, br in eng_date_list:
            if br in needed:
                abs_hit = True
                abs_note = f"日期{d}对应{''.join(needed)}"
                break

    if main_hit:
        return (w, w, f"主应期命中（{exp_unit}级）[loose]")
    elif any_hit:
        return (w, w, f"候选命中（{exp_unit}级）[loose]")
    elif rel_hit:
        return (w, w, f"相对窗命中（{exp_unit}级）[loose]: {rel_note}")
    elif abs_hit:
        return (w, w, f"日期命中（{exp_unit}级）[loose]: {abs_note}")
    else:
        return (0, w, f"未命中({x_yq})")


def evaluate(engine_out: dict, model: str, label: str, ids: list[str], verbose: bool) -> dict:
    """六爻古籍案例对齐评分（框架与 N/A 口径见 yishu_core.eval，此处只给维度比较）。"""
    base = {c["id"]: c for c in case_runner.load_cases()}

    def _score_case(eng: dict, exp: dict, model_: str) -> dict:
        # 引擎单例带 id，用它找回完整案例（相对期锚日在案例顶层，见 score_case docstring）
        return score_case(eng, exp, model_, case=base.get(eng.get("id")))

    return run_eval(engine_out, base, ids, WEIGHTS, _score_case, model, label, verbose)


def _branches_in(text: str) -> list[str]:
    """按出现顺序抽出互不重复的地支。"""
    seen, out = set(), []
    for ch in str(text or ""):
        if ch in DAY_CHARS and ch not in seen:
            seen.add(ch)
            out.append(ch)
    return out


def yingqi_discrimination(engine_out: dict, ids: list[str]) -> dict:
    """应期的"信息量"体检。

    只看召回会被候选集大小骗过去：若引擎把十二支列个遍，字面命中 100% 也毫无意义。
    这里只数引擎**自己声明的重点应期**（yingqi_branches），报告：
      候选集平均大小、top-1 命中率、基准应支在候选中的平均名次、
      以及"随机列同样多候选即全覆盖"的期望概率（召回分的无信息基线）。

    同时输出 loose 评分（区间化命中）指标：
      - loose_hit_rate: 命中任一 loose 规则（相对窗/绝对日期）即算命中
      - loose_rel_hit_rate: 通过相对窗命中的比例
      - loose_abs_hit_rate: 通过绝对日期命中的比例
    """
    base = {c["id"]: c for c in case_runner.load_cases()}
    by_e = {c.get("id"): c for c in engine_out.get("cases", [])}
    sizes, ranks, top1_hit, top1_n, random_p = [], [], 0, 0, []
    loose_hit, rel_hit, abs_hit, loose_n = 0, 0, 0, 0
    per_unit = {}

    for cid in ids:
        e, b = by_e.get(cid), base.get(cid)
        if not e or not b or "error" in e:
            continue
        x_yq = str((b.get("expected") or {}).get("yingqi") or "")
        m_unit = YQ_UNIT_RE.search(x_yq)
        needed = [m_unit.group(1)] if m_unit else _branches_in(x_yq)
        if not needed:
            continue
        unit = _expected_unit(x_yq)
        offered = _offered_branches(_unit_pool(e, unit))
        # 同单位候选池为空＝引擎根本没能在这个单位上作答，算失败而不是从分母里消失。
        # 跳过会让"答不出的单位"悄悄退出统计，n 变小、分数变好看，属于假指标。
        sizes.append(len(offered))
        top1_n += 1
        loose_n += 1
        u = per_unit.setdefault(unit, {"n": 0, "top1": 0, "ranks": [],
                                        "loose": 0, "rel": 0, "abs": 0})
        u["n"] += 1
        if not offered:
            continue
        k, n = len(needed), len(offered)
        p = 1.0
        for i in range(k):
            p *= max(n - i, 0) / (12 - i)
        random_p.append(p)
        if needed[0] == offered[0] or offered[0] in needed:
            top1_hit += 1
            u["top1"] += 1
        hit_at = next((i + 1 for i, ch in enumerate(offered) if ch in needed), None)
        if hit_at:
            ranks.append(hit_at)
            u["ranks"].append(hit_at)

        # ── loose 评分判定 ──
        loose_result = score_yingqi_loose(e, b.get("expected") or {}, b)
        if loose_result[0] > 0:
            loose_hit += 1
            u["loose"] += 1
        # 解析 loose 命中类型
        loose_note = loose_result[2]
        if "[loose]" in loose_note:
            if "相对窗" in loose_note:
                rel_hit += 1
                u["rel"] += 1
            if "日期命中" in loose_note:
                abs_hit += 1
                u["abs"] += 1

    if not sizes:
        return {}
    return {
        "cases_with_yingqi": len(sizes),
        "avg_candidate_set_size": round(sum(sizes) / len(sizes), 1),
        "top1_hit_rate": round(top1_hit * 100.0 / top1_n, 1) if top1_n else None,
        "avg_rank_of_correct": round(sum(ranks) / len(ranks), 2) if ranks else None,
        "ranked_cases": len(ranks),
        "random_full_coverage_expectancy": round(sum(random_p) * 100.0 / len(random_p), 1),
        "loose_hit_rate": round(loose_hit * 100.0 / loose_n, 1) if loose_n else None,
        "loose_rel_hit_rate": round(rel_hit * 100.0 / loose_n, 1) if loose_n else None,
        "loose_abs_hit_rate": round(abs_hit * 100.0 / loose_n, 1) if loose_n else None,
        "yingqi_day": None,
        "yingqi_month": None,
        "yingqi_year": None,
        "by_unit": {u: {"n": v["n"],
                        "top1_hit_rate": round(v["top1"] * 100.0 / v["n"], 1) if v["n"] else None,
                        "avg_rank": round(sum(v["ranks"]) / len(v["ranks"]), 2) if v["ranks"] else None,
                        "ranked": len(v["ranks"]),
                        "loose_hit_rate": round(v["loose"] * 100.0 / v["n"], 1) if v["n"] else None,
                        "loose_rel_hit_rate": round(v["rel"] * 100.0 / v["n"], 1) if v["n"] and v["rel"] else None,
                        "loose_abs_hit_rate": round(v["abs"] * 100.0 / v["n"], 1) if v["n"] and v["abs"] else None}
                    for u, v in sorted(per_unit.items())},
    }


def report(res: dict) -> None:
    """六爻出口：换行风格与共享 report 一致，避免两处给分逻辑。"""
    _report(res)


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="六爻古籍案例对齐评分（非现实预测命中率）")
    ap.add_argument("--split", choices=["tune", "holdout", "yingqi_holdout",
                                        "wikisource_holdout", "wikisource_direction",
                                        "huozhulin_holdout", "huozhulin_qualitative",
                                        "suigui_holdout", "bushi_zhengzong_holdout", "all"],
                    default="all")
    ap.add_argument("--ids", nargs="*", help="指定案例 ID，优先于 --split")
    ap.add_argument("--stage", choices=["run", "score", "all"], default="all")
    ap.add_argument("--engine-file", type=Path, help="已有的引擎输出（配合 --stage score）")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--save", action="store_true", help="写出 JSON 明细到 data/cases/")
    ap.add_argument("--yingqi-mode", choices=["strict", "loose", "both"], default="both",
                    help="应期体检评分模型（strict=精确支命中, loose=区间化命中, both=双列对比）")
    args = ap.parse_args()

    import case_runner

    if args.ids:
        ids, label = case_runner.load_ids(only=args.ids), "custom"
    else:
        ids, label = case_runner.load_ids(args.split), args.split

    if args.stage == "score" and args.engine_file:
        loaded = json.loads(Path(args.engine_file).read_text(encoding="utf-8"))
        engine_out = loaded.get("engine_output", loaded)
        available = [c.get("id") for c in engine_out.get("cases", [])]
        ids = [i for i in ids if i in available] or available
        label = f"{label}(cached)"
    else:
        print(f"运行 {len(ids)} 例（{label}）…")
        engine_out = case_runner.run_ids(ids, verbose=args.verbose)

    exit_code = 0
    results = {}
    sources = {}
    for c in engine_out.get("cases", []):
        sources[c.get("time_source", "error" if "error" in c else "?")] = \
            sources.get(c.get("time_source", "error" if "error" in c else "?"), 0) + 1
    if sources:
        print("时刻还原方式：" + "，".join(f"{k}={v}" for k, v in sorted(sources.items())))

    for model in ("strict", "legacy"):
        res = evaluate(engine_out, model, label, ids, args.verbose)
        report(res)
        results[model] = res

    strict, legacy = results["strict"], results["legacy"]
    if strict["avg"] is None:
        print("无可用结果")
        return 1

    yq_mode = getattr(args, "yingqi_mode", "both")
    disc = yingqi_discrimination(engine_out, ids)
    if disc:
        results["yingqi_discrimination"] = disc
        print(f"\n应期信息量体检（n={disc['cases_with_yingqi']}，只看引擎自己声明的重点应期）")
        print(f"  候选集平均大小 {disc['avg_candidate_set_size']}/12 —— 越接近 12，召回分越没有信息量")
        print(f"  随机列同样多候选即全覆盖的期望 {disc['random_full_coverage_expectancy']}%"
              f"（召回分接近此值 = 等于没判断）")
        # 严格 / loose 双列对比
        strict_top1 = disc.get("top1_hit_rate")
        loose_top1 = disc.get("loose_hit_rate")
        strict_rank = disc.get("avg_rank_of_correct")
        ranked_n = disc.get("ranked_cases")
        if yq_mode in ("strict", "both"):
            print(f"  strict top-1 命中 {strict_top1}%；基准应支平均排在第 {strict_rank} 位"
                  f"（{ranked_n} 例可定位）← 这一项才见真章")
        if yq_mode in ("loose", "both") and loose_top1 is not None:
            rel_rate = disc.get("loose_rel_hit_rate") or 0
            abs_rate = disc.get("loose_abs_hit_rate") or 0
            print(f"  loose top-1 命中 {loose_top1}%（相对窗 {rel_rate}% + 绝对日期 {abs_rate}%）")
        # 应期日/月/年分列
        unit_map = {"日": "yingqi_day", "月": "yingqi_month", "年": "yingqi_year"}
        for u, v in (disc.get("by_unit") or {}).items():
            key = unit_map.get(u)
            if key and key in disc:
                disc[key] = dict(v)
            if yq_mode == "strict":
                print(f"    {u}级：n={v['n']} strict={v.get('top1_hit_rate')}%")
            elif yq_mode == "loose":
                print(f"    {u}级：n={v['n']} loose={v.get('loose_hit_rate')}%")
            else:
                print(f"    {u}级：n={v['n']} strict={v.get('top1_hit_rate')}% "
                      f"loose={v.get('loose_hit_rate')}%")

    print(f"\n口径差异：strict {strict['avg']}% vs legacy {legacy['avg']}%"
          f"（差 {round(legacy['avg'] - strict['avg'], 1)} 分来自空白基准满分与应期保底）")
    print("提示：本分数衡量与古籍案例要点的一致性，不代表现实预测命中率。")

    if args.save:
        out = OUT_DIR / f"eval_{label}.json"
        out.write_text(json.dumps({"results": results, "engine_output": engine_out},
                                  ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("明细 →", out)

    errored = [e["id"] for e in engine_out.get("errors", [])]
    if errored:
        print(f"\n引擎报错 {len(errored)} 例：{', '.join(errored)}")
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
