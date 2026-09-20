#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch blind evaluation script for 20 classical cases."""
import json
import subprocess
import os
import re
import sys

SCRIPT_DIR = r"C:\Users\Lin\.meituan-catpaw\4567030888\skills\liu-yao\scripts"
ENGINE = os.path.join(SCRIPT_DIR, "liuyao_engine.py")
TMP_FILE = r"C:\Users\Lin\.meituan-catpaw\4567030888\skills\liu-yao\data\cases\tmp_result.json"

# Month mapping: lunar month char -> solar month number
MONTH_MAP = {
    "寅": 2, "卯": 3, "辰": 4, "巳": 5, "午": 6, "未": 7,
    "申": 8, "酉": 9, "戌": 10, "亥": 11, "子": 12, "丑": 1
}

def extract_month(date_str):
    """Extract lunar month from date string like '巳月戊戌日' or '亥月甲子日'."""
    for key, val in MONTH_MAP.items():
        if key + "月" in date_str:
            return val
    return 6  # Default if no month found

def run_engine(question, year, month, day):
    """Run the liuyao engine and return parsed JSON result or None."""
    cmd = [
        sys.executable, ENGINE,
        "--mode", "coin",
        "--question", question,
        "--year", str(year),
        "--month", str(month),
        "--day", str(day),
        "--hour", "10",
        "--format", "json"
    ]
    
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60,
            cwd=SCRIPT_DIR, encoding="utf-8"
        )
        
        stdout = result.stdout
        stderr = result.stderr
        
        # Write raw output for debugging
        with open(TMP_FILE, 'w', encoding='utf-8') as f:
            f.write(stdout)
            if stderr:
                f.write("\n[STDERR]\n" + stderr)
        
        # Parse JSON from stdout only
        json_start = stdout.find('{')
        if json_start < 0:
            print("  [WARN] No JSON found in stdout", file=sys.stderr)
            return None
        
        json_str = stdout[json_start:]
        
        # Try to parse the full JSON first
        try:
            data = json.loads(json_str)
            return data
        except json.JSONDecodeError:
            pass
        
        # Trim trailing non-JSON content (event logs etc.)
        brace_count = 0
        end_pos = 0
        for i, ch in enumerate(json_str):
            if ch == '{':
                brace_count += 1
            elif ch == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i + 1
                    break
        
        if end_pos > 0:
            try:
                data = json.loads(json_str[:end_pos])
                return data
            except json.JSONDecodeError:
                pass
        
        print("  [WARN] Failed to parse JSON", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  [ERROR] Engine execution failed: {e}", file=sys.stderr)
        return None

def extract_fields(data, case_id, question_text):
    """Extract required fields from engine JSON output."""
    if data is None:
        return {
            "id": case_id, "question": question_text, "hexagram_used": "ERROR",
            "use_god": "", "use_god_element": "", "use_god_branch": "",
            "use_god_position": 0, "strength_level": "", "strength_score": 0,
            "verdict": "ERROR", "verdict_score": 0,
            "key_reasoning": "engine_failed", "yingqi": "", "classical_quotes_used": []
        }
    
    tc = data.get("thinking_chain", {})
    
    # step2
    step2 = tc.get("step2_use_god_identification", {})
    selected = step2.get("selected_use_god") or {}
    
    # step3
    step3 = tc.get("step3_strength_analysis", {})
    
    # step5
    step5 = tc.get("step5_synthesis", {})
    timing = step5.get("timing", {})
    yingqi_dates = step5.get("yingqi_dates", {})
    
    # Hexagram names
    orig_hex_info = data.get("original_hexagram", {}) or {}
    orig_hex = orig_hex_info.get("name", "未知")
    changed_hex_data = data.get("changed_hexagram", None)
    changed_hex = ""
    if isinstance(changed_hex_data, dict):
        changed_hex = changed_hex_data.get("name", "")
    hex_used = f"{orig_hex}" + (f"→{changed_hex}" if changed_hex else "")
    
    # reasoning_chain - take key segments (up to 200 chars)
    rc = step5.get("reasoning_chain", [])
    key_reasoning = " | ".join(rc[:3]) if rc else ""
    if len(key_reasoning) > 200:
        key_reasoning = key_reasoning[:200]
    
    # classical_quotes
    quotes = step5.get("classical_quotes", [])
    quotes_used = [f"{q.get('source','')}: {q.get('quote','')}" for q in quotes] if quotes else []
    
    # yingqi: prefer timing.summary_text, fallback to yingqi_dates.summary_text
    yingqi_text = timing.get("summary_text", "") or yingqi_dates.get("summary_text", "")
    
    result = {
        "id": case_id,
        "question": question_text,
        "hexagram_used": hex_used,
        "use_god": step2.get("use_god_category", ""),
        "use_god_element": step2.get("use_god_element", ""),
        "use_god_branch": selected.get("earthly_branch", ""),
        "use_god_position": selected.get("position", 0),
        "strength_level": step3.get("strength_level", ""),
        "strength_score": step3.get("effective_score", 0),
        "verdict": step5.get("verdict", ""),
        "verdict_score": step5.get("final_score", 0),
        "key_reasoning": key_reasoning,
        "yingqi": yingqi_text,
        "classical_quotes_used": quotes_used
    }
    
    return result

def main():
    input_file = r"C:\Users\Lin\.meituan-catpaw\4567030888\skills\liu-yao\data\cases\blind_input.json"
    output_file = r"C:\Users\Lin\.meituan-catpaw\4567030888\skills\liu-yao\data\cases\blind_engine_results.json"
    
    with open(input_file, 'r', encoding='utf-8') as f:
        cases_data = json.load(f)
    
    cases = cases_data["cases"]
    results = []
    
    print(f"Running blind evaluation for {len(cases)} cases...")
    print("=" * 60)
    
    for i, case in enumerate(cases):
        case_id = case["id"]
        inp = case["input"]
        question_text = inp.get("question", case.get("question", ""))
        date_str = inp["date"]
        
        month = extract_month(date_str)
        
        print(f"[{i+1}/{len(cases)}] {case_id}: {case['question']}")
        print(f"  Question: {question_text}, Date: {date_str} -> Month: {month}")
        
        data = run_engine(question_text, 2026, month, 15)
        result = extract_fields(data, case_id, question_text)
        results.append(result)
        
        print(f"  Hexagram: {result['hexagram_used']}")
        print(f"  Verdict: {result['verdict']} | Score: {result['verdict_score']}")
        print(f"  Use God: {result['use_god']}({result['use_god_element']}) at pos {result['use_god_position']}")
        print(f"  Strength: {result['strength_level']} ({result['strength_score']})")
        print()
    
    # Build final output
    output = {
        "evaluator": "engine_blind_v2",
        "engine_version": "liuyao_engine.py",
        "total_cases": len(results),
        "method": "engine_coin_toss",
        "results": results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("=" * 60)
    print(f"Results saved to: {output_file}")
    print(f"Total: {len(results)} cases processed")
    
    # Count verdicts
    verdicts = {}
    for r in results:
        v = r.get("verdict", "error")
        verdicts[v] = verdicts.get(v, 0) + 1
    print(f"Verdict distribution: {verdicts}")

if __name__ == "__main__":
    main()
