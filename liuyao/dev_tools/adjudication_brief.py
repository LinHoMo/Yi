# -*- coding: utf-8 -*-
"""裁决简报生成器（第两百二十六批·值守面）——把六本观察册里等人裁的事汇编成一页。

原则：**纯装配零新判断**——只从在册观察册搬运原文引证与既有读数，不添加任何解读；
每事项附决策勾选框（入/弃/改），人写完勾选项后由后续正式批执行（本简报不授权任何变更）。
生成物 `docs/ADJUDICATION-BRIEF.md` 随观察册变化重生成即可（write_stable 幂等）。

    python dev_tools/adjudication_brief.py            # 生成/刷新简报
    python dev_tools/adjudication_brief.py --selftest
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(DISC / "scripts"))
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from stable_write import write_stable  # noqa: E402

OUT = DISC / "docs" / "ADJUDICATION-BRIEF.md"


def build() -> int:
    tri = json.loads((DISC / "data" / "cases" / "verifications_triage.json").read_text(encoding="utf-8"))
    rec = json.loads((DISC / "data" / "cases" / "restorable_recheck.json").read_text(encoding="utf-8"))
    cand = json.loads((DISC / "data" / "cases" / "restorable_candidates.json").read_text(encoding="utf-8"))
    parts = []
    parts.append("# 六爻·待裁简报（机械汇编，零新判断）\n")
    parts.append("> 生成器 `dev_tools/adjudication_brief.py`；未勾选项由**后续正式批**执行，"
                 "已执行的裁决与依据见各段「已判／已裁／已复核」小节（本简报不构成变更授权）。\n")

    # A. 候选入册（签字面）
    cs = cand["candidates"]
    cs_dec = [c for c in cs if c.get("enroll_verdict")]
    cs_pend = [c for c in cs if not c.get("enroll_verdict")]
    parts.append(f"\n## A. 入册候选 {len(cs_pend)} 条待裁（213/215 批双器共识草稿；"
                 f"已判 {len(cs_dec)} 条见 A2）\n")
    for c in cs_pend:
        g = c.get("gaps") or []
        parts.append("- [ ] **%s**｜%s｜%s之%s｜应期 %s｜question=%s" % (
            c["id"].replace("RC-VER-", ""), c["input"].get("date"),
            (c["hexagram"] or {}).get("original"), (c["hexagram"] or {}).get("changed") or "—",
            (c["expected"] or {}).get("yingqi") or "—", (c.get("question") or "待给")))
        parts.append("      原文：%s" % (c.get("source_quote") or "")[:96])
        if g:
            parts.append("      开口：%s" % "；".join(g))
        parts.append("      决策：□入（去重后并入外部集）　□弃（登记理由）　□改＿＿＿＿")

    if cs_dec:
        parts.append(f"\n## A2. 入册候选·已判 {len(cs_dec)} 条（逐条查建器去留理由）\n")
        parts.append("查法：`python dev_tools/build_zengshan_dz_cases.py --dry-run --why <ID>`——"
                     "建器会给出「与在册同案／无应期锚／未产出块」三类理由之一。\n")
        for c in cs_dec:
            parts.append("- [x] **%s**｜%s之%s｜→ **%s**" % (
                c["id"].replace("RC-VER-", ""), c["input"].get("date"),
                (c["hexagram"] or {}).get("original"),
                c["enroll_verdict"]))
            parts.append("      依据：%s" % (c.get("enroll_basis") or "")[:200])

    # B. 双器分歧（读数裁决面）
    # 370 批：已裁的（带 decision）不再进待裁桶——否则「裁过」与「没裁」在简报里长得一样，
    # 下一轮值守还要把它们重新读一遍。裁决与依据落在 restorable_recheck.json 的 row 上。
    decided = [r for r in rec["rows"] if r["verdict"] != "consensus" and r.get("decision")]
    nb = [r for r in rec["rows"] if r["verdict"] != "consensus" and not r.get("decision")]
    parts.append(f"\n## B. 复部分歧 {len(nb)} 条（201 批 A/B 双解析器不一致，需裁读数；已裁 {len(decided)} 条见 B2）\n")
    for r in nb:
        parts.append("- [ ] **%s**（%s L%d）%s" % (r["id"].replace("VER-", ""), r["file"], r["line"], r["verdict"]))
        parts.append("      A=%s" % json.dumps(r["a"], ensure_ascii=False)[:110])
        parts.append("      B=%s" % json.dumps(r["b"], ensure_ascii=False)[:110])
        parts.append("      决策：□A 对　□B 对　□都错（改写）＿＿＿＿")

    if decided:
        parts.append(f"\n## B2. 已裁 {len(decided)} 条（逐字取证，不再待裁）\n")
        for r in decided:
            side = (r.get("decision") or "?").upper()
            chosen = r.get("a") if side == "A" else r.get("b") if side == "B" else None
            parts.append("- [x] **%s**（%s L%d）→ 取 %s：%s" % (
                r["id"].replace("VER-", ""), r["file"], r["line"], side,
                json.dumps(chosen, ensure_ascii=False)[:90]))
            parts.append("      依据：%s" % (r.get("decision_basis") or "")[:200])
            if r.get("decision_stale_b"):
                parts.append("      ⚠ B 器输出已变（当时 B=%s），请复核裁决是否仍成立"
                             % json.dumps(r["decision_stale_b"], ensure_ascii=False)[:80])

    # C. 分诊真分歧＋兜底
    tz = tri["rows"]
    _c1 = tz.get("B_真分歧需人", [])
    _c2 = tz.get("B_异写候选", [])
    _c1d = [r for r in _c1 if r.get("decision")]
    _c1p = [r for r in _c1 if not r.get("decision")]
    _c2d = [r for r in _c2 if r.get("decision")]
    _c2p = [r for r in _c2 if not r.get("decision")]
    parts.append(f"\n## C. 分诊真分歧 {len(_c1p)} 条＋兜底 {len(_c2p)} 条待裁（202 批；"
                 f"已裁 {len(_c1d) + len(_c2d)} 条见 C2）\n")
    for r in _c1p:
        parts.append("- [ ] **%s**（L%d）A=%s｜B=%s" % (
            r["id"].replace("VER-", ""), r["line"],
            json.dumps(r.get("a"), ensure_ascii=False)[:70],
            json.dumps(r.get("b"), ensure_ascii=False)[:70]))
        parts.append("      决策：□取A　□取B　□另裁＿＿＿＿")
    for r in _c2p:
        parts.append("- [ ] 兜底 **%s**（L%d）毕业报错串疑为噪声：%s——决策：□结案（写明噪声根因）　□重读　"
                     % (r["id"].replace("VER-", ""), r["line"],
                        json.dumps(r.get("near"), ensure_ascii=False)[:80]))
    if _c1d or _c2d:
        parts.append(f"\n## C2. 已裁 {len(_c1d) + len(_c2d)} 条（逐字取证回原文真头）\n")
        for r in _c1d:
            parts.append("- [x] **%s**（L%d）→ **%s**" % (
                r["id"].replace("VER-", ""), r["line"], r["decision"]))
            parts.append("      依据：%s" % (r.get("decision_basis") or "")[:200])
        for r in _c2d:
            parts.append("- [x] 兜底 **%s**（L%d）→ **%s**" % (
                r["id"].replace("VER-", ""), r["line"], r["decision"]))
            parts.append("      依据：%s" % (r.get("decision_basis") or "")[:200])

    # D. 验支候选速裁
    _dz_all = tz.get("A_有验支候选", [])
    dz_dec = [r for r in _dz_all if r.get("decision")]
    dz_pend = [r for r in _dz_all if not r.get("decision")]
    parts.append(f"\n## D. 验支宽松候选 {len(dz_pend)} 条待裁（199/202 批命中，人只定夺是否采信；"
                 f"已裁 {len(dz_dec)} 条见 D2）\n")
    for r in dz_pend:
        parts.append("- [ ] **%s**（%s L%d）命中 %s｜块：%s" % (
            r["id"].replace("VER-", ""), r["file"], r["line"],
            "、".join(r.get("hits") or [])[:60], (r.get("context") or "").replace("\n", " ")[:70]))
        parts.append("      决策：□采信入候选　□否（结案）")

    if dz_dec:
        n_y = sum(1 for r in dz_dec if r["decision"] == "采信")
        _pc = [r.get("postcheck") for r in dz_dec if r.get("postcheck")]
        _n_in = sum(1 for p in _pc if p.get("status") == "已在册")
        _n_bad = sum(1 for p in _pc if p.get("status") == "验收有误")
        _n_open = sum(1 for p in _pc if p.get("status") == "未入册")
        _extra = (f"；采信复核后可升 0：已在册 {_n_in}／验收有误 {_n_bad}／未入册 {_n_open}"
                  if _pc else "")
        parts.append(f"\n## D2. 验支宽松候选·已裁 {len(dz_dec)} 条"
                     f"（同案采信 {n_y}／异案否 {len(dz_dec) - n_y}{_extra}）\n")
        parts.append("判定口径：**验支上方最近的卦例头是否等于本条卦例头**——同头即同案；"
                     "异头说明验支落在下一个卦例里，是串味，不得采信。逐条行号见依据。"
                     "399 批另对 8 条采信做升册复核：已在册者不重复计数，串味者更正，"
                     "无独立日期者记未入册。\n")
        for r in dz_dec:
            parts.append("- [x] **%s**（%s L%d）→ **%s**：%s" % (
                r["id"].replace("VER-", ""), r["file"], r["line"], r["decision"],
                "／".join(r.get("hits") or [])))
            parts.append("      依据：%s" % (r.get("decision_basis") or "")[:180])
            p = r.get("postcheck")
            if p:
                parts.append("      升册复核：**%s**%s" % (
                    p.get("status") or "?", ("（%s）" % p["case_id"]) if p.get("case_id") else ""))
                parts.append("      复核依据：%s" % (p.get("basis") or "")[:200])

    # E. 结案候选批量签字（399 批：已复核的进 E2，未复核的才留待签）
    e_all = tz.get("A_无验支结案候选", [])
    e_dec = [r for r in e_all if r.get("decision")]
    e_pend = [r for r in e_all if not r.get("decision")]
    parts.append(f"\n## E. 结案候选 {len(e_pend)} 条待签"
                 f"（宽松式亦无验支——§六.5 类；已复核 {len(e_dec)} 条见 E2）\n")
    if e_pend:
        parts.append("- [ ] **整批签字**：确认这 %d 条按「素材缺验支」结案"
                     "（逐条 id 见 verifications_triage.json 同名桶）；任一不服者单独上提进 D 形。\n"
                     % len(e_pend))
    if e_dec:
        n_close = sum(1 for r in e_dec if r.get("decision") == "结案")
        n_open = len(e_dec) - n_close
        parts.append(f"\n## E2. 已复核 {len(e_dec)} 条（结案 {n_close}／未入册 {n_open}）\n")
        _close_kinds = Counter(r.get("decision_kind") or "未分类" for r in e_dec
                               if r.get("decision") == "结案")
        parts.append("399 批口径：结案 %d 条细分＝%s；未入册 %d 条单列。"
                     "**整批签字的前提（35 条全按素材缺验支）不成立**：书载有验支、已在册、"
                     "只有时辰/相对日/节日、终身叙述各自单列，未硬签。\n"
                     % (n_close, "／".join("%s %d" % (k, v)
                                          for k, v in _close_kinds.most_common()), n_open))
        for r in e_dec:
            parts.append("- [x] **%s** → **%s**（%s）" % (
                r["id"].replace("VER-", ""), r.get("decision") or "?",
                r.get("decision_kind") or "未分类"))
            parts.append("      依据：%s" % (r.get("decision_basis") or "")[:240])

    text = "\n".join(parts) + "\n"
    changed = OUT.exists() and OUT.read_text(encoding="utf-8") != text
    if changed or not OUT.exists():
        OUT.write_text(text, encoding="utf-8")
    n = sum(len(v) for k, v in tri["rows"].items()) + len(nb) + len(cs)
    print("√ 简报%s：%d 事项入册 %s（A%d(已判%d) B%d C%d D%d(已裁%d) E%d(已复核%d)）"
          % ("已刷新" if changed else "无变化保持", n, OUT.name,
             len(cs_pend), len(cs_dec), len(nb), len(_c1p) + len(_c2p),
             len(dz_pend), len(dz_dec), len(e_pend), len(e_dec)))
    return 0


def selftest() -> int:
    fails = []
    for rel in ("data/cases/verifications_triage.json", "data/cases/restorable_recheck.json",
                "data/cases/restorable_candidates.json"):
        if not (DISC / rel).exists():
            fails.append("前置观察册缺失：" + rel)
    # 负例：观察册齐但生成物缺 → build 必须落文件且非空
    if not fails:
        build()
        t = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        # 399 批：A/B/C/D/E 全部裁清后简报不再有「决策：□」行；改用稳定标记「依据」＋E2。
        if "待裁简报" not in t or "依据" not in t or "## E2." not in t:
            fails.append("简报未产出或缺已裁依据/E2 段")
        if "可能" in t or "大概" in t or "或许" in t:
            fails.append("简报混入猜测措辞（装配器不许判断）")
    print("√ selftest：三前置册在、产物非空、无猜测措辞" if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="待裁事项一页简报（纯装配零新判断）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return build()


if __name__ == "__main__":
    raise SystemExit(main())
