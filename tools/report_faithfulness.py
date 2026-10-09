# -*- coding: utf-8 -*-
"""报告忠实度审计（tools/report_faithfulness.py）——「报告文本 vs 引擎结构化输出」。

设计思想参照调研入库的 HorosaBench（docs/RESEARCH-HOROSA.md §二.3）：
不用 LLM 自评，用**确定性校验器**把报告正文里的关键断言逐条分类为：
  - supported     ：文本断言与引擎结构化输出一致
  - invented      ：文本讲了、结构化输出里没有依据（凭空/模板过度发挥）
  - contradicted  ：文本断言与结构化输出直接矛盾
  - unknown       ：该断言处在**否定语境**（「并无三合局」「不是六冲卦」）——引擎没有
                    算出"否定"这个结论，所以既不能记 supported 也不能记 contradicted；
                    旧实现看不见否定词，把「此处并无三合局」抽成 `三合 value=True`，
                    引擎若真有三合就判 supported（把否定句当成肯定句背书）。

意义：铁律一（机械运算归代码）在报告层的延伸——叙事模板或后续 LLM 改写
若在报告里写出了引擎没有算出的结论，审计会当场点名，而不是等用户发现。

首版覆盖六爻（narrate 正文 ↔ thinking_chain/advanced_analysis/盘面字段）。
断言抽取与对照**全部是确定性规则**，不引入任何模型判断。

用法：
    python tools/report_faithfulness.py analyze.json          # 审已有 analyze JSON
    python tools/report_faithfulness.py --chart chart.json    # 从 chart 起跑 chart→analyze→narrate→审计
    python tools/report_faithfulness.py --demo                # 跑内置演示案例（1 例）
    python tools/report_faithfulness.py --corpus              # 跑内置语料（三种起卦法，例数见输出）
    python tools/report_faithfulness.py --selftest            # 抽取器负例自证（AGENTS.md §四.8）
退出码：断言全 supported/unknown（或空断言集）→ 0；出现 invented/contradicted → 1；错误 → 2。
`--selftest` 判据：负例必须**被抓**、正例必须**不误报**，任一不成立退出 1 并逐条列明细；
通过时报出口令 `SELFTEST PASS：正例 N 例 + 负例 M 例`（tools/check.py [2b] 断言该口令，
退出码 0 不算通过——§四.8 的"空壳自测"同此防）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))
LIUYAO_SCRIPTS = ROOT / "disciplines" / "liuyao" / "scripts"
if str(LIUYAO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(LIUYAO_SCRIPTS))

from yishu_core.relations import LIUQIN_NAMES  # noqa: E402
from yishu_core.symbols import EARTHLY_BRANCHES  # noqa: E402

# ── 词表 ────────────────────────────────────────────────────────────────────
# 六亲名与地支序均为内核唯一真值源的派生视图（AGENTS.md §二），此处不另存副本。
SIX_RELATIONS = tuple(LIUQIN_NAMES)
SIX_SPIRITS = ("青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武")
BRANCHES = "".join(EARTHLY_BRANCHES)
POS_NAMES = {"初": 1, "二": 2, "三": 3, "四": 4, "五": 5, "上": 6}
STRENGTH_WORDS = ("旺", "相", "休", "囚", "死")

# 内置审计语料（架构评审 A10：忠实度门原只跑单例 --demo，证明不了「换一种起卦法、
# 换一类问事」时叙述模板仍不越界）。全部为**合成请求**，不取自 data/cases/（铁律二）。
CORPUS_CASES: tuple[tuple[str, str, dict], ...] = (
    ("coin", "占求财", {"seed": 42}),
    ("coin", "占病", {"seed": 7}),
    ("coin", "占考试", {"seed": 11}),
    ("coin", "占婚姻", {"seed": 23}),
    ("coin", "占出行", {"seed": 101}),
    ("time", "占求财", {"datetime_str": "2026-03-05 09:30"}),
    ("time", "占官司", {"datetime_str": "2026-07-18 15:10"}),
    ("time", "占失物", {"datetime_str": "2026-01-09 21:40"}),
    ("time", "占天气", {"datetime_str": "2026-05-02 06:20"}),
    ("number", "占求财", {"numbers": "3,8,5"}),
    ("number", "占病", {"numbers": "5,2,9"}),
    ("number", "占行人", {"numbers": "7,4,6"}),
)


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

    排除四类引用：①「古歌诀有云：…」起至行尾；②「古人类似情境也说过」起的
    整段；③行内「（《…》…）」括号引用；④成对 ASCII/弯引号包裹的古文长引用。

    两处缺陷修复（2026-10-09，负例见 `--selftest`）：
      · **②必须复位**。旧实现只有 `in_quotes = True`、全函数没有任何 `= False`，
        于是正文一旦出现「古人类似情境」，其后所有行**永久**退出审计
        （实测 3 行进 → 1 行出），而 `extract_assertions` 也走本函数，污染是全链的
        ——报告后半页的真断言从此不再被审。现以空行或下一个标题（`#`）收束复位。
      · **④不得吃掉术语强调**。旧实现把 `['\"「」『』]…['\"「」『』]`（≥4 字）**整段删除**，
        于是 `「青龙临用」` 在抽取之前就被删掉了。CJK 角括号「」『』在本仓是
        **术语强调**（AGENTS.md §三 的中文强调约定），不是古籍句子；现只去掉括号
        本身、保留内容。ASCII/弯引号仍按整段删除（narrate 用它包古籍原句，
        如 `'用神休囚已極，雖得元神生扶不能起也'`）。
    """
    lines = text.split("\n")
    out, in_quotes = [], False
    for ln in lines:
        s = ln.strip()
        if in_quotes and (not s or s.startswith("#")):
            in_quotes = False           # 引文段以空行或下一个标题收束（缺陷复位）
        if "古人类似情境" in s:
            in_quotes = True
        if in_quotes:
            continue
        if "古歌诀有云" in s:
            s = s.split("古歌诀有云")[0]
        s = re.sub(r"（《[^》]*》[^）]*）", "", s)
        s = re.sub(r"['\"“”‘’]([^'\"“”‘’]{4,})['\"“”‘’]", "", s)
        s = re.sub(r"[「」『』]", "", s)
        out.append(s)
    return "\n".join(out)


# 关键词与取值之间可能插着句读或一个括号注：`旬空午未` / `旬空：午未` / `旬空（午未）`
# 都得抽出（旧实现只认裸写形态，加一个冒号即抽出 0 条 = 绕过审计）。
_SEP = r"\s*[：:，、]?\s*[（(]?\s*"
# 否定语境：小句内、关键词**之前**出现这些词，则该断言不能记 supported（也不能记
# contradicted——引擎压根没算"否定"这个结论）。只回看当前小句，越过句读不算。
_NEGATION = re.compile(r"无|没有|并非|非|未|不|难|岂|勿|别|缺|不见")
_CLAUSE_BREAK = "，。；：、！？\n"


def _negated_before(text: str, start: int, lookback: int = 8) -> bool:
    """关键词之前（同一小句内）是否有否定词。"""
    window = text[max(0, start - lookback):start]
    cut = max((window.rfind(c) for c in _CLAUSE_BREAK), default=-1)
    if cut >= 0:
        window = window[cut + 1:]
    return bool(_NEGATION.search(window))


def _add(out: list, src: str, m: re.Match, kind: str, value) -> None:
    """收一条断言；记录它是否处在否定语境里。"""
    out.append({"kind": kind, "raw": m.group(0), "value": value,
                "negated": _negated_before(src, m.start())})


def extract_assertions(text: str, *, strip_quotes: bool = True) -> list[dict]:
    """从报告正文抽断言（默认先剥引文）。每条：{kind, raw, value, negated}。"""
    src = _strip_quotes(text) if strip_quotes else text
    out = []
    six = "|".join(SIX_RELATIONS)
    spirits = "|".join(SIX_SPIRITS)
    # 用神：明确指向"关键看X"为用
    for m in re.finditer(r"关键看(%s)" % six, src):
        _add(out, src, m, "用神", m.group(1))
    # 六亲持世
    for m in re.finditer(r"(%s)%s持世" % (six, _SEP), src):
        _add(out, src, m, "持世", m.group(1))
    # 卦身（不现 / 在X爻）
    for m in re.finditer(r"卦身([%s])%s不现" % (BRANCHES, _SEP), src):
        _add(out, src, m, "卦身不现", m.group(1))
    if "卦身不现" in src and not any(a["kind"] == "卦身不现" for a in out):
        m = re.search("卦身不现", src)
        _add(out, src, m, "卦身不现", None)
    for m in re.finditer(r"卦身%s在([%s])爻?（?((?:%s))?）?"
                        % (_SEP, "".join(POS_NAMES), six), src):
        out.append({"kind": "卦身", "raw": m.group(0), "negated": _negated_before(src, m.start()),
                    "value": {"pos": POS_NAMES.get(m.group(1)), "relation": m.group(2) or ""}})
    for m in re.finditer(r"旬空%s([%s、]+)" % (_SEP, BRANCHES), src):
        branches = [b for b in m.group(1) if b in BRANCHES]
        _add(out, src, m, "旬空", set(branches))
    # 六神临用
    for m in re.finditer(r"(%s)%s临用" % (spirits, _SEP), src):
        _add(out, src, m, "六神临用", m.group(1))
    # 卦级类别：六冲/六合
    for pat, val in ((r"六冲卦|遇六冲", "六冲"), (r"六合卦|遇六合", "六合")):
        m = re.search(pat, src)
        if m:
            _add(out, src, m, "卦级", val)
    # 三合局：逐个出现处都看，只要有**一处不在否定语境**就当作肯定断言
    hits = list(re.finditer(r"三合", src))
    if hits:
        aff = next((m for m in hits if not _negated_before(src, m.start())), None)
        if aff is not None:
            _add(out, src, aff, "三合", True)
        else:
            # 全部处在否定语境（「此处并无三合局」）：如实收一条 unknown，
            # 绝不再记 supported（旧实现看不见否定词）。
            _add(out, src, hits[0], "三合", True)
            out[-1]["negated"] = True
    # 用神旺衰：优先"失令/得令"，再单字旺相休囚死（避开"旺衰"词组）
    m = re.search(r"用神%s[（(]?失令|用神%s[（(]?得令" % (_SEP, _SEP), src)
    if m:
        _add(out, src, m, "旺衰", "失令" if "失令" in m.group(0) else "得令")
    else:
        m = re.search(r"用神(?![旺衰])[%s]" % "".join(STRENGTH_WORDS), src)
        if m:
            _add(out, src, m, "旺衰", m.group(0)[-1])
    return out



# ── 分类 ────────────────────────────────────────────────────────────────────

_MARKS = {"supported": "√", "invented": "! 凭空", "contradicted": "× 矛盾",
          "unknown": "? 否定语境"}


def classify(assertion: dict, st: dict) -> str:
    """返回 supported / invented / contradicted / unknown。"""
    kind, value = assertion["kind"], assertion["value"]
    if assertion.get("negated"):
        # 「此处并无三合局」不是「有三合局」的肯定断言：引擎没有"否定"这一结论，
        # 记 supported 等于替否定句背书，记 contradicted 又是假阳——只报 unknown。
        return "unknown"
    if kind == "用神":
        return "supported" if value == st["用神六亲"] else "contradicted"
    if kind == "持世":
        return "supported" if value == st["世爻六亲"] else "contradicted"
    if kind == "卦身":
        return ("supported" if value["pos"] in st["卦身爻位"] else "contradicted")
    if kind == "卦身不现":
        if not st["卦身不现"]:
            return "contradicted"
        # 裸写「卦身不现」没有点支，只判布尔；点了支的形态仍逐字对照
        return "supported" if value is None or value == st["卦身支"] else "contradicted"
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
    summary = {"supported": 0, "invented": 0, "contradicted": 0, "unknown": 0}
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
    print(f"  unknown(否定)  {s['unknown']}")
    if res["rows"]:
        print("\n逐条（断言｜类别｜判定｜结构真值）：")
        for r in res["rows"]:
            mark = _MARKS[r["判定"]]
            print(f"  {mark} {r['断言']}  [{r['类别']}]  结构={r['结构真值'] or '—'}")


def run_corpus() -> dict:
    """跑内置语料（`CORPUS_CASES`）逐例审计并汇总（A10）。

    返回 {cases, 断言, supported, invented, contradicted, rows, fails}；
    `rows` 为逐例读数（起卦法/问事/断言数/三项判定），`fails` 只列有 invented|contradicted 的例。
    """
    from chart import chart as _chart

    agg = {"cases": 0, "断言": 0, "supported": 0, "invented": 0,
           "contradicted": 0, "unknown": 0, "rows": [], "fails": []}
    for mode, question, kw in CORPUS_CASES:
        label = f"{mode}/{question}" + (f" seed={kw['seed']}" if "seed" in kw else "")
        try:
            data = run_analyze(_chart(mode, question, **kw))
            text = run_narrate(data)
            res = audit(data, text)
        except Exception as exc:  # noqa: BLE001 —— 某例起不来即判败，但不掩盖其余各例
            agg["cases"] += 1
            agg["contradicted"] += 1
            agg["rows"].append({"case": label, "断言": 0, "supported": 0,
                                "invented": 0, "contradicted": 1, "unknown": 0,
                                "error": f"{type(exc).__name__}: {exc}"})
            agg["fails"].append({"case": label, "summary": {"contradicted": 1}, "rows": [],
                                 "error": f"{type(exc).__name__}: {exc}"})
            continue
        s = res["summary"]
        n = sum(s.values())
        agg["cases"] += 1
        agg["断言"] += n
        for k in ("supported", "invented", "contradicted", "unknown"):
            agg[k] += s[k]
        agg["rows"].append({"case": label, "断言": n, **s})
        if s["invented"] or s["contradicted"]:
            agg["fails"].append({"case": label, "summary": s,
                                 "rows": [r for r in res["rows"] if r["判定"] != "supported"]})
    return agg


def _print_corpus(agg: dict) -> None:
    for r in agg["rows"]:
        flag = "×" if (r["invented"] or r["contradicted"]) else "√"
        print(f"  {flag} {r['case']:<26s} 断言 {r['断言']:>3d}"
              f"｜supported {r['supported']}｜invented {r['invented']}"
              f"｜contradicted {r['contradicted']}｜unknown {r['unknown']}")
    print(f"\n语料 {agg['cases']} 例｜断言 {agg['断言']} 条 → supported {agg['supported']}"
          f"｜invented {agg['invented']}｜contradicted {agg['contradicted']}"
          f"｜unknown {agg['unknown']}")
    for f in agg["fails"]:
        print(f"\n× {f['case']} 的越界断言：")
        for r in f["rows"]:
            print(f"  {'! 凭空' if r['判定'] == 'invented' else '× 矛盾'} {r['断言']}"
                  f"  [{r['类别']}]  结构={r['结构真值'] or '—'}")


# ── 抽取器负例自证（AGENTS.md §四.8：新门先怀疑、再证明）────────────────────
#
# 为什么住在脚本里而不是 tests/：这三类绕过（引文段后永久免疫、标点变体、否定句）
# 都是**抽取器自身**的缺陷，只有抽最上游的 `_strip_quotes`/`extract_assertions`
# 才测得到；挂在 tests/ 里同样要 import 本模块，而 [2b] 要求子门**自己**报出口令。
# 探针不调用学科脚本（不起子进程、不落文件），因此与 --corpus 的引擎依赖解耦。

_ST_BASE: dict = {
    "卦名": "坤为地", "变卦": None, "用神六亲": "妻财", "用神支": "亥", "用神爻位": 5,
    "用神六神": "玄武", "世爻六亲": "子孙", "世爻支": "申", "旬空": {"子", "丑"},
    "月破": set(), "卦身爻位": {5}, "卦身支": "亥", "卦身六亲": "妻财",
    "卦身不现": False, "旺衰": "极弱", "用神月令旺衰": "休", "格局标签": [],
    "卦级类别": "六冲卦", "三合": False, "动爻位": [],
}


def _st(**over) -> dict:
    st = dict(_ST_BASE)
    st.update(over)
    return st


# 负例：给定正文与引擎结构，抽取器**必须**抓出越界断言（判定落在 expect 里），
# 且绝不能记成 supported。expect 为空集表示"至少要抓到一条非 supported"。
SELFTEST_NEG: tuple[tuple[str, str, dict, tuple[str, ...], str], ...] = (
    ("引文段之后的越界断言必须被检出",
     "古人类似情境也说过：\n- （《卜筮正宗·六神论》）青龙临用主喜庆。\n\n"
     "六神方面：本卦青龙临用。",
     _st(用神六神="玄武"), ("contradicted",),
     "旧实现没有 in_quotes 复位：这一段之后的正文永久不审，抽出 0 条"),
    ("冒号写法必须被检出",
     "旬空：寅卯。",
     _st(), ("contradicted",),
     "旧实现只认「旬空午未」裸写，加一个冒号即抽出 0 条"),
    ("括号注写法必须被检出",
     "旬空（寅卯）",
     _st(), ("contradicted",),
     "旧实现括号注挡在关键词与取值之间，抽取落空"),
    ("「」包裹的断言必须被检出",
     "「青龙临用」",
     _st(用神六神="玄武"), ("contradicted",),
     "旧实现的引号剥离在抽取前把整段内容删掉"),
    ("凭空断语不得被记为 supported",
     "卦逢三合局，三合局成。",
     _st(三合=False), ("invented",),
     "引擎没算出三合，正文却写成了肯定句"),
    ("否定语境不得被记为 supported",
     "此处并无三合局，不可作三合论。",
     _st(三合=True), ("unknown",),
     "旧实现看不见否定词：引擎有三合时把「并无三合局」背书成 supported"),
)

# 正例：干净正文不得误报（复位不等于把引文豁免也一起拆掉）
SELFTEST_POS: tuple[tuple[str, str, dict, int], ...] = (
    ("引文段内不抽（复位后仍豁免引文本身）",
     "古人类似情境也说过：\n- （《卜筮正宗》）青龙临用，妻财持世。\n\n"
     "以上为机械推演，医疗、法律请以专业意见为准。",
     _st(用神六神="玄武", 世爻六亲="子孙"), 0),
    ("与引擎一致的正文应全 supported",
     "关键看妻财，子孙持世，旬空：子、丑，玄武临用，此卦三合局成，用神失令。",
     _st(三合=True), 5),
)


def run_selftest() -> int:
    """负例必须被抓、正例必须不误报；任一不成立退出 1 并逐条列明细。"""
    bad: list[str] = []
    for name, text, st, expect, why in SELFTEST_NEG:
        assertions = extract_assertions(text)
        verdicts = [(a["kind"], classify(a, st)) for a in assertions]
        if not assertions:
            bad.append(f"负例「{name}」抽出 0 条断言（越界断言漏审）——{why}")
            continue
        got = {v for _, v in verdicts}
        if "supported" in got:
            bad.append(f"负例「{name}」被判 supported：{verdicts}——{why}")
        elif not (got & set(expect)):
            bad.append(f"负例「{name}」判定 {got} 不在期望 {set(expect)} 内：{verdicts}")
    for name, text, st, min_n in SELFTEST_POS:
        assertions = extract_assertions(text)
        verdicts = [(a["kind"], classify(a, st)) for a in assertions]
        wrong = [v for _, v in verdicts if v not in ("supported", "unknown")]
        if len(assertions) < min_n:
            bad.append(f"正例「{name}」只抽出 {len(assertions)} 条（应 ≥{min_n}）：{verdicts}")
        elif wrong:
            bad.append(f"正例「{name}」误报 {wrong}：{verdicts}")
    print(f"忠实度抽取器自证：负例 {len(SELFTEST_NEG)} 条、正例 {len(SELFTEST_POS)} 条")
    for name, *_ in SELFTEST_NEG:
        print(f"  · 负例 {name}")
    if bad:
        print("× 自证失败：")
        for b in bad:
            print("  -", b)
        return 1
    print(f"SELFTEST PASS（正例 {len(SELFTEST_POS)} 例 + 负例 {len(SELFTEST_NEG)} 例）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="报告忠实度审计：报告正文断言 vs 引擎结构化输出"
                    "（supported/invented/contradicted/unknown）")
    ap.add_argument("analyze_json", nargs="?", help="六爻 analyze JSON 文件")
    ap.add_argument("--chart", type=Path, help="从 chart JSON 起跑 chart→analyze→narrate→审计")
    ap.add_argument("--demo", action="store_true", help="跑内置演示案例（1 例）")
    ap.add_argument("--corpus", action="store_true",
                    help=f"跑内置语料（{len(CORPUS_CASES)} 例，coin/time/number 三种起卦法）")
    ap.add_argument("--selftest", action="store_true",
                    help="抽取器负例自证（引文段复位/标点变体/否定语境；不跑引擎）")
    ap.add_argument("--out", type=Path, help="写出审计明细 JSON")
    args = ap.parse_args()

    if args.selftest:
        return run_selftest()

    if args.corpus:
        agg = run_corpus()
        _print_corpus(agg)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(agg, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
            print("\n明细 →", args.out)
        return 1 if (agg["invented"] or agg["contradicted"]) else 0

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
