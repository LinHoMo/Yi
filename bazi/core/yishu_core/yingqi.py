# -*- coding: utf-8 -*-
"""应期回填判定口径 —— **唯一真值源**（架构评审 A2）。

同一语义「预测应期 → 现实回填 → 命中判定」在本仓有两条消费链：

  · 合参层 `synthesis/outcome_eval.py`（读人档案 `divinations[].outcome`）
  · 六爻 `disciplines/liuyao/dev_tools/feedback_store.py`（读学科反馈记录）

本模块把两条链**共用的口径常量、日期解析、日支反推与口径语句**收成一份，
两个消费方只准调用，不得各自再写一份表（`tools/check.py` 门 `[1i]` 检查）。

两种口径**并列存在、互不代替**——同一批数据用两种口径会得到两个数，
所以任何报分都必须写明用的是哪一种（`AGENTS.md` §一.3）：

  ① 名次制 `judge_rank`：断卦时给出的应期候选是**有序**的，实际发生日命中第 k 位
     → 按名次给分（主应期全分，越靠后越低）。问的是「候选排序质量」。
  ② 容差窗 `judge_window`：预测日是**集合**，实际发生日与某个预测日的距离落在
     容差内即算命中（严格 ±1 天；宽松 ±7 天，或 ±21 天内支同/六合/六冲）。
     问的是「应期数值接近程度」。

两条链的口径差别是**真实差别**（一个问排序、一个问距离），不是实现缺陷；
此前的缺陷是两处各写一份常量，且六爻侧的支合表多出两条错项（丑午、未申——
既非六合亦非六冲），会造成虚假宽松命中，现由本模块唯一持有并在门里锁死。
"""
from __future__ import annotations

from datetime import date

from yishu_core.ganzhi_calendar import EARTHLY_BRANCHES, day_ganzhi_index
from yishu_core.symbols import CHONG_PAIRS, HE_PAIRS

# ---------------------------------------------------------------- ② 容差窗
STRICT_WINDOW_DAYS = 1     # 严格：抵消排盘日差
LOOSE_WINDOW_DAYS = 7      # 宽松：纯日期容差
BRANCH_WINDOW_DAYS = 21    # 支窗口：超出纯日期容差后，只认支同/六合/六冲
                           # （地支 12 天一轮，窗口不设上限会与远距日期反复重影）

# ---------------------------------------------------------------- 口径语句（报分必附）
RANK_CALIBER = ("应期命中按六爻结构化候选**名次**判定（第 1 位为主应期）；"
                "本分数为现实回填命中，非古籍案例对齐分，不代表预测率。")
WINDOW_CALIBER = ("应期命中按**容差窗**判定（严格 ±"
                  f"{STRICT_WINDOW_DAYS} 天；宽松 ±{LOOSE_WINDOW_DAYS} 天，"
                  f"或 ±{BRANCH_WINDOW_DAYS} 天内支同/六合/六冲）；"
                  "本分数为现实回填命中，非古籍案例对齐分，不代表预测率。")

# ---------------------------------------------------------------- ① 名次制
# 名次 → 得分（主应期全分，越靠后越低；early 与 late 同档：均非命中）
RANK_SCORE: dict = {1: 1.0, 2: 0.8, 3: 0.7, 4: 0.55,
                    "late": 0.35, "early": 0.35, "overrun": 0.0}
RANK_LABEL: dict = {
    (1, "hit"): "主应期命中",
    (2, "hit"): "次应期命中(第2位)",
    (3, "hit"): "第3位命中",
    (4, "hit"): "第4位命中",
    ("late", "hit"): "命中但名次靠后",
    ("early", None): "提前于全部候选",
    ("overrun", None): "超期未验",
}

_HE_SET = {frozenset(p) for p in HE_PAIRS}
_CHONG_SET = {frozenset(p) for p in CHONG_PAIRS}


def parse_date(text) -> date | None:
    """宽松解析 `YYYY-MM-DD`；不可解析返回 None（不抛）。"""
    try:
        return date.fromisoformat(str(text).strip()[:10])
    except (ValueError, TypeError):
        return None


def branch_of(date_str: str) -> str | None:
    """`YYYY-MM-DD` → 当日地支。**复用内核干支历**（不另立锚点、不另立支表）。"""
    d = parse_date(date_str)
    if d is None:
        return None
    return EARTHLY_BRANCHES[day_ganzhi_index(d) % 12]


def branches_relate(a: str, b: str) -> bool:
    """两个地支是否「同 / 六合 / 六冲」（六爻应期直读法）。"""
    if not a or not b:
        return False
    return a == b or frozenset((a, b)) in _HE_SET or frozenset((a, b)) in _CHONG_SET


def rate(hit: int, n: int) -> float | None:
    """命中率（百分数，一位小数）；分母为 0 返回 None（不给 0%，那是「无数」）。"""
    return round(hit * 100.0 / n, 1) if n else None


def judge_rank(offered: list[dict], occurred: str | None) -> dict | None:
    """名次制单例判定。候选/日期不全返回 None（不评，也不进分母）。

    `offered` = `[{"date": "YYYY-MM-DD", "rule": "..."}, ...]`，**顺序即名次**。
    """
    if not occurred:
        return None
    obs = parse_date(occurred)
    if obs is None:
        return {"可评": False, "判定": "occurred_at 无效", "命中": False}
    dates: list[str] = []
    for it in offered or []:
        d = str(it.get("date") or "")
        if d and d not in dates:
            dates.append(d)
    if not dates:
        return None  # 该卦未给结构化候选（如仅支级应期）→ 不评
    valid = [(d, parse_date(d)) for d in dates]
    valid = [(d, d0) for d, d0 in valid if d0 is not None]
    if not valid:
        return {"可评": False, "判定": "候选日期无效", "命中": False}

    hit = next((i for i, (_, d0) in enumerate(valid) if d0 == obs), None)
    if hit is not None:
        rank = hit + 1
        label = RANK_LABEL.get((rank, "hit")) or "命中但名次靠后"
        return {"可评": True, "命中": True, "名次": rank,
                "得分": RANK_SCORE.get(rank, RANK_SCORE["late"]),
                "判定": label, "rule": (offered[hit].get("rule") or "")}
    earliest, latest = valid[0][1], valid[-1][1]
    if obs < earliest:
        return {"可评": True, "命中": False, "名次": None, "得分": RANK_SCORE["early"],
                "判定": "提前于全部候选", "rule": (offered[0].get("rule") or "")}
    if obs > latest:
        return {"可评": True, "命中": False, "名次": None, "得分": RANK_SCORE["overrun"],
                "判定": f"超期（末位候选 {latest}）", "rule": ""}
    return {"可评": True, "命中": False, "名次": None, "得分": RANK_SCORE["late"],
            "判定": "候选窗口内但日期未对齐", "rule": ""}


def judge_window(predicted: list[str], occurred: str | None) -> dict:
    """容差窗单例判定 → `{"hit_strict": bool, "hit_loose": bool}`。

    缺实际日期 / 缺预测日 / 日期非法 → 双 False（不命中，也不谎报命中）。
    """
    out = {"hit_strict": False, "hit_loose": False}
    if not predicted or not occurred:
        return out
    actual_dt = parse_date(occurred)
    if actual_dt is None:
        return out
    actual_branch = branch_of(occurred)
    for p in predicted:
        p_dt = parse_date(p)
        if p_dt is None:
            continue
        delta = abs((actual_dt - p_dt).days)
        if delta <= STRICT_WINDOW_DAYS:
            return {"hit_strict": True, "hit_loose": True}
        if delta <= LOOSE_WINDOW_DAYS:
            out["hit_loose"] = True
        elif delta <= BRANCH_WINDOW_DAYS and branches_relate(actual_branch, branch_of(p)):
            out["hit_loose"] = True
    return out
