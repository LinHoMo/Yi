#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
六爻古籍数字化检索表（机器可搜索索引）
==========================================
读取 references/classical_digital_index.md 中的 Markdown 表格，
提供按分类(cate)、主题(topic)、关键词(keyword)、出处(source)、
方向(direction)、条件(conditions) 检索的功能。

仅使用 Python 标准库，无外部依赖。
"""

import os
import re
import sys
from typing import List, Dict, Optional

# 索引文件默认路径（相对于本脚本的上级目录中的 references/）
_DEFAULT_INDEX_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "references",
    "classical_digital_index.md",
)


def parse_table_rows(filepath: str = None) -> List[Dict[str, str]]:
    """
    解析 classical_digital_index.md 中的 Markdown 表格，

    Returns:
        每条记录为一个 dict，keys: source, category, topic, quote, interpretation, direction, conditions
    """
    if filepath is None:
        filepath = _DEFAULT_INDEX_PATH

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    rows: List[Dict[str, str]] = []

    # 匹配表格数据行 (跳过表头和分隔行)
    lines_buf = content.splitlines()
    in_table = False
    header_line = None

    for line in lines_buf:
        stripped = line.strip()

        # 检测表头行
        if stripped.startswith("|") and "出处" in stripped and "分类" in stripped:
            in_table = True
            header_line = stripped
            continue

        # 检测分隔行
        if in_table and re.match(r"^\|[\s\-:|]+\|$", stripped):
            continue

        # 解析数据行
        if in_table and stripped.startswith("|") and "出处" not in stripped:
            cells = [cell.strip() for cell in stripped.split("|")]
            # split("|") produces empty strings at start/end due to leading/trailing |
            cells = [c for c in cells if c != ""]

            if len(cells) >= 7:
                rows.append({
                    "source": cells[0],          # 出处
                    "category": cells[1],        # 分类
                    "topic": cells[2],           # 主题
                    "quote": cells[3],           # 古文
                    "interpretation": cells[4],  # 今译
                    "direction": cells[5],        # 方向
                    "conditions": cells[6],      # 条件
                })

        # 检测表格结束（非表格行且有内容）
        elif in_table and not stripped.startswith("|"):
            if stripped and not stripped.startswith("#"):
                in_table = False

    return rows


def search_classical_index(
    category: Optional[str] = None,
    topic: Optional[str] = None,
    keyword: Optional[str] = None,
    source: Optional[str] = None,
    direction: Optional[str] = None,
    conditions: Optional[str] = None,
    filepath: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    搜索六爻古籍数字化检索表。

    Args:
        category: 精确或部分匹配分类（如 "六亲持世"）
        topic:   精确或部分匹配主题（如 "父母持世"）
        keyword: 全文模糊搜索（搜索所有字段）
        source:  精确或部分匹配出处（如 "黄金策"、"增删易"、"卜筮正宗"、"火珠林"）
        direction: 精确匹配方向（"positive"、"negative"、"neutral"、"modifier"）
        conditions: 部分匹配条件列
        filepath: 手动指定索引文件路径

    Returns:
        匹配的条目列表，每个元素为 dict。
        如果没有提供任何搜索参数，返回全部条目。

    Example:
        >>> results = search_classical_index(category="六亲持世")
        >>> for r in results:
        ...     print(f"[{r['source']}] {r['topic']}: {r['interpretation']}")
    """
    rows = parse_table_rows(filepath)

    if not any([category, topic, keyword, source, direction, conditions]):
        return rows

    results: List[Dict[str, str]] = []

    for row in rows:
        match = True

        # 分类：部分匹配（不区分大小写）
        if category is not None:
            if category.lower() not in row["category"].lower():
                match = False

        # 主题：部分匹配
        if match and topic is not None:
            if topic.lower() not in row["topic"].lower():
                match = False

        # 出处：部分匹配
        if match and source is not None:
            if source.lower() not in row["source"].lower():
                match = False

        # 方向：精确匹配
        if match and direction is not None:
            if direction != row["direction"]:
                match = False

        # 条件：部分匹配
        if match and conditions is not None:
            if conditions.lower() not in row["conditions"].lower():
                match = False

        # 全文关键词：模糊搜索所有字段
        if match and keyword is not None:
            all_text = " ".join(row.values())
            if keyword.lower() not in all_text.lower():
                match = False

        if match:
            results.append(row)

    return results


def list_categories(filepath: Optional[str] = None) -> List[str]:
    """列出索引中包含的所有唯一分类"""
    rows = parse_table_rows(filepath)
    return sorted(set(row["category"] for row in rows))


def list_sources(filepath: Optional[str] = None) -> List[str]:
    """列出索引中包含的所有唯一出处"""
    rows = parse_table_rows(filepath)
    return sorted(set(row["source"] for row in rows))


def list_topics(filepath: Optional[str] = None) -> List[str]:
    """列出索引中包含的所有主题（唯一值）"""
    rows = parse_table_rows(filepath)
    return sorted(set(row["topic"] for row in rows))


def format_results(results: List[Dict[str, str]]) -> str:
    """将搜索结果格式化为可读的文本"""
    if not results:
        return "(无匹配结果)"

    lines = []
    for i, row in enumerate(results, 1):
        lines.append(f"[{i}] {row['source']} | {row['category']} | {row['topic']}")
        lines.append(f"    古文：{row['quote']}")
        lines.append(f"    今译：{row['interpretation']}")
        lines.append(f"    方向：{row['direction']} | 条件：{row['conditions']}")
        lines.append("")

    return "\n".join(lines)


# =============================================================================
# 命令行接口
# =============================================================================

def _cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="六爻古籍数字化检索表 — 搜索四大经典条文",
    )
    parser.add_argument("--category", "-c", type=str, help="分类关键词")
    parser.add_argument("--topic", "-t", type=str, help="主题关键词")
    parser.add_argument("--keyword", "-k", type=str, help="全文模糊搜索关键词")
    parser.add_argument("--source", "-s", type=str, help="出处关键词")
    parser.add_argument("--direction", "-d", type=str, choices=["positive", "negative", "neutral", "modifier"], help="吉凶方向")
    parser.add_argument("--conditions", type=str, help="适用条件关键词")
    parser.add_argument("--list-categories", action="store_true", help="列出所有分类")
    parser.add_argument("--list-sources", action="store_true", help="列出所有出处")
    parser.add_argument("--list-topics", action="store_true", help="列出所有主题")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")

    args = parser.parse_args()

    if args.list_categories:
        cats = list_categories()
        print("所有分类：")
        for c in cats:
            print(f"  - {c}")
        return

    if args.list_sources:
        sources = list_sources()
        print("所有出处：")
        for s in sources:
            print(f"  - {s}")
        return

    if args.list_topics:
        topics = list_topics()
        print("所有主题：")
        for t in topics:
            print(f"  - {t}")
        return

    results = search_classical_index(
        category=args.category,
        topic=args.topic,
        keyword=args.keyword,
        source=args.source,
        direction=args.direction,
        conditions=args.conditions,
    )

    if args.json:
        import json
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"匹配到 {len(results)} 条记录：\n")
        print(format_results(results))


if __name__ == "__main__":
    _cli()
