# -*- coding: utf-8 -*-
"""纳音取象：`core/yishu_core/ming_tables.py:NAYIN_XIANGGE` ↔ `data/nayin_quxiang.json` 同步门。

为什么需要它（2026-10-10）：调候表有 [9] 这道「静态表 ↔ data 层」同步门，纳音表却没有——
两处记载长期各写各的。这不是理论风险：本轮先只改了代码侧（补 戊辰/乙卯/庚申/癸亥、
剥掉 己巳/甲申/癸巳 性质名里混入的系词「为／者」），data 层一字未动，
于是「今天一致」立刻变成「两边差 4 格 + 3 个标签」。**改坏没人发现**正是同步门要防的。

    python dev_tools/sync_nayin_engine.py            # 看差异与应当写入的字面量
    python dev_tools/sync_nayin_engine.py --check     # 只校验（gate [14] 用；有差异退 1）
    python dev_tools/sync_nayin_engine.py --selftest  # 负例：人为造漂移，必须被检出

口径：
  · 唯一真值源是 data 层（它是《五行精纪》卷一的逐格抽取物，带底本行号与原文引句）；
  · 内核表必须与 data 在「有哪些干支」「性质名」「性质行号」三点上一致；
  · 性质引文本身逐字校验回底本（防止有人改标签时顺手改出处行号）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

DATA = ROOT / "data" / "nayin_quxiang.json"
CORPUS = ROOT / "data" / "sources" / "wuxing_jingji_dz.dz.txt"

from yishu_core.ming_tables import NAYIN_XIANGGE  # noqa: E402


def data_table() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))["纳音性质"]


def drift(data: dict, code: dict, corpus_lines: list[str]) -> list[str]:
    """返回人可读的差异清单；空 = 同源。"""
    out: list[str] = []
    only_data = sorted(set(data) - set(code))
    only_code = sorted(set(code) - set(data))
    if only_data:
        out.append(f"data 有而代码缺 {len(only_data)} 格：{'、'.join(only_data)}")
    if only_code:
        out.append(f"代码有而 data 缺 {len(only_code)} 格：{'、'.join(only_code)}")
    for gz in sorted(set(data) & set(code)):
        dv, cv = data[gz], code[gz]
        dn, cn = str(dv.get("性质名") or ""), str(cv.get("性质名") or "")
        if dn != cn:
            out.append(f"{gz} 性质名不一致：data={dn!r} 代码={cn!r}")
        dm = re.search(r"\d+", str(dv.get("性质行") or ""))
        cm = re.search(r"L(\d+)", str(cv.get("出处") or ""))
        if bool(dm) != bool(cm) or (dm and cm and dm.group(0) != cm.group(1)):
            out.append(f"{gz} 底本行号不一致：data={dv.get('性质行')!r} 代码={cv.get('出处')!r}")
        quote = str(dv.get("性质引文") or "").replace(" ", "")
        if dm and quote:
            ln = int(dm.group(0))
            if ln > len(corpus_lines) or quote not in corpus_lines[ln - 1].replace("　", "").replace(" ", ""):
                out.append(f"{gz} 性质引文未逐字命中底本 L{ln}：{quote[:20]}")
    return out


def emit_block(data: dict) -> str:
    """把 data 渲染成内核表应当采用的字面量（同步方向：data → 代码）。"""
    lines = ["NAYIN_XIANGGE: dict[str, dict[str, str]] = {"]
    for gz in sorted(data, key=lambda g: (HEAVENLY.index(g[0]), BRANCHES.index(g[1]))):
        v = data[gz]
        lines.append(f'    "{gz}": {{"性质名": "{v["性质名"]}", '
                     f'"出处": "《五行精纪》{v["性质行"]}"}},')
    lines.append("}")
    return "\n".join(lines)


HEAVENLY = list("甲乙丙丁戊己庚辛壬癸")
BRANCHES = list("子丑寅卯辰巳午未申酉戌亥")


def as_code_table(data: dict) -> dict:
    """把 data 渲染成「若已同步则代码侧应当长这样」的表，供负例构造与正对照使用。"""
    return {gz: {"性质名": v["性质名"], "出处": f"《五行精纪》{v['性质行']}"}
            for gz, v in data.items()}


def selftest() -> list[str]:
    """负例：三类漂移（代码缺格 / 标签回潮 / 行号漂走）+ 一类数据侧错（引文不符），
    以及一条假阳性对照（同源自比不得报差异）。"""
    data = data_table()
    corpus = CORPUS.read_text(encoding="utf-8").splitlines()
    base = as_code_table(data)
    problems: list[str] = []

    # 正对照：一致时必须零差异，否则本门会把同步好的仓库判红（逼人拆门）
    if drift(data, base, corpus):
        problems.append(f"假阳性：同源自比却报出差异 → {drift(data, base, corpus)[:2]}")

    # 1 代码缺格
    c1 = dict(base)
    c1.pop("癸亥")
    if not any("癸亥" in x and "代码缺" in x for x in drift(data, c1, corpus)):
        problems.append("负例失效：代码删掉一格没被抓出")

    # 2 性质名混入系词（就是本轮真实发生过的那种漂移）
    c2 = {k: dict(v) for k, v in base.items()}
    c2["己巳"]["性质名"] = "为近火之木"
    if not any("己巳" in x and "性质名" in x for x in drift(data, c2, corpus)):
        problems.append("负例失效：性质名混入系词没被抓出")

    # 3 底本行号漂走
    c3 = {k: dict(v) for k, v in base.items()}
    c3["戊辰"]["出处"] = "《五行精纪》L999"
    if not any("戊辰" in x and "行号" in x for x in drift(data, c3, corpus)):
        problems.append("负例失效：底本行号漂移没被抓出")

    # 4 数据侧引文与所标行号不符（data 是真值源，故这条造在 data 上）
    d4 = {k: dict(v) for k, v in data.items()}
    d4["庚申"] = dict(d4["庚申"], 性质行="L1")
    if not any("庚申" in x and "逐字命中" in x for x in drift(d4, base, corpus)):
        problems.append("负例失效：引文与所标行号不符没被抓出")

    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="纳音取象表 data↔内核同步门")
    ap.add_argument("--check", action="store_true", help="只校验是否已同步（CI/gate 用）")
    ap.add_argument("--selftest", action="store_true", help="负例自证")
    ap.add_argument("--emit", action="store_true", help="打印应当写入内核表的字面量")
    args = ap.parse_args()

    data = data_table()
    corpus = CORPUS.read_text(encoding="utf-8").splitlines()
    d = drift(data, NAYIN_XIANGGE, corpus)

    if args.selftest:
        sp = selftest()
        for x in sp:
            print(f"  × {x}")
        print(f"  [selftest] 负例{'全部抓到' if not sp else '失效'}")
        if sp:
            return 1

    print(f"纳音取象：data {len(data)} 格 / 代码 {len(NAYIN_XIANGGE)} 格 / 差异 {len(d)} 处")
    if args.emit:
        print(emit_block(data))
    if d:
        for x in d[:20]:
            print(f"  × {x}")
        print("  → 同步方向是 data → 代码（data 是《五行精纪》逐格抽取物，带行号与原文）；"
              "跑 `python dev_tools/sync_nayin_engine.py --emit` 取字面量后改 ming_tables.py，"
              "不要手改 data 迁就读数。")
        return 1
    print("  √ NAYIN_XIANGGE 与 data/nayin_quxiang.json 同源（干支集/性质名/底本行号三点一致）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
