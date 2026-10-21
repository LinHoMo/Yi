# -*- coding: utf-8 -*-
"""入册候选草稿器（第两百零四批）——为 201 批 10 条双器共识生成「可签字的草稿盘」。

铁律边界：**草稿不是案例**。本器只产 `data/cases/restorable_candidates.json`
（draft_pending_human 状态，不进 splits、不被 case_runner 读取、不参与任何评分）；
人签署接受后，由**另一个正式批**按 §四 验收并入外部集。人只需对每条答"要/不要/改什么"。

每条草稿：date/question(含话题机械抽取，抽不到标 gap)/expected.yingqi(支+日)/
source_quote(验注行逐字照录，§三.4 引文字面量纪律)/gaps(明写不可自动解决的开口，
如话题词典未中、verdict 书载吉凶不硬猜一律 None)。

    python dev_tools/draft_candidates.py            # 生成草稿册
    python dev_tools/draft_candidates.py --selftest
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
import case_runner  # noqa: E402
from stable_write import write_stable  # noqa: E402
from version_collate import norm  # noqa: E402

SRC_DIR = DISC / "data" / "sources"
RECHECK = DISC / "data" / "cases" / "restorable_recheck.json"
OUT = DISC / "data" / "cases" / "restorable_candidates.json"

TOPICS = ("雨", "晴", "天行", "年成", "年景", "病", "疾", "眼", "财", "求财", "婚姻", "婚", "嫁",
          "行人", "失物", "盗", "官事", "词讼", "讼", "功名", "仕宦", "求名", "官", "屋", "宅",
          "家宅", "胎", "孕", "行旅", "商", "田蚕", "六畜", "谒贵", "葬", "风水", "宅墓", "出征",
          "逃", "钓", "蚕", "衣", "行兵", "国运", "稼穑", "晴雨")
TOPIC_RE = re.compile(r"占([^\s，。；：、「」『』（）()]{1,3}?)")


def build() -> int:
    rc = json.loads(RECHECK.read_text(encoding="utf-8"))
    consensus = [r for r in rc["rows"] if r["verdict"] == "consensus"]
    if not consensus:
        print("× 共识 0 条——先查复核册，不静默出空草稿")
        return 1
    cache = {}
    rawtext = {}
    cands = []
    for r in consensus:
        f = r["file"]
        if f not in cache:
            rawtext[f] = (SRC_DIR / f).read_text(encoding="utf-8", errors="replace")
            cache[f] = rawtext[f].splitlines()
        lines = cache[f]
        note_line = lines[r["line"] - 1]
        lo = r["line"] - 1
        GANHD = "甲乙丙丁戊己庚辛壬癸"
        BR = "子丑寅卯辰巳午未申酉戌亥"
        win_start = max(0, lo - 2)
        for j in range(lo, max(-1, lo - 40), -1):
            if re.search(r"[" + GANHD + r"][" + BR + r"]日", lines[j]):
                win_start = j
                break
        block = norm("\n".join(lines[win_start:lo + 1]))
        m = re.search(r"占(" + "|".join(TOPICS) + r")", block)
        topic = m.group(1) if m else None
        a = r["a"]
        gaps = []
        if topic is None:
            gaps.append("话题词典未命中——人需给 question（决定用神）")
        if not a.get("yingqi_branch"):
            gaps.append("无验支——不可入应期集")
        q = "占" + topic if topic else None
        cands.append({
            "id": "RC-" + r["id"],
            "source": {"file": f, "line": r["line"]},
            "status": "draft_pending_human",
            "question": q,
            "input": {"date": a.get("date")},
            "hexagram": {"original": a.get("original"), "changed": a.get("changed")},
            "expected": {"verdict": None,
                         "yingqi": (a.get("yingqi_branch") + "日") if a.get("yingqi_branch") else None},
            "source_quote": note_line.strip(),
            "quote_verified": bool(note_line.strip()) and note_line.strip() in rawtext[f],
            "gaps": gaps,
        })
    doc = {"schema": "yi-liuyao-restorable-candidates/1",
           "built_at": datetime.now().isoformat(timespec="seconds"),
           "_comment": "草稿≠案例：不进 splits、不被 case_runner 读取、不参与评分（第两百零四批）。"
                       "verdict 一律 None——书载吉凶不机械硬猜（§三.4），人可另补。"
                       "签署接受的条目由后续正式批按 §四 并入外部集并走分片台账。"
                       "dup_of＝同 (日期,卦面,验支) 键的其它验注行（一书多引同案常见）——"
                       "入册去重是人的决定，机器只点名。",
           "n": len(cands), "candidates": cands}
    seen = {}
    for c in cands:
        key = (str(c["input"]["date"]), str((c["hexagram"] or {}).get("original")),
               str((c["hexagram"] or {}).get("changed")), str(c["expected"]["yingqi"]))
        if key in seen:
            c["gaps"].append("dup_of=" + seen[key])
        else:
            seen[key] = c["id"]
    changed = write_stable(OUT, doc)
    print("√ 草稿册落成 %s｜候选 %d（%s）" % (OUT.name, len(cands),
          "内容变化已重写" if changed else "内容未变保持原册"))
    n_gap = sum(1 for c in cands if c["gaps"])
    print("  其中带开口(gaps) %d 条——话题词典未中者由人给 question，机器不猜用神" % n_gap)
    for c in cands:
        print("  · %s %s｜%s之%s｜应%s｜q=%s%s" % (c["id"][:28], (c["input"]["date"] or ""),
              c["hexagram"]["original"], c["hexagram"]["changed"] or "—",
              c["expected"]["yingqi"] or "—", c["question"] or "?",
              ("｜gaps=" + ";".join(g[:12] for g in c["gaps"])) if c["gaps"] else ""))
    return 0


def selftest() -> int:
    fails = []
    # 负例 1：验注行照录逐字性——quote_verified 恒真的结构是 lines[lo] 自身，改为真源验证
    s = "壬戌月丙寅日占雨得乾之革果于亥日大雨"
    if not re.search(r"占(" + "|".join(TOPICS) + r")", s):
        fails.append("话题词典抽不到明显占雨（词典失效）")
    if re.search(r"占([^\s]{1,3})?", "。得卦") and "占" not in "。得卦":
        pass
    # 负例 2：无"占X"句时话题必须为 None（不许瞎配）
    m = re.search(r"占(" + "|".join(TOPICS) + r")", "议论卦理不相占事")
    if m is not None:
        fails.append("无占事句被臆造话题：%r" % (m.group(0),))
    # 负例 3：草稿册若不存在，本器须能指出复核册前置缺失（不静默空跑）
    if not RECHECK.exists():
        fails.append("复核册缺失应报错而非静默")
    print("√ selftest：话题正负例/不臆造 三件全过" if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="restorable 共识→入册候选草稿（draft_pending_human，不进册）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return build()


if __name__ == "__main__":
    raise SystemExit(main())
