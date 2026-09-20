#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
六爻 MCP JSON-RPC 服务器 (Liu Yao MCP JSON-RPC Server)
=====================================================
通过 JSON-RPC 2.0 over stdio 暴露六爻占卜引擎的能力。

方法:
  - liuyao.divinate          — 完整排盘 + 断卦
  - liuyao.quick_reading     — 简化版，仅返回判语 + 推理链
  - liuyao.validate_hexagram — 校验六爻排列是否符合古典规则
  - liuyao.get_classical_quotes — 按格局检索经典引文

仅使用 Python 标准库。
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# =============================================================================
# 确保能导入同目录的引擎模块
# =============================================================================

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from liuyao_engine import (
    coin_toss,
    time_based_hexagram,
    number_based_hexagram,
    build_hexagram_result,
    BAGUA,
    TRIGRAM_LOOKUP,
    HEXAGRAM_LOOKUP,
)

# =============================================================================
# JSON-RPC 2.0 错误码
# =============================================================================

ERROR_PARSE_ERROR = -32700
ERROR_INVALID_REQUEST = -32600
ERROR_METHOD_NOT_FOUND = -32601
ERROR_INVALID_PARAMS = -32602
ERROR_INTERNAL_ERROR = -32603
ERROR_SERVER_ERROR = -32000


# =============================================================================
# 方法实现
# =============================================================================

def _method_divinate(params: dict) -> dict:
    """
    liuyao.divinate — 完整排盘 + 断卦

    参数:
      question  (str, 必填)  求测问题
      method    (str, 可选)  起卦方式: coin/time/number/manual (默认 coin)
      time      (str, 可选)  指定时间 "YYYY-MM-DD HH:MM" (默认当前时间)
      seed      (int, 可选)  随机种子 (仅 coin 模式)
      longitude (float, 选项) 经度用于真太阳时校正
      numbers   (list[int], 可选) 数字起卦三数 [a, b, c]
      yao       (list[int], 可选) 手动六爻 [v1..v6]

    返回: 完整排盘结果 JSON（含思维链）
    """
    question = params.get("question", "")
    if not question:
        raise ValueError("缺少必填参数: question")

    method = params.get("method", "coin")
    time_str = params.get("time", None)
    seed = params.get("seed", None)
    longitude = params.get("longitude", None)
    numbers = params.get("numbers", None)
    yao_values_input = params.get("yao", None)

    # 确定时间
    if time_str:
        try:
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            year, month, day, hour = dt.year, dt.month, dt.day, dt.hour
        except ValueError:
            raise ValueError(f"时间格式错误，应为 'YYYY-MM-DD HH:MM'，收到: {time_str}")
    else:
        now = datetime.now()
        year, month, day, hour = now.year, now.month, now.day, now.hour

    # 真太阳时校正
    if longitude is not None:
        from liuyao_engine import apply_true_solar_time
        info = apply_true_solar_time(year, month, day, hour, longitude)
        hour = info["corrected_hour"]

    # 起卦
    rng = None
    if seed is not None:
        import random
        rng = random.Random(seed)

    if method == "coin":
        yao_values = coin_toss(random_gen=rng)
        method_name = "铜钱摇卦"
    elif method == "time":
        yao_values = time_based_hexagram(year, month, day, hour)
        method_name = "时间起卦"
    elif method == "number":
        if not numbers or len(numbers) != 3:
            raise ValueError("数字起卦需要 numbers 参数（3个整数）")
        yao_values = number_based_hexagram(int(numbers[0]), int(numbers[1]), int(numbers[2]))
        method_name = "数字起卦"
    elif method == "manual":
        if not yao_values_input or len(yao_values_input) != 6:
            raise ValueError("手动起卦需要 yao 参数（6个值，每个为6/7/8/9）")
        yao_values = [int(v) for v in yao_values_input]
        for v in yao_values:
            if v not in (6, 7, 8, 9):
                raise ValueError(f"爻值必须为 6/7/8/9，收到 {v}")
        method_name = "手动指定"
    else:
        raise ValueError(f"不支持的起卦方式: {method}（可选: coin/time/number/manual）")

    # 装卦
    result = build_hexagram_result(
        yao_values, question, method_name,
        year, month, day, hour,
    )

    # 增强分析
    try:
        from classical_analysis import enhance_reading
        enhance_reading(result)
    except ImportError:
        pass

    # 五步思维链
    try:
        from thinking_chain import run_thinking_chain
        chain = run_thinking_chain(result)
    except ImportError:
        chain = None

    # 尝试记录日志
    try:
        from event_logger import log_divination
        log_divination(result, notes="", seed=seed, longitude=longitude)
    except Exception:
        pass

    if chain:
        result["thinking_chain"] = chain
    elif chain is None and "thinking_chain" not in result:
        result["thinking_chain"] = {}

    return result


def _method_quick_reading(params: dict) -> dict:
    """
    liuyao.quick_reading — 简化版断卦

    参数:
      question  (str, 必填) 求测问题
      method    (str, 可选) 起卦方式 (默认 coin)
      time      (str, 可选) 指定时间
      seed      (int, 可选) 随机种子
      numbers   (list[int], 可选) 数字起卦

    返回: { verdict, reasoning, score, hexagram, changed_hexagram, use_god }
    """
    # 复用完整排盘
    full = _method_divinate(params)

    # 确保 full 结果中有 section_advice（趋避建议）
    if "section_advice" not in full:
        try:
            from advice_framework import generate_advice
            tc = full.get("thinking_chain", {})
            step5_inner = tc.get("step5_synthesis", {}) if isinstance(tc, dict) else {}
            verdict = step5_inner.get("verdict", "") if isinstance(step5_inner, dict) else ""
            question = params.get("question", "")
            full["section_advice"] = generate_advice(verdict, question, full)
        except ImportError:
            full["section_advice"] = []

    chain = full.get("thinking_chain", {})
    step2 = chain.get("step2_use_god_identification", {}) if chain else {}
    step5 = chain.get("step5_synthesis", {}) if chain else {}

    oh = full.get("original_hexagram", {})
    ch = full.get("changed_hexagram")

    # 简化推理链
    reasoning_parts = []
    if chain and isinstance(chain, dict):
        step1 = chain.get("step1_situational_reading", {})
        if step1 and isinstance(step1, dict):
            desc = step1.get("description", "")
            if desc:
                reasoning_parts.append(f"观局: {desc}")

        step3 = chain.get("step3_strength_analysis", {})
        if step3 and isinstance(step3, dict):
            lvl = step3.get("strength_level", "")
            desc3 = step3.get("description", "")
            if lvl:
                reasoning_parts.append(f"旺衰: {lvl}")
            if desc3:
                reasoning_parts.append(desc3)

        step4 = chain.get("step4_change_analysis", {})
        if step4 and isinstance(step4, dict):
            net = step4.get("net_effect_description", "")
            if net:
                reasoning_parts.append(f"动变: {net}")

    # quick_reading 自动使用 brief 深度：截断 reasoning 长度
    _BRIEF_LIMIT = 120
    _brief_reasoning = []
    cumulative_len = 0
    for part in reasoning_parts:
        if cumulative_len + len(part) > _BRIEF_LIMIT:
            remaining = _BRIEF_LIMIT - cumulative_len
            if remaining > 20:
                _brief_reasoning.append(part[:remaining] + "…")
            break
        _brief_reasoning.append(part)
        cumulative_len += len(part) + 1

    # 从 engine 结果中取 section_advice（趋避建议）
    section_advice = full.get("section_advice", [])

    return {
        "verdict": step5.get("verdict", "待定") if isinstance(step5, dict) else "待定",
        "reasoning": _brief_reasoning,
        "score": step5.get("final_score", 0.0) if isinstance(step5, dict) else 0.0,
        "confidence": str(step5.get("confidence", "")) if isinstance(step5, dict) else "",
        "hexagram": oh.get("name", ""),
        "hexagram_judgment": oh.get("judgment", ""),
        "upper_trigram": oh.get("upper_trigram", ""),
        "lower_trigram": oh.get("lower_trigram", ""),
        "palace": oh.get("palace", ""),
        "changed_hexagram": ch.get("name", "") if ch else "",
        "changed_lines": ch.get("changed_lines", []) if ch else [],
        "use_god": step2.get("use_god_category", "") if isinstance(step2, dict) else "",
        "use_god_element": step2.get("use_god_element", "") if isinstance(step2, dict) else "",
        "classical_quotes": step5.get("classical_quotes", []) if isinstance(step5, dict) else [],
        "section_advice": section_advice,
        "depth": "brief",
    }


def _method_validate_hexagram(params: dict) -> dict:
    """
    liuyao.validate_hexagram — 校验六爻排列

    参数:
      yao (list[int], 必填) 六个爻值，每个为 6/7/8/9

    返回: { valid, errors, warnings, hexagram_name?, upper?, lower? }
    """
    yao_values = params.get("yao", None)
    errors = []
    warnings = []

    if yao_values is None:
        errors.append("缺少参数: yao")
        return {"valid": False, "errors": errors, "warnings": warnings}

    if not isinstance(yao_values, list) or len(yao_values) != 6:
        actual_len = len(yao_values) if isinstance(yao_values, list) else "N/A"
        errors.append(f"yao 必须为包含6个值的列表，收到 {actual_len} 个元素")
        return {"valid": False, "errors": errors, "warnings": warnings}

    # 校验每个值
    for i, v in enumerate(yao_values):
        if not isinstance(v, int):
            errors.append(f"第{i+1}爻必须是整数，收到 {type(v).__name__}")
        elif v not in (6, 7, 8, 9):
            errors.append(f"第{i+1}爻值 {v} 不合法（必须为6/7/8/9）")

    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings}

    # 提取上下卦三爻
    from liuyao_engine import yao_value_to_lines, find_trigram_name, find_hexagram

    lower_lines, upper_lines = yao_value_to_lines(yao_values)
    upper_name = find_trigram_name(upper_lines)
    lower_name = find_trigram_name(lower_lines)

    if upper_name == "未知":
        errors.append(f"上卦三线 {upper_lines} 无法识别为已知八卦")
    if lower_name == "未知":
        errors.append(f"下卦三线 {lower_lines} 无法识别为已知八卦")

    # 查找本卦
    hex_info = find_hexagram(upper_name, lower_name)
    hex_name = None
    if hex_info:
        hex_name = hex_info[1]
    else:
        errors.append(f"上{upper_name}下{lower_name} 无法在六十四卦中找到")

    # 警告检查
    moving_count = sum(1 for v in yao_values if v in (6, 9))
    if moving_count == 0:
        warnings.append("六爻皆静，无动爻，为静卦")
    elif moving_count > 3:
        warnings.append(f"动爻过多（{moving_count}个），事体不稳")

    result = {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "upper_trigram": upper_name,
        "lower_trigram": lower_name,
    }
    if hex_name:
        result["hexagram_name"] = hex_name
        result["hexagram_sequence"] = hex_info[0] if hex_info else None
        result["judgment"] = hex_info[2] if hex_info else ""
    if moving_count > 0:
        result["moving_yao_positions"] = [i + 1 for i, v in enumerate(yao_values) if v in (6, 9)]

    return result


def _method_get_classical_quotes(params: str | dict) -> list[dict]:
    """
    liuyao.get_classical_quotes — 按格局检索经典引文

    参数:
      pattern (str, 必填) 格局名称，如 "六合卦", "游魂", "用神旺" 等

    返回: [{ pattern, source, quote }, ...]
    """
    # 支持直接传字符串或 dict
    if isinstance(params, dict):
        pattern_input = params.get("pattern", "")
    elif isinstance(params, str):
        pattern_input = params
    else:
        raise ValueError("参数应为字符串或 {pattern: str}")

    pattern_input = pattern_input.strip()
    if not pattern_input:
        raise ValueError("pattern 参数不能为空")

    # 从 thinking_chain 模块导入 QUOTE_DATABASE
    try:
        from thinking_chain import QUOTE_DATABASE
    except ImportError:
        # Fallback: 内嵌最小引文库
        QUOTE_DATABASE = [
            {"pattern": "六合卦", "source": "《卜筮正宗》", "quote": "六合卦者，买卖交通，和合纳财，百事皆吉。"},
            {"pattern": "六冲卦", "source": "《卜筮正宗》", "quote": "六冲卦者，行人不通，散离失群，百事乖张。"},
            {"pattern": "回头克", "source": "《黄金策》", "quote": "动爻变爻，有回头克者，谓之大凶。"},
            {"pattern": "绝处逢生", "source": "《卜筮正宗》", "quote": "用神绝于日辰，若得原神发动来生，谓之绝处逢生，凶中反吉。"},
            {"pattern": "游魂", "source": "《卜筮正宗》", "quote": "游魂行无定，事主忧疑不定，心无归宿。"},
            {"pattern": "归魂", "source": "《卜筮正宗》", "quote": "归魂回故乡，事主有归宿，终有所归。"},
            {"pattern": "妻财持世", "source": "《黄金策》", "quote": "财爻持世，财利必得，然须看旺衰。"},
            {"pattern": "官鬼持世", "source": "《黄金策》", "quote": "官鬼持世，忧疑难释，功名有望。"},
            {"pattern": "用神旺", "source": "《火珠林》", "quote": "用神旺相，如春木之向荣，百事亨通。"},
            {"pattern": "用神休囚", "source": "《火珠林》", "quote": "用神休囚，如秋叶之飘零，百事难成。"},
        ]

    # 模糊匹配
    results = []
    for entry in QUOTE_DATABASE:
        p = entry.get("pattern", "")
        if pattern_input == p or pattern_input in p or p in pattern_input:
            results.append(entry.copy())

    return results


# =============================================================================
# 方法路由表
# =============================================================================

METHODS = {
    "liuyao.divinate": _method_divinate,
    "liuyao.quick_reading": _method_quick_reading,
    "liuyao.validate_hexagram": _method_validate_hexagram,
    "liuyao.get_classical_quotes": _method_get_classical_quotes,
}

# 帮助信息
METHOD_DESCRIPTIONS = {
    "liuyao.divinate": "完整排盘+断卦（支持 coin/time/number/manual 四种起卦方式）",
    "liuyao.quick_reading": "简化版断卦，仅返回判语+推理链",
    "liuyao.validate_hexagram": "校验六爻排列 [6,7,8,9] 是否符合古典规则",
    "liuyao.get_classical_quotes": "按格局名称检索经典引文",
    "liuyao.list_methods": "（内建）列出所有可用方法的帮助信息",
}


def _method_list_methods(params: dict = None) -> dict:
    """列出所有可用方法。"""
    return {
        "methods": {
            name: desc for name, desc in METHOD_DESCRIPTIONS.items()
        }
    }


# 添加 list_methods
METHODS["liuyao.list_methods"] = _method_list_methods


# =============================================================================
# JSON-RPC 请求处理
# =============================================================================

def handle_request(request_data: dict) -> Optional[dict]:
    """
    处理单个 JSON-RPC 请求，返回响应 dict 或 None（通知无响应）。
    """
    # 校验 jsonrpc 版本
    if request_data.get("jsonrpc") != "2.0":
        return {
            "jsonrpc": "2.0",
            "id": request_data.get("id"),
            "error": {
                "code": ERROR_INVALID_REQUEST,
                "message": "Invalid JSON-RPC version (expected '2.0')",
            },
        }

    req_id = request_data.get("id")
    method_name = request_data.get("method", "")
    params = request_data.get("params", {})

    # 校验 method
    if not method_name:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": ERROR_INVALID_REQUEST, "message": "Missing 'method' field"},
        }

    handler = METHODS.get(method_name)
    if handler is None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": ERROR_METHOD_NOT_FOUND,
                "message": f"Method not found: {method_name}",
                "data": {"available_methods": list(METHODS.keys())},
            },
        }

    # 执行方法
    try:
        result = handler(params)
    except ValueError as e:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": ERROR_INVALID_PARAMS, "message": str(e)},
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": ERROR_INTERNAL_ERROR,
                "message": f"Internal error: {type(e).__name__}: {e}",
            },
        }

    # 通知（无 id）不需要响应
    if req_id is None:
        return None

    return {"jsonrpc": "2.0", "id": req_id, "result": result}


# =============================================================================
# 主循环：stdio 传输
# =============================================================================

def run_server():
    """
    从 stdin 读取 JSON-RPC 请求（每行一个），处理后将响应写入 stdout。
    """
    # 名称行响应
    sys.stdout.write("")  # flush buffer
    sys.stdout.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        # 解析请求
        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            error_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": ERROR_PARSE_ERROR,
                    "message": f"JSON parse error: {e}",
                },
            }
            sys.stdout.write(json.dumps(error_resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
            continue

        # 处理请求
        response = handle_request(request)

        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


# =============================================================================
# CLI 入口
# =============================================================================

def main():
    """CLI 入口。"""
    import argparse

    parser = argparse.ArgumentParser(
        description="六爻 MCP JSON-RPC 服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
传输协议: JSON-RPC 2.0 over stdio
  每行一个 JSON 请求，响应同样为一行 JSON。

示例用法:
  # 启动服务（stdio 模式）
  python mcp_server.py

  # 列出可用方法
  python mcp_server.py --list-methods

  # 快速测试：直接执行一次占卜
  python mcp_server.py --test-divinate --question "测投资"

  # 验证六爻排列
  python mcp_server.py --test-validate --yao 7,8,9,7,6,8

  # 获取经典引文
  python mcp_server.py --test-quotes --pattern "六合卦"

JSON-RPC 请求示例:
  {"jsonrpc": "2.0", "id": 1, "method": "liuyao.divinate", "params": {"question": "测投资", "method": "coin"}}
  {"jsonrpc": "2.0", "id": 2, "method": "liuyao.quick_reading", "params": {"question": "测感情"}}
  {"jsonrpc": "2.0", "id": 3, "method": "liuyao.validate_hexagram", "params": {"yao": [7,8,9,7,6,8]}}
  {"jsonrpc": "2.0", "id": 4, "method": "liuyao.get_classical_quotes", "params": {"pattern": "六合卦"}}
        """,
    )

    parser.add_argument(
        "--list-methods",
        action="store_true",
        help="列出所有可用的 JSON-RPC 方法",
    )
    parser.add_argument(
        "--test-divinate",
        action="store_true",
        help="直接运行一次 divinate 测试（不启动服务）",
    )
    parser.add_argument(
        "--test-validate",
        action="store_true",
        help="直接运行一次 validate 测试",
    )
    parser.add_argument(
        "--test-quotes",
        action="store_true",
        help="直接运行一次 quotes 测试",
    )
    parser.add_argument(
        "--question",
        type=str,
        default="测试占卜",
        help="测试用求测问题",
    )
    parser.add_argument(
        "--yao",
        type=str,
        default=None,
        help="测试用六爻值，逗号分隔，如 '7,8,9,7,6,8'",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="六合卦",
        help="测试用格局名称",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="测试用随机种子",
    )

    args = parser.parse_args()

    if args.list_methods:
        print("可用方法:")
        for name, desc in METHOD_DESCRIPTIONS.items():
            print(f"  {name}: {desc}")
        print("\nJSON-RPC 2.0 over stdio 协议。")
        return

    if args.test_divinate:
        result = _method_divinate({
            "question": args.question,
            "method": "coin",
            "seed": args.seed,
        })
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.test_validate:
        yao_values = None
        if args.yao:
            yao_values = [int(x.strip()) for x in args.yao.split(",")]
        result = _method_validate_hexagram({"yao": yao_values})
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.test_quotes:
        result = _method_get_classical_quotes({"pattern": args.pattern})
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 默认：启动 JSON-RPC stdio 服务
    run_server()


if __name__ == "__main__":
    main()
