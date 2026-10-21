# -*- coding: utf-8 -*-
"""restorable 机械复核器（第两百零一批）——双解析器共识，替人把「抽没抽错」核完。

189 批毕业册给出 18 条 restorable（A 器装配验证过）。它们进正式外部集前仍要人核
「卦面/验支是否读对了原文」——这一步的机械半可以用**独立第二解析器**做完：
  B 器与 A 器不同源：卦名取内核全表按字数倒序贪婪匹配「得/占/化」窗口；
  验支动词族扩集（应于/验于/果于/定于/应/验＋支＋日|月|年）；日期允许 干支日 在 月建 前后两种语序。
两器逐项比对 original/changed/yingqi_branch：
  consensus        ＝ 双器一致（人只看语义与正误，不再核对抽取本身）
  needs_human      ＝ 任一项分歧或 B 器抽不到——**分歧是信息不是噪音**，逐条标字段
升册永远是人的决定（§三.4）；本器只把人工从「重新读文言」降为「裁决两个读数」。

    python dev_tools/recheck_restorable.py            # 生成复核册＋打印共识统计
    python dev_tools/recheck_restorable.py --selftest
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
sys.path.insert(0, str(HERE))
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from stable_write import write_stable  # noqa: E402  203 批：幂等写，时间戳=内容最后变化
from yishu_core.symbols import HEXAGRAM_TRIGRAMS  # noqa: E402
from version_collate import norm  # noqa: E402

SRC_DIR = DISC / "data" / "sources"
GRAD = DISC / "data" / "cases" / "verifications_graduation.json"
OUT = DISC / "data" / "cases" / "restorable_recheck.json"

GAN = "甲乙丙丁戊己庚辛壬癸"
BR = "子丑寅卯辰巳午未申酉戌亥"
# B 器文法：卦名词袋（全表＋常见冠名字，按长度倒序贪婪）
_HEXNAMES = sorted(list(HEXAGRAM_TRIGRAMS) +
                   ["乾", "坤", "屯", "蒙", "需", "訟", "讼", "師", "师", "比", "小畜", "履", "泰", "否",
                    "同人", "大有", "謙", "谦", "豫", "随", "隨", "蠱", "蛊", "臨", "临", "观", "噬嗑",
                    "賁", "贲", "剥", "剝", "復", "复", "无妄", "天夬", "姤", "聚", "革", "兌", "鼎",
                    "震", "艮", "漸", "渐", "归妹", "女归", "豐", "丰", "旅", "巽", "兌", "涣", "渙",
                    "节", "節", "中孚", "小过", "過", "既济", "未济", "旣濟", "未濟"],
                   key=len, reverse=True)
_HEX_ALT = "|".join(re.escape(h) for h in _HEXNAMES)
GET_PAIR = re.compile(r"(?:得|占得|化|变|變)\s*(?P<hx>" + _HEX_ALT + r")"
                      r"(?:\s*(?:之|化|變|变)\s*(?P<hx2>" + _HEX_ALT + r")|(?P<hx2b>卦))?")
YING_B = re.compile(r"[应應验驗果定]于?\s*[" + GAN + r"]?([" + BR + r"])\s*(?:日|月|年)")


def parse_b(text: str):
    """B 器：独立文法。返回 (original, changed, ying_branch) 或 None 项。"""
    t = norm(text)
    orig = chg = ying = None
    for m in GET_PAIR.finditer(t):
        h1 = m.group("hx")
        h2 = m.group("hx2") or (h1 if m.group("hx2b") else None)
        if h1 in HEXAGRAM_TRIGRAMS:
            orig = h1
            if h2 and h2 in HEXAGRAM_TRIGRAMS and h2 != h1:
                chg = h2
            break
    m = YING_B.search(t)
    if m:
        ying = m.group(1)
    return orig, chg, ying


def recheck() -> int:
    grad = json.loads(GRAD.read_text(encoding="utf-8"))
    items = [r for r in grad["rows"] if r.get("status") == "restorable"]
    if not items:
        print("× restorable 0 条——先查毕业册，不静默")
        return 1
    cache = {}
    rows = []
    for it in items:
        f = it["file"]
        if f not in cache:
            cache[f] = (SRC_DIR / f).read_text(encoding="utf-8", errors="replace").splitlines()
        lines = cache[f]
        lo = it["line"] - 1
        # B 器窗口独立推导（与 A 器的块界法不同源）：从验注行向上找**最近的干支日行**作开案行，
        # 窗口=开案行..验注行；找不到则回退 3 行窗（并因此产生真分歧→人裁）。
        win_start = max(0, lo - 2)
        for j in range(lo, max(-1, lo - 40), -1):
            if re.search(r"[" + GAN + r"][" + BR + r"]日", lines[j]):
                win_start = j
                break
        block = "\n".join(norm(x) for x in lines[win_start:lo + 1])
        b_o, b_c, b_y = parse_b(block)
        a = it.get("hex", {})
        diffs = []
        if (a.get("original") or None) != (b_o or None):
            diffs.append("original")
        if (a.get("changed") or None) != (b_c or None):
            diffs.append("changed")
        if (a.get("yingqi_branch") or None) != (b_y or None):
            diffs.append("yingqi")
        rows.append({"id": it["source_id"], "file": f, "line": it["line"],
                     "a": {k: a.get(k) for k in ("date", "original", "changed", "yingqi_branch")},
                     "b": {"original": b_o, "changed": b_c, "yingqi": b_y},
                     "verdict": "consensus" if not diffs else ("needs_human:" + ",".join(diffs))})
    n_ok = sum(1 for r in rows if r["verdict"] == "consensus")
    doc = {"generated_at": datetime.now().isoformat(timespec="seconds"),
           "_comment": "双解析器共识复核：consensus 条目人只裁语义；needs_human 标分歧字段。"
                       "升册永远是人的决定（§三.4），本册不改毕业册状态、不写 expected。",
           "n": len(rows), "consensus": n_ok, "needs_human": len(rows) - n_ok, "rows": rows}
    write_stable(OUT, doc)
    print("√ 复核册落成 %s｜restorable %d → 双器共识 %d｜需人看分歧 %d"
          % (OUT.name, len(rows), n_ok, len(rows) - n_ok))
    for r in rows:
        if r["verdict"] != "consensus":
            print("  · %s L%d %s｜A=%s B=%s" % (r["id"], r["line"], r["verdict"],
                                                r["a"], r["b"]))
    return 0


def selftest() -> int:
    fails = []
    o, c, y = parse_b("己卯月戊申日占婚得乾之否，明年壬子月赘成。应于甲寅日完娶。")
    if (o, c, y) != ("乾", "否", "寅"):
        fails.append("合成共识例解析错：%r" % ((o, c, y),))
    o2, c2, y2 = parse_b("纯议论句，无占无卦。")
    if any([o2, c2, y2]):
        fails.append("无例句被臆造读出（假阳性）")
    o3, _, y3 = parse_b("占病得泰卦，验于丙子日而愈。")
    if o3 != "泰" or y3 != "子":
        fails.append("单卦+干支日扩动词例解析错：%r" % ((o3, y3),))
    print("√ selftest：合成共识/假阳性/单卦扩动词 三例全过" if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="restorable 双解析器共识复核（观察册）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return recheck()


if __name__ == "__main__":
    raise SystemExit(main())
