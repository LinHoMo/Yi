# -*- coding: utf-8 -*-
"""报告忠实度审计（tools/report_faithfulness.py）——「报告文本 vs 引擎结构化输出」。

设计思想参照调研入库的 HorosaBench（docs/RESEARCH-HOROSA.md §二.3）：
不用 LLM 自评，用**确定性校验器**把报告正文里的关键断言逐条分类为：
  - supported     ：文本断言与引擎结构化输出一致
  - invented      ：文本讲了、结构化输出里没有依据（凭空/模板过度发挥）
  - contradicted  ：文本断言与结构化输出直接矛盾

意义：铁律一（机械运算归代码）在报告层的延伸——叙事模板或后续 LLM 改写
若在报告里写出了引擎没有算出的结论，审计会当场点名，而不是等用户发现。

首版覆盖六爻（narrate 正文 ↔ thinking_chain/advanced_analysis/盘面字段）。
断言抽取与对照**全部是确定性规则**，不引入任何模型判断。

用法：
    python tools/report_faithfulness.py analyze.json          # 审已有 analyze JSON
    python tools/report_faithfulness.py --chart chart.json    # 从 chart 起跑 chart→analyze→narrate→审计
    python tools/report_faithfulness.py --demo                # 跑内置演示案例
退出码：断言全 supported（或空断言集）→ 0；出现 invented/contradicted → 1；错误 → 2。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIUYAO_SCRIPTS = ROOT / "disciplines" / "liuyao" / "scripts"
if str(LIUYAO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(LIUYAO_SCRIPTS))

# ── 词表 ────────────────────────────────────────────────────────────────────
SIX_RELATIONS = ("父母", "兄弟", "妻财", "官鬼", "子孙")
SIX_SPIRITS = ("青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武")
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
POS_NAMES = {"初": 1, "二": 2, "三": 3, "四": 4, "五": 5, "上": 6}
STRENGTH_WORDS = ("旺", "相", "休", "囚", "死")


# ── 结构化真值提取 ──────────────────────────────────────────────────────────

def extract_structure(analyze_json: dict) -> dict:
    """从 analyze JSON 提取「引擎算出的真值」，供断言对照。"""
    oh = analyze_json.get("original_hexagram") or {}
    yao_lines = oh.get("yao_lines") or []
    chain = analyze_json.get("thinking_chain") or {}
    step5 = chain.get("step5_synthesis") or {}
    step2 = chain.get("step2_use_god_identification") or {}
    sel = step2.get("selected_use_god") or {}
    adv = analyze_json.get("advanced_analysis") or {}
    summary = analyze_json.get("chart_summary") or {}

    world_yao = next((y for y in yao_lines if y.get("is_world")), None)
    use_yao = next((y for y in yao_lines if y.get("position") == sel.get("position")), None)

    # 格局：reasoning_chain 里的 [格局 xxx] 标签 + hexagram 级结构
    pattern_tags = [t for t in (chain.get("reasoning_chain") or [])
                    if isinstance(t, str) and t.startswith("[格局")]
    hex_cat = (adv.get("clash_harmony") or {}).get("hexagram_type") or ""
    triple = adv.get("triple_combo") or {}

    # 用神爻月令旺衰（旺相休囚死，五档）："得令/失令/用神X"断言的对照维度
    use_pos = sel.get("position")
    use_month_strength = ""
    for d in (adv.get("element_strength") or {}).get("details") or []:
        if d.get("position") == use_pos:
            use_month_strength = d.get("month_strength") or ""
            break

    return {
        "卦名": oh.get("name"),
        "变卦": (analyze_json.get("changed_hexagram") or {}).get("name"),
        "用神六亲": summary.get("用神") or sel.get("category") or step2.get("use_god_category") or "",
        "用神支": sel.get("earthly_branch") or "",
        "用神爻位": sel.get("position"),
        "用神六神": (use_yao or {}).get("six_spirit") or "",
        "世爻六亲": (world_yao or {}).get("six_relation") or "",
        "世爻支": (world_yao or {}).get("earthly_branch") or "",
        "旬空": set(analyze_json.get("empty_branches") or []),
        "月破": set((adv.get("monthly_break") or {}).get("branches") or [])
        if isinstance((adv.get("monthly_break") or {}).get("branches"), list) else set(),
        "卦身爻位": set((adv.get("hexagram_body") or {}).get("body_positions") or []),
        "卦身支": (adv.get("hexagram_body") or {}).get("body_branch") or "",
        "卦身六亲": (adv.get("hexagram_body") or {}).get("body_relation") or "",
        "卦身不现": bool((adv.get("hexagram_body") or {}).get("body_not_present")),
        "旺衰": step5.get("strength_level") or "",
        "用神月令旺衰": use_month_strength,
        "格局标签": pattern_tags,
        "卦级类别": hex_cat,
        "三合": bool(triple.get("has_triple_combo")),
        "动爻位": [y.get("position") for y in yao_lines if y.get("is_moving")],
    }


# ── 文本断言抽取（确定性正则） ──────────────────────────────────────────────

def _strip_quotes(text: str) -> str:
    """剥掉引文块，避免把古籍原文引用误当成本卦断言。

    排除三类引用：①「古歌诀有云：…」起至行尾；②「古人类似情境也说过」起的
    整段；③行内「（《…》…）」括号引用；④成对单引号/双引号包裹的古文引用。
    """
    lines = text.split("\n")
    out, in_quotes = [], False
    for ln in lines:
        s = ln.strip()
        if "古人类似情境" in s:
            in_quotes = True
        if in_quotes:
            continue
        if "古歌诀有云" in s:
            s = s.split("古歌诀有云")[0]
        s = re.sub(r"（《[^》]*》[^）]*）", "", s)
        s = re.sub(r"['\"「」『』]([^'\"「」『』]{4,})['\"「」『』]", "", s)
        out.append(s)
    return "\n".join(out)


def extract_assertions(text: str) -> list[dict]:
    """从报告正文抽断言（先剥引文）。每条：{kind, raw, value}。"""
    text = _strip_quotes(text)
    out = []
    six = "|".join(SIX_RELATIONS)
    spirits = "|".join(SIX_SPIRITS)
    # 用神：明确指向"关键看X"为用
    for m in re.finditer(r"关键看(%s)" % six, text):
        out.append({"kind": "用神", "raw": m.group(0), "value": m.group(1)})
    # 六亲持世
    for m in re.finditer(r"(%s)持世" % six, text):
        out.append({"kind": "持世", "raw": m.group(0), "value": m.group(1)})
    # 卦身（不现 / 在X爻）
    for m in re.finditer(r"卦身([%s])不现" % BRANCHES, text):
        out.append({"kind": "卦身不现", "raw": m.group(0), "value": m.group(1)})
    if "卦身不现" in text and not any(a["kind"] == "卦身不现" for a in out):
        out.append({"kind": "卦身不现", "raw": "卦身不现", "value": None})
    for m in re.finditer(r"卦身在([%s])爻（?((?:%s))?）?" % ("".join(POS_NAMES), six),
                         text):
        out.append({"kind": "卦身", "raw": m.group(0),
                    "value": {"pos": POS_NAMES.get(m.group(1)), "relation": m.group(2) or ""}})
    # 旬空
    for m in re.finditer(r"旬空([%s、]+)" % BRANCHES, text):
        branches = [b for b in m.group(1) if b in BRANCHES]
        out.append({"kind": "旬空", "raw": m.group(0), "value": set(branches)})
    # 六神临用
    for m in re.finditer(r"(%s)临用" % spirits, text):
        out.append({"kind": "六神临用", "raw": m.group(0), "value": m.group(1)})
    # 卦级类别：六冲/六合
    if "六冲卦" in text or re.search(r"遇六冲", text):
        out.append({"kind": "卦级", "raw": "六冲", "value": "六冲"})
    if "六合卦" in text or re.search(r"遇六合", text):
        out.append({"kind": "卦级", "raw": "六合", "value": "六合"})
    # 三合局
    if re.search(r"三合", text):
        out.append({"kind": "三合", "raw": "三合", "value": True})
    # 用神旺衰：优先"失令/得令"，再单字旺相休囚死（避开"旺衰"词组）
    m = re.search(r"用神[（(]?失令|用神[（(]?得令", text)
    if m:
        raw = m.group(0)
        out.append({"kind": "旺衰", "raw": raw, "value": "失令" if "失令" in raw else "得令"})
    else:
        m = re.search(r"用神(?![旺衰])[%s]" % "".join(STRENGTH_WORDS), text)
        if m:
            out.append({"kind": "旺衰", "raw": m.group(0), "value": m.group(0)[-1]})
    return out


# ── 分类 ────────────────────────────────────────────────────────────────────

def classify(assertion: dict, st: dict) -> str:
    """返回 supported / invented / contradicted。"""
    kind, value = assertion["kind"], assertion["value"]
    if kind == "用神":
        return "supported" if value == st["用神六亲"] else "contradicted"
    if kind == "持世":
        return "supported" if value == st["世爻六亲"] else "contradicted"
    if kind == "卦身":
        return ("supported" if value["pos"] in st["卦身爻位"] else "contradicted")
    if kind == "卦身不现":
        return "supported" if st["卦身不现"] and value == st["卦身支"] else "contradicted"
    if kind == "旬空":
        missing = value - st["旬空"]
        return "supported" if not missing else "contradicted"
    if kind == "六神临用":
        return "supported" if value == st["用神六神"] else "contradicted"
    if kind == "卦级":
        return "supported" if value in st["卦级类别"] else "contradicted"
    if kind == "三合":
        return "supported" if st["三合"] else "invented"
    if kind == "旺衰":
        # "得令/失令"与"旺相休囚死"均为月令旺衰语义，对照用神爻 month_strength
        ms = st["用神月令旺衰"]
        if value == "失令":
            return "supported" if ms in ("休", "囚", "死") else "contradicted"
        if value == "得令":
            return "supported" if ms in ("旺", "相") else "contradicted"
        return "supported" if value == ms else "contradicted"
    return "invented"


# ── 审计入口 ────────────────────────────────────────────────────────────────

def audit(analyze_json: dict, text: str) -> dict:
    st = extract_structure(analyze_json)
    assertions = extract_assertions(text)
    rows = []
    for a in assertions:
        verdict = classify(a, st)
        rows.append({
            "断言": a["raw"],
            "类别": a["kind"],
            "判定": verdict,
            "结构真值": _structure_hint(a["kind"], st),
        })
    summary = {"supported": 0, "invented": 0, "contradicted": 0}
    for r in rows:
        summary[r["判定"]] += 1
    return {"summary": summary, "rows": rows, "structure": st}


def _structure_hint(kind: str, st: dict) -> str:
    hints = {
        "用神": st["用神六亲"],
        "持世": st["世爻六亲"],
        "卦身": f"{sorted(st['卦身爻位'])}爻/{st['卦身支']}",
        "卦身不现": f"{st['卦身支']}({'不现' if st['卦身不现'] else '现'})",
        "旬空": "、".join(sorted(st["旬空"])) or "无",
        "六神临用": st["用神六神"],
        "卦级": st["卦级类别"],
        "三合": "有" if st["三合"] else "无",
        "旺衰": f"{st['旺衰']}/月令{st['用神月令旺衰']}",
    }
    return hints.get(kind, "")


def run_analyze(chart_json: dict) -> dict:
    from analyze import analyze
    return analyze(chart_json)


def run_narrate(analyze_json: dict) -> str:
    from narrate import narrate
    return narrate(analyze_json)


def _print_report(res: dict, text_len: int) -> None:
    s = res["summary"]
    print(f"报告正文 {text_len} 字｜断言 {sum(s.values())} 条")
    print(f"  supported      {s['supported']}")
    print(f"  invented       {s['invented']}")
    print(f"  contradicted   {s['contradicted']}")
    if res["rows"]:
        print("\n逐条（断言｜类别｜判定｜结构真值）：")
        for r in res["rows"]:
            mark = {"supported": "√", "invented": "! 凭空", "contradicted": "× 矛盾"}[r["判定"]]
            print(f"  {mark} {r['断言']}  [{r['类别']}]  结构={r['结构真值'] or '—'}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="报告忠实度审计：报告正文断言 vs 引擎结构化输出（supported/invented/contradicted）")
    ap.add_argument("analyze_json", nargs="?", help="六爻 analyze JSON 文件")
    ap.add_argument("--chart", type=Path, help="从 chart JSON 起跑 chart→analyze→narrate→审计")
    ap.add_argument("--demo", action="store_true", help="跑内置演示案例")
    ap.add_argument("--out", type=Path, help="写出审计明细 JSON")
    args = ap.parse_args()

    try:
        if args.analyze_json:
            data = json.loads(Path(args.analyze_json).read_text(encoding="utf-8"))
        elif args.chart:
            chart_data = json.loads(Path(args.chart).read_text(encoding="utf-8"))
            data = run_analyze(chart_data)
        elif args.demo:
            from chart import chart as _chart
            data = run_analyze(_chart("coin", "占求财", seed=42))
        else:
            ap.print_help()
            return 2
    except FileNotFoundError as exc:
        print(f"× 文件不存在：{exc.filename}")
        return 2
    except json.JSONDecodeError as exc:
        print(f"× JSON 解析失败：{exc}")
        return 2

    text = run_narrate(data)
    res = audit(data, text)
    _print_report(res, len(text))

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
        print("\n明细 →", args.out)

    bad = res["summary"]["invented"] + res["summary"]["contradicted"]
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
