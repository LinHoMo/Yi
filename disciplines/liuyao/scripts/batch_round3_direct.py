#!/usr/bin/env python3
"""
第3轮确定性盲评 - 直接调用引擎函数（非subprocess）
避免编码和进程间通信问题
"""
import json
import sys
import traceback
import random
from pathlib import Path

# 确保能导入
sys.path.insert(0, str(Path(__file__).parent))

from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain

SKILL_DIR = Path(__file__).parent.parent
BLIND_INPUT = SKILL_DIR / "data" / "cases" / "blind_input.json"
OUTPUT_FILE = SKILL_DIR / "data" / "cases" / "blind_engine_output_v3.json"

# ============================================================
# 64卦名称 → 六爻值映射
# ============================================================
TRIGRAM_YAO = {
    "乾": [7, 7, 7], "坤": [8, 8, 8], "坎": [8, 7, 8], "离": [7, 8, 7],
    "震": [8, 8, 7], "巽": [7, 7, 8], "艮": [7, 8, 8], "兑": [8, 7, 7],
}

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

def hex_to_yao(hex_name, moving=None):
    if hex_name not in HEXAGRAM_TRIGRAMS:
        return None
    upper, lower = HEXAGRAM_TRIGRAMS[hex_name]
    base = TRIGRAM_YAO[lower] + TRIGRAM_YAO[upper]
    if moving:
        for pos in moving:
            if 1 <= pos <= 6:
                idx = pos - 1
                base[idx] = 9 if base[idx] == 7 else 6
    return base

# 预计算的日期
CASE_DATES = {
    "ZS001": {"year": 2024, "month": 6, "day": 3},
    "ZS002": {"year": 2024, "month": 4, "day": 10},
    "ZS003": {"year": 2024, "month": 11, "day": 8},
    "ZS004": {"year": 2024, "month": 8, "day": 19},
    "ZS005": {"year": 2024, "month": 12, "day": 11},
    "ZS006": {"year": 2024, "month": 6, "day": 6},
    "ZS007": {"year": 2024, "month": 2, "day": 4},
    "ZS008": {"year": 2024, "month": 9, "day": 10},
    "ZS009": {"year": 2024, "month": 6, "day": 9},
    "ZS010": {"year": 2024, "month": 10, "day": 19},
    "ZS011": {"year": 2024, "month": 2, "day": 4},
    "ZS012": {"year": 2024, "month": 4, "day": 15},
    "ZS013": {"year": 2024, "month": 4, "day": 16},
    "ZS014": {"year": 2024, "month": 5, "day": 17},
    "ZS015": {"year": 2024, "month": 4, "day": 14},
    "ZS016": {"year": 2024, "month": 3, "day": 17},
    "ZS017": {"year": 2024, "month": 3, "day": 17},
    "ZS018": {"year": 2024, "month": 2, "day": 4},
    "ZS019": {"year": 2024, "month": 4, "day": 15},
    "ZS020": {"year": 2024, "month": 6, "day": 10},
}

CASE_HEXAGRAMS = {
    "ZS001": {"hex": "益", "moving": []},
    "ZS002": None,
    "ZS003": {"hex": "革", "moving": []},
    "ZS004": {"hex": "同人", "moving": []},
    "ZS005": {"hex": "恒", "moving": [4]},
    "ZS006": {"hex": "萃", "moving": [2]},
    "ZS007": {"hex": "姤", "moving": []},
    "ZS008": {"hex": "屯", "moving": [5]},
    "ZS009": {"hex": "恒", "moving": []},
    "ZS010": {"hex": "坤", "moving": []},
    "ZS011": {"hex": "巽", "moving": [3]},
    "ZS012": {"hex": "否", "moving": []},
    "ZS013": {"hex": "姤", "moving": []},
    "ZS014": {"hex": "蹇", "moving": []},
    "ZS015": {"hex": "既济", "moving": []},
    "ZS016": {"hex": "升", "moving": []},
    "ZS017": {"hex": "贲", "moving": []},
    "ZS018": {"hex": "复", "moving": []},
    "ZS019": {"hex": "巽", "moving": [3]},
    "ZS020": {"hex": "蹇", "moving": []},
}


def run_case_direct(case):
    case_id = case["id"]
    question = case.get("question", "古籍案例")
    date_info = CASE_DATES.get(case_id, {"year": 2024, "month": 6, "day": 15})
    hex_info = CASE_HEXAGRAMS.get(case_id)

    try:
        if hex_info is not None:
            yao = hex_to_yao(hex_info["hex"], hex_info.get("moving"))
            if yao is None:
                return {"id": case_id, "question": question, "error": f"Unknown hex: {hex_info['hex']}"}
            h = build_hexagram_result(
                yao_values=yao, question=question, method="manual",
                year=date_info["year"], month=date_info["month"],
                day=date_info["day"], hour=10
            )
            actual_hex = h['original_hexagram']['name']
            if actual_hex != hex_info['hex']:
                return {"id": case_id, "question": question,
                        "error": f"Hex mismatch: expected {hex_info['hex']}, got {actual_hex}"}
        else:
            # Coin mode - use deterministic seed based on case_id
            random.seed(hash(case_id) % 10000)
            yao = [sum(random.choice([2, 3]) for _ in range(3)) for _ in range(6)]
            h = build_hexagram_result(
                yao_values=yao, question=question, method="coin",
                year=date_info["year"], month=date_info["month"],
                day=date_info["day"], hour=10
            )

        tc = run_thinking_chain(h)
        thinking = tc.get("thinking_chain", tc)
        s2 = thinking.get("step2_use_god_identification", {})
        s3 = thinking.get("step3_strength_analysis", {})
        s5 = thinking.get("step5_synthesis", {}) or {}
        
        ch = h.get("changed_hexagram") or {}

        pattern_tags = []
        reasoning_chain = s5.get("reasoning_chain", [])
        for line in reasoning_chain:
            if isinstance(line, str) and "[格局]" in line:
                pattern_tags.append(line)

        return {
            "id": case_id,
            "question": question,
            "hexagram": h['original_hexagram']['name'],
            "moving_lines": [m.get("position") for m in h.get("moving_lines", [])],
            "changed_hexagram": ch.get("name", "?"),
            "use_god_category": s2.get("use_god_category", "?"),
            "use_god_branch": (s2.get("selected_use_god") or {}).get("earthly_branch", "?"),
            "use_god_element": s2.get("use_god_element", "?"),
            "use_god_position": (s2.get("selected_use_god") or {}).get("position", "?"),
            "strength_level": s3.get("strength_level", "?"),
            "strength_score": s3.get("effective_score", "?"),
            "final_score": s5.get("final_score", "?"),
            "verdict": s5.get("verdict", "?"),
            "verdict_desc": s5.get("verdict_description", "?"),
            "special_pattern": s5.get("special_pattern", {}).get("pattern"),
            "yingqi": (s5.get("timing") or {}).get("summary_text", "?"),
            "reasoning_chain": reasoning_chain,
            "pattern_tags": pattern_tags,
            "classical_quotes": h.get("classical_quotes", []),
            "empty_branches": h.get("empty_branches", []),
        }
    except Exception as e:
        tb = traceback.format_exc().split('\n')[-3:]
        return {"id": case_id, "question": question, "error": str(e)[:300], "tb": tb[-1]}


def main():
    with open(BLIND_INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)
    cases = data.get("cases", data) if isinstance(data, dict) else data

    print(f"=== 第3轮确定性盲评（直接调用）：{len(cases)} 条 ===\n")

    results = []
    for i, case in enumerate(cases, 1):
        cid = case["id"]
        print(f"[{i:2d}/{len(cases)}] {cid}: {case.get('question','')[:35]}...", end=" ", flush=True)
        r = run_case_direct(case)
        results.append(r)
        if "error" in r:
            print(f"✗ {r['error'][:80]}")
        else:
            tags = len(r.get('pattern_tags', []))
            sp = r.get('special_pattern', '') or ''
            sp_str = f" 格局={sp[:15]}" if sp else ''
            print(f"卦={r['hexagram']} 用={r['use_god_category']} 断={r['verdict']} 分={r['final_score']} 标={tags}{sp_str}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"engine": "liuyao_engine.py v3 (direct)", "total_cases": len(cases),
                   "method": "original_hexagram + matched_date",
                   "timestamp": "2026-09-19", "cases": results}, f, ensure_ascii=False, indent=2)

    valid = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]
    print(f"\n=== 成功: {len(valid)}/{len(cases)}, 失败: {len(errors)}/{len(cases)} ===")
    if valid:
        verdicts = {}
        for r in valid:
            v = r.get("verdict", "?")
            verdicts[v] = verdicts.get(v, 0) + 1
        print(f"断语分布: {verdicts}")
        avg_tags = sum(len(r.get("pattern_tags", [])) for r in valid) / len(valid)
        print(f"平均格局标签: {avg_tags:.1f}")

        patterns_found = {}
        for r in valid:
            p = r.get("special_pattern")
            if p:
                patterns_found[p] = patterns_found.get(p, 0) + 1
        if patterns_found:
            print(f"特殊格局: {patterns_found}")

    print(f"\n保存: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
