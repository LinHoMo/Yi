# -*- coding: utf-8 -*-
"""断语外置审计（重建 `tools/verdict_audit.py` 的等价物，2026-10-11 第三十八批）。

为什么查的是**渲染出来的报告**而不是源码字面量：
约定是「`scripts/narrate.py` 的断语必须外置到 `data/verdicts.json`」（`docs/CHANGELOG.md`
第三批登记、第五批结转，历史上由 `tools/verdict_audit.py` 机械守，该器随扁平化删除后**未重建**）。
在源码上做静态匹配必然假阳性——同一个「旺」「逆」在代码里既可能是判词、也可能是
字典键名、十二运名、格局顺逆的枚举值；门一旦假阳性，人就学会把它拆掉或把词改写到
别处去躲。改成查**产物**：报告里真出现的判断措辞，必须能在 `data/*.json` 里找到出处，
找不到就是内联在代码里的断语——这正是约定要拦的东西。

    python dev_tools/verdict_audit.py            # 渲染若干命盘并取证
    python dev_tools/verdict_audit.py --verbose  # 连报告原文一起打
    python dev_tools/verdict_audit.py --selftest # 负例：内联断语必须被抓、合法措辞不得误抓

判定口径（SKILL.md 铁律一：代码不算命、只算结构；措辞一律外置）：
  · 报告行里的判断措辞，其出处在 `data/*.json`（含 verdicts/tiaohou_quotes/nayin_quxiang/
    shi_shen_actions/ditian_sui/liushen_image）任一处 → 合规
  · 引文括注（`「…」` 与 `（《…》…）`）内不取证——那是底本原文，不是本科断语
  · 一条都没检视到 → 本器自报失败，绝不当通过
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DISC = Path(__file__).resolve().parents[1]
DATA = DISC / "data"
SCRATCH = DISC / "scratch"

# 判断措辞（闭表）。只收"给出吉凶贵贱层次"的词，不收结构术语
# （旺/衰/刑/冲/克/合 是状态与关系名，属引擎输出词表，见 core/symbols.py）。
VERDICT_WORDS = [
    "大吉", "大凶", "主吉", "主凶", "吉兆", "凶兆", "不吉", "吉利", "凶险",
    "富贵", "贫贱", "贫寒", "显达", "落魄", "清高", "福禄", "灾祸", "祸患",
    "忧患", "寿元", "夭折", "短寿", "长寿", "贵格", "贫命", "顺遂", "逆境",
    "欠佳", "平平", "亨通", "萧条", "荣达", "孤克", "刑克", "破家", "败业",
]

# 底本引文与出处括注：其中字样不作取证（是古籍原文，不是本科措辞）
CITATION = re.compile(r"「[^」]*」|（《[^）]*）|\([^)]*\)|《[^》]*》")


def load_corpus_words() -> str:
    """`data/*.json` 里全部字符串值拼成一块"允许措辞"的语料。"""
    buf = []
    for p in sorted(DATA.glob("*.json")):
        try:
            buf.append(json.dumps(json.loads(p.read_text(encoding="utf-8")), ensure_ascii=False))
        except Exception as exc:  # 数据坏了要让门显式失败，不能静默当空集
            buf.append(f"!BROKEN!{p.name}:{type(exc).__name__}")
    return "".join(buf)


def _clean(line: str) -> str:
    return CITATION.sub("", line)


def audit_line(line: str, corpus: str) -> list[str]:
    """返回本行里"无外置出处"的判断措辞（空 = 合规）。"""
    hits = []
    txt = _clean(line)
    for w in VERDICT_WORDS:
        if w in txt and w not in corpus:
            hits.append(w)
    return hits


def render_samples() -> list[tuple[str, str]]:
    """跑三个真命盘，返回 (标签, narrate 报告全文)。"""
    charts = [("坤造·1990-05-20 10:30", "女"), ("乾造·1986-08-03 07:15", "男"),
              ("乾造·2001-12-21 23:40", "男")]
    out = []
    SCRATCH.mkdir(exist_ok=True)
    for i, (label, gender) in enumerate(charts):
        when = label.split("·")[1]
        cp = SCRATCH / f"verdict_audit_chart_{i}.json"
        ap = SCRATCH / f"verdict_audit_analyze_{i}.json"
        steps = [["scripts/chart.py", "--datetime", when, "--gender", gender, "-o", str(cp)],
                 ["scripts/analyze.py", str(cp), "-o", str(ap)],
                 ["scripts/narrate.py", str(ap)]]
        text = ""
        for s in steps:
            r = subprocess.run([sys.executable, *s], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", cwd=str(DISC), timeout=180)
            if r.returncode != 0:
                raise RuntimeError(f"{s[1] if len(s)>1 else s[0]} 跑不通：{r.stderr[:200]}")
            text = r.stdout
        out.append((label, text))
    for p in (SCRATCH / f"verdict_audit_chart_{i}.json" for i in range(len(charts))):
        p.unlink(missing_ok=True)
    for p in (SCRATCH / f"verdict_audit_analyze_{i}.json" for i in range(len(charts))):
        p.unlink(missing_ok=True)
    return out


def selftest(corpus: str, problems: list[str]) -> int:
    """两件事都要成立：内联断语必须被抓（有牙齿），合法措辞不得被抓（不假阳性）。"""
    bad = "此命富贵双全，兼主大吉，兼论寿元。"
    good_line = "格局：正官格，顺用。"
    probe_corpus = ""  # 空语料下三个词都应被抓到
    caught = set(audit_line(bad, probe_corpus))
    if not {"富贵", "大吉"} <= caught:
        problems.append(f"负例自证失效：内联断语没被抓到 → {caught}")
    if audit_line(good_line, probe_corpus):
        problems.append(f"负例自证假阳性：结构术语行被判成断语 → {good_line}")
    if audit_line("《子平真诠》云「用神既清，富贵可用」（论用神）。", probe_corpus):
        problems.append("负例自证假阳性：底本引文括注里的字样应当豁免，不该算本科断语")
    return len(caught)


def main() -> int:
    ap = argparse.ArgumentParser(description="八字科断语外置审计")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    problems: list[str] = []
    corpus = load_corpus_words()
    if "!BROKEN!" in corpus:
        problems.append(f"data/*.json 有解析失败，措辞语料不可信：{[x for x in re.findall(r'!BROKEN![^!]*', corpus)]}")

    checked = 0
    for label, text in render_samples():
        for ln in text.splitlines():
            hits = audit_line(ln, corpus)
            if hits:
                problems.append(f"{label}：报告出现无外置出处的判断措辞 {'、'.join(hits)} → {ln.strip()[:80]}")
            if _clean(ln).strip():
                checked += 1
        if args.verbose:
            print(f"---- {label}\n{text}")

    n_probe = 0
    if args.selftest:
        n_probe = selftest(corpus, problems)
        print(f"  [selftest] 负例已跑（内联断语样本抓到 {n_probe} 个词）")

    print(f"合计：检视报告行 {checked} 行，判断措辞词表 {len(VERDICT_WORDS)} 个，"
          f"外置语料 {len(corpus)} 字，{len(problems)} 条违规")
    if checked == 0:
        print("× 0 行被检视——本器等于没跑，不判通过")
        return 1
    if n_probe == 0:
        print("× 自检负例一个词都没抓到，本器不足以当门")
        return 1
    for p in problems:
        print(f"  × {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
