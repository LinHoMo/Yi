# -*- coding: utf-8 -*-
"""T1: audit ZS021-030 vs tune set + case_library.md coverage."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
cases_path = ROOT / "data" / "cases" / "classical_cases.json"
lib_path = ROOT / "references" / "case_library.md"
out_path = ROOT / "data" / "cases" / "holdout_audit.md"

data = json.loads(cases_path.read_text(encoding="utf-8"))
cases = data["cases"]
by_id = {c["id"]: c for c in cases}
tune = [c for c in cases if c["id"] <= "ZS020"]
candidates = [c for c in cases if c["id"] > "ZS020"]

BRANCHES = set("子丑寅卯辰巳午未申酉戌亥")


def signature(c: dict) -> str:
    hx = c.get("hexagram") or {}
    q = (c.get("question") or "") + " " + (c.get("input") or {}).get("question", "")
    exp = c.get("expected") or {}
    # normalize question tokens
    toks = re.findall(r"[一-鿿]{2,}", q)
    core = "".join(sorted(set(toks), key=len, reverse=True)[:4])
    return f"{hx.get('original')}|{hx.get('changed')}|{exp.get('verdict')}|{exp.get('use_god')}|{exp.get('use_god_branch')}|{core[:24]}"


def topic_conflict(c: dict) -> str | None:
    topic = (c.get("topic") or "").strip()
    q = (c.get("question") or "") + (c.get("input") or {}).get("question", "")
    rules = [
        ("疾病", ["病", "疾", "愈", "医"]),
        ("出行", ["出行", "出外", "旅行", "行人"]),
        ("婚姻", ["婚", "姻", "嫁", "娶"]),
        ("官司", ["官", "讼", "诉"]),
        ("寻人", ["逃", "仆", "寻", "走失"]),
        ("求财", ["财", "价", "生意", "贸易", "赌", "银"]),
    ]
    for label, kws in rules:
        if topic == label:
            if not any(k in q for k in kws):
                # topic claims X but question lacks X keywords
                other = []
                for l2, kws2 in rules:
                    if l2 != topic and any(k in q for k in kws2):
                        other.append(l2)
                if other:
                    return f"topic={topic} 但 question 更像 {'/'.join(other)}"
    return None


tune_sigs = {c["id"]: signature(c) for c in tune}
lines = []
lines.append("# Holdout 数据审计（ZS021–030 + case_library）\n")
lines.append(f"- tune 集：{len(tune)} 例（ZS001–020）")
lines.append(f"- 候选扩展：{len(candidates)} 例（ZS021–030）\n")

lib_text = lib_path.read_text(encoding="utf-8") if lib_path.exists() else ""
lib_titles = re.findall(r"^## (案例[^\n]+)", lib_text, re.M)
lines.append(f"## case_library.md 标题（{len(lib_titles)}）\n")
for t in lib_titles:
    lines.append(f"- {t}")
lines.append("")

# fingerprint tune questions for library overlap
tune_q_blob = " ".join((c.get("question") or "") + (c.get("input") or {}).get("question", "") for c in tune)

lines.append("## ZS021–030 逐例建议\n")
lines.append("| ID | source | topic | question | expected | 冲突/重复 | 建议 |")
lines.append("|----|--------|-------|----------|----------|-----------|------|")

splits = {"tune": [c["id"] for c in tune], "holdout": [], "excluded": []}
holdout_details = []

for c in candidates:
    cid = c["id"]
    exp = c.get("expected") or {}
    hx = c.get("hexagram") or {}
    q = (c.get("question") or "") + " | " + (c.get("input") or {}).get("question", "")
    sig = signature(c)
    issues = []
    tc = topic_conflict(c)
    if tc:
        issues.append(tc)
    # near-duplicate tune
    dup_of = None
    for tid, tsig in tune_sigs.items():
        if tsig == sig:
            dup_of = tid
            break
        # looser: same original hex + same use_god + same verdict
        tcase = by_id[tid]
        te = tcase.get("expected") or {}
        th = tcase.get("hexagram") or {}
        if (
            th.get("original") == hx.get("original")
            and te.get("verdict") == exp.get("verdict")
            and te.get("use_god") == exp.get("use_god")
            and (exp.get("use_god_branch") or te.get("use_god_branch") or "")
            and exp.get("use_god_branch") == te.get("use_god_branch")
        ):
            # also check question overlap
            tq = tcase.get("question") or ""
            if tq and (tq[:6] in q or q[:6] in tq or (c.get("input") or {}).get("date", "") == (tcase.get("input") or {}).get("date", "")):
                dup_of = tid
                break
    if dup_of:
        issues.append(f"疑似重复 {dup_of}")
    # missing fields
    if not hx.get("original"):
        issues.append("无卦名")
    if not exp.get("verdict"):
        issues.append("无 verdict")
    if not exp.get("use_god"):
        issues.append("无 use_god")

    if issues and (dup_of or "无卦名" in issues or "无 verdict" in issues):
        advice = "excluded"
        splits["excluded"].append({"id": cid, "reason": "；".join(issues) if issues else "字段不足"})
    elif issues:
        # topic conflict only: can still be holdout after field fix
        advice = "holdout（校正 topic 后）"
        splits["holdout"].append(cid)
        holdout_details.append({"id": cid, "fix_topic": issues})
    else:
        advice = "holdout"
        splits["holdout"].append(cid)
        holdout_details.append({"id": cid, "fix_topic": []})

    exp_s = f"{exp.get('use_god')}@{exp.get('use_god_branch') or '—'} / {exp.get('verdict')}"
    lines.append(
        f"| {cid} | {c.get('source','')} | {c.get('topic','')} | {q[:48]} | {exp_s} | {';'.join(issues) or '—'} | {advice} |"
    )

lines.append("\n## case_library.md 与 JSON 重叠粗判\n")
# crude: library narrative questions vs tune/candidate questions
lib_blocks = re.split(r"^## ", lib_text, flags=re.M)
unstructured = []
for block in lib_blocks:
    if not block.startswith("案例"):
        continue
    title = block.split("\n", 1)[0].strip()
    body = block[:800]
    # find dates / hex names
    dates = re.findall(r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]日", body)
    has_expected = any(k in body for k in ("用神", "断", "吉", "凶", "应验"))
    # overlap if a distinctive date+topic appears in JSON
    matched = None
    blob_all = " ".join((c.get("question") or "") + (c.get("input") or {}).get("question", "") + (c.get("input") or {}).get("date", "") for c in cases)
    for d in dates[:3]:
        if d in blob_all:
            matched = d
            break
    status = f"日期 {matched} 已见于 JSON" if matched else "未见对应 JSON 痕迹"
    if not matched and has_expected:
        unstructured.append(title)
    lines.append(f"- **{title}** — {status}；dates={dates[:3]}")

lines.append("\n## 建议 holdout 名单（审计结论）\n")
lines.append("holdout IDs: " + ", ".join(splits["holdout"]) if splits["holdout"] else "holdout IDs: （空）")
lines.append("excluded: " + json.dumps(splits["excluded"], ensure_ascii=False))
lines.append("\n未结构化且可能可入库的 library 标题：")
for t in unstructured:
    lines.append(f"- {t}")

lines.append("\n## 下一步（T2）\n")
lines.append("- 写入 `data/cases/case_splits.json`")
lines.append("- 对 holdout 例校正 topic / 补齐 expected 字段")
lines.append("- library 未入库例在 T4 以 HO 编号补充，不得伪造卦象")

out_path.write_text("\n".join(lines), encoding="utf-8")
# also dump machine-readable draft splits
(ROOT / "data" / "cases" / "case_splits.draft.json").write_text(
    json.dumps({"splits": splits, "holdout_details": holdout_details, "unstructured_library": unstructured},
               ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print("wrote", out_path)
print("holdout", splits["holdout"])
print("excluded", splits["excluded"])
print("unstructured", unstructured)
