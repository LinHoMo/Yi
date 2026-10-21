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
from yishu_core.symbols import HEXAGRAM_TRIGRAMS  # noqa: E402
from version_collate import norm  # noqa: E402

BR = "子丑寅卯辰巳午未申酉戌亥"
SRC_DIR = DISC / "data" / "sources"
GRAD = DISC / "data" / "cases" / "verifications_graduation.json"
OUT = DISC / "data" / "cases" / "verifications_triage.json"

LOOSE_YING = re.compile(r"([" + BR + r"])(?:日|月|年)(?:而|则)?[应應验驗]|"
                        r"[应應验驗]于?[甲乙丙丁戊己庚辛壬癸]?([" + BR + r"])(?:日|月|年)|"
                        r"果于?[甲乙丙丁戊己庚辛壬癸]?([" + BR + r"])(?:日|月|年)|"
                        r"后[一二两三四五六七八九十0-9]+日[而]?[应應验驗]?")
DATE_PAT = re.compile(r"([子丑寅卯辰巳午未申酉戌亥])月([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])日")


def triage() -> int:
    grad = json.loads(GRAD.read_text(encoding="utf-8"))
    rows = [r for r in grad["rows"] if r.get("status") == "partial_needs_human"]
    if not rows:
        print("× partial 条目 0——先核毕业册，不静默出空 triage")
        return 1
    cache = {}
    buckets = {"A_有验支候选": [], "A_无验支结案候选": [], "B_异写候选": [],
               "C_深回溯命中": [], "C_仍缺日期结案候选": []}
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
                buckets["A_有验支候选"].append({
                    "id": r["source_id"], "line": r["line"], "file": f,
                    "hits": [m.group(0) for m in ms[:4]],
                    "context": block[:120]})
            else:
                buckets["A_无验支结案候选"].append({"id": r["source_id"], "why": "宽松式仍无候选——素材缺验支"})
        elif why.startswith("卦名异写"):
            toks = re.findall(r"'([^']+)'", why)[:2]
            near = []
            for t in toks:
                n = norm(t).rstrip("卦")
                cands = [k for k in HEXAGRAM_TRIGRAMS if n.endswith(k) or k.endswith(n) or k in n]
                near.append({"token": t, "candidates": cands[:3]})
            buckets["B_异写候选"].append({"id": r["source_id"], "line": r["line"], "file": f, "near": near})
        elif why.startswith("有日期键") or "日期" in why:
            lo2 = max(0, lo - 80)
            seg = "\n".join(norm(x) for x in lines[lo2:lo + 1])
            hits = list(DATE_PAT.finditer(seg))
            if hits:
                buckets["C_深回溯命中"].append({"id": r["source_id"], "line": r["line"], "file": f,
                                                "date_hit": hits[-1].group(0)})
            else:
                buckets["C_仍缺日期结案候选"].append({"id": r["source_id"], "why": "80 行内仍无日期键"})
        else:
            buckets.setdefault("Z_其他", []).append({"id": r["source_id"], "why": why[:40]})
    doc = {"generated_at": datetime.now().isoformat(timespec="seconds"),
           "_comment": "观察册：分诊不改判——『结案候选』也须人签字后才算 §六.5 诚实结案；"
                       "B 桶异写候选是 TRAD 表增补提案非既成事实",
           "input": len(rows), "buckets": {k: len(v) for k, v in buckets.items()},
           "rows": buckets}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print("√ triage 册落成 %s｜partial %d 条 → %s"
          % (OUT.name, len(rows), doc["buckets"]))
    print("  人可速裁面：A_有候选 %d（一键定夺）＋B 异写 %d（对照候选）＋C 命中 %d；"
          "结案候选 %d＋%d 待签"
          % (len(buckets["A_有验支候选"]), len(buckets["B_异写候选"]), len(buckets["C_深回溯命中"]),
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
    print("√ selftest：验支宽松式/日期式正负例 全过" if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="partial 机械预分诊（观察册，不改判）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return triage()


if __name__ == "__main__":
    raise SystemExit(main())
