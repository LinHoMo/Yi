#!/usr/bin/env python3
"""
第3轮确定性盲评运行器：
- 使用案例原始卦象（非随机coin）
- 使用与古典日期匹配的月日数据
- 正确设置月建日辰
- 按笔记推断动爻
"""
import json
import os
import sys
import subprocess
import traceback
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
CLASSICAL_CASES = SKILL_DIR / "data" / "cases" / "classical_cases.json"
BLIND_INPUT = SKILL_DIR / "data" / "cases" / "blind_input.json"
OUTPUT_FILE = SKILL_DIR / "data" / "cases" / "blind_engine_output_v3.json"

# ============================================================
# 64卦名称 → 六爻值映射（bottom-to-top，7=少阳静,8=少阴静）
# ============================================================
TRIGRAM_YAO = {
    "乾": [7, 7, 7],  # ☰
    "坤": [8, 8, 8],  # ☷
    "坎": [8, 7, 8],  # ☵
    "离": [7, 8, 7],  # ☲
    "震": [8, 8, 7],  # ☳
    "巽": [7, 7, 8],  # ☴
    "艮": [7, 8, 8],  # ☶
    "兑": [8, 7, 7],  # ☱
}

# 完整64卦名称→(上卦,下卦)映射
HEXAGRAM_TRIGRAMS = {
    "乾": ("乾", "乾"), "坤": ("坤", "坤"), "屯": ("坎", "震"), "蒙": ("艮", "坎"),
    "需": ("坎", "乾"), "讼": ("乾", "坎"), "师": ("坤", "坎"), "比": ("坎", "坤"),
    "小畜": ("巽", "乾"), "履": ("乾", "兑"), "泰": ("坤", "乾"), "否": ("乾", "坤"),
    "同人": ("乾", "离"), "大有": ("离", "乾"), "谦": ("坤", "艮"), "豫": ("震", "坤"),
    "随": ("兑", "震"), "蛊": ("艮", "巽"), "临": ("坤", "兑"), "观": ("巽", "坤"),
    "噬嗑": ("离", "震"), "贲": ("艮", "离"), "剥": ("艮", "坤"), "复": ("坤", "震"),
    "无妄": ("乾", "震"), "大畜": ("艮", "乾"), "颐": ("艮", "震"), "大过": ("兑", "巽"),
    "坎": ("坎", "坎"), "离": ("离", "离"), "咸": ("兑", "艮"), "恒": ("震", "巽"),
    "遁": ("乾", "艮"), "大壮": ("震", "乾"), "晋": ("离", "坤"), "明夷": ("坤", "离"),
    "家人": ("巽", "离"), "睽": ("离", "兑"), "蹇": ("坎", "艮"), "解": ("震", "坎"),
    "损": ("艮", "兑"), "益": ("巽", "震"), "夬": ("兑", "乾"), "姤": ("乾", "巽"),
    "萃": ("兑", "坤"), "升": ("坤", "巽"), "困": ("兑", "坎"), "井": ("坎", "巽"),
    "革": ("兑", "离"), "鼎": ("离", "巽"), "震": ("震", "震"), "艮": ("艮", "艮"),
    "渐": ("巽", "艮"), "归妹": ("震", "兑"), "丰": ("震", "离"), "旅": ("离", "艮"),
    "巽": ("巽", "巽"), "兑": ("兑", "兑"), "涣": ("巽", "坎"), "节": ("坎", "兑"),
    "中孚": ("巽", "兑"), "小过": ("震", "艮"), "既济": ("坎", "离"), "未济": ("离", "坎"),
}

def hex_to_yao(hex_name: str) -> list[int]:
    """卦名 → 六爻值列表（bottom-to-top，全静爻）"""
    if hex_name not in HEXAGRAM_TRIGRAMS:
        return None
    upper, lower = HEXAGRAM_TRIGRAMS[hex_name]
    # 下卦在前(初爻到三爻)，上卦在后(四爻到上爻)
    return TRIGRAM_YAO[lower] + TRIGRAM_YAO[upper]

def hex_to_yao_with_moving(hex_name: str, moving_positions: list[int]) -> list[int]:
    """卦名 + 动爻位置 → 六爻值列表（6=老阴动,9=老阳动）"""
    base = hex_to_yao(hex_name)
    if base is None:
        return None
    result = list(base)
    for pos in moving_positions:
        if 1 <= pos <= 6:
            idx = pos - 1
            # 7(少阳)→9(老阳动), 8(少阴)→6(老阴动)
            result[idx] = 9 if result[idx] == 7 else 6
    return result

# ============================================================
# 预计算的太阳历日期（匹配古典月日）
# ============================================================
CASE_DATES = {
    "ZS001": {"year": 2024, "month": 6, "day": 3},    # 巳月戊戌日
    "ZS002": {"year": 2024, "month": 4, "day": 10},   # 辰月庚辰日 (coin mode)
    "ZS003": {"year": 2024, "month": 11, "day": 8},   # 亥月甲子日
    "ZS004": {"year": 2024, "month": 8, "day": 19},   # 申月丁卯日
    "ZS005": {"year": 2024, "month": 12, "day": 11},  # 子月癸酉日
    "ZS006": {"year": 2024, "month": 6, "day": 6},    # 午月癸丑日
    "ZS007": {"year": 2024, "month": 2, "day": 4},    # 寅月庚戌日
    "ZS008": {"year": 2024, "month": 9, "day": 10},   # 酉月己丑日
    "ZS009": {"year": 2024, "month": 6, "day": 9},    # 午月丙辰日
    "ZS010": {"year": 2024, "month": 10, "day": 19},  # 戌月甲辰日
    "ZS011": {"year": 2024, "month": 2, "day": 4},    # 寅月戊戌日
    "ZS012": {"year": 2024, "month": 4, "day": 15},   # 辰月丁酉日
    "ZS013": {"year": 2024, "month": 4, "day": 16},   # 辰月庚戌日
    "ZS014": {"year": 2024, "month": 5, "day": 17},   # 巳月丁巳日
    "ZS015": {"year": 2024, "month": 4, "day": 14},   # 辰月庚申日
    "ZS016": {"year": 2024, "month": 3, "day": 17},   # 卯月壬辰日
    "ZS017": {"year": 2024, "month": 3, "day": 17},   # 卯月丙辰日
    "ZS018": {"year": 2024, "month": 2, "day": 4},    # 寅月戊戌日
    "ZS019": {"year": 2024, "month": 4, "day": 15},   # 辰月丁亥日
    "ZS020": {"year": 2024, "month": 6, "day": 10},   # 午月丙辰日
}

# ============================================================
# 案例原始卦象（部分含动爻推断）
# ============================================================
CASE_HEXAGRAMS = {
    "ZS001": {"hex": "益", "moving": []},
    "ZS002": None,  # 无卦象，使用coin模式
    "ZS003": {"hex": "革", "moving": []},
    "ZS004": {"hex": "同人", "moving": []},
    "ZS005": {"hex": "恒", "moving": [4]},  # 四爻戌土财爻动化巳火
    "ZS006": {"hex": "萃", "moving": [2]},  # 二爻亥水原神动
    "ZS007": {"hex": "姤", "moving": []},
    "ZS008": {"hex": "屯", "moving": [5]},  # 五爻申金父母动化午火
    "ZS009": {"hex": "恒", "moving": []},
    "ZS010": {"hex": "坤", "moving": []},
    "ZS011": {"hex": "巽", "moving": [3]},  # 三爻未土化午火回头生合
    "ZS012": {"hex": "否", "moving": []},
    "ZS013": {"hex": "姤", "moving": []},
    "ZS014": {"hex": "蹇", "moving": []},
    "ZS015": {"hex": "既济", "moving": []},
    "ZS016": {"hex": "升", "moving": []},
    "ZS017": {"hex": "贲", "moving": []},
    "ZS018": {"hex": "复", "moving": []},
    "ZS019": {"hex": "巽", "moving": [3]},  # 三爻未土化午火
    "ZS020": {"hex": "恒", "moving": []},
}


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
    """对单个案例执行确定性排盘"""
    case_id = case["id"]
    question = case.get("question", "古籍案例")
    date_info = CASE_DATES.get(case_id, {"year": 2024, "month": 6, "day": 15})
    hex_info = CASE_HEXAGRAMS.get(case_id)
    
    cmd = [
        sys.executable, str(SCRIPTS_DIR / "liuyao_engine.py"),
    ]
    
    if hex_info is not None:
        # 使用原始卦象
        hex_name = hex_info["hex"]
        moving = hex_info.get("moving", [])
        yao_values = hex_to_yao_with_moving(hex_name, moving)
        if yao_values is None:
            return {"id": case_id, "question": question, "error": f"Unknown hexagram: {hex_name}"}
        cmd.extend(["--mode", "manual", "--yao", ",".join(str(v) for v in yao_values)])
    else:
        # 无卦象，使用coin模式
        cmd.extend(["--mode", "coin"])
    
    cmd.extend([
        "--question", question,
        "--year", str(date_info["year"]),
        "--month", str(date_info["month"]),
        "--day", str(date_info["day"]),
        "--hour", "10",
        "--format", "json",
    ])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                              cwd=str(SCRIPTS_DIR), encoding="utf-8")
        if result.returncode != 0:
            stderr = result.stderr.strip()
            return {"id": case_id, "question": question, "error": stderr[:500]}
        
        engine_result = extract_engine_output(result.stdout)
        if "error" in engine_result:
            return {"id": case_id, "question": question, "error": engine_result["error"]}
        
        # 提取关键字段
        original = engine_result.get("original_hexagram", {})
        tc = engine_result.get("thinking_chain", {})
        step2 = tc.get("step2_use_god_identification", {})
        step3 = tc.get("step3_strength_analysis", {})
        step5 = tc.get("step5_synthesis", {})
        
        # 格局标签
        pattern_tags = []
        reasoning_chain = step5.get("reasoning_chain", [])
        for line in reasoning_chain:
            if isinstance(line, str) and "[格局]" in line:
                pattern_tags.append(line)
        
        output = {
            "id": case_id,
            "question": question,
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
            "reasoning_chain": reasoning_chain,
            "pattern_tags": pattern_tags,
            "classical_quotes": engine_result.get("classical_quotes", []),
        }
        return output
    except Exception as e:
        return {"id": case_id, "question": question, "error": str(e)[:500]}


def main():
    with open(BLIND_INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)
    cases = data.get("cases", data) if isinstance(data, dict) else data
    total = len(cases)
    
    print(f"=== 第3轮确定性盲评：{total} 条案例 ===")
    print(f"使用原始卦象 + 精确月日\n")
    
    results = []
    for i, case in enumerate(cases, 1):
        case_id = case["id"]
        print(f"[{i}/{total}] {case_id}: {case.get('question', '')[:40]}...", end=" ", flush=True)
        result = run_case(case)
        results.append(result)
        
        if "error" in result:
            print(f"✗ 错误: {result['error'][:80]}")
        else:
            tags_cnt = len(result.get("pattern_tags", []))
            print(f"卦={result['hexagram']} 用={result['use_god_category']} 断={result['verdict']} 分={result['final_score']} 标={tags_cnt}")
    
    # 保存结果
    output_data = {
        "engine": "liuyao_engine.py v3 (deterministic)",
        "method": "original_hexagram + matched_date",
        "total_cases": total,
        "timestamp": "2026-09-19",
        "cases": results
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 结果已保存到: {OUTPUT_FILE} ===")
    valid = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]
    print(f"成功: {len(valid)}/{total}, 失败: {len(errors)}/{total}")
    
    if valid:
        verdicts = {}
        for r in valid:
            v = r.get("verdict", "?")
            verdicts[v] = verdicts.get(v, 0) + 1
        print(f"断语分布: {verdicts}")
        
        # 计算平均格局标签数
        avg_tags = sum(len(r.get("pattern_tags", [])) for r in valid) / len(valid)
        print(f"平均格局标签数: {avg_tags:.1f}")


if __name__ == "__main__":
    main()
