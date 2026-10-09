# -*- coding: utf-8 -*-
"""《周易尚占》卷下八宫立成表 → core 纳甲/八宫表 逐格对拍（**外部真值源**）。

【OPT-zhouyi_shangzhan_dz-01，2026-10-07 新增】

为什么需要这个门：core 的 `NAJIA_STEMS` / `NAJIA_BRANCHES` / `EIGHT_PALACES`
目前**没有独立书源对拍**——它若被误改，只能靠现有案例读数事后发现，而读数
未必覆盖全部 64 卦的纳甲（AGENTS.md §四.5：改静态表须逐格对拍报
「新增 N/变空 N/改值 N」）。本书卷下 L924-L1395 的「六十四卦立成表」
逐卦给出上爻→初爻的**天干纳甲**与**世应**，是 core 纳甲表的独立外部证据。

本脚本**只读、只报差异**，不做任何修复（范式同
`disciplines/ming/dev_tools/diff_tiaohou_vs_head.py`）：
  · 书源侧：从 `data/sources/zhouyi_shangzhan_dz.dz.txt` 逐行解析卦名与其六爻纳甲干支；
  · 引擎侧：由 `core.yishu_core.symbols` 的 `HEXAGRAM_TRIGRAMS`（卦→内外卦）
    ＋ `NAJIA_STEMS`（宫→纳甲干）＋ `NAJIA_BRANCHES`（宫→六爻地支）**独立重算**六爻干支；
  · 逐格比对，报「一致 N 格 / 改值 N 格 / 变空 N 格」，改值与变空**逐条列出**。

用法：
    python dev_tools/diff_shangzhan_vs_core.py            # 人读报告，EXIT=0/1
    python dev_tools/diff_shangzhan_vs_core.py --json     # 机器读，供门禁挂接

退出码：0 全同；1 有差异；2 书源缺失/解析不出卦（视为门的输入坏了，须报而非静默放过）。
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "core"))

from yishu_core.symbols import (  # noqa: E402
    EIGHT_PALACES,
    HEXAGRAM_TRIGRAMS,
    NAJIA_BRANCHES,
    NAJIA_STEMS,
)

SRC = ROOT / "data" / "sources" / "zhouyi_shangzhan_dz.dz.txt"
SCAN_FROM, SCAN_TO = 924, 1395      # 卷下八宫立成表区间（书源 L924 表头）
GZ = r"[子丑寅卯辰巳午未申酉戌亥]"

# 卦名行：<卦名><空白><天干><地支><五行> …（立成表每卦首行）
RE_GUA_ROW = re.compile(
    r"^[　\s]*(?P<name>[一-龥]{2,5})\s+"
    r"(?P<cells>(?:[甲乙丙丁戊己庚辛壬癸]" + GZ + r"[金木水火土]\s*){6})"
)
RE_POS_NAME = {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}
# 八纯卦全称「X为Y」→ 单字卦名
RE_PURE = re.compile(r"^(乾|坎|艮|震|巽|离|坤|兑)为[天地雷风水火山泽]$")

# ── 已知**书源形讹**豁免表（不是「改数据迎读数」，而是登记书源自身的错字）──
# 源 L954「火天大有」行：己巳火 / **乙未**土 / 己酉金 / 甲辰土 / 甲寅木 / 甲子水
# 大有＝离上乾下，离之外卦纳甲干为「己」，故四/五/上三爻皆当从「己」；
# 该行五爻作「乙未」，与同行上爻「己巳」、四爻「己酉」自相矛盾，
# 且与其余 63 卦「同卦同干」之例（乾宫诸卦外卦皆甲/壬…）全异 —— **书源形讹**。
# 处理：core **不动**（core 的己未 由 NAJIA_STEMS 离 outer=己 推出，自洽）；
# 本门把该格列入豁免并**在报告里显式打印**，不静默吞掉（AGENTS.md §四.8：
# 全绿的新门先怀疑、再证明——豁免必须可见）。
SOURCE_TYPOS: dict[str, dict] = {
    "火天大有": {
        "五爻": {"书源": "乙未", "应为": "己未", "src": "L954",
                 "理由": "离之外卦纳甲干为「己」，四爻书源作「己酉」、上爻作「己巳」，"
                         "唯五爻作「乙未」，同行自相矛盾且与其余卦例皆异，判为形讹"},
    },
}


def parse_source() -> dict:
    """书源 → {卦名: {爻位: 纳音干支原文}}；同时记行号便于回指。"""
    if not SRC.exists():
        return {}
    out: dict[str, dict] = {}
    for idx, raw in enumerate(SRC.read_text(encoding="utf-8").split("\n"), start=1):
        if not (SCAN_FROM <= idx <= SCAN_TO):
            continue
        m = RE_GUA_ROW.match(raw)
        if not m:
            continue
        cells = re.findall(r"[甲乙丙丁戊己庚辛壬癸]" + GZ + r"[金木水火土]", m.group("cells"))
        if len(cells) != 6:
            continue
        name = m.group("name")
        # 书中自上而下排（上爻→初爻），转成爻位键
        row = {RE_POS_NAME[7 - i]: c[:2] for i, c in enumerate(cells, start=1)}
        row["_src"] = f"L{idx}"
        out[name] = row
    return out


def _strip_prefix(gua_name: str) -> str:
    """书源卦名 → core 的简称（两字卦名）。

    core.HEXAGRAM_TRIGRAMS 用**简称**（如「革」「泰」「大畜」），书源用**全称**
    （「泽火革」「天地否」「山天大畜」）。两类需分别处理：
      · 八纯卦「X为Y」（乾为天/艮为山…）→ 取「X」；
      · 其余全称去掉卦宫前缀字即得简称——**按 core 表反查唯一命中**，
        不建别名表（那是第二份卦名真值源，违反 AGENTS.md §二）；命中不唯一即判失败。
    """
    if gua_name in HEXAGRAM_TRIGRAMS:
        return gua_name
    m = RE_PURE.match(gua_name)          # 八纯卦：艮为山 → 艮
    if m:
        return m.group(1) if m.group(1) in HEXAGRAM_TRIGRAMS else ""
    cand = [k for k in HEXAGRAM_TRIGRAMS if k != gua_name and gua_name.endswith(k)]
    return cand[0] if len(cand) == 1 else ""


def engine_ganzhi(hex_name: str) -> dict | None:
    """由 core 三表独立重算一卦六爻干支；结构不支持则 None。"""
    key = _strip_prefix(hex_name)
    if not key:
        return None
    tri = HEXAGRAM_TRIGRAMS.get(key)
    if not tri:
        return None
    # core.HEXAGRAM_TRIGRAMS 的元组是 **(上卦, 下卦)**——实测：革=泽火革→('兑','离')、
    # 泰=地天泰→('坤','乾')，均以上卦在前。（曾在此写反导致 336 格全报改值，
    # 属脚本自身缺陷、非 core 缺陷；铁律四.8：全红先怀疑自己的门。）
    upper, lower = tri[0], tri[1]
    lb = (NAJIA_BRANCHES.get(lower) or {}).get("inner") or []
    ub = (NAJIA_BRANCHES.get(upper) or {}).get("outer") or []
    if len(lb) != 3 or len(ub) != 3:
        return None
    lower_stem = (NAJIA_STEMS.get(lower) or {}).get("inner") or ""
    upper_stem = (NAJIA_STEMS.get(upper) or {}).get("outer") or ""
    if not lower_stem or not upper_stem:
        return None
    out = {}
    for i in range(3):                     # 初/二/三 ← 内卦自下而上
        out[RE_POS_NAME[i + 1]] = lower_stem + lb[i]
    for i in range(3):                     # 四/五/上 ← 外卦自下而上
        out[RE_POS_NAME[i + 4]] = upper_stem + ub[i]
    return out


def palace_of(hex_name: str) -> str:
    for p, v in EIGHT_PALACES.items():
        if any(h == hex_name for h, _ in v["order"]):
            return p
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="《周易尚占》立成表 vs core 纳甲逐格对拍")
    ap.add_argument("--json", action="store_true", help="机器读输出")
    args = ap.parse_args()

    src = parse_source()
    if not src:
        print("书源解析不出卦行（源文件缺失或格式变化）——门的输入坏了，须修脚本而非静默放过",
              file=sys.stderr)
        return 2

    same, changed, emptied = 0, [], []
    waived = []
    covered = 0
    for name, row in sorted(src.items(), key=lambda kv: kv[1]["_src"]):
        eng = engine_ganzhi(name)
        if eng is None:
            emptied.append({"卦": name, "src": row["_src"],
                            "书源": {k: row[k] for k in RE_POS_NAME.values()},
                            "引擎": "core 表未收录该卦/该宫结构不全"})
            continue
        covered += 1
        typos = SOURCE_TYPOS.get(name) or {}
        for pos in RE_POS_NAME.values():
            s, e = row.get(pos, ""), eng.get(pos, "")
            if s == e:
                same += 1
                continue
            t = typos.get(pos)
            if t and t["书源"] == s and t["应为"] == e:
                waived.append({"卦": name, "爻": pos, "src": t["src"],
                               "书源": s, "引擎": e, "理由": t["理由"]})
                continue
            changed.append({"卦": name, "core卦名": _strip_prefix(name),
                            "宫": palace_of(_strip_prefix(name)), "爻": pos,
                            "src": row["_src"], "书源": s, "引擎": e})

    total = same + len(changed) + len(waived)
    report = {
        "书源": SRC.name,
        "书源卦数": len(src),
        "对拍覆盖卦数": covered,
        "一致格数": same,
        "改值格数": len(changed),
        "书源形讹豁免格数": len(waived),
        "变空卦数": len(emptied),
        "对拍总格数": total,
        "改值明细": changed,
        "形讹豁免明细": waived,
        "变空明细": emptied,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if (changed or emptied) else 0

    print(f"《周易尚占》卷下立成表（{SRC.name} L{SCAN_FROM}-L{SCAN_TO}）"
          f" vs core 纳甲表")
    print(f"书源卦数 {len(src)}｜对拍覆盖 {covered}｜一致 {same} 格"
          f"｜改值 {len(changed)} 格｜书源形讹豁免 {len(waived)} 格"
          f"｜变空 {len(emptied)} 卦｜对拍总格 {total}")
    if changed:
        print("\n改值明细（逐条）：")
        for c in changed:
            print(f"  {c['卦']}（{c['宫']}宫）{c['爻']}：书源 {c['书源']} → 引擎 {c['引擎']}"
                  f"  [{c['src']}]")
    if waived:
        print("\n书源形讹豁免（**core 未动**，逐条列出以免静默吞掉）：")
        for w in waived:
            print(f"  {w['卦']}{w['爻']}：书源 {w['书源']}（形讹） vs 引擎 {w['引擎']}"
                  f"  [{w['src']}] —— {w['理由']}")
    if emptied:
        print("\n变空明细（逐条）：")
        for e in emptied:
            print(f"  {e['卦']} [{e['src']}]：引擎 {e['引擎']}")
    if not changed and not emptied:
        print(f"\n√ 六十四卦六爻纳甲与 core 逐格全同"
              f"（无改值、无变空；书源形讹 {len(waived)} 格已单列）")
    return 1 if (changed or emptied) else 0


if __name__ == "__main__":
    sys.exit(main())
