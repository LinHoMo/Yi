# -*- coding: utf-8 -*-
"""生成交付物：样例报告 + 门户数据，并把门户数据内嵌回 index.html。

    python scripts/build_portal_assets.py            # 用已有评测结果重建门户
    python scripts/build_portal_assets.py --run-eval # 先跑 evaluate 再重建

分数一律取自 `scripts/evaluate.py --save` 落盘的 data/cases/eval_{tune,holdout}.json，
**不再手写常量**：上一版把 v8 的 100.0 硬编在脚本里，引擎改了、门户照旧显示满分。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "core"))

OUT_REPORTS = ROOT / "outputs" / "reports"
EVAL_FILES = {"tune": ROOT / "data" / "cases" / "eval_tune.json",
              "holdout": ROOT / "data" / "cases" / "eval_holdout.json"}
SHOWCASE = ("ZS001", "ZS005", "ZS007", "ZS012", "ZS015", "ZS016")


def load_eval(split: str) -> dict | None:
    path = EVAL_FILES[split]
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_blind() -> dict:
    tune, holdout = load_eval("tune"), load_eval("holdout")
    if not tune:
        print("× 缺 data/cases/eval_tune.json，先跑：python scripts/evaluate.py --split tune --save")
        return {}
    strict = tune["results"]["strict"]
    disc = tune["results"].get("yingqi_discrimination") or {}
    blind = {
        "metric": "古籍案例对齐分（strict 口径）",
        "updated": date.today().isoformat(),
        "headline": (holdout or tune)["results"]["strict"]["avg"],
        "headline_split": "holdout（未参与调参）" if holdout else "tune",
        "headline_n": (holdout or tune)["results"]["strict"]["n"],
        "tune": {"avg": strict["avg"], "n": strict["n"], "min": strict.get("min"),
                 "scores": [r.get("pct") for r in strict["rows"] if "dims" in r],
                 "ids": [r.get("id") for r in strict["rows"] if "dims" in r]},
        "dims": strict.get("dims"),
        "yingqi": {
            "top1": disc.get("top1_hit_rate"),
            "avg_rank": disc.get("avg_rank_of_correct"),
            "set_size": disc.get("avg_candidate_set_size"),
            "random_expectancy": disc.get("random_full_coverage_expectancy"),
            "n": disc.get("cases_with_yingqi"),
        },
        "note": ("衡量引擎输出与《增删卜易》等古籍案例要点的一致性，"
                 "属回归指标，不是现实世界预言命中率。real 占卜为象征推演，给方向不给定论。"),
    }
    if holdout:
        hs = holdout["results"]["strict"]
        hd = holdout["results"].get("yingqi_discrimination") or {}
        blind["holdout"] = {"avg": hs["avg"], "n": hs["n"], "dims": hs.get("dims"),
                            "scores": [r.get("pct") for r in hs["rows"] if "dims" in r],
                            "ids": [r.get("id") for r in hs["rows"] if "dims" in r],
                            "yingqi_top1": hd.get("top1_hit_rate"),
                            "yingqi_rank": hd.get("avg_rank_of_correct")}
    blind["scores"] = blind["tune"]["scores"]
    blind["avg"] = blind["headline"]
    blind["history"] = [
        {"label": "M0 真基线(tune)", "avg": 97.1},
        {"label": "M2.2 应期择优(tune)", "avg": strict["avg"]},
    ]
    return blind


def build_samples() -> list[dict]:
    from liuyao_engine import build_hexagram_result
    from thinking_chain import run_thinking_chain
    from human_narrative import build_human_narrative
    from visualization import build_html_report
    from advice_framework import generate_advice
    import case_runner as cr

    cases = {c["id"]: c for c in json.loads(
        (ROOT / "data" / "cases" / "classical_cases.json").read_text(encoding="utf-8"))["cases"]}
    OUT_REPORTS.mkdir(parents=True, exist_ok=True)
    samples = []
    for cid in SHOWCASE:
        case = cases.get(cid)
        if not case:
            print(f"  跳过 {cid}（案例库中不存在）")
            continue
        try:
            resolved = cr.resolve_case_time(case)
            dt = resolved["dt"]
            yao = cr.hex2yao(case["hexagram"]["original"], case["hexagram"].get("changed"))
            h = build_hexagram_result(yao, case["question"], "manual",
                                      dt.year, dt.month, dt.day, dt.hour)
        except Exception as exc:
            print(f"  跳过 {cid}：{exc}")
            continue
        tc = run_thinking_chain(h)
        thinking = tc.get("thinking_chain", tc)
        human = build_human_narrative(tc)
        tc["human_narrative"] = human
        try:
            tc["section_advice"] = generate_advice(
                (thinking.get("step5_synthesis") or {}).get("verdict", ""),
                case["question"], tc)
        except Exception as exc:                      # 建议层缺项不应阻断交付物生成
            print(f"  {cid} 建议生成跳过：{exc}")
        out_html = OUT_REPORTS / f"report_{cid}.html"
        out_html.write_text(build_html_report(tc), encoding="utf-8")

        s5 = thinking.get("step5_synthesis") or {}
        timing = s5.get("timing") or {}
        samples.append({
            "id": cid,
            "question": case["question"],
            "hexagram": tc["original_hexagram"]["name"],
            "changed": (tc.get("changed_hexagram") or {}).get("name"),
            "palace": tc["original_hexagram"].get("palace"),
            "generation": tc["original_hexagram"].get("generation"),
            "time": {**tc.get("divination_time", {}),
                     "assembled": dt.strftime("%Y-%m-%d %H:%M"),
                     "source": resolved["source"], "notes": resolved["notes"]},
            "empty": tc.get("empty_branches", []),
            "use_god": human.get("use_god"),
            "verdict": s5.get("verdict"),
            "final_score": s5.get("final_score"),
            "confidence": s5.get("confidence"),
            "yingqi": timing.get("summary_text"),
            "yingqi_branches": timing.get("key_branches") or [],
            "yingqi_rules": timing.get("timing_rules") or [],
            "pattern_tags": thinking.get("reasoning_chain", []),
            "human": human,
            "reasoning_chain": thinking.get("reasoning_chain", []),
            "yao_lines": tc["original_hexagram"]["yao_lines"],
            # 变卦逐爻数据：门户卦盘要画"某爻动、变出什么支"，只给卦名画不出来
            "changed_yao_lines": (tc.get("changed_hexagram") or {}).get("yao_lines") or [],
            "advanced": {k: v for k, v in (tc.get("advanced_analysis") or {}).items()
                         if k in ("monthly_break", "hidden_movement", "triple_combo",
                                  "advance_retreat", "clash_harmony")},
            "expected": case.get("expected", {}),
            "html_file": str(out_html.relative_to(ROOT)),
        })
        print(f"  {cid} → {out_html.name}  verdict={s5.get('verdict')}")
    return samples


def embed_into_index(payload: dict) -> None:
    index = ROOT / "index.html"
    text = index.read_text(encoding="utf-8")
    blob = json.dumps(payload, ensure_ascii=False, indent=2)
    blob = blob.replace("</", "<\\/")            # 防止提前闭合 <script>
    pattern = re.compile(r'(<script id="portal-data" type="application/json">).*?('
                         r'</script>)', re.S)
    if not pattern.search(text):
        print("× index.html 里找不到 portal-data 块，未内嵌")
        return
    index.write_text(pattern.sub(lambda m: m.group(1) + "\n" + blob + "\n" + m.group(2),
                                 text, count=1), encoding="utf-8")
    print("已内嵌 portal-data → index.html")


def main() -> int:
    from yishu_core.runtime import force_utf8_stdio
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="重建门户与样例报告")
    ap.add_argument("--run-eval", action="store_true", help="先跑 tune/holdout 评测")
    args = ap.parse_args()

    if args.run_eval:
        for split in ("tune", "holdout"):
            subprocess.run([sys.executable, str(ROOT / "scripts" / "evaluate.py"),
                            "--split", split, "--save"], cwd=str(ROOT), check=False)

    from yishu_core import __version__
    payload = {
        "project": "易 · 六爻纳甲断卦系统",
        "version": __version__,
        "blind": build_blind(),
        "samples": build_samples(),
        "pipeline": [
            {"step": "01", "title": "收集信息", "desc": "问题、起卦方式、时间"},
            {"step": "02", "title": "引擎排盘", "desc": "liuyao_engine.py 纳甲装卦，禁止手排"},
            {"step": "03", "title": "五步思维链", "desc": "观局→定用→断旺→察变→综合"},
            {"step": "04", "title": "应期择优", "desc": "按用神状态取主/次应期，附法则"},
            {"step": "05", "title": "正文解读", "desc": "human_narrative 唯一正文，不做两张皮"},
            {"step": "06", "title": "交付", "desc": "单文件 HTML 报告 + 本门户"},
        ],
    }
    out = ROOT / "assets" / "portal_data.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("portal data →", out)
    embed_into_index(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
