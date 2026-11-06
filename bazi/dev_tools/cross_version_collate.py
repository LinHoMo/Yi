# -*- coding: utf-8 -*-
"""跨版本窗口对拍（499批）——八字各书 dz(殆知阁) vs wikitext(维基文库) 两转录链一致性。

为什么：六爻 version_collate.py 只对过《增删卜易》一本；八字侧此前只有《三命通会》
四库本对拍（diff_siku_sanming.py，深度绑三命锚点）。本器把同一把尺子（40字窗口逐字命中）
推广到其余有双转录链的八字底本，**只读观测，不改案例库、不动读数**。

口径：
  1. 归一化复用三命 norm_map：t2s 繁简表、剥 {{}} 模板（{{SK notes|x}} 取 x）、
     剥 <tag>、剥空白与【】注文标记。
  2. 从 dz 本每 STEP=40 字取一 WIN=40 字窗口，在 wikitext 归一串里逐字 find；
     命中率＝命中窗口/总窗口。这是「dz 文本能否在 wiki 中逐字找到」，不是「案例冲突率」。
  3. 低命中先看是不是同源/节选/不同注本，不强行当版本差异（神峰通考 100%＝两本同源）。

    python dev_tools/cross_version_collate.py            # 跑全部已配书
    python dev_tools/cross_version_collate.py --selftest
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DISC = Path(__file__).resolve().parents[1]
T2S_PATH = DISC / "dev_tools" / "t2s_table.json"
OUT = DISC / "data" / "collation" / "cross_version_summary.json"

WIN, STEP = 40, 40

# (书名人, dz文件名, wikitext文件名)；路径相对 data/sources/
BOOKS = [
    ("滴天髓阐微", "ditian_sui_chanwei_dz.dz.txt", "di-tian-sui-chan-wei.wikitext.txt"),
    ("穷通宝鉴",   "qiong_tong_bao_jian_dz.dz.txt", "qiong-tong-bao-jian.wikitext.txt"),
    ("神峰通考",   "shenfeng_tongkao_dz.dz.txt",    "shen-feng-tong-kao.wikitext.txt"),
    ("渊海子平",   "yuanhai_ziping_dz.dz.txt",      "yuan-hai-zi-ping.wikitext.txt"),
]


def norm_map(raw: str, tbl: dict) -> str:
    """逐行归一：繁简 translate、剥 {{}}/<>/空白/【】。返回归一串（不带行映射，够窗口用）。"""
    trans = str.maketrans(tbl) if tbl else {}
    out, in_tag = [], False
    for raw_line in raw.splitlines():
        buf, i, n = [], 0, len(raw_line)
        while i < n:
            ch = raw_line[i]
            if in_tag:
                j = raw_line.find(">", i)
                if j < 0:
                    i = n
                    continue
                in_tag = False
                i = j + 1
                continue
            if ch == "<":
                in_tag = True
                i += 1
                continue
            if ch == "{":
                j = raw_line.find("}}", i + 2)
                if j < 0:
                    break
                content = raw_line[i + 2:j]
                if content.startswith("SK notes|"):
                    buf.append(content[9:])
                i = j + 2
                continue
            if ch.isspace() or ch == "　":
                i += 1
                continue
            if ch in "【】":
                i += 1
                continue
            buf.append(ch)
            i += 1
        out.extend(c.translate(trans) for c in buf)
    return "".join(out)


def collate_one(dz_path: Path, wiki_path: Path, tbl: dict) -> dict:
    dz_norm = norm_map(dz_path.read_text(encoding="utf-8", errors="replace"), tbl)
    wk_norm = norm_map(wiki_path.read_text(encoding="utf-8", errors="replace"), tbl)
    wins = [dz_norm[k:k + WIN] for k in range(0, len(dz_norm) - WIN + 1, STEP)]
    hits = sum(1 for w in wins if w in wk_norm)
    ratio = hits / len(wins) if wins else 0.0
    return {
        "dz_file": dz_path.name, "wiki_file": wiki_path.name,
        "dz_chars": len(dz_norm), "wiki_chars": len(wk_norm),
        "windows": len(wins), "hits": hits,
        "hit_ratio": round(ratio, 4),
        "note": ("两本归一后字数完全相等且全窗口命中＝同源转录链，非独立版本"
                 if ratio >= 0.999 and len(dz_norm) == len(wk_norm) else
                 "篇幅相近但命中低＝疑不同注本/编排，需人工判定是否同一版本"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="八字各书跨版本窗口对拍（只读观测）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--reconcile", action="store_true",
                    help="只读对账：CAPABILITY③ 命中率 ↔ 现场复算（闭环 G13）")
    ap.add_argument("--dry-run", action="store_true", help="只打印不写 json")
    args = ap.parse_args()

    if args.reconcile:
        return reconcile()
    if args.selftest:
        return _selftest()

    tbl = json.loads(T2S_PATH.read_text(encoding="utf-8"))
    results = {}
    print(f"{'书':<10} {'dz字':>7} {'wiki字':>7} {'窗':>5} {'中':>5} {'命中':>6}")
    for name, dzf, wkf in BOOKS:
        dzp = DISC / "data" / "sources" / dzf
        wkp = DISC / "data" / "sources" / wkf
        if not dzp.exists() or not wkp.exists():
            results[name] = {"error": f"缺文件 dz={dzp.exists()} wiki={wkp.exists()}"}
            print(f"{name:<10} 缺文件")
            continue
        r = collate_one(dzp, wkp, tbl)
        results[name] = r
        print(f"{name:<10} {r['dz_chars']:>7} {r['wiki_chars']:>7} {r['windows']:>5} "
              f"{r['hits']:>5} {r['hit_ratio']*100:>5.1f}%")

    payload = {"_meta": "499批跨版本窗口对拍，只读观测不改读数", "win": WIN, "step": STEP,
               "books": results}
    if not args.dry_run:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\n√ 已写 {OUT.relative_to(DISC)}")
    return 0


def _selftest() -> int:
    fails = []
    tbl = {"東": "东", "與": "与", "後": "后"}
    # 同文归一后应全命中
    same = norm_map("東方與後　\n", tbl)
    if same != "东方与后":
        fails.append("归一化错：%r" % same)
    # 窗口命中逻辑
    dz = "甲乙丙丁戊己庚辛壬癸" * 10
    wk = dz  # 完全相同
    wins = [dz[k:k + 4] for k in range(0, len(dz) - 3, 4)]
    hits = sum(1 for w in wins if w in wk)
    if hits != len(wins):
        fails.append("同文窗口未全命中")
    # 去模板：{{SK notes|夹注}} 应取「夹注」且剥外层
    tpl = norm_map("正文{{SK notes|夹注}}后", {})
    if "夹注" not in tpl or "{{" in tpl:
        fails.append("模板剥离错：%r" % tpl)
    if fails:
        print("× selftest：" + "；".join(fails))
        return 1
    print("√ selftest：归一/窗口命中/模板剥离 全过")
    return 0


def reconcile() -> int:
    """只读对账：CAPABILITY ③ 声称的跨版本窗口命中率，须与现场复算一致（闭环 G13 缺口）。

    现场从已入库底本复算（collate_one），不依赖被 gitignore 的 collation 产物，
    fresh-tree CI 可跑。守 528 约定：不新增 check.py 门号，挂 CI root-gates。
    """
    cap = (DISC.parent / "CAPABILITY.md").read_text(encoding="utf-8")
    m = re.search(r"③(.*?)(?:\n④|$)", cap, re.S)
    block = m.group(1) if m else cap

    def grab(name):
        mm = re.search(name + r"\s*([\d.]+)\s*%", block)
        return float(mm.group(1)) if mm else None

    claimed = {
        "滴天髓阐微": grab("滴天髓阐微"),
        "穷通宝鉴": grab("穷通宝鉴"),
        "渊海子平": grab("渊海子平"),
        "神峰通考": grab("神峰通考"),
    }
    tbl = json.loads(T2S_PATH.read_text(encoding="utf-8"))
    fails = []
    for name, dzf, wkf in BOOKS:
        dzp = DISC / "data" / "sources" / dzf
        wkp = DISC / "data" / "sources" / wkf
        if not dzp.exists() or not wkp.exists():
            fails.append("%s 缺底本（dz=%s wiki=%s）" % (name, dzp.exists(), wkp.exists()))
            continue
        r = collate_one(dzp, wkp, tbl)
        data_pct = round(r["hit_ratio"] * 100, 1)
        cv = claimed.get(name)
        if cv is None or abs(data_pct - cv) > 0.15:
            fails.append("%s: CAPABILITY 声称 %s%% vs 现场复算 %.1f%%" % (name, cv, data_pct))
    if fails:
        print("× 跨版本命中率「声明↔数据」对账失败：" + "；".join(fails))
        return 1
    print("√ 跨版本命中率声明↔数据一致：滴天髓阐微 %.1f%%／穷通宝鉴 %.1f%%／渊海子平 %.1f%%／神峰通考 %.1f%%"
          % (claimed["滴天髓阐微"], claimed["穷通宝鉴"], claimed["渊海子平"], claimed["神峰通考"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
