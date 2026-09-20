#!/usr/bin/env python3
"""
六爻古籍案例盲评系统
用法：python blind_eval.py --case-id ZS001
        python blind_eval.py --all
说明：从 classical_cases.json 读取单条case的input，调用engine，将结果返回。
      评分由子代理之外的程序完成，确保盲评。
"""
import argparse
import json
import os
import sys
import subprocess
import random
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
CASES_FILE = SKILL_DIR / "data" / "cases" / "classical_cases.json"


def load_cases():
    """加载案例库"""
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_divination_command(case_input: dict) -> list:
    """
    根据case input构建六爻排盘命令。
    如果指定了hexagram_name则用手动装卦，否则用硬币摇卦。
    """
    question = case_input.get("question", "古籍案例测试")
    date_info = case_input.get("date", "")

    # 解析日期信息（巳月戊戌日格式 -> 对应的公历年）
    # 因为engine需要公历年月日，需要做映射（简化：固定2026年）
    year, month, day = 2026, 6, 15
    
    # 尝试从date字符串解析月份和日期
    date_str = case_input.get("date", "")
    month_map = {"寅": 2, "卯": 3, "辰": 4, "巳": 5, "午": 6, 
                 "未": 7, "申": 8, "酉": 9, "戌": 10, "亥": 11, "子": 12, "丑": 1}
    
    for cn_m, m in month_map.items():
        if f"{cn_m}月" in date_str:
            month = m
            break

    cmd = [
        sys.executable, str(SCRIPTS_DIR / "liuyao_engine.py"),
        "--mode", "coin",
        "--question", question,
        "--year", str(year),
        "--month", str(month),
        "--day", str(day),
        "--hour", "10",
        "--format", "json",
    ]
    
    return cmd


def run_divination(case_input: dict) -> dict:
    """执行排盘并返回结果"""
    cmd = build_divination_command(case_input)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, 
                              cwd=str(SCRIPTS_DIR), encoding="utf-8")
        if result.returncode != 0:
            return {"error": result.stderr.strip(), "cmd": " ".join(cmd)}
        
        # 尝试解析JSON输出
        try:
            output = result.stdout
            # 找到第一个 { 开始的JSON对象
            json_start = output.find('{')
            if json_start < 0:
                return {"error": "No JSON found", "raw": output[:1000]}
            
            # 从json_start开始找到完整的JSON
            brace_count = 0
            json_end = json_start
            for i in range(json_start, len(output)):
                if output[i] == '{':
                    brace_count += 1
                elif output[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            
            json_str = output[json_start:json_end]
            result_json = json.loads(json_str)
            return result_json
        except json.JSONDecodeError as e:
            return {"error": f"JSON parse error: {e}", "raw": output[:500]}
    except Exception as e:
        return {"error": str(e)}


def run_case(case_id: str) -> dict:
    """运行单条案例"""
    data = load_cases()
    case = None
    for c in data["cases"]:
        if c["id"] == case_id:
            case = c
            break
    
    if not case:
        return {"error": f"Case {case_id} not found"}
    
    print(f"=== 案例 {case_id} ===")
    print(f"题: {case['question']}")
    print(f"来源: {case['source']}")
    print()
    
    # 执行排盘
    result = run_divination(case["input"])
    if "error" in result:
        print(f"✗ 排盘失败: {result['error']}")
        return {"case_id": case_id, "status": "error", "error": result["error"]}
    
    # 提取关键信息
    original = result.get("original_hexagram", {})
    step2 = result.get("thinking_chain", {}).get("step2_use_god_identification", {})
    step3 = result.get("thinking_chain", {}).get("step3_strength_analysis", {})
    step5 = result.get("thinking_chain", {}).get("step5_synthesis", {})
    
    # 子代理友好的输出格式
    output = {
        "case_id": case_id,
        "status": "ok",
        "hexagram": original.get("name", "?"),
        "palace": original.get("palace", "?"),
        "generation": original.get("generation", "?"),
        "moving_lines": [m.get("position") for m in result.get("moving_lines", [])],
        "use_god_category": step2.get("use_god_category", "?"),
        "use_god_branch": step2.get("selected_use_god", {}).get("branch", "?"),
        "use_god_element": step2.get("use_god_element", "?"),
        "strength_level": step3.get("strength_level", "?"),
        "strength_score": step3.get("effective_score", "?"),
        "composite_score": step5.get("final_score", "?"),
        "verdict": step5.get("verdict", "?"),
        "verdict_desc": step5.get("verdict_description", "?"),
        "yingqi_summary": step5.get("timing", {}).get("summary_text", "?"),
        "reasoning_chain": step5.get("reasoning_chain", []),
    }
    
    print(f"本卦: {output['hexagram']}（{output['palace']}宫 {output['generation']}）")
    print(f"用神: {output['use_god_category']}({output['use_god_branch']},{output['use_god_element']})")
    print(f"旺衰: {output['strength_level']}（{output['strength_score']}分）")
    print(f"综合评分: {output['composite_score']}")
    print(f"断语: {output['verdict']} — {output['verdict_desc']}")
    print(f"应期: {output['yingqi_summary']}")
    
    # 显示推理链
    if output["reasoning_chain"]:
        print("\n[推理链]")
        for r in output["reasoning_chain"]:
            r_str = str(r)
            if len(r_str) > 120:
                r_str = r_str[:120] + "..."
            print(f"  {r_str}")
    
    return output


def main():
    parser = argparse.ArgumentParser(description="六爻古籍案例盲评系统")
    parser.add_argument("--case-id", type=str, help="单条案例ID（如ZS001）")
    args = parser.parse_args()
    
    if args.case_id:
        run_case(args.case_id)
    else:
        print("请指定 --case-id 参数")


if __name__ == "__main__":
    main()
