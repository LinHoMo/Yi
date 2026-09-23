# -*- coding: utf-8 -*-
"""六爻纳甲引擎：数据表 / 干支历与真太阳时 / 排盘核心 / 文本输出 / 历史遗留梅花与批量接口。（拆分自 liuyao_engine.py，纯搬移不改逻辑；聚合入口见 liuyao_engine.py）。"""

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel, kernel_dir

_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    ADVANCE_PAIRS,
    BRANCH_ELEMENTS,
    BREAK_PAIRS,
    CHONG_PAIRS,
    EARTHLY_BRANCHES,
    EIGHT_PALACES,
    BAGUA_LINES,
    HEAVENLY_STEMS,
    HEXAGRAM_TRIGRAMS,
    HE_PAIRS,
    KE_CYCLE,
    NAJIA_BRANCHES,
    RETREAT_PAIRS,
    SHENG_CYCLE,
    STEM_ELEMENTS,
    TOMB_MAP,
)

from yishu_core.najia import najia_branch  # noqa: E402

import argparse

import json

import math

import os

import random

import sys

from datetime import datetime, timedelta

from pathlib import Path

from yishu_core.runtime import force_utf8_stdio as _force_utf8_stdio  # noqa: E402

from engine_chart import build_hexagram_result, coin_toss, number_based_hexagram, time_based_hexagram
from engine_tables import HEXAGRAMS

def mei_hua_divination(question: str, year: int, month: int, day: int,
                        hour: int, number: int = None) -> dict:
    """
    梅花易数起卦互参。

    先天八卦数（先天八卦，伏羲八卦序）：
    1=乾  2=兑  3=离  4=震  5=巽  6=坎  7=艮  8=坤

    规则：
    - 上卦 = (年 + 月 + 日) mod 8
    - 下卦 = (年 + 月 + 日 + 时) mod 8
    - 动爻 = (年 + 月 + 日 + 时) mod 6 + 1

    Body/Use 体用：
    - 动爻在下卦(1-3爻) → 上卦为体 下卦为用
    - 动爻在上卦(4-6爻) → 下卦为体 上卦为用
    - 体用五行生克定吉凶
    """
    trigram_map = {
        1: ("乾", "天", "金"), 2: ("兑", "泽", "金"),
        3: ("离", "火", "火"), 4: ("震", "雷", "木"),
        5: ("巽", "风", "木"), 6: ("坎", "水", "水"),
        7: ("艮", "山", "土"), 8: ("坤", "地", "土"),
    }

    # 也可选数字起卦
    if number is not None:
        upper_idx = number % 8
        lower_idx = (number + hour) % 8
        moving_yao = (number + hour) % 6 + 1
    else:
        upper_idx = (year + month + day) % 8
        lower_idx = (year + month + day + hour) % 8
        moving_yao = (year + month + day + hour) % 6 + 1

    # 将 0 映射到 8（坤）
    upper_idx = upper_idx if upper_idx > 0 else 8
    lower_idx = lower_idx if lower_idx > 0 else 8

    upper = trigram_map[upper_idx]
    lower = trigram_map[lower_idx]

    # 体用判断：有动爻的一方为用，无动的一方为体
    # 动爻 1-3 → 动在下卦 → 上卦为体，下卦为用
    # 动爻 4-6 → 动在上卦 → 下卦为体，上卦为用
    if moving_yao <= 3:
        body, use = upper, lower
    else:
        body, use = lower, upper

    body_elem = body[2]
    use_elem = use[2]

    # 五行相生（Sheng）：木→火→土→金→水→木
    SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    # 五行相克（Ke）：木→土→水→火→金→木
    KE = {"木": "土", "火": "金", "土": "水", "水": "火", "金": "木"}

    if body_elem == use_elem:
        interaction = "比和"      # 大吉
        score = 3.5
    elif SHENG.get(body_elem) == use_elem:
        interaction = "体生用"    # 泄气
        score = 2.0
    elif SHENG.get(use_elem) == body_elem:
        interaction = "用生体"    # 进气大吉
        score = 4.0
    elif KE.get(body_elem) == use_elem:
        interaction = "体克用"    # 可控
        score = 2.5
    else:
        interaction = "用克体"    # 大凶
        score = 0.5

    # 动爻所在卦
    moving_in_lower = (moving_yao <= 3)

    return {
        "method": "梅花易数",
        "upper_hexagram": upper[0],
        "lower_hexagram": lower[0],
        "upper_nature": upper[1],
        "lower_nature": lower[1],
        "full_hexagram": f"{upper[0]}上{lower[0]}下",
        "moving_yao": moving_yao,
        "moving_in_lower": moving_in_lower,
        "body": body[0],
        "use": use[0],
        "body_element": body_elem,
        "use_element": use_elem,
        "interaction": interaction,
        "score": score,
        "interpretation": (
            f"{body[0]}({body_elem})为体，{use[0]}({use_elem})为用，"
            f"体用{interaction}"
        ),
        "auspicious": score >= 3.0,
        "details": {
            "upper_trigram": {"name": upper[0], "element": upper[2]},
            "lower_trigram": {"name": lower[0], "element": lower[2]},
            "moving_yao_position": moving_yao,
            "moving_in_lower_trigram": moving_in_lower,
        },
    }


def mei_hua_cross_reference(question: str, year: int, month: int, day: int,
                             hour: int) -> dict:
    """
    梅花易数 + 六爻互参。

    同时起：
    1. 六爻卦（铜钱摇卦/时间起卦）
    2. 梅花易数卦（时间/数字起卦）

    然后交叉验证两个体系的一致性。
    """
    # 六爻起卦 — 用时间起卦
    liuyao_yao_values = time_based_hexagram(year, month, day, hour)
    liuyao_result = build_hexagram_result(
        liuyao_yao_values, question, "时间起卦(六爻)",
        year, month, day, hour
    )

    # 运行思维链
    liuyao_chain = None
    try:
        from thinking_chain import run_thinking_chain
        chain_result = run_thinking_chain(liuyao_result)
        liuyao_chain = chain_result.get("thinking_chain", chain_result)
    except ImportError:
        pass

    # 梅花起卦
    mei_hua_result = mei_hua_divination(question, year, month, day, hour)

    # 交叉验证
    cross_checks = []

    # 比较两卦的 吉凶方向
    liuyao_score = None
    liuyao_verdict = ""
    if liuyao_chain:
        s5 = liuyao_chain.get("step5_synthesis", {})
        liuyao_score = s5.get("final_score", 2.5)
        liuyao_verdict = s5.get("verdict", "")

    mei_hua_score = mei_hua_result.get("score", 2.5)

    # 判定方向是否一致
    liuyao_favorable = liuyao_score >= 2.5 if liuyao_score is not None else True
    mei_hua_favorable = mei_hua_score >= 3.0

    if liuyao_favorable == mei_hua_favorable:
        cross_checks.append({
            "check": "吉凶方向一致性",
            "result": "一致",
            "detail": f"六爻{'吉' if liuyao_favorable else '凶'}向，梅花{'吉' if mei_hua_favorable else '凶'}向",
        })
    else:
        cross_checks.append({
            "check": "吉凶方向一致性",
            "result": "矛盾",
            "detail": f"六爻{'吉' if liuyao_favorable else '凶'}向，梅花{'吉' if mei_hua_favorable else '凶'}向 — 需审慎解读",
        })

    # 五行元素共振
    liuyao_element = liuyao_result.get("original_hexagram", {}).get("palace_element", "")
    mei_hua_body_elem = mei_hua_result.get("body_element", "")
    mei_hua_use_elem = mei_hua_result.get("use_element", "")

    if liuyao_element and liuyao_element in (mei_hua_body_elem, mei_hua_use_elem):
        cross_checks.append({
            "check": "五行元素共振",
            "result": "共振",
            "detail": f"六爻宫五行({liuyao_element})与梅花体/用五行({mei_hua_body_elem}/{mei_hua_use_elem})共振",
        })
    else:
        cross_checks.append({
            "check": "五行元素共振",
            "result": "无显著共振",
            "detail": f"六爻宫五行({liuyao_element})，梅花体用五行({mei_hua_body_elem}/{mei_hua_use_elem})",
        })

    # 综合判断
    agree_count = sum(1 for c in cross_checks if c["result"] in ("一致", "共振"))
    total_checks = len(cross_checks)
    confidence = agree_count / total_checks if total_checks > 0 else 0.5

    return {
        "mode": "梅花易数互参",
        "liuyao_result": liuyao_result,
        "mei_hua_result": mei_hua_result,
        "thinking_chain": liuyao_chain,
        "cross_checks": cross_checks,
        "cross_confidence": confidence,
        "summary": (
            f"六爻卦：{liuyao_result['original_hexagram']['name']}"
            f"（{liuyao_verdict}，评分{liuyao_score:.2f}）；"
            f"梅花卦：{mei_hua_result['full_hexagram']}"
            f"（{mei_hua_result['interaction']}，评分{mei_hua_score:.2f}）；"
            f"交叉验证置信度{confidence:.0%}"
        ),
    }


def batch_divination(question: str, n: int = 10, method: str = "time",
                     year: int = None, month: int = None, day: int = None,
                     hour: int = None, seed: int = None) -> dict:
    """
    批量演卦对比。

    生成 N 个卦（使用不同种子或时间扰动），积累统计信息：
    - 吉凶分布
    - 平均评分
    - 最常见卦
    - 卦体多样性
    """
    from collections import Counter
    from datetime import datetime

    if year is None:
        now = datetime.now()
        year, month, day, hour = now.year, now.month, now.day, now.hour

    results = []
    rng = random.Random(seed) if seed is not None else random.Random()

    for i in range(n):
        # 对铜钱模式用不同种子；对时间模式加了分钟/秒扰动
        if method == "coin":
            sub_rng = random.Random(seed + i if seed is not None else rng.randint(0, 999999))
            yao_values = coin_toss(random_gen=sub_rng)
            m = "铜钱摇卦"
        elif method == "number":
            a = rng.randint(1, 1000)
            b = rng.randint(1, 1000)
            c = rng.randint(1, 6)
            yao_values = number_based_hexagram(a, b, c)
            m = f"数字起卦({a},{b},{c})"
        else:
            # 时间起卦 + i 秒扰动（模拟不同时刻起卦）
            yao_values = time_based_hexagram(year, month, day, hour)
            m = "时间起卦"

        result = build_hexagram_result(
            yao_values, question, m, year, month, day, hour
        )

        # 运行思维链
        try:
            from thinking_chain import run_thinking_chain
            chain_full = run_thinking_chain(result)
            chain = chain_full.get("thinking_chain", chain_full)
        except ImportError:
            chain = None

        s5 = chain.get("step5_synthesis", {}) if chain else {}
        verdict = s5.get("verdict", "待定")
        fscore = s5.get("final_score", 2.5)
        hex_name = result["original_hexagram"]["name"]

        results.append({
            "index": i + 1,
            "hexagram": hex_name,
            "verdict": verdict,
            "score": fscore,
            "method": m,
            "result": result,
            "thinking_chain": chain,
        })

    # 统计
    verdicts = [r["verdict"] for r in results]
    scores = [r["score"] for r in results]
    hexagrams = [r["hexagram"] for r in results]
    hex_counts = Counter(hexagrams)

    # 吉凶分布（基于 verdict 字段）
    dist_auspicious = sum(1 for v in verdicts if "吉" in v and "凶" not in v)
    dist_inauspicious = sum(1 for v in verdicts if "凶" in v and "吉" not in v)
    dist_mixed = sum(1 for v in verdicts if "平" in v or ("吉" in v and "凶" in v))

    # 平均评分
    avg_score = sum(scores) / len(scores) if scores else 0.0
    min_score = min(scores) if scores else 0.0
    max_score = max(scores) if scores else 0.0

    # 最常见卦
    most_common = hex_counts.most_common(1)[0] if hex_counts else None

    # 卦体多样性
    diversity = len(hex_counts)

    # 稳定性：同一卦出现 N 次以上为稳定
    stability_threshold = max(2, n // 3)  # 至少出现 n/3 次视为稳定
    stable_hex = [(h, c) for h, c in hex_counts.items() if c >= stability_threshold]
    is_stable = len(stable_hex) > 0 and stable_hex[0][1] >= stability_threshold

    return {
        "mode": "批量演卦对比",
        "n": n,
        "question": question,
        "verdict_distribution": {
            "吉": dist_auspicious,
            "凶": dist_inauspicious,
            "平/混合": dist_mixed,
        },
        "score_statistics": {
            "mean": round(avg_score, 3),
            "min": round(min_score, 3),
            "max": round(max_score, 3),
            "range": round(max_score - min_score, 3),
        },
        "most_common_hexagram": {
            "name": most_common[0],
            "count": most_common[1],
            "percentage": round(most_common[1] / n * 100, 1),
        } if most_common else None,
        "hexagram_diversity": diversity,
        "total_hexagrams": len(HEXAGRAMS),
        "diversity_ratio": round(diversity / n, 3),
        "is_stable": is_stable,
        "stable_hexagrams": [
            {"name": h, "count": c} for h, c in sorted(stable_hex, key=lambda x: -x[1])
        ],
        "hexagram_frequency": hex_counts.most_common(),
        "individual_results": results,
        "summary": (
            f"共演{n}卦：吉{dist_auspicious}、凶{dist_inauspicious}、平{dist_mixed}；"
            f"均分{avg_score:.2f}（{min_score:.2f}~{max_score:.2f}）；"
            f"出现{diversity}种不同卦；"
            + (f"最频为{most_common[0]}（{most_common[1]}次）" if most_common else "")
            + (f"，卦象{'稳定' if is_stable else '不稳定'}"
              if is_stable else "")
        ),
    }


def _format_mei_hua_text(cross_result: dict) -> str:
    """将梅花易数互参结果格式化为可读文本。"""
    lines = []
    W = 52
    lines.append("=" * W)
    lines.append("梅花易数 · 六爻互参报告".center(W))
    lines.append("=" * W)
    lines.append("")

    # 梅花结果
    mh = cross_result.get("mei_hua_result", {})
    if mh:
        lines.append("【梅花易数卦】")
        lines.append(f"  卦　象：{mh.get('full_hexagram', '?')}")
        lines.append(f"　上卦：{mh.get('upper_hexagram', '?')}"
                     f"({mh.get('details', {}).get('upper_trigram', {}).get('element', '?')})")
        lines.append(f"　下卦：{mh.get('lower_hexagram', '?')}"
                     f"（{mh.get('details', {}).get('lower_trigram', {}).get('element', '?')}）")
        lines.append(f"　动爻：第{mh.get('moving_yao', '?')}爻"
                     f"（{'下卦' if mh.get('moving_in_lower') else '上卦'}）")
        lines.append(f"　体　用：{mh.get('body', '?')}({mh.get('body_element', '?')})"
                     f"为体，{mh.get('use', '?')}({mh.get('use_element', '?')})为用")
        lines.append(f"　关　系：{mh.get('interaction', '?')}（评分 {mh.get('score', 0):.2f}）")
        lines.append("")

    # 六爻结果
    lr = cross_result.get("liuyao_result", {})
    if lr:
        oh = lr.get("original_hexagram", {})
        ch = lr.get("changed_hexagram")
        lines.append("【六爻卦】")
        lines.append(f"　本卦：{oh.get('name', '?')}　"
                     f"{oh.get('upper_trigram', '?')}上{oh.get('lower_trigram', '?')}下")
        lines.append(f"　宫　位：{oh.get('palace', '?')}宫（{oh.get('palace_element', '?')}行）")
        if ch:
            lines.append(f"　变卦：{ch.get('name', '?')}　"
                         f"动爻 第{', '.join(str(n) for n in ch.get('changed_lines', []))}爻")
        lines.append("")

    # 交叉验证
    cross_checks = cross_result.get("cross_checks", [])
    confidence = cross_result.get("cross_confidence", 0)
    if cross_checks:
        lines.append("─" * W)
        lines.append("【交叉验证】")
        for cc in cross_checks:
            mark = "OK" if cc.get("result") in ("一致", "共振") else "!!"
            lines.append(f"  [{mark}] {cc.get('check', '?')}：{cc.get('detail', '')}")
        lines.append(f"　置信度：{confidence:.0%}")
        lines.append("")

    summary = cross_result.get("summary", "")
    if summary:
        lines.append("─" * W)
        lines.append(f"　{summary}")
        lines.append("")
    lines.append("=" * W)
    return "\n".join(lines)


def _check_batch_mode(args):
    """执行批量演卦模式。"""
    from datetime import datetime

    # 确定时间
    if args.datetime:
        dt = datetime.strptime(args.datetime, "%Y-%m-%d %H:%M")
        year, month, day, hour = dt.year, dt.month, dt.day, dt.hour
    else:
        now = datetime.now()
        year, month, day, hour = now.year, now.month, now.day, now.hour

    if args.hour is not None:
        hour = args.hour

    # 决定批量起卦方法
    method = args.mode if args.mode in ("coin", "number") else "coin"

    batch_result = batch_divination(
        question=args.question,
        n=args.batch,
        method=method,
        year=year, month=month, day=day, hour=hour,
        seed=args.seed,
    )

    output_format = args.format if args.format is not None else args.output
    if output_format == "json":
        print(json.dumps(batch_result, ensure_ascii=False, indent=2, default=str))
    else:
        print(_format_batch_text(batch_result))


def _identify_use_god(yao_lines: list, hints: list) -> tuple:
    """从建卦结果中识别用神六亲及对应爻位置。

    返回 ``(relation, position, branch)``，找不到则返回 ``(None, 0, "")``。
    """
    # 先从 hints 中提取六亲名
    target_relation = None
    for hint in hints:
        for rel in ["妻财", "官鬼", "父母", "子孙", "兄弟"]:
            if f"取{rel}" in hint:
                target_relation = rel
                break
        if target_relation:
            break
    if not target_relation:
        # 默认取妻财（通用问财运/结果）
        target_relation = "子孙"

    for y in yao_lines:
        if y["six_relation"] == target_relation:
            return target_relation, y["position"], y["earthly_branch"]
    # fallback: return first line info
    if yao_lines:
        y = yao_lines[0]
        return y["six_relation"], y["position"], y["earthly_branch"]
    return None, 0, ""


def _find_decisive_yao(yao_lines: list) -> dict:
    """找出最具影响力的单爻：优先取动爻，若无动爻则取世爻。"""
    moving = [y for y in yao_lines if y["is_moving"]]
    if moving:
        return moving[0]
    world = [y for y in yao_lines if y["is_world"]]
    if world:
        return world[0]
    return yao_lines[0] if yao_lines else {}


def _compute_quick_score(yao_lines: list, hints: list, day_branch: str) -> int:
    """简化的评分逻辑（0–100）。

    规则：
    - 基础分 65
    - 用神不空 +8
    - 用神非月破 +5
    - 有动爻且原神明动 +10
    - 忌神明动克用神 -12
    - 用神临日支 +7
    """
    score = 65

    relation, pos, branch = _identify_use_god(yao_lines, hints)
    if not relation:
        return score

    target = None
    for y in yao_lines:
        if y["six_relation"] == relation:
            target = y
            break
    if not target:
        return score

    # 旬空检查
    if not target.get("is_empty", False):
        score += 8

    # 原神（生用神之六亲 = 父母）暗中生
    # 忌神（克用神之六亲 = 官鬼/子孙等）明动克
    sheng_relation = None
    for r in ["父母", "兄弟", "子孙", "妻财", "官鬼"]:
        pass
    # 简化的生克：用神的五行 → 生我者（父母）为原神
    # 根据六亲反推：用神为妻财→原神为子孙；用神为官鬼→原神为妻财...
    yuan_map = {
        "妻财": "子孙",
        "官鬼": "妻财",
        "父母": "官鬼",
        "子孙": "兄弟",
        "兄弟": "父母",
    }
    ji_map = {
        "妻财": "兄弟",
        "官鬼": "子孙",
        "父母": "妻财",
        "子孙": "官鬼",
        "兄弟": "父母",
    }
    yuan_rel = yuan_map.get(relation, "")
    ji_rel = ji_map.get(relation, "")

    for y in yao_lines:
        if y["is_moving"]:
            if y["six_relation"] == yuan_rel:
                score += 10
            elif y["six_relation"] == ji_rel:
                score -= 12
            elif y["six_relation"] == relation:
                # 用神自身动：阴阳转变，力量增强
                score += 5

    # 日支临值
    if branch == day_branch:
        score += 7

    return max(30, min(95, score))


def _score_to_verdict(score: int) -> str:
    """分数转断语简词。"""
    if score >= 85:
        return "大吉"
    elif score >= 75:
        return "吉"
    elif score >= 65:
        return "中平"
    elif score >= 55:
        return "需审慎"
    elif score >= 45:
        return "艰难"
    else:
        return "不利"


def _verdict_to_action(verdict: str) -> str:
    """断语转建议行动项。"""
    actions = {
        "大吉": "顺势而为，果断行动，勿失良机",
        "吉": "稳步推进，保持当前方向",
        "中平": "量力而行，静观其变",
        "需审慎": "三思后行，避免冲动决策",
        "艰难": "守静为上，退一步海阔天空",
        "不利": "停止当前计划，重新审视局势",
    }
    return actions.get(verdict, "细察形势，因时而动")


def quick_reading(question: str, year: int, month: int, day: int, hour: int,
                  method: str = "coin") -> str:
    """直觉速读 — 200字以内的即时解读。

    流程：起卦 → 定用神 → 找关键动爻 → 单句断语。
    """
    # 1. 起卦
    if method == "time":
        yao_values = time_based_hexagram(year, month, day, hour)
        method_str = "时间起卦"
    elif method == "number":
        # 默认随机数字起卦
        import random
        random.seed()
        a, b, c = random.randint(1, 100), random.randint(1, 100), random.randint(1, 100)
        yao_values = number_based_hexagram(a, b, c)
        method_str = "数字起卦"
    else:
        yao_values = coin_toss()
        method_str = "铜钱摇卦"

    # 2. 建卦
    result = build_hexagram_result(
        yao_values, question, method_str, year, month, day, hour
    )
    oh = result["original_hexagram"]
    yao_lines = oh["yao_lines"]
    hints = result["analysis_hints"]["possible_use_gods"]
    day_branch = result["divination_time"]["day_stem_branch"]

    # 3. 用神 + 关键爻
    relation, pos, branch = _identify_use_god(yao_lines, hints)
    decisive = _find_decisive_yao(yao_lines)
    decisive_text = decisive.get("line_text", "")
    moving_count = sum(1 for y in yao_lines if y["is_moving"])

    # 4. 评分
    score = _compute_quick_score(yao_lines, hints, day_branch[1] if len(day_branch) > 1 else "")
    verdict = _score_to_verdict(score)
    action = _verdict_to_action(verdict)

    # 5. 单句原因
    hex_name = oh["name"]
    if decisive_text and decisive.get("is_moving"):
        one_line = f"第{decisive['position']}爻动「{decisive_text}」"
    elif moving_count == 0:
        one_line = f"{hex_name}静卦，以世爻断之"
    else:
        one_line = f"{hex_name}卦动爻 {moving_count} 个，{verdict}之象"

    return (
        f"【{question}】\n"
        f"{verdict}（{score}分）\n"
        f"{one_line}\n"
        f"建议：{action}"
    )


def single_yao_judgment(question: str, year: int, month: int, day: int, hour: int,
                        yao_values: list = None) -> str:
    """单爻断法 — 仅当只有一个动爻时生效。

    若无动爻或多动爻，回退到 :func:`quick_reading`。
    """
    # 起卦（若未提供爻值）
    if yao_values is None:
        yao_values = coin_toss()

    result = build_hexagram_result(
        yao_values, question, "单爻断法", year, month, day, hour
    )
    oh = result["original_hexagram"]
    hex_name = oh["name"]
    yao_lines = oh["yao_lines"]
    moving = [y for y in yao_lines if y["is_moving"]]

    if len(moving) != 1:
        # 回退到速读
        return quick_reading(question, year, month, day, hour)

    line = moving[0]
    line_text = line.get("line_text", "（爻辞缺失）")
    line_pos = line["position"]
    line_name = line.get("name", f"第{line_pos}爻")
    line_relation = line["six_relation"]
    line_branch = line["earthly_branch"]
    line_spirit = line["six_spirit"]

    # 位置解读
    pos_meanings = {
        1: "初爻动，事在萌发，吉凶初现端倪",
        2: "二爻动，得中道，多主和合顺利",
        3: "三爻动，事多凶悔，进退两难之际",
        4: "四爻动，近君位惧，宜慎言慎行",
        5: "五爻动，居尊决断，大事将定",
        6: "上爻动，事物至极，盛极则衰",
    }
    pos_meaning = pos_meanings.get(line_pos, "动爻所示，细察爻辞")

    # 现代白话
    modern_interp = (
        f"此第{line_pos}爻动，时当{'初起' if line_pos <= 2 else '转折' if line_pos <= 4 else '极变'}之时。"
        f"爻辞所言{line_text}，{pos_meaning}。"
    )

    return (
        f"【单爻断法 · {question}】\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"本卦：{hex_name}（{oh.get('judgment', '')}）\n"
        f"动爻：第{line_pos}爻（{line_name}）{line_relation}·{line_branch}\n"
        f"六神：{line_spirit}\n"
        f"\n"
        f"爻辞：「{line_text}」\n"
        f"\n"
        f"断曰：{pos_meaning}\n"
        f"\n"
        f"今译：{modern_interp}\n"
        f"\n"
        f"决：细玩爻辞之义，循之以行，得失自明。\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def _format_batch_text(batch_result: dict) -> str:
    """将批量演卦结果格式化为可读文本。"""
    lines = []
    W = 60
    lines.append("=" * W)
    lines.append("批量演卦对比报告".center(W))
    lines.append("=" * W)
    lines.append(f"　问　题：{batch_result.get('question', '?')}")
    lines.append(f"　总　数：{batch_result.get('n', 0)} 卦")
    lines.append("")

    dist = batch_result.get("verdict_distribution", {})
    lines.append("─" * W)
    lines.append("【吉凶分布】")
    lines.append(f"　吉：{dist.get('吉', 0)}　　"
                 f"凶：{dist.get('凶', 0)}　　"
                 f"平/混合：{dist.get('平/混合', 0)}")
    lines.append("")

    score = batch_result.get("score_statistics", {})
    lines.append("【评分统计】")
    lines.append(f"　均值：{score.get('mean', 0):.3f}　"
                 f"最低：{score.get('min', 0):.3f}　"
                 f"最高：{score.get('max', 0):.3f}　"
                 f"极差：{score.get('range', 0):.3f}")
    lines.append("")

    mch = batch_result.get("most_common_hexagram")
    lines.append("【卦体统计】")
    if mch:
        lines.append(f"　最常见卦：{mch.get('name', '?')}（{mch.get('count', 0)}次，"
                     f"{mch.get('percentage', 0):.1f}%）")
    lines.append(f"　卦体多样性：{batch_result.get('hexagram_diversity', 0)} 种不同卦"
                 f"（共 {batch_result.get('total_hexagrams', 64)} 卦）")
    lines.append(f"　多样性比：{batch_result.get('diversity_ratio', 0):.3f}")
    lines.append(f"　稳　定　性：{'稳定' if batch_result.get('is_stable') else '不稳定'}")

    stable = batch_result.get("stable_hexagrams", [])
    if stable:
        lines.append("　稳定卦象：")
        for sh in stable:
            lines.append(f"　　· {sh.get('name', '?')}（{sh.get('count', 0)}次）")

    # 频率表
    hf = batch_result.get("hexagram_frequency", [])
    if hf:
        lines.append("　频率表（前10）：")
        for h_name, h_count in hf[:10]:
            pct = h_count / batch_result.get("n", 1) * 100
            lines.append(f"　　· {h_name}：{h_count}次 ({pct:.1f}%)")
    lines.append("")

    summary = batch_result.get("summary", "")
    if summary:
        lines.append("─" * W)
        lines.append(f"　{summary}")
    lines.append("")
    lines.append("=" * W)
    return "\n".join(lines)


def _check_verify_mode(args):
    """执行反幻觉校验模式。"""
    # 读取引擎结果
    engine_result = None
    if args.engine_result:
        with open(args.engine_result, "r", encoding="utf-8") as f:
            engine_result = json.load(f)
    else:
        # 先用指定 mode 起一卦
        from datetime import datetime
        if args.datetime:
            dt = datetime.strptime(args.datetime, "%Y-%m-%d %H:%M")
            year, month, day, hour = dt.year, dt.month, dt.day, dt.hour
        else:
            now = datetime.now()
            year, month, day, hour = now.year, now.month, now.day, now.hour

        if args.mode == "coin":
            yao_values = coin_toss()
            method = "铜钱摇卦"
        elif args.mode == "time":
            yao_values = time_based_hexagram(year, month, day, hour)
            method = "时间起卦"
        elif args.mode == "number" and args.numbers:
            nums = [int(x.strip()) for x in args.numbers.split(",")]
            yao_values = number_based_hexagram(nums[0], nums[1], nums[2])
            method = "数字起卦"
        elif args.mode == "manual" and args.yao:
            yao_values = [int(x.strip()) for x in args.yao.split(",")]
            method = "手动指定"
        else:
            yao_values = coin_toss()
            method = "铜钱摇卦(默认)"

        engine_result = build_hexagram_result(
            yao_values, args.question, method,
            year, month, day, hour
        )
        # 运行思维链
        try:
            from thinking_chain import run_thinking_chain
            chain_full = run_thinking_chain(engine_result)
            chain = chain_full.get("thinking_chain", chain_full)
            engine_result["thinking_chain"] = chain
        except ImportError:
            chain = None
            pass

    # 读取解读文本
    with open(args.verify, "r", encoding="utf-8") as f:
        interp_text = f.read()

    # 运行校验
    try:
        from hallucination_guard import verify_interpretation, generate_report
        checks = verify_interpretation(engine_result, interp_text)
        report = generate_report(checks)
    except ImportError:
        print("错误：hallucination_guard 模块未找到", file=sys.stderr)
        sys.exit(1)

    # 输出
    output_format = args.format if args.format is not None else args.output
    if output_format == "json":
        output = {
            "score": report.score,
            "risk_level": report.risk_level,
            "summary": report.summary,
            "checks": [
                {
                    "check_name": c.check_name,
                    "passed": c.passed,
                    "detail": c.detail,
                    "severity": c.severity,
                }
                for c in checks
            ],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print("六爻反幻觉校验报告".center(60))
        print("=" * 60)
        print(f"通过率：{report.score * 100:.0f}% "
              f"({sum(1 for c in checks if c.passed)}/{len(checks)})")
        print(f"风险等级：{report.risk_level}")
        print(f"总结：{report.summary}")
        print("-" * 60)
        for c in checks:
            mark = "PASS" if c.passed else "FAIL"
            print(f"  [{mark}/{c.severity}] {c.check_name}: {c.detail}")
        print("=" * 60)

