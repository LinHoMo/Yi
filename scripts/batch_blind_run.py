#!/usr/bin/env python3
"""
批量盲评运行器：对 blind_input.json 中所有案例执行排盘，
仅保留引擎输出（不含标准答案），供独立子代理盲评。
"""
import json
import os
import sys
import subprocess
import json
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
BLIND_INPUT = SKILL_DIR / "data" / "cases" / "blind_input.json"
OUTPUT_FILE = SKILL_DIR / "data" / "cases" / "blind_engine_output_v2.json"

def load_blind_input():
    with open(BLIND_INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 兼容两种格式：{"cases": [...]} 或 直接数组
    if isinstance(data, dict) and "cases" in data:
        return data["cases"]
    return data

def extract_engine_output(raw_stdout: str) -> dict:
    """从引擎标准输出中提取JSON结果"""
    try:
        output = raw_stdout
        json_start = output.find('{')
        if json_start < 0:
            return {"error": "No JSON found"}
        
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
        return json.loads(json_str)
    except Exception as e:
        return {"error": str(e)}

def run_case(case: dict) -> dict:
    """对单个案例执行排盘，仅保留引擎输出"""
    case_id = case["id"]
    question = case.get("question", "古籍案例")
    
    # 解析日期
    date_str = case.get("date", "")
    month_map = {"寅": 2, "卯": 3, "辰": 4, "巳": 5, "午": 6, 
                 "未": 7, "申": 8, "酉": 9, "戌": 10, "亥": 11, "子": 12, "丑": 1}
    month = 6  # 默认
    for cn_m, m in month_map.items():
        if f"{cn_m}月" in date_str:
            month = m
            break
    
    cmd = [
        sys.executable, str(SCRIPTS_DIR / "liuyao_engine.py"),
        "--mode", "coin",
        "--question", question,
        "--year", "2026",
        "--month", str(month),
        "--day", "15",
        "--hour", "10",
        "--format", "json",
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                              cwd=str(SCRIPTS_DIR), encoding="utf-8")
        if result.returncode != 0:
            return {"id": case_id, "question": question, "error": result.stderr.strip()[:500]}
        
        engine_result = extract_engine_output(result.stdout)
        if "error" in engine_result:
            return {"id": case_id, "question": question, "error": engine_result["error"]}
        
        # 提取关键字段
        original = engine_result.get("original_hexagram", {})
        tc = engine_result.get("thinking_chain", {})
        step2 = tc.get("step2_use_god_identification", {})
        step3 = tc.get("step3_strength_analysis", {})
        step5 = tc.get("step5_synthesis", {})
        
        # 构建输出（不含标准答案）
        output = {
            "id": case_id,
            "question": question,
            "input_date": date_str,
            "hexagram": original.get("name", "?"),
            "palace": original.get("palace", "?"),
            "generation": original.get("generation", "?"),
            "palace_element": original.get("palace_element", "?"),
            "moving_lines": [m.get("position") for m in engine_result.get("moving_lines", [])],
            "changed_hexagram": engine_result.get("changed_hexagram", {}).get("name", "?"),
            "use_god_category": step2.get("use_god_category", "?"),
            "use_god_branch": (step2.get("selected_use_god") or {}).get("branch", "?"),
            "use_god_element": step2.get("use_god_element", "?"),
            "use_god_position": (step2.get("selected_use_god") or {}).get("position", "?"),
            "strength_level": step3.get("strength_level", "?"),
            "strength_score": step3.get("effective_score", "?"),
            "final_score": step5.get("final_score", "?"),
            "verdict": step5.get("verdict", "?"),
            "verdict_desc": step5.get("verdict_description", "?"),
            "yingqi": step5.get("timing", {}).get("summary_text", "?"),
            "reasoning_chain": step5.get("reasoning_chain", []),
            "classical_quotes": engine_result.get("classical_quotes", []),
        }
        return output
    except Exception as e:
        return {"id": case_id, "question": question, "error": str(e)[:500]}

def main():
    cases = load_blind_input()
    results = []
    total = len(cases)
    
    print(f"=== 批量盲评运行：{total} 条案例 ===\n")
    
    for i, case in enumerate(cases, 1):
        case_id = case["id"]
        print(f"[{i}/{total}] {case_id}: {case.get('question', '')[:40]}...", end=" ", flush=True)
        result = run_case(case)
        results.append(result)
        
        if "error" in result:
            print(f"✗ 错误: {result['error'][:80]}")
        else:
            print(f"卦={result['hexagram']} 用神={result['use_god_category']} 断语={result['verdict']} 评分={result['final_score']}")
    
    # 保存结果
    output_data = {
        "engine": "liuyao_engine.py v2",
        "total_cases": total,
        "timestamp": "2026-09-19",
        "cases": results
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 结果已保存到: {OUTPUT_FILE} ===")
    
    # 统计
    valid = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]
    print(f"成功: {len(valid)}/{total}, 失败: {len(errors)}/{total}")
    
    if valid:
        verdicts = {}
        for r in valid:
            v = r.get("verdict", "?")
            verdicts[v] = verdicts.get(v, 0) + 1
        print(f"断语分布: {verdicts}")

if __name__ == "__main__":
    main()
