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
    parts.append("> 生成器 `dev_tools/adjudication_brief.py`；勾选后由**后续正式批**执行，本简报不构成变更授权。\n")

    # A. 候选入册（签字面）
    cs = cand["candidates"]
    parts.append(f"\n## A. 入册候选 {len(cs)} 条（213/215 批双器共识草稿；含 dup_of 标记者与首现者同盘多注）\n")
    for c in cs:
        g = c.get("gaps") or []
        parts.append("- [ ] **%s**｜%s｜%s之%s｜应期 %s｜question=%s" % (
            c["id"].replace("RC-VER-", ""), c["input"].get("date"),
            (c["hexagram"] or {}).get("original"), (c["hexagram"] or {}).get("changed") or "—",
            (c["expected"] or {}).get("yingqi") or "—", (c.get("question") or "待给")))
        parts.append("      原文：%s" % (c.get("source_quote") or "")[:96])
        if g:
            parts.append("      开口：%s" % "；".join(g))
        parts.append("      决策：□入（去重后并入外部集）　□弃（登记理由）　□改＿＿＿＿")

    # B. 双器分歧（读数裁决面）
    nb = [r for r in rec["rows"] if r["verdict"] != "consensus"]
    parts.append(f"\n## B. 复部分歧 {len(nb)} 条（201 批 A/B 双解析器不一致，需裁读数）\n")
    for r in nb:
        parts.append("- [ ] **%s**（%s L%d）%s" % (r["id"].replace("VER-", ""), r["file"], r["line"], r["verdict"]))
        parts.append("      A=%s" % json.dumps(r["a"], ensure_ascii=False)[:110])
        parts.append("      B=%s" % json.dumps(r["b"], ensure_ascii=False)[:110])
        parts.append("      决策：□A 对　□B 对　□都错（改写）＿＿＿＿")

    # C. 分诊真分歧＋兜底
    tz = tri["rows"]
    parts.append(f"\n## C. 分诊真分歧 {len(tz.get('B_真分歧需人', []))} 条＋兜底 {len(tz.get('B_异写候选', []))} 条（202 批）\n")
    for r in tz.get("B_真分歧需人", []):
        parts.append("- [ ] **%s**（L%d）A=%s｜B=%s" % (
            r["id"].replace("VER-", ""), r["line"],
            json.dumps(r.get("a"), ensure_ascii=False)[:70],
            json.dumps(r.get("b"), ensure_ascii=False)[:70]))
        parts.append("      决策：□取A　□取B　□另裁＿＿＿＿")
    for r in tz.get("B_异写候选", []):
        parts.append("- [ ] 兜底 **%s**（L%d）毕业报错串疑为噪声：%s——决策：□结案（写明噪声根因）　□重读　"
                     % (r["id"].replace("VER-", ""), r["line"],
                        json.dumps(r.get("near"), ensure_ascii=False)[:80]))

    # D. 验支候选速裁
    parts.append(f"\n## D. 验支宽松候选 {len(tz.get('A_有验支候选', []))} 条（199/202 批命中，人只定夺是否采信）\n")
    for r in tz.get("A_有验支候选", []):
        parts.append("- [ ] **%s**（%s L%d）命中 %s｜块：%s" % (
            r["id"].replace("VER-", ""), r["file"], r["line"],
            "、".join(r.get("hits") or [])[:60], (r.get("context") or "").replace("\n", " ")[:70]))
        parts.append("      决策：□采信入候选　□否（结案）")

    # E. 结案候选批量签字
    parts.append(f"\n## E. 结案候选 {len(tz.get('A_无验支结案候选', []))} 条（宽松式亦无验支——§六.5 类，一次签字批量结案）\n")
    parts.append("- [ ] **整批签字**：确认这 %d 条按「素材缺验支」结案（逐条 id 见 verifications_triage.json 同名桶）；"
                 "任一不服者单独上提进 D 形。\n" % len(tz.get("A_无验支结案候选", [])))

    text = "\n".join(parts) + "\n"
    changed = OUT.exists() and OUT.read_text(encoding="utf-8") != text
    if changed or not OUT.exists():
        OUT.write_text(text, encoding="utf-8")
    n = sum(len(v) for k, v in tri["rows"].items()) + len(nb) + len(cs)
    print("√ 简报%s：%d 事项入册 %s（A%d B%d C%d D%d E批%d）"
          % ("已刷新" if changed else "无变化保持", n, OUT.name,
             len(cs), len(nb), len(tz.get("B_真分歧需人", [])) + len(tz.get("B_异写候选", [])),
             len(tz.get("A_有验支候选", [])), len(tz.get("A_无验支结案候选", []))))
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
        if "待裁简报" not in t or "决策" not in t:
            fails.append("简报未产出或缺决策栏")
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
