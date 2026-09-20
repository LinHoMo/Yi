# -*- coding: utf-8 -*-
"""生成样例完整报告 + 门户用数据。"""
import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Lin\Desktop\skills\liu-yao")
sys.path.insert(0, str(ROOT / "scripts"))

from liuyao_engine import build_hexagram_result
from thinking_chain import run_thinking_chain
from human_narrative import build_human_narrative, render_human_markdown
from visualization import build_html_report
from run_blind_v4 import date_from_str, hex2yao
from advice_framework import generate_advice

cc = json.load(open(ROOT / "data" / "cases" / "classical_cases.json", encoding="utf-8"))
blind = json.load(open(ROOT / "data" / "cases" / "blind_engine_output_v5.json", encoding="utf-8"))
eval_sum = json.load(open(ROOT / "data" / "cases" / "blind_eval_v8_summary.json", encoding="utf-8"))

samples = []
for cid in ("ZS001", "ZS005", "ZS007", "ZS012", "ZS015", "ZS016"):
    case = next(c for c in cc["cases"] if c["id"] == cid)
    d = date_from_str(case["input"]["date"])
    yao = hex2yao(case["hexagram"]["original"], case["hexagram"].get("changed"))
    explicit = None
    if d.get("day_sb") or d.get("month_branch"):
        explicit = {}
        if d.get("day_sb"):
            explicit["day_sb"] = d["day_sb"]
        if d.get("month_branch"):
            explicit["month_sb"] = "甲" + d["month_branch"]
    h = build_hexagram_result(
        yao, case["question"], "manual",
        d["year"], d["month"], d["day"], 10, explicit_time=explicit,
    )
    tc = run_thinking_chain(h)
    human = build_human_narrative(h)
    h["human_narrative"] = human
    try:
        h["section_advice"] = generate_advice(
            (tc.get("step5_synthesis") or {}).get("verdict", ""),
            case["question"], h,
        )
    except Exception:
        pass
    html = build_html_report(h)
    out_html = ROOT / f"sample_report_{cid}.html"
    out_html.write_text(html, encoding="utf-8")

    s2 = tc.get("step2_use_god_identification") or {}
    s5 = tc.get("step5_synthesis") or {}
    samples.append({
        "id": cid,
        "question": case["question"],
        "hexagram": h["original_hexagram"]["name"],
        "changed": (h.get("changed_hexagram") or {}).get("name"),
        "palace": h["original_hexagram"].get("palace"),
        "generation": h["original_hexagram"].get("generation"),
        "time": h.get("divination_time", {}),
        "empty": h.get("empty_branches", []),
        "use_god": human.get("use_god"),
        "verdict": s5.get("verdict"),
        "final_score": s5.get("final_score"),
        "confidence": s5.get("confidence"),
        "yingqi": (s5.get("timing") or {}).get("summary_text"),
        "yingqi_branches": (s5.get("timing") or {}).get("key_branches") or [],
        "pattern_tags": tc.get("reasoning_chain", []),
        "human": human,
        "reasoning_chain": tc.get("reasoning_chain", []),
        "yao_lines": h["original_hexagram"]["yao_lines"],
        "expected": case.get("expected", {}),
        "blind_score": next((c.get("verdict") for c in blind["cases"] if c.get("id") == cid), None),
        "html_file": out_html.name,
    })
    print(cid, "html", out_html.name, "verdict", s5.get("verdict"), "human", human.get("headline", "")[:40])

# 主样例（门户默认打开）
main = samples[0]
(ROOT / "sample_report_final.html").write_text(
    (ROOT / "sample_report_ZS001.html").read_text(encoding="utf-8"), encoding="utf-8"
)

portal_data = {
    "project": "六爻纳甲预测系统",
    "version": "v8",
    "blind": {
        "metric": "古典案例库对齐分（非现实世界预言命中率）",
        "avg": eval_sum.get("avg"),
        "scores": eval_sum.get("scores"),
        "note": "衡量引擎输出与《增删卜易》等古籍案例要点的一致性。现实占卜属象征推演，不能承诺固定命中率。",
        "history": [
            {"label": "v6 基线", "avg": 62.5},
            {"label": "v7 handoff", "avg": 90.3},
            {"label": "v8 当前", "avg": eval_sum.get("avg")},
        ],
    },
    "samples": samples,
    "pipeline": [
        {"step": "01", "title": "收集信息", "desc": "问题、起卦方式、时间"},
        {"step": "02", "title": "引擎排盘", "desc": "liuyao_engine.py 纳甲装卦，禁止手排"},
        {"step": "03", "title": "解析 JSON", "desc": "核对本卦/用神/动变字段"},
        {"step": "04", "title": "五步思维链", "desc": "观局→定用→断旺→察变→综合"},
        {"step": "05", "title": "人话解读", "desc": "human_narrative 口语化输出"},
        {"step": "06", "title": "HTML 导出", "desc": "visualization 报告 + 交互门户"},
    ],
}

out = ROOT / "assets" / "portal_data.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(portal_data, ensure_ascii=False, indent=2), encoding="utf-8")
print("portal data ->", out)
print("eval avg", eval_sum.get("avg"))
