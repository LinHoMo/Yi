# -*- coding: utf-8 -*-
"""
自动校准工具 ——— 基于回归测试结果推荐评分参数调整。

分析哪些案例不准，推断可能的参数问题，给出具体的权重调整建议。

Usage:
    py -3.12 scripts/auto_calibrate.py                     # Analyze and recommend
    py -3.12 scripts/auto_calibrate.py --apply             # Apply recommended adjustments
    py -3.12 scripts/auto_calibrate.py --from-json PATH   # Load from JSON results
    py -3.12 scripts/auto_calibrate.py --dry-run           # Show what would change
"""

import argparse
import json
import os
import sys
from typing import Optional

# ---------------------------------------------------------------------------
# Import regression test module
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

from regression_test import run_regression_suite, REGRESSION_CASES  # noqa: E402


# ===========================================================================
# Calibration issue detection
# ===========================================================================

def analyze_calibration_issues(regression_result: dict) -> list[dict]:
    """
    分析哪些案例不准，推断可能的参数问题。

    Returns a list of issue dicts, each with:
        case, problem, suggestion, category, severity
    """
    issues = []
    for case in regression_result["cases"]:
        if not case["band_acceptable"]:
            score = case.get("final_score", 2.5)
            expected = case["expected_direction"]
            actual = case["actual_direction"]

            # Pattern 1: 凶案判吉 → 罚分不足
            if score > 3.5 and expected == "inauspicious":
                issues.append({
                    "case": case["case_id"],
                    "case_name": case["case_name"],
                    "problem": "凶案判吉 → 罚分不足",
                    "detail": (
                        f"引擎评分{score:.2f}({actual})，古典结论为凶({expected})。"
                        f"罚分机制未能充分惩罚凶象。"
                    ),
                    "suggestion": "增强三刑/回头克/随官入墓/日破扣分权重",
                    "category": "over-positive",
                    "severity": "high",
                })

            # Pattern 2: 凶案判平吉 → 轻微罚分不足
            elif score > 2.0 and expected == "inauspicious":
                issues.append({
                    "case": case["case_id"],
                    "case_name": case["case_name"],
                    "problem": "凶案判平吉 → 罚分偏弱",
                    "detail": (
                        f"引擎评分{score:.2f}({actual})，古典结论为凶({expected})。"
                        f"方向判定偏高，罚分权重可适当增强。"
                    ),
                    "suggestion": "适度增强忌神克用/化退/月破扣分权重",
                    "category": "over-positive-mild",
                    "severity": "medium",
                })

            # Pattern 3: 吉案判凶 → 加分不足
            elif score < 1.5 and expected == "auspicious":
                issues.append({
                    "case": case["case_id"],
                    "case_name": case["case_name"],
                    "problem": "吉案判凶 → 加分不足",
                    "detail": (
                        f"引擎评分{score:.2f}({actual})，古典结论为吉({expected})。"
                        f"加分机制未能充分奖励吉象。"
                    ),
                    "suggestion": "增强六合/用神旺相/原神暗动/回头生加分权重",
                    "category": "over-negative",
                    "severity": "high",
                })

            # Pattern 4: 吉案判平凶 → 轻微加分不足
            elif score < 2.0 and expected == "auspicious":
                issues.append({
                    "case": case["case_id"],
                    "case_name": case["case_name"],
                    "problem": "吉案判平凶 → 加分偏弱",
                    "detail": (
                        f"引擎评分{score:.2f}({actual})，古典结论为吉({expected})。"
                        f"方向判定偏低，加分权重可适当增强。"
                    ),
                    "suggestion": "适度增强六合加分/用神得生扶加分",
                    "category": "over-negative-mild",
                    "severity": "medium",
                })

            # Pattern 5: 用神取错 → 方向必然错
            if not case["use_god_correct"]:
                issues.append({
                    "case": case["case_id"],
                    "case_name": case["case_name"],
                    "problem": "用神取用错误 → 全盘方向偏差",
                    "detail": (
                        f"引擎取用神为{case['actual_use_god']}，应为{case['expected_use_god']}。"
                        f"用神取错导致旺衰、吉凶分析全部偏离。"
                    ),
                    "suggestion": f"修正用神识别规则，确保'{case['expected_use_god']}'在此类问题中被正确触发",
                    "category": "use-god-error",
                    "severity": "high",
                })

    return issues


# ===========================================================================
# Pattern aggregation
# ===========================================================================

def aggregate_patterns(issues: list[dict]) -> dict:
    """Aggregate individual issues into systemic patterns."""
    patterns = {
        "over-positive": [],
        "over-positive-mild": [],
        "over-negative": [],
        "over-negative-mild": [],
        "use-god-error": [],
    }

    for issue in issues:
        cat = issue.get("category", "unknown")
        if cat in patterns:
            patterns[cat].append(issue["case"])

    return patterns


def generate_calibration_recommendations(patterns: dict, issues: list[dict]) -> list[dict]:
    """
    根据聚合模式生成具体校准建议。

    Returns a list of recommendation dicts with:
        priority, problem, affected_cases, action, parameter_changes
    """
    recommendations = []

    # Systemic over-positive
    if len(patterns.get("over-positive", [])) >= 2:
        recommendations.append({
            "priority": 1,
            "problem": "系统性偏吉 — 多例凶案判吉",
            "affected_cases": patterns["over-positive"],
            "action": "增强凶象罚分机制",
            "parameter_changes": [
                {"param": "回头克扣分", "current": -2.0, "recommended": -2.5, "scope": "step4_change_analysis"},
                {"param": "随官入墓扣分", "current": -1.5, "recommended": -2.0, "scope": "step5_synthesis"},
                {"param": "三刑扣分", "current": -1.0, "recommended": -1.5, "scope": "step3/step5"},
                {"param": "化退扣分", "current": -1.0, "recommended": -1.5, "scope": "step4"},
            ],
        })

    # Systemic over-negative
    if len(patterns.get("over-negative", [])) >= 2:
        recommendations.append({
            "priority": 1,
            "problem": "系统性偏凶 — 多例吉案判凶",
            "affected_cases": patterns["over-negative"],
            "action": "增强吉象加分机制",
            "parameter_changes": [
                {"param": "回头生加分", "current": 1.5, "recommended": 2.0, "scope": "step4_change_analysis"},
                {"param": "六合加分", "current": 0.5, "recommended": 0.7, "scope": "step5_synthesis"},
                {"param": "用神旺相加分", "current": 0.5, "recommended": 0.7, "scope": "step3"},
                {"param": "原神暗动加分", "current": 0.4, "recommended": 0.6, "scope": "step3/step4"},
            ],
        })

    # Mild over-positive
    if len(patterns.get("over-positive-mild", [])) >= 3:
        recommendations.append({
            "priority": 2,
            "problem": "轻微偏吉 — 多例凶案判平吉",
            "affected_cases": patterns["over-positive-mild"],
            "action": "微调忌神力量",
            "parameter_changes": [
                {"param": "忌神克用扣分", "current": -1.5, "recommended": -1.8, "scope": "step4"},
                {"param": "化退扣分", "current": -1.0, "recommended": -1.3, "scope": "step4"},
            ],
        })

    # Mild over-negative
    if len(patterns.get("over-negative-mild", [])) >= 3:
        recommendations.append({
            "priority": 2,
            "problem": "轻微偏凶 — 多例吉案判平凶",
            "affected_cases": patterns["over-negative-mild"],
            "action": "微调生扶力量",
            "parameter_changes": [
                {"param": "六合加分", "current": 0.5, "recommended": 0.6, "scope": "step5"},
                {"param": "用神得生加分", "current": 1.5, "recommended": 1.7, "scope": "step4"},
            ],
        })

    # Use-god errors
    if patterns.get("use-god-error"):
        recommendations.append({
            "priority": 0,  # highest
            "problem": f"用神取用错误 ({len(patterns['use-god-error'])}例)",
            "affected_cases": patterns["use-god-error"],
            "action": "修正用神识别关键词映射",
            "parameter_changes": [
                {"param": "关键词映射表", "scope": "step2_identify_use_god"},
            ],
        })

    recommendations.sort(key=lambda x: x["priority"])
    return recommendations


# ===========================================================================
# Calibration report generation
# ===========================================================================

def generate_calibration_report(issues: list[dict], regression_result: dict) -> str:
    """Generate actionable calibration recommendations (text format)."""
    patterns = aggregate_patterns(issues)
    recommendations = generate_calibration_recommendations(patterns, issues)

    lines = []
    lines.append("=" * 72)
    lines.append("六爻思维链自动校准报告")
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"回归测试总结: {regression_result['summary']}")
    lines.append(f"总案例数: {regression_result['total']}")
    lines.append(f"方向不一致(不可接受): {len(regression_result.get('band_failed_cases', []))}")
    lines.append(f"发现校准问题: {len(issues)}个")
    lines.append("")

    # Pattern summary
    lines.append("-" * 72)
    lines.append("问题模式聚合:")
    lines.append("-" * 72)
    for cat, cases in patterns.items():
        if cases:
            label = {
                "over-positive": "凶案判吉(严重)",
                "over-positive-mild": "凶案判平吉(轻微)",
                "over-negative": "吉案判凶(严重)",
                "over-negative-mild": "吉案判平凶(轻微)",
                "use-god-error": "用神取用错误",
            }.get(cat, cat)
            lines.append(f"  [{label}] {len(cases)}例: {', '.join(cases)}")
    lines.append("")

    # Individual issues
    if issues:
        lines.append("-" * 72)
        lines.append("具体问题:")
        lines.append("-" * 72)
        for i, issue in enumerate(issues, 1):
            sev_marker = {"high": "**", "medium": "*", "low": ""}.get(issue["severity"], "")
            lines.append(f"  {i}. [{issue['case']}] {sev_marker}{issue['problem']}{sev_marker}")
            lines.append(f"     案例: {issue['case_name']}")
            lines.append(f"     详情: {issue['detail']}")
            lines.append(f"     建议: {issue['suggestion']}")
            lines.append("")

    # Recommendations
    lines.append("-" * 72)
    lines.append("校准建议 (按优先级排序):")
    lines.append("-" * 72)
    for rec in recommendations:
        p_label = {0: "最高", 1: "高", 2: "中", 3: "低"}.get(rec["priority"], str(rec["priority"]))
        lines.append(f"\n  [优先级 {p_label}] {rec['problem']}")
        lines.append(f"  影响案例: {', '.join(rec['affected_cases'])}")
        lines.append(f"  操作: {rec['action']}")
        if rec["parameter_changes"]:
            lines.append(f"  参数调整:")
            for pc in rec["parameter_changes"]:
                cur = pc.get("current", "")
                rec_val = pc.get("recommended", "")
                scope = pc.get("scope", "")
                if isinstance(cur, (int, float)) and isinstance(rec_val, (int, float)):
                    lines.append(
                        f"    - {pc['param']}: {cur} → {rec_val}  (范围: {scope})"
                    )
                else:
                    lines.append(f"    - {pc['param']}: {rec_val}  (范围: {scope})")

    if not recommendations:
        lines.append("\n  无需校准 — 所有案例方向一致！")

    lines.append("")
    lines.append("=" * 72)

    # Apply instructions
    lines.append("")
    lines.append("使用方式:")
    lines.append("  py -3.12 scripts/auto_calibrate.py --dry-run    # 查看详情")
    lines.append("  py -3.12 scripts/auto_calibrate.py --apply       # 应用调整")
    lines.append("")

    return "\n".join(lines)


def generate_json_recommendations(issues: list[dict], regression_result: dict) -> str:
    """Generate machine-readable calibration recommendations."""
    patterns = aggregate_patterns(issues)
    recommendations = generate_calibration_recommendations(patterns, issues)

    output = {
        "regression_summary": regression_result["summary"],
        "total_cases": regression_result["total"],
        "band_failed_count": len(regression_result.get("band_failed_cases", [])),
        "issue_count": len(issues),
        "patterns": {k: v for k, v in patterns.items() if v},
        "issues": issues,
        "recommendations": recommendations,
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


# ===========================================================================
# Simulated apply (dry-run)
# ===========================================================================

def simulate_apply(recommendations: list[dict]) -> str:
    """Show what would happen if --apply is used."""
    lines = []
    lines.append("=" * 72)
    lines.append("模拟应用校准参数 (dry-run)")
    lines.append("=" * 72)
    lines.append("")
    lines.append("注意: 当前版本不会直接修改 thinking_chain.py 源码, ")
    lines.append("      而是输出 patch 命令供人工审核后应用。")
    lines.append("")

    for rec in recommendations:
        lines.append(f"[优先级 {rec['priority']}] {rec['problem']}")
        for pc in rec["parameter_changes"]:
            param = pc.get("param", "")
            cur = pc.get("current", "")
            rec_val = pc.get("recommended", "")
            scope = pc.get("scope", "")
            if isinstance(cur, (int, float)):
                lines.append(
                    f"  PATCH: thinking_chain.py → {scope} → "
                    f"{param}: {cur} → {rec_val}"
                )
            else:
                lines.append(f"  PATCH: thinking_chain.py → {scope} → {param}")
        lines.append("")

    lines.append("请审查以上参数变更后, 手动在源码中对应位置修改。")
    return "\n".join(lines)


# ===========================================================================
# CLI
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="自动校准工具 — 基于回归测试结果推荐评分参数调整",
    )
    parser.add_argument(
        "--from-json",
        type=str,
        default=None,
        help="Load regression results from JSON file instead of running fresh",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Show detailed patch instructions (does not modify source)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be modified without applying",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Save calibration report to file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON recommendations",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose regression test output",
    )
    args = parser.parse_args()

    # Run or load regression
    if args.from_json:
        with open(args.from_json, "r", encoding="utf-8") as f:
            regression_result = json.load(f)
        # Normalize: JSON format may already be clean
        if "band_failed_cases" not in regression_result:
            regression_result["band_failed_cases"] = [
                c for c in regression_result["cases"] if not c.get("band_acceptable", True)
            ]
        if "failed_cases" not in regression_result:
            regression_result["failed_cases"] = [
                c for c in regression_result["cases"] if not c.get("all_passed", True)
            ]
    else:
        print("Running regression suite...", file=sys.stderr)
        regression_result = run_regression_suite(verbose=args.verbose)

    # Analyze issues
    issues = analyze_calibration_issues(regression_result)

    # Output
    if args.json:
        output = generate_json_recommendations(issues, regression_result)
    elif args.apply:
        patterns = aggregate_patterns(issues)
        recommendations = generate_calibration_recommendations(patterns, issues)
        output = simulate_apply(recommendations)
    elif args.dry_run:
        patterns = aggregate_patterns(issues)
        recommendations = generate_calibration_recommendations(patterns, issues)
        output = simulate_apply(recommendations)
        # Also prepend the text report
        text_report = generate_calibration_report(issues, regression_result)
        output = text_report + "\n\n" + output
    else:
        output = generate_calibration_report(issues, regression_result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Calibration report saved: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
