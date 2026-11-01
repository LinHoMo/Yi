# -*- coding: utf-8 -*-
"""partial 预分诊器（第一百九十九批·B3 人工流的机械半）——把 63 条 partial 变成人可速裁的短单。

输入 `data/cases/verifications_graduation.json` 的 partial_needs_human 条目，按原因分路做**机械**
核查（不写 expected、不入册——升格永远是人的决定，§三.4）：
  A 验支不可提 → 块内扫宽松式（验于X/后X日/至X/逢X日…），有候选者输出「候选支＋命中位置＋
    原句片段」供人一键定夺；全空者归「素材缺验支」结案候选；
  B 卦名异写不可唯一落表 → 列出逐字 token＋内核表最近候选（前缀/后缀双查），给出**候选异体字**
    注记（供 TRAD 表增补的提案，增补本身走正式批）；
  C 日期键跨块（回溯 40 行未及）→ 放宽到 80 行重找一次，命中者回填候选，未中者结案候选。
输出 `data/cases/verifications_triage.json`（观察册）。

    python dev_tools/triage_partials.py            # 生成 triage 册
    python dev_tools/triage_partials.py --selftest
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
from version_collate import norm  # noqa: E402

BR = "子丑寅卯辰巳午未申酉戌亥"
SRC_DIR = DISC / "data" / "sources"
GRAD = DISC / "data" / "cases" / "verifications_graduation.json"
OUT = DISC / "data" / "cases" / "verifications_triage.json"

LOOSE_YING = re.compile(r"([" + BR + r"])(?:日|月|年)(?:而|则)?[应應验驗]|"
                        r"[应應验驗]于?[甲乙丙丁戊己庚辛壬癸]?([" + BR + r"])(?:日|月|年)|"
                        # 400 批：补实录式（果得於／果卒於／果至／后至／果于次年三月）。
                        # 只认结果标记，且跨句以「．」等句读为界；不认纯预测句。
                        r"[果竟卒后][^。；\n．.]{0,12}?([" + BR + r"])(日|月|年)|"
                        r"[果竟卒后][^。；\n．.]{0,12}?([正一二三四五六七八九十冬腊])月|"
                        r"后[一二两三四五六七八九十0-9]+日[而]?[应應验驗]?")
DATE_PAT = re.compile(r"([子丑寅卯辰巳午未申酉戌亥])月([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])日")

# 399 批：本册是「生成物＋人工裁决」的混合体——裁决字段由后续正式批按 id 追加，
# 重建时若一律重算就会把已裁的结论静默抹掉（下一次值守会重读一遍，且看起来像没裁）。
# 口径：只搬运「裁决/复核」字段，不搬运机械桶归属；桶归属永远按当前分诊逻辑重算。
CARRY_KEYS = ("decision", "decision_basis", "decision_kind", "postcheck")
# 顶层的授权/签署记录同样是人工写上的，重建时保留（不含 generated_at/_comment）。
META_KEEP = ("decision_authority",)


def _carry(row: dict, prev: dict | None) -> None:
    """把上版同 id 的裁决字段搬到新行（只搬 CARRY_KEYS）。"""
    if not prev:
        return
    for k in CARRY_KEYS:
        if k in prev:
            row[k] = prev[k]


def triage(report_only: bool = False) -> int:
    grad = json.loads(GRAD.read_text(encoding="utf-8"))
    rows = [r for r in grad["rows"] if r.get("status") == "partial_needs_human"]
    if not rows:
        print("× partial 条目 0——先核毕业册，不静默出空 triage")
        return 1
    prev_doc = {}
    if OUT.exists():
        try:
            prev_doc = json.loads(OUT.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            prev_doc = {}
    prev_by_id = {}
    for items in (prev_doc.get("rows") or {}).values():
        for r in items:
            if isinstance(r, dict) and r.get("id"):
                prev_by_id[r["id"]] = r
    cache = {}
    buckets = {"A_有验支候选": [], "A_无验支结案候选": [], "B_异写候选": [],
               "B_词袋可解（建议入 restorable 候选）": [], "B_真分歧需人": [],
               "C_深回溯命中": [], "C_仍缺日期结案候选": []}

    def add(bucket: str, row: dict) -> None:
        _carry(row, prev_by_id.get(row.get("id")))
        buckets.setdefault(bucket, []).append(row)

    for r in rows:
        f = r["file"]
        if f not in cache:
            cache[f] = (SRC_DIR / f).read_text(encoding="utf-8", errors="replace").splitlines()
        lines = cache[f]
        why = r.get("why", "")
        lo = r["line"] - 1
        block = "\n".join(norm(x) for x in lines[lo:lo + 14])
        if why.startswith("卦面齐但书载验支"):
            ms = list(LOOSE_YING.finditer(block))
            if ms:
                add("A_有验支候选", {
                    "id": r["source_id"], "line": r["line"], "file": f,
                    "hits": [m.group(0) for m in ms[:4]],
                    "context": block[:120]})
            else:
                add("A_无验支结案候选", {"id": r["source_id"], "why": "宽松式仍无候选——素材缺验支"})
        elif why.startswith("卦名异写"):
            # B 路解析与 201 批 recheck 的卦名词袋同源（器内口径唯一，第两百零二批统一）——
            # 原「剥/無妄/困卦」级假分歧 10/13 皆因旧分词无词袋贪婪与剥后缀。
            from recheck_restorable import parse_b
            b_o, b_c, b_y = parse_b(block)
            a = r.get("hex") or {}
            if b_o and (b_o != a.get("original") or (b_c or None) != (a.get("changed") or None)):
                add("B_真分歧需人", {"id": r["source_id"], "line": r["line"], "file": f,
                                     "a": a, "b": {"original": b_o, "changed": b_c,
                                                   "yingqi": b_y}})
            elif b_o:
                add("B_词袋可解（建议入 restorable 候选）",
                    {"id": r["source_id"], "line": r["line"], "file": f,
                     "resolved": {"original": b_o, "changed": b_c}})
            else:
                toks = re.findall(r"'([^']+)'", why)[:2]
                add("B_异写候选", {"id": r["source_id"], "line": r["line"], "file": f,
                                   "near": [{"token": t, "candidates": []} for t in toks]})
        elif why.startswith("有日期键") or "日期" in why:
            lo2 = max(0, lo - 80)
            seg = "\n".join(norm(x) for x in lines[lo2:lo + 1])
            hits = list(DATE_PAT.finditer(seg))
            if hits:
                add("C_深回溯命中", {"id": r["source_id"], "line": r["line"], "file": f,
                                     "date_hit": hits[-1].group(0)})
            else:
                add("C_仍缺日期结案候选", {"id": r["source_id"], "why": "80 行内仍无日期键"})
        else:
            add("Z_其他", {"id": r["source_id"], "why": why[:40]})
    doc = {"generated_at": datetime.now().isoformat(timespec="seconds"),
           "_comment": "观察册：分诊不改判——『结案候选』也须人签字后才算 §六.5 诚实结案；"
                       "B 桶异写候选是 TRAD 表增补提案非既成事实。"
                       "399 批：D 8 条采信补 postcheck、E 35 条补 decision_kind/decision_basis；"
                       "重建本册时按 id 保留这些裁决字段（不再被重算抹掉）。",
           "input": len(rows), "buckets": {k: len(v) for k, v in buckets.items()},
           "rows": buckets}
    for k in META_KEEP:
        if k in prev_doc:
            doc[k] = prev_doc[k]
    if report_only:
        old = prev_doc or {}
        old_b = old.get("buckets") or {}
        new_b = doc["buckets"]
        print("√ 报告模式（**未写盘**）：partial %d 条" % len(rows))
        for k in sorted(set(old_b) | set(new_b)):
            if old_b.get(k, 0) != new_b.get(k, 0):
                print("  %-24s 旧 %d → 新 %d" % (k, old_b.get(k, 0), new_b.get(k, 0)))
        old_a = {r.get("id") for r in (old.get("rows") or {}).get("A_有验支候选", [])}
        new_a = {r.get("id") for r in buckets.get("A_有验支候选", [])}
        old_e = {r.get("id") for r in (old.get("rows") or {}).get("A_无验支结案候选", [])}
        new_e = {r.get("id") for r in buckets.get("A_无验支结案候选", [])}
        print("  A_有验支 新增 %d：%s" % (len(new_a - old_a), sorted(new_a - old_a)))
        print("  A_无验支 移出 %d：%s" % (len(old_e - new_e), sorted(old_e - new_e)))
        print("  （这是正则盲区复核的实测差；应用差集＝另批重建观察册，本批只报数）")
        return 0
    write_stable(OUT, doc)
    print("√ triage 册落成 %s｜partial %d 条 → %s"
          % (OUT.name, len(rows), doc["buckets"]))
    print("  人可速裁面：A_有候选 %d（一键定夺）＋B_词袋可解 %d（附解析结果待签升级）＋"
          "B_真分歧 %d（A/B 并排裁决）＋旧词袋兜底 %d；结案候选 %d＋%d 待签"
          % (len(buckets["A_有验支候选"]),
             len(buckets["B_词袋可解（建议入 restorable 候选）"]),
             len(buckets["B_真分歧需人"]), len(buckets["B_异写候选"]),
             len(buckets["A_无验支结案候选"]), len(buckets["C_仍缺日期结案候选"])))
    return 0


def selftest() -> int:
    fails = []
    m = list(LOOSE_YING.finditer("果于卯日大晴，验于甲子日。后五日而应。应于寅日。"))
    got = " ".join(x.group(0) for x in m)
    if "果于卯" not in got or "应于寅" not in got or "验于甲子" not in got:
        fails.append("宽松验句式命中不足：%r" % got)
    if not DATE_PAT.search("卯月壬辰日占"):
        fails.append("日期式正向失效")
    if DATE_PAT.search("明日复占"):
        fails.append("日期式假阳性")
    # 400 批：实录式正负例（旧式只认果于X日，漏果得於/果卒於/果至/后至/月序）
    got2 = " ".join(x.group(0) for x in LOOSE_YING.finditer(
        "果得於甲午日。果卒於申日。后至辛卯日。果于次年三月。果于七月。"))
    for want in ("果得於甲午日", "果卒於申日", "后至辛卯日", "果于次年三月", "果于七月"):
        if want not in got2:
            fails.append("实录式漏取：%r 未命中" % want)
    for bad in ("果于本日酉时", "果于次日大晴", "果得长子.甲戌年", "果得长子．甲戌年"):
        if LOOSE_YING.search(bad):
            fails.append("非验支被误取：%r" % bad)
    # 399 批负例：裁决字段必须按 id 搬运；机械桶字段不搬（桶归属永远重算）
    row = {"id": "X", "why": "机械值"}
    prev = {"id": "X", "decision": "结案", "decision_kind": "已在册",
            "decision_basis": "b", "postcheck": {"status": "已在册"}, "why": "旧机械值"}
    _carry(row, prev)
    if row.get("decision") != "结案" or row.get("decision_kind") != "已在册" \
            or not row.get("postcheck") or row.get("why") != "机械值":
        fails.append("裁决字段搬运/机械字段隔离失效：%r" % row)
    print("√ selftest：验支宽松式/日期式/裁决字段搬运 全过" if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="partial 机械预分诊（观察册，不改判）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true",
                    help="只按当前分诊逻辑重算并打印与在册册的差集，**不写盘**")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return triage(report_only=args.report)


if __name__ == "__main__":
    raise SystemExit(main())
