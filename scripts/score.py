#!/usr/bin/env python3
"""
六爻古籍案例评分系统
用法：python score.py --case-id ZS001 --engine-output '{"verdict":"吉",...}'
说明：将排盘结果与案例库中的expected对比，输出0-100分的得分。
"""
import argparse
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
CASES_FILE = SKILL_DIR / "data" / "cases" / "classical_cases.json"

# 评分标准：吉/凶方向一致性、用神正确性、关键格局识别、应期方向
WEIGHTS = {
    "verdict_match": 0.35,       # 吉凶判断正确
    "verdict_strength": 0.10,    # 凶中吉凶程度
    "use_god_correct": 0.20,     # 用神取法正确
    "key_pattern_id": 0.20,      # 关键格局识别
    "yingqi_direction": 0.15,    # 应期方向大致正确
}

# verdict映射表：将吉/凶/平映射为数值
VERDICT_MAP = {
    "大吉": 1.0, "吉": 0.8, "小吉": 0.7,
    "平/混合": 0.5, "平": 0.5, "中性": 0.5,
    "小凶": 0.3, "凶": 0.2, "大凶": 0.0,
    "下跌": 0.2, "不利": 0.3,
}


def score_case(case: dict, engine_output: dict) -> dict:
    """对单条案例评分"""
    expected = case["expected"]
    scores = {}
    details = []
    
    # 1. 吉凶判断
    exp_verdict_cn = expected["verdict"]
    eng_verdict = engine_output.get("verdict", "")
    
    exp_score = VERDICT_MAP.get(exp_verdict_cn, 0.5)
    eng_score = VERDICT_MAP.get(eng_verdict, 0.5)
    verdict_diff = abs(exp_score - eng_score)
    verdict_accuracy = max(0, 1 - verdict_diff * 2)  # 完全相反=0，完全相同=1
    scores["verdict_match"] = verdict_accuracy * WEIGHTS["verdict_match"]
    
    details.append(f"吉凶: 期望={exp_verdict_cn}({exp_score}), 实际={eng_verdict}({eng_score}), 准确率={verdict_accuracy:.2f}")
    
    # 2. 用神正确性
    exp_use_god = expected.get("use_god", "")
    eng_use_god = engine_output.get("use_god_category", "")
    
    if exp_use_god and eng_use_god:
        use_god_ok = (exp_use_god == eng_use_god)
        scores["use_god_correct"] = WEIGHTS["use_god_correct"] if use_god_ok else 0
        details.append(f"用神: 期望={exp_use_god}, 实际={eng_use_god}, {'✓' if use_god_ok else '✗'}")
    else:
        scores["use_god_correct"] = WEIGHTS["use_god_correct"] * 0.5  # 部分得分
        details.append(f"用神: 不确定")
    
    # 3. 关键格局识别
    exp_keys = expected.get("key_points", [])
    eng_reasoning = " ".join([str(r) for r in engine_output.get("reasoning_chain", [])])
    eng_reasoning += engine_output.get("verdict_desc", "")
    
    if exp_keys:
        matched = sum(1 for k in exp_keys if any(kw in eng_reasoning for kw in [k[:4]]))
        key_accuracy = matched / len(exp_keys)
        scores["key_pattern_id"] = key_accuracy * WEIGHTS["key_pattern_id"]
        details.append(f"格局识别: {matched}/{len(exp_keys)} 关键点评分到, 准确率={key_accuracy:.2f}")
    else:
        scores["key_pattern_id"] = WEIGHTS["key_pattern_id"] * 0.5
    
    # 4. 应期方向（匹配即可，允许误差）
    exp_yingqi = expected.get("yingqi", "")
    eng_yingqi = engine_output.get("yingqi_summary", "")
    
    if exp_yingqi and eng_yingqi:
        # 包含性匹配
        yingqi_ok = any(k in eng_yingqi for k in [exp_yingqi[:3], exp_yingqi[:2]])
        scores["yingqi_direction"] = WEIGHTS["yingqi_direction"] if yingqi_ok else WEIGHTS["yingqi_direction"] * 0.3
        details.append(f"应期: 期望={exp_yingqi}, 实际方向={'✓' if yingqi_ok else '✗'}")
    else:
        scores["yingqi_direction"] = WEIGHTS["yingqi_direction"] * 0.5
    
    # 5. 综合加分：composite_score方向与verdict一致
    composite = engine_output.get("composite_score", 0)
    if isinstance(composite, (int, float)):
        # 正分应与吉对应，负分应与凶对应
        score_sign = 1 if composite > 0 else (-1 if composite < 0 else 0)
        verdict_sign = 1 if eng_score > 0.5 else (-1 if eng_score < 0.5 else 0)
        if score_sign == verdict_sign:
            scores["verdict_strength"] = WEIGHTS["verdict_strength"]
            details.append(f"分数方向: 复合分={composite:.2f} 与 verdict={eng_verdict} 一致 ✓")
        else:
            scores["verdict_strength"] = 0
            details.append(f"分数方向: 复合分={composite:.2f} 与 verdict={eng_verdict} 矛盾 ✗")
    else:
        scores["verdict_strength"] = 0
    
    # 计算总分
    total_score = sum(scores.values()) * 100  # 转换为百分制
    
    return {
        "case_id": case["id"],
        "question": case["question"],
        "source": case["source"],
        "total_score": round(total_score, 1),
        "max_possible": 100,
        "scores": {k: round(v * 100, 2) for k, v in scores.items()},
        "details": details,
        "engine_verdict": eng_verdict,
        "expected_verdict": exp_verdict_cn,
    }


def load_cases():
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_case(case_id: str) -> dict:
    data = load_cases()
    for c in data["cases"]:
        if c["id"] == case_id:
            return c
    return None


def main():
    parser = argparse.ArgumentParser(description="六爻案例评分系统")
    parser.add_argument("--case-id", type=str, required=True)
    parser.add_argument("--engine-output", type=str, help="JSON格式的排盘结果")
    parser.add_argument("--engine-output-file", type=str, help="排盘结果JSON文件路径")
    args = parser.parse_args()
    
    case = get_case(args.case_id)
    if not case:
        print(f"✗ 案例 {args.case_id} 未找到")
        sys.exit(1)
    
    # 加载engine output
    if args.engine_output_file:
        with open(args.engine_output_file, "r", encoding="utf-8") as f:
            engine_output = json.load(f)
    elif args.engine_output:
        try:
            engine_output = json.loads(args.engine_output)
        except json.JSONDecodeError:
            print(f"✗ engine_output JSON解析失败")
            sys.exit(1)
    else:
        print("✗ 需要 --engine-output 或 --engine-output-file")
        sys.exit(1)
    
    # 评分
    result = score_case(case, engine_output)
    
    print(f"=== 案例 {args.case_id} 评分结果 ===")
    print(f"题: {result['question'][:50]}")
    print(f"来源: {result['source']}")
    print(f"总分: {result['total_score']:.1f} / 100")
    print(f"吉凶: 期望={result['expected_verdict']}, 实际={result['engine_verdict']}")
    print()
    for d in result["details"]:
        print(f"  {d}")
    print()
    print("分项得分：")
    for k, v in result["scores"].items():
        weight = WEIGHTS.get(k, 0)
        print(f"  {k:25s}: {v:6.2f} (权重{weight:.0%})")


if __name__ == "__main__":
    main()
