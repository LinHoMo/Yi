# -*- coding: utf-8 -*-
"""评测维度 ↔ 报告面「同名同义」门（EVAL-PLAN §五 步 7 / §六）。

规则出处（docs/EVAL-PLAN.md §六）：narrate/render 新增任何维度时，
**评测维度与报告章节必须同名同义**，否则「算出来了但看不到」或「看到的没在评」，
两边都会慢慢失真。

为什么需要它（2026-10-10 首轮实跑）：`hidden_stems` 是**计分维度（权重 8）**、
引擎也确实算出来了（`factors[k].hidden_stems`），但样本报告里「藏干」**出现 0 次**——
这条 §六 的禁令一直没人守。写进散文的门等于没跑，故机械化如下：

    python dev_tools/check_dim_surface.py            # 校验
    python dev_tools/check_dim_surface.py --selftest # 负例：证明本门抓得住

口径（两侧都查，缺一即红）：
  · 引擎侧：`analyze` 必须真的产出该维度的结构（不是空值）；
  · 报告侧：`narrate` 正文必须含该维度的**专属标记串**（不是随便哪里出现过同名子串——
    「十神」在大运行文里也会出现，那不算十神维度有了落点）；
  · 反向：报告里每个 `**小节**` 必须被某个评测维度认领，或在
    `NON_SCORED_SECTIONS` 里点名登记「为什么只作旁证、不评分」。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DISC = Path(__file__).resolve().parents[1]
for p in (str(DISC / "scripts"), str(DISC / "core")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analyze as analyze_mod  # noqa: E402
import chart as chart_mod  # noqa: E402
import narrate as narrate_mod  # noqa: E402
import evaluate as ev  # noqa: E402

SAMPLE = ("1990-05-20 10:30", "男")

# dim → (引擎取值路径, 报告专属标记)
DIM_SURFACES = {
    "pillars":      (lambda a: len(a.get("pillars") or {}) >= 4, "四柱："),
    "ten_gods":     (lambda a: all((a.get("pillars") or {}).get(k, {}).get("ten_god")
                                    for k in ("year", "month", "day", "hour")),
                     "四柱十神"),
    "hidden_stems": (lambda a: all((a.get("factors") or {}).get(k, {}).get("hidden_stems")
                                    for k in ("year", "month", "day", "hour")),
                     "四柱藏干"),
    "tiaohou":      (lambda a: bool((a.get("tiaohou") or {}).get("main")), "调候"),
    "pattern":      (lambda a: bool((a.get("strength") or {}).get("pattern")), "格局"),
    "cong_ge":      (lambda a: "from_kind" in (a.get("strength") or {}), "从格"),
    "shensha":      (lambda a: isinstance(a.get("shensha"), list), "神煞"),
    "dayun":        (lambda a: len(a.get("dayun") or []) >= 4, "大运"),
}

# 报告小节 → 不评分的登记理由（§六 要求「看到的没在评」必须说明，不许沉默）
NON_SCORED_SECTIONS = {
    "强弱": "扶抑喜用的前置量，其可评部分落在 pattern/cong_ge 判据里",
    "喜用": "定义式推论（身旺喜克泄耗），无古籍逐例标答可比",
    "空亡": "历法定义式，已由 dev_tools/regression.py 机械回归守住",
    "女命夫子星": "六亲克应属 §二.2 不可评（无客观标的），只作机械标注",
    "大运×流年对照": "具体吉凶年份不可评（§二.2）；此处只出机械关系",
    "行运引动": "运对本命四柱的结构标签（第一百零八批 #31②），书例可回验但**尚无标答语料**："
               "主评分语料 670 例的 expected 里行运键为 0（第一百零七批实测），"
               "一经记分就变成拿未验证机制去凑分；dayun 维度仍只按 顺逆 8＋起运 4 计分",
    "四柱结构与组合": "胎元/身宫等为定义式结构量，暂无古籍逐例标答",
    "十神取象": "《千里命稿》引文旁证，非判据、不进评分",
    "纳音取象": "纳音法与子平日主法并行不混用，物性标签旁证，不计格不评分",
    "四柱干支关系": "机械关系标签，吉凶由格局层定，不重复计分",
    "通关／关隔": "病药/通关体系未建评测基准（见 _uncovered），只出结构",
    "病药": "《神峰通考》病药说与 engine 月令口径方向相反，见 _uncovered 登记",
    # 以下 5 节为首轮实跑被本门抓出「看到了没在评也没登记」的小节，逐条补理由：
    "日主体性": "性情描述属 §二.2 不可评（无法离散化比对），只作定性注记",
    "格局所本": "书源引文与出处（provenance），其可评部分已落在 pattern 维度里",
    "流年前六年": "具体吉凶年份属 §二.2 不可评；此处只出机械干支与十神推算",
    "流月": "月级干支为历法推算，无古籍逐例标答；不并入 dayun 维度记分",
    "小运": "小运起例各家不同（流派差异），未定口径前不建标答，只出机械值",
}

HEAD = re.compile(r"^\*\*(.+?)\*\*")


def surfaces(a: dict, text: str) -> list[str]:
    problems: list[str] = []
    for dim in ev.WEIGHTS:
        probe = DIM_SURFACES.get(dim)
        if probe is None:
            problems.append(f"维度 {dim} 未登记「引擎取值 + 报告标记」映射（新增维度必须两侧同时落）")
            continue
        getter, marker = probe
        try:
            has_engine = bool(getter(a))
        except Exception as exc:
            has_engine = False
            problems.append(f"维度 {dim} 引擎取值探针异常：{type(exc).__name__}: {exc}")
        if not has_engine:
            problems.append(f"维度 {dim}（权重 {ev.WEIGHTS[dim]}）引擎未产出可评结构 → 评测该维恒 N/A")
        if marker not in text:
            problems.append(f"维度 {dim} 已计分，但报告正文无专属标记「{marker}」→ 算出来了看不到")
    for line in text.splitlines():
        m = HEAD.match(line.strip())
        if not m:
            continue
        sec = m.group(1).split("（")[0].strip()
        if any(sec.startswith(k.split("（")[0]) for k in NON_SCORED_SECTIONS):
            continue
        # 认领方向：小节标题**含**某维度的专属标记，才算被该维度认领
        # （写成反向会把「四柱十神与四柱藏干」这种真落点评成无人认领）
        if any(marker and marker in sec for _, (_, marker) in DIM_SURFACES.items()):
            continue
        problems.append(f"报告小节「{sec}」既不被任何评测维度认领，也未登记不评分的理由"
                        f"（§六：看到的没在评必须说明）")
    return problems


def selftest(a: dict, text: str) -> list[str]:
    """负例：抹掉一个标记 / 造一个无名小节，本门必须分别抓到两侧。"""
    problems: list[str] = []
    if "四柱藏干" in text:
        if "四柱藏干" in surfaces(a, text.replace("四柱藏干", "××"))and "算出来了看不到" not in "".join(
                surfaces(a, text.replace("四柱藏干", "××"))):
            problems.append("负例失效：抹掉报告标记没被抓到")
    elif "藏干" not in text:
        # 当前报告本来就缺该标记，正门已判红；负例改用别的维度验证机制有效
        probe_text = text.replace("神煞", "××", 1)
        if "神煞" in text and not any("shensha" in x for x in surfaces(a, probe_text)):
            problems.append("负例失效：抹掉「神煞」标记没被抓到")
    fake = text + "\n**凭空多出来的一节**：测试。\n"
    if not any("凭空多出来的一节" in x for x in surfaces(a, fake)):
        problems.append("负例失效：新增未认领小节没被抓到（反向半边是空的）")
    return problems


def main() -> int:
    ch = chart_mod.chart(datetime_str=SAMPLE[0], gender=SAMPLE[1])
    a = dict(analyze_mod.analyze(ch))
    text = narrate_mod.narrate(a)
    problems = surfaces(a, text)
    print(f"评测维度 {len(ev.WEIGHTS)} 个 / 报告 {len(text.splitlines())} 行 → "
          f"两侧不一致 {len(problems)} 处")
    if "--selftest" in sys.argv:
        sp = selftest(a, text)
        for x in sp:
            print(f"  × {x}")
        print(f"  [selftest] 负例{'全部抓到' if not sp else '失效'}")
        if sp:
            return 1
    for x in problems:
        print(f"  × {x}")
    if not problems:
        print("  √ 每个计分维度都有引擎结构 + 报告专属落点；每个报告小节都被认领或登记了不评分理由")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
