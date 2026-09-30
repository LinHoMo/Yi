# -*- coding: utf-8 -*-
"""灵棋经·起课（chart 段）—— 纯机械查表，无解读成分。

灵棋法（《靈棋經》书源，data/sources/ling-qi-jing.wikitext.txt）：
  十二枚棋分上/中/下三部（各四枚），掷之数「面」：每部 0..4（全零不成课），
  共 124 课。本段只做：(三部掷数) → 课号 → 查 data/ketables.json 得课名/象/卦注/
  象曰/詩曰——全部逐字录自书源（铁律三），代码零断语字面量。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
for _p in (str(DISC / "scripts"),):
    if _p not in sys.path:
        sys.path.insert(0, _p)

KETABLE = DISC / "data" / "ketables.json"


def load_ketable() -> dict:
    return json.loads(KETABLE.read_text(encoding="utf-8"))


def chart(up: int, mid: int, down: int, question: str = "") -> dict:
    for label, v in (("上", up), ("中", mid), ("下", down)):
        if not isinstance(v, int) or not 0 <= v <= 4:
            raise ValueError(f"{label}部掷数必须是 0..4，收到 {v!r}")
    if up == mid == down == 0:
        raise ValueError("三部全零不成课（《靈棋經》：掷不获面则不立课）；请重新掷棋")
    key = f"{up}-{mid}-{down}"
    table = load_ketable()
    course = (table.get("courses") or {}).get(key)
    if not course:
        raise ValueError(f"课号 {key} 不在课表（课表应含全部非零组合）——数据完整性问题")
    return {
        "discipline": "lingqi",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "question": question,
        "input": {"up": up, "mid": mid, "down": down},
        "key": key,
        "men": course["name"],
        "ke_name": course["name"],
        "xiang": course["xiang"],
        "zhu": course["zhu"],
        "xiangyue": course["xiangyue"],
        "shiyue": course["shiyue"],
        "men_trigger": f"三部掷数：上{up} 中{mid} 下{down} → {key}",
        "men_verified": True,
        "day_kind": "",
        "san_chuan": [],
        "dun_gan": [],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="灵棋经起课（纯机械查表）")
    ap.add_argument("--up", type=int, required=True, help="上掷面数 0..4")
    ap.add_argument("--mid", type=int, required=True, help="中掷面数 0..4")
    ap.add_argument("--down", type=int, required=True, help="下掷面数 0..4")
    ap.add_argument("--question", "-q", default="", help="所问之事")
    ap.add_argument("--out", "-o", help="输出 JSON 路径（缺省打印 stdout）")
    args = ap.parse_args()
    out = chart(args.up, args.mid, args.down, args.question)
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"chart 已写出 → {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
