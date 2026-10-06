# -*- coding: utf-8 -*-
"""把 data/tiaohou_quotes.json（键=月序+日干）同步进引擎表 TIAO_HOU（键=月支+日干）。

引擎表是静态字面量、data 是产物，两者会漂移，故本脚本做唯一同步入口：
  python dev_tools/sync_tiaohou_engine.py          # 写盘
  python dev_tools/sync_tiaohou_engine.py --check  # 只校验是否已同步（CI/gate 用）

口径：只同步 main 非空的格；assist 空串如实写空串。注释里的格数随之重算，
不手写——避免注释与实际条数长期不一致。
"""
import argparse
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "core"))
# 干支序列唯一真值源在 core（tools/check.py 第 6 项门禁会拦 disciplines 下复制字面量）
from yishu_core.symbols import HEAVENLY_STEMS  # noqa: E402

DATA = ROOT / "disciplines" / "ming" / "data" / "tiaohou_quotes.json"
ENGINE = ROOT / "core" / "yishu_core" / "ming_tables.py"

BRANCH_OF_MONTH = {
    1: "寅", 2: "卯", 3: "辰", 4: "巳", 5: "午", 6: "未",
    7: "申", 8: "酉", 9: "戌", 10: "亥", 11: "子", 12: "丑",
}
STEMS = "".join(HEAVENLY_STEMS)  # HEAVENLY_STEMS 是 list，展平后当字符串用
_ORDER = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]

START = "TIAO_HOU: dict[str, dict[str, dict[str, str]]] = {"
# 引擎表块结束：下一个顶层 `}` （缩进 0）
BLOCK_RE = re.compile(
    r"(?P<head>^TIAO_HOU[^\n]*\{\n)(?P<body>.*?)(?P<tail>^\}\n)", re.S | re.M
)


def build_block(table: dict) -> tuple[str, int, int]:
    by_branch: dict[str, dict[str, dict[str, str]]] = {}
    season = 0
    for mo in range(1, 13):
        br = BRANCH_OF_MONTH[mo]
        for st in STEMS:
            v = table.get(f"{mo}{st}") or {}
            if not v.get("main"):
                continue
            by_branch.setdefault(br, {})[st] = {
                "main": v["main"], "assist": v.get("assist") or "",
            }
            if (v.get("via") or "").endswith("(season)"):
                season += 1
    lines = []
    for br in _ORDER:
        cells = by_branch.get(br)
        if not cells:
            continue
        lines.append(f'    "{br}": {{')
        for st in STEMS:
            if st in cells:
                c = cells[st]
                lines.append(f'        "{st}": {{"main": "{c["main"]}", "assist": "{c["assist"]}"}},')
        lines.append("    },")
    total = sum(len(v) for v in by_branch.values())
    return "\n".join(lines) + "\n", total, season


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验是否已同步")
    args = ap.parse_args()

    table = json.loads(DATA.read_text(encoding="utf-8"))
    body, total, season = build_block(table)
    src = ENGINE.read_text(encoding="utf-8")

    m = BLOCK_RE.search(src)
    if not m:
        print("× 未在 ming_tables.py 定位到 TIAO_HOU 块", file=sys.stderr)
        return 2

    new_src = src[: m.start("body")] + body + src[m.end("body") :]

    # 注释里的格数与兜底数随实际重算，避免注释长期失真。
    # 只改数字，措辞不动（措辞归文档层管，此处只做机械同步）。
    new_src = re.sub(
        r"（(\d+)/120 格",
        f"（{total}/120 格",
        new_src,
    )
    new_src = re.sub(
        r"其中 \d+ 格为季节总论句兜底",
        f"其中 {season} 格为季节总论句兜底",
        new_src,
    )

    if new_src == src:
        print(f"√ TIAO_HOU 已同步（{total} 格，季节兜底 {season} 格）")
        return 0
    if args.check:
        cur = ast.literal_eval("{" + m.group("body") + "}")
        new = ast.literal_eval("{" + body + "}")
        diff = [k for k in set(cur) | set(new) if cur.get(k) != new.get(k)]
        # 格数 = 各月支下日干条目之和（不是 top-level 月支键数）
        n_cur = sum(len(v) for v in cur.values())
        n_new = sum(len(v) for v in new.values())
        print(
            f"× TIAO_HOU 未同步：应为 {total} 格（当前 {n_cur} 格），差异 {len(diff)} 个月支",
            file=sys.stderr,
        )
        for br in diff:
            print(f"    {br}: {cur.get(br)}  →  {new.get(br)}", file=sys.stderr)
        return 1
    ENGINE.write_text(new_src, encoding="utf-8")
    print(f"√ 已同步 TIAO_HOU：{total} 格（季节兜底 {season} 格）→ {ENGINE.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
