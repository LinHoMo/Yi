# -*- coding: utf-8 -*-
"""
六爻反幻觉校验模块 (Anti-Hallucination Guard)
============================================
在 LLM 生成解读后，校验解读内容与引擎输出之间的一致性。
检测常见的幻觉问题：卦名错误、用神不一致、吉凶矛盾、伪造经典引文等。

用法：
  py -3.12 scripts/hallucination_guard.py --engine-result result.json --interpretation interp.txt
  py -3.12 scripts/hallucination_guard.py < interpreter_output.txt  (engine result from stdin)
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# 六十四卦标准名（用于检测解读中引用的卦名是否与引擎一致）
# ---------------------------------------------------------------------------
HEXAGRAM_NAMES = [
    "乾", "坤", "屯", "蒙", "需", "讼", "师", "比",
    "小畜", "履", "泰", "否", "同人", "大有", "谦", "豫",
    "随", "蛊", "临", "观", "噬嗑", "贲", "剥", "复",
    "无妄", "大畜", "颐", "大过", "坎", "离", "咸", "恒",
    "遁", "大壮", "晋", "明夷", "家人", "睽", "蹇", "解",
    "损", "益", "夬", "姤", "萃", "升", "困", "井",
    "革", "鼎", "震", "艮", "渐", "归妹", "丰", "旅",
    "巽", "兑", "涣", "节", "中孚", "小过", "既济", "未济",
]

# 六亲标准名
SIX_RELATIONS = ["父母", "官鬼", "妻财", "子孙", "兄弟"]

# 六神标准名
SIX_SPIRITS = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]


# ---------------------------------------------------------------------------
# 检测结果数据类
# ---------------------------------------------------------------------------

@dataclass
class HallucinationCheck:
    """单次校验结果"""
    check_name: str
    passed: bool
    detail: str
    severity: str = "info"  # "info" | "warning" | "critical"

    def __repr__(self):
        mark = "PASS" if self.passed else "FAIL"
        return f"[{mark}/{self.severity}] {self.check_name}: {self.detail}"


@dataclass
class VerificationReport:
    """校验总报告"""
    checks: list = field(default_factory=list)
    score: float = 0.0  # 0.0 ~ 1.0 (通过率)
    risk_level: str = "low"  # "low" | "medium" | "high"
    summary: str = ""


# ---------------------------------------------------------------------------
# 核心校验函数
# ---------------------------------------------------------------------------

def verify_interpretation(
    engine_result: dict,
    interpretation_text: str,
) -> list:
    """
    比较 LLM 解读文本与引擎输出，返回所有校验项。

    参数
    ----
    engine_result : dict
        build_hexagram_result() + run_thinking_chain() 后的完整结果字典。
    interpretation_text : str
        LLM 生成的解读文本原文。

    返回
    ----
    list[HallucinationCheck]
        所有校验项的结果列表。
    """
    checks = []

    # 1. 本卦卦名一致性
    checks.append(_check_hexagram_name(engine_result, interpretation_text))

    # 2. 用神一致性
    checks.append(_check_use_god_consistency(engine_result, interpretation_text))

    # 3. 动爻一致性
    checks.append(_check_moving_lines(engine_result, interpretation_text))

    # 4. 吉凶方向一致性
    checks.append(_check_verdict_alignment(engine_result, interpretation_text))

    # 5. 六亲术语合法性
    checks.append(_check_six_relations_validity(interpretation_text))

    # 6. 经典引文来源校验
    checks.append(_check_classical_quotes(engine_result, interpretation_text))

    # 7. 变卦卦名一致性（若有变卦）
    checks.append(_check_changed_hexagram_name(engine_result, interpretation_text))

    # 8. 地支术语合法性
    checks.append(_check_earthly_branches_validity(interpretation_text))

    return checks


# ---------------------------------------------------------------------------
# 各项校验实现
# ---------------------------------------------------------------------------

def _check_hexagram_name(engine_result: dict, text: str) -> HallucinationCheck:
    """校验解读中引用的本卦卦名是否与引擎一致。"""
    engine_hex = engine_result.get("original_hexagram", {}).get("name", "")
    if not engine_hex:
        return HallucinationCheck("本卦卦名匹配", False, "引擎结果中无本卦名称", "warning")

    # 检查引擎卦名是否在解读中被提及
    if engine_hex in text:
        return HallucinationCheck(
            "本卦卦名匹配", True,
            f"本卦「{engine_hex}」在解读中正确提及"
        )

    # 解读中提到了其他卦名（可能幻觉其他卦）
    mentioned_hex = [h for h in HEXAGRAM_NAMES if h in text and h != engine_hex]
    # 过滤掉单字匹配的误报（如"乾"出现在"乾坤"中但实际指另一卦）
    # 检查是否有明确的"XX卦"或"XX宫"或"XX之变"模式
    false_positive_patterns = []
    for h in mentioned_hex:
        # 如果 h 只在 text 中作为 engine_hex 的一部分出现，不算幻觉
        idx = text.find(h)
        while idx != -1:
            context = text[max(0, idx - 3):idx + len(h) + 3]
            # 检查上下文是否明确指向一卦名
            if re.search(rf'{h}(卦|宫|上|下|象|之)', context):
                false_positive_patterns.append(h)
                break
            idx = text.find(h, idx + 1)

    if false_positive_patterns:
        return HallucinationCheck(
            "本卦卦名匹配", False,
            f"引擎本卦为「{engine_hex}」，但解读提及其他卦「{'、'.join(false_positive_patterns)}」",
            "critical"
        )

    return HallucinationCheck(
        "本卦卦名匹配", False,
        f"本卦「{engine_hex}」在解读中未明确提及",
        "warning"
    )


def _check_use_god_consistency(engine_result: dict, text: str) -> HallucinationCheck:
    """校验用神在解读中是否被提及或与引擎一致。"""
    chain = engine_result.get("thinking_chain", {})
    step2 = chain.get("step2_use_god_identification", {})
    engine_use_god = step2.get("use_god_category", "")

    if not engine_use_god:
        # 跳过：引擎无思维链数据
        return HallucinationCheck("用神一致性", True, "引擎无思维链用神数据，跳过校验", "info")

    # 检查引擎用神是否在解读文本中被提及
    if engine_use_god in text:
        return HallucinationCheck(
            "用神一致性", True,
            f"用神「{engine_use_god}」在解读中被提及"
        )

    # 解读中是否用了截然不同的用神
    other_gods = [r for r in SIX_RELATIONS if r in text and r != engine_use_god]
    if other_gods:
        return HallucinationCheck(
            "用神一致性", False,
            f"引擎用神为「{engine_use_god}」，但解读突出提及「{'、'.join(other_gods)}」",
            "warning"
        )

    return HallucinationCheck(
        "用神一致性", False,
        f"引擎用神「{engine_use_god}」在解读中未提及",
        "warning"
    )


def _check_moving_lines(engine_result: dict, text: str) -> HallucinationCheck:
    """校验解读中提及的动爻是否与引擎一致。"""
    chain = engine_result.get("thinking_chain", {})
    step4 = chain.get("step4_change_analysis", {})
    yao_analysis = step4.get("yao_analysis", step4.get("moving_details", []))

    # 从引擎结果获取动爻位置列表
    changed_lines = []
    ch = engine_result.get("changed_hexagram")
    if ch:
        changed_lines = ch.get("changed_lines", [])

    if not changed_lines:
        # 无动爻——检查解读是否虚构了动爻
        # 查找"第X爻动"模式
        moving_pattern = re.findall(r'第([一二三四五六六])爻动', text)
        if moving_pattern:
            return HallucinationCheck(
                "动爻一致性", False,
                f"引擎无动爻，但解读声称「第{'、'.join(moving_pattern)}爻动」",
                "critical"
            )
        return HallucinationCheck("动爻一致性", True, "静卦无动爻，解读一致", "info")

    # 有动爻——检查解读中是否提及了它们
    engine_set = set(changed_lines)

    # 尝试从解读中提取提及的动爻
    mentioned_positions = set()
    for match in re.finditer(r'第([一二三四五六])爻(?:动|发动|变动)', text):
        cn_to_num = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6}
        num = cn_to_num.get(match.group(1))
        if num:
            mentioned_positions.add(num)

    # 也检查阿拉伯数字
    for match in re.finditer(r'第(\d+)(?:爻|yáo)', text):
        num = int(match.group(1))
        if 1 <= num <= 6:
            mentioned_positions.add(num)

    if mentioned_positions:
        extra = mentioned_positions - engine_set
        missing = engine_set - mentioned_positions
        if extra:
            return HallucinationCheck(
                "动爻一致性", False,
                f"解读提及不存在的动爻 第{', '.join(str(e) for e in sorted(extra))}爻",
                "critical"
            )
        if missing:
            return HallucinationCheck(
                "动爻一致性", True,  # 缺失不等于幻觉，infoyer可能简述
                f"解读未提及所有动爻 — 缺 第{', '.join(str(m) for m in sorted(missing))}爻（可能是简写）",
                "info"
            )
        return HallucinationCheck(
            "动爻一致性", True,
            f"动爻 第{', '.join(str(m) for m in sorted(engine_set))}爻 在解读中被提及"
        )

    # 没找到解读中明确提到动爻——不一定是幻觉，可能隐含在描述中
    return HallucinationCheck(
        "动爻一致性", True,
        f"引擎有动爻 第{', '.join(str(m) for m in sorted(engine_set))}爻，解读未显式编号提及（非幻觉）",
        "info"
    )


def _check_verdict_alignment(engine_result: dict, text: str) -> HallucinationCheck:
    """校验解读的吉凶方向是否与引擎综合判断一致。"""
    chain = engine_result.get("thinking_chain", {})
    step5 = chain.get("step5_synthesis", {})
    engine_verdict = step5.get("verdict", "")

    if not engine_verdict:
        return HallucinationCheck("吉凶方向校验", True, "引擎无思维链 verdict 数据，跳过", "info")

    # 提取解读中的吉凶关键词
    auspicious_in_text = any(kw in text for kw in ["大吉", "吉", "上吉", "中吉", "顺利", "可成", "亨通"])
    inauspicious_in_text = any(kw in text for kw in ["大凶", "凶", "不利", "大凶", "危", "不可", "失败", "凶险"])
    mixed_in_text = any(kw in text for kw in ["平吉", "平凶", "吉中有凶", "凶中藏吉", "平"])

    # 引擎吉 verdict
    engine_auspicious = "吉" in engine_verdict and "凶" not in engine_verdict
    engine_inauspicious = "凶" in engine_verdict and "吉" not in engine_verdict
    engine_mixed = ("平" in engine_verdict) or ("吉" in engine_verdict and "凶" in engine_verdict)

    if engine_auspicious:
        if inauspicious_in_text and not auspicious_in_text:
            return HallucinationCheck(
                "吉凶方向校验", False,
                f"引擎判「{engine_verdict}(吉向)」，但解读纯凶无吉",
                "critical"
            )
        return HallucinationCheck(
            "吉凶方向校验", True,
            f"引擎判「{engine_verdict}(吉向)」，解读方向不矛盾"
        )

    if engine_inauspicious:
        if auspicious_in_text and not inauspicious_in_text:
            return HallucinationCheck(
                "吉凶方向校验", False,
                f"引擎判「{engine_verdict}(凶向)」，但解读纯吉无凶",
                "critical"
            )
        return HallucinationCheck(
            "吉凶方向校验", True,
            f"引擎判「{engine_verdict}(凶向)」，解读方向不矛盾"
        )

    # 混合 verdict
    return HallucinationCheck(
        "吉凶方向校验", True,
        f"引擎判「{engine_verdict}(混合)」，无单一方向冲突",
        "info"
    )


def _check_six_relations_validity(text: str) -> HallucinationCheck:
    """校验解读中使用的六亲术语是否合法（无杜撰）。"""
    # 文本中出现的六亲模式
    relation_pattern = re.findall(r'[父母官鬼妻财子孙兄弟]', text)
    invalid = set()
    for char_pair in relation_pattern:
        if char_pair not in SIX_RELATIONS:
            # 单个字符被误匹配 — 仅当它不属于任何标准六亲
            pass

    # 更严格：查找连续两个字符的六亲
    found_relations = set()
    for rel in SIX_RELATIONS:
        if rel in text:
            found_relations.add(rel)

    # 检查杜撰的六亲（生僻组合）
    fabricated = set()
    common_fabricated = ["父官", "子兄", "财鬼", "官父", "鬼兄", "财父"]
    for fab in common_fabricated:
        if fab in text:
            fabricated.add(fab)

    if fabricated:
        return HallucinationCheck(
            "六亲术语合法性", False,
            f"解读中出现非标准六亲术语「{'、'.join(fabricated)}」",
            "critical"
        )

    return HallucinationCheck(
        "六亲术语合法性", True,
        f"六亲术语使用正确（{len(found_relations)}种标准六亲被引用）"
    )


def _check_classical_quotes(engine_result: dict, text: str) -> HallucinationCheck:
    """校验引用的经典是否与引擎输出的经典引文一致。"""
    # 提取解读中声称的经典来源
    claimed_sources = re.findall(r'[《〈]([^》〉]+)[》〉]', text)
    if not claimed_sources:
        return HallucinationCheck(
            "经典引文来源", True,
            "解读未引用具体经典，跳过校验",
            "info"
        )

    # 从引擎思维链中获取实际的引文
    chain = engine_result.get("thinking_chain", {})
    step5 = chain.get("step5_synthesis", {})
    engine_quotes = step5.get("classical_quotes", [])
    engine_sources = set()
    if isinstance(engine_quotes, list):
        for q in engine_quotes:
            if isinstance(q, dict) and q.get("source"):
                engine_sources.add(q["source"].strip("《》"))

    # 检查每个声称的经典
    verified = []
    unverified = []
    for claimed in claimed_sources:
        # 去除书名号后比较
        clean_claimed = claimed.strip("《》")
        found = False
        for eng_src in engine_sources:
            if clean_claimed in eng_src or eng_src in clean_claimed:
                found = True
                break
        if found:
            verified.append(claimed)
        else:
            unverified.append(claimed)

    if unverified:
        return HallucinationCheck(
            "经典引文来源", False,
            f"解读引用「{'、'.join('《' + u + '》' for u in unverified)}" +
            (f"」，引擎实际引用的经典为「{'、'.join('《' + s + '》' for s in engine_sources)}」"
             if engine_sources else "」，但引擎未检出相关引文"),
            "warning"
        )

    return HallucinationCheck(
        "经典引文来源", True,
        f"引用的经典「{'、'.join('《' + v + '》' for v in verified)}」均有引擎数据支撑"
    )


def _check_changed_hexagram_name(engine_result: dict, text: str) -> HallucinationCheck:
    """若有变卦，校验解读中提及的变卦名是否与引擎一致。"""
    ch = engine_result.get("changed_hexagram")
    if not ch:
        return HallucinationCheck("变卦一致性", True, "无变卦，跳过校验", "info")

    changed_name = ch.get("name", "")
    if not changed_name:
        return HallucinationCheck("变卦一致性", True, "变卦名为空，跳过校验", "info")

    if changed_name in text:
        return HallucinationCheck(
            "变卦一致性", True,
            f"变卦「{changed_name}」在解读中被正确提及"
        )

    # 检查误解了变卦
    mentioned_wrong = [h for h in HEXAGRAM_NAMES
                       if h in text and h != changed_name and h != engine_result.get("original_hexagram", {}).get("name", "")]
    # 与本卦同名不计算
    original_name = engine_result.get("original_hexagram", {}).get("name", "")
    wrong_for_changed = [h for h in mentioned_wrong if h != original_name]

    if wrong_for_changed:
        # 检查上下文中是否明确指变卦
        for h in wrong_for_changed:
            idx = text.find(h)
            context = text[max(0, idx - 4):idx + len(h) + 4]
            if re.search(rf'(变|之|化|转).*{h}', context) or re.search(rf'{h}.*(变|之|化|转)', context):
                return HallucinationCheck(
                    "变卦一致性", False,
                    f"引擎变卦为「{changed_name}」，但解读声称变卦为「{h}」",
                    "critical"
                )

    return HallucinationCheck(
        "变卦一致性", True,
        f"变卦「{changed_name}」在解读中未显式提及（可能以其他方式描述）",
        "info"
    )


def _check_earthly_branches_validity(text: str) -> HallucinationCheck:
    """校验解读中出现的地支术语是否合法。"""
    BRANCHES = {"子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"}

    # 提取可能的"X土/火/金/水/木"组合
    illegal = set()
    # 常见错误：把非地支字当下支
    non_branch_chars = {"甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸",
                       "东", "南", "西", "北", "春", "夏", "秋", "冬"}
    for char in non_branch_chars:
        # 检查是否有"X土"这样的错误模式
        matches = re.findall(rf'{char}[土火水木金]', text)
        for m in matches:
            illegal.add(m)

    if illegal:
        return HallucinationCheck(
            "地支术语合法性", False,
            f"解读中出现非标准地支术语「{'、'.join(sorted(illegal))}」",
            "warning"
        )

    return HallucinationCheck(
        "地支术语合法性", True,
        "地支术语使用正确",
        "info"
    )


# ---------------------------------------------------------------------------
# 生成校验报告
# ---------------------------------------------------------------------------

def generate_report(checks: list) -> VerificationReport:
    """将校验结果列表汇总为报告。"""
    if not checks:
        return VerificationReport(
            checks=[], score=1.0, risk_level="low", summary="无校验项"
        )

    total = len(checks)
    passed = sum(1 for c in checks if c.passed)
    critical_fail = sum(1 for c in checks if not c.passed and c.severity == "critical")
    warning_fail = sum(1 for c in checks if not c.passed and c.severity == "warning")

    score = passed / total if total else 1.0

    if critical_fail > 0:
        risk_level = "high"
    elif warning_fail > 1:
        risk_level = "medium"
    elif warning_fail == 1:
        risk_level = "low"
    else:
        risk_level = "low"

    failed = [c for c in checks if not c.passed]
    summary_parts = []
    if failed:
        critical_parts = [c.check_name for c in failed if c.severity == "critical"]
        warning_parts = [c.check_name for c in failed if c.severity == "warning"]
        parts = []
        if critical_parts:
            parts.append(f"严重错误: {', '.join(critical_parts)}")
        if warning_parts:
            parts.append(f"警告: {', '.join(warning_parts)}")
        summary_parts.append("；".join(parts))
    else:
        summary_parts.append("全部校验通过")

    return VerificationReport(
        checks=checks,
        score=score,
        risk_level=risk_level,
        summary="；".join(summary_parts),
    )


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="六爻反幻觉校验 — 验证 LLM 解读与引擎输出的一致性"
    )
    parser.add_argument(
        "--engine-result", "-e",
        type=str,
        help="引擎输出的 JSON 文件路径（默认为 stdin）"
    )
    parser.add_argument(
        "--interpretation", "-i",
        type=str,
        help="LLM 解读文本文件路径（默认为 stdin 或第二个参数）"
    )
    parser.add_argument(
        "--output", "-o",
        choices=["text", "json"],
        default="text",
        help="输出格式"
    )
    args = parser.parse_args()

    # 读取引擎结果
    if args.engine_result:
        with open(args.engine_result, "r", encoding="utf-8") as f:
            engine_result = json.load(f)
    else:
        # 从 stdin 读取 JSON
        try:
            engine_result = json.load(sys.stdin)
        except json.JSONDecodeError:
            print("错误：无法解析 stdin 为 JSON，请提供 --engine-result 文件", file=sys.stderr)
            sys.exit(1)

    # 读取解读文本
    if args.interpretation:
        with open(args.interpretation, "r", encoding="utf-8") as f:
            interpretation_text = f.read()
    else:
        # 尝试从第二个位置参数读取文件
        if len(sys.argv) > 1 and not sys.stdin.isatty():
            interpretation_text = sys.stdin.read()
        else:
            print("错误：请提供 --interpretation 文件路径", file=sys.stderr)
            sys.exit(1)

    # 执行校验
    checks = verify_interpretation(engine_result, interpretation_text)
    report = generate_report(checks)

    # 输出
    if args.output == "json":
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
        print(f"通过率：{report.score * 100:.0f}% ({sum(1 for c in checks if c.passed)}/{len(checks)})")
        print(f"风险等级：{report.risk_level}")
        print(f"总结：{report.summary}")
        print("-" * 60)
        for c in checks:
            mark = "PASS" if c.passed else "FAIL"
            print(f"  [{mark}/{c.severity}] {c.check_name}: {c.detail}")
        print("=" * 60)


if __name__ == "__main__":
    main()
