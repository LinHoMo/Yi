# -*- coding: utf-8 -*-
"""读数对账台（第两百批·防御性维护）——登记值 vs 当前 HEAD 重放值，逐位核对。

176→199 批把二十余个关键读数写散在 CHANGELOG/README/CAPABILITY 里。凡散落的数字，
终有一天和产生它的代码分家（§六.3 的时延版）。本器把**每个对外声称的读数**做成可重放
断言：expected 逐字来自登记文本（注明批次），actual 由当前 HEAD 现场重跑取回。

    python dev_tools/readout_ledger.py --quick   # 快组（纯文本/装配/小扫描，秒级~2min）
    python dev_tools/readout_ledger.py           # 全量（含两科评测与外部集，十分钟级）
    python dev_tools/readout_ledger.py --selftest

对账失败＝读数已与代码分家：要么改代码前偷动了读数（缺陷），要么登记文本过期（§六.2）——
两种都必须立案，不许静默刷新基线。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
ROOT = DISC.parent
sys.path.insert(0, str(DISC / "scripts"))
sys.path.insert(0, str(HERE))
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402


def sh(args, cwd=None):
    r = subprocess.run([sys.executable, "-X", "utf8"] + args,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(cwd or DISC))
    return (r.stdout or "") + (r.stderr or "")


def grab(text, pat, group=1):
    m = re.search(pat, text)
    return m.group(group) if m else None


# ── 读数账目：id -> (登记出处, 取数函数, 比对) ──────────────────────────────
def checks():
    out = []

    def add(cid, src, fn, expect):
        out.append((cid, src, fn, expect))

    # --- 六爻内部集 ---
    def c_tune(t):
        s = sh(["scripts/evaluate.py", "--split", "tune"])
        return (grab(s, r"平均分 = ([0-9.]+)%.*n=20"),
                grab(s, r"strict top-1 命中 ([0-9.]+)%"),
                grab(s, r"平均排在第 ([0-9.]+) 位"))
    add("liuyao.tune(97.9/64.7/1.53)", "README 表/172批", c_tune,
        ("97.9", "64.7", "1.53"))

    def c_holdout(t):
        s = sh(["scripts/evaluate.py", "--split", "holdout"])
        return (grab(s, r"平均分 = ([0-9.]+)%"),
                grab(s, r"strict top-1 命中 ([0-9.]+)%"),
                grab(s, r"平均排在第 ([0-9.]+) 位"))
    add("liuyao.holdout(90.2/50.0/1.6)", "README 表", c_holdout,
        ("90.2", "50.0", "1.6"))

    # --- 外部集 ---
    def c_wiki(t):
        s = sh(["scripts/evaluate.py", "--split", "wikisource_holdout"])
        return (grab(s, r"平均分 = ([0-9.]+)%"), grab(s, r"strict top-1 命中 ([0-9.]+)%"),
                grab(s, r"平均排在第 ([0-9.]+) 位"))
    add("liuyao.wikisource(62.4/27.3/2.19)", "README 表/181批", c_wiki,
        ("62.4", "27.3", "2.19"))

    def c_dz(t):
        s = sh(["scripts/evaluate.py", "--split", "zengshan_dz_holdout"])
        return (grab(s, r"平均分 = ([0-9.]+)%"), grab(s, r"strict top-1 命中 ([0-9.]+)%"))
    add("liuyao.zengshan_dz(53.4/33.3)", "README 表", c_dz, ("53.4", "33.3"))

    def c_window2(t):
        s = sh(["dev_tools/window_report.py"])
        blk = s.split("═ zengshan_dz_holdout")[0]
        # 实际格式是编号行「  1   12/44 =  27.3%」（200 批立案教训：模式抄实样非凭印象）
        t1 = re.search(r"^\s+1\s+(\d+)/(\d+) =\s*([\d.]+)%", blk, re.M)
        t3 = re.search(r"^\s+3\s+(\d+)/(\d+) =\s*([\d.]+)%", blk, re.M)
        return ((t1.group(3), t3.group(3)) if t1 and t3 else (None, None))
    add("liuyao.wiki top1/top3(27.3/52.3)", "181/199批", c_window2, ("27.3", "52.3"))

    def c_baselines(t):
        s = sh(["dev_tools/baselines.py"])
        yong = re.search(r"用神值支\s+(\d+)/\s*\d+ =\s*([\d.]+)%", s)
        day = re.search(r"日辰即答\s+(\d+)/\s*\d+ =\s*([\d.]+)%", s)
        return ((yong.group(2), day.group(2)) if yong and day else (None, None))
    add("liuyao.baselines 用神18.2/日辰4.5", "183批", c_baselines, ("18.2", "4.5"))

    # --- 版本对拍/毕业/分诊（JSON 直读 + 现场重生成核对） ---
    add("liuyao.collate(卦面0/47 判词1/37)", "185批", lambda t: _collate_now(), ("0/47", "1/37"))
    add("liuyao.graduation(18/63/161)", "189批", lambda t: _json_counts(
        "data/cases/verifications_graduation.json", "summary",
        ("restorable", "partial_needs_human", "unrestorable")), ("18", "63", "161"))
    add("liuyao.triage(15/35/13)", "199批", lambda t: _json_counts(
        "data/cases/verifications_triage.json", None,
        ("A_有验支候选", "A_无验支结案候选", "B_异写候选"), key="buckets"), ("15", "35", "13"))
    add("liuyao.restorable_recheck(共识10/分歧8)", "201批", lambda t: _json_counts(
        "data/cases/restorable_recheck.json", None, ("consensus", "needs_human")), ("10", "8"))

    # --- 裁决表/治理图/指纹 ---
    add("liuyao.adjudications(7=5+1+1)", "188批", lambda t: _adjud_counts(), ("7", "5", "1", "1"))
    add("liuyao.golden(b716/a46f)", "193批", lambda t: _golden("liuyao"),
        ("b7162bfc99e2cce8", "a46f7374276a17a6"))
    add("bazi.golden(2a4c/1a0f)", "176批前", lambda t: _golden("bazi"),
        ("2a4c9258d6c1e4cb", "1a0f165ebfa7b6da"))
    add("governance(48/34, blk 20/19)", "194批（201 批更新：+复核器；200 批 +分诊/对账）", lambda t: _gov_counts(), ("48", "34", "20", "19"))

    # --- 八字侧 ---
    def c_bazi_holdout(t):
        s = sh(["scripts/evaluate.py", "--split", "holdout"], cwd=ROOT / "bazi")
        return grab(s, r"平均分 = ([0-9.]+)%")
    add("bazi.holdout(97.6)", "bazi README", c_bazi_holdout, ("97.6",))

    def c_bazi_base(t):
        s = sh(["dev_tools/baselines.py", "--split", "holdout"], cwd=ROOT / "bazi")
        th = re.search(r"pattern：引擎 (\d+)/(\d+) =\s*([\d.]+)%", s)  # 拿错维了？改 tiaohou 行
        m_t = re.search(r"tiaohou：引擎 (\d+)/(\d+) =\s*([\d.]+)%", s)
        m_p = re.search(r"pattern：引擎 (\d+)/(\d+) =\s*([\d.]+)%", s)
        m_c = re.search(r"先验定答从\s+(\d+)/(\d+) =\s*([\d.]+)%", s)
        vals = tuple(x.group(3) if x else None for x in (m_t, m_p, m_c))
        mb = re.search(r"定答\(tune边际\)\s+\d+/\s*\d+ =\s*[\d.]+% ｜配对 b=(\d+) c=(\d+)", s)
        return vals + ((mb.group(1), mb.group(2)) if mb else (None, None))
    add("bazi(tiaohou96.2 pattern80.6 常数从100 b42c0)", "187批", c_bazi_base,
        ("96.2", "80.6", "100.0", "42", "0"))

    # --- 前瞻通道在册 0 ---
    add("prospective 在册 0 条", "177/178批", lambda t: (
        "0" if not (DISC / "data" / "feedback" / "predictions.jsonl").exists()
        else str(len([1 for _ in open(DISC / "data" / "feedback" / "predictions.jsonl",
                                     encoding="utf-8") if _.strip()])),), ("0",))
    return out


def _collate_now():
    s = sh(["dev_tools/version_collate.py"])
    g = re.search(r"卦面冲突率 = (\d+/\d+)", s)
    p = re.search(r"判词冲突率 = (\d+/\d+)", s)
    return ((g.group(1), p.group(1)) if g and p else (None, None))


def _json_counts(rel, top, keys, key=None):
    d = json.loads((DISC / rel).read_text(encoding="utf-8"))
    src = d.get(top) if top else (d.get(key) if key else d)
    return tuple(str(src.get(k)) for k in keys) if isinstance(src, dict) else (None,) * len(keys)


def _adjud_counts():
    d = json.loads((DISC / "data" / "rules" / "adjudications.json").read_text(encoding="utf-8"))
    c = {"settled_by_source": 0, "frozen_by_user": 0, "open_conflict": 0}
    for e in d["entries"]:
        c[e["status"]] += 1
    return (str(d["count"]), str(c["settled_by_source"]), str(c["frozen_by_user"]),
            str(c["open_conflict"]))


def _golden(disc):
    s = sh(["dev_tools/golden.py", "verify"], cwd=ROOT / disc)
    m = re.search(r"机械 ([0-9a-f]{16})｜措辞 ([0-9a-f]{16})", s)
    return (m.group(1), m.group(2)) if m else (None, None)


def _gov_counts():
    s = sh(["dev_tools/governance_map.py"])
    l = re.search(r"liuyao：(\d+) 脚本｜blocking (\d+)", s)
    b = re.search(r"bazi：(\d+) 脚本｜blocking (\d+)", s)
    return ((l.group(1), b.group(1), l.group(2), b.group(2)) if l and b else (None,) * 4)


QUICK_SKIP = {"liuyao.wiki top1/top3(27.3/52.3)", "liuyao.baselines 用神18.2/日辰4.5",
              "bazi(tiaohou96.2 pattern80.6 常数从100 b42c0)",
              "liuyao.collate(卦面0/47 判词1/37)"}


def run(quick: bool) -> int:
    bad = 0
    print("═ 读数对账台（登记值 vs HEAD 重放值）%s ═" % ("quick" if quick else "full"))
    for cid, src, fn, expect in checks():
        if quick and cid in QUICK_SKIP:
            print("  ~ %-46s 跳过（full 才跑）" % cid)
            continue
        try:
            got = fn(None)
            if not isinstance(got, tuple):
                got = (got,)
        except Exception as e:  # noqa: BLE001
            print("  ! %-46s 取数异常 %s" % (cid, str(e)[:40]))
            bad += 1
            continue
        def norm(x):
            if isinstance(x, tuple):
                return tuple(str(i) for i in x)
            return str(x)
        ok = all(norm(g) == norm(e) for g, e in zip(got, expect)) and len(got) == len(expect)
        print("  %s %-46s（登记：%s）%s" % ("√" if ok else "×", cid, src,
              "" if ok else " 实得 %r ≠ 期望 %r" % (got, expect)))
        bad += 0 if ok else 1
    print("═ 结论：%s（bad=%d）——任何 × 都是读数与代码分家的现形，按 §六.2 立案处理，"
          "禁止静默改期望值 ═" % ("全部对账一致" if bad == 0 else "存在分家读数", bad))
    return 1 if bad else 0


def selftest() -> int:
    fails = []
    # 自测解析器本体：golden 与 evaluate 的输出必须可抽——对账器不许先瞎
    s = sh(["dev_tools/golden.py", "verify"], cwd=ROOT / "liuyao")
    if not re.search(r"机械 ([0-9a-f]{16})｜措辞 ([0-9a-f]{16})", s):
        fails.append("golden 解析式失配（对账器瞎了）")
    print("√ selftest：抽取器在线（golden 双指纹可抽）" if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="读数对账台（登记值 vs HEAD 重放值）")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return run(args.quick)


if __name__ == "__main__":
    raise SystemExit(main())
