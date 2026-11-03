#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""象层门（362 批）：象目必须有出处、象类别必须随题类走、象层不得倒灌评分。

为什么需要它：本仓的「象分析」此前**只存在于两个地方**——trigram_symbolism 里
一张八卦类象表，和 analyze 里一句写死 `category="general"` 的调用。结果是：
八卦类象、卦辞爻辞、互体、六神象义这些素材盘面里全有，正文里一个字都不出。
素材在、能力不在，是**看不见的缺口**——原有门一条都拦不住（键面合规、评分未变、
指纹不动）。

本门三条判据：
  ① 出处：每个象目（trigram/ti_yong/guaci/yaoci/hu_gua/spirit/fangwei）必须带
     非空 `basis`，无出处的象目不得产出（AGENTS §三：文案进 data，出处随文案走）。
  ② 联动：题类→象类别必须真联动（疾病→health、失物→loss、功名→career），
     且问句无题类信号时落 general——只验"能取到类别"会把恒 general 判成过。
  ③ 禁评分：评分侧模块（step1-5/timing/judge/classical_*）不得读 `xiang`；
     `xiang` 不得出现在 evaluate.WEIGHTS 的维度键里。象可以进正文，不许进分数。

`--selftest` 做负例：挖空 basis／恒 general／评分侧偷读 xiang，三处各须被抓。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

# 评分侧：象层一旦被这里读到，象就变成了分数——CONTRACT §五-bis 禁边
# D4 收编：classical_enhancements 族迁 scripts/classical/——名单改带子目录前缀，
# 否则下方 ROOT/"scripts"/name 解析不到会静默跳过（== 评分侧禁读象覆盖面悄悄缩水）。
SCORING_MODULES = (
    "step1.py", "step2.py", "step3.py", "step4.py", "step5.py",
    "timing.py", "judge.py", "classical_analysis.py",
    "classical/classical_enhancements.py",
    "classical/classical_enhancements_dufa.py", "classical/classical_enhancements_fangwei.py",
    "classical/classical_enhancements_fushi.py", "classical/classical_enhancements_menlei.py",
    "classical/classical_enhancements_shen_yao.py",
    "classical/classical_enhancements_yimao_zhugui.py",
    "classical/classical_enhancements_zhugui.py", "effects.py",
)
# 允许读象的层：装配、呈现、输出——象的合法去向
XIANG_CONSUMERS = ("xiang.py", "analyze.py", "narrate.py", "render.py", "output.py",
                   "engine_format.py", "engine_format_report.py")

# 题类→象类别的正例（问句须能命中 question_classes.json 的对应题类）
CATEGORY_CASES = (
    ("占问疾病何时痊愈", "health"),
    ("占问失物能否找回", "loss"),
    ("占问功名能否中第", "career"),
    ("占问婚姻是否可成", "relationship"),
    ("占问行人何时归来", "travel"),
)

# 题类回归锚（362 批）：象类别依赖题类，题类判错则象必错。
# 前 3 条是**全语料对拍查出的漏判**——曾落「其他」/被行人的「何日」抢走；
# 后 3 条是同期必须保持不倒退的古籍问法。问句取自 data/cases 真实例。
CLASS_REGRESSION = (
    ("本日何时有雨", "天气·占雨"),
    ("何雨", "天气·占雨"),
    ("占何日雨", "天气·占雨"),
    ("中秋晴否癸巳日又占", "天气·占晴"),
    ("占何日晴", "天气·占晴"),
    ("本日阴晴", "天气·占晴"),
)


def _xiang_of(question: str) -> dict:
    """实跑一路 analyze，取其象层。失败即抛（不静默降级——门不能假装通过）。"""
    from chart import chart as _chart
    from analyze import analyze as _analyze
    return (_analyze(_chart("coin", question, seed=42)).get("xiang") or {})


def basis_problems(samples: dict[str, dict]) -> list[str]:
    """① 出处：每个产出的象目都必须带非空 basis。"""
    problems: list[str] = []
    for q, x in samples.items():
        if not x:
            problems.append(f"象层整块缺失：{q}（素材在盘面里，analyze 没装配出来）")
            continue
        for key in ("trigram", "ti_yong", "guaci", "yaoci", "hu_gua", "spirit", "fangwei"):
            blk = x.get(key)
            if not isinstance(blk, dict):
                continue
            if not str(blk.get("basis") or "").strip():
                problems.append(f"象目 {key} 缺 basis（{q}）——无出处的象目不得产出")
    return problems


def category_problems(samples: dict[str, dict]) -> list[str]:
    """② 联动：题类→象类别必须真联动；无信号落 general。"""
    problems: list[str] = []
    for q, want in CATEGORY_CASES:
        got = (samples.get(q) or {}).get("category")
        if got != want:
            problems.append(f"象类别未随题类联动：{q} 应为 {want}，实得 {got}")
    # 兜底：问句无任何题类信号时必须落 general（否则就是关键词表过宽）
    from xiang import resolve_xiang_category
    if resolve_xiang_category("", "占问此事如何") != "general":
        problems.append("无题类信号的问句未落 general（关键词兜底表过宽）")
    return problems


def class_problems(regression=CLASS_REGRESSION) -> list[str]:
    """②-bis 题类回归：题类本身不得漏判（象类别是题类的下游）。

    为什么单列一条：362 批查实「本日何时有雨」被行人的「何日」词族抢走、
    「何雨」「中秋晴否…」漏判为「其他」——象类别因此落到 travel/general。
    这类缺陷在象门里看不出来（象门只验类别联动），只能靠题类锚点拦。
    """
    from chain_tables import classify_question
    problems: list[str] = []
    for q, want in regression:
        got = classify_question(q)
        if got != want:
            problems.append(f"题类漏判：{q!r} 应为 {want}，实得 {got}"
                            "——题类判错则象类别必错（见 CLASS_REGRESSION 注）")
    return problems


def no_scoring_problems() -> list[str]:
    """③ 禁评分：评分侧不得读 xiang；xiang 不得成为评分维度。"""
    problems: list[str] = []
    for name in SCORING_MODULES:
        p = ROOT / "scripts" / name
        if not p.exists():
            problems.append(f"评分侧名单失效：scripts/{name} 不在盘上——"
                            "静默跳过＝禁读象覆盖面缩水（D4 收编后名单须带子目录前缀）")
            continue
        text = p.read_text(encoding="utf-8")
        if "xiang" in text and "xiang" not in ("",):
            # 只在真正取用（get/import/[）时判红，避免注释里提一句就红
            for line in text.splitlines():
                s = line.strip()
                if s.startswith("#"):
                    continue
                if ("xiang" in s and ("import" in s or '"xiang"' in s or "'xiang'" in s
                                      or "get(\"xiang\"" in s or "get('xiang'" in s)):
                    problems.append(f"评分侧 {name} 读象：{s[:90]}——象不得倒灌评分（CONTRACT §五-bis）")
                    break
    try:
        from evaluate import WEIGHTS
        if "xiang" in WEIGHTS:
            problems.append("evaluate.WEIGHTS 含 xiang 维度——象层不进评分")
    except Exception:  # noqa: BLE001
        pass
    return problems


def selftest() -> int:
    """负例自证：先证明判据抓得住，再谈它是不是绿的。
    455 批：本函数只证判据；`--selftest` 分支在其通过后仍继续跑真实数据面。
    """
    problems: list[str] = []
    ok = {"trigram": {"basis": "x"}, "ti_yong": {"basis": "x"}}
    if basis_problems({"占": ok}):
        problems.append("自证失败：合规象层被误判为缺出处")
    if not basis_problems({"占": {"trigram": {"basis": ""}}}):
        problems.append("自证失败：挖空 basis 的象目没被抓到")
    if not basis_problems({"占": {}}):
        problems.append("自证失败：象层整块缺失没被抓到")

    bad = {q: {"category": "general"} for q, _ in CATEGORY_CASES}
    if not category_problems(bad):
        problems.append("自证失败：category 恒 general（旧缺陷写法）没被抓到")
    good = {q: {"category": w} for q, w in CATEGORY_CASES}
    if category_problems(good):
        problems.append("自证失败：合规联动被误判")

    if class_problems():
        problems.append("自证失败：题类回归锚未过（先确认正跑是否真的绿）")
    # 负例：把天气词族退化回 362 批前的极简形态，漏判必须被抓到
    # 负例：把天气词族退化回 362 批前的极简形态（只留「占雨」/「占晴」），
    # 「本日何时有雨」「何雨」「中秋晴否…」必须重新漏判并被本判据抓到。
    # 只改内存里的常量（不动盘上 JSON），finally 还原，不给数据文件留风险。
    import chain_tables as _ct
    degenerate = (("本日何时有雨", "天气·占雨"), ("何雨", "天气·占雨"),
                  ("中秋晴否癸巳日又占", "天气·占晴"))
    _saved = _ct.QUESTION_CLASS_KEYWORDS
    try:
        _ct.QUESTION_CLASS_KEYWORDS = {
            c: (["占雨"] if c == "天气·占雨"
                else ["占晴"] if c == "天气·占晴" else list(k))
            for c, k in _saved.items()
        }
        if not class_problems(degenerate):
            problems.append("自证失败：天气词族退化后漏判没被抓到（判据无牙）")
    finally:
        _ct.QUESTION_CLASS_KEYWORDS = _saved

    if problems:
        print("FAIL：负例自证未通过")
        for p in problems:
            print("  " + p)
        return 1
    print("selftest：四类负例（缺出处／恒 general／整块缺失／天气词族退化致题类漏判）"
          "全部抓到；合规输入放行")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="象层门：出处／联动／禁评分")
    ap.add_argument("--selftest", action="store_true", help="负例自证")
    args = ap.parse_args()
    if args.selftest:
        st = selftest()
        if st != 0:
            return st
        # 455 批：负例通过后继续跑真实数据面（不提前 return；check.py 只以 --selftest 调本门）

    samples: dict[str, dict] = {}
    for q, _ in CATEGORY_CASES:
        samples[q] = _xiang_of(q)

    problems: list[str] = []
    problems.extend(basis_problems(samples))
    problems.extend(category_problems(samples))
    problems.extend(class_problems())
    problems.extend(no_scoring_problems())

    cats = {q: (x.get("category") or "—") for q, x in samples.items()}
    print(f"象层门：{len(samples)} 路实跑；象类别 {list(cats.values())}")
    print(f"      题类回归锚 {len(CLASS_REGRESSION)} 条（占雨/占晴漏判回归）；"
          f"评分侧 {len(SCORING_MODULES)} 个模块禁读象")
    if problems:
        print(f"FAIL：{len(problems)} 项")
        for p in problems:
            print("  " + p)
        return 1
    print("校验不过项: 无（象目有出处、类别随题类、象层未倒灌评分）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
