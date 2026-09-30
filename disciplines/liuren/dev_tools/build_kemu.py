# -*- coding: utf-8 -*-
"""课目诀表提取器（一次性数据构建）。

源：data/sources/liu-ren-da-quan.wikitext.txt 卷一「课目」（行 2694–2818），
六十五条课目诀逐条一行：课名（两字）+ 诀文 + 序号（汉字数字）+ 卦名注记。
产物 data/kemu.json：65 条全量登记（verse 逐字），implemented 标记首批判据。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
SRC = DISC.parents[1] / "data" / "sources" / "liu-ren-da-quan.wikitext.txt"
OUT = DISC / "data" / "kemu.json"

FIRST = "别责无克三课备"
LAST = "六纯十难兼物类"

CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7,
          "八": 8, "九": 9, "十": 10}
ORDINAL_RE = re.compile(r"([一二三四五六七八九十]{1,3})([\u4e00-\u9fff]{1,3})$")


def cn_to_int(s: str) -> int | None:
    if s == "十":
        return 10
    if "十" in s:
        a, _, b = s.partition("十")
        hi = CN_NUM.get(a, 1) if a else 1
        lo = CN_NUM.get(b, 0) if b else 0
        return hi * 10 + lo
    return CN_NUM.get(s)


def main() -> int:
    text = SRC.read_text(encoding="utf-8")
    seg = text[text.index(FIRST): text.index(LAST) + len(LAST)]

    # 表实为第 7–65 条：1–6（元首/重审/知一/涉害/遥克/昴星）即九宗门前六门，
    # 判据已落 jiuzongmen.py，课目表从别责（第 7）起。
    expected_names = {"别责","八专","伏吟","返吟","三光","三阳","三奇","六仪","时太",
        "龙德","官爵","富贵","轩盖","铸印","斲轮","引从","亨通","繁昌","繁华","德庆",
        "合欢","和美","斩关","闭口","游子","三交","乱首","赘胥","冲破","淫泆","芜淫",
        "解离","孤寡","地盘","度厄","无禄","迍福","侵害","刑伤","二烦","天祸",
        "天狱","天寇","天网","魄化","三阴","龙战","死奇","灾厄","殃咎","九丑","鬼墓",
        "励德","盘珠","全局","玄胎","联珠","六纯"}
    entries = []
    for raw in seg.splitlines():
        line = raw.strip().rstrip("。").strip()
        if len(line) < 6:
            continue
        entry = {"name": line[:2], "verse": line}
        if entry["name"] not in expected_names:
            # 书源个别行编码二次转码（如「地盘为孤」行）：尝试还原；还原不出
            # 则 verse 置空并标 damaged——引文纪律不容损坏文本冒充原文
            try:
                fixed = line.encode("gbk").decode("utf-8").rstrip("。").strip()
            except (UnicodeEncodeError, UnicodeDecodeError):
                fixed = ""
            if fixed[:2] in expected_names:
                entry = {"name": fixed[:2], "verse": fixed}
            else:
                entry = {"name": "?", "verse": None, "damaged": True,
                         "raw": line[:60]}
        entries.append(entry)
    entries = [e for e in entries if e["name"] in expected_names | {"?"}]

    implemented = {"亨通", "三交", "乱首", "赘胥", "冲破", "轩盖", "斲轮", "引从"}
    for e in entries:
        e["implemented"] = e["name"] in implemented

    OUT.write_text(json.dumps({
        "schema": "yi-liuren-kemu/1",
        "_comment": [
            "六壬大全 卷一「课目」诀表（第 7–65 条；1–6 即九宗门前六门，判据见",
            "scripts/jiuzongmen.py）。verse 逐字（铁律三：引文可回指）。",
            "implemented=true 为已落机械判据（scripts/kemu.py）；其余仅登记诀文，",
            "判据落地前不得在 analyze 中输出该课目名（不写占位识别）。",
        ],
        "entries": entries,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"课目 {len(entries)} 条（书源该段实有条行数，覆盖第 7–65 号，个别号同行并注）；"
          f"首批实现 {sum(e['implemented'] for e in entries)} 条："
          f"{[e['name'] for e in entries if e['implemented']]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
